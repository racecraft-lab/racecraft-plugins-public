#!/usr/bin/env python3
"""Reference simulator for route availability, fallback, and recovery resolution.

The three committed schema documents under
``tests/speckit-pro/layer6-efficiency/contracts-claude/`` — ``route-policy``,
``environment-snapshot-projection``, and ``route-resolution-report`` — are the
single source of truth. This module drives its closed vocabularies *from* the
resolution-report document rather than restating them: that document's
``$defs/resolutionDiagnostic/properties/code/enum`` is the one declaration site
for the five route-resolution codes, and nothing else may restate those members
(FR-016, FR-017a). Parsing the committed contract once at import is the shape
``claude_policy_controls.py`` already uses for its own frozen registry schema.

Resolution is a **pure function** of its arguments: no filesystem, network,
wall-clock, or randomness input reaches ``resolve``, which is what makes replay
byte-identical (FR-001, FR-014).

This is the **single** module for this capability across both slices (FR-033d).
Structural policy validation is not a second module — it is a second rule family
inside the one resolution walk, and ``fallback_loop`` detection needs the walk
state this module already owns.

Two evaluation orders live here, orthogonal and both structural rather than
documented in a comment a later edit can reorder. The *intra-diagnostic* order
picks the single ``details.sub_reason`` a ``preferred_model_unavailable`` entry
carries; the *inter-diagnostic* order sequences whole entries. Each is a staged
call graph of private helpers called in declaration order, mirroring
``claude_control_comparison.py``'s stated rationale for the same technique.

Every entrypoint is fail-closed: it raises on the first violation and never
returns a partial verdict. Standard library only — no third-party ``jsonschema``.
"""

from __future__ import annotations

from typing import Any

# Read-only imports of the shared fail-closed schema engine. ``load_contract``
# parses the committed contract this module reads its vocabularies from;
# ``CONTRACT_ROOT`` locates it without re-deriving a second path;
# ``validate_instance`` and ``ControlContractError`` are the engine surface the
# corpus loader and the resolution walk consult, so no second validator is
# authored here (FR-016).
from claude_policy_controls import (  # noqa: F401
    CONTRACT_ROOT,
    ControlContractError,
    load_contract,
    validate_instance,
)

# Read-only import of the one canonical serializer for the whole program
# (FR-014a): ``sort_keys=True``, ``separators=(",", ":")``, ``ensure_ascii=False``,
# ``allow_nan=False``, and no trailing newline. A local copy here would be a
# second serializer, and the pinning comparison would then cancel a real
# discrepancy rather than fail on it.
from claude_successor_freeze import canonical_json


REPORT_SCHEMA_PATH = CONTRACT_ROOT / "route-resolution-report.schema.json"
POLICY_SCHEMA_PATH = CONTRACT_ROOT / "route-policy.schema.json"
SNAPSHOT_SCHEMA_PATH = CONTRACT_ROOT / "environment-snapshot-projection.schema.json"

# The committed contract is the single source of truth, parsed once.
REPORT_SCHEMA: dict[str, Any] = load_contract(REPORT_SCHEMA_PATH)

_RESOLUTION_DIAGNOSTIC: dict[str, Any] = REPORT_SCHEMA["$defs"]["resolutionDiagnostic"]
_POLICY_VIOLATION_DIAGNOSTIC: dict[str, Any] = REPORT_SCHEMA["$defs"]["policyViolationDiagnostic"]

# FR-005: the five route-resolution codes, read live rather than transcribed. The
# schema pointer is the declaration site; a literal here would be a second one and
# would absorb the drift the read-live discipline exists to catch.
RESOLUTION_CODES: tuple[str, ...] = tuple(_RESOLUTION_DIAGNOSTIC["properties"]["code"]["enum"])

# FR-019: the five policy-violation codes, read live from the same document. They
# are declared in slice 1 even though no slice-1 case can emit one.
POLICY_VIOLATION_CODES: tuple[str, ...] = tuple(
    _POLICY_VIOLATION_DIAGNOSTIC["properties"]["code"]["enum"]
)

# FR-006: the closed four-member sub-reason vocabulary in its evaluation order.
# The first three partition the state of ``alias_bindings`` against
# ``available_models`` and cannot co-occur; ``platform_route_changed`` reads a
# separate snapshot field and *can* co-occur with any of them, so it is disjoint
# only because it is evaluated last. This constant records the order; the staged
# private helpers are what make it a call-graph property.
SUB_REASON_ORDER: tuple[str, ...] = tuple(
    _RESOLUTION_DIAGNOSTIC["properties"]["details"]["properties"]["sub_reason"]["enum"]
)


class RouteFallbackError(AssertionError):
    """Raised when an input or a produced report violates the CAR-005 contract."""


def _require(condition: object, message: str) -> None:
    """Fail closed: raise on the first violation rather than return a partial verdict."""
    if not condition:
        raise RouteFallbackError(message)


def serialize_report(report: Any) -> str:
    """The one canonical serialization of a resolution report.

    Delegates to the shared ``canonical_json`` so key order, whitespace, and
    non-ASCII handling are pinned by a single named in-tree function rather than
    by a restated convention (FR-014a). No trailing newline is appended, and the
    reports this module produces carry no floating-point value — the only numeric
    fields are the integer budget caps and counts — so neither dimension is left
    to a serializer default.
    """
    return canonical_json(report)
