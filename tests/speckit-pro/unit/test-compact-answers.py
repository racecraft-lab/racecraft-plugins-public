#!/usr/bin/env python3
"""Compact root answers through the public request/dispatch seam."""
from __future__ import annotations

import json
import hashlib
import itertools
import subprocess
import tempfile
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "speckit-pro"))
sys.path.insert(0, str(REPO / "tests/speckit-pro/lib"))
from speckit_pro_runner.envelope import COMPACT_EXECUTION_HISTORY_LIMIT_BYTES, parse_request, response  # noqa: E402
from speckit_pro_runner.runtime import handle_request  # noqa: E402
from speckit_pro_runner.execution_control import execution_control, UNKNOWN_GUARDED_ACTIONS  # noqa: E402
from speckit_pro_runner.helpers.registry import HELPERS, MUTATION_HELPERS  # noqa: E402
from speckit_pro_runner.helpers.read_only import (  # noqa: E402
    PLAN_REPAIR_MESSAGE_LIMIT_BYTES,
    PLAN_REPAIR_CONTEXT_LIMIT_BYTES,
    render_plan_repair_context,
)
from test_result import run_counted  # noqa: E402


class CompactAnswerTests(unittest.TestCase):
    def request(self, helper: str, **fields: object):
        entry = (HELPERS | MUTATION_HELPERS)[helper]
        raw = {"schema_version": "1.0", "helper_id": helper, "operation": entry.operation,
               "mode": "read_only", "inputs": {}, "answer_format": "compact", **fields}
        request, error = parse_request(json.dumps(raw))
        self.assertIsNone(error)
        return request

    def test_every_registered_helper_has_a_bounded_root_answer(self):
        for helper in HELPERS | MUTATION_HELPERS:
            with self.subTest(helper=helper):
                request = self.request(helper)
                result = handle_request(request)
                self.assertLessEqual(len(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()) + 1, 16384)
                self.assertTrue(result["next_action"])
                self.assertIn(result["status"], ("ok", "input_error", "missing_prerequisite", "internal_failure", "expected_failure", "subprocess_failure"))

    def test_small_success_preserves_decision_and_removes_duplicate_transport(self):
        body = response("ok", data={"stdout_json": {"action": "stop", "count": 3},
                                   "stdout": {"text": "duplicate", "truncated": False}, "stdin_request": {"ignored": True}})
        with patch("speckit_pro_runner.helpers.registry.dispatch_helper", return_value=body):
            result = handle_request(self.request("count-markers"))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["next_action"], "stop")
        self.assertEqual(result["data"]["stdout_json"], {"action": "stop", "count": 3})
        self.assertNotIn("stdout", result["data"])
        self.assertNotIn("stdin_request", result["data"])
        self.assertIn("stdout", body["data"], "compact projection must not mutate detailed evidence")

    def test_over_cap_fixture_fails_without_leaking_or_repeating_a_mutation(self):
        body = response("ok", data={"evidence": "private fixture text " * 2000})
        with patch("speckit_pro_runner.helpers.registry.dispatch_helper", return_value=body) as dispatch:
            result = handle_request(self.request("count-markers", mode="apply", request_id="r" * 20000))
        dispatch.assert_called_once()
        self.assertEqual(result["status"], "internal_failure")
        self.assertEqual(result["exit_code"], 5)
        self.assertEqual(result["diagnostics"][0]["code"], "compact_answer_overflow")
        self.assertEqual(result["data"]["helper_status"], "ok")
        self.assertIn("without repeating", result["next_action"])
        self.assertNotIn("private fixture text", json.dumps(result))
        self.assertLessEqual(len(json.dumps(result).encode()), 16384)

    def test_failures_keep_their_status_and_remediation(self):
        for status in ("expected_failure", "input_error", "missing_prerequisite", "subprocess_failure", "internal_failure"):
            body = response(status, diagnostics=[{"code": "fixture", "remediation": {"actions": ["Repair the fixture."]}}])
            with self.subTest(status=status), patch("speckit_pro_runner.helpers.registry.dispatch_helper", return_value=body):
                result = handle_request(self.request("count-markers"))
                self.assertEqual(result["status"], status)
                self.assertEqual(result["exit_code"], body["exit_code"])
                self.assertEqual(result["next_action"], "Repair the fixture.")

    def test_detailed_phase_consumer_keeps_full_evidence(self):
        body = response("ok", data={"text": "x" * 20000})
        with patch("speckit_pro_runner.helpers.registry.dispatch_helper", return_value=body):
            result = handle_request(self.request("count-markers", answer_format="detailed"))
        self.assertEqual(result, body)


