#!/usr/bin/env python3
"""Foundation tests for XPLAT-007 runner gate dispatch."""

from __future__ import annotations

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

    def test_registry_lists_planned_gate_operations_without_active_cutover(self) -> None:
        from speckit_pro_runner.gates.registry import all_gate_operations, gate_registry_report

        report = gate_registry_report()
        self.assertEqual(report["schema_version"], "1.0")
        self.assertEqual(report["promotion_status"], "planned")
        self.assertFalse(report["active_cutover"])
        self.assertEqual(
            set(report["groups"]),
            {"suite", "payload", "install", "release", "guard"},
        )

        operations = all_gate_operations()
        self.assertGreaterEqual(len(operations), 20)
        for operation in operations:
            self.assertEqual(operation.promotion_status, "planned")
            self.assertFalse(operation.implemented)
            self.assertIn(operation.group, report["groups"])
            self.assertIn(operation.helper_id, report["gate_helper_ids"])

    def test_planned_gate_operation_rejects_until_story_implementation(self) -> None:
        response = self.assert_input_error_code(
            gate_request("suite-gate", "run-default-suite"),
            "gate_operation_not_implemented",
        )
        gate = response["data"]["gate"]
        self.assertEqual(gate["gate_id"], "suite-gate")
        self.assertEqual(gate["operation"], "run-default-suite")
        self.assertEqual(gate["gate_status"], "input_error")
        self.assertFalse(gate["promoted"])
        self.assertTrue(gate["blocking"])

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

    def test_promotion_records_cover_planned_groups(self) -> None:
        promotion_schema = json.loads((CONTRACT_DIR / "promotion-record.schema.json").read_text(encoding="utf-8"))
        document = json.loads(PROMOTION_RECORDS.read_text(encoding="utf-8"))
        self.assertEqual(document["schema_version"], "1.0")
        self.assertEqual(document["promotion_status"], "planned")
        records = document["records"]
        self.assertEqual(
            {record["gate_id"] for record in records},
            {"suite-gate", "payload-gate", "install-verification", "release-readiness", "active-path-guard"},
        )
        required = set(promotion_schema["required"])
        allowed = set(promotion_schema["properties"])
        for record in records:
            self.assertTrue(required <= set(record), record["gate_id"])
            self.assertFalse(set(record) - allowed, record["gate_id"])
            self.assertEqual(record["schema_version"], "1.0")
            self.assertEqual(record["comparison_mode"], "not_applicable")
            self.assertEqual(record["exit_code_result"], "not_applicable")
            self.assertEqual(record["stream_result"], "not_applicable")
            self.assertEqual(record["artifact_result"], "not_applicable")
            self.assertEqual(record["active_path_guard_result"], "not_run")
            self.assertEqual(record["bash_reference_retirement"], "not_applicable")
            self.assertTrue(record["rollback"])

    def test_request_fixture_root_exists_before_user_story_fixtures(self) -> None:
        self.assertTrue(REQUESTS_DIR.is_dir())
        self.assertEqual(sorted(REQUESTS_DIR.iterdir()), [])

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
