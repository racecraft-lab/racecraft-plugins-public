#!/usr/bin/env python3
"""Consolidated Layer 1 contracts owned by validate-payload-contracts.py."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json
import os
import re
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

# Contracts transferred from validate-plugin-payload.py.
SOURCE_ROOT = REPO_ROOT / 'speckit-pro'
BUILDER = REPO_ROOT / 'scripts' / 'build-plugin-payloads.py'
CLAUDE_PAYLOAD = REPO_ROOT / 'dist' / 'claude' / 'speckit-pro'
CODEX_PAYLOAD = REPO_ROOT / 'dist' / 'codex' / 'speckit-pro'
PATH_ESCAPE_RE = re.compile('\\.\\./\\.\\./(?:skills|codex-skills)/|\\.\\./\\.\\./\\.\\./(?:skills|codex-skills)/')

def run_builder() -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(BUILDER)], cwd=REPO_ROOT, text=True, capture_output=True, shell=False, check=False)

def _display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()

def load_json_file(path: Path) -> dict:
    try:
        text = path.read_text(encoding='utf-8')
    except OSError as exc:
        raise AssertionError(f'unable to read {_display_path(path)}: {exc.__class__.__name__}: {exc}') from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise AssertionError(f'malformed JSON in {_display_path(path)}: {exc.msg} (line {exc.lineno}, column {exc.colno})') from exc

def count_skill_entrypoints(root: Path) -> int:
    """Mirror `find <root> -mindepth 2 -maxdepth 2 -type f -name SKILL.md | wc -l`."""
    if not root.is_dir():
        return 0
    return sum((1 for p in root.glob('*/SKILL.md') if p.is_file()))

def skill_entrypoint_set(root: Path) -> str:
    """Mirror `(cd <root> && find . -mindepth 2 -maxdepth 2 -type f -name SKILL.md | LC_ALL=C sort)`."""
    if not root.is_dir():
        return ''
    entries = [f'./{p.relative_to(root).as_posix()}' for p in root.glob('*/SKILL.md') if p.is_file()]
    return '\n'.join(sorted(entries))

def payload_fingerprint() -> str:
    """Mirror the sorted `shasum -a 256` fingerprint over both payload trees."""
    files: list[Path] = []
    for base in (CLAUDE_PAYLOAD, CODEX_PAYLOAD):
        if base.is_dir():
            files.extend((p for p in base.rglob('*') if p.is_file()))
    lines = []
    for path in sorted(files, key=lambda p: p.as_posix()):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f'{digest}  {path.as_posix()}')
    return '\n'.join(lines)

class ValidatePluginPayload(unittest.TestCase):

    def test_payload(self) -> None:
        with self.subTest(msg='payload builder exists'):
            self.assertTrue(BUILDER.is_file(), f'file not found: {BUILDER}')
        with self.subTest(msg='payload builder rebuilds from scratch'):
            completed = run_builder()
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        with self.subTest(msg='Claude payload directory exists'):
            self.assertTrue(CLAUDE_PAYLOAD.is_dir(), f'missing {CLAUDE_PAYLOAD}')
        with self.subTest(msg='Codex payload directory exists'):
            self.assertTrue(CODEX_PAYLOAD.is_dir(), f'missing {CODEX_PAYLOAD}')
        claude_source = ''
        with self.subTest(msg='Claude marketplace installs the Claude dist payload'):
            claude_market = load_json_file(REPO_ROOT / '.claude-plugin' / 'marketplace.json')
            claude_source = claude_market['plugins'][0]['source']
            self.assertEqual('./dist/claude/speckit-pro', claude_source, 'Claude marketplace source')
        codex_source = ''
        with self.subTest(msg='Codex marketplace installs the Codex dist payload'):
            codex_market = load_json_file(REPO_ROOT / '.agents' / 'plugins' / 'marketplace.json')
            codex_source = codex_market['plugins'][0]['source']['path']
            self.assertEqual('./dist/codex/speckit-pro', codex_source, 'Codex marketplace source.path')
        claude_rel = claude_source[2:] if claude_source.startswith('./') else claude_source
        with self.subTest(msg='Claude marketplace path resolves to a payload'):
            self.assertTrue(bool(claude_rel) and (REPO_ROOT / claude_rel).is_dir(), f'missing {_display_path(REPO_ROOT / claude_rel)}')
        codex_rel = codex_source[2:] if codex_source.startswith('./') else codex_source
        with self.subTest(msg='Codex marketplace path resolves to a payload'):
            self.assertTrue(bool(codex_rel) and (REPO_ROOT / codex_rel).is_dir(), f'missing {_display_path(REPO_ROOT / codex_rel)}')
        for forbidden in ('.codex-plugin', 'codex-skills', 'codex-agents', 'codex-hooks.json'):
            with self.subTest(msg=f'Claude payload excludes {forbidden}'):
                self.assertFalse((CLAUDE_PAYLOAD / forbidden).exists(), f'{forbidden} exists in the Claude payload')
        for forbidden in ('.claude-plugin', 'codex-skills', 'agents'):
            with self.subTest(msg=f'Codex payload excludes {forbidden}'):
                self.assertFalse((CODEX_PAYLOAD / forbidden).exists(), f'{forbidden} exists in the Codex payload')
        with self.subTest(msg='Claude payload keeps the Claude skill set'):
            self.assertEqual(count_skill_entrypoints(SOURCE_ROOT / 'skills'), count_skill_entrypoints(CLAUDE_PAYLOAD / 'skills'), 'Claude skill count')
        with self.subTest(msg='Codex payload keeps exactly the Codex skill set'):
            self.assertEqual(skill_entrypoint_set(SOURCE_ROOT / 'codex-skills'), skill_entrypoint_set(CODEX_PAYLOAD / 'skills'), 'Codex skill entrypoints')
        with self.subTest(msg='Codex payload manifest exposes skills at ./skills/'):
            codex_manifest = load_json_file(CODEX_PAYLOAD / '.codex-plugin' / 'plugin.json')
            self.assertEqual('./skills/', codex_manifest['skills'], 'Codex manifest skills')
        with self.subTest(msg='Codex payload has no duplicate nested skill entrypoints'):
            skills_dir = CODEX_PAYLOAD / 'skills'
            nested = 0
            if skills_dir.is_dir():
                nested = sum((1 for p in skills_dir.rglob('SKILL.md') if p.is_file() and len(p.relative_to(skills_dir).parts) >= 3))
            self.assertEqual(0, nested, 'nested Codex SKILL.md count')
        with self.subTest(msg='Payload files do not reference source-tree skill paths'):
            matches: list[str] = []
            for base in (CLAUDE_PAYLOAD, CODEX_PAYLOAD):
                if not base.is_dir():
                    continue
                for path in base.rglob('*'):
                    if not path.is_file():
                        continue
                    text = path.read_text(encoding='utf-8', errors='ignore')
                    if PATH_ESCAPE_RE.search(text):
                        matches.append(path.as_posix())
            self.assertEqual([], matches, 'source-tree path references')
        with self.subTest(msg='Payload rebuild is deterministic'):
            first_fingerprint = payload_fingerprint()
            completed = run_builder()
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            second_fingerprint = payload_fingerprint()
            self.assertEqual(first_fingerprint, second_fingerprint, 'payload fingerprint')
        with self.subTest(msg='release-please extra-files stay inside package paths'):
            config = load_json_file(REPO_ROOT / 'release-please-config.json')
            bad: list[str] = []
            for package, cfg in config.get('packages', {}).items():
                for extra in cfg.get('extra-files', []):
                    path = extra.get('path', '') if isinstance(extra, dict) else ''
                    if path.startswith('../') or '/../' in path or path == '..':
                        bad.append(f'{package}: {path}')
            self.assertEqual([], bad, 'release-please illegal pathing characters')
        with self.subTest(msg='CI committed payload files are current'):
            import os
            if os.environ.get('GITHUB_ACTIONS') == 'true':
                diff = subprocess.run(['git', '-C', str(REPO_ROOT), 'diff', '--exit-code', '--', 'dist', '.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json', 'release-please-config.json'], text=True, capture_output=True, shell=False, check=False)
                self.assertEqual(0, diff.returncode, diff.stdout + diff.stderr)
            else:
                self.assertTrue(True)
# Contracts transferred from validate-payload-completeness.py.
SRC_SKILLS_DIR = REPO_ROOT / 'speckit-pro' / 'skills'
DIST_CLAUDE_SKILLS_DIR = REPO_ROOT / 'dist' / 'claude' / 'speckit-pro' / 'skills'
GUARD_HEADING = '## Codex Skill-Selection Guard'
LINE_SLACK = 5

def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()

def guard_section_lines(text: str) -> int:
    """Mirror the awk guard-section counter: from the guard heading (inclusive)
    up to (not including) the next level-2 ``## `` heading or EOF. A ``### ``
    sub-heading is part of the guard section. 0 when no guard heading is present."""
    in_guard = False
    count = 0
    for line in text.splitlines():
        if not in_guard:
            if line == GUARD_HEADING:
                in_guard = True
                count = 1
        elif line.startswith('## '):
            in_guard = False
        else:
            count += 1
    return count

def last_non_guard_heading(text: str) -> str:
    """Mirror the awk last-non-guard-heading finder: the text of the LAST level-2
    ``## `` heading (not ``### ``, not the guard heading). Empty if none."""
    last = ''
    for line in text.splitlines():
        if line.startswith('## ') and (not line.startswith('### ')) and (line != GUARD_HEADING):
            last = line
    return last

