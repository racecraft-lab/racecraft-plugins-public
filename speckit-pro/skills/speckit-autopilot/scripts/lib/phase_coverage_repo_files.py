"""Read repository files without following links or leaving the repository root."""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path, PurePosixPath


WINDOWS_ABSOLUTE_PATH_RE = re.compile(r"^[A-Za-z]:")


MAX_REPO_FILE_BYTES = 32 * 1024 * 1024


HAS_DESCRIPTOR_RELATIVE_IO = (
    os.name != "nt"
    and bool(getattr(os, "O_NOFOLLOW", 0))
    and os.open in os.supports_dir_fd
    and os.stat in os.supports_dir_fd
    and os.stat in os.supports_follow_symlinks
)


def _repository_root(path: Path) -> Path | None:
    # Resolve before walking, so whether a root is found depends on where the file
    # *is* rather than on how the caller spelled the path and which directory they
    # ran from. A relative path's parents chain terminates at the working
    # directory, which found no marker for a file sitting inside the repository.
    #
    # A resolution failure is treated as an unresolvable root, which is the same
    # verdict this function already returns when no marker is found and which the
    # callers already handle. The alternative is an exception escaping into
    # ``main()``, which catches only ``ValidationError`` and would print a
    # traceback where the autopilot expects a JSON report. Reaching this today
    # requires the state file to be readable while its own path will not resolve,
    # because ``load_state`` runs first; that ordering is a property of the caller
    # rather than of this function, so the guard does not depend on it holding.
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError):
        return None
    for candidate in (resolved.parent, *resolved.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _repo_file(repo_root: Path, raw_path: object) -> Path | None:
    if not _is_normalized_repo_path(raw_path):
        return None
    relative = Path(str(raw_path))
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None
    return resolved


def _stable_file_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        metadata.st_nlink,
    )


def _stable_directory_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
    )


def _normalized_absolute_path(path: Path) -> str:
    return os.path.normcase(os.path.abspath(path))


def _windows_final_path_from_descriptor(descriptor: int) -> Path:
    try:
        import ctypes
        import msvcrt
        from ctypes import wintypes
    except ImportError as exc:  # pragma: no cover - available on supported Windows Python
        raise OSError("repository file handle inspection is unavailable") from exc
    get_final_path = ctypes.WinDLL("kernel32", use_last_error=True).GetFinalPathNameByHandleW
    get_final_path.argtypes = [
        wintypes.HANDLE,
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
    ]
    get_final_path.restype = wintypes.DWORD
    handle = wintypes.HANDLE(msvcrt.get_osfhandle(descriptor))
    required = get_final_path(handle, None, 0, 0)
    if required == 0:
        raise OSError("repository file handle could not be resolved")
    buffer = ctypes.create_unicode_buffer(required + 1)
    written = get_final_path(handle, buffer, len(buffer), 0)
    if written == 0 or written >= len(buffer):
        raise OSError("repository file handle could not be resolved")
    value = buffer.value
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    return Path(value)


def _repo_path_snapshot(
    source: Path,
    root: Path,
    relative: Path,
) -> tuple[tuple[int, ...], list[tuple[int, ...]], os.stat_result, Path]:
    canonical_root = root.resolve(strict=True)
    canonical_source = source.resolve(strict=True)
    if _normalized_absolute_path(canonical_root) != _normalized_absolute_path(root):
        raise OSError("repository root must be a real directory")
    if _normalized_absolute_path(canonical_source) != _normalized_absolute_path(source):
        raise OSError("repository file path must not contain symlinks")
    canonical_source.relative_to(canonical_root)
    root_metadata = os.stat(root, follow_symlinks=False)
    if not stat.S_ISDIR(root_metadata.st_mode):
        raise OSError("repository root must be a real directory")
    directory_identities: list[tuple[int, ...]] = []
    current = root
    for component in relative.parts[:-1]:
        current /= component
        metadata = os.stat(current, follow_symlinks=False)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise OSError("repository path components must be real directories")
        directory_identities.append(_stable_directory_identity(metadata))
    pathname = os.stat(source, follow_symlinks=False)
    if not stat.S_ISREG(pathname.st_mode) or stat.S_ISLNK(pathname.st_mode):
        raise OSError("repository file must be a regular non-symlink file")
    return (
        _stable_directory_identity(root_metadata),
        directory_identities,
        pathname,
        canonical_source,
    )


