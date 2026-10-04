"""G0's setup probes and its unratified quality-gate defaults observation, without setup writes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..envelope import response
from ..strict_input import SelectionError, require_fields, require_text
from ..trusted_io import resolve_repo_root, validate_bounded_inputs
from .read_only import (
    EXIT_STATUS, check_prerequisites, detect_commands, detect_presets, helper_failure_diagnostic, output_capture,
)

SHIPPED_DEFAULTS = "complexity 10, CRAP 30, mutation-score floor 60, no skips, no opt-in slots"
PROBES = {
    "prerequisites": ("check-prerequisites", check_prerequisites),
    "commands": ("detect-commands", detect_commands),
    "presets": ("detect-presets", detect_presets),
}


def g0_setup(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    """Preserve each probe's result; commands also reports an unratified-defaults observation."""
    require_fields({key: value for key, value in inputs.items() if key != "repo_root"},
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
        gate: dict[str, Any] = {"verdict": "proceed", "message": ""}
        if quality["status"] != "present":
            gate["unratified_defaults"] = unratified_defaults(quality, surface)
        data["quality_gate"] = gate
    return data


def unratified_defaults(quality: dict[str, Any], surface: str) -> dict[str, Any]:
    """The observation for a missing or invalid file: G0 runs on the shipped defaults (ADR 0007)."""
    problem = " ".join(str(quality.get("problems", [""])[0]).split())[:300] or "no detail"
    detail = "missing" if quality["status"] == "missing" else f"invalid: {problem}"
    sigil = "/" if surface == "claude" else "$"
    return {
        "flag": (f"Unratified quality-gate defaults: .specify/quality-gates.json is {detail}; "
                 f"this run used the shipped defaults ({SHIPPED_DEFAULTS}). "
                 f"Run `{sigil}speckit-pro:speckit-coach quality gates` to ratify them."),
        "decision": {
            "kind": "unratified_default",
            "option_chosen": f"Ran G0 on the shipped quality-gate defaults ({SHIPPED_DEFAULTS}).",
            "rejected_alternative": "Stopping G0 until the quality-gates file is created.",
            "evidence": f".specify/quality-gates.json is {detail}.",
            "affected_unit": ".specify/quality-gates.json",
        },
    }


def run_g0_setup_helper(entry: Any, request: Any) -> dict[str, Any]:
    root = resolve_repo_root(request.inputs)
    if isinstance(root, dict):
        status = "missing_prerequisite" if root["code"] == "missing_prerequisite" else "input_error"
        return response(status, request_id=request.request_id, diagnostics=[root])
    try:
        data = g0_setup(request.inputs, root)
    except SelectionError as exc:
        return response("input_error", request_id=request.request_id, data={"problems": [str(exc)]})
    # Prerequisite failures still go to repair. The quality observation is
    # consumed at Step 0.11, after the same earlier setup work as before this seam.
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
