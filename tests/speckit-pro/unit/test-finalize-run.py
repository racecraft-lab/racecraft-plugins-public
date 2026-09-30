#!/usr/bin/env python3
"""How an autopilot run ends once no runnable work remains (issue 804).

Human UAT is the only gate a run may defer. A run whose non-UAT gates all
passed and that holds no unresolved deferral is done: its pull-request stack
goes ready for review (never merged), the top PR body opens with a
"Deferred / not verified" section listing the human UAT, the goal is marked
complete, and one plain-text request names what is left. A failed gate, a
ledger deferral, or an unresolved deferred task at the end is one human stop
that names the gate and its exact command, never ready for review. The
`finalize-run` helper derives that decision and fails closed.

Every gate result is tied to the PR head it ran at (issue 814). A multi-PR
stack finalizes only when every PR head has passed every non-UAT gate; a head
with no result for a gate is a human stop that names the head and the gate.

A harness or tooling error that blocks a gate is retried within a fixed budget
(issue 815). If it persists, the gate reports status `harness_error` with its
attempt count and the `.process/verification/` path holding each attempt's raw
error and trace. It never counts as passed, and the one human stop reports it
as a harness error, never as a failure of the code under test.

The stop triggers are proved from the runner's own records (issue 829). A gate's
status comes from the verification dispatch the runner fingerprinted, so a forged
status fails closed. A deferred unit or failed gate gets one escalation cycle
first, a gate missing at a head becomes pending work, and a harness error gets
one more attempt in a changed environment. A stop needs the earlier cycle the
runner counted in the ledger.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
for entry in (PLUGIN_ROOT, REPO_ROOT / "tests" / "speckit-pro" / "lib"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from test_result import run_counted  # noqa: E402

from speckit_pro_runner.execution_control import execution_control, record_failing_checks  # noqa: E402
from speckit_pro_runner.helpers.run_finalization import gate_command_digest as command_digest  # noqa: E402

HELPER_ID = "finalize-run"
FIXTURE_REQUEST = (
    REPO_ROOT / "tests/speckit-pro/unit/fixtures/read-only-helpers/requests" / f"{HELPER_ID}.json"
)
RESUME = "/speckit-pro:speckit-autopilot docs/ai/specs/.process/FEATURE-001-workflow.md --from-phase implement"
UAT = {
    "item": "UAT story 2: the export opens in a spreadsheet app",
    "reason": "It needs a person to open the exported file.",
    "finish": "Follow steps 4 to 6 of the UAT runbook and record the result on the pull request.",
}
VETO = {
    "unit": "T042",
    "reason": "The approval reviewer denied the live evaluation twice despite the recorded chat authorization.",
    "finish": "python3 tests/live/run-eval.py --task T042",
}
HEADS = {101: "a" * 40, 102: "b" * 40, 103: "c" * 40}
GREEN = (
    {"gate": "G7", "status": "passed", "command": "python3 tests/run-all.py"},
    {"gate": "Post: Integration Suite", "status": "passed", "command": "python3 tests/integration.py"},
)
LIVE_EVAL = {"gate": "Post: Live Evaluation", "status": "failed",
             "command": "python3 tests/live/run-eval.py --task T042", "head_sha": HEADS[103]}


HARNESS_EVIDENCE = "clean/.process/verification/harness/g7-cccccccc"
HARNESS_ERROR = {"gate": "G7", "status": "harness_error", "command": "python3 tests/run-all.py",
                 "head_sha": HEADS[103], "attempts": 3, "evidence": HARNESS_EVIDENCE}


DROP = object()  # marks an evidence key the seeded verification record leaves out


def per_head(*gates: dict[str, object], heads: tuple[str, ...] = tuple(HEADS.values())) -> list[dict[str, object]]:
    """Each gate result repeated at every listed PR head."""
    return [{**gate, "head_sha": head} for head in heads for gate in gates]


def finalize(root: Path, inputs: dict[str, object], record: bool = False) -> dict[str, object]:
    """The read-only decision; with `record`, the runner then counts the cycle through execution-control."""
    from speckit_pro_runner.helpers.run_finalization import finalize_run

    result = finalize_run(root, inputs)
    if record:
        ledger = json.loads((root / str(inputs["ledger_path"])).read_text(encoding="utf-8"))
        with patch("speckit_pro_runner.execution_control.time.time", return_value=ledger["last_observed_at"]):
            execution_control(root, {"workflow_file": ledger["workflow_identity"]["current_workflow_file"],
                                     "action": "record-finalize-cycle", "expected_run_id": inputs["expected_run_id"],
                                     "ledger_path": inputs["ledger_path"], "finalize_inputs": inputs}, "apply")
    return result


class _VerificationEvidence:
    """Runner-fingerprinted verification dispatches that back each gate result."""

    def verification(self, run: dict[str, object], gate: dict[str, object], **changes: object) -> str:
        """One verification dispatch the runner fingerprinted for this gate, returned as its dispatch id."""
        self.clock += 10
        run["verifications"] = int(run.get("verifications", 0)) + 1  # type: ignore[call-overload]
        dispatch_id = f"verify-{run['verifications']}"
        passed = gate["status"] == "passed"
        evidence: dict[str, object] = {
            "command_id": "UNIT_TEST", "command_sha256": command_digest(str(gate["command"])),
            "format": "passed" if passed else "unittest", "failing": [] if passed else ["test_x (m.T.test_x)"],
            "passing": None, "checks_run": None if passed else 1, "output_sha256": "0" * 64,
            "head_sha": gate["head_sha"], "worktree_clean": True}
        evidence.update(changes)
        for key in [key for key, value in evidence.items() if value is DROP]:
            del evidence[key]
        self.invoke(run, "reserve", dispatch_id=dispatch_id, kind="verification")
        self.invoke(run, "begin-verification", dispatch_id=dispatch_id)
        with patch("speckit_pro_runner.execution_control.time.time", return_value=self.clock):
            record_failing_checks(self.root, {"workflow_file": run["workflow"], "expected_run_id": run["run_id"],
                                              "dispatch_id": dispatch_id}, evidence)
        self.invoke(run, "complete", dispatch_id=dispatch_id, outcome="completed" if passed else "failed")
        return dispatch_id

    def bind_gates(self, run: dict[str, object], gates: list[dict[str, object]]) -> list[dict[str, object]]:
        """Back each passed or failed gate result with a runner-fingerprinted verification dispatch."""
        bound = []
        for gate in gates:
            if (gate.get("status") in ("passed", "failed") and "dispatch_id" not in gate
                    and isinstance(gate.get("command"), str) and str(gate["command"]).strip()
                    and isinstance(gate.get("head_sha"), str) and len(str(gate["head_sha"])) == 40):
                gate = {**gate, "dispatch_id": self.verification(run, gate)}
            bound.append(gate)
        return bound


class _HarnessEvidence:
    """Gate results with a persistent harness error, before and after the extra attempt."""

    def harness_gates(self, **overrides: object) -> list[dict[str, object]]:
        """Green at every head except G7 at the tip, which hit a persistent harness error."""
        evidence = self.root / HARNESS_EVIDENCE
        evidence.mkdir(parents=True, exist_ok=True)
        for attempt in (1, 2, 3, 4):
            (evidence / f"attempt-{attempt}.log").write_text("harness exited 70 before the suite ran\n")
        gates = [gate for gate in per_head(*GREEN) if not (gate["head_sha"] == HEADS[103] and gate["gate"] == "G7")]
        return gates + [{**HARNESS_ERROR, **overrides}]

    def changed_environment_gates(self) -> list[dict[str, object]]:
        """The harness error after the extra attempt in a changed environment."""
        return self.harness_gates(attempts=4, environment_change="fresh_worktree")


class _EscalationEvidence(_VerificationEvidence):
    """Escalation retries for deferred units and failed gates."""

    def fail_escalation(self, run: dict[str, object], unit: tuple[str, str], tiers: tuple[int, ...] = (2, 3),
                        outcome: str | None = "failed") -> None:
        """Run each listed tier's retry for one (unit kind, unit); the last settles as `outcome`, or stays open when None."""
        unit_kind, unit_name = unit
        for tier in tiers:
            self.clock += 10
            name = f"escalate-{unit_kind}-{unit_name[:12]}-tier-{tier}"
            self.invoke(run, "reserve", dispatch_id=name, kind="corrective",
                        escalation={"unit_kind": unit_kind, "unit": unit_name, "tier": tier})
            if outcome is not None or tier != tiers[-1]:
                self.clock += 10
                self.invoke(run, "complete", dispatch_id=name, outcome=outcome or "failed")

    def exhaust(self, run: dict[str, object], inputs: dict[str, object]) -> dict[str, object]:
        """Fail every escalation tier of every failed gate in the inputs and every open deferral in the ledger."""
        ledger = json.loads((self.root / str(run["ledger_path"])).read_text())
        for entry in ledger.get("deferred", []):
            if "resolved_by" not in entry:
                self.fail_escalation(run, (entry["unit_kind"], entry["unit"]))
        for gate in inputs["gates"]:  # type: ignore[attr-defined]
            if gate["status"] == "failed":
                digest = command_digest(gate["command"])
                self.fail_escalation(run, ("gate_failure", digest), tiers=(2,))
                self.verification(run, gate)  # the gate is red again after the tier-2 retry
                self.fail_escalation(run, ("gate_failure", digest), tiers=(3,))
        return inputs


