"""Read-only CLI queries with fixed argv, a per-caller allowlist and a timeout; hosts take only --version."""

from __future__ import annotations

import errno
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
HOSTS = ("claude", "codex")
# The operator's own install serves these, as it already does for the host agent and the runner's direct Git calls.
OPERATOR_CLIS = ("git", "gh")
SHARED_WRITE = stat.S_IWGRP | stat.S_IWOTH
Reach = Callable[[], frozenset[tuple[int, int]]]


def ignore_vanished(error: OSError) -> None:
    if not isinstance(error, FileNotFoundError):
        raise error


def worktree_reach(worktree: Path) -> frozenset[tuple[int, int]]:
    """Identify the inodes a write through a worktree name can change: shared regular files and symlink targets.

    A name or directory removed during the walk, a dangling link and a link loop reach nothing now.
    Any other unreadable part of the worktree fails closed.
    """
    reached = set()
    for directory, subdirectories, files in os.walk(worktree, onerror=ignore_vanished):
        for name in (*subdirectories, *files):
            path = os.path.join(directory, name)
            try:
                info = os.lstat(path)
                if stat.S_ISLNK(info.st_mode):
                    info = os.stat(path)
                elif not (stat.S_ISREG(info.st_mode) and info.st_nlink > 1):
                    continue
            except FileNotFoundError:
                continue
            except OSError as error:
                if error.errno != errno.ELOOP:
                    raise
                continue
            reached.add((info.st_dev, info.st_ino))
    return frozenset(reached)


def operator_installed(info: os.stat_result, chain: list[Path], reach: Reach) -> bool:
    """Only the operator's identity can change this file, and no worktree name reaches it or its lookup chain.

    Mode bits are read; ACLs are not, as before. A writer that relinks or rewrites the file
    after validation already runs as the operator who installed it, so the probe cannot stop it.
    """
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & SHARED_WRITE:
        return False
    identities = {(info.st_dev, info.st_ino)} | {(link.st_dev, link.st_ino) for link in map(os.stat, set(chain))}
    return not identities & reach()


def reject_mutable_probe_alias(info: os.stat_result, path: Path, *, host: bool) -> None:
    """A mutable inode cannot authenticate bytes used by a later child lookup.

    Reject ownership as well as effective write access: owners can chmod read-only
    files through a hardlink. Link counts and worktree inventories cannot establish
    protection, because an alias may be absent at validation and relinked later.
    Hosts additionally require protected namespaces; other CLIs retain their
    external-directory policy, where replacing names already requires external write access.
    """
    writable = info.st_uid == os.geteuid() or os.access(path, os.W_OK, effective_ids=True)
    if host and stat.S_ISDIR(info.st_mode) and writable:
        raise ValueError("CLI lookup cannot authenticate a mutable directory")
    if stat.S_ISREG(info.st_mode) and writable:
        raise ValueError("CLI lookup cannot authenticate a mutable executable inode")


def external_probe_path(path: Path, worktree: Path, links: int = 40, *, host: bool = False,
                        chain: list[Path] | None = None) -> Path:
    """Resolve links root-first; host lookups require protected ancestors at every hop.

    Protect the parent before observing a child: holding only an executable inode
    leaves directory replacement and the child's later PATH lookups unauthenticated.
    A same-identity writer must not own (and chmod) or effectively write any ancestor.
    `chain`, when given, collects every ancestor and link hop the lookup visits.
    """
    if links < 0 or path.is_relative_to(worktree):
        raise ValueError("CLI path traverses the worktree or too many symlinks")
    if path.parent == path:
        reject_mutable_probe_alias(path.lstat(), path, host=host)
        if chain is not None:
            chain.append(path)
        return path
    parent = external_probe_path(path.parent, worktree, links, host=host, chain=chain)
    candidate = parent.parent if path.name == ".." else parent / path.name
    if candidate.is_relative_to(worktree) or (candidate.is_dir() and candidate.samefile(worktree)):
        raise ValueError("CLI path traverses the worktree")
    if chain is not None:
        chain.append(candidate)
    if candidate.is_symlink():
        target = candidate.readlink()
        return external_probe_path(target if target.is_absolute() else parent / target, worktree, links - 1,
                                   host=host, chain=chain)
    if candidate.is_dir():
        reject_mutable_probe_alias(candidate.lstat(), candidate, host=host)
    return candidate


def validate_probe_directory(directory: Path, worktree: Path, *, host: bool, reach: Reach | None = None) -> None:
    """Require protected regular-file targets for every selected CLI and helper name.

    With `reach` (operator CLIs), an operator-installed file that no worktree name reaches also passes.
    """
    ancestors: list[Path] = []
    external_probe_path(directory, worktree, host=host, chain=ancestors)
    for entry in directory.iterdir():
        chain, path, info = [*ancestors, entry], entry, entry.lstat()
        if stat.S_ISLNK(info.st_mode):
            path = external_probe_path(entry, worktree, host=host, chain=chain)
            if not path.exists():
                continue
            info = path.stat()
        if reach is None or not operator_installed(info, chain, reach):
            reject_mutable_probe_alias(info, path, host=host)


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
    reach = functools.cache(functools.partial(worktree_reach, worktree)) if cli in OPERATOR_CLIS else None
    directories = []
    for entry in os.environ.get("PATH", os.defpath).split(os.pathsep):
        directory = Path(entry)
        if not directory.is_absolute() or directory.is_relative_to(root.absolute()):
            continue
        try:
            directory = directory.resolve(strict=True)
            target = external_probe_path(directory / cli, worktree, host=cli in HOSTS)
            validate_probe_directory(directory, worktree, host=cli in HOSTS, reach=reach)
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
        if argv[0] in HOSTS and argv[1:] != ["--version"]:
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
