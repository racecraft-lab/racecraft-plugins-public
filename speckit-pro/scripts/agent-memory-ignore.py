#!/usr/bin/env python3
"""Check or repair a consumer repository's Claude local-memory ignore rule."""
from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path


RULE = "**/.claude/agent-memory-local/"
PROBE = "__speckit_agent_memory_probe__.md"


def git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, check=False, timeout=30,
    )


def git_paths(root: Path, *args: str) -> list[str]:
    result = git(root, *args)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.decode(errors='replace').strip()}")
    return [os.fsdecode(path) for path in result.stdout.split(b"\0") if path]


def ignore_bytes(path: Path) -> tuple[bytes, int]:
    if not path.exists() and not path.is_symlink():
        return b"", 0o644
    if path.is_symlink():
        raise RuntimeError(".gitignore is a symlink; refusing to read or replace it")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise RuntimeError(".gitignore is not a regular file")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            return stream.read(), stat.S_IMODE(info.st_mode)
    finally:
        os.close(fd)


def write_ignore(path: Path, content: bytes, mode: int) -> None:
    fd, temporary = tempfile.mkstemp(prefix=".gitignore.speckit-", dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if path.is_symlink():
            raise RuntimeError(".gitignore became a symlink; refusing to replace it")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def probe_locations(root: Path) -> list[str]:
    files = git_paths(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    parents = {""}
    for item in files:
        path = Path(item)
        if path.name == ".gitignore" and ".claude" not in path.parts:
            parents.add(path.parent.as_posix() if path.parent != Path(".") else "")
    for parent in parents:
        base = root / parent
        for candidate in (base / ".claude", base / ".claude/agent-memory-local"):
            if candidate.is_symlink():
                raise RuntimeError(f"memory path is a symlink: {candidate.relative_to(root)}")
    return sorted(f"{parent + '/' if parent else ''}.claude/agent-memory-local/{PROBE}" for parent in parents)


def unignored_probes(root: Path) -> list[str]:
    unignored: list[str] = []
    for path in probe_locations(root):
        result = git(root, "check-ignore", "--no-index", "-q", "--", path)
        if result.returncode == 1:
            unignored.append(path)
        elif result.returncode != 0:
            raise RuntimeError(f"git check-ignore failed for {path}: {result.stderr.decode(errors='replace').strip()}")
    return unignored


def tracked_memory(root: Path) -> list[str]:
    paths = git_paths(root, "ls-files", "--cached", "-z")
    return sorted(path for path in paths if any(
        Path(path).parts[i:i + 2] == (".claude", "agent-memory-local")
        for i in range(len(Path(path).parts) - 1)
    ))


def run(root: Path, mode: str) -> tuple[int, dict[str, object]]:
    root = root.resolve(strict=True)
    actual = git(root, "rev-parse", "--show-toplevel")
    if actual.returncode != 0 or Path(os.fsdecode(actual.stdout).strip()).resolve() != root:
        raise RuntimeError("--repo-root must name the Git worktree root")
    ignore = root / ".gitignore"
    original, permissions = ignore_bytes(ignore)
    missing = unignored_probes(root)
    changed = False
    if mode == "apply" and missing and RULE.encode() not in original.splitlines():
        separator = b"" if not original or original.endswith(b"\n") else b"\n"
        write_ignore(ignore, original + separator + RULE.encode() + b"\n", permissions)
        changed = True
        missing = unignored_probes(root)
    tracked = tracked_memory(root)
    report: dict[str, object] = {
        "status": "ok" if not missing and not tracked else "needs_attention",
        "changed": changed,
        "unignored_paths": missing,
        "tracked_memory": tracked,
        "remediation": "Add an effective recursive ignore rule; deliberately untrack listed memory files without deleting them." if missing or tracked else "",
    }
    return (0 if report["status"] == "ok" else 1), report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("check", "apply"), required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        code, result = run(args.repo_root, args.mode)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        code, result = 2, {"status": "error", "error": str(exc)}
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