class _LedgerFixture(_EscalationEvidence, _HarnessEvidence):
    """A temporary repository with a clean ledger and one holding a deferral."""

    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.clock = 1000.0
        self.clean = self.start("clean")
        self.deferring = self.start("feature")
        self.invoke(self.deferring, "reserve", dispatch_id="fix-a", kind="corrective", failure_invariant="FR-001")
        self.invoke(self.deferring, "complete", dispatch_id="fix-a", outcome="completed")
        self.clock += 10  # the deferral comes after the completed fix, as it does in a real run
        deferred = self.invoke(self.deferring, "reserve", dispatch_id="fix-a-again", kind="corrective",
                               failure_invariant="FR-001")
        assert deferred["disposition"] == "defer", deferred

    def start(self, name: str) -> dict[str, object]:
        (self.root / name).mkdir()
        (self.root / name / "workflow.md").write_text("# Workflow\n")
        (self.root / name / "spec.md").write_text("- FR-001: preserve data\n")
        run: dict[str, object] = {"workflow": f"{name}/workflow.md"}
        self.invoke(run, "start")
        return run

    def invoke(self, run: dict[str, object], action: str, **inputs: object) -> dict[str, object]:
        binding = {"expected_run_id": run["run_id"]} if "run_id" in run else {}
        with patch("speckit_pro_runner.execution_control.time.time", return_value=self.clock):
            result = execution_control(
                self.root, {"workflow_file": run["workflow"], "action": action, **binding, **inputs}, "apply"
            )
        run.update(run_id=result["ledger"]["run_id"], ledger_path=result["ledger_path"])
        return result

    def assert_finalizes_after_a_recorded_cycle(self, gates: list[dict[str, object]]) -> None:
        """A recorded cycle over `gates` is followed by an all-green run that finalizes ready for review."""
        finalize(self.root, self.inputs(gates=gates), record=True)
        result = finalize(self.root, self.inputs())
        self.assertEqual((result["outcome"], result["mark_ready"]), ("complete_with_deferred", True))

    def inputs(self, run: dict[str, object] | None = None, **overrides: object) -> dict[str, object]:
        run = run or self.clean
        inputs: dict[str, object] = {
            "ledger_path": run["ledger_path"],
            "expected_run_id": run["run_id"],
            "gates": per_head(*GREEN),
            "pending_items": [],
            "unresolved_deferrals": [],
            "human_uat": [dict(UAT)],
            "pull_requests": [
                {"number": 101, "url": "https://github.com/example-org/example-repo/pull/101", "draft": True,
                 "head_sha": HEADS[101]},
                {"number": 102, "url": "https://github.com/example-org/example-repo/pull/102", "draft": False,
                 "head_sha": HEADS[102]},
                {"number": 103, "url": "https://github.com/example-org/example-repo/pull/103", "draft": True,
                 "head_sha": HEADS[103]},
            ],
            "resume_command": RESUME,
        }
        inputs.update(overrides)
        inputs["gates"] = self.bind_gates(run, inputs["gates"])  # type: ignore[arg-type]
        return inputs


