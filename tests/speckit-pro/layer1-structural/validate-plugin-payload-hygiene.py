#!/usr/bin/env python3
"""Plugin payload hygiene: no shell scripts, and no hardcoded interpreter in shipped prose."""

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

from test_result import run_counted

SCRIPT_SUFFIXES = {'.sh', '.ps1', '.bat', '.cmd'}
SHELL_SHEBANG_RE = re.compile('^#!.*\\b(?:bash|sh|zsh|powershell|pwsh)\\b', re.IGNORECASE)

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


class ValidatePluginScripts(unittest.TestCase):

    def test_001_zero_live_script_files(self) -> None:
        with self.subTest(msg='speckit-pro: contains zero live shell/command script files'):
            script_count = _live_script_count(PLUGIN_ROOT)
            self.assertEqual(0, script_count, f'expected zero live plugin script files, found {script_count}')

EXCLUDED_NAMES = frozenset({'CHANGELOG.md'})
HARDCODED_INTERPRETER = re.compile('(?<![\\w./-])(?:python[0-9.]*|py)\\s+(?=[-\\w\\"\'/$])')
RESOLVED_TOKEN = 'resolved_python'
COVERAGE_SCRIPT = 'validate-autopilot-phase-coverage.py'
COVERAGE_RULE_FLAG = '--rule status-evidence'
COVERAGE_FLAGS = ('--workflow', '--state')
PLATFORM_HOSTS = {'Claude': 'claude', 'Codex': 'codex'}
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

def host_coverage_invocations(host: str) -> list[str]:
    """Guard invocation lines in the skill tree `host` loads (host blocks rendered)."""
    from host_skill_views import host_skill_root

    return [line for path in sorted(host_skill_root(host).rglob('*.md'))
            for line in path.read_text(encoding='utf-8').splitlines()
            if COVERAGE_SCRIPT in line and any((flag in line for flag in COVERAGE_FLAGS))]

def coverage_invocation_errors() -> list[str]:
    """Every discovered guard invocation must be resolvable and identically scoped."""
    invocations = coverage_invocations()
    errors: list[str] = []
    for platform, host in sorted(PLATFORM_HOSTS.items()):
        if not host_coverage_invocations(host):
            errors.append(f'no {COVERAGE_SCRIPT} invocation found in the {platform} skill view, so the {platform} distribution would run no coverage guard at all')
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


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-plugin-payload-hygiene")


if __name__ == "__main__":
    raise SystemExit(main())
