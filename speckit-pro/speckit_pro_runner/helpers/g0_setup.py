"""G0's setup probes, quality-gates stop, and the project baseline plan, without setup writes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..envelope import response
from ..strict_input import SelectionError, require_fields, require_text
from ..trusted_io import resolve_repo_root, validate_bounded_inputs
from .read_only import (
    BASELINE_SLOTS, EXIT_STATUS, check_prerequisites, detect_commands, detect_presets, helper_failure_diagnostic, output_capture,
)

PROBES = {
    "prerequisites": ("check-prerequisites", check_prerequisites),
    "commands": ("detect-commands", detect_commands),
    "presets": ("detect-presets", detect_presets),
}


def baseline_plan(commands: dict[str, str], project_commands: Any) -> dict[str, Any]:
    """Plan the baseline from detected commands with recorded commands taking precedence."""
    if not isinstance(project_commands, dict):
        raise SelectionError("project_commands must be an object")
    recorded = {require_text(slot, "project_commands slot"): require_text(command, "project_commands command")
                for slot, command in project_commands.items()}
    effective = commands | recorded
    return {"plan_stage": [], "implement_entry": [
        {"slot": slot, "command": effective[slot]} for slot in BASELINE_SLOTS if effective.get(slot, "N/A") != "N/A"
    ]}


def g0_setup(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    """Preserve each probe's result; commands also reports the current G0 stop."""
    optional = {"repo_root", "project_commands"} if inputs.get("probe") == "commands" else {"repo_root"}
    require_fields({key: value for key, value in inputs.items() if key not in optional},
                   {"probe", "surface", "workflow_file"}, "g0-setup inputs")
    probe = require_text(inputs["probe"], "probe")
    surface = require_text(inputs["surface"], "surface")
    if probe not in PROBES or surface not in {"claude", "codex"}:
        raise SelectionError("probe must be prerequisites, commands, or presets; surface must be claude or codex")
    workflow = require_text(inputs["workflow_file"], "workflow_file")
    helper_id, run_probe = PROBES[probe]
    legacy_inputs = {"workflow_file": workflow}
    problem = validate_bounded_inputs(helper_id, legacy_inputs, repo_root)
    if problem is not None:
        raise SelectionError(problem["message"])
    result = run_probe(legacy_inputs, repo_root)
    result["stdout_json"] = json.loads(result.pop("stdout"))
    data: dict[str, Any] = {"probe": probe, "result": result}
    if probe == "commands":
        quality = result["stdout_json"]["quality_gates"]
        gate = {"verdict": "proceed", "message": ""}
        if quality["status"] != "present":
            detail = "missing" if quality["status"] == "missing" else f"invalid: {quality['problems'][0]}"
            sigil = "/" if surface == "claude" else "$"
            gate = {"verdict": "stop", "message": (
                f"G0 blocked: .specify/quality-gates.json is {detail}.\n"
                f"Run `{sigil}speckit-pro:speckit-coach quality gates` to create it. Agents never edit this file."
            )}
        data["quality_gate"] = gate
        data["baseline"] = baseline_plan(result["stdout_json"]["commands"], inputs.get("project_commands", {}))
    return data


def run_g0_setup_helper(entry: Any, request: Any) -> dict[str, Any]:
    root = resolve_repo_root(request.inputs)
    if isinstance(root, dict):
        status = "missing_prerequisite" if root["code"] == "missing_prerequisite" else "input_error"
        return response(status, request_id=request.request_id, diagnostics=[root])
    try:
        data = g0_setup(request.inputs, root)
    except SelectionError as exc:
        return response("input_error", request_id=request.request_id, data={"problems": [str(exc)]})
    # Prerequisite failures still go to repair. The quality stop is consumed
    # at Step 0.11, after the same earlier setup work as before this seam.
    exit_code = int(data["result"]["exit_code"])
    if exit_code == 0:
        return response("ok", request_id=request.request_id, data=data)
    # Same status and diagnostic the standalone probe reported for a failure.
    stdout = output_capture(json.dumps(data["result"]["stdout_json"]))
    stderr = output_capture(data["result"]["stderr"])
    helper_id = PROBES[data["probe"]][0]
    return response(
        EXIT_STATUS.get(exit_code, "subprocess_failure"), request_id=request.request_id, data=data,
        diagnostics=[helper_failure_diagnostic(helper_id, exit_code, stdout, stderr)],
    )