class ValidatePayloadCompleteness(unittest.TestCase):

    def test_body_completeness(self) -> None:
        with self.subTest(msg=f'built Claude skills directory exists ({_rel(DIST_CLAUDE_SKILLS_DIR)})'):
            self.assertTrue(DIST_CLAUDE_SKILLS_DIR.is_dir(), f'built Claude skills directory missing: {_rel(DIST_CLAUDE_SKILLS_DIR)} (run python3 scripts/build-plugin-payloads.py)')
        if not DIST_CLAUDE_SKILLS_DIR.is_dir():
            return
        dist_skills = sorted((p for p in DIST_CLAUDE_SKILLS_DIR.glob('*/SKILL.md') if p.is_file()), key=lambda p: p.as_posix())
        with self.subTest(msg='built Claude skills glob matched at least one SKILL.md'):
            self.assertTrue(dist_skills, f'no built Claude SKILL.md found under {_rel(DIST_CLAUDE_SKILLS_DIR)}/*/SKILL.md (empty glob — refusing to pass vacuously)')
        if not dist_skills:
            return
        for dist_file in dist_skills:
            skill_name = dist_file.parent.name
            src_file = SRC_SKILLS_DIR / skill_name / 'SKILL.md'
            src_ok = src_file.is_file() and os.access(src_file, os.R_OK)
            with self.subTest(msg=f'[{skill_name}] source SKILL.md exists and is readable ({_rel(src_file)})'):
                self.assertTrue(src_ok, f"built skill '{skill_name}' has no readable source SKILL.md at {_rel(src_file)}")
            if not src_ok:
                continue
            dist_ok = os.access(dist_file, os.R_OK)
            with self.subTest(msg=f'[{skill_name}] built SKILL.md is readable ({_rel(dist_file)})'):
                self.assertTrue(dist_ok, f"built skill '{skill_name}' SKILL.md is not readable at {_rel(dist_file)}")
            if not dist_ok:
                continue
            src_text = src_file.read_text(encoding='utf-8', errors='replace')
            anchor = last_non_guard_heading(src_text)
            with self.subTest(msg=f'[{skill_name}] source has a non-guard level-2 heading to anchor on'):
                self.assertNotEqual('', anchor, f"source SKILL.md for '{skill_name}' has no non-guard '## ' heading — cannot anchor completeness")
            if anchor == '':
                continue
            dist_text = dist_file.read_text(encoding='utf-8', errors='replace')
            with self.subTest(msg=f"[{skill_name}] last non-guard source heading survives in built body: '{anchor}'"):
                self.assertIn(anchor, dist_text, f"built '{skill_name}' SKILL.md is missing the last non-guard source heading ('{anchor}') — body truncated")
            src_lines = src_file.read_bytes().count(b'\n')
            dist_lines = dist_file.read_bytes().count(b'\n')
            guard_lines = guard_section_lines(src_text)
            expected = src_lines - guard_lines
            diff = abs(dist_lines - expected)
            with self.subTest(msg=f'[{skill_name}] built body length within tolerance of source-minus-guard (dist={dist_lines}, expected≈{expected}, guard={guard_lines})'):
                self.assertLessEqual(diff, LINE_SLACK, f"built '{skill_name}' SKILL.md has {dist_lines} lines; expected ≈{expected} (source {src_lines} − guard {guard_lines}), off by {diff} (> {LINE_SLACK}) — likely truncated")
