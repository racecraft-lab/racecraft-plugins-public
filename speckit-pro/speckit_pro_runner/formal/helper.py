"""Runner interface for read-only readiness and preview/execute model checks."""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response
from .catalog import CATALOG_PATH, FormalError, confined, selected_catalog
from .engine import execute_model, inspect_tool, obligations, preview_model
from .evidence import CHECKPOINT_ROWS, fingerprint, read_checkpoint, record_path, write_checkpoint
from .selection import SelectionError, selection_from_workflow


def relative_input(root: Path, value: str) -> str:
    path = Path(value)
    return path.resolve().relative_to(root).as_posix() if path.is_absolute() else value


def discover(root: Path, workflow: str) -> dict[str, Any]:
    selection = selection_from_workflow(confined(root, workflow).read_text(encoding="utf-8"))
    if selection["status"] != "enabled":
        return {"selection": selection, "models": {}, "identities": {}, "gaps": [], "verdict": "disabled"}
    models, gaps = selected_catalog(root, selection)
    identities = {}
    for model_id, item in models.items():
        try:
            identities[model_id] = inspect_tool(root, item["tool"], item["model"]["checker"])
        except FormalError as exc:
            gaps.append({"model": model_id, "verdict": exc.verdict, "reason": str(exc)})
    blocking = [gap for gap in gaps if gap["verdict"] != "pending_authoring"]
    verdict = (blocking or gaps)[0]["verdict"] if gaps else "ready"
    return {"selection": selection, "models": models, "identities": identities, "gaps": gaps, "verdict": verdict}


def current_checkpoint(root: Path, workflow: str, checkpoint: str = "plan") -> dict[str, Any]:
    context = discover(root, workflow)
    if context["verdict"] == "disabled":
        return {"required": False, "complete": True, "verdict": "disabled"}
    record = read_checkpoint(root, workflow, checkpoint)
    if context["gaps"] or not isinstance(record, dict) or record.get("verdict") != "pass":
        return {"required": True, "complete": False, "verdict": context["verdict"] if context["gaps"] else "pending", "resume": "plan"}
    expected = fingerprint(root, context["selection"], context["models"], context["identities"], record["spec_file"], record["plan_file"])
    complete = record.get("fingerprint") == expected and record.get("workflow_file") == workflow and complete_results(record, context["models"])
    return {"required": True, "complete": complete, "verdict": "pass" if complete else "stale", "resume": None if complete else "plan", "evidence": record_path(root, workflow, checkpoint).relative_to(root).as_posix()}


def checkpoint_guard(root: Path, workflow: str, checkpoint: str = "plan") -> dict[str, Any]:
    """Return a blocking result on malformed or missing checkpoint prerequisites."""
    try:
        return current_checkpoint(root, relative_input(root, workflow), checkpoint)
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        return {"required": True, "complete": False, "verdict": "invalid_configuration", "reason": str(exc), "resume": "plan"}


def apply_resume_guard(root: Path, workflow: str, parsed: dict[str, Any], signals: dict[str, Any]) -> dict[str, Any]:
    """Constrain parsed resume state without skipping earlier planning phases."""
    formal = checkpoint_guard(root, workflow)
    if formal["complete"]:
        return formal
    if parsed["stage"] == "implement" or parsed["from_phase"] in {"checklist", "tasks", "analyze", "implement"}:
        raise SelectionError(f"formal checkpoint {formal['verdict']}; resume --stage plan --from-phase plan")
    signals["planning_complete"] = False
    first = signals.get("first_open")
    if first is None or first[0] not in {"Specify", "Clarify", "Plan"}:
        signals["first_open"] = ("Formal Check", formal["verdict"])
        parsed["from_phase"] = parsed["from_phase"] or "plan"
    return formal


def gate_checkpoint(root: Path, inputs: dict[str, Any]) -> dict[str, Any] | None:
    gate = inputs["gate"]
    if gate not in {"G3", "G5", "G6", "G7"} or not inputs.get("workflow_file"):
        return None
    formal = checkpoint_guard(root, str(inputs["workflow_file"]), "final" if gate == "G7" else "plan")
    if formal["complete"]:
        return None
    return {"gate": gate, "pass": False, "reason": "selected formal checkpoint is incomplete or stale", "formal_checkpoint": formal, "markers": 0, "details": []}


