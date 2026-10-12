"""Phase envelope: the fixed result a phase driver returns, and the runner's re-verification of it from disk.

The envelope states what a driver claims. Nothing in it decides a gate: the runner re-runs each claimed gate
against the artifacts on disk and rejects any disagreement. Missing or unparseable evidence fails the phase.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any

from ..envelope import diagnostic, response
from ..json_schema import json_schema_failures, schema_failure
from ..strict_input import SelectionError, require_fields, require_text
from ..trusted_io import resolve_input_path, resolve_repo_root, trusted_bytes, trusted_dir_exists
from .phase_brief import PHASES, brief_path
from .read_only import validate_gate

SCHEMA_VERSION = "phase-envelope/v1"
# Serialized UTF-8 bytes, so multibyte text cannot slip under a character count.
ENVELOPE_LIMIT_BYTES = 2048
# Gate fields a driver may restate as counts; each must equal what the gate reports on disk.
VERIFIED_COUNTS = ("markers", "task_count")
# Files each gate reads. validate-gate counts an absent or undecodable file as zero markers, so the runner
# insists the sources are present, non-empty and valid UTF-8 before it trusts a verdict. G6 also reads the workflow.
GATE_SOURCES = {"G1": ("spec.md",), "G2": ("spec.md",), "G3": ("plan.md",), "G4": ("spec.md", "plan.md"),
                "G5": ("tasks.md",), "G6": ("spec.md", "plan.md", "tasks.md"), "G7": ("tasks.md",)}
GATE_IDS = [f"G{number}" for number in range(1, 8)]
COUNTER = {"type": "integer", "minimum": 0}

ENVELOPE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "phase", "status", "next_action", "artifacts", "gates", "counts", "blocker", "usage"],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "phase": {"enum": list(PHASES)},
        "status": {"enum": ["pass", "fail", "blocked"]},
        "next_action": {"type": "string", "minLength": 1, "maxLength": 240},
        "artifacts": {"type": "array", "maxItems": 16, "items": {"type": "string", "minLength": 1, "maxLength": 200}},
        "gates": {
            "type": "array", "minItems": 1, "maxItems": len(GATE_IDS),
            "items": {
                "type": "object", "additionalProperties": False, "required": ["id", "result"],
                "properties": {"id": {"enum": GATE_IDS}, "result": {"enum": ["pass", "fail"]}},
            },
        },
        "counts": {"type": "object", "maxProperties": 16, "propertyNames": {"maxLength": 40}, "additionalProperties": COUNTER},
        "blocker": {"type": "string", "maxLength": 240},
        "usage": {
            "type": "object", "additionalProperties": False, "required": ["input_tokens", "output_tokens", "tool_calls"],
            "properties": {"input_tokens": COUNTER, "output_tokens": COUNTER, "tool_calls": COUNTER},
        },
    },
}


@dataclass
class Mismatch(Exception):
    """The first place the driver's claim and the evidence on disk disagree."""

    code: str
    detail: str


def envelope_failures(value: Any) -> list[dict[str, Any]]:
    """Contract failures for one envelope; an empty list means the shape and byte cap hold."""
    try:
        size = len(json.dumps(value, separators=(",", ":")).encode("utf-8"))
    except (TypeError, ValueError):
        return [schema_failure("type", "envelope", "Envelope is not serializable JSON.")]
    if size > ENVELOPE_LIMIT_BYTES:
        return [schema_failure("size", "envelope", f"Envelope is {size} bytes; the cap is {ENVELOPE_LIMIT_BYTES}.")]
    return json_schema_failures(value, ENVELOPE_SCHEMA, ENVELOPE_SCHEMA, "envelope")


def check_artifacts(envelope: dict[str, Any], root: Path) -> None:
    for raw in envelope["artifacts"]:
        try:
            path = brief_path(raw, "artifact")
            if PureWindowsPath(path).anchor or path.startswith("/"):
                raise ValueError("artifact must be relative to the repository root")
        except (SelectionError, ValueError) as exc:
            raise Mismatch("artifact_path_invalid", str(exc)) from exc
        resolved = resolve_input_path(path, root)
        # Absolute paths and links that leave the repository read back as None here.
        if trusted_dir_exists(resolved, root):
            if not any(resolved.iterdir()):
                raise Mismatch("artifact_missing", f"{path} is an empty directory")
        elif not trusted_bytes(resolved, root):
            raise Mismatch("artifact_missing", f"{path} is missing, empty or unreadable")


def check_gate_sources(gate: str, workflow: str, feature: str, root: Path) -> None:
    """Fail unless every file the gate reads is present, non-empty and strict UTF-8."""
    names = [f"{feature}/{name}" for name in GATE_SOURCES[gate]] + ([workflow] if gate == "G6" else [])
    for name in names:
        data = trusted_bytes(resolve_input_path(name, root), root)
        if not data:
            raise Mismatch("gate_evidence_missing", f"{gate} reads {name}, which is missing, empty or unreadable")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise Mismatch("gate_evidence_unparseable", f"{gate} reads {name}, which is not valid UTF-8") from exc


