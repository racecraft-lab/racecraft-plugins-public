#!/usr/bin/env python3
"""Consolidated Layer 1 contracts owned by validate-ci-release-contracts.py."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import importlib.util
import json
import posixpath
import re
import shlex
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for _import_root in (LIB_DIR, PLUGIN_ROOT):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))

from speckit_pro_runner.helpers import read_only
from test_result import run_counted

CollectionKind = Literal['mapping', 'sequence']
BLOCK_SCALARS = {'|', '>', '|-', '>-', '|+', '>+'}

@dataclass(frozen=True)
class _Collection:
    indent: int
    kind: CollectionKind

@dataclass(frozen=True)
class _NestedValue:
    parent_indent: int
    kind: CollectionKind | None

def _split_mapping(text: str) -> tuple[str, str] | None:
    """Split a block mapping entry at a YAML-significant colon."""
    quote: str | None = None
    escaped = False
    flow: list[str] = []
    pairs = {']': '[', '}': '{'}
    for index, char in enumerate(text):
        if quote == '"':
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                quote = None
            continue
        if quote == "'":
            if char == quote:
                if index + 1 < len(text) and text[index + 1] == quote:
                    continue
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
        elif char in '[{':
            flow.append(char)
        elif char in ']}':
            if not flow or flow.pop() != pairs[char]:
                return None
        elif char == ':' and (not flow) and (index + 1 == len(text) or text[index + 1].isspace()):
            return (text[:index], text[index + 1:])
    return None

def _strip_comment(text: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(text):
        if quote == '"':
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                quote = None
        elif quote == "'":
            if char == quote:
                if index + 1 < len(text) and text[index + 1] == quote:
                    continue
                quote = None
        elif char in {'"', "'"}:
            quote = char
        elif char == '#' and (index == 0 or text[index - 1].isspace()):
            return text[:index].rstrip()
    return text.rstrip()

def _scalar_sane(text: str) -> bool:
    """Reject unterminated quotes and flow collections in a scalar value."""
    text = _strip_comment(text)
    quote: str | None = None
    escaped = False
    flow: list[str] = []
    pairs = {']': '[', '}': '{'}
    for index, char in enumerate(text):
        if quote == '"':
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                quote = None
            continue
        if quote == "'":
            if char == quote:
                if index + 1 < len(text) and text[index + 1] == quote:
                    continue
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
        elif char in '[{':
            flow.append(char)
        elif char in ']}':
            if not flow or flow.pop() != pairs[char]:
                return False
    return quote is None and (not flow) and (not escaped)

def yaml_syntax_sane(text: str) -> bool:
    """Check the indentation and scalar surface used by GitHub workflow YAML."""
    collections: list[_Collection] = []
    nested_value: _NestedValue | None = None
    block_parent_indent: int | None = None
    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue
        leading = raw_line[:len(raw_line) - len(raw_line.lstrip(' \t'))]
        if '\t' in leading:
            return False
        indent = len(leading)
        if block_parent_indent is not None:
            if indent > block_parent_indent:
                continue
            block_parent_indent = None
        stripped = raw_line[indent:]
        if stripped.startswith('#'):
            continue
        if stripped in {'---', '...'}:
            if indent != 0:
                return False
            continue
        is_sequence = stripped == '-' or stripped.startswith('- ')
        line_kind: CollectionKind = 'sequence' if is_sequence else 'mapping'
        while collections and indent < collections[-1].indent:
            collections.pop()
        if not collections:
            if indent != 0 or line_kind != 'mapping':
                return False
            collections.append(_Collection(indent, line_kind))
        elif indent == collections[-1].indent:
            if line_kind != collections[-1].kind:
                return False
        else:
            if nested_value is None or nested_value.parent_indent != collections[-1].indent:
                return False
            if nested_value.kind is not None and line_kind != nested_value.kind:
                return False
            collections.append(_Collection(indent, line_kind))
        nested_value = None
        item = stripped[1:].lstrip() if is_sequence else stripped
        if is_sequence and (not item):
            nested_value = _NestedValue(indent, None)
            continue
        mapping = _split_mapping(item)
        if mapping is None:
            if not is_sequence or not _scalar_sane(item):
                return False
            continue
        key, value = mapping
        if not key.strip() or not _scalar_sane(value):
            return False
        scalar = _strip_comment(value).strip()
        if scalar in BLOCK_SCALARS:
            block_parent_indent = indent
        elif not scalar:
            nested_value = _NestedValue(indent, None)
        elif is_sequence:
            nested_value = _NestedValue(indent, 'mapping')
    return True
validate_pr_checks_sentinel_WORKFLOW_FILE = REPO_ROOT / '.github' / 'workflows' / 'pr-checks.yml'
ACTIONLINT_HELPER_FILE = REPO_ROOT / 'scripts' / 'install-actionlint.py'
DOCS_CLASSIFIER_FILE = REPO_ROOT / 'scripts' / 'classify-docs-validation.py'
RESULTS_HELPER_FILE = REPO_ROOT / 'scripts' / 'check-pr-workflow-results.py'
MATRIX_HELPER_FILE = REPO_ROOT / 'scripts' / 'emit-plugin-matrix.py'
CONTAINER_WORKFLOW_FILE = REPO_ROOT / '.github' / 'workflows' / 'container-preflight.yml'
WINDOWS_PREFLIGHT_HELPER_FILE = REPO_ROOT / 'tests' / 'speckit-pro' / 'run-hosted-windows-preflight.py'
CONTAINER_DISPATCH_HELPER_FILE = REPO_ROOT / 'tests' / 'speckit-pro' / 'run-container-preflight.py'
WORKFLOWS_DIR = REPO_ROOT / '.github' / 'workflows'
validate_pr_checks_sentinel_CHECKOUT_PIN_RE = re.compile('uses: actions/checkout@[0-9a-f]{40}')
UPLOAD_ARTIFACT_PIN = 'actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a'
SETUP_PYTHON_PIN_RE = re.compile('actions/setup-python@[0-9a-f]{40}')
SETUP_PYTHON_COMMENTED_PIN_RE = re.compile('uses: actions/setup-python@[0-9a-f]{40} # v\\d+\\.\\d+\\.\\d+')
HOSTED_PYTHON_VERSION = 'HOSTED_PYTHON_VERSION: "3.13.14"'
CONTAINER_IMAGE_PIN = 'python:3.11.15-bookworm@sha256:b7ae8a4dcc0ab327e333c5e46a3eaa6c1b0ff585bed77e01cd6de4be1325837e'
CONTAINER_DISPATCH = 'run: import runpy; runpy.run_path("tests/speckit-pro/run-container-preflight.py", run_name="__main__")'
SPEC_KIT_VERSION_PIN = 'SPEC_KIT_VERSION: v0.8.13'
SPEC_KIT_REF_PIN = 'SPEC_KIT_GIT_REF: git+https://github.com/github/spec-kit.git@b2314680fce898e0a9151b37ad2535d810c93eef'
UNIQUE_ARTIFACT_SUFFIX = '-${{ github.run_id }}-${{ github.run_attempt }}'
TITLE_LITERAL = "TITLE: ${{ github.event_name == 'pull_request' && github.event.pull_request.title || inputs.pr_title }}"
CONTENT_CHECKS: list[tuple[str, str, str, list[str]]] = [('workflow', 'all', 'title validation uses the live Python title gate', ['validate-pr-title-live.json', 'python3 -m speckit_pro_runner']), ('workflow', 'all', 'title validation supplies the live title', [TITLE_LITERAL]), ('workflow', 'all', 'workflow validation job is defined', ['validate-workflows:']), ('combined', 'all', 'workflow validation installs pinned actionlint', ['ACTIONLINT_VERSION: "1.7.12"', 'ACTIONLINT_SHA256: "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8"', 'run: python3 scripts/install-actionlint.py install', 'https://github.com/rhysd/actionlint/releases/download/', 'verify_sha256(archive_path, pinned_sha256)']), ('combined', 'all', 'workflow validation runs actionlint over all workflows', ['run: python3 scripts/install-actionlint.py run', 'workflows_directory.glob("*.yml")', 'shell=False']), ('combined', 'all', 'Python-gated plugin matrix is emitted', ['Emit Python-gated plugin matrix', 'run: python3 scripts/emit-plugin-matrix.py', 'PLUGINS = ("speckit-pro",)']), ('workflow', 'all', 'workflow_dispatch trigger is defined', ['workflow_dispatch:']), ('workflow', 'all', 'dispatched PR checks identify the PR number', ['run-name: "PR Checks #', 'inputs.pr_number']), ('workflow', 'all', 'workflow_dispatch accepts PR check inputs', ['pr_number:', 'pr_title:', 'base_ref:']), ('workflow', 'all', 'detect supports dispatched release PR checks', ["github.event_name == 'workflow_dispatch' || github.event.pull_request.draft == false", "github.event_name == 'pull_request' && github.base_ref || inputs.base_ref"]), ('workflow', 'all', 'title validation supports dispatched release PR checks', ["github.event_name == 'pull_request' && github.event.pull_request.title || inputs.pr_title"]), ('workflow', 'all', 'sentinel depends on detect, test, and artifact-consistency jobs', ['needs: [detect, test, artifact-consistency]']), ('workflow', 'all', 'sentinel checks the artifact-consistency result', ['ARTIFACT_RESULT: ${{ needs.artifact-consistency.result }}', 'run: python3 scripts/check-pr-workflow-results.py']), ('workflow', 'all', 'sentinel runs if: always()', ['if: always()']), ('workflow', 'all', 'sentinel has only checkout read permission', ['validate-plugins:', 'contents: read']), ('workflow', 'absent', 'latest jq job is deferred', ['test-latest-jq:', 'latest_jq_result']), ('workflow', 'all', 'test job dispatches runner toolchain gate', ['run-toolchain-preflight.json', 'PYTHONPATH="${PLUGIN}" python3 -m speckit_pro_runner']), ('workflow', 'all', 'test job dispatches runner default suite gate', ['run-default-suite.json', 'PYTHONPATH="${PLUGIN}" python3 -m speckit_pro_runner']), ('workflow', 'all', 'docs validation dispatches runner toolchain preflight', ['Report docs toolchain', 'run-toolchain-preflight-docs.json']), ('workflow', 'absent', 'docs validation does not dispatch bash toolchain check', ['bash tests/speckit-pro/check-toolchain.sh --mode docs']), ('combined', 'all', 'sentinel checks detect_result for failure', ['DETECT_RESULT: ${{ needs.detect.result }}', 'detect_result in {"failure", "cancelled"}']), ('combined', 'all', 'sentinel checks test_result for success or skipped', ['TEST_RESULT: ${{ needs.test.result }}', 'test_result not in {"success", "skipped"}']), ('combined', 'all', 'sentinel exits 0 on success or skipped', ['Plugin tests passed or were skipped', 'artifact_result not in {"success", "skipped"}']), ('combined', 'all', 'sentinel exits 1 on detect failure', ['"failure"']), ('combined', 'all', 'sentinel exits 1 on detect cancellation', ['"cancelled"'])]
CONTAINER_JOBS = ('changes', 'linux-amd64-preflight', 'linux-arm64-preflight', 'windows-availability', 'windows-x64-smoke', 'windows-arm64-smoke', 'linux-amd64', 'linux-arm64')
LINUX_REQUESTS = ('run-toolchain-preflight.json', 'run-default-suite.json', 'repository-bash-confinement/requests/repo-bash-confinement.json', 'installed-plugin-release/requests/runner-invocation.json', 'installed-plugin-release/requests/active-runtime-guard.json', 'installed-plugin-release/requests/payload-completeness.json', 'installed-plugin-release/requests/release-readiness.json')
EXPECTED_PERMISSIONS = {'changes': 'contents: read', 'linux-amd64-preflight': 'contents: read', 'linux-arm64-preflight': 'contents: read', 'windows-availability': 'contents: read', 'windows-x64-smoke': 'contents: read', 'windows-arm64-smoke': 'contents: read', 'linux-amd64': 'contents: read', 'linux-arm64': 'contents: read'}
EXPECTED_UPLOAD_COUNTS = {'changes': 1, 'linux-amd64-preflight': 1, 'linux-arm64-preflight': 1, 'windows-availability': 2, 'windows-x64-smoke': 1, 'windows-arm64-smoke': 1, 'linux-amd64': 1, 'linux-arm64': 1}

def _job_block(content: str, job_id: str) -> str:
    match = re.search(f'(?ms)^  {re.escape(job_id)}:\\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:\\n|\\Z)', content)
    return match.group('body') if match else ''

def _yaml_valid(path: Path) -> bool:
    return yaml_syntax_sane(path.read_text(encoding='utf-8'))

def _required_sentinel_passes(changes: str, run_preflight: str, heavy: str) -> bool:
    if changes != 'success':
        return False
    if run_preflight == 'true':
        return heavy == 'success'
    return heavy == 'skipped'

class ValidatePrChecksSentinel(unittest.TestCase):

    def test_sentinel(self) -> None:
        with self.subTest(msg='pr-checks.yml exists'):
            self.assertTrue(validate_pr_checks_sentinel_WORKFLOW_FILE.is_file(), f'file not found: {validate_pr_checks_sentinel_WORKFLOW_FILE}')
        content = validate_pr_checks_sentinel_WORKFLOW_FILE.read_text(encoding='utf-8') if validate_pr_checks_sentinel_WORKFLOW_FILE.is_file() else ''
        helper_files = (ACTIONLINT_HELPER_FILE, DOCS_CLASSIFIER_FILE, RESULTS_HELPER_FILE, MATRIX_HELPER_FILE)
        helper_contents = {path: path.read_text(encoding='utf-8') if path.is_file() else '' for path in helper_files}
        sources = {'workflow': content, 'combined': '\n'.join((content, *helper_contents.values()))}
        with self.subTest(msg='validate-plugins job is defined'):
            self.assertIn('validate-plugins:', content)
        with self.subTest(msg='validate-plugins has name: validate-plugins'):
            self.assertIn('name: validate-plugins', content)
        with self.subTest(msg='history-sensitive plugin tests checkout repository history'):
            self.assertIn('fetch-depth: 0', _job_block(content, 'test'), 'expected history-sensitive plugin tests to checkout repository history')
        for source, kind, name, needles in CONTENT_CHECKS:
            with self.subTest(msg=name):
                selected_content = sources[source]
                if kind == 'all':
                    missing = [n for n in needles if n not in selected_content]
                    self.assertEqual([], missing, f'missing expected content: {missing}')
                else:
                    present = [n for n in needles if n in selected_content]
                    self.assertEqual([], present, f'unexpected content present: {present}')
        with self.subTest(msg='all GitHub workflow files are valid YAML'):
            valid_nested_step = 'name: Valid\njobs:\n  probe:\n    runs-on: ubuntu-latest\n    steps:\n      - name: Probe\n        run: echo valid\n'
            under_indented_step = 'name: Invalid\njobs:\n  probe:\n    runs-on: ubuntu-latest\n    steps:\n      - name: Probe\n      run: echo invalid\n'
            malformed = 'name: Invalid\njobs:\n  probe:\n    runs-on: [ubuntu-latest\n'
            self.assertTrue(yaml_syntax_sane(valid_nested_step), 'stdlib YAML sanity check rejected a valid nested workflow step')
            self.assertFalse(yaml_syntax_sane(under_indented_step), 'stdlib YAML sanity check accepted an under-indented step child')
            self.assertFalse(yaml_syntax_sane(malformed), 'stdlib YAML sanity check accepted an unterminated flow sequence')
            failures = [p.name for p in sorted(WORKFLOWS_DIR.glob('*.yml')) if not _yaml_valid(p)]
            self.assertEqual([], failures, f'GitHub workflow YAML syntax validation failed for: {failures}')
            missing_helpers = [str(path.relative_to(REPO_ROOT)) for path in helper_files if not path.is_file()]
            self.assertEqual([], missing_helpers, f'PR Checks helper files are missing: {missing_helpers}')
            for path, helper_content in helper_contents.items():
                compile(helper_content, str(path), 'exec')
                self.assertNotIn('shell=True', helper_content)
            self.assertIn('run: PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py --check', content)
            self.assertIn('run: python3 scripts/classify-docs-validation.py', content)
            self.assertNotRegex(content, '(?m)^\\s*run:\\s*[|>]\\s*$')
            self.assertNotRegex(content, '(?mi)^\\s*shell:\\s*(?:sh|bash|zsh|pwsh|powershell)\\s*$')
            self.assertNotRegex(content, '(?i)(?:^|[\\s\\"\'=])[^\\s\\"\']+\\.(?:sh|bash|zsh)\\b')
            direct_jq = re.compile('(?<![\\w-])jq(?![\\w-])')
            self.assertNotRegex(content, direct_jq)
            self.assertIsNone(direct_jq.search('gh pr view 123 --jq .title'))
            self.assertIsNotNone(direct_jq.search('jq -r .title result.json'))
            run_commands = re.findall('(?m)^\\s+run:\\s*([^\\n]+)$', content)
            self.assertTrue(run_commands)
            for command in run_commands:
                for shell_token in ('|', '&', ';', '<<', '>', '$(', '<(', '`', '*'):
                    self.assertNotIn(shell_token, command, f'shell logic in run command: {command}')
                match = re.match('^(?:[A-Z_][A-Z0-9_]*=(?:\\"[^\\"]*\\"|\'[^\']*\'|\\S+)\\s+)*(?P<executable>\\S+)', command)
                self.assertIsNotNone(match, f'unable to classify run command: {command}')
                executable = match.group('executable') if match else ''
                self.assertIn(executable, {'python', 'python3', 'node', 'pnpm', 'corepack'}, f'run command is not a thin Python/Node/pnpm dispatch: {command}')
            sentinel_block = _job_block(content, 'validate-plugins')
            self.assertRegex(sentinel_block, '(?m)^    permissions:\\n      contents: read$')
            self.assertIn('persist-credentials: false', sentinel_block)
            actionlint_content = helper_contents[ACTIONLINT_HELPER_FILE]
            self.assertNotIn('extractall(', actionlint_content)
            self.assertNotIn('archive.extract(', actionlint_content)
            self.assertIn('archive.extractfile(member)', actionlint_content)
            self.assertIn('sorted_workflow_files', actionlint_content)
            self.assertIn('shell=False', actionlint_content)
            docs_content = helper_contents[DOCS_CLASSIFIER_FILE]
            self.assertIn('["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"]', docs_content)
            for output_name in ('should_validate_docs', 'validation_mode', 'rendered_docs', 'generated_reference', 'docs_contract'):
                self.assertIn(output_name, docs_content)
            self.assertNotIn('git add -A', content)
            self.assertNotIn('sha256sum', content)
            self.assertNotIn('curl ', content)
            self.assertNotIn('tar ', content)

    def test_container_preflight(self) -> None:
        with self.subTest(msg='container-preflight.yml exists'):
            self.assertTrue(CONTAINER_WORKFLOW_FILE.is_file(), f'file not found: {CONTAINER_WORKFLOW_FILE}')
        content = CONTAINER_WORKFLOW_FILE.read_text(encoding='utf-8') if CONTAINER_WORKFLOW_FILE.is_file() else ''
        dispatch_content = CONTAINER_DISPATCH_HELPER_FILE.read_text(encoding='utf-8') if CONTAINER_DISPATCH_HELPER_FILE.is_file() else ''
        trigger_block = content.split('permissions:', 1)[0]
        with self.subTest(msg='container preflight always reports on pull requests'):
            self.assertIn('pull_request:', trigger_block)
            self.assertNotIn('paths:', trigger_block)
        with self.subTest(msg='container preflight supports manual dispatch'):
            self.assertIn('workflow_dispatch:', trigger_block)
        with self.subTest(msg='container preflight has workflow permissions empty'):
            self.assertRegex(content, '(?m)^permissions: \\{\\}$')
        with self.subTest(msg='change detector owns the heavy preflight decision'):
            block = _job_block(content, 'changes')
            self.assertIn('run_preflight:', block)
            self.assertIn('steps.changes.outputs.run_preflight', block)
            self.assertIn('fetch-depth: 0', block)
            self.assertIn('persist-credentials: false', block)
            self.assertIn('PREFLIGHT_OPERATION: detect-changes', block)
            self.assertIn('shell: python', block)
            self.assertIn(CONTAINER_DISPATCH, block)
            self.assertTrue(CONTAINER_DISPATCH_HELPER_FILE.is_file(), f'file not found: {CONTAINER_DISPATCH_HELPER_FILE}')
            compile(dispatch_content, str(CONTAINER_DISPATCH_HELPER_FILE), 'exec')
            self.assertIn('["merge-base", base_sha, head_sha]', dispatch_content)
            self.assertIn('["diff", "--no-renames", "--name-only", merge_base, head_sha]', dispatch_content)
            self.assertIn('merge-base.txt', dispatch_content)
            for path in ('speckit-pro/speckit_pro_runner/', 'tests/speckit-pro/', '.github/workflows/'):
                self.assertIn(path, dispatch_content)
        with self.subTest(msg='Linux amd64 heavy preflight is job-level conditional'):
            block = _job_block(content, 'linux-amd64-preflight')
            self.assertIn("needs.changes.outputs.run_preflight == 'true'", block)
            self.assertIn('container:', block)
            self.assertIn(f'image: {CONTAINER_IMAGE_PIN}', block)
            self.assertIn('runs-on: ubuntu-24.04', block)
            self.assertIn('4d216ad3beb5b697c4049071c82fc375acb8abad', content)
            self.assertIn('the job userland is Debian', content)
            self.assertNotRegex(block, SETUP_PYTHON_PIN_RE)
            self.assertNotIn('apt-get', block)
            self.assertIn('id: checkout', block)
            self.assertIn('fetch-depth: 0', block)
            self.assertIn('persist-credentials: false', block)
            self.assertIn("if: steps.checkout.outcome == 'success'", block)
            self.assertIn('PREFLIGHT_OPERATION: linux-gates', block)
            self.assertIn('PREFLIGHT_ROLE: linux-amd64', block)
            self.assertIn('shell: python', block)
            self.assertIn(CONTAINER_DISPATCH, block)
            self.assertIn('EVIDENCE_DIR: /tmp/container-preflight-linux-amd64', block)
            self.assertIn('path: ${{ env.EVIDENCE_DIR }}', block)
            self.assertNotIn('RUNNER_TEMP', block)
            self.assertNotIn('${{ runner.temp }}', block)
            self.assertNotIn('- name: Checkout repository\n        if: always()', block)
        with self.subTest(msg='Linux arm64 heavy preflight is job-level conditional'):
            block = _job_block(content, 'linux-arm64-preflight')
            self.assertIn("needs.changes.outputs.run_preflight == 'true'", block)
            self.assertIn('runs-on: ubuntu-24.04-arm', block)
            self.assertIn('container:', block)
            self.assertIn(f'image: {CONTAINER_IMAGE_PIN}', block)
            self.assertNotRegex(block, SETUP_PYTHON_PIN_RE)
            self.assertNotIn('apt-get', block)
            self.assertIn('id: checkout', block)
            self.assertIn('fetch-depth: 0', block)
            self.assertIn('persist-credentials: false', block)
            self.assertIn("if: steps.checkout.outcome == 'success'", block)
            self.assertIn('PREFLIGHT_OPERATION: linux-gates', block)
            self.assertIn('PREFLIGHT_ROLE: linux-arm64', block)
            self.assertIn('shell: python', block)
            self.assertIn(CONTAINER_DISPATCH, block)
            self.assertIn('EVIDENCE_DIR: /tmp/container-preflight-linux-arm64', block)
            self.assertIn('path: ${{ env.EVIDENCE_DIR }}', block)
            self.assertNotIn('RUNNER_TEMP', block)
            self.assertNotIn('${{ runner.temp }}', block)
            self.assertNotIn('- name: Checkout repository\n        if: always()', block)
        with self.subTest(msg='Linux amd64 runs current Python gate entrypoints'):
            block = _job_block(content, 'linux-amd64-preflight')
            self.assertIn('PREFLIGHT_ROLE: linux-amd64', block)
            self.assertIn('[sys.executable, "-m", "speckit_pro_runner"]', dispatch_content)
            for request in LINUX_REQUESTS:
                self.assertIn(request, dispatch_content)
            request_positions = [dispatch_content.index(request) for request in LINUX_REQUESTS]
            self.assertEqual(request_positions, sorted(request_positions))
            self.assertIn('child_env["SPECKIT_SKIP_TOOLCHAIN_CHECK"] = "1"', dispatch_content)
        with self.subTest(msg='Linux arm64 runs current Python gate entrypoints'):
            block = _job_block(content, 'linux-arm64-preflight')
            self.assertIn('PREFLIGHT_ROLE: linux-arm64', block)
            self.assertIn('[sys.executable, "-m", "speckit_pro_runner"]', dispatch_content)
            for request in LINUX_REQUESTS:
                self.assertIn(request, dispatch_content)
            self.assertIn('"container_userland": "Debian Bookworm"', dispatch_content)
        with self.subTest(msg='Linux amd64 required check is an always sentinel'):
            block = _job_block(content, 'linux-amd64')
            self.assertIn('name: container-preflight-linux-amd64', block)
            self.assertIn('if: always()', block)
            self.assertIn('needs.linux-amd64-preflight.result', block)
            self.assertIn('PREFLIGHT_OPERATION: sentinel', block)
            self.assertIn('PREFLIGHT_ROLE: linux-amd64-required', block)
            self.assertIn('shell: python', block)
            self.assertIn(CONTAINER_DISPATCH, block)
            for condition in ('if changes_result != "success":', 'if run_preflight == "true":', 'return heavy_result == "success"', 'return run_preflight == "false" and heavy_result == "skipped"'):
                self.assertIn(condition, dispatch_content)
            self.assertEqual([True, False, False, True, False, False, False], [_required_sentinel_passes('success', 'true', 'success'), _required_sentinel_passes('success', 'true', 'failure'), _required_sentinel_passes('success', 'true', 'cancelled'), _required_sentinel_passes('success', 'false', 'skipped'), _required_sentinel_passes('success', 'false', 'success'), _required_sentinel_passes('failure', 'true', 'success'), _required_sentinel_passes('cancelled', 'false', 'skipped')])
        with self.subTest(msg='Linux arm64 required check is an always sentinel'):
            block = _job_block(content, 'linux-arm64')
            self.assertIn('name: container-preflight-linux-arm64', block)
            self.assertIn('if: always()', block)
            self.assertIn('needs.linux-arm64-preflight.result', block)
            self.assertIn('PREFLIGHT_OPERATION: sentinel', block)
            self.assertIn('PREFLIGHT_ROLE: linux-arm64-required', block)
            self.assertIn('shell: python', block)
            self.assertIn(CONTAINER_DISPATCH, block)
            self.assertIn('"verdict": "pass" if passed else "fail"', dispatch_content)
        with self.subTest(msg='Windows availability is configured on an Ubuntu control job'):
            block = _job_block(content, 'windows-availability')
            self.assertIn('runs-on: ubuntu-latest', block)
            self.assertIn('XPLAT_WINDOWS_X64_ENABLED', block)
            self.assertIn('XPLAT_WINDOWS_ARM64_ENABLED', block)
            self.assertNotIn('XPLAT_WINDOWS_ARM64_AVAILABLE', block)
            self.assertRegex(block, SETUP_PYTHON_PIN_RE)
            self.assertIn('persist-credentials: false', block)
            self.assertIn('PREFLIGHT_OPERATION: windows-availability', block)
            self.assertIn('shell: python', block)
            self.assertIn(CONTAINER_DISPATCH, block)
            self.assertEqual(1, trigger_block.count('default: true'))
            self.assertEqual(1, trigger_block.count('default: false'))
            for label in ('windows-2025', 'windows-11-arm'):
                self.assertIn(f'"runner_label": "{label}"', dispatch_content)
            self.assertIn('"hosted_label_status": "stable"', dispatch_content)
            self.assertIn('"hosted_label_status": "public_preview"', dispatch_content)
            self.assertIn('"available": True', dispatch_content)
            self.assertIn('x64_source = "stable_label_default"', dispatch_content)
            self.assertIn('arm64_source = "public_preview_default"', dispatch_content)
            self.assertIn('arm64_enabled = "false"', dispatch_content)
            self.assertEqual(2, dispatch_content.count('= "repository_variable_disable"'))
            self.assertIn('"x64_enabled": x64_enabled', dispatch_content)
            self.assertIn('"arm64_enabled": arm64_enabled', dispatch_content)
            self.assertLess(dispatch_content.index('if event_name == "workflow_dispatch":'), dispatch_content.index('if repo_x64 == "false":'))
            self.assertIn('windows_x64_enabled', trigger_block)
            self.assertIn('windows_arm64_enabled', trigger_block)
        with self.subTest(msg='Windows x64 smoke is advisory and conditionally queued'):
            block = _job_block(content, 'windows-x64-smoke')
            self.assertIn('continue-on-error: true', block)
            self.assertIn("needs.windows-availability.outputs.x64_enabled == 'true'", block)
            self.assertIn('runs-on: windows-2025', block)
            self.assertRegex(block, SETUP_PYTHON_PIN_RE)
            self.assertIn('python-version: ${{ env.HOSTED_PYTHON_VERSION }}', block)
            self.assertIn('id: checkout', block)
            self.assertIn('persist-credentials: false', block)
            self.assertIn("if: always() && steps.checkout.outcome == 'success'", block)
            self.assertIn('PREFLIGHT_OPERATION: windows-smoke', block)
            self.assertIn('PREFLIGHT_ROLE: windows-x64', block)
            self.assertIn('shell: python', block)
            self.assertIn(CONTAINER_DISPATCH, block)
            self.assertNotIn('- name: Checkout repository\n        if: always()', block)
        with self.subTest(msg='Windows ARM64 smoke is advisory and conditionally queued'):
            block = _job_block(content, 'windows-arm64-smoke')
            self.assertIn('continue-on-error: true', block)
            self.assertIn("needs.windows-availability.outputs.arm64_enabled == 'true'", block)
            self.assertIn('runs-on: windows-11-arm', block)
            self.assertRegex(block, SETUP_PYTHON_PIN_RE)
            self.assertIn('python-version: ${{ env.HOSTED_PYTHON_VERSION }}', block)
            self.assertIn('id: checkout', block)
            self.assertIn('persist-credentials: false', block)
            self.assertIn("if: always() && steps.checkout.outcome == 'success'", block)
            self.assertIn('PREFLIGHT_OPERATION: windows-smoke', block)
            self.assertIn('PREFLIGHT_ROLE: windows-arm64', block)
            self.assertIn('shell: python', block)
            self.assertIn(CONTAINER_DISPATCH, block)
            self.assertNotIn('- name: Checkout repository\n        if: always()', block)
        with self.subTest(msg='Windows smoke runs interpreter discovery runtime-info and preflight'):
            self.assertTrue(WINDOWS_PREFLIGHT_HELPER_FILE.is_file(), f'file not found: {WINDOWS_PREFLIGHT_HELPER_FILE}')
            helper_content = WINDOWS_PREFLIGHT_HELPER_FILE.read_text(encoding='utf-8') if WINDOWS_PREFLIGHT_HELPER_FILE.is_file() else ''
            compile(helper_content, str(WINDOWS_PREFLIGHT_HELPER_FILE), 'exec')
            for expected in ('"operation": "runtime-info"', '"operation": "preflight"', 'runtime-info.json', 'preflight.json', 'specify-version.txt', 'specify_version_compatible', 'runtime_info_diagnostics', 'preflight_diagnostics', 'preflight_metadata_status', 'runner_metadata_mismatch', 'IMMUTABLE_SPEC_KIT_REF_RE', 'f"pipx=={args.pipx_version}"', 'shell=False'):
                self.assertIn(expected, helper_content)
            self.assertIn(HOSTED_PYTHON_VERSION, content)
            self.assertRegex(content, SETUP_PYTHON_PIN_RE)
            self.assertIn('3.13.14-27320626148', content)
            self.assertIn('PIPX_VERSION: "1.15.0"', content)
            self.assertIn(SPEC_KIT_VERSION_PIN, content)
            self.assertIn(SPEC_KIT_REF_PIN, content)
            self.assertNotIn('spec-kit.git@v0.8.13', content)
            for job_id in ('windows-x64-smoke', 'windows-arm64-smoke'):
                block = _job_block(content, job_id)
                self.assertRegex(block, SETUP_PYTHON_PIN_RE)
                self.assertNotIn('PREFLIGHT_INTERPRETER_CANDIDATE', block)
                self.assertIn('PREFLIGHT_OPERATION: windows-smoke', block)
                self.assertIn(CONTAINER_DISPATCH, block)
                self.assertNotIn('-m pipx', block)
                self.assertNotIn('operation = "runtime-info"', block)
                self.assertNotIn('operation = "preflight"', block)
                self.assertNotIn('specifyCommand', block)
            candidates = ('"py -V:3"', '"py -3"', '"python"', '"python3"')
            candidate_positions = [dispatch_content.index(candidate) for candidate in candidates]
            self.assertEqual(candidate_positions, sorted(candidate_positions))
            self.assertIn('interpreter-probes.json', dispatch_content)
            self.assertIn('architecture_emulated', dispatch_content)
            self.assertIn('child_env["PREFLIGHT_INTERPRETER_CANDIDATE"] = selected', dispatch_content)
            for expected in ('run-hosted-windows-preflight.py', '"--pipx-version"', '"--spec-kit-version"', '"--spec-kit-ref"'):
                self.assertIn(expected, dispatch_content)
        with self.subTest(msg='every container preflight job declares minimal permissions'):
            failures = []
            for job_id, expected in EXPECTED_PERMISSIONS.items():
                block = _job_block(content, job_id)
                if expected == '{}':
                    valid = re.search('(?m)^    permissions: \\{\\}$', block) is not None
                else:
                    valid = re.search(f'(?m)^    permissions:\\n      {re.escape(expected)}$', block) is not None
                if not valid or re.search('(?m)^\\s+[A-Za-z-]+: write$', block):
                    failures.append(job_id)
            self.assertEqual([], failures, f'jobs with incorrect permissions: {failures}')
        with self.subTest(msg='every container preflight job uploads evidence with always semantics'):
            failures = []
            artifact_names = []
            for job_id, expected_count in EXPECTED_UPLOAD_COUNTS.items():
                block = _job_block(content, job_id)
                upload_steps = [step for step in re.split('(?m)(?=^      - name: )', block) if UPLOAD_ARTIFACT_PIN in step]
                artifact_names.extend((match.group(1) for step in upload_steps if (match := re.search('(?m)^\\s+name: (container-preflight-[^\\n]+)$', step))))
                if len(upload_steps) != expected_count or any(('if: always()' not in step or 'continue-on-error: true' not in step or 'if-no-files-found: error' not in step or (UNIQUE_ARTIFACT_SUFFIX not in step) or ('overwrite: true' in step) for step in upload_steps)):
                    failures.append(job_id)
            self.assertEqual([], failures, f'jobs with incorrect evidence uploads: {failures}')
            self.assertEqual(sum(EXPECTED_UPLOAD_COUNTS.values()), len(artifact_names))
            self.assertEqual(len(artifact_names), len(set(artifact_names)))
        with self.subTest(msg='evidence uploads cannot mask or flip role verdicts'):
            upload_count = sum(EXPECTED_UPLOAD_COUNTS.values())
            self.assertEqual(upload_count, content.count(f'uses: {UPLOAD_ARTIFACT_PIN}'))
            self.assertEqual(6, len(SETUP_PYTHON_PIN_RE.findall(content)))
            self.assertEqual(6, len(SETUP_PYTHON_COMMENTED_PIN_RE.findall(content)))
            self.assertEqual(2, content.count(f'image: {CONTAINER_IMAGE_PIN}'))
            action_refs = re.findall('(?m)^\\s+uses: ([^\\s]+)', content)
            self.assertTrue(action_refs)
            self.assertTrue(all((re.search('@[0-9a-f]{40}$', ref) for ref in action_refs)))
            self.assertEqual(upload_count + 2, content.count('continue-on-error: true'), 'only nine upload steps and two Windows advisory jobs may continue on error')
        with self.subTest(msg='container preflight dispatches no repo-local shell helper'):
            self.assertIsNone(re.search('(?i)(?:scripts|tests|speckit-pro)/[^\\s\\"\']+\\.(?:sh|bash|zsh|ps1|bat|cmd)\\b', content))
            self.assertNotRegex(content, '(?i)(?<![\\w-])jq(?![\\w-])')
            self.assertNotRegex(content, '(?m)^\\s*shell:\\s*(?:bash|pwsh)\\s*$')
            self.assertNotIn('apt-get', content)
            self.assertNotIn('run: |', content)
            self.assertNotIn('$(', content)
            self.assertEqual(len(CONTAINER_JOBS), content.count('shell: python'))
            self.assertEqual(len(CONTAINER_JOBS), content.count(CONTAINER_DISPATCH))
            self.assertIn('shell=False', dispatch_content)
            self.assertNotIn('shell=True', dispatch_content)
validate_release_workflow_WORKFLOW_FILE = REPO_ROOT / '.github' / 'workflows' / 'release.yml'
PR_CHECKS_WORKFLOW_FILE = REPO_ROOT / '.github' / 'workflows' / 'pr-checks.yml'
COMPOSER_FILE = REPO_ROOT / 'scripts' / 'compose-release-notes.py'
AUDIT_HELPER_FILE = REPO_ROOT / 'scripts' / 'audit-release-notes.py'
DISPATCH_HELPER_FILE = REPO_ROOT / 'scripts' / 'dispatch-release-pr-checks.py'
POLICY_FILE = REPO_ROOT / 'scripts' / 'release_note_policy.py'
REFRESH_HELPER_FILE = REPO_ROOT / 'scripts' / 'refresh-release-artifacts.py'
RESOLVER_FILE = REPO_ROOT / 'scripts' / 'resolve_release_prs.py'
RUNNER_REQUEST_HELPER_FILE = REPO_ROOT / 'scripts' / 'run-runner-requests.py'
SYNC_HELPER_FILE = REPO_ROOT / 'scripts' / 'sync_release_pr.py'
RELEASE_CONFIG_FILE = REPO_ROOT / 'release-please-config.json'
validate_release_workflow_CHECKOUT_PIN_RE = re.compile('actions/checkout@[0-9a-f]{40}')
UPLOAD_ARTIFACT_PIN_RE = re.compile('actions/upload-artifact@[0-9a-f]{40}')
DOWNLOAD_ARTIFACT_PIN_RE = re.compile('actions/download-artifact@[0-9a-f]{40}')
MAIN_PUSH_RE = re.compile('^\\s*git push(\\s|$).*(\\s|\\"|\'|:|/)main(\\s|\\"|\'|:|$)', re.MULTILINE)
RELEASE_NOTE_EVENTS = ('opened', 'reopened', 'synchronize', 'edited', 'labeled', 'unlabeled', 'ready_for_review')
RELEASE_PR_FOUND_CONDITION = "steps.release_prs.outputs.found == 'true'"
RELEASE_CREATED_CONDITION = "steps.release.outputs['speckit-pro--release_created'] == 'true'"
RUNNER_REQUEST_PREFIX = 'python3 scripts/run-runner-requests.py'
TEST_PAYLOAD_EVIDENCE_REQUEST = 'tests/speckit-pro/unit/fixtures/runner-gates/requests/test-payload-evidence.json'
INSTALLED_PLUGIN_RELEASE_REQUESTS = ('tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/runner-invocation.json', 'tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/active-runtime-guard.json', 'tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/payload-completeness.json', 'tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/release-readiness.json')

def _contains_all(text: str, needles: tuple[str, ...]) -> bool:
    return all((needle in text for needle in needles))

def _runner_request_command(request_files: tuple[str, ...]) -> str:
    return ' '.join((RUNNER_REQUEST_PREFIX, *request_files))

def _mapping_block(text: str, key: str, indent: int) -> str:
    """Return one indentation-delimited YAML mapping block."""
    prefix = ' ' * indent
    match = re.search(f'(?m)^{re.escape(prefix + key)}:\\s*$', text)
    if match is None:
        return ''
    end = len(text)
    for candidate in re.finditer(f'(?m)^{re.escape(prefix)}[A-Za-z0-9_-]+:\\s*', text[match.end():]):
        end = match.end() + candidate.start()
        break
    return text[match.start():end]

def _permission_map(job_block: str) -> dict[str, str]:
    permissions = _mapping_block(job_block, 'permissions', 4)
    return {match.group('name'): match.group('access') for match in re.finditer('(?m)^\\s{6}(?P<name>[a-z-]+):\\s*(?P<access>read|write|none)\\s*$', permissions)}

def _scalar_values(text: str, key: str, indent: int) -> list[str]:
    prefix = ' ' * indent
    return [match.group('value').strip() for match in re.finditer(f'(?m)^{re.escape(prefix + key)}:[ \\t]*(?P<value>[^\\r\\n]*)$', text)]

def _named_step_block(job_block: str, name: str) -> str:
    """Return one named workflow step, including its nested mappings."""
    match = re.search(f'(?m)^      - name:\\s*{re.escape(name)}\\s*$', job_block)
    if match is None:
        return ''
    next_step = re.search('(?m)^      - ', job_block[match.end():])
    end = len(job_block) if next_step is None else match.end() + next_step.start()
    return job_block[match.start():end]

def _python_function_block(text: str, name: str) -> str:
    """Return one top-level Python function for structural contract checks."""
    match = re.search(f'(?m)^def {re.escape(name)}\\(', text)
    if match is None:
        return ''
    next_symbol = re.search('(?m)^(?:def|class) [A-Za-z_]', text[match.end():])
    end = len(text) if next_symbol is None else match.end() + next_symbol.start()
    return text[match.start():end]

def _inline_list(value: str) -> tuple[str, ...]:
    """Parse the workflow's intentionally simple inline event list."""
    if not value.startswith('[') or not value.endswith(']'):
        return ()
    return tuple((item.strip() for item in value[1:-1].split(',') if item.strip()))

