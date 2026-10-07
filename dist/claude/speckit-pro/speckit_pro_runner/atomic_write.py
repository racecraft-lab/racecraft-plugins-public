"""Write-target validation and snapshot-checked atomic file writes shared by runner core and helpers."""

from __future__ import annotations

import ctypes
import errno
import functools
import hashlib
import os
import stat
import sys
import uuid
import collections.abc
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .trusted_io import (
    is_relative_to,
    looks_like_windows_absolute_path,
    normalize_display,
    path_diagnostic,
    repo_relative,
    read_tree_entry,
    resolve_input_path,
    TreeEntryReadOptions,
)


class WritePreconditionChanged(OSError):
    """Raised when a write target no longer matches its captured snapshot."""


class AtomicSwapUnavailable(OSError):
    """The platform or filesystem cannot swap two names atomically, so a checked write is refused, never downgraded."""


class AtomicWriteInterrupted(OSError):
    """A write may have reached disk; any displaced temporary entry must survive cleanup."""


def atomic_write_cleanup_errors(exc: OSError) -> list[str]:
    errors = getattr(exc, "cleanup_errors", None)
    return errors if isinstance(errors, list) else []


def cleanup_temporary_entry(parent_fd: int, name: str, failure: OSError | None) -> list[str]:
    """Remove an owned temporary entry; a failed rollback transfers it to the competing writer."""
    if isinstance(failure, AtomicWriteInterrupted):
        return []
    try:
        os.unlink(name, dir_fd=parent_fd)
    except FileNotFoundError:
        return []  # Successful replacement already removed the temporary name.
    except OSError:
        return [f"{name}:OSError"]
    return []


def validate_target_path(raw: str, repo_root: Path) -> dict[str, Any] | None:
    if "\x00" in raw:
        return path_diagnostic("invalid_input", "path contains a NUL byte", {"field": "target"})
    if looks_like_windows_absolute_path(raw) and os.name != "nt":
        return path_diagnostic(
            "unsupported_path",
            "path escapes the repo/plugin trust boundary",
            {"field": "target", "path": normalize_display(raw)},
        )
    target = resolve_input_path(raw, repo_root)
    resolved = target.resolve(strict=False)
    if not is_relative_to(resolved, repo_root):
        return path_diagnostic(
            "unsupported_path",
            "path escapes the repo/plugin trust boundary",
            {"field": "target", "path": normalize_display(raw)},
        )
    if target.is_symlink():
        return path_diagnostic(
            "unsupported_path",
            "mutation target must not be a symlink",
            {"field": "target", "path": repo_relative(target, repo_root)},
        )
    if target.exists() and not target.is_file():
        return path_diagnostic(
            "unsupported_path",
            "mutation target must be a regular file path",
            {"field": "target", "path": repo_relative(target, repo_root)},
        )
    parent = target.parent
    if not is_relative_to(parent.resolve(strict=False), repo_root):
        return path_diagnostic(
            "unsupported_path",
            "mutation target parent escapes the repo/plugin trust boundary",
            {"field": "target", "path": normalize_display(raw)},
        )
    current = parent
    while is_relative_to(current.resolve(strict=False), repo_root):
        if current.exists():
            if current.is_symlink():
                return path_diagnostic(
                    "unsupported_path",
                    "mutation target parent must not be a symlink",
                    {"field": "target", "path": repo_relative(current, repo_root)},
                )
            if not current.is_dir():
                return path_diagnostic(
                    "unsupported_path",
                    "mutation target parent must be a directory",
                    {"field": "target", "path": repo_relative(current, repo_root)},
                )
        if current == repo_root:
            break
        current = current.parent
    return None


