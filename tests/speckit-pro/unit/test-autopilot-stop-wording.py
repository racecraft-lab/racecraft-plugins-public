#!/usr/bin/env python3
"""Clean-finish and stop wording: finish asks only on a human stop, and agents return
blockers instead of stopping.

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

from guide_text import assert_guides_say
from autopilot_bookkeeping_support import (
    CLAUDE_AUTOPILOT_SKILL,
    CODEX_AUTOPILOT_SKILL,
    PHRASES,
    SKILL_DIR,
    _assert_absent,
    _assert_phrases,
    _flat,
)  # noqa: E402
from test_result import run_counted  # noqa: E402


CLEAN_FINISH_QUESTION = "Print the final report as plain text on `outcome=complete`"


BLOCKER_PHRASE = "return a blocker for consensus or deferral"


EXECUTORS = ("implement-executor", "analyze-executor", "clarify-executor", "checklist-executor", "phase-executor")


class CleanFinishAndStopWordingSourceContractTests(unittest.TestCase):
    """Finish asks only on a human stop; agents return blockers, never stop (issue 836)."""

    def test_clean_complete_run_prints_plain_text_without_a_question(self) -> None:
        for skill in (CLAUDE_AUTOPILOT_SKILL, CODEX_AUTOPILOT_SKILL):
            text = _flat(skill)
            _assert_phrases(self, text, (CLEAN_FINISH_QUESTION, "The run never pauses to ask."))
            _assert_absent(self, text, ("Either way, make one consolidated", "Either way, make the one consolidated"))
        codex_phase = _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / "phase-execution.md")
        _assert_phrases(self, codex_phase, (CLEAN_FINISH_QUESTION, "The run never pauses to ask"))

    def test_executors_return_a_blocker_instead_of_escalating_or_deciding(self) -> None:
        plugin = REPO_ROOT / "speckit-pro"
        stale_by_host = (
            ("agents", ".md", PHRASES["CleanFinishAndStopWordingSourceContractTests.test_claude_executors_return_a_blocker_instead_of_escalating#1"]),
            ("codex-agents", ".toml", ("let the orchestrator",)),
        )
        for folder, suffix, stale in stale_by_host:
            for name in EXECUTORS:
                with self.subTest(folder=folder, name=name):
                    text = _flat(plugin / folder / f"{name}{suffix}")
                    self.assertIn(BLOCKER_PHRASE, text)
                    _assert_absent(self, text, stale)


# (file, phrases the file carries, phrases it no longer carries)
SINGLE_FILE_PINS = (
    ((SKILL_DIR + "references/phase-execution.md", "claude"),
     ("follows the Failure Escalation Protocol and defers",), ("configured gate-failure/escalation path",)),
    ((SKILL_DIR + "SKILL.md", "claude"),
     ("warn the operator once and route gate and consensus dispatches to the strongest available tier",),
     ("small-tier", "stop and ask the operator to switch")),
    ((SKILL_DIR + "SKILL.md", "codex"),
     ("Route the ambiguity to Clarify consensus, and defer it when consensus cannot settle it",),
     ("Fail the gate, surface the ambiguity, and stop",)),
    ("codex-agents/phase-executor.toml",
     (BLOCKER_PHRASE,), ("surface the condition to the orchestrator",)),
    (SKILL_DIR + "references/stack-manager.md",
     ("Preserve packet metadata, and draft status until finalization", "at its own head", "bottom-up",
      "re-verify every affected head"), ()),
)


class SingleFilePinTests(unittest.TestCase):
    def test_each_file_carries_its_pinned_wording_and_none_of_the_stale_wording(self) -> None:
        for name, present, absent in SINGLE_FILE_PINS:
            assert_guides_say(self, (name,), present, absent)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-autopilot-stop-wording"))
