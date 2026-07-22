#!/usr/bin/env python3
"""Crash-safe append-only temporary locking and recovery."""

from __future__ import annotations

import time

from codex_capability_io import *

_APPEND_ONLY_TEMPORARY_NAME = re.compile(
    rf"{re.escape(PRIVATE_TEMPORARY_PREFIX)}[0-9a-f]{{32}}",
)
_APPEND_ONLY_LOCK_WAIT_SECONDS = 5.0


def _acquire_append_only_lock(descriptor, *, wait, label):
    try:
        import fcntl
    except ImportError as error:
        raise ValueError("append-only recovery requires advisory file locking") from error
    deadline = time.monotonic() + _APPEND_ONLY_LOCK_WAIT_SECONDS
    while True:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except BlockingIOError as error:
            if not wait or time.monotonic() >= deadline:
                raise ValueError(f"append-only {label} operation is already in progress") from error
            time.sleep(0.01)


def _acquire_append_only_directory_lock(descriptor, *, wait):
    _acquire_append_only_lock(descriptor, wait=wait, label="directory")


def _acquire_append_only_temporary_lock(descriptor, *, wait):
    _acquire_append_only_lock(descriptor, wait=wait, label="temporary")


def _read_open_descriptor(descriptor):
    chunks, total = [], 0
    os.lseek(descriptor, 0, os.SEEK_SET)
    while True:
        chunk = os.read(descriptor, min(1024 * 1024, PRIVATE_REFRESH_MAX_BYTES + 1 - total))
        if not chunk:
            break
        chunks.append(chunk); total += len(chunk)
        if total > PRIVATE_REFRESH_MAX_BYTES:
            raise ValueError("append-only recovery target exceeds the bounded size")
    return b"".join(chunks)


def _read_append_only_target_at(parent_descriptor, name):
    descriptor = os.open(
        name, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        dir_fd=parent_descriptor,
    )
    try:
        before = os.fstat(descriptor)
        current = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_size > PRIVATE_REFRESH_MAX_BYTES
            or _stable_file_identity(current) != _stable_file_identity(before)
        ):
            raise ValueError("append-only recovery target must be a stable bounded regular file")
        payload = _read_open_descriptor(descriptor)
        after = os.fstat(descriptor)
        current = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
        if _stable_file_identity(after) != _stable_file_identity(before) or _stable_file_identity(current) != _stable_file_identity(after):
            raise ValueError("append-only recovery target changed while it was read")
        return payload
    finally:
        os.close(descriptor)


