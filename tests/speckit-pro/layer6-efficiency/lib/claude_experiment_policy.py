#!/usr/bin/env python3
"""CAR-003 partitions, pre-execution pair binding, campaign budgets, and strata.

Everything in this module happens **before** any arm of a pair runs. That is the
whole point of it: each rule here is only meaningful as a precommitment, and a
check applied after outcomes are visible is the outcome-conditioned filtering the
requirements exist to prevent.

**Partitions are disjoint at the objective level** (FR-013). Partition-level
disjointness would be trivially satisfiable by two partitions that list the same
objectives, so the registry entry binds an objective-set digest over the
deduplicated, lexicographically sorted objective ids — two partitions listing the
same objectives in different orders therefore produce the same digest and the
collision is detected rather than hidden by ordering. An objective appearing in
two registered partitions fails closed with ``failure_plane=partition``.

**Calibration pairs bind the calibration protocol, not the analysis plan**
(FR-037). The analysis plan freezes only *after* calibration, so requiring a
calibration pair to bind it is a circular dependency that makes the calibration
pilot unrunnable. The substitution is keyed on ``qualification_eligible`` rather
than on ``partition_type``, so the two branches are exhaustive: keying on
``partition_type=calibration`` alone would leave a non-calibration ineligible
partition bound to neither artifact, failing open on the very invariant the rule
enforces. The substitution holds transitively at the experiment-policy edge,
because every assignment binds a policy and the cycle would otherwise reappear
one edge away.

**The analysis-plan budget is authoritative** (FR-038). The policy budget must
*equal* it for qualification-eligible partitions and may be tighter only for
calibration. Budget exhaustion enters the estimand at acceptance zero, so a
per-campaign budget adjusted after results are visible would silently redefine
the estimand — which is why "tighter" is a calibration-only allowance and any
inequality on an eligible partition fails closed rather than being tolerated as
conservative.

**Stratum membership is a design-time allocation variable** (FR-052). It derives
only from the closed set of task and protocol characteristics the role-corpus
contract already binds, exactly as randomization strata in a controlled trial are
built from prognostic baseline covariates rather than from observed results.
Realized duration, turns, tokens, retries, and compactions are post-treatment
quantities; stratifying on them conditions the comparison on a consequence of the
treatment and would let the powered long-horizon stratum be populated after
results are visible.

Digest and invalidation vocabulary are imported from the slice-1 and slice-2
modules rather than restated, so one FR-033 preimage rule and one closed
invalidation set govern every CAR-003 record. This module is repository-only
harness code and makes **no live model calls**.
"""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

if __package__:  # pragma: no cover - the lib is imported flat by the suite
    from .claude_score_bundle import INVALIDATION_REASONS
    from .claude_successor_freeze import canonical_json, record_digest
else:
    from claude_score_bundle import INVALIDATION_REASONS
    from claude_successor_freeze import canonical_json, record_digest


SCHEMA_VERSION = "1.0.0"

# FR-034: every refusal in this module lands on the partition plane, using the
# closed score-taxonomy codes rather than coining partition-local ones.
PARTITION_PLANE = "partition"
PARTITION_MISMATCH = "partition_mismatch"
PARTITION_NOT_ELIGIBLE = "partition_not_eligible"
CROSS_PARTITION_REUSE = "cross_partition_reuse"

# FR-013: the closed partition-type set.
PARTITION_TYPES = (
    "calibration",
    "screening",
    "selection",
    "cohort_lock",
    "integrated_confirmation",
)

# FR-022: the eight live-campaign ceilings, closed and identical in both budgets.
BUDGET_CEILINGS = (
    "max_attempts",
    "max_duration_seconds",
    "max_input_tokens",
    "max_cache_write_tokens_by_ttl_class",
    "max_cache_read_tokens",
    "max_output_tokens",
    "max_candidates",
    "max_confirmation_entries",
)
TTL_CEILING_FIELD = "max_cache_write_tokens_by_ttl_class"

# FR-022: closed TTL-class key space, reusing the two cache-creation classes the
# frozen CAR-002 telemetry profile already records. The budget ceilings and the
# additive cache diagnostic share this key set exactly, so a ceiling can never be
# keyed differently from the measurement it bounds and silently stop applying.
TTL_CLASSES = ("ephemeral_5m", "ephemeral_1h")

