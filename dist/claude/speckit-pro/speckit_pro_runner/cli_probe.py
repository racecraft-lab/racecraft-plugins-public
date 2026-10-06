"""Read-only CLI queries with fixed argv, a per-caller allowlist and a timeout; hosts take only --version."""

from __future__ import annotations

import functools
import os
import re
import shutil
import stat
import subprocess
from collections.abc import Callable, Collection
from pathlib import Path
from typing import Any

# A branch name that could be read as an option, or that git would reject, is never passed to a CLI.
BRANCH = re.compile(r"(?!-)(?!.*\.\.)(?!.*//)[A-Za-z0-9._/-]{1,255}\Z")
STDERR_TAIL_CHARS = 2048
STDOUT_TAIL_CHARS = 1024 * 1024
DOCKER_STDOUT_TAIL_CHARS = STDERR_TAIL_CHARS
CLIS = ("gh", "git", "docker", "claude", "codex")


def reject_mutable_probe_alias(info: os.stat_result, path: Path, *, host: bool,
                               shared: Callable[[os.stat_result], bool] | None = None) -> None:
    """A writable host inode or namespace cannot authenticate a later lookup.

    Keep system-owned, non-group/other-writable hardlinks: a worktree writer
    cannot modify them or grant itself write access through an alias. `shared`
    narrows a writable hardlink to one that is also a worktree file, because root
    can write every system hardlink in a container.
    """
    writable = info.st_uid == os.geteuid() or os.access(path, os.W_OK, effective_ids=True)
    if host and stat.S_ISDIR(info.st_mode) and writable:
        raise ValueError("CLI lookup cannot authenticate a mutable directory")
    if stat.S_ISREG(info.st_mode) and writable and (host or info.st_nlink > 1) and (shared is None or shared(info)):
        raise ValueError("CLI lookup cannot authenticate a mutable executable inode")


def worktree_link_inodes(worktree: Path) -> set[tuple[int, int]]:
    """Every multiply linked worktree file; an unreadable directory fails closed."""
    def fail(error: OSError) -> None:
        raise error

    inodes = set()
    for parent, directories, files in os.walk(worktree, onerror=fail):
        for name in (*directories, *files):
            info = os.lstat(os.path.join(parent, name))
            if stat.S_ISREG(info.st_mode) and info.st_nlink > 1:
                inodes.add((info.st_dev, info.st_ino))
    return inodes


def external_probe_path(path: Path, worktree: Path, links: int = 40, *, host: bool = False) -> Path:
    """Resolve links root-first; host lookups require protected ancestors at every hop.

    Protect the parent before observing a child: holding only an executable inode
    leaves directory replacement and the child's later PATH lookups unauthenticated.
    A same-identity writer must not own (and chmod) or effectively write any ancestor.
    """
    if links < 0 or path.is_relative_to(worktree):
        raise ValueError("CLI path traverses the worktree or too many symlinks")
    if path.parent == path:
        reject_mutable_probe_alias(path.lstat(), path, host=host)
        return path
    parent = external_probe_path(path.parent, worktree, links, host=host)
    candidate = parent.parent if path.name == ".." else parent / path.name
    if candidate.is_relative_to(worktree) or (candidate.is_dir() and candidate.samefile(worktree)):
        raise ValueError("CLI path traverses the worktree")
    if candidate.is_symlink():
        target = candidate.readlink()
        return external_probe_path(target if target.is_absolute() else parent / target, worktree, links - 1, host=host)
    if candidate.is_dir():
        reject_mutable_probe_alias(candidate.lstat(), candidate, host=host)
    return candidate


def validate_probe_directory(directory: Path, worktree: Path, *, host: bool, cli: str,
                             shared: Callable[[os.stat_result], bool]) -> None:
    """Authenticate every child lookup name, including env-shebang interpreters/helpers.

    Other CLIs judge a writable hardlink beside the selected name by `shared`, so an
    unrelated system hardlink keeps the directory while a worktree alias rejects it.
    """
    external_probe_path(directory, worktree, host=host)
    for entry in directory.iterdir():
        narrow = None if host or entry.name.casefold() == cli else shared
        info = entry.lstat()
        if stat.S_ISLNK(info.st_mode):
            target = external_probe_path(entry, worktree, host=host)
            if target.exists():
                reject_mutable_probe_alias(target.stat(), target, host=host, shared=narrow)
        else:
            reject_mutable_probe_alias(info, entry, host=host, shared=narrow)


