#!/usr/bin/env python3
"""Deterministic durable budget and independently observed verification contracts."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "speckit-pro"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from test_result import run_counted
from speckit_pro_runner.execution_control import (durable_json, execution_control, ignore_owned_directory, is_runner_byproduct,
                                                  record_failing_checks)
from speckit_pro_runner.failing_checks import fingerprint as failing_check_fingerprint
from speckit_pro_runner.helpers.read_only import json_schema_failures, validate_task_execution
from speckit_pro_runner.task_execution import fingerprints
from speckit_pro_runner.verification_records import digest, execute_verification, project_command, run_snapshot_command, tree_bytes, validate_execution_record


class _ExecutionControlFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "feature").mkdir()
        (self.root / "feature/workflow.md").write_text("# Workflow\n")
        (self.root / "feature/spec.md").write_text("- FR-001: preserve data\n- FR-002: no secrets\n")
        self.now = 1000.0
        self.run_id = None

    def invoke(self, action, mode="apply", **inputs):
        binding = {"expected_run_id": self.run_id} if self.run_id else {}
        with patch("speckit_pro_runner.execution_control.time.time", return_value=self.now):
            result = execution_control(self.root, {"workflow_file": "feature/workflow.md", "action": action, **binding, **inputs}, mode)
        if mode == "apply":
            self.run_id = result["ledger"]["run_id"]
        return result

    def assert_schema_valid(self, ledger):
        schema = json.loads(SCHEMA_PATH.read_text())
        self.assertEqual(json_schema_failures(ledger, schema, schema, "ledger"), [])

    def verify(self, stdout, exit_code=1, completed=True, command_id="UNIT_TEST", argv=("python3", "-m", "unittest")):
        """Run one verification dispatch whose output the runner fingerprints into the ledger."""
        self.verifications = getattr(self, "verifications", 0) + 1
        dispatch_id = f"verify-{self.verifications}"
        self.now += 10
        self.invoke("reserve", dispatch_id=dispatch_id, kind="verification")
        self.invoke("begin-verification", dispatch_id=dispatch_id)
        evidence = failing_check_fingerprint(command_id, list(argv), exit_code, completed, stdout.encode(), b"")
        with patch("speckit_pro_runner.execution_control.time.time", return_value=self.now):
            record_failing_checks(self.root, {"workflow_file": "feature/workflow.md", "expected_run_id": self.run_id,
                                              "dispatch_id": dispatch_id}, evidence)
        self.invoke("complete", dispatch_id=dispatch_id, outcome="failed" if exit_code else "completed")
        return dispatch_id


def _assert_relocation_event_reuse_rejected(test, path, common):
    event_id, run_id = "workflow-move-1", test.run_id
    requests = (
        {"action": "complete", "dispatch_id": "uncertain", "outcome": "completed",
         "native_observation": {"native_event_id": event_id, "run_id": run_id, "dispatch_id": "uncertain",
                                "action": "dispatch_result", "outcome": "completed"}},
        {"action": "pause", "native_observation": {"native_event_id": event_id, "run_id": run_id,
                                                    "kind": "human_uat", "action": "wait_started"}},
    )
    before = path.read_bytes()
    for request in requests:
        with test.subTest(action=request["action"]):
            path.write_bytes(before)
            with test.assertRaises(ValueError):
                execution_control(test.root, {**common, **request}, "apply")
            test.assertEqual(path.read_bytes(), before)
    path.write_bytes(before)


class GreenfieldInvariantBindingTests(_ExecutionControlFixture, unittest.TestCase):
    def test_greenfield_run_binds_first_spec_once_without_resetting_repair_budget(self):
        spec = self.root / "feature/spec.md"
        spec.unlink()
        started = self.invoke("start")
        self.assertEqual(started["ledger"]["approved_invariants"], [])
        self.invoke("reserve", dispatch_id="tasks-prefix", kind="corrective",
                    failure_invariant="not-yet-in-spec")
        self.invoke("complete", dispatch_id="tasks-prefix", outcome="completed")
        before = self.invoke("status", mode="read_only")["ledger"]
        spec.write_text("- FR-001: preserve data\n- FR-002: no secrets\n")

        bound = self.invoke("bind-invariants", spec_file="feature/spec.md")["ledger"]
        for key in ("run_id", "started_at", "slice_started_at", "checkpoint_at",
                    "corrective_cycles", "reservations", "dispatches"):
            self.assertEqual(bound[key], before[key], key)
        self.assertEqual(bound["approved_invariants"], ["FR-001", "FR-002"])
        self.assertEqual(next(iter(bound["reservations"].values()))["family"], "unresolved")
        second = self.invoke("reserve", dispatch_id="analyze-repair", kind="corrective",
                             failure_invariant="FR-002")
        self.assertEqual(second["disposition"], "continue")
        self.assertEqual(second["ledger"]["corrective_cycles"], 2)
        third = self.invoke("reserve", dispatch_id="third-repair", kind="corrective", failure_invariant="FR-001")
        self.assertEqual(third["disposition"], "defer")
        self.assertNotIn("third-repair", third["ledger"]["dispatches"])

    def test_late_binding_rejects_missing_empty_and_repeated_specs_without_mutation(self):
        spec = self.root / "feature/spec.md"
        spec.unlink()
        started = self.invoke("start")
        path = self.root / started["ledger_path"]
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            self.invoke("bind-invariants")
        self.assertEqual(path.read_bytes(), before)
        spec.write_text("# No approved requirements yet\n")
        with self.assertRaises(ValueError):
            self.invoke("bind-invariants", spec_file="feature/spec.md")
        self.assertEqual(path.read_bytes(), before)
        spec.write_text("- FR-001: preserve data\n")
        self.invoke("bind-invariants", spec_file="feature/spec.md")
        bound = path.read_bytes()
        spec.write_text("- FR-001: preserve data\n- FR-002: added later\n")
        with self.assertRaises(ValueError):
            self.invoke("bind-invariants", spec_file="feature/spec.md")
        self.assertEqual(path.read_bytes(), bound)
        malformed = json.loads(bound)
        malformed["invariant_binding"] = None
        path.write_text(json.dumps(malformed))
        with self.assertRaises(ValueError):
            self.invoke("status", mode="read_only")

class ExecutionControlTests(_ExecutionControlFixture, unittest.TestCase):
    def test_start_is_idempotent_and_phase_changes_do_not_reset_clock(self):
        first = self.invoke("start")
        self.now += 2800
        second = self.invoke("start")
        self.assertEqual(first["ledger"]["run_id"], second["ledger"]["run_id"])
        self.assertTrue(second["checkpoint_due"])
        self.assertEqual(second["elapsed_seconds"], 2800)

    def test_one_family_and_two_global_reservations_across_restart(self):
        self.invoke("start")
        first = self.invoke("reserve", dispatch_id="fix-a", kind="corrective", failure_invariant="FR-001")
        self.invoke("complete", dispatch_id="fix-a", outcome="failed")
        denied = self.invoke("reserve", dispatch_id="renamed-error", kind="corrective", failure_invariant="FR-001")
        self.assertEqual(denied["disposition"], "defer")
        self.assertNotIn("renamed-error", denied["ledger"]["dispatches"])
        second = self.invoke("reserve", dispatch_id="fix-b", kind="corrective", failure_invariant="FR-002")
        self.assertEqual(second["disposition"], "continue")
        third = self.invoke("reserve", dispatch_id="fix-c", kind="corrective", failure_invariant="new-error")
        self.assertEqual(third["disposition"], "defer")
        self.assertNotIn("fix-c", third["ledger"]["dispatches"])
        self.assertEqual(first["ledger"]["corrective_cycles"], 1)

    def test_unknown_families_share_budget_and_nested_hardener_reuses_reservation(self):
        self.invoke("start")
        first = self.invoke("reserve", dispatch_id="repair", kind="corrective", failure_invariant="whatever")
        reservation = first["reservation_id"]
        nested = self.invoke("reserve", dispatch_id="nested", kind="corrective", reservation_id=reservation)
        self.assertEqual(nested["ledger"]["corrective_cycles"], 1)
        denied = self.invoke("reserve", dispatch_id="other", kind="corrective", failure_invariant="different words")
        self.assertEqual(denied["disposition"], "defer")
        self.assertNotIn("other", denied["ledger"]["dispatches"])

    def test_failed_nested_correction_cannot_launder_another_cycle(self):
        self.invoke("start")
        first = self.invoke("reserve", dispatch_id="owner", kind="corrective", failure_invariant="FR-001")
        reservation = first["reservation_id"]
        self.invoke("reserve", dispatch_id="nested-one", kind="corrective", reservation_id=reservation)
        self.invoke("complete", dispatch_id="nested-one", outcome="failed")
        refused = self.invoke("reserve", dispatch_id="nested-two", kind="corrective", reservation_id=reservation)
        self.assertEqual(refused["disposition"], "defer")
        self.assertNotIn("nested-two", refused["ledger"]["dispatches"])

    def test_missing_result_has_one_inspection_and_no_relaunch(self):
        self.invoke("start")
        self.invoke("reserve", dispatch_id="task", kind="implementation")
        first = self.invoke("reconcile", dispatch_id="task")
        self.assertTrue(first["reconciliation_allowed"])
        second = self.invoke("reconcile", dispatch_id="task")
        self.assertFalse(second["reconciliation_allowed"])
        self.assertEqual(self.invoke("reserve", dispatch_id="task", kind="implementation")["disposition"], "checkpoint_required")
        status = self.invoke("status", mode="read_only")
        self.assertEqual((status["disposition"], status["unknown_dispatch_ids"]), ("continue", ["task"]))
        self.assertEqual(self.invoke("reserve", dispatch_id="renamed-task", kind="implementation")["disposition"], "checkpoint_required")

    def test_unknown_effects_block_already_reserved_verification_until_native_resolution(self):
        start = self.invoke("start")
        self.invoke("reserve", dispatch_id="worker", kind="implementation")
        self.invoke("reserve", dispatch_id="verify", kind="verification")
        self.invoke("complete", dispatch_id="worker", outcome="unknown")
        self.assertEqual(self.invoke("begin-verification", dispatch_id="verify")["disposition"], "checkpoint_required")
        self.assertEqual(self.invoke("complete", dispatch_id="worker", outcome="completed")["disposition"], "checkpoint_required")
        resolved = self.invoke("complete", dispatch_id="worker", outcome="completed", native_observation={
            "native_event_id": "recovered-real-result", "run_id": start["ledger"]["run_id"],
            "dispatch_id": "worker", "action": "dispatch_result", "outcome": "completed"})
        self.assertEqual(resolved["disposition"], "continue")
        self.assertEqual(self.invoke("begin-verification", dispatch_id="verify")["disposition"], "continue")

    def test_expected_tdd_red_is_not_repair_but_verification_red_is_failure(self):
        self.invoke("start")
        self.invoke("reserve", dispatch_id="tdd", kind="implementation")
        result = self.invoke("complete", dispatch_id="tdd", outcome="expected_tdd_red")
        self.assertEqual(result["ledger"]["corrective_cycles"], 0)
        self.invoke("reserve", dispatch_id="verify", kind="verification")
        with self.assertRaises(ValueError):
            self.invoke("complete", dispatch_id="verify", outcome="expected_tdd_red")

    def test_no_wall_clock_limit_but_unknown_clock_and_self_asserted_pause_fail_closed(self):
        self.invoke("start")
        self.now += 86400
        late = self.invoke("reserve", dispatch_id="late", kind="implementation")
        self.assertEqual(late["disposition"], "continue")
        self.assertEqual(late["reasons"], [])
        self.now = 900
        self.assertIn("clock_moved_backwards", self.invoke("status", mode="read_only")["reasons"])
        with self.assertRaises(ValueError):
            self.invoke("pause", authorized=True, pause_kind="human_uat")

    def test_only_independent_native_wait_events_exclude_wall_time(self):
        initial = self.invoke("start")
        self.now += 100
        self.invoke("pause", native_observation={"native_event_id": "wait-start", "kind": "human_uat",
                    "action": "wait_started", "run_id": initial["ledger"]["run_id"]})
        self.now += 8000
        paused = self.invoke("status", mode="read_only")
        self.assertEqual(paused["elapsed_seconds"], 100)
        self.invoke("resume", native_observation={"native_event_id": "wait-end", "kind": "human_uat",
                    "action": "wait_ended", "wait_start_event_id": "wait-start", "run_id": initial["ledger"]["run_id"]})
        self.now += 100
        self.assertEqual(self.invoke("status", mode="read_only")["elapsed_seconds"], 200)

    def test_wait_end_replay_and_wrong_pair_cannot_exclude_more_time(self):
        initial = self.invoke("start")
        common = {"kind": "human_uat", "run_id": initial["ledger"]["run_id"]}
        self.invoke("pause", native_observation={**common, "native_event_id": "start-one", "action": "wait_started"})
        self.now += 100
        self.invoke("resume", native_observation={**common, "native_event_id": "end-one", "action": "wait_ended", "wait_start_event_id": "start-one"})
        self.invoke("pause", native_observation={**common, "native_event_id": "start-two", "action": "wait_started"})
        self.now += 100
        for event_id, start_id in (("end-one", "start-two"), ("end-two", "start-one")):
            with self.subTest(event_id=event_id, start_id=start_id):
                with self.assertRaises(ValueError):
                    self.invoke("resume", native_observation={**common, "native_event_id": event_id,
                                "action": "wait_ended", "wait_start_event_id": start_id})

    def test_completed_work_does_not_silently_reset_checkpoint_deadline(self):
        self.invoke("start")
        self.now += 2500
        self.invoke("reserve", dispatch_id="work", kind="implementation")
        self.invoke("complete", dispatch_id="work", outcome="completed")
        self.now += 300
        self.assertTrue(self.invoke("status", mode="read_only")["checkpoint_due"])
        self.assertFalse(self.invoke("checkpoint")["checkpoint_due"])

    def test_corrupted_boolean_counter_and_unapproved_invariant_rejected(self):
        result = self.invoke("start")
        path = self.root / result["ledger_path"]
        original = json.loads(path.read_text())
        for key, value in (("corrective_cycles", True), ("workflow_identity", None)):
            with self.subTest(key=key):
                corrupted = {**original, key: value}
                if value is None:
                    corrupted.pop(key)
                path.write_text(json.dumps(corrupted))
                with self.assertRaises(ValueError):
                    self.invoke("status", mode="read_only")

    def test_dry_run_does_not_write(self):
        self.invoke("start", mode="dry_run")
        self.assertFalse((self.root / "feature/.process").exists())

    def test_interrupted_atomic_publication_preserves_previous_record(self):
        first = self.invoke("start")
        path = self.root / first["ledger_path"]
        before = path.read_bytes()
        with patch("speckit_pro_runner.execution_control.os.replace", side_effect=OSError("injected publication interruption")):
            with self.assertRaises(OSError):
                durable_json(path, {"partial": True})
        self.assertEqual(before, path.read_bytes())
        self.assertEqual(list(path.parent.glob(".execution-*")), [])

    def test_existing_lock_fails_closed_without_resetting_reservations(self):
        first = self.invoke("start")
        path = self.root / first["ledger_path"]
        path.with_suffix(".lock").mkdir()
        with self.assertRaises(ValueError):
            self.invoke("reserve", dispatch_id="blocked", kind="corrective", failure_invariant="FR-001")
        self.assertEqual(json.loads(path.read_text())["corrective_cycles"], 0)


class CorrectiveContinuationTests(_ExecutionControlFixture, unittest.TestCase):
    def test_consensus_continuation_rejects_unbound_or_replayed_approval(self):
        self.invoke("start")
        owner = self.invoke("reserve", dispatch_id="analyze", kind="corrective", failure_invariant="FR-001")
        reservation = owner["reservation_id"]
        self.invoke("complete", dispatch_id="analyze", outcome="completed")
        self.invoke("reserve", dispatch_id="other-family", kind="corrective", failure_invariant="FR-002")
        approval = {"native_event_id": "operator-consensus-message", "run_id": self.run_id,
                    "action": "corrective_continuation_approved", "completed_dispatch_id": "analyze",
                    "continuation_dispatch_id": "metadata", "reservation_id": reservation,
                    "purpose": "task_metadata_reconciliation"}
        path = next((self.root / "feature/.process/execution-control").glob("*.json"))
        before = path.read_bytes()
        bad_events = (None, {**approval, "run_id": "wrong-run"},
                      {**approval, "action": "corrective_retry_approved"},
                      {**approval, "completed_dispatch_id": "other-family"},
                      {**approval, "continuation_dispatch_id": "different"},
                      {**approval, "reservation_id": "different"},
                      {**approval, "purpose": "unbounded_repair"})
        for event in bad_events:
            with self.subTest(event=event), self.assertRaises(ValueError):
                self.invoke("authorize-corrective-continuation", dispatch_id="metadata",
                            completed_dispatch_id="analyze", reservation_id=reservation,
                            native_observation=event)
            self.assertEqual(path.read_bytes(), before)
        accepted = self.invoke("authorize-corrective-continuation", dispatch_id="metadata",
                               completed_dispatch_id="analyze", reservation_id=reservation,
                               native_observation=approval)
        self.assertEqual(accepted["ledger"]["corrective_cycles"], 2)
        with self.assertRaises(ValueError):
            self.invoke("pause", native_observation={"native_event_id": "operator-consensus-message",
                                                     "run_id": self.run_id, "kind": "human_uat",
                                                     "action": "wait_started"})
        with self.assertRaises(ValueError):
            self.invoke("authorize-corrective-continuation", dispatch_id="metadata-two",
                        completed_dispatch_id="analyze", reservation_id=reservation,
                        native_observation={**approval, "native_event_id": "second-message",
                                            "continuation_dispatch_id": "metadata-two"})
        recorded = path.read_bytes()
        tampered = json.loads(recorded)
        tampered["dispatches"]["metadata"]["continuation_purpose"] = "unbounded_repair"
        path.write_text(json.dumps(tampered))
        with self.assertRaises(ValueError):
            self.invoke("status", mode="read_only")
        path.write_bytes(recorded)

    def test_approved_consensus_metadata_continuation_after_completed_retry(self):
        started = self.invoke("start")
        owner = self.invoke("reserve", dispatch_id="analyze", kind="corrective", failure_invariant="FR-001")
        reservation = owner["reservation_id"]
        self.invoke("reconcile", dispatch_id="analyze")
        self.invoke("complete", dispatch_id="analyze", outcome="failed", native_observation={
            "native_event_id": "host-auth-error", "run_id": self.run_id,
            "dispatch_id": "analyze", "action": "dispatch_result", "outcome": "failed"})
        self.invoke("reserve", dispatch_id="other-family", kind="corrective", failure_invariant="FR-002")
        self.invoke("authorize-corrective-retry", dispatch_id="analyze-retry", failed_dispatch_id="analyze",
                    reservation_id=reservation, native_observation={
            "native_event_id": "operator-retry-message", "run_id": self.run_id,
            "action": "corrective_retry_approved", "failed_dispatch_id": "analyze",
            "failed_native_event_id": "host-auth-error", "retry_dispatch_id": "analyze-retry",
            "reservation_id": reservation, "failure_kind": "infrastructure"})
        self.invoke("complete", dispatch_id="analyze-retry", outcome="completed")
        feature = self.root / "feature"
        (feature / ".process").mkdir(exist_ok=True)
        (feature / "plan.md").write_text("plan\n")
        tasks = "## Phase 1\n- [ ] T001 Reconcile metadata after consensus\n"
        (feature / "tasks.md").write_text(tasks)
        sidecar = feature / ".process/task-execution.json"
        metadata = {"schema_version": "task-execution.v1",
                    "fingerprints": fingerprints((feature / "spec.md").read_text(), "plan\n", tasks),
                    "tasks": {"T001": {"capability_group": "metadata", "depends_on": [],
                                       "owns": ["feature/.process/task-execution.json"],
                                       "tdd_unit": "metadata"}}}
        sidecar.write_text(json.dumps(metadata))
        request = {"tasks_file": "feature/tasks.md", "task_execution_required": True}
        initial_validation = validate_task_execution(request, self.root.resolve())
        self.assertEqual(initial_validation["exit_code"], 0, initial_validation)
        (feature / "spec.md").write_text("- FR-001: preserve data\n- FR-002: no secrets\nconsensus clarification\n")
        self.assertEqual(validate_task_execution(request, self.root.resolve())["exit_code"], 2)
        self.assertEqual(self.invoke("reserve", dispatch_id="metadata-ordinary", kind="corrective",
                                     reservation_id=reservation)["reasons"], ["corrective_cycle_already_closed"])

        approval = {"native_event_id": "operator-consensus-message", "run_id": self.run_id,
                    "action": "corrective_continuation_approved", "completed_dispatch_id": "analyze-retry",
                    "continuation_dispatch_id": "metadata", "reservation_id": reservation,
                    "purpose": "task_metadata_reconciliation"}
        before = self.invoke("status", mode="read_only")["ledger"]
        preview = self.invoke("authorize-corrective-continuation", mode="dry_run", dispatch_id="metadata",
                              completed_dispatch_id="analyze-retry", reservation_id=reservation,
                              native_observation=approval)
        self.assertEqual(preview["ledger"]["corrective_cycles"], 2)
        self.assertEqual(self.invoke("status", mode="read_only")["ledger"], before)
        continued = self.invoke("authorize-corrective-continuation", dispatch_id="metadata",
                                completed_dispatch_id="analyze-retry", reservation_id=reservation,
                                native_observation=approval)
        self.assertEqual(continued["disposition"], "continue")
        self.assertEqual(continued["ledger"]["run_id"], started["ledger"]["run_id"])
        self.assertEqual(continued["ledger"]["corrective_cycles"], 2)
        self.assertEqual(continued["ledger"]["dispatches"]["analyze"]["outcome"], "failed")
        self.assertEqual(continued["ledger"]["dispatches"]["analyze-retry"]["outcome"], "completed")
        self.assertEqual(continued["ledger"]["dispatches"]["metadata"]["continuation_of"], "analyze-retry")
        self.assertEqual(continued["ledger"]["dispatches"]["metadata"]["operator_continuation_event_id"],
                         "operator-consensus-message")
        schema = json.loads((Path(__file__).resolve().parents[3] /
                             "speckit-pro/speckit_pro_runner/contracts/execution-control.schema.json").read_text())
        self.assertEqual(json_schema_failures(continued["ledger"], schema, schema, "ledger"), [])
        metadata["fingerprints"] = fingerprints((feature / "spec.md").read_text(), "plan\n", tasks)
        sidecar.write_text(json.dumps(metadata))
        self.assertEqual(validate_task_execution(request, self.root.resolve())["exit_code"], 0)
        self.invoke("complete", dispatch_id="metadata", outcome="completed")
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")
        with self.assertRaises(ValueError):
            self.invoke("authorize-corrective-continuation", dispatch_id="metadata-again",
                        completed_dispatch_id="analyze-retry", reservation_id=reservation,
                        native_observation={**approval, "native_event_id": "operator-second-message",
                                            "continuation_dispatch_id": "metadata-again"})

class CorrectiveRecoveryTests(_ExecutionControlFixture, unittest.TestCase):
    def test_operator_approved_infrastructure_retry_preserves_failed_attempt_and_budget(self):
        started = self.invoke("start")
        first = self.invoke("reserve", dispatch_id="owner", kind="corrective", failure_invariant="FR-001")
        reservation = first["reservation_id"]
        self.invoke("reconcile", dispatch_id="owner")
        self.invoke("complete", dispatch_id="owner", outcome="failed", native_observation={
            "native_event_id": "host-auth-error", "run_id": self.run_id,
            "dispatch_id": "owner", "action": "dispatch_result", "outcome": "failed"})
        self.invoke("reserve", dispatch_id="other-family", kind="corrective", failure_invariant="FR-002")
        self.assertEqual(self.invoke("reserve", dispatch_id="ordinary-retry", kind="corrective",
                                     failure_invariant="FR-001")["reasons"], ["failure_family_budget_exhausted"])
        approval = {"native_event_id": "operator-message", "run_id": self.run_id,
                    "action": "corrective_retry_approved", "failed_dispatch_id": "owner",
                    "failed_native_event_id": "host-auth-error", "retry_dispatch_id": "owner-retry",
                    "reservation_id": reservation, "failure_kind": "infrastructure"}
        preview = self.invoke("authorize-corrective-retry", mode="dry_run", dispatch_id="owner-retry",
                              reservation_id=reservation, failed_dispatch_id="owner", native_observation=approval)
        self.assertEqual(preview["ledger"]["corrective_cycles"], 2)
        self.assertNotIn("owner-retry", self.invoke("status", mode="read_only")["ledger"]["dispatches"])
        retry = self.invoke("authorize-corrective-retry", dispatch_id="owner-retry",
                            reservation_id=reservation, failed_dispatch_id="owner", native_observation=approval)
        self.assertEqual(retry["disposition"], "continue")
        self.assertEqual(retry["ledger"]["run_id"], started["ledger"]["run_id"])
        self.assertEqual(retry["ledger"]["corrective_cycles"], 2)
        self.assertEqual(len(retry["ledger"]["reservations"]), 2)
        self.assertEqual(retry["ledger"]["dispatches"]["owner"]["outcome"], "failed")
        self.assertEqual(retry["ledger"]["dispatches"]["owner-retry"]["outcome"], "reserved")
        self.assertEqual(retry["ledger"]["dispatches"]["owner-retry"]["recovery_of"], "owner")
        self.assertEqual(retry["ledger"]["dispatches"]["owner-retry"]["operator_recovery_event_id"], "operator-message")
        schema = json.loads((Path(__file__).resolve().parents[3] /
                             "speckit-pro/speckit_pro_runner/contracts/execution-control.schema.json").read_text())
        self.assertEqual(json_schema_failures(retry["ledger"], schema, schema, "ledger"), [])
        self.invoke("complete", dispatch_id="owner-retry", outcome="completed")
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")
        with self.assertRaises(ValueError):
            self.invoke("authorize-corrective-retry", dispatch_id="second-retry",
                        reservation_id=reservation, failed_dispatch_id="owner",
                        native_observation={**approval, "native_event_id": "second-message",
                                            "retry_dispatch_id": "second-retry"})
        with self.assertRaises(ValueError):
            self.invoke("pause", native_observation={"native_event_id": "operator-message", "run_id": self.run_id,
                                                     "kind": "human_uat", "action": "wait_started"})

    def test_infrastructure_retry_rejects_unbound_or_replayed_approval(self):
        self.invoke("start")
        first = self.invoke("reserve", dispatch_id="owner", kind="corrective", failure_invariant="FR-001")
        reservation = first["reservation_id"]
        self.invoke("reconcile", dispatch_id="owner")
        self.invoke("complete", dispatch_id="owner", outcome="failed", native_observation={
            "native_event_id": "host-error", "run_id": self.run_id,
            "dispatch_id": "owner", "action": "dispatch_result", "outcome": "failed"})
        self.invoke("reserve", dispatch_id="other-family", kind="corrective", failure_invariant="FR-002")
        approval = {"native_event_id": "operator-message", "run_id": self.run_id,
                    "action": "corrective_retry_approved", "failed_dispatch_id": "owner",
                    "failed_native_event_id": "host-error", "retry_dispatch_id": "owner-retry",
                    "reservation_id": reservation, "failure_kind": "infrastructure"}
        path = self.root / "feature/.process/execution-control"
        ledger = next(path.glob("*.json"))
        before = ledger.read_bytes()
        bad_events = (None, {**approval, "run_id": "different-run"},
                      {**approval, "failed_native_event_id": "different-host-event"},
                      {**approval, "failure_kind": "assertion_failure"},
                      {**approval, "native_event_id": "host-error"},
                      {**approval, "retry_dispatch_id": "different-retry"})
        for event in bad_events:
            with self.subTest(event=event):
                with self.assertRaises(ValueError):
                    self.invoke("authorize-corrective-retry", dispatch_id="owner-retry",
                                reservation_id=reservation, failed_dispatch_id="owner", native_observation=event)
                self.assertEqual(ledger.read_bytes(), before)
        self.invoke("complete", dispatch_id="other-family", outcome="failed")
        other_reservation = self.invoke("status", mode="read_only")["ledger"]["dispatches"]["other-family"]["reservation_id"]
        with self.assertRaises(ValueError):
            self.invoke("authorize-corrective-retry", dispatch_id="other-retry", reservation_id=other_reservation,
                        failed_dispatch_id="other-family", native_observation={**approval,
                            "native_event_id": "another-message", "failed_dispatch_id": "other-family",
                            "failed_native_event_id": "missing-host-event", "retry_dispatch_id": "other-retry",
                            "reservation_id": other_reservation})


class CorrectiveExceptionTests(_ExecutionControlFixture, unittest.TestCase):
    SCOPE = "a" * 64

    def greenfield_run(self, consume_unresolved=True):
        spec = self.root / "feature/spec.md"
        spec.unlink()
        self.invoke("start")
        if consume_unresolved:
            self.invoke("reserve", dispatch_id="fix-a", kind="corrective", failure_invariant="FR-001")
            self.invoke("complete", dispatch_id="fix-a", outcome="failed")
        spec.write_text("- FR-001: preserve data\n- FR-002: no secrets\n")
        bound = self.invoke("bind-invariants", spec_file="feature/spec.md")["ledger"]
        return bound["invariant_binding"]["spec_sha256"]

    def approval(self, spec_digest, **changes):
        event = {"native_event_id": "operator-exception", "run_id": self.run_id,
                 "action": "corrective_exception_approved", "failure_invariant": "FR-001",
                 "dispatch_id": "fix-c", "failure_kind": "application",
                 "refusal_reason": "corrective_run_budget_exhausted",
                 "scope_sha256": self.SCOPE, "spec_sha256": spec_digest}
        return {**event, **changes}

    def authorize(self, event, mode="apply", **inputs):
        request = {"dispatch_id": "fix-c", "failure_invariant": "FR-001", "scope_sha256": self.SCOPE,
                   "native_observation": event, **inputs}
        return self.invoke("authorize-corrective-exception", mode=mode, **request)

    def test_exhausted_run_budget_recovers_only_the_approved_correction(self):
        digest_value = self.greenfield_run()
        self.invoke("reserve", dispatch_id="fix-b", kind="corrective", failure_invariant="FR-002")
        self.invoke("complete", dispatch_id="fix-b", outcome="failed")
        refused = self.invoke("reserve", dispatch_id="fix-c", kind="corrective", failure_invariant="FR-001")
        self.assertEqual(refused["reasons"], ["corrective_run_budget_exhausted"])
        before = self.invoke("status", mode="read_only")["ledger"]
        preview = self.authorize(self.approval(digest_value), mode="dry_run")
        self.assertEqual(preview["disposition"], "continue")
        self.assertNotIn("corrective_exception", self.invoke("status", mode="read_only")["ledger"])

        granted = self.authorize(self.approval(digest_value))
        ledger = granted["ledger"]
        self.assertEqual(granted["disposition"], "continue")
        for key in ("run_id", "started_at", "corrective_cycles", "reservations", "approved_invariants",
                    "invariant_binding"):
            self.assertEqual(ledger[key], before[key], key)
        for dispatch_id in ("fix-a", "fix-b"):
            self.assertEqual(ledger["dispatches"][dispatch_id], before["dispatches"][dispatch_id])
        exception = ledger["corrective_exception"]
        self.assertEqual({key: exception[key] for key in ("dispatch_id", "failure_invariant", "refusal_reason",
                                                          "scope_sha256", "spec_sha256", "operator_exception_event_id")},
                         {"dispatch_id": "fix-c", "failure_invariant": "FR-001",
                          "refusal_reason": "corrective_run_budget_exhausted", "scope_sha256": self.SCOPE,
                          "spec_sha256": digest_value, "operator_exception_event_id": "operator-exception"})
        self.assertEqual(ledger["dispatches"]["fix-c"]["reservation_id"], exception["reservation_id"])
        self.assertEqual(ledger["dispatches"]["fix-c"]["kind"], "corrective")
        self.assertNotIn(exception["reservation_id"], ledger["reservations"])
        self.assertEqual(granted["reservation_id"], exception["reservation_id"])
        schema = json.loads((Path(__file__).resolve().parents[3] /
                             "speckit-pro/speckit_pro_runner/contracts/execution-control.schema.json").read_text())
        self.assertEqual(json_schema_failures(ledger, schema, schema, "ledger"), [])

        self.invoke("complete", dispatch_id="fix-c", outcome="failed")
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")
        path = self.root / granted["ledger_path"]
        after = path.read_bytes()
        self.assertEqual(self.invoke("reserve", dispatch_id="fix-d", kind="corrective", failure_invariant="FR-001",
                                     mode="dry_run")["reasons"], ["corrective_run_budget_exhausted"])
        refusals = (
            lambda: self.authorize(self.approval(digest_value, native_event_id="second-exception", dispatch_id="fix-d"),
                                   dispatch_id="fix-d"),
            lambda: self.invoke("reserve", dispatch_id="nested", kind="corrective",
                                reservation_id=exception["reservation_id"]),
            lambda: self.invoke("authorize-corrective-retry", dispatch_id="fix-c-retry", failed_dispatch_id="fix-c",
                                reservation_id=exception["reservation_id"], native_observation={
                                    "native_event_id": "retry-message", "run_id": self.run_id,
                                    "action": "corrective_retry_approved", "failed_dispatch_id": "fix-c",
                                    "failed_native_event_id": "none", "retry_dispatch_id": "fix-c-retry",
                                    "reservation_id": exception["reservation_id"], "failure_kind": "infrastructure"}),
            lambda: self.invoke("pause", native_observation={"native_event_id": "operator-exception",
                                                             "run_id": self.run_id, "kind": "human_uat",
                                                             "action": "wait_started"}),
        )
        for index, refusal in enumerate(refusals):
            with self.subTest(refusal=index):
                with self.assertRaises(ValueError):
                    refusal()
                self.assertEqual(path.read_bytes(), after)

        tampered = json.loads(after)
        tampered["workflow_identity"]["relocation_event_ids"].append("operator-exception")
        path.write_text(json.dumps(tampered), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.invoke("status", mode="read_only")
        path.write_bytes(after)

    def test_repeat_of_reserved_family_is_recoverable_without_consuming_a_cycle(self):
        digest_value = self.greenfield_run(consume_unresolved=False)
        self.invoke("reserve", dispatch_id="fix-b", kind="corrective", failure_invariant="FR-001")
        path = self.root / self.invoke("status", mode="read_only")["ledger_path"]
        before = path.read_bytes()
        in_flight = self.approval(digest_value, refusal_reason="failure_family_budget_exhausted")
        with self.assertRaises(ValueError):
            self.authorize(in_flight)
        self.assertEqual(path.read_bytes(), before)
        self.invoke("complete", dispatch_id="fix-b", outcome="failed")
        self.assertEqual(self.invoke("reserve", dispatch_id="fix-c", kind="corrective", failure_invariant="FR-001",
                                     mode="dry_run")["reasons"], ["failure_family_budget_exhausted"])
        granted = self.authorize(in_flight)
        self.assertEqual(granted["disposition"], "continue")
        self.assertEqual(granted["ledger"]["corrective_cycles"], 1)
        self.invoke("complete", dispatch_id="fix-c", outcome="completed")
        self.assertEqual(self.invoke("reserve", dispatch_id="fix-d", kind="corrective",
                                     failure_invariant="FR-002")["disposition"], "continue")
        self.assertEqual(self.invoke("reserve", dispatch_id="fix-e", kind="corrective", failure_invariant="NFR-001",
                                     mode="dry_run")["reasons"], ["corrective_run_budget_exhausted"])
        with self.assertRaises(ValueError):
            self.invoke("authorize-corrective-continuation", dispatch_id="fix-c-metadata",
                        completed_dispatch_id="fix-c", reservation_id=granted["reservation_id"],
                        native_observation={"native_event_id": "continuation-message", "run_id": self.run_id,
                                            "action": "corrective_continuation_approved",
                                            "completed_dispatch_id": "fix-c",
                                            "continuation_dispatch_id": "fix-c-metadata",
                                            "reservation_id": granted["reservation_id"],
                                            "purpose": "task_metadata_reconciliation"})

    def test_unbound_mismatched_or_ordinary_requests_are_refused_without_mutation(self):
        digest_value = self.greenfield_run()
        self.invoke("reserve", dispatch_id="fix-b", kind="corrective", failure_invariant="FR-002")
        self.invoke("complete", dispatch_id="fix-b", outcome="failed")
        path = self.root / self.invoke("status", mode="read_only")["ledger_path"]
        before = path.read_bytes()
        approval = self.approval(digest_value)
        cases = (
            ({"event": None}, {}),
            ({"event": {**approval, "extra": "field"}}, {}),
            ({"event": self.approval(digest_value, run_id="other-run")}, {}),
            ({"event": self.approval(digest_value, action="corrective_retry_approved")}, {}),
            ({"event": self.approval(digest_value, failure_kind="infrastructure")}, {}),
            ({"event": self.approval(digest_value, failure_invariant="FR-002")}, {}),
            ({"event": self.approval(digest_value, dispatch_id="other-dispatch")}, {}),
            ({"event": self.approval(digest_value, refusal_reason="failure_family_budget_exhausted")}, {}),
            ({"event": self.approval(digest_value, scope_sha256="b" * 64)}, {}),
            ({"event": self.approval(digest_value, spec_sha256="c" * 64)}, {}),
            ({"event": self.approval(digest_value, failure_invariant="unresolved",
                                     refusal_reason="failure_family_budget_exhausted")},
             {"failure_invariant": "unresolved"}),
            ({"event": self.approval(digest_value, failure_invariant="FR-999")}, {"failure_invariant": "FR-999"}),
            ({"event": self.approval(digest_value, dispatch_id="fix-b")}, {"dispatch_id": "fix-b"}),
            ({"event": self.approval(digest_value, scope_sha256="not-a-digest")}, {"scope_sha256": "not-a-digest"}),
        )
        for index, (event, inputs) in enumerate(cases):
            with self.subTest(case=index):
                with self.assertRaises(ValueError):
                    self.authorize(event["event"], **inputs)
                self.assertEqual(path.read_bytes(), before)
        granted = self.authorize(approval)["ledger"]
        for change in ({"spec_sha256": "c" * 64}, {"failure_invariant": "unresolved"}, {"dispatch_id": "fix-b"}):
            with self.subTest(tamper=change):
                path.write_text(json.dumps({**granted, "corrective_exception": {**granted["corrective_exception"],
                                                                                **change}}))
                with self.assertRaises(ValueError):
                    self.invoke("status", mode="read_only")

    def test_exception_needs_a_refusing_ordinary_reserve_and_a_bound_spec(self):
        digest_value = self.greenfield_run()
        path = self.root / self.invoke("status", mode="read_only")["ledger_path"]
        before = path.read_bytes()
        for reason in ("corrective_run_budget_exhausted", "failure_family_budget_exhausted"):
            with self.subTest(reason=reason):
                with self.assertRaises(ValueError):
                    self.authorize(self.approval(digest_value, failure_invariant="FR-002", refusal_reason=reason),
                                   failure_invariant="FR-002")
                self.assertEqual(path.read_bytes(), before)
        other = tempfile.TemporaryDirectory()
        self.addCleanup(other.cleanup)
        self.root, self.run_id = Path(other.name), None
        (self.root / "feature").mkdir()
        (self.root / "feature/workflow.md").write_text("# Workflow\n")
        (self.root / "feature/spec.md").write_text("- FR-001: preserve data\n- FR-002: no secrets\n")
        self.invoke("start")
        for dispatch_id, invariant in (("fix-a", "FR-001"), ("fix-b", "FR-002")):
            self.invoke("reserve", dispatch_id=dispatch_id, kind="corrective", failure_invariant=invariant)
            self.invoke("complete", dispatch_id=dispatch_id, outcome="failed")
        with self.assertRaises(ValueError):
            self.authorize(self.approval(digest_value))


class CorrectiveFailureClassTests(_ExecutionControlFixture, unittest.TestCase):
    """One operator approval scoped to a failure class covers its follow-ups (issue 785)."""

    SCOPE = "a" * 64
    CLASS = {"test_file": "tests/cli.test.ts", "failure_signature": "Test timed out in 5000ms",
             "change_kind": "test_timeout"}

    def exhausted_run(self):
        spec = self.root / "feature/spec.md"
        text = spec.read_text()
        spec.unlink()
        self.invoke("start")
        spec.write_text(text)
        spec_digest = self.invoke("bind-invariants", spec_file="feature/spec.md")["ledger"]["invariant_binding"]["spec_sha256"]
        for dispatch_id, invariant in (("fix-a", "FR-001"), ("fix-b", "FR-002")):
            self.invoke("reserve", dispatch_id=dispatch_id, kind="corrective", failure_invariant=invariant)
            self.invoke("complete", dispatch_id=dispatch_id, outcome="failed")
        return spec_digest

    def approve_class(self, spec_digest, failure_class=None, mode="apply", **changes):
        failure_class = dict(self.CLASS if failure_class is None else failure_class)
        event = {"native_event_id": "operator-class", "run_id": self.run_id,
                 "action": "corrective_exception_approved", "failure_invariant": "FR-001",
                 "dispatch_id": "fix-c", "failure_kind": "application",
                 "refusal_reason": "failure_family_budget_exhausted", "scope_sha256": self.SCOPE,
                 "spec_sha256": spec_digest, "failure_class": failure_class, **changes}
        return self.invoke("authorize-corrective-exception", mode=mode, dispatch_id="fix-c",
                           failure_invariant="FR-001", scope_sha256=self.SCOPE,
                           failure_class=failure_class, native_observation=event)

    def follow_up(self, dispatch_id, mode="apply", **changes):
        return self.invoke("reserve-class-correction", mode=mode, dispatch_id=dispatch_id,
                           failure_class={**self.CLASS, **changes})

    def test_class_approval_admits_follow_ups_inside_the_exact_scope(self):
        digest_value = self.exhausted_run()
        granted = self.approve_class(digest_value)
        self.assertEqual(granted["disposition"], "continue")
        exception = granted["ledger"]["corrective_exception"]
        self.assertEqual(exception["failure_class"], {**self.CLASS, "follow_up_dispatch_ids": []})
        # The approved class-level fix lands, then the rerun times out different
        # tests in the same file with the same signature: no new question.
        self.invoke("complete", dispatch_id="fix-c", outcome="completed")
        preview = self.follow_up("fix-d", mode="dry_run")
        self.assertEqual(preview["disposition"], "continue")
        admitted = self.follow_up("fix-d")
        self.assertEqual(admitted["disposition"], "continue")
        ledger = admitted["ledger"]
        self.assertEqual(ledger["dispatches"]["fix-d"]["reservation_id"], exception["reservation_id"])
        self.assertEqual(ledger["dispatches"]["fix-d"]["kind"], "corrective")
        self.assertEqual(ledger["corrective_exception"]["failure_class"]["follow_up_dispatch_ids"], ["fix-d"])
        self.assertEqual(ledger["corrective_cycles"], 2)
        self.assertEqual(ledger["corrective_exception"]["operator_exception_event_id"], "operator-class")
        schema = json.loads((Path(__file__).resolve().parents[3] /
                             "speckit-pro/speckit_pro_runner/contracts/execution-control.schema.json").read_text())
        self.assertEqual(json_schema_failures(ledger, schema, schema, "ledger"), [])
        self.invoke("complete", dispatch_id="fix-d", outcome="completed")
        self.assertEqual(self.follow_up("fix-e")["disposition"], "continue")
        self.invoke("complete", dispatch_id="fix-e", outcome="completed")
        capped = self.follow_up("fix-f")
        self.assertEqual((capped["disposition"], capped["reasons"]), ("defer", ["failure_class_allowance_exhausted"]))
        self.assertEqual((capped["deferred"]["unit_kind"], capped["deferred"]["unit"]),
                         ("failure_class", self.CLASS["test_file"]))
        self.assertNotIn("fix-f", capped["ledger"]["dispatches"])
        self.assertEqual(capped["ledger"]["corrective_exception"]["failure_class"]["follow_up_dispatch_ids"],
                         ["fix-d", "fix-e"])
        self.assertEqual(json_schema_failures(capped["ledger"], schema, schema, "ledger"), [])

    def test_class_follow_ups_validate_in_recorded_order_not_key_order(self):
        """#789 review: the ledger is saved with sorted keys, so ownership must not depend on key order."""
        digest_value = self.exhausted_run()
        self.approve_class(digest_value)
        self.invoke("complete", dispatch_id="fix-c", outcome="completed")
        self.assertEqual(self.follow_up("fix-z")["disposition"], "continue")
        self.invoke("complete", dispatch_id="fix-z", outcome="completed")
        self.assertEqual(self.follow_up("fix-b2")["disposition"], "continue")
        done = self.invoke("complete", dispatch_id="fix-b2", outcome="completed")
        self.assertEqual(done["ledger"]["corrective_exception"]["failure_class"]["follow_up_dispatch_ids"],
                         ["fix-z", "fix-b2"])

    def test_follow_ups_outside_the_scope_or_after_an_unsettled_fix_are_refused(self):
        digest_value = self.exhausted_run()
        self.approve_class(digest_value)
        path = self.root / self.invoke("status", mode="read_only")["ledger_path"]
        in_flight = path.read_bytes()
        with self.assertRaises(ValueError):
            self.follow_up("fix-d")
        self.assertEqual(path.read_bytes(), in_flight)
        self.invoke("complete", dispatch_id="fix-c", outcome="completed")
        before = path.read_bytes()
        cases = (
            {"test_file": "tests/other.test.ts"},
            {"failure_signature": "Expected 2 to equal 3"},
            {"change_kind": "assertion_update"},
            {"test_file": "src/cli.ts"},
            {"test_file": "feature/.process/execution-control/cli.test.ts"},
            {"test_file": "../tests/cli.test.ts"},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    self.follow_up("fix-d", **changes)
                self.assertEqual(path.read_bytes(), before)
        for dispatch_id in ("fix-a", "fix-c"):
            with self.subTest(reused=dispatch_id):
                with self.assertRaises(ValueError):
                    self.follow_up(dispatch_id)
                self.assertEqual(path.read_bytes(), before)
        with self.assertRaises(ValueError):
            self.invoke("reserve-class-correction", dispatch_id="fix-d",
                        failure_class={**self.CLASS, "extra": "field"})
        self.assertEqual(path.read_bytes(), before)
        self.follow_up("fix-d")
        self.invoke("complete", dispatch_id="fix-d", outcome="failed")
        failed = path.read_bytes()
        with self.assertRaises(ValueError):
            self.follow_up("fix-e")
        self.assertEqual(path.read_bytes(), failed)

    def test_exact_diff_exception_and_production_class_admit_no_follow_up(self):
        digest_value = self.exhausted_run()
        path = self.root / self.invoke("status", mode="read_only")["ledger_path"]
        before = path.read_bytes()
        for failure_class in ({**self.CLASS, "test_file": "src/cli.ts"},
                              {**self.CLASS, "change_kind": "production_timeout"},
                              {**self.CLASS, "failure_signature": ""}):
            with self.subTest(failure_class=failure_class):
                with self.assertRaises(ValueError):
                    self.approve_class(digest_value, failure_class=failure_class)
                self.assertEqual(path.read_bytes(), before)
        event = {"native_event_id": "operator-class", "run_id": self.run_id,
                 "action": "corrective_exception_approved", "failure_invariant": "FR-001",
                 "dispatch_id": "fix-c", "failure_kind": "application",
                 "refusal_reason": "failure_family_budget_exhausted", "scope_sha256": self.SCOPE,
                 "spec_sha256": digest_value, "failure_class": {**self.CLASS, "test_file": "tests/other.test.ts"}}
        with self.assertRaises(ValueError):
            self.invoke("authorize-corrective-exception", dispatch_id="fix-c", failure_invariant="FR-001",
                        scope_sha256=self.SCOPE, failure_class=self.CLASS, native_observation=event)
        self.assertEqual(path.read_bytes(), before)
        exact = {key: value for key, value in event.items() if key != "failure_class"}
        self.invoke("authorize-corrective-exception", dispatch_id="fix-c", failure_invariant="FR-001",
                    scope_sha256=self.SCOPE, native_observation=exact)
        self.invoke("complete", dispatch_id="fix-c", outcome="completed")
        settled = path.read_bytes()
        with self.assertRaises(ValueError):
            self.follow_up("fix-d")
        self.assertEqual(path.read_bytes(), settled)

    def test_class_scope_is_tamper_checked_and_archived_by_a_replan(self):
        digest_value = self.exhausted_run()
        self.approve_class(digest_value)
        self.invoke("complete", dispatch_id="fix-c", outcome="completed")
        ledger = self.follow_up("fix-d")["ledger"]
        path = self.root / self.invoke("status", mode="read_only")["ledger_path"]
        good = path.read_bytes()
        exception = ledger["corrective_exception"]
        tampers = (
            {**exception, "failure_class": {**exception["failure_class"], "test_file": "src/cli.ts"}},
            {**exception, "failure_class": {**exception["failure_class"], "change_kind": "other"}},
            {**exception, "failure_class": {**exception["failure_class"], "follow_up_dispatch_ids": []}},
            {**exception, "failure_class": {**exception["failure_class"],
                                            "follow_up_dispatch_ids": ["fix-d", "fix-e", "fix-f"]}},
        )
        for index, tampered in enumerate(tampers):
            with self.subTest(tamper=index):
                path.write_text(json.dumps({**ledger, "corrective_exception": tampered}))
                with self.assertRaises(ValueError):
                    self.invoke("status", mode="read_only")
        path.write_bytes(good)
        self.invoke("complete", dispatch_id="fix-d", outcome="completed")
        spec = self.root / "feature/spec.md"
        spec.write_text("- FR-001: preserve data\n- FR-002: no secrets\n- FR-003: explain refusals\n")
        rotated = self.invoke("begin-replan-epoch", spec_file="feature/spec.md", native_observation={
            "native_event_id": "operator-replan", "run_id": self.run_id, "action": "replan_epoch_approved",
            "spec_sha256": hashlib.sha256(spec.read_bytes()).hexdigest()})["ledger"]
        self.assertEqual(rotated["corrective_epochs"][0]["corrective_exception"]["failure_class"]
                         ["follow_up_dispatch_ids"], ["fix-d"])
        archived = path.read_bytes()
        with self.assertRaises(ValueError):
            self.follow_up("fix-e")
        self.assertEqual(path.read_bytes(), archived)


PLANNING_PHASES = ("Specify", "Clarify", "Plan", "Checklist", "Tasks", "Analyze", "Confidence Gate")


def stage_workflow(stage="implement", analyze="✅ Complete"):
    """A workflow file whose planning stage is complete and whose Stage row names ``stage``."""
    rows = [(phase, analyze if phase == "Analyze" else "✅ Complete") for phase in PLANNING_PHASES]
    rows.append(("Implement", "⏳ Pending"))
    stage_row = f"| **Stage** | {stage} |\n" if stage else ""
    return ("# Workflow\n\n## Workflow Overview\n\n| Phase | Command | Status | Notes |\n"
            + "|-------|---------|--------|-------|\n"
            + "".join(f"| {phase} | `/speckit-run` | {status} | |\n" for phase, status in rows)
            + "\n### Basic Information\n\n| Field | Value |\n|-------|-------|\n"
            + "| **Branch** | `test-branch` |\n" + stage_row)


class ReplanEpochTests(_ExecutionControlFixture, unittest.TestCase):
    SCOPE = "a" * 64

    def rescope(self):
        spec = self.root / "feature/spec.md"
        spec.write_text("- FR-001: preserve data\n- FR-002: no secrets\n- FR-003: explain refusals\n")
        return hashlib.sha256(spec.read_bytes()).hexdigest()

    def epoch_event(self, spec_digest, **changes):
        event = {"native_event_id": "operator-replan", "run_id": self.run_id,
                 "action": "replan_epoch_approved", "spec_sha256": spec_digest}
        return {**event, **changes}

    def begin(self, event, mode="apply"):
        return self.invoke("begin-replan-epoch", mode=mode, spec_file="feature/spec.md", native_observation=event)

    def greenfield(self):
        spec = self.root / "feature/spec.md"
        text = spec.read_text()
        spec.unlink()
        self.invoke("start")
        spec.write_text(text)
        self.invoke("bind-invariants", spec_file="feature/spec.md")
        for dispatch_id, invariant in (("fix-a", "FR-001"), ("fix-b", "FR-002")):
            self.invoke("reserve", dispatch_id=dispatch_id, kind="corrective", failure_invariant=invariant)
            self.invoke("complete", dispatch_id=dispatch_id, outcome="failed")
        spec_digest = self.invoke("status", mode="read_only")["ledger"]["invariant_binding"]["spec_sha256"]
        event = {"native_event_id": "operator-exception", "run_id": self.run_id,
                 "action": "corrective_exception_approved", "failure_invariant": "FR-001", "dispatch_id": "fix-c",
                 "failure_kind": "application", "refusal_reason": "failure_family_budget_exhausted",
                 "scope_sha256": self.SCOPE, "spec_sha256": spec_digest}
        self.invoke("authorize-corrective-exception", dispatch_id="fix-c", failure_invariant="FR-001",
                    scope_sha256=self.SCOPE, native_observation=event)
        self.invoke("complete", dispatch_id="fix-c", outcome="completed")

    def test_approved_replan_opens_a_fresh_allowance_and_keeps_history(self):
        self.greenfield()
        before = self.invoke("status", mode="read_only")["ledger"]
        self.assertEqual(self.invoke("reserve", dispatch_id="fix-d", kind="corrective", failure_invariant="FR-002",
                                     mode="dry_run")["reasons"], ["failure_family_budget_exhausted"])
        new_digest = self.rescope()
        preview = self.begin(self.epoch_event(new_digest), mode="dry_run")
        self.assertEqual(preview["disposition"], "continue")
        self.assertNotIn("corrective_epochs", self.invoke("status", mode="read_only")["ledger"])

        ledger = self.begin(self.epoch_event(new_digest))["ledger"]
        self.assertEqual(ledger["run_id"], before["run_id"])
        self.assertEqual(ledger["started_at"], before["started_at"])
        self.assertEqual((ledger["corrective_cycles"], ledger["reservations"], ledger["dispatches"]), (0, {}, {}))
        self.assertNotIn("corrective_exception", ledger)
        self.assertEqual(ledger["approved_invariants"], ["FR-001", "FR-002", "FR-003"])
        self.assertEqual(ledger["invariant_binding"]["spec_sha256"], new_digest)
        [epoch] = ledger["corrective_epochs"]
        for key in ("corrective_cycles", "reservations", "dispatches", "approved_invariants",
                    "invariant_binding", "corrective_exception"):
            self.assertEqual(epoch[key], before[key], key)
        self.assertEqual(epoch["epoch_event_id"], "operator-replan")
        schema = json.loads((Path(__file__).resolve().parents[3] /
                             "speckit-pro/speckit_pro_runner/contracts/execution-control.schema.json").read_text())
        self.assertEqual(json_schema_failures(ledger, schema, schema, "ledger"), [])

        granted = self.invoke("reserve", dispatch_id="fix-d", kind="corrective", failure_invariant="FR-003")
        self.assertEqual(granted["disposition"], "continue")
        self.assertIn(granted["reservation_id"], granted["ledger"]["reservations"])
        self.assertEqual(self.invoke("reserve", dispatch_id="fix-a", kind="corrective", failure_invariant="FR-001",
                                     mode="dry_run")["reasons"], ["dispatch_already_reserved_no_relaunch"])
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")

    def test_replan_refuses_replay_mismatch_and_unsettled_work_without_mutation(self):
        self.greenfield()
        new_digest = self.rescope()
        path = self.root / self.invoke("status", mode="read_only")["ledger_path"]
        before = path.read_bytes()
        refusals = (
            self.epoch_event(new_digest, run_id="another-run"),
            self.epoch_event(new_digest, action="corrective_exception_approved"),
            self.epoch_event("b" * 64),
            self.epoch_event(new_digest, native_event_id="operator-exception"),
            {k: v for k, v in self.epoch_event(new_digest).items() if k != "spec_sha256"},
        )
        for index, event in enumerate(refusals):
            with self.subTest(refusal=index):
                with self.assertRaises(ValueError):
                    self.begin(event)
                self.assertEqual(path.read_bytes(), before)

        self.begin(self.epoch_event(new_digest))
        rotated = path.read_bytes()
        with self.assertRaises(ValueError):
            self.begin(self.epoch_event(new_digest))
        self.assertEqual(path.read_bytes(), rotated)

        self.invoke("reserve", dispatch_id="fix-d", kind="corrective", failure_invariant="FR-003")
        running = path.read_bytes()
        with self.assertRaises(ValueError):
            self.begin(self.epoch_event(new_digest, native_event_id="operator-replan-2"))
        self.assertEqual(path.read_bytes(), running)

        tampered = json.loads(running)
        tampered["corrective_epochs"][0]["corrective_cycles"] = 1
        path.write_text(json.dumps(tampered), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.invoke("status", mode="read_only")
        tampered = json.loads(running)
        tampered["dispatches"]["fix-a"] = tampered["corrective_epochs"][0]["dispatches"]["fix-a"]
        path.write_text(json.dumps(tampered), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.invoke("status", mode="read_only")
        path.write_bytes(running)


class StageEpochTests(_ExecutionControlFixture, unittest.TestCase):
    """An operator's explicit `--stage implement` after a complete plan opens one fresh allowance."""

    SCOPE = ReplanEpochTests.SCOPE
    greenfield = ReplanEpochTests.greenfield
    IMPLEMENT = ["--stage", "implement"]

    def begin(self, args, mode="apply"):
        return self.invoke("begin-stage-epoch", mode=mode, autopilot_args=args)

    def test_operator_stage_transition_opens_a_fresh_allowance_and_keeps_history(self):
        self.greenfield()
        (self.root / "feature/workflow.md").write_text(stage_workflow())
        before = self.invoke("status", mode="read_only")["ledger"]
        self.assertEqual(self.invoke("reserve", dispatch_id="fix-d", kind="corrective", failure_invariant="FR-001",
                                     mode="dry_run")["reasons"], ["failure_family_budget_exhausted"])
        preview = self.begin(self.IMPLEMENT, mode="dry_run")
        self.assertEqual(preview["disposition"], "continue")
        self.assertNotIn("corrective_epochs", self.invoke("status", mode="read_only")["ledger"])

        opened = self.begin(self.IMPLEMENT)
        self.assertEqual((opened["disposition"], opened["stage_epoch_opened"], opened["corrective_epoch"]),
                         ("continue", True, 1))
        ledger = opened["ledger"]
        self.assertEqual((ledger["run_id"], ledger["started_at"]), (before["run_id"], before["started_at"]))
        self.assertEqual((ledger["corrective_cycles"], ledger["reservations"], ledger["dispatches"]), (0, {}, {}))
        self.assertNotIn("corrective_exception", ledger)
        self.assertEqual(ledger["approved_invariants"], before["approved_invariants"])
        self.assertEqual(ledger["invariant_binding"], before["invariant_binding"])
        [epoch] = ledger["corrective_epochs"]
        for key in ("corrective_cycles", "reservations", "dispatches", "approved_invariants",
                    "invariant_binding", "corrective_exception"):
            self.assertEqual(epoch[key], before[key], key)
        self.assertEqual((epoch["epoch_event_id"], epoch["stage_transition"]),
                         ("stage-transition:implement", "implement"))
        schema = json.loads((Path(__file__).resolve().parents[3] /
                             "speckit-pro/speckit_pro_runner/contracts/execution-control.schema.json").read_text())
        self.assertEqual(json_schema_failures(ledger, schema, schema, "ledger"), [])

        granted = self.invoke("reserve", dispatch_id="fix-d", kind="corrective", failure_invariant="FR-001")
        self.assertEqual(granted["disposition"], "continue")
        self.assertEqual(self.invoke("reserve", dispatch_id="fix-a", kind="corrective", failure_invariant="FR-002",
                                     mode="dry_run")["reasons"], ["dispatch_already_reserved_no_relaunch"])

    def test_a_resumed_implement_invocation_does_not_open_a_second_allowance(self):
        self.greenfield()
        (self.root / "feature/workflow.md").write_text(stage_workflow())
        self.begin(self.IMPLEMENT)
        self.invoke("reserve", dispatch_id="fix-d", kind="corrective", failure_invariant="FR-001")
        self.invoke("complete", dispatch_id="fix-d", outcome="completed")
        path = self.root / self.invoke("status", mode="read_only")["ledger_path"]
        spent = path.read_bytes()
        again = self.begin(self.IMPLEMENT)
        self.assertEqual((again["disposition"], again["stage_epoch_opened"]), ("continue", False))
        self.assertEqual(again["ledger"]["corrective_cycles"], 1)
        self.assertEqual(len(again["ledger"]["corrective_epochs"]), 1)
        self.assertEqual(json.loads(path.read_bytes())["dispatches"], json.loads(spent)["dispatches"])
        with self.assertRaises(ValueError):
            self.invoke("begin-replan-epoch", spec_file="feature/spec.md",
                        native_observation={"native_event_id": "stage-transition:implement", "run_id": self.run_id,
                                            "action": "replan_epoch_approved",
                                            "spec_sha256": hashlib.sha256((self.root / "feature/spec.md").read_bytes()).hexdigest()})

    def test_only_an_explicit_implement_stage_after_complete_planning_opens_an_allowance(self):
        self.greenfield()
        workflow = self.root / "feature/workflow.md"
        path = self.root / self.invoke("status", mode="read_only")["ledger_path"]
        before = path.read_bytes()
        refusals = (
            ("auto-detected stage", [], stage_workflow()),
            ("full stage", ["--stage", "full"], stage_workflow("full")),
            ("plan stage", ["--stage", "plan"], stage_workflow("plan")),
            ("conflicting stages", ["--stage", "implement", "--stage", "plan"], stage_workflow()),
            ("argv is not a string list", "--stage implement", stage_workflow()),
            ("planning incomplete", self.IMPLEMENT, stage_workflow(analyze="⏳ Pending")),
            ("stage row not yet written", self.IMPLEMENT, stage_workflow("plan")),
            ("no stage row", self.IMPLEMENT, stage_workflow("")),
            ("no overview table", self.IMPLEMENT, "# Workflow\n"),
        )
        for label, args, text in refusals:
            with self.subTest(refusal=label):
                workflow.write_text(text)
                with self.assertRaises(ValueError):
                    self.begin(args)
                self.assertEqual(path.read_bytes(), before)

        workflow.write_text(stage_workflow())
        self.invoke("reserve", dispatch_id="verify-1", kind="verification")
        running = path.read_bytes()
        with self.assertRaises(ValueError):
            self.begin(self.IMPLEMENT)
        self.assertEqual(path.read_bytes(), running)

    def test_a_forged_stage_epoch_record_fails_validation(self):
        self.greenfield()
        (self.root / "feature/workflow.md").write_text(stage_workflow())
        self.begin(self.IMPLEMENT)
        path = self.root / self.invoke("status", mode="read_only")["ledger_path"]
        opened = path.read_bytes()
        forgeries = (
            ("unknown stage", {"stage_transition": "plan"}),
            ("event id disagrees", {"epoch_event_id": "operator-replan"}),
            ("reserved id without a stage", {"stage_transition": None}),
        )
        for label, change in forgeries:
            with self.subTest(forgery=label):
                tampered = json.loads(opened)
                epoch = tampered["corrective_epochs"][0]
                for key, value in change.items():
                    if value is None:
                        epoch.pop(key)
                    else:
                        epoch[key] = value
                path.write_text(json.dumps(tampered), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.invoke("status", mode="read_only")
        path.write_bytes(opened)


    def test_both_hosts_document_the_stage_allowance(self):
        plugin = Path(__file__).resolve().parents[3] / "speckit-pro"
        shared = (plugin / "skills/speckit-autopilot/references/execution-efficiency.md").read_text()
        for phrase in ("`begin-stage-epoch`", "`autopilot_args`", "`stage-transition:implement`",
                       "`stage_epoch_opened=false`"):
            self.assertIn(phrase, shared)
        self.assertNotIn("stage changes, a reclaimed state mirror", shared)
        for host in ("skills/speckit-autopilot/SKILL.md", "skills/speckit-autopilot/references/error-recovery.md",
                     "codex-skills/speckit-autopilot/references/error-recovery-codex.md"):
            with self.subTest(host=host):
                self.assertIn("`begin-stage-epoch`", " ".join((plugin / host).read_text().split()))

class IncrementReviewAllowanceTests(_ExecutionControlFixture, unittest.TestCase):
    """Review fixes inside one increment's owned paths draw on that increment's own bound."""

    TASKS = ("## Phase 3: Stories\n- [ ] T001 Build the alpha increment\n"
             + "- [ ] T002 Build the beta increment\n- [ ] T003 Build the gamma increment\n")
    OWNERSHIP = {"T001": ("alpha", ["src/alpha", "src/common.py"]), "T002": ("beta", ["src/beta"]),
                 "T003": ("gamma", ["src/common.py"])}

    def write_sidecar(self, **changes):
        feature = self.root / "feature"
        (feature / ".process").mkdir(exist_ok=True)
        (feature / "plan.md").write_text("plan\n")
        (feature / "tasks.md").write_text(self.TASKS)
        tasks = {task_id: {"capability_group": "stories", "depends_on": [], "owns": owns, "tdd_unit": unit}
                 for task_id, (unit, owns) in self.OWNERSHIP.items()}
        metadata = {"schema_version": "task-execution.v1",
                    "fingerprints": fingerprints((feature / "spec.md").read_text(), "plan\n", self.TASKS),
                    "tasks": tasks, **changes}
        (feature / ".process/task-execution.json").write_text(json.dumps(metadata))

    def spend_run_wide_budget(self):
        self.invoke("start")
        for dispatch_id, invariant in (("fix-a", "FR-001"), ("fix-b", "FR-002")):
            self.invoke("reserve", dispatch_id=dispatch_id, kind="corrective", failure_invariant=invariant)
            self.invoke("complete", dispatch_id=dispatch_id, outcome="completed")
        self.assertEqual(self.invoke("reserve", dispatch_id="ordinary", kind="corrective", mode="dry_run",
                                     failure_invariant="FR-001")["reasons"], ["failure_family_budget_exhausted"])

    def review_fix(self, dispatch_id, unit, paths, mode="apply"):
        return self.invoke("reserve", mode=mode, dispatch_id=dispatch_id, kind="corrective", spec_file="feature/spec.md",
                           failure_invariant="FR-001", review_remediation={"tdd_unit": unit, "paths": paths})

    def test_review_fix_names_the_feature_spec_when_the_workflow_lives_elsewhere(self):
        self.write_sidecar()
        workflow = "docs/ai/specs/.process/SPEC-001-workflow.md"
        (self.root / workflow).parent.mkdir(parents=True)
        (self.root / workflow).write_text("# Workflow\n")
        run_id = execution_control(self.root, {"workflow_file": workflow, "action": "start"}, "apply")["ledger"]["run_id"]
        request = {"workflow_file": workflow, "action": "reserve", "expected_run_id": run_id, "kind": "corrective",
                   "dispatch_id": "alpha-review", "failure_invariant": "FR-001",
                   "review_remediation": {"tdd_unit": "alpha", "paths": ["src/alpha/core.py"]}}
        with self.assertRaisesRegex(ValueError, "explicit spec_file"):
            execution_control(self.root, request, "apply")
        admitted = execution_control(self.root, {**request, "spec_file": "feature/spec.md"}, "apply")
        self.assertEqual((admitted["disposition"], admitted["review_allowance"]), ("continue", "increment"))

    def test_review_fix_inside_owned_paths_is_admitted_after_run_wide_exhaustion_up_to_the_bound(self):
        self.write_sidecar()
        self.spend_run_wide_budget()
        first = self.review_fix("alpha-review-1", "alpha", ["src/alpha/core.py", "src/alpha"])
        self.assertEqual((first["disposition"], first["review_allowance"]), ("continue", "increment"))
        self.assertIsNone(first["reservation_id"])
        self.assertEqual(first["ledger"]["corrective_cycles"], 2)
        self.assertEqual(first["ledger"]["increment_allowances"]["alpha"],
                         {"rounds": 1, "dispatch_ids": ["alpha-review-1"]})
        self.assertEqual(first["ledger"]["dispatches"]["alpha-review-1"]["increment"], "alpha")
        self.invoke("complete", dispatch_id="alpha-review-1", outcome="completed")
        second = self.review_fix("alpha-review-2", "alpha", ["src/alpha/core.py"])
        self.assertEqual(second["disposition"], "continue")
        self.invoke("complete", dispatch_id="alpha-review-2", outcome="failed")
        path = self.root / second["ledger_path"]
        before = path.read_bytes()
        spent = self.review_fix("alpha-review-3", "alpha", ["src/alpha/core.py"])
        self.assertEqual(spent["reasons"], ["increment_review_allowance_exhausted"])
        self.assertEqual(spent["disposition"], "defer")
        self.assertEqual((spent["deferred"]["unit_kind"], spent["deferred"]["unit"]), ("increment", "alpha"))
        self.assertNotIn("alpha-review-3", spent["ledger"]["dispatches"])
        self.assertEqual(json.loads(path.read_bytes())["increment_allowances"],
                         json.loads(before)["increment_allowances"])
        self.assertEqual(self.review_fix("alpha-review-1", "beta", ["src/beta/b.py"])["reasons"],
                         ["dispatch_already_reserved_no_relaunch"])
        independent = self.review_fix("beta-review-1", "beta", ["src/beta/b.py"])
        self.assertEqual((independent["disposition"], independent["review_allowance"]), ("continue", "increment"))
        schema = json.loads((Path(__file__).resolve().parents[3] /
                             "speckit-pro/speckit_pro_runner/contracts/execution-control.schema.json").read_text())
        self.assertEqual(json_schema_failures(independent["ledger"], schema, schema, "ledger"), [])

    def test_fix_outside_ownership_or_reopening_accepted_work_uses_the_run_wide_budget(self):
        self.write_sidecar()
        self.invoke("start")
        outside = self.review_fix("alpha-reaches-beta", "alpha", ["src/alpha/core.py", "src/beta/b.py"])
        self.assertEqual((outside["disposition"], outside["review_allowance"]), ("continue", "run_wide"))
        self.assertEqual(outside["increment_ineligible"], "path_outside_increment_ownership")
        self.assertEqual(outside["ledger"]["corrective_cycles"], 1)
        self.assertNotIn("increment_allowances", outside["ledger"])
        self.invoke("complete", dispatch_id="alpha-reaches-beta", outcome="completed")
        self.invoke("reserve", dispatch_id="fix-b", kind="corrective", failure_invariant="FR-002")
        self.invoke("complete", dispatch_id="fix-b", outcome="completed")
        for paths in (["src/beta/b.py"], ["src/common.py"], ["src"]):
            with self.subTest(paths=paths):
                refused = self.review_fix("alpha-refused", "alpha", paths)
                self.assertEqual(refused["reasons"], ["failure_family_budget_exhausted"])
                self.assertEqual(refused["review_allowance"], "run_wide")
                self.assertNotIn("alpha-refused", refused["ledger"]["dispatches"])
        self.assertEqual(self.review_fix("alpha-refused", "alpha", ["src/common.py"])["increment_ineligible"],
                         "path_reopens_another_increment")

    def test_a_shared_file_is_judged_only_against_increments_still_open(self):
        self.write_sidecar()
        tasks = self.root / "feature/tasks.md"
        completed = self.TASKS.replace("- [ ] T003", "- [X] T003")
        tasks.write_text(completed)
        commit_fixture(self.root)
        self.spend_run_wide_budget()
        admitted = self.review_fix("alpha-shared", "alpha", ["src/common.py"])
        self.assertEqual((admitted["disposition"], admitted["review_allowance"]), ("continue", "increment"))
        self.assertNotIn("increment_ineligible", admitted)
        cases = {"open in the worktree": (completed, self.TASKS),
                 "checked but not committed": (self.TASKS, completed),
                 "open everywhere": (self.TASKS, self.TASKS),
                 "committed task definitions differ": (completed.replace("gamma", "delta"), completed)}
        for name, (committed, worktree) in cases.items():
            with self.subTest(case=name):
                tasks.write_text(committed)
                commit_fixture(self.root)
                tasks.write_text(worktree)
                refused = self.review_fix("alpha-" + name.replace(" ", "-"), "alpha", ["src/common.py"],
                                          mode="dry_run")
                self.assertEqual(refused["increment_ineligible"], "path_reopens_another_increment")
                self.assertEqual(refused["review_allowance"], "run_wide")

    def test_missing_stale_or_unknown_ownership_evidence_never_grants_a_free_allowance(self):
        self.spend_run_wide_budget()
        cases = (("no_sidecar", None, "alpha", ["src/alpha/core.py"]),
                 ("stale_fingerprints", {"fingerprints": {"spec_sha256": "0" * 64, "plan_sha256": "0" * 64,
                                                          "tasks_sha256": "0" * 64}}, "alpha", ["src/alpha/core.py"]),
                 ("unknown_unit", {}, "delta", ["src/alpha/core.py"]),
                 ("escaping_path", {}, "alpha", ["src/alpha/../../outside.py"]),
                 ("empty_paths", {}, "alpha", []),
                 ("malformed_owns", {"tasks": {"T001": {"tdd_unit": "alpha", "owns": "src/alpha"}}},
                  "alpha", ["src/alpha/core.py"]))
        for name, changes, unit, paths in cases:
            with self.subTest(case=name):
                sidecar = self.root / "feature/.process/task-execution.json"
                sidecar.unlink(missing_ok=True)
                if changes is not None:
                    self.write_sidecar(**changes)
                refused = self.review_fix("review-" + name.replace("_", "-"), unit, paths)
                self.assertEqual(refused["reasons"], ["failure_family_budget_exhausted"])
                self.assertEqual(refused["review_allowance"], "run_wide")
                self.assertNotIn("increment_allowances", refused["ledger"])
        for malformed in ({"tdd_unit": "alpha"}, {"tdd_unit": "alpha", "paths": "src/alpha"},
                          {"tdd_unit": "", "paths": ["src/alpha"]}, ["alpha"]):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                self.invoke("reserve", dispatch_id="malformed", kind="corrective", spec_file="feature/spec.md",
                            review_remediation=malformed)
        with self.assertRaises(ValueError):
            self.invoke("reserve", dispatch_id="not-corrective", kind="implementation", spec_file="feature/spec.md",
                        review_remediation={"tdd_unit": "alpha", "paths": ["src/alpha/core.py"]})

    def test_a_serial_plan_keeps_running_after_a_review_fix_deferral(self):
        from speckit_pro_runner.helpers.run_finalization import finalize_run

        self.write_sidecar()
        self.spend_run_wide_budget()
        for number in (1, 2):
            self.review_fix(f"alpha-review-{number}", "alpha", ["src/alpha/core.py"])
            self.invoke("complete", dispatch_id=f"alpha-review-{number}", outcome="completed")
        deferred = self.review_fix("alpha-review-3", "alpha", ["src/alpha/core.py"])
        self.assertEqual(deferred["disposition"], "defer")
        # beta depends on alpha in a strictly serial plan; its implementation still runs.
        dependent = self.invoke("reserve", dispatch_id="beta-implement", kind="implementation")
        self.assertEqual(dependent["disposition"], "continue")
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")
        self.invoke("reserve", dispatch_id="verify-g7", kind="verification")
        self.invoke("begin-verification", dispatch_id="verify-g7")
        evidence = failing_check_fingerprint("UNIT_TEST", ["python3", "-m", "unittest"], 0, True, b"", b"")
        with patch("speckit_pro_runner.execution_control.time.time", return_value=self.now):
            record_failing_checks(self.root, {"workflow_file": "feature/workflow.md", "expected_run_id": self.run_id,
                                              "dispatch_id": "verify-g7"},
                                  {**evidence, "head_sha": "a" * 40, "worktree_clean": True})
        self.invoke("complete", dispatch_id="verify-g7", outcome="completed")
        common = {"ledger_path": dependent["ledger_path"], "expected_run_id": self.run_id,
                  "gates": [{"gate": "G7", "status": "passed", "command": "python3 -m unittest",
                             "head_sha": "a" * 40, "dispatch_id": "verify-g7"}],
                  "pull_requests": [{"number": 1, "url": "https://github.com/example/repo/pull/1", "draft": True,
                                     "head_sha": "a" * 40}],
                  "resume_command": "/speckit-pro:speckit-autopilot feature/workflow.md --stage implement"}
        running = finalize_run(self.root, {**common, "pending_items": ["T002 Build the beta increment"]})
        self.assertEqual((running["outcome"], running["human_stop"]), ("continue", None))
        # The deferred increment climbs its escalation tiers before it becomes a decision for the owner (issue 829).
        escalating = finalize_run(self.root, {**common, "pending_items": []})
        self.assertEqual((escalating["outcome"], escalating["human_stop"]), ("continue", None))
        self.assertIn("Escalate Increment alpha", escalating["pending_items"][0])
        for tier in (2, 3):
            self.invoke("reserve", dispatch_id=f"alpha-tier-{tier}", kind="corrective",
                        escalation={"unit_kind": "increment", "unit": "alpha", "tier": tier})
            self.invoke("complete", dispatch_id=f"alpha-tier-{tier}", outcome="failed")
        # Every tier failed: the run still finalizes ready for review, with the unit listed as a decision.
        ended = finalize_run(self.root, {**common, "pending_items": []})
        self.assertEqual((ended["outcome"], ended["mark_ready"]), ("complete_with_deferred", True))
        self.assertEqual([decision["class"] for decision in ended["decisions"]], ["exhausted"])
        self.assertIn("Decisions for you", ended["end_of_run_request"])
        self.assertIn("Increment alpha", ended["end_of_run_request"])

    def test_forged_or_overspent_increment_records_fail_closed(self):
        self.write_sidecar()
        self.spend_run_wide_budget()
        admitted = self.review_fix("alpha-review-1", "alpha", ["src/alpha/core.py"])
        path = self.root / admitted["ledger_path"]
        valid = path.read_bytes()
        forged_dispatch = {"kind": "corrective", "outcome": "reserved", "reserved_at": self.now,
                           "reservation_id": None, "reconciliations": 0, "increment": "alpha"}
        tampers = {
            "unlisted increment dispatch": lambda ledger: ledger["dispatches"].update(forged=forged_dispatch),
            "rounds over the bound": lambda ledger: (
                ledger["dispatches"].update({"a2": forged_dispatch, "a3": forged_dispatch}),
                ledger["increment_allowances"]["alpha"].update(
                    rounds=3, dispatch_ids=["alpha-review-1", "a2", "a3"])),
            "counter disagrees": lambda ledger: ledger["increment_allowances"]["alpha"].update(rounds=2),
            "allowance record dropped": lambda ledger: ledger.pop("increment_allowances"),
            "unreserved corrective": lambda ledger: ledger["dispatches"]["alpha-review-1"].pop("increment"),
            "increment on a reservation": lambda ledger: ledger["dispatches"]["alpha-review-1"].update(
                reservation_id=next(iter(ledger["reservations"]))),
        }
        for name, tamper in tampers.items():
            with self.subTest(tamper=name):
                ledger = json.loads(valid)
                tamper(ledger)
                path.write_text(json.dumps(ledger), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.invoke("status", mode="read_only")
        path.write_bytes(valid)
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")

    def test_stage_epoch_archives_increment_allowances(self):
        self.write_sidecar()
        self.spend_run_wide_budget()
        for number in (1, 2):
            self.review_fix(f"alpha-review-{number}", "alpha", ["src/alpha/core.py"])
            self.invoke("complete", dispatch_id=f"alpha-review-{number}", outcome="completed")
        (self.root / "feature/workflow.md").write_text(stage_workflow())
        opened = self.invoke("begin-stage-epoch", autopilot_args=["--stage", "implement"])
        self.assertEqual(opened["ledger"]["corrective_epochs"][0]["increment_allowances"]["alpha"]["rounds"], 2)
        self.assertNotIn("increment_allowances", opened["ledger"])
        self.assertEqual(self.review_fix("alpha-review-1", "alpha", ["src/alpha/core.py"])["reasons"],
                         ["dispatch_already_reserved_no_relaunch"])
        fresh = self.review_fix("alpha-review-3", "alpha", ["src/alpha/core.py"])
        self.assertEqual((fresh["disposition"], fresh["ledger"]["increment_allowances"]["alpha"]["rounds"]),
                         ("continue", 1))
        schema = json.loads((Path(__file__).resolve().parents[3] /
                             "speckit-pro/speckit_pro_runner/contracts/execution-control.schema.json").read_text())
        self.assertEqual(json_schema_failures(fresh["ledger"], schema, schema, "ledger"), [])

    def test_both_hosts_document_the_increment_review_allowance(self):
        plugin = Path(__file__).resolve().parents[3] / "speckit-pro"
        shared = " ".join((plugin / "skills/speckit-autopilot/references/execution-efficiency.md").read_text().split())
        for phrase in ("`review_remediation`", "an explicit `spec_file`", "`increment_review_allowance_exhausted`",
                       "`review_allowance=increment`", "`review_allowance=run_wide`",
                       "`increment_ineligible`", "never draws on the run-wide"):
            self.assertIn(phrase, shared)
        for host in ("skills/speckit-autopilot/references/phase-execution.md",
                     "codex-skills/speckit-autopilot/references/phase-execution-codex.md"):
            with self.subTest(host=host):
                text = " ".join((plugin / host).read_text().split())
                self.assertIn("`review_remediation`", text)
                self.assertIn("`spec_file`", text)
                self.assertIn("`increment_review_allowance_exhausted`", text)
                self.assertIn("defer that increment", text)
                self.assertIn("never a mid-run question", text)
                self.assertNotIn("except `increment_review_allowance_exhausted`", text)
                self.assertIn("An exhausted correction allowance is not a stop", text)


SCHEMA_PATH = Path(__file__).resolve().parents[3] / "speckit-pro/speckit_pro_runner/contracts/execution-control.schema.json"


class DeferOnExhaustedAllowanceTests(_ExecutionControlFixture, unittest.TestCase):
    """An exhausted correction allowance defers the blocked unit instead of stopping the run (issue 795)."""

    def entry(self, dispatch_id, reason, unit_kind, unit):
        return {"dispatch_id": dispatch_id, "reason": reason, "unit_kind": unit_kind, "unit": unit,
                "deferred_at": self.now}

    def test_exhausted_family_and_run_budgets_defer_the_named_family_and_keep_refusing(self):
        self.invoke("start")
        self.invoke("reserve", dispatch_id="fix-a", kind="corrective", failure_invariant="FR-001")
        self.invoke("complete", dispatch_id="fix-a", outcome="completed")
        family = self.invoke("reserve", dispatch_id="fix-a-again", kind="corrective", failure_invariant="FR-001")
        self.assertEqual(family["disposition"], "defer")
        self.assertEqual(family["reasons"], ["failure_family_budget_exhausted"])
        expected_family = self.entry("fix-a-again", "failure_family_budget_exhausted", "failure_family", "FR-001")
        self.assertEqual(family["deferred"], expected_family)
        self.assertNotIn("fix-a-again", family["ledger"]["dispatches"])
        self.assertNotIn("reservation_id", family)
        self.assertEqual(family["ledger"]["corrective_cycles"], 1)
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")
        second = self.invoke("reserve", dispatch_id="fix-b", kind="corrective", failure_invariant="FR-002")
        self.assertEqual(second["disposition"], "continue")
        self.now += 5
        run = self.invoke("reserve", dispatch_id="fix-c", kind="corrective", failure_invariant="new words")
        self.assertEqual((run["disposition"], run["reasons"]), ("defer", ["corrective_run_budget_exhausted"]))
        expected_run = self.entry("fix-c", "corrective_run_budget_exhausted", "failure_family", "unresolved")
        self.assertEqual(run["deferred"], expected_run)
        on_disk = json.loads((self.root / run["ledger_path"]).read_text())
        self.assertEqual(on_disk["deferred"], [expected_family, expected_run])
        self.assert_schema_valid(on_disk)
        independent = self.invoke("reserve", dispatch_id="task-9", kind="implementation")
        self.assertEqual(independent["disposition"], "continue")
        self.now += 5
        repeated = self.invoke("reserve", dispatch_id="fix-c", kind="corrective", failure_invariant="new words")
        self.assertEqual((repeated["disposition"], repeated["deferred"]), ("defer", expected_run))
        self.assertEqual(repeated["ledger"]["deferred"], [expected_family, expected_run])
        path = self.root / run["ledger_path"]
        before = path.read_bytes()
        preview = self.invoke("reserve", mode="dry_run", dispatch_id="fix-d", kind="corrective",
                              failure_invariant="FR-002")
        self.assertEqual(preview["disposition"], "defer")
        self.assertEqual(path.read_bytes(), before)

    def test_a_spent_reservation_defers_its_family_for_nested_work(self):
        self.invoke("start")
        failed = self.invoke("reserve", dispatch_id="owner", kind="corrective", failure_invariant="FR-001")["reservation_id"]
        self.invoke("reserve", dispatch_id="nested-one", kind="corrective", reservation_id=failed)
        self.invoke("complete", dispatch_id="nested-one", outcome="failed")
        retry = self.invoke("reserve", dispatch_id="nested-two", kind="corrective", reservation_id=failed)
        self.assertEqual((retry["disposition"], retry["deferred"]), ("defer", self.entry(
            "nested-two", "corrective_cycle_failed_no_nested_retry", "failure_family", "FR-001")))
        closed = self.invoke("reserve", dispatch_id="fix-b", kind="corrective", failure_invariant="FR-002")["reservation_id"]
        self.invoke("complete", dispatch_id="fix-b", outcome="completed")
        late = self.invoke("reserve", dispatch_id="late-nested", kind="corrective", reservation_id=closed)
        self.assertEqual((late["disposition"], late["deferred"]), ("defer", self.entry(
            "late-nested", "corrective_cycle_already_closed", "failure_family", "FR-002")))
        self.assert_schema_valid(late["ledger"])

    def test_integrity_failures_and_unknown_effects_still_stop(self):
        self.invoke("start")
        self.invoke("reserve", dispatch_id="fix-a", kind="corrective", failure_invariant="FR-001")
        self.invoke("complete", dispatch_id="fix-a", outcome="completed")
        deferred = self.invoke("reserve", dispatch_id="fix-a-again", kind="corrective", failure_invariant="FR-001")
        path = self.root / deferred["ledger_path"]
        valid = path.read_bytes()
        relaunch = self.invoke("reserve", dispatch_id="fix-a", kind="corrective", failure_invariant="FR-002")
        self.assertEqual((relaunch["disposition"], relaunch["reasons"]),
                         ("checkpoint_required", ["dispatch_already_reserved_no_relaunch"]))
        entry = deferred["deferred"]
        tampers = {
            "unknown reason": lambda ledger: ledger["deferred"][0].update(reason="operator_said_so"),
            "unit not exhausted": lambda ledger: ledger["deferred"][0].update(unit="FR-002"),
            "wrong unit kind": lambda ledger: ledger["deferred"][0].update(unit_kind="increment"),
            "duplicate dispatch": lambda ledger: ledger["deferred"].append(dict(entry)),
            "extra key": lambda ledger: ledger["deferred"][0].update(approved=True),
            "missing key": lambda ledger: ledger["deferred"][0].pop("deferred_at"),
            "clock before start": lambda ledger: ledger["deferred"][0].update(deferred_at=-1),
            "clock out of order": lambda ledger: ledger["deferred"].append(
                {**entry, "dispatch_id": "later", "deferred_at": entry["deferred_at"] - 1}),
            "empty list": lambda ledger: ledger.update(deferred=[]),
            "not a list": lambda ledger: ledger.update(deferred={"fix-a-again": entry}),
            "run budget not spent": lambda ledger: ledger["deferred"][0].update(
                reason="corrective_run_budget_exhausted"),
        }
        for name, tamper in tampers.items():
            with self.subTest(tamper=name):
                ledger = json.loads(valid)
                tamper(ledger)
                path.write_text(json.dumps(ledger), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.invoke("status", mode="read_only")
                with self.assertRaises(ValueError):
                    self.invoke("reserve", dispatch_id="fix-b", kind="corrective", failure_invariant="FR-002")
        path.write_bytes(valid)
        self.invoke("reserve", dispatch_id="worker", kind="implementation")
        self.invoke("complete", dispatch_id="worker", outcome="unknown")
        unknown = self.invoke("reserve", dispatch_id="fix-b", kind="corrective", failure_invariant="FR-002")
        self.assertEqual(unknown["disposition"], "checkpoint_required")
        self.assertIn("unknown_dispatch_blocks_unit", unknown["reasons"])
        self.now = 1
        with self.assertRaisesRegex(ValueError, "clock moved backwards"):
            self.invoke("reserve", dispatch_id="fix-c", kind="corrective", failure_invariant="FR-002")

    def test_a_new_allowance_archives_the_deferrals_it_answers(self):
        spec = self.root / "feature/spec.md"
        text = spec.read_text()
        spec.unlink()
        self.invoke("start")
        spec.write_text(text)
        self.invoke("bind-invariants", spec_file="feature/spec.md")
        for dispatch_id, invariant in (("fix-a", "FR-001"), ("fix-b", "FR-002")):
            self.invoke("reserve", dispatch_id=dispatch_id, kind="corrective", failure_invariant=invariant)
            self.invoke("complete", dispatch_id=dispatch_id, outcome="failed")
        deferred = self.invoke("reserve", dispatch_id="fix-c", kind="corrective", failure_invariant="FR-001")
        self.assertEqual(deferred["disposition"], "defer")
        event = {"native_event_id": "operator-replan", "run_id": self.run_id, "action": "replan_epoch_approved",
                 "spec_sha256": hashlib.sha256(spec.read_bytes()).hexdigest()}
        opened = self.invoke("begin-replan-epoch", spec_file="feature/spec.md", native_observation=event)
        self.assertNotIn("deferred", opened["ledger"])
        self.assertEqual(opened["ledger"]["corrective_epochs"][0]["deferred"], [deferred["deferred"]])
        self.assert_schema_valid(opened["ledger"])
        admitted = self.invoke("reserve", dispatch_id="fix-c", kind="corrective", failure_invariant="FR-001")
        self.assertEqual(admitted["disposition"], "continue")
        path = self.root / opened["ledger_path"]
        forged = json.loads(path.read_text())
        forged["corrective_epochs"][0]["deferred"][0]["unit"] = "FR-009"
        path.write_text(json.dumps(forged), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.invoke("status", mode="read_only")


class DeferOnExhaustedAllowanceGuidanceTests(unittest.TestCase):
    """Both hosts defer exhausted-allowance work to the end-of-run request, never a mid-run question."""

    PLUGIN = Path(__file__).resolve().parents[3] / "speckit-pro"

    def flat(self, relative):
        return " ".join((self.PLUGIN / relative).read_text().split())

    def test_shared_ledger_reference_defers_and_keeps_approvals_for_the_end(self):
        text = self.flat("skills/speckit-autopilot/references/execution-efficiency.md")
        for phrase in ("`disposition=defer`", "`deferred`", "`unit_kind`", "`failure_class_allowance_exhausted`",
                       "`corrective_cycle_failed_no_nested_retry`", "end-of-run tools",
                       "never a mid-run question", "keep executing every independent task, increment, gate, and Post check",
                       "one end-of-run consolidated request", "`expected_failure`"):
            self.assertIn(phrase, text)
        for stale in ("checkpoint and obtain explicit operator approval for that exact correction",
                      "ask the operator to approve a fresh allowance",
                      "Ask the operator only when this stage's own allowance is spent"):
            self.assertNotIn(stale, text)

    def test_shared_gate_and_hardener_references_defer_on_exhaustion(self):
        gates = self.flat("skills/speckit-autopilot/references/gate-validation.md")
        escalation = gates.split("## Failure Escalation Protocol", 1)[1]
        for phrase in ("`disposition=defer`", "one end-of-run consolidated request", "never a mid-run question",
                       "`authorize-corrective-exception`", "`begin-replan-epoch`"):
            self.assertIn(phrase, escalation)
        for stale in ("**STOP** execution", "Wait for guidance", "Time/budget exhaustion checkpoints"):
            self.assertNotIn(stale, gates)
        hardener = self.flat("skills/speckit-autopilot/references/hardener-delegation.md")
        self.assertIn("On exhaustion retain the failing MUTATION result and defer", hardener)

    def test_both_hosts_turn_an_exhausted_budget_into_a_deferral(self):
        pairs = (("skills/speckit-autopilot/SKILL.md", "## Error Recovery", "## References"),
                 ("skills/speckit-autopilot/references/error-recovery.md", "## Common Issues", "## Context Window"),
                 ("codex-skills/speckit-autopilot/references/error-recovery-codex.md", "## Common Issues", None),
                 ("skills/speckit-autopilot/references/phase-execution.md",
                  "#### Blocked Actions Mid-Run", "#### Append Contract"),
                 ("codex-skills/speckit-autopilot/references/phase-execution-codex.md",
                  "### Blocked Actions Mid-Run", "## PR Packet and Body Boundary"))
        for relative, start, end in pairs:
            with self.subTest(host=relative):
                text = self.flat(relative)
                section = text.split(start, 1)[1]
                section = section.split(end, 1)[0] if end else section
                self.assertIn("`disposition=defer`", section)
                self.assertIn("end-of-run", section)
                self.assertIn("`authorize-corrective-exception`", section)
                self.assertIn("never a mid-run question", section)
                for stale in ("checkpoint with the exact gate output", "On exhaustion, checkpoint",
                              "checkpoint with exact output on exhaustion", "including an exhausted repair budget",
                              "When the repair budget is exhausted and the fix needs operator approval"):
                    self.assertNotIn(stale, section)

    def test_both_hosts_list_only_unresolved_deferrals_at_the_end(self):
        shared = self.flat("skills/speckit-autopilot/references/execution-efficiency.md")
        for phrase in ("`resolved_by`", "`resolved_at`", "keeps the entry for audit",
                       "No request can name a resolution", "`finalize-run` omits resolved entries"):
            self.assertIn(phrase, shared)
        for relative in ("skills/speckit-autopilot/references/phase-execution.md",
                         "codex-skills/speckit-autopilot/references/phase-execution-codex.md"):
            with self.subTest(host=relative):
                text = self.flat(relative)
                self.assertIn("lists it under \"Decisions for you\"", text)
                self.assertIn("unresolved ledger deferral first climbs the escalation tiers in rule 3", text)
                self.assertNotIn("the ledger's `deferred` list is not empty", text)

    def test_a_serial_plan_never_stops_mid_run_on_a_deferral(self):
        shared = self.flat("skills/speckit-autopilot/references/execution-efficiency.md")
        self.assertIn("a serial plan never stops mid-run on a deferral", shared)
        self.assertIn("tracked follow-up", shared)
        for relative, start, end in (
                ("skills/speckit-autopilot/references/phase-execution.md",
                 "#### Blocked Actions Mid-Run", "#### Repeated Gate Failures"),
                ("codex-skills/speckit-autopilot/references/phase-execution-codex.md",
                 "### Blocked Actions Mid-Run", "### Repeated Gate Failures")):
            with self.subTest(host=relative):
                text = self.flat(relative)
                section = text.split(start, 1)[1].split(end, 1)[0]
                for phrase in ("a serial plan never stops mid-run on a deferral", "`finalize-run`",
                               "the only stop is a required gate that is still not green"):
                    self.assertIn(phrase, section)
                review = text.split("**Review fixes inside one increment.**", 1)[1].split("\n\n", 1)[0]
                review = " ".join(review.split())
                for phrase in ("tracked follow-up", "its dependents stay runnable", "never a new task line",
                               "`ownership_evidence_stale`", "defer that increment", "never a mid-run question"):
                    self.assertIn(phrase, review)
                self.assertNotIn("keep its dependents deferred", review)

    def test_codex_audit_and_both_hosts_keep_the_true_stops(self):
        audit = self.flat("codex-skills/speckit-autopilot/SKILL.md").split("### 3.4 Pre-final completion audit", 1)[1]
        self.assertIn("`execution_control.disposition=defer`", audit)
        for relative, start, end in (
                ("skills/speckit-autopilot/references/phase-execution.md",
                 "#### Blocked Actions Mid-Run", "#### Repeated Gate Failures"),
                ("codex-skills/speckit-autopilot/references/phase-execution-codex.md",
                 "### Blocked Actions Mid-Run", "### Repeated Gate Failures")):
            with self.subTest(host=relative):
                section = self.flat(relative).split(start, 1)[1].split(end, 1)[0]
                for phrase in ("unknown side effects", "`checkpoint_required`", "a ledger or clock error",
                               "invalid or stale state"):
                    self.assertIn(phrase, section)


def unittest_output(*failing, ran=6):
    """Default (non-verbose) unittest output naming each failing test."""
    blocks = [f"FAIL: {name} (tests.test_sample.SampleTests.{name})\n" + "-" * 70 + "\nAssertionError\n"
              for name in failing]
    return ("=" * 70 + "\n").join(["", *blocks]) + "-" * 70 + f"\nRan {ran} tests in 0.010s\n\nFAILED (failures={len(failing)})\n"


def bun_output(failing, passing):
    """bun test output, which names every passing and failing test."""
    lines = [f"(pass) sample > {name} [0.10ms]" for name in passing]
    lines += [f"(fail) sample > {name} [0.20ms]" for name in failing]
    lines += ["", f" {len(passing)} pass", f" {len(failing)} fail",
              f"Ran {len(passing) + len(failing)} tests across 1 files. [5.00ms]"]
    return "tests/sample.test.ts:\n" + "\n".join(lines) + "\n"


class EscalationAllowanceTests(_ExecutionControlFixture, unittest.TestCase):
    """A failed unit climbs tier 2 then tier 3 outside the corrective budget before it is exhausted (issue 829)."""

    def setUp(self):
        super().setUp()
        self.invoke("start")
        self.invoke("reserve", dispatch_id="fix-a", kind="corrective", failure_invariant="FR-001")
        self.invoke("complete", dispatch_id="fix-a", outcome="completed")
        self.deferred = self.invoke("reserve", dispatch_id="fix-a-again", kind="corrective", failure_invariant="FR-001")
        self.assertEqual(self.deferred["disposition"], "defer")
        self.family = {"unit_kind": "failure_family", "unit": "FR-001"}

    def escalate(self, dispatch_id, tier, unit=None, **inputs):
        self.now += 10
        return self.invoke("reserve", dispatch_id=dispatch_id, kind="corrective",
                           escalation={**(unit or self.family), "tier": tier}, **inputs)

    def settle(self, dispatch_id, outcome="failed"):
        self.now += 10
        return self.invoke("complete", dispatch_id=dispatch_id, outcome=outcome)

    def verify_red(self, argv):
        """A failing verification of one command, fingerprinted by the runner; returns the command digest."""
        self.verify(unittest_output("test_a"), argv=argv)
        return digest(list(argv))

    def test_a_deferred_unit_gets_tier_two_outside_the_corrective_budget_and_records_its_tier(self):
        admitted = self.escalate("tier-2", 2)
        self.assertEqual((admitted["disposition"], admitted["escalation_allowance"]), ("continue", "unit"))
        ledger = admitted["ledger"]
        self.assertEqual(ledger["corrective_cycles"], 1)
        self.assertEqual((ledger["dispatches"]["tier-2"]["escalation"], ledger["dispatches"]["tier-2"]["escalation_tier"]),
                         ("failure_family:FR-001", 2))
        record = ledger["escalation_allowances"]["failure_family:FR-001"]
        self.assertEqual((record["tier"], [entry["dispatch_id"] for entry in record["dispatches"]]), (2, ["tier-2"]))
        self.assertEqual(ledger["escalation_tier3_cap"], 3)
        self.assert_schema_valid(ledger)
        spent = self.escalate("tier-2-again", 2)
        self.assertEqual((spent["disposition"], spent["reasons"]), ("checkpoint_required", ["escalation_allowance_spent"]))
        self.assertNotIn("tier-2-again", spent["ledger"]["dispatches"])

    def test_tier_three_follows_a_failed_tier_two_and_records_the_tier_reached(self):
        skipped = self.escalate("tier-3-early", 3)
        self.assertEqual(skipped["reasons"], ["escalation_tier_out_of_order"])
        self.escalate("tier-2", 2)
        running = self.escalate("tier-3-running", 3)
        self.assertEqual(running["reasons"], ["escalation_tier_out_of_order"])
        self.settle("tier-2")
        admitted = self.escalate("tier-3", 3)
        self.assertEqual(admitted["disposition"], "continue")
        record = admitted["ledger"]["escalation_allowances"]["failure_family:FR-001"]
        self.assertEqual((record["tier"], [entry["tier"] for entry in record["dispatches"]]), (3, [2, 3]))
        self.assert_schema_valid(admitted["ledger"])
        self.assertEqual(self.escalate("tier-3-again", 3)["reasons"], ["escalation_allowance_spent"])
        self.assertEqual(self.invoke("status", mode="read_only")["ledger"]["corrective_cycles"], 1)

    def test_a_completed_tier_resolves_the_deferral_and_a_failed_one_does_not(self):
        self.escalate("tier-2", 2)
        failed = self.settle("tier-2")
        self.assertNotIn("resolved_by", failed["ledger"]["deferred"][0])
        self.invoke("reserve", dispatch_id="fix-b", kind="corrective", failure_invariant="FR-002")
        self.invoke("reserve", dispatch_id="fix-b-again", kind="corrective", failure_invariant="FR-002")
        other = {"unit_kind": "failure_family", "unit": "FR-002"}
        self.escalate("other-tier-2", 2, other)
        done = self.settle("other-tier-2", "completed")
        self.assertEqual(done["ledger"]["deferred"][1]["resolved_by"], "other-tier-2")
        self.assertNotIn("resolved_by", done["ledger"]["deferred"][0])
        self.assertEqual(self.escalate("other-tier-3", 3, other)["reasons"], ["escalation_requires_a_failed_unit"])
        self.assert_schema_valid(done["ledger"])

    def test_tier_three_has_a_per_run_cap_the_runner_enforces(self):
        digests = [self.verify_red(("python3", f"gate-{number}.py")) for number in range(4)]
        for number, digest_value in enumerate(digests[:3]):
            unit = {"unit_kind": "gate_failure", "unit": digest_value}
            self.assertEqual(self.escalate(f"g{number}-tier-2", 2, unit)["disposition"], "continue")
            self.settle(f"g{number}-tier-2")
            self.verify_red(("python3", f"gate-{number}.py"))
            self.assertEqual(self.escalate(f"g{number}-tier-3", 3, unit)["disposition"], "continue")
            self.settle(f"g{number}-tier-3")
        last = {"unit_kind": "gate_failure", "unit": digests[3]}
        self.escalate("g3-tier-2", 2, last)
        self.settle("g3-tier-2")
        self.verify_red(("python3", "gate-3.py"))
        capped = self.escalate("g3-tier-3", 3, last)
        self.assertEqual((capped["disposition"], capped["reasons"]), ("checkpoint_required", ["escalation_tier3_cap_reached"]))
        from speckit_pro_runner.execution_control import escalation_progress, escalation_tier3_used

        ledger = self.invoke("status", mode="read_only")["ledger"]
        self.assertEqual(escalation_tier3_used(ledger), 3)
        self.assertEqual(escalation_progress(ledger, "gate_failure", digests[3]), "exhausted")
        self.assertEqual(escalation_progress(ledger, "gate_failure", digests[0]), "exhausted")
        self.assertEqual(escalation_progress(ledger, "failure_family", "FR-001"), "tier2")

    def test_a_gate_failure_needs_a_fresh_red_run_after_each_tier(self):
        digest_value = self.verify_red(("python3", "gate.py"))
        unit = {"unit_kind": "gate_failure", "unit": digest_value}
        self.escalate("tier-2", 2, unit)
        self.settle("tier-2", "completed")
        stale = self.escalate("tier-3", 3, unit)
        self.assertEqual(stale["reasons"], ["escalation_requires_a_failed_unit"])
        self.verify_red(("python3", "gate.py"))
        self.assertEqual(self.escalate("tier-3", 3, unit)["disposition"], "continue")

    def test_an_escalation_needs_a_failed_unit_and_a_well_formed_request(self):
        refused = self.escalate("tier-x", 2, {"unit_kind": "increment", "unit": "alpha"})
        self.assertEqual(refused["reasons"], ["escalation_requires_a_failed_unit"])
        self.assertNotIn("escalation_allowances", refused["ledger"])
        passing = self.verify_red(("python3", "gate.py"))
        self.assertEqual(self.escalate("tier-y", 2, {"unit_kind": "gate_failure", "unit": "0" * 64})["reasons"],
                         ["escalation_requires_a_failed_unit"])
        self.assertNotEqual(passing, "0" * 64)
        for name, request in {"unknown kind": {"unit_kind": "gate_zero", "unit": "FR-001", "tier": 2},
                              "extra key": {**self.family, "tier": 2, "approved": True},
                              "no tier": dict(self.family), "tier one": {**self.family, "tier": 1},
                              "tier four": {**self.family, "tier": 4}, "tier as text": {**self.family, "tier": "2"},
                              "blank unit": {"unit_kind": "failure_family", "unit": " ", "tier": 2},
                              "not an object": "FR-001"}.items():
            with self.subTest(request=name), self.assertRaises(ValueError):
                self.invoke("reserve", dispatch_id="escalate-y", kind="corrective", escalation=request)
        with self.assertRaises(ValueError):
            self.invoke("reserve", dispatch_id="escalate-z", kind="implementation", escalation={**self.family, "tier": 2})
        reservation = next(iter(self.deferred["ledger"]["reservations"]))
        with self.assertRaises(ValueError):
            self.escalate("escalate-w", 2, reservation_id=reservation)

    def test_a_ledger_without_escalation_records_still_validates(self):
        from speckit_pro_runner.execution_control import escalation_progress, validate_ledger

        ledger = self.deferred["ledger"]
        for key in ("escalation_allowances", "escalation_tier3_cap", "finalize_observations"):
            self.assertNotIn(key, ledger)
        validate_ledger(ledger)
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")
        self.assertEqual(escalation_progress(ledger, "failure_family", "FR-001"), "tier2")

    def test_forged_escalation_records_fail_closed(self):
        self.escalate("tier-2", 2)
        self.settle("tier-2")
        admitted = self.escalate("tier-3", 3)
        path = self.root / admitted["ledger_path"]
        valid = path.read_bytes()
        key = "failure_family:FR-001"
        tampers = {
            "allowance for a unit that never failed": lambda ledger: ledger["escalation_allowances"].update(
                {"increment:alpha": {**ledger["escalation_allowances"][key], "unit_kind": "increment", "unit": "alpha"}}),
            "dispatch marker without an allowance": lambda ledger: ledger.pop("escalation_allowances"),
            "allowance names another dispatch": lambda ledger: ledger["escalation_allowances"][key]["dispatches"][
                1].update(dispatch_id="fix-a"),
            "allowance key disagrees with its unit": lambda ledger: ledger["escalation_allowances"].update(
                {"failure_family:FR-002": ledger["escalation_allowances"].pop(key)}),
            "unknown unit kind": lambda ledger: ledger["escalation_allowances"][key].update(unit_kind="merge"),
            "extra key": lambda ledger: ledger["escalation_allowances"][key].update(approved=True),
            "tier disagrees with its dispatches": lambda ledger: ledger["escalation_allowances"][key].update(tier=2),
            "tier three with no tier two": lambda ledger: ledger["escalation_allowances"][key].update(
                dispatches=ledger["escalation_allowances"][key]["dispatches"][1:]),
            "tier three before tier two settled": lambda ledger: ledger["dispatches"]["tier-2"].update(
                outcome="running"),
            "tier three after a completed tier two": lambda ledger: ledger["dispatches"]["tier-2"].update(
                outcome="completed"),
            "dispatch tier rewritten": lambda ledger: ledger["dispatches"]["tier-3"].update(escalation_tier=2),
            "reserved_at disagrees": lambda ledger: ledger["escalation_allowances"][key]["dispatches"][0].update(
                reserved_at=1.0),
            "cap missing": lambda ledger: ledger.pop("escalation_tier3_cap"),
            "cap raised": lambda ledger: ledger.update(escalation_tier3_cap=99),
            "escalation on a corrective reservation": lambda ledger: ledger["dispatches"]["tier-3"].update(
                reservation_id=next(iter(ledger["reservations"]))),
            "escalation on an implementation dispatch": lambda ledger: ledger["dispatches"]["tier-3"].update(
                kind="implementation"),
            "escalation and an increment allowance": lambda ledger: ledger["dispatches"]["tier-3"].update(
                increment="alpha"),
            "empty allowance map": lambda ledger: ledger.update(escalation_allowances={}),
            "deferral removed": lambda ledger: ledger.pop("deferred"),
        }
        for name, tamper in tampers.items():
            with self.subTest(tamper=name):
                ledger = json.loads(valid)
                tamper(ledger)
                path.write_text(json.dumps(ledger), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.invoke("status", mode="read_only")
        path.write_bytes(valid)
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")

    def test_a_new_epoch_archives_the_escalation_records_and_the_cap_still_counts_them(self):
        from speckit_pro_runner.execution_control import escalation_tier3_used

        spec = self.root / "feature/spec.md"
        self.escalate("tier-2", 2)
        self.settle("tier-2")
        self.escalate("tier-3", 3)
        self.settle("tier-3")
        event = {"native_event_id": "operator-replan", "run_id": self.run_id, "action": "replan_epoch_approved",
                 "spec_sha256": hashlib.sha256(spec.read_bytes()).hexdigest()}
        opened = self.invoke("begin-replan-epoch", spec_file="feature/spec.md", native_observation=event)
        self.assertNotIn("escalation_allowances", opened["ledger"])
        self.assertEqual(opened["ledger"]["corrective_epochs"][0]["escalation_allowances"]["failure_family:FR-001"]["tier"], 3)
        self.assertEqual(escalation_tier3_used(opened["ledger"]), 1)
        self.assert_schema_valid(opened["ledger"])

    def test_forged_finalize_observations_fail_closed(self):
        from speckit_pro_runner.execution_control import FINALIZE_OBSERVATION_CAP, finalize_observation_key, validate_ledger

        key = finalize_observation_key("missing_gate", "a" * 40, "G7")
        valid = self.deferred["ledger"]
        validate_ledger({**valid, "finalize_observations": {key: FINALIZE_OBSERVATION_CAP}})
        self.assert_schema_valid({**valid, "finalize_observations": {key: FINALIZE_OBSERVATION_CAP}})
        for name, forged in {"bad kind": {f"stop:{'a' * 40}:G7": 1}, "short head": {"missing_gate:abc:G7": 1},
                             "no gate": {f"missing_gate:{'a' * 40}:": 1}, "over the cap": {key: FINALIZE_OBSERVATION_CAP + 1},
                             "zero": {key: 0}, "boolean count": {key: True}, "empty": {}}.items():
            with self.subTest(forged=name), self.assertRaises(ValueError):
                validate_ledger({**valid, "finalize_observations": forged})
        with self.assertRaises(ValueError):
            self.invoke("record-finalize-cycle", finalize_inputs={"ledger_path": "elsewhere.json"})


FAILING_CHECK_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "failing-checks"


def runner_output(name):
    """Real test-runner output captured from the tool itself (see the fixture directory)."""
    return (FAILING_CHECK_FIXTURES / name).read_text(encoding="utf-8")


class FailingCheckFingerprintTests(unittest.TestCase):
    """The runner derives a failing-check set from the output it executed, from a closed set of formats."""

    def fingerprint(self, stdout="", stderr="", exit_code=1, completed=True):
        return failing_check_fingerprint("UNIT_TEST", ["python3", "-m", "unittest"], exit_code, completed,
                                         stdout.encode(), stderr.encode())

    def test_each_supported_format_yields_a_sorted_failing_set(self):
        unittest_text = unittest_output("test_b", "test_a")
        pytest_text = ("============ short test summary info ============\n"
                       + "FAILED tests/test_x.py::test_b - assert 1 == 2\n"
                       + "ERROR tests/test_y.py::test_c\n"
                       + "======== 2 failed, 3 passed in 0.12s ========\n")
        jest_text = ("  ● math › adds\n\n    expect(received)\n\n  ● math › subtracts\n\n"
                     + "Tests:       2 failed, 4 passed, 6 total\n")
        cases = {
            "unittest": (unittest_text, "", ["test_a (tests.test_sample.SampleTests.test_a)",
                                             "test_b (tests.test_sample.SampleTests.test_b)"], None, 6),
            "pytest": ("", pytest_text, ["tests/test_x.py::test_b", "tests/test_y.py::test_c"], None, 5),
            "bun": (bun_output(["b"], ["a"]), "", ["sample > b"], ["sample > a"], 2),
            "jest": ("", jest_text, ["math › adds", "math › subtracts"], None, 6),
        }
        for name, (stdout, stderr, failing, passing, checks_run) in cases.items():
            with self.subTest(format=name):
                result = self.fingerprint(stdout, stderr)
                self.assertEqual((result["format"], result["failing"], result["passing"], result["checks_run"]),
                                 (name, failing, passing, checks_run))
                self.assertEqual(result["command_id"], "UNIT_TEST")
                self.assertEqual(result["command_sha256"], digest(["python3", "-m", "unittest"]))
                self.assertRegex(result["output_sha256"], r"^[0-9a-f]{64}$")
        verbose = "test_a (tests.T.test_a) ... ok\ntest_b (tests.T.test_b) ... FAIL\n" + unittest_output("test_b")
        self.assertEqual(self.fingerprint(stderr=verbose)["passing"], ["test_a (tests.T.test_a)"])

    def test_unparseable_ambiguous_or_unfinished_output_records_no_failing_set(self):
        cases = {"no known format": self.fingerprint("Segmentation fault\n", exit_code=139),
                 "nonzero exit without a named failure": self.fingerprint("Ran 3 tests in 0.1s\n\nOK\n"),
                 "two formats at once": self.fingerprint(unittest_output("test_a") + bun_output(["b"], [])),
                 "timed out": self.fingerprint(unittest_output("test_a"), exit_code=None, completed=False)}
        for name, result in cases.items():
            with self.subTest(case=name):
                self.assertIsNone(result["failing"])
                self.assertEqual(result["format"], "unparsed")
                self.assertRegex(result["output_sha256"], r"^[0-9a-f]{64}$")
        passed = self.fingerprint("Ran 3 tests in 0.1s\n\nOK\n", exit_code=0)
        self.assertEqual(passed["failing"], [])
        unknown_pass = self.fingerprint("all good\n", exit_code=0)
        self.assertEqual((unknown_pass["format"], unknown_pass["failing"], unknown_pass["checks_run"]),
                         ("passed", [], None))


class MoreTestRunnerFingerprintTests(unittest.TestCase):
    """go test, cargo test, vitest, mocha, and JUnit XML parse from output the tools really produced."""

    fingerprint = FailingCheckFingerprintTests.fingerprint

    CASES = {
        "go-test-v.txt": ("go", ["TestGroup", "TestGroup/inner_bad", "TestSub"], ["TestAdd", "TestGroup/inner_ok"], 5),
        "go-test.txt": ("go", ["TestGroup", "TestGroup/inner_bad", "TestSub"], None, None),
        "cargo-test.txt": ("cargo", ["tests::nested_path_bad", "tests::subs"], ["tests::adds"], 3),
        "vitest.txt": ("vitest", ["math.test.js > math > subtracts", "math.test.js > strings > upper"], None, 3),
        "mocha.txt": ("mocha", ["math nested upper", "math subtracts"], None, 3),
        "junit-vitest.xml": ("junit", ["math.test.js.math > subtracts", "math.test.js.strings > upper"],
                             ["math.test.js.math > adds"], 3),
        "junit-mocha.xml": ("junit", ["math nested.upper", "math.subtracts"], ["math.adds"], 3),
    }

    def test_each_new_format_yields_a_sorted_failing_set(self):
        for name, (fmt, failing, passing, checks_run) in self.CASES.items():
            with self.subTest(fixture=name):
                result = self.fingerprint(runner_output(name))
                self.assertEqual((result["format"], result["failing"], result["passing"], result["checks_run"]),
                                 (fmt, failing, passing, checks_run))

    def test_stderr_carries_the_same_output(self):
        for name in ("go-test-v.txt", "cargo-test.txt", "mocha.txt"):
            with self.subTest(fixture=name):
                self.assertEqual(self.fingerprint(stderr=runner_output(name))["failing"],
                                 self.fingerprint(runner_output(name))["failing"])

    def test_a_passing_run_in_a_new_format_records_an_empty_set_and_its_count(self):
        cases = {"go": ("=== RUN   TestAdd\n--- PASS: TestAdd (0.00s)\n=== RUN   TestSub\n--- PASS: TestSub (0.00s)\nPASS\n"
                        "ok  \texample.test/demo\t0.1s\n", 2),
                 "cargo": ("test a ... ok\ntest b ... ok\n\ntest result: ok. 2 passed; 0 failed; 1 ignored; "
                           "0 measured; 0 filtered out; finished in 0.00s\n", 3),
                 "vitest": (" Test Files  1 passed (1)\n      Tests  4 passed (4)\n", 4),
                 "mocha": ("  3 passing (5ms)\n  1 pending\n", 4),
                 "junit": ('<testsuite tests="2"><testcase classname="a" name="b"/><testcase classname="a" name="c"/>'
                           "</testsuite>\n", 2)}
        for fmt, (text, checks_run) in cases.items():
            with self.subTest(format=fmt):
                result = self.fingerprint(text, exit_code=0)
                self.assertEqual((result["format"], result["failing"], result["checks_run"]), (fmt, [], checks_run))

    def test_new_format_output_that_cannot_be_trusted_records_no_failing_set(self):
        junit = runner_output("junit-vitest.xml")
        cases = {"two formats at once": runner_output("go-test-v.txt") + runner_output("cargo-test.txt"),
                 "junit and a text format": junit + runner_output("mocha.txt"),
                 "truncated xml": junit[:junit.index("</testsuite>")],
                 "entity declaration": '<!DOCTYPE x [<!ENTITY a "b">]>' + junit,
                 "junit that names no failure": '<testsuite tests="1"><testcase classname="a" name="b"/></testsuite>',
                 "go build failure": "FAIL\texample.test/demo [build failed]\nFAIL\n",
                 "cargo compile error": "error[E0425]: cannot find value\n\nerror: could not compile `demo`\n"}
        for name, text in cases.items():
            with self.subTest(case=name):
                result = self.fingerprint(text)
                self.assertEqual((result["format"], result["failing"]), ("unparsed", None))

    def test_the_ledger_accepts_each_new_format_and_older_ledgers_still_validate(self):
        schema = json.loads(SCHEMA_PATH.read_text())
        formats = schema["properties"]["dispatches"]["additionalProperties"]["properties"]["failing_checks"][
            "properties"]["format"]["enum"]
        self.assertEqual(formats[:4] + formats[-2:], ["unittest", "pytest", "bun", "jest", "passed", "unparsed"])
        self.assertEqual({"go", "cargo", "vitest", "mocha", "junit"}, set(formats) - {
            "unittest", "pytest", "bun", "jest", "passed", "unparsed"})


class _CorrectionProgressFixture(_ExecutionControlFixture):

    def setUp(self):
        super().setUp()
        self.invoke("start")
        self.verifications = 0

    def correct(self, dispatch_id, invariant="FR-001", outcome="completed", **inputs):
        self.now += 10
        result = self.invoke("reserve", dispatch_id=dispatch_id, kind="corrective", failure_invariant=invariant, **inputs)
        if result["disposition"] == "continue" and outcome is not None:
            self.now += 10
            self.invoke("complete", dispatch_id=dispatch_id, outcome=outcome)
        return result


class CorrectionProgressTests(_CorrectionProgressFixture, unittest.TestCase):
    """A correction that measurably converged admits the next one with no operator event (issue 796)."""

    def assert_deferred_for(self, result, reason):
        self.assertEqual(result["disposition"], "defer")
        self.assertEqual(result["reasons"], ["failure_family_budget_exhausted"])
        self.assertEqual(result["progress"], {"admitted": False, "reason": reason})
        self.assertNotIn(result["deferred"]["dispatch_id"], result["ledger"]["dispatches"])

    def test_three_successive_shrinking_corrections_are_admitted_with_no_operator_event(self):
        first_state = self.verify(unittest_output("test_a", "test_b", "test_c", "test_d"))
        owner = self.correct("fix-1")
        self.assertEqual(owner["disposition"], "continue")
        self.assertEqual(owner["ledger"]["dispatches"]["fix-1"]["baseline"], first_state)
        previous = "fix-1"
        for number, failing in enumerate((("test_a", "test_b", "test_c"), ("test_a", "test_b"), ("test_a",)), 2):
            state = self.verify(unittest_output(*failing))
            admitted = self.correct(f"fix-{number}")
            with self.subTest(correction=number):
                self.assertEqual(admitted["disposition"], "continue", admitted["reasons"])
                self.assertEqual(admitted["reservation_id"], owner["reservation_id"])
                self.assertEqual(admitted["progress"], {"admitted": True, "change": "shrank",
                                                        "previous_dispatch_id": previous, "baseline": state})
                record = admitted["ledger"]["dispatches"][f"fix-{number}"]
                self.assertEqual((record["progress_of"], record["baseline"]), (previous, state))
                self.assertEqual(admitted["ledger"]["corrective_cycles"], 1)
                self.assertNotIn("corrective_exception", admitted["ledger"])
                self.assertNotIn("deferred", admitted["ledger"])
            previous = f"fix-{number}"
        on_disk = json.loads((self.root / admitted["ledger_path"]).read_text())
        self.assert_schema_valid(on_disk)
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")
        other = self.correct("fix-other", invariant="FR-002")
        self.assertEqual(other["disposition"], "continue")

    def test_a_correction_that_leaves_the_failing_set_unchanged_or_larger_defers(self):
        self.verify(unittest_output("test_a", "test_b"))
        self.correct("fix-1")
        self.verify(unittest_output("test_a", "test_b"))
        self.assert_deferred_for(self.correct("fix-2"), "no_progress")
        self.verify(unittest_output("test_a", "test_b", "test_c"))
        self.assert_deferred_for(self.correct("fix-3"), "no_progress")
        self.verify(unittest_output("test_c"))
        self.assert_deferred_for(self.correct("fix-4"), "no_progress")

    def test_a_return_to_an_earlier_failing_state_defers(self):
        self.verify(bun_output(["a"], ["b", "c"]))
        self.correct("fix-1")
        self.verify(bun_output(["b"], ["a", "c"]))
        moved = self.correct("fix-2")
        self.assertEqual(moved["disposition"], "continue", moved["reasons"])
        self.assertEqual(moved["progress"]["change"], "moved")
        self.verify(bun_output(["a"], ["b", "c"]))
        self.assert_deferred_for(self.correct("fix-3"), "returned_to_earlier_state")

    def test_a_scope_changing_correction_is_refused_even_when_it_made_progress(self):
        self.verify(unittest_output("test_a", "test_b"))
        self.correct("fix-1")
        spec = self.root / "feature/spec.md"
        (self.root / "feature/unchanged-copy.md").write_bytes(spec.read_bytes())
        spec.write_text(spec.read_text() + "- FR-003: accept any output\n")
        self.verify(unittest_output("test_a"))
        self.assert_deferred_for(self.correct("fix-2"), "spec_changed")
        self.assert_deferred_for(self.correct("fix-2b", spec_file="feature/unchanged-copy.md"), "spec_changed")
        self.verify(unittest_output("test_x", "test_y"))
        self.correct("fix-u1", invariant="words that name no requirement")
        self.verify(unittest_output("test_x"))
        # The shrunk set is a different untagged family, so only the run-wide cap refuses it; no progress path applies.
        shrunk = self.correct("fix-u2", invariant="other words")
        self.assertEqual((shrunk["disposition"], shrunk["reasons"]), ("defer", ["corrective_run_budget_exhausted"]))
        self.assertNotIn("progress", shrunk)
        self.assertNotIn("fix-u2", shrunk["ledger"]["dispatches"])

    def test_a_narrowed_command_or_a_removed_check_is_not_progress(self):
        self.verify(unittest_output("test_a", "test_b"))
        self.correct("fix-1")
        self.verify(unittest_output("test_a"), argv=("python3", "-m", "unittest", "tests.test_sample.SampleTests.test_a"))
        self.assert_deferred_for(self.correct("fix-2"), "command_changed")
        self.verify(unittest_output("test_x", "test_y"))
        self.correct("fix-3", invariant="FR-002")
        self.verify(unittest_output("test_x", ran=5))
        self.assert_deferred_for(self.correct("fix-4", invariant="FR-002"), "fewer_checks_ran")

    def test_a_failed_correction_or_a_missing_after_state_never_counts_as_progress(self):
        self.verify(unittest_output("test_a", "test_b"))
        self.correct("fix-1", outcome="failed")
        self.verify(unittest_output("test_a"))
        self.assert_deferred_for(self.correct("fix-2"), "previous_correction_unsettled")
        self.verify(unittest_output("test_x", "test_y"))
        self.correct("fix-3", invariant="FR-002")
        self.assert_deferred_for(self.correct("fix-4", invariant="FR-002"), "no_new_evidence")

    def test_a_failed_nested_correction_under_the_first_one_blocks_progress(self):
        self.verify(unittest_output("test_a", "test_b"))
        reservation = self.correct("fix-1", outcome=None)["reservation_id"]
        self.now += 10
        self.invoke("reserve", dispatch_id="nested-1", kind="corrective", reservation_id=reservation)
        self.invoke("complete", dispatch_id="nested-1", outcome="failed")
        self.invoke("complete", dispatch_id="fix-1", outcome="completed")
        self.verify(unittest_output("test_a"))
        self.assert_deferred_for(self.correct("fix-2"), "previous_correction_unsettled")

    def test_disjoint_failures_need_every_prior_failure_named_as_passing(self):
        self.verify(unittest_output("test_a"))
        self.correct("fix-1")
        self.verify(unittest_output("test_b"))
        self.assert_deferred_for(self.correct("fix-2"), "no_progress")

    def test_unparseable_output_falls_back_to_the_caps(self):
        self.correct("fix-0", invariant="FR-002")
        self.verify(unittest_output("test_a", "test_b"))
        self.correct("fix-1")
        self.verify("Segmentation fault\n", exit_code=139)
        self.assert_deferred_for(self.correct("fix-2"), "evidence_unparsed")
        self.verify(unittest_output("test_a"), exit_code=None, completed=False)
        self.assert_deferred_for(self.correct("fix-3"), "evidence_unparsed")
        fresh = self.correct("fix-4", invariant="FR-009-not-approved")
        self.assertEqual((fresh["disposition"], fresh["reasons"]), ("defer", ["corrective_run_budget_exhausted"]))
        self.assertNotIn("progress", fresh)

    def test_tampered_progress_history_fails_validation(self):
        self.verify(unittest_output("test_a", "test_b", "test_c"))
        self.correct("fix-1")
        self.verify(unittest_output("test_a", "test_b"))
        self.correct("fix-2")
        self.verify(unittest_output("test_a"))
        admitted = self.correct("fix-3")
        self.assertEqual(admitted["disposition"], "continue", admitted["reasons"])
        path = self.root / admitted["ledger_path"]
        valid = path.read_bytes()

        def dispatches(ledger):
            return ledger["dispatches"]

        tampers = {
            "after state no longer shrank": lambda ledger: dispatches(ledger)["verify-2"]["failing_checks"].update(
                failing=["test_a (tests.test_sample.SampleTests.test_a)", "test_z (tests.test_sample.SampleTests.test_z)",
                         "test_zz (tests.test_sample.SampleTests.test_zz)", "test_zzz (tests.test_sample.SampleTests.test_zzz)"]),
            "baseline repointed": lambda ledger: dispatches(ledger)["fix-3"].update(baseline="verify-2"),
            "baseline shared": lambda ledger: dispatches(ledger)["fix-2"].update(baseline="verify-3"),
            "chain forked": lambda ledger: dispatches(ledger)["fix-3"].update(progress_of="fix-1"),
            "unknown previous": lambda ledger: dispatches(ledger)["fix-3"].update(progress_of="fix-9"),
            "previous failed": lambda ledger: dispatches(ledger)["fix-2"].update(outcome="failed"),
            "evidence removed": lambda ledger: dispatches(ledger)["verify-3"].pop("failing_checks"),
            "evidence unparsed": lambda ledger: dispatches(ledger)["verify-3"]["failing_checks"].update(
                failing=None, format="unparsed"),
            "evidence on a correction": lambda ledger: dispatches(ledger)["fix-1"].update(
                failing_checks=dict(dispatches(ledger)["verify-1"]["failing_checks"])),
            "unsorted failing set": lambda ledger: dispatches(ledger)["verify-1"]["failing_checks"]["failing"].reverse(),
            "evidence recorded before its dispatch": lambda ledger: dispatches(ledger)["verify-3"]["failing_checks"].update(
                recorded_at=0),
            "other command": lambda ledger: dispatches(ledger)["verify-3"]["failing_checks"].update(command_id="LINT"),
            "other argv": lambda ledger: dispatches(ledger)["verify-3"]["failing_checks"].update(command_sha256="1" * 64),
            "fewer checks ran": lambda ledger: dispatches(ledger)["verify-3"]["failing_checks"].update(checks_run=1),
            "spec digest changed mid-chain": lambda ledger: dispatches(ledger)["fix-3"].update(spec_sha256="0" * 64),
            "progress without a reservation": lambda ledger: dispatches(ledger)["fix-3"].update(reservation_id=None),
            "baseline on a nested correction": lambda ledger: dispatches(ledger)["fix-3"].pop("progress_of"),
            "baseline names no dispatch": lambda ledger: dispatches(ledger)["fix-1"].update(baseline="verify-9"),
            "owner baseline removed": lambda ledger: [dispatches(ledger)["fix-1"].pop(key) for key in ("baseline", "spec_sha256")],
            "first evidence removed": lambda ledger: dispatches(ledger)["verify-1"].pop("failing_checks"),
            "spec path swapped": lambda ledger: dispatches(ledger)["fix-3"].update(spec_file="feature/other.md"),
            "failed nested correction": lambda ledger: dispatches(ledger).update({"nested-x": {
                "kind": "corrective", "outcome": "failed", "reserved_at": dispatches(ledger)["fix-1"]["reserved_at"] + 1,
                "reservation_id": dispatches(ledger)["fix-1"]["reservation_id"], "reconciliations": 0}}),
        }
        for name, tamper in tampers.items():
            for order in ("recorded", "reversed"):
                with self.subTest(tamper=name, order=order):
                    ledger = json.loads(valid)
                    tamper(ledger)
                    if order == "reversed":
                        ledger["dispatches"] = dict(reversed(list(ledger["dispatches"].items())))
                    path.write_text(json.dumps(ledger), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        self.invoke("status", mode="read_only")
        ledger = json.loads(valid)
        ledger["dispatches"] = dict(reversed(list(ledger["dispatches"].items())))
        path.write_text(json.dumps(ledger), encoding="utf-8")
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")
        path.write_bytes(valid)

    def test_evidence_can_only_come_from_the_runner(self):
        verification = self.verify(unittest_output("test_a"))
        with self.assertRaisesRegex(ValueError, "unsupported action"):
            self.invoke("record-failing-checks", dispatch_id=verification,
                        failing_checks={"command_id": "UNIT_TEST", "failing": []})
        with self.assertRaises(ValueError):
            record_failing_checks(self.root, {"workflow_file": "feature/workflow.md", "expected_run_id": self.run_id,
                                              "dispatch_id": verification},
                                  failing_check_fingerprint("UNIT_TEST", ["python3"], 0, True, b"", b""))
        self.invoke("reserve", dispatch_id="worker", kind="implementation")
        with self.assertRaises(ValueError):
            record_failing_checks(self.root, {"workflow_file": "feature/workflow.md", "expected_run_id": self.run_id,
                                              "dispatch_id": "worker"},
                                  failing_check_fingerprint("UNIT_TEST", ["python3"], 0, True, b"", b""))

    def test_a_stage_epoch_archives_the_progress_history(self):
        self.verify(unittest_output("test_a", "test_b"))
        self.correct("fix-1")
        self.verify(unittest_output("test_a"))
        self.assertEqual(self.correct("fix-2")["disposition"], "continue")
        (self.root / "feature/workflow.md").write_text(stage_workflow())
        opened = self.invoke("begin-stage-epoch", autopilot_args=["--stage", "implement"])
        self.assertTrue(opened["stage_epoch_opened"])
        archived = opened["ledger"]["corrective_epochs"][0]["dispatches"]
        self.assertEqual(archived["fix-2"]["progress_of"], "fix-1")
        self.assert_schema_valid(opened["ledger"])


class UntaggedFailureFamilyTests(_CorrectionProgressFixture, unittest.TestCase):
    """An untagged failure takes its family from the failing set the runner recorded, not one shared name."""

    def families(self, result):
        ledger = result["ledger"]
        return {ledger["reservations"][item["reservation_id"]]["family"]
                for item in ledger["dispatches"].values() if item.get("reservation_id") in ledger["reservations"]}

    def test_two_unrelated_untagged_failures_get_separate_families_and_reservations(self):
        self.verify(runner_output("go-test-v.txt"))
        first = self.correct("fix-go", invariant="words that name no requirement")
        self.assertEqual(first["disposition"], "continue")
        self.verify(runner_output("cargo-test.txt"))
        second = self.correct("fix-rust", invariant="other words")
        self.assertEqual(second["disposition"], "continue", second.get("reasons"))
        families = [record["family"] for record in second["ledger"]["reservations"].values()]
        self.assertEqual(len(set(families)), 2)
        self.assertNotIn("unresolved", families)
        self.assertEqual(second["ledger"]["corrective_cycles"], 2)
        self.assert_schema_valid(json.loads((self.root / second["ledger_path"]).read_text()))

    def test_the_same_untagged_failing_set_keeps_one_family_and_one_reservation(self):
        outcomes = []
        for attempt, words in enumerate(("words that name no requirement", "different words"), 1):
            self.verify(runner_output("cargo-test.txt"))
            outcomes.append(self.correct(f"fix-{attempt}", invariant=words))
        repeated = outcomes[-1]
        self.assertEqual((outcomes[0]["disposition"], repeated["disposition"], repeated["reasons"]),
                         ("continue", "defer", ["failure_family_budget_exhausted"]))
        self.assertRegex(repeated["deferred"]["unit"], r"^untagged-[0-9a-f]{16}$")
        self.assert_schema_valid(repeated["ledger"])
        self.assertNotIn("fix-2", repeated["ledger"]["dispatches"])

    def test_the_family_ignores_identifier_order_and_the_tagging_words(self):
        self.verify(unittest_output("test_a", "test_b"))
        first = self.correct("fix-1", invariant="words that name no requirement", outcome=None)
        (family,) = self.families(first)
        self.assertRegex(family, r"^untagged-[0-9a-f]{16}$")

    def test_an_untagged_failure_with_no_recorded_failing_set_keeps_the_shared_family(self):
        first = self.correct("fix-1", invariant="words that name no requirement")
        self.assertEqual(self.families(first), {"unresolved"})
        self.assert_schema_valid(first["ledger"])
        denied = self.correct("fix-2", invariant="other words")
        self.assertEqual(denied["reasons"], ["failure_family_budget_exhausted"])

    def test_an_approved_invariant_still_names_its_own_family(self):
        self.verify(runner_output("go-test-v.txt"))
        first = self.correct("fix-1", invariant="FR-001")
        self.assertEqual(self.families(first), {"FR-001"})


class CorrectionProgressGuidanceTests(unittest.TestCase):
    """Both hosts remediate while rounds converge; a deferral is the non-convergence fallback."""

    PLUGIN = Path(__file__).resolve().parents[3] / "speckit-pro"

    def flat(self, relative):
        return " ".join((self.PLUGIN / relative).read_text().split())

    def test_shared_ledger_reference_documents_the_progress_path(self):
        text = self.flat("skills/speckit-autopilot/references/execution-efficiency.md")
        self.assertIn("keep remediating while each round converges", text.lower())
        for phrase in ("`progress_of`", "`failing_checks`",
                       "strict subset", "no operator event", "`returned_to_earlier_state`", "`evidence_unparsed`",
                       "`spec_changed`", "non-convergence fallback", "unittest, pytest, bun, jest, go test, cargo test, vitest, mocha, and JUnit XML"):
            self.assertIn(phrase, text)

    def test_both_hosts_remediate_while_converging_and_defer_only_on_non_convergence(self):
        pairs = (("skills/speckit-autopilot/SKILL.md", "## Error Recovery", "## References"),
                 ("codex-skills/speckit-autopilot/SKILL.md", "### 3.4 Pre-final completion audit", None),
                 ("skills/speckit-autopilot/references/error-recovery.md", "## Common Issues", "## Context Window"),
                 ("codex-skills/speckit-autopilot/references/error-recovery-codex.md", "## Common Issues", None),
                 ("skills/speckit-autopilot/references/phase-execution.md",
                  "#### Blocked Actions Mid-Run", "#### Append Contract"),
                 ("codex-skills/speckit-autopilot/references/phase-execution-codex.md",
                  "### Blocked Actions Mid-Run", "## PR Packet and Body Boundary"))
        for relative, start, end in pairs:
            with self.subTest(host=relative):
                section = self.flat(relative).split(start, 1)[1]
                section = section.split(end, 1)[0] if end else section
                self.assertIn("keep remediating while each round converges", section.lower())
                self.assertIn("non-convergence", section.lower())
                self.assertIn("`disposition=defer`", section)


class GateRemediationAllowanceTests(_ExecutionControlFixture, unittest.TestCase):
    """A planning gate's documentation-only remediation draws on that gate's own bound."""

    PLANNING = ["feature/spec.md", "feature/plan.md", "feature/research.md", "feature/tasks.md"]

    def spend_run_wide_budget(self):
        IncrementReviewAllowanceTests.spend_run_wide_budget(self)

    def gate_fix(self, dispatch_id, gate, paths, mode="apply", **inputs):
        request = {"spec_file": "feature/spec.md", "failure_invariant": "FR-001", **inputs}
        return self.invoke("reserve", mode=mode, dispatch_id=dispatch_id, kind="corrective",
                           gate_remediation={"gate": gate, "paths": paths}, **request)

    def test_documentation_only_g6_remediation_is_admitted_after_run_wide_exhaustion_up_to_the_bound(self):
        self.spend_run_wide_budget()
        first = self.gate_fix("g6-fix-1", "G6", self.PLANNING)
        self.assertEqual((first["disposition"], first["remediation_allowance"]), ("continue", "gate"))
        self.assertIsNone(first["reservation_id"])
        self.assertEqual(first["ledger"]["corrective_cycles"], 2)
        self.assertNotIn("corrective_exception", first["ledger"])
        self.assertEqual(first["ledger"]["gate_allowances"]["G6"], {"rounds": 1, "dispatch_ids": ["g6-fix-1"]})
        self.assertEqual(first["ledger"]["dispatches"]["g6-fix-1"]["gate"], "G6")
        self.invoke("complete", dispatch_id="g6-fix-1", outcome="completed")
        second = self.gate_fix("g6-fix-2", "G6", ["feature/data-model.md", "feature/quickstart.md",
                                                  "feature/checklists/security.md",
                                                  "feature/.process/task-execution.json"])
        self.assertEqual((second["disposition"], second["remediation_allowance"]), ("continue", "gate"))
        self.invoke("complete", dispatch_id="g6-fix-2", outcome="failed")
        path = self.root / second["ledger_path"]
        before = path.read_bytes()
        spent = self.gate_fix("g6-fix-3", "G6", ["feature/spec.md"])
        self.assertEqual(spent["reasons"], ["gate_remediation_allowance_exhausted"])
        self.assertEqual(spent["disposition"], "defer")
        self.assertEqual({key: spent["deferred"][key] for key in ("dispatch_id", "unit_kind", "unit")},
                         {"dispatch_id": "g6-fix-3", "unit_kind": "gate", "unit": "G6"})
        self.assertNotIn("g6-fix-3", spent["ledger"]["dispatches"])
        self.assertEqual(json.loads(path.read_bytes())["gate_allowances"], json.loads(before)["gate_allowances"])
        self.assertEqual(json.loads(path.read_bytes())["corrective_cycles"], 2)
        self.assertEqual(self.gate_fix("g6-fix-1", "G4", ["feature/spec.md"])["reasons"],
                         ["dispatch_already_reserved_no_relaunch"])
        other_gate = self.gate_fix("g4-fix-1", "G4", ["feature/spec.md"])
        self.assertEqual((other_gate["disposition"], other_gate["remediation_allowance"]), ("continue", "gate"))
        self.assertEqual(other_gate["ledger"]["gate_allowances"]["G4"]["rounds"], 1)
        schema = json.loads((Path(__file__).resolve().parents[3] /
                             "speckit-pro/speckit_pro_runner/contracts/execution-control.schema.json").read_text())
        self.assertEqual(json_schema_failures(other_gate["ledger"], schema, schema, "ledger"), [])

    def test_code_test_formal_or_outside_paths_are_refused_on_the_gate_allowance(self):
        (self.root / "src").mkdir()
        (self.root / "src/app.py").write_text("value = 1\n")
        (self.root / "feature/research.md").symlink_to(self.root / "src/app.py")
        self.invoke("start")
        code = self.gate_fix("g6-code", "G6", ["feature/spec.md", "src/app.py"])
        self.assertEqual((code["disposition"], code["remediation_allowance"]), ("continue", "run_wide"))
        self.assertEqual(code["gate_ineligible"], "path_outside_planning_documents")
        self.assertEqual(code["ledger"]["corrective_cycles"], 1)
        self.assertNotIn("gate_allowances", code["ledger"])
        self.invoke("complete", dispatch_id="g6-code", outcome="completed")
        self.invoke("reserve", dispatch_id="fix-b", kind="corrective", failure_invariant="FR-002")
        self.invoke("complete", dispatch_id="fix-b", outcome="completed")
        cases = {"code": ["src/app.py"], "test": ["tests/test_app.py"], "formal model": ["feature/formal/model.tla"],
                 "contract": ["feature/contracts/api.json"], "other feature": ["other/spec.md"],
                 "nested checklist": ["feature/checklists/deep/security.md"], "unlisted note": ["feature/notes.md"],
                 "traversal": ["feature/../feature/spec.md"], "absolute": ["/feature/spec.md"],
                 "git metadata": ["feature/.git/spec.md"], "symlinked document": ["feature/research.md"],
                 "workflow sidecar": ["feature/.process/autopilot-state.json"]}
        for name, paths in cases.items():
            with self.subTest(case=name):
                refused = self.gate_fix("g6-refused", "G6", paths)
                self.assertEqual(refused["reasons"], ["failure_family_budget_exhausted"])
                self.assertEqual(refused["remediation_allowance"], "run_wide")
                self.assertEqual(refused["gate_ineligible"], "path_outside_planning_documents")
                self.assertNotIn("g6-refused", refused["ledger"]["dispatches"])
                self.assertNotIn("gate_allowances", refused["ledger"])
        empty = self.gate_fix("g6-empty", "G6", [])
        self.assertEqual((empty["remediation_allowance"], empty["gate_ineligible"]), ("run_wide", "no_remediation_paths"))

    def test_missing_or_mismatched_feature_binding_never_grants_a_free_allowance(self):
        self.spend_run_wide_budget()
        with self.assertRaisesRegex(ValueError, "explicit spec_file"):
            self.invoke("reserve", dispatch_id="g6-unbound", kind="corrective", failure_invariant="FR-001",
                        gate_remediation={"gate": "G6", "paths": ["feature/spec.md"]})
        path = self.root / self.invoke("status", mode="read_only")["ledger_path"]
        ledger = json.loads(path.read_text())
        ledger["invariant_binding"] = {"spec_file": "other/spec.md", "spec_sha256": "0" * 64, "bound_at": self.now}
        path.write_text(json.dumps(ledger))
        mismatched = self.gate_fix("g6-mismatch", "G6", ["feature/spec.md"])
        self.assertEqual(mismatched["reasons"], ["failure_family_budget_exhausted"])
        self.assertEqual((mismatched["remediation_allowance"], mismatched["gate_ineligible"]),
                         ("run_wide", "feature_binding_mismatch"))
        self.assertNotIn("gate_allowances", mismatched["ledger"])
        for malformed in ({"gate": "G6"}, {"gate": "G6", "paths": "feature/spec.md"}, {"gate": "G1", "paths": []},
                          {"gate": "G6.5", "paths": ["feature/spec.md"]}, {"gate": "G6", "paths": [1]}, ["G6"]):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                self.invoke("reserve", dispatch_id="malformed", kind="corrective", spec_file="feature/spec.md",
                            gate_remediation=malformed)
        with self.assertRaises(ValueError):
            self.invoke("reserve", dispatch_id="not-corrective", kind="implementation", spec_file="feature/spec.md",
                        gate_remediation={"gate": "G6", "paths": ["feature/spec.md"]})
        with self.assertRaises(ValueError):
            self.invoke("reserve", dispatch_id="both", kind="corrective", spec_file="feature/spec.md",
                        gate_remediation={"gate": "G6", "paths": ["feature/spec.md"]},
                        review_remediation={"tdd_unit": "alpha", "paths": ["src/alpha/core.py"]})

    def test_forged_or_overspent_gate_records_fail_closed(self):
        self.spend_run_wide_budget()
        admitted = self.gate_fix("g6-fix-1", "G6", ["feature/spec.md"])
        path = self.root / admitted["ledger_path"]
        valid = path.read_bytes()
        forged_dispatch = {"kind": "corrective", "outcome": "reserved", "reserved_at": self.now,
                           "reservation_id": None, "reconciliations": 0, "gate": "G6"}
        tampers = {
            "unlisted gate dispatch": lambda ledger: ledger["dispatches"].update(forged=forged_dispatch),
            "rounds over the bound": lambda ledger: (
                ledger["dispatches"].update({"g2": forged_dispatch, "g3": forged_dispatch}),
                ledger["gate_allowances"]["G6"].update(rounds=3, dispatch_ids=["g6-fix-1", "g2", "g3"])),
            "counter disagrees": lambda ledger: ledger["gate_allowances"]["G6"].update(rounds=2),
            "allowance record dropped": lambda ledger: ledger.pop("gate_allowances"),
            "unreserved corrective": lambda ledger: ledger["dispatches"]["g6-fix-1"].pop("gate"),
            "gate on a reservation": lambda ledger: ledger["dispatches"]["g6-fix-1"].update(
                reservation_id=next(iter(ledger["reservations"]))),
            "unknown gate": lambda ledger: (ledger["gate_allowances"].update({"G1": ledger["gate_allowances"].pop("G6")}),
                                            ledger["dispatches"]["g6-fix-1"].update(gate="G1")),
            "gate and increment on one dispatch": lambda ledger: (
                ledger["dispatches"]["g6-fix-1"].update(increment="alpha"),
                ledger.update(increment_allowances={"alpha": {"rounds": 1, "dispatch_ids": ["g6-fix-1"]}})),
        }
        for name, tamper in tampers.items():
            with self.subTest(tamper=name):
                ledger = json.loads(valid)
                tamper(ledger)
                path.write_text(json.dumps(ledger), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.invoke("status", mode="read_only")
        path.write_bytes(valid)
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")

    def test_stage_epoch_archives_gate_allowances(self):
        self.spend_run_wide_budget()
        for number in (1, 2):
            self.gate_fix(f"g6-fix-{number}", "G6", ["feature/tasks.md"])
            self.invoke("complete", dispatch_id=f"g6-fix-{number}", outcome="completed")
        (self.root / "feature/workflow.md").write_text(stage_workflow())
        opened = self.invoke("begin-stage-epoch", autopilot_args=["--stage", "implement"])
        self.assertEqual(opened["ledger"]["corrective_epochs"][0]["gate_allowances"]["G6"]["rounds"], 2)
        self.assertNotIn("gate_allowances", opened["ledger"])
        self.assertEqual(self.gate_fix("g6-fix-1", "G7", ["feature/tasks.md"])["reasons"],
                         ["dispatch_already_reserved_no_relaunch"])
        fresh = self.gate_fix("g7-fix-1", "G7", ["feature/tasks.md"])
        self.assertEqual((fresh["disposition"], fresh["ledger"]["gate_allowances"]["G7"]["rounds"]), ("continue", 1))
        schema = json.loads((Path(__file__).resolve().parents[3] /
                             "speckit-pro/speckit_pro_runner/contracts/execution-control.schema.json").read_text())
        self.assertEqual(json_schema_failures(fresh["ledger"], schema, schema, "ledger"), [])

    def test_both_hosts_document_the_gate_remediation_allowance(self):
        plugin = Path(__file__).resolve().parents[3] / "speckit-pro"
        references = plugin / "skills/speckit-autopilot/references"
        shared = " ".join((references / "execution-efficiency.md").read_text().split())
        for phrase in ("`gate_remediation`", "`gate_allowances`", "`gate_remediation_allowance_exhausted`",
                       "`remediation_allowance=gate`", "`remediation_allowance=run_wide`", "`gate_ineligible`",
                       "`path_outside_planning_documents`", "`feature_binding_mismatch`"):
            self.assertIn(phrase, shared)
        gates = (references / "gate-validation.md").read_text()
        rows = {line.split("|")[1].strip(): line.split("|")[5].strip() for line in gates.splitlines()
                if line.startswith("| G")}
        for gate in ("G2", "G3", "G4", "G5", "G6", "G7"):
            with self.subTest(gate=gate):
                self.assertIn("own", rows[gate])
        self.assertIn("`gate_remediation_allowance_exhausted`", " ".join(gates.split()))
        for host in ("skills/speckit-autopilot/references/phase-execution.md",
                     "codex-skills/speckit-autopilot/references/phase-execution-codex.md"):
            with self.subTest(host=host):
                text = " ".join((plugin / host).read_text().split())
                self.assertIn("`gate_remediation`", text)
                self.assertIn("planning documents", text)
                self.assertIn("`gate_remediation_allowance_exhausted`", text)
                self.assertIn("never a mid-run question", text)


GIT_ENVIRONMENT = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def commit_fixture(root):
    """Commit every file under ``root`` so HEAD holds the task-definition baseline."""
    if not (root / ".git").exists():
        subprocess.run(["git", "init", "-q", str(root)], check=True, env=GIT_ENVIRONMENT)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, env=GIT_ENVIRONMENT)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=fixture", "-c", "user.email=git@github.com",
                    "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "baseline"],
                   check=True, env=GIT_ENVIRONMENT)


class MetadataOnlyCorrectionTests(_ExecutionControlFixture, unittest.TestCase):
    """A task-verb swap inside the verification verbs is recorded without spending a cycle."""

    TASKS = ("## Phase 1: Setup\n\n"
             "- [ ] T001 Confirm the fixture loads from `src/app.py`\n"
             "- [ ] T002 [P] [US1] **Recheck** the parser output after T001\n"
             "- [ ] T003 Add the alpha increment in src/alpha/core.py\n")
    CORRECTED = TASKS.replace("T001 Confirm", "T001 Verify").replace("**Recheck**", "**Verify**")

    def setUp(self):
        super().setUp()
        (self.root / "feature/plan.md").write_text("# Plan\n")
        (self.root / "feature/tasks.md").write_text(self.TASKS)

    def correct(self, dispatch_id, mode="apply", **inputs):
        request = {"spec_file": "feature/spec.md", "failure_invariant": "FR-001", "metadata_only": True, **inputs}
        return self.invoke("reserve", mode=mode, dispatch_id=dispatch_id, kind="corrective", **request)

    def schema(self):
        return json.loads((Path(__file__).resolve().parents[3] /
                           "speckit-pro/speckit_pro_runner/contracts/execution-control.schema.json").read_text())

    def test_a_verification_verb_swap_is_admitted_without_spending_a_cycle(self):
        commit_fixture(self.root)
        IncrementReviewAllowanceTests.spend_run_wide_budget(self)
        before = self.invoke("status", mode="read_only")["ledger"]
        tasks = self.CORRECTED.replace("- [ ] T003", "- [x] T003").replace("- [ ] T001", "- [x] T001")
        (self.root / "feature/tasks.md").write_text(tasks)
        admitted = self.correct("verb-fix")
        self.assertEqual((admitted["disposition"], admitted["correction_allowance"]), ("continue", "metadata_only"))
        self.assertIsNone(admitted["reservation_id"])
        self.assertEqual(admitted["task_ids"], ["T001", "T002"])
        ledger = admitted["ledger"]
        self.assertEqual(ledger["corrective_cycles"], before["corrective_cycles"])
        self.assertEqual(ledger["reservations"], before["reservations"])
        self.assertNotIn("deferred", ledger)
        self.assertEqual(ledger["dispatches"]["verb-fix"]["metadata_correction"], ["T001", "T002"])
        record = ledger["metadata_corrections"][0]
        self.assertEqual({key: record[key] for key in ("dispatch_id", "task_ids", "tasks_file")},
                         {"dispatch_id": "verb-fix", "task_ids": ["T001", "T002"], "tasks_file": "feature/tasks.md"})
        self.assertEqual(record["baseline_sha256"], hashlib.sha256(self.TASKS.encode()).hexdigest())
        self.assertEqual(record["corrected_sha256"], hashlib.sha256(tasks.encode()).hexdigest())
        self.assertEqual(json_schema_failures(ledger, self.schema(), self.schema(), "ledger"), [])
        self.invoke("complete", dispatch_id="verb-fix", outcome="completed")
        self.assertEqual(self.invoke("status", mode="read_only")["ledger"]["corrective_cycles"], 2)

    def write_sidecar(self, tasks_text=None, **changes):
        texts = [(self.root / f"feature/{name}").read_text() for name in ("spec.md", "plan.md")]
        sidecar = {"schema_version": "task-execution.v1",
                   "fingerprints": fingerprints(*texts, tasks_text or self.TASKS),
                   "tasks": {task: {"capability_group": "core", "depends_on": [], "owns": [f"src/{task.lower()}"],
                                    "tdd_unit": task.lower()} for task in ("T001", "T002", "T003")}}
        for task, entry in changes.items():
            sidecar["tasks"][task].update(entry)
        path = self.root / "feature/.process/task-execution.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(sidecar, indent=2) + "\n")

    def test_the_task_execution_sidecar_must_keep_every_task_entry(self):
        self.write_sidecar()
        commit_fixture(self.root)
        IncrementReviewAllowanceTests.spend_run_wide_budget(self)
        (self.root / "feature/tasks.md").write_text(self.CORRECTED)
        sidecar = self.root / "feature/.process/task-execution.json"
        cases = {"ownership change": lambda: self.write_sidecar(T001={"owns": ["src/elsewhere"]}),
                 "dependency change": lambda: self.write_sidecar(self.CORRECTED, T002={"depends_on": ["T003"]}),
                 "unbound fingerprints": lambda: self.write_sidecar("- [ ] T009 Something else\n"),
                 "sidecar removed": sidecar.unlink,
                 "sidecar unreadable": lambda: sidecar.write_text("{not json")}
        for number, (name, change) in enumerate(cases.items()):
            with self.subTest(case=name):
                change()
                refused = self.correct(f"sidecar-{number}")
                self.assertEqual((refused["correction_allowance"], refused["metadata_ineligible"]),
                                 ("run_wide", "not_metadata_only"))
                self.assertNotIn("metadata_corrections", refused["ledger"])
        self.write_sidecar()
        stale = self.correct("sidecar-not-yet-refreshed", mode="dry_run")
        self.assertEqual(stale["correction_allowance"], "metadata_only")
        self.write_sidecar(self.CORRECTED)
        refreshed = self.correct("sidecar-refreshed")
        self.assertEqual((refreshed["correction_allowance"], refreshed["ledger"]["corrective_cycles"]),
                         ("metadata_only", 2))

    def test_a_sidecar_absent_from_the_baseline_is_refused(self):
        commit_fixture(self.root)
        self.invoke("start")
        (self.root / "feature/tasks.md").write_text(self.CORRECTED)
        self.write_sidecar(self.CORRECTED)
        refused = self.correct("new-sidecar")
        self.assertEqual((refused["correction_allowance"], refused["metadata_ineligible"]),
                         ("run_wide", "not_metadata_only"))
        self.assertEqual(refused["ledger"]["corrective_cycles"], 1)

    def test_an_unspent_budget_stays_unspent(self):
        commit_fixture(self.root)
        self.invoke("start")
        (self.root / "feature/tasks.md").write_text(self.CORRECTED)
        admitted = self.correct("verb-fix")
        self.assertEqual(admitted["correction_allowance"], "metadata_only")
        self.assertEqual((admitted["ledger"]["corrective_cycles"], admitted["ledger"]["reservations"]), (0, {}))

    def test_scope_changing_edits_take_the_ordinary_path(self):
        commit_fixture(self.root)
        IncrementReviewAllowanceTests.spend_run_wide_budget(self)
        cases = {
            "extra word": self.TASKS.replace("T001 Confirm the", "T001 Verify carefully the"),
            "non-verification verb": self.TASKS.replace("T001 Confirm", "T001 Add"),
            "verb into verification": self.TASKS.replace("T003 Add", "T003 Verify"),
            "path change": self.CORRECTED.replace("src/app.py", "src/other.py"),
            "description change": self.CORRECTED.replace("after T001", "after T003"),
            "marker change": self.CORRECTED.replace("[P] [US1] ", "[US1] "),
            "story change": self.CORRECTED.replace("[US1]", "[US2]"),
            "task id change": self.CORRECTED.replace("T003 Add", "T004 Add"),
            "added task": self.CORRECTED + "- [ ] T004 Verify the release notes\n",
            "removed task": self.CORRECTED.replace("- [ ] T003 Add the alpha increment in src/alpha/core.py\n", ""),
            "reordered tasks": self.CORRECTED.replace(
                "- [ ] T003 Add the alpha increment in src/alpha/core.py\n", "").replace(
                "## Phase 1: Setup\n\n", "## Phase 1: Setup\n\n- [ ] T003 Add the alpha increment in src/alpha/core.py\n"),
            "phase change": self.CORRECTED.replace("Phase 1: Setup", "Phase 2: Foundation"),
            "no change": self.TASKS,
        }
        reasons = {"no change": "no_task_correction"}
        for number, (name, tasks) in enumerate(cases.items()):
            with self.subTest(case=name):
                (self.root / "feature/tasks.md").write_text(tasks)
                refused = self.correct(f"refused-{number}")
                self.assertEqual(refused["reasons"], ["failure_family_budget_exhausted"])
                self.assertEqual(refused["disposition"], "defer")
                self.assertEqual((refused["correction_allowance"], refused["metadata_ineligible"]),
                                 ("run_wide", reasons.get(name, "not_metadata_only")))
                self.assertNotIn(f"refused-{number}", refused["ledger"]["dispatches"])
                self.assertNotIn("metadata_corrections", refused["ledger"])
                self.assertEqual(refused["ledger"]["corrective_cycles"], 2)
        for name in ("spec.md", "plan.md"):
            with self.subTest(changed=name):
                (self.root / "feature/tasks.md").write_text(self.CORRECTED)
                source = self.root / "feature" / name
                original = source.read_text()
                source.write_text(original + "- FR-003: a new requirement\n")
                refused = self.correct(f"source-{name}")
                self.assertEqual(refused["metadata_ineligible"], "planning_source_changed")
                self.assertNotIn("metadata_corrections", refused["ledger"])
                source.write_text(original)

    def test_a_scope_change_under_an_open_budget_spends_an_ordinary_cycle(self):
        commit_fixture(self.root)
        self.invoke("start")
        (self.root / "feature/tasks.md").write_text(self.TASKS.replace("T001 Confirm", "T001 Add"))
        ordinary = self.correct("scope-fix")
        self.assertEqual((ordinary["correction_allowance"], ordinary["metadata_ineligible"]),
                         ("run_wide", "not_metadata_only"))
        self.assertEqual(ordinary["ledger"]["corrective_cycles"], 1)
        self.assertIsNotNone(ordinary["reservation_id"])
        self.assertNotIn("metadata_correction", ordinary["ledger"]["dispatches"]["scope-fix"])

    def test_a_missing_baseline_is_refused(self):
        IncrementReviewAllowanceTests.spend_run_wide_budget(self)
        (self.root / "feature/tasks.md").write_text(self.CORRECTED)
        no_repository = self.correct("no-git-repo")
        self.assertEqual((no_repository["correction_allowance"], no_repository["metadata_ineligible"]),
                         ("run_wide", "baseline_unavailable"))
        (self.root / "feature/tasks.md").write_text(self.TASKS)
        (self.root / "feature/plan.md").rename(self.root / "plan.md.hold")
        commit_fixture(self.root)
        (self.root / "plan.md.hold").rename(self.root / "feature/plan.md")
        (self.root / "feature/tasks.md").write_text(self.CORRECTED)
        untracked = self.correct("untracked-plan")
        self.assertEqual(untracked["metadata_ineligible"], "baseline_unavailable")
        commit_fixture(self.root)
        (self.root / "feature/tasks.md").write_text(self.CORRECTED)
        with patch("speckit_pro_runner.execution_control.shutil.which", return_value=None):
            no_git = self.correct("no-git")
        self.assertEqual(no_git["metadata_ineligible"], "baseline_unavailable")
        (self.root / "feature/tasks.md").unlink()
        (self.root / "feature/tasks.md").symlink_to(self.root / "feature/plan.md")
        linked = self.correct("linked-tasks")
        self.assertEqual(linked["metadata_ineligible"], "baseline_unavailable")
        for ledger in (no_repository, untracked, no_git, linked):
            self.assertNotIn("metadata_corrections", ledger["ledger"])

    def test_a_task_is_corrected_once_per_run_even_across_stage_epochs(self):
        commit_fixture(self.root)
        IncrementReviewAllowanceTests.spend_run_wide_budget(self)
        (self.root / "feature/tasks.md").write_text(self.CORRECTED)
        self.correct("verb-fix")
        self.invoke("complete", dispatch_id="verb-fix", outcome="completed")
        commit_fixture(self.root)
        (self.root / "feature/tasks.md").write_text(self.CORRECTED.replace("T001 Verify", "T001 Check"))
        again = self.correct("verb-fix-again")
        self.assertEqual((again["correction_allowance"], again["metadata_ineligible"]),
                         ("run_wide", "task_already_corrected"))
        (self.root / "feature/tasks.md").write_text(self.CORRECTED)
        (self.root / "feature/workflow.md").write_text(stage_workflow())
        commit_fixture(self.root)
        opened = self.invoke("begin-stage-epoch", autopilot_args=["--stage", "implement"])
        self.assertEqual(opened["ledger"]["corrective_epochs"][0]["metadata_corrections"][0]["task_ids"], ["T001", "T002"])
        (self.root / "feature/tasks.md").write_text(self.CORRECTED.replace("T001 Verify", "T001 Check"))
        after_epoch = self.correct("verb-fix-after-epoch")
        self.assertEqual((after_epoch["correction_allowance"], after_epoch["metadata_ineligible"]),
                         ("run_wide", "task_already_corrected"))
        self.assertEqual(after_epoch["ledger"]["corrective_cycles"], 1)

    def test_a_malformed_request_is_rejected(self):
        commit_fixture(self.root)
        self.invoke("start")
        with self.assertRaisesRegex(ValueError, "explicit spec_file"):
            self.invoke("reserve", dispatch_id="unbound", kind="corrective", metadata_only=True)
        for name, inputs in {"not true": {"metadata_only": "yes"}, "false": {"metadata_only": False},
                             "with a gate": {"gate_remediation": {"gate": "G6", "paths": ["feature/tasks.md"]}},
                             "with a review": {"review_remediation": {"tdd_unit": "alpha", "paths": ["src/a.py"]}}}.items():
            with self.subTest(case=name), self.assertRaises(ValueError):
                self.correct("malformed", **inputs)
        with self.assertRaises(ValueError):
            self.invoke("reserve", dispatch_id="not-corrective", kind="implementation", spec_file="feature/spec.md",
                        metadata_only=True)

    def test_forged_metadata_records_fail_closed(self):
        commit_fixture(self.root)
        IncrementReviewAllowanceTests.spend_run_wide_budget(self)
        (self.root / "feature/tasks.md").write_text(self.CORRECTED)
        admitted = self.correct("verb-fix")
        path = self.root / admitted["ledger_path"]
        valid = path.read_bytes()
        forged = {"kind": "corrective", "outcome": "reserved", "reserved_at": self.now, "reservation_id": None,
                  "reconciliations": 0, "metadata_correction": ["T003"]}
        entry = json.loads(valid)["metadata_corrections"][0]
        tampers = {
            "unlisted metadata dispatch": lambda ledger: ledger["dispatches"].update(forged=forged),
            "record dropped": lambda ledger: ledger.pop("metadata_corrections"),
            "empty record list": lambda ledger: ledger.update(metadata_corrections=[]),
            "marker dropped": lambda ledger: ledger["dispatches"]["verb-fix"].pop("metadata_correction"),
            "task ids disagree": lambda ledger: ledger["dispatches"]["verb-fix"].update(metadata_correction=["T001"]),
            "task corrected twice": lambda ledger: (
                ledger["dispatches"].update(forged={**forged, "metadata_correction": ["T001"]}),
                ledger["metadata_corrections"].append({**entry, "dispatch_id": "forged", "task_ids": ["T001"]})),
            "malformed task id": lambda ledger: (
                ledger["dispatches"]["verb-fix"].update(metadata_correction=["X1"]),
                ledger["metadata_corrections"][0].update(task_ids=["X1"])),
            "extra key": lambda ledger: ledger["metadata_corrections"][0].update(cycles_spent=0),
            "on a reservation": lambda ledger: ledger["dispatches"]["verb-fix"].update(
                reservation_id=next(iter(ledger["reservations"]))),
            "with a gate": lambda ledger: (
                ledger["dispatches"]["verb-fix"].update(gate="G6"),
                ledger.update(gate_allowances={"G6": {"rounds": 1, "dispatch_ids": ["verb-fix"]}})),
            "not corrective": lambda ledger: ledger["dispatches"]["verb-fix"].update(kind="implementation"),
            "bad digest": lambda ledger: ledger["metadata_corrections"][0].update(baseline_sha256="0"),
            "absolute tasks file": lambda ledger: ledger["metadata_corrections"][0].update(
                tasks_file="/tmp/feature/tasks.md"),
            "traversing tasks file": lambda ledger: ledger["metadata_corrections"][0].update(
                tasks_file="feature/../other/tasks.md"),
            "not a tasks file": lambda ledger: ledger["metadata_corrections"][0].update(tasks_file="feature/plan.md"),
        }
        for name, tamper in tampers.items():
            with self.subTest(tamper=name):
                ledger = json.loads(valid)
                tamper(ledger)
                path.write_text(json.dumps(ledger), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.invoke("status", mode="read_only")
        # A bound run's record must name the bound feature's tasks.md.
        ledger = json.loads(valid)
        ledger.update(approved_invariants=ledger["approved_invariants"] or ["FR-001"],
                      invariant_binding={"spec_file": "other/spec.md", "spec_sha256": "0" * 64,
                                         "bound_at": ledger["started_at"]})
        path.write_text(json.dumps(ledger), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "bound feature's canonical tasks.md"):
            self.invoke("status", mode="read_only")
        path.write_bytes(valid)
        self.invoke("complete", dispatch_id="verb-fix", outcome="completed")
        (self.root / "feature/workflow.md").write_text(stage_workflow())
        opened = self.invoke("begin-stage-epoch", autopilot_args=["--stage", "implement"])
        archived = path.read_bytes()
        ledger = json.loads(archived)
        ledger["dispatches"]["forged"] = {**forged, "metadata_correction": ["T001"]}
        ledger["metadata_corrections"] = [{**entry, "dispatch_id": "forged", "task_ids": ["T001"]}]
        path.write_text(json.dumps(ledger), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "corrected twice"):
            self.invoke("status", mode="read_only")
        path.write_bytes(archived)
        self.assertEqual(opened["disposition"], "continue")
        self.assertEqual(json_schema_failures(opened["ledger"], self.schema(), self.schema(), "ledger"), [])

    def test_both_hosts_document_the_metadata_only_correction(self):
        plugin = Path(__file__).resolve().parents[3] / "speckit-pro"
        shared = " ".join((plugin / "skills/speckit-autopilot/references/execution-efficiency.md").read_text().split())
        for phrase in ("`metadata_only: true`", "`metadata_corrections`", "`correction_allowance=metadata_only`",
                       "`correction_allowance=run_wide`", "`metadata_ineligible`", "`PHASE7_VERIFY_KEYWORDS`",
                       "`baseline_unavailable`", "`planning_source_changed`", "`not_metadata_only`",
                       "`no_task_correction`", "`task_already_corrected`", "`feature_binding_mismatch`",
                       "`action=fingerprints`"):
            self.assertIn(phrase, shared)
        self.assertNotIn("admission is deferred", shared)
        for host in ("skills/speckit-autopilot/SKILL.md", "skills/speckit-autopilot/references/error-recovery.md",
                     "codex-skills/speckit-autopilot/references/error-recovery-codex.md"):
            with self.subTest(host=host):
                self.assertIn("`metadata_only: true`", " ".join((plugin / host).read_text().split()))


class WorkflowIdentityTests(_ExecutionControlFixture, unittest.TestCase):
    def test_different_workflows_cannot_adopt_an_existing_ledger(self):
        first = self.invoke("start")
        (self.root / "feature/other-workflow.md").write_text("# Other workflow\n")
        other = execution_control(self.root, {"workflow_file": "feature/other-workflow.md", "action": "start"}, "apply")
        self.assertNotEqual((first["ledger_path"], first["ledger"]["run_id"]),
                            (other["ledger_path"], other["ledger"]["run_id"]))
        path, shared = self.root / first["ledger_path"], {
            "workflow_file": "feature/other-workflow.md", "ledger_path": first["ledger_path"]}
        before = path.read_bytes()
        requests = ({**shared, "action": "start"}, {**shared, "action": "reserve", "expected_run_id": self.run_id,
                    "dispatch_id": "cross-workflow", "kind": "implementation"})
        for request in requests:
            with self.assertRaises(ValueError):
                execution_control(self.root, request, "apply")
            self.assertEqual(path.read_bytes(), before)

    def test_known_run_missing_ledger_cannot_be_reset_and_relocation_preserves_budget(self):
        first = self.invoke("start")
        self.invoke("reserve", dispatch_id="fix", kind="corrective", failure_invariant="FR-001")
        self.invoke("reserve", dispatch_id="uncertain", kind="implementation")
        self.invoke("complete", dispatch_id="uncertain", outcome="unknown")
        old_path, invariants = self.root / first["ledger_path"], first["ledger"]["approved_invariants"]
        (self.root / "feature/workflow.md").rename(self.root / "feature/moved-workflow.md")
        moved_inputs = {"workflow_file": "feature/moved-workflow.md", "expected_run_id": self.run_id}
        for action, mode in (("start", "apply"), ("status", "read_only")):
            with self.assertRaises(ValueError):
                execution_control(self.root, {**moved_inputs, "action": action}, mode)
        moved_path = old_path.with_name("relocated-owned-ledger.json")
        old_path.rename(moved_path)
        ledger_path, before = moved_path.relative_to(self.root).as_posix(), moved_path.read_bytes()
        event = {"native_event_id": "workflow-move-1", "run_id": self.run_id, "action": "workflow_relocated",
                 "previous_workflow_file": "feature/workflow.md", "workflow_file": "feature/moved-workflow.md"}
        for change in ({"run_id": "wrong-run"}, {"previous_workflow_file": "feature/not-the-owner.md"},
                       {"workflow_file": "feature/not-the-request.md"}):
            with self.assertRaises(ValueError):
                execution_control(self.root, {**moved_inputs, "action": "relocate-workflow", "ledger_path": ledger_path,
                                               "native_observation": {**event, **change}}, "apply")
            self.assertEqual(moved_path.read_bytes(), before)
        moved = execution_control(self.root, {**moved_inputs, "action": "relocate-workflow", "ledger_path": ledger_path,
                                               "native_observation": event}, "apply")
        self.assertEqual((moved["ledger"]["run_id"], moved["ledger"]["corrective_cycles"],
                          moved["ledger"]["approved_invariants"]), (self.run_id, 1, invariants))
        self.assertEqual(moved["ledger"]["workflow_identity"], {"original_workflow_file": "feature/workflow.md",
                         "current_workflow_file": "feature/moved-workflow.md", "relocation_event_ids": ["workflow-move-1"]})
        after = moved_path.read_bytes()
        _assert_relocation_event_reuse_rejected(self, moved_path, {**moved_inputs, "ledger_path": ledger_path})
        (self.root / "feature/moved-again-workflow.md").write_text("# Moved again workflow\n")
        replay = {**event, "previous_workflow_file": "feature/moved-workflow.md",
                  "workflow_file": "feature/moved-again-workflow.md"}
        with self.assertRaises(ValueError):
            execution_control(self.root, {**moved_inputs, "workflow_file": "feature/moved-again-workflow.md",
                                           "action": "relocate-workflow", "ledger_path": ledger_path,
                                           "native_observation": replay}, "apply")
        self.assertEqual(moved_path.read_bytes(), after)
        resumed = execution_control(self.root, {**moved_inputs, "action": "status", "ledger_path": ledger_path}, "read_only")
        self.assertEqual(resumed["ledger"]["run_id"], self.run_id)
        with self.assertRaises(ValueError):
            self.invoke("start")

    def test_process_directory_workflow_ledger_is_not_doubled_and_legacy_path_is_accepted(self):
        workflow = "docs/ai/specs/.process/SPEC-workflow.md"
        (self.root / "docs/ai/specs/.process").mkdir(parents=True)
        (self.root / workflow).write_text("# Workflow\n")
        (self.root / "docs/ai/specs/.process/spec.md").write_text("- FR-001: preserve data\n")
        started = execution_control(self.root, {"workflow_file": workflow, "action": "start"}, "apply")
        key = Path(started["ledger_path"]).name
        self.assertEqual(started["ledger_path"], f"docs/ai/specs/.process/execution-control/{key}")
        self.assertTrue((self.root / started["ledger_path"]).is_file())
        snapshot = tree_bytes(self.root, workflow)
        self.assertFalse([path for path in snapshot if "execution-control" in path])

        legacy = f"docs/ai/specs/.process/.process/execution-control/{key}"
        (self.root / legacy).parent.mkdir(parents=True)
        (self.root / started["ledger_path"]).rename(self.root / legacy)
        common = {"workflow_file": workflow, "ledger_path": legacy, "expected_run_id": started["ledger"]["run_id"]}
        status = execution_control(self.root, {**common, "action": "status"}, "read_only")
        self.assertEqual((status["ledger_path"], status["ledger"]["run_id"]), (legacy, started["ledger"]["run_id"]))
        reserved = execution_control(self.root, {**common, "action": "reserve", "dispatch_id": "impl-1",
                                                 "kind": "implementation"}, "apply")
        self.assertEqual(reserved["disposition"], "continue")
        self.assertTrue((self.root / legacy).is_file())
        self.assertFalse((self.root / started["ledger_path"]).exists())
        snapshot = tree_bytes(self.root, workflow)
        self.assertFalse([path for path in snapshot if "execution-control" in path])


class IncrementTestFixAllowanceTests(_ExecutionControlFixture, unittest.TestCase):
    """A test-only fix to test code an increment itself edited in this run needs no re-plan (issue 826)."""

    TASKS = ("## Phase 3: Stories\n- [ ] T001 Build the alpha increment\n"
             + "- [ ] T002 Build the beta increment\n")
    OWNERSHIP = {"T001": ("alpha", ["src/alpha", "tests/test_runner.py", "tests/test_alpha_extra.py"]),
                 "T002": ("beta", ["src/beta", "tests/test_beta.py"])}
    RUNNER_TEST = "tests/test_runner.py"

    def setUp(self):
        super().setUp()
        feature = self.root / "feature"
        (feature / ".process").mkdir()
        (feature / "plan.md").write_text("plan\n")
        (feature / "tasks.md").write_text(self.TASKS)
        tasks = {task_id: {"capability_group": "stories", "depends_on": [], "owns": owns, "tdd_unit": unit}
                 for task_id, (unit, owns) in self.OWNERSHIP.items()}
        metadata = {"schema_version": "task-execution.v1",
                    "fingerprints": fingerprints((feature / "spec.md").read_text(), "plan\n", self.TASKS),
                    "tasks": tasks}
        (feature / ".process/task-execution.json").write_text(json.dumps(metadata))
        for relative, text in ((self.RUNNER_TEST, "def test_cancellation():\n    assert True\n"),
                               ("tests/test_beta.py", "def test_beta():\n    assert True\n"),
                               ("tests/test_alpha_extra.py", "def test_extra():\n    assert True\n")):
            (self.root / relative).parent.mkdir(parents=True, exist_ok=True)
            (self.root / relative).write_text(text)
        commit_fixture(self.root)
        self.invoke("start")
        for dispatch_id, invariant in (("fix-a", "FR-001"), ("fix-b", "FR-002")):
            self.invoke("reserve", dispatch_id=dispatch_id, kind="corrective", failure_invariant=invariant)
            self.invoke("complete", dispatch_id=dispatch_id, outcome="completed")

    def write(self, relative, text):
        (self.root / relative).parent.mkdir(parents=True, exist_ok=True)
        (self.root / relative).write_text(text)

    def implement(self):
        """alpha stops at RED: its optional mock in an existing test file breaks the cancellation test."""
        reserved = self.invoke("reserve", dispatch_id="alpha-implement", kind="implementation", tdd_units=["alpha"])
        self.assertEqual(reserved["disposition"], "continue")
        self.write("src/alpha/core.py", "def cancel():\n    return None\n")
        self.write(self.RUNNER_TEST, "import mock\n\ndef test_cancellation():\n    assert False\n")
        done = self.invoke("complete", dispatch_id="alpha-implement", outcome="failed")
        self.assertEqual(done["ledger"]["dispatches"]["alpha-implement"]["changed_paths"],
                         ["src/alpha/core.py", self.RUNNER_TEST])
        self.invoke("reserve", dispatch_id="beta-implement", kind="implementation", tdd_units=["beta"])
        self.write("tests/test_beta.py", "def test_beta():\n    assert 1\n")
        self.invoke("complete", dispatch_id="beta-implement", outcome="completed")

    def request_fix(self, dispatch_id, paths, unit="alpha", mode="apply"):
        return self.invoke("reserve", mode=mode, dispatch_id=dispatch_id, kind="corrective",
                           spec_file="feature/spec.md", failure_invariant="FR-001",
                           test_fix={"tdd_unit": unit, "paths": paths})

    def test_a_test_only_fix_to_the_increments_own_test_edit_runs_without_a_replan(self):
        self.implement()
        admitted = self.request_fix("alpha-test-fix", [self.RUNNER_TEST])
        self.assertEqual((admitted["disposition"], admitted["test_fix_allowance"]), ("continue", "increment"))
        self.assertIsNone(admitted["reservation_id"])
        ledger = admitted["ledger"]
        self.assertEqual(ledger["corrective_cycles"], 2)
        self.assertNotIn("corrective_epochs", ledger)
        self.assertEqual(ledger["test_fix_allowances"], {"alpha": {"rounds": 1, "dispatch_ids": ["alpha-test-fix"]}})
        self.assertEqual(ledger["dispatches"]["alpha-test-fix"]["test_fix"], "alpha")
        self.write(self.RUNNER_TEST, "def test_cancellation():\n    assert True\n")
        completed = self.invoke("complete", dispatch_id="alpha-test-fix", outcome="completed")
        self.assertEqual(completed["disposition"], "continue")
        record = completed["ledger"]["dispatches"]["alpha-test-fix"]
        self.assertEqual((record["outcome"], record["changed_paths"]), ("completed", [self.RUNNER_TEST]))
        self.assertNotIn("worktree_before", record)
        schema = json.loads(SCHEMA_PATH.read_text())
        self.assertEqual(json_schema_failures(completed["ledger"], schema, schema, "ledger"), [])
        ordinary = self.invoke("reserve", mode="dry_run", dispatch_id="ordinary", kind="corrective",
                               failure_invariant="FR-001")
        self.assertEqual(ordinary["reasons"], ["failure_family_budget_exhausted"])

    def test_a_fix_that_touches_product_code_is_refused(self):
        self.implement()
        refused = self.request_fix("alpha-product", [self.RUNNER_TEST, "src/alpha/core.py"])
        self.assertEqual((refused["test_fix_allowance"], refused["test_fix_ineligible"]),
                         ("run_wide", "path_not_test_code"))
        self.assertEqual((refused["disposition"], refused["reasons"]), ("defer", ["failure_family_budget_exhausted"]))
        self.assertNotIn("test_fix_allowances", refused["ledger"])
        self.assertNotIn("alpha-product", refused["ledger"]["dispatches"])

    def test_a_test_file_the_increment_did_not_edit_in_this_run_is_refused(self):
        self.implement()
        cases = {"another increment's test file": ("tests/test_beta.py", "path_outside_increment_ownership"),
                 "an owned test file nobody edited": ("tests/test_alpha_extra.py", "path_not_edited_by_increment"),
                 "an owned directory": ("src/alpha", "path_not_test_code")}
        for name, (path, reason) in cases.items():
            with self.subTest(case=name):
                refused = self.request_fix("alpha-" + name.replace(" ", "-").replace("'", ""), [path])
                self.assertEqual((refused["test_fix_allowance"], refused["test_fix_ineligible"]), ("run_wide", reason))
                self.assertEqual(refused["disposition"], "defer")
        beta_edit = self.request_fix("beta-claims-alpha", ["tests/test_beta.py"], unit="alpha")
        self.assertEqual(beta_edit["test_fix_ineligible"], "path_outside_increment_ownership")
        unrecorded = self.request_fix("gamma-fix", [self.RUNNER_TEST], unit="gamma")
        self.assertEqual(unrecorded["test_fix_ineligible"], "increment_not_in_ownership_evidence")

    def test_edits_are_attributed_only_to_recorded_implementation_dispatches(self):
        self.invoke("reserve", dispatch_id="untagged-implement", kind="implementation")
        self.write(self.RUNNER_TEST, "import mock\n")
        self.invoke("complete", dispatch_id="untagged-implement", outcome="failed")
        refused = self.request_fix("alpha-untagged", [self.RUNNER_TEST])
        self.assertEqual(refused["test_fix_ineligible"], "path_not_edited_by_increment")
        with patch("speckit_pro_runner.execution_control.shutil.which", return_value=None):
            self.invoke("reserve", dispatch_id="no-git-implement", kind="implementation", tdd_units=["alpha"])
            self.write(self.RUNNER_TEST, "import other_mock\n")
            done = self.invoke("complete", dispatch_id="no-git-implement", outcome="failed")
        self.assertNotIn("changed_paths", done["ledger"]["dispatches"]["no-git-implement"])
        self.assertEqual(self.request_fix("alpha-no-git", [self.RUNNER_TEST])["test_fix_ineligible"],
                         "path_not_edited_by_increment")
        with self.assertRaises(ValueError):
            self.invoke("reserve", dispatch_id="tagged-corrective", kind="corrective", failure_invariant="FR-001",
                        tdd_units=["alpha"])
        for malformed in ([], ["alpha", "alpha"], [""], "alpha"):
            with self.subTest(tdd_units=malformed), self.assertRaises(ValueError):
                self.invoke("reserve", dispatch_id="malformed-implement", kind="implementation", tdd_units=malformed)

    def test_a_second_test_fix_for_the_same_increment_is_refused(self):
        self.implement()
        self.request_fix("alpha-test-fix", [self.RUNNER_TEST])
        self.write(self.RUNNER_TEST, "def test_cancellation():\n    assert True\n")
        self.invoke("complete", dispatch_id="alpha-test-fix", outcome="completed")
        second = self.request_fix("alpha-test-fix-2", [self.RUNNER_TEST])
        self.assertEqual((second["test_fix_allowance"], second["test_fix_ineligible"]),
                         ("run_wide", "test_fix_allowance_spent"))
        self.assertEqual(second["disposition"], "defer")
        self.assertEqual(second["ledger"]["test_fix_allowances"]["alpha"]["rounds"], 1)
        self.assertNotIn("alpha-test-fix-2", second["ledger"]["dispatches"])

    def test_a_fix_whose_actual_changes_leave_its_declared_test_paths_does_not_complete(self):
        self.implement()
        self.request_fix("alpha-test-fix", [self.RUNNER_TEST])
        self.write(self.RUNNER_TEST, "def test_cancellation():\n    assert True\n")
        self.write("src/alpha/core.py", "def cancel():\n    return 1\n")
        refused = self.invoke("complete", dispatch_id="alpha-test-fix", outcome="completed")
        self.assertEqual((refused["disposition"], refused["reasons"]),
                         ("checkpoint_required", ["test_fix_scope_unproven"]))
        self.assertEqual(refused["ledger"]["dispatches"]["alpha-test-fix"]["outcome"], "reserved")
        failed = self.invoke("complete", dispatch_id="alpha-test-fix", outcome="failed")
        record = failed["ledger"]["dispatches"]["alpha-test-fix"]
        self.assertEqual((record["outcome"], record["changed_paths"]), ("failed", ["src/alpha/core.py", self.RUNNER_TEST]))

    def test_a_fix_that_changes_nothing_does_not_complete(self):
        self.implement()
        self.request_fix("alpha-test-fix", [self.RUNNER_TEST])
        refused = self.invoke("complete", dispatch_id="alpha-test-fix", outcome="completed")
        self.assertEqual((refused["disposition"], refused["reasons"]),
                         ("checkpoint_required", ["test_fix_scope_unproven"]))
        self.assertEqual(refused["ledger"]["dispatches"]["alpha-test-fix"]["outcome"], "reserved")

    def test_a_completed_test_fix_does_not_resolve_a_deferred_review_fix(self):
        self.implement()
        for dispatch_id in ("alpha-review-1", "alpha-review-2"):
            request = dict(dispatch_id=dispatch_id, kind="corrective", spec_file="feature/spec.md",
                           failure_invariant="FR-001", review_remediation={"tdd_unit": "alpha", "paths": ["src/alpha"]})
            self.invoke("reserve", **request)
            self.invoke("complete", dispatch_id=dispatch_id, outcome="completed")
        deferred = self.invoke("reserve", dispatch_id="alpha-review-3", kind="corrective", spec_file="feature/spec.md",
                               failure_invariant="FR-001",
                               review_remediation={"tdd_unit": "alpha", "paths": ["src/alpha"]})
        self.assertEqual(deferred["reasons"], ["increment_review_allowance_exhausted"])
        self.assertEqual(self.request_fix("alpha-test-fix", [self.RUNNER_TEST])["test_fix_allowance"], "increment")
        self.write(self.RUNNER_TEST, "def test_cancellation():\n    assert True\n")
        completed = self.invoke("complete", dispatch_id="alpha-test-fix", outcome="completed")
        entry = completed["ledger"]["deferred"][0]
        self.assertEqual((entry["unit"], "resolved_by" in entry), ("alpha", False))

    def test_forged_test_fix_and_edit_records_fail_closed(self):
        self.implement()
        admitted = self.request_fix("alpha-test-fix", [self.RUNNER_TEST])
        path = self.root / admitted["ledger_path"]
        valid = path.read_bytes()
        forged = {"kind": "corrective", "outcome": "reserved", "reserved_at": self.now, "reservation_id": None,
                  "reconciliations": 0, "test_fix": "alpha", "test_fix_paths": [self.RUNNER_TEST]}
        tampers = {
            "unlisted test-fix dispatch": lambda ledger: ledger["dispatches"].update(forged=forged),
            "rounds over the bound": lambda ledger: (
                ledger["dispatches"].update(forged=forged),
                ledger["test_fix_allowances"]["alpha"].update(rounds=2, dispatch_ids=["alpha-test-fix", "forged"])),
            "allowance record dropped": lambda ledger: ledger.pop("test_fix_allowances"),
            "product path declared": lambda ledger: ledger["dispatches"]["alpha-test-fix"].update(
                test_fix_paths=["src/alpha/core.py"]),
            "test fix on a reservation": lambda ledger: ledger["dispatches"]["alpha-test-fix"].update(
                reservation_id=next(iter(ledger["reservations"]))),
            "test fix and increment review at once": lambda ledger: ledger["dispatches"]["alpha-test-fix"].update(
                increment="alpha"),
            "edits on an untagged dispatch": lambda ledger: ledger["dispatches"]["fix-a"].update(
                changed_paths=[self.RUNNER_TEST]),
            "units on a corrective dispatch": lambda ledger: ledger["dispatches"]["fix-a"].update(tdd_units=["alpha"]),
            "unsorted edits": lambda ledger: ledger["dispatches"]["alpha-implement"].update(
                changed_paths=[self.RUNNER_TEST, "src/alpha/core.py"]),
            "escaping edit": lambda ledger: ledger["dispatches"]["alpha-implement"].update(
                changed_paths=["../outside.py"]),
            "snapshot after settlement": lambda ledger: ledger["dispatches"]["alpha-implement"].update(
                worktree_before={"head": "0" * 40, "dirty": {}}),
        }
        for name, tamper in tampers.items():
            with self.subTest(tamper=name):
                ledger = json.loads(valid)
                tamper(ledger)
                path.write_text(json.dumps(ledger), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.invoke("status", mode="read_only")
        path.write_bytes(valid)
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")

    def test_malformed_test_fix_requests_are_rejected(self):
        for malformed in ({"tdd_unit": "alpha"}, {"tdd_unit": "alpha", "paths": "tests/x.py"},
                          {"tdd_unit": "", "paths": ["tests/x.py"]}, ["alpha"]):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                self.invoke("reserve", dispatch_id="malformed", kind="corrective", spec_file="feature/spec.md",
                            test_fix=malformed)
        request = {"tdd_unit": "alpha", "paths": [self.RUNNER_TEST]}
        for extra in ({"review_remediation": request}, {"gate_remediation": {"gate": "G6", "paths": []}},
                      {"metadata_only": True}):
            with self.subTest(extra=list(extra)), self.assertRaises(ValueError):
                self.invoke("reserve", dispatch_id="mixed", kind="corrective", spec_file="feature/spec.md",
                            test_fix=request, **extra)
        with self.assertRaisesRegex(ValueError, "explicit spec_file"):
            self.invoke("reserve", dispatch_id="no-spec", kind="corrective", test_fix=request)
        with self.assertRaises(ValueError):
            self.invoke("reserve", dispatch_id="not-corrective", kind="implementation", spec_file="feature/spec.md",
                        test_fix=request)

    def test_a_replan_archives_the_test_fix_allowance(self):
        self.implement()
        self.request_fix("alpha-test-fix", [self.RUNNER_TEST])
        self.write(self.RUNNER_TEST, "def test_cancellation():\n    assert True\n")
        self.invoke("complete", dispatch_id="alpha-test-fix", outcome="completed")
        (self.root / "feature/workflow.md").write_text(stage_workflow())
        opened = self.invoke("begin-stage-epoch", autopilot_args=["--stage", "implement"])
        self.assertEqual(opened["ledger"]["corrective_epochs"][0]["test_fix_allowances"]["alpha"]["rounds"], 1)
        self.assertNotIn("test_fix_allowances", opened["ledger"])
        schema = json.loads(SCHEMA_PATH.read_text())
        self.assertEqual(json_schema_failures(opened["ledger"], schema, schema, "ledger"), [])

    def test_both_hosts_document_the_test_fix_allowance(self):
        plugin = Path(__file__).resolve().parents[3] / "speckit-pro"
        shared = " ".join((plugin / "skills/speckit-autopilot/references/execution-efficiency.md").read_text().split())
        for phrase in ("`test_fix`", "`tdd_units`", "`changed_paths`", "`test_fix_allowance=increment`",
                       "`test_fix_allowance=run_wide`", "`test_fix_ineligible`", "`test_fix_scope_unproven`",
                       "`path_not_edited_by_increment`", "one test fix per increment"):
            self.assertIn(phrase, shared)
        for host in ("skills/speckit-autopilot/references/phase-execution.md",
                     "codex-skills/speckit-autopilot/references/phase-execution-codex.md"):
            with self.subTest(host=host):
                text = " ".join((plugin / host).read_text().split())
                for phrase in ("`test_fix`", "`tdd_units`", "without `begin-replan-epoch`",
                               "never ask the operator for a re-plan"):
                    self.assertIn(phrase, text)


class SelfIgnoringByproductDirectoryTests(_ExecutionControlFixture, unittest.TestCase):
    """#813: every runner byproduct directory ignores itself from the run's first write."""

    def setUp(self):
        super().setUp()
        self.environment = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        self.git("init", "-q")
        self.git("add", "-A")
        self.git("-c", "user.name=fixture", "-c", "user.email=git@github.com", "commit", "-q", "-m", "base")

    def git(self, *args, check=True):
        return subprocess.run(["git", "-C", str(self.root), *args], check=check, capture_output=True, text=True,
                              env=self.environment)

    def assert_clean_and_ignored(self, relative):
        self.assertEqual(self.git("status", "--porcelain", "--untracked-files=all").stdout, "")
        self.assertEqual(self.git("check-ignore", "-q", relative, check=False).returncode, 0, relative)

    def test_ledger_directory_is_ignored_after_the_first_write(self):
        started = self.invoke("start")
        self.assert_clean_and_ignored(started["ledger_path"])

    def test_verification_directory_is_ignored_before_any_verification_record(self):
        self.invoke("start")
        home = "/".join(("", "home", "synthoperator", "repo"))
        log = self.root / "feature/.process/verification/orchestrator.log"
        log.parent.mkdir(exist_ok=True)
        log.write_text(f"ran the suite from {home}\n")
        self.assert_clean_and_ignored(log.relative_to(self.root).as_posix())

    def test_committed_marker_evidence_stays_tracked_and_visible(self):
        self.invoke("start")
        process = self.root / "feature/.process"
        record, checkpoint = process / "verification/M1.json", process / "checkpoints/M1.json"
        checkpoint.parent.mkdir()
        record.parent.mkdir(exist_ok=True)
        record.write_text("{}\n")
        checkpoint.write_text("{}\n")
        self.assertEqual(self.git("check-ignore", "-q", "feature/.process/checkpoints/M1.json", check=False).returncode, 1)
        self.git("add", "--force", "--", "feature/.process/verification/M1.json")
        self.git("add", "--", "feature/.process/checkpoints/M1.json")
        self.git("-c", "user.name=fixture", "-c", "user.email=git@github.com", "commit", "-q", "-m", "marker")
        record.write_text('{"status": "complete"}\n')
        self.assertEqual(self.git("status", "--porcelain").stdout, " M feature/.process/verification/M1.json\n")
        self.assertEqual(self.git("check-ignore", "-q", "feature/.process/verification/M1.json", check=False).returncode, 1)

    def test_both_hosts_say_the_verification_directory_is_self_ignoring(self):
        plugin = Path(__file__).resolve().parents[3] / "speckit-pro"
        for name in ("skills/speckit-autopilot/references/phase-execution.md",
                     "codex-skills/speckit-autopilot/references/phase-execution-codex.md"):
            with self.subTest(file=name):
                text = " ".join((plugin / name).read_text(encoding="utf-8").split())
                self.assertIn("the verification directory is self-ignoring before any verification record exists", text)


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "feature").mkdir()
        commands = {"UNIT_TEST": f"{sys.executable} check.py"}
        (self.root / "feature/workflow.md").write_text("## PROJECT_COMMANDS\n```json\n" + json.dumps(commands) + "\n```\n")
        (self.root / "check.py").write_text("print('verified')\n")
        (self.root / "fixture.txt").write_text("dirty untracked fixture")
        self.inputs = {"workflow_file": "feature/workflow.md", "command_id": "UNIT_TEST"}
        self.run_id = None

    def produce(self):
        binding = {"expected_run_id": self.run_id} if self.run_id else {}
        started = execution_control(self.root, {"workflow_file": "feature/workflow.md", "action": "start", **binding}, "apply")
        run_id = started["ledger"]["run_id"]
        self.run_id = run_id
        dispatch = uuid.uuid4().hex
        execution_control(self.root, {"workflow_file": "feature/workflow.md", "action": "reserve",
                                      "dispatch_id": dispatch, "kind": "verification", "expected_run_id": run_id}, "apply")
        result = execute_verification(self.root, {**self.inputs, "dispatch_id": dispatch, "expected_run_id": run_id}, "apply")
        observation = {**result["observation_material"], "native_event_id": "actual-host-event-1"}
        return result, observation

    def validate(self, result, observation=None):
        return validate_execution_record(self.root, {**self.inputs, "record_path": result["record_path"], "native_observation": observation})

    def test_directory_named_gitignore_fails_with_a_clear_error(self):
        owned = self.root / "feature/.process/execution-control"
        (owned / ".gitignore").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, r"\.gitignore is not a regular file"):
            ignore_owned_directory(owned)
        self.assertTrue((owned / ".gitignore").is_dir())

    def test_directory_wide_add_never_stages_ledger_or_verification_evidence(self):
        environment = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, env=environment)
        result, _ = self.produce()
        ledger = self.root / "feature/.process/execution-control"
        self.assertTrue(any(ledger.glob("*.json")) and (self.root / result["record_path"]).is_file())
        subprocess.run(["git", "-C", str(self.root), "add", "-A"], check=True, env=environment)
        staged = subprocess.run(["git", "-C", str(self.root), "diff", "--cached", "--name-only", "-z"], check=True,
                                capture_output=True, text=True, env=environment).stdout.split("\0")
        staged = [name for name in staged if name]
        self.assertIn("fixture.txt", staged)
        self.assertEqual([name for name in staged if is_runner_byproduct(name)], [])
        self.assertEqual([name for name in staged if "execution-control" in name or "verification" in name], [])
        for directory in (ledger, (self.root / result["record_path"]).parent):
            self.assertTrue(is_runner_byproduct((directory / ".gitignore").relative_to(self.root).as_posix()))

    def test_true_reuse_requires_independent_native_observation(self):
        result, observed = self.produce()
        self.assertFalse(self.validate(result, observed)["reusable"])
        self.assertFalse(self.validate(result)["reusable"])

    def test_a_failing_run_records_its_failing_checks_on_the_ledger(self):
        (self.root / "check.py").write_text("import sys\nsys.stderr.write(" + repr(unittest_output("test_a"))
                                            + ")\nsys.exit(1)\n")
        result, _ = self.produce()
        ledger_file = next((self.root / "feature/.process/execution-control").glob("*.json"))
        item = json.loads(ledger_file.read_text())["dispatches"][result["record"]["dispatch_id"]]
        self.assertEqual(item["failing_checks"]["command_id"], "UNIT_TEST")
        self.assertEqual(item["failing_checks"]["failing"], ["test_a (tests.test_sample.SampleTests.test_a)"])

    def test_produced_record_fields_match_published_schema(self):
        result, _ = self.produce()
        schema_path = Path(__file__).resolve().parents[3] / "speckit-pro/speckit_pro_runner/contracts/verification-record.schema.json"
        schema = json.loads(schema_path.read_text())
        self.assertLessEqual(set(result["record"]), set(schema["properties"]))
        self.assertLessEqual(set(schema["required"]), set(result["record"]))
        self.assertIn("output_directory", schema["required"])

    def test_synthetic_qualified_host_event_not_portable_runtime_qualification(self):
        result, observed = self.produce()
        path = self.root / result["record_path"]
        record = json.loads(path.read_text())
        # Synthetic host adapter fixture: no claim the portable copy-only
        # producer actually implements this independently qualified host mode.
        record["isolation_mode"] = "qualified_readonly_snapshot"
        path.write_text(json.dumps(record))
        observed["isolation_mode"] = "qualified_readonly_snapshot"
        observed["qualified_isolation"] = {
            "schema_version": "native-isolation/v1",
            **{key: record[key] for key in ("execution_id", "snapshot_sha256", "environment_sha256", "toolchain", "output_directory")},
            "readonly_snapshot_identity": "fixture-readonly-mount", "isolated_output_identity": "fixture-output-mount",
            "qualification_id": "synthetic-test-only", "external_input_sha256": "a" * 64,
            "current_external_input_sha256": "a" * 64}
        self.assertTrue(self.validate(result, observed)["reusable"])
        observed["qualified_isolation"]["output_directory"] = str(self.root / "wrong-output")
        self.assertIn("isolation_event_binding_mismatch", self.validate(result, observed)["reasons"])
        observed["qualified_isolation"]["output_directory"] = record["output_directory"]
        observed["qualified_isolation"]["current_external_input_sha256"] = "b" * 64
        self.assertFalse(self.validate(result, observed)["reusable"])
        observed["qualified_isolation"]["current_external_input_sha256"] = "a" * 64
        record["isolation_mode"] = "copy_only"
        observed["isolation_mode"] = "copy_only"
        path.write_text(json.dumps(record))
        self.assertFalse(self.validate(result, observed)["reusable"])

    def test_forged_receipt_and_failed_command_cannot_pass(self):
        (self.root / "check.py").write_text("raise SystemExit(1)\n")
        result, observed = self.produce()
        path = self.root / result["record_path"]
        forged = json.loads(path.read_text())
        forged["exit_code"] = 0
        path.write_text(json.dumps(forged))
        self.assertFalse(self.validate(result, observed)["reusable"])

    def test_source_fixture_configuration_and_environment_invalidate(self):
        for name in ("check.py", "fixture.txt", "feature/workflow.md"):
            with self.subTest(name=name):
                result, observed = self.produce()
                path = self.root / name
                old = path.read_bytes()
                path.write_bytes(old + b"\n")
                invalid = self.validate(result, observed)
                self.assertFalse(invalid["reusable"])
                self.assertIn("input_snapshot_changed", invalid["reasons"])
                path.write_bytes(old)
        result, observed = self.produce()
        # The binding covers the variables the child actually receives. Changing
        # one of those still invalidates reuse; an unrelated host variable no
        # longer reaches the child, so it must not.
        with patch.dict(os.environ, {"TZ": "UTC-14"}):
            self.assertIn("toolchain_or_environment_changed", self.validate(result, observed)["reasons"])
        with patch.dict(os.environ, {"VERIFICATION_CHANGED": "yes"}):
            self.assertNotIn("toolchain_or_environment_changed", self.validate(result, observed)["reasons"])

    def test_missing_receipt_and_native_result_mismatch_fail_closed(self):
        result, observed = self.produce()
        observed["exit_code"] = 99
        self.assertFalse(self.validate(result, observed)["reusable"])
        (self.root / result["record_path"]).unlink()
        self.assertFalse(self.validate(result, observed)["reusable"])

    def test_file_and_directory_modes_invalidate_snapshot_identity(self):
        for name in ("fixture.txt", "feature"):
            with self.subTest(name=name):
                result, observed = self.produce()
                path = self.root / name
                original_mode = path.stat().st_mode & 0o777
                try:
                    path.chmod(original_mode ^ 0o010)
                    self.assertIn("input_snapshot_changed", self.validate(result, observed)["reasons"])
                finally:
                    path.chmod(original_mode)

    def test_empty_directory_changes_invalidate_snapshot_identity(self):
        result, observed = self.produce()
        (self.root / "new-empty-directory").mkdir()
        self.assertIn("input_snapshot_changed", self.validate(result, observed)["reasons"])

    def test_materialized_snapshot_preserves_empty_directories_and_executable_bits(self):
        (self.root / "empty-directory").mkdir(mode=0o750)
        (self.root / "fixture.txt").chmod(0o754)
        (self.root / "check.py").write_text(
            "from pathlib import Path\n"
            "assert Path('empty-directory').is_dir()\n"
            "assert Path('empty-directory').stat().st_mode & 0o777 == 0o750\n"
            "assert Path('fixture.txt').stat().st_mode & 0o777 == 0o754\n"
        )
        result, _ = self.produce()
        self.assertEqual(result["record"]["exit_code"], 0)
        self.assertTrue(result["record"]["snapshot_unchanged"])

    def test_snapshot_directory_mode_mutation_is_detected(self):
        (self.root / "check.py").write_text("from pathlib import Path\nPath('feature').chmod(0o700)\n")
        result, _ = self.produce()
        self.assertFalse(result["record"]["snapshot_unchanged"])

    def test_child_environment_excludes_host_credentials(self):
        canaries = {
            "SPECKIT_TEST_CANARY": "top-secret-value",
            "AWS_SECRET_ACCESS_KEY": "aws-canary",
            "GITHUB_TOKEN": "gh-canary",
            "NPM_TOKEN": "npm-canary",
        }
        with patch.dict(os.environ, canaries):
            with patch("speckit_pro_runner.verification_records.run_snapshot_command", wraps=run_snapshot_command) as launched:
                self.produce()
        environment = launched.call_args.args[2]
        for name, value in canaries.items():
            self.assertNotIn(name, environment, f"{name} leaked into the verification child environment")
            self.assertNotIn(value, environment.values())

    def test_child_home_is_relocated_away_from_the_operator_account(self):
        with patch("speckit_pro_runner.verification_records.run_snapshot_command", wraps=run_snapshot_command) as launched:
            result, _ = self.produce()
        environment = launched.call_args.args[2]
        outputs = result["record"]["output_directory"]
        self.assertEqual(outputs, environment["HOME"])
        self.assertNotEqual(str(Path.home()), environment["HOME"])
        for name in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME"):
            self.assertEqual(outputs, environment[name])

    def test_record_binds_effective_child_environment_after_output_relocation(self):
        with patch("speckit_pro_runner.verification_records.run_snapshot_command", wraps=run_snapshot_command) as launched:
            result, _ = self.produce()
        environment = launched.call_args.args[2]
        self.assertEqual(result["record"]["environment_sha256"], digest(environment))
        self.assertEqual(result["record"]["output_directory"], environment["SPECKIT_VERIFICATION_OUTPUT_DIR"])

    def test_output_relocation_is_bound_to_independent_observation(self):
        result, observed = self.produce()
        path = self.root / result["record_path"]
        record = json.loads(path.read_text())
        record["output_directory"] = str(self.root / "forged-output")
        path.write_text(json.dumps(record))
        self.assertIn("native_event_disagrees_with_receipt", self.validate(result, observed)["reasons"])

    def test_reserved_verification_cannot_launch_twice(self):
        result, _ = self.produce()
        with self.assertRaisesRegex(ValueError, "dispatch_already_started_no_relaunch"):
            execute_verification(self.root, {**self.inputs, "dispatch_id": result["record"]["dispatch_id"],
                                            "expected_run_id": self.run_id}, "apply")

    def test_snapshot_mutation_and_unknown_command_do_not_reuse(self):
        (self.root / "check.py").write_text("from pathlib import Path\np=Path('fixture.txt')\np.chmod(0o600)\np.write_text('mutated')\n")
        result, observed = self.produce()
        self.assertFalse(self.validate(result, observed)["reusable"])
        self.assertEqual((self.root / "fixture.txt").read_text(), "dirty untracked fixture")
        with self.assertRaises(ValueError):
            execute_verification(self.root, {**self.inputs, "command_id": "LINT_FIX"}, "apply")

    def test_verification_source_has_no_dynamic_or_shell_executable_findings(self):
        from speckit_pro_runner.gates.active_path_guard import repo_bash_python_findings

        source = Path(__file__).resolve().parents[3] / "speckit-pro/speckit_pro_runner/verification_records.py"
        self.assertEqual(repo_bash_python_findings("speckit-pro/speckit_pro_runner/verification_records.py", source.read_text()), [])

    def test_workflow_shell_jq_and_unsupported_executables_are_rejected(self):
        for command in ("bash -c true", "sh -c true", "jq . fixture.json", "env python3 check.py", "unqualified-tool check.py"):
            with self.subTest(command=command):
                (self.root / "feature/workflow.md").write_text("## PROJECT_COMMANDS\n```json\n" + json.dumps({"UNIT_TEST": command}) + "\n```\n")
                with self.assertRaisesRegex(ValueError, "ordinary native verification"):
                    project_command(self.root / "feature/workflow.md", "UNIT_TEST")

    def test_supported_tools_keep_literal_executable_arguments_and_environment(self):
        programs = ("python", "python3", "node", "npm", "npx", "pnpm", "yarn", "bun", "cargo", "go", "make", "pytest", "lint-imports", "uv", "ruff", "mypy")
        for program in programs:
            with self.subTest(program=program), patch("speckit_pro_runner.verification_records.shutil.which", side_effect=lambda name, **kwargs: f"/qualified-tools/{name}"), patch("speckit_pro_runner.verification_records.subprocess.Popen") as popen:
                process = popen.return_value.__enter__.return_value
                process.communicate.return_value = (b"ok", b"")
                process.returncode = 0
                environment = {"PATH": "/qualified-tools"}
                result = run_snapshot_command([program, "check", "one argument"], self.root, environment, 1)
                self.assertEqual(result, (0, b"ok", b"", True))
                self.assertEqual(popen.call_args.args[0], [f"/qualified-tools/{program}", "check", "one argument"])
                self.assertEqual(popen.call_args.kwargs["env"], environment)
                self.assertIs(popen.call_args.kwargs["shell"], False)
                self.assertNotIn("executable", popen.call_args.kwargs)

    def test_path_python_is_not_replaced_with_the_runner_interpreter(self):
        requested = "/qualified-tools/python3.11"
        with patch("speckit_pro_runner.verification_records.shutil.which", return_value=requested), patch("speckit_pro_runner.verification_records.subprocess.Popen") as popen:
            process = popen.return_value.__enter__.return_value
            process.communicate.return_value = (b"ok", b"")
            process.returncode = 0
            run_snapshot_command(["python3", "check.py"], self.root, {"PATH": "/qualified-tools"}, 1, expected_executable=requested)
            self.assertEqual(popen.call_args.args[0], [requested, "check.py"])
            self.assertNotIn("executable", popen.call_args.kwargs)

    def test_changed_or_relative_executable_resolution_cannot_launch(self):
        for resolved, expected in (("/different-tools/python3", "/qualified-tools/python3"), ("relative/python3", None)):
            with self.subTest(resolved=resolved), patch("speckit_pro_runner.verification_records.shutil.which", return_value=resolved), patch("speckit_pro_runner.verification_records.subprocess.Popen") as popen:
                with self.assertRaisesRegex(ValueError, "ordinary native verification"):
                    run_snapshot_command(["python3", "check.py"], self.root, {"PATH": "relative"}, 1, expected_executable=expected)
                popen.assert_not_called()

    def test_virtualenv_invocation_is_preserved_even_when_binary_target_is_shared(self):
        interpreter = self.root / "venv/bin/python3"
        interpreter.parent.mkdir(parents=True)
        interpreter.symlink_to(sys.executable)
        with patch("speckit_pro_runner.verification_records.shutil.which", return_value=str(interpreter)), patch("speckit_pro_runner.verification_records.subprocess.Popen") as popen:
            process = popen.return_value.__enter__.return_value
            process.communicate.return_value = (b"ok", b"")
            process.returncode = 0
            run_snapshot_command(["python3", "check.py"], self.root, {"PATH": str(interpreter.parent)}, 1, expected_executable=str(interpreter))
            self.assertEqual(popen.call_args.args[0], [str(interpreter), "check.py"])

    def test_process_directory_workflow_evidence_is_not_doubled_and_legacy_record_is_read(self):
        workflow = "docs/ai/specs/.process/workflow.md"
        # An in-flight run already holds the doubled evidence directory.
        (self.root / "docs/ai/specs/.process/.process/verification").mkdir(parents=True)
        (self.root / workflow).write_text((self.root / "feature/workflow.md").read_text())
        inputs = {"workflow_file": workflow, "command_id": "UNIT_TEST"}
        run_id = execution_control(self.root, {"workflow_file": workflow, "action": "start"}, "apply")["ledger"]["run_id"]
        execution_control(self.root, {"workflow_file": workflow, "action": "reserve", "dispatch_id": "verify-1",
                                      "kind": "verification", "expected_run_id": run_id}, "apply")
        result = execute_verification(self.root, {**inputs, "dispatch_id": "verify-1", "expected_run_id": run_id}, "apply")
        name = Path(result["record_path"]).name
        self.assertEqual(result["record_path"], f"docs/ai/specs/.process/verification/{name}")
        self.assertTrue((self.root / result["record_path"]).is_file())
        self.assertFalse([path for path in tree_bytes(self.root, workflow) if "verification" in path])
        current = validate_execution_record(self.root, {**inputs, "record_path": result["record_path"]})
        self.assertFalse([reason for reason in current["reasons"] if reason.startswith("unverifiable_record")])

        legacy = f"docs/ai/specs/.process/.process/verification/{name}"
        (self.root / result["record_path"]).rename(self.root / legacy)
        self.assertFalse([path for path in tree_bytes(self.root, workflow) if "verification" in path])
        self.assertTrue(is_runner_byproduct(legacy) and is_runner_byproduct(result["record_path"]))
        self.assertEqual(validate_execution_record(self.root, {**inputs, "record_path": legacy}), current)
        stray = f"docs/ai/specs/verification/{name}"
        (self.root / stray).parent.mkdir(parents=True)
        (self.root / legacy).rename(self.root / stray)
        self.assertIn("unverifiable_record: record_path is not this workflow's verification evidence",
                      validate_execution_record(self.root, {**inputs, "record_path": stray})["reasons"])


class RunnerRouteCase(unittest.TestCase):
    """Exercise actual request-envelope entrypoints in a temporary consumer repo."""

    def setUp(self):
        VerificationTests.setUp(self)
        (self.root / ".specify").mkdir()

    def call_runner(self, helper, mode, **inputs):
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[3] / "speckit-pro")
        binding = {"expected_run_id": self.run_id} if getattr(self, "run_id", None) else {}
        request = {"schema_version": "1.0", "helper_id": helper, "operation": helper,
                   "mode": mode, "inputs": {"workflow_file": "feature/workflow.md", **binding, **inputs}}
        process = subprocess.run([sys.executable, "-m", "speckit_pro_runner"], cwd=self.root,
                                 env=environment, input=json.dumps(request), text=True, capture_output=True)
        result = json.loads(process.stdout)
        if helper == "execution-control" and "ledger" in result["data"]:
            self.run_id = result["data"]["ledger"]["run_id"]
        return process.returncode, result


class RunnerDispatchTests(RunnerRouteCase):
    def test_ledger_and_verification_helpers_are_real_runner_routes(self):
        code, started = self.call_runner("execution-control", "apply", action="start")
        self.assertEqual(code, 0, started)
        code, denied = self.call_runner("execution-control", "read_only", action="reserve", dispatch_id="x", kind="implementation")
        self.assertEqual(code, 2, denied)
        code, reserved = self.call_runner("execution-control", "apply", action="reserve", dispatch_id="verify-1", kind="verification")
        self.assertEqual(code, 0, reserved)
        code, executed = self.call_runner("execute-verification", "apply", command_id="UNIT_TEST", dispatch_id="verify-1")
        self.assertEqual(code, 0, executed)
        data = executed["data"]
        code, validated = self.call_runner("validate-execution-record", "read_only", command_id="UNIT_TEST",
                                          record_path=data["record_path"], native_observation={**data["observation_material"], "native_event_id": "fixture-native-event"})
        self.assertEqual(code, 1, validated)
        self.assertFalse(validated["data"]["stdout_json"]["reusable"])

    def test_corrective_exception_is_a_real_runner_route(self):
        self.call_runner("execution-control", "apply", action="start")
        self.call_runner("execution-control", "apply", action="reserve", dispatch_id="fix-a", kind="corrective",
                         failure_invariant="FR-001")
        self.call_runner("execution-control", "apply", action="complete", dispatch_id="fix-a", outcome="failed")
        (self.root / "feature/spec.md").write_text("- FR-001: preserve data\n- FR-002: no secrets\n")
        code, bound = self.call_runner("execution-control", "apply", action="bind-invariants",
                                       spec_file="feature/spec.md")
        self.assertEqual(code, 0, bound)
        self.call_runner("execution-control", "apply", action="reserve", dispatch_id="fix-b", kind="corrective",
                         failure_invariant="FR-002")
        self.call_runner("execution-control", "apply", action="complete", dispatch_id="fix-b", outcome="failed")
        event = {"native_event_id": "operator-exception", "run_id": self.run_id,
                 "action": "corrective_exception_approved", "failure_invariant": "FR-001", "dispatch_id": "fix-c",
                 "failure_kind": "application", "refusal_reason": "corrective_run_budget_exhausted",
                 "scope_sha256": "a" * 64,
                 "spec_sha256": bound["data"]["ledger"]["invariant_binding"]["spec_sha256"]}
        code, granted = self.call_runner("execution-control", "apply", action="authorize-corrective-exception",
                                         dispatch_id="fix-c", failure_invariant="FR-001", scope_sha256="a" * 64,
                                         native_observation=event)
        self.assertEqual(code, 0, granted)
        self.assertEqual(granted["data"]["disposition"], "continue")
        self.assertEqual(granted["data"]["ledger"]["corrective_exception"]["dispatch_id"], "fix-c")

    def test_replan_epoch_is_a_real_runner_route(self):
        self.call_runner("execution-control", "apply", action="start")
        for dispatch_id, invariant in (("fix-a", "FR-001"), ("fix-b", "FR-002")):
            self.call_runner("execution-control", "apply", action="reserve", dispatch_id=dispatch_id,
                             kind="corrective", failure_invariant=invariant)
            self.call_runner("execution-control", "apply", action="complete", dispatch_id=dispatch_id,
                             outcome="failed")
        spec = self.root / "feature/spec.md"
        spec.write_text("- FR-001: preserve data\n- FR-002: no secrets\n- FR-003: explain refusals\n")
        event = {"native_event_id": "operator-replan", "run_id": self.run_id,
                 "action": "replan_epoch_approved", "spec_sha256": hashlib.sha256(spec.read_bytes()).hexdigest()}
        code, preview = self.call_runner("execution-control", "dry_run", action="begin-replan-epoch",
                                         spec_file="feature/spec.md", native_observation=event)
        self.assertEqual(code, 0, preview)
        code, rotated = self.call_runner("execution-control", "apply", action="begin-replan-epoch",
                                         spec_file="feature/spec.md", native_observation=event)
        self.assertEqual(code, 0, rotated)
        self.assertEqual(rotated["data"]["corrective_epoch"], 1)
        code, reserved = self.call_runner("execution-control", "apply", action="reserve", dispatch_id="fix-c",
                                          kind="corrective", failure_invariant="FR-003")
        self.assertEqual(code, 0, reserved)

    def test_class_correction_is_a_real_runner_route(self):
        self.call_runner("execution-control", "apply", action="start")
        (self.root / "feature/spec.md").write_text("- FR-001: preserve data\n- FR-002: no secrets\n")
        code, bound = self.call_runner("execution-control", "apply", action="bind-invariants",
                                       spec_file="feature/spec.md")
        self.assertEqual(code, 0, bound)
        for dispatch_id, invariant in (("fix-a", "FR-001"), ("fix-b", "FR-002")):
            self.call_runner("execution-control", "apply", action="reserve", dispatch_id=dispatch_id,
                             kind="corrective", failure_invariant=invariant)
            self.call_runner("execution-control", "apply", action="complete", dispatch_id=dispatch_id,
                             outcome="failed")
        failure_class = {"test_file": "tests/cli.test.ts", "failure_signature": "Test timed out in 5000ms",
                         "change_kind": "test_timeout"}
        event = {"native_event_id": "operator-class", "run_id": self.run_id,
                 "action": "corrective_exception_approved", "failure_invariant": "FR-001", "dispatch_id": "fix-c",
                 "failure_kind": "application", "refusal_reason": "failure_family_budget_exhausted",
                 "scope_sha256": "a" * 64, "failure_class": failure_class,
                 "spec_sha256": bound["data"]["ledger"]["invariant_binding"]["spec_sha256"]}
        code, granted = self.call_runner("execution-control", "apply", action="authorize-corrective-exception",
                                         dispatch_id="fix-c", failure_invariant="FR-001", scope_sha256="a" * 64,
                                         failure_class=failure_class, native_observation=event)
        self.assertEqual(code, 0, granted)
        self.call_runner("execution-control", "apply", action="complete", dispatch_id="fix-c", outcome="completed")
        code, admitted = self.call_runner("execution-control", "apply", action="reserve-class-correction",
                                          dispatch_id="fix-d", failure_class=failure_class)
        self.assertEqual(code, 0, admitted)
        self.assertEqual(admitted["data"]["disposition"], "continue")
        code, refused = self.call_runner("execution-control", "apply", action="reserve-class-correction",
                                         dispatch_id="fix-e", failure_class={**failure_class,
                                                                             "test_file": "src/cli.ts"})
        self.assertEqual(code, 2, refused)

    def test_increment_review_allowance_is_a_real_runner_route(self):
        (self.root / "feature/spec.md").write_text("- FR-001: preserve data\n- FR-002: no secrets\n")
        self.TASKS, self.OWNERSHIP = IncrementReviewAllowanceTests.TASKS, IncrementReviewAllowanceTests.OWNERSHIP
        IncrementReviewAllowanceTests.write_sidecar(self)
        self.call_runner("execution-control", "apply", action="start")
        for dispatch_id, invariant in (("fix-a", "FR-001"), ("fix-b", "FR-002")):
            self.call_runner("execution-control", "apply", action="reserve", dispatch_id=dispatch_id,
                             kind="corrective", failure_invariant=invariant)
            self.call_runner("execution-control", "apply", action="complete", dispatch_id=dispatch_id,
                             outcome="completed")
        code, admitted = self.call_runner("execution-control", "apply", action="reserve", dispatch_id="alpha-review",
                                          kind="corrective", failure_invariant="FR-001", spec_file="feature/spec.md",
                                          review_remediation={"tdd_unit": "alpha", "paths": ["src/alpha/core.py"]})
        self.assertEqual(code, 0, admitted)
        self.assertEqual(admitted["data"]["review_allowance"], "increment")

    def test_gate_remediation_allowance_is_a_real_runner_route(self):
        (self.root / "feature/spec.md").write_text("- FR-001: preserve data\n- FR-002: no secrets\n")
        self.call_runner("execution-control", "apply", action="start")
        for dispatch_id, invariant in (("fix-a", "FR-001"), ("fix-b", "FR-002")):
            self.call_runner("execution-control", "apply", action="reserve", dispatch_id=dispatch_id,
                             kind="corrective", failure_invariant=invariant)
            self.call_runner("execution-control", "apply", action="complete", dispatch_id=dispatch_id,
                             outcome="completed")
        code, admitted = self.call_runner("execution-control", "apply", action="reserve", dispatch_id="g6-fix",
                                          kind="corrective", failure_invariant="FR-001", spec_file="feature/spec.md",
                                          gate_remediation={"gate": "G6", "paths": ["feature/tasks.md"]})
        self.assertEqual(code, 0, admitted)
        self.assertEqual(admitted["data"]["remediation_allowance"], "gate")

    def test_metadata_only_correction_is_a_real_runner_route(self):
        (self.root / "feature/spec.md").write_text("- FR-001: preserve data\n- FR-002: no secrets\n")
        (self.root / "feature/plan.md").write_text("# Plan\n")
        (self.root / "feature/tasks.md").write_text(MetadataOnlyCorrectionTests.TASKS)
        commit_fixture(self.root)
        self.call_runner("execution-control", "apply", action="start")
        for dispatch_id, invariant in (("fix-a", "FR-001"), ("fix-b", "FR-002")):
            self.call_runner("execution-control", "apply", action="reserve", dispatch_id=dispatch_id,
                             kind="corrective", failure_invariant=invariant)
            self.call_runner("execution-control", "apply", action="complete", dispatch_id=dispatch_id,
                             outcome="completed")
        (self.root / "feature/tasks.md").write_text(MetadataOnlyCorrectionTests.CORRECTED)
        code, admitted = self.call_runner("execution-control", "apply", action="reserve", dispatch_id="verb-fix",
                                          kind="corrective", failure_invariant="FR-001", spec_file="feature/spec.md",
                                          metadata_only=True)
        self.assertEqual(code, 0, admitted)
        self.assertEqual((admitted["data"]["correction_allowance"], admitted["data"]["ledger"]["corrective_cycles"]),
                         ("metadata_only", 2))

    def test_stage_epoch_is_a_real_runner_route(self):
        self.call_runner("execution-control", "apply", action="start")
        for dispatch_id, invariant in (("fix-a", "FR-001"), ("fix-b", "FR-002")):
            self.call_runner("execution-control", "apply", action="reserve", dispatch_id=dispatch_id,
                             kind="corrective", failure_invariant=invariant)
            self.call_runner("execution-control", "apply", action="complete", dispatch_id=dispatch_id,
                             outcome="failed")
        (self.root / "feature/workflow.md").write_text(stage_workflow())
        code, preview = self.call_runner("execution-control", "dry_run", action="begin-stage-epoch",
                                         autopilot_args=["--stage", "implement"])
        self.assertEqual(code, 0, preview)
        code, opened = self.call_runner("execution-control", "apply", action="begin-stage-epoch",
                                        autopilot_args=["--stage", "implement"])
        self.assertEqual(code, 0, opened)
        self.assertEqual((opened["data"]["corrective_epoch"], opened["data"]["stage_epoch_opened"]), (1, True))
        code, reserved = self.call_runner("execution-control", "apply", action="reserve", dispatch_id="fix-c",
                                          kind="corrective", failure_invariant="FR-001")
        self.assertEqual(code, 0, reserved)

    def test_a_deferral_is_expected_failure_on_the_runner_envelope(self):
        (self.root / "feature/spec.md").write_text("- FR-001: preserve data\n")
        self.call_runner("execution-control", "apply", action="start")
        self.call_runner("execution-control", "apply", action="reserve", dispatch_id="fix-a",
                         kind="corrective", failure_invariant="FR-001")
        self.call_runner("execution-control", "apply", action="complete", dispatch_id="fix-a", outcome="completed")
        code, refused = self.call_runner("execution-control", "apply", action="reserve", dispatch_id="fix-b",
                                         kind="corrective", failure_invariant="FR-001")
        self.assertEqual((code, refused["status"]), (1, "expected_failure"), refused)
        self.assertEqual(refused["data"]["disposition"], "defer")
        self.assertEqual(refused["data"]["deferred"]["unit"], "FR-001")

    def test_task_metadata_helper_is_registered_and_read_only(self):
        (self.root / "feature/tasks.md").write_text("# Tasks\n## Phase 1: Setup\n- [ ] T001 Create fixture in `fixture.txt`\n")
        (self.root / "feature/spec.md").write_text("# Spec\n")
        (self.root / "feature/plan.md").write_text("# Plan\n")
        code, result = self.call_runner("validate-task-execution", "read_only", tasks_file="feature/tasks.md", action="fingerprints")
        self.assertEqual(code, 0, result)
        self.assertIn("fingerprints", result["data"]["stdout_json"])
        code, result = self.call_runner("validate-task-execution", "apply", tasks_file="feature/tasks.md")
        self.assertEqual(code, 2, result)


class RunnerFormatConvergenceTests(RunnerRouteCase):
    """A shrinking failing set in a runner-executed test format continues a corrective family."""

    def test_go_test_output_admits_a_converging_correction_through_the_real_runner_routes(self):
        """End to end: `go test -v` output the runner executed lets a shrinking failing set continue a family."""
        self.assert_shrinking_failures_continue(
            "go", "go-test-v.txt", "go-test-v-shrunk.txt", ["TestGroup", "TestGroup/inner_bad"])

    def test_cargo_test_output_admits_a_converging_correction_through_the_real_runner_routes(self):
        """End to end: `cargo test` output the runner executed lets a shrinking failing set continue a family."""
        self.assert_shrinking_failures_continue(
            "cargo", "cargo-test.txt", "cargo-test-shrunk.txt", ["tests::nested_path_bad"])

    def assert_shrinking_failures_continue(self, format_name, first_fixture, shrunk_fixture, shrunk_failing):
        (self.root / "feature/spec.md").write_text("- FR-001: preserve data\n")
        self.call_runner("execution-control", "apply", action="start")

        def verify(dispatch_id, fixture):
            (self.root / "check.py").write_text("import sys\nsys.stdout.write(" + repr(runner_output(fixture))
                                                + ")\nsys.exit(1)\n")
            self.call_runner("execution-control", "apply", action="reserve", dispatch_id=dispatch_id,
                             kind="verification")
            code, executed = self.call_runner("execute-verification", "apply", command_id="UNIT_TEST",
                                              dispatch_id=dispatch_id)
            self.assertEqual(code, 0, executed)
            self.call_runner("execution-control", "apply", action="complete", dispatch_id=dispatch_id,
                             outcome="failed")

        def correct(dispatch_id):
            code, result = self.call_runner("execution-control", "apply", action="reserve", dispatch_id=dispatch_id,
                                            kind="corrective", failure_invariant="FR-001")
            self.assertEqual(code, 0, result)
            if result["data"]["disposition"] == "continue":
                self.call_runner("execution-control", "apply", action="complete", dispatch_id=dispatch_id,
                                 outcome="completed")
            return result["data"]

        verify("verify-1", first_fixture)
        self.assertEqual(correct("fix-1")["disposition"], "continue")
        verify("verify-2", shrunk_fixture)
        second = correct("fix-2")
        self.assertEqual(second["disposition"], "continue", second)
        self.assertEqual((second["progress"]["admitted"], second["progress"]["change"]), (True, "shrank"))
        ledger = second["ledger"]
        self.assertEqual(ledger["corrective_cycles"], 1)
        self.assertEqual(ledger["dispatches"]["verify-1"]["failing_checks"]["format"], format_name)
        self.assertEqual(ledger["dispatches"]["verify-2"]["failing_checks"]["failing"], shrunk_failing)


class DockerVerificationTests(VerificationTests):
    """Only these Docker-specific methods run; host methods have their own class."""

    def setUp(self):
        super().setUp()
        (self.root / "feature/workflow.md").write_text('## PROJECT_COMMANDS\n```json\n{"UNIT_TEST":"python3 check.py"}\n```\n')
        self.inputs["docker"] = {"executable": "/usr/local/bin/docker", "endpoint": "unix:///tmp/docker.sock",
                                 "base_image": "python@sha256:" + "a" * 64, "output_contract": "streams_only"}

    def test_docker_directory_wide_add_never_stages_evidence(self):
        self.test_directory_wide_add_never_stages_ledger_or_verification_evidence()

    def test_docker_dry_run_does_not_resolve_host_tools_or_contact_daemon(self):
        with patch("speckit_pro_runner.verification_records.project_program", side_effect=AssertionError("host tool used")):
            result = execute_verification(self.root, self.inputs, "dry_run")
        self.assertEqual(result["argv"], ["python3", "check.py"])
        self.assertFalse(result["authorization_granted"] or result["writes_state"] or result["reusable"])

    def test_docker_requires_explicit_supported_configuration(self):
        for change in ({"output_contract": "files"}, {"extra": True}, {"base_image": "python:latest"},
                       {"endpoint": "tcp://remote:2375"}, {"executable": "docker"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                execute_verification(self.root, {**self.inputs, "docker": {**self.inputs["docker"], **change}}, "dry_run")

    def test_docker_requires_ledger_reservation_before_daemon_access(self):
        from speckit_pro_runner import verification_docker_workflow as workflow_backend
        with patch.object(workflow_backend, "DockerClient") as client, self.assertRaises(ValueError):
            execute_verification(self.root, {**self.inputs, "dispatch_id": "not-reserved"}, "apply")
        client.assert_not_called()

    def test_docker_receipt_is_image_bound_and_cannot_authorize_reuse_or_relaunch(self):
        from speckit_pro_runner import verification_docker_workflow as workflow_backend
        image_id = "sha256:" + "b" * 64
        backend = {"completed": True, "exit_code": 0, "stdout": b"verified\n", "stderr": b"",
                   "input_readback": {"verified": True},
                   "image_id": image_id, "base_image": {"Id": "sha256:" + "c" * 64},
                   "cleanup_confirmed": True, "image_tag_cleanup_confirmed": True, "reusable": False}
        with patch.object(workflow_backend, "DockerClient") as client, \
             patch.object(workflow_backend, "execute_image", return_value=backend) as launch:
            client.return_value.events = []
            result, observation = self.produce()
            record = result["record"]
            self.assertEqual(record["schema_version"], "docker-verification-record/v1")
            self.assertEqual(record["toolchain"]["image_id"], image_id)
            self.assertNotIn("executable_sha256", record["toolchain"])
            self.assertTrue(record["completed"] and record["inputs_unchanged"])
            self.assertTrue(record["input_snapshot_verified"])
            self.assertFalse(self.validate(result, observation)["reusable"])
            evidence = self.root / result["evidence_path"]
            self.assertTrue(evidence.is_file())
            self.assertEqual((evidence.parent / "stdout").read_bytes(), b"verified\n")
            self.assertEqual(record["evidence_sha256"], workflow_backend.sha(evidence.read_bytes()))
            schema = json.loads((Path(workflow_backend.__file__).parent / "contracts/docker-verification-record.schema.json").read_text())
            self.assertEqual(set(record), set(schema["required"]))
            self.assertEqual(set(record), set(schema["properties"]))
            with self.assertRaisesRegex(ValueError, "dispatch_already_started_no_relaunch"):
                execute_verification(self.root, {**self.inputs, "dispatch_id": record["dispatch_id"],
                                                "expected_run_id": self.run_id}, "apply")
            client.assert_called_once()
            launch.assert_called_once()

    def test_docker_failed_preparation_retains_evidence_and_consumes_reservation(self):
        from speckit_pro_runner import verification_docker_workflow as workflow_backend
        with patch.object(workflow_backend, "DockerClient", side_effect=ValueError("daemon unavailable")):
            result, _ = self.produce()
        self.assertFalse(result["record"]["completed"] or result["reusable"])
        self.assertIsNone(result["record"]["toolchain"]["image_id"])
        self.assertTrue((self.root / result["evidence_path"]).is_file())
        ledger_file = next((self.root / "feature/.process/execution-control").glob("*.json"))
        evidence = json.loads(ledger_file.read_text())["dispatches"][result["record"]["dispatch_id"]]["failing_checks"]
        self.assertEqual((evidence["command_id"], evidence["format"], evidence["failing"]), ("UNIT_TEST", "unparsed", None))
        with patch.object(workflow_backend, "DockerClient") as client, \
             self.assertRaisesRegex(ValueError, "dispatch_already_started_no_relaunch"):
            execute_verification(self.root, {**self.inputs, "dispatch_id": result["record"]["dispatch_id"],
                                            "expected_run_id": self.run_id}, "apply")
        client.assert_not_called()

    def test_docker_command_cannot_silently_rewrite_a_host_executable(self):
        for command in (f"{sys.executable} check.py", "sh -c true", "python3 ../outside.py", "python3 check.py\u0000bad"):
            with self.subTest(command=command), self.assertRaises(ValueError):
                (self.root / "feature/workflow.md").write_text("## PROJECT_COMMANDS\n```json\n" + json.dumps({"UNIT_TEST": command}) + "\n```\n")
                execute_verification(self.root, self.inputs, "dry_run")


class UnknownDispatchUnitScopeTests(_ExecutionControlFixture, unittest.TestCase):
    """An unknown dispatch outcome blocks only its own unit; the runner reconciles it from git state (issue 831)."""

    TASKS = ("## Phase 3: Stories\n- [ ] T001 Build the alpha core\n- [ ] T002 Build the alpha edge\n"
             + "- [ ] T003 Build the beta increment\n")
    OWNERSHIP = {"T001": ("alpha", ["src/alpha"]), "T002": ("alpha", ["src/alpha"]), "T003": ("beta", ["src/beta"])}
    BLOCKED = "unknown_dispatch_blocks_unit"

    def setUp(self):
        super().setUp()
        feature = self.root / "feature"
        (feature / ".process").mkdir()
        (feature / "plan.md").write_text("plan\n")
        (feature / "tasks.md").write_text(self.TASKS)
        tasks = {task_id: {"capability_group": "stories", "depends_on": [], "owns": owns, "tdd_unit": unit}
                 for task_id, (unit, owns) in self.OWNERSHIP.items()}
        metadata = {"schema_version": "task-execution.v1",
                    "fingerprints": fingerprints((feature / "spec.md").read_text(), "plan\n", self.TASKS),
                    "tasks": tasks}
        (feature / ".process/task-execution.json").write_text(json.dumps(metadata))
        for relative in ("src/alpha/core.py", "src/beta/core.py"):
            (self.root / relative).parent.mkdir(parents=True, exist_ok=True)
            (self.root / relative).write_text("VALUE = 0\n")
        commit_fixture(self.root)
        self.invoke("start")

    def dispatch(self, dispatch_id, unit, outcome=None):
        result = self.invoke("reserve", dispatch_id=dispatch_id, kind="implementation", tdd_units=[unit])
        if outcome is not None:
            result = self.invoke("complete", dispatch_id=dispatch_id, outcome=outcome)
        return result

    def reconcile(self, dispatch_id, classification, **extra):
        return self.invoke("reconcile-unit", dispatch_id=dispatch_id, spec_file="feature/spec.md",
                           classification=classification, **extra)

    def check_tasks(self, *task_ids):
        path = self.root / "feature/tasks.md"
        text = path.read_text()
        for task_id in task_ids:
            text = text.replace(f"- [ ] {task_id}", f"- [x] {task_id}")
        path.write_text(text)

    def test_an_unknown_outcome_leaves_independent_units_dispatchable(self):
        self.dispatch("alpha-1", "alpha", "unknown")
        status = self.invoke("status", mode="read_only")
        self.assertEqual((status["disposition"], status["reasons"]), ("continue", []))
        self.assertEqual(status["unknown_dispatch_ids"], ["alpha-1"])
        beta = self.dispatch("beta-1", "beta")
        self.assertEqual((beta["disposition"], beta["reasons"]), ("continue", []))
        self.invoke("complete", dispatch_id="beta-1", outcome="completed")
        for label, request in {
                "same unit": {"kind": "implementation", "tdd_units": ["alpha"]},
                "overlapping units": {"kind": "implementation", "tdd_units": ["beta", "alpha"]},
                "review of the unit": {"kind": "corrective", "failure_invariant": "FR-001", "spec_file": "feature/spec.md",
                                       "review_remediation": {"tdd_unit": "alpha", "paths": ["src/alpha/core.py"]}},
                "unscoped work": {"kind": "implementation"}}.items():
            with self.subTest(label):
                blocked = self.invoke("reserve", dispatch_id="next-" + label.replace(" ", "-"), **request)
                self.assertEqual((blocked["disposition"], blocked["reasons"], blocked["blocked_by"]),
                                 ("checkpoint_required", [self.BLOCKED], ["alpha-1"]))
                self.assertNotIn("next-" + label.replace(" ", "-"), blocked["ledger"]["dispatches"])
        corrective = self.invoke("reserve", dispatch_id="beta-fix", kind="corrective", failure_invariant="FR-002")
        self.assertEqual(corrective["disposition"], "continue")

    def test_an_unscoped_unknown_dispatch_still_blocks_all_new_dispatch(self):
        self.invoke("reserve", dispatch_id="worker", kind="implementation")
        self.invoke("complete", dispatch_id="worker", outcome="unknown")
        blocked = self.dispatch("beta-1", "beta")
        self.assertEqual((blocked["disposition"], blocked["reasons"]), ("checkpoint_required", [self.BLOCKED]))
        refused = self.reconcile("worker", "no_effect")
        self.assertEqual(refused["reasons"], ["unit_not_reconcilable"])

    def test_no_effect_marks_the_dispatch_failed_and_allows_a_redispatch_with_no_parent_event(self):
        self.dispatch("alpha-1", "alpha", "unknown")
        (self.root / "src/beta/core.py").write_text("VALUE = 1\n")
        result = self.reconcile("alpha-1", "no_effect")
        record = result["ledger"]["dispatches"]["alpha-1"]
        self.assertEqual((result["disposition"], result["reconciled"], result["relaunch_allowed"]),
                         ("continue", "no_effect", True))
        self.assertEqual((record["outcome"], record["reconciled_as"], record["changed_paths"]), ("failed", "no_effect", []))
        self.assertNotIn("resolution_event_id", record)
        self.assertNotIn("worktree_before", record)
        again = self.dispatch("alpha-2", "alpha")
        self.assertEqual((again["disposition"], again["reasons"]), ("continue", []))
        schema = json.loads(SCHEMA_PATH.read_text())
        self.assertEqual(json_schema_failures(again["ledger"], schema, schema, "ledger"), [])

    def test_partial_changes_need_a_verification_pass_before_the_unit_is_released(self):
        self.dispatch("alpha-1", "alpha", "unknown")
        (self.root / "src/alpha/core.py").write_text("VALUE = 1\n")
        result = self.reconcile("alpha-1", "partial")
        record = result["ledger"]["dispatches"]["alpha-1"]
        self.assertEqual((result["reconciled"], result["verification_required"]), ("partial", True))
        self.assertEqual((record["outcome"], record["reconciliation"]["class"], record["reconciliation"]["paths"]),
                         ("unknown", "partial", ["src/alpha/core.py"]))
        self.assertEqual(self.dispatch("alpha-2", "alpha")["reasons"], [self.BLOCKED])
        self.assertEqual(self.invoke("complete", dispatch_id="alpha-1", outcome="failed")["reasons"],
                         ["missing_independent_native_result"])
        self.invoke("reserve", dispatch_id="verify-1", kind="verification", verifies_dispatch_id="alpha-1")
        early = self.invoke("complete", dispatch_id="alpha-1", outcome="failed", verification_dispatch_id="verify-1")
        self.assertEqual(early["reasons"], ["unit_verification_not_completed"])
        self.invoke("begin-verification", dispatch_id="verify-1")
        self.invoke("complete", dispatch_id="verify-1", outcome="completed")
        wrong = self.invoke("complete", dispatch_id="alpha-1", outcome="completed", verification_dispatch_id="verify-1")
        self.assertEqual(wrong["reasons"], ["unit_resolution_mismatch"])
        resolved = self.invoke("complete", dispatch_id="alpha-1", outcome="failed", verification_dispatch_id="verify-1")
        item = resolved["ledger"]["dispatches"]["alpha-1"]
        self.assertEqual((resolved["disposition"], item["outcome"], item["verified_by"]), ("continue", "failed", "verify-1"))
        self.assertEqual(self.dispatch("alpha-2", "alpha")["disposition"], "continue")
        schema = json.loads(SCHEMA_PATH.read_text())
        self.assertEqual(json_schema_failures(resolved["ledger"], schema, schema, "ledger"), [])

    def test_complete_changes_with_every_unit_task_checked_resolve_as_completed_after_verification(self):
        self.dispatch("alpha-1", "alpha", "unknown")
        (self.root / "src/alpha/core.py").write_text("VALUE = 1\n")
        self.check_tasks("T001", "T002")
        result = self.reconcile("alpha-1", "complete")
        self.assertEqual((result["reconciled"], result["verification_required"]), ("complete", True))
        self.invoke("reserve", dispatch_id="verify-1", kind="verification", verifies_dispatch_id="alpha-1")
        self.invoke("begin-verification", dispatch_id="verify-1")
        self.invoke("complete", dispatch_id="verify-1", outcome="completed")
        resolved = self.invoke("complete", dispatch_id="alpha-1", outcome="completed", verification_dispatch_id="verify-1")
        item = resolved["ledger"]["dispatches"]["alpha-1"]
        self.assertEqual((item["outcome"], item["changed_paths"], item["verified_by"]),
                         ("completed", ["src/alpha/core.py"], "verify-1"))
        schema = json.loads(SCHEMA_PATH.read_text())
        self.assertEqual(json_schema_failures(resolved["ledger"], schema, schema, "ledger"), [])

    def test_a_forged_classification_fails_closed(self):
        self.dispatch("alpha-1", "alpha", "unknown")
        (self.root / "src/alpha/core.py").write_text("VALUE = 1\n")
        before = self.invoke("status", mode="read_only")["ledger"]["dispatches"]
        for claim in ("no_effect", "complete"):
            with self.subTest(claim=claim):
                forged = self.reconcile("alpha-1", claim)
                self.assertEqual((forged["disposition"], forged["reasons"]), ("checkpoint_required", ["unit_classification_mismatch"]))
                self.assertEqual(forged["ledger"]["dispatches"], before)
        for bad in ("finished", None, True):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.reconcile("alpha-1", bad)
        with self.assertRaises(ValueError):
            self.reconcile("alpha-1", "partial", native_observation={"native_event_id": "x"})
        self.assertEqual(self.reconcile("alpha-1", "partial")["reconciled"], "partial")
        unnamed = self.invoke("reserve", dispatch_id="verify-x", kind="verification", verifies_dispatch_id="beta-none")
        self.assertEqual((unnamed["disposition"], unnamed["reasons"]), ("checkpoint_required", [self.BLOCKED]))
        with self.assertRaises(ValueError):
            self.invoke("reserve", dispatch_id="verify-y", kind="implementation", tdd_units=["beta"],
                            verifies_dispatch_id="alpha-1")

    def test_missing_evidence_or_other_units_changes_never_reclassify(self):
        self.dispatch("alpha-1", "alpha", "unknown")
        (self.root / "src/beta/core.py").write_text("VALUE = 2\n")
        self.assertEqual(self.reconcile("alpha-1", "partial")["reasons"], ["unit_classification_mismatch"])
        (self.root / "feature/plan.md").write_text("plan changed\n")
        self.assertEqual(self.reconcile("alpha-1", "no_effect")["reasons"], ["ownership_evidence_stale"])
        (self.root / "feature/plan.md").write_text("plan\n")
        self.assertEqual(self.reconcile("alpha-1", "no_effect")["reconciled"], "no_effect")
        with self.assertRaises(ValueError):
            self.invoke("reconcile-unit", dispatch_id="alpha-1", classification="no_effect")

    def test_verifying_one_reconciled_unit_is_not_blocked_by_another_units_unknown_dispatch(self):
        self.dispatch("alpha-1", "alpha", "unknown")
        self.dispatch("beta-1", "beta", "unknown")
        (self.root / "src/alpha/core.py").write_text("VALUE = 1\n")
        (self.root / "src/beta/core.py").write_text("VALUE = 1\n")
        for dispatch_id in ("alpha-1", "beta-1"):
            self.assertEqual(self.reconcile(dispatch_id, "partial")["reconciled"], "partial")
        for unit in ("alpha", "beta"):
            verified = self.invoke("reserve", dispatch_id=f"verify-{unit}", kind="verification",
                                   verifies_dispatch_id=f"{unit}-1")
            self.assertEqual((verified["disposition"], verified["reasons"]), ("continue", []))
        self.invoke("begin-verification", dispatch_id="verify-alpha")
        self.assertEqual(self.invoke("begin-verification", dispatch_id="verify-beta")["disposition"], "continue")
        self.invoke("complete", dispatch_id="verify-alpha", outcome="unknown")
        blocked = self.invoke("reserve", dispatch_id="alpha-2", kind="implementation", tdd_units=["alpha"])
        self.assertEqual(blocked["blocked_by"], ["alpha-1", "verify-alpha"])
        self.invoke("complete", dispatch_id="verify-beta", outcome="completed")
        resolved = self.invoke("complete", dispatch_id="beta-1", outcome="failed", verification_dispatch_id="verify-beta")
        self.assertEqual(resolved["ledger"]["dispatches"]["beta-1"]["outcome"], "failed")
        self.assertEqual(self.dispatch("beta-2", "beta")["disposition"], "continue")

    def test_tampered_reconciliation_records_fail_validation(self):
        self.dispatch("alpha-1", "alpha", "unknown")
        (self.root / "src/alpha/core.py").write_text("VALUE = 1\n")
        self.reconcile("alpha-1", "partial")
        self.invoke("reserve", dispatch_id="verify-1", kind="verification", verifies_dispatch_id="alpha-1")
        path = self.root / self.invoke("status", mode="read_only")["ledger_path"]
        valid = path.read_bytes()
        tampers = {
            "unknown class": lambda ledger: ledger["dispatches"]["alpha-1"]["reconciliation"].update({"class": "no_effect"}),
            "unsorted paths": lambda ledger: ledger["dispatches"]["alpha-1"]["reconciliation"].update({"paths": ["b", "a"]}),
            "verified without a verifier": lambda ledger: ledger["dispatches"]["alpha-1"].update(verified_by="verify-1"),
            "verifier for nothing": lambda ledger: ledger["dispatches"]["verify-1"].update(verifies="beta-none"),
            "no-effect with a record": lambda ledger: ledger["dispatches"]["alpha-1"].update(reconciled_as="no_effect"),
            "verifier that is not verification": lambda ledger: ledger["dispatches"]["verify-1"].update(kind="corrective"),
        }
        for name, tamper in tampers.items():
            with self.subTest(tamper=name):
                ledger = json.loads(valid)
                tamper(ledger)
                path.write_text(json.dumps(ledger), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.invoke("status", mode="read_only")
        path.write_bytes(valid)
        self.assertEqual(self.invoke("status", mode="read_only")["unknown_dispatch_ids"], ["alpha-1"])

    def test_operator_native_resolution_of_an_unknown_dispatch_still_works(self):
        self.dispatch("alpha-1", "alpha", "unknown")
        event = {"native_event_id": "recovered", "run_id": self.run_id, "dispatch_id": "alpha-1",
                 "action": "dispatch_result", "outcome": "completed"}
        resolved = self.invoke("complete", dispatch_id="alpha-1", outcome="completed", native_observation=event)
        self.assertEqual(resolved["ledger"]["dispatches"]["alpha-1"]["outcome"], "completed")


class UnknownDispatchGuidanceTests(unittest.TestCase):
    """Both hosts tell the lead to reconcile an unknown outcome per unit instead of asking the operator (issue 831)."""

    GUIDANCE = ("skills/speckit-autopilot/references/execution-efficiency.md",
                "skills/speckit-autopilot/references/error-recovery.md",
                "skills/speckit-autopilot/references/phase-execution.md",
                "codex-skills/speckit-autopilot/SKILL.md",
                "codex-skills/speckit-autopilot/references/phase-execution-codex.md",
                "codex-skills/speckit-autopilot/references/error-recovery-codex.md")

    def test_every_host_guide_names_the_unit_scoped_reconciliation(self):
        root = Path(__file__).resolve().parents[3] / "speckit-pro"
        for relative in self.GUIDANCE:
            with self.subTest(guide=relative):
                text = " ".join((root / relative).read_text(encoding="utf-8").split())
                self.assertIn("reconcile-unit", text)
                self.assertNotIn("Unknown effects require a checkpoint", text)
                self.assertNotIn("Unknown effects require an honest checkpoint", text)


class AgentApprovalTests(_ExecutionControlFixture, unittest.TestCase):
    """An agent issues capped approvals the runner proves itself, with no operator event (issue 830)."""

    TASKS = MetadataOnlyCorrectionTests.TASKS
    CORRECTED = MetadataOnlyCorrectionTests.CORRECTED

    def setUp(self):
        super().setUp()
        (self.root / "feature/plan.md").write_text("# Plan\n")
        (self.root / "feature/tasks.md").write_text(self.TASKS)

    def schema_failures(self, ledger):
        schema = json.loads(SCHEMA_PATH.read_text())
        return json_schema_failures(ledger, schema, schema, "ledger")

    def fail_owner(self, dispatch_id, invariant, event_id):
        reservation = self.invoke("reserve", dispatch_id=dispatch_id, kind="corrective",
                                  failure_invariant=invariant)["reservation_id"]
        self.invoke("reconcile", dispatch_id=dispatch_id)
        self.invoke("complete", dispatch_id=dispatch_id, outcome="failed", native_observation={
            "native_event_id": event_id, "run_id": self.run_id, "dispatch_id": dispatch_id,
            "action": "dispatch_result", "outcome": "failed"})
        return reservation

    def agent_retry(self, dispatch_id, owner, reservation, **changes):
        request = {"dispatch_id": dispatch_id, "reservation_id": reservation, "failed_dispatch_id": owner,
                   "agent_authorized": True, "failure_kind": "infrastructure", **changes}
        return self.invoke("authorize-corrective-retry", **request)

    def test_an_agent_authorizes_one_infrastructure_retry_with_no_operator_event(self):
        self.invoke("start")
        first = self.fail_owner("owner", "FR-001", "host-auth-error")
        second = self.fail_owner("other", "FR-002", "host-timeout")
        retry = self.agent_retry("owner-retry", "owner", first)
        record = retry["ledger"]["dispatches"]["owner-retry"]
        self.assertEqual((retry["disposition"], retry["ledger"]["corrective_cycles"]), ("continue", 2))
        self.assertEqual((record["recovery_of"], record["failure_event_id"], record["operator_recovery_event_id"]),
                         ("owner", "host-auth-error", "agent-recovery:owner-retry"))
        self.assertEqual(self.schema_failures(retry["ledger"]), [])
        self.invoke("complete", dispatch_id="owner-retry", outcome="completed")
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")
        with self.assertRaisesRegex(ValueError, "agent-authorized corrective retry approvals are spent"):
            self.agent_retry("other-retry", "other", second)
        operator = self.invoke("authorize-corrective-retry", dispatch_id="other-retry", reservation_id=second,
                               failed_dispatch_id="other", native_observation={
                                   "native_event_id": "operator-message", "run_id": self.run_id,
                                   "action": "corrective_retry_approved", "failed_dispatch_id": "other",
                                   "failed_native_event_id": "host-timeout", "retry_dispatch_id": "other-retry",
                                   "reservation_id": second, "failure_kind": "infrastructure"})
        self.assertEqual(operator["disposition"], "continue")

    def test_an_agent_retry_fails_closed_without_the_runners_own_proof(self):
        self.invoke("start")
        reservation = self.invoke("reserve", dispatch_id="owner", kind="corrective",
                                  failure_invariant="FR-001")["reservation_id"]
        self.invoke("reserve", dispatch_id="other", kind="corrective", failure_invariant="FR-002")
        self.invoke("complete", dispatch_id="owner", outcome="failed")
        path = self.root / self.invoke("status", mode="read_only")["ledger_path"]
        before = path.read_bytes()
        cases = {"no native resolution of the failure": {},
                 "an application failure": {"failure_kind": "application"},
                 "no failure kind": {"failure_kind": None},
                 "an operator event beside the flag": {"native_observation": {"native_event_id": "x"}},
                 "a flag that is not true": {"agent_authorized": "yes"},
                 "another reservation": {"reservation_id": "other-reservation"}}
        for name, changes in cases.items():
            with self.subTest(case=name), self.assertRaises(ValueError):
                self.agent_retry("owner-retry", "owner", reservation, **changes)
            self.assertEqual(path.read_bytes(), before)
        with self.assertRaisesRegex(ValueError, "reserved for agent approvals"):
            self.invoke("authorize-corrective-retry", dispatch_id="owner-retry", reservation_id=reservation,
                        failed_dispatch_id="owner", native_observation={
                            "native_event_id": "agent-recovery:owner-retry", "run_id": self.run_id,
                            "action": "corrective_retry_approved", "failed_dispatch_id": "owner",
                            "failed_native_event_id": "x", "retry_dispatch_id": "owner-retry",
                            "reservation_id": reservation, "failure_kind": "infrastructure"})

    def test_forged_agent_approval_records_fail_validation(self):
        self.invoke("start")
        reservation = self.fail_owner("owner", "FR-001", "host-auth-error")
        self.invoke("reserve", dispatch_id="other", kind="corrective", failure_invariant="FR-002")
        retry = self.agent_retry("owner-retry", "owner", reservation)
        path = self.root / retry["ledger_path"]
        valid = path.read_bytes()
        tampers = {
            "event for another dispatch": lambda ledger: ledger["dispatches"]["owner-retry"].update(
                operator_recovery_event_id="agent-recovery:someone-else"),
            "second agent retry": lambda ledger: ledger["dispatches"].update(
                {"forged": {**ledger["dispatches"]["owner-retry"], "recovery_of": "other",
                            "operator_recovery_event_id": "agent-recovery:forged"}}),
        }
        for name, tamper in tampers.items():
            with self.subTest(tamper=name):
                ledger = json.loads(valid)
                tamper(ledger)
                path.write_text(json.dumps(ledger), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.invoke("status", mode="read_only")
        path.write_bytes(valid)
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")

    def plan_sidecar(self, plan="# Plan\n"):
        feature = self.root / "feature"
        (feature / "plan.md").write_text(plan)
        sources = [(feature / name).read_text() for name in ("spec.md", "plan.md", "tasks.md")]
        (feature / ".process").mkdir(exist_ok=True)
        (feature / ".process/task-execution.json").write_text(json.dumps({
            "schema_version": "task-execution.v1", "fingerprints": fingerprints(*sources), "tasks": {}}))

    def start_bound(self):
        spec = self.root / "feature/spec.md"
        text = spec.read_text()
        spec.unlink()
        self.invoke("start")
        spec.write_text(text)
        self.invoke("bind-invariants", spec_file="feature/spec.md")

    def spend_and_defer(self, suffix):
        for dispatch_id, invariant in ((f"fix-a{suffix}", "FR-001"), (f"fix-b{suffix}", "FR-002")):
            self.invoke("reserve", dispatch_id=dispatch_id, kind="corrective", failure_invariant=invariant)
            self.invoke("complete", dispatch_id=dispatch_id, outcome="failed")
        deferred = self.invoke("reserve", dispatch_id=f"fix-c{suffix}", kind="corrective", failure_invariant="FR-001")
        self.assertEqual(deferred["disposition"], "defer")

    def agent_replan(self, mode="apply"):
        return self.invoke("begin-replan-epoch", mode=mode, spec_file="feature/spec.md", agent_authorized=True)

    def open_first_epoch(self):
        """An operator re-plan opens the first epoch, which records the planning fingerprints an agent later compares."""
        self.plan_sidecar()
        self.start_bound()
        self.spend_and_defer("")
        digest = hashlib.sha256((self.root / "feature/spec.md").read_bytes()).hexdigest()
        opened = self.invoke("begin-replan-epoch", spec_file="feature/spec.md", native_observation={
            "native_event_id": "operator-replan", "run_id": self.run_id, "action": "replan_epoch_approved",
            "spec_sha256": digest})
        self.assertIn("planning_fingerprints", opened["ledger"]["invariant_binding"])

    def test_an_agent_opens_a_replan_epoch_after_the_tasks_rerun_and_stops_at_the_cap(self):
        self.open_first_epoch()
        for number, suffix in enumerate(("-1", "-2"), start=2):
            self.spend_and_defer(suffix)
            self.plan_sidecar(f"# Plan\nrevision {number}\n")
            opened = self.agent_replan()
            ledger = opened["ledger"]
            self.assertEqual((opened["disposition"], ledger["corrective_epochs"][-1]["epoch_event_id"]),
                             ("continue", f"agent-replan:{number}"))
            self.assertEqual((ledger["corrective_cycles"], ledger["dispatches"], ledger["approved_invariants"]),
                             (0, {}, ["FR-001", "FR-002"]))
            self.assertEqual(ledger["invariant_binding"]["planning_fingerprints"]["plan_sha256"],
                             hashlib.sha256(f"# Plan\nrevision {number}\n".encode()).hexdigest())
            self.assertEqual(self.schema_failures(ledger), [])
        self.spend_and_defer("-3")
        self.plan_sidecar("# Plan\nrevision 4\n")
        with self.assertRaisesRegex(ValueError, "agent-authorized re-plan epoch approvals are spent"):
            self.agent_replan()

    def test_an_agent_replan_fails_closed_when_a_precondition_is_missing(self):
        self.open_first_epoch()
        path = self.root / self.invoke("status", mode="read_only")["ledger_path"]
        self.spend_and_defer("-1")
        before = path.read_bytes()
        spec = self.root / "feature/spec.md"
        original = spec.read_text()
        def rescope():
            spec.write_text(original + "- FR-003: explain refusals\n")
        def stale_sidecar():
            (self.root / "feature/plan.md").write_text("# Plan\nedited without a rerun\n")
        cases = {"the Tasks rerun changed nothing": lambda: None, "the plan changed without a sidecar refresh": stale_sidecar,
                 "the spec (scope) changed": rescope}
        for name, prepare in cases.items():
            with self.subTest(case=name):
                if name.startswith("the Tasks"):
                    self.plan_sidecar()
                prepare()
                with self.assertRaisesRegex(ValueError, "not provable"):
                    self.agent_replan()
                self.assertEqual(path.read_bytes(), before)
                spec.write_text(original)
                self.plan_sidecar()
        self.plan_sidecar("# Plan\nrevision\n")
        with self.assertRaises(ValueError):
            self.invoke("begin-replan-epoch", spec_file="feature/spec.md", agent_authorized=True,
                        native_observation={"native_event_id": "x"})
        self.invoke("reserve", dispatch_id="in-flight", kind="implementation")
        with self.assertRaisesRegex(ValueError, "settle every dispatch"):
            self.agent_replan()

    def test_an_agent_replan_needs_an_open_deferral_and_recorded_fingerprints(self):
        self.plan_sidecar()
        self.start_bound()
        self.plan_sidecar("# Plan\nrevision\n")
        with self.assertRaisesRegex(ValueError, "no_recorded_planning_fingerprints"):
            self.agent_replan()
        self.open_first_epoch_from_bound()
        self.plan_sidecar("# Plan\nrevision 2\n")
        with self.assertRaisesRegex(ValueError, "no_open_deferral"):
            self.agent_replan()

    def test_a_ledger_written_before_agent_approvals_still_validates(self):
        self.open_first_epoch()
        path = self.root / self.invoke("status", mode="read_only")["ledger_path"]
        ledger = json.loads(path.read_text())
        del ledger["invariant_binding"]["planning_fingerprints"]
        path.write_text(json.dumps(ledger), encoding="utf-8")
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")
        ledger["invariant_binding"]["planning_fingerprints"] = {"spec_sha256": "z"}
        path.write_text(json.dumps(ledger), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.invoke("status", mode="read_only")

    def open_first_epoch_from_bound(self):
        self.spend_and_defer("")
        digest = hashlib.sha256((self.root / "feature/spec.md").read_bytes()).hexdigest()
        self.invoke("begin-replan-epoch", spec_file="feature/spec.md", native_observation={
            "native_event_id": "operator-replan", "run_id": self.run_id, "action": "replan_epoch_approved",
            "spec_sha256": digest})

    def continuation_setup(self):
        commit_fixture(self.root)
        self.invoke("start")
        reservation = self.invoke("reserve", dispatch_id="analyze", kind="corrective",
                                  failure_invariant="FR-001")["reservation_id"]
        self.invoke("complete", dispatch_id="analyze", outcome="completed")
        self.invoke("reserve", dispatch_id="other-family", kind="corrective", failure_invariant="FR-002")
        return reservation

    def continuation(self, reservation, **changes):
        request = {"dispatch_id": "metadata", "completed_dispatch_id": "analyze", "reservation_id": reservation,
                   "agent_authorized": True, "spec_file": "feature/spec.md", **changes}
        return self.invoke("authorize-corrective-continuation", **request)

    def test_an_agent_continues_task_metadata_when_the_metadata_only_proof_holds(self):
        reservation = self.continuation_setup()
        (self.root / "feature/tasks.md").write_text(self.CORRECTED)
        admitted = self.continuation(reservation)
        record = admitted["ledger"]["dispatches"]["metadata"]
        self.assertEqual((admitted["disposition"], admitted["continuation_of"]), ("continue", "analyze"))
        self.assertEqual((record["operator_continuation_event_id"], record["continuation_purpose"]),
                         ("agent-continuation:metadata", "task_metadata_reconciliation"))
        self.assertEqual(self.schema_failures(admitted["ledger"]), [])
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "continue")

    def test_an_agent_continuation_fails_closed_without_the_metadata_only_proof(self):
        reservation = self.continuation_setup()
        path = self.root / self.invoke("status", mode="read_only")["ledger_path"]
        before = path.read_bytes()
        cases = {"no correction on disk": (self.TASKS, {}),
                 "a scope-changing edit": (self.CORRECTED.replace("src/app.py", "src/other.py"), {}),
                 "no spec_file": (self.CORRECTED, {"spec_file": None}),
                 "an operator event beside the flag": (self.CORRECTED, {"native_observation": {"native_event_id": "x"}}),
                 "another reservation": (self.CORRECTED, {"reservation_id": "elsewhere"})}
        for name, (tasks, changes) in cases.items():
            with self.subTest(case=name):
                (self.root / "feature/tasks.md").write_text(tasks)
                with self.assertRaises(ValueError):
                    self.continuation(reservation, **changes)
                self.assertEqual(path.read_bytes(), before)

    def test_the_guides_tell_the_lead_to_issue_the_agent_approvals(self):
        root = Path(__file__).resolve().parents[3] / "speckit-pro"
        for relative in UnknownDispatchGuidanceTests.GUIDANCE:
            with self.subTest(guide=relative):
                text = " ".join((root / relative).read_text(encoding="utf-8").split())
                self.assertIn("agent_authorized", text)


if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                               for case in (GreenfieldInvariantBindingTests, ExecutionControlTests, CorrectiveRecoveryTests,
                                            CorrectiveContinuationTests, CorrectiveExceptionTests, CorrectiveFailureClassTests,
                                            ReplanEpochTests, StageEpochTests, IncrementReviewAllowanceTests,
                                            DeferOnExhaustedAllowanceTests, DeferOnExhaustedAllowanceGuidanceTests,
                                            EscalationAllowanceTests,
                                            FailingCheckFingerprintTests, MoreTestRunnerFingerprintTests,
                                            CorrectionProgressTests, UntaggedFailureFamilyTests,
                                            CorrectionProgressGuidanceTests, GateRemediationAllowanceTests,
                                            MetadataOnlyCorrectionTests, IncrementTestFixAllowanceTests,
                                            WorkflowIdentityTests, SelfIgnoringByproductDirectoryTests, VerificationTests,
                                            RunnerDispatchTests, RunnerFormatConvergenceTests))
    suite.addTests(DockerVerificationTests(name) for name in DockerVerificationTests.__dict__ if name.startswith("test_docker_"))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case) for case in (UnknownDispatchUnitScopeTests, UnknownDispatchGuidanceTests,
                                                                            AgentApprovalTests))
    raise SystemExit(run_counted(suite, label="test-execution-control"))
