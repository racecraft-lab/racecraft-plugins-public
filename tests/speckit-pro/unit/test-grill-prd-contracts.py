#!/usr/bin/env python3
"""Install and invocation-policy contracts for the Grill Me and PRD skills.

These checks prove packaging and explicit-invocation boundaries. They do not
claim that text instructions alone prove a model's interview behavior.
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
SKILLS = (
    PLUGIN_ROOT / "skills" / "grill-me",
    PLUGIN_ROOT / "skills" / "speckit-prd",
    PLUGIN_ROOT / "codex-skills" / "grill-me",
    PLUGIN_ROOT / "codex-skills" / "speckit-prd",
)
CODEX_SKILLS = tuple(skill for skill in SKILLS if "codex-skills" in skill.parts)
CAPABILITY_LINK = re.compile(
    r"\[[^]]+\]\((\$\{CLAUDE_PLUGIN_ROOT\}/|speckit-pro/)([^)#]+\.md)(?:#[^)]+)?\)"
)


def capability_targets(skill: Path, root: Path) -> list[Path]:
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    return [root / (link if prefix.startswith("${") else Path(prefix) / link) for prefix, link in CAPABILITY_LINK.findall(text)]


class GrillPrdContracts(unittest.TestCase):
    def test_capability_pointers_resolve_from_runtime_roots(self) -> None:
        for skill in SKILLS[:2]:
            with self.subTest(skill=skill.name):
                targets = capability_targets(skill, PLUGIN_ROOT)
                self.assertTrue(targets)
                self.assertTrue(all(target.is_file() for target in targets))
        for skill in CODEX_SKILLS:
            with self.subTest(skill=skill.name):
                targets = capability_targets(skill, REPO_ROOT)
                self.assertTrue(targets)
                self.assertTrue(all(target.is_file() for target in targets))

    def test_codex_skills_are_explicit_invocation_only(self) -> None:
        for skill in CODEX_SKILLS:
            with self.subTest(skill=skill.name):
                policy = (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")
                self.assertRegex(policy, r"(?m)^\s*allow_implicit_invocation:\s*false\s*$")

    def test_installed_payload_keeps_skill_references_resolvable(self) -> None:
        sys.path.insert(0, str(PLUGIN_ROOT))
        from speckit_pro_runner.gates.payloads import build_installed_plugin_payloads

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            build_installed_plugin_payloads(REPO_ROOT, output)
            for platform in ("claude", "codex"):
                for name in ("grill-me", "speckit-prd"):
                    with self.subTest(platform=platform, skill=name):
                        skill = output / platform / "speckit-pro" / "skills" / name
                        root = output / platform / "speckit-pro" if platform == "claude" else output / platform
                        targets = capability_targets(skill, root)
                        self.assertTrue(targets)
                        self.assertTrue(all(target.is_file() for target in targets))

    def test_claude_payload_removes_codex_selection_guard(self) -> None:
        sys.path.insert(0, str(PLUGIN_ROOT))
        from speckit_pro_runner.gates.payloads import build_installed_plugin_payloads

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            build_installed_plugin_payloads(REPO_ROOT, output)
            for name in ("grill-me", "speckit-prd"):
                text = (output / "claude" / "speckit-pro" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertNotIn("Codex Skill-Selection Guard", text)


if __name__ == "__main__":
    TEST_LIB = REPO_ROOT / "tests" / "speckit-pro" / "lib"
    sys.path.insert(0, str(TEST_LIB))
    from test_result import run_counted

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GrillPrdContracts)
    raise SystemExit(run_counted(suite, label="test-grill-prd-contracts"))