def _recover_append_only_target(
    path, payload, expected_parent_identity=None, *, directory_lock_held=False,
    expected_temporary_name=None, parent_descriptor=None,
):
    if not HAS_DESCRIPTOR_RELATIVE_IO:
        raise ValueError("append-only recovery requires descriptor-relative filesystem operations")
    target = Path(os.path.abspath(path)); parent = target.parent
    owns_parent_descriptor = parent_descriptor is None
    if owns_parent_descriptor:
        parent_metadata = os.stat(parent, follow_symlinks=False)
        if not stat.S_ISDIR(parent_metadata.st_mode):
            raise ValueError("append-only recovery parent must be a real directory")
        parent_identity = _stable_directory_identity(parent_metadata)
        if expected_parent_identity is not None and parent_identity != expected_parent_identity:
            raise ValueError("append-only recovery parent changed after validation")
        parent_descriptor = os.open(
            parent, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_DIRECTORY", 0),
        )
    else:
        if expected_parent_identity is None:
            raise ValueError("bound append-only recovery requires its parent identity")
        if not directory_lock_held:
            raise ValueError("bound append-only recovery requires its directory lock")
        parent_identity = expected_parent_identity
    target_descriptor = temporary_descriptor = None
    try:
        if (
            _stable_directory_identity(os.stat(parent, follow_symlinks=False)) != parent_identity
            or _stable_directory_identity(os.fstat(parent_descriptor)) != parent_identity
        ):
            raise ValueError("append-only recovery parent changed before it was opened")
        if not directory_lock_held:
            _acquire_append_only_directory_lock(parent_descriptor, wait=True)
            if (
                _stable_directory_identity(os.stat(parent, follow_symlinks=False)) != parent_identity
                or _stable_directory_identity(os.fstat(parent_descriptor)) != parent_identity
            ):
                raise ValueError("append-only recovery parent changed while locking")
        try:
            target_descriptor = os.open(
                target.name, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=parent_descriptor,
            )
        except FileNotFoundError:
            return False
        def target_state():
            opened = os.fstat(target_descriptor)
            current = os.stat(target.name, dir_fd=parent_descriptor, follow_symlinks=False)
            if not stat.S_ISREG(opened.st_mode) or _stable_file_identity(current) != _stable_file_identity(opened):
                raise ValueError("append-only recovery target changed before inspection")
            return opened

        def target_is_committed(*, verify_payload):
            before = target_state()
            if before.st_nlink != 1:
                return False
            if not verify_payload:
                return True
            retained = _read_open_descriptor(target_descriptor)
            after = target_state()
            if retained != payload or _stable_file_identity(before) != _stable_file_identity(after):
                raise ValueError("append-only recovery target changed or has unexpected bytes")
            return True

        if target_is_committed(verify_payload=expected_temporary_name is not None):
            os.fsync(parent_descriptor)
            return False
        target_before = target_state()
        if target_before.st_nlink != 2:
            raise ValueError("append-only target retains unrecognized alternate hard links")
        candidates = []
        candidate_names = (
            [expected_temporary_name] if expected_temporary_name is not None
            else _bounded_directory_names(parent_descriptor, label="append-only recovery directory")
        )
        for name in candidate_names:
            if not isinstance(name, str) or not _APPEND_ONLY_TEMPORARY_NAME.fullmatch(name):
                if expected_temporary_name is not None:
                    raise ValueError("append-only recovery temporary name is invalid")
                continue
            try:
                metadata = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
            except FileNotFoundError:
                continue
            if (metadata.st_dev, metadata.st_ino) == (target_before.st_dev, target_before.st_ino):
                candidates.append(name)
        if len(candidates) != 1:
            if target_is_committed(verify_payload=True):
                return False
            raise ValueError("single-link append-only target lacks one recoverable temporary link")
        temporary_name = candidates[0]
        try:
            temporary_descriptor = os.open(
                temporary_name, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=parent_descriptor,
            )
        except FileNotFoundError:
            if target_is_committed(verify_payload=True):
                return False
            raise ValueError("append-only temporary link changed during recovery")
        _acquire_append_only_temporary_lock(temporary_descriptor, wait=True)
        if target_is_committed(verify_payload=True):
            return False
        temporary_metadata = os.fstat(temporary_descriptor)
        latest_target = target_state()
        current_temporary = os.stat(temporary_name, dir_fd=parent_descriptor, follow_symlinks=False)
        if (
            latest_target.st_nlink != 2
            or _stable_file_identity(current_temporary) != _stable_file_identity(temporary_metadata)
            or _stable_file_identity(latest_target) != _stable_file_identity(temporary_metadata)
        ):
            raise ValueError("append-only temporary link changed during recovery")
        retained = _read_open_descriptor(target_descriptor)
        target_after = target_state()
        if retained != payload or _stable_file_identity(latest_target) != _stable_file_identity(target_after):
            raise ValueError("append-only recovery target changed or has unexpected bytes")
        os.fsync(parent_descriptor)
        os.unlink(temporary_name, dir_fd=parent_descriptor)
        os.fsync(parent_descriptor)
        final_target = os.stat(target.name, dir_fd=parent_descriptor, follow_symlinks=False)
        if (
            _stable_file_content_identity(final_target) != _stable_file_content_identity(target_after)
            or final_target.st_nlink != 1
            or _stable_directory_identity(os.stat(parent, follow_symlinks=False)) != parent_identity
            or _stable_directory_identity(os.fstat(parent_descriptor)) != parent_identity
        ):
            raise ValueError("append-only target changed during temporary-link recovery")
        return True
    finally:
        if temporary_descriptor is not None: os.close(temporary_descriptor)
        if target_descriptor is not None: os.close(target_descriptor)
        if owns_parent_descriptor: os.close(parent_descriptor)


