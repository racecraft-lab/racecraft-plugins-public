#!/usr/bin/env python3
"""Atomic pending retention for raw capability capture materialization."""

from __future__ import annotations

if __package__:
    from .codex_capability_retention_records import *
else:
    from codex_capability_retention_records import *


_materialize_source_capture_unlocked = materialize_source_capture
_materialize_unknown_capture_unlocked = materialize_unknown_capture
_PENDING_CAPTURE_FREEZE_ID = digest(b"G56R-002 pending raw evidence capture v1")


def _deletion_started_evidence_digests(raw, repository_root):
    values = {
        _validate_deletion_record(record_digest, record)["raw_evidence_digest"]
        for record_digest, record in _load_private_records(
            raw / DELETION_RECORDS_DIR, repository_root, "deletion record",
        )
    }
    values.update(
        _validate_deletion_intent(record_digest, record)["raw_evidence_digest"]
        for record_digest, record in _load_private_records(
            raw / DELETION_INTENTS_DIR, repository_root, "deletion intent",
        )
    )
    return values


def _pending_capture_record(evidence_digest, registered):
    if registered.tzinfo is None or registered.utcoffset() != timedelta(0):
        raise ValueError("pending retention registration clock must be UTC")
    registered_at = _format_timestamp(registered)
    return {
        "schema_version": "raw-evidence-retention.v1",
        "candidate_freeze_id": _PENDING_CAPTURE_FREEZE_ID,
        "raw_evidence_digest": evidence_digest,
        "published_at": registered_at,
        "registered_at": registered_at,
        "delete_after": _format_timestamp(
            registered + timedelta(days=RAW_EVIDENCE_PENDING_DAYS)
        ),
    }


def _register_pending_capture_locked(
    evidence_digest, raw, raw_identity, repository_root, *, registered=None,
):
    _need_digest(evidence_digest, "raw_evidence_digest")
    if evidence_digest in _deletion_started_evidence_digests(raw, repository_root):
        raise ValueError("raw evidence cannot be materialized after deletion has begun")
    directory, directory_identity = _private_record_directory(
        raw, RETENTION_RECORDS_DIR, raw_identity,
    )
    existing = []
    for record_digest, raw_record in _load_private_records(
        directory, repository_root, "retention record",
    ):
        record = _validate_retention_record(record_digest, raw_record)
        if (
            record["candidate_freeze_id"] == _PENDING_CAPTURE_FREEZE_ID
            and record["raw_evidence_digest"] == evidence_digest
        ):
            existing.append(record_digest)
    if len(existing) > 1:
        raise ValueError("raw evidence has multiple pending capture records")
    if existing:
        return existing[0]
    if registered is None:
        registered = _retention_now()
    record = _pending_capture_record(evidence_digest, registered)
    record_digest = _store_private_record(
        directory, record, repository_root, directory_identity,
    )
    _validate_retention_record(record_digest, record)
    return record_digest


def _raw_capture_inventory(raw, raw_identity, repository_root):
    raw_descriptor = _private_directory_descriptor(raw, raw_identity)
    try:
        names = sorted(os.listdir(raw_descriptor))
        captures = {}
        for name in names:
            if not re.fullmatch(r"[0-9a-f]{64}\.json", name):
                continue
            before = os.stat(name, dir_fd=raw_descriptor, follow_symlinks=False)
            if (
                not stat.S_ISREG(before.st_mode)
                or stat.S_IMODE(before.st_mode) != 0o600
                or before.st_nlink != 1
                or before.st_size > PRIVATE_REFRESH_MAX_BYTES
            ):
                raise ValueError("raw evidence capture inventory contains an invalid file")
            path = raw / name
            _, payload = read_content_addressed_private_file(
                path, repository_root, "unregistered raw evidence",
            )
            after = os.stat(name, dir_fd=raw_descriptor, follow_symlinks=False)
            if _stable_file_identity(before) != _stable_file_identity(after):
                raise ValueError("raw evidence capture changed during inventory")
            evidence_digest = digest(payload)
            captures[evidence_digest] = datetime.fromtimestamp(
                after.st_mtime, timezone.utc,
            )
        if sorted(os.listdir(raw_descriptor)) != names:
            raise ValueError("raw evidence root changed during capture inventory")
        _assert_private_directory_current(raw, raw_descriptor, raw_identity)
        return captures
    except OSError as error:
        raise ValueError("raw evidence captures could not be inventoried safely") from error
    finally:
        os.close(raw_descriptor)


def _register_untracked_raw_evidence_locked(
    raw, raw_identity, repository_root, *, apply,
):
    captures = _raw_capture_inventory(raw, raw_identity, repository_root)
    registered = {
        _validate_retention_record(record_digest, record)["raw_evidence_digest"]
        for record_digest, record in _load_private_records(
            raw / RETENTION_RECORDS_DIR, repository_root, "retention record",
        )
    }
    untracked = sorted(set(captures) - registered)
    if untracked and not apply:
        raise ValueError("unregistered raw evidence requires retention cleanup")
    for evidence_digest in untracked:
        _register_pending_capture_locked(
            evidence_digest,
            raw,
            raw_identity,
            repository_root,
            registered=captures[evidence_digest],
        )
    return untracked


def materialize_source_capture(raw_root, repository_root, capture_bytes):
    raw, raw_identity = _validated_raw_evidence_root_binding(
        raw_root, repository_root,
    )
    capture_digest = digest(capture_bytes)
    with _retention_lock(raw, raw_identity):
        if capture_digest in _deletion_started_evidence_digests(raw, repository_root):
            raise ValueError("raw evidence cannot be materialized after deletion has begun")
        retained_digest, target = _materialize_source_capture_unlocked(
            raw, repository_root, capture_bytes,
        )
        if retained_digest != capture_digest:
            raise ValueError("source capture identity changed during materialization")
        _register_pending_capture_locked(
            capture_digest, raw, raw_identity, repository_root,
        )
        return retained_digest, target


def materialize_unknown_capture(
    raw_root, repository_root, surface, client_identity_id,
    repository_binding, work_item, captured_at,
):
    raw, raw_identity = _validated_raw_evidence_root_binding(
        raw_root, repository_root,
    )
    record = _unknown_capture_record(
        surface, client_identity_id, repository_binding, work_item, captured_at,
    )
    evidence_digest = digest(canonical_bytes(record) + b"\n")
    with _retention_lock(raw, raw_identity):
        if evidence_digest in _deletion_started_evidence_digests(raw, repository_root):
            raise ValueError("raw evidence cannot be materialized after deletion has begun")
        retained_digest, target = _materialize_unknown_capture_unlocked(
            raw,
            repository_root,
            surface,
            client_identity_id,
            repository_binding,
            work_item,
            captured_at,
        )
        if retained_digest != evidence_digest:
            raise ValueError("unknown capture identity changed during materialization")
        _register_pending_capture_locked(
            evidence_digest, raw, raw_identity, repository_root,
        )
        return retained_digest, target


__all__ = [name for name in globals() if not name.startswith("__")]
