#!/usr/bin/env python3
"""Consolidated Layer 1 contracts owned by validate-skill-contracts.py."""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for _import_root in (LIB_DIR, PLUGIN_ROOT):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))

from speckit_pro_runner.helpers.registry import MUTATION_HELPERS
from structural_helpers import body as _body
from structural_helpers import frontmatter as _frontmatter
from test_result import run_counted

# Contracts transferred from validate-skills.py.
validate_skills_SKILLS_DIR = PLUGIN_ROOT / 'skills'
validate_skills_SKILLS = ('grill-me', 'speckit-archive-cleanup', 'speckit-autopilot', 'speckit-coach', 'speckit-install', 'speckit-upgrade', 'speckit-scaffold-spec', 'speckit-status', 'speckit-resolve-pr', 'speckit-prd')
SKILLS_REQUIRING_REFERENCES = frozenset({'speckit-autopilot', 'speckit-coach'})
ALLOWED_KEYS = frozenset({'name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility', 'user-invocable', 'disable-model-invocation', 'argument-hint'})
NAME_RE = re.compile('^[a-z][a-z0-9]*(-[a-z0-9]+)*$')
TOP_LEVEL_KEY_RE = re.compile('^([a-zA-Z][a-zA-Z0-9_-]*):', re.MULTILINE)

def _field(frontmatter: str, key: str) -> str:
    for line in frontmatter.splitlines():
        if line.startswith(f'{key}:'):
            value = re.sub(f'^{key}:[ \\t]*', '', line)
            return value.replace('"', '').replace("'", '')
    return ''

def _description_value(frontmatter: str) -> str:
    block = re.search('description:\\s*([>|])\\s*\\n((?:\\s+.*\\n?)*)', frontmatter)
    if block:
        return ' '.join((line.strip() for line in block.group(2).split('\n') if line.strip()))
    inline = re.search('description:\\s*"([^"]*)"|description:\\s*(.+)', frontmatter)
    if inline:
        return (inline.group(1) or inline.group(2) or '').strip()
    return ''

class ValidateSkills(unittest.TestCase):

    def test_skills(self) -> None:
        for skill in validate_skills_SKILLS:
            skill_dir = validate_skills_SKILLS_DIR / skill
            skill_file = skill_dir / 'SKILL.md'
            with self.subTest(msg=f'{skill}: SKILL.md exists'):
                self.assertTrue(skill_file.is_file(), f'file not found: {skill_file}')
            if not skill_file.is_file():
                continue
            content = skill_file.read_text(encoding='utf-8')
            lines = content.splitlines()
            first_line = lines[0] if lines else ''
            with self.subTest(msg=f'{skill}: YAML frontmatter present (starts with ---)'):
                self.assertEqual('---', first_line, 'first line must be ---')
            with self.subTest(msg=f'{skill}: has closing ---'):
                fence_count = sum((1 for line in lines if line == '---'))
                self.assertGreaterEqual(fence_count, 2, f"expected at least 2 '---' lines, found {fence_count}")
            frontmatter = _frontmatter(lines)
            name_val = _field(frontmatter, 'name')
            with self.subTest(msg=f'{skill}: name: field exists and is kebab-case'):
                if not name_val:
                    self.fail('name field is missing')
                self.assertRegex(name_val, NAME_RE, 'name must be kebab-case')
            with self.subTest(msg=f'{skill}: name max 64 chars'):
                self.assertLessEqual(len(name_val), 64, f'name is {len(name_val)} chars (max 64)')
            with self.subTest(msg=f'{skill}: description: field exists'):
                self.assertIn('description:', frontmatter)
            desc_val = _description_value(frontmatter)
            with self.subTest(msg=f'{skill}: description max 1024 chars'):
                self.assertLessEqual(len(desc_val), 1024, f'description is {len(desc_val)} chars (max 1024)')
            with self.subTest(msg=f'{skill}: description has no angle brackets'):
                self.assertNotRegex(desc_val, '[<>]', 'description contains angle brackets')
            with self.subTest(msg=f'{skill}: only allowed frontmatter keys'):
                found_keys = TOP_LEVEL_KEY_RE.findall(frontmatter)
                bad_keys = [key for key in found_keys if key not in ALLOWED_KEYS]
                self.assertEqual([], bad_keys, 'disallowed frontmatter keys:' + ''.join((f' {key}' for key in bad_keys)))
            body = _body(lines)
            with self.subTest(msg=f'{skill}: body content exists'):
                self.assertTrue(body.strip(), 'body must contain non-whitespace content')
            if skill == 'grill-me':
                with self.subTest(msg='grill-me: Claude variant requires AskUserQuestion'):
                    self.assertTrue('AskUserQuestion' in body and 'Call `AskUserQuestion` for exactly one question at a time.' in body, 'expected Claude grill-me to retain its AskUserQuestion-only adapter')
            if skill == 'speckit-scaffold-spec':
                with self.subTest(msg='speckit-scaffold-spec: skill heading uses scaffold naming'):
                    self.assertTrue(re.search('^# SpecKit Scaffold Spec$', content, re.MULTILINE) is not None and re.search('^# SpecKit Setup$', content, re.MULTILINE) is None, "expected '# SpecKit Scaffold Spec' heading in skills/speckit-scaffold-spec/SKILL.md")
                with self.subTest(msg='speckit-scaffold-spec: completion report uses scaffold naming'):
                    self.assertTrue(re.search('^## Scaffold Complete$', content, re.MULTILINE) is not None and re.search('^## Setup Complete$', content, re.MULTILINE) is None, "expected '## Scaffold Complete' report heading in skills/speckit-scaffold-spec/SKILL.md")
            with self.subTest(msg=f'{skill}: references directory exists if required'):
                if skill in SKILLS_REQUIRING_REFERENCES:
                    self.assertTrue((skill_dir / 'references').is_dir(), f"references directory not found at {skill_dir / 'references'}")
                else:
                    self.assertTrue(True)
