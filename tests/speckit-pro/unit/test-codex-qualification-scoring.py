#!/usr/bin/env python3
"""Focused deterministic tests for G56R-003 qualification scoring gates."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/lib/qualification_scoring.py"
REPLAY_MODULE_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/lib/qualification_replay.py"
SCORE_BUNDLE_SCHEMA_PATH = (
    ROOT / "tests/speckit-pro/layer6-efficiency/contracts/score-bundle.schema.json"
)

EXPECTED_HARD_GATE_ORDER = (
    "role",
    "safety",
    "grounding",
    "mutation",
    "tool",
    "output",
    "acceptance",
)
EXPECTED_PUBLIC_API = frozenset(
    {
        "CANDIDATE_TERMINALS",
        "FAILURE_CODE_PLANES",
        "GATE_DISPOSITIONS",
        "GATE_FAILURE_CODES",
        "HARD_GATE_ORDER",
        "HARD_GATE_SCHEMA_VERSION",
        "SCORER_EVIDENCE_SCHEMA_VERSION",
        "SCORE_BUNDLE_SCHEMA_VERSION",
        "SCORE_DISPOSITIONS",
        "SCORE_FAILURE_CODES",
        "SCORE_FAILURE_PLANES",
        "SCORE_INVALIDATION_REASONS",
        "SEMANTIC_BALLOT_SCHEMA_VERSION",
        "assert_semantic_scoring_allowed",
        "build_score_bundle",
        "canonical_bytes",
        "content_id",
        "digest",
        "evaluate_blinded_ballots",
        "evaluate_hard_gates",
        "sanitize_committed_scorer_evidence",
        "validate_score_bundle",
    }
)
EXPECTED_REPLAY_PUBLIC_API = frozenset(
    {
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
    }
)
EXPECTED_RESULT_FIELDS = frozenset(
    {
        "schema_version",
        "gate_result_id",
        "gate_result_digest",
        "execution_trace_id",
        "trace_digest",
        "fixture_id",
        "fixture_digest",
        "gate_disposition",
        "failure_code",
        "first_failed_gate",
        "gates",
    }
)
EXPECTED_GATE_FIELDS = frozenset(
    {
        "gate_name",
        "passed",
        "evidence_refs",
        "evaluator_version",
        "evaluator_digest",
    }
)
EXPECTED_SEMANTIC_RESULT_FIELDS = frozenset(
    {
        "schema_version",
        "semantic_result_id",
        "semantic_result_digest",
        "gate_result_id",
        "gate_result_digest",
        "score_bundle_draft_id",
        "score_disposition",
        "failure_plane",
        "failure_code",
        "ballots",
        "adjudication",
        "resolved_outcome",
        "semantic_score",
        "reliability_score",
        "disagreement",
    }
)
EXPECTED_BALLOT_FIELDS = frozenset(
    {
        "ballot_id",
        "ballot_digest",
        "blinded_artifact_digest",
        "candidate_blind",
        "scorer_id",
        "scorer_status",
        "scorer_digest",
        "scorer_execution_id",
        "scorer_execution_digest",
        "calibration_id",
        "calibration_digest",
        "calibration_status",
        "rubric_id",
        "rubric_version",
        "rubric_digest",
        "rubric_status",
        "criterion_scores",
        "outcome",
        "submitted_at",
        "provenance_refs",
    }
)
EXPECTED_ADJUDICATION_FIELDS = frozenset(
    {
        "adjudication_id",
        "adjudication_digest",
        "adjudicator_id",
        "adjudicator_status",
        "adjudicator_digest",
        "adjudicator_execution_id",
        "adjudicator_execution_digest",
        "calibration_id",
        "calibration_digest",
        "calibration_status",
        "rubric_id",
        "rubric_version",
        "rubric_digest",
        "rubric_status",
        "ballot_bindings",
        "disagreement_rule",
        "resolved_outcome",
        "submitted_at",
        "provenance_refs",
    }
)
EXPECTED_SCORE_BUNDLE_REQUIRED = [
    "schema_version",
    "score_bundle_id",
    "score_bundle_digest",
    "score_bundle_version",
    "partition_binding",
    "assignment_binding",
    "execution_trace_binding",
    "candidate_route_binding",
    "agent_contract_binding",
    "runtime_snapshot_binding",
    "candidate_freeze_binding",
    "route_resolution_binding",
    "experiment_policy_binding",
    "treatment_contract_binding",
    "telemetry_profile_binding",
    "fixture_binding",
    "gate_result_binding",
    "rubric_binding",
    "scorer_bindings",
    "ballot_bindings",
    "adjudication_binding",
    "deterministic_gates",
    "ballots",
    "adjudication",
    "score_disposition",
    "failure_plane",
    "failure_code",
    "invalidation_reason",
    "invalidated_bundle_binding",
    "semantic_score",
    "reliability_score",
    "resource_vector",
    "evidence_refs",
]
EXPECTED_SCORE_BUNDLE_FIELDS = frozenset(EXPECTED_SCORE_BUNDLE_REQUIRED)
EXPECTED_REPLAY_BUNDLE_FIELDS = frozenset(
    {
        "schema_version",
        "replay_bundle_id",
        "replay_bundle_digest",
        "score_bundle_binding",
        "score_bundle",
        "evidence_refs",
    }
)
EXPECTED_SCORE_REPLAY_SUMMARY_FIELDS = frozenset(
    {
        "schema_version",
        "summary_id",
        "summary_digest",
        "required_core",
        "optional_helpers",
    }
)
EXPECTED_SCORE_REPLAY_SUMMARY_GROUP_FIELDS = frozenset(
    {
        "role_count",
        "accepted_count",
        "score_bundle_ids",
        "replay_bundle_ids",
        "role_ids",
    }
)
EXPECTED_SCORE_BINDING_FIELDS = (
    "partition_binding",
    "assignment_binding",
    "execution_trace_binding",
    "candidate_route_binding",
    "agent_contract_binding",
    "runtime_snapshot_binding",
    "candidate_freeze_binding",
    "route_resolution_binding",
    "experiment_policy_binding",
    "treatment_contract_binding",
    "telemetry_profile_binding",
    "fixture_binding",
    "gate_result_binding",
    "rubric_binding",
)
EXPECTED_SCORE_DISPOSITIONS = ("accepted", "gate_failed", "non_scorable", "invalidated")
EXPECTED_SCORE_FAILURE_PLANES = (
    "none",
    "treatment",
    "fixture",
    "scorer",
    "ballot",
    "adjudication",
    "candidate",
    "infrastructure",
    "evidence_boundary",
    "partition",
    "schema",
)
EXPECTED_SCORE_FAILURE_CODES = (
    "none",
    "treatment_misdelivery",
    "service_reroute",
    "mandatory_telemetry_missing",
    "treatment_infrastructure_failure",
    "fixture_invalid",
    "fixture_stale",
    "fixture_partition_invalid",
    "fixture_oracle_invalid",
    "scorer_invalid",
    "scorer_stale",
    "scorer_calibration_missing",
    "ballot_missing",
    "ballot_non_blind",
    "ballot_provenance_incomplete",
    "ballot_rubric_stale",
    "adjudication_disagreement_unresolved",
    "adjudicator_invalid",
    "adjudicator_stale",
    "adjudicator_reused_primary_scorer",
    "candidate_failed",
    "candidate_timed_out",
    "candidate_cancelled",
    "candidate_budget_exhausted",
    "candidate_abandoned",
    "transient_harness_failure",
    "infrastructure_failure",
    "unclassifiable_attrition",
    "sensitive_evidence_violation",
    "required_evidence_missing",
    "partition_mismatch",
    "partition_not_eligible",
    "cross_partition_reuse",
    "schema_invalid",
    "binding_digest_mismatch",
)
EXPECTED_INVALIDATION_REASONS = (
    "none",
    "fixture_changed",
    "scorer_changed",
    "rubric_changed",
    "adjudicator_changed",
    "treatment_changed",
    "capability_changed",
    "partition_changed",
    "schema_changed",
)
EXPECTED_CANDIDATE_TERMINALS = {
    "failed": "candidate_failed",
    "timed_out": "candidate_timed_out",
    "cancelled": "candidate_cancelled",
    "budget_exhausted": "candidate_budget_exhausted",
    "abandoned": "candidate_abandoned",
}
EXPECTED_FAILURE_CODE_PLANES = {
    "none": "none",
    "treatment_misdelivery": "treatment",
    "service_reroute": "treatment",
    "mandatory_telemetry_missing": "treatment",
    "treatment_infrastructure_failure": "treatment",
    "fixture_invalid": "fixture",
    "fixture_stale": "fixture",
    "fixture_partition_invalid": "fixture",
    "fixture_oracle_invalid": "fixture",
    "scorer_invalid": "scorer",
    "scorer_stale": "scorer",
    "scorer_calibration_missing": "scorer",
    "ballot_missing": "ballot",
    "ballot_non_blind": "ballot",
    "ballot_provenance_incomplete": "ballot",
    "ballot_rubric_stale": "ballot",
    "adjudication_disagreement_unresolved": "adjudication",
    "adjudicator_invalid": "adjudication",
    "adjudicator_stale": "adjudication",
    "adjudicator_reused_primary_scorer": "adjudication",
    "candidate_failed": "candidate",
    "candidate_timed_out": "candidate",
    "candidate_cancelled": "candidate",
    "candidate_budget_exhausted": "candidate",
    "candidate_abandoned": "candidate",
    "transient_harness_failure": "infrastructure",
    "infrastructure_failure": "infrastructure",
    "unclassifiable_attrition": "evidence_boundary",
    "sensitive_evidence_violation": "evidence_boundary",
    "required_evidence_missing": "evidence_boundary",
    "partition_mismatch": "partition",
    "partition_not_eligible": "partition",
    "cross_partition_reuse": "partition",
    "schema_invalid": "schema",
    "binding_digest_mismatch": "schema",
}


def load_scoring_module(name: str | None = None):
    if not MODULE_PATH.exists():
        def missing(*_args, **_kwargs):
            raise AssertionError(f"missing implementation: {MODULE_PATH}")

        return types.SimpleNamespace(
            __all__=(),
            CANDIDATE_TERMINALS=(),
            FAILURE_CODE_PLANES={},
            HARD_GATE_SCHEMA_VERSION="",
            SCORER_EVIDENCE_SCHEMA_VERSION="",
            HARD_GATE_ORDER=(),
            SCORE_BUNDLE_SCHEMA_VERSION="",
            GATE_DISPOSITIONS=(),
            GATE_FAILURE_CODES=(),
            SCORE_INVALIDATION_REASONS=(),
            canonical_bytes=missing,
            digest=missing,
            content_id=missing,
            evaluate_hard_gates=missing,
            assert_semantic_scoring_allowed=missing,
            evaluate_blinded_ballots=missing,
            build_score_bundle=missing,
            sanitize_committed_scorer_evidence=missing,
            validate_score_bundle=missing,
        )

    module_name = name or f"_g56r_003_qualification_scoring_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_replay_module(name: str | None = None):
    if not REPLAY_MODULE_PATH.exists():
        def missing(*_args, **_kwargs):
            raise AssertionError(f"missing implementation: {REPLAY_MODULE_PATH}")

        return types.SimpleNamespace(
            __all__=(),
            REPLAY_BUNDLE_SCHEMA_VERSION="",
            SCORE_REPLAY_SUMMARY_SCHEMA_VERSION="",
            build_score_replay_bundle=missing,
            replay_score_bundle=missing,
            summarize_score_replays=missing,
            validate_score_replay_bundle=missing,
        )

    module_name = name or f"_g56r_003_qualification_replay_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, REPLAY_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {REPLAY_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest(value: object) -> str:
    payload = value if isinstance(value, bytes) else canonical_bytes(value)
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def gate_evidence(gate_name: str, *, passed: bool = True, evidence_refs: list[str] | None = None) -> dict:
    return {
        "gate_name": gate_name,
        "passed": passed,
        "evidence_refs": evidence_refs if evidence_refs is not None else [digest({"evidence": gate_name})],
        "evaluator_version": "hard-gate-evaluator.v1",
        "evaluator_digest": digest({"evaluator": gate_name, "version": "1.0.0"}),
    }


def gate_request(*, gates: list[dict] | None = None, role_id: str = "phase-executor") -> dict:
    return {
        "execution_trace_id": digest(
            {"execution_trace_id": f"trace-{role_id}", "treatment_disposition": "proven"}
        ),
        "trace_digest": digest(
            {"trace": role_id, "terminal": "complete", "treatment_disposition": "proven"}
        ),
        "fixture_id": f"g56r-003-fixture-{role_id}",
        "fixture_digest": digest({"fixture": role_id}),
        "gates": gates if gates is not None else [gate_evidence(name) for name in EXPECTED_HARD_GATE_ORDER],
    }


def result_digest_payload(result: dict) -> dict:
    return {
        key: value
        for key, value in result.items()
        if key not in {"gate_result_id", "gate_result_digest"}
    }


def semantic_digest_payload(result: dict) -> dict:
    return {
        key: value
        for key, value in result.items()
        if key not in {"semantic_result_id", "semantic_result_digest"}
    }


def ballot_digest_payload(ballot: dict) -> dict:
    return {
        key: value
        for key, value in ballot.items()
        if key not in {"ballot_id", "ballot_digest"}
    }


def adjudication_digest_payload(adjudication: dict) -> dict:
    return {
        key: value
        for key, value in adjudication.items()
        if key not in {"adjudication_id", "adjudication_digest"}
    }


def scorer_ballot(
    scorer_id: str,
    *,
    scorer_execution_id: str | None = None,
    candidate_blind: bool = True,
    scorer_status: str = "current",
    calibration_status: str = "current",
    rubric_status: str = "frozen",
    rubric_digest_value: str | None = None,
    outcome: str = "accept",
    semantic: float = 0.92,
    reliability: float = 0.88,
    provenance_refs: list[str] | None = None,
) -> dict:
    execution_id = scorer_execution_id or f"g56r-003-scorer-execution-{scorer_id}"
    rubric_digest = rubric_digest_value or digest({"rubric": "g56r-003", "version": "1.0.0"})
    return {
        "blinded_artifact_digest": digest({"artifact": "candidate-blind-summary"}),
        "candidate_blind": candidate_blind,
        "scorer_id": scorer_id,
        "scorer_status": scorer_status,
        "scorer_digest": digest({"scorer": scorer_id, "version": "1.0.0"}),
        "scorer_execution_id": execution_id,
        "scorer_execution_digest": digest({"scorer_execution": execution_id}),
        "calibration_id": "g56r-003-scorer-calibration-v1",
        "calibration_digest": digest({"calibration": "scorer", "version": "1.0.0"}),
        "calibration_status": calibration_status,
        "rubric_id": "g56r-003-semantic-rubric",
        "rubric_version": "1.0.0",
        "rubric_digest": rubric_digest,
        "rubric_status": rubric_status,
        "criterion_scores": {"semantic": semantic, "reliability": reliability},
        "outcome": outcome,
        "submitted_at": "2026-07-24T12:00:00Z",
        "provenance_refs": provenance_refs if provenance_refs is not None else [digest({"ballot": scorer_id})],
    }


def adjudicator_record(
    *,
    adjudicator_id: str = "opaque-adjudicator-c",
    adjudicator_status: str = "current",
    calibration_status: str = "current",
    rubric_status: str = "frozen",
    resolved_outcome: str = "accept",
    provenance_refs: list[str] | None = None,
) -> dict:
    execution_id = f"g56r-003-adjudicator-execution-{adjudicator_id}"
    return {
        "adjudicator_id": adjudicator_id,
        "adjudicator_status": adjudicator_status,
        "adjudicator_digest": digest({"adjudicator": adjudicator_id, "version": "1.0.0"}),
        "adjudicator_execution_id": execution_id,
        "adjudicator_execution_digest": digest({"adjudicator_execution": execution_id}),
        "calibration_id": "g56r-003-adjudicator-calibration-v1",
        "calibration_digest": digest({"calibration": "adjudicator", "version": "1.0.0"}),
        "calibration_status": calibration_status,
        "rubric_id": "g56r-003-semantic-rubric",
        "rubric_version": "1.0.0",
        "rubric_digest": digest({"rubric": "g56r-003", "version": "1.0.0"}),
        "rubric_status": rubric_status,
        "disagreement_rule": "decision_affecting_outcome_mismatch",
        "resolved_outcome": resolved_outcome,
        "submitted_at": "2026-07-24T12:05:00Z",
        "provenance_refs": provenance_refs
        if provenance_refs is not None
        else [digest({"adjudication": adjudicator_id})],
    }


def semantic_request(*, ballots: list[dict] | None = None, adjudication: dict | None = None) -> dict:
    return {
        "score_bundle_draft_id": "g56r-003-score-draft-phase-executor",
        "ballots": ballots
        if ballots is not None
        else [
            scorer_ballot("opaque-scorer-a"),
            scorer_ballot("opaque-scorer-b", semantic=0.9, reliability=0.86),
        ],
        "adjudication": adjudication,
    }


def binding(name: str) -> dict:
    return {"id": f"g56r-003-{name}", "digest": digest({"binding": name})}


def resource_vector(*, terminal_state: str = "completed", acceptance: float | None = 1.0) -> dict:
    return {
        "input_tokens": 1200,
        "cached_input_tokens": 200,
        "output_tokens": 320,
        "duration_ms": 45000,
        "retries": 0,
        "compactions": 0,
        "acceptance": acceptance,
        "terminal_state": terminal_state,
    }


def score_bundle_request(
    gate_result: dict,
    *,
    semantic_result: dict | None,
    score_disposition: str = "accepted",
    failure_plane: str = "none",
    failure_code: str = "none",
    invalidation_reason: str = "none",
    invalidated_bundle_binding: dict | None = None,
    vector: dict | None = None,
) -> dict:
    if semantic_result and semantic_result.get("ballots"):
        rubric = semantic_result["ballots"][0]
        rubric_binding = {"id": rubric["rubric_id"], "digest": rubric["rubric_digest"]}
    else:
        rubric_binding = binding("rubric")
    return {
        "score_bundle_version": "1.0.0",
        "partition_binding": binding("partition-calibration"),
        "assignment_binding": binding("assignment-phase-executor"),
        "execution_trace_binding": {
            "id": gate_result["execution_trace_id"],
            "digest": gate_result["trace_digest"],
        },
        "candidate_route_binding": binding("candidate-route-phase-executor"),
        "agent_contract_binding": binding("agent-contract-phase-executor"),
        "runtime_snapshot_binding": binding("runtime-snapshot"),
        "candidate_freeze_binding": binding("candidate-freeze"),
        "route_resolution_binding": binding("route-resolution"),
        "experiment_policy_binding": binding("experiment-policy"),
        "treatment_contract_binding": binding("treatment-contract"),
        "telemetry_profile_binding": binding("telemetry-profile"),
        "fixture_binding": {
            "id": gate_result["fixture_id"],
            "digest": gate_result["fixture_digest"],
        },
        "gate_result_binding": {
            "id": gate_result["gate_result_id"],
            "digest": gate_result["gate_result_digest"],
        },
        "rubric_binding": rubric_binding,
        "gate_result": gate_result,
        "semantic_result": semantic_result,
        "score_disposition": score_disposition,
        "failure_plane": failure_plane,
        "failure_code": failure_code,
        "invalidation_reason": invalidation_reason,
        "invalidated_bundle_binding": invalidated_bundle_binding,
        "resource_vector": vector if vector is not None else resource_vector(),
        "evidence_refs": [digest({"score-bundle-evidence": "phase-executor"})],
    }


def score_bundle_digest_payload(bundle: dict) -> dict:
    return {
        key: value
        for key, value in bundle.items()
        if key not in {"score_bundle_id", "score_bundle_digest"}
    }


def score_replay_summary_digest_payload(summary: dict) -> dict:
    return {
        key: value
        for key, value in summary.items()
        if key not in {"summary_id", "summary_digest"}
    }


class CodexQualificationScoringGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scoring = load_scoring_module()
        self.replay = load_replay_module()

    def assert_failed_gate_result(self, result: dict, *, code: str, first_gate: str | None) -> None:
        self.assertEqual(set(result), EXPECTED_RESULT_FIELDS)
        self.assertEqual(result["gate_disposition"], "failed")
        self.assertEqual(result["failure_code"], code)
        self.assertEqual(result["first_failed_gate"], first_gate)
        with self.assertRaisesRegex(ValueError, "deterministic hard gates must pass"):
            self.scoring.assert_semantic_scoring_allowed(result)

    def assert_failed_semantic_result(self, result: dict, *, plane: str, code: str) -> None:
        self.assertEqual(set(result), EXPECTED_SEMANTIC_RESULT_FIELDS)
        self.assertEqual(result["schema_version"], self.scoring.SEMANTIC_BALLOT_SCHEMA_VERSION)
        self.assertEqual(result["score_disposition"], "non_scorable")
        self.assertEqual(result["failure_plane"], plane)
        self.assertEqual(result["failure_code"], code)
        self.assertIsNone(result["resolved_outcome"])
        self.assertIsNone(result["semantic_score"])
        self.assertIsNone(result["reliability_score"])
        self.assertEqual(result["semantic_result_digest"], self.scoring.digest(semantic_digest_payload(result)))
        self.assertEqual(result["semantic_result_id"], self.scoring.content_id(result, "semantic_result_id"))

    def test_public_api_declares_closed_ordered_hard_gates(self) -> None:
        self.assertEqual(frozenset(self.scoring.__all__), EXPECTED_PUBLIC_API)
        self.assertEqual(frozenset(self.replay.__all__), EXPECTED_REPLAY_PUBLIC_API)
        self.assertEqual(tuple(self.scoring.HARD_GATE_ORDER), EXPECTED_HARD_GATE_ORDER)
        self.assertEqual(self.scoring.HARD_GATE_SCHEMA_VERSION, "hard-gates.v1")
        self.assertEqual(self.scoring.SCORER_EVIDENCE_SCHEMA_VERSION, "scorer-evidence.v1")
        self.assertEqual(self.scoring.SEMANTIC_BALLOT_SCHEMA_VERSION, "semantic-ballots.v1")
        self.assertEqual(self.scoring.SCORE_BUNDLE_SCHEMA_VERSION, "score-bundle.v1")
        self.assertEqual(self.replay.REPLAY_BUNDLE_SCHEMA_VERSION, "score-replay.v1")
        self.assertEqual(self.replay.SCORE_REPLAY_SUMMARY_SCHEMA_VERSION, "score-replay-summary.v1")
        self.assertEqual(tuple(self.scoring.GATE_DISPOSITIONS), ("passed", "failed"))
        self.assertEqual(
            tuple(self.scoring.GATE_FAILURE_CODES),
            ("none", "gate_failed", "gate_missing", "evidence_missing", "gate_order_invalid"),
        )
        self.assertEqual(tuple(self.scoring.SCORE_DISPOSITIONS), EXPECTED_SCORE_DISPOSITIONS)
        self.assertEqual(tuple(self.scoring.SCORE_FAILURE_PLANES), EXPECTED_SCORE_FAILURE_PLANES)
        self.assertEqual(tuple(self.scoring.SCORE_FAILURE_CODES), EXPECTED_SCORE_FAILURE_CODES)
        self.assertEqual(tuple(self.scoring.SCORE_INVALIDATION_REASONS), EXPECTED_INVALIDATION_REASONS)
        self.assertEqual(dict(self.scoring.CANDIDATE_TERMINALS), EXPECTED_CANDIDATE_TERMINALS)
        self.assertEqual(dict(self.scoring.FAILURE_CODE_PLANES), EXPECTED_FAILURE_CODE_PLANES)

    def test_score_bundle_schema_is_self_contained_and_matches_closed_contract(self) -> None:
        self.assertTrue(
            SCORE_BUNDLE_SCHEMA_PATH.exists(),
            f"missing repository score-bundle schema: {SCORE_BUNDLE_SCHEMA_PATH}",
        )
        schema = json.loads(SCORE_BUNDLE_SCHEMA_PATH.read_text(encoding="utf-8"))

        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["$id"], "https://racecraft.dev/schemas/g56r-003/score-bundle.schema.json")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["required"], EXPECTED_SCORE_BUNDLE_REQUIRED)
        self.assertEqual(set(schema["properties"]), EXPECTED_SCORE_BUNDLE_FIELDS)
        self.assertEqual(schema["properties"]["schema_version"], {"const": "score-bundle.v1"})
        self.assertEqual(
            tuple(schema["properties"]["score_disposition"]["enum"]),
            tuple(self.scoring.SCORE_DISPOSITIONS),
        )
        self.assertEqual(
            tuple(schema["properties"]["failure_plane"]["enum"]),
            tuple(self.scoring.SCORE_FAILURE_PLANES),
        )
        self.assertEqual(
            tuple(schema["properties"]["failure_code"]["enum"]),
            tuple(self.scoring.SCORE_FAILURE_CODES),
        )
        self.assertEqual(
            tuple(schema["properties"]["invalidation_reason"]["enum"]),
            tuple(self.scoring.SCORE_INVALIDATION_REASONS),
        )
        self.assertEqual(
            tuple(schema["properties"]["resource_vector"]["properties"]["terminal_state"]["enum"]),
            ("completed", "failed", "timed_out", "cancelled", "budget_exhausted", "abandoned", "unknown"),
        )
        for field in EXPECTED_SCORE_BINDING_FIELDS:
            with self.subTest(binding_field=field):
                self.assertEqual(schema["properties"][field], {"$ref": "#/$defs/binding"})
        self.assertEqual(schema["properties"]["invalidated_bundle_binding"]["oneOf"][0], {"type": "null"})

    def test_score_bundle_builder_emits_immutable_bundle_without_embedding_traces(self) -> None:
        gate_result = self.scoring.evaluate_hard_gates(gate_request())
        semantic_result = self.scoring.evaluate_blinded_ballots(gate_result, semantic_request())
        request = score_bundle_request(gate_result, semantic_result=semantic_result)
        original = copy.deepcopy(request)

        bundle = self.scoring.build_score_bundle(request)

        self.assertEqual(request, original, "score bundle construction must not mutate caller data")
        self.assertEqual(set(bundle), EXPECTED_SCORE_BUNDLE_FIELDS)
        self.assertNotIn("execution_trace", bundle)
        self.assertNotIn("trace", bundle)
        self.assertNotIn("gate_result", bundle)
        self.assertNotIn("semantic_result", bundle)
        self.assertEqual(bundle["schema_version"], self.scoring.SCORE_BUNDLE_SCHEMA_VERSION)
        self.assertEqual(bundle["execution_trace_binding"], request["execution_trace_binding"])
        self.assertEqual(bundle["fixture_binding"], request["fixture_binding"])
        self.assertEqual(bundle["gate_result_binding"], request["gate_result_binding"])
        self.assertEqual(bundle["score_disposition"], "accepted")
        self.assertEqual(bundle["failure_plane"], "none")
        self.assertEqual(bundle["failure_code"], "none")
        self.assertEqual(bundle["invalidation_reason"], "none")
        self.assertIsNone(bundle["invalidated_bundle_binding"])
        self.assertEqual(bundle["semantic_score"], semantic_result["semantic_score"])
        self.assertEqual(bundle["reliability_score"], semantic_result["reliability_score"])
        self.assertEqual(len(bundle["deterministic_gates"]), len(EXPECTED_HARD_GATE_ORDER))
        self.assertEqual([gate["gate"] for gate in bundle["deterministic_gates"]], list(EXPECTED_HARD_GATE_ORDER))
        self.assertEqual(len(bundle["ballots"]), 2)
        self.assertEqual(
            bundle["ballot_bindings"],
            [{"id": ballot["ballot_id"], "digest": ballot["ballot_digest"]} for ballot in semantic_result["ballots"]],
        )
        self.assertEqual(
            bundle["scorer_bindings"],
            [
                {"id": ballot["scorer_id"], "digest": ballot["scorer_digest"]}
                for ballot in semantic_result["ballots"]
            ],
        )
        self.assertEqual(bundle["score_bundle_digest"], self.scoring.digest(score_bundle_digest_payload(bundle)))
        self.assertEqual(bundle["score_bundle_id"], self.scoring.content_id(bundle, "score_bundle_id"))
        self.assertEqual(self.scoring.validate_score_bundle(bundle), bundle)

        request["gate_result"]["trace_digest"] = digest({"trace": "mutated-after-build"})
        self.assertEqual(bundle["execution_trace_binding"], original["execution_trace_binding"])

    def test_score_bundle_requires_every_upstream_id_and_digest_join(self) -> None:
        gate_result = self.scoring.evaluate_hard_gates(gate_request())
        semantic_result = self.scoring.evaluate_blinded_ballots(gate_result, semantic_request())

        for field in EXPECTED_SCORE_BINDING_FIELDS:
            for key in ("id", "digest"):
                with self.subTest(binding_field=field, missing=key):
                    request = score_bundle_request(gate_result, semantic_result=semantic_result)
                    request[field] = copy.deepcopy(request[field])
                    request[field].pop(key)
                    with self.assertRaisesRegex(ValueError, "binding"):
                        self.scoring.build_score_bundle(request)

        mismatch_cases = (
            ("execution_trace_binding", "digest", digest({"trace": "wrong"})),
            ("fixture_binding", "id", "wrong-fixture"),
            ("gate_result_binding", "digest", digest({"gate-result": "wrong"})),
        )
        for field, key, value in mismatch_cases:
            with self.subTest(binding_field=field, mismatched=key):
                request = score_bundle_request(gate_result, semantic_result=semantic_result)
                request[field] = copy.deepcopy(request[field])
                request[field][key] = value
                with self.assertRaisesRegex(ValueError, "does not match"):
                    self.scoring.build_score_bundle(request)

    def test_score_bundle_closed_enums_and_none_coupling_fail_closed(self) -> None:
        gate_result = self.scoring.evaluate_hard_gates(gate_request())
        semantic_result = self.scoring.evaluate_blinded_ballots(gate_result, semantic_request())
        cases = (
            ("bad disposition", {"score_disposition": "pending"}, "score disposition"),
            ("bad plane", {"failure_plane": "runtime"}, "failure plane"),
            ("bad code", {"failure_code": "mystery"}, "failure code"),
            ("bad invalidation", {"invalidation_reason": "manually_redacted"}, "invalidation reason"),
            ("none plane with code", {"failure_plane": "none", "failure_code": "candidate_failed"}, "failure code"),
            ("candidate plane with none", {"failure_plane": "candidate", "failure_code": "none"}, "failure code"),
            (
                "wrong plane for attrition",
                {"failure_plane": "candidate", "failure_code": "unclassifiable_attrition"},
                "failure plane",
            ),
            (
                "invalidated without reason",
                {"score_disposition": "invalidated", "invalidated_bundle_binding": binding("old-score")},
                "invalidation reason",
            ),
            (
                "invalidated without target",
                {"score_disposition": "invalidated", "invalidation_reason": "rubric_changed"},
                "invalidated bundle",
            ),
            (
                "non-invalidated with reason",
                {"invalidation_reason": "rubric_changed"},
                "invalidation reason",
            ),
        )

        for label, overrides, message in cases:
            with self.subTest(label=label):
                request = score_bundle_request(gate_result, semantic_result=semantic_result)
                request.update(overrides)
                with self.assertRaisesRegex(ValueError, message):
                    self.scoring.build_score_bundle(request)

    def test_candidate_terminals_are_accepted_estimand_records_with_zero_acceptance(self) -> None:
        gate_result = self.scoring.evaluate_hard_gates(gate_request())
        for terminal_state, failure_code in EXPECTED_CANDIDATE_TERMINALS.items():
            with self.subTest(terminal_state=terminal_state):
                request = score_bundle_request(
                    gate_result,
                    semantic_result=None,
                    failure_plane="candidate",
                    failure_code=failure_code,
                    vector=resource_vector(terminal_state=terminal_state, acceptance=0.0),
                )
                bundle = self.scoring.build_score_bundle(request)

                self.assertEqual(bundle["score_disposition"], "accepted")
                self.assertEqual(bundle["failure_plane"], "candidate")
                self.assertEqual(bundle["failure_code"], failure_code)
                self.assertEqual(bundle["resource_vector"]["terminal_state"], terminal_state)
                self.assertEqual(bundle["resource_vector"]["acceptance"], 0.0)
                self.assertEqual(bundle["ballots"], [])
                self.assertEqual(bundle["ballot_bindings"], [])
                self.assertIsNone(bundle["semantic_score"])
                self.assertIsNone(bundle["reliability_score"])
                self.assertEqual(self.scoring.validate_score_bundle(bundle), bundle)

    def test_unclassifiable_attrition_is_evidence_boundary_not_candidate_or_transient(self) -> None:
        gate_result = self.scoring.evaluate_hard_gates(gate_request())
        request = score_bundle_request(
            gate_result,
            semantic_result=None,
            score_disposition="non_scorable",
            failure_plane="evidence_boundary",
            failure_code="unclassifiable_attrition",
            vector=resource_vector(terminal_state="unknown", acceptance=None),
        )

        bundle = self.scoring.build_score_bundle(request)

        self.assertEqual(bundle["score_disposition"], "non_scorable")
        self.assertEqual(bundle["failure_plane"], "evidence_boundary")
        self.assertEqual(bundle["failure_code"], "unclassifiable_attrition")
        self.assertEqual(bundle["resource_vector"]["terminal_state"], "unknown")
        self.assertIsNone(bundle["resource_vector"]["acceptance"])
        self.assertEqual(bundle["ballots"], [])
        self.assertEqual(self.scoring.validate_score_bundle(bundle), bundle)

    def test_additive_invalidation_creates_new_bundle_without_mutating_prior(self) -> None:
        gate_result = self.scoring.evaluate_hard_gates(gate_request())
        semantic_result = self.scoring.evaluate_blinded_ballots(gate_result, semantic_request())
        prior = self.scoring.build_score_bundle(score_bundle_request(gate_result, semantic_result=semantic_result))
        prior_original = copy.deepcopy(prior)
        invalidated_binding = {
            "id": prior["score_bundle_id"],
            "digest": prior["score_bundle_digest"],
        }

        replacement = self.scoring.build_score_bundle(
            score_bundle_request(
                gate_result,
                semantic_result=semantic_result,
                score_disposition="invalidated",
                invalidation_reason="rubric_changed",
                invalidated_bundle_binding=invalidated_binding,
            )
        )

        self.assertEqual(prior, prior_original, "additive invalidation must not mutate the prior bundle")
        self.assertEqual(replacement["score_disposition"], "invalidated")
        self.assertEqual(replacement["failure_plane"], "none")
        self.assertEqual(replacement["failure_code"], "none")
        self.assertEqual(replacement["invalidation_reason"], "rubric_changed")
        self.assertEqual(replacement["invalidated_bundle_binding"], invalidated_binding)
        self.assertNotEqual(replacement["score_bundle_id"], prior["score_bundle_id"])
        self.assertNotEqual(replacement["score_bundle_digest"], prior["score_bundle_digest"])
        self.assertEqual(self.scoring.validate_score_bundle(replacement), replacement)

    def test_score_bundle_rejects_embedded_or_mutated_trace_inputs(self) -> None:
        gate_result = self.scoring.evaluate_hard_gates(gate_request())
        semantic_result = self.scoring.evaluate_blinded_ballots(gate_result, semantic_request())

        embedded = score_bundle_request(gate_result, semantic_result=semantic_result)
        embedded["execution_trace"] = {"execution_trace_id": gate_result["execution_trace_id"]}
        with self.assertRaisesRegex(ValueError, "embedded trace"):
            self.scoring.build_score_bundle(embedded)

        bundle = self.scoring.build_score_bundle(score_bundle_request(gate_result, semantic_result=semantic_result))
        mutated = copy.deepcopy(bundle)
        mutated["execution_trace_binding"]["digest"] = digest({"trace": "post-hoc mutation"})
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.scoring.validate_score_bundle(mutated)

    def test_committed_scorer_evidence_sanitizer_rejects_private_values_and_unknown_keys(self) -> None:
        gate_result = self.scoring.evaluate_hard_gates(gate_request())
        semantic_result = self.scoring.evaluate_blinded_ballots(gate_result, semantic_request())
        bundle = self.scoring.build_score_bundle(score_bundle_request(gate_result, semantic_result=semantic_result))
        original = copy.deepcopy(bundle)

        sanitized = self.scoring.sanitize_committed_scorer_evidence(bundle)

        self.assertEqual(sanitized, bundle)
        self.assertEqual(bundle, original, "scorer evidence sanitization must not mutate caller data")

        sensitive_cases = (
            ("raw prompt", lambda evidence: evidence.update({"raw_prompt": "score this raw prompt"})),
            ("raw response", lambda evidence: evidence.update({"raw_response": "model output"})),
            ("raw transcript", lambda evidence: evidence.update({"raw_transcript": "terminal transcript"})),
            (
                "personal scorer mapping",
                lambda evidence: evidence.update({"personal_scorer_mapping": {"opaque-scorer-a": "Ada"}}),
            ),
            ("account", lambda evidence: evidence.update({"account_id": "acct_personal_123"})),
            ("auth", lambda evidence: evidence.update({"auth_token": "Bearer private-token"})),
            ("credential", lambda evidence: evidence.update({"credential": "sk-local-secret"})),
            ("session", lambda evidence: evidence.update({"session_id": "session-private-123"})),
            ("cookie", lambda evidence: evidence.update({"cookie": "sid=private"})),
            ("header", lambda evidence: evidence.update({"header": "Authorization: Bearer token"})),
            ("private host", lambda evidence: evidence.update({"private_host": "internal.service.local"})),
            ("absolute path", lambda evidence: evidence["evidence_refs"].append("/private/runtime/raw-score.json")),
            ("remote", lambda evidence: evidence["candidate_route_binding"].update({"id": "git@github.com:org/private"})),
            ("billing", lambda evidence: evidence.update({"billing_id": "billing-private"})),
            ("plan", lambda evidence: evidence.update({"plan_id": "enterprise-private"})),
        )
        for label, mutate in sensitive_cases:
            with self.subTest(label=label):
                evidence = copy.deepcopy(bundle)
                mutate(evidence)
                with self.assertRaisesRegex(ValueError, "sensitive evidence"):
                    self.scoring.sanitize_committed_scorer_evidence(evidence)

        unknown = copy.deepcopy(bundle)
        unknown["operator_notes"] = "not on the committed evidence allowlist"
        with self.assertRaisesRegex(ValueError, "unknown committed evidence key"):
            self.scoring.sanitize_committed_scorer_evidence(unknown)

    def test_scorer_and_adjudicator_bindings_must_be_opaque(self) -> None:
        gate_result = self.scoring.evaluate_hard_gates(gate_request())
        personal_scorer = self.scoring.evaluate_blinded_ballots(
            gate_result,
            semantic_request(
                ballots=[
                    scorer_ballot("personal-scorer-a"),
                    scorer_ballot("opaque-scorer-b"),
                ]
            ),
        )
        self.assert_failed_semantic_result(personal_scorer, plane="scorer", code="scorer_invalid")

        ballots = [
            scorer_ballot("opaque-scorer-a", outcome="accept"),
            scorer_ballot("opaque-scorer-b", outcome="reject", semantic=0.72, reliability=0.74),
        ]
        personal_adjudicator = self.scoring.evaluate_blinded_ballots(
            gate_result,
            semantic_request(ballots=ballots, adjudication=adjudicator_record(adjudicator_id="personal-adjudicator-c")),
        )
        self.assert_failed_semantic_result(
            personal_adjudicator,
            plane="adjudication",
            code="adjudicator_invalid",
        )

    def test_stale_score_bundle_versions_require_additive_invalidation(self) -> None:
        gate_result = self.scoring.evaluate_hard_gates(gate_request())
        semantic_result = self.scoring.evaluate_blinded_ballots(gate_result, semantic_request())
        current = self.scoring.build_score_bundle(score_bundle_request(gate_result, semantic_result=semantic_result))
        current_original = copy.deepcopy(current)

        stale_request = score_bundle_request(gate_result, semantic_result=semantic_result)
        stale_request["score_bundle_version"] = "0.9.0"
        with self.assertRaisesRegex(ValueError, "stale score bundle version"):
            self.scoring.build_score_bundle(stale_request)

        stale_published = copy.deepcopy(current)
        stale_published["score_bundle_version"] = "0.9.0"
        stale_published["score_bundle_digest"] = self.scoring.digest(score_bundle_digest_payload(stale_published))
        stale_published["score_bundle_id"] = self.scoring.content_id(stale_published, "score_bundle_id")
        with self.assertRaisesRegex(ValueError, "stale score bundle version"):
            self.scoring.sanitize_committed_scorer_evidence(stale_published)

        invalidated_binding = {
            "id": current["score_bundle_id"],
            "digest": current["score_bundle_digest"],
        }
        replacement = self.scoring.build_score_bundle(
            score_bundle_request(
                gate_result,
                semantic_result=semantic_result,
                score_disposition="invalidated",
                invalidation_reason="schema_changed",
                invalidated_bundle_binding=invalidated_binding,
            )
        )

        self.assertEqual(current, current_original, "stale-version handling must not mutate prior bundles")
        self.assertEqual(replacement["score_disposition"], "invalidated")
        self.assertEqual(replacement["invalidation_reason"], "schema_changed")
        self.assertEqual(replacement["invalidated_bundle_binding"], invalidated_binding)
        self.assertEqual(self.scoring.sanitize_committed_scorer_evidence(replacement), replacement)

    def test_score_replay_is_deterministic_and_detects_drift(self) -> None:
        gate_result = self.scoring.evaluate_hard_gates(gate_request())
        semantic_result = self.scoring.evaluate_blinded_ballots(gate_result, semantic_request())
        bundle = self.scoring.build_score_bundle(score_bundle_request(gate_result, semantic_result=semantic_result))

        replay_bundle = self.replay.build_score_replay_bundle(
            {
                "score_bundle": bundle,
                "evidence_refs": [digest({"replay": "score-bundle"})],
            }
        )

        self.assertEqual(set(replay_bundle), EXPECTED_REPLAY_BUNDLE_FIELDS)
        self.assertEqual(replay_bundle["schema_version"], self.replay.REPLAY_BUNDLE_SCHEMA_VERSION)
        self.assertEqual(
            replay_bundle["score_bundle_binding"],
            {"id": bundle["score_bundle_id"], "digest": bundle["score_bundle_digest"]},
        )
        self.assertEqual(self.replay.validate_score_replay_bundle(replay_bundle), replay_bundle)
        self.assertEqual(self.replay.replay_score_bundle(replay_bundle), bundle)

        drifted = copy.deepcopy(replay_bundle)
        drifted["score_bundle"]["resource_vector"]["output_tokens"] += 1
        with self.assertRaisesRegex(ValueError, "score replay drift"):
            self.replay.replay_score_bundle(drifted)

        rebound_drift = copy.deepcopy(replay_bundle)
        rebound_drift["score_bundle"]["resource_vector"]["output_tokens"] += 1
        rebound_drift["score_bundle"]["score_bundle_digest"] = self.scoring.digest(
            score_bundle_digest_payload(rebound_drift["score_bundle"])
        )
        rebound_drift["score_bundle"]["score_bundle_id"] = self.scoring.content_id(
            rebound_drift["score_bundle"],
            "score_bundle_id",
        )
        rebound_drift["replay_bundle_digest"] = self.scoring.digest(
            {
                key: value
                for key, value in rebound_drift.items()
                if key not in {"replay_bundle_id", "replay_bundle_digest"}
            }
        )
        rebound_drift["replay_bundle_id"] = self.scoring.content_id(rebound_drift, "replay_bundle_id")
        with self.assertRaisesRegex(ValueError, "score replay drift"):
            self.replay.replay_score_bundle(rebound_drift)

    def test_treatment_proven_governed_fixture_adjudication_replay_and_helper_summary(self) -> None:
        gate_result = self.scoring.evaluate_hard_gates(gate_request(role_id="implement-executor"))
        ballots = [
            scorer_ballot("opaque-scorer-a", outcome="accept"),
            scorer_ballot("opaque-scorer-b", outcome="reject", semantic=0.72, reliability=0.74),
        ]
        semantic_result = self.scoring.evaluate_blinded_ballots(
            gate_result,
            semantic_request(ballots=ballots, adjudication=adjudicator_record(resolved_outcome="accept")),
        )
        bundle = self.scoring.build_score_bundle(score_bundle_request(gate_result, semantic_result=semantic_result))
        replay_bundle = self.replay.build_score_replay_bundle(
            {
                "score_bundle": bundle,
                "evidence_refs": [digest({"replay": "implement-executor-adjudicated"})],
            }
        )

        self.assertEqual(self.replay.replay_score_bundle(replay_bundle), bundle)
        self.assertEqual(bundle["score_disposition"], "accepted")
        self.assertEqual(bundle["failure_plane"], "none")
        self.assertEqual(bundle["fixture_binding"]["id"], "g56r-003-fixture-implement-executor")
        self.assertIsNotNone(bundle["adjudication_binding"])
        self.assertEqual(bundle["semantic_score"], 0.82)
        self.assertEqual(bundle["reliability_score"], 0.81)

        helper_gate = self.scoring.evaluate_hard_gates(gate_request(role_id="autopilot-fast-helper"))
        helper_semantic = self.scoring.evaluate_blinded_ballots(helper_gate, semantic_request())
        helper_bundle = self.scoring.build_score_bundle(
            score_bundle_request(helper_gate, semantic_result=helper_semantic)
        )
        helper_replay = self.replay.build_score_replay_bundle(
            {
                "score_bundle": helper_bundle,
                "evidence_refs": [digest({"replay": "autopilot-fast-helper"})],
            }
        )

        summary = self.replay.summarize_score_replays(
            {
                "score_replays": [
                    {
                        "role_id": "implement-executor",
                        "required_core": True,
                        "optional_helper": False,
                        "replay_bundle": replay_bundle,
                    },
                    {
                        "role_id": "autopilot-fast-helper",
                        "required_core": False,
                        "optional_helper": True,
                        "replay_bundle": helper_replay,
                    },
                ]
            }
        )

        self.assertEqual(set(summary), EXPECTED_SCORE_REPLAY_SUMMARY_FIELDS)
        self.assertEqual(summary["schema_version"], self.replay.SCORE_REPLAY_SUMMARY_SCHEMA_VERSION)
        self.assertEqual(set(summary["required_core"]), EXPECTED_SCORE_REPLAY_SUMMARY_GROUP_FIELDS)
        self.assertEqual(set(summary["optional_helpers"]), EXPECTED_SCORE_REPLAY_SUMMARY_GROUP_FIELDS)
        self.assertEqual(summary["required_core"]["role_ids"], ["implement-executor"])
        self.assertEqual(summary["required_core"]["score_bundle_ids"], [bundle["score_bundle_id"]])
        self.assertEqual(summary["optional_helpers"]["role_ids"], ["autopilot-fast-helper"])
        self.assertEqual(summary["optional_helpers"]["score_bundle_ids"], [helper_bundle["score_bundle_id"]])
        self.assertNotIn("autopilot-fast-helper", summary["required_core"]["role_ids"])
        self.assertEqual(summary["summary_digest"], self.scoring.digest(score_replay_summary_digest_payload(summary)))
        self.assertEqual(summary["summary_id"], self.scoring.content_id(summary, "summary_id"))

    def test_all_ordered_hard_gates_pass_before_semantic_scoring(self) -> None:
        request = gate_request()
        original = copy.deepcopy(request)
        result = self.scoring.evaluate_hard_gates(request)

        self.assertEqual(request, original, "gate evaluation must not mutate caller data")
        self.assertEqual(set(result), EXPECTED_RESULT_FIELDS)
        self.assertEqual(result["schema_version"], self.scoring.HARD_GATE_SCHEMA_VERSION)
        self.assertEqual(result["gate_disposition"], "passed")
        self.assertEqual(result["failure_code"], "none")
        self.assertIsNone(result["first_failed_gate"])
        self.assertEqual([gate["gate_name"] for gate in result["gates"]], list(EXPECTED_HARD_GATE_ORDER))
        self.assertTrue(all(gate["passed"] for gate in result["gates"]))
        self.assertTrue(all(set(gate) == EXPECTED_GATE_FIELDS for gate in result["gates"]))
        self.assertEqual(result["gate_result_digest"], self.scoring.digest(result_digest_payload(result)))
        self.assertEqual(result["gate_result_id"], self.scoring.content_id(result, "gate_result_id"))
        self.assertEqual(self.scoring.assert_semantic_scoring_allowed(result), result)

    def test_each_role_safety_grounding_mutation_tool_output_and_acceptance_gate_fails_closed(self) -> None:
        for gate_name in EXPECTED_HARD_GATE_ORDER:
            with self.subTest(gate_name=gate_name):
                gates = [gate_evidence(name, passed=name != gate_name) for name in EXPECTED_HARD_GATE_ORDER]
                result = self.scoring.evaluate_hard_gates(gate_request(gates=gates))
                self.assert_failed_gate_result(result, code="gate_failed", first_gate=gate_name)

    def test_missing_evidence_fails_closed_without_reaching_scoring(self) -> None:
        gates = [
            gate_evidence(name, evidence_refs=[] if name == "grounding" else None)
            for name in EXPECTED_HARD_GATE_ORDER
        ]
        result = self.scoring.evaluate_hard_gates(gate_request(gates=gates))

        self.assert_failed_gate_result(result, code="evidence_missing", first_gate="grounding")

    def test_missing_required_gate_fails_closed(self) -> None:
        gates = [
            gate_evidence(name)
            for name in EXPECTED_HARD_GATE_ORDER
            if name != "output"
        ]
        result = self.scoring.evaluate_hard_gates(gate_request(gates=gates))

        self.assert_failed_gate_result(result, code="gate_missing", first_gate="output")

    def test_gate_order_must_be_exact_before_scoring(self) -> None:
        gates = [gate_evidence(name) for name in EXPECTED_HARD_GATE_ORDER]
        gates[0], gates[1] = gates[1], gates[0]
        result = self.scoring.evaluate_hard_gates(gate_request(gates=gates))

        self.assert_failed_gate_result(result, code="gate_order_invalid", first_gate="role")

    def test_gate_inputs_use_closed_names_shapes_and_digests(self) -> None:
        gates = [gate_evidence(name) for name in EXPECTED_HARD_GATE_ORDER]
        gates[0]["notes"] = "free-form gate notes are not allowed"
        with self.assertRaisesRegex(ValueError, "gate evidence must use its closed shape"):
            self.scoring.evaluate_hard_gates(gate_request(gates=gates))

        gates = [gate_evidence(name) for name in EXPECTED_HARD_GATE_ORDER]
        gates[0]["gate_name"] = "semantic"
        with self.assertRaisesRegex(ValueError, "closed hard gate"):
            self.scoring.evaluate_hard_gates(gate_request(gates=gates))

        gates = [gate_evidence(name) for name in EXPECTED_HARD_GATE_ORDER]
        gates[0]["evaluator_digest"] = "not-a-digest"
        with self.assertRaisesRegex(ValueError, "evaluator digest"):
            self.scoring.evaluate_hard_gates(gate_request(gates=gates))

    def test_score_before_gates_is_prohibited_even_for_plausible_pending_results(self) -> None:
        pending = {
            "schema_version": "hard-gates.v1",
            "gate_disposition": "pending_ballots",
            "failure_code": "none",
            "gates": [],
        }
        with self.assertRaisesRegex(ValueError, "deterministic hard gates must pass"):
            self.scoring.assert_semantic_scoring_allowed(pending)

    def test_two_distinct_blind_current_rubric_ballots_accept_without_adjudication(self) -> None:
        gate_result = self.scoring.evaluate_hard_gates(gate_request())
        request = semantic_request()
        original = copy.deepcopy(request)
        result = self.scoring.evaluate_blinded_ballots(gate_result, request)

        self.assertEqual(request, original, "ballot evaluation must not mutate caller data")
        self.assertEqual(set(result), EXPECTED_SEMANTIC_RESULT_FIELDS)
        self.assertEqual(result["schema_version"], self.scoring.SEMANTIC_BALLOT_SCHEMA_VERSION)
        self.assertEqual(result["gate_result_id"], gate_result["gate_result_id"])
        self.assertEqual(result["gate_result_digest"], gate_result["gate_result_digest"])
        self.assertEqual(result["score_disposition"], "accepted")
        self.assertEqual(result["failure_plane"], "none")
        self.assertEqual(result["failure_code"], "none")
        self.assertFalse(result["disagreement"])
        self.assertIsNone(result["adjudication"])
        self.assertEqual(result["resolved_outcome"], "accept")
        self.assertEqual(result["semantic_score"], 0.91)
        self.assertEqual(result["reliability_score"], 0.87)
        self.assertEqual(result["semantic_result_digest"], self.scoring.digest(semantic_digest_payload(result)))
        self.assertEqual(result["semantic_result_id"], self.scoring.content_id(result, "semantic_result_id"))
        self.assertEqual(len(result["ballots"]), 2)
        self.assertEqual({ballot["scorer_id"] for ballot in result["ballots"]}, {"opaque-scorer-a", "opaque-scorer-b"})
        self.assertEqual(
            {ballot["scorer_execution_id"] for ballot in result["ballots"]},
            {"g56r-003-scorer-execution-opaque-scorer-a", "g56r-003-scorer-execution-opaque-scorer-b"},
        )
        for ballot in result["ballots"]:
            self.assertEqual(set(ballot), EXPECTED_BALLOT_FIELDS)
            self.assertTrue(ballot["candidate_blind"])
            self.assertEqual(ballot["rubric_status"], "frozen")
            self.assertEqual(ballot["calibration_status"], "current")
            self.assertEqual(ballot["ballot_digest"], self.scoring.digest(ballot_digest_payload(ballot)))
            self.assertEqual(ballot["ballot_id"], self.scoring.content_id(ballot, "ballot_id"))

    def test_missing_stale_non_blind_and_duplicate_ballots_fail_closed(self) -> None:
        gate_result = self.scoring.evaluate_hard_gates(gate_request())
        cases = (
            (
                "missing second ballot",
                [scorer_ballot("opaque-scorer-a")],
                "ballot",
                "ballot_missing",
            ),
            (
                "non blind artifact",
                [scorer_ballot("opaque-scorer-a", candidate_blind=False), scorer_ballot("opaque-scorer-b")],
                "ballot",
                "ballot_non_blind",
            ),
            (
                "duplicate scorer identity",
                [
                    scorer_ballot("opaque-scorer-a"),
                    scorer_ballot("opaque-scorer-a", scorer_execution_id="distinct-execution"),
                ],
                "ballot",
                "ballot_provenance_incomplete",
            ),
            (
                "duplicate scorer execution",
                [
                    scorer_ballot("opaque-scorer-a", scorer_execution_id="shared-execution"),
                    scorer_ballot("opaque-scorer-b", scorer_execution_id="shared-execution"),
                ],
                "ballot",
                "ballot_provenance_incomplete",
            ),
            (
                "stale scorer",
                [scorer_ballot("opaque-scorer-a", scorer_status="stale"), scorer_ballot("opaque-scorer-b")],
                "scorer",
                "scorer_stale",
            ),
            (
                "stale calibration",
                [scorer_ballot("opaque-scorer-a", calibration_status="stale"), scorer_ballot("opaque-scorer-b")],
                "scorer",
                "scorer_calibration_missing",
            ),
            (
                "stale rubric",
                [scorer_ballot("opaque-scorer-a", rubric_status="draft"), scorer_ballot("opaque-scorer-b")],
                "ballot",
                "ballot_rubric_stale",
            ),
            (
                "rubric mismatch",
                [
                    scorer_ballot("opaque-scorer-a"),
                    scorer_ballot("opaque-scorer-b", rubric_digest_value=digest({"rubric": "changed"})),
                ],
                "ballot",
                "ballot_rubric_stale",
            ),
            (
                "missing ballot provenance",
                [scorer_ballot("opaque-scorer-a", provenance_refs=[]), scorer_ballot("opaque-scorer-b")],
                "ballot",
                "ballot_provenance_incomplete",
            ),
        )

        for label, ballots, plane, code in cases:
            with self.subTest(label=label):
                result = self.scoring.evaluate_blinded_ballots(gate_result, semantic_request(ballots=ballots))
                self.assert_failed_semantic_result(result, plane=plane, code=code)

    def test_decision_affecting_disagreement_requires_frozen_third_adjudicator(self) -> None:
        gate_result = self.scoring.evaluate_hard_gates(gate_request())
        ballots = [
            scorer_ballot("opaque-scorer-a", outcome="accept"),
            scorer_ballot("opaque-scorer-b", outcome="reject", semantic=0.72, reliability=0.74),
        ]

        unresolved = self.scoring.evaluate_blinded_ballots(gate_result, semantic_request(ballots=ballots))
        self.assert_failed_semantic_result(
            unresolved,
            plane="adjudication",
            code="adjudication_disagreement_unresolved",
        )
        self.assertTrue(unresolved["disagreement"])

        result = self.scoring.evaluate_blinded_ballots(
            gate_result,
            semantic_request(ballots=ballots, adjudication=adjudicator_record(resolved_outcome="accept")),
        )

        self.assertEqual(set(result), EXPECTED_SEMANTIC_RESULT_FIELDS)
        self.assertEqual(result["score_disposition"], "accepted")
        self.assertEqual(result["failure_plane"], "none")
        self.assertEqual(result["failure_code"], "none")
        self.assertTrue(result["disagreement"])
        self.assertEqual(result["resolved_outcome"], "accept")
        self.assertEqual(result["semantic_score"], 0.82)
        self.assertEqual(result["reliability_score"], 0.81)
        self.assertEqual(set(result["adjudication"]), EXPECTED_ADJUDICATION_FIELDS)
        self.assertEqual(result["adjudication"]["rubric_status"], "frozen")
        self.assertEqual(result["adjudication"]["adjudicator_status"], "current")
        self.assertEqual(result["adjudication"]["calibration_status"], "current")
        self.assertEqual(
            result["adjudication"]["ballot_bindings"],
            [
                {"id": result["ballots"][0]["ballot_id"], "digest": result["ballots"][0]["ballot_digest"]},
                {"id": result["ballots"][1]["ballot_id"], "digest": result["ballots"][1]["ballot_digest"]},
            ],
        )
        self.assertEqual(
            result["adjudication"]["adjudication_digest"],
            self.scoring.digest(adjudication_digest_payload(result["adjudication"])),
        )
        self.assertEqual(
            result["adjudication"]["adjudication_id"],
            self.scoring.content_id(result["adjudication"], "adjudication_id"),
        )

    def test_third_adjudicator_provenance_currentness_and_non_reuse_fail_closed(self) -> None:
        gate_result = self.scoring.evaluate_hard_gates(gate_request())
        ballots = [
            scorer_ballot("opaque-scorer-a", outcome="accept"),
            scorer_ballot("opaque-scorer-b", outcome="reject", semantic=0.72, reliability=0.74),
        ]
        cases = (
            (
                "missing adjudicator provenance",
                adjudicator_record(provenance_refs=[]),
                "adjudicator_invalid",
            ),
            (
                "stale adjudicator",
                adjudicator_record(adjudicator_status="stale"),
                "adjudicator_stale",
            ),
            (
                "stale adjudicator calibration",
                adjudicator_record(calibration_status="stale"),
                "adjudicator_stale",
            ),
            (
                "third adjudicator reuses primary scorer",
                adjudicator_record(adjudicator_id="opaque-scorer-a"),
                "adjudicator_reused_primary_scorer",
            ),
        )

        for label, adjudication, code in cases:
            with self.subTest(label=label):
                result = self.scoring.evaluate_blinded_ballots(
                    gate_result,
                    semantic_request(ballots=ballots, adjudication=adjudication),
                )
                self.assert_failed_semantic_result(result, plane="adjudication", code=code)


if __name__ == "__main__":
    unittest.main(verbosity=2)
