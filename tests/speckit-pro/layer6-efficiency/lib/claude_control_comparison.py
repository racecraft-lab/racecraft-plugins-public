#!/usr/bin/env python3
"""Validator for the CAR-004 control-comparison contract and its decision procedure.

The committed schema document at
``tests/speckit-pro/layer6-efficiency/contracts-claude/control-comparison.schema.json``
is the single source of truth for the contract's shape; the frozen CAR-003
documents it binds are the source of truth for every enumeration it restates.
Neither is transcribed here — a set-equality check only fails closed on an
upstream membership change while both sides read the same committed bytes.

CAR-004 concludes nothing about dominance. This module freezes *how* a verdict
will be produced: three stages in a fixed order — the FR-019 eligibility floors,
then the frozen eight-dimension Pareto rule, then the FR-021 materiality margin —
implemented as three functions so the order is a call-graph property rather than
a convention. No weighted scalar ranking is imported or accepted.

The fail-closed schema engine is imported from ``claude_policy_controls`` rather
than duplicated: it has exactly two in-tree callers, which is why it lives there
(research D1).

Every entrypoint is fail-closed: it raises on the first violation and never
returns a partial verdict. Standard library only — no third-party ``jsonschema``
(constitution principle II).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

# Read-only import: one preimage rule governs every digest in the program.
from claude_successor_freeze import record_digest

# The shared fail-closed schema engine and the committed-document roots, imported
# rather than restated (research D1).
from claude_policy_controls import (
    CONTRACT_ROOT,
    FIXTURE_ROOT,
    ControlContractError,
    load_contract,
    require_utc_timestamp,
    validate_instance,
    verify_car_003_bindings,
)


FROZEN_COMPARISON_SCHEMA_PATH = CONTRACT_ROOT / "control-comparison.schema.json"
FROZEN_COMPARISON_PATH = FIXTURE_ROOT / "control-comparison.json"

FROZEN_SCORE_BUNDLE_SCHEMA_PATH = CONTRACT_ROOT / "score-bundle.schema.json"
FROZEN_ANALYSIS_PLAN_SCHEMA_PATH = CONTRACT_ROOT / "analysis-plan.schema.json"


class ControlComparisonError(AssertionError):
    """Raised when an instance violates the CAR-004 control-comparison contract."""


# --------------------------------------------------------------------------- #
# Frozen sources, read once from the committed bytes                            #
# --------------------------------------------------------------------------- #

COMPARISON_SCHEMA: dict[str, Any] = load_contract(FROZEN_COMPARISON_SCHEMA_PATH)
_SCORE_BUNDLE_SCHEMA: dict[str, Any] = load_contract(FROZEN_SCORE_BUNDLE_SCHEMA_PATH)
_ANALYSIS_PLAN_SCHEMA: dict[str, Any] = load_contract(FROZEN_ANALYSIS_PLAN_SCHEMA_PATH)

# FR-019: the seven mandatory gates a candidate already faces.
FROZEN_GATES: tuple[str, ...] = tuple(
    _SCORE_BUNDLE_SCHEMA["properties"]["deterministic_gates"]["items"]["properties"]["gate"]["enum"]
)

# FR-020: the eight decision-bearing dimensions, under the decision-vector names.
FROZEN_DIMENSIONS: tuple[str, ...] = tuple(
    _ANALYSIS_PLAN_SCHEMA["properties"]["pareto_policy"]["properties"]["dimensions"]["items"]["enum"]
)

# FR-021e: the frozen score bundle's own resource-vector member names, which the
# projection carries onto the dimension names above.
FROZEN_RESOURCE_VECTOR_MEMBERS: tuple[str, ...] = tuple(
    _SCORE_BUNDLE_SCHEMA["properties"]["resource_vector"]["required"]
)

# FR-019: a guardrail breach withholds qualification; the CAR-004 contract
# restates that outcome and is checked against the frozen declaration.
FROZEN_GUARDRAIL_BREACH_RESULT: str = (
    _ANALYSIS_PLAN_SCHEMA["properties"]["reliability_guardrails"]["properties"]["breach_result"]
    ["const"]
)

# FR-005, FR-023, SC-017: the analysis plan's multiplicity declaration is closed
# at three families. The CAR-004 family is declared beside them, never inside.
FROZEN_MULTIPLICITY_FAMILIES: tuple[str, ...] = tuple(
    member
    for member in _ANALYSIS_PLAN_SCHEMA["properties"]["non_inferiority"]["properties"]
    ["multiplicity_declaration"]["required"]
    if member.endswith("_family")
)

_ELIGIBILITY_FLOORS_DEF: dict[str, Any] = COMPARISON_SCHEMA["$defs"]["eligibilityFloors"]
_DOMINANCE_RULE_DEF: dict[str, Any] = COMPARISON_SCHEMA["$defs"]["dominanceRule"]

# FR-024a: the eligibility stage's own outcome. It is deliberately not a member
# of the verdict enum, and reading it from the committed document keeps it that
# way rather than coining a fourth verdict here.
NO_VERDICT: str = _ELIGIBILITY_FLOORS_DEF["properties"]["verdict_when_floor_unmet"]["const"]

# FR-021a: the three stages, in the order the contract states literally.
EVALUATION_ORDER: tuple[str, ...] = tuple(
    _DOMINANCE_RULE_DEF["properties"]["evaluation_order"]["const"]
)

# FR-021c: the denominator, and the outcome when it is zero.
MARGIN_DENOMINATOR: str = _DOMINANCE_RULE_DEF["properties"]["margin_denominator"]["const"]
MARGIN_NOT_COMPUTABLE: str = _DOMINANCE_RULE_DEF["properties"]["zero_denominator_result"]["const"]

# FR-024: the closed verdict enum. CAR-004 owns these three names, so they are
# written here and immediately checked against the committed messaging map — a
# fourth member added on either side fails closed at import.
VERDICT_DOMINANT = "dominant"
VERDICT_NOT_DOMINANT = "not_dominant"
VERDICT_INCONCLUSIVE = "inconclusive"
VERDICTS: tuple[str, ...] = (VERDICT_DOMINANT, VERDICT_NOT_DOMINANT, VERDICT_INCONCLUSIVE)

if sorted(VERDICTS) != sorted(COMPARISON_SCHEMA["properties"]["messaging_map"]["required"]):
    raise ControlComparisonError(
        f"the verdict enum {sorted(VERDICTS)} is not the committed messaging map's member set "
        f"{sorted(COMPARISON_SCHEMA['properties']['messaging_map']['required'])}"
    )
if NO_VERDICT in VERDICTS:
    raise ControlComparisonError(
        f"the eligibility stage's {NO_VERDICT!r} outcome is not a verdict; FR-024a forbids "
        "closing the hole with a fourth verdict member"
    )

# The margin-map classes, and the three per-component materiality statuses.
MARGIN_ELIGIBLE = "margin_eligible"
NO_WORSE_ONLY = "no_worse_only"
CLEARED = "cleared"
NOT_CLEARED = "not_cleared"

# FR-021: the four ratio-scale cost quantities are the only dimensions that can
# supply material dominance; the other four are no-worse-only, so any of them
# being worse defeats it and none of them can ever supply it. Frozen by name here
# exactly as the raw-token identity's summands are, while the margin itself stays
# a numeric the committed instance owns.
MARGIN_ELIGIBLE_DIMENSIONS = ("input_tokens", "cached_input_tokens", "output_tokens", "duration")

if not set(MARGIN_ELIGIBLE_DIMENSIONS) <= set(FROZEN_DIMENSIONS):
    raise ControlComparisonError(
        f"the margin-eligible dimensions {sorted(MARGIN_ELIGIBLE_DIMENSIONS)} are not all members "
        f"of the frozen Pareto dimensions {sorted(FROZEN_DIMENSIONS)}"
    )

# The Pareto stage's own outcomes. Distinct from the verdicts: stage two never
# concludes, it only hands stage three a candidate to test for materiality.
CANDIDATE_DOMINANT = "candidate_dominant"
COMPARATOR_DOMINANT = "comparator_dominant"
TIED = "tied"
MIXED = "mixed"

# The arm members carrying the three non-gate floors, all positively phrased so a
# reader never has to invert one to know whether the floor was cleared.
ELIGIBILITY_FLOOR_MEMBERS = (
    "quality_floors_met",
    "reliability_guardrails_respected",
    "availability_gate_passed",
)


# --------------------------------------------------------------------------- #
# Contract loading and semantics                                                #
# --------------------------------------------------------------------------- #


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ControlComparisonError(message)


def _block(contract: Mapping[str, Any], member: str) -> Mapping[str, Any]:
    block = contract.get(member)
    _require(isinstance(block, Mapping), f"{member} is missing or is not an object")
    return block  # type: ignore[return-value]


def _validate_eligibility_floors(contract: Mapping[str, Any]) -> None:
    """C3 and C16: the frozen gate set, and the no-verdict outcome's own home."""
    floors = _block(contract, "eligibility_floors")
    gates = floors.get("required_gates")
    _require(
        isinstance(gates, list) and sorted(gates) == sorted(FROZEN_GATES),
        f"eligibility_floors.required_gates must be set-equal to the frozen gate enum "
        f"{sorted(FROZEN_GATES)}, not {gates!r}",
    )
    _require(
        floors.get("all_gates_must_pass") is True,
        "eligibility_floors.all_gates_must_pass is frozen at true",
    )
    # FR-019 names the availability gate among the mandatory ones, so the member
    # that switches it on is frozen at true rather than merely present. Left
    # unchecked, deleting it would silently retire a mandatory gate.
    _require(
        floors.get("availability_gate_required") is True,
        "eligibility_floors.availability_gate_required is frozen at true; FR-019 counts "
        "availability among the mandatory gates",
    )
    _require(
        floors.get("reliability_guardrail_breach_result") == FROZEN_GUARDRAIL_BREACH_RESULT,
        f"eligibility_floors.reliability_guardrail_breach_result must restate the frozen "
        f"guardrail outcome {FROZEN_GUARDRAIL_BREACH_RESULT!r}",
    )
    _require(
        floors.get("verdict_when_floor_unmet") == NO_VERDICT,
        f"eligibility_floors.verdict_when_floor_unmet is frozen at {NO_VERDICT!r}",
    )
    _require(
        isinstance(floors.get("claim_class_when_floor_unmet"), str)
        and floors["claim_class_when_floor_unmet"],
        "eligibility_floors.claim_class_when_floor_unmet carries the no-verdict outcome's "
        "wording class, so the claim-class lookup is total over every reachable outcome",
    )
    _require(
        floors.get("messaging_restriction_when_floor_unmet") is False,
        "an ineligible control imposes no messaging restriction",
    )


