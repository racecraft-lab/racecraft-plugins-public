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
from unittest import mock
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
LIB_DIR = TEST_DIR.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402

SKILL_SCRIPTS = REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "scripts"
VALIDATOR = SKILL_SCRIPTS / "validate-autopilot-phase-coverage.py"
CLAUDE_AUTOPILOT_SKILL = REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "SKILL.md"
CODEX_AUTOPILOT_SKILL = REPO_ROOT / "speckit-pro" / "codex-skills" / "speckit-autopilot" / "SKILL.md"
BLOCKING_STATE_INVARIANT_KEYS = (
    "in_progress_errors",
    "duplicate_state_steps",
    "state_order_errors",
)

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


def _clean_state_plan() -> list[dict[str, str]]:
    """A state plan with every validator-required step, once, in canonical order."""
    steps = [
        {"step": step, "status": "completed"}
        for step in validator.STATE_PREFIXES
    ]
    steps.extend(
        {"step": post, "status": "pending"}
        for post in validator.POST_STEPS
    )
    return steps


def _clean_workflow() -> str:
    """A workflow document with the sections and table cells coverage expects."""
    lines = [
        "# Workflow",
        "",
        "## Workflow Overview",
        "",
        "| Phase | Command | Status | Notes |",
        "|---|---|---|---|",
        "| Specify | `/speckit-x` | ⏳ Pending | |",
        "",
        "| Confidence Gate | G6.5 | Status | Notes |",
        "|---|---|---|---|",
        "| G6.5 | Confidence Gate | ⏳ Pending | |",
        "",
    ]
    lines.extend(validator.WORKFLOW_SECTIONS)
    lines.extend([
        "",
        "| Post | Status | Notes |",
        "|---|---|---|",
    ])
    lines.extend(f"| Post | {post} | ⏳ Pending | |" for post in validator.POST_STEPS)
    return "\n".join(lines)


def clean_workflow_state_fixture(
    root: Path,
    *,
    state_workflow_ref: str | None = SUPPLIED_WORKFLOW_REF,
) -> tuple[Path, Path]:
    """Lay out one clean repository-shaped workflow/state pair.

    FR-009 negative controls mutate this pair one problem key at a time. FR-011
    uses it unchanged to prove the same scoped invocation can succeed.
    """
    (root / ".git").write_text("gitdir: ../elsewhere/.git/worktrees/fixture\n", encoding="utf-8")
    supplied = root / SUPPLIED_WORKFLOW_REF
    supplied.parent.mkdir(parents=True, exist_ok=True)
    supplied.write_text(_clean_workflow(), encoding="utf-8")
    state = supplied.parent / "autopilot-state.json"
    state.write_text(
        json.dumps({
            "workflow_file": state_workflow_ref,
            "plan": _clean_state_plan(),
        }),
        encoding="utf-8",
    )
    return supplied, state


def run_status_evidence_report(workflow_path: Path, state_path: Path) -> tuple[int, dict]:
    """Run the exact scoped invocation autopilot issues at phase transitions."""
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR),
         "--workflow", str(workflow_path), "--state", str(state_path),
         "--rule", "status-evidence"],
        text=True, capture_output=True, check=False,
    )
    return completed.returncode, json.loads(completed.stdout)


def status_evidence_guidance_paragraph(path: Path) -> str:
    """Return the source paragraph that explains the scoped bookkeeping guard."""
    paragraphs = [
        paragraph.replace("\n", " ")
        for paragraph in path.read_text(encoding="utf-8").split("\n\n")
    ]
    matches = [
        paragraph
        for paragraph in paragraphs
        if "status-evidence" in paragraph
        and "exit code" in paragraph
        and "full report" in paragraph
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected one status-evidence guidance paragraph in {path}")
    return matches[0]


def tracked_workflow_state_paths(repo_root: Path = REPO_ROOT) -> tuple[str, ...]:
    """Return tracked workflow/state paths from the git index in stable order."""
    try:
        completed = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=repo_root,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("git ls-files -z failed while enumerating tracked paths") from exc
    paths = completed.stdout.decode("utf-8").split("\0")
    return tuple(sorted(
        path for path in paths
        if path.endswith("-workflow.md") or path.endswith("/autopilot-state.json")
    ))


def _adjacent_state_path(workflow_path: str) -> str:
    if "/" not in workflow_path:
        return "autopilot-state.json"
    return workflow_path.rsplit("/", 1)[0] + "/autopilot-state.json"


def classify_authority_matched_pairs(repo_root: Path, tracked_paths: tuple[str, ...]) -> dict:
    """Classify tracked workflows by adjacent state authority."""
    tracked = frozenset(tracked_paths)
    eligible: list[tuple[str, str]] = []
    excluded: list[dict[str, str | None]] = []

    for workflow_path in sorted(path for path in tracked if path.endswith("-workflow.md")):
        state_ref = _adjacent_state_path(workflow_path)
        state_path = repo_root / state_ref
        if state_ref not in tracked:
            reason = "untracked-adjacent-state" if state_path.exists() else "missing-adjacent-state"
            excluded.append({
                "workflow": workflow_path,
                "state": state_ref,
                "reason": reason,
            })
            continue

        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"could not parse tracked state JSON: {state_ref}") from exc
        workflow_file = state.get("workflow_file") if isinstance(state, dict) else None
        if workflow_file == workflow_path:
            eligible.append((workflow_path, state_ref))
        else:
            excluded.append({
                "workflow": workflow_path,
                "state": state_ref,
                "reason": "workflow-file-mismatch",
                "workflow_file": workflow_file,
            })

    return {"eligible": tuple(eligible), "excluded": tuple(excluded)}


