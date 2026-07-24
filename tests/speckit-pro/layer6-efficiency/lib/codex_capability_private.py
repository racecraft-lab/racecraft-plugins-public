#!/usr/bin/env python3
"""Private evidence path binding and materialization."""

from __future__ import annotations

if __package__:
    from .codex_capability_matrix import *
else:
    from codex_capability_matrix import *
if __package__:
    from .codex_capability_append_only import *
else:
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


def _write_private_bytes_at(
    parent_descriptor, parent_path, filename, payload, *, append_only,
    expected_parent_identity, directory_lock_held=False,
):
    if len(payload) > PRIVATE_REFRESH_MAX_BYTES:
        raise ValueError("private output exceeds the bounded size")
    temporary = None; descriptor = None; target_descriptor = None
    try:
        if not directory_lock_held:
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


def _raw_evidence_root_path(raw_root, repository_root):
    if os.name == "nt":
        raise ValueError("operator-only raw evidence permissions are not supported on Windows")
    lexical, repo = Path(os.path.abspath(raw_root)), Path(repository_root).resolve()
    if lexical.is_symlink(): raise ValueError("raw_evidence_root cannot be a symlink")
    raw = lexical.resolve(strict=True)
    if raw == repo or repo in raw.parents or _git_worktree_ancestor(raw):
        raise ValueError("raw_evidence_root must resolve outside every Git worktree")
    return raw


def validate_raw_evidence_root(
    raw_root, repository_root, *, raw_descriptor=None,
    raw_directory_lock_held=False, expected_raw_identity=None,
):
    raw = _raw_evidence_root_path(raw_root, repository_root)
    if raw_descriptor is not None:
        if not raw_directory_lock_held or expected_raw_identity is None:
            raise ValueError("bound raw evidence validation requires its directory lock and identity")
        _assert_private_directory_current(raw, raw_descriptor, expected_raw_identity)
    _recover_content_addressed_append_only_links(
        raw, raw_descriptor=raw_descriptor,
        raw_directory_lock_held=raw_directory_lock_held,
    )
    _validate_raw_evidence_tree(raw)
    if raw_descriptor is not None:
        _assert_private_directory_current(raw, raw_descriptor, expected_raw_identity)
    return raw


def _validated_raw_evidence_root_binding(raw_root, repository_root):
    raw = _raw_evidence_root_path(raw_root, repository_root)
    metadata = os.stat(raw, follow_symlinks=False)
    identity = _stable_directory_identity(metadata)
    descriptor = _private_directory_descriptor(raw, identity)
    try:
        _acquire_append_only_directory_lock(descriptor, wait=True)
        validate_raw_evidence_root(
            raw,
            repository_root,
            raw_descriptor=descriptor,
            raw_directory_lock_held=True,
            expected_raw_identity=identity,
        )
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


__all__ = [name for name in globals() if not name.startswith("__")]
