#!/usr/bin/env python3
"""Descriptor-bound raw evidence deletion and retention reconciliation."""

from __future__ import annotations

from codex_capability_retention_recovery import *


def _delete_single_link_private_file(
    target, raw, expected_digest, expected_raw_identity, *,
    expected_target_identity, deletion_record, deletion_directory,
    deletion_directory_identity, repository_root, staged_intent=None, quarantined=False,
):
    if not HAS_DESCRIPTOR_RELATIVE_IO:
        raise ValueError("raw evidence deletion requires descriptor-relative path validation")
    filename = Path(target).name
    if Path(target).parent != raw:
        raise ValueError("raw evidence deletion target must be an immediate child of its private root")
    staged_record, staged_digest = staged_intent or (None, None)
    quarantine_filename = (
        staged_record["quarantine_filename"] if staged_record is not None
        else _deletion_quarantine_filename(deletion_record["deletion_intent_digest"])
    )
    canonical_filename = f"{expected_digest.removeprefix('sha256:')}.json"
    expected_filename = quarantine_filename if quarantined else canonical_filename
    if filename != expected_filename:
        raise ValueError("raw evidence deletion target does not match its deletion phase")
    deletion_record_digest = digest(canonical_bytes(deletion_record) + b"\n")
    _validate_deletion_record(deletion_record_digest, deletion_record)
    if deletion_record["raw_evidence_digest"] != expected_digest or Path(deletion_directory).parent != raw:
        raise ValueError("deletion completion record does not bind its private evidence target")
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | nofollow | getattr(os, "O_DIRECTORY", 0)
    file_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | nofollow
    parent_descriptor = descriptor = deletion_directory_descriptor = None
    verified_payload = None; deletion_proved = False; quarantine_durable = False

    def preserve_verified_payload_before_proof():
        if verified_payload is None: return
        if _descriptor_entry_exists(parent_descriptor, filename):
            current, opened = os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False), os.fstat(descriptor)
            if (
                not stat.S_ISREG(current.st_mode)
                or current.st_nlink != 1
                or _stable_file_content_identity(current) != _stable_file_content_identity(opened)
                or _stable_file_content_identity(opened) != _stable_file_content_identity(before)
            ):
                raise ValueError("expired raw evidence changed before deletion recovery")
            return
        _write_private_bytes_at(
            parent_descriptor, raw, filename, verified_payload, append_only=True,
            expected_parent_identity=expected_raw_identity,
        )
        if staged_record is not None:
            restored = _verified_republished_quarantine_metadata(
                raw / filename, raw, expected_digest, expected_raw_identity,
            )
            _store_republished_recovery_intent(
                raw, expected_raw_identity, repository_root, staged_record,
                staged_digest, restored, deletion_record["deleted_at"],
            )
    try:
        deletion_directory_descriptor = _private_directory_descriptor(
            deletion_directory, deletion_directory_identity,
        )
        raw_before = os.stat(raw, follow_symlinks=False)
        parent_descriptor = os.open(raw, directory_flags)
        raw_open = os.fstat(parent_descriptor)
        if (
            _stable_directory_identity(raw_before) != expected_raw_identity
            or _stable_directory_identity(raw_open) != expected_raw_identity
        ):
            raise ValueError("raw evidence root changed before deletion")
        pathname_before = os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
        if not stat.S_ISREG(pathname_before.st_mode) or pathname_before.st_nlink != 1:
            raise ValueError("expired raw evidence must be a single-link regular non-symlink file")
        descriptor = os.open(filename, file_flags, dir_fd=parent_descriptor)
        before = os.fstat(descriptor)
        if (
            _stable_file_identity(pathname_before) != _stable_file_identity(before)
            or stat.S_IMODE(before.st_mode) != 0o600
            or _deletion_intent_file_identity(before) != expected_target_identity
        ):
            raise ValueError("expired raw evidence changed before deletion")
        chunks, total = [], 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, PRIVATE_REFRESH_MAX_BYTES + 1 - total))
            if not chunk: break
            chunks.append(chunk); total += len(chunk)
            if total > PRIVATE_REFRESH_MAX_BYTES: raise ValueError("expired raw evidence exceeds the maximum size")
        payload = b"".join(chunks)
        if total != before.st_size or digest(payload) != expected_digest:
            raise ValueError("expired raw evidence does not match its content identity")
        verified_payload = payload
        current = os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
        raw_current = os.stat(raw, follow_symlinks=False)
        immediately_before = os.fstat(descriptor)
        if current.st_nlink != 1 or immediately_before.st_nlink != 1:
            raise _BlockingHardLinkRace("expired raw evidence acquired an alternate hard link before deletion")
        if _stable_file_identity(current) != _stable_file_identity(before) or _stable_file_identity(immediately_before) != _stable_file_identity(before):
            raise ValueError("expired raw evidence changed after digest verification")
        if _stable_directory_identity(raw_current) != _stable_directory_identity(raw_open):
            raise ValueError("raw evidence root changed before deletion")
        if not quarantined:
            if _descriptor_entry_exists(parent_descriptor, quarantine_filename):
                raise ValueError("raw evidence deletion quarantine already exists")
            os.rename(
                filename, quarantine_filename,
                src_dir_fd=parent_descriptor, dst_dir_fd=parent_descriptor,
            )
            filename = quarantine_filename
        quarantined_pathname = _sync_verified_quarantine(
            parent_descriptor, raw, expected_raw_identity, canonical_filename,
            filename, expected_target_identity, descriptor,
        )
        quarantine_durable = True
        if staged_record is None:
            staged_record, staged_digest = _store_staged_recovery_intent(
                raw, expected_raw_identity, repository_root, deletion_record,
                quarantine_filename, quarantined_pathname,
            )
        _unlink_descriptor_relative(filename, parent_descriptor)
        after_unlink = os.fstat(descriptor)
        if after_unlink.st_nlink != 0:
            raise _BlockingHardLinkRace("expired raw evidence retains an alternate hard link after deletion")
        if _stable_file_content_identity(after_unlink) != _stable_file_content_identity(before):
            raise ValueError("expired raw evidence changed while it was being unlinked")
        os.lseek(descriptor, 0, os.SEEK_SET)
        unlinked_chunks, unlinked_total = [], 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, PRIVATE_REFRESH_MAX_BYTES + 1 - unlinked_total))
            if not chunk: break
            unlinked_chunks.append(chunk); unlinked_total += len(chunk)
            if unlinked_total > PRIVATE_REFRESH_MAX_BYTES: raise ValueError("unlinked raw evidence exceeds the maximum size")
        after_rehash = os.fstat(descriptor); unlinked_payload = b"".join(unlinked_chunks)
        if after_rehash.st_nlink != 0:
            raise _BlockingHardLinkRace("unlinked raw evidence reacquired an alternate hard link")
        if _stable_file_content_identity(after_rehash) != _stable_file_content_identity(after_unlink) or unlinked_payload != verified_payload or digest(unlinked_payload) != expected_digest:
            raise ValueError("unlinked raw evidence does not match the verified content identity")
        os.fsync(parent_descriptor)
        raw_after = os.stat(raw, follow_symlinks=False)
        if _stable_directory_identity(raw_after) != _stable_directory_identity(raw_open):
            raise ValueError("raw evidence root changed during deletion")
        deletion_proved = True
        _, stored_digest = _store_staged_recovery_completion(
            raw, expected_raw_identity, repository_root, staged_record, staged_digest,
            deletion_record["deleted_at"],
        )
        os.fsync(deletion_directory_descriptor)
        _assert_private_directory_current(
            deletion_directory, deletion_directory_descriptor, deletion_directory_identity,
        )
        return stored_digest, staged_record, staged_digest
    except _BlockingHardLinkRace:
        preserve_verified_payload_before_proof()
        raise
    except OSError as error:
        if verified_payload is not None:
            if not deletion_proved and not quarantine_durable:
                preserve_verified_payload_before_proof()
            if quarantine_durable:
                _assert_private_directory_current(raw, parent_descriptor, expected_raw_identity)
            if deletion_proved:
                raise
        raise ValueError("expired raw evidence could not be deleted safely") from error
    except ValueError:
        if verified_payload is not None and not deletion_proved:
            preserve_verified_payload_before_proof()
        raise
    finally:
        if descriptor is not None: os.close(descriptor)
        if parent_descriptor is not None: os.close(parent_descriptor)
        if deletion_directory_descriptor is not None: os.close(deletion_directory_descriptor)


