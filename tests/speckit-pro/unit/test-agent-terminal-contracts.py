#!/usr/bin/env python3
"""Cross-client regression gates for terminal agent result boundaries."""

from __future__ import annotations

import re
import sys
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402


CLAUDE_DIR = REPO_ROOT / "speckit-pro" / "agents"
CODEX_DIR = REPO_ROOT / "speckit-pro" / "codex-agents"
TERMINAL_RESULT_ROLES = (
    "phase-executor",
    "implement-executor",
    "codebase-analyst",
    "spec-context-analyst",
    "domain-researcher",
)
PROTOCOL_READERS = ("consensus-synthesizer", "analyze-executor", "checklist-executor")
NO_SPAWN_ROLES = (
    "clarify-executor",
    "formal-model-author",
    "codebase-analyst",
    "spec-context-analyst",
    "domain-researcher",
)


def claude_body(name: str) -> str:
    text = (CLAUDE_DIR / f"{name}.md").read_text(encoding="utf-8")
    return text.split("\n---\n", 1)[1]


def codex_policy(name: str) -> dict:
    return tomllib.loads((CODEX_DIR / f"{name}.toml").read_text(encoding="utf-8"))


def terminal_deliverable(text: str) -> str:
    match = re.search(
        r"^### Terminal Deliverable\n(.*?)(?=^#{2,3} |^<hard_constraints>|\Z)",
        text,
        re.S | re.M,
    )
    if match is None:
        raise AssertionError("missing Terminal Deliverable section")
    return match.group(1)


class AgentTerminalContractTests(unittest.TestCase):
    def test_codex_terminal_result_contracts_match_claude(self) -> None:
        for name in TERMINAL_RESULT_ROLES:
            with self.subTest(agent=name):
                instructions = codex_policy(name)["developer_instructions"]
                self.assertEqual(
                    terminal_deliverable(instructions),
                    terminal_deliverable(claude_body(name)),
                )

    def test_terminal_roles_explicitly_forbid_child_dispatch(self) -> None:
        for name in NO_SPAWN_ROLES:
            with self.subTest(agent=name):
                self.assertIn(
                    "Do NOT spawn subagents or create teams.",
                    codex_policy(name)["developer_instructions"],
                )

    def test_protocol_readers_use_the_path_the_orchestrator_passes(self) -> None:
        # A path relative to the agent file never resolves from the consumer
        # repository, so the agent searched the plugin cache and could read a
        # stale version. The orchestrator passes the active path instead, and
        # the agent reports the path it read so the parent can check it.
        for name in PROTOCOL_READERS:
            body = claude_body(name)
            flat = " ".join(body.split())
            with self.subTest(agent=name):
                self.assertNotIn("../skills/speckit-autopilot/references/", body)
                self.assertIn("`Protocol:` line", flat)
                self.assertIn("never search the plugin cache", flat)
                self.assertIn("**Protocol:** <", body)
        self.assertIn(
            "**Protocol:** <the path copied from the prompt's `Protocol:` line>",
            codex_policy("consensus-synthesizer")["developer_instructions"],
        )
        for name in ("analyze-executor", "checklist-executor"):
            instructions = " ".join(codex_policy(name)["developer_instructions"].split())
            with self.subTest(codex=name):
                self.assertIn("`Protocol:` line", instructions)
                self.assertIn("**Protocol:** <", codex_policy(name)["developer_instructions"])

    def test_consensus_synthesizer_is_read_only_terminal_and_evidence_closed(self) -> None:
        policy = codex_policy("consensus-synthesizer")
        instructions = policy["developer_instructions"]
        self.assertEqual(policy["sandbox_mode"], "read-only")
        for phrase in (
            "without editing artifacts, spawning agents, conducting interviews, using",
            "or gathering new evidence",
            "Add no analysis, arguments, or evidence beyond",
            "The parent alone owns workflow state",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, instructions)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AgentTerminalContractTests)
    return run_counted(suite, label="test-agent-terminal-contracts")


if __name__ == "__main__":
    raise SystemExit(main())
