#!/usr/bin/env python3
"""G56R-003 deterministic score-bundle replay helpers."""

from __future__ import annotations

import copy as _copy
import importlib.util as _importlib_util
import re as _re
import sys as _sys
from pathlib import Path as _Path


REPLAY_BUNDLE_SCHEMA_VERSION = "score-replay.v1"
SCORE_REPLAY_SUMMARY_SCHEMA_VERSION = "score-replay-summary.v1"

_SCORING_MODULE_NAME = "_g56r_003_qualification_scoring_for_replay"
_REPLAY_REQUEST_FIELDS = frozenset({"score_bundle", "evidence_refs"})
_REPLAY_BUNDLE_FIELDS = frozenset({
    "schema_version",
    "replay_bundle_id",
    "replay_bundle_digest",
    "score_bundle_binding",
    "score_bundle",
    "evidence_refs",
})
_SUMMARY_REQUEST_FIELDS = frozenset({"score_replays"})
_SUMMARY_ROW_FIELDS = frozenset({"role_id", "required_core", "optional_helper", "replay_bundle"})
_SUMMARY_FIELDS = frozenset({
    "schema_version",
    "summary_id",
    "summary_digest",
    "required_core",
    "optional_helpers",
})
_SUMMARY_GROUP_FIELDS = frozenset({
    "role_count",
    "accepted_count",
    "score_bundle_ids",
    "replay_bundle_ids",
    "role_ids",
})
_DIGEST_RE = _re.compile(r"^sha256:[0-9a-f]{64}$")