def probe_search_path(root: Path, cli: str) -> str:
    """Exclude cwd-relative entries and worktree-owned directories or executable targets.

    Host PATH directories and every link target ancestor must be protected from
    same-identity changes for lookup, launch and later helper resolution. Canonical
    paths alone cannot prevent rename/recreation. An empty search path must never reach subprocess: on
    POSIX it would search cwd again. Other platforms' cwd lookup rules fail closed.
    """
    if os.name != "posix":
        raise ValueError("trusted CLI lookup requires POSIX")
    worktree = root.resolve(strict=True)
    inodes = functools.cache(functools.partial(worktree_link_inodes, worktree))
    directories = []
    for entry in os.environ.get("PATH", os.defpath).split(os.pathsep):
        directory = Path(entry)
        if not directory.is_absolute() or directory.is_relative_to(root.absolute()):
            continue
        try:
            directory = directory.resolve(strict=True)
            target = external_probe_path(directory / cli, worktree, host=cli in ("claude", "codex"))
            validate_probe_directory(directory, worktree, host=cli in ("claude", "codex"), cli=cli,
                                     shared=lambda info: (info.st_dev, info.st_ino) in inodes())
        except (OSError, RuntimeError, ValueError):
            continue
        if not directory.is_relative_to(worktree) and not target.is_relative_to(worktree):
            directories.append(str(directory))
    if not directories:
        raise ValueError("no external absolute CLI search directory")
    return os.pathsep.join(directories)


def probe(root: Path, argv: list[str], *, allowed: Collection[str], timeout: float) -> dict[str, Any]:
    """Run `argv` when its CLI is in `allowed`; any failure to run is reported, never raised.

    The record always has the same four keys. `exit_status` is None when the CLI is not
    allowed, cannot start, exceeds `timeout` seconds, or overflows the stdout limit.
    Docker output is limited to 2048 characters; Git/GitHub retain up to 1 MiB
    so ordinary structured responses stay complete. Overflow is never a successful probe.
    """
    try:
        if not argv or argv[0] not in allowed or argv[0] not in CLIS:
            raise ValueError(f"only {', '.join(sorted(allowed))} may run here")
        if argv[0] in ("claude", "codex") and argv[1:] != ["--version"]:
            raise ValueError("host probes take only --version")
        search_path = probe_search_path(root, argv[0])
        environment = {**os.environ, "PATH": search_path}
        # Each executable is a literal, so the repository Bash-confinement guard can prove it Bash-free.
        options: dict[str, Any] = {"cwd": root, "capture_output": True, "text": True, "timeout": timeout,
                                   "stdin": subprocess.DEVNULL, "shell": False, "env": environment}
        if argv[0] == "gh":
            result = subprocess.run(["gh", *argv[1:]], executable=shutil.which("gh", path=search_path), **options)
        elif argv[0] == "docker":
            result = subprocess.run(["docker", *argv[1:]], executable=shutil.which("docker", path=search_path), **options)
        elif argv[0] == "claude":
            result = subprocess.run(["claude", "--version"], executable=shutil.which("claude", path=search_path), **options)
        elif argv[0] == "codex":
            result = subprocess.run(["codex", "--version"], executable=shutil.which("codex", path=search_path), **options)
        else:
            result = subprocess.run(["git", *argv[1:]], executable=shutil.which("git", path=search_path), **options)
        stdout_limit = DOCKER_STDOUT_TAIL_CHARS if argv[0] == "docker" else STDOUT_TAIL_CHARS
        overflow = len(result.stdout) > stdout_limit
        stderr = result.stderr[-STDERR_TAIL_CHARS:].strip()
        if overflow:
            stderr = f"CLI stdout exceeded {stdout_limit} characters; probe output is incomplete. {stderr}"[:STDERR_TAIL_CHARS]
        return {
            "argv": argv,
            "exit_status": None if overflow else result.returncode,
            "stdout_tail": result.stdout[-stdout_limit:].strip(),
            "stderr_tail": stderr,
        }
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        return {"argv": argv, "exit_status": None, "stdout_tail": "", "stderr_tail": str(exc)}
