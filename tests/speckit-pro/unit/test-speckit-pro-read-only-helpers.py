#!/usr/bin/env python3
"""Stdlib-only tests for XPLAT-005 read-only runner helpers."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
GENERIC_CAPTURE_LIMIT_BYTES = 16 * 1024
PLAN_LAYERS_CAPTURE_LIMIT_BYTES = 256 * 1024
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "read-only-helpers"
PLAN_LAYERS_FIXTURE_DIR = "tests/speckit-pro/unit/fixtures/plan-layers"
FEATURE_DIR = "tests/speckit-pro/unit/fixtures/read-only-helpers/read-only-helper-feature"
ARCHIVED_FEATURE_DIR = "specs/xplat-005-read-only-helper-port"
REPOSITORY_BASH_CONFINEMENT_PLAN_DIR = (
    "tests/speckit-pro/unit/fixtures/plan-layers/repository-bash-confinement-plan"
)
WORKFLOW_FILE = "docs/ai/specs/.process/XPLAT-005-workflow.md"
PR_PACKET_FIXTURE_DIR = REPO_ROOT / "tests" / "speckit-pro" / "unit" / "fixtures" / "pr-packet"
PR_PACKET_SCHEMA = (
    PLUGIN_ROOT / "skills" / "speckit-autopilot" / "contracts" / "pr-packet.schema.json"
)
PR_PACKET_SCHEMA_FIXTURE = (
    REPO_ROOT
    / "tests"
    / "speckit-pro"
    / "unit"
    / "fixtures"
    / "pr-packet-feature"
    / "specs"
    / "prsg-012-reviewer-ready-pr-packet-contract"
    / "contracts"
    / "pr-packet.schema.json"
)

if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

EXPECTED_HELPERS = [
    "helper-registry-dispatch",
    "check-prerequisites",
    "detect-commands",
    "detect-presets",
    "count-markers",
    "validate-gate",
    "reviewability-gate",
    "estimate-reviewable-loc",
    "resolve-confidence-mode",
    "confidence-gate",
    "generate-spec-index-check",
    "o5-topology",
    "atomicity-route",
    "plan-layers-feature-dir",
    "validate-pr-workflow-contract",
    "validate-pr-packet-read-only",
    "estimate-spec-size",
]

JSON_STDOUT_PARITY_HELPERS = {"atomicity-route"}

HELPER_CASES: dict[str, dict[str, object]] = {
    "check-prerequisites": {"workflow_file": WORKFLOW_FILE},
    "detect-commands": {},
    "detect-presets": {},
    "count-markers": {"type": "all", "feature_dir": FEATURE_DIR},
    "validate-gate": {"gate": "G7", "feature_dir": FEATURE_DIR},
    "reviewability-gate": {"mode_name": "setup", "target": WORKFLOW_FILE},
    "estimate-reviewable-loc": {"plan_file": f"{FEATURE_DIR}/plan.md"},
    "resolve-confidence-mode": {"autopilot_args": ["--advisory", WORKFLOW_FILE]},
    "confidence-gate": {"workflow_file": WORKFLOW_FILE, "mode_name": "advisory"},
    "generate-spec-index-check": {},
    "o5-topology": {"target": FEATURE_DIR},
    "atomicity-route": {"feature_dir": FEATURE_DIR},
    "plan-layers-feature-dir": {"feature_dir": FEATURE_DIR},
    "validate-pr-workflow-contract": {"title": "feat(XPLAT-005): Add read-only helper port"},
    "validate-pr-packet-read-only": {"packet_path": "tests/speckit-pro/unit/fixtures/read-only-helpers/missing-pr-packet.json"},
    "estimate-spec-size": {"user_stories": 2, "files": 3, "frs": 4},
}


def runner_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(PLUGIN_ROOT) if not existing else f"{PLUGIN_ROOT}{os.pathsep}{existing}"
    env.setdefault("SPECKIT_PR_PACKET_TIMESTAMP", "2026-07-02T00:00:00Z")
    return env


def helper_request(helper_id: str, inputs: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "request_id": f"test-{helper_id}",
        "helper_id": helper_id,
        "operation": helper_id,
        "mode": "read_only",
        "inputs": inputs or {},
    }


def run_runner(
    request: object,
    env_override: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, object], list[dict[str, object]]]:
    env = runner_env()
    if env_override:
        env.update(env_override)
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=json.dumps(request) if not isinstance(request, str) else request,
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        env=env,
        shell=False,
        check=False,
    )
    response = json.loads(completed.stdout) if completed.stdout.strip() else {}
    stderr_records = [json.loads(line) for line in completed.stderr.splitlines() if line.strip()]
    return completed, response, stderr_records


def response_cwd(data: dict[str, object]) -> Path:
    record = data.get("effective_cwd") or data.get("cwd")
    if not isinstance(record, dict):
        return REPO_ROOT
    value = str(record.get("value") or ".")
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def command_stdin_fixture(command: str) -> Path:
    if "<" not in command:
        raise AssertionError(f"authoritative_command must include a stdin fixture: {command}")
    stdin_path = command.split("<", 1)[1].strip()
    if not stdin_path or any(char.isspace() for char in stdin_path):
        raise AssertionError(f"authoritative_command must use one stdin fixture path: {command}")
    return REPO_ROOT / stdin_path


class ReadOnlyHelperTests(unittest.TestCase):
    helper_filter: str | None = None

    def assert_response(self, response: dict[str, object], status: str, exit_code: int) -> None:
        self.assertEqual(response["schema_version"], "1.0")
        self.assertEqual(response["status"], status)
        self.assertEqual(response["exit_code"], exit_code)
        self.assertIsNone(response["legacy_exit_code"])
        self.assertIsInstance(response["diagnostics"], list)
        self.assertIsInstance(response["data"], dict)

    def filtered_helpers(self) -> list[str]:
        if self.helper_filter:
            self.assertIn(self.helper_filter, EXPECTED_HELPERS)
            return [self.helper_filter]
        return EXPECTED_HELPERS

    def assert_helper_matches_bash_reference(self, helper_id: str, inputs: dict[str, object]) -> dict[str, object]:
        completed, response, stderr_records = run_runner(helper_request(helper_id, inputs))
        data = response["data"]
        self.assertEqual(data["shell"], False)
        self.assertEqual(data["argv"][-2:], ["-m", "speckit_pro_runner"])
        self.assertEqual(data["python_operation"], helper_id)
        self.assertEqual(data["authoritative_command"].split(" < ", 1)[0], "python -m speckit_pro_runner")
        self.assertEqual(completed.returncode, response["exit_code"])
        self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])
        return response

    def assert_stdout_matches_reference(self, helper_id: str, actual: str, expected: str) -> None:
        if helper_id not in JSON_STDOUT_PARITY_HELPERS:
            self.assertEqual(actual, expected)
            return
        try:
            actual_json = json.loads(actual)
            expected_json = json.loads(expected)
        except json.JSONDecodeError as exc:
            self.fail(f"FAIL detail: {helper_id} stdout must be valid JSON: {exc}; actual={actual!r}; expected={expected!r}")
        self.assertEqual(
            actual_json,
            expected_json,
            f"FAIL detail: {helper_id} JSON stdout mismatch: actual_json={actual_json!r}; expected_json={expected_json!r}; actual={actual!r}; expected={expected!r}",
        )

    def run_plan_layers(
        self,
        feature_dir: str,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object], dict[str, object]]:
        completed, response, stderr_records = run_runner(
            helper_request("plan-layers-feature-dir", {"feature_dir": feature_dir})
        )
        self.assertEqual(completed.returncode, response["exit_code"])
        self.assertEqual(
            [diag["code"] for diag in stderr_records],
            [diag["code"] for diag in response["diagnostics"]],
        )
        planner = response["data"]["stdout_json"]
        self.assertEqual(planner["tool"], "plan-layers")
        self.assertEqual(planner["contract_version"], 1)
        return completed, response, planner

    def test_registry_dispatch_lists_only_read_only_helpers(self) -> None:
        if self.helper_filter and self.helper_filter != "helper-registry-dispatch":
            self.skipTest("registry test is not part of this helper filter")
        completed, response, stderr_records = run_runner(helper_request("helper-registry-dispatch"))
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(stderr_records, [])
        self.assert_response(response, "ok", 0)
        data = response["data"]
        helpers = data["helpers"]
        helper_ids = [record["helper_id"] for record in helpers]
        self.assertEqual(helper_ids, sorted(EXPECTED_HELPERS))
        self.assertEqual(data["mutation_modes_promoted"], [])
        for record in helpers:
            self.assertEqual(record["mode"], "read_only")
            self.assertIn(record["promotion_status"], {"python_authoritative", "bash_reference_only", "out_of_scope"})
            self.assertEqual(record["python_operation"], record["operation"])
            self.assertNotIn("script", record)
            self.assertNotIn("generate-pr-body", str(record))
            self.assertNotIn("restack.sh", str(record))
            active_record = {key: value for key, value in record.items() if key != "inactive_provenance"}
            self.assertNotIn(".sh", json.dumps(active_record, sort_keys=True))
            fixture_path = command_stdin_fixture(record["authoritative_command"])
            self.assertTrue(fixture_path.is_file(), record["authoritative_command"])
            request = json.loads(fixture_path.read_text(encoding="utf-8"))
            self.assertEqual(request["helper_id"], record["helper_id"])
            self.assertEqual(request["operation"], record["operation"])

    def test_envelope_rejects_unknown_and_mutation_modes(self) -> None:
        if self.helper_filter:
            self.skipTest("envelope rejection test is registry-level")
        cases = [
            (helper_request("not-a-helper"), "unknown_helper", 2),
            ({**helper_request("count-markers"), "mode": "write"}, "invalid_envelope", 2),
            ({**helper_request("count-markers"), "operation": "other"}, "helper_operation_mismatch", 2),
        ]
        for request, code, exit_code in cases:
            with self.subTest(code=code):
                completed, response, stderr_records = run_runner(request)
                self.assertEqual(completed.returncode, exit_code)
                self.assert_response(response, "input_error", exit_code)
                self.assertEqual([diag["code"] for diag in response["diagnostics"]], [code])
                self.assertEqual([diag["code"] for diag in stderr_records], [code])

    def test_write_mode_diagnostic_names_registered_mutation_operation(self) -> None:
        if self.helper_filter:
            self.skipTest("write-mode remediation is registry-level")
        cases = [
            (
                "generate-spec-index-check",
                {"write_mode": True},
                "Submit a separate runner request with helper_id and operation generate-spec-index-write.",
            ),
            (
                "count-markers",
                {"type": "all", "feature_dir": FEATURE_DIR, "write_mode": True},
                "Inspect mutation-registry-dispatch for a registered Python mutation operation.",
            ),
            (
                "plan-layers-feature-dir",
                {"feature_dir": FEATURE_DIR, "write_mode": True},
                "The registered plan-layers-marker-plan operation remains deferred; keep this request read_only.",
            ),
            (
                "validate-pr-packet-read-only",
                {**HELPER_CASES["validate-pr-packet-read-only"], "write_mode": True},
                "Submit a separate runner request with helper_id and operation validate-pr-packet-write.",
            ),
        ]
        for helper_id, inputs, mutation_action in cases:
            with self.subTest(helper_id=helper_id):
                completed, response, stderr_records = run_runner(helper_request(helper_id, inputs))
                self.assertEqual(completed.returncode, 2)
                self.assert_response(response, "input_error", 2)
                diagnostic = response["diagnostics"][0]
                self.assertEqual(diagnostic["code"], "unsupported_mode")
                self.assertEqual(
                    diagnostic["remediation"]["actions"],
                    ["Remove write_mode from the request.", mutation_action],
                )
                self.assertNotIn("Bash", json.dumps(diagnostic, sort_keys=True))
                self.assertEqual(stderr_records, response["diagnostics"])

    def test_active_error_output_uses_registered_operation_names(self) -> None:
        if self.helper_filter:
            self.skipTest("active output regression is cross-helper")
        from speckit_pro_runner.helpers.read_only import (
            confidence_gate,
            count_markers,
            validate_pr_packet_read_only,
            validate_pr_workflow_contract,
        )

        cases = [
            (
                count_markers({}, REPO_ROOT),
                '{"error":"Usage: count-markers <gaps|findings|clarifications|all> <feature_dir>"}\n',
                "",
                2,
            ),
            (
                confidence_gate({}, REPO_ROOT),
                '{"error":"Usage: confidence-gate <workflow-file> [--threshold N.NN] [--mode advisory|strict]"}\n',
                "",
                1,
            ),
            (
                validate_pr_workflow_contract({}, REPO_ROOT),
                "",
                "validate-pr-workflow-contract: input_error: missing required option --title\n",
                2,
            ),
            (
                validate_pr_packet_read_only({}, REPO_ROOT),
                None,
                "validate-pr-packet-read-only: input_error: missing-packet-path: input.error: no-path\n",
                2,
            ),
        ]
        for result, stdout, stderr, exit_code in cases:
            with self.subTest(stderr=stderr):
                if stdout is not None:
                    self.assertEqual(result["stdout"], stdout)
                self.assertEqual(result["stderr"], stderr)
                self.assertEqual(result["exit_code"], exit_code)
                self.assertNotIn(".sh", result["stdout"] + result["stderr"])

    def test_fixture_manifests_cover_registered_helpers(self) -> None:
        if self.helper_filter and self.helper_filter != "helper-registry-dispatch":
            self.skipTest("manifest coverage test is registry-level")
        fixture_manifest = json.loads((FIXTURE_DIR / "fixture-manifest.json").read_text(encoding="utf-8"))
        bash_manifest = json.loads((FIXTURE_DIR / "bash-reference-manifest.json").read_text(encoding="utf-8"))
        fixture_ids = [record["helper_id"] for record in fixture_manifest["helpers"]]
        bash_ids = [record["helper_id"] for record in bash_manifest["comparisons"]]
        self.assertEqual(fixture_ids, EXPECTED_HELPERS)
        self.assertEqual(bash_ids, [helper for helper in EXPECTED_HELPERS if helper != "helper-registry-dispatch"])
        for record in fixture_manifest["helpers"]:
            for field in (
                "promotion_status",
                "failure_classes",
                "rejected_stdout_schema",
                "deterministic_remediation",
                "subprocess_policy",
                "path_boundary_policy",
                "authoritative_command",
                "rollback",
            ):
                self.assertIn(field, record)
            self.assertEqual(record["subprocess_policy"]["shell"], False)
            self.assertTrue(record["deterministic_remediation"]["actions"])
            active_guidance = json.dumps(
                {
                    "deterministic_remediation": record["deterministic_remediation"],
                    "rollback": record["rollback"],
                },
                sort_keys=True,
            )
            self.assertNotIn(".sh", active_guidance)
            self.assertNotIn("bash", active_guidance.lower())
            fixture_path = command_stdin_fixture(record["authoritative_command"])
            self.assertTrue(fixture_path.is_file(), record["authoritative_command"])
            request = json.loads(fixture_path.read_text(encoding="utf-8"))
            self.assertEqual(request["helper_id"], record["helper_id"])
            self.assertEqual(request["operation"], record["operation"])
        for comparison in bash_manifest["comparisons"]:
            self.assertFalse(comparison["subprocess"]["shell"])
            self.assertIsInstance(comparison["subprocess"]["argv"], list)
            self.assertLessEqual(comparison["subprocess"]["timeout_seconds"], 30)
            self.assertTrue(comparison["source_script"].endswith(".sh"), comparison["source_script"])
            expected_stdout_comparison = "json_semantic" if comparison["helper_id"] in JSON_STDOUT_PARITY_HELPERS else "exact"
            self.assertEqual(comparison.get("stdout_comparison", "exact"), expected_stdout_comparison)

    def test_path_boundary_rejects_traversal_and_symlink_escape(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("path-boundary cases use check-prerequisites")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as inside, tempfile.TemporaryDirectory() as outside:
            outside_file = Path(outside) / "outside-workflow.md"
            outside_file.write_text("# outside\n", encoding="utf-8")
            symlink_path = Path(inside) / "escape.md"
            try:
                symlink_path.symlink_to(outside_file)
            except OSError:
                symlink_path = Path(inside) / "not-a-symlink.md"
                symlink_path.write_text("# fallback\n", encoding="utf-8")
            cases = [
                "../outside.md",
                symlink_path.relative_to(REPO_ROOT).as_posix(),
            ]
            for workflow_file in cases:
                with self.subTest(workflow_file=workflow_file):
                    completed, response, stderr_records = run_runner(
                        helper_request("check-prerequisites", {"workflow_file": workflow_file})
                    )
                    if workflow_file == cases[1] and not symlink_path.is_symlink():
                        self.assertIn(response["status"], {"ok", "expected_failure"})
                        continue
                    self.assertEqual(completed.returncode, 2)
                    self.assert_response(response, "input_error", 2)
                    self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["unsupported_path"])
                    self.assertEqual([diag["code"] for diag in stderr_records], ["unsupported_path"])

    def test_windows_style_relative_paths_are_normalized_before_execution(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("path-normalization case uses check-prerequisites")
        windows_workflow = WORKFLOW_FILE.replace("/", "\\")
        completed, response, stderr_records = run_runner(
            helper_request("check-prerequisites", {"workflow_file": windows_workflow})
        )
        self.assertIn(completed.returncode, {0, 1})
        self.assertIn(response["status"], {"ok", "expected_failure"})
        self.assertEqual(response["data"]["argv"][-2:], ["-m", "speckit_pro_runner"])
        workflow_checks = [
            check
            for check in response["data"]["stdout_json"]["checks"]
            if check["check"] == "workflow_file"
        ]
        self.assertEqual(workflow_checks[0]["detail"], WORKFLOW_FILE)
        self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])

    def test_explicit_repo_root_cannot_redefine_trust_boundary(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("repo_root trust-boundary case uses detect-commands")
        with tempfile.TemporaryDirectory() as outside:
            outside_root = Path(outside)
            (outside_root / "speckit-pro" / "speckit_pro_runner").mkdir(parents=True)
            completed, response, stderr_records = run_runner(
                helper_request("detect-commands", {"repo_root": str(outside_root)})
            )
        self.assertEqual(completed.returncode, 2)
        self.assert_response(response, "input_error", 2)
        self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["unsupported_path"])
        self.assertEqual([diag["code"] for diag in stderr_records], ["unsupported_path"])

    def test_repo_root_symlink_escape_is_rejected(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("repo_root symlink-boundary case uses detect-commands")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project, tempfile.TemporaryDirectory() as outside:
            project_path = Path(project)
            outside_root = Path(outside)
            (outside_root / "speckit-pro" / "speckit_pro_runner").mkdir(parents=True)
            link = project_path / "external"
            try:
                link.symlink_to(outside_root, target_is_directory=True)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            completed, response, stderr_records = run_runner(
                helper_request("detect-commands", {"repo_root": link.relative_to(REPO_ROOT).as_posix()})
            )
        self.assertEqual(completed.returncode, 2)
        self.assert_response(response, "input_error", 2)
        self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["unsupported_path"])
        self.assertEqual([diag["code"] for diag in stderr_records], ["unsupported_path"])

    def test_find_repo_root_rejects_symlinked_plugin_anchor(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("repo-root discovery case uses check-prerequisites")
        with tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as outside:
            project_path = Path(project)
            outside_plugin = Path(outside) / "speckit-pro"
            (outside_plugin / "speckit_pro_runner").mkdir(parents=True)
            try:
                (project_path / "speckit-pro").symlink_to(outside_plugin, target_is_directory=True)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            from speckit_pro_runner.helpers.read_only import find_repo_root

            self.assertIsNone(find_repo_root(project_path))

    def test_find_repo_root_falls_back_to_specify_project_root(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("repo-root discovery case uses check-prerequisites")
        with tempfile.TemporaryDirectory() as project:
            project_path = Path(project)
            (project_path / ".specify").mkdir()
            nested = project_path / "docs" / "ai" / "specs"
            nested.mkdir(parents=True)
            from speckit_pro_runner.helpers.read_only import find_repo_root

            self.assertEqual(find_repo_root(nested), project_path.resolve())

    def test_find_repo_root_prefers_vendored_runner_over_specify_fallback(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("repo-root discovery case uses check-prerequisites")
        with tempfile.TemporaryDirectory() as project:
            project_path = Path(project)
            (project_path / ".specify").mkdir()
            vendored = project_path / "sub"
            (vendored / "speckit-pro" / "speckit_pro_runner").mkdir(parents=True)
            start = vendored / "deeper"
            start.mkdir()
            from speckit_pro_runner.helpers.read_only import find_repo_root

            self.assertEqual(find_repo_root(start), vendored.resolve())

    def test_find_repo_root_rejects_symlinked_specify_anchor(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("repo-root discovery case uses check-prerequisites")
        with tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as outside:
            project_path = Path(project)
            outside_specify = Path(outside) / ".specify"
            outside_specify.mkdir()
            try:
                (project_path / ".specify").symlink_to(outside_specify, target_is_directory=True)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            from speckit_pro_runner.helpers.read_only import find_repo_root

            self.assertIsNone(find_repo_root(project_path))

    def test_find_specify_returns_none_when_home_is_unresolvable(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("specify discovery case uses check-prerequisites")
        from speckit_pro_runner.helpers import read_only

        with patch.object(read_only.shutil, "which", return_value=None), patch.object(
            read_only.Path, "home", side_effect=RuntimeError("no home directory")
        ):
            self.assertIsNone(read_only.find_specify())

    def test_helper_argv_uses_runner_even_when_registered_script_is_symlinked(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("helper argv script-boundary case uses check-prerequisites")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project, tempfile.TemporaryDirectory() as outside:
            project_path = Path(project)
            outside_script = Path(outside) / "helper.sh"
            outside_script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            try:
                (project_path / "helper.sh").symlink_to(outside_script)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            from speckit_pro_runner.helpers.read_only import helper_argv

            result = helper_argv(SimpleNamespace(helper_id="check-prerequisites", script="helper.sh"), {}, project_path)
            self.assertIsInstance(result, list)
            self.assertEqual(result[-2:], ["-m", "speckit_pro_runner"])

    def test_helper_result_reports_executable_runner_stdin_request(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("helper argv/stdin metadata case uses detect-commands")
        completed, response, stderr_records = run_runner(helper_request("detect-commands"))
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(stderr_records, [])
        self.assert_response(response, "ok", 0)
        data = response["data"]
        self.assertEqual(data["argv"][-2:], ["-m", "speckit_pro_runner"])
        self.assertEqual(data["argv_role"], "replay_runner_command")
        self.assertEqual(data["execution_model"], "direct_python_helper")
        self.assertTrue(data["executed_in_process"])
        self.assertEqual(data["stdin_mode"], "single_json_request")
        self.assertEqual(
            data["invocation_contract"],
            {
                "actual_execution_uses_argv": False,
                "argv_executable_without_stdin": False,
                "stdin_required": True,
                "stdin_request_field": "stdin_request",
            },
        )
        stdin_request = data["stdin_request"]
        self.assertEqual(stdin_request["helper_id"], "detect-commands")
        self.assertEqual(stdin_request["operation"], "detect-commands")
        replay_argv = data["argv"]
        self.assertIsInstance(replay_argv, list)
        self.assertEqual(replay_argv[0], sys.executable)
        replay = subprocess.run(
            [sys.executable, *replay_argv[1:]],
            input=json.dumps(stdin_request),
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
            env=runner_env(),
            shell=False,
            check=False,
        )
        self.assertEqual(replay.returncode, 0, replay.stderr)
        replay_response = json.loads(replay.stdout)
        self.assertEqual(replay_response["status"], "ok")

    def test_detect_commands_rejects_file_repo_root_and_reports_directory_cwd(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("detect-commands repo_root validation case")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            file_root = project_path / "not-a-directory"
            file_root.write_text("", encoding="utf-8")
            completed, response, stderr_records = run_runner(
                helper_request("detect-commands", {"repo_root": file_root.relative_to(REPO_ROOT).as_posix()})
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["invalid_input"])
            self.assertEqual([diag["code"] for diag in stderr_records], ["invalid_input"])

            (project_path / "pnpm-lock.yaml").write_text("", encoding="utf-8")
            (project_path / "package.json").write_text('{"scripts":{"test":"vitest"}}\n', encoding="utf-8")
            completed, response, stderr_records = run_runner(
                helper_request("detect-commands", {"repo_root": project_path.relative_to(REPO_ROOT).as_posix()})
            )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        self.assertEqual(response["data"]["cwd"]["value"], ".")
        self.assertEqual(response["data"]["effective_cwd"]["value"], project_path.relative_to(REPO_ROOT).as_posix())
        self.assertEqual(stderr_records, [])

    def test_detect_commands_defaults_package_json_only_node_to_npm(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("detect-commands package-json-only case")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            (project_path / "package.json").write_text('{"scripts":{"build":"vite","test":"vitest"}}\n', encoding="utf-8")
            completed, response, stderr_records = run_runner(
                helper_request("detect-commands", {"repo_root": project_path.relative_to(REPO_ROOT).as_posix()})
            )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        stdout_json = response["data"]["stdout_json"]
        self.assertEqual(stdout_json["stack"], "nodejs")
        self.assertEqual(stdout_json["package_manager"], "npm")
        self.assertEqual(stdout_json["commands"]["BUILD"], "npm build")
        self.assertEqual(stdout_json["commands"]["UNIT_TEST"], "npm test")
        self.assertEqual(stderr_records, [])

    def test_detect_commands_subdir_matches_bash_reference_from_effective_cwd(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("detect-commands effective-cwd parity case")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            (project_path / "package-lock.json").write_text("{}\n", encoding="utf-8")
            (project_path / "package.json").write_text(
                '{"scripts":{"build":"vite","typecheck":"tsc --noEmit","lint":"eslint .","test":"vitest","test:e2e":"playwright test"}}\n',
                encoding="utf-8",
            )
            response = self.assert_helper_matches_bash_reference(
                "detect-commands",
                {"repo_root": project_path.relative_to(REPO_ROOT).as_posix()},
            )
        self.assertEqual(response["data"]["cwd"]["value"], ".")
        self.assertNotEqual(response["data"]["effective_cwd"]["value"], ".")

    def test_redundant_confidence_gate_path_is_canonicalized_before_execution(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate canonical argv case")
        redundant_workflow = "docs/ai/specs/.process/../.process/XPLAT-005-workflow.md"
        response = self.assert_helper_matches_bash_reference(
            "confidence-gate",
            {"workflow_file": redundant_workflow, "mode_name": "advisory"},
        )
        self.assertEqual(response["data"]["argv"][-2:], ["-m", "speckit_pro_runner"])
        self.assertNotIn("..", response["data"]["stdout"]["text"])

    def test_check_prerequisites_uses_canonical_input_for_replay(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("check-prerequisites canonical argv case")
        redundant_workflow = "docs/ai/specs/.process/../.process/XPLAT-005-workflow.md"
        response = self.assert_helper_matches_bash_reference(
            "check-prerequisites",
            {"workflow_file": redundant_workflow},
        )
        workflow_checks = [
            check
            for check in response["data"]["stdout_json"]["checks"]
            if check["check"] == "workflow_file"
        ]
        self.assertEqual(workflow_checks[0]["detail"], WORKFLOW_FILE)

    def test_confidence_gate_rejects_invalid_threshold(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate threshold case")
        cases = [
            {"workflow_file": WORKFLOW_FILE, "threshold": "abc"},
            {"workflow_file": WORKFLOW_FILE, "threshold": "nan"},
            {"workflow_file": WORKFLOW_FILE, "mode_name": "maybe"},
        ]
        for inputs in cases:
            with self.subTest(inputs=inputs):
                completed, response, stderr_records = run_runner(helper_request("confidence-gate", inputs))
                self.assertEqual(completed.returncode, 2)
                self.assert_response(response, "input_error", 2)
                self.assertTrue("invalid threshold" in response["data"]["stdout_json"]["error"] or "invalid mode" in response["data"]["stdout_json"]["error"])
                self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])

    def test_generate_spec_index_ignores_symlinked_spec_children(self) -> None:
        if self.helper_filter and self.helper_filter != "generate-spec-index-check":
            self.skipTest("generate-spec-index path-boundary case")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project, tempfile.TemporaryDirectory() as outside:
            root = Path(project)
            specs = root / "specs"
            specs.mkdir()
            outside_spec = Path(outside) / "escaped"
            outside_spec.mkdir()
            (outside_spec / "SPEC-MOC.md").write_text("---\nstatus: complete\n---\n", encoding="utf-8")
            try:
                (specs / "escaped").symlink_to(outside_spec, target_is_directory=True)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            completed, response, stderr_records = run_runner(
                helper_request("generate-spec-index-check", {"repo_root": root.relative_to(REPO_ROOT).as_posix()})
            )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        self.assertIn("all in-scope maps up to date", response["data"]["stdout"]["text"])
        self.assertEqual(stderr_records, [])

    def test_o5_topology_reports_bad_child_shapes_without_crashing(self) -> None:
        if self.helper_filter and self.helper_filter != "o5-topology":
            self.skipTest("o5-topology shape case")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            manifest = Path(project) / "o5-parent-manifest.json"
            manifest.write_text(
                json.dumps({"schemaVersion": 1, "kind": "o5_parent_manifest", "parent": {}, "children": ["bad", {"id": "c", "path": "specs/c", "dependsOn": "bad"}]}),
                encoding="utf-8",
            )
            completed, response, stderr_records = run_runner(
                helper_request("o5-topology", {"target": manifest.relative_to(REPO_ROOT).as_posix()})
            )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        codes = {problem["code"] for problem in response["data"]["stdout_json"]["problems"]}
        self.assertIn("invalid_child_shape", codes)
        self.assertIn("invalid_depends_on", codes)
        self.assertEqual(stderr_records, [])

    def test_validate_pr_packet_rejects_non_object_and_bad_nested_shapes(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet shape case")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            packet = Path(project) / "packet.json"
            packet.write_text('{"broken":\n', encoding="utf-8")
            completed, response, stderr_records = run_runner(
                helper_request("validate-pr-packet-read-only", {"packet_path": packet.relative_to(REPO_ROOT).as_posix()})
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual(response["data"]["stdout_json"]["failures"][0]["rule"], "input.error")
            self.assertEqual(stderr_records, response["diagnostics"])

            packet.write_bytes(b'{"schema_version":"1.0.0","packet_id":"bad-\xff"}\n')
            completed, response, stderr_records = run_runner(
                helper_request("validate-pr-packet-read-only", {"packet_path": packet.relative_to(REPO_ROOT).as_posix()})
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual(response["data"]["stdout_json"]["failures"][0]["rule"], "input.utf8")
            self.assertEqual(stderr_records, response["diagnostics"])

            packet.write_text("[]\n", encoding="utf-8")
            completed, response, stderr_records = run_runner(
                helper_request("validate-pr-packet-read-only", {"packet_path": packet.relative_to(REPO_ROOT).as_posix()})
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])

            packet.write_text(
                json.dumps({"verification_evidence": ["ok"], "scope_evidence": [], "generated_title": [], "target": [], "validation_result_path": "../outside.json", "body_file": []}),
                encoding="utf-8",
            )
            completed, response, stderr_records = run_runner(
                helper_request("validate-pr-packet-read-only", {"packet_path": packet.relative_to(REPO_ROOT).as_posix()})
            )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        rules = {failure["rule"] for failure in response["data"]["stdout_json"]["failures"]}
        self.assertIn("input.shape.scope_evidence", rules)
        self.assertIn("input.path.validation_result_path", rules)
        self.assertIn("input.path.body_file", rules)
        self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])

    def test_validate_pr_packet_reports_oversized_json_integer_as_input_error(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet oversized integer case")
        max_digits = getattr(sys, "get_int_max_str_digits", lambda: 0)()
        if max_digits <= 0:
            self.skipTest("Python JSON integer digit limit is disabled")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            packet = Path(project) / "packet.json"
            packet.write_text(
                '{"packet_id": "oversized-integer", "oversized": '
                + ("9" * (max_digits + 1))
                + "}\n",
                encoding="utf-8",
            )
            completed, response, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    {"packet_path": packet.relative_to(REPO_ROOT).as_posix()},
                )
            )

        self.assertEqual(completed.returncode, 2)
        self.assert_response(response, "input_error", 2)
        self.assertEqual(response["data"]["stdout_json"]["failures"][0]["rule"], "input.error")
        self.assertNotIn("Traceback", completed.stderr)
        self.assertEqual(stderr_records, response["diagnostics"])

    def test_validate_pr_packet_rejects_schema_minimal_false_pass(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet schema case")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            packet = Path(project) / "minimal-packet.json"
            packet.write_text(
                json.dumps(
                    {
                        "verification_evidence": ["present"],
                        "scope_evidence": {"changed_files": ["README.md"]},
                        "validation_result_path": (
                            "specs/example/.process/pr-packets/minimal-packet/validation.json"
                        ),
                    }
                ),
                encoding="utf-8",
            )
            completed, response, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    {"packet_path": packet.relative_to(REPO_ROOT).as_posix()},
                )
            )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        failures = response["data"]["stdout_json"]["failures"]
        self.assertIn("packet.schema.required", {failure["rule"] for failure in failures})
        missing_fields = {failure["field"] for failure in failures}
        self.assertTrue({"target", "generated_title", "body_file"}.issubset(missing_fields))
        self.assertEqual(stderr_records, response["diagnostics"])

    def test_validate_pr_packet_enforces_validation_result_source_fingerprint_schema(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet schema source fingerprint case")
        valid_packet_path = PR_PACKET_FIXTURE_DIR / "valid-single.json"
        completed, response, _stderr_records = run_runner(
            helper_request(
                "validate-pr-packet-read-only",
                {"packet_path": valid_packet_path.relative_to(REPO_ROOT).as_posix()},
            )
        )
        self.assertEqual(completed.returncode, 0)
        validation_result = response["data"]["stdout_json"]
        valid_packet = json.loads(valid_packet_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            packet = Path(project) / "source-fingerprints.json"
            for name, source_fingerprints, expected_rule in (
                ("empty", {}, "packet.schema.min_properties"),
                ("malformed", {"packet": {"path": "source-fingerprints.json"}}, "packet.schema.required"),
            ):
                with self.subTest(name=name):
                    packet.write_text(
                        json.dumps(
                            {
                                **valid_packet,
                                "packet_id": "source-fingerprints",
                                "validation_result_path": (
                                    "specs/prsg-012-reviewer-ready-pr-packet-contract/.process/"
                                    "pr-packets/source-fingerprints/validation.json"
                                ),
                                "validation_result": {
                                    **validation_result,
                                    "source_fingerprints": source_fingerprints,
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    completed, response, stderr_records = run_runner(
                        helper_request(
                            "validate-pr-packet-read-only",
                            {"packet_path": packet.relative_to(REPO_ROOT).as_posix()},
                        )
                    )
                    self.assertEqual(completed.returncode, 1)
                    self.assert_response(response, "expected_failure", 1)
                    rules = {failure["rule"] for failure in response["data"]["stdout_json"]["failures"]}
                    self.assertIn(expected_rule, rules)
                    self.assertEqual(stderr_records, response["diagnostics"])

    def test_pr_packet_schema_accepts_established_scopes_and_rejects_mixed_case(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet schema pattern case")
        schema = json.loads(PR_PACKET_SCHEMA.read_text(encoding="utf-8"))
        title_properties = schema["$defs"]["generated_title"]["properties"]
        scope_pattern = title_properties["scope"]["pattern"]
        value_pattern = title_properties["value"]["pattern"]
        fixture_schema = json.loads(PR_PACKET_SCHEMA_FIXTURE.read_text(encoding="utf-8"))
        fixture_title_properties = fixture_schema["$defs"]["generated_title"]["properties"]
        self.assertEqual(fixture_title_properties["scope"]["pattern"], scope_pattern)
        self.assertEqual(fixture_title_properties["value"]["pattern"], value_pattern)

        for scope in ("speckit-pro", "PRSG-012", "SPEC-014C"):
            with self.subTest(scope=scope, expected="accepted"):
                self.assertIsNotNone(re.fullmatch(scope_pattern, scope))
                self.assertIsNotNone(
                    re.fullmatch(value_pattern, f"feat({scope}): Add packet validation")
                )

        for scope in ("PRsg-012", "SPEC-014c", "speckit-PRO"):
            with self.subTest(scope=scope, expected="rejected"):
                self.assertIsNone(re.fullmatch(scope_pattern, scope))
                self.assertIsNone(
                    re.fullmatch(value_pattern, f"feat({scope}): Add packet validation")
                )

    def test_validate_pr_packet_rejects_unsafe_missing_and_unreadable_body(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet body path case")
        valid_packet = json.loads((PR_PACKET_FIXTURE_DIR / "valid-single.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            packet = project_path / "packet.json"
            cases = {
                "unsafe": ("../outside.md", "input.path.body_file"),
                "missing": (
                    (project_path / "missing.md").relative_to(REPO_ROOT).as_posix(),
                    "body.path",
                ),
            }
            for name, (body_file, expected_rule) in cases.items():
                with self.subTest(name=name):
                    packet.write_text(
                        json.dumps({**valid_packet, "body_file": body_file}),
                        encoding="utf-8",
                    )
                    completed, response, stderr_records = run_runner(
                        helper_request(
                            "validate-pr-packet-read-only",
                            {"packet_path": packet.relative_to(REPO_ROOT).as_posix()},
                        )
                    )
                    self.assertEqual(completed.returncode, 1)
                    self.assert_response(response, "expected_failure", 1)
                    rules = {
                        failure["rule"]
                        for failure in response["data"]["stdout_json"]["failures"]
                    }
                    self.assertIn(expected_rule, rules)
                    self.assertEqual(stderr_records, response["diagnostics"])

            body = project_path / "unreadable.md"
            body.write_text(
                (PR_PACKET_FIXTURE_DIR / "bodies" / "valid-single.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            packet.write_text(
                json.dumps(
                    {
                        **valid_packet,
                        "body_file": body.relative_to(REPO_ROOT).as_posix(),
                    }
                ),
                encoding="utf-8",
            )
            from speckit_pro_runner.helpers import read_only

            original_trusted_bytes = read_only.trusted_bytes

            def unreadable_body(path: Path, root: Path | None = None) -> bytes | None:
                if path.resolve(strict=False) == body.resolve(strict=False):
                    return None
                return original_trusted_bytes(path, root)

            with patch.object(read_only, "trusted_bytes", side_effect=unreadable_body):
                result = read_only.validate_pr_packet_read_only(
                    {"packet_path": packet.relative_to(REPO_ROOT).as_posix()},
                    REPO_ROOT,
                )
        self.assertEqual(result["exit_code"], 1)
        failures = json.loads(result["stdout"])["failures"]
        self.assertIn("body.readable", {failure["rule"] for failure in failures})

        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            body = project_path / "invalid-utf8.md"
            body.write_bytes((PR_PACKET_FIXTURE_DIR / "bodies" / "valid-single.md").read_bytes() + b"\xff")
            packet = project_path / "invalid-body-utf8.json"
            packet.write_text(
                json.dumps(
                    {
                        **valid_packet,
                        "packet_id": "invalid-body-utf8",
                        "body_file": body.relative_to(REPO_ROOT).as_posix(),
                        "validation_result_path": (
                            "specs/prsg-012-reviewer-ready-pr-packet-contract/.process/"
                            "pr-packets/invalid-body-utf8/validation.json"
                        ),
                    }
                ),
                encoding="utf-8",
            )
            completed, response, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    {"packet_path": packet.relative_to(REPO_ROOT).as_posix()},
                )
            )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        failures = response["data"]["stdout_json"]["failures"]
        self.assertIn("body.utf8", {failure["rule"] for failure in failures})
        self.assertEqual(stderr_records, response["diagnostics"])

    def test_validate_pr_packet_rejects_validation_result_path_not_owned_by_packet(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet validation ownership case")
        valid_packet = json.loads((PR_PACKET_FIXTURE_DIR / "valid-single.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            packet = Path(project) / "valid-single.json"
            packet.write_text(
                json.dumps(
                    {
                        **valid_packet,
                        "validation_result_path": "specs/other-feature/.process/pr-packets/valid-single/validation.json",
                    }
                ),
                encoding="utf-8",
            )
            completed, response, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    {"packet_path": packet.relative_to(REPO_ROOT).as_posix()},
                )
            )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        rules = {failure["rule"] for failure in response["data"]["stdout_json"]["failures"]}
        self.assertIn("input.identity.validation_result_path", rules)
        self.assertEqual(stderr_records, response["diagnostics"])

    def test_validate_pr_packet_checks_body_currentness_without_writing_state(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet currentness case")
        for packet_name in ("valid-single.json", "valid-split.json"):
            with self.subTest(packet_name=packet_name):
                valid_packet_path = PR_PACKET_FIXTURE_DIR / packet_name
                completed, response, stderr_records = run_runner(
                    helper_request(
                        "validate-pr-packet-read-only",
                        {"packet_path": valid_packet_path.relative_to(REPO_ROOT).as_posix()},
                    )
                )
                self.assertEqual(completed.returncode, 0)
                self.assert_response(response, "ok", 0)
                self.assertEqual(response["data"]["stdout_json"]["status"], "passed")
                self.assertEqual(set(response["data"]["stdout_json"]["source_fingerprints"]), {"body", "packet"})
                self.assertFalse(response["data"]["writes_state"])
                self.assertEqual(response["data"]["promotion_status"], "python_authoritative")
                self.assertEqual(stderr_records, [])

        stale_packet = PR_PACKET_FIXTURE_DIR / "invalid-protected-edit.json"
        completed, response, stderr_records = run_runner(
            helper_request(
                "validate-pr-packet-read-only",
                {"packet_path": stale_packet.relative_to(REPO_ROOT).as_posix()},
            )
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        stale_rules = {
            failure["rule"] for failure in response["data"]["stdout_json"]["failures"]
        }
        self.assertIn("body.protected_fingerprint", stale_rules)
        self.assertFalse(response["data"]["writes_state"])
        self.assertEqual(response["data"]["promotion_status"], "python_authoritative")
        self.assertEqual(stderr_records, response["diagnostics"])

        valid_packet = json.loads((PR_PACKET_FIXTURE_DIR / "valid-single.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            packet = Path(project) / "current-editable-packet.json"
            packet.write_text(
                json.dumps(
                    {
                        **valid_packet,
                        "packet_id": "current-editable-packet",
                        "body_file": (
                            PR_PACKET_FIXTURE_DIR / "bodies" / "valid-single-edited.md"
                        ).relative_to(REPO_ROOT).as_posix(),
                        "validation_result_path": (
                            "specs/prsg-012-reviewer-ready-pr-packet-contract/.process/"
                            "pr-packets/current-editable-packet/validation.json"
                        ),
                    }
                ),
                encoding="utf-8",
            )
            completed, response, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    {"packet_path": packet.relative_to(REPO_ROOT).as_posix()},
                )
            )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        self.assertEqual(response["data"]["stdout_json"]["status"], "passed")
        self.assertFalse(response["data"]["stdout_json"]["pr_blocked"])
        self.assertFalse(response["data"]["writes_state"])
        self.assertEqual(response["data"]["promotion_status"], "python_authoritative")
        self.assertEqual(stderr_records, [])

    def test_validate_pr_packet_reports_unsupported_platform_for_descriptorless_reads(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet unsupported-platform case")
        from speckit_pro_runner.helpers import read_only

        valid_packet_path = PR_PACKET_FIXTURE_DIR / "valid-single.json"
        with patch.object(read_only, "descriptor_read_supported", return_value=False):
            result = read_only.validate_pr_packet_read_only(
                {"packet_path": valid_packet_path.relative_to(REPO_ROOT).as_posix()},
                REPO_ROOT,
            )
        payload = json.loads(result["stdout"])
        self.assertEqual(result["exit_code"], 2)
        self.assertEqual(payload["error_class"], "unsupported_platform")
        self.assertEqual(payload["failures"][0]["rule"], "input.unsupported_platform")
        schema = json.loads(PR_PACKET_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            read_only.json_schema_failures(payload, schema["$defs"]["validation_result"], schema, "validation_result"),
            [],
        )

    def test_validate_pr_packet_rejects_packet_id_that_disagrees_with_filename(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet identity case")
        valid_packet = json.loads((PR_PACKET_FIXTURE_DIR / "valid-single.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            packet = Path(project) / "expected-id.json"
            packet.write_text(
                json.dumps(
                    {
                        **valid_packet,
                        "packet_id": "wrong-id",
                        "validation_result_path": (
                            "specs/prsg-012-reviewer-ready-pr-packet-contract/.process/"
                            "pr-packets/expected-id/validation.json"
                        ),
                    }
                ),
                encoding="utf-8",
            )
            completed, response, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    {"packet_path": packet.relative_to(REPO_ROOT).as_posix()},
                )
            )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        rules = {
            failure["rule"]
            for failure in response["data"]["stdout_json"]["failures"]
        }
        self.assertIn("input.identity.packet_id", rules)
        self.assertEqual(stderr_records, response["diagnostics"])

    def test_validate_pr_packet_fingerprint_covers_pre_h1_trailing_and_crossed_markers(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet protected body coverage case")
        valid_packet = json.loads((PR_PACKET_FIXTURE_DIR / "valid-single.json").read_text(encoding="utf-8"))
        body_text = (PR_PACKET_FIXTURE_DIR / "bodies" / "valid-single.md").read_text(encoding="utf-8")
        body_lines = body_text.splitlines()
        h1_index = next(index for index, line in enumerate(body_lines) if line.startswith("# "))
        late_h1_body = "\n".join(body_lines[:h1_index] + body_lines[h1_index + 1 :] + [body_lines[h1_index]]) + "\n"
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            cases = {
                "pre_h1": (
                    "<!-- unexpected protected preface -->\n" + body_text,
                    {"body.protected_fingerprint"},
                ),
                "trailing": (
                    body_text + "\n## Release Notes\n\nUnexpected protected trailer.\n",
                    {"body.protected_fingerprint"},
                ),
                "late_h1": (
                    late_h1_body,
                    {"body.title", "body.protected_fingerprint"},
                ),
                "crossed_marker": (
                    body_text.replace(
                        "<!-- speckit-pro-editable:summary:end -->\n\nSource:",
                        "Source:",
                        1,
                    ).replace(
                        "<!-- speckit-pro-editable:what_changed:start -->",
                        "<!-- speckit-pro-editable:what_changed:start -->\n<!-- speckit-pro-editable:summary:end -->",
                        1,
                    ),
                    {"body.editable_markers"},
                ),
            }
            for name, (mutated_body, expected_rules) in cases.items():
                with self.subTest(name=name):
                    body = project_path / f"{name}.md"
                    body.write_text(mutated_body, encoding="utf-8")
                    packet = project_path / f"{name}.json"
                    packet.write_text(
                        json.dumps(
                            {
                                **valid_packet,
                                "packet_id": f"{name}-packet",
                                "body_file": body.relative_to(REPO_ROOT).as_posix(),
                                "validation_result_path": (
                                    "specs/prsg-012-reviewer-ready-pr-packet-contract/.process/"
                                    f"pr-packets/{name}-packet/validation.json"
                                ),
                            }
                        ),
                        encoding="utf-8",
                    )
                    completed, response, stderr_records = run_runner(
                        helper_request(
                            "validate-pr-packet-read-only",
                            {"packet_path": packet.relative_to(REPO_ROOT).as_posix()},
                        )
                    )
                    self.assertEqual(completed.returncode, 1)
                    self.assert_response(response, "expected_failure", 1)
                    rules = {
                        failure["rule"]
                        for failure in response["data"]["stdout_json"]["failures"]
                    }
                    self.assertTrue(expected_rules.issubset(rules))
                    self.assertEqual(stderr_records, response["diagnostics"])

    def test_validate_pr_workflow_contract_changed_files_is_canonicalized_and_evaluated(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-workflow-contract":
            self.skipTest("validate-pr-workflow-contract changed-files case")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            changed_files = project_path / "changed-files.txt"
            changed_files.write_text(f"{ARCHIVED_FEATURE_DIR}/plan.md\n", encoding="utf-8")
            redundant_changed_files = f"{project_path.relative_to(REPO_ROOT).as_posix()}/../{project_path.name}/changed-files.txt"
            response = self.assert_helper_matches_bash_reference(
                "validate-pr-workflow-contract",
                {
                    "title": "feat(OTHER): Wrong scope",
                    "repo_root": ".",
                    "changed_files": redundant_changed_files,
                },
            )
        self.assertEqual(response["data"]["argv"][-2:], ["-m", "speckit_pro_runner"])
        failures = response["data"]["stdout_json"]["failures"]
        self.assertEqual(failures[0]["rule"], "title.spec_scope")

    def test_validate_pr_workflow_contract_unreadable_changed_files_is_input_error(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-workflow-contract":
            self.skipTest("validate-pr-workflow-contract changed-files read-error case")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            changed_files = Path(project) / "changed-files.txt"
            changed_files.write_text(f"{FEATURE_DIR}/plan.md\n", encoding="utf-8")
            from speckit_pro_runner.helpers import read_only

            with patch.object(read_only, "trusted_text", return_value=None):
                result = read_only.validate_pr_workflow_contract(
                    {
                        "title": "feat(XPLAT-005): Scope check",
                        "repo_root": ".",
                        "changed_files": changed_files.relative_to(REPO_ROOT).as_posix(),
                    },
                    REPO_ROOT,
                )
        self.assertEqual(result["exit_code"], 2)
        self.assertEqual(result["stdout"], "")
        self.assertIn("changed-files list not readable", result["stderr"])

    def test_validate_pr_workflow_contract_matches_bash_when_origin_main_is_missing(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-workflow-contract":
            self.skipTest("validate-pr-workflow-contract missing-origin case")
        from speckit_pro_runner.helpers.read_only import validate_pr_workflow_contract

        with patch("speckit_pro_runner.helpers.read_only.git_diff_changed_paths", return_value=None):
            result = validate_pr_workflow_contract(
                {
                    "title": "feat(XPLAT-005): Scope check",
                    "repo_root": ".",
                },
                REPO_ROOT,
            )
        self.assertEqual(result["exit_code"], 2)
        self.assertEqual(result["stdout"], "")
        self.assertIn("missing --changed-files and origin/main is unavailable", result["stderr"])

    def test_git_branch_rejects_untrusted_gitdir_pointer(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git branch pointer case uses check-prerequisites")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project, tempfile.TemporaryDirectory() as outside:
            project_path = Path(project)
            (project_path / ".git").write_text(f"gitdir: {outside}\n", encoding="utf-8")
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "")

    def test_git_branch_accepts_same_repo_worktree_metadata_name(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git branch worktree metadata case uses check-prerequisites")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as workspace, tempfile.TemporaryDirectory() as checkout_parent:
            project_path = Path(workspace) / REPO_ROOT.name
            project_path.mkdir()
            checkout_root = Path(checkout_parent) / REPO_ROOT.name
            git_dir = checkout_root / ".git" / "worktrees" / f"{REPO_ROOT.name}1"
            runner_dir = checkout_root / "speckit-pro" / "speckit_pro_runner"
            runner_dir.mkdir(parents=True)
            git_dir.mkdir(parents=True)
            (git_dir / "HEAD").write_text("ref: refs/heads/codex/xplat-008-archive-cleanup\n", encoding="utf-8")
            (project_path / ".git").write_text(f"gitdir: {git_dir}\n", encoding="utf-8")
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "codex/xplat-008-archive-cleanup")

    def test_trusted_text_returns_none_on_read_error(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("trusted text read-error case uses shared helper behavior")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            path = Path(project) / "unreadable.md"
            path.write_text("secret\n", encoding="utf-8")
            from speckit_pro_runner.helpers import read_only

            with patch.object(read_only.os, "open", side_effect=PermissionError("denied")):
                self.assertIsNone(read_only.trusted_text(path, REPO_ROOT))

    @unittest.skipIf(os.name == "nt", "POSIX no-follow descriptor behavior is not portable to Windows")
    def test_trusted_bytes_rejects_symlink_replacement_between_check_and_open(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("trusted bytes race case uses shared helper behavior")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project, tempfile.TemporaryDirectory() as outside:
            project_path = Path(project)
            target = project_path / "packet.json"
            target.write_text('{"packet": true}\n', encoding="utf-8")
            outside_file = Path(outside) / "outside.json"
            outside_file.write_text('{"outside": true}\n', encoding="utf-8")
            from speckit_pro_runner.helpers import read_only

            real_open = read_only.os.open
            swapped = False

            def swap_before_leaf_open(path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None):
                nonlocal swapped
                if path == "packet.json" and dir_fd is not None and not swapped:
                    target.unlink()
                    target.symlink_to(outside_file)
                    swapped = True
                return real_open(path, flags, mode, dir_fd=dir_fd)

            with patch.object(read_only.os, "open", side_effect=swap_before_leaf_open):
                self.assertIsNone(read_only.trusted_bytes(target, project_path))

    def test_git_branch_rejects_symlinked_git_paths(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git branch symlink case uses check-prerequisites")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project, tempfile.TemporaryDirectory() as outside:
            project_path = Path(project)
            outside_git = Path(outside) / "gitfile"
            outside_git.write_text("gitdir: /tmp/outside\n", encoding="utf-8")
            try:
                (project_path / ".git").symlink_to(outside_git)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "")

    def test_git_branch_reports_head_for_detached_checkout(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git branch detached-HEAD case uses check-prerequisites")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            git_dir = project_path / ".git"
            git_dir.mkdir()
            (git_dir / "HEAD").write_text("2d7388cc96f81cb805948bc19a8ccdd1cf896222\n", encoding="utf-8")
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "HEAD")

    def test_git_branch_rejects_symlinked_head_escape(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git HEAD symlink case uses check-prerequisites")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project, tempfile.TemporaryDirectory() as outside:
            project_path = Path(project)
            git_dir = project_path / ".git"
            git_dir.mkdir()
            outside_head = Path(outside) / "HEAD"
            outside_head.write_text("ref: refs/heads/external\n", encoding="utf-8")
            try:
                (git_dir / "HEAD").symlink_to(outside_head)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "")

    def test_repo_root_for_specs_path_uses_rightmost_specs_segment(self) -> None:
        if self.helper_filter and self.helper_filter != "o5-topology":
            self.skipTest("spec root inference case uses o5-topology")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            target = project_path / "outer" / "specs" / "container" / "repo" / "specs" / "feature"
            expected = project_path / "outer" / "specs" / "container" / "repo"
            from speckit_pro_runner.helpers.read_only import repo_root_for_specs_path

            self.assertEqual(repo_root_for_specs_path(target, project_path), expected.resolve(strict=False))

    def test_runtime_info_smoke_fixture_still_works(self) -> None:
        if self.helper_filter and self.helper_filter != "helper-registry-dispatch":
            self.skipTest("runtime smoke is registry-level")
        request = json.loads((FIXTURE_DIR / "smoke-runtime-info-request.json").read_text(encoding="utf-8"))
        completed, response, stderr_records = run_runner(request)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(stderr_records, [])
        self.assert_response(response, "ok", 0)
        self.assertEqual(response["data"]["report"]["runner_contract_id"], "speckit-pro-runner")

    def test_promoted_helper_runs_without_bash_on_path(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("no-Bash smoke is scoped to detect-commands")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            (project_path / "pnpm-lock.yaml").write_text("", encoding="utf-8")
            (project_path / "package.json").write_text(
                '{"scripts":{"build":"tsup","test":"vitest run"}}\n',
                encoding="utf-8",
            )
            completed, response, stderr_records = run_runner(
                helper_request("detect-commands", {"repo_root": project}),
                env_override={"PATH": "/nonexistent"},
            )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        self.assertEqual(response["data"]["stdout_json"]["stack"], "nodejs")
        self.assertEqual(stderr_records, [])

    def test_count_markers_modes_match_bash_reference(self) -> None:
        if self.helper_filter and self.helper_filter != "count-markers":
            self.skipTest("count-markers expanded parity cases")
        for marker_type in ("gaps", "findings", "clarifications", "all"):
            with self.subTest(marker_type=marker_type):
                self.assert_helper_matches_bash_reference(
                    "count-markers",
                    {"type": marker_type, "feature_dir": FEATURE_DIR},
                )

    def test_validate_gate_modes_match_bash_reference(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-gate":
            self.skipTest("validate-gate expanded parity cases")
        for gate in ("G1", "G2", "G3", "G4", "G5", "G6", "G7"):
            with self.subTest(gate=gate):
                self.assert_helper_matches_bash_reference(
                    "validate-gate",
                    {"gate": gate, "feature_dir": FEATURE_DIR},
                )

    def test_plan_layers_valid_real_preserves_legacy_increment_contract(self) -> None:
        if self.helper_filter and self.helper_filter != "plan-layers-feature-dir":
            self.skipTest("plan-layers valid fixture case")
        completed, response, planner = self.run_plan_layers(f"{PLAN_LAYERS_FIXTURE_DIR}/valid-real")
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        self.assertEqual(planner["status"], "ok")
        self.assertEqual(planner["summary"]["increment_count"], 4)
        self.assertEqual(planner["summary"]["task_count"], 8)
        increments = planner["increments"]
        self.assertEqual([increment["id"] for increment in increments], ["foundation", "us1", "us2", "polish"])
        self.assertEqual([increment["order"] for increment in increments], [0, 1, 2, 3])
        self.assertEqual(
            [increment["depends_on"] for increment in increments],
            [[], ["foundation"], ["us1"], ["us2"]],
        )
        tasks = {task["id"]: task for increment in increments for task in increment["tasks"]}
        self.assertEqual(len(tasks), 8)
        self.assertEqual(tasks["T003"]["status"], "done")
        self.assertTrue(tasks["T004"]["parallel"])
        self.assertEqual(tasks["T004"]["story"], "us1")
        self.assertEqual(tasks["T004"]["increment_id"], "us1")

    def test_plan_layers_dependency_cycle_is_invalid_plan(self) -> None:
        if self.helper_filter and self.helper_filter != "plan-layers-feature-dir":
            self.skipTest("plan-layers dependency-cycle case")
        completed, response, planner = self.run_plan_layers(f"{PLAN_LAYERS_FIXTURE_DIR}/dependency-cycle")
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        self.assertEqual(planner["status"], "invalid_plan")
        cycle_errors = [error for error in planner["errors"] if error["code"] == "dependency_cycle"]
        self.assertEqual(len(cycle_errors), 1)
        self.assertEqual(cycle_errors[0]["details"]["cycle"], ["us1", "us2", "us3", "us1"])

    def test_plan_layers_malformed_task_is_invalid_plan(self) -> None:
        if self.helper_filter and self.helper_filter != "plan-layers-feature-dir":
            self.skipTest("plan-layers malformed-task case")
        completed, response, planner = self.run_plan_layers(f"{PLAN_LAYERS_FIXTURE_DIR}/malformed-task")
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        self.assertEqual(planner["status"], "invalid_plan")
        self.assertEqual(
            {error["code"] for error in planner["errors"]},
            {"duplicate_task_id", "duplicate_increment_id", "malformed_task"},
        )

    def test_plan_layers_repository_bash_confinement_preserves_increment_contract(self) -> None:
        if self.helper_filter and self.helper_filter != "plan-layers-feature-dir":
            self.skipTest("plan-layers repository Bash confinement case")
        completed, response, stderr_records = run_runner(
            helper_request(
                "plan-layers-feature-dir",
                {"feature_dir": REPOSITORY_BASH_CONFINEMENT_PLAN_DIR},
            )
        )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        self.assertEqual(stderr_records, [])
        data = response["data"]
        stdout = data["stdout"]
        self.assertFalse(stdout["truncated"])
        self.assertEqual(stdout["limit_bytes"], PLAN_LAYERS_CAPTURE_LIMIT_BYTES)
        self.assertLessEqual(stdout["byte_count"], stdout["limit_bytes"])
        self.assertIn("stdout_json", data)
        planner = data["stdout_json"]
        self.assertEqual(planner["status"], "ok")
        self.assertEqual(planner["summary"]["increment_count"], 18)
        self.assertEqual(planner["summary"]["task_count"], 136)
        self.assertEqual(
            [increment["id"] for increment in planner["increments"]],
            ["foundation", "us1", "us16", *[f"us{number}" for number in range(2, 16)], "polish"],
        )
        self.assertEqual(planner["increments"][0]["depends_on"], [])
        self.assertEqual(planner["increments"][1]["depends_on"], ["foundation"])
        self.assertEqual(planner["increments"][2]["depends_on"], ["us1"])

    def test_helper_python_authoritative_records(self) -> None:
        for helper_id in self.filtered_helpers():
            if helper_id == "helper-registry-dispatch":
                continue
            with self.subTest(helper_id=helper_id):
                completed, response, stderr_records = run_runner(helper_request(helper_id, HELPER_CASES[helper_id]))
                data = response["data"]
                self.assertEqual(data["shell"], False)
                self.assertEqual(data["argv"][-2:], ["-m", "speckit_pro_runner"])
                self.assertEqual(data["python_operation"], helper_id)
                self.assertEqual(data["authoritative_command"].split(" < ", 1)[0], "python -m speckit_pro_runner")
                expected_stdout_limit = (
                    PLAN_LAYERS_CAPTURE_LIMIT_BYTES
                    if helper_id == "plan-layers-feature-dir"
                    else GENERIC_CAPTURE_LIMIT_BYTES
                )
                self.assertEqual(data["stdout"]["limit_bytes"], expected_stdout_limit)
                self.assertEqual(data["stderr"]["limit_bytes"], GENERIC_CAPTURE_LIMIT_BYTES)
                self.assertEqual(completed.returncode, response["exit_code"])
                self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])
                if data["exit_code"] == 0:
                    self.assert_response(response, "ok", 0)
                elif data["exit_code"] == 1:
                    self.assert_response(response, "expected_failure", 1)
                elif data["exit_code"] == 2:
                    self.assert_response(response, "input_error", 2)
                elif data["exit_code"] == 3:
                    self.assert_response(response, "missing_prerequisite", 3)
                else:
                    self.assert_response(response, "subprocess_failure", response["exit_code"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--helper", choices=EXPECTED_HELPERS)
    args = parser.parse_args()
    ReadOnlyHelperTests.helper_filter = args.helper
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReadOnlyHelperTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed
    print(f"test-speckit-pro-read-only-helpers: {passed}/{total} passed")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
