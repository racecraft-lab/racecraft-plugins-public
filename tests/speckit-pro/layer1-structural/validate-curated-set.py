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

sys.path.insert(0, str(PLUGIN_ROOT))
from speckit_pro_runner.helpers.readiness_host_items import host_item
from speckit_pro_runner.helpers.readiness_values import clean_text
from speckit_pro_runner.strict_input import SelectionError

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


class CuratedRecommendationContracts(unittest.TestCase):

    def test_shipped_curated_recommendations_have_an_archive_source(self) -> None:
        catalog = json.loads(MANIFEST.read_text(encoding='utf-8'))['entries']
        names = {entry['id'] for entry in catalog} | {'<name>', '<id>', '{name}'}
        command = re.compile(r'''\bspecify (?:extension|preset) add ([^`\n"']+)''')
        roots = (PLUGIN_ROOT, REPO_ROOT / 'dist' / 'claude' / 'speckit-pro',
                 REPO_ROOT / 'dist' / 'codex' / 'speckit-pro')
        for root in roots:
            self.assertTrue(root.is_dir())
            paths = sorted((root / 'skills').rglob('*.md'))
            paths += sorted((root / 'codex-skills').rglob('*.md'))
            paths += sorted((root / 'speckit_pro_runner' / 'helpers').glob('*.py'))
            for path in paths:
                for match in command.finditer(path.read_text(encoding='utf-8')):
                    args = match.group(1).split()
                    if args[0] in names:
                        with self.subTest(path=str(path.relative_to(REPO_ROOT)), command=match.group()):
                            self.assertIn('--from', args)
                            self.assertLess(args.index('--from') + 1, len(args))

    def test_readiness_missing_curated_extensions_use_the_pinned_archive(self) -> None:
        for entry in json.loads(MANIFEST.read_text(encoding='utf-8'))['entries']:
            if entry['kind'] != 'extension':
                continue
            with self.subTest(extension=entry['id']):
                _, item = host_item({'item': 'extension_versions', 'evidence_source': 'extension registry',
                                     'extensions': [{'extension': entry['id'], 'installed': None,
                                                     'expected': '1.0.0'}]}, 'codex', 'observed', 'revision')
                self.assertEqual(item['status'], 'unavailable')
                self.assertIn(f"specify extension add {entry['id']} --from {entry['archive_url']}", item['action'])
                self.assertIn('operator', item['action'].lower())

    def test_many_missing_extensions_keep_the_archive_install_instructions(self) -> None:
        entries = [{'extension': entry['id'], 'installed': None, 'expected': '1.0.0'}
                   for entry in json.loads(MANIFEST.read_text(encoding='utf-8'))['entries']
                   if entry['kind'] == 'extension']
        _, item = host_item({'item': 'extension_versions', 'evidence_source': 'extension registry',
                             'extensions': entries}, 'codex', 'observed', 'revision')
        self.assertEqual(item['status'], 'unavailable')
        self.assertIn('curated-set.json', item['action'])
        self.assertIn('--from <archive_url>', item['action'])
        self.assertIn('operator', item['action'].lower())

    def test_readiness_archive_urls_do_not_relax_local_path_privacy(self) -> None:
        url = json.loads(MANIFEST.read_text(encoding='utf-8'))['entries'][0]['archive_url']
        self.assertEqual(clean_text(url, 'action'), url)
        for path in ('/' + 'private/data', '~' + '/data', 'C:' + '/data', 'prefix:/' + 'data'):
            with self.subTest(path=path), self.assertRaises(SelectionError):
                clean_text(f'{url} {path}', 'action')

    def test_readiness_https_urls_refuse_userinfo(self) -> None:
        for value in ('https://user:hunter2@example.com/x.zip',
                      'https://user:letters@example.com/x.zip',
                      'https://user@example.com/x.zip',
                      'https://@example.com/x.zip',
                      'HTTPS://user:hunter2@example.com/x.zip',
                      'Download https://user:hunter2@example.com/x.zip before installing.'):
            with self.subTest(value=value):
                with self.assertRaises(SelectionError) as refused:
                    clean_text(value, 'action')
                self.assertNotIn(value, str(refused.exception))
        for url in ('https://example.com/x.zip',
                    'https://example.com/user@docs.zip',
                    'https://example.com/x.zip?contact=reader@example.com',
                    'https://example.com/x.zip#reader@example.com'):
            with self.subTest(url=url):
                self.assertEqual(clean_text(url, 'action'), url)


class CuratedGuidanceContracts(unittest.TestCase):

    def test_install_and_upgrade_skills_install_through_from(self) -> None:
        guide = ' '.join((PLUGIN_ROOT / 'skills' / 'speckit-coach' / 'references' / 'presets-extensions-guide.md').read_text(encoding='utf-8').split())
        with self.subTest(msg='guide says what the pin guarantees and what the operator reviews'):
            for phrase in ('pins the bytes but does not vet them', 'specify extension info', 'commands, scripts, and hooks'):
                self.assertIn(phrase, guide)
        with self.subTest(msg='each kind is inspected with its own info command, which prints no archive URL'):
            # Spec Kit v1.1.0 extensions/command_info.py and presets/command_info.py print a
            # Repository link and never the download URL; `extension info` cannot see presets.
            for phrase in ('`specify extension info <id>` for an extension', '`specify preset info <id>` for a preset',
                           'Repository'):
                self.assertIn(phrase, guide)
            self.assertNotIn('prints the candidate archive URL', guide)
        with self.subTest(msg='directory presence leaves completed installation unproven'):
            self.assertIn('Directory presence and a successful exit leave completion unproven', guide)
            self.assertIn('owner-run acceptance', guide)
            self.assertNotIn('confirm each entry by listing', guide)
        for skill in SKILLS_WITH_CURATED_STEP:
            text = (PLUGIN_ROOT / 'skills' / skill / 'SKILL.md').read_text(encoding='utf-8')
            flat = ' '.join(text.split())
            with self.subTest(msg=f'{skill} names the --from install shape'):
                self.assertIn(INSTALL_SHAPE, flat)
            with self.subTest(msg=f'{skill} asks the operator to vet the pinned archive before confirming'):
                self.assertIn('pins the bytes but does not vet them', flat)
            with self.subTest(msg=f'{skill} no longer tells the operator to add by catalog id'):
                self.assertNotIn('"extension", "add", "<id>"]', flat)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-curated-set")

if __name__ == "__main__":
    raise SystemExit(main())
