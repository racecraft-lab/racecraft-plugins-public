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

# Typed commands and model skill calls, in each host's payload shape.
HOST_CASES = {
    "claude": [
        # The shipping CLI sends `prompt`; the current hooks reference names `user_input`.
        {"hook_event_name": "UserPromptSubmit", "prompt": "/speckit-pro:speckit-autopilot docs/plan.md"},
        {"hook_event_name": "UserPromptSubmit", "user_input": "/speckit-autopilot docs/plan.md"},
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Skill",
            "tool_input": {"skill": "speckit-pro:speckit-autopilot", "args": ""},
        },
    ],
    "codex": [
        {"hook_event_name": "UserPromptSubmit", "prompt": "$speckit-autopilot run the workflow"},
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": f"sed -n '1,200p' {INSTALLED_SKILL}"},
        },
    ],
}

# Payloads the guard cannot read: a parse failure and an event it does not handle.
UNREADABLE_CASES = {host: ["{not json", {"hook_event_name": "Mystery"}] for host in HOST_CASES}

# Work that never runs a speckit-pro skill, including reads of the clone's own skill sources.
UNRELATED_CASES = {
    "claude": [
        {"hook_event_name": "UserPromptSubmit", "prompt": "fix /speckit-pro:speckit-autopilot resume"},
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

# Environment variables that look like a scratch mark or inject git config.
MARK_LOOKALIKES = {
    "SPECKIT_HEALTH_SCRATCH": "true",
    "GIT_CONFIG_COUNT": "1",
    "GIT_CONFIG_KEY_0": SCRATCH_KEY,
    "GIT_CONFIG_VALUE_0": "true",
    "GIT_CONFIG_PARAMETERS": f"'{SCRATCH_KEY}'='true'",
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


def block_reason(stdout: str, event: str) -> str:
    """The reason from the host's documented block shape for `event`, or "" for any other output."""
    output = json.loads(stdout)
    if event == "UserPromptSubmit":
        return output["reason"] if output.get("decision") == "block" else ""
    specific = output.get("hookSpecificOutput", {})
    if (specific.get("hookEventName"), specific.get("permissionDecision")) != ("PreToolUse", "deny"):
        return ""
    return specific["permissionDecisionReason"]


class HostWiringTests(unittest.TestCase):
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


class ScratchCloneGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def assert_outcome(self, cases: dict, cwd: Path, outcome: str, env: dict[str, str] | None = None) -> None:
        """Run every case from `cwd` and expect `outcome`: "allow", "block", or "error"."""
        for host, payloads in cases.items():
            for payload in payloads:
                with self.subTest(host=host, payload=payload, cwd=cwd.name):
                    result = run_guard(host, payload, cwd, env)
                    if outcome == "block":
                        self.assertEqual(0, result.returncode, result.stderr)
                        self.assertIn(SCRATCH_KEY, block_reason(result.stdout, payload["hook_event_name"]))
                        continue
                    # Exit 2 with a stderr reason blocks both events on both hosts.
                    code = 2 if outcome == "error" else 0
                    self.assertEqual(code, result.returncode, result.stdout + result.stderr)
                    self.assertEqual(code == 2, bool((result.stderr if code else result.stdout).strip()))

    def test_scratch_mark_decides_typed_and_model_calls_on_both_hosts(self) -> None:
        self.assert_outcome(HOST_CASES, make_clone(self.root), "block")
        self.assert_outcome(HOST_CASES, make_clone(self.root, marked=True), "allow")

    def test_unmarked_clone_allows_work_that_does_not_run_speckit_pro(self) -> None:
        self.assert_outcome(UNRELATED_CASES, make_clone(self.root), "allow")

    def test_environment_variables_never_mark_a_clone(self) -> None:
        self.assert_outcome(HOST_CASES, make_clone(self.root), "block", MARK_LOOKALIKES)

    def test_hook_errors_fail_closed_on_both_hosts(self) -> None:
        bad_mark = make_clone(self.root, marked="not-a-bool")
        outside = self.root / "outside"
        outside.mkdir()
        self.assert_outcome(UNREADABLE_CASES, bad_mark, "error")
        self.assert_outcome(HOST_CASES, bad_mark, "error")
        self.assert_outcome(HOST_CASES, outside, "error")


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    return unittest.TestSuite(loader.loadTestsFromTestCase(case) for case in (HostWiringTests, ScratchCloneGuardTests))


def main() -> int:
    return run_counted(build_suite(), label="test-scratch-clone-guard")


if __name__ == "__main__":
    raise SystemExit(main())
