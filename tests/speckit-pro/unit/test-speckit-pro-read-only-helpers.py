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
# resolve-autopilot-stage reads its workflow file, so its case needs one that is
# actually on disk; the archived XPLAT-005 record no longer is.
AUTOPILOT_STAGE_WORKFLOW_FILE = "docs/ai/specs/.process/ART-006-workflow.md"
PR_PACKET_FIXTURE_DIR = REPO_ROOT / "tests" / "speckit-pro" / "unit" / "fixtures" / "pr-packet"
DRAFT_PACKET_VALIDATION_DIR = "specs/art-007-draft-pr-emission/.process/pr-packets"
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
    "resolve-workflow-binding",
    "detect-commands",
    "detect-presets",
    "count-markers",
    "validate-gate",
    "reviewability-gate",
    "estimate-reviewable-loc",
    "resolve-confidence-mode",
    "resolve-autopilot-stage",
    "confidence-gate",
    "generate-spec-index-check",
    "o5-topology",
    "atomicity-route",
    "plan-layers-feature-dir",
    "validate-pr-workflow-contract",
    "validate-pr-packet-read-only",
    "estimate-spec-size",
    "sweep-pr-feedback",
    "sweep-isolation-session",
    "check-artifact-freshness",
]

JSON_STDOUT_PARITY_HELPERS = {"atomicity-route"}

# Helpers with no bash predecessor to compare against, so they carry no
# bash-reference record. `helper-registry-dispatch` is the runner's own registry
# view and never had a script; `resolve-autopilot-stage` is new behaviour with no
# deleted `.sh` ancestor, and inventing a `source_script` for it would record a
# lie in a provenance manifest. `sweep-pr-feedback` is new behaviour for the same
# reason: it reads an observation the orchestrator already took, so there was
# never a script to delete. `check-artifact-freshness` is new behaviour with no
# deleted `.sh` ancestor for the same reason, and inventing a `source_script` for
# it would record a lie in a provenance manifest.
NO_BASH_ANCESTOR = (
    "helper-registry-dispatch",
    "resolve-workflow-binding",
    "resolve-autopilot-stage",
    "sweep-pr-feedback",
    "sweep-isolation-session",
    "check-artifact-freshness",
)

