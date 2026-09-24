"""Fail-closed validation for the one reviewed trigger evidence carry-forward.

The predecessor is an external, immutable evidence source.  This module never
opens its SQLite ledger as a database and never returns a pathname for a caller
to reopen.  Every external byte is read once through a bounded descriptor and
is the byte string that is hashed, parsed, or replay-bound.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import stat
import subprocess
from types import SimpleNamespace
from typing import Callable

import trigger_comparison as comparison


SCHEMA_VERSION = "trigger-case-carry-forward/v1"
INDEX_SCHEMA_VERSION = "trigger-evidence-index/v2"
MULTI_GENERATION_SCHEMA_VERSION = "trigger-case-carry-forward/v2"
CLEAN_BOUNDARY_MODE = "clean-boundary-adoption/v1"
MULTI_SOURCE_INDEX_SCHEMA_VERSION = "trigger-evidence-index/v3"
DUAL_REPLAY_SCHEMA_VERSION = "trigger-dual-replay/v1"
OBSERVER_REPLAY_SCHEMA_VERSION = "trigger-observer-replay/v1"
COMPATIBILITY_SCHEMA_VERSION = "codex-relative-skill-read/v1"
OLD_OBSERVER_SHA256 = "c5faa93ab3c25340e38933b69ba1968835a501ff78a4344354f5c36e45470a72"
PARTIAL_EXPERIMENT_SHA256 = "959b2740ff161e155f5d1f5d645944a7f603d614479a92b3c056c29bafb96f51"
BEHAVIOR_FAILURES = frozenset({
    "l2-1b43ca2d753dec02b20c5e17",
    "l2-d714c484e5bbf90475418772",
})
PARTIAL_CASE_ID = "l2-f714040c928fadaabb26eab2"
EXPECTED_RAW_SHA256 = {
    "manifest": "32189f6581d6b78b1910305755b3107421fb13f3d6c9f7faf5c8b7bb8f36a98b",
    "approval": "54b0c442743c6d53bd6615795692239f44f464fc598d78d4fb155a7e68c98afb",
    "ledger": "933372dd5118219b83d79f537049e9a46345d626f651342fb4b934105103cddc",
    "interrupted_ledger": "432a3afbf6cdc39723e49f047c70ed66e3fe9a8f24dfacd3388cba54b8e04c5a",
    "terminal_evidence": "913c1b9063ce98d49f43a119115b9dc4b069aa8d22a0ff50f168d6e444979f17",
    "terminal_review": "7170f3429f8c81c2d34f545e6d48f0ae43392c0d2de368a6a881fc0d1f2b215a",
    "cohort": "3f2bcbf40d4424da12764d23843d40d177006a5d21db3da386a50216acd2cdc8",
    "partial_index": "3b4282e2d4df37bf69c15aff00d56f693ede851f3b4fd19dc0b11ab01c2eb6d5",
    "source_stability_review": "e079e1dc4b7aa86c1abc7291cb2e45194a60e4ce9cdf04a7f6b44e56ec65a201",
    "compatibility_review": "10fadc231a41c23298802aab8f847745bd00b19652ce07bbad7b43ab1c5337bb",
    "terminal_cleanup": "161a9e8ace4f9116a9ee9f5d48af3f77a8001bb23c534fab7d1a90dfa28fa49a",
    "terminal_launch": "772151829c4aa62686545046b92600897d2d1fd731bb67a674aa58d2f411afdf",
}
EXPECTED_TERMINAL_TRIAL_SHA256 = [
    "6faec4e8785907fa491a07a68375a8ec3c421c6bc0a0413591b92485daecf42b",
    "ce6895049987bb7414cecbd8a219a7fd4c6c8521bc52cd8448642822380e2a9a",
    "832f2926c955b73bef82d8d168c8a1947e516d10ff081ef2172bedf8190a6621",
]
EXPECTED_ACCOUNTING = {
    "logical_full_trials": 1302,
    "carried_trials": 411,
    "fresh_launch_ceiling": 891,
    "historical_charged_launches": 414,
    "maximum_total_charged_attempts": 1305,
}
PROJECTION_FIELDS = (
    "selected",
    "selected_skill",
    "selected_skill_set",
    "consulted_skills",
    "requested_model",
    "resolved_model",
    "model_identity_check",
    "observation_scope",
    "qualification_observed",
    "qualification_eligible",
    "execution_checks",
    "cleanup",
)
_SHA256 = re.compile(r"[0-9a-f]{64}", re.ASCII)
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", re.ASCII)
_MAX_JSON = 8 * 1024 * 1024
_MAX_STREAM = 2 * 1024 * 1024
_MAX_LEDGER = 2 * 1024 * 1024


@dataclass(frozen=True)
class CarryForwardPlan:
    component: dict
    component_sha256: str
    source_root: Path
    review_root: Path
    source_manifest: dict
    partial_manifest: dict
    source_index: dict
    carried: frozenset[tuple[str, str]]
    carried_trials: frozenset[tuple[str, str, int]]
    fresh: frozenset[tuple[str, str]]
    fresh_trials: frozenset[tuple[str, str, int]]
    carried_case_ids: tuple[str, ...]
    fresh_case_ids: tuple[str, ...]
    carried_models: dict[str, frozenset]
    fresh_launch_ceiling: int = 891
    historical_charged_launches: int = 414


@dataclass(frozen=True)
class HistoricalSegmentPlan:
    generation_id: str
    root: Path
    review_root: Path
    manifest: dict
    approval: dict
    snapshot: dict
    ledger_sha256: str
    complete_pairs: frozenset[tuple[str, str]]
    complete_trials: frozenset[tuple[str, str, int]]
    invalid_identities: frozenset[tuple[str, str, int]]
    charged_trials: int
    invalid_trials: int
    unknown_trials: int
    evidence: tuple[dict, ...]
    nested_carry_forward: dict | None
    lease_path: Path


@dataclass(frozen=True)
class HistoricalEvidenceSource:
    generation_id: str
    root: Path
    arm: str
    manifest: dict
    index: dict
    case_ids: tuple[str, ...]
    models: dict[str, frozenset]


@dataclass(frozen=True)
class MultiGenerationPlan:
    component: dict
    component_sha256: str
    logical_manifest: dict
    histories: tuple[HistoricalSegmentPlan, ...]
    sources: tuple[HistoricalEvidenceSource, ...]
    carried: frozenset[tuple[str, str]]
    carried_trials: frozenset[tuple[str, str, int]]
    fresh: frozenset[tuple[str, str]]
    fresh_trials: frozenset[tuple[str, str, int]]
    carried_models: dict[str, frozenset]
    fresh_launch_ceiling: int
    historical_charged_launches: int
    maximum_total_charged_attempts: int


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _json(payload: bytes, label: str):
    try:
        return json.loads(payload, object_pairs_hook=_unique_pairs)
    except (json.JSONDecodeError, UnicodeError):
        raise ValueError(f"{label} is not strict JSON") from None


def _normalized_reference(value: object, label: str) -> tuple[PurePosixPath, str]:
    comparison._require(isinstance(value, dict) and set(value) == {"path", "sha256"},
                        f"{label} reference is malformed")
    raw_path, digest = value["path"], value["sha256"]
    comparison._require(isinstance(raw_path, str) and raw_path and "\\" not in raw_path
                        and not raw_path.startswith("/") and isinstance(digest, str)
                        and _SHA256.fullmatch(digest) is not None,
                        f"{label} reference is malformed")
    relative = PurePosixPath(raw_path)
    comparison._require(relative.as_posix() == raw_path
                        and all(part not in {"", ".", ".."} for part in relative.parts),
                        f"{label} path is not normalized beneath its root")
    return relative, digest


def _file_identity(value: os.stat_result) -> tuple[int, ...]:
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
            value.st_ctime_ns, stat.S_IFMT(value.st_mode), stat.S_IMODE(value.st_mode),
            value.st_nlink, value.st_uid)


def _directory_identity(value: os.stat_result) -> tuple[int, ...]:
    return (value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode),
            stat.S_IMODE(value.st_mode), value.st_uid)


def _safe_directory(value: os.stat_result, label: str) -> None:
    comparison._require(stat.S_ISDIR(value.st_mode) and not stat.S_ISLNK(value.st_mode)
                        and value.st_uid == os.getuid()
                        and not value.st_mode & (stat.S_IWGRP | stat.S_IWOTH),
                        f"{label} directory ownership or mode is unsafe")


def _safe_absolute_ancestor(value: os.stat_result, label: str, *, declared_root: bool) -> None:
    comparison._require(stat.S_ISDIR(value.st_mode) and not stat.S_ISLNK(value.st_mode),
                        f"{label} absolute ancestor is not a real directory")
    writable = bool(value.st_mode & (stat.S_IWGRP | stat.S_IWOTH))
    if declared_root:
        comparison._require(value.st_uid == os.getuid() and not writable,
                            f"{label} root ownership or mode is unsafe")
        return
    comparison._require(value.st_uid in {0, os.getuid()}
                        and (not writable or value.st_uid == 0 and value.st_mode & stat.S_ISVTX),
                        f"{label} absolute ancestor ownership or mode is unsafe")


def _canonical_root(raw_root: object, label: str) -> Path:
    comparison._require(isinstance(raw_root, str) and Path(raw_root).is_absolute(),
                        f"{label} root must be an absolute canonical path")
    root = Path(raw_root)
    comparison._require(str(root) == raw_root and root != Path("/")
                        and all(part not in {"", ".", ".."} for part in root.parts[1:]),
                        f"{label} root path is not canonical")
    return root


def _open_absolute_root(root: Path, label: str, flags: int) -> tuple[list[int], list[tuple[int, ...]], list[str]]:
    """Retain a no-follow descriptor for every component from `/` to root."""
    descriptors = [os.open("/", flags)]
    anchor = os.fstat(descriptors[0])
    _safe_absolute_ancestor(anchor, label, declared_root=False)
    identities = [_directory_identity(anchor)]
    components: list[str] = []
    try:
        for index, component in enumerate(root.parts[1:]):
            parent = descriptors[-1]
            before = os.stat(component, dir_fd=parent, follow_symlinks=False)
            declared = index == len(root.parts[1:]) - 1
            _safe_absolute_ancestor(before, label, declared_root=declared)
            child = os.open(component, flags, dir_fd=parent)
            opened = os.fstat(child)
            _safe_absolute_ancestor(opened, label, declared_root=declared)
            comparison._require(_directory_identity(before) == _directory_identity(opened),
                                f"{label} absolute ancestor changed before open")
            descriptors.append(child)
            identities.append(_directory_identity(opened))
            components.append(component)
    except BaseException:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
        raise
    return descriptors, identities, components


def _read_external_file(root: Path, reference: object, label: str, *, max_bytes: int,
                        verify_digest: bool) -> bytes:
    """Read one safe external file by descriptor and return the verified bytes."""
    relative, expected_digest = _normalized_reference(reference, label)
    root = _canonical_root(str(root), label)
    directory_flags = (os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
                       | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_DIRECTORY", 0))
    file_flags = (os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
                  | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    directories: list[int] = []
    identities: list[tuple[int, ...]] = []
    components: list[str] = []
    descriptor: int | None = None
    try:
        directories, identities, components = _open_absolute_root(root, label, directory_flags)
        parent = directories[-1]
        for component in relative.parts[:-1]:
            before = os.stat(component, dir_fd=parent, follow_symlinks=False)
            _safe_directory(before, label)
            child = os.open(component, directory_flags, dir_fd=parent)
            opened = os.fstat(child)
            _safe_directory(opened, label)
            comparison._require(_directory_identity(before) == _directory_identity(opened),
                                f"{label} directory changed before open")
            directories.append(child)
            identities.append(_directory_identity(opened))
            components.append(component)
            parent = child
        filename = relative.parts[-1]
        pathname = os.stat(filename, dir_fd=parent, follow_symlinks=False)
        comparison._require(stat.S_ISREG(pathname.st_mode) and not stat.S_ISLNK(pathname.st_mode),
                            f"{label} is not a regular non-symlink file")
        descriptor = os.open(filename, file_flags, dir_fd=parent)
        before = os.fstat(descriptor)
        comparison._require(_file_identity(pathname) == _file_identity(before)
                            and stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
                            and not before.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
                            and before.st_nlink == 1,
                            f"{label} ownership, mode, or identity is unsafe")
        comparison._require(before.st_size <= max_bytes, f"{label} exceeds its size limit")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, max_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            comparison._require(total <= max_bytes, f"{label} exceeds its size limit")
        after = os.fstat(descriptor)
        current = os.stat(filename, dir_fd=parent, follow_symlinks=False)
        comparison._require(_file_identity(before) == _file_identity(after)
                            == _file_identity(current) and total == after.st_size,
                            f"{label} changed while it was read")
        comparison._require(all(_directory_identity(os.fstat(directory)) == identity
                                for directory, identity in zip(directories, identities, strict=True)),
                            f"{label} retained ancestor descriptor changed while it was read")
        for index, component in enumerate(components):
            current_ancestor = os.stat(component, dir_fd=directories[index], follow_symlinks=False)
            comparison._require(_directory_identity(current_ancestor) == identities[index + 1],
                                f"{label} ancestor pathname changed while it was read")
        comparison._require(_file_identity(os.stat(filename, dir_fd=parent, follow_symlinks=False))
                            == _file_identity(after), f"{label} pathname changed while it was read")
        payload = b"".join(chunks)
    except OSError as exc:
        raise ValueError(f"{label} could not be read safely: {exc}") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        for directory in reversed(directories):
            os.close(directory)
    if verify_digest:
        comparison._require(hashlib.sha256(payload).hexdigest() == expected_digest,
                            f"{label} digest changed")
    return payload


def read_external_file(root: Path, reference: object, label: str, *, max_bytes: int) -> bytes:
    """Read one safe external file by descriptor and return the verified bytes."""
    return _read_external_file(root, reference, label, max_bytes=max_bytes, verify_digest=True)


def _read_external_path(root: Path, relative: PurePosixPath, label: str, *, max_bytes: int) -> bytes:
    """Read an unbound path for later verification by its signed tree manifest."""
    reference = {"path": relative.as_posix(), "sha256": "0" * 64}
    return _read_external_file(root, reference, label, max_bytes=max_bytes, verify_digest=False)


def _read_json(root: Path, reference: object, label: str, *, max_bytes: int = _MAX_JSON):
    return _json(read_external_file(root, reference, label, max_bytes=max_bytes), label)


def _assert_sidecars_absent(root: Path, ledger_reference: object) -> None:
    relative, _digest = _normalized_reference(ledger_reference, "predecessor ledger")
    comparison._require(len(relative.parts) == 1, "predecessor ledger must be at the source root")
    for suffix in ("-journal", "-wal", "-shm"):
        sidecar = root / f"{relative.as_posix()}{suffix}"
        try:
            os.stat(sidecar, follow_symlinks=False)
        except FileNotFoundError:
            continue
        except OSError:
            raise ValueError("predecessor ledger sidecar state is unreadable") from None
        raise ValueError("predecessor ledger has a live journal, WAL, or shared-memory sidecar")


def _validate_inactive_lease(path: object) -> None:
    """Read and non-blockingly lock the exact retained global-lease pathname."""
    import fcntl
    lease = _canonical_root(str(Path(path).parent), "historical lease") / Path(path).name
    comparison._require(isinstance(path, str) and Path(path).is_absolute()
                        and str(lease) == path, "historical lease path is malformed")
    try:
        descriptor = os.open(lease, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0))
    except OSError as exc:
        raise ValueError(f"historical lease could not be inspected: {exc}") from None
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        comparison._require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                            and not info.st_mode & (stat.S_IWGRP | stat.S_IWOTH),
                            "historical lease ownership or mode is unsafe")
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("historical campaign lease is active") from None
        try:
            value = _json(stream.read(), "historical lease")
            comparison._require(isinstance(value, dict)
                                and set(value) == {"schema_version", "state", "campaign"}
                                and value["schema_version"] == "trigger-global-lease/v1"
                                and value["state"] == "idle"
                                and isinstance(value["campaign"], str),
                                "historical campaign lease is not terminal and idle")
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def _validate_history_ownership(
    value: object, source_root: Path, charged_pairs: dict[tuple[str, str], list[dict]],
    manifest_cases: dict[str, dict],
    *, check_lease: bool = True,
) -> Path:
    fields = {"runners", "groups", "workspaces", "lease_path", "cases"}
    comparison._require(isinstance(value, dict) and set(value) == fields
                        and isinstance(value["runners"], list)
                        and isinstance(value["groups"], list)
                        and isinstance(value["workspaces"], list)
                        and isinstance(value["cases"], list),
                        "historical ownership inventory is malformed")
    expected_pairs = tuple(charged_pairs)
    supplied_pairs = tuple((item.get("arm"), item.get("case_id"))
                           for item in value["cases"] if isinstance(item, dict))
    comparison._require(len(supplied_pairs) == len(value["cases"])
                        and supplied_pairs == expected_pairs,
                        "historical ownership cases differ from every reserved pair")
    derived: dict[str, list] = {"runners": [], "groups": [], "workspaces": []}
    case_fields = {"arm", "case_id", "root", "file_count", "files_manifest_sha256"}
    for case in value["cases"]:
        arm, case_id = case["arm"], case["case_id"]
        expected_root = source_root / "serial" / arm / case_id
        comparison._require(set(case) == case_fields
                            and case["root"] == str(expected_root),
                            "historical ownership case root or descriptor is malformed")
        payloads = _case_tree_bytes(source_root, case)
        launch = _json(payloads.get("launch.json", b""), "historical runner launch")
        execution = _json(payloads.get("execution.json", b""), "historical runner execution")
        cleanup = _json(payloads.get("evidence/arm-cleanup.json", b""),
                        "historical runner cleanup")
        context = _json(payloads.get("evidence/replay-context.json", b""),
                        "historical replay context")
        host = context.get("host")
        workspace = (context.get("plugin_root") if host == "claude"
                     else context.get("workspace") if host == "codex" else None)
        comparison._require(set(launch) == {"pid", "command", "started_at"}
                            and type(launch["pid"]) is int and launch["pid"] > 0
                            and isinstance(launch["command"], list) and launch["command"]
                            and all(isinstance(part, str) and part for part in launch["command"])
                            and type(launch["started_at"]) is float,
                            "historical runner ownership fingerprint is malformed")
        comparison._require(type(execution.get("finished_at")) is float
                            and type(execution.get("runner_exit_code")) is int
                            and cleanup.get("schema_version") == "trigger-arm-cleanup/v1"
                            and cleanup.get("workspace_removed") is True
                            and cleanup.get("cleanup_error") is None
                            and cleanup.get("runner_exit_code") == execution["runner_exit_code"]
                            and host == manifest_cases[case_id]["host"]
                            and isinstance(workspace, str)
                            and cleanup.get("workspace") == workspace
                            and _workspace_is_absent(workspace),
                            "historical completion or workspace ownership fingerprint is malformed")
        derived["runners"].append(launch)
        derived["workspaces"].append(workspace)
        trial_names = sorted(name for name in payloads if name.endswith(".trial.json"))
        trials = [_json(payloads[name], "historical trial ownership") for name in trial_names]
        ordinals = [trial.get("trial_number") for trial in trials]
        complete = {row["status"] for row in charged_pairs[(arm, case_id)]} == {"complete"}
        comparison._require(bool(ordinals) and len(ordinals) == len(set(ordinals))
                            and all(type(number) is int and number in {1, 2, 3}
                                    for number in ordinals)
                            and (sorted(ordinals) == [1, 2, 3] if complete else True),
                            "historical trial ownership inventory is incomplete")
        for trial in trials:
            pid, pgid = trial.get("child_pid"), trial.get("child_pgid")
            comparison._require(trial.get("case_id") == case_id
                                and type(pid) is int and pid > 0 and pid == pgid
                                and trial.get("cleanup_verified") is True
                                and trial.get("cleanup_error") is None
                                and trial.get("unexpected_descendants") is False
                                and isinstance(trial.get("cleanup_observations"), list)
                                and trial["cleanup_observations"]
                                and all(observation.get("pgid") == pgid
                                        and observation.get("errno") == 3
                                        for observation in trial["cleanup_observations"]),
                                "historical child process-group ownership fingerprint is malformed")
            derived["groups"].append({"pgid": pgid,
                                      "completed_at": execution["finished_at"]})
    comparison._require(value["runners"] == derived["runners"]
                        and value["groups"] == derived["groups"]
                        and value["workspaces"] == derived["workspaces"],
                        "historical ownership inventory omits or changes derived identities")
    inventory = {"runners": derived["runners"], "groups": derived["groups"]}
    comparison._require(_ownership_is_absent(inventory, _current_process_snapshot()),
                        "a historical runner or child process group may still be live")
    raw_lease = value["lease_path"]
    comparison._require(isinstance(raw_lease, str) and Path(raw_lease).is_absolute(),
                        "historical lease path is malformed")
    lease_path = (_canonical_root(str(Path(raw_lease).parent), "historical lease")
                  / Path(raw_lease).name)
    comparison._require(str(lease_path) == raw_lease,
                        "historical lease path is malformed")
    if check_lease:
        _validate_inactive_lease(raw_lease)
    return lease_path


def _validate_historical_segment(
    value: object, logical_manifest: dict, fresh_output: Path, *, check_lease: bool = True,
) -> HistoricalSegmentPlan:
    """Validate one read-only terminal source; never apply destination resume rules."""
    fields = {"generation_id", "output_root", "review_root", "manifest", "approval", "ledger",
              "terminal_ledger", "inventory", "nested_carry_forward", "evidence",
              "ownership", "review"}
    comparison._require(isinstance(value, dict) and set(value) == fields,
                        "historical segment is malformed")
    generation_id = value["generation_id"]
    comparison._require(isinstance(generation_id, str) and bool(generation_id.strip()),
                        "historical segment lacks generation identity")
    root = _canonical_root(value["output_root"], "historical output")
    review_root = _canonical_root(value["review_root"], "historical review")
    logical_output = Path(logical_manifest["output_directory"])
    comparison._require(all(root != other
                            and not root.is_relative_to(other)
                            and not other.is_relative_to(root)
                            for other in (fresh_output, logical_output)),
                        "historical and fresh output roots must not overlap")
    comparison._require(all(review_root != other
                            and not review_root.is_relative_to(other)
                            and not other.is_relative_to(review_root)
                            for other in (root, fresh_output,
                                          Path(logical_manifest["output_directory"]))),
                        "historical review root must be outside output and destination trees")
    directory_flags = (os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
                       | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_DIRECTORY", 0))
    review_descriptors, _review_identities, _review_components = _open_absolute_root(
        review_root, "historical review", directory_flags)
    for descriptor in reversed(review_descriptors):
        os.close(descriptor)
    for name in ("manifest", "approval", "ledger", "terminal_ledger", "inventory"):
        _normalized_reference(value[name], f"historical {name.replace('_', ' ')}")
    review = value["review"]
    review_fields = {"reviewer", "review_id", "reviewed_at", "source_commit",
                     "source_tree_sha256", "segment_sha256"}
    comparison._require(isinstance(review, dict) and set(review) == review_fields
                        and review["reviewer"] == "independent-reviewer"
                        and isinstance(review["review_id"], str) and bool(review["review_id"].strip())
                        and isinstance(review["source_commit"], str)
                        and re.fullmatch(r"[0-9a-f]{40}", review["source_commit"])
                        and isinstance(review["source_tree_sha256"], str)
                        and _SHA256.fullmatch(review["source_tree_sha256"]),
                        "historical segment review is malformed")
    comparison._require(isinstance(review["reviewed_at"], str)
                        and _TIMESTAMP.fullmatch(review["reviewed_at"]),
                        "historical segment review timestamp is invalid")
    try:
        datetime.fromisoformat(review["reviewed_at"][:-1] + "+00:00")
    except ValueError:
        raise ValueError("historical segment review timestamp is invalid") from None
    core = {key: value[key] for key in fields - {"review"}}
    comparison._require(review["segment_sha256"] == comparison.json_digest(core),
                        "historical segment review does not bind exact bytes and cleanup")
    _assert_sidecars_absent(root, value["ledger"])
    raw_manifest = read_external_file(root, value["manifest"], "historical manifest", max_bytes=_MAX_JSON)
    raw_approval = read_external_file(root, value["approval"], "historical approval", max_bytes=_MAX_JSON)
    raw_ledger = read_external_file(root, value["ledger"], "historical ledger", max_bytes=_MAX_LEDGER)
    raw_terminal = read_external_file(root, value["terminal_ledger"], "historical terminal ledger",
                                      max_bytes=_MAX_JSON)
    raw_inventory = read_external_file(root, value["inventory"], "historical inventory", max_bytes=_MAX_JSON)
    manifest = _json(raw_manifest, "historical manifest")
    approval = _json(raw_approval, "historical approval")
    terminal = _json(raw_terminal, "historical terminal ledger")
    inventory = _json(raw_inventory, "historical inventory")
    cases = comparison.validate_experiment(manifest)
    version = approval.get("schema_version")
    comparison.validate_inventory_binding(
        logical_manifest if version == "trigger-campaign-approval/v5" else manifest,
        inventory)
    immutable = set(logical_manifest) | set(manifest)
    flexible = {"roster", "corpus_sha256"} if version == "trigger-campaign-approval/v5" else set()
    for key in immutable - {"experiment_id", "output_directory", "identities", "arms"} - flexible:
        comparison._require(manifest.get(key) == logical_manifest.get(key),
                            f"historical segment changed immutable manifest field: {key}")
    logical_cases = {row["case_id"]: row for row in logical_manifest["roster"]}
    subset = (all(logical_cases.get(case_id) == case for case_id, case in cases.items())
              and [row["case_id"] for row in logical_manifest["roster"]
                   if row["case_id"] in cases] == list(cases))
    comparison._require((version == "trigger-campaign-approval/v5" and subset
                         or tuple(manifest["roster"]) == tuple(logical_manifest["roster"]))
                        and {key: manifest["identities"][key] for key in ("catalog", "fixture")}
                        == {key: logical_manifest["identities"][key] for key in ("catalog", "fixture")},
                        "historical segment roster or source identities drifted")
    nested = value["nested_carry_forward"]
    comparison._require(nested is None or isinstance(nested, dict),
                        "historical nested carry-forward is malformed")
    comparison._require(version in {"trigger-campaign-approval/v3",
                                    "trigger-campaign-approval/v4",
                                    "trigger-campaign-approval/v5"}
                        and (version == "trigger-campaign-approval/v3" and nested is None
                             or version == "trigger-campaign-approval/v4"
                             and nested is not None
                             and nested.get("schema_version") == SCHEMA_VERSION
                             or version == "trigger-campaign-approval/v5"
                             and nested is not None
                             and nested.get("schema_version") == MULTI_GENERATION_SCHEMA_VERSION),
                        "historical approval is relabeled or lacks its reviewed lineage")
    comparison._require(manifest.get("output_directory") == str(root),
                        "historical manifest does not bind its physical output root")
    from trigger_campaign import read_ledger_bytes, validate_approval
    validate_approval(approval, comparison.json_digest(manifest), approval.get("launch_budget"),
                      carry_forward=nested)
    try:
        authorization, ledger = read_ledger_bytes(raw_ledger)
    except (sqlite3.Error, TypeError, IndexError, KeyError,
            json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError(f"historical ledger bytes are unreadable: {exc}") from None
    expected_authorization = {
        "manifest_sha256": comparison.json_digest(manifest),
        "approval_sha256": comparison.json_digest(approval),
        "launch_budget": approval["launch_budget"],
    }
    if nested is not None:
        expected_authorization["carry_forward_sha256"] = comparison.json_digest(nested)
    comparison._require(authorization == expected_authorization and terminal == ledger,
                        "historical ledger authorization or terminal snapshot changed")
    comparison._require(ledger.get("schema_version") == "trigger-campaign-ledger/v1"
                        and ledger.get("launch_budget") == approval["launch_budget"]
                        and type(ledger.get("reserved_launches")) is int
                        and ledger["reserved_launches"] == len(ledger.get("launches", []))
                        and type(ledger.get("unknown_launches")) is int
                        and ledger["unknown_launches"]
                        == sum(row.get("status") == "unknown" for row in ledger["launches"]),
                        "historical terminal ledger accounting is malformed")
    seen: set[tuple[str, str, int]] = set()
    by_pair: dict[tuple[str, str], list[dict]] = {}
    invalid_identities: set[tuple[str, str, int]] = set()
    for row in ledger["launches"]:
        comparison._require(isinstance(row, dict)
                            and set(row) == {"arm", "case_id", "trial_number", "status",
                                            "reserved_at", "completed_at"}
                            and isinstance(row["arm"], str) and row["arm"].startswith("serial:")
                            and row["arm"].partition(":")[2] in logical_manifest["arms"]
                            and row["case_id"] in cases
                            and type(row["trial_number"]) is int and row["trial_number"] in {1, 2, 3}
                            and row["status"] in {"complete", "invalid", "unknown"}
                            and type(row["reserved_at"]) in {int, float}
                            and not isinstance(row["reserved_at"], bool)
                            and (row["completed_at"] is None
                                 if row["status"] == "unknown"
                                 else type(row["completed_at"]) in {int, float}
                                 and not isinstance(row["completed_at"], bool)
                                 and row["reserved_at"] <= row["completed_at"]),
                            "historical terminal ledger row is malformed")
        arm = row["arm"].partition(":")[2]
        identity = (arm, row["case_id"], row["trial_number"])
        comparison._require(identity not in seen, "historical ledger duplicates a charged identity")
        seen.add(identity)
        by_pair.setdefault(identity[:2], []).append(row)
        if row["status"] != "complete":
            invalid_identities.add(identity)
    complete_pairs = frozenset(pair for pair, rows in by_pair.items()
                               if len(rows) == 3
                               and {row["trial_number"] for row in rows} == {1, 2, 3}
                               and {row["status"] for row in rows} == {"complete"})
    complete_trials = frozenset((arm, case_id, trial) for arm, case_id in complete_pairs
                                for trial in (1, 2, 3))
    comparison._require(all(pair in complete_pairs or all(row["status"] != "complete" for row in rows)
                            for pair, rows in by_pair.items()),
                        "historical partial case mixes valid and invalid evidence")
    comparison._require(isinstance(value["evidence"], list)
                        and all(isinstance(item, dict) for item in value["evidence"]),
                        "historical evidence descriptors are malformed")
    lease_path = _validate_history_ownership(
        value["ownership"], root, by_pair, cases, check_lease=check_lease)
    _assert_sidecars_absent(root, value["ledger"])
    for name, retained in (("manifest", raw_manifest), ("approval", raw_approval),
                           ("ledger", raw_ledger), ("terminal_ledger", raw_terminal),
                           ("inventory", raw_inventory)):
        maximum = _MAX_LEDGER if name == "ledger" else _MAX_JSON
        comparison._require(
            read_external_file(root, value[name], f"historical {name.replace('_', ' ')}",
                               max_bytes=maximum) == retained,
            f"historical {name.replace('_', ' ')} changed during admission")
    return HistoricalSegmentPlan(
        generation_id, root, review_root, manifest, approval, ledger,
        value["ledger"]["sha256"],
        complete_pairs, complete_trials, frozenset(invalid_identities), len(seen),
        sum(row["status"] == "invalid" for row in ledger["launches"]),
        sum(row["status"] == "unknown" for row in ledger["launches"]),
        tuple(value["evidence"]), nested, lease_path,
    )


def _reference_fields(source: dict) -> None:
    output_names = {"manifest", "approval", "ledger", "interrupted_ledger", "terminal_cleanup",
                    "terminal_launch"}
    review_names = {"terminal_evidence", "terminal_review", "cohort", "partial_index",
                    "source_stability_review", "compatibility_review", "dual_replay"}
    expected = {"output_root", "review_root", "terminal_trial_records", *output_names, *review_names}
    comparison._require(isinstance(source, dict) and set(source) == expected,
                        "carry-forward source binding is malformed")
    for name in output_names | review_names:
        _normalized_reference(source[name], f"predecessor {name.replace('_', ' ')}")
    comparison._require(isinstance(source["terminal_trial_records"], list)
                        and len(source["terminal_trial_records"]) == 3,
                        "terminal trial-record references are malformed")
    for reference in source["terminal_trial_records"]:
        _normalized_reference(reference, "terminal trial record")


def _validate_terminal_ledger(snapshot: object, old_manifest: dict) -> tuple[tuple[str, ...], frozenset[tuple[str, str, int]]]:
    fields = {"schema_version", "launch_budget", "reserved_launches", "unknown_launches", "launches"}
    comparison._require(isinstance(snapshot, dict) and set(snapshot) == fields
                        and snapshot["schema_version"] == "trigger-campaign-ledger/v1"
                        and type(snapshot["launch_budget"]) is int and snapshot["launch_budget"] == 1302
                        and type(snapshot["reserved_launches"]) is int and snapshot["reserved_launches"] == 414
                        and type(snapshot["unknown_launches"]) is int and snapshot["unknown_launches"] == 0
                        and isinstance(snapshot["launches"], list) and len(snapshot["launches"]) == 414,
                        "terminal interrupted-ledger snapshot is malformed")
    expected_row_fields = {"arm", "case_id", "trial_number", "status", "reserved_at", "completed_at"}
    by_case: dict[tuple[str, str], list[dict]] = {}
    seen: set[tuple[str, str, int]] = set()
    for row in snapshot["launches"]:
        comparison._require(isinstance(row, dict) and set(row) == expected_row_fields
                            and row["arm"] == "serial:baseline"
                            and type(row["trial_number"]) is int and row["trial_number"] in {1, 2, 3}
                            and row["status"] in {"complete", "invalid"}
                            and type(row["reserved_at"]) in {int, float} and not isinstance(row["reserved_at"], bool)
                            and type(row["completed_at"]) in {int, float} and not isinstance(row["completed_at"], bool)
                            and row["reserved_at"] <= row["completed_at"],
                            "terminal interrupted-ledger row is malformed")
        identity = (row["arm"], row["case_id"], row["trial_number"])
        comparison._require(identity not in seen, "terminal interrupted-ledger contains a duplicate identity")
        seen.add(identity)
        by_case.setdefault((row["arm"], row["case_id"]), []).append(row)
    complete = {identity for identity, rows in by_case.items()
                if len(rows) == 3 and {row["trial_number"] for row in rows} == {1, 2, 3}
                and {row["status"] for row in rows} == {"complete"}}
    invalid = {identity for identity, rows in by_case.items()
               if {row["status"] for row in rows} == {"invalid"}}
    comparison._require(len(complete) == 137 and len(invalid) == 1
                        and invalid == {("serial:baseline", PARTIAL_CASE_ID)}
                        and sum(row["status"] == "complete" for row in snapshot["launches"]) == 411
                        and sum(row["status"] == "invalid" for row in snapshot["launches"]) == 3,
                        "terminal interrupted-ledger is not the reviewed 411-complete/3-invalid state")
    roster = [row["case_id"] for row in old_manifest["roster"]]
    complete_ids = {case_id for _arm, case_id in complete}
    ordered = tuple(case_id for case_id in roster if case_id in complete_ids)
    comparison._require(len(ordered) == 137 and set(ordered) == complete_ids,
                        "terminal complete cohort is not contained in the full predecessor roster")
    trials = frozenset(("baseline", case_id, trial) for case_id in ordered for trial in (1, 2, 3))
    return ordered, trials


def _partial_manifest(old_manifest: dict, carried_ids: tuple[str, ...]) -> dict:
    roster = [row for row in old_manifest["roster"] if row["case_id"] in set(carried_ids)]
    partial = {**old_manifest, "qualification_scope": "pr-core", "roster": roster,
               "corpus_sha256": comparison.json_digest(roster)}
    comparison._require(tuple(row["case_id"] for row in roster) == carried_ids
                        and comparison.json_digest(partial) == PARTIAL_EXPERIMENT_SHA256,
                        "deterministically derived predecessor partial experiment changed")
    return partial


def fresh_partial_manifest(manifest: dict, fresh_ids: tuple[str, ...]) -> dict:
    """Derive an admitted ordered submanifest from the approved full manifest."""
    allowed = set(fresh_ids)
    roster = [row for row in manifest["roster"] if row["case_id"] in allowed]
    comparison._require(tuple(row["case_id"] for row in roster) == fresh_ids,
                        "fresh baseline identities are not the ordered full-manifest complement")
    partial = {**manifest, "qualification_scope": "pr-core", "roster": roster,
               "corpus_sha256": comparison.json_digest(roster)}
    comparison.validate_experiment(partial)
    return partial


def _projection(record: dict) -> dict:
    return {
        "selected": record.get("selected"),
        "selected_skill": record.get("selected_skill"),
        "selected_skill_set": record.get("selected_skill_set"),
        "consulted_skills": record.get("consulted_skills"),
        "requested_model": record.get("requested_model"),
        "resolved_model": record.get("resolved_model"),
        "model_identity_check": record.get("model_identity_check"),
        "observation_scope": record.get("observation_scope"),
        "qualification_observed": record.get("qualification_observed"),
        "qualification_eligible": record.get("qualification_eligible"),
        "execution_checks": record.get("checks"),
        "cleanup": {
            "provider_exit_code": record.get("provider_exit_code"),
            "timed_out": record.get("timed_out"),
            "interrupted_by_signal": record.get("interrupted_by_signal"),
            "cleanup_verified": record.get("cleanup_verified"),
            "cleanup_error": record.get("cleanup_error"),
            "cleanup_scope": record.get("cleanup_scope"),
            "unexpected_descendants": record.get("unexpected_descendants"),
        },
    }


def _validate_closure(value: object, observer_sha256: str, *, current: bool) -> None:
    fields = {"observer_sha256", "source_commit", "root", "files", "loaded_files",
              "module_namespace", "import_isolation", "module_files"}
    comparison._require(isinstance(value, dict) and set(value) == fields
                        and value["observer_sha256"] == observer_sha256
                        and isinstance(value["source_commit"], str)
                        and re.fullmatch(r"[0-9a-f]{40}", value["source_commit"])
                        and isinstance(value["root"], str) and Path(value["root"]).is_absolute()
                        and value["root"] == str(Path(value["root"]).resolve())
                        and isinstance(value["files"], dict) and value["files"]
                        and all(isinstance(path, str) and path and _SHA256.fullmatch(digest or "")
                                for path, digest in value["files"].items())
                        and isinstance(value["loaded_files"], dict) and value["loaded_files"]
                        and set(value["loaded_files"]).issubset(value["files"])
                        and all(value["loaded_files"][path] == value["files"][path]
                                for path in value["loaded_files"])
                        and isinstance(value["module_namespace"], str) and value["module_namespace"]
                        and value["import_isolation"] is True
                        and isinstance(value["module_files"], dict) and value["module_files"]
                        and all(isinstance(name, str) and name.startswith(value["module_namespace"] + ":")
                                and isinstance(path, str) and Path(path).is_absolute()
                                and Path(path).is_relative_to(Path(value["root"]))
                                for name, path in value["module_files"].items())
                        and set(value["loaded_files"])
                        == {Path(path).relative_to(Path(value["root"]) / "tests/speckit-pro").as_posix()
                            for path in value["module_files"].values()}
                        and comparison.json_digest(value["files"]) == observer_sha256,
                        "dual-replay observer closure is malformed or not hermetic")
    if current:
        current_files = comparison.measurement_snapshot()["observer"]
        comparison._require(value["files"] == current_files,
                            "current dual-replay observer closure changed on disk")


def _validate_dual_replay(value: object, old_manifest: dict, new_manifest: dict,
                          carried_trials: frozenset[tuple[str, str, int]], records: dict,
                          live_current_observer: bool = True) -> dict[str, frozenset]:
    fields = {"schema_version", "source_index_sha256", "equality_projection",
              "original_closure", "current_closure", "trials"}
    comparison._require(isinstance(value, dict) and set(value) == fields
                        and value["schema_version"] == DUAL_REPLAY_SCHEMA_VERSION
                        and value["source_index_sha256"] == EXPECTED_RAW_SHA256["partial_index"]
                        and value["equality_projection"] == list(PROJECTION_FIELDS)
                        and isinstance(value["trials"], list) and len(value["trials"]) == 411,
                        "dual-replay artifact is malformed")
    _validate_closure(value["original_closure"], old_manifest["identities"]["observer"], current=False)
    _validate_closure(value["current_closure"], new_manifest["identities"]["observer"],
                      current=live_current_observer)
    comparison._require(value["original_closure"]["module_namespace"]
                        != value["current_closure"]["module_namespace"],
                        "old and current replay modules share a namespace")
    seen = set()
    models: dict[str, set] = {}
    for item in value["trials"]:
        item_fields = {"arm", "case_id", "trial_number", "record_sha256", "stdout_sha256",
                       "replay_context_sha256", "original", "current"}
        comparison._require(isinstance(item, dict) and set(item) == item_fields
                            and item["arm"] == "baseline" and type(item["trial_number"]) is int,
                            "dual-replay trial identity is malformed")
        identity = (item["arm"], item["case_id"], item["trial_number"])
        comparison._require(identity in carried_trials and identity not in seen,
                            "dual-replay trial set differs from the ledger-derived cohort")
        seen.add(identity)
        record_info = records[identity]
        comparison._require(item["record_sha256"] == record_info["record_sha256"]
                            and item["stdout_sha256"] == record_info["stdout_sha256"]
                            and item["replay_context_sha256"] == record_info["context_sha256"]
                            and type(item["original"]) is dict and type(item["current"]) is dict
                            and set(item["original"]) == set(PROJECTION_FIELDS)
                            and set(item["current"]) == set(PROJECTION_FIELDS)
                            and comparison.json_digest(item["original"]) == comparison.json_digest(item["current"])
                            and comparison.json_digest(item["original"]) == comparison.json_digest(record_info["projection"]),
                            "old/current typed replay projection disagrees with retained evidence")
        host = records[identity]["host"]
        models.setdefault(host, set()).add(item["current"]["resolved_model"])
    comparison._require(seen == carried_trials, "dual-replay artifact is not the exact 411-trial map")
    return {host: frozenset(values) for host, values in models.items()}


def _validate_evidence(source_root: Path, source_index: dict, partial_manifest: dict,
                       carried_ids: tuple[str, ...], carried_trials: frozenset[tuple[str, str, int]]) -> dict:
    comparison._require(source_index.get("schema_version") == "trigger-evidence-index/v1"
                        and source_index.get("experiment_sha256") == PARTIAL_EXPERIMENT_SHA256
                        and source_index.get("arm") == "baseline"
                        and source_index.get("pins") == partial_manifest["pins"]
                        and source_index.get("identities") == partial_manifest["identities"]
                        and source_index.get("complete") is True,
                        "predecessor partial evidence index bindings changed")
    index_ids = tuple(source_index.get("summary", {}))
    comparison._require(index_ids == carried_ids, "partial evidence summary order differs from ledger-derived cohort")
    trials = source_index.get("trials")
    cleanup = source_index.get("cleanup")
    comparison._require(isinstance(trials, list) and len(trials) == 411
                        and isinstance(cleanup, list) and len(cleanup) == 137,
                        "predecessor partial index cardinality changed")
    cache: dict[tuple[str, str], bytes] = {}

    def read(reference: dict, label: str, maximum: int = _MAX_STREAM) -> bytes:
        relative, digest = _normalized_reference(reference, label)
        key = (relative.as_posix(), digest)
        if key not in cache:
            cache[key] = read_external_file(source_root, reference, label, max_bytes=maximum)
        return cache[key]

    read(source_index["inventory"], "predecessor inventory", _MAX_JSON)
    read(source_index["controlled_description"], "predecessor controlled description", _MAX_STREAM)
    workspaces: dict[str, int] = {}
    for reference in cleanup:
        receipt = _json(read(reference, "predecessor cleanup receipt", _MAX_JSON), "predecessor cleanup receipt")
        comparison._require(receipt.get("schema_version") == "trigger-arm-cleanup/v1"
                            and receipt.get("workspace_removed") is True
                            and receipt.get("cleanup_error") is None
                            and type(receipt.get("runner_exit_code")) is int
                            and receipt["runner_exit_code"] in {0, 1}
                            and isinstance(receipt.get("workspace"), str)
                            and Path(receipt["workspace"]).is_absolute()
                            and receipt["workspace"] not in workspaces
                            and not Path(receipt["workspace"]).exists(),
                            "predecessor cleanup receipt or current workspace absence is invalid")
        workspaces[receipt["workspace"]] = receipt["runner_exit_code"]
    records = {}
    hits = dict.fromkeys(carried_ids, 0)
    seen = set()
    cases = {row["case_id"]: row for row in partial_manifest["roster"]}
    for item in trials:
        comparison._require(isinstance(item, dict)
                            and set(item) == {"case_id", "trial_number", "selected", "record", "stdout",
                                              "stderr", "report", "replay_context"}
                            and type(item["trial_number"]) is int and type(item["selected"]) is bool,
                            "predecessor partial index trial is malformed")
        identity = ("baseline", item["case_id"], item["trial_number"])
        comparison._require(identity in carried_trials and identity not in seen,
                            "predecessor partial index trial set changed")
        seen.add(identity)
        record_bytes = read(item["record"], "predecessor trial record", _MAX_JSON)
        stdout = read(item["stdout"], "predecessor stdout", _MAX_STREAM)
        read(item["stderr"], "predecessor stderr", _MAX_STREAM)
        report = _json(read(item["report"], "predecessor report", _MAX_JSON), "predecessor report")
        record = _json(record_bytes, "predecessor trial record")
        case = cases[item["case_id"]]
        comparison._require(all(type(record.get(key)) is type(case[key]) and record.get(key) == case[key]
                                for key in ("case_id", "host", "skill", "query", "should_trigger"))
                            and type(record.get("trial_number")) is int
                            and record["trial_number"] == item["trial_number"]
                            and record.get("valid") is True and record.get("trial_valid") is True
                            and record.get("qualification_eligible") is True
                            and record.get("qualification_observed") is True
                            and record.get("cleanup_verified") is True and record.get("cleanup_error") is None
                            and record.get("provider_exit_code") == 0
                            and record.get("timed_out") is False
                            and record.get("interrupted_by_signal") is None
                            and isinstance(record.get("checks"), dict) and all(record["checks"].values())
                            and item["selected"] is record.get("selected")
                            and record.get("stdout_sha256", record.get("jsonl_sha256"))
                            == hashlib.sha256(stdout).hexdigest()
                            and item["replay_context"] == report.get("metadata", {}).get("replay_context"),
                            "predecessor retained trial validity or typed record changed")
        report_results = [row for row in report.get("results", []) if row.get("case_id") == item["case_id"]]
        comparison._require(len(report_results) == 1
                            and all(row.get("case_id") in cases for row in report["results"]),
                            "predecessor report contains a duplicate or undeclared case")
        report_trials = [row for row in report_results[0].get("selection_evidence", [])
                         if type(row.get("trial_number")) is int
                         and row["trial_number"] == item["trial_number"]]
        comparison._require(len(report_trials) == 1
                            and report_trials[0].get("trial_record_sha256") == item["record"]["sha256"],
                            "predecessor report trial reference changed")
        embedded = {key: value for key, value in report_trials[0].items()
                    if key not in {"trial_record_path", "trial_record_sha256"}}
        summary = report.get("summary", {})
        passed = sum(row.get("pass") is True for row in report["results"])
        failed = sum(row.get("pass") is False for row in report["results"])
        workspace = item["replay_context"].get("plugin_root", item["replay_context"].get("workspace"))
        comparison._require(comparison.json_digest(embedded) == comparison.json_digest(record)
                            and summary.get("total") == len(report["results"])
                            and summary.get("passed") == passed and summary.get("failed") == failed
                            and summary.get("complete") is True and summary.get("not_run") == 0
                            and summary.get("qualification_eligible") is True
                            and workspace in workspaces
                            and workspaces[workspace] == (1 if failed else 0),
                            "predecessor report summary, embedded record, or cleanup binding changed")
        context_sha = comparison.json_digest(item["replay_context"])
        records[identity] = {"record_sha256": hashlib.sha256(record_bytes).hexdigest(),
                             "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
                             "context_sha256": context_sha, "projection": _projection(record),
                             "host": case["host"]}
        hits[item["case_id"]] += int(item["selected"])
    comparison._require(seen == carried_trials, "predecessor partial index is not the exact carried trial set")
    expected_summary = {case_id: {"target_hits": hits[case_id],
                        "pass": (hits[case_id] / 3 >= 0.5) == cases[case_id]["should_trigger"]}
                        for case_id in carried_ids}
    comparison._require(comparison.json_digest(source_index["summary"]) == comparison.json_digest(expected_summary)
                        and {case_id for case_id, result in expected_summary.items() if result["pass"] is False}
                        == BEHAVIOR_FAILURES,
                        "predecessor behavior summary changed or was pass-filtered")
    return records


def _validate_cohort_file(value: object, old_manifest: dict, source_index: dict,
                          carried_ids: tuple[str, ...]) -> None:
    comparison._require(isinstance(value, dict)
                        and value.get("schema_version") == "trigger-case-carry-forward-cohort/v1-draft"
                        and value.get("cohort", {}).get("case_count") == 137
                        and value.get("cohort", {}).get("trial_count") == 411
                        and value.get("cohort", {}).get("behavior_pass_cases") == 135
                        and value.get("cohort", {}).get("behavior_fail_cases") == 2
                        and tuple(value.get("cohort", {}).get("case_ids_in_original_roster_order", [])) == carried_ids
                        and value.get("remaining", {}).get("fresh_launch_ceiling") == 891
                        and value.get("source_observer_sha256") == OLD_OBSERVER_SHA256,
                        "frozen cohort file differs from the ledger-derived complete cohort")
    rows = value["cohort"].get("cases")
    comparison._require(isinstance(rows, list) and len(rows) == 137
                        and tuple(row.get("case_id") for row in rows) == carried_ids,
                        "frozen cohort case roster changed")
    manifest_cases = {row["case_id"]: row for row in old_manifest["roster"]}
    index_trials: dict[str, list[dict]] = {case_id: [] for case_id in carried_ids}
    for item in source_index["trials"]:
        if item.get("case_id") in index_trials:
            index_trials[item["case_id"]].append(item)
    for row in rows:
        case = manifest_cases[row["case_id"]]
        summary = source_index["summary"][row["case_id"]]
        trials = sorted(index_trials[row["case_id"]], key=lambda item: item["trial_number"])
        comparison._require(row.get("host") == case["host"] and row.get("skill") == case["skill"]
                            and row.get("should_trigger") is case["should_trigger"]
                            and row.get("query_sha256") == hashlib.sha256(case["query"].encode()).hexdigest()
                            and row.get("trial_numbers") == [1, 2, 3]
                            and row.get("target_hits") == summary["target_hits"]
                            and row.get("behavior_pass") is summary["pass"]
                            and len(trials) == 3
                            and row.get("trial_record_sha256") == [item["record"]["sha256"] for item in trials]
                            and row.get("stdout_sha256") == [item["stdout"]["sha256"] for item in trials]
                            and row.get("stderr_sha256") == [item["stderr"]["sha256"] for item in trials]
                            and row.get("report_sha256") == trials[0]["report"]["sha256"]
                            and len({item["report"]["sha256"] for item in trials}) == 1
                            and row.get("replay_context_sha256")
                            == comparison.json_digest(trials[0]["replay_context"])
                            and len({comparison.json_digest(item["replay_context"]) for item in trials}) == 1,
                            "frozen cohort metadata differs from retained manifest/evidence")


def _validate_terminal_snapshot(value: object, source_root: Path, ledger_snapshot: dict) -> None:
    comparison._require(isinstance(value, dict)
                        and value.get("schema_version") == "terminal-trigger-evidence-snapshot/v1"
                        and value.get("terminal_exit_code") == 2
                        and value.get("output_root") == str(source_root)
                        and value.get("ledger_sha256") == EXPECTED_RAW_SHA256["ledger"]
                        and isinstance(value.get("cases"), list) and len(value["cases"]) == 138,
                        "terminal campaign evidence snapshot changed")
    ledger_rows = {(row["arm"], row["case_id"], row["trial_number"]): row["status"]
                   for row in ledger_snapshot["launches"]}
    seen = set()
    for case in value["cases"]:
        comparison._require(isinstance(case, dict)
                            and set(case) == {"arm", "case_id", "root", "ledger_trials", "file_count",
                                               "files_manifest_sha256"}
                            and case["arm"] == "serial:baseline"
                            and Path(case["root"]).is_absolute()
                            and Path(case["root"]).is_relative_to(source_root)
                            and _SHA256.fullmatch(case["files_manifest_sha256"] or ""),
                            "terminal evidence case binding is malformed")
        identity = (case["arm"], case["case_id"])
        comparison._require(identity not in seen, "terminal evidence snapshot duplicates a case")
        seen.add(identity)
        for trial in case["ledger_trials"]:
            comparison._require(set(trial) == {"trial", "status"}
                                and ledger_rows.get((case["arm"], case["case_id"], trial["trial"])) == trial["status"],
                                "terminal evidence snapshot differs from interrupted ledger")
    comparison._require(len(seen) == 138, "terminal evidence snapshot omitted a reserved case")


def _case_tree_bytes(source_root: Path, case: dict) -> dict[str, bytes]:
    """Secure-read and verify every byte named by one signed case-tree digest."""
    case_root = Path(case["root"])
    try:
        before = sorted(case_root.rglob("*"))
        files = []
        prior = []
        for path in before:
            status = path.lstat()
            comparison._require(not stat.S_ISLNK(status.st_mode),
                                "terminal evidence case tree contains a symlink")
            comparison._require(stat.S_ISDIR(status.st_mode) or stat.S_ISREG(status.st_mode),
                                "terminal evidence case tree contains an unsupported entry")
            identity = (_file_identity(status) if stat.S_ISREG(status.st_mode)
                        else _directory_identity(status))
            prior.append((path.relative_to(case_root).as_posix(), identity))
            if stat.S_ISREG(status.st_mode):
                files.append(path)
    except OSError as exc:
        raise ValueError(f"terminal evidence case tree could not be enumerated: {exc}") from None
    comparison._require(len(files) == case["file_count"],
                        "terminal evidence case file count changed")
    payloads: dict[str, bytes] = {}
    rows = []
    for path in files:
        relative = PurePosixPath(path.relative_to(source_root).as_posix())
        case_relative = path.relative_to(case_root).as_posix()
        payload = _read_external_path(source_root, relative, "terminal ownership evidence",
                                      max_bytes=_MAX_JSON)
        payloads[case_relative] = payload
        rows.append({"path": case_relative, "bytes": len(payload),
                     "sha256": hashlib.sha256(payload).hexdigest()})
    try:
        after = []
        for path in sorted(case_root.rglob("*")):
            status = path.lstat()
            identity = (_file_identity(status) if stat.S_ISREG(status.st_mode)
                        else _directory_identity(status))
            after.append((path.relative_to(case_root).as_posix(), identity))
    except OSError as exc:
        raise ValueError(f"terminal evidence case tree could not be revalidated: {exc}") from None
    comparison._require(prior == after, "terminal evidence case tree changed while it was read")
    digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    comparison._require(digest == case["files_manifest_sha256"],
                        "terminal evidence case-tree digest changed")
    return payloads


def _workspace_is_absent(raw_path: object) -> bool:
    comparison._require(isinstance(raw_path, str) and Path(raw_path).is_absolute()
                        and str(Path(raw_path)) == raw_path,
                        "predecessor workspace path is malformed")
    try:
        os.lstat(raw_path)
    except FileNotFoundError:
        return True
    except OSError as exc:
        raise ValueError(f"predecessor workspace absence could not be inspected: {exc}") from None
    return False


def _current_process_snapshot(
    *, runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> tuple[dict, ...]:
    try:
        completed = runner(["ps", "-axo", "uid=,pid=,pgid=,lstart=,command="],
                           check=False, capture_output=True, text=True)
    except OSError as exc:
        raise ValueError(f"predecessor ownership process inspection failed: {exc}") from None
    comparison._require(completed.returncode == 0 and completed.stdout.strip(),
                        "predecessor ownership process inspection was inconclusive")
    pattern = re.compile(r"\s*(\d+)\s+(\d+)\s+(\d+)\s+"
                         r"([A-Z][a-z]{2}\s+[A-Z][a-z]{2}\s+\d+\s+\d\d:\d\d:\d\d\s+\d{4})\s+(.*)")
    rows = []
    for line in completed.stdout.splitlines():
        match = pattern.fullmatch(line)
        comparison._require(match is not None,
                            "predecessor ownership process inspection was malformed")
        try:
            started_at = datetime.strptime(match.group(4), "%a %b %d %H:%M:%S %Y").timestamp()
        except ValueError:
            raise ValueError("predecessor ownership process start identity was malformed") from None
        rows.append({"uid": int(match.group(1)), "pid": int(match.group(2)),
                     "pgid": int(match.group(3)), "started_at": started_at,
                     "command": match.group(5)})
    return tuple(rows)


def _ownership_is_absent(inventory: dict, processes: tuple[dict, ...]) -> bool:
    """Reject exact runners and historical groups, but permit later recycled IDs."""
    uid = os.getuid()
    for runner in inventory["runners"]:
        if any(row["uid"] == uid and row["pid"] == runner["pid"]
               and abs(row["started_at"] - runner["started_at"]) < 2
               and row["command"] == " ".join(runner["command"])
               for row in processes):
            return False
    for group in inventory["groups"]:
        if any(row["uid"] == uid and row["pgid"] == group["pgid"]
               and row["started_at"] <= group["completed_at"] + 2
               for row in processes):
            return False
    return True


def _validate_ownership_inventory(source_root: Path, terminal_evidence: dict,
                                  carried_ids: tuple[str, ...]) -> None:
    expected_ids = {*carried_ids, PARTIAL_CASE_ID}
    cases = {row["case_id"]: row for row in terminal_evidence["cases"]}
    comparison._require(set(cases) == expected_ids,
                        "terminal evidence ownership inventory has the wrong cases")
    inventory = {"runners": [], "groups": [], "workspaces": []}
    for case_id in (*carried_ids, PARTIAL_CASE_ID):
        case = cases[case_id]
        expected_root = source_root / "serial" / "baseline" / case_id
        comparison._require(case["root"] == str(expected_root),
                            "terminal evidence case root changed")
        payloads = _case_tree_bytes(source_root, case)
        launch = _json(payloads.get("launch.json", b""), "terminal case runner launch")
        execution = _json(payloads.get("execution.json", b""), "terminal case execution")
        cleanup = _json(payloads.get("evidence/arm-cleanup.json", b""), "terminal case cleanup")
        context = _json(payloads.get("evidence/replay-context.json", b""), "terminal replay context")
        trial_names = sorted(name for name in payloads if name.endswith(".trial.json"))
        trials = [_json(payloads[name], "terminal case trial record") for name in trial_names]
        comparison._require(set(launch) == {"pid", "command", "started_at"}
                            and type(launch["pid"]) is int and launch["pid"] > 0
                            and isinstance(launch["command"], list) and launch["command"]
                            and all(isinstance(part, str) and part for part in launch["command"])
                            and type(launch["started_at"]) is float,
                            "terminal runner ownership fingerprint is malformed")
        comparison._require(type(execution.get("finished_at")) is float
                            and type(execution.get("runner_exit_code")) is int,
                            "terminal runner completion fingerprint is malformed")
        comparison._require(cleanup.get("schema_version") == "trigger-arm-cleanup/v1"
                            and cleanup.get("workspace_removed") is True
                            and cleanup.get("cleanup_error") is None
                            and cleanup.get("workspace")
                            == context.get("plugin_root", context.get("workspace"))
                            and _workspace_is_absent(cleanup.get("workspace")),
                            "terminal case workspace is not absent under its cleanup receipt")
        comparison._require(len(trials) == 3
                            and [trial.get("trial_number") for trial in trials] == [1, 2, 3],
                            "terminal case trial ownership inventory is incomplete")
        inventory["runners"].append(launch)
        inventory["workspaces"].append(cleanup["workspace"])
        for trial in trials:
            pid, pgid = trial.get("child_pid"), trial.get("child_pgid")
            comparison._require(trial.get("case_id") == case_id
                                and type(pid) is int and pid > 0 and pid == pgid
                                and trial.get("cleanup_verified") is True
                                and trial.get("cleanup_error") is None
                                and trial.get("unexpected_descendants") is False
                                and isinstance(trial.get("cleanup_observations"), list)
                                and trial["cleanup_observations"]
                                and all(observation.get("pgid") == pgid
                                        and observation.get("errno") == 3
                                        for observation in trial["cleanup_observations"]),
                                "terminal child process-group ownership fingerprint is malformed")
            inventory["groups"].append({"pgid": pgid,
                                        "completed_at": execution["finished_at"]})
    comparison._require(len(inventory["runners"]) == 138
                        and len(inventory["groups"]) == 414
                        and len({row["pgid"] for row in inventory["groups"][:-3]}) == 410
                        and len(set(inventory["workspaces"])) == 138,
                        "terminal ownership inventory cardinality changed")
    comparison._require(_ownership_is_absent(inventory, _current_process_snapshot()),
                        "a predecessor-owned runner or child process group may still be live")


def _validate_terminal_cleanup(source_root: Path, source: dict, interrupted: dict) -> None:
    comparison._require([reference.get("sha256") for reference in source["terminal_trial_records"]]
                        == EXPECTED_TERMINAL_TRIAL_SHA256,
                        "terminal trial-record fingerprint changed")
    cleanup = _read_json(source_root, source["terminal_cleanup"], "terminal cleanup receipt")
    launch = _read_json(source_root, source["terminal_launch"], "terminal runner launch")
    trials = [_read_json(source_root, reference, "terminal trial record")
              for reference in source["terminal_trial_records"]]
    comparison._require(cleanup.get("schema_version") == "trigger-arm-cleanup/v1"
                        and cleanup.get("workspace_removed") is True
                        and cleanup.get("cleanup_error") is None
                        and cleanup.get("runner_exit_code") == 1
                        and isinstance(cleanup.get("workspace"), str)
                        and Path(cleanup["workspace"]).is_absolute(),
                        "terminal cleanup receipt changed")
    comparison._require(set(launch) == {"pid", "command", "started_at"}
                        and launch["pid"] == 15029 and isinstance(launch["command"], list)
                        and launch["command"] and type(launch["started_at"]) is float,
                        "terminal runner ownership fingerprint changed")
    expected_processes = [(15228, 15228), (15514, 15514), (15735, 15735)]
    for trial, (pid, pgid) in zip(trials, expected_processes, strict=True):
        comparison._require(trial.get("case_id") == PARTIAL_CASE_ID
                            and trial.get("child_pid") == pid and trial.get("child_pgid") == pgid
                            and trial.get("cleanup_verified") is True and trial.get("cleanup_error") is None
                            and trial.get("unexpected_descendants") is False
                            and isinstance(trial.get("cleanup_observations"), list)
                            and trial["cleanup_observations"]
                            and all(observation.get("pgid") == pgid and observation.get("errno") == 3
                                    for observation in trial["cleanup_observations"]),
            "terminal child process-group cleanup fingerprint changed")


def _validate_clean_boundary_lease(path: object, source_root: Path) -> Path:
    """Prove that the predecessor's stale lease is not held by a live owner."""
    import fcntl
    comparison._require(isinstance(path, str) and Path(path).is_absolute(),
                        "clean-boundary lease path is malformed")
    lease_path = _canonical_root(str(Path(path).parent), "clean-boundary lease") / Path(path).name
    comparison._require(str(lease_path) == path, "clean-boundary lease path is malformed")
    try:
        descriptor = os.open(lease_path, os.O_RDONLY | os.O_NOFOLLOW |
                             getattr(os, "O_CLOEXEC", 0))
    except OSError as exc:
        raise ValueError(f"clean-boundary lease could not be inspected: {exc}") from None
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        comparison._require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                            and not info.st_mode & (stat.S_IWGRP | stat.S_IWOTH),
                            "clean-boundary lease ownership or mode is unsafe")
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("clean-boundary predecessor lease is still active") from None
        value = _json(stream.read(), "clean-boundary lease")
    comparison._require(isinstance(value, dict)
                        and set(value) == {"schema_version", "state", "campaign"}
                        and value["schema_version"] == "trigger-global-lease/v1"
                        and value["state"] == "active"
                        and value["campaign"] == str(source_root),
                        "clean-boundary lease is not the stale predecessor lease")
    return lease_path


