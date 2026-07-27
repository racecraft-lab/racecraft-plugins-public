"""Canonical Codex agent policy materialization contract."""

from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


MATERIALIZATION_SCHEMA_VERSION = "agent-materialization.v1"
MATERIALIZER_VERSION = "agent-materializer.v1"
MATERIALIZER_SOURCE_PATH = "speckit-pro/speckit_pro_runner/agent_materialization.py"

__all__ = (
    "AgentMaterialization",
    "AgentMaterializationError",
    "MATERIALIZATION_SCHEMA_VERSION",
    "MATERIALIZER_VERSION",
    "canonical_bytes",
    "digest",
    "materialize_agent_policy",
    "verify_destination_bytes",
)


@dataclass(frozen=True)
class AgentMaterialization:
    materialization_id: str
    materializer_version: str
    source_binding: dict[str, Any]
    materializer_binding: dict[str, str]
    candidate_route: dict[str, Any]
    parent_controls: dict[str, Any]
    destination_bytes: bytes
    destination_bytes_digest: str
    instruction_digest: str
    configuration_digest: str
    byte_count: int


class AgentMaterializationError(ValueError):
    """Raised when a source policy cannot be safely materialized."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical_bytes(value)
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def materialize_agent_policy(
    *,
    source_relative_path: str,
    source_bytes: bytes,
    candidate_route: Mapping[str, Any] | None = None,
    parent_controls: Mapping[str, Any] | None = None,
) -> AgentMaterialization:
    """Return exact destination bytes and deterministic proof metadata."""

    source_path = _safe_source_relative_path(source_relative_path)
    if not isinstance(source_bytes, bytes):
        raise AgentMaterializationError("source_bytes must be bytes")
    source_text = _decode_utf8(source_bytes)
    policy = _parse_toml(source_text)
    instructions = _need_string(policy, "developer_instructions")

    expected_route = _route_from_policy(policy)
    expected_controls = _parent_controls_from_policy(policy)
    route = _validated_mapping(candidate_route, expected_route, "candidate route")
    controls = _validated_mapping(parent_controls, expected_controls, "parent controls")
    configuration = {
        key: policy[key]
        for key in sorted(policy)
        if key != "developer_instructions"
    }

    destination_bytes = source_bytes
    source_binding = {
        "path": source_path,
        "digest": digest(destination_bytes),
        "byte_count": len(destination_bytes),
    }
    materializer_binding = {
        "path": MATERIALIZER_SOURCE_PATH,
        "digest": digest(_materializer_source_bytes()),
    }
    destination_bytes_digest = digest(destination_bytes)
    instruction_digest = digest(instructions.encode("utf-8"))
    configuration_digest = digest(configuration)
    identity_record = {
        "schema_version": MATERIALIZATION_SCHEMA_VERSION,
        "materializer_version": MATERIALIZER_VERSION,
        "source_binding": source_binding,
        "materializer_binding": materializer_binding,
        "candidate_route": route,
        "parent_controls": controls,
        "destination_bytes_digest": destination_bytes_digest,
        "instruction_digest": instruction_digest,
        "configuration_digest": configuration_digest,
        "byte_count": len(destination_bytes),
    }

    return AgentMaterialization(
        materialization_id=digest(canonical_bytes(identity_record) + b"\n"),
        materializer_version=MATERIALIZER_VERSION,
        source_binding=source_binding,
        materializer_binding=materializer_binding,
        candidate_route=route,
        parent_controls=controls,
        destination_bytes=destination_bytes,
        destination_bytes_digest=destination_bytes_digest,
        instruction_digest=instruction_digest,
        configuration_digest=configuration_digest,
        byte_count=len(destination_bytes),
    )


def verify_destination_bytes(
    materialization: AgentMaterialization | Mapping[str, Any],
    observed_bytes: bytes,
) -> bool:
    if not isinstance(observed_bytes, bytes):
        return False
    expected_digest = _field(materialization, "destination_bytes_digest")
    if not isinstance(expected_digest, str) or digest(observed_bytes) != expected_digest:
        return False
    expected_bytes = _field(materialization, "destination_bytes")
    if isinstance(expected_bytes, bytes) and observed_bytes != expected_bytes:
        return False
    return True


def _field(materialization: AgentMaterialization | Mapping[str, Any], key: str) -> Any:
    if isinstance(materialization, Mapping):
        return materialization.get(key)
    return getattr(materialization, key, None)


def _safe_source_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentMaterializationError(
            "source_relative_path must be a non-empty repository-relative path"
        )
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise AgentMaterializationError(
            "source_relative_path must be a safe repository-relative path"
        )
    return path.as_posix()


def _decode_utf8(value: bytes) -> str:
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AgentMaterializationError("source_bytes must be valid UTF-8") from exc


def _parse_toml(value: str) -> dict[str, Any]:
    try:
        policy = tomllib.loads(value)
    except tomllib.TOMLDecodeError as exc:
        raise AgentMaterializationError("source_bytes must be valid TOML") from exc
    if not isinstance(policy, dict):
        raise AgentMaterializationError("source policy must parse to a TOML table")
    return policy


def _need_string(policy: Mapping[str, Any], key: str) -> str:
    value = policy.get(key)
    if not isinstance(value, str) or not value:
        raise AgentMaterializationError(f"source policy requires non-empty {key}")
    return value


def _route_from_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "agent_name": _need_string(policy, "name"),
        "model": _need_string(policy, "model"),
        "model_reasoning_effort": policy.get("model_reasoning_effort"),
    }


def _parent_controls_from_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    return {"sandbox_mode": _need_string(policy, "sandbox_mode")}


def _validated_mapping(
    provided: Mapping[str, Any] | None,
    expected: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    if provided is None:
        return dict(expected)
    normalized = dict(provided)
    if normalized != expected:
        raise AgentMaterializationError(f"{label} does not match source policy")
    return normalized


def _materializer_source_bytes() -> bytes:
    try:
        return Path(__file__).read_bytes()
    except OSError as exc:
        raise AgentMaterializationError("materializer source digest could not be computed") from exc
