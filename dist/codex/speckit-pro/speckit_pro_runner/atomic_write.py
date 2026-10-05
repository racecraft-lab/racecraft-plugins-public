"""Write-target validation and snapshot-checked atomic file writes shared by runner core and helpers."""

from __future__ import annotations

import hashlib
import os
import stat
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .trusted_io import (
    is_relative_to,
    looks_like_windows_absolute_path,
    normalize_display,
    path_diagnostic,
    repo_relative,
    resolve_input_path,
)


class WritePreconditionChanged(OSError):
    """Raised when a write target no longer matches its captured snapshot."""


def atomic_write_cleanup_errors(exc: OSError) -> list[str]:
    errors = getattr(exc, "cleanup_errors", None)
    return errors if isinstance(errors, list) else []


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


def write_bytes_atomic(
    target: Path,
    content: bytes,
    *,
    trust_root: Path | None = None,
    mode: int | None = None,
    expected_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    created_dirs: list[str] = []
    if trust_root is None:
        target.parent.mkdir(parents=True, exist_ok=True)
        parent_fd = os.open(target.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0))
        target_name = target.name
    else:
        opened = open_safe_parent_fd(target, trust_root, create=True)
        if opened is None:
            raise OSError("target parent missing")
        parent_fd, target_name, created_dirs = opened
    failure: OSError | None = None
    result: dict[str, Any] | None = None
    try:
        result = write_bytes_atomic_at(parent_fd, target_name, content, AtomicWriteOptions(
            mode=mode, expected_snapshot=expected_snapshot, guard_target=trust_root is not None))
    except OSError as exc:
        failure = exc
        raise
    finally:
        try:
            os.close(parent_fd)
        except OSError as exc:
            if result is None:
                if failure is None:
                    raise
                failure.cleanup_errors = [*atomic_write_cleanup_errors(failure), f"parent_fd:{type(exc).__name__}"]
        if trust_root is not None and failure is not None and created_dirs:
            cleanup_errors = remove_created_parent_dirs(created_dirs, trust_root)
            if cleanup_errors:
                failure.cleanup_errors = [*atomic_write_cleanup_errors(failure), *cleanup_errors]
    return {"digest": result["digest"], "mode": result["mode"], "created_parent_dirs": created_dirs}


@dataclass(frozen=True)
class AtomicWriteOptions:
    mode: int | None = None
    expected_snapshot: dict[str, Any] | None = None
    guard_target: bool = True
    verify_content: bool = False
    post_publish_check: Callable[[], None] | None = None


def write_bytes_atomic_at(parent_fd: int, target_name: str, content: bytes,
                          options: AtomicWriteOptions) -> dict[str, Any]:
    """Publish and verify through held descriptors; preserve recovery entries on races."""
    tmp_name = f"{atomic_temporary_prefix(target_name)}{os.getpid()}-{uuid.uuid4().hex}"
    tmp_fd = -1
    failure: OSError | None = None
    applied_mode: int | None = None
    tmp_cleanup_errors: list[str] = []
    written_stat: os.stat_result | None = None
    replaced = False
    previous = preserve_previous_bytes_at(parent_fd, target_name) if options.verify_content else None
    try:
        try:
            if options.guard_target:
                ensure_safe_write_target_fd(parent_fd, target_name)
            existing_mode = options.mode if options.mode is not None else current_file_mode_fd(parent_fd, target_name)
            write_mode = existing_mode if existing_mode is not None else 0o666
            tmp_fd = os.open(
                tmp_name,
                os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                write_mode,
                dir_fd=parent_fd,
            )
            if existing_mode is not None:
                os.fchmod(tmp_fd, existing_mode)
            written_stat = os.fstat(tmp_fd)
            applied_mode = stat.S_IMODE(written_stat.st_mode)
            write_open_file(tmp_fd, content)
            if options.verify_content and read_open_file(tmp_fd, len(content)) != content:
                raise WritePreconditionChanged("temporary bytes changed before publication")
            if options.guard_target:
                ensure_safe_write_target_fd(parent_fd, target_name)
            if options.expected_snapshot is not None:
                ensure_write_target_matches_snapshot_fd(parent_fd, target_name, options.expected_snapshot)
            replaced = True
            os.replace(tmp_name, target_name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
            if options.verify_content:
                verify_written_file_at(parent_fd, target_name, content, written_stat)
                if options.post_publish_check is not None:
                    options.post_publish_check()
            try:
                os.fsync(parent_fd)
            except OSError:
                # Directory fsync is best-effort after replace; the atomic swap already succeeded.
                pass
        except (OSError, ValueError) as exc:
            if isinstance(exc, OSError):
                failure = exc
            if replaced and options.verify_content:
                recover_failed_publication_at(parent_fd, target_name, previous)
            raise
    finally:
        if previous is not None:
            os.close(previous[1])
            os.close(previous[0])
        try:
            if written_stat is not None:
                quarantine_entry_at(parent_fd, tmp_name, [written_stat.st_dev, written_stat.st_ino])
        except OSError:
            tmp_cleanup_errors.append(f"{tmp_name}:OSError")
        if tmp_fd >= 0:
            try:
                os.close(tmp_fd)
            except OSError:
                # Best-effort cleanup only; a close error cannot safely change the write outcome.
                pass
        if failure is not None and tmp_cleanup_errors:
            failure.cleanup_errors = [*atomic_write_cleanup_errors(failure), *tmp_cleanup_errors]
    return {"digest": hashlib.sha256(content).hexdigest(), "mode": applied_mode,
            "file_identity": [written_stat.st_dev, written_stat.st_ino]}


def atomic_temporary_prefix(target_name: str) -> str:
    return f".{target_name}.tmp-"


def open_recovery_directory_at(parent_fd: int) -> tuple[str, int]:
    directory = f".artifact-recovery-{uuid.uuid4().hex}"
    os.mkdir(directory, 0o700, dir_fd=parent_fd)
    return directory, os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)