def _validate_dominance_rule(contract: Mapping[str, Any]) -> None:
    """C4 through C8: the dimensions, the projection, and the margin map."""
    rule = _block(contract, "dominance_rule")
    dimensions = rule.get("dimensions")
    _require(
        isinstance(dimensions, list) and sorted(dimensions) == sorted(FROZEN_DIMENSIONS),
        f"dominance_rule.dimensions must be set-equal to the frozen Pareto dimensions "
        f"{sorted(FROZEN_DIMENSIONS)}, not {dimensions!r}",
    )
    _require(
        rule.get("weights_prohibited") is True,
        "dominance_rule.weights_prohibited is frozen at true; no weighted scalar ranking exists",
    )
    _require(
        list(rule.get("evaluation_order", ())) == list(EVALUATION_ORDER),
        f"dominance_rule.evaluation_order is frozen at {list(EVALUATION_ORDER)}; the margin is a "
        "second-stage materiality filter and never replaces the Pareto rule",
    )
    _require(
        rule.get("margin_denominator") == MARGIN_DENOMINATOR,
        f"dominance_rule.margin_denominator is frozen at {MARGIN_DENOMINATOR!r}",
    )
    _require(
        rule.get("zero_denominator_result") == MARGIN_NOT_COMPUTABLE,
        f"a zero comparator value records {MARGIN_NOT_COMPUTABLE!r}, never an infinite or "
        "hundred-percent improvement",
    )

    projection = rule.get("dimension_projection")
    _require(isinstance(projection, Mapping) and projection, "dimension_projection is missing")
    for source, target in projection.items():  # type: ignore[union-attr]
        _require(
            source in FROZEN_RESOURCE_VECTOR_MEMBERS,
            f"dimension_projection renames {source!r}, which is not a frozen resource-vector member",
        )
        _require(
            target in FROZEN_DIMENSIONS,
            f"dimension_projection carries {source!r} onto {target!r}, which is not a frozen "
            "Pareto dimension",
        )

    _validate_margin_map(rule.get("margin_map"))


