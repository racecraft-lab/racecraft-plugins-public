#!/usr/bin/env python3
"""G56R-003 governed role-corpus validation and scheduling."""

from __future__ import annotations

import copy as _copy
import hashlib as _hashlib
import json as _json
import re as _re
import tomllib as _tomllib
from pathlib import Path as _Path
from typing import Iterable as _Iterable


ROLE_CORPUS_SCHEMA_VERSION = "role-corpus.v1"
GOVERNED_ROLE_ORDER = (
    "analyze-executor",
    "autopilot-fast-helper",
    "checklist-executor",
    "clarify-executor",
    "codebase-analyst",
    "consensus-synthesizer",
    "domain-researcher",
    "gate-validator",
    "implement-executor",
    "phase-executor",
    "spec-context-analyst",
    "uat-runbook-author",
)
REQUIRED_CORE_ROLES = (
    "analyze-executor",
    "checklist-executor",
    "clarify-executor",
    "codebase-analyst",
    "consensus-synthesizer",
    "domain-researcher",
    "gate-validator",
    "implement-executor",
    "phase-executor",
    "spec-context-analyst",
    "uat-runbook-author",
)
EXECUTABLE_CORE_ROLES = (
    "analyze-executor",
    "checklist-executor",
    "clarify-executor",
    "codebase-analyst",
    "domain-researcher",
    "implement-executor",
    "phase-executor",
    "spec-context-analyst",
    "uat-runbook-author",
)
NON_EXECUTABLE_CORE_ROLES = ("consensus-synthesizer", "gate-validator")
OPTIONAL_HELPER_ROLES = ("autopilot-fast-helper",)
PARTITION_TYPES = ("calibration", "screening", "selection", "cohort_lock", "integrated_confirmation")

_ROLE_INDEX = {role_id: index for index, role_id in enumerate(GOVERNED_ROLE_ORDER)}
_ROLE_SET = frozenset(GOVERNED_ROLE_ORDER)
_REQUIRED_CORE_SET = frozenset(REQUIRED_CORE_ROLES)
_EXECUTABLE_CORE_SET = frozenset(EXECUTABLE_CORE_ROLES)
_NON_EXECUTABLE_CORE_SET = frozenset(NON_EXECUTABLE_CORE_ROLES)
_HELPER_SET = frozenset(OPTIONAL_HELPER_ROLES)
_EXECUTABLE_ROLE_SET = _EXECUTABLE_CORE_SET | _HELPER_SET
_DIGEST_RE = _re.compile(r"^sha256:[0-9a-f]{64}$")
_UTC_RE = _re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_TOP_LEVEL_FIELDS = frozenset({
    "schema_version",
    "corpus_id",
    "corpus_version",
    "corpus_digest",
    "partition_binding",
    "roles",
})
_ROLE_FIELDS = frozenset({
    "role_id",
    "required_core",
    "optional_helper",
    "executable",
    "source_binding",
    "fixture_binding",
    "objective_binding",
    "partition_binding",
    "permitted_tools",
    "sandbox",
    "expected_artifacts",
    "acceptance_oracle",
    "independent_review",
    "route_bindings",
})
_SOURCE_FIELDS = frozenset({"source_path", "source_kind", "source_digest"})
_FIXTURE_FIELDS = frozenset({
    "fixture_id",
    "fixture_version",
    "fixture_digest",
    "fixture_state",
    "current",
    "invalidated_at",
    "invalidation_reason",
})
_OBJECTIVE_FIELDS = frozenset({"objective_id", "objective_digest"})
_PARTITION_FIELDS = frozenset({
    "partition_id",
    "partition_type",
    "partition_digest",
    "qualification_eligible",
})
_SANDBOX_FIELDS = frozenset({"mode", "network", "mutation"})
_ARTIFACT_FIELDS = frozenset({"artifact_contract_id", "artifact_type", "artifact_digest"})
_ORACLE_FIELDS = frozenset({"oracle_id", "oracle_version", "oracle_digest"})
_REVIEW_FIELDS = frozenset({"review_id", "reviewer_digest", "review_digest", "review_state", "reviewed_at"})
_ROUTE_FIELDS = frozenset({
    "role_id",
    "route_id",
    "candidate_freeze_id",
    "agent_contract_id",
    "route_digest",
    "admission_status",
})


def canonical_bytes(value: object) -> bytes:
    """Return the deterministic JSON byte representation used for corpus digests."""
    return _json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest(value: object) -> str:
    """Return a ``sha256:<hex>`` digest for bytes or canonical JSON values."""
    payload = value if isinstance(value, bytes) else canonical_bytes(value)
    return "sha256:" + _hashlib.sha256(payload).hexdigest()


