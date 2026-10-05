"""Codex scaffold's git write probe: can this session create a ref under the repository's git directory?

Codex `workspace-write` keeps `.git` read-only unless the user grants it, so
branch creation fails late with a lock-file error. This helper creates and
removes one lock file where `git branch` would, and reports the result as a
`git_write` readiness observation. It stores nothing and names no local path.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response

ITEM = "git_write"
STOP_MESSAGE = (
    "Scaffold stopped before any gate or branch step: this session cannot write to the repository's .git "
    "directory ({cause}), and scaffold must create a branch and a worktree there. "
    "Fix it one of two ways, then rerun scaffold: approve git writes when Codex asks, or add the "
    "repository's .git directory to sandbox_workspace_write.writable_roots in the Codex config."
)
STOP_ACTION = ("Approve git writes, or add the repository's .git directory to "
               "sandbox_workspace_write.writable_roots, then rerun scaffold.")


def git_common_directory(cwd: Path) -> Path | None:
    try:
        completed = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--git-common-dir"], shell=False,
                                   capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0 or not completed.stdout.strip():
        return None
    return (cwd / completed.stdout.strip()).resolve()


def create_and_remove_lock(directory: Path) -> str | None:
    """The error class that blocked a lock-file create and remove under `directory`, or None."""
    lock = directory / f".speckit-git-write-probe-{os.getpid()}.lock"
    try:
        os.close(os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
        os.unlink(lock)
    except OSError as error:
        return type(error).__name__
    return None


def observation(status: str, source: str, probe: str, action: str | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"item": ITEM, "status": status, "evidence_source": source, "values": {"probe": probe}}
    if action is not None:
        item["action"] = action
    return item


def run_git_write_probe_helper(entry: Any, request: Any) -> dict[str, Any]:
    common = git_common_directory(Path.cwd())
    if common is None:
        data = {"verdict": "proceed", "message": "", "observation": observation(
            "unknown", "git directory not found for the write probe", "git_directory_not_found",
            "Run scaffold from inside the repository, then rerun it.")}
        return response("ok", request_id=request.request_id, data=data)
    blocked = create_and_remove_lock(common / "refs" / "heads")
    if blocked is None:
        data = {"verdict": "proceed", "message": "", "observation": observation(
            "verified", "lock file create and remove under the git refs directory", "lock_created_and_removed")}
        return response("ok", request_id=request.request_id, data=data)
    message = STOP_MESSAGE.format(cause=blocked)
    data = {"verdict": "stop", "message": message, "observation": observation(
        "unavailable", f"git refs directory is not writable: {blocked}", blocked, STOP_ACTION)}
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diagnostic(
        "git_not_writable", message, remediation_summary=STOP_ACTION,
        remediation_actions=["Approve git writes.", "Or add .git to sandbox_workspace_write.writable_roots.",
                             "Rerun scaffold."])])
