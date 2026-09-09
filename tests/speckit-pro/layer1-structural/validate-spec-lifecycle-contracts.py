#!/usr/bin/env python3
"""Consolidated Layer 1 contracts owned by validate-spec-lifecycle-contracts.py."""

from __future__ import annotations

from pathlib import Path
from typing import TextIO
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for _import_root in (LIB_DIR, PLUGIN_ROOT):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))

from test_result import run_counted

# Contracts transferred from validate-scripts.py.
SCRIPT_SUFFIXES = {'.sh', '.ps1', '.bat', '.cmd'}
SHELL_SHEBANG_RE = re.compile('^#!.*\\b(?:bash|sh|zsh|powershell|pwsh)\\b', re.IGNORECASE)
ROADMAP_TEMPLATE = PLUGIN_ROOT / 'skills/speckit-coach/templates/technical-roadmap-template.md'
SPEC_TEMPLATES = (REPO_ROOT / '.specify/presets/speckit-pro-reviewability/templates/spec-template.md', REPO_ROOT / '.specify/templates/spec-template.md')
PRESET_PLAN_TEMPLATE = REPO_ROOT / '.specify/presets/speckit-pro-reviewability/templates/plan-template.md'

def _rel_repo(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()

def _live_script_count(root: Path) -> int:
    count = 0
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        if path.suffix.lower() in SCRIPT_SUFFIXES:
            count += 1
            continue
        if path.suffix:
            continue
        try:
            first_line = path.open('r', encoding='utf-8').readline(4096)
        except (OSError, UnicodeDecodeError):
            continue
        if SHELL_SHEBANG_RE.search(first_line):
            count += 1
    return count

class ValidateScripts(unittest.TestCase):

    def test_001_zero_live_script_files(self) -> None:
        with self.subTest(msg='speckit-pro: contains zero live shell/command script files'):
            script_count = _live_script_count(PLUGIN_ROOT)
            self.assertEqual(0, script_count, f'expected zero live plugin script files, found {script_count}')

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
# Contracts transferred from validate-specify-extensions.py.
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
# Contracts transferred from validate-moc-orphan.py.
FIX = Path(__file__).resolve().parent / 'fixtures' / 'moc'
GATE_VERSION = 1

def _moc_fm_block(file: Path) -> list[str]:
    if not file.is_file() or not os.access(file, os.R_OK):
        return []
    try:
        lines = file.read_text(encoding='utf-8', errors='replace').splitlines()
    except OSError:
        return []
    if not lines or lines[0] != '---':
        return []
    block: list[str] = []
    for line in lines[1:]:
        if line == '---':
            break
        block.append(line)
    return block

def _strip_frontmatter_value(value: str) -> str:
    value = value.lstrip()
    value = re.sub('\\s+#.*$', '', value)
    value = value.rstrip()
    if value.startswith('"'):
        value = value[1:]
        if value.endswith('"'):
            value = value[:-1]
    elif value.startswith("'"):
        value = value[1:]
        if value.endswith("'"):
            value = value[:-1]
    return value

def validate_moc_orphan_moc_frontmatter_field(file: Path, field: str) -> str | None:
    prefix = re.compile(f'^\\s*{re.escape(field)}:')
    for line in _moc_fm_block(file):
        if prefix.match(line):
            return _strip_frontmatter_value(line.split(':', 1)[1])
    return None

def _raw_frontmatter_field(file: Path, field: str) -> str | None:
    prefix = re.compile(f'^\\s*{re.escape(field)}:')
    for line in _moc_fm_block(file):
        if prefix.match(line):
            raw = line.split(':', 1)[1]
            raw = raw.lstrip()
            raw = re.sub('\\s+#.*$', '', raw)
            return raw.rstrip()
    return None

def validate_moc_orphan_moc_is_gated(file: Path) -> bool:
    version = validate_moc_orphan_moc_frontmatter_field(file, 'structureVersion')
    if version is None or not re.fullmatch('[0-9]+', version):
        return False
    raw_token = _raw_frontmatter_field(file, 'structureVersion')
    if raw_token is None or not re.fullmatch('[0-9]+', raw_token):
        return False
    return int(version) >= GATE_VERSION

def moc_normalize(value: str) -> tuple[str, str]:
    parts = value.lower().split('-')
    first = parts[0] if parts else ''
    if re.fullmatch('[a-z]+', first):
        namespace = first
        number_suffix = parts[1] if len(parts) > 1 else ''
    else:
        namespace = 'spec'
        number_suffix = first
    return (namespace, number_suffix)

def moc_id_match(left: str, right: str) -> bool:
    return moc_normalize(left) == moc_normalize(right)

def moc_up_well_formed(file: Path) -> bool:
    up = validate_moc_orphan_moc_frontmatter_field(file, 'up')
    if not up:
        return False
    if '[[' in up:
        return False
    before, sep, after = up.partition('](')
    if not sep or '[' not in before or ')' not in after:
        return False
    target = after.split(')', 1)[0].strip()
    if not target:
        return False
    if '://' in target or target.startswith('//') or target.startswith('/') or target.startswith('#'):
        return False
    before_slash = target.split('/', 1)[0]
    return ':' not in before_slash

def moc_specid_matches_dir(file: Path, dir_name: str) -> bool:
    spec_id = validate_moc_orphan_moc_frontmatter_field(file, 'spec_id')
    return bool(spec_id) and moc_id_match(spec_id, dir_name)

def _iter_spec_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted((child for child in root.iterdir() if child.is_dir()), key=lambda path: path.name)

def validate_moc_orphan_scan_root(root: Path, *, stdout: TextIO=sys.stdout, stderr: TextIO=sys.stderr) -> int:
    violation_count = 0
    for spec_dir in _iter_spec_dirs(root):
        if '.process' in spec_dir.parts:
            continue
        marker = spec_dir / 'SPEC-MOC.md'
        if marker.exists() and (not os.access(marker, os.R_OK)):
            print(f'WARNING: validate-moc-orphan.py: skipping unreadable marker {marker.as_posix()}', file=stderr)
            continue
        if not validate_moc_orphan_moc_is_gated(marker):
            continue
        dir_name = spec_dir.name
        marker_text = marker.as_posix()
        if not moc_up_well_formed(marker):
            print(f'VIOLATION [orphan]: {marker_text} — up: missing, empty, or ill-formed (not a well-formed relative [](...) link)', file=stdout)
            violation_count += 1
        if not moc_specid_matches_dir(marker, dir_name):
            print(f'VIOLATION [spec_id]: {marker_text} — spec_id absent/empty or does not namespace-match directory "{dir_name}"', file=stdout)
            violation_count += 1
    return violation_count

class ValidateMocOrphan(unittest.TestCase):

    def test_moc_orphan_lint(self) -> None:
        with self.subTest(msg='valid relative up: passes'):
            self.assertTrue(moc_up_well_formed(FIX / 'orphan' / 'orphan-valid' / 'SPEC-MOC.md'))
        with self.subTest(msg='missing up: is a violation'):
            self.assertFalse(moc_up_well_formed(FIX / 'orphan' / 'orphan-missing-up' / 'SPEC-MOC.md'))
        with self.subTest(msg='empty up: is a violation'):
            self.assertFalse(moc_up_well_formed(FIX / 'orphan' / 'orphan-empty-up' / 'SPEC-MOC.md'))
        with self.subTest(msg='wikilink up: is a violation (ill-formed for orphan)'):
            self.assertFalse(moc_up_well_formed(FIX / 'orphan' / 'orphan-wikilink-up' / 'SPEC-MOC.md'))
        with self.subTest(msg='absolute-URL up: is a violation (not a relative target)'):
            self.assertFalse(moc_up_well_formed(FIX / 'orphan' / 'orphan-absolute-url-up' / 'SPEC-MOC.md'))
        with self.subTest(msg='root-absolute up: is a violation (not a relative target)'):
            self.assertFalse(moc_up_well_formed(FIX / 'orphan' / 'orphan-root-absolute-up' / 'SPEC-MOC.md'))
        with self.subTest(msg='protocol-relative up: is a violation (not a relative target)'):
            self.assertFalse(moc_up_well_formed(FIX / 'orphan' / 'orphan-protocol-relative-up' / 'SPEC-MOC.md'))
        with self.subTest(msg='anchor-only up: is a violation (not a relative target)'):
            self.assertFalse(moc_up_well_formed(FIX / 'orphan' / 'orphan-anchor-only-up' / 'SPEC-MOC.md'))
        with self.subTest(msg='root-absolute up: with a LEADING SPACE is still a violation (trimmed)'):
            self.assertFalse(moc_up_well_formed(FIX / 'orphan' / 'orphan-leading-space-up' / 'SPEC-MOC.md'))
        with self.subTest(msg='schemed up: (mailto:/tel:) is a violation (not a relative target)'):
            self.assertFalse(moc_up_well_formed(FIX / 'orphan' / 'orphan-scheme-up' / 'SPEC-MOC.md'))
        with self.subTest(msg='non-MOC docs in a gated spec are not required to carry up: (scan clean)'):
            self.assertEqual(0, validate_moc_orphan_scan_root(FIX / 'scan-clean', stdout=io.StringIO()))
        with self.subTest(msg='no structureVersion -> SKIP (not gated)'):
            self.assertFalse(validate_moc_orphan_moc_is_gated(FIX / 'gate' / 'gate-no-version' / 'SPEC-MOC.md'))
        with self.subTest(msg='structureVersion 0 (< 1) -> SKIP'):
            self.assertFalse(validate_moc_orphan_moc_is_gated(FIX / 'gate' / 'gate-version-zero' / 'SPEC-MOC.md'))
        with self.subTest(msg='quoted "1" -> SKIP (non-bare-integer)'):
            self.assertFalse(validate_moc_orphan_moc_is_gated(FIX / 'gate' / 'gate-version-quoted' / 'SPEC-MOC.md'))
        with self.subTest(msg='decimal 1.0 -> SKIP (non-bare-integer)'):
            self.assertFalse(validate_moc_orphan_moc_is_gated(FIX / 'gate' / 'gate-version-decimal' / 'SPEC-MOC.md'))
        with self.subTest(msg='non-numeric text -> SKIP (non-bare-integer)'):
            self.assertFalse(validate_moc_orphan_moc_is_gated(FIX / 'gate' / 'gate-version-text' / 'SPEC-MOC.md'))
        with self.subTest(msg='no --- fence -> SKIP (unparseable frontmatter)'):
            self.assertFalse(validate_moc_orphan_moc_is_gated(FIX / 'gate' / 'gate-no-fence' / 'SPEC-MOC.md'))
        with self.subTest(msg='no SPEC-MOC.md in dir -> SKIP (scan clean, no marker globbed)'):
            self.assertEqual(0, validate_moc_orphan_scan_root(FIX / 'gate', stdout=io.StringIO()))
        with self.subTest(msg='bare integer 1 WITH inline # comment -> GATED (guards inline-comment false-skip)'):
            self.assertTrue(validate_moc_orphan_moc_is_gated(FIX / 'gate' / 'gate-version-commented' / 'SPEC-MOC.md'))
        with self.subTest(msg='spec_id namespace-matches dir (prsg,002) -> PASS'):
            self.assertTrue(moc_specid_matches_dir(FIX / 'specid' / 'prsg-002-something' / 'SPEC-MOC.md', 'prsg-002-something'))
        with self.subTest(msg='spec_id namespace-matches dir (spec,006a) -> PASS'):
            self.assertTrue(moc_specid_matches_dir(FIX / 'specid' / '006a-uat-skeleton' / 'SPEC-MOC.md', '006a-uat-skeleton'))
        with self.subTest(msg='spec_id (spec,002) vs dir (prsg,002) collision -> VIOLATION'):
            self.assertFalse(moc_specid_matches_dir(FIX / 'specid' / 'prsg-002-collision' / 'SPEC-MOC.md', 'prsg-002-collision'))
        with self.subTest(msg='spec_id 013a1 vs dir 013a near-miss -> VIOLATION'):
            self.assertFalse(moc_specid_matches_dir(FIX / 'specid' / '013a' / 'SPEC-MOC.md', '013a'))
        with self.subTest(msg='absent spec_id in gated marker -> VIOLATION'):
            self.assertFalse(moc_specid_matches_dir(FIX / 'specid' / 'specid-absent' / 'SPEC-MOC.md', 'specid-absent'))
        with self.subTest(msg='empty spec_id in gated marker -> VIOLATION'):
            self.assertFalse(moc_specid_matches_dir(FIX / 'specid' / 'specid-empty' / 'SPEC-MOC.md', 'specid-empty'))
        dogfood_marker = FIX / 'specid' / 'prsg-002-something' / 'SPEC-MOC.md'
        with self.subTest(msg='Dogfood PRSG marker is version-gated (observable, not inferred from exit 0)'):
            self.assertTrue(validate_moc_orphan_moc_is_gated(dogfood_marker), 'fixture SPEC-MOC.md is NOT gated')
        with self.subTest(msg='Dogfood PRSG marker spec_id namespace-matches its directory'):
            self.assertTrue(moc_specid_matches_dir(dogfood_marker, 'prsg-002-something'))
        with self.subTest(msg='real-tree scan of docs/ai/specs/ is clean (legacy skipped)'):
            self.assertEqual(0, validate_moc_orphan_scan_root(REPO_ROOT / 'docs' / 'ai' / 'specs', stdout=io.StringIO()))
        with self.subTest(msg='real-tree scan of specs/ is clean (active markers pass, legacy skipped)'):
            self.assertEqual(0, validate_moc_orphan_scan_root(REPO_ROOT / 'specs', stdout=io.StringIO()))
# Contracts transferred from validate-moc-stale-index.py.
FIXTURES = Path(__file__).resolve().parent / 'fixtures' / 'moc'
LINK_RE = re.compile('\\[[^\\][]*\\]\\(([^()]*)\\)')
SCHEME_RE = re.compile('^[A-Za-z][A-Za-z0-9+.-]*://')

def _read_text(path: Path) -> str | None:
    if not path.is_file() or not os.access(path, os.R_OK):
        return None
    try:
        return path.read_text(encoding='utf-8')
    except OSError:
        return None

def _frontmatter_block(path: Path) -> list[str]:
    text = _read_text(path)
    if text is None:
        return []
    lines = text.splitlines()
    if not lines or lines[0] != '---':
        return []
    block: list[str] = []
    for line in lines[1:]:
        if line == '---':
            break
        block.append(line)
    return block

def _strip_inline_comment(value: str) -> str:
    return re.sub('\\s+#.*$', '', value).strip()

def validate_moc_stale_index_moc_frontmatter_field(path: Path, field: str) -> str | None:
    for line in _frontmatter_block(path):
        if re.match(f'^\\s*{re.escape(field)}:', line):
            value = line.split(':', 1)[1]
            value = _strip_inline_comment(value)
            if len(value) >= 2 and value[0] == value[-1] and (value[0] in {"'", '"'}):
                value = value[1:-1]
            return value
    return None

def validate_moc_stale_index_moc_is_gated(marker: Path) -> bool:
    if not marker.is_file() or not os.access(marker, os.R_OK):
        return False
    version = validate_moc_stale_index_moc_frontmatter_field(marker, 'structureVersion')
    if version is None or not version.isdigit():
        return False
    raw_token: str | None = None
    for line in _frontmatter_block(marker):
        if re.match('^\\s*structureVersion:', line):
            raw_token = _strip_inline_comment(line.split(':', 1)[1])
            break
    if raw_token is None or not raw_token.isdigit():
        return False
    return int(version) >= 1

def stale_body(marker: Path) -> str:
    text = _read_text(marker)
    if text is None:
        return ''
    lines = text.splitlines()
    if not lines or lines[0] != '---':
        return text
    body: list[str] = []
    in_frontmatter = True
    for line in lines[1:]:
        if in_frontmatter and line == '---':
            in_frontmatter = False
            continue
        if in_frontmatter:
            continue
        body.append(line)
    return '\n'.join(body)

def stale_link_targets(marker: Path) -> list[str]:
    if not marker.is_file() or not os.access(marker, os.R_OK):
        return []
    targets: list[str] = []
    up_value = validate_moc_stale_index_moc_frontmatter_field(marker, 'up') or ''
    targets.extend(LINK_RE.findall(up_value))
    targets.extend(LINK_RE.findall(stale_body(marker)))
    return targets

def stale_is_relative_ref(target: str) -> bool:
    if not target:
        return False
    if target.startswith('#'):
        return False
    if target.startswith('/'):
        return False
    if SCHEME_RE.match(target):
        return False
    if target.startswith('mailto:'):
        return False
    return True

def stale_target_resolves(marker_dir: Path, target: str) -> bool:
    target = target.split('#', 1)[0]
    target = target.split('?', 1)[0]
    if not target:
        return False
    path = marker_dir / target
    return path.is_file() and os.access(path, os.R_OK)

def moc_links_resolve(marker: Path) -> bool:
    text = _read_text(marker)
    if text is None:
        return False
    if '[[' in text:
        return False
    marker_dir = marker.parent
    for target in stale_link_targets(marker):
        if not stale_is_relative_ref(target):
            continue
        if not stale_target_resolves(marker_dir, target):
            return False
    return True

def validate_moc_stale_index_scan_root(root: Path, *, emit: bool=False) -> list[str]:
    if not root.is_dir():
        return []
    violations: list[str] = []
    for spec_dir in sorted((path for path in root.iterdir() if path.is_dir()), key=lambda path: path.as_posix()):
        if spec_dir.name == '.process' or '.process' in spec_dir.parts:
            continue
        marker = spec_dir / 'SPEC-MOC.md'
        if marker.exists() and (not os.access(marker, os.R_OK)):
            print(f'WARNING: validate-moc-stale-index.py: skipping unreadable marker {marker}', file=sys.stderr)
            continue
        if not validate_moc_stale_index_moc_is_gated(marker):
            continue
        text = _read_text(marker) or ''
        if '[[' in text:
            violations.append(f'VIOLATION [stale-index/wikilink]: {marker} — contains a [[wikilink]] (wikilinks are not allowed in a gated MOC)')
        for target in stale_link_targets(marker):
            if not stale_is_relative_ref(target):
                continue
            if not stale_target_resolves(marker.parent, target):
                violations.append(f'VIOLATION [stale-index/link]: {marker} — relative link target does not resolve to a regular readable file: {target}')
    if emit:
        for violation in violations:
            print(violation)
    return violations

def _with_broken_symlink() -> None:
    broken_link = FIXTURES / 'stale/stale-broken-symlink/broken-link.md'
    try:
        if broken_link.exists() or broken_link.is_symlink():
            broken_link.unlink()
        broken_link.symlink_to('this-target-does-not-exist.md')
    except (NotImplementedError, OSError):
        if broken_link.exists() or broken_link.is_symlink():
            broken_link.unlink(missing_ok=True)

def _cleanup_broken_symlink() -> None:
    broken_link = FIXTURES / 'stale/stale-broken-symlink/broken-link.md'
    if broken_link.exists() or broken_link.is_symlink():
        broken_link.unlink()

class ValidateMocStaleIndex(unittest.TestCase):

    def test_stale_index_lint(self) -> None:
        with self.subTest(msg='all relative targets resolve (up: + body link) -> PASS'):
            self.assertTrue(moc_links_resolve(FIXTURES / 'stale/stale-valid/SPEC-MOC.md'))
        with self.subTest(msg='an absent relative body-link target -> VIOLATION'):
            self.assertFalse(moc_links_resolve(FIXTURES / 'stale/stale-absent-link/SPEC-MOC.md'))
        with self.subTest(msg='a relative target that is a DIRECTORY (not a regular file) -> VIOLATION'):
            self.assertFalse(moc_links_resolve(FIXTURES / 'stale/stale-dir-target/SPEC-MOC.md'))
        with self.subTest(msg='a relative target that is a BROKEN SYMLINK -> VIOLATION (distinct from absent)'):
            self.assertFalse(moc_links_resolve(FIXTURES / 'stale/stale-broken-symlink/SPEC-MOC.md'))
        with self.subTest(msg='a [[wikilink]] anywhere in a gated MOC -> VIOLATION'):
            self.assertFalse(moc_links_resolve(FIXTURES / 'stale/stale-wikilink/SPEC-MOC.md'))
        with self.subTest(msg='a non-gated marker with a dangling link is skipped (exempt-before-content)'):
            self.assertEqual(0, len(validate_moc_stale_index_scan_root(FIXTURES / 'stale-exempt')))
        with self.subTest(msg='scan of the stale fixture tree counts the negative cases as violations'):
            self.assertEqual(4, len(validate_moc_stale_index_scan_root(FIXTURES / 'stale')))
        dogfood_marker = FIXTURES / 'stale/stale-valid/SPEC-MOC.md'
        with self.subTest(msg='Dogfood MOC marker is version-gated (observable, not inferred)'):
            self.assertTrue(validate_moc_stale_index_moc_is_gated(dogfood_marker))
        with self.subTest(msg='Dogfood MOC marker links all resolve (up: and body links)'):
            self.assertTrue(moc_links_resolve(dogfood_marker))
        with self.subTest(msg='real-tree scan of docs/ai/specs/ is clean (legacy skipped)'):
            self.assertEqual(0, len(validate_moc_stale_index_scan_root(REPO_ROOT / 'docs/ai/specs')))
        with self.subTest(msg='real-tree scan of specs/ is clean (active markers pass, legacy skipped)'):
            self.assertEqual(0, len(validate_moc_stale_index_scan_root(REPO_ROOT / 'specs')))
# Contracts transferred from validate-spec-index-determinism.py.
RUNNER_DIR = REPO_ROOT / 'speckit-pro' / 'speckit_pro_runner'
FIXTURE_ROOT = REPO_ROOT / 'tests' / 'speckit-pro' / 'layer1-structural' / 'fixtures' / 'spec-index' / 'determinism'
TEMPLATE = REPO_ROOT / 'speckit-pro' / 'skills' / 'speckit-coach' / 'templates' / 'roadmap-moc-template.md'
REGISTRY_REQ = {'schema_version': '1.0', 'request_id': 'l1-helper-registry', 'helper_id': 'helper-registry-dispatch', 'operation': 'helper-registry-dispatch', 'mode': 'read_only', 'inputs': {}}
MUTATION_REGISTRY_REQ = {'schema_version': '1.0', 'request_id': 'l1-mutation-registry', 'helper_id': 'mutation-registry-dispatch', 'operation': 'mutation-registry-dispatch', 'mode': 'read_only', 'inputs': {}}
CHECK_REQ = {'schema_version': '1.0', 'request_id': 'l1-generate-spec-index-check', 'helper_id': 'generate-spec-index-check', 'operation': 'generate-spec-index-check', 'mode': 'read_only', 'inputs': {'repo_root': 'tests/speckit-pro/layer1-structural/fixtures/spec-index/determinism'}}

def _runner_request(payload: dict[str, object]) -> str:
    env = os.environ.copy()
    plugin_root = REPO_ROOT / 'speckit-pro'
    existing = env.get('PYTHONPATH')
    env['PYTHONPATH'] = plugin_root.as_posix() if not existing else f'{plugin_root.as_posix()}{os.pathsep}{existing}'
    completed = subprocess.run([sys.executable, '-m', 'speckit_pro_runner'], input=json.dumps(payload), text=True, capture_output=True, cwd=REPO_ROOT, env=env, shell=False, check=False)
    return completed.stdout

def _snapshot(root: Path) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    for path in sorted((p for p in root.rglob('*') if p.is_file()), key=lambda p: p.relative_to(root).as_posix()):
        digest = hashlib.sha1(path.read_bytes()).hexdigest()
        records.append((path.relative_to(root).as_posix(), digest))
    return records

def _first_line_containing(path: Path, needle: str) -> str:
    if not path.is_file():
        return ''
    for line in path.read_text(encoding='utf-8').splitlines():
        if needle in line:
            return line
    return ''

class ValidateSpecIndexDeterminism(unittest.TestCase):

    def test_spec_index_helper_contract(self) -> None:
        with self.subTest(msg='runner package exists at the contracted path'):
            self.assertTrue((RUNNER_DIR / '__main__.py').is_file(), f"FAIL: runner entrypoint not found at {RUNNER_DIR / '__main__.py'}")
        registry_json = _runner_request(REGISTRY_REQ)
        with self.subTest(msg='read-only registry dispatch succeeds'):
            self.assertIn('"status":"ok"', registry_json)
        with self.subTest(msg='generate-spec-index-check is registered'):
            self.assertIn('"helper_id":"generate-spec-index-check"', registry_json)
        with self.subTest(msg='generate-spec-index-check is Python-authoritative'):
            self.assertIn('"promotion_status":"python_authoritative"', registry_json)
        mutation_registry_json = _runner_request(MUTATION_REGISTRY_REQ)
        with self.subTest(msg='mutation registry dispatch succeeds'):
            self.assertIn('"status":"ok"', mutation_registry_json)
        mutation_registry = json.loads(mutation_registry_json)
        write_entry = next((record for record in mutation_registry['data']['helpers'] if record['helper_id'] == 'generate-spec-index-write'))
        with self.subTest(msg='generate-spec-index-write is registered'):
            self.assertIn('"helper_id":"generate-spec-index-write"', mutation_registry_json)
        with self.subTest(msg='generate-spec-index-write is promoted with an authoritative request'):
            self.assertEqual(write_entry['promotion_status'], 'golden_only')
            self.assertTrue(write_entry['authoritative_command'])
        snap_before = _snapshot(FIXTURE_ROOT)
        check_json = _runner_request(CHECK_REQ)
        snap_after = _snapshot(FIXTURE_ROOT)
        with self.subTest(msg='generate-spec-index-check detects stale rendered output with exit 1'):
            self.assertIn('"status":"expected_failure"', check_json)
            self.assertIn('"exit_code":1', check_json)
        with self.subTest(msg='generate-spec-index-check reports the helper id'):
            self.assertIn('"helper_id":"generate-spec-index-check"', check_json)
        with self.subTest(msg='generate-spec-index-check uses shell:false'):
            self.assertIn('"shell":false', check_json)
        with self.subTest(msg='generate-spec-index-check records writes_state:false'):
            self.assertIn('"writes_state":false', check_json)
        with self.subTest(msg='generate-spec-index-check leaves fixture bytes unchanged'):
            self.assertEqual(snap_before, snap_after, 'read-only helper must not mutate spec-index fixtures')
        with self.subTest(msg='roadmap-MOC template exists at the contracted path'):
            self.assertTrue(TEMPLATE.is_file(), f'FAIL: roadmap-MOC template not found at {TEMPLATE}')
        tpl_index_start = _first_line_containing(TEMPLATE, 'GENERATED:INDEX:START')
        tpl_index_end = _first_line_containing(TEMPLATE, 'GENERATED:INDEX:END')
        with self.subTest(msg='template INDEX sentinels are present'):
            self.assertTrue(tpl_index_start and tpl_index_end, 'missing INDEX sentinel in roadmap-MOC template')
        with self.subTest(msg='template INDEX:START keeps the sentinel grammar'):
            self.assertEqual('<!-- GENERATED:INDEX:START (do not edit; regenerated by generate-spec-index) -->', tpl_index_start, 'template INDEX:START sentinel drifted')
        with self.subTest(msg='template INDEX:END keeps the sentinel grammar'):
            self.assertEqual('<!-- GENERATED:INDEX:END -->', tpl_index_end, 'template INDEX:END sentinel drifted')
# Contracts transferred from validate-installed-interpreter-contract.py.
EXCLUDED_NAMES = frozenset({'CHANGELOG.md'})
HARDCODED_INTERPRETER = re.compile('(?<![\\w./-])(?:python[0-9.]*|py)\\s+(?=[-\\w\\"\'/$])')
RESOLVED_TOKEN = 'resolved_python'
COVERAGE_SCRIPT = 'validate-autopilot-phase-coverage.py'
COVERAGE_RULE_FLAG = '--rule status-evidence'
COVERAGE_FLAGS = ('--workflow', '--state')
PLATFORM_ROOTS = {'Claude': 'speckit-pro/skills/', 'Codex': 'speckit-pro/codex-skills/'}
POSITIVE_CASES = ('python3 "runner helper validate-autopilot-phase-coverage.py" --workflow "$WORKFLOW_FILE"', 'python3 -m json.tool docs/ai/specs/.process/autopilot-state.json', 'python3 tests/speckit-pro/run-all.py', '- `python -m venv .venv`', 'Run python3.11 scripts/build.py to regenerate', 'py -3 scripts/build.py')
NEGATIVE_CASES = ('resolved_python -m speckit_pro_runner < request.json', 'resolved_python "<plugin-root>/skills/speckit-autopilot/scripts/validate.py" --rule x', '`[resolved_python, "-m", "speckit_pro_runner"]`, send one JSON request on', 'Keep repository-owned tooling on Python 3.11+ standard library.', 'resolve Python 3.11 or newer, invoke', '#!/usr/bin/env python3', 'the interpreter at /usr/bin/python3 is not guaranteed', '`resolved_python` is the Python 3.11+ interpreter resolved by the installed')

def shipped_markdown() -> list[Path]:
    """Every shipped plugin markdown file, in deterministic order."""
    return sorted((path for path in PLUGIN_ROOT.rglob('*.md') if path.name not in EXCLUDED_NAMES))

def hardcoded_interpreter_errors() -> list[str]:
    """Plain-English `file:line` strings for every hardcoded interpreter command."""
    errors: list[str] = []
    for path in shipped_markdown():
        display = path.relative_to(REPO_ROOT).as_posix()
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f'{display}: unreadable ({exc})')
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            for match in HARDCODED_INTERPRETER.finditer(line):
                errors.append(f'{display}:{number}: {match.group(0).strip()!r} hardcodes an interpreter; the Installed Runtime Contract requires {RESOLVED_TOKEN!r}')
    return errors