def _closed(value: object, keys: frozenset[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} must use its closed shape")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _digest(value: object, label: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a sha256 digest")
    return value


def _timestamp(value: object, label: str) -> str:
    if not isinstance(value, str) or _UTC_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be an RFC3339 UTC timestamp")
    return value


def _bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be boolean")
    return value


def _source_path_for(role_id: str) -> str:
    if role_id in _NON_EXECUTABLE_CORE_SET:
        return f"speckit-pro/agents/{role_id}.md"
    return f"speckit-pro/codex-agents/{role_id}.toml"


def _source_kind_for(role_id: str) -> str:
    return "governed_markdown_contract" if role_id in _NON_EXECUTABLE_CORE_SET else "codex_toml"


def _read_source_bytes(repo_root: _Path, relative_path: str) -> bytes:
    source_path = _Path(relative_path)
    if source_path.is_absolute() or ".." in source_path.parts:
        raise ValueError("source path must be repository-relative")
    full_path = repo_root / source_path
    try:
        if not full_path.is_file():
            raise ValueError("source path does not resolve to a file")
        return full_path.read_bytes()
    except OSError as exc:
        raise ValueError("source path could not be read") from exc


def _validate_source_binding(value: object, *, role_id: str, repo_root: _Path) -> dict:
    row = _closed(value, _SOURCE_FIELDS, "source binding")
    source_path = _text(row["source_path"], "source path")
    source_kind = row["source_kind"]
    if source_path != _source_path_for(role_id):
        raise ValueError("source path does not match governed role")
    if source_kind != _source_kind_for(role_id):
        raise ValueError("source kind does not match governed role")
    source_digest = _digest(row["source_digest"], "source digest")
    source_bytes = _read_source_bytes(repo_root, source_path)
    if source_digest != digest(source_bytes):
        raise ValueError("source digest does not match role source bytes")
    if source_kind == "codex_toml":
        try:
            source_toml = _tomllib.loads(source_bytes.decode("utf-8"))
        except (_tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("source TOML is not parseable") from exc
        if source_toml.get("name") != role_id:
            raise ValueError("source TOML name does not match governed role")
    return _copy.deepcopy(row)


def _validate_fixture_binding(value: object) -> dict:
    row = _closed(value, _FIXTURE_FIELDS, "fixture binding")
    _text(row["fixture_id"], "fixture ID")
    _text(row["fixture_version"], "fixture version")
    _digest(row["fixture_digest"], "fixture digest")
    if row["fixture_state"] != "valid" or row["current"] is not True:
        raise ValueError("stale fixture cannot be scheduled")
    if row["invalidated_at"] is not None or row["invalidation_reason"] is not None:
        raise ValueError("stale fixture cannot be scheduled")
    return _copy.deepcopy(row)


def _validate_objective_binding(value: object) -> dict:
    row = _closed(value, _OBJECTIVE_FIELDS, "objective binding")
    _text(row["objective_id"], "objective ID")
    _digest(row["objective_digest"], "objective digest")
    return _copy.deepcopy(row)


def _validate_partition_binding(value: object, *, expected: dict | None, label: str) -> dict:
    row = _closed(value, _PARTITION_FIELDS, label)
    _text(row["partition_id"], "partition ID")
    if row["partition_type"] not in PARTITION_TYPES:
        raise ValueError("partition type is outside the closed inventory")
    _digest(row["partition_digest"], "partition digest")
    _bool(row["qualification_eligible"], "partition eligibility")
    if row["partition_type"] != "calibration" or row["qualification_eligible"] is not False:
        raise ValueError("G56R-003 role corpus must use a non-eligible calibration partition")
    if expected is not None and row != expected:
        raise ValueError("role partition does not match corpus partition")
    return _copy.deepcopy(row)


def _validate_tools(value: object) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
        or len(set(value)) != len(value)
    ):
        raise ValueError("permitted tools must be a non-empty unique string array")
    return list(value)


def _validate_sandbox(value: object) -> dict:
    row = _closed(value, _SANDBOX_FIELDS, "sandbox")
    mode = row["mode"]
    network = row["network"]
    mutation = row["mutation"]
    if network != "restricted":
        raise ValueError("sandbox network must be restricted")
    if (mode, mutation) not in {("read-only", "read_only"), ("workspace-write", "workspace_write")}:
        raise ValueError("sandbox mode and mutation policy are inconsistent")
    return _copy.deepcopy(row)


def _validate_expected_artifacts(value: object) -> list[dict]:
    if not isinstance(value, list) or not value:
        raise ValueError("expected artifacts must be a non-empty array")
    result: list[dict] = []
    seen: set[str] = set()
    for item in value:
        row = _closed(item, _ARTIFACT_FIELDS, "expected artifact")
        artifact_id = _text(row["artifact_contract_id"], "artifact contract ID")
        if artifact_id in seen:
            raise ValueError("expected artifacts must be unique")
        seen.add(artifact_id)
        _text(row["artifact_type"], "artifact type")
        _digest(row["artifact_digest"], "artifact digest")
        result.append(_copy.deepcopy(row))
    return result


