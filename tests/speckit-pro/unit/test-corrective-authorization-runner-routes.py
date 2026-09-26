#!/usr/bin/env python3
"""Replay the ledger's operator-approved corrective actions through the real runner.

Each scenario drives `python -m speckit_pro_runner` with request envelopes, the
way an autopilot parent does, in a consumer repository built at run time. It
checks the accepted path and the refusals an agent must not talk its way past:
an unbound or replayed operator event, a second use of a one-time allowance, and
a mismatched spec digest. A refusal must leave the ledger bytes unchanged.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tests" / "speckit-pro" / "lib"))

from test_result import run_counted  # noqa: E402


WORKFLOW = "feature/workflow.md"
SPEC = "feature/spec.md"
SPEC_TEXT = "- FR-001: preserve data\n- FR-002: no secrets\n"


class _RunnerLedger:
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / ".specify").mkdir()
        (self.root / "feature").mkdir()
        (self.root / WORKFLOW).write_text("# Workflow\n", encoding="utf-8")
        (self.root / SPEC).write_text(SPEC_TEXT, encoding="utf-8")
        self.run_id: str | None = None
        self.ledger_path: Path | None = None

    def call(self, action: str, mode: str = "apply", **inputs: object) -> tuple[int, dict]:
        binding = {"expected_run_id": self.run_id} if self.run_id else {}
        request = {
            "schema_version": "1.0", "helper_id": "execution-control",
            "operation": "execution-control", "mode": mode,
            "inputs": {"workflow_file": WORKFLOW, "action": action, **binding, **inputs},
        }
        environment = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "speckit-pro"),
                       "PYTHONDONTWRITEBYTECODE": "1"}
        completed = subprocess.run(
            [sys.executable, "-B", "-m", "speckit_pro_runner"], cwd=self.root,
            env=environment, input=json.dumps(request), text=True,
            capture_output=True, timeout=60, check=False, shell=False,
        )
        envelope = json.loads(completed.stdout)
        data = envelope.get("data") or {}
        if "ledger" in data:
            self.run_id = data["ledger"]["run_id"]
            self.ledger_path = self.root / data["ledger_path"]
        return completed.returncode, envelope

    def accept(self, action: str, **inputs: object) -> dict:
        code, envelope = self.call(action, **inputs)
        self.assertEqual((code, envelope["status"]), (0, "ok"), envelope)
        self.assertEqual(envelope["data"]["disposition"], "continue", envelope)
        return envelope["data"]

    def refuse(self, action: str, message: str, **inputs: object) -> None:
        before = self.ledger_path.read_bytes()
        code, envelope = self.call(action, **inputs)
        self.assertEqual((code, envelope["status"]), (2, "input_error"), envelope)
        diagnostic = envelope["diagnostics"][0]
        self.assertEqual(diagnostic["code"], "invalid_execution_request", envelope)
        self.assertIn(message, diagnostic["message"])
        self.assertEqual(self.ledger_path.read_bytes(), before, f"{action} mutated the ledger")

    def status(self) -> dict:
        code, envelope = self.call("status", mode="read_only")
        self.assertEqual(code, 0, envelope)
        return envelope["data"]["ledger"]

    def fail_with_host_event(self, dispatch_id: str, event_id: str) -> None:
        code, envelope = self.call("reconcile", dispatch_id=dispatch_id)
        self.assertEqual((code, envelope["data"]["disposition"]), (1, "checkpoint_required"), envelope)
        code, envelope = self.call("complete", dispatch_id=dispatch_id, outcome="failed", native_observation={
            "native_event_id": event_id, "run_id": self.run_id, "dispatch_id": dispatch_id,
            "action": "dispatch_result", "outcome": "failed"})
        self.assertEqual(code, 0, envelope)


class BindInvariantsRouteTests(_RunnerLedger, unittest.TestCase):
    def test_greenfield_run_binds_its_spec_once_through_the_runner(self) -> None:
        (self.root / SPEC).unlink()
        started = self.accept("start")
        self.assertEqual(started["ledger"]["approved_invariants"], [])
        self.refuse("bind-invariants", "requires an explicit spec_file")
        (self.root / SPEC).write_text(SPEC_TEXT, encoding="utf-8")

        bound = self.accept("bind-invariants", spec_file=SPEC)["ledger"]
        self.assertEqual(bound["run_id"], started["ledger"]["run_id"])
        self.assertEqual(bound["approved_invariants"], ["FR-001", "FR-002"])
        self.assertTrue(bound["invariant_binding"]["spec_sha256"])

        (self.root / SPEC).write_text(SPEC_TEXT + "- FR-003: added later\n", encoding="utf-8")
        self.refuse("bind-invariants", "already frozen", spec_file=SPEC)
        self.assertEqual(self.status()["approved_invariants"], ["FR-001", "FR-002"])


class CorrectiveRetryRouteTests(_RunnerLedger, unittest.TestCase):
    def test_one_operator_approved_infrastructure_retry_through_the_runner(self) -> None:
        self.accept("start")
        reservation = self.accept("reserve", dispatch_id="owner", kind="corrective",
                                  failure_invariant="FR-001")["reservation_id"]
        self.fail_with_host_event("owner", "host-auth-error")
        self.accept("reserve", dispatch_id="other-family", kind="corrective", failure_invariant="FR-002")
        approval = {"native_event_id": "operator-retry-message", "run_id": self.run_id,
                    "action": "corrective_retry_approved", "failed_dispatch_id": "owner",
                    "failed_native_event_id": "host-auth-error", "retry_dispatch_id": "owner-retry",
                    "reservation_id": reservation, "failure_kind": "infrastructure"}
        request = {"dispatch_id": "owner-retry", "failed_dispatch_id": "owner",
                   "reservation_id": reservation}
        for label, event in (
            ("missing event", None),
            ("other run", {**approval, "run_id": "other-run"}),
            ("replayed host event", {**approval, "native_event_id": "host-auth-error"}),
            ("unrecorded failure", {**approval, "failed_native_event_id": "other-host-event"}),
            ("application failure", {**approval, "failure_kind": "application"}),
        ):
            with self.subTest(label):
                self.refuse("authorize-corrective-retry", "", native_observation=event, **request)

        retry = self.accept("authorize-corrective-retry", native_observation=approval, **request)["ledger"]
        self.assertEqual(retry["corrective_cycles"], 2)
        self.assertEqual(retry["dispatches"]["owner"]["outcome"], "failed")
        self.assertEqual(retry["dispatches"]["owner-retry"]["recovery_of"], "owner")
        self.accept("complete", dispatch_id="owner-retry", outcome="completed")

        self.refuse("authorize-corrective-retry", "", native_observation={
            **approval, "native_event_id": "second-message", "retry_dispatch_id": "second-retry"},
            **{**request, "dispatch_id": "second-retry"})
        self.refuse("pause", "", native_observation={
            "native_event_id": "operator-retry-message", "run_id": self.run_id,
            "kind": "human_uat", "action": "wait_started"})


class CorrectiveContinuationRouteTests(_RunnerLedger, unittest.TestCase):
    def test_one_operator_approved_metadata_continuation_through_the_runner(self) -> None:
        self.accept("start")
        reservation = self.accept("reserve", dispatch_id="analyze", kind="corrective",
                                  failure_invariant="FR-001")["reservation_id"]
        self.accept("complete", dispatch_id="analyze", outcome="completed")
        self.accept("reserve", dispatch_id="other-family", kind="corrective", failure_invariant="FR-002")
        approval = {"native_event_id": "operator-consensus-message", "run_id": self.run_id,
                    "action": "corrective_continuation_approved", "completed_dispatch_id": "analyze",
                    "continuation_dispatch_id": "metadata", "reservation_id": reservation,
                    "purpose": "task_metadata_reconciliation"}
        request = {"dispatch_id": "metadata", "completed_dispatch_id": "analyze",
                   "reservation_id": reservation}
        for label, event in (
            ("missing event", None),
            ("other run", {**approval, "run_id": "other-run"}),
            ("retry approval", {**approval, "action": "corrective_retry_approved"}),
            ("unrelated source", {**approval, "completed_dispatch_id": "other-family"}),
            ("general repair", {**approval, "purpose": "unbounded_repair"}),
        ):
            with self.subTest(label):
                self.refuse("authorize-corrective-continuation", "", native_observation=event, **request)

        continued = self.accept("authorize-corrective-continuation", native_observation=approval,
                                **request)["ledger"]
        self.assertEqual(continued["corrective_cycles"], 2)
        self.assertEqual(continued["dispatches"]["metadata"]["continuation_of"], "analyze")

        self.refuse("authorize-corrective-continuation", "", native_observation={
            **approval, "native_event_id": "second-message", "continuation_dispatch_id": "metadata-two"},
            **{**request, "dispatch_id": "metadata-two"})
        self.refuse("pause", "", native_observation={
            "native_event_id": "operator-consensus-message", "run_id": self.run_id,
            "kind": "human_uat", "action": "wait_started"})


class CorrectiveExceptionRouteTests(_RunnerLedger, unittest.TestCase):
    SCOPE = "a" * 64

    def test_one_operator_approved_exception_after_budget_exhaustion_through_the_runner(self) -> None:
        (self.root / SPEC).unlink()
        self.accept("start")
        self.accept("reserve", dispatch_id="fix-a", kind="corrective", failure_invariant="FR-001")
        self.accept("complete", dispatch_id="fix-a", outcome="failed")
        (self.root / SPEC).write_text(SPEC_TEXT, encoding="utf-8")
        spec_digest = self.accept("bind-invariants", spec_file=SPEC)["ledger"]["invariant_binding"]["spec_sha256"]
        self.accept("reserve", dispatch_id="fix-b", kind="corrective", failure_invariant="FR-002")
        self.accept("complete", dispatch_id="fix-b", outcome="failed")
        code, refused = self.call("reserve", dispatch_id="fix-c", kind="corrective", failure_invariant="FR-001")
        self.assertEqual((code, refused["status"]), (1, "expected_failure"), refused)
        self.assertEqual(refused["data"]["reasons"], ["corrective_run_budget_exhausted"])

        approval = {"native_event_id": "operator-exception", "run_id": self.run_id,
                    "action": "corrective_exception_approved", "failure_invariant": "FR-001",
                    "dispatch_id": "fix-c", "failure_kind": "application",
                    "refusal_reason": "corrective_run_budget_exhausted",
                    "scope_sha256": self.SCOPE, "spec_sha256": spec_digest}
        request = {"dispatch_id": "fix-c", "failure_invariant": "FR-001", "scope_sha256": self.SCOPE}
        for label, event in (
            ("missing event", None),
            ("other run", {**approval, "run_id": "other-run"}),
            ("spec digest mismatch", {**approval, "spec_sha256": "c" * 64}),
            ("scope mismatch", {**approval, "scope_sha256": "b" * 64}),
            ("wrong refusal", {**approval, "refusal_reason": "failure_family_budget_exhausted"}),
        ):
            with self.subTest(label):
                self.refuse("authorize-corrective-exception", "", native_observation=event, **request)

        before = self.status()
        granted = self.accept("authorize-corrective-exception", native_observation=approval, **request)
        ledger = granted["ledger"]
        for key in ("run_id", "corrective_cycles", "reservations", "invariant_binding"):
            self.assertEqual(ledger[key], before[key], key)
        self.assertEqual(ledger["corrective_exception"]["dispatch_id"], "fix-c")
        self.assertEqual(ledger["corrective_exception"]["operator_exception_event_id"], "operator-exception")
        self.accept("complete", dispatch_id="fix-c", outcome="failed")

        self.refuse("authorize-corrective-exception", "", native_observation={
            **approval, "native_event_id": "second-exception", "dispatch_id": "fix-d"},
            **{**request, "dispatch_id": "fix-d"})
        self.refuse("pause", "", native_observation={
            "native_event_id": "operator-exception", "run_id": self.run_id,
            "kind": "human_uat", "action": "wait_started"})


if __name__ == "__main__":
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(case)
        for case in (BindInvariantsRouteTests, CorrectiveRetryRouteTests,
                     CorrectiveContinuationRouteTests, CorrectiveExceptionRouteTests)
    )
    raise SystemExit(run_counted(suite, label="test-corrective-authorization-runner-routes"))