def disk_gate(gate: str, workflow: str, feature: str, root: Path) -> dict[str, Any]:
    """Re-run one gate against the disk and return its verdict object; anything unreadable raises."""
    try:
        result = validate_gate({"gate": gate, "workflow_file": workflow, "feature_dir": feature}, root)
        verdict = json.loads(result["stdout"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise Mismatch("gate_evidence_unparseable", f"{gate} evidence could not be read: {type(exc).__name__}") from exc
    if not isinstance(verdict, dict) or not isinstance(verdict.get("pass"), bool):
        raise Mismatch("gate_evidence_unparseable", f"{gate} evidence carries no boolean verdict")
    return verdict


def check_gates(envelope: dict[str, Any], workflow: str, feature: str, root: Path) -> dict[str, dict[str, Any]]:
    claimed = {gate["id"]: gate["result"] for gate in envelope["gates"]}
    phase_gate = PHASES[envelope["phase"]][1]
    if phase_gate not in claimed:
        raise Mismatch("phase_gate_missing", f"{envelope['phase']} must report {phase_gate}")
    for gate in claimed:
        check_gate_sources(gate, workflow, feature, root)
    verdicts = {gate: disk_gate(gate, workflow, feature, root) for gate in claimed}
    for gate, verdict in verdicts.items():
        observed = "pass" if verdict["pass"] else "fail"
        if claimed[gate] != observed:
            raise Mismatch("gate_claim_mismatch", f"{gate} claimed {claimed[gate]} but the evidence on disk says {observed}")
    return verdicts


def check_status_and_counts(envelope: dict[str, Any], verdicts: dict[str, dict[str, Any]]) -> None:
    gates_pass = all(gate["result"] == "pass" for gate in envelope["gates"])
    if envelope["status"] == "pass" and not gates_pass:
        raise Mismatch("status_contradicts_gates", "status pass cannot carry a failed gate")
    if envelope["status"] != "pass":
        raise Mismatch("phase_not_passed", envelope["blocker"] or f"driver reported {envelope['status']}")
    phase_verdict = verdicts[PHASES[envelope["phase"]][1]]
    for name in VERIFIED_COUNTS:
        if name in envelope["counts"] and envelope["counts"][name] != phase_verdict.get(name):
            raise Mismatch("count_mismatch", f"{name} claimed {envelope['counts'][name]} but the gate reports {phase_verdict.get(name)}")


def reverify(envelope: Any, workflow: str, feature: str, root: Path) -> dict[str, Any]:
    """Return the compact pass data, or raise the first mismatch."""
    failures = envelope_failures(envelope)
    if failures:
        raise Mismatch("envelope_invalid", f"{failures[0]['field']}: {failures[0]['message']}"[:240])
    check_artifacts(envelope, root)
    verdicts = check_gates(envelope, workflow, feature, root)
    check_status_and_counts(envelope, verdicts)
    return {"verdict": "pass", "phase": envelope["phase"], "next_action": envelope["next_action"]}


def run_phase_envelope_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Re-verify a phase envelope from disk; the answer is a compact pass or the first mismatch.

    Closed inputs: envelope (phase-envelope/v1, see ENVELOPE_SCHEMA), workflow_file and feature_dir
    (repo-relative; no traversal). The runner re-runs every claimed gate and checks every artifact path.

    pass: status ok, data {verdict: "pass", phase, next_action}.
    mismatch: status expected_failure, data {verdict: "fail", mismatch: {code, detail}} with code one of
        envelope_invalid, artifact_path_invalid, artifact_missing, phase_gate_missing, gate_evidence_missing, gate_evidence_unparseable,
        gate_claim_mismatch, status_contradicts_gates, phase_not_passed, count_mismatch.
    Malformed request inputs are an input_error; an envelope that breaks the contract fails the phase instead.
    """
    try:
        inputs = require_fields(request.inputs, {"envelope", "workflow_file", "feature_dir"}, "verify-phase-envelope inputs")
        workflow = brief_path(inputs["workflow_file"], "workflow_file")
        feature = brief_path(inputs["feature_dir"], "feature_dir").rstrip("/")
        require_text(feature, "feature_dir")
    except (SelectionError, ValueError) as exc:
        return response("input_error", request_id=request.request_id,
                        diagnostics=[diagnostic("invalid_phase_envelope_request", str(exc))])
    root = resolve_repo_root({})
    if isinstance(root, dict):
        return response("missing_prerequisite", request_id=request.request_id, diagnostics=[root])
    try:
        data = reverify(inputs["envelope"], workflow, feature, root)
    except Mismatch as exc:
        return response("expected_failure", request_id=request.request_id,
                        data={"verdict": "fail", "mismatch": {"code": exc.code, "detail": exc.detail[:240]}},
                        diagnostics=[diagnostic(exc.code, exc.detail,
                                                remediation_summary="The phase is not verified.",
                                                remediation_actions=["Repair the named mismatch, then return a new envelope."])])
    return response("ok", request_id=request.request_id, data=data)