def _clean_boundary_ref(root: Path, path: Path, cache: dict[str, bytes], label: str) -> dict:
    """Read a predecessor artifact once and retain those exact bytes for replay."""
    comparison._require(path.is_absolute() and path.is_relative_to(root),
                        f"{label} escaped the clean-boundary root")
    relative = path.relative_to(root)
    payload = _read_external_path(root, relative, label, max_bytes=_MAX_STREAM)
    key = relative.as_posix()
    comparison._require(key not in cache, f"{label} was referenced more than once")
    cache[key] = payload
    return {"path": key, "sha256": hashlib.sha256(payload).hexdigest()}


def _clean_boundary_tree(root: Path, case_id: str) -> None:
    case_root = root / "serial" / "candidate" / case_id
    try:
        entries = list(os.walk(case_root, topdown=True, followlinks=False))
    except OSError as exc:
        raise ValueError(f"clean-boundary case tree could not be enumerated: {exc}") from None
    comparison._require(entries and not case_root.is_symlink(),
                        "clean-boundary case tree is missing")
    for directory, dirs, files in entries:
        for name in (*dirs, *files):
            path = Path(directory) / name
            value = os.lstat(path)
            comparison._require(not stat.S_ISLNK(value.st_mode)
                                and (stat.S_ISDIR(value.st_mode) or stat.S_ISREG(value.st_mode))
                                and value.st_uid == os.getuid()
                                and not value.st_mode & (stat.S_IWGRP | stat.S_IWOTH),
                                "clean-boundary case tree contains an unsafe entry")