HELPER_CASES: dict[str, dict[str, object]] = {
    "check-prerequisites": {"workflow_file": WORKFLOW_FILE},
    "resolve-workflow-binding": {"workflow_file": AUTOPILOT_STAGE_WORKFLOW_FILE},
    "detect-commands": {},
    "detect-presets": {},
    "count-markers": {"type": "all", "feature_dir": FEATURE_DIR},
    "validate-gate": {"gate": "G7", "feature_dir": FEATURE_DIR},
    "reviewability-gate": {"mode_name": "setup", "target": WORKFLOW_FILE},
    "estimate-reviewable-loc": {"plan_file": f"{FEATURE_DIR}/plan.md"},
    "resolve-confidence-mode": {"autopilot_args": ["--advisory", WORKFLOW_FILE]},
    "resolve-autopilot-stage": {
        "workflow_file": AUTOPILOT_STAGE_WORKFLOW_FILE,
        "autopilot_args": ["--stage", "plan"],
    },
    "confidence-gate": {"workflow_file": WORKFLOW_FILE, "mode_name": "advisory"},
    "generate-spec-index-check": {},
    "o5-topology": {"target": FEATURE_DIR},
    "atomicity-route": {"feature_dir": FEATURE_DIR},
    "plan-layers-feature-dir": {"feature_dir": FEATURE_DIR},
    "validate-pr-workflow-contract": {"title": "feat(XPLAT-005): Add read-only helper port"},
    "validate-pr-packet-read-only": {"packet_path": "tests/speckit-pro/unit/fixtures/read-only-helpers/missing-pr-packet.json"},
    "estimate-spec-size": {"user_stories": 2, "files": 3, "frs": 4},
    "sweep-pr-feedback": {
        "workflow_file": "docs/ai/specs/.process/ART-008-workflow.md",
        "self_login": "speckit-pro-bot",
        "feature_dir": "specs/art-008-feedback-sweep",
        "pr_observation": {
            "ok": True,
            "comments": [
                {
                    "id": "IC_kwDO...",
                    "surface": "pr_conversation",
                    "author": "octocat",
                    "author_association": "OWNER",
                    "body": (
                        "Artifact: Implementation Plan\nFeature: ART-008\n\n"
                        "Objections recorded while reviewing this plan.\n\n"
                        "Phase / Registry  (#phase-2)\n"
                        "The registry should cover every exporting template."
                    ),
                    "truncated": False,
                },
                {
                    "id": "PRRC_kwDO...",
                    "surface": "review_thread",
                    "author": None,
                    "author_association": "CONTRIBUTOR",
                    "body": "Drive-by suggestion.",
                    "truncated": False,
                    "thread_resolved": False,
                },
            ],
        },
    },
    "sweep-isolation-session": {"named_surface": "attest_claude"},
    "check-artifact-freshness": {
        "workflow_file": "docs/ai/specs/.process/ART-008-workflow.md",
        "artifacts_observation": {
            "ok": True,
            "artifacts_dir_state": "present",
            "last_artifacts_commit": "9f2c1ab8d4e5f60718293a4b5c6d7e8f90123456",
            "pages": ["implementation-plan", "spec-explainer"],
            "amended_commits": [
                {
                    "cell": "a1b2c3d",
                    "resolved": True,
                    "is_ancestor_of_artifacts_commit": True,
                },
            ],
        },
    },
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

    def build_binding_worktrees(self, base: Path) -> tuple[Path, Path, Path]:
        task_root = base / "repo"
        descendant_root = task_root / ".worktrees" / "nested"
        external_root = base / "external"
        task_root.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main", str(task_root)],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(task_root), "config", "user.email", "support@openai.com"],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(task_root), "config", "user.name", "SpecKit Tests"],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(task_root), "config", "commit.gpgsign", "false"],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        (task_root / "seed.txt").write_text("seed\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(task_root), "add", "seed.txt"],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(task_root), "commit", "-m", "seed"],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(task_root), "worktree", "add", "-b", "nested", str(descendant_root)],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(task_root), "worktree", "add", "-b", "external", str(external_root)],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        return task_root, descendant_root, external_root

    def binding_result(self, task_root: Path, workflow_file: str) -> tuple[dict[str, object], int]:
        from speckit_pro_runner.helpers.read_only import resolve_workflow_binding

        result = resolve_workflow_binding({"workflow_file": workflow_file}, task_root)
        return json.loads(result["stdout"]), int(result["exit_code"])

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
        self.assertEqual(bash_ids, [helper for helper in EXPECTED_HELPERS if helper not in NO_BASH_ANCESTOR])
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

    def test_resolve_workflow_binding_covers_registered_worktree_relations(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        with tempfile.TemporaryDirectory() as temp:
            task_root, descendant_root, external_root = self.build_binding_worktrees(Path(temp))

            same_file = task_root / "same-workflow.md"
            same_file.write_text("# same\n", encoding="utf-8")
            payload, exit_code = self.binding_result(task_root, same_file.name)
            self.assertEqual((payload["binding_status"], payload["relation"], exit_code), ("resolved", "same", 0))
            self.assertEqual(payload["workflow_root"], task_root.resolve().as_posix())

            nested_file = descendant_root / "nested-workflow.md"
            nested_file.write_text("# nested\n", encoding="utf-8")
            payload, exit_code = self.binding_result(task_root, nested_file.name)
            self.assertEqual(
                (payload["binding_status"], payload["relation"], exit_code),
                ("resolved", "descendant", 0),
            )
            self.assertEqual(payload["workflow_root"], descendant_root.resolve().as_posix())

            rebound, exit_code = self.binding_result(descendant_root, str(nested_file))
            self.assertEqual(
                (rebound["binding_status"], rebound["relation"], exit_code),
                ("resolved", "same", 0),
            )
            self.assertEqual(rebound["task_root"], descendant_root.resolve().as_posix())
            self.assertEqual(rebound["workflow_root"], descendant_root.resolve().as_posix())
            self.assertEqual(rebound["workflow_file"], nested_file.resolve().as_posix())

            external_file = external_root / "external-workflow.md"
            external_file.write_text("# external\n", encoding="utf-8")
            payload, exit_code = self.binding_result(task_root, external_file.name)
            self.assertEqual(
                (payload["binding_status"], payload["relation"], exit_code),
                ("resolved", "external", 0),
            )
            self.assertEqual(payload["workflow_root"], external_root.resolve().as_posix())

    def test_registered_worktree_roots_ignores_only_explicitly_prunable_entries(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        from speckit_pro_runner.helpers import read_only

        canonical_root = REPO_ROOT.resolve()
        missing_root = Path("/missing-prunable-worktree")
        output = (
            f"worktree {canonical_root}\0HEAD abc\0branch refs/heads/main\0\0"
            f"worktree {missing_root}\0HEAD def\0prunable gitdir file points to a missing location\0\0"
        )
        original_resolve = Path.resolve

        def guarded_resolve(path: Path, strict: bool = False) -> Path:
            if path == missing_root:
                raise AssertionError("prunable roots must not be canonicalized")
            return original_resolve(path, strict=strict)

        completed = SimpleNamespace(returncode=0, stdout=output, stderr="")
        with patch.object(read_only.subprocess, "run", return_value=completed), patch.object(
            Path, "resolve", guarded_resolve
        ):
            roots, error = read_only.registered_worktree_roots(canonical_root)

        self.assertEqual(roots, [canonical_root])
        self.assertIsNone(error)

    def test_registered_worktree_roots_fails_closed_on_unreadable_registered_entry(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        from speckit_pro_runner.helpers import read_only

        canonical_root = REPO_ROOT.resolve()
        denied_root = Path("/denied-registered-worktree")
        output = (
            f"worktree {canonical_root}\0HEAD abc\0branch refs/heads/main\0\0"
            f"worktree {denied_root}\0HEAD def\0branch refs/heads/feature\0\0"
        )
        original_resolve = Path.resolve

        def guarded_resolve(path: Path, strict: bool = False) -> Path:
            if path == denied_root:
                raise PermissionError("sandbox denied")
            return original_resolve(path, strict=strict)

        completed = SimpleNamespace(returncode=0, stdout=output, stderr="")
        with patch.object(read_only.subprocess, "run", return_value=completed), patch.object(
            Path, "resolve", guarded_resolve
        ):
            roots, error = read_only.registered_worktree_roots(canonical_root)

        self.assertEqual(roots, [])
        self.assertIn("registered worktree cannot be canonicalized", error or "")
        self.assertIn(denied_root.as_posix(), error or "")
        self.assertIn("sandbox denied", error or "")

    def test_resolve_workflow_binding_absolute_path_uses_longest_registered_root(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        with tempfile.TemporaryDirectory() as temp:
            task_root, descendant_root, _ = self.build_binding_worktrees(Path(temp))
            relative = Path("specs") / "workflow.md"
            (task_root / relative).parent.mkdir()
            (descendant_root / relative).parent.mkdir()
            (task_root / relative).write_text("# stale parent copy\n", encoding="utf-8")
            (descendant_root / relative).write_text("# nested owner\n", encoding="utf-8")

            payload, exit_code = self.binding_result(task_root, str(descendant_root / relative))
            self.assertEqual(
                (payload["binding_status"], payload["relation"], exit_code),
                ("resolved", "descendant", 0),
            )
            self.assertEqual(payload["workflow_root"], descendant_root.resolve().as_posix())
            self.assertEqual(payload["workflow_file"], (descendant_root / relative).resolve().as_posix())

            rebound, exit_code = self.binding_result(descendant_root, str(descendant_root / relative))
            self.assertEqual(
                (rebound["binding_status"], rebound["relation"], exit_code),
                ("resolved", "same", 0),
            )
            self.assertEqual(rebound["workflow_root"], descendant_root.resolve().as_posix())
            self.assertEqual(rebound["workflow_file"], (descendant_root / relative).resolve().as_posix())

    def test_resolve_workflow_binding_rejects_external_symlink_alias_into_worktree(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            task_root, descendant_root, _ = self.build_binding_worktrees(base)
            workflow = descendant_root / "aliased-workflow.md"
            workflow.write_text("# registered target\n", encoding="utf-8")
            alias = base / "workflow-link"
            try:
                alias.symlink_to(descendant_root, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            payload, exit_code = self.binding_result(task_root, str(alias / workflow.name))

            self.assertEqual((payload["binding_status"], exit_code), ("invalid", 1))
            self.assertIsNone(payload["relation"])
            self.assertEqual(payload["candidates"], [])
            self.assertIn("outside every registered worktree", payload["problems"][0])

    def test_resolve_workflow_binding_allows_in_worktree_symlink_with_same_owner(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            task_root, descendant_root, _ = self.build_binding_worktrees(base)
            target_dir = descendant_root / "workflow-target"
            target_dir.mkdir()
            workflow = target_dir / "workflow.md"
            workflow.write_text("# same owner\n", encoding="utf-8")
            alias = descendant_root / "workflow-link"
            try:
                alias.symlink_to(target_dir, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            payload, exit_code = self.binding_result(task_root, str(alias / workflow.name))

            self.assertEqual(
                (payload["binding_status"], payload["relation"], exit_code),
                ("resolved", "descendant", 0),
            )
            self.assertEqual(payload["workflow_root"], descendant_root.resolve().as_posix())
            self.assertEqual(payload["workflow_file"], workflow.resolve().as_posix())

    def test_resolve_workflow_binding_rejects_ambiguous_missing_and_unregistered_paths(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            task_root, descendant_root, _ = self.build_binding_worktrees(base)
            duplicate = Path("duplicate-workflow.md")
            (task_root / duplicate).write_text("# parent\n", encoding="utf-8")
            (descendant_root / duplicate).write_text("# nested\n", encoding="utf-8")

            payload, exit_code = self.binding_result(task_root, duplicate.as_posix())
            self.assertEqual((payload["binding_status"], exit_code), ("ambiguous", 1))
            self.assertEqual(
                payload["candidates"],
                [task_root.resolve().as_posix(), descendant_root.resolve().as_posix()],
            )

            payload, exit_code = self.binding_result(task_root, "missing-workflow.md")
            self.assertEqual((payload["binding_status"], exit_code), ("missing", 1))

            payload, exit_code = self.binding_result(task_root, str(descendant_root / "missing-absolute.md"))
            self.assertEqual((payload["binding_status"], exit_code), ("missing", 1))

            invalid_directory = descendant_root / "not-a-workflow.md"
            invalid_directory.mkdir()
            payload, exit_code = self.binding_result(task_root, invalid_directory.name)
            self.assertEqual((payload["binding_status"], exit_code), ("invalid", 1))

            unregistered = base / "unregistered" / "workflow.md"
            unregistered.parent.mkdir()
            unregistered.write_text("# unregistered\n", encoding="utf-8")
            payload, exit_code = self.binding_result(task_root, str(unregistered))
            self.assertEqual((payload["binding_status"], exit_code), ("invalid", 1))

    def test_resolve_workflow_binding_rejects_symlink_escape(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            task_root, descendant_root, external_root = self.build_binding_worktrees(base)
            outside = base / "outside-workflow.md"
            outside.write_text("# outside\n", encoding="utf-8")
            parent = task_root / "parent-workflow.md"
            parent.write_text("# parent\n", encoding="utf-8")
            sibling = external_root / "sibling-workflow.md"
            sibling.write_text("# sibling\n", encoding="utf-8")
            links = [
                (descendant_root / "outside-escape-workflow.md", outside),
                (descendant_root / "parent-escape-workflow.md", parent),
                (descendant_root / "sibling-escape-workflow.md", sibling),
            ]
            try:
                for link, target in links:
                    link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            for link, _ in links:
                with self.subTest(link=link.name):
                    payload, exit_code = self.binding_result(task_root, str(link))
                    self.assertEqual((payload["binding_status"], exit_code), ("invalid", 1))
                    self.assertTrue(payload["problems"])

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

    def test_validate_pr_packet_enforces_canonical_packet_owned_paths(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet canonical ownership case")
        valid_packet = json.loads((PR_PACKET_FIXTURE_DIR / "valid-single.json").read_text(encoding="utf-8"))
        specs_root = REPO_ROOT / "specs"
        with tempfile.TemporaryDirectory(prefix="packet-identity-", dir=specs_root) as feature:
            feature_dir = Path(feature)
            source_feature_dir = feature_dir.relative_to(REPO_ROOT).as_posix()
            packet_id = "valid-single"
            packet_root = feature_dir / ".process" / "pr-packets"
            body_path = packet_root / packet_id / "body.md"
            body_path.parent.mkdir(parents=True)
            body_path.write_text(
                (PR_PACKET_FIXTURE_DIR / "bodies" / "valid-single.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            packet_path = packet_root / f"{packet_id}.json"
            canonical_packet = {
                **valid_packet,
                "packet_id": packet_id,
                "source_feature_dir": source_feature_dir,
                "body_file": body_path.relative_to(REPO_ROOT).as_posix(),
                "validation_result_path": f"{source_feature_dir}/.process/pr-packets/{packet_id}/validation.json",
            }
            packet_path.write_text(json.dumps(canonical_packet), encoding="utf-8")
            completed, response, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    {"packet_path": packet_path.relative_to(REPO_ROOT).as_posix()},
                )
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])

            cases = {
                "source_mismatch": (
                    {"source_feature_dir": "specs/other-feature"},
                    "input.identity.source_feature_dir",
                ),
                "body_mismatch": (
                    {"body_file": (PR_PACKET_FIXTURE_DIR / "bodies" / "valid-single.md").relative_to(REPO_ROOT).as_posix()},
                    "input.identity.body_file",
                ),
                "validation_mismatch": (
                    {"validation_result_path": f"{source_feature_dir}/.process/pr-packets/other/validation.json"},
                    "input.identity.validation_result_path",
                ),
            }
            for name, (overrides, expected_rule) in cases.items():
                with self.subTest(name=name):
                    packet_path.write_text(
                        json.dumps({**canonical_packet, **overrides}),
                        encoding="utf-8",
                    )
                    completed, response, stderr_records = run_runner(
                        helper_request(
                            "validate-pr-packet-read-only",
                            {"packet_path": packet_path.relative_to(REPO_ROOT).as_posix()},
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

    def draft_packet_fixture(self) -> dict[str, object]:
        return json.loads((PR_PACKET_FIXTURE_DIR / "valid-draft.json").read_text(encoding="utf-8"))

    def draft_packet_variant(self, packet_id: str, **overrides: object) -> dict[str, object]:
        """Re-own a draft packet copy so identity checks stay quiet on the variant."""
        return {
            **self.draft_packet_fixture(),
            "packet_id": packet_id,
            "validation_result_path": f"{DRAFT_PACKET_VALIDATION_DIR}/{packet_id}/validation.json",
            **overrides,
        }

    def packet_failure_rules(self, packet: Path) -> set[str]:
        completed, response, stderr_records = run_runner(
            helper_request(
                "validate-pr-packet-read-only",
                {"packet_path": packet.relative_to(REPO_ROOT).as_posix()},
            )
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        self.assertEqual(stderr_records, response["diagnostics"])
        return {failure["rule"] for failure in response["data"]["stdout_json"]["failures"]}

    def test_validate_pr_packet_accepts_draft_without_verification_or_uat_evidence(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet draft acceptance case")
        draft_packet = self.draft_packet_fixture()
        self.assertEqual(draft_packet["verification_evidence"], [])
        self.assertEqual(draft_packet["scope_evidence"]["changed_files"], [])
        self.assertEqual(draft_packet["uat"]["how_to_uat"], "")
        self.assertEqual(draft_packet["uat"]["uat_runbook_heading"], "")
        self.assertTrue(draft_packet["uat"]["uat_source"])
        # Non-goals are the one piece of scope evidence a plan stage already has,
        # so draft mode must not relax them.
        self.assertTrue(draft_packet["scope_evidence"]["non_goals"])
        self.assertEqual(draft_packet["required_headings"], ["Artifacts", "Resume"])
        self.assertEqual(draft_packet["editable_fields"], [])
        self.assertEqual(draft_packet["protected_body_fingerprint"]["elided_fields"], [])
        self.assertNotIn("split_slice", draft_packet)

        completed, response, stderr_records = run_runner(
            helper_request(
                "validate-pr-packet-read-only",
                {
                    "packet_path": (PR_PACKET_FIXTURE_DIR / "valid-draft.json")
                    .relative_to(REPO_ROOT)
                    .as_posix()
                },
            )
        )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        payload = response["data"]["stdout_json"]
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["mode"], "draft")
        self.assertEqual(payload["failures"], [])
        self.assertFalse(payload["pr_blocked"])
        self.assertEqual(set(payload["source_fingerprints"]), {"body", "packet"})
        self.assertFalse(response["data"]["writes_state"])
        self.assertEqual(stderr_records, [])

        from speckit_pro_runner.helpers import read_only

        # The validation_result mode enum is the schema's second mode site. If only
        # the top-level enum learns draft, a passing draft packet's own validation
        # record stays unrepresentable.
        schema = json.loads(PR_PACKET_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            read_only.json_schema_failures(
                payload, schema["$defs"]["validation_result"], schema, "validation_result"
            ),
            [],
        )

    def test_validate_pr_packet_rejects_draft_that_carries_split_slice(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet draft split_slice case")
        split_packet = json.loads(
            (PR_PACKET_FIXTURE_DIR / "valid-split.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            packet = Path(project) / "draft-with-slice.json"
            packet.write_text(
                json.dumps(
                    self.draft_packet_variant(
                        "draft-with-slice",
                        split_slice=split_packet["split_slice"],
                    )
                ),
                encoding="utf-8",
            )
            rules = self.packet_failure_rules(packet)
        # Only the split branch's else arm may object: a schema-clean split_slice
        # on a draft packet is forbidden, and nothing else about the packet is.
        self.assertEqual(rules, {"packet.schema.not"})

    def test_validate_pr_packet_rejects_draft_body_missing_a_required_heading(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet draft heading case")
        from speckit_pro_runner.helpers import read_only

        body_text = (PR_PACKET_FIXTURE_DIR / "bodies" / "valid-draft.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            for heading in ("## Artifacts", "## Resume"):
                packet_id = f"draft-missing-{heading[3:].lower()}"
                with self.subTest(missing=heading):
                    mutated = (
                        "\n".join(line for line in body_text.splitlines() if line != heading) + "\n"
                    )
                    body = project_path / f"{packet_id}.md"
                    body.write_text(mutated, encoding="utf-8")
                    packet = project_path / f"{packet_id}.json"
                    packet.write_text(
                        json.dumps(
                            self.draft_packet_variant(
                                packet_id,
                                body_file=body.relative_to(REPO_ROOT).as_posix(),
                                protected_body_fingerprint={
                                    **self.draft_packet_fixture()["protected_body_fingerprint"],
                                    "value": read_only.protected_body_sha256(mutated),
                                },
                            )
                        ),
                        encoding="utf-8",
                    )
                    # Fingerprint is recomputed for the mutated body, so the missing
                    # heading is the only thing left for the validator to object to.
                    self.assertEqual(self.packet_failure_rules(packet), {"body.required_headings"})

    def test_validate_pr_packet_accepts_draft_body_whose_artifacts_table_holds_only_gap_rows(
        self,
    ) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet draft zero-artifact case")
        from speckit_pro_runner.helpers import read_only

        draft_packet = self.draft_packet_fixture()
        gap_body = (
            f"# {draft_packet['generated_title']['value']}\n"
            "\n"
            "## Artifacts\n"
            "\n"
            "| Artifact | Purpose | Open |\n"
            "| --- | --- | --- |\n"
            "| Gap: Implementation Plan | Not generated for this run. | Not available |\n"
            "| Gap: Spec Explainer | Not generated for this run. | Not available |\n"
            "\n"
            "## Resume\n"
            "\n"
            "Stage: plan, stopped at the plan-stage boundary for review.\n"
            "Resume with: `/speckit-pro:speckit-autopilot <workflow-file> --stage implement`\n"
        )
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            body = project_path / "draft-gap-rows.md"
            body.write_text(gap_body, encoding="utf-8")
            packet = project_path / "draft-gap-rows.json"
            packet.write_text(
                json.dumps(
                    self.draft_packet_variant(
                        "draft-gap-rows",
                        body_file=body.relative_to(REPO_ROOT).as_posix(),
                        protected_body_fingerprint={
                            **draft_packet["protected_body_fingerprint"],
                            "value": read_only.protected_body_sha256(gap_body),
                        },
                    )
                ),
                encoding="utf-8",
            )
            completed, response, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    {"packet_path": packet.relative_to(REPO_ROOT).as_posix()},
                )
            )
        # FR-004 / FR-008: a run that generated no artifact still opens a valid draft.
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        self.assertEqual(response["data"]["stdout_json"]["status"], "passed")
        self.assertEqual(response["data"]["stdout_json"]["failures"], [])
        self.assertEqual(stderr_records, [])

    def test_validate_pr_packet_still_rejects_an_unknown_mode_value(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet unknown mode case")
        valid_packet = json.loads(
            (PR_PACKET_FIXTURE_DIR / "valid-single.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            packet = Path(project) / "unknown-mode.json"
            for mode in ("sketch", "DRAFT", ""):
                with self.subTest(mode=mode):
                    packet.write_text(
                        json.dumps(
                            {
                                **valid_packet,
                                "packet_id": "unknown-mode",
                                "mode": mode,
                                "validation_result_path": (
                                    "specs/prsg-012-reviewer-ready-pr-packet-contract/.process/"
                                    "pr-packets/unknown-mode/validation.json"
                                ),
                            }
                        ),
                        encoding="utf-8",
                    )
                    # Widening the enum to admit draft must not admit anything else,
                    # and the enum stays case-sensitive.
                    self.assertEqual(self.packet_failure_rules(packet), {"packet.schema.enum"})

    def test_validate_pr_packet_rejects_draft_required_headings_other_than_the_two_draft_blocks(
        self,
    ) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet draft required-headings case")
        cases = {
            "too-few": (["Artifacts"], {"packet.schema.min_items"}),
            "out-of-order": (
                ["Resume", "Artifacts"],
                {"packet.schema.const", "body.required_headings"},
            ),
            "too-many": (
                ["Artifacts", "Resume", "Known Gaps"],
                {"packet.schema.max_items", "body.required_headings"},
            ),
        }
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            for name, (required_headings, expected_rules) in cases.items():
                with self.subTest(name=name):
                    packet_id = f"draft-headings-{name}"
                    packet = project_path / f"{packet_id}.json"
                    packet.write_text(
                        json.dumps(
                            self.draft_packet_variant(
                                packet_id, required_headings=required_headings
                            )
                        ),
                        encoding="utf-8",
                    )
                    self.assertEqual(self.packet_failure_rules(packet), expected_rules)

    def test_validate_pr_packet_rejects_draft_that_declares_editable_fields(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet draft editable-fields case")
        valid_packet = json.loads(
            (PR_PACKET_FIXTURE_DIR / "valid-single.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            packet = Path(project) / "draft-editable-fields.json"
            packet.write_text(
                json.dumps(
                    self.draft_packet_variant(
                        "draft-editable-fields",
                        editable_fields=valid_packet["editable_fields"][:1],
                    )
                ),
                encoding="utf-8",
            )
            rules = self.packet_failure_rules(packet)
        # The schema caps draft editable_fields at zero, and the draft body carries
        # no editable markers for the declared field to bind to.
        self.assertEqual(rules, {"packet.schema.max_items", "body.editable_markers"})

    def test_validate_pr_packet_still_rejects_single_required_headings_that_are_not_reviewer_set(
        self,
    ) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet single required-headings regression case")
        valid_packet = json.loads(
            (PR_PACKET_FIXTURE_DIR / "valid-single.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            packet = Path(project) / "single-draft-headings.json"
            packet.write_text(
                json.dumps(
                    {
                        **valid_packet,
                        "packet_id": "single-draft-headings",
                        "required_headings": ["Artifacts", "Resume"],
                        "validation_result_path": (
                            "specs/prsg-012-reviewer-ready-pr-packet-contract/.process/"
                            "pr-packets/single-draft-headings/validation.json"
                        ),
                    }
                ),
                encoding="utf-8",
            )
            rules = self.packet_failure_rules(packet)
        # SC-008: moving the eight-heading pin into the else arm must keep binding
        # single mode. If the else arm were omitted, only body.required_headings
        # would survive here.
        self.assertEqual(
            rules,
            {"packet.schema.const", "packet.schema.min_items", "body.required_headings"},
        )

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

    @staticmethod
    def _build_linked_worktree(
        workspace: Path,
        checkout_parent: Path,
        *,
        worktree_relpath: str,
        branch: str,
        backpointer: str | None = "self",
        admin_name: str | None = None,
    ) -> Path:
        """Build a git worktree the way git actually lays one out.

        Git records the link in both directions: the worktree's ``.git`` file
        points at ``<checkout>/.git/worktrees/<name>``, and that admin directory
        holds a ``gitdir`` file pointing back at the worktree's own ``.git``.
        ``backpointer`` selects what the admin directory records — ``"self"`` for
        the honest link, ``None`` to omit it, or a literal path to forge one.
        """
        project_path = workspace / worktree_relpath
        project_path.mkdir(parents=True)
        checkout_root = checkout_parent / REPO_ROOT.name
        git_dir = checkout_root / ".git" / "worktrees" / (admin_name or Path(worktree_relpath).name)
        (checkout_root / "speckit-pro" / "speckit_pro_runner").mkdir(parents=True)
        git_dir.mkdir(parents=True)
        (git_dir / "HEAD").write_text(f"ref: refs/heads/{branch}\n", encoding="utf-8")
        (project_path / ".git").write_text(f"gitdir: {git_dir}\n", encoding="utf-8")
        if backpointer == "self":
            (git_dir / "gitdir").write_text(f"{project_path / '.git'}\n", encoding="utf-8")
        elif backpointer is not None:
            (git_dir / "gitdir").write_text(f"{backpointer}\n", encoding="utf-8")
        return project_path

    def test_git_branch_accepts_worktree_named_for_its_branch(self) -> None:
        """The repository's own convention: .worktrees/<branch-name>.

        The worktree directory is named for the branch, never for the checkout,
        so a check that compares those two names rejects every feature worktree
        this repository creates.
        """
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git branch worktree metadata case uses check-prerequisites")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as workspace, tempfile.TemporaryDirectory() as checkout_parent:
            project_path = self._build_linked_worktree(
                Path(workspace),
                Path(checkout_parent),
                worktree_relpath=".worktrees/codex-xplat-008-archive-cleanup",
                branch="codex/xplat-008-archive-cleanup",
            )
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "codex/xplat-008-archive-cleanup")

    def test_git_branch_accepts_same_repo_worktree_metadata_name(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git branch worktree metadata case uses check-prerequisites")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as workspace, tempfile.TemporaryDirectory() as checkout_parent:
            project_path = self._build_linked_worktree(
                Path(workspace),
                Path(checkout_parent),
                worktree_relpath=REPO_ROOT.name,
                branch="codex/xplat-008-archive-cleanup",
                admin_name=f"{REPO_ROOT.name}1",
            )
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "codex/xplat-008-archive-cleanup")

    def test_git_branch_rejects_worktree_metadata_without_backpointer(self) -> None:
        """A same-named directory is not proof of ownership.

        Name equality alone lets an unrelated checkout that merely shares a
        directory name supply HEAD. Git's own back-pointer is what proves the
        admin directory belongs to this worktree.
        """
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git branch worktree metadata case uses check-prerequisites")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as workspace, tempfile.TemporaryDirectory() as checkout_parent:
            project_path = self._build_linked_worktree(
                Path(workspace),
                Path(checkout_parent),
                worktree_relpath=REPO_ROOT.name,
                branch="codex/xplat-008-archive-cleanup",
                backpointer=None,
            )
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "")

    def test_git_branch_rejects_worktree_metadata_pointing_elsewhere(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git branch worktree metadata case uses check-prerequisites")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as workspace, tempfile.TemporaryDirectory() as checkout_parent, tempfile.TemporaryDirectory() as other:
            project_path = self._build_linked_worktree(
                Path(workspace),
                Path(checkout_parent),
                worktree_relpath=REPO_ROOT.name,
                branch="codex/xplat-008-archive-cleanup",
                backpointer=f"{Path(other) / '.git'}",
            )
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "")

    @staticmethod
    def _feature_state(project_path: Path, **inputs: object) -> dict[str, object]:
        from speckit_pro_runner.helpers.read_only import check_prerequisites

        result = check_prerequisites(dict(inputs), project_path)
        return json.loads(result["stdout"])

    def test_check_prerequisites_honors_feature_json_feature_directory(self) -> None:
        """`.specify/feature.json` is the sanctioned feature-state carrier.

        The vendored resolver reads it (scripts/bash/common.sh), so the runner
        must agree; otherwise the two implementations disagree about whether a
        run is on a feature, which is every spec this repository ships on a
        non-numeric branch.
        """
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("feature-state precedence case uses check-prerequisites")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            (project_path / ".specify").mkdir()
            (project_path / ".specify" / "feature.json").write_text(
                '{"feature_directory":"specs/art-006-autopilot-staging"}\n', encoding="utf-8"
            )
            payload = self._feature_state(project_path)
            self.assertTrue(payload["on_feature_branch"])

    def test_check_prerequisites_honors_specify_feature_directory_env(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("feature-state precedence case uses check-prerequisites")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            (project_path / ".specify").mkdir()
            with patch.dict(
                os.environ, {"SPECIFY_FEATURE_DIRECTORY": "specs/car-005-availability"}, clear=False
            ):
                payload = self._feature_state(project_path)
            self.assertTrue(payload["on_feature_branch"])

    def test_check_prerequisites_reports_no_feature_without_state_or_branch(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("feature-state precedence case uses check-prerequisites")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            (project_path / ".specify").mkdir()
            environment = {
                key: value
                for key, value in os.environ.items()
                if key not in {"SPECIFY_FEATURE_DIRECTORY", "SPECIFY_FEATURE"}
            }
            with patch.dict(os.environ, environment, clear=True):
                payload = self._feature_state(project_path)
            self.assertFalse(payload["on_feature_branch"])

    def test_check_prerequisites_ignores_blank_feature_directory(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("feature-state precedence case uses check-prerequisites")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            (project_path / ".specify").mkdir()
            (project_path / ".specify" / "feature.json").write_text(
                '{"feature_directory":"   "}\n', encoding="utf-8"
            )
            environment = {
                key: value
                for key, value in os.environ.items()
                if key not in {"SPECIFY_FEATURE_DIRECTORY", "SPECIFY_FEATURE"}
            }
            with patch.dict(os.environ, environment, clear=True):
                payload = self._feature_state(project_path)
            self.assertFalse(payload["on_feature_branch"])

    @staticmethod
    def _detected(project_path: Path) -> dict[str, object]:
        from speckit_pro_runner.helpers.read_only import detect_commands

        return json.loads(detect_commands({}, project_path)["stdout"])

    def test_detect_commands_finds_repository_test_runner(self) -> None:
        """A runner script under tests/ is real, verifiable evidence of a test command.

        A repository can be pure-stdlib Python with no packaging marker at all;
        returning every command as N/A there reads as "this project has no
        tests" rather than "the detector stopped at the repository root".
        """
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("test-runner discovery case uses detect-commands")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            (project_path / "tests" / "suite").mkdir(parents=True)
            (project_path / "tests" / "suite" / "run-all.py").write_text("", encoding="utf-8")
            payload = self._detected(project_path)
            self.assertEqual("python", payload["stack"])
            self.assertEqual("python3 tests/suite/run-all.py", payload["commands"]["UNIT_TEST"])
            self.assertEqual("python3 tests/suite/run-all.py", payload["commands"]["FULL_VERIFY"])
            self.assertEqual("test_runner_script", payload["detection"]["source"])
            self.assertEqual("tests/suite/run-all.py", payload["detection"]["evidence"])

    def test_detect_commands_recognizes_python_without_pyproject(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("python marker case uses detect-commands")
        for marker in ("requirements.txt", "setup.py", "setup.cfg", "tox.ini", "pytest.ini", "Pipfile"):
            with self.subTest(marker=marker):
                with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
                    project_path = Path(project)
                    (project_path / marker).write_text("", encoding="utf-8")
                    payload = self._detected(project_path)
                    self.assertEqual("python", payload["stack"])
                    self.assertEqual("pytest", payload["commands"]["UNIT_TEST"])
                    self.assertEqual(marker, payload["detection"]["evidence"])

    def test_detect_commands_prefers_root_marker_over_runner_script(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("precedence case uses detect-commands")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            (project_path / "pyproject.toml").write_text("", encoding="utf-8")
            (project_path / "tests" / "suite").mkdir(parents=True)
            (project_path / "tests" / "suite" / "run-all.py").write_text("", encoding="utf-8")
            payload = self._detected(project_path)
            self.assertEqual("pytest", payload["commands"]["UNIT_TEST"])
            self.assertEqual("root_marker", payload["detection"]["source"])

    def test_detect_commands_runner_discovery_is_deterministic(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("determinism case uses detect-commands")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            project_path = Path(project)
            for sub in ("zeta", "alpha"):
                (project_path / "tests" / sub).mkdir(parents=True)
                (project_path / "tests" / sub / "run-all.py").write_text("", encoding="utf-8")
            first = self._detected(project_path)["commands"]["UNIT_TEST"]
            self.assertEqual("python3 tests/alpha/run-all.py", first)
            for _ in range(3):
                self.assertEqual(first, self._detected(project_path)["commands"]["UNIT_TEST"])

    def test_detect_commands_reports_what_it_searched_when_nothing_found(self) -> None:
        """An empty result must say it looked, not just return a wall of N/A."""
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("no-detection case uses detect-commands")
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as project:
            payload = self._detected(Path(project))
            self.assertEqual("unknown", payload["stack"])
            self.assertEqual("none", payload["detection"]["source"])
            self.assertEqual("", payload["detection"]["evidence"])
            searched = payload["detection"]["searched"]
            self.assertIn("pyproject.toml", searched)
            self.assertIn("package.json", searched)
            self.assertTrue(payload["detection"]["hint"])

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
