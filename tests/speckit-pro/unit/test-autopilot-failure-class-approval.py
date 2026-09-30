#!/usr/bin/env python3
"""Repeated gate failures: diagnose one failure class and approve it once.

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
    CLAUDE_AUTOPILOT_SKILL,
    CODEX_AUTOPILOT_SKILL,
    PHRASES,
    _assert_phrases,
    _flat,
    _section,
)  # noqa: E402
from test_result import run_counted  # noqa: E402


FAILURE_CLASS_HEADING = "Repeated Gate Failures: Diagnose One Class, Approve It Once"


class FailureClassApprovalSourceContractTests(unittest.TestCase):
    """Repeated same-signature gate failures are one class with one approval (issue 785)."""

    def assert_class_rules(self, section: str) -> None:
        for phrase in PHRASES["FailureClassApprovalSourceContractTests.assert_class_rules#1"]:
            self.assertIn(phrase, section)

    def test_codex_phase_execution_states_the_class_rule(self) -> None:
        phase = _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / "phase-execution-codex.md")
        section = _section(phase, f"### {FAILURE_CLASS_HEADING}", "## PR Packet and Body Boundary")
        self.assert_class_rules(section)
        recovery = _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / "error-recovery-codex.md")
        _assert_phrases(self, recovery, (FAILURE_CLASS_HEADING, "`reserve-class-correction`"))

    def test_claude_phase_execution_states_the_class_rule(self) -> None:
        references = CLAUDE_AUTOPILOT_SKILL.parent / "references"
        phase = _flat(references / "phase-execution.md")
        section = _section(phase, f"#### {FAILURE_CLASS_HEADING}", "#### Append Contract")
        self.assert_class_rules(section)
        recovery = _flat(references / "error-recovery.md")
        _assert_phrases(self, recovery, (FAILURE_CLASS_HEADING, "`reserve-class-correction`"))
        skill = _flat(CLAUDE_AUTOPILOT_SKILL)
        self.assertIn("`reserve-class-correction`", _section(skill, "## Error Recovery", "## References"))

    def test_ledger_reference_documents_the_class_request_shape(self) -> None:
        efficiency = _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "execution-efficiency.md")
        section = _section(efficiency, "- `reserve-class-correction`:", "- `begin-replan-epoch`:")
        for phrase in PHRASES["FailureClassApprovalSourceContractTests.test_ledger_reference_documents_the_class_request_shape#1"]:
            self.assertIn(phrase, section)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-autopilot-failure-class-approval"))
