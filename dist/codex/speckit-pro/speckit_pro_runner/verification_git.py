"""Explicit original Git metadata inputs for unqualified Docker verification.

This is a bounded read-only metadata profile, not a clone or a native isolation
receipt. It does not inherit host globals or hook programs, or qualify
relocation of every Git dependency. Known unsupported dependencies are refused.
Layout reference: https://git-scm.com/docs/gitrepository-layout
"""
from __future__ import annotations

import configparser
from contextlib import ExitStack
import os
from pathlib import Path
import re
import stat
from typing import Any
from urllib.parse import urlsplit

from .verification_records import MAX_BYTES, MAX_FILES, digest, sha, tree_digest

COMMON_INPUTS = ("objects", "refs", "info", "packed-refs", "config")
PRIVATE_INPUTS = ("HEAD", "index", "ORIG_HEAD", "FETCH_HEAD", "config.worktree")
LIMITATIONS = ["git_metadata_profile_not_independently_qualified", "host_global_configuration_not_inherited",
               "hook_programs_and_external_tools_not_captured", "reflogs_and_worktree_topology_not_relocated",
               "nested_git_repositories_not_captured"]


def read_git_file(path: Path, limit: int) -> bytes:
    """Read only bounded regular files, without following any path symlinks."""
    if not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise ValueError("Git metadata requires no-follow directory access; use ordinary verification")
    with ExitStack() as stack:
        descriptor = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY)
        stack.callback(os.close, descriptor)
        for part in path.parts[1:-1]:
            descriptor = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            stack.callback(os.close, descriptor)
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
                raise ValueError("Git input is not a bounded regular file")
            body = handle.read(limit + 1)
            after = os.fstat(handle.fileno())
    if len(body) > limit or (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError("Git input changed during capture or exceeds snapshot limit")
    return body


def git_directories(root: Path, settings: Any) -> tuple[Path, Path, dict[str, str]]:
    keys = {"common_directory", "worktree_directory"}
    if not isinstance(settings, dict) or set(settings) != keys:
        raise ValueError("git_snapshot requires explicit common_directory and worktree_directory")
    directories = []
    for key in ("common_directory", "worktree_directory"):
        value = settings[key]
        if not isinstance(value, str) or not value or "\x00" in value:
            raise ValueError("Git directory must be a canonical absolute path")
        path = Path(value)
        if not path.is_absolute() or path.resolve(strict=True) != path or not path.is_dir():
            raise ValueError("Git directory must be a canonical absolute directory")
        directories.append(path)
    common, private = directories
    gitfile = root / ".git"
    controls = {}
    if gitfile.is_symlink():
        raise ValueError("unsupported Git symlink layout")
    if gitfile.is_dir():
        if common != private or gitfile.resolve() != common:
            raise ValueError("explicit Git directories do not match repository")
    else:
        body = read_git_file(gitfile, 4096)
        text = body.decode("utf-8").strip()
        if not text.startswith("gitdir: ") or (root / text[8:]).resolve(strict=True) != private:
            raise ValueError("explicit Git worktree directory does not match gitfile")
        shared = read_git_file(private / "commondir", 4096)
        if (private / shared.decode("utf-8").strip()).resolve(strict=True) != common:
            raise ValueError("explicit Git common directory does not match commondir")
        controls = {"gitfile": sha(body), "commondir": sha(shared)}
    return common, private, controls


def check_git_configuration(body: bytes) -> None:
    """Admission only; Git receives the original configuration bytes unchanged."""
    parser = configparser.RawConfigParser(strict=False, allow_no_value=True)
    try:
        parser.read_string(body.decode("utf-8"))
    except (configparser.Error, UnicodeError) as exc:
        raise ValueError("unsupported Git configuration syntax") from exc
    if parser.defaults():
        raise ValueError("unsupported Git configuration defaults")
    for section in parser.sections():
        family = section.split(maxsplit=1)[0].lower()
        if not family.isalpha():
            raise ValueError("unsupported Git configuration section syntax")
        for option, raw_value in parser.items(section):
            key = f"{family}.{option}".lower()
            value = (raw_value or "").strip().strip('"')
            if family.startswith("include") or any(word in key for word in (
                    "credential", "password", "token", "extraheader", "signingkey")):
                raise ValueError("unsupported Git configuration: credential or include dependency")
            if key in {"core.worktree", "core.excludesfile", "core.attributesfile", "core.fsmonitor",
                       "core.sshcommand", "core.gitproxy", "core.askpass"} or family in {"filter", "diff"}:
                raise ValueError("unsupported Git configuration: external dependency")
            if family == "extensions" and option not in {"worktreeconfig", "objectformat"}:
                raise ValueError("unsupported Git configuration: repository extension")
            if family == "remote" and option in {"url", "pushurl"}:
                parsed = urlsplit(value)
                if parsed.query or parsed.fragment or parsed.password or (parsed.username and parsed.scheme != "ssh"):
                    raise ValueError("unsupported Git configuration: credential-bearing remote")
                if parsed.scheme not in {"https", "http", "ssh", "git", "file"} and not re.fullmatch(
                        r"(?:[A-Za-z0-9_-]+@)?[A-Za-z0-9.-]+:[^\s@]+", value):
                    raise ValueError("unsupported Git configuration: ambiguous remote syntax")


def metadata_paths(base: Path, names: tuple[str, ...]) -> list[Path]:
    paths = []
    pending = [base / name for name in names if (base / name).exists() or (base / name).is_symlink()]
    while pending:
        path = pending.pop()
        mode = path.lstat().st_mode
        if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise ValueError("unsupported Git non-regular metadata input")
        paths.append(path)
        if len(paths) > MAX_FILES:
            raise ValueError("Git input closure exceeds snapshot entry limit")
        if stat.S_ISDIR(mode):
            for child in path.iterdir():
                if len(paths) + len(pending) >= MAX_FILES:
                    raise ValueError("Git input closure exceeds snapshot entry limit")
                pending.append(child)
    return sorted(paths)


def capture_git_metadata(root: Path, settings: Any) -> tuple[dict[str, tuple[int, bytes | None]], dict[str, Any]]:
    """Capture selected original metadata; never authorize reuse or hidden reads."""
    root = root.resolve(strict=True)
    common, private, controls = git_directories(root, settings)
    for path in (common / "objects/info/alternates", common / "objects/info/http-alternates", common / "shallow"):
        if path.exists() or path.is_symlink():
            raise ValueError("unsupported Git external or shallow object store")
    if next(private.glob("sharedindex.*"), None) is not None:
        raise ValueError("unsupported Git split index")
    if private != common and (private / "refs").exists() and any((private / "refs").iterdir()):
        raise ValueError("unsupported Git per-worktree references")
    for required in (common / "config", common / "objects", common / "refs", private / "HEAD", private / "index"):
        if not required.exists():
            raise ValueError("unsupported Git metadata layout: required input missing")
    files: dict[str, tuple[int, bytes | None]] = {".git": (stat.S_IMODE(common.stat().st_mode), None)}
    sources = {}
    total = 0
    groups = ((common, COMMON_INPUTS), (private, PRIVATE_INPUTS))
    for base, names in groups:
        for path in metadata_paths(base, names):
            info = path.lstat()
            if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
                raise ValueError("unsupported Git non-regular metadata input")
            name = ".git/" + path.relative_to(base).as_posix()
            if name in files:
                raise ValueError("Git metadata relocation collision")
            configuration = name in {".git/config", ".git/config.worktree"}
            limit = min(MAX_BYTES - total, 65536) if configuration else MAX_BYTES - total
            body = read_git_file(path, limit) if stat.S_ISREG(info.st_mode) else None
            current = path.lstat()
            if any(getattr(info, field) != getattr(current, field) for field in (
                    "st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")):
                raise ValueError("Git metadata changed during capture")
            if body is not None:
                total += len(body)
            if configuration:
                if body is None or len(body) > 65536:
                    raise ValueError("unsupported Git configuration size")
                check_git_configuration(body)
            mode = stat.S_IMODE(info.st_mode)
            files[name] = (mode, body)
            sources[name] = {"source": str(path), "mode": mode, "sha256": sha(body) if body is not None else None}
            if len(files) > MAX_FILES:
                raise ValueError("Git input closure exceeds snapshot entry limit")
    binding = {"profile": "git-readonly-metadata/v1", "qualified": False,
               "layout": "plain" if common == private else "linked", "directories": dict(settings),
               "directory_modes": {"common": stat.S_IMODE(common.stat().st_mode),
                                   "worktree": stat.S_IMODE(private.stat().st_mode)},
               "control_files": controls, "snapshot_sha256": tree_digest(files),
               "source_binding_sha256": digest(sources), "entry_count": len(files),
               "limitations": list(LIMITATIONS)}
    return files, binding
