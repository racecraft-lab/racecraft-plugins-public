"""Host-neutral planning dispatch facts; gate execution and stop policy stay separate."""

from __future__ import annotations

from typing import Any

from ..envelope import diagnostic, response
from ..strict_input import require_fields, require_text

PHASES = {
    "Specify": ("phase-executor", "G1", ()),
    "Clarify": ("clarify-executor", "G2", ("spec.md",)),
    "Plan": ("phase-executor", "G3", ("spec.md",)),
    "Checklist": ("checklist-executor", "G4", ("spec.md", "plan.md", "checklists/")),
    "Tasks": ("phase-executor", "G5", ("spec.md", "plan.md", "research.md", "data-model.md", "contracts/", "quickstart.md")),
    "Analyze": ("analyze-executor", "G6", ("spec.md", "plan.md", "tasks.md", "checklists/")),
}
PROMPT_SECTIONS = {"Clarify": "Clarify Prompts", "Checklist": "Step 2: Run Enriched Checklist Prompts"}


def run_phase_brief_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Return dispatch metadata without reading artifacts or deciding whether a run stops."""
    try:
        inputs = require_fields(request.inputs, {"phase", "workflow_file", "feature_dir"}, "phase-brief inputs")
        phase = require_text(inputs["phase"], "phase")
        workflow = require_text(inputs["workflow_file"], "workflow_file")
        feature = require_text(inputs["feature_dir"], "feature_dir").rstrip("/")
        if phase not in PHASES:
            raise ValueError("phase must be Specify, Clarify, Plan, Checklist, Tasks or Analyze")
    except ValueError as exc:
        return response("input_error", request_id=request.request_id,
                        diagnostics=[diagnostic("invalid_phase_brief", str(exc))])
    agent, gate, artifacts = PHASES[phase]
    instruction = "Prepare a Clarify Question Set for:" if phase == "Clarify" else f"Run the speckit-{phase.lower()} skill with:"
    return response("ok", request_id=request.request_id, data={
        "schema_version": "phase-brief/v1", "phase": phase, "agent": agent,
        "inputs": {"workflow_file": workflow, "feature_dir": feature,
                   "prompt_section": PROMPT_SECTIONS.get(phase, phase + " Prompt"), "instruction": instruction},
        "readable_files": [workflow, ".specify/memory/constitution.md"] + [feature + "/" + name for name in artifacts],
        "gate": gate, "slices": [], "waves": [], "model": None, "hooks": [],
    })
