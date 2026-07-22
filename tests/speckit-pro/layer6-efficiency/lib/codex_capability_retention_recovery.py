#!/usr/bin/env python3
"""Verified retention-quarantine republication and recovery intent helpers."""

from __future__ import annotations

from codex_capability_publication_records import *


def _unlink_descriptor_relative(filename, parent_descriptor):
    os.unlink(filename, dir_fd=parent_descriptor)


def _descriptor_entry_exists(parent_descriptor, filename):
    try:
        os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
        return True
    except FileNotFoundError:
        return False


def _verified_republished_quarantine_metadata(
    target, raw, expected_digest, expected_raw_identity,
):
    if Path(target).parent != raw:
        raise ValueError("republished quarantine must remain in its private root")
    filename = Path(target).name
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    file_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | nofollow
    parent_descriptor = _private_directory_descriptor(raw, expected_raw_identity)
    descriptor = None
    try:
        before = os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o600
            or before.st_nlink != 1
            or before.st_size > PRIVATE_REFRESH_MAX_BYTES
        ):
            raise ValueError("republished quarantine is not a bounded single-link private file")
        descriptor = os.open(filename, file_flags, dir_fd=parent_descriptor)
        opened = os.fstat(descriptor)
        if _stable_file_identity(before) != _stable_file_identity(opened):
            raise ValueError("republished quarantine changed before verification")
        chunks, total = [], 0
        while True:
            chunk = os.read(
                descriptor,
                min(1024 * 1024, PRIVATE_REFRESH_MAX_BYTES + 1 - total),
            )
            if not chunk:
                break
            chunks.append(chunk); total += len(chunk)
            if total > PRIVATE_REFRESH_MAX_BYTES:
                raise ValueError("republished quarantine exceeds the maximum size")
        after = os.fstat(descriptor)
        current = os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
        if (
            after.st_nlink != 1
            or _stable_file_identity(after) != _stable_file_identity(opened)
            or _stable_file_identity(current) != _stable_file_identity(opened)
            or total != after.st_size
            or digest(b"".join(chunks)) != expected_digest
        ):
            raise ValueError("republished quarantine does not match its verified payload")
        _assert_private_directory_current(raw, parent_descriptor, expected_raw_identity)
        return after
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent_descriptor)


def _store_republished_recovery_intent(
    raw, raw_identity, repository_root, predecessor, predecessor_digest,
    quarantine_metadata, deleted_at,
):
    staged = {
        "schema_version": "raw-evidence-deletion-intent.v3",
        "raw_evidence_digest": predecessor["raw_evidence_digest"],
        "retention_record_digests": predecessor["retention_record_digests"],
        "delete_after": predecessor["delete_after"],
        "deletion_started_at": deleted_at,
        "predecessor_deletion_intent_digest": predecessor_digest,
        "quarantine_filename": predecessor["quarantine_filename"],
        "recovery_proof": "verified-payload-republication-v1",
        "target_file_identity": _deletion_intent_file_identity(quarantine_metadata),
    }
    directory, directory_identity = _private_record_directory(
        raw, DELETION_INTENTS_DIR, raw_identity,
    )
    return staged, _store_private_record(
        directory, staged, repository_root, directory_identity,
    )


__all__ = [name for name in globals() if not name.startswith("__")]
