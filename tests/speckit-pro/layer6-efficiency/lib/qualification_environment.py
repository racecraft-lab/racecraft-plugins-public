#!/usr/bin/env python3
"""Closed pre-execution environment contracts for G56R-003 scoring."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime


ENVIRONMENT_CONTRACT_SCHEMA_VERSION = "qualification-environment.v1"
AUTHENTICATION_MODES = ("chatgpt_subscription", "api_key")
CONTROLLED_OVERRIDE_FIELDS = (
    "model_override_absent",
    "reasoning_effort_override_absent",
    "service_tier_override_absent",
    "model_provider_override_absent",
    "api_key_override_absent",
)
_CONTRACT_FIELDS = frozenset({
    "schema_version",
    "environment_contract_id",
    "environment_contract_digest",
    "status",
    "client_version_range",
    "parent_session",
    "controlled_runtime_overrides",
    "authentication_mode",
    "ultra_state",
    "frozen_at",
})
_RANGE_FIELDS = frozenset({"minimum", "maximum"})
_PARENT_FIELDS = frozenset({"model", "effort"})
_OBSERVATION_FIELDS = frozenset({
    "client_version",
    "parent_session",
    "controlled_runtime_overrides",
    "authentication_mode",
    "ultra_state",
    "observed_at",
})
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_VERSION_RE = re.compile(r"^codex-cli ([0-9]+)\.([0-9]+)\.([0-9]+)$")


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _closed(value: object, fields: frozenset[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(f"{label} must use the closed field set")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _timestamp(value: object, label: str) -> str:
    text = _text(value, label)
    normalized = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{label} must be RFC3339") from exc
    if parsed.utcoffset() is None:
        raise ValueError(f"{label} must include an offset")
    return text


def _version(value: object, label: str) -> tuple[int, int, int]:
    text = _text(value, label)
    match = _VERSION_RE.fullmatch(text)
    if match is None:
        raise ValueError(f"{label} must be a codex-cli semantic version")
    return tuple(int(part) for part in match.groups())


def _validate_overrides(value: object) -> dict:
    row = _closed(
        value,
        frozenset(CONTROLLED_OVERRIDE_FIELDS),
        "controlled runtime overrides",
    )
    if any(row[field] is not True for field in CONTROLLED_OVERRIDE_FIELDS):
        raise ValueError("controlled runtime overrides must all be proven absent")
    return copy.deepcopy(row)


def validate_environment_contract(value: object) -> dict:
    """Validate a frozen, content-addressed environment contract."""
    row = _closed(copy.deepcopy(value), _CONTRACT_FIELDS, "environment contract")
    if (
        row["schema_version"] != ENVIRONMENT_CONTRACT_SCHEMA_VERSION
        or row["status"] != "frozen_before_execution"
    ):
        raise ValueError("environment contract version or status is invalid")
    version_range = _closed(
        row["client_version_range"],
        _RANGE_FIELDS,
        "client version range",
    )
    minimum = _version(version_range["minimum"], "minimum client version")
    maximum = _version(version_range["maximum"], "maximum client version")
    if minimum > maximum:
        raise ValueError("client version range is inverted")
    parent = _closed(row["parent_session"], _PARENT_FIELDS, "parent session")
    _text(parent["model"], "parent-session model")
    _text(parent["effort"], "parent-session effort")
    row["controlled_runtime_overrides"] = _validate_overrides(
        row["controlled_runtime_overrides"]
    )
    if row["authentication_mode"] not in AUTHENTICATION_MODES:
        raise ValueError("authentication mode is outside the closed set")
    if row["ultra_state"] != "off":
        raise ValueError("Ultra must be off as a pre-execution admission condition")
    _timestamp(row["frozen_at"], "environment contract freeze timestamp")
    expected_digest = _digest({
        key: item
        for key, item in row.items()
        if key not in {
            "environment_contract_id",
            "environment_contract_digest",
        }
    })
    if row["environment_contract_digest"] != expected_digest:
        raise ValueError("environment contract digest does not match content")
    if row["environment_contract_id"] != _digest({
        key: item
        for key, item in row.items()
        if key != "environment_contract_id"
    }):
        raise ValueError("environment contract ID does not match content")
    if _DIGEST_RE.fullmatch(row["environment_contract_id"]) is None:
        raise ValueError("environment contract ID must be a SHA-256 digest")
    return row


def freeze_environment_contract(value: object) -> dict:
    """Seal a draft. This records expectations; it never mutates the environment."""
    if not isinstance(value, dict):
        raise ValueError("environment contract draft must be an object")
    row = copy.deepcopy(value)
    row["schema_version"] = ENVIRONMENT_CONTRACT_SCHEMA_VERSION
    row["status"] = "frozen_before_execution"
    row["environment_contract_id"] = "sha256:" + "0" * 64
    row["environment_contract_digest"] = _digest({
        key: item
        for key, item in row.items()
        if key not in {
            "environment_contract_id",
            "environment_contract_digest",
        }
    })
    row["environment_contract_id"] = _digest({
        key: item
        for key, item in row.items()
        if key != "environment_contract_id"
    })
    return validate_environment_contract(row)


def environment_contract_binding(value: object) -> dict:
    row = validate_environment_contract(value)
    return {
        "id": row["environment_contract_id"],
        "digest": row["environment_contract_digest"],
    }


def evaluate_environment_conformance(
    contract: object,
    observation: object,
) -> dict:
    """Compare without mutating; accumulate all mismatches before returning."""
    frozen = validate_environment_contract(contract)
    if not isinstance(observation, dict):
        missing = sorted(_OBSERVATION_FIELDS)
    else:
        missing = sorted(_OBSERVATION_FIELDS - set(observation))
    if missing:
        return {
            "status": "unobservable",
            "score_eligible": False,
            "failure_plane": "evidence_boundary",
            "failure_code": "required_evidence_missing",
            "findings": [f"missing observation field: {field}" for field in missing],
        }
    extra = sorted(set(observation) - _OBSERVATION_FIELDS)
    if extra:
        return {
            "status": "unobservable",
            "score_eligible": False,
            "failure_plane": "evidence_boundary",
            "failure_code": "required_evidence_missing",
            "findings": [f"undeclared observation field: {field}" for field in extra],
        }
    findings: list[str] = []
    try:
        observed_version = _version(
            observation["client_version"], "observed client version"
        )
        minimum = _version(
            frozen["client_version_range"]["minimum"], "minimum client version"
        )
        maximum = _version(
            frozen["client_version_range"]["maximum"], "maximum client version"
        )
        if not minimum <= observed_version <= maximum:
            findings.append("observed client version is outside the frozen range")
    except ValueError as exc:
        findings.append(str(exc))
    if observation["parent_session"] != frozen["parent_session"]:
        findings.append("observed parent session differs from the frozen contract")
    if observation["controlled_runtime_overrides"] != frozen[
        "controlled_runtime_overrides"
    ]:
        findings.append("observed controlled overrides differ from the frozen contract")
    if observation["authentication_mode"] != frozen["authentication_mode"]:
        findings.append("observed authentication mode differs from the frozen contract")
    if observation["ultra_state"] != frozen["ultra_state"]:
        findings.append("observed Ultra state differs from the frozen contract")
    try:
        _timestamp(observation["observed_at"], "environment observation timestamp")
    except ValueError as exc:
        findings.append(str(exc))
    if findings:
        return {
            "status": "diverged",
            "score_eligible": False,
            "failure_plane": "treatment",
            "failure_code": "treatment_infrastructure_failure",
            "findings": findings,
        }
    return {
        "status": "conforming",
        "score_eligible": True,
        "failure_plane": "none",
        "failure_code": "none",
        "findings": [],
    }


__all__ = (
    "AUTHENTICATION_MODES",
    "CONTROLLED_OVERRIDE_FIELDS",
    "ENVIRONMENT_CONTRACT_SCHEMA_VERSION",
    "environment_contract_binding",
    "evaluate_environment_conformance",
    "freeze_environment_contract",
    "validate_environment_contract",
)