def write_file_atomic(
    target: Path,
    content: str,
    *,
    trust_root: Path | None = None,
    expected_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return write_bytes_atomic(
        target,
        ensure_final_newline(content).encode("utf-8"),
        trust_root=trust_root,
        expected_snapshot=expected_snapshot,
    )


@dataclass(frozen=True)
class WriteBinding:
    """A caller-held directory and publication preconditions; the writer duplicates its descriptor."""

    parent_fd: int
    single_link: bool = False
    validate_parent: collections.abc.Callable[[], None] | None = None


@dataclass(frozen=True)
class AtomicWriteOptions:
    trust_root: Path | None = None
    mode: int | None = None
    expected_snapshot: dict[str, Any] | None = None
    binding: WriteBinding | None = None


@dataclass
class _AtomicWriteState:
    parent_fd: int
    target_name: str
    temporary_name: str
    created_dirs: list[str]
    temporary_fd: int = -1
    failure: OSError | None = None
    replaced: bool = False
    applied_mode: int | None = None
    identity: tuple[int, int, int] | None = None


def _open_atomic_write_state(target: Path, options: AtomicWriteOptions) -> _AtomicWriteState:
    created_dirs: list[str] = []
    if options.binding is not None:
        parent_fd = os.dup(options.binding.parent_fd)
        target_name = target.name
        temporary_name = f".{target_name}.tmp-{os.getpid()}-{uuid.uuid4().hex}"
    elif options.trust_root is None:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary_name = f".{target.name}.tmp-{os.getpid()}-{uuid.uuid4().hex}"
        parent_fd = os.open(target.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0))
        target_name = target.name
    else:
        opened = open_safe_parent_fd(target, options.trust_root, create=True)
        if opened is None:
            raise OSError("target parent missing")
        parent_fd, target_name, created_dirs = opened
        temporary_name = f".{target_name}.tmp-{os.getpid()}-{uuid.uuid4().hex}"
    return _AtomicWriteState(parent_fd, target_name, temporary_name, created_dirs)


def _check_atomic_write_parent(state: _AtomicWriteState, options: AtomicWriteOptions) -> None:
    expected_snapshot = options.expected_snapshot
    expected_parent = expected_snapshot.get("parent") if expected_snapshot is not None else None
    if expected_parent is not None and file_identity(os.fstat(state.parent_fd)) != tuple(expected_parent):
        raise WritePreconditionChanged("write target directory changed after snapshot capture")
    if options.trust_root is not None:
        binding = options.binding
        if binding is not None and binding.single_link:
            ensure_safe_write_target_fd(state.parent_fd, state.target_name, single_link=True)
        else:
            ensure_safe_write_target_fd(state.parent_fd, state.target_name)


def _create_atomic_temporary(state: _AtomicWriteState, options: AtomicWriteOptions) -> None:
    _check_atomic_write_parent(state, options)
    existing_mode = options.mode if options.mode is not None else current_file_mode_fd(state.parent_fd, state.target_name)
    write_mode = existing_mode if existing_mode is not None else 0o666
    state.temporary_fd = os.open(
        state.temporary_name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        write_mode,
        dir_fd=state.parent_fd,
    )
    if existing_mode is not None:
        os.fchmod(state.temporary_fd, existing_mode)
    temporary_stat = os.fstat(state.temporary_fd)
    state.applied_mode = stat.S_IMODE(temporary_stat.st_mode)
    state.identity = entry_identity(temporary_stat)


def _write_atomic_temporary(state: _AtomicWriteState, content: bytes, options: AtomicWriteOptions) -> None:
    binding = options.binding
    with os.fdopen(state.temporary_fd, "wb", closefd=binding is None) as handle:
        state.temporary_fd = handle.fileno() if binding is not None else -1
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    _check_atomic_write_parent(state, options)


def _validate_atomic_install(state: _AtomicWriteState, content: bytes, options: AtomicWriteOptions) -> None:
    expected_snapshot = options.expected_snapshot
    if expected_snapshot is not None:
        ensure_write_target_matches_snapshot_fd(state.parent_fd, state.target_name, expected_snapshot)
    binding = options.binding
    if binding is not None and binding.validate_parent is not None:
        binding.validate_parent()
    verify_bound_publication(binding, state.temporary_fd, state.temporary_name, content)


def _install_atomic_temporary(state: _AtomicWriteState, content: bytes, options: AtomicWriteOptions) -> None:
    _validate_atomic_install(state, content, options)
    expected_snapshot = options.expected_snapshot
    if not (
        expected_snapshot is not None
        and "identity" in expected_snapshot
        and install_checked(state.parent_fd, state.temporary_name, state.target_name, expected_snapshot)
    ):
        os.replace(state.temporary_name, state.target_name, src_dir_fd=state.parent_fd, dst_dir_fd=state.parent_fd)
    state.replaced = True
    try:
        os.fsync(state.parent_fd)
    except OSError:
        # Directory fsync is best-effort after replace; the atomic swap already succeeded.
        pass
    verify_bound_publication(options.binding, state.temporary_fd, state.target_name, content, installed=True)


