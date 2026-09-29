#!/usr/bin/env python3
"""Plugin update mid-run: record, re-resolve, continue.

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


PLUGIN_DRIFT_HEADING = "Plugin Update Mid-Run: Record, Re-resolve, Continue"


class MidRunPluginDriftSourceContractTests(unittest.TestCase):
    """A plugin update during a run is recorded, never a restart stop (issue 767)."""

    def assert_drift_rules(self, section: str) -> None:
        for phrase in PHRASES["MidRunPluginDriftSourceContractTests.assert_drift_rules#1"]:
            self.assertIn(phrase, section)

    def test_codex_phase_seven_records_drift_and_continues(self) -> None:
        section = _section_after(
            self, _codex_reference("phase-execution-codex.md"), f"### {BLOCKED_ACTION_HEADING}",
            f"### {PLUGIN_DRIFT_HEADING}", "## PR Packet and Body Boundary",
        )
        self.assert_drift_rules(section)
        # Codex 0.158 re-reads a registered role file at spawn time, but the
        # role list is fixed when the session starts.
        _assert_phrases(self, section, ("next `spawn_agent`", "when the session starts"))

    def test_codex_restart_rule_is_scoped_to_setup_or_run_start(self) -> None:
        skill = _flat(CODEX_AUTOPILOT_SKILL)
        prerequisites = _codex_reference("prerequisites-codex.md")
        recovery = _codex_reference("error-recovery-codex.md")
        for text in (skill, prerequisites):
            _assert_absent(self, text, (
                "cannot reload changed custom agents safely",
                "cannot load refreshed custom-agent definitions safely",
            ))
        guard = _section(skill, "Do not translate this skill into Claude-only", "## Prerequisites — Model")
        mapping = _section(skill, "Concrete Codex mapping:", "Spawn each agent with")
        availability = _section(skill, "**Step 0.10: Codex Agent Availability Check**", "**Step 0.10b")
        preflight = _section(prerequisites, "### 0.10 Codex Agent Availability Check", "### 0.10b")
        for text in (guard, mapping, availability, preflight):
            _assert_phrases(self, text, ("at setup or run start", PLUGIN_DRIFT_HEADING))
        self.assertIn("next `spawn_agent`", preflight)
        _assert_phrases(self, recovery, ("Plugin updated mid-run", PLUGIN_DRIFT_HEADING))

    def test_claude_phase_seven_mirrors_the_drift_rule(self) -> None:
        section = _section_after(
            self, _claude_reference("phase-execution.md"), f"#### {BLOCKED_ACTION_HEADING}",
            f"#### {PLUGIN_DRIFT_HEADING}", "#### Append Contract",
        )
        self.assert_drift_rules(section)
        _assert_phrases(self, section, ("`validate-agent-install`", "`/reload-plugins`"))
        install_check = _section(_claude_reference("prerequisites.md"), "If the check fails, STOP.", "## Step 0.0c")
        _assert_phrases(self, install_check, ("at setup or run start", PLUGIN_DRIFT_HEADING))
        _assert_phrases(self, _claude_reference("error-recovery.md"), ("Plugin updated mid-run", PLUGIN_DRIFT_HEADING))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-autopilot-plugin-drift"))