class FinalizeRunTests(_LedgerFixture, unittest.TestCase):
    def test_green_gates_with_only_human_uat_left_finalize_ready_for_review(self) -> None:
        result = finalize(self.root, self.inputs())
        self.assertEqual(result["outcome"], "complete_with_deferred")
        self.assertEqual(result["goal_status"], "complete")
        self.assertTrue(result["mark_ready"])
        self.assertTrue(result["finalized"])
        self.assertFalse(result["writes_state"])
        self.assertEqual(result["ready_commands"], ["gh pr ready 101", "gh pr ready 103"])
        self.assertFalse(any("merge" in command for command in result["ready_commands"]))
        self.assertEqual(result["top_pull_request"], "https://github.com/example-org/example-repo/pull/103")
        self.assertEqual(result["deferred_items"], [UAT])
        request = result["end_of_run_request"]
        self.assertIn("ready for review", request)
        for value in UAT.values():
            self.assertIn(value, request)
        self.assertIn(RESUME, request)
        self.assertTrue(result["deferred_digest"].startswith("sha256:"))
        self.assertIsNone(result["human_stop"])

    def test_a_failed_gate_is_one_human_stop_naming_the_gate_and_command(self) -> None:
        gates = per_head(GREEN[0]) + per_head({**LIVE_EVAL, "status": "passed"}, heads=(HEADS[101], HEADS[102]))
        gates.append(dict(LIVE_EVAL))
        inputs = self.inputs(gates=gates)
        self.assertEqual(finalize(self.root, inputs)["outcome"], "continue")
        result = finalize(self.root, self.exhaust(self.clean, inputs))
        self.assertEqual(result["outcome"], "human_stop")
        self.assertEqual(result["goal_status"], "blocked")
        self.assertFalse(result["mark_ready"])
        self.assertFalse(result["finalized"])
        self.assertEqual(result["ready_commands"], [])
        stop = result["human_stop"]
        self.assertEqual(stop["gates"], [{"gate": LIVE_EVAL["gate"], "command": LIVE_EVAL["command"],
                                          "pull_request": 103, "head_sha": HEADS[103], "class": "exhausted",
                                          "reason_code": "all_tiers_failed"}])
        self.assertEqual(stop["missing"], [])
        request = result["end_of_run_request"]
        self.assertIn(LIVE_EVAL["gate"], request)
        self.assertIn(LIVE_EVAL["command"], request)
        self.assertIn(HEADS[103], request)
        self.assertNotIn("ready for review.", request)

    def test_only_human_uat_reaches_the_deferred_section(self) -> None:
        result = finalize(self.root, self.inputs(self.deferring, gates=per_head(LIVE_EVAL),
                                                 unresolved_deferrals=[dict(VETO)]))
        self.assertEqual(result["deferred_items"], [UAT])

    def test_remaining_runnable_work_continues_the_run(self) -> None:
        result = finalize(self.root, self.inputs(self.deferring, pending_items=["Post: Retrospective"],
                                                 gates=per_head(LIVE_EVAL)))
        self.assertEqual(result["outcome"], "continue")
        self.assertEqual(result["goal_status"], "not_complete")
        self.assertFalse(result["mark_ready"])
        self.assertIsNone(result["human_stop"])

    def test_nothing_left_completes_without_a_request(self) -> None:
        result = finalize(self.root, self.inputs(human_uat=[]))
        self.assertEqual(result["outcome"], "complete")
        self.assertEqual(result["goal_status"], "complete")
        self.assertTrue(result["mark_ready"])
        self.assertEqual(result["deferred_items"], [])
        self.assertEqual(result["end_of_run_request"], "")

    def test_digest_is_stable_for_an_unchanged_blocker(self) -> None:
        self.fail_escalation(self.deferring, ("failure_family", "FR-001"))
        first = finalize(self.root, self.inputs(self.deferring))
        second = finalize(self.root, self.inputs(self.deferring))
        self.assertEqual(first["deferred_digest"], second["deferred_digest"])
        changed = finalize(self.root, self.inputs(self.deferring, unresolved_deferrals=[dict(VETO)]))
        self.assertNotEqual(first["deferred_digest"], changed["deferred_digest"])

    def test_digest_and_request_ignore_input_order(self) -> None:
        """#807 review: the same blocker listed in another order is not a changed blocker."""
        gates = per_head(*({**gate, "status": "failed"} for gate in GREEN))
        uat = [dict(UAT), {**UAT, "item": "Second walkthrough"}]
        forward = finalize(self.root, self.exhaust(self.clean, self.inputs(gates=gates, human_uat=uat)))
        backward = finalize(self.root, self.exhaust(self.clean, self.inputs(gates=gates[::-1], human_uat=uat[::-1])))
        self.assertEqual(forward["deferred_digest"], backward["deferred_digest"])
        self.assertEqual(forward["end_of_run_request"], backward["end_of_run_request"])
        ready = finalize(self.root, self.inputs(human_uat=uat))
        again = finalize(self.root, self.inputs(human_uat=uat[::-1]))
        self.assertEqual(ready["deferred_digest"], again["deferred_digest"])
        self.assertEqual(ready["end_of_run_request"], again["end_of_run_request"])

    def test_every_pr_head_passing_every_gate_is_what_finalizes_a_stack(self) -> None:
        result = finalize(self.root, self.inputs())
        self.assertTrue(result["mark_ready"])
        self.assertEqual([pr["head_sha"] for pr in result["pull_requests"]], list(HEADS.values()))
        for pr in result["pull_requests"]:
            with self.subTest(pull_request=pr["number"]):
                # Each PR body cites only the evidence produced at its own head.
                self.assertEqual([{key: value for key, value in gate.items() if key != "dispatch_id"}
                                  for gate in pr["gates"]], [{**gate, "head_sha": pr["head_sha"]} for gate in GREEN])
                self.assertTrue(all(gate["dispatch_id"].startswith("verify-") for gate in pr["gates"]))

    def test_a_stack_verified_only_at_its_tip_is_a_human_stop_naming_each_unverified_head(self) -> None:
        tip_only = per_head(*GREEN, heads=(HEADS[103],))
        first = finalize(self.root, self.inputs(gates=tip_only), record=True)
        self.assertEqual(first["outcome"], "continue")
        self.assertEqual(len(first["pending_items"]), 4)
        result = finalize(self.root, self.inputs(gates=tip_only))
        self.assertEqual(result["outcome"], "human_stop")
        self.assertFalse(result["mark_ready"])
        self.assertEqual(result["ready_commands"], [])
        missing = result["human_stop"]["missing"]
        self.assertEqual(sorted((entry["pull_request"], entry["gate"]) for entry in missing),
                         [(101, "G7"), (101, "Post: Integration Suite"), (102, "G7"), (102, "Post: Integration Suite")])
        for entry in missing:
            self.assertEqual(entry["head_sha"], HEADS[entry["pull_request"]])
        request = result["end_of_run_request"]
        for head in (HEADS[101], HEADS[102]):
            self.assertIn(head, request)
        self.assertNotIn(HEADS[103], request)
        self.assertIn("Post: Integration Suite", request)

    def test_a_gate_missing_at_one_lower_head_blocks_the_whole_stack(self) -> None:
        gates = [gate for gate in per_head(*GREEN)
                 if not (gate["head_sha"] == HEADS[102] and gate["gate"] == "Post: Integration Suite")]
        self.assertEqual(finalize(self.root, self.inputs(gates=gates), record=True)["outcome"], "continue")
        result = finalize(self.root, self.inputs(gates=gates))
        self.assertEqual(result["outcome"], "human_stop")
        self.assertEqual(result["human_stop"]["missing"],
                         [{"pull_request": 102, "head_sha": HEADS[102], "gate": "Post: Integration Suite",
                           "command": GREEN[1]["command"], "class": "exhausted"}])

    def test_a_failed_gate_at_a_lower_head_is_a_human_stop_even_when_the_tip_passed(self) -> None:
        gates = per_head(*GREEN, heads=(HEADS[102], HEADS[103]))
        gates += [dict(GREEN[0], head_sha=HEADS[101]), dict(GREEN[1], status="failed", head_sha=HEADS[101])]
        result = finalize(self.root, self.exhaust(self.clean, self.inputs(gates=gates)))
        self.assertEqual(result["outcome"], "human_stop")
        self.assertEqual(result["human_stop"]["gates"],
                         [{"gate": GREEN[1]["gate"], "command": GREEN[1]["command"], "pull_request": 101,
                           "head_sha": HEADS[101], "class": "exhausted", "reason_code": "all_tiers_failed"}])

    def test_a_single_pull_request_run_finalizes_at_its_one_head(self) -> None:
        prs = [{"number": 7, "url": "https://github.com/example-org/example-repo/pull/7", "draft": True,
                "head_sha": "d" * 40}]
        result = finalize(self.root, self.inputs(pull_requests=prs, gates=per_head(*GREEN, heads=("d" * 40,))))
        self.assertEqual(result["outcome"], "complete_with_deferred")
        self.assertEqual(result["ready_commands"], ["gh pr ready 7"])

    def test_a_persistent_harness_error_is_a_human_stop_citing_its_evidence(self) -> None:
        first = finalize(self.root, self.inputs(gates=self.harness_gates()), record=True)
        self.assertEqual(first["outcome"], "continue")
        result = finalize(self.root, self.inputs(gates=self.changed_environment_gates()))
        self.assertEqual(result["outcome"], "human_stop")
        self.assertFalse(result["mark_ready"])
        self.assertEqual(result["ready_commands"], [])
        stop = result["human_stop"]
        self.assertEqual(stop["harness_errors"], [{"gate": "G7", "command": HARNESS_ERROR["command"],
                                                   "pull_request": 103, "head_sha": HEADS[103], "attempts": 4,
                                                   "evidence": HARNESS_EVIDENCE, "class": "exhausted"}])
        # Reported as a harness error, not as a failed gate or a missing result.
        self.assertEqual(stop["gates"], [])
        self.assertEqual(stop["missing"], [])
        request = result["end_of_run_request"]
        self.assertIn("harness error", request)
        self.assertIn("not a failure of the code under test", request)
        self.assertIn(HARNESS_EVIDENCE, request)
        self.assertIn("4 attempts", request)
        self.assertNotIn("G7 failed", request)

    def test_a_harness_error_never_counts_as_passed(self) -> None:
        finalize(self.root, self.inputs(gates=self.harness_gates()), record=True)
        result = finalize(self.root, self.inputs(gates=self.changed_environment_gates(), human_uat=[]))
        self.assertFalse(result["finalized"])
        self.assertEqual(result["goal_status"], "blocked")
        tip = result["pull_requests"][-1]
        self.assertIn("harness_error", [gate["status"] for gate in tip["gates"]])

    def test_the_retry_budget_in_the_guidance_is_the_helper_constant(self) -> None:
        from speckit_pro_runner.helpers.run_finalization import HARNESS_RETRY_BUDGET

        words = {2: "two", 3: "three", 4: "four", 5: "five"}
        for reference in ("skills/speckit-autopilot/references/phase-execution.md",
                          "codex-skills/speckit-autopilot/references/phase-execution-codex.md"):
            with self.subTest(reference=reference):
                text = " ".join((PLUGIN_ROOT / reference).read_text(encoding="utf-8").split())
                for phrase in (f"up to {words[HARNESS_RETRY_BUDGET]} attempts",
                               f"`attempts` reaches {HARNESS_RETRY_BUDGET}"):
                    self.assertTrue(phrase in text, f"{reference} must state: {phrase}")

    def test_harness_errors_fail_closed(self) -> None:
        cases: dict[str, dict[str, object]] = {
            "retry budget not spent": {"attempts": 2},
            "unknown environment change": {"attempts": 4, "environment_change": "reboot"},
            "environment change without the extra attempt": {"attempts": 3, "environment_change": "fresh_worktree"},
            "attempts is not an integer": {"attempts": "3"},
            "attempts is a boolean": {"attempts": True},
            "evidence outside the verification directory": {"evidence": "clean/.process/task-results/g7"},
            "evidence not under a .process directory": {"evidence": "clean/verification/g7"},
            "evidence missing": {"evidence": "clean/.process/verification/harness/absent"},
            "evidence traversal": {"evidence": "../.process/verification/harness"},
            "evidence absolute": {"evidence": "/.process/verification/harness"},
        }
        for name, override in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(ValueError):
                    finalize(self.root, self.inputs(gates=self.harness_gates(**override)))
        without_evidence = self.harness_gates()
        del without_evidence[-1]["evidence"]
        with self.assertRaises(ValueError):
            finalize(self.root, self.inputs(gates=without_evidence))
        passed_with_attempts = per_head(*GREEN)
        passed_with_attempts[0] = {**passed_with_attempts[0], "attempts": 3, "evidence": HARNESS_EVIDENCE}
        with self.assertRaises(ValueError):
            finalize(self.root, self.inputs(gates=passed_with_attempts))

    def test_inputs_fail_closed(self) -> None:
        pr = {"number": 1, "url": "https://x/pull/1", "draft": True, "head_sha": "d" * 40}
        cases: dict[str, dict[str, object]] = {
            "no gates": {"gates": []},
            "unknown gate status": {"gates": [{"gate": "G7", "status": "green", "command": "x"}]},
            "deferred gate status": {"gates": [{"gate": "G7", "status": "deferred", "command": "x"}]},
            "gate without command": {"gates": [{"gate": "G7", "status": "failed", "head_sha": HEADS[101]}]},
            "gate without head": {"gates": [dict(GREEN[0])]},
            "gate at a head outside the stack": {"gates": per_head(*GREEN) + per_head(GREEN[0], heads=("e" * 40,))},
            "gate reported twice at one head": {"gates": per_head(*GREEN) + per_head(GREEN[0])},
            "short head": {"gates": per_head(*GREEN, heads=("abc1234",)),
                           "pull_requests": [dict(pr, head_sha="abc1234")]},
            "pull request without head": {"pull_requests": [{"number": 1, "url": "https://x/pull/1", "draft": True}]},
            "two pull requests sharing a head": {"pull_requests": [pr, dict(pr, number=2, url="https://x/pull/2")]},
            "no pull requests": {"pull_requests": []},
            "draft is not a boolean": {"pull_requests": [dict(pr, draft="yes")]},
            "run id mismatch": {"expected_run_id": "another-run"},
            "missing ledger": {"ledger_path": "clean/.process/execution-control/missing.json"},
            "ledger outside its directory": {"ledger_path": "clean/workflow.md"},
            "traversal": {"ledger_path": "../execution-control/x.json"},
            "deferral without finish": {"unresolved_deferrals": [{"unit": "T042", "reason": "veto"}]},
            "uat without finish": {"human_uat": [{"item": "UAT", "reason": "person"}]},
            "unknown input": {"approve": True},
            "old input name": {"blocked_action_deferrals": []},
            "no resume command": {"resume_command": ""},
        }
        for name, override in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(ValueError):
                    finalize(self.root, self.inputs(**override))


