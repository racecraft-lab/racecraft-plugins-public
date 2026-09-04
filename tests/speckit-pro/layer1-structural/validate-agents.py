#!/usr/bin/env python3
"""Validate Claude agent definitions."""

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
from structural_helpers import body as _body  # noqa: E402
from structural_helpers import frontmatter as _frontmatter  # noqa: E402
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
    "consensus-synthesizer",
    "artifact-author",
    "uat-runbook-author",
    "sweep-classifier",
    "sweep-analyst",
)

PLUGIN_AGENT_FIELDS = {
    "name",
    "description",
    "model",
    "effort",
    "maxTurns",
    "tools",
    "disallowedTools",
    "skills",
    "memory",
    "background",
    "isolation",
    "color",
}
UNSUPPORTED_PLUGIN_AGENT_FIELDS = {
    "hooks",
    "mcpServers",
    "permissionMode",
    "initialPrompt",
    "experimental.cacheTtl",
}
MEMORY_POLICY = {
    "codebase-analyst": "local",
    "implement-executor": "local",
    "spec-context-analyst": "local",
}

NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-]{2,49}$")
MODEL_RE = re.compile(r"^(opus|sonnet|haiku|inherit)$")


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
        with self.subTest(msg="Claude agent roster exactly matches all shipped source definitions"):
            discovered = {path.stem for path in AGENTS_DIR.glob("*.md")}
            self.assertEqual(set(AGENTS), discovered)

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

            declared_fields = {
                line.split(":", 1)[0]
                for line in frontmatter.splitlines()
                if line and not line[0].isspace() and ":" in line
            }
            with self.subTest(msg=f"{agent}: uses only supported plugin-agent frontmatter fields"):
                self.assertFalse(declared_fields - PLUGIN_AGENT_FIELDS)
                self.assertFalse(declared_fields & UNSUPPORTED_PLUGIN_AGENT_FIELDS)

            memory_val = _field(frontmatter, "memory")
            with self.subTest(msg=f"{agent}: memory scope matches the curated persistence policy"):
                self.assertEqual(MEMORY_POLICY.get(agent, ""), memory_val)

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

            if agent in MEMORY_POLICY:
                with self.subTest(msg=f"{agent}: explicitly consults current inputs before memory"):
                    self.assertIn("Current task inputs always override memory", body)
                with self.subTest(msg=f"{agent}: curates only verified durable memory"):
                    self.assertRegex(body, r"verified\s+durable project knowledge")
                with self.subTest(msg=f"{agent}: forbids sensitive and ephemeral memory content"):
                    self.assertIn("Never store secrets", body)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateAgents)


def main() -> int:
    return run_counted(build_suite(), label="validate-agents")


if __name__ == "__main__":
    raise SystemExit(main())
