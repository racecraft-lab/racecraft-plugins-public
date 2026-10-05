#!/usr/bin/env python3
"""Consolidated Layer 1 contracts owned by validate-skill-contracts.py."""

from __future__ import annotations

from pathlib import Path
import atexit
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for _import_root in (LIB_DIR, PLUGIN_ROOT):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))

from speckit_pro_runner.helpers.registry import MUTATION_HELPERS
from speckit_pro_runner.agent_inventory import AGENT_INVENTORY
from speckit_pro_runner.codex_agent_generator import generated_codex_files
from speckit_pro_runner.gates.payloads import build_installed_plugin_payloads
from speckit_pro_runner.host_parity import emit_host
import agent_roster
import codex_isolation
from host_skill_views import host_skill_root
from host_progress_contract import forbidden_task_tools
from script_loader import load_script
from structural_helpers import body as _body
from structural_helpers import discover_skill_names
from structural_helpers import frontmatter as _frontmatter
from structural_helpers import frontmatter_field as _field
from test_result import run_counted

# Shared skill sources carry host blocks; each host's checks read its rendered view.
CLAUDE_VIEW = host_skill_root('claude')
CODEX_VIEW = host_skill_root('codex')
validate_skills_SKILLS_DIR = CLAUDE_VIEW
validate_skills_SKILLS = tuple(discover_skill_names(validate_skills_SKILLS_DIR))
SKILLS_REQUIRING_REFERENCES = frozenset({'speckit-autopilot', 'speckit-coach'})
ALLOWED_KEYS = frozenset({'name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility', 'user-invocable', 'disable-model-invocation', 'argument-hint'})
NAME_RE = re.compile('^[a-z][a-z0-9]*(-[a-z0-9]+)*$')
TOP_LEVEL_KEY_RE = re.compile('^([a-zA-Z][a-zA-Z0-9_-]*):', re.MULTILINE)

def _description_value(frontmatter: str) -> str:
    block = re.search('description:\\s*([>|])\\s*\\n((?:\\s+.*\\n?)*)', frontmatter)
    if block:
        return ' '.join((line.strip() for line in block.group(2).split('\n') if line.strip()))
    inline = re.search('description:\\s*"([^"]*)"|description:\\s*(.+)', frontmatter)
    if inline:
        return (inline.group(1) or inline.group(2) or '').strip()
    return ''

class CodexSkillMentionTests(unittest.TestCase):

    def test_codex_skill_mentions_include_the_plugin_namespace(self) -> None:
        names = discover_skill_names(CODEX_VIEW)
        self.assertIn('speckit-scaffold-spec', names)
        short = re.compile(r'\$(?:' + '|'.join(re.escape(name) for name in names)
                           + r')(?![\w:-])')
        surfaces = list(CODEX_VIEW.rglob('*.md'))
        surfaces += list((PLUGIN_ROOT / 'codex-skills').rglob('*.yaml'))
        surfaces += [path for path in (REPO_ROOT / 'docs-site/src').rglob('*')
                     if path.suffix in {'.md', '.mdx', '.ts', '.astro'}]
        surfaces += [REPO_ROOT / 'README.md', PLUGIN_ROOT / 'README.md']
        for source in surfaces:
            with self.subTest(file=source.name):
                self.assertEqual(short.findall(source.read_text(encoding='utf-8')), [])
        for source in (PLUGIN_ROOT / 'agents').glob('*.md'):
            with self.subTest(agent=source.name):
                self.assertEqual(short.findall(emit_host(source.read_text(encoding='utf-8'), 'codex')), [])


def assert_decoded_host_progress_probes(test: unittest.TestCase) -> None:
    for encoded in (
        '["UPDATE_PLAN"]',
        '["tAsKcReAtE"]',
        r'["\u201cupdate_plan\u201d"]',
        r'["\u201cTaskCreate\u201d"]',
        r'["\u0075pdate_plan"]',
        r'["\nupdate_plan"]',
        r'{"\u0075pdate_plan": [{"label": "progress"}]}',
    ):
        with test.subTest(encoded=encoded):
            test.assertTrue(forbidden_task_tools(json.loads(encoded)))


def prepared_codex_contract_result() -> unittest.TestResult:
    # Reuse the hermetic preparation fixture; it never launches a provider host.
    adapter_tests = load_script(
        'structural_native_eval_adapter_tests',
        REPO_ROOT / 'tests/speckit-pro/unit/test-native-eval-adapters.py',
    )
    prepared_test = adapter_tests.AdapterPreparationTests(
        'test_prepares_isolated_codex_project_with_full_repository_catalog',
    )
    result = unittest.TestResult()
    prepared_test.run(result)
    return result


def assert_real_codex_producer_probes(test: unittest.TestCase) -> None:
    original = codex_isolation.skill_isolation_args
    value = 'tools.' + 'update' + '_plan.enabled=true'
    for arguments in (
        ['-c', value], ['-c' + value],
        ['--config', value], ['--config=' + value],
    ):
        with test.subTest(arguments=arguments), mock.patch.object(
            codex_isolation, 'skill_isolation_args',
            side_effect=lambda *args, **kwargs: original(*args, **kwargs) + arguments,
        ) as producer:
            result = prepared_codex_contract_result()
            test.assertEqual(producer.call_count, 1)
            test.assertFalse(result.wasSuccessful())
            test.assertEqual(result.errors, [])
            test.assertTrue(any('update_plan' in trace for _, trace in result.failures))


def assert_host_eval_adapter_progress(test: unittest.TestCase) -> None:
    sources = sorted(LIB_DIR.glob('native_eval*adapter*.py'))
    test.assertIn(LIB_DIR / 'native_eval_codex_adapter.py', sources)
    test.assertIn(LIB_DIR / 'native_eval_claude_adapter.py', sources)
    for source in sources:
        with test.subTest(file=source.name):
            test.assertEqual(forbidden_task_tools(_read(source)), [], 'eval adapter names a task-list tool or opt-in')
    result = prepared_codex_contract_result()
    test.assertEqual(result.testsRun, 1)
    test.assertEqual(result.skipped, [])
    test.assertTrue(result.wasSuccessful(), result.failures + result.errors)
    assert_real_codex_producer_probes(test)


class ValidateHostProgressGuidance(unittest.TestCase):

    # ADR 0001 applies to guidance, grading inputs, and host launch configuration.
    def test_host_guidance_uses_no_task_list_tools(self) -> None:
        for host, root in (('claude', CLAUDE_VIEW), ('codex', CODEX_VIEW)):
            sources = sorted(root.rglob('*.md')) + sorted(root.rglob('*.yaml'))
            self.assertTrue(sources, f'{host}: missing rendered skill guidance')
            agents = sorted((PLUGIN_ROOT / ('agents' if host == 'claude' else 'codex-agents')).glob('*.md' if host == 'claude' else '*.toml'))
            self.assertTrue(agents, f'{host}: missing agent guidance')
            sources += agents
            for source in sources:
                with self.subTest(host=host, file=source.relative_to(source.parent.parent)):
                    self.assertEqual(forbidden_task_tools(_read(source)), [], 'host guidance names a task-list tool or opt-in')

    def test_host_eval_cases_use_no_task_list_tools(self) -> None:
        assert_decoded_host_progress_probes(self)
        functional = REPO_ROOT / 'tests/speckit-pro/layer3-functional'
        for catalog in ('evals', 'codex-evals'):
            sources = sorted((functional / catalog).glob('*-evals.json'))
            self.assertTrue(sources, f'{catalog}: missing functional eval cases')
            self.assertIn(functional / catalog / 'speckit-autopilot-evals.json', sources)
            for source in sources:
                cases = json.loads(_read(source))['evals']
                self.assertIsInstance(cases, list)
                self.assertTrue(cases, f'{source.name}: empty eval cases')
                with self.subTest(catalog=catalog, file=source.name):
                    self.assertEqual(forbidden_task_tools(cases), [], 'eval case names a task-list tool or opt-in')
        for relative in ('evals/catalog.json', 'evals/fixtures/functional/legacy-selection.json', 'evals/audit/functional-inventory.json'):
            source = REPO_ROOT / 'tests/speckit-pro' / relative
            with self.subTest(file=relative):
                self.assertEqual(forbidden_task_tools(json.loads(_read(source))), [], 'native eval contract names a task-list tool or opt-in')

    def test_host_eval_adapters_use_no_task_list_tools(self) -> None:
        assert_host_eval_adapter_progress(self)


