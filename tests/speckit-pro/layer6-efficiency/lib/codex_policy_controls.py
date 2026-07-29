"""Codex-local policy-control validation for G56R-004.

The module starts with the registry-owned CAR-004 mirror subset. Later tasks
extend the same fail-closed surface with comparison, partition, replay, and
reconciliation behavior as those artifacts become available.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


class ControlContractError(ValueError):
    """Raised when a Codex policy-control artifact drifts from its authority."""


_CAR_SCHEMA_ID = "https://racecraft.dev/schemas/car-004/policy-control-registry.schema.json"
_CODEX_SCHEMA_ID = "https://racecraft.dev/schemas/g56r-004/policy-control-registry.schema.json"
_CAR_REGISTRY_ID = "car-004-policy-control-registry"
_CODEX_REGISTRY_ID = "g56r-004-policy-control-registry"
_CONTROL_ID_MAP = {
    "g56r-004-unpinned-control": "car-004-unpinned-control",
    "g56r-004-adaptive-control": "car-004-adaptive-control",
    "g56r-004-justified-high-effort-control": "car-004-orchestration-changing-control",
}
_SANCTIONED_DIVERGENCE = {
    "category": 3,
    "car_value": "orchestration_changing",
    "codex_value": "justified_high_effort",
    "unchanged_values": ["adaptive", "unpinned"],
}


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ControlContractError(f"cannot load {path}: {exc}") from exc


def _record_digest(record: dict[str, Any], digest_field: str) -> str:
    preimage = copy.deepcopy(record)
    preimage.pop(digest_field, None)
    encoded = json.dumps(
        preimage,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _normalize_platform_value(value: Any) -> Any:
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, member in value.items():
            normalized_key = (
                "orchestration_changing" if key == "justified_high_effort" else key
            )
            if (
                key in {"registry_digest", "control_digest"}
                and isinstance(member, str)
                and member.startswith("sha256:")
            ):
                normalized[normalized_key] = "<content-address>"
            else:
                normalized[normalized_key] = _normalize_platform_value(member)
        return normalized
    if isinstance(value, list):
        return [_normalize_platform_value(member) for member in value]
    if value == _CODEX_SCHEMA_ID:
        return _CAR_SCHEMA_ID
    if value == "G56R-004 Policy Control Registry":
        return "CAR-004 Policy Control Registry"
    if value == _CODEX_REGISTRY_ID:
        return _CAR_REGISTRY_ID
    if value in _CONTROL_ID_MAP:
        return _CONTROL_ID_MAP[value]
    if value == "justified_high_effort":
        return "orchestration_changing"
    return value


def _assert_content_addresses(registry: dict[str, Any]) -> None:
    controls = registry.get("controls")
    if not isinstance(controls, list) or len(controls) != 3:
        raise ControlContractError("the Codex registry must carry exactly three controls")
    kinds = [control.get("control_kind") for control in controls]
    if len(set(kinds)) != len(kinds):
        raise ControlContractError("the Codex registry repeats a control_kind")
    expected_kinds = {"unpinned", "adaptive", "justified_high_effort"}
    if set(kinds) != expected_kinds:
        raise ControlContractError(
            f"unexpected Codex control_kind set: {sorted(str(kind) for kind in kinds)}"
        )
    for control in controls:
        expected = _record_digest(control, "control_digest")
        if control.get("control_digest") != expected:
            raise ControlContractError(
                f"control digest drift for {control.get('control_id')}"
            )
    expected_registry = _record_digest(registry, "registry_digest")
    if registry.get("registry_digest") != expected_registry:
        raise ControlContractError("registry digest drift")


def validate_car_004_twin_mirror(
    *,
    car_handoff_path: Path,
    codex_registry_schema_path: Path,
    codex_registry_instance_path: Path,
) -> dict[str, Any]:
    """Validate the registry-owned category 1-6 mirror subset bidirectionally."""

    try:
        handoff = car_handoff_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ControlContractError(f"cannot load {car_handoff_path}: {exc}") from exc
    for category in range(1, 7):
        if f'"category": {category}' not in handoff:
            raise ControlContractError(f"CAR-004 handoff omits category {category}")
    if (
        '"mirror_obligation": "sanctioned_divergence"' not in handoff
        or '"members": ["unpinned", "adaptive", "orchestration_changing"]'
        not in handoff
        or '"status": "closed_nothing_owed"' not in handoff
    ):
        raise ControlContractError("CAR-004 handoff omits the sanctioned divergence")

    layer6_root = codex_registry_schema_path.parent.parent
    car_schema_path = (
        layer6_root / "contracts-claude" / "policy-control-registry.schema.json"
    )
    car_registry_path = (
        layer6_root / "fixtures-controls" / "policy-control-registry.json"
    )
    car_schema = _load_json(car_schema_path)
    codex_schema = _load_json(codex_registry_schema_path)
    car_registry = _load_json(car_registry_path)
    codex_registry = _load_json(codex_registry_instance_path)

    _assert_content_addresses(codex_registry)
    if _normalize_platform_value(codex_schema) != car_schema:
        raise ControlContractError(
            "Codex registry schema has drift beyond the sanctioned platform values"
        )
    if _normalize_platform_value(codex_registry) != _normalize_platform_value(
        car_registry
    ):
        raise ControlContractError(
            "Codex registry fixture has drift beyond the sanctioned platform values"
        )

    smoke_bounds = codex_registry["smoke_bounds"]
    control_kind_enum = codex_schema["$defs"]["control"]["properties"]["control_kind"][
        "enum"
    ]
    return {
        "compared_categories": [1, 2, 3, 4, 5, 6],
        "differences": {
            "missing_from_record": [],
            "absent_from_artifacts": [],
            "mismatched": [],
            "duplicated": [],
        },
        "sanctioned_divergences": [copy.deepcopy(_SANCTIONED_DIVERGENCE)],
        "preserved_literals": {
            "zeros": {
                "max_confirmation_entries": smoke_bounds["max_confirmation_entries"][
                    "value"
                ]
            },
            "units": {
                "raw_token_ceiling": smoke_bounds["raw_token_ceiling"]["unit"]
            },
            "enums": {"control_kind": list(control_kind_enum)},
            "numerics": {
                "raw_token_ceiling": smoke_bounds["raw_token_ceiling"]["value"]
            },
        },
    }