def _validate_margin_map(margin_map: Any) -> None:
    """C6: total over all eight dimensions, four eligible at their margin, four not."""
    _require(isinstance(margin_map, Mapping), "dominance_rule.margin_map is missing")
    _require(
        sorted(margin_map) == sorted(FROZEN_DIMENSIONS),
        f"margin_map must be total over the eight frozen dimensions {sorted(FROZEN_DIMENSIONS)}, "
        f"not {sorted(margin_map)}",
    )
    eligible = []
    for dimension, entry in margin_map.items():
        path = f"margin_map.{dimension}"
        _require(isinstance(entry, Mapping), f"{path} is not an object")
        entry_class = entry.get("class")
        if entry_class == MARGIN_ELIGIBLE:
            eligible.append(dimension)
            margin = entry.get("relative_margin")
            _require(
                isinstance(margin, (int, float)) and not isinstance(margin, bool) and margin > 0,
                f"{path}: a margin-eligible dimension declares its relative margin",
            )
            _require("reason" not in entry, f"{path}: a margin-eligible dimension carries no reason")
        elif entry_class == NO_WORSE_ONLY:
            _require(
                isinstance(entry.get("reason"), str) and entry["reason"],
                f"{path}: a no-worse-only dimension records why it can never supply dominance",
            )
            _require(
                "relative_margin" not in entry,
                f"{path}: a no-worse-only dimension carries no margin",
            )
        else:
            raise ControlComparisonError(
                f"{path}: class is {entry_class!r}, not {MARGIN_ELIGIBLE!r} or {NO_WORSE_ONLY!r}"
            )
        _require(
            isinstance(entry.get("unit"), str) and isinstance(entry.get("direction"), str),
            f"{path}: every entry carries its unit and its comparison direction",
        )
    _require(
        sorted(eligible) == sorted(MARGIN_ELIGIBLE_DIMENSIONS),
        f"the margin-eligible dimensions are frozen at {sorted(MARGIN_ELIGIBLE_DIMENSIONS)}; the "
        f"map declares {sorted(eligible)}",
    )