def coverage_invocations() -> list[tuple[str, int, str]]:
    """Every shipped line that tells an agent to run the phase-coverage guard."""
    found: list[tuple[str, int, str]] = []
    for path in shipped_markdown():
        display = path.relative_to(REPO_ROOT).as_posix()
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if COVERAGE_SCRIPT in line and any((flag in line for flag in COVERAGE_FLAGS)):
                found.append((display, number, line))
    return found

def coverage_invocation_errors() -> list[str]:
    """Every discovered guard invocation must be resolvable and identically scoped."""
    invocations = coverage_invocations()
    errors: list[str] = []
    for platform, root in sorted(PLATFORM_ROOTS.items()):
        if not any((display.startswith(root) for display, _, _ in invocations)):
            errors.append(f'no {COVERAGE_SCRIPT} invocation found under {root} — the {platform} distribution would run no coverage guard at all')
    for display, number, line in invocations:
        if RESOLVED_TOKEN not in line:
            errors.append(f'{display}:{number}: guard invocation does not name {RESOLVED_TOKEN!r}, so it names an interpreter the Installed Runtime Contract cannot resolve')
        if COVERAGE_RULE_FLAG not in line:
            errors.append(f'{display}:{number}: guard invocation omits {COVERAGE_RULE_FLAG!r}, so this call site gates on checks the others do not')
    return errors

