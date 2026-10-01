#!/usr/bin/env python3
"""Ambiguous task wording and gate-task splitting in the Tasks guidance.

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
    _assert_phrases,
    _flat,
    _section,
)  # noqa: E402
from test_result import run_counted  # noqa: E402


AMBIGUOUS_WORDING_HEADING = "Ambiguous Task Wording: Apply the Recorded Decision, Else Defer"


class AmbiguousTaskWordingSourceContractTests(unittest.TestCase):
    """A recorded owner decision settles ambiguous task wording mid-run (issue 773)."""

    def assert_recorded_decision_rule(self, section: str) -> None:
        for phrase in (
            "wording is ambiguous",
            "recorded owner decision",
            "apply that decision",
            "record the interpretation with a reference to that decision",
            "then continue",
            "no recorded decision covers it",
            "defer the item",
            "end-of-run request",
            "Never ask the operator mid-run",
            BLOCKED_ACTION_HEADING,
        ):
            self.assertIn(phrase, section)

    def test_claude_phase_seven_applies_a_recorded_decision_to_ambiguous_wording(self) -> None:
        phase = _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "phase-execution.md")
        section = _section(phase, f"#### {AMBIGUOUS_WORDING_HEADING}", "#### Append Contract")
        self.assertLess(phase.index(f"#### {BLOCKED_ACTION_HEADING}"), phase.index(section))
        self.assert_recorded_decision_rule(section)

    def test_codex_phase_seven_applies_a_recorded_decision_to_ambiguous_wording(self) -> None:
        phase = _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / "phase-execution.md")
        section = _section(phase, f"### {AMBIGUOUS_WORDING_HEADING}", "## PR Packet and Body Boundary")
        self.assertLess(phase.index(f"### {BLOCKED_ACTION_HEADING}"), phase.index(section))
        self.assert_recorded_decision_rule(section)


class GateTaskEvidenceLoopGuidanceTests(unittest.TestCase):
    """Tasks guidance splits a gate task instead of making it wait on its dependents (issue 773)."""

    def test_tasks_prompt_and_g5_guidance_split_gate_tasks(self) -> None:
        template = _flat(REPO_ROOT / "speckit-pro" / "skills" / "speckit-coach" / "templates" / "workflow-template.md")
        prompt = _section(template, "### Tasks Prompt", "### Tasks Results")
        gates = _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "gate-validation.md")
        g5 = _section(gates, "### G5 — After Tasks", "#### Post-G5 Reviewability Capture Matrix")
        claude = _section(
            _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "phase-execution.md"),
            "### Phase 5: Tasks", "### Phase 6: Analyze",
        )
        codex = _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / "phase-execution.md")
        for text in (prompt, g5, claude, codex):
            _assert_phrases(self, text, ("candidate check", "emission step"))
        for text in (g5, claude, codex):
            self.assertIn("gate_task_loops", text)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-autopilot-ambiguous-task-wording"))
