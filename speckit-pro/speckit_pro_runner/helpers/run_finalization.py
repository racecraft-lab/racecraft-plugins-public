"""Decide how an autopilot run ends once no runnable work remains.

Human UAT is the only gate a run may defer. A run whose non-UAT gates all
passed and that holds no unresolved deferral is done: its pull-request stack
goes ready for review (never merged), the top PR body opens with a
"Deferred / not verified" section listing the human UAT, the goal is marked
complete, and one plain-text request names what is left.

Anything else left at the end is one human stop, never ready for review: a
failed gate (named with its exact command), an unresolved entry in the
execution-control ledger's `deferred` list, or a deferred task nobody resolved.
A ledger entry is resolved only when the ledger itself shows a later completed
dispatch for the same unit; it stays in the ledger for audit but leaves the stop. A `defer`
disposition keeps the run working on other units mid-run; it never survives to
a finalized run. This read-only helper fails closed on missing or malformed
evidence and never writes a file.

Every gate result names the PR head (`head_sha`) it ran at. A stack finalizes
only when every PR head passed every non-UAT gate reported for any head, so a
stack verified only at its tip is a human stop naming each head and gate left
unverified. Evidence from one head never stands in for another.

A harness or tooling error that blocks a gate is retried up to
HARNESS_RETRY_BUDGET attempts. If it persists, the gate reports status
`harness_error` with its `attempts` and the `evidence` path under a
`.process/verification/` directory holding each attempt's raw error and trace.
A harness error never counts as passed; the one human stop reports it as a
harness error, never as a failure of the code under test, and cites that path.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from ..envelope import diagnostic, response
from ..execution_control import confined_path, require_text, validate_ledger
from ..sweep_isolation import HEX_OBJECT_RE

ALLOWED_INPUTS = frozenset({"repo_root", "ledger_path", "expected_run_id", "gates", "pending_items",
                            "unresolved_deferrals", "human_uat", "pull_requests", "resume_command"})
GATE_STATUSES = ("passed", "failed", "harness_error")
GATE_FIELDS = {"gate", "status", "command", "head_sha"}
HARNESS_FIELDS = GATE_FIELDS | {"attempts", "evidence"}
HARNESS_RETRY_BUDGET = 3
DEFERRAL_FIELDS = ("unit", "reason", "finish")
UAT_FIELDS = ("item", "reason", "finish")
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
    # A resolved entry stays in the ledger for audit; validate_ledger proved its resolution.
    return [entry for entry in ledger.get("deferred", []) if "resolved_by" not in entry]


def _records(value: Any, name: str, fields: tuple[str, ...]) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    records: list[dict[str, str]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, dict) or set(raw) != set(fields):
            raise ValueError(f"{name}[{index}] must have exactly {', '.join(fields)}")
        records.append({field: _text(raw[field], f"{name}[{index}].{field}") for field in fields})
    return records


def _head(value: Any, field: str) -> str:
    if not isinstance(value, str) or HEX_OBJECT_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be the full lowercase commit SHA of a PR head")
    return value


def _harness_evidence(root: Path, value: Any, field: str) -> str:
    """An existing path under a `.process/verification/` directory, which the runner keeps out of commits."""
    relative = _text(value, field)
    parts = PurePosixPath(relative).parts
    if (".process", "verification") not in zip(parts, parts[1:], strict=False):
        raise ValueError(f"{field} must sit under a .process/verification/ directory")
    if not confined_path(root, relative).exists():
        raise ValueError(f"{field} must name the retained raw errors and traces; a harness error needs its evidence")
    return relative


def _gates(root: Path, value: Any, heads: set[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("gates must list every final non-UAT gate result; a run never finalizes on no evidence")
    gates: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(value):
        if not isinstance(raw, dict) or raw.get("status") not in GATE_STATUSES:
            raise ValueError(f"gates[{index}].status must be passed, failed, or harness_error; "
                             + "only human UAT may be deferred")
        if raw["status"] == "harness_error":
            if set(raw) != HARNESS_FIELDS:
                raise ValueError(f"gates[{index}] must have exactly gate, status, command, head_sha, attempts, "
                                 + "and evidence")
        elif set(raw) != GATE_FIELDS:
            raise ValueError(f"gates[{index}] must have exactly gate, status, command, and head_sha")
        gate: dict[str, Any] = {"gate": _text(raw["gate"], f"gates[{index}].gate"), "status": raw["status"],
                                "command": _text(raw["command"], f"gates[{index}].command"),
                                "head_sha": _head(raw["head_sha"], f"gates[{index}].head_sha")}
        if raw["status"] == "harness_error":
            if type(raw["attempts"]) is not int or raw["attempts"] < HARNESS_RETRY_BUDGET:
                raise ValueError(f"gates[{index}].attempts must show the harness retry budget of "
                                 + f"{HARNESS_RETRY_BUDGET} attempts was spent before reporting harness_error")
            gate.update(attempts=raw["attempts"],
                        evidence=_harness_evidence(root, raw["evidence"], f"gates[{index}].evidence"))
        if gate["head_sha"] not in heads:
            raise ValueError(f"gates[{index}].head_sha is not the head of any listed pull request; "
                             + "evidence from another head never counts")
        if (gate["head_sha"], gate["gate"]) in seen:
            raise ValueError(f"gates[{index}] repeats gate {gate['gate']} at one head; pass its final result once")
        seen.add((gate["head_sha"], gate["gate"]))
        gates.append(gate)
    return gates


def _pull_requests(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("pull_requests must list the run's stack, bottom first")
    prs: list[dict[str, Any]] = []
    for index, raw in enumerate(value):
        if (not isinstance(raw, dict) or set(raw) != {"number", "url", "draft", "head_sha"}
                or type(raw["number"]) is not int or raw["number"] < 1 or type(raw["draft"]) is not bool):
            raise ValueError(f"pull_requests[{index}] must have a positive number, a url, a boolean draft, "
                             + "and its head_sha")
        prs.append({"number": raw["number"], "url": _text(raw["url"], f"pull_requests[{index}].url"),
                    "draft": raw["draft"], "head_sha": _head(raw["head_sha"], f"pull_requests[{index}].head_sha")})
    if len({pr["head_sha"] for pr in prs}) != len(prs):
        raise ValueError("pull_requests must each have their own head_sha")
    return prs


def _missing(prs: list[dict[str, Any]], gates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Each PR head without a result for a gate that any head reported."""
    commands: dict[str, str] = {}
    for gate in sorted(gates, key=lambda record: record["command"]):
        commands.setdefault(gate["gate"], gate["command"])
    reported = {(gate["head_sha"], gate["gate"]) for gate in gates}
    return [{"pull_request": pr["number"], "head_sha": pr["head_sha"], "gate": name, "command": command}
            for pr in prs for name, command in sorted(commands.items())
            if (pr["head_sha"], name) not in reported]


