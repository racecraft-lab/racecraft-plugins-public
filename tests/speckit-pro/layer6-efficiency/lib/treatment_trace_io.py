#!/usr/bin/env python3
"""Canonical JSON and descriptor-bound treatment input helpers."""

from __future__ import annotations

from contextlib import ExitStack as _ExitStack, contextmanager as _contextmanager

if __package__:
    from .treatment_trace_authority import *
else:
    from treatment_trace_authority import *


@_contextmanager
def _open_descriptor(path, flags, *, dir_fd=None):
    descriptor = os.open(path, flags, dir_fd=dir_fd)
    try:
        yield descriptor
    finally:
        os.close(descriptor)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _stable_file_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns,
        metadata.st_ctime_ns, stat.S_IMODE(metadata.st_mode), metadata.st_nlink,
    )


def _stable_directory_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode), stat.S_IMODE(metadata.st_mode)


def _normalized_path(path: Path) -> str:
    return os.path.normcase(os.path.abspath(path))


def _windows_final_path_from_descriptor(descriptor: int) -> Path:
    try:
        import ctypes
        import msvcrt
        from ctypes import wintypes
    except ImportError as exc:  # pragma: no cover - available on supported Windows Python
        raise ValueError("bounded input cannot inspect its Windows file handle") from exc
    get_final_path = ctypes.WinDLL("kernel32", use_last_error=True).GetFinalPathNameByHandleW
    get_final_path.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    get_final_path.restype = wintypes.DWORD
    handle = wintypes.HANDLE(msvcrt.get_osfhandle(descriptor))
    required = get_final_path(handle, None, 0, 0)
    if required == 0:
        raise ValueError("bounded input cannot resolve its Windows file handle")
    buffer = ctypes.create_unicode_buffer(required + 1)
    written = get_final_path(handle, buffer, len(buffer), 0)
    if written == 0 or written >= len(buffer):
        raise ValueError("bounded input cannot resolve its Windows file handle")
    value = buffer.value
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    return Path(value)


def _handle_bound_path_snapshot(source: Path, root: Path, relative: Path) -> tuple[
    tuple[int, ...], list[tuple[int, ...]], os.stat_result, Path,
]:
    try:
        canonical_root = root.resolve(strict=True)
        canonical_source = source.resolve(strict=True)
        if _normalized_path(canonical_root) != _normalized_path(root):
            raise ValueError("bounded input approved root must be a real directory")
        if _normalized_path(canonical_source) != _normalized_path(source):
            raise ValueError("bounded input path components must be real directories and the file non-symlink")
        canonical_source.relative_to(canonical_root)
        root_metadata = os.stat(root, follow_symlinks=False)
        if not stat.S_ISDIR(root_metadata.st_mode):
            raise ValueError("bounded input approved root must be a real directory")
        directory_identities: list[tuple[int, ...]] = []
        current = root
        for component in relative.parts[:-1]:
            current /= component
            metadata = os.stat(current, follow_symlinks=False)
            if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
                raise ValueError("bounded input path components must be real directories")
            directory_identities.append(_stable_directory_identity(metadata))
        pathname = os.stat(source, follow_symlinks=False)
    except OSError as exc:
        raise ValueError("bounded input must be a readable regular non-symlink file") from exc
    except ValueError:
        raise
    if not stat.S_ISREG(pathname.st_mode) or stat.S_ISLNK(pathname.st_mode) or pathname.st_nlink != 1:
        raise ValueError("bounded input must be a single-link regular non-symlink file")
    return _stable_directory_identity(root_metadata), directory_identities, pathname, canonical_source


