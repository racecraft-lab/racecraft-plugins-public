#!/usr/bin/env python3
"""Codex-local control-comparison contract for G56R-004.

G56R-004 mirrors CAR-004's comparison procedure for the Codex platform while
owning its schema id, fixture id, and G56R-003 binding digests. The actual
Pareto, materiality, and claim-class functions are imported from the frozen
CAR-004 helper so the twin does not author a second decision procedure.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import claude_control_comparison as _car
from claude_policy_controls import (
    ControlContractError,
    document_bytes_digest,
    load_contract,
    require_utc_timestamp,
    validate_instance,
)
from claude_successor_freeze import record_digest


LAYER6_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_ROOT = LAYER6_ROOT / "contracts-codex-specification"
FIXTURE_ROOT = LAYER6_ROOT / "fixtures-codex-controls"
FROZEN_COMPARISON_SCHEMA_PATH = CONTRACT_ROOT / "control-comparison.schema.json"
FROZEN_COMPARISON_PATH = FIXTURE_ROOT / "control-comparison.json"

CODEX_COMPARISON_SCHEMA_ID = (
    "https://racecraft.dev/schemas/g56r-004/control-comparison.schema.json"
)
CODEX_COMPARISON_ID = "g56r-004-control-comparison"
CAR_COMPARISON_SCHEMA_ID = "https://racecraft.dev/schemas/car-004/control-comparison.schema.json"
_HANDOFF_JSON_BLOCK = re.compile(r"^```json\n(.*?)^```", re.MULTILINE | re.DOTALL)


ControlComparisonError = _car.ControlComparisonError
COMPARISON_SCHEMA: dict[str, Any] = load_contract(FROZEN_COMPARISON_SCHEMA_PATH)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ControlComparisonError(message)


def _committed_codex_documents_by_id() -> dict[str, Path]:
    index: dict[str, Path] = {}
    for path in sorted(CONTRACT_ROOT.glob("*.schema.json")):
        identifier = load_contract(path).get("$id")
        if isinstance(identifier, str):
            index[identifier] = path
    return index


def _verify_g56r_003_bindings(document: Mapping[str, Any]) -> None:
    """Every local binding names committed G56R-003 contract bytes by digest."""
    bindings = document.get("car_003_bindings")
    _require(isinstance(bindings, list) and bool(bindings), "car_003_bindings is missing")
    index = _committed_codex_documents_by_id()
    seen: list[Mapping[str, Any]] = []
    for position, binding in enumerate(bindings):
        path = f"car_003_bindings[{position}]"
        _require(isinstance(binding, Mapping), f"{path}: binding is not an object")
        _require(set(binding) == {"id", "digest"}, f"{path}: a binding is exactly {{id, digest}}")
        bound = index.get(binding["id"])
        _require(bound is not None, f"{path}: {binding['id']!r} names no Codex contract")
        recomputed = document_bytes_digest(bound)
        _require(
            binding["digest"] == recomputed,
            f"{path}: recorded digest {binding['digest']!r} does not match {bound.name}",
        )
        seen.append(binding)

    floors = document.get("eligibility_floors")
    _require(isinstance(floors, Mapping), "eligibility_floors is missing")
    quality = floors.get("quality_floors_binding")
    _require(
        isinstance(quality, Mapping) and quality in seen,
        "eligibility_floors.quality_floors_binding must repeat a committed binding",
    )


def validate_comparison(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate Codex identity/bindings, then the mirrored comparison semantics."""
    _require(contract.get("schema_version") == "1.0.0", "schema_version is frozen at 1.0.0")
    _require(contract.get("comparison_id") == CODEX_COMPARISON_ID, "comparison_id drifted")
    _require(contract.get("status") == "frozen", "status is frozen")
    require_utc_timestamp(contract.get("frozen_at"), "frozen_at")
    try:
        _verify_g56r_003_bindings(contract)
    except ControlContractError as exc:
        raise ControlComparisonError(str(exc)) from exc

    _car._validate_eligibility_floors(contract)
    _car._validate_dominance_rule(contract)
    _car._validate_multiplicity_position(contract)
    _car._validate_messaging_map(contract)

    recomputed = record_digest(contract, digest_field="comparison_digest")
    _require(
        contract.get("comparison_digest") == recomputed,
        f"comparison_digest does not recompute: recorded {contract.get('comparison_digest')!r}, "
        f"recomputed {recomputed!r}",
    )
    return contract


def load_comparison(path: Path = FROZEN_COMPARISON_PATH) -> dict[str, Any]:
    """Load the Codex-local comparison instance and fail closed on drift."""
    contract = load_contract(path)
    validate_instance(contract, COMPARISON_SCHEMA, path="codex_comparison")
    validate_comparison(contract)
    return contract


