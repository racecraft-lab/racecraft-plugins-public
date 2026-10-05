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
from host_skill_views import host_skill_root

ROADMAP_TEMPLATE = PLUGIN_ROOT / 'skills/speckit-coach/templates/technical-roadmap-template.md'
SPEC_TEMPLATES = (REPO_ROOT / '.specify/presets/speckit-pro-reviewability/templates/spec-template.md', REPO_ROOT / '.specify/templates/spec-template.md')
PRESET_PLAN_TEMPLATE = REPO_ROOT / '.specify/presets/speckit-pro-reviewability/templates/plan-template.md'
WORKFLOW_TEMPLATE = PLUGIN_ROOT / 'skills/speckit-coach/templates/workflow-template.md'
AUTOPILOT_SKILL_DIR = PLUGIN_ROOT / 'skills/speckit-autopilot'
SCAFFOLD_SKILL = PLUGIN_ROOT / 'skills/speckit-scaffold-spec/SKILL.md'

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

def markdown_section(content: str, heading: str) -> str:
    """Return a section's text from its heading line to the next heading of equal or higher level."""
    level = len(heading) - len(heading.lstrip('#'))
    match = re.search(rf'^{re.escape(heading)}\s*$(.*?)(?=^#{{1,{level}}} |\Z)', content, re.M | re.S)
    return match.group(1) if match else ''

class ValidateOneClarifySession(unittest.TestCase):
    """Every SPEC runs one Clarify session of at most 5 questions (one planning path)."""

    def setUp(self) -> None:
        self.template = WORKFLOW_TEMPLATE.read_text(encoding='utf-8')
        self.clarify = markdown_section(self.template, '## Phase 2: Clarify')

    def assert_absent(self, text: str, pattern: str) -> None:
        match = re.search(pattern, text)
        self.assertIsNone(match, f'contradicting clarify text: {match.group(0) if match else ""}')

    def test_workflow_template_has_one_clarify_session(self) -> None:
        prompts = markdown_section(self.clarify, '### Clarify Prompts')
        self.assertEqual(1, prompts.count('/speckit-clarify'), 'the template carries exactly one clarify prompt')
        self.assertEqual(1, len(re.findall(r'^#### Session \d+', prompts, re.M)))
        results = markdown_section(self.clarify, '### Clarify Results')
        self.assertEqual(1, len(re.findall(r'^\| \d+ \|', results, re.M)), 'Clarify Results has one session row')

    def test_workflow_template_caps_the_session_at_five_questions(self) -> None:
        self.assertIn('at most 5 questions', self.clarify)

    def test_workflow_template_does_not_make_clarify_optional(self) -> None:
        overview = re.search(r'^\| Clarify \|.*$', self.template, re.M)
        self.assertIsNotNone(overview, 'Workflow Overview has a Clarify row')
        self.assert_absent(overview.group(0), r'(?i)optional')
        self.assert_absent(self.clarify, r'(?i)\bwhen to run:\*\*\s*when')

    def test_phase_reference_has_no_marker_gate_on_clarify(self) -> None:
        text = (AUTOPILOT_SKILL_DIR / 'references/phase-execution.md').read_text(encoding='utf-8')
        section = markdown_section(text, '### Phase 2: Clarify')
        self.assertTrue(section, 'the Phase 2 section is present')
        self.assert_absent(text, r'Phase 2: Clarify \(Conditional\)')
        self.assert_absent(text, r'(?i)only runs if G1')
        self.assert_absent(text, r'(?i)separate subagent for each clarify session')
        self.assertIn('one session', text.lower())

    def test_autopilot_skill_has_no_marker_gate_on_clarify(self) -> None:
        text = (AUTOPILOT_SKILL_DIR / 'SKILL.md').read_text(encoding='utf-8')
        gate_text = (AUTOPILOT_SKILL_DIR / 'references/gate-validation.md').read_text(encoding='utf-8')
        self.assert_absent(text, r'(?i)clarify still runs only when')
        self.assert_absent(text, r'(?i)Clarify and Checklist have multiple prompts')
        self.assert_absent(gate_text, r'(?i)skip clarify')
        self.assertNotRegex(gate_text, r'(?i)re-run clarify')
        self.assertIn('without dispatching another clarify session', gate_text.lower())

    def test_scaffold_seeds_one_clarify_session(self) -> None:
        text = SCAFFOLD_SKILL.read_text(encoding='utf-8')
        self.assert_absent(text, r'(?i)one focus per open\s+behavior area')
        self.assertIn('one clarify session', text.lower())

    def test_both_hosts_consolidate_older_clarify_prompts_before_dispatch(self) -> None:
        for host in ('claude', 'codex'):
            with self.subTest(host=host):
                root = host_skill_root(host) / 'speckit-autopilot'
                skill = (root / 'SKILL.md').read_text(encoding='utf-8')
                rule = markdown_section(skill, '### 4. Multi-prompt phases')
                self.assertRegex(rule, r'(?s)older workflows.*multiple Clarify prompts')
                self.assertRegex(rule, r'(?s)combine.*one prompt')
                self.assertRegex(rule, r'(?s)before creating.*task.*phase brief')
                phase = (root / 'references/phase-execution.md').read_text(encoding='utf-8')
                self.assertIn('Normalize Clarify through Rule 4 before reading phase prompts.', phase)

