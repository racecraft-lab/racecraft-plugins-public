#!/usr/bin/env python3
"""Run finalization: only human UAT may be deferred; anything else left is one human stop.

Python 3.11+ standard library only.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
LIB_DIR = TEST_DIR.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from autopilot_bookkeeping_support import (
    BLOCKED_ACTION_HEADING,
    CLAUDE_AUTOPILOT_SKILL,
    CODEX_AUTOPILOT_SKILL,
    PHRASES,
    _assert_phrases,
    _flat,
    _section,
)  # noqa: E402
from test_result import run_counted  # noqa: E402


class RunFinalizationSourceContractTests(unittest.TestCase):
    """Only human UAT may be deferred; anything else left is one human stop (issue 804)."""

    STALE = PHRASES["RunFinalizationSourceContractTests#1"]
    PER_HEAD = PHRASES["RunFinalizationSourceContractTests#2"]
    STACK_PER_HEAD = PHRASES["RunFinalizationSourceContractTests#3"]

    def assert_finalization_rules(self, section: str) -> None:
        for phrase in (
            "`finalize-run`",
            "Human UAT is the only gate a run may defer",
            "`human_uat`",
            "ready for review",
            "never merges",
            "`Deferred / not verified`",
            "`deferred_items`",
            "`ready_commands`",
            "`end_of_run_request`",
            "`outcome=human_stop`",
            "one human stop",
            "exact command",
            "retry with backoff",
            "reviewer veto despite a recorded chat authorization",
            "never lets a gate pass, be skipped, or be deferred",
            "at the end of the run an unresolved deferral climbs the escalation tiers",
            "\"Decisions for you\"",
            "The run never pauses to ask",
            "the only stop is a required gate that is still not green",
            "`deferred_digest`",
            "never re-checks an unchanged blocker",
            *self.PER_HEAD,
        ):
            self.assertIn(phrase, section)
        for phrase in self.STALE:
            self.assertNotIn(phrase, section)

    def test_codex_finalizes_a_deferred_run_and_completes_the_goal(self) -> None:
        references = CODEX_AUTOPILOT_SKILL.parent / "references"
        phase = _flat(references / "phase-execution.md")
        section = _section(phase, f"### {BLOCKED_ACTION_HEADING}", "### Repeated Gate Failures")
        self.assert_finalization_rules(section)
        self.assertIn("marks the thread goal complete", section)
        self.assertIn("never set the thread goal blocked for it mid-run", phase)
        recovery = _flat(references / "error-recovery.md")
        self.assertIn("never sets the thread goal blocked mid-run", recovery)
        self.assertNotIn("never sets the thread goal blocked.", recovery)
        hardener = _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "hardener-delegation.md")
        self.assertIn("It is a gate, so it never stays deferred", hardener)
        efficiency = _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "execution-efficiency.md")
        self.assertIn("only a required gate that is not green makes `finalize-run` return", efficiency)
        preflight = _section(phase, "### Autonomy Boundary Preflight", "1. Read mode from `CONFIDENCE_GATE_MODE`")
        for phrase in PHRASES["RunFinalizationSourceContractTests.test_codex_finalizes_a_deferred_run_and_completes_the_goal#1"]:
            self.assertIn(phrase, preflight)
        skill = _flat(CODEX_AUTOPILOT_SKILL)
        audit = _section(skill, "### 3.4 Pre-final completion audit", "## Workflow File Update Protocol")
        self.assertIn("`finalize-run`", audit)
        for phrase in self.STALE:
            self.assertNotIn(phrase, skill)
        post = _flat(references / "post-implementation.md")
        _assert_phrases(self, post, ("`finalize-run`", "`deferred_items`"))
        self.assertIn("every PR head", audit)
        for phrase in self.STACK_PER_HEAD:
            self.assertIn(phrase, post)
        for phrase in self.STALE:
            self.assertNotIn(phrase, post)

    def test_claude_mirrors_the_finalization(self) -> None:
        references = CLAUDE_AUTOPILOT_SKILL.parent / "references"
        phase = _flat(references / "phase-execution.md")
        section = _section(phase, f"#### {BLOCKED_ACTION_HEADING}", "#### Repeated Gate Failures")
        self.assert_finalization_rules(section)
        skill = _flat(CLAUDE_AUTOPILOT_SKILL)
        audit = _section(skill, "### 3.4 Pre-final completion audit", "## Workflow File Update Protocol")
        _assert_phrases(self, audit, ("`finalize-run`", "every PR head"))
        for phrase in self.STALE:
            self.assertNotIn(phrase, skill)
        post = _flat(references / "post-implementation.md")
        for phrase in self.STACK_PER_HEAD:
            self.assertIn(phrase, post)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-autopilot-run-finalization"))