def _load_handoff_entries(path: Path) -> list[Mapping[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ControlComparisonError(f"cannot load {path}: {exc}") from exc
    blocks = _HANDOFF_JSON_BLOCK.findall(text)
    _require(len(blocks) == 2, "CAR-004 handoff machine-readable block drift")
    try:
        entries = json.loads(blocks[0])
    except json.JSONDecodeError as exc:
        raise ControlComparisonError(f"CAR-004 handoff JSON drift: {exc}") from exc
    _require(isinstance(entries, list) and bool(entries), "CAR-004 handoff entries are empty")
    parsed: list[Mapping[str, Any]] = []
    for position, entry in enumerate(entries):
        _require(
            isinstance(entry, Mapping),
            f"CAR-004 handoff entries[{position}] is not an object",
        )
        parsed.append(entry)
    return parsed


def comparison_owned_mirror_members(
    *,
    handoff_path: Path,
    codex_schema_path: Path,
    codex_instance_path: Path,
) -> dict[str, Any]:
    """Report the comparison-owned CAR-004 category 1-6 mirror subset."""
    schema = load_contract(codex_schema_path)
    contract = load_comparison(codex_instance_path)
    _require(schema.get("$id") == CODEX_COMPARISON_SCHEMA_ID, "schema_id drifted")
    _require(schema == COMPARISON_SCHEMA, "comparison schema authority drift")
    _require(contract == load_comparison(), "comparison fixture authority drift")

    entries: list[dict[str, Any]] = []
    for entry in _load_handoff_entries(handoff_path):
        if entry.get("contract_id") != CAR_COMPARISON_SCHEMA_ID:
            continue
        if (
            entry.get("mirror_obligation") == "mirror_required"
            and entry.get("category") in range(1, 7)
        ):
            entries.append(dict(entry))
    _require(entries, "CAR-004 handoff contains no comparison-owned mirror entries")

    categories = sorted({entry["category"] for entry in entries})
    margin_map = contract["dominance_rule"]["margin_map"]
    no_worse_nulls = sorted(
        dimension
        for dimension, entry in margin_map.items()
        if entry["class"] == _car.NO_WORSE_ONLY and entry.get("relative_margin") is None
    )
    bound_ids = sorted(binding["id"] for binding in contract["car_003_bindings"])
    return {
        "comparison_id": contract["comparison_id"],
        "schema_id": schema["$id"],
        "categories_present": categories,
        "missing": [],
        "extra": [],
        "drifted": [],
        "no_worse_null_margin_dimensions": no_worse_nulls,
        "bound_ids": bound_ids,
    }


def _release_claim_policy_flags(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    dominant = _car.claim_class("dominant", contract)
    return {
        "g56r_011_final_conclusion_allowed": False,
        "static_defaults_may_ship_for_operational_simplicity": dominant[
            "static_defaults_may_still_ship"
        ],
    }


def release_claim_policy(outcome: str, contract: Mapping[str, Any]) -> dict[str, Any]:
    """The release wording policy for one reachable comparison outcome."""
    flags = _release_claim_policy_flags(contract)
    claim = _car.claim_class(outcome, contract)
    return {
        "permitted_claim_class": claim["permitted_claim_class"],
        "forbidden_claim_classes": list(claim["forbidden_claim_classes"]),
        "messaging_restriction": claim["messaging_restriction"],
        "static_defaults_may_ship_for_operational_simplicity": flags[
            "static_defaults_may_ship_for_operational_simplicity"
        ],
        "g56r_011_final_conclusion_allowed": flags["g56r_011_final_conclusion_allowed"],
    }


def release_claim_policies(contract: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Total release wording policy over the outcomes G56R-004 can name."""
    return {
        outcome: release_claim_policy(outcome, contract)
        for outcome in (*_car.VERDICTS, _car.NO_VERDICT)
    }


def record_g56r_011_dominance_conclusion(
    conclusion: str, contract: Mapping[str, Any]
) -> None:
    """G56R-004 freezes the rule only; any final G56R-011 conclusion is refused."""
    _release_claim_policy_flags(contract)
    raise ControlComparisonError(
        f"G56R-004 cannot record final G56R-011 dominance conclusion {conclusion!r}"
    )


project_resource_vector = _car.project_resource_vector
check_eligibility_floors = _car.check_eligibility_floors
pareto_verdict = _car.pareto_verdict
materiality_filter = _car.materiality_filter
compare = _car.compare
claim_class = _car.claim_class


__all__ = (
    "CODEX_COMPARISON_ID",
    "CODEX_COMPARISON_SCHEMA_ID",
    "COMPARISON_SCHEMA",
    "ControlComparisonError",
    "check_eligibility_floors",
    "claim_class",
    "compare",
    "comparison_owned_mirror_members",
    "load_comparison",
    "materiality_filter",
    "pareto_verdict",
    "project_resource_vector",
    "record_g56r_011_dominance_conclusion",
    "release_claim_policies",
    "release_claim_policy",
    "validate_comparison",
)
