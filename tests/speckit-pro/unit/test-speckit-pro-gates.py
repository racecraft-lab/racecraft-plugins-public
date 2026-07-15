#!/usr/bin/env python3
"""Foundation tests for XPLAT-007 runner gate dispatch."""

from __future__ import annotations

import ast
from contextlib import ExitStack
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "runner-gates"
CONTRACT_DIR = FIXTURE_DIR / "contracts"
PROMOTION_RECORDS = FIXTURE_DIR / "promotion-records.json"
REQUESTS_DIR = FIXTURE_DIR / "requests"
INSTALLED_RELEASE_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "installed-plugin-release"
INSTALLED_RELEASE_CONTRACT_DIR = INSTALLED_RELEASE_FIXTURE_DIR / "contracts"
INSTALLED_RELEASE_REQUESTS_DIR = INSTALLED_RELEASE_FIXTURE_DIR / "requests"
INSTALLED_RELEASE_PROMOTION_RECORD = "tests/speckit-pro/unit/fixtures/installed-plugin-release/promotion-records.json"
PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "plugin-bash-confinement"
PLUGIN_BASH_CONFINEMENT_REQUESTS_DIR = PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR / "requests"
PLUGIN_BASH_CONFINEMENT_CONTRACT_DIR = PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR / "contracts"

if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))


STATUS_EXIT_CODES = {
    "ok": 0,
    "expected_failure": 1,
    "input_error": 2,
    "missing_prerequisite": 3,
    "subprocess_failure": 4,
    "internal_failure": 5,
}


def runner_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(PLUGIN_ROOT) if not existing else f"{PLUGIN_ROOT}{os.pathsep}{existing}"
    return env


def gate_request(
    helper_id: str,
    operation: str,
    *,
    mode: str = "read_only",
    inputs: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "request_id": f"test-{operation}",
        "helper_id": helper_id,
        "operation": operation,
        "mode": mode,
        "inputs": inputs or {},
    }


def run_runner(
    request: object,
    *,
    extra_env: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any], list[dict[str, Any]]]:
    env = runner_env()
    if extra_env:
        env.update(extra_env)
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


def fixture_request(name: str) -> dict[str, Any]:
    return json.loads((REQUESTS_DIR / f"{name}.json").read_text(encoding="utf-8"))


def fixture_cases(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / f"{name}-cases.json").read_text(encoding="utf-8"))


def installed_release_fixture_request(name: str) -> dict[str, Any]:
    return json.loads((INSTALLED_RELEASE_REQUESTS_DIR / f"{name}.json").read_text(encoding="utf-8"))


def installed_release_fixture_cases(name: str) -> dict[str, Any]:
    return json.loads((INSTALLED_RELEASE_FIXTURE_DIR / f"{name}-cases.json").read_text(encoding="utf-8"))


def plugin_bash_confinement_fixture_request(name: str) -> dict[str, Any]:
    return json.loads((PLUGIN_BASH_CONFINEMENT_REQUESTS_DIR / f"{name}.json").read_text(encoding="utf-8"))


def plugin_bash_confinement_fixture_cases(name: str) -> dict[str, Any]:
    return json.loads((PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR / f"{name}-cases.json").read_text(encoding="utf-8"))


