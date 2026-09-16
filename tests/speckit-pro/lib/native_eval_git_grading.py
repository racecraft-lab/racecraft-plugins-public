"""Deterministic grading for controller-attested native Git final state."""

from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
import re
from typing import Any, Mapping


CHECK_FIELDS = frozenset({
    "head_equals_initial_feature", "branch", "commit_count", "commits_added",
    "changed_tracked_paths_from_initial_feature", "status",
})
RECORD_SCHEMA = "native-eval-controller-git-observation/v1"
OBSERVATION_SCHEMA = "native-eval-git-observation/v1"
_OBJECT_ID = re.compile(r"[a-f0-9]{40}|[a-f0-9]{64}")
_SHA256 = re.compile(r"[a-f0-9]{64}")


class GitGradingError(ValueError):
    """Raised when a Git check or controller evidence record is malformed."""


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise GitGradingError(message)


def _path(value: object, label: str) -> str:
    _need(isinstance(value, str) and bool(value) and "\\" not in value and "\x00" not in value,
          f"{label} is malformed")
    path = PurePosixPath(value)
    _need(bool(path.parts) and not path.is_absolute() and path.as_posix() == value
          and all(part not in {"", ".", ".."} for part in path.parts),
          f"{label} is malformed")
    return value


def _paths(value: object, label: str) -> list[str]:
    _need(isinstance(value, list), f"{label} must be a list")
    result = [_path(item, f"{label} item") for item in value]
    _need(result == sorted(set(result)), f"{label} must be sorted and unique")
    return result


def _oid(value: object, label: str) -> str:
    _need(isinstance(value, str) and _OBJECT_ID.fullmatch(value) is not None,
          f"{label} is malformed")
    return value


def _tracked(value: object, label: str) -> list[dict[str, str]]:
    _need(isinstance(value, list), f"{label} must be a list")
    result: list[dict[str, str]] = []
    for item in value:
        _need(isinstance(item, Mapping) and set(item) == {"path", "index", "worktree"},
              f"{label} item is malformed")
        path = _path(item["path"], f"{label} path")
        _need(all(isinstance(item[key], str) and len(item[key]) == 1
                  for key in ("index", "worktree")),
              f"{label} status code is malformed")
        result.append({"path": path, "index": item["index"], "worktree": item["worktree"]})
    _need([item["path"] for item in result] == sorted({item["path"] for item in result}),
          f"{label} must be sorted and unique")
    return result


def _status(value: object, label: str) -> dict[str, Any]:
    fields = {"clean", "tracked_dirty", "untracked_dirty", "tracked", "untracked"}
    _need(isinstance(value, Mapping) and set(value) == fields, f"{label} is malformed")
    _need(all(type(value[key]) is bool for key in ("clean", "tracked_dirty", "untracked_dirty")),
          f"{label} booleans are malformed")
    tracked = _tracked(value["tracked"], f"{label} tracked")
    untracked = _paths(value["untracked"], f"{label} untracked")
    _need(value["clean"] is (not tracked and not untracked)
          and value["tracked_dirty"] is bool(tracked)
          and value["untracked_dirty"] is bool(untracked),
          f"{label} summary is inconsistent")
    return {
        "clean": value["clean"], "tracked_dirty": value["tracked_dirty"],
        "untracked_dirty": value["untracked_dirty"], "tracked": tracked,
        "untracked": untracked,
    }


def _commits(value: object, label: str) -> list[dict[str, Any]]:
    _need(isinstance(value, list), f"{label} must be a list")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in value:
        _need(isinstance(item, Mapping) and set(item) == {"commit", "message", "paths"},
              f"{label} item is malformed")
        commit = _oid(item["commit"], f"{label} commit")
        _need(commit not in seen and isinstance(item["message"], str),
              f"{label} item is malformed")
        seen.add(commit)
        result.append({
            "commit": commit, "message": item["message"],
            "paths": _paths(item["paths"], f"{label} paths"),
        })
    return result


def validate_check(check: Mapping[str, object], label: str) -> None:
    """Validate the type-specific fields for a native_git_final_state check."""

    _need(type(check.get("head_equals_initial_feature")) is bool,
          f"{label} head_equals_initial_feature must be boolean")
    _need(isinstance(check.get("branch"), str) and bool(check["branch"]),
          f"{label} branch must be nonempty text")
    count = check.get("commit_count")
    _need(type(count) is int and count >= 0, f"{label} commit_count must be a nonnegative integer")
    commits = _commits(check.get("commits_added"), f"{label} commits_added")
    _need(count == len(commits), f"{label} commit_count does not match commits_added")
    _paths(check.get("changed_tracked_paths_from_initial_feature"),
           f"{label} changed_tracked_paths_from_initial_feature")
    _status(check.get("status"), f"{label} status")
    if "registered_worktrees_unchanged" in check:
        _need(check["registered_worktrees_unchanged"] is True,
              f"{label} registered_worktrees_unchanged must be true when specified")


def _registered_worktrees(value: object, initial: Mapping[str, str]) -> dict[str, Any]:
    from native_eval_git_observation import _validate_expected_worktrees

    _need(isinstance(value, Mapping) and set(value) == {"schema_version", "worktrees"}
          and value.get("schema_version") == "native-eval-git-worktrees/v1",
          "controller registered worktrees are malformed")
    rows = value["worktrees"]
    _need(isinstance(rows, list) and bool(rows), "controller registered worktrees are empty")
    for row in rows:
        _need(isinstance(row, Mapping) and set(row) == {"initial", "head", "branch", "status"},
              "controller registered worktree row is malformed")
        _oid(row["head"], "controller registered worktree head")
        _need(row["branch"] is None or isinstance(row["branch"], str) and bool(row["branch"]),
              "controller registered worktree branch is malformed")
        _status(row["status"], "controller registered worktree status")
    try:
        _validate_expected_worktrees([row["initial"] for row in rows], initial)
    except ValueError as exc:
        raise GitGradingError(str(exc)) from exc
    return dict(value)


