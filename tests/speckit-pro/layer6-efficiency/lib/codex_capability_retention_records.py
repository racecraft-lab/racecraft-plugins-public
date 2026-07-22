#!/usr/bin/env python3
"""Private evidence retention records and publication receipts."""

from __future__ import annotations

if __package__:
    from .codex_capability_retention_lock import *
else:
    from codex_capability_retention_lock import *


def _bounded_directory_names(descriptor, *, limit, label):
    names = []
    with os.scandir(descriptor) as entries:
        for entry in entries:
            if len(names) >= limit:
                raise ValueError(f"{label} exceeds the maximum entry count")
            names.append(entry.name)
    return sorted(names)

def _retention_now():
    return datetime.now(timezone.utc)


def _format_timestamp(value):
    return value.isoformat().replace("+00:00", "Z")


def _private_record_directory(raw, name, expected_raw_identity):
    if not HAS_DESCRIPTOR_RELATIVE_IO or Path(name).name != name:
        raise ValueError("raw evidence records require descriptor-relative directory creation")
    target = raw / name
    raw_descriptor = _private_directory_descriptor(raw, expected_raw_identity)
    child_descriptor = None
    try:
        try:
            os.mkdir(name, mode=0o700, dir_fd=raw_descriptor)
            os.fsync(raw_descriptor)
        except FileExistsError:
            pass
        metadata = os.stat(name, dir_fd=raw_descriptor, follow_symlinks=False)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o700:
            raise ValueError("raw evidence record path must be a private directory")
        child_identity = _stable_directory_identity(metadata)
        child_descriptor = os.open(
            name,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_DIRECTORY", 0),
            dir_fd=raw_descriptor,
        )
        _assert_private_directory_current(target, child_descriptor, child_identity)
        _assert_private_directory_current(raw, raw_descriptor, expected_raw_identity)
        return target, child_identity
    finally:
        if child_descriptor is not None: os.close(child_descriptor)
        os.close(raw_descriptor)


def _store_private_record(directory, value, repository_root, expected_directory_identity):
    payload = canonical_bytes(value) + b"\n"; record_digest = digest(payload)
    target = directory / f"{record_digest.removeprefix('sha256:')}.json"
    if target.exists():
        _, retained = read_content_addressed_private_file(target, repository_root, "raw evidence record")
        if retained != payload: raise ValueError("content-addressed raw evidence record bytes disagree")
        return record_digest
    try:
        _write(
            target, value, private=True, append_only=True,
            expected_parent_identity=expected_directory_identity,
        )
    except FileExistsError:
        _, retained = read_content_addressed_private_file(target, repository_root, "raw evidence record")
        if retained != payload: raise ValueError("content-addressed raw evidence record bytes disagree")
    return record_digest