class ValidateSkills(unittest.TestCase):

    def test_plan_ambiguity_repair_preserves_requirement_provenance(self) -> None:
        surfaces = (
            (
                'Claude source',
                PLUGIN_ROOT / 'skills/speckit-autopilot/SKILL.md',
                PLUGIN_ROOT / 'skills/speckit-autopilot/references/gate-validation.md',
                PLUGIN_ROOT / 'skills/speckit-autopilot/references/phase-execution.md',
                PLUGIN_ROOT / 'skills/speckit-autopilot/references/workflow-file-protocol.md',
            ),
            (
                'Codex source',
                CODEX_VIEW / 'speckit-autopilot/SKILL.md',
                PLUGIN_ROOT / 'skills/speckit-autopilot/references/gate-validation.md',
                CODEX_VIEW / 'speckit-autopilot/references/phase-execution.md',
                CODEX_VIEW / 'speckit-autopilot/references/workflow-file-protocol.md',
            ),
            (
                'Claude payload',
                REPO_ROOT / 'dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md',
                REPO_ROOT / 'dist/claude/speckit-pro/skills/speckit-autopilot/references/gate-validation.md',
                REPO_ROOT / 'dist/claude/speckit-pro/skills/speckit-autopilot/references/phase-execution.md',
                REPO_ROOT / 'dist/claude/speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md',
            ),
            (
                'Codex payload',
                REPO_ROOT / 'dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md',
                REPO_ROOT / 'dist/codex/speckit-pro/skills/speckit-autopilot/references/gate-validation.md',
                REPO_ROOT / 'dist/codex/speckit-pro/skills/speckit-autopilot/references/phase-execution.md',
                REPO_ROOT / 'dist/codex/speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md',
            ),
        )
        log_header = '| Attempt | Disputed wording | Source evidence | Provenance class | Repair action | G3 result | Remaining escalation reason |'

        for label, skill_path, gate_path, phase_path, workflow_path in surfaces:
            with self.subTest(host=label):
                skill = _read(skill_path)
                gate = _read(gate_path)
                phase = _read(phase_path)
                workflow = _read(workflow_path)

                self.assertIn('Plan ambiguity uses provenance, not consensus', skill)
                for provenance_class in (
                    'explicit-human',
                    'necessary-implication',
                    'assistant-inference',
                    'unresolved-provenance',
                ):
                    self.assertIn(f'`{provenance_class}`', gate)
                self.assertIn('None can upgrade a constraint', gate)
                self.assertIn('shared corrective reservation', phase)
                self.assertIn('Plan Repair Context', phase)
                self.assertIn('run `validate-gate` for G3 again', gate)
                self.assertIn('acknowledgement time is not interchangeable with actual UI-delivery timing', gate)
                self.assertIn('Never delete or disguise an unresolved marker merely to make G3 pass', gate)
                self.assertIn('leaves the failed G3 verdict and unresolved marker', gate)
                self.assertIn('label its source `human answer`', workflow)
                self.assertIn('#### Plan Ambiguity Repair Log', workflow)
                self.assertIn(log_header, workflow)

    def test_coach_workflow_explanation_reads_host_scaffold_authority(self) -> None:
        for label, skills_root, template_root in (
            ('Claude source', CLAUDE_VIEW, CLAUDE_VIEW),
            ('Codex source', CODEX_VIEW, CODEX_VIEW),
            ('Claude payload', REPO_ROOT / 'dist/claude/speckit-pro/skills', REPO_ROOT / 'dist/claude/speckit-pro/skills'),
            ('Codex payload', REPO_ROOT / 'dist/codex/speckit-pro/skills', REPO_ROOT / 'dist/codex/speckit-pro/skills'),
        ):
            with self.subTest(host=label):
                coach = skills_root / 'speckit-coach' / 'SKILL.md'
                template = template_root / 'speckit-coach/templates/workflow-template.md'
                scaffold = skills_root / 'speckit-scaffold-spec' / 'SKILL.md'
                routes = [line for line in coach.read_text(encoding='utf-8').splitlines()
                          if line.startswith('|') and 'workflow-template.md)' in line]
                self.assertEqual(len(routes), 1, 'workflow explanation must have one authority route')
                route = routes[0]
                targets = {(coach.parent / link).resolve()
                           for link in re.findall(r'\]\(([^)]+)\)', route)}
                for authority in (template, scaffold):
                    self.assertIn(authority, targets, 'route must link the template and host scaffold authority')
                    self.assertTrue(authority.is_file(), f'missing workflow authority: {authority}')
                for topic in ('creation', 'population', 'inputs', 'output locations'):
                    self.assertIn(topic, route, f'scaffold explanation route must cover {topic}')
                self.assertRegex(route, r'read .*speckit-scaffold-spec/SKILL\.md\) as a reference only; do not execute or invoke it')

    def test_coach_descriptions_preserve_sdd_scope_and_execution_boundary(self) -> None:
        for host, view in (('claude', CLAUDE_VIEW), ('codex', CODEX_VIEW)):
            with self.subTest(host=host):
                source = (view / 'speckit-coach' / 'SKILL.md').read_text(encoding='utf-8')
                description = _description_value(_frontmatter(source.splitlines()))
                for purpose in ('SDD methodology', 'command and gate guidance',
                                'technical-roadmap and workflow design', 'roadmap-MOC',
                                'checklist selection', 'SpecKit project repair',
                                'SpecKit preset and extension discovery'):
                    self.assertIn(purpose, description)
                self.assertRegex(description, r'Not for running autopilot, conducting grill-me, or unrelated coding.*MCP tool implementation')

    def test_coach_extension_discovery_discloses_non_exhaustive_scope(self) -> None:
        guide = (PLUGIN_ROOT / 'skills' / 'speckit-coach' / 'references' / 'presets-extensions-guide.md').read_text(encoding='utf-8')
        discovery = ' '.join(guide.split('## Explain or discover', 1)[1].split('## Change state', 1)[0].split())
        self.assertRegex(discovery, r'Before answering about user-named or observed extensions.*scope of the list.*explicitly state that it is non-exhaustive')

    def test_coach_extension_advice_distinguishes_installed_and_callable_state(self) -> None:
        guide = (PLUGIN_ROOT / 'skills' / 'speckit-coach' / 'references' / 'presets-extensions-guide.md').read_text(encoding='utf-8')
        inspection = ' '.join(guide.split('## Inspect before advising', 1)[1].split('## The curated set', 1)[0].split())
        discovery = ' '.join(guide.split('## Explain or discover', 1)[1].split('## Change state', 1)[0].split())
        self.assertRegex(inspection, r'Before advising on installed preset or extension behavior, read the active `specify` version/help and host-integration evidence')
        for obligation in (
            'Separate installed presence, host command registration, and enabled hook wiring.',
            'An installed id or description does not prove a callable command or automatic hook.',
            'Report empty command or hook declarations as empty;',
            'if the registration or wiring evidence is unavailable, say it is unverified.',
        ):
            with self.subTest(obligation=obligation):
                self.assertIn(obligation, discovery)

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
                with self.subTest(msg='grill-me: Design Concept contract carries the always-resolved branch sections'):
                    output_formats = (skill_dir / 'references' / 'output-formats.md').read_text(encoding='utf-8')
                    for heading in ('## Module and Interface Deltas', '## Terms', '## Verification Gates'):
                        self.assertIn(heading, output_formats, f'expected grill-me output-formats.md to keep the {heading!r} section')
            if skill == 'speckit-autopilot':
                with self.subTest(msg='speckit-autopilot: hardener delegation reference is shipped and wired on both platforms'):
                    hardener = skill_dir / 'references' / 'hardener-delegation.md'
                    self.assertTrue(hardener.is_file(), f'file not found: {hardener}')
                    hardener_text = hardener.read_text(encoding='utf-8')
                    for needle in ('once per spec', 'delegate_health', 'delegate_task', 'delegate_status', 'delegate_candidate', 'delegate_apply', 'route: "auto"', 'webPolicy: "disabled"', 'Allowed writes: tests only', 'Fallback path (primary model)'):
                        self.assertIn(needle, hardener_text, f'expected hardener-delegation.md to state {needle!r}')
                    phase_exec = (skill_dir / 'references' / 'phase-execution.md').read_text(encoding='utf-8')
                    codex_post = (CODEX_VIEW / 'speckit-autopilot' / 'references' / 'post-implementation.md').read_text(encoding='utf-8')
                    self.assertIn('hardener-delegation.md', phase_exec, 'expected Phase 7 Step 4 to point at the hardener reference')
                    self.assertIn('hardener-delegation.md', codex_post, 'expected the Codex integration-suite row to point at the hardener reference')
                with self.subTest(msg='speckit-autopilot: delegation guidance uses the gateway delegate_* tools and never hard-codes the local route'):
                    retired = re.compile(r'qwen_[a-z]+|local qwen|route=local|route: "local"', re.IGNORECASE)
                    shipped = [p for root in ('skills', 'codex-skills', 'agents', 'codex-agents') for p in sorted((PLUGIN_ROOT / root).rglob('*')) if p.suffix in ('.md', '.toml') and p.is_file()]
                    self.assertTrue(shipped, 'expected shipped skill and agent text to scan')
                    offenders = [f'{p.relative_to(PLUGIN_ROOT)}:{n}: {m.group(0)}' for p in shipped for n, line in enumerate(p.read_text(encoding='utf-8').splitlines(), 1) for m in retired.finditer(line)]
                    self.assertEqual([], offenders, 'retired qwen_* tool names or a hard-coded local delegation route in shipped text')
                with self.subTest(msg='speckit-autopilot: Codex autonomy preflight inventories delegation at the gateway route=auto destination'):
                    codex_phase = (CODEX_VIEW / 'speckit-autopilot' / 'references' / 'phase-execution.md').read_text(encoding='utf-8')
                    start = codex_phase.find('### Autonomy Boundary Preflight')
                    self.assertNotEqual(-1, start, 'expected the Autonomy Boundary Preflight section')
                    end = codex_phase.find('\n### ', start + 1)
                    preflight = codex_phase[start:end if end != -1 else len(codex_phase)]
                    delegation = [para for para in preflight.split('\n\n') if 'delegation gateway' in para]
                    self.assertTrue(delegation, 'expected a preflight paragraph about the delegation gateway')
                    self.assertTrue(any('route=auto' in para and 'data egress' in para for para in delegation), 'expected planned delegation to be inventoried as one data-egress action naming route=auto')
            if skill in ('grill-me', 'speckit-prd'):
                with self.subTest(msg=f'{skill}: reads the ubiquitous-language terms document when present'):
                    codex_content = (CODEX_VIEW / skill / 'SKILL.md').read_text(encoding='utf-8')
                    for label, text in (('Claude', content), ('Codex', codex_content)):
                        self.assertIn('docs/ai/specs/ubiquitous-language.md', text, f'expected the {label} {skill} skill to read the terms document when present')
            if skill == 'speckit-prd':
                with self.subTest(msg='speckit-prd: PRD and roadmap templates require Module and Interface Deltas'):
                    prd_template = (PLUGIN_ROOT / 'skills' / 'speckit-coach' / 'templates' / 'prd-template.md').read_text(encoding='utf-8')
                    roadmap_template = (PLUGIN_ROOT / 'skills' / 'speckit-coach' / 'templates' / 'technical-roadmap-template.md').read_text(encoding='utf-8')
                    protocol = (skill_dir / 'references' / 'prd-authoring-protocol.md').read_text(encoding='utf-8')
                    self.assertIn('## 5. Module and Interface Deltas', prd_template, 'expected the PRD template to carry the required Module and Interface Deltas section')
                    self.assertIn('No module or interface changes.', prd_template, 'expected the PRD template to allow the canonical explicit no-change row')
                    self.assertEqual(4, roadmap_template.count('**Module and Interface Deltas:**'), 'expected every roadmap SPEC entry to carry a Module and Interface Deltas field')
                    self.assertIn('No module or interface changes.', roadmap_template, 'expected the roadmap template to allow an explicit no-change line')
                    self.assertIn('Module and Interface Deltas', protocol, 'expected the PRD authoring protocol to require the section')
                with self.subTest(msg='speckit-prd: reviewability preset plan template carries Module and Interface Deltas'):
                    plan_template = (REPO_ROOT / '.specify' / 'presets' / 'speckit-pro-reviewability' / 'templates' / 'plan-template.md').read_text(encoding='utf-8')
                    self.assertIn('## Module and Interface Deltas', plan_template, 'expected the preset plan template to carry the required Module and Interface Deltas section')
                    self.assertIsNotNone(re.search(r'No module or interface\s+changes\.', plan_template), 'expected the preset plan template to allow the explicit no-change line')
                    self.assertLess(plan_template.index('## Module and Interface Deltas'), plan_template.index('## Declared File Operations'), 'expected the deltas section before Declared File Operations')
            if skill == 'speckit-scaffold-spec':
                with self.subTest(msg='speckit-scaffold-spec: skill heading uses scaffold naming'):
                    self.assertTrue(re.search('^# SpecKit Scaffold Spec$', content, re.MULTILINE) is not None and re.search('^# SpecKit Setup$', content, re.MULTILINE) is None, "expected '# SpecKit Scaffold Spec' heading in skills/speckit-scaffold-spec/SKILL.md")
                with self.subTest(msg='speckit-scaffold-spec: completion report uses scaffold naming'):
                    self.assertTrue(re.search('^## Scaffold Complete$', content, re.MULTILINE) is not None and re.search('^## Setup Complete$', content, re.MULTILINE) is None, "expected '## Scaffold Complete' report heading in skills/speckit-scaffold-spec/SKILL.md")
                normalized = ' '.join(content.split())
                with self.subTest(msg='speckit-scaffold-spec: branch reuse never writes main'):
                    self.assertIn('all commits and pushes still originate from the resolved worktree branch, never `main`', normalized)
                    self.assertIn('Never commit or push `main` while recovering or reusing a remote branch', normalized)
                with self.subTest(msg='speckit-scaffold-spec: rejected push preserves and reports local work'):
                    self.assertIn('The failure report identifies the existing local branch, canonical worktree, workflow file, and local commit', normalized)
                    self.assertIn('retry the push from that same existing worktree', normalized)
                    self.assertIn('Do not recreate the branch or worktree, regenerate the workflow, or replace the existing commit', normalized)
                with self.subTest(msg='speckit-scaffold-spec: reviewability setup gate is scoped to the SPEC-ID'):
                    self.assertIn('Run runner helper reviewability-gate with the request fields above. Set `target` to the repository-relative technical roadmap path and `spec_id` to the requested SPEC-ID.', normalized)
                with self.subTest(msg='speckit-scaffold-spec: resolver ordering gates mutation and interview'):
                    self.assertIn('the first resolver result comes before `git worktree add`, artifact writes, or roadmap mutation', normalized)
                    self.assertIn('A second resolver check then runs after creation or reuse and immediately before bootstrap or Grill Me', normalized)
                    self.assertIn('Neither bootstrap nor Grill Me may begin unless that second check confirms the registered worktree', normalized)
            if skill in SKILLS_REQUIRING_REFERENCES:
                with self.subTest(msg=f'{skill}: references directory exists if required'):
                    self.assertTrue((skill_dir / 'references').is_dir(), f"references directory not found at {skill_dir / 'references'}")