class FinalizeRunOneLineTests(_LedgerFixture, unittest.TestCase):
    """A deferred item is one line per field, as the packet normalizer requires."""

    def test_multi_line_text_is_refused_before_the_packet_normalizer_would_reject_it(self) -> None:
        # pr-packet-output rejects a newline in a deferred item, so finalize-run must refuse it first.
        records = {"human_uat": ("item", "reason", "finish"), "unresolved_deferrals": ("unit", "reason", "finish")}
        for name, fields in records.items():
            for field in fields:
                record = {key: "one line" for key in fields} | {field: "first line\nsecond line"}
                with self.subTest(record=name, field=field):
                    with self.assertRaisesRegex(ValueError, "one line"):
                        finalize(self.root, self.inputs(**{name: [record]}))


class FinalizeRunDecisionTests(_LedgerFixture, unittest.TestCase):
    """An exhausted unit is a decision, not a stop, and the stop policy owns the stop classes."""

    def test_an_exhausted_ledger_unit_is_a_decision_and_the_stack_still_goes_ready(self) -> None:
        self.fail_escalation(self.deferring, ("failure_family", "FR-001"))
        result = finalize(self.root, self.inputs(self.deferring))
        self.assertEqual(result["outcome"], "complete_with_deferred")
        self.assertTrue(result["mark_ready"])
        self.assertEqual(result["ready_commands"], ["gh pr ready 101", "gh pr ready 103"])
        self.assertIsNone(result["human_stop"])
        decisions = result["decisions"]
        self.assertEqual([decision["unit"] for decision in decisions], ["Failure family FR-001"])
        self.assertEqual(decisions[0]["class"], "exhausted")
        self.assertIn("authorize-corrective-exception", decisions[0]["finish"])
        self.assertIn("tier 3", decisions[0]["evidence"])
        request = result["end_of_run_request"]
        self.assertIn("Decisions for you", request)
        self.assertIn("Failure family FR-001", request)
        self.assertIn("ready for review", request)

    def test_exhausted_stop_classes_and_reasons_come_from_the_stop_policy(self) -> None:
        from speckit_pro_runner import stop_policy

        self.fail_escalation(self.deferring, ("failure_family", "FR-001"))
        decision = finalize(self.root, self.inputs(self.deferring))["decisions"][0]
        self.assertEqual((decision["class"], decision["reason_code"]),
                         (stop_policy.EXHAUSTED, stop_policy.ALL_TIERS_FAILED))
        self.assertEqual(stop_policy.stop_class(decision["reason_code"]), decision["class"])

    def test_a_stop_reason_the_stop_policy_does_not_know_fails_closed(self) -> None:
        from speckit_pro_runner import stop_policy

        with self.assertRaises(ValueError):
            stop_policy.stop_class("made_up_reason")
        self.fail_escalation(self.deferring, ("failure_family", "FR-001"))
        with patch("speckit_pro_runner.helpers.run_finalization._exhausted_reason", return_value="made_up_reason"):
            with self.assertRaises(ValueError):
                finalize(self.root, self.inputs(self.deferring))

    def test_an_unresolved_deferred_task_is_an_authority_decision_not_a_draft_stack(self) -> None:
        result = finalize(self.root, self.inputs(unresolved_deferrals=[dict(VETO)]))
        self.assertEqual(result["outcome"], "complete_with_deferred")
        self.assertTrue(result["mark_ready"])
        self.assertEqual(len(result["decisions"]), 1)
        self.assertEqual({key: result["decisions"][0][key] for key in VETO} | {"class": result["decisions"][0]["class"]},
                         {**VETO, "class": "authority"})
        self.assertIn(VETO["finish"], result["end_of_run_request"])
        self.assertIn("Decisions for you", result["end_of_run_request"])

    def test_decisions_and_human_uat_alone_never_keep_the_stack_draft(self) -> None:
        self.fail_escalation(self.deferring, ("failure_family", "FR-001"))
        result = finalize(self.root, self.inputs(self.deferring, unresolved_deferrals=[dict(VETO)]))
        self.assertEqual((result["outcome"], result["goal_status"], result["mark_ready"]),
                         ("complete_with_deferred", "complete", True))
        self.assertEqual(sorted(decision["class"] for decision in result["decisions"]), ["authority", "exhausted"])
        self.assertEqual(result["deferred_items"], [UAT])


