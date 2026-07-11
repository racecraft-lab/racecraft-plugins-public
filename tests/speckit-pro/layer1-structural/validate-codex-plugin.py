#!/usr/bin/env python3
"""Structural validation for .codex-plugin/plugin.json (port of validate-codex-plugin.sh).

XPLAT-010 count-parity port (T025, US2). Python 3.11+ standard library only.
Asserts the Codex plugin manifest exists, is valid JSON, uses scaffold naming,
declares the required interface/skills fields and required Codex skill
directories, and that its version matches ``.claude-plugin/plugin.json``. Every
former ``assert_*``/``_pass``/``_fail`` execution maps to one counted ``subTest``
unit; names reproduced verbatim via ``subTest(msg=...)`` for a 1:1 baseline match.

Baseline: ``tests/speckit-pro/parity/xplat-010/validate-codex-plugin-baseline.txt``
(TOTAL: 33).
"""

from __future__ import annotations

import json
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

CODEX_JSON = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
CLAUDE_JSON = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"

# Fixed iteration order (mirrors the bash REQUIRED_SKILLS array, not a glob).
REQUIRED_SKILLS = (
    "speckit-archive-cleanup",
    "speckit-autopilot",
    "speckit-coach",
    "speckit-scaffold-spec",
    "speckit-status",
    "speckit-resolve-pr",
    "install",
    "grill-me",
    "speckit-prd",
)

SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def _field_exists(data: object, dotted: str) -> bool:
    """Mirror assert_json_field_exists: walk ``a.b.c`` keys without raising."""
    current = data
    try:
        for key in dotted.split("."):
            current = current[key]
    except (KeyError, TypeError, IndexError):
        return False
    return True


def _nested(data: object, *keys: object) -> object:
    current = data
    try:
        for key in keys:
            current = current[key]  # type: ignore[index]
    except (KeyError, TypeError, IndexError):
        return None
    return current


class ValidateCodexPlugin(unittest.TestCase):
    def test_codex_plugin(self) -> None:
        with self.subTest(msg=".codex-plugin/plugin.json exists"):
            self.assertTrue(CODEX_JSON.is_file(), f"file not found: {CODEX_JSON}")

        raw = CODEX_JSON.read_text(encoding="utf-8") if CODEX_JSON.is_file() else ""
        with self.subTest(msg=".codex-plugin/plugin.json is valid JSON"):
            try:
                json.loads(raw)
            except json.JSONDecodeError:
                self.fail(".codex-plugin/plugin.json is not valid JSON")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}

        with self.subTest(msg="name field exists"):
            self.assertTrue(_field_exists(data, "name"), "JSON field 'name' does not exist")
        with self.subTest(msg="name matches speckit-pro"):
            name_val = _nested(data, "name")
            self.assertEqual("speckit-pro", str(name_val) if name_val is not None else "", "field 'name' mismatch")

        with self.subTest(msg="version is semver X.Y.Z"):
            version_val = _nested(data, "version")
            self.assertRegex(str(version_val) if version_val is not None else "", SEMVER_RE, "version must be X.Y.Z")

        desc_val = _nested(data, "description")
        desc = str(desc_val) if desc_val is not None else ""
        with self.subTest(msg="description is non-empty"):
            self.assertTrue(desc, "description is empty")
        with self.subTest(msg="description uses scaffold naming for spec preparation"):
            self.assertTrue(
                "spec scaffolding" in desc and "setup" not in desc,
                "expected Codex plugin description to use scaffolding terminology (no 'setup')",
            )

        with self.subTest(msg="homepage field exists"):
            self.assertTrue(_field_exists(data, "homepage"), "JSON field 'homepage' does not exist")
        with self.subTest(msg="skills field equals ./codex-skills/"):
            skills_val = _nested(data, "skills")
            self.assertEqual("./codex-skills/", str(skills_val) if skills_val is not None else "", "field 'skills' mismatch")

        with self.subTest(msg="interface.displayName exists"):
            self.assertTrue(_field_exists(data, "interface.displayName"), "JSON field 'interface.displayName' does not exist")
        with self.subTest(msg="interface.category exists"):
            self.assertTrue(_field_exists(data, "interface.category"), "JSON field 'interface.category' does not exist")
        with self.subTest(msg="interface.defaultPrompt exists"):
            self.assertTrue(_field_exists(data, "interface.defaultPrompt"), "JSON field 'interface.defaultPrompt' does not exist")

        with self.subTest(msg="interface.defaultPrompt uses scaffold naming for spec preparation"):
            dp_list = _nested(data, "interface", "defaultPrompt")
            default_prompts = "\n".join(dp_list) if isinstance(dp_list, list) else ""
            self.assertTrue(
                "scaffold a spec worktree" in default_prompts and "set up a spec worktree" not in default_prompts,
                "expected Codex default prompt to say scaffold a spec worktree",
            )

        with self.subTest(msg="codex-skills/ directory exists"):
            self.assertTrue((PLUGIN_ROOT / "codex-skills").is_dir(), f"codex-skills/ directory not found at {PLUGIN_ROOT / 'codex-skills'}")

        for skill in REQUIRED_SKILLS:
            with self.subTest(msg=f"codex-skills/{skill}/ directory exists"):
                self.assertTrue((PLUGIN_ROOT / "codex-skills" / skill).is_dir(), f"codex-skills/{skill}/ directory not found")
            with self.subTest(msg=f"codex-skills/{skill}/SKILL.md exists"):
                self.assertTrue((PLUGIN_ROOT / "codex-skills" / skill / "SKILL.md").is_file(), f"file not found: codex-skills/{skill}/SKILL.md")

        with self.subTest(msg="version matches .claude-plugin/plugin.json"):
            if CLAUDE_JSON.is_file():
                try:
                    claude_version = json.loads(CLAUDE_JSON.read_text(encoding="utf-8")).get("version")
                except (json.JSONDecodeError, OSError):
                    claude_version = None
                codex_version = _nested(data, "version")
                self.assertEqual(
                    claude_version, codex_version,
                    f"version mismatch: .claude-plugin/plugin.json='{claude_version}', .codex-plugin/plugin.json='{codex_version}'",
                )
            else:
                self.fail(".claude-plugin/plugin.json not found — cannot compare versions")


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateCodexPlugin)


def main() -> int:
    return run_counted(build_suite(), label="validate-codex-plugin")


if __name__ == "__main__":
    raise SystemExit(main())
