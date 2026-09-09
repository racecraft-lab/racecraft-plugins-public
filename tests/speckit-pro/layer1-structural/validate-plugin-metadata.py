#!/usr/bin/env python3
"""Consolidated Layer 1 contracts owned by validate-plugin-metadata.py."""

from __future__ import annotations

from pathlib import Path
import json
import os
import re
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for _import_root in (LIB_DIR, PLUGIN_ROOT):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))

from structural_helpers import field_exists as _field_exists
from structural_helpers import nested as _nested
from test_result import run_counted

PLUGIN_JSON = PLUGIN_ROOT / '.claude-plugin' / 'plugin.json'
KEBAB_RE = re.compile('^[a-z][a-z0-9]*(-[a-z0-9]+)*$')
validate_plugin_SEMVER_RE = re.compile('^[0-9]+\\.[0-9]+\\.[0-9]+$')

def _field_str(data: object, key: str) -> str:
    """Mirror the bash `python3 -c ... 2>/dev/null` field read: value as a string,
    empty when the key is absent or the document is not a mapping."""
    if isinstance(data, dict) and key in data:
        return str(data[key])
    return ''

class ValidatePlugin(unittest.TestCase):

    def test_plugin_manifest(self) -> None:
        with self.subTest(msg='plugin.json exists'):
            self.assertTrue(PLUGIN_JSON.is_file(), f'file not found: {PLUGIN_JSON}')
        raw = PLUGIN_JSON.read_text(encoding='utf-8') if PLUGIN_JSON.is_file() else ''
        with self.subTest(msg='plugin.json is valid JSON'):
            try:
                json.loads(raw)
            except json.JSONDecodeError as exc:
                self.fail(f'plugin.json is not valid JSON: {exc}')
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}
        with self.subTest(msg='name field exists'):
            self.assertTrue(isinstance(data, dict) and 'name' in data, "JSON field 'name' does not exist")
        with self.subTest(msg='name matches speckit-pro'):
            self.assertEqual(_field_str(data, 'name'), 'speckit-pro', "field 'name'")
        with self.subTest(msg='name is kebab-case'):
            name_val = _field_str(data, 'name')
            self.assertRegex(name_val, KEBAB_RE, 'name must be kebab-case')
        with self.subTest(msg='version field exists and is semver'):
            version_val = _field_str(data, 'version')
            self.assertRegex(version_val, validate_plugin_SEMVER_RE, 'version must be X.Y.Z')
        with self.subTest(msg='description field exists and is non-empty'):
            desc_val = _field_str(data, 'description')
            self.assertTrue(bool(desc_val), 'description is empty')
        with self.subTest(msg='author field exists'):
            self.assertTrue(isinstance(data, dict) and 'author' in data, "JSON field 'author' does not exist")
CODEX_JSON = PLUGIN_ROOT / '.codex-plugin' / 'plugin.json'
CLAUDE_JSON = PLUGIN_ROOT / '.claude-plugin' / 'plugin.json'
REQUIRED_SKILLS = ('speckit-archive-cleanup', 'speckit-autopilot', 'speckit-coach', 'speckit-scaffold-spec', 'speckit-status', 'speckit-resolve-pr', 'install', 'grill-me', 'speckit-prd')
validate_codex_plugin_SEMVER_RE = re.compile('^[0-9]+\\.[0-9]+\\.[0-9]+$')