# Contracts transferred from validate-codex-skills.py.
validate_codex_skills_CODEX_SKILLS_DIR = PLUGIN_ROOT / 'codex-skills'
validate_codex_skills_SKILLS = ('speckit-archive-cleanup', 'speckit-autopilot', 'speckit-coach', 'speckit-scaffold-spec', 'speckit-status', 'speckit-resolve-pr', 'install', 'speckit-install', 'speckit-upgrade', 'grill-me', 'speckit-prd')
COLLISION_GUARD_SKILLS = ('speckit-archive-cleanup', 'speckit-autopilot', 'speckit-coach', 'grill-me', 'speckit-prd')
CC_ONLY_KEYS = ('user-invocable', 'disable-model-invocation', 'license', 'argument-hint')
CLAUDE_ONLY_RUNTIME_RE = re.compile('TaskCreate|TaskUpdate|Agent\\(|Bash\\(|Opus-class|Opus 4\\.6|/model opus|/effort max|/speckit[.:]|run /<command>|general-purpose agent')
ALLOW_IMPLICIT_RE = re.compile('^[ \\t]*allow_implicit_invocation:[ \\t]*(true|false)[ \\t]*$')

def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8') if path.is_file() else ''

def _allow_implicit_values(yaml_content: str) -> list[str]:
    values: list[str] = []
    for line in yaml_content.splitlines():
        match = ALLOW_IMPLICIT_RE.match(line)
        if match:
            values.append(match.group(1))
    return values

def _source_artifact_exists(skill: str) -> bool:
    if skill == 'install':
        return True
    return (PLUGIN_ROOT / 'skills' / skill / 'SKILL.md').is_file()