validate_codex_skills_CODEX_SKILLS_DIR = CODEX_VIEW
validate_codex_skills_SKILLS = tuple(discover_skill_names(validate_codex_skills_CODEX_SKILLS_DIR))
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

    def test_no_shared_skill_redirects_codex_to_an_overlay(self) -> None:
        # Every shared skill renders its Codex text from host blocks, so none
        # may point Codex at a separate overlay copy.
        shared = sorted((PLUGIN_ROOT / 'skills').glob('*/SKILL.md'))
        self.assertGreaterEqual(len(shared), 10, 'no shared skills found; the check would pass on nothing')
        for skill_file in shared:
            with self.subTest(msg=f'{skill_file.parent.name}: no Codex Skill-Selection Guard'):
                self.assertNotIn('Codex Skill-Selection Guard', skill_file.read_text(encoding='utf-8'))

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
                with self.subTest(msg='speckit-scaffold-spec: Codex reviewability setup gate is scoped to the SPEC-ID'):
                    self.assertIn('Run runner helper reviewability-gate with the request fields above. Set `target` to the repository-relative technical roadmap path and `spec_id` to the requested SPEC-ID.', ' '.join(content.split()))
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
        phase_execution = _read(skill_dir / 'references' / 'phase-execution.md')
        post_implementation = _read(skill_dir / 'references' / 'post-implementation.md')
        error_recovery = _read(skill_dir / 'references' / 'error-recovery.md')
        runtime_doc = f"{body}\n{phase_execution}\n{post_implementation}\n{error_recovery}"
        with self.subTest(msg='speckit-autopilot: requires durable autopilot-state.json persistence'):
            self.assertIn('autopilot-state.json', runtime_doc)
        with self.subTest(msg='speckit-autopilot: names Codex-native delegation tools'):
            self.assertTrue('spawn_agent' in runtime_doc and 'wait_agent' in runtime_doc, 'expected both spawn_agent and wait_agent in the Codex autopilot skill')
        with self.subTest(msg='speckit-autopilot: routes consensus through the parse-consensus-categories helper'):
            self.assertIn('parse-consensus-categories', body)
            self.assertNotIn('per the routing table', body)
            self.assertNotIn('codebase-analyst only', body)
        with self.subTest(msg='speckit-autopilot: dispatches the installed Codex consensus synthesizer'):
            self.assertTrue(
                re.search(r'Shared consensus rounds, analyst routing, decision rules, output formats,\s+artifact edits, and logging remain authoritative\.', phase_execution)
                and re.search(r'every shared\s+consensus-synthesizer step dispatches the installed\s+`consensus-synthesizer`', phase_execution)
                and re.search(r'awaits its actual result', phase_execution)
                and re.search(r'parent never performs synthesis as a\s+fallback', phase_execution)
                and re.search(r'calling `spawn_agent` with the installed\s+`consensus-synthesizer` role, then `wait_agent`', phase_execution)
                and re.search(r'parent session dispatches the installed\s+`consensus-synthesizer` with the fresh analyst result', phase_execution)
                and re.search(r'persists the returned canonical `Pre-Implement Confidence`\s+block exactly once', phase_execution),
                'expected shared consensus behavior to dispatch and consume the installed Codex synthesizer',
            )
        with self.subTest(msg='speckit-autopilot: names built-in default for both general Post tracks'):
            self.assertTrue(
                re.search(r'\*\*Track B:\*\* Code Review \(item 13\) — spawn the built-in `default` subagent', post_implementation)
                and re.search(r'\*\*Track C:\*\* Verify-chain \(items 11 → 12 → 14\) — spawn one built-in `default`\s+subagent without a model or reasoning-effort override', post_implementation),
                'expected Code Review and Verify-chain to use the documented Codex built-in default role',
            )
        with self.subTest(msg='speckit-autopilot: excludes undocumented general-purpose Codex roles'):
            self.assertNotIn('general-purpose', post_implementation, 'Codex role guidance must use the built-in default role')
        with self.subTest(msg='speckit-autopilot: maps hosted and local Codex follow-up tools'):
            self.assertTrue('followup_task' in runtime_doc and 'send_message' in runtime_doc and ('resume_agent' in runtime_doc) and ('send_input' in runtime_doc), 'expected hosted followup_task/send_message plus local send_input and resume-then-send_input handling')
        with self.subTest(msg='speckit-autopilot: adapts agent cleanup to the exposed Codex surface'):
            self.assertTrue('absence of `close_agent` is NOT' in runtime_doc and 'prerequisite failure' in runtime_doc and ('only when `close_agent` is exposed' in runtime_doc) and ('interrupt_agent' in runtime_doc) and ('list_agents' in runtime_doc) and ('terminal status is corroboration or recovery evidence only' in runtime_doc) and ('A `wait_agent` timeout is one bounded mailbox poll' in runtime_doc) and ('`close_agent` is REQUIRED' not in runtime_doc), 'expected capability-aware hosted/local lifecycle handling without a close_agent hard requirement')
        with self.subTest(msg='speckit-autopilot: validates a single in_progress item before phase execution'):
            self.assertIn('Exactly one plan item is `in_progress`', body)
        with self.subTest(msg='speckit-autopilot: requires all canonical phase families before execution'):
            self.assertTrue('Phase family coverage is mandatory' in runtime_doc and 'Phase 7: Implement - Pending task decomposition' in runtime_doc and ('Post: Doctor Extension Check' in runtime_doc) and ('Post: Retrospective' in runtime_doc), 'expected all-phase coverage, Phase 7 placeholder, and the canonical Post item list (Doctor Extension Check -> Retrospective) in the Codex autopilot skill')
        with self.subTest(msg='speckit-autopilot: documents canonical PHASES order'):
            self.assertIn('PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]', runtime_doc)
        with self.subTest(msg='speckit-autopilot: prevents from-phase from dropping later phases'):
            self.assertTrue(
                'Read the workflow file and apply\n[`references/phase-execution.md`](./references/phase-execution.md)\n§Stage-Bounded Phase Selection.' in body
                and '`--from-phase` changes the first phase to execute, not the required plan\ncoverage.' in phase_execution
                and 'all seven SDD phases, and Post before any subagent is spawned.' in phase_execution
                and 'a value outside an explicitly named stage\'s range is rejected at Step\n0.6c before any phase work begins.' in phase_execution,
                'expected the entrypoint to require the stage-bounded reference, which keeps whole-plan coverage visible and rejects out-of-stage --from-phase values',
            )
        with self.subTest(msg='speckit-autopilot: requires concrete Phase 7 tasks after G5'):
            self.assertTrue(
                'Before performing the post-G5 steps (8 through 8e), read\n[`references/phase-execution.md`](./references/phase-execution.md)\n§Phase 5: Tasks' in body
                and 'After G5 passes, the placeholder is invalid.' in phase_execution
                and '- no `Phase 7: Implement - Pending task decomposition` item remains' in phase_execution
                and '- each concrete item names one or more task IDs parsed from `tasks.md`' in phase_execution
                and 'Correctness stops remain blocking:' in phase_execution,
                'expected the entrypoint to require Phase 7 guidance that removes the G5 placeholder, names concrete task IDs, and retains correctness stops',
            )
        with self.subTest(msg='speckit-autopilot: resumes into Post before reporting complete'):
            self.assertTrue(
                'After Phase 7 passes G7, read and execute\n[`references/post-implementation.md`](./references/post-implementation.md)\nin canonical order.' in body
                and 'all seven SDD phases being complete is not sufficient to stop.' in post_implementation
                and 'continue with the first incomplete Post item.' in post_implementation
                and 'resume at the first incomplete Post\n   item. Do not summarize completion from a `Phase 7: Implement Complete`\n   state.' in error_recovery,
                'expected the Post entrypoint and recovery reference to continue from the first incomplete Post item without a premature completion summary',
            )
        with self.subTest(msg='speckit-autopilot: blocks completion but allows honest budget checkpoints'):
            self.assertTrue(
                '### 3.4 Pre-final completion audit' in body
                and 'A completion response is\nforbidden if any `Post:` item is `pending`, `in_progress`, or missing.' in body
                and 'execution_control.disposition=checkpoint_required' in body
                and 'run is **not complete**' in body
                and 'never mark them completed to stop' in body
                and 'set the first\nincomplete item to `in_progress` in `autopilot-state.json` and continue the\nautopilot loop instead of summarizing.' in body
                and '`Post: Retrospective` is the final\nPost item; it must be completed or explicitly skipped before the\nautopilot can report completion.' in body,
                'expected the direct final audit to forbid completion, continue the first incomplete Post item, and require Retrospective',
            )
        with self.subTest(msg='speckit-autopilot: documents skill-local agents/openai.yaml metadata'):
            self.assertIn('agents/openai.yaml', body)
        with self.subTest(msg='speckit-autopilot: validates installed Codex subagent paths'):
            self.assertTrue('.codex/agents/' in body and '~/.codex/agents/' in body, 'expected both project and user Codex subagent paths in the autopilot skill')
        with self.subTest(msg='speckit-autopilot: fails closed to the install skill when subagents are missing'):
            prerequisites = _read(skill_dir / 'references' / 'prerequisites.md')
            self.assertTrue('$speckit-pro:install' in body and '$speckit-pro:install' in prerequisites and ('install-codex-agents' in prerequisites) and ('dry_run' in prerequisites) and ('validate-agent-install' not in prerequisites) and ('--autoheal' not in prerequisites), 'expected read-only installer dry-run preflight and install/restart fail-closed guidance')
        with self.subTest(msg='speckit-autopilot: explicit external workflow binds to its registered worktree'):
            prerequisites = _read(skill_dir / 'references' / 'prerequisites.md')
            self.assertTrue('explicitly supplied the absolute workflow path' in prerequisites and 'relation=external' in prerequisites and 'registered worktree' in prerequisites and 'real sandbox denial' in prerequisites and ('Open a new Codex task rooted at <workflow_root>' not in prerequisites), 'expected explicit registered-worktree binding with permission failures reported at the actual operation')
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
            self.assertTrue((skill_dir / 'references' / 'phase-execution.md').is_file())
        with self.subTest(msg='speckit-autopilot: Codex post-implementation reference exists'):
            self.assertTrue((skill_dir / 'references' / 'post-implementation.md').is_file())
        with self.subTest(msg='speckit-autopilot: Codex SKILL.md names the plan-phase estimator helper'):
            self.assertIn('estimate-reviewable-loc', body)
        with self.subTest(msg='speckit-autopilot: Codex SKILL.md carries the three-value status vocab'):
            self.assertIn('`pass` / `over_budget` / `not_estimated`', body)
        phase_exec = _read(skill_dir / 'references' / 'phase-execution.md')
        with self.subTest(msg='speckit-autopilot: Codex phase-execution.md names the plan-phase estimator helper'):
            self.assertIn('estimate-reviewable-loc', phase_exec)
        with self.subTest(msg='speckit-autopilot: Codex phase-execution.md documents the over_budget status'):
            self.assertIn('over_budget', phase_exec)
        with self.subTest(msg='speckit-autopilot: Codex phase-execution.md documents the not_estimated status'):
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
            elif skill in ('speckit-archive-cleanup', 'speckit-autopilot', 'speckit-resolve-pr', 'install', 'speckit-install', 'speckit-upgrade', 'grill-me', 'speckit-prd', 'ubiquitous-language'):
                self.assertEqual('false', policy_value, 'mutation-heavy skill must have allow_implicit_invocation: false')
            elif skill in ('speckit-coach', 'speckit-status'):
                self.assertEqual('true', policy_value, 'read-only skill must have allow_implicit_invocation: true')
            else:
                self.fail(f"no implicit-invocation policy expectation defined for '{skill}'; update this contract")
            if skill == 'speckit-autopilot':
                self.assertNotIn('dependencies:', sidecar.read_text(encoding='utf-8'), 'autopilot optional research capabilities must not be declared as required tool dependencies')