class CompactExecutionProjectionTests(unittest.TestCase):
    request = CompactAnswerTests.request

    def test_execution_history_projection_keeps_refusals_and_nested_results(self):
        ledger = {"run_id": "existing-run", "dispatches": {"old": {"outcome": "completed"}},
                  "corrective_epochs": [{"dispatches": {"old-fix": {"outcome": "failed"}}}],
                  "excluded_intervals": [{"evidence": "large history " * 2000}]}
        for disposition in ("continue", "defer", "checkpoint_required"):
            data = {"helper_id": "execution-control", "ledger": ledger, "ledger_path": "feature/ledger.json",
                    "disposition": disposition, "reasons": ["fixture-reason"], "dispatch_id": "existing-worker",
                    "authorization_granted": False, "checkpoint_due": True}
            status = "ok" if disposition == "continue" else "expected_failure"
            for wrapped in (False, True):
                body = response(status, data={"result": data} if wrapped else data)
                before = json.dumps(body, sort_keys=True)
                with self.subTest(disposition=disposition, wrapped=wrapped), patch(
                        "speckit_pro_runner.helpers.registry.dispatch_helper", return_value=body):
                    answer = handle_request(self.request("execution-control"))
                    self.assertEqual(answer["status"], status)
                    projected = answer["data"]["result"] if wrapped else answer["data"]
                    self.assertEqual(projected, {**data, "ledger": {"run_id": "existing-run"}})
                    self.assertEqual(json.dumps(body, sort_keys=True), before)

    def test_other_helpers_keep_their_ledger_evidence(self):
        body = response("ok", data={"helper_id": "other-helper", "ledger": {"dispatches": ["evidence"]},
                                   "unknown_dispatch_ids": ["other"], "blocked_by": ["other"]})
        with patch("speckit_pro_runner.helpers.registry.dispatch_helper", return_value=body):
            answer = handle_request(self.request("count-markers"))
        self.assertEqual(answer["data"], body["data"])

    def test_unknown_history_counts_preserve_nested_refusals_without_mutating_details(self):
        for wrapped in (False, True):
            with self.subTest(wrapped=wrapped):
                data = {"helper_id": "execution-control", "ledger": {"run_id": "existing-run"},
                        "ledger_path": "feature/ledger.json", "disposition": "checkpoint_required",
                        "reasons": ["unknown_dispatch_blocks_unit"], "authorization_granted": False,
                        "unknown_dispatch_ids": ["unknown-worker"] * 2000, "blocked_by": ["blocker"] * 1000}
                body = response("expected_failure", data={"result": data} if wrapped else data)
                before = json.dumps(body, sort_keys=True)
                with patch("speckit_pro_runner.helpers.registry.dispatch_helper", return_value=body):
                    answer = handle_request(self.request("execution-control"))
                self.assertEqual(answer["status"], "expected_failure")
                projected = answer["data"]["result"] if wrapped else answer["data"]
                self.assertEqual(projected, {key: value for key, value in data.items()
                                            if key not in {"unknown_dispatch_ids", "blocked_by"}}
                                 | {"unknown_dispatch_count": 2000, "blocked_by_count": 1000,
                                    "unknown_dispatch_ids": projected["unknown_dispatch_ids"],
                                    "blocked_by": projected["blocked_by"]})
                self.assertTrue(projected["unknown_dispatch_ids"])
                self.assertTrue(projected["blocked_by"])
                self.assertLess(len(projected["unknown_dispatch_ids"]), 2000)
                self.assertLess(len(projected["blocked_by"]), 1000)
                self.assertEqual(set(projected["unknown_dispatch_ids"]), {"unknown-worker"})
                self.assertEqual(set(projected["blocked_by"]), {"blocker"})
                self.assertEqual(json.dumps(body, sort_keys=True), before)


@dataclass(frozen=True)
class MirrorFailureCase:
    action: str
    count: int
    state: str


class ExecutionFixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / ".specify").mkdir()
        (self.root / "feature").mkdir()
        (self.root / "feature/workflow.md").write_text("# Workflow\n")
        self.binding = {"workflow_file": "feature/workflow.md"}
        started = execution_control(self.root, {**self.binding, "action": "start"}, "apply")
        self.binding["expected_run_id"] = started["ledger"]["run_id"]
        self.ledger_path = self.root / started["ledger_path"]
        reserved = execution_control(self.root, {**self.binding, "action": "reserve",
                                               "dispatch_id": "seed", "kind": "implementation"}, "apply")
        self.seed = reserved["ledger"]