def _read_repo_file_by_handle(
    source: Path,
    root: Path,
    relative: Path,
    max_bytes: int,
) -> bytes:
    root_identity, directory_identities, pathname_before, canonical_source = (
        _repo_path_snapshot(source, root, relative)
    )
    flags = (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_NOINHERIT", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    descriptor = os.open(source, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise OSError("repository file must be regular")
        if _stable_file_identity(pathname_before) != _stable_file_identity(before):
            raise OSError("repository file changed before it was opened")
        if os.name == "nt" and (
            _normalized_absolute_path(_windows_final_path_from_descriptor(descriptor))
            != _normalized_absolute_path(canonical_source)
        ):
            raise OSError("repository file handle escaped its approved path")
        if before.st_size > max_bytes:
            raise OSError("repository file exceeds the maximum size")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, max_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise OSError("repository file exceeds the maximum size")
        after = os.fstat(descriptor)
        if _stable_file_identity(after) != _stable_file_identity(before) or total != after.st_size:
            raise OSError("repository file changed while it was being read")
        current_root, current_directories, current_pathname, current_canonical = (
            _repo_path_snapshot(source, root, relative)
        )
        if (
            current_root != root_identity
            or current_directories != directory_identities
            or _stable_file_identity(current_pathname) != _stable_file_identity(after)
            or _normalized_absolute_path(current_canonical)
            != _normalized_absolute_path(canonical_source)
        ):
            raise OSError("repository file path changed while it was being read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _open_directory_chain(
    root: Path, relative: Path, directory_flags: int, descriptors: list[int],
) -> tuple[int, list[tuple[int, ...]]]:
    """Open the root and each parent directory of `relative`, one descriptor per level.

    Every opened descriptor is appended to `descriptors` so the caller closes it.
    Returns the innermost descriptor and each level's stable identity.
    """
    root_before = os.stat(root, follow_symlinks=False)
    if not stat.S_ISDIR(root_before.st_mode):
        raise OSError("repository root must be a real directory")
    root_descriptor = os.open(root, directory_flags)
    descriptors.append(root_descriptor)
    root_open = os.fstat(root_descriptor)
    if _stable_directory_identity(root_before) != _stable_directory_identity(root_open):
        raise OSError("repository root changed before it was opened")
    identities = [_stable_directory_identity(root_open)]
    parent_descriptor = root_descriptor
    for component in relative.parts[:-1]:
        component_before = os.stat(component, dir_fd=parent_descriptor, follow_symlinks=False)
        if not stat.S_ISDIR(component_before.st_mode):
            raise OSError("repository path components must be real directories")
        child_descriptor = os.open(component, directory_flags, dir_fd=parent_descriptor)
        child_open = os.fstat(child_descriptor)
        if _stable_directory_identity(component_before) != _stable_directory_identity(child_open):
            os.close(child_descriptor)
            raise OSError("repository directory changed before it was opened")
        descriptors.append(child_descriptor)
        identities.append(_stable_directory_identity(child_open))
        parent_descriptor = child_descriptor
    return parent_descriptor, identities


def _read_stable_file(
    filename: str, parent_descriptor: int, file_flags: int, max_bytes: int,
) -> tuple[bytes, os.stat_result]:
    """Read one regular file under `parent_descriptor` and prove it did not change while read."""
    pathname_before = os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
    if not stat.S_ISREG(pathname_before.st_mode):
        raise OSError("repository file must be a regular non-symlink file")
    descriptor = os.open(filename, file_flags, dir_fd=parent_descriptor)
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or _stable_file_identity(pathname_before) != _stable_file_identity(before)
        ):
            raise OSError("repository file changed before it was opened")
        if before.st_size > max_bytes:
            raise OSError("repository file exceeds the maximum size")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, max_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise OSError("repository file exceeds the maximum size")
        after = os.fstat(descriptor)
        current = os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
        if (
            _stable_file_identity(after) != _stable_file_identity(before)
            or _stable_file_identity(current) != _stable_file_identity(after)
            or total != after.st_size
        ):
            raise OSError("repository file changed while it was being read")
        return b"".join(chunks), after
    finally:
        os.close(descriptor)