validate_capability_pointer_AGENTS_DIR = PLUGIN_ROOT / 'agents'
validate_capability_pointer_CODEX_AGENTS_DIR = PLUGIN_ROOT / 'codex-agents'
validate_capability_pointer_DIRECTIVE_MARKER = 'capability-discovery.md'
validate_capability_pointer_GROUNDING_MARKER = 'grounding.md'
CAPABILITY_NOTE = 'Capability path:'

def validate_capability_pointer__rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()

def validate_capability_pointer__excluded(runtime: str, name: str) -> bool:
    return name in agent_roster.capability_exempt_roles(runtime)

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
            with self.subTest(msg=f"{runtime}: in-scope agent '{agent_name}' references {validate_capability_pointer_DIRECTIVE_MARKER}"):
                self.assertIn(validate_capability_pointer_DIRECTIVE_MARKER, text, f"uncovered in-scope agent: {runtime} '{agent_name}' does not reference {validate_capability_pointer_DIRECTIVE_MARKER}")
            with self.subTest(msg=f"{runtime}: in-scope agent '{agent_name}' references {validate_capability_pointer_GROUNDING_MARKER}"):
                self.assertIn(validate_capability_pointer_GROUNDING_MARKER, text, f"{runtime} '{agent_name}' does not reference {validate_capability_pointer_GROUNDING_MARKER}")
            with self.subTest(msg=f"{runtime}: in-scope agent '{agent_name}' output requires the grounding evidence note"):
                self.assertIn(CAPABILITY_NOTE, text, f"in-scope agent '{agent_name}' ({runtime}) output format does not require the grounding evidence note")

    def test_pointer_coverage(self) -> None:
        self._check_runtime('claude', validate_capability_pointer_AGENTS_DIR, 'md')
        self._check_runtime('codex', validate_capability_pointer_CODEX_AGENTS_DIR, 'toml')
