#!/usr/bin/env python3
"""Structural validation for scripts/curated-set.json (port of validate-curated-set.sh).

XPLAT-010 count-parity port (T026, US2). Python 3.11+ standard library only.
Asserts the curated-set manifest is valid JSON with the schema
``install-curated-set`` depends on, that the required curated ids are present,
and that every entry carries the required fields, a valid ``kind``, and an
``owner/name``-shaped repo. Every former ``assert_*``/``_pass``/``_fail``
execution maps to one counted ``subTest`` unit; names reproduced verbatim via
``subTest(msg=...)`` for a 1:1 baseline match.

The check names embed live ``scripts/curated-set.json`` entry ids and iterate the
entries in file order, so this data file is a baseline regeneration trigger
(count-parity contract §2, rule 4): adding/removing/reordering an entry changes
the inventory and requires recapturing the baseline.

Baseline: ``tests/speckit-pro/parity/xplat-010/validate-curated-set-baseline.txt``
(TOTAL: 58).
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

MANIFEST = PLUGIN_ROOT / "scripts" / "curated-set.json"

REQUIRED_IDS = ("review", "verify", "verify-tasks", "cleanup", "retrospective", "claude-ask-questions")
REQUIRED_FIELDS = ("id", "kind", "repo", "recommended_default", "description", "min_speckit_version")
REPO_SHAPE_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _jq_field(value: object) -> str:
    """Mirror jq ``.[field] // "MISSING"``: null/false collapse to MISSING, else
    render the value's raw string form (``jq -r``)."""
    if value is None or value is False:
        return "MISSING"
    if value is True:
        return "true"
    if isinstance(value, str):
        return value
    return str(value)


class ValidateCuratedSet(unittest.TestCase):
    def test_curated_set(self) -> None:
        with self.subTest(msg="manifest file exists"):
            self.assertTrue(MANIFEST.is_file(), f"file not found: {MANIFEST}")

        raw = MANIFEST.read_text(encoding="utf-8") if MANIFEST.is_file() else ""
        with self.subTest(msg="manifest parses as JSON"):
            try:
                json.loads(raw)
            except json.JSONDecodeError:
                self.fail("invalid JSON")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}

        with self.subTest(msg="manifest has version field set to 1"):
            version_val = data.get("version", "") if isinstance(data, dict) else ""
            rendered = "" if version_val == "" or version_val is None else _jq_field(version_val)
            self.assertEqual("1", rendered, f"version='{rendered}' (expected 1)")

        entries = data.get("entries") if isinstance(data, dict) else None
        entries_list = entries if isinstance(entries, list) else []
        with self.subTest(msg="manifest has non-empty entries array"):
            self.assertGreater(len(entries_list), 0, "entries is empty")

        for curated_id in REQUIRED_IDS:
            with self.subTest(msg=f"entry '{curated_id}' is present"):
                found = any(isinstance(e, dict) and e.get("id") == curated_id for e in entries_list)
                self.assertTrue(found, f"missing id '{curated_id}'")

        for entry in entries_list:
            entry_id_val = entry.get("id") if isinstance(entry, dict) else None
            entry_id = str(entry_id_val) if entry_id_val is not None else "null"

            for field in REQUIRED_FIELDS:
                with self.subTest(msg=f"entry '{entry_id}' has field '{field}'"):
                    rendered = _jq_field(entry.get(field) if isinstance(entry, dict) else None)
                    self.assertTrue(rendered != "MISSING" and len(rendered) > 0, f"missing or empty '{field}'")

            with self.subTest(msg=f"entry '{entry_id}' has valid kind (extension or preset)"):
                kind = entry.get("kind") if isinstance(entry, dict) else None
                self.assertIn(kind, ("extension", "preset"), f"kind='{kind}' is not extension or preset")

            with self.subTest(msg=f"entry '{entry_id}' has plausibly-shaped repo (owner/name)"):
                repo = entry.get("repo") if isinstance(entry, dict) else None
                repo_str = repo if isinstance(repo, str) else ""
                self.assertRegex(repo_str, REPO_SHAPE_RE, f"repo='{repo_str}' is not owner/name shape")


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateCuratedSet)


def main() -> int:
    return run_counted(build_suite(), label="validate-curated-set")


if __name__ == "__main__":
    raise SystemExit(main())