def _validate_acceptance_oracle(value: object) -> dict:
    row = _closed(value, _ORACLE_FIELDS, "acceptance oracle")
    _text(row["oracle_id"], "oracle ID")
    _text(row["oracle_version"], "oracle version")
    _digest(row["oracle_digest"], "oracle digest")
    return _copy.deepcopy(row)


def _validate_independent_review(value: object) -> dict:
    row = _closed(value, _REVIEW_FIELDS, "independent review")
    _text(row["review_id"], "review ID")
    _digest(row["reviewer_digest"], "reviewer digest")
    _digest(row["review_digest"], "review digest")
    if row["review_state"] != "passed":
        raise ValueError("independent review must be passed")
    _timestamp(row["reviewed_at"], "independent review timestamp")
    return _copy.deepcopy(row)


def _route_digest_payload(row: dict) -> dict:
    return {
        "agent_contract_id": row["agent_contract_id"],
        "candidate_freeze_id": row["candidate_freeze_id"],
        "role_id": row["role_id"],
        "route_id": row["route_id"],
    }


def _validate_route_bindings(value: object, *, role_id: str, executable: bool) -> list[dict]:
    if not isinstance(value, list):
        raise ValueError("route bindings must be an array")
    if not executable:
        if value:
            raise ValueError("non-executable roles cannot carry route bindings")
        return []
    if not value:
        raise ValueError("executable role must bind at least one admitted route")
    result: list[dict] = []
    seen: set[str] = set()
    for item in value:
        row = _closed(item, _ROUTE_FIELDS, "route binding")
        if row["role_id"] != role_id:
            raise ValueError("route binding role does not match role contract")
        route_id = _text(row["route_id"], "route ID")
        if route_id in seen:
            raise ValueError("route bindings must be unique")
        seen.add(route_id)
        _digest(row["candidate_freeze_id"], "candidate freeze ID")
        _text(row["agent_contract_id"], "agent contract ID")
        route_digest = _digest(row["route_digest"], "route digest")
        if route_digest != digest(_route_digest_payload(row)):
            raise ValueError("route digest does not match route binding")
        if row["admission_status"] != "admitted":
            raise ValueError("executable role must bind only admitted route bindings")
        result.append(_copy.deepcopy(row))
    return result


def _validate_role(value: object, *, repo_root: _Path, corpus_partition: dict) -> dict:
    row = _closed(value, _ROLE_FIELDS, "closed role")
    role_id = row["role_id"]
    if role_id not in _ROLE_SET:
        raise ValueError("role is outside exact governed membership")
    required_core = _bool(row["required_core"], "required-core marker")
    optional_helper = _bool(row["optional_helper"], "helper marker")
    executable = _bool(row["executable"], "executable marker")
    if required_core != (role_id in _REQUIRED_CORE_SET):
        raise ValueError("required-core/helper role classification is invalid")
    if optional_helper != (role_id in _HELPER_SET):
        raise ValueError("required-core/helper role classification is invalid")
    if required_core and optional_helper:
        raise ValueError("helper cannot be part of required-core primary statistics")
    if executable != (role_id in _EXECUTABLE_ROLE_SET):
        if role_id in _NON_EXECUTABLE_CORE_SET:
            raise ValueError("non-executable governed role cannot be marked executable")
        raise ValueError("executable governed role cannot be marked non-executable")
    return {
        "role_id": role_id,
        "required_core": required_core,
        "optional_helper": optional_helper,
        "executable": executable,
        "source_binding": _validate_source_binding(row["source_binding"], role_id=role_id, repo_root=repo_root),
        "fixture_binding": _validate_fixture_binding(row["fixture_binding"]),
        "objective_binding": _validate_objective_binding(row["objective_binding"]),
        "partition_binding": _validate_partition_binding(
            row["partition_binding"], expected=corpus_partition, label="role partition binding",
        ),
        "permitted_tools": _validate_tools(row["permitted_tools"]),
        "sandbox": _validate_sandbox(row["sandbox"]),
        "expected_artifacts": _validate_expected_artifacts(row["expected_artifacts"]),
        "acceptance_oracle": _validate_acceptance_oracle(row["acceptance_oracle"]),
        "independent_review": _validate_independent_review(row["independent_review"]),
        "route_bindings": _validate_route_bindings(
            row["route_bindings"], role_id=role_id, executable=executable,
        ),
    }