def _ledger_item(entry: dict[str, Any], resume_command: str) -> dict[str, str]:
    unit = str(entry["unit"])
    return {
        "unit": f"{UNIT_LABELS.get(entry['unit_kind'], entry['unit_kind'])} {unit}",
        "reason": f"{REASON_TEXT.get(entry['reason'], 'Its correction allowance is spent.')} ({entry['reason']})",
        "finish": f"Reply approving one `authorize-corrective-exception` for {unit}, or a re-plan with "
                  f"`begin-replan-epoch`, then resume with: {resume_command}",
    }


def _canonical(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Records in one order that does not depend on the order the caller listed them."""
    return sorted(records, key=lambda record: json.dumps(record, sort_keys=True))


def render_request(items: list[dict[str, str]], resume_command: str) -> str:
    """The end-of-run request of a finalized run, as plain text."""
    lines = ["The run is finished: every runnable task and gate is done, and the pull request stack is ready "
             + "for review. Nothing was merged. This human UAT is deferred and not verified:", ""]
    for number, item in enumerate(items, start=1):
        lines.extend([f"{number}. {item['item']}: {item['reason']}", f"   To finish it: {item['finish']}"])
    lines.extend(["", f"Reply in this thread with any finding. The run resumes with: {resume_command}"])
    return "\n".join(lines) + "\n"


def render_stop(stop: dict[str, list[dict[str, Any]]], resume_command: str) -> str:
    """The run's one human stop, as plain text."""
    lines = ["The run stopped, and its pull request stack stays in draft. Nothing was merged.", ""]
    number = 0
    for gate in stop["gates"]:
        number += 1
        lines.extend([f"{number}. Gate {gate['gate']} failed after its retries at head {gate['head_sha']} "
                      + f"of PR #{gate['pull_request']}.", f"   Command: {gate['command']}"])
    for gate in stop["missing"]:
        number += 1
        lines.extend([f"{number}. Gate {gate['gate']} has no result at head {gate['head_sha']} of PR "
                      + f"#{gate['pull_request']}.", f"   Run it at that head: {gate['command']}"])
    for gate in stop["harness_errors"]:
        number += 1
        lines.extend([f"{number}. Gate {gate['gate']} could not run at head {gate['head_sha']} of PR "
                      + f"#{gate['pull_request']}: a harness error persisted through {gate['attempts']} attempts. "
                      + "This is a harness error, not a failure of the code under test.",
                      f"   Command: {gate['command']}",
                      f"   Raw errors and traces: {gate['evidence']}"])
    for unit in stop["units"]:
        number += 1
        lines.extend([f"{number}. {unit['unit']} is unresolved: {unit['reason']}", f"   To finish it: {unit['finish']}"])
    lines.extend(["", f"Reply in this thread with the fix or authorization. The run resumes with: {resume_command}"])
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
    unresolved = _records(inputs.get("unresolved_deferrals", []), "unresolved_deferrals", DEFERRAL_FIELDS)
    human_uat = _records(inputs.get("human_uat", []), "human_uat", UAT_FIELDS)
    prs = _pull_requests(inputs.get("pull_requests"))
    gates = _gates(root, inputs.get("gates"), {pr["head_sha"] for pr in prs})
    numbers = {pr["head_sha"]: pr["number"] for pr in prs}
    pending = inputs.get("pending_items")
    if not isinstance(pending, list):
        raise ValueError("pending_items must list the runnable work still open, or be empty")
    pending_items = [_text(item, "pending_items") for item in pending]

    # Canonical order, so the same blocker listed another way has the same digest and request text.
    stop = {"gates": _canonical([{"gate": gate["gate"], "command": gate["command"],
                                  "pull_request": numbers[gate["head_sha"]], "head_sha": gate["head_sha"]}
                                 for gate in gates if gate["status"] == "failed"]),
            "missing": _canonical(_missing(prs, gates)),
            "harness_errors": _canonical([{"gate": gate["gate"], "command": gate["command"],
                                           "pull_request": numbers[gate["head_sha"]], "head_sha": gate["head_sha"],
                                           "attempts": gate["attempts"], "evidence": gate["evidence"]}
                                          for gate in gates if gate["status"] == "harness_error"]),
            "units": _canonical([_ledger_item(entry, resume_command) for entry in ledger_deferrals] + unresolved)}
    human_uat = _canonical(human_uat)
    if pending_items:
        outcome = "continue"
    elif any(stop.values()):
        outcome = "human_stop"
    else:
        outcome = "complete_with_deferred" if human_uat else "complete"
    finalized = outcome in {"complete", "complete_with_deferred"}
    request = (render_request(human_uat, resume_command) if finalized and human_uat
               else render_stop(stop, resume_command) if outcome == "human_stop" else "")
    digest = "sha256:" + hashlib.sha256(json.dumps([stop, human_uat], sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "outcome": outcome,
        "goal_status": "complete" if finalized else "blocked" if outcome == "human_stop" else "not_complete",
        "finalized": finalized,
        "mark_ready": finalized,
        "ready_commands": [f"gh pr ready {pr['number']}" for pr in prs if pr["draft"]] if finalized else [],
        "top_pull_request": prs[-1]["url"],
        "gates": gates,
        "pull_requests": [{**pr, "gates": [gate for gate in gates if gate["head_sha"] == pr["head_sha"]]}
                          for pr in prs],
        "pending_items": pending_items,
        "human_stop": stop if outcome == "human_stop" else None,
        "deferred_items": human_uat,
        "deferred_digest": digest,
        "end_of_run_request": request,
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
                    remediation_summary="Pass the run's execution-control ledger, every final non-UAT gate result "
                    + "with its command and the PR head it ran at, the open runnable work, every unresolved "
                    + "deferral, the human UAT, and the pull-request stack with each head_sha.",
                    remediation_actions=["Correct the named input.", "Rerun finalize-run."],
                )
            ],
        )
    data.update(helper_id=entry.helper_id, operation=entry.operation)
    return response("ok", request_id=request.request_id, data=data)
