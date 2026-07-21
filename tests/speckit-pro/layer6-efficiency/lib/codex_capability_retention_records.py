#!/usr/bin/env python3
"""Private evidence retention records and publication receipts."""

from __future__ import annotations

from codex_capability_private import *

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
    if not directory.exists(): return []
    if directory.is_symlink() or not directory.is_dir(): raise ValueError(f"{label} path must be a private directory")
    entries = sorted(directory.iterdir(), key=lambda path: path.name)
    if any(path.is_symlink() or not path.is_file() or path.suffix != ".json" for path in entries):
        raise ValueError(f"{label} directory contains an undeclared entry")
    records = []
    for path in entries:
        _, raw = read_content_addressed_private_file(path, repository_root, label)
        record = _parse_json_bytes(raw)
        if raw != canonical_bytes(record) + b"\n": raise ValueError(f"{label} must use canonical JSON bytes")
        records.append((digest(raw), record))
    return records


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


def _deletion_intent_file_identity(metadata):
    return {
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
        "size": metadata.st_size,
        "mtime_ns": metadata.st_mtime_ns,
        "mode": stat.S_IMODE(metadata.st_mode),
    }

def _validate_deletion_intent(record_digest, record):
    authority_keys = {"schema_version", "raw_evidence_digest", "retention_record_digests", "delete_after", "deletion_started_at"}
    initial_keys = authority_keys | {"target_file_identity"}
    staged_keys = authority_keys | {"predecessor_deletion_intent_digest", "recovery_proof"}
    restored_keys = staged_keys | {"target_file_identity"}
    version = record.get("schema_version") if isinstance(record, dict) else None
    if not isinstance(record, dict) or (
        version == "raw-evidence-deletion-intent.v2" and set(record) != initial_keys
        or version == "raw-evidence-deletion-intent.v3" and set(record) != staged_keys
        or version == "raw-evidence-deletion-intent.v4" and set(record) != restored_keys
        or version not in {"raw-evidence-deletion-intent.v2", "raw-evidence-deletion-intent.v3", "raw-evidence-deletion-intent.v4"}
    ):
        raise ValueError("raw evidence deletion intent must use the closed v2, v3, or v4 shape")
    _need_digest(record_digest, "deletion intent digest"); _need_digest(record["raw_evidence_digest"], "raw_evidence_digest")
    refs = record["retention_record_digests"]
    if not isinstance(refs, list) or not refs or refs != sorted(set(refs)):
        raise ValueError("raw evidence deletion intent requires unique retention records")
    for value in refs: _need_digest(value, "retention_record_digest")
    if version in {"raw-evidence-deletion-intent.v2", "raw-evidence-deletion-intent.v4"}:
        identity = record["target_file_identity"]
        identity_keys = {"device", "inode", "size", "mtime_ns", "mode"}
        if (
            not isinstance(identity, dict)
            or set(identity) != identity_keys
            or any(
                not isinstance(identity[key], int) or isinstance(identity[key], bool) or identity[key] < 0
                for key in identity_keys
            )
            or identity["mode"] != 0o600
        ):
            raise ValueError("raw evidence deletion intent requires a private target file identity")
    deadline = _parsed_timestamp(record["delete_after"], "deletion intent deadline")
    if _parsed_timestamp(record["deletion_started_at"], "deletion intent timestamp") < deadline:
        raise ValueError("raw evidence deletion intent precedes its retention deadline")
    if version in {"raw-evidence-deletion-intent.v3", "raw-evidence-deletion-intent.v4"}:
        _need_digest(record["predecessor_deletion_intent_digest"], "predecessor_deletion_intent_digest")
        expected_proof = {
            "raw-evidence-deletion-intent.v3": "verified-post-unlink-recovery-stage-v1",
            "raw-evidence-deletion-intent.v4": "verified-post-unlink-restoration-v1",
        }[version]
        if record["recovery_proof"] != expected_proof:
            raise ValueError("raw evidence recovery intent requires its verified phase proof")
    return record

