"""Snapshot and evidence primitives shared by host and Docker verification: bounds, digests, the bounded input tree, and the workflow command binding."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import stat
from pathlib import Path
from typing import Any

from .canonical_json import canonical_bytes
from .execution_control import default_ledger_directory, evidence_directory


COMMAND_IDS = {"BUILD", "TYPECHECK", "LINT", "UNIT_TEST", "INTEGRATION_TEST", "FULL_VERIFY",
               "COMPLEXITY", "MUTATION", "DEPENDENCY_RULES"}


MAX_FILES = 50000
MAX_BYTES = 512 * 1024 * 1024


# Guards one verification command against a hang. A run has no wall-clock limit.
COMMAND_TIMEOUT_SECONDS = 7200
PROJECT_PROGRAMS = {"python", "python3", "node", "npm", "npx", "pnpm", "yarn", "bun", "cargo", "go",
                    "make", "pytest", "lint-imports", "uv", "ruff", "mypy"}


def digest(value: Any) -> str:
    return sha(canonical_bytes(value))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bounded_regular(path: Path, limit: int, description: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise ValueError(f"{description} is not a bounded regular file")
        body = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    identity = lambda info: (info.st_dev, info.st_ino, info.st_mode, info.st_size,
                             info.st_mtime_ns, info.st_ctime_ns)
    if len(body) > limit or identity(before) != identity(after):
        raise ValueError(f"{description} changed while being read")
    return body


def workflow_argv(workflow: Path, command_id: str) -> list[str]:
    """Parse direct workflow arguments without resolving a host toolchain."""
    if command_id not in COMMAND_IDS:
        raise ValueError("command_id must select a non-mutating PROJECT_COMMANDS slot")
    text = workflow.read_text(encoding="utf-8")
    blocks = re.findall(r"^## PROJECT_COMMANDS\s*\n```json\s*\n(.*?)\n```", text, re.M | re.S)
    if len(blocks) != 1:
        raise ValueError("persist one PROJECT_COMMANDS JSON section in the workflow first")
    commands = json.loads(blocks[0])
    command = commands.get(command_id) if isinstance(commands, dict) else None
    if not isinstance(command, str) or not command.strip() or command == "N/A":
        raise ValueError("selected PROJECT_COMMANDS slot is unavailable")
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    argv = list(lexer)
    if not argv or any(set(arg) & set(";&|<>`\n") for arg in argv) or any("$(" in arg for arg in argv):
        raise ValueError("compound or interpolated commands require ordinary native verification")
    if any(Path(arg).is_absolute() for arg in argv[1:]):
        raise ValueError("absolute command inputs escape the isolated snapshot")
    if any(".." in Path(arg).parts for arg in argv[1:]):
        raise ValueError("parent-relative command inputs escape the isolated snapshot")
    return argv


def evidence_directories(workflow_name: str) -> set[str]:
    """The current evidence directory plus the earlier doubled `.process/.process` one, still read."""
    return {evidence_directory(workflow_name), (Path(workflow_name).parent / ".process/verification").as_posix()}


def tree_bytes(root: Path, workflow_name: str) -> dict[str, tuple[int, bytes | None]]:
    excluded = {*evidence_directories(workflow_name), default_ledger_directory(workflow_name),
                (Path(workflow_name).parent / ".process/execution-control").as_posix()}
    files: dict[str, tuple[int, bytes | None]] = {}
    walk_errors: list[OSError] = []
    total = 0
    for directory, names, filenames in os.walk(root, followlinks=False, onerror=walk_errors.append):
        base = Path(directory)
        files[base.relative_to(root).as_posix()] = (base.stat().st_mode & 0o7777, None)
        if len(files) > MAX_FILES:
            raise ValueError("input closure exceeds bounded snapshot; use ordinary verification")
        for name in list(names):
            path = base / name
            relative = path.relative_to(root).as_posix()
            if name == ".git" or relative in excluded:
                names.remove(name)
            elif path.is_symlink():
                raise ValueError("symlink input closure requires ordinary verification")
        for name in sorted(filenames):
            path = base / name
            relative = path.relative_to(root).as_posix()
            if relative in excluded or name == ".git":
                continue
            if path.is_symlink() or not path.is_file():
                raise ValueError("non-regular input closure requires ordinary verification")
            data = path.read_bytes()
            files[relative] = (path.stat().st_mode & 0o7777, data)
            total += len(data)
            if len(files) > MAX_FILES or total > MAX_BYTES:
                raise ValueError("input closure exceeds bounded snapshot; use ordinary verification")
    if walk_errors:
        raise ValueError("unreadable input closure requires ordinary verification") from walk_errors[0]
    return files


def tree_digest(files: dict[str, tuple[int, bytes | None]]) -> str:
    return digest({name: {"mode": mode, "sha256": sha(data) if data is not None else None}
                   for name, (mode, data) in sorted(files.items())})


def runner_binding() -> str:
    runner_root = Path(__file__).parent
    runner_files = {source.relative_to(runner_root).as_posix(): sha(source.read_bytes())
                    for source in runner_root.rglob("*") if source.is_file() and source.suffix in {".py", ".json"}}
    return digest(runner_files)
