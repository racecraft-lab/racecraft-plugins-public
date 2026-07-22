#!/usr/bin/env python3
"""Retention registration and durable publication authority records."""

from __future__ import annotations

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


def _register_raw_evidence_retention_locked(freeze, raw, raw_identity, repository_root):
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
    validate_raw_evidence_root(raw, repository_root)
    return sorted(record_digests)


def _publication_target_matches(path, payload):
    target = Path(path)
    if not target.exists():
        return False
    _recover_append_only_target(target, payload)
    if _read_bounded_regular_file(target, require_single_link=True) != payload:
        raise ValueError("publication output already exists with different bytes")
    return True


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