def _run_commands(text: str) -> list[str]:
    return [match.group('command').strip() for match in re.finditer('(?m)^\\s+run:\\s*(?P<command>[^\\r\\n]*)$', text)]

def _is_thin_direct_dispatch(command: str) -> bool:
    """Accept one direct tool invocation and reject shell composition."""
    if not command or command in {'|', '>', '|-', '>-'}:
        return False
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=';&|<>')
        lexer.whitespace_split = True
        lexer.commenters = ''
        tokens = list(lexer)
    except ValueError:
        return False
    if not tokens or tokens[0] not in {'corepack', 'gh', 'node', 'pnpm', 'python3'}:
        return False
    if any((token and set(token) <= set(';&|<>') for token in tokens)):
        return False
    if any(('$(' in token or '`' in token for token in tokens)):
        return False
    return not any((token.endswith('.sh') for token in tokens))

class ValidateReleaseWorkflow(unittest.TestCase):

    def test_release_workflow(self) -> None:
        with self.subTest(msg='release.yml exists'):
            self.assertTrue(validate_release_workflow_WORKFLOW_FILE.is_file(), f'file not found: {validate_release_workflow_WORKFLOW_FILE}')
        content = validate_release_workflow_WORKFLOW_FILE.read_text(encoding='utf-8') if validate_release_workflow_WORKFLOW_FILE.is_file() else ''
        pr_checks_content = PR_CHECKS_WORKFLOW_FILE.read_text(encoding='utf-8') if PR_CHECKS_WORKFLOW_FILE.is_file() else ''
        composer_content = COMPOSER_FILE.read_text(encoding='utf-8') if COMPOSER_FILE.is_file() else ''
        audit_helper_content = AUDIT_HELPER_FILE.read_text(encoding='utf-8') if AUDIT_HELPER_FILE.is_file() else ''
        dispatch_helper_content = DISPATCH_HELPER_FILE.read_text(encoding='utf-8') if DISPATCH_HELPER_FILE.is_file() else ''
        policy_content = POLICY_FILE.read_text(encoding='utf-8') if POLICY_FILE.is_file() else ''
        refresh_helper_content = REFRESH_HELPER_FILE.read_text(encoding='utf-8') if REFRESH_HELPER_FILE.is_file() else ''
        resolver_content = RESOLVER_FILE.read_text(encoding='utf-8') if RESOLVER_FILE.is_file() else ''
        runner_request_helper_content = RUNNER_REQUEST_HELPER_FILE.read_text(encoding='utf-8') if RUNNER_REQUEST_HELPER_FILE.is_file() else ''
        sync_helper_content = SYNC_HELPER_FILE.read_text(encoding='utf-8') if SYNC_HELPER_FILE.is_file() else ''
        with self.subTest(msg='release workflow uses release-please'):
            self.assertIn('googleapis/release-please-action@v5', content)
        with self.subTest(msg='release workflow pins checkout actions'):
            self.assertEqual(4, len(validate_release_workflow_CHECKOUT_PIN_RE.findall(content)), 'release workflow pinned checkout count')
        release_job = _mapping_block(content, 'release', 2)
        capture_job = _mapping_block(content, 'capture-release-note-inputs', 2)
        composer_job = _mapping_block(content, 'compose-release-notes', 2)
        capture_step = _named_step_block(capture_job, 'Capture complete immutable release inputs')
        snapshot_upload_step = _named_step_block(capture_job, 'Upload immutable release input snapshot')
        snapshot_download_step = _named_step_block(composer_job, 'Download immutable release input snapshot')
        compose_step = _named_step_block(composer_job, 'Compose and verify public release notes')
        audit_upload_step = _named_step_block(composer_job, 'Upload immutable release note audit')
        audit_record_step = _named_step_block(composer_job, 'Record immutable audit artifact')
        with self.subTest(msg='release workflow can dispatch PR checks'):
            self.assertTrue(_contains_all(content + dispatch_helper_content, ('actions: write', 'scripts/dispatch-release-pr-checks.py', '"gh",', '"workflow",', '"run",', '"pr-checks.yml",', '"--ref",', 'f"pr_number={release_pr[\'number\']}"', 'f"pr_title={release_pr[\'title\']}"', '"base_ref=main",', 'check=True', 'shell=False')), 'expected release workflow to dispatch PR Checks for release-please PR branches')
        with self.subTest(msg='release workflow resolves new or unchanged release PRs for payload sync'):
            self.assertTrue(_contains_all(content, ('RELEASE_PRS: ${{ steps.release.outputs.prs }}', 'scripts/resolve_release_prs.py', 'RELEASE_PRS: ${{ steps.release_prs.outputs.prs }}', "steps.release_prs.outputs.found == 'true'", 'scripts/dispatch-release-pr-checks.py')), 'expected release workflow to normalize release-please output and reconcile unchanged open release PRs')
            self.assertTrue(_contains_all(dispatch_helper_content, ('item.get("headBranchName") or item.get("headRefName")', 'release PR resolver returned no metadata', 'parse_release_prs')))
        with self.subTest(msg='release PR resolver discovers unchanged open Release Please branches'):
            self.assertTrue(RESOLVER_FILE.is_file() and _contains_all(resolver_content, ('"gh",', '"pr",', '"list",', 'release-please--branches--', 'headRefName')), 'expected resolver fallback to list and filter existing open Release Please PRs')
        with self.subTest(msg='release reconciliation is not gated only on prs_created'):
            self.assertNotIn("steps.release.outputs.prs_created == 'true'", content, 'unchanged open release PRs must reconcile even when release-please reports prs_created=false')
        with self.subTest(msg='release workflow does not depend on pending release labels for payload sync'):
            self.assertNotIn('--label "autorelease: pending"', content, 'release PR payload sync must not depend on a just-created label query')
        with self.subTest(msg='release workflow validates release PR readiness before dispatch'):
            self.assertTrue(_contains_all(content, ('Validate installed-plugin release gates', "steps.release_prs.outputs.found == 'true'", 'RELEASE_PRS: ${{ steps.release_prs.outputs.prs }}', 'scripts/run-runner-requests.py', 'release-readiness.json', 'Dispatch PR Checks for release PRs')), 'expected release workflow to validate release PR readiness before dispatching PR Checks')
            self.assertTrue(RUNNER_REQUEST_HELPER_FILE.is_file() and _contains_all(runner_request_helper_content, ('[sys.executable, "-m", "speckit_pro_runner"]', 'input=request_bytes', 'shell=False', 'if completed.returncode != 0:')))
            runner_steps = (('Validate installed-plugin release gates', RELEASE_PR_FOUND_CONDITION, INSTALLED_PLUGIN_RELEASE_REQUESTS), ('Verify generated test payload evidence', RELEASE_CREATED_CONDITION, (TEST_PAYLOAD_EVIDENCE_REQUEST,)), ('Validate post-release installed-plugin gates', RELEASE_CREATED_CONDITION, INSTALLED_PLUGIN_RELEASE_REQUESTS))
            expected_runner_commands: list[str] = []
            for step_name, condition, request_files in runner_steps:
                step = _named_step_block(release_job, step_name)
                expected_command = _runner_request_command(request_files)
                self.assertTrue(step, f'missing release workflow step: {step_name}')
                self.assertEqual([condition], _scalar_values(step, 'if', 8))
                self.assertEqual([expected_command], _scalar_values(step, 'run', 8))
                expected_runner_commands.append(expected_command)
            actual_runner_commands = [command for command in _run_commands(release_job) if command.startswith(RUNNER_REQUEST_PREFIX)]
            self.assertEqual(expected_runner_commands, actual_runner_commands)
            ordered_pre_release_steps = ('Set up Node', 'Sync generated artifacts onto the release PR', 'Validate installed-plugin release gates', 'Dispatch PR Checks for release PRs')
            step_positions = [release_job.find(f'      - name: {step_name}') for step_name in ordered_pre_release_steps]
            self.assertNotIn(-1, step_positions)
            self.assertEqual(sorted(step_positions), step_positions)
            for step_name in ordered_pre_release_steps:
                self.assertEqual([RELEASE_PR_FOUND_CONDITION], _scalar_values(_named_step_block(release_job, step_name), 'if', 8))
        with self.subTest(msg='release workflow verifies generated test payload evidence'):
            self.assertIn('test-payload-evidence.json', content)
        with self.subTest(msg='release workflow syncs generated artifacts on the release PR'):
            self.assertTrue('scripts/sync_release_pr.py' in content and 'Sync generated artifacts onto the release PR' in content and ('bash scripts/sync-marketplace-versions.sh' not in content) and SYNC_HELPER_FILE.is_file() and ('scripts/refresh-release-artifacts.py' in sync_helper_content), 'expected release workflow to refresh generated artifacts via the Python refresh script on the release PR')
        with self.subTest(msg='release workflow sync checks out the release PR branch with the release token'):
            self.assertTrue('token: ${{ secrets.RELEASE_PLEASE_TOKEN || github.token }}' in content and 'scripts/sync_release_pr.py' in content and ('["git", "checkout", "-B", branch, remote_branch_sha]' in sync_helper_content), 'expected release workflow to check out the release PR branch using the release token')
        with self.subTest(msg='release workflow merges current main before regenerating an existing release PR'):
            merge_line = sync_helper_content.find('["git", "merge", "--no-edit", base_sha]')
            refresh_line = sync_helper_content.find('[sys.executable, "scripts/refresh-release-artifacts.py"]')
            self.assertTrue('BASE_REF: main' in content and merge_line >= 0 and (refresh_line >= 0) and (merge_line < refresh_line), 'expected release branch to merge current main before artifact refresh')
        with self.subTest(msg='release workflow pushes main-only reconciliation changes'):
            self.assertTrue(_contains_all(sync_helper_content, ('["git", "rev-parse", "FETCH_HEAD"]', 'if head_sha == remote_branch_sha:', '["git", "push", "origin", f"HEAD:{branch}"]')), 'expected workflow to push when merging main changed the release branch even if generated files were already current')
        with self.subTest(msg='release workflow guards the artifact sync commit with a dirty check'):
            self.assertTrue('["git", "status", "--porcelain"]' in sync_helper_content and 'chore(release): sync generated artifacts for release' in sync_helper_content, 'expected release workflow to commit the artifact sync only when the tree is dirty')
        with self.subTest(msg='release workflow regenerates the docs reference on sync'):
            self.assertIn('pnpm --dir docs-site reference:generate', content)
        with self.subTest(msg='release workflow verifies release artifacts are consistent after publishing'):
            self.assertTrue(_contains_all(content + refresh_helper_content, ('Verify release artifacts are consistent', 'scripts/refresh-release-artifacts.py --check', 'def check_release_artifacts(', 'tempfile.TemporaryDirectory', 'shutil.copytree', 'shell=False', 'Recovery Scenario 1')), 'expected a non-mutating release artifact check after publishing')
        with self.subTest(msg='release workflow opens NO follow-up payload/marketplace sync PR'):
            self.assertFalse('gh pr create --base main' in content or 'release/sync-speckit-pro-v' in content, "release workflow must NOT open a follow-up sync PR; the release PR's payload-sync step already commits dist, marketplace versions, and the docs reference")
        with self.subTest(msg='release workflow sync commit does not skip required PR checks'):
            self.assertNotIn('[skip ci]', content)
        with self.subTest(msg='release workflow does not direct-push generated sync changes to main'):
            self.assertIsNone(MAIN_PUSH_RE.search(content), 'release workflow must not push generated sync changes directly to main')
        with self.subTest(msg='release workflow main-push regex catches common protected-branch pushes'):
            samples = ('git push origin main', 'git push origin HEAD:main', 'git push --force origin HEAD:main', 'git push origin refs/heads/main')
            missed = [sample for sample in samples if MAIN_PUSH_RE.search(sample) is None]
            self.assertEqual([], missed, f'main-push regex missed: {missed}')
        with self.subTest(msg='release note validation covers all seven pull request events'):
            pull_request_trigger = _mapping_block(pr_checks_content, 'pull_request', 2)
            event_values = _scalar_values(pull_request_trigger, 'types', 4)
            self.assertEqual(1, len(event_values), 'expected one pull_request event list')
            self.assertEqual(RELEASE_NOTE_EVENTS, _inline_list(event_values[0]))
        with self.subTest(msg='release workflow defaults permissions to none'):
            self.assertRegex(content, '(?m)^permissions:\\s*\\{\\}\\s*$')
        with self.subTest(msg='release job declares publishing permissions'):
            self.assertEqual({'actions': 'write', 'contents': 'write', 'pull-requests': 'write'}, _permission_map(release_job))
        with self.subTest(msg='release job exports raw component release inputs'):
            self.assertTrue(_contains_all(release_job, ("release_created: ${{ steps.release.outputs['speckit-pro--release_created'] }}", "tag_name: ${{ steps.release.outputs['speckit-pro--tag_name'] }}", "body: ${{ steps.release.outputs['speckit-pro--body'] }}")))
            outputs_block = _mapping_block(release_job, 'outputs', 4)
            self.assertNotIn('snapshot_', outputs_block)
        with self.subTest(msg='capture is an own read-only dependent job'):
            self.assertIn('capture-release-note-inputs:', capture_job)
            self.assertEqual(['release'], _scalar_values(capture_job, 'needs', 4))
            self.assertEqual(["${{ always() && needs.release.outputs.release_created == 'true' }}"], _scalar_values(capture_job, 'if', 4))
            self.assertEqual({'contents': 'read'}, _permission_map(capture_job))
            self.assertTrue(_contains_all(_mapping_block(capture_job, 'outputs', 4), ("snapshot_artifact_id: ${{ steps.upload_release_snapshot.outputs['artifact-id'] }}", "snapshot_artifact_digest: ${{ steps.upload_release_snapshot.outputs['artifact-digest'] }}", "snapshot_artifact_url: ${{ steps.upload_release_snapshot.outputs['artifact-url'] }}", 'snapshot_sha256: ${{ steps.capture_snapshot.outputs.snapshot_sha256 }}')))
            self.assertNotIn('RELEASE_PLEASE_TOKEN', capture_job)
            self.assertNotIn('actions: write', capture_job)
            self.assertNotIn('pull-requests: write', capture_job)
        with self.subTest(msg='capture uploads complete canonical Compare and PR inputs'):
            self.assertEqual(2, len(UPLOAD_ARTIFACT_PIN_RE.findall(content)))
            self.assertLess(capture_job.find('actions/checkout@'), capture_job.find('--capture-snapshot'))
            self.assertTrue(_contains_all(capture_step + snapshot_upload_step, ('GITHUB_TOKEN: ${{ github.token }}', 'GITHUB_REPOSITORY: ${{ github.repository }}', 'RELEASE_BODY: ${{ needs.release.outputs.body }}', 'RELEASE_TAG: ${{ needs.release.outputs.tag_name }}', 'python3 scripts/compose-release-notes.py --capture-snapshot ', '--snapshot-output release-note-snapshot.json', 'actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a', 'name: release-note-input-${{ github.run_id }}-${{ github.run_attempt }}', 'path: release-note-snapshot.json', 'if-no-files-found: error', 'retention-days: 90')))
            self.assertNotIn('overwrite: true', snapshot_upload_step)
            capture_function = _python_function_block(composer_content, 'capture_release_input_snapshot')
            canonical_function = _python_function_block(composer_content, 'canonical_snapshot_bytes')
            loader_function = _python_function_block(composer_content, 'load_release_input_snapshot')
            self.assertTrue(_contains_all(capture_function + canonical_function + loader_function, ('f"/repos/{client.repository}/compare/{base}...{head}"', 'f"/repos/{client.repository}/pulls/{commit.pr_number}"', '"body": body', '"labels": sorted(_label_names(pr))', '"release_body": raw_body', '"compare": compare', '"pulls": pulls', 'raw != canonical_snapshot_bytes(value)', 'digest != expected_sha256', 'set(pulls_value) != expected_pull_keys')))
        with self.subTest(msg='composer audits all non-cancelled post-publication capture outcomes'):
            self.assertIn('compose-release-notes:', composer_job)
            self.assertEqual(['[release, capture-release-note-inputs]'], _scalar_values(composer_job, 'needs', 4))
            self.assertEqual(["${{ always() && !cancelled() && needs.release.outputs.release_created == 'true' }}"], _scalar_values(composer_job, 'if', 4))
            self.assertNotIn('needs.release.result', composer_job)
        with self.subTest(msg='composer has exact minimum endpoint permissions'):
            self.assertEqual({'contents': 'write'}, _permission_map(composer_job))
        with self.subTest(msg='composer downloads the exact immutable snapshot by artifact id'):
            self.assertEqual(1, len(DOWNLOAD_ARTIFACT_PIN_RE.findall(content)))
            self.assertTrue(_contains_all(snapshot_download_step, ('id: download_release_snapshot', 'if: ${{ always() && !cancelled() }}', 'actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c', 'artifact-ids: ${{ needs.capture-release-note-inputs.outputs.snapshot_artifact_id }}', 'path: release-note-input', 'digest-mismatch: error')))
        with self.subTest(msg='composer audits capture download and digest failures'):
            self.assertTrue(_contains_all(compose_step + audit_helper_content, ('if: ${{ always() && !cancelled() }}', 'CAPTURE_RESULT: ${{ needs.capture-release-note-inputs.result }}', 'EXPECTED_SNAPSHOT_SHA256: ${{ needs.capture-release-note-inputs.outputs.snapshot_sha256 }}', 'SNAPSHOT_ARTIFACT_DIGEST: ${{ needs.capture-release-note-inputs.outputs.snapshot_artifact_digest }}', 'SNAPSHOT_DOWNLOAD_OUTCOME: ${{ steps.download_release_snapshot.outcome }}', 'run: python3 scripts/audit-release-notes.py', 'FAILURE_OUTCOME = "release_note_composition_failed"', '"capture_result": capture_result', '"snapshot_download_outcome": download_outcome', 'if capture_result != "success":', 'if download_outcome != "success":', 'snapshot_sha256 != expected_sha256', 'snapshot["repository"] != environment["GITHUB_REPOSITORY"]', '"compare_headers"', '"release_body"', '"pulls"', 'not re.fullmatch(r"[0-9a-f]{64}", artifact_digest)', 'except AuditFailure as error:')))
            self.assertNotIn('release_note_audit_failed', audit_helper_content)
            failure_branch = audit_helper_content.find('if completed.returncode != 0:')
            wrapper_fail = audit_helper_content.find('fail(message, completed.returncode)', failure_branch)
            forwarded_stderr = audit_helper_content.find('stderr.write(completed.stderr)')
            self.assertGreater(failure_branch, -1)
            self.assertGreater(wrapper_fail, failure_branch)
            self.assertGreater(forwarded_stderr, failure_branch)
            self.assertLess(wrapper_fail, forwarded_stderr)
        with self.subTest(msg='composer rejects highlights emptied by sanitization'):
            validation_function = _python_function_block(policy_content, 'validate_release_note')
            compose_body_function = _python_function_block(composer_content, 'compose_release_body')
            self.assertTrue(_contains_all(validation_function + compose_body_function, ('extracted = extract_release_note(body)', 'if not sanitize_release_note(extracted):', 'return False, "release-note fence is empty after sanitization"', 'note = sanitize_release_note(extracted)', 'if extracted is not None and not note:', 'release-note block is empty after sanitization', 'if note is not None and not skipped:')))
        with self.subTest(msg='composer defends enclosing release-note fence boundaries'):
            opening_function = _python_function_block(policy_content, '_opening_fence')
            closing_function = _python_function_block(policy_content, '_is_closing_fence')
            extraction_function = _python_function_block(policy_content, 'extract_release_note')
            self.assertTrue(_contains_all(opening_function + closing_function + extraction_function, ('FENCE_RE.fullmatch(rest)', '_strip_quote_prefix(line, opening.quote_depth)', 're.escape(opening.character)', 'opening.length', '_is_closing_fence(candidate, opening)', 'if opening.info == "release-note":', 'An unclosed enclosing fence owns the remainder of the document', 'index = close_index + 1', 'malformed or len(matches) != 1')))
        with self.subTest(msg='capture owns Compare and PR reads while compose does not refetch'):
            request_methods = re.findall('client\\.request_json\\(\\s*"(?P<method>GET|PATCH|POST|PUT|DELETE)"', composer_content)
            self.assertEqual(['GET', 'GET', 'GET', 'PATCH'], request_methods)
            capture_function = _python_function_block(composer_content, 'capture_release_input_snapshot')
            resolve_release_function = _python_function_block(composer_content, '_resolve_release')
            run_function = _python_function_block(composer_content, 'run')
            self.assertIn('if not args.snapshot:', run_function)
            live_composition = run_function.split('if not args.snapshot:', 1)[1]
            self.assertTrue(_contains_all(capture_function, ('f"/repos/{client.repository}/compare/{base}...{head}"', 'f"/repos/{client.repository}/pulls/{commit.pr_number}"')))
            self.assertTrue(_contains_all(resolve_release_function + live_composition, ('load_release_input_snapshot(', '_resolve_release(client, args.tag)', 'f"/repos/{client.repository}/releases/tags/{quoted_tag}"', 'f"/repos/{client.repository}/releases/{release_id}"', '{"body": composed}')))
            self.assertNotIn('/compare/', live_composition)
            self.assertNotIn('/pulls/', live_composition)
            self.assertNotIn('capture_release_input_snapshot', live_composition)
        with self.subTest(msg='raw tag and body outputs flow only through capture environment'):
            self.assertNotIn('needs.release.outputs.body', composer_job)
            self.assertNotIn('needs.release.outputs.tag_name', composer_job)
            self.assertNotRegex(composer_job, 'RELEASE_BODY:\\s*\\$\\{\\{')
            self.assertIn('RELEASE_BODY: ${{ needs.release.outputs.body }}', capture_step)
            self.assertIn('RELEASE_TAG: ${{ needs.release.outputs.tag_name }}', capture_step)
            self.assertIn('composer_environment["RELEASE_TAG"] = snapshot["tag"]', audit_helper_content)
            self.assertNotIn('composer_environment["RELEASE_BODY"]', audit_helper_content)
        with self.subTest(msg='composer emits a verified digest-bound audit record'):
            self.assertTrue(_contains_all(audit_helper_content, ('"release_note_composed_and_verified"', 'published_body.startswith("## Highlights\\n\\n")', 'published_body.count(marker) != 1', 'payload.endswith(expected_suffix)', '"body_byte_count"', '"commit_count"', '"snapshot_byte_count"', 'composer_result["body_sha256"] != published_body_sha256', 'composer_result["body_byte_count"] != len(published_body.encode())', 'composer_result["snapshot_payload_sha256"] != sha256(payload.encode())', 'composer_result["snapshot_source_sha256"] != snapshot_sha256', 'snapshot_byte_count != len(snapshot_bytes)', '"release_body_sha256": published_body_sha256', 'output.write(f"audit_sha256={digest}\\n")', 'output.write(f"release_body_sha256={audit[\'release_body_sha256\']}\\n")')))
        with self.subTest(msg='composer uploads and summarizes an immutable audit artifact'):
            self.assertTrue(_contains_all(audit_upload_step + audit_record_step + audit_helper_content, ('if: ${{ always() }}', 'name: release-note-audit-${{ github.run_id }}-${{ github.run_attempt }}', 'path: release-note-audit.json', 'if-no-files-found: error', "AUDIT_ARTIFACT_DIGEST: ${{ steps.upload_release_audit.outputs['artifact-digest'] }}", "AUDIT_ARTIFACT_ID: ${{ steps.upload_release_audit.outputs['artifact-id'] }}", "AUDIT_ARTIFACT_URL: ${{ steps.upload_release_audit.outputs['artifact-url'] }}", 'run: python3 scripts/audit-release-notes.py --record-artifact', 'Immutable audit artifact')))
            self.assertNotIn('overwrite: true', audit_upload_step)
        with self.subTest(msg='composer invokes Python without elevated release token'):
            self.assertIn('[sys.executable, str(composer_path), "--snapshot", str(snapshot_path)]', audit_helper_content)
            self.assertIn('shell=False', audit_helper_content)
            self.assertIn('EXPECTED_SNAPSHOT_SHA256:', compose_step)
            self.assertIn('GITHUB_TOKEN: ${{ github.token }}', compose_step)
            self.assertNotIn('actions: write', composer_job)
            self.assertNotIn('pull-requests: write', composer_job)
            self.assertNotIn('pull-requests: read', composer_job)
            self.assertNotIn('RELEASE_PLEASE_TOKEN', composer_job)
        with self.subTest(msg='release.yml is valid YAML'):
            tab_indented_step = 'name: Invalid\njobs:\n\tbuild:\n\t  runs-on: ubuntu-latest\n'
            valid_nested_step = 'name: Valid\njobs:\n  release:\n    runs-on: ubuntu-latest\n    steps:\n      - name: Publish\n        run: echo valid\n'
            under_indented_step = 'name: Invalid\njobs:\n  release:\n    runs-on: ubuntu-latest\n    steps:\n      - name: Publish\n      run: echo invalid\n'
            self.assertFalse(yaml_syntax_sane(tab_indented_step), 'stdlib YAML sanity check accepted a tab-indented workflow line')
            self.assertTrue(yaml_syntax_sane(valid_nested_step), 'stdlib YAML sanity check rejected a valid nested workflow step')
            self.assertFalse(yaml_syntax_sane(under_indented_step), 'stdlib YAML sanity check accepted an under-indented step child')
            self.assertTrue(yaml_syntax_sane(content), 'release.yml failed YAML syntax validation')
            run_commands = _run_commands(content)
            self.assertTrue(run_commands, 'release workflow has no direct dispatch steps')
            self.assertTrue(all((_is_thin_direct_dispatch(command) for command in run_commands)), f'release workflow contains shell logic or a non-direct dispatch: {run_commands}')
            self.assertTrue(_is_thin_direct_dispatch("gh pr view 123 --jq '.number | tostring'"), 'GitHub CLI --jq must not be treated as an external jq command')
            self.assertFalse(_is_thin_direct_dispatch('jq -r .number input.json'))
            self.assertFalse(_is_thin_direct_dispatch('python3 helper.py && echo unsafe'))
            self.assertFalse(_is_thin_direct_dispatch('python3 helper.py > result.json'))
            self.assertFalse(_is_thin_direct_dispatch("python3 - <<'PY'"))
            self.assertFalse(_is_thin_direct_dispatch('if python3 helper.py; then exit 1; fi'))
            self.assertFalse(_is_thin_direct_dispatch('python3 legacy.sh'))
        with self.subTest(msg='release-please-config.json exists'):
            self.assertTrue(RELEASE_CONFIG_FILE.is_file(), f'file not found: {RELEASE_CONFIG_FILE}')
        with self.subTest(msg='release-please extra-files never pre-bump generated dist trees'):
            forbidden: list[str] = []
            if RELEASE_CONFIG_FILE.is_file():
                config = json.loads(RELEASE_CONFIG_FILE.read_text(encoding='utf-8'))
                for package in (config.get('packages') or {}).values():
                    if not isinstance(package, dict):
                        continue
                    for entry in package.get('extra-files') or []:
                        raw = entry.get('path', '') if isinstance(entry, dict) else str(entry)
                        normalized = posixpath.normpath(raw.lstrip('/')).lstrip('./')
                        if normalized == 'dist' or normalized.startswith('dist/'):
                            forbidden.append(raw)
            self.assertEqual([], forbidden, 'release-please extra-files must not target dist/** payloads; scripts/refresh-release-artifacts.py owns that tree')
