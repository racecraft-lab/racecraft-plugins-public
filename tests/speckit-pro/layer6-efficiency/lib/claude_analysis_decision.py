#!/usr/bin/env python3
"""CAR-003 decision ladder, Pareto dominance, terminal mapping, and replay.

The ladder is **ordered and short-circuiting**: bindings, partition, treatment,
deterministic, provenance, and completeness gates, then absolute semantic and
reliability floors, then task-paired cluster-adjusted non-inferiority, and only
then Pareto dominance over the eight raw dimensions. A stage that was not reached
records ``not_evaluated`` rather than being omitted, because an omitted stage and
a passed stage read identically and SC-007 is a claim about *order* rather than
about outcomes (FR-017, FR-018).

**Direction of preference is what makes dominance decidable** (FR-058). "No worse
on every dimension" has no meaning until each dimension says which way is worse,
and two conforming implementations could otherwise reach opposite verdicts on
identical evidence. Six resource dimensions are lower-is-better, acceptance is
higher-is-better, and terminal state is categorical and unordered — a candidate is
"no worse" on terminal state only when it *equals* the comparator's, and any
difference makes the whole comparison mixed rather than being silently read as
better or worse.

``reasoning_output_tokens`` is recorded and reported beside every dominance result
and is never a dimension while the twin's frozen policy omits it. The field is
disjoint from ``output_tokens`` and is billed, so the exclusion is a **stated
limitation, not a claim the cost is absent**, and adding it must be a joint
cross-platform change (FR-049).

Three design points the requirements left for the implementation, stated here so
a reviewer can see them rather than infer them:

* **"Failed gate" names two different things.** FR-019 routes a failed
  deterministic hard gate to ``no_qualification`` — the evidence was sufficient
  and the bar was not cleared — while a failed *bindings* gate is a
  ``binding_failure`` and routes to ``invalid``. Both record the closed
  ``gate_failed`` reason, because the published ``decision_reasons`` enumeration
  carries no binding-specific member and is a parity mirror that must not gain
  one unilaterally. The distinction therefore lives in the terminal member, which
  is exactly where SC-011 requires replay to reproduce it.
* **An unobservable environment has no reason member of its own.** FR-051 records
  it on the evidence-boundary plane with ``required_evidence_missing`` and returns
  inconclusive; in decision-reason vocabulary that is ``evidence_incomplete``. No
  member is coined for it.
* **``analysis_output.floor_result`` is closed to three members** and cannot carry
  ``not_evaluated``, unlike the ordered gate results. A floor stage that was never
  reached therefore summarizes as ``uncertain`` in the analysis output while the
  ordered ladder still records ``not_evaluated`` — the FR-017 obligation is
  discharged by the ladder, which is the surface that states it.

Nothing here can force a weighted ranking, and no scalar score, per-category
weight, or price coefficient may appear anywhere in a decision bundle. Published
price data is diagnostic context only (FR-019). ``qualified`` is unreachable from
a calibration partition, so CAR-003 structurally cannot emit a final preferred or
fallback route policy (FR-024).

This module is repository-only harness code and makes **no live model calls**:
every decision here is replayed from a recorded fixture.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

# ``_parse_timestamp`` is reused rather than reimplemented: an ISO instant is
# only comparable once it is parsed and normalized to UTC, and a second parser
# would be a second place for the two modules to disagree about what "before"
# means.
if __package__:  # pragma: no cover - the lib is imported flat by the suite
    from .claude_score_bundle import REASONING_TOKEN_LIMITATION
    from .claude_successor_freeze import _parse_timestamp, record_digest
else:
    from claude_score_bundle import REASONING_TOKEN_LIMITATION
    from claude_successor_freeze import _parse_timestamp, record_digest


REPO_ROOT = Path(__file__).resolve().parents[4]
LAYER6_ROOT = REPO_ROOT / "tests" / "speckit-pro" / "layer6-efficiency"
REPLAY_FIXTURE_PATH = LAYER6_ROOT / "fixtures" / "car-003-calibration-replay.json"

# FR-037. 1.1.0 substitutes the calibration protocol for the analysis plan on a
# qualification-ineligible decision. Under 1.0.0 the plan binding was required
# unconditionally, so a calibration bundle -- produced before any plan exists --
# could only satisfy the contract by carrying the protocol's {id, digest} under
# the plan's name. The contract still accepts 1.0.0 so evidence already sealed
# under it stays conforming to the version it declared.
SCHEMA_VERSION = "1.1.0"


class AnalysisDecisionError(AssertionError):
    """Fail-closed error for a refused stage, dimension, condition, or stop."""


# ---------------------------------------------------------------------------
# The ordered ladder (FR-017, FR-018)
# ---------------------------------------------------------------------------

LADDER_GATES = (
    "bindings",
    "partition",
    "treatment",
    "deterministic",
    "provenance",
    "completeness",
    "floors",
    "non_inferiority",
    "pareto",
)
GATE_RESULTS = ("pass", "fail", "uncertain", "not_evaluated")
NOT_EVALUATED = "not_evaluated"


def evaluate_ladder(stage_results: Mapping[str, str]) -> tuple[dict[str, str], ...]:
    """Return every stage in order, short-circuiting at the first non-pass.

    Each stage is emitted even when it was never reached, because omitting an
    unreached stage makes it indistinguishable from one that passed.
    """
    for gate, result in stage_results.items():
        if gate not in LADDER_GATES:
            raise AnalysisDecisionError(f"{gate!r} is not a member of the closed ladder")
        if result not in GATE_RESULTS:
            raise AnalysisDecisionError(f"{result!r} is not a closed ladder result")

    ordered: list[dict[str, str]] = []
    reached = True
    for gate in LADDER_GATES:
        if not reached:
            ordered.append({"gate": gate, "result": NOT_EVALUATED})
            continue
        result = stage_results.get(gate, NOT_EVALUATED)
        ordered.append({"gate": gate, "result": result})
        if result != "pass":
            reached = False
    return tuple(ordered)


def stage_reachable(ordered: Sequence[Mapping[str, str]], gate: str) -> bool:
    """True when every stage *before* ``gate`` passed, so ``gate`` is evaluated.

    Reachability is a property of the stages ahead of a gate, not of the gate's
    own recorded result: a stage whose result has not been computed yet still
    reads ``not_evaluated``, so asking whether the gate itself was evaluated
    would report every unreached and every not-yet-computed stage identically.
    """
    for entry in ordered:
        if entry["gate"] == gate:
            return True
        if entry["result"] != "pass":
            return False
    return False


# ---------------------------------------------------------------------------
# Pareto dominance over exactly eight dimensions (FR-018, FR-049, FR-058)
# ---------------------------------------------------------------------------

PARETO_DIMENSIONS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "duration",
    "retries",
    "compactions",
    "acceptance",
    "terminal_state",
)

LOWER_IS_BETTER = "lower_is_better"
HIGHER_IS_BETTER = "higher_is_better"
CATEGORICAL_UNORDERED = "categorical_unordered"

DIRECTION_OF_PREFERENCE: Mapping[str, str] = MappingProxyType(
    {
        "input_tokens": LOWER_IS_BETTER,
        "cached_input_tokens": LOWER_IS_BETTER,
        "output_tokens": LOWER_IS_BETTER,
        "duration": LOWER_IS_BETTER,
        "retries": LOWER_IS_BETTER,
        "compactions": LOWER_IS_BETTER,
        "acceptance": HIGHER_IS_BETTER,
        "terminal_state": CATEGORICAL_UNORDERED,
    }
)

# FR-018, FR-049: recorded and reported, never compared.
REASONING_TOKEN_FIELD = "reasoning_output_tokens"
DIAGNOSTIC_ONLY_FIELDS = (
    REASONING_TOKEN_FIELD,
    "cache_write_tokens_by_ttl_class",
    "cache_read_tokens",
)

PARETO_RESULTS = (
    "candidate_dominates",
    "comparator_dominates",
    "tie",
    "mixed",
    "uncertain",
    "not_evaluated",
)


@dataclass(frozen=True)
class ParetoResult:
    """One dominance comparison with its per-dimension derivation kept visible."""

    result: str
    better_on: tuple[str, ...] = field(default_factory=tuple)
    worse_on: tuple[str, ...] = field(default_factory=tuple)
    equal_on: tuple[str, ...] = field(default_factory=tuple)
    mixed_on: tuple[str, ...] = field(default_factory=tuple)
    uncertain_on: tuple[str, ...] = field(default_factory=tuple)


def compare_dimension(dimension: str, candidate: Any, comparator: Any) -> str:
    """Compare one dimension under its declared direction of preference."""
    direction = DIRECTION_OF_PREFERENCE.get(dimension)
    if direction is None:
        raise AnalysisDecisionError(
            f"{dimension!r} is not one of the eight decision-bearing dimensions"
        )
    if candidate is None or comparator is None:
        return "uncertain"
    if direction == CATEGORICAL_UNORDERED:
        # Unordered: equal is "no worse", and any difference is mixed. Treating a
        # terminal-state change as an improvement or a regression would impose an
        # ordering the requirement explicitly withholds.
        return "equal" if candidate == comparator else "mixed"
    if candidate == comparator:
        return "equal"
    if direction == LOWER_IS_BETTER:
        return "better" if candidate < comparator else "worse"
    return "better" if candidate > comparator else "worse"


def pareto_compare(
    candidate_vector: Mapping[str, Any], comparator_vector: Mapping[str, Any]
) -> ParetoResult:
    """Dominance over exactly the eight dimensions, refusing a ninth."""
    for label, vector in (("candidate", candidate_vector), ("comparator", comparator_vector)):
        extra = tuple(sorted(set(vector) - set(PARETO_DIMENSIONS)))
        if extra:
            raise AnalysisDecisionError(
                f"the {label} vector carries non-dimension fields {extra}; the decision "
                "vector stays at the eight of FR-018 and additions are a joint "
                "cross-platform change"
            )

    buckets: dict[str, list[str]] = {
        "better": [],
        "worse": [],
        "equal": [],
        "mixed": [],
        "uncertain": [],
    }
    for dimension in PARETO_DIMENSIONS:
        verdict = compare_dimension(
            dimension, candidate_vector.get(dimension), comparator_vector.get(dimension)
        )
        buckets[verdict].append(dimension)

    better = tuple(buckets["better"])
    worse = tuple(buckets["worse"])
    equal = tuple(buckets["equal"])
    mixed = tuple(buckets["mixed"])
    uncertain = tuple(buckets["uncertain"])

    if uncertain:
        result = "uncertain"
    elif mixed:
        result = "mixed"
    elif better and not worse:
        result = "candidate_dominates"
    elif worse and not better:
        result = "comparator_dominates"
    elif not better and not worse:
        result = "tie"
    else:
        result = "mixed"
    return ParetoResult(result, better, worse, equal, mixed, uncertain)


def reasoning_token_report(reasoning_output_tokens_total: int | None) -> dict[str, Any]:
    """FR-049: reported for every attempt, decision-bearing for none."""
    return {
        "reasoning_output_tokens_total": reasoning_output_tokens_total,
        "decision_bearing": False,
        "stated_limitation": REASONING_TOKEN_LIMITATION,
    }


def dominance_with_reasoning_report(
    candidate_vector: Mapping[str, Any],
    comparator_vector: Mapping[str, Any],
    *,
    reasoning_output_tokens_total: int | None,
) -> dict[str, Any]:
    """Emit the dominance result and its reasoning-token report together."""
    result = pareto_compare(candidate_vector, comparator_vector)
    return {
        "pareto_result": result.result,
        "better_on": list(result.better_on),
        "worse_on": list(result.worse_on),
        "mixed_on": list(result.mixed_on),
        "uncertain_on": list(result.uncertain_on),
        "reasoning_token_report": reasoning_token_report(reasoning_output_tokens_total),
    }


# ---------------------------------------------------------------------------
# Terminal mapping and the no-weighting guards (FR-019, FR-024)
# ---------------------------------------------------------------------------

TERMINAL_STATES = (
    "qualified",
    "no_qualification",
    "inconclusive",
    "calibration_complete",
    "invalid",
)

DECISION_REASONS = (
    "none",
    "gate_failed",
    "floors_failed",
    "non_inferiority_failed",
    "pareto_tie",
    "pareto_mixed",
    "evidence_incomplete",
    "statistical_uncertainty",
    "partition_not_eligible",
    "rerun_cap_exhausted",
    "attrition_cap_exceeded",
    "unclassifiable_attrition",
    "trace_reference_integrity_failure",
    "budget_exhausted",
    "calibration_only",
)

TERMINAL_BY_CONDITION: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        # Evidence was sufficient; the bar was not cleared.
        "failed_gate": ("no_qualification", "gate_failed"),
        "failed_floor": ("no_qualification", "floors_failed"),
        "failed_non_inferiority": ("no_qualification", "non_inferiority_failed"),
        # Evidence could not decide.
        "pareto_tie": ("inconclusive", "pareto_tie"),
        "mixed_dominance": ("inconclusive", "pareto_mixed"),
        "statistical_uncertainty": ("inconclusive", "statistical_uncertainty"),
        "incomplete_evidence": ("inconclusive", "evidence_incomplete"),
        "rerun_cap_exhausted": ("inconclusive", "rerun_cap_exhausted"),
        "attrition_cap_exceeded": ("inconclusive", "attrition_cap_exceeded"),
        "unclassifiable_attrition": ("inconclusive", "unclassifiable_attrition"),
        "unobservable_environment": ("inconclusive", "evidence_incomplete"),
        "campaign_budget_exhausted": ("inconclusive", "budget_exhausted"),
        # The record itself cannot be trusted.
        "binding_failure": ("invalid", "gate_failed"),
        "partition_not_eligible": ("invalid", "partition_not_eligible"),
        "reference_integrity_failure": ("invalid", "trace_reference_integrity_failure"),
        # The calibration partition ran to completion.
        "calibration_partition_complete": ("calibration_complete", "calibration_only"),
    }
)

# Worst-wins precedence. A record that cannot be trusted outranks one that could
# not decide, which outranks one that decided against the candidate.
_TERMINAL_PRECEDENCE = {
    "qualified": 0,
    "calibration_complete": 0,
    "no_qualification": 1,
    "inconclusive": 2,
    "invalid": 3,
}


@dataclass(frozen=True)
class TerminalDecision:
    """One terminal member with every reason that contributed to it."""

    decision: str
    decision_reasons: tuple[str, ...]


def terminal_for(condition: str) -> tuple[str, str]:
    """Map one fired condition onto its closed terminal member and reason."""
    try:
        return TERMINAL_BY_CONDITION[condition]
    except KeyError:
        raise AnalysisDecisionError(
            f"{condition!r} has no mapped terminal member; an unmapped condition would "
            "block a decision with no recordable reason"
        ) from None


def resolve_terminal(
    conditions: Iterable[str], *, qualification_eligible: bool
) -> TerminalDecision:
    """Resolve every fired condition into one terminal member and its reasons."""
    fired = tuple(dict.fromkeys(conditions))
    if not fired:
        if qualification_eligible:
            return TerminalDecision("qualified", ("none",))
        # FR-024: calibration is never qualification-eligible, so a clean
        # calibration partition completes rather than qualifying.
        state, reason = terminal_for("calibration_partition_complete")
        return TerminalDecision(state, (reason,))

    states: list[str] = []
    reasons: list[str] = []
    for condition in fired:
        state, reason = terminal_for(condition)
        states.append(state)
        reasons.append(reason)
    decision = max(states, key=lambda state: _TERMINAL_PRECEDENCE[state])
    if decision == "qualified" and not qualification_eligible:  # pragma: no cover - unreachable
        decision = "calibration_complete"
    return TerminalDecision(decision, tuple(sorted(dict.fromkeys(reasons))))


# FR-019: no weighted ranking may be forced. "price" alone is permitted as
# diagnostic context; a price *coefficient* is not.
WEIGHTING_KEY_MARKERS = (
    "weight",
    "coefficient",
    "scalar_score",
    "composite_score",
    "ranking",
)

# FR-024: CAR-003 creates none of these.
FORBIDDEN_OUTPUT_KEYS = (
    "preferred_route_policy",
    "fallback_route_policy",
    "installed_default",
    "aggregate_identity",
    "release_claim",
    "cohort_decision",
)


def _walk_keys(record: Any, path: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(record, Mapping):
        for key, value in record.items():
            where = f"{path}.{key}" if path else str(key)
            yield (str(key), where)
            yield from _walk_keys(value, where)
    elif isinstance(record, (list, tuple)):
        for index, value in enumerate(record):
            yield from _walk_keys(value, f"{path}[{index}]")


def weighting_findings(record: Any) -> tuple[str, ...]:
    """Name every field that would force a weighted ranking or a scalar score."""
    return tuple(
        f"{where} would force a weighted ranking or scalar score"
        for key, where in _walk_keys(record)
        if any(marker in key.lower() for marker in WEIGHTING_KEY_MARKERS)
    )


def final_output_findings(record: Any) -> tuple[str, ...]:
    """FR-024: name every final route policy, default, identity, or release claim."""
    forbidden = frozenset(FORBIDDEN_OUTPUT_KEYS)
    return tuple(
        f"{where} creates a final decision CAR-003 may not create"
        for key, where in _walk_keys(record)
        if key.lower() in forbidden
    )


# ---------------------------------------------------------------------------
# Estimand retention, campaign truncation, and rerun governance (FR-020, FR-021, FR-056)
# ---------------------------------------------------------------------------

ESTIMAND_RETAINED_CODES = (
    "candidate_failed",
    "candidate_timed_out",
    "candidate_cancelled",
    "candidate_budget_exhausted",
    "candidate_abandoned",
)
CANDIDATE_FAILURE_ACCEPTANCE = 0
COMPLETE_CASE_FILTERING = False

RERUN_SCOPE = "complete_pair"
CLASSIFICATION_TIMING = "arm_blind_before_outcome_read"
CLASSIFICATION_RECORD_KIND = "transient_classification"


def retained_in_estimand(failure_code: str) -> bool:
    """FR-020: candidate-caused outcomes stay in their pairs, never filtered out."""
    return failure_code in ESTIMAND_RETAINED_CODES


def estimand_acceptance(failure_code: str) -> int:
    """A retained candidate-plane outcome enters the estimand at acceptance zero."""
    if not retained_in_estimand(failure_code):
        raise AnalysisDecisionError(
            f"{failure_code!r} is not a candidate-plane outcome retained in the estimand"
        )
    return CANDIDATE_FAILURE_ACCEPTANCE


@dataclass(frozen=True)
class CampaignStop:
    """A campaign ceiling reached between the two arms of one pair (FR-056)."""

    assignment_id: str
    failure_plane: str
    failure_code: str
    pair_status: str
    one_arm_rerun_permitted: bool
    terminal_condition: str


def classify_campaign_ceiling_stop(*, assignment_id: str, arms_completed: int) -> CampaignStop:
    """An administrative truncation of the harness, never a candidate property.

    Recording it as ``candidate_budget_exhausted`` would attribute a harness stop
    to the candidate, and because which arm is truncated depends on assigned
    order, that misattribution would be order-correlated.
    """
    if arms_completed >= 2:
        raise AnalysisDecisionError(
            "a completed pair was not truncated between arms; classify_campaign_ceiling_stop "
            "records the between-arms case only"
        )
    return CampaignStop(
        assignment_id=assignment_id,
        failure_plane="infrastructure",
        failure_code="infrastructure_failure",
        pair_status="incomplete",
        one_arm_rerun_permitted=False,
        terminal_condition="campaign_budget_exhausted",
    )


def build_transient_classification_record(
    *, record_id: str, arm_blind_evidence_digest: str, recorded_at: str
) -> dict[str, Any]:
    """FR-021: the evidence half of the arm-blind precommitment.

    Pinning ``classification_timing`` in the frozen policy is a precommitment and
    is not by itself evidence that it held, so a rerun binds this record and its
    timestamp is compared against the arms' outcome digests.
    """
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_kind": CLASSIFICATION_RECORD_KIND,
        "classification_id": record_id,
        "classification_timing": CLASSIFICATION_TIMING,
        "arm_blind_evidence_digest": arm_blind_evidence_digest,
        "recorded_at": recorded_at,
    }
    record["classification_digest"] = record_digest(record, digest_field="classification_digest")
    return record


@dataclass(frozen=True)
class RerunVerdict:
    """Whether one capped, complete-pair, arm-symmetric rerun may be granted."""

    granted: bool
    pair_result: str
    failure_condition: str = "none"
    findings: tuple[str, ...] = field(default_factory=tuple)


def attempts_for_reruns(reruns: int) -> int:
    """FR-021: the cap counts reruns; each rerun of a pair is two attempts."""
    return reruns * 2


def grant_rerun(
    *,
    classification_record: Mapping[str, Any] | None,
    arm_outcome_digest_timestamps: Sequence[str],
    cap: int,
    reruns_used: int,
    scope: str,
) -> RerunVerdict:
    """Grant a rerun only when every FR-021 precondition is evidenced."""
    findings: list[str] = []
    if scope != RERUN_SCOPE:
        findings.append(
            f"scope {scope!r} is not {RERUN_SCOPE!r}: exclusion is complete-pair and "
            "arm-symmetric, and a one-arm rerun is never granted"
        )
    if reruns_used >= cap:
        return RerunVerdict(
            False,
            "inconclusive",
            "rerun_cap_exhausted",
            tuple(findings + [f"the per-pair rerun cap of {cap} is exhausted"]),
        )
    if findings:
        return RerunVerdict(False, "inconclusive", "incomplete_evidence", tuple(findings))

    if classification_record is None:
        return RerunVerdict(
            False,
            "inconclusive",
            "incomplete_evidence",
            ("no transient-classification record is bound to this rerun",),
        )
    recorded = classification_record.get("classification_digest")
    if recorded != record_digest(classification_record, digest_field="classification_digest"):
        findings.append("the transient-classification record does not match its own digest")
    if classification_record.get("classification_timing") != CLASSIFICATION_TIMING:
        findings.append(f"classification_timing must be {CLASSIFICATION_TIMING!r}")
    # Instants, not strings. ``2026-07-01T09:00:00-06:00`` sorts below
    # ``2026-07-01T12:00:00Z`` as text while being three hours later in fact, so
    # a textual comparison reads a post-dated classification as arm-blind and
    # silently readmits the outcome-conditioned filtering FR-021 forbids. A
    # timestamp that will not parse is refused rather than ordered.
    recorded_at = classification_record.get("recorded_at")
    recorded_instant = _parse_timestamp(recorded_at)
    if recorded_instant is None:
        findings.append(
            f"the transient-classification recorded_at {recorded_at!r} is not a parseable "
            "instant, so it cannot be shown to pre-date the arm outcomes"
        )
    if not arm_outcome_digest_timestamps:
        findings.append(
            "no arm outcome digest timestamp is bound to this rerun, so the arm-blind "
            "precommitment has nothing to be checked against"
        )
    for outcome_timestamp in arm_outcome_digest_timestamps:
        outcome_instant = _parse_timestamp(outcome_timestamp)
        if outcome_instant is None:
            findings.append(
                f"the arm outcome digest timestamp {outcome_timestamp!r} is not a parseable "
                "instant, so the classification cannot be shown to pre-date it"
            )
        elif recorded_instant is not None and recorded_instant >= outcome_instant:
            findings.append(
                "the transient-classification record post-dates an arm outcome digest "
                f"({recorded_at} >= {outcome_timestamp}); classifying after outcomes are "
                "visible is outcome-conditioned filtering"
            )
    if findings:
        return RerunVerdict(False, "inconclusive", "incomplete_evidence", tuple(findings))
    return RerunVerdict(True, "granted", "none", ())


def supersede_pair(pair: Mapping[str, Any]) -> dict[str, Any]:
    """FR-021: a superseded pair is retained immutably and marked, never deleted."""
    retained = copy.deepcopy(dict(pair))
    retained["superseded"] = True
    return retained


def terminal_complete_pairs(
    pairs: Sequence[Mapping[str, Any]]
) -> tuple[Mapping[str, Any], ...]:
    """The live, complete pairs primary statistics are permitted to use."""
    return tuple(
        pair for pair in pairs if not pair.get("superseded") and pair.get("complete")
    )


def primary_statistics_findings(pairs: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    """FR-021: exactly one terminal complete pair per assignment."""
    counts: dict[str, int] = {}
    for pair in terminal_complete_pairs(pairs):
        assignment_id = str(pair.get("assignment_id"))
        counts[assignment_id] = counts.get(assignment_id, 0) + 1
    return tuple(
        f"assignment {assignment_id!r} contributes {count} terminal complete pairs; "
        "primary statistics use exactly one"
        for assignment_id, count in sorted(counts.items())
        if count != 1
    )


# ---------------------------------------------------------------------------
# Guardrails, multiplicity, racing and futility (FR-050, FR-053, FR-054, FR-055)
# ---------------------------------------------------------------------------

GUARDRAIL_DECLARATION_FIELDS = (
    "units",
    "denominator",
    "comparator",
    "margin",
    "confidence_method",
    "missing_data_rule",
    "direction",
    "multiplicity_family",
    "breach_result",
    "decision_bearing",
)
GUARDED_QUANTITIES = (
    "p95_duration_ms_max",
    "p95_input_tokens_max",
    "p95_cached_input_tokens_max",
    "p95_output_tokens_max",
)
GUARDRAIL_DENOMINATORS = (
    "per_attempt_within_stratum_arm",
    "per_pair_within_stratum",
    "per_task_within_stratum_arm",
)
GUARDRAIL_COMPARATORS = ("absolute_ceiling", "relative_to_comparator_arm")
GUARDRAIL_MISSING_DATA_RULES = ("worst_case_imputation", "report_jointly_with_attrition")
GUARDRAIL_DIRECTION = "higher_is_worse"
GUARDRAIL_BREACH_RESULT = "no_qualification"
GUARDRAIL_FAMILY = "guardrail"

MULTIPLICITY_FAMILIES = (
    "conjunctive_family",
    "pareto_disjunctive_family",
    "across_ladder_family",
)
_CLUSTER_ADJUSTMENT_MARKERS = ("cluster",)


def guardrail_findings(
    guardrail_method: Mapping[str, Any], *, non_inferiority_margins: Mapping[str, Any]
) -> tuple[str, ...]:
    """A guardrail is a complete comparison, not a bare ceiling (FR-053)."""
    findings: list[str] = []
    for declared in GUARDRAIL_DECLARATION_FIELDS:
        if declared not in guardrail_method:
            findings.append(f"guardrail_method leaves {declared} undeclared")
    if findings:
        return tuple(findings)

    units = guardrail_method["units"]
    for quantity in GUARDED_QUANTITIES:
        if quantity not in units:
            findings.append(f"guardrail_method.units declares no unit for {quantity}")
    if guardrail_method["denominator"] not in GUARDRAIL_DENOMINATORS:
        findings.append("guardrail_method.denominator is outside the closed set")
    if guardrail_method["comparator"] not in GUARDRAIL_COMPARATORS:
        findings.append("guardrail_method.comparator is outside the closed set")

    margin = guardrail_method["margin"]
    reused = margin != 0 and margin in tuple(non_inferiority_margins.values())
    if reused:
        findings.append(
            f"guardrail_method.margin {margin!r} is reused from the FR-018 non-inferiority "
            "margins; the two are distinct declarations"
        )

    confidence = guardrail_method["confidence_method"]
    if not confidence.get("method") or not 0 < float(confidence.get("confidence_level", 0)) < 1:
        findings.append("guardrail_method.confidence_method is incompletely declared")
    if guardrail_method["missing_data_rule"] not in GUARDRAIL_MISSING_DATA_RULES:
        findings.append(
            "guardrail_method.missing_data_rule must not be silent exclusion: dropping "
            "failed, timed-out, and cancelled attempts biases the percentile downward"
        )
    if guardrail_method["direction"] != GUARDRAIL_DIRECTION:
        findings.append(f"guardrail_method.direction must be {GUARDRAIL_DIRECTION!r}")

    family = guardrail_method["multiplicity_family"]
    if family.get("family") != GUARDRAIL_FAMILY:
        findings.append(
            f"guardrail_method.multiplicity_family.family must be {GUARDRAIL_FAMILY!r}: "
            "guardrails form a family distinct from the three FR-050 families"
        )
    if family.get("family") in MULTIPLICITY_FAMILIES:
        findings.append(
            "a guardrail may not be filed under one of the three FR-050 multiplicity families"
        )
    if not family.get("adjustment") or not family.get("rationale"):
        findings.append("guardrail_method.multiplicity_family is incompletely declared")
    if guardrail_method["breach_result"] != GUARDRAIL_BREACH_RESULT:
        findings.append(f"guardrail_method.breach_result must be {GUARDRAIL_BREACH_RESULT!r}")
    if guardrail_method["decision_bearing"] is not False:
        findings.append(
            "guardrail_method.decision_bearing must be false: the decision vector stays "
            "at the eight dimensions of FR-018"
        )
    return tuple(findings)


@dataclass(frozen=True)
class GuardrailBreach:
    """A breached guardrail returns no qualification and is never traded off."""

    quantity: str
    observed: Any
    ceiling: Any
    breached: bool
    result: str
    tradeable: bool = False
    decision_bearing: bool = False


def guardrail_breach(quantity: str, *, observed: Any, ceiling: Any) -> GuardrailBreach:
    """FR-053, FR-019: a breach is terminal, never weighted against a dimension."""
    breached = observed > ceiling
    return GuardrailBreach(
        quantity=quantity,
        observed=observed,
        ceiling=ceiling,
        breached=breached,
        result=GUARDRAIL_BREACH_RESULT if breached else "pass",
        tradeable=False,
        decision_bearing=False,
    )


@dataclass(frozen=True)
class GuardrailAdmissibility:
    """Whether a stratum carries enough unique tasks to support its percentile."""

    stratum_id: str
    admissible: bool
    result: str
    observed_unique_tasks: int
    stratum_minimum_unique_tasks: int
    shortfall_reported: bool


def guardrail_admissibility(
    stratum: Mapping[str, Any], *, observed_unique_tasks: int
) -> GuardrailAdmissibility:
    """FR-054: below its own floor a stratum returns inconclusive, never a pass.

    The floor is per stratum. A manifest-wide count says nothing about whether any
    single stratum can support the percentile it claims, because a corpus can
    clear a pooled floor while every individual stratum sits below its own.
    """
    floor = int(stratum["stratum_minimum_unique_tasks"])
    admissible = observed_unique_tasks >= floor
    return GuardrailAdmissibility(
        stratum_id=str(stratum.get("stratum_id")),
        admissible=admissible,
        result="admissible" if admissible else "inconclusive",
        observed_unique_tasks=observed_unique_tasks,
        stratum_minimum_unique_tasks=floor,
        shortfall_reported=not admissible,
    )


def multiplicity_findings(declaration: Mapping[str, Any]) -> tuple[str, ...]:
    """FR-050: three families addressed separately, plus a stated precondition."""
    findings: list[str] = []
    for family in MULTIPLICITY_FAMILIES:
        entry = declaration.get(family)
        if not isinstance(entry, Mapping):
            findings.append(f"the multiplicity declaration omits {family}")
            continue
        if not entry.get("adjustment"):
            findings.append(f"{family} declares no adjustment")
        if not entry.get("rationale"):
            findings.append(f"{family} declares no rationale")
        if any(
            marker in str(entry.get("adjustment", "")).lower()
            for marker in _CLUSTER_ADJUSTMENT_MARKERS
        ):
            findings.append(
                f"{family} names cluster adjustment as its multiplicity control; "
                "cluster-adjusted variance is a precondition, and no familywise or "
                "false-discovery correction repairs a mis-estimated test statistic"
            )
    conjunctive = declaration.get("conjunctive_family") or {}
    if conjunctive.get("adjustment") not in (None, "none_required"):
        findings.append(
            "conjunctive_family must be none_required: all stages must pass, so the "
            "stage controls error at alpha without adjustment"
        )
    disjunctive = declaration.get("pareto_disjunctive_family") or {}
    if disjunctive.get("adjustment") in (None, "", "none_required"):
        findings.append(
            "pareto_disjunctive_family must state how the disjunctive half is "
            "controlled: 'better on at least one dimension' inflates the spurious-win "
            "rate with each added dimension"
        )
    if declaration.get("cluster_adjustment_is_precondition") is not True:
        findings.append("cluster_adjustment_is_precondition must be true")
    return tuple(findings)


def interim_look_findings(
    policy: Mapping[str, Any], *, futility: bool = False
) -> tuple[str, ...]:
    """FR-055: every planned look, its boundary, bindingness, and stop scope."""
    findings: list[str] = []
    looks = policy.get("interim_looks")
    if not isinstance(looks, Mapping):
        return ("the declaration records no interim_looks",)
    fractions = looks.get("information_fractions")
    if not isinstance(fractions, (list, tuple)):
        findings.append("interim_looks.information_fractions is not declared")
    else:
        if looks.get("count") != len(fractions):
            findings.append(
                f"interim_looks.count {looks.get('count')!r} disagrees with its "
                f"{len(fractions)} declared information fractions"
            )
        if list(fractions) != sorted(set(fractions)):
            findings.append(
                "interim_looks.information_fractions must be unique and increasing"
            )
        findings.extend(
            f"information fraction {fraction!r} is outside (0, 1]"
            for fraction in fractions
            if not 0 < float(fraction) <= 1
        )
    boundary = policy.get("boundary") or {}
    if not boundary.get("type") or not boundary.get("rationale"):
        findings.append("the stopping boundary is incompletely declared")
    if policy.get("look_schedule_frozen") is not True:
        findings.append("look_schedule_frozen must be true")
    if policy.get("early_stop_biases_estimate") is not True:
        findings.append("early_stop_biases_estimate must be true")
    if policy.get("stop_scope") != RERUN_SCOPE:
        findings.append(f"stop_scope must be {RERUN_SCOPE!r}: a stop retires the pair as a whole")
    if futility and policy.get("boundary_binding") not in ("binding", "non_binding"):
        findings.append(
            "futility must declare boundary_binding: a binding boundary is credited in "
            "the error-rate calculation and a non-binding one is not"
        )
    return tuple(findings)


def look_schedule_findings(
    frozen: Mapping[str, Any], revised: Mapping[str, Any], *, outcome_visible: bool
) -> tuple[str, ...]:
    """A look added, moved, or repeated after an outcome is visible invalidates it."""
    if not outcome_visible:
        return ()
    frozen_looks = (frozen.get("interim_looks") or {}).get("information_fractions", ())
    revised_looks = (revised.get("interim_looks") or {}).get("information_fractions", ())
    if list(frozen_looks) == list(revised_looks):
        return ()
    return (
        "the look schedule changed after an outcome became visible, which invalidates "
        f"the declaration rather than being absorbed into it: {list(frozen_looks)} -> "
        f"{list(revised_looks)}",
    )


def stop_report(*, reason: str, stop_scope: str) -> dict[str, Any]:
    """FR-055: a stopped comparison is reported as stopped, never as completed."""
    if stop_scope != RERUN_SCOPE:
        raise AnalysisDecisionError(
            f"stop_scope {stop_scope!r} is not {RERUN_SCOPE!r}: racing and futility never "
            "retire a single arm"
        )
    return {
        "reported_as": "stopped",
        "stopping_reason": reason,
        "stop_scope": stop_scope,
        "early_stop_biases_estimate": True,
    }


# ---------------------------------------------------------------------------
# Analysis-plan supersession and non-pooling (FR-056)
# ---------------------------------------------------------------------------


# Appended to a superseded plan's id. Distinctive enough that re-superseding a
# revision reuses the original base rather than truncating it at a stray letter.
_REVISION_MARKER = "+revision-"


@dataclass(frozen=True)
class PlanSupersession:
    """A new versioned plan plus the binding of the plan it supersedes.

    ``supersedes`` is returned beside the plan rather than written into it: the
    plan contract is closed under ``additionalProperties: false`` and non-pooling
    is carried by the ``{id, digest}`` binding every decision bundle already
    holds, not by a new field or a new taxonomy member.
    """

    plan: dict[str, Any]
    supersedes: dict[str, str]


def supersede_analysis_plan(plan: Mapping[str, Any], **changes: Any) -> PlanSupersession:
    """FR-056: a changed ceiling or threshold produces a new id and digest."""
    if not changes:
        raise AnalysisDecisionError(
            "supersession requires at least one changed ceiling or threshold"
        )
    revised = copy.deepcopy(dict(plan))
    for key, value in changes.items():
        if key not in revised:
            raise AnalysisDecisionError(f"{key!r} is not a member of the frozen plan")
        revised[key] = copy.deepcopy(value)
    base = str(plan["analysis_plan_id"]).split(_REVISION_MARKER, 1)[0]
    content = {
        key: value
        for key, value in revised.items()
        if key not in ("analysis_plan_id", "analysis_plan_digest")
    }
    revision = record_digest(content)[len("sha256:") : len("sha256:") + 12]
    revised["analysis_plan_id"] = f"{base}{_REVISION_MARKER}{revision}"
    revised["analysis_plan_digest"] = record_digest(revised, digest_field="analysis_plan_digest")
    return PlanSupersession(
        plan=revised,
        supersedes={
            "id": str(plan["analysis_plan_id"]),
            "digest": str(plan["analysis_plan_digest"]),
        },
    )


def pooling_permitted(binding_a: Mapping[str, str], binding_b: Mapping[str, str]) -> bool:
    """Outcomes pool only when they were observed under the identical plan binding."""
    return (binding_a.get("id"), binding_a.get("digest")) == (
        binding_b.get("id"),
        binding_b.get("digest"),
    )


# ---------------------------------------------------------------------------
# Decision bundles and deterministic replay (SC-011, FR-032)
# ---------------------------------------------------------------------------

# Which condition a non-passing precondition gate fires. Split rather than
# collapsed, because FR-019 routes a bindings failure and a hard-gate failure to
# different terminal members.
_GATE_FAIL_CONDITION: Mapping[str, str] = MappingProxyType(
    {
        "bindings": "binding_failure",
        "partition": "partition_not_eligible",
        "treatment": "failed_gate",
        "deterministic": "failed_gate",
        "provenance": "failed_gate",
        "completeness": "incomplete_evidence",
        "floors": "failed_floor",
        "non_inferiority": "failed_non_inferiority",
    }
)
_GATE_UNCERTAIN_CONDITION: Mapping[str, str] = MappingProxyType(
    {
        "bindings": "incomplete_evidence",
        "partition": "incomplete_evidence",
        "treatment": "incomplete_evidence",
        "deterministic": "incomplete_evidence",
        "provenance": "incomplete_evidence",
        "completeness": "incomplete_evidence",
        "floors": "statistical_uncertainty",
        "non_inferiority": "statistical_uncertainty",
    }
)
_PARETO_CONDITION: Mapping[str, str] = MappingProxyType(
    {
        "tie": "pareto_tie",
        "mixed": "mixed_dominance",
        "uncertain": "statistical_uncertainty",
    }
)
# ``analysis_output.complete`` is an evidence claim, so every condition that names
# an evidence shortfall clears it. An ``invalid`` record clears it too: a bundle
# whose bindings, partition eligibility, or references failed has no analysis for
# completeness to describe, and reporting it complete would overstate the record.
EVIDENCE_SHORTFALL_CONDITIONS = (
    "incomplete_evidence",
    "campaign_budget_exhausted",
    "rerun_cap_exhausted",
    "attrition_cap_exceeded",
    "unclassifiable_attrition",
    "unobservable_environment",
)


def _pareto_stage_result(pareto_result: str) -> str:
    """Map a dominance outcome onto a ladder stage result.

    Only ``candidate_dominates`` passes. ``comparator_dominates`` is the
    candidate being strictly beaten on every dimension — the clearest possible
    losing case — and MUST fail the stage. Treating it as a pass inverts the
    selection rule: with no condition raised, ``resolve_terminal`` sees an empty
    condition set and returns ``qualified``, so the worst possible candidate
    qualifies. A tie and mixed dominance already fail here, and FR-019 requires
    a failed comparison to yield no qualification rather than a forced ranking.

    The outcome is checked against the closed ``PARETO_RESULTS`` set first. Every
    unrecognised value would otherwise fall through to ``fail``, so a typo in a
    caller — ``"uncertian"`` for ``"uncertain"`` — would silently convert an
    inconclusive comparison into a definite loss instead of raising. Failing
    closed is right for a value that IS a losing outcome; it is wrong for one
    that is not an outcome at all.
    """
    if pareto_result not in PARETO_RESULTS:
        raise AnalysisDecisionError(
            f"{pareto_result!r} is not a closed Pareto dominance outcome"
        )
    if pareto_result == "candidate_dominates":
        return "pass"
    if pareto_result == "uncertain":
        return "uncertain"
    return "fail"


def build_decision_bundle(
    *,
    decision_bundle_id: str,
    partition: Mapping[str, Any],
    comparison_set_binding: Mapping[str, str],
    assignment_bindings: Sequence[Mapping[str, str]],
    score_bundle_bindings: Sequence[Mapping[str, str]],
    analysis_plan_binding: Mapping[str, str] | None = None,
    calibration_protocol_binding: Mapping[str, str] | None = None,
    analysis_output_id: str,
    ordered_gate_results: Sequence[Mapping[str, str]],
    floor_result: str,
    non_inferiority_result: str,
    pareto_result: str,
    complete: bool,
    decision: str,
    decision_reasons: Sequence[str],
    reasoning_output_tokens_total: int | None,
    provenance_inference_count: int,
    evidence_refs: Sequence[str],
) -> dict[str, Any]:
    """Assemble one decision bundle carrying no weight, score, or price coefficient."""
    if decision not in TERMINAL_STATES:
        raise AnalysisDecisionError(f"{decision!r} is not a closed terminal member")
    if decision == "qualified" and not partition.get("qualification_eligible"):
        raise AnalysisDecisionError(
            "qualified is unreachable from a partition that is not qualification-eligible"
        )
    # FR-037: which artifact a bundle binds is decided by eligibility, not by the
    # caller. An ineligible partition binds the calibration protocol because the
    # analysis plan does not exist until calibration finishes; binding both, or
    # the wrong one, is refused rather than silently accepted under whichever
    # name the caller supplied.
    eligible = bool(partition.get("qualification_eligible"))
    required_binding = "analysis_plan_binding" if eligible else "calibration_protocol_binding"
    forbidden_binding = "calibration_protocol_binding" if eligible else "analysis_plan_binding"
    supplied = {
        "analysis_plan_binding": analysis_plan_binding,
        "calibration_protocol_binding": calibration_protocol_binding,
    }
    if supplied[required_binding] is None:
        raise AnalysisDecisionError(
            f"a decision with qualification_eligible={eligible} must bind {required_binding}"
        )
    if supplied[forbidden_binding] is not None:
        raise AnalysisDecisionError(
            f"a decision with qualification_eligible={eligible} must not bind {forbidden_binding}"
        )
    analysis_output: dict[str, Any] = {
        "analysis_output_id": analysis_output_id,
        "complete": complete,
        "floor_result": floor_result,
        "non_inferiority_result": non_inferiority_result,
        "pareto_result": pareto_result,
    }
    analysis_output["analysis_output_digest"] = record_digest(
        analysis_output, digest_field="analysis_output_digest"
    )
    bundle: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "decision_bundle_id": decision_bundle_id,
        "partition": dict(partition),
        "comparison_set_binding": dict(comparison_set_binding),
        "assignment_bindings": [dict(item) for item in assignment_bindings],
        "score_bundle_bindings": [dict(item) for item in score_bundle_bindings],
        required_binding: dict(supplied[required_binding]),
        "analysis_output": analysis_output,
        "ordered_gate_results": [dict(entry) for entry in ordered_gate_results],
        "decision": decision,
        "decision_reasons": list(decision_reasons),
        "reported_limitations": {
            "reasoning_output_tokens_total": reasoning_output_tokens_total,
            "reasoning_tokens_excluded_from_dominance": True,
            "blinding_bounded": True,
            "provenance_inference_count": provenance_inference_count,
        },
        "evidence_refs": list(evidence_refs),
    }
    # FR-019, FR-024: both guards run here, on the write path, before the digest
    # seals. Read as a report they name a violation that has already been
    # committed; run as a gate they are the only thing standing between a
    # caller-supplied nested mapping — a partition, a binding, an evidence
    # reference — and a weight, price coefficient, or final route policy inside
    # sealed decision evidence.
    findings = weighting_findings(bundle) + final_output_findings(bundle)
    if findings:
        raise AnalysisDecisionError(
            "a decision bundle may carry no weight, scalar score, price coefficient, or "
            f"final route policy: {findings}"
        )
    bundle["decision_bundle_digest"] = record_digest(bundle, digest_field="decision_bundle_digest")
    return bundle


def replay_decision(case: Mapping[str, Any]) -> dict[str, Any]:
    """Reconstruct one terminal decision from frozen bundles, deriving nothing new.

    Every value below comes from the recorded evidence: the ladder is re-run, the
    dominance comparison is recomputed from the two frozen vectors, and the
    terminal member is re-derived from the conditions those stages fire. Nothing
    is read from the committed decision bundle, so a replay that matches it is
    evidence of reconstruction rather than of copying.
    """
    evidence = case["evidence"]
    partition = case["partition"]

    stage_results = dict(evidence["gate_outcomes"])
    stage_results["floors"] = evidence["floor_result"]
    stage_results["non_inferiority"] = evidence["non_inferiority_result"]

    provisional = evaluate_ladder(stage_results)
    pareto_result = "not_evaluated"
    if stage_reachable(provisional, "pareto"):
        candidate = evidence.get("candidate_vector")
        comparator = evidence.get("comparator_vector")
        if candidate is None or comparator is None:
            pareto_result = "uncertain"
        else:
            pareto_result = pareto_compare(candidate, comparator).result
        stage_results["pareto"] = _pareto_stage_result(pareto_result)

    ordered = evaluate_ladder(stage_results)

    conditions: list[str] = []
    for entry in ordered:
        gate, result = entry["gate"], entry["result"]
        if result == "pass" or result == NOT_EVALUATED:
            continue
        if gate == "pareto":
            conditions.append(_PARETO_CONDITION[pareto_result])
            continue
        conditions.append(
            _GATE_FAIL_CONDITION[gate] if result == "fail" else _GATE_UNCERTAIN_CONDITION[gate]
        )
    conditions.extend(evidence.get("conditions", ()))

    terminal = resolve_terminal(
        conditions, qualification_eligible=bool(partition["qualification_eligible"])
    )
    complete = not set(EVIDENCE_SHORTFALL_CONDITIONS) & set(conditions)
    if terminal.decision == "invalid":
        complete = False

    # The analysis-output summary is closed to pass/fail/uncertain, so a stage that
    # was never reached summarizes as uncertain there while the ordered ladder
    # above carries the FR-017 not_evaluated fact.
    ladder_by_gate = {entry["gate"]: entry["result"] for entry in ordered}
    floor_result = ladder_by_gate["floors"]
    if floor_result == NOT_EVALUATED:
        floor_result = "uncertain"

    return build_decision_bundle(
        decision_bundle_id=case["decision_bundle_id"],
        partition=partition,
        comparison_set_binding=case["comparison_set_binding"],
        assignment_bindings=case["assignment_bindings"],
        score_bundle_bindings=case["score_bundle_bindings"],
        # FR-037: the case carries whichever binding its eligibility calls for.
        analysis_plan_binding=case.get("analysis_plan_binding"),
        calibration_protocol_binding=case.get("calibration_protocol_binding"),
        analysis_output_id=case["analysis_output_id"],
        ordered_gate_results=ordered,
        floor_result=floor_result,
        non_inferiority_result=ladder_by_gate["non_inferiority"],
        pareto_result=pareto_result,
        complete=complete,
        decision=terminal.decision,
        decision_reasons=terminal.decision_reasons,
        reasoning_output_tokens_total=evidence.get("reasoning_output_tokens_total"),
        provenance_inference_count=int(evidence.get("provenance_inference_count", 0)),
        evidence_refs=case.get("evidence_refs", ()),
    )


def load_replay_fixture(path: Path | None = None) -> dict[str, Any]:
    """Read the bounded, committed calibration replay fixture."""
    target = REPLAY_FIXTURE_PATH if path is None else path
    return json.loads(target.read_text(encoding="utf-8"))


__all__ = [
    "CLASSIFICATION_TIMING",
    "COMPLETE_CASE_FILTERING",
    "DECISION_REASONS",
    "DIAGNOSTIC_ONLY_FIELDS",
    "DIRECTION_OF_PREFERENCE",
    "ESTIMAND_RETAINED_CODES",
    "EVIDENCE_SHORTFALL_CONDITIONS",
    "FORBIDDEN_OUTPUT_KEYS",
    "GUARDRAIL_DECLARATION_FIELDS",
    "GUARDRAIL_FAMILY",
    "LADDER_GATES",
    "MULTIPLICITY_FAMILIES",
    "PARETO_DIMENSIONS",
    "REPLAY_FIXTURE_PATH",
    "RERUN_SCOPE",
    "TERMINAL_BY_CONDITION",
    "TERMINAL_STATES",
    "AnalysisDecisionError",
    "CampaignStop",
    "GuardrailAdmissibility",
    "GuardrailBreach",
    "ParetoResult",
    "PlanSupersession",
    "RerunVerdict",
    "TerminalDecision",
    "attempts_for_reruns",
    "build_decision_bundle",
    "build_transient_classification_record",
    "classify_campaign_ceiling_stop",
    "compare_dimension",
    "dominance_with_reasoning_report",
    "estimand_acceptance",
    "evaluate_ladder",
    "final_output_findings",
    "grant_rerun",
    "guardrail_admissibility",
    "guardrail_breach",
    "guardrail_findings",
    "interim_look_findings",
    "load_replay_fixture",
    "look_schedule_findings",
    "multiplicity_findings",
    "pareto_compare",
    "pooling_permitted",
    "primary_statistics_findings",
    "reasoning_token_report",
    "replay_decision",
    "resolve_terminal",
    "retained_in_estimand",
    "stage_reachable",
    "stop_report",
    "supersede_analysis_plan",
    "supersede_pair",
    "terminal_complete_pairs",
    "terminal_for",
]
