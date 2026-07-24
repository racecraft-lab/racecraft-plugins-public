#!/usr/bin/env python3
"""Structural validation for hooks/hooks.json (port of validate-hooks.sh).

XPLAT-010 count-parity port (T027, US2). Python 3.11+ standard library only.
Asserts the plugin hook is scoped via ``UserPromptExpansion`` with a
plugin-scoping matcher and an intentionally empty command list — never a global
``SessionStart``/``UserPromptSubmit`` hook. Every former ``assert_*``/``_pass``/
``_fail`` execution maps to one counted ``subTest`` unit; names reproduced
verbatim via ``subTest(msg=...)`` for a 1:1 baseline match.

Baseline: ``tests/speckit-pro/parity/bash-to-python/validate-hooks-baseline.txt``
(TOTAL: 11).
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
from structural_helpers import field_exists as _field_exists  # noqa: E402
from test_result import run_counted  # noqa: E402

HOOKS_FILE = PLUGIN_ROOT / "hooks" / "hooks.json"


class ValidateHooks(unittest.TestCase):
    def test_hooks(self) -> None:
        with self.subTest(msg="hooks.json exists"):
            self.assertTrue(HOOKS_FILE.is_file(), f"file not found: {HOOKS_FILE}")

        # Bash sources CONTENT via `cat` after the existence check; it exists here.
        raw = HOOKS_FILE.read_text(encoding="utf-8") if HOOKS_FILE.is_file() else ""
        with self.subTest(msg="hooks.json is valid JSON"):
            try:
                json.loads(raw)
            except json.JSONDecodeError as exc:
                self.fail(f"hooks.json is not valid JSON: {exc}")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}

        with self.subTest(msg="has top-level hooks key"):
            self.assertTrue(_field_exists(data, "hooks"), "JSON field 'hooks' does not exist")
        with self.subTest(msg="UserPromptExpansion event exists under hooks"):
            self.assertTrue(
                _field_exists(data, "hooks.UserPromptExpansion"),
                "JSON field 'hooks.UserPromptExpansion' does not exist",
            )

        hooks_map = data.get("hooks", {}) if isinstance(data.get("hooks"), dict) else {}

        with self.subTest(msg="NO SessionStart hook (would fire on every session — regression guard)"):
            has_session_start = "SessionStart" in hooks_map
            self.assertEqual(
                "false", "true" if has_session_start else "false",
                "plugin must not register a global SessionStart hook",
            )
        with self.subTest(msg="NO UserPromptSubmit hook (would fire on every prompt — regression guard)"):
            has_user_prompt_submit = "UserPromptSubmit" in hooks_map
            self.assertEqual(
                "false", "true" if has_user_prompt_submit else "false",
                "plugin must not register a global UserPromptSubmit hook",
            )

        with self.subTest(msg="UserPromptExpansion is a non-empty array"):
            arr = hooks_map.get("UserPromptExpansion")
            ok = isinstance(arr, list) and len(arr) > 0
            self.assertEqual("true", "true" if ok else "false", "UserPromptExpansion must have a non-empty array")

        def _entry() -> object:
            try:
                return data["hooks"]["UserPromptExpansion"][0]
            except (KeyError, TypeError, IndexError):
                return None

        with self.subTest(msg="Hook entry has matcher field (scopes to plugin command_name)"):
            entry = _entry()
            ok = isinstance(entry, dict) and bool(entry.get("matcher"))
            self.assertEqual("true", "true" if ok else "false", "hook entry must have a non-empty matcher")

        with self.subTest(msg="Matcher contains plugin-scoping regex (speckit-pro: or speckit. or speckit- or grill-me)"):
            entry = _entry()
            matcher_val = entry.get("matcher", "") if isinstance(entry, dict) else ""
            ok = ("speckit-pro:" in matcher_val) or ("speckit" in matcher_val) or ("grill-me" in matcher_val)
            self.assertTrue(ok, f"matcher must scope to plugin commands (was: '{matcher_val}')")

        with self.subTest(msg="Hook entry has hooks array"):
            entry = _entry()
            ok = isinstance(entry, dict) and "hooks" in entry and isinstance(entry["hooks"], list)
            self.assertEqual("true", "true" if ok else "false", "hook entry must have hooks array")

        with self.subTest(msg="Hook entry has an empty command list"):
            try:
                inner = data["hooks"]["UserPromptExpansion"][0]["hooks"]
                ok = isinstance(inner, list) and len(inner) == 0
            except (KeyError, TypeError, IndexError):
                ok = False
            self.assertEqual(
                "true", "true" if ok else "false",
                "Claude plugin hook must not run a static interpreter command; skills own runner discovery",
            )


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateHooks)


def main() -> int:
    return run_counted(build_suite(), label="validate-hooks")


if __name__ == "__main__":
    raise SystemExit(main())