def _runner(request: dict[str, object], cwd: Path = REPO_ROOT) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        cwd=cwd,
        env={"PYTHONPATH": str(PLUGIN_ROOT), "PATH": os.defpath},
        check=False,
        timeout=60,
    )
    return json.loads(completed.stdout.splitlines()[-1])


class _ResolvedDeferralFixture(_LedgerFixture):
    """Shared fixture for the tests below."""

    SCOPE = "a" * 64

    def setUp(self) -> None:
        super().setUp()
        self.clock = 1000.0  # this ledger's fixes and its deferral share one reading
        spec = self.root / "resolved/spec.md"
        (self.root / "resolved").mkdir()
        (self.root / "resolved/workflow.md").write_text("# Workflow\n")
        self.run: dict[str, object] = {"workflow": "resolved/workflow.md"}
        self.invoke(self.run, "start")
        spec.write_text("- FR-001: preserve data\n- FR-002: no secrets\n")
        bound = self.invoke(self.run, "bind-invariants", spec_file="resolved/spec.md")
        self.spec_digest = bound["ledger"]["invariant_binding"]["spec_sha256"]
        for dispatch_id, invariant in (("fix-a", "FR-001"), ("fix-b", "FR-002")):
            self.invoke(self.run, "reserve", dispatch_id=dispatch_id, kind="corrective", failure_invariant=invariant)
            self.invoke(self.run, "complete", dispatch_id=dispatch_id, outcome="completed")
        deferred = self.invoke(self.run, "reserve", dispatch_id="fix-c", kind="corrective", failure_invariant="FR-001")
        assert deferred["reasons"] == ["failure_family_budget_exhausted"], deferred

    def fix_under_exception(self, outcome: str = "completed") -> dict[str, object]:
        event = {"native_event_id": "operator-exception", "run_id": self.run["run_id"],
                 "action": "corrective_exception_approved", "failure_invariant": "FR-001", "dispatch_id": "fix-c",
                 "failure_kind": "application", "refusal_reason": "failure_family_budget_exhausted",
                 "scope_sha256": self.SCOPE, "spec_sha256": self.spec_digest}
        self.invoke(self.run, "authorize-corrective-exception", dispatch_id="fix-c", failure_invariant="FR-001",
                    scope_sha256=self.SCOPE, native_observation=event)
        return self.invoke(self.run, "complete", dispatch_id="fix-c", outcome=outcome)

    def ledger_path(self) -> Path:
        return self.root / str(self.run["ledger_path"])

    def escalate_and_finalize(self, outcome: str, units: tuple[str, ...]) -> tuple[dict[str, object], dict[str, object]]:
        """Settle fix-c under the exception as `outcome`, exhaust each unit's tiers, then finalize the run."""
        self.invoke(self.run, "reserve", dispatch_id="fix-d", kind="corrective", failure_invariant="FR-002")
        settled = self.fix_under_exception(outcome)
        for unit in units:
            self.fail_escalation(self.run, ("failure_family", unit))
        result = finalize(self.root, self.inputs(self.run))
        self.assertEqual((result["outcome"], result["mark_ready"]), ("complete_with_deferred", True))
        return settled, result


class ResolvedDeferralTests(_ResolvedDeferralFixture, unittest.TestCase):
    """A deferral that a later completed dispatch for its unit resolved leaves the request (issue 825)."""

    def test_a_deferral_whose_fix_completed_leaves_the_request_and_keeps_its_history(self) -> None:
        completed = self.fix_under_exception()
        entry = completed["ledger"]["deferred"][0]
        self.assertEqual((entry["dispatch_id"], entry["unit"], entry["resolved_by"], entry["resolved_at"]),
                         ("fix-c", "FR-001", "fix-c", 1000.0))
        result = finalize(self.root, self.inputs(self.run))
        self.assertEqual(result["outcome"], "complete_with_deferred")
        self.assertTrue(result["mark_ready"])
        self.assertNotIn("FR-001", result["end_of_run_request"])
        self.assertEqual(len(json.loads(self.ledger_path().read_text())["deferred"]), 1)
        from speckit_pro_runner.helpers.read_only import json_schema_failures

        schema = json.loads((PLUGIN_ROOT / "speckit_pro_runner/contracts/execution-control.schema.json").read_text())
        self.assertEqual(json_schema_failures(completed["ledger"], schema, schema, "ledger"), [])

    def test_a_deferral_with_no_completed_fix_reaches_the_owner_as_a_decision(self) -> None:
        failed, result = self.escalate_and_finalize("failed", ("FR-001", "FR-002"))
        self.assertNotIn("resolved_by", failed["ledger"]["deferred"][0])
        self.assertEqual(sorted(unit["unit"] for unit in result["decisions"]),
                         ["Failure family FR-001", "Failure family FR-002"])

    def test_only_the_resolved_unit_leaves_the_request(self) -> None:
        _, result = self.escalate_and_finalize("completed", ("FR-002",))
        self.assertEqual([unit["unit"] for unit in result["decisions"]], ["Failure family FR-002"])


