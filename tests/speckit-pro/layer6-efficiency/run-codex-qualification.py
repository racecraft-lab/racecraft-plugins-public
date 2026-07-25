#!/usr/bin/env python3
"""Thin deterministic entry point for Codex route qualification evidence."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR / "lib"
REPO_ROOT = SCRIPT_DIR.parents[2]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"

for _path in (PLUGIN_ROOT, LIB_DIR):
    _text = str(_path)
    if _text not in sys.path:
        sys.path.insert(0, _text)

from speckit_pro_runner.agent_materialization import (  # noqa: E402
    MATERIALIZATION_SCHEMA_VERSION,
    AgentMaterialization,
    materialize_agent_policy,
    verify_destination_bytes,
)
from codex_successor_capability import publish_successor_freeze  # noqa: E402
from qualification_contracts import validate_qualification_bundle  # noqa: E402
from qualification_replay import build_analysis_replay_bundle  # noqa: E402
from qualification_scoring import build_score_bundle, content_id, digest  # noqa: E402
from qualification_statistics import _validate_plan as validate_analysis_plan  # noqa: E402


QUALIFICATION_ENTRY_POINT = "tests/speckit-pro/layer6-efficiency/run-codex-qualification.py"
LEGACY_SMOKE_RUNNER = "tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py"
LEGACY_SMOKE_SCORER = "tests/speckit-pro/layer6-efficiency/lib/quality-scorer.py"


class QualificationCliError(ValueError):
    """Raised for deterministic qualification command failures."""


class ScoreBlocked(QualificationCliError):
    """Raised when a score action is attempted before exact treatment exists."""


class QualificationBoundaryError(QualificationCliError):
    """Raised with a stable reason code for a fail-closed CLI boundary."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"


def emit_json(value: Any) -> None:
    sys.stdout.write(canonical_json(value))