class ValidateCodexSkills(unittest.TestCase):

    def test_codex_skill_selection_collision_guards(self) -> None:
        for skill in COLLISION_GUARD_SKILLS:
            shared_skill_file = PLUGIN_ROOT / 'skills' / skill / 'SKILL.md'
            codex_skill_file = validate_codex_skills_CODEX_SKILLS_DIR / skill / 'SKILL.md'
            both_exist = shared_skill_file.is_file() and codex_skill_file.is_file()
            with self.subTest(msg=f'{skill}: shared and Codex variants both exist'):
                self.assertTrue(both_exist, f'expected both {shared_skill_file} and {codex_skill_file}')
            if not both_exist:
                continue
            shared_content = shared_skill_file.read_text(encoding='utf-8')
            with self.subTest(msg=f'{skill}: shared variant redirects when selected by Codex'):
                self.assertIn('Codex Skill-Selection Guard', shared_content)
            with self.subTest(msg=f'{skill}: shared guard names the Codex variant path'):
                self.assertIn(f'../../codex-skills/{skill}/SKILL.md', shared_content)

    def test_codex_skills(self) -> None:
        for skill in validate_codex_skills_SKILLS:
            skill_dir = validate_codex_skills_CODEX_SKILLS_DIR / skill
            skill_file = skill_dir / 'SKILL.md'
            with self.subTest(msg=f'{skill}: SKILL.md exists'):
                self.assertTrue(skill_file.is_file(), f'file not found: {skill_file}')
            if not skill_file.is_file():
                continue
            content = skill_file.read_text(encoding='utf-8')
            lines = content.splitlines()
            first_line = lines[0] if lines else ''
            with self.subTest(msg=f'{skill}: YAML frontmatter present (starts with ---)'):
                self.assertEqual('---', first_line, 'first line must be ---')
            with self.subTest(msg=f'{skill}: has closing ---'):
                fence_count = sum((1 for line in lines if line == '---'))
                self.assertGreaterEqual(fence_count, 2, f"expected at least 2 '---' lines, found {fence_count}")
            frontmatter = _frontmatter(lines)
            with self.subTest(msg=f'{skill}: has name: field'):
                self.assertIn('name:', frontmatter)
            with self.subTest(msg=f'{skill}: has description: field'):
                self.assertIn('description:', frontmatter)
            with self.subTest(msg=f'{skill}: no Claude Code-only frontmatter keys'):
                bad_keys = [key for key in CC_ONLY_KEYS if re.search(f'^{re.escape(key)}:', frontmatter, re.MULTILINE)]
                self.assertEqual([], bad_keys, 'Claude Code-only keys found:' + ''.join((f' {key}' for key in bad_keys)))
            with self.subTest(msg=f'{skill}: agents/openai.yaml sidecar exists'):
                self.assertTrue((skill_dir / 'agents' / 'openai.yaml').is_file(), f"file not found: {skill_dir / 'agents' / 'openai.yaml'}")
            if skill == 'speckit-scaffold-spec':
                sidecar_content = _read(skill_dir / 'agents' / 'openai.yaml')
                with self.subTest(msg='speckit-scaffold-spec: Codex picker metadata uses scaffold naming'):
                    self.assertTrue('display_name: "SpecKit Scaffold Spec"' in sidecar_content and 'default_prompt: "Scaffold a SPEC-ID from the technical roadmap for SpecKit autopilot"' in sidecar_content and ('SpecKit Setup' not in sidecar_content) and ('Set up a SPEC-ID' not in sidecar_content), 'expected scaffold naming in codex-skills/speckit-scaffold-spec/agents/openai.yaml')
                with self.subTest(msg='speckit-scaffold-spec: Codex skill heading uses scaffold naming'):
                    self.assertTrue(re.search('^# SpecKit Scaffold Spec$', content, re.MULTILINE) is not None and re.search('^# SpecKit Setup$', content, re.MULTILINE) is None, "expected '# SpecKit Scaffold Spec' heading in codex-skills/speckit-scaffold-spec/SKILL.md")
                dispatch_section = content.split('**Dispatch, then await.**', 1)[-1].split('**The bound.', 1)[0]
                with self.subTest(msg='speckit-scaffold-spec: blind-spot custom agent uses an isolated fork'):
                    self.assertTrue('`agent_type: "codebase-analyst"`' in dispatch_section and '`fork_turns: "none"`' in dispatch_section and ('`fork_turns: "all"`' in dispatch_section) and ('self-contained' in dispatch_section), 'expected blind-spot dispatch to select codebase-analyst with an explicit isolated fork')
                with self.subTest(msg='speckit-scaffold-spec: placement is task-root-bound before mutation'):
                    self.assertTrue('resolve-scaffold-worktree-placement' in content and 'Before `git worktree add` or any artifact or roadmap write' in content and ('`TASK_ROOT/.worktrees/<branch-name>`' in content) and ('Never derive worktree placement from' in content) and ('`git rev-parse --git-common-dir`' in content) and ('the primary checkout, or the first' in content) and ('`placement_status=resolved`' in content) and ('`relation=same` or `relation=descendant`' in content), 'expected scaffold to resolve task-root placement before any mutation')
                with self.subTest(msg='speckit-scaffold-spec: placement is revalidated before bootstrap'):
                    self.assertTrue('Re-run `resolve-scaffold-worktree-placement` after' in content and 'worktree creation and again before bootstrap or Grill Me' in content and ('`disposition=reuse`' in content) and ('before bootstrap or Grill Me' in content), 'expected scaffold to revalidate the identical registered root before bootstrap')
            body = _body(lines)
            with self.subTest(msg=f'{skill}: body content exists'):
                self.assertTrue(body.strip(), 'body must contain non-whitespace content')
            if skill == 'speckit-scaffold-spec':
                with self.subTest(msg='speckit-scaffold-spec: Codex Grill Me preserves foreground interaction'):
                    self.assertTrue('picker-first HITL guard' in body and 'request_user_input' in body and re.search('active\\s+foreground\\s+user\\s+chat', body) and re.search('same\\s+single\\s+Grill Me question\\s+in free text', body) and re.search('autonomous,\\s+background,\\s+CI,\\s+or subagent', body) and ('stop before writing' in body), 'expected scaffold to fall back only in a foreground user chat and stop autonomous runs')
            if skill == 'grill-me':
                with self.subTest(msg='grill-me: Codex picker fallback stays foreground-only'):
                    self.assertTrue('request_user_input' in body and 'already active user chat' in body and re.search('Ask exactly one question in the\\s+current conversation', body) and 'Never use this fallback in background, CI, autopilot, or subagent execution.' in body, 'expected picker preference, one-question foreground fallback, and a background stop boundary')
            if skill == 'speckit-autopilot':
                self._check_autopilot_skill(skill_dir, body)
            self._check_allow_implicit_invocation_policy(skill, skill_dir)
            with self.subTest(msg=f'{skill}: corresponding source artifact exists'):
                self.assertTrue(_source_artifact_exists(skill), f'corresponding Claude skill not found at skills/{skill}/SKILL.md')
            if skill == 'speckit-scaffold-spec':
                with self.subTest(msg='speckit-scaffold-spec: referenced workflow template exists (skills/speckit-coach/templates/workflow-template.md)'):
                    self.assertTrue((PLUGIN_ROOT / 'skills' / 'speckit-coach' / 'templates' / 'workflow-template.md').is_file(), f"file not found: {PLUGIN_ROOT / 'skills' / 'speckit-coach' / 'templates' / 'workflow-template.md'}")
            if skill == 'install':
                with self.subTest(msg='install: installer helper is documented'):
                    entry = MUTATION_HELPERS['install-codex-agents']
                    self.assertTrue('install-codex-agents' in body and 'dry_run' in body and ('apply' in body) and ('verified' in body) and (entry.promotion_status == 'golden_only') and bool(entry.authoritative_command), 'expected a promoted, fixture-backed install-codex-agents dry-run/apply contract')

    def _check_autopilot_skill(self, skill_dir: Path, body: str) -> None:
        phase_execution = _read(skill_dir / 'references' / 'phase-execution-codex.md')
        post_implementation = _read(skill_dir / 'references' / 'post-implementation-codex.md')
        error_recovery = _read(skill_dir / 'references' / 'error-recovery-codex.md')
        runtime_doc = f"{body}\n{phase_execution}\n{post_implementation}\n{error_recovery}"
        with self.subTest(msg='speckit-autopilot: requires update_plan as the progress contract'):
            self.assertIn('update_plan', runtime_doc)
        with self.subTest(msg='speckit-autopilot: requires durable autopilot-state.json persistence'):
            self.assertIn('autopilot-state.json', runtime_doc)
        with self.subTest(msg='speckit-autopilot: names Codex-native delegation tools'):
            self.assertTrue('spawn_agent' in runtime_doc and 'wait_agent' in runtime_doc, 'expected both spawn_agent and wait_agent in the Codex autopilot skill')
        with self.subTest(msg='speckit-autopilot: routes consensus through the parse-consensus-categories helper'):
            self.assertIn('parse-consensus-categories', body)
            self.assertNotIn('per the routing table', body)
            self.assertNotIn('codebase-analyst only', body)
        with self.subTest(msg='speckit-autopilot: maps hosted and local Codex follow-up tools'):
            self.assertTrue('followup_task' in runtime_doc and 'send_message' in runtime_doc and ('resume_agent' in runtime_doc) and ('send_input' in runtime_doc), 'expected hosted followup_task/send_message plus local send_input and resume-then-send_input handling')
        with self.subTest(msg='speckit-autopilot: adapts agent cleanup to the exposed Codex surface'):
            self.assertTrue('absence of `close_agent` is NOT' in runtime_doc and 'prerequisite failure' in runtime_doc and ('only when `close_agent` is exposed' in runtime_doc) and ('interrupt_agent' in runtime_doc) and ('list_agents' in runtime_doc) and ('terminal status is corroboration or recovery evidence only' in runtime_doc) and ('A `wait_agent` timeout is one bounded mailbox poll' in runtime_doc) and ('`close_agent` is REQUIRED' not in runtime_doc), 'expected capability-aware hosted/local lifecycle handling without a close_agent hard requirement')
        with self.subTest(msg='speckit-autopilot: validates a single in_progress item before phase execution'):
            self.assertIn('Exactly one plan item is `in_progress`', body)
        with self.subTest(msg='speckit-autopilot: requires all canonical phase families before execution'):
            self.assertTrue('phase family coverage is mandatory' in runtime_doc and 'Phase 7: Implement - Pending task decomposition' in runtime_doc and ('Post: Doctor Extension Check' in runtime_doc) and ('Post: Retrospective' in runtime_doc), 'expected all-phase coverage, Phase 7 placeholder, and the canonical Post item list (Doctor Extension Check -> Retrospective) in the Codex autopilot skill')
        with self.subTest(msg='speckit-autopilot: documents canonical PHASES order'):
            self.assertIn('PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]', runtime_doc)
        with self.subTest(msg='speckit-autopilot: prevents from-phase from dropping later phases'):
            self.assertTrue(
                'Read the workflow file and apply\n[`phase-execution-codex.md`](./references/phase-execution-codex.md)\n§Stage-Bounded Execution.' in body
                and '`--from-phase` changes the first phase to execute, not the required plan\ncoverage.' in phase_execution
                and 'all seven SDD phases, and Post before any subagent is spawned.' in phase_execution
                and 'a value outside an explicitly named stage\'s range is rejected at Step\n0.6c before any phase work begins.' in phase_execution,
                'expected the entrypoint to require the stage-bounded reference, which keeps whole-plan coverage visible and rejects out-of-stage --from-phase values',
            )
        with self.subTest(msg='speckit-autopilot: requires concrete Phase 7 tasks after G5'):
            self.assertTrue(
                'Before performing it, read\n[`phase-execution-codex.md`](./references/phase-execution-codex.md)\n§Phase 7: Implement' in body
                and 'After G5 passes, the placeholder is invalid.' in phase_execution
                and '- no `Phase 7: Implement - Pending task decomposition` item remains' in phase_execution
                and '- each concrete item names one or more task IDs parsed from `tasks.md`' in phase_execution
                and 'Correctness stops remain blocking:' in phase_execution,
                'expected the entrypoint to require Phase 7 guidance that removes the G5 placeholder, names concrete task IDs, and retains correctness stops',
            )
        with self.subTest(msg='speckit-autopilot: resumes into Post before reporting complete'):
            self.assertTrue(
                'After Phase 7 passes G7, read and execute\n[`post-implementation-codex.md`](./references/post-implementation-codex.md)\nin canonical order.' in body
                and 'all seven SDD phases being complete is not sufficient to stop.' in post_implementation
                and 'continue with the first incomplete Post item.' in post_implementation
                and 'resume at the first incomplete Post\n   item. Do not summarize completion from a `Phase 7: Implement Complete`\n   state.' in error_recovery,
                'expected the Post entrypoint and recovery reference to continue from the first incomplete Post item without a premature completion summary',
            )
        with self.subTest(msg='speckit-autopilot: blocks final answers while Post items remain incomplete'):
            self.assertTrue(
                '### 3.4 Pre-final completion audit' in body
                and 'You MUST NOT send a\nfinal response if any `Post:` item is `pending`, `in_progress`, or missing.' in body
                and 'set the first\nincomplete item to `in_progress` in both state stores and continue the\nautopilot loop instead of summarizing.' in body
                and '`Post: Retrospective` is the final\nPost item; it must be completed or explicitly skipped before the\nautopilot can report completion.' in body,
                'expected the direct final audit to forbid completion, continue the first incomplete Post item, and require Retrospective',
            )
        with self.subTest(msg='speckit-autopilot: documents skill-local agents/openai.yaml metadata'):
            self.assertIn('agents/openai.yaml', body)
        with self.subTest(msg='speckit-autopilot: validates installed Codex subagent paths'):
            self.assertTrue('.codex/agents/' in body and '~/.codex/agents/' in body, 'expected both project and user Codex subagent paths in the autopilot skill')
        with self.subTest(msg='speckit-autopilot: fails closed to the install skill when subagents are missing'):
            prerequisites = _read(skill_dir / 'references' / 'prerequisites-codex.md')
            self.assertTrue('$install' in body and '$install' in prerequisites and ('install-codex-agents' in prerequisites) and ('dry_run' in prerequisites) and ('validate-agent-install' not in prerequisites) and ('--autoheal' not in prerequisites), 'expected read-only installer dry-run preflight and install/restart fail-closed guidance')
        with self.subTest(msg='speckit-autopilot: external recovery opens a correctly rooted task'):
            prerequisites = _read(skill_dir / 'references' / 'prerequisites-codex.md')
            self.assertTrue('Open a new Codex task rooted at <workflow_root>' in prerequisites and 'exact absolute workflow command' in prerequisites and ('original stage flags' in prerequisites) and ('Use Codex Handoff to move this task to' not in prerequisites), 'expected fail-closed external recovery without arbitrary-path Handoff claims')
        with self.subTest(msg='speckit-autopilot: documents the optional Luna helper'):
            self.assertIn('autopilot-fast-helper', body)
        with self.subTest(msg='speckit-autopilot: keeps the Luna helper advisory and parent-only'):
            self.assertTrue('Only the parent orchestrator may call this helper' in body and 'latency optimization, not a dependency' in body, 'expected parent-only and optional guardrails for autopilot-fast-helper')
        with self.subTest(msg='speckit-autopilot: does not bundle skill-local TOML subagents'):
            agents_dir = skill_dir / 'agents'
            bundled_count = len(list(agents_dir.glob('*.toml'))) if agents_dir.is_dir() else 0
            self.assertEqual('0', str(bundled_count), 'expected no bundled custom-agent templates in speckit-autopilot/agents')
        with self.subTest(msg='speckit-autopilot: excludes Claude-only runtime primitives'):
            self.assertIsNone(CLAUDE_ONLY_RUNTIME_RE.search(runtime_doc), 'found Claude-only primitive or runtime guidance in Codex autopilot skill')
        with self.subTest(msg='speckit-autopilot: Codex-specific references exist'):
            self.assertTrue((skill_dir / 'references' / 'phase-execution-codex.md').is_file())
        with self.subTest(msg='speckit-autopilot: Codex post-implementation reference exists'):
            self.assertTrue((skill_dir / 'references' / 'post-implementation-codex.md').is_file())
        with self.subTest(msg='speckit-autopilot: Codex SKILL.md names the plan-phase estimator helper'):
            self.assertIn('estimate-reviewable-loc', body)
        with self.subTest(msg='speckit-autopilot: Codex SKILL.md carries the three-value status vocab'):
            self.assertIn('`pass` / `over_budget` / `not_estimated`', body)
        phase_exec = _read(skill_dir / 'references' / 'phase-execution-codex.md')
        with self.subTest(msg='speckit-autopilot: phase-execution-codex.md names the plan-phase estimator helper'):
            self.assertIn('estimate-reviewable-loc', phase_exec)
        with self.subTest(msg='speckit-autopilot: phase-execution-codex.md documents the over_budget status'):
            self.assertIn('over_budget', phase_exec)
        with self.subTest(msg='speckit-autopilot: phase-execution-codex.md documents the not_estimated status'):
            self.assertIn('not_estimated', phase_exec)

    def _check_allow_implicit_invocation_policy(self, skill: str, skill_dir: Path) -> None:
        sidecar = skill_dir / 'agents' / 'openai.yaml'
        with self.subTest(msg=f'{skill}: agents/openai.yaml allow_implicit_invocation policy'):
            if not sidecar.is_file():
                self.fail('agents/openai.yaml not found; skipping policy check')
            values = _allow_implicit_values(sidecar.read_text(encoding='utf-8'))
            if len(values) != 1:
                self.fail('agents/openai.yaml must declare exactly one anchored allow_implicit_invocation policy')
            policy_value = values[0]
            if skill == 'speckit-scaffold-spec':
                self.assertEqual('true', policy_value, 'scaffold skill must have allow_implicit_invocation: true for Codex discovery')
            elif skill in ('speckit-archive-cleanup', 'speckit-autopilot', 'speckit-resolve-pr', 'install', 'speckit-install', 'speckit-upgrade', 'grill-me', 'speckit-prd'):
                self.assertEqual('false', policy_value, 'mutation-heavy skill must have allow_implicit_invocation: false')
            elif skill in ('speckit-coach', 'speckit-status'):
                self.assertEqual('true', policy_value, 'read-only skill must have allow_implicit_invocation: true')
            else:
                self.fail(f"no implicit-invocation policy expectation defined for '{skill}'; update validate-codex-skills.sh")
            if skill == 'speckit-autopilot':
                self.assertNotIn('dependencies:', sidecar.read_text(encoding='utf-8'), 'autopilot optional research capabilities must not be declared as required tool dependencies')
