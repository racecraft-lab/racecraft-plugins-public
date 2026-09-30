#!/usr/bin/env python3
"""Blocked actions and gate failures fall back or defer; neither stops for a human.

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
    _assert_absent,
    _assert_phrases,
    _claude_reference,
    _codex_reference,
    _flat,
    _section,
    _section_after,
)  # noqa: E402
from test_result import run_counted  # noqa: E402


class BlockedActionDeferralSourceContractTests(unittest.TestCase):
    """One blocked action mid-run must not stop independent work (issue 752)."""

    def assert_deferral_rules(self, section: str, ask_tool: str) -> None:
        _assert_phrases(self, section, (*PHRASES["BlockedActionDeferralSourceContractTests.assert_deferral_rules#1"], ask_tool))

    def test_codex_phase_seven_defers_a_blocked_action_and_continues(self) -> None:
        phase = _codex_reference("phase-execution-codex.md")
        section = _section_after(
            self, phase, "## Phase 7: Implement", f"### {BLOCKED_ACTION_HEADING}", "## PR Packet and Body Boundary"
        )
        self.assert_deferral_rules(section, "`request_user_input`")
        self.assertIn("make no `request_user_input` call for it", section)
        # The late-discovery rule no longer routes a mid-run boundary into the
        # pre-Phase-7 stop.
        late = _section(phase, "If a worker discovers a predictable boundary", "```text")
        _assert_phrases(self, late, ("defers only that task", BLOCKED_ACTION_HEADING))

    def test_codex_entrypoint_and_post_audit_allow_an_honest_deferred_end(self) -> None:
        skill = _flat(CODEX_AUTOPILOT_SKILL)
        post = _codex_reference("post-implementation-codex.md")
        recovery = _codex_reference("error-recovery-codex.md")
        self.assertIn(BLOCKED_ACTION_HEADING, skill)
        audit = _section(skill, "### 3.4 Pre-final completion audit", "Only after every Post item")
        _assert_phrases(self, audit, ("deferred items remain", "plain text in the final message"))
        _assert_phrases(self, post, ("deferred items remain", "known_gaps"))
        _assert_phrases(self, recovery, ("Action blocked mid-run", BLOCKED_ACTION_HEADING))

    def test_claude_phase_seven_mirrors_the_deferral_rule(self) -> None:
        phase = _claude_reference("phase-execution.md")
        section = _section_after(
            self, phase, "#### Never Yield With Nothing In Flight", f"#### {BLOCKED_ACTION_HEADING}", "#### Append Contract"
        )
        self.assert_deferral_rules(section, "`AskUserQuestion`")
        never_yield = _section(
            phase, "#### Never Yield With Nothing In Flight", f"#### {BLOCKED_ACTION_HEADING}"
        )
        self.assertIn("A blocked action is not a stop condition", never_yield)

    def test_claude_entrypoint_and_recovery_mirror_the_deferred_end(self) -> None:
        skill = _flat(CLAUDE_AUTOPILOT_SKILL)
        recovery = _claude_reference("error-recovery.md")
        audit = _section(skill, "### 3.4 Pre-final completion audit", "## Workflow File Update Protocol")
        _assert_phrases(self, audit, (
            "deferred items remain",
            "plain text in the final message",
            BLOCKED_ACTION_HEADING,
        ))
        _assert_phrases(self, recovery, ("Action blocked mid-run", BLOCKED_ACTION_HEADING))


GATE_DEFER_PHRASE = "run the repair loop within its allowance, then defer per the Failure Escalation Protocol"


class GateFailureDeferSourceContractTests(unittest.TestCase):
    """A gate failure repairs, then defers; it never stops for a human (issue 828)."""

    def gate_validation(self) -> str:
        return _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "gate-validation.md")

    def test_every_gate_failure_line_defers_instead_of_stopping(self) -> None:
        text = self.gate_validation()
        bounds = (("G0", "### G1"), ("G2", "### G3"), ("G3", "### G4"), ("G4", "### G5"),
                  ("G5", "#### Post-G5"), ("G6", "### G7"), ("G7", "## Gate Summary Table"))
        for gate_id, next_heading in bounds:
            self.assertIn(GATE_DEFER_PHRASE, _section(text, f"### {gate_id} ", next_heading), gate_id)
        for stale in PHRASES["GateFailureDeferSourceContractTests.test_every_gate_failure_line_defers_instead_of_stopping#1"]:
            self.assertNotIn(stale, text)

    def test_skip_and_log_is_not_a_gate_failure_option(self) -> None:
        text = self.gate_validation()
        g3 = _section(text, "### G3 ", "### G4 ")
        _assert_absent(self, g3, ("skip-and-log", "configured `gate-failure` behavior"))

    def test_gate_failure_default_is_defer_on_both_hosts(self) -> None:
        claude = _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "prerequisites.md")
        codex = _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / "prerequisites-codex.md")
        readme = _flat(REPO_ROOT / "speckit-pro" / "README.md")
        for text in (claude, codex):
            self.assertIn("`gate-failure` (default: `defer`)", text)
            self.assertNotIn("`gate-failure` (default: `stop`)", text)
        self.assertIn("gate-failure: defer", readme)
        self.assertNotIn("gate-failure: stop", readme)

    def test_codex_phase_seven_defers_a_persistent_gate_failure(self) -> None:
        phase = _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / "phase-execution-codex.md")
        _assert_absent(self, phase, ('gate-failure == "stop"', 'gate-failure == "skip-and-log"'))
        _assert_phrases(self, phase, (
            "If still failing, defer per the Failure Escalation Protocol",
            "A selected formal failure defers and names the Plan resume point",
        ))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-autopilot-blocked-action-deferral"))
