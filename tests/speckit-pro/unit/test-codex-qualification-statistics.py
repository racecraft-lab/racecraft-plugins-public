#!/usr/bin/env python3
"""Focused deterministic tests for G56R-003 qualification statistics."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/lib/qualification_statistics.py"
REPLAY_MODULE_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/lib/qualification_replay.py"
SCORING_TEST_PATH = ROOT / "tests/speckit-pro/unit/test-codex-qualification-scoring.py"
CONTRACT_TEST_PATH = ROOT / "tests/speckit-pro/unit/test-codex-qualification-contracts.py"
QUALIFICATION_RUNNER_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/run-codex-qualification.py"
ANALYSIS_PLAN_SCHEMA_PATH = (
    ROOT / "tests/speckit-pro/layer6-efficiency/contracts/analysis-plan.schema.json"
)
ANALYSIS_DECISION_SCHEMA_PATH = (
    ROOT / "tests/speckit-pro/layer6-efficiency/contracts/analysis-decision.schema.json"
)
RUN_CODEX_ROLE_EVAL_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/run_codex_role_eval.py"
SHIPPED_MATERIALIZER_PATH = ROOT / "speckit-pro/speckit_pro_runner/agent_materialization.py"

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
EXPECTED_PUBLIC_API = frozenset({
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
})
EXPECTED_REPLAY_PUBLIC_API = frozenset({
    "ANALYSIS_REPLAY_SCHEMA_VERSION",
    "REPLAY_BUNDLE_SCHEMA_VERSION",
    "SCORE_REPLAY_SUMMARY_SCHEMA_VERSION",
    "build_analysis_replay_bundle",
    "build_score_replay_bundle",
    "replay_analysis_decision",
    "replay_score_bundle",
    "summarize_score_replays",
    "validate_analysis_replay_bundle",
    "validate_score_replay_bundle",
})
CANDIDATE_TERMINAL_STATES = (
    "failed",
    "timed_out",
    "cancelled",
    "budget_exhausted",
    "abandoned",
)
CANDIDATE_TERMINAL_FAILURE_CODES = {
    "failed": "candidate_failed",
    "timed_out": "candidate_timed_out",
    "cancelled": "candidate_cancelled",
    "budget_exhausted": "candidate_budget_exhausted",
    "abandoned": "candidate_abandoned",
}


def load_statistics_module():
    if not MODULE_PATH.exists():
        return types.SimpleNamespace(
            __all__=(),
            CALIBRATION_DECISIONS=(),
            CAMPAIGN_BUDGET_FIELDS=(),
            DECISION_SEQUENCE=(),
            PARETO_DIMENSIONS=(),
            PARETO_DIRECTIONS={},
            PARETO_RESULTS=(),
            PROHIBITED_FINAL_OUTPUTS=(),
            STATISTICS_SCHEMA_VERSION="missing",
            TERMINAL_STATE_ORDER=(),
            compare_pareto_vectors=lambda *_args, **_kwargs: {"result": "missing"},
            evaluate_qualification_decision=lambda *_args, **_kwargs: {
                "schema_version": "missing",
                "decision": "missing",
                "ordered_results": [],
                "quality_floors": {"status": "missing"},
                "non_inferiority": {"status": "missing"},
                "pareto": {"result": "missing"},
                "qualification_policy_output": {},
                "reason_codes": ["missing_implementation"],
            },
        )
    module_name = f"_g56r_003_qualification_statistics_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_contract_test_helpers():
    module_name = f"_g56r_003_contract_test_helpers_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, CONTRACT_TEST_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {CONTRACT_TEST_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_replay_module():
    module_name = f"_g56r_003_qualification_replay_statistics_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, REPLAY_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {REPLAY_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_scoring_test_helpers():
    module_name = f"_g56r_003_scoring_helpers_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, SCORING_TEST_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCORING_TEST_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"


def canonical_bytes(value: object) -> bytes:
    return canonical_json(value).rstrip("\n").encode("utf-8")


def digest(value: object) -> str:
    if isinstance(value, str):
        payload = value.encode("utf-8")
    else:
        payload = canonical_bytes(value)
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def content_id(value: dict, identity_field: str) -> str:
    return digest({key: item for key, item in value.items() if key != identity_field})


def seal_analysis_plan(plan: dict) -> dict:
    sealed = copy.deepcopy(plan)
    sealed["analysis_plan_digest"] = digest({
        key: value
        for key, value in sealed.items()
        if key not in {"analysis_plan_id", "analysis_plan_digest"}
    })
    sealed["analysis_plan_id"] = content_id(sealed, "analysis_plan_id")
    return sealed


def write_canonical_json(path: Path, value: object) -> None:
    path.write_text(canonical_json(value), encoding="utf-8")


def run_qualification_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(QUALIFICATION_RUNNER_PATH), *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=env,
        shell=False,
        check=False,
    )


def binding(label: str) -> dict:
    return {"id": label, "digest": digest(label)}


def object_binding(object_id: str, object_digest: str) -> dict:
    return {"id": object_id, "digest": object_digest}


def cache_policy_binding() -> dict:
    return {"id": "cache-isolation-v1", "digest": digest("cache-policy")}


def scorer_bindings() -> list[dict]:
    return [
        {
            "id": scorer_id,
            "digest": digest({"scorer": scorer_id, "version": "1.0.0"}),
        }
        for scorer_id in ("opaque-scorer-a", "opaque-scorer-b")
    ]


def partition_binding(partition_type: str = "calibration", *, eligible: bool = False) -> dict:
    return {
        "partition_id": f"{partition_type}-partition",
        "partition_type": partition_type,
        "partition_digest": digest(f"{partition_type}-partition"),
        "qualification_eligible": eligible,
    }


def workload_manifest_fixture() -> dict:
    return {
        "manifest_id": "workload-manifest-v1",
        "manifest_digest": digest("workload-manifest"),
        "minimum_unique_tasks": 3,
        "unknown_stratum_policy": "inconclusive",
        "strata": [
            {
                "stratum_id": "implementation-small",
                "target_weight": 0.75,
                "long_horizon": False,
                "p95_guardrails": {
                    "raw_input_tokens_max": 150,
                    "cached_input_tokens_max": 30,
                    "output_tokens_max": 80,
                    "duration_ms_max": 1500,
                },
            },
            {
                "stratum_id": "analysis-long",
                "target_weight": 0.25,
                "long_horizon": True,
                "p95_guardrails": {
                    "raw_input_tokens_max": 300,
                    "cached_input_tokens_max": 60,
                    "output_tokens_max": 160,
                    "duration_ms_max": 3000,
                },
            },
        ],
    }


def cache_policy_fixture() -> dict:
    return {
        "policy_id": "cache-isolation-v1",
        "policy_digest": digest("cache-policy"),
        "pair_isolation": True,
        "order_leakage_prohibited": True,
        "cache_state": "isolated_by_pair",
    }


def campaign_budget_fixture() -> dict:
    return {
        "max_attempts": 64,
        "max_wall_clock_seconds": 7200,
        "max_raw_input_tokens": 5000,
        "max_cached_input_tokens": 1000,
        "max_output_tokens": 3000,
        "max_candidates": 4,
        "max_confirmation_entries": 0,
    }


def analysis_plan_fixture(cluster_unit: str = "role", per_cluster_minimum: int = 1) -> dict:
    return seal_analysis_plan({
        "schema_version": "analysis-plan.v1",
        "analysis_plan_id": digest("analysis-plan"),
        "analysis_plan_version": "2026-07-24.calibration",
        "analysis_plan_digest": digest("analysis-plan-digest"),
        "status": "frozen",
        "calibration_protocol_binding": binding("calibration-protocol"),
        "calibration_partition_binding": partition_binding("calibration", eligible=False),
        "calibration_evidence_bindings": [binding("calibration-evidence")],
        "freeze_provenance": {
            "frozen_at": "2026-07-24T16:00:00Z",
            "frozen_after_calibration": True,
            "cohort_outcome_observed": False,
            "pre_cohort_outcome_absence_digest": digest("pre-cohort-absence"),
            "independent_review_binding": binding("analysis-review"),
        },
        "workload_manifest": workload_manifest_fixture(),
        "cache_policy": cache_policy_fixture(),
        "quality_floors": {
            "evaluation_order": 1,
            "semantic": {"metric": "semantic_score", "minimum": 0.85},
            "reliability": {"metric": "reliability_score", "minimum": 0.95},
        },
        "non_inferiority": {
            "evaluation_order": 2,
            "endpoints": ["semantic_score", "reliability_score"],
            "margins": {"semantic_score": -0.02, "reliability_score": -0.01},
            "confidence_level": 0.95,
            "alpha": 0.05,
            "power": 0.8,
            "sample_sizes": {"per_role_minimum": per_cluster_minimum},
            "sample_size_assumptions": {
                "variance_source_binding": binding("calibration-variance"),
                "expected_missingness_rate": 0.05,
            },
            "cluster_unit": cluster_unit,
            "cluster_adjustment": "cluster_robust",
            "multiplicity_adjustment": "holm",
        },
        "pareto_policy": {
            "evaluation_order": 3,
            "dimensions": list(PARETO_DIMENSIONS),
            "directions": {
                "raw_input_tokens": "lower",
                "cached_input_tokens": "lower",
                "output_tokens": "lower",
                "duration_ms": "lower",
                "retries": "lower",
                "compactions": "lower",
                "acceptance": "higher",
                "terminal_state": "not_worse",
            },
            "weights_prohibited": True,
            "mixed_or_tied_result": "inconclusive",
        },
        "estimand_policy": {
            "assigned_attempt": True,
            "candidate_terminal_acceptance_zero": True,
            "candidate_terminal_states": [
                "failed",
                "timed_out",
                "cancelled",
                "budget_exhausted",
                "abandoned",
            ],
            "complete_case_filtering": False,
        },
        "attrition_policy": {
            "cap": 0.1,
            "unclassifiable_attrition": "evidence_boundary_failure",
            "unclassifiable_result": "inconclusive",
            "complete_case_filtering": False,
        },
        "rerun_policy": {
            "eligible_failure": "independently_preclassified_transient_harness_failure",
            "scope": "complete_pair",
            "cap": 1,
            "one_arm_rerun_prohibited": True,
        },
        "campaign_budget": campaign_budget_fixture(),
        "racing_policy": {"enabled": False, "terminal_rule": "disabled"},
        "futility_policy": {"enabled": False, "terminal_rule": "disabled"},
        "terminal_policy": {
            "incomplete_result": "inconclusive",
            "uncertain_result": "inconclusive",
            "no_forced_ranking": True,
        },
    })


def resource_vector(
    raw_input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
    duration_ms: int,
    *,
    retries: int = 0,
    compactions: int = 0,
    acceptance: int = 1,
    terminal_state: str = "completed",
) -> dict:
    return {
        "raw_input_tokens": raw_input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "output_tokens": output_tokens,
        "duration_ms": duration_ms,
        "retries": retries,
        "compactions": compactions,
        "acceptance": acceptance,
        "terminal_state": terminal_state,
    }


def outcome(
    pair_id: str,
    arm: str,
    *,
    attempt_index: int = 1,
    role_id: str = "implement-executor",
    fixture_id: str = "fixture-a",
    semantic_score: float,
    reliability_score: float,
    vector: dict,
    workload_stratum_id: str = "implementation-small",
    outcome_cache_policy_binding: dict | None = None,
    cache_state: str = "isolated_by_pair",
    treatment_order_leakage: bool = False,
    terminal_state: str = "completed",
    score_disposition: str = "accepted",
    failure_plane: str = "none",
    failure_code: str = "none",
    attrition_classification: str = "complete",
    wall_clock_seconds: int = 0,
    candidate_route_id: str = "candidate-route",
    confirmation_entries: int = 0,
) -> dict:
    return {
        "pair_id": pair_id,
        "attempt_index": attempt_index,
        "arm": arm,
        "role_id": role_id,
        "fixture_id": fixture_id,
        "task_id": f"task-{pair_id}",
        "score_disposition": score_disposition,
        "failure_plane": failure_plane,
        "failure_code": failure_code,
        "attrition_classification": attrition_classification,
        "terminal_state": terminal_state,
        "semantic_score": semantic_score,
        "reliability_score": reliability_score,
        "resource_vector": copy.deepcopy(vector),
        "workload_stratum_id": workload_stratum_id,
        "cache_policy_binding": copy.deepcopy(outcome_cache_policy_binding or cache_policy_binding()),
        "cache_state": cache_state,
        "treatment_order_leakage": treatment_order_leakage,
        "wall_clock_seconds": wall_clock_seconds,
        "candidate_route_id": candidate_route_id,
        "confirmation_entries": confirmation_entries,
        "assignment_binding": binding(f"assignment-{pair_id}-{arm}"),
        "score_bundle_binding": binding(f"score-{pair_id}-{arm}"),
    }


def paired_outcomes(
    *,
    cluster_unit: str = "role",
    cluster_count: int = 3,
    pairs_per_cluster: int = 2,
    candidate_semantic: float = 0.9,
    comparator_semantic: float = 0.87,
    candidate_reliability: float = 0.98,
    comparator_reliability: float = 0.96,
) -> list[dict]:
    rows: list[dict] = []
    for cluster_index in range(cluster_count):
        role_id = f"role-{cluster_index}" if cluster_unit == "role" else "shared-role"
        fixture_id = f"fixture-{cluster_index}" if cluster_unit == "fixture" else "shared-fixture"
        for pair_index in range(pairs_per_cluster):
            pair_id = f"pair-{cluster_index}-{pair_index}"
            workload_stratum_id = (
                "analysis-long"
                if cluster_index == 0 and pair_index == 0
                else "implementation-small"
            )
            rows.extend([
                outcome(
                    pair_id,
                    "candidate",
                    role_id=role_id,
                    fixture_id=fixture_id,
                    semantic_score=candidate_semantic,
                    reliability_score=candidate_reliability,
                    vector=resource_vector(80, 10, 40, 900),
                    workload_stratum_id=workload_stratum_id,
                ),
                outcome(
                    pair_id,
                    "comparator",
                    role_id=role_id,
                    fixture_id=fixture_id,
                    semantic_score=comparator_semantic,
                    reliability_score=comparator_reliability,
                    vector=resource_vector(100, 15, 50, 1100),
                    workload_stratum_id=workload_stratum_id,
                ),
            ])
    return rows


def analysis_replay_request() -> dict:
    plan = analysis_plan_fixture(per_cluster_minimum=1)
    outcomes = paired_outcomes(cluster_count=3, pairs_per_cluster=1)
    authorities = {
        "analysis_plan_binding": object_binding(
            plan["analysis_plan_id"],
            plan["analysis_plan_digest"],
        ),
        "partition_binding": copy.deepcopy(plan["calibration_partition_binding"]),
        "pinned_client_binding": binding("codex-0.145.0"),
        "runtime_snapshot_binding": binding("runtime-snapshot"),
        "candidate_freeze_binding": binding("candidate-freeze"),
        "scorer_bindings": scorer_bindings(),
        "rubric_binding": {
            "id": "g56r-003-semantic-rubric",
            "digest": digest({"rubric": "g56r-003", "version": "1.0.0"}),
        },
        "adjudicator_binding": binding("opaque-adjudicator-c"),
        "workload_manifest_binding": {
            "id": plan["workload_manifest"]["manifest_id"],
            "digest": plan["workload_manifest"]["manifest_digest"],
        },
        "cache_policy_binding": cache_policy_binding(),
    }
    score_bundles = score_bundles_for_outcomes(outcomes, plan, authorities)
    request = {
        "schema_version": "analysis-replay-request.v1",
        "analysis_plan": plan,
        "partition": partition_binding(),
        "paired_outcomes": outcomes,
        "score_bundles": score_bundles,
        "binding_authorities": authorities,
        "execution_boundary": {
            "network_access": False,
            "live_repository_writes": [],
            "operator_only_raw_evidence_root": "operator-retention://g56r-003/calibration",
        },
    }
    request["source_lineage"] = source_lineage_fixture(request)
    return request


def score_bundles_for_outcomes(
    outcomes: list[dict],
    plan: dict,
    authorities: dict,
) -> list[dict]:
    helpers = load_scoring_test_helpers()
    scoring = helpers.load_scoring_module()
    bundles = []
    for index, row in enumerate(outcomes):
        gate_request = helpers.gate_request(role_id=f"{row['role_id']}-{index}")
        gate_request.update({
            "fixture_id": row["fixture_id"],
            "fixture_digest": digest({"fixture_id": row["fixture_id"]}),
        })
        gate_result = scoring.evaluate_hard_gates(gate_request)
        ballots = [
            helpers.scorer_ballot(
                "opaque-scorer-a",
                semantic=row["semantic_score"],
                reliability=row["reliability_score"],
            ),
            helpers.scorer_ballot(
                "opaque-scorer-b",
                semantic=row["semantic_score"],
                reliability=row["reliability_score"],
            ),
        ]
        semantic_result = scoring.evaluate_blinded_ballots(
            gate_result,
            helpers.semantic_request(ballots=ballots),
        )
        vector = row["resource_vector"]
        request = helpers.score_bundle_request(
            gate_result,
            semantic_result=semantic_result,
            vector={
                "input_tokens": vector["raw_input_tokens"],
                "cached_input_tokens": vector["cached_input_tokens"],
                "output_tokens": vector["output_tokens"],
                "duration_ms": vector["duration_ms"],
                "retries": vector["retries"],
                "compactions": vector["compactions"],
                "acceptance": vector["acceptance"],
                "terminal_state": vector["terminal_state"],
            },
        )
        request["assignment_binding"] = copy.deepcopy(row["assignment_binding"])
        request["partition_binding"] = {
            "id": plan["calibration_partition_binding"]["partition_id"],
            "digest": plan["calibration_partition_binding"]["partition_digest"],
        }
        request["candidate_route_binding"]["id"] = row["candidate_route_id"]
        request["runtime_snapshot_binding"] = copy.deepcopy(
            authorities["runtime_snapshot_binding"]
        )
        request["candidate_freeze_binding"] = copy.deepcopy(
            authorities["candidate_freeze_binding"]
        )
        bundle = scoring.build_score_bundle(request)
        row["score_bundle_binding"] = {
            "id": bundle["score_bundle_id"],
            "digest": bundle["score_bundle_digest"],
        }
        bundles.append(bundle)
    return bundles


def source_lineage_fixture(request: dict) -> dict:
    plan = request["analysis_plan"]
    authorities = request["binding_authorities"]
    source_ledger = binding("sanitized-source-ledger")
    materialization = binding("canonical-materialization")
    treatment_trace = binding("immutable-treatment-trace")
    corpus = binding("governed-twelve-role-corpus")
    score_bundle_bindings = sorted(
        (
            {
                "id": item["score_bundle_id"],
                "digest": item["score_bundle_digest"],
            }
            for item in request["score_bundles"]
        ),
        key=lambda item: (item["id"], item["digest"]),
    )
    analysis_plan = object_binding(
        plan["analysis_plan_id"],
        plan["analysis_plan_digest"],
    )
    successor_freeze = {
        "source_ledger_binding": copy.deepcopy(source_ledger),
        "candidate_freeze_binding": copy.deepcopy(authorities["candidate_freeze_binding"]),
        "runtime_snapshot_binding": copy.deepcopy(authorities["runtime_snapshot_binding"]),
    }
    return {
        "schema_version": "source-ledger-lineage.v1",
        "source_ledger_binding": source_ledger,
        "successor_freeze": successor_freeze,
        "materialization": {
            "materialization_binding": copy.deepcopy(materialization),
            "candidate_freeze_binding": copy.deepcopy(successor_freeze["candidate_freeze_binding"]),
        },
        "treatment_trace": {
            "execution_trace_binding": copy.deepcopy(treatment_trace),
            "materialization_binding": copy.deepcopy(materialization),
            "candidate_freeze_binding": copy.deepcopy(successor_freeze["candidate_freeze_binding"]),
        },
        "corpus": {
            "corpus_binding": copy.deepcopy(corpus),
            "partition_binding": copy.deepcopy(request["partition"]),
        },
        "score_bundle": {
            "score_bundle_bindings": score_bundle_bindings,
            "paired_outcomes_digest": digest(request["paired_outcomes"]),
            "execution_trace_binding": copy.deepcopy(treatment_trace),
            "corpus_binding": copy.deepcopy(corpus),
            "candidate_freeze_binding": copy.deepcopy(successor_freeze["candidate_freeze_binding"]),
            "runtime_snapshot_binding": copy.deepcopy(successor_freeze["runtime_snapshot_binding"]),
            "analysis_plan_binding": copy.deepcopy(analysis_plan),
        },
        "analysis_plan_binding": analysis_plan,
    }


def full_sanitized_cross_slice_replay_request() -> dict:
    request = analysis_replay_request()
    request["source_lineage"] = source_lineage_fixture(request)
    return request


def equal_resource_outcomes(**kwargs: object) -> list[dict]:
    rows = paired_outcomes(cluster_count=3, pairs_per_cluster=1, **kwargs)
    for row in rows:
        row["resource_vector"] = resource_vector(100, 10, 40, 1000)
    return rows


def ordered_results(stop_gate: str | None = None) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    stopped = False
    for gate in (
        "partition",
        "budget",
        "pairing",
        "workload_cache",
        "quality_floors",
        "non_inferiority",
        "pareto",
    ):
        if stopped:
            result = "not_evaluated"
        elif gate == stop_gate:
            result = "fail"
            stopped = True
        else:
            result = "pass"
        rows.append((gate, result))
    return rows


def seal_calibration_report(report: dict) -> dict:
    sealed = copy.deepcopy(report)
    sealed["calibration_report_digest"] = digest({
        key: value
        for key, value in sealed.items()
        if key not in {"calibration_report_id", "calibration_report_digest"}
    })
    sealed["calibration_report_id"] = content_id(
        sealed,
        "calibration_report_id",
    )
    return sealed


def calibration_report_fixture(*, completed: bool = True) -> dict:
    plan = analysis_plan_fixture()
    outcomes = paired_outcomes(
        candidate_semantic=0.9 if completed else 0.84,
    )
    decision = load_statistics_module().evaluate_qualification_decision(
        analysis_plan=plan,
        paired_outcomes=outcomes,
        partition=partition_binding(),
    )
    return seal_calibration_report({
        "schema_version": "calibration-report.v1",
        "calibration_protocol_binding": copy.deepcopy(
            plan["calibration_protocol_binding"]
        ),
        "calibration_partition_binding": partition_binding(),
        "calibration_evidence_bindings": copy.deepcopy(plan["calibration_evidence_bindings"]),
        "freeze_provenance": copy.deepcopy(plan["freeze_provenance"]),
        "analysis_decision": decision,
    })


class QualificationStatisticsTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.stats = load_statistics_module()
        self.contracts = load_contract_test_helpers()
        self.decision_schema = json.loads(
            ANALYSIS_DECISION_SCHEMA_PATH.read_text(encoding="utf-8")
        )

    def evaluate(self, plan: dict, outcomes: list[dict], *, partition: dict | None = None) -> dict:
        decision = self.stats.evaluate_qualification_decision(
            analysis_plan=copy.deepcopy(plan),
            paired_outcomes=copy.deepcopy(outcomes),
            partition=copy.deepcopy(partition or partition_binding()),
        )
        self.contracts.validate_contract_schema_instance(
            decision,
            self.decision_schema,
            self.decision_schema,
        )
        return decision["analysis_output"]["details"]

    def assert_calibration_decision(self, result: dict, expected: str) -> None:
        self.assertEqual(result["decision"], expected)
        self.assertIn(result["decision"], set(self.stats.CALIBRATION_DECISIONS))
        self.assertNotIn(result["decision"], {"qualified"})
        self.assertEqual(result["qualification_policy_output"], {
            "preferred_route_policy_created": False,
            "fallback_route_policy_created": False,
            "installed_default_changed": False,
            "aggregate_identity_created": False,
            "release_claim_created": False,
        })
        for prohibited in self.stats.PROHIBITED_FINAL_OUTPUTS:
            self.assertFalse(result["qualification_policy_output"][prohibited])

    def test_public_api_and_frozen_plan_terms_are_explicit(self) -> None:
        self.assertEqual(frozenset(self.stats.__all__), EXPECTED_PUBLIC_API)
        self.assertEqual(tuple(self.stats.CAMPAIGN_BUDGET_FIELDS), (
            "max_attempts",
            "max_wall_clock_seconds",
            "max_raw_input_tokens",
            "max_cached_input_tokens",
            "max_output_tokens",
            "max_candidates",
            "max_confirmation_entries",
        ))
        self.assertEqual(tuple(self.stats.CALIBRATION_DECISIONS), (
            "calibration_complete",
            "no_qualification",
            "inconclusive",
            "invalid",
        ))
        self.assertEqual(tuple(self.stats.PROHIBITED_FINAL_OUTPUTS), (
            "preferred_route_policy_created",
            "fallback_route_policy_created",
            "installed_default_changed",
            "aggregate_identity_created",
            "release_claim_created",
        ))
        self.assertEqual(tuple(self.stats.CANDIDATE_TERMINAL_STATES), CANDIDATE_TERMINAL_STATES)
        self.assertEqual(tuple(self.stats.ATTRITION_CLASSIFICATIONS), (
            "complete",
            "candidate_terminal",
            "transient_harness_failure",
            "unclassifiable_attrition",
        ))
        self.assertEqual(tuple(self.stats.RERUN_DECISIONS), (
            "not_needed",
            "complete_pair_rerun",
            "one_arm_rerun_prohibited",
            "rerun_cap_exhausted",
        ))
        self.assertEqual(tuple(self.stats.DECISION_SEQUENCE), (
            "partition",
            "budget",
            "pairing",
            "workload_cache",
            "quality_floors",
            "non_inferiority",
            "pareto",
        ))
        self.assertEqual(tuple(self.stats.PARETO_DIMENSIONS), PARETO_DIMENSIONS)
        self.assertNotIn("WEIGHTS", set(dir(self.stats)))

        plan = analysis_plan_fixture(per_cluster_minimum=2)
        result = self.evaluate(plan, paired_outcomes(pairs_per_cluster=2))

        self.assert_calibration_decision(result, "calibration_complete")
        self.assertEqual(result["frozen_plan"]["margins"], plan["non_inferiority"]["margins"])
        self.assertEqual(result["frozen_plan"]["alpha"], plan["non_inferiority"]["alpha"])
        self.assertEqual(result["frozen_plan"]["power"], plan["non_inferiority"]["power"])
        self.assertEqual(result["frozen_plan"]["sample_sizes"], plan["non_inferiority"]["sample_sizes"])
        self.assertEqual(
            result["frozen_plan"]["sample_size_assumptions"],
            plan["non_inferiority"]["sample_size_assumptions"],
        )
        self.assertEqual(
            result["frozen_plan"]["multiplicity_adjustment"],
            plan["non_inferiority"]["multiplicity_adjustment"],
        )
        self.assertEqual(result["frozen_plan"]["workload_manifest"], plan["workload_manifest"])
        self.assertEqual(result["frozen_plan"]["cache_policy"], plan["cache_policy"])
        self.assertEqual(result["frozen_plan"]["campaign_budget"], plan["campaign_budget"])
        self.assertEqual(result["frozen_plan"]["analysis_plan_version"], plan["analysis_plan_version"])
        self.assertEqual(
            result["frozen_plan"]["calibration_protocol_binding"],
            plan["calibration_protocol_binding"],
        )
        self.assertEqual(result["frozen_plan"]["calibration_evidence_bindings"], plan["calibration_evidence_bindings"])
        self.assertEqual(result["frozen_plan"]["freeze_provenance"], plan["freeze_provenance"])
        self.assertEqual(result["workload_cache"]["status"], "pass")
        self.assertTrue(result["workload_cache"]["strata"]["analysis-long"]["long_horizon"])

        missing_alpha = copy.deepcopy(plan)
        del missing_alpha["non_inferiority"]["alpha"]
        with self.assertRaises(ValueError):
            self.evaluate(missing_alpha, paired_outcomes())

        weighted = copy.deepcopy(plan)
        weighted["pareto_policy"]["weights"] = {"duration_ms": 1}
        with self.assertRaises(ValueError):
            self.evaluate(weighted, paired_outcomes())

    def test_analysis_plan_freeze_metadata_is_required_before_statistics(self) -> None:
        cases = [
            ("analysis_plan_version", ("analysis_plan_version",)),
            ("calibration_protocol_binding", ("calibration_protocol_binding",)),
            ("calibration_evidence_bindings", ("calibration_evidence_bindings",)),
            ("freeze_provenance", ("freeze_provenance",)),
            ("independent_review_binding", ("freeze_provenance", "independent_review_binding")),
            ("pre_cohort_outcome_absence_digest", ("freeze_provenance", "pre_cohort_outcome_absence_digest")),
        ]
        for label, path in cases:
            with self.subTest(missing=label):
                plan = analysis_plan_fixture()
                target = plan
                for key in path[:-1]:
                    target = target[key]
                del target[path[-1]]

                with self.assertRaises(ValueError):
                    self.evaluate(plan, paired_outcomes())

    def test_frozen_plan_identity_and_partition_authority_reject_drift(self) -> None:
        stale_identity = analysis_plan_fixture()
        stale_identity["quality_floors"]["semantic"]["minimum"] = 0.86
        with self.assertRaisesRegex(ValueError, "analysis plan digest does not match"):
            self.evaluate(stale_identity, paired_outcomes())

        alternate_partition = partition_binding()
        alternate_partition["partition_id"] = "alternate-calibration-partition"
        alternate_partition["partition_digest"] = digest("alternate-calibration-partition")
        result = self.evaluate(
            analysis_plan_fixture(),
            paired_outcomes(),
            partition=alternate_partition,
        )

        self.assertEqual(result["decision"], "invalid")
        self.assertIn("partition_binding_mismatch", result["reason_codes"])
        self.assertEqual(result["partition_boundary"]["status"], "fail")

        post_cohort = analysis_plan_fixture()
        post_cohort["freeze_provenance"]["cohort_outcome_observed"] = True
        with self.assertRaises(ValueError):
            self.evaluate(post_cohort, paired_outcomes())

    def test_analysis_plan_schema_keeps_numeric_freeze_and_budget_complete(self) -> None:
        schema = json.loads(ANALYSIS_PLAN_SCHEMA_PATH.read_text(encoding="utf-8"))

        self.assertIn("calibration_protocol_binding", schema["required"])
        self.assertIn("freeze_provenance", schema["required"])
        self.assertIn("independent_review_binding", schema["$defs"]["freezeProvenance"]["required"])
        self.assertIn(
            "pre_cohort_outcome_absence_digest",
            schema["$defs"]["freezeProvenance"]["required"],
        )
        self.assertEqual(
            schema["$defs"]["budget"]["required"],
            list(self.stats.CAMPAIGN_BUDGET_FIELDS),
        )

        for path in (
            ("non_inferiority", "alpha"),
            ("non_inferiority", "power"),
            ("non_inferiority", "sample_sizes"),
            ("campaign_budget", "max_confirmation_entries"),
        ):
            with self.subTest(missing_numeric=path):
                plan = analysis_plan_fixture()
                target = plan
                for key in path[:-1]:
                    target = target[key]
                del target[path[-1]]

                with self.assertRaises(ValueError):
                    self.evaluate(plan, paired_outcomes())

    def test_prohibited_boundaries_reject_post_hoc_thresholds_mutation_fields_and_open_failure_codes(self) -> None:
        plan = analysis_plan_fixture()
        plan["post_hoc_thresholds"] = {"semantic_score": 0.99}
        with self.assertRaises(ValueError):
            self.evaluate(plan, paired_outcomes())

        trace_mutation = paired_outcomes()
        trace_mutation[0]["execution_trace_mutation"] = {
            "execution_trace_id": digest("trace"),
            "after_scoring": True,
        }
        with self.assertRaises(ValueError):
            self.evaluate(analysis_plan_fixture(), trace_mutation)

        unrestricted_failure_code = paired_outcomes()
        unrestricted_failure_code[0].update({
            "score_disposition": "non_scorable",
            "failure_plane": "candidate",
            "failure_code": "operator_invented_failure",
        })
        with self.assertRaises(ValueError):
            self.evaluate(analysis_plan_fixture(), unrestricted_failure_code)

        unknown_attrition = paired_outcomes()
        unknown_attrition[0].update({
            "score_disposition": "non_scorable",
            "failure_plane": "evidence_boundary",
            "failure_code": "unclassifiable_attrition",
            "attrition_classification": "operator_unknown",
        })
        with self.assertRaises(ValueError):
            self.evaluate(analysis_plan_fixture(), unknown_attrition)

    def test_no_duplicate_materializer_or_legacy_role_eval_route_exists(self) -> None:
        candidates = sorted(
            path.relative_to(ROOT).as_posix()
            for base in (
                ROOT / "speckit-pro",
                ROOT / "tests/speckit-pro/layer6-efficiency",
            )
            for path in base.rglob("*materializ*.py")
        )

        self.assertFalse(RUN_CODEX_ROLE_EVAL_PATH.exists())
        self.assertEqual(candidates, [SHIPPED_MATERIALIZER_PATH.relative_to(ROOT).as_posix()])

    def test_campaign_budget_requires_every_dimension_and_fails_closed_when_exceeded(self) -> None:
        for field in self.stats.CAMPAIGN_BUDGET_FIELDS:
            with self.subTest(missing=field):
                plan = analysis_plan_fixture()
                del plan["campaign_budget"][field]
                with self.assertRaises(ValueError):
                    self.evaluate(plan, paired_outcomes())

        cases = [
            ("max_attempts", 1, None, "budget_max_attempts_exceeded"),
            ("max_wall_clock_seconds", 1, ("wall_clock_seconds", 2), "budget_max_wall_clock_seconds_exceeded"),
            ("max_raw_input_tokens", 1, None, "budget_max_raw_input_tokens_exceeded"),
            ("max_cached_input_tokens", 1, None, "budget_max_cached_input_tokens_exceeded"),
            ("max_output_tokens", 1, None, "budget_max_output_tokens_exceeded"),
            ("max_candidates", 1, None, "budget_max_candidates_exceeded"),
            ("max_confirmation_entries", 0, ("confirmation_entries", 1), "budget_max_confirmation_entries_exceeded"),
        ]
        for field, ceiling, row_override, reason in cases:
            with self.subTest(exceeded=field):
                plan = analysis_plan_fixture()
                outcomes = paired_outcomes(cluster_count=2, pairs_per_cluster=1)
                plan["campaign_budget"][field] = ceiling
                plan = seal_analysis_plan(plan)
                if row_override is not None:
                    key, value = row_override
                    outcomes[0][key] = value
                if field == "max_candidates":
                    outcomes[2]["candidate_route_id"] = "second-candidate"

                result = self.evaluate(plan, outcomes)

                self.assert_calibration_decision(result, "invalid")
                self.assertEqual(result["budget"]["status"], "fail")
                self.assertIn(reason, result["reason_codes"])
                self.assertEqual(
                    [(row["gate"], row["result"]) for row in result["ordered_results"]],
                    ordered_results("budget"),
                )

    def test_calibration_rejects_later_partitions_and_eligible_calibration(self) -> None:
        cases = [
            partition_binding("calibration", eligible=True),
            partition_binding("screening", eligible=True),
            partition_binding("selection", eligible=True),
            partition_binding("cohort_lock", eligible=True),
            partition_binding("integrated_confirmation", eligible=True),
        ]
        for partition in cases:
            with self.subTest(partition=partition["partition_type"], eligible=partition["qualification_eligible"]):
                result = self.evaluate(analysis_plan_fixture(), paired_outcomes(), partition=partition)

                self.assert_calibration_decision(result, "invalid")
                self.assertIn("partition_not_calibration_only", result["reason_codes"])
                self.assertEqual(result["partition_boundary"]["status"], "fail")
                self.assertEqual(
                    [(row["gate"], row["result"]) for row in result["ordered_results"]],
                    ordered_results("partition"),
                )

    def test_calibration_terminal_cases_emit_the_governed_closed_decisions(self) -> None:
        plan = analysis_plan_fixture(per_cluster_minimum=1)
        tie = equal_resource_outcomes()
        mixed = paired_outcomes()
        for row in mixed:
            if row["arm"] == "candidate":
                row["resource_vector"]["duration_ms"] = 1300
        comparator_dominates = equal_resource_outcomes()
        for row in comparator_dominates:
            if row["arm"] == "candidate":
                row["resource_vector"]["raw_input_tokens"] = 120
        incomplete = paired_outcomes()
        incomplete.pop()
        floor_failed = paired_outcomes()
        for row in floor_failed:
            if row["arm"] == "candidate":
                row["semantic_score"] = 0.84
        non_inferiority_failed = paired_outcomes(candidate_semantic=0.85, comparator_semantic=0.95)
        uncertain = paired_outcomes(pairs_per_cluster=1)
        uncertain_plan = analysis_plan_fixture(per_cluster_minimum=3)
        cases = [
            ("dominates", plan, paired_outcomes(), "calibration_complete", None),
            ("floor_failed", plan, floor_failed, "no_qualification", "semantic_floor_failed"),
            ("non_inferiority_failed", plan, non_inferiority_failed, "no_qualification", "non_inferiority_failed"),
            ("comparator_dominates", plan, comparator_dominates, "no_qualification", "pareto_comparator_dominates"),
            ("tie", plan, tie, "inconclusive", "pareto_tie"),
            ("mixed", plan, mixed, "inconclusive", "pareto_mixed"),
            ("incomplete", plan, incomplete, "inconclusive", "unpaired_comparison"),
            ("uncertain", uncertain_plan, uncertain, "inconclusive", "sample_size_insufficient"),
        ]
        for label, case_plan, outcomes, expected, reason in cases:
            with self.subTest(case=label):
                result = self.evaluate(case_plan, outcomes)

                self.assert_calibration_decision(result, expected)
                if reason is not None:
                    self.assertIn(reason, result["reason_codes"])

    def test_candidate_caused_terminals_stay_assigned_with_acceptance_zero(self) -> None:
        for terminal_state, failure_code in CANDIDATE_TERMINAL_FAILURE_CODES.items():
            with self.subTest(terminal_state=terminal_state):
                outcomes = equal_resource_outcomes()
                terminal = outcomes[0]
                terminal.update({
                    "terminal_state": terminal_state,
                    "failure_plane": "candidate",
                    "failure_code": failure_code,
                    "attrition_classification": "candidate_terminal",
                })
                terminal["resource_vector"]["terminal_state"] = "completed"
                terminal["resource_vector"]["acceptance"] = 1

                result = self.evaluate(analysis_plan_fixture(), outcomes)

                self.assertEqual(result["completeness"]["status"], "pass")
                self.assertFalse(result["completeness"]["complete_case_filtering"])
                self.assertEqual(result["completeness"]["assigned_pair_count"], 3)
                self.assertEqual(result["completeness"]["retained_pair_count"], 3)
                self.assertEqual(
                    result["completeness"]["candidate_terminal_counts"][terminal_state],
                    1,
                )
                self.assertEqual(result["pareto"]["candidate_vector"]["acceptance"], 0.75)
                self.assertEqual(
                    result["pareto"]["candidate_vector"]["terminal_state"],
                    terminal_state,
                )
                self.assertEqual(result["pareto"]["result"], "comparator_dominates")
                self.assert_calibration_decision(result, "no_qualification")
                self.assertNotIn("complete_case_filtered", result["reason_codes"])

    def test_unclassifiable_attrition_blocks_completeness_without_complete_case_filtering(self) -> None:
        outcomes = equal_resource_outcomes()
        outcomes[0].update({
            "score_disposition": "non_scorable",
            "failure_plane": "evidence_boundary",
            "failure_code": "unclassifiable_attrition",
            "attrition_classification": "unclassifiable_attrition",
        })

        result = self.evaluate(analysis_plan_fixture(), outcomes)

        self.assertEqual(result["decision"], "inconclusive")
        self.assertIn("unclassifiable_attrition", result["reason_codes"])
        self.assertEqual(result["completeness"]["status"], "fail")
        self.assertEqual(result["completeness"]["assigned_pair_count"], 3)
        self.assertEqual(result["completeness"]["retained_pair_count"], 0)
        self.assertEqual(result["completeness"]["incomplete_pair_ids"], ["pair-0-0"])
        self.assertEqual(
            result["completeness"]["attrition"]["classifications"]["unclassifiable_attrition"],
            1,
        )
        self.assertFalse(result["completeness"]["complete_case_filtering"])
        self.assertEqual(result["quality_floors"]["status"], "not_evaluated")

    def test_transient_harness_failures_use_capped_complete_pair_reruns(self) -> None:
        plan = analysis_plan_fixture(per_cluster_minimum=1)
        plan["attrition_policy"]["cap"] = 0.5
        plan = seal_analysis_plan(plan)
        outcomes = [
            outcome(
                "pair-rerun",
                "candidate",
                attempt_index=1,
                semantic_score=0.9,
                reliability_score=0.98,
                vector=resource_vector(100, 10, 40, 1000),
                score_disposition="non_scorable",
                failure_plane="infrastructure",
                failure_code="transient_harness_failure",
                attrition_classification="independently_preclassified_transient_harness_failure",
            ),
            outcome(
                "pair-rerun",
                "comparator",
                attempt_index=1,
                semantic_score=0.87,
                reliability_score=0.96,
                vector=resource_vector(100, 10, 40, 1000),
            ),
            outcome(
                "pair-rerun",
                "candidate",
                attempt_index=2,
                semantic_score=0.9,
                reliability_score=0.98,
                vector=resource_vector(80, 8, 35, 900),
                workload_stratum_id="analysis-long",
            ),
            outcome(
                "pair-rerun",
                "comparator",
                attempt_index=2,
                semantic_score=0.87,
                reliability_score=0.96,
                vector=resource_vector(100, 10, 40, 1000),
                workload_stratum_id="analysis-long",
            ),
        ]
        for index in range(2):
            pair_id = f"pair-control-{index}"
            outcomes.extend([
                outcome(
                    pair_id,
                    "candidate",
                    role_id=f"role-control-{index}",
                    semantic_score=0.9,
                    reliability_score=0.98,
                    vector=resource_vector(80, 8, 35, 900),
                ),
                outcome(
                    pair_id,
                    "comparator",
                    role_id=f"role-control-{index}",
                    semantic_score=0.87,
                    reliability_score=0.96,
                    vector=resource_vector(100, 10, 40, 1000),
                ),
            ])

        result = self.evaluate(plan, outcomes)

        self.assert_calibration_decision(result, "calibration_complete")
        self.assertEqual(result["completeness"]["status"], "pass")
        self.assertEqual(result["completeness"]["assigned_pair_count"], 3)
        self.assertEqual(result["completeness"]["retained_pair_count"], 3)
        self.assertEqual(result["completeness"]["reruns"]["complete_pair_reruns"], 1)
        self.assertEqual(result["completeness"]["reruns"]["decisions"], {
            "pair-rerun": "complete_pair_rerun",
        })
        self.assertEqual(
            result["completeness"]["attrition"]["classifications"]["transient_harness_failure"],
            1,
        )
        self.assertEqual(result["completeness"]["attrition"]["status"], "within_cap")

    def test_attrition_and_rerun_caps_fail_closed_without_one_arm_or_complete_case_rescue(self) -> None:
        plan = analysis_plan_fixture()
        one_arm = [
            outcome(
                "pair-one-arm",
                "candidate",
                attempt_index=1,
                semantic_score=0.9,
                reliability_score=0.98,
                vector=resource_vector(100, 10, 40, 1000),
                score_disposition="non_scorable",
                failure_plane="infrastructure",
                failure_code="transient_harness_failure",
                attrition_classification="independently_preclassified_transient_harness_failure",
            ),
            outcome(
                "pair-one-arm",
                "comparator",
                attempt_index=1,
                semantic_score=0.87,
                reliability_score=0.96,
                vector=resource_vector(100, 10, 40, 1000),
            ),
            outcome(
                "pair-one-arm",
                "candidate",
                attempt_index=2,
                semantic_score=0.9,
                reliability_score=0.98,
                vector=resource_vector(80, 8, 35, 900),
            ),
        ]

        one_arm_result = self.evaluate(plan, one_arm)

        self.assertEqual(one_arm_result["decision"], "inconclusive")
        self.assertIn("one_arm_rerun_prohibited", one_arm_result["reason_codes"])
        self.assertEqual(
            one_arm_result["completeness"]["reruns"]["decisions"]["pair-one-arm"],
            "one_arm_rerun_prohibited",
        )
        self.assertEqual(one_arm_result["completeness"]["retained_pair_count"], 0)
        self.assertFalse(one_arm_result["completeness"]["complete_case_filtering"])

        after_cap = copy.deepcopy(plan)
        after_cap["attrition_policy"]["cap"] = 1.0
        after_cap = seal_analysis_plan(after_cap)
        incomplete_after_cap = [
            outcome(
                "pair-after-cap",
                "candidate",
                attempt_index=1,
                semantic_score=0.9,
                reliability_score=0.98,
                vector=resource_vector(100, 10, 40, 1000),
                score_disposition="non_scorable",
                failure_plane="infrastructure",
                failure_code="transient_harness_failure",
                attrition_classification="independently_preclassified_transient_harness_failure",
            ),
            outcome(
                "pair-after-cap",
                "comparator",
                attempt_index=1,
                semantic_score=0.87,
                reliability_score=0.96,
                vector=resource_vector(100, 10, 40, 1000),
            ),
            outcome(
                "pair-after-cap",
                "candidate",
                attempt_index=2,
                semantic_score=0.9,
                reliability_score=0.98,
                vector=resource_vector(100, 10, 40, 1000),
                score_disposition="non_scorable",
                failure_plane="infrastructure",
                failure_code="transient_harness_failure",
                attrition_classification="independently_preclassified_transient_harness_failure",
            ),
            outcome(
                "pair-after-cap",
                "comparator",
                attempt_index=2,
                semantic_score=0.87,
                reliability_score=0.96,
                vector=resource_vector(100, 10, 40, 1000),
            ),
        ]

        after_cap_result = self.evaluate(after_cap, incomplete_after_cap)

        self.assertEqual(after_cap_result["decision"], "inconclusive")
        self.assertIn("incomplete_after_rerun_cap", after_cap_result["reason_codes"])
        self.assertEqual(
            after_cap_result["completeness"]["reruns"]["decisions"]["pair-after-cap"],
            "rerun_cap_exhausted",
        )

        attrition_cap = analysis_plan_fixture()
        attrition_cap["attrition_policy"]["cap"] = 0.0
        attrition_cap = seal_analysis_plan(attrition_cap)
        resolved = copy.deepcopy(incomplete_after_cap[:2])
        resolved.extend([
            outcome(
                "pair-after-cap",
                "candidate",
                attempt_index=2,
                semantic_score=0.9,
                reliability_score=0.98,
                vector=resource_vector(80, 8, 35, 900),
            ),
            outcome(
                "pair-after-cap",
                "comparator",
                attempt_index=2,
                semantic_score=0.87,
                reliability_score=0.96,
                vector=resource_vector(100, 10, 40, 1000),
            ),
        ])

        attrition_cap_result = self.evaluate(attrition_cap, resolved)

        self.assertEqual(attrition_cap_result["decision"], "inconclusive")
        self.assertIn("attrition_cap_exceeded", attrition_cap_result["reason_codes"])
        self.assertEqual(attrition_cap_result["completeness"]["attrition"]["status"], "exceeds_cap")

    def test_workload_manifest_closes_strata_weights_and_long_horizon_policy(self) -> None:
        plan = analysis_plan_fixture()
        result = self.evaluate(plan, paired_outcomes())

        self.assertEqual(result["workload_cache"]["status"], "pass")
        self.assertEqual(result["workload_cache"]["minimum_unique_tasks"], 3)
        self.assertEqual(result["workload_cache"]["unique_task_count"], 6)
        self.assertEqual(
            result["workload_cache"]["strata"]["implementation-small"]["target_weight"],
            0.75,
        )
        self.assertFalse(result["workload_cache"]["strata"]["implementation-small"]["long_horizon"])
        self.assertTrue(result["workload_cache"]["strata"]["analysis-long"]["long_horizon"])

        cases = [
            ("weight_sum", ("strata", 1, "target_weight"), 0.5),
            ("unknown_policy", ("unknown_stratum_policy",), "assign_to_other"),
            ("long_horizon", ("strata", 0, "long_horizon"), "false"),
        ]
        for label, path, value in cases:
            with self.subTest(case=label):
                invalid = copy.deepcopy(plan)
                target = invalid["workload_manifest"]
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                with self.assertRaises(ValueError):
                    self.evaluate(invalid, paired_outcomes())

        duplicate = copy.deepcopy(plan)
        duplicate["workload_manifest"]["strata"][1]["stratum_id"] = "implementation-small"
        with self.assertRaises(ValueError):
            self.evaluate(duplicate, paired_outcomes())

    def test_workload_cache_gate_fails_closed_for_minimum_tasks_and_unknown_strata(self) -> None:
        plan = analysis_plan_fixture()
        too_few_tasks = copy.deepcopy(plan)
        too_few_tasks["workload_manifest"]["minimum_unique_tasks"] = 7
        too_few_tasks = seal_analysis_plan(too_few_tasks)

        minimum_result = self.evaluate(too_few_tasks, paired_outcomes())

        self.assertEqual(minimum_result["decision"], "inconclusive")
        self.assertIn("minimum_unique_tasks_not_met", minimum_result["reason_codes"])
        self.assertEqual(
            [(row["gate"], row["result"]) for row in minimum_result["ordered_results"]],
            ordered_results("workload_cache"),
        )

        unknown = paired_outcomes()
        unknown[0]["workload_stratum_id"] = "operator-invented"

        unknown_result = self.evaluate(plan, unknown)

        self.assertEqual(unknown_result["decision"], "inconclusive")
        self.assertIn("unknown_workload_stratum", unknown_result["reason_codes"])
        self.assertEqual(unknown_result["workload_cache"]["unknown_stratum_policy"], "inconclusive")

        missing_weighted_stratum = [
            row
            for row in paired_outcomes()
            if row["workload_stratum_id"] != "analysis-long"
        ]
        missing_result = self.evaluate(plan, missing_weighted_stratum)
        self.assertEqual(missing_result["decision"], "inconclusive")
        self.assertIn("weighted_stratum_missing_candidate", missing_result["reason_codes"])
        self.assertIn("weighted_stratum_missing_comparator", missing_result["reason_codes"])

    def test_pareto_aggregation_applies_frozen_workload_weights(self) -> None:
        outcomes = paired_outcomes()
        for row in outcomes:
            if row["workload_stratum_id"] == "implementation-small":
                row["resource_vector"]["raw_input_tokens"] = (
                    10 if row["arm"] == "candidate" else 20
                )
            else:
                row["resource_vector"]["raw_input_tokens"] = (
                    100 if row["arm"] == "candidate" else 50
                )

        result = self.evaluate(analysis_plan_fixture(), outcomes)

        self.assertTrue(result["pareto"]["workload_weights_applied"])
        self.assertEqual(result["pareto"]["candidate_vector"]["raw_input_tokens"], 32.5)
        self.assertEqual(result["pareto"]["comparator_vector"]["raw_input_tokens"], 27.5)

    def test_p95_guardrails_block_average_only_token_and_duration_claims(self) -> None:
        cases = [
            ("raw_input_tokens", 400, "raw_input_tokens_max"),
            ("cached_input_tokens", 100, "cached_input_tokens_max"),
            ("output_tokens", 200, "output_tokens_max"),
            ("duration_ms", 3500, "duration_ms_max"),
        ]
        for dimension, tail_value, guardrail_key in cases:
            with self.subTest(dimension=dimension):
                outcomes = paired_outcomes(pairs_per_cluster=2)
                outcomes[2]["resource_vector"][dimension] = tail_value

                result = self.evaluate(analysis_plan_fixture(), outcomes)

                self.assertEqual(result["decision"], "inconclusive")
                self.assertIn(f"p95_{dimension}_guardrail_exceeded", result["reason_codes"])
                dimension_stats = (
                    result["workload_cache"]["strata"]["implementation-small"]["candidate"]
                    ["dimensions"][dimension]
                )
                guardrail = workload_manifest_fixture()["strata"][0]["p95_guardrails"][guardrail_key]
                self.assertLess(dimension_stats["mean"], guardrail)
                self.assertGreater(dimension_stats["p95"], guardrail)

    def test_cache_policy_and_treatment_order_leakage_are_immutable_bindings(self) -> None:
        plan = analysis_plan_fixture()
        cache_leak_policy = copy.deepcopy(plan)
        cache_leak_policy["cache_policy"]["pair_isolation"] = False
        with self.assertRaises(ValueError):
            self.evaluate(cache_leak_policy, paired_outcomes())

        cases = [
            ("cache_policy_binding_mismatch", ("cache_policy_binding", "digest"), digest("post-treatment-cache")),
            ("cache_state_not_isolated", ("cache_state",), "shared_by_thread"),
            ("treatment_order_leakage", ("treatment_order_leakage",), True),
        ]
        for expected_reason, path, value in cases:
            with self.subTest(reason=expected_reason):
                outcomes = paired_outcomes()
                target = outcomes[0]
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value

                result = self.evaluate(plan, outcomes)

                self.assertEqual(result["decision"], "inconclusive")
                self.assertIn(expected_reason, result["reason_codes"])
                self.assertEqual(result["workload_cache"]["cache_policy_binding"], cache_policy_binding())

    def test_semantic_and_reliability_floors_short_circuit_before_statistics(self) -> None:
        cases = [
            ("semantic_score", 0.84, "semantic_floor_failed"),
            ("reliability_score", 0.94, "reliability_floor_failed"),
        ]
        for metric, value, reason in cases:
            with self.subTest(metric=metric):
                outcomes = paired_outcomes()
                for row in outcomes:
                    if row["arm"] == "candidate":
                        row[metric] = value

                result = self.evaluate(analysis_plan_fixture(), outcomes)

                self.assert_calibration_decision(result, "no_qualification")
                self.assertIn(reason, result["reason_codes"])
                self.assertEqual(
                    [(row["gate"], row["result"]) for row in result["ordered_results"]],
                    ordered_results("quality_floors"),
                )
                self.assertEqual(result["non_inferiority"]["status"], "not_evaluated")
                self.assertEqual(result["pareto"]["result"], "not_evaluated")

    def test_non_inferiority_uses_paired_cluster_adjusted_confidence_bounds(self) -> None:
        for cluster_unit in ("role", "fixture"):
            with self.subTest(cluster_unit=cluster_unit):
                plan = analysis_plan_fixture(cluster_unit=cluster_unit, per_cluster_minimum=2)
                result = self.evaluate(plan, paired_outcomes(cluster_unit=cluster_unit, pairs_per_cluster=2))

                self.assertEqual(result["non_inferiority"]["status"], "pass")
                self.assert_calibration_decision(result, "calibration_complete")
                endpoint = result["non_inferiority"]["endpoints"]["semantic_score"]
                self.assertEqual(endpoint["cluster_unit"], cluster_unit)
                self.assertEqual(endpoint["cluster_count"], 3)
                self.assertEqual(endpoint["pair_count"], 6)
                self.assertEqual(endpoint["mean_difference"], 0.03)
                self.assertEqual(endpoint["lower_confidence_bound"], 0.03)
                self.assertGreaterEqual(endpoint["lower_confidence_bound"], endpoint["margin"])
                self.assertEqual(endpoint["degrees_of_freedom"], 2)
                self.assertEqual(
                    endpoint["adjusted_confidence_level"],
                    1.0 - endpoint["adjusted_alpha"],
                )

    def test_holm_uses_ordered_step_down_thresholds_and_confidence_matches_alpha(self) -> None:
        invalid = analysis_plan_fixture()
        invalid["non_inferiority"]["alpha"] = 0.2
        invalid = seal_analysis_plan(invalid)
        with self.assertRaisesRegex(ValueError, "one minus alpha"):
            self.evaluate(invalid, paired_outcomes())

        plan = analysis_plan_fixture()
        p_values = {"semantic_score": 0.01, "reliability_score": 0.04}
        original = self.stats._cluster_endpoint

        def fake_endpoint(endpoint, _pairs, _policy, adjusted_alpha):
            return {
                "status": "pass" if p_values[endpoint] <= adjusted_alpha else "fail",
                "p_value": p_values[endpoint],
                "adjusted_alpha": adjusted_alpha,
            }

        try:
            self.stats._cluster_endpoint = fake_endpoint
            holm, _reasons = self.stats._evaluate_non_inferiority(plan, [])
            bonferroni_plan = copy.deepcopy(plan)
            bonferroni_plan["non_inferiority"][
                "multiplicity_adjustment"
            ] = "bonferroni"
            bonferroni, _reasons = self.stats._evaluate_non_inferiority(
                bonferroni_plan,
                [],
            )
        finally:
            self.stats._cluster_endpoint = original

        self.assertEqual(holm["endpoints"]["semantic_score"]["adjusted_alpha"], 0.025)
        self.assertEqual(holm["endpoints"]["reliability_score"]["adjusted_alpha"], 0.05)
        self.assertEqual(holm["status"], "pass")
        self.assertEqual(bonferroni["status"], "fail")

    def test_cluster_adjustment_and_pairing_fail_closed_without_complete_pairs(self) -> None:
        plan = analysis_plan_fixture(cluster_unit="role", per_cluster_minimum=1)
        outcomes = []
        for index in range(5):
            workload_stratum_id = "analysis-long" if index == 0 else "implementation-small"
            outcomes.extend([
                outcome(
                    f"role-a-{index}",
                    "candidate",
                    role_id="role-a",
                    semantic_score=0.9,
                    reliability_score=0.97,
                    vector=resource_vector(80, 10, 40, 900),
                    workload_stratum_id=workload_stratum_id,
                ),
                outcome(
                    f"role-a-{index}",
                    "comparator",
                    role_id="role-a",
                    semantic_score=0.85,
                    reliability_score=0.95,
                    vector=resource_vector(100, 15, 50, 1100),
                    workload_stratum_id=workload_stratum_id,
                ),
            ])
        outcomes.extend([
            outcome(
                "role-b-0",
                "candidate",
                role_id="role-b",
                semantic_score=0.85,
                reliability_score=0.95,
                vector=resource_vector(80, 10, 40, 900),
            ),
            outcome(
                "role-b-0",
                "comparator",
                role_id="role-b",
                semantic_score=0.95,
                reliability_score=0.97,
                vector=resource_vector(100, 15, 50, 1100),
            ),
        ])

        result = self.evaluate(plan, outcomes)

        self.assert_calibration_decision(result, "no_qualification")
        self.assertEqual(result["non_inferiority"]["status"], "fail")
        semantic = result["non_inferiority"]["endpoints"]["semantic_score"]
        self.assertEqual(semantic["cluster_count"], 2)
        self.assertLess(semantic["lower_confidence_bound"], semantic["margin"])

        unpaired = copy.deepcopy(paired_outcomes())
        unpaired.pop()
        unpaired_result = self.evaluate(plan, unpaired)
        self.assertEqual(unpaired_result["decision"], "inconclusive")
        self.assertIn("unpaired_comparison", unpaired_result["reason_codes"])
        self.assertEqual(
            [(row["gate"], row["result"]) for row in unpaired_result["ordered_results"]],
            ordered_results("pairing"),
        )

    def test_non_inferiority_uncertainty_short_circuits_pareto_dominance(self) -> None:
        plan = analysis_plan_fixture(per_cluster_minimum=3)
        result = self.evaluate(plan, paired_outcomes(pairs_per_cluster=1))

        self.assertEqual(result["decision"], "inconclusive")
        self.assertIn("sample_size_insufficient", result["reason_codes"])
        self.assertEqual(result["non_inferiority"]["status"], "uncertain")
        self.assertEqual(result["pareto"]["result"], "not_evaluated")

    def test_non_inferiority_requires_two_independent_clusters(self) -> None:
        result = self.evaluate(
            analysis_plan_fixture(per_cluster_minimum=1),
            paired_outcomes(cluster_count=1, pairs_per_cluster=3),
        )

        self.assertEqual(result["decision"], "inconclusive")
        self.assertIn("independent_cluster_count_insufficient", result["reason_codes"])
        endpoint = result["non_inferiority"]["endpoints"]["semantic_score"]
        self.assertEqual(endpoint["status"], "uncertain")
        self.assertEqual(endpoint["cluster_count"], 1)
        self.assertIsNone(endpoint["lower_confidence_bound"])

    def test_raw_vector_pareto_cases_use_no_weights_or_forced_ranking(self) -> None:
        cases = [
            (
                "candidate_dominates",
                resource_vector(80, 8, 35, 900, retries=0, compactions=0, acceptance=1),
                resource_vector(100, 9, 40, 1000, retries=1, compactions=1, acceptance=1),
            ),
            (
                "comparator_dominates",
                resource_vector(120, 12, 50, 1100, retries=1, compactions=1, acceptance=1),
                resource_vector(100, 9, 40, 1000, retries=0, compactions=0, acceptance=1),
            ),
            (
                "tie",
                resource_vector(100, 9, 40, 1000, retries=0, compactions=0, acceptance=1),
                resource_vector(100, 9, 40, 1000, retries=0, compactions=0, acceptance=1),
            ),
            (
                "mixed",
                resource_vector(80, 8, 35, 1200, retries=0, compactions=0, acceptance=1),
                resource_vector(100, 9, 40, 1000, retries=0, compactions=0, acceptance=1),
            ),
            (
                "uncertain",
                {key: value for key, value in resource_vector(80, 8, 35, 900).items() if key != "duration_ms"},
                resource_vector(100, 9, 40, 1000),
            ),
        ]

        for expected, candidate, comparator in cases:
            with self.subTest(expected=expected):
                result = self.stats.compare_pareto_vectors(
                    candidate,
                    comparator,
                    analysis_plan_fixture()["pareto_policy"],
                )

                self.assertEqual(result["result"], expected)
                self.assertFalse(result["weights_used"])
                self.assertEqual(tuple(result["dimensions"]), PARETO_DIMENSIONS)


class DeterministicQualificationReplayTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.replay = load_replay_module()

    def test_analysis_replay_api_is_explicit_and_deterministic(self) -> None:
        self.assertEqual(frozenset(self.replay.__all__), EXPECTED_REPLAY_PUBLIC_API)

        bundle = self.replay.build_analysis_replay_bundle(analysis_replay_request())
        first = self.replay.validate_analysis_replay_bundle(copy.deepcopy(bundle))
        second = self.replay.replay_analysis_decision(copy.deepcopy(first))

        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], self.replay.ANALYSIS_REPLAY_SCHEMA_VERSION)
        self.assertEqual(first["status"], "replayed")
        self.assertEqual(first["decision"]["decision"], "calibration_complete")
        self.assertEqual(first["decision_binding"], {
            "id": first["decision"]["decision_bundle_id"],
            "digest": first["decision"]["decision_bundle_digest"],
        })
        self.assertEqual(
            first["analysis_replay_artifact_digest"],
            digest({
                key: value
                for key, value in first.items()
                if key not in {"analysis_replay_artifact_id", "analysis_replay_artifact_digest"}
            }),
        )
        self.assertEqual(
            first["analysis_replay_artifact_id"],
            content_id(first, "analysis_replay_artifact_id"),
        )
        self.assertFalse(first["execution_boundary"]["network_access"])
        self.assertEqual(first["execution_boundary"]["live_repository_writes"], [])
        self.assertEqual(
            first["binding_authorities"]["scorer_bindings"],
            scorer_bindings(),
        )
        self.assertEqual(
            first["binding_authorities"]["workload_manifest_binding"],
            {
                "id": first["analysis_plan"]["workload_manifest"]["manifest_id"],
                "digest": first["analysis_plan"]["workload_manifest"]["manifest_digest"],
            },
        )
        self.assertEqual(first["binding_authorities"]["cache_policy_binding"], cache_policy_binding())

    def test_full_sanitized_source_ledger_to_calibration_decision_replay_rejects_join_drift(self) -> None:
        bundle = self.replay.build_analysis_replay_bundle(
            full_sanitized_cross_slice_replay_request()
        )

        self.assertEqual(bundle["decision"]["decision"], "calibration_complete")
        self.assertEqual(
            bundle["source_lineage"]["successor_freeze"]["source_ledger_binding"],
            bundle["source_lineage"]["source_ledger_binding"],
        )
        self.assertEqual(
            bundle["source_lineage"]["successor_freeze"]["candidate_freeze_binding"],
            bundle["binding_authorities"]["candidate_freeze_binding"],
        )
        self.assertEqual(
            bundle["source_lineage"]["treatment_trace"]["materialization_binding"],
            bundle["source_lineage"]["materialization"]["materialization_binding"],
        )
        self.assertEqual(
            bundle["source_lineage"]["score_bundle"]["execution_trace_binding"],
            bundle["source_lineage"]["treatment_trace"]["execution_trace_binding"],
        )
        self.assertEqual(
            self.replay.replay_analysis_decision(copy.deepcopy(bundle)),
            bundle,
        )

        drifted = copy.deepcopy(bundle)
        drifted["source_lineage"]["score_bundle"]["execution_trace_binding"] = binding(
            "wrong-execution-trace"
        )
        drifted["analysis_replay_artifact_digest"] = digest({
            key: value
            for key, value in drifted.items()
            if key not in {"analysis_replay_artifact_id", "analysis_replay_artifact_digest"}
        })
        drifted["analysis_replay_artifact_id"] = content_id(
            drifted,
            "analysis_replay_artifact_id",
        )

        with self.assertRaisesRegex(
            ValueError,
            "source lineage score bundle does not join treatment trace",
        ):
            self.replay.replay_analysis_decision(drifted)

    def test_analysis_replay_fails_closed_on_digest_drift_or_missing_binding(self) -> None:
        bundle = self.replay.build_analysis_replay_bundle(analysis_replay_request())

        digest_drift = copy.deepcopy(bundle)
        digest_drift["decision"]["reason_codes"] = ["post_hoc_change"]
        with self.assertRaises(ValueError):
            self.replay.replay_analysis_decision(digest_drift)

        id_drift = copy.deepcopy(bundle)
        id_drift["analysis_replay_artifact_id"] = digest("wrong-artifact-id")
        with self.assertRaises(ValueError):
            self.replay.validate_analysis_replay_bundle(id_drift)

        missing = analysis_replay_request()
        del missing["binding_authorities"]["rubric_binding"]
        with self.assertRaises(ValueError):
            self.replay.build_analysis_replay_bundle(missing)

        later_partition = analysis_replay_request()
        later_partition["partition"] = partition_binding("selection", eligible=True)
        with self.assertRaises(ValueError):
            self.replay.build_analysis_replay_bundle(later_partition)

        missing_lineage = analysis_replay_request()
        del missing_lineage["source_lineage"]
        with self.assertRaises(ValueError):
            self.replay.build_analysis_replay_bundle(missing_lineage)

        synthetic_outcomes = analysis_replay_request()
        synthetic_outcomes["paired_outcomes"][0]["semantic_score"] = 1.0
        synthetic_outcomes["source_lineage"]["score_bundle"][
            "paired_outcomes_digest"
        ] = digest(synthetic_outcomes["paired_outcomes"])
        with self.assertRaisesRegex(
            ValueError,
            "paired outcome semantic_score does not match score bundle",
        ):
            self.replay.build_analysis_replay_bundle(synthetic_outcomes)

    def test_analysis_replay_rejects_prohibited_live_raw_integrated_and_trace_mutation_boundaries(self) -> None:
        cases = [
            ("integrated_confirmation", ("partition",), partition_binding("integrated_confirmation", eligible=True)),
            ("live_default_ci", ("execution_boundary", "network_access"), True),
            ("live_repository_write", ("execution_boundary", "live_repository_writes"), ["trace.json"]),
            ("raw_committed_evidence", ("execution_boundary", "operator_only_raw_evidence_root"), "fixture://raw"),
            (
                "trace_mutation",
                ("paired_outcomes", 0, "execution_trace_mutation"),
                {"execution_trace_id": digest("trace"), "after_scoring": True},
            ),
        ]
        for label, path, value in cases:
            with self.subTest(boundary=label):
                request = analysis_replay_request()
                target = request
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value

                with self.assertRaises(ValueError):
                    self.replay.build_analysis_replay_bundle(request)

    def test_cli_replay_uses_deterministic_request_without_live_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request_path = root / "analysis-replay-request.json"
            write_canonical_json(request_path, analysis_replay_request())

            completed = run_qualification_cli("replay", "--request", str(request_path))

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.stdout, canonical_json(payload))
        self.assertEqual(payload["command"], "replay")
        self.assertEqual(payload["status"], "replayed")
        self.assertEqual(payload["decision"]["decision"], "calibration_complete")
        self.assertFalse(payload["execution_boundary"]["network_access"])
        self.assertEqual(payload["execution_boundary"]["live_repository_writes"], [])

    def test_cli_freeze_analysis_plan_requires_completed_protocol_bound_report(self) -> None:
        cases = (
            (
                "missing_protocol",
                "calibration_report_invalid",
            ),
            (
                "incomplete",
                "calibration_not_complete",
            ),
            (
                "invalid_protocol_binding",
                "calibration_protocol_binding_invalid",
            ),
        )
        for label, reason in cases:
            with self.subTest(case=label):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    report_path = root / "calibration-report.json"
                    draft_path = root / "analysis-plan-draft.json"
                    output_path = root / "analysis-plan.json"
                    report = calibration_report_fixture(
                        completed=label != "incomplete",
                    )
                    if label == "missing_protocol":
                        report.pop("calibration_protocol_binding")
                    elif label == "invalid_protocol_binding":
                        report["calibration_protocol_binding"].pop("digest")
                    report = seal_calibration_report(report)
                    draft = analysis_plan_fixture()
                    draft["status"] = "draft_from_calibration"
                    write_canonical_json(report_path, report)
                    write_canonical_json(draft_path, draft)

                    completed = run_qualification_cli(
                        "freeze-analysis-plan",
                        "--calibration-report", str(report_path),
                        "--draft-plan", str(draft_path),
                        "--output", str(output_path),
                    )

                self.assertEqual(completed.returncode, 2)
                payload = json.loads(completed.stdout)
                self.assertEqual(payload["reason"], reason)

    def test_cli_freeze_analysis_plan_rejects_schema_invalid_post_hoc_and_missing_budget_drafts(self) -> None:
        cases = [
            ("missing_numeric_alpha", ("non_inferiority", "alpha"), None),
            ("missing_budget_ceiling", ("campaign_budget", "max_output_tokens"), None),
            ("post_hoc_threshold", ("post_hoc_thresholds",), {"semantic_score": 0.99}),
        ]
        for label, path, value in cases:
            with self.subTest(case=label):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    report_path = root / "calibration-report.json"
                    draft_path = root / "analysis-plan-draft.json"
                    output_path = root / "analysis-plan.json"
                    report = calibration_report_fixture()
                    draft = analysis_plan_fixture()
                    draft["status"] = "draft_from_calibration"
                    target = draft
                    for key in path[:-1]:
                        target = target[key]
                    if value is None:
                        del target[path[-1]]
                    else:
                        target[path[-1]] = value
                    write_canonical_json(report_path, report)
                    write_canonical_json(draft_path, draft)

                    completed = run_qualification_cli(
                        "freeze-analysis-plan",
                        "--calibration-report", str(report_path),
                        "--draft-plan", str(draft_path),
                        "--output", str(output_path),
                    )

                self.assertEqual(completed.returncode, 2)
                payload = json.loads(completed.stdout)
                self.assertEqual(payload["status"], "error")
                self.assertEqual(payload["reason"], "analysis_plan_schema_invalid")

    def test_cli_freeze_analysis_plan_never_overwrites_an_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report_path = root / "calibration-report.json"
            draft_path = root / "analysis-plan-draft.json"
            output_path = root / "analysis-plan.json"
            report = calibration_report_fixture()
            draft = analysis_plan_fixture()
            draft["status"] = "draft_from_calibration"
            write_canonical_json(report_path, report)
            write_canonical_json(draft_path, draft)

            first = run_qualification_cli(
                "freeze-analysis-plan",
                "--calibration-report", str(report_path),
                "--draft-plan", str(draft_path),
                "--output", str(output_path),
            )
            original = output_path.read_bytes()
            second = run_qualification_cli(
                "freeze-analysis-plan",
                "--calibration-report", str(report_path),
                "--draft-plan", str(draft_path),
                "--output", str(output_path),
            )

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(output_path.read_bytes(), original)

            target_path = root / "symlink-target.json"
            target_path.write_text("do-not-overwrite\n", encoding="utf-8")
            symlink_path = root / "symlink-output.json"
            symlink_path.symlink_to(target_path)
            symlinked = run_qualification_cli(
                "freeze-analysis-plan",
                "--calibration-report", str(report_path),
                "--draft-plan", str(draft_path),
                "--output", str(symlink_path),
            )

            self.assertEqual(symlinked.returncode, 2)
            self.assertEqual(target_path.read_text(encoding="utf-8"), "do-not-overwrite\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