# Contracts transferred from validate-capability-pointer.py.
validate_capability_pointer_AGENTS_DIR = PLUGIN_ROOT / 'agents'
validate_capability_pointer_CODEX_AGENTS_DIR = PLUGIN_ROOT / 'codex-agents'
validate_capability_pointer_DIRECTIVE_MARKER = 'capability-discovery.md'
validate_capability_pointer_GROUNDING_MARKER = 'grounding.md'
CAPABILITY_NOTE = 'Capability path:'
validate_capability_pointer_CC_EXCLUSIONS = frozenset({'consensus-synthesizer', 'phase-executor', 'sweep-analyst', 'sweep-classifier'})
validate_capability_pointer_CODEX_EXCLUSIONS = frozenset({'autopilot-fast-helper', 'phase-executor'})
APPROVED_EQUIVALENTS: frozenset[str] = frozenset()

def validate_capability_pointer__rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()

def validate_capability_pointer__excluded(runtime: str, name: str) -> bool:
    return name in (validate_capability_pointer_CC_EXCLUSIONS if runtime == 'claude' else validate_capability_pointer_CODEX_EXCLUSIONS)

def _approved_equivalent(runtime: str, name: str) -> bool:
    return f'{runtime}:{name}' in APPROVED_EQUIVALENTS