class ValidateInstalledInterpreterContract(unittest.TestCase):

    def test_installed_interpreter_contract(self) -> None:
        files = shipped_markdown()
        with self.subTest(msg='shipped plugin markdown is discoverable'):
            self.assertTrue(files, f'no *.md files under {PLUGIN_ROOT}')
        with self.subTest(msg='no shipped prose hardcodes a Python interpreter name'):
            errors = hardcoded_interpreter_errors()
            self.assertEqual([], errors, '\n'.join(errors))
        with self.subTest(msg='every phase-coverage guard invocation is resolvable and identically scoped'):
            errors = coverage_invocation_errors()
            self.assertEqual([], errors, '\n'.join(errors))
        with self.subTest(msg='guard call-site discovery separates invocations from prose'):
            invocations = {display for display, _, _ in coverage_invocations()}
            mentions = {path.relative_to(REPO_ROOT).as_posix() for path in shipped_markdown() if COVERAGE_SCRIPT in path.read_text(encoding='utf-8')}
            self.assertTrue(invocations, f'no {COVERAGE_SCRIPT} invocation discovered')
            self.assertTrue(invocations <= mentions, 'discovery reported an invocation in a file that never names the script')
        with self.subTest(msg='matcher catches every hardcoded-interpreter form'):
            missed = [case for case in POSITIVE_CASES if not HARDCODED_INTERPRETER.search(case)]
            self.assertEqual([], missed, '\n'.join(missed))
        with self.subTest(msg='matcher accepts resolved_python, shebangs, and Python-version prose'):
            matched = [case for case in NEGATIVE_CASES if HARDCODED_INTERPRETER.search(case)]
            self.assertEqual([], matched, '\n'.join(matched))

