#!/usr/bin/env python3
"""G56R-003 deterministic score-bundle replay helpers."""

from __future__ import annotations

import copy as _copy
import importlib.util as _importlib_util
import re as _re
import sys as _sys
from pathlib import Path as _Path


REPLAY_BUNDLE_SCHEMA_VERSION = "score-replay.v1"
SCORE_REPLAY_SUMMARY_SCHEMA_VERSION = "score-replay-summary.v1"
ANALYSIS_REPLAY_SCHEMA_VERSION = "analysis-replay.v1"

_SCORING_MODULE_NAME = "_g56r_003_qualification_scoring_for_replay"
_STATISTICS_MODULE_NAME = "_g56r_003_qualification_statistics_for_replay"
_CORPUS_MODULE_NAME = "_g56r_003_qualification_corpus_for_replay"
_REPLAY_REQUEST_FIELDS = frozenset({"score_bundle", "evidence_refs"})
_REPLAY_BUNDLE_FIELDS = frozenset({
    "schema_version",
    "replay_bundle_id",
    "replay_bundle_digest",
    "score_bundle_binding",
    "score_bundle",
    "evidence_refs",
})
_SUMMARY_REQUEST_FIELDS = frozenset({"score_replays", "role_corpus"})
_SUMMARY_ROW_FIELDS = frozenset({"role_id", "replay_bundle"})
_SUMMARY_FIELDS = frozenset({
    "schema_version",
    "summary_id",
    "summary_digest",
    "required_core",
    "optional_helpers",
})
_SUMMARY_GROUP_FIELDS = frozenset({
    "role_count",
    "accepted_count",
    "score_bundle_ids",
    "replay_bundle_ids",
    "role_ids",
})
_ANALYSIS_REQUEST_FIELDS = frozenset({
    "schema_version",
    "analysis_plan",
    "partition",
    "paired_outcomes",
    "score_bundles",
    "binding_authorities",
    "execution_boundary",
    "source_lineage",
})
_ANALYSIS_OPTIONAL_REQUEST_FIELDS = frozenset()
_ANALYSIS_BINDING_FIELDS = frozenset({
    "analysis_plan_binding",
    "partition_binding",
    "pinned_client_binding",
    "runtime_snapshot_binding",
    "candidate_freeze_binding",
    "scorer_bindings",
    "rubric_binding",
    "adjudicator_binding",
    "workload_manifest_binding",
    "cache_policy_binding",
})
_EXECUTION_BOUNDARY_FIELDS = frozenset({
    "network_access",
    "live_repository_writes",
    "operator_only_raw_evidence_root",
})
_ANALYSIS_REPLAY_FIELDS = frozenset({
    *_ANALYSIS_REQUEST_FIELDS,
    "status",
    "decision",
    "decision_binding",
    "analysis_replay_artifact_id",
    "analysis_replay_artifact_digest",
})
_SOURCE_LINEAGE_FIELDS = frozenset({
    "schema_version",
    "source_ledger_binding",
    "successor_freeze",
    "materialization",
    "treatment_trace",
    "corpus",
    "score_bundle",
    "analysis_plan_binding",
})
_SUCCESSOR_LINEAGE_FIELDS = frozenset({
    "source_ledger_binding",
    "candidate_freeze_binding",
    "runtime_snapshot_binding",
})
_MATERIALIZATION_LINEAGE_FIELDS = frozenset({
    "materialization_binding",
    "candidate_freeze_binding",
})
_TREATMENT_TRACE_LINEAGE_FIELDS = frozenset({
    "execution_trace_binding",
    "materialization_binding",
    "candidate_freeze_binding",
})
_CORPUS_LINEAGE_FIELDS = frozenset({
    "corpus_binding",
    "partition_binding",
})
_SCORE_BUNDLE_LINEAGE_FIELDS = frozenset({
    "score_bundle_bindings",
    "paired_outcomes_digest",
    "execution_trace_binding",
    "corpus_binding",
    "candidate_freeze_binding",
    "runtime_snapshot_binding",
    "analysis_plan_binding",
})
_DIGEST_RE = _re.compile(r"^sha256:[0-9a-f]{64}$")


