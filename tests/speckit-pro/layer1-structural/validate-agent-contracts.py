#!/usr/bin/env python3
"""Consolidated Layer 1 contracts owned by validate-agent-contracts.py."""

from __future__ import annotations

from pathlib import Path
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

from structural_helpers import body as _body
from structural_helpers import frontmatter as _frontmatter
from test_result import run_counted

EXPECTED_AGENT_DIRS = (Path('.'), Path('speckit-pro'), Path('tests/speckit-pro'), Path('docs-site'))
CLAUDE_WRAPPER = '@./AGENTS.md\n'
GEMINI_WRAPPER = '@./AGENTS.md\n'
COPILOT_POINTER = '# Copilot Instructions\n\nFollow the repository agent contract in `AGENTS.md`. Do not maintain separate\nCopilot-specific project rules here.\n'
AGENT_CONTEXT_BUDGET_BYTES = 32768
SKIP_DIR_NAMES = {'.git', '.mypy_cache', '.pytest_cache', '.specify', '.worktrees', 'dist', 'node_modules'}
SKIP_PREFIXES = (Path('docs-site/src/content/docs/reference'),)
INSTRUCTION_NAMES = {'AGENTS.md', 'CLAUDE.md', 'GEMINI.md'}
FORBIDDEN_AGENT_PHRASES = ('<!-- SPECKIT START -->', '<!-- SPECKIT END -->', 'Auto-generated from feature plans', '## Active Technologies', '## Recent Changes', '### Test Layers')

def _display(path: Path) -> str:
    text = path.as_posix()
    return '.' if text == '.' else text

def _is_skipped(rel_dir: Path) -> bool:
    return any((rel_dir == prefix or prefix in rel_dir.parents for prefix in SKIP_PREFIXES))

def find_instruction_files(repo_root: Path) -> dict[str, list[Path]]:
    files = {name: [] for name in INSTRUCTION_NAMES}
    for dirpath, dirnames, filenames in os.walk(repo_root):
        current = Path(dirpath)
        rel_dir = current.relative_to(repo_root)
        if _is_skipped(rel_dir):
            dirnames[:] = []
            continue
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIR_NAMES]
        for filename in filenames:
            if filename in files:
                files[filename].append((current / filename).relative_to(repo_root))
    for matches in files.values():
        matches.sort()
    return files

def _read(repo_root: Path, rel_path: Path) -> str:
    return (repo_root / rel_path).read_text(encoding='utf-8')

def collect_errors(repo_root: Path) -> list[str]:
    errors: list[str] = []
    expected_dirs = set(EXPECTED_AGENT_DIRS)
    files = find_instruction_files(repo_root)
    agent_dirs = {path.parent for path in files['AGENTS.md']}
    if agent_dirs != expected_dirs:
        expected = ', '.join((_display(path / 'AGENTS.md') for path in sorted(expected_dirs)))
        actual = ', '.join((_display(path) for path in files['AGENTS.md'])) or '<none>'
        errors.append(f'AGENTS.md files must be exactly [{expected}], got [{actual}]')
    for directory in sorted(expected_dirs):
        agents = directory / 'AGENTS.md'
        claude = directory / 'CLAUDE.md'
        gemini = directory / 'GEMINI.md'
        if not (repo_root / agents).is_file():
            continue
        if not (repo_root / claude).is_file():
            errors.append(f'missing Claude wrapper: {_display(claude)}')
        elif _read(repo_root, claude) != CLAUDE_WRAPPER:
            errors.append(f'{_display(claude)} must contain only {CLAUDE_WRAPPER.strip()!r}')
        if not (repo_root / gemini).is_file():
            errors.append(f'missing Gemini wrapper: {_display(gemini)}')
        elif _read(repo_root, gemini) != GEMINI_WRAPPER:
            errors.append(f'{_display(gemini)} must contain only {GEMINI_WRAPPER.strip()!r}')
    for filename in ('CLAUDE.md', 'GEMINI.md'):
        expected_files = {directory / filename for directory in expected_dirs}
        actual_files = set(files[filename])
        extras = sorted(actual_files - expected_files)
        if extras:
            errors.append(f"unexpected {filename} files: {', '.join((_display(path) for path in extras))}")
    total_bytes = 0
    for path in files['AGENTS.md']:
        text = _read(repo_root, path)
        total_bytes += len(text.encode('utf-8'))
        for phrase in FORBIDDEN_AGENT_PHRASES:
            if phrase in text:
                errors.append(f'{_display(path)} contains stale agent-context exhaust: {phrase}')
    if total_bytes > AGENT_CONTEXT_BUDGET_BYTES:
        errors.append(f'AGENTS.md context is {total_bytes} bytes, above {AGENT_CONTEXT_BUDGET_BYTES}')
    copilot = repo_root / '.github' / 'copilot-instructions.md'
    if not copilot.is_file():
        errors.append('missing .github/copilot-instructions.md')
    elif copilot.read_text(encoding='utf-8') != COPILOT_POINTER:
        errors.append('.github/copilot-instructions.md must only point to AGENTS.md')
    return errors

