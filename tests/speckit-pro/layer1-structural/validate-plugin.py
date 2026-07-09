#!/usr/bin/env python3
"""Structural validation for .claude-plugin/plugin.json (port of validate-plugin.sh).

XPLAT-010 count-parity port (T031, US2). Python 3.11+ standard library only.
Asserts the shipped Claude plugin manifest exists, is valid JSON, and carries the
required identity fields (kebab-case ``name`` == ``speckit-pro``, semver
``version``, non-empty ``description``, present ``author``). Every former
``assert_*``/``_pass``/``_fail`` execution maps to one counted ``subTest`` unit;
names reproduced verbatim via ``subTest(msg=...)`` for a 1:1 baseline match.

Baseline: ``tests/speckit-pro/parity/xplat-010/validate-plugin-baseline.txt``
(TOTAL: 8).
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

PLUGIN_JSON = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"

KEBAB_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def _field_str(data: object, key: str) -> str:
    """Mirror the bash `python3 -c ... 2>/dev/null` field read: value as a string,
    empty when the key is absent or the document is not a mapping."""
    if isinstance(data, dict) and key in data:
        return str(data[key])
    return ""


class ValidatePlugin(unittest.TestCase):
    def test_plugin_manifest(self) -> None:
        with self.subTest(msg="plugin.json exists"):
            self.assertTrue(PLUGIN_JSON.is_file(), f"file not found: {PLUGIN_JSON}")

        raw = PLUGIN_JSON.read_text(encoding="utf-8") if PLUGIN_JSON.is_file() else ""
        with self.subTest(msg="plugin.json is valid JSON"):
            try:
                json.loads(raw)
            except json.JSONDecodeError as exc:
                self.fail(f"plugin.json is not valid JSON: {exc}")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}

        with self.subTest(msg="name field exists"):
            self.assertTrue(
                isinstance(data, dict) and "name" in data,
                "JSON field 'name' does not exist",
            )

        with self.subTest(msg="name matches speckit-pro"):
            self.assertEqual(_field_str(data, "name"), "speckit-pro", "field 'name'")

        with self.subTest(msg="name is kebab-case"):
            name_val = _field_str(data, "name")
            self.assertRegex(name_val, KEBAB_RE, "name must be kebab-case")

        with self.subTest(msg="version field exists and is semver"):
            version_val = _field_str(data, "version")
            self.assertRegex(version_val, SEMVER_RE, "version must be X.Y.Z")

        with self.subTest(msg="description field exists and is non-empty"):
            desc_val = _field_str(data, "description")
            self.assertTrue(bool(desc_val), "description is empty")

        with self.subTest(msg="author field exists"):
            self.assertTrue(
                isinstance(data, dict) and "author" in data,
                "JSON field 'author' does not exist",
            )


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidatePlugin)


def main() -> int:
    return run_counted(build_suite(), label="validate-plugin")


if __name__ == "__main__":
    raise SystemExit(main())