class StatusEvidenceReportAssertions:
    """Reusable checks for status-evidence report shape and isolated findings."""

    SELECTED_KEYS = frozenset(validator.RULE_PROBLEM_KEYS["status-evidence"])
    EXPECTED_KEYS = frozenset({
        "status",
        "workflow_file",
        "state_file",
        "plan_step_count",
        *validator.PROBLEM_KEY_INTENT,
    })

    def assertCompleteReport(self, report: dict) -> None:  # noqa: N802
        self.assertEqual(set(report), self.EXPECTED_KEYS)
        for key in validator.PROBLEM_KEY_INTENT:
            with self.subTest(report_key=key):
                self.assertIsInstance(report[key], list)

    def assertSelectedKeysEmpty(self, report: dict) -> None:  # noqa: N802
        for key in self.SELECTED_KEYS:
            with self.subTest(selected_key=key):
                self.assertEqual(report[key], [])

    def assertOnlySelectedProblemKeyPopulated(  # noqa: N802
        self,
        report: dict,
        target_key: str,
    ) -> None:
        self.assertIn(target_key, report)
        self.assertTrue(report[target_key], f"{target_key} should be populated")
        for key in self.SELECTED_KEYS - {target_key}:
            with self.subTest(selected_key=key):
                self.assertEqual(report[key], [])


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


class CleanStatusEvidenceControlTests(StatusEvidenceReportAssertions, unittest.TestCase):
    """FR-007/FR-011: the clean builder succeeds under the exact scoped gate."""

    def test_clean_builder_status_evidence_run_exits_zero_with_complete_report(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            supplied, state = clean_workflow_state_fixture(Path(raw))
            code, report = run_status_evidence_report(supplied, state)

        self.assertEqual(code, 0, report)
        self.assertCompleteReport(report)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["plan_step_count"], len(_clean_state_plan()))
        self.assertSelectedKeysEmpty(report)