class ValidateAgentInstructions(unittest.TestCase):

    def test_agent_instruction_files_do_not_drift(self) -> None:
        errors = collect_errors(REPO_ROOT)
        with self.subTest(msg='agent instruction files have canonical wrapper shape'):
            self.assertFalse(errors, '\n'.join(errors))
AGENTS_DIR = PLUGIN_ROOT / 'agents'
validate_agents_AGENTS = ('phase-executor', 'clarify-executor', 'checklist-executor', 'analyze-executor', 'implement-executor', 'codebase-analyst', 'spec-context-analyst', 'domain-researcher', 'consensus-synthesizer', 'artifact-author', 'uat-runbook-author', 'sweep-classifier', 'sweep-analyst')
PLUGIN_AGENT_FIELDS = {'name', 'description', 'model', 'effort', 'maxTurns', 'tools', 'disallowedTools', 'skills', 'memory', 'background', 'isolation', 'color'}
UNSUPPORTED_PLUGIN_AGENT_FIELDS = {'hooks', 'mcpServers', 'permissionMode', 'initialPrompt', 'experimental.cacheTtl'}
MEMORY_POLICY = {'codebase-analyst': 'local', 'implement-executor': 'local', 'spec-context-analyst': 'local'}
NAME_RE = re.compile('^[a-zA-Z0-9][a-zA-Z0-9-]{2,49}$')
validate_agents_MODEL_RE = re.compile('^(opus|sonnet|haiku|inherit)$')

def _field(frontmatter: str, key: str) -> str:
    """First ``key: value`` in the frontmatter, quote-stripped (mirrors sed/tr)."""
    for line in frontmatter.split('\n'):
        if line.startswith(f'{key}:'):
            value = re.sub(f'^{key}:[ \\t]*', '', line)
            return value.replace('"', '').replace("'", '')
    return ''

def validate_agents__nonblank(text: str) -> str:
    return '\n'.join((line for line in text.split('\n') if line.strip()))

