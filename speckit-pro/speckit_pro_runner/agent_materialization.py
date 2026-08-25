"""Canonical Codex agent policy materialization contract."""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


MATERIALIZATION_SCHEMA_VERSION = "agent-materialization.v1"
MATERIALIZER_VERSION = "agent-materializer.v1"
MATERIALIZER_SOURCE_PATH = "speckit-pro/speckit_pro_runner/agent_materialization.py"
ROUTE_FIELD_NAMES = frozenset({"model", "model_reasoning_effort"})

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
    selected_model: str
    selected_model_reasoning_effort: str
    non_route_fields_digest: str
    non_route_fields_unchanged: bool
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

    expected_controls = _parent_controls_from_policy(policy)
    route = _selected_route_from_policy(policy, candidate_route)
    controls = _validated_mapping(parent_controls, expected_controls, "parent controls")
    if candidate_route is None:
        destination_text = source_text
    else:
        destination_text = _render_selected_route(source_text, policy, route)
    destination_policy = _parse_toml(destination_text)
    _require_unchanged_non_route_fields(policy, destination_policy)
    configuration = {
        key: destination_policy[key]
        for key in sorted(destination_policy)
        if key != "developer_instructions"
    }
    non_route_fields = _non_route_fields(policy)

    destination_bytes = destination_text.encode("utf-8")
    source_binding = {
        "path": source_path,
        "digest": digest(source_bytes),
        "byte_count": len(source_bytes),
    }
    materializer_binding = {
        "path": MATERIALIZER_SOURCE_PATH,
        "digest": digest(_materializer_source_bytes()),
    }
    destination_bytes_digest = digest(destination_bytes)
    instruction_digest = digest(instructions.encode("utf-8"))
    configuration_digest = digest(configuration)
    non_route_fields_digest = digest(non_route_fields)
    identity_record = {
        "schema_version": MATERIALIZATION_SCHEMA_VERSION,
        "materializer_version": MATERIALIZER_VERSION,
        "source_binding": source_binding,
        "materializer_binding": materializer_binding,
        "candidate_route": route,
        "parent_controls": controls,
        "selected_model": route["model"],
        "selected_model_reasoning_effort": route["model_reasoning_effort"],
        "destination_bytes_digest": destination_bytes_digest,
        "instruction_digest": instruction_digest,
        "configuration_digest": configuration_digest,
        "non_route_fields_digest": non_route_fields_digest,
        "non_route_fields_unchanged": True,
        "byte_count": len(destination_bytes),
    }

    return AgentMaterialization(
        materialization_id=digest(canonical_bytes(identity_record) + b"\n"),
        materializer_version=MATERIALIZER_VERSION,
        source_binding=source_binding,
        materializer_binding=materializer_binding,
        candidate_route=route,
        parent_controls=controls,
        selected_model=route["model"],
        selected_model_reasoning_effort=route["model_reasoning_effort"],
        non_route_fields_digest=non_route_fields_digest,
        non_route_fields_unchanged=True,
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
    if "model_reasoning_effort" in policy:
        model_reasoning_effort = _need_string(policy, "model_reasoning_effort")
    else:
        model_reasoning_effort = ""
    return {
        "agent_name": _need_string(policy, "name"),
        "model": _need_string(policy, "model"),
        "model_reasoning_effort": model_reasoning_effort,
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


def _selected_route_from_policy(
    policy: Mapping[str, Any],
    provided: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if provided is None:
        return _route_from_policy(policy)
    if not isinstance(provided, Mapping):
        raise AgentMaterializationError("candidate route must be a mapping")
    expected_agent_name = _need_string(policy, "name")
    agent_name = provided.get("agent_name", expected_agent_name)
    if agent_name != expected_agent_name:
        raise AgentMaterializationError("candidate route does not match source policy")
    return {
        "agent_name": expected_agent_name,
        "model": _need_mapping_string(provided, "model", "candidate route"),
        "model_reasoning_effort": _need_mapping_string(
            provided,
            "model_reasoning_effort",
            "candidate route",
        ),
    }


def _need_mapping_string(mapping: Mapping[str, Any], key: str, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise AgentMaterializationError(f"{label} requires non-empty {key}")
    return value


def _render_selected_route(
    source_text: str,
    source_policy: Mapping[str, Any],
    route: Mapping[str, Any],
) -> str:
    _need_string(source_policy, "model")
    rendered = _replace_top_level_string_field(source_text, "model", route["model"])
    route_effort = route["model_reasoning_effort"]
    if "model_reasoning_effort" in source_policy:
        _need_string(source_policy, "model_reasoning_effort")
        if not route_effort:
            raise AgentMaterializationError(
                "selected route requires non-empty model_reasoning_effort"
            )
        rendered = _replace_top_level_string_field(
            rendered,
            "model_reasoning_effort",
            route_effort,
        )
    elif route_effort:
        rendered, insertion_count = re.subn(
            r"(?m)^(model\s*=.*)$",
            rf'\1\nmodel_reasoning_effort = {json.dumps(route_effort, ensure_ascii=False)}',
            rendered,
            count=1,
        )
        if insertion_count != 1:
            raise AgentMaterializationError(
                "source policy requires one model field for model_reasoning_effort insertion"
            )
    destination_policy = _parse_toml(rendered)
    if destination_policy.get("model") != route["model"]:
        raise AgentMaterializationError("destination model did not render selected route")
    if route_effort and destination_policy.get("model_reasoning_effort") != route_effort:
        raise AgentMaterializationError(
            "destination model_reasoning_effort did not render selected route"
        )
    if not route_effort and "model_reasoning_effort" in destination_policy:
        raise AgentMaterializationError(
            "destination model_reasoning_effort rendered unexpectedly"
        )
    return rendered


def _replace_top_level_string_field(source_text: str, key: str, value: str) -> str:
    replacement = f"{key} = {json.dumps(value, ensure_ascii=False)}"
    rendered, replacement_count = re.subn(
        rf"(?m)^{re.escape(key)}\s*=.*$",
        replacement,
        source_text,
    )
    if replacement_count != 1:
        raise AgentMaterializationError(f"source policy requires exactly one {key} field")
    return rendered


def _non_route_fields(policy: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: policy[key]
        for key in sorted(policy)
        if key not in ROUTE_FIELD_NAMES
    }


def _require_unchanged_non_route_fields(
    source_policy: Mapping[str, Any],
    destination_policy: Mapping[str, Any],
) -> None:
    if _non_route_fields(source_policy) != _non_route_fields(destination_policy):
        raise AgentMaterializationError("destination policy changed non-route fields")


def _materializer_source_bytes() -> bytes:
    try:
        return Path(__file__).read_bytes()
    except OSError as exc:
        raise AgentMaterializationError("materializer source digest could not be computed") from exc
