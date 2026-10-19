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
                   "tasks": {task: {"capability_group": "stories", "depends_on": deps, "owns": OWNS.get(task, [f"src/{UNITS[task]}"]),
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


class PinnedRevisionTest(DriftFixture):
    def test_the_first_task_dispatch_pins_the_approved_revision(self):
        self.assertContinues(self.dispatch("alpha"))
        pinned = self.ledger()["planning_binding"]
        self.assertEqual(pinned["manifest_digest"], self.approved["manifest_digest"])
        self.assertEqual(sorted(pinned["tasks"]), sorted(DEPENDS))

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

    def assertBlocksAllRemainingWork(self, change):
        self.assertContinues(self.dispatch("alpha"))
        self.control("complete", dispatch_id="alpha-0", outcome="completed")
        change()
        self.assertBlocked(self.dispatch("delta"))
        self.assertEqual(sorted(self.entries()), ["task:T002", "task:T003", "task:T004"])
        (cause,) = self.ledger()["blocked_work"]["causes"].values()
        self.assertIsNone(cause["drifted_tasks"])

    def test_a_changed_spec_blocks_all_remaining_work(self):
        self.assertBlocksAllRemainingWork(lambda: (self.feature / "spec.md").write_text("A different feature"))

    def test_an_added_task_blocks_all_remaining_work_and_is_never_dispatched(self):
        self.assertBlocksAllRemainingWork(lambda: self.write_tasks(TASKS + "- [ ] T005 Build part 5\n"))
        self.assertRefused(self.dispatch("epsilon"), "tdd_units names a TDD unit the approved plan does not define")

    def test_a_changed_heading_blocks_all_remaining_work(self):
        self.assertBlocksAllRemainingWork(lambda: self.write_tasks(TASKS.replace("Phase 3", "Phase 4")))

    def test_a_blank_line_between_tasks_is_a_layout_change(self):
        self.assertBlocksAllRemainingWork(lambda: self.write_tasks(TASKS.replace("- [ ] T003", "\n- [ ] T003")))

    def test_missing_task_metadata_blocks_all_remaining_work(self):
        self.assertBlocksAllRemainingWork(lambda: (self.feature / ".process/task-execution.json").unlink())

    def test_a_task_writing_a_planning_file_it_owns_is_not_drift(self):
        self.assertContinues(self.dispatch("delta"))
        (self.feature / "quickstart.md").write_text("Run part 4\n")
        self.assertContinues(self.dispatch("alpha"))
        self.assertNotIn("blocked_work", self.ledger())

    def test_unscoped_work_waits_after_drift(self):
        self.assertContinues(self.dispatch("delta"))
        self.write_tasks(TASKS.replace("Build part 1", "Build part 1 twice"))
        self.assertContinues(self.dispatch("delta"))
        for action, inputs in (("reserve", {"kind": "implementation"}),
                               ("reserve", {"kind": "corrective", "failure_invariant": "FR-001"}),
                               ("reserve-retry-rung", {"host": "claude", "command_sha256": "a" * 64})):
            with self.subTest(action=action, kind=inputs.get("kind")):
                self.assertBlocked(self.control(action, dispatch_id=f"unscoped-{action}", **inputs))
        self.assertContinues(self.control("reserve", dispatch_id="verify", kind="verification"))


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
                               for case in (PinnedRevisionTest, DriftBlockTest, DriftBlockPersistenceTest,
                                            DriftGuidanceTest))
    raise SystemExit(run_counted(suite, label="test-implement-planning-drift"))
