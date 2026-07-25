#!/usr/bin/env python3
"""Quality-first G56R-003 statistical qualification decisions."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from collections import defaultdict


STATISTICS_SCHEMA_VERSION = "qualification-statistics.v1"
DECISION_SEQUENCE = (
    "partition",
    "budget",
    "pairing",
    "workload_cache",
    "quality_floors",
    "non_inferiority",
    "pareto",
)
PARETO_DIMENSIONS = (
    "raw_input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "duration_ms",
    "retries",
    "compactions",
    "acceptance",
    "terminal_state",
)
PARETO_DIRECTIONS = {
    "raw_input_tokens": "lower",
    "cached_input_tokens": "lower",
    "output_tokens": "lower",
    "duration_ms": "lower",
    "retries": "lower",
    "compactions": "lower",
    "acceptance": "higher",
    "terminal_state": "not_worse",
}
PARETO_RESULTS = (
    "candidate_dominates",
    "comparator_dominates",
    "tie",
    "mixed",
    "uncertain",
)
CANDIDATE_TERMINAL_STATES = (
    "failed",
    "timed_out",
    "cancelled",
    "budget_exhausted",
    "abandoned",
)
ATTRITION_CLASSIFICATIONS = (
    "complete",
    "candidate_terminal",
    "transient_harness_failure",
    "unclassifiable_attrition",
)
RERUN_DECISIONS = (
    "not_needed",
    "complete_pair_rerun",
    "one_arm_rerun_prohibited",
    "rerun_cap_exhausted",
)
CAMPAIGN_BUDGET_FIELDS = (
    "max_attempts",
    "max_wall_clock_seconds",
    "max_raw_input_tokens",
    "max_cached_input_tokens",
    "max_output_tokens",
    "max_candidates",
    "max_confirmation_entries",
)
CALIBRATION_DECISIONS = (
    "calibration_complete",
    "no_qualification",
    "inconclusive",
    "invalid",
)
PROHIBITED_FINAL_OUTPUTS = (
    "preferred_route_policy_created",
    "fallback_route_policy_created",
    "installed_default_changed",
    "aggregate_identity_created",
    "release_claim_created",
)
TERMINAL_STATE_ORDER = (
    "abandoned",
    "budget_exhausted",
    "cancelled",
    "timed_out",
    "failed",
    "succeeded",
    "completed",
)

_PARTITION_TYPES = frozenset({
    "calibration",
    "screening",
    "selection",
    "cohort_lock",
    "integrated_confirmation",
})
_NON_INFERIORITY_FIELDS = frozenset({
    "evaluation_order",
    "endpoints",
    "margins",
    "confidence_level",
    "alpha",
    "power",
    "sample_sizes",
    "sample_size_assumptions",
    "cluster_unit",
    "cluster_adjustment",
    "multiplicity_adjustment",
})
_PARETO_POLICY_FIELDS = frozenset({
    "evaluation_order",
    "dimensions",
    "directions",
    "weights_prohibited",
    "mixed_or_tied_result",
})
_WORKLOAD_MANIFEST_FIELDS = frozenset({
    "manifest_id",
    "manifest_digest",
    "minimum_unique_tasks",
    "unknown_stratum_policy",
    "strata",
})
_WORKLOAD_STRATUM_FIELDS = frozenset({
    "stratum_id",
    "target_weight",
    "long_horizon",
    "p95_guardrails",
})
_P95_GUARDRAIL_FIELDS = frozenset({
    "raw_input_tokens_max",
    "cached_input_tokens_max",
    "output_tokens_max",
    "duration_ms_max",
})
_CACHE_POLICY_FIELDS = frozenset({
    "policy_id",
    "policy_digest",
    "pair_isolation",
    "order_leakage_prohibited",
    "cache_state",
})
_CAMPAIGN_BUDGET_FIELDS = frozenset(CAMPAIGN_BUDGET_FIELDS)
_CACHE_POLICY_BINDING_FIELDS = frozenset({"id", "digest"})
_P95_DIMENSION_GUARDRAILS = {
    "raw_input_tokens": "raw_input_tokens_max",
    "cached_input_tokens": "cached_input_tokens_max",
    "output_tokens": "output_tokens_max",
    "duration_ms": "duration_ms_max",
}
_ANALYSIS_PLAN_FIELDS = frozenset({
    "schema_version",
    "analysis_plan_id",
    "analysis_plan_version",
    "analysis_plan_digest",
    "status",
    "calibration_partition_binding",
    "calibration_evidence_bindings",
    "freeze_provenance",
    "workload_manifest",
    "cache_policy",
    "quality_floors",
    "non_inferiority",
    "pareto_policy",
    "estimand_policy",
    "attrition_policy",
    "rerun_policy",
    "campaign_budget",
    "racing_policy",
    "futility_policy",
    "terminal_policy",
})
_FREEZE_PROVENANCE_FIELDS = frozenset({
    "frozen_at",
    "frozen_after_calibration",
    "cohort_outcome_observed",
    "pre_cohort_outcome_absence_digest",
    "independent_review_binding",
})
_BINDING_FIELDS = frozenset({"id", "digest"})
_PARTITION_FIELDS = frozenset({
    "partition_id",
    "partition_type",
    "partition_digest",
    "qualification_eligible",
})
_OUTCOME_FIELDS = frozenset({
    "pair_id",
    "attempt_index",
    "arm",
    "role_id",
    "fixture_id",
    "task_id",
    "score_disposition",
    "failure_plane",
    "failure_code",
    "attrition_classification",
    "terminal_state",
    "semantic_score",
    "reliability_score",
    "resource_vector",
    "workload_stratum_id",
    "cache_policy_binding",
    "cache_state",
    "treatment_order_leakage",
    "wall_clock_seconds",
    "candidate_route_id",
    "confirmation_entries",
    "assignment_binding",
    "score_bundle_binding",
})
_QUALITY_FLOOR_FIELDS = frozenset({"evaluation_order", "semantic", "reliability"})
_ENDPOINTS = frozenset({"semantic_score", "reliability_score"})
_ARMS = frozenset({"candidate", "comparator"})
_ROUND_PLACES = 6


def _content_digest(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_TRANSIENT_CLASSIFICATION = "independently_preclassified_transient_harness_failure"
_CANDIDATE_TERMINAL_FAILURE_CODE_BY_STATE = {
    "failed": "candidate_failed",
    "timed_out": "candidate_timed_out",
    "cancelled": "candidate_cancelled",
    "budget_exhausted": "candidate_budget_exhausted",
    "abandoned": "candidate_abandoned",
}
_CANDIDATE_TERMINAL_STATE_BY_FAILURE_CODE = {
    code: state for state, code in _CANDIDATE_TERMINAL_FAILURE_CODE_BY_STATE.items()
}
_FAILURE_CODES_BY_PLANE = {
    "none": frozenset({"none"}),
    "gate": frozenset({"gate_failed"}),
    "treatment": frozenset({
        "treatment_misdelivery",
        "service_reroute",
        "mandatory_telemetry_missing",
        "treatment_infrastructure_failure",
    }),
    "fixture": frozenset({
        "fixture_invalid",
        "fixture_stale",
        "fixture_partition_invalid",
        "fixture_oracle_invalid",
    }),
    "scorer": frozenset({
        "scorer_invalid",
        "scorer_stale",
        "scorer_calibration_missing",
    }),
    "ballot": frozenset({
        "ballot_missing",
        "ballot_non_blind",
        "ballot_provenance_incomplete",
        "ballot_rubric_stale",
    }),
    "adjudication": frozenset({
        "adjudication_disagreement_unresolved",
        "adjudicator_invalid",
        "adjudicator_stale",
        "adjudicator_reused_primary_scorer",
    }),
    "candidate": frozenset(_CANDIDATE_TERMINAL_FAILURE_CODE_BY_STATE.values()),
    "infrastructure": frozenset({
        "transient_harness_failure",
        "infrastructure_failure",
    }),
    "evidence_boundary": frozenset({
        "unclassifiable_attrition",
        "sensitive_evidence_violation",
        "required_evidence_missing",
    }),
    "partition": frozenset({
        "partition_mismatch",
        "partition_not_eligible",
        "cross_partition_reuse",
    }),
    "schema": frozenset({
        "schema_invalid",
        "binding_digest_mismatch",
    }),
}
_SCORE_DISPOSITIONS = frozenset({"accepted", "gate_failed", "non_scorable"})
_ATTRITION_CLASSIFICATION_INPUTS = frozenset({
    *ATTRITION_CLASSIFICATIONS,
    _TRANSIENT_CLASSIFICATION,
})


def _round(value: float) -> float:
    rounded = round(float(value), _ROUND_PLACES)
    return 0.0 if rounded == -0.0 else rounded


def _require_mapping(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _closed(value: object, allowed: frozenset[str], label: str) -> dict:
    row = _require_mapping(value, label)
    extra = set(row) - set(allowed)
    if extra:
        raise ValueError(f"{label} contains undeclared fields: {sorted(extra)}")
    return row


def _require(value: dict, fields: frozenset[str], label: str) -> None:
    missing = set(fields) - set(value)
    if missing:
        raise ValueError(f"{label} is missing required fields: {sorted(missing)}")


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _digest(value: object, label: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a sha256 digest")
    return value


def _validate_binding(value: object, label: str) -> dict:
    row = _closed(value, _BINDING_FIELDS, label)
    _require(row, _BINDING_FIELDS, label)
    return {
        "id": _text(row["id"], f"{label} ID"),
        "digest": _digest(row["digest"], f"{label} digest"),
    }


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    if not math.isfinite(float(value)):
        raise ValueError(f"{label} must be finite")
    return float(value)


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _non_negative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _validate_partition(
    partition: object,
    *,
    require_calibration: bool = False,
    label: str = "partition",
) -> dict:
    row = _closed(partition, _PARTITION_FIELDS, label)
    _require(row, _PARTITION_FIELDS, label)
    _text(row["partition_id"], f"{label} ID")
    _digest(row["partition_digest"], f"{label} digest")
    if row["partition_type"] not in _PARTITION_TYPES:
        raise ValueError("partition type is outside the closed inventory")
    if not isinstance(row["qualification_eligible"], bool):
        raise ValueError("partition qualification eligibility must be boolean")
    if require_calibration and (
        row["partition_type"] != "calibration" or row["qualification_eligible"] is not False
    ):
        raise ValueError("G56R-003 statistics require qualification-ineligible calibration")
    return copy.deepcopy(row)


def _evaluate_partition_boundary(partition: dict) -> tuple[dict, list[str]]:
    reasons: list[str] = []
    if partition["partition_type"] != "calibration" or partition["qualification_eligible"] is not False:
        reasons.append("partition_not_calibration_only")
    return {
        "status": "pass" if not reasons else "fail",
        "allowed_partition_type": "calibration",
        "qualification_eligible": False,
        "partition_binding": copy.deepcopy(partition),
        "reason_codes": reasons,
    }, reasons


def _validate_p95_guardrails(value: object) -> dict:
    row = _closed(value, _P95_GUARDRAIL_FIELDS, "p95 guardrails")
    _require(row, _P95_GUARDRAIL_FIELDS, "p95 guardrails")
    return {
        "raw_input_tokens_max": _positive_int(
            row["raw_input_tokens_max"], "p95 raw input token guardrail",
        ),
        "cached_input_tokens_max": _non_negative_int(
            row["cached_input_tokens_max"], "p95 cached input token guardrail",
        ),
        "output_tokens_max": _positive_int(
            row["output_tokens_max"], "p95 output token guardrail",
        ),
        "duration_ms_max": _positive_int(
            row["duration_ms_max"], "p95 duration guardrail",
        ),
    }


def _validate_workload_manifest(value: object) -> dict:
    row = _closed(value, _WORKLOAD_MANIFEST_FIELDS, "workload manifest")
    _require(row, _WORKLOAD_MANIFEST_FIELDS, "workload manifest")
    manifest = {
        "manifest_id": _text(row["manifest_id"], "workload manifest ID"),
        "manifest_digest": _digest(row["manifest_digest"], "workload manifest digest"),
        "minimum_unique_tasks": _positive_int(
            row["minimum_unique_tasks"], "minimum unique tasks",
        ),
        "unknown_stratum_policy": row["unknown_stratum_policy"],
        "strata": [],
    }
    if manifest["unknown_stratum_policy"] != "inconclusive":
        raise ValueError("unknown workload strata must fail closed as inconclusive")
    strata = row["strata"]
    if not isinstance(strata, list) or not strata:
        raise ValueError("workload manifest strata must be a non-empty array")
    seen: set[str] = set()
    total_weight = 0.0
    for raw in strata:
        stratum = _closed(raw, _WORKLOAD_STRATUM_FIELDS, "workload stratum")
        _require(stratum, _WORKLOAD_STRATUM_FIELDS, "workload stratum")
        stratum_id = _text(stratum["stratum_id"], "workload stratum ID")
        if stratum_id in seen:
            raise ValueError("workload strata must have unique IDs")
        seen.add(stratum_id)
        target_weight = _number(stratum["target_weight"], "workload target weight")
        if target_weight <= 0:
            raise ValueError("workload target weights must be positive")
        if not isinstance(stratum["long_horizon"], bool):
            raise ValueError("workload long_horizon must be boolean")
        total_weight += target_weight
        manifest["strata"].append({
            "stratum_id": stratum_id,
            "target_weight": target_weight,
            "long_horizon": stratum["long_horizon"],
            "p95_guardrails": _validate_p95_guardrails(stratum["p95_guardrails"]),
        })
    if not math.isclose(total_weight, 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("workload target weights must sum to 1.0")
    return manifest


def _validate_cache_policy(value: object) -> dict:
    row = _closed(value, _CACHE_POLICY_FIELDS, "cache policy")
    _require(row, _CACHE_POLICY_FIELDS, "cache policy")
    policy = {
        "policy_id": _text(row["policy_id"], "cache policy ID"),
        "policy_digest": _digest(row["policy_digest"], "cache policy digest"),
        "pair_isolation": row["pair_isolation"],
        "order_leakage_prohibited": row["order_leakage_prohibited"],
        "cache_state": row["cache_state"],
    }
    if policy["pair_isolation"] is not True:
        raise ValueError("cache policy must isolate each pair")
    if policy["order_leakage_prohibited"] is not True:
        raise ValueError("cache policy must prohibit treatment-order leakage")
    if policy["cache_state"] != "isolated_by_pair":
        raise ValueError("cache state must be isolated_by_pair")
    return policy


def _validate_campaign_budget(value: object) -> dict:
    row = _closed(value, _CAMPAIGN_BUDGET_FIELDS, "campaign budget")
    _require(row, _CAMPAIGN_BUDGET_FIELDS, "campaign budget")
    return {
        "max_attempts": _positive_int(row["max_attempts"], "campaign attempt budget"),
        "max_wall_clock_seconds": _positive_int(
            row["max_wall_clock_seconds"], "campaign wall-clock budget",
        ),
        "max_raw_input_tokens": _positive_int(
            row["max_raw_input_tokens"], "campaign raw input token budget",
        ),
        "max_cached_input_tokens": _non_negative_int(
            row["max_cached_input_tokens"], "campaign cached input token budget",
        ),
        "max_output_tokens": _positive_int(
            row["max_output_tokens"], "campaign output token budget",
        ),
        "max_candidates": _positive_int(row["max_candidates"], "campaign candidate budget"),
        "max_confirmation_entries": _non_negative_int(
            row["max_confirmation_entries"], "campaign confirmation-entry budget",
        ),
    }


def _validate_bindings(value: object, label: str) -> list[dict]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty array")
    return [_validate_binding(item, label) for item in value]


def _validate_freeze_provenance(value: object) -> dict:
    row = _closed(value, _FREEZE_PROVENANCE_FIELDS, "freeze provenance")
    _require(row, _FREEZE_PROVENANCE_FIELDS, "freeze provenance")
    frozen_at = _text(row["frozen_at"], "freeze timestamp")
    if row["frozen_after_calibration"] is not True:
        raise ValueError("analysis plan may freeze only after calibration")
    if row["cohort_outcome_observed"] is not False:
        raise ValueError("analysis plan must freeze before cohort outcomes are observed")
    return {
        "frozen_at": frozen_at,
        "frozen_after_calibration": True,
        "cohort_outcome_observed": False,
        "pre_cohort_outcome_absence_digest": _digest(
            row["pre_cohort_outcome_absence_digest"],
            "pre-cohort outcome absence digest",
        ),
        "independent_review_binding": _validate_binding(
            row["independent_review_binding"],
            "independent review binding",
        ),
    }


def _validate_floor(value: object, label: str) -> dict:
    row = _require_mapping(value, label)
    for field in ("metric", "minimum"):
        if field not in row:
            raise ValueError(f"{label} is missing {field}")
    minimum = _number(row["minimum"], f"{label} minimum")
    if minimum < 0 or minimum > 1:
        raise ValueError(f"{label} minimum must be between 0 and 1")
    metric = _text(row["metric"], f"{label} metric")
    allowed = (
        {"semantic_score", "semantic_acceptance_rate"}
        if label == "semantic floor"
        else {"reliability_score", "non_candidate_failure_free_rate"}
    )
    if metric not in allowed:
        raise ValueError(f"{label} metric is outside the closed inventory")
    return {"metric": metric, "minimum": minimum}


def _validate_quality_floors(value: object) -> dict:
    row = _closed(value, _QUALITY_FLOOR_FIELDS, "quality floors")
    _require(row, _QUALITY_FLOOR_FIELDS, "quality floors")
    if row["evaluation_order"] != 1:
        raise ValueError("quality floors must be the first statistical gate")
    return {
        "evaluation_order": 1,
        "semantic": _validate_floor(row["semantic"], "semantic floor"),
        "reliability": _validate_floor(row["reliability"], "reliability floor"),
    }


def _validate_non_inferiority(value: object) -> dict:
    row = _closed(value, _NON_INFERIORITY_FIELDS, "non-inferiority policy")
    _require(row, _NON_INFERIORITY_FIELDS, "non-inferiority policy")
    if row["evaluation_order"] != 2:
        raise ValueError("non-inferiority must run after quality floors")
    endpoints = row["endpoints"]
    if not isinstance(endpoints, list) or not endpoints:
        raise ValueError("non-inferiority endpoints must be a non-empty array")
    if set(endpoints) - _ENDPOINTS or len(set(endpoints)) != len(endpoints):
        raise ValueError("non-inferiority endpoints are outside the closed inventory")
    margins = _closed(row["margins"], frozenset(endpoints), "non-inferiority margins")
    sample_sizes = _closed(row["sample_sizes"], frozenset({"per_role_minimum"}), "sample sizes")
    sample_assumptions = _closed(
        row["sample_size_assumptions"],
        frozenset({"variance_source_binding", "expected_missingness_rate"}),
        "sample-size assumptions",
    )
    if row["cluster_unit"] not in {"role", "fixture"}:
        raise ValueError("cluster unit must be role or fixture")
    confidence_level = _number(row["confidence_level"], "confidence level")
    alpha = _number(row["alpha"], "alpha")
    power = _number(row["power"], "power")
    if not 0 < confidence_level < 1 or not 0 < alpha < 1 or not 0 < power < 1:
        raise ValueError("confidence level, alpha, and power must be inside (0, 1)")
    if not math.isclose(confidence_level, 1.0 - alpha, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("confidence level must equal one minus alpha")
    if row["cluster_adjustment"] != "cluster_robust":
        raise ValueError("cluster adjustment must be cluster_robust")
    if row["multiplicity_adjustment"] not in {"holm", "bonferroni", "none"}:
        raise ValueError("multiplicity adjustment is outside the closed inventory")
    missingness = _number(sample_assumptions["expected_missingness_rate"], "expected missingness")
    if missingness < 0 or missingness > 1:
        raise ValueError("expected missingness must be between 0 and 1")
    return {
        "evaluation_order": 2,
        "endpoints": list(endpoints),
        "margins": {endpoint: _number(margins[endpoint], f"{endpoint} margin") for endpoint in endpoints},
        "confidence_level": confidence_level,
        "alpha": alpha,
        "power": power,
        "sample_sizes": {"per_role_minimum": _positive_int(
            sample_sizes["per_role_minimum"], "per-role sample minimum",
        )},
        "sample_size_assumptions": copy.deepcopy(sample_assumptions),
        "cluster_unit": row["cluster_unit"],
        "cluster_adjustment": str(row["cluster_adjustment"]),
        "multiplicity_adjustment": str(row["multiplicity_adjustment"]),
    }


def _validate_pareto_policy(value: object) -> dict:
    row = _closed(value, _PARETO_POLICY_FIELDS, "Pareto policy")
    _require(row, _PARETO_POLICY_FIELDS, "Pareto policy")
    if row["evaluation_order"] != 3:
        raise ValueError("Pareto policy must run after non-inferiority")
    if tuple(row["dimensions"]) != PARETO_DIMENSIONS:
        raise ValueError("Pareto dimensions must match the frozen raw vector")
    if row["directions"] != PARETO_DIRECTIONS:
        raise ValueError("Pareto directions must match the frozen policy")
    if row["weights_prohibited"] is not True:
        raise ValueError("Pareto weights are prohibited")
    if row["mixed_or_tied_result"] != "inconclusive":
        raise ValueError("mixed or tied Pareto results must remain inconclusive")
    return copy.deepcopy(row)


def _validate_plan(analysis_plan: object) -> dict:
    plan = _closed(copy.deepcopy(analysis_plan), _ANALYSIS_PLAN_FIELDS, "analysis plan")
    if plan.get("schema_version") != "analysis-plan.v1" or plan.get("status") != "frozen":
        raise ValueError("analysis plan must be a frozen analysis-plan.v1 object")
    _require(plan, _ANALYSIS_PLAN_FIELDS, "analysis plan")
    expected_digest = _content_digest({
        key: value
        for key, value in plan.items()
        if key not in {"analysis_plan_id", "analysis_plan_digest"}
    })
    if plan["analysis_plan_digest"] != expected_digest:
        raise ValueError("analysis plan digest does not match frozen content")
    expected_id = _content_digest({
        key: value
        for key, value in plan.items()
        if key != "analysis_plan_id"
    })
    if plan["analysis_plan_id"] != expected_id:
        raise ValueError("analysis plan ID does not match frozen content")
    validated = plan
    validated["analysis_plan_id"] = _digest(plan["analysis_plan_id"], "analysis plan ID")
    validated["analysis_plan_version"] = _text(
        plan["analysis_plan_version"], "analysis plan version",
    )
    validated["analysis_plan_digest"] = _digest(
        plan["analysis_plan_digest"], "analysis plan digest",
    )
    validated["calibration_partition_binding"] = _validate_partition(
        plan["calibration_partition_binding"],
        require_calibration=True,
        label="analysis plan calibration partition",
    )
    validated["calibration_evidence_bindings"] = _validate_bindings(
        plan["calibration_evidence_bindings"],
        "calibration evidence binding",
    )
    validated["freeze_provenance"] = _validate_freeze_provenance(
        plan["freeze_provenance"]
    )
    validated["workload_manifest"] = _validate_workload_manifest(plan["workload_manifest"])
    validated["cache_policy"] = _validate_cache_policy(plan["cache_policy"])
    validated["campaign_budget"] = _validate_campaign_budget(plan["campaign_budget"])
    validated["quality_floors"] = _validate_quality_floors(plan["quality_floors"])
    validated["non_inferiority"] = _validate_non_inferiority(plan["non_inferiority"])
    validated["pareto_policy"] = _validate_pareto_policy(plan["pareto_policy"])
    if plan["estimand_policy"].get("assigned_attempt") is not True:
        raise ValueError("statistics require the assigned-attempt estimand")
    if plan["estimand_policy"].get("candidate_terminal_acceptance_zero") is not True:
        raise ValueError("candidate-caused terminals must carry acceptance zero")
    if tuple(plan["estimand_policy"].get("candidate_terminal_states", [])) != CANDIDATE_TERMINAL_STATES:
        raise ValueError("candidate terminal states must match the closed policy")
    if plan["estimand_policy"].get("complete_case_filtering") is not False:
        raise ValueError("complete-case filtering is prohibited")
    attrition_policy = _require_mapping(plan["attrition_policy"], "attrition policy")
    attrition_cap = _number(attrition_policy.get("cap"), "attrition cap")
    if attrition_cap < 0 or attrition_cap > 1:
        raise ValueError("attrition cap must be between 0 and 1")
    if attrition_policy.get("unclassifiable_attrition") != "evidence_boundary_failure":
        raise ValueError("unclassifiable attrition must remain an evidence-boundary failure")
    if attrition_policy.get("unclassifiable_result") != "inconclusive":
        raise ValueError("unclassifiable attrition must be inconclusive")
    if attrition_policy.get("complete_case_filtering") is not False:
        raise ValueError("attrition policy must prohibit complete-case filtering")
    rerun_policy = _require_mapping(plan["rerun_policy"], "rerun policy")
    if rerun_policy.get("eligible_failure") != _TRANSIENT_CLASSIFICATION:
        raise ValueError("only independently preclassified transient harness failures may rerun")
    if plan["rerun_policy"].get("scope") != "complete_pair":
        raise ValueError("reruns must be complete-pair reruns")
    _non_negative_int(rerun_policy.get("cap"), "rerun cap")
    if plan["rerun_policy"].get("one_arm_rerun_prohibited") is not True:
        raise ValueError("one-arm reruns are prohibited")
    if plan["terminal_policy"].get("no_forced_ranking") is not True:
        raise ValueError("terminal policy must prohibit forced rankings")
    if plan["racing_policy"].get("enabled") is not False:
        raise ValueError("racing policy must be frozen disabled for deterministic replay")
    if plan["futility_policy"].get("enabled") is not False:
        raise ValueError("futility policy must be frozen disabled for deterministic replay")
    return validated


def _ordered_results(stop_gate: str | None = None) -> list[dict]:
    rows: list[dict] = []
    stopped = False
    for index, gate in enumerate(DECISION_SEQUENCE, start=1):
        if stopped:
            result = "not_evaluated"
        elif gate == stop_gate:
            result = "fail"
            stopped = True
        else:
            result = "pass"
        rows.append({"sequence": index, "gate": gate, "result": result})
    return rows


def _not_evaluated(label: str) -> dict:
    if label == "pareto":
        return {"status": "not_evaluated", "result": "not_evaluated"}
    return {"status": "not_evaluated"}


def _candidate_terminal_state(row: dict) -> str | None:
    terminal_state = row.get("terminal_state")
    if terminal_state in CANDIDATE_TERMINAL_STATES:
        return str(terminal_state)
    failure_code = row.get("failure_code")
    if row.get("failure_plane") == "candidate" and failure_code in _CANDIDATE_TERMINAL_STATE_BY_FAILURE_CODE:
        return _CANDIDATE_TERMINAL_STATE_BY_FAILURE_CODE[str(failure_code)]
    return None


def _normalize_attempt_row(raw: dict) -> dict:
    row = copy.deepcopy(_validate_outcome_row(raw))
    vector = copy.deepcopy(_require_mapping(row.get("resource_vector"), "resource vector"))
    if "input_tokens" in vector and "raw_input_tokens" not in vector:
        vector["raw_input_tokens"] = vector["input_tokens"]
    terminal_state = row.get("terminal_state", vector.get("terminal_state"))
    candidate_terminal = _candidate_terminal_state(row)
    if candidate_terminal is not None:
        vector["acceptance"] = 0
        vector["terminal_state"] = candidate_terminal
        row["terminal_state"] = candidate_terminal
    elif isinstance(terminal_state, str) and terminal_state:
        if terminal_state == "succeeded":
            terminal_state = "completed"
        row["terminal_state"] = terminal_state
        vector["terminal_state"] = terminal_state
    row["resource_vector"] = vector
    return row


def _validate_failure_code(row: dict) -> None:
    plane = row.get("failure_plane")
    code = row.get("failure_code")
    if plane not in _FAILURE_CODES_BY_PLANE:
        raise ValueError("failure plane is outside the closed inventory")
    if code not in _FAILURE_CODES_BY_PLANE[plane]:
        raise ValueError("failure code is outside the closed inventory")
    if plane == "none" and code != "none":
        raise ValueError("failure code none coupling is invalid")
    if plane != "none" and code == "none":
        raise ValueError("non-none failure plane requires a closed failure code")


def _validate_outcome_row(raw: dict) -> dict:
    row = _closed(raw, _OUTCOME_FIELDS, "paired outcome")
    _require(row, _OUTCOME_FIELDS, "paired outcome")
    row["assignment_binding"] = _validate_binding(
        row["assignment_binding"], "paired outcome assignment binding"
    )
    row["score_bundle_binding"] = _validate_binding(
        row["score_bundle_binding"], "paired outcome score bundle binding"
    )
    if row["score_disposition"] not in _SCORE_DISPOSITIONS:
        raise ValueError("score disposition is outside the closed inventory")
    if row["attrition_classification"] not in _ATTRITION_CLASSIFICATION_INPUTS:
        raise ValueError("attrition classification is outside the closed inventory")
    _validate_failure_code(row)
    return row


def _attempt_index(raw: dict) -> int:
    value = raw.get("attempt_index", 1)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("attempt index must be a positive integer")
    return value


def _attrition_classification(row: dict) -> str:
    if _candidate_terminal_state(row) is not None:
        return "candidate_terminal"
    if (
        row.get("failure_plane") == "infrastructure"
        and row.get("failure_code") == "transient_harness_failure"
    ):
        if row.get("attrition_classification") == _TRANSIENT_CLASSIFICATION:
            return "transient_harness_failure"
        return "unclassifiable_attrition"
    if (
        row.get("failure_plane") == "evidence_boundary"
        and row.get("failure_code") == "unclassifiable_attrition"
    ):
        return "unclassifiable_attrition"
    if row.get("attrition_classification") == "unclassifiable_attrition":
        return "unclassifiable_attrition"
    if row.get("score_disposition", "accepted") != "accepted":
        return "unclassifiable_attrition"
    if row.get("failure_plane", "none") != "none" or row.get("failure_code", "none") != "none":
        return "unclassifiable_attrition"
    return "complete"


def _empty_completeness_summary(plan: dict) -> dict:
    return {
        "status": "fail",
        "assigned_pair_count": 0,
        "retained_pair_count": 0,
        "complete_case_filtering": False,
        "candidate_terminal_acceptance_zero": True,
        "candidate_terminal_counts": {state: 0 for state in CANDIDATE_TERMINAL_STATES},
        "incomplete_pair_ids": [],
        "attrition": {
            "count": 0,
            "rate": 0.0,
            "cap": _round(plan["attrition_policy"]["cap"]),
            "status": "within_cap",
            "classifications": {item: 0 for item in ATTRITION_CLASSIFICATIONS},
        },
        "reruns": {
            "cap": plan["rerun_policy"]["cap"],
            "complete_pair_reruns": 0,
            "decisions": {},
        },
        "reason_codes": ["missing_pairs"],
    }


def _resource_usage(row: dict, dimension: str) -> int:
    vector = row.get("resource_vector")
    if not isinstance(vector, dict) or dimension not in vector:
        return 0
    return int(_non_negative_int(vector[dimension], f"budget {dimension} usage"))


def _row_usage(row: dict, field: str) -> int:
    value = row.get(field, 0)
    return _non_negative_int(value, f"budget {field} usage")


def _evaluate_campaign_budget(plan: dict, paired_outcomes: object) -> tuple[dict, list[str]]:
    budget = plan["campaign_budget"]
    rows = [row for row in paired_outcomes if isinstance(row, dict)] if isinstance(paired_outcomes, list) else []
    candidate_ids = {
        str(row.get("candidate_route_id") or "candidate-route")
        for row in rows
        if row.get("arm") == "candidate"
    }
    usage = {
        "max_attempts": len(rows),
        "max_wall_clock_seconds": sum(_row_usage(row, "wall_clock_seconds") for row in rows),
        "max_raw_input_tokens": sum(_resource_usage(row, "raw_input_tokens") for row in rows),
        "max_cached_input_tokens": sum(_resource_usage(row, "cached_input_tokens") for row in rows),
        "max_output_tokens": sum(_resource_usage(row, "output_tokens") for row in rows),
        "max_candidates": len(candidate_ids),
        "max_confirmation_entries": sum(_row_usage(row, "confirmation_entries") for row in rows),
    }
    reasons = [
        f"budget_{field}_exceeded"
        for field in CAMPAIGN_BUDGET_FIELDS
        if usage[field] > budget[field]
    ]
    return {
        "status": "pass" if not reasons else "fail",
        "ceilings": copy.deepcopy(budget),
        "usage": usage,
        "reason_codes": reasons,
    }, reasons


def _classifications_for_attempt(arms: dict[str, dict]) -> dict[str, str]:
    return {arm: _attrition_classification(row) for arm, row in arms.items()}


def _pair_bindings_match(candidate: dict, comparator: dict) -> bool:
    return all(candidate.get(field) == comparator.get(field) for field in ("role_id", "fixture_id", "task_id"))


def _pair_outcomes(paired_outcomes: object, plan: dict) -> tuple[list[dict], list[str], dict]:
    if not isinstance(paired_outcomes, list) or not paired_outcomes:
        summary = _empty_completeness_summary(plan)
        return [], ["missing_pairs"], summary

    raw_pairs: dict[str, dict[int, dict[str, dict]]] = defaultdict(lambda: defaultdict(dict))
    reasons: list[str] = []
    for raw in paired_outcomes:
        if not isinstance(raw, dict):
            reasons.append("invalid_outcome")
            continue
        pair_id = raw.get("pair_id")
        arm = raw.get("arm")
        if not isinstance(pair_id, str) or not pair_id or arm not in _ARMS:
            reasons.append("invalid_pair_identity")
            continue
        attempt_index = _attempt_index(raw)
        if arm in raw_pairs[pair_id][attempt_index]:
            reasons.append("duplicate_pair_arm")
            continue
        raw_pairs[pair_id][attempt_index][arm] = _normalize_attempt_row(raw)

    pairs: list[dict] = []
    incomplete_pair_ids: set[str] = set()
    attrition_pair_ids: set[str] = set()
    attrition_counts = {item: 0 for item in ATTRITION_CLASSIFICATIONS}
    candidate_terminal_counts = {state: 0 for state in CANDIDATE_TERMINAL_STATES}
    rerun_decisions: dict[str, str] = {}
    complete_pair_reruns = 0
    rerun_cap = plan["rerun_policy"]["cap"]

    for pair_id in sorted(raw_pairs):
        attempts = raw_pairs[pair_id]
        attempt_numbers = sorted(attempts)
        selected: dict | None = None
        reruns_used = 0
        index = 0
        while index < len(attempt_numbers):
            attempt_number = attempt_numbers[index]
            arms = attempts[attempt_number]
            classifications = _classifications_for_attempt(arms)
            has_transient = "transient_harness_failure" in classifications.values()
            has_unclassifiable = "unclassifiable_attrition" in classifications.values()
            if set(arms) != _ARMS:
                if has_transient:
                    attrition_pair_ids.add(pair_id)
                    attrition_counts["transient_harness_failure"] += 1
                    if reruns_used >= rerun_cap or index == len(attempt_numbers) - 1:
                        reasons.append("incomplete_after_rerun_cap")
                        rerun_decisions[pair_id] = "rerun_cap_exhausted"
                    else:
                        next_arms = attempts[attempt_numbers[index + 1]]
                        if set(next_arms) != _ARMS:
                            reasons.append("one_arm_rerun_prohibited")
                            rerun_decisions[pair_id] = "one_arm_rerun_prohibited"
                        else:
                            reruns_used += 1
                            complete_pair_reruns += 1
                            rerun_decisions[pair_id] = "complete_pair_rerun"
                            index += 1
                            continue
                elif has_unclassifiable:
                    attrition_pair_ids.add(pair_id)
                    attrition_counts["unclassifiable_attrition"] += 1
                    reasons.append("unclassifiable_attrition")
                else:
                    reasons.append("unpaired_comparison")
                incomplete_pair_ids.add(pair_id)
                break

            if has_unclassifiable:
                attrition_pair_ids.add(pair_id)
                attrition_counts["unclassifiable_attrition"] += 1
                reasons.append("unclassifiable_attrition")
                incomplete_pair_ids.add(pair_id)
                break
            if has_transient:
                attrition_pair_ids.add(pair_id)
                attrition_counts["transient_harness_failure"] += 1
                if reruns_used >= rerun_cap or index == len(attempt_numbers) - 1:
                    reasons.append("incomplete_after_rerun_cap")
                    rerun_decisions[pair_id] = "rerun_cap_exhausted"
                    incomplete_pair_ids.add(pair_id)
                    break
                next_arms = attempts[attempt_numbers[index + 1]]
                if set(next_arms) != _ARMS:
                    reasons.append("one_arm_rerun_prohibited")
                    rerun_decisions[pair_id] = "one_arm_rerun_prohibited"
                    incomplete_pair_ids.add(pair_id)
                    break
                reruns_used += 1
                complete_pair_reruns += 1
                rerun_decisions[pair_id] = "complete_pair_rerun"
                index += 1
                continue

            candidate = arms["candidate"]
            comparator = arms["comparator"]
            if not _pair_bindings_match(candidate, comparator):
                reasons.append("pair_binding_mismatch")
                incomplete_pair_ids.add(pair_id)
                break
            selected = {"pair_id": pair_id, "candidate": candidate, "comparator": comparator}
            for row in (candidate, comparator):
                terminal_state = _candidate_terminal_state(row)
                if terminal_state is not None:
                    attrition_counts["candidate_terminal"] += 1
                    candidate_terminal_counts[terminal_state] += 1
            break

        if selected is None:
            incomplete_pair_ids.add(pair_id)
        else:
            pairs.append(selected)

    assigned_pair_count = len(raw_pairs)
    attrition_rate = 0.0 if assigned_pair_count == 0 else len(attrition_pair_ids) / assigned_pair_count
    attrition_status = "within_cap"
    if attrition_rate > plan["attrition_policy"]["cap"]:
        reasons.append("attrition_cap_exceeded")
        attrition_status = "exceeds_cap"
    if assigned_pair_count == 0:
        reasons.append("missing_pairs")
    reason_codes = sorted(set(reasons))
    status = "pass" if not reason_codes else "fail"
    if status != "pass":
        pairs = []
    summary = {
        "status": status,
        "assigned_pair_count": assigned_pair_count,
        "retained_pair_count": len(pairs) if status == "pass" else 0,
        "complete_case_filtering": False,
        "candidate_terminal_acceptance_zero": True,
        "candidate_terminal_counts": candidate_terminal_counts,
        "incomplete_pair_ids": sorted(incomplete_pair_ids if status != "pass" else set()),
        "attrition": {
            "count": len(attrition_pair_ids),
            "rate": _round(attrition_rate),
            "cap": _round(plan["attrition_policy"]["cap"]),
            "status": attrition_status,
            "classifications": attrition_counts,
        },
        "reruns": {
            "cap": rerun_cap,
            "complete_pair_reruns": complete_pair_reruns,
            "decisions": rerun_decisions,
        },
        "reason_codes": reason_codes,
    }
    return pairs, reason_codes, summary


def _cache_policy_binding(cache_policy: dict) -> dict:
    return {"id": cache_policy["policy_id"], "digest": cache_policy["policy_digest"]}


def _validate_outcome_workload_cache(
    row: dict,
    strata_by_id: dict[str, dict],
    cache_policy: dict,
) -> tuple[str | None, list[str]]:
    reasons: list[str] = []
    stratum_id = row.get("workload_stratum_id")
    if not isinstance(stratum_id, str) or stratum_id not in strata_by_id:
        reasons.append("unknown_workload_stratum")
        stratum_id = None
    binding = row.get("cache_policy_binding")
    if not isinstance(binding, dict) or set(binding) != set(_CACHE_POLICY_BINDING_FIELDS):
        reasons.append("cache_policy_binding_mismatch")
    elif binding != _cache_policy_binding(cache_policy):
        reasons.append("cache_policy_binding_mismatch")
    if row.get("cache_state") != cache_policy["cache_state"]:
        reasons.append("cache_state_not_isolated")
    if row.get("treatment_order_leakage") is not False:
        reasons.append("treatment_order_leakage")
    return stratum_id, reasons


def _p95(values: list[float]) -> float:
    if not values:
        raise ValueError("p95 requires at least one value")
    ordered = sorted(values)
    index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return ordered[index]


def _empty_stratum_summary(stratum: dict) -> dict:
    base = {
        "target_weight": _round(stratum["target_weight"]),
        "long_horizon": stratum["long_horizon"],
        "p95_guardrails": copy.deepcopy(stratum["p95_guardrails"]),
    }
    for arm in _ARMS:
        base[arm] = {"count": 0, "dimensions": {}}
    return base


def _evaluate_workload_cache(plan: dict, pairs: list[dict]) -> tuple[dict, list[str]]:
    manifest = plan["workload_manifest"]
    cache_policy = plan["cache_policy"]
    strata_by_id = {item["stratum_id"]: item for item in manifest["strata"]}
    values: dict[str, dict[str, dict[str, list[float]]]] = {
        stratum_id: {
            arm: {dimension: [] for dimension in _P95_DIMENSION_GUARDRAILS}
            for arm in _ARMS
        }
        for stratum_id in strata_by_id
    }
    summary = {
        "status": "pass",
        "minimum_unique_tasks": manifest["minimum_unique_tasks"],
        "unique_task_count": 0,
        "unknown_stratum_policy": manifest["unknown_stratum_policy"],
        "cache_policy_binding": _cache_policy_binding(cache_policy),
        "strata": {
            stratum_id: _empty_stratum_summary(stratum)
            for stratum_id, stratum in strata_by_id.items()
        },
        "reason_codes": [],
    }
    reasons: list[str] = []
    unique_tasks: set[str] = set()
    for pair in pairs:
        task_id = pair["candidate"].get("task_id")
        if not isinstance(task_id, str) or not task_id:
            reasons.append("task_binding_missing")
        else:
            unique_tasks.add(task_id)
        for arm in _ARMS:
            row = pair[arm]
            stratum_id, row_reasons = _validate_outcome_workload_cache(
                row, strata_by_id, cache_policy,
            )
            reasons.extend(row_reasons)
            if stratum_id is None:
                continue
            vector = _require_mapping(row.get("resource_vector"), "resource vector")
            for dimension in _P95_DIMENSION_GUARDRAILS:
                if dimension not in vector:
                    reasons.append(f"p95_{dimension}_evidence_missing")
                    continue
                values[stratum_id][arm][dimension].append(
                    _number(vector[dimension], f"{arm} {dimension}"),
                )
    summary["unique_task_count"] = len(unique_tasks)
    if len(unique_tasks) < manifest["minimum_unique_tasks"]:
        reasons.append("minimum_unique_tasks_not_met")
    for stratum_id, stratum in strata_by_id.items():
        guardrails = stratum["p95_guardrails"]
        for arm in _ARMS:
            arm_summary = summary["strata"][stratum_id][arm]
            arm_values = values[stratum_id][arm]
            arm_summary["count"] = max((len(item) for item in arm_values.values()), default=0)
            if arm_summary["count"] == 0:
                reasons.append(f"weighted_stratum_missing_{arm}")
            for dimension, guardrail_key in _P95_DIMENSION_GUARDRAILS.items():
                dimension_values = arm_values[dimension]
                if not dimension_values:
                    continue
                mean = _mean(dimension_values)
                p95 = _p95(dimension_values)
                guardrail = guardrails[guardrail_key]
                status = "pass" if p95 <= guardrail else "fail"
                if status != "pass":
                    reasons.append(f"p95_{dimension}_guardrail_exceeded")
                arm_summary["dimensions"][dimension] = {
                    "mean": _round(mean),
                    "p95": _round(p95),
                    "guardrail": _round(guardrail),
                    "status": status,
                }
    summary["reason_codes"] = sorted(set(reasons))
    summary["status"] = "pass" if not summary["reason_codes"] else "fail"
    return summary, summary["reason_codes"]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _evaluate_quality_floors(plan: dict, pairs: list[dict]) -> tuple[dict, list[str]]:
    floors = plan["quality_floors"]
    candidate_rows = [pair["candidate"] for pair in pairs]
    metric_values = {
        "semantic_score": lambda row: _number(
            row["semantic_score"], "candidate semantic score"
        ),
        "reliability_score": lambda row: _number(
            row["reliability_score"], "candidate reliability score"
        ),
        "semantic_acceptance_rate": lambda row: 1.0
        if row["score_disposition"] == "accepted" and row["semantic_score"] is not None
        else 0.0,
        "non_candidate_failure_free_rate": lambda row: 1.0
        if row["failure_plane"] in {"none", "candidate"}
        else 0.0,
    }
    semantic_metric = floors["semantic"]["metric"]
    reliability_metric = floors["reliability"]["metric"]
    semantic_mean = _mean([
        metric_values[semantic_metric](row) for row in candidate_rows
    ])
    reliability_mean = _mean([
        metric_values[reliability_metric](row) for row in candidate_rows
    ])
    semantic_status = "pass" if semantic_mean >= floors["semantic"]["minimum"] else "fail"
    reliability_status = "pass" if reliability_mean >= floors["reliability"]["minimum"] else "fail"
    reasons: list[str] = []
    if semantic_status != "pass":
        reasons.append("semantic_floor_failed")
    if reliability_status != "pass":
        reasons.append("reliability_floor_failed")
    return {
        "status": "pass" if not reasons else "fail",
        "semantic": {
            "metric": floors["semantic"]["metric"],
            "candidate_mean": _round(semantic_mean),
            "minimum": _round(floors["semantic"]["minimum"]),
            "status": semantic_status,
        },
        "reliability": {
            "metric": floors["reliability"]["metric"],
            "candidate_mean": _round(reliability_mean),
            "minimum": _round(floors["reliability"]["minimum"]),
            "status": reliability_status,
        },
    }, reasons


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    maximum_iterations = 200
    epsilon = 3e-14
    floor = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < floor:
        d = floor
    d = 1.0 / d
    result = d
    for iteration in range(1, maximum_iterations + 1):
        even = 2 * iteration
        coefficient = iteration * (b - iteration) * x / (
            (qam + even) * (a + even)
        )
        d = 1.0 + coefficient * d
        if abs(d) < floor:
            d = floor
        c = 1.0 + coefficient / c
        if abs(c) < floor:
            c = floor
        d = 1.0 / d
        result *= d * c
        coefficient = -(a + iteration) * (qab + iteration) * x / (
            (a + even) * (qap + even)
        )
        d = 1.0 + coefficient * d
        if abs(d) < floor:
            d = floor
        c = 1.0 + coefficient / c
        if abs(c) < floor:
            c = floor
        d = 1.0 / d
        delta = d * c
        result *= delta
        if abs(delta - 1.0) < epsilon:
            break
    return result


def _regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _beta_continued_fraction(a, b, x) / a
    return 1.0 - front * _beta_continued_fraction(b, a, 1.0 - x) / b


def _student_t_survival(value: float, degrees_of_freedom: int) -> float:
    if degrees_of_freedom < 1:
        raise ValueError("finite-cluster inference requires positive degrees of freedom")
    x = degrees_of_freedom / (degrees_of_freedom + value * value)
    tail = 0.5 * _regularized_incomplete_beta(
        degrees_of_freedom / 2.0,
        0.5,
        x,
    )
    return tail if value >= 0 else 1.0 - tail


def _student_t_critical(alpha: float, degrees_of_freedom: int) -> float:
    lower = 0.0
    upper = 1.0
    while _student_t_survival(upper, degrees_of_freedom) > alpha:
        upper *= 2.0
    for _ in range(100):
        midpoint = (lower + upper) / 2.0
        if _student_t_survival(midpoint, degrees_of_freedom) > alpha:
            lower = midpoint
        else:
            upper = midpoint
    return (lower + upper) / 2.0


def _cluster_key(pair: dict, cluster_unit: str) -> str:
    field = "role_id" if cluster_unit == "role" else "fixture_id"
    return str(pair["candidate"][field])


def _cluster_endpoint(
    endpoint: str,
    pairs: list[dict],
    policy: dict,
    adjusted_alpha: float,
) -> dict:
    cluster_unit = policy["cluster_unit"]
    per_cluster_minimum = policy["sample_sizes"]["per_role_minimum"]
    clustered: dict[str, list[float]] = defaultdict(list)
    for pair in pairs:
        candidate = _number(pair["candidate"][endpoint], f"candidate {endpoint}")
        comparator = _number(pair["comparator"][endpoint], f"comparator {endpoint}")
        clustered[_cluster_key(pair, cluster_unit)].append(candidate - comparator)
    cluster_means = {cluster: _mean(values) for cluster, values in clustered.items()}
    pair_count = sum(len(values) for values in clustered.values())
    insufficient = [
        cluster for cluster, values in clustered.items()
        if len(values) < per_cluster_minimum
    ]
    mean_difference = _mean(list(cluster_means.values()))
    if insufficient:
        return {
            "status": "uncertain",
            "cluster_unit": cluster_unit,
            "cluster_count": len(cluster_means),
            "pair_count": pair_count,
            "mean_difference": _round(mean_difference),
            "lower_confidence_bound": None,
            "margin": _round(policy["margins"][endpoint]),
            "confidence_level": _round(policy["confidence_level"]),
            "alpha": _round(policy["alpha"]),
            "adjusted_alpha": _round(adjusted_alpha),
            "adjusted_confidence_level": _round(1.0 - adjusted_alpha),
            "reason": "sample_size_insufficient",
        }
    if len(cluster_means) < 2:
        return {
            "status": "uncertain",
            "cluster_unit": cluster_unit,
            "cluster_count": len(cluster_means),
            "pair_count": pair_count,
            "mean_difference": _round(mean_difference),
            "lower_confidence_bound": None,
            "margin": _round(policy["margins"][endpoint]),
            "confidence_level": _round(policy["confidence_level"]),
            "alpha": _round(policy["alpha"]),
            "adjusted_alpha": _round(adjusted_alpha),
            "adjusted_confidence_level": _round(1.0 - adjusted_alpha),
            "reason": "independent_cluster_count_insufficient",
        }
    values = list(cluster_means.values())
    variance = sum((value - mean_difference) ** 2 for value in values) / (len(values) - 1)
    standard_error = math.sqrt(variance) / math.sqrt(len(values))
    degrees_of_freedom = len(values) - 1
    margin = policy["margins"][endpoint]
    if standard_error == 0.0:
        statistic = math.inf if mean_difference >= margin else -math.inf
        p_value = 0.0 if mean_difference >= margin else 1.0
    else:
        statistic = (mean_difference - margin) / standard_error
        p_value = _student_t_survival(statistic, degrees_of_freedom)
    critical = _student_t_critical(adjusted_alpha, degrees_of_freedom)
    lower_bound = mean_difference - critical * standard_error
    status = "pass" if p_value <= adjusted_alpha else "fail"
    return {
        "status": status,
        "cluster_unit": cluster_unit,
        "cluster_count": len(cluster_means),
        "pair_count": pair_count,
        "mean_difference": _round(mean_difference),
        "lower_confidence_bound": _round(lower_bound),
        "margin": _round(margin),
        "confidence_level": _round(policy["confidence_level"]),
        "alpha": _round(policy["alpha"]),
        "adjusted_alpha": _round(adjusted_alpha),
        "adjusted_confidence_level": _round(1.0 - adjusted_alpha),
        "degrees_of_freedom": degrees_of_freedom,
        "p_value": _round(p_value),
    }


def _evaluate_non_inferiority(plan: dict, pairs: list[dict]) -> tuple[dict, list[str]]:
    policy = plan["non_inferiority"]
    endpoint_count = len(policy["endpoints"])
    initial_alpha = (
        policy["alpha"] / endpoint_count
        if policy["multiplicity_adjustment"] in {"holm", "bonferroni"}
        else policy["alpha"]
    )
    endpoints = {
        endpoint: _cluster_endpoint(endpoint, pairs, policy, initial_alpha)
        for endpoint in policy["endpoints"]
    }
    if (
        policy["multiplicity_adjustment"] == "holm"
        and not any(item["status"] == "uncertain" for item in endpoints.values())
    ):
        ordered = sorted(
            policy["endpoints"],
            key=lambda endpoint: endpoints[endpoint]["p_value"],
        )
        continue_rejecting = True
        for rank, endpoint in enumerate(ordered):
            adjusted_alpha = policy["alpha"] / (endpoint_count - rank)
            item = _cluster_endpoint(endpoint, pairs, policy, adjusted_alpha)
            if not continue_rejecting or item["p_value"] > adjusted_alpha:
                item["status"] = "fail"
                continue_rejecting = False
            endpoints[endpoint] = item
    reasons: list[str] = []
    if any(item["status"] == "uncertain" for item in endpoints.values()):
        status = "uncertain"
        reasons.extend(sorted({
            item.get("reason", "sample_size_insufficient")
            for item in endpoints.values()
            if item["status"] == "uncertain"
        }))
    elif any(item["status"] == "fail" for item in endpoints.values()):
        status = "fail"
        reasons.append("non_inferiority_failed")
    else:
        status = "pass"
    return {
        "status": status,
        "cluster_unit": policy["cluster_unit"],
        "cluster_adjustment": policy["cluster_adjustment"],
        "multiplicity_adjustment": policy["multiplicity_adjustment"],
        "endpoints": endpoints,
    }, reasons


def _compare_dimension(candidate: object, comparator: object, direction: str) -> str:
    if candidate is None or comparator is None:
        return "uncertain"
    if direction == "not_worse":
        order = {state: index for index, state in enumerate(TERMINAL_STATE_ORDER)}
        order["completed"] = order["succeeded"]
        if candidate not in order or comparator not in order:
            return "uncertain"
        if order[candidate] > order[comparator]:
            return "candidate_better"
        if order[candidate] < order[comparator]:
            return "comparator_better"
        return "tie"
    candidate_number = _number(candidate, "candidate Pareto dimension")
    comparator_number = _number(comparator, "comparator Pareto dimension")
    if candidate_number == comparator_number:
        return "tie"
    if direction == "lower":
        return "candidate_better" if candidate_number < comparator_number else "comparator_better"
    if direction == "higher":
        return "candidate_better" if candidate_number > comparator_number else "comparator_better"
    return "uncertain"


def compare_pareto_vectors(candidate: dict, comparator: dict, pareto_policy: dict | None = None) -> dict:
    """Compare the frozen unweighted raw resource vectors."""
    policy = _validate_pareto_policy(pareto_policy or {
        "evaluation_order": 3,
        "dimensions": list(PARETO_DIMENSIONS),
        "directions": PARETO_DIRECTIONS,
        "weights_prohibited": True,
        "mixed_or_tied_result": "inconclusive",
    })
    candidate_vector = _require_mapping(candidate, "candidate Pareto vector")
    comparator_vector = _require_mapping(comparator, "comparator Pareto vector")
    dimension_results = {}
    for dimension in PARETO_DIMENSIONS:
        if dimension not in candidate_vector or dimension not in comparator_vector:
            dimension_results[dimension] = "uncertain"
        else:
            dimension_results[dimension] = _compare_dimension(
                candidate_vector[dimension],
                comparator_vector[dimension],
                policy["directions"][dimension],
            )
    values = set(dimension_results.values())
    if "uncertain" in values:
        result = "uncertain"
    elif "candidate_better" in values and "comparator_better" not in values:
        result = "candidate_dominates"
    elif "comparator_better" in values and "candidate_better" not in values:
        result = "comparator_dominates"
    elif values == {"tie"}:
        result = "tie"
    else:
        result = "mixed"
    return {
        "result": result,
        "dimensions": PARETO_DIMENSIONS,
        "directions": copy.deepcopy(policy["directions"]),
        "dimension_results": dimension_results,
        "weights_used": False,
    }


def _aggregate_vectors(rows: list[dict], workload_manifest: dict) -> dict:
    aggregate = {
        dimension: 0.0
        for dimension in PARETO_DIMENSIONS
        if dimension != "terminal_state"
    }
    rows_by_stratum: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        rows_by_stratum[row["workload_stratum_id"]].append(row)
    for stratum in workload_manifest["strata"]:
        stratum_rows = rows_by_stratum.get(stratum["stratum_id"], [])
        if not stratum_rows:
            raise ValueError("positive-weight workload stratum has no observations")
        for dimension in aggregate:
            aggregate[dimension] += stratum["target_weight"] * _mean([
                _number(
                    _require_mapping(row["resource_vector"], "resource vector").get(dimension),
                    f"resource {dimension}",
                )
                for row in stratum_rows
            ])
    terminal_order = {state: index for index, state in enumerate(TERMINAL_STATE_ORDER)}
    terminal_order["completed"] = terminal_order["succeeded"]
    worst_terminal = "completed"
    for row in rows:
        vector = _require_mapping(row["resource_vector"], "resource vector")
        terminal_state = vector.get("terminal_state", row.get("terminal_state"))
        if terminal_state not in terminal_order:
            worst_terminal = None
        elif worst_terminal is not None and terminal_order[terminal_state] < terminal_order[worst_terminal]:
            worst_terminal = terminal_state
    aggregate["terminal_state"] = worst_terminal
    return {
        dimension: (_round(value) if isinstance(value, (int, float)) else value)
        for dimension, value in aggregate.items()
    }


def _evaluate_pareto(plan: dict, pairs: list[dict]) -> dict:
    candidate_vector = _aggregate_vectors(
        [pair["candidate"] for pair in pairs],
        plan["workload_manifest"],
    )
    comparator_vector = _aggregate_vectors(
        [pair["comparator"] for pair in pairs],
        plan["workload_manifest"],
    )
    result = compare_pareto_vectors(candidate_vector, comparator_vector, plan["pareto_policy"])
    return {
        "status": "pass" if result["result"] == "candidate_dominates" else "inconclusive",
        "result": result["result"],
        "candidate_vector": candidate_vector,
        "comparator_vector": comparator_vector,
        "dimension_results": result["dimension_results"],
        "weights_used": False,
        "workload_weights_applied": True,
    }


def _frozen_plan_summary(plan: dict) -> dict:
    policy = plan["non_inferiority"]
    return {
        "analysis_plan_version": plan["analysis_plan_version"],
        "calibration_partition_binding": copy.deepcopy(plan["calibration_partition_binding"]),
        "calibration_evidence_bindings": copy.deepcopy(plan["calibration_evidence_bindings"]),
        "freeze_provenance": copy.deepcopy(plan["freeze_provenance"]),
        "workload_manifest": copy.deepcopy(plan["workload_manifest"]),
        "cache_policy": copy.deepcopy(plan["cache_policy"]),
        "campaign_budget": copy.deepcopy(plan["campaign_budget"]),
        "margins": copy.deepcopy(policy["margins"]),
        "confidence_level": _round(policy["confidence_level"]),
        "alpha": _round(policy["alpha"]),
        "power": _round(policy["power"]),
        "sample_sizes": copy.deepcopy(policy["sample_sizes"]),
        "sample_size_assumptions": copy.deepcopy(policy["sample_size_assumptions"]),
        "cluster_unit": policy["cluster_unit"],
        "cluster_adjustment": policy["cluster_adjustment"],
        "multiplicity_adjustment": policy["multiplicity_adjustment"],
    }


def _decision_payload(
    *,
    plan: dict,
    partition_binding: dict,
    decision: str,
    reason_codes: list[str],
    stop_gate: str | None,
    partition_boundary: dict | None = None,
    budget: dict | None = None,
    completeness: dict,
    workload_cache: dict,
    quality_floors: dict,
    non_inferiority: dict,
    pareto: dict,
    paired_outcomes: list[dict],
) -> dict:
    policy_output = {field: False for field in PROHIBITED_FINAL_OUTPUTS}
    details = {
        "schema_version": STATISTICS_SCHEMA_VERSION,
        "decision": decision,
        "reason_codes": reason_codes,
        "partition_binding": partition_binding,
        "partition_boundary": partition_boundary or {
            "status": "pass",
            "allowed_partition_type": "calibration",
            "qualification_eligible": False,
            "partition_binding": copy.deepcopy(partition_binding),
            "reason_codes": [],
        },
        "budget": budget or _not_evaluated("budget"),
        "ordered_results": _ordered_results(stop_gate),
        "completeness": completeness,
        "workload_cache": workload_cache,
        "quality_floors": quality_floors,
        "non_inferiority": non_inferiority,
        "pareto": pareto,
        "qualification_policy_output": policy_output,
        "frozen_plan": _frozen_plan_summary(plan),
    }
    assignment_bindings = sorted(
        {
            (row["assignment_binding"]["id"], row["assignment_binding"]["digest"])
            for row in paired_outcomes
            if isinstance(row, dict) and isinstance(row.get("assignment_binding"), dict)
        }
    )
    score_bundle_bindings = sorted(
        {
            (row["score_bundle_binding"]["id"], row["score_bundle_binding"]["digest"])
            for row in paired_outcomes
            if isinstance(row, dict) and isinstance(row.get("score_bundle_binding"), dict)
        }
    )
    pair_ids = sorted({
        row["pair_id"]
        for row in paired_outcomes
        if isinstance(row, dict) and isinstance(row.get("pair_id"), str)
    })
    comparison_digest = _content_digest({"pair_ids": pair_ids})
    complete = (
        completeness.get("status") == "pass"
        and workload_cache.get("status") == "pass"
    )
    floor_result = quality_floors.get("status", "not_evaluated")
    ni_result = non_inferiority.get("status", "not_evaluated")
    pareto_result = pareto.get("result", "not_evaluated")
    analysis_output = {
        "complete": complete,
        "floor_result": floor_result,
        "non_inferiority_result": ni_result,
        "pareto_result": pareto_result,
        "terminal_analysis_disposition": decision,
        "details": details,
    }
    analysis_output["analysis_output_digest"] = _content_digest(analysis_output)
    analysis_output["analysis_output_id"] = _content_digest({
        key: value
        for key, value in analysis_output.items()
        if key != "analysis_output_id"
    })

    gate_values = {
        "bindings": "pass",
        "partition": partition_boundary.get("status", "pass")
        if partition_boundary is not None
        else "pass",
        "treatment": "pass",
        "deterministic": "pass",
        "provenance": "pass",
        "completeness": completeness.get("status", "not_evaluated"),
        "floors": floor_result,
        "non_inferiority": ni_result,
        "pareto": (
            "pass"
            if pareto_result == "candidate_dominates"
            else "not_evaluated"
            if pareto_result == "not_evaluated"
            else "uncertain"
        ),
    }
    ordered_gate_results = [
        {"sequence": index, "gate": gate, "result": gate_values[gate]}
        for index, gate in enumerate(
            (
                "bindings",
                "partition",
                "treatment",
                "deterministic",
                "provenance",
                "completeness",
                "floors",
                "non_inferiority",
                "pareto",
            ),
            start=1,
        )
    ]
    result = {
        "schema_version": "analysis-decision.v1",
        "decision_bundle_version": plan["analysis_plan_version"],
        "partition_binding": copy.deepcopy(plan["calibration_partition_binding"]),
        "comparison_set_binding": {
            "id": comparison_digest,
            "digest": comparison_digest,
        },
        "assignment_bindings": [
            {"id": value_id, "digest": value_digest}
            for value_id, value_digest in assignment_bindings
        ],
        "score_bundle_bindings": [
            {"id": value_id, "digest": value_digest}
            for value_id, value_digest in score_bundle_bindings
        ],
        "analysis_plan_binding": {
            "id": plan["analysis_plan_id"],
            "digest": plan["analysis_plan_digest"],
        },
        "analysis_output": analysis_output,
        "ordered_gate_results": ordered_gate_results,
        "decision": decision,
        "qualification_policy_output": {
            key: False
            for key in (
                "preferred_route_policy_created",
                "fallback_route_policy_created",
                "installed_default_changed",
            )
        },
        "evidence_refs": sorted({
            item["digest"] for item in plan["calibration_evidence_bindings"]
        } | {
            value_digest for _value_id, value_digest in score_bundle_bindings
        }),
    }
    result["decision_bundle_digest"] = _content_digest(result)
    result["decision_bundle_id"] = _content_digest({
        key: value for key, value in result.items() if key != "decision_bundle_id"
    })
    return result


def _calibration_non_qualifying_decision() -> str:
    return "no_qualification"


def validate_analysis_decision_bundle(value: object) -> dict:
    """Validate the governed decision identity and all score/assignment bindings."""
    fields = frozenset({
        "schema_version",
        "decision_bundle_id",
        "decision_bundle_version",
        "decision_bundle_digest",
        "partition_binding",
        "comparison_set_binding",
        "assignment_bindings",
        "score_bundle_bindings",
        "analysis_plan_binding",
        "analysis_output",
        "ordered_gate_results",
        "decision",
        "qualification_policy_output",
        "evidence_refs",
    })
    bundle = _closed(copy.deepcopy(value), fields, "analysis decision bundle")
    _require(bundle, fields, "analysis decision bundle")
    if bundle["schema_version"] != "analysis-decision.v1":
        raise ValueError("analysis decision schema version is unsupported")
    bundle["partition_binding"] = _validate_partition(
        bundle["partition_binding"], require_calibration=True
    )
    for field in (
        "comparison_set_binding",
        "analysis_plan_binding",
    ):
        bundle[field] = _validate_binding(bundle[field], field.replace("_", " "))
    for field in ("assignment_bindings", "score_bundle_bindings"):
        rows = bundle[field]
        if not isinstance(rows, list) or len(rows) < 2:
            raise ValueError(f"{field} must contain both comparison arms")
        bundle[field] = [
            _validate_binding(item, field.replace("_", " ")) for item in rows
        ]
        if len({(item["id"], item["digest"]) for item in bundle[field]}) != len(
            bundle[field]
        ):
            raise ValueError(f"{field} must be unique")
    output = _require_mapping(bundle["analysis_output"], "analysis output")
    output_fields = frozenset({
        "analysis_output_id",
        "analysis_output_digest",
        "complete",
        "floor_result",
        "non_inferiority_result",
        "pareto_result",
        "terminal_analysis_disposition",
        "details",
    })
    output = _closed(output, output_fields, "analysis output")
    _require(output, output_fields, "analysis output")
    if type(output["complete"]) is not bool:
        raise ValueError("analysis output complete marker must be boolean")
    if not isinstance(output["details"], dict):
        raise ValueError("analysis output details must be an object")
    _digest(output["analysis_output_id"], "analysis output ID")
    _digest(output["analysis_output_digest"], "analysis output digest")
    expected_output_digest = _content_digest({
        key: item
        for key, item in output.items()
        if key not in {"analysis_output_id", "analysis_output_digest"}
    })
    if output["analysis_output_digest"] != expected_output_digest:
        raise ValueError("analysis output digest does not match content")
    if output["analysis_output_id"] != _content_digest({
        key: item for key, item in output.items() if key != "analysis_output_id"
    }):
        raise ValueError("analysis output ID does not match content")
    if output["terminal_analysis_disposition"] != bundle["decision"]:
        raise ValueError("analysis output disposition does not match decision")
    disposition_tuple = (
        output["complete"],
        output["floor_result"],
        output["non_inferiority_result"],
        output["pareto_result"],
        output["terminal_analysis_disposition"],
    )
    allowed_dispositions = {
        (True, "pass", "pass", "candidate_dominates", "calibration_complete"),
        (True, "fail", "not_evaluated", "not_evaluated", "no_qualification"),
        (True, "pass", "fail", "not_evaluated", "no_qualification"),
        (True, "pass", "pass", "comparator_dominates", "no_qualification"),
        (True, "pass", "uncertain", "not_evaluated", "inconclusive"),
        (True, "pass", "pass", "tie", "inconclusive"),
        (True, "pass", "pass", "mixed", "inconclusive"),
        (True, "pass", "pass", "uncertain", "inconclusive"),
        (
            False,
            "not_evaluated",
            "not_evaluated",
            "not_evaluated",
            "inconclusive",
        ),
        (
            False,
            "not_evaluated",
            "not_evaluated",
            "not_evaluated",
            "invalid",
        ),
    }
    if disposition_tuple not in allowed_dispositions:
        raise ValueError("analysis output metrics contradict its terminal disposition")
    bundle["analysis_output"] = output
    if bundle["decision"] not in CALIBRATION_DECISIONS:
        raise ValueError("analysis decision is outside the closed inventory")
    _text(bundle["decision_bundle_version"], "analysis decision bundle version")
    if not isinstance(bundle["ordered_gate_results"], list) or len(
        bundle["ordered_gate_results"]
    ) != 9:
        raise ValueError("analysis decision must contain nine ordered gate results")
    expected_gates = (
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
    for index, (gate, expected_gate) in enumerate(
        zip(bundle["ordered_gate_results"], expected_gates), start=1
    ):
        if gate != {
            "sequence": index,
            "gate": expected_gate,
            "result": gate.get("result") if isinstance(gate, dict) else None,
        } or gate["result"] not in {"pass", "fail", "uncertain", "not_evaluated"}:
            raise ValueError("analysis decision gates are not in frozen order")
    policy_output = bundle["qualification_policy_output"]
    expected_policy_output = {
        "preferred_route_policy_created": False,
        "fallback_route_policy_created": False,
        "installed_default_changed": False,
    }
    if policy_output != expected_policy_output:
        raise ValueError("analysis decision cannot create qualification policy")
    if not isinstance(bundle["evidence_refs"], list):
        raise ValueError("analysis decision evidence references must be an array")
    bundle["evidence_refs"] = [
        _digest(item, "analysis decision evidence reference")
        for item in bundle["evidence_refs"]
    ]
    if len(bundle["evidence_refs"]) != len(set(bundle["evidence_refs"])):
        raise ValueError("analysis decision evidence references must be unique")
    _digest(bundle["decision_bundle_id"], "analysis decision bundle ID")
    _digest(bundle["decision_bundle_digest"], "analysis decision bundle digest")
    if bundle["decision_bundle_digest"] != _content_digest({
        key: item
        for key, item in bundle.items()
        if key not in {"decision_bundle_id", "decision_bundle_digest"}
    }):
        raise ValueError("analysis decision bundle digest does not match content")
    if bundle["decision_bundle_id"] != _content_digest({
        key: item for key, item in bundle.items() if key != "decision_bundle_id"
    }):
        raise ValueError("analysis decision bundle ID does not match content")
    return bundle


def evaluate_qualification_decision(
    *,
    analysis_plan: dict,
    paired_outcomes: list[dict],
    partition: dict,
) -> dict:
    """Replay the frozen quality-first statistical decision sequence."""
    plan = _validate_plan(analysis_plan)
    partition_binding = _validate_partition(partition)
    partition_boundary, partition_reasons = _evaluate_partition_boundary(partition_binding)
    if partition_binding != plan["calibration_partition_binding"]:
        partition_reasons.append("partition_binding_mismatch")
        partition_boundary["status"] = "fail"
        partition_boundary["reason_codes"] = list(partition_reasons)
    if partition_reasons:
        return validate_analysis_decision_bundle(_decision_payload(
            plan=plan,
            partition_binding=partition_binding,
            decision="invalid",
            reason_codes=partition_reasons,
            stop_gate="partition",
            partition_boundary=partition_boundary,
            budget=_not_evaluated("budget"),
            completeness=_not_evaluated("completeness"),
            workload_cache=_not_evaluated("workload_cache"),
            quality_floors=_not_evaluated("quality_floors"),
            non_inferiority=_not_evaluated("non_inferiority"),
            pareto=_not_evaluated("pareto"),
            paired_outcomes=paired_outcomes,
        ))
    budget, budget_reasons = _evaluate_campaign_budget(plan, paired_outcomes)
    if budget_reasons:
        return validate_analysis_decision_bundle(_decision_payload(
            plan=plan,
            partition_binding=partition_binding,
            decision="invalid",
            reason_codes=budget_reasons,
            stop_gate="budget",
            partition_boundary=partition_boundary,
            budget=budget,
            completeness=_not_evaluated("completeness"),
            workload_cache=_not_evaluated("workload_cache"),
            quality_floors=_not_evaluated("quality_floors"),
            non_inferiority=_not_evaluated("non_inferiority"),
            pareto=_not_evaluated("pareto"),
            paired_outcomes=paired_outcomes,
        ))
    pairs, pairing_reasons, completeness = _pair_outcomes(paired_outcomes, plan)
    if pairing_reasons:
        return validate_analysis_decision_bundle(_decision_payload(
            plan=plan,
            partition_binding=partition_binding,
            decision="inconclusive",
            reason_codes=pairing_reasons,
            stop_gate="pairing",
            partition_boundary=partition_boundary,
            budget=budget,
            completeness=completeness,
            workload_cache=_not_evaluated("workload_cache"),
            quality_floors=_not_evaluated("quality_floors"),
            non_inferiority=_not_evaluated("non_inferiority"),
            pareto=_not_evaluated("pareto"),
            paired_outcomes=paired_outcomes,
        ))
    workload_cache, workload_reasons = _evaluate_workload_cache(plan, pairs)
    if workload_reasons:
        return validate_analysis_decision_bundle(_decision_payload(
            plan=plan,
            partition_binding=partition_binding,
            decision="inconclusive",
            reason_codes=workload_reasons,
            stop_gate="workload_cache",
            partition_boundary=partition_boundary,
            budget=budget,
            completeness=completeness,
            workload_cache=workload_cache,
            quality_floors=_not_evaluated("quality_floors"),
            non_inferiority=_not_evaluated("non_inferiority"),
            pareto=_not_evaluated("pareto"),
            paired_outcomes=paired_outcomes,
        ))
    quality_floors, floor_reasons = _evaluate_quality_floors(plan, pairs)
    if floor_reasons:
        return validate_analysis_decision_bundle(_decision_payload(
            plan=plan,
            partition_binding=partition_binding,
            decision=_calibration_non_qualifying_decision(),
            reason_codes=floor_reasons,
            stop_gate="quality_floors",
            partition_boundary=partition_boundary,
            budget=budget,
            completeness=completeness,
            workload_cache=workload_cache,
            quality_floors=quality_floors,
            non_inferiority=_not_evaluated("non_inferiority"),
            pareto=_not_evaluated("pareto"),
            paired_outcomes=paired_outcomes,
        ))
    non_inferiority, ni_reasons = _evaluate_non_inferiority(plan, pairs)
    if non_inferiority["status"] != "pass":
        return validate_analysis_decision_bundle(_decision_payload(
            plan=plan,
            partition_binding=partition_binding,
            decision=(
                "no_qualification"
                if non_inferiority["status"] == "fail"
                else "inconclusive"
            ),
            reason_codes=ni_reasons,
            stop_gate="non_inferiority",
            partition_boundary=partition_boundary,
            budget=budget,
            completeness=completeness,
            workload_cache=workload_cache,
            quality_floors=quality_floors,
            non_inferiority=non_inferiority,
            pareto=_not_evaluated("pareto"),
            paired_outcomes=paired_outcomes,
        ))
    pareto = _evaluate_pareto(plan, pairs)
    pareto_reasons = [] if pareto["result"] == "candidate_dominates" else [f"pareto_{pareto['result']}"]
    if pareto["result"] == "candidate_dominates":
        decision = "calibration_complete"
    elif pareto["result"] == "comparator_dominates":
        decision = "no_qualification"
    else:
        decision = "inconclusive"
    return validate_analysis_decision_bundle(_decision_payload(
        plan=plan,
        partition_binding=partition_binding,
        decision=decision,
        reason_codes=pareto_reasons,
        stop_gate=None,
        partition_boundary=partition_boundary,
        budget=budget,
        completeness=completeness,
        workload_cache=workload_cache,
        quality_floors=quality_floors,
        non_inferiority=non_inferiority,
        pareto=pareto,
        paired_outcomes=paired_outcomes,
    ))


__all__ = [
    "ATTRITION_CLASSIFICATIONS",
    "CALIBRATION_DECISIONS",
    "CANDIDATE_TERMINAL_STATES",
    "CAMPAIGN_BUDGET_FIELDS",
    "DECISION_SEQUENCE",
    "PARETO_DIMENSIONS",
    "PARETO_DIRECTIONS",
    "PARETO_RESULTS",
    "PROHIBITED_FINAL_OUTPUTS",
    "RERUN_DECISIONS",
    "STATISTICS_SCHEMA_VERSION",
    "TERMINAL_STATE_ORDER",
    "compare_pareto_vectors",
    "evaluate_qualification_decision",
    "validate_analysis_decision_bundle",
]
