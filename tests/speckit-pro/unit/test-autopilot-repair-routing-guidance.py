#!/usr/bin/env python3
"""Guidance pins: a fixable helper result routes to its owner instead of stopping (issue 835).

Once a run starts, a fixable condition goes to the owning agent, is retried within
the shared allowance, and defers only when repair fails. Only authority and
exhausted-tier reasons involve a human (`references/stop-policy.md`). Each test
pins one case from the audit on both hosts, so a stop line cannot return.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
sys.path.insert(0, str(TEST_DIR.parent / "lib"))

from test_result import run_counted  # noqa: E402

PLUGIN = REPO_ROOT / "speckit-pro"
CLAUDE = PLUGIN / "skills" / "speckit-autopilot"
CODEX = PLUGIN / "codex-skills" / "speckit-autopilot"
REPAIR_THEN_DEFER = "run the repair loop within its allowance, then defer per the Failure Escalation Protocol"

CLAUDE_SKILL = CLAUDE / "SKILL.md"
CODEX_SKILL = CODEX / "SKILL.md"
CLAUDE_PHASE = CLAUDE / "references" / "phase-execution.md"
CODEX_PHASE = CODEX / "references" / "phase-execution-codex.md"
CLAUDE_POST = CLAUDE / "references" / "post-implementation.md"
CODEX_POST = CODEX / "references" / "post-implementation-codex.md"
CLAUDE_PREREQ = CLAUDE / "references" / "prerequisites.md"
CODEX_PREREQ = CODEX / "references" / "prerequisites-codex.md"
GATES = CLAUDE / "references" / "gate-validation.md"
EFFICIENCY = CLAUDE / "references" / "execution-efficiency.md"
STACK_MANAGER = CLAUDE / "references" / "stack-manager.md"


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class Pinned(unittest.TestCase):
    def assert_pinned(self, path: Path, present: tuple[str, ...], absent: tuple[str, ...] = ()) -> None:
        text = flat(path)
        for phrase in present:
            self.assertIn(phrase, text, f"{path.name}: missing {phrase!r}")
        for phrase in absent:
            self.assertNotIn(phrase, text, f"{path.name}: still has {phrase!r}")


class LayerPlannerRepairTests(Pinned):
    PRESENT = (
        "route the planner's `repair` record to the phase-executor",
        "rerun `plan-layers-feature-dir`",
        "`tasks_file_missing`",
        REPAIR_THEN_DEFER,
    )
    ABSENT = ("STOP: Layer planner returned invalid_plan", "STOP before implementation", "STOP separately")

    def test_invalid_plan_and_input_error_route_to_their_owner_on_both_hosts(self) -> None:
        for skill in (CLAUDE_SKILL, CODEX_SKILL):
            with self.subTest(skill=skill.parent.parent.name):
                self.assert_pinned(skill, self.PRESENT, self.ABSENT)


class CoverageGuardRepairTests(Pinned):
    PRESENT = (
        "On a nonzero exit, route the report's `repair` record to the orchestrator",
        "`failing_keys`",
        REPAIR_THEN_DEFER,
    )
    ABSENT = (
        "guard and STOP on a nonzero exit",
        "guard and STOP on nonzero exit",
        "any other failing gated key, is a stop",
    )

    def test_a_nonzero_guard_exit_is_repaired_not_a_stop_on_both_hosts(self) -> None:
        for skill in (CLAUDE_SKILL, CODEX_SKILL):
            with self.subTest(skill=skill.parent.parent.name):
                self.assert_pinned(skill, self.PRESENT, self.ABSENT)

    def test_codex_plan_state_validation_repairs_before_phase_one(self) -> None:
        self.assert_pinned(
            CODEX_SKILL,
            ("Before Phase 1 starts, validate all of the following or repair it",),
            ("Before Phase 1 starts, validate all of the following or STOP",),
        )


class SpecIndexWriteRepairTests(Pinned):
    def test_exit_two_routes_the_stderr_line_to_the_phase_executor(self) -> None:
        for phase in (CLAUDE_PHASE, CODEX_PHASE):
            with self.subTest(phase=phase.name):
                self.assert_pinned(
                    phase,
                    (
                        "Route the actionable stderr line to the phase-executor",
                        "rerun `generate-spec-index-write` once",
                        "Do NOT commit a broken regeneration",
                        REPAIR_THEN_DEFER,
                    ),
                    ("Surface the actionable stderr line and STOP",),
                )


class PostImplementationRepairTests(Pinned):
    STALE = (
        "stop before PR creation",
        "stop before PR side effects",
        "stop before `generate-pr-body`",
        "stop before branch or PR mutation",
        "must stop before `gh pr create`",
        "STOP before PR-body generation",
        "or stop blocked with the validator output",
        "stop with state only",
        "stop-before-PR boundary",
    )

    def test_no_post_implementation_file_tells_the_run_to_stop_before_a_pr(self) -> None:
        for path in (CLAUDE_POST, CODEX_POST, GATES, CODEX_PHASE):
            with self.subTest(path=path.name):
                self.assert_pinned(path, (), self.STALE)

    def test_an_invalid_packet_goes_to_the_packet_regenerator(self) -> None:
        for path in (CLAUDE_POST, CODEX_POST):
            with self.subTest(path=path.name):
                self.assert_pinned(
                    path,
                    (
                        "regenerate it with `pr-packet-output` from the validator diagnostics",
                        "No PR is created until",
                        REPAIR_THEN_DEFER,
                    ),
                )

    def test_a_failing_scoped_command_goes_to_the_implement_executor(self) -> None:
        for path in (CLAUDE_POST, CODEX_POST):
            with self.subTest(path=path.name):
                self.assert_pinned(
                    path,
                    ("route the failing command to the implement-executor", "keep `next_slice_id` on the blocked slice"),
                )

    def test_an_invalid_runbook_goes_to_the_uat_runbook_author(self) -> None:
        for path in (CLAUDE_POST, CODEX_POST):
            with self.subTest(path=path.name):
                self.assert_pinned(
                    path,
                    ("route the validator diagnostics to the uat-runbook-author", "hold PR-body generation"),
                )

    def test_missing_reviewability_evidence_and_checkpoint_shas_are_repaired(self) -> None:
        for path in (CLAUDE_POST, CODEX_POST):
            with self.subTest(path=path.name):
                self.assert_pinned(
                    path,
                    (
                        "regenerate the committed reviewability evidence",
                        "record the marker checkpoint commit SHAs",
                    ),
                )


class RedBaselineRepairTests(Pinned):
    def test_a_red_baseline_goes_to_the_implement_executor_on_both_hosts(self) -> None:
        for path in (CLAUDE_PREREQ, CODEX_PREREQ):
            with self.subTest(path=path.name):
                self.assert_pinned(
                    path,
                    ("route the failing check to the implement-executor", REPAIR_THEN_DEFER),
                    ("If any check or populated blocking gate fails, STOP", "report each failed check's `message` and STOP"),
                )
        self.assert_pinned(
            CLAUDE_PHASE,
            ("route the failing gate to the implement-executor", REPAIR_THEN_DEFER),
            ("If any fail, STOP; a missing or",),
        )
        self.assert_pinned(
            CLAUDE_SKILL,
            ("route each failing check to the implement-executor",),
            ("workflow's Prerequisites table. STOP on any failure.",),
        )


class MissingQualityToolTests(Pinned):
    def test_a_missing_tool_defaults_to_its_install_hint_then_skip_spec(self) -> None:
        for path in (CLAUDE_PREREQ, CODEX_PREREQ):
            with self.subTest(path=path.name):
                self.assert_pinned(
                    path,
                    (
                        "default to the recorded install hint, then `skip (spec)`",
                        "never asks",
                        "Decisions for you",
                    ),
                    (
                        "one question per tool per repository",
                        "STOP naming the tool and the three options",
                        "If it is still false, STOP.",
                        "ask once with `AskUserQuestion`",
                        "ask once with `request_user_input`",
                    ),
                )


class ArchiveSweepRepairTests(Pinned):
    def test_a_failed_archive_sweep_defers_and_the_run_continues_to_phase_zero(self) -> None:
        self.assert_pinned(
            CLAUDE_SKILL,
            ("defer the Archive Sweep with that discovery evidence and continue to Phase 0",),
            ("STOP pre-flight with that discovery evidence",),
        )
        self.assert_pinned(
            CODEX_PREREQ,
            (
                "defer the Archive Sweep with the exact failed path or operation and continue to Phase 0",
                "Retry the failed archive run once",
            ),
            ("Then STOP before Phase 0 with the exact failed path", "then STOP before Phase 0."),
        )


class PrSplitRatificationRepairTests(Pinned):
    def test_input_error_and_size_findings_repair_and_only_scope_changes_stay_with_the_operator(self) -> None:
        for phase in (CLAUDE_PHASE, CODEX_PHASE):
            with self.subTest(phase=phase.name):
                self.assert_pinned(
                    phase,
                    (
                        "regenerate the split evidence from the layer plan",
                        "`decision=reslice_required`",
                        "`stop_reason:scope_changing_pr_split`",
                        "never ratify it yourself",
                    ),
                    ("An `input_error`, a missing budget, or unreadable evidence also goes to the operator",),
                )


class TaskResultsRedispatchTests(Pinned):
    def test_unfinished_task_results_redispatch_to_the_batch_agent(self) -> None:
        for path in (CLAUDE_PHASE, CODEX_PHASE, EFFICIENCY):
            with self.subTest(path=path.name):
                self.assert_pinned(
                    path,
                    ("`disposition=redispatch`", "`repair` record", "unfinished task IDs"),
                )
        self.assert_pinned(
            EFFICIENCY,
            (),
            ("persisted with `helper_exit_code=1` and `disposition=checkpoint_required`",),
        )


class StackManagerRecoveryTests(Pinned):
    def test_a_partial_mutation_is_reverified_and_retried_before_it_defers(self) -> None:
        for path in (STACK_MANAGER, CODEX_POST):
            with self.subTest(path=path.name):
                self.assert_pinned(path, ("`reverify_recovery=true`", "retry the existing-PR link"))
        self.assert_pinned(
            STACK_MANAGER,
            ("stays blocked and defers only when", "recreate PRs, or erase the attempted boundary"),
        )


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    return unittest.TestSuite(
        loader.loadTestsFromTestCase(case)
        for case in (
            LayerPlannerRepairTests,
            CoverageGuardRepairTests,
            SpecIndexWriteRepairTests,
            PostImplementationRepairTests,
            RedBaselineRepairTests,
            MissingQualityToolTests,
            ArchiveSweepRepairTests,
            PrSplitRatificationRepairTests,
            TaskResultsRedispatchTests,
            StackManagerRecoveryTests,
        )
    )


def main() -> int:
    return run_counted(build_suite(), label="test-autopilot-repair-routing-guidance")


if __name__ == "__main__":
    raise SystemExit(main())