class ValidateCodexPlugin(unittest.TestCase):

    def test_codex_plugin(self) -> None:
        with self.subTest(msg='.codex-plugin/plugin.json exists'):
            self.assertTrue(CODEX_JSON.is_file(), f'file not found: {CODEX_JSON}')
        raw = CODEX_JSON.read_text(encoding='utf-8') if CODEX_JSON.is_file() else ''
        with self.subTest(msg='.codex-plugin/plugin.json is valid JSON'):
            try:
                json.loads(raw)
            except json.JSONDecodeError:
                self.fail('.codex-plugin/plugin.json is not valid JSON')
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}
        with self.subTest(msg='name field exists'):
            self.assertTrue(_field_exists(data, 'name'), "JSON field 'name' does not exist")
        with self.subTest(msg='name matches speckit-pro'):
            name_val = _nested(data, 'name')
            self.assertEqual('speckit-pro', str(name_val) if name_val is not None else '', "field 'name' mismatch")
        with self.subTest(msg='version is semver X.Y.Z'):
            version_val = _nested(data, 'version')
            self.assertRegex(str(version_val) if version_val is not None else '', validate_codex_plugin_SEMVER_RE, 'version must be X.Y.Z')
        desc_val = _nested(data, 'description')
        desc = str(desc_val) if desc_val is not None else ''
        with self.subTest(msg='description is non-empty'):
            self.assertTrue(desc, 'description is empty')
        with self.subTest(msg='description uses scaffold naming for spec preparation'):
            self.assertTrue('spec scaffolding' in desc and 'setup' not in desc, "expected Codex plugin description to use scaffolding terminology (no 'setup')")
        with self.subTest(msg='homepage field exists'):
            self.assertTrue(_field_exists(data, 'homepage'), "JSON field 'homepage' does not exist")
        with self.subTest(msg='skills field equals ./codex-skills/'):
            skills_val = _nested(data, 'skills')
            self.assertEqual('./codex-skills/', str(skills_val) if skills_val is not None else '', "field 'skills' mismatch")
        with self.subTest(msg='interface.displayName exists'):
            self.assertTrue(_field_exists(data, 'interface.displayName'), "JSON field 'interface.displayName' does not exist")
        with self.subTest(msg='interface.category exists'):
            self.assertTrue(_field_exists(data, 'interface.category'), "JSON field 'interface.category' does not exist")
        with self.subTest(msg='interface.defaultPrompt exists'):
            self.assertTrue(_field_exists(data, 'interface.defaultPrompt'), "JSON field 'interface.defaultPrompt' does not exist")
        with self.subTest(msg='interface.defaultPrompt uses scaffold naming for spec preparation'):
            dp_list = _nested(data, 'interface', 'defaultPrompt')
            default_prompts = '\n'.join(dp_list) if isinstance(dp_list, list) else ''
            self.assertTrue('scaffold a spec worktree' in default_prompts and 'set up a spec worktree' not in default_prompts, 'expected Codex default prompt to say scaffold a spec worktree')
        with self.subTest(msg='codex-skills/ directory exists'):
            self.assertTrue((PLUGIN_ROOT / 'codex-skills').is_dir(), f"codex-skills/ directory not found at {PLUGIN_ROOT / 'codex-skills'}")
        for skill in REQUIRED_SKILLS:
            with self.subTest(msg=f'codex-skills/{skill}/ directory exists'):
                self.assertTrue((PLUGIN_ROOT / 'codex-skills' / skill).is_dir(), f'codex-skills/{skill}/ directory not found')
            with self.subTest(msg=f'codex-skills/{skill}/SKILL.md exists'):
                self.assertTrue((PLUGIN_ROOT / 'codex-skills' / skill / 'SKILL.md').is_file(), f'file not found: codex-skills/{skill}/SKILL.md')
        with self.subTest(msg='version matches .claude-plugin/plugin.json'):
            if CLAUDE_JSON.is_file():
                try:
                    claude_version = json.loads(CLAUDE_JSON.read_text(encoding='utf-8')).get('version')
                except (json.JSONDecodeError, OSError):
                    claude_version = None
                codex_version = _nested(data, 'version')
                self.assertEqual(claude_version, codex_version, f"version mismatch: .claude-plugin/plugin.json='{claude_version}', .codex-plugin/plugin.json='{codex_version}'")
            else:
                self.fail('.claude-plugin/plugin.json not found — cannot compare versions')
MARKETPLACE_JSON = REPO_ROOT / '.agents' / 'plugins' / 'marketplace.json'

