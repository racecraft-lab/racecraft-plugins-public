#!/usr/bin/env python3
"""Workflow guard hooks: lockfile package-manager deny and unpushed-commit stop.

Two modes, both reading the hook payload on stdin and answering with the
JSON shape Claude Code and Codex both document:

``lockfile`` (PreToolUse, matched to the shell tool by the hook manifest):
when exactly one JavaScript lockfile kind is present, a shell command that
invokes a different package manager is denied with
``hookSpecificOutput.permissionDecision = "deny"``. The hook keys on the
``tool_input.command`` string; the manifest's matcher is the only place the
tool is named, which is the one field the installed-runtime guard exempts.

``unpushed`` (Stop): while an autopilot run is active
(``docs/ai/specs/.process/autopilot-state.json`` with an in-flight status),
a turn may not end with commits that the upstream branch does not have;
the hook answers ``{"decision": "block", "reason": ...}``. It yields when
``stop_hook_active`` is true so a blocked turn cannot loop.

Anything unexpected fails open: the hook exits 0 with a note on stderr,
because a broken guard must not lock an operator out of their own session.
That includes the interpreter itself: below Python 3.11, the Installed
Runtime Contract floor, the hook prints one warning and exits 0, so an old
interpreter degrades to the prose rules instead of blocking the operator.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HOOK_VERSION = "workflow-guard-v1"
LOCKFILES = {
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "yarn",
    "bun.lockb": "bun",
    "bun.lock": "bun",
    "package-lock.json": "npm",
}
MANAGER_ALIASES = {"npm": "npm", "npx": "npm", "pnpm": "pnpm", "pnpx": "pnpm", "yarn": "yarn", "bun": "bun", "bunx": "bun"}
MANAGER_RE = re.compile(r"(?<![\w./-])(npm|npx|pnpm|pnpx|yarn|bun|bunx)(?![\w.-])")
STATE_PATH = Path("docs/ai/specs/.process/autopilot-state.json")
ACTIVE_STATUSES = {"in_progress", "awaiting_review"}
MAX_PAYLOAD = 64 * 1024


def payload() -> dict[str, Any]:
    raw = sys.stdin.buffer.read(MAX_PAYLOAD + 1)
    if len(raw) > MAX_PAYLOAD:
        raise ValueError("hook input exceeds the bound")
    value = json.loads(raw or b"{}")
    if not isinstance(value, dict):
        raise ValueError("hook input must be an object")
    return value


def work_root(data: dict[str, Any]) -> Path:
    value = data.get("cwd")
    return Path(value if isinstance(value, str) and value else os.getcwd()).resolve(strict=False)


def lockfile_manager(root: Path) -> str | None:
    """The single package manager the nearest lockfile directory names, else None."""
    for directory in (root, *root.parents):
        found = {manager for name, manager in LOCKFILES.items() if (directory / name).is_file()}
        if found:
            return found.pop() if len(found) == 1 else None
        if (directory / ".git").exists():
            break
    return None


def lockfile_decision(data: dict[str, Any]) -> str | None:
    tool_input = data.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str):
        return None
    used = {MANAGER_ALIASES[m] for m in MANAGER_RE.findall(command)}
    if not used:
        return None
    expected = lockfile_manager(work_root(data))
    if expected is None or used == {expected}:
        return None
    wrong = ", ".join(sorted(used - {expected}))
    return (
        f"The lockfile selects {expected}; this command uses {wrong}. "
        f"Re-run it with {expected} so the lockfile stays authoritative."
    )


def active_state(root: Path) -> bool:
    for directory in (root, *root.parents):
        state = directory / STATE_PATH
        if state.is_file():
            try:
                status = json.loads(state.read_text(encoding="utf-8")).get("status")
            except (OSError, ValueError, AttributeError):
                return False
            return status in ACTIVE_STATUSES
        if (directory / ".git").exists():
            break
    return False


def git_count(root: Path, *args: str) -> int | None:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-list", "--count", *args],
        capture_output=True, text=True, shell=False, check=False, timeout=10,
    )
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


def unpushed_decision(data: dict[str, Any]) -> str | None:
    if data.get("stop_hook_active") is True:
        return None
    root = work_root(data)
    if not active_state(root):
        return None
    ahead = git_count(root, "@{upstream}..HEAD")
    if ahead is None:
        # No upstream: every local commit is unpushed.
        ahead = git_count(root, "HEAD")
    if not ahead:
        return None
    return (
        f"{ahead} commit(s) on this branch are not on its upstream while an autopilot "
        "workflow is active. Push them (or set the upstream and push) before ending the turn."
    )


def main(argv: list[str]) -> int:
    if sys.version_info < (3, 11):
        print("workflow guard hook: interpreter below Python 3.11, guard inactive (fail-open)", file=sys.stderr)
        return 0
    if len(argv) != 2 or argv[1] != HOOK_VERSION or argv[0] not in {"lockfile", "unpushed"}:
        print("workflow guard hook: usage <lockfile|unpushed> " + HOOK_VERSION, file=sys.stderr)
        return 2
    try:
        data = payload()
        if argv[0] == "lockfile":
            reason = lockfile_decision(data)
            if reason:
                print(json.dumps({"hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }}))
        else:
            reason = unpushed_decision(data)
            if reason:
                print(json.dumps({"decision": "block", "reason": reason}))
        return 0
    except Exception as exc:  # fail open, see module docstring
        print(f"workflow guard hook: no decision ({exc.__class__.__name__}: {exc})", file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
