#!/usr/bin/env python3
"""Host-parity tests for the repo hook that blocks speckit-pro outside scratch clones."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
GUARD = REPO_ROOT / "scripts" / "scratch-clone-guard.py"
CLAUDE_SETTINGS = REPO_ROOT / ".claude" / "settings.json"
CODEX_HOOKS = REPO_ROOT / ".codex" / "hooks.json"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


SCRATCH_KEY = "speckit-health.scratch"
INSTALLED_SKILL = "/home/owner/.codex/plugins/cache/market/speckit-pro/9.9.9/skills/speckit-autopilot/SKILL.md"

# One typed command and one model skill call per host, in each host's payload shape.
HOST_CASES = {
    "claude": {
        "typed": {"hook_event_name": "UserPromptSubmit", "user_input": "/speckit-pro:speckit-autopilot docs/plan.md"},
        "model": {
            "hook_event_name": "PreToolUse",
            "tool_name": "Skill",
            "tool_input": {"skill": "speckit-pro:speckit-autopilot", "args": ""},
        },
    },
    "codex": {
        "typed": {"hook_event_name": "UserPromptSubmit", "prompt": "$speckit-autopilot run the workflow"},
        "model": {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": f"sed -n '1,200p' {INSTALLED_SKILL}"},
        },
    },
}


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True)


def make_clone(root: Path, *, marked: bool | str = False) -> Path:
    clone = root / ("marked" if marked else "unmarked")
    clone.mkdir()
    git(clone, "init", "--quiet")
    if marked:
        git(clone, "config", SCRATCH_KEY, "true" if marked is True else marked)
    return clone


def run_guard(host: str, payload: dict | str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    if isinstance(payload, dict):
        payload = json.dumps({**payload, "cwd": str(cwd)})
    return subprocess.run(
        [sys.executable, str(GUARD), host],
        input=payload,
        text=True,
        capture_output=True,
        cwd=cwd,
        env={**os.environ, **(env or {})},
        shell=False,
        check=False,
    )


def hook_commands(config: Path, event: str) -> list[tuple[str | None, str]]:
    document = json.loads(config.read_text(encoding="utf-8"))
    return [
        (group.get("matcher"), handler["command"])
        for group in document["hooks"][event]
        for handler in group["hooks"]
    ]


class ScratchCloneGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def assert_blocked(self, result: subprocess.CompletedProcess[str], event: str) -> None:
        self.assertEqual(0, result.returncode, result.stderr)
        output = json.loads(result.stdout)
        if event == "UserPromptSubmit":
            self.assertEqual("block", output["decision"])
            self.assertIn(SCRATCH_KEY, output["reason"])
        else:
            specific = output["hookSpecificOutput"]
            self.assertEqual("PreToolUse", specific["hookEventName"])
            self.assertEqual("deny", specific["permissionDecision"])
            self.assertIn(SCRATCH_KEY, specific["permissionDecisionReason"])

    def assert_allowed(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout.strip())

    def assert_fails_closed(self, result: subprocess.CompletedProcess[str]) -> None:
        # Exit 2 with a stderr reason blocks both events on both hosts.
        self.assertEqual(2, result.returncode, result.stdout)
        self.assertTrue(result.stderr.strip())

    def test_hosts_wire_the_guard(self) -> None:
        claude_prompt = hook_commands(CLAUDE_SETTINGS, "UserPromptSubmit")
        claude_tool = hook_commands(CLAUDE_SETTINGS, "PreToolUse")
        codex_prompt = hook_commands(CODEX_HOOKS, "UserPromptSubmit")
        codex_tool = hook_commands(CODEX_HOOKS, "PreToolUse")
        claude_command = 'python3 "${CLAUDE_PROJECT_DIR}/scripts/scratch-clone-guard.py" claude'
        codex_command = 'python3 "$(git rev-parse --show-toplevel)/scripts/scratch-clone-guard.py" codex'
        self.assertEqual([(None, claude_command)], claude_prompt)
        self.assertEqual([("Skill", claude_command)], claude_tool)
        self.assertEqual([(None, codex_command)], codex_prompt)
        self.assertEqual([("Bash", codex_command)], codex_tool)

    def test_unmarked_clone_blocks_typed_and_model_calls_on_both_hosts(self) -> None:
        clone = make_clone(self.root)
        for host, cases in HOST_CASES.items():
            for kind, payload in cases.items():
                with self.subTest(host=host, kind=kind):
                    self.assert_blocked(run_guard(host, payload, clone), payload["hook_event_name"])

    def test_marked_clone_allows_typed_and_model_calls_on_both_hosts(self) -> None:
        clone = make_clone(self.root, marked=True)
        for host, cases in HOST_CASES.items():
            for kind, payload in cases.items():
                with self.subTest(host=host, kind=kind):
                    self.assert_allowed(run_guard(host, payload, clone))

    def test_unmarked_clone_allows_work_that_does_not_run_speckit_pro(self) -> None:
        clone = make_clone(self.root)
        allowed = {
            "claude": [
                {"hook_event_name": "UserPromptSubmit", "user_input": "fix /speckit-pro:speckit-autopilot resume"},
                {"hook_event_name": "UserPromptSubmit", "user_input": "/speckit-plan"},
                {"hook_event_name": "PreToolUse", "tool_name": "Skill", "tool_input": {"skill": "code-review"}},
            ],
            "codex": [
                {"hook_event_name": "UserPromptSubmit", "prompt": "fix the autopilot resume path"},
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git status"}},
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": "sed -n '1,80p' speckit-pro/skills/speckit-autopilot/SKILL.md"},
                },
            ],
        }
        for host, payloads in allowed.items():
            for payload in payloads:
                with self.subTest(host=host, payload=payload):
                    self.assert_allowed(run_guard(host, payload, clone))

    def test_environment_variables_never_mark_a_clone(self) -> None:
        clone = make_clone(self.root)
        lookalikes = {
            "SPECKIT_HEALTH_SCRATCH": "true",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": SCRATCH_KEY,
            "GIT_CONFIG_VALUE_0": "true",
            "GIT_CONFIG_PARAMETERS": f"'{SCRATCH_KEY}'='true'",
        }
        for host, cases in HOST_CASES.items():
            for kind, payload in cases.items():
                with self.subTest(host=host, kind=kind):
                    self.assert_blocked(run_guard(host, payload, clone, lookalikes), payload["hook_event_name"])

    def test_hook_errors_fail_closed_on_both_hosts(self) -> None:
        bad_mark = make_clone(self.root, marked="not-a-bool")
        for host, cases in HOST_CASES.items():
            with self.subTest(host=host, error="malformed payload"):
                self.assert_fails_closed(run_guard(host, "{not json", bad_mark))
            with self.subTest(host=host, error="unknown event"):
                self.assert_fails_closed(run_guard(host, {"hook_event_name": "Mystery"}, bad_mark))
            for kind, payload in cases.items():
                with self.subTest(host=host, kind=kind, error="unreadable mark"):
                    self.assert_fails_closed(run_guard(host, payload, bad_mark))
                with self.subTest(host=host, kind=kind, error="not a clone"):
                    outside = self.root / f"outside-{host}-{kind}"
                    outside.mkdir()
                    self.assert_fails_closed(run_guard(host, payload, outside))


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ScratchCloneGuardTests)


def main() -> int:
    return run_counted(build_suite(), label="test-scratch-clone-guard")


if __name__ == "__main__":
    raise SystemExit(main())