def _publish_atomic_write(state: _AtomicWriteState, content: bytes, options: AtomicWriteOptions) -> None:
    _create_atomic_temporary(state, options)
    _write_atomic_temporary(state, content, options)
    _install_atomic_temporary(state, content, options)


def _cleanup_atomic_write(state: _AtomicWriteState, options: AtomicWriteOptions) -> None:
    if state.temporary_fd >= 0:
        try:
            os.close(state.temporary_fd)
        except OSError:
            # A close error cannot safely change the write outcome.
            pass
    temporary_cleanup_errors = cleanup_temporary_entry(state.parent_fd, state.temporary_name, state.failure)
    close_error: OSError | None = None
    try:
        os.close(state.parent_fd)
    except OSError as exc:
        close_error = exc
    if close_error is not None and not state.replaced:
        if state.failure is None:
            raise close_error
        cleanup_errors = atomic_write_cleanup_errors(state.failure)
        cleanup_errors.append(f"parent_fd:{type(close_error).__name__}")
        state.failure.cleanup_errors = cleanup_errors
    if state.failure is not None and not state.replaced and temporary_cleanup_errors:
        state.failure.cleanup_errors = [*atomic_write_cleanup_errors(state.failure), *temporary_cleanup_errors]
    if options.trust_root is not None and state.failure is not None and not state.replaced and state.created_dirs:
        cleanup_errors = remove_created_parent_dirs(state.created_dirs, options.trust_root)
        if cleanup_errors:
            state.failure.cleanup_errors = [*atomic_write_cleanup_errors(state.failure), *cleanup_errors]


def _write_atomic(target: Path, content: bytes, options: AtomicWriteOptions) -> dict[str, Any]:
    state = _open_atomic_write_state(target, options)
    try:
        try:
            _publish_atomic_write(state, content, options)
        except OSError as exc:
            state.failure = exc
            raise
    finally:
        _cleanup_atomic_write(state, options)
    return {
        "digest": hashlib.sha256(content).hexdigest(),
        "mode": state.applied_mode,
        "identity": state.identity,
        "created_parent_dirs": state.created_dirs,
    }


def write_bytes_atomic_with_options(
    target: Path,
    content: bytes,
    options: AtomicWriteOptions,
) -> dict[str, Any]:
    """Atomically replace a target using explicit write options."""
    return _write_atomic(target, content, options)


