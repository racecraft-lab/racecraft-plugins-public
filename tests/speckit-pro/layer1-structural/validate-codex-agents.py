#!/usr/bin/env python3
"""Structural validation for bundled Codex custom subagent TOML templates.

Port of validate-codex-agents.sh (XPLAT-010 count-parity port, T021, US2). Python
3.11+ standard library only. Every former ``assert_*``/``_pass``/``_fail``
execution maps to one counted ``subTest`` unit; bash check names reproduced
verbatim via ``subTest(msg=...)`` for a 1:1 baseline match.

Baseline: ``tests/speckit-pro/parity/bash-to-python/validate-codex-agents-baseline.txt``
(TOTAL: 148).
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

CODEX_AGENTS_DIR = PLUGIN_ROOT / "codex-agents"
CC_AGENTS_DIR = PLUGIN_ROOT / "agents"

AGENTS = (
    "autopilot-fast-helper",
    "clarify-executor",
    "checklist-executor",
    "analyze-executor",
    "implement-executor",
    "phase-executor",
    "codebase-analyst",
    "spec-context-analyst",
    "domain-researcher",
)

CC_ONLY_FIELDS = ("tools", "disallowedTools", "permissionMode", "color", "maxTurns", "background", "effort")

MODEL_RE = re.compile(r"^(gpt-5\.5|gpt-5\.4|gpt-5\.4-mini|gpt-5\.3-codex|gpt-5\.3-codex-spark)$")
EFFORT_RE = re.compile(r"^(minimal|low|medium|high|xhigh)$")
SANDBOX_RE = re.compile(r"^(read-only|workspace-write)$")


def _extract_toml_string(text: str, field: str) -> str:
    """First ``field = "value"`` line's value (mirrors the sed -n extractor)."""
    match = re.search(rf'^{re.escape(field)} = "([^"]*)"$', text, re.MULTILINE)
    return match.group(1) if match else ""


def _extract_developer_instructions(text: str) -> str:
    """Lines between ``developer_instructions = \"\"\"`` and the closing ``\"\"\"``."""
    out: list[str] = []
    capture = False
    for line in text.split("\n"):
        if not capture and line.startswith('developer_instructions = """'):
            capture = True
            continue
        if capture and line == '"""':
            break
        if capture:
            out.append(line)
    return "\n".join(out)


def _nonblank(text: str) -> str:
    return "\n".join(line for line in text.split("\n") if line.strip())


def _has_field_line(text: str, field: str) -> bool:
    return re.search(rf"^{re.escape(field)}[ \t]*=", text, re.MULTILINE) is not None