class ValidateAgents(unittest.TestCase):

    def test_agents(self) -> None:
        with self.subTest(msg='Claude agent roster exactly matches all shipped source definitions'):
            discovered = {path.stem for path in AGENTS_DIR.glob('*.md')}
            self.assertEqual(set(validate_agents_AGENTS), discovered)
        for agent in validate_agents_AGENTS:
            agent_file = AGENTS_DIR / f'{agent}.md'
            with self.subTest(msg=f'{agent}: file exists'):
                self.assertTrue(agent_file.is_file(), f'file not found: {agent_file}')
            if not agent_file.is_file():
                continue
            lines = agent_file.read_text(encoding='utf-8').splitlines()
            first_line = lines[0] if lines else ''
            with self.subTest(msg=f'{agent}: starts with --- (YAML frontmatter)'):
                self.assertEqual('---', first_line, 'first line must be ---')
            with self.subTest(msg=f'{agent}: has closing ---'):
                fence_count = sum((1 for line in lines if line == '---'))
                self.assertGreaterEqual(fence_count, 2, f"expected at least 2 '---' lines, found {fence_count}")
            frontmatter = _frontmatter(lines)
            declared_fields = {line.split(':', 1)[0] for line in frontmatter.splitlines() if line and (not line[0].isspace()) and (':' in line)}
            with self.subTest(msg=f'{agent}: uses only supported plugin-agent frontmatter fields'):
                self.assertFalse(declared_fields - PLUGIN_AGENT_FIELDS)
                self.assertFalse(declared_fields & UNSUPPORTED_PLUGIN_AGENT_FIELDS)
            memory_val = _field(frontmatter, 'memory')
            with self.subTest(msg=f'{agent}: memory scope matches the curated persistence policy'):
                self.assertEqual(MEMORY_POLICY.get(agent, ''), memory_val)
            with self.subTest(msg=f'{agent}: has name: field'):
                self.assertIn('name:', frontmatter)
            name_val = _field(frontmatter, 'name')
            with self.subTest(msg=f'{agent}: name is valid format (alphanumeric + hyphens, 3-50 chars)'):
                self.assertRegex(name_val, NAME_RE, f"name '{name_val}' must be 3-50 chars")
            with self.subTest(msg=f'{agent}: has description: field'):
                self.assertIn('description:', frontmatter)
            with self.subTest(msg=f'{agent}: has model: field'):
                self.assertIn('model:', frontmatter)
            model_val = _field(frontmatter, 'model')
            with self.subTest(msg=f'{agent}: model is valid (opus|sonnet|haiku|inherit)'):
                self.assertRegex(model_val, validate_agents_MODEL_RE, 'model must be opus, sonnet, haiku, or inherit')
            body = _body(lines)
            body_trimmed = validate_agents__nonblank(body)
            with self.subTest(msg=f'{agent}: system prompt body exists (after frontmatter)'):
                self.assertTrue(body_trimmed, 'no system prompt body after frontmatter')
            with self.subTest(msg=f'{agent}: system prompt length > 20 chars'):
                self.assertGreater(len(body_trimmed), 20, f'system prompt is only {len(body_trimmed)} chars (need > 20)')
            if agent == 'clarify-executor':
                with self.subTest(msg='clarify-executor: returns questions to parent'):
                    self.assertIn('## Clarify Question Set', body)
                with self.subTest(msg='clarify-executor: does not claim to be the user'):
                    self.assertNotIn('YOU ARE THE USER', body)
                with self.subTest(msg='clarify-executor: does not forbid returning questions'):
                    self.assertNotIn('Do NOT present questions back', body)
                with self.subTest(msg='clarify-executor: does not invoke interactive clarify skill'):
                    self.assertNotIn('Use the Skill tool to run', body)
            if agent in MEMORY_POLICY:
                with self.subTest(msg=f'{agent}: explicitly consults current inputs before memory'):
                    self.assertIn('Current task inputs always override memory', body)
                with self.subTest(msg=f'{agent}: curates only verified durable memory'):
                    self.assertRegex(body, 'verified\\s+durable project knowledge')
                with self.subTest(msg=f'{agent}: forbids sensitive and ephemeral memory content'):
                    self.assertIn('Never store secrets', body)
CODEX_AGENTS_DIR = PLUGIN_ROOT / 'codex-agents'
CC_AGENTS_DIR = PLUGIN_ROOT / 'agents'
validate_codex_agents_AGENTS = ('autopilot-fast-helper', 'clarify-executor', 'checklist-executor', 'analyze-executor', 'implement-executor', 'phase-executor', 'codebase-analyst', 'spec-context-analyst', 'domain-researcher')
LOW_EFFORT_ANALYST_ROLES = frozenset({'codebase-analyst', 'spec-context-analyst'})
CC_ONLY_FIELDS = ('tools', 'disallowedTools', 'permissionMode', 'color', 'maxTurns', 'background', 'effort')
validate_codex_agents_MODEL_RE = re.compile('^(gpt-5\\.6-sol|gpt-5\\.6-terra|gpt-5\\.6-luna|gpt-5\\.5|gpt-5\\.4|gpt-5\\.4-mini|gpt-5\\.3-codex|gpt-5\\.3-codex-spark)$')
EFFORT_RE = re.compile('^(minimal|low|medium|high|xhigh)$')
SANDBOX_RE = re.compile('^(read-only|workspace-write)$')

def _extract_toml_string(text: str, field: str) -> str:
    """First ``field = "value"`` line's value (mirrors the sed -n extractor)."""
    match = re.search(f'^{re.escape(field)} = "([^"]*)"$', text, re.MULTILINE)
    return match.group(1) if match else ''

