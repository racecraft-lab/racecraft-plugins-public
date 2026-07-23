#!/usr/bin/env python3
"""Standard-library validator for the CAR-002 Claude trace/telemetry contract.

The shipped JSON Schema at ``docs/ai/research/claude-trace-contract.schema.json``
is the single source of truth. This module loads it **once** at import and drives
every check *from* it — required keys, ``additionalProperties: false``, ``const`` /
``enum``, the ``$ref``-shared ID patterns, the ``sha256`` pattern, and the
``format: date-time`` UTC-timestamp rule. Nothing about the contract is hardcoded
here; re-authoring the schema re-drives the validator.

One fail-closed entrypoint is published per record ``$def``:

* ``validate_runtime_capability_snapshot``
* ``validate_telemetry_profile``
* ``validate_route_resolution``
* ``validate_exact_treatment_replay``

Each raises :class:`ClaudeTraceContractError` on the first violation (mirrors the
CAR-001 ``validate_manifest`` fail-closed idiom and reuses its
``require_utc_timestamp`` / ``schema_keys`` naming). Standard library only — no
third-party ``jsonschema``.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = REPO_ROOT / "docs" / "ai" / "research" / "claude-trace-contract.schema.json"

# The four record contracts this module publishes an entrypoint for.
RECORD_DEFS = (
    "runtimeCapabilitySnapshot",
    "telemetryProfile",
    "routeResolution",
    "exactTreatmentReplay",
)


class ClaudeTraceContractError(AssertionError):
    """Raised when an instance violates the shipped CAR-002 trace contract."""


def _load_schema() -> dict[str, Any]:
    try:
        return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover - shipped artifact must exist
        raise ClaudeTraceContractError(f"shipped schema not found: {SCHEMA_PATH}") from exc


# Single source of truth: parsed exactly once at import.
SCHEMA: dict[str, Any] = _load_schema()
_DEFS: dict[str, Any] = SCHEMA["$defs"]
_PATTERN_CACHE: dict[str, re.Pattern[str]] = {}
_REF_PREFIX = "#/$defs/"


def schema_keys(definition: str) -> set[str]:
    """Declared property set for a ``$def`` (mirrors the CAR-001 ``schema_keys``)."""
    return set(_DEFS[definition]["properties"])


def _compiled(pattern: str) -> re.Pattern[str]:
    cached = _PATTERN_CACHE.get(pattern)
    if cached is None:
        cached = re.compile(pattern)
        _PATTERN_CACHE[pattern] = cached
    return cached


def _matches_type(instance: Any, type_name: str, path: str) -> bool:
    # ``bool`` is a subclass of ``int``; keep the two disjoint so a boolean never
    # satisfies an ``integer`` field and vice versa (fail-closed).
    if type_name == "null":
        return instance is None
    if type_name == "boolean":
        return isinstance(instance, bool)
    if type_name == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if type_name == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if type_name == "string":
        return isinstance(instance, str)
    if type_name == "object":
        return isinstance(instance, dict)
    if type_name == "array":
        return isinstance(instance, list)
    raise ClaudeTraceContractError(f"{path}: schema declares unknown type {type_name!r}")


def require_utc_timestamp(value: Any, context: str) -> None:
    """UTC-timestamp rule reused verbatim from the CAR-001 validator idiom.

    Applied wherever the schema declares ``format: date-time``: the value must be
    a ``Z``-suffixed, parseable, zero-offset UTC instant.
    """
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ClaudeTraceContractError(f"{context}: expected UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ClaudeTraceContractError(f"{context}: invalid timestamp") from exc
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ClaudeTraceContractError(f"{context}: timestamp is not UTC")


def _resolve_ref(ref: str, path: str) -> dict[str, Any]:
    if not ref.startswith(_REF_PREFIX):
        raise ClaudeTraceContractError(f"{path}: unsupported $ref {ref!r}")
    name = ref[len(_REF_PREFIX):]
    try:
        return _DEFS[name]
    except KeyError as exc:
        raise ClaudeTraceContractError(f"{path}: unknown $def {name!r}") from exc


def _validate_object(instance: dict[str, Any], node: dict[str, Any], path: str) -> None:
    props = node.get("properties", {})
    required = set(node.get("required", ()))
    actual = set(instance)
    missing = required - actual
    if missing:
        raise ClaudeTraceContractError(f"{path}: missing required keys {sorted(missing)}")
    if node.get("additionalProperties") is False:
        extra = actual - set(props)
        if extra:
            raise ClaudeTraceContractError(f"{path}: unexpected keys {sorted(extra)}")
    for key, subschema in props.items():
        if key in instance:
            child = f"{path}.{key}" if path else key
            _validate(instance[key], subschema, child)


def _validate(instance: Any, node: dict[str, Any], path: str) -> None:
    """Recursively validate ``instance`` against a schema ``node`` (fail-closed)."""
    if "$ref" in node:
        _validate(instance, _resolve_ref(node["$ref"], path), path)
        return
    if "anyOf" in node:
        failures: list[str] = []
        for index, branch in enumerate(node["anyOf"]):
            try:
                _validate(instance, branch, path)
                return
            except ClaudeTraceContractError as exc:
                failures.append(f"[{index}] {exc}")
        raise ClaudeTraceContractError(
            f"{path}: no anyOf branch matched ({'; '.join(failures)})"
        )
    if "const" in node:
        if instance != node["const"]:
            raise ClaudeTraceContractError(
                f"{path}: expected const {node['const']!r}, got {instance!r}"
            )
        return
    if "enum" in node:
        if instance not in node["enum"]:
            raise ClaudeTraceContractError(
                f"{path}: {instance!r} not in enum {node['enum']}"
            )
        return

    if "type" in node:
        type_spec = node["type"]
        types = type_spec if isinstance(type_spec, list) else [type_spec]
        if not any(_matches_type(instance, name, path) for name in types):
            got = "null" if instance is None else type(instance).__name__
            raise ClaudeTraceContractError(f"{path}: expected type {type_spec}, got {got}")

    # Type-specific constraints apply only to the matching runtime type, matching
    # JSON Schema keyword semantics.
    if isinstance(instance, str):
        min_length = node.get("minLength")
        if min_length is not None and len(instance) < min_length:
            raise ClaudeTraceContractError(f"{path}: shorter than minLength {min_length}")
        pattern = node.get("pattern")
        if pattern is not None and not _compiled(pattern).fullmatch(instance):
            raise ClaudeTraceContractError(
                f"{path}: {instance!r} does not match pattern {pattern}"
            )
        if node.get("format") == "date-time":
            require_utc_timestamp(instance, path)
    elif isinstance(instance, list):
        min_items = node.get("minItems")
        if min_items is not None and len(instance) < min_items:
            raise ClaudeTraceContractError(f"{path}: fewer than minItems {min_items}")
        items = node.get("items")
        if items is not None:
            for index, element in enumerate(instance):
                _validate(element, items, f"{path}[{index}]")
    elif isinstance(instance, dict):
        if "properties" in node or "required" in node or node.get("additionalProperties") is False:
            _validate_object(instance, node, path)


def _validate_against_def(definition: str, record: Any) -> Any:
    if definition not in _DEFS:
        raise ClaudeTraceContractError(f"schema is missing $def {definition!r}")
    _validate(record, {"$ref": f"{_REF_PREFIX}{definition}"}, definition)
    return record


def validate_runtime_capability_snapshot(record: Any) -> Any:
    """Validate a ``runtimeCapabilitySnapshot`` instance; raise on any violation."""
    return _validate_against_def("runtimeCapabilitySnapshot", record)


def validate_telemetry_profile(record: Any) -> Any:
    """Validate a ``telemetryProfile`` instance; raise on any violation."""
    return _validate_against_def("telemetryProfile", record)


def validate_route_resolution(record: Any) -> Any:
    """Validate a ``routeResolution`` instance; raise on any violation."""
    return _validate_against_def("routeResolution", record)


def validate_exact_treatment_replay(record: Any) -> Any:
    """Validate an ``exactTreatmentReplay`` instance; raise on any violation."""
    return _validate_against_def("exactTreatmentReplay", record)


__all__ = (
    "ClaudeTraceContractError",
    "RECORD_DEFS",
    "SCHEMA",
    "SCHEMA_PATH",
    "schema_keys",
    "require_utc_timestamp",
    "validate_runtime_capability_snapshot",
    "validate_telemetry_profile",
    "validate_route_resolution",
    "validate_exact_treatment_replay",
)