class ResolvedDeferralIntegrityTests(_ResolvedDeferralFixture, unittest.TestCase):
    """A forged resolution fails closed and an earlier ledger still validates."""

    def test_a_forged_resolution_fails_closed(self) -> None:
        self.invoke(self.run, "reserve", dispatch_id="fix-d", kind="corrective", failure_invariant="FR-002")
        self.fix_under_exception()
        valid = self.ledger_path().read_bytes()
        inputs = self.inputs(self.run)
        valid = self.ledger_path().read_bytes()
        tampers = {
            "claimed by a dispatch of another unit": lambda ledger: ledger["deferred"][1].update(
                resolved_by="fix-c", resolved_at=1000.0),
            "claimed by an unknown dispatch": lambda ledger: ledger["deferred"][1].update(
                resolved_by="operator-said-so", resolved_at=1000.0),
            "claimed by a dispatch reserved before the deferral": lambda ledger: ledger["deferred"][1].update(
                resolved_by="fix-b", resolved_at=1000.0),
            "resolution clock disagrees": lambda ledger: ledger["deferred"][0].update(resolved_at=999.0),
            "resolution without its clock": lambda ledger: ledger["deferred"][0].pop("resolved_at"),
            "resolving dispatch did not complete": lambda ledger: ledger["dispatches"]["fix-c"].update(
                outcome="failed"),
        }
        for name, tamper in tampers.items():
            with self.subTest(tamper=name):
                ledger = json.loads(valid)
                if name == "claimed by a dispatch reserved before the deferral":
                    ledger["deferred"][1]["deferred_at"] = 1000.0
                    ledger["dispatches"]["fix-b"]["reserved_at"] = 999.0
                tamper(ledger)
                self.ledger_path().write_text(json.dumps(ledger), encoding="utf-8")
                with self.assertRaises(ValueError):
                    finalize(self.root, inputs)

    def test_a_ledger_from_an_earlier_version_still_validates_and_reports_its_deferral(self) -> None:
        self.fix_under_exception()
        legacy = json.loads(self.ledger_path().read_text())
        for entry in legacy["deferred"]:
            entry.pop("resolved_by", None)
            entry.pop("resolved_at", None)
        self.ledger_path().write_text(json.dumps(legacy), encoding="utf-8")
        result = finalize(self.root, self.inputs(self.run))
        self.assertEqual(result["outcome"], "continue")
        self.assertTrue(any("Failure family FR-001" in item for item in result["pending_items"]))
        self.fail_escalation(self.run, ("failure_family", "FR-001"))
        result = finalize(self.root, self.inputs(self.run))
        self.assertEqual(result["outcome"], "complete_with_deferred")
        self.assertEqual([unit["unit"] for unit in result["decisions"]], ["Failure family FR-001"])


class EscalationBeforeStopTests(_LedgerFixture, unittest.TestCase):
    """A failed unit climbs tier 2 then tier 3 before it becomes a decision or a red-gate stop (issue 829)."""

    def test_a_deferred_unit_climbs_both_tiers_before_it_becomes_a_decision(self) -> None:
        before = finalize(self.root, self.inputs(self.deferring))
        self.assertEqual((before["outcome"], before["goal_status"], before["human_stop"]), ("continue", "not_complete", None))
        self.assertFalse(before["mark_ready"])
        self.assertEqual(before["ready_commands"], [])
        self.assertIn("Escalate Failure family FR-001 to tier 2", before["pending_items"][0])
        self.assertIn("different approach", before["pending_items"][0])
        self.assertIn("consensus", before["pending_items"][0])
        self.fail_escalation(self.deferring, ("failure_family", "FR-001"), tiers=(2,), outcome=None)
        running = finalize(self.root, self.inputs(self.deferring))
        self.assertEqual(running["outcome"], "continue")
        self.assertIn("Finish the escalation retry", running["pending_items"][0])
        self.clock += 10
        self.invoke(self.deferring, "complete", dispatch_id="escalate-failure_family-FR-001-tier-2", outcome="failed")
        tier_three = finalize(self.root, self.inputs(self.deferring))
        self.assertEqual(tier_three["outcome"], "continue")
        self.assertIn("Escalate Failure family FR-001 to tier 3", tier_three["pending_items"][0])
        self.assertIn("strongest model at max effort with the full failure history", tier_three["pending_items"][0])
        self.fail_escalation(self.deferring, ("failure_family", "FR-001"), tiers=(3,))
        after = finalize(self.root, self.inputs(self.deferring))
        self.assertEqual((after["outcome"], after["mark_ready"]), ("complete_with_deferred", True))
        self.assertIn("escalation tiers are exhausted", after["decisions"][0]["reason"])
        self.assertEqual(after["decisions"][0]["reason_code"], "all_tiers_failed")

    def test_the_tier_three_cap_sends_a_unit_straight_to_the_decisions(self) -> None:
        for number in range(3):
            gate = {"gate": f"X{number}", "status": "failed", "command": f"python3 tests/x{number}.py",
                    "head_sha": HEADS[101]}
            digest = command_digest(gate["command"])
            self.verification(self.deferring, gate)
            self.fail_escalation(self.deferring, ("gate_failure", digest), tiers=(2,))
            self.verification(self.deferring, gate)
            self.fail_escalation(self.deferring, ("gate_failure", digest), tiers=(3,))
        self.fail_escalation(self.deferring, ("failure_family", "FR-001"), tiers=(2,))
        result = finalize(self.root, self.inputs(self.deferring))
        self.assertEqual((result["outcome"], result["mark_ready"]), ("complete_with_deferred", True))
        self.assertEqual(result["decisions"][0]["reason_code"], "tier3_cap_reached")
        self.assertIn("tier 2", result["decisions"][0]["evidence"])
        ledger = json.loads((self.root / str(self.deferring["ledger_path"])).read_text())
        self.assertEqual(ledger["escalation_tier3_cap"], 3)

    def test_a_completed_tier_resolves_the_unit_and_the_run_finalizes(self) -> None:
        self.fail_escalation(self.deferring, ("failure_family", "FR-001"), tiers=(2,), outcome="completed")
        result = finalize(self.root, self.inputs(self.deferring))
        self.assertEqual(result["outcome"], "complete_with_deferred")
        self.assertTrue(result["mark_ready"])
        self.assertEqual(result["decisions"], [])


class EscalationGateStopTests(_LedgerFixture, unittest.TestCase):
    """A failed gate climbs the tiers before it keeps the stack draft, and forged escalation records fail closed."""

    def test_a_failed_gate_climbs_the_tiers_before_it_keeps_the_stack_draft(self) -> None:
        gates = self.per_head_gates(failed=(HEADS[103], "G7"))
        inputs = self.inputs(gates=gates)
        failed = next(gate for gate in inputs["gates"] if gate["status"] == "failed")  # type: ignore[attr-defined]
        digest = command_digest(failed["command"])
        first = finalize(self.root, inputs)
        self.assertEqual(first["outcome"], "continue")
        self.assertIn("Escalate failed gate G7 at head", first["pending_items"][0])
        self.assertIn("tier 2", first["pending_items"][0])
        self.fail_escalation(self.clean, ("gate_failure", digest), tiers=(2,), outcome="completed")
        rerun = finalize(self.root, inputs)
        self.assertEqual(rerun["outcome"], "continue")
        self.assertIn("Rerun gate G7", rerun["pending_items"][0])
        red_again = self.inputs(gates=gates)
        tier_three = finalize(self.root, red_again)
        self.assertIn("tier 3", tier_three["pending_items"][0])
        self.fail_escalation(self.clean, ("gate_failure", digest), tiers=(3,))
        result = finalize(self.root, red_again)
        self.assertEqual((result["outcome"], result["goal_status"], result["mark_ready"]), ("human_stop", "blocked", False))
        self.assertEqual((result["human_stop"]["gates"][0]["gate"], result["human_stop"]["gates"][0]["reason_code"]),
                         ("G7", "all_tiers_failed"))

    def per_head_gates(self, failed: tuple[str, str]) -> list[dict[str, object]]:
        return [dict(gate, status="failed") if (gate["head_sha"], gate["gate"]) == failed else gate
                for gate in per_head(*GREEN)]

    def test_forged_escalation_records_fail_closed(self) -> None:
        path = self.root / str(self.deferring["ledger_path"])
        self.fail_escalation(self.deferring, ("failure_family", "FR-001"))
        inputs = self.inputs(self.deferring)
        valid = path.read_bytes()
        record = json.loads(valid)["escalation_allowances"]["failure_family:FR-001"]
        forged_dispatch = {"kind": "corrective", "outcome": "failed", "reserved_at": 1000.0, "completed_at": 1000.0,
                           "reservation_id": None, "reconciliations": 0}
        tampers = {
            "failed dispatch that claims an escalation with no allowance": lambda ledger: (
                ledger.pop("escalation_allowances"),
                ledger["dispatches"].update(
                    {"forged": {**forged_dispatch, "escalation": "failure_family:FR-001"}})),
            "allowance that names no dispatch": lambda ledger: ledger["escalation_allowances"][
                "failure_family:FR-001"].update(dispatch_id="never-ran"),
            "allowance for a unit that never failed": lambda ledger: ledger["escalation_allowances"].update(
                {"failure_family:FR-002": {**record, "unit": "FR-002"}}),
            "allowance for a passing verification": lambda ledger: (
                ledger["dispatches"].update({"verify-p": {**forged_dispatch, "kind": "verification"}}),
                ledger["escalation_allowances"].update(
                    {"gate_failure:verify-p": {**record, "unit_kind": "gate_failure", "unit": "verify-p"}})),
            "escalation marker dropped from a dispatch": lambda ledger: ledger["dispatches"][
                "escalate-failure_family-FR-001-tier-2"].pop("escalation"),
        }
        for name, tamper in tampers.items():
            with self.subTest(tamper=name):
                ledger = json.loads(valid)
                tamper(ledger)
                path.write_text(json.dumps(ledger), encoding="utf-8")
                with self.assertRaises(ValueError):
                    finalize(self.root, inputs)