# Contracts transferred from validate-payload-conformance.py.
CLAUDE_ROOT = REPO_ROOT / 'dist' / 'claude' / 'speckit-pro'
CODEX_ROOT = REPO_ROOT / 'dist' / 'codex' / 'speckit-pro'
NAME_RE = re.compile('^[a-z0-9][a-z0-9-]*$')
BLOCK_SCALAR_RE = re.compile('^[>|][-+]?[0-9]*$')
POINTER_KEYS = ('skills', 'hooks', 'mcpServers', 'apps', 'agents', 'commands', 'lsp')

def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except OSError:
        return ''

def _first_line(path: Path) -> str:
    text = _read_text(path)
    return text.splitlines()[0] if text.splitlines() else ''

def repo_rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()

def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))

def _json_or_none(path: Path) -> Any | None:
    try:
        return _load_json(path)
    except (OSError, json.JSONDecodeError):
        return None

def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and (value[0] in {"'", '"'}):
        return value[1:-1]
    return value

def fm_value(path: Path, key: str) -> str:
    """Return a leading-frontmatter top-level scalar, mirroring the bash awk helper."""
    lines = _read_text(path).splitlines()
    if not lines or lines[0] != '---':
        return ''
    for line in lines[1:]:
        if line == '---':
            return ''
        if line.startswith(f'{key}:'):
            value = line[len(key) + 1:].strip()
            if BLOCK_SCALAR_RE.fullmatch(value):
                return '__BLOCK__'
            return value
    return ''

