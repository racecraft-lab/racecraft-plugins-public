#!/usr/bin/env python3
"""Consolidated Layer 1 contracts owned by validate-hook-contracts.py."""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for _import_root in (LIB_DIR, PLUGIN_ROOT):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))

from structural_helpers import declared_hook_commands as _declared_hook_commands
from structural_helpers import field_exists as _field_exists
from test_result import run_counted

validate_hooks_HOOKS_FILE = PLUGIN_ROOT / 'hooks' / 'hooks.json'

class ValidateHooks(unittest.TestCase):

    def test_hooks(self) -> None:
        with self.subTest(msg='hooks.json exists'):
            self.assertTrue(validate_hooks_HOOKS_FILE.is_file(), f'file not found: {validate_hooks_HOOKS_FILE}')
        raw = validate_hooks_HOOKS_FILE.read_text(encoding='utf-8') if validate_hooks_HOOKS_FILE.is_file() else ''
        with self.subTest(msg='hooks.json is valid JSON'):
            try:
                json.loads(raw)
            except json.JSONDecodeError as exc:
                self.fail(f'hooks.json is not valid JSON: {exc}')
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}
        with self.subTest(msg='has top-level hooks key'):
            self.assertTrue(_field_exists(data, 'hooks'), "JSON field 'hooks' does not exist")
        hooks_map = data.get('hooks', {}) if isinstance(data.get('hooks'), dict) else {}
        with self.subTest(msg='SessionStart attests the feedback-sweep hook boundary'):
            commands = _declared_hook_commands({'hooks': {'SessionStart': hooks_map.get('SessionStart', [])}})
            self.assertEqual(['command=${CLAUDE_PLUGIN_ROOT}/scripts/sweep-isolation-hook.py attest sweep-isolation-v1'], commands, 'SessionStart must run only the version-pinned sweep hook attestation')
        with self.subTest(msg='NO UserPromptSubmit hook (would fire on every prompt — regression guard)'):
            has_user_prompt_submit = 'UserPromptSubmit' in hooks_map
            self.assertEqual('false', 'true' if has_user_prompt_submit else 'false', 'plugin must not register a global UserPromptSubmit hook')
        with self.subTest(msg='Only the four version-pinned sweep isolation commands are executable'):
            declared = _declared_hook_commands(data)
            self.assertEqual(['command=${CLAUDE_PLUGIN_ROOT}/scripts/sweep-isolation-hook.py attest sweep-isolation-v1', 'command=${CLAUDE_PLUGIN_ROOT}/scripts/sweep-isolation-hook.py pre-dispatch sweep-isolation-v1', 'command=${CLAUDE_PLUGIN_ROOT}/scripts/sweep-isolation-hook.py authorize-broker sweep-isolation-v1', 'command=${CLAUDE_PLUGIN_ROOT}/scripts/sweep-isolation-hook.py validate-stop sweep-isolation-v1'], declared, 'Claude sweep confinement requires exactly its attestation, dispatch, and receipt hooks')
validate_codex_hooks_HOOKS_FILE = PLUGIN_ROOT / 'codex-hooks.json'
MANIFEST_FILE = PLUGIN_ROOT / '.codex-plugin' / 'plugin.json'

class ValidateCodexHooks(unittest.TestCase):

    def test_codex_hooks(self) -> None:
        with self.subTest(msg='codex-hooks.json exists'):
            self.assertTrue(validate_codex_hooks_HOOKS_FILE.is_file(), f'file not found: {validate_codex_hooks_HOOKS_FILE}')
        with self.subTest(msg='.codex-plugin/plugin.json declares hooks pointer'):
            hooks_ptr = ''
            if MANIFEST_FILE.is_file():
                try:
                    hooks_ptr = json.loads(MANIFEST_FILE.read_text(encoding='utf-8')).get('hooks', '')
                except (json.JSONDecodeError, OSError):
                    hooks_ptr = ''
                self.assertEqual('./codex-hooks.json', hooks_ptr, f'manifest hooks field must be "./codex-hooks.json" (was: "{hooks_ptr}")')
            else:
                self.fail('.codex-plugin/plugin.json missing')
        if not validate_codex_hooks_HOOKS_FILE.is_file():
            return
        raw = validate_codex_hooks_HOOKS_FILE.read_text(encoding='utf-8')
        with self.subTest(msg='codex-hooks.json is valid JSON'):
            try:
                json.loads(raw)
            except json.JSONDecodeError as exc:
                self.fail(f'codex-hooks.json is not valid JSON: {exc}')
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}
        with self.subTest(msg='has top-level hooks key'):
            self.assertTrue(_field_exists(data, 'hooks'), "JSON field 'hooks' does not exist")
        with self.subTest(msg='UserPromptSubmit event exists under hooks'):
            self.assertTrue(_field_exists(data, 'hooks.UserPromptSubmit'), "JSON field 'hooks.UserPromptSubmit' does not exist")
        with self.subTest(msg='NO SessionStart hook (would fire on every session — regression guard)'):
            has_session_start = 'SessionStart' in (data.get('hooks', {}) if isinstance(data.get('hooks'), dict) else {})
            self.assertEqual('false', 'true' if has_session_start else 'false', 'Codex hook must not register SessionStart')
        with self.subTest(msg='UserPromptSubmit has non-empty hooks array'):
            arr = data.get('hooks', {}).get('UserPromptSubmit')
            self.assertEqual('true', 'true' if isinstance(arr, list) and len(arr) > 0 else 'false', 'UserPromptSubmit must have a non-empty array')
        with self.subTest(msg='Hook entry has hooks array'):
            try:
                entry = data['hooks']['UserPromptSubmit'][0]
                ok = isinstance(entry, dict) and 'hooks' in entry and isinstance(entry['hooks'], list)
            except (KeyError, TypeError, IndexError):
                ok = False
            self.assertEqual('true', 'true' if ok else 'false', 'hook entry must have hooks array')
        with self.subTest(msg='No hook event declares an executable command'):
            declared = _declared_hook_commands(data)
            self.assertEqual('true', 'true' if not declared else 'false', f'Plugin hook manifests declare event scope only: no hook event may carry an executable command, because a static manifest cannot resolve the Python 3.11+ interpreter the Installed Runtime Contract requires. Skills own interpreter resolution. Found: {declared}')

def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-hook-contracts")

if __name__ == "__main__":
    raise SystemExit(main())