def _extract_developer_instructions(text: str) -> str:
    '''Lines between ``developer_instructions = """`` and the closing ``"""``.'''
    out: list[str] = []
    capture = False
    for line in text.split('\n'):
        if not capture and line.startswith('developer_instructions = """'):
            capture = True
            continue
        if capture and line == '"""':
            break
        if capture:
            out.append(line)
    return '\n'.join(out)

def validate_codex_agents__nonblank(text: str) -> str:
    return '\n'.join((line for line in text.split('\n') if line.strip()))

def _has_field_line(text: str, field: str) -> bool:
    return re.search(f'^{re.escape(field)}[ \\t]*=', text, re.MULTILINE) is not None

class ValidateCodexAgents(unittest.TestCase):

    def test_codex_agents(self) -> None:
        for agent in validate_codex_agents_AGENTS:
            agent_file = CODEX_AGENTS_DIR / f'{agent}.toml'
            with self.subTest(msg=f'{agent}: TOML file exists'):
                self.assertTrue(agent_file.is_file(), f'file not found: {agent_file}')
            with self.subTest(msg=f'{agent}: legacy Markdown file removed'):
                self.assertFalse((CODEX_AGENTS_DIR / f'{agent}.md').is_file(), 'legacy .md must be removed')
            if not agent_file.is_file():
                continue
            content = agent_file.read_text(encoding='utf-8')
            with self.subTest(msg=f'{agent}: has name field'):
                self.assertIn('name = "', content)
            name_val = _extract_toml_string(content, 'name')
            with self.subTest(msg=f'{agent}: name matches filename'):
                self.assertEqual(agent, name_val, 'name field must match filename stem')
            with self.subTest(msg=f'{agent}: has description field'):
                self.assertIn('description = "', content)
            with self.subTest(msg=f'{agent}: has model field'):
                self.assertIn('model = "', content)
            model_val = _extract_toml_string(content, 'model')
            with self.subTest(msg=f'{agent}: model is an officially documented Codex GPT model'):
                self.assertRegex(model_val, validate_codex_agents_MODEL_RE, 'model must be an officially documented Codex GPT model')
            if model_val == 'gpt-5.3-codex-spark':
                with self.subTest(msg=f'{agent}: model_reasoning_effort field is absent (Spark does not support reasoning fields)'):
                    self.assertNotIn('model_reasoning_effort = "', content)
                effort_val = ''
            elif agent == 'autopilot-fast-helper' or agent in LOW_EFFORT_ANALYST_ROLES:
                with self.subTest(msg=f'{agent}: has low model_reasoning_effort field'):
                    self.assertIn('model_reasoning_effort = "low"', content)
                effort_val = _extract_toml_string(content, 'model_reasoning_effort')
            else:
                with self.subTest(msg=f'{agent}: has model_reasoning_effort field'):
                    self.assertIn('model_reasoning_effort = "', content)
                effort_val = _extract_toml_string(content, 'model_reasoning_effort')
                with self.subTest(msg=f'{agent}: reasoning effort uses supported values'):
                    self.assertRegex(effort_val, EFFORT_RE, 'reasoning effort must be minimal, low, medium, high, or xhigh')
            with self.subTest(msg=f'{agent}: has sandbox_mode field'):
                self.assertIn('sandbox_mode = "', content)
            sandbox_val = _extract_toml_string(content, 'sandbox_mode')
            with self.subTest(msg=f'{agent}: sandbox_mode uses supported values'):
                self.assertRegex(sandbox_val, SANDBOX_RE)
            with self.subTest(msg=f'{agent}: has developer_instructions block'):
                self.assertIn('developer_instructions = """', content)
            instructions = _extract_developer_instructions(content)
            with self.subTest(msg=f'{agent}: developer_instructions body is non-empty'):
                self.assertTrue(validate_codex_agents__nonblank(instructions), 'developer_instructions block is empty')
            with self.subTest(msg=f'{agent}: no Claude Code-only fields'):
                bad = [field for field in CC_ONLY_FIELDS if _has_field_line(content, field)]
                self.assertFalse(bad, f"Claude Code-only fields found: {' '.join(bad)}")
            if agent != 'autopilot-fast-helper':
                with self.subTest(msg=f'{agent}: corresponding Claude agent exists in agents/'):
                    self.assertTrue((CC_AGENTS_DIR / f'{agent}.md').is_file(), f'missing Claude twin: {agent}.md')
            else:
                with self.subTest(msg='autopilot-fast-helper: intentionally Codex-only'):
                    self.assertFalse((CC_AGENTS_DIR / 'autopilot-fast-helper.md').is_file(), 'autopilot-fast-helper should remain Codex-only; do not add a Claude twin')
            self._check_profile(agent, model_val, effort_val, sandbox_val, instructions)
        with self.subTest(msg='codex-agents/openai.yaml removed'):
            self.assertFalse((CODEX_AGENTS_DIR / 'openai.yaml').is_file(), 'openai.yaml must be removed')
        with self.subTest(msg='codex-agents directory contains TOML files only'):
            non_toml = [p for p in CODEX_AGENTS_DIR.iterdir() if p.is_file() and p.suffix != '.toml']
            self.assertEqual(0, len(non_toml), 'only standalone TOML custom-agent files are allowed')

    def _check_profile(self, agent: str, model_val: str, effort_val: str, sandbox_val: str, instructions: str) -> None:
        if agent == 'autopilot-fast-helper':
            with self.subTest(msg='autopilot-fast-helper: uses Luna low-effort read-only advisory profile'):
                self.assertTrue(model_val == 'gpt-5.6-luna' and effort_val == 'low' and (sandbox_val == 'read-only'), f'expected gpt-5.6-luna / low / read-only, got {model_val} / {effort_val} / {sandbox_val}')
        elif agent == 'clarify-executor':
            with self.subTest(msg='clarify-executor: uses xhigh GPT-5.6 Sol read-only question-prep profile'):
                self.assertTrue(model_val == 'gpt-5.6-sol' and effort_val == 'xhigh' and (sandbox_val == 'read-only'), f'expected gpt-5.6-sol / xhigh / read-only, got {model_val} / {effort_val} / {sandbox_val}')
            with self.subTest(msg='clarify-executor: returns questions to parent'):
                self.assertIn('## Clarify Question Set', instructions)
            with self.subTest(msg='clarify-executor: does not claim to be the user'):
                self.assertNotIn('YOU ARE THE USER', instructions)
            with self.subTest(msg='clarify-executor: does not invoke interactive clarify skill'):
                self.assertNotIn('Run `$speckit-clarify`', instructions)
        elif agent in ('phase-executor', 'checklist-executor', 'analyze-executor'):
            with self.subTest(msg=f'{agent}: uses xhigh GPT-5.6 Sol executor profile'):
                self.assertTrue(model_val == 'gpt-5.6-sol' and effort_val == 'xhigh' and (sandbox_val == 'workspace-write'), f'expected gpt-5.6-sol / xhigh / workspace-write, got {model_val} / {effort_val} / {sandbox_val}')
        elif agent == 'implement-executor':
            with self.subTest(msg='implement-executor: uses xhigh GPT-5.6 Sol TDD profile'):
                self.assertTrue(model_val == 'gpt-5.6-sol' and effort_val == 'xhigh' and (sandbox_val == 'workspace-write'), f'expected gpt-5.6-sol / xhigh / workspace-write, got {model_val} / {effort_val} / {sandbox_val}')
        elif agent in ('codebase-analyst', 'spec-context-analyst'):
            with self.subTest(msg=f'{agent}: uses low-effort GPT-5.6 Sol in a read-only sandbox'):
                self.assertTrue(model_val == 'gpt-5.6-sol' and effort_val == 'low' and (sandbox_val == 'read-only'), f'expected gpt-5.6-sol / low / read-only, got {model_val} / {effort_val} / {sandbox_val}')
        elif agent == 'domain-researcher':
            with self.subTest(msg='domain-researcher: uses xhigh read-only GPT-5.6 Sol consensus profile'):
                self.assertTrue(model_val == 'gpt-5.6-sol' and effort_val == 'xhigh' and (sandbox_val == 'read-only'), f'expected gpt-5.6-sol / xhigh / read-only, got {model_val} / {effort_val} / {sandbox_val}')

AGENT_INSTRUCTION_DIRS = EXPECTED_AGENT_DIRS
collect_agent_instruction_errors = collect_errors

def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-agent-contracts", allow_live_specs=True)

if __name__ == "__main__":
    raise SystemExit(main())