class ValidateCapabilityPointer(unittest.TestCase):

    def _check_runtime(self, runtime: str, directory: Path, ext: str) -> None:
        rel_dir = validate_capability_pointer__rel(directory)
        with self.subTest(msg=f'{runtime}: agents directory exists ({rel_dir})'):
            self.assertTrue(directory.is_dir(), f'agents directory missing: {rel_dir}')
        if not directory.is_dir():
            return
        files = sorted((f for f in directory.glob(f'*.{ext}') if f.is_file()))
        with self.subTest(msg=f'{runtime}: active-agent glob matched at least one agent'):
            self.assertTrue(files, f'no active agents found under {rel_dir}/*.{ext}')
        if not files:
            return
        for agent_file in files:
            agent_name = agent_file.name[:-(len(ext) + 1)]
            if validate_capability_pointer__excluded(runtime, agent_name):
                continue
            text = agent_file.read_text(encoding='utf-8', errors='replace')
            with self.subTest(msg=f"{runtime}: in-scope agent '{agent_name}' references {validate_capability_pointer_DIRECTIVE_MARKER} (or approved equivalent)"):
                self.assertTrue(validate_capability_pointer_DIRECTIVE_MARKER in text or _approved_equivalent(runtime, agent_name), f"uncovered in-scope agent: {runtime} '{agent_name}' references neither {validate_capability_pointer_DIRECTIVE_MARKER} nor an approved equivalent")
            with self.subTest(msg=f"{runtime}: in-scope agent '{agent_name}' references {validate_capability_pointer_GROUNDING_MARKER}"):
                self.assertIn(validate_capability_pointer_GROUNDING_MARKER, text, f"{runtime} '{agent_name}' does not reference {validate_capability_pointer_GROUNDING_MARKER}")
            with self.subTest(msg=f"{runtime}: in-scope agent '{agent_name}' output requires the grounding evidence note"):
                self.assertIn(CAPABILITY_NOTE, text, f"in-scope agent '{agent_name}' ({runtime}) output format does not require the grounding evidence note")

    def test_pointer_coverage(self) -> None:
        self._check_runtime('claude', validate_capability_pointer_AGENTS_DIR, 'md')
        self._check_runtime('codex', validate_capability_pointer_CODEX_AGENTS_DIR, 'toml')
# Contracts transferred from validate-capability-resolution.py.
validate_capability_resolution_AGENTS_DIR = PLUGIN_ROOT / 'agents'
validate_capability_resolution_CODEX_AGENTS_DIR = PLUGIN_ROOT / 'codex-agents'
validate_capability_resolution_DIST_CLAUDE = REPO_ROOT / 'dist' / 'claude'
validate_capability_resolution_DIST_CODEX = REPO_ROOT / 'dist' / 'codex'
validate_capability_resolution_DIRECTIVE_MARKER = 'capability-discovery.md'
validate_capability_resolution_GROUNDING_MARKER = 'grounding.md'
validate_capability_resolution_PATH_TOKEN_RE = re.compile('speckit-pro/[A-Za-z0-9._/-]*capability-discovery\\.md')
validate_capability_resolution_GROUNDING_TOKEN_RE = re.compile('speckit-pro/[A-Za-z0-9._/-]*grounding\\.md')
validate_capability_resolution_CC_EXCLUSIONS = frozenset({'consensus-synthesizer', 'phase-executor'})
validate_capability_resolution_CODEX_EXCLUSIONS = frozenset({'autopilot-fast-helper', 'phase-executor'})

def validate_capability_resolution__rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()

def validate_capability_resolution__excluded(runtime: str, name: str) -> bool:
    return name in (validate_capability_resolution_CC_EXCLUSIONS if runtime == 'claude' else validate_capability_resolution_CODEX_EXCLUSIONS)