validate_capability_resolution_AGENTS_DIR = PLUGIN_ROOT / 'agents'
validate_capability_resolution_CODEX_AGENTS_DIR = PLUGIN_ROOT / 'codex-agents'
validate_capability_resolution_DIST_CLAUDE = REPO_ROOT / 'dist' / 'claude'
validate_capability_resolution_DIST_CODEX = REPO_ROOT / 'dist' / 'codex'
validate_capability_resolution_DIRECTIVE_MARKER = 'capability-discovery.md'
validate_capability_resolution_GROUNDING_MARKER = 'grounding.md'
validate_capability_resolution_PATH_TOKEN_RE = re.compile('speckit-pro/[A-Za-z0-9._/-]*capability-discovery\\.md')
validate_capability_resolution_GROUNDING_TOKEN_RE = re.compile('speckit-pro/[A-Za-z0-9._/-]*grounding\\.md')
CONTRACT_REFERENCES = 'skills/speckit-autopilot/references'
# One sentence per agent-facing grounding rule, quoted verbatim from grounding.md.
GROUNDING_RULE_SENTENCES = (
    ('G1', 'A claim with no invoked-capability result behind it must not be asserted as fact.'),
    ('G2', 'When no available capability can ground a needed claim, say so instead of asserting it.'),
    ('G3', 'never assign `high` confidence to a claim that is not grounded in an invoked result.'),
    ('G4', 'each external claim names the capability result and a locator (URL, `file:line`, command, or returned record)'),
)

def validate_capability_resolution__rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()

def validate_capability_resolution__excluded(runtime: str, name: str) -> bool:
    return name in agent_roster.capability_exempt_roles(runtime)

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
            if runtime == 'claude':
                # A repo-relative path does not exist in the consumer repository; Claude
                # agents read both files from the directory the orchestrator passes.
                with self.subTest(msg=f"claude: in-scope agent '{agent_name}' names no repo-relative contract path"):
                    self.assertFalse(validate_capability_resolution_PATH_TOKEN_RE.findall(text) or validate_capability_resolution_GROUNDING_TOKEN_RE.findall(text), f'repo-relative contract path in {validate_capability_resolution__rel(agent_file)}')
                with self.subTest(msg=f"claude: in-scope agent '{agent_name}' reads the contracts from its `Reference dir:` line"):
                    self.assertIn("prompt's `Reference dir:` line", ' '.join(text.split()), f'no Reference dir directive in {validate_capability_resolution__rel(agent_file)}')
                continue
            # An installed Codex agent cannot read the plugin's references, so it
            # carries the grounding rules inline, word for word from grounding.md.
            flat = ' '.join(text.split())
            found_tokens.append(f'codex:{agent_name}')
            with self.subTest(msg=f"codex: in-scope agent '{agent_name}' names no repo-relative contract path"):
                self.assertFalse(validate_capability_resolution_PATH_TOKEN_RE.findall(text) or validate_capability_resolution_GROUNDING_TOKEN_RE.findall(text), f'repo-relative contract path in {validate_capability_resolution__rel(agent_file)}')
            for rule, sentence in GROUNDING_RULE_SENTENCES:
                with self.subTest(msg=f"codex: in-scope agent '{agent_name}' carries grounding rule {rule}"):
                    self.assertIn(sentence, flat, f'{rule} missing from {validate_capability_resolution__rel(agent_file)}')

    def test_target_resolution(self) -> None:
        checked: list[str] = []
        self._collect_runtime('claude', validate_capability_resolution_AGENTS_DIR, 'md', checked)
        self._collect_runtime('codex', validate_capability_resolution_CODEX_AGENTS_DIR, 'toml', checked)
        with self.subTest(msg='at least one Codex agent carries the inline grounding rules'):
            self.assertTrue(checked, 'no in-scope Codex agent checked — refusing to report success on zero work')
        grounding = ' '.join((PLUGIN_ROOT / CONTRACT_REFERENCES / 'grounding.md').read_text(encoding='utf-8').split())
        for rule, sentence in GROUNDING_RULE_SENTENCES:
            with self.subTest(msg=f'grounding.md states rule {rule} as the agents quote it'):
                self.assertIn(sentence, grounding)
        for tree in (validate_capability_resolution_DIST_CLAUDE, validate_capability_resolution_DIST_CODEX):
            for name in ('capability-discovery.md', 'grounding.md'):
                target = tree / 'speckit-pro' / CONTRACT_REFERENCES / name
                with self.subTest(msg=f'resolves under {validate_capability_resolution__rel(tree)}: {name}'):
                    self.assertTrue(target.is_file(), f'absent in built tree: {validate_capability_resolution__rel(target)}')
CLAUDE_SKILLS_DIR = CLAUDE_VIEW
validate_skill_capability_pointers_CODEX_SKILLS_DIR = CODEX_VIEW
validate_skill_capability_pointers_DIST_CLAUDE = REPO_ROOT / 'dist' / 'claude'
validate_skill_capability_pointers_DIST_CODEX = REPO_ROOT / 'dist' / 'codex'
validate_skill_capability_pointers_DIRECTIVE_MARKER = 'capability-discovery.md'
validate_skill_capability_pointers_GROUNDING_MARKER = 'grounding.md'
PLUGIN_ROOT_VAR = '${CLAUDE_PLUGIN_ROOT}/'
PLUGIN_ROOT_PREFIX = 'speckit-pro/'
validate_skill_capability_pointers_PATH_TOKEN_RE = re.compile('(?:\\$\\{CLAUDE_PLUGIN_ROOT\\}/|(?:\\.\\./)+)[A-Za-z0-9._/-]*capability-discovery\\.md')
validate_skill_capability_pointers_GROUNDING_TOKEN_RE = re.compile('(?:\\$\\{CLAUDE_PLUGIN_ROOT\\}/|(?:\\.\\./)+)[A-Za-z0-9._/-]*grounding\\.md')
validate_skill_capability_pointers_PAYLOAD_LINK_RES = (re.compile('(?:\\.\\./)*(?:[A-Za-z0-9._-]+/)+capability-discovery\\.md'), re.compile('(?:\\.\\./)*(?:[A-Za-z0-9._-]+/)+grounding\\.md'))

def _payload_relative(token: str, skill_file: Path) -> str:
    """Normalize either pointer form to a path under a built payload tree.

    A relative token resolves from the skill file inside its rendered view,
    which is named skills/ as in each payload.
    """
    if token.startswith(PLUGIN_ROOT_VAR):
        return PLUGIN_ROOT_PREFIX + token[len(PLUGIN_ROOT_VAR):]
    view = skill_file.parent.parent
    return PLUGIN_ROOT_PREFIX + (skill_file.parent / token).resolve().relative_to(view.parent).as_posix()
EXCLUSIONS = frozenset({'speckit-install', 'install', 'speckit-upgrade', 'speckit-status', 'speckit-archive-cleanup'})
HOST_SKILL = 'speckit-autopilot'

