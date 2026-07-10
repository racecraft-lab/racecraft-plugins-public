#!/usr/bin/env python3
"""Structural validation for codex-hooks.json (port of validate-codex-hooks.sh).

XPLAT-010 count-parity port (T022, US2). Python 3.11+ standard library only.
Asserts both the Codex hook file location and the manifest pointer, plus the
UserPromptSubmit shape with an intentionally empty command list. Every former
``_pass``/``_fail`` execution maps to one counted ``subTest`` unit; names
reproduced verbatim via ``subTest(msg=...)`` for a 1:1 baseline match.

Baseline: ``tests/speckit-pro/parity/bash-to-python/validate-codex-hooks-baseline.txt``
(TOTAL: 9).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

HOOKS_FILE = PLUGIN_ROOT / "codex-hooks.json"
MANIFEST_FILE = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"


def _field_exists(data: object, dotted: str) -> bool:
    """Mirror assert_json_field_exists: walk ``a.b.c`` keys without raising."""
    current = data
    try:
        for key in dotted.split("."):
            current = current[key]
    except (KeyError, TypeError, IndexError):
        return False
    return True


class ValidateCodexHooks(unittest.TestCase):
    def test_codex_hooks(self) -> None:
        with self.subTest(msg="codex-hooks.json exists"):
            self.assertTrue(HOOKS_FILE.is_file(), f"file not found: {HOOKS_FILE}")

        with self.subTest(msg=".codex-plugin/plugin.json declares hooks pointer"):
            hooks_ptr = ""
            if MANIFEST_FILE.is_file():
                try:
                    hooks_ptr = json.loads(MANIFEST_FILE.read_text(encoding="utf-8")).get("hooks", "")
                except (json.JSONDecodeError, OSError):
                    hooks_ptr = ""
                self.assertEqual(
                    "./codex-hooks.json", hooks_ptr,
                    f'manifest hooks field must be "./codex-hooks.json" (was: "{hooks_ptr}")',
                )
            else:
                self.fail(".codex-plugin/plugin.json missing")

        # Bash early-exits (uncounted) when the hooks file is absent; it exists here.
        if not HOOKS_FILE.is_file():
            return

        raw = HOOKS_FILE.read_text(encoding="utf-8")
        with self.subTest(msg="codex-hooks.json is valid JSON"):
            try:
                json.loads(raw)
            except json.JSONDecodeError as exc:
                self.fail(f"codex-hooks.json is not valid JSON: {exc}")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}

        with self.subTest(msg="has top-level hooks key"):
            self.assertTrue(_field_exists(data, "hooks"), "JSON field 'hooks' does not exist")
        with self.subTest(msg="UserPromptSubmit event exists under hooks"):
            self.assertTrue(_field_exists(data, "hooks.UserPromptSubmit"), "JSON field 'hooks.UserPromptSubmit' does not exist")

        with self.subTest(msg="NO SessionStart hook (would fire on every session — regression guard)"):
            has_session_start = "SessionStart" in (data.get("hooks", {}) if isinstance(data.get("hooks"), dict) else {})
            self.assertEqual("false", "true" if has_session_start else "false", "Codex hook must not register SessionStart")

        with self.subTest(msg="UserPromptSubmit has non-empty hooks array"):
            arr = data.get("hooks", {}).get("UserPromptSubmit")
            self.assertEqual("true", "true" if isinstance(arr, list) and len(arr) > 0 else "false", "UserPromptSubmit must have a non-empty array")

        with self.subTest(msg="Hook entry has hooks array"):
            try:
                entry = data["hooks"]["UserPromptSubmit"][0]
                ok = isinstance(entry, dict) and "hooks" in entry and isinstance(entry["hooks"], list)
            except (KeyError, TypeError, IndexError):
                ok = False
            self.assertEqual("true", "true" if ok else "false", "hook entry must have hooks array")

        with self.subTest(msg="Hook entry has an empty command list"):
            try:
                inner = data["hooks"]["UserPromptSubmit"][0]["hooks"]
                ok = isinstance(inner, list) and len(inner) == 0
            except (KeyError, TypeError, IndexError):
                ok = False
            self.assertEqual("true", "true" if ok else "false", "Codex plugin hook must not run a static interpreter command")


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateCodexHooks)


def main() -> int:
    return run_counted(build_suite(), label="validate-codex-hooks")


if __name__ == "__main__":
    raise SystemExit(main())