scan_moc_orphans = validate_moc_orphan_scan_root
scan_stale_moc_links = validate_moc_stale_index_scan_root

def run_moc_orphan(argv: list[str]) -> int:
    if argv:
        try:
            violations = scan_moc_orphans(Path(argv[0]))
        except Exception as exc:
            print(f"ERROR: validate-spec-lifecycle-contracts.py --moc-orphan: internal failure ({exc.__class__.__name__}: {exc})", file=sys.stderr)
            return 2
        return 1 if violations > 0 else 0
    return run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(ValidateMocOrphan), label="validate-spec-lifecycle-contracts", allow_live_specs=True)

def run_moc_stale(argv: list[str]) -> int:
    if argv:
        try:
            violations = scan_stale_moc_links(Path(argv[0]), emit=True)
        except Exception as exc:
            print(f"ERROR: validate-spec-lifecycle-contracts.py --moc-stale: internal failure ({exc})", file=sys.stderr)
            return 2
        return 1 if violations else 0
    _with_broken_symlink()
    try:
        try:
            return run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(ValidateMocStaleIndex), label="validate-spec-lifecycle-contracts", allow_live_specs=True)
        except Exception as exc:
            print(f"ERROR: validate-spec-lifecycle-contracts.py --moc-stale: internal failure ({exc})", file=sys.stderr)
            return 2
    finally:
        _cleanup_broken_symlink()

def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "--moc-orphan":
        return run_moc_orphan(args[1:])
    if args and args[0] == "--moc-stale":
        return run_moc_stale(args[1:])
    if args:
        print(f"ERROR: unknown lifecycle mode: {args[0]}", file=sys.stderr)
        return 2
    _with_broken_symlink()
    try:
        suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
        return run_counted(suite, label="validate-spec-lifecycle-contracts", allow_live_specs=True)
    finally:
        _cleanup_broken_symlink()

if __name__ == "__main__":
    raise SystemExit(main())