class MirrorFailureFixture(ExecutionFixture):
    def invoke(self, payload, case, mode="apply", answer_format="compact"):
        action, count, state = case.action, case.count, case.state
        ledger = {**self.seed, "dispatches": {f"implementation-{i}": dict(self.seed["dispatches"]["seed"])
                                             for i in range(count)}}
        self.ledger_path.write_text(json.dumps(ledger))
        # A public read validates the fixture rather than trusting a hand-built ledger.
        execution_control(self.root, {**self.binding, "action": "status"}, "read_only")
        state_path = self.root / "feature/autopilot-state.json"
        state_path.write_text(state)
        before = self.ledger_path.read_bytes()
        inputs = {**self.binding, "action": action}
        if action == "reserve":
            inputs.update(dispatch_id="next-worker", kind="implementation")
        raw = {"schema_version": "1.0", "helper_id": "execution-control", "operation": "execution-control",
               "request_id": "applied-result", "mode": mode, "answer_format": answer_format, "inputs": inputs}
        done = subprocess.run([sys.executable, str(REPO / payload / "scripts/run-speckit-pro.py")],
                              input=json.dumps(raw), capture_output=True, text=True, cwd=self.root,
                              check=False, timeout=30)
        answer = json.loads(done.stdout)
        # Check durable effects even when the envelope loses the answer.
        persisted = execution_control(self.root, {**self.binding, "action": "status"}, "read_only")["ledger"]
        self.assertEqual(len(persisted["dispatches"]), count + (action == "reserve" and mode == "apply"))
        if mode != "apply":
            self.assertEqual(self.ledger_path.read_bytes(), before)
        self.assertEqual(state_path.read_text(), state)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(answer["status"], "ok", answer)
        self.assertEqual(answer["data"]["ledger"]["run_id"], self.binding["expected_run_id"])
        self.assertEqual(answer["data"]["disposition"], "continue")
        self.assertFalse(answer["data"]["authorization_granted"])
        if action == "reserve":
            self.assertEqual(answer["data"]["dispatch_id"], "next-worker")
            self.assertEqual(persisted["dispatches"].get("next-worker", {}).get("outcome"),
                             "reserved" if mode == "apply" else None)
        if answer_format == "compact":
            self.assertLessEqual(len(done.stdout.encode()) + len(done.stderr.encode()), 16384)
            self.assertEqual(answer["data"]["ledger"], {"run_id": self.binding["expected_run_id"]})
        else:
            self.assertEqual(answer["data"]["ledger"], persisted)
        if mode == "apply":
            self.assertEqual([diag["code"] for diag in answer["diagnostics"]], ["state_mirror_not_refreshed"])
            if answer_format == "compact":
                self.assertIn("action=status mode=apply", answer["next_action"])
        else:
            self.assertEqual(answer["diagnostics"], [])


class CompactExecutionTests(MirrorFailureFixture):
    def check_mirror_failure_matrix(self, action):
        payloads = ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro")
        for payload, count, state in itertools.product(payloads, (109, 110, 300), ("[]", "{not json")):
            with self.subTest(action=action, payload=payload, count=count, state=state):
                self.invoke(payload, MirrorFailureCase(action, count, state))

    def test_compact_status_retains_applied_result_when_the_state_mirror_fails(self):
        self.check_mirror_failure_matrix("status")

    def test_compact_reserve_retains_applied_result_when_the_state_mirror_fails(self):
        self.check_mirror_failure_matrix("reserve")

    def test_detailed_applied_results_and_non_apply_mirror_controls(self):
        for action in ("status", "reserve"):
            for state in ("[]", "{not json"):
                for mode, answer_format in (("apply", "detailed"), ("read_only", "compact"), ("dry_run", "compact")):
                    if action == "reserve" and mode == "read_only":
                        continue  # Mutating actions intentionally reject read_only mode.
                    with self.subTest(action=action, state=state, mode=mode, answer_format=answer_format):
                        self.invoke("speckit-pro", MirrorFailureCase(action, 110, state), mode, answer_format)


