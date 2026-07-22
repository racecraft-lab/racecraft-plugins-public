#!/usr/bin/env python3
"""Private evidence path binding and materialization."""

from __future__ import annotations

from codex_capability_matrix import *
from codex_capability_append_only import *

def _private_directory_descriptor(path, expected_identity):
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | nofollow | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    if _stable_directory_identity(os.fstat(descriptor)) != expected_identity:
        os.close(descriptor)
        raise ValueError("private output parent changed after validation")
    return descriptor


def _assert_private_directory_current(path, descriptor, expected_identity):
    current = os.stat(path, follow_symlinks=False)
    if (
        _stable_directory_identity(current) != expected_identity
        or _stable_directory_identity(os.fstat(descriptor)) != expected_identity
    ):
        raise ValueError("private output parent changed after validation")


def _fsync_directory(path):
    if os.name == "nt":
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_private_bytes_at(parent_descriptor, parent_path, filename, payload, *, append_only, expected_parent_identity):
    temporary = None; descriptor = None; target_descriptor = None
    try:
        _acquire_append_only_directory_lock(parent_descriptor, wait=True)
        _assert_private_directory_current(parent_path, parent_descriptor, expected_parent_identity)
        for _ in range(64):
            candidate = f"{PRIVATE_TEMPORARY_PREFIX}{secrets.token_hex(16)}"
            try:
                descriptor = os.open(
                    candidate,
                    os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=parent_descriptor,
                )
            except FileExistsError:
                continue
            temporary = candidate
            _acquire_append_only_temporary_lock(descriptor, wait=False)
            break
        if descriptor is None or temporary is None:
            raise ValueError("private output temporary name allocation failed")
        os.fchmod(descriptor, 0o600)
        with os.fdopen(os.dup(descriptor), "wb") as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        _assert_private_directory_current(parent_path, parent_descriptor, expected_parent_identity)
        if append_only:
            os.link(
                temporary, filename, src_dir_fd=parent_descriptor, dst_dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
            target_descriptor = os.open(
                filename,
                os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=parent_descriptor,
            )
            temporary_metadata = os.fstat(descriptor)
            target_before = os.fstat(target_descriptor)
            if (
                not stat.S_ISREG(target_before.st_mode)
                or (target_before.st_dev, target_before.st_ino)
                != (temporary_metadata.st_dev, temporary_metadata.st_ino)
            ):
                raise ValueError("append-only published target does not match its temporary file")
            retained = bytearray()
            while len(retained) <= len(payload):
                chunk = os.read(target_descriptor, min(1024 * 1024, len(payload) + 1 - len(retained)))
                if not chunk: break
                retained.extend(chunk)
            target_after = os.fstat(target_descriptor)
            current_target = os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
            if (
                bytes(retained) != payload
                or _stable_file_identity(target_after) != _stable_file_identity(target_before)
                or _stable_file_identity(current_target) != _stable_file_identity(target_after)
            ):
                raise ValueError("append-only published target changed during verification")
            os.fsync(parent_descriptor)
            os.unlink(temporary, dir_fd=parent_descriptor); temporary = None
            final_target = os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
            if (
                _stable_file_content_identity(final_target)
                != _stable_file_content_identity(target_after)
                or final_target.st_nlink != 1
            ):
                raise ValueError("append-only published target changed during commit")
        else:
            os.replace(
                temporary, filename, src_dir_fd=parent_descriptor, dst_dir_fd=parent_descriptor,
            )
            temporary = None
        os.fsync(parent_descriptor)
        _assert_private_directory_current(parent_path, parent_descriptor, expected_parent_identity)
    finally:
        if target_descriptor is not None:
            try: os.close(target_descriptor)
            except OSError: pass  # Best-effort cleanup must not mask the original failure.
        if descriptor is not None:
            try: os.close(descriptor)
            except OSError: pass  # Best-effort cleanup must not mask the original failure.
        if temporary is not None:
            try: os.unlink(temporary, dir_fd=parent_descriptor)
            except OSError: pass  # Best-effort cleanup must not mask the original failure.


def _write_private_bytes(path, payload, *, append_only=False, expected_parent_identity=None):
    if os.name == "nt":
        raise ValueError("operator-only private-file permissions are not supported on Windows")
    if expected_parent_identity is None:
        raise ValueError("private output requires its validated parent identity")
    if len(payload) > PRIVATE_REFRESH_MAX_BYTES: raise ValueError("private output exceeds the bounded size")
    target = Path(path); parent = target.parent
    parent_descriptor = _private_directory_descriptor(parent, expected_parent_identity)
    try:
        _write_private_bytes_at(
            parent_descriptor, parent, target.name, payload, append_only=append_only,
            expected_parent_identity=expected_parent_identity,
        )
    finally:
        os.close(parent_descriptor)


def _write_public_append_only_bytes(path, payload):
    if not HAS_DESCRIPTOR_RELATIVE_IO:
        raise ValueError("append-only publication requires descriptor-relative filesystem operations")
    if len(payload) > PRIVATE_REFRESH_MAX_BYTES:
        raise ValueError("append-only publication exceeds the bounded size")
    target = Path(os.path.abspath(path)); parent = target.parent
    metadata = os.stat(parent, follow_symlinks=False)
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("append-only publication parent must be a real directory")
    parent_identity = _stable_directory_identity(metadata)
    _recover_append_only_directory(parent, parent_identity, require_content_addressed=False)
    if target.exists():
        _recover_append_only_target(target, payload, parent_identity)
        raise FileExistsError(f"append-only publication target already exists: {target}")
    parent_descriptor = _private_directory_descriptor(parent, parent_identity)
    try:
        _write_private_bytes_at(
            parent_descriptor, parent, target.name, payload, append_only=True,
            expected_parent_identity=parent_identity,
        )
        retained = _read_bounded_regular_file(
            target, allowed_root=parent, expected_parent_identity=parent_identity,
            require_single_link=True,
        )
        if retained != payload:
            raise ValueError("append-only published target bytes disagree")
        _assert_private_directory_current(parent, parent_descriptor, parent_identity)
    finally:
        os.close(parent_descriptor)


def _write(path, value, *, private=False, append_only=False, expected_parent_identity=None):
    payload = canonical_bytes(value) + b"\n"
    if private:
        if os.name == "nt":
            raise ValueError("operator-only private-file permissions are not supported on Windows")
        if expected_parent_identity is None:
            raise ValueError("private output requires its validated parent identity")
        _write_private_bytes(
            path, payload, append_only=append_only,
            expected_parent_identity=expected_parent_identity,
        )
        return
    if append_only:
        _write_public_append_only_bytes(path, payload)
        return
    Path(path).write_bytes(payload)


def validate_raw_evidence_root(raw_root, repository_root):
    if os.name == "nt":
        raise ValueError("operator-only raw evidence permissions are not supported on Windows")
    lexical, repo = Path(os.path.abspath(raw_root)), Path(repository_root).resolve()
    if lexical.is_symlink(): raise ValueError("raw_evidence_root cannot be a symlink")
    raw = lexical.resolve(strict=True)
    if raw == repo or repo in raw.parents or _git_worktree_ancestor(raw):
        raise ValueError("raw_evidence_root must resolve outside every Git worktree")
    _recover_content_addressed_append_only_links(raw)
    _validate_raw_evidence_tree(raw)
    return raw


def _validated_raw_evidence_root_binding(raw_root, repository_root):
    raw = validate_raw_evidence_root(raw_root, repository_root)
    metadata = os.stat(raw, follow_symlinks=False)
    identity = _stable_directory_identity(metadata)
    descriptor = _private_directory_descriptor(raw, identity)
    try:
        validate_raw_evidence_root(raw, repository_root)
        _assert_private_directory_current(raw, descriptor, identity)
    finally:
        os.close(descriptor)
    return raw, identity


def _git_worktree_ancestor(path):
    current = path if path.is_dir() else path.parent
    return any((ancestor / ".git").exists() for ancestor in (current, *current.parents))


def _private_external_file_binding(path, repository_root, label, *, output=False):
    if os.name == "nt":
        raise ValueError("operator-only private-file permissions are not supported on Windows")
    lexical = Path(os.path.abspath(path)); repo = Path(repository_root).resolve()
    if lexical.is_symlink(): raise ValueError(f"{label} cannot be a symlink")
    parent = lexical.parent.resolve(strict=True); resolved = parent / lexical.name
    if resolved == repo or repo in resolved.parents or _git_worktree_ancestor(resolved): raise ValueError(f"{label} must remain outside every Git worktree")
    parent_metadata = os.stat(parent, follow_symlinks=False)
    if not stat.S_ISDIR(parent_metadata.st_mode) or stat.S_IMODE(parent_metadata.st_mode) != 0o700:
        raise ValueError(f"{label} parent directory must use mode 0700")
    parent_identity = _stable_directory_identity(parent_metadata)
    parent_descriptor = _private_directory_descriptor(parent, parent_identity)
    try:
        try:
            os.stat(resolved.name, dir_fd=parent_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            if output:
                return resolved, parent_identity
            raise ValueError(f"{label} must be a regular non-symlink file")
    finally:
        os.close(parent_descriptor)
    _read_bounded_regular_file(
        resolved, required_mode=0o600, allowed_root=parent,
        expected_parent_identity=parent_identity, require_single_link=True,
    )
    return resolved, parent_identity


def validate_private_external_file(path, repository_root, label, *, output=False):
    resolved, _ = _private_external_file_binding(path, repository_root, label, output=output)
    return resolved


def read_private_external_file(path, repository_root, label):
    resolved, parent_identity = _private_external_file_binding(path, repository_root, label)
    return resolved, _read_bounded_regular_file(
        resolved, required_mode=0o600, allowed_root=Path(resolved.anchor),
        expected_parent_identity=parent_identity, require_single_link=True,
    )


def validate_content_addressed_private_file(path, repository_root, label):
    resolved, raw = read_content_addressed_private_file(path, repository_root, label)
    return resolved


def read_content_addressed_private_file(path, repository_root, label):
    resolved, raw = read_private_external_file(path, repository_root, label)
    expected_name = f"{digest(raw).removeprefix('sha256:')}.json"
    if resolved.name != expected_name:
        raise ValueError(f"{label} must use its exact content digest as the filename")
    return resolved, raw


def _bounded_source_capture_bytes(capture_bytes):
    try:
        capture_size = memoryview(capture_bytes).nbytes
    except TypeError as error:
        raise ValueError("source capture must be bytes-like") from error
    if capture_size > PRIVATE_REFRESH_MAX_BYTES:
        raise ValueError("source capture exceeds the bounded private-file size")
    return bytes(capture_bytes)


def _materialize_source_capture_unlocked(raw_root, repository_root, capture_bytes):
    capture_bytes = _bounded_source_capture_bytes(capture_bytes)
    captured = _parse_json_bytes(capture_bytes)
    if not isinstance(captured, list):
        raise ValueError("captured refresh must be a JSON list")
    raw, raw_identity = _validated_raw_evidence_root_binding(raw_root, repository_root)
    capture_digest = digest(capture_bytes)
    target = raw / f"{capture_digest.removeprefix('sha256:')}.json"
    if target.exists():
        _recover_append_only_target(target, capture_bytes, raw_identity)
        _, retained = read_content_addressed_private_file(target, repository_root, "source capture")
        if retained != capture_bytes: raise ValueError("content-addressed source capture bytes disagree")
    else:
        try:
            _write_private_bytes(
                target, capture_bytes, append_only=True,
                expected_parent_identity=raw_identity,
            )
        except FileExistsError:
            _recover_append_only_target(target, capture_bytes, raw_identity)
            _, retained = read_content_addressed_private_file(target, repository_root, "source capture")
            if retained != capture_bytes:
                raise ValueError("concurrent source capture bytes disagree")
    validate_raw_evidence_root(raw, repository_root)
    _, retained = read_content_addressed_private_file(target, repository_root, "source capture")
    if retained != capture_bytes:
        raise ValueError("source capture was not retained under its content identity")
    return capture_digest, target


def validate_source_capture_evidence(manifest, refreshes, raw_root, repository_root):
    capture_digests = {item.get("source_capture_digest") for item in refreshes}
    if len(capture_digests) != 1:
        raise ValueError("source refreshes must bind one complete raw source capture")
    capture_digest = capture_digests.pop(); _need_digest(capture_digest, "source_capture_digest")
    raw = validate_raw_evidence_root(raw_root, repository_root)
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


def validate_canary_evidence(raw_root, repository_root, result):
    _need_digest(result.get("evidence_digest"), "evidence_digest")
    raw = validate_raw_evidence_root(raw_root, repository_root)
    target = raw / f"{result['evidence_digest'].removeprefix('sha256:')}.json"
    _, evidence_bytes = read_content_addressed_private_file(target, repository_root, "canary evidence")
    validate_canary_result(result, evidence_bytes=evidence_bytes)
    return evidence_bytes


def _materialize_unknown_capture_unlocked(raw_root, repository_root, surface, client_identity_id, repository_binding, work_item, captured_at):
    raw, raw_identity = _validated_raw_evidence_root_binding(raw_root, repository_root)
    record = _unknown_capture_record(surface, client_identity_id, repository_binding, work_item, captured_at)
    stored = canonical_bytes(record) + b"\n"; evidence = digest(stored)
    target = raw / f"{evidence.removeprefix('sha256:')}.json"
    if target.exists():
        _recover_append_only_target(target, stored, raw_identity)
        _, retained = read_content_addressed_private_file(target, repository_root, "unknown capture")
        if retained != stored: raise ValueError("content-addressed unknown capture bytes disagree")
    else:
        try:
            _write_private_bytes(
                target, stored, append_only=True,
                expected_parent_identity=raw_identity,
            )
        except FileExistsError:
            _recover_append_only_target(target, stored, raw_identity)
            _, retained = read_content_addressed_private_file(
                target, repository_root, "unknown capture",
            )
            if retained != stored:
                raise ValueError("concurrent unknown capture bytes disagree")
    validate_raw_evidence_root(raw, repository_root)
    _, retained = read_content_addressed_private_file(target, repository_root, "unknown capture")
    if retained != stored or digest(retained) != evidence:
        raise ValueError("unknown capture was not retained under its content identity")
    return evidence, target


def validate_unknown_observation_evidence(observation, raw_root, repository_root):
    observation = validate_observation(dict(observation))
    if observation["collection_method_id"] != "unknown-observation-v1":
        return
    raw = validate_raw_evidence_root(raw_root, repository_root)
    target = raw / f"{observation['raw_evidence_digest'].removeprefix('sha256:')}.json"
    _, retained = read_content_addressed_private_file(target, repository_root, "unknown observation evidence")
    expected = canonical_bytes(_unknown_capture_record(
        observation["surface"], observation["client_identity_id"], observation["repository_binding"],
        observation["work_item"], observation["started_at"],
    )) + b"\n"
    if retained != expected:
        raise ValueError("unknown observation evidence bytes do not match the deterministic attempt record")

__all__ = [name for name in globals() if not name.startswith("__")]
