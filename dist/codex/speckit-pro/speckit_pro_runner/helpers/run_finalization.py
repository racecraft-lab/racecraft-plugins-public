"""Decide how an autopilot run ends once no runnable work remains.

A run that finished every runnable task and Post check, and holds only deferred
or fallback items, is done: its pull-request stack goes ready for review (never
merged), the top PR body opens with a "Deferred / not verified" section, the
goal is marked complete, and one plain-text request names what is left.

This read-only helper derives that decision from the execution-control
ledger's `deferred` list, the blocked-action deferrals the parent recorded, and
the final gate results. A gate that failed only on deferred units is reported
as deferred, never green; any other failure blocks. It fails closed on
missing or malformed evidence and never writes a file.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response
from ..execution_control import confined_path, require_text, validate_ledger

ALLOWED_INPUTS = frozenset({"repo_root", "ledger_path", "expected_run_id", "gates", "pending_items",
                            "blocked_action_deferrals", "pull_requests", "resume_command"})
GATE_STATUSES = ("passed", "failed")
DEFERRAL_FIELDS = ("unit", "reason", "finish")
UNIT_LABELS = {"failure_family": "Failure family", "failure_class": "Failure class",
               "increment": "Increment", "gate": "Gate"}
REASON_TEXT = {
    "failure_family_budget_exhausted": "Its correction allowance is spent and the last correction made no "
                                       "measurable progress.",
    "corrective_run_budget_exhausted": "The run-wide correction allowance is spent.",
    "corrective_cycle_failed_no_nested_retry": "Its correction cycle failed, and a failed cycle gets no nested retry.",
    "corrective_cycle_already_closed": "Its correction cycle is already closed.",
    "increment_review_allowance_exhausted": "Its review-fix rounds are spent with findings still open.",
    "gate_remediation_allowance_exhausted": "Its remediation rounds are spent with findings still open.",
    "failure_class_allowance_exhausted": "Its failure-class follow-ups are spent.",
}


def _text(value: Any, field: str) -> str:
    return require_text(value, field).strip()


def _ledger_deferrals(root: Path, inputs: dict[str, Any]) -> list[dict[str, Any]]:
    relative = _text(inputs.get("ledger_path"), "ledger_path")
    if Path(relative).parent.name != "execution-control" or Path(relative).suffix != ".json":
        raise ValueError("ledger_path must reference an owned execution-control JSON record")
    path = confined_path(root, relative)
    if not path.is_file():
        raise ValueError("ledger_path must name an existing execution-control ledger")
    ledger = json.loads(path.read_text(encoding="utf-8"))
    validate_ledger(ledger)
    if ledger["run_id"] != _text(inputs.get("expected_run_id"), "expected_run_id"):
        raise ValueError("expected_run_id does not match the ledger")
    return list(ledger.get("deferred", []))


def _blocked_action_deferrals(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ValueError("blocked_action_deferrals must be a list")
    items: list[dict[str, str]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, dict) or set(raw) != set(DEFERRAL_FIELDS):
            raise ValueError(f"blocked_action_deferrals[{index}] must have exactly unit, reason, and finish")
        items.append({field: _text(raw[field], f"blocked_action_deferrals[{index}].{field}")
                      for field in DEFERRAL_FIELDS})
    return items


def _gates(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("gates must list every final gate result; a run never finalizes on no evidence")
    gates: list[dict[str, Any]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, dict) or not set(raw) <= {"gate", "status", "attributed_units"}:
            raise ValueError(f"gates[{index}] must have gate, status, and optional attributed_units")
        status = raw.get("status")
        if status not in GATE_STATUSES:
            raise ValueError(f"gates[{index}].status must be passed or failed")
        units = raw.get("attributed_units", [])
        if not isinstance(units, list):
            raise ValueError(f"gates[{index}].attributed_units must be a list")
        if status == "passed" and units:
            raise ValueError(f"gates[{index}] passed, so it attributes no failure")
        gates.append({"gate": _text(raw.get("gate"), f"gates[{index}].gate"), "status": status,
                      "attributed_units": [_text(unit, f"gates[{index}].attributed_units") for unit in units]})
    return gates


def _pull_requests(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("pull_requests must list the run's stack, bottom first")
    prs: list[dict[str, Any]] = []
    for index, raw in enumerate(value):
        if (not isinstance(raw, dict) or set(raw) != {"number", "url", "draft"}
                or type(raw["number"]) is not int or raw["number"] < 1 or type(raw["draft"]) is not bool):
            raise ValueError(f"pull_requests[{index}] must have a positive number, a url, and a boolean draft")
        prs.append({"number": raw["number"], "url": _text(raw["url"], f"pull_requests[{index}].url"),
                    "draft": raw["draft"]})
    return prs


def _ledger_item(entry: dict[str, Any], resume_command: str) -> dict[str, str]:
    unit = str(entry["unit"])
    return {
        "item": f"{UNIT_LABELS.get(entry['unit_kind'], entry['unit_kind'])} {unit}",
        "reason": f"{REASON_TEXT.get(entry['reason'], 'Its correction allowance is spent.')} ({entry['reason']})",
        "finish": f"Reply approving one `authorize-corrective-exception` for {unit}, or a re-plan with "
                  f"`begin-replan-epoch`, then resume with: {resume_command}",
    }


def render_request(items: list[dict[str, str]], resume_command: str) -> str:
    """The one consolidated end-of-run request, as plain text."""
    lines = ["The run is finished: every runnable task and Post check is done, and the pull request stack is "
             "ready for review. Nothing was merged. These items are deferred and not verified:", ""]
    for number, item in enumerate(items, start=1):
        lines.extend([f"{number}. {item['item']}: {item['reason']}", f"   To finish it: {item['finish']}"])
    lines.extend(["", "Reply in this thread with the approval or answer for any item. "
                  f"The run then resumes with: {resume_command}"])
    return "\n".join(lines) + "\n"


def finalize_run(root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    """The run's terminal decision; raises ValueError on missing or malformed evidence."""
    if not isinstance(inputs, dict):
        raise ValueError("inputs must be an object")
    unknown = sorted(set(inputs) - ALLOWED_INPUTS)
    if unknown:
        raise ValueError(f"unknown inputs: {', '.join(unknown)}")
    resume_command = _text(inputs.get("resume_command"), "resume_command")
    ledger_deferrals = _ledger_deferrals(root, inputs)
    blocked = _blocked_action_deferrals(inputs.get("blocked_action_deferrals", []))
    gates = _gates(inputs.get("gates"))
    prs = _pull_requests(inputs.get("pull_requests"))
    pending = inputs.get("pending_items")
    if not isinstance(pending, list):
        raise ValueError("pending_items must list the runnable work still open, or be empty")
    pending_items = [_text(item, "pending_items") for item in pending]

    deferred_units = {str(entry["unit"]) for entry in ledger_deferrals} | {item["unit"] for item in blocked}
    for gate in gates:
        units = gate["attributed_units"]
        gate["result"] = ("passed" if gate["status"] == "passed"
                          else "deferred" if units and set(units) <= deferred_units else "failed")
    items = [_ledger_item(entry, resume_command) for entry in ledger_deferrals]
    items.extend({"item": item["unit"], "reason": item["reason"], "finish": item["finish"]} for item in blocked)

    if pending_items:
        outcome = "continue"
    elif any(gate["result"] == "failed" for gate in gates):
        outcome = "blocked"
    else:
        outcome = "complete_with_deferred" if items else "complete"
    finalized = outcome in {"complete", "complete_with_deferred"}
    digest = "sha256:" + hashlib.sha256(json.dumps(items, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "outcome": outcome,
        "goal_status": "complete" if finalized else "not_complete",
        "finalized": finalized,
        "mark_ready": finalized,
        "ready_commands": [f"gh pr ready {pr['number']}" for pr in prs if pr["draft"]] if finalized else [],
        "top_pull_request": prs[-1]["url"],
        "gates": gates,
        "pending_items": pending_items,
        "deferred_items": items,
        "deferred_digest": digest,
        "end_of_run_request": render_request(items, resume_command) if finalized and items else "",
        "writes_state": False,
    }


def run_run_finalization_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Runner helper entry point: reads one ledger, writes nothing."""
    from .read_only import resolve_repo_root

    inputs = request.inputs if isinstance(request.inputs, dict) else {}
    root = resolve_repo_root(inputs)
    if isinstance(root, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[root])
    try:
        data = finalize_run(root, request.inputs)
    except (ValueError, OSError, TypeError, KeyError) as error:
        return response(
            "input_error",
            request_id=request.request_id,
            diagnostics=[
                diagnostic(
                    "invalid_input",
                    str(error),
                    remediation_summary="Pass the run's execution-control ledger, every final gate result, "
                    + "the open runnable work, every blocked-action deferral, and the pull-request stack.",
                    remediation_actions=["Correct the named input.", "Rerun finalize-run."],
                )
            ],
        )
    data.update(helper_id=entry.helper_id, operation=entry.operation)
    return response("ok", request_id=request.request_id, data=data)