class UnknownDispatchFixture(ExecutionFixture):
    PAYLOADS = ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro")

    def prepare_unknowns(self, count=700, padding="implementation-worker-"):
        (self.root / "feature/spec.md").write_text("# Spec\n")
        self.ledger_path.write_text(json.dumps(self.seed))
        completed = execution_control(self.root, {**self.binding, "action": "complete",
                                                "dispatch_id": "seed", "outcome": "unknown"}, "apply")
        record = completed["ledger"]["dispatches"]["seed"]
        ledger = {**completed["ledger"], "dispatches": {
            f"{padding}{i:04d}": {**record, "tdd_units": [f"unit-{i}"]} for i in range(count)}}
        self.ledger_path.write_text(json.dumps(ledger))
        validated = execution_control(self.root, {**self.binding, "action": "status"}, "read_only")
        self.assertEqual(len(validated["unknown_dispatch_ids"]), count)
        return ledger

    def call(self, payload="speckit-pro", *, answer_format="compact", **inputs):
        mode = inputs.pop("mode", "apply")
        raw = {"schema_version": "1.0", "helper_id": "execution-control", "operation": "execution-control",
               "request_id": "unknown-history", "mode": mode, "answer_format": answer_format,
               "inputs": {**self.binding, "action": "status", **inputs}}
        done = subprocess.run([sys.executable, str(REPO / payload / "scripts/run-speckit-pro.py")],
                              input=json.dumps(raw), capture_output=True, text=True, cwd=self.root,
                              check=False, timeout=30)
        answer = json.loads(done.stdout)
        self.assertEqual(done.returncode, answer["exit_code"], done.stderr)
        if answer_format == "compact":
            self.assertLessEqual(len(done.stdout.encode()) + len(done.stderr.encode()), 16384)
        return answer

    def assert_compact_result(self, answer, count, status="ok"):
        self.assertEqual(answer["status"], status, answer)
        data = answer["data"]
        self.assertEqual(data["ledger"], {"run_id": self.binding["expected_run_id"]})
        self.assertEqual(self.root / data["ledger_path"], self.ledger_path)
        self.assertEqual(data["unknown_dispatch_count"], count)
        ids = data["unknown_dispatch_ids"]
        self.assertTrue(ids)
        self.assertLessEqual(len(ids), count)
        persisted_ids = sorted(json.loads(self.ledger_path.read_text())["dispatches"])
        self.assertEqual(ids, persisted_ids[:len(ids)])
        self.assertFalse(data["authorization_granted"])
        return data


class CompactUnknownMirrorTests(UnknownDispatchFixture):
    def test_unknown_status_apply_keeps_mirror_warning_on_all_launchers(self):
        for payload, state in itertools.product(self.PAYLOADS, ("[]", "{not json")):
            with self.subTest(payload=payload, state=state):
                self.prepare_unknowns()
                path = self.root / "feature/autopilot-state.json"
                path.write_text(state)
                before = self.ledger_path.read_bytes()
                answer = self.call(payload)
                self.assertNotEqual(self.ledger_path.read_bytes(), before)
                self.assertEqual(path.read_text(), state)
                self.assert_compact_result(answer, 700)
                self.assertEqual(answer["data"]["disposition"], "continue")
                self.assertEqual([d["code"] for d in answer["diagnostics"]], ["state_mirror_not_refreshed"])
                self.assertIn("action=status mode=apply", answer["next_action"])

    def test_unknown_scoped_reserve_keeps_durable_dispatch_on_all_launchers(self):
        for payload, state in itertools.product(self.PAYLOADS, ("[]", "{not json")):
            with self.subTest(payload=payload, state=state):
                self.prepare_unknowns()
                (self.root / "feature/autopilot-state.json").write_text(state)
                answer = self.call(payload, action="reserve", dispatch_id="next-worker",
                                   kind="implementation", tdd_units=["next-unit"])
                persisted = json.loads(self.ledger_path.read_text())
                self.assertEqual(len(persisted["dispatches"]), 701)
                self.assertEqual(persisted["dispatches"]["next-worker"]["outcome"], "reserved")
                data = self.assert_compact_result(answer, 700)
                self.assertEqual(data["dispatch_id"], "next-worker")
                self.assertEqual(data["disposition"], "continue")
                self.assertEqual([d["code"] for d in answer["diagnostics"]], ["state_mirror_not_refreshed"])

    def test_unknown_status_without_state_keeps_applied_result_on_all_launchers(self):
        for payload in self.PAYLOADS:
            with self.subTest(payload=payload):
                self.prepare_unknowns(800)
                before = self.ledger_path.read_bytes()
                answer = self.call(payload)
                self.assertNotEqual(self.ledger_path.read_bytes(), before)
                self.assertFalse((self.root / "feature/autopilot-state.json").exists())
                self.assert_compact_result(answer, 800)
                self.assertEqual(answer["diagnostics"], [])