def write_bytes_atomic(
    target: Path,
    content: bytes,
    *,
    trust_root: Path | None = None,
    mode: int | None = None,
    expected_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Atomically replace a target with optional mode and snapshot checks."""
    return write_bytes_atomic_with_options(
        target,
        content,
        AtomicWriteOptions(trust_root, mode, expected_snapshot),
    )


def verify_bound_publication(binding: WriteBinding | None, held_fd: int, name: str, content: bytes,
                             installed: bool = False) -> None:
    """Bind a protected publication to the still-open written inode and exact bytes.

    A rename consumes a pathname, not a descriptor. Check both sides of that
    boundary and never certify a substituted or mutated entry as published.
    """
    if binding is None:
        return
    try:
        captured = read_tree_entry(
            binding.parent_fd,
            name,
            os.fstat(held_fd),
            options=TreeEntryReadOptions(byte_limit=len(content)),
        )
        if captured[Path()][1] != content:
            raise WritePreconditionChanged("written content changed before publication confirmation")
    except OSError as exc:
        if installed:
            raise AtomicWriteInterrupted("publication reached disk but its identity or content is unconfirmed") from exc
        raise


def file_identity(file_stat: os.stat_result) -> tuple[int, int]:
    """The device and inode pair: one file or directory whatever path reaches it."""
    return file_stat.st_dev, file_stat.st_ino


def entry_identity(file_stat: os.stat_result) -> tuple[int, int, int]:
    """A file's identity plus its link count, so a hard-link alias added to it counts as a change."""
    return file_stat.st_dev, file_stat.st_ino, file_stat.st_nlink


@functools.cache
def entry_swapper() -> collections.abc.Callable[[int, str, str], int] | None:
    """The platform call that atomically swaps two names in one directory, or None when there is none."""
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        if sys.platform == "darwin":
            call, flag = libc.renameatx_np, 0x2  # RENAME_SWAP
        elif sys.platform.startswith("linux"):
            call, flag = libc.renameat2, 0x2  # RENAME_EXCHANGE
        else:
            return None
    except (OSError, AttributeError):
        return None
    call.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    call.restype = ctypes.c_int

    def swap(directory_fd: int, first: str, second: str) -> int:
        if call(directory_fd, os.fsencode(first), directory_fd, os.fsencode(second), flag) == 0:
            return 0
        return ctypes.get_errno()

    return swap


def swap_entries(directory_fd: int, first: str, second: str) -> bool:
    """Swap two names atomically; False when this platform or filesystem cannot."""
    swapper = entry_swapper()
    if swapper is None:
        return False
    failure = swapper(directory_fd, first, second)
    if failure == 0:
        return True
    if failure in (errno.EINVAL, errno.ENOSYS, errno.ENOTSUP, errno.EOPNOTSUPP):
        return False
    raise OSError(failure, os.strerror(failure))


def install_checked(parent_fd: int, tmp_name: str, target_name: str, expected: dict[str, Any]) -> bool:
    """Put `tmp_name` at `target_name` only if what it displaces still matches `expected`.

    Refuses existing-target writes when the platform cannot perform the checked swap.
    """
    if not expected.get("exists"):
        try:
            os.link(tmp_name, target_name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        except FileExistsError as error:
            raise WritePreconditionChanged("write target appeared after snapshot capture") from error
        return True
    if not swap_entries(parent_fd, tmp_name, target_name):
        raise AtomicSwapUnavailable("checked atomic swap is unavailable on this filesystem; write refused")
    try:
        displaced_matches = write_target_matches_snapshot(snapshot_write_target_fd(parent_fd, tmp_name), expected)
    except OSError:
        displaced_matches = False
    if displaced_matches:
        return True
    rollback_error: OSError | None = None
    try:
        swapped_back = swap_entries(parent_fd, tmp_name, target_name)
    except OSError as error:
        swapped_back, rollback_error = False, error
    if swapped_back:
        raise WritePreconditionChanged("write target changed after snapshot capture")
    # The swap back failed or was refused, so the temporary name holds the competing entry; keep it, never delete it.
    kept = tmp_name.replace(".tmp-", ".kept-", 1)
    try:
        os.rename(tmp_name, kept, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
    except OSError:
        kept = tmp_name  # Recovery rename failed; this name now belongs to the competitor, not cleanup.
    raise AtomicWriteInterrupted(f"write reached disk but rollback failed; the competing entry is kept as {kept}") from rollback_error


def open_safe_parent_fd(target: Path, trust_root: Path, *, create: bool) -> tuple[int, str, list[str]] | None:
    trust_root = trust_root.resolve(strict=False)
    target = target if target.is_absolute() else trust_root / target
    try:
        relative = target.relative_to(trust_root)
    except ValueError as exc:
        raise OSError("target escapes trust root") from exc
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise OSError("unsafe target path")
    target_name = relative.parts[-1]
    if "/" in target_name or target_name in {"", ".", ".."}:
        raise OSError("unsafe target name")
    root_mode = trust_root.lstat().st_mode
    if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode):
        raise OSError("unsafe trust root")

    parent_fd = os.open(trust_root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0))
    created_dirs: list[str] = []
    current_rel = Path()
    try:
        for part in relative.parts[:-1]:
            current_rel = current_rel / part
            try:
                next_fd = os.open(
                    part,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=parent_fd,
                )
            except FileNotFoundError:
                if not create:
                    os.close(parent_fd)
                    return None
                os.mkdir(part, 0o777, dir_fd=parent_fd)
                created_dirs.append(current_rel.as_posix())
                next_fd = os.open(
                    part,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=parent_fd,
                )
            os.close(parent_fd)
            parent_fd = next_fd
    except Exception as exc:
        try:
            os.close(parent_fd)
        finally:
            if created_dirs:
                cleanup_errors = remove_created_parent_dirs(created_dirs, trust_root)
                if cleanup_errors:
                    exc.cleanup_errors = [*atomic_write_cleanup_errors(exc), *cleanup_errors]
        raise
    return parent_fd, target_name, created_dirs


def ensure_safe_write_target_fd(parent_fd: int, name: str, *, single_link: bool = False) -> None:
    if "/" in name or name in {"", ".", ".."}:
        raise OSError("unsafe target name")
    try:
        info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        mode = info.st_mode
    except FileNotFoundError:
        return
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode) or (single_link and info.st_nlink > 1):
        raise OSError("unsafe existing target")


