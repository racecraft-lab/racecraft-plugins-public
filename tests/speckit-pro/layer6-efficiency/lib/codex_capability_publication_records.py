#!/usr/bin/env python3
"""Retention registration and durable publication authority records."""

from __future__ import annotations

if __package__:
    from .codex_capability_retention_records import *
else:
    from codex_capability_retention_records import *


def _validate_publication_record(record_digest, record, *, intent):
    version = "raw-evidence-publication-intent.v1" if intent else "raw-evidence-publication.v1"
    label = "publication intent" if intent else "publication receipt"
    keys = {"schema_version", "candidate_freeze_id", "published_artifact_digest", "published_at", "retention_record_digests"}
    if not isinstance(record, dict) or set(record) != keys or record["schema_version"] != version:
        raise ValueError(f"raw evidence {label} must use the closed v1 shape")
    _need_digest(record_digest, f"{label} digest")
    _need_digest(record["candidate_freeze_id"], "candidate_freeze_id")
    _need_digest(record["published_artifact_digest"], "published_artifact_digest")
    _parsed_timestamp(record["published_at"], f"{label} timestamp")
    refs = record["retention_record_digests"]
    if not isinstance(refs, list) or not refs or refs != sorted(set(refs)):
        raise ValueError(f"{label} requires unique retention records")
    for value in refs: _need_digest(value, "retention_record_digest")
    return record


def _validate_publication_receipt(record_digest, record):
    return _validate_publication_record(record_digest, record, intent=False)


def _validate_publication_intent(record_digest, record):
    return _validate_publication_record(record_digest, record, intent=True)


def _register_raw_evidence_retention_locked(
    freeze, raw, raw_identity, repository_root, *, raw_descriptor,
):
    _parsed_timestamp(freeze.get("published_at"), "freeze publication timestamp")
    evidence_digests = _freeze_raw_evidence_digests(freeze)
    if not evidence_digests: return []
    deletion_started_digests = {
        _validate_deletion_record(record_digest, record)["raw_evidence_digest"]
        for record_digest, record in _load_private_records(raw / DELETION_RECORDS_DIR, repository_root, "deletion record")
    }
    deletion_started_digests.update(
        _validate_deletion_intent(record_digest, record)["raw_evidence_digest"]
        for record_digest, record in _load_private_records(raw / DELETION_INTENTS_DIR, repository_root, "deletion intent")
    )
    if set(evidence_digests) & deletion_started_digests:
        raise ValueError("raw evidence cannot be registered after deletion has begun")
    records, records_identity = _private_record_directory(raw, RETENTION_RECORDS_DIR, raw_identity)
    existing, existing_by_digest = {}, {}
    for record_digest, raw_record in _load_private_records(records, repository_root, "retention record"):
        record = _validate_retention_record(record_digest, raw_record)
        key = (record["candidate_freeze_id"], record["raw_evidence_digest"], record["published_at"])
        if key in existing:
            raise ValueError("freeze evidence has multiple retention registration records")
        existing[key] = (record_digest, record)
        existing_by_digest[record_digest] = record
    governing_record_digests = set()
    for intent_digest, raw_intent in _load_private_records(
        raw / PUBLICATION_INTENTS_DIR, repository_root, "publication intent",
    ):
        intent = _validate_publication_intent(intent_digest, raw_intent)
        refs = set(intent["retention_record_digests"])
        if not refs <= set(existing_by_digest):
            raise ValueError("publication intent references a missing retention record")
        for ref in refs:
            retained = existing_by_digest[ref]
            if retained["candidate_freeze_id"] != intent["candidate_freeze_id"] or retained["published_at"] != intent["published_at"]:
                raise ValueError("publication intent does not bind its freeze retention records")
        governing_record_digests.update(refs)
    registered = _retention_now()
    if registered.tzinfo is None or registered.utcoffset() != timedelta(0):
        raise ValueError("retention registration clock must be UTC")
    registered_at = _format_timestamp(registered)
    record_digests = []
    for evidence_digest in evidence_digests:
        evidence_path = raw / f"{evidence_digest.removeprefix('sha256:')}.json"
        read_content_addressed_private_file(evidence_path, repository_root, "retained raw evidence")
        key = (freeze["candidate_freeze_id"], evidence_digest, freeze["published_at"])
        if key in existing:
            record_digest, record = existing[key]
            pending_deadline = _parsed_timestamp(
                record["registered_at"], "retention registration timestamp",
            ) + timedelta(days=RAW_EVIDENCE_PENDING_DAYS)
            if record_digest not in governing_record_digests and registered >= pending_deadline:
                raise ValueError("expired pending retention registration requires cleanup")
            record_digests.append(record_digest); continue
        record = {
            "schema_version": "raw-evidence-retention.v1",
            "candidate_freeze_id": freeze["candidate_freeze_id"],
            "raw_evidence_digest": evidence_digest,
            "published_at": freeze["published_at"],
            "registered_at": registered_at,
            "delete_after": _format_timestamp(registered + timedelta(days=RAW_EVIDENCE_RETENTION_DAYS)),
        }
        record_digests.append(_store_private_record(records, record, repository_root, records_identity))
    validate_raw_evidence_root(
        raw, repository_root, **_raw_lock_kwargs(raw_descriptor, raw_identity),
    )
    return sorted(record_digests)