def validate_role_corpus(corpus: object, *, repo_root: _Path | str | None = None) -> dict:
    """Validate and deterministically order the governed twelve-role corpus."""
    root = _Path(repo_root) if repo_root is not None else _Path(__file__).resolve().parents[3]
    value = _closed(_copy.deepcopy(corpus), _TOP_LEVEL_FIELDS, "closed corpus")
    if value["schema_version"] != ROLE_CORPUS_SCHEMA_VERSION:
        raise ValueError("role corpus schema version is unsupported")
    _text(value["corpus_id"], "corpus ID")
    _text(value["corpus_version"], "corpus version")
    _digest(value["corpus_digest"], "corpus digest")
    corpus_partition = _validate_partition_binding(
        value["partition_binding"], expected=None, label="corpus partition binding",
    )
    roles = value["roles"]
    if not isinstance(roles, list) or len(roles) != len(GOVERNED_ROLE_ORDER):
        raise ValueError("role corpus must contain exactly twelve governed roles")
    role_ids = []
    for raw in roles:
        if not isinstance(raw, dict):
            raise ValueError("closed role must be an object")
        role_id = raw.get("role_id")
        if not isinstance(role_id, str):
            raise ValueError("closed role must carry a role ID")
        role_ids.append(role_id)
    if len(set(role_ids)) != len(role_ids):
        raise ValueError("duplicate role in governed corpus")
    if set(role_ids) != _ROLE_SET:
        raise ValueError("role corpus does not match exact governed membership")
    validated_roles = [
        _validate_role(role, repo_root=root, corpus_partition=corpus_partition)
        for role in roles
    ]
    value["partition_binding"] = corpus_partition
    value["roles"] = sorted(validated_roles, key=lambda role: _ROLE_INDEX[role["role_id"]])
    return value


def corpus_statistics(corpus: dict) -> dict:
    """Return the governed population counts used by primary corpus analysis."""
    roles = corpus["roles"]
    required = [role["role_id"] for role in roles if role["required_core"]]
    helpers = [role["role_id"] for role in roles if role["optional_helper"]]
    executable_required = [
        role["role_id"] for role in roles if role["required_core"] and role["executable"]
    ]
    non_executable_required = [
        role["role_id"] for role in roles if role["required_core"] and not role["executable"]
    ]
    executable_helpers = [
        role["role_id"] for role in roles if role["optional_helper"] and role["executable"]
    ]
    return {
        "total_roles": len(roles),
        "required_core_roles": len(required),
        "optional_helper_roles": len(helpers),
        "executable_required_core_roles": len(executable_required),
        "non_executable_required_core_roles": len(non_executable_required),
        "executable_optional_helper_roles": len(executable_helpers),
        "required_core_primary_role_ids": required,
        "optional_helper_role_ids": helpers,
    }


def _schedule_entry(role: dict, *, skip_reasons: list[str] | None = None) -> dict:
    entry = {
        "role_id": role["role_id"],
        "required_core": role["required_core"],
        "optional_helper": role["optional_helper"],
        "executable": role["executable"],
        "route_bindings": _copy.deepcopy(role["route_bindings"]),
    }
    if skip_reasons is not None:
        entry["skip_reasons"] = list(skip_reasons)
    return entry


def schedule_admitted_roles(corpus: dict, *, admitted_route_ids: _Iterable[str]) -> dict:
    """Return only executable roles whose route IDs are admitted by the active freeze."""
    admitted = set(admitted_route_ids)
    schedule = {"required_core": [], "optional_helpers": [], "unschedulable_governed": []}
    roles = sorted(corpus["roles"], key=lambda role: _ROLE_INDEX[role["role_id"]])
    for role in roles:
        if not role["executable"]:
            schedule["unschedulable_governed"].append(
                _schedule_entry(role, skip_reasons=["non_executable_governed_role"])
            )
            continue
        entry = _schedule_entry(role)
        route_ids = {route["route_id"] for route in role["route_bindings"]}
        if not route_ids or not route_ids <= admitted:
            raise ValueError("scheduled roles must have admitted route bindings")
        if role["optional_helper"]:
            schedule["optional_helpers"].append(entry)
        else:
            schedule["required_core"].append(entry)
    return schedule


globals().pop("annotations", None)

__all__ = [
    "EXECUTABLE_CORE_ROLES",
    "GOVERNED_ROLE_ORDER",
    "NON_EXECUTABLE_CORE_ROLES",
    "OPTIONAL_HELPER_ROLES",
    "PARTITION_TYPES",
    "REQUIRED_CORE_ROLES",
    "ROLE_CORPUS_SCHEMA_VERSION",
    "canonical_bytes",
    "corpus_statistics",
    "digest",
    "schedule_admitted_roles",
    "validate_role_corpus",
]