class ValidateCodexAgents(unittest.TestCase):
    def test_codex_agents(self) -> None:
        for agent in AGENTS:
            agent_file = CODEX_AGENTS_DIR / f"{agent}.toml"

            with self.subTest(msg=f"{agent}: TOML file exists"):
                self.assertTrue(agent_file.is_file(), f"file not found: {agent_file}")
            with self.subTest(msg=f"{agent}: legacy Markdown file removed"):
                self.assertFalse((CODEX_AGENTS_DIR / f"{agent}.md").is_file(), "legacy .md must be removed")
            if not agent_file.is_file():
                continue

            content = agent_file.read_text(encoding="utf-8")

            with self.subTest(msg=f"{agent}: has name field"):
                self.assertIn('name = "', content)
            name_val = _extract_toml_string(content, "name")
            with self.subTest(msg=f"{agent}: name matches filename"):
                self.assertEqual(agent, name_val, "name field must match filename stem")

            with self.subTest(msg=f"{agent}: has description field"):
                self.assertIn('description = "', content)
            with self.subTest(msg=f"{agent}: has model field"):
                self.assertIn('model = "', content)

            model_val = _extract_toml_string(content, "model")
            with self.subTest(msg=f"{agent}: model is an officially documented Codex GPT model"):
                self.assertRegex(model_val, MODEL_RE, "model must be an officially documented Codex GPT model")

            if model_val == "gpt-5.3-codex-spark":
                with self.subTest(
                    msg=f"{agent}: model_reasoning_effort field is absent (Spark does not support reasoning fields)"
                ):
                    self.assertNotIn('model_reasoning_effort = "', content)
                effort_val = ""
            else:
                with self.subTest(msg=f"{agent}: has model_reasoning_effort field"):
                    self.assertIn('model_reasoning_effort = "', content)
                effort_val = _extract_toml_string(content, "model_reasoning_effort")
                with self.subTest(msg=f"{agent}: reasoning effort uses supported values"):
                    self.assertRegex(effort_val, EFFORT_RE, "reasoning effort must be minimal, low, medium, high, or xhigh")

            with self.subTest(msg=f"{agent}: has sandbox_mode field"):
                self.assertIn('sandbox_mode = "', content)
            sandbox_val = _extract_toml_string(content, "sandbox_mode")
            with self.subTest(msg=f"{agent}: sandbox_mode uses supported values"):
                self.assertRegex(sandbox_val, SANDBOX_RE)

            with self.subTest(msg=f"{agent}: has developer_instructions block"):
                self.assertIn('developer_instructions = """', content)
            instructions = _extract_developer_instructions(content)
            with self.subTest(msg=f"{agent}: developer_instructions body is non-empty"):
                self.assertTrue(_nonblank(instructions), "developer_instructions block is empty")

            with self.subTest(msg=f"{agent}: no Claude Code-only fields"):
                bad = [field for field in CC_ONLY_FIELDS if _has_field_line(content, field)]
                self.assertFalse(bad, f"Claude Code-only fields found: {' '.join(bad)}")

            if agent != "autopilot-fast-helper":
                with self.subTest(msg=f"{agent}: corresponding Claude agent exists in agents/"):
                    self.assertTrue((CC_AGENTS_DIR / f"{agent}.md").is_file(), f"missing Claude twin: {agent}.md")
            else:
                with self.subTest(msg="autopilot-fast-helper: intentionally Codex-only"):
                    self.assertFalse(
                        (CC_AGENTS_DIR / "autopilot-fast-helper.md").is_file(),
                        "autopilot-fast-helper should remain Codex-only; do not add a Claude twin",
                    )

            self._check_profile(agent, model_val, effort_val, sandbox_val, instructions)

        with self.subTest(msg="codex-agents/openai.yaml removed"):
            self.assertFalse((CODEX_AGENTS_DIR / "openai.yaml").is_file(), "openai.yaml must be removed")
        with self.subTest(msg="codex-agents directory contains TOML files only"):
            non_toml = [p for p in CODEX_AGENTS_DIR.iterdir() if p.is_file() and p.suffix != ".toml"]
            self.assertEqual(0, len(non_toml), "only standalone TOML custom-agent files are allowed")

    def _check_profile(self, agent: str, model_val: str, effort_val: str, sandbox_val: str, instructions: str) -> None:
        if agent == "autopilot-fast-helper":
            with self.subTest(
                msg="autopilot-fast-helper: uses Spark read-only (no reasoning effort — Spark does not support reasoning fields per OpenAI docs)"
            ):
                self.assertTrue(
                    model_val == "gpt-5.3-codex-spark" and effort_val == "" and sandbox_val == "read-only",
                    f"expected gpt-5.3-codex-spark / no-effort-field / read-only, got {model_val} / {effort_val} / {sandbox_val}",
                )
        elif agent == "clarify-executor":
            with self.subTest(msg="clarify-executor: uses xhigh GPT-5.5 read-only question-prep profile"):
                self.assertTrue(
                    model_val == "gpt-5.5" and effort_val == "xhigh" and sandbox_val == "read-only",
                    f"expected gpt-5.5 / xhigh / read-only, got {model_val} / {effort_val} / {sandbox_val}",
                )
            with self.subTest(msg="clarify-executor: returns questions to parent"):
                self.assertIn("## Clarify Question Set", instructions)
            with self.subTest(msg="clarify-executor: does not claim to be the user"):
                self.assertNotIn("YOU ARE THE USER", instructions)
            with self.subTest(msg="clarify-executor: does not invoke interactive clarify skill"):
                self.assertNotIn("Run `$speckit-clarify`", instructions)
        elif agent in ("phase-executor", "checklist-executor", "analyze-executor"):
            with self.subTest(msg=f"{agent}: uses xhigh GPT-5.5 executor profile"):
                self.assertTrue(
                    model_val == "gpt-5.5" and effort_val == "xhigh" and sandbox_val == "workspace-write",
                    f"expected gpt-5.5 / xhigh / workspace-write, got {model_val} / {effort_val} / {sandbox_val}",
                )
        elif agent == "implement-executor":
            with self.subTest(msg="implement-executor: uses xhigh GPT-5.5 TDD profile"):
                self.assertTrue(
                    model_val == "gpt-5.5" and effort_val == "xhigh" and sandbox_val == "workspace-write",
                    f"expected gpt-5.5 / xhigh / workspace-write, got {model_val} / {effort_val} / {sandbox_val}",
                )
        elif agent in ("codebase-analyst", "spec-context-analyst"):
            with self.subTest(msg=f"{agent}: uses GPT-5.5 read-only consensus profile (L6-validated effort)"):
                self.assertTrue(
                    model_val == "gpt-5.5" and effort_val in ("low", "xhigh") and sandbox_val == "read-only",
                    f"expected gpt-5.5 / low|xhigh / read-only, got {model_val} / {effort_val} / {sandbox_val}",
                )
        elif agent == "domain-researcher":
            with self.subTest(
                msg="domain-researcher: uses xhigh read-only GPT-5.5 consensus profile (L6 has not validated lower effort)"
            ):
                self.assertTrue(
                    model_val == "gpt-5.5" and effort_val == "xhigh" and sandbox_val == "read-only",
                    f"expected gpt-5.5 / xhigh / read-only, got {model_val} / {effort_val} / {sandbox_val}",
                )


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateCodexAgents)


def main() -> int:
    return run_counted(build_suite(), label="validate-codex-agents")


if __name__ == "__main__":
    raise SystemExit(main())
