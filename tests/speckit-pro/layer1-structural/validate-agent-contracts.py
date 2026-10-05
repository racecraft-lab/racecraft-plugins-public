#!/usr/bin/env python3
"""Consolidated Layer 1 contracts owned by validate-agent-contracts.py."""

from __future__ import annotations

from pathlib import Path
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
from structural_helpers import developer_instructions as _extract_developer_instructions
from structural_helpers import frontmatter as _frontmatter
from structural_helpers import frontmatter_field as _field
from structural_helpers import toml_string_field
from test_result import run_counted
from speckit_pro_runner.agent_inventory import (
    AGENT_INVENTORY,
    CLAUDE_REQUIRED_AGENT_NAMES,
    CODEX_OPTIONAL_AGENT_NAMES,
    CODEX_REQUIRED_AGENT_NAMES,
    inventory_source_errors,
)

AGENTS_DIR = PLUGIN_ROOT / 'agents'
validate_agents_AGENTS = CLAUDE_REQUIRED_AGENT_NAMES
PLUGIN_AGENT_FIELDS = {'name', 'description', 'model', 'effort', 'maxTurns', 'tools', 'disallowedTools', 'skills', 'memory', 'background', 'isolation', 'color'}
UNSUPPORTED_PLUGIN_AGENT_FIELDS = {'hooks', 'mcpServers', 'permissionMode', 'initialPrompt', 'experimental.cacheTtl'}
MEMORY_POLICY = {
    role['name']: role['claude_code']['memory']
    for role in AGENT_INVENTORY['roles']
    if role['claude_code']['memory'] != 'none'
}
NAME_RE = re.compile('^[a-zA-Z0-9][a-zA-Z0-9-]{2,49}$')
validate_agents_MODEL_RE = re.compile('^(opus|sonnet|haiku|inherit)$')

def validate_agents__nonblank(text: str) -> str:
    return '\n'.join((line for line in text.split('\n') if line.strip()))

class ValidateAgents(unittest.TestCase):

    def test_agents(self) -> None:
        with self.subTest(msg='authored agent sources exactly match the authoritative inventory'):
            self.assertEqual(inventory_source_errors(PLUGIN_ROOT, AGENT_INVENTORY), [])
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
CODEX_AGENT_PROFILES = {
    role['name']: (
        role['codex']['model'],
        role['codex']['effort'] or '',
        role['codex']['sandbox'],
    )
    for role in AGENT_INVENTORY['roles']
    if role['codex']['implementation'] == 'custom_agent'
}
validate_codex_agents_AGENTS = (*CODEX_REQUIRED_AGENT_NAMES, *CODEX_OPTIONAL_AGENT_NAMES)
CONSENSUS_ANALYST_ROLES = frozenset({'codebase-analyst', 'spec-context-analyst', 'domain-researcher'})
NATIVE_COMMAND_LIFECYCLE_EXEMPT_ROLES = frozenset({'autopilot-fast-helper', 'consensus-synthesizer', 'consensus-tiebreaker'})
CC_ONLY_FIELDS = ('tools', 'disallowedTools', 'permissionMode', 'color', 'maxTurns', 'background', 'effort')
validate_codex_agents_MODEL_RE = re.compile('^(gpt-6-sol|gpt-6-luna|gpt-6-astra)$')
EFFORT_RE = re.compile('^(minimal|low|medium|high|xhigh|max)$')
SANDBOX_RE = re.compile('^(read-only|workspace-write)$')
NATIVE_COMMAND_LIFECYCLE_CONTRACT = (
    'inspect the whole returned object, not only its',
    '`session_id` without an integer `exit_code`',
    'Poll `write_stdin` with empty `chars` and that exact `session_id`',
    'every intermediate response remains pending',
    'Do not relaunch an equivalent gate',
    'return while any owned command remains pending',
    'succeeds only when its own `exit_code` is `0`',
    'partial stdout',
    'every exact handle is tracked and drained',
)

def validate_codex_agents__nonblank(text: str) -> str:
    return '\n'.join((line for line in text.split('\n') if line.strip()))

def _has_field_line(text: str, field: str) -> bool:
    return re.search(f'^{re.escape(field)}[ \\t]*=', text, re.MULTILINE) is not None