def _clean_boundary_index(source_root: Path, source_manifest: dict,
                          carried_ids: tuple[str, ...]) -> tuple[dict, dict[str, bytes], dict]:
    """Construct an evidence index from one secure read of every source artifact."""
    cache: dict[str, bytes] = {}
    partial = {**source_manifest, "qualification_scope": "pr-core",
               "roster": [row for row in source_manifest["roster"]
                          if row["case_id"] in set(carried_ids)]}
    partial["corpus_sha256"] = comparison.json_digest(partial["roster"])
    trials: list[dict] = []
    cleanup: list[dict] = []
    summary: dict = {}
    for case_id in carried_ids:
        _clean_boundary_tree(source_root, case_id)
        case_root = source_root / "serial" / "candidate" / case_id
        _clean_boundary_ref(source_root, case_root / "launch.json", cache,
                            "clean-boundary runner launch")
        _clean_boundary_ref(source_root, case_root / "execution.json", cache,
                            "clean-boundary execution")
        _clean_boundary_ref(source_root, case_root / "evidence" / "replay-context.json",
                            cache, "clean-boundary replay context")
        report_path = case_root / "report.json"
        report_ref = _clean_boundary_ref(source_root, report_path, cache,
                                         "clean-boundary report")
        report = _json(cache[report_ref["path"]], "clean-boundary report")
        comparison._require(isinstance(report, dict)
                            and report.get("metadata", {}).get("replay_context")
                            and isinstance(report.get("results"), list)
                            and len(report["results"]) == 1
                            and report["results"][0].get("case_id") == case_id,
                            "clean-boundary report is incomplete")
        context = report["metadata"]["replay_context"]
        result = report["results"][0]
        summary[case_id] = {"target_hits": result.get("selected", result.get("triggers")),
                            "pass": result["pass"]}
        cleanup_ref = _clean_boundary_ref(
            source_root, case_root / "evidence" / "arm-cleanup.json", cache,
            "clean-boundary cleanup receipt")
        cleanup.append(cleanup_ref)
        for record in result.get("selection_evidence", []):
            trial_number = record["trial_number"]
            record_ref = _clean_boundary_ref(source_root, Path(record["trial_record_path"]),
                                             cache, "clean-boundary trial record")
            stdout_ref = _clean_boundary_ref(
                source_root, Path(record.get("stdout_path", record.get("jsonl_path"))),
                cache, "clean-boundary stdout")
            stderr_ref = _clean_boundary_ref(source_root, Path(record["stderr_path"]),
                                             cache, "clean-boundary stderr")
            trials.append({"case_id": case_id, "trial_number": trial_number,
                           "selected": record["selected"], "record": record_ref,
                           "stdout": stdout_ref, "stderr": stderr_ref,
                           "report": report_ref, "replay_context": context})
    inventory_ref = _clean_boundary_ref(source_root, source_root / "inventory.json", cache,
                                        "clean-boundary inventory")
    description_ref = _clean_boundary_ref(
        source_root, source_root / "candidate-description.txt", cache,
        "clean-boundary controlled description")
    index = {"schema_version": "trigger-evidence-index/v1",
             "experiment_id": partial["experiment_id"],
             "experiment_sha256": comparison.json_digest(partial), "arm": "candidate",
             "pins": partial["pins"], "identities": partial["identities"],
             "inventory": inventory_ref, "controlled_description": description_ref,
             "trials": trials, "cleanup": cleanup, "summary": summary,
             "complete": True}
    def reader(_root, reference):
        comparison._require(isinstance(reference, dict)
                            and reference.get("path") in cache
                            and hashlib.sha256(cache[reference["path"]]).hexdigest()
                            == reference.get("sha256"),
                            "clean-boundary replay requested an unbound artifact")
        return cache[reference["path"]]
    _hits, qualified = comparison._read_arm(
        partial, source_root, index, "candidate", comparison.validate_experiment(partial),
        {"artifact_reader": reader,
         "current_observer_sha256": partial["identities"]["observer"]})
    comparison._require(qualified, "clean-boundary evidence is not qualification eligible")
    return index, cache, {"runners": [], "groups": [], "workspaces": []}


