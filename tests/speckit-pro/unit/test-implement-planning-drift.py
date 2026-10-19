#!/usr/bin/env python3
"""Planning drift during implement blocks the affected work and keeps verified independent work going (ADR 0013)."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
sys.path.insert(0, str(HERE.parents[2] / "speckit-pro"))

from guide_text import GuidePhrases, assert_guides_document
from script_loader import load_script
from test_result import run_counted
from speckit_pro_runner.helpers.read_only import json_schema_failures
from speckit_pro_runner.task_execution import fingerprints

AdmissionFixture = load_script("implement_admission_tests", HERE / "test-implement-admission.py").AdmissionFixture

TASKS = "## Phase 3: Stories\n" + "".join(f"- [ ] T00{n} Build part {n}\n" for n in range(1, 5))
DEPENDS = {"T001": [], "T002": ["T001"], "T003": ["T002"], "T004": []}
UNITS = {"T001": "alpha", "T002": "beta", "T003": "gamma", "T004": "delta"}
OWNS = {"T004": ["src/delta", "specs/demo/quickstart.md"]}
SCHEMA = json.loads((HERE.parents[2] / "speckit-pro/speckit_pro_runner/contracts/execution-control.schema.json").read_text())


class DriftFixture(AdmissionFixture):
    """An approved four-task feature whose implement run has started; T002 and T003 depend on T001."""

    OWNS = OWNS

    def setUp(self):
        super().setUp()
        self.write_tasks(TASKS)
        _, self.approved = self.record()
        self.run_id = None
        self.control("start")

    def write_tasks(self, text):
        (self.feature / "tasks.md").write_text(text)
        (self.feature / ".process").mkdir(exist_ok=True)
        sidecar = {"schema_version": "task-execution.v1",
                   "fingerprints": fingerprints("A feature", "A plan", text),
                   "tasks": {task: {"capability_group": "stories", "depends_on": deps, "owns": self.OWNS.get(task, [f"src/{UNITS[task]}"]),
                                    "tdd_unit": UNITS[task]} for task, deps in DEPENDS.items()}}
        (self.feature / ".process/task-execution.json").write_text(json.dumps(sidecar))

    def control(self, action, mode="apply", **inputs):
        binding = {"expected_run_id": self.run_id} if self.run_id else {}
        reply = self.run_helper("execution-control", {"workflow_file": self.workflow_file, "action": action,
                                                      **binding, **inputs}, mode=mode)
        if reply["status"] in ("ok", "expected_failure") and mode == "apply":
            self.run_id = reply["data"]["ledger"]["run_id"]
        return reply

    def dispatch(self, unit, **inputs):
        return self.control("reserve", dispatch_id=f"{unit}-{len(self.ledger()['dispatches'])}",
                            kind="implementation", tdd_units=[unit], **inputs)

    def ledger(self):
        ledger = self.control("status", mode="read_only")["data"]["ledger"]
        self.assertEqual(json_schema_failures(ledger, SCHEMA, SCHEMA, "ledger"), [])
        return ledger

    def entries(self):
        return self.ledger()["blocked_work"]["entries"]

    def assertContinues(self, reply):
        self.assertEqual((reply["status"], reply["data"]["disposition"]), ("ok", "continue"), reply)

    def assertBlocked(self, reply):
        self.assertEqual(reply["data"]["reasons"], ["blocked_for_uat"], reply)

    def assertWriteIsDrift(self, dispatched, name):
        """After `dispatched` runs, writing the feature file `name` blocks every remaining task."""
        self.assertContinues(self.dispatch(dispatched))
        (self.feature / name).write_text("Planned elsewhere\n")
        self.assertBlocked(self.dispatch("delta"))
        (cause,) = self.ledger()["blocked_work"]["causes"].values()
        self.assertEqual((cause["changed_files"], cause["drifted_tasks"]), ([f"specs/demo/{name}"], None))


class PinnedRevisionTest(DriftFixture):
    def test_the_first_task_dispatch_pins_the_approved_revision(self):
        self.assertContinues(self.dispatch("alpha"))
        pinned = self.ledger()["planning_binding"]
        self.assertEqual(pinned["manifest_digest"], self.approved["manifest_digest"])
        self.assertEqual(sorted(pinned["tasks"]), sorted(DEPENDS))

    def test_an_approved_run_pins_even_when_the_workflow_shows_planning_open(self):
        workflow = self.feature / "workflow.md"
        workflow.write_text(workflow.read_text().replace("| Confidence Gate | G6.5 | ✅ Complete |",
                                                         "| Confidence Gate | G6.5 | 🔄 In Progress |"))
        self.assertContinues(self.dispatch("alpha"))
        self.assertEqual(self.ledger()["planning_binding"]["manifest_digest"], self.approved["manifest_digest"])

    def test_a_task_dispatch_without_a_valid_approval_is_refused_by_name(self):
        for path in self.feature.glob("plan-approvals/*.json"):
            path.unlink()
        reply = self.dispatch("alpha")
        self.assertRefused(reply, "planning approval field record:")

    def test_ordinary_implement_writes_are_not_drift(self):
        self.assertContinues(self.dispatch("alpha"))
        self.control("complete", dispatch_id="alpha-0", outcome="completed")
        (self.feature / "tasks.md").write_text(TASKS.replace("- [ ] T001", "- [x] T001"))
        (self.feature / ".process/implementation-notes.md").write_text("T001: built part 1\n")
        (self.feature / ".process/task-results").mkdir(exist_ok=True)
        (self.feature / ".process/task-results/run.json").write_text("{}")
        (self.feature / "workflow.md").write_text((self.feature / "workflow.md").read_text().replace(
            "| Implement | `/speckit-implement` | ⏳ Pending |", "| Implement | `/speckit-implement` | 🔄 In Progress |").replace(
            "| **Stage** | plan |", "| **Stage** | implement |"))
        (self.root / "src").mkdir()
        (self.root / "src/alpha.py").write_text("PART = 1\n")
        self.assertContinues(self.dispatch("beta"))
        self.assertNotIn("blocked_work", self.ledger())


class DriftBlockTest(DriftFixture):
    def test_a_changed_task_blocks_it_and_its_dependents_while_independent_work_continues(self):
        self.assertContinues(self.dispatch("delta"))
        self.write_tasks(TASKS.replace("Build part 1", "Build part 1 twice"))
        self.assertContinues(self.dispatch("delta"))
        entries = self.entries()
        self.assertEqual(sorted(entries), ["task:T001", "task:T002", "task:T003"])
        self.assertEqual({entry["reason"] for entry in entries.values()}, {"planning_drift"})
        self.assertEqual({entry["attempted"] for entry in entries.values()}, {False})
        self.assertEqual({entry["plan_sha256"] for entry in entries.values()},
                         {self.approved["manifest"]["files"]["specs/demo/tasks.md"]})
        (cause,) = self.ledger()["blocked_work"]["causes"].values()
        self.assertEqual(cause["approved_manifest_digest"], self.approved["manifest_digest"])
        self.assertEqual(cause["drifted_tasks"], ["T001"])
        self.assertIn("specs/demo/tasks.md", cause["changed_files"])
        for unit in ("alpha", "beta", "gamma"):
            with self.subTest(unit=unit):
                self.assertBlocked(self.dispatch(unit))

    def test_a_task_writing_a_planning_file_it_owns_is_drift(self):
        self.assertWriteIsDrift("delta", "quickstart.md")

    def test_owned_outputs_outside_the_planning_manifest_are_not_drift(self):
        self.assertContinues(self.dispatch("delta"))
        (self.root / "src/delta").mkdir(parents=True)
        (self.root / "src/delta/result.py").write_text("RESULT = 4\n")
        self.assertContinues(self.dispatch("alpha"))
        self.assertNotIn("blocked_work", self.ledger())

    def test_a_planning_file_owned_by_an_undispatched_task_is_drift(self):
        self.assertWriteIsDrift("alpha", "quickstart.md")

    def test_a_unit_the_approved_plan_does_not_define_is_refused_in_any_request(self):
        self.assertContinues(self.dispatch("alpha"))
        reply = self.control("reserve", dispatch_id="fix", kind="corrective", failure_invariant="FR-001",
                             spec_file="specs/demo/spec.md",
                             review_remediation={"tdd_unit": "epsilon", "paths": ["src/epsilon"]})
        self.assertRefused(reply, "names a TDD unit the approved plan does not define")


class WholePlanChangeTest(DriftFixture):
    """A change to a plan input beyond one task's text blocks every task still open, never one task's dependents."""

    CHANGES = {
        "a_changed_spec": lambda case: (case.feature / "spec.md").write_text("A different feature"),
        "a_changed_heading": lambda case: case.write_tasks(TASKS.replace("Phase 3", "Phase 4")),
        "a_blank_line_between_tasks": lambda case: case.write_tasks(TASKS.replace("- [ ] T003", "\n- [ ] T003")),
        "missing_task_metadata": lambda case: (case.feature / ".process/task-execution.json").unlink(),
        "an_added_task": lambda case: case.write_tasks(TASKS + "- [ ] T005 Build part 5\n"),
    }

    def assertBlocksAllRemainingWork(self, change):
        self.assertContinues(self.dispatch("alpha"))
        self.control("complete", dispatch_id="alpha-0", outcome="completed")
        change(self)
        self.assertBlocked(self.dispatch("delta"))
        self.assertEqual(sorted(self.entries()), ["task:T002", "task:T003", "task:T004"])
        (cause,) = self.ledger()["blocked_work"]["causes"].values()
        self.assertIsNone(cause["drifted_tasks"])

    def test_an_added_task_is_never_dispatched(self):
        self.assertBlocksAllRemainingWork(self.CHANGES["an_added_task"])
        self.assertRefused(self.dispatch("epsilon"), "names a TDD unit the approved plan does not define")


for _name, _change in WholePlanChangeTest.CHANGES.items():
    setattr(WholePlanChangeTest, f"test_{_name}_blocks_all_remaining_work",
            lambda self, change=_change: self.assertBlocksAllRemainingWork(change))


class UnscopedWorkDriftTest(DriftFixture):
    def test_unscoped_work_waits_after_drift(self):
        self.assertContinues(self.dispatch("delta"))
        self.write_tasks(TASKS.replace("Build part 1", "Build part 1 twice"))
        self.assertContinues(self.dispatch("delta"))
        for action, inputs in (("reserve", {"kind": "implementation"}),
                               ("reserve", {"kind": "corrective", "failure_invariant": "FR-001"}),
                               ("reserve", {"kind": "infrastructure"}),
                               ("reserve-retry-rung", {"host": "claude", "command_sha256": "a" * 64})):
            with self.subTest(action=action, kind=inputs.get("kind")):
                self.assertBlocked(self.control(action, dispatch_id=f"unscoped-{action}", **inputs))
        self.assertContinues(self.control("reserve", dispatch_id="verify", kind="verification"))

    def test_ineligible_independent_remediation_cannot_fall_back_to_unscoped_work_after_drift(self):
        self.assertContinues(self.dispatch("delta"))
        self.write_tasks(TASKS.replace("Build part 1", "Build part 1 twice"))
        requests = {"review_remediation": ["src/alpha"], "test_fix": ["tests/delta.py"]}
        for field, paths in requests.items():
            with self.subTest(field=field):
                reply = self.control("reserve", mode="dry_run", dispatch_id=field, kind="corrective",
                                     failure_invariant="FR-001", spec_file="specs/demo/spec.md",
                                     **{field: {"tdd_unit": "delta", "paths": paths}})
                self.assertBlocked(reply)
        for field, paths in requests.items():
            reply = self.control("reserve", dispatch_id=field, kind="corrective", failure_invariant="FR-001",
                                 spec_file="specs/demo/spec.md", **{field: {"tdd_unit": "delta", "paths": paths}})
            self.assertBlocked(reply)
            self.assertNotIn(field, self.ledger()["dispatches"])
        self.assertEqual(self.ledger()["corrective_cycles"], 0)
        self.assertContinues(self.control("reserve", dispatch_id="independent-review", kind="corrective",
                                         spec_file="specs/demo/spec.md",
                                         review_remediation={"tdd_unit": "delta", "paths": ["src/delta"]}))


class FeatureOwnerDriftTest(DriftFixture):
    """T004 owns the whole feature directory; that ownership never covers the plan's own inputs."""

    OWNS = {"T004": ["src/delta", "specs/demo"]}

    def test_owning_the_feature_directory_exempts_no_planning_file(self):
        self.assertWriteIsDrift("delta", "data-model.md")


