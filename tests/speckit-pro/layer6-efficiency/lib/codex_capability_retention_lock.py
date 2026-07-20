#!/usr/bin/env python3
"""Descriptor-bound serialization for raw evidence retention operations."""

from __future__ import annotations

if __package__:
    from .codex_capability_private import *
else:
    from codex_capability_private import *


def _assert_retention_lock_current(raw_descriptor, lock_descriptor, expected_lock_identity):
    try:
        path_metadata = os.stat(
            RETENTION_LOCK_FILE, dir_fd=raw_descriptor, follow_symlinks=False,
        )
        descriptor_metadata = os.fstat(lock_descriptor)
    except OSError as error:
        raise ValueError("raw evidence retention lock path changed") from error
    for metadata in (path_metadata, descriptor_metadata):
        if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_nlink != 1:
            raise ValueError("raw evidence retention lock is invalid")
    if (
        _stable_file_identity(path_metadata) != expected_lock_identity
        or _stable_file_identity(descriptor_metadata) != expected_lock_identity
    ):
        raise ValueError("raw evidence retention lock path changed")


def _acquire_retention_flock(fcntl, descriptor):
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        raise ValueError("raw evidence retention operation is already in progress") from error


@contextmanager
def _retention_lock(raw, expected_raw_identity):
    if not HAS_DESCRIPTOR_RELATIVE_IO:
        raise ValueError("raw evidence retention requires descriptor-relative locking")
    try:
        import fcntl
    except ImportError as error:
        raise ValueError("raw evidence retention requires advisory file locking") from error
    parent = raw.parent
    parent_identity = _stable_directory_identity(os.stat(parent, follow_symlinks=False))
    parent_descriptor = _private_directory_descriptor(parent, parent_identity)
    raw_descriptor = None
    lock_descriptor = None
    lock_identity = None
    locked_descriptors = []
    try:
        _acquire_retention_flock(fcntl, parent_descriptor)
        locked_descriptors.append(parent_descriptor)
        raw_descriptor = _private_directory_descriptor(raw, expected_raw_identity)
        _acquire_retention_flock(fcntl, raw_descriptor)
        locked_descriptors.append(raw_descriptor)
        try:
            lock_descriptor = os.open(
                RETENTION_LOCK_FILE,
                os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=raw_descriptor,
            )
        except OSError as error:
            raise ValueError("raw evidence retention lock is invalid") from error
        metadata = os.fstat(lock_descriptor)
        if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_nlink != 1:
            raise ValueError("raw evidence retention lock is invalid")
        lock_identity = _stable_file_identity(metadata)
        _assert_retention_lock_current(raw_descriptor, lock_descriptor, lock_identity)
        _acquire_retention_flock(fcntl, lock_descriptor)
        locked_descriptors.append(lock_descriptor)
        os.fsync(lock_descriptor); os.fsync(raw_descriptor)
        _assert_retention_lock_current(raw_descriptor, lock_descriptor, lock_identity)
        _assert_private_directory_current(raw, raw_descriptor, expected_raw_identity)
        _assert_private_directory_current(parent, parent_descriptor, parent_identity)
        yield
    finally:
        try:
            if raw_descriptor is not None:
                _assert_private_directory_current(raw, raw_descriptor, expected_raw_identity)
            _assert_private_directory_current(parent, parent_descriptor, parent_identity)
            if lock_descriptor is not None and lock_identity is not None:
                _assert_retention_lock_current(raw_descriptor, lock_descriptor, lock_identity)
        finally:
            for descriptor in reversed(locked_descriptors):
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                except OSError:
                    pass
            if lock_descriptor is not None: os.close(lock_descriptor)
            if raw_descriptor is not None: os.close(raw_descriptor)
            os.close(parent_descriptor)


__all__ = [name for name in globals() if not name.startswith("__")]