class CompactUnknownGuardTests(UnknownDispatchFixture):
    def test_unknown_guarded_actions_keep_refusal_and_exact_blocker_count(self):
        for payload, action in itertools.product(self.PAYLOADS, sorted(UNKNOWN_GUARDED_ACTIONS)):
            with self.subTest(payload=payload, action=action):
                self.prepare_unknowns()
                answer = self.call(payload, action=action, dispatch_id="next-worker", kind="implementation",
                                   spec_file="feature/spec.md")
                self.assertEqual(len(json.loads(self.ledger_path.read_text())["dispatches"]), 700)
                data = self.assert_compact_result(answer, 700, "expected_failure")
                self.assertEqual(data["disposition"], "checkpoint_required")
                self.assertEqual(data["reasons"], ["unknown_dispatch_blocks_unit"])
                self.assertEqual(data["blocked_by_count"], 700)
                self.assertTrue(data["blocked_by"])
                self.assertLess(len(data["blocked_by"]), 700)
                self.assertTrue(set(data["blocked_by"]).issubset(data["unknown_dispatch_ids"]))
                self.assertNotIn("dispatch_id", data)

    def test_unknown_overlapping_reserve_counts_only_actual_blockers(self):
        self.prepare_unknowns()
        answer = self.call(action="reserve", dispatch_id="next-worker", kind="implementation", tdd_units=["unit-0"])
        data = self.assert_compact_result(answer, 700, "expected_failure")
        self.assertEqual(data["blocked_by_count"], 1)
        self.assertEqual(data["blocked_by"], ["implementation-worker-0000"])
        self.assertEqual(len(json.loads(self.ledger_path.read_text())["dispatches"]), 700)


class CompactUnknownControlTests(UnknownDispatchFixture):
    def test_unknown_detailed_apply_and_compact_non_apply_controls(self):
        for payload, mode in itertools.product(self.PAYLOADS, ("read_only", "dry_run")):
            with self.subTest(payload=payload, mode=mode):
                self.prepare_unknowns()
                (self.root / "feature/autopilot-state.json").write_text("[]")
                before = self.ledger_path.read_bytes()
                compact = self.call(payload, mode=mode)
                self.assertEqual(self.ledger_path.read_bytes(), before)
                self.assertEqual(compact["diagnostics"], [])
                self.assert_compact_result(compact, 700)
                detailed = self.call(payload, answer_format="detailed")
                self.assertEqual(detailed["status"], "ok")
                self.assertEqual(len(detailed["data"]["unknown_dispatch_ids"]), 700)
                self.assertEqual(detailed["data"]["ledger"], json.loads(self.ledger_path.read_text()))
                self.assertNotIn("unknown_dispatch_count", detailed["data"])
                self.assertEqual([d["code"] for d in detailed["diagnostics"]], ["state_mirror_not_refreshed"])

    def test_unknown_compact_size_is_independent_of_id_length(self):
        for padding in ("u", "implementation-worker-", "worker-" + "界\\\"" * 70):
            with self.subTest(padding=padding[:25]):
                self.prepare_unknowns(padding=padding)
                self.assert_compact_result(self.call(), 700)



    def test_independent_units_can_accumulate_unknowns_through_public_actions(self):
        # No fabricated history: these unknowns come from normal reserve/complete calls.
        self.ledger_path.write_text(json.dumps(self.seed))
        self.call(action="complete", dispatch_id="seed", outcome="completed", answer_format="detailed")
        for unit in ("alpha", "beta"):
            reserved = self.call(action="reserve", dispatch_id=unit, kind="implementation",
                                 tdd_units=[unit], answer_format="detailed")
            self.assertEqual(reserved["status"], "ok")
            completed = self.call(action="complete", dispatch_id=unit, outcome="unknown", answer_format="detailed")
            self.assertEqual(completed["status"], "ok")
        answer = self.call(action="reserve", dispatch_id="gamma", kind="implementation", tdd_units=["gamma"])
        data = self.assert_compact_result(answer, 2)
        self.assertEqual(data["dispatch_id"], "gamma")
        self.assertEqual(json.loads(self.ledger_path.read_text())["dispatches"]["gamma"]["outcome"], "reserved")