def _verify_directory_chain(
    root: Path,
    relative: Path,
    directory_flags: int,
    identities: list[tuple[int, ...]],
    after: os.stat_result,
) -> None:
    """Re-walk the path from the root and fail if any directory or the file was swapped."""
    verifier_descriptors: list[int] = []
    try:
        root_current = os.stat(root, follow_symlinks=False)
        verifier = os.open(root, directory_flags)
        verifier_descriptors.append(verifier)
        if (
            _stable_directory_identity(root_current) != identities[0]
            or _stable_directory_identity(os.fstat(verifier)) != identities[0]
        ):
            raise OSError("repository root changed while it was being read")
        for component, expected_identity in zip(relative.parts[:-1], identities[1:], strict=True):
            next_descriptor = os.open(component, directory_flags, dir_fd=verifier)
            verifier_descriptors.append(next_descriptor)
            if _stable_directory_identity(os.fstat(next_descriptor)) != expected_identity:
                raise OSError("repository directory changed while it was being read")
            verifier = next_descriptor
        current_path = os.stat(relative.parts[-1], dir_fd=verifier, follow_symlinks=False)
        if _stable_file_identity(current_path) != _stable_file_identity(after):
            raise OSError("repository file path changed while it was being read")
    finally:
        for verifier_descriptor in reversed(verifier_descriptors):
            os.close(verifier_descriptor)


def _read_repo_file_by_descriptor(
    source: Path,
    root: Path,
    relative: Path,
    max_bytes: int,
) -> bytes:
    nofollow = os.O_NOFOLLOW
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | nofollow
        | getattr(os, "O_DIRECTORY", 0)
    )
    file_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | nofollow
        | getattr(os, "O_NONBLOCK", 0)
    )
    directory_descriptors: list[int] = []
    try:
        parent_descriptor, identities = _open_directory_chain(
            root, relative, directory_flags, directory_descriptors,
        )
        content, after = _read_stable_file(
            relative.parts[-1], parent_descriptor, file_flags, max_bytes,
        )
        _verify_directory_chain(root, relative, directory_flags, identities, after)
        return content
    finally:
        for directory_descriptor in reversed(directory_descriptors):
            os.close(directory_descriptor)


def _read_repo_bytes(
    repo_root: Path,
    raw_path: object,
    *,
    max_bytes: int = MAX_REPO_FILE_BYTES,
) -> bytes | None:
    if not _is_normalized_repo_path(raw_path):
        return None
    root = Path(os.path.abspath(repo_root))
    relative = Path(*PurePosixPath(str(raw_path)).parts)
    source = root / relative
    try:
        if HAS_DESCRIPTOR_RELATIVE_IO:
            return _read_repo_file_by_descriptor(source, root, relative, max_bytes)
        return _read_repo_file_by_handle(source, root, relative, max_bytes)
    except (OSError, RuntimeError, ValueError):
        return None


def _is_normalized_repo_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    if value.startswith("/") or WINDOWS_ABSOLUTE_PATH_RE.match(value):
        return False
    path = PurePosixPath(value)
    return path.as_posix() == value and all(part not in {"", ".", ".."} for part in path.parts)