class OwnedPlanningFixture(DriftFixture):
    """Ownership permits writes, but cannot exempt an approval manifest input."""

    OWNS = {"T004": ["src/delta", "specs/demo/spec.md", "specs/demo/plan.md", "specs/demo/tasks.md",
                     "specs/demo/.process", "specs/demo/workflow.md", "specs/demo/contracts",
                     ".specify", "AGENTS.md", "formal"]}

    def assertChangedInputsBlock(self, expected):
        self.assertBlocked(self.dispatch("beta"))
        (cause,) = self.ledger()["blocked_work"]["causes"].values()
        self.assertEqual(cause["changed_files"], sorted(expected))
        self.assertEqual(sorted(self.entries()), [f"task:{task}" for task in DEPENDS])


class OwnedPlanningInputTest(OwnedPlanningFixture):
    def test_exact_feature_planning_sources_cannot_be_exempted(self):
        self.assertContinues(self.dispatch("delta"))
        (self.feature / "spec.md").write_text("Changed feature")
        (self.feature / "plan.md").write_text("Changed plan")
        self.write_tasks(TASKS.replace("Phase 3", "Phase 4"))
        self.assertChangedInputsBlock([f"specs/demo/{name}" for name in
                                      ("spec.md", "plan.md", "tasks.md", ".process/task-execution.json")])

    def test_owned_workflow_and_subtree_mutations_remain_visible(self):
        contracts = self.feature / "contracts"
        contracts.mkdir()
        (contracts / "remove.md").write_text("Remove this input")
        (contracts / "rename.md").write_text("Rename this input")
        self.record()
        self.assertContinues(self.dispatch("delta"))
        (contracts / "remove.md").unlink()
        (contracts / "rename.md").rename(contracts / "renamed.md")
        (contracts / "added.md").write_text("New input")
        workflow = self.feature / "workflow.md"
        workflow.write_text(workflow.read_text() + "\nChanged planning instructions\n")
        self.assertChangedInputsBlock(["specs/demo/workflow.md", *[f"specs/demo/contracts/{name}.md" for name in
                                                               ("remove", "rename", "renamed", "added")]])

    def test_owned_project_and_catalog_inputs_remain_visible(self):
        inputs = (".specify/templates/plan.md", "AGENTS.md", "formal/model.tla")
        for name in inputs:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("Original input")
        (self.root / ".specify/formal-methods.json").write_text(json.dumps(
            {"models": {"demo": {"inputs": ["formal/model.tla"]}}}))
        self.record()
        self.assertContinues(self.dispatch("delta"))
        for name in inputs:
            (self.root / name).write_text("Changed input")
        self.assertChangedInputsBlock(inputs)


