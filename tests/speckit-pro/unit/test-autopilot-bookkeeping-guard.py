#!/usr/bin/env python3
"""Behavioural coverage for the autopilot bookkeeping guard.

Covers the surfaces that enforce the bookkeeping rule at run time: the
``workflow_status_evidence_errors`` and ``validate_state_status`` checks inside
the shipped phase-coverage validator, and its ``--rule`` exit-code scoping.

The rule's own CI gate asserts that the live corpus is clean, which cannot show
that the gate would *catch* a violation. These tests supply the negative
fixtures: each one constructs a workflow that is wrong in exactly one way and
asserts the specific error.

Python 3.11+ standard library only.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
LIB_DIR = TEST_DIR.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402

SKILL_SCRIPTS = REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "scripts"
VALIDATOR = SKILL_SCRIPTS / "validate-autopilot-phase-coverage.py"

PLAN_STEPS = (
    "Archive Sweep: previously merged specs dry-run/apply eligibility",
    "Phase 0: Prerequisites",
    "Phase 1: Specify",
    "Phase 2: Clarify",
    "Phase 3: Plan",
    "Phase 4: Domain Checklists",
    "Phase 5: Tasks",
    "Phase 6: Analyze",
    "Phase 6.5: Pre-Implement Confidence",
    "Phase 7: Implement",
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


validator = _load(VALIDATOR, "speckit_autopilot_phase_coverage_under_test")


def workflow(*rows: tuple[str, str], body: str = "") -> str:
    """A minimal workflow document with the given (phase, status) overview rows."""
    lines = ["# Workflow", "", "## Workflow Overview", "", "| Phase | Command | Status | Notes |", "|---|---|---|---|"]
    lines.extend(f"| {phase} | `/speckit-x` | {status} | |" for phase, status in rows)
    lines.extend(["", body])
    return "\n".join(lines)


class WorkflowStatusEvidenceTests(unittest.TestCase):
    """Negative fixtures for the rule this PR introduces."""

    def test_recorded_gate_pass_requires_a_terminal_row(self) -> None:
        text = workflow(("Tasks", "⏳ Pending"), body="**G5 gate:** ✅ PASS — 63 tasks found")
        errors = validator.workflow_status_evidence_errors(text)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("'Tasks'", errors[0])
        self.assertIn("G5 PASS", errors[0])

    def test_terminal_row_after_open_row_is_an_ordering_error(self) -> None:
        text = workflow(("Tasks", "⏳ Pending"), ("Implement", "✅ Complete"))
        errors = validator.workflow_status_evidence_errors(text)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("while earlier", errors[0])

    def test_clean_workflow_reports_nothing(self) -> None:
        text = workflow(("Tasks", "✅ Complete"), ("Implement", "✅ Complete"),
                        body="**G5 gate:** ✅ PASS")
        self.assertEqual(validator.workflow_status_evidence_errors(text), [])

    def test_unknown_status_is_reported(self) -> None:
        text = workflow(("Tasks", "mostly done"))
        errors = validator.workflow_status_evidence_errors(text)
        self.assertTrue(any("unsupported status" in e for e in errors), errors)

    def test_gate_criteria_table_is_not_evidence(self) -> None:
        """A '### Phase Gates' approval-criteria row must not count as a verdict."""
        text = workflow(
            ("Tasks", "⏳ Pending"),
            body="### Phase Gates\n\n| Gate | Checkpoint | Criteria |\n|---|---|---|\n"
                 "| G5 | After Tasks | Tests pass, coverage verified |",
        )
        self.assertEqual(validator.workflow_status_evidence_errors(text), [])

    def test_commented_out_evidence_is_not_evidence(self) -> None:
        text = workflow(("Tasks", "⏳ Pending"), body="<!-- **G5 gate:** ✅ PASS -->")
        self.assertEqual(validator.workflow_status_evidence_errors(text), [])

    def test_advisory_confidence_gate_does_not_bar_later_rows(self) -> None:
        """An advisory row the phase loop never drives must not cascade."""
        text = workflow(("Confidence Gate", "⏳ Pending"), ("Implement", "✅ Complete"))
        self.assertEqual(validator.workflow_status_evidence_errors(text), [])

    def test_missing_overview_table_is_reported(self) -> None:
        errors = validator.workflow_status_evidence_errors("# Workflow\n\nNo table here.\n")
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("no parseable", errors[0])


class StateStatusSchemaTests(unittest.TestCase):
    def test_retired_spelling_is_rejected(self) -> None:
        errors = validator.validate_state_status({"status": "complete_pr_open"})["state_status_errors"]
        self.assertTrue(any("enum" in e for e in errors), errors)

    def test_current_spellings_are_accepted(self) -> None:
        for status in ("in_progress", "completed", "completed_pr_open", "completed_archived"):
            with self.subTest(status=status):
                self.assertEqual(
                    validator.validate_state_status({"status": status})["state_status_errors"], []
                )

    def test_absent_status_is_accepted(self) -> None:
        """The canonical state shape carries no top-level status; absence is legal."""
        self.assertEqual(validator.validate_state_status({})["state_status_errors"], [])


class RuleScopingTests(unittest.TestCase):
    """`--rule` must scope the exit code without hiding anything from the report."""

    def _run(self, extra: list[str]) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            wf = root / "workflow.md"
            # Fails coverage (no Post items / sections) but passes status-evidence.
            wf.write_text(workflow(("Specify", "✅ Complete"), body="G1 gate: PASS"), encoding="utf-8")
            state = root / "autopilot-state.json"
            state.write_text(
                json.dumps({
                    "workflow_file": str(wf),
                    "plan": [{"step": s, "status": "pending"} for s in PLAN_STEPS],
                }),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(VALIDATOR), "--workflow", str(wf), "--state", str(state), *extra],
                text=True, capture_output=True, check=False,
            )
            return completed.returncode, json.loads(completed.stdout)

    def test_full_gate_fails_on_pre_existing_coverage_debt(self) -> None:
        code, report = self._run([])
        self.assertEqual(code, 1)
        self.assertTrue(report["missing_workflow_post_items"])

    def test_status_evidence_rule_ignores_coverage_debt(self) -> None:
        code, report = self._run(["--rule", "status-evidence"])
        self.assertEqual(code, 0)
        self.assertEqual(report["workflow_status_evidence_errors"], [])

    def test_scoped_run_still_reports_every_list(self) -> None:
        """Scoping the exit code must not hide the debt from the report."""
        _code, report = self._run(["--rule", "status-evidence"])
        self.assertTrue(report["missing_workflow_post_items"])


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for case in (WorkflowStatusEvidenceTests, StateStatusSchemaTests, RuleScopingTests):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-autopilot-bookkeeping-guard")


if __name__ == "__main__":
    raise SystemExit(main())