def _read_bounded_regular_file_by_handle(source: Path, root: Path, relative: Path, max_bytes: int) -> bytes:
    root_identity, directory_identities, pathname_before, canonical_source = _handle_bound_path_snapshot(
        source, root, relative,
    )
    flags = (
        os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOINHERIT", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    descriptor: int | None = None
    try:
        descriptor = os.open(source, flags)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError("bounded input must be a single-link regular file")
        if _stable_file_identity(pathname_before) != _stable_file_identity(before):
            raise ValueError("bounded input pathname changed before it was read")
        if IS_WINDOWS and _normalized_path(_windows_final_path_from_descriptor(descriptor)) != _normalized_path(canonical_source):
            raise ValueError("bounded input Windows handle escaped its approved path")
        if before.st_size > max_bytes:
            raise ValueError("bounded input exceeds the maximum size")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, max_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("bounded input exceeds the maximum size")
        after = os.fstat(descriptor)
        if _stable_file_identity(after) != _stable_file_identity(before) or total != after.st_size:
            raise ValueError("bounded input changed while it was being read")
        current_root, current_directories, current_pathname, current_canonical = _handle_bound_path_snapshot(
            source, root, relative,
        )
        if (
            current_root != root_identity
            or current_directories != directory_identities
            or _stable_file_identity(current_pathname) != _stable_file_identity(after)
            or _normalized_path(current_canonical) != _normalized_path(canonical_source)
        ):
            raise ValueError("bounded input path changed while it was being read")
        return b"".join(chunks)
    except OSError as exc:
        raise ValueError("bounded input must be a readable regular non-symlink file") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _read_bounded_regular_file(path: Path, *, allowed_root: Path = ROOT,
                               max_bytes: int = MAX_INPUT_BYTES) -> bytes:
    source = Path(os.path.abspath(path)); root = Path(os.path.abspath(allowed_root))
    try:
        relative = source.relative_to(root)
    except ValueError as exc:
        raise ValueError("bounded input must remain inside its approved root") from exc
    if not relative.parts:
        raise ValueError("bounded input must name a file below its approved root")
    if not HAS_DESCRIPTOR_RELATIVE_IO:
        return _read_bounded_regular_file_by_handle(source, root, relative, max_bytes)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | nofollow | getattr(os, "O_DIRECTORY", 0)
    file_flags = (
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | nofollow
        | getattr(os, "O_NONBLOCK", 0)
    )
    directory_identities: list[tuple[int, ...]] = []
    with _ExitStack() as descriptors:
        try:
            root_before = os.stat(root, follow_symlinks=False)
            if not stat.S_ISDIR(root_before.st_mode):
                raise ValueError("bounded input approved root must be a real directory")
            root_descriptor = descriptors.enter_context(_open_descriptor(root, directory_flags))
            root_open = os.fstat(root_descriptor)
            if _stable_directory_identity(root_before) != _stable_directory_identity(root_open):
                raise ValueError("bounded input approved root changed before it was opened")
            directory_identities.append(_stable_directory_identity(root_open))
            parent_descriptor = root_descriptor
            for component in relative.parts[:-1]:
                component_before = os.stat(component, dir_fd=parent_descriptor, follow_symlinks=False)
                if not stat.S_ISDIR(component_before.st_mode):
                    raise ValueError("bounded input path components must be real directories")
                child_descriptor = descriptors.enter_context(
                    _open_descriptor(component, directory_flags, dir_fd=parent_descriptor)
                )
                child_open = os.fstat(child_descriptor)
                if _stable_directory_identity(component_before) != _stable_directory_identity(child_open):
                    raise ValueError("bounded input directory changed before it was opened")
                directory_identities.append(_stable_directory_identity(child_open))
                parent_descriptor = child_descriptor
            filename = relative.parts[-1]
            pathname_before = os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
            if not stat.S_ISREG(pathname_before.st_mode) or pathname_before.st_nlink != 1:
                raise ValueError("bounded input must be a single-link regular non-symlink file")
            descriptor = descriptors.enter_context(
                _open_descriptor(filename, file_flags, dir_fd=parent_descriptor)
            )
        except OSError as exc:
            raise ValueError("bounded input must be a readable regular non-symlink file") from exc
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError("bounded input must be a single-link regular file")
        if _stable_file_identity(pathname_before) != _stable_file_identity(before):
            raise ValueError("bounded input pathname changed before it was read")
        if before.st_size > max_bytes:
            raise ValueError("bounded input exceeds the maximum size")
        chunks: list[bytes] = []; total = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, max_bytes + 1 - total))
            if not chunk: break
            chunks.append(chunk); total += len(chunk)
            if total > max_bytes: raise ValueError("bounded input exceeds the maximum size")
        after = os.fstat(descriptor)
        if _stable_file_identity(after) != _stable_file_identity(before) or total != after.st_size:
            raise ValueError("bounded input changed while it was being read")
        current = os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
        if _stable_file_identity(current) != _stable_file_identity(after):
            raise ValueError("bounded input pathname changed while it was being read")
        try:
            root_current = os.stat(root, follow_symlinks=False)
            root_verifier = descriptors.enter_context(_open_descriptor(root, directory_flags))
            if _stable_directory_identity(root_current) != directory_identities[0] or _stable_directory_identity(os.fstat(root_verifier)) != directory_identities[0]:
                raise ValueError("bounded input approved root changed while it was being read")
            parent_verifier = root_verifier
            for component, expected_identity in zip(relative.parts[:-1], directory_identities[1:]):
                child_verifier = descriptors.enter_context(
                    _open_descriptor(component, directory_flags, dir_fd=parent_verifier)
                )
                if _stable_directory_identity(os.fstat(child_verifier)) != expected_identity:
                    raise ValueError("bounded input directory changed while it was being read")
                parent_verifier = child_verifier
            current_path = os.stat(filename, dir_fd=parent_verifier, follow_symlinks=False)
            if _stable_file_identity(current_path) != _stable_file_identity(after):
                raise ValueError("bounded input path changed while it was being read")
        except OSError as exc:
            raise ValueError("bounded input path changed while it was being read") from exc
        return b"".join(chunks)


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result: raise ValueError("input contains a duplicate JSON object key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-JSON numeric constant: {value}")


def _validate_json_lexical_bounds(text: str) -> None:
    nodes = depth = index = 0
    while index < len(text):
        character = text[index]
        if character in " \t\r\n,:]}":
            if character in "]}":
                depth = max(0, depth - 1)
            index += 1
            continue
        if character == '"':
            nodes += 1; index += 1
            while index < len(text):
                if text[index] == "\\":
                    index += 2
                elif text[index] == '"':
                    index += 1; break
                else:
                    index += 1
        elif character in "[{":
            nodes += 1; depth += 1; index += 1
            if depth > MAX_NESTING_DEPTH:
                raise ValueError("treatment input exceeds the maximum nesting depth")
        elif character in "-0123456789":
            nodes += 1; index += 1
            while index < len(text) and text[index] not in " \t\r\n,]}":
                index += 1
        elif text.startswith("true", index):
            nodes += 1; index += 4
        elif text.startswith("false", index):
            nodes += 1; index += 5
        elif text.startswith("null", index):
            nodes += 1; index += 4
        else:
            index += 1
        if nodes > MAX_TOTAL_NODES:
            raise ValueError("treatment input exceeds the maximum node count")


def _parse_json_bytes(raw: bytes) -> object:
    try:
        text = raw.decode("utf-8", errors="strict")
        _validate_json_lexical_bounds(text)
        return json.loads(
            text, object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("input must be strict UTF-8 JSON") from exc


def _read_json_file(path: Path, *, allowed_root: Path = ROOT) -> object:
    return _parse_json_bytes(_read_bounded_regular_file(path, allowed_root=allowed_root))


__all__ = [name for name in globals() if not name.startswith("__")]