class AliasOwnedPlanningInputTest(OwnedPlanningFixture):
    """Case folding and Unicode normalization never remove changed planning inputs."""

    OWNS = {"T004": ["src/delta", "specs/demo/PLAN.md", "specs/demo/caf\u00e9"]}

    def test_case_and_unicode_ownership_aliases_cannot_hide_drift(self):
        target = self.feature / "cafe\u0301/contract.md"
        target.parent.mkdir()
        target.write_text("Original contract")
        self.record()
        self.assertContinues(self.dispatch("delta"))
        (self.feature / "plan.md").write_text("Changed plan")
        target.write_text("Changed contract")
        self.assertChangedInputsBlock(["specs/demo/plan.md", target.relative_to(self.root).as_posix()])


class CorrectiveDriftFixture(DriftFixture):
    """A pinned run with spent corrective cycles and eligible follow-up requests."""

    def prepareCorrectiveRun(self):
        (self.feature / "spec.md").write_text("A feature\n- FR-001: preserve data\n- FR-002: bounded work\n")
        self.assertContinues(self.control("bind-invariants", spec_file="specs/demo/spec.md"))
        self.record()
        self.assertContinues(self.dispatch("delta"))
        reservations = {}
        for dispatch, invariant, outcome in (("owner", "FR-001", "failed"), ("other", "FR-002", "completed")):
            reply = self.control("reserve", dispatch_id=dispatch, kind="corrective", failure_invariant=invariant)
            self.assertContinues(reply)
            reservations[dispatch] = reply["data"]["reservation_id"]
            self.control("reconcile", dispatch_id=dispatch)
            self.assertContinues(self.control("complete", dispatch_id=dispatch, outcome=outcome, native_observation={
                "native_event_id": f"native-{dispatch}", "run_id": self.run_id, "dispatch_id": dispatch,
                "action": "dispatch_result", "outcome": outcome}))
        digest = self.ledger()["invariant_binding"]["spec_sha256"]
        return {
            "authorize-corrective-retry": {"dispatch_id": "retry", "failed_dispatch_id": "owner",
                "reservation_id": reservations["owner"], "agent_authorized": True, "failure_kind": "infrastructure"},
            "authorize-corrective-continuation": {"dispatch_id": "continuation", "completed_dispatch_id": "other",
                "reservation_id": reservations["other"], "native_observation": {"native_event_id": "approve-continuation",
                    "run_id": self.run_id, "action": "corrective_continuation_approved", "completed_dispatch_id": "other",
                    "continuation_dispatch_id": "continuation", "reservation_id": reservations["other"],
                    "purpose": "task_metadata_reconciliation"}},
            "authorize-corrective-exception": {"dispatch_id": "exception", "failure_invariant": "FR-001",
                "scope_sha256": "a" * 64, "native_observation": {"native_event_id": "approve-exception",
                    "run_id": self.run_id, "action": "corrective_exception_approved", "failure_invariant": "FR-001",
                    "dispatch_id": "exception", "failure_kind": "application", "refusal_reason": "failure_family_budget_exhausted",
                    "scope_sha256": "a" * 64, "spec_sha256": digest}},
        }

    def assertFollowUpsWait(self, requests):
        self.write_tasks(TASKS.replace("Build part 1", "Build part 1 twice"))
        for action, inputs in requests.items():
            for claim in ({}, {"kind": "verification"}, {"tdd_units": ["delta"]}):
                with self.subTest(action=action, claim=claim):
                    self.assertBlocked(self.control(action, mode="dry_run", **inputs, **claim))
                    self.assertNotIn(inputs["dispatch_id"], self.ledger()["dispatches"])
        for action, inputs in requests.items():
            self.assertBlocked(self.control(action, **inputs))
        self.assertContinues(self.dispatch("delta"))