def _load_private_records(directory, repository_root, label):
    lexical_target = Path(os.path.abspath(directory))
    if lexical_target.name != Path(directory).name:
        raise ValueError(f"{label} path must be an immediate private-root child")
    raw, raw_identity = _validated_raw_evidence_root_binding(
        lexical_target.parent, repository_root,
    )
    target = raw / lexical_target.name
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory_flags = (
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | nofollow
        | getattr(os, "O_DIRECTORY", 0)
    )
    file_flags = (
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | nofollow
        | getattr(os, "O_NONBLOCK", 0)
    )
    raw_descriptor = _private_directory_descriptor(raw, raw_identity)
    directory_descriptor = None
    try:
        try:
            pathname = os.stat(target.name, dir_fd=raw_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            _assert_private_directory_current(raw, raw_descriptor, raw_identity)
            return []
        if not stat.S_ISDIR(pathname.st_mode) or stat.S_IMODE(pathname.st_mode) != 0o700:
            raise ValueError(f"{label} path must be a private directory")
        directory_identity = _stable_directory_identity(pathname)
        directory_descriptor = os.open(
            target.name, directory_flags, dir_fd=raw_descriptor,
        )
        if _stable_directory_identity(os.fstat(directory_descriptor)) != directory_identity:
            raise ValueError(f"{label} directory changed before enumeration")
        names = _bounded_directory_names(
            directory_descriptor, limit=PRIVATE_RECORD_MAX_ENTRIES, label=label,
        )
        records = []
        aggregate_bytes = 0
        aggregate_nodes = [0]
        for name in names:
            if Path(name).name != name or Path(name).suffix != ".json":
                raise ValueError(f"{label} directory contains an undeclared entry")
            entry = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
            if (
                not stat.S_ISREG(entry.st_mode)
                or stat.S_IMODE(entry.st_mode) != 0o600
                or entry.st_nlink != 1
                or entry.st_size > PRIVATE_REFRESH_MAX_BYTES
            ):
                raise ValueError(f"{label} directory contains an undeclared entry")
            if aggregate_bytes + entry.st_size > PRIVATE_RECORD_MAX_TOTAL_BYTES:
                raise ValueError(f"{label} directory exceeds the maximum aggregate size")
            descriptor = os.open(name, file_flags, dir_fd=directory_descriptor)
            try:
                before = os.fstat(descriptor)
                if _stable_file_identity(entry) != _stable_file_identity(before):
                    raise ValueError(f"{label} record changed before it was read")
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
                        raise ValueError(f"{label} exceeds the bounded private-file size")
                after = os.fstat(descriptor)
                current = os.stat(
                    name, dir_fd=directory_descriptor, follow_symlinks=False,
                )
                if (
                    _stable_file_identity(before) != _stable_file_identity(after)
                    or _stable_file_identity(current) != _stable_file_identity(after)
                    or total != after.st_size
                ):
                    raise ValueError(f"{label} record changed while it was being read")
            finally:
                os.close(descriptor)
            raw_bytes = b"".join(chunks)
            aggregate_bytes += total
            record_digest = digest(raw_bytes)
            if name != f"{record_digest.removeprefix('sha256:')}.json":
                raise ValueError(f"{label} must use its exact content digest as the filename")
            record = _parse_json_bytes(raw_bytes, counter=aggregate_nodes)
            if raw_bytes != canonical_bytes(record) + b"\n":
                raise ValueError(f"{label} must use canonical JSON bytes")
            records.append((record_digest, record))
        if _bounded_directory_names(
            directory_descriptor, limit=PRIVATE_RECORD_MAX_ENTRIES, label=label,
        ) != names:
            raise ValueError(f"{label} directory changed during enumeration")
        _assert_private_directory_current(target, directory_descriptor, directory_identity)
        _assert_private_directory_current(raw, raw_descriptor, raw_identity)
        return records
    except OSError as error:
        raise ValueError(f"{label} directory could not be read safely") from error
    finally:
        if directory_descriptor is not None:
            os.close(directory_descriptor)
        os.close(raw_descriptor)


def _validate_retention_record(record_digest, record):
    keys = {"schema_version", "candidate_freeze_id", "raw_evidence_digest", "published_at", "registered_at", "delete_after"}
    if not isinstance(record, dict) or set(record) != keys or record["schema_version"] != "raw-evidence-retention.v1":
        raise ValueError("raw evidence retention record must use the closed v1 shape")
    _need_digest(record_digest, "retention record digest"); _need_digest(record["candidate_freeze_id"], "candidate_freeze_id"); _need_digest(record["raw_evidence_digest"], "raw_evidence_digest")
    published = _parsed_timestamp(record["published_at"], "retention publication timestamp")
    _parsed_timestamp(record["registered_at"], "retention registration timestamp")
    delete_after = _parsed_timestamp(record["delete_after"], "retention deletion deadline")
    if delete_after != published + timedelta(days=RAW_EVIDENCE_RETENTION_DAYS):
        raise ValueError("raw evidence retention deadline must be exactly 30 days after publication")
    return record


def _validate_deletion_record(record_digest, record):
    keys = {"schema_version", "completion_proof", "raw_evidence_digest", "retention_record_digests", "deletion_intent_digest", "delete_after", "deleted_at"}
    if (
        not isinstance(record, dict)
        or set(record) != keys
        or record["schema_version"] != "raw-evidence-deletion.v2"
        or record["completion_proof"] != "post-unlink-nlink-zero-rehashed-v1"
    ):
        raise ValueError("raw evidence deletion record must use the closed v2 completion-proof shape")
    _need_digest(record_digest, "deletion record digest"); _need_digest(record["raw_evidence_digest"], "raw_evidence_digest")
    refs = record["retention_record_digests"]
    if not isinstance(refs, list) or not refs or refs != sorted(set(refs)):
        raise ValueError("raw evidence deletion record requires unique retention records")
    for value in refs: _need_digest(value, "retention_record_digest")
    _need_digest(record["deletion_intent_digest"], "deletion_intent_digest")
    deadline = _parsed_timestamp(record["delete_after"], "deletion deadline")
    if _parsed_timestamp(record["deleted_at"], "deletion timestamp") < deadline:
        raise ValueError("raw evidence deletion precedes its retention deadline")
    return record


def _validate_deletion_intent(record_digest, record):
    keys = {"schema_version", "raw_evidence_digest", "retention_record_digests", "delete_after", "deletion_started_at"}
    if not isinstance(record, dict) or set(record) != keys or record["schema_version"] != "raw-evidence-deletion-intent.v1":
        raise ValueError("raw evidence deletion intent must use the closed v1 shape")
    _need_digest(record_digest, "deletion intent digest"); _need_digest(record["raw_evidence_digest"], "raw_evidence_digest")
    refs = record["retention_record_digests"]
    if not isinstance(refs, list) or not refs or refs != sorted(set(refs)):
        raise ValueError("raw evidence deletion intent requires unique retention records")
    for value in refs: _need_digest(value, "retention_record_digest")
    deadline = _parsed_timestamp(record["delete_after"], "deletion intent deadline")
    if _parsed_timestamp(record["deletion_started_at"], "deletion intent timestamp") < deadline:
        raise ValueError("raw evidence deletion intent precedes its retention deadline")
    return record


def _validate_publication_receipt(record_digest, record):
    keys = {"schema_version", "candidate_freeze_id", "published_artifact_digest", "published_at", "retention_record_digests"}
    if not isinstance(record, dict) or set(record) != keys or record["schema_version"] != "raw-evidence-publication.v1":
        raise ValueError("raw evidence publication receipt must use the closed v1 shape")
    _need_digest(record_digest, "publication receipt digest")
    _need_digest(record["candidate_freeze_id"], "candidate_freeze_id")
    _need_digest(record["published_artifact_digest"], "published_artifact_digest")
    _parsed_timestamp(record["published_at"], "publication receipt timestamp")
    refs = record["retention_record_digests"]
    if not isinstance(refs, list) or not refs or refs != sorted(set(refs)):
        raise ValueError("publication receipt requires unique retention records")
    for value in refs: _need_digest(value, "retention_record_digest")
    return record


def _freeze_raw_evidence_digests(freeze):
    observations = freeze["surface_matrix"]["observations"]
    digests = {
        item["raw_evidence_digest"] for item in observations
        if item["collection_method_id"] != "fixture-enumeration-v1"
    }
    digests.update(item["source_capture_digest"] for item in freeze["official_source_refreshes"])
    digests.update(item["evidence_digest"] for item in freeze["canary_results"])
    for value in digests: _need_digest(value, "raw_evidence_digest")
    return sorted(digests)


def _register_raw_evidence_retention_locked(freeze, raw, raw_identity, repository_root):
    published = _parsed_timestamp(freeze.get("published_at"), "freeze publication timestamp")
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
    existing = {}
    for record_digest, raw_record in _load_private_records(records, repository_root, "retention record"):
        record = _validate_retention_record(record_digest, raw_record)
        key = (record["candidate_freeze_id"], record["raw_evidence_digest"], record["published_at"])
        if key in existing:
            raise ValueError("freeze evidence has multiple retention registration records")
        existing[key] = record_digest
    registered_at = None
    record_digests = []
    for evidence_digest in evidence_digests:
        evidence_path = raw / f"{evidence_digest.removeprefix('sha256:')}.json"
        read_content_addressed_private_file(evidence_path, repository_root, "retained raw evidence")
        key = (freeze["candidate_freeze_id"], evidence_digest, freeze["published_at"])
        if key in existing:
            record_digests.append(existing[key]); continue
        if registered_at is None:
            registered = _retention_now()
            if registered.tzinfo is None or registered.utcoffset() != timedelta(0):
                raise ValueError("retention registration clock must be UTC")
            registered_at = _format_timestamp(registered)
        record = {
            "schema_version": "raw-evidence-retention.v1",
            "candidate_freeze_id": freeze["candidate_freeze_id"],
            "raw_evidence_digest": evidence_digest,
            "published_at": freeze["published_at"],
            "registered_at": registered_at,
            "delete_after": _format_timestamp(published + timedelta(days=RAW_EVIDENCE_RETENTION_DAYS)),
        }
        record_digests.append(_store_private_record(records, record, repository_root, records_identity))
    validate_raw_evidence_root(raw, repository_root)
    return sorted(record_digests)


def _publication_target_matches(path, payload):
    target = Path(path)
    if not target.exists():
        return False
    if _read_bounded_regular_file(target) != payload:
        raise ValueError("publication output already exists with different bytes")
    return True


def _store_publication_receipt_locked(freeze, retention_record_digests, raw, raw_identity, repository_root):
    receipt = {
        "schema_version": "raw-evidence-publication.v1",
        "candidate_freeze_id": freeze["candidate_freeze_id"],
        "published_artifact_digest": digest(canonical_bytes(freeze) + b"\n"),
        "published_at": freeze["published_at"],
        "retention_record_digests": sorted(retention_record_digests),
    }
    directory, directory_identity = _private_record_directory(raw, PUBLICATION_RECEIPTS_DIR, raw_identity)
    receipt_digest = _store_private_record(directory, receipt, repository_root, directory_identity)
    _validate_publication_receipt(receipt_digest, receipt)
    return receipt_digest

__all__ = [name for name in globals() if not name.startswith("__")]