def quarantine_entry_at(parent_fd: int, name: str, identity: list[int] | None = None,
                        expected_digest: str | None = None) -> str | None:
    """Capture before checking; retain entries because POSIX has no inode-conditional unlink."""
    opened = -1
    try:
        if identity is not None:
            try:
                opened = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent_fd)
            except FileNotFoundError:
                return None
            observed = os.fstat(opened)
            if not stat.S_ISREG(observed.st_mode) or [observed.st_dev, observed.st_ino] != identity:
                raise WritePreconditionChanged("cleanup entry identity changed; replacement preserved")
        directory, held = open_recovery_directory_at(parent_fd)
        try:
            try:
                os.rename(name, "entry", src_dir_fd=parent_fd, dst_dir_fd=held)
            except FileNotFoundError:
                return None
            if identity is not None:
                verify_captured_entry_at(held, parent_fd, name, identity, expected_digest)
            return f"{directory}/entry"
        finally:
            os.close(held)
    finally:
        if opened >= 0:
            os.close(opened)


def verify_captured_entry_at(held: int, parent_fd: int, name: str,
                             identity: list[int], expected_digest: str | None) -> None:
    try:
        captured = read_file_snapshot_at(held, "entry")
        if (not captured["exists"] or captured["file_identity"] != identity
                or expected_digest is not None and captured["digest"] != expected_digest):
            raise WritePreconditionChanged("cleanup entry identity or bytes changed during capture; replacement preserved")
    except OSError:
        restore_quarantined_entry_at(held, "entry", parent_fd, name)
        raise
    try:
        os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    raise WritePreconditionChanged("cleanup basename was replaced after capture; replacement preserved")


def restore_quarantined_entry_at(source_fd: int, source: str, parent_fd: int, name: str) -> None:
    """Restore without overwriting a concurrent entry; retain the recovery copy."""
    try:
        os.link(source, name, src_dir_fd=source_fd, dst_dir_fd=parent_fd, follow_symlinks=False)
    except FileExistsError:
        pass


