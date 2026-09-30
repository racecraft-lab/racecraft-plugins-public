#!/usr/bin/env python3
"""Consolidated Layer 1 contracts owned by validate-plugin-metadata.py."""

from __future__ import annotations

from pathlib import Path
import json
import os
import re
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for _import_root in (LIB_DIR, PLUGIN_ROOT):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))

from structural_helpers import discover_skill_names
from structural_helpers import entries_by_name
from structural_helpers import field_exists as _field_exists
from structural_helpers import nested as _nested
from structural_helpers import source_path
from test_result import run_counted
from speckit_pro_runner.host_skills import render_host_skills

PLUGIN_JSON = PLUGIN_ROOT / '.claude-plugin' / 'plugin.json'
KEBAB_RE = re.compile('^[a-z][a-z0-9]*(-[a-z0-9]+)*$')

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
        with self.subTest(msg='version field is omitted for commit-addressed cache identity'):
            self.assertNotIn('version', data)
        with self.subTest(msg='description field exists and is non-empty'):
            desc_val = _field_str(data, 'description')
            self.assertTrue(bool(desc_val), 'description is empty')
        with self.subTest(msg='author field exists'):
            self.assertTrue(isinstance(data, dict) and 'author' in data, "JSON field 'author' does not exist")
CODEX_JSON = PLUGIN_ROOT / '.codex-plugin' / 'plugin.json'
CLAUDE_JSON = PLUGIN_ROOT / '.claude-plugin' / 'plugin.json'
# Codex skills with no Claude twin: the installer for the bundled Codex custom subagents.
CODEX_ONLY_SKILLS = frozenset({'install'})


def required_codex_skills(plugin_root: Path) -> tuple[str, ...]:
    """Every Claude skill directory, which needs a Codex counterpart, plus the Codex-only skills.

    Read from ``skills/``, never from ``codex-skills/``, so a dropped Codex skill is a gap.
    """
    claude = {path.name for path in (plugin_root / 'skills').iterdir() if path.is_dir()}
    return tuple(sorted(claude | CODEX_ONLY_SKILLS))


def codex_skill_gaps(plugin_root: Path) -> list[str]:
    """Required Codex skills that Codex would load no SKILL.md for, and Codex skills nothing requires.

    Codex loads the shared skills/ tree overlaid by codex-skills/, so the roster
    is read from that rendered tree.
    """
    required = set(required_codex_skills(plugin_root))
    with tempfile.TemporaryDirectory() as temporary:
        view = Path(temporary) / 'skills'
        render_host_skills(plugin_root, 'codex', view)
        present = set(discover_skill_names(view))
    return [f'Codex skill {name}/SKILL.md is missing' for name in sorted(required - present)] + [f'Codex skill {name}/ is not a required skill' for name in sorted(present - required)]


REQUIRED_SKILLS = required_codex_skills(PLUGIN_ROOT)
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
        with self.subTest(msg='codex-skills/ holds exactly the skills skills/ ships plus the Codex-only skills'):
            self.assertEqual([], codex_skill_gaps(PLUGIN_ROOT))
        for skill in REQUIRED_SKILLS:
            with self.subTest(msg=f'codex-skills/{skill}/ directory exists for its Codex sidecar'):
                self.assertTrue((PLUGIN_ROOT / 'codex-skills' / skill).is_dir(), f'codex-skills/{skill}/ directory not found')
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
CLAUDE_MARKETPLACE_JSON = REPO_ROOT / '.claude-plugin' / 'marketplace.json'
class ValidateMarketplaceEntries(unittest.TestCase):
    """Both registries list the same plugins, and every entry resolves to that
    plugin's own manifest for that client."""

    def test_both_registries_list_the_same_plugins(self) -> None:
        claude = json.loads(CLAUDE_MARKETPLACE_JSON.read_text(encoding='utf-8'))
        codex = json.loads(MARKETPLACE_JSON.read_text(encoding='utf-8'))
        with self.subTest(msg='marketplace names agree'):
            self.assertEqual(claude.get('name'), codex.get('name'))
        with self.subTest(msg='plugin names agree'):
            self.assertEqual(sorted(entries_by_name(claude)), sorted(entries_by_name(codex)))
        with self.subTest(msg='typesafe-jev is listed'):
            self.assertIn('typesafe-jev', entries_by_name(claude))

    def test_every_entry_resolves_to_its_client_manifest(self) -> None:
        # Codex reads .agents/plugins/marketplace.json, whose source is an
        # object; Claude Code reads .claude-plugin/marketplace.json, whose
        # source is a bare path. Each must reach the manifest for its client.
        for registry, manifest_dir in ((CLAUDE_MARKETPLACE_JSON, '.claude-plugin'), (MARKETPLACE_JSON, '.codex-plugin')):
            document = json.loads(registry.read_text(encoding='utf-8'))
            for name, entry in entries_by_name(document).items():
                path = source_path(entry)
                with self.subTest(msg=f'{registry.relative_to(REPO_ROOT)} {name} source is ./-relative inside the repository'):
                    self.assertTrue(path.startswith('./') and '..' not in path, path)
                manifest = REPO_ROOT / path / manifest_dir / 'plugin.json'
                with self.subTest(msg=f'{registry.relative_to(REPO_ROOT)} {name} resolves to {manifest_dir}/plugin.json'):
                    self.assertTrue(manifest.is_file(), f'{manifest} does not exist')
                with self.subTest(msg=f'{registry.relative_to(REPO_ROOT)} {name} names the manifest it resolves to'):
                    declared = json.loads(manifest.read_text(encoding='utf-8')).get('name') if manifest.is_file() else None
                    self.assertEqual(name, declared)
                if registry == MARKETPLACE_JSON:
                    with self.subTest(msg=f'{name} Codex source is local'):
                        self.assertEqual('local', (entry.get('source') or {}).get('source'))

def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-plugin-metadata")

if __name__ == "__main__":
    raise SystemExit(main())