SPEC_DIR = REPO_ROOT / 'docs' / 'ai' / 'specs'
WORKFLOW_DIRS = (SPEC_DIR / '.process', SPEC_DIR)
COVERAGE_VALIDATOR = REPO_ROOT / 'speckit-pro' / 'skills' / 'speckit-autopilot' / 'scripts' / 'validate-autopilot-phase-coverage.py'
OVERVIEW_HEADING = '## Workflow Overview'
CRITERIA_HEADING_PREFIX = '### Phase Gates'
GATE_LINE_PREFIX = re.compile('^[ \\t]*(?:(?:[-*+]|[0-9]+\\.)[ \\t]+(?:\\[[ xX]\\][ \\t]+)?|>[ \\t]*|#{1,6}[ \\t]+)+')
HTML_COMMENT = re.compile('(?s)<!--.*?-->')
GATE_ID = 'G(?P<gate>[0-9](?:\\.5)?)'
EMPHASIS = '[ \\t*_`]*'
GATE_LABEL = '(?:Gate|GATE|gate|Result|Status|Validation|Confidence[ \\t]+[Gg]ate)'
VERDICT = '(?:PASS(?:ED)?|Pass(?:ed)?|pass(?:ed)?)(?![A-Za-z])(?![ \\t]+(?i:only|when|if|once|unless|after|requires|criteria)\\b)'
TICK = '(?:[✅✓][ \\t]*)?'
GATE_RECORD_INLINE = re.compile('(?:^|\\||\\*\\*)' + EMPHASIS + TICK + EMPHASIS + '(?:Gate[ \\t]+)?' + GATE_ID + EMPHASIS + '(?:' + GATE_LABEL + EMPHASIS + ')?[:—–-]?' + EMPHASIS + TICK + EMPHASIS + VERDICT)
GATE_RECORD_CELL = re.compile('\\|' + EMPHASIS + TICK + EMPHASIS + '(?:Gate[ \\t]+)?' + GATE_ID + EMPHASIS + '(?:' + GATE_LABEL + ')?' + EMPHASIS + '\\|[ \\t]*' + TICK + '\\*{0,2}' + VERDICT)
GATE_RECORD_JSON = re.compile('"gate"[ \\t]*:[ \\t]*"' + GATE_ID + '"[^{}]*?"pass"[ \\t]*:[ \\t]*true')
GATE_RECORD_PATTERNS = (GATE_RECORD_INLINE, GATE_RECORD_CELL, GATE_RECORD_JSON)
PHASE_GATE_IDS = {'Specify': '1', 'Clarify': '2', 'Plan': '3', 'Checklist': '4', 'Tasks': '5', 'Analyze': '6', 'Confidence Gate': '6.5', 'Implement': '7'}
ADVISORY_PHASES = frozenset({'Confidence Gate'})
TERMINAL_STATUSES = frozenset({'Complete', '✅ Complete', 'Skipped', '✅ Skipped', '⏭ Skipped', '⏭️ Skipped'})
OPEN_STATUSES = frozenset({'Pending', '⏳ Pending', 'In Progress', '🔄 In Progress', 'Blocked', '⚠ Blocked', '⚠️ Blocked'})
KNOWN_STATUSES = TERMINAL_STATUSES | OPEN_STATUSES
GATE_RECORD_POSITIVE_CASES = ('**G5 gate:** ✅ PASS — `validate-gate G5`, "63 tasks found".', 'Completed 2026-07-24. **G3: PASS** (`plan.md exists with 0 unresolved markers`).', '**Gate G1: ✅ PASS** — `validate-gate` returned', '**G2 Gate:** Passed — 0 `[NEEDS CLARIFICATION]` markers remain.', '**G2 Result:** ✅ Passed. The authoritative gate reported', '**G6:** ✅ pass — 0 CRITICAL (1 MEDIUM found and remediated via consensus).', '**G6.5 Confidence Gate**: Pass: composite 0.98', '| Gate G5 | Passed: 32 tasks found and 0 unresolved markers |', '| G5 Gate | Passed: 39 tasks found, 0 markers. |', '| G1 Gate | ✅ Passed: `spec.md` exists with 0 markers |', '| G5 Gate | ✅ PASS (37 tasks; every FR has ≥1 task) |', '| G3 gate | Passed |', '| G3 | Pass: `validate-gate.sh G3` reported `pass=true`, 0 markers |', '| G5 Validation | Passed; 28 tasks detected |', '| **G5 Status** | Pass: tasks cover implementation |', '| **G5** | ✅ pass (30 tasks, 0 markers) |', '| Gate G1 | PASS — runner validate-gate: `spec.md exists with 0 markers` |', '| **Gate G5** | PASS — runner-verified: 136 tasks found, 0 markers |', '| G7 | Passed | `run-all` passed `2937/2937` |', '{"gate":"G5","pass":true,"reason":"40 tasks found","markers":0,"task_count":40}', '- [x] **G5 gate:** ✅ PASS — 63 tasks found', '- G3 gate: PASS — `plan.md` with 0 unresolved markers', '| Total | 99 | 8 found / 8 resolved | ✅ G4 PASS (0 `[Gap]` markers) |', '**✅ G5 PASS** — 40 tasks found', '#### G1 Gate: PASS', '> **G6 gate:** PASS — 0 CRITICAL findings', '1. G7 gate: Passed')
STAGE_VALUES = ('plan', 'implement', 'full')
BASIC_INFO_HEADING = '### Basic Information'
STAGE_ROW_REJECTED_VALUES = ('planning', 'Plan', 'implementation', 'PLAN', 'full run')
STAGE_ROW_ACCEPTED_ROWS = ('| **Stage** | plan |\n', '| Stage | implement |\n', '| **Stage** | `full` |\n', '')
GATE_RECORD_NEGATIVE_CASES = ('| G7 | After Each Implementation Phase | Tests pass, manual verification complete |', '| G3 | After Plan | Architecture approved, constitution gates pass, dependencies identified |', 'reads Tasks and Analyze as Pending while the same file records G5 and G6 PASS at', '**G2 Gate:** Pass only when zero unresolved requirement markers remain.', '| Analyze | `/speckit-analyze` | Complete | 3 findings remediated; G6 ready |', 'Doctor health (after G0): 4 PASS, 1 WARN, 0 FAIL', '**G5 gate:** ❌ FAIL — 0 tasks found.', '| G6 | recommended pass once the analyzer reruns |', '{"gate":"G5","pass":false,"reason":"0 tasks found"}', '- **G2 Gate:** Pass Only when zero unresolved markers remain.', '#### G3 Gate: PASS IF the architecture review lands first')