def _scoring():
    module = _sys.modules.get(_SCORING_MODULE_NAME)
    if module is not None:
        return module
    module_path = _Path(__file__).with_name("qualification_scoring.py")
    spec = _importlib_util.spec_from_file_location(_SCORING_MODULE_NAME, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    module = _importlib_util.module_from_spec(spec)
    _sys.modules[_SCORING_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def _closed(value: object, keys: frozenset[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} must use its closed shape")
    return value


def _digest_ref(value: object, label: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a sha256 digest")
    return value


def _digest_refs(value: object, label: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return [_digest_ref(item, label) for item in value]


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be boolean")
    return value


def _binding_record(value: object, label: str) -> dict:
    row = _closed(_copy.deepcopy(value), frozenset({"id", "digest"}), f"{label} binding")
    if not isinstance(row["id"], str) or not row["id"]:
        raise ValueError(f"{label} binding ID must be a non-empty string")
    return {
        "id": row["id"],
        "digest": _digest_ref(row["digest"], f"{label} binding digest"),
    }


def _binding(value_id: str, value_digest: str) -> dict:
    return {"id": value_id, "digest": value_digest}


def _replay_digest_payload(bundle: dict) -> dict:
    return {
        key: value
        for key, value in bundle.items()
        if key not in {"replay_bundle_id", "replay_bundle_digest"}
    }


def _summary_digest_payload(summary: dict) -> dict:
    return {
        key: value
        for key, value in summary.items()
        if key not in {"summary_id", "summary_digest"}
    }


def _empty_summary_group() -> dict:
    return {
        "role_count": 0,
        "accepted_count": 0,
        "score_bundle_ids": [],
        "replay_bundle_ids": [],
        "role_ids": [],
    }


def _record_summary_row(group: dict, *, role_id: str, replay_bundle: dict, score_bundle: dict) -> None:
    group["role_count"] += 1
    if score_bundle["score_disposition"] == "accepted":
        group["accepted_count"] += 1
    group["score_bundle_ids"].append(score_bundle["score_bundle_id"])
    group["replay_bundle_ids"].append(replay_bundle["replay_bundle_id"])
    group["role_ids"].append(role_id)


def _validate_summary_group(value: object, label: str) -> dict:
    row = _closed(_copy.deepcopy(value), _SUMMARY_GROUP_FIELDS, label)
    for field in ("role_count", "accepted_count"):
        if not isinstance(row[field], int) or row[field] < 0:
            raise ValueError(f"{label} {field} must be a non-negative integer")
    if row["accepted_count"] > row["role_count"]:
        raise ValueError(f"{label} accepted count cannot exceed role count")
    for field in ("score_bundle_ids", "replay_bundle_ids", "role_ids"):
        if not isinstance(row[field], list):
            raise ValueError(f"{label} {field} must be an array")
    row["score_bundle_ids"] = [_digest_ref(item, f"{label} score bundle ID") for item in row["score_bundle_ids"]]
    row["replay_bundle_ids"] = [_digest_ref(item, f"{label} replay bundle ID") for item in row["replay_bundle_ids"]]
    row["role_ids"] = [_text(item, f"{label} role ID") for item in row["role_ids"]]
    if row["role_count"] != len(row["role_ids"]):
        raise ValueError(f"{label} role count does not match role IDs")
    if row["role_count"] != len(row["score_bundle_ids"]) or row["role_count"] != len(row["replay_bundle_ids"]):
        raise ValueError(f"{label} role count does not match replay bindings")
    return row


def build_score_replay_bundle(value: object) -> dict:
    """Build a replay bundle from one sanitized immutable score bundle."""
    request = _closed(_copy.deepcopy(value), _REPLAY_REQUEST_FIELDS, "score replay request")
    scoring = _scoring()
    score_bundle = scoring.sanitize_committed_scorer_evidence(request["score_bundle"])
    replay_bundle = {
        "schema_version": REPLAY_BUNDLE_SCHEMA_VERSION,
        "score_bundle_binding": _binding(score_bundle["score_bundle_id"], score_bundle["score_bundle_digest"]),
        "score_bundle": score_bundle,
        "evidence_refs": _digest_refs(request["evidence_refs"], "score replay evidence refs"),
    }
    replay_bundle["replay_bundle_digest"] = scoring.digest(_replay_digest_payload(replay_bundle))
    replay_bundle["replay_bundle_id"] = scoring.content_id(replay_bundle, "replay_bundle_id")
    return validate_score_replay_bundle(replay_bundle)


def validate_score_replay_bundle(value: object) -> dict:
    """Validate a replay bundle and its score-bundle binding."""
    replay_bundle = _closed(_copy.deepcopy(value), _REPLAY_BUNDLE_FIELDS, "score replay bundle")
    scoring = _scoring()
    if replay_bundle["schema_version"] != REPLAY_BUNDLE_SCHEMA_VERSION:
        raise ValueError("score replay schema version is unsupported")
    _digest_ref(replay_bundle["replay_bundle_id"], "score replay bundle ID")
    _digest_ref(replay_bundle["replay_bundle_digest"], "score replay bundle digest")
    replay_bundle["score_bundle_binding"] = _binding_record(
        replay_bundle["score_bundle_binding"],
        "score bundle",
    )
    replay_bundle["score_bundle"] = scoring.sanitize_committed_scorer_evidence(
        replay_bundle["score_bundle"]
    )
    expected_binding = _binding(
        replay_bundle["score_bundle"]["score_bundle_id"],
        replay_bundle["score_bundle"]["score_bundle_digest"],
    )
    if replay_bundle["score_bundle_binding"] != expected_binding:
        raise ValueError("score replay drift: score bundle binding does not match")
    replay_bundle["evidence_refs"] = _digest_refs(
        replay_bundle["evidence_refs"],
        "score replay evidence refs",
    )
    if replay_bundle["replay_bundle_digest"] != scoring.digest(_replay_digest_payload(replay_bundle)):
        raise ValueError("score replay bundle digest does not match content")
    if replay_bundle["replay_bundle_id"] != scoring.content_id(replay_bundle, "replay_bundle_id"):
        raise ValueError("score replay bundle ID does not match content")
    return replay_bundle


def replay_score_bundle(value: object) -> dict:
    """Replay a frozen score bundle and return the deterministic score record."""
    try:
        replay_bundle = validate_score_replay_bundle(value)
    except ValueError as exc:
        raise ValueError("score replay drift") from exc
    return replay_bundle["score_bundle"]


def summarize_score_replays(value: object) -> dict:
    """Summarize replayed scores while keeping optional helpers out of primary stats."""
    request = _closed(_copy.deepcopy(value), _SUMMARY_REQUEST_FIELDS, "score replay summary request")
    if not isinstance(request["score_replays"], list):
        raise ValueError("score replays must be an array")
    groups = {
        "required_core": _empty_summary_group(),
        "optional_helpers": _empty_summary_group(),
    }
    for item in request["score_replays"]:
        row = _closed(item, _SUMMARY_ROW_FIELDS, "score replay summary row")
        role_id = _text(row["role_id"], "score replay role ID")
        required_core = _bool(row["required_core"], "required-core marker")
        optional_helper = _bool(row["optional_helper"], "optional-helper marker")
        if required_core == optional_helper:
            raise ValueError("score replay role classification must separate required core and optional helper")
        replay_bundle = validate_score_replay_bundle(row["replay_bundle"])
        score_bundle = replay_score_bundle(replay_bundle)
        _record_summary_row(
            groups["optional_helpers" if optional_helper else "required_core"],
            role_id=role_id,
            replay_bundle=replay_bundle,
            score_bundle=score_bundle,
        )
    scoring = _scoring()
    summary = {
        "schema_version": SCORE_REPLAY_SUMMARY_SCHEMA_VERSION,
        "required_core": groups["required_core"],
        "optional_helpers": groups["optional_helpers"],
    }
    summary["summary_digest"] = scoring.digest(_summary_digest_payload(summary))
    summary["summary_id"] = scoring.content_id(summary, "summary_id")
    return validate_score_replay_summary(summary)


def validate_score_replay_summary(value: object) -> dict:
    """Validate a helper-separated replay summary."""
    summary = _closed(_copy.deepcopy(value), _SUMMARY_FIELDS, "score replay summary")
    scoring = _scoring()
    if summary["schema_version"] != SCORE_REPLAY_SUMMARY_SCHEMA_VERSION:
        raise ValueError("score replay summary schema version is unsupported")
    _digest_ref(summary["summary_id"], "score replay summary ID")
    _digest_ref(summary["summary_digest"], "score replay summary digest")
    summary["required_core"] = _validate_summary_group(summary["required_core"], "required-core summary")
    summary["optional_helpers"] = _validate_summary_group(summary["optional_helpers"], "optional-helper summary")
    helper_roles = set(summary["optional_helpers"]["role_ids"])
    primary_roles = set(summary["required_core"]["role_ids"])
    if helper_roles.intersection(primary_roles):
        raise ValueError("optional helper roles must stay separate from required-core primary stats")
    if summary["summary_digest"] != scoring.digest(_summary_digest_payload(summary)):
        raise ValueError("score replay summary digest does not match content")
    if summary["summary_id"] != scoring.content_id(summary, "summary_id"):
        raise ValueError("score replay summary ID does not match content")
    return summary


globals().pop("annotations", None)

__all__ = [
    "REPLAY_BUNDLE_SCHEMA_VERSION",
    "SCORE_REPLAY_SUMMARY_SCHEMA_VERSION",
    "build_score_replay_bundle",
    "replay_score_bundle",
    "summarize_score_replays",
    "validate_score_replay_bundle",
]
