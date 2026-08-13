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

# Repository-relative references inside the authority fixture's own temporary root.
SUPPLIED_WORKFLOW_REF = "docs/supplied-workflow.md"
OTHER_WORKFLOW_REF = "docs/a-different-workflow.md"


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


class WorkflowAuthorityTests(unittest.TestCase):
    """`autopilot-state.json.workflow_file` is the authority on which workflow a run may touch.

    The FR-012 controlled pair shares one fixture builder whose only parameter is
    the state's ``workflow_file`` value, so each failure names its own claim
    rather than the fixture.
    """

    #: FR-009 fixes the opening sentence. Assert the prefix and never the full
    #: string, so the appended paths can be reformatted without breaking this.
    AUTHORITY_PREFIX = (
        "supplied workflow does not match autopilot state workflow_file authority"
    )

    @staticmethod
    def _plant(root: Path, state_workflow_ref: str) -> tuple[Path, Path]:
        """Lay out a repository-shaped fixture and return (supplied workflow, state)."""
        # A *file* marker, not a directory. ``_repository_root`` is satisfied by
        # either, and a file is what a git worktree carries -- which is what every
        # real autopilot run for this repository uses. Without a marker the
        # comparison skips under FR-006 and every control here passes vacuously.
        (root / ".git").write_text("gitdir: ../elsewhere/.git/worktrees/fixture\n", encoding="utf-8")
        supplied = root / SUPPLIED_WORKFLOW_REF
        supplied.parent.mkdir(parents=True, exist_ok=True)
        # Passes status-evidence; fails coverage, which this rule does not gate on.
        supplied.write_text(
            workflow(("Specify", "✅ Complete"), body="G1 gate: PASS"), encoding="utf-8"
        )
        state = supplied.parent / "autopilot-state.json"
        state.write_text(
            json.dumps({
                # Repository-relative against this root. An absolute value is
                # rejected as malformed before the comparison is ever reached.
                "workflow_file": state_workflow_ref,
                "plan": [{"step": s, "status": "pending"} for s in PLAN_STEPS],
            }),
            encoding="utf-8",
        )
        return supplied, state

    def _run(self, state_workflow_ref: str) -> tuple[int, dict]:
        """Invoke the guard exactly as the autopilot does, varying one value.

        The autopilot's own invocation is `--rule status-evidence` with no commit
        flags and a state carrying no `pr_marker_plan`.
        """
        with tempfile.TemporaryDirectory() as raw:
            supplied, state = self._plant(Path(raw), state_workflow_ref)
            completed = subprocess.run(
                [sys.executable, str(VALIDATOR),
                 "--workflow", str(supplied), "--state", str(state),
                 "--rule", "status-evidence"],
                text=True, capture_output=True, check=False,
            )
            return completed.returncode, json.loads(completed.stdout)

    def test_state_naming_a_different_workflow_halts_the_run(self) -> None:
        """FR-012's negative control: the run this specification exists to stop."""
        code, report = self._run(OTHER_WORKFLOW_REF)
        self.assertEqual(code, 1, report)
        self.assertIn("workflow_authority_errors", report)
        errors = report["workflow_authority_errors"]
        self.assertTrue(errors, report)
        self.assertTrue(errors[0].startswith(self.AUTHORITY_PREFIX), errors[0])

    def test_state_naming_the_supplied_workflow_allows_the_run(self) -> None:
        """FR-012's positive control: the same fixture, one value different.

        It differs from the negative control in exactly one value, the state's
        ``workflow_file``, and it is a separate method rather than a parameter so
        each failure names its own claim. This is what proves the negative
        control detects a mismatch rather than failing everything.
        """
        code, report = self._run(SUPPLIED_WORKFLOW_REF)
        self.assertEqual(code, 0, report)
        self.assertIn("workflow_authority_errors", report)
        self.assertEqual(report["workflow_authority_errors"], [])

    def test_state_named_relatively_from_a_subdirectory_is_still_compared(self) -> None:
        """FR-006b: evaluating depends on where the state *is*, not how it is spelled.

        This state sits inside the repository fixture exactly as the controlled
        pair's does, and names a mismatching workflow exactly as the negative
        control's does. Only the spelling differs: it is named by a relative path
        from a subdirectory. Root resolution walked the parents of the path *as
        supplied*, whose chain terminated at the working directory, so no marker
        was found and the comparison skipped while the state file sat untouched
        inside the tree.

        This control is what separates FR-006b's repair from a no-op. The FR-006
        verdict for a state genuinely outside any repository is deliberately
        unchanged: there is still no marker to find, so it still skips.
        """
        with tempfile.TemporaryDirectory() as raw:
            supplied, state = self._plant(Path(raw), OTHER_WORKFLOW_REF)
            completed = subprocess.run(
                [sys.executable, str(VALIDATOR),
                 "--workflow", str(supplied), "--state", state.name,
                 "--rule", "status-evidence"],
                cwd=str(state.parent),
                text=True, capture_output=True, check=False,
            )
            report = json.loads(completed.stdout)
        self.assertIn("workflow_authority_errors", report)
        self.assertTrue(report["workflow_authority_errors"], report)

    def test_state_without_a_workflow_file_key_skips_the_comparison(self) -> None:
        """FR-003: a state that names no workflow asserts no authority.

        Deliberately outside the FR-012 pair, so that pair keeps differing in
        exactly one value. This is the one branch neither control reaches: both
        set ``workflow_file``, and ``RuleScopingTests`` sets it too while
        reaching the unresolvable-root skip rather than this one. The fixture
        root carries its repository marker, so the skip is attributable to the
        absent field rather than to a root that could not be resolved. It is the
        branch that keeps the tracked state slot carrying no ``workflow_file``
        validating, and the one the corpus evidence structurally cannot cover,
        because every synthesized corpus state sets the field.
        """
        with tempfile.TemporaryDirectory() as raw:
            supplied, state = self._plant(Path(raw), SUPPLIED_WORKFLOW_REF)
            # Remove the key itself, never null it: an explicitly nulled field is
            # malformed, and only key membership distinguishes the two.
            planted = json.loads(state.read_text(encoding="utf-8"))
            del planted["workflow_file"]
            state.write_text(json.dumps(planted), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(VALIDATOR),
                 "--workflow", str(supplied), "--state", str(state),
                 "--rule", "status-evidence"],
                text=True, capture_output=True, check=False,
            )
            report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, report)
        self.assertIn("workflow_authority_errors", report)
        self.assertEqual(report["workflow_authority_errors"], [])

    def test_malformed_workflow_file_fails_as_malformed_not_as_a_mismatch(self) -> None:
        """FR-005: a garbage value cannot become a silent opt-out.

        Branch 3 of FR-004d's ordering, which no other test reaches. The two
        assertions that matter are the exit code and the *attribution*: the
        whitespace-only case must be caught by the explicit malformed check
        rather than falling through to the identity branch, because
        ``_is_normalized_repo_path`` accepts a run of spaces as a valid path
        part. If it fell through, the operator would see the identity message
        with a blank path in it and the verdict would be right by accident.
        """
        for label, value in (
            ("whitespace only", "   "),
            ("empty string", ""),
            ("absolute path", "/etc/workflow.md"),
            ("parent traversal", "../outside-workflow.md"),
            ("explicit null", None),
            ("non-string", 42),
        ):
            with self.subTest(malformed=label):
                code, report = self._run(value)
                self.assertEqual(code, 1, report)
                errors = report["workflow_authority_errors"]
                self.assertTrue(errors, report)
                self.assertFalse(
                    errors[0].startswith(self.AUTHORITY_PREFIX),
                    f"{label} was reported as an identity mismatch rather than as "
                    f"malformed: {errors[0]}",
                )

    def test_supplied_workflow_outside_the_repository_fails(self) -> None:
        """FR-004c: a completed evaluation with an out-of-boundary result fails.

        Branch 4 of FR-004d's ordering, which no other test reaches. This is the
        branch a unanimous three-lens consensus settled as a failure rather than
        a skip, on the grounds that a path escaping the root is an affirmative
        anomaly and not the absence of information FR-006 covers. It reuses the
        sentence the guard already emitted for this condition, so the assertion
        deliberately checks that the identity prefix is *not* used.
        """
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "repo"
            root.mkdir()
            _, state = self._plant(root, SUPPLIED_WORKFLOW_REF)
            # A workflow that exists but resolves outside the resolved root.
            outside = Path(raw) / "outside-workflow.md"
            outside.write_text(
                workflow(("Specify", "✅ Complete"), body="G1 gate: PASS"), encoding="utf-8"
            )
            completed = subprocess.run(
                [sys.executable, str(VALIDATOR),
                 "--workflow", str(outside), "--state", str(state),
                 "--rule", "status-evidence"],
                text=True, capture_output=True, check=False,
            )
            report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1, report)
        errors = report["workflow_authority_errors"]
        self.assertTrue(errors, report)
        self.assertIn("outside the authorized repository", errors[0])
        self.assertFalse(errors[0].startswith(self.AUTHORITY_PREFIX), errors[0])


