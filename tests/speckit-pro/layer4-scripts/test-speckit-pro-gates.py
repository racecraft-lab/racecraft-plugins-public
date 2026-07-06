#!/usr/bin/env python3
"""Foundation tests for XPLAT-007 runner gate dispatch."""

from __future__ import annotations

import ast
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
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "xplat-007-gates"
CONTRACT_DIR = FIXTURE_DIR / "contracts"
PROMOTION_RECORDS = FIXTURE_DIR / "promotion-records.json"
REQUESTS_DIR = FIXTURE_DIR / "requests"
XPLAT_008_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "xplat-008-release"
XPLAT_008_REQUESTS_DIR = XPLAT_008_FIXTURE_DIR / "requests"
XPLAT_008_PROMOTION_RECORD = "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/promotion-records.json"

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


def xplat008_fixture_request(name: str) -> dict[str, Any]:
    return json.loads((XPLAT_008_REQUESTS_DIR / f"{name}.json").read_text(encoding="utf-8"))


def xplat008_fixture_cases(name: str) -> dict[str, Any]:
    return json.loads((XPLAT_008_FIXTURE_DIR / f"{name}-cases.json").read_text(encoding="utf-8"))


def python_argv(source: str) -> list[str]:
    return [sys.executable, "-c", source]


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

    def assert_xplat008_promotion_metadata(self, response: dict[str, Any], case_file: str) -> None:
        self.assertEqual(response["data"]["gate"]["promotion_record"], XPLAT_008_PROMOTION_RECORD)
        artifacts = response["data"].get("artifacts", [])
        self.assertIn({"path": XPLAT_008_PROMOTION_RECORD, "kind": "promotion_record"}, artifacts)
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
        schema = json.loads(
            (
                REPO_ROOT
                / "specs/xplat-008-claude-codex-cutover-universal-install-release-gate/contracts/payload-completeness.schema.json"
            ).read_text(encoding="utf-8")
        )
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
        schema = json.loads(
            (
                REPO_ROOT
                / "specs/xplat-008-claude-codex-cutover-universal-install-release-gate/contracts/release-readiness.schema.json"
            ).read_text(encoding="utf-8")
        )
        check_schema = schema["$defs"]["check"]["properties"]
        check_ids = set(check_schema["check_id"]["enum"])
        blocker_classes = set(check_schema["blocker_class"]["enum"])
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
        self.assertEqual(report["feature_id"], "XPLAT-007+XPLAT-008")
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
        xplat008_guard_operations = {
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
            "classify-shell-finding",
        }
        for operation in operations:
            if operation.operation in runtime_operations:
                self.assertEqual(operation.group, "runtime")
                self.assertEqual(operation.story, "US1")
                self.assertTrue(operation.implemented)
                self.assertEqual(operation.promotion_status, "python_authoritative")
            elif operation.operation in xplat008_guard_operations:
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

    def test_xplat008_runner_invocation_fixtures_cover_interpreter_resolution(self) -> None:
        cases = xplat008_fixture_cases("runner-invocation")
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

        request = xplat008_fixture_request("runner-invocation")
        self.assertEqual(request["helper_id"], "runner-invocation")
        self.assertEqual(request["operation"], "runner-invocation")
        self.assertEqual(request["mode"], "read_only")
        self.assertEqual(request["inputs"]["case_id"], "live-host-runtime-info")

    def test_xplat008_runner_invocation_records_have_no_shell_fallback(self) -> None:
        contract = json.loads(
            (
                REPO_ROOT
                / "specs/xplat-008-claude-codex-cutover-universal-install-release-gate/contracts/runner-invocation.schema.json"
            ).read_text(encoding="utf-8")
        )
        release_contract = json.loads(
            (
                REPO_ROOT
                / "specs/xplat-008-claude-codex-cutover-universal-install-release-gate/contracts/release-readiness.schema.json"
            ).read_text(encoding="utf-8")
        )
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
                            "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/runner-invocation-cases.json",
                            "case_id": case_id,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 0)
                self.assert_stdout_json(completed)
                self.assert_response(response, "ok")
                self.assert_status_exit_mapping(completed, response)
                self.assertEqual(stderr_records, [])
                self.assert_xplat008_promotion_metadata(
                    response,
                    "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/runner-invocation-cases.json",
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
                    "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/runner-invocation-cases.json",
                    "case_id": "live-host-runtime-info",
                },
            )
        )
        self.assertEqual(completed.returncode, 0)
        self.assert_stdout_json(completed)
        self.assert_response(response, "ok")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual(stderr_records, [])
        self.assert_xplat008_promotion_metadata(
            response,
            "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/runner-invocation-cases.json",
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
                    "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/runner-invocation-cases.json",
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

    def test_xplat008_active_runtime_guard_fixtures_block_only_active_runtime_findings(self) -> None:
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

        cases = xplat008_fixture_cases("active-runtime-guard")
        self.assertEqual(cases["schema_version"], "1.0")
        self.assertEqual(cases["feature_id"], "XPLAT-008")
        self.assertEqual(
            {case["case_id"] for case in cases["cases"]},
            {
                "blocking-active-runtime-patterns",
                "allowed-runtime-exceptions",
                "final-current-implementation",
            },
        )
        final_case = next(case for case in cases["cases"] if case["case_id"] == "final-current-implementation")
        self.assertFalse(final_case["scan_changed_sources"])
        self.assertIn(
            "final current implementation scans the full release surface without requiring PR review-base diff metadata",
            cases["coverage"],
        )
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
                        "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/active-runtime-guard-cases.json",
                        "case_id": "final-current-implementation",
                    },
                ),
                REPO_ROOT,
            )
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["data"]["blocking_count"], 0)

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
        missing_roots = active_path_guard.missing_xplat008_scan_root_findings(
            REPO_ROOT,
            {"scan_roots": ["dist/missing-runtime-root"]},
        )
        self.assertEqual(len(missing_roots), 1)
        self.assertEqual(missing_roots[0].classification, "blocking_active_runtime")
        self.assertEqual(missing_roots[0].category, "scan_root")

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
        self.assert_xplat008_promotion_metadata(
            response,
            "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/active-runtime-guard-cases.json",
        )

        completed, response, stderr_records = run_runner(
            gate_request(
                "active-path-guard",
                "active-runtime-guard",
                inputs={
                    "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/active-runtime-guard-cases.json",
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

        completed, response, stderr_records = run_runner(
            gate_request(
                "active-path-guard",
                "active-runtime-guard",
                inputs={
                    "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/active-runtime-guard-cases.json",
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
                    "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/active-runtime-guard-cases.json",
                    "case_id": "final-current-implementation",
                },
            )
        )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        self.assertEqual(response["data"]["blocking_count"], 0)

    def test_xplat008_payload_completeness_fixtures_cover_release_payload_blockers(self) -> None:
        cases = xplat008_fixture_cases("payload-completeness")
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

        request = xplat008_fixture_request("payload-completeness")
        self.assertEqual(request["helper_id"], "payload-gate")
        self.assertEqual(request["operation"], "payload-completeness")
        self.assertEqual(request["mode"], "read_only")

        apply_request = xplat008_fixture_request("payload-completeness-apply")
        self.assertEqual(apply_request["helper_id"], "payload-gate")
        self.assertEqual(apply_request["operation"], "payload-completeness")
        self.assertEqual(apply_request["mode"], "apply")
        self.assertTrue(apply_request["inputs"]["apply_dist"])

    def test_xplat008_payload_completeness_blocks_seeded_negative_cases(self) -> None:
        for case_id in ["missing-runner-file", "stale-metadata", "extra-file", "path-leak", "transform-mismatch"]:
            with self.subTest(case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "payload-gate",
                        "payload-completeness",
                        inputs={
                            "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/payload-completeness-cases.json",
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
                            "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/payload-completeness-cases.json",
                            "case_id": case_id,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 2)
                self.assert_response(response, "input_error")
                self.assertEqual([diag["code"] for diag in stderr_records], ["invalid_payload_surface_selection"])

    def test_xplat008_payload_completeness_apply_builds_runner_payloads_without_shell(self) -> None:
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
                        "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/payload-completeness-cases.json",
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
                    "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/payload-completeness-cases.json",
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

    def test_xplat008_payload_completeness_current_dist_passes_after_runner_rebuild(self) -> None:
        completed, response, stderr_records = run_runner(xplat008_fixture_request("payload-completeness"))
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        self.assert_xplat008_promotion_metadata(
            response,
            "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/payload-completeness-cases.json",
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

    def test_xplat008_payload_completeness_detects_stale_runner_trust_metadata(self) -> None:
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

    def test_xplat008_release_readiness_fixtures_cover_release_blockers(self) -> None:
        promotion_records = json.loads((XPLAT_008_FIXTURE_DIR / "promotion-records.json").read_text(encoding="utf-8"))
        self.assertEqual(promotion_records["schema_version"], "1.0")
        self.assertEqual(promotion_records["feature_id"], "XPLAT-008")
        self.assertEqual(promotion_records["promotion_status"], "installed_cutover_release_authoritative")
        self.assertLessEqual(
            {"runner-invocation", "active-path-guard", "payload-gate", "release-readiness"},
            {record["gate_id"] for record in promotion_records["records"]},
        )
        case_ids_by_operation = {
            "runner-invocation": {case["case_id"] for case in xplat008_fixture_cases("runner-invocation")["cases"]},
            "active-runtime-guard": {case["case_id"] for case in xplat008_fixture_cases("active-runtime-guard")["cases"]},
            "payload-completeness": {case["case_id"] for case in xplat008_fixture_cases("payload-completeness")["cases"]},
            "release-readiness-xplat008": {case["case_id"] for case in xplat008_fixture_cases("release-readiness")["cases"]},
        }
        for record in promotion_records["records"]:
            with self.subTest(promotion=record["python_operation"]):
                self.assertLessEqual(set(record["fixture_ids"]), case_ids_by_operation[record["python_operation"]])
        cases = xplat008_fixture_cases("release-readiness")
        self.assertEqual(cases["schema_version"], "1.0")
        self.assertEqual(cases["feature_id"], "XPLAT-008")
        self.assertEqual(
            {case["case_id"] for case in cases["cases"]},
            {
                "ready",
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
                "failed-runner-invocation",
            },
        )
        request = xplat008_fixture_request("release-readiness")
        self.assertEqual(request["helper_id"], "release-readiness")
        self.assertEqual(request["operation"], "release-readiness-xplat008")
        self.assertEqual(request["mode"], "read_only")
        runner_request = xplat008_fixture_request("runner-invocation")
        self.assertEqual(runner_request["inputs"]["case_id"], "live-host-runtime-info")
        release_workflow = (REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        for request_name in [
            "runner-invocation.json",
            "active-runtime-guard.json",
            "payload-completeness.json",
            "release-readiness.json",
        ]:
            self.assertIn(f"tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/requests/{request_name}", release_workflow)

    def test_xplat008_release_readiness_reports_pass_and_seeded_blockers(self) -> None:
        completed, response, stderr_records = run_runner(xplat008_fixture_request("release-readiness"))
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        self.assert_xplat008_promotion_metadata(
            response,
            "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/release-readiness-cases.json",
        )
        readiness = response["data"]["release_readiness"]
        self.assertEqual(readiness["feature_id"], "XPLAT-008")
        self.assertEqual(readiness["status"], "pass")
        self.assertEqual(readiness["blocking_count"], 0)
        self.assertEqual({item["payload_surface"] for item in readiness["payload_results"]}, {"claude", "codex"})
        self.assertEqual(len(readiness["uat_rows"]), 6)
        self.assertTrue(readiness["traceability"])
        self.assertIn("live_gate_requests", readiness["evidence_refs"])
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
            "failed-runner-invocation",
        ]
        for case_id in blocker_cases:
            with self.subTest(case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "release-readiness",
                        "release-readiness-xplat008",
                        inputs={
                            "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/release-readiness-cases.json",
                            "case_id": case_id,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 1)
                self.assert_response(response, "expected_failure")
                self.assertEqual([diag["code"] for diag in stderr_records], ["release_readiness_xplat008_blocked"])
                self.assertGreater(response["data"]["release_readiness"]["blocking_count"], 0)
                self.assert_release_readiness_contract_subset(response["data"]["release_readiness"])

    def test_xplat008_release_readiness_malformed_records_become_structured_blockers(self) -> None:
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
        self.assertIn("failing_payloads=unknown", payload_check["evidence"])

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
                        "missing_paths": [],
                        "extra_paths": [],
                        "mismatched_paths": [],
                        "path_leaks": [],
                        "file_tree_hash": "2" * 64,
                        "status": "pass",
                    },
                ]
            ),
            uat_rows=[{"product": "codex", "platform": "macos", "status": "pass"}],
            repair_actions=[{"action_id": "repair", "status": "pass"}],
            public_claim_results=[{"claim_id": "claim", "status": "pass"}],
            runner_invocations=[{"request_id": "runner", "status": "pass"}],
            traceability=[{"requirement_id": "FR-006"}],
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
        self.assertIn("missing_or_invalid=runner_request", evidence)
        self.assertIn("missing_or_invalid=surface_path", evidence)
        self.assertIn("missing_or_invalid=diagnostics", evidence)

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
        for result in results:
            argv = list(result.argv)
            self.assertEqual(argv, [sys.executable, "-m", "speckit_pro_runner"])
            self.assertNotIn("bash", " ".join(argv).lower())
            self.assertNotIn("jq", " ".join(argv).lower())
            self.assertFalse(any(arg.endswith(".sh") for arg in argv))
            self.assertTrue(result.internal)

    def test_missing_executable_treats_windows_altsep_paths_as_repo_relative(self) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        original_altsep = suite_gate.os.altsep
        try:
            suite_gate.os.altsep = "/"
            self.assertFalse(suite_gate.missing_executable("tests/speckit-pro/run-all.sh", REPO_ROOT))
        finally:
            suite_gate.os.altsep = original_altsep

        layer1_scripts = [self.repo_rel(path) for path in suite_gate.canonical_test_scripts(REPO_ROOT, "1")]
        layer4_scripts = [self.repo_rel(path) for path in suite_gate.canonical_test_scripts(REPO_ROOT, "4")]
        self.assertGreaterEqual(len(layer1_scripts), 20)
        self.assertGreaterEqual(len(layer4_scripts), 40)
        self.assertIn("tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.sh", layer1_scripts)
        self.assertIn("tests/speckit-pro/layer1-structural/validate-release-workflow.sh", layer1_scripts)
        self.assertIn("tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh", layer4_scripts)
        self.assertIn("tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py", layer4_scripts)
        self.assertIn("tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py", layer4_scripts)

    def test_default_suite_without_explicit_suite_uses_python_authoritative_default(self) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        requested = suite_gate.requested_suite({})
        self.assertEqual(requested, suite_gate.DEFAULT_SUITE)
        self.assertEqual(
            [suite_gate.suite_item_to_command_id(item) for item in requested],
            ["toolchain", "layer-1", "layer-4", "layer-5"],
        )

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
        self.assertEqual([plan["layer"] for plan in response["data"]["suite"]["planned_dispatch"]], ["2", "3", "6"])

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
            self.assertTrue(item["output_root"].startswith("tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/"))

        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as tmp:
            output_root = self.repo_rel(Path(tmp) / "payload-output")
            dry_run_request = gate_request(
                "payload-gate",
                "build-test-payload-evidence",
                mode="dry_run",
                inputs={
                    "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/payload-evidence-cases.json",
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
                "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/payload-evidence-cases.json",
                "case_id": "claude-codex-test-payloads",
                "output_root": "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/generated/payload-evidence",
                "release_payload_cutover": True,
            },
        )
        response = self.assert_input_error_code(release_cutover, "release_payload_cutover_refused")
        self.assertEqual(response["data"]["gate"]["operation"], "build-test-payload-evidence")

        stale = gate_request(
            "payload-gate",
            "build-test-payload-evidence",
            inputs={
                "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/payload-evidence-cases.json",
                "case_id": "stale-generated-files",
                "output_root": "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/generated/payload-evidence",
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
                "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/install-verification-cases.json",
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
                "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/install-verification-cases.json",
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
                            "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/install-verification-cases.json",
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
                self.assertTrue(install["install_root"].startswith("tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/"))

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
                            "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/release-readiness-cases.json",
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
                            "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/release-readiness-cases.json",
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
                "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/release-readiness-cases.json",
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
            "tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py",
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
                    "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/active-path-guard-cases.json",
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
                    "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/active-path-guard-cases.json",
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
                "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/active-path-guard-cases.json",
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
                "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/active-path-guard-cases.json",
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
            "build-test-payload-evidence": "scripts/build-plugin-payloads.sh",
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