class ValidateCapabilityResolution(unittest.TestCase):

    def _collect_runtime(self, runtime: str, directory: Path, ext: str, found_tokens: list[str]) -> None:
        rel_dir = validate_capability_resolution__rel(directory)
        with self.subTest(msg=f'{runtime}: agents directory exists ({rel_dir})'):
            self.assertTrue(directory.is_dir(), f'agents directory missing: {rel_dir}')
        if not directory.is_dir():
            return
        files = sorted((f for f in directory.glob(f'*.{ext}') if f.is_file()))
        with self.subTest(msg=f'{runtime}: active-agent glob matched at least one agent'):
            self.assertTrue(files, f'no active agents found under {rel_dir}/*.{ext}')
        if not files:
            return
        for agent_file in files:
            agent_name = agent_file.name[:-(len(ext) + 1)]
            if validate_capability_resolution__excluded(runtime, agent_name):
                continue
            text = agent_file.read_text(encoding='utf-8', errors='replace')
            if validate_capability_resolution_DIRECTIVE_MARKER not in text:
                continue
            directive_tokens = sorted(set(validate_capability_resolution_PATH_TOKEN_RE.findall(text)))
            for token in directive_tokens:
                if token not in found_tokens:
                    found_tokens.append(token)
            with self.subTest(msg=f"{runtime}: extracted directive path token(s) from in-scope agent '{agent_name}'"):
                self.assertTrue(directive_tokens, f'agent references {validate_capability_resolution_DIRECTIVE_MARKER} but no path token matched in {validate_capability_resolution__rel(agent_file)}')
            if validate_capability_resolution_GROUNDING_MARKER in text:
                grounding_tokens = sorted(set(validate_capability_resolution_GROUNDING_TOKEN_RE.findall(text)))
                for token in grounding_tokens:
                    if token not in found_tokens:
                        found_tokens.append(token)
                with self.subTest(msg=f"{runtime}: extracted grounding path token(s) from in-scope agent '{agent_name}'"):
                    self.assertTrue(grounding_tokens, f'agent references {validate_capability_resolution_GROUNDING_MARKER} but no path token matched in {validate_capability_resolution__rel(agent_file)}')

    def test_target_resolution(self) -> None:
        found_tokens: list[str] = []
        self._collect_runtime('claude', validate_capability_resolution_AGENTS_DIR, 'md', found_tokens)
        self._collect_runtime('codex', validate_capability_resolution_CODEX_AGENTS_DIR, 'toml', found_tokens)
        with self.subTest(msg='at least one directive path token was collected from the inventory'):
            self.assertTrue(found_tokens, 'no directive path tokens collected — refusing to report success on zero work')
        if not found_tokens:
            return
        with self.subTest(msg=f'built Claude payload tree exists ({validate_capability_resolution__rel(validate_capability_resolution_DIST_CLAUDE)})'):
            self.assertTrue(validate_capability_resolution_DIST_CLAUDE.is_dir(), f'missing built tree: {validate_capability_resolution__rel(validate_capability_resolution_DIST_CLAUDE)}')
        with self.subTest(msg=f'built Codex payload tree exists ({validate_capability_resolution__rel(validate_capability_resolution_DIST_CODEX)})'):
            self.assertTrue(validate_capability_resolution_DIST_CODEX.is_dir(), f'missing built tree: {validate_capability_resolution__rel(validate_capability_resolution_DIST_CODEX)}')
        for token in found_tokens:
            with self.subTest(msg=f'resolves under dist/claude: {token}'):
                self.assertTrue((validate_capability_resolution_DIST_CLAUDE / token).is_file(), f'absent in built Claude tree: dist/claude/{token}')
            with self.subTest(msg=f'resolves under dist/codex: {token}'):
                self.assertTrue((validate_capability_resolution_DIST_CODEX / token).is_file(), f'absent in built Codex tree: dist/codex/{token}')
# Contracts transferred from validate-skill-capability-pointers.py.
CLAUDE_SKILLS_DIR = PLUGIN_ROOT / 'skills'
validate_skill_capability_pointers_CODEX_SKILLS_DIR = PLUGIN_ROOT / 'codex-skills'
validate_skill_capability_pointers_DIST_CLAUDE = REPO_ROOT / 'dist' / 'claude'
validate_skill_capability_pointers_DIST_CODEX = REPO_ROOT / 'dist' / 'codex'
validate_skill_capability_pointers_DIRECTIVE_MARKER = 'capability-discovery.md'
validate_skill_capability_pointers_GROUNDING_MARKER = 'grounding.md'
PLUGIN_ROOT_VAR = '${CLAUDE_PLUGIN_ROOT}/'
PLUGIN_ROOT_PREFIX = 'speckit-pro/'
validate_skill_capability_pointers_PATH_TOKEN_RE = re.compile('(?:speckit-pro/|\\$\\{CLAUDE_PLUGIN_ROOT\\}/)[A-Za-z0-9._/-]*capability-discovery\\.md')
validate_skill_capability_pointers_GROUNDING_TOKEN_RE = re.compile('(?:speckit-pro/|\\$\\{CLAUDE_PLUGIN_ROOT\\}/)[A-Za-z0-9._/-]*grounding\\.md')

def _payload_relative(token: str) -> str:
    """Normalize either pointer form to a path under a built payload tree."""
    if token.startswith(PLUGIN_ROOT_VAR):
        return PLUGIN_ROOT_PREFIX + token[len(PLUGIN_ROOT_VAR):]
    return token
EXCLUSIONS = frozenset({'speckit-install', 'install', 'speckit-upgrade', 'speckit-status', 'speckit-archive-cleanup'})
HOST_SKILL = 'speckit-autopilot'

def validate_skill_capability_pointers__rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()

def _display_path(path: Path) -> str:
    try:
        return validate_skill_capability_pointers__rel(path)
    except ValueError:
        return path.as_posix()

def _skill_dirs(directory: Path) -> list[Path]:
    return sorted((p for p in directory.iterdir() if (p / 'SKILL.md').is_file()), key=lambda p: p.name)

def _unique_matches(pattern: re.Pattern[str], text: str) -> list[str]:
    return sorted(set(pattern.findall(text)))