# FR-052: the closed pre-execution derivation basis.
STRATUM_BASIS = (
    "role_id",
    "objective",
    "permitted_tools",
    "mutation_contract",
    "expected_artifacts",
    "acceptance_oracle",
)
UNKNOWN_STRATUM_RESULT = "inconclusive"

# FR-037: every field a pair binds before execution. ``superseded`` and the
# record's own digest are state rather than bindings, so they are emitted but not
# listed here.
PRE_EXECUTION_BINDING_FIELDS = (
    "comparison_set_id",
    "assignment_id",
    "partition",
    "candidate_route_binding",
    "comparator_route_binding",
    "role_id",
    "fixture_binding",
    "task_binding",
    "instruction_hash",
    "configuration_hash",
    "capability_freeze_binding",
    "runtime_snapshot_binding",
    "route_resolution_binding",
    "materialization_binding",
    "experiment_policy_binding",
    "environment_contract",
    "stratum_assignment",
    "assigned_order",
    "pre_execution_timestamp",
)

BINDING_FIELDS = tuple(
    name for name in PRE_EXECUTION_BINDING_FIELDS if name.endswith("_binding")
)

ANALYSIS_PLAN_BINDING = "analysis_plan_binding"
CALIBRATION_PROTOCOL_BINDING = "calibration_protocol_binding"

# FR-041: the assignment-level invalidation vocabulary is the closed score-bundle
# set plus the FR-032 reference-integrity reason the assignment contract adds.
ASSIGNMENT_INVALIDATION_REASONS = INVALIDATION_REASONS + ("trace_reference_integrity_failure",)

__all__ = [
    "ANALYSIS_PLAN_BINDING",
    "ASSIGNMENT_INVALIDATION_REASONS",
    "BUDGET_CEILINGS",
    "CALIBRATION_PROTOCOL_BINDING",
    "PARTITION_TYPES",
    "PRE_EXECUTION_BINDING_FIELDS",
    "STRATUM_BASIS",
    "TTL_CLASSES",
    "UNKNOWN_STRATUM_RESULT",
    "ExperimentPolicyError",
    "PartitionVerdict",
    "StratumResolution",
    "assignment_verdict",
    "budget_verdict",
    "build_assignment",
    "build_calibration_protocol",
    "build_experiment_policy",
    "build_partition_registry_entry",
    "bundle_partition_verdict",
    "consumable_objectives",
    "consumption_verdict",
    "immutability_verdict",
    "long_horizon_strata",
    "manifest_findings",
    "objective_set_digest",
    "policy_verdict",
    "rebind_assignment",
    "refresh_assignment",
    "register_partitions",
    "required_plan_binding",
    "resolve_stratum",
    "stratum_verdict",
    "unbound_pair_fields",
]


class ExperimentPolicyError(AssertionError):
    """Fail-closed error for a refused partition, pair, budget, or stratum."""


@dataclass(frozen=True)
class PartitionVerdict:
    """One fail-closed outcome on the partition plane."""

    ok: bool
    failure_plane: str = "none"
    failure_code: str = "none"
    findings: tuple[str, ...] = field(default_factory=tuple)


def _clean() -> PartitionVerdict:
    return PartitionVerdict(True, "none", "none", ())


def _refused(code: str, findings: Sequence[str]) -> PartitionVerdict:
    return PartitionVerdict(False, PARTITION_PLANE, code, tuple(findings))


def _unbound(value: Any) -> bool:
    """A field is unbound when it is absent, null, or an empty container."""
    if value is None:
        return True
    return isinstance(value, (str, list, tuple, dict, set)) and len(value) == 0


# ---------------------------------------------------------------------------
# Partition registry (FR-013, FR-033)
# ---------------------------------------------------------------------------