def validate_skill_capability_pointers__rel(path: Path) -> str:
    for base, label in ((REPO_ROOT, ''), (CLAUDE_VIEW.parent, 'claude view:'), (CODEX_VIEW.parent, 'codex view:')):
        if path.is_relative_to(base):
            return label + path.relative_to(base).as_posix()
    return path.as_posix()

def _display_path(path: Path) -> str:
    try:
        return validate_skill_capability_pointers__rel(path)
    except ValueError:
        return path.as_posix()

def _skill_dirs(directory: Path) -> list[Path]:
    return sorted((p for p in directory.iterdir() if (p / 'SKILL.md').is_file()), key=lambda p: p.name)

def _unique_matches(pattern: re.Pattern[str], text: str) -> list[str]:
    return sorted(set(pattern.findall(text)))

PRD_WORKFLOW_TARGETS = (
    ('shared PRD authoring protocol', Path('skills/speckit-prd/references/prd-authoring-protocol.md')),
    ('PRD template', Path('skills/speckit-coach/templates/prd-template.md')),
    ('technical-roadmap template', Path('skills/speckit-coach/templates/technical-roadmap-template.md')),
    ('slicing heuristics', Path('skills/speckit-coach/references/slicing-heuristics.md')),
    ('roadmap-MOC template', Path('skills/speckit-coach/templates/roadmap-moc-template.md')),
)
PRD_WORKFLOW_CASES = (
    ('Claude source', CLAUDE_VIEW / 'speckit-prd/SKILL.md', CLAUDE_VIEW.parent),
    ('Codex source', CODEX_VIEW / 'speckit-prd/SKILL.md', CODEX_VIEW.parent),
    ('Claude payload', REPO_ROOT / 'dist/claude/speckit-pro/skills/speckit-prd/SKILL.md', REPO_ROOT / 'dist/claude/speckit-pro'),
    ('Codex payload', REPO_ROOT / 'dist/codex/speckit-pro/skills/speckit-prd/SKILL.md', REPO_ROOT / 'dist/codex/speckit-pro'),
)

class ValidatePrdWorkflowContract(unittest.TestCase):

    def test_prd_workflow_routes_and_overwrite_guard(self) -> None:
        for label, path, root in PRD_WORKFLOW_CASES:
            content = _read(path)
            workflow_marker = '## Workflow\n'
            output_marker = '\n## Output contract'
            workflow_start = content.find(workflow_marker)
            workflow_end = content.find(output_marker, workflow_start + len(workflow_marker))
            bounded_workflow = workflow_start >= 0 and workflow_end > workflow_start
            section_contract = f'{label}: Workflow section is bounded by Output contract'
            with self.subTest(msg=section_contract):
                self.assertTrue(bounded_workflow, section_contract)
            if not bounded_workflow:
                continue
            workflow = content[workflow_start + len(workflow_marker):workflow_end]
            normalized_workflow = ' '.join(workflow.split())
            links = tuple(Path(os.path.relpath(root / target, path.parent)).as_posix() for _, target in PRD_WORKFLOW_TARGETS)
            protocol_link = links[0]
            protocol_contract = f'{label}: Workflow requires protocol read/follow before authoring'
            with self.subTest(msg=protocol_contract):
                self.assertIn(f'Read and follow the [shared PRD authoring protocol]({protocol_link}) before authoring.', normalized_workflow, protocol_contract)
            for (resource, expected_target), link in zip(PRD_WORKFLOW_TARGETS, links, strict=True):
                route_contract = f'{label}: Workflow links {resource} at its host root'
                with self.subTest(msg=route_contract):
                    self.assertIn(f'[{resource}]({link})', normalized_workflow, route_contract)
                    self.assertEqual(root / expected_target, (path.parent / link).resolve(), route_contract)
                    self.assertTrue((path.parent / link).is_file(), route_contract)
            overwrite = 'before overwriting, confirm the exact output path'
            apply = 'Apply the protocol'
            resource_indices = [normalized_workflow.find(f']({link})') for link in links[1:]]
            order_contract = f'{label}: Workflow confirms output path before resources or apply'
            with self.subTest(msg=order_contract):
                self.assertGreaterEqual(normalized_workflow.find(overwrite), 0, order_contract)
                self.assertGreaterEqual(normalized_workflow.find(apply), 0, order_contract)
                if all(index >= 0 for index in resource_indices) and normalized_workflow.find(apply) >= 0:
                    self.assertLess(normalized_workflow.find(overwrite), min(*resource_indices, normalized_workflow.find(apply)), order_contract)

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
            payload_token = _payload_relative(token, skill_file)
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


def _codex_skill_files() -> list[Path]:
    return [p / 'SKILL.md' for p in _skill_dirs(validate_skill_capability_pointers_CODEX_SKILLS_DIR)]


class ValidateCodexPayloadPointers(unittest.TestCase):
    """The built Codex payload must link the shared contracts from each SKILL.md."""

    def test_codex_skills_use_no_repo_root_paths(self) -> None:
        skill_files = _codex_skill_files()
        self.assertTrue(skill_files, 'no Codex skills found - refusing to pass vacuously')
        for skill_file in skill_files:
            with self.subTest(msg=f'{skill_file.parent.name} has no repo-root skills path'):
                text = skill_file.read_text(encoding='utf-8', errors='replace')
                self.assertNotIn(PLUGIN_ROOT_PREFIX + 'skills/', text, f'{_display_path(skill_file)} names a repo-root path the payload build never rewrites; use ../../skills/...')

    def test_built_links_resolve_from_the_payload_skill_file(self) -> None:
        checked = 0
        for source_file in _codex_skill_files():
            source = source_file.read_text(encoding='utf-8', errors='replace')
            payload_file = validate_skill_capability_pointers_DIST_CODEX / PLUGIN_ROOT_PREFIX / 'skills' / source_file.parent.name / 'SKILL.md'
            payload = payload_file.read_text(encoding='utf-8', errors='replace') if payload_file.is_file() else ''
            for marker, pattern in zip((validate_skill_capability_pointers_DIRECTIVE_MARKER, validate_skill_capability_pointers_GROUNDING_MARKER), validate_skill_capability_pointers_PAYLOAD_LINK_RES, strict=True):
                if marker not in source:
                    continue
                tokens = _unique_matches(pattern, payload)
                with self.subTest(msg=f'{source_file.parent.name}: built SKILL.md links {marker}'):
                    self.assertTrue(tokens, f'no {marker} link in built {_display_path(payload_file)}')
                for token in tokens:
                    checked += 1
                    with self.subTest(msg=f'{source_file.parent.name}: {token} resolves from the built SKILL.md'):
                        self.assertTrue((payload_file.parent / token).is_file(), f'{token} does not resolve from {_display_path(payload_file)}')
        self.assertTrue(checked, 'no built Codex links checked - refusing to pass vacuously')
CC_PLUGIN = PLUGIN_ROOT / '.claude-plugin' / 'plugin.json'
CODEX_PLUGIN = PLUGIN_ROOT / '.codex-plugin' / 'plugin.json'
CC_MARKETPLACE = REPO_ROOT / '.claude-plugin' / 'marketplace.json'
CODEX_MARKETPLACE = REPO_ROOT / '.agents' / 'plugins' / 'marketplace.json'
validate_codex_parity_AGENTS_DIR = PLUGIN_ROOT / 'agents'
validate_codex_parity_CODEX_AGENTS_DIR = PLUGIN_ROOT / 'codex-agents'
validate_codex_parity_SKILLS_DIR = CLAUDE_VIEW
validate_codex_parity_CODEX_SKILLS_DIR = CODEX_VIEW
CC_ONLY_AGENTS = agent_roster.claude_only_roles()
CODEX_ONLY_AGENTS = agent_roster.codex_only_roles()
REF_RE = re.compile('\\.\\./\\.\\./skills/[^)\\s`]+\\.md')

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

def _tree(root: Path) -> dict[str, bytes]:
    """Every file under ``root`` by relative path; empty when ``root`` is missing."""
    if not root.is_dir():
        return {}
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}

_FRESH_PAYLOADS: list[Path] = []

def _fresh_payloads() -> Path:
    """Both payloads built from the current source into a temp root, once per process."""
    if not _FRESH_PAYLOADS:
        root = Path(tempfile.mkdtemp(prefix='speckit-payload-parity-')).resolve()
        atexit.register(shutil.rmtree, root, ignore_errors=True)
        build_installed_plugin_payloads(REPO_ROOT, root)
        _FRESH_PAYLOADS.append(root)
    return _FRESH_PAYLOADS[0]

def _sorted_subdirs(directory: Path) -> list[Path]:
    return sorted((p for p in directory.iterdir() if p.is_dir()), key=lambda p: p.name)