FROZEN_MARKER = "🧊 Frozen"
HEALTH_PROGRAM = "https://github.com/racecraft-lab/racecraft-plugins-public/issues/1038"
SPEC_ID = r"[A-Z][A-Z0-9]*-\d+[a-z]?"
CLOSED_STATUS = re.compile(r"^[^\w]*(?:complete(?:d)?|archived|retired|superseded|dropped|shipped)\b", re.I)


def roadmap_progress_statuses(content: str) -> list[tuple[str, str]]:
    """Read SPEC rows only within a progress table, including omitted cells."""
    # GFM permits optional outer pipes and fills omitted cells with empty values.
    rows = []
    status_column = None
    for line in content.splitlines():
        if not line.strip() or line.lstrip().startswith(("#", ">", "```", "~~~")):
            status_column = None
            continue
        cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip().removeprefix("|"))]
        columns = [cell.casefold() for cell in cells]
        if columns[0] == "spec" and "status" in columns:
            status_column = columns.index("status")
        elif status_column is not None and re.fullmatch(SPEC_ID, cells[0]):
            rows.append((cells[0], cells[status_column] if len(cells) > status_column else ""))
    return rows


def roadmap_entry_statuses(content: str) -> list[tuple[str, str]]:
    """Read statuses from progress rows and SPEC sections without changing them."""
    rows = roadmap_progress_statuses(content)
    statuses = dict(rows)
    entries = list(rows)
    sections = re.findall(rf"^### ({SPEC_ID})\b([^\n]*)(.*?)(?=^#{{1,3}} |\Z)", content, re.M | re.S)
    for spec_id, heading, body in sections:
        status = re.search(r"^\*\*Status:\*\* (.+)$", body, re.M)
        entries.append((spec_id, status.group(1) if status else statuses.get(spec_id, heading.rsplit("·", 1)[-1].strip())))
    return entries


def roadmap_freeze_errors(content: str) -> list[str]:
    """Check every catalog entry, including headings outside a progress table."""
    entries = roadmap_entry_statuses(content)
    if not entries:
        return ["no roadmap SPEC entries found"]
    errors = []
    for spec_id, status in entries:
        if spec_id == "HRNS-015":
            if FROZEN_MARKER in status:
                errors.append("HRNS-015 must remain exempt")
        elif not CLOSED_STATUS.match(status) and FROZEN_MARKER not in status:
            errors.append(f"{spec_id}: open entry lacks {FROZEN_MARKER}")
    if any(FROZEN_MARKER in status for _, status in entries):
        if f"]({HEALTH_PROGRAM})" not in content:
            errors.append("freeze note must link the health program spec")
        if "EDA-001" not in content:
            errors.append("freeze note must name EDA-001")
    return errors