class ValidateCodexAgents(unittest.TestCase):

    def test_codex_agents(self) -> None:
        with self.subTest(msg='codex-agents directory exists (fail closed)'):
            self.assertTrue(CODEX_AGENTS_DIR.is_dir(), f'directory not found: {CODEX_AGENTS_DIR}')
        if not CODEX_AGENTS_DIR.is_dir():
            return

        discovered = tuple(sorted(path.stem for path in CODEX_AGENTS_DIR.glob('*.toml') if path.is_file()))
        with self.subTest(msg='codex-agents TOML roster exactly matches the policy matrix'):
            self.assertEqual(tuple(sorted(CODEX_AGENT_PROFILES)), discovered, 'missing or unknown Codex agent TOML files')

        for agent, expected_profile in CODEX_AGENT_PROFILES.items():
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
            name_val = toml_string_field(content, 'name')
            with self.subTest(msg=f'{agent}: name matches filename'):
                self.assertEqual(agent, name_val, 'name field must match filename stem')
            with self.subTest(msg=f'{agent}: has description field'):
                self.assertIn('description = "', content)
            with self.subTest(msg=f'{agent}: has model field'):
                self.assertIn('model = "', content)
            model_val = toml_string_field(content, 'model')
            with self.subTest(msg=f'{agent}: model is an officially documented Codex GPT model'):
                self.assertRegex(model_val, validate_codex_agents_MODEL_RE, 'model must be an officially documented Codex GPT model')
            if not expected_profile[1]:
                with self.subTest(msg=f'{agent}: sets no model_reasoning_effort, so the spawn value applies'):
                    self.assertNotIn('model_reasoning_effort', content)
                effort_val = ''
            elif agent == 'autopilot-fast-helper':
                with self.subTest(msg=f'{agent}: has low model_reasoning_effort field'):
                    self.assertIn('model_reasoning_effort = "low"', content)
                effort_val = toml_string_field(content, 'model_reasoning_effort')
            else:
                with self.subTest(msg=f'{agent}: has model_reasoning_effort field'):
                    self.assertIn('model_reasoning_effort = "', content)
                effort_val = toml_string_field(content, 'model_reasoning_effort')
                with self.subTest(msg=f'{agent}: reasoning effort uses supported values'):
                    self.assertRegex(effort_val, EFFORT_RE, 'reasoning effort must be minimal, low, medium, high, xhigh, or max')
            with self.subTest(msg=f'{agent}: has sandbox_mode field'):
                self.assertIn('sandbox_mode = "', content)
            sandbox_val = toml_string_field(content, 'sandbox_mode')
            with self.subTest(msg=f'{agent}: sandbox_mode uses supported values'):
                self.assertRegex(sandbox_val, SANDBOX_RE)
            with self.subTest(msg=f'{agent}: model, effort, and sandbox match the exact role policy'):
                self.assertEqual(expected_profile, (model_val, effort_val, sandbox_val))
            with self.subTest(msg=f'{agent}: has developer_instructions block'):
                self.assertIn('developer_instructions = """', content)
            instructions = _extract_developer_instructions(content)
            with self.subTest(msg=f'{agent}: developer_instructions body is non-empty'):
                self.assertTrue(validate_codex_agents__nonblank(instructions), 'developer_instructions block is empty')
            normalized_instructions = ' '.join(instructions.split())
            if agent in NATIVE_COMMAND_LIFECYCLE_EXEMPT_ROLES:
                with self.subTest(msg=f'{agent}: omits the native command lifecycle contract (runs no commands)'):
                    present = [
                        phrase for phrase in NATIVE_COMMAND_LIFECYCLE_CONTRACT
                        if phrase in normalized_instructions
                    ]
                    self.assertFalse(present, f'native command lifecycle clauses present in a no-command role: {present}')
            else:
                with self.subTest(msg=f'{agent}: drains native command handles before dependent work or return'):
                    missing = [
                        phrase for phrase in NATIVE_COMMAND_LIFECYCLE_CONTRACT
                        if phrase not in normalized_instructions
                    ]
                    self.assertFalse(missing, f'native command lifecycle clauses missing: {missing}')
            with self.subTest(msg=f'{agent}: no Claude Code-only fields'):
                bad = [field for field in CC_ONLY_FIELDS if _has_field_line(content, field)]
                self.assertFalse(bad, f"Claude Code-only fields found: {' '.join(bad)}")
            if agent != 'autopilot-fast-helper':
                with self.subTest(msg=f'{agent}: corresponding Claude agent exists in agents/'):
                    self.assertTrue((CC_AGENTS_DIR / f'{agent}.md').is_file(), f'missing Claude twin: {agent}.md')
            else:
                with self.subTest(msg='autopilot-fast-helper: intentionally Codex-only'):
                    self.assertFalse((CC_AGENTS_DIR / 'autopilot-fast-helper.md').is_file(), 'autopilot-fast-helper should remain Codex-only; do not add a Claude twin')
            self._check_profile(agent, instructions)
        with self.subTest(msg='codex-agents/openai.yaml removed'):
            self.assertFalse((CODEX_AGENTS_DIR / 'openai.yaml').is_file(), 'openai.yaml must be removed')
        with self.subTest(msg='codex-agents directory contains TOML files only'):
            non_toml = [p for p in CODEX_AGENTS_DIR.iterdir() if p.is_file() and p.suffix != '.toml']
            self.assertEqual(0, len(non_toml), 'only standalone TOML custom-agent files are allowed')

    def _check_profile(self, agent: str, instructions: str) -> None:
        """Profile values come from the inventory; only role prose is pinned here."""
        if agent == 'clarify-executor':
            with self.subTest(msg='clarify-executor: returns questions to parent'):
                self.assertIn('## Clarify Question Set', instructions)
            with self.subTest(msg='clarify-executor: does not claim to be the user'):
                self.assertNotIn('YOU ARE THE USER', instructions)
            with self.subTest(msg='clarify-executor: does not invoke interactive clarify skill'):
                self.assertNotIn('Run `$speckit-clarify`', instructions)