def objective_set_digest(objective_ids: Iterable[str]) -> str:
    """FR-033: SHA-256 over the deduplicated, lexicographically sorted id array.

    Pinning the preimage to the *sorted* array is what makes two partitions
    listing the same objectives in a different order collide detectably instead
    of producing two digests for one objective set.
    """
    payload = sorted({str(objective) for objective in objective_ids})
    if not payload:
        raise ExperimentPolicyError("a partition must register at least one objective")
    return "sha256:" + hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def build_partition_registry_entry(
    *,
    partition_id: str,
    partition_type: str,
    qualification_eligible: bool,
    objective_ids: Sequence[str],
    frozen_at: str,
    owning_spec: str,
) -> dict[str, Any]:
    """Freeze one versioned Partition Registry Entry."""
    if partition_type not in PARTITION_TYPES:
        raise ExperimentPolicyError(
            f"{partition_type!r} is not a member of the closed partition-type set"
        )
    if partition_type == "calibration" and qualification_eligible:
        raise ExperimentPolicyError(
            "calibration always carries qualification_eligible=false; refusing to "
            f"register {partition_id!r} as eligible"
        )
    sorted_ids = sorted({str(objective) for objective in objective_ids})
    return {
        "schema_version": SCHEMA_VERSION,
        "record_kind": "partition_registry_entry",
        "partition_id": partition_id,
        "partition_type": partition_type,
        "qualification_eligible": bool(qualification_eligible),
        "objective_set_digest": objective_set_digest(sorted_ids),
        "objective_ids": sorted_ids,
        "frozen_at": frozen_at,
        "owning_spec": owning_spec,
    }


def register_partitions(entries: Sequence[Mapping[str, Any]]) -> PartitionVerdict:
    """Fail closed on a duplicated partition id or a shared objective."""
    findings: list[str] = []
    seen_ids: set[str] = set()
    for entry in entries:
        partition_id = str(entry.get("partition_id"))
        if partition_id in seen_ids:
            findings.append(f"partition_id {partition_id!r} is registered more than once")
        seen_ids.add(partition_id)
        if entry.get("partition_type") not in PARTITION_TYPES:
            findings.append(
                f"{partition_id}: partition_type {entry.get('partition_type')!r} is not closed"
            )
        recorded = entry.get("objective_set_digest")
        objective_ids = tuple(entry.get("objective_ids", ()))
        if not objective_ids:
            # ``objective_set_digest`` refuses an empty set by raising, which is
            # correct at the builder. It is wrong here: this loop accumulates
            # findings across every entry, so letting the exception escape would
            # discard every finding already collected and hand the caller a
            # traceback where every other refusal returns a verdict. Record it
            # and keep validating the rest.
            findings.append(f"{partition_id}: registers no objectives")
        elif recorded != objective_set_digest(objective_ids):
            findings.append(f"{partition_id}: objective_set_digest does not match its preimage")
    if findings:
        return _refused(PARTITION_MISMATCH, findings)

    owners: dict[str, str] = {}
    collisions: list[str] = []
    for entry in entries:
        partition_id = str(entry.get("partition_id"))
        for objective in entry.get("objective_ids", ()):
            previous = owners.get(objective)
            if previous is not None:
                collisions.append(
                    f"objective {objective!r} is registered in both {previous!r} and {partition_id!r}"
                )
                continue
            owners[objective] = partition_id
    if collisions:
        return _refused(CROSS_PARTITION_REUSE, collisions)
    return _clean()


def immutability_verdict(
    frozen: Mapping[str, Any], candidate: Mapping[str, Any]
) -> PartitionVerdict:
    """FR-013: ``partition_type`` and ``qualification_eligible`` never move."""
    findings = [
        f"{field_name} is immutable after freeze: {frozen.get(field_name)!r} -> "
        f"{candidate.get(field_name)!r}"
        for field_name in ("partition_type", "qualification_eligible")
        if frozen.get(field_name) != candidate.get(field_name)
    ]
    if findings:
        return _refused(PARTITION_MISMATCH, findings)
    return _clean()


def _registry_index(registry: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(entry.get("partition_id")): entry for entry in registry}


def _is_consumable(entry: Mapping[str, Any]) -> bool:
    """FR-013: CAR-003 consumes only ineligible calibration objectives."""
    return entry.get("partition_type") == "calibration" and not entry.get("qualification_eligible")


