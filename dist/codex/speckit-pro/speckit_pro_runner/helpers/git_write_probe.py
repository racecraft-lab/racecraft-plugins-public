"""Codex scaffold's git write probe: can this session create a ref under the repository's git directory?

Codex `workspace-write` keeps `.git` read-only unless the user grants it, so
branch creation fails late with a lock-file error. This helper creates and
removes one lock file where `git branch` would, and reports the result as a
`git_write` readiness observation. Cleanup failures name only probe basenames.
"""

from __future__ import annotations

import errno
import os
import secrets
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any, Iterator

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
ANCHORED_PROBE_SUPPORTED = (
    hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY")
    and {os.open, os.stat, os.unlink, os.rename, os.link, os.mkdir, os.rmdir} <= os.supports_dir_fd
    and os.stat in os.supports_follow_symlinks
)


def probe_error(errors: list[OSError]) -> OSError | None:
    """A known permission denial takes priority over unrelated storage or teardown errors."""
    return next((error for error in errors if error.errno in DENIED), next(iter(errors), None))


def close_probe_descriptor(fd: int, errors: list[OSError]) -> None:
    """Record teardown errors without masking the probe's earlier observations."""
    try:
        os.close(fd)
    except OSError as error:
        errors.append(error)


@contextmanager
def probe_directory(common: Path, directory: Path, errors: list[OSError]) -> Iterator[int]:
    """Hold each component below the canonical Git directory without following links."""
    if not ANCHORED_PROBE_SUPPORTED:
        raise OSError(errno.ENOTSUP, "descriptor-relative git write probe unavailable")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    with ExitStack() as stack:
        fd = os.open(common, flags)
        stack.callback(close_probe_descriptor, fd, errors)
        for component in directory.relative_to(common).parts:
            try:
                fd = os.open(component, flags, dir_fd=fd)
            except OSError as error:
                if error.errno in {errno.ELOOP, errno.ENOTDIR}:
                    raise PermissionError(errno.EACCES, "unsafe git directory component") from error
                raise
            stack.callback(close_probe_descriptor, fd, errors)
        yield fd


def create_probe_lock(directory_fd: int) -> tuple[int, str]:
    """Exclusive creation with bounded retries for random-name collisions."""
    for _ in range(100):
        name = f".speckit-git-write-probe-{secrets.token_hex(16)}.lock"
        try:
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory_fd)
        except FileExistsError:
            continue
        return fd, name
    raise FileExistsError(errno.EEXIST, "git write probe names exhausted")


def remove_probe_lock(lock: str, directory_fd: int, created: os.stat_result) -> OSError | None:
    """Retry deletion only inside the probe's private cleanup directory."""
    blocked = None
    for _ in range(2):
        try:
            current = os.stat(lock, dir_fd=directory_fd, follow_symlinks=False)
            if (current.st_dev, current.st_ino) != (created.st_dev, created.st_ino):
                return OSError(errno.ESTALE, "git write probe was replaced")
            os.unlink(lock, dir_fd=directory_fd)
        except FileNotFoundError:
            return None
        except OSError as error:
            blocked = error
        else:
            return None
    return blocked


def retire_probe_lock(lock: str, directory_fd: int, created: os.stat_result) -> tuple[OSError | None, str | None]:
    """Capture the public name before checking identity; never unlink that public name."""
    private = lock + ".cleanup"
    errors: list[OSError] = []
    leftover = lock
    private_fd = None
    private_created = False
    try:
        os.mkdir(private, 0o700, dir_fd=directory_fd)
        private_created = True
        private_fd = os.open(private, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd)
        os.rename(lock, lock, src_dir_fd=directory_fd, dst_dir_fd=private_fd)
        leftover = f"{private} ({lock})"
        current = os.stat(lock, dir_fd=private_fd, follow_symlinks=False)
        if (current.st_dev, current.st_ino) != (created.st_dev, created.st_ino):
            # Exclusive link restores a captured replacement without overwriting a new public entry.
            os.link(lock, lock, src_dir_fd=private_fd, dst_dir_fd=directory_fd, follow_symlinks=False)
            os.unlink(lock, dir_fd=private_fd)
            errors.append(OSError(errno.ESTALE, "git write probe was replaced"))
        else:
            cleanup = remove_probe_lock(lock, private_fd, created)
            if cleanup is not None:
                raise cleanup
        leftover = ""
    except OSError as error:
        errors.append(error)
    finally:
        if private_fd is not None:
            close_probe_descriptor(private_fd, errors)
        if private_created:
            try:
                os.rmdir(private, dir_fd=directory_fd)
            except OSError as error:
                errors.append(error)
                leftover = leftover or private
    return probe_error(errors), leftover or None


def create_and_remove_lock(directory: Path, common: Path) -> tuple[OSError | None, str | None]:
    """Create exclusively with fresh random names, returning any error and leftover basename."""
    leftover = None
    errors: list[OSError] = []
    try:
        with probe_directory(common, directory, errors) as directory_fd:
            fd, lock = create_probe_lock(directory_fd)
            leftover = lock
            try:
                cleanup, leftover = retire_probe_lock(lock, directory_fd, os.fstat(fd))
                if cleanup is not None:
                    errors.append(cleanup)
            finally:
                close_probe_descriptor(fd, errors)
    except OSError as error:
        errors.append(error)
    return probe_error(errors), leftover


def probe_directories(common: Path) -> list[Path]:
    """Where scaffold writes: the refs directory (a stub file under reftable) and the git directory itself."""
    heads = common / "refs" / "heads"
    directories = [heads] if heads.is_dir() or heads.is_symlink() else []
    directories.append(common)
    metadata = common / "worktrees"
    if metadata.exists() or metadata.is_symlink():
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
    results = [] if common is None else [create_and_remove_lock(directory, common) for directory in probe_directories(common)]
    errors = [error for error, _ in results if error is not None]
    blocked = probe_error(errors)
    verdict, message, item = probe_result(blocked, common is not None)
    leftovers = [name for _, name in results if name is not None]
    if leftovers:
        message += " Probe files could not be removed under the repository's git directory: " + ", ".join(leftovers) + "."
        item["evidence_source"] += "; probe cleanup failed"
        item["action"] = (item.get("action") or "Rerun scaffold.") + (
            " Inspect the named leftover entries and restore any replacement files before removing only probe-owned files."
        )
    data = {"verdict": verdict, "message": message, "observation": item}
    if verdict == "proceed":
        return response("ok", request_id=request.request_id, data=data)
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diagnostic(
        "git_not_writable", message, remediation_summary=STOP_ACTION,
        remediation_actions=["Approve git writes.", "Or add .git to sandbox_workspace_write.writable_roots.",
                             "Rerun scaffold."])])
