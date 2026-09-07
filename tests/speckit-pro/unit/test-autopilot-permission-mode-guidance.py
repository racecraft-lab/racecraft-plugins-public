#!/usr/bin/env python3
"""Contracts for the autopilot's operator-facing permission-mode guidance.

Plugin-shipped agents inherit the parent session's permission mode, so the
autopilot's ability to run unattended is decided outside the plugin. Three
shipped Claude documents tell the operator about that: the skill's plugin-agent
caveat and the two references it links, ``plugin-limitations.md`` and
``prerequisites.md``. They are one instruction split across three files, and an
operator who reads only the skill must not get different advice from an
operator who follows its links.

These contracts hold the three in step. Trimming the guidance from one file
while the other two still carry it leaves the skill contradicting the reference
it points at, which is the drift these tests exist to catch.

"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
AUTOPILOT = REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot"

SKILL = AUTOPILOT / "SKILL.md"
PLUGIN_LIMITATIONS = AUTOPILOT / "references" / "plugin-limitations.md"
PREREQUISITES = AUTOPILOT / "references" / "prerequisites.md"
GUIDANCE_SURFACES = (SKILL, PLUGIN_LIMITATIONS, PREREQUISITES)

# The two Claude Code permission modes that let a parent session run the
# autopilot without prompting on every delegated edit.
PERMISSIVE_MODE_TOKENS = ("acceptEdits", "bypassPermissions")

# Frontmatter fields Claude Code silently ignores on plugin-shipped agents.
IGNORED_PLUGIN_AGENT_FIELDS = ("permissionMode", "hooks", "mcpServers")

PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

SHARED_LIB = TESTS_ROOT / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))

from test_result import run_counted  # noqa: E402


def body(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def carries_permissive_mode_guidance(text: str) -> bool:
    return any(token in text for token in PERMISSIVE_MODE_TOKENS)


class AutopilotPermissionModeGuidanceTests(unittest.TestCase):
    def test_permission_mode_guidance_is_consistent_across_skill_and_references(self) -> None:
        carried = {
            str(path.relative_to(REPO_ROOT)): carries_permissive_mode_guidance(body(path))
            for path in GUIDANCE_SURFACES
        }
        self.assertEqual(
            len(set(carried.values())),
            1,
            f"permission-mode guidance disagrees across shipped surfaces: {carried}",
        )

    def test_skill_links_both_references_that_repeat_the_guidance(self) -> None:
        skill_body = body(SKILL)
        for path in (PLUGIN_LIMITATIONS, PREREQUISITES):
            with self.subTest(reference=path.name):
                self.assertIn(f"references/{path.name}", skill_body)

    def test_skill_caveat_names_every_ignored_plugin_agent_field(self) -> None:
        skill_body = body(SKILL)
        missing = [field for field in IGNORED_PLUGIN_AGENT_FIELDS if f"`{field}`" not in skill_body]
        self.assertEqual(missing, [])

    def test_skill_that_mandates_a_runner_subprocess_documents_how_it_is_authorized(self) -> None:
        skill_body = body(SKILL)
        if 'Command("' not in skill_body:
            self.skipTest("skill no longer invokes the runner as a subprocess")
        self.assertTrue(
            carries_permissive_mode_guidance(skill_body),
            "skill mandates a runner subprocess but never tells the operator how to authorize it",
        )

    def test_reference_explains_that_allowed_tools_is_pre_approval(self) -> None:
        reference = body(PLUGIN_LIMITATIONS)
        for phrase in ("allowed-tools", "pre-approval"):
            with self.subTest(phrase=phrase):
                self.assertIn(
                    phrase,
                    reference,
                    "the skill leans on this reference for what allowed-tools decides, "
                    "but the reference never says it",
                )

    def test_a_declaration_token_blocks_under_the_named_guard_only(self) -> None:
        from speckit_pro_runner.gates import active_path_guard

        skill_path = "speckit-pro/skills/speckit-autopilot/SKILL.md"
        declaration = "allowed-tools: Read Edit Write Glob Grep Bash"

        self.assertEqual(
            active_path_guard.zero_bash_classification(
                skill_path,
                "bash",
                "Bash",
                declaration,
                [],
                declaration_line=declaration,
            ),
            "blocking_zero_bash",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                skill_path,
                "bash",
                "Bash",
                declaration,
                "repo",
            ),
            "source_checkout_helper",
        )


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AutopilotPermissionModeGuidanceTests)
    return run_counted(suite, label="test-autopilot-permission-mode-guidance")


if __name__ == "__main__":
    raise SystemExit(main())
