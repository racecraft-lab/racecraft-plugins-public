#!/usr/bin/env python3
"""Descriptor-bound raw evidence capture materialization and validation."""

from __future__ import annotations

if __package__:
    from .codex_capability_private import *
else:
    from codex_capability_private import *


def _bounded_source_capture_bytes(capture_bytes):
    try:
        capture_size = memoryview(capture_bytes).nbytes
    except TypeError as error:
        raise ValueError("source capture must be bytes-like") from error
    if capture_size > PRIVATE_REFRESH_MAX_BYTES:
        raise ValueError("source capture exceeds the bounded private-file size")
    return bytes(capture_bytes)


def _raw_lock_kwargs(raw_descriptor, raw_identity):
    if raw_descriptor is None: return {}
    if raw_identity is None: raise ValueError("bound raw evidence operation requires its identity")
    return {
        "raw_descriptor": raw_descriptor, "raw_directory_lock_held": True,
        "expected_raw_identity": raw_identity,
    }


def _raw_capture_binding(raw_root, repository_root, raw_descriptor, raw_identity):
    if raw_descriptor is None:
        return _validated_raw_evidence_root_binding(raw_root, repository_root)
    raw = Path(raw_root)
    validate_raw_evidence_root(
        raw, repository_root, **_raw_lock_kwargs(raw_descriptor, raw_identity),
    )
    return raw, raw_identity


def _store_raw_capture(raw, raw_identity, raw_descriptor, target, payload, repository_root, label):
    recovery = (
        {"directory_lock_held": True, "parent_descriptor": raw_descriptor}
        if raw_descriptor is not None else {}
    )
    if target.exists():
        _recover_append_only_target(target, payload, raw_identity, **recovery)
    else:
        try:
            if raw_descriptor is None:
                _write_private_bytes(
                    target, payload, append_only=True,
                    expected_parent_identity=raw_identity,
                )
            else:
                _write_private_bytes_at(
                    raw_descriptor, raw, target.name, payload, append_only=True,
                    expected_parent_identity=raw_identity, directory_lock_held=True,
                )
        except FileExistsError:
            _recover_append_only_target(target, payload, raw_identity, **recovery)
    _, retained = read_content_addressed_private_file(target, repository_root, label)
    if retained != payload: raise ValueError(f"content-addressed {label} bytes disagree")
    return retained


def _materialize_source_capture_unlocked(
    raw_root, repository_root, capture_bytes, *, raw_descriptor=None, raw_identity=None,
):
    capture_bytes = _bounded_source_capture_bytes(capture_bytes)
    captured = _parse_json_bytes(capture_bytes)
    if not isinstance(captured, list):
        raise ValueError("captured refresh must be a JSON list")
    raw, raw_identity = _raw_capture_binding(
        raw_root, repository_root, raw_descriptor, raw_identity,
    )
    capture_digest = digest(capture_bytes)
    target = raw / f"{capture_digest.removeprefix('sha256:')}.json"
    _store_raw_capture(
        raw, raw_identity, raw_descriptor, target, capture_bytes,
        repository_root, "source capture",
    )
    validate_raw_evidence_root(
        raw, repository_root, **_raw_lock_kwargs(raw_descriptor, raw_identity),
    )
    return capture_digest, target


def validate_source_capture_evidence(
    manifest, refreshes, raw_root, repository_root, *, raw_descriptor=None, raw_identity=None,
):
    capture_digests = {item.get("source_capture_digest") for item in refreshes}
    if len(capture_digests) != 1:
        raise ValueError("source refreshes must bind one complete raw source capture")
    capture_digest = capture_digests.pop(); _need_digest(capture_digest, "source_capture_digest")
    raw = validate_raw_evidence_root(
        raw_root, repository_root, **_raw_lock_kwargs(raw_descriptor, raw_identity),
    )
    target = raw / f"{capture_digest.removeprefix('sha256:')}.json"
    _, capture_bytes = read_content_addressed_private_file(target, repository_root, "source capture")
    expected = normalize_source_refreshes(
        manifest, _parse_json_bytes(capture_bytes), source_capture_digest=capture_digest,
    )
    if refreshes and "retrieved_body_b64" not in refreshes[0]:
        expected = validate_source_refreshes(manifest, expected)["sanitized_refreshes"]
    if canonical_bytes(expected) != canonical_bytes(refreshes):
        raise ValueError("normalized source refresh does not match its retained raw capture")
    return capture_digest


def validate_canary_evidence(
    raw_root, repository_root, result, *, raw_descriptor=None, raw_identity=None,
):
    _need_digest(result.get("evidence_digest"), "evidence_digest")
    raw = validate_raw_evidence_root(
        raw_root, repository_root, **_raw_lock_kwargs(raw_descriptor, raw_identity),
    )
    target = raw / f"{result['evidence_digest'].removeprefix('sha256:')}.json"
    _, evidence_bytes = read_content_addressed_private_file(target, repository_root, "canary evidence")
    validate_canary_result(result, evidence_bytes=evidence_bytes)
    return evidence_bytes


def _materialize_unknown_capture_unlocked(
    raw_root, repository_root, surface, client_identity_id, repository_binding,
    work_item, captured_at, *, raw_descriptor=None, raw_identity=None,
):
    raw, raw_identity = _raw_capture_binding(
        raw_root, repository_root, raw_descriptor, raw_identity,
    )
    record = _unknown_capture_record(surface, client_identity_id, repository_binding, work_item, captured_at)
    stored = canonical_bytes(record) + b"\n"; evidence = digest(stored)
    target = raw / f"{evidence.removeprefix('sha256:')}.json"
    retained = _store_raw_capture(
        raw, raw_identity, raw_descriptor, target, stored,
        repository_root, "unknown capture",
    )
    validate_raw_evidence_root(
        raw, repository_root, **_raw_lock_kwargs(raw_descriptor, raw_identity),
    )
    if digest(retained) != evidence: raise ValueError("unknown capture digest changed")
    return evidence, target


def validate_unknown_observation_evidence(
    observation, raw_root, repository_root, *, raw_descriptor=None, raw_identity=None,
):
    observation = validate_observation(dict(observation))
    if observation["collection_method_id"] != "unknown-observation-v1":
        return
    raw = validate_raw_evidence_root(
        raw_root, repository_root, **_raw_lock_kwargs(raw_descriptor, raw_identity),
    )
    target = raw / f"{observation['raw_evidence_digest'].removeprefix('sha256:')}.json"
    _, retained = read_content_addressed_private_file(target, repository_root, "unknown observation evidence")
    expected = canonical_bytes(_unknown_capture_record(
        observation["surface"], observation["client_identity_id"], observation["repository_binding"],
        observation["work_item"], observation["started_at"],
    )) + b"\n"
    if retained != expected:
        raise ValueError("unknown observation evidence bytes do not match the deterministic attempt record")


__all__ = [name for name in globals() if not name.startswith("__")]
