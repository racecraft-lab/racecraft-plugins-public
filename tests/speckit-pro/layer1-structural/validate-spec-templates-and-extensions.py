#!/usr/bin/env python3
"""Spec templates, the .specify extension payload, and the .process gitattributes scope."""

from __future__ import annotations

from pathlib import Path
import json
import re
import stat
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for _import_root in (LIB_DIR, PLUGIN_ROOT):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))

from test_result import run_counted

ROADMAP_TEMPLATE = PLUGIN_ROOT / 'skills/speckit-coach/templates/technical-roadmap-template.md'
SPEC_TEMPLATES = (REPO_ROOT / '.specify/presets/speckit-pro-reviewability/templates/spec-template.md', REPO_ROOT / '.specify/templates/spec-template.md')
PRESET_PLAN_TEMPLATE = REPO_ROOT / '.specify/presets/speckit-pro-reviewability/templates/plan-template.md'

def _rel_repo(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()

class ValidateSpecTemplates(unittest.TestCase):

    def test_003_technical_roadmap_template_reviewability_vocabulary(self) -> None:
        with self.subTest(msg='technical-roadmap-template.md: exists'):
            self.assertTrue(ROADMAP_TEMPLATE.is_file(), f'file not found: {ROADMAP_TEMPLATE}')
        content = ROADMAP_TEMPLATE.read_text(encoding='utf-8') if ROADMAP_TEMPLATE.is_file() else ''
        contains_checks = (('technical-roadmap-template.md: has Reviewability Contract section', '## Reviewability Contract'), ('technical-roadmap-template.md: advertises the production-LOC warn threshold', '400 reviewable production LOC'), ('technical-roadmap-template.md: advertises the production-LOC block threshold', '800 reviewable production LOC'), ('technical-roadmap-template.md: documents surface-count-as-warning rule', 'more than one primary surface is also a warning'), ('technical-roadmap-template.md: documents the typed exception pragma', 'Reviewability-Exception: <class>'), ('technical-roadmap-template.md: names the refactor exception class', 'refactor'), ('technical-roadmap-template.md: names the infra exception class', 'infra'), ('technical-roadmap-template.md: names the upgrade exception class', 'upgrade'))
        for name, needle in contains_checks:
            with self.subTest(msg=name):
                self.assertIn(needle, content)
        for klass in ('refactor', 'infra', 'upgrade'):
            with self.subTest(msg=f"technical-roadmap-template.md: no concrete '{klass}' exception pragma"):
                self.assertNotIn(f'Reviewability-Exception: {klass}', content)

    def test_003_technical_roadmap_template_workflow_links_point_under_process(self) -> None:
        # Scaffold writes each workflow to .process/ beside the roadmap, so a bare link breaks.
        content = ROADMAP_TEMPLATE.read_text(encoding='utf-8')
        targets = re.findall(r'\[SPEC-\d+-workflow\.md\]\(([^)]*)\)', content)
        self.assertEqual(4, len(targets), 'expected one workflow link per template spec row')
        for target in targets:
            with self.subTest(msg=f'technical-roadmap-template.md: workflow link {target} points under .process/'):
                self.assertRegex(target, r'^\.process/SPEC-\d+-workflow\.md$')

    def test_004_spec_templates_generated_exception_safety(self) -> None:
        for spec_template in SPEC_TEMPLATES:
            template_name = _rel_repo(spec_template)
            with self.subTest(msg=f'{template_name}: exists'):
                self.assertTrue(spec_template.is_file(), f'file not found: {spec_template}')
            if not spec_template.is_file():
                continue
            template_content = spec_template.read_text(encoding='utf-8')
            with self.subTest(msg=f'{template_name}: names accepted exception classes'):
                self.assertIn('refactor, infra, and upgrade', template_content)
            with self.subTest(msg=f'{template_name}: explains invalid generated/template provenance'):
                self.assertIn('generated templates', template_content)
            for klass in ('refactor', 'infra', 'upgrade'):
                with self.subTest(msg=f'{template_name}: no concrete {klass} exception pragma'):
                    self.assertNotIn(f'Reviewability-Exception: {klass}', template_content)

    def test_005_reviewability_preset_plan_template_declared_files_format(self) -> None:
        with self.subTest(msg='reviewability-preset plan-template.md: exists'):
            self.assertTrue(PRESET_PLAN_TEMPLATE.is_file(), f'file not found: {PRESET_PLAN_TEMPLATE}')
        if not PRESET_PLAN_TEMPLATE.is_file():
            return
        preset_plan_content = PRESET_PLAN_TEMPLATE.read_text(encoding='utf-8')
        checks = (('reviewability-preset plan-template.md: has Declared File Operations section', '## Declared File Operations'), ("reviewability-preset plan-template.md: teaches the '- NEW' list-marker format the parser requires", '- NEW '), ("reviewability-preset plan-template.md: teaches the '- MODIFIED' list-marker format the parser requires", '- MODIFIED '))
        for name, needle in checks:
            with self.subTest(msg=name):
                self.assertIn(needle, preset_plan_content)

EXTENSIONS_ROOT = REPO_ROOT / '.specify' / 'extensions'
REGISTRY_PATH = EXTENSIONS_ROOT / '.registry'
HOOKS_PATH = REPO_ROOT / '.specify' / 'extensions.yml'
FILE_ENTRY = re.compile('^\\s+file:\\s+["\\\']?([^"\\\']+)["\\\']?\\s*$')
HOOK_COMMAND = re.compile('^\\s+command:\\s+([A-Za-z0-9_.-]+)\\s*$')

def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))