class CompactCheckpointTests(unittest.TestCase):
    setUp = ExecutionFixture.setUp
    call = UnknownDispatchFixture.call

    def test_completed_history_keeps_checkpoint_result_and_warning_on_all_launchers(self):
        execution_control(self.root, {**self.binding, "action": "complete",
                                     "dispatch_id": "seed", "outcome": "completed"}, "apply")
        completed_ids = ["seed"]
        for index in range(8):
            dispatch_id = "\U0001f680" * 236 + f"{index:04d}"
            execution_control(self.root, {**self.binding, "action": "reserve", "dispatch_id": dispatch_id,
                                         "kind": "implementation"}, "apply")
            execution_control(self.root, {**self.binding, "action": "complete", "dispatch_id": dispatch_id,
                                         "outcome": "completed"}, "apply")
            completed_ids.append(dispatch_id)
        for payload, state in itertools.product(UnknownDispatchFixture.PAYLOADS, (None, "[]")):
            with self.subTest(payload=payload, state=state):
                state_path = self.root / "feature/autopilot-state.json"
                state_path.unlink(missing_ok=True)
                if state is not None:
                    state_path.write_text(state)
                before = json.loads(self.ledger_path.read_text())["checkpoint_at"]
                answer = self.call(payload, action="checkpoint")
                persisted = json.loads(self.ledger_path.read_text())
                self.assertGreater(persisted["checkpoint_at"], before)
                self.assertEqual(answer["status"], "ok", answer)
                data = answer["data"]
                self.assertEqual(data["ledger"], {"run_id": self.binding["expected_run_id"]})
                self.assertEqual(data["disposition"], "continue")
                self.assertEqual(data["completed_dispatch_count"], 9)
                ids = data["completed_dispatch_ids"]
                self.assertTrue(ids)
                self.assertLess(len(ids), 9)
                self.assertEqual(ids, completed_ids[:len(ids)])
                self.assertLessEqual(len(json.dumps(ids, separators=(",", ":")).encode()),
                                     COMPACT_EXECUTION_HISTORY_LIMIT_BYTES)
                self.assertEqual([d["code"] for d in answer["diagnostics"]],
                                 [] if state is None else ["state_mirror_not_refreshed"])
                detailed = self.call(payload, action="checkpoint", answer_format="detailed")
                self.assertEqual(detailed["data"]["completed_dispatch_ids"], completed_ids)
                self.assertEqual(list(detailed["data"]["ledger"]["dispatches"]), completed_ids)
                self.assertNotIn("completed_dispatch_count", detailed["data"])


class CompactRecoveryIdsTests(unittest.TestCase):
    setUp = ExecutionFixture.setUp
    PAYLOADS = UnknownDispatchFixture.PAYLOADS
    prepare_unknowns = UnknownDispatchFixture.prepare_unknowns
    call = UnknownDispatchFixture.call

    def test_compact_only_root_receives_ids_to_reconcile_on_all_launchers(self):
        for payload in self.PAYLOADS:
            with self.subTest(payload=payload):
                self.ledger_path.write_text(json.dumps(self.seed))
                self.call(payload, action="complete", dispatch_id="seed", outcome="completed")
                reserved = self.call(payload, action="reserve", dispatch_id="worker-a",
                                     kind="implementation", tdd_units=["unit-a"])
                self.assertEqual(reserved["data"]["dispatch_id"], "worker-a")
                self.call(payload, action="complete", dispatch_id="worker-a", outcome="unknown")
                status = self.call(payload)
                blocked = self.call(payload, action="reserve", dispatch_id="worker-b",
                                    kind="implementation", tdd_units=["unit-a"])
                self.assertEqual(status["data"]["unknown_dispatch_ids"], ["worker-a"])
                self.assertEqual(blocked["data"]["blocked_by"], ["worker-a"])
                self.assertEqual(blocked["data"]["reasons"], ["unknown_dispatch_blocks_unit"])
                self.assertNotIn("worker-b", json.loads(self.ledger_path.read_text())["dispatches"])

    def test_compact_batches_reveal_remaining_exact_ids_after_resolution(self):
        # 240 astral characters is the existing admission boundary and expands on the wire.
        ledger = self.prepare_unknowns(3, padding="\U0001f680" * 236)
        remaining = sorted(ledger["dispatches"])
        for index in range(3):
            answer = self.call()
            self.assertEqual(answer["data"]["unknown_dispatch_count"], 3 - index)
            self.assertEqual(answer["data"]["unknown_dispatch_ids"], remaining[:1])
            dispatch_id = remaining.pop(0)
            settled = self.call(action="complete", dispatch_id=dispatch_id, outcome="failed", native_observation={
                "native_event_id": f"recovered-{index}", "run_id": self.binding["expected_run_id"],
                "dispatch_id": dispatch_id, "action": "dispatch_result", "outcome": "failed"})
            self.assertEqual(settled["status"], "ok")
        self.assertNotIn("unknown_dispatch_ids", self.call()["data"])

    def test_invalid_persisted_dispatch_ids_fail_before_apply_writes(self):
        for payload, invalid_id in itertools.product(self.PAYLOADS, ("", " " * 10, "x" * 241)):
            with self.subTest(payload=payload, invalid_id=invalid_id[:20]):
                ledger = self.prepare_unknowns(1)
                record = next(iter(ledger["dispatches"].values()))
                ledger["dispatches"] = {invalid_id: record}
                self.ledger_path.write_text(json.dumps(ledger))
                before = self.ledger_path.read_bytes()
                answer = self.call(payload)
                self.assertEqual(answer["status"], "input_error")
                self.assertEqual(self.ledger_path.read_bytes(), before)