def run_installed_release_readiness_case(case_id: str, *, live_evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    from speckit_pro_runner.gates import registry, release as release_gate

    entry = next(
        operation
        for operation in registry.all_gate_operations()
        if operation.operation == "release-readiness-xplat008"
    )
    request = SimpleNamespace(
        request_id=f"test-installed-release-readiness-{case_id}",
        operation="release-readiness-xplat008",
        inputs={
            "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/release-readiness-cases.json",
            "case_id": case_id,
        },
    )
    if live_evidence is None:
        return release_gate.release_readiness_xplat008(entry, request, REPO_ROOT)
    with patch.object(release_gate, "live_xplat008_gate_evidence", return_value=live_evidence):
        return release_gate.release_readiness_xplat008(entry, request, REPO_ROOT)


def run_plugin_bash_confinement_case(
    case_id: str,
    *,
    max_findings: int | None = None,
    skip_source_scan: bool = False,
    skip_installed_root_scan: bool = False,
) -> dict[str, Any]:
    from speckit_pro_runner.gates import active_path_guard, registry

    entry = next(
        operation
        for operation in registry.all_gate_operations()
        if operation.operation == "zero-bash-guard"
    )
    inputs: dict[str, Any] = {
        "case_file": "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/zero-bash-guard-cases.json",
        "case_id": case_id,
    }
    if max_findings is not None:
        inputs["max_findings"] = max_findings
    request = SimpleNamespace(
        request_id=f"test-zero-bash-guard-{case_id}",
        operation="zero-bash-guard",
        inputs=inputs,
    )
    if not skip_source_scan and not skip_installed_root_scan:
        return active_path_guard.run_zero_bash_guard(entry, request, REPO_ROOT)
    with ExitStack() as stack:
        if skip_source_scan:
            stack.enter_context(patch.object(active_path_guard, "source_files", return_value=[]))
        if skip_installed_root_scan:
            stack.enter_context(patch.object(active_path_guard, "scan_repo_sources", return_value=[]))
        return active_path_guard.run_zero_bash_guard(entry, request, REPO_ROOT)


def python_argv(source: str) -> list[str]:
    return [sys.executable, "-c", source]


def load_layer_script_dispatcher() -> Any:
    dispatcher_path = REPO_ROOT / "tests" / "speckit-pro" / "run-layer-scripts.py"
    spec = importlib.util.spec_from_file_location("run_layer_scripts", dispatcher_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def successful_command(label: str) -> dict[str, Any]:
    return {
        "argv": python_argv(f"import sys; print('{label} stdout'); print('{label} stderr', file=sys.stderr)"),
        "timeout_seconds": 5,
    }


def failing_command(label: str, exit_code: int = 1) -> dict[str, Any]:
    return {
        "argv": python_argv(
            f"import sys; print('{label} stdout'); print('{label} stderr', file=sys.stderr); raise SystemExit({exit_code})"
        ),
        "timeout_seconds": 5,
    }


class GateFoundationTests(unittest.TestCase):
    maxDiff = None

    def assert_stdout_json(self, completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, completed.stdout)
        parsed = json.loads(lines[0])
        self.assertIsInstance(parsed, dict)
        return parsed

    def assert_response(self, response: dict[str, Any], status: str) -> None:
        self.assertEqual(response["schema_version"], "1.0")
        self.assertEqual(response["status"], status)
        self.assertEqual(response["exit_code"], STATUS_EXIT_CODES[status])
        self.assertIsNone(response["legacy_exit_code"])
        self.assertIsInstance(response["diagnostics"], list)
        self.assertIsInstance(response["data"], dict)

    def assert_status_exit_mapping(self, completed: subprocess.CompletedProcess[str], response: dict[str, Any]) -> None:
        self.assertEqual(completed.returncode, response["exit_code"])
        self.assertEqual(completed.returncode, STATUS_EXIT_CODES[response["status"]])

    def assert_stderr_diagnostics(self, response: dict[str, Any], stderr_records: list[dict[str, Any]]) -> None:
        self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])
        for diag in response["diagnostics"]:
            for field in ("severity", "source", "code", "message", "remediation"):
                self.assertIn(field, diag)
            self.assertEqual(diag["source"], "runner")
            self.assertIsInstance(diag["remediation"], dict)
            self.assertTrue(diag["remediation"]["summary"])
            self.assertTrue(diag["remediation"]["actions"])

    def assert_artifact_paths(self, response: dict[str, Any]) -> None:
        artifacts = response["data"].get("artifacts", [])
        self.assertIsInstance(artifacts, list)
        for artifact in artifacts:
            self.assertIsInstance(artifact, dict)
            path = Path(artifact["path"])
            self.assertFalse(path.is_absolute(), artifact["path"])
            self.assertNotIn("..", path.parts)

    def assert_installed_release_promotion_metadata(self, response: dict[str, Any], case_file: str) -> None:
        self.assertEqual(response["data"]["gate"]["promotion_record"], INSTALLED_RELEASE_PROMOTION_RECORD)
        artifacts = response["data"].get("artifacts", [])
        self.assertIn({"path": INSTALLED_RELEASE_PROMOTION_RECORD, "kind": "promotion_record"}, artifacts)
        self.assertIn({"path": case_file, "kind": "fixture"}, artifacts)
        self.assertEqual(len({artifact["path"] for artifact in artifacts}), len(artifacts))

    def assert_no_shell_argv(self, argv: list[str]) -> None:
        joined = " ".join(argv).lower()
        self.assertNotIn("bash", joined)
        self.assertNotIn("jq", joined)
        self.assertNotIn("powershell", joined)
        self.assertNotIn("pwsh", joined)
        self.assertFalse(any(arg.lower().endswith(".sh") for arg in argv))

    def assert_payload_completeness_contract_subset(self, results: list[dict[str, Any]]) -> None:
        schema = json.loads((INSTALLED_RELEASE_CONTRACT_DIR / "payload-completeness.schema.json").read_text(encoding="utf-8"))
        required = set(schema["required"])
        allowed = set(schema["properties"])
        file_required = set(schema["$defs"]["payload_file"]["required"])
        file_allowed = set(schema["$defs"]["payload_file"]["properties"])
        for result in results:
            self.assertLessEqual(required, set(result), result.get("payload_surface"))
            self.assertFalse(set(result) - allowed, result.get("payload_surface"))
            for files_key in ("expected_files", "actual_files"):
                for file_record in result[files_key]:
                    with self.subTest(surface=result["payload_surface"], path=file_record["path"]):
                        self.assertLessEqual(file_required, set(file_record), file_record)
                        self.assertFalse(set(file_record) - file_allowed, file_record)
                        path = file_record["path"]
                        self.assertFalse(path.startswith("/") or ".." in path.split("/") or ":" in path.split("/")[0], path)

    def assert_release_readiness_contract_subset(self, readiness: dict[str, Any]) -> None:
        schema = json.loads((INSTALLED_RELEASE_CONTRACT_DIR / "release-readiness.schema.json").read_text(encoding="utf-8"))
        check_schema = schema["$defs"]["check"]["properties"]
        check_ids = set(check_schema["check_id"]["enum"])
        blocker_classes = set(check_schema["blocker_class"]["enum"])
        payload_schema = schema["$defs"]["payload_result"]
        payload_required = set(payload_schema["required"])
        payload_allowed = set(payload_schema["properties"])
        file_schema = schema["$defs"]["payload_file"]
        file_required = set(file_schema["required"])
        file_allowed = set(file_schema["properties"])
        for result in readiness["payload_results"]:
            with self.subTest(release_payload=result.get("payload_surface")):
                self.assertLessEqual(payload_required, set(result), result.get("payload_surface"))
                self.assertFalse(set(result) - payload_allowed, result.get("payload_surface"))
                for files_key in ("expected_files", "actual_files"):
                    for file_record in result[files_key]:
                        self.assertLessEqual(file_required, set(file_record), file_record)
                        self.assertFalse(set(file_record) - file_allowed, file_record)
        evidence_ref_schema = schema["properties"]["evidence_refs"]
        self.assertLessEqual(set(evidence_ref_schema["required"]), set(readiness["evidence_refs"]))
        self.assertFalse(set(readiness["evidence_refs"]) - set(evidence_ref_schema["properties"]))
        for check in readiness["checks"]:
            with self.subTest(check_id=check["check_id"]):
                self.assertIn(check["check_id"], check_ids)
                self.assertIn(check["blocker_class"], blocker_classes)
        runner_required = set(schema["$defs"]["runner_invocation"]["required"])
        resolution_required = set(schema["$defs"]["interpreter_resolution"]["required"])
        for record in readiness["runner_invocations"]:
            with self.subTest(runner_invocation=record["request_id"]):
                self.assertLessEqual(runner_required, set(record), record)
                self.assertLessEqual(resolution_required, set(record["interpreter_resolution"]), record)
                self.assertIsInstance(record["interpreter_resolution"]["invocation_argv_prefix"], list)

    def assert_uat_matrix_contract_subset(self, matrix: dict[str, Any]) -> None:
        schema = json.loads((INSTALLED_RELEASE_CONTRACT_DIR / "uat-matrix.schema.json").read_text(encoding="utf-8"))
        self.assertLessEqual(set(schema["required"]), set(matrix))
        self.assertFalse(set(matrix) - set(schema["properties"]))
        check_ids = set(schema["$defs"]["check"]["properties"]["check_id"]["enum"])
        blocker_classes = set(schema["$defs"]["check"]["properties"]["blocker_class"]["enum"])
        for check in matrix["checks"]:
            self.assertIn(check["check_id"], check_ids)
            self.assertIn(check["blocker_class"], blocker_classes)

    def repo_rel(self, path: Path) -> str:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve(strict=False)).as_posix()

    def assert_input_error_code(self, request: dict[str, object], expected_code: str) -> dict[str, Any]:
        completed, response, stderr_records = run_runner(request)
        self.assert_stdout_json(completed)
        self.assert_response(response, "input_error")
        self.assert_status_exit_mapping(completed, response)
        self.assert_stderr_diagnostics(response, stderr_records)
        self.assert_artifact_paths(response)
        self.assertEqual([diag["code"] for diag in response["diagnostics"]], [expected_code])
        return response

    def test_registry_marks_us1_suite_operations_implemented_without_active_cutover(self) -> None:
        from speckit_pro_runner.gates.registry import all_gate_operations, gate_registry_report

        report = gate_registry_report()
        self.assertEqual(report["schema_version"], "1.0")
        self.assertEqual(report["feature_id"], "XPLAT-007+XPLAT-008+XPLAT-009+XPLAT-010")
        self.assertEqual(report["promotion_status"], "mixed")
        self.assertFalse(report["active_cutover"])
        self.assertEqual(
            set(report["groups"]),
            {"runtime", "suite", "payload", "install", "release", "guard"},
        )

        operations = all_gate_operations()
        self.assertGreaterEqual(len(operations), 21)
        runtime_operations = {
            "runner-invocation",
        }
        installed_release_guard_operations = {
            "active-runtime-guard",
        }
        us1_operations = {
            "run-default-suite",
            "run-layer",
            "run-toolchain-preflight",
            "run-ai-evals",
            "run-integration-suite",
            "run-parity-suite",
        }
        us2_operations = {
            "payload-completeness",
            "build-test-payload-evidence",
            "refresh-local-plugin-fixture",
            "verify-install",
            "detect-changed-plugin",
            "aggregate-suite-results",
            "check-marketplace-version-sync",
            "validate-pr-title",
            "validate-workflow-contract",
            "check-payload-evidence",
            "parse-release-pr-payload-sync",
            "check-post-release-drift",
            "release-readiness",
            "release-readiness-xplat008",
        }
        us3_operations = {
            "active-path-guard",
            "zero-bash-guard",
            "classify-shell-finding",
            "repo-bash-confinement",
        }
        us4_operations = {
            "uat-matrix",
        }
        for operation in operations:
            if operation.operation in runtime_operations:
                self.assertEqual(operation.group, "runtime")
                self.assertEqual(operation.story, "US1")
                self.assertTrue(operation.implemented)
                self.assertEqual(operation.promotion_status, "python_authoritative")
            elif operation.operation in installed_release_guard_operations:
                self.assertEqual(operation.group, "guard")
                self.assertEqual(operation.story, "US1")
                self.assertTrue(operation.implemented)
                self.assertEqual(operation.promotion_status, "python_authoritative")
            elif operation.operation in us1_operations:
                self.assertEqual(operation.group, "suite")
                self.assertEqual(operation.story, "US1")
                self.assertTrue(operation.implemented)
                self.assertEqual(operation.promotion_status, "python_authoritative")
            elif operation.operation in us2_operations:
                self.assertEqual(operation.story, "US2")
                self.assertTrue(operation.implemented)
                self.assertEqual(operation.promotion_status, "python_authoritative")
            elif operation.operation in us3_operations:
                self.assertEqual(operation.group, "guard")
                self.assertEqual(operation.story, "US3")
                self.assertTrue(operation.implemented)
                self.assertEqual(operation.promotion_status, "python_authoritative")
            elif operation.operation in us4_operations:
                self.assertEqual(operation.group, "release")
                self.assertEqual(operation.story, "US4")
                self.assertTrue(operation.implemented)
                self.assertEqual(operation.promotion_status, "python_authoritative")
            else:
                self.assertEqual(operation.promotion_status, "planned")
                self.assertFalse(operation.implemented)
            self.assertIn(operation.group, report["groups"])
            self.assertIn(operation.helper_id, report["gate_helper_ids"])

    def test_us1_request_fixtures_cover_suite_operations(self) -> None:
        expected = {
            "run-default-suite.json",
            "run-layer.json",
            "run-toolchain-preflight.json",
            "run-toolchain-preflight-docs.json",
            "run-ai-evals.json",
            "run-integration-suite.json",
            "run-parity-suite.json",
            "test-payload-evidence.json",
            "install-verification.json",
            "release-readiness.json",
            "release-readiness-live-github.json",
            "active-path-guard.json",
            "classify-shell-finding.json",
        }
        self.assertEqual({path.name for path in REQUESTS_DIR.iterdir()}, expected)

        default_request = fixture_request("run-default-suite")
        self.assertEqual(default_request["helper_id"], "suite-gate")
        self.assertEqual(default_request["operation"], "run-default-suite")
        self.assertEqual(default_request["mode"], "read_only")
        self.assertEqual(default_request["inputs"]["suite"], ["toolchain", "1", "4", "5", "7", "8"])
        self.assertFalse(default_request["inputs"]["xplat_008_cutover_allowed"])

        for name in [
            "run-default-suite",
            "run-layer",
            "run-toolchain-preflight",
            "run-ai-evals",
            "run-integration-suite",
            "run-parity-suite",
        ]:
            with self.subTest(fixture=name):
                request = fixture_request(name)
                self.assertEqual(request["schema_version"], "1.0")
                self.assertEqual(request["helper_id"], "suite-gate")
                self.assertEqual(request["mode"], "read_only")
                self.assertIn(request["operation"], {
                    "run-default-suite",
                    "run-layer",
                    "run-toolchain-preflight",
                    "run-ai-evals",
                    "run-integration-suite",
                    "run-parity-suite",
                })

        payload_request = fixture_request("test-payload-evidence")
        self.assertEqual(payload_request["helper_id"], "payload-gate")
        self.assertEqual(payload_request["operation"], "build-test-payload-evidence")
        self.assertEqual(payload_request["mode"], "read_only")
        self.assertFalse(payload_request["inputs"]["release_payload_cutover"])

        install_request = fixture_request("install-verification")
        self.assertEqual(install_request["helper_id"], "install-verification")
        self.assertEqual(install_request["operation"], "verify-install")
        self.assertTrue(install_request["inputs"]["fake_home"])

        release_request = fixture_request("release-readiness")
        self.assertEqual(release_request["helper_id"], "release-readiness")
        self.assertEqual(release_request["operation"], "release-readiness")
        self.assertFalse(release_request["inputs"]["xplat_008_cutover_allowed"])

        active_guard_request = fixture_request("active-path-guard")
        self.assertEqual(active_guard_request["helper_id"], "active-path-guard")
        self.assertEqual(active_guard_request["operation"], "active-path-guard")
        self.assertEqual(active_guard_request["mode"], "read_only")
        self.assertEqual(active_guard_request["inputs"]["case_id"], "final-current-implementation")
        self.assertFalse(active_guard_request["inputs"]["xplat_008_cutover_allowed"])

        classify_request = fixture_request("classify-shell-finding")
        self.assertEqual(classify_request["helper_id"], "active-path-guard")
        self.assertEqual(classify_request["operation"], "classify-shell-finding")
        self.assertEqual(classify_request["mode"], "read_only")
        self.assertIn("text", classify_request["inputs"])
        self.assertFalse(classify_request["inputs"]["xplat_008_cutover_allowed"])

    def test_us2_case_fixtures_cover_payload_install_and_release_failures(self) -> None:
        payload_cases = fixture_cases("payload-evidence")
        self.assertEqual(payload_cases["schema_version"], "1.0")
        self.assertIn("release_payload_cutover=false", payload_cases["coverage"])
        self.assertEqual({case["case_id"] for case in payload_cases["cases"]}, {"claude-codex-test-payloads", "stale-generated-files"})

        install_cases = fixture_cases("install-verification")
        self.assertEqual(install_cases["schema_version"], "1.0")
        self.assertEqual(
            {case["case_id"] for case in install_cases["cases"]},
            {
                "complete-fake-home",
                "safe-repair-plan",
                "windows-style-paths",
                "traversal-rejection",
                "line-ending-normalization",
            },
        )

        release_cases = fixture_cases("release-readiness")
        self.assertEqual(release_cases["schema_version"], "1.0")
        self.assertEqual(
            {case["case_id"] for case in release_cases["cases"]},
            {
                "ready",
                "stale-version-data",
                "missing-promotion-records",
                "stale-payload-evidence",
                "changed-plugin-false-positive",
                "suite-aggregation-failure",
                "release-pr-payload-sync-parse-failure",
                "post-release-drift",
                "workflow-contract-failure",
                "xplat-008-handoff-items",
            },
        )

        active_cases = fixture_cases("active-path-guard")
        self.assertEqual(active_cases["schema_version"], "1.0")
        self.assertEqual(
            {case["case_id"] for case in active_cases["cases"]},
            {
                "blocking-active-patterns",
                "nonblocking-classifications",
                "workflow-dispatch-good",
                "workflow-dispatch-with-plugin-logic",
                "final-current-implementation",
            },
        )
        for label in [
            "active Bash",
            ".sh",
            "jq",
            "Git Bash",
            "WSL",
            "PowerShell helper",
            "shell parsing",
            "shell interpolation",
            "shell=True",
            "os.system",
            "command-string subprocess",
            "CI dispatch glue",
            "XPLAT-008 cutover surface",
        ]:
            self.assertIn(label, active_cases["coverage"])

    def test_installed_release_runner_invocation_fixtures_cover_interpreter_resolution(self) -> None:
        cases = installed_release_fixture_cases("runner-invocation")
        self.assertEqual(cases["schema_version"], "1.0")
        self.assertEqual(cases["feature_id"], "XPLAT-008")
        self.assertEqual(
            {case["case_id"] for case in cases["cases"]},
            {
                "windows-py-v3",
                "windows-py-3-fallback",
                "macos-python3",
                "linux-python-fallback",
                "live-host-runtime-info",
                "too-old-or-missing",
            },
        )
        expected_candidates = {
            "windows": ["py -V:3", "py -3", "python", "python3"],
            "macos": ["python3", "python"],
            "linux": ["python3", "python"],
        }
        for case in cases["cases"]:
            with self.subTest(case_id=case["case_id"]):
                self.assertIn(case["product"], {"claude", "codex"})
                self.assertIn(case["operation"], {"preflight", "scaffold", "status", "autopilot-dry-run"})
                self.assertTrue(case["cache_root"])
                if "candidate_results" not in case:
                    continue
                platform = case["platform"]
                attempted = [item["candidate"] for item in case["candidate_results"]]
                self.assertEqual(attempted, expected_candidates[platform][: len(attempted)])

        request = installed_release_fixture_request("runner-invocation")
        self.assertEqual(request["helper_id"], "runner-invocation")
        self.assertEqual(request["operation"], "runner-invocation")
        self.assertEqual(request["mode"], "read_only")
        self.assertEqual(request["inputs"]["case_id"], "live-host-runtime-info")

    def test_installed_release_runner_invocation_records_have_no_shell_fallback(self) -> None:
        contract = json.loads((INSTALLED_RELEASE_CONTRACT_DIR / "runner-invocation.schema.json").read_text(encoding="utf-8"))
        release_contract = json.loads((INSTALLED_RELEASE_CONTRACT_DIR / "release-readiness.schema.json").read_text(encoding="utf-8"))
        argv_contract = contract["properties"]["invocation"]["properties"]["argv"]
        self.assertEqual(len(argv_contract["oneOf"]), 3)
        self.assertEqual(contract["$defs"]["diagnostic"]["properties"]["remediation"]["type"], "object")
        release_runner = release_contract["$defs"]["runner_invocation"]
        self.assertEqual(release_runner["properties"]["invocation"]["properties"]["argv"], argv_contract)
        self.assertIn(
            "runner-invocations",
            release_contract["$defs"]["check"]["properties"]["check_id"]["enum"],
        )
        self.assertIn(
            "missing_runner_invocation",
            release_contract["$defs"]["check"]["properties"]["blocker_class"]["enum"],
        )
        self.assertIn("evidence_refs", release_contract["required"])
        self.assertEqual(release_contract["properties"]["runner_invocations"]["minItems"], 1)
        self.assertEqual(
            release_contract["$defs"]["interpreter_resolution"],
            contract["$defs"]["interpreter_resolution"],
        )
        self.assertEqual(
            release_contract["$defs"]["diagnostic"]["properties"]["remediation"]["type"],
            "object",
        )

        from speckit_pro_runner.helpers import install as install_helper

        self.assertEqual(
            install_helper.invocation_prefix_for_candidate("windows", "py -V:3", "C:/Python312/python.exe"),
            ["C:/Python312/python.exe"],
        )
        self.assertEqual(
            install_helper.invocation_prefix_for_candidate("windows", "py -V:3", "C:/Windows/py.exe"),
            ["C:/Windows/py.exe", "-3"],
        )
        self.assertEqual(
            install_helper.invocation_prefix_for_live_probe("py -V:3", "C:/Python312/python.exe"),
            ["py", "-3"],
        )
        self.assertTrue(install_helper.allowed_python_executable("linux", "/usr/bin/python3.11"))
        resolution, diagnostics = install_helper.resolve_python_interpreter(
            "linux",
            {"candidate_results": [{"candidate": "bash", "returncode": 0, "version": "3.11.8", "resolved_executable": "bash"}]},
            "dist/codex/speckit-pro",
        )
        self.assertFalse(resolution["accepted"])
        self.assertEqual(resolution["failure_code"], "python_runtime_unavailable")
        self.assertEqual([diag["code"] for diag in diagnostics], ["python_runtime_unavailable"])
        self.assertIn("unsupported Python candidate", resolution["diagnostic"])
        resolution, diagnostics = install_helper.resolve_python_interpreter(
            "linux",
            {
                "candidate_results": [
                    {
                        "candidate": "python3",
                        "returncode": 0,
                        "version": "3.11.8",
                        "resolved_executable": "bash",
                    }
                ]
            },
            "dist/codex/speckit-pro",
        )
        self.assertFalse(resolution["accepted"])
        self.assertEqual(resolution["failure_code"], "python_runtime_unavailable")
        self.assertEqual([diag["code"] for diag in diagnostics], ["python_runtime_unavailable"])
        self.assertIn("unsupported resolved executable", resolution["diagnostic"])
        resolution, diagnostics = install_helper.resolve_python_interpreter(
            "linux",
            {
                "candidate_results": [
                    {
                        "candidate": "python3",
                        "returncode": 0,
                        "version": "3.11.8",
                        "resolved_executable": "python3",
                        "invocation_argv_prefix": ["bash"],
                    }
                ]
            },
            "dist/codex/speckit-pro",
        )
        self.assertFalse(resolution["accepted"])
        self.assertEqual(resolution["failure_code"], "python_runtime_unavailable")
        self.assertEqual([diag["code"] for diag in diagnostics], ["python_runtime_unavailable"])
        self.assertIn("unsupported invocation prefix", resolution["diagnostic"])
        for prefix in [["python3", "-c"], ["python3", "bash"], ["python3", "-m"], ["py"], ["py", "-c"]]:
            with self.subTest(prefix=prefix):
                self.assertFalse(install_helper.allowed_python_invocation_prefix("linux", prefix))
        self.assertFalse(install_helper.allowed_python_invocation_prefix("windows", ["py", "-c"]))
        self.assertTrue(install_helper.allowed_python_invocation_prefix("windows", ["py", "-3"]))
        self.assertTrue(install_helper.allowed_python_invocation_prefix("linux", ["python3"]))
        for payload_root in [
            REPO_ROOT / "dist" / "claude" / "speckit-pro",
            REPO_ROOT / "dist" / "codex" / "speckit-pro",
        ]:
            self.assertTrue((payload_root / "speckit_pro_runner" / "__main__.py").is_file())
            self.assertTrue((payload_root / "speckit_pro_runner" / "speckit-pro-runner.manifest.json").is_file())

        pass_cases = [
            "windows-py-v3",
            "windows-py-3-fallback",
            "macos-python3",
            "linux-python-fallback",
        ]
        for case_id in pass_cases:
            with self.subTest(case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "runner-invocation",
                        "runner-invocation",
                        inputs={
                            "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/runner-invocation-cases.json",
                            "case_id": case_id,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 0)
                self.assert_stdout_json(completed)
                self.assert_response(response, "ok")
                self.assert_status_exit_mapping(completed, response)
                self.assertEqual(stderr_records, [])
                self.assert_installed_release_promotion_metadata(
                    response,
                    "tests/speckit-pro/unit/fixtures/installed-plugin-release/runner-invocation-cases.json",
                )
                record = response["data"]["runner_invocation"]
                self.assertEqual(record["schema_version"], "1.0")
                self.assertEqual(record["request_id"], response["request_id"])
                self.assertTrue(record["interpreter_resolution"]["accepted"])
                self.assertEqual(record["interpreter_resolution"]["minimum_version"], "3.11")
                self.assertIsNone(record["interpreter_resolution"]["failure_code"])
                self.assertTrue(record["interpreter_resolution"]["attempted_candidates"])
                self.assertTrue(record["interpreter_resolution"]["resolved_executable"])
                self.assertTrue(record["interpreter_resolution"]["invocation_argv_prefix"])
                self.assertRegex(record["interpreter_resolution"]["version"], r"^3\.(1[1-9]|[2-9][0-9])\.")
                expected_argv = [
                    *record["interpreter_resolution"]["invocation_argv_prefix"],
                    "-m",
                    "speckit_pro_runner",
                ]
                self.assertEqual(
                    record["invocation"],
                    {
                        "argv": expected_argv,
                        "stdin_mode": "single_json_request",
                        "stdout_mode": "single_json_response",
                        "stderr_mode": "diagnostics_only",
                        "shell_used": False,
                    },
                )
                self.assertEqual(record["runner_request"]["helper_id"], "runner")
                self.assertEqual(record["runner_response"]["schema_version"], "1.0")
                self.assertEqual(record["runner_response"]["evidence_source"], "fixture")
                self.assertEqual(record["status"], "pass")
                self.assertEqual(record["diagnostics"], [])
                self.assert_no_shell_argv(record["invocation"]["argv"])
                if record["platform"] == "windows":
                    self.assertEqual(record["invocation"]["argv"][-3:], ["-3", "-m", "speckit_pro_runner"])

        completed, response, stderr_records = run_runner(
            gate_request(
                "runner-invocation",
                "runner-invocation",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/runner-invocation-cases.json",
                    "case_id": "live-host-runtime-info",
                },
            )
        )
        self.assertEqual(completed.returncode, 0)
        self.assert_stdout_json(completed)
        self.assert_response(response, "ok")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual(stderr_records, [])
        self.assert_installed_release_promotion_metadata(
            response,
            "tests/speckit-pro/unit/fixtures/installed-plugin-release/runner-invocation-cases.json",
        )
        record = response["data"]["runner_invocation"]
        self.assertEqual(record["status"], "pass")
        self.assertTrue(record["interpreter_resolution"]["accepted"])
        self.assertNotEqual(record["runner_response"].get("evidence_source"), "fixture")
        self.assertEqual(record["runner_response"]["status"], "ok")
        self.assertEqual(record["runner_response"]["data"]["report"]["runner_name"], "speckit_pro_runner")
        self.assert_no_shell_argv(record["invocation"]["argv"])

        from speckit_pro_runner import runtime as runner_runtime

        with tempfile.TemporaryDirectory() as tmp:
            installed_root = Path(tmp) / "installed-cache" / "speckit-pro"
            (installed_root / ".codex-plugin").mkdir(parents=True)
            (installed_root / ".codex-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
            (installed_root / "speckit_pro_runner").mkdir()
            self.assertEqual(runner_runtime.runtime_context(installed_root), "installed_payload")
        self.assertEqual(runner_runtime.runtime_context(PLUGIN_ROOT), "source_checkout")

        runner_response, execution_diag = install_helper.execute_runner_runtime_info(
            [sys.executable, "-m", "speckit_pro_runner"],
            record["runner_request"],
            REPO_ROOT,
            "dist/missing-installed-cache",
        )
        self.assertIsNone(runner_response)
        self.assertEqual(execution_diag["code"], "runner_cache_missing")

        with tempfile.TemporaryDirectory() as tmp:
            fake_root = Path(tmp) / "fake-payload"
            package = fake_root / "speckit_pro_runner"
            package.mkdir(parents=True)
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "__main__.py").write_text(
                "import json\n"
                "print(json.dumps({"
                "'schema_version':'1.0',"
                "'status':'ok',"
                "'exit_code':0,"
                "'legacy_exit_code':None,"
                "'diagnostics':[],"
                "'data':{'report':{"
                "'runner_name':'fake_runner',"
                "'runner_contract_id':'speckit-pro-runner',"
                "'selected_runtime_name':'python-stdlib-runner',"
                "'source_vs_installed_context':'installed_payload',"
                "'paths':{}"
                "}}}))\n",
                encoding="utf-8",
            )
            runner_response, execution_diag = install_helper.execute_runner_runtime_info(
                [sys.executable, "-m", "speckit_pro_runner"],
                record["runner_request"],
                REPO_ROOT,
                fake_root.as_posix(),
            )
        self.assertIsNotNone(runner_response)
        self.assertEqual(execution_diag["code"], "runner_identity_mismatch")

        with tempfile.TemporaryDirectory() as tmp:
            fake_root = Path(tmp) / "list-payload"
            package = fake_root / "speckit_pro_runner"
            package.mkdir(parents=True)
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "__main__.py").write_text("print('[]')\n", encoding="utf-8")
            runner_response, execution_diag = install_helper.execute_runner_runtime_info(
                [sys.executable, "-m", "speckit_pro_runner"],
                record["runner_request"],
                REPO_ROOT,
                fake_root.as_posix(),
            )
        self.assertIsNotNone(runner_response)
        self.assertEqual(runner_response["data"]["parsed_type"], "list")
        self.assertEqual(execution_diag["code"], "runner_response_malformed")

        completed, response, stderr_records = run_runner(
            gate_request(
                "runner-invocation",
                "runner-invocation",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/runner-invocation-cases.json",
                    "case_id": "too-old-or-missing",
                },
            )
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_stdout_json(completed)
        self.assert_response(response, "expected_failure")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual([diag["code"] for diag in stderr_records], ["python_runtime_unavailable"])
        record = response["data"]["runner_invocation"]
        self.assertFalse(record["interpreter_resolution"]["accepted"])
        self.assertIsNone(record["interpreter_resolution"]["resolved_executable"])
        self.assertEqual(record["interpreter_resolution"]["failure_code"], "python_runtime_unavailable")
        self.assertEqual(record["interpreter_resolution"]["invocation_argv_prefix"], [])
        self.assertIsNone(record["runner_response"])
        self.assertEqual(record["status"], "blocked")
        self.assertEqual(record["invocation"]["argv"], [])
        self.assertFalse(record["invocation"]["shell_used"])

    def test_installed_release_active_runtime_guard_fixtures_block_only_active_runtime_findings(self) -> None:
        from speckit_pro_runner.gates import active_path_guard

        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "bash",
                "bash",
                "Run bash before status.",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/codex-agents/implement-executor.toml",
                "bash",
                "Bash",
                "Require Bash before running this agent.",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "shell_interpolation",
                "`speckit-pro/skills/speckit-status/SKILL.md`",
                "`speckit-pro/skills/speckit-status/SKILL.md`",
                "repo_baseline",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "jq",
                "jq",
                "Do not add a shell fallback, jq parsing path, Git Bash, WSL, or PowerShell requirement.",
                "repo",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "bash",
                "Bash",
                "Do not run without Bash.",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "bash",
                "bash",
                "Run bash without Python before status.",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "shell_interpolation",
                "`bash`",
                "Run `bash` before status.",
                "repo",
            ),
            "blocking_active_runtime",
        )

        cases = installed_release_fixture_cases("active-runtime-guard")
        self.assertEqual(cases["schema_version"], "1.0")
        self.assertEqual(cases["feature_id"], "XPLAT-008")
        self.assertEqual(
            {case["case_id"] for case in cases["cases"]},
            {
                "blocking-active-runtime-patterns",
                "allowed-runtime-exceptions",
                "final-current-implementation",
                "empty-scan-roots",
                "non-list-scan-roots",
            },
        )
        final_case = next(case for case in cases["cases"] if case["case_id"] == "final-current-implementation")
        self.assertFalse(final_case["scan_changed_sources"])
        self.assertIn(
            "final current implementation scans the full release surface without requiring PR review-base diff metadata",
            cases["coverage"],
        )
        self.assertIn(
            "empty and non-list configured scan roots fail closed instead of falling back to default roots",
            cases["coverage"],
        )
        blocking_case = next(case for case in cases["cases"] if case["case_id"] == "blocking-active-runtime-patterns")
        blocking_yaml = next(file for file in blocking_case["files"] if file["path"] == "speckit-pro/codex-agents/openai.yaml")
        blocking_yaml_findings = active_path_guard.scan_sources_xplat008(
            [active_path_guard.SourceFile(blocking_yaml["path"], blocking_yaml["content"], "fixture")],
            REPO_ROOT,
        )
        blocking_yaml_records = {(finding.category, finding.line): finding.pattern for finding in blocking_yaml_findings}
        self.assertIn(("shell_command_wrapper", 2), blocking_yaml_records)
        self.assertIn("/bin/sh", blocking_yaml_records[("shell_command_wrapper", 2)])
        self.assertIn("-c", blocking_yaml_records[("shell_command_wrapper", 2)])
        self.assertIn(("shell_runtime", 6), blocking_yaml_records)
        self.assertIn("/bin/sh", blocking_yaml_records[("shell_runtime", 6)])
        self.assertIn(("shell_runtime", 8), blocking_yaml_records)
        self.assertIn("/usr/bin/zsh", blocking_yaml_records[("shell_runtime", 8)])
        self.assertLessEqual(
            {
                "dist/claude/speckit-pro/hooks",
                "dist/claude/speckit-pro/agents",
                "dist/claude/speckit-pro/skills",
                "dist/claude/speckit-pro/scripts",
                "dist/claude/speckit-pro/speckit_pro_runner",
                "dist/claude/speckit-pro/.claude-plugin",
                "dist/codex/speckit-pro/codex-hooks.json",
                "dist/codex/speckit-pro/codex-agents",
                "dist/codex/speckit-pro/skills",
                "dist/codex/speckit-pro/scripts",
                "dist/codex/speckit-pro/speckit_pro_runner",
                "dist/codex/speckit-pro/.codex-plugin",
                ".github/workflows",
                "README.md",
                "speckit-pro/README.md",
                "docs-site/src/content/docs",
            },
            set(final_case["scan_roots"]),
        )

        with patch.object(active_path_guard, "review_base_ref", return_value=None):
            response = active_path_guard.run_active_runtime_guard(
                SimpleNamespace(helper_id="active-path-guard"),
                SimpleNamespace(
                    operation="active-runtime-guard",
                    request_id="test-final-current-no-review-base",
                    inputs={
                        "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/active-runtime-guard-cases.json",
                        "case_id": "final-current-implementation",
                    },
                ),
                REPO_ROOT,
            )
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["data"]["blocking_count"], 0)
        for payload_root in (REPO_ROOT / "dist/claude/speckit-pro", REPO_ROOT / "dist/codex/speckit-pro"):
            for suffix in (".sh", ".ps1", ".bat", ".cmd"):
                self.assertFalse([path for path in payload_root.rglob(f"*{suffix}")], payload_root)

        with patch.object(active_path_guard, "review_base_ref", return_value=None):
            changed_sources = active_path_guard.changed_repo_sources(REPO_ROOT, {"scan_roots": ["speckit-pro/skills"]})
        self.assertIsInstance(changed_sources, active_path_guard.RawFinding)
        self.assertEqual(changed_sources.classification, "blocking_active_runtime")
        self.assertEqual(changed_sources.category, "diff_scan")
        with patch.object(active_path_guard.subprocess, "run", side_effect=OSError("git missing")):
            changed_sources = active_path_guard.changed_repo_sources(REPO_ROOT, {"scan_roots": ["speckit-pro/skills"]})
        self.assertIsInstance(changed_sources, active_path_guard.RawFinding)
        self.assertEqual(changed_sources.classification, "blocking_active_runtime")
        self.assertEqual(changed_sources.category, "diff_scan")
        self.assertNotIn("HEAD^", active_path_guard.review_base_ref.__code__.co_consts)
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "README.md",
                "bash",
                "bash",
                "Install requires Bash before running SpecKit Pro.",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "README.md",
                "bash",
                "bash",
                "Install requires Bash before running SpecKit Pro.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "docs-site/src/content/docs/install/codex.md",
                "jq",
                "jq",
                "Installed runtime requires jq before first use.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "README.md",
                "bash",
                "bash",
                "SpecKit Pro does not require Bash.",
                "repo",
            ),
            "docs_non_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "docs-site/src/content/docs/contribute-and-release.md",
                "script_file",
                "scripts/sync-marketplace-versions.sh",
                "`scripts/sync-marketplace-versions.sh`",
                "repo",
            ),
            "docs_non_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "docs-site/src/content/docs/troubleshooting.md",
                "bash",
                "Bash",
                "Bash source-checkout prerequisite",
                "repo",
            ),
            "docs_non_runtime",
        )
        wrapped_negative_findings = active_path_guard.scan_sources_xplat008(
            [
                active_path_guard.SourceFile(
                    "docs-site/src/content/docs/install/codex.md",
                    "payload; Bash, Git Bash, WSL, PowerShell-specific command language, and `jq` are\n"
                    "not installed-runtime requirements.",
                    "repo",
                )
            ],
            REPO_ROOT,
        )
        self.assertFalse(
            [finding for finding in wrapped_negative_findings if finding.classification == "blocking_active_runtime"]
        )
        markdown_heading_findings = active_path_guard.scan_sources_xplat008(
            [
                active_path_guard.SourceFile(
                    "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
                    "# Requires Bash before first use\n",
                    "repo_baseline",
                )
            ],
            REPO_ROOT,
        )
        self.assertTrue(
            [finding for finding in markdown_heading_findings if finding.classification == "blocking_active_runtime"]
        )
        script_suffix_findings = active_path_guard.scan_sources_xplat008(
            [
                active_path_guard.SourceFile(
                    "dist/codex/speckit-pro/scripts/install.ps1",
                    "Write-Host 'install'\n",
                    "repo_baseline",
                )
            ],
            REPO_ROOT,
        )
        self.assertTrue(
            [finding for finding in script_suffix_findings if finding.classification == "blocking_active_runtime"]
        )
        payload_detector_findings = active_path_guard.scan_sources_xplat008(
            [
                active_path_guard.SourceFile(
                    "dist/codex/speckit-pro/speckit_pro_runner/gates/payloads.py",
                    '    first_line = handle.readline(4096)\n'
                    '    return bool(re.search(r"^#!.*\\b(?:bash|sh|zsh|powershell|pwsh)\\b", first_line))\n',
                    "repo",
                )
            ],
            REPO_ROOT,
        )
        self.assertFalse(
            [finding for finding in payload_detector_findings if finding.classification == "blocking_active_runtime"]
        )
        mixed_tool_guidance_findings = active_path_guard.scan_sources_xplat008(
            [
                active_path_guard.SourceFile(
                    "speckit-pro/agents/phase-executor.md",
                    "allowed-tools: Bash, Read\nRun scripts/install.sh before release.\n",
                    "repo",
                )
            ],
            REPO_ROOT,
        )
        self.assertTrue(
            [
                finding
                for finding in mixed_tool_guidance_findings
                if finding.line == 2 and finding.classification == "blocking_active_runtime"
            ]
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
                "bash",
                "bash",
                "Run bash before status.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
                "script_file",
                "scripts/setup.sh",
                "Run scripts/setup.sh before use.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "dist/codex/speckit-pro/scripts/install.sh",
                "script_file",
                "*.sh",
                "#!/usr/bin/env bash\njq -n '{}'\n",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
                "jq",
                "jq",
                "Run jq before use.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "jq",
                "jq",
                "If Python is missing, use command -v jq and run Bash.",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "powershell",
                "PowerShell",
                "Requires PowerShell before status.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "script_file",
                "scripts/setup.sh",
                "Run scripts/setup.sh before first use.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "jq",
                "jq",
                "Run jq before status.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/agents/phase-executor.md",
                "shell_interpolation",
                "`$SHELL`",
                "Use `$SHELL` to run the installed agent.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "bash",
                "Bash",
                "Do not add Bash as an installed-runtime requirement.",
                "repo_baseline",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/skills/speckit-upgrade/SKILL.md",
                "bash",
                "Bash",
                "allowed-tools: Bash Read Edit Write",
                "repo",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/skills/speckit-upgrade/SKILL.md",
                "bash",
                "Bash",
                "allowed-tools: Bash Read Edit Write\nRun Bash before use.",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
                "bash",
                "Bash",
                "Maintainer-only source-checkout helper text may mention Bash.",
                "repo",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md",
                "script_file",
                "`estimate-reviewable-loc.sh",
                "The parent runs `estimate-reviewable-loc.sh <plan.md>` via `exec_command`, capturing the exit code.",
                "repo",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
                "jq",
                "jq",
                "If Python is missing, use command -v jq and run Bash.",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
                "jq",
                "jq",
                "If Python is missing, use command -v jq and run Bash.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
                "bash",
                "Bash",
                "Do not add Bash as an installed-runtime requirement.",
                "repo_baseline",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/agents/phase-executor.md",
                "bash",
                "Bash",
                "allowed-tools: Bash, Read",
                "repo",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/agents/clarify-executor.md",
                "bash",
                "Bash",
                "disallowedTools: Write, Edit, Bash, Agent",
                "repo",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_xplat008_path(
                "speckit-pro/agents/phase-executor.md",
                "bash",
                "Bash",
                "allowed-tools: Bash, Read; run scripts/install.sh",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.zero_bash_classification(
                "dist/claude/speckit-pro/agents/clarify-executor.md",
                "bash",
                "Bash",
                "disallowedTools: Write, Edit, Bash, Agent",
                [],
                declaration_line="disallowedTools: Write, Edit, Bash, Agent",
            ),
            "blocking_zero_bash",
        )
        self.assertEqual(
            active_path_guard.zero_bash_classification(
                "dist/claude/speckit-pro/skills/speckit-autopilot/references/capability-discovery.md",
                "shell_interpolation",
                "$SHELL",
                "Do not use $SHELL to run installed helpers.",
                [],
                declaration_line="Do not use $SHELL to run installed helpers.",
            ),
            "negative_policy",
        )
        self.assertEqual(
            active_path_guard.zero_bash_classification(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "bash",
                "Bash",
                "Run Bash instead of Python.",
                [],
                declaration_line="Run Bash instead of Python.",
            ),
            "blocking_zero_bash",
        )
        self.assertEqual(
            active_path_guard.zero_bash_classification(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "jq",
                "jq",
                "Use jq rather than Python JSON parsing.",
                [],
                declaration_line="Use jq rather than Python JSON parsing.",
            ),
            "blocking_zero_bash",
        )
        missing_roots = active_path_guard.missing_xplat008_scan_root_findings(
            REPO_ROOT,
            {"scan_roots": ["dist/missing-runtime-root"]},
        )
        self.assertEqual(len(missing_roots), 1)
        self.assertEqual(missing_roots[0].classification, "blocking_active_runtime")
        self.assertEqual(missing_roots[0].category, "scan_root")
        for malformed_case in ({"scan_roots": []}, {"scan_roots": "speckit-pro/skills"}):
            with self.subTest(malformed_case=malformed_case):
                malformed_roots = active_path_guard.missing_xplat008_scan_root_findings(REPO_ROOT, malformed_case)
                self.assertEqual(len(malformed_roots), 1)
                self.assertEqual(malformed_roots[0].classification, "blocking_active_runtime")
                self.assertEqual(malformed_roots[0].category, "scan_root")
                changed_sources = active_path_guard.changed_repo_sources(REPO_ROOT, malformed_case)
                self.assertIsInstance(changed_sources, active_path_guard.RawFinding)
                self.assertEqual(changed_sources.classification, "blocking_active_runtime")
                self.assertEqual(changed_sources.category, "scan_root")

        with tempfile.TemporaryDirectory() as tmp:
            completed, response, stderr_records = run_runner(
                gate_request(
                    "active-path-guard",
                    "active-runtime-guard",
                    inputs={"repo_root": tmp},
                )
            )
        self.assertEqual(completed.returncode, 3)
        self.assert_response(response, "missing_prerequisite")
        self.assertEqual([diag["code"] for diag in stderr_records], ["missing_prerequisite"])
        self.assertEqual(response["data"]["gate"]["comparison_ids"], ["xplat-008-active-runtime-guard"])
        self.assert_installed_release_promotion_metadata(
            response,
            "tests/speckit-pro/unit/fixtures/installed-plugin-release/active-runtime-guard-cases.json",
        )

        completed, response, stderr_records = run_runner(
            gate_request(
                "active-path-guard",
                "active-runtime-guard",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/active-runtime-guard-cases.json",
                    "case_id": "blocking-active-runtime-patterns",
                },
            )
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        self.assertEqual([diag["code"] for diag in stderr_records], ["active_runtime_guard_blocked"])
        self.assertGreaterEqual(response["data"]["blocking_count"], 4)
        self.assertTrue(
            all(finding["classification"] == "blocking_active_runtime" for finding in response["data"]["findings"])
        )
        self.assertLessEqual(
            {"bash", "script_file", "jq", "git_bash", "wsl"},
            {finding["category"] for finding in response["data"]["findings"]},
        )

        for case_id in ["empty-scan-roots", "non-list-scan-roots"]:
            with self.subTest(case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "active-path-guard",
                        "active-runtime-guard",
                        inputs={
                            "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/active-runtime-guard-cases.json",
                            "case_id": case_id,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 1)
                self.assert_response(response, "expected_failure")
                self.assertEqual([diag["code"] for diag in stderr_records], ["active_runtime_guard_blocked"])
                self.assertEqual(response["data"]["blocking_count"], 1)
                self.assertEqual({finding["category"] for finding in response["data"]["findings"]}, {"scan_root"})

        completed, response, stderr_records = run_runner(
            gate_request(
                "active-path-guard",
                "active-runtime-guard",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/active-runtime-guard-cases.json",
                    "case_id": "allowed-runtime-exceptions",
                },
            )
        )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        self.assertEqual(response["data"]["blocking_count"], 0)
        self.assertLessEqual(
            {
                "archive_provenance",
                "upstream_spec_kit_helper",
                "test_fixture",
                "ci_dispatch_glue",
            },
            set(response["data"]["classified_counts"]),
        )

        completed, response, stderr_records = run_runner(
            gate_request(
                "active-path-guard",
                "active-runtime-guard",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/active-runtime-guard-cases.json",
                    "case_id": "final-current-implementation",
                },
            )
        )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        self.assertEqual(response["data"]["blocking_count"], 0)

    def test_installed_release_payload_completeness_fixtures_cover_release_payload_blockers(self) -> None:
        cases = installed_release_fixture_cases("payload-completeness")
        self.assertEqual(cases["schema_version"], "1.0")
        self.assertEqual(cases["feature_id"], "XPLAT-008")
        self.assertEqual(
            {case["case_id"] for case in cases["cases"]},
            {
                "current-committed-dist",
                "empty-surfaces",
                "invalid-surfaces",
                "missing-runner-file",
                "stale-metadata",
                "extra-file",
                "path-leak",
                "transform-mismatch",
            },
        )
        for label in [
            "source-derived expected inventory",
            "apply-mode rebuild comparison",
            "missing runner file blocker",
            "stale metadata blocker",
            "extra file blocker",
            "path leak blocker",
            "empty surface selection blocker",
            "invalid surface selection blocker",
            "transform mismatch blocker",
        ]:
            self.assertIn(label, cases["coverage"])

        request = installed_release_fixture_request("payload-completeness")
        self.assertEqual(request["helper_id"], "payload-gate")
        self.assertEqual(request["operation"], "payload-completeness")
        self.assertEqual(request["mode"], "read_only")

        apply_request = installed_release_fixture_request("payload-completeness-apply")
        self.assertEqual(apply_request["helper_id"], "payload-gate")
        self.assertEqual(apply_request["operation"], "payload-completeness")
        self.assertEqual(apply_request["mode"], "apply")
        self.assertTrue(apply_request["inputs"]["apply_dist"])

    def test_plugin_bash_confinement_zero_bash_guard_fixtures_cover_source_payload_and_cache_proof(self) -> None:
        from speckit_pro_runner.gates import active_path_guard

        cases = plugin_bash_confinement_fixture_cases("zero-bash-guard")
        self.assertEqual(cases["schema_version"], "1.0")
        self.assertEqual(cases["feature_id"], "XPLAT-009")
        self.assertEqual(
            {case["case_id"] for case in cases["cases"]},
            {
                "clean-fixture",
                "blocking-active-source",
                "blocking-active-allowlist-entry",
                "blocking-missing-allowlist-fields",
                "blocking-unsupported-allowlist-field",
                "blocking-traversal-allowlist-path",
                "blocking-invalid-allowlist-line-bounds",
                "blocking-python-shell-exec",
                "blocking-uppercase-script-file",
                "blocking-suffixful-shell-script",
                "blocking-extensionless-script",
                "blocking-active-reference",
                "blocking-active-source-tree-language",
                "blocking-active-guidance-categories",
                "blocking-active-tool-declaration",
                "missing-scan-root",
                "missing-required-scan-root",
                "traversal-scan-root",
                "malformed-scan-root",
                "empty-scan-roots",
                "non-list-scan-roots",
                "missing-installed-cache-proof",
                "mutable-installed-cache-proof",
                "stale-installed-cache-proof",
                "single-product-installed-cache-proof",
                "missing-source-root-installed-cache-proof",
                "file-root-installed-cache-proof",
                "source-mismatch-installed-cache-proof",
                "same-root-installed-cache-proof",
                "product-root-mismatch-installed-cache-proof",
                "partial-root-installed-cache-proof",
                "traversal-root-installed-cache-proof",
                "missing-mutable-installed-cache-proof",
                "final-current-implementation",
            },
        )
        final_case = next(case for case in cases["cases"] if case["case_id"] == "final-current-implementation")
        self.assertLessEqual(
            {"speckit-pro", "scripts/build-plugin-payloads.py", "dist/claude/speckit-pro", "dist/codex/speckit-pro", "README.md"},
            set(final_case["scan_roots"]),
        )
        self.assertEqual(final_case["installed_cache_proof"], "docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json")
        self.assertEqual(
            json.loads((REPO_ROOT / final_case["installed_cache_proof"]).read_text(encoding="utf-8")),
            json.loads((PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR / "installed-cache-proof.json").read_text(encoding="utf-8")),
        )
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/usr/bin/env", "-S bash -lc jq -r . package.json"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["sh", "-c", "python -m speckit_pro_runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/bin/sh", "runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/usr/bin/env", "zsh", "runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/usr/bin/env", "-i", "sh", "-c", "python -m speckit_pro_runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["env", "FOO=bar", "zsh", "-c", "python -m speckit_pro_runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/usr/bin/env", "--ignore-environment", "sh", "-c", "python -m speckit_pro_runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/bin/sh", "--noprofile", "--norc", "-c", "python -m speckit_pro_runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/bin/zsh", "-o", "pipefail", "-c", "python -m speckit_pro_runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/usr/bin/env", "-S", "sh -c python -m speckit_pro_runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/usr/bin/env", "-S sh -c python -m speckit_pro_runner"]))
        with tempfile.TemporaryDirectory() as tmp:
            extensionless = Path(tmp) / "install"
            extensionless.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            self.assertEqual(active_path_guard.count_prohibited_script_files(extensionless), 1)
            zsh_script = Path(tmp) / "install.zsh"
            zsh_script.write_text("#!/usr/bin/env zsh\n", encoding="utf-8")
            self.assertEqual(active_path_guard.count_prohibited_script_files(zsh_script), 1)
            bash_script = Path(tmp) / "install.bash"
            bash_script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            self.assertEqual(active_path_guard.count_prohibited_script_files(bash_script), 1)
            oversized = Path(tmp) / "large-install"
            oversized.write_text("#!/usr/bin/env bash\n" + ("#" * (active_path_guard.MAX_SCAN_BYTES + 1)), encoding="utf-8")
            self.assertEqual(active_path_guard.count_prohibited_script_files(oversized), 1)
        with tempfile.TemporaryDirectory(prefix=".plugin-bash-confinement-large-script-", dir=PLUGIN_ROOT) as tmp:
            temp_root = Path(tmp)
            large_suffix_script = temp_root / "install.sh"
            large_suffix_script.write_text("#!/usr/bin/env bash\n" + ("#" * (active_path_guard.MAX_SCAN_BYTES + 1)), encoding="utf-8")
            large_extensionless_script = temp_root / "install"
            large_extensionless_script.write_text(
                "#!/usr/bin/env bash\n" + ("#" * (active_path_guard.MAX_SCAN_BYTES + 1)),
                encoding="utf-8",
            )
            sources = active_path_guard.scan_repo_sources(
                REPO_ROOT,
                roots=(temp_root.relative_to(REPO_ROOT).as_posix(),),
            )
            findings = active_path_guard.zero_bash_source_findings(sources, [])
            script_paths = {finding.path for finding in findings if finding.category == "script_file"}
            self.assertLessEqual(
                {
                    large_suffix_script.relative_to(REPO_ROOT).as_posix(),
                    large_extensionless_script.relative_to(REPO_ROOT).as_posix(),
                },
                script_paths,
            )
        with tempfile.TemporaryDirectory(prefix=".plugin-bash-confinement-symlink-", dir=PLUGIN_ROOT) as tmp:
            temp_root = Path(tmp)
            with tempfile.TemporaryDirectory() as outside:
                outside_script = Path(outside) / "install"
                outside_script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
                symlink = temp_root / "install"
                symlink.symlink_to(outside_script)
                sources = active_path_guard.scan_repo_sources(
                    REPO_ROOT,
                    roots=(temp_root.relative_to(REPO_ROOT).as_posix(),),
                )
            self.assertFalse([source for source in sources if source.path == symlink.relative_to(REPO_ROOT).as_posix()])
        with tempfile.TemporaryDirectory() as tmp:
            completed, response, stderr_records = run_runner(
                gate_request(
                    "active-path-guard",
                    "zero-bash-guard",
                    inputs={"repo_root": tmp},
                )
            )
            self.assertEqual(completed.returncode, 3)
            self.assert_response(response, "missing_prerequisite")
            self.assertEqual([diag["code"] for diag in stderr_records], ["missing_prerequisite"])
            self.assertEqual(response["data"]["gate"]["comparison_ids"], ["xplat-009-zero-bash-guard"])
            self.assertEqual(response["data"]["gate"]["gate_status"], "fail")
            self.assertEqual(response["data"]["feature_id"], "XPLAT-009")
            self.assertEqual(response["data"]["status"], "fail")
            self.assertEqual(response["data"]["blocking_count"], 1)
            self.assertEqual(
                response["data"]["gate"]["promotion_record"],
                "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/promotion-records.json",
            )

        completed, response, stderr_records = run_runner(
            gate_request(
                "active-path-guard",
                "zero-bash-guard",
                inputs={"case_file": "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/missing-case-file.json"},
            )
        )
        self.assertEqual(completed.returncode, 2)
        self.assert_response(response, "input_error")
        self.assertEqual([diag["code"] for diag in stderr_records], ["invalid_case_file"])
        self.assertEqual(response["data"]["gate"]["gate_status"], "fail")
        self.assertEqual(response["data"]["feature_id"], "XPLAT-009")
        self.assertEqual(response["data"]["status"], "fail")

        completed, response, stderr_records = run_runner(plugin_bash_confinement_fixture_request("zero-bash-guard"))
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        clean_response = response
        result = response["data"]
        self.assertEqual(result["feature_id"], "XPLAT-009")
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["blocking_count"], 0)
        self.assertEqual(result["script_file_count"], 0)
        self.assertTrue(result["allowlist"]["release_readiness_excluded"])
        self.assertEqual(result["installed_cache_proof"]["proof_count"], 2)
        self.assertTrue(result["installed_cache_proof"]["source_derived"])
        self.assertFalse(result["installed_cache_proof"]["mutable_user_cache"])

        scan_root_only_cases = {
            "missing-scan-root",
            "missing-required-scan-root",
            "traversal-scan-root",
            "malformed-scan-root",
            "empty-scan-roots",
            "non-list-scan-roots",
        }
        for case_id in [
            "blocking-active-source",
            "blocking-active-allowlist-entry",
            "blocking-missing-allowlist-fields",
            "blocking-unsupported-allowlist-field",
            "blocking-traversal-allowlist-path",
            "blocking-invalid-allowlist-line-bounds",
            "blocking-python-shell-exec",
            "blocking-uppercase-script-file",
            "blocking-suffixful-shell-script",
            "blocking-extensionless-script",
            "blocking-active-reference",
            "blocking-active-source-tree-language",
            "blocking-active-guidance-categories",
            "blocking-active-tool-declaration",
            "missing-scan-root",
            "missing-required-scan-root",
            "traversal-scan-root",
            "malformed-scan-root",
            "empty-scan-roots",
            "non-list-scan-roots",
            "missing-installed-cache-proof",
            "mutable-installed-cache-proof",
            "stale-installed-cache-proof",
            "single-product-installed-cache-proof",
            "missing-source-root-installed-cache-proof",
            "file-root-installed-cache-proof",
            "source-mismatch-installed-cache-proof",
            "same-root-installed-cache-proof",
            "product-root-mismatch-installed-cache-proof",
            "partial-root-installed-cache-proof",
            "traversal-root-installed-cache-proof",
            "missing-mutable-installed-cache-proof",
        ]:
            with self.subTest(case_id=case_id):
                response = run_plugin_bash_confinement_case(
                    case_id,
                    skip_source_scan=case_id in scan_root_only_cases,
                    skip_installed_root_scan=True,
                )
                self.assert_response(response, "expected_failure")
                self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["zero_bash_guard_blocked"])
                self.assertGreater(response["data"]["blocking_count"], 0)
                self.assertTrue(
                    all(finding["classification"] == "blocking_zero_bash" for finding in response["data"]["findings"])
                )

        expected_categories = {
            "blocking-active-source": {"bash", "git_bash", "jq", "script_file", "shell_command_wrapper", "shell_runtime", "shell_true", "wsl"},
            "blocking-missing-allowlist-fields": {"allowlist"},
            "blocking-unsupported-allowlist-field": {"allowlist"},
            "blocking-traversal-allowlist-path": {"allowlist"},
            "blocking-invalid-allowlist-line-bounds": {"allowlist"},
            "blocking-python-shell-exec": {"os_system", "shell_true", "command_string_subprocess", "command_argv_subprocess"},
            "blocking-uppercase-script-file": {"script_file"},
            "blocking-suffixful-shell-script": {"script_file"},
            "blocking-extensionless-script": {"script_file"},
            "blocking-active-reference": {"bash", "script_file", "wsl"},
            "blocking-active-source-tree-language": {"bash", "jq"},
            "blocking-active-guidance-categories": {
                "bash",
                "wsl",
                "script_file",
                "powershell_helper",
                "jq",
                "shell_interpolation",
                "shell_command_wrapper",
                "shell_runtime",
            },
            "blocking-active-tool-declaration": {"bash", "shell_runtime"},
            "missing-required-scan-root": {"scan_root"},
            "traversal-scan-root": {"scan_root"},
            "malformed-scan-root": {"scan_root"},
            "empty-scan-roots": {"scan_root"},
            "non-list-scan-roots": {"scan_root"},
            "mutable-installed-cache-proof": {"mutable_user_cache"},
            "stale-installed-cache-proof": {"source_payload_tree_hash"},
            "single-product-installed-cache-proof": {"product_coverage"},
            "missing-source-root-installed-cache-proof": {"source_payload_root"},
            "file-root-installed-cache-proof": {"installed_root"},
            "source-mismatch-installed-cache-proof": {"source_payload_tree_hash"},
            "same-root-installed-cache-proof": {"installed_root"},
            "product-root-mismatch-installed-cache-proof": {"installed_root", "source_payload_root"},
            "partial-root-installed-cache-proof": {
                "installed_root",
                "source_payload_root",
            },
            "traversal-root-installed-cache-proof": {"installed_root", "source_payload_root"},
            "missing-mutable-installed-cache-proof": {"mutable_user_cache"},
        }
        exact_category_cases = {case_id for case_id in expected_categories if case_id.endswith("-installed-cache-proof")}
        for case_id, categories in expected_categories.items():
            with self.subTest(case_id=f"{case_id}-categories"):
                response = run_plugin_bash_confinement_case(
                    case_id,
                    max_findings=20,
                    skip_source_scan=case_id in scan_root_only_cases,
                    skip_installed_root_scan=True,
                )
                self.assert_response(response, "expected_failure")
                actual_categories = {finding["category"] for finding in response["data"]["findings"]}
                if case_id in exact_category_cases:
                    self.assertEqual(actual_categories, categories)
                else:
                    self.assertLessEqual(categories, actual_categories)

        capped = active_path_guard.bounded_findings(
            [
                active_path_guard.RawFinding(
                    path=f"speckit-pro/file-{index}.py",
                    line=None,
                    category="bash",
                    pattern="bash",
                    reason="test",
                    active_role="test",
                    classification="blocking_zero_bash",
                    remediation="test",
                )
                for index in range(600)
            ],
            {"max_findings": 10000},
        )
        self.assertEqual(len(capped), 500)

        yaml_case = next(case for case in cases["cases"] if case["case_id"] == "blocking-active-guidance-categories")
        yaml_source = next(file for file in yaml_case["files"] if file["path"] == "speckit-pro/codex-agents/openai.yaml")
        yaml_findings = active_path_guard.zero_bash_source_findings(
            [active_path_guard.SourceFile(yaml_source["path"], yaml_source["content"], "fixture")],
            [],
        )
        yaml_records = {(finding.category, finding.line): finding.pattern for finding in yaml_findings}
        self.assertIn(("shell_command_wrapper", 2), yaml_records)
        self.assertIn("/bin/sh", yaml_records[("shell_command_wrapper", 2)])
        self.assertIn("-c", yaml_records[("shell_command_wrapper", 2)])
        self.assertIn(("shell_command_wrapper", 7), yaml_records)
        self.assertIn("/usr/bin/zsh", yaml_records[("shell_command_wrapper", 7)])
        self.assertIn("pipefail", yaml_records[("shell_command_wrapper", 7)])
        self.assertIn("-c", yaml_records[("shell_command_wrapper", 7)])
        self.assertIn(("shell_runtime", 14), yaml_records)
        self.assertIn("/bin/sh", yaml_records[("shell_runtime", 14)])
        self.assertIn("runner", yaml_records[("shell_runtime", 14)])
        self.assertIn(("shell_runtime", 16), yaml_records)
        self.assertIn("/bin/sh", yaml_records[("shell_runtime", 16)])
        self.assertIn(("shell_runtime", 18), yaml_records)
        self.assertIn("/usr/bin/zsh", yaml_records[("shell_runtime", 18)])

        python_case = next(case for case in cases["cases"] if case["case_id"] == "blocking-python-shell-exec")
        dynamic_python = next(file for file in python_case["files"] if file["path"].endswith("dynamic_shell.py"))
        dynamic_python_findings = active_path_guard.zero_bash_source_findings(
            [active_path_guard.SourceFile(dynamic_python["path"], dynamic_python["content"], "fixture")],
            [],
        )
        dynamic_python_records = {(finding.category, finding.line): finding.pattern for finding in dynamic_python_findings}
        self.assertIn(("shell_true", 8), dynamic_python_records)
        self.assertIn("shell=use_shell", dynamic_python_records[("shell_true", 8)])
        self.assertIn(("shell_true", 9), dynamic_python_records)
        self.assertIn("shell=1", dynamic_python_records[("shell_true", 9)])
        self.assertNotIn(("shell_true", 10), dynamic_python_records)
        self.assertIn(("command_string_subprocess", 11), dynamic_python_records)
        self.assertIn("subprocess.getoutput", dynamic_python_records[("command_string_subprocess", 11)])
        self.assertIn(("command_string_subprocess", 12), dynamic_python_records)
        self.assertIn("subprocess.getstatusoutput", dynamic_python_records[("command_string_subprocess", 12)])
        self.assertIn(("os_system", 13), dynamic_python_records)
        self.assertIn("os.popen", dynamic_python_records[("os_system", 13)])
        self.assertIn(("os_system", 14), dynamic_python_records)
        self.assertIn("os_popen", dynamic_python_records[("os_system", 14)])
        self.assertIn(("command_string_subprocess", 15), dynamic_python_records)
        self.assertIn("getoutput", dynamic_python_records[("command_string_subprocess", 15)])
        self.assertIn(("command_string_subprocess", 16), dynamic_python_records)
        self.assertIn("getstatusoutput", dynamic_python_records[("command_string_subprocess", 16)])

        self.assert_plugin_bash_confinement_contracts_match_fixtures(clean_response)

    def test_plugin_bash_confinement_installed_cache_proof_blocks_empty_payload_roots(self) -> None:
        with tempfile.TemporaryDirectory(prefix="plugin-bash-confinement-empty-", dir=REPO_ROOT / "dist" / "claude") as claude_root:
            with tempfile.TemporaryDirectory(prefix="plugin-bash-confinement-empty-", dir=REPO_ROOT / "dist" / "codex") as codex_root:
                with tempfile.TemporaryDirectory(prefix=".plugin-bash-confinement-proof-", dir=REPO_ROOT) as proof_root:
                    proof_dir = Path(proof_root)
                    proof_file = proof_dir / "installed-cache-proof-empty.json"
                    case_file = proof_dir / "zero-bash-empty-root-case.json"
                    proof_file.write_text(
                        json.dumps(
                            {
                                "schema_version": "1.0",
                                "feature_id": "XPLAT-009",
                                "proofs": [
                                    {
                                        "product": "claude",
                                        "surface": "claude_payload_fixture",
                                        "installed_root": Path(claude_root).relative_to(REPO_ROOT).as_posix(),
                                        "source_payload_root": Path(claude_root).relative_to(REPO_ROOT).as_posix(),
                                        "source_payload_tree_hash": "0" * 64,
                                        "source_derived": True,
                                        "mutable_user_cache": False,
                                        "script_file_count": 0,
                                        "active_guidance_findings": [],
                                        "allowlist_release_readiness_excluded": True,
                                    },
                                    {
                                        "product": "codex",
                                        "surface": "codex_payload_fixture",
                                        "installed_root": Path(codex_root).relative_to(REPO_ROOT).as_posix(),
                                        "source_payload_root": Path(codex_root).relative_to(REPO_ROOT).as_posix(),
                                        "source_payload_tree_hash": "0" * 64,
                                        "source_derived": True,
                                        "mutable_user_cache": False,
                                        "script_file_count": 0,
                                        "active_guidance_findings": [],
                                        "allowlist_release_readiness_excluded": True,
                                    },
                                ],
                            },
                            indent=2,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    case_file.write_text(
                        json.dumps(
                            {
                                "schema_version": "1.0",
                                "feature_id": "XPLAT-009",
                                "cases": [
                                    {
                                        "case_id": "empty-installed-cache-proof",
                                        "files": [
                                            {
                                                "path": "speckit-pro/skills/speckit-status/SKILL.md",
                                                "content": "Use python -m speckit_pro_runner.\n",
                                            }
                                        ],
                                        "allowlist_file": "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/allowlist.json",
                                        "installed_cache_proof": proof_file.relative_to(REPO_ROOT).as_posix(),
                                    }
                                ],
                            },
                            indent=2,
                        )
                        + "\n",
                        encoding="utf-8",
                    )

                    completed, response, _ = run_runner(
                        gate_request(
                            "active-path-guard",
                            "zero-bash-guard",
                            inputs={
                                "case_file": case_file.relative_to(REPO_ROOT).as_posix(),
                                "case_id": "empty-installed-cache-proof",
                            },
                        )
                    )

        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        categories = {finding["category"] for finding in response["data"]["findings"]}
        self.assertLessEqual({"source_payload_root", "installed_root"}, categories)

    def test_plugin_bash_confinement_installed_cache_proof_blocks_schema_drift(self) -> None:
        proof = json.loads((REPO_ROOT / "docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json").read_text(encoding="utf-8"))
        proof["proofs"][0].pop("surface")
        proof["proofs"][1]["product"] = "cursor"
        proof["proofs"][1]["unexpected_field"] = "drift"
        with tempfile.TemporaryDirectory(prefix=".plugin-bash-confinement-proof-schema-", dir=REPO_ROOT) as proof_root:
            proof_dir = Path(proof_root)
            proof_file = proof_dir / "installed-cache-proof-schema-drift.json"
            case_file = proof_dir / "zero-bash-proof-schema-drift-case.json"
            proof_file.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
            case_file.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "feature_id": "XPLAT-009",
                        "cases": [
                            {
                                "case_id": "schema-drift-installed-cache-proof",
                                "files": [
                                    {
                                        "path": "speckit-pro/skills/speckit-status/SKILL.md",
                                        "content": "Use python -m speckit_pro_runner.\n",
                                    }
                                ],
                                "allowlist_file": "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/allowlist.json",
                                "installed_cache_proof": proof_file.relative_to(REPO_ROOT).as_posix(),
                            }
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            completed, response, _ = run_runner(
                gate_request(
                    "active-path-guard",
                    "zero-bash-guard",
                    inputs={
                        "case_file": case_file.relative_to(REPO_ROOT).as_posix(),
                        "case_id": "schema-drift-installed-cache-proof",
                    },
                )
            )

        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        categories = {finding["category"] for finding in response["data"]["findings"]}
        self.assertLessEqual({"surface", "product", "malformed"}, categories)

    def test_plugin_bash_confinement_installed_cache_proof_scans_cache_text(self) -> None:
        installed_root = REPO_ROOT / "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro"
        with tempfile.TemporaryDirectory(prefix=".plugin-bash-confinement-active-cache-", dir=installed_root) as cache_root:
            cache_file = Path(cache_root) / "README.md"
            cache_file.write_text("Run Bash before continuing.\\n", encoding="utf-8")

            completed, response, _ = run_runner(plugin_bash_confinement_fixture_request("zero-bash-guard"))

        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        cache_findings = [
            finding
            for finding in response["data"]["findings"]
            if "installed-cache/claude/speckit-pro" in finding["path"]
        ]
        self.assertTrue(cache_findings)
        self.assertIn("bash", {finding["category"] for finding in cache_findings})

    def test_plugin_bash_confinement_zero_bash_guard_allows_missing_optional_installed_cache_proof(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".plugin-bash-confinement-optional-proof-", dir=REPO_ROOT) as scan_root:
            scan_dir = Path(scan_root)
            (scan_dir / "README.md").write_text("Python runner only.\n", encoding="utf-8")
            case_file = scan_dir / "zero-bash-optional-proof-case.json"
            case_file.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "feature_id": "XPLAT-009",
                        "cases": [
                            {
                                "case_id": "optional-proof-clean-root",
                                "scan_roots": [scan_dir.relative_to(REPO_ROOT).as_posix()],
                                "require_installed_cache_proof": False,
                                "allowlist_file": "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/allowlist.json",
                            }
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            completed, response, stderr_records = run_runner(
                gate_request(
                    "active-path-guard",
                    "zero-bash-guard",
                    inputs={
                        "case_file": case_file.relative_to(REPO_ROOT).as_posix(),
                        "case_id": "optional-proof-clean-root",
                    },
                )
            )

        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        self.assertFalse(response["data"]["installed_cache_proof"]["required"])
        self.assertEqual(response["data"]["installed_cache_proof"]["proof_count"], 0)
        self.assertEqual(response["data"]["blocking_count"], 0)

    def test_plugin_bash_confinement_zero_bash_guard_blocks_physical_uppercase_script_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".plugin-bash-confinement-uppercase-", dir=REPO_ROOT) as scan_root:
            scan_dir = Path(scan_root)
            (scan_dir / "RUN.SH").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            case_file = scan_dir / "zero-bash-uppercase-case.json"
            case_file.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "feature_id": "XPLAT-009",
                        "cases": [
                            {
                                "case_id": "physical-uppercase-script",
                                "scan_roots": [scan_dir.relative_to(REPO_ROOT).as_posix()],
                                "require_installed_cache_proof": False,
                                "allowlist_file": "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/allowlist.json",
                            }
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            completed, response, stderr_records = run_runner(
                gate_request(
                    "active-path-guard",
                    "zero-bash-guard",
                    inputs={
                        "case_file": case_file.relative_to(REPO_ROOT).as_posix(),
                        "case_id": "physical-uppercase-script",
                    },
                )
            )

        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        self.assertEqual([diag["code"] for diag in stderr_records], ["zero_bash_guard_blocked"])
        self.assertIn("script_file", {finding["category"] for finding in response["data"]["findings"]})

    def assert_plugin_bash_confinement_contracts_match_fixtures(self, response: dict[str, Any]) -> None:
        request_schema = json.loads((PLUGIN_BASH_CONFINEMENT_CONTRACT_DIR / "zero-bash-guard-request.schema.json").read_text(encoding="utf-8"))
        result_schema = json.loads((PLUGIN_BASH_CONFINEMENT_CONTRACT_DIR / "zero-bash-guard-result.schema.json").read_text(encoding="utf-8"))
        proof_schema = json.loads((PLUGIN_BASH_CONFINEMENT_CONTRACT_DIR / "installed-cache-proof.schema.json").read_text(encoding="utf-8"))
        allowlist_schema = json.loads((PLUGIN_BASH_CONFINEMENT_CONTRACT_DIR / "historical-allowlist-entry.schema.json").read_text(encoding="utf-8"))

        request = plugin_bash_confinement_fixture_request("zero-bash-guard")
        self.assertLessEqual(set(request_schema["required"]), set(request))
        self.assertEqual(request_schema["properties"]["operation"]["const"], request["operation"])
        self.assertEqual(request_schema["properties"]["mode"]["const"], request["mode"])
        input_schema = request_schema["properties"]["inputs"]
        self.assertLessEqual(set(input_schema["required"]), set(request["inputs"]))
        self.assertFalse(set(request["inputs"]) - set(input_schema["properties"]))

        self.assertIn(response["status"], result_schema["properties"]["status"]["enum"])
        data_schema = result_schema["properties"]["data"]
        self.assertLessEqual(set(data_schema["required"]), set(response["data"]))
        self.assertIsInstance(response["data"]["scan_roots"], list)
        for scan_root in response["data"]["scan_roots"]:
            self.assertIsInstance(scan_root, str)
        finding_schema = result_schema["$defs"]["finding"]
        for finding in response["data"]["findings"]:
            self.assertLessEqual(set(finding_schema["required"]), set(finding))
            self.assertFalse(set(finding) - set(finding_schema["properties"]))
            self.assertIn(finding["classification"], finding_schema["properties"]["classification"]["enum"])
            self.assertIn(finding["surface"], finding_schema["properties"]["surface"]["enum"])

        proof = json.loads((PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR / "installed-cache-proof.json").read_text(encoding="utf-8"))
        self.assertLessEqual(set(proof_schema["required"]), set(proof))
        self.assertEqual({item["product"] for item in proof["proofs"]}, {"claude", "codex"})
        proof_item_schema = proof_schema["$defs"]["proof"]
        for item in proof["proofs"]:
            self.assertLessEqual(set(proof_item_schema["required"]), set(item))
            self.assertFalse(set(item) - set(proof_item_schema["properties"]))
            self.assertNotEqual(item["installed_root"], item["source_payload_root"])

        allowlist = json.loads((PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR / "allowlist.json").read_text(encoding="utf-8"))
        entry_schema = allowlist_schema["$defs"]["entry"]
        for item in allowlist["entries"]:
            self.assertLessEqual(set(entry_schema["required"]), set(item))
            self.assertFalse(set(item) - set(entry_schema["properties"]))
            self.assertIn("categories", item)
            self.assertNotIn("category", item)

    def test_installed_release_payload_completeness_blocks_seeded_negative_cases(self) -> None:
        for case_id in ["missing-runner-file", "stale-metadata", "extra-file", "path-leak", "transform-mismatch"]:
            with self.subTest(case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "payload-gate",
                        "payload-completeness",
                        inputs={
                            "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/payload-completeness-cases.json",
                            "case_id": case_id,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 1)
                self.assert_response(response, "expected_failure")
                self.assertEqual([diag["code"] for diag in stderr_records], ["payload_completeness_blocked"])
                self.assertTrue(response["data"]["gate"]["blocking"])
                self.assertTrue(
                    any(result["status"] == "fail" for result in response["data"]["payload_completeness"])
                )
                self.assert_payload_completeness_contract_subset(response["data"]["payload_completeness"])
                if case_id == "path-leak":
                    failed = [result for result in response["data"]["payload_completeness"] if result["status"] == "fail"]
                    self.assertEqual(len(failed), 1)
                    self.assertEqual(failed[0]["path_leaks"], ["../outside-cache.txt"])
                    self.assertFalse(any(".." in item["path"].split("/") for item in failed[0]["actual_files"]))

        for case_id in ["empty-surfaces", "invalid-surfaces"]:
            with self.subTest(case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "payload-gate",
                        "payload-completeness",
                        inputs={
                            "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/payload-completeness-cases.json",
                            "case_id": case_id,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 2)
                self.assert_response(response, "input_error")
                self.assertEqual([diag["code"] for diag in stderr_records], ["invalid_payload_surface_selection"])

    def test_installed_release_payload_completeness_apply_builds_runner_payloads_without_shell(self) -> None:
        from speckit_pro_runner.gates import payloads as payload_gate

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "dist"
            sentinel = output_root / "claude" / "speckit-pro" / "sentinel.txt"
            sentinel.parent.mkdir(parents=True)
            sentinel.write_text("keep", encoding="utf-8")
            completed, response, stderr_records = run_runner(
                gate_request(
                    "payload-gate",
                    "payload-completeness",
                    mode="dry_run",
                    inputs={
                        "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/payload-completeness-cases.json",
                        "case_id": "current-committed-dist",
                        "output_root": output_root.as_posix(),
                    },
                )
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok")
            self.assertEqual(stderr_records, [])
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

        with tempfile.TemporaryDirectory() as tmp:
            output_root = str(Path(tmp) / "dist")
            request = gate_request(
                "payload-gate",
                "payload-completeness",
                mode="apply",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/payload-completeness-cases.json",
                    "case_id": "current-committed-dist",
                    "output_root": output_root,
                },
            )
            completed, response, stderr_records = run_runner(request)
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok")
            self.assertEqual(stderr_records, [])
            for surface in ["claude", "codex"]:
                payload_root = Path(output_root) / surface / "speckit-pro"
                self.assertTrue((payload_root / "speckit_pro_runner" / "__main__.py").is_file())
                self.assertTrue((payload_root / "speckit_pro_runner" / "speckit-pro-runner.manifest.json").is_file())
            for result in response["data"]["payload_completeness"]:
                self.assertEqual(result["status"], "pass")
                paths = {item["path"] for item in result["actual_files"]}
                self.assertIn("speckit_pro_runner/__main__.py", paths)
                self.assertIn("speckit_pro_runner/speckit-pro-runner.sha256", paths)

        with tempfile.TemporaryDirectory() as tmp:
            payload_root = Path(tmp) / "payload"
            for relative in ("scripts/install.sh", "scripts/install.bash", "scripts/install.zsh", "scripts/install.ps1", "scripts/install.bat", "scripts/install.cmd"):
                script = payload_root / relative
                script.parent.mkdir(parents=True, exist_ok=True)
                script.write_text("echo unsafe\n", encoding="utf-8")
            payload_gate.remove_payload_shell_scripts_xplat008(payload_root)
            for suffix in (".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd"):
                self.assertFalse([path for path in payload_root.rglob(f"*{suffix}")], suffix)
            extensionless = payload_root / "bin" / "install"
            extensionless.parent.mkdir(parents=True, exist_ok=True)
            extensionless.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            self.assertEqual(payload_gate.payload_script_file_count(payload_root, [{"path": "bin/install"}]), 1)
            suffixful = payload_root / "bin" / "install.zsh"
            suffixful.write_text("#!/usr/bin/env zsh\n", encoding="utf-8")
            self.assertEqual(payload_gate.payload_script_file_count(payload_root, [{"path": "bin/install.zsh"}]), 1)
            result = payload_gate.xplat008_payload_result(REPO_ROOT, "claude", payload_root, payload_root, {})
            self.assertEqual(result["script_file_count"], 2)
            self.assertEqual(result["status"], "fail")

    def test_installed_release_payload_completeness_current_dist_passes_after_runner_rebuild(self) -> None:
        completed, response, stderr_records = run_runner(installed_release_fixture_request("payload-completeness"))
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        self.assert_installed_release_promotion_metadata(
            response,
            "tests/speckit-pro/unit/fixtures/installed-plugin-release/payload-completeness-cases.json",
        )
        self.assertEqual({item["payload_surface"] for item in response["data"]["payload_completeness"]}, {"claude", "codex"})
        by_surface = {item["payload_surface"]: item for item in response["data"]["payload_completeness"]}
        claude_status = next(item for item in by_surface["claude"]["actual_files"] if item["path"] == "skills/speckit-status/SKILL.md")
        codex_status = next(item for item in by_surface["codex"]["actual_files"] if item["path"] == "skills/speckit-status/SKILL.md")
        self.assertEqual(claude_status["source_path"], "speckit-pro/skills/speckit-status/SKILL.md")
        self.assertEqual(codex_status["source_path"], "speckit-pro/codex-skills/speckit-status/SKILL.md")
        for result in response["data"]["payload_completeness"]:
            self.assertEqual(result["status"], "pass")
            self.assertFalse(result["missing_paths"])
            self.assertFalse(result["extra_paths"])
            self.assertFalse(result["mismatched_paths"])
            self.assertFalse(result["path_leaks"])
        self.assert_payload_completeness_contract_subset(response["data"]["payload_completeness"])

    def test_installed_release_payload_completeness_detects_stale_runner_trust_metadata(self) -> None:
        from speckit_pro_runner.gates import payloads as payload_gate

        with tempfile.TemporaryDirectory() as tmp:
            dist_root = Path(tmp) / "dist"
            payload_gate.build_xplat008_payloads(REPO_ROOT, dist_root)
            payload_root = dist_root / "claude" / "speckit-pro"
            runner_file = payload_root / "speckit_pro_runner" / "__main__.py"
            runner_file.write_text(runner_file.read_text(encoding="utf-8") + "\n# stale trust metadata test\n", encoding="utf-8")

            mismatches = payload_gate.payload_trust_metadata_mismatches(payload_root)

        self.assertEqual(
            set(mismatches),
            {
                "speckit_pro_runner/speckit-pro-runner.manifest.json",
                "speckit_pro_runner/speckit-pro-runner.sha256",
            },
        )

    def test_installed_release_readiness_fixtures_cover_release_blockers(self) -> None:
        promotion_records = json.loads((INSTALLED_RELEASE_FIXTURE_DIR / "promotion-records.json").read_text(encoding="utf-8"))
        self.assertEqual(promotion_records["schema_version"], "1.0")
        self.assertEqual(promotion_records["feature_id"], "XPLAT-008")
        self.assertEqual(promotion_records["promotion_status"], "installed_cutover_release_authoritative")
        self.assertLessEqual(
            {"runner-invocation", "active-path-guard", "payload-gate", "release-readiness"},
            {record["gate_id"] for record in promotion_records["records"]},
        )
        case_ids_by_operation = {
            "runner-invocation": {case["case_id"] for case in installed_release_fixture_cases("runner-invocation")["cases"]},
            "active-runtime-guard": {case["case_id"] for case in installed_release_fixture_cases("active-runtime-guard")["cases"]},
            "payload-completeness": {case["case_id"] for case in installed_release_fixture_cases("payload-completeness")["cases"]},
            "release-readiness-xplat008": {case["case_id"] for case in installed_release_fixture_cases("release-readiness")["cases"]},
        }
        for record in promotion_records["records"]:
            with self.subTest(promotion=record["python_operation"]):
                self.assertLessEqual(set(record["fixture_ids"]), case_ids_by_operation[record["python_operation"]])
        cases = installed_release_fixture_cases("release-readiness")
        self.assertEqual(cases["schema_version"], "1.0")
        self.assertEqual(cases["feature_id"], "XPLAT-008")
        self.assertEqual(
            {case["case_id"] for case in cases["cases"]},
            {
                "ready",
                "current-native-uat-pending",
                "active-shell-dependency",
                "incomplete-payload",
                "missing-bundled-agent",
                "missing-hook",
                "missing-runner-file",
                "stale-metadata",
                "unsafe-public-claim",
                "incomplete-uat",
                "unsafe-repair-claim",
                "missing-traceability",
                "nondeterministic-dist",
                "missing-release-evidence",
                "live-evidence-disabled",
                "failed-runner-invocation",
                "placeholder-uat",
                "smoke-only-uat",
                "raw-html-uat",
                "missing-uat-evidence-link",
                "incomplete-update-proof",
                "broad-reinstall-rejected",
            },
        )
        request = installed_release_fixture_request("release-readiness")
        self.assertEqual(request["helper_id"], "release-readiness")
        self.assertEqual(request["operation"], "release-readiness-xplat008")
        self.assertEqual(request["mode"], "read_only")
        runner_request = installed_release_fixture_request("runner-invocation")
        self.assertEqual(runner_request["inputs"]["case_id"], "live-host-runtime-info")
        release_workflow = (REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        for request_name in [
            "runner-invocation.json",
            "active-runtime-guard.json",
            "payload-completeness.json",
            "release-readiness.json",
        ]:
            self.assertIn(f"tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/{request_name}", release_workflow)

    def test_installed_release_uat_matrix_fixtures_cover_native_rows_and_blockers(self) -> None:
        cases = installed_release_fixture_cases("uat-matrix")
        self.assertEqual(cases["schema_version"], "1.0")
        self.assertEqual(cases["feature_id"], "XPLAT-008")
        ready_rows = cases["base_case"]["rows"]
        self.assertEqual(len(ready_rows), 6)
        self.assertEqual(
            {(row["product"], row["platform"]) for row in ready_rows},
            {
                ("claude", "windows"),
                ("claude", "macos"),
                ("claude", "linux"),
                ("codex", "windows"),
                ("codex", "macos"),
                ("codex", "linux"),
            },
        )
        for row in ready_rows:
            self.assertGreaterEqual(len(row["runner_invocation_ids"]), 3)
            self.assertEqual(row["latest_tag_update"], "pass")
            self.assertEqual(row["incomplete_install_repair"], "pass")
            self.assertNotIn("<a", row["evidence_link"])
        self.assertLessEqual(
            {
                "missing-row",
                "placeholder-row",
                "smoke-only-row",
                "failing-update-row",
                "raw-html-anchor",
                "empty-expected-result",
                "missing-evidence-link",
                "unsupported-native-support-claim",
            },
            {case["case_id"] for case in cases["cases"]},
        )
        request = installed_release_fixture_request("uat-matrix")
        self.assertEqual(request["helper_id"], "release-readiness")
        self.assertEqual(request["operation"], "uat-matrix")

    def test_installed_release_uat_matrix_reports_pass_and_seeded_blockers(self) -> None:
        completed, response, stderr_records = run_runner(installed_release_fixture_request("uat-matrix"))
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        matrix = response["data"]["uat_matrix"]
        self.assertEqual(matrix["status"], "pass")
        self.assertEqual(matrix["blocking_count"], 0)
        self.assertEqual(len(matrix["rows"]), 6)
        self.assert_uat_matrix_contract_subset(matrix)

        for case_id in [
            "missing-row",
            "placeholder-row",
            "smoke-only-row",
            "failing-update-row",
            "raw-html-anchor",
            "empty-expected-result",
            "missing-evidence-link",
            "unsupported-native-support-claim",
        ]:
            with self.subTest(case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "release-readiness",
                        "uat-matrix",
                        inputs={
                            "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/uat-matrix-cases.json",
                            "case_id": case_id,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 1)
                self.assert_response(response, "expected_failure")
                self.assertEqual([diag["code"] for diag in stderr_records], ["uat_matrix_blocked"])
                self.assertGreater(response["data"]["uat_matrix"]["blocking_count"], 0)

    def test_installed_release_install_health_repair_reports_safe_and_manual_outcomes(self) -> None:
        cases = installed_release_fixture_cases("install-health-repair")
        self.assertEqual(cases["schema_version"], "1.0")
        self.assertEqual(cases["feature_id"], "XPLAT-008")
        self.assertLessEqual(
            {
                "ready",
                "trusted-missing",
                "trusted-missing-metadata",
                "trusted-stale",
                "unsafe-unknown",
                "unsafe-extra",
                "unsafe-mismatch",
                "unsafe-trust-root-change",
                "unsafe-out-of-cache",
                "broad-reinstall-rejected",
            },
            {case["case_id"] for case in cases["cases"]},
        )

        completed, response, stderr_records = run_runner(installed_release_fixture_request("install-health-repair"))
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        health = response["data"]["install_health_repair"]
        self.assertEqual(health["status"], "pass")
        self.assertTrue(health["repair_actions"])
        self.assertEqual(health["repair_actions"][0]["action_type"], "autoheal_refresh")
        self.assertTrue(health["repair_actions"][0]["digest_verified"])

        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        self.assertEqual(MUTATION_HELPERS["install-health-repair"].modes, ("read_only",))

        for case_id in [
            "trusted-missing-metadata",
            "unsafe-unknown",
            "unsafe-extra",
            "unsafe-mismatch",
            "unsafe-trust-root-change",
            "unsafe-out-of-cache",
        ]:
            with self.subTest(case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "install-health-repair",
                        "install-health-repair",
                        inputs={
                            "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/install-health-repair-cases.json",
                            "case_id": case_id,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 0)
                self.assert_response(response, "ok")
                self.assertEqual(stderr_records, [])
                health = response["data"]["install_health_repair"]
                self.assertEqual(health["status"], "manual_remediation_required")
                self.assertEqual(health["repair_actions"][0]["action_type"], "manual_remediation")
                self.assertTrue(health["repair_actions"][0]["manual_steps"])

        completed, response, stderr_records = run_runner(
            gate_request(
                "install-health-repair",
                "install-health-repair",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/install-health-repair-cases.json",
                    "case_id": "broad-reinstall-rejected",
                },
            )
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        self.assertEqual([diag["code"] for diag in stderr_records], ["install_health_repair_blocked"])

    def test_installed_release_readiness_default_request_passes_after_native_uat_completion(self) -> None:
        completed, response, stderr_records = run_runner(installed_release_fixture_request("release-readiness"))
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        readiness = response["data"]["release_readiness"]
        self.assertEqual(readiness["feature_id"], "XPLAT-008")
        self.assertEqual(readiness["status"], "pass")
        self.assertEqual(readiness["blocking_count"], 0)
        self.assertEqual(len(readiness["uat_rows"]), 6)
        self.assertFalse(any(check["blocking"] for check in readiness["checks"]))
        zero_bash_checks = [check for check in readiness["checks"] if check["check_id"] == "zero-bash-guard"]
        self.assertEqual(len(zero_bash_checks), 1)
        self.assertEqual(zero_bash_checks[0]["blocker_class"], "active_zero_bash_dependency")
        self.assertIn("docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json", readiness["evidence_refs"]["zero_bash_guard"])
        self.assertTrue(all("script_file_count" in item for item in readiness["payload_results"]))
        self.assert_release_readiness_contract_subset(readiness)

    def test_installed_release_readiness_pending_native_uat_still_blocks(self) -> None:
        completed, response, stderr_records = run_runner(
            gate_request(
                "release-readiness",
                "release-readiness-xplat008",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/release-readiness-cases.json",
                    "case_id": "current-native-uat-pending",
                },
            )
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        self.assertEqual([diag["code"] for diag in stderr_records], ["release_readiness_xplat008_blocked"])
        readiness = response["data"]["release_readiness"]
        self.assertEqual(readiness["feature_id"], "XPLAT-008")
        self.assertEqual(readiness["status"], "fail")
        self.assertEqual(readiness["blocking_count"], 1)
        self.assertEqual(readiness["uat_rows"], [])
        self.assertTrue(any(check["check_id"] == "uat-matrix" and check["blocking"] for check in readiness["checks"]))
        self.assert_release_readiness_contract_subset(readiness)

    def test_installed_release_readiness_ready_fixture_passes(self) -> None:
        completed, response, stderr_records = run_runner(installed_release_fixture_request("release-readiness-ready"))
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        self.assert_installed_release_promotion_metadata(
            response,
            "tests/speckit-pro/unit/fixtures/installed-plugin-release/release-readiness-cases.json",
        )
        readiness = response["data"]["release_readiness"]
        self.assertEqual(readiness["feature_id"], "XPLAT-008")
        self.assertEqual(readiness["status"], "pass")
        self.assertEqual(readiness["blocking_count"], 0)
        self.assertEqual(len(readiness["payload_results"]), 2)
        self.assertEqual({item["payload_surface"] for item in readiness["payload_results"]}, {"claude", "codex"})
        self.assertEqual(len(readiness["uat_rows"]), 6)
        self.assertTrue(readiness["traceability"])
        self.assertNotIn("live_gate_requests", readiness["evidence_refs"])
        self.assertTrue(
            any(
                item.get("request_id") == "xplat-008-release-readiness:runner-invocation"
                for item in readiness["runner_invocations"]
            )
        )
        live_runner_record = next(
            item
            for item in readiness["runner_invocations"]
            if item.get("request_id") == "xplat-008-release-readiness:runner-invocation"
        )
        self.assertEqual(live_runner_record["runner_response"]["status"], "ok")
        self.assertEqual(
            live_runner_record["runner_response"]["data"]["report"]["source_vs_installed_context"],
            "installed_payload",
        )
        self.assertTrue(
            any(
                file_record["path"] == "speckit_pro_runner/speckit-pro-runner.manifest.json"
                for result in readiness["payload_results"]
                for file_record in result.get("actual_files", [])
            )
        )
        self.assert_release_readiness_contract_subset(readiness)

    def test_installed_release_readiness_seeded_blocker_cases_fail(self) -> None:
        blocker_cases = [
            "active-shell-dependency",
            "incomplete-payload",
            "missing-bundled-agent",
            "missing-hook",
            "missing-runner-file",
            "stale-metadata",
            "unsafe-public-claim",
            "incomplete-uat",
            "unsafe-repair-claim",
            "missing-traceability",
            "nondeterministic-dist",
            "missing-release-evidence",
            "live-evidence-disabled",
            "failed-runner-invocation",
            "placeholder-uat",
            "smoke-only-uat",
            "raw-html-uat",
            "missing-uat-evidence-link",
            "incomplete-update-proof",
            "broad-reinstall-rejected",
        ]
        for case_id in blocker_cases:
            with self.subTest(case_id=case_id):
                response = run_installed_release_readiness_case(case_id, live_evidence={})
                self.assert_response(response, "expected_failure")
                self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["release_readiness_xplat008_blocked"])
                self.assertGreater(response["data"]["release_readiness"]["blocking_count"], 0)
                self.assert_release_readiness_contract_subset(response["data"]["release_readiness"])

    def test_installed_release_readiness_handles_partial_failure_records(self) -> None:
        from speckit_pro_runner.gates import release as release_gate

        checks = release_gate.computed_xplat008_checks(
            payload_results=[{"status": "fail"}],
            uat_rows=[],
            repair_actions=[{"action_type": "manual_remediation"}],
            public_claim_results=[{"status": "fail"}],
            runner_invocations=[{"status": "blocked"}],
            traceability=[],
        )
        collapsed = release_gate.collapse_checks(checks)

        self.assertTrue(all("check_id" in check for check in collapsed))
        self.assertTrue(any(check["check_id"] == "payload-completeness" and check["blocking"] for check in collapsed))
        payload_check = next(check for check in collapsed if check["check_id"] == "payload-completeness")
        evidence = "\n".join(item for check in checks for item in check["evidence"])
        self.assertIn("unknown-payload", evidence)
        self.assertIn("scripted_payloads=unknown-payload:script_file_count=None", evidence)
        self.assertIn("unknown-repair-action", evidence)
        self.assertIn("unknown-public-claim", evidence)
        self.assertIn("unknown-runner-invocation", evidence)
        self.assertGreaterEqual(sum(1 for check in checks if check["blocking"]), 5)

        scripted_payload_checks = release_gate.computed_xplat008_checks(
            payload_results=[
                {"payload_surface": "claude", "status": "pass", "script_file_count": 1},
                {"payload_surface": "codex", "status": "pass", "script_file_count": 0},
            ],
            uat_rows=[],
            repair_actions=[{"action_id": "repair", "status": "completed"}],
            public_claim_results=[{"claim_id": "python-runner", "status": "pass"}],
            runner_invocations=[{"request_id": "runner", "status": "pass"}],
            traceability=[{"requirement_id": "FR-006"}],
        )
        scripted_payload_check = next(check for check in scripted_payload_checks if check["check_id"] == "payload-completeness")
        self.assertTrue(scripted_payload_check["blocking"])
        self.assertIn("scripted_payloads=claude:script_file_count=1", scripted_payload_check["evidence"])

        malformed_checks = release_gate.normalize_xplat008_checks(
            [
                {
                    "check_id": "public-claims",
                    "blocker_class": "unsafe_public_claim",
                    "status": "maybe",
                    "evidence": None,
                }
            ]
        )
        self.assertEqual(malformed_checks[0]["status"], "fail")
        self.assertTrue(malformed_checks[0]["blocking"])
        self.assertIn("malformed_check_record", malformed_checks[0]["evidence"])
        unknown_checks = release_gate.normalize_xplat008_checks(
            [
                {
                    "check_id": "unknown-check",
                    "blocker_class": "unknown-blocker",
                    "status": "pass",
                    "evidence": [],
                }
            ]
        )
        self.assertEqual(unknown_checks[0]["status"], "fail")
        self.assertTrue(unknown_checks[0]["blocking"])
        self.assertEqual(unknown_checks[0]["check_id"], "release-packet-traceability")
        self.assertIn("malformed_check_record", unknown_checks[0]["evidence"])

        malformed_contract_checks = release_gate.validate_xplat008_evidence_contracts(
            payload_results=release_gate.normalize_payload_results(
                [
                    "not-an-object",
                    {
                        "payload_surface": "claude",
                        "plugin_version": "2.17.0",
                        "runner_version": "0.1.0",
                        "expected_files": [{}],
                        "actual_files": ["bad-file-record"],
                        "missing_paths": [123],
                        "extra_paths": [None],
                        "mismatched_paths": [False],
                        "path_leaks": [{}],
                        "file_tree_hash": "2" * 64,
                        "status": "pass",
                    },
                ]
            ),
            uat_rows=[{"product": "codex", "platform": "macos", "status": "pass"}],
            repair_actions=[
                {
                    "action_id": "repair",
                    "finding_id": "finding",
                    "action_type": "manual_remediation",
                    "target_path": "install/cache",
                    "status": "blocked",
                    "message": "Manual remediation required.",
                    "manual_steps": [123],
                    "digest_verified": False,
                }
            ],
            public_claim_results=[
                {
                    "claim_id": "claim",
                    "surface": "docs",
                    "claim_text_or_pattern": "safe install",
                    "classification": "public",
                    "status": "pass",
                    "evidence": [123],
                }
            ],
            runner_invocations=[{"request_id": "runner", "status": "pass", "diagnostics": ["bad-diagnostic"]}],
            traceability=[{"requirement_id": "FR-006", "changed_files": [123], "verification_evidence": [None]}],
        )
        evidence = [evidence for check in malformed_contract_checks for evidence in check["evidence"]]
        for marker in [
            "malformed_payload_record:index=0",
            "malformed_uat_record:index=0",
            "malformed_repair_record:index=0",
            "malformed_public_claim_record:index=0",
            "malformed_runner_invocation_record:index=0",
            "malformed_traceability_record:index=0",
        ]:
            self.assertIn(marker, evidence)
        self.assertIn("missing_or_invalid=expected_files[0].path", evidence)
        self.assertIn("missing_or_invalid=actual_files[0]", evidence)
        self.assertIn("missing_or_invalid=missing_paths", evidence)
        self.assertIn("missing_or_invalid=extra_paths", evidence)
        self.assertIn("missing_or_invalid=mismatched_paths", evidence)
        self.assertIn("missing_or_invalid=path_leaks", evidence)
        self.assertIn("missing_or_invalid=manual_steps", evidence)
        self.assertIn("missing_or_invalid=evidence", evidence)
        self.assertIn("missing_or_invalid=diagnostics[0]", evidence)
        self.assertIn("missing_or_invalid=changed_files", evidence)
        self.assertIn("missing_or_invalid=verification_evidence", evidence)
        self.assertIn("missing_or_invalid=runner_request", evidence)
        self.assertIn("missing_or_invalid=surface_path", evidence)

        valid_repair_checks = release_gate.validate_xplat008_evidence_contracts(
            payload_results=[],
            uat_rows=[],
            repair_actions=[
                {
                    "action_id": "repair-1",
                    "finding_id": "install-cache-drift",
                    "action_type": "autoheal_refresh",
                    "target_path": "speckit-pro/install_inventory.json",
                    "source_path": "dist/codex/speckit-pro/install_inventory.json",
                    "digest_verified": True,
                    "status": "completed",
                    "message": "Refreshed stale install inventory from generated payload.",
                    "manual_steps": [],
                }
            ],
            public_claim_results=[],
            runner_invocations=[],
            traceability=[],
        )
        self.assertFalse([check for check in valid_repair_checks if "repair" in ",".join(check["evidence"])])

        duplicate_uat_rows = [release_gate.default_uat_row("claude", "windows", "pass") for _ in range(6)]
        duplicate_uat_checks = release_gate.computed_xplat008_checks(
            payload_results=[
                release_gate.synthetic_payload_result("claude", "pass"),
                release_gate.synthetic_payload_result("codex", "pass"),
            ],
            uat_rows=duplicate_uat_rows,
            repair_actions=[],
            public_claim_results=[
                {
                    "claim_id": "python-runner",
                    "surface": "README.md",
                    "claim_text_or_pattern": "Python runner",
                    "classification": "implemented-control",
                    "status": "pass",
                    "evidence": ["speckit-pro/speckit_pro_runner/runtime.py"],
                }
            ],
            runner_invocations=[
                {
                    "request_id": "runner",
                    "product": "codex",
                    "platform": "macos",
                    "surface_path": "speckit-pro/codex-skills/speckit-status/SKILL.md",
                    "operation": "status",
                    "interpreter_resolution": {"accepted": True},
                    "invocation": {"argv": ["python3", "-m", "speckit_pro_runner"], "shell_used": False},
                    "runner_request": {"operation": "runtime-info", "mode": "read_only", "inputs": {}},
                    "runner_response": {"status": "ok"},
                    "status": "pass",
                    "diagnostics": [],
                }
            ],
            traceability=[{"requirement_id": "FR-006", "changed_files": ["README.md"], "verification_evidence": ["test"]}],
        )
        uat_check = next(check for check in duplicate_uat_checks if check["check_id"] == "uat-matrix")
        self.assertTrue(uat_check["blocking"])
        self.assertIn("duplicate_rows=claude:windows", uat_check["evidence"])

    def test_run_default_suite_aggregates_success_stdout_stderr_and_exit_behavior(self) -> None:
        request = gate_request(
            "suite-gate",
            "run-default-suite",
            inputs={
                "suite": ["toolchain", "1", "4", "5", "7", "8"],
                "test_commands": {
                    "toolchain": successful_command("toolchain"),
                    "layer-1": successful_command("layer1"),
                    "layer-4": successful_command("layer4"),
                    "layer-5": successful_command("layer5"),
                    "layer-7": successful_command("layer7"),
                    "layer-8": successful_command("layer8"),
                },
            },
        )
        completed, response, stderr_records = run_runner(request)
        self.assertEqual(completed.returncode, 0)
        self.assert_stdout_json(completed)
        self.assert_response(response, "ok")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual(stderr_records, [])
        gate = response["data"]["gate"]
        self.assertEqual(gate["gate_id"], "suite-gate")
        self.assertEqual(gate["operation"], "run-default-suite")
        self.assertEqual(gate["gate_status"], "pass")
        self.assertTrue(gate["promoted"])
        self.assertFalse(gate["blocking"])
        summary = response["data"]["suite"]["summary"]
        self.assertEqual(summary, {"total": 6, "passed": 6, "failed": 0, "skipped": 0})
        results = response["data"]["suite"]["results"]
        self.assertEqual([result["command_id"] for result in results], ["toolchain", "layer-1", "layer-4", "layer-5", "layer-7", "layer-8"])
        for result in results:
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["exit_code"], 0)
            self.assertFalse(result["shell"])
            self.assertIsInstance(result["argv"], list)
            self.assertIn("stdout", result)
            self.assertIn("stderr", result)
            self.assertIn("stdout", result["stdout"]["text"])
            self.assertIn("stderr", result["stderr"]["text"])

    def test_default_suite_fixture_uses_python_authoritative_commands_without_shell_paths(self) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        request = fixture_request("run-default-suite")
        results = [
            suite_gate.command_spec(suite_gate.suite_item_to_command_id(item), request["inputs"], REPO_ROOT)
            for item in request["inputs"]["suite"]
        ]
        self.assertEqual(
            [result.command_id for result in results],
            ["toolchain", "layer-1", "layer-4", "layer-5", "layer-7", "layer-8"],
        )
        external_layer_argv = {
            "toolchain": [sys.executable, "tests/speckit-pro/check-toolchain.py", "--mode", "tests"],
            "layer-1": [sys.executable, "tests/speckit-pro/run-layer-scripts.py", "--layer", "1"],
            "layer-4": [sys.executable, "tests/speckit-pro/run-layer-scripts.py", "--layer", "4"],
            "layer-5": [sys.executable, "tests/speckit-pro/run-layer-scripts.py", "--layer", "5"],
            "layer-7": [sys.executable, "tests/speckit-pro/run-layer-scripts.py", "--layer", "7"],
            "layer-8": [sys.executable, "tests/speckit-pro/run-layer-scripts.py", "--layer", "8"],
        }
        for result in results:
            argv = list(result.argv)
            if result.command_id in external_layer_argv:
                self.assertEqual(argv, external_layer_argv[result.command_id])
                self.assertFalse(result.internal)
            else:
                self.assertEqual(argv, [sys.executable, "-m", "speckit_pro_runner"])
                self.assertTrue(result.internal)
            self.assertNotIn("bash", " ".join(argv).lower())
            self.assertNotIn("jq", " ".join(argv).lower())
            self.assertFalse(any(arg.endswith(".sh") for arg in argv))

    def test_missing_executable_treats_windows_altsep_paths_as_repo_relative(self) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        original_altsep = suite_gate.os.altsep
        try:
            suite_gate.os.altsep = "/"
            self.assertFalse(suite_gate.missing_executable("tests/speckit-pro/run-layer-scripts.py", REPO_ROOT))
        finally:
            suite_gate.os.altsep = original_altsep

        dispatcher = load_layer_script_dispatcher()
        layer1_scripts = [self.repo_rel(path) for path in dispatcher.canonical_test_scripts(REPO_ROOT, "1")]
        layer4_scripts = [self.repo_rel(path) for path in dispatcher.canonical_test_scripts(REPO_ROOT, "4")]
        self.assertGreaterEqual(len(layer1_scripts), 20)
        self.assertGreaterEqual(len(layer4_scripts), 17)
        self.assertIn("tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.py", layer1_scripts)
        self.assertIn("tests/speckit-pro/layer1-structural/validate-release-workflow.py", layer1_scripts)
        manifest = json.loads((REPO_ROOT / "tests/speckit-pro/suite-manifest.json").read_text(encoding="utf-8"))
        manifest_layer4 = next(layer for layer in manifest["layers"] if layer["id"] == "4")
        self.assertEqual(layer4_scripts, [script["path"] for script in manifest_layer4["scripts"]])
        self.assertTrue(all(path.endswith(".py") for path in layer4_scripts))

    def test_default_suite_without_explicit_suite_uses_python_authoritative_default(self) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        requested = suite_gate.requested_suite({})
        self.assertEqual(requested, suite_gate.DEFAULT_SUITE)
        self.assertEqual(
            [suite_gate.suite_item_to_command_id(item) for item in requested],
            ["toolchain", "layer-1", "layer-4", "layer-5"],
        )

    def test_suite_manifest_is_single_source_of_truth_for_roster_and_dispatch(self) -> None:
        # FR-007 drift guard: the shipped gate's advertised roster AND dispatch
        # kinds equal tests/speckit-pro/suite-manifest.json, exactly.
        from speckit_pro_runner.gates import suite as suite_gate

        manifest = json.loads((REPO_ROOT / "tests/speckit-pro/suite-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], "1.0")
        layers = manifest["layers"]

        default_suite = tuple(layer["id"] for layer in layers if layer["default"])
        extended_suite = tuple(layer["id"] for layer in layers if not layer["live_only"])
        allowed = frozenset(layer["id"] for layer in layers if not layer["live_only"] and layer["id"] != "toolchain")
        ai_layers = frozenset(layer["id"] for layer in layers if layer["live_only"])

        # (1) The module roster derives solely from the manifest.
        self.assertEqual(suite_gate.DEFAULT_SUITE, default_suite)
        self.assertEqual(suite_gate.EXTENDED_SUITE, extended_suite)
        self.assertEqual(suite_gate.ALLOWED_LAYERS, allowed)
        self.assertEqual(suite_gate.AI_EVAL_LAYERS, ai_layers)
        self.assertIsNone(suite_gate.SUITE_MANIFEST_ERROR)

        loaded = suite_gate.load_suite_manifest(REPO_ROOT)
        self.assertEqual(suite_gate.manifest_default_suite(loaded), default_suite)
        self.assertEqual(suite_gate.manifest_extended_suite(loaded), extended_suite)
        self.assertEqual(suite_gate.manifest_allowed_layers(loaded), allowed)

        # (2) Manifest dispatch kinds match the gate's actual command routing.
        dispatch_by_id = {layer["id"]: layer["dispatch"] for layer in layers}
        for item in extended_suite:
            with self.subTest(layer=item):
                spec = suite_gate.default_command_spec(suite_gate.suite_item_to_command_id(item), {}, REPO_ROOT)
                self.assertNotIsInstance(spec, dict, item)
                if item == "toolchain":
                    self.assertFalse(spec.internal)
                    self.assertIn("check-toolchain.py", " ".join(spec.argv))
                elif dispatch_by_id[item] == "internal-check":
                    self.assertTrue(spec.internal)
                elif dispatch_by_id[item] == "python-module":
                    self.assertFalse(spec.internal)
                    self.assertIn("run-layer-scripts.py", " ".join(spec.argv))
                else:
                    self.fail(f"unexpected deterministic dispatch {dispatch_by_id[item]!r} for layer {item}")

        # (3) Manifest-integrity invariant (a): every scripts[].path resolves.
        for layer in layers:
            for script in layer["scripts"]:
                with self.subTest(path=script["path"]):
                    self.assertEqual(set(script), {"path", "label", "baseline"})
                    self.assertTrue((REPO_ROOT / script["path"]).is_file(), script["path"])

        # (4) Manifest-integrity invariant (b): transitional Bash dispatch is
        # the only escape hatch permitted until PR 10; the current architecture
        # routes every layer via internal-check or a Python module, so none
        # remain (the FR-007 terminal-absence assertion already holds).
        self.assertEqual([layer["id"] for layer in layers if layer["dispatch"] == "shell-legacy-transitional"], [])

    def test_layer7_replay_runners_use_ported_python_module_only(self) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        manifest = json.loads((REPO_ROOT / "tests/speckit-pro/suite-manifest.json").read_text(encoding="utf-8"))
        layer7 = next(layer for layer in manifest["layers"] if layer["id"] == "7")

        self.assertEqual(layer7["dispatch"], "python-module")
        self.assertEqual(
            layer7["scripts"],
            [
                {
                    "path": "tests/speckit-pro/layer7-integration/run-all-fixtures.py",
                    "label": "run-all-fixtures",
                    "baseline": "tests/speckit-pro/parity/bash-to-python/run-all-fixtures-baseline.txt",
                }
            ],
        )
        spec = suite_gate.default_command_spec("layer-7", {}, REPO_ROOT)
        self.assertNotIsInstance(spec, dict)
        self.assertFalse(spec.internal)
        self.assertIn("run-layer-scripts.py", " ".join(spec.argv))
        self.assertFalse(hasattr(suite_gate, "check_layer7"), "native check_layer7 must retire at the Layer-7 port boundary")

        completed = subprocess.run(
            [sys.executable, "tests/speckit-pro/run-layer-scripts.py", "--layer", "7"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            env=runner_env(),
            shell=False,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr + completed.stdout)
        self.assertIn("layer-7 integration fixtures", completed.stdout)
        self.assertIn("PASS tests/speckit-pro/layer7-integration/run-all-fixtures.py", completed.stdout)

    def test_layer8_parity_runner_uses_ported_python_module_only(self) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        manifest = json.loads((REPO_ROOT / "tests/speckit-pro/suite-manifest.json").read_text(encoding="utf-8"))
        layer8 = next(layer for layer in manifest["layers"] if layer["id"] == "8")

        self.assertEqual(layer8["dispatch"], "python-module")
        self.assertEqual(
            layer8["scripts"],
            [
                {
                    "path": "tests/speckit-pro/layer8-parity/run-parity-fixtures.py",
                    "label": "run-parity-fixtures",
                    "baseline": "tests/speckit-pro/parity/bash-to-python/run-parity-fixtures-baseline.txt",
                }
            ],
        )
        spec = suite_gate.default_command_spec("layer-8", {}, REPO_ROOT)
        self.assertNotIsInstance(spec, dict)
        self.assertFalse(spec.internal)
        self.assertIn("run-layer-scripts.py", " ".join(spec.argv))
        self.assertFalse(hasattr(suite_gate, "check_layer8"), "native check_layer8 must retire at the Layer-8 port boundary")

        completed = subprocess.run(
            [sys.executable, "tests/speckit-pro/run-layer-scripts.py", "--layer", "8"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            env=runner_env(),
            shell=False,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr + completed.stdout)
        self.assertIn("layer-8 parity fixtures", completed.stdout)
        self.assertIn("PASS tests/speckit-pro/layer8-parity/run-parity-fixtures.py", completed.stdout)

    def test_suite_manifest_loader_fails_closed_when_absent_or_malformed(self) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(suite_gate.SuiteManifestError):
                suite_gate.load_suite_manifest(Path(tmp))

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "tests" / "speckit-pro"
            target.mkdir(parents=True)
            (target / "suite-manifest.json").write_text("{ not valid json", encoding="utf-8")
            with self.assertRaises(suite_gate.SuiteManifestError):
                suite_gate.load_suite_manifest(Path(tmp))

    def test_run_suite_gate_fails_closed_when_manifest_unavailable(self) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        entry = SimpleNamespace(helper_id="suite-gate")
        request = SimpleNamespace(operation="run-default-suite", request_id="drift-fail-closed", inputs={"repo_root": "."})
        with patch.object(suite_gate, "SUITE_MANIFEST_ERROR", "simulated manifest loss"):
            result = suite_gate.run_suite_gate(entry, request)
        self.assertEqual(result["status"], "missing_prerequisite")
        self.assertEqual([diag["code"] for diag in result["diagnostics"]], ["suite_manifest_unavailable"])

    def test_unknown_gate_operation_rejects_deterministically(self) -> None:
        response = self.assert_input_error_code(
            gate_request("suite-gate", "not-a-gate"),
            "unknown_gate_operation",
        )
        details = response["diagnostics"][0]["details"]
        self.assertEqual(details["helper_id"], "suite-gate")
        self.assertEqual(details["operation"], "not-a-gate")
        self.assertEqual(details["known_operations"], sorted(details["known_operations"]))
        self.assertIn("run-default-suite", details["known_operations"])

    def test_gate_operation_mismatch_and_mode_validation_are_deterministic(self) -> None:
        mismatch = self.assert_input_error_code(
            gate_request("payload-gate", "run-default-suite"),
            "gate_operation_mismatch",
        )
        self.assertEqual(mismatch["diagnostics"][0]["details"]["expected_helper_id"], "suite-gate")

        unsupported = self.assert_input_error_code(
            gate_request("release-readiness", "release-readiness", mode="apply"),
            "unsupported_gate_mode",
        )
        self.assertEqual(unsupported["diagnostics"][0]["details"]["supported_modes"], ["read_only"])

    def test_run_layer_expected_failure_preserves_streams_and_exit_mapping(self) -> None:
        request = gate_request(
            "suite-gate",
            "run-layer",
            inputs={
                "layer": "4",
                "test_commands": {
                    "layer-4": failing_command("layer4", exit_code=1),
                },
            },
        )
        completed, response, stderr_records = run_runner(request)
        self.assert_stdout_json(completed)
        self.assert_response(response, "expected_failure")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["gate_expected_failure"])
        self.assertEqual([diag["code"] for diag in stderr_records], ["gate_expected_failure"])
        result = response["data"]["suite"]["results"][0]
        self.assertEqual(result["command_id"], "layer-4")
        self.assertEqual(result["exit_code"], 1)
        self.assertEqual(result["status"], "expected_failure")
        self.assertIn("layer4 stdout", result["stdout"]["text"])
        self.assertIn("layer4 stderr", result["stderr"]["text"])
        self.assertEqual(response["data"]["gate"]["gate_status"], "fail")

    def test_run_layer_missing_dispatcher_reports_missing_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            (Path(tmp) / "speckit-pro" / "speckit_pro_runner").mkdir(parents=True)
            request = gate_request(
                "suite-gate",
                "run-layer",
                inputs={"layer": "1", "repo_root": tmp},
            )
            completed, response, stderr_records = run_runner(request)
        self.assert_stdout_json(completed)
        self.assert_response(response, "missing_prerequisite")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual([diag["code"] for diag in stderr_records], ["gate_missing_prerequisite"])
        result = response["data"]["suite"]["results"][0]
        self.assertEqual(result["command_id"], "layer-1")
        self.assertEqual(result["status"], "missing_prerequisite")
        self.assertEqual(result["exit_code"], 3)
        self.assertIn("tests/speckit-pro/run-layer-scripts.py", result["stderr"]["text"])

    def test_toolchain_integration_and_parity_suite_dispatch(self) -> None:
        cases = [
            ("run-toolchain-preflight", "toolchain"),
            ("run-integration-suite", "layer-7"),
            ("run-parity-suite", "layer-8"),
        ]
        for operation, command_id in cases:
            with self.subTest(operation=operation):
                request = gate_request(
                    "suite-gate",
                    operation,
                    inputs={"test_commands": {command_id: successful_command(command_id.replace("-", ""))}},
                )
                completed, response, stderr_records = run_runner(request)
                self.assert_stdout_json(completed)
                self.assert_response(response, "ok")
                self.assert_status_exit_mapping(completed, response)
                self.assertEqual(stderr_records, [])
                self.assertEqual(response["data"]["suite"]["results"][0]["command_id"], command_id)

    def test_run_ai_evals_dispatch_and_missing_prerequisites_are_stable(self) -> None:
        success = gate_request(
            "suite-gate",
            "run-ai-evals",
            inputs={"layers": ["2", "3", "6"], "test_overrides": {"available_tools": ["claude", "codex"]}},
        )
        completed, response, stderr_records = run_runner(success)
        self.assert_stdout_json(completed)
        self.assert_response(response, "ok")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual(stderr_records, [])
        planned_dispatch = response["data"]["suite"]["planned_dispatch"]
        self.assertEqual([plan["layer"] for plan in planned_dispatch], ["2", "3", "6"])
        manifest = json.loads((REPO_ROOT / "tests/speckit-pro/suite-manifest.json").read_text(encoding="utf-8"))
        manifest_paths = {
            layer["id"]: [script["path"] for script in layer["scripts"]]
            for layer in manifest["layers"]
            if layer["id"] in {"2", "3", "6"}
        }
        for plan in planned_dispatch:
            self.assertEqual(plan["runner_references"], manifest_paths[plan["layer"]])
            self.assertEqual(plan["bash_references"], [])
            self.assertTrue(all(path.endswith(".py") for path in plan["runner_references"]))

        missing = gate_request(
            "suite-gate",
            "run-ai-evals",
            inputs={"layers": ["2", "3", "6"], "test_overrides": {"available_tools": []}},
        )
        completed, response, stderr_records = run_runner(missing)
        self.assert_stdout_json(completed)
        self.assert_response(response, "missing_prerequisite")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["gate_missing_prerequisite"])
        self.assertEqual([diag["code"] for diag in stderr_records], ["gate_missing_prerequisite"])
        missing_by_layer = response["diagnostics"][0]["details"]["missing_by_layer"]
        self.assertEqual(set(missing_by_layer), {"2", "3", "6"})

    def test_unsafe_command_specs_are_rejected(self) -> None:
        unsafe_cases = [
            {"layer-1": "python -c 'print(1)'"},
            {"layer-1": {"argv": "python -c 'print(1)'"}},
            {"layer-1": {"argv": python_argv("print(1)"), "shell": True}},
            {"layer-1": {"argv": ["bash", "tests/speckit-pro/run-all.sh", "--layer", "1"]}},
            {"layer-1": {"argv": [sys.executable, "tests/speckit-pro/run-all.sh"]}},
            {"layer-1": {"argv": ["jq", "."]}},
        ]
        for commands in unsafe_cases:
            with self.subTest(commands=commands):
                response = self.assert_input_error_code(
                    gate_request("suite-gate", "run-layer", inputs={"layer": "1", "test_commands": commands}),
                    "unsafe_command_spec",
                )
                self.assertEqual(response["data"]["gate"]["operation"], "run-layer")

    def test_suite_commands_are_pinned_to_the_active_python_interpreter(self) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        default_spec = suite_gate.default_command_spec("layer-4", {}, REPO_ROOT)
        self.assertNotIsInstance(default_spec, dict)
        self.assertEqual(default_spec.argv[0], sys.executable)

        with tempfile.TemporaryDirectory() as temporary:
            foreign_python = Path(temporary) / ("python.exe" if os.name == "nt" else "python")
            foreign_python.write_bytes(b"")
            foreign_python.chmod(0o755)
            command = suite_gate.CommandSpec("foreign-python", (str(foreign_python), "-c", "print('unsafe')"))
            result = suite_gate.run_command(command, REPO_ROOT)

        self.assertEqual(result["status"], "input_error")
        self.assertEqual(result["exit_code"], 2)
        self.assertIn("active Python interpreter", result["stderr"]["text"])

    def test_payload_evidence_modes_are_fixture_bound_and_cutover_safe(self) -> None:
        completed, response, stderr_records = run_runner(fixture_request("test-payload-evidence"))
        self.assertEqual(completed.returncode, 0)
        self.assert_stdout_json(completed)
        self.assert_response(response, "ok")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual(stderr_records, [])
        evidence = response["data"]["payload_evidence"]
        self.assertEqual({item["payload_surface"] for item in evidence}, {"claude_test", "codex_test"})
        for item in evidence:
            self.assertEqual(item["mode"], "read_only")
            self.assertFalse(item["release_payload_cutover"])
            self.assertRegex(item["file_tree_hash"], r"^[a-f0-9]{64}$")
            self.assertTrue(item["files"])
            self.assertTrue(item["output_root"].startswith("tests/speckit-pro/unit/fixtures/runner-gates/"))

        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as tmp:
            output_root = self.repo_rel(Path(tmp) / "payload-output")
            dry_run_request = gate_request(
                "payload-gate",
                "build-test-payload-evidence",
                mode="dry_run",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/payload-evidence-cases.json",
                    "case_id": "claude-codex-test-payloads",
                    "output_root": output_root,
                    "release_payload_cutover": False,
                },
            )
            completed, response, stderr_records = run_runner(dry_run_request)
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok")
            self.assertEqual(stderr_records, [])
            self.assertFalse((REPO_ROOT / output_root).exists())

            apply_request = dict(dry_run_request)
            apply_request["request_id"] = "test-build-test-payload-evidence-apply"
            apply_request["mode"] = "apply"
            completed, response, stderr_records = run_runner(apply_request)
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok")
            self.assertEqual(stderr_records, [])
            written = sorted(path.name for path in (REPO_ROOT / output_root).glob("*.json"))
            self.assertEqual(written, ["claude-test-payload-evidence.json", "codex-test-payload-evidence.json"])
            for item in response["data"]["payload_evidence"]:
                self.assertEqual(item["mode"], "apply")
                self.assertFalse(item["release_payload_cutover"])

    def test_payload_evidence_rejects_release_cutover_and_stale_generated_payloads(self) -> None:
        release_cutover = gate_request(
            "payload-gate",
            "build-test-payload-evidence",
            inputs={
                "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/payload-evidence-cases.json",
                "case_id": "claude-codex-test-payloads",
                "output_root": "tests/speckit-pro/unit/fixtures/runner-gates/generated/payload-evidence",
                "release_payload_cutover": True,
            },
        )
        response = self.assert_input_error_code(release_cutover, "release_payload_cutover_refused")
        self.assertEqual(response["data"]["gate"]["operation"], "build-test-payload-evidence")

        stale = gate_request(
            "payload-gate",
            "build-test-payload-evidence",
            inputs={
                "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/payload-evidence-cases.json",
                "case_id": "stale-generated-files",
                "output_root": "tests/speckit-pro/unit/fixtures/runner-gates/generated/payload-evidence",
                "release_payload_cutover": False,
            },
        )
        completed, response, stderr_records = run_runner(stale)
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        self.assertEqual([diag["code"] for diag in stderr_records], ["stale_generated_payload_evidence"])

    def test_payload_evidence_filename_and_crlf_normalization_are_safe(self) -> None:
        from speckit_pro_runner.gates import payloads as payload_gate

        self.assertEqual(payload_gate.payload_evidence_filename("../bad\\surface_name"), "surface-name-payload-evidence.json")
        self.assertNotIn("/", payload_gate.payload_evidence_filename("nested/path/../surface"))
        self.assertNotIn("..", payload_gate.payload_evidence_filename("nested/path/../surface"))
        self.assertEqual(
            payload_gate.normalized_content("one\ntwo\r\nthree\r", {"installed_files": "from_inventory_crlf"}),
            "one\r\ntwo\r\nthree\r\n",
        )

    def test_install_verification_uses_fake_home_roots_and_command_plans_only(self) -> None:
        completed, response, stderr_records = run_runner(fixture_request("install-verification"))
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        install = response["data"]["install_verification"]
        self.assertEqual(install["status"], "complete")
        self.assertTrue(install["fake_home"])
        self.assertTrue(install["stubbed_cli"])
        self.assertGreaterEqual(install["bundled_agent_count"], 1)
        self.assertEqual(install["missing_files"], [])
        self.assertEqual(install["checksum_mismatches"], [])
        self.assertFalse(install["native_uat_claimed"])

        dry_run = gate_request(
            "install-verification",
            "refresh-local-plugin-fixture",
            mode="dry_run",
            inputs={
                "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/install-verification-cases.json",
                "case_id": "safe-repair-plan",
                "fake_home": True,
            },
        )
        completed, response, stderr_records = run_runner(dry_run)
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        install = response["data"]["install_verification"]
        self.assertEqual(install["status"], "safe_repair")
        self.assertTrue(install["safe_repairs"])
        for plan in install["command_plans"]:
            self.assert_no_shell_argv(plan["argv"])

        traversal = gate_request(
            "install-verification",
            "verify-install",
            inputs={
                "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/install-verification-cases.json",
                "case_id": "traversal-rejection",
                "fake_home": True,
            },
        )
        self.assert_input_error_code(traversal, "fixture_install_root_refused")

    def test_install_verification_handles_windows_paths_spaces_and_line_endings(self) -> None:
        for case_id in ["windows-style-paths", "line-ending-normalization"]:
            with self.subTest(case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "install-verification",
                        "verify-install",
                        inputs={
                            "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/install-verification-cases.json",
                            "case_id": case_id,
                            "fake_home": True,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 0)
                self.assert_response(response, "ok")
                self.assertEqual(stderr_records, [])
                install = response["data"]["install_verification"]
                self.assertEqual(install["status"], "complete")
                self.assertTrue(install["install_root"].startswith("tests/speckit-pro/unit/fixtures/runner-gates/"))

    def test_release_readiness_operations_report_pass_and_blocking_failures(self) -> None:
        pass_cases = [
            ("detect-changed-plugin", "ready", "changed_plugin"),
            ("detect-changed-plugin", "changed-plugin-false-positive", "changed_plugin"),
            ("validate-pr-title", "ready", "pr_title"),
        ]
        for operation, case_id, data_key in pass_cases:
            with self.subTest(operation=operation, case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "release-readiness",
                        operation,
                        inputs={
                            "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/release-readiness-cases.json",
                            "case_id": case_id,
                            "xplat_008_cutover_allowed": False,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 0)
                self.assert_response(response, "ok")
                self.assertEqual(stderr_records, [])
                self.assertIn(data_key, response["data"])
                self.assertEqual(response["data"]["release_check"]["status"], "pass")

        blocking_cases = [
            ("aggregate-suite-results", "suite-aggregation-failure"),
            ("check-marketplace-version-sync", "stale-version-data"),
            ("validate-workflow-contract", "workflow-contract-failure"),
            ("check-payload-evidence", "stale-payload-evidence"),
            ("parse-release-pr-payload-sync", "release-pr-payload-sync-parse-failure"),
            ("check-post-release-drift", "post-release-drift"),
        ]
        for operation, case_id in blocking_cases:
            with self.subTest(operation=operation, case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "release-readiness",
                        operation,
                        inputs={
                            "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/release-readiness-cases.json",
                            "case_id": case_id,
                            "xplat_008_cutover_allowed": False,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 1)
                self.assert_response(response, "expected_failure")
                self.assertEqual([diag["code"] for diag in stderr_records], ["release_check_failed"])
                self.assertTrue(response["data"]["release_check"]["blocking"])

    def test_release_readiness_aggregates_promotion_evidence_and_handoff_items(self) -> None:
        completed, response, stderr_records = run_runner(fixture_request("release-readiness"))
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        readiness = response["data"]["release_readiness"]
        self.assertEqual(readiness["status"], "pass")
        self.assertEqual(readiness["blocking_count"], 0)
        self.assertGreaterEqual(readiness["promotion_record_count"], 12)
        self.assertEqual(set(readiness["test_payload_evidence_ids"]), {"us2-claude-test-payload", "us2-codex-test-payload"})
        self.assertEqual(readiness["install_verification_ids"], ["us2-install-complete-fake-home"])
        self.assertEqual(readiness["active_path_guard_summary"], {"status": "ok", "blocking_count": 0})
        self.assertTrue(readiness["xplat_008_handoff_items"])
        self.assertEqual(
            {item["category"] for item in readiness["xplat_008_handoff_items"]},
            {
                "active_invocation_cutover",
                "generated_release_payload",
                "public_docs",
                "release_notes",
                "installed_cache_uat",
                "native_platform_uat",
                "update",
                "autoheal",
                "public_release_readiness",
            },
        )
        for item in readiness["xplat_008_handoff_items"]:
            self.assertEqual(item["owner_spec"], "XPLAT-008")

        missing_promotion = gate_request(
            "release-readiness",
            "release-readiness",
            inputs={
                "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/release-readiness-cases.json",
                "case_id": "missing-promotion-records",
                "xplat_008_cutover_allowed": False,
            },
        )
        completed, response, stderr_records = run_runner(missing_promotion)
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        self.assertEqual([diag["code"] for diag in stderr_records], ["release_readiness_blocked"])
        self.assertGreater(response["data"]["release_readiness"]["blocking_count"], 0)

    def test_detect_changed_plugin_requires_boolean_expected_value(self) -> None:
        from speckit_pro_runner.gates import release as release_gate

        check, details = release_gate.build_check(
            "detect-changed-plugin",
            {"changed_files": ["speckit-pro/speckit_pro_runner/runtime.py"], "expected_changed_plugin": 1},
        )
        self.assertEqual(check["status"], "fail")
        self.assertTrue(check["blocking"])
        self.assertTrue(details["changed_plugin"]["changed"])

    def test_release_readiness_live_github_context_uses_real_title_and_changed_files(self) -> None:
        request = fixture_request("release-readiness-live-github")
        request["inputs"]["github_context"]["changed_files"] = [
            "speckit-pro/speckit_pro_runner/gates/release.py",
            "tests/speckit-pro/unit/test-speckit-pro-gates.py",
        ]
        completed, response, stderr_records = run_runner(
            request,
            extra_env={"TITLE": "feat(xplat): live release readiness", "BASE_REF": "main"},
        )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        readiness = response["data"]["release_readiness"]
        self.assertEqual(readiness["status"], "pass")
        checks = {check["check_id"]: check for check in readiness["checks"]}
        self.assertEqual(checks["validate-pr-title"]["evidence"], ["feat(xplat): live release readiness"])
        self.assertEqual(checks["detect-changed-plugin"]["evidence"], ["changed_plugin=true"])

        request = fixture_request("release-readiness-live-github")
        request["inputs"]["github_context"]["changed_files"] = [
            "docs/prd-harness-engineering-uplift.md",
            "docs/ai/specs/harness-engineering-uplift-technical-roadmap.md",
        ]
        completed, response, stderr_records = run_runner(
            request,
            extra_env={"TITLE": "docs(specs): add harness engineering uplift roadmap", "BASE_REF": "main"},
        )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        readiness = response["data"]["release_readiness"]
        self.assertEqual(readiness["status"], "pass")
        checks = {check["check_id"]: check for check in readiness["checks"]}
        self.assertEqual(checks["validate-pr-title"]["evidence"], ["docs(specs): add harness engineering uplift roadmap"])
        self.assertEqual(checks["detect-changed-plugin"]["evidence"], ["changed_plugin=false"])

        request = fixture_request("release-readiness-live-github")
        request["inputs"]["github_context"]["changed_files"] = [
            "speckit-pro/speckit_pro_runner/gates/release.py"
        ]
        completed, response, stderr_records = run_runner(
            request,
            extra_env={"TITLE": "invalid title", "BASE_REF": "main"},
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        self.assertEqual([diag["code"] for diag in stderr_records], ["release_readiness_blocked"])
        failed_checks = {
            check["check_id"]
            for check in response["data"]["release_readiness"]["checks"]
            if check["blocking"]
        }
        self.assertIn("validate-pr-title", failed_checks)

    def test_active_path_guard_blocks_active_findings_and_exit_1(self) -> None:
        completed, response, stderr_records = run_runner(
            gate_request(
                "active-path-guard",
                "active-path-guard",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/active-path-guard-cases.json",
                    "case_id": "blocking-active-patterns",
                    "xplat_008_cutover_allowed": False,
                },
            )
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_stdout_json(completed)
        self.assert_response(response, "expected_failure")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["active_path_guard_blocked"])
        self.assertEqual([diag["code"] for diag in stderr_records], ["active_path_guard_blocked"])
        self.assertEqual(response["data"]["gate"]["gate_status"], "fail")
        self.assertTrue(response["data"]["gate"]["blocking"])

        categories = {finding["category"] for finding in response["data"]["findings"]}
        self.assertLessEqual(
            {
                "bash",
                "script_file",
                "jq",
                "git_bash",
                "wsl",
                "powershell_helper",
                "shell_parsing",
                "shell_interpolation",
                "shell_true",
                "os_system",
                "command_string_subprocess",
            },
            categories,
        )
        self.assertEqual(response["data"]["blocking_count"], len(response["data"]["findings"]))
        self.assertEqual(response["data"]["classified_counts"]["blocking_active_gate"], response["data"]["blocking_count"])

    def test_active_path_guard_classifies_nonblocking_findings(self) -> None:
        completed, response, stderr_records = run_runner(
            gate_request(
                "active-path-guard",
                "active-path-guard",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/active-path-guard-cases.json",
                    "case_id": "nonblocking-classifications",
                    "xplat_008_cutover_allowed": False,
                },
            )
        )
        self.assertEqual(completed.returncode, 0)
        self.assert_stdout_json(completed)
        self.assert_response(response, "ok")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual(stderr_records, [])
        self.assertEqual(response["data"]["blocking_count"], 0)
        self.assertEqual(
            {finding["classification"] for finding in response["data"]["findings"]},
            {
                "archive_provenance",
                "temporary_parity_evidence",
                "consumer_spec_kit_helper",
                "generated_payload_mirror",
                "docs_out_of_scope",
                "ci_dispatch_glue",
                "xplat_008_cutover_surface",
            },
        )

    def test_classify_shell_finding_blocks_active_gate_candidates(self) -> None:
        completed, response, stderr_records = run_runner(
            fixture_request("classify-shell-finding")
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_stdout_json(completed)
        self.assert_response(response, "expected_failure")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual([diag["code"] for diag in stderr_records], ["active_path_guard_blocked"])
        self.assertGreaterEqual(response["data"]["blocking_count"], 1)
        self.assertEqual(response["data"]["findings"][0]["classification"], "blocking_active_gate")
        self.assertEqual(
            response["data"]["classified_counts"]["blocking_active_gate"],
            response["data"]["blocking_count"],
        )

    def test_workflow_dispatch_glue_is_only_allowed_for_direct_python_gate_dispatch(self) -> None:
        good = gate_request(
            "active-path-guard",
            "active-path-guard",
            inputs={
                "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/active-path-guard-cases.json",
                "case_id": "workflow-dispatch-good",
                "xplat_008_cutover_allowed": False,
            },
        )
        completed, response, stderr_records = run_runner(good)
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        self.assertEqual(response["data"]["blocking_count"], 0)
        self.assertEqual([finding["classification"] for finding in response["data"]["findings"]], ["ci_dispatch_glue"])

        bad = gate_request(
            "active-path-guard",
            "active-path-guard",
            inputs={
                "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/active-path-guard-cases.json",
                "case_id": "workflow-dispatch-with-plugin-logic",
                "xplat_008_cutover_allowed": False,
            },
        )
        completed, response, stderr_records = run_runner(bad)
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        self.assertEqual([diag["code"] for diag in stderr_records], ["active_path_guard_blocked"])
        self.assertGreater(response["data"]["blocking_count"], 0)
        self.assertTrue(all(finding["classification"] == "blocking_active_gate" for finding in response["data"]["findings"]))

    def test_active_path_guard_request_fixture_scans_current_repo_clean(self) -> None:
        completed, response, stderr_records = run_runner(fixture_request("active-path-guard"))
        self.assertEqual(completed.returncode, 0)
        self.assert_stdout_json(completed)
        self.assert_response(response, "ok")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual(stderr_records, [])
        self.assertEqual(response["data"]["status"], "ok")
        self.assertEqual(response["data"]["blocking_count"], 0)
        self.assertGreater(sum(response["data"]["classified_counts"].values()), 0)

    def test_us2_gate_implementations_use_no_shell_true_os_system_or_command_string_subprocess(self) -> None:
        for module in ["payloads.py", "release.py"]:
            with self.subTest(module=module):
                path = PLUGIN_ROOT / "speckit_pro_runner" / "gates" / module
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call):
                        continue
                    if isinstance(node.func, ast.Attribute):
                        self.assertFalse(
                            node.func.attr == "system"
                            and isinstance(node.func.value, ast.Name)
                            and node.func.value.id == "os",
                            f"{module} must not use os.system",
                        )
                        if (
                            node.func.attr in {"run", "Popen", "call", "check_call", "check_output"}
                            and isinstance(node.func.value, ast.Name)
                            and node.func.value.id == "subprocess"
                        ):
                            for keyword in node.keywords:
                                self.assertFalse(
                                    keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True,
                                    f"{module} must not use shell=True",
                                )
                            if node.args:
                                self.assertFalse(
                                    isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str),
                                    f"{module} must not pass a command string to subprocess",
                                )

    def test_suite_implementation_uses_no_shell_true_os_system_or_command_string_subprocess(self) -> None:
        suite_path = PLUGIN_ROOT / "speckit_pro_runner" / "gates" / "suite.py"
        tree = ast.parse(suite_path.read_text(encoding="utf-8"), filename=suite_path.as_posix())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    self.assertFalse(
                        node.func.attr == "system"
                        and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "os",
                        "suite.py must not use os.system",
                    )
                    if (
                        node.func.attr in {"run", "Popen", "call", "check_call", "check_output"}
                        and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "subprocess"
                    ):
                        for keyword in node.keywords:
                            self.assertFalse(
                                keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True,
                                "suite.py must not use shell=True",
                            )
                        if node.args:
                            self.assertFalse(
                                isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str),
                                "suite.py must not pass a command string to subprocess",
                            )

    def test_promotion_records_cover_planned_groups(self) -> None:
        promotion_schema = json.loads((CONTRACT_DIR / "promotion-record.schema.json").read_text(encoding="utf-8"))
        document = json.loads(PROMOTION_RECORDS.read_text(encoding="utf-8"))
        self.assertEqual(document["schema_version"], "1.0")
        self.assertEqual(document["promotion_status"], "us3_python_authoritative")
        records = document["records"]
        self.assertLessEqual({"payload-gate", "install-verification", "release-readiness", "active-path-guard"}, {record["gate_id"] for record in records})
        us1_operations = {
            "run-default-suite": "tests/speckit-pro/run-all.sh",
            "run-toolchain-preflight": "tests/speckit-pro/check-toolchain.sh",
            "run-layer-1": "tests/speckit-pro/run-all.sh --layer 1",
            "run-layer-4": "tests/speckit-pro/run-all.sh --layer 4",
            "run-layer-5": "tests/speckit-pro/run-all.sh --layer 5",
            "run-integration-suite": "tests/speckit-pro/layer7-integration/run-all-fixtures.sh",
            "run-parity-suite": "tests/speckit-pro/layer8-parity/run-parity-fixtures.sh",
            "run-ai-evals": "tests/speckit-pro/run-all.sh --layer 2/3/6",
        }
        records_by_operation = {record["python_operation"]: record for record in records}
        for operation, bash_reference in us1_operations.items():
            with self.subTest(operation=operation):
                record = records_by_operation[operation]
                self.assertEqual(record["gate_id"], "suite-gate")
                self.assertEqual(record["prior_bash_gate"], bash_reference)
                self.assertTrue(record["fixture_ids"])
                self.assertTrue(record["bash_reference_ids"])
                self.assertEqual(record["comparison_mode"], "command_plan")
                self.assertEqual(record["exit_code_result"], "match")
                self.assertEqual(record["stream_result"], "match")
                self.assertEqual(record["artifact_result"], "not_applicable")
                self.assertEqual(record["active_path_guard_result"], "pass")
                self.assertEqual(record["bash_reference_retirement"], "inactive_parity_evidence")
                self.assertIn("promoted_at", record)
        us2_operations = {
            "build-test-payload-evidence": "scripts/build-plugin-payloads.py",
            "refresh-local-plugin-fixture": "scripts/refresh-local-plugin.sh",
            "verify-install": "scripts/refresh-local-plugin.sh",
            "detect-changed-plugin": ".github/workflows/pr-checks.yml",
            "aggregate-suite-results": ".github/workflows/pr-checks.yml",
            "check-marketplace-version-sync": "scripts/sync-marketplace-versions.sh",
            "validate-pr-title": ".github/workflows/pr-checks.yml",
            "validate-workflow-contract": ".github/workflows/pr-checks.yml",
            "check-payload-evidence": ".github/workflows/release.yml",
            "parse-release-pr-payload-sync": ".github/workflows/release.yml",
            "check-post-release-drift": ".github/workflows/release.yml",
            "release-readiness": ".github/workflows/release.yml",
        }
        for operation, bash_reference in us2_operations.items():
            with self.subTest(operation=operation):
                record = records_by_operation[operation]
                self.assertEqual(record["prior_bash_gate"], bash_reference)
                self.assertTrue(record["fixture_ids"])
                self.assertTrue(record["bash_reference_ids"])
                self.assertIn(record["comparison_mode"], {"artifact_hash", "command_plan", "json_semantic"})
                self.assertEqual(record["exit_code_result"], "match")
                self.assertEqual(record["stream_result"], "match")
                self.assertIn(record["artifact_result"], {"match", "not_applicable"})
                self.assertEqual(record["active_path_guard_result"], "pass")
                self.assertEqual(record["bash_reference_retirement"], "inactive_parity_evidence")
                self.assertIn("promoted_at", record)
        guard_record = records_by_operation["active-path-guard"]
        self.assertEqual(guard_record["gate_id"], "active-path-guard")
        self.assertEqual(guard_record["fixture_ids"], [
            "blocking-active-patterns",
            "nonblocking-classifications",
            "workflow-dispatch-good",
            "workflow-dispatch-with-plugin-logic",
            "final-current-implementation",
        ])
        self.assertEqual(guard_record["failure_classes"], ["active_path_guard_blocked", "xplat_008_cutover_refused"])
        self.assertEqual(guard_record["active_path_guard_result"], "pass")
        self.assertEqual(guard_record["bash_reference_retirement"], "not_applicable")
        self.assertIn("promoted_at", guard_record)
        required = set(promotion_schema["required"])
        allowed = set(promotion_schema["properties"])
        for record in records:
            self.assertLessEqual(required, set(record), record["gate_id"])
            self.assertFalse(set(record) - allowed, record["gate_id"])
            self.assertEqual(record["schema_version"], "1.0")
            self.assertTrue(record["rollback"])

    def test_contract_schemas_parse_as_json_objects(self) -> None:
        schema_paths = sorted(CONTRACT_DIR.glob("*.json"))
        self.assertEqual(len(schema_paths), 7)
        for schema_path in schema_paths:
            with self.subTest(schema=schema_path.name):
                parsed = json.loads(schema_path.read_text(encoding="utf-8"))
                self.assertIsInstance(parsed, dict)
                self.assertEqual(parsed["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(parsed["type"], "object")
                if schema_path.name == "migrated-gate-request.schema.json":
                    operations = set(parsed["properties"]["operation"]["enum"])
                    self.assertLessEqual(
                        {
                            "detect-changed-plugin",
                            "aggregate-suite-results",
                            "validate-pr-title",
                            "validate-workflow-contract",
                            "check-payload-evidence",
                            "parse-release-pr-payload-sync",
                            "check-post-release-drift",
                        },
                        operations,
                    )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GateFoundationTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed
    print(f"test-speckit-pro-gates: {passed}/{total} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
