"""G0 setup probes, readiness read, unratified-defaults observation, and project baseline plan, without setup writes."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..envelope import response
from ..quality_gates import SHIPPED_DEFAULTS
from ..strict_input import SelectionError, require_fields, require_text
from ..trusted_io import resolve_repo_root, validate_bounded_inputs
from .decisions_list import decisions_list, recorded
from .readiness_record import FRESH_ITEMS, RECORD_DIRECTORY, stale_items
from .read_only import (
    BASELINE_SLOTS, EXIT_STATUS, check_prerequisites, detect_commands, detect_presets, helper_failure_diagnostic, output_capture,
)

UNSAFE_TEXT = re.compile(r"[^A-Za-z0-9 _.,:;'=>()-]")
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
    """Preserve each probe, the unratified-defaults observation, and the baseline plan."""
    optional = {"repo_root", "project_commands"} if inputs.get("probe") == "commands" else {"repo_root"}
    require_fields({key: value for key, value in inputs.items() if key not in optional},
                   {"probe", "surface", "workflow_file"}, "g0-setup inputs")
    probe = require_text(inputs["probe"], "probe")
    surface = require_text(inputs["surface"], "surface")
    if probe not in {*PROBES, "readiness"} or surface not in {"claude", "codex"}:
        raise SelectionError("probe must be readiness, prerequisites, commands, or presets; surface must be claude or codex")
    workflow = require_text(inputs["workflow_file"], "workflow_file")
    if probe == "readiness":
        return {"probe": probe, "readiness": readiness(repo_root, surface, workflow)}
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
            observed = unratified_defaults(quality, surface)
            entries = decisions_list(repo_root, {"workflow_file": workflow}, "read_only")["entries"]
            observed["record_decision"] = not recorded(observed["decision"], entries)
            gate["unratified_defaults"] = observed
        data["quality_gate"] = gate
        data["baseline"] = baseline_plan(result["stdout_json"]["commands"], inputs.get("project_commands", {}))
    return data


def readiness(root: Path, surface: str, workflow: str) -> dict[str, Any]:
    """G0 reads the readiness record and continues: each stale item is one decisions-list note (ADR 0008)."""
    stale = [{"item": item, "reason": reason} for item, reason in stale_items(root, surface)]
    entries = decisions_list(root, {"workflow_file": workflow}, "read_only")["entries"]
    decisions = [{
        "kind": "readiness_stale",
        "option_chosen": "Continued G0 on safe defaults without this readiness evidence.",
        "rejected_alternative": "Stopping G0 to ask a setup question or to rerun scaffold.",
        "evidence": f"readiness stale: {row['item']}: {row['reason']}",
        "affected_unit": f"{RECORD_DIRECTORY}/{surface}.json",
    } for row in stale]
    return {"verdict": "proceed", "stale": stale, "observe_fresh": list(FRESH_ITEMS),
            "decisions": [decision for decision in decisions if not recorded(decision, entries)]}


def unratified_defaults(quality: dict[str, Any], surface: str) -> dict[str, Any]:
    """The observation for a missing or invalid file: G0 runs on the shipped defaults (ADR 0007)."""
    # The problem text can quote keys from the file. Keep plain words only, so it
    # cannot carry markup, links, mentions, control characters, or paths into the PR.
    problem = " ".join(UNSAFE_TEXT.sub("?", str(quality.get("problems", [""])[0])).split())[:300] or "no detail"
    detail = "missing" if quality["status"] == "missing" else f"invalid: {problem}"
    sigil = "/" if surface == "claude" else "$"
    defaults = (f"complexity {SHIPPED_DEFAULTS['complexity']}, CRAP {SHIPPED_DEFAULTS['crap']}, "
                f"mutation-score floor {SHIPPED_DEFAULTS['mutation_score_floor']}, no skips, no opt-in slots")
    return {
        "flag": (f"Unratified quality-gate defaults: .specify/quality-gates.json is {detail}; "
                 f"this run used the shipped defaults ({defaults}). "
                 f"Run `{sigil}speckit-pro:speckit-coach quality gates` to ratify them."),
        "decision": {
            "kind": "unratified_default",
            "option_chosen": f"Ran G0 on the shipped quality-gate defaults ({defaults}).",
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
    exit_code = int(data["result"]["exit_code"]) if "result" in data else 0
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