class CompactLauncherTests(unittest.TestCase):
    def test_source_and_both_host_launchers_return_compact_decisions(self):
        raw = {"schema_version": "1.0", "helper_id": "count-markers", "operation": "count-markers",
               "mode": "read_only", "answer_format": "compact",
               "inputs": {"type": "all", "feature_dir": "tests/speckit-pro/unit/fixtures/read-only-helpers/read-only-helper-feature"}}
        decisions = []
        for relative in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            command = [sys.executable, str(REPO / relative / "scripts/run-speckit-pro.py")]
            done = subprocess.run(command, input=json.dumps(raw), capture_output=True, text=True,
                                  cwd=REPO, check=False, timeout=30)
            with self.subTest(payload=relative):
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertLessEqual(len(done.stdout.encode()) + len(done.stderr.encode()), 16384)
                answer = json.loads(done.stdout)
                self.assertEqual(answer["status"], "ok")
                self.assertTrue(answer["next_action"])
                decisions.append(answer["data"]["stdout_json"])
        self.assertEqual(len(decisions), 3)
        self.assertEqual(decisions[0], decisions[1])
        self.assertEqual(decisions[0], decisions[2])

    def test_full_sized_tasks_bindings_survive_compact_publish_and_consumption(self):
        text = "# Tasks\n" + "\x00" * (32768 - len("# Tasks\n"))
        for payload in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(binding_payload=payload), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                (root / ".specify").mkdir()
                feature = root / "feature"
                feature.mkdir()
                snapshot = root / "snapshot"
                snapshot.mkdir(mode=0o700)
                (snapshot / "tasks.md").write_text(text, encoding="utf-8")
                identity = feature.stat()
                raw = {"schema_version": "1.0", "helper_id": "publish-tasks-output",
                       "operation": "publish-tasks-output", "mode": "apply", "answer_format": "compact",
                       "inputs": {"feature_dir": "feature", "snapshot_dir": str(snapshot),
                                  "feature_identity": {"device": identity.st_dev, "inode": identity.st_ino}}}
                command = [sys.executable, str(REPO / payload / "scripts/run-speckit-pro.py")]
                published = subprocess.run(command, input=json.dumps(raw), capture_output=True, text=True,
                                           cwd=root, check=False, timeout=30)
                answer = json.loads(published.stdout)
                self.assertEqual(answer["status"], "ok", answer)
                binding = answer["data"]["tasks_binding"]
                self.assertEqual(binding["text"], text)
                self.assertLessEqual(len(published.stdout.encode()) + len(published.stderr.encode()), 212992)
                raw.update(helper_id="read-tasks-output", operation="read-tasks-output", mode="read_only",
                           inputs={"tasks_binding": binding, "live_path": "feature/tasks.md"})
                consumed = subprocess.run(command, input=json.dumps(raw), capture_output=True, text=True,
                                          cwd=root, check=False, timeout=30)
                verified = json.loads(consumed.stdout)
                self.assertEqual(verified["status"], "ok", verified)
                self.assertEqual(verified["data"]["text"], text)
                self.assertTrue(verified["data"]["after_hooks_ready"])
                self.assertLessEqual(len(consumed.stdout.encode()) + len(consumed.stderr.encode()), 212992)


