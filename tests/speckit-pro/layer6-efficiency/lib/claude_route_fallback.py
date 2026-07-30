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

import json
from pathlib import Path
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

# The pinned corpus sits beside the contracts it validates against, reached from
# CONTRACT_ROOT rather than by re-deriving a second path to the same tree.
FIXTURE_ROOT = CONTRACT_ROOT.parent / "fixtures-fallback"
DEFAULT_CORPUS_PATH = FIXTURE_ROOT / "fallback-scenario-corpus.json"

SCHEMA_VERSION = "1.0.0"
CORPUS_FIXTURE_KIND = "route_fallback_replay"

# FR-015 and FR-015a: the members every case carries. ``overrides`` is listed here
# because a case that declares none must carry an explicit null rather than omit the
# key — the corpus has no schema of its own, so presence is the only way to tell a
# declared-empty case from a malformed one.
CASE_MEMBERS: tuple[str, ...] = (
    "case_id",
    "purpose",
    "proves",
    "requirements",
    "policy",
    "snapshot",
    "overrides",
    "expected_report",
)

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


# FR-012c: the one literal every diagnostic this module emits carries, read live from
# the schema's own ``const`` rather than transcribed.
DIAGNOSTIC_SOURCE: str = _RESOLUTION_DIAGNOSTIC["properties"]["source"]["const"]

# FR-012a: the closed remediation-action vocabulary, read live from its single
# declaration site. Reading it is what lets the tables below be checked against it at
# import instead of trusting that a verbatim string was copied without a typo — the
# rollback member in particular is required verbatim by FR-029.
REMEDIATION_ACTIONS: tuple[str, ...] = tuple(
    REPORT_SCHEMA["$defs"]["remediation"]["properties"]["actions"]["items"]["enum"]
)

SEVERITY_VALUES: tuple[str, ...] = tuple(_RESOLUTION_DIAGNOSTIC["properties"]["severity"]["enum"])

# FR-026: the three declared caps a report echoes, read live from the contract so the
# projection cannot drift from the member set the schema closes ``declared`` to.
DECLARED_BUDGET_MEMBERS: tuple[str, ...] = tuple(
    REPORT_SCHEMA["$defs"]["reportedBudgets"]["properties"]["declared"]["required"]
)

# FR-012c: severity is a function of ``code``, not of the occurrence. The table is the
# one recorded in data-model.md section 3 and covers both closed enums, so the
# completeness check below is a real check rather than a check of half a table.
DIAGNOSTIC_SEVERITY: dict[str, str] = {
    "preferred_model_unavailable": "warning",
    "effort_unsupported": "warning",
    "capability_probe_unavailable": "warning",
    "treatment_probe_failed": "warning",
    "no_safe_route": "error",
    "fallback_loop": "error",
    "unqualified_adjacent_model": "error",
    "generic_agent_substitution": "error",
    "silent_inherit_materialization": "error",
    "unqualified_override": "warning",
}

# FR-012a: one apt action per code, from the same recorded table. ``no_safe_route`` is
# the only code carrying both a forward remedy and the mandated rollback, so the
# rollback never repeats on a per-route entry and no code approaches the cap of three.
DIAGNOSTIC_ACTIONS: dict[str, tuple[str, ...]] = {
    "preferred_model_unavailable": (
        "Re-probe the environment and confirm the pinned alias and resolved model.",
    ),
    "effort_unsupported": ("Declare an effort the model's probed capability set supports.",),
    "capability_probe_unavailable": ("Re-run capability probing before trusting this route.",),
    "treatment_probe_failed": ("Inspect the exact-invocation probe evidence for this route.",),
    "no_safe_route": (
        "Widen the declared fallback list with qualified routes.",
        "Roll back to the previous plugin release.",
    ),
    "fallback_loop": ("Remove the repeated route from the fallback chain.",),
    "unqualified_adjacent_model": ("Replace the adjacent model with a qualified route.",),
    "generic_agent_substitution": ("Restore the named agent in the fallback route.",),
    "silent_inherit_materialization": ("Declare the model and effort explicitly on the route.",),
    "unqualified_override": (
        "Unset the unqualified subagent-model override before making release claims.",
    ),
}


class RouteFallbackError(AssertionError):
    """Raised when an input or a produced report violates the CAR-005 contract."""


def _require(condition: object, message: str) -> None:
    """Fail closed: raise on the first violation rather than return a partial verdict."""
    if not condition:
        raise RouteFallbackError(message)


# Import-time grounding of the two tables against the committed contract. Each check
# fails closed on a class of authoring mistake a runtime assertion would find only if
# the affected code happened to be emitted: a code missing from a table, a severity
# outside the closed set, or an action string that is one character off the verbatim
# member the schema declares.
_ALL_CODES = frozenset(RESOLUTION_CODES) | frozenset(POLICY_VIOLATION_CODES)
_require(
    frozenset(DIAGNOSTIC_SEVERITY) == _ALL_CODES,
    "the severity table does not cover exactly the two closed code vocabularies",
)
_require(
    frozenset(DIAGNOSTIC_ACTIONS) == _ALL_CODES,
    "the action table does not cover exactly the two closed code vocabularies",
)
_require(
    all(value in SEVERITY_VALUES for value in DIAGNOSTIC_SEVERITY.values()),
    "the severity table names a value outside the contract's closed severity set",
)
_require(
    all(
        action in REMEDIATION_ACTIONS
        for actions in DIAGNOSTIC_ACTIONS.values()
        for action in actions
    ),
    "the action table names a string outside the contract's closed action vocabulary",
)


