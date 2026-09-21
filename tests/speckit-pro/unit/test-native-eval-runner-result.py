#!/usr/bin/env python3
"""Focused tests for controller-bound native runner results."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
sys.path.insert(0, str(TEST_ROOT / "lib"))

import native_eval_adapters  # noqa: E402
from native_eval_fixture_setup import materialize_workspace  # noqa: E402
from native_eval_grading import grade_observation  # noqa: E402
from native_eval_runner_result import (  # noqa: E402
    RunnerResultError,
    attach_receipt,
    bind_result,
)
from test_result import run_counted  # noqa: E402


REQUEST_PATH = "scenario-inputs/binding-request.json"
FIXTURE_ROOT = "tests/speckit-pro/evals/fixtures/functional/registered-worktree-migration"
WORKFLOW = "docs/ai/specs/.process/SPEC-107-workflow.md"
REQUEST = {
    "schema_version": "1.0",
    "request_id": "workflow-binding-preflight",
    "helper_id": "resolve-workflow-binding",
    "operation": "resolve-workflow-binding",
    "mode": "read_only",
    "inputs": {"workflow_file": "docs/ai/specs/.process/SPEC-107-workflow.md"},
}


def check() -> dict[str, object]:
    return {
        "id": "runner-binding", "requirement": "binding",
        "type": "native_runner_result", "request_path": REQUEST_PATH,
        "helper_id": "resolve-workflow-binding",
        "operation": "resolve-workflow-binding", "mode": "read_only",
        "expected_status": "expected_failure", "expected_exit_code": 1,
        "stdout_field_path": ["binding_status"],
        "expected_stdout_value": "ambiguous",
        "response_field_path": ["binding_result"],
    }


def native_case() -> dict[str, object]:
    return {
        "id": "functional.case-107",
        "requirements": [{"id": "binding", "description": "stop on ambiguity"}],
        "checks": [check()],
    }


def request_bytes(value: object = REQUEST) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def fixture(source: str, destination: str) -> dict[str, str]:
    payload = (REPO_ROOT / source).read_bytes()
    return {
        "source": source, "destination": destination,
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def stdout_value(status="ambiguous") -> dict[str, object]:
    return {
        "binding_status": status,
        "task_root": "/workspace",
        "workflow_root": None,
        "workflow_file": None,
        "relation": None,
        "candidates": ["/workspace", "/workspace/.worktrees/ambiguous"],
        "problems": ["workflow path exists in multiple registered worktrees"],
    }


def capture(text: str) -> dict[str, object]:
    encoded = text.encode()
    return {
        "text": text, "byte_count": len(encoded),
        "limit_bytes": 16 * 1024, "truncated": False,
    }


def response(status="ambiguous") -> dict[str, object]:
    stdout_json = stdout_value(status)
    stdout = json.dumps(stdout_json, separators=(",", ":")) + "\n"
    return {
        "schema_version": "1.0", "status": "expected_failure", "exit_code": 1,
        "legacy_exit_code": None,
        "diagnostics": [{"source": "runner", "code": "validation_failure"}],
        "request_id": REQUEST["request_id"],
        "data": {
            "helper_id": REQUEST["helper_id"], "operation": REQUEST["operation"],
            "mode": "read_only", "executed_in_process": True,
            "stdin_mode": "single_json_request",
            "stdin_request": {key: value for key, value in REQUEST.items()
                              if key != "request_id"},
            "shell": False, "exit_code": 1,
            "stdout": capture(stdout), "stderr": capture(""),
            "timed_out": False, "writes_state": False,
            "stdout_json": stdout_json,
        },
    }


def invocation(value=None, *, native_exit=1, request_path=REQUEST_PATH) -> dict[str, object]:
    value = response() if value is None else value
    return {
        "authority": "protected-native-runner", "call_id": "runner-call",
        "tool_call_index": 2, "request_path": request_path,
        "output": json.dumps(value, separators=(",", ":")),
        "success": False, "native_exit_code": native_exit,
    }


def observation(reported: object) -> dict[str, object]:
    return {
        "completed": True, "error": None,
        "final_text": json.dumps({
            "binding_result": reported, "decision": "stop",
            "next_action": "provide_absolute_workflow_path",
        }),
        "activations": [], "tool_calls": [], "artifacts": {}, "usage": {},
        "native_metadata": {},
    }


def bound(value=None, raw_request=None) -> dict[str, object]:
    payload = request_bytes() if raw_request is None else raw_request
    return bind_result(check(), invocation(value), payload)


class NativeEvalRunnerResultTests(unittest.TestCase):
    def test_real_runner_ambiguity_envelope_satisfies_the_binding_contract(self) -> None:
        baseline = f"{FIXTURE_ROOT}/ambiguous/baseline/{WORKFLOW}"
        feature = f"{FIXTURE_ROOT}/ambiguous/feature/{WORKFLOW}"
        request_source = f"{FIXTURE_ROOT}/ambiguous/binding-request.json"
        plan = {
            "schema_version": "native-eval-fixtures/v2",
            "source_root": str(REPO_ROOT),
            "fixtures": [
                fixture(feature, WORKFLOW),
                fixture(request_source, REQUEST_PATH),
            ],
            "git_repository": {
                "recipe": "baseline-feature-origin-main/v1",
                "baseline": [
                    fixture(baseline, WORKFLOW),
                    fixture(
                        "tests/speckit-pro/evals/fixtures/functional/autopilot-scenarios/common/project.json",
                        ".specify/project.json",
                    ),
                ],
                "worktrees": [{
                    "path": ".worktrees/ambiguous", "branch": "scenario/ambiguous",
                    "revision": "baseline",
                }],
            },
        }
        with tempfile.TemporaryDirectory(prefix="native-runner-real-") as temporary:
            workspace = Path(temporary) / "workspace"
            workspace.mkdir()
            materialize_workspace(plan, workspace)
            staged_request = (workspace / REQUEST_PATH).read_bytes()
            environment = {
                **os.environ, "PYTHONPATH": str(REPO_ROOT / "speckit-pro"),
                "PYTHONSAFEPATH": "1", "PYTHONDONTWRITEBYTECODE": "1",
                "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
            }
            completed = subprocess.run(
                [sys.executable, "-B", "-m", "speckit_pro_runner"], cwd=workspace,
                env=environment, input=staged_request, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, timeout=30, check=False,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr.decode())
            actual_invocation = invocation(
                json.loads(completed.stdout), native_exit=completed.returncode,
            )
            actual_invocation["output"] = completed.stdout.decode()
            receipt = bind_result(check(), actual_invocation, staged_request)
            self.assertEqual(receipt["actual"]["status"], "expected_failure")
            self.assertEqual(
                receipt["actual"]["stdout_json"]["binding_status"], "ambiguous",
            )

    def test_adapter_witnesses_the_controller_staged_request_bytes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="native-runner-witness-") as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            payload = request_bytes()
            (source / "request.json").write_bytes(payload)
            plan = root / "fixture-plan.json"
            plan.write_text(json.dumps({
                "schema_version": "native-eval-fixtures/v1",
                "source_root": str(source),
                "fixtures": [{
                    "source": "request.json", "destination": REQUEST_PATH,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }],
            }))
            value = native_case()
            value["fixtures"] = [{"source": "request.json", "destination": REQUEST_PATH}]
            self.assertEqual(
                native_eval_adapters._fixture_read_witnesses(value, plan),
                {REQUEST_PATH: {
                    "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
                }},
            )

    def test_genuine_expected_failure_and_exact_complete_report_pass(self) -> None:
        value = response()
        evidence = observation(value)
        attach_receipt(evidence, [bound(value)])
        result = grade_observation(native_case(), evidence)
        self.assertEqual(result["status"], "pass", result)

    def test_nested_controller_response_binding_passes(self) -> None:
        value = response()
        selected = value["data"]["stdout_json"]
        changed = native_case()
        changed["checks"][0]["response_value_path"] = ["data", "stdout_json"]
        evidence = observation(selected)
        attach_receipt(evidence, [bound(value)])

        result = grade_observation(changed, evidence)

        self.assertEqual(result["status"], "pass", result)

    def test_raw_formatting_and_canonical_request_identities_are_distinct(self) -> None:
        value = response()
        pretty = request_bytes()
        compact = json.dumps(REQUEST, separators=(",", ":")).encode()
        receipts = [bound(value, payload) for payload in (pretty, compact)]
        self.assertNotEqual(
            receipts[0]["actual"]["request_sha256"],
            receipts[1]["actual"]["request_sha256"],
        )
        self.assertNotEqual(
            receipts[0]["actual"]["request_bytes"],
            receipts[1]["actual"]["request_bytes"],
        )
        self.assertEqual(
            receipts[0]["actual"]["request_canonical_sha256"],
            receipts[1]["actual"]["request_canonical_sha256"],
        )
        self.assertEqual(
            receipts[0]["actual"]["request_canonical_bytes"],
            receipts[1]["actual"]["request_canonical_bytes"],
        )
        for receipt in receipts:
            with self.subTest(raw_bytes=receipt["actual"]["request_bytes"]):
                evidence = observation(value)
                attach_receipt(evidence, [receipt])
                self.assertEqual(grade_observation(native_case(), evidence)["status"], "pass")

    def test_response_only_claim_without_controller_authority_is_invalid(self) -> None:
        evidence = observation(response())
        self.assertEqual(grade_observation(native_case(), evidence)["status"], "invalid")
        evidence["native_metadata"]["controller_runner_results"] = {
            "schema": "subject-claim", "authority": "subject", "checks": [],
        }
        self.assertEqual(grade_observation(native_case(), evidence)["status"], "invalid")

    def test_authenticated_wrong_outcome_fails_even_when_report_matches(self) -> None:
        wrong = response("resolved")
        evidence = observation(wrong)
        attach_receipt(evidence, [bound(wrong)])
        self.assertEqual(grade_observation(native_case(), evidence)["status"], "fail")

    def test_wrong_or_missing_complete_report_is_behavioral_failure(self) -> None:
        actual = response()
        for reported in (response("resolved"), None):
            with self.subTest(reported=reported is not None):
                evidence = observation(reported)
                attach_receipt(evidence, [bound(actual)])
                self.assertEqual(grade_observation(native_case(), evidence)["status"], "fail")

    def test_wrong_request_path_or_staged_request_is_invalid(self) -> None:
        with self.assertRaisesRegex(RunnerResultError, "wrong request path"):
            bind_result(check(), invocation(request_path="other.json"), request_bytes())
        changed = copy.deepcopy(REQUEST)
        changed["inputs"]["workflow_file"] = "other.md"
        with self.assertRaisesRegex(RunnerResultError, "did not consume"):
            bind_result(check(), invocation(), request_bytes(changed))

    def test_duplicate_truncated_and_non_json_outputs_are_invalid(self) -> None:
        valid = json.dumps(response(), separators=(",", ":"))
        for output in (valid + valid, valid[:-1], "not-json"):
            bad = invocation()
            bad["output"] = output
            with self.subTest(output=output[-12:]), self.assertRaises(RunnerResultError):
                bind_result(check(), bad, request_bytes())

    def test_declared_and_native_exit_contradictions_are_invalid(self) -> None:
        wrong_declared = response()
        wrong_declared["exit_code"] = 0
        for bad in (invocation(native_exit=0), invocation(wrong_declared)):
            with self.subTest(native_exit=bad["native_exit_code"]), \
                    self.assertRaises(RunnerResultError):
                bind_result(check(), bad, request_bytes())

    def test_malformed_capture_and_boolean_as_integer_are_invalid(self) -> None:
        for field, value in (("truncated", True), ("byte_count", 0)):
            malformed = response()
            malformed["data"]["stdout"][field] = value
            with self.subTest(field=field), self.assertRaises(RunnerResultError):
                bind_result(check(), invocation(malformed), request_bytes())
        malformed = response()
        malformed["data"]["timed_out"] = 0
        with self.assertRaises(RunnerResultError):
            bind_result(check(), invocation(malformed), request_bytes())

    def test_tampered_controller_response_receipt_is_invalid(self) -> None:
        receipt = bound()
        receipt["actual"]["response"]["data"]["stdout_json"]["binding_status"] = "resolved"
        evidence = observation(response())
        attach_receipt(evidence, [receipt])
        self.assertEqual(grade_observation(native_case(), evidence)["status"], "invalid")

    def test_tampered_raw_and_canonical_request_identities_are_invalid(self) -> None:
        mutations = (
            ("request_sha256", "0" * 64),
            ("request_bytes", 1),
            ("request_raw_text", json.dumps({**REQUEST, "request_id": "changed"})),
            ("request_canonical_sha256", "0" * 64),
            ("request_canonical_bytes", 1),
        )
        for field, changed in mutations:
            with self.subTest(field=field):
                receipt = bound()
                receipt["actual"][field] = changed
                evidence = observation(response())
                attach_receipt(evidence, [receipt])
                self.assertEqual(
                    grade_observation(native_case(), evidence)["status"], "invalid",
                )

    def test_strict_json_types_prevent_boolean_integer_equivalence(self) -> None:
        value = response()
        value["data"]["stdout_json"]["binding_status"] = True
        stdout = json.dumps(value["data"]["stdout_json"], separators=(",", ":")) + "\n"
        value["data"]["stdout"] = capture(stdout)
        evidence = observation(value)
        attach_receipt(evidence, [bound(value)])
        changed = native_case()
        changed["checks"][0]["expected_stdout_value"] = 1
        self.assertEqual(grade_observation(changed, evidence)["status"], "fail")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeEvalRunnerResultTests)
    raise SystemExit(run_counted(suite, label="test-native-eval-runner-result"))