def consumable_objectives(registry: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    """Every objective CAR-003 is permitted to consume, sorted."""
    objectives: set[str] = set()
    for entry in registry:
        if _is_consumable(entry):
            objectives.update(str(objective) for objective in entry.get("objective_ids", ()))
    return tuple(sorted(objectives))


def consumption_verdict(
    registry: Sequence[Mapping[str, Any]], objective_id: str
) -> PartitionVerdict:
    """Refuse any objective outside an ineligible calibration partition."""
    for entry in registry:
        if objective_id not in entry.get("objective_ids", ()):
            continue
        if _is_consumable(entry):
            return _clean()
        return _refused(
            PARTITION_NOT_ELIGIBLE,
            (
                f"objective {objective_id!r} belongs to {entry.get('partition_id')!r} "
                f"({entry.get('partition_type')}, qualification_eligible="
                f"{entry.get('qualification_eligible')}); CAR-003 consumes only "
                "qualification_eligible=false calibration objectives",
            ),
        )
    return _refused(
        PARTITION_MISMATCH, (f"objective {objective_id!r} is not registered in any partition",)
    )


def bundle_partition_verdict(
    bundle: Mapping[str, Any], registry: Sequence[Mapping[str, Any]]
) -> PartitionVerdict:
    """Every fixture, experiment, score, and decision bundle resolves its partition."""
    partition = bundle.get("partition") or {}
    partition_id = str(partition.get("partition_id"))
    entry = _registry_index(registry).get(partition_id)
    if entry is None:
        return _refused(
            PARTITION_MISMATCH,
            (f"{bundle.get('bundle_kind', 'bundle')}: partition {partition_id!r} is unregistered",),
        )
    findings = [
        f"{bundle.get('bundle_kind', 'bundle')}: {field_name} {partition.get(field_name)!r} "
        f"contradicts the registry entry {entry.get(field_name)!r}"
        for field_name in ("partition_type", "qualification_eligible")
        if partition.get(field_name) != entry.get(field_name)
    ]
    if partition.get("partition_type") not in PARTITION_TYPES:
        findings.append(f"partition_type {partition.get('partition_type')!r} is not closed")
    if findings:
        return _refused(PARTITION_MISMATCH, findings)
    return _clean()


# ---------------------------------------------------------------------------
# Pre-execution pair binding and the calibration substitution (FR-037, FR-041)
# ---------------------------------------------------------------------------


def required_plan_binding(qualification_eligible: bool) -> str:
    """FR-037: keyed on eligibility, so the two branches are exhaustive."""
    return ANALYSIS_PLAN_BINDING if qualification_eligible else CALIBRATION_PROTOCOL_BINDING


def build_calibration_protocol(
    *,
    calibration_protocol_id: str,
    partition_binding: Mapping[str, str],
    objective_bindings: Sequence[Mapping[str, str]],
    frozen_at: str,
) -> dict[str, Any]:
    """FR-037: no margins, no sample sizes, no terminal thresholds — all pinned false."""
    protocol: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_kind": "calibration_protocol",
        "calibration_protocol_id": calibration_protocol_id,
        "partition_binding": dict(partition_binding),
        "objective_bindings": [dict(item) for item in objective_bindings],
        "carries_margins": False,
        "carries_sample_sizes": False,
        "carries_terminal_thresholds": False,
        "frozen_at": frozen_at,
    }
    protocol["protocol_digest"] = record_digest(protocol, digest_field="protocol_digest")
    return protocol