def _recover_append_only_directory(
    directory, expected_identity, *, require_content_addressed,
    descriptor=None, directory_lock_held=False,
):
    owns_descriptor = descriptor is None
    if not owns_descriptor and not directory_lock_held:
        raise ValueError("bound append-only recovery requires its directory lock")
    if owns_descriptor:
        descriptor = os.open(
            directory, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_DIRECTORY", 0),
        )
    try:
        if _stable_directory_identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("append-only recovery directory changed before it was opened")
        if not directory_lock_held:
            _acquire_append_only_directory_lock(descriptor, wait=True)
        if (
            _stable_directory_identity(os.stat(directory, follow_symlinks=False)) != expected_identity
            or _stable_directory_identity(os.fstat(descriptor)) != expected_identity
        ):
            raise ValueError("append-only recovery directory changed while locking")
        for temporary_name in _bounded_directory_names(descriptor, label="append-only recovery directory"):
            if not _APPEND_ONLY_TEMPORARY_NAME.fullmatch(temporary_name):
                continue
            try:
                temporary_descriptor = os.open(
                    temporary_name, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=descriptor,
                )
            except FileNotFoundError:
                continue
            try:
                before = os.fstat(temporary_descriptor)
                try:
                    current = os.stat(temporary_name, dir_fd=descriptor, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                if not stat.S_ISREG(before.st_mode) or stat.S_IMODE(before.st_mode) != 0o600 or _stable_file_identity(current) != _stable_file_identity(before):
                    raise ValueError("append-only recovery temporary must be a stable private regular file")
                if before.st_nlink != 1:
                    continue
                _acquire_append_only_temporary_lock(temporary_descriptor, wait=True)
                try:
                    current = os.stat(temporary_name, dir_fd=descriptor, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                opened = os.fstat(temporary_descriptor)
                if opened.st_nlink != 1:
                    continue
                if _stable_file_identity(current) != _stable_file_identity(opened):
                    raise ValueError("append-only temporary changed before abandoned-write recovery")
                os.fsync(descriptor)
                os.unlink(temporary_name, dir_fd=descriptor)
                os.fsync(descriptor)
            finally:
                os.close(temporary_descriptor)
        names = _bounded_directory_names(descriptor, label="append-only recovery directory")
        entries_by_inode = {}
        metadata_by_name = {}
        for name in names:
            try:
                metadata = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError as error:
                raise ValueError("append-only recovery directory changed during recovery") from error
            metadata_by_name[name] = metadata
            entries_by_inode.setdefault((metadata.st_dev, metadata.st_ino), []).append(name)
        for temporary_name in names:
            if not _APPEND_ONLY_TEMPORARY_NAME.fullmatch(temporary_name):
                continue
            temporary = metadata_by_name[temporary_name]
            targets = [
                name for name in entries_by_inode[(temporary.st_dev, temporary.st_ino)]
                if name != temporary_name and not _APPEND_ONLY_TEMPORARY_NAME.fullmatch(name)
            ]
            if temporary.st_nlink != 2 or len(targets) != 1:
                raise ValueError("append-only temporary link lacks one published target")
            target = Path(directory) / targets[0]
            payload = _read_append_only_target_at(descriptor, target.name)
            if require_content_addressed and target.name != f"{digest(payload).removeprefix('sha256:')}.json":
                raise ValueError("append-only recovery target is not content-addressed")
            _recover_append_only_target(
                target, payload, expected_identity, directory_lock_held=True,
                expected_temporary_name=temporary_name, parent_descriptor=descriptor,
            )
        if (
            any(
                _APPEND_ONLY_TEMPORARY_NAME.fullmatch(name)
                for name in _bounded_directory_names(descriptor, label="append-only recovery directory")
            )
            or _stable_directory_identity(os.stat(directory, follow_symlinks=False)) != expected_identity
            or _stable_directory_identity(os.fstat(descriptor)) != expected_identity
        ):
            raise ValueError("append-only recovery directory changed during recovery")
    finally:
        if owns_descriptor: os.close(descriptor)


def _recover_content_addressed_append_only_links(raw):
    directories = [Path(raw)]
    directories.extend(
        Path(raw) / name for name in (
            RETENTION_RECORDS_DIR, PUBLICATION_INTENTS_DIR, PUBLICATION_RECEIPTS_DIR,
            DELETION_INTENTS_DIR, DELETION_RECORDS_DIR,
        ) if (Path(raw) / name).exists()
    )
    for directory in directories:
        metadata = os.stat(directory, follow_symlinks=False)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o700:
            raise ValueError("append-only recovery requires a private directory")
        _recover_append_only_directory(
            directory, _stable_directory_identity(metadata), require_content_addressed=True,
        )


__all__ = [name for name in globals() if not name.startswith("__")]
