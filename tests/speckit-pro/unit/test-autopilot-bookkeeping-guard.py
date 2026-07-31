#!/usr/bin/env python3
"""Behavioural coverage for the autopilot bookkeeping guard.

Covers the three surfaces that enforce the bookkeeping rule at run time: the
``workflow_status_evidence_errors`` and ``validate_state_status`` checks inside
the shipped phase-coverage validator, its ``--rule`` exit-code scoping, and the
Stop hook that consumes them.

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
from unittest import mock

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
LIB_DIR = TEST_DIR.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402

SKILL_SCRIPTS = REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "scripts"
VALIDATOR = SKILL_SCRIPTS / "validate-autopilot-phase-coverage.py"
STOP_HOOK = SKILL_SCRIPTS / "autopilot-bookkeeping-stop-hook.py"

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
hook = _load(STOP_HOOK, "speckit_autopilot_bookkeeping_stop_hook_under_test")


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


class StopHookTests(unittest.TestCase):
    """The hook blocks exactly once, on real drift, and fails open otherwise."""

    def _project(self, root: Path, *, state: dict | None, drifted: bool) -> None:
        process = root / "docs" / "ai" / "specs" / ".process"
        process.mkdir(parents=True, exist_ok=True)
        status = "⏳ Pending" if drifted else "✅ Complete"
        (process / "T-workflow.md").write_text(
            workflow(("Tasks", status), body="**G5 gate:** ✅ PASS"), encoding="utf-8"
        )
        if state is not None:
            (process / "autopilot-state.json").write_text(json.dumps(state), encoding="utf-8")

    def _run(self, root: Path, payload: dict) -> tuple[int, str]:
        completed = subprocess.run(
            [sys.executable, str(STOP_HOOK)],
            input=json.dumps(payload), text=True, capture_output=True, check=False,
        )
        return completed.returncode, completed.stdout

    def _blocks(self, root: Path, payload: dict) -> bool:
        payload = {"cwd": str(root), **payload}
        code, out = self._run(root, payload)
        self.assertEqual(code, 0, "the hook must never exit nonzero; python3 itself uses exit 2")
        return '"decision": "block"' in out

    def test_blocks_on_real_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._project(root, state={"workflow_file": "docs/ai/specs/.process/T-workflow.md"}, drifted=True)
            self.assertTrue(self._blocks(root, {"session_id": "s1"}))

    def test_absent_top_level_status_still_blocks(self) -> None:
        """No shipped contract declares a top-level status; absence must not disable the hook."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._project(root, state={"workflow_file": "docs/ai/specs/.process/T-workflow.md"}, drifted=True)
            self.assertTrue(self._blocks(root, {"session_id": "s2"}))

    def test_finished_run_does_not_block(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._project(root, state={
                "status": "completed_archived",
                "workflow_file": "docs/ai/specs/.process/T-workflow.md",
            }, drifted=True)
            self.assertFalse(self._blocks(root, {"session_id": "s3"}))

    def test_clean_workflow_does_not_block(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._project(root, state={"workflow_file": "docs/ai/specs/.process/T-workflow.md"}, drifted=False)
            self.assertFalse(self._blocks(root, {"session_id": "s4"}))

    def test_missing_state_file_does_not_block(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._project(root, state=None, drifted=True)
            self.assertFalse(self._blocks(root, {"session_id": "s5"}))

    def test_path_traversal_is_contained(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._project(root, state={"workflow_file": "../../../etc/passwd"}, drifted=True)
            self.assertFalse(self._blocks(root, {"session_id": "s6"}))

    def test_unparseable_payload_does_not_block(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(STOP_HOOK)], input="not json",
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertNotIn('"decision": "block"', completed.stdout)

    def test_state_declaring_a_workflow_wins_over_one_that_does_not(self) -> None:
        """A legacy state file without workflow_file must not shadow the real one."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._project(root, state={"workflow_file": "docs/ai/specs/.process/T-workflow.md"}, drifted=True)
            specify = root / ".specify"
            specify.mkdir(parents=True, exist_ok=True)
            (specify / "autopilot-state.json").write_text(json.dumps({"status": "in_progress"}), encoding="utf-8")
            self.assertTrue(self._blocks(root, {"session_id": "s7"}))

    def test_stop_hook_active_suppresses_a_repeat_block(self) -> None:
        self.assertTrue(hook._already_blocked({"stop_hook_active": True}, Path("/tmp/w.md")))

    def test_second_stop_in_one_session_is_suppressed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            marker_home = Path(raw)
            with mock.patch.object(hook.tempfile, "gettempdir", return_value=str(marker_home)):
                first = hook._already_blocked({"session_id": "dup"}, Path("/tmp/w.md"))
                second = hook._already_blocked({"session_id": "dup"}, Path("/tmp/w.md"))
        self.assertFalse(first)
        self.assertTrue(second)

    def test_unwritable_marker_suppresses_the_block(self) -> None:
        """Without a recordable bound, blocking would repeat forever."""
        with mock.patch.object(Path, "touch", side_effect=OSError("read-only")):
            results = [hook._already_blocked({"session_id": "ro"}, Path("/tmp/w.md")) for _ in range(4)]
        self.assertEqual(results, [True, True, True, True])

    def test_missing_session_id_suppresses_the_block(self) -> None:
        self.assertTrue(hook._already_blocked({}, Path("/tmp/w.md")))


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for case in (WorkflowStatusEvidenceTests, StateStatusSchemaTests, RuleScopingTests, StopHookTests):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-autopilot-bookkeeping-guard")


if __name__ == "__main__":
    raise SystemExit(main())