def current_file_mode_fd(parent_fd: int, name: str) -> int | None:
    try:
        file_stat = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
        raise OSError("unsafe existing target")
    return stat.S_IMODE(file_stat.st_mode)


def snapshot_write_target(target: Path, repo_root: Path) -> dict[str, Any]:
    """The descriptor snapshot by path, plus the parents a write would create; it keeps no file identity."""
    created_parent_dirs = missing_parent_dirs(target, repo_root)
    opened = open_safe_parent_fd(target, repo_root, create=False)
    if opened is None:
        return {
            "exists": False,
            "content": None,
            "mode": None,
            "digest": None,
            "created_parent_dirs": created_parent_dirs,
        }
    parent_fd, target_name, _created_dirs = opened
    try:
        snapshot = snapshot_write_target_fd(parent_fd, target_name)
    finally:
        os.close(parent_fd)
    # Path snapshots stay content preconditions, as their callers have always relied on.
    snapshot.pop("identity")
    return {**snapshot, "created_parent_dirs": created_parent_dirs}


def snapshot_write_target_fd(parent_fd: int, target_name: str) -> dict[str, Any]:
    try:
        fd = os.open(target_name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0), dir_fd=parent_fd)
    except FileNotFoundError:
        return {"exists": False, "content": None, "mode": None, "digest": None, "identity": None}
    try:
        file_stat = os.fstat(fd)
        if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
            raise OSError("unsafe existing target")
        with os.fdopen(fd, "rb") as stream:
            fd = -1
            content = stream.read()
    finally:
        if fd >= 0:
            os.close(fd)
    return {
        "exists": True,
        "content": content,
        "mode": stat.S_IMODE(file_stat.st_mode),
        "digest": hashlib.sha256(content).hexdigest(),
        "identity": entry_identity(file_stat),
    }


def write_target_matches_snapshot(current: dict[str, Any], expected: dict[str, Any]) -> bool:
    expected_exists = bool(expected.get("exists"))
    if expected_exists != bool(current.get("exists")):
        return False
    if not expected_exists:
        return True
    if "identity" in expected and current.get("identity") != expected["identity"]:
        return False
    return current.get("digest") == expected.get("digest") and current.get("mode") == expected.get("mode")


def ensure_write_target_matches_snapshot_fd(parent_fd: int, target_name: str, expected: dict[str, Any]) -> None:
    if not write_target_matches_snapshot(snapshot_write_target_fd(parent_fd, target_name), expected):
        raise WritePreconditionChanged("write target changed after snapshot capture")


def missing_parent_dirs(target: Path, repo_root: Path) -> list[str]:
    repo_root = repo_root.resolve(strict=False)
    target = target if target.is_absolute() else repo_root / target
    try:
        relative = target.relative_to(repo_root)
    except ValueError as exc:
        raise OSError("target escapes trust root") from exc
    missing: list[str] = []
    current = repo_root
    missing_started = False
    for part in relative.parts[:-1]:
        current = current / part
        rel = current.relative_to(repo_root).as_posix()
        if missing_started:
            missing.append(rel)
            continue
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            missing_started = True
            missing.append(rel)
            continue
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise OSError("unsafe parent path")
    return missing


def remove_created_parent_dirs(relative_dirs: list[str], repo_root: Path) -> list[str]:
    errors: list[str] = []
    for rel in reversed(relative_dirs):
        if not isinstance(rel, str) or not rel:
            continue
        target = resolve_input_path(rel, repo_root)
        try:
            opened = open_safe_parent_fd(target, repo_root, create=False)
            if opened is None:
                continue
            parent_fd, target_name, _created_dirs = opened
            try:
                os.rmdir(target_name, dir_fd=parent_fd)
                try:
                    os.fsync(parent_fd)
                except OSError:
                    # Directory fsync is best-effort after cleanup; rmdir already succeeded.
                    pass
            finally:
                os.close(parent_fd)
        except FileNotFoundError:
            continue
        except OSError as exc:
            errors.append(f"{rel}:{type(exc).__name__}")
    return errors


def ensure_final_newline(content: str) -> str:
    return content if content.endswith("\n") else f"{content}\n"
