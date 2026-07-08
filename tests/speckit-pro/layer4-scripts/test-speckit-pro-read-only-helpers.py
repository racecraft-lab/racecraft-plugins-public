#!/usr/bin/env python3
"""Stdlib-only tests for XPLAT-005 read-only runner helpers."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "read-only-helpers"
FEATURE_DIR = "tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/xplat-005-feature"
ARCHIVED_FEATURE_DIR = "specs/xplat-005-read-only-helper-port"
WORKFLOW_FILE = "docs/ai/specs/.process/XPLAT-005-workflow.md"

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
    "validate-pr-packet-read-only": {"packet_path": "tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/missing-pr-packet.json"},
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


def run_bash_reference(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    real_argv = [str(REPO_ROOT / argv[0]), *argv[1:]]
    return subprocess.run(
        real_argv,
        text=True,
        capture_output=True,
        cwd=cwd or REPO_ROOT,
        env=runner_env(),
        shell=False,
        check=False,
    )


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
        replay = subprocess.run(
            data["argv"],
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
            from speckit_pro_runner.helpers.read_only import validate_pr_workflow_contract

            with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
                result = validate_pr_workflow_contract(
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
            from speckit_pro_runner.helpers.read_only import trusted_text

            with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
                self.assertIsNone(trusted_text(path, REPO_ROOT))

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