def _scoring():
    module = _sys.modules.get(_SCORING_MODULE_NAME)
    if module is not None:
        return module
    module_path = _Path(__file__).with_name("qualification_scoring.py")
    spec = _importlib_util.spec_from_file_location(_SCORING_MODULE_NAME, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    module = _importlib_util.module_from_spec(spec)
    _sys.modules[_SCORING_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def _statistics():
    module = _sys.modules.get(_STATISTICS_MODULE_NAME)
    if module is not None:
        return module
    module_path = _Path(__file__).with_name("qualification_statistics.py")
    spec = _importlib_util.spec_from_file_location(_STATISTICS_MODULE_NAME, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    module = _importlib_util.module_from_spec(spec)
    _sys.modules[_STATISTICS_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def _corpus():
    module = _sys.modules.get(_CORPUS_MODULE_NAME)
    if module is not None:
        return module
    module_path = _Path(__file__).with_name("qualification_corpus.py")
    spec = _importlib_util.spec_from_file_location(_CORPUS_MODULE_NAME, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    module = _importlib_util.module_from_spec(spec)
    _sys.modules[_CORPUS_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def _closed(value: object, keys: frozenset[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} must use its closed shape")
    return value


def _closed_with_optional(
    value: object,
    required_keys: frozenset[str],
    optional_keys: frozenset[str],
    label: str,
) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must use its closed shape")
    actual = set(value)
    if required_keys - actual or actual - required_keys - optional_keys:
        raise ValueError(f"{label} must use its closed shape")
    return value


def _digest_ref(value: object, label: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a sha256 digest")
    return value


def _digest_refs(value: object, label: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return [_digest_ref(item, label) for item in value]


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be boolean")
    return value


def _binding_record(value: object, label: str) -> dict:
    row = _closed(_copy.deepcopy(value), frozenset({"id", "digest"}), f"{label} binding")
    if not isinstance(row["id"], str) or not row["id"]:
        raise ValueError(f"{label} binding ID must be a non-empty string")
    return {
        "id": row["id"],
        "digest": _digest_ref(row["digest"], f"{label} binding digest"),
    }


def _binding(value_id: str, value_digest: str) -> dict:
    return {"id": value_id, "digest": value_digest}


def _require_binding_match(left: dict, right: dict, message: str) -> None:
    if left != right:
        raise ValueError(message)


def _validate_source_lineage(
    value: object,
    authorities: dict,
    plan: dict,
    partition: dict,
    paired_outcomes: list,
    score_bundles: list[dict],
) -> dict:
    lineage = _closed(
        _copy.deepcopy(value),
        _SOURCE_LINEAGE_FIELDS,
        "source lineage",
    )
    if lineage["schema_version"] != "source-ledger-lineage.v1":
        raise ValueError("source lineage schema version is unsupported")

    source_ledger = _binding_record(
        lineage["source_ledger_binding"],
        "source ledger",
    )
    analysis_plan = _binding_record(
        lineage["analysis_plan_binding"],
        "source lineage analysis plan",
    )
    expected_plan = _binding(
        _text(plan.get("analysis_plan_id"), "analysis plan ID"),
        _digest_ref(plan.get("analysis_plan_digest"), "analysis plan digest"),
    )
    _require_binding_match(
        analysis_plan,
        expected_plan,
        "source lineage analysis plan does not match frozen plan",
    )

    successor = _closed(
        lineage["successor_freeze"],
        _SUCCESSOR_LINEAGE_FIELDS,
        "source lineage successor freeze",
    )
    successor["source_ledger_binding"] = _binding_record(
        successor["source_ledger_binding"],
        "successor source ledger",
    )
    successor["candidate_freeze_binding"] = _binding_record(
        successor["candidate_freeze_binding"],
        "successor candidate freeze",
    )
    successor["runtime_snapshot_binding"] = _binding_record(
        successor["runtime_snapshot_binding"],
        "successor runtime snapshot",
    )
    _require_binding_match(
        successor["source_ledger_binding"],
        source_ledger,
        "source lineage successor freeze does not join source ledger",
    )
    _require_binding_match(
        successor["candidate_freeze_binding"],
        authorities["candidate_freeze_binding"],
        "source lineage successor freeze does not match candidate freeze authority",
    )
    _require_binding_match(
        successor["runtime_snapshot_binding"],
        authorities["runtime_snapshot_binding"],
        "source lineage successor freeze does not match runtime snapshot authority",
    )

    materialization = _closed(
        lineage["materialization"],
        _MATERIALIZATION_LINEAGE_FIELDS,
        "source lineage materialization",
    )
    materialization["materialization_binding"] = _binding_record(
        materialization["materialization_binding"],
        "materialization",
    )
    materialization["candidate_freeze_binding"] = _binding_record(
        materialization["candidate_freeze_binding"],
        "materialization candidate freeze",
    )
    _require_binding_match(
        materialization["candidate_freeze_binding"],
        successor["candidate_freeze_binding"],
        "source lineage materialization does not join successor freeze",
    )

    treatment_trace = _closed(
        lineage["treatment_trace"],
        _TREATMENT_TRACE_LINEAGE_FIELDS,
        "source lineage treatment trace",
    )
    treatment_trace["execution_trace_binding"] = _binding_record(
        treatment_trace["execution_trace_binding"],
        "treatment trace",
    )
    treatment_trace["materialization_binding"] = _binding_record(
        treatment_trace["materialization_binding"],
        "treatment trace materialization",
    )
    treatment_trace["candidate_freeze_binding"] = _binding_record(
        treatment_trace["candidate_freeze_binding"],
        "treatment trace candidate freeze",
    )
    _require_binding_match(
        treatment_trace["materialization_binding"],
        materialization["materialization_binding"],
        "source lineage treatment trace does not join materialization",
    )
    _require_binding_match(
        treatment_trace["candidate_freeze_binding"],
        successor["candidate_freeze_binding"],
        "source lineage treatment trace does not join successor freeze",
    )

    corpus = _closed(
        lineage["corpus"],
        _CORPUS_LINEAGE_FIELDS,
        "source lineage corpus",
    )
    corpus["corpus_binding"] = _binding_record(corpus["corpus_binding"], "corpus")
    corpus["partition_binding"] = _copy.deepcopy(corpus["partition_binding"])
    _require_binding_match(
        corpus["partition_binding"],
        partition,
        "source lineage corpus does not match partition authority",
    )

    score_bundle = _closed(
        lineage["score_bundle"],
        _SCORE_BUNDLE_LINEAGE_FIELDS,
        "source lineage score bundle",
    )
    raw_score_bindings = score_bundle["score_bundle_bindings"]
    if not isinstance(raw_score_bindings, list):
        raise ValueError("source lineage score bundle bindings must be an array")
    score_bundle["score_bundle_bindings"] = [
        _binding_record(item, "score bundle") for item in raw_score_bindings
    ]
    expected_score_bindings = sorted(
        (
            _binding(item["score_bundle_id"], item["score_bundle_digest"])
            for item in score_bundles
        ),
        key=lambda item: (item["id"], item["digest"]),
    )
    if score_bundle["score_bundle_bindings"] != expected_score_bindings:
        raise ValueError("source lineage score bundle bindings do not match score authority")
    score_bundle["paired_outcomes_digest"] = _digest_ref(
        score_bundle["paired_outcomes_digest"],
        "score bundle paired outcomes digest",
    )
    if score_bundle["paired_outcomes_digest"] != _scoring().digest(paired_outcomes):
        raise ValueError(
            "source lineage score bundle does not match paired outcomes"
        )
    score_bundle["execution_trace_binding"] = _binding_record(
        score_bundle["execution_trace_binding"],
        "score bundle execution trace",
    )
    score_bundle["corpus_binding"] = _binding_record(
        score_bundle["corpus_binding"],
        "score bundle corpus",
    )
    score_bundle["candidate_freeze_binding"] = _binding_record(
        score_bundle["candidate_freeze_binding"],
        "score bundle candidate freeze",
    )
    score_bundle["runtime_snapshot_binding"] = _binding_record(
        score_bundle["runtime_snapshot_binding"],
        "score bundle runtime snapshot",
    )
    score_bundle["analysis_plan_binding"] = _binding_record(
        score_bundle["analysis_plan_binding"],
        "score bundle analysis plan",
    )
    _require_binding_match(
        score_bundle["execution_trace_binding"],
        treatment_trace["execution_trace_binding"],
        "source lineage score bundle does not join treatment trace",
    )
    _require_binding_match(
        score_bundle["corpus_binding"],
        corpus["corpus_binding"],
        "source lineage score bundle does not join corpus",
    )
    _require_binding_match(
        score_bundle["candidate_freeze_binding"],
        successor["candidate_freeze_binding"],
        "source lineage score bundle does not join successor freeze",
    )
    _require_binding_match(
        score_bundle["runtime_snapshot_binding"],
        successor["runtime_snapshot_binding"],
        "source lineage score bundle does not join runtime snapshot",
    )
    _require_binding_match(
        score_bundle["analysis_plan_binding"],
        analysis_plan,
        "source lineage score bundle does not join frozen analysis plan",
    )

    lineage["source_ledger_binding"] = source_ledger
    lineage["analysis_plan_binding"] = analysis_plan
    lineage["successor_freeze"] = successor
    lineage["materialization"] = materialization
    lineage["treatment_trace"] = treatment_trace
    lineage["corpus"] = corpus
    lineage["score_bundle"] = score_bundle
    return lineage


def _validate_analysis_score_bundles(
    value: object,
    paired_outcomes: object,
    plan: dict,
    authorities: dict,
) -> list[dict]:
    if not isinstance(value, list) or not value:
        raise ValueError("analysis replay requires score bundles")
    if not isinstance(paired_outcomes, list):
        raise ValueError("analysis replay paired outcomes must be an array")
    scoring = _scoring()
    bundles = [scoring.sanitize_committed_scorer_evidence(item) for item in value]
    by_binding = {
        (item["score_bundle_id"], item["score_bundle_digest"]): item
        for item in bundles
    }
    if len(by_binding) != len(bundles):
        raise ValueError("analysis replay score bundles must be unique")
    expected_partition = {
        "id": plan["calibration_partition_binding"]["partition_id"],
        "digest": plan["calibration_partition_binding"]["partition_digest"],
    }
    scorer_bindings: set[tuple[str, str]] = set()
    for bundle in bundles:
        for field, expected in (
            ("partition_binding", expected_partition),
            ("runtime_snapshot_binding", authorities["runtime_snapshot_binding"]),
            ("candidate_freeze_binding", authorities["candidate_freeze_binding"]),
            ("rubric_binding", authorities["rubric_binding"]),
        ):
            if bundle[field] != expected:
                raise ValueError(f"score bundle {field} does not match analysis authority")
        scorer_bindings.update(
            (item["id"], item["digest"]) for item in bundle["scorer_bindings"]
        )
        if (
            bundle["adjudication_binding"] is not None
            and bundle["adjudication_binding"] != authorities["adjudicator_binding"]
        ):
            raise ValueError("score bundle adjudicator does not match analysis authority")
    expected_scorers = {
        (item["id"], item["digest"]) for item in authorities["scorer_bindings"]
    }
    if scorer_bindings != expected_scorers:
        raise ValueError("score bundle scorers do not match analysis authority")
    used_bindings: set[tuple[str, str]] = set()
    for outcome in paired_outcomes:
        if not isinstance(outcome, dict):
            raise ValueError("analysis replay outcomes must be objects")
        binding = _binding_record(
            outcome.get("score_bundle_binding"),
            "paired outcome score bundle",
        )
        bundle = by_binding.get((binding["id"], binding["digest"]))
        if bundle is None:
            raise ValueError("paired outcome does not bind a validated score bundle")
        binding_key = (binding["id"], binding["digest"])
        if binding_key in used_bindings:
            raise ValueError("paired outcomes cannot reuse a score bundle")
        used_bindings.add(binding_key)
        if outcome.get("assignment_binding") != bundle["assignment_binding"]:
            raise ValueError("paired outcome assignment does not match score bundle")
        if outcome.get("fixture_id") != bundle["fixture_binding"]["id"]:
            raise ValueError("paired outcome fixture does not match score bundle")
        if outcome.get("candidate_route_id") != bundle["candidate_route_binding"]["id"]:
            raise ValueError("paired outcome candidate route does not match score bundle")
        for outcome_field, bundle_field in (
            ("score_disposition", "score_disposition"),
            ("failure_plane", "failure_plane"),
            ("failure_code", "failure_code"),
            ("semantic_score", "semantic_score"),
            ("reliability_score", "reliability_score"),
        ):
            if outcome.get(outcome_field) != bundle[bundle_field]:
                raise ValueError(f"paired outcome {outcome_field} does not match score bundle")
        vector = outcome.get("resource_vector")
        if not isinstance(vector, dict):
            raise ValueError("paired outcome resource vector is missing")
        expected_vector = {
            "raw_input_tokens": bundle["resource_vector"]["input_tokens"],
            "cached_input_tokens": bundle["resource_vector"]["cached_input_tokens"],
            "output_tokens": bundle["resource_vector"]["output_tokens"],
            "duration_ms": bundle["resource_vector"]["duration_ms"],
            "retries": bundle["resource_vector"]["retries"],
            "compactions": bundle["resource_vector"]["compactions"],
            "acceptance": bundle["resource_vector"]["acceptance"],
            "terminal_state": bundle["resource_vector"]["terminal_state"],
        }
        if {
            key: vector.get(key) for key in expected_vector
        } != expected_vector:
            raise ValueError("paired outcome resource vector does not match score bundle")
    if used_bindings != set(by_binding):
        raise ValueError("analysis replay contains an orphan score bundle")
    return bundles


def _analysis_replay_digest_payload(bundle: dict) -> dict:
    return {
        key: value
        for key, value in bundle.items()
        if key not in {
            "analysis_replay_artifact_id",
            "analysis_replay_artifact_digest",
        }
    }


def _validate_analysis_authorities(value: object, plan: dict, partition: dict) -> dict:
    authorities = _closed(
        _copy.deepcopy(value),
        _ANALYSIS_BINDING_FIELDS,
        "analysis replay binding authorities",
    )
    for field in (
        "analysis_plan_binding",
        "pinned_client_binding",
        "runtime_snapshot_binding",
        "candidate_freeze_binding",
        "rubric_binding",
        "adjudicator_binding",
        "workload_manifest_binding",
        "cache_policy_binding",
    ):
        authorities[field] = _binding_record(
            authorities[field],
            field.removesuffix("_binding").replace("_", " "),
        )
    scorers = authorities["scorer_bindings"]
    if not isinstance(scorers, list) or len(scorers) != 2:
        raise ValueError("analysis replay requires exactly two scorer bindings")
    authorities["scorer_bindings"] = [
        _binding_record(item, "scorer") for item in scorers
    ]
    if len({item["id"] for item in authorities["scorer_bindings"]}) != 2:
        raise ValueError("analysis replay scorer bindings must be distinct")
    authorities["partition_binding"] = _copy.deepcopy(authorities["partition_binding"])

    expected_plan = _binding(
        _text(plan.get("analysis_plan_id"), "analysis plan ID"),
        _digest_ref(plan.get("analysis_plan_digest"), "analysis plan digest"),
    )
    if authorities["analysis_plan_binding"] != expected_plan:
        raise ValueError("analysis replay plan binding does not match")
    if authorities["partition_binding"] != partition:
        raise ValueError("analysis replay partition authority does not match")
    if authorities["partition_binding"] != plan.get("calibration_partition_binding"):
        raise ValueError("analysis replay partition does not match frozen analysis plan")

    workload = plan.get("workload_manifest")
    if not isinstance(workload, dict):
        raise ValueError("analysis replay plan workload manifest is missing")
    expected_workload = _binding(
        _text(workload.get("manifest_id"), "workload manifest ID"),
        _digest_ref(workload.get("manifest_digest"), "workload manifest digest"),
    )
    if authorities["workload_manifest_binding"] != expected_workload:
        raise ValueError("analysis replay workload manifest binding does not match")

    cache = plan.get("cache_policy")
    if not isinstance(cache, dict):
        raise ValueError("analysis replay plan cache policy is missing")
    expected_cache = _binding(
        _text(cache.get("policy_id"), "cache policy ID"),
        _digest_ref(cache.get("policy_digest"), "cache policy digest"),
    )
    if authorities["cache_policy_binding"] != expected_cache:
        raise ValueError("analysis replay cache policy binding does not match")
    return authorities


def _validate_execution_boundary(value: object) -> dict:
    boundary = _closed(
        _copy.deepcopy(value),
        _EXECUTION_BOUNDARY_FIELDS,
        "analysis replay execution boundary",
    )
    if boundary["network_access"] is not False:
        raise ValueError("analysis replay prohibits network access")
    if boundary["live_repository_writes"] != []:
        raise ValueError("analysis replay prohibits live repository writes")
    raw_root = _text(
        boundary["operator_only_raw_evidence_root"],
        "operator-only raw evidence root",
    )
    if not raw_root.startswith("operator-retention://"):
        raise ValueError("analysis replay requires an operator-only raw evidence root")
    return boundary


def _validate_analysis_request(value: object) -> dict:
    request = _closed_with_optional(
        _copy.deepcopy(value),
        _ANALYSIS_REQUEST_FIELDS,
        _ANALYSIS_OPTIONAL_REQUEST_FIELDS,
        "analysis replay request",
    )
    if request["schema_version"] != "analysis-replay-request.v1":
        raise ValueError("analysis replay request schema version is unsupported")
    plan = request["analysis_plan"]
    if not isinstance(plan, dict) or plan.get("status") != "frozen":
        raise ValueError("analysis replay requires a frozen analysis plan")
    partition = request["partition"]
    if not isinstance(partition, dict):
        raise ValueError("analysis replay partition must be an object")
    if (
        partition.get("partition_type") != "calibration"
        or partition.get("qualification_eligible") is not False
    ):
        raise ValueError("analysis replay requires qualification-ineligible calibration")
    request["binding_authorities"] = _validate_analysis_authorities(
        request["binding_authorities"],
        plan,
        partition,
    )
    request["execution_boundary"] = _validate_execution_boundary(
        request["execution_boundary"]
    )
    request["score_bundles"] = _validate_analysis_score_bundles(
        request["score_bundles"],
        request["paired_outcomes"],
        plan,
        request["binding_authorities"],
    )
    request["source_lineage"] = _validate_source_lineage(
        request["source_lineage"],
        request["binding_authorities"],
        plan,
        request["partition"],
        request["paired_outcomes"],
        request["score_bundles"],
    )
    if not isinstance(request["paired_outcomes"], list):
        raise ValueError("analysis replay paired outcomes must be an array")
    return request


def build_analysis_replay_bundle(value: object) -> dict:
    """Build a deterministic offline replay artifact for one frozen analysis."""
    request = _validate_analysis_request(value)
    decision = _statistics().evaluate_qualification_decision(
        analysis_plan=_copy.deepcopy(request["analysis_plan"]),
        paired_outcomes=_copy.deepcopy(request["paired_outcomes"]),
        partition=_copy.deepcopy(request["partition"]),
    )
    scoring = _scoring()
    bundle = {
        **request,
        "schema_version": ANALYSIS_REPLAY_SCHEMA_VERSION,
        "status": "replayed",
        "decision": decision,
        "decision_binding": _binding(
            _digest_ref(decision.get("decision_bundle_id"), "analysis decision bundle ID"),
            _digest_ref(
                decision.get("decision_bundle_digest"),
                "analysis decision bundle digest",
            ),
        ),
    }
    bundle["analysis_replay_artifact_digest"] = scoring.digest(
        _analysis_replay_digest_payload(bundle)
    )
    bundle["analysis_replay_artifact_id"] = scoring.content_id(
        bundle,
        "analysis_replay_artifact_id",
    )
    return validate_analysis_replay_bundle(bundle)


def validate_analysis_replay_bundle(value: object) -> dict:
    """Validate artifact identity, joins, and the recomputed analysis decision."""
    bundle = _closed_with_optional(
        _copy.deepcopy(value),
        _ANALYSIS_REPLAY_FIELDS,
        _ANALYSIS_OPTIONAL_REQUEST_FIELDS,
        "analysis replay bundle",
    )
    if bundle["schema_version"] != ANALYSIS_REPLAY_SCHEMA_VERSION:
        raise ValueError("analysis replay schema version is unsupported")
    request_input = {
        **{key: bundle[key] for key in _ANALYSIS_REQUEST_FIELDS},
        "schema_version": "analysis-replay-request.v1",
    }
    if "source_lineage" in bundle:
        request_input["source_lineage"] = bundle["source_lineage"]
    request = _validate_analysis_request(request_input)
    bundle.update({
        key: item for key, item in request.items() if key != "schema_version"
    })
    if bundle["status"] != "replayed":
        raise ValueError("analysis replay status must be replayed")
    scoring = _scoring()
    bundle["decision_binding"] = _binding_record(
        bundle["decision_binding"],
        "analysis decision",
    )
    expected_decision = _statistics().evaluate_qualification_decision(
        analysis_plan=_copy.deepcopy(bundle["analysis_plan"]),
        paired_outcomes=_copy.deepcopy(bundle["paired_outcomes"]),
        partition=_copy.deepcopy(bundle["partition"]),
    )
    if bundle["decision"] != expected_decision:
        raise ValueError("analysis replay decision does not match recomputation")
    expected_decision_binding = _binding(
        _digest_ref(
            expected_decision.get("decision_bundle_id"),
            "analysis decision bundle ID",
        ),
        _digest_ref(
            expected_decision.get("decision_bundle_digest"),
            "analysis decision bundle digest",
        ),
    )
    if bundle["decision_binding"] != expected_decision_binding:
        raise ValueError("analysis replay decision binding does not match")
    _digest_ref(
        bundle["analysis_replay_artifact_digest"],
        "analysis replay artifact digest",
    )
    _digest_ref(
        bundle["analysis_replay_artifact_id"],
        "analysis replay artifact ID",
    )
    if bundle["analysis_replay_artifact_digest"] != scoring.digest(
        _analysis_replay_digest_payload(bundle)
    ):
        raise ValueError("analysis replay artifact digest does not match content")
    if bundle["analysis_replay_artifact_id"] != scoring.content_id(
        bundle,
        "analysis_replay_artifact_id",
    ):
        raise ValueError("analysis replay artifact ID does not match content")
    return bundle


def replay_analysis_decision(value: object) -> dict:
    """Replay an offline artifact and fail closed on any identity or decision drift."""
    try:
        return validate_analysis_replay_bundle(value)
    except ValueError as exc:
        raise ValueError(f"analysis replay drift: {exc}") from exc


def _replay_digest_payload(bundle: dict) -> dict:
    return {
        key: value
        for key, value in bundle.items()
        if key not in {"replay_bundle_id", "replay_bundle_digest"}
    }


def _summary_digest_payload(summary: dict) -> dict:
    return {
        key: value
        for key, value in summary.items()
        if key not in {"summary_id", "summary_digest"}
    }


def _empty_summary_group() -> dict:
    return {
        "role_count": 0,
        "accepted_count": 0,
        "score_bundle_ids": [],
        "replay_bundle_ids": [],
        "role_ids": [],
    }


def _record_summary_row(group: dict, *, role_id: str, replay_bundle: dict, score_bundle: dict) -> None:
    group["role_count"] += 1
    if score_bundle["score_disposition"] == "accepted":
        group["accepted_count"] += 1
    group["score_bundle_ids"].append(score_bundle["score_bundle_id"])
    group["replay_bundle_ids"].append(replay_bundle["replay_bundle_id"])
    group["role_ids"].append(role_id)


def _validate_summary_group(value: object, label: str) -> dict:
    row = _closed(_copy.deepcopy(value), _SUMMARY_GROUP_FIELDS, label)
    for field in ("role_count", "accepted_count"):
        if not isinstance(row[field], int) or row[field] < 0:
            raise ValueError(f"{label} {field} must be a non-negative integer")
    if row["accepted_count"] > row["role_count"]:
        raise ValueError(f"{label} accepted count cannot exceed role count")
    for field in ("score_bundle_ids", "replay_bundle_ids", "role_ids"):
        if not isinstance(row[field], list):
            raise ValueError(f"{label} {field} must be an array")
    row["score_bundle_ids"] = [_digest_ref(item, f"{label} score bundle ID") for item in row["score_bundle_ids"]]
    row["replay_bundle_ids"] = [_digest_ref(item, f"{label} replay bundle ID") for item in row["replay_bundle_ids"]]
    row["role_ids"] = [_text(item, f"{label} role ID") for item in row["role_ids"]]
    if row["role_count"] != len(row["role_ids"]):
        raise ValueError(f"{label} role count does not match role IDs")
    if row["role_count"] != len(row["score_bundle_ids"]) or row["role_count"] != len(row["replay_bundle_ids"]):
        raise ValueError(f"{label} role count does not match replay bindings")
    return row


def build_score_replay_bundle(value: object) -> dict:
    """Build a replay bundle from one sanitized immutable score bundle."""
    request = _closed(_copy.deepcopy(value), _REPLAY_REQUEST_FIELDS, "score replay request")
    scoring = _scoring()
    score_bundle = scoring.sanitize_committed_scorer_evidence(request["score_bundle"])
    replay_bundle = {
        "schema_version": REPLAY_BUNDLE_SCHEMA_VERSION,
        "score_bundle_binding": _binding(score_bundle["score_bundle_id"], score_bundle["score_bundle_digest"]),
        "score_bundle": score_bundle,
        "evidence_refs": _digest_refs(request["evidence_refs"], "score replay evidence refs"),
    }
    replay_bundle["replay_bundle_digest"] = scoring.digest(_replay_digest_payload(replay_bundle))
    replay_bundle["replay_bundle_id"] = scoring.content_id(replay_bundle, "replay_bundle_id")
    return validate_score_replay_bundle(replay_bundle)


def validate_score_replay_bundle(value: object) -> dict:
    """Validate a replay bundle and its score-bundle binding."""
    replay_bundle = _closed(_copy.deepcopy(value), _REPLAY_BUNDLE_FIELDS, "score replay bundle")
    scoring = _scoring()
    if replay_bundle["schema_version"] != REPLAY_BUNDLE_SCHEMA_VERSION:
        raise ValueError("score replay schema version is unsupported")
    _digest_ref(replay_bundle["replay_bundle_id"], "score replay bundle ID")
    _digest_ref(replay_bundle["replay_bundle_digest"], "score replay bundle digest")
    replay_bundle["score_bundle_binding"] = _binding_record(
        replay_bundle["score_bundle_binding"],
        "score bundle",
    )
    replay_bundle["score_bundle"] = scoring.sanitize_committed_scorer_evidence(
        replay_bundle["score_bundle"]
    )
    expected_binding = _binding(
        replay_bundle["score_bundle"]["score_bundle_id"],
        replay_bundle["score_bundle"]["score_bundle_digest"],
    )
    if replay_bundle["score_bundle_binding"] != expected_binding:
        raise ValueError("score replay drift: score bundle binding does not match")
    replay_bundle["evidence_refs"] = _digest_refs(
        replay_bundle["evidence_refs"],
        "score replay evidence refs",
    )
    if replay_bundle["replay_bundle_digest"] != scoring.digest(_replay_digest_payload(replay_bundle)):
        raise ValueError("score replay bundle digest does not match content")
    if replay_bundle["replay_bundle_id"] != scoring.content_id(replay_bundle, "replay_bundle_id"):
        raise ValueError("score replay bundle ID does not match content")
    return replay_bundle


def replay_score_bundle(value: object) -> dict:
    """Replay a frozen score bundle and return the deterministic score record."""
    try:
        replay_bundle = validate_score_replay_bundle(value)
    except ValueError as exc:
        raise ValueError("score replay drift") from exc
    return replay_bundle["score_bundle"]


def summarize_score_replays(value: object) -> dict:
    """Summarize replayed scores while keeping optional helpers out of primary stats."""
    request = _closed(_copy.deepcopy(value), _SUMMARY_REQUEST_FIELDS, "score replay summary request")
    if not isinstance(request["score_replays"], list):
        raise ValueError("score replays must be an array")
    corpus = _corpus().validate_role_corpus(
        request["role_corpus"],
        repo_root=_Path(__file__).resolve().parents[4],
    )
    roles = {item["role_id"]: item for item in corpus["roles"]}
    groups = {
        "required_core": _empty_summary_group(),
        "optional_helpers": _empty_summary_group(),
    }
    for item in request["score_replays"]:
        row = _closed(item, _SUMMARY_ROW_FIELDS, "score replay summary row")
        role_id = _text(row["role_id"], "score replay role ID")
        if role_id not in roles:
            raise ValueError("score replay role is outside the governed corpus")
        optional_helper = roles[role_id]["optional_helper"]
        replay_bundle = validate_score_replay_bundle(row["replay_bundle"])
        score_bundle = replay_score_bundle(replay_bundle)
        fixture = roles[role_id]["fixture_binding"]
        expected_fixture_binding = {
            "id": fixture["fixture_id"],
            "digest": fixture["fixture_digest"],
        }
        if score_bundle["fixture_binding"] != expected_fixture_binding:
            raise ValueError("score replay does not bind the governed role fixture")
        _record_summary_row(
            groups["optional_helpers" if optional_helper else "required_core"],
            role_id=role_id,
            replay_bundle=replay_bundle,
            score_bundle=score_bundle,
        )
    scoring = _scoring()
    summary = {
        "schema_version": SCORE_REPLAY_SUMMARY_SCHEMA_VERSION,
        "required_core": groups["required_core"],
        "optional_helpers": groups["optional_helpers"],
    }
    summary["summary_digest"] = scoring.digest(_summary_digest_payload(summary))
    summary["summary_id"] = scoring.content_id(summary, "summary_id")
    return validate_score_replay_summary(summary)


def validate_score_replay_summary(value: object) -> dict:
    """Validate a helper-separated replay summary."""
    summary = _closed(_copy.deepcopy(value), _SUMMARY_FIELDS, "score replay summary")
    scoring = _scoring()
    if summary["schema_version"] != SCORE_REPLAY_SUMMARY_SCHEMA_VERSION:
        raise ValueError("score replay summary schema version is unsupported")
    _digest_ref(summary["summary_id"], "score replay summary ID")
    _digest_ref(summary["summary_digest"], "score replay summary digest")
    summary["required_core"] = _validate_summary_group(summary["required_core"], "required-core summary")
    summary["optional_helpers"] = _validate_summary_group(summary["optional_helpers"], "optional-helper summary")
    helper_roles = set(summary["optional_helpers"]["role_ids"])
    primary_roles = set(summary["required_core"]["role_ids"])
    if helper_roles.intersection(primary_roles):
        raise ValueError("optional helper roles must stay separate from required-core primary stats")
    if summary["summary_digest"] != scoring.digest(_summary_digest_payload(summary)):
        raise ValueError("score replay summary digest does not match content")
    if summary["summary_id"] != scoring.content_id(summary, "summary_id"):
        raise ValueError("score replay summary ID does not match content")
    return summary


globals().pop("annotations", None)

__all__ = [
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
]