class CorrectiveDriftTest(CorrectiveDriftFixture):
    def test_eligible_corrective_approvals_detect_drift_before_they_dispatch(self):
        requests = self.prepareCorrectiveRun()
        for action, inputs in requests.items():
            self.assertContinues(self.control(action, mode="dry_run", **inputs))
        self.assertFollowUpsWait(requests)

    def test_eligible_class_follow_up_detects_drift_before_it_dispatches(self):
        requests = self.prepareCorrectiveRun()
        failure_class = {"test_file": "tests/cli.test.ts", "failure_signature": "Test timed out in 5000ms",
                         "change_kind": "test_timeout"}
        exception = requests["authorize-corrective-exception"]
        exception["failure_class"] = failure_class
        exception["native_observation"]["failure_class"] = failure_class
        self.assertContinues(self.control("authorize-corrective-exception", **exception))
        self.assertContinues(self.control("complete", dispatch_id="exception", outcome="completed"))
        request = {"dispatch_id": "class-follow-up", "failure_class": failure_class}
        self.assertContinues(self.control("reserve-class-correction", mode="dry_run", **request))
        self.assertFollowUpsWait({"reserve-class-correction": request})

    def test_an_escalation_naming_a_remediation_unit_waits_after_drift(self):
        self.prepareCorrectiveRun()
        self.assertEqual(self.control("reserve", dispatch_id="again", kind="corrective",
                                      failure_invariant="FR-001")["data"]["disposition"], "defer")
        escalation = {"escalation": {"unit_kind": "failure_family", "unit": "FR-001", "tier": 2}}
        self.assertContinues(self.control("reserve", mode="dry_run", dispatch_id="plain", kind="corrective", **escalation))
        self.write_tasks(TASKS.replace("Build part 1", "Build part 1 twice"))
        decoys = {"plain": {}, **{field: {"spec_file": "specs/demo/spec.md",
                                          field: {"tdd_unit": "delta", "paths": ["src/delta"]}}
                                  for field in ("review_remediation", "test_fix")}}
        for name, decoy in decoys.items():
            with self.subTest(decoy=name):
                request = {"dispatch_id": f"escalate-{name}", "kind": "corrective", **escalation, **decoy}
                self.assertBlocked(self.control("reserve", mode="dry_run", **request))
                self.assertBlocked(self.control("reserve", **request))
                self.assertNotIn(request["dispatch_id"], self.ledger()["dispatches"])