def read_json_file(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise QualificationCliError(f"{label} must be valid JSON") from exc
    except OSError as exc:
        raise QualificationCliError(f"{label} could not be read: {exc}") from exc


def write_json_file(path: Path, value: Any, label: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical_json(value), encoding="utf-8", newline="\n")
    except OSError as exc:
        raise QualificationCliError(f"{label} could not be written: {exc}") from exc


def write_json_file_exclusive(path: Path, value: Any, label: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="\n") as output:
            output.write(canonical_json(value))
    except OSError as exc:
        raise QualificationCliError(
            f"{label} requires a new output path and could not be written: {exc}"
        ) from exc


def materialize_source(source: Path, source_relative_path: str) -> tuple[AgentMaterialization, bytes]:
    try:
        source_bytes = source.read_bytes()
    except OSError as exc:
        raise QualificationCliError(f"agent policy source could not be read: {exc}") from exc
    materialized = materialize_agent_policy(
        source_relative_path=source_relative_path,
        source_bytes=source_bytes,
    )
    if not verify_destination_bytes(materialized, source_bytes):
        raise QualificationCliError("source materialization did not verify destination bytes")
    return materialized, source_bytes


def materialization_payload(materialized: AgentMaterialization) -> dict[str, Any]:
    return {
        "byte_count": materialized.byte_count,
        "candidate_route": copy.deepcopy(materialized.candidate_route),
        "configuration_digest": materialized.configuration_digest,
        "destination_bytes_digest": materialized.destination_bytes_digest,
        "instruction_digest": materialized.instruction_digest,
        "materialization_id": materialized.materialization_id,
        "materializer_binding": copy.deepcopy(materialized.materializer_binding),
        "materializer_version": materialized.materializer_version,
        "parent_controls": copy.deepcopy(materialized.parent_controls),
        "schema_version": MATERIALIZATION_SCHEMA_VERSION,
        "source_binding": copy.deepcopy(materialized.source_binding),
        "status": "materialized",
    }


def load_trusted_qualification_evidence(path: Path | None) -> dict[str, dict] | None:
    if path is None:
        return None
    raw = read_json_file(path, "trusted qualification evidence")
    if isinstance(raw, dict) and "qualification_evidence_registry" in raw:
        raw = raw["qualification_evidence_registry"]
    if isinstance(raw, list):
        result = {}
        for item in raw:
            if not isinstance(item, dict) or not isinstance(item.get("qualification_evidence_id"), str):
                raise QualificationCliError("trusted qualification evidence entries must carry IDs")
            result[item["qualification_evidence_id"]] = copy.deepcopy(item)
        return result
    if isinstance(raw, dict) and all(isinstance(key, str) and isinstance(value, dict) for key, value in raw.items()):
        return copy.deepcopy(raw)
    raise QualificationCliError("trusted qualification evidence must be an object map or registry array")


def matching_materialization(
    qualification_bundle: dict[str, Any],
    materialized: AgentMaterialization,
) -> dict[str, Any]:
    assignments_by_materialization = {
        item["materialization_id"]: item
        for item in qualification_bundle["qualification_assignments"]
    }
    traces_by_execution = {
        trace["objective_binding"]["execution_trace_id"]: trace
        for trace in qualification_bundle["treatment_bundle"]["treatment_traces"]
    }
    for row in qualification_bundle["materializations"]:
        assignment = assignments_by_materialization.get(row["materialization_id"])
        trace = traces_by_execution.get(assignment["execution_trace_id"]) if assignment else None
        if trace is None:
            continue
        route = materialized.candidate_route
        if (
            row["destination_bytes_digest"] == materialized.destination_bytes_digest
            and row["instruction_digest"] == materialized.instruction_digest
            and row["requested_model"] == route["model"]
            and row["requested_effort"] == route["model_reasoning_effort"]
            and trace["named_agent"] == route["agent_name"]
        ):
            return row
    raise QualificationCliError("source materialization does not match qualification bundle")


def legacy_smoke_status() -> tuple[int, dict[str, Any]]:
    return 0, {
        "legacy_runner": LEGACY_SMOKE_RUNNER,
        "legacy_scorer": LEGACY_SMOKE_SCORER,
        "qualification_entry_point": QUALIFICATION_ENTRY_POINT,
        "release_qualification": False,
        "status": "non_release_smoke",
    }


def publish_materialization_command(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    materialized, _source_bytes = materialize_source(
        args.agent_policy_source,
        args.source_relative_path,
    )
    payload = materialization_payload(materialized)
    if args.output is not None:
        write_json_file(args.output, payload, "materialization output")
    return 0, payload


def validate_treatment_command(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    materialized, _source_bytes = materialize_source(
        args.agent_policy_source,
        args.source_relative_path,
    )
    bundle = read_json_file(args.qualification_bundle, "qualification bundle")
    if not isinstance(bundle, dict):
        raise QualificationCliError("qualification bundle must be a JSON object")
    trusted = load_trusted_qualification_evidence(args.trusted_qualification_evidence)
    validated = validate_qualification_bundle(
        bundle,
        trusted_qualification_evidence=trusted,
    )
    matched = matching_materialization(validated, materialized)
    assignments = validated["qualification_assignments"]
    trace_digests = {
        item["execution_trace_id"]: item["source_trace_digest"]
        for item in validated["qualification_traces"]
    }
    eligible = sum(1 for item in assignments if item["score_eligible"])
    payload = {
        "command": "validate-treatment",
        "execution_trace_ids": sorted(item["execution_trace_id"] for item in assignments),
        "score_eligible_execution_trace_ids": sorted(
            item["execution_trace_id"]
            for item in assignments
            if item["score_eligible"]
        ),
        "score_eligible_execution_trace_bindings": sorted(
            (
                {
                    "id": item["execution_trace_id"],
                    "digest": trace_digests[item["execution_trace_id"]],
                }
                for item in assignments
                if item["score_eligible"]
            ),
            key=lambda item: (item["id"], item["digest"]),
        ),
        "materialization_ids": sorted(item["materialization_id"] for item in validated["materializations"]),
        "materializer_source_path": materialized.materializer_binding["path"],
        "matched_materialization_id": matched["materialization_id"],
        "score_eligible_count": eligible,
        "score_ineligible_count": len(assignments) - eligible,
        "status": "valid",
        "validated_treatment": "exact",
    }
    if args.output is not None:
        write_json_file(args.output, payload, "validated treatment output")
    return 0, payload


def publish_successor_freeze_command(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    request = read_json_file(args.request, "successor request")
    manifest = read_json_file(args.manifest, "source manifest")
    if not isinstance(request, dict):
        raise QualificationCliError("successor request must be a JSON object")
    if not isinstance(manifest, dict):
        raise QualificationCliError("source manifest must be a JSON object")
    result = publish_successor_freeze(
        args.predecessor_freeze,
        request,
        args.output,
        args.raw_evidence_root,
        REPO_ROOT,
        manifest=manifest,
    )
    payload = {"command": "publish-successor-freeze", "status": "published", **result}
    return 0, payload


def score_command(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    score_request = read_json_file(args.score_request, "score request")
    if not isinstance(score_request, dict):
        raise QualificationCliError("score request must be a JSON object")
    if (
        args.validated_treatment is None
        or args.qualification_bundle is None
        or args.agent_policy_source is None
        or args.source_relative_path is None
    ):
        raise ScoreBlocked(
            "score requires validated exact treatment joined to original evidence"
        )
    treatment = read_json_file(args.validated_treatment, "validated treatment")
    _code, replayed_treatment = validate_treatment_command(
        argparse.Namespace(
            qualification_bundle=args.qualification_bundle,
            agent_policy_source=args.agent_policy_source,
            source_relative_path=args.source_relative_path,
            trusted_qualification_evidence=args.trusted_qualification_evidence,
            output=None,
        )
    )
    if treatment != replayed_treatment:
        raise ScoreBlocked(
            "score requires a validated treatment receipt joined to original evidence"
        )
    execution_trace_binding = score_request.get("execution_trace_binding")
    eligible_trace_bindings = replayed_treatment[
        "score_eligible_execution_trace_bindings"
    ]
    if (
        not isinstance(execution_trace_binding, dict)
        or not isinstance(eligible_trace_bindings, list)
        or execution_trace_binding not in eligible_trace_bindings
    ):
        raise ScoreBlocked(
            "score requires validated exact treatment for the requested execution trace binding"
        )
    bundle = build_score_bundle(score_request)
    return 0, {
        "command": "score",
        "score_bundle": bundle,
        "status": "scored",
    }


_CAMPAIGN_BUDGET_FIELDS = frozenset({
    "max_attempts",
    "max_wall_clock_seconds",
    "max_raw_input_tokens",
    "max_cached_input_tokens",
    "max_output_tokens",
    "max_candidates",
    "max_confirmation_entries",
})


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise QualificationBoundaryError(
            f"{label.replace(' ', '_')}_invalid",
            f"{label} must be a JSON object",
        )
    return value


def _binding(value_id: Any, value_digest: Any, label: str) -> dict[str, str]:
    if not isinstance(value_id, str) or not value_id:
        raise QualificationBoundaryError(
            f"{label.replace(' ', '_')}_invalid",
            f"{label} ID must be a non-empty string",
        )
    if not isinstance(value_digest, str) or not value_digest.startswith("sha256:"):
        raise QualificationBoundaryError(
            f"{label.replace(' ', '_')}_invalid",
            f"{label} digest must be a sha256 binding",
        )
    return {"id": value_id, "digest": value_digest}


def _require_binding(value: Any, label: str) -> dict[str, str]:
    row = _require_object(value, label)
    if set(row) != {"id", "digest"}:
        raise QualificationBoundaryError(
            f"{label.replace(' ', '_')}_invalid",
            f"{label} must use the closed ID/digest shape",
        )
    return _binding(row["id"], row["digest"], label)


def _require_calibration_partition(value: Any) -> dict[str, Any]:
    partition = _require_object(value, "partition")
    if (
        partition.get("partition_type") != "calibration"
        or partition.get("qualification_eligible") is not False
    ):
        raise QualificationBoundaryError(
            "calibration_partition_required",
            "only the qualification-ineligible calibration partition may run",
        )
    for field in ("partition_id", "partition_digest"):
        if not isinstance(partition.get(field), str) or not partition[field]:
            raise QualificationBoundaryError(
                "calibration_partition_required",
                f"calibration partition is missing {field}",
            )
    return copy.deepcopy(partition)


def _require_campaign_budget(value: Any) -> dict[str, int]:
    budget = _require_object(value, "campaign budget")
    if set(budget) != _CAMPAIGN_BUDGET_FIELDS:
        raise QualificationBoundaryError(
            "campaign_budget_incomplete",
            "campaign budget must declare all seven ceilings",
        )
    for field, item in budget.items():
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise QualificationBoundaryError(
                "campaign_budget_invalid",
                f"campaign budget field {field} must be a non-negative integer",
            )
    return copy.deepcopy(budget)


def _require_policy_bindings(
    policy: dict[str, Any],
    freeze: dict[str, Any],
    corpus: dict[str, Any],
    partition: dict[str, Any],
    budget: dict[str, int],
) -> dict[str, Any]:
    expected_freeze = _binding(
        freeze.get("candidate_freeze_id"),
        freeze.get("freeze_digest"),
        "candidate freeze",
    )
    expected_corpus = _binding(
        corpus.get("corpus_id"),
        corpus.get("corpus_digest"),
        "corpus",
    )
    if policy.get("partition_binding") != partition:
        raise QualificationBoundaryError(
            "partition_binding_mismatch",
            "experiment policy partition binding does not match",
        )
    if policy.get("candidate_freeze_binding") != expected_freeze:
        raise QualificationBoundaryError(
            "candidate_freeze_binding_mismatch",
            "experiment policy candidate freeze binding does not match",
        )
    if policy.get("corpus_binding") != expected_corpus:
        raise QualificationBoundaryError(
            "corpus_binding_mismatch",
            "experiment policy corpus binding does not match",
        )
    if policy.get("budget") != budget:
        raise QualificationBoundaryError(
            "campaign_budget_binding_mismatch",
            "experiment policy budget does not match the requested campaign budget",
        )
    pinned_client = _require_binding(
        freeze.get("pinned_client_binding"),
        "pinned client binding",
    )
    runtime_snapshot = _require_binding(
        freeze.get("runtime_snapshot_binding"),
        "runtime snapshot binding",
    )
    if policy.get("pinned_client_binding") != pinned_client:
        raise QualificationBoundaryError(
            "pinned_client_binding_mismatch",
            "experiment policy pinned client binding does not match",
        )
    if policy.get("runtime_snapshot_binding") != runtime_snapshot:
        raise QualificationBoundaryError(
            "runtime_snapshot_binding_mismatch",
            "experiment policy runtime snapshot binding does not match",
        )
    scorers = policy.get("scorer_bindings")
    if not isinstance(scorers, list) or len(scorers) != 2:
        raise QualificationBoundaryError(
            "scorer_bindings_invalid",
            "experiment policy requires exactly two scorer bindings",
        )
    validated_scorers = [_require_binding(item, "scorer binding") for item in scorers]
    if len({item["id"] for item in validated_scorers}) != 2:
        raise QualificationBoundaryError(
            "scorer_bindings_invalid",
            "experiment policy scorer bindings must be distinct",
        )
    return {
        "pinned_client_binding": pinned_client,
        "runtime_snapshot_binding": runtime_snapshot,
        "scorer_bindings": validated_scorers,
        "rubric_binding": _require_binding(policy.get("rubric_binding"), "rubric binding"),
        "adjudicator_binding": _require_binding(
            policy.get("adjudicator_binding"),
            "adjudicator binding",
        ),
        "workload_manifest_binding": _require_binding(
            policy.get("workload_manifest_binding"),
            "workload manifest binding",
        ),
        "cache_policy_binding": _require_binding(
            policy.get("cache_policy_binding"),
            "cache policy binding",
        ),
    }


def calibrate_command(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    if not args.confirm_explicit_local_live:
        return 2, {
            "command": "calibrate",
            "message": "calibration requires explicit confirmation of local live execution",
            "reason": "explicit_live_confirmation_required",
            "status": "blocked",
        }
    partition = _require_calibration_partition(
        read_json_file(args.partition, "partition")
    )
    freeze = _require_object(
        read_json_file(args.candidate_freeze, "candidate freeze"),
        "candidate freeze",
    )
    policy = _require_object(
        read_json_file(args.experiment_policy, "experiment policy"),
        "experiment policy",
    )
    corpus = _require_object(read_json_file(args.corpus, "corpus"), "corpus")
    budget = _require_campaign_budget(read_json_file(args.budget, "campaign budget"))
    raw_root = args.raw_evidence_root.resolve()
    try:
        raw_root.relative_to(REPO_ROOT.resolve())
    except ValueError:
        pass
    else:
        raise QualificationBoundaryError(
            "operator_only_raw_root_required",
            "raw calibration evidence must remain outside the live repository",
        )
    if not raw_root.is_dir():
        raise QualificationBoundaryError(
            "operator_only_raw_root_required",
            "operator-only raw evidence root must be an existing directory",
        )
    bindings = _require_policy_bindings(
        policy,
        freeze,
        corpus,
        partition,
        budget,
    )
    return 0, {
        "command": "calibrate",
        "status": "calibration_ready",
        "execution_mode": "explicit_local_live",
        "network_access": False,
        "live_writes": [],
        "partition_binding": partition,
        "budget": budget,
        "operator_only_raw_evidence_root": str(raw_root),
        **bindings,
    }


def replay_command(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    request = _require_object(
        read_json_file(args.request, "analysis replay request"),
        "analysis replay request",
    )
    bundle = build_analysis_replay_bundle(request)
    return 0, {"command": "replay", **bundle}


def freeze_analysis_plan_command(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    report = _require_object(
        read_json_file(args.calibration_report, "calibration report"),
        "calibration report",
    )
    draft = _require_object(
        read_json_file(args.draft_plan, "analysis plan draft"),
        "analysis plan draft",
    )
    partition = _require_calibration_partition(
        report.get("calibration_partition_binding")
    )
    provenance = _require_object(report.get("freeze_provenance"), "freeze provenance")
    if provenance.get("frozen_after_calibration") is not True:
        raise QualificationBoundaryError(
            "calibration_not_complete",
            "analysis plan may freeze only after calibration",
        )
    if provenance.get("cohort_outcome_observed") is not False:
        raise QualificationBoundaryError(
            "cohort_outcome_observed",
            "analysis plan must freeze before cohort outcomes are observed",
        )
    _require_binding(
        provenance.get("independent_review_binding"),
        "independent review binding",
    )
    evidence = report.get("calibration_evidence_bindings")
    if not isinstance(evidence, list) or not evidence:
        raise QualificationBoundaryError(
            "calibration_evidence_missing",
            "analysis plan freeze requires calibration evidence bindings",
        )
    for item in evidence:
        _require_binding(item, "calibration evidence binding")
    frozen = copy.deepcopy(draft)
    frozen["status"] = "frozen"
    frozen["calibration_partition_binding"] = partition
    frozen["calibration_evidence_bindings"] = copy.deepcopy(evidence)
    frozen["freeze_provenance"] = copy.deepcopy(provenance)
    frozen["analysis_plan_digest"] = digest({
        key: value
        for key, value in frozen.items()
        if key not in {"analysis_plan_id", "analysis_plan_digest"}
    })
    frozen["analysis_plan_id"] = content_id(frozen, "analysis_plan_id")
    try:
        frozen = validate_analysis_plan(frozen)
    except ValueError as exc:
        raise QualificationBoundaryError(
            "analysis_plan_schema_invalid",
            str(exc),
        ) from exc
    write_json_file_exclusive(args.output, frozen, "frozen analysis plan")
    return 0, frozen


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    subcommands.add_parser(
        "legacy-smoke-status",
        help="Report that the historical efficiency runner is smoke-only evidence.",
    )

    materialize = subcommands.add_parser(
        "publish-materialization",
        help="Materialize a Codex agent policy into deterministic proof JSON.",
    )
    materialize.add_argument("--agent-policy-source", type=Path, required=True)
    materialize.add_argument("--source-relative-path", required=True)
    materialize.add_argument("--output", type=Path)

    treatment = subcommands.add_parser(
        "validate-treatment",
        help="Validate score eligibility against exact materialized policy bytes.",
    )
    treatment.add_argument("--qualification-bundle", type=Path, required=True)
    treatment.add_argument("--agent-policy-source", type=Path, required=True)
    treatment.add_argument("--source-relative-path", required=True)
    treatment.add_argument("--trusted-qualification-evidence", type=Path)
    treatment.add_argument("--output", type=Path)

    successor = subcommands.add_parser(
        "publish-successor-freeze",
        help="Publish an additive successor freeze through the successor capability contract.",
    )
    successor.add_argument("--predecessor-freeze", type=Path, required=True)
    successor.add_argument("--request", type=Path, required=True)
    successor.add_argument("--manifest", type=Path, required=True)
    successor.add_argument("--raw-evidence-root", type=Path, required=True)
    successor.add_argument("--output", type=Path, required=True)

    score = subcommands.add_parser(
        "score",
        help="Fail closed unless exact treatment validation has already succeeded.",
    )
    score.add_argument("--score-request", type=Path, required=True)
    score.add_argument("--validated-treatment", type=Path)
    score.add_argument("--qualification-bundle", type=Path)
    score.add_argument("--agent-policy-source", type=Path)
    score.add_argument("--source-relative-path")
    score.add_argument("--trusted-qualification-evidence", type=Path)

    calibrate = subcommands.add_parser(
        "calibrate",
        help="Validate an explicit, pinned, local-only calibration campaign.",
    )
    calibrate.add_argument("--partition", type=Path, required=True)
    calibrate.add_argument("--candidate-freeze", type=Path, required=True)
    calibrate.add_argument("--experiment-policy", type=Path, required=True)
    calibrate.add_argument("--corpus", type=Path, required=True)
    calibrate.add_argument("--budget", type=Path, required=True)
    calibrate.add_argument("--raw-evidence-root", type=Path, required=True)
    calibrate.add_argument("--confirm-explicit-local-live", action="store_true")

    replay = subcommands.add_parser(
        "replay",
        help="Recompute a deterministic qualification decision without live inputs.",
    )
    replay.add_argument("--request", type=Path, required=True)

    freeze = subcommands.add_parser(
        "freeze-analysis-plan",
        help="Freeze a versioned analysis plan from calibration-only evidence.",
    )
    freeze.add_argument("--calibration-report", type=Path, required=True)
    freeze.add_argument("--draft-plan", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "legacy-smoke-status": lambda _args: legacy_smoke_status(),
        "publish-materialization": publish_materialization_command,
        "validate-treatment": validate_treatment_command,
        "publish-successor-freeze": publish_successor_freeze_command,
        "score": score_command,
        "calibrate": calibrate_command,
        "replay": replay_command,
        "freeze-analysis-plan": freeze_analysis_plan_command,
    }
    try:
        exit_code, payload = handlers[args.command](args)
    except ScoreBlocked as exc:
        emit_json({
            "command": args.command,
            "message": str(exc),
            "reason": "score_before_treatment_refused",
            "status": "blocked",
        })
        return 2
    except QualificationBoundaryError as exc:
        emit_json({
            "command": args.command,
            "error": str(exc),
            "reason": exc.reason,
            "status": "error",
        })
        return 2
    except (OSError, ValueError, RecursionError) as exc:
        emit_json({
            "command": args.command,
            "error": str(exc),
            "status": "error",
        })
        return 2
    emit_json(payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "LEGACY_SMOKE_RUNNER",
    "LEGACY_SMOKE_SCORER",
    "QUALIFICATION_ENTRY_POINT",
    "build_parser",
    "calibrate_command",
    "canonical_json",
    "freeze_analysis_plan_command",
    "main",
    "materialize_source",
    "matching_materialization",
    "publish_materialization_command",
    "publish_successor_freeze_command",
    "read_json_file",
    "replay_command",
    "score_command",
    "validate_treatment_command",
    "write_json_file",
]