def _diagnostic(
    code: str, message: str, summary: str, *, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    """One diagnostic entry in the installed runner's envelope shape (FR-012).

    ``severity``, ``source``, and ``actions`` are looked up rather than passed, so no
    caller can vary them per occurrence; ``details`` is omitted rather than emitted
    empty, mirroring the runner.
    """
    entry: dict[str, Any] = {
        "code": code,
        "message": message,
        "severity": DIAGNOSTIC_SEVERITY[code],
        "source": DIAGNOSTIC_SOURCE,
        "remediation": {"summary": summary, "actions": list(DIAGNOSTIC_ACTIONS[code])},
    }
    if details is not None:
        entry["details"] = details
    return entry


# --------------------------------------------------------------------------- #
# FR-006: the intra-diagnostic staged call graph over the sub-reason vocabulary #
# --------------------------------------------------------------------------- #
# Each helper below returns the ``details`` payload its own sub-reason carries, or
# None when its predicate misses. They are called in the order SUB_REASON_STAGES
# declares, which an import-time check holds equal to the schema's own enum order —
# so the evaluation order is a call-graph property, not a comment a later edit can
# reorder by moving a line.


def _sub_reason_alias_unresolved(
    route: dict[str, Any], snapshot: dict[str, Any]
) -> dict[str, Any] | None:
    """The pinned alias has no binding at all. No model was ever resolved, so the
    payload names none — which is why this is a member rather than a fold into
    ``model_absent``, whose payload must name a missing model ID."""
    if route["alias"] in snapshot["alias_bindings"]:
        return None
    return {
        "alias": route["alias"],
        "route_id": route["route_id"],
        "sub_reason": "alias_unresolved",
    }


def _sub_reason_alias_repointed(
    route: dict[str, Any], snapshot: dict[str, Any]
) -> dict[str, Any] | None:
    """The alias is bound, but to a model other than the one the route pins. The
    sub-reason is deliberately cause-agnostic: version drift, per-family redefinition,
    and allowlist substitution all present identically as a moved binding."""
    observed = snapshot["alias_bindings"].get(route["alias"])
    if observed is None or observed == route["resolved_model"]:
        return None
    return {
        "alias": route["alias"],
        "observed_resolved_model": observed,
        "pinned_resolved_model": route["resolved_model"],
        "route_id": route["route_id"],
        "sub_reason": "alias_repointed",
    }


def _sub_reason_model_absent(
    route: dict[str, Any], snapshot: dict[str, Any]
) -> dict[str, Any] | None:
    """The alias binds exactly as pinned, but the pinned model is not offered. The
    binding precondition holds by construction: reaching this stage means both prior
    predicates missed, which is only possible when the alias binds to the pinned ID."""
    if route["resolved_model"] in snapshot["available_models"]:
        return None
    return {
        "alias": route["alias"],
        "pinned_resolved_model": route["resolved_model"],
        "route_id": route["route_id"],
        "sub_reason": "model_absent",
    }


def _sub_reason_platform_route_changed(
    route: dict[str, Any], snapshot: dict[str, Any]
) -> dict[str, Any] | None:
    """The snapshot declares a platform-side route change for the pinned tuple.

    This reads a *separate* snapshot array, so it can co-occur with any of the three
    predicates above and is disjoint only because it is evaluated last. The observed
    model equals the pinned one here, and recording both is the evidence that the
    divergence is not in the alias table.
    """
    pinned = {"alias": route["alias"], "resolved_model": route["resolved_model"]}
    if pinned not in snapshot["platform_route_changes"]:
        return None
    return {
        "alias": route["alias"],
        "observed_resolved_model": snapshot["alias_bindings"][route["alias"]],
        "pinned_resolved_model": route["resolved_model"],
        "route_id": route["route_id"],
        "sub_reason": "platform_route_changed",
    }


SUB_REASON_STAGES: tuple[tuple[str, Any], ...] = (
    ("alias_unresolved", _sub_reason_alias_unresolved),
    ("alias_repointed", _sub_reason_alias_repointed),
    ("model_absent", _sub_reason_model_absent),
    ("platform_route_changed", _sub_reason_platform_route_changed),
)

_require(
    tuple(name for name, _ in SUB_REASON_STAGES) == SUB_REASON_ORDER,
    "the staged sub-reason call graph does not match the contract's declared order",
)

# The first three stages partition the alias-binding table and leave no resolvable
# model to consult probe state or effort support for; ``platform_route_changed``
# leaves the binding intact and the model available, so it does not suppress the
# downstream per-route checks. Sliced from the contract's own order rather than
# restated, so a reordering of the enum cannot silently repartition this set.
_ALIAS_TABLE_SUB_REASONS: frozenset[str] = frozenset(SUB_REASON_ORDER[:3])


def _sub_reason(route: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any] | None:
    """Return the single applicable sub-reason payload, or None when the tuple holds."""
    for name, stage in SUB_REASON_STAGES:
        details = stage(route, snapshot)
        if details is not None:
            _require(
                details["sub_reason"] == name,
                f"sub-reason stage {name} emitted a payload for {details['sub_reason']}",
            )
            return details
    return None


def _stage_preferred_model_unavailable(
    route: dict[str, Any], snapshot: dict[str, Any]
) -> list[dict[str, Any]]:
    """FR-006: the pinned tuple is unavailable, with a machine-readable sub-reason."""
    details = _sub_reason(route, snapshot)
    if details is None:
        return []
    return [
        _diagnostic(
            "preferred_model_unavailable",
            f"Route {route['route_id']} pins a tuple the environment does not offer"
            f" ({details['sub_reason']}).",
            "The route's pinned alias and resolved model no longer match the environment.",
            details=details,
        )
    ]


def load_corpus(path: Path | str = DEFAULT_CORPUS_PATH) -> dict[str, Any]:
    """Read the pinned scenario corpus and structurally check its envelope.

    The corpus has **no schema of its own** — FR-016 permits exactly three contract
    documents and none of them validates the envelope — so the properties FR-033b's
    append-only seam rule and SC-007's read-one-case guarantee lean on are checked
    here, fail-closed, before any case reaches the walk. This is the one entry point
    that touches the filesystem; ``resolve`` never does.
    """
    document = Path(path)
    _require(document.is_file(), f"scenario corpus is not committed: {document}")
    try:
        corpus = json.loads(document.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RouteFallbackError(f"scenario corpus is not valid JSON: {document}") from exc
    _require(isinstance(corpus, dict), "scenario corpus is not an object")
    _require(
        corpus.get("schema_version") == SCHEMA_VERSION,
        f"scenario corpus does not pin schema_version {SCHEMA_VERSION}",
    )
    _require(
        corpus.get("fixture_kind") == CORPUS_FIXTURE_KIND,
        f"scenario corpus does not declare fixture_kind {CORPUS_FIXTURE_KIND}",
    )
    description = corpus.get("description")
    _require(
        isinstance(description, str) and bool(description),
        "scenario corpus carries no description",
    )
    cases = corpus.get("cases")
    _require(isinstance(cases, list) and bool(cases), "scenario corpus declares no cases")
    for index, case in enumerate(cases):
        _require(isinstance(case, dict), f"corpus case at position {index} is not an object")
        for member in CASE_MEMBERS:
            _require(member in case, f"corpus case at position {index} omits {member}")
        case_id = case["case_id"]
        _require(
            isinstance(case_id, str) and bool(case_id),
            f"corpus case at position {index} carries no case_id",
        )
    return corpus


class _WalkState:
    """Mutable accounting for one resolution walk.

    The attempt list and the per-route diagnostic lists are held together because the
    diagnostics array is assembled from them *after* the walk ends, in the attempt
    order this state records rather than in the order the checks happened to run.
    """

    __slots__ = ("attempted", "diagnostics_by_route", "probe_attempts", "retries", "consulted")

    def __init__(self) -> None:
        self.attempted: list[dict[str, Any]] = []
        self.diagnostics_by_route: list[list[dict[str, Any]]] = []
        self.probe_attempts = 0
        self.retries = 0
        self.consulted: set[str] = set()


def _declared_routes(policy: dict[str, Any]) -> list[dict[str, Any]]:
    """FR-004: the preferred route first, then the declared fallbacks in order."""
    return [policy["preferred_route"], *policy["fallback_routes"]]


def _require_pinned_tuple(route: dict[str, Any]) -> None:
    """A route reaching the walk pins both a resolved model and an effort.

    Both are optional in the route contract deliberately, so a route omitting one is
    admitted by the schema and rejected here rather than failing validation. Failing
    closed at walk entry is the honest handling: resolution cannot consult a tuple it
    was never given, and a selected route must yield a dispatch tuple whose four
    members are all required.
    """
    for member in INHERITABLE_ROUTE_MEMBERS:
        value = route.get(member)
        _require(
            isinstance(value, str) and bool(value),
            f"route {route.get('route_id')!r} declares no {member}",
        )


def _dispatch_tuple(agent: str, route: dict[str, Any]) -> dict[str, Any]:
    """FR-013: the four-member tuple resolution selected, all members required."""
    return {
        "agent": agent,
        "alias": route["alias"],
        "resolved_model": route["resolved_model"],
        "effort": route["effort"],
    }


def _attempted_entry(route: dict[str, Any], disposition: str) -> dict[str, Any]:
    """One ``attempted_routes`` entry. Array position carries the attempt index, so
    no index field is recorded (FR-004)."""
    return {
        "route_id": route["route_id"],
        "alias": route["alias"],
        "resolved_model": route["resolved_model"],
        "effort": route["effort"],
        "disposition": disposition,
    }


def _model_is_consultable(route: dict[str, Any], snapshot: dict[str, Any]) -> bool:
    """Whether the route resolves to a model whose effort support and probe state can
    be read at all.

    False exactly when one of the three alias-table sub-reasons applies: the alias is
    unbound, or bound elsewhere, or the pinned model is not offered. In each of those
    the snapshot holds no resolvable model, so the downstream checks would be reading
    an entry for a tuple that does not exist and ``probe_attempts`` is not raised —
    which is what FR-026a means by a route rejected before probing is reached.
    ``platform_route_changed`` leaves the binding intact and the model available, so it
    does **not** gate them.
    """
    details = _sub_reason(route, snapshot)
    return details is None or details["sub_reason"] not in _ALIAS_TABLE_SUB_REASONS


def _stage_effort_unsupported(
    route: dict[str, Any], snapshot: dict[str, Any]
) -> list[dict[str, Any]]:
    """FR-007: the model is available but does not support the declared effort.

    This is a **preflight qualification failure**, deliberately diverging from the
    documented runtime, which degrades silently to the highest supported level at or
    below the declared one. A route whose effort silently degrades is not the tuple the
    policy pinned, so it is not a qualified route (FR-007a, SC-013).
    """
    supported = snapshot["supported_efforts"].get(route["resolved_model"], [])
    if route["effort"] in supported:
        return []
    return [
        _diagnostic(
            "effort_unsupported",
            f"Route {route['route_id']} declares effort {route['effort']}, which model"
            f" {route['resolved_model']} does not support.",
            "The route's declared effort is outside the model's supported effort set.",
            details={
                "declared_effort": route["effort"],
                "route_id": route["route_id"],
                "supported_efforts": list(supported),
            },
        )
    ]


def _consult_probe_state(state: _WalkState, route: dict[str, Any]) -> None:
    """FR-026a: one consultation of a route's probe state, counted once.

    Capability-probe availability and the exact-invocation outcome are read together as
    a single consultation. A route's **first** consultation raises ``probe_attempts``;
    every consultation after it raises ``retries`` instead. That split is load bearing,
    not stylistic: counting every consultation here would let a route probed twice report
    ``probe_attempts: 2`` against ``candidate_routes: 1``, falsifying the invariant that
    the former never exceeds the latter, and would make one retry unreachable under a
    probe cap of one.
    """
    route_id = route["route_id"]
    if route_id in state.consulted:
        state.retries += 1
        return
    state.consulted.add(route_id)
    state.probe_attempts += 1


def _release_claim_eligible(
    outcome: str, diagnostics: list[dict[str, Any]], overrides: dict[str, Any] | None
) -> bool:
    """FR-024a: a closed list of disqualifiers with ``true`` as the residual.

    ``false`` when an override is in force, when the outcome is ``no_safe_route``, or
    when any policy-violation diagnostic is present. Note what is deliberately **not**
    a disqualifier: a preferred route rejected for ``alias_repointed`` or
    ``platform_route_changed`` that then resolves on a declared qualified fallback stays
    eligible, because the route that will dispatch is qualified. That route-scoped fact
    is carried by its ``attempted_routes`` entry and its diagnostic sub-reason, not by
    this report-scoped flag.
    """
    if overrides is not None:
        return False
    if outcome != "resolved":
        return False
    if any(entry["code"] in POLICY_VIOLATION_CODES for entry in diagnostics):
        return False
    return True


def _optional_helper_state(policy: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    """FR-025 and FR-025a: the helper block, structured and never a diagnostic.

    Helper unavailability is an environment condition rather than a policy-authoring
    defect, so it emits no diagnostic and neither closed enum gains a member for it.

    All three reachable states are reported from one walk over the helper's own
    declared routes, held in its **own** ``_WalkState``. That is what makes three
    separate obligations structural rather than asserted:

    * ``consulted`` is derived from the probe counter, not set beside it, so "not
      consulted" is a measurable zero. An implementation cannot probe every helper
      route and still report ``false`` — the two cannot disagree, because one is
      defined as the other being non-zero.
    * the counter is **disjoint** from ``budgets.actual.probe_attempts``, because the
      helper's consultations are counted in a state the reported agent's walk never
      touches.
    * no helper route can reach ``attempted_routes``, because only the agent's own
      state feeds that array.

    A policy declaring no helper reports the same triple as an unavailable one, which
    is deliberate rather than a lost distinction: whether a helper exists is a
    property of the policy, and every case carries its own policy.
    """
    declared = policy.get("optional_helper")
    if declared is None:
        return {"consulted": False, "no_helper_path_validated": True, "probe_attempts": 0}
    helper = _WalkState()
    for route in _declared_routes(declared):
        _require_pinned_tuple(route)
        if not _route_diagnostics(route, snapshot, helper):
            break
    consulted = helper.probe_attempts > 0
    return {
        "consulted": consulted,
        "no_helper_path_validated": not consulted,
        "probe_attempts": helper.probe_attempts,
    }


def _reported_budgets(state: _WalkState, budgets: dict[str, Any]) -> dict[str, Any]:
    """FR-026: the declared caps beside the actual counts.

    ``candidate_routes`` is read off the attempt list rather than counted separately,
    because one candidate entered is exactly one entry recorded — the two are
    definitionally equal, and deriving it makes them unable to disagree.
    """
    return {
        "declared": {member: budgets[member] for member in DECLARED_BUDGET_MEMBERS},
        "actual": {
            "probe_attempts": state.probe_attempts,
            "retries": state.retries,
            "candidate_routes": len(state.attempted),
        },
    }


def _stage_capability_probe_unavailable(
    route: dict[str, Any], snapshot: dict[str, Any]
) -> list[dict[str, Any]]:
    """FR-008: capability probing is unavailable for the route's model.

    The lookup defaults to unavailable, so a snapshot omitting a model's entry fails
    closed. Probe absence is never treated as probe success — an absent key is exactly
    the ambiguity that invites that substitution, which is why the projection writes an
    explicit ``false`` and why the default here agrees with it.
    """
    if snapshot["probe_availability"].get(route["resolved_model"], False):
        return []
    return [
        _diagnostic(
            "capability_probe_unavailable",
            f"Route {route['route_id']} has capability probing unavailable for model"
            f" {route['resolved_model']}.",
            "Capability probing is unavailable for the route's model.",
            details={"route_id": route["route_id"]},
        )
    ]


def _stage_treatment_probe_failed(
    route: dict[str, Any], snapshot: dict[str, Any]
) -> list[dict[str, Any]]:
    """FR-009: the exact-invocation probe outcome is a failure, so the route is never
    selected. ``absent`` is not a failure — it records that no exact-invocation outcome
    was captured at all, which ``capability_probe_unavailable`` is the code for when the
    probe itself could not run."""
    if snapshot["exact_invocation_probe"].get(route["resolved_model"]) != "failure":
        return []
    return [
        _diagnostic(
            "treatment_probe_failed",
            f"Route {route['route_id']} has an exact-invocation probe failure for model"
            f" {route['resolved_model']}.",
            "The exact-invocation probe failed for the route's model.",
            details={"route_id": route["route_id"]},
        )
    ]


def _route_diagnostics(
    route: dict[str, Any], snapshot: dict[str, Any], state: _WalkState
) -> list[dict[str, Any]]:
    """The *inter-diagnostic* staged call graph for one attempted route.

    One private helper per rejection family, called in the FR-005 declaration order,
    each appending its own diagnostic when its predicate holds — so a route failing
    several independent checks emits one diagnostic per failed check rather than only
    the highest-precedence reason. A route is compatible exactly when this returns an
    empty list.
    """
    diagnostics: list[dict[str, Any]] = []
    diagnostics.extend(_stage_preferred_model_unavailable(route, snapshot))
    if not _model_is_consultable(route, snapshot):
        return diagnostics
    diagnostics.extend(_stage_effort_unsupported(route, snapshot))
    _consult_probe_state(state, route)
    diagnostics.extend(_stage_capability_probe_unavailable(route, snapshot))
    diagnostics.extend(_stage_treatment_probe_failed(route, snapshot))
    return diagnostics


def _stage_no_safe_route(agent: str) -> list[dict[str, Any]]:
    """FR-029: the one terminal entry, carrying the mandated rollback action.

    It is the only code carrying both a forward remedy and the rollback, so per-route
    entries are never inflated toward the three-action truncation boundary. ``details``
    is omitted rather than emitted empty: its only member here would be the at-cap
    budget set, and ``minItems: 1`` forbids recording an empty one.
    """
    return [
        _diagnostic(
            "no_safe_route",
            f"No declared route resolved for agent {agent}.",
            "No declared route resolved, so this environment cannot support a release claim.",
        )
    ]


# --------------------------------------------------------------------------- #
# FR-019c: the pre-walk staged call graph over the policy-document violations   #
# --------------------------------------------------------------------------- #
# The four policy-authoring codes do NOT partition uniformly, and recording the
# partition is what reconciles FR-020 with the pre-pass framing. Three are
# properties of the policy *document*, decidable by reading the declared routes
# with no walk state, so they run to completion before the first route is
# attempted and suppress the walk entirely. ``fallback_loop`` is deliberately not
# among them: it is defined against a route already attempted, and deciding it from
# the document alone would convert a policy that RESOLVES into a failing one,
# because a duplicate later in the chain is never reached when an earlier route
# resolves. ``unqualified_override`` is neither — it is an environment condition
# read from the overrides input and never suppresses the walk.

IN_WALK_VIOLATION_CODE = "fallback_loop"
ENVIRONMENT_VIOLATION_CODE = "unqualified_override"

# Derived by filtering the live enum rather than transcribed, so "three, not four"
# is a property of the one declaration site instead of a second list to keep in step.
PRE_WALK_VIOLATION_CODES: tuple[str, ...] = tuple(
    code
    for code in POLICY_VIOLATION_CODES
    if code not in (IN_WALK_VIOLATION_CODE, ENVIRONMENT_VIOLATION_CODE)
)
_require(
    len(PRE_WALK_VIOLATION_CODES) == len(POLICY_VIOLATION_CODES) - 2,
    "the pre-walk partition does not exclude exactly the in-walk and environment codes",
)

# FR-023: the two dispatch members a route may leave to inheritance. One declaration
# site, read by the pre-walk stage that rejects an omission and by the walk-entry
# guard that fails closed on one, so the two cannot disagree about which members
# resolution requires.
INHERITABLE_ROUTE_MEMBERS: tuple[str, ...] = ("resolved_model", "effort")


def _adjacent_sibling(route: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """The declared route a route's ``adjacent_to`` reference names.

    Fails closed on a dangling reference: an adjacency claim against a route the
    policy does not declare is unresolvable, and silently reading it as "no
    adjacency" would let the defect FR-021 exists to catch pass as a clean policy.
    """
    reference = route["adjacent_to"]
    siblings = [each for each in _declared_routes(policy) if each["route_id"] == reference]
    _require(
        siblings,
        f"route {route['route_id']!r} declares adjacency to {reference!r},"
        " which this policy does not declare",
    )
    return siblings[0]


def _stage_unqualified_adjacent_model(
    route: dict[str, Any], policy: dict[str, Any]
) -> list[dict[str, Any]]:
    """FR-021: a fallback adjacent to a qualified route but not itself qualified.

    The adjacency relation is read from the route's own ``adjacent_to`` sibling
    reference rather than inferred from declaration position, so "adjacent" is a
    stated property of the fixture instead of an artefact of list order.
    """
    if "adjacent_to" not in route:
        return []
    sibling = _adjacent_sibling(route, policy)
    if route.get("qualified") or not sibling.get("qualified"):
        return []
    return [
        _diagnostic(
            "unqualified_adjacent_model",
            f"Route {route['route_id']} is adjacent to qualified route"
            f" {sibling['route_id']} without being qualified itself.",
            "The declared fallback is adjacent to a qualified route but is not qualified.",
            details={"route_id": route["route_id"]},
        )
    ]


def _stage_generic_agent_substitution(
    route: dict[str, Any], policy: dict[str, Any]
) -> list[dict[str, Any]]:
    """FR-022: a fallback replacing a named synthetic agent with a generic one."""
    substituted = route.get("substituted_agent")
    if substituted is None or substituted.get("class") != "generic":
        return []
    return [
        _diagnostic(
            "generic_agent_substitution",
            f"Route {route['route_id']} substitutes generic agent"
            f" {substituted['name']} for named agent {policy['agent']['name']}.",
            "The declared fallback substitutes a generic agent for the policy's named agent.",
            details={"route_id": route["route_id"]},
        )
    ]


def _stage_silent_inherit_materialization(
    route: dict[str, Any], policy: dict[str, Any]
) -> list[dict[str, Any]]:
    """FR-023: a route whose model or effort would be materialized by inheritance.

    Such a route is **admitted by the route contract and rejected here**, which is
    why both members stay optional in that contract: requiring them there would make
    the fixture fail validation and no diagnostic would ever be produced. The omitted
    member is named in the message rather than in ``details``, which carries the join
    key alone for every policy-authoring code.
    """
    for member in INHERITABLE_ROUTE_MEMBERS:
        value = route.get(member)
        if isinstance(value, str) and value:
            continue
        return [
            _diagnostic(
                "silent_inherit_materialization",
                f"Route {route['route_id']} of policy {policy['agent']['name']} omits"
                f" {member}, which resolution would materialize by inheritance.",
                "The declared route leaves a dispatch member to be materialized by inheritance.",
                details={"route_id": route["route_id"]},
            )
        ]
    return []


PRE_WALK_STAGES: tuple[tuple[str, Any], ...] = (
    ("unqualified_adjacent_model", _stage_unqualified_adjacent_model),
    ("generic_agent_substitution", _stage_generic_agent_substitution),
    ("silent_inherit_materialization", _stage_silent_inherit_materialization),
)

_require(
    tuple(name for name, _ in PRE_WALK_STAGES) == PRE_WALK_VIOLATION_CODES,
    "the staged pre-walk call graph does not match the contract's declared order",
)


def _pre_walk_violations(policy: dict[str, Any]) -> list[dict[str, Any]]:
    """FR-019c and FR-012b: the whole pre-walk pass, run to completion.

    Ordered by the declared route position each violation concerns and then by the
    FR-019 declaration order, which the staged tuple above makes a call-graph
    property. Every route is read even after one has already been rejected, because
    the pass reports the policy rather than stopping at the first defect.
    """
    violations: list[dict[str, Any]] = []
    for route in _declared_routes(policy):
        for code, stage in PRE_WALK_STAGES:
            for entry in stage(route, policy):
                _require(
                    entry["code"] == code,
                    f"pre-walk stage {code} emitted a {entry['code']} entry",
                )
                violations.append(entry)
    return violations


def _already_attempted(state: _WalkState, route: dict[str, Any]) -> bool:
    """FR-020: whether the walk has already attempted this route.

    Read off the attempt list the walk already builds rather than from a second set,
    so the identity a revisit is recognised by is the same identity the report
    records — which is what makes the loop diagnostic's join key trustworthy.
    """
    return any(entry["route_id"] == route["route_id"] for entry in state.attempted)


def _stage_fallback_loop(route: dict[str, Any]) -> list[dict[str, Any]]:
    """FR-020: the revisit, detected in the walk at the point it is reached.

    Emitted as a trailing per-route group so it lands after the last attempted
    route's entries in the whole-array order, which is where detection-on-arrival
    puts it. The revisited route is neither re-attempted nor re-consulted.
    """
    return [
        _diagnostic(
            "fallback_loop",
            f"Route {route['route_id']} is revisited by the declared fallback chain.",
            "The declared fallback chain revisits a route the walk already attempted.",
            details={"route_id": route["route_id"]},
        )
    ]


# --------------------------------------------------------------------------- #
# FR-024 and FR-024b: the two override branches                                #
# --------------------------------------------------------------------------- #
# The honored branch records what will dispatch; the allowlist-skip branch records
# only that the override did NOT take effect. The second is deliberately bounded to
# that negative: the documented fallback target there is the *inherited* model,
# which this projection does not carry and must not gain, so naming a model that
# runs instead would be inference rather than simulation.

# FR-024b: the documented mechanism, read live from the contract's own ``const`` so
# the variable's name has one declaration site here as it does in the schema.
OVERRIDE_SOURCE: str = REPORT_SCHEMA["$defs"]["override"]["properties"]["source"]["const"]

# The documented value that restores normal model resolution. It is a SET value that
# behaves as unset, so it is the no-override state rather than an override, and a
# case declaring it carries a null ``overrides`` member instead (FR-015a, FR-024b).
INHERIT_SENTINEL = "inherit"


def _override_requested_model(overrides: dict[str, Any]) -> str:
    """The raw override value, which may be a family alias or a full model ID."""
    _require(
        set(overrides) == {OVERRIDE_SOURCE},
        f"the environment overrides declare something other than {OVERRIDE_SOURCE},"
        " and this simulation recognises no second override mechanism",
    )
    requested = overrides[OVERRIDE_SOURCE]
    _require(
        isinstance(requested, str) and bool(requested),
        f"the {OVERRIDE_SOURCE} override declares no value",
    )
    _require(
        requested != INHERIT_SENTINEL,
        f"{OVERRIDE_SOURCE}={INHERIT_SENTINEL} restores normal model resolution and is"
        " the no-override state, which a case declares with a null overrides member",
    )
    return requested


def _override_target(requested: str, snapshot: dict[str, Any]) -> str:
    """The resolved model the override's requested value names.

    The documented variable accepts either a family alias or a full model ID, so a
    value the snapshot binds resolves through the binding and one it does not binds
    to itself. This is the value the organization allowlist is checked against,
    because the documented runtime skips a value that *resolves to* an excluded model.
    """
    return snapshot["alias_bindings"].get(requested, requested)


def _override_is_qualified(policy: dict[str, Any], requested: str, target: str) -> bool:
    """FR-024b: an override is unqualified when its tuple matches no qualified route.

    Compared on alias and resolved model, which are the two members the override
    determines: the agent is the policy's own subject and the effort is retained from
    the walk, so neither discriminates between an override and a declared route.
    """
    return any(
        route.get("qualified")
        and route.get("alias") == requested
        and route.get("resolved_model") == target
        for route in _declared_routes(policy)
    )


def _override_dispatch_tuple(
    policy: dict[str, Any],
    requested: str,
    target: str,
    selected: dict[str, Any] | None,
) -> dict[str, Any]:
    """FR-024b: the hybrid tuple, part override and part retained.

    The variable sets a **model** only — no documented subagent-effort environment
    override exists — so the alias and resolved model come from the override's
    requested value while the agent and effort are retained from the route the
    qualified walk selected, or from the preferred route when it selected none.
    Attributing each member is what makes the pinned bytes derivable.
    """
    retained = policy["preferred_route"] if selected is None else selected
    effort = retained.get("effort")
    _require(
        isinstance(effort, str) and bool(effort),
        f"the override retains its effort from route {retained.get('route_id')!r},"
        " which declares none",
    )
    return {
        "agent": policy["agent"]["name"],
        "alias": requested,
        "resolved_model": target,
        "effort": effort,
    }


def _override_record(
    policy: dict[str, Any],
    snapshot: dict[str, Any],
    overrides: dict[str, Any],
    selected: dict[str, Any] | None,
    outcome: str,
) -> dict[str, Any]:
    """The override block, on whichever of the two documented branches applies."""
    requested = _override_requested_model(overrides)
    target = _override_target(requested, snapshot)
    honored = target in snapshot["available_models_allowlist"]
    would_have_been: dict[str, Any] = {"outcome": outcome}
    if selected is not None:
        would_have_been["effective_dispatch_tuple"] = _dispatch_tuple(
            policy["agent"]["name"], selected
        )
    record: dict[str, Any] = {
        "source": OVERRIDE_SOURCE,
        "requested_model": requested,
        "disposition": "honored" if honored else "skipped_by_allowlist",
        "qualified": _override_is_qualified(policy, requested, target),
        "would_have_been": would_have_been,
    }
    if honored:
        record["tuple"] = _override_dispatch_tuple(policy, requested, target, selected)
    return record


def _stage_unqualified_override(record: dict[str, Any]) -> list[dict[str, Any]]:
    """FR-024: the diagnostic an *unqualified* override in force emits.

    Scoped to the qualification defect alone: a qualified override is equally in
    force and equally disqualifies the environment, but emits nothing here, because
    the diagnostic reports the defect while ``release_claim_eligible`` reports the
    environment. It carries no ``details`` at all — it is an environment condition
    scoped to no route, so it has no join key to carry — and its severity is
    ``warning`` because dispatch proceeds under it.
    """
    if record["qualified"]:
        return []
    return [
        _diagnostic(
            "unqualified_override",
            f"A {OVERRIDE_SOURCE} override requests {record['requested_model']},"
            " which matches no route this policy declares qualified.",
            "An unqualified subagent-model override excludes this environment"
            " from release claims.",
        )
    ]


def _effective_dispatch_tuple(
    agent: str, selected: dict[str, Any] | None, record: dict[str, Any] | None
) -> dict[str, Any] | None:
    """What will actually dispatch, which is not always what resolution selected.

    An honored override wins at dispatch by its documented precedence. A skipped one
    does not, so the tuple falls back to the qualified walk's own selection — never
    to a model named for the override, and never to the inherited model the runtime
    would use, which this projection does not carry. When the override was skipped
    *and* the walk selected nothing there is no honest tuple to record and the
    contract requires one, so that state fails closed rather than being invented.
    """
    if record is not None and record["disposition"] == "honored":
        return record["tuple"]
    if selected is not None:
        return _dispatch_tuple(agent, selected)
    _require(
        record is None,
        f"a {OVERRIDE_SOURCE} override skipped by the organization allowlist over a walk"
        " that resolved nothing has no representable effective dispatch tuple: the"
        " projection does not carry the inherited model the runtime would run",
    )
    return None


def _assemble_diagnostics(
    *,
    pre_walk: Any = (),
    per_route: Any = (),
    override: Any = (),
    terminal: Any = (),
) -> list[dict[str, Any]]:
    """FR-012b: the whole-array order, in the four ordering slots the contract fixes.

    First the policy-document violations the pre-walk pass decides; second, for each
    attempted route in attempt order, that route's own entries in the inter-code order
    ``_route_diagnostics`` produced them in; third ``unqualified_override``; last
    exactly one terminal ``no_safe_route``. The slots are parameters rather than reads
    of walk state so the array contract is one function with one order, checkable
    independently of which rule families a given input happens to trigger.
    """
    assembled: list[dict[str, Any]] = list(pre_walk)
    for route_entries in per_route:
        assembled.extend(route_entries)
    assembled.extend(override)
    assembled.extend(terminal)
    return assembled


def resolve(
    policy: dict[str, Any],
    snapshot: dict[str, Any],
    overrides: dict[str, Any] | None,
    budgets: dict[str, Any],
) -> dict[str, Any]:
    """Walk one policy against one snapshot and return the resolution report.

    A **pure function** of its four arguments: no filesystem, network, wall-clock, or
    randomness input, and no mutation of any argument, which is what makes replay
    byte-identical (FR-001, FR-014).
    """
    _require(isinstance(policy, dict), "policy is not an object")
    _require(isinstance(snapshot, dict), "snapshot is not an object")
    _require(
        overrides is None or isinstance(overrides, dict),
        "overrides is neither an object nor null",
    )
    _require(
        budgets == policy.get("budgets"),
        "the declared budgets argument does not match the policy's own declaration",
    )

    agent = policy["agent"]["name"]
    state = _WalkState()
    selected: dict[str, Any] | None = None

    # FR-019c: the pre-walk pass runs to completion first, and the walk does not start
    # at all when it emits anything. The biconditional the report contract leans on
    # follows from this shape rather than from a bound: the attempt array is empty
    # exactly when this branch was not taken.
    pre_walk = _pre_walk_violations(policy)
    revisited: list[list[dict[str, Any]]] = []
    if not pre_walk:
        for route in _declared_routes(policy):
            if _already_attempted(state, route):
                revisited.append(_stage_fallback_loop(route))
                break
            _require_pinned_tuple(route)
            route_diagnostics = _route_diagnostics(route, snapshot, state)
            state.diagnostics_by_route.append(route_diagnostics)
            disposition = "rejected" if route_diagnostics else "selected"
            state.attempted.append(_attempted_entry(route, disposition))
            if disposition == "selected":
                selected = route
                break

    # FR-024a: the outcome follows the QUALIFIED walk. An override is recorded beside
    # it and never promotes it, which is what lets one report say that nothing
    # qualified resolved and that something will nevertheless dispatch.
    outcome = "resolved" if selected is not None else "no_safe_route"
    override = (
        None
        if overrides is None
        else _override_record(policy, snapshot, overrides, selected, outcome)
    )
    diagnostics = _assemble_diagnostics(
        pre_walk=pre_walk,
        per_route=[*state.diagnostics_by_route, *revisited],
        override=() if override is None else _stage_unqualified_override(override),
        terminal=() if selected is not None else _stage_no_safe_route(agent),
    )

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "agent": agent,
        "outcome": outcome,
        "attempted_routes": state.attempted,
        "diagnostics": diagnostics,
        "budgets": _reported_budgets(state, budgets),
        "release_claim_eligible": _release_claim_eligible(outcome, diagnostics, overrides),
        "optional_helper": _optional_helper_state(policy, snapshot),
    }
    if override is not None:
        report["override"] = override
    effective = _effective_dispatch_tuple(agent, selected, override)
    if effective is not None:
        report["effective_dispatch_tuple"] = effective
    if selected is None:
        report["unresolved_agent"] = agent

    # FR-012b: the outcome value and the terminal code are coupled BOTH ways, so a
    # report can neither claim resolved while carrying a terminal failure nor claim
    # no_safe_route while carrying no remediation at all.
    terminal_entries = [entry for entry in diagnostics if entry["code"] == "no_safe_route"]
    _require(
        len(terminal_entries) == (0 if outcome == "resolved" else 1),
        f"outcome {outcome} does not match the terminal diagnostic count"
        f" {len(terminal_entries)}",
    )
    if terminal_entries:
        _require(
            diagnostics[-1] is terminal_entries[0],
            "the terminal no_safe_route entry is not the final element of the array",
        )

    # FR-026a: a route rejected before probing is reached raises candidate_routes
    # without raising probe_attempts, so the two are not redundant and the inequality
    # is one-directional.
    actual = report["budgets"]["actual"]
    _require(
        actual["probe_attempts"] <= actual["candidate_routes"],
        f"probe_attempts {actual['probe_attempts']} exceeds candidate_routes"
        f" {actual['candidate_routes']}",
    )

    # FR-033b: every report this module emits is a fully valid instance of the committed
    # contract, checked against the schema parsed once at import — so validity is a
    # property of the simulator rather than of the corpus that happens to replay it.
    validate_instance(report, REPORT_SCHEMA, path="route-resolution-report")
    return report


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