class ValidateRoadmapFreeze(unittest.TestCase):
    def setUp(self) -> None:
        self.content = (Path(__file__).parent / "fixtures/roadmap-freeze/catalog.txt").read_text(encoding="utf-8")

    def test_freeze_fixture_accepts_closed_entries_and_the_exemption(self) -> None:
        content = self.content
        self.assertEqual([], roadmap_freeze_errors(content))

    def test_freeze_fixture_rejects_unfrozen_progress_rows(self) -> None:
        content = self.content
        for status in ("Pending", "Ready", "In Progress", "In Review", "Blocked", "Unknown", ""):
            with self.subTest(status=status):
                unfrozen = content.replace("⏳ Pending · 🧊 Frozen", status)
                self.assertIn("TEST-001: open entry lacks 🧊 Frozen", roadmap_freeze_errors(unfrozen))

    def test_freeze_fixture_rejects_section_and_exemption_regressions(self) -> None:
        cases = (
            (self.content.replace("| HRNS-015", "TEST-006|New open work\n| HRNS-015", 1),
             "TEST-006: open entry lacks 🧊 Frozen"),
            (self.content.replace("| HRNS-015", "TEST-006|New\\|Complete\n| HRNS-015", 1),
             "TEST-006: open entry lacks 🧊 Frozen"),
            (self.content.replace("| HRNS-015", "| TEST-006 | New\\|Complete | Ready | - | Specify |\n| HRNS-015", 1),
             "TEST-006: open entry lacks 🧊 Frozen"),
            (self.content.replace("| HRNS-015", "|TEST-006|New open work|Ready|-|Specify|\n| HRNS-015", 1),
             "TEST-006: open entry lacks 🧊 Frozen"),
            (self.content.replace("| HRNS-015", "TEST-006|New open work|Ready|-|Specify\n| HRNS-015", 1),
             "TEST-006: open entry lacks 🧊 Frozen"),
            (self.content.replace("| HRNS-015", "|TEST-006|New open work|Ready\n| HRNS-015", 1),
             "TEST-006: open entry lacks 🧊 Frozen"),
            (self.content.replace("**Status:** 🧊 Frozen — previously Pending.", "**Status:** Pending."),
             "TEST-001: open entry lacks 🧊 Frozen"),
            (self.content + "\n### TEST-006: New open work\n\n**Status:** Ready\n",
             "TEST-006: open entry lacks 🧊 Frozen"),
            (self.content.replace("⏳ Ready", "⏳ Ready · 🧊 Frozen"),
             "HRNS-015 must remain exempt"),
        )
        for content, error in cases:
            with self.subTest(error=error):
                self.assertIn(error, roadmap_freeze_errors(content))

    def test_freeze_fixture_requires_the_health_program_link_and_eda_note(self) -> None:
        content = self.content
        for missing, error in ((HEALTH_PROGRAM, "freeze note must link the health program spec"),
                               ("EDA-001", "freeze note must name EDA-001")):
            with self.subTest(missing=missing):
                self.assertIn(error, roadmap_freeze_errors(content.replace(missing, "removed")))

    def test_freeze_check_rejects_an_empty_catalog(self) -> None:
        self.assertEqual(["no roadmap SPEC entries found"], roadmap_freeze_errors("# Empty roadmap\n"))

    def test_open_roadmap_specs_are_frozen(self) -> None:
        roadmaps = sorted((REPO_ROOT / "docs/ai/specs").rglob("*technical-roadmap.md"))
        self.assertTrue(roadmaps, "no technical roadmaps found")
        for roadmap in roadmaps:
            with self.subTest(roadmap=_rel_repo(roadmap)):
                self.assertEqual([], roadmap_freeze_errors(roadmap.read_text(encoding="utf-8")))

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

    def registered_extensions(self) -> dict | None:
        """The registry's extension records, or None (after failing a subtest) when unusable."""
        with self.subTest(msg='Spec Kit extension registry exists'):
            self.assertTrue(REGISTRY_PATH.is_file(), f'file not found: {REGISTRY_PATH}')
        with self.subTest(msg='Spec Kit extension hook configuration exists'):
            self.assertTrue(HOOKS_PATH.is_file(), f'file not found: {HOOKS_PATH}')
        if not REGISTRY_PATH.is_file() or not HOOKS_PATH.is_file():
            return None
        registry = load_registry()
        extensions = registry.get('extensions') if isinstance(registry, dict) else None
        with self.subTest(msg='Spec Kit extension registry has schema 1.0 and extension records'):
            self.assertEqual(registry.get('schema_version'), '1.0')
            self.assertIsInstance(extensions, dict)
        return extensions if isinstance(extensions, dict) else None

    def check_extension_payload(self, extension_id: str, record: dict) -> set[str]:
        """Check one enabled extension's files and Claude commands; return its commands."""
        extension_dir = EXTENSIONS_ROOT / extension_id
        with self.subTest(msg=f'enabled extension payload exists: {extension_id}'):
            self.assertTrue((extension_dir / 'extension.yml').is_file())
        if not (extension_dir / 'extension.yml').is_file():
            return set()
        for path in declared_files(extension_dir):
            with self.subTest(msg=f'declared extension file exists: {path.relative_to(REPO_ROOT)}'):
                self.assertTrue(path.is_file(), f'declared extension file not found: {path}')
        commands = record.get('registered_commands')
        claude_commands = commands.get('claude', []) if isinstance(commands, dict) else []
        registered = {command for command in claude_commands if isinstance(command, str)} if isinstance(claude_commands, list) else set()
        for command in sorted(registered):
            with self.subTest(msg=f'registered Claude extension command resolves: {command}'):
                self.assertTrue(claude_skill_path(command).is_file(), f'generated Claude skill not found for {command}: {claude_skill_path(command)}')
        return registered

    def check_verify_extension(self, extensions: dict) -> None:
        verify = extensions.get('verify')
        with self.subTest(msg='Verify extension is pinned to repaired v1.0.3 payload'):
            self.assertIsInstance(verify, dict)
            self.assertEqual(verify.get('version') if isinstance(verify, dict) else None, '1.0.3')
        verify_loader = EXTENSIONS_ROOT / 'verify' / 'scripts' / 'bash' / 'load-config.sh'
        with self.subTest(msg='Verify Bash loader retains its declared executable mode'):
            self.assertTrue(verify_loader.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH), f'declared executable is not executable: {verify_loader}')

    def test_extension_integrity(self) -> None:
        extensions = self.registered_extensions()
        if extensions is None:
            return
        registered_commands: set[str] = set()
        for extension_id, record in sorted(extensions.items()):
            if isinstance(record, dict) and record.get('enabled') is True:
                registered_commands |= self.check_extension_payload(extension_id, record)
        hook_commands = {match.group(1) for line in HOOKS_PATH.read_text(encoding='utf-8').splitlines() if (match := HOOK_COMMAND.match(line)) is not None}
        for command in sorted(hook_commands):
            with self.subTest(msg=f'configured extension hook resolves: {command}'):
                self.assertIn(command, registered_commands)
        self.check_verify_extension(extensions)

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
