#!/usr/bin/env python3
"""Repo hook that blocks speckit-pro skills outside a marked scratch clone (ADR 0002).

Claude Code runs it on UserPromptSubmit (typed commands) and PreToolUse on Skill
(model calls). Codex runs it on UserPromptSubmit (typed `$skill` mentions) and
PreToolUse on Bash (the model reading an installed speckit-pro SKILL.md).

The only scratch mark is the clone-local git config key `speckit-health.scratch`.
Git runs with every `GIT_*` variable removed, so the environment can never set or
redirect the mark. Any error blocks: exit 2 with the reason on stderr is a
supported denial for both events on both hosts.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRATCH_KEY = "speckit-health.scratch"
PLUGIN = "speckit-pro"
REPO_ROOT = Path(__file__).resolve().parents[1]
BLOCK_REASON = (
    f"{PLUGIN} skills are blocked in this clone until the canary is green on both hosts "
    f"(ADR 0002). Run them only in a scratch clone marked with: git config {SCRATCH_KEY} true"
)
CLAUDE_COMMAND = re.compile(r"\s*/(?P<name>[\w:-]+)")
CODEX_MENTION = re.compile(r"(?<![\w$-])\$(?P<name>[\w:-]+)")


class GuardError(Exception):
    """Evidence the guard needs is missing or unreadable."""


def skill_names(host: str) -> frozenset[str]:
    sources = ["skills"] if host == "claude" else ["skills", "codex-skills"]
    names = frozenset(
        path.parent.name
        for source in sources
        for path in (REPO_ROOT / PLUGIN / source).glob("*/SKILL.md")
    )
    if not names:
        raise GuardError(f"no {PLUGIN} skills found under {REPO_ROOT / PLUGIN}")
    return names


def is_plugin_skill(name: str, host: str) -> bool:
    name = name.lstrip("/$")
    return name.startswith(f"{PLUGIN}:") or name in skill_names(host)


def typed_skill(host: str, payload: dict[str, Any]) -> bool:
    # Codex and Claude Code 2.1 send `prompt`; the current Claude Code reference names `user_input`.
    text = payload.get("prompt", payload.get("user_input"))
    if not isinstance(text, str):
        raise GuardError("UserPromptSubmit payload has no prompt text")
    if host == "claude":
        match = CLAUDE_COMMAND.match(text)
        return bool(match) and is_plugin_skill(match["name"], host)
    return any(is_plugin_skill(match["name"], host) for match in CODEX_MENTION.finditer(text))


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        env=env,
        shell=False,
        check=False,
    )


def clone_root(cwd: Path) -> Path:
    result = git(cwd, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        raise GuardError(f"{cwd} is not inside a git clone: {result.stderr.strip()}")
    return Path(result.stdout.strip()).resolve()


def installed_skill_read(command: Any, cwd: Path) -> bool:
    """True when a shell command reads a speckit-pro SKILL.md outside this clone."""
    if isinstance(command, list):
        command = " ".join(str(part) for part in command)
    if not isinstance(command, str):
        raise GuardError("Bash payload has no command")
    if "SKILL.md" not in command or PLUGIN not in command:
        return False
    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        raise GuardError(f"cannot parse Bash command: {exc}") from exc
    root = clone_root(cwd)
    for token in tokens:
        path = Path(os.path.expanduser(token.rsplit("=", 1)[-1]))
        parts = path.parts
        if len(parts) < 3 or parts[-1] != "SKILL.md" or parts[-3] != "skills" or PLUGIN not in parts:
            continue
        if not (cwd / path).resolve().is_relative_to(root):
            return True
    return False


def runs_plugin_skill(host: str, payload: dict[str, Any], cwd: Path) -> bool:
    event = payload.get("hook_event_name")
    if event == "UserPromptSubmit":
        return typed_skill(host, payload)
    if event != "PreToolUse":
        raise GuardError(f"unsupported hook event: {event!r}")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        raise GuardError("PreToolUse payload has no tool_input")
    tool = payload.get("tool_name")
    if tool == "Skill":
        skill = tool_input.get("skill")
        if not isinstance(skill, str):
            raise GuardError("Skill payload has no skill name")
        return is_plugin_skill(skill, host)
    if tool == "Bash":
        return installed_skill_read(tool_input.get("command"), cwd)
    return False


def scratch_marked(cwd: Path) -> bool:
    result = git(cwd, "config", "--local", "--type=bool", "--get", SCRATCH_KEY)
    if result.returncode == 1 and not result.stderr.strip():
        return False
    if result.returncode != 0:
        raise GuardError(f"cannot read {SCRATCH_KEY}: {result.stderr.strip()}")
    return result.stdout.strip() == "true"


def block_output(event: str) -> dict[str, Any]:
    if event == "UserPromptSubmit":
        return {"decision": "block", "reason": BLOCK_REASON}
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": BLOCK_REASON,
        }
    }


def decide(host: str, payload: Any) -> dict[str, Any] | None:
    """Return the host's block output, or None to allow."""
    if not isinstance(payload, dict):
        raise GuardError("hook payload is not a JSON object")
    cwd_text = payload.get("cwd")
    if not isinstance(cwd_text, str) or not cwd_text:
        raise GuardError("hook payload has no cwd")
    cwd = Path(cwd_text)
    if not runs_plugin_skill(host, payload, cwd) or scratch_marked(cwd):
        return None
    return block_output(payload["hook_event_name"])


def main(argv: list[str]) -> int:
    try:
        if len(argv) != 1 or argv[0] not in {"claude", "codex"}:
            raise GuardError("usage: scratch-clone-guard.py claude|codex")
        output = decide(argv[0], json.loads(sys.stdin.read()))
    except BaseException as exc:  # noqa: BLE001 - any failure must block, never allow
        print(f"{PLUGIN} scratch-clone guard failed, so this call is blocked: {exc}", file=sys.stderr)
        return 2
    if output is not None:
        print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