def _validate_multiplicity_position(contract: Mapping[str, Any]) -> None:
    """C10: the family is declared beside the frozen three, never added to them."""
    position = _block(contract, "multiplicity_position")
    family = position.get("family")
    _require(
        family not in FROZEN_MULTIPLICITY_FAMILIES,
        f"{family!r} is one of the frozen analysis plan's {list(FROZEN_MULTIPLICITY_FAMILIES)}; "
        "the secondary control-arm family is declared here and disjoint from them",
    )
    _require(
        position.get("disjoint_from_frozen_families") is True
        and position.get("draws_alpha_from_primary") is False,
        "the family is disjoint from the frozen families and draws no alpha from the primary "
        "comparison",
    )


def _validate_messaging_map(contract: Mapping[str, Any]) -> None:
    """C11, C12, C14, C15: total, single-valued, and restricting only on dominance."""
    messaging_map = _block(contract, "messaging_map")
    _require(
        sorted(messaging_map) == sorted(VERDICTS),
        f"messaging_map must be total and single-valued over {sorted(VERDICTS)}, not "
        f"{sorted(messaging_map)}",
    )
    for verdict, entry in messaging_map.items():
        path = f"messaging_map.{verdict}"
        _require(isinstance(entry, Mapping), f"{path} is not an object")
        restricts = verdict == VERDICT_DOMINANT
        _require(
            entry.get("messaging_restriction") is restricts,
            f"{path}: only the dominant verdict restricts wording; a mixed, tied, inconclusive, "
            "or incomplete comparison imposes none",
        )
        forbidden = entry.get("forbidden_claim_classes")
        _require(isinstance(forbidden, list), f"{path}: forbidden_claim_classes is a list")
        if restricts:
            _require(
                entry.get("permitted_claim_class")
                == "measured_improvement_over_previous_static_baseline",
                f"{path}: dominance permits measured improvement over the previous static baseline",
            )
            _require(
                sorted(forbidden) == sorted(("best_measured", "efficient", "optimal")),
                f"{path}: dominance forbids the efficient, optimal, and best_measured classes",
            )
            _require(
                entry.get("restriction_scope") == "release_wording_only"
                and entry.get("static_defaults_may_still_ship") is True,
                f"{path}: the restriction reaches release wording alone, so a mechanical consumer "
                "cannot read it as a bar on shipping the static defaults",
            )
        else:
            _require(
                entry.get("permitted_claim_class") == "no_comparative_claim",
                f"{path}: a non-dominant verdict permits no comparative claim",
            )
            _require(
                not forbidden,
                f"{path}: a forbidden set IS a restriction, and FR-022 imposes none here",
            )