@contextmanager
def _bound_publication_output(path, raw, raw_identity):
    if not HAS_DESCRIPTOR_RELATIVE_IO:
        raise ValueError("append-only publication requires descriptor-relative filesystem operations")
    lexical = Path(os.path.abspath(path)); raw = Path(raw)
    try:
        if stat.S_ISLNK(os.stat(lexical, follow_symlinks=False).st_mode):
            raise ValueError("publication output cannot be a symlink")
    except FileNotFoundError:
        # A new publication output has no path, so there is no symlink to reject yet.
        pass
    target = lexical.parent.resolve(strict=False) / lexical.name
    if lexical == raw or raw in lexical.parents or target == raw or raw in target.parents:
        raise ValueError("publication output must remain outside raw_evidence_root")
    directory_flags = (
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_DIRECTORY", 0)
    )
    descriptor = os.open(target.anchor, directory_flags)
    try:
        for part in target.parent.parts[1:]:
            child = os.open(part, directory_flags, dir_fd=descriptor)
            os.close(descriptor); descriptor = child
            metadata = os.fstat(descriptor)
            if _stable_directory_identity(metadata)[:2] == raw_identity[:2]:
                raise ValueError("publication output must remain outside raw_evidence_root")
        parent_identity = _stable_directory_identity(os.fstat(descriptor))
        _acquire_append_only_directory_lock(descriptor, wait=True)
        _assert_private_directory_current(target.parent, descriptor, parent_identity)
        try:
            leaf = os.stat(target.name, dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            leaf = None
        if leaf is not None and stat.S_ISLNK(leaf.st_mode):
            raise ValueError("publication output cannot be a symlink")
        yield target, descriptor, parent_identity
        os.fsync(descriptor)
        _assert_private_directory_current(target.parent, descriptor, parent_identity)
    finally:
        os.close(descriptor)


def _publication_target_matches(
    path, payload, *, parent_descriptor=None, parent_identity=None,
    directory_lock_held=False,
):
    target = Path(os.path.abspath(path))
    try:
        if parent_descriptor is None:
            os.stat(target, follow_symlinks=False)
        else:
            os.stat(target.name, dir_fd=parent_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return False
    _recover_append_only_target(
        target, payload, parent_identity, parent_descriptor=parent_descriptor,
        directory_lock_held=directory_lock_held,
    )
    with _bound_publication_target(
        target, payload, parent_descriptor=parent_descriptor,
        parent_identity=parent_identity, directory_lock_held=directory_lock_held,
    ):
        pass
    return True


def _validate_bound_publication_target(
    parent_descriptor, target_name, target_descriptor, payload, bound_identity=None,
    *, mismatch_message,
):
    opened_before = os.fstat(target_descriptor)
    current_before = os.stat(target_name, dir_fd=parent_descriptor, follow_symlinks=False)
    if (
        not stat.S_ISREG(opened_before.st_mode)
        or opened_before.st_nlink != 1
        or _stable_file_identity(current_before) != _stable_file_identity(opened_before)
    ):
        if bound_identity is not None:
            raise ValueError(mismatch_message)
        raise ValueError("publication output is not a stable single-link regular file")
    retained = _read_open_descriptor(target_descriptor)
    opened_after = os.fstat(target_descriptor)
    current_after = os.stat(target_name, dir_fd=parent_descriptor, follow_symlinks=False)
    identity = _stable_file_identity(opened_after)
    if (
        retained != payload
        or identity != _stable_file_identity(opened_before)
        or _stable_file_identity(current_after) != identity
        or (bound_identity is not None and identity != bound_identity)
    ):
        raise ValueError(mismatch_message)
    return identity


@contextmanager
def _bound_publication_target(
    path, payload, *, receipt_commit=False, parent_descriptor=None,
    parent_identity=None, directory_lock_held=False,
):
    target = Path(os.path.abspath(path)); parent = target.parent
    owns_parent_descriptor = parent_descriptor is None
    if owns_parent_descriptor:
        parent_metadata = os.stat(parent, follow_symlinks=False)
        if not stat.S_ISDIR(parent_metadata.st_mode):
            raise ValueError("publication output parent must be a real directory")
        parent_identity = _stable_directory_identity(parent_metadata)
        parent_descriptor = _private_directory_descriptor(parent, parent_identity)
    elif parent_identity is None or not directory_lock_held:
        raise ValueError("bound publication target requires its locked parent identity")
    target_descriptor = None
    mismatch_message = (
        "publication output changed while its receipt was committed"
        if receipt_commit else "publication output already exists with different bytes"
    )
    try:
        if owns_parent_descriptor:
            _acquire_append_only_directory_lock(parent_descriptor, wait=True)
        _assert_private_directory_current(parent, parent_descriptor, parent_identity)
        try:
            target_descriptor = os.open(
                target.name,
                os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=parent_descriptor,
            )
        except FileNotFoundError as error:
            raise ValueError(mismatch_message) from error
        try:
            bound_identity = _validate_bound_publication_target(
                parent_descriptor, target.name, target_descriptor, payload,
                mismatch_message=mismatch_message,
            )
        except FileNotFoundError as error:
            raise ValueError(mismatch_message) from error
        os.fsync(parent_descriptor)
        yield
        try:
            final_identity = _validate_bound_publication_target(
                parent_descriptor, target.name, target_descriptor, payload, bound_identity,
                mismatch_message=mismatch_message,
            )
        except FileNotFoundError as error:
            raise ValueError(mismatch_message) from error
        if final_identity != bound_identity:
            raise ValueError(mismatch_message)
        os.fsync(parent_descriptor)
        _assert_private_directory_current(parent, parent_descriptor, parent_identity)
    finally:
        if target_descriptor is not None: os.close(target_descriptor)
        if owns_parent_descriptor: os.close(parent_descriptor)


def _store_publication_record_locked(freeze, retention_record_digests, raw, raw_identity, repository_root, *, intent):
    record = {
        "schema_version": "raw-evidence-publication-intent.v1" if intent else "raw-evidence-publication.v1",
        "candidate_freeze_id": freeze["candidate_freeze_id"],
        "published_artifact_digest": digest(canonical_bytes(freeze) + b"\n"),
        "published_at": freeze["published_at"],
        "retention_record_digests": sorted(retention_record_digests),
    }
    directory_name = PUBLICATION_INTENTS_DIR if intent else PUBLICATION_RECEIPTS_DIR
    directory, directory_identity = _private_record_directory(raw, directory_name, raw_identity)
    record_digest = _store_private_record(directory, record, repository_root, directory_identity)
    validator = _validate_publication_intent if intent else _validate_publication_receipt
    validator(record_digest, record)
    return record_digest


def _store_publication_receipt_locked(freeze, retention_record_digests, raw, raw_identity, repository_root):
    return _store_publication_record_locked(
        freeze, retention_record_digests, raw, raw_identity, repository_root, intent=False,
    )


def _store_publication_intent_locked(freeze, retention_record_digests, raw, raw_identity, repository_root):
    return _store_publication_record_locked(
        freeze, retention_record_digests, raw, raw_identity, repository_root, intent=True,
    )


__all__ = [name for name in globals() if not name.startswith("__")]
