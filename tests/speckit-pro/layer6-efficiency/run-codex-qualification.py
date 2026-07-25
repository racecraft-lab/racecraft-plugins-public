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
    MATERIALIZER_VERSION,
    AgentMaterialization,
    materialize_agent_policy,
    verify_destination_bytes,
)
from codex_successor_capability import publish_successor_freeze  # noqa: E402
from qualification_contracts import validate_qualification_bundle  # noqa: E402


QUALIFICATION_ENTRY_POINT = "tests/speckit-pro/layer6-efficiency/run-codex-qualification.py"
LEGACY_SMOKE_RUNNER = "tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py"
LEGACY_SMOKE_SCORER = "tests/speckit-pro/layer6-efficiency/lib/quality-scorer.py"


class QualificationCliError(ValueError):
    """Raised for deterministic qualification command failures."""


class ScoreBlocked(QualificationCliError):
    """Raised when a score action is attempted before exact treatment exists."""


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
    eligible = sum(1 for item in assignments if item["score_eligible"])
    payload = {
        "command": "validate-treatment",
        "execution_trace_ids": sorted(item["execution_trace_id"] for item in assignments),
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
    read_json_file(args.score_request, "score request")
    if args.validated_treatment is None:
        raise ScoreBlocked("score requires validated exact treatment before outcome scoring")
    treatment = read_json_file(args.validated_treatment, "validated treatment")
    if not (
        isinstance(treatment, dict)
        and treatment.get("status") == "valid"
        and treatment.get("validated_treatment") == "exact"
    ):
        raise ScoreBlocked("score requires validated exact treatment before outcome scoring")
    return 2, {
        "command": "score",
        "message": "scoring is intentionally unavailable in this slice",
        "reason": "score_engine_unavailable",
        "status": "blocked",
    }


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
    "canonical_json",
    "main",
    "materialize_source",
    "matching_materialization",
    "publish_materialization_command",
    "publish_successor_freeze_command",
    "read_json_file",
    "score_command",
    "validate_treatment_command",
    "write_json_file",
]
