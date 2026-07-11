#!/usr/bin/env python3
"""Structural validation for all Claude agent files (port of validate-agents.sh).

XPLAT-010 count-parity port (T018, US2). Python 3.11+ standard library only, no
new runtime dependency. Every former ``assert_*`` / ``_pass`` / ``_fail``
execution maps to exactly one counted ``subTest`` unit; each bash check name is
reproduced verbatim via ``subTest(msg=...)`` so the ordered inventory matches the
committed baseline 1:1.

Baseline: ``tests/speckit-pro/parity/xplat-010/validate-agents-baseline.txt``
(TOTAL: 104). Run standalone::

    python3 tests/speckit-pro/layer1-structural/validate-agents.py

prints ``validate-agents: {passed}/{total} passed`` (exit 0 iff all pass).
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

AGENTS_DIR = PLUGIN_ROOT / "agents"
AGENTS = (
    "phase-executor",
    "clarify-executor",
    "checklist-executor",
    "analyze-executor",
    "implement-executor",
    "codebase-analyst",
    "spec-context-analyst",
    "domain-researcher",
    "gate-validator",
    "consensus-synthesizer",
)

NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-]{2,49}$")
MODEL_RE = re.compile(r"^(opus|sonnet|haiku|inherit)$")


def _frontmatter(lines: list[str]) -> str:
    """Lines between the first and second ``---`` fence (exclusive)."""
    out: list[str] = []
    fences = 0
    for line in lines:
        if line == "---":
            fences += 1
            if fences == 1:
                continue
            if fences == 2:
                break
        elif fences == 1:
            out.append(line)
    return "\n".join(out)


def _body(lines: list[str]) -> str:
    """Everything after the second ``---`` fence."""
    out: list[str] = []
    fences = 0
    found = False
    for line in lines:
        if line == "---":
            fences += 1
            if fences == 2:
                found = True
                continue
        if found:
            out.append(line)
    return "\n".join(out)


def _field(frontmatter: str, key: str) -> str:
    """First ``key: value`` in the frontmatter, quote-stripped (mirrors sed/tr)."""
    for line in frontmatter.split("\n"):
        if line.startswith(f"{key}:"):
            value = re.sub(rf"^{key}:[ \t]*", "", line)
            return value.replace('"', "").replace("'", "")
    return ""


def _nonblank(text: str) -> str:
    return "\n".join(line for line in text.split("\n") if line.strip())


class ValidateAgents(unittest.TestCase):
    def test_agents(self) -> None:
        for agent in AGENTS:
            agent_file = AGENTS_DIR / f"{agent}.md"

            with self.subTest(msg=f"{agent}: file exists"):
                self.assertTrue(agent_file.is_file(), f"file not found: {agent_file}")
            if not agent_file.is_file():
                continue

            lines = agent_file.read_text(encoding="utf-8").splitlines()
            first_line = lines[0] if lines else ""

            with self.subTest(msg=f"{agent}: starts with --- (YAML frontmatter)"):
                self.assertEqual("---", first_line, "first line must be ---")

            with self.subTest(msg=f"{agent}: has closing ---"):
                fence_count = sum(1 for line in lines if line == "---")
                self.assertGreaterEqual(
                    fence_count, 2, f"expected at least 2 '---' lines, found {fence_count}"
                )

            frontmatter = _frontmatter(lines)

            with self.subTest(msg=f"{agent}: has name: field"):
                self.assertIn("name:", frontmatter)

            name_val = _field(frontmatter, "name")
            with self.subTest(
                msg=f"{agent}: name is valid format (alphanumeric + hyphens, 3-50 chars)"
            ):
                self.assertRegex(name_val, NAME_RE, f"name '{name_val}' must be 3-50 chars")

            with self.subTest(msg=f"{agent}: has description: field"):
                self.assertIn("description:", frontmatter)

            with self.subTest(msg=f"{agent}: has model: field"):
                self.assertIn("model:", frontmatter)

            model_val = _field(frontmatter, "model")
            with self.subTest(msg=f"{agent}: model is valid (opus|sonnet|haiku|inherit)"):
                self.assertRegex(model_val, MODEL_RE, "model must be opus, sonnet, haiku, or inherit")

            body = _body(lines)
            body_trimmed = _nonblank(body)
            with self.subTest(msg=f"{agent}: system prompt body exists (after frontmatter)"):
                self.assertTrue(body_trimmed, "no system prompt body after frontmatter")

            with self.subTest(msg=f"{agent}: system prompt length > 20 chars"):
                self.assertGreater(
                    len(body_trimmed), 20, f"system prompt is only {len(body_trimmed)} chars (need > 20)"
                )

            if agent == "clarify-executor":
                with self.subTest(msg="clarify-executor: returns questions to parent"):
                    self.assertIn("## Clarify Question Set", body)
                with self.subTest(msg="clarify-executor: does not claim to be the user"):
                    self.assertNotIn("YOU ARE THE USER", body)
                with self.subTest(msg="clarify-executor: does not forbid returning questions"):
                    self.assertNotIn("Do NOT present questions back", body)
                with self.subTest(msg="clarify-executor: does not invoke interactive clarify skill"):
                    self.assertNotIn("Use the Skill tool to run", body)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateAgents)


def main() -> int:
    return run_counted(build_suite(), label="validate-agents")


if __name__ == "__main__":
    raise SystemExit(main())