class ValidateSkillCapabilityPointers(unittest.TestCase):

    def setUp(self) -> None:
        self.found_tokens: list[str] = []

    def _token_seen(self, token: str) -> bool:
        return token in self.found_tokens

    def _collect_marker(self, runtime: str, skill: str, skill_file: Path, marker: str, pattern: re.Pattern[str]) -> None:
        text = skill_file.read_text(encoding='utf-8', errors='replace')
        with self.subTest(msg=f"{runtime} skill '{skill}' references {marker}"):
            if marker not in text:
                self.fail(f"in-scope skill '{skill}' ({runtime}) does not reference {marker} (add the pointer, or record it in EXCLUSIONS with a reason - do NOT widen EXCLUSIONS to silence it)")
        matches = _unique_matches(pattern, text)
        for token in matches:
            payload_token = _payload_relative(token)
            if not self._token_seen(payload_token):
                self.found_tokens.append(payload_token)
        with self.subTest(msg=f"{runtime} skill '{skill}' {marker} reference yields a repo-root-relative path token"):
            self.assertTrue(matches, f'skill references {marker} but no token matched {pattern.pattern} in {_display_path(skill_file)}')

    def _check_runtime(self, runtime: str, directory: Path) -> None:
        with self.subTest(msg=f'{runtime}: skills directory exists ({validate_skill_capability_pointers__rel(directory)})'):
            self.assertTrue(directory.is_dir(), f'skills directory missing: {validate_skill_capability_pointers__rel(directory)}')
        if not directory.is_dir():
            return
        skill_dirs = _skill_dirs(directory)
        with self.subTest(msg=f'{runtime}: at least one skill with a SKILL.md was found'):
            self.assertTrue(skill_dirs, f'no skills found under {validate_skill_capability_pointers__rel(directory)}/*/SKILL.md (empty glob - refusing to pass vacuously)')
        if not skill_dirs:
            return
        for skill_dir in skill_dirs:
            skill = skill_dir.name
            skill_file = skill_dir / 'SKILL.md'
            if skill in EXCLUSIONS:
                continue
            if skill == HOST_SKILL:
                text = skill_file.read_text(encoding='utf-8', errors='replace')
                with self.subTest(msg=f"{runtime} host skill '{skill}' references {validate_skill_capability_pointers_DIRECTIVE_MARKER}"):
                    self.assertIn(validate_skill_capability_pointers_DIRECTIVE_MARKER, text, f"host skill '{skill}' ({runtime}) dropped its {validate_skill_capability_pointers_DIRECTIVE_MARKER} reference")
                with self.subTest(msg=f"{runtime} host skill '{skill}' references {validate_skill_capability_pointers_GROUNDING_MARKER}"):
                    self.assertIn(validate_skill_capability_pointers_GROUNDING_MARKER, text, f"host skill '{skill}' ({runtime}) dropped its {validate_skill_capability_pointers_GROUNDING_MARKER} reference")
                continue
            self._collect_marker(runtime, skill, skill_file, validate_skill_capability_pointers_DIRECTIVE_MARKER, validate_skill_capability_pointers_PATH_TOKEN_RE)
            self._collect_marker(runtime, skill, skill_file, validate_skill_capability_pointers_GROUNDING_MARKER, validate_skill_capability_pointers_GROUNDING_TOKEN_RE)

    def test_skill_pointer_coverage_and_resolution(self) -> None:
        self._check_runtime('claude', CLAUDE_SKILLS_DIR)
        self._check_runtime('codex', validate_skill_capability_pointers_CODEX_SKILLS_DIR)
        with self.subTest(msg='at least one skill directive/grounding token was collected'):
            self.assertTrue(self.found_tokens, 'no skill path tokens collected - refusing to report resolution success on zero work')
        if not self.found_tokens:
            return
        with self.subTest(msg=f'built Claude payload tree exists ({validate_skill_capability_pointers__rel(validate_skill_capability_pointers_DIST_CLAUDE)})'):
            self.assertTrue(validate_skill_capability_pointers_DIST_CLAUDE.is_dir(), f'missing built tree: {_display_path(validate_skill_capability_pointers_DIST_CLAUDE)}')
        with self.subTest(msg=f'built Codex payload tree exists ({validate_skill_capability_pointers__rel(validate_skill_capability_pointers_DIST_CODEX)})'):
            self.assertTrue(validate_skill_capability_pointers_DIST_CODEX.is_dir(), f'missing built tree: {_display_path(validate_skill_capability_pointers_DIST_CODEX)}')
        for token in self.found_tokens:
            with self.subTest(msg=f'resolves under dist/claude: {token}'):
                self.assertTrue((validate_skill_capability_pointers_DIST_CLAUDE / token).is_file(), f'skill reference correct in source but absent in built Claude tree (dist/claude/{token})')
            with self.subTest(msg=f'resolves under dist/codex: {token}'):
                self.assertTrue((validate_skill_capability_pointers_DIST_CODEX / token).is_file(), f'skill reference correct in source but absent in built Codex tree (dist/codex/{token})')
# Contracts transferred from validate-codex-parity.py.
CC_PLUGIN = PLUGIN_ROOT / '.claude-plugin' / 'plugin.json'
CODEX_PLUGIN = PLUGIN_ROOT / '.codex-plugin' / 'plugin.json'
CC_MARKETPLACE = REPO_ROOT / '.claude-plugin' / 'marketplace.json'
CODEX_MARKETPLACE = REPO_ROOT / '.agents' / 'plugins' / 'marketplace.json'
validate_codex_parity_AGENTS_DIR = PLUGIN_ROOT / 'agents'
validate_codex_parity_CODEX_AGENTS_DIR = PLUGIN_ROOT / 'codex-agents'
validate_codex_parity_SKILLS_DIR = PLUGIN_ROOT / 'skills'
validate_codex_parity_CODEX_SKILLS_DIR = PLUGIN_ROOT / 'codex-skills'
CC_ONLY_AGENTS = frozenset({'consensus-synthesizer', 'sweep-classifier', 'sweep-analyst'})
CODEX_ONLY_AGENTS = frozenset({'autopilot-fast-helper'})
REF_RE = re.compile('\\.\\./\\.\\./skills/[^)]+\\.md')

def _json_field(path: Path, key: str) -> str:
    """Mirror ``jq -r '.<key>'``: the value's string form, or ``null`` on
    missing key / unreadable / invalid JSON."""
    try:
        value = json.loads(path.read_text(encoding='utf-8')).get(key)
    except (json.JSONDecodeError, OSError, AttributeError):
        return 'null'
    return 'null' if value is None else str(value)

def _sorted_files(directory: Path, suffix: str) -> list[Path]:
    return sorted((p for p in directory.glob(f'*{suffix}') if p.is_file()), key=lambda p: p.name)

def _sorted_subdirs(directory: Path) -> list[Path]:
    return sorted((p for p in directory.iterdir() if p.is_dir()), key=lambda p: p.name)

