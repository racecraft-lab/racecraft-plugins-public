"""Autopilot policy for formal checkpoints: resume constraints, gate ids, and Post step names.

The formal package answers whether a checkpoint is current; this module decides what
the autopilot does about it, next to the stage and gate helpers that call it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..formal.helper import checkpoint_guard
from ..formal.primitives import confined
from ..formal.selection import selection_from_workflow
from ..strict_input import SelectionError


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


def required_checkpoints(steps: list[tuple[str, str | None]]) -> list[str]:
    active = {name for name, status in steps if status in ("completed", "in_progress")}
    completed = {name for name, status in steps if status == "completed"}
    required = []
    if "Phase 3: Plan" in completed or any(name.startswith(("Phase 4:", "Phase 5:", "Phase 6:", "Phase 6.5:", "Phase 7:", "Post:")) for name in active):
        required.append("plan")
    if any(name.startswith("Post:") for name in active):
        required.append("final")
    after_integration = {"Post: Reviewability Diff Gate", "Post: UAT Runbook Generation", "Post: PR Body Generation", "Post: PR Creation", "Post: Review Remediation", "Post: Retrospective"}
    if "Post: Integration Suite" in completed or active & after_integration:
        required.append("post")
    return required


def coverage_errors(root: Path, workflow: str, state: dict[str, Any], steps: list[tuple[str, str | None]]) -> list[str]:
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
