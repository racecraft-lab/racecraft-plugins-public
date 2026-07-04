#!/usr/bin/env python3
"""Foundation tests for XPLAT-007 runner gate dispatch."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "xplat-007-gates"
CONTRACT_DIR = REPO_ROOT / "specs" / "xplat-007-python-tooling-and-release-gate-migration" / "contracts"
PROMOTION_RECORDS = FIXTURE_DIR / "promotion-records.json"
REQUESTS_DIR = FIXTURE_DIR / "requests"

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


def run_runner(request: object) -> tuple[subprocess.CompletedProcess[str], dict[str, Any], list[dict[str, Any]]]:
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=json.dumps(request) if not isinstance(request, str) else request,
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        env=runner_env(),
        shell=False,
        check=False,
    )
    response = json.loads(completed.stdout) if completed.stdout.strip() else {}
    stderr_records = [json.loads(line) for line in completed.stderr.splitlines() if line.strip()]
    return completed, response, stderr_records


def fixture_request(name: str) -> dict[str, Any]:
    return json.loads((REQUESTS_DIR / f"{name}.json").read_text(encoding="utf-8"))


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
        self.assertEqual(report["promotion_status"], "mixed")
        self.assertFalse(report["active_cutover"])
        self.assertEqual(
            set(report["groups"]),
            {"suite", "payload", "install", "release", "guard"},
        )

        operations = all_gate_operations()
        self.assertGreaterEqual(len(operations), 20)
        us1_operations = {
            "run-default-suite",
            "run-layer",
            "run-toolchain-preflight",
            "run-ai-evals",
            "run-integration-suite",
            "run-parity-suite",
        }
        for operation in operations:
            if operation.operation in us1_operations:
                self.assertEqual(operation.group, "suite")
                self.assertEqual(operation.story, "US1")
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
        }
        self.assertEqual({path.name for path in REQUESTS_DIR.iterdir()}, expected)

        default_request = fixture_request("run-default-suite")
        self.assertEqual(default_request["helper_id"], "suite-gate")
        self.assertEqual(default_request["operation"], "run-default-suite")
        self.assertEqual(default_request["mode"], "read_only")
        self.assertEqual(default_request["inputs"]["suite"], ["toolchain", "1", "4", "5", "7", "8"])
        self.assertFalse(default_request["inputs"]["xplat_008_cutover_allowed"])

        for name in sorted(path.stem for path in REQUESTS_DIR.iterdir()):
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
        self.assertEqual(document["promotion_status"], "us1_python_authoritative")
        records = document["records"]
        self.assertTrue({"payload-gate", "install-verification", "release-readiness", "active-path-guard"} <= {record["gate_id"] for record in records})
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
        required = set(promotion_schema["required"])
        allowed = set(promotion_schema["properties"])
        for record in records:
            self.assertTrue(required <= set(record), record["gate_id"])
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


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GateFoundationTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed
    print(f"test-speckit-pro-gates: {passed}/{total} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