class DriftBlockPersistenceTest(DriftFixture):
    def test_a_block_survives_a_revert_a_new_approval_and_resume(self):
        self.assertContinues(self.dispatch("delta"))
        self.write_tasks(TASKS.replace("Build part 1", "Build part 1 twice"))
        self.assertContinues(self.dispatch("delta"))
        recorded = self.ledger()["blocked_work"]
        self.record()
        self.assertBlocked(self.dispatch("alpha"))
        self.write_tasks(TASKS)
        self.assertBlocked(self.dispatch("alpha"))
        self.control("start")
        self.assertBlocked(self.dispatch("beta"))
        self.assertContinues(self.dispatch("delta"))
        self.assertEqual(self.ledger()["blocked_work"], recorded)

    def test_planning_dispatches_need_no_approval(self):
        for path in self.feature.glob("plan-approvals/*.json"):
            path.unlink()
        self.assertContinues(self.control("reserve", dispatch_id="planner", kind="implementation"))
        self.assertNotIn("planning_binding", self.ledger())


class DriftGuidanceTest(unittest.TestCase):
    def test_both_hosts_skip_blocked_units_and_keep_independent_work_going(self):
        assert_guides_document(self, GuidePhrases(("`planning_binding`", "`planning_drift`", "`blocked_for_uat`")),
                               GuidePhrases(("Planning drift during implement", "`blocked_for_uat`: skip that batch",
                                             "Ready for UAT with blocked work", "opens no changed task")))


if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                               for case in (PinnedRevisionTest, DriftBlockTest, WholePlanChangeTest, UnscopedWorkDriftTest,
                                            FeatureOwnerDriftTest,
                                            OwnedPlanningInputTest, AliasOwnedPlanningInputTest, CorrectiveDriftTest,
                                            DriftBlockPersistenceTest,
                                            DriftGuidanceTest))
    raise SystemExit(run_counted(suite, label="test-implement-planning-drift"))
