#!/usr/bin/env python3
"""Planning-choice binding through source and both packaged approval seams."""
import runpy
import unittest
from pathlib import Path

fixture = runpy.run_path(str(Path(__file__).with_name("test-planning-approval.py")))
WorkflowFixture = fixture["WorkflowFixture"]
run_counted = fixture["run_counted"]
SOURCE = Path(__file__).resolve().parents[3]
RUNNERS = (SOURCE / "speckit-pro", *(SOURCE / "dist" / host / "speckit-pro" for host in ("claude", "codex")))
# Checkbox lines that resemble a generated-path tick but remain planning choices.
LOOKALIKES = ("  - [x] Require signed release approval", "- [x] `Require signed release approval`",
              "- [x] `src/demo.py` Require signed release approval",
              "- [x] [Require signed release approval](src/demo.py)", "```text\n- [x] `src/demo.py`\n```")
# Status ticks, by the headings they sit under, that never change a planning choice.
PRESERVED_TICKS = {
    "success criteria": (("## Success Criteria\n", "## Specification Context\n### Success Criteria Summary\n"),
                         "  - [x] Contract correct"),
    "generated path": (("## Files Generated\n", "## Phase 7: Implement\n### Files Generated\n"),
                       "  - [x] `src/demo.py`"),
}


class CheckboxAssertions(WorkflowFixture):
    def assertHostsEdit(self, headings, bodies, *, preserves=False):
        for runner in RUNNERS:
            self.runner_root = runner
            for heading in headings:
                for body in bodies:
                    for checked in ("x", "X"):
                        with self.subTest(runner=runner.relative_to(SOURCE).as_posix(), heading=heading,
                                          body=body, checked=checked):
                            before = heading + body.replace("[x]", f"[{checked}]") + "\n"
                            after = before.replace(f"[{checked}]", "[ ]")
                            self.assertWorkflowEdit(before, after, preserves=preserves)

    def assertTicksPreserve(self, kind):
        headings, body = PRESERVED_TICKS[kind]
        self.assertHostsEdit(headings, (body,), preserves=True)


class PlanningCheckboxTest(CheckboxAssertions):
    def test_implementation_progress_choices_invalidate_record(self):
        self.assertHostsEdit(("## Implementation Progress\n", "## Phase 7: Implement\n### Implementation Progress\n"),
                             ("- [x] Require signed release approval",))

    def test_files_generated_choices_invalidate_record(self):
        self.assertHostsEdit(("## Files Generated\n", "## Phase 7: Implement\n### Files Generated\n"),
                             ("- [x] Require signed release approval",))

    def test_success_criteria_ticks_preserve_record(self):
        self.assertTicksPreserve("success criteria")

    def test_preimplementation_choices_invalidate_record(self):
        self.assertHostsEdit(("## Pre-Implementation Setup\n",), ("- [x] Require signed release approval",))

    def test_files_generated_path_ticks_preserve_record(self):
        self.assertTicksPreserve("generated path")

    def test_checkbox_lookalikes_keep_choices_bound(self):
        self.assertHostsEdit(("## Files Generated\n", "## Phase 7: Implement\n### Implementation Progress\n"),
                             LOOKALIKES)

    def test_generated_path_rename_and_link_edits_invalidate_record(self):
        for runner in RUNNERS:
            self.runner_root = runner
            before = "## Files Generated\n- [x] `src/demo.py`\n"
            for after in (before.replace("demo.py", "other.py"),
                          before.replace("`src/demo.py`", "[demo](src/demo.py)")):
                with self.subTest(runner=runner.relative_to(SOURCE).as_posix(), after=after):
                    self.assertWorkflowEdit(before, after)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PlanningCheckboxTest)
    raise SystemExit(run_counted(suite, label="test-planning-approval-checkboxes"))
