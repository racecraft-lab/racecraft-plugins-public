#!/usr/bin/env python3
"""Publication authority and bounded retention deadline resolution."""

from __future__ import annotations

from codex_capability_retention_recovery import *


def _effective_retention_deadline(grouped, governing_record_digests, current):
    deadlines = []
    for record, record_digest in grouped:
        registered = _parsed_timestamp(record["registered_at"], "retention registration timestamp")
        if current < registered:
            raise ValueError("retention as-of timestamp precedes the registration record")
        deadline = _parsed_timestamp(record["delete_after"], "retention deletion deadline")
        if record_digest not in governing_record_digests:
            deadline = min(deadline, registered + timedelta(days=RAW_EVIDENCE_PENDING_DAYS))
        deadlines.append(deadline)
    return max(deadlines)


def _load_publication_authority(raw, repository_root):
    retention_records = [
        (_validate_retention_record(record_digest, record), record_digest)
        for record_digest, record in _load_private_records(
            raw / RETENTION_RECORDS_DIR, repository_root, "retention record",
        )
    ]
    retention_by_digest = {record_digest: record for record, record_digest in retention_records}
    publication_intents = [
        (_validate_publication_intent(record_digest, record), record_digest)
        for record_digest, record in _load_private_records(
            raw / PUBLICATION_INTENTS_DIR, repository_root, "publication intent",
        )
    ]
    publication_receipts = [
        (_validate_publication_receipt(record_digest, record), record_digest)
        for record_digest, record in _load_private_records(
            raw / PUBLICATION_RECEIPTS_DIR, repository_root, "publication receipt",
        )
    ]
    intents_by_freeze, governing_record_digests = {}, set()
    for intent, _ in publication_intents:
        freeze_id = intent["candidate_freeze_id"]
        if freeze_id in intents_by_freeze:
            raise ValueError("candidate freeze has multiple publication intents")
        intents_by_freeze[freeze_id] = intent
        refs = set(intent["retention_record_digests"])
        if not refs <= set(retention_by_digest):
            raise ValueError("publication intent references a missing retention record")
        for ref in refs:
            retained = retention_by_digest[ref]
            if retained["candidate_freeze_id"] != freeze_id or retained["published_at"] != intent["published_at"]:
                raise ValueError("publication intent does not bind its freeze retention records")
        governing_record_digests.update(refs)
    receipt_freeze_ids = set()
    for receipt, _ in publication_receipts:
        freeze_id = receipt["candidate_freeze_id"]
        if freeze_id in receipt_freeze_ids:
            raise ValueError("candidate freeze has multiple publication receipts")
        receipt_freeze_ids.add(freeze_id)
        intent = intents_by_freeze.get(freeze_id)
        if intent is None or {
            key: value for key, value in intent.items() if key != "schema_version"
        } != {
            key: value for key, value in receipt.items() if key != "schema_version"
        }:
            raise ValueError("publication receipt lacks its exact durable intent")
    return (
        retention_records, publication_intents, publication_receipts,
        governing_record_digests,
    )


__all__ = [name for name in globals() if not name.startswith("__")]