def validate_observation(value: object) -> dict[str, Any]:
    fields = {
        "schema_version", "initial", "head", "branch", "origin_main", "status",
        "commit_count", "commits_added", "changed_tracked_paths_from_initial_feature",
    }
    _need(isinstance(value, Mapping) and fields <= set(value) <= fields | {"registered_worktrees"}
          and value.get("schema_version") == OBSERVATION_SCHEMA,
          "controller Git observation is malformed")
    initial = value.get("initial")
    _need(isinstance(initial, Mapping)
          and set(initial) == {"baseline_commit", "feature_commit", "feature_tree"},
          "controller Git observation initial identity is malformed")
    normalized_initial = {
        key: _oid(initial[key], f"controller Git observation initial {key}")
        for key in ("baseline_commit", "feature_commit", "feature_tree")
    }
    head = _oid(value.get("head"), "controller Git observation head")
    origin_main = _oid(value.get("origin_main"), "controller Git observation origin_main")
    branch = value.get("branch")
    _need(branch is None or isinstance(branch, str) and bool(branch),
          "controller Git observation branch is malformed")
    count = value.get("commit_count")
    _need(type(count) is int and count >= 0,
          "controller Git observation commit_count is malformed")
    commits = _commits(value.get("commits_added"), "controller Git observation commits_added")
    _need(count == len(commits),
          "controller Git observation commit_count does not match commits_added")
    result = {
        "schema_version": OBSERVATION_SCHEMA, "initial": normalized_initial,
        "head": head, "branch": branch, "origin_main": origin_main,
        "status": _status(value.get("status"), "controller Git observation status"),
        "commit_count": count, "commits_added": commits,
        "changed_tracked_paths_from_initial_feature": _paths(
            value.get("changed_tracked_paths_from_initial_feature"),
            "controller Git observation changed_tracked_paths_from_initial_feature",
        ),
    }
    if "registered_worktrees" in value:
        result["registered_worktrees"] = _registered_worktrees(value["registered_worktrees"], normalized_initial)
    return result


def _controller_record(observation: Mapping[str, object]) -> dict[str, Any]:
    metadata = observation.get("native_metadata")
    _need(isinstance(metadata, Mapping), "controller Git observation evidence is missing")
    record = metadata.get("controller_git_observation")
    _need(isinstance(record, Mapping)
          and set(record) == {"schema", "authority", "observation", "evidence"}
          and record.get("schema") == RECORD_SCHEMA
          and record.get("authority") == "controller",
          "controller Git observation record is missing or malformed")
    value = validate_observation(record.get("observation"))
    evidence = record.get("evidence")
    _need(isinstance(evidence, Mapping) and set(evidence) == {"path", "sha256", "bytes"},
          "controller Git observation evidence binding is malformed")
    _path(evidence.get("path"), "controller Git observation evidence path")
    _need(isinstance(evidence.get("sha256"), str)
          and _SHA256.fullmatch(evidence["sha256"]) is not None
          and type(evidence.get("bytes")) is int and evidence["bytes"] > 0,
          "controller Git observation evidence binding is malformed")
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode("utf-8") + b"\n"
    _need(evidence["sha256"] == hashlib.sha256(payload).hexdigest()
          and evidence["bytes"] == len(payload),
          "controller Git observation evidence is unbound")
    return value


def grade_final_state(
    check: Mapping[str, object], observation: Mapping[str, object],
) -> tuple[str, str]:
    """Grade exact final Git state from the execution-bound controller record."""

    try:
        validate_check(check, "native_git_final_state check")
        actual = _controller_record(observation)
        if check.get("registered_worktrees_unchanged"):
            _need("registered_worktrees" in actual,
                  "controller registered worktree evidence is missing")
    except GitGradingError as exc:
        return "invalid", str(exc)
    expected = {
        "head_equals_initial_feature": check["head_equals_initial_feature"],
        "branch": check["branch"], "commit_count": check["commit_count"],
        "commits_added": check["commits_added"],
        "changed_tracked_paths_from_initial_feature":
            check["changed_tracked_paths_from_initial_feature"],
        "status": check["status"],
    }
    observed = {
        "head_equals_initial_feature": actual["head"] == actual["initial"]["feature_commit"],
        "branch": actual["branch"], "commit_count": actual["commit_count"],
        "commits_added": actual["commits_added"],
        "changed_tracked_paths_from_initial_feature":
            actual["changed_tracked_paths_from_initial_feature"],
        "status": actual["status"],
    }
    mismatches = [key for key in expected if type(observed[key]) is not type(expected[key])
                  or observed[key] != expected[key]]
    if check.get("registered_worktrees_unchanged"):
        for row in actual["registered_worktrees"]["worktrees"]:
            if row["head"] != row["initial"]["head"] or row["branch"] != row["initial"]["branch"] \
                    or not row["status"]["clean"]:
                mismatches.append("registered worktree " + row["initial"]["path"])
    if mismatches:
        return "fail", "controller Git final state differed at: " + ", ".join(mismatches)
    return "pass", "controller-attested Git final state matched every declared field"


__all__ = ("CHECK_FIELDS", "GitGradingError", "grade_final_state", "validate_check", "validate_observation")