class ValidateCodexMarketplace(unittest.TestCase):

    def test_codex_marketplace(self) -> None:
        with self.subTest(msg='.agents/plugins/marketplace.json exists'):
            self.assertTrue(MARKETPLACE_JSON.is_file(), f'file not found: {MARKETPLACE_JSON}')
        raw = MARKETPLACE_JSON.read_text(encoding='utf-8') if MARKETPLACE_JSON.is_file() else ''
        with self.subTest(msg='.agents/plugins/marketplace.json is valid JSON'):
            try:
                json.loads(raw)
            except json.JSONDecodeError:
                self.fail('.agents/plugins/marketplace.json is not valid JSON')
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}
        with self.subTest(msg='name field exists'):
            self.assertTrue(_field_exists(data, 'name'), "JSON field 'name' does not exist")
        with self.subTest(msg='interface.displayName field exists'):
            self.assertTrue(_field_exists(data, 'interface.displayName'), "JSON field 'interface.displayName' does not exist")
        with self.subTest(msg='plugins array exists'):
            plugins = data.get('plugins') if isinstance(data, dict) else None
            self.assertIsInstance(plugins, list, 'plugins field is missing or not an array')
        with self.subTest(msg='first plugin name is speckit-pro'):
            first_name = _nested(data, 'plugins', 0, 'name')
            got = str(first_name) if first_name is not None else ''
            self.assertEqual('speckit-pro', got, f"expected first plugin name 'speckit-pro', got '{got}'")
        with self.subTest(msg='source.source is local'):
            source_kind = _nested(data, 'plugins', 0, 'source', 'source')
            got = str(source_kind) if source_kind is not None else ''
            self.assertEqual('local', got, f"expected source.source 'local', got '{got}'")
        source_path_val = _nested(data, 'plugins', 0, 'source', 'path')
        source_path = str(source_path_val) if source_path_val is not None else ''
        with self.subTest(msg='source.path is ./-prefixed and relative'):
            self.assertTrue(source_path.startswith('./'), f"source.path must start with ./, got '{source_path}'")
        resolved_path = os.path.normpath(f'{REPO_ROOT}/{source_path}')
        with self.subTest(msg='source.path resolves to existing directory'):
            self.assertTrue(Path(resolved_path).is_dir(), f"source.path '{source_path}' does not resolve to an existing directory (checked: {resolved_path})")
        with self.subTest(msg='source.path stays inside repo root'):
            repo_real = os.path.realpath(str(REPO_ROOT))
            target_real = os.path.realpath(resolved_path)
            self.assertEqual(repo_real, os.path.commonpath([repo_real, target_real]), f"source.path '{source_path}' resolves outside repo root")
        with self.subTest(msg='policy.installation field exists'):
            val = _nested(data, 'plugins', 0, 'policy', 'installation')
            self.assertTrue(val, 'policy.installation field is missing or empty')
        with self.subTest(msg='policy.authentication field exists'):
            val = _nested(data, 'plugins', 0, 'policy', 'authentication')
            self.assertTrue(val, 'policy.authentication field is missing or empty')
        with self.subTest(msg='category field exists'):
            val = _nested(data, 'plugins', 0, 'category')
            self.assertTrue(val, 'category field is missing or empty')
MANIFEST = PLUGIN_ROOT / 'scripts' / 'curated-set.json'
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
                self.assertEqual(set(entry) if isinstance(entry, dict) else set(), {'id', 'kind'})
            with self.subTest(msg=f"entry '{entry_id}' has valid kind (extension or preset)"):
                kind = entry.get('kind') if isinstance(entry, dict) else None
                self.assertIn(kind, ('extension', 'preset'), f"kind='{kind}' is not extension or preset")
            with self.subTest(msg=f"entry '{entry_id}' is unique"):
                self.assertNotIn(entry_id, catalog)
            catalog[entry_id] = entry.get('kind') if isinstance(entry, dict) else None
        with self.subTest(msg='catalog retains the supported recommendations and kinds'):
            self.assertEqual(catalog, EXPECTED_ENTRIES)

def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-plugin-metadata")

if __name__ == "__main__":
    raise SystemExit(main())
