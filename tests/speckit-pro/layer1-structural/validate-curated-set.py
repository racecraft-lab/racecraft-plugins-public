#!/usr/bin/env python3
"""Curated extension and preset catalog contracts."""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted

MANIFEST = PLUGIN_ROOT / 'scripts' / 'curated-set.json'
# Spec Kit v1.1.0 refuses `add <id>` for community-catalog entries (discovery-only), so each
# entry carries the archive the install command takes through `--from`. Pinning a commit
# keeps the vetted bytes fixed even when the upstream tag moves.
ARCHIVE_URL = re.compile(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/archive/[0-9a-f]{40}\.zip')
INSTALL_SHAPE = '["<kind>", "add", "<id>", "--from", "<archive_url>"]'
SKILLS_WITH_CURATED_STEP = ('speckit-install', 'speckit-upgrade')
EXPECTED_ENTRIES = {'review': 'extension', 'verify': 'extension', 'verify-tasks': 'extension', 'cleanup': 'extension', 'retrospective': 'extension', 'claude-ask-questions': 'preset'}

def _jq_field(value: object) -> str:
    """Mirror jq ``.[field] // "MISSING"``: null/false collapse to MISSING, else
    render the value's raw string form (``jq -r``)."""
    if value is None or value is False:
        return 'MISSING'
    if value is True:
        return 'true'
    if isinstance(value, str):
        return value
    return str(value)

class ValidateCuratedSet(unittest.TestCase):

    def test_curated_set(self) -> None:
        with self.subTest(msg='manifest file exists'):
            self.assertTrue(MANIFEST.is_file(), f'file not found: {MANIFEST}')
        raw = MANIFEST.read_text(encoding='utf-8') if MANIFEST.is_file() else ''
        with self.subTest(msg='manifest parses as JSON'):
            try:
                json.loads(raw)
            except json.JSONDecodeError:
                self.fail('invalid JSON')
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}
        with self.subTest(msg='manifest contains only live catalog fields'):
            self.assertEqual(set(data), {'version', 'description', 'entries'})
        with self.subTest(msg='catalog describes manual recommendations'):
            description = str(data.get('description', '')).lower()
            self.assertIn('manual recommendation', description)
            self.assertNotIn('auto-install', description)
        with self.subTest(msg='manifest has version field set to 1'):
            version_val = data.get('version', '') if isinstance(data, dict) else ''
            rendered = '' if version_val == '' or version_val is None else _jq_field(version_val)
            self.assertEqual('1', rendered, f"version='{rendered}' (expected 1)")
        entries = data.get('entries') if isinstance(data, dict) else None
        entries_list = entries if isinstance(entries, list) else []
        with self.subTest(msg='manifest has non-empty entries array'):
            self.assertGreater(len(entries_list), 0, 'entries is empty')
        catalog: dict[str, object] = {}
        for entry in entries_list:
            entry_id_val = entry.get('id') if isinstance(entry, dict) else None
            entry_id = str(entry_id_val) if entry_id_val is not None else 'null'
            with self.subTest(msg=f"entry '{entry_id}' contains only operator-consumed fields"):
                self.assertEqual(set(entry) if isinstance(entry, dict) else set(), {'id', 'kind', 'archive_url'})
            with self.subTest(msg=f"entry '{entry_id}' has valid kind (extension or preset)"):
                kind = entry.get('kind') if isinstance(entry, dict) else None
                self.assertIn(kind, ('extension', 'preset'), f"kind='{kind}' is not extension or preset")
            with self.subTest(msg=f"entry '{entry_id}' is unique"):
                self.assertNotIn(entry_id, catalog)
            catalog[entry_id] = entry.get('kind') if isinstance(entry, dict) else None
        with self.subTest(msg='catalog retains the supported recommendations and kinds'):
            self.assertEqual(catalog, EXPECTED_ENTRIES)

    def test_entries_pin_a_commit_archive(self) -> None:
        for entry in json.loads(MANIFEST.read_text(encoding='utf-8'))['entries']:
            with self.subTest(msg=f"entry '{entry['id']}' pins a commit archive for the --from install"):
                url = entry.get('archive_url')
                self.assertTrue(isinstance(url, str) and ARCHIVE_URL.fullmatch(url), f'archive_url={url!r}')

    def test_install_and_upgrade_skills_install_through_from(self) -> None:
        for skill in SKILLS_WITH_CURATED_STEP:
            text = (PLUGIN_ROOT / 'skills' / skill / 'SKILL.md').read_text(encoding='utf-8')
            flat = ' '.join(text.split())
            with self.subTest(msg=f'{skill} names the --from install shape'):
                self.assertIn(INSTALL_SHAPE, flat)
            with self.subTest(msg=f'{skill} no longer tells the operator to add by catalog id'):
                self.assertNotIn('"extension", "add", "<id>"]', flat)

def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-curated-set")

if __name__ == "__main__":
    raise SystemExit(main())