class ValidateCodexParity(unittest.TestCase):

    def test_codex_parity(self) -> None:
        with self.subTest(msg='both plugin.json files exist'):
            self.assertTrue(CC_PLUGIN.is_file() and CODEX_PLUGIN.is_file(), f'missing one or both plugin.json files (CC: {CC_PLUGIN}, Codex: {CODEX_PLUGIN})')
        if CC_PLUGIN.is_file() and CODEX_PLUGIN.is_file():
            cc_version = _json_field(CC_PLUGIN, 'version')
            codex_version = _json_field(CODEX_PLUGIN, 'version')
            with self.subTest(msg=f'CC and Codex plugin.json versions match ({cc_version})'):
                self.assertEqual(cc_version, codex_version, f'versions must match: CC={cc_version}, Codex={codex_version}')
        with self.subTest(msg='both marketplace.json files exist'):
            self.assertTrue(CC_MARKETPLACE.is_file() and CODEX_MARKETPLACE.is_file(), f'missing one or both marketplace.json files (CC: {CC_MARKETPLACE}, Codex: {CODEX_MARKETPLACE})')
        if CC_MARKETPLACE.is_file() and CODEX_MARKETPLACE.is_file():
            cc_marketplace_name = _json_field(CC_MARKETPLACE, 'name')
            codex_marketplace_name = _json_field(CODEX_MARKETPLACE, 'name')
            with self.subTest(msg=f'CC and Codex marketplace names match ({cc_marketplace_name})'):
                self.assertEqual(cc_marketplace_name, codex_marketplace_name, f'marketplace names must match: CC={cc_marketplace_name}, Codex={codex_marketplace_name}')
        if validate_codex_parity_AGENTS_DIR.is_dir() and validate_codex_parity_CODEX_AGENTS_DIR.is_dir():
            for cc_agent_file in _sorted_files(validate_codex_parity_AGENTS_DIR, '.md'):
                agent_name = cc_agent_file.name[:-len('.md')]
                if agent_name in CC_ONLY_AGENTS:
                    continue
                with self.subTest(msg=f'codex-agents/{agent_name}.toml exists for CC agent'):
                    self.assertTrue((validate_codex_parity_CODEX_AGENTS_DIR / f'{agent_name}.toml').is_file(), f"file not found: {validate_codex_parity_CODEX_AGENTS_DIR / (agent_name + '.toml')}")
            for agent_name, resource_name in (('sweep-analyst', 'analyst.md'), ('sweep-classifier', 'classifier.md')):
                resource = validate_codex_parity_CODEX_SKILLS_DIR / 'speckit-autopilot' / 'references' / 'sweep-prompts' / resource_name
                with self.subTest(msg=f'codex trusted launcher resource exists for {agent_name}'):
                    self.assertTrue(resource.is_file(), f'file not found: {resource}')
        else:
            with self.subTest(msg='agents/ and codex-agents/ directories exist'):
                self.fail(f'one or both agent directories missing (CC: {validate_codex_parity_AGENTS_DIR}, Codex: {validate_codex_parity_CODEX_AGENTS_DIR})')
        if validate_codex_parity_AGENTS_DIR.is_dir() and validate_codex_parity_CODEX_AGENTS_DIR.is_dir():
            for codex_agent_file in _sorted_files(validate_codex_parity_CODEX_AGENTS_DIR, '.toml'):
                agent_name = codex_agent_file.name[:-len('.toml')]
                if agent_name in CODEX_ONLY_AGENTS:
                    continue
                with self.subTest(msg=f'agents/{agent_name}.md exists for Codex agent'):
                    self.assertTrue((validate_codex_parity_AGENTS_DIR / f'{agent_name}.md').is_file(), f"file not found: {validate_codex_parity_AGENTS_DIR / (agent_name + '.md')}")
        if validate_codex_parity_SKILLS_DIR.is_dir() and validate_codex_parity_CODEX_SKILLS_DIR.is_dir():
            for skill_dir in _sorted_subdirs(validate_codex_parity_SKILLS_DIR):
                skill_name = skill_dir.name
                with self.subTest(msg=f'skills/{skill_name}/SKILL.md exists'):
                    self.assertTrue((validate_codex_parity_SKILLS_DIR / skill_name / 'SKILL.md').is_file(), f"file not found: {validate_codex_parity_SKILLS_DIR / skill_name / 'SKILL.md'}")
                with self.subTest(msg=f'codex-skills/{skill_name}/SKILL.md exists for CC skill'):
                    self.assertTrue((validate_codex_parity_CODEX_SKILLS_DIR / skill_name / 'SKILL.md').is_file(), f"file not found: {validate_codex_parity_CODEX_SKILLS_DIR / skill_name / 'SKILL.md'}")
        else:
            with self.subTest(msg='skills/ and codex-skills/ directories exist'):
                self.fail(f'one or both skills directories missing (CC: {validate_codex_parity_SKILLS_DIR}, Codex: {validate_codex_parity_CODEX_SKILLS_DIR})')
        if validate_codex_parity_CODEX_SKILLS_DIR.is_dir():
            for skill_dir in _sorted_subdirs(validate_codex_parity_CODEX_SKILLS_DIR):
                skill_name = skill_dir.name
                with self.subTest(msg=f'codex-skills/{skill_name}/agents/openai.yaml exists'):
                    self.assertTrue((validate_codex_parity_CODEX_SKILLS_DIR / skill_name / 'agents' / 'openai.yaml').is_file(), f"file not found: {validate_codex_parity_CODEX_SKILLS_DIR / skill_name / 'agents' / 'openai.yaml'}")
        else:
            with self.subTest(msg='codex-skills/ directory exists for metadata sidecars'):
                self.fail(f'codex-skills directory missing: {validate_codex_parity_CODEX_SKILLS_DIR}')
        if validate_codex_parity_SKILLS_DIR.is_dir() and validate_codex_parity_CODEX_SKILLS_DIR.is_dir():
            for skill_dir in _sorted_subdirs(validate_codex_parity_SKILLS_DIR):
                skill_name = skill_dir.name
                cc_refs = validate_codex_parity_SKILLS_DIR / skill_name / 'references'
                if not cc_refs.is_dir():
                    continue
                with self.subTest(msg=f'{skill_name}: CC skill references/ has at least one file'):
                    ref_count = sum((1 for p in cc_refs.iterdir() if p.is_file()))
                    self.assertGreater(ref_count, 0, f'skills/{skill_name}/references/ exists but contains no files')
                codex_skill_file = validate_codex_parity_CODEX_SKILLS_DIR / skill_name / 'SKILL.md'
                if codex_skill_file.is_file():
                    text = codex_skill_file.read_text(encoding='utf-8', errors='replace')
                    matches: list[str] = []
                    for line in text.splitlines():
                        matches.extend(REF_RE.findall(line))
                    for rel_path in sorted(set(matches)):
                        stripped = rel_path.removeprefix('../../')
                        resolved = PLUGIN_ROOT / stripped
                        with self.subTest(msg=f'{skill_name}: referenced file exists ({stripped})'):
                            self.assertTrue(resolved.is_file(), f'file not found: {resolved}')

def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-skill-contracts")

if __name__ == "__main__":
    raise SystemExit(main())