class ValidateCodexParity(unittest.TestCase):

    def _assert_agent_generated(self, agent_name: str, generated: dict[str, str]) -> None:
        """The committed Codex agent equals the text generated from its Claude source."""
        relative = f'codex-agents/{agent_name}.toml'
        committed = validate_codex_parity_CODEX_AGENTS_DIR / f'{agent_name}.toml'
        with self.subTest(msg=f'{relative} equals the text generated from agents/{agent_name}.md'):
            self.assertIn(relative, generated, f'agents/{agent_name}.md is paired but generates no Codex agent')
            self.assertTrue(committed.is_file(), f'file not found: {committed}')
            self.assertEqual(committed.read_text(encoding='utf-8'), generated.get(relative), f'{relative} drifted from agents/{agent_name}.md; run python3 scripts/refresh-release-artifacts.py')

    def _assert_payload_skill_built(self, skill_name: str) -> None:
        """Each host's committed payload skill equals a fresh build from source."""
        for host in ('claude', 'codex'):
            shipped = REPO_ROOT / 'dist' / host / 'speckit-pro' / 'skills' / skill_name
            built = _fresh_payloads() / host / 'speckit-pro' / 'skills' / skill_name
            with self.subTest(msg=f'{host} payload skills/{skill_name}/ equals a fresh build from source'):
                self.assertTrue((built / 'SKILL.md').is_file(), f'{host} builds no SKILL.md for {skill_name}')
                self.assertEqual(_tree(shipped), _tree(built), f'{host} payload skills/{skill_name}/ drifted from its source; run python3 scripts/refresh-release-artifacts.py')

    def test_codex_parity(self) -> None:
        with self.subTest(msg='both plugin.json files exist'):
            self.assertTrue(CC_PLUGIN.is_file() and CODEX_PLUGIN.is_file(), f'missing one or both plugin.json files (CC: {CC_PLUGIN}, Codex: {CODEX_PLUGIN})')
        if CC_PLUGIN.is_file() and CODEX_PLUGIN.is_file():
            cc_version = _json_field(CC_PLUGIN, 'version')
            codex_version = _json_field(CODEX_PLUGIN, 'version')
            with self.subTest(msg='Claude plugin.json omits a cache-pinning version'):
                self.assertEqual(cc_version, 'null', f'Claude version must be omitted, got {cc_version}')
            with self.subTest(msg=f'Codex plugin.json remains release-versioned ({codex_version})'):
                self.assertRegex(codex_version, r'^\d+\.\d+\.\d+$', f'Codex version must be X.Y.Z, got {codex_version}')
        with self.subTest(msg='both marketplace.json files exist'):
            self.assertTrue(CC_MARKETPLACE.is_file() and CODEX_MARKETPLACE.is_file(), f'missing one or both marketplace.json files (CC: {CC_MARKETPLACE}, Codex: {CODEX_MARKETPLACE})')
        if CC_MARKETPLACE.is_file() and CODEX_MARKETPLACE.is_file():
            cc_marketplace_name = _json_field(CC_MARKETPLACE, 'name')
            codex_marketplace_name = _json_field(CODEX_MARKETPLACE, 'name')
            with self.subTest(msg=f'CC and Codex marketplace names match ({cc_marketplace_name})'):
                self.assertEqual(cc_marketplace_name, codex_marketplace_name, f'marketplace names must match: CC={cc_marketplace_name}, Codex={codex_marketplace_name}')
        if validate_codex_parity_AGENTS_DIR.is_dir() and validate_codex_parity_CODEX_AGENTS_DIR.is_dir():
            generated = generated_codex_files(PLUGIN_ROOT, AGENT_INVENTORY)
            for cc_agent_file in _sorted_files(validate_codex_parity_AGENTS_DIR, '.md'):
                agent_name = cc_agent_file.name[:-len('.md')]
                if agent_name in CC_ONLY_AGENTS:
                    continue
                self._assert_agent_generated(agent_name, generated)
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
                self._assert_payload_skill_built(skill_name)
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

CODEX_SKILLS_PRIMARY = '.agents/skills/'
CODEX_SKILLS_LEGACY = '.codex/skills/'


def _mirrors(skill: str) -> tuple[tuple[str, str], ...]:
    return tuple(
        (f'{host}/{skill}', (view / skill / 'SKILL.md').read_text(encoding='utf-8'))
        for host, view in (('claude', CLAUDE_VIEW), ('codex', CODEX_VIEW))
    )


def _step(text: str, start: str, end: str) -> str:
    return ' '.join(text.split(start, 1)[1].split(end, 1)[0].split())


class ValidateCodexSkillsDualPath(unittest.TestCase):
    """Codex skills live in .agents/skills (primary) or .codex/skills (legacy)."""

    def test_install_mirrors_name_agents_skills_as_primary(self) -> None:
        for label, text in _mirrors('speckit-install'):
            with self.subTest(mirror=label):
                self.assertIn(f'{CODEX_SKILLS_PRIMARY}speckit-*/', text)

    def test_legacy_codex_skills_path_is_always_labelled_legacy(self) -> None:
        for skill in ('speckit-install', 'speckit-upgrade'):
            for label, text in _mirrors(skill):
                for paragraph in text.split('\n\n'):
                    if CODEX_SKILLS_LEGACY in paragraph:
                        with self.subTest(mirror=label, paragraph=paragraph[:80]):
                            self.assertIn('legacy', paragraph.lower())
                            self.assertIn(CODEX_SKILLS_PRIMARY, paragraph)

    def test_upgrade_snapshot_backs_up_both_codex_skills_paths(self) -> None:
        for label, text in _mirrors('speckit-upgrade'):
            snapshot = _step(text, '### 4. Snapshot', '### 5.')
            with self.subTest(mirror=label):
                for directory in ('`.specify/`', '`.claude/`', '`.codex/`', '`.agents/skills/`', '`.github/`'):
                    self.assertIn(directory, snapshot)
                self.assertRegex(snapshot, r'`\.agents/skills/` \(primary\) or `\.codex/skills/` \(legacy\); back up whichever exists')

    def test_upgrade_dedupe_detects_both_codex_skills_paths(self) -> None:
        for label, text in _mirrors('speckit-upgrade'):
            dedupe = _step(text, '### 6. Deduplicate', '### 7.')
            with self.subTest(mirror=label):
                for path in ('`.codex/prompts/', '`.agents/skills/speckit-*/` (primary)', '`.codex/skills/speckit-*/`'):
                    self.assertIn(path, dedupe)


class ValidateStopPolicyReference(unittest.TestCase):
    """Both autopilot skills load the one shared stop-policy reference."""

    LINKS = (
        ('Claude', 'skills/speckit-autopilot/SKILL.md', '(./references/stop-policy.md)'),
        ('Codex', 'skills/speckit-autopilot/SKILL.md', '(./references/stop-policy.md)'),
    )

    def test_shared_reference_exists_in_source_and_both_payloads(self) -> None:
        for label, root in (('source', PLUGIN_ROOT),
                            ('Claude payload', REPO_ROOT / 'dist/claude/speckit-pro'),
                            ('Codex payload', REPO_ROOT / 'dist/codex/speckit-pro')):
            with self.subTest(msg=f'{label}: references/stop-policy.md exists'):
                self.assertTrue((root / 'skills/speckit-autopilot/references/stop-policy.md').is_file())

    def test_both_autopilot_skills_link_it_and_the_link_resolves(self) -> None:
        for label, skill, link in self.LINKS:
            path = PLUGIN_ROOT / skill
            with self.subTest(msg=f'{label} autopilot skill links stop-policy.md'):
                self.assertIn(link, _read(path))
                self.assertTrue((path.parent / link.strip('()')).resolve().is_file())

class ValidatePayloadLinksStayInside(unittest.TestCase):
    """A shipped skill or agent never links a file outside the installed plugin.

    The repository resolves `../../../../docs-site/...`, but an installed plugin
    holds only its payload, so such a link is dead for every reader of the
    installed copy.
    """

    LINK_RE = re.compile(r'\]\(([^)\s]+)\)')
    FENCE_RE = re.compile(r'```.*?```', re.DOTALL)

    SKIP_RE = re.compile(r'^(?:[a-z][a-z0-9+.-]*:|[$<{])')

    def payload_links(self, root: Path) -> list[tuple[Path, str]]:
        """Every relative link in the payload's skill and agent Markdown."""
        links = []
        for path in sorted([*(root / 'skills').rglob('*.md'), *(root / 'agents').rglob('*.md')]):
            text = self.FENCE_RE.sub('', path.read_text(encoding='utf-8', errors='replace'))
            links.extend((path, target) for target in self.LINK_RE.findall(text))
        return [(path, target) for path, target in links
                if target.split('#', 1)[0] and not self.SKIP_RE.match(target)]

    def test_relative_links_resolve_inside_each_payload(self) -> None:
        checked = 0
        for host in ('claude', 'codex'):
            root = (REPO_ROOT / 'dist' / host / 'speckit-pro').resolve()
            for path, target in self.payload_links(root):
                checked += 1
                resolved = (path.parent / target.split('#', 1)[0]).resolve()
                with self.subTest(msg=f'{host}: {path.relative_to(root)} -> {target}'):
                    self.assertTrue(resolved.is_relative_to(root), f'{target} leaves the installed {host} payload')
        self.assertTrue(checked, 'no payload links checked - refusing to pass vacuously')