def workflow_files(*directories: Path) -> list[Path]:
    """Every autopilot workflow markdown file, in deterministic order."""
    found: list[Path] = []
    for directory in directories:
        if not directory.is_dir():
            continue
        found.extend(directory.glob('*-workflow.md'))
    return sorted(found, key=lambda path: (path.name, str(path)))

def stage_fixture(stage_row: str) -> str:
    """A minimal workflow document carrying `stage_row` in `### Basic Information`."""
    return f'# Test Workflow\n\n{BASIC_INFO_HEADING}\n\n| Field | Value |\n|-------|-------|\n| **Branch** | `test-branch` |\n{stage_row}'

def markdown_without_comments(text: str) -> str:
    """Blank HTML comment spans while preserving line numbering.

    Mirrors the shipped validator: a commented-out example must not become
    evidence, or CI and the in-run guard would disagree about the same file.
    """
    return HTML_COMMENT.sub(lambda m: '\n' * m.group(0).count('\n'), text)

def _table_row_indexes(lines: list[str], start: int) -> list[int]:
    rows: list[int] = []
    for index in range(start, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith('|') and stripped.endswith('|'):
            rows.append(index)
        elif rows:
            break
        elif stripped.startswith('#'):
            break
    return rows

def overview_row_indexes(lines: list[str]) -> list[int]:
    """Row indexes of the '## Workflow Overview' table, header and separator included."""
    for index, line in enumerate(lines):
        if line.strip() == OVERVIEW_HEADING:
            return _table_row_indexes(lines, index + 1)
    return []

def criteria_row_indexes(lines: list[str]) -> set[int]:
    """Row indexes of every '### Phase Gates' approval-criteria table."""
    rows: set[int] = set()
    for index, line in enumerate(lines):
        if line.strip().startswith(CRITERIA_HEADING_PREFIX):
            rows.update(_table_row_indexes(lines, index + 1))
    return rows

def row_cells(line: str) -> list[str]:
    stripped = line.strip()
    return [cell.strip() for cell in stripped[1:-1].split('|')]

def gate_record_ids(line: str) -> set[str]:
    """Gate ids this line records a PASS verdict for."""
    unprefixed = GATE_LINE_PREFIX.sub('', line)
    return {match.group('gate') for pattern in GATE_RECORD_PATTERNS for match in pattern.finditer(unprefixed)}

def recorded_gates(lines: list[str], excluded: set[int]) -> dict[str, int]:
    """Map gate id -> 1-indexed line of its first PASS record outside the excluded rows."""
    found: dict[str, int] = {}
    for index, line in enumerate(lines):
        if index in excluded:
            continue
        for gate in gate_record_ids(line):
            found.setdefault(gate, index + 1)
    return found

def stage_value_errors(display: str, lines: list[str]) -> list[str]:
    """A recorded `Stage` row must read one of the three stage literals.

    Absence is legal and is not an error: it means "no run yet" and
    resolves through ordinary auto-detection. The row is read through the shared
    resolver, so this gate and the runner operation cannot disagree about what a
    given workflow file records.
    """
    value = read_only.workflow_recorded_stage(lines)
    if value is None or value in STAGE_VALUES:
        return []
    return [f"{display}: 'Stage' reads {value!r}, outside the closed stage vocabulary {list(STAGE_VALUES)}"]

def collect_errors(*directories: Path) -> dict[str, list[str]]:
    """Return each violation class as plain-English `file:line` strings."""
    missing_table: list[str] = []
    unknown_status: list[str] = []
    evidence: list[str] = []
    ordering: list[str] = []
    stage: list[str] = []
    for path in workflow_files(*directories):
        display = path.relative_to(REPO_ROOT).as_posix()
        lines = markdown_without_comments(path.read_text(encoding='utf-8')).splitlines()
        stage.extend(stage_value_errors(display, lines))
        rows = overview_row_indexes(lines)
        if len(rows) < 3:
            missing_table.append(f"{display}: no parseable '{OVERVIEW_HEADING}' table")
            continue
        excluded = set(rows) | criteria_row_indexes(lines)
        records = recorded_gates(lines, excluded)
        first_open: tuple[int, str, str] | None = None
        for index in rows[2:]:
            cells = row_cells(lines[index])
            if len(cells) < 3:
                continue
            phase, status = (cells[0], cells[2])
            number = index + 1
            if status not in KNOWN_STATUSES:
                unknown_status.append(f'{display}:{number}: {phase!r} status {status!r} is outside the closed vocabulary')
            gate = PHASE_GATE_IDS.get(phase)
            if gate is not None and gate in records and (status not in TERMINAL_STATUSES):
                evidence.append(f'{display}:{number}: {phase!r} reads {status!r} but the file records a G{gate} PASS at :{records[gate]}')
            if status in TERMINAL_STATUSES:
                if first_open is not None:
                    ordering.append(f'{display}:{number}: {phase!r} reads {status!r} after {first_open[1]!r} at :{first_open[0]} still reads {first_open[2]!r}')
            elif first_open is None and phase not in ADVISORY_PHASES:
                first_open = (number, phase, status)
    return {'missing_table': missing_table, 'unknown_status': unknown_status, 'evidence': evidence, 'ordering': ordering, 'stage': stage}

def load_coverage_validator():
    """Import the shipped phase-coverage validator so the vocabulary lock reads real bytes."""
    spec = importlib.util.spec_from_file_location('speckit_autopilot_phase_coverage', COVERAGE_VALIDATOR)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

class ValidateWorkflowStatusEvidence(unittest.TestCase):

    def test_workflow_status_tables_agree_with_gate_evidence(self) -> None:
        files = workflow_files(*WORKFLOW_DIRS)
        with self.subTest(msg='autopilot workflow files are discoverable'):
            self.assertTrue(files, f'no *-workflow.md files under {list(WORKFLOW_DIRS)}')
        errors = collect_errors(*WORKFLOW_DIRS)
        with self.subTest(msg='every workflow file exposes a parseable Workflow Overview table'):
            self.assertFalse(errors['missing_table'], '\n'.join(errors['missing_table']))
        with self.subTest(msg='every Workflow Overview status cell uses the closed vocabulary'):
            self.assertFalse(errors['unknown_status'], '\n'.join(errors['unknown_status']))
        with self.subTest(msg='a recorded gate PASS implies its Workflow Overview row is terminal'):
            self.assertFalse(errors['evidence'], '\n'.join(errors['evidence']))
        with self.subTest(msg='no terminal Workflow Overview row follows a non-terminal row'):
            self.assertFalse(errors['ordering'], '\n'.join(errors['ordering']))
        with self.subTest(msg='every recorded Stage row reads one of the three stage literals'):
            self.assertFalse(errors['stage'], '\n'.join(errors['stage']))
        with self.subTest(msg='the Stage vocabulary matches the shared resolver'):
            self.assertEqual(list(STAGE_VALUES), list(read_only.AUTOPILOT_STAGES), 'CI stage vocabulary drifted from the shared runner operation')
        with self.subTest(msg='a Stage row outside the closed vocabulary is reported'):
            unreported = [value for value in STAGE_ROW_REJECTED_VALUES if not stage_value_errors('fixture', stage_fixture(f'| **Stage** | {value} |\n').splitlines())]
            self.assertEqual([], unreported, f'accepted outside the vocabulary: {unreported}')
        with self.subTest(msg='a valid Stage row and an absent Stage row are both accepted'):
            rejected = [row for row in STAGE_ROW_ACCEPTED_ROWS if stage_value_errors('fixture', stage_fixture(row).splitlines())]
            self.assertEqual([], rejected, f'wrongly reported: {rejected}')
        with self.subTest(msg='gate-record matcher accepts every recorded evidence form'):
            unmatched = [case for case in GATE_RECORD_POSITIVE_CASES if not gate_record_ids(case)]
            self.assertEqual([], unmatched, '\n'.join(unmatched))
        with self.subTest(msg='gate-record matcher rejects criteria prose, citations, and FAIL records'):
            matched = [case for case in GATE_RECORD_NEGATIVE_CASES if gate_record_ids(case)]
            self.assertEqual([], matched, '\n'.join(matched))
        with self.subTest(msg='status vocabulary matches the shipped phase-coverage validator'):
            module = load_coverage_validator()
            self.assertIsNotNone(module, f'could not import {COVERAGE_VALIDATOR}')
            self.assertEqual(sorted(TERMINAL_STATUSES), sorted(module.WORKFLOW_TERMINAL_STATUSES), 'CI vocabulary drifted from the shipped validator')
            self.assertEqual(sorted(OPEN_STATUSES), sorted(module.WORKFLOW_OPEN_STATUSES), 'CI open-status vocabulary drifted from the shipped validator')
            self.assertEqual(dict(PHASE_GATE_IDS), dict(module.WORKFLOW_PHASE_GATE_IDS), 'CI phase-to-gate map drifted from the shipped validator')
            self.assertEqual(sorted(ADVISORY_PHASES), sorted(module.WORKFLOW_ADVISORY_PHASES), 'CI advisory-phase set drifted from the shipped validator')
        with self.subTest(msg='gate-record matcher matches the shipped phase-coverage validator'):
            module = load_coverage_validator()
            self.assertIsNotNone(module, f'could not import {COVERAGE_VALIDATOR}')
            self.assertEqual([pattern.pattern for pattern in GATE_RECORD_PATTERNS], [pattern.pattern for pattern in module.GATE_RECORD_PATTERNS], 'CI gate-record matcher drifted from the shipped validator')
            self.assertEqual(GATE_LINE_PREFIX.pattern, module.GATE_LINE_PREFIX_RE.pattern, 'CI line-prefix stripper drifted from the shipped validator')
            self.assertEqual(HTML_COMMENT.pattern, module.HTML_COMMENT_RE.pattern, 'CI HTML-comment handling drifted from the shipped validator')

# yaml_syntax_sane is shared by both workflow owners and regression tests.

def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-ci-release-contracts")

if __name__ == "__main__":
    raise SystemExit(main())