def build_assignment(
    *,
    comparison_set_id: str,
    assignment_id: str,
    partition: Mapping[str, Any],
    bindings: Mapping[str, Mapping[str, str]],
    role_id: str,
    instruction_hash: str,
    configuration_hash: str,
    environment_contract: Mapping[str, Any],
    stratum_assignment: Mapping[str, Any],
    assigned_order: int,
    pre_execution_timestamp: str,
    plan_binding: Mapping[str, str],
    originating_comparison_set_id: str | None = None,
) -> dict[str, Any]:
    """Bind one pair completely, before execution, with the correct plan artifact."""
    missing = tuple(name for name in BINDING_FIELDS if name not in bindings)
    if missing:
        raise ExperimentPolicyError(f"the pair is missing pre-execution bindings: {missing}")
    eligible = bool(partition.get("qualification_eligible"))
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_kind": "comparison_set_assignment",
        "comparison_set_id": comparison_set_id,
        "assignment_id": assignment_id,
        "partition": dict(partition),
        **{name: dict(bindings[name]) for name in BINDING_FIELDS},
        "role_id": role_id,
        "instruction_hash": instruction_hash,
        "configuration_hash": configuration_hash,
        "environment_contract": copy.deepcopy(dict(environment_contract)),
        "stratum_assignment": copy.deepcopy(dict(stratum_assignment)),
        required_plan_binding(eligible): dict(plan_binding),
        "assigned_order": assigned_order,
        "pre_execution_timestamp": pre_execution_timestamp,
        "superseded": False,
    }
    if originating_comparison_set_id is not None:
        record["originating_comparison_set_id"] = originating_comparison_set_id
    record["assignment_digest"] = record_digest(record, digest_field="assignment_digest")
    return record


def unbound_pair_fields(assignment: Mapping[str, Any]) -> tuple[str, ...]:
    """Name every pre-execution field the pair left absent, null, or empty."""
    return tuple(
        name for name in PRE_EXECUTION_BINDING_FIELDS if _unbound(assignment.get(name))
    )


def _plan_binding_findings(record: Mapping[str, Any], label: str) -> tuple[str, str] | None:
    """Return ``(code, finding)`` when the plan/protocol substitution is broken."""
    eligible = bool((record.get("partition") or {}).get("qualification_eligible"))
    required = required_plan_binding(eligible)
    forbidden = CALIBRATION_PROTOCOL_BINDING if eligible else ANALYSIS_PLAN_BINDING
    has_required = not _unbound(record.get(required))
    has_forbidden = not _unbound(record.get(forbidden))
    if has_required and has_forbidden:
        return (
            PARTITION_MISMATCH,
            f"{label} binds both {ANALYSIS_PLAN_BINDING} and {CALIBRATION_PROTOCOL_BINDING}",
        )
    if has_forbidden:
        return (
            PARTITION_NOT_ELIGIBLE,
            f"{label} with qualification_eligible={eligible} must bind {required}, not {forbidden}",
        )
    if not has_required:
        return (PARTITION_MISMATCH, f"{label} binds neither artifact; {required} is required")
    return None


def assignment_verdict(assignment: Mapping[str, Any]) -> PartitionVerdict:
    """Every pre-execution binding present, and exactly the right plan artifact."""
    findings = [f"pair leaves {name} unbound" for name in unbound_pair_fields(assignment)]
    if findings:
        return _refused(PARTITION_MISMATCH, findings)
    broken = _plan_binding_findings(assignment, "pair")
    if broken is not None:
        return _refused(broken[0], (broken[1],))
    stratum = stratum_verdict(assignment.get("stratum_assignment") or {})
    if not stratum.ok:
        return stratum
    return _clean()


def build_experiment_policy(
    *,
    experiment_policy_id: str,
    partition: Mapping[str, Any],
    candidate_freeze_binding: Mapping[str, str],
    corpus_binding: Mapping[str, str],
    plan_binding: Mapping[str, str],
    scorer_family_exclusion: Mapping[str, Any],
    budget: Mapping[str, Any],
    rerun_cap: int,
    execution_mode: str = "deterministic_replay",
    order_rule: str = "seeded_random",
) -> dict[str, Any]:
    """Freeze one experiment policy, substituting the plan artifact transitively."""
    eligible = bool(partition.get("qualification_eligible"))
    policy: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "experiment_policy_id": experiment_policy_id,
        "partition": dict(partition),
        "candidate_freeze_binding": dict(candidate_freeze_binding),
        "corpus_binding": dict(corpus_binding),
        required_plan_binding(eligible): dict(plan_binding),
        "assignment_policy": {
            "pair_before_execution": True,
            "order_rule": order_rule,
            "cache_isolation": "per_arm_ephemeral_root",
        },
        "terminal_policy": {
            "candidate_failures_remain_in_estimand": True,
            "candidate_failure_acceptance": 0,
        },
        "rerun_policy": {
            "eligible_failure": "independently_preclassified_transient_harness_failure",
            "scope": "complete_pair",
            "cap": rerun_cap,
            "classification_timing": "arm_blind_before_outcome_read",
        },
        "scorer_family_exclusion": copy.deepcopy(dict(scorer_family_exclusion)),
        "budget": copy.deepcopy(dict(budget)),
        "execution_mode": execution_mode,
    }
    policy["policy_digest"] = record_digest(policy, digest_field="policy_digest")
    return policy


