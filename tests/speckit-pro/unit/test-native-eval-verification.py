#!/usr/bin/env python3
"""Focused tests for native verification record and emission-pointer binding."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
sys.path.insert(0, str(TEST_ROOT / "lib"))

import native_eval_adapters  # noqa: E402
from native_eval_grading import grade_observation  # noqa: E402
from native_eval_verification import (  # noqa: E402
    ABSENCE_KIND,
    ABSENCE_SCHEMA,
    VerificationError,
    absence_bytes,
    absence_marker,
    absence_row,
    attach_receipt,
    bind_result,
    parse_runner_result,
    record_directories,
)
from test_result import run_counted  # noqa: E402


EXECUTION_ID = "a" * 32
SNAPSHOT = "b" * 64
RECORD_PATH = f".process/verification/{EXECUTION_ID}.json"
POINTER_PATH = "specs/parity-01/.process/emission/verification-pointer.json"


def check() -> dict[str, object]:
    return {
        "id": "verification", "requirement": "r1",
        "type": "native_verification_pointer", "workflow_file": "workflow.md",
        "command_id": "INTEGRATION_TEST", "pointer_path": POINTER_PATH,
        "reusable": False,
    }


def native_case() -> dict[str, object]:
    return {
        "id": "parity.01", "requirements": [{"id": "r1", "description": "verify"}],
        "checks": [check()],
    }


def record(*, workflow="workflow.md", command="INTEGRATION_TEST") -> dict[str, object]:
    return {
        "schema_version": "verification-record/v1", "execution_id": EXECUTION_ID,
        "dispatch_id": "verify", "command_id": command, "argv": ["python3", "verify.py"],
        "workflow_file": workflow, "snapshot_sha256": SNAPSHOT,
        "environment_sha256": "c" * 64, "output_directory": "/private/tmp/outputs",
        "toolchain": {}, "exit_code": 0, "stdout_sha256": "d" * 64,
        "stderr_sha256": "e" * 64, "inputs_unchanged": True,
        "snapshot_unchanged": True, "producer": "runner-isolated-project-command/v1",
        "completed": True, "elapsed_seconds": 0.1, "isolation_mode": "copy_only",
    }


def response(*, value=None, reusable=False) -> dict[str, object]:
    value = record() if value is None else value
    record_path = (Path(value["workflow_file"]).parent / ".process" / "verification"
                   / f"{value['execution_id']}.json").as_posix()
    return {
        "schema_version": "1.0", "status": "ok", "exit_code": 0,
        "legacy_exit_code": None, "diagnostics": [], "request_id": "verify-request",
        "data": {
            "record_path": record_path, "record": value, "observation_material": {},
            "writes_state": True, "reusable": reusable,
            "requires_independent_native_event": True, "authorization_granted": False,
            "rerun_required": True,
            "limitations": ["copy_only_is_not_qualified_immutable_isolation"],
            "helper_id": "execute-verification", "operation": "execute-verification",
            "mode": "apply", "promotion_status": "supported",
        },
    }


def encoded_record(value: dict[str, object]) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def invocation(value: dict[str, object] | None = None, *, reusable=False) -> dict[str, object]:
    return {
        "authority": "protected-native-runner", "success": True,
        "call_id": "native-call", "tool_call_index": 2,
        "output": json.dumps(response(value=value, reusable=reusable), separators=(",", ":")),
    }


def pointer(value: dict[str, object], record_bytes: bytes, *, reusable=False) -> dict[str, object]:
    return {
        "schema_version": "native-eval-verification-pointer/v1",
        "record_path": RECORD_PATH, "record_sha256": hashlib.sha256(record_bytes).hexdigest(),
        "execution_id": EXECUTION_ID, "command_id": value["command_id"],
        "snapshot_sha256": value["snapshot_sha256"], "reusable": reusable,
        "isolation_mode": value["isolation_mode"],
    }


def absence_identity(**overrides: object) -> dict[str, object]:
    identity: dict[str, object] = {
        "host": "codex", "root_thread_id": "root-thread-id", "root_trace_sha256": "f" * 64,
    }
    identity.update(overrides)
    return identity


def claude_absence_identity(**overrides: object) -> dict[str, object]:
    identity: dict[str, object] = {
        "host": "claude", "session_id": "session-id", "cwd": "/private/tmp/e-test/subject-cwd",
        "cli_version": "2.1.278", "public_trace_sha256": "a" * 64,
        "public_trace_bytes": 120, "retained_session_sha256": "b" * 64,
        "retained_session_bytes": 240, "activation_witness_sha256": "c" * 64,
        "framework_result_sha256": "d" * 64, "framework_result_bytes": 360,
    }
    identity.update(overrides)
    return identity


def absence_evidence(
    identity: dict[str, object] | None = None, *, artifact: object | None = None,
) -> dict[str, object]:
    evidence = observation()
    if artifact is not None:
        evidence["artifacts"][POINTER_PATH] = artifact
    attach_receipt(evidence, [absence_row(check(), identity or absence_identity())])
    return evidence


def observation(pointer_value: object | None = None) -> dict[str, object]:
    return {
        "completed": True, "error": None, "final_text": "done", "activations": [],
        "tool_calls": [], "artifacts": ({POINTER_PATH: json.dumps(pointer_value)}
                                        if pointer_value is not None else {}),
        "usage": {}, "native_metadata": {},
    }


def bound(*, value=None, reusable=False) -> tuple[dict[str, object], bytes]:
    value = record() if value is None else value
    payload = encoded_record(value)
    receipt = bind_result(check(), invocation(value, reusable=reusable), lambda _path: payload)
    return receipt, payload


class NativeEvalVerificationTests(unittest.TestCase):
    def test_adapter_declares_pointer_and_dynamic_record_directory(self) -> None:
        self.assertEqual(
            native_eval_adapters._declared_artifacts(native_case(), REPO_ROOT),
            (POINTER_PATH,),
        )
        self.assertEqual(record_directories(native_case()), (".process/verification",))

    def test_claude_capture_retains_dynamic_record_bytes_with_the_pointer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="native-verification-capture-") as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            attempt = root / "attempt"
            workspace.mkdir()
            attempt.mkdir()
            record_path = workspace / RECORD_PATH
            pointer_path = workspace / POINTER_PATH
            record_path.parent.mkdir(parents=True)
            pointer_path.parent.mkdir(parents=True)
            record_bytes = encoded_record(record())
            record_path.write_bytes(record_bytes)
            pointer_bytes = json.dumps(pointer(record(), record_bytes)).encode()
            pointer_path.write_bytes(pointer_bytes)
            workspace_fd = os.open(workspace, os.O_RDONLY)
            try:
                captured = native_eval_adapters._write_artifact_capture(
                    SimpleNamespace(attempt_dir=attempt), workspace_fd,
                    (POINTER_PATH,), (".process/verification",),
                )
            finally:
                os.close(workspace_fd)
            self.assertEqual((captured / RECORD_PATH).read_bytes(), record_bytes)
            self.assertEqual((captured / POINTER_PATH).read_bytes(), pointer_bytes)

    def test_genuine_copy_only_record_and_exact_pointer_pass(self) -> None:
        receipt, payload = bound()
        evidence = observation(pointer(record(), payload))
        attach_receipt(evidence, [receipt])
        result = grade_observation(native_case(), evidence)
        self.assertEqual(result["status"], "pass", result)
        self.assertIn("controller-bound", result["checks"][0]["reason"])

    def test_pointer_without_controller_authority_is_invalid(self) -> None:
        payload = encoded_record(record())
        evidence = observation(pointer(record(), payload))
        evidence["native_metadata"]["controller_verification"] = {
            "schema": "subject-claim", "authority": "subject", "checks": [],
        }
        self.assertEqual(grade_observation(native_case(), evidence)["status"], "invalid")

    def test_pointer_identity_hash_path_and_strict_boolean_mismatches_fail(self) -> None:
        receipt, payload = bound()
        valid = pointer(record(), payload)
        variants = {
            "path": {**valid, "record_path": ".process/verification/" + "f" * 32 + ".json"},
            "hash": {**valid, "record_sha256": "0" * 64},
            "execution": {**valid, "execution_id": "0" * 32},
            "command": {**valid, "command_id": "UNIT_TEST"},
            "snapshot": {**valid, "snapshot_sha256": "0" * 64},
            "reuse": {**valid, "reusable": True},
            "bool-int": {**valid, "reusable": 0},
        }
        for label, value in variants.items():
            with self.subTest(label=label):
                evidence = observation(value)
                attach_receipt(evidence, [copy.deepcopy(receipt)])
                self.assertEqual(grade_observation(native_case(), evidence)["status"], "fail")

    def test_duplicate_or_malformed_pointer_json_is_behavioral_failure(self) -> None:
        receipt, payload = bound()
        valid = pointer(record(), payload)
        duplicate_key = '"schema_version":"native-eval-verification-pointer/v1"'
        texts = [
            f"{{{duplicate_key},{duplicate_key}}}",
            '{"schema_version":',
        ]
        for text in texts:
            with self.subTest(text=text):
                evidence = observation()
                evidence["artifacts"][POINTER_PATH] = text
                attach_receipt(evidence, [copy.deepcopy(receipt)])
                self.assertEqual(grade_observation(native_case(), evidence)["status"], "fail")

    def test_missing_changed_or_malformed_record_is_invalid(self) -> None:
        with self.assertRaises(VerificationError):
            bind_result(check(), invocation(), lambda _path: b"")
        changed = record()
        changed["command_id"] = "UNIT_TEST"
        with self.assertRaises(VerificationError):
            bind_result(check(), invocation(), lambda _path: encoded_record(changed))
        malformed = encoded_record(record()) + b"{}"
        with self.assertRaises(VerificationError):
            bind_result(check(), invocation(), lambda _path: malformed)

    def test_duplicate_truncated_or_wrong_helper_response_is_invalid(self) -> None:
        valid = json.dumps(response(), separators=(",", ":"))
        integer_completion = response()
        integer_completion["data"]["record"]["completed"] = 1
        integer_reuse = response()
        integer_reuse["data"]["reusable"] = 0
        cases = [
            valid + valid,
            valid[:-1],
            json.dumps({"data": {"helper_id": "other"}}),
            json.dumps(integer_completion),
            json.dumps(integer_reuse),
        ]
        for output in cases:
            with self.subTest(output=output[-30:]), self.assertRaises(VerificationError):
                parse_runner_result(output)

    def test_invalid_native_invocation_identity_is_invalid(self) -> None:
        for field, value in (("authority", "subject"), ("success", False),
                             ("tool_call_index", True), ("call_id", "")):
            bad = invocation()
            bad[field] = value
            with self.subTest(field=field), self.assertRaises(VerificationError):
                bind_result(check(), bad, lambda _path: encoded_record(record()))

    def test_wrong_actual_workflow_and_unsupported_reuse_fail(self) -> None:
        wrong = record(workflow="other.md")
        wrong_payload = encoded_record(wrong)
        wrong_receipt = bind_result(check(), invocation(wrong), lambda _path: wrong_payload)
        wrong_pointer = pointer(wrong, wrong_payload)
        wrong_pointer["record_path"] = f".process/verification/{EXECUTION_ID}.json"
        evidence = observation(wrong_pointer)
        attach_receipt(evidence, [wrong_receipt])
        self.assertEqual(grade_observation(native_case(), evidence)["status"], "fail")

        reuse_receipt, reuse_payload = bound(reusable=True)
        reuse_pointer = pointer(record(), reuse_payload, reusable=True)
        reused = observation(reuse_pointer)
        attach_receipt(reused, [reuse_receipt])
        self.assertEqual(grade_observation(native_case(), reused)["status"], "fail")

    def test_same_fabricated_pointer_fails_independently_for_both_hosts(self) -> None:
        receipt, payload = bound()
        wrong = pointer(record(), payload)
        wrong["record_sha256"] = "0" * 64
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                evidence = observation(wrong)
                attach_receipt(evidence, [copy.deepcopy(receipt)])
                self.assertEqual(
                    grade_observation(native_case(), evidence, host=host)["status"], "fail"
                )

class NativeEvalAbsenceVerificationTests(unittest.TestCase):
    def test_complete_codex_root_trace_absence_grades_behavior_fail(self) -> None:
        evidence = absence_evidence()
        result = grade_observation(native_case(), evidence)
        self.assertEqual(result["status"], "fail", result)
        self.assertIn("proves zero native runner invocations", result["checks"][0]["reason"])
        self.assertEqual(evidence["artifacts"], {})

    def test_absence_is_bound_to_the_exact_check_and_root_trace_identity(self) -> None:
        marker = absence_marker(check(), absence_identity())
        self.assertEqual(set(marker["check"]), {
            "id", "workflow_file", "command_id", "pointer_path", "reusable",
        })
        self.assertEqual(marker["check"]["workflow_file"], "workflow.md")
        self.assertEqual(marker["root_trace"], {
            "schema": "codex-native-plan-repair-trace/v1", "thread_id": "root-thread-id",
            "raw_sha256": "f" * 64, "runner_invocation_count": 0,
        })
        self.assertEqual((marker["schema"], marker["kind"], marker["authority"]), (
            ABSENCE_SCHEMA, ABSENCE_KIND, "controller-bound-retained-native-evidence",
        ))
        payload = absence_bytes(check(), absence_identity())
        self.assertEqual(payload, (json.dumps(marker, sort_keys=True, separators=(",", ":"))
                                   + "\n").encode())
        self.assertEqual(absence_bytes(check(), absence_identity()), payload)
        self.assertEqual(absence_marker(check(), absence_identity()), marker)

    def test_claude_absence_is_a_distinct_exact_trace_variant(self) -> None:
        marker = absence_marker(check(), claude_absence_identity())
        self.assertEqual(marker["host"], "claude")
        self.assertNotIn("root_trace", marker)
        self.assertEqual(marker["claude_trace"], {
            "schema": "claude-plugin-eval-trace/v1", "session_id": "session-id",
            "cwd": "/private/tmp/e-test/subject-cwd", "cli_version": "2.1.278",
            "public_trace_sha256": "a" * 64, "public_trace_bytes": 120,
            "retained_session_sha256": "b" * 64, "retained_session_bytes": 240,
            "activation_witness_sha256": "c" * 64,
            "framework_result_sha256": "d" * 64, "framework_result_bytes": 360,
            "runner_invocation_count": 0,
        })
        evidence = observation()
        attach_receipt(evidence, [absence_row(check(), claude_absence_identity())])
        result = grade_observation(native_case(), evidence, host="claude")
        self.assertEqual(result["status"], "fail", result)
        self.assertIn("zero native runner invocations", result["checks"][0]["reason"])

    def test_claude_absence_identity_and_shape_variants_are_invalid(self) -> None:
        for identity in (
            claude_absence_identity(session_id=""),
            claude_absence_identity(public_trace_sha256="0" * 63),
            claude_absence_identity(public_trace_bytes=True),
            {**claude_absence_identity(), "extra": 1},
        ):
            with self.subTest(identity=identity), self.assertRaises(VerificationError):
                absence_marker(check(), identity)
        evidence = observation()
        row = absence_row(check(), claude_absence_identity())
        row["absence"]["claude_trace"]["runner_invocation_count"] = 1
        attach_receipt(evidence, [row])
        self.assertEqual(grade_observation(native_case(), evidence, host="claude")["status"],
                         "invalid")

    def test_subject_absence_marker_authority_and_identity_variants_are_invalid(self) -> None:
        def variant(mutate) -> dict[str, object]:
            evidence = absence_evidence()
            row = evidence["native_metadata"]["controller_verification"]["checks"][0]
            mutate(row)
            return evidence

        cases = {
            "subject-authority": lambda row: row["absence"].__setitem__("authority", "subject"),
            "subject-schema": lambda row: row["absence"].__setitem__("schema", "subject-claim"),
            "wrong-kind": lambda row: row["absence"].__setitem__("kind", "runner-ran"),
            "claude-host": lambda row: row["absence"].__setitem__("host", "claude"),
            "count-one": lambda row: row["absence"]["root_trace"].__setitem__(
                "runner_invocation_count", 1),
            "count-bool": lambda row: row["absence"]["root_trace"].__setitem__(
                "runner_invocation_count", True),
            "trace-hash": lambda row: row["absence"]["root_trace"].__setitem__(
                "raw_sha256", "not-a-digest"),
            "trace-thread": lambda row: row["absence"]["root_trace"].__setitem__("thread_id", ""),
            "check-command": lambda row: row["absence"]["check"].__setitem__(
                "command_id", "UNIT_TEST"),
            "check-workflow": lambda row: row["absence"]["check"].__setitem__(
                "workflow_file", "other.md"),
            "check-reuse": lambda row: row["absence"]["check"].__setitem__("reusable", True),
            "check-extra": lambda row: row["absence"]["check"].__setitem__("extra", "field"),
            "trace-extra": lambda row: row["absence"]["root_trace"].__setitem__("extra", 0),
            "row-extra": lambda row: row.__setitem__("call", {"id": "forged"}),
            "absence-missing": lambda row: row.__setitem__("absence", None),
            "check-mismatch": lambda row: row.__setitem__("check_id", "other"),
        }
        for label, mutate in cases.items():
            with self.subTest(label=label):
                self.assertEqual(
                    grade_observation(native_case(), variant(mutate))["status"], "invalid")

    def test_subject_output_cannot_manufacture_controller_absence(self) -> None:
        forged = json.dumps(absence_marker(check(), absence_identity()))
        unbound = observation(forged)
        self.assertEqual(grade_observation(native_case(), unbound)["status"], "invalid")

        claimed = observation()
        claimed["native_metadata"]["controller_verification"] = {
            "schema": ABSENCE_SCHEMA, "authority": "subject",
            "checks": [{"check_id": "verification",
                        "absence": absence_marker(check(), absence_identity())}],
        }
        self.assertEqual(grade_observation(native_case(), claimed)["status"], "invalid")

        forged_subject = absence_evidence()
        forged_subject["native_metadata"]["controller_verification"]["authority"] = "subject"
        self.assertEqual(
            grade_observation(native_case(), forged_subject)["status"], "invalid")

    def test_controller_absence_is_not_overwritten_by_subject_metadata(self) -> None:
        evidence = absence_evidence()
        with self.assertRaises(VerificationError):
            attach_receipt(evidence, [absence_row(check(), absence_identity())])
        evidence["native_metadata"]["controller_verification"] = {
            "schema": "subject-claim", "authority": "subject", "checks": [],
        }
        with self.assertRaises(VerificationError):
            attach_receipt(evidence, [absence_row(check(), absence_identity())])

    def test_subject_pointer_cannot_outrank_controller_absence(self) -> None:
        receipt, payload = bound()
        fabricated = json.dumps(pointer(record(), payload))
        self.assertIn("record_sha256", receipt["actual"])
        evidence = absence_evidence(artifact=fabricated)
        result = grade_observation(native_case(), evidence)
        self.assertEqual(result["status"], "fail", result)
        self.assertIn("absence", result["checks"][0]["reason"])

    def test_absence_identity_rejects_unsupported_or_malformed_traces(self) -> None:
        for identity in (
            absence_identity(host="claude"),
            absence_identity(root_thread_id=""),
            absence_identity(root_trace_sha256="0" * 63),
            {"host": "codex", "root_thread_id": "thread"},
            {"host": "codex", "root_thread_id": "thread", "root_trace_sha256": "f" * 64,
             "extra": 1},
        ):
            with self.subTest(identity=identity), self.assertRaises(VerificationError):
                absence_marker(check(), identity)
        with self.assertRaises(VerificationError):
            absence_marker({**check(), "command_id": "lowercase"}, absence_identity())
        with self.assertRaises(VerificationError):
            absence_row({**check(), "pointer_path": "../escape.json"}, absence_identity())

    def test_replay_rebinds_exact_bytes_and_detects_tamper(self) -> None:
        receipt, payload = bound()
        replayed = bind_result(check(), invocation(), lambda path: payload if path == RECORD_PATH else b"")
        self.assertEqual(replayed, receipt)
        tampered = bytearray(payload)
        tampered[-2] = ord(" ")
        with self.assertRaises(VerificationError):
            bind_result(check(), invocation(), lambda _path: bytes(tampered))


if __name__ == "__main__":
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(case)
        for case in (NativeEvalVerificationTests, NativeEvalAbsenceVerificationTests)
    )
    raise SystemExit(run_counted(suite, label="test-native-eval-verification"))