class GateStatusFromRunnerRecordsTests(_LedgerFixture, unittest.TestCase):
    """A gate's status is the runner's own verification record, never the caller's claim (issue 829)."""

    def gate(self, status: str = "passed", **changes: object) -> dict[str, object]:
        """One G7 result at the tip, backed by a verification dispatch with `changes` to its evidence."""
        base = {"gate": "G7", "status": status, "command": "python3 tests/run-all.py", "head_sha": HEADS[103]}
        return {**base, "dispatch_id": self.verification(self.clean, base, **changes)}

    def finalize_tip(self, gate: dict[str, object]) -> dict[str, object]:
        prs = [pr for pr in self.inputs()["pull_requests"] if pr["head_sha"] == HEADS[103]]  # type: ignore[attr-defined]
        return finalize(self.root, self.inputs(pull_requests=prs, gates=[gate]))

    def test_a_forged_passed_status_no_longer_finalizes_ready(self) -> None:
        failing = self.gate("failed")
        with self.assertRaisesRegex(ValueError, "claims passed, but the runner's verification record shows failed"):
            self.finalize_tip({**failing, "status": "passed"})
        unparsed = self.gate("failed", format="unparsed", failing=None, checks_run=None)
        with self.assertRaisesRegex(ValueError, "shows failed"):
            self.finalize_tip({**unparsed, "status": "passed"})

    def test_a_forged_failed_status_does_not_stop_a_passing_run(self) -> None:
        with self.assertRaisesRegex(ValueError, "claims failed, but the runner's verification record shows passed"):
            self.finalize_tip({**self.gate("passed"), "status": "failed"})

    def test_the_runner_record_decides_the_status_and_an_unparsed_failure_is_failed(self) -> None:
        self.assertEqual(self.finalize_tip(self.gate("passed"))["outcome"], "complete_with_deferred")
        unparsed = self.gate("failed", format="unparsed", failing=None, checks_run=None)
        self.assertEqual(self.finalize_tip(unparsed)["outcome"], "continue")

    def test_a_status_the_runner_did_not_record_never_counts(self) -> None:
        base = self.gate("passed")
        cases: dict[str, dict[str, object]] = {
            "no dispatch": {"dispatch_id": "never-ran"},
            "another command": {"command": "python3 tests/other.py"},
            "another head": {"head_sha": HEADS[102]},
        }
        for name, change in cases.items():
            with self.subTest(case=name), self.assertRaises(ValueError):
                self.finalize_tip({**base, **change})
        for name, evidence in {"verified at another head": {"head_sha": HEADS[102]},
                               "dirty worktree": {"worktree_clean": False},
                               "no head recorded": {"head_sha": DROP, "worktree_clean": DROP}}.items():
            with self.subTest(case=name), self.assertRaises(ValueError):
                self.finalize_tip(self.gate("passed", **evidence))
        self.invoke(self.clean, "reserve", dispatch_id="not-a-verification", kind="implementation")
        with self.assertRaises(ValueError):
            self.finalize_tip({**base, "dispatch_id": "not-a-verification"})
        unbacked = self.inputs(gates=[{key: value for key, value in base.items() if key != "dispatch_id"}])
        unbacked["gates"] = [{key: value for key, value in gate.items() if key != "dispatch_id"}
                             for gate in unbacked["gates"]]  # type: ignore[attr-defined]
        with self.assertRaisesRegex(ValueError, "dispatch_id of the verification the runner ran"):
            finalize(self.root, unbacked)

    def test_one_verification_never_backs_two_gate_results(self) -> None:
        gate = self.gate("passed")
        twin = {**gate, "gate": "G8"}
        prs = [pr for pr in self.inputs()["pull_requests"] if pr["head_sha"] == HEADS[103]]  # type: ignore[attr-defined]
        with self.assertRaisesRegex(ValueError, "already backs another gate result"):
            finalize(self.root, self.inputs(pull_requests=prs, gates=[gate, twin]))


