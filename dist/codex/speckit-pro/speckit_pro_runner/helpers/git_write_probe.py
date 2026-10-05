"""Codex scaffold's git write probe: can this session create a ref under the repository's git directory?

Codex `workspace-write` keeps `.git` read-only unless the user grants it, so
branch creation fails late with a lock-file error. This helper creates and
removes one lock file where `git branch` would, and reports the result as a
`git_write` readiness observation. Cleanup failures name only probe basenames.
"""

from __future__ import annotations

import errno
import os
import tempfile
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response
from .gate_preflight_coverage import git_common_directory

ITEM = "git_write"
STOP_MESSAGE = (
    "Scaffold stopped before any gate or branch step: this session cannot write to the repository's .git "
    "directory ({cause}), and scaffold must create a branch and worktree metadata there. "
    "Fix it one of two ways, then rerun scaffold: approve git writes when Codex asks, or add the "
    "repository's .git directory to sandbox_workspace_write.writable_roots in the Codex config."
)
STOP_ACTION = ("Approve git writes, or add the repository's .git directory to "
               "sandbox_workspace_write.writable_roots, then rerun scaffold.")


DENIED = frozenset({errno.EACCES, errno.EPERM, errno.EROFS})


def remove_probe_lock(lock: str) -> OSError | None:
    """Retry cleanup once; an already removed probe needs no further cleanup."""
    blocked = None
    for _ in range(2):
        try:
            os.unlink(lock)
        except FileNotFoundError:
            return None
        except OSError as error:
            blocked = error
        else:
            return None
    return blocked


def create_and_remove_lock(directory: Path) -> tuple[OSError | None, str | None]:
    """Create exclusively with fresh random names, returning any error and leftover basename."""
    try:
        fd, lock = tempfile.mkstemp(prefix=".speckit-git-write-probe-", suffix=".lock", dir=directory)
    except OSError as error:
        return error, None
    blocked = None
    try:
        os.close(fd)
    except OSError as error:
        blocked = error
    finally:
        cleanup = remove_probe_lock(lock)
    return cleanup or blocked, Path(lock).name if cleanup else None


def probe_directories(common: Path) -> list[Path]:
    """Where scaffold writes: the refs directory (a stub file under reftable) and the git directory itself."""
    heads = common / "refs" / "heads"
    directories = [heads] if heads.is_dir() else []
    directories.append(common)
    metadata = common / "worktrees"
    if metadata.exists():
        directories.append(metadata)
    return directories


def probe_result(blocked: OSError | None, found: bool) -> tuple[str, str, dict[str, Any]]:
    """The verdict, the stop message and the `git_write` readiness observation for one probe outcome."""
    if not found:
        status, source, probe = "unknown", "git directory not found for the write probe", "git_directory_not_found"
        action = "Run scaffold from inside the repository, then rerun it."
    elif blocked is not None and blocked.errno not in DENIED:
        status, source, probe = "unknown", f"git write probe failed: {type(blocked).__name__}", type(blocked).__name__
        action = "Fix the reported storage problem under the repository's .git directory, then rerun scaffold."
    elif blocked is None:
        status, source, probe = "verified", "lock file create and remove under the git directory", "lock_created_and_removed"
        action = None
    else:
        name = type(blocked).__name__
        status, source, probe = "unavailable", f"git directory is not writable: {name}", name
        action = STOP_ACTION
    item: dict[str, Any] = {"item": ITEM, "status": status, "evidence_source": source, "values": {"probe": probe}}
    if action is not None:
        item["action"] = action
    verdict = "stop" if status == "unavailable" else "proceed"
    return verdict, STOP_MESSAGE.format(cause=probe) if verdict == "stop" else "", item


def run_git_write_probe_helper(entry: Any, request: Any) -> dict[str, Any]:
    try:
        common: Path | None = git_common_directory(Path.cwd())
    except ValueError:
        common = None
    results = [create_and_remove_lock(directory) for directory in ([] if common is None else probe_directories(common))]
    errors = [error for error, _ in results if error is not None]
    blocked = next((error for error in errors if error.errno in DENIED), next(iter(errors), None))
    verdict, message, item = probe_result(blocked, common is not None)
    leftovers = [name for _, name in results if name is not None]
    if leftovers:
        message += " Probe files could not be removed under the repository's git directory: " + ", ".join(leftovers) + "."
        item["evidence_source"] += "; probe cleanup failed"
        item["action"] = (item.get("action") or "Rerun scaffold.") + " Remove the named leftover probe files."
    data = {"verdict": verdict, "message": message, "observation": item}
    if verdict == "proceed":
        return response("ok", request_id=request.request_id, data=data)
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diagnostic(
        "git_not_writable", message, remediation_summary=STOP_ACTION,
        remediation_actions=["Approve git writes.", "Or add .git to sandbox_workspace_write.writable_roots.",
                             "Rerun scaffold."])])
