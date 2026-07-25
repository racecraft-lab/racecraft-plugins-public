#!/usr/bin/env python3
"""G56R-003 deterministic hard-gate evaluation for qualification scoring."""

from __future__ import annotations

import copy as _copy
import hashlib as _hashlib
import json as _json
import math as _math
import re as _re


HARD_GATE_SCHEMA_VERSION = "hard-gates.v1"
SCORER_EVIDENCE_SCHEMA_VERSION = "scorer-evidence.v1"
SEMANTIC_BALLOT_SCHEMA_VERSION = "semantic-ballots.v1"
SCORE_BUNDLE_SCHEMA_VERSION = "score-bundle.v1"
_CURRENT_SCORE_BUNDLE_VERSION = "1.0.0"
HARD_GATE_ORDER = (
    "role",
    "safety",
    "grounding",
    "mutation",
    "tool",
    "output",
    "acceptance",
)
GATE_DISPOSITIONS = ("passed", "failed")
GATE_FAILURE_CODES = ("none", "gate_failed", "gate_missing", "evidence_missing", "gate_order_invalid")
SCORE_DISPOSITIONS = ("accepted", "gate_failed", "non_scorable", "invalidated")
SCORE_FAILURE_PLANES = (
    "none",
    "gate",
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
SCORE_FAILURE_CODES = (
    "none",
    "gate_failed",
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
SCORE_INVALIDATION_REASONS = (
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
CANDIDATE_TERMINALS = {
    "failed": "candidate_failed",
    "timed_out": "candidate_timed_out",
    "cancelled": "candidate_cancelled",
    "budget_exhausted": "candidate_budget_exhausted",
    "abandoned": "candidate_abandoned",
}
FAILURE_CODE_PLANES = {
    "none": "none",
    "gate_failed": "gate",
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

_GATE_SET = frozenset(HARD_GATE_ORDER)
_DIGEST_RE = _re.compile(r"^sha256:[0-9a-f]{64}$")
_UTC_RE = _re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_ABSOLUTE_PATH_RE = _re.compile(r"(^|[\s:=])/(Users|home|private|var|tmp|etc|Volumes)/")
_REMOTE_RE = _re.compile(r"(?i)(https?://|ssh://|git@|[a-z0-9_.+-]+@[a-z0-9_.-]+)")
_PRIVATE_HOST_RE = _re.compile(r"(?i)(localhost|127\.0\.0\.1|\.local\b|internal[.-]|private[.-])")
_TOKEN_RE = _re.compile(r"(?i)(authorization:\s*bearer|bearer\s+[a-z0-9_.-]+|sk-[a-z0-9_-]+|sid=)")
_REQUEST_FIELDS = frozenset({
    "execution_trace_id",
    "trace_digest",
    "fixture_id",
    "fixture_digest",
    "gates",
})
_SEMANTIC_REQUEST_FIELDS = frozenset({
    "score_bundle_draft_id",
    "ballots",
    "adjudication",
})
_GATE_FIELDS = frozenset({
    "gate_name",
    "passed",
    "evidence_refs",
    "evaluator_version",
    "evaluator_digest",
})
_BALLOT_INPUT_FIELDS = frozenset({
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
})
_BALLOT_RESULT_FIELDS = _BALLOT_INPUT_FIELDS | frozenset({"ballot_id", "ballot_digest"})
_ADJUDICATION_INPUT_FIELDS = frozenset({
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
    "disagreement_rule",
    "resolved_outcome",
    "submitted_at",
    "provenance_refs",
})
_ADJUDICATION_RESULT_FIELDS = _ADJUDICATION_INPUT_FIELDS | frozenset({
    "adjudication_id",
    "adjudication_digest",
    "ballot_bindings",
})
_SCORE_BINDING_FIELDS = (
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
_SCORE_BUNDLE_REQUEST_FIELDS = frozenset({
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
    "gate_result",
    "semantic_result",
    "score_disposition",
    "failure_plane",
    "failure_code",
    "invalidation_reason",
    "invalidated_bundle_binding",
    "resource_vector",
    "evidence_refs",
})
_SCORE_BUNDLE_FIELDS = frozenset({
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
})
_RESOURCE_VECTOR_FIELDS = frozenset({
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "duration_ms",
    "retries",
    "compactions",
    "acceptance",
    "terminal_state",
})
_TERMINAL_STATES = frozenset({"completed", *CANDIDATE_TERMINALS, "unknown"})
_RESULT_FIELDS = frozenset({
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
})
_SEMANTIC_RESULT_FIELDS = frozenset({
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
})
_OUTCOMES = frozenset({"accept", "reject"})
_SCORE_KEYS = frozenset({"semantic", "reliability"})
_COMMITTED_SCORER_KEY_ALLOWLIST = (
    _SCORE_BUNDLE_FIELDS
    | _BALLOT_RESULT_FIELDS
    | _ADJUDICATION_RESULT_FIELDS
    | _RESOURCE_VECTOR_FIELDS
    | frozenset({
        "id",
        "digest",
        "gate",
        "pass",
        "evidence_digest",
        "semantic",
        "reliability",
    })
)
_SENSITIVE_KEY_FRAGMENTS = (
    "raw_prompt",
    "raw_response",
    "raw_transcript",
    "prompt",
    "response",
    "transcript",
    "personal",
    "mapping",
    "account",
    "auth",
    "credential",
    "access_token",
    "refresh_token",
    "auth_token",
    "api_key",
    "secret",
    "session",
    "cookie",
    "header",
    "private_host",
    "hostname",
    "host",
    "remote",
    "billing",
    "plan_id",
    "plan_identifier",
    "catalog_bytes",
)


def canonical_bytes(value: object) -> bytes:
    """Return the deterministic JSON byte representation for scoring records."""
    return _json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest(value: object) -> str:
    """Return a ``sha256:<hex>`` digest for bytes or canonical JSON values."""
    payload = value if isinstance(value, bytes) else canonical_bytes(value)
    return "sha256:" + _hashlib.sha256(payload).hexdigest()


def content_id(value: dict, identity_field: str) -> str:
    """Return a content-addressed ID while excluding the identity field itself."""
    return digest({key: item for key, item in value.items() if key != identity_field})


def _closed(value: object, keys: frozenset[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} must use its closed shape")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _digest(value: object, label: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a sha256 digest")
    return value


def _bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be boolean")
    return value


def _timestamp(value: object, label: str) -> str:
    if not isinstance(value, str) or _UTC_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be an RFC3339 UTC timestamp")
    return value


def _status(value: object, label: str) -> str:
    status = _text(value, label)
    if status not in {"current", "stale", "frozen", "draft"}:
        raise ValueError(f"{label} is outside the closed status inventory")
    return status


def _scores(value: object) -> dict:
    if not isinstance(value, dict) or set(value) != _SCORE_KEYS:
        raise ValueError("criterion scores must include semantic and reliability")
    result: dict[str, float] = {}
    for key in ("semantic", "reliability"):
        score = value[key]
        if (
            not isinstance(score, (int, float))
            or isinstance(score, bool)
            or not _math.isfinite(score)
            or not 0.0 <= float(score) <= 1.0
        ):
            raise ValueError("criterion scores must be finite values from zero to one")
        result[key] = float(score)
    return result


def _digest_refs(value: object, label: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    result = [_digest(item, label) for item in value]
    if len(result) != len(set(result)):
        raise ValueError(f"{label} must contain unique digests")
    return result


def _key_path(path: tuple[str, ...]) -> str:
    return ".".join(path) if path else "<root>"


def _sensitive_key(key: object) -> bool:
    normalized = str(key).replace("-", "_").lower()
    return any(fragment in normalized for fragment in _SENSITIVE_KEY_FRAGMENTS)


def _sensitive_string(value: str) -> bool:
    return (
        _ABSOLUTE_PATH_RE.search(value) is not None
        or _REMOTE_RE.search(value) is not None
        or _PRIVATE_HOST_RE.search(value) is not None
        or _TOKEN_RE.search(value) is not None
    )


def _opaque_id(value: str) -> bool:
    return value.startswith("opaque-") and not _sensitive_string(value)


def _scan_committed_scorer_evidence(value: object, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"unknown committed evidence key at {_key_path(path)}")
            child_path = (*path, key)
            if _sensitive_key(key):
                raise ValueError(f"sensitive evidence is not allowed at {_key_path(child_path)}")
            if key not in _COMMITTED_SCORER_KEY_ALLOWLIST:
                raise ValueError(f"unknown committed evidence key at {_key_path(child_path)}")
            _scan_committed_scorer_evidence(item, child_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _scan_committed_scorer_evidence(item, (*path, str(index)))
        return
    if isinstance(value, str) and _sensitive_string(value):
        raise ValueError(f"sensitive evidence is not allowed at {_key_path(path)}")


def _validate_gate(value: object) -> dict:
    row = _closed(_copy.deepcopy(value), _GATE_FIELDS, "gate evidence")
    gate_name = _text(row["gate_name"], "gate name")
    if gate_name not in _GATE_SET:
        raise ValueError("gate name must be a closed hard gate")
    result = {
        "gate_name": gate_name,
        "passed": _bool(row["passed"], "gate pass marker"),
        "evidence_refs": _digest_refs(row["evidence_refs"], "gate evidence refs"),
        "evaluator_version": _text(row["evaluator_version"], "evaluator version"),
        "evaluator_digest": _digest(row["evaluator_digest"], "evaluator digest"),
    }
    return result


def _request(value: object) -> dict:
    row = _closed(_copy.deepcopy(value), _REQUEST_FIELDS, "hard gate request")
    _digest(row["execution_trace_id"], "execution trace ID")
    _digest(row["trace_digest"], "trace digest")
    _text(row["fixture_id"], "fixture ID")
    _digest(row["fixture_digest"], "fixture digest")
    if not isinstance(row["gates"], list):
        raise ValueError("hard gates must be an array")
    row["gates"] = [_validate_gate(gate) for gate in row["gates"]]
    return row


def _first_missing_gate(gate_names: list[str]) -> str:
    present = set(gate_names)
    for gate_name in HARD_GATE_ORDER:
        if gate_name not in present:
            return gate_name
    return HARD_GATE_ORDER[0]


def _first_order_mismatch(gate_names: list[str]) -> str:
    for expected, observed in zip(HARD_GATE_ORDER, gate_names):
        if expected != observed:
            return expected
    return HARD_GATE_ORDER[0]


def _result_digest_payload(result: dict) -> dict:
    return {
        key: value
        for key, value in result.items()
        if key not in {"gate_result_id", "gate_result_digest"}
    }


def _replay_request(result: dict) -> dict:
    return {
        "execution_trace_id": result["execution_trace_id"],
        "trace_digest": result["trace_digest"],
        "fixture_id": result["fixture_id"],
        "fixture_digest": result["fixture_digest"],
        "gates": result["gates"],
    }


def _semantic_digest_payload(result: dict) -> dict:
    return {
        key: value
        for key, value in result.items()
        if key not in {"semantic_result_id", "semantic_result_digest"}
    }


def _ballot_digest_payload(ballot: dict) -> dict:
    return {
        key: value
        for key, value in ballot.items()
        if key not in {"ballot_id", "ballot_digest"}
    }


def _adjudication_digest_payload(adjudication: dict) -> dict:
    return {
        key: value
        for key, value in adjudication.items()
        if key not in {"adjudication_id", "adjudication_digest"}
    }


def _binding(value_id: str, value_digest: str) -> dict:
    return {"id": value_id, "digest": value_digest}


def _binding_record(value: object, label: str) -> dict:
    row = _closed(_copy.deepcopy(value), frozenset({"id", "digest"}), f"{label} binding")
    return {
        "id": _text(row["id"], f"{label} binding ID"),
        "digest": _digest(row["digest"], f"{label} binding digest"),
    }


def _nullable_binding(value: object, label: str) -> dict | None:
    if value is None:
        return None
    return _binding_record(value, label)


def _integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _nullable_number(value: object, label: str) -> float | None:
    if value is None:
        return None
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not _math.isfinite(value)
    ):
        raise ValueError(f"{label} must be numeric or null")
    return float(value)


def _nullable_unit_interval(value: object, label: str) -> float | None:
    result = _nullable_number(value, label)
    if result is not None and not 0.0 <= result <= 1.0:
        raise ValueError(f"{label} must be a value from zero to one or null")
    return result


def _resource_vector(value: object) -> dict:
    row = _closed(_copy.deepcopy(value), _RESOURCE_VECTOR_FIELDS, "resource vector")
    terminal_state = _text(row["terminal_state"], "terminal state")
    if terminal_state not in _TERMINAL_STATES:
        raise ValueError("terminal state is outside the closed inventory")
    return {
        "input_tokens": _integer(row["input_tokens"], "input tokens"),
        "cached_input_tokens": _integer(row["cached_input_tokens"], "cached input tokens"),
        "output_tokens": _integer(row["output_tokens"], "output tokens"),
        "duration_ms": _integer(row["duration_ms"], "duration ms"),
        "retries": _integer(row["retries"], "retries"),
        "compactions": _integer(row["compactions"], "compactions"),
        "acceptance": _nullable_unit_interval(row["acceptance"], "acceptance"),
        "terminal_state": terminal_state,
    }
    return result


def _score_bundle_digest_payload(bundle: dict) -> dict:
    return {
        key: value
        for key, value in bundle.items()
        if key not in {"score_bundle_id", "score_bundle_digest"}
    }


def _failure_plane_for_code(failure_code: str) -> str:
    if failure_code not in FAILURE_CODE_PLANES:
        raise ValueError("failure code is outside the closed inventory")
    return FAILURE_CODE_PLANES[failure_code]


def _validate_score_classification(
    *,
    score_disposition: str,
    failure_plane: str,
    failure_code: str,
    invalidation_reason: str,
    invalidated_bundle_binding: dict | None,
    vector: dict,
) -> None:
    if score_disposition not in SCORE_DISPOSITIONS:
        raise ValueError("score disposition is outside the closed inventory")
    if failure_plane not in SCORE_FAILURE_PLANES:
        raise ValueError("failure plane is outside the closed inventory")
    if failure_code not in SCORE_FAILURE_CODES:
        raise ValueError("failure code is outside the closed inventory")
    if invalidation_reason not in SCORE_INVALIDATION_REASONS:
        raise ValueError("invalidation reason is outside the closed inventory")

    expected_plane = _failure_plane_for_code(failure_code)
    if failure_code == "none" and failure_plane != "none":
        raise ValueError("failure code none is only valid with failure plane none")
    if failure_plane == "none" and failure_code != "none":
        raise ValueError("failure code must be none when failure plane is none")
    if expected_plane != failure_plane:
        raise ValueError("failure plane does not match failure code")

    if score_disposition == "invalidated":
        if invalidation_reason == "none":
            raise ValueError("invalidation reason is required for invalidated score bundles")
        if invalidated_bundle_binding is None:
            raise ValueError("invalidated bundle binding is required")
    else:
        if invalidation_reason != "none":
            raise ValueError("invalidation reason must be none unless the bundle is invalidated")
        if invalidated_bundle_binding is not None:
            raise ValueError("invalidated bundle binding is allowed only for invalidated bundles")

    if score_disposition == "accepted" and failure_plane not in {"none", "candidate"}:
        raise ValueError("accepted score bundles cannot carry non-candidate failures")
    if score_disposition == "gate_failed":
        if failure_plane in {"none", "candidate"} or failure_code == "none":
            raise ValueError("gate-failed score bundles require a non-candidate failure")
    if score_disposition == "non_scorable":
        if failure_plane in {"none", "candidate"} or failure_code == "none":
            raise ValueError("non-scorable score bundles require a non-candidate failure")
    if failure_code == "none" and score_disposition not in {"accepted", "invalidated"}:
        raise ValueError("failure-free score bundles must be accepted or invalidated")

    terminal_state = vector["terminal_state"]
    if failure_plane == "candidate":
        if CANDIDATE_TERMINALS.get(terminal_state) != failure_code:
            raise ValueError("candidate terminal state does not match failure code")
        if score_disposition != "accepted":
            raise ValueError("candidate terminal outcomes remain accepted estimand records")
        if vector["acceptance"] != 0.0:
            raise ValueError("candidate terminal outcomes must record acceptance zero")
    if failure_code == "unclassifiable_attrition":
        if score_disposition != "non_scorable":
            raise ValueError("unclassifiable attrition must be non-scorable")
        if terminal_state != "unknown":
            raise ValueError("unclassifiable attrition must use unknown terminal state")
    if failure_code == "none" and score_disposition == "accepted" and terminal_state != "completed":
        raise ValueError("accepted score bundles without failure must be completed")


def _build_result(
    request: dict,
    *,
    gate_disposition: str,
    failure_code: str,
    first_failed_gate: str | None,
) -> dict:
    result = {
        "schema_version": HARD_GATE_SCHEMA_VERSION,
        "execution_trace_id": request["execution_trace_id"],
        "trace_digest": request["trace_digest"],
        "fixture_id": request["fixture_id"],
        "fixture_digest": request["fixture_digest"],
        "gate_disposition": gate_disposition,
        "failure_code": failure_code,
        "first_failed_gate": first_failed_gate,
        "gates": _copy.deepcopy(request["gates"]),
    }
    result["gate_result_digest"] = digest(_result_digest_payload(result))
    result["gate_result_id"] = content_id(result, "gate_result_id")
    return result


def _build_semantic_result(
    gate_result: dict,
    *,
    score_bundle_draft_id: str,
    score_disposition: str,
    failure_plane: str,
    failure_code: str,
    ballots: list[dict],
    adjudication: dict | None,
    resolved_outcome: str | None,
    semantic_score: float | None,
    reliability_score: float | None,
    disagreement: bool,
) -> dict:
    result = {
        "schema_version": SEMANTIC_BALLOT_SCHEMA_VERSION,
        "gate_result_id": gate_result["gate_result_id"],
        "gate_result_digest": gate_result["gate_result_digest"],
        "score_bundle_draft_id": score_bundle_draft_id,
        "score_disposition": score_disposition,
        "failure_plane": failure_plane,
        "failure_code": failure_code,
        "ballots": _copy.deepcopy(ballots),
        "adjudication": _copy.deepcopy(adjudication),
        "resolved_outcome": resolved_outcome,
        "semantic_score": semantic_score,
        "reliability_score": reliability_score,
        "disagreement": disagreement,
    }
    result["semantic_result_digest"] = digest(_semantic_digest_payload(result))
    result["semantic_result_id"] = content_id(result, "semantic_result_id")
    return result


def _semantic_request(value: object) -> dict:
    row = _closed(_copy.deepcopy(value), _SEMANTIC_REQUEST_FIELDS, "semantic ballot request")
    row["score_bundle_draft_id"] = _text(row["score_bundle_draft_id"], "score bundle draft ID")
    if not isinstance(row["ballots"], list):
        raise ValueError("semantic ballots must be an array")
    if row["adjudication"] is not None and not isinstance(row["adjudication"], dict):
        raise ValueError("adjudication must be an object or null")
    return row


def _ballot_record(value: object) -> dict:
    row = _closed(_copy.deepcopy(value), _BALLOT_INPUT_FIELDS, "semantic ballot")
    record = {
        "blinded_artifact_digest": _digest(row["blinded_artifact_digest"], "blinded artifact digest"),
        "candidate_blind": _bool(row["candidate_blind"], "candidate-blind marker"),
        "scorer_id": _text(row["scorer_id"], "scorer ID"),
        "scorer_status": _status(row["scorer_status"], "scorer status"),
        "scorer_digest": _digest(row["scorer_digest"], "scorer digest"),
        "scorer_execution_id": _text(row["scorer_execution_id"], "scorer execution ID"),
        "scorer_execution_digest": _digest(row["scorer_execution_digest"], "scorer execution digest"),
        "calibration_id": _text(row["calibration_id"], "scorer calibration ID"),
        "calibration_digest": _digest(row["calibration_digest"], "scorer calibration digest"),
        "calibration_status": _status(row["calibration_status"], "scorer calibration status"),
        "rubric_id": _text(row["rubric_id"], "rubric ID"),
        "rubric_version": _text(row["rubric_version"], "rubric version"),
        "rubric_digest": _digest(row["rubric_digest"], "rubric digest"),
        "rubric_status": _status(row["rubric_status"], "rubric status"),
        "criterion_scores": _scores(row["criterion_scores"]),
        "outcome": _text(row["outcome"], "ballot outcome"),
        "submitted_at": _timestamp(row["submitted_at"], "ballot submission timestamp"),
        "provenance_refs": _digest_refs(row["provenance_refs"], "ballot provenance refs"),
    }
    if record["outcome"] not in _OUTCOMES:
        raise ValueError("ballot outcome is outside the closed inventory")
    record["ballot_digest"] = digest(_ballot_digest_payload(record))
    record["ballot_id"] = content_id(record, "ballot_id")
    return record


def _adjudication_record(value: object, *, ballots: list[dict]) -> dict:
    row = _closed(_copy.deepcopy(value), _ADJUDICATION_INPUT_FIELDS, "adjudication")
    record = {
        "adjudicator_id": _text(row["adjudicator_id"], "adjudicator ID"),
        "adjudicator_status": _status(row["adjudicator_status"], "adjudicator status"),
        "adjudicator_digest": _digest(row["adjudicator_digest"], "adjudicator digest"),
        "adjudicator_execution_id": _text(row["adjudicator_execution_id"], "adjudicator execution ID"),
        "adjudicator_execution_digest": _digest(row["adjudicator_execution_digest"], "adjudicator execution digest"),
        "calibration_id": _text(row["calibration_id"], "adjudicator calibration ID"),
        "calibration_digest": _digest(row["calibration_digest"], "adjudicator calibration digest"),
        "calibration_status": _status(row["calibration_status"], "adjudicator calibration status"),
        "rubric_id": _text(row["rubric_id"], "adjudicator rubric ID"),
        "rubric_version": _text(row["rubric_version"], "adjudicator rubric version"),
        "rubric_digest": _digest(row["rubric_digest"], "adjudicator rubric digest"),
        "rubric_status": _status(row["rubric_status"], "adjudicator rubric status"),
        "ballot_bindings": [_binding(ballot["ballot_id"], ballot["ballot_digest"]) for ballot in ballots],
        "disagreement_rule": _text(row["disagreement_rule"], "adjudication disagreement rule"),
        "resolved_outcome": _text(row["resolved_outcome"], "adjudication resolved outcome"),
        "submitted_at": _timestamp(row["submitted_at"], "adjudication submission timestamp"),
        "provenance_refs": _digest_refs(row["provenance_refs"], "adjudication provenance refs"),
    }
    if record["resolved_outcome"] not in _OUTCOMES:
        raise ValueError("adjudication outcome is outside the closed inventory")
    record["adjudication_digest"] = digest(_adjudication_digest_payload(record))
    record["adjudication_id"] = content_id(record, "adjudication_id")
    return record


def _rubric_binding(row: dict) -> tuple[str, str, str]:
    return (row["rubric_id"], row["rubric_version"], row["rubric_digest"])


def _semantic_failure(
    gate_result: dict,
    request: dict,
    *,
    failure_code: str,
    ballots: list[dict],
    adjudication: dict | None = None,
    disagreement: bool = False,
) -> dict:
    return _build_semantic_result(
        gate_result,
        score_bundle_draft_id=request["score_bundle_draft_id"],
        score_disposition="non_scorable",
        failure_plane=_failure_plane_for_code(failure_code),
        failure_code=failure_code,
        ballots=ballots,
        adjudication=adjudication,
        resolved_outcome=None,
        semantic_score=None,
        reliability_score=None,
        disagreement=disagreement,
    )


def evaluate_hard_gates(value: object) -> dict:
    """Evaluate the seven required deterministic hard gates in frozen order."""
    request = _request(value)
    gate_names = [gate["gate_name"] for gate in request["gates"]]
    if len(gate_names) != len(HARD_GATE_ORDER) or set(gate_names) != _GATE_SET:
        return _build_result(
            request,
            gate_disposition="failed",
            failure_code="gate_missing",
            first_failed_gate=_first_missing_gate(gate_names),
        )
    if tuple(gate_names) != HARD_GATE_ORDER:
        return _build_result(
            request,
            gate_disposition="failed",
            failure_code="gate_order_invalid",
            first_failed_gate=_first_order_mismatch(gate_names),
        )
    for gate in request["gates"]:
        if not gate["evidence_refs"]:
            return _build_result(
                request,
                gate_disposition="failed",
                failure_code="evidence_missing",
                first_failed_gate=gate["gate_name"],
            )
    for gate in request["gates"]:
        if gate["passed"] is not True:
            return _build_result(
                request,
                gate_disposition="failed",
                failure_code="gate_failed",
                first_failed_gate=gate["gate_name"],
            )
    return _build_result(
        request,
        gate_disposition="passed",
        failure_code="none",
        first_failed_gate=None,
    )


def _validated_gate_result(gate_result: object) -> dict:
    result = _closed(_copy.deepcopy(gate_result), _RESULT_FIELDS, "hard gate result")
    if result["schema_version"] != HARD_GATE_SCHEMA_VERSION:
        raise ValueError("hard gate schema version is unsupported")
    _digest(result["gate_result_id"], "gate result ID")
    _digest(result["gate_result_digest"], "gate result digest")
    _digest(result["execution_trace_id"], "execution trace ID")
    _digest(result["trace_digest"], "trace digest")
    _text(result["fixture_id"], "fixture ID")
    _digest(result["fixture_digest"], "fixture digest")
    if result["gate_disposition"] not in GATE_DISPOSITIONS:
        raise ValueError("gate disposition is outside the closed inventory")
    if result["failure_code"] not in GATE_FAILURE_CODES:
        raise ValueError("gate failure code is outside the closed inventory")
    if result["first_failed_gate"] is not None and result["first_failed_gate"] not in _GATE_SET:
        raise ValueError("first failed gate is outside the closed inventory")
    if not isinstance(result["gates"], list):
        raise ValueError("hard gates must be an array")
    validated = evaluate_hard_gates(_replay_request(result))
    if result["gate_result_digest"] != digest(_result_digest_payload(result)):
        raise ValueError("gate result digest does not match content")
    if result["gate_result_id"] != content_id(result, "gate_result_id"):
        raise ValueError("gate result ID does not match content")
    if result != validated:
        raise ValueError("hard gate result does not replay from gate evidence")
    return result


def assert_semantic_scoring_allowed(gate_result: object) -> dict:
    """Return a validated gate result only after deterministic gates pass."""
    try:
        result = _validated_gate_result(gate_result)
        if result["gate_disposition"] != "passed" or result["failure_code"] != "none":
            raise ValueError("hard gates failed")
        return result
    except ValueError as exc:
        raise ValueError("deterministic hard gates must pass before semantic scoring") from exc


def evaluate_blinded_ballots(gate_result: object, value: object) -> dict:
    """Validate two blinded semantic ballots and adjudicate disagreements."""
    gate = assert_semantic_scoring_allowed(gate_result)
    request = _semantic_request(value)
    ballot_values = request["ballots"]
    try:
        ballots = [_ballot_record(ballot) for ballot in ballot_values]
    except ValueError:
        ballots = []
        return _semantic_failure(
            gate,
            request,
            failure_code="schema_invalid",
            ballots=ballots,
        )
    if len(ballots) != 2:
        return _semantic_failure(
            gate,
            request,
            failure_code="ballot_missing",
            ballots=ballots,
        )
    if any(ballot["candidate_blind"] is not True for ballot in ballots):
        return _semantic_failure(
            gate,
            request,
            failure_code="ballot_non_blind",
            ballots=ballots,
        )
    if any(not ballot["provenance_refs"] for ballot in ballots):
        return _semantic_failure(
            gate,
            request,
            failure_code="ballot_provenance_incomplete",
            ballots=ballots,
        )
    if len({ballot["scorer_id"] for ballot in ballots}) != 2:
        return _semantic_failure(
            gate,
            request,
            failure_code="ballot_provenance_incomplete",
            ballots=ballots,
        )
    if len({ballot["scorer_execution_id"] for ballot in ballots}) != 2:
        return _semantic_failure(
            gate,
            request,
            failure_code="ballot_provenance_incomplete",
            ballots=ballots,
        )
    if any(not _opaque_id(ballot["scorer_id"]) for ballot in ballots):
        return _semantic_failure(gate, request, failure_code="scorer_invalid", ballots=ballots)
    if any(ballot["scorer_status"] != "current" for ballot in ballots):
        return _semantic_failure(gate, request, failure_code="scorer_stale", ballots=ballots)
    if any(ballot["calibration_status"] != "current" for ballot in ballots):
        return _semantic_failure(
            gate,
            request,
            failure_code="scorer_calibration_missing",
            ballots=ballots,
        )
    if (
        any(ballot["rubric_status"] != "frozen" for ballot in ballots)
        or _rubric_binding(ballots[0]) != _rubric_binding(ballots[1])
    ):
        return _semantic_failure(
            gate,
            request,
            failure_code="ballot_rubric_stale",
            ballots=ballots,
        )

    disagreement = ballots[0]["outcome"] != ballots[1]["outcome"]
    adjudication = None
    resolved_outcome = ballots[0]["outcome"]
    if disagreement:
        if request["adjudication"] is None:
            return _semantic_failure(
                gate,
                request,
                failure_code="adjudication_disagreement_unresolved",
                ballots=ballots,
                disagreement=True,
            )
        try:
            adjudication = _adjudication_record(request["adjudication"], ballots=ballots)
        except ValueError:
            return _semantic_failure(
                gate,
                request,
                failure_code="adjudicator_invalid",
                ballots=ballots,
                disagreement=True,
            )
        if not adjudication["provenance_refs"]:
            return _semantic_failure(
                gate,
                request,
                failure_code="adjudicator_invalid",
                ballots=ballots,
                adjudication=adjudication,
                disagreement=True,
            )
        if not _opaque_id(adjudication["adjudicator_id"]):
            return _semantic_failure(
                gate,
                request,
                failure_code="adjudicator_invalid",
                ballots=ballots,
                adjudication=adjudication,
                disagreement=True,
            )
        if adjudication["adjudicator_id"] in {ballot["scorer_id"] for ballot in ballots}:
            return _semantic_failure(
                gate,
                request,
                failure_code="adjudicator_reused_primary_scorer",
                ballots=ballots,
                adjudication=adjudication,
                disagreement=True,
            )
        if adjudication["adjudicator_execution_id"] in {ballot["scorer_execution_id"] for ballot in ballots}:
            return _semantic_failure(
                gate,
                request,
                failure_code="adjudicator_reused_primary_scorer",
                ballots=ballots,
                adjudication=adjudication,
                disagreement=True,
            )
        if adjudication["adjudicator_status"] != "current" or adjudication["calibration_status"] != "current":
            return _semantic_failure(
                gate,
                request,
                failure_code="adjudicator_stale",
                ballots=ballots,
                adjudication=adjudication,
                disagreement=True,
            )
        if adjudication["rubric_status"] != "frozen" or _rubric_binding(adjudication) != _rubric_binding(ballots[0]):
            return _semantic_failure(
                gate,
                request,
                failure_code="adjudicator_stale",
                ballots=ballots,
                adjudication=adjudication,
                disagreement=True,
            )
        resolved_outcome = adjudication["resolved_outcome"]

    return _build_semantic_result(
        gate,
        score_bundle_draft_id=request["score_bundle_draft_id"],
        score_disposition="accepted",
        failure_plane="none",
        failure_code="none",
        ballots=ballots,
        adjudication=adjudication,
        resolved_outcome=resolved_outcome,
        semantic_score=round(sum(ballot["criterion_scores"]["semantic"] for ballot in ballots) / 2, 6),
        reliability_score=round(sum(ballot["criterion_scores"]["reliability"] for ballot in ballots) / 2, 6),
        disagreement=disagreement,
    )


def _semantic_result_record(value: object, *, gate_result: dict | None = None) -> dict | None:
    if value is None:
        return None
    result = _closed(_copy.deepcopy(value), _SEMANTIC_RESULT_FIELDS, "semantic result")
    if result["schema_version"] != SEMANTIC_BALLOT_SCHEMA_VERSION:
        raise ValueError("semantic result schema version is unsupported")
    _digest(result["semantic_result_id"], "semantic result ID")
    _digest(result["semantic_result_digest"], "semantic result digest")
    _digest(result["gate_result_id"], "semantic gate result ID")
    _digest(result["gate_result_digest"], "semantic gate result digest")
    _text(result["score_bundle_draft_id"], "score bundle draft ID")
    if result["score_disposition"] not in SCORE_DISPOSITIONS:
        raise ValueError("semantic result score disposition is outside the closed inventory")
    if result["failure_plane"] not in SCORE_FAILURE_PLANES:
        raise ValueError("semantic result failure plane is outside the closed inventory")
    if result["failure_code"] not in SCORE_FAILURE_CODES:
        raise ValueError("semantic result failure code is outside the closed inventory")
    if not isinstance(result["ballots"], list):
        raise ValueError("semantic result ballots must be an array")
    ballots = [_closed(ballot, _BALLOT_RESULT_FIELDS, "semantic result ballot") for ballot in result["ballots"]]
    for ballot in ballots:
        if ballot["ballot_digest"] != digest(_ballot_digest_payload(ballot)):
            raise ValueError("ballot digest does not match content")
        if ballot["ballot_id"] != content_id(ballot, "ballot_id"):
            raise ValueError("ballot ID does not match content")
    adjudication = result["adjudication"]
    if adjudication is not None:
        adjudication = _closed(adjudication, _ADJUDICATION_RESULT_FIELDS, "semantic adjudication")
        if adjudication["adjudication_digest"] != digest(_adjudication_digest_payload(adjudication)):
            raise ValueError("adjudication digest does not match content")
        if adjudication["adjudication_id"] != content_id(adjudication, "adjudication_id"):
            raise ValueError("adjudication ID does not match content")
    if result["semantic_result_digest"] != digest(_semantic_digest_payload(result)):
        raise ValueError("semantic result digest does not match content")
    if result["semantic_result_id"] != content_id(result, "semantic_result_id"):
        raise ValueError("semantic result ID does not match content")
    if gate_result is not None:
        replay_request = {
            "score_bundle_draft_id": result["score_bundle_draft_id"],
            "ballots": [
                {field: ballot[field] for field in _BALLOT_INPUT_FIELDS}
                for ballot in ballots
            ],
            "adjudication": (
                None
                if adjudication is None
                else {
                    field: adjudication[field]
                    for field in _ADJUDICATION_INPUT_FIELDS
                }
            ),
        }
        replayed = evaluate_blinded_ballots(gate_result, replay_request)
        if result != replayed:
            if replayed["failure_code"] == "ballot_non_blind":
                raise ValueError("semantic result replays from non-blind ballot evidence")
            raise ValueError("semantic result does not replay from ballot evidence")
    return result


def _require_binding_match(binding: dict, expected_id: str, expected_digest: str, label: str) -> None:
    if binding != {"id": expected_id, "digest": expected_digest}:
        raise ValueError(f"{label} does not match bound evidence")


def _deterministic_gate_rows(gate_result: dict) -> list[dict]:
    return [
        {
            "gate": gate["gate_name"],
            "pass": gate["passed"],
            "evidence_digest": digest(gate["evidence_refs"]),
        }
        for gate in gate_result["gates"]
    ]


def _validated_gate_row(value: object) -> dict:
    row = _closed(_copy.deepcopy(value), frozenset({"gate", "pass", "evidence_digest"}), "score bundle gate")
    gate = _text(row["gate"], "score bundle gate")
    if gate not in _GATE_SET:
        raise ValueError("score bundle gate is outside the closed inventory")
    return {
        "gate": gate,
        "pass": _bool(row["pass"], "score bundle gate pass marker"),
        "evidence_digest": _digest(row["evidence_digest"], "score bundle gate evidence digest"),
    }


def _score_bundle_request(value: object) -> dict:
    if isinstance(value, dict) and any(key in value for key in ("execution_trace", "trace", "trace_record")):
        raise ValueError("embedded trace documents are not allowed in score bundles")
    request = _closed(_copy.deepcopy(value), _SCORE_BUNDLE_REQUEST_FIELDS, "score bundle request")
    gate_result = _validated_gate_result(request["gate_result"])
    semantic_result = _semantic_result_record(
        request["semantic_result"],
        gate_result=gate_result,
    )
    bindings = {
        field: _binding_record(request[field], field.replace("_", " "))
        for field in _SCORE_BINDING_FIELDS
    }
    _require_binding_match(
        bindings["execution_trace_binding"],
        gate_result["execution_trace_id"],
        gate_result["trace_digest"],
        "execution trace binding",
    )
    _require_binding_match(
        bindings["fixture_binding"],
        gate_result["fixture_id"],
        gate_result["fixture_digest"],
        "fixture binding",
    )
    _require_binding_match(
        bindings["gate_result_binding"],
        gate_result["gate_result_id"],
        gate_result["gate_result_digest"],
        "gate result binding",
    )
    if semantic_result is not None:
        _require_binding_match(
            bindings["gate_result_binding"],
            semantic_result["gate_result_id"],
            semantic_result["gate_result_digest"],
            "semantic gate result binding",
        )
        if semantic_result["ballots"]:
            first_ballot = semantic_result["ballots"][0]
            _require_binding_match(
                bindings["rubric_binding"],
                first_ballot["rubric_id"],
                first_ballot["rubric_digest"],
                "rubric binding",
            )
    vector = _resource_vector(request["resource_vector"])
    invalidated_bundle_binding = _nullable_binding(
        request["invalidated_bundle_binding"],
        "invalidated bundle",
    )
    score_disposition = _text(request["score_disposition"], "score disposition")
    failure_plane = _text(request["failure_plane"], "failure plane")
    failure_code = _text(request["failure_code"], "failure code")
    invalidation_reason = _text(request["invalidation_reason"], "invalidation reason")
    _validate_score_classification(
        score_disposition=score_disposition,
        failure_plane=failure_plane,
        failure_code=failure_code,
        invalidation_reason=invalidation_reason,
        invalidated_bundle_binding=invalidated_bundle_binding,
        vector=vector,
    )
    if score_disposition == "gate_failed":
        if gate_result["gate_disposition"] != "failed" or request["semantic_result"] is not None:
            raise ValueError("gate-failed score bundles require failed gates and no semantic result")
    elif gate_result["gate_disposition"] != "passed":
        raise ValueError("deterministic hard gates must pass before semantic scoring")
    score_bundle_version = _text(request["score_bundle_version"], "score bundle version")
    if score_bundle_version != _CURRENT_SCORE_BUNDLE_VERSION:
        raise ValueError("stale score bundle version is not committed directly")
    if failure_code == "none" and semantic_result is None:
        raise ValueError("semantic result is required when score failure code is none")
    return {
        "score_bundle_version": score_bundle_version,
        **bindings,
        "gate_result": gate_result,
        "semantic_result": semantic_result,
        "score_disposition": score_disposition,
        "failure_plane": failure_plane,
        "failure_code": failure_code,
        "invalidation_reason": invalidation_reason,
        "invalidated_bundle_binding": invalidated_bundle_binding,
        "resource_vector": vector,
        "evidence_refs": _digest_refs(request["evidence_refs"], "score bundle evidence refs"),
    }


def build_score_bundle(value: object) -> dict:
    """Build an immutable sanitized score bundle from validated scoring evidence."""
    request = _score_bundle_request(value)
    semantic_result = request["semantic_result"]
    ballots = _copy.deepcopy(semantic_result["ballots"]) if semantic_result is not None else []
    adjudication = _copy.deepcopy(semantic_result["adjudication"]) if semantic_result is not None else None
    ballot_bindings = [_binding(ballot["ballot_id"], ballot["ballot_digest"]) for ballot in ballots]
    scorer_bindings = [_binding(ballot["scorer_id"], ballot["scorer_digest"]) for ballot in ballots]
    adjudication_binding = (
        _binding(adjudication["adjudication_id"], adjudication["adjudication_digest"])
        if adjudication is not None
        else None
    )
    bundle = {
        "schema_version": SCORE_BUNDLE_SCHEMA_VERSION,
        "score_bundle_version": request["score_bundle_version"],
        "partition_binding": request["partition_binding"],
        "assignment_binding": request["assignment_binding"],
        "execution_trace_binding": request["execution_trace_binding"],
        "candidate_route_binding": request["candidate_route_binding"],
        "agent_contract_binding": request["agent_contract_binding"],
        "runtime_snapshot_binding": request["runtime_snapshot_binding"],
        "candidate_freeze_binding": request["candidate_freeze_binding"],
        "route_resolution_binding": request["route_resolution_binding"],
        "experiment_policy_binding": request["experiment_policy_binding"],
        "treatment_contract_binding": request["treatment_contract_binding"],
        "telemetry_profile_binding": request["telemetry_profile_binding"],
        "fixture_binding": request["fixture_binding"],
        "gate_result_binding": request["gate_result_binding"],
        "rubric_binding": request["rubric_binding"],
        "scorer_bindings": scorer_bindings,
        "ballot_bindings": ballot_bindings,
        "adjudication_binding": adjudication_binding,
        "deterministic_gates": _deterministic_gate_rows(request["gate_result"]),
        "ballots": ballots,
        "adjudication": adjudication,
        "score_disposition": request["score_disposition"],
        "failure_plane": request["failure_plane"],
        "failure_code": request["failure_code"],
        "invalidation_reason": request["invalidation_reason"],
        "invalidated_bundle_binding": request["invalidated_bundle_binding"],
        "semantic_score": (
            semantic_result["semantic_score"]
            if semantic_result is not None and request["failure_plane"] == "none"
            else None
        ),
        "reliability_score": (
            semantic_result["reliability_score"]
            if semantic_result is not None and request["failure_plane"] == "none"
            else None
        ),
        "resource_vector": request["resource_vector"],
        "evidence_refs": request["evidence_refs"],
    }
    bundle["score_bundle_digest"] = digest(_score_bundle_digest_payload(bundle))
    bundle["score_bundle_id"] = content_id(bundle, "score_bundle_id")
    _scan_committed_scorer_evidence(bundle)
    return validate_score_bundle(bundle)


def sanitize_committed_scorer_evidence(value: object) -> dict:
    """Validate committed scorer evidence against the sanitized allowlist."""
    if not isinstance(value, dict):
        raise ValueError("committed scorer evidence must be an object")
    evidence = _copy.deepcopy(value)
    _scan_committed_scorer_evidence(evidence)
    return validate_score_bundle(evidence)


def _validate_accepted_semantic_evidence(
    ballots: list[dict],
    adjudication: dict | None,
    semantic_score: float | None,
    reliability_score: float | None,
    rubric_binding: dict,
) -> None:
    replayed_ballots = [
        _ballot_record({
            field: ballot[field]
            for field in _BALLOT_INPUT_FIELDS
        })
        for ballot in ballots
    ]
    if replayed_ballots != ballots:
        raise ValueError("accepted semantic score contains invalid ballot evidence")
    if len(ballots) != 2:
        raise ValueError("accepted semantic score requires exactly two ballots")
    if any(ballot["candidate_blind"] is not True for ballot in ballots):
        raise ValueError("accepted semantic score contains non-blind ballot evidence")
    if any(not ballot["provenance_refs"] for ballot in ballots):
        raise ValueError("accepted semantic score has incomplete ballot provenance")
    if len({ballot["scorer_id"] for ballot in ballots}) != 2:
        raise ValueError("accepted semantic score reuses a scorer identity")
    if len({ballot["scorer_execution_id"] for ballot in ballots}) != 2:
        raise ValueError("accepted semantic score reuses a scorer execution")
    if any(not _opaque_id(ballot["scorer_id"]) for ballot in ballots):
        raise ValueError("accepted semantic score has an invalid scorer identity")
    if any(ballot["scorer_status"] != "current" for ballot in ballots):
        raise ValueError("accepted semantic score has a stale scorer")
    if any(ballot["calibration_status"] != "current" for ballot in ballots):
        raise ValueError("accepted semantic score has stale scorer calibration")
    if (
        any(ballot["rubric_status"] != "frozen" for ballot in ballots)
        or _rubric_binding(ballots[0]) != _rubric_binding(ballots[1])
    ):
        raise ValueError("accepted semantic score has stale or mismatched rubric evidence")
    if rubric_binding != _binding(
        ballots[0]["rubric_id"],
        ballots[0]["rubric_digest"],
    ):
        raise ValueError(
            "accepted semantic score does not match the frozen rubric binding"
        )
    disagreement = ballots[0]["outcome"] != ballots[1]["outcome"]
    if disagreement != (adjudication is not None):
        raise ValueError("accepted semantic score adjudication does not match ballot disagreement")
    if adjudication is not None:
        replayed_adjudication = _adjudication_record(
            {
                field: adjudication[field]
                for field in _ADJUDICATION_INPUT_FIELDS
            },
            ballots=ballots,
        )
        if replayed_adjudication != adjudication:
            raise ValueError(
                "accepted semantic score contains invalid adjudication evidence"
            )
        if not adjudication["provenance_refs"] or not _opaque_id(adjudication["adjudicator_id"]):
            raise ValueError("accepted semantic score has invalid adjudicator provenance")
        if adjudication["adjudicator_id"] in {ballot["scorer_id"] for ballot in ballots}:
            raise ValueError("accepted semantic score reuses a primary scorer as adjudicator")
        if adjudication["adjudicator_execution_id"] in {
            ballot["scorer_execution_id"] for ballot in ballots
        }:
            raise ValueError("accepted semantic score reuses a primary scorer execution")
        if (
            adjudication["adjudicator_status"] != "current"
            or adjudication["calibration_status"] != "current"
            or adjudication["rubric_status"] != "frozen"
            or _rubric_binding(adjudication) != _rubric_binding(ballots[0])
        ):
            raise ValueError("accepted semantic score has stale adjudicator evidence")
    expected_semantic = round(
        sum(ballot["criterion_scores"]["semantic"] for ballot in ballots) / 2,
        6,
    )
    expected_reliability = round(
        sum(ballot["criterion_scores"]["reliability"] for ballot in ballots) / 2,
        6,
    )
    if semantic_score != expected_semantic or reliability_score != expected_reliability:
        raise ValueError("accepted semantic scores do not match ballot evidence")


def validate_score_bundle(value: object) -> dict:
    """Validate an already-built score bundle without accepting embedded traces."""
    bundle = _closed(_copy.deepcopy(value), _SCORE_BUNDLE_FIELDS, "score bundle")
    if bundle["schema_version"] != SCORE_BUNDLE_SCHEMA_VERSION:
        raise ValueError("score bundle schema version is unsupported")
    _digest(bundle["score_bundle_id"], "score bundle ID")
    _digest(bundle["score_bundle_digest"], "score bundle digest")
    score_bundle_version = _text(bundle["score_bundle_version"], "score bundle version")
    if score_bundle_version != _CURRENT_SCORE_BUNDLE_VERSION:
        raise ValueError("stale score bundle version is not committed directly")
    bundle["score_bundle_version"] = score_bundle_version
    for field in _SCORE_BINDING_FIELDS:
        bundle[field] = _binding_record(bundle[field], field.replace("_", " "))
    if not isinstance(bundle["scorer_bindings"], list):
        raise ValueError("scorer bindings must be an array")
    bundle["scorer_bindings"] = [
        _binding_record(item, "scorer")
        for item in bundle["scorer_bindings"]
    ]
    if not isinstance(bundle["ballot_bindings"], list):
        raise ValueError("ballot bindings must be an array")
    bundle["ballot_bindings"] = [
        _binding_record(item, "ballot")
        for item in bundle["ballot_bindings"]
    ]
    bundle["adjudication_binding"] = _nullable_binding(
        bundle["adjudication_binding"],
        "adjudication",
    )
    if not isinstance(bundle["deterministic_gates"], list):
        raise ValueError("deterministic gates must be an array")
    bundle["deterministic_gates"] = [
        _validated_gate_row(item)
        for item in bundle["deterministic_gates"]
    ]
    if not isinstance(bundle["ballots"], list):
        raise ValueError("score bundle ballots must be an array")
    bundle["ballots"] = [
        _closed(ballot, _BALLOT_RESULT_FIELDS, "score bundle ballot")
        for ballot in bundle["ballots"]
    ]
    for ballot in bundle["ballots"]:
        if ballot["ballot_digest"] != digest(_ballot_digest_payload(ballot)):
            raise ValueError("ballot digest does not match content")
        if ballot["ballot_id"] != content_id(ballot, "ballot_id"):
            raise ValueError("ballot ID does not match content")
    if bundle["adjudication"] is not None:
        bundle["adjudication"] = _closed(
            bundle["adjudication"],
            _ADJUDICATION_RESULT_FIELDS,
            "score bundle adjudication",
        )
        if bundle["adjudication"]["adjudication_digest"] != digest(
            _adjudication_digest_payload(bundle["adjudication"])
        ):
            raise ValueError("adjudication digest does not match content")
        if bundle["adjudication"]["adjudication_id"] != content_id(
            bundle["adjudication"],
            "adjudication_id",
        ):
            raise ValueError("adjudication ID does not match content")
    else:
        if bundle["adjudication_binding"] is not None:
            raise ValueError("adjudication binding does not match adjudication")
    if bundle["adjudication"] is not None:
        _require_binding_match(
            bundle["adjudication_binding"],
            bundle["adjudication"]["adjudication_id"],
            bundle["adjudication"]["adjudication_digest"],
            "adjudication binding",
        )
    if len(bundle["ballot_bindings"]) != len(bundle["ballots"]):
        raise ValueError("ballot bindings do not match ballots")
    for expected, ballot in zip(bundle["ballot_bindings"], bundle["ballots"]):
        _require_binding_match(expected, ballot["ballot_id"], ballot["ballot_digest"], "ballot binding")
    if len(bundle["scorer_bindings"]) != len(bundle["ballots"]):
        raise ValueError("scorer bindings do not match ballots")
    for expected, ballot in zip(bundle["scorer_bindings"], bundle["ballots"]):
        _require_binding_match(expected, ballot["scorer_id"], ballot["scorer_digest"], "scorer binding")
    vector = _resource_vector(bundle["resource_vector"])
    bundle["resource_vector"] = vector
    score_disposition = _text(bundle["score_disposition"], "score disposition")
    failure_plane = _text(bundle["failure_plane"], "failure plane")
    failure_code = _text(bundle["failure_code"], "failure code")
    invalidation_reason = _text(bundle["invalidation_reason"], "invalidation reason")
    invalidated_bundle_binding = _nullable_binding(
        bundle["invalidated_bundle_binding"],
        "invalidated bundle",
    )
    bundle["invalidated_bundle_binding"] = invalidated_bundle_binding
    _validate_score_classification(
        score_disposition=score_disposition,
        failure_plane=failure_plane,
        failure_code=failure_code,
        invalidation_reason=invalidation_reason,
        invalidated_bundle_binding=invalidated_bundle_binding,
        vector=vector,
    )
    bundle["semantic_score"] = _nullable_unit_interval(bundle["semantic_score"], "semantic score")
    bundle["reliability_score"] = _nullable_unit_interval(
        bundle["reliability_score"], "reliability score"
    )
    if failure_code == "none":
        _validate_accepted_semantic_evidence(
            bundle["ballots"],
            bundle["adjudication"],
            bundle["semantic_score"],
            bundle["reliability_score"],
            bundle["rubric_binding"],
        )
    bundle["evidence_refs"] = _digest_refs(bundle["evidence_refs"], "score bundle evidence refs")
    if bundle["score_bundle_digest"] != digest(_score_bundle_digest_payload(bundle)):
        raise ValueError("score bundle digest does not match content")
    if bundle["score_bundle_id"] != content_id(bundle, "score_bundle_id"):
        raise ValueError("score bundle ID does not match content")
    return bundle


globals().pop("annotations", None)

__all__ = [
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
]