def validate_comparison(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    """Fail-closed comparison semantics: identity, frozen sets, and the messaging map."""
    require_utc_timestamp(contract.get("frozen_at"), "frozen_at")
    # FR-005a and SC-018, on the path every consumer takes. The shared verifier
    # raises in its own module's currency; restate it in this module's so a
    # caller catching ControlComparisonError still sees a binding drift.
    try:
        verify_car_003_bindings(contract)
    except ControlContractError as exc:
        raise ControlComparisonError(str(exc)) from exc
    _validate_eligibility_floors(contract)
    _validate_dominance_rule(contract)
    _validate_multiplicity_position(contract)
    _validate_messaging_map(contract)

    recomputed = record_digest(contract, digest_field="comparison_digest")
    _require(
        contract.get("comparison_digest") == recomputed,
        f"comparison_digest does not recompute: recorded {contract.get('comparison_digest')!r}, "
        f"recomputed {recomputed!r}",
    )
    return contract


def load_comparison(path: Path = FROZEN_COMPARISON_PATH) -> dict[str, Any]:
    """Load the frozen comparison instance, schema-validate it, then check semantics."""
    contract = load_contract(path)
    validate_instance(contract, COMPARISON_SCHEMA, path="comparison")
    validate_comparison(contract)
    return contract


# --------------------------------------------------------------------------- #
# Stage zero: the dimension-name projection (FR-021e)                           #
# --------------------------------------------------------------------------- #


def project_resource_vector(resource_vector: Mapping[str, Any]) -> dict[str, Any]:
    """Carry a frozen resource vector onto the frozen decision-vector names.

    The single frozen rename is read from the committed contract rather than
    transcribed. Any key outside the eight frozen dimensions raises, so an
    unprojected or over-wide vector never silently compares under two names for
    one quantity.
    """
    _require(isinstance(resource_vector, Mapping), "a resource vector is an object")
    projection = COMPARISON_SCHEMA["$defs"]["dimensionProjection"]["properties"]
    renames = {source: node["const"] for source, node in projection.items()}

    projected: dict[str, Any] = {}
    for key, value in resource_vector.items():
        name = renames.get(key, key)
        _require(
            name in FROZEN_DIMENSIONS,
            f"{key!r} is outside the eight frozen Pareto dimensions {sorted(FROZEN_DIMENSIONS)}; "
            "an unprojected vector raises rather than comparing",
        )
        _require(
            name not in projected,
            f"{key!r} and its projected name {name!r} are two names for one quantity",
        )
        projected[name] = value
    return projected


# --------------------------------------------------------------------------- #
# Stage one: the eligibility floors (FR-019)                                    #
# --------------------------------------------------------------------------- #


def check_eligibility_floors(arm: Mapping[str, Any], contract: Mapping[str, Any]) -> bool:
    """Whether an arm cleared every mandatory gate and floor.

    Returns ``False`` — never a verdict — when any mandatory contract, safety,
    quality, reliability, or availability floor is unmet or simply unrecorded:
    a floor with no evidence has not been cleared. The resource numbers are never
    read here, so an ineligible control yields no verdict whatever they say.
    """
    _require(isinstance(arm, Mapping), "an arm is an object")
    floors = _block(contract, "eligibility_floors")

    gates = arm.get("deterministic_gates")
    _require(isinstance(gates, list), "an arm records its deterministic gates as a list")
    passed = set()
    for position, entry in enumerate(gates):
        _require(isinstance(entry, Mapping), f"deterministic_gates[{position}] is not an object")
        gate = entry.get("gate")
        _require(
            gate in FROZEN_GATES,
            f"deterministic_gates[{position}]: {gate!r} is not a member of the frozen gate enum",
        )
        if entry.get("pass") is True:
            passed.add(gate)

    if any(gate not in passed for gate in floors["required_gates"]):
        return False
    if arm.get("quality_floors_met") is not True:
        return False
    if arm.get("reliability_guardrails_respected") is not True:
        return False
    # Read strictly, not truthily: an absent member would otherwise disable the
    # gate rather than fail the arm, which is the wrong direction for a floor.
    _require(
        floors.get("availability_gate_required") is True,
        "eligibility_floors.availability_gate_required is frozen at true; a contract that "
        "omits it cannot be used to clear an arm",
    )
    if arm.get("availability_gate_passed") is not True:
        return False
    return True


# --------------------------------------------------------------------------- #
# Stage two: the frozen environment-independent Pareto rule (FR-020)            #
# --------------------------------------------------------------------------- #


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _exact(value: int | float) -> Decimal:
    """The decimal the contract's JSON source actually wrote.

    ``json.load`` turns the literal ``0.3`` into the nearest binary float, which
    is not three tenths. Routing through ``repr`` — the shortest string that
    round-trips — recovers the written decimal, so the margin below is tested in
    the base the contract was authored in rather than in binary.
    """
    return Decimal(str(value))


def _require_projected(vector: Any, label: str) -> Mapping[str, Any]:
    """FR-021e: the comparison stages read projected names and nothing else."""
    _require(isinstance(vector, Mapping), f"the {label} vector is an object")
    outside = sorted(set(vector) - set(FROZEN_DIMENSIONS))
    _require(
        not outside,
        f"the {label} vector carries {outside} outside the eight frozen dimensions "
        f"{sorted(FROZEN_DIMENSIONS)}; project it before comparing",
    )
    return vector


def pareto_verdict(
    candidate: Mapping[str, Any], comparator: Mapping[str, Any], contract: Mapping[str, Any]
) -> str:
    """Resolve two projected vectors under the frozen Pareto rule.

    Returns ``candidate_dominant``, ``comparator_dominant``, ``tied``, or
    ``mixed``. No weight is imported or accepted: each dimension is read under
    its own declared direction and nothing is combined into a scalar.

    An absent or null value on any dimension leaves the comparison incomplete,
    and a differing terminal state leaves it categorically unresolved; both are
    reported as ``mixed``, which ``compare`` turns into ``inconclusive`` under
    FR-022. The FR-016a severity rank is never read here.
    """
    rule = _block(contract, "dominance_rule")
    margin_map = rule["margin_map"]
    _require_projected(candidate, "candidate")
    _require_projected(comparator, "comparator")

    better = False
    worse = False
    for dimension in rule["dimensions"]:
        direction = margin_map[dimension]["direction"]
        left = candidate.get(dimension)
        right = comparator.get(dimension)
        if left is None or right is None:
            return MIXED
        if direction == "equal_only":
            if left != right:
                return MIXED
            continue
        _require(
            _is_number(left) and _is_number(right),
            f"{dimension} is compared under {direction!r} but carries a non-numeric value",
        )
        _require(
            direction in ("lower_is_better", "higher_is_better"),
            f"{dimension}: {direction!r} is not a comparison direction the rule reads",
        )
        if left == right:
            continue
        improved = left < right if direction == "lower_is_better" else left > right
        better = better or improved
        worse = worse or not improved

    if better and worse:
        return MIXED
    if better:
        return CANDIDATE_DOMINANT
    if worse:
        return COMPARATOR_DOMINANT
    return TIED


# --------------------------------------------------------------------------- #
# Stage three: the materiality margin (FR-021, FR-021c, FR-021d)                #
# --------------------------------------------------------------------------- #


def materiality_filter(
    candidate: Mapping[str, Any], comparator: Mapping[str, Any], contract: Mapping[str, Any]
) -> dict[str, str]:
    """Test each margin-eligible component against the frozen relative margin.

    Keyed by the margin-eligible dimensions alone: the four no-worse-only
    dimensions are absent because none of them can ever supply material
    dominance. The denominator is the comparator's value, and a zero comparator
    records ``margin_not_computable`` rather than an infinite or hundred-percent
    improvement.
    """
    rule = _block(contract, "dominance_rule")
    method = _block(contract, "confidence_method")
    _require(
        method.get("replay_point_estimate_stand_in") is True,
        "a one-sided lower confidence bound needs a sampling distribution; this contract "
        "declares no replay point-estimate stand-in, so no bound is invented here",
    )
    _require_projected(candidate, "candidate")
    _require_projected(comparator, "comparator")

    per_component: dict[str, str] = {}
    for dimension, entry in rule["margin_map"].items():
        if entry["class"] != MARGIN_ELIGIBLE:
            continue
        denominator = comparator.get(dimension)
        value = candidate.get(dimension)
        if not _is_number(denominator) or not _is_number(value) or denominator == 0:
            per_component[dimension] = MARGIN_NOT_COMPUTABLE
            continue
        base, observed = _exact(denominator), _exact(value)
        if entry["direction"] == "lower_is_better":
            improvement = (base - observed) / base
        else:
            improvement = (observed - base) / base
        # FR-021d: the point estimate stands in for the one-sided lower bound on
        # the single deterministic row the replay fixtures exercise. The test is
        # exact — a candidate sitting on the declared boundary must not change
        # verdict with the scale its inputs happen to be recorded in.
        per_component[dimension] = (
            CLEARED if improvement >= _exact(entry["relative_margin"]) else NOT_CLEARED
        )
    return per_component


# --------------------------------------------------------------------------- #
# The three stages, in the frozen order (FR-021a)                               #
# --------------------------------------------------------------------------- #

STAGE_FLOORS, STAGE_PARETO, STAGE_MATERIALITY = EVALUATION_ORDER


def _arm_vector(arm: Mapping[str, Any], label: str) -> Mapping[str, Any]:
    vector = arm.get("resource_vector")
    _require(isinstance(vector, Mapping), f"the {label} arm records no resource_vector")
    return vector  # type: ignore[return-value]


def compare(
    candidate: Mapping[str, Any], comparator: Mapping[str, Any], contract: Mapping[str, Any]
) -> dict[str, Any]:
    """Run the three stages in the frozen order over two arms.

    Returns ``{verdict, per_component, stage_reached}``. ``verdict`` is a member
    of the closed three-member enum, or the eligibility stage's own no-verdict
    outcome — which FR-024a keeps out of that enum — when a floor was unmet.
    ``stage_reached`` names the last stage the comparison entered, so the margin
    is visibly never reached except on candidate dominance.
    """
    # Both arms are read before either verdict is taken. Short-circuiting on the
    # candidate would let a structurally malformed comparator return a clean
    # no-verdict, which reads as a comparison that ran when half of it never did.
    candidate_eligible = check_eligibility_floors(candidate, contract)
    comparator_eligible = check_eligibility_floors(comparator, contract)
    if not candidate_eligible or not comparator_eligible:
        return {"verdict": NO_VERDICT, "per_component": {}, "stage_reached": STAGE_FLOORS}

    candidate_vector = project_resource_vector(_arm_vector(candidate, "candidate"))
    comparator_vector = project_resource_vector(_arm_vector(comparator, "comparator"))

    outcome = pareto_verdict(candidate_vector, comparator_vector, contract)
    if outcome != CANDIDATE_DOMINANT:
        verdict = (
            VERDICT_NOT_DOMINANT if outcome == COMPARATOR_DOMINANT else VERDICT_INCONCLUSIVE
        )
        return {"verdict": verdict, "per_component": {}, "stage_reached": STAGE_PARETO}

    per_component = materiality_filter(candidate_vector, comparator_vector, contract)
    verdict = (
        VERDICT_DOMINANT if CLEARED in per_component.values() else VERDICT_NOT_DOMINANT
    )
    return {
        "verdict": verdict,
        "per_component": per_component,
        "stage_reached": STAGE_MATERIALITY,
    }


# --------------------------------------------------------------------------- #
# The verdict-to-claim-class mapping (FR-024, FR-024a)                          #
# --------------------------------------------------------------------------- #


def claim_class(verdict: str, contract: Mapping[str, Any]) -> dict[str, Any]:
    """The one permitted wording class for an outcome the procedure can reach.

    Total over the three verdicts **and** over the eligibility stage's own
    no-verdict outcome, whose class is read from the eligibility block rather
    than from a fourth messaging-map row: the verdict enum still carries exactly
    three members. Only the dominant verdict carries a forbidden set and a true
    restriction flag, and its entry records that the restriction reaches release
    wording alone.
    """
    if verdict == NO_VERDICT:
        floors = _block(contract, "eligibility_floors")
        permitted = floors.get("claim_class_when_floor_unmet")
        _require(
            isinstance(permitted, str) and permitted,
            "the eligibility block declares no claim class for its no-verdict outcome",
        )
        return {
            "permitted_claim_class": permitted,
            "forbidden_claim_classes": [],
            "messaging_restriction": floors.get("messaging_restriction_when_floor_unmet"),
        }

    entry = _block(contract, "messaging_map").get(verdict)
    _require(
        isinstance(entry, Mapping),
        f"{verdict!r} is not an outcome the frozen decision procedure reaches; the lookup is "
        f"total over {sorted(VERDICTS)} and the {NO_VERDICT!r} outcome, and nothing else",
    )
    looked_up = dict(entry)  # type: ignore[arg-type]
    looked_up["forbidden_claim_classes"] = list(entry.get("forbidden_claim_classes", ()))
    return looked_up


__all__ = (
    "CANDIDATE_DOMINANT",
    "CLEARED",
    "COMPARATOR_DOMINANT",
    "COMPARISON_SCHEMA",
    "ELIGIBILITY_FLOOR_MEMBERS",
    "EVALUATION_ORDER",
    "FROZEN_COMPARISON_PATH",
    "FROZEN_COMPARISON_SCHEMA_PATH",
    "FROZEN_DIMENSIONS",
    "FROZEN_GATES",
    "FROZEN_MULTIPLICITY_FAMILIES",
    "FROZEN_RESOURCE_VECTOR_MEMBERS",
    "MARGIN_DENOMINATOR",
    "MARGIN_ELIGIBLE",
    "MARGIN_ELIGIBLE_DIMENSIONS",
    "MARGIN_NOT_COMPUTABLE",
    "MIXED",
    "NOT_CLEARED",
    "NO_VERDICT",
    "NO_WORSE_ONLY",
    "STAGE_FLOORS",
    "STAGE_MATERIALITY",
    "STAGE_PARETO",
    "TIED",
    "VERDICTS",
    "VERDICT_DOMINANT",
    "VERDICT_INCONCLUSIVE",
    "VERDICT_NOT_DOMINANT",
    "ControlComparisonError",
    "check_eligibility_floors",
    "claim_class",
    "compare",
    "load_comparison",
    "materiality_filter",
    "pareto_verdict",
    "project_resource_vector",
    "validate_comparison",
)
