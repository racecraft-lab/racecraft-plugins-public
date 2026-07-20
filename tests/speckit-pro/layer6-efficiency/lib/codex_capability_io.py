#!/usr/bin/env python3
"""Descriptor-bound capability evidence input helpers."""

from __future__ import annotations

if __package__:
    from .codex_capability_contract import *
else:
    from codex_capability_contract import *

def _stable_file_identity(metadata):
    return (
        metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns,
        metadata.st_ctime_ns, stat.S_IMODE(metadata.st_mode), metadata.st_nlink,
    )


def _stable_directory_identity(metadata):
    return metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode), stat.S_IMODE(metadata.st_mode)


def _stable_file_content_identity(metadata):
    return metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns, stat.S_IMODE(metadata.st_mode)


def _read_bounded_regular_file(
    path, *, required_mode=None, allowed_root=None, expected_parent_identity=None,
    require_single_link=False,
):
    source = Path(os.path.abspath(path)); root = Path(os.path.abspath(allowed_root or source.parent))
    try:
        relative = source.relative_to(root)
    except ValueError as error:
        raise ValueError("bounded input must remain inside its approved root") from error
    if not relative.parts:
        raise ValueError("bounded input must name a file below its approved root")
    if not HAS_DESCRIPTOR_RELATIVE_IO:
        raise ValueError("bounded input requires descriptor-relative path validation")
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | nofollow | getattr(os, "O_DIRECTORY", 0)
    file_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | nofollow
    directory_descriptors, directory_identities = [], []
    descriptor = None
    try:
        root_before = os.stat(root, follow_symlinks=False)
        if not stat.S_ISDIR(root_before.st_mode):
            raise ValueError("bounded input approved root must be a real directory")
        root_descriptor = os.open(root, directory_flags)
        directory_descriptors.append(root_descriptor)
        root_open = os.fstat(root_descriptor)
        if _stable_directory_identity(root_before) != _stable_directory_identity(root_open):
            raise ValueError("bounded input approved root changed before it was opened")
        directory_identities.append(_stable_directory_identity(root_open))
        parent_descriptor = root_descriptor
        for component in relative.parts[:-1]:
            component_before = os.stat(component, dir_fd=parent_descriptor, follow_symlinks=False)
            if not stat.S_ISDIR(component_before.st_mode):
                raise ValueError("bounded input path components must be real directories")
            child_descriptor = os.open(component, directory_flags, dir_fd=parent_descriptor)
            child_open = os.fstat(child_descriptor)
            if _stable_directory_identity(component_before) != _stable_directory_identity(child_open):
                os.close(child_descriptor)
                raise ValueError("bounded input directory changed before it was opened")
            directory_descriptors.append(child_descriptor)
            directory_identities.append(_stable_directory_identity(child_open))
            parent_descriptor = child_descriptor
        if expected_parent_identity is not None and _stable_directory_identity(os.fstat(parent_descriptor)) != expected_parent_identity:
            raise ValueError("bounded input parent changed after validation")
        filename = relative.parts[-1]
        pathname_before = os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
        if not stat.S_ISREG(pathname_before.st_mode) or require_single_link and pathname_before.st_nlink != 1:
            raise ValueError("bounded input must be a single-link regular non-symlink file")
        descriptor = os.open(filename, file_flags, dir_fd=parent_descriptor)
    except OSError as error:
        if descriptor is not None: os.close(descriptor)
        for directory_descriptor in reversed(directory_descriptors): os.close(directory_descriptor)
        raise ValueError("bounded input must be a readable regular non-symlink file") from error
    except ValueError:
        if descriptor is not None: os.close(descriptor)
        for directory_descriptor in reversed(directory_descriptors): os.close(directory_descriptor)
        raise
    try:
        if descriptor is None:
            raise ValueError("bounded input could not be opened safely")
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or require_single_link and before.st_nlink != 1:
            raise ValueError("bounded input must be a single-link regular file")
        if _stable_file_identity(pathname_before) != _stable_file_identity(before):
            raise ValueError("bounded input pathname changed before it was read")
        if required_mode is not None and os.name != "nt" and stat.S_IMODE(before.st_mode) != required_mode:
            raise ValueError(f"private input must use mode {required_mode:04o}")
        if before.st_size > PRIVATE_REFRESH_MAX_BYTES:
            raise ValueError("bounded input exceeds the maximum size")
        chunks, total = [], 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, PRIVATE_REFRESH_MAX_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk); total += len(chunk)
            if total > PRIVATE_REFRESH_MAX_BYTES:
                raise ValueError("bounded input exceeds the maximum size")
        after = os.fstat(descriptor)
        if _stable_file_identity(after) != _stable_file_identity(before) or total != after.st_size:
            raise ValueError("bounded input changed while it was being read")
        current = os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
        if _stable_file_identity(current) != _stable_file_identity(after):
            raise ValueError("bounded input pathname changed while it was being read")
        verifier_descriptors = []
        try:
            root_current = os.stat(root, follow_symlinks=False)
            verifier = os.open(root, directory_flags)
            verifier_descriptors.append(verifier)
            if _stable_directory_identity(root_current) != directory_identities[0] or _stable_directory_identity(os.fstat(verifier)) != directory_identities[0]:
                raise ValueError("bounded input approved root changed while it was being read")
            for component, expected_identity in zip(relative.parts[:-1], directory_identities[1:]):
                next_descriptor = os.open(component, directory_flags, dir_fd=verifier)
                verifier_descriptors.append(next_descriptor)
                if _stable_directory_identity(os.fstat(next_descriptor)) != expected_identity:
                    raise ValueError("bounded input directory changed while it was being read")
                verifier = next_descriptor
            current_path = os.stat(filename, dir_fd=verifier, follow_symlinks=False)
            if _stable_file_identity(current_path) != _stable_file_identity(after):
                raise ValueError("bounded input path changed while it was being read")
        except OSError as error:
            raise ValueError("bounded input path changed while it was being read") from error
        finally:
            for verifier_descriptor in reversed(verifier_descriptors): os.close(verifier_descriptor)
        return b"".join(chunks)
    finally:
        if descriptor is not None: os.close(descriptor)
        for directory_descriptor in reversed(directory_descriptors): os.close(directory_descriptor)


def digest_regular_file(path):
    source = Path(os.path.abspath(path)); flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        pathname_before = os.stat(source, follow_symlinks=False)
        if not stat.S_ISREG(pathname_before.st_mode): raise ValueError("client executable must be a regular file that is not a symlink")
        descriptor = os.open(source, flags)
    except OSError as error:
        raise ValueError("client executable must be a readable regular file that is not a symlink") from error
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or _stable_file_identity(pathname_before) != _stable_file_identity(before):
            raise ValueError("client executable pathname changed before hashing")
        hasher, remaining = hashlib.sha256(), before.st_size
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                raise ValueError("client executable changed while hashing")
            hasher.update(chunk); remaining -= len(chunk)
        after = os.fstat(descriptor)
        if _stable_file_identity(before) != _stable_file_identity(after):
            raise ValueError("client executable changed while hashing")
        try:
            current = os.stat(source, follow_symlinks=False)
        except OSError as error:
            raise ValueError("client executable pathname changed while hashing") from error
        if not stat.S_ISREG(current.st_mode) or _stable_file_identity(current) != _stable_file_identity(after):
            raise ValueError("client executable pathname changed while hashing")
        return f"sha256:{hasher.hexdigest()}"
    finally:
        os.close(descriptor)

__all__ = [name for name in globals() if not name.startswith("__")]
