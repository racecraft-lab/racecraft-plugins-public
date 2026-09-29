#!/usr/bin/env python3
"""Spec-index helper contract: runner registry entries, read-only check, and template sentinels."""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for _import_root in (LIB_DIR, PLUGIN_ROOT):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))

from test_result import run_counted

RUNNER_DIR = REPO_ROOT / 'speckit-pro' / 'speckit_pro_runner'
FIXTURES = REPO_ROOT / 'tests' / 'speckit-pro' / 'layer1-structural' / 'fixtures' / 'spec-index'
TEMPLATE = REPO_ROOT / 'speckit-pro' / 'skills' / 'speckit-coach' / 'templates' / 'roadmap-moc-template.md'
REGISTRY_REQ = {'schema_version': '1.0', 'request_id': 'l1-helper-registry', 'helper_id': 'helper-registry-dispatch', 'operation': 'helper-registry-dispatch', 'mode': 'read_only', 'inputs': {}}
MUTATION_REGISTRY_REQ = {'schema_version': '1.0', 'request_id': 'l1-mutation-registry', 'helper_id': 'mutation-registry-dispatch', 'operation': 'mutation-registry-dispatch', 'mode': 'read_only', 'inputs': {}}
CHECK_REQ = {'schema_version': '1.0', 'request_id': 'l1-generate-spec-index-check', 'helper_id': 'generate-spec-index-check', 'operation': 'generate-spec-index-check', 'mode': 'read_only', 'inputs': {'repo_root': '.'}}

def _runner_request(payload: dict[str, object], *, root: Path = REPO_ROOT, environment: dict[str, str] | None = None) -> str:
    env = dict(os.environ if environment is None else environment)
    plugin_root = REPO_ROOT / 'speckit-pro'
    existing = env.get('PYTHONPATH')
    env['PYTHONPATH'] = plugin_root.as_posix() if not existing else f'{plugin_root.as_posix()}{os.pathsep}{existing}'
    completed = subprocess.run([sys.executable, '-m', 'speckit_pro_runner'], input=json.dumps(payload), text=True, capture_output=True, cwd=root, env=env, shell=False, check=False)
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

def tracked_fixture_repo(test: unittest.TestCase, fixture: str) -> tuple[Path, dict[str, str]]:
    """Copy one spec-index fixture into a test-owned Git repository with its files tracked.

    The committed fixture's files are tracked; preserve that distinction without
    borrowing the enclosing checkout's index or user configuration.
    """
    temporary = tempfile.TemporaryDirectory(prefix='spec-index-fixtures-')
    test.addCleanup(temporary.cleanup)
    root = Path(temporary.name) / 'repo'
    template = Path(temporary.name) / 'empty-template'
    template.mkdir()
    shutil.copytree(FIXTURES / fixture, root)
    (root / '.specify').mkdir()
    environment = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_OPTIONAL_LOCKS='0')
    for arguments in (['init', '--quiet', '--initial-branch=fixture', f'--template={template}'],
                      ['add', '--force', '--', '.']):
        subprocess.run(['git', *arguments], cwd=root, env=environment, capture_output=True, check=True, timeout=30)
    return root, environment


class ValidateSpecIndexRegistry(unittest.TestCase):

    def test_spec_index_helpers_are_registered(self) -> None:
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


class ValidateSpecIndexDeterminism(unittest.TestCase):

    def setUp(self) -> None:
        self.fixture_root, self.environment = tracked_fixture_repo(self, 'determinism')

    def test_check_is_read_only_on_a_tracked_tree(self) -> None:
        with self.subTest(msg='determinism fixture owns a real Git index'):
            self.assertFalse(self.fixture_root.is_relative_to(REPO_ROOT))
            self.assertTrue((self.fixture_root / '.git' / 'index').is_file())
            tracked = subprocess.run(['git', 'ls-files', '-z'], cwd=self.fixture_root, env=self.environment,
                                     capture_output=True, check=True, timeout=30).stdout.decode().split('\0')
            self.assertEqual(sorted(name for name, _ in _snapshot(FIXTURES / 'determinism')), sorted(name for name in tracked if name))
        snap_before = _snapshot(self.fixture_root)
        check_json = _runner_request(CHECK_REQ, root=self.fixture_root, environment=self.environment)
        snap_after = _snapshot(self.fixture_root)
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


class ValidateSpecIndexCanonicalSpelling(unittest.TestCase):
    """``current-canonical/`` is the one fixture that starts in the current sentinel spelling."""

    def test_canonical_spelling_is_current(self) -> None:
        root, environment = tracked_fixture_repo(self, 'current-canonical')
        moc = (root / 'specs' / 'prsg-909-canonical' / 'SPEC-MOC.md').read_text(encoding='utf-8')
        with self.subTest(msg='fixture carries the canonical sentinel and no legacy .sh spelling'):
            self.assertIn('regenerated by generate-spec-index) -->', moc)
            self.assertNotIn('generate-spec-index.sh', moc)
        snap_before = _snapshot(root)
        check_json = _runner_request(CHECK_REQ, root=root, environment=environment)
        with self.subTest(msg='generate-spec-index-check finds the canonical spelling current with exit 0'):
            self.assertIn('"status":"ok"', check_json)
            self.assertIn('"exit_code":0', check_json)
        with self.subTest(msg='generate-spec-index-check leaves the canonical fixture unchanged'):
            self.assertEqual(snap_before, _snapshot(root))


class ValidateRoadmapMocTemplate(unittest.TestCase):

    def test_template_keeps_the_sentinel_grammar(self) -> None:
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


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-spec-index-helper-contract")


if __name__ == "__main__":
    raise SystemExit(main())