def validate_clean_boundary_carry_forward(
    value: object, manifest: dict, manifest_digest: str, *, approval: dict | None = None,
    check_lease: bool = True,
) -> MultiGenerationPlan:
    """Admit a complete-case predecessor whose receipt was lost at a clean boundary."""
    standard = {"schema_version", "logical_manifest", "histories", "observer_replays",
                "accounting", "policy", "mode", "clean_boundary"}
    comparison._require(isinstance(value, dict) and set(value) == standard
                        and value["schema_version"] == MULTI_GENERATION_SCHEMA_VERSION
                        and value["mode"] == CLEAN_BOUNDARY_MODE,
                        "clean-boundary carry-forward request is malformed")
    request_cases = comparison.validate_experiment(manifest)
    logical = value["logical_manifest"]
    logical_cases = comparison.validate_experiment(logical)
    comparison._require(comparison.json_digest(manifest) == manifest_digest
                        and manifest["qualification_scope"] == "full"
                        and manifest["arms"] == ["candidate"]
                        and logical["arms"] == ["candidate"]
                        and logical["qualification_scope"] == "full"
                        and len(logical_cases) == 217,
                        "clean-boundary carry-forward requires a full candidate logical roster")
    for key in set(logical) | set(manifest):
        if key not in {"roster", "corpus_sha256", "output_directory", "draft_status",
                       "qualification_scope",
                       "launch_authorized", "launch_budget_requested", "experiment_id"}:
            comparison._require(logical.get(key) == manifest.get(key),
                                f"clean-boundary request changed immutable field: {key}")
    comparison._require(all(logical_cases.get(case_id) == case
                            for case_id, case in request_cases.items())
                        and [case_id for case_id in logical_cases if case_id in request_cases]
                        == list(request_cases),
                        "clean-boundary request roster is not an ordered logical subset")
    source = value["clean_boundary"]
    fields = {"output_root", "manifest", "approval", "ledger", "inventory",
              "description", "lineage", "lease_path"}
    comparison._require(isinstance(source, dict) and set(source) == fields,
                        "clean-boundary source binding is malformed")
    source_root = _canonical_root(source["output_root"], "clean-boundary output")
    fresh_root = _canonical_root(manifest["output_directory"], "fresh output")
    comparison._require(source_root != fresh_root and not source_root.is_relative_to(fresh_root)
                        and not fresh_root.is_relative_to(source_root),
                        "clean-boundary source and fresh roots must be disjoint")
    for name in ("manifest", "approval", "ledger", "inventory", "description", "lineage"):
        _normalized_reference(source[name], f"clean-boundary {name}")
    _assert_sidecars_absent(source_root, source["ledger"])
    raw_manifest = read_external_file(source_root, source["manifest"],
                                      "clean-boundary manifest", max_bytes=_MAX_JSON)
    raw_approval = read_external_file(source_root, source["approval"],
                                      "clean-boundary approval", max_bytes=_MAX_JSON)
    raw_ledger = read_external_file(source_root, source["ledger"],
                                    "clean-boundary ledger", max_bytes=_MAX_LEDGER)
    raw_lineage = read_external_file(source_root, source["lineage"],
                                     "clean-boundary lineage", max_bytes=_MAX_JSON)
    source_manifest = _json(raw_manifest, "clean-boundary manifest")
    source_approval = _json(raw_approval, "clean-boundary approval")
    source_lineage = _json(raw_lineage, "clean-boundary lineage")
    comparison.validate_experiment(source_manifest)
    comparison._require(source_manifest["arms"] == ["candidate"]
                        and source_manifest["qualification_scope"] == "full"
                        and len(source_manifest["roster"]) == 217
                        and source_manifest["output_directory"] == str(source_root)
                        and source_manifest["identities"] == logical["identities"],
                        "clean-boundary predecessor manifest changed")
    comparison._require(isinstance(value["histories"], list)
                        and value["histories"] == [{"generation_id": source_manifest["experiment_id"]}]
                        and value["observer_replays"] == [],
                        "clean-boundary history metadata is not the exact predecessor")
    comparison._require(source_approval.get("schema_version") == "trigger-campaign-approval/v5"
                        and source_approval.get("manifest_sha256")
                        == comparison.json_digest(source_manifest)
                        and source_approval.get("launch_budget") == 651,
                        "clean-boundary predecessor approval changed")
    comparison._require(source_lineage.get("schema_version") == "trigger-carry-forward-lineage/v2"
                        and source_lineage.get("manifest_sha256")
                        == source_approval.get("manifest_sha256")
                        and source_lineage.get("approval_sha256")
                        == comparison.json_digest(source_approval)
                        and source_lineage.get("carried_trials") == 651
                        and source_lineage.get("fresh_trials") == 651
                        and source_lineage.get("non_contiguous") is True
                        and source_lineage.get("timing_eligible") is False,
                        "clean-boundary predecessor lineage changed")
    try:
        authorization, ledger = __import__("trigger_campaign").read_ledger_bytes(raw_ledger)
    except (sqlite3.Error, TypeError, IndexError, KeyError,
            json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError(f"clean-boundary predecessor ledger is unreadable: {exc}") from None
    expected_authorization = {
        "manifest_sha256": comparison.json_digest(source_manifest),
        "approval_sha256": comparison.json_digest(source_approval), "launch_budget": 651,
        "carry_forward_sha256": source_approval["carry_forward_review"]["carry_forward_sha256"],
    }
    required_row_fields = {"arm", "case_id", "trial_number", "status", "reserved_at", "completed_at"}
    comparison._require(authorization == expected_authorization
                        and ledger["schema_version"] == "trigger-campaign-ledger/v1"
                        and ledger["launch_budget"] == 651
                        and ledger["reserved_launches"] == 315
                        and ledger["unknown_launches"] == 0
                        and len(ledger["launches"]) == 315
                        and all(isinstance(row, dict) and set(row) == required_row_fields
                                and row["arm"] == "serial:candidate"
                                and row["status"] == "complete"
                                and type(row["trial_number"]) is int
                                and row["trial_number"] in {1, 2, 3}
                                and type(row["reserved_at"]) in {int, float}
                                and type(row["completed_at"]) in {int, float}
                                and row["reserved_at"] <= row["completed_at"]
                                for row in ledger["launches"]),
                        "clean-boundary predecessor ledger is not a complete candidate prefix")
    by_case: dict[str, list[dict]] = {}
    seen: set[tuple[str, int]] = set()
    for row in ledger["launches"]:
        identity = (row["case_id"], row["trial_number"])
        comparison._require(identity not in seen and row["case_id"] in logical_cases
                            and type(row["trial_number"]) is int
                            and row["trial_number"] in {1, 2, 3},
                            "clean-boundary predecessor ledger identity is malformed")
        seen.add(identity)
        by_case.setdefault(row["case_id"], []).append(row)
    carried_ids = tuple(case_id for case_id in (row["case_id"] for row in source_manifest["roster"])
                        if case_id in by_case)
    comparison._require(len(carried_ids) == 105
                        and all(len(rows) == 3 and {r["trial_number"] for r in rows} == {1, 2, 3}
                                for rows in by_case.values()),
                        "clean-boundary predecessor ledger does not end at a case boundary")
    comparison._require(all(source_manifest["roster"]
                            [next(i for i, item in enumerate(source_manifest["roster"])
                                  if item["case_id"] == case_id)]["host"] == "claude"
                        for case_id in carried_ids)
                        and all(source_manifest["roster"]
                                [next(i for i, item in enumerate(source_manifest["roster"])
                                      if item["case_id"] == case_id)]["host"] == "codex"
                                for case_id in logical_cases if case_id not in set(carried_ids)),
                        "clean-boundary carried or fresh host roster changed")
    candidate_root = source_root / "serial" / "candidate"
    try:
        candidate_entries = {entry.name: entry for entry in candidate_root.iterdir()}
    except OSError as exc:
        raise ValueError(f"clean-boundary candidate tree could not be enumerated: {exc}") from None
    comparison._require(set(candidate_entries) == set(carried_ids)
                        and all(entry.is_dir() and not entry.is_symlink()
                                for entry in candidate_entries.values()),
                        "clean-boundary candidate tree differs from the ledger-derived cases")
    index, cache, _ownership = _clean_boundary_index(source_root, source_manifest, carried_ids)
    lease_path = _validate_clean_boundary_lease(source["lease_path"], source_root) if check_lease else Path(source["lease_path"])
    processes = _current_process_snapshot()
    runners, groups, workspaces = [], [], []
    for case_id in carried_ids:
        launch = _json(cache[f"serial/candidate/{case_id}/launch.json"],
                       "clean-boundary runner launch")
        execution = _json(cache[f"serial/candidate/{case_id}/execution.json"],
                          "clean-boundary execution")
        cleanup = _json(cache[f"serial/candidate/{case_id}/evidence/arm-cleanup.json"],
                        "clean-boundary cleanup")
        comparison._require(type(launch.get("pid")) is int and launch["pid"] > 0
                            and isinstance(launch.get("command"), list)
                            and type(launch.get("started_at")) is float
                            and type(execution.get("finished_at")) is float
                            and cleanup.get("workspace_removed") is True
                            and cleanup.get("cleanup_error") is None,
                            "clean-boundary ownership evidence is malformed")
        runners.append(launch)
        workspaces.append(cleanup["workspace"])
        for row in by_case[case_id]:
            indexed_trial = next(item for item in index["trials"]
                                 if item["case_id"] == case_id
                                 and item["trial_number"] == row["trial_number"])
            trial = _json(cache[indexed_trial["record"]["path"]],
                          "clean-boundary trial ownership")
            groups.append({"pgid": trial["child_pgid"], "completed_at": execution["finished_at"]})
    comparison._require(_ownership_is_absent({"runners": runners, "groups": groups}, processes),
                        "clean-boundary predecessor ownership is still live")
    comparison._require(index["complete"] is True,
                        "clean-boundary predecessor evidence is incomplete")
    carried = frozenset(("candidate", case_id) for case_id in carried_ids)
    carried_trials = frozenset(("candidate", case_id, trial)
                               for case_id in carried_ids for trial in (1, 2, 3))
    fresh = frozenset(("candidate", case_id) for case_id in logical_cases
                      if case_id not in set(carried_ids))
    fresh_trials = frozenset((arm, case_id, trial) for arm, case_id in fresh for trial in (1, 2, 3))
    comparison._require(frozenset(("candidate", case_id, trial)
                                  for case_id in request_cases for trial in (1, 2, 3)) == fresh_trials
                        and len(fresh_trials) == 336,
                        "clean-boundary request is not the exact remaining Codex schedule")
    accounting = {"logical_full_trials": 651, "carried_trials": 315,
                  "fresh_launch_ceiling": 336, "historical_charged_launches": 315,
                  "invalid_launches": 0, "unknown_launches": 0,
                  "maximum_total_charged_attempts": 651}
    comparison._require(value["accounting"] == accounting
                        and value["policy"] == {"automatic_retries": 0, "refunds": False,
                                                 "regrades": False, "resets": False,
                                                 "new_generation_invalid_reruns": True},
                        "clean-boundary accounting or retry policy changed")
    if approval is not None:
        comparison._require(approval.get("schema_version") == "trigger-campaign-approval/v5"
                            and approval.get("carry_forward_review", {}).get("carry_forward_sha256")
                            == comparison.json_digest(value),
                            "clean-boundary review does not bind the exact component")
    models = {host: frozenset({logical["pins"][host]["model"]}) for host in ("claude", "codex")}
    history = SimpleNamespace(generation_id=source_manifest["experiment_id"],
                              root=source_root, review_root=source_root.parent,
                              lease_path=lease_path)
    source_evidence = HistoricalEvidenceSource(
        history.generation_id, source_root, "candidate", source_manifest, index,
        carried_ids, models)
    return MultiGenerationPlan(value, comparison.json_digest(value), logical, (history,),
                               (source_evidence,), carried, carried_trials, fresh, fresh_trials,
                               models, len(fresh_trials), 315, 651)


def _validate_compatibility(value: object, old_manifest: dict, new_manifest: dict,
                            dual_replay: dict) -> None:
    fields = {"schema_version", "decision", "old_observer_sha256", "new_observer_sha256",
              "changed_files", "parser_change", "bookkeeping_paths", "timing_eligible",
              "concurrency_eligible"}
    old_files = dual_replay["original_closure"]["files"]
    new_files = dual_replay["current_closure"]["files"]
    changed_files = {path: {"old_sha256": old_files.get(path), "new_sha256": new_files.get(path)}
                     for path in sorted(set(old_files) | set(new_files))
                     if old_files.get(path) != new_files.get(path)}
    bookkeeping_paths = [
        "layer2-trigger/generate-carry-forward-replay.py",
        "layer2-trigger/run-trigger-campaign.py",
        "lib/trigger_campaign.py",
        "lib/trigger_campaign_execution.py",
        "lib/trigger_carry_forward.py",
        "lib/trigger_comparison.py",
    ]
    comparison._require(isinstance(value, dict) and set(value) == fields
                        and value["schema_version"] == COMPATIBILITY_SCHEMA_VERSION
                        and value["decision"] == "unchanged-evidence-compatible"
                        and value["old_observer_sha256"] == old_manifest["identities"]["observer"]
                        and value["new_observer_sha256"] == new_manifest["identities"]["observer"]
                        and value["changed_files"] == changed_files
                        and sorted(changed_files) == sorted([
                            "layer2-trigger/run_codex_evals.py", *bookkeeping_paths])
                        and value["parser_change"]
                        == "sed -n '1,<N>p' <matched-skill>/SKILL.md"
                        and value["bookkeeping_paths"] == bookkeeping_paths
                        and value["timing_eligible"] is False
                        and value["concurrency_eligible"] is False,
                        "carry-forward compatibility is not the reviewed narrow parser transition")


def validate_carry_forward(value: object, manifest: dict, manifest_digest: str,
                           *, approval: dict | None = None,
                           live_current_observer: bool = True) -> CarryForwardPlan:
    """Validate exact immutable lineage and return only ledger-derived identities."""
    fields = {"schema_version", "source", "cohort", "compatibility", "accounting"}
    comparison._require(isinstance(value, dict) and set(value) == fields
                        and value["schema_version"] == SCHEMA_VERSION,
                        "carry-forward request is malformed or unsupported")
    comparison.validate_experiment(manifest)
    comparison._require(comparison.json_digest(manifest) == manifest_digest
                        and manifest["qualification_scope"] == "full"
                        and manifest["arms"] == ["baseline", "candidate"]
                        and manifest["trials"] == 3 and len(manifest["roster"]) == 217,
                        "carry-forward requires the exact full dual-arm experiment")
    source = value["source"]
    _reference_fields(source)
    source_root = _canonical_root(source["output_root"], "predecessor output")
    review_root = _canonical_root(source["review_root"], "predecessor review")
    comparison._require(source_root != review_root
                        and Path(manifest["output_directory"]) != source_root
                        and Path(manifest["output_directory"]) != review_root,
                        "carry-forward requires distinct old, review, and new roots")
    for name, expected in EXPECTED_RAW_SHA256.items():
        if name in source:
            comparison._require(source[name]["sha256"] == expected,
                                f"predecessor {name.replace('_', ' ')} is not the reviewed retained input")
    _assert_sidecars_absent(source_root, source["ledger"])
    raw_manifest = read_external_file(source_root, source["manifest"], "predecessor manifest", max_bytes=_MAX_JSON)
    raw_approval = read_external_file(source_root, source["approval"], "predecessor approval", max_bytes=_MAX_JSON)
    read_external_file(source_root, source["ledger"], "predecessor ledger bytes", max_bytes=_MAX_LEDGER)
    interrupted = _read_json(source_root, source["interrupted_ledger"], "terminal interrupted ledger")
    terminal_evidence = _read_json(review_root, source["terminal_evidence"], "terminal evidence snapshot")
    read_external_file(review_root, source["terminal_review"], "terminal campaign review", max_bytes=_MAX_JSON)
    cohort_file = _read_json(review_root, source["cohort"], "frozen carry-forward cohort")
    source_index = _read_json(review_root, source["partial_index"], "frozen partial evidence index")
    read_external_file(review_root, source["source_stability_review"], "source stability review", max_bytes=_MAX_JSON)
    read_external_file(review_root, source["compatibility_review"], "compatibility review", max_bytes=_MAX_JSON)
    dual_replay = _read_json(review_root, source["dual_replay"], "immutable dual replay")
    _validate_terminal_cleanup(source_root, source, interrupted)
    _assert_sidecars_absent(source_root, source["ledger"])
    old_manifest = _json(raw_manifest, "predecessor manifest")
    old_approval = _json(raw_approval, "predecessor approval")
    comparison.validate_experiment(old_manifest)
    from trigger_campaign import validate_approval
    validate_approval(old_approval, comparison.json_digest(old_manifest), 1302)
    comparison._require(old_manifest["qualification_scope"] == "full"
                        and old_manifest["arms"] == ["baseline", "candidate"]
                        and old_manifest["trials"] == 3 and len(old_manifest["roster"]) == 217
                        and old_manifest["output_directory"] == str(source_root)
                        and old_manifest["identities"]["observer"] == OLD_OBSERVER_SHA256,
                        "predecessor manifest is not the reviewed full campaign")
    immutable_keys = set(old_manifest) | set(manifest)
    for key in immutable_keys - {"experiment_id", "output_directory", "identities"}:
        comparison._require(old_manifest.get(key) == manifest.get(key),
                            f"carry-forward changed immutable manifest field: {key}")
    comparison._require(tuple(old_manifest["roster"]) == tuple(manifest["roster"])
                        and {key: old_manifest["identities"][key] for key in ("catalog", "fixture")}
                        == {key: manifest["identities"][key] for key in ("catalog", "fixture")}
                        and (not live_current_observer
                             or manifest["identities"]
                             == comparison.snapshot_identities(comparison.measurement_snapshot())),
                        "new manifest roster or current source identities changed")
    carried_ids, carried_trials = _validate_terminal_ledger(interrupted, old_manifest)
    partial_manifest = _partial_manifest(old_manifest, carried_ids)
    _validate_terminal_snapshot(terminal_evidence, source_root, interrupted)
    _validate_cohort_file(cohort_file, old_manifest, source_index, carried_ids)
    records = _validate_evidence(source_root, source_index, partial_manifest, carried_ids, carried_trials)
    _validate_ownership_inventory(source_root, terminal_evidence, carried_ids)
    carried_models = _validate_dual_replay(
        dual_replay, old_manifest, manifest, carried_trials, records,
        live_current_observer=live_current_observer)
    _validate_compatibility(value["compatibility"], old_manifest, manifest, dual_replay)
    cohort = value["cohort"]
    comparison._require(isinstance(cohort, dict)
                        and set(cohort) == {"arm", "case_ids", "case_count", "trial_count"}
                        and cohort["arm"] == "baseline"
                        and cohort["case_ids"] == list(carried_ids)
                        and type(cohort["case_count"]) is int and cohort["case_count"] == 137
                        and type(cohort["trial_count"]) is int and cohort["trial_count"] == 411,
                        "caller cohort differs from the exact ledger-derived cohort")
    comparison._require(value["accounting"] == EXPECTED_ACCOUNTING
                        and all(type(value["accounting"][key]) is int for key in EXPECTED_ACCOUNTING),
                        "carry-forward accounting differs from exact reviewed arithmetic")
    if approval is not None:
        comparison._require(approval.get("carry_forward_review", {}).get("carry_forward_sha256")
                            == comparison.json_digest(value),
                            "V4 review does not bind the exact carry-forward component")
    all_cases = tuple(row["case_id"] for row in manifest["roster"])
    fresh_ids = tuple(case_id for case_id in all_cases if case_id not in set(carried_ids))
    carried = frozenset(("baseline", case_id) for case_id in carried_ids)
    fresh = frozenset({*(('baseline', case_id) for case_id in fresh_ids),
                       *(('candidate', case_id) for case_id in all_cases)})
    fresh_trials = frozenset((arm, case_id, trial) for arm, case_id in fresh for trial in (1, 2, 3))
    comparison._require(len(fresh_ids) == 80 and len(fresh) == 297 and len(fresh_trials) == 891
                        and carried_trials.isdisjoint(fresh_trials)
                        and carried_trials | fresh_trials
                        == frozenset((arm, case_id, trial) for arm in manifest["arms"]
                                     for case_id in all_cases for trial in (1, 2, 3)),
                        "ledger-derived carried and fresh identities do not form the exact 1302-trial union")
    return CarryForwardPlan(value, comparison.json_digest(value), source_root, review_root, old_manifest,
                            partial_manifest, source_index, carried, carried_trials, fresh, fresh_trials,
                            carried_ids, fresh_ids, carried_models)


def _validate_historical_evidence(
    segment: HistoricalSegmentPlan,
    logical_manifest: dict,
    legacy_plans: dict[str, CarryForwardPlan],
    multi_plans: dict[str, MultiGenerationPlan] | None = None,
) -> tuple[HistoricalEvidenceSource, ...]:
    """Replay exactly the all-valid pairs named by one reviewed physical segment."""
    sources: list[HistoricalEvidenceSource] = []
    covered: set[tuple[str, str]] = set()
    for descriptor in segment.evidence:
        kind = descriptor.get("kind")
        if kind == "legacy-anchor":
            comparison._require(set(descriptor) == {"kind", "carry_forward_sha256"}
                                and descriptor["carry_forward_sha256"] in legacy_plans,
                                "historical legacy evidence lacks a reviewed V1 anchor")
            plan = legacy_plans[descriptor["carry_forward_sha256"]]
            case_ids = plan.carried_case_ids
            source = HistoricalEvidenceSource(
                segment.generation_id, plan.source_root, "baseline", plan.partial_manifest,
                plan.source_index, case_ids, plan.carried_models)
        else:
            fields = {"kind", "arm", "index", "case_ids"}
            comparison._require(set(descriptor) == fields
                                and kind in {"direct", "reviewed-partial",
                                             "source-aware-fresh", "multi-source-fresh"}
                                and descriptor["arm"] in logical_manifest["arms"]
                                and isinstance(descriptor["case_ids"], list)
                                and descriptor["case_ids"]
                                and len(descriptor["case_ids"]) == len(set(descriptor["case_ids"])),
                                "historical evidence descriptor is malformed")
            _normalized_reference(descriptor["index"], "historical evidence index")
            case_ids = tuple(descriptor["case_ids"])
            index_root = segment.review_root if kind == "reviewed-partial" else segment.root
            raw_index = read_external_file(
                index_root, descriptor["index"], "historical evidence index", max_bytes=_MAX_JSON)
            top = _json(raw_index, "historical evidence index")
            if kind == "reviewed-partial":
                expected_ids = tuple(row["case_id"] for row in segment.manifest["roster"]
                                     if (descriptor["arm"], row["case_id"])
                                     in segment.complete_pairs)
                comparison._require(case_ids == expected_ids,
                                    "reviewed partial index case order differs from terminal ledger")
            if kind == "source-aware-fresh":
                carried, fresh = source_aware_union(top, segment.manifest, descriptor["arm"])
                nested_digest = comparison.json_digest(segment.nested_carry_forward)
                anchor = legacy_plans.get(nested_digest)
                comparison._require(top.get("carry_forward") == segment.nested_carry_forward
                                    and anchor is not None
                                    and carried["root"] == str(anchor.source_root)
                                    and carried["manifest"] == anchor.partial_manifest
                                    and carried["index"] == anchor.source_index
                                    and carried["case_ids"] == list(anchor.carried_case_ids)
                                    and fresh["root"] is None
                                    and fresh["case_ids"] == list(case_ids),
                                    "historical source-aware fresh evidence changed")
                source_manifest, index = fresh["manifest"], fresh["index"]
            elif kind == "multi-source-fresh":
                nested_digest = comparison.json_digest(segment.nested_carry_forward)
                nested_plan = (multi_plans or {}).get(nested_digest)
                comparison._require(nested_plan is not None
                                    and top.get("carry_forward") == segment.nested_carry_forward,
                                    "historical multi-source evidence lacks its reviewed V2 lineage")
                _historical, fresh = multi_source_union(top, nested_plan, descriptor["arm"])
                comparison._require(fresh is not None and fresh["root"] is None
                                    and fresh["case_ids"] == list(case_ids),
                                    "historical multi-source fresh evidence changed")
                source_manifest, index = fresh["manifest"], fresh["index"]
            else:
                source_manifest = fresh_partial_manifest(segment.manifest, case_ids)
                index = top
            cases = comparison.validate_experiment(source_manifest)
            comparison._require(set(cases) == set(case_ids),
                                "historical evidence source coverage drifted")
            artifact_reader = ((lambda _root, reference: read_external_file(
                segment.root, reference, "historical nested evidence", max_bytes=_MAX_JSON))
                               if kind == "reviewed-partial" else comparison.read_artifact)
            _hits, qualified = comparison._read_arm(
                source_manifest, segment.root, index, descriptor["arm"], cases,
                {"artifact_reader": artifact_reader,
                 "current_observer_sha256": logical_manifest["identities"]["observer"]})
            comparison._require(qualified, "historical carried evidence is not qualification eligible")
            models = {host: frozenset(values)
                      for host, values in comparison._resolved_models(
                          segment.root, index, artifact_reader).items()}
            comparison._require(read_external_file(
                index_root, descriptor["index"], "historical evidence index",
                max_bytes=_MAX_JSON) == raw_index,
                "historical evidence index changed during replay")
            source = HistoricalEvidenceSource(
                segment.generation_id, segment.root, descriptor["arm"], source_manifest,
                index, case_ids, models)
        identities = {(source.arm, case_id) for case_id in source.case_ids}
        comparison._require(not covered.intersection(identities),
                            "historical evidence descriptors overlap")
        covered.update(identities)
        sources.append(source)
    comparison._require(covered == set(segment.complete_pairs),
                        "historical evidence omits or carries a non-complete case-arm pair")
    return tuple(sources)


def _validate_observer_replay(
    value: object, source: HistoricalEvidenceSource, current_observer: str,
) -> None:
    """Replay one historical source through the final observer and bind both projections."""
    import trigger_evidence as evidence
    fields = {"schema_version", "source_index_sha256", "equality_projection",
              "original_closure", "current_closure", "trials"}
    comparison._require(isinstance(value, dict) and set(value) == fields
                        and value["schema_version"] == OBSERVER_REPLAY_SCHEMA_VERSION
                        and value["source_index_sha256"] == comparison.json_digest(source.index)
                        and value["equality_projection"] == list(PROJECTION_FIELDS)
                        and isinstance(value["trials"], list),
                        "multi-generation observer replay artifact is malformed")
    observer = source.manifest["identities"]["observer"]
    _validate_closure(value["original_closure"], observer, current=False)
    _validate_closure(value["current_closure"], current_observer, current=True)
    comparison._require(current_observer == comparison._LOADED_OBSERVER_DIGEST,
                        "final observer parser was not loaded from the reviewed source bytes")
    comparison._require(value["original_closure"]["module_namespace"]
                        != value["current_closure"]["module_namespace"],
                        "observer replay closures share a module namespace")
    index_trials = source.index.get("trials")
    comparison._require(isinstance(index_trials, list),
                        "observer replay source index lacks exact trials")
    expected = {(source.arm, case_id, trial) for case_id in source.case_ids
                for trial in (1, 2, 3)}
    by_identity = {(source.arm, item.get("case_id"), item.get("trial_number")): item
                   for item in index_trials if isinstance(item, dict)}
    comparison._require(set(by_identity) == expected and len(by_identity) == len(index_trials),
                        "observer replay source index trial identities changed")
    seen = set()
    trial_fields = {"arm", "case_id", "trial_number", "record_sha256", "stdout_sha256",
                    "replay_context_sha256", "original", "current"}
    for item in value["trials"]:
        comparison._require(isinstance(item, dict) and set(item) == trial_fields
                            and type(item["trial_number"]) is int,
                            "observer replay trial identity is malformed")
        identity = (item["arm"], item["case_id"], item["trial_number"])
        comparison._require(identity in expected and identity not in seen,
                            "observer replay trial set differs from its historical source")
        seen.add(identity)
        indexed = by_identity[identity]
        record_bytes = read_external_file(
            source.root, indexed["record"], "observer replay record", max_bytes=_MAX_JSON)
        stdout_bytes = read_external_file(
            source.root, indexed["stdout"], "observer replay stdout", max_bytes=_MAX_STREAM)
        record = _json(record_bytes, "observer replay record")
        try:
            parsed = comparison.replay(stdout_bytes, indexed["replay_context"])
            checks = evidence.trial_checks({**record, **parsed, "stream_valid": parsed["valid"]})
        except (ValueError, TypeError, KeyError, OSError, UnicodeError) as exc:
            raise ValueError(f"final observer rejected historical stdout: {exc}") from None
        original_projection = _projection(record)
        current_projection = _projection({**record, **parsed, "checks": checks})
        comparison._require(
            item["record_sha256"] == hashlib.sha256(record_bytes).hexdigest()
            and item["record_sha256"] == indexed["record"]["sha256"]
            and item["stdout_sha256"] == hashlib.sha256(stdout_bytes).hexdigest()
            and item["stdout_sha256"] == indexed["stdout"]["sha256"]
            and item["replay_context_sha256"]
            == comparison.json_digest(indexed["replay_context"])
            and parsed.get("valid") is True and all(checks.values())
            and type(item["original"]) is dict and type(item["current"]) is dict
            and set(item["original"]) == set(PROJECTION_FIELDS)
            and set(item["current"]) == set(PROJECTION_FIELDS)
            and item["original"] == original_projection
            and item["current"] == current_projection
            and item["original"] == item["current"],
            "historical/final typed replay projection disagrees with retained evidence")
    comparison._require(seen == expected,
                        "observer replay artifact is not the exact historical trial map")


def _validate_observer_replays(
    value: object, logical_manifest: dict, sources: tuple[HistoricalEvidenceSource, ...],
    histories: tuple[HistoricalSegmentPlan, ...], allowed_observers: set[str],
) -> None:
    comparison._require(isinstance(value, list) and value,
                        "multi-generation observer replay inventory is missing")
    expected_current = logical_manifest["identities"]["observer"]
    source_lookup = {(source.generation_id, source.arm): source for source in sources}
    history_lookup = {segment.generation_id: segment for segment in histories}
    seen: set[tuple[str, str]] = set()
    fields = {"generation_id", "arm", "observer_sha256", "current_observer_sha256",
              "replay"}
    for item in value:
        identity = (item.get("generation_id"), item.get("arm")) if isinstance(item, dict) else (None, None)
        source = source_lookup.get(identity)
        comparison._require(isinstance(item, dict) and set(item) == fields
                            and source is not None and identity not in seen
                            and item["observer_sha256"]
                            == source.manifest["identities"]["observer"]
                            and item["observer_sha256"] in allowed_observers
                            and item["current_observer_sha256"] == expected_current,
                            "multi-generation observer replay binding is malformed or unreviewed")
        if item["observer_sha256"] == expected_current:
            comparison._require(item["replay"] is None,
                                "current observer cannot be relabeled through a historical replay")
        else:
            _normalized_reference(item["replay"], "observer replay artifact")
            review_root = history_lookup[item["generation_id"]].review_root
            raw_replay = read_external_file(
                review_root, item["replay"], "observer replay artifact", max_bytes=_MAX_JSON)
            _validate_observer_replay(
                _json(raw_replay, "observer replay artifact"), source, expected_current)
            comparison._require(read_external_file(
                review_root, item["replay"], "observer replay artifact",
                max_bytes=_MAX_JSON) == raw_replay,
                "observer replay artifact changed during admission")
        seen.add(identity)
    comparison._require(seen == set(source_lookup),
                        "observer replay inventory differs from contributing evidence sources")


def validate_multi_generation_carry_forward(
    value: object, manifest: dict, manifest_digest: str, *, approval: dict | None = None,
    check_historical_lease: bool = True,
) -> MultiGenerationPlan:
    """Validate a reviewed flat set of terminal histories and its exact fresh complement."""
    if isinstance(value, dict) and value.get("mode") == CLEAN_BOUNDARY_MODE:
        return validate_clean_boundary_carry_forward(
            value, manifest, manifest_digest, approval=approval,
            check_lease=check_historical_lease)
    fields = {"schema_version", "logical_manifest", "histories", "observer_replays",
              "accounting", "policy"}
    comparison._require(isinstance(value, dict) and set(value) == fields
                        and value["schema_version"] == MULTI_GENERATION_SCHEMA_VERSION,
                        "multi-generation carry-forward request is malformed or unsupported")
    request_cases = comparison.validate_experiment(manifest)
    logical = value["logical_manifest"]
    logical_cases = comparison.validate_experiment(logical)
    comparison._require(comparison.json_digest(manifest) == manifest_digest
                        and logical["qualification_scope"] == manifest["qualification_scope"] == "full"
                        and logical["arms"] == ["baseline", "candidate"]
                        and len(logical_cases) == 217 and manifest["arms"] in (["candidate"],
                                                                               ["baseline", "candidate"]),
                        "multi-generation carry-forward requires a full logical dual-arm experiment")
    for key in set(logical) | set(manifest):
        if key not in {"arms", "roster", "corpus_sha256"}:
            comparison._require(logical.get(key) == manifest.get(key),
                                f"fresh request changed logical manifest field: {key}")
    comparison._require(all(logical_cases.get(case_id) == case
                            for case_id, case in request_cases.items())
                        and [case_id for case_id in logical_cases if case_id in request_cases]
                        == list(request_cases),
                        "fresh request roster is not an ordered subset of the full logical manifest")
    current_identities = comparison.snapshot_identities(comparison.measurement_snapshot())
    comparison._require(logical["identities"] == current_identities,
                        "multi-generation logical source identities changed")
    histories = value["histories"]
    comparison._require(isinstance(histories, list) and len(histories) >= 2,
                        "multi-generation carry-forward requires multiple reviewed histories")
    fresh_raw = Path(manifest["output_directory"])
    comparison._require(fresh_raw.is_absolute(),
                        "multi-generation fresh output path is malformed")
    fresh_output = (_canonical_root(str(fresh_raw.parent), "fresh output parent")
                    / fresh_raw.name)
    comparison._require(str(fresh_output) == str(fresh_raw),
                        "multi-generation fresh output path is malformed")
    segments = tuple(_validate_historical_segment(
        item, logical, fresh_output, check_lease=check_historical_lease)
                     for item in histories)
    generation_ids = [segment.generation_id for segment in segments]
    ledger_ids = [(str(segment.root), segment.ledger_sha256) for segment in segments]
    comparison._require(len(set(generation_ids)) == len(generation_ids)
                        and len({segment.root for segment in segments}) == len(segments)
                        and len(set(ledger_ids)) == len(segments),
                        "historical generation, root, or physical ledger binding is duplicated")
    output_roots = [fresh_output, *(segment.root for segment in segments)]
    comparison._require(all(left != right
                            and not left.is_relative_to(right)
                            and not right.is_relative_to(left)
                            for position, left in enumerate(output_roots)
                            for right in output_roots[position + 1:]),
                        "historical and fresh output roots must be pairwise non-overlapping")
    comparison._require(all(review != output
                            and not review.is_relative_to(output)
                            and not output.is_relative_to(review)
                            for review in {segment.review_root for segment in segments}
                            for output in output_roots),
                        "historical review roots overlap an output or destination tree")
    legacy_plans: dict[str, CarryForwardPlan] = {}
    multi_plans: dict[str, MultiGenerationPlan] = {}
    history_positions = {comparison.json_digest(item): index
                         for index, item in enumerate(histories)}
    for segment in segments:
        nested = segment.nested_carry_forward
        if nested is None:
            continue
        digest = comparison.json_digest(nested)
        current_position = generation_ids.index(segment.generation_id)
        if nested.get("schema_version") == SCHEMA_VERSION and digest not in legacy_plans:
            legacy_plan = validate_carry_forward(
                nested, segment.manifest, comparison.json_digest(segment.manifest),
                approval=segment.approval, live_current_observer=False)
            anchor_ledger = nested.get("source", {}).get("ledger", {}).get("sha256")
            anchors = [prior for prior in segments[:current_position]
                       if prior.root == legacy_plan.source_root
                       and prior.ledger_sha256 == anchor_ledger
                       and prior.manifest == legacy_plan.source_manifest]
            comparison._require(len(anchors) == 1,
                                "nested V1 lineage omitted its exact earlier physical history")
            legacy_plans[digest] = legacy_plan
        elif (nested.get("schema_version") == MULTI_GENERATION_SCHEMA_VERSION
              and digest not in multi_plans):
            nested_histories = nested.get("histories")
            comparison._require(isinstance(nested_histories, list) and nested_histories
                                and all(comparison.json_digest(item) in history_positions
                                        and history_positions[comparison.json_digest(item)] < current_position
                                        for item in nested_histories),
                                "nested V2 lineage is not an exact reviewed subset of earlier flat histories")
            multi_plans[digest] = validate_multi_generation_carry_forward(
                nested, segment.manifest, comparison.json_digest(segment.manifest),
                approval=segment.approval, check_historical_lease=check_historical_lease)
        else:
            comparison._require(digest in legacy_plans or digest in multi_plans,
                                "nested history lacks an independently reviewed V1 or V2 lineage")
    sources = tuple(source for segment in segments
                    for source in _validate_historical_evidence(
                        segment, logical, legacy_plans, multi_plans))
    comparison._require(len({(source.generation_id, source.arm) for source in sources})
                        == len(sources),
                        "historical generation has duplicate evidence sources for one arm")
    covered: set[tuple[str, str, int]] = set()
    for segment in segments:
        comparison._require(covered.isdisjoint(segment.complete_trials),
                            "historical valid coverage overlap would double-count carried evidence")
        covered.update(segment.complete_trials)
    source_pairs = [(source.arm, case_id) for source in sources for case_id in source.case_ids]
    comparison._require(len(source_pairs) == len(set(source_pairs))
                        and set(source_pairs) == {identity[:2] for identity in covered},
                        "historical evidence source coverage is duplicated or incomplete")
    allowed_observers = {OLD_OBSERVER_SHA256, logical["identities"]["observer"],
                         *(segment.manifest["identities"]["observer"] for segment in segments
                           if segment.nested_carry_forward is not None
                           and segment.nested_carry_forward.get("schema_version") == SCHEMA_VERSION)}
    _validate_observer_replays(
        value["observer_replays"], logical, sources, segments, allowed_observers)
    logical_pairs = frozenset((arm, case_id) for arm in logical["arms"] for case_id in logical_cases)
    carried = frozenset(identity[:2] for identity in covered)
    carried_trials = frozenset(covered)
    fresh = logical_pairs - carried
    fresh_trials = frozenset((arm, case_id, trial) for arm, case_id in fresh for trial in (1, 2, 3))
    request_trials = frozenset((arm, case_id, trial) for arm in manifest["arms"]
                               for case_id in request_cases for trial in (1, 2, 3))
    comparison._require(carried_trials.isdisjoint(fresh_trials)
                        and carried_trials | fresh_trials
                        == frozenset((arm, case_id, trial) for arm, case_id in logical_pairs
                                     for trial in (1, 2, 3))
                        and request_trials == fresh_trials,
                        "fresh request is not the exact disjoint logical complement")
    policy = value["policy"]
    comparison._require(policy == {"automatic_retries": 0, "refunds": False,
                                  "regrades": False, "resets": False,
                                  "new_generation_invalid_reruns": True}
                        and all(type(policy[key]) is bool
                                for key in ("refunds", "regrades", "resets",
                                            "new_generation_invalid_reruns")),
                        "multi-generation retry, refund, regrade, or reset policy changed")
    historical_charged = sum(segment.charged_trials for segment in segments)
    invalid = sum(segment.invalid_trials for segment in segments)
    unknown = sum(segment.unknown_trials for segment in segments)
    accounting = {
        "logical_full_trials": len(logical_pairs) * 3,
        "carried_trials": len(carried_trials),
        "fresh_launch_ceiling": len(fresh_trials),
        "historical_charged_launches": historical_charged,
        "invalid_launches": invalid,
        "unknown_launches": unknown,
        "maximum_total_charged_attempts": historical_charged + len(fresh_trials),
    }
    comparison._require(value["accounting"] == accounting
                        and all(type(number) is int for number in accounting.values()),
                        "multi-generation accounting differs from physical histories and semantic coverage")
    if approval is not None:
        comparison._require(approval.get("schema_version") == "trigger-campaign-approval/v5"
                            and approval.get("carry_forward_review", {}).get("carry_forward_sha256")
                            == comparison.json_digest(value),
                            "V5 review does not bind the exact multi-generation component")
    models: dict[str, set] = {}
    for source in sources:
        for host, values in source.models.items():
            models.setdefault(host, set()).update(values)
    return MultiGenerationPlan(
        value, comparison.json_digest(value), logical, segments, sources, carried,
        carried_trials, fresh, fresh_trials,
        {host: frozenset(values) for host, values in models.items()},
        len(fresh_trials), historical_charged, historical_charged + len(fresh_trials),
    )


def validate_fresh_ledger(
    plan: CarryForwardPlan | MultiGenerationPlan, launches: list[dict], *, complete: bool = False,
) -> None:
    seen = set()
    for row in launches:
        comparison._require(isinstance(row, dict) and row.get("arm") in {"serial:baseline", "serial:candidate"}
                            and type(row.get("trial_number")) is int
                            and row.get("status") in {"unknown", "complete", "invalid"},
                            "fresh ledger row is malformed")
        identity = (row["arm"].partition(":")[2], row.get("case_id"), row["trial_number"])
        comparison._require(identity in plan.fresh_trials and identity not in seen,
                            "fresh ledger contains carried, duplicate, or out-of-scope identity")
        seen.add(identity)
    if complete:
        comparison._require(seen == plan.fresh_trials
                            and all(row["status"] == "complete" for row in launches),
                            "completed fresh ledger is not the exact approved identity complement")


def source_aware_index(manifest: dict, plan: CarryForwardPlan, fresh_index: dict) -> dict:
    """Represent the baseline as two immutable sources without copying old artifacts."""
    fresh_manifest = {**manifest, "qualification_scope": "pr-core",
                      "roster": [row for row in manifest["roster"] if row["case_id"] in set(plan.fresh_case_ids)]}
    fresh_manifest["corpus_sha256"] = comparison.json_digest(fresh_manifest["roster"])
    return {
        "schema_version": INDEX_SCHEMA_VERSION,
        "experiment_id": manifest["experiment_id"],
        "experiment_sha256": comparison.json_digest(manifest),
        "arm": "baseline",
        "non_contiguous": True,
        "timing_eligible": False,
        "carry_forward": plan.component,
        "sources": [
            {"kind": "carried", "root": str(plan.source_root), "manifest": plan.partial_manifest,
             "index": plan.source_index, "case_ids": list(plan.carried_case_ids)},
            {"kind": "fresh", "root": None, "manifest": fresh_manifest,
             "index": fresh_index, "case_ids": list(plan.fresh_case_ids)},
        ],
    }


def source_aware_union(index: dict, manifest: dict, expected_arm: str) -> tuple[dict, dict]:
    """Return carried/fresh sources after enforcing the exact typed union contract."""
    comparison._require(isinstance(index, dict) and set(index) == {
        "schema_version", "experiment_id", "experiment_sha256", "arm", "non_contiguous",
        "timing_eligible", "carry_forward", "sources"}
        and index["schema_version"] == INDEX_SCHEMA_VERSION
        and index["experiment_id"] == manifest["experiment_id"]
        and index["experiment_sha256"] == comparison.json_digest(manifest)
        and index["arm"] == expected_arm == "baseline"
        and index["non_contiguous"] is True and index["timing_eligible"] is False
        and isinstance(index["sources"], list) and len(index["sources"]) == 2,
        "source-aware carry-forward index is malformed")
    sources = {source.get("kind"): source for source in index["sources"] if isinstance(source, dict)}
    comparison._require(set(sources) == {"carried", "fresh"}, "source-aware index lacks exact provenance arms")
    carried, fresh = sources["carried"], sources["fresh"]
    expected_fields = {"kind", "root", "manifest", "index", "case_ids"}
    comparison._require(set(carried) == expected_fields and set(fresh) == expected_fields
                        and isinstance(carried["root"], str) and Path(carried["root"]).is_absolute()
                        and fresh["root"] is None,
                        "source-aware index roots are malformed")
    full_ids = [row["case_id"] for row in manifest["roster"]]
    carried_ids, fresh_ids = carried["case_ids"], fresh["case_ids"]
    comparison._require(len(carried_ids) == 137 and len(fresh_ids) == 80
                        and len(set(carried_ids)) == 137 and len(set(fresh_ids)) == 80
                        and set(carried_ids).isdisjoint(fresh_ids)
                        and [case_id for case_id in full_ids if case_id in set(carried_ids)] == carried_ids
                        and [case_id for case_id in full_ids if case_id in set(fresh_ids)] == fresh_ids
                        and set(carried_ids) | set(fresh_ids) == set(full_ids),
                        "source-aware index is not the ordered disjoint 217-case baseline union")
    return carried, fresh


def multi_source_index(
    plan: MultiGenerationPlan, arm: str, fresh_index: dict | None,
) -> dict:
    """Publish one logical arm from any number of reviewed sources, including no fresh source."""
    comparison._require(arm in plan.logical_manifest["arms"],
                        "multi-source index arm is outside the logical experiment")
    sources = [
        {"kind": "historical", "generation_id": source.generation_id,
         "root": str(source.root), "manifest": source.manifest, "index": source.index,
         "case_ids": list(source.case_ids)}
        for source in plan.sources if source.arm == arm
    ]
    fresh_ids = tuple(row["case_id"] for row in plan.logical_manifest["roster"]
                      if (arm, row["case_id"]) in plan.fresh)
    if fresh_ids:
        comparison._require(isinstance(fresh_index, dict),
                            "multi-source arm with fresh coverage lacks its evidence index")
        fresh_manifest = fresh_partial_manifest(plan.logical_manifest, fresh_ids)
        sources.append({"kind": "fresh", "generation_id": None, "root": None,
                        "manifest": fresh_manifest, "index": fresh_index,
                        "case_ids": list(fresh_ids)})
    else:
        comparison._require(fresh_index is None,
                            "no-fresh arm cannot publish an empty synthetic evidence source")
    return {
        "schema_version": MULTI_SOURCE_INDEX_SCHEMA_VERSION,
        "experiment_id": plan.logical_manifest["experiment_id"],
        "experiment_sha256": comparison.json_digest(plan.logical_manifest),
        "arm": arm, "non_contiguous": True, "timing_eligible": False,
        "carry_forward": plan.component, "sources": sources,
    }
def multi_source_union(
    index: dict, plan: MultiGenerationPlan, expected_arm: str,
) -> tuple[tuple[dict, ...], dict | None]:
    """Validate a V3 index against the re-admitted histories and exact fresh complement."""
    fields = {"schema_version", "experiment_id", "experiment_sha256", "arm",
              "non_contiguous", "timing_eligible", "carry_forward", "sources"}
    comparison._require(isinstance(index, dict) and set(index) == fields
                        and index["schema_version"] == MULTI_SOURCE_INDEX_SCHEMA_VERSION
                        and index["experiment_id"] == plan.logical_manifest["experiment_id"]
                        and index["experiment_sha256"] == comparison.json_digest(plan.logical_manifest)
                        and index["arm"] == expected_arm
                        and index["non_contiguous"] is True
                        and index["timing_eligible"] is False
                        and index["carry_forward"] == plan.component
                        and isinstance(index["sources"], list),
                        "multi-source evidence index is malformed")
    expected = multi_source_index(
        plan, expected_arm,
        next((source.get("index") for source in index["sources"]
              if isinstance(source, dict) and source.get("kind") == "fresh"), None),
    )
    comparison._require(index == expected,
                        "multi-source evidence index differs from revalidated lineage")
    historical = tuple(source for source in index["sources"] if source["kind"] == "historical")
    fresh = next((source for source in index["sources"] if source["kind"] == "fresh"), None)
    case_ids = [case_id for source in index["sources"] for case_id in source["case_ids"]]
    expected_ids = [row["case_id"] for row in plan.logical_manifest["roster"]]
    comparison._require(len(case_ids) == len(set(case_ids))
                        and case_ids == expected_ids,
                        "multi-source arm is not the ordered disjoint logical case union")
    return historical, fresh


def predecessor_runner_is_live(pid: int, command: list[str], started_at: float,
                               *, runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
                               probe: Callable[..., object] = os.kill) -> bool:
    """Match an exact retained ownership fingerprint; PID reuse alone is never ownership."""
    comparison._require(type(pid) is int and pid > 0 and isinstance(command, list) and command,
                        "predecessor runner fingerprint is malformed")
    try:
        probe(pid, 0)
    except ProcessLookupError:
        return False
    except OSError as exc:
        raise ValueError(f"predecessor runner liveness could not be inspected: {exc}") from None
    completed = runner(["ps", "-p", str(pid), "-o", "uid=", "-o", "lstart=", "-o", "command="],
                       check=False, capture_output=True, text=True)
    comparison._require(completed.returncode == 0 and completed.stdout.strip(),
                        "predecessor runner liveness inspection was inconclusive")
    match = re.match(r"\s*(\d+)\s+([A-Z][a-z]{2}\s+[A-Z][a-z]{2}\s+\d+\s+\d\d:\d\d:\d\d\s+\d{4})\s+(.*)",
                     completed.stdout.strip())
    comparison._require(match is not None, "predecessor runner liveness inspection was malformed")
    if int(match.group(1)) != os.getuid():
        return False
    try:
        observed = datetime.strptime(match.group(2), "%a %b %d %H:%M:%S %Y").timestamp()
    except ValueError:
        raise ValueError("predecessor runner start identity was malformed") from None
    return abs(observed - started_at) < 2 and match.group(3) == " ".join(command)


def predecessor_process_group_is_live(
    pgid: int,
    completed_at: float,
    *,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    probe: Callable[..., object] = os.killpg,
) -> bool:
    """Distinguish an old owned group from a later unrelated PGID reuse."""
    comparison._require(type(pgid) is int and pgid > 0
                        and type(completed_at) in {int, float} and not isinstance(completed_at, bool),
                        "predecessor child process-group fingerprint is malformed")
    try:
        probe(pgid, 0)
    except ProcessLookupError:
        return False
    except OSError as exc:
        raise ValueError(f"predecessor process-group liveness could not be inspected: {exc}") from None
    completed = runner(["ps", "-axo", "uid=,pid=,pgid=,lstart=,command="],
                       check=False, capture_output=True, text=True)
    comparison._require(completed.returncode == 0,
                        "predecessor process-group liveness inspection was inconclusive")
    members = []
    pattern = re.compile(r"\s*(\d+)\s+(\d+)\s+(\d+)\s+"
                         r"([A-Z][a-z]{2}\s+[A-Z][a-z]{2}\s+\d+\s+\d\d:\d\d:\d\d\s+\d{4})\s+(.*)")
    for line in completed.stdout.splitlines():
        match = pattern.fullmatch(line)
        comparison._require(match is not None,
                            "predecessor process-group liveness inspection was malformed")
        if int(match.group(3)) == pgid:
            try:
                started = datetime.strptime(match.group(4), "%a %b %d %H:%M:%S %Y").timestamp()
            except ValueError:
                raise ValueError("predecessor child start identity was malformed") from None
            members.append(started)
    comparison._require(members, "live predecessor process group was missing from process inspection")
    return any(started <= completed_at + 2 for started in members)