class ProblemKeyClassificationTests(unittest.TestCase):
    """FR-011: every problem key the guard emits carries a recorded verdict.

    The emitted set is derived from a real report and never from a second
    hardcoded list, because a parallel list drifts out of step exactly as the
    classification record itself could -- which is the failure mode being closed.
    """

    #: FR-010 fixes a closed three-value vocabulary. Spelled out here rather than
    #: read back from the guard: deriving it from the module under test would let
    #: a fourth verdict added there pass unnoticed, and "closed" is precisely the
    #: property this test exists to hold.
    VERDICTS = frozenset({"gated", "advisory-deliberate", "advisory-accidental"})

    #: Report fields that describe the run rather than name a finding.
    METADATA_KEYS = frozenset({"status", "workflow_file", "state_file", "plan_step_count"})

    @classmethod
    def setUpClass(cls) -> None:
        cls.emitted = cls._emitted_problem_keys()

    @classmethod
    def _emitted_problem_keys(cls) -> set[str]:
        """Every problem key of a real report, minus the metadata fields.

        One report is the complete set rather than a sample because every
        per-check function returns its full key set on every return path,
        including its early returns, so no key is ever conditionally absent.
        That is a property of the guard this test relies on rather than one it
        checks. The limit follows directly: a future key emitted only under some
        state shapes would be absent from this fixture's report and would pass
        unclassified. The response then is to extend this fixture to a state
        shape that emits it, never to relax the assertion.

        The fixture carries a repository marker so the checks that resolve a
        root evaluate for real instead of taking their unresolvable-root skip.
        """
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".git").write_text(
                "gitdir: ../elsewhere/.git/worktrees/fixture\n", encoding="utf-8"
            )
            supplied = root / SUPPLIED_WORKFLOW_REF
            supplied.parent.mkdir(parents=True, exist_ok=True)
            supplied.write_text(
                workflow(("Specify", "✅ Complete"), body="G1 gate: PASS"), encoding="utf-8"
            )
            state = supplied.parent / "autopilot-state.json"
            state.write_text(
                json.dumps({
                    "workflow_file": SUPPLIED_WORKFLOW_REF,
                    "plan": [{"step": s, "status": "pending"} for s in PLAN_STEPS],
                }),
                encoding="utf-8",
            )
            # The autopilot's own invocation. The full report prints under every
            # rule, so scoping changes the exit code and never the key set.
            completed = subprocess.run(
                [sys.executable, str(VALIDATOR),
                 "--workflow", str(supplied), "--state", str(state),
                 "--rule", "status-evidence"],
                text=True, capture_output=True, check=False,
            )
        report = json.loads(completed.stdout)
        return set(report) - cls.METADATA_KEYS

    def test_every_emitted_problem_key_carries_a_verdict(self) -> None:
        """SC-005: adding a problem key without recording a verdict fails here."""
        missing = sorted(self.emitted - set(validator.PROBLEM_KEY_INTENT))
        self.assertFalse(
            missing,
            "the guard emits problem keys with no PROBLEM_KEY_INTENT verdict: "
            + ", ".join(missing),
        )

    def test_the_record_classifies_nothing_the_guard_never_emits(self) -> None:
        """The other direction, which the completeness check alone does not cover.

        A verdict recorded for a key the report never emits is dead weight that
        reads as coverage. Checking only ``emitted - intent`` would let the record
        accumulate entries for keys that were renamed or removed, and the record
        would still look complete. Both directions together are what make the
        record an accurate census rather than a superset.
        """
        extraneous = sorted(set(validator.PROBLEM_KEY_INTENT) - self.emitted)
        self.assertFalse(
            extraneous,
            "PROBLEM_KEY_INTENT classifies keys the guard never emits: "
            + ", ".join(extraneous),
        )

    def test_every_verdict_is_drawn_from_the_closed_vocabulary(self) -> None:
        """FR-010: three values, and a fourth is not a value."""
        outside = sorted(
            f"{key}={entry['verdict']!r}"
            for key, entry in validator.PROBLEM_KEY_INTENT.items()
            if entry["verdict"] not in self.VERDICTS
        )
        self.assertFalse(
            outside,
            "verdicts outside the closed vocabulary " + repr(sorted(self.VERDICTS)) + ": "
            + ", ".join(outside),
        )

    def test_every_entry_carries_a_reason(self) -> None:
        """FR-010a: a verdict without a stated reason records nothing."""
        reasonless = sorted(
            key
            for key, entry in validator.PROBLEM_KEY_INTENT.items()
            if not isinstance(entry["reason"], str) or not entry["reason"].strip()
        )
        self.assertFalse(
            reasonless,
            "classification entries carrying no reason: " + ", ".join(reasonless),
        )


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for case in (
        WorkflowStatusEvidenceTests,
        StateStatusSchemaTests,
        RuleScopingTests,
        WorkflowAuthorityTests,
        ProblemKeyClassificationTests,
    ):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-autopilot-bookkeeping-guard")


if __name__ == "__main__":
    raise SystemExit(main())