class ValidateScaffoldBlindSpotDeadline(unittest.TestCase):

    def test_scaffold_blind_spot_deadline_is_enforced_on_each_host(self) -> None:
        # A deadline stated only in prose idled a session for 12 minutes: each
        # host must arm a wake at dispatch and stop the analyst when it fires.
        def blind_spot_pass(view: Path) -> str:
            skill = (view / 'speckit-scaffold-spec' / 'SKILL.md').read_text(encoding='utf-8')
            section = skill.split('### 3.6 Blind-Spot Pass', 1)[-1].split('\n### ', 1)[0]
            self.assertIn('**The bound.', section, 'expected the blind-spot pass section')
            return ' '.join(section.split())

        claude, codex = blind_spot_pass(CLAUDE_VIEW), blind_spot_pass(CODEX_VIEW)
        for host, section in (('claude', claude), ('codex', codex)):
            with self.subTest(host=host, check='one deadline value'):
                minutes = re.findall(r'Pass execution deadline \| \*\*(\d+) minutes from dispatch\*\*', section)
                self.assertEqual(1, len(minutes), 'expected one pass execution deadline in the bound table')
            with self.subTest(host=host, check='analyst carries a tool-call budget'):
                block = section.split('You are running a blindspot pass', 1)[-1].split('```', 1)[0]
                self.assertRegex(block, r'Budget: at most \d+ tool calls\. When you reach it, stop exploring and return the findings you have')
                self.assertIn('If you find nothing, reply exactly: The blindspot pass raised no unknown unknowns.', block)
                self.assertIn('N. **<Title>** - the finding, plus a repo-relative file or path pointer.', block)
        seconds = int(re.search(r'\*\*(\d+) minutes from dispatch\*\*', claude).group(1)) * 60
        with self.subTest(host='claude', check='timer armed at dispatch'):
            self.assertIn(f'background command (`run_in_background: true`) that runs `[resolved_python, "-c", "import time; time.sleep({seconds})"]`', claude)
            self.assertIn('Arm the deadline in the same turn as the dispatch', claude)
        with self.subTest(host='claude', check='deadline stops the analyst'):
            self.assertIn('**The timer completes first:** the deadline has passed. Stop the analyst with `TaskStop` on its task id', claude)
            self.assertIn('**The analyst replies first:** stop the timer with `TaskStop` on its task id', claude)
        with self.subTest(host='codex', check='wait is capped at the deadline'):
            self.assertIn('pass `timeout_ms` set to the time left until the pass execution deadline, never more', codex)
        with self.subTest(host='codex', check='deadline closes the analyst'):
            self.assertIn('When the deadline passes with no summary, call `close_agent` on the analyst when that action is exposed, otherwise `interrupt_agent` when exposed', codex)
            self.assertNotIn('TaskStop', codex)
        for host, section in (('claude', claude), ('codex', codex)):
            with self.subTest(host=host, check='deadline records did not run'):
                self.assertRegex(section, r'record `did not run` with reason `wait deadline expired`')

class ValidateScaffoldHelperInputs(unittest.TestCase):

    def test_scaffold_names_exact_helper_inputs_on_each_host(self) -> None:
        # ADR 0008: guessed mode/setup keys caused a real scaffold failure.
        expected_inputs = {
            'reviewability-gate': {'mode_name': 'setup', 'target': '<technical-roadmap-path>', 'spec_id': '<SPEC-ID>'},
            'check-prerequisites': {'workflow_file': '<workflow-file>'},
            'check-roadmap-freshness': {'roadmap_path': '<technical-roadmap-path>'},
            'detect-commands': {},
            'research-broker-preflight': {},
            'o5-topology': {'target': 'specs/<parent-branch>'},
            'resolve-workflow-binding': {'workflow_file': '<absolute-workflow-path>'},
            'resolve-scaffold-worktree-placement': {'branch_name': '<branch-name>'},
            'scaffold-answers': {'answers_file': '<answers-file>', 'spec_id': '<SPEC-ID>'},
        }
        for host, view in (('claude', CLAUDE_VIEW), ('codex', CODEX_VIEW)):
            skill = (view / 'speckit-scaffold-spec' / 'SKILL.md').read_text(encoding='utf-8')
            for helper, inputs in expected_inputs.items():
                with self.subTest(host=host, helper=helper):
                    rows = re.findall(r'\| `' + re.escape(helper) + r'` \| `read_only` \| `(\{[^\n`]*\})`', skill)
                    self.assertEqual(1, len(rows), f'{helper}: expected one explicit request-input example')
                    self.assertEqual(inputs, json.loads(rows[0]))
                    self._assert_runner_accepts_keys(helper, rows[0])
            if host == 'codex':
                section = skill.split('### -0.5 Verify Codex Agent Install', 1)[1].split('\n### ', 1)[0]
                examples = [json.loads(block) for block in re.findall(r'```json\n(.*?)\n```', section, re.DOTALL)]
                self.assertEqual(2, len(examples), 'verification must document static and routed request fields')
                for example, keys in zip(examples, (
                    {'destination', 'model', 'luna_fallback'},
                    {'destination', 'route_policy_manifest', 'strict_model_override'},
                ), strict=True):
                    with self.subTest(host=host, helper='install-codex-agents', keys=keys):
                        self.assertEqual({'mode', 'inputs'}, set(example))
                        self.assertEqual('dry_run', example['mode'])
                        self.assertEqual(keys, set(example['inputs']))
                self.assertIn('Replay the selected installation inputs', section)
                self.assertIn('Omit optional fields that were absent from the selected installation', section)
                self.assertNotIn('routing_mode', skill)

    def _assert_runner_accepts_keys(self, helper: str, example: str) -> None:
        # Drift guard: replay the documented keys through the real runner. A key the
        # helper no longer accepts (or a new required key) surfaces as one of these
        # input-schema diagnostics.
        samples = {'mode_name': 'setup', 'spec_id': 'SPEC-1', 'branch_name': 'scaffold-helper-inputs'}
        inputs = {key: samples.get(key, 'README.md') for key in json.loads(example)}
        request = {'schema_version': '1.0', 'helper_id': helper, 'operation': helper, 'mode': 'read_only', 'inputs': inputs}
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'README.md').write_text('# roadmap\n', encoding='utf-8')
            proc = subprocess.run([sys.executable, '-m', 'speckit_pro_runner'], input=json.dumps(request), capture_output=True, text=True, cwd=tmp,
                                  env={**os.environ, 'PYTHONPATH': str(REPO_ROOT / 'speckit-pro')}, check=False, timeout=120)
        response = json.loads(proc.stdout.strip().splitlines()[-1])
        text = json.dumps(response.get('diagnostics', [])) + json.dumps(response.get('data', {}).get('stderr', ''))
        for phrase in ('is required', 'unknown inputs', 'takes no inputs', 'unexpected_inputs'):
            self.assertNotIn(phrase, text, f'{helper}: runner rejected documented inputs {inputs}')

class ValidateScaffoldRoadmapFreshness(unittest.TestCase):

    def test_scaffold_checks_roadmap_freshness_before_parsing_on_each_host(self) -> None:
        # A stale checkout once fed scaffold an old roadmap entry: each host must
        # call the runner check before step 2 parses the roadmap, stop on its
        # verdict, and base the new worktree branch on the revision it returns.
        from speckit_pro_runner.helpers.registry import HELPERS
        helper = 'check-roadmap-freshness'
        self.assertIn(helper, HELPERS, 'the freshness check must be a registered runner helper')
        for host, view in (('claude', CLAUDE_VIEW), ('codex', CODEX_VIEW)):
            skill = ' '.join((view / 'speckit-scaffold-spec' / 'SKILL.md').read_text(encoding='utf-8').split())
            with self.subTest(host=host, check='called before the roadmap is parsed'):
                call = skill.find(f'run runner helper `{helper}`')
                self.assertNotEqual(-1, call, 'expected scaffold to call the freshness helper')
                self.assertLess(call, skill.index('### 2. Find the Spec in the Technical Roadmap'))
                self.assertLess(skill.index('### 1. Find the Technical Roadmap'), call)
            with self.subTest(host=host, check='stops on the verdict'):
                self.assertIn('Require `verdict=proceed`. On `verdict=stop`, print the returned `stop_message` unchanged and STOP', skill)
            with self.subTest(host=host, check='worktree is based on the returned revision'):
                self.assertIn('Base a new branch on the `base_revision` from step 1', skill)
        self.assertFalse((REPO_ROOT / 'speckit-pro' / 'codex-skills' / 'speckit-scaffold-spec' / 'SKILL.md').exists(), 'scaffold keeps one shared skill source')

def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-skill-contracts")

if __name__ == "__main__":
    raise SystemExit(main())