class CompactPlanRepairBoundaryTests(unittest.TestCase):
    def test_maximum_escaped_plan_repair_survives_capture_on_both_hosts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / ".specify").mkdir()
            (root / "attempts.json").write_text('{"attempts": [{}]}', encoding="utf-8")
            contexts = {f"evidence-{index}": f"context-{index}.md" for index in range(3)}
            inputs = {"context_paths": contexts,
                      "g3_attempts_path": "attempts.json", "g3_attempt_index": 0,
                      "executor_task": "Repair.", "attempt_number": 1,
                      "disputed_wording": "wording", "provenance_class": "assistant-inference",
                      "prior_repair_result": "initial failure"}
            for character in ("\x00", '"', "\\"):
                inputs["executor_task"] = "Repair." + character * (32768 - len("Repair."))
                for name in contexts.values():
                    (root / name).write_text("x", encoding="utf-8")
                baseline = json.loads(render_plan_repair_context(inputs, root)["stdout"])
                padding = PLAN_REPAIR_MESSAGE_LIMIT_BYTES - baseline["message_bytes"]
                for name in contexts.values():
                    count = min(padding, PLAN_REPAIR_CONTEXT_LIMIT_BYTES - 1)
                    (root / name).write_text("x" + character * count, encoding="utf-8")
                    padding -= count
                self.assertEqual(padding, 0)
                rendered = render_plan_repair_context(inputs, root)
                self.assertEqual(rendered["exit_code"], 0)
                expected = json.loads(rendered["stdout"])
                self.assertEqual(expected["message_bytes"], PLAN_REPAIR_MESSAGE_LIMIT_BYTES)
                self.assertEqual(expected["message_sha256"], hashlib.sha256(
                    expected["executor_message"].encode("utf-8")).hexdigest())
                raw = {"schema_version": "1.0", "helper_id": "render-plan-repair-context",
                       "operation": "render-plan-repair-context", "mode": "read_only", "inputs": inputs}
                for payload in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
                    command = [sys.executable, str(REPO / payload / "scripts/run-speckit-pro.py")]
                    for answer_format in ("compact", "detailed"):
                        with self.subTest(character=repr(character), payload=payload, answer_format=answer_format):
                            raw["answer_format"] = answer_format
                            done = subprocess.run(command, input=json.dumps(raw), capture_output=True, text=True,
                                                  cwd=root, check=False, timeout=30)
                            answer = json.loads(done.stdout)
                            self.assertEqual(done.returncode, 0, done.stderr)
                            self.assertEqual(answer["status"], "ok")
                            self.assertEqual(answer["data"]["stdout_json"], expected)
                            if answer_format == "detailed":
                                self.assertFalse(answer["data"]["stdout"]["truncated"])
                inputs["executor_task"] += "x"
                rejected = render_plan_repair_context(inputs, root)
                self.assertEqual(rejected["exit_code"], 2)
                self.assertEqual(json.loads(rejected["stdout"])["error"],
                                 "rendered Plan-repair message is oversized")

class CompactPlanRepairTests(unittest.TestCase):
    def test_real_sized_plan_repair_preserves_complete_executor_message(self):
        fixtures = REPO / "tests/speckit-pro/unit/fixtures/read-only-helpers"
        raw = json.loads((fixtures / "requests/render-plan-repair-context.json").read_text())
        raw["inputs"]["context_paths"]["source-evidence"] = str(fixtures.relative_to(REPO) / "read-only-helper-feature/plan.md")
        for payload in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            command = [sys.executable, str(REPO / payload / "scripts/run-speckit-pro.py")]
            with self.subTest(repair_payload=payload):
                raw["answer_format"] = "detailed"
                detailed = subprocess.run(command, input=json.dumps(raw), capture_output=True, text=True,
                                          cwd=REPO, check=False, timeout=30)
                evidence = json.loads(detailed.stdout)
                self.assertEqual(evidence["status"], "ok", evidence)
                self.assertGreater(evidence["data"]["stdout_json"]["message_bytes"], 23000)
                raw["answer_format"] = "compact"
                compact = subprocess.run(command, input=json.dumps(raw), capture_output=True, text=True,
                                         cwd=REPO, check=False, timeout=30)
                answer = json.loads(compact.stdout)
                self.assertEqual(answer["status"], "ok", answer)
                self.assertEqual(answer["data"]["stdout_json"], evidence["data"]["stdout_json"])
                self.assertLessEqual(len(compact.stdout.encode()) + len(compact.stderr.encode()), 1196032)
                self.assertTrue(answer["next_action"])


class CompactRequestTests(unittest.TestCase):
    def test_answer_format_rejects_unsupported_values(self):
        for value in (None, [], {}, True, "unbounded"):
            raw = {"schema_version": "1.0", "helper_id": "runner", "operation": "runtime-info",
                   "mode": "read_only", "inputs": {}, "answer_format": value}
            with self.subTest(value=value):
                request, error = parse_request(json.dumps(raw))
                self.assertIsNone(request)
                self.assertEqual(error["status"], "input_error")


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]), label="test-compact-answers"))