def declared_files(extension_dir: Path) -> list[Path]:
    manifest = extension_dir / 'extension.yml'
    paths: list[Path] = []
    for line in manifest.read_text(encoding='utf-8').splitlines():
        match = FILE_ENTRY.match(line)
        if match is not None:
            paths.append(extension_dir / match.group(1))
    return paths

def claude_skill_path(command: str) -> Path:
    return REPO_ROOT / '.claude' / 'skills' / command.replace('.', '-') / 'SKILL.md'

class ValidateSpecifyExtensions(unittest.TestCase):

    def test_extension_integrity(self) -> None:
        with self.subTest(msg='Spec Kit extension registry exists'):
            self.assertTrue(REGISTRY_PATH.is_file(), f'file not found: {REGISTRY_PATH}')
        with self.subTest(msg='Spec Kit extension hook configuration exists'):
            self.assertTrue(HOOKS_PATH.is_file(), f'file not found: {HOOKS_PATH}')
        if not REGISTRY_PATH.is_file() or not HOOKS_PATH.is_file():
            return
        registry = load_registry()
        extensions = registry.get('extensions') if isinstance(registry, dict) else None
        with self.subTest(msg='Spec Kit extension registry has schema 1.0 and extension records'):
            self.assertEqual(registry.get('schema_version'), '1.0')
            self.assertIsInstance(extensions, dict)
        if not isinstance(extensions, dict):
            return
        registered_commands: set[str] = set()
        for extension_id, record in sorted(extensions.items()):
            if not isinstance(record, dict) or record.get('enabled') is not True:
                continue
            extension_dir = EXTENSIONS_ROOT / extension_id
            with self.subTest(msg=f'enabled extension payload exists: {extension_id}'):
                self.assertTrue((extension_dir / 'extension.yml').is_file())
            if not (extension_dir / 'extension.yml').is_file():
                continue
            for path in declared_files(extension_dir):
                with self.subTest(msg=f'declared extension file exists: {path.relative_to(REPO_ROOT)}'):
                    self.assertTrue(path.is_file(), f'declared extension file not found: {path}')
            commands = record.get('registered_commands')
            if not isinstance(commands, dict):
                continue
            claude_commands = commands.get('claude', [])
            if not isinstance(claude_commands, list):
                continue
            for command in claude_commands:
                if not isinstance(command, str):
                    continue
                registered_commands.add(command)
                with self.subTest(msg=f'registered Claude extension command resolves: {command}'):
                    self.assertTrue(claude_skill_path(command).is_file(), f'generated Claude skill not found for {command}: {claude_skill_path(command)}')
        hook_commands = {match.group(1) for line in HOOKS_PATH.read_text(encoding='utf-8').splitlines() if (match := HOOK_COMMAND.match(line)) is not None}
        for command in sorted(hook_commands):
            with self.subTest(msg=f'configured extension hook resolves: {command}'):
                self.assertIn(command, registered_commands)
        verify = extensions.get('verify')
        with self.subTest(msg='Verify extension is pinned to repaired v1.0.3 payload'):
            self.assertIsInstance(verify, dict)
            self.assertEqual(verify.get('version') if isinstance(verify, dict) else None, '1.0.3')
        verify_loader = EXTENSIONS_ROOT / 'verify' / 'scripts' / 'bash' / 'load-config.sh'
        with self.subTest(msg='Verify Bash loader retains its declared executable mode'):
            self.assertTrue(verify_loader.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH), f'declared executable is not executable: {verify_loader}')
# Contracts transferred from validate-process-gitattributes.py.
GITATTRIBUTES = REPO_ROOT / '.gitattributes'

def rules_scoped(text: str) -> bool:
    """Return True iff EVERY ``linguist-generated`` line is scoped to a
    ``.process/`` path segment. Mirrors the bash ``rules_scoped`` predicate: skip
    comment (``#``-leading) and blank lines; a ``linguist-generated`` line is
    scoped when it contains ``/.process/`` or starts with ``.process/`` (the bash
    ``*/.process/*|.process/*`` case), otherwise the file is broadened. A file
    with no ``linguist-generated`` lines is scoped (nothing to broaden)."""
    for line in text.splitlines():
        if line.startswith('#') or line == '':
            continue
        if 'linguist-generated' in line:
            if '/.process/' in line or line.startswith('.process/'):
                continue
            return False
    return True

class ValidateProcessGitattributes(unittest.TestCase):

    def test_gitattributes_scope(self) -> None:
        with self.subTest(msg='repo-root .gitattributes exists'):
            self.assertTrue(GITATTRIBUTES.is_file(), f'file not found: {GITATTRIBUTES}')
        if GITATTRIBUTES.is_file():
            content = GITATTRIBUTES.read_text(encoding='utf-8')
            with self.subTest(msg='at least one linguist-generated rule is present'):
                self.assertIn('linguist-generated', content, 'no linguist-generated rule found in repo-root .gitattributes')
            with self.subTest(msg='every linguist-generated rule is scoped to .process/'):
                self.assertTrue(rules_scoped(content), 'a linguist-generated rule is broadened beyond .process/ (could match a CONTRACT artifact)')
        with self.subTest(msg='scoped rule passes (SC-005 positive case)'):
            self.assertTrue(rules_scoped('**/.process/** linguist-generated=true\n'))
        with self.subTest(msg='broadened rule fails (SC-005 negative case)'):
            self.assertFalse(rules_scoped('**/* linguist-generated=true\n'))
        with self.subTest(msg='rule for a dir ending in .process (foo.process/) fails — not the .process/ dir'):
            self.assertFalse(rules_scoped('**/foo.process/** linguist-generated=true\n'))


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-spec-templates-and-extensions")


if __name__ == "__main__":
    raise SystemExit(main())