def fm_has_key(path: Path, key: str) -> bool:
    """Return true iff leading frontmatter declares a top-level ``key:`` line."""
    lines = _read_text(path).splitlines()
    if not lines or lines[0] != '---':
        return False
    for line in lines[1:]:
        if line == '---':
            return False
        if line.startswith(f'{key}:'):
            return True
    return False

class ValidatePayloadConformance(unittest.TestCase):

    def assert_md_frontmatter(self, label: str, item: str, path: Path) -> None:
        with self.subTest(msg=f"[{label}/{item}] opens with a '---' frontmatter fence"):
            self.assertEqual('---', _first_line(path), f'{path} does not begin with a YAML frontmatter fence')
        if _first_line(path) != '---':
            return
        name = _strip_quotes(fm_value(path, 'name'))
        with self.subTest(msg=f"[{label}/{item}] frontmatter has a non-empty 'name' (required)"):
            self.assertTrue(name, f"{path} frontmatter is missing 'name'")
        with self.subTest(msg=f"[{label}/{item}] frontmatter 'name' is kebab-case ('{name}')"):
            self.assertRegex(name, NAME_RE, f"{path} 'name' ('{name}') is not lowercase kebab-case")
        desc = fm_value(path, 'description')
        with self.subTest(msg=f"[{label}/{item}] frontmatter has a non-empty 'description' (required)"):
            self.assertTrue(desc, f"{path} frontmatter is missing 'description'")

    def assert_no_forbidden_agent_fields(self, label: str, item: str, path: Path) -> None:
        for key in ('permissionMode', 'hooks', 'mcpServers'):
            with self.subTest(msg=f"[{label}/{item}] does NOT declare plugin-unsupported '{key}' (plugins-reference)"):
                self.assertFalse(fm_has_key(path, key), f"{path} declares '{key}' - not supported for plugin-shipped agents per official docs")

    def assert_toml_agent(self, label: str, path: Path) -> None:
        item = path.stem
        text = _read_text(path)
        with self.subTest(msg=f"[{label}/{item}] built agent .toml has a 'name =' key"):
            self.assertRegex(text, re.compile('^name\\s*=', re.MULTILINE), f"{path} is missing a top-level 'name =' key")
        with self.subTest(msg=f"[{label}/{item}] built agent .toml has a 'description =' key"):
            self.assertRegex(text, re.compile('^description\\s*=', re.MULTILINE), f"{path} is missing a top-level 'description =' key")

    def assert_hooks_json(self, label: str, path: Path) -> None:
        with self.subTest(msg=f'[{label}] hooks file exists ({repo_rel(path)})'):
            self.assertTrue(path.is_file(), f'missing hooks file: {path}')
        if not path.is_file():
            return
        data: Any | None = None
        with self.subTest(msg=f'[{label}] hooks file is valid JSON'):
            try:
                data = _load_json(path)
            except json.JSONDecodeError as exc:
                self.fail(f'invalid JSON: {path}: {exc}')
        if data is None:
            return
        with self.subTest(msg=f"[{label}] hooks file has a top-level 'hooks' object"):
            self.assertTrue(isinstance(data, dict) and isinstance(data.get('hooks'), dict), f"{path} has no top-level 'hooks' object")

    def assert_pointers_resolve(self, label: str, manifest: Path, root: Path) -> None:
        data = _json_or_none(manifest)
        for key in POINTER_KEYS:
            value = data.get(key) if isinstance(data, dict) else None
            if not isinstance(value, str) or not value:
                continue
            rel = value.removeprefix('./').removesuffix('/')
            with self.subTest(msg=f"[{label}] manifest '{key}' pointer resolves in payload ('{value}')"):
                self.assertTrue((root / rel).exists(), f"manifest '{key}' ('{value}') does not resolve to a path under the payload")

    def test_payload_conformance(self) -> None:
        self.validate_claude_payload()
        self.validate_codex_payload()

    def validate_claude_payload(self) -> None:
        with self.subTest(msg=f'[claude] built payload root exists ({repo_rel(CLAUDE_ROOT)})'):
            self.assertTrue(CLAUDE_ROOT.is_dir(), 'Claude payload missing - run python3 scripts/build-plugin-payloads.py')
        if not CLAUDE_ROOT.is_dir():
            return
        manifest = CLAUDE_ROOT / '.claude-plugin' / 'plugin.json'
        with self.subTest(msg='[claude] manifest exists at .claude-plugin/plugin.json'):
            self.assertTrue(manifest.is_file(), f'missing {manifest}')
        manifest_data: Any | None = None
        with self.subTest(msg='[claude] manifest is valid JSON'):
            try:
                manifest_data = _load_json(manifest)
            except (OSError, json.JSONDecodeError) as exc:
                self.fail(f'invalid JSON: {manifest}: {exc}')
        with self.subTest(msg="[claude] manifest has the required 'name' (string, non-empty)"):
            cname = manifest_data.get('name') if isinstance(manifest_data, dict) else None
            self.assertTrue(isinstance(cname, str) and cname, "manifest 'name' missing or not a string")
        with self.subTest(msg="[claude] manifest 'version', if present, is a string"):
            ok = isinstance(manifest_data, dict) and ('version' not in manifest_data or isinstance(manifest_data.get('version'), str))
            self.assertTrue(ok, "manifest 'version' present but not a string")
        self.assert_pointers_resolve('claude', manifest, CLAUDE_ROOT)
        skills_dir = CLAUDE_ROOT / 'skills'
        with self.subTest(msg='[claude] skills/ directory exists in the payload'):
            self.assertTrue(skills_dir.is_dir(), f'missing {skills_dir}')
        claude_skills = sorted((p for p in skills_dir.glob('*/SKILL.md') if p.is_file()), key=lambda p: p.as_posix())
        with self.subTest(msg='[claude] at least one skills/*/SKILL.md is present'):
            self.assertTrue(claude_skills, f'no SKILL.md under {skills_dir}/*/ - refusing to pass vacuously')
        if not claude_skills:
            return
        for path in claude_skills:
            self.assert_md_frontmatter('claude-skill', path.parent.name, path)
        agents_dir = CLAUDE_ROOT / 'agents'
        with self.subTest(msg='[claude] agents/ directory exists in the payload'):
            self.assertTrue(agents_dir.is_dir(), f'missing {agents_dir}')
        claude_agents = sorted((p for p in agents_dir.glob('*.md') if p.is_file()), key=lambda p: p.as_posix())
        with self.subTest(msg='[claude] at least one agents/*.md is present'):
            self.assertTrue(claude_agents, f'no agents/*.md under {agents_dir} - refusing to pass vacuously')
        if not claude_agents:
            return
        for path in claude_agents:
            item = path.stem
            self.assert_md_frontmatter('claude-agent', item, path)
            self.assert_no_forbidden_agent_fields('claude-agent', item, path)
        self.assert_hooks_json('claude', CLAUDE_ROOT / 'hooks' / 'hooks.json')

    def validate_codex_payload(self) -> None:
        with self.subTest(msg=f'[codex] built payload root exists ({repo_rel(CODEX_ROOT)})'):
            self.assertTrue(CODEX_ROOT.is_dir(), 'Codex payload missing - run python3 scripts/build-plugin-payloads.py')
        if not CODEX_ROOT.is_dir():
            return
        manifest = CODEX_ROOT / '.codex-plugin' / 'plugin.json'
        with self.subTest(msg='[codex] manifest exists at .codex-plugin/plugin.json'):
            self.assertTrue(manifest.is_file(), f'missing {manifest}')
        manifest_data: Any | None = None
        with self.subTest(msg='[codex] manifest is valid JSON'):
            try:
                manifest_data = _load_json(manifest)
            except (OSError, json.JSONDecodeError) as exc:
                self.fail(f'invalid JSON: {manifest}: {exc}')
        xname = manifest_data.get('name') if isinstance(manifest_data, dict) and isinstance(manifest_data.get('name'), str) else ''
        with self.subTest(msg="[codex] manifest 'name' is present, a string, and kebab-case"):
            self.assertTrue(xname and NAME_RE.fullmatch(xname), f"manifest 'name' missing/not-a-string/not-kebab-case ('{xname}')")
        xver = manifest_data.get('version') if isinstance(manifest_data, dict) and isinstance(manifest_data.get('version'), str) else ''
        with self.subTest(msg="[codex] manifest 'version' is present and non-empty (semver)"):
            self.assertTrue(xver, "manifest 'version' missing or not a string")
        xdesc = manifest_data.get('description') if isinstance(manifest_data, dict) and isinstance(manifest_data.get('description'), str) else ''
        with self.subTest(msg="[codex] manifest 'description' is present and non-empty"):
            self.assertTrue(xdesc, "manifest 'description' missing or empty")
        codex_plugin_dir = CODEX_ROOT / '.codex-plugin'
        expected_plugin_files = {'plugin.json', 'sweep-mcp.json'}
        actual_plugin_files = {path.name for path in codex_plugin_dir.iterdir() if path.is_file()} if codex_plugin_dir.is_dir() else set()
        with self.subTest(msg='[codex] .codex-plugin/ contains only the manifest and sweep broker MCP config'):
            self.assertEqual(expected_plugin_files, actual_plugin_files, '.codex-plugin/ must contain exactly plugin.json and sweep-mcp.json')
        self.assert_pointers_resolve('codex', manifest, CODEX_ROOT)
        skills_dir = CODEX_ROOT / 'skills'
        with self.subTest(msg='[codex] skills/ directory exists at the plugin root'):
            self.assertTrue(skills_dir.is_dir(), f'missing {skills_dir}')
        codex_skills = sorted((p for p in skills_dir.glob('*/SKILL.md') if p.is_file()), key=lambda p: p.as_posix())
        with self.subTest(msg='[codex] at least one skills/*/SKILL.md is present'):
            self.assertTrue(codex_skills, f'no SKILL.md under {skills_dir}/*/ - refusing to pass vacuously')
        if not codex_skills:
            return
        for path in codex_skills:
            self.assert_md_frontmatter('codex-skill', path.parent.name, path)
        agents_dir = CODEX_ROOT / 'codex-agents'
        with self.subTest(msg='[codex] codex-agents/ directory exists at the plugin root'):
            self.assertTrue(agents_dir.is_dir(), f'missing {agents_dir}')
        codex_agents = sorted((p for p in agents_dir.glob('*.toml') if p.is_file()), key=lambda p: p.as_posix())
        with self.subTest(msg='[codex] at least one codex-agents/*.toml is present'):
            self.assertTrue(codex_agents, f'no codex-agents/*.toml under {agents_dir} - refusing to pass vacuously')
        if not codex_agents:
            return
        for path in codex_agents:
            self.assert_toml_agent('codex-agent', path)
        self.assert_hooks_json('codex', CODEX_ROOT / 'codex-hooks.json')

def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-payload-contracts")

if __name__ == "__main__":
    raise SystemExit(main())