def policy_verdict(policy: Mapping[str, Any]) -> PartitionVerdict:
    """FR-037: the substitution holds at the policy edge too, or the cycle returns."""
    broken = _plan_binding_findings(policy, "experiment policy")
    if broken is not None:
        return _refused(broken[0], (broken[1],))
    return _clean()


def refresh_assignment(
    assignment: Mapping[str, Any], *, reason: str, recorded_at: str
) -> dict[str, Any]:
    """FR-041: record an additive invalidation. The pair is never rebound."""
    if reason not in ASSIGNMENT_INVALIDATION_REASONS or reason == "none":
        raise ExperimentPolicyError(f"{reason!r} is not a live closed invalidation reason")
    refreshed = copy.deepcopy(dict(assignment))
    invalidations = list(refreshed.get("invalidations", ()))
    invalidations.append({"reason": reason, "recorded_at": recorded_at})
    refreshed["invalidations"] = invalidations
    refreshed["assignment_digest"] = record_digest(refreshed, digest_field="assignment_digest")
    return refreshed


def rebind_assignment(assignment: Mapping[str, Any], **_replacements: Any) -> dict[str, Any]:
    """FR-037: refuse outright. A bound pair is invalidated, never rebound."""
    raise ExperimentPolicyError(
        "a bound pair is never rebound; record an additive invalidation with "
        f"refresh_assignment() instead (assignment {assignment.get('assignment_id')!r})"
    )


# ---------------------------------------------------------------------------
# Campaign budgets (FR-022, FR-038)
# ---------------------------------------------------------------------------


def _ttl_findings(label: str, ceiling: Any) -> list[str]:
    if not isinstance(ceiling, Mapping) or not ceiling:
        return [f"{label}.{TTL_CEILING_FIELD} must carry at least one closed TTL class"]
    return [
        f"{label}.{TTL_CEILING_FIELD} key {key!r} is outside the closed TTL-class key space"
        for key in ceiling
        if key not in TTL_CLASSES
    ]


def budget_verdict(
    *,
    policy_budget: Mapping[str, Any],
    plan_budget: Mapping[str, Any],
    qualification_eligible: bool,
) -> PartitionVerdict:
    """FR-038: the plan budget is authoritative; equality, or calibration-only tighter."""
    findings: list[str] = []
    for label, budget in (("experiment policy", policy_budget), ("analysis plan", plan_budget)):
        for ceiling in BUDGET_CEILINGS:
            if ceiling not in budget:
                findings.append(f"{label} budget is missing ceiling {ceiling}")
        findings.extend(_ttl_findings(label, budget.get(TTL_CEILING_FIELD)))
    if findings:
        return _refused(PARTITION_MISMATCH, findings)

    for ceiling in BUDGET_CEILINGS:
        recorded = policy_budget[ceiling]
        authoritative = plan_budget[ceiling]
        if ceiling == TTL_CEILING_FIELD:
            for ttl_class in TTL_CLASSES:
                findings.extend(
                    _compare_ceiling(
                        f"{ceiling}.{ttl_class}",
                        recorded.get(ttl_class),
                        authoritative.get(ttl_class),
                        qualification_eligible,
                    )
                )
            continue
        findings.extend(
            _compare_ceiling(ceiling, recorded, authoritative, qualification_eligible)
        )
    if findings:
        return _refused(PARTITION_MISMATCH, findings)
    return _clean()


def _compare_ceiling(
    label: str, recorded: Any, authoritative: Any, qualification_eligible: bool
) -> list[str]:
    if recorded is None or authoritative is None:
        return [f"{label} is declared on only one side of the comparison"]
    if qualification_eligible:
        if recorded != authoritative:
            return [
                f"{label} must equal the authoritative analysis-plan ceiling on a "
                f"qualification-eligible partition: {recorded!r} != {authoritative!r}"
            ]
        return []
    if recorded > authoritative:
        return [
            f"{label} may be tighter than the analysis-plan ceiling but never looser: "
            f"{recorded!r} > {authoritative!r}"
        ]
    return []