def _terminal_deletion_intents(deletion_intents):
    grouped = {}
    for record, record_digest in deletion_intents:
        grouped.setdefault(record["raw_evidence_digest"], []).append((record, record_digest))
    terminals = {}
    for evidence_digest, records in grouped.items():
        by_digest = {record_digest: record for record, record_digest in records}
        roots = [record_digest for record, record_digest in records if record["schema_version"] == "raw-evidence-deletion-intent.v2"]
        if len(roots) != 1:
            raise ValueError("raw evidence deletion intent chain requires one initial intent")
        successors = {}
        for record, record_digest in records:
            if record["schema_version"] == "raw-evidence-deletion-intent.v2":
                continue
            predecessor = record["predecessor_deletion_intent_digest"]
            prior = by_digest.get(predecessor)
            if prior is None or predecessor in successors:
                raise ValueError("raw evidence deletion intent recovery chain is missing or forked")
            prior_version = prior["schema_version"]
            if (
                record["schema_version"] == "raw-evidence-deletion-intent.v3"
                and prior_version not in {"raw-evidence-deletion-intent.v2", "raw-evidence-deletion-intent.v4"}
                or record["schema_version"] == "raw-evidence-deletion-intent.v4"
                and prior_version != "raw-evidence-deletion-intent.v3"
            ):
                raise ValueError("raw evidence deletion intent recovery phases are out of order")
            if (
                record["retention_record_digests"] != prior["retention_record_digests"]
                or record["delete_after"] != prior["delete_after"]
                or _parsed_timestamp(record["deletion_started_at"], "recovery intent timestamp")
                < _parsed_timestamp(prior["deletion_started_at"], "predecessor intent timestamp")
            ):
                raise ValueError("raw evidence recovery intent changes its governing authority")
            successors[predecessor] = record_digest
        current, visited = roots[0], set()
        while current not in visited:
            visited.add(current)
            if current not in successors:
                break
            current = successors[current]
        if visited != set(by_digest):
            raise ValueError("raw evidence deletion intent recovery chain is disconnected or cyclic")
        terminals[evidence_digest] = (by_digest[current], current)
    return terminals

def _store_staged_recovery_intent(raw, raw_identity, repository_root, deletion_record):
    staged = {
        "schema_version": "raw-evidence-deletion-intent.v3",
        "raw_evidence_digest": deletion_record["raw_evidence_digest"],
        "retention_record_digests": deletion_record["retention_record_digests"],
        "delete_after": deletion_record["delete_after"],
        "deletion_started_at": deletion_record["deleted_at"],
        "predecessor_deletion_intent_digest": deletion_record["deletion_intent_digest"],
        "recovery_proof": "verified-post-unlink-recovery-stage-v1",
    }
    directory, directory_identity = _private_record_directory(raw, DELETION_INTENTS_DIR, raw_identity)
    return staged, _store_private_record(directory, staged, repository_root, directory_identity)

def _store_restored_recovery_intent(raw, raw_identity, repository_root, staged, staged_digest, target, started_at):
    resolved, restored = read_content_addressed_private_file(target, repository_root, "restored raw evidence")
    metadata = os.stat(resolved, follow_symlinks=False)
    if digest(restored) != staged["raw_evidence_digest"] or metadata.st_nlink != 1:
        raise ValueError("restored raw evidence does not preserve its deletion authority")
    recovery = {
        "schema_version": "raw-evidence-deletion-intent.v4",
        "raw_evidence_digest": staged["raw_evidence_digest"],
        "retention_record_digests": staged["retention_record_digests"],
        "target_file_identity": _deletion_intent_file_identity(metadata),
        "delete_after": staged["delete_after"],
        "deletion_started_at": started_at,
        "predecessor_deletion_intent_digest": staged_digest,
        "recovery_proof": "verified-post-unlink-restoration-v1",
    }
    directory, directory_identity = _private_record_directory(raw, DELETION_INTENTS_DIR, raw_identity)
    recovery_digest = _store_private_record(directory, recovery, repository_root, directory_identity)
    if _deletion_intent_file_identity(os.stat(resolved, follow_symlinks=False)) != recovery["target_file_identity"]:
        raise ValueError("restored raw evidence changed while its recovery intent was stored")
    return recovery, recovery_digest

def _store_staged_recovery_completion(raw, raw_identity, repository_root, staged, staged_digest):
    completion = {
        "schema_version": "raw-evidence-deletion.v2",
        "completion_proof": "post-unlink-nlink-zero-rehashed-v1",
        "raw_evidence_digest": staged["raw_evidence_digest"],
        "retention_record_digests": staged["retention_record_digests"],
        "deletion_intent_digest": staged_digest,
        "delete_after": staged["delete_after"],
        "deleted_at": staged["deletion_started_at"],
    }
    directory, directory_identity = _private_record_directory(raw, DELETION_RECORDS_DIR, raw_identity)
    return completion, _store_private_record(directory, completion, repository_root, directory_identity)

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


@contextmanager
def _retention_lock(raw, expected_raw_identity):
    if not HAS_DESCRIPTOR_RELATIVE_IO:
        raise ValueError("raw evidence retention requires descriptor-relative locking")
    try:
        import fcntl
    except ImportError as error:
        raise ValueError("raw evidence retention requires advisory file locking") from error
    raw_descriptor = _private_directory_descriptor(raw, expected_raw_identity)
    lock_descriptor = None
    try:
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
        try:
            fcntl.flock(lock_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("raw evidence retention operation is already in progress") from error
        os.fsync(lock_descriptor)
        os.fsync(raw_descriptor)
        _assert_private_directory_current(raw, raw_descriptor, expected_raw_identity)
        yield
    finally:
        try:
            if lock_descriptor is not None:
                try:
                    _assert_private_directory_current(raw, raw_descriptor, expected_raw_identity)
                finally:
                    try:
                        fcntl.flock(lock_descriptor, fcntl.LOCK_UN)
                    finally:
                        os.close(lock_descriptor)
        finally:
            os.close(raw_descriptor)


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
