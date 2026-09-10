"""Explicit waivers and durable formal evidence at existing phase boundaries."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .catalog import CATALOG_PATH, FormalError, confined, read_json, selected_catalog
from .evidence import CHECKPOINT_ROWS, atomic_record, fingerprint, read_checkpoint, record_path, write_checkpoint
from .selection import SelectionError, require_fields, require_text, selection_from_workflow


def recorded_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def record_time(record: dict[str, Any]) -> datetime | None:
    recorded_at = record.get("recorded_at")
    if not isinstance(recorded_at, str):
        return None
    try:
        value = datetime.fromisoformat(recorded_at)
    except ValueError:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        return None
    return value


def latest_planning_checkpoint(root: Path, workflow: str) -> str:
    candidates = []
    stale_candidates = []
    for checkpoint in ("plan", "planning"):
        for suffix in ("", "-waiver"):
            record = read_checkpoint(root, workflow, checkpoint + suffix)
            if isinstance(record, dict):
                timestamp = record_time(record)
                if timestamp is None:
                    stale_candidates.append(checkpoint)
                else:
                    candidates.append((timestamp, checkpoint))
    if candidates:
        return max(candidates)[1]
    return stale_candidates[-1] if stale_candidates else "plan"


def validate_waiver(value: Any) -> None:
    require_fields(value, {"operator_confirmed", "approved_by", "reason", "approval_reference"}, "operator waiver")
    if value["operator_confirmed"] is not True:
        raise SelectionError("A waiver requires explicit operator confirmation")
    for field in ("approved_by", "reason", "approval_reference"):
        require_text(value[field], f"waiver.{field}")


def waiver_material(root: Path, workflow: str, spec: str, plan: str, checkpoint: str) -> tuple[dict[str, Any], str, list[str]]:
    selection = selection_from_workflow(confined(root, workflow).read_text(encoding="utf-8"))
    if selection["status"] != "enabled":
        raise SelectionError("Disabled workflows do not need a formal waiver")
    models, gaps = selected_catalog(root, selection)
    if gaps:
        raise FormalError(gaps[0]["verdict"], "Complete the selected model catalog and inputs before binding an operator waiver")
    digest = fingerprint(root, selection, models, {}, spec, plan, checkpoint)
    paths = sorted({p for item in models.values() for p in item["model"]["inputs"]})
    return selection, digest, paths


def waive_checkpoint(root: Path, workflow: str, inputs: dict[str, Any], mode: str, writes: dict[str, bool] | None = None) -> dict[str, Any]:
    checkpoint = inputs.get("checkpoint", "plan")
    if checkpoint not in CHECKPOINT_ROWS:
        raise SelectionError("Unknown formal waiver checkpoint")
    validate_waiver(inputs["waiver"])
    spec, plan = inputs["spec_file"], inputs["plan_file"]
    selection, digest, paths = waiver_material(root, workflow, spec, plan, checkpoint)
    evidence = record_path(root, workflow, checkpoint + "-waiver")
    record = {"schema_version": "1.0", "workflow_file": workflow, "spec_file": spec, "plan_file": plan,
              "checkpoint": checkpoint, "selection": selection, "fingerprint": digest,
              "verdict": "preview" if mode == "dry_run" else "waived", "waiver": inputs["waiver"],
              "recorded_at": recorded_now(), "evidence": evidence.relative_to(root).as_posix()}
    if mode == "apply":
        write_checkpoint(root, workflow, checkpoint, record, writes)
        record["commit_paths"] = sorted({workflow, CATALOG_PATH, record["evidence"], *paths})
    return record


def current_waiver(root: Path, workflow: str, checkpoint: str, record: dict[str, Any], newer_time: datetime | None) -> dict[str, Any] | None:
    waiver_time = record_time(record)
    if waiver_time is None or (newer_time is not None and newer_time >= waiver_time):
        return None
    selection, digest, _ = waiver_material(root, workflow, record["spec_file"], record["plan_file"], checkpoint)
    if record.get("workflow_file") != workflow or record.get("checkpoint") != checkpoint:
        raise SelectionError("Formal waiver belongs to a different workflow or checkpoint")
    if record.get("fingerprint") != digest or record.get("selection") != selection:
        return None
    return {"required": True, "complete": True, "verdict": "waived", "checkpoint": checkpoint,
            "fingerprint": digest, "waiver": record["waiver"],
            "evidence": record_path(root, workflow, checkpoint + "-waiver").relative_to(root).as_posix()}


def waiver_status(root: Path, workflow: str, checkpoint: str) -> dict[str, Any] | None:
    record = read_checkpoint(root, workflow, checkpoint + "-waiver")
    newer = read_checkpoint(root, workflow, checkpoint)
    newer_time = record_time(newer) if isinstance(newer, dict) else None
    if record is not None:
        if not isinstance(record, dict) or record.get("schema_version") != "1.0" or record.get("verdict") != "waived":
            raise SelectionError("Malformed formal operator waiver")
        validate_waiver(record.get("waiver"))
        waived = current_waiver(root, workflow, checkpoint, record, newer_time)
        if waived is not None:
            return waived
    stale_checkpoint = None
    if isinstance(newer, dict) and newer_time is None:
        stale_checkpoint = checkpoint
    elif record is not None and record_time(record) is None and not isinstance(newer, dict):
        stale_checkpoint = checkpoint + "-waiver"
    if stale_checkpoint is None:
        return None
    return {"required": True, "complete": False, "verdict": "stale", "checkpoint": checkpoint,
            "resume": "plan", "evidence": record_path(root, workflow, stale_checkpoint).relative_to(root).as_posix()}


def state_path(root: Path, workflow: str, value: str) -> Path:
    path = confined(root, value)
    if path.name != "autopilot-state.json" or path.parent != confined(root, workflow).parent:
        raise SelectionError("state_file must be autopilot-state.json beside the workflow")
    if not isinstance(read_json(path), dict):
        raise SelectionError("autopilot state must be an existing JSON object")
    return path


def mirror_checkpoint(root: Path, workflow: str, value: str, record: dict[str, Any]) -> None:
    path = state_path(root, workflow, value)
    state = read_json(path)
    formal = state.get("formal_checkpoints", {})
    if not isinstance(formal, dict) or not isinstance(formal.get("checkpoints", {}), dict):
        raise SelectionError("Malformed formal_checkpoints state mirror")
    checkpoints = formal.get("checkpoints", {})
    checkpoint = record["checkpoint"]
    checkpoints[checkpoint] = {key: record[key] for key in ("verdict", "fingerprint", "evidence")}
    state["formal_checkpoints"] = {"schema_version": "1.0", "workflow_file": workflow,
                                   "selection": record["selection"], "checkpoints": checkpoints}
    atomic_record(path, state)


def required_checkpoints(steps: list[tuple[str, str | None]]) -> list[str]:
    active = {name for name, status in steps if status in ("completed", "in_progress")}
    completed = {name for name, status in steps if status == "completed"}
    required = []
    if "Phase 3: Plan" in completed or any(name.startswith(("Phase 4:", "Phase 5:", "Phase 6:", "Phase 6.5:", "Phase 7:", "Post:")) for name in active):
        required.append("plan")
    if any(name.startswith("Post:") for name in active):
        required.append("final")
    after_integration = {"Post: Reviewability Diff Gate", "Post: Self-Review", "Post: UAT Runbook Generation", "Post: PR Body Generation", "Post: PR Creation", "Post: Review Remediation", "Post: Retrospective"}
    if "Post: Integration Suite" in completed or active & after_integration:
        required.append("post")
    return required


def coverage_errors(root: Path, workflow: str, state: dict[str, Any], steps: list[tuple[str, str | None]]) -> list[str]:
    from .helper import checkpoint_guard

    selection = selection_from_workflow(confined(root, workflow).read_text(encoding="utf-8"))
    if selection["status"] != "enabled":
        return []
    errors = []
    formal = state.get("formal_checkpoints", {})
    for checkpoint in required_checkpoints(steps):
        current = checkpoint_guard(root, workflow, checkpoint)
        if not current["complete"]:
            errors.append(f"formal {checkpoint} is {current['verdict']}; reconcile and rerun the selected checkpoint")
            continue
        if not isinstance(formal, dict) or formal.get("selection") != selection or formal.get("workflow_file") != workflow or formal.get("schema_version") != "1.0":
            errors.append("formal state mirror is missing or differs from the workflow selection")
            continue
        mirrors = formal.get("checkpoints", {})
        expected = {key: current[key] for key in ("verdict", "fingerprint", "evidence")}
        if not isinstance(mirrors, dict) or mirrors.get(current["checkpoint"]) != expected:
            errors.append(f"formal {checkpoint} state mirror differs from current evidence")
    return errors