# ---------------------------------------------------------------------------
# Workload strata (FR-052)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StratumResolution:
    """The outcome of resolving one task onto the frozen workload manifest."""

    stratum_id: str | None
    result: str
    long_horizon: bool = False


def stratum_verdict(stratum_assignment: Mapping[str, Any]) -> PartitionVerdict:
    """Membership is fixed before either arm runs, from a closed non-realized basis."""
    findings: list[str] = []
    if _unbound(stratum_assignment.get("stratum_id")):
        findings.append("stratum_assignment leaves stratum_id unbound")
    basis = stratum_assignment.get("membership_basis")
    if not isinstance(basis, (list, tuple)) or not basis:
        findings.append(
            "stratum_assignment.membership_basis must be non-empty: an assignment with "
            "no stated basis is indistinguishable from one chosen after the fact"
        )
    else:
        findings.extend(
            f"stratum_assignment.membership_basis member {member!r} is outside the closed "
            "pre-execution set"
            for member in basis
            if member not in STRATUM_BASIS
        )
    if stratum_assignment.get("derived_from_realized_outcomes") is not False:
        findings.append(
            "stratum_assignment.derived_from_realized_outcomes must be false: realized "
            "duration, turns, tokens, retries, and compactions are post-treatment quantities"
        )
    if findings:
        return _refused(PARTITION_MISMATCH, findings)
    return _clean()


def long_horizon_strata(manifest: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    """Every stratum the frozen manifest marks long-horizon."""
    return tuple(
        stratum for stratum in manifest.get("strata", ()) if stratum.get("long_horizon")
    )


def manifest_findings(manifest: Mapping[str, Any]) -> tuple[str, ...]:
    """FR-052, FR-054: every stratum carries its own power and estimability numbers."""
    findings: list[str] = []
    if manifest.get("unknown_stratum_policy") != UNKNOWN_STRATUM_RESULT:
        findings.append(f"unknown_stratum_policy must be {UNKNOWN_STRATUM_RESULT!r}")
    if _unbound(manifest.get("minimum_unique_tasks")):
        findings.append("the manifest-wide minimum_unique_tasks backstop is unbound")
    strata = manifest.get("strata", ())
    if not strata:
        findings.append("the workload manifest must register at least one stratum")
    seen: set[str] = set()
    for stratum in strata:
        stratum_id = str(stratum.get("stratum_id"))
        if stratum_id in seen:
            findings.append(f"{stratum_id}: stratum_id is registered more than once")
        seen.add(stratum_id)
        for required_field in ("stratum_sample_size", "stratum_minimum_unique_tasks"):
            if _unbound(stratum.get(required_field)):
                findings.append(
                    f"{stratum_id}: {required_field} must be declared per stratum rather "
                    "than inherited from the pooled numbers"
                )
        rule = stratum.get("membership_rule") or {}
        basis = rule.get("permitted_basis")
        if not isinstance(basis, (list, tuple)) or not basis:
            findings.append(f"{stratum_id}: membership_rule.permitted_basis must be non-empty")
        else:
            findings.extend(
                f"{stratum_id}: membership_rule.permitted_basis member {member!r} is outside "
                "the closed pre-execution set"
                for member in basis
                if member not in STRATUM_BASIS
            )
        if rule.get("derived_from_realized_outcomes") is not False:
            findings.append(
                f"{stratum_id}: membership_rule.derived_from_realized_outcomes must be false"
            )
    return tuple(findings)


def resolve_stratum(manifest: Mapping[str, Any], stratum_id: str) -> StratumResolution:
    """FR-052: a task matching no registered stratum returns inconclusive."""
    for stratum in manifest.get("strata", ()):
        if stratum.get("stratum_id") == stratum_id:
            return StratumResolution(stratum_id, "resolved", bool(stratum.get("long_horizon")))
    return StratumResolution(None, UNKNOWN_STRATUM_RESULT, False)