class LegacyCoverageAdvisoryTests(StatusEvidenceReportAssertions, unittest.TestCase):
    """FR-004: legacy coverage debt stays visible without blocking status-evidence."""

    def test_missing_state_coverage_lists_remain_visible_but_nonblocking(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            supplied, state = clean_workflow_state_fixture(Path(raw))
            planted = json.loads(state.read_text(encoding="utf-8"))
            planted["plan"] = [planted["plan"][0]]
            state.write_text(json.dumps(planted), encoding="utf-8")

            code, report = run_status_evidence_report(supplied, state)

        self.assertEqual(code, 0, report)
        self.assertCompleteReport(report)
        self.assertTrue(report["missing_state_prefixes"], report)
        self.assertTrue(report["missing_state_post_items"], report)
        self.assertSelectedKeysEmpty(report)


class StatusEvidenceSourceGuidanceTests(unittest.TestCase):
    """The shipped source skills must describe the same scoped-gate contract."""

    def test_source_guidance_distinguishes_legacy_debt_from_blocking_state_invariants(self) -> None:
        for label, path in (
            ("Claude", CLAUDE_AUTOPILOT_SKILL),
            ("Codex", CODEX_AUTOPILOT_SKILL),
        ):
            with self.subTest(skill=label):
                guidance = status_evidence_guidance_paragraph(path)
                folded = guidance.lower()
                self.assertIn("legacy structural coverage debt", folded)
                self.assertIn("visible", folded)
                self.assertIn("nonblocking", folded)
                self.assertIn("current-run state invariants", folded)
                self.assertIn("stop the run", folded)
                for key in BLOCKING_STATE_INVARIANT_KEYS:
                    self.assertIn(key, guidance)


class TrackedPathEnumerationTests(unittest.TestCase):
    """FR-013: tracked workflow/state discovery comes from the git index."""

    def test_tracked_workflow_state_paths_use_git_index_contract(self) -> None:
        stdout = (
            "specs/zeta/ART-999-workflow.md\0"
            "docs/unrelated.md\0"
            "specs/alpha/autopilot-state.json\0"
            "specs/alpha/ART-001-workflow.md\0"
        ).encode("utf-8")
        completed = subprocess.CompletedProcess(
            args=["git", "ls-files", "-z"],
            returncode=0,
            stdout=stdout,
            stderr=b"",
        )

        with mock.patch("subprocess.run", return_value=completed) as run:
            paths = tracked_workflow_state_paths(REPO_ROOT)

        run.assert_called_once_with(
            ["git", "ls-files", "-z"],
            cwd=REPO_ROOT,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        self.assertEqual(
            paths,
            (
                "specs/alpha/ART-001-workflow.md",
                "specs/alpha/autopilot-state.json",
                "specs/zeta/ART-999-workflow.md",
            ),
        )

    def test_git_index_enumeration_failure_is_not_silently_skipped(self) -> None:
        failure = subprocess.CalledProcessError(
            returncode=128,
            cmd=["git", "ls-files", "-z"],
            stderr=b"fatal: not a git repository",
        )

        with mock.patch("subprocess.run", side_effect=failure):
            with self.assertRaisesRegex(RuntimeError, "git ls-files -z failed"):
                tracked_workflow_state_paths(REPO_ROOT)


class AuthorityMatchedPairClassificationTests(unittest.TestCase):
    """FR-012/FR-015: only tracked adjacent workflow/state authority pairs qualify."""

    @staticmethod
    def _write_state(root: Path, rel_path: str, workflow_file: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"workflow_file": workflow_file, "plan": _clean_state_plan()}),
            encoding="utf-8",
        )

    def test_exact_tracked_adjacent_authority_match_is_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_state(
                root,
                "specs/alpha/autopilot-state.json",
                "specs/alpha/ART-001-workflow.md",
            )
            result = classify_authority_matched_pairs(
                root,
                (
                    "specs/alpha/ART-001-workflow.md",
                    "specs/alpha/autopilot-state.json",
                ),
            )

        self.assertEqual(
            result,
            {
                "eligible": ((
                    "specs/alpha/ART-001-workflow.md",
                    "specs/alpha/autopilot-state.json",
                ),),
                "excluded": (),
            },
        )

    def test_missing_adjacent_state_is_excluded_without_synthesis(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = classify_authority_matched_pairs(
                Path(raw),
                ("specs/missing/ART-002-workflow.md",),
            )

        self.assertEqual(result["eligible"], ())
        self.assertEqual(
            result["excluded"],
            ({
                "workflow": "specs/missing/ART-002-workflow.md",
                "state": "specs/missing/autopilot-state.json",
                "reason": "missing-adjacent-state",
            },),
        )

    def test_mismatched_authority_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_state(
                root,
                "specs/mismatch/autopilot-state.json",
                "specs/other/ART-003-workflow.md",
            )
            result = classify_authority_matched_pairs(
                root,
                (
                    "specs/mismatch/ART-003-workflow.md",
                    "specs/mismatch/autopilot-state.json",
                ),
            )

        self.assertEqual(result["eligible"], ())
        self.assertEqual(
            result["excluded"],
            ({
                "workflow": "specs/mismatch/ART-003-workflow.md",
                "state": "specs/mismatch/autopilot-state.json",
                "reason": "workflow-file-mismatch",
                "workflow_file": "specs/other/ART-003-workflow.md",
            },),
        )

    def test_untracked_adjacent_state_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_state(
                root,
                "specs/untracked/autopilot-state.json",
                "specs/untracked/ART-004-workflow.md",
            )
            result = classify_authority_matched_pairs(
                root,
                ("specs/untracked/ART-004-workflow.md",),
            )

        self.assertEqual(result["eligible"], ())
        self.assertEqual(
            result["excluded"],
            ({
                "workflow": "specs/untracked/ART-004-workflow.md",
                "state": "specs/untracked/autopilot-state.json",
                "reason": "untracked-adjacent-state",
            },),
        )

    def test_matching_non_adjacent_state_is_not_synthesized(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_state(
                root,
                "specs/elsewhere/autopilot-state.json",
                "specs/synthetic/ART-005-workflow.md",
            )
            result = classify_authority_matched_pairs(
                root,
                (
                    "specs/elsewhere/autopilot-state.json",
                    "specs/synthetic/ART-005-workflow.md",
                ),
            )

        self.assertEqual(result["eligible"], ())
        self.assertEqual(
            result["excluded"],
            ({
                "workflow": "specs/synthetic/ART-005-workflow.md",
                "state": "specs/synthetic/autopilot-state.json",
                "reason": "missing-adjacent-state",
            },),
        )

    def test_tracked_state_read_failure_is_not_silently_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            state = root / "specs/read/autopilot-state.json"
            state.parent.mkdir(parents=True, exist_ok=True)
            state.mkdir()

            with self.assertRaisesRegex(OSError, "specs/read/autopilot-state.json"):
                classify_authority_matched_pairs(
                    root,
                    (
                        "specs/read/ART-006-workflow.md",
                        "specs/read/autopilot-state.json",
                    ),
                )

    def test_tracked_state_json_parse_failure_is_not_silently_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            state = root / "specs/bad-json/autopilot-state.json"
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text("{not-json", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "specs/bad-json/autopilot-state.json"):
                classify_authority_matched_pairs(
                    root,
                    (
                        "specs/bad-json/ART-007-workflow.md",
                        "specs/bad-json/autopilot-state.json",
                    ),
                )


class TrackedPairCorpusTests(StatusEvidenceReportAssertions, unittest.TestCase):
    """FR-012/FR-014: live tracked authority-matched pairs stay valid."""

    def test_tracked_authority_matched_pair_corpus_reconciles_and_passes(self) -> None:
        tracked_paths = tracked_workflow_state_paths(REPO_ROOT)
        workflow_candidates = tuple(
            path for path in tracked_paths if path.endswith("-workflow.md")
        )
        classified = classify_authority_matched_pairs(REPO_ROOT, tracked_paths)
        eligible = classified["eligible"]
        exclusions = classified["excluded"]

        invoked: list[tuple[str, str]] = []
        passed: list[tuple[str, str]] = []
        for workflow_ref, state_ref in eligible:
            code, report = run_status_evidence_report(REPO_ROOT / workflow_ref, REPO_ROOT / state_ref)
            invoked.append((workflow_ref, state_ref))
            self.assertCompleteReport(report)
            if code == 0:
                passed.append((workflow_ref, state_ref))
            else:
                self.fail(f"tracked pair {workflow_ref} failed status-evidence: {report}")

        self.assertGreater(len(workflow_candidates), 0)
        self.assertGreater(len(eligible), 0)
        self.assertEqual(len(invoked), len(eligible))
        self.assertEqual(len(passed), len(eligible))
        self.assertEqual(len(eligible) + len(exclusions), len(workflow_candidates))
        self.assertEqual(
            {entry["workflow"] for entry in exclusions},
            set(workflow_candidates) - {workflow for workflow, _state in eligible},
        )
        for entry in exclusions:
            with self.subTest(workflow=entry["workflow"]):
                self.assertIn("reason", entry)
                self.assertTrue(entry["reason"])


class ART017StatusEvidenceNegativeTests(StatusEvidenceReportAssertions, unittest.TestCase):
    """ART-017 isolated state-invariant controls for the status-evidence gate."""

    def test_in_progress_errors_isolated_mutation_blocks_status_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            supplied, state = clean_workflow_state_fixture(Path(raw))
            planted = json.loads(state.read_text(encoding="utf-8"))
            planted["plan"][0]["status"] = "in_progress"
            planted["plan"][1]["status"] = "in_progress"
            state.write_text(json.dumps(planted), encoding="utf-8")

            code, report = run_status_evidence_report(supplied, state)

        self.assertCompleteReport(report)
        self.assertOnlySelectedProblemKeyPopulated(report, "in_progress_errors")
        self.assertEqual(code, 1, report)

    def test_duplicate_state_steps_isolated_mutation_blocks_status_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            supplied, state = clean_workflow_state_fixture(Path(raw))
            planted = json.loads(state.read_text(encoding="utf-8"))
            planted["plan"].append(dict(planted["plan"][0]))
            state.write_text(json.dumps(planted), encoding="utf-8")

            code, report = run_status_evidence_report(supplied, state)

        self.assertCompleteReport(report)
        self.assertOnlySelectedProblemKeyPopulated(report, "duplicate_state_steps")
        self.assertEqual(code, 1, report)

    def test_state_order_errors_isolated_mutation_blocks_status_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            supplied, state = clean_workflow_state_fixture(Path(raw))
            planted = json.loads(state.read_text(encoding="utf-8"))
            planted["plan"][0], planted["plan"][1] = planted["plan"][1], planted["plan"][0]
            state.write_text(json.dumps(planted), encoding="utf-8")

            code, report = run_status_evidence_report(supplied, state)

        self.assertCompleteReport(report)
        self.assertOnlySelectedProblemKeyPopulated(report, "state_order_errors")
        self.assertEqual(code, 1, report)


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
        # Repository-relative against this root. An absolute value is rejected
        # as malformed before the comparison is ever reached.
        return clean_workflow_state_fixture(root, state_workflow_ref=state_workflow_ref)

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
        # The exit code too, and not only the report key. Reporting a finding the
        # scoped invocation does not gate on is the defect this specification
        # exists to close, so a control that stops at the key would still pass if
        # the key left the ``status-evidence`` tuple.
        self.assertEqual(completed.returncode, 1, report)

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


class RepositoryRootResolutionTests(unittest.TestCase):
    """A resolution failure must skip, never escape as a traceback."""

    def test_unresolvable_path_returns_none_instead_of_raising(self) -> None:
        """`main()` catches only ValidationError, so anything else prints a
        traceback where the autopilot expects a JSON report. Today this is hard
        to reach because ``load_state`` reads the state file first, but that is
        a property of the caller, not of this function, and four call sites rely
        on it. The guard makes the function safe on its own terms.
        """
        import os

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            a, b = root / "loop_a", root / "loop_b"
            os.symlink(b, a)
            os.symlink(a, b)
            # Whether resolve() raises on a loop is platform and version
            # dependent; either way the contract is the same, never raise.
            self.assertIsNone(validator._repository_root(a / "state.json"))

    def test_an_unresolvable_supplied_workflow_skips_instead_of_raising(self) -> None:
        """The authority helper resolves a second path, and it must not raise either.

        ``_repository_root`` is guarded, so the same fixture that proves that
        guard also reaches the helper's own ``workflow.resolve()``. The state
        file here is a real readable path inside a marked root, so the helper
        gets past branches 1 and 2 and reaches the resolution of the *supplied*
        workflow. A raise there escapes ``build_report``, which has no handler,
        and then ``main()``, which catches only ``ValidationError`` -- printing a
        traceback where the autopilot expects the JSON report.
        """
        import os

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".git").write_text(
                "gitdir: ../elsewhere/.git/worktrees/fixture\n", encoding="utf-8"
            )
            state = root / "autopilot-state.json"
            state.write_text(
                json.dumps({"workflow_file": SUPPLIED_WORKFLOW_REF, "plan": []}),
                encoding="utf-8",
            )
            a, b = root / "loop_a", root / "loop_b"
            os.symlink(b, a)
            os.symlink(a, b)
            self.assertEqual(
                validator._workflow_authority_errors(
                    a / "supplied-workflow.md",
                    state,
                    {"workflow_file": SUPPLIED_WORKFLOW_REF},
                ),
                [],
            )


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
            supplied, state = clean_workflow_state_fixture(Path(raw))
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

    def test_the_gated_verdict_agrees_with_the_rule_map(self) -> None:
        """A `gated` verdict is a claim about ``RULE_PROBLEM_KEYS``, so check it there.

        ``verdict == "gated"`` says a named rule can move the exit code on that
        key, which is decided entirely by membership in ``RULE_PROBLEM_KEYS``.
        Recording it by hand in a second place is how the two drift: arm a key in
        the rule map and leave it advisory here, or retire it from the rule map
        and leave the verdict behind, and every other assertion in this class
        still passes. The record would then misdescribe exactly the property it
        exists to make visible.
        """
        gated_by_record = {
            key
            for key, entry in validator.PROBLEM_KEY_INTENT.items()
            if entry["verdict"] == "gated"
        }
        gated_by_rules = {
            key for keys in validator.RULE_PROBLEM_KEYS.values() for key in keys
        }
        self.assertEqual(
            gated_by_record,
            gated_by_rules,
            "PROBLEM_KEY_INTENT and RULE_PROBLEM_KEYS disagree about which keys are "
            f"gated; recorded-only {sorted(gated_by_record - gated_by_rules)}, "
            f"rule-only {sorted(gated_by_rules - gated_by_record)}",
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
        CleanStatusEvidenceControlTests,
        LegacyCoverageAdvisoryTests,
        StatusEvidenceSourceGuidanceTests,
        TrackedPathEnumerationTests,
        AuthorityMatchedPairClassificationTests,
        TrackedPairCorpusTests,
        ART017StatusEvidenceNegativeTests,
        WorkflowAuthorityTests,
        RepositoryRootResolutionTests,
        ProblemKeyClassificationTests,
    ):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-autopilot-bookkeeping-guard")


if __name__ == "__main__":
    raise SystemExit(main())
