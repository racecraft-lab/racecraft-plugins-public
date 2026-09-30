#!/usr/bin/env python3
"""typesafe-jev provenance, marketplace install path, and version contracts."""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from structural_helpers import entries_by_name
from structural_helpers import source_path
from test_result import run_counted

TYPESAFE_JEV_ROOT = REPO_ROOT / 'typesafe-jev'
TYPESAFE_JEV_MODULE = 'module github.com/racecraft-lab/racecraft-plugins-public/typesafe-jev'
UPSTREAM_REFERENCE = 'itsmostafa/typesafe-mcp'
# The fork's former standalone home. The plugin manifests must point at this
# repository instead; the `skills add racecraft-lab/typesafe-mcp` lines in the
# skills and docs are intentional and stay outside this check.
FORMER_FORK_REFERENCE = 'racecraft-lab/typesafe-mcp'
TYPESAFE_JEV_MANIFESTS = (
    TYPESAFE_JEV_ROOT / 'plugin' / '.claude-plugin' / 'plugin.json',
    TYPESAFE_JEV_ROOT / 'plugin' / '.codex-plugin' / 'plugin.json',
)

class ValidateTypesafeJevProvenance(unittest.TestCase):
    """typesafe-jev forks itsmostafa/typesafe-mcp. Its code and its shipped
    plugin must never point back at upstream, or an update or an install could
    fetch a binary without this fork's credential and backend rules. Prose that
    credits upstream (README, CHANGELOG, docs) is outside this check."""

    def test_no_upstream_reference_in_code_or_packaging(self) -> None:
        scanned = [TYPESAFE_JEV_ROOT / 'go.mod']
        for root in (TYPESAFE_JEV_ROOT / 'cmd', TYPESAFE_JEV_ROOT / 'plugin'):
            scanned.extend(path for path in sorted(root.rglob('*')) if path.is_file())
        with self.subTest(msg='typesafe-jev code and packaging exist'):
            self.assertGreater(len(scanned), 1, 'no typesafe-jev files were found to scan')
        for path in scanned:
            text = path.read_text(encoding='utf-8', errors='replace')
            with self.subTest(msg=f'{path.relative_to(REPO_ROOT)} has no upstream reference'):
                self.assertNotIn(UPSTREAM_REFERENCE, text)

    def test_manifests_do_not_point_at_the_former_fork(self) -> None:
        for path in TYPESAFE_JEV_MANIFESTS:
            with self.subTest(msg=f'{path.relative_to(REPO_ROOT)} has no {FORMER_FORK_REFERENCE} reference'):
                self.assertNotIn(FORMER_FORK_REFERENCE, path.read_text(encoding='utf-8'))

    def test_module_path_is_this_repository(self) -> None:
        go_mod = (TYPESAFE_JEV_ROOT / 'go.mod').read_text(encoding='utf-8')
        self.assertEqual(TYPESAFE_JEV_MODULE, go_mod.splitlines()[0])

CLAUDE_MARKETPLACE_JSON = REPO_ROOT / '.claude-plugin' / 'marketplace.json'
MARKETPLACE_JSON = REPO_ROOT / '.agents' / 'plugins' / 'marketplace.json'
RELEASE_MANIFEST_JSON = REPO_ROOT / '.release-please-manifest.json'
RELEASE_CONFIG_JSON = REPO_ROOT / 'release-please-config.json'
TYPESAFE_JEV_PLUGIN = 'typesafe-jev/plugin'
# Every file that states typesafe-jev's version, with the release-please
# extra-files path and jsonpath that bump it. Adding a declaration without
# wiring it into the release is the mistake this table makes visible.
TYPESAFE_JEV_VERSION_DECLARATIONS = (
    ('typesafe-jev/plugin/.claude-plugin/plugin.json', 'plugin/.claude-plugin/plugin.json', '$.version'),
    ('typesafe-jev/plugin/.codex-plugin/plugin.json', 'plugin/.codex-plugin/plugin.json', '$.version'),
    ('.agents/plugins/marketplace.json', '/.agents/plugins/marketplace.json', '$.plugins[?(@.name=="typesafe-jev")].version'),
)

class ValidateTypesafeJevInstall(unittest.TestCase):
    def test_typesafe_jev_installs_from_its_plugin_directory(self) -> None:
        claude = entries_by_name(json.loads(CLAUDE_MARKETPLACE_JSON.read_text(encoding='utf-8')))
        codex = entries_by_name(json.loads(MARKETPLACE_JSON.read_text(encoding='utf-8')))
        self.assertEqual(f'./{TYPESAFE_JEV_PLUGIN}', source_path(claude.get('typesafe-jev', {})))
        self.assertEqual(f'./{TYPESAFE_JEV_PLUGIN}', source_path(codex.get('typesafe-jev', {})))

class ValidateTypesafeJevVersions(unittest.TestCase):
    """Every file that states typesafe-jev's version states the released one,
    and release-please bumps every one of them. A version a release cannot
    reach is a version an operator sees and cannot install."""

    def test_versions_agree_and_are_bumped(self) -> None:
        released = json.loads(RELEASE_MANIFEST_JSON.read_text(encoding='utf-8')).get('typesafe-jev')
        self.assertRegex(str(released), '^[0-9]+\\.[0-9]+\\.[0-9]+$')
        config = json.loads(RELEASE_CONFIG_JSON.read_text(encoding='utf-8'))
        package = (config.get('packages') or {}).get('typesafe-jev') or {}
        wired = {(entry.get('path'), entry.get('jsonpath')) for entry in package.get('extra-files') or [] if isinstance(entry, dict)}
        for file_path, extra_path, jsonpath in TYPESAFE_JEV_VERSION_DECLARATIONS:
            document = json.loads((REPO_ROOT / file_path).read_text(encoding='utf-8'))
            if jsonpath == '$.version':
                stated = document.get('version')
            else:
                stated = entries_by_name(document).get('typesafe-jev', {}).get('version')
            with self.subTest(msg=f'{file_path} states the released version'):
                self.assertEqual(released, stated)
            with self.subTest(msg=f'release-please bumps {file_path}'):
                self.assertIn((extra_path, jsonpath), wired)
        skill = (REPO_ROOT / 'typesafe-jev/plugin/shared-skills/typed-judgments/SKILL.md').read_text(encoding='utf-8')
        with self.subTest(msg='typed-judgments states the released version'):
            self.assertIn(f'version: {released} # x-release-please-version', skill)
        with self.subTest(msg='release-please bumps typed-judgments'):
            self.assertIn(('plugin/shared-skills/typed-judgments/SKILL.md', None), wired)
        claude_entry = entries_by_name(json.loads(CLAUDE_MARKETPLACE_JSON.read_text(encoding='utf-8'))).get('typesafe-jev', {})
        with self.subTest(msg='the Claude registry entry states the released version'):
            # refresh-release-artifacts.py copies it from the plugin manifest.
            self.assertEqual(released, claude_entry.get('version'))

def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-typesafe-jev-metadata")

if __name__ == "__main__":
    raise SystemExit(main())