def write_open_file(fd: int, content: bytes) -> None:
    with os.fdopen(os.dup(fd), "wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def verify_written_file_at(parent_fd: int, name: str, content: bytes, written: os.stat_result) -> None:
    final = read_file_snapshot_at(parent_fd, name, len(content))
    if (not final["exists"] or final["content"] != content
            or final["file_identity"] != [written.st_dev, written.st_ino]):
        raise WritePreconditionChanged("published artifact identity or bytes differ from the held temporary")


def read_open_file(fd: int, limit: int | None = None) -> bytes:
    """Read through the held file, leaving it open for subsequent identity checks."""
    before = os.fstat(fd)
    os.lseek(fd, 0, os.SEEK_SET)
    with os.fdopen(os.dup(fd), "rb") as stream:
        content = stream.read() if limit is None else stream.read(limit + 1)
    after = os.fstat(fd)
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise WritePreconditionChanged("file changed during descriptor read")
    return content


def preserve_previous_bytes_at(parent_fd: int, name: str) -> tuple[int, int] | None:
    snapshot = read_file_snapshot_at(parent_fd, name)
    if not snapshot["exists"]:
        return None
    _directory, held = open_recovery_directory_at(parent_fd)
    try:
        fd = os.open("previous", os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     snapshot["mode"], dir_fd=held)
        try:
            write_open_file(fd, snapshot["content"])
            return held, fd
        except BaseException:
            os.close(fd)
            raise
    except BaseException:
        os.close(held)
        raise


def recover_failed_publication_at(parent_fd: int, name: str, previous: tuple[int, int] | None) -> None:
    # Capture untrusted final bytes without deleting them, then restore only into an absent slot.
    quarantine_entry_at(parent_fd, name)
    if previous is not None:
        source_fd, file_fd = previous
        restore_quarantined_entry_at(source_fd, "previous", parent_fd, name)
        try:
            verify_restored_file_at(parent_fd, name, file_fd)
        except OSError:
            quarantine_entry_at(parent_fd, name)
            raise


def verify_restored_file_at(parent_fd: int, name: str, file_fd: int) -> None:
    final = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent_fd)
    try:
        written, observed = os.fstat(file_fd), os.fstat(final)
        if (written.st_dev, written.st_ino) != (observed.st_dev, observed.st_ino):
            raise WritePreconditionChanged("rollback slot changed; previous page retained in recovery")
    finally:
        os.close(final)


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


def ensure_safe_write_target_fd(parent_fd: int, name: str) -> None:
    if "/" in name or name in {"", ".", ".."}:
        raise OSError("unsafe target name")
    try:
        mode = os.stat(name, dir_fd=parent_fd, follow_symlinks=False).st_mode
    except FileNotFoundError:
        return
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
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
        snapshot = read_file_snapshot_at(parent_fd, target_name)
        return {**{key: snapshot[key] for key in ("exists", "content", "mode", "digest")},
                "created_parent_dirs": created_parent_dirs}
    finally:
        os.close(parent_fd)


def snapshot_write_target_fd(parent_fd: int, target_name: str) -> dict[str, Any]:
    snapshot = read_file_snapshot_at(parent_fd, target_name)
    return {key: snapshot[key] for key in ("exists", "content", "mode", "digest")}


def read_file_snapshot_at(parent_fd: int, target_name: str, max_bytes: int | None = None) -> dict[str, Any]:
    """Read a regular entry without following links or blocking on special files."""
    try:
        fd = os.open(target_name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0),
                     dir_fd=parent_fd)
    except FileNotFoundError:
        return {"exists": False, "content": None, "mode": None, "digest": None}
    try:
        file_stat = os.fstat(fd)
        if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
            raise OSError("unsafe existing target")
        if max_bytes is not None and file_stat.st_size > max_bytes:
            raise OSError("artifact page exceeds its byte limit")
        with os.fdopen(fd, "rb") as stream:
            fd = -1
            content = stream.read() if max_bytes is None else stream.read(max_bytes + 1)
            after = os.fstat(stream.fileno())
        if max_bytes is not None and len(content) > max_bytes:
            raise OSError("artifact page exceeds its byte limit")
        if (file_stat.st_size, file_stat.st_mtime_ns, file_stat.st_ctime_ns) != (
                after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise WritePreconditionChanged("artifact changed during its read")
        current = os.stat(target_name, dir_fd=parent_fd, follow_symlinks=False)
        if (current.st_dev, current.st_ino) != (file_stat.st_dev, file_stat.st_ino) or not stat.S_ISREG(current.st_mode):
            raise WritePreconditionChanged("artifact identity changed during its read")
    finally:
        if fd >= 0:
            os.close(fd)
    return {
        "exists": True,
        "content": content,
        "mode": stat.S_IMODE(file_stat.st_mode),
        "digest": hashlib.sha256(content).hexdigest(),
        "file_identity": [file_stat.st_dev, file_stat.st_ino],
    }


def write_target_matches_snapshot(current: dict[str, Any], expected: dict[str, Any]) -> bool:
    expected_exists = bool(expected.get("exists"))
    if expected_exists != bool(current.get("exists")):
        return False
    if not expected_exists:
        return True
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