# A backticked path in agent prose names a plugin file; it must resolve from the plugin root.
PROSE_PLUGIN_PATH = re.compile(r'`((?:skills|codex-skills|references|agents|codex-agents|scripts)/[A-Za-z0-9_./-]+\.(?:md|json|py|toml))`')


class ValidateAgentProsePaths(unittest.TestCase):

    def test_plugin_paths_in_agent_prose_resolve_from_the_plugin_root(self) -> None:
        surfaces = sorted(CC_AGENTS_DIR.glob('*.md')) + sorted(CODEX_AGENTS_DIR.glob('*.toml'))
        self.assertTrue(surfaces, 'no agent definitions found; the path check would pass on nothing')
        checked = 0
        for surface in surfaces:
            for target in sorted(set(PROSE_PLUGIN_PATH.findall(surface.read_text(encoding='utf-8')))):
                checked += 1
                with self.subTest(surface=surface.name, target=target):
                    self.assertTrue((PLUGIN_ROOT / target).is_file(), f'{surface.name} names {target}, which is not a plugin file')
        self.assertGreater(checked, 0, 'no plugin path found in agent prose; the pattern matches nothing')


# The owner's plan-stage table (issue 1150): (Claude model, Claude effort, Codex model, Codex effort)
# per installed agent. phase-executor's Codex file sets no effort (a file effort would override the spawn
# value), so the brief sets it per phase: Plan high, Specify and Tasks medium. None marks that row.
PLAN_STAGE_TABLE = {
    'phase-executor': ('opus', 'high', 'gpt-6-sol', None),
    'clarify-executor': ('sonnet', 'high', 'gpt-6-sol', 'medium'),
    'checklist-executor': ('sonnet', 'high', 'gpt-6-sol', 'medium'),
    'analyze-executor': ('sonnet', 'high', 'gpt-6-sol', 'medium'),
    'codebase-analyst': ('sonnet', 'high', 'gpt-6-luna', 'high'),
    'spec-context-analyst': ('sonnet', 'high', 'gpt-6-luna', 'high'),
    'domain-researcher': ('sonnet', 'high', 'gpt-6-luna', 'high'),
    'artifact-author': ('sonnet', 'high', 'gpt-6-sol', 'medium'),
    # Unchanged rows.
    'consensus-synthesizer': ('sonnet', 'high', 'gpt-6-sol', 'medium'),
    'consensus-tiebreaker': ('sonnet', 'max', 'gpt-6-sol', 'max'),
    'artifact-preview-observer': ('haiku', '', None, None),
}


class ValidatePlanStageModelTable(unittest.TestCase):

    def test_agent_files_and_codex_tomls_match_the_table(self) -> None:
        inventory = {role['name']: role for role in AGENT_INVENTORY['roles']}
        for agent, (claude_model, claude_effort, codex_model, codex_effort) in PLAN_STAGE_TABLE.items():
            source = _frontmatter((CC_AGENTS_DIR / f'{agent}.md').read_text(encoding='utf-8').splitlines())
            with self.subTest(agent=agent, host='claude'):
                self.assertEqual((claude_model, claude_effort), (_field(source, 'model'), _field(source, 'effort')))
                self.assertEqual((claude_model, claude_effort or None),
                                 (inventory[agent]['claude_code']['model'], inventory[agent]['claude_code']['effort'] or None))
            if codex_model is None:
                continue
            toml = (CODEX_AGENTS_DIR / f'{agent}.toml').read_text(encoding='utf-8')
            with self.subTest(agent=agent, host='codex'):
                self.assertEqual((codex_model, codex_effort or ''),
                                 (toml_string_field(toml, 'model'), toml_string_field(toml, 'model_reasoning_effort')))
                self.assertEqual((codex_model, codex_effort),
                                 (inventory[agent]['codex']['model'], inventory[agent]['codex']['effort']))


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-agent-contracts", allow_live_specs=True)

if __name__ == "__main__":
    raise SystemExit(main())