class MissingGateAcrossCyclesTests(_LedgerFixture, unittest.TestCase):
    """A gate missing at one PR head is pending work first and stops only if it stays missing (issue 829)."""

    TIP_ONLY = per_head(*GREEN, heads=(HEADS[103],))

    def ledger_counts(self) -> dict[str, int]:
        ledger = json.loads((self.root / str(self.clean["ledger_path"])).read_text())
        return ledger.get("finalize_observations", {})

    def test_a_missing_head_gate_continues_and_then_stops_when_it_stays_missing(self) -> None:
        first = finalize(self.root, self.inputs(gates=self.TIP_ONLY), record=True)
        self.assertEqual((first["outcome"], first["human_stop"], first["mark_ready"]), ("continue", None, False))
        self.assertFalse(first["writes_state"])
        self.assertEqual(len(first["observed"]), 4)
        self.assertEqual(len(first["pending_items"]), 4)
        self.assertIn(f"Run gate G7 at head {HEADS[101]} of PR #101: python3 tests/run-all.py", first["pending_items"])
        self.assertEqual(len(self.ledger_counts()), 4)
        second = finalize(self.root, self.inputs(gates=self.TIP_ONLY), record=True)
        self.assertEqual(second["outcome"], "human_stop")
        self.assertEqual(len(second["human_stop"]["missing"]), 4)
        self.assertFalse(second["writes_state"])
        self.assertEqual(second["pending_items"], [])

    def test_a_gate_that_is_run_before_the_next_cycle_finalizes_the_stack(self) -> None:
        self.assert_finalizes_after_a_recorded_cycle(self.TIP_ONLY)

    def test_only_a_recording_cycle_counts_and_a_read_only_look_never_stops_the_run(self) -> None:
        for _ in range(3):
            result = finalize(self.root, self.inputs(gates=self.TIP_ONLY))
            self.assertEqual((result["outcome"], result["writes_state"]), ("continue", False))
        self.assertEqual(self.ledger_counts(), {})

    def test_a_stop_needs_the_same_head_and_gate_seen_missing_before(self) -> None:
        seen = per_head(*GREEN, heads=(HEADS[101], HEADS[103]))
        finalize(self.root, self.inputs(gates=seen), record=True)
        result = finalize(self.root, self.inputs(gates=per_head(*GREEN, heads=(HEADS[102], HEADS[103]))))
        self.assertEqual((result["outcome"], result["human_stop"]), ("continue", None))
        self.assertTrue(all(f"head {HEADS[101]}" in item for item in result["pending_items"]))

    def test_the_count_stops_at_its_cap_and_a_request_for_another_ledger_is_refused(self) -> None:
        from speckit_pro_runner.execution_control import FINALIZE_OBSERVATION_CAP

        inputs = self.inputs(gates=self.harness_gates())  # stays pending, so each cycle counts it again
        for _ in range(FINALIZE_OBSERVATION_CAP + 2):
            finalize(self.root, inputs, record=True)
        self.assertEqual(set(self.ledger_counts().values()), {FINALIZE_OBSERVATION_CAP})
        for name, change in {"another run": {"expected_run_id": "another-run"},
                             "another ledger": {"ledger_path": self.deferring["ledger_path"]}}.items():
            with self.subTest(request=name), self.assertRaises(ValueError):
                with patch("speckit_pro_runner.execution_control.time.time", return_value=5000.0):
                    execution_control(self.root, {"workflow_file": "clean/workflow.md", "action": "record-finalize-cycle",
                                                  "expected_run_id": self.clean["run_id"],
                                                  "ledger_path": self.clean["ledger_path"],
                                                  "finalize_inputs": {**inputs, **change}}, "apply")

    def test_a_forged_observation_count_fails_closed(self) -> None:
        finalize(self.root, self.inputs(gates=self.TIP_ONLY), record=True)
        path = self.root / str(self.clean["ledger_path"])
        ledger = json.loads(path.read_text())
        ledger["finalize_observations"] = {f"missing_gate:{HEADS[101]}:G7": 99}
        path.write_text(json.dumps(ledger), encoding="utf-8")
        with self.assertRaises(ValueError):
            finalize(self.root, self.inputs(gates=self.TIP_ONLY))


class HarnessExtraAttemptTests(_LedgerFixture, unittest.TestCase):
    """One extra harness attempt in a changed environment comes before a harness error stops (issue 829)."""

    def test_a_harness_error_continues_for_one_changed_environment_attempt_first(self) -> None:
        first = finalize(self.root, self.inputs(gates=self.harness_gates()), record=True)
        self.assertEqual((first["outcome"], first["human_stop"]), ("continue", None))
        self.assertIn("changed environment (fresh_worktree or cleared_caches)", first["pending_items"][0])
        self.assertIn("`attempts` 4", first["pending_items"][0])

    def test_the_extra_attempt_alone_never_stops_the_run_without_an_earlier_counted_cycle(self) -> None:
        result = finalize(self.root, self.inputs(gates=self.changed_environment_gates()))
        self.assertEqual(result["outcome"], "continue")

    def test_a_repeat_at_the_budget_stays_pending_until_the_changed_environment_attempt_shows(self) -> None:
        for _ in range(3):
            result = finalize(self.root, self.inputs(gates=self.harness_gates()), record=True)
            self.assertEqual(result["outcome"], "continue")
        self.assertEqual(finalize(self.root, self.inputs(gates=self.harness_gates()))["outcome"], "continue")
        stopped = finalize(self.root, self.inputs(gates=self.changed_environment_gates()))
        self.assertEqual(stopped["outcome"], "human_stop")

    def test_a_later_pass_in_the_changed_environment_finalizes(self) -> None:
        self.assert_finalizes_after_a_recorded_cycle(self.harness_gates())


class FinalizeRunRegistryTests(unittest.TestCase):
    def test_fixture_request_runs_through_the_runner(self) -> None:
        # The fixture ledger holds a deferral whose escalation tiers all failed, so the request finalizes ready
        # with that unit under "Decisions for you".
        response = _runner(json.loads(FIXTURE_REQUEST.read_text(encoding="utf-8")))
        self.assertEqual(response["status"], "ok", response)
        data = response["data"]
        self.assertEqual(data["helper_id"], HELPER_ID)
        self.assertEqual(data["outcome"], "complete_with_deferred")
        self.assertEqual(data["goal_status"], "complete")
        self.assertEqual([decision["class"] for decision in data["decisions"]], ["exhausted"])
        self.assertIn("Decisions for you", data["end_of_run_request"])
        self.assertFalse(data["writes_state"])

    def test_bad_request_is_an_input_error(self) -> None:
        request = json.loads(FIXTURE_REQUEST.read_text(encoding="utf-8"))
        request["inputs"]["gates"] = []
        self.assertEqual(_runner(request)["status"], "input_error")


class FinalizeRunCycleCountTests(unittest.TestCase):
    """The finalize cycle count is reachable through the runner and only moves toward a stop."""

    def test_the_cycle_count_is_reachable_through_the_runner_and_only_ever_moves_toward_a_stop(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = REPO_ROOT / "tests/speckit-pro/unit/fixtures/run-finalization/.process/execution-control/ledger.json"
            (root / ".process/execution-control").mkdir(parents=True)
            (root / ".specify").mkdir()
            (root / ".specify/project.json").write_text("{}", encoding="utf-8")
            (root / "feature").mkdir()
            (root / "feature/workflow.md").write_text("# Workflow\n", encoding="utf-8")
            (root / ".process/execution-control/ledger.json").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            request = json.loads(FIXTURE_REQUEST.read_text(encoding="utf-8"))
            request["inputs"]["ledger_path"] = ".process/execution-control/ledger.json"
            tip = request["inputs"]["pull_requests"][-1]["head_sha"]
            request["inputs"]["gates"] = [gate for gate in request["inputs"]["gates"]
                                          if not (gate["head_sha"] == tip and gate["gate"] != "G7")]
            request["inputs"]["pull_requests"][0]["draft"] = True

            def call(payload: dict[str, object]) -> dict[str, object]:
                return _runner(payload, root)

            first = call(request)
            self.assertEqual((first["status"], first["data"]["outcome"]), ("ok", "continue"), first)
            self.assertEqual(len(first["data"]["observed"]), 1)
            self.assertEqual(call({**request, "mode": "apply"})["status"], "input_error")
            recorded = call({"schema_version": "1.0", "request_id": "record-cycle", "helper_id": "execution-control",
                             "operation": "execution-control", "mode": "apply",
                             "inputs": {"workflow_file": "feature/workflow.md", "action": "record-finalize-cycle",
                                        "expected_run_id": request["inputs"]["expected_run_id"],
                                        "ledger_path": ".process/execution-control/ledger.json",
                                        "finalize_inputs": request["inputs"]}})
            self.assertEqual(recorded["status"], "ok", recorded)
            self.assertEqual(recorded["data"]["finalize_observed"], first["data"]["observed"])
            self.assertEqual(recorded["data"]["ledger"]["finalize_observations"],
                             {first["data"]["observed"][0]: 1})
            second = call(request)
            self.assertEqual((second["data"]["outcome"], second["data"]["mark_ready"]), ("human_stop", False))
            self.assertEqual(len(second["data"]["human_stop"]["missing"]), 1)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-finalize-run"))