def complete_results(record: dict[str, Any], models: dict[str, Any]) -> bool:
    results = record.get("results")
    if not isinstance(results, list) or len(results) != len(models):
        return False
    if record.get("schema_version") != "1.0" or any(not isinstance(r, dict) for r in results):
        return False
    if [r.get("model") for r in results] != list(models):
        return False
    for result in results:
        expected = [o["id"] for o in obligations(models[result["model"]]["model"])]
        checks = result.get("obligations", [])
        if not isinstance(checks, list) or any(not isinstance(c, dict) for c in checks):
            return False
        if result.get("verdict") != "pass" or [c.get("id") for c in checks] != expected:
            return False
        if any(c.get("verdict") != "pass" or c.get("exit_code") != 0 for c in checks):
            return False
    return True


def check(root: Path, workflow: str, inputs: dict[str, Any], mode: str, context: dict[str, Any], writes: dict[str, bool]) -> dict[str, Any]:
    checkpoint = inputs.get("checkpoint", "plan")
    if checkpoint not in CHECKPOINT_ROWS:
        raise SelectionError("checkpoint must be plan, planning, final, or post")
    if context["verdict"] == "disabled" or context["gaps"]:
        return context
    spec = relative_input(root, inputs["spec_file"])
    plan = relative_input(root, inputs["plan_file"])
    before = fingerprint(root, context["selection"], context["models"], context["identities"], spec, plan)
    plans = {key: preview_model(root, item) for key, item in context["models"].items()}
    record = {"schema_version": "1.0", "workflow_file": workflow, "spec_file": spec, "plan_file": plan, "checkpoint": checkpoint, "fingerprint": before, "selection": context["selection"], "checkers": context["identities"], "verdict": "preview", "commands": plans, "results": []}
    if mode == "dry_run":
        return record
    record["verdict"] = "running"
    write_checkpoint(root, workflow, checkpoint, record, writes)
    record["results"] = []
    for key, item in context["models"].items():
        try:
            record["results"].append(execute_model(root, key, item))
        except (FormalError, OSError, subprocess.SubprocessError) as exc:
            record["results"].append({"model": key, "verdict": getattr(exc, "verdict", "inconclusive"), "reason": str(exc)})
    failures = [r["verdict"] for r in record["results"] if r["verdict"] != "pass"]
    record["verdict"] = failures[0] if failures else "pass"
    try:
        after = discover(root, workflow)
        changed = bool(after["gaps"]) or fingerprint(root, after["selection"], after["models"], after["identities"], spec, plan) != before
    except (ValueError, OSError, subprocess.SubprocessError):
        changed = True
    if changed:
        record["verdict"] = "stale"
    if record["verdict"] == "pass" and checkpoint in ("final", "post") and any(m["evidence"] == "model_and_trace" for m in context["selection"]["models"]):
        record["verdict"] = "missing_trace"
    write_checkpoint(root, workflow, checkpoint, record, writes)
    record["commit_paths"] = sorted({workflow, CATALOG_PATH, record_path(root, workflow, checkpoint).relative_to(root).as_posix(), *[p for item in context["models"].values() for p in item["model"]["inputs"]]})
    return record


def run_formal_helper(entry: Any, request: Any) -> dict[str, Any]:
    writes = {"writes_state": False}
    try:
        unknown = set(request.inputs) - {"repo_root", "workflow_file", "spec_file", "plan_file", "checkpoint"}
        if unknown:
            raise SelectionError(f"unknown formal inputs: {sorted(unknown)}")
        root = Path(request.inputs["repo_root"]).resolve(strict=True)
        workflow = relative_input(root, request.inputs["workflow_file"])
        context = discover(root, workflow)
        data = context if entry.helper_id == "formal-doctor" else check(root, workflow, request.inputs, request.mode, context, writes)
        data["helper_id"] = entry.helper_id
        data.update(writes)
        status = "ok" if data["verdict"] in ("disabled", "ready", "preview", "pass", "pending_authoring") else "expected_failure"
        if entry.helper_id == "formal-check" and data["verdict"] == "pending_authoring":
            status = "missing_prerequisite"
        return response(status, request_id=request.request_id, data=data)
    except FormalError as exc:
        return response("expected_failure", request_id=request.request_id, data={"verdict": exc.verdict, **writes}, diagnostics=[diagnostic(exc.verdict, str(exc))])
    except (SelectionError, ValueError, KeyError, TypeError, OSError, subprocess.TimeoutExpired, zipfile.BadZipFile) as exc:
        return response("input_error", request_id=request.request_id, data={"verdict": "invalid_configuration", **writes}, diagnostics=[diagnostic("formal_configuration", str(exc), remediation_summary="Repair the selected formal configuration; inspect any interrupted record before resuming Plan.")])