def reconcile_raw_evidence_retention(raw_evidence_root, repository_root, as_of=None, *, apply=False):
    raw, raw_identity = _validated_raw_evidence_root_binding(raw_evidence_root, repository_root)
    if apply:
        if as_of is not None: raise ValueError("cleanup derives its deletion time from current UTC")
        current = _retention_now()
        if current.tzinfo is None or current.utcoffset() != timedelta(0): raise ValueError("cleanup clock must be UTC")
        effective_as_of = _format_timestamp(current)
    else:
        current = _parsed_timestamp(as_of, "retention as-of timestamp"); effective_as_of = as_of
    with _retention_lock(raw, raw_identity):
        validate_raw_evidence_root(raw, repository_root)
        return _reconcile_raw_evidence_retention_locked(
            raw, raw_identity, repository_root, effective_as_of, current, apply=apply,
        )


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


def _reconcile_raw_evidence_retention_locked(raw, raw_identity, repository_root, as_of, current, *, apply):
    all_retention_records = [(_validate_retention_record(record_digest, record), record_digest) for record_digest, record in _load_private_records(raw / RETENTION_RECORDS_DIR, repository_root, "retention record")]
    retention_by_digest = {record_digest: record for record, record_digest in all_retention_records}
    publication_receipts = [(_validate_publication_receipt(record_digest, record), record_digest) for record_digest, record in _load_private_records(raw / PUBLICATION_RECEIPTS_DIR, repository_root, "publication receipt")]
    receipt_freeze_ids, governing_record_digests = set(), set()
    for receipt, _ in publication_receipts:
        if receipt["candidate_freeze_id"] in receipt_freeze_ids:
            raise ValueError("candidate freeze has multiple publication receipts")
        receipt_freeze_ids.add(receipt["candidate_freeze_id"])
        refs = set(receipt["retention_record_digests"])
        if not refs <= set(retention_by_digest):
            raise ValueError("publication receipt references a missing retention record")
        for ref in refs:
            retained = retention_by_digest[ref]
            if retained["candidate_freeze_id"] != receipt["candidate_freeze_id"] or retained["published_at"] != receipt["published_at"]:
                raise ValueError("publication receipt does not bind its freeze retention records")
        governing_record_digests.update(refs)
    pending_record_digests = sorted(set(retention_by_digest) - governing_record_digests)
    retention_records = all_retention_records
    deletion_intents = [(_validate_deletion_intent(record_digest, record), record_digest) for record_digest, record in _load_private_records(raw / DELETION_INTENTS_DIR, repository_root, "deletion intent")]
    deletion_records = [(_validate_deletion_record(record_digest, record), record_digest) for record_digest, record in _load_private_records(raw / DELETION_RECORDS_DIR, repository_root, "deletion record")]
    retention_by_evidence = {}
    for record, record_digest in retention_records:
        retention_by_evidence.setdefault(record["raw_evidence_digest"], []).append((record, record_digest))
    intent_by_evidence = _terminal_deletion_intents(deletion_intents)
    deletion_by_evidence = {}
    for record, record_digest in deletion_records:
        if record["raw_evidence_digest"] in deletion_by_evidence:
            raise ValueError("raw evidence digest has multiple deletion records")
        deletion_by_evidence[record["raw_evidence_digest"]] = (record, record_digest)
    if not set(intent_by_evidence) <= set(retention_by_evidence) or not set(deletion_by_evidence) <= set(intent_by_evidence):
        raise ValueError("deletion state lacks retained evidence authority")
    for evidence_digest, (record, _) in deletion_by_evidence.items():
        intent, intent_digest = intent_by_evidence[evidence_digest]
        if record["deletion_intent_digest"] != intent_digest or record["retention_record_digests"] != intent["retention_record_digests"] or record["delete_after"] != intent["delete_after"]:
            raise ValueError("raw evidence deletion record does not bind its deletion intent")
    retained, deleted, deletion_digests = [], [], []
    for evidence_digest in sorted(retention_by_evidence):
        grouped = retention_by_evidence[evidence_digest]
        record_digests = sorted(record_digest for _, record_digest in grouped)
        deadline = _effective_retention_deadline(grouped, governing_record_digests, current)
        deadline_text = _format_timestamp(deadline); target = raw / f"{evidence_digest.removeprefix('sha256:')}.json"
        deletion_target = target; quarantined = False
        intent = intent_by_evidence.get(evidence_digest)
        if intent is not None:
            intent_record, _ = intent
            if intent_record["retention_record_digests"] != record_digests or intent_record["delete_after"] != deadline_text:
                raise ValueError("raw evidence deletion intent does not bind the complete retention history")
            if current < _parsed_timestamp(intent_record["deletion_started_at"], "deletion intent timestamp"):
                raise ValueError("retention as-of timestamp precedes the deletion intent")
        deletion = deletion_by_evidence.get(evidence_digest)
        if deletion is not None:
            record, record_digest = deletion
            if record["retention_record_digests"] != record_digests or record["delete_after"] != deadline_text:
                raise ValueError("raw evidence deletion record does not bind the complete retention history")
            if current < _parsed_timestamp(record["deleted_at"], "deletion timestamp"):
                raise ValueError("retention as-of timestamp precedes the deletion record")
            quarantine = (
                raw / intent_record["quarantine_filename"]
                if intent_record["schema_version"] == "raw-evidence-deletion-intent.v3"
                else None
            )
            if target.exists() or (quarantine is not None and quarantine.exists()):
                raise ValueError("deletion completion record still has retained raw evidence bytes")
            deleted.append(evidence_digest); deletion_digests.append(record_digest); continue
        if intent is not None:
            if intent_record["schema_version"] == "raw-evidence-deletion-intent.v3":
                if not apply:
                    raise ValueError("staged raw evidence recovery requires cleanup")
                if target.exists():
                    raise ValueError("staged raw evidence deletion target reappeared")
                quarantine = raw / intent_record["quarantine_filename"]
                if quarantine.exists():
                    quarantine_metadata = os.stat(quarantine, follow_symlinks=False)
                    if (
                        not stat.S_ISREG(quarantine_metadata.st_mode)
                        or _deletion_intent_file_identity(quarantine_metadata)
                        != intent_record["target_file_identity"]
                    ):
                        try:
                            quarantine_metadata = _verified_republished_quarantine_metadata(
                                quarantine, raw, evidence_digest, raw_identity,
                            )
                        except ValueError as error:
                            raise ValueError(
                                "staged raw evidence target identity changed before retry"
                            ) from error
                        intent_record, intent_digest = _store_republished_recovery_intent(
                            raw, raw_identity, repository_root, intent_record,
                            intent[1], quarantine_metadata, as_of,
                        )
                        intent = (intent_record, intent_digest)
                        deletion_intents.append(intent)
                        intent_by_evidence[evidence_digest] = intent
                    deletion_record = {
                        "schema_version": "raw-evidence-deletion.v2",
                        "completion_proof": "post-unlink-nlink-zero-rehashed-v1",
                        "raw_evidence_digest": evidence_digest,
                        "retention_record_digests": record_digests,
                        "deletion_intent_digest": intent[1],
                        "delete_after": deadline_text,
                        "deleted_at": as_of,
                    }
                    directory, directory_identity = _private_record_directory(
                        raw, DELETION_RECORDS_DIR, raw_identity,
                    )
                    record_digest, _, _ = _delete_single_link_private_file(
                        quarantine, raw, evidence_digest, raw_identity,
                        expected_target_identity=intent_record["target_file_identity"],
                        deletion_record=deletion_record,
                        deletion_directory=directory,
                        deletion_directory_identity=directory_identity,
                        repository_root=repository_root,
                        staged_intent=intent,
                        quarantined=True,
                    )
                    deleted.append(evidence_digest); deletion_digests.append(record_digest); continue
                raise ValueError("staged raw evidence deletion is missing without durable completion proof")
            quarantine = raw / _deletion_quarantine_filename(intent[1])
            if target.exists() and quarantine.exists():
                raise ValueError("raw evidence deletion has both canonical and quarantined targets")
            if not target.exists() and not quarantine.exists():
                raise ValueError("raw evidence deletion was interrupted after the quarantine unlink")
            deletion_target = target if target.exists() else quarantine
            quarantined = deletion_target == quarantine
            target_metadata = os.stat(deletion_target, follow_symlinks=False)
            if (
                not stat.S_ISREG(target_metadata.st_mode)
                or _deletion_intent_file_identity(target_metadata)
                != intent_record["target_file_identity"]
            ):
                raise ValueError("raw evidence deletion intent target identity changed before retry")
        if current < deadline:
            if intent is not None: raise ValueError("raw evidence deletion intent precedes its governing deadline")
            read_content_addressed_private_file(target, repository_root, "retained raw evidence")
            retained.append(evidence_digest); continue
        if not deletion_target.exists(): raise ValueError("expired raw evidence is missing without a deletion record")
        if not apply: raise ValueError("expired raw evidence requires cleanup")
        if intent is None:
            target_metadata = os.stat(target, follow_symlinks=False)
            if not stat.S_ISREG(target_metadata.st_mode) or target_metadata.st_nlink != 1:
                raise ValueError("expired raw evidence must be a single-link regular non-symlink file")
            intent_record = {
                "schema_version": "raw-evidence-deletion-intent.v2",
                "raw_evidence_digest": evidence_digest,
                "retention_record_digests": record_digests,
                "target_file_identity": _deletion_intent_file_identity(target_metadata),
                "delete_after": deadline_text,
                "deletion_started_at": as_of,
            }
            intent_directory, intent_directory_identity = _private_record_directory(
                raw, DELETION_INTENTS_DIR, raw_identity,
            )
            intent_digest = _store_private_record(
                intent_directory, intent_record, repository_root, intent_directory_identity,
            )
            deletion_intents.append((intent_record, intent_digest))
            intent_by_evidence[evidence_digest] = (intent_record, intent_digest)
        else:
            intent_record, intent_digest = intent
        deletion_record = {
            "schema_version": "raw-evidence-deletion.v2",
            "completion_proof": "post-unlink-nlink-zero-rehashed-v1",
            "raw_evidence_digest": evidence_digest,
            "retention_record_digests": record_digests,
            "deletion_intent_digest": intent_digest,
            "delete_after": deadline_text,
            "deleted_at": as_of,
        }
        directory, directory_identity = _private_record_directory(raw, DELETION_RECORDS_DIR, raw_identity)
        record_digest, staged_record, staged_digest = _delete_single_link_private_file(
            deletion_target, raw, evidence_digest, raw_identity,
            expected_target_identity=intent_record["target_file_identity"],
            deletion_record=deletion_record,
            deletion_directory=directory,
            deletion_directory_identity=directory_identity,
            repository_root=repository_root,
            quarantined=quarantined,
        )
        deletion_intents.append((staged_record, staged_digest))
        intent_by_evidence[evidence_digest] = (staged_record, staged_digest)
        deleted.append(evidence_digest); deletion_digests.append(record_digest)
    validate_raw_evidence_root(raw, repository_root)
    return {
        "schema_version": "raw-evidence-retention-report.v1", "mode": "cleanup" if apply else "verify", "as_of": as_of,
        "retained_evidence_digests": retained, "deleted_evidence_digests": deleted,
        "retention_record_digests": sorted(record_digest for _, record_digest in retention_records),
        "pending_retention_record_digests": pending_record_digests,
        "publication_receipt_digests": sorted(record_digest for _, record_digest in publication_receipts),
        "deletion_intent_digests": sorted(record_digest for _, record_digest in deletion_intents),
        "deletion_record_digests": sorted(deletion_digests),
    }

__all__ = [name for name in globals() if not name.startswith("__")]
