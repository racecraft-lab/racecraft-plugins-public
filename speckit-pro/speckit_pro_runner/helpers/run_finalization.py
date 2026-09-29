"""Decide how an autopilot run ends once no runnable work remains.

A run whose required gates are all green finalizes: its pull-request stack goes
ready for review (never merged), the top PR body opens with a "Deferred / not
verified" section, the goal is marked complete, and one plain-text request names
what is left. What is left never keeps the stack draft: human UAT, an
execution-control ledger unit whose escalation tiers are exhausted, and a
deferred task nobody resolved all reach the owner as items in that request, the
units and tasks under "Decisions for you" with their evidence and a stop class
(`authority`, `exhausted`, or `harm_halt`).

Only a required gate that is not green keeps the stack draft, as one human stop:
a failed gate (named with its exact command) whose escalation tiers are
exhausted, a gate still missing at a head, or a harness error. A ledger entry is
resolved only when the ledger itself shows a later completed dispatch for the
same unit; it stays in the ledger for audit but leaves the request. A `defer`
disposition keeps the run working on other units mid-run; it never survives to
a finalized run as a stop. This read-only helper fails closed on missing or
malformed evidence and never writes a file.

Every gate result names the PR head (`head_sha`) it ran at. A stack finalizes
only when every PR head passed every non-UAT gate reported for any head, so a
stack verified only at its tip names each head and gate left unverified. Evidence
from one head never stands in for another.

A harness or tooling error that blocks a gate is retried up to
HARNESS_RETRY_BUDGET attempts, then once more in a changed environment (a fresh
worktree or cleared caches). If it persists, the gate reports status
`harness_error` with its `attempts` and the `evidence` path under a
`.process/verification/` directory holding each attempt's raw error and trace.
A harness error never counts as passed; the human stop reports it as a harness
error, never as a failure of the code under test, and cites that path.

Stop triggers are proved from the runner's own records, never from a caller's
claim. A passed or failed gate cites the verification `dispatch_id` the runner
ran; its status comes from that dispatch's failing-check fingerprint and the
head and clean worktree the runner read, so a forged status fails closed. A unit
that failed climbs the escalation tiers first (outcome `continue`): tier 2, a
fresh agent with a different approach guided by a consensus diagnosis, then tier
3, the strongest model at max effort with the full failure history, capped per
run by the ledger. Only after tier 3 fails, or the cap is spent, is the unit
exhausted. A gate missing at a head and a harness error awaiting its
changed-environment attempt are pending too; a head-and-gate pair stops the run
only when an earlier finalize cycle, counted in the ledger by the
`execution-control` action `record-finalize-cycle`, saw it unfinished too.
"""

from __future__ import annotations

import hashlib
import json
import shlex
from pathlib import Path, PurePosixPath
from typing import Any

from ..agent_materialization import canonical_bytes
from ..envelope import diagnostic, response
from ..execution_control import (ESCALATION_TIER3_CAP, confined_path, escalation_key, escalation_progress,
                                 failed_verification, finalize_observation_key, require_text, validate_ledger)
from ..stop_policy import ALL_TIERS_FAILED, AUTHORITY, EXHAUSTED, TIER3_CAP_REACHED, stop_class
from ..sweep_isolation import HEX_OBJECT_RE

ALLOWED_INPUTS = frozenset({"repo_root", "ledger_path", "expected_run_id", "gates", "pending_items",
                            "unresolved_deferrals", "human_uat", "pull_requests", "resume_command"})
GATE_STATUSES = ("passed", "failed", "harness_error")
GATE_FIELDS = {"gate", "status", "command", "head_sha"}
VERIFIED_FIELDS = GATE_FIELDS | {"dispatch_id"}
HARNESS_FIELDS = GATE_FIELDS | {"attempts", "evidence"}
HARNESS_RETRY_BUDGET = 3
# One more attempt, in a changed environment, before a persistent harness error stops the run.
HARNESS_ENVIRONMENT_ATTEMPTS = 1
ENVIRONMENT_CHANGES = ("fresh_worktree", "cleared_caches")
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


def _ledger(root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
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
    return ledger


def _ledger_deferrals(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    # A resolved entry stays in the ledger for audit; validate_ledger proved its resolution.
    return [entry for entry in ledger.get("deferred", []) if "resolved_by" not in entry]


def gate_command_digest(command: str) -> str:
    """The digest of the argv the verification runner derives from a workflow command."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    return hashlib.sha256(canonical_bytes(list(lexer))).hexdigest()


def _derived_status(ledger: dict[str, Any], gate: dict[str, Any], field: str) -> str:
    """A gate's status as the runner's own verification record shows it; raises when the record cannot prove it."""
    item = ledger["dispatches"].get(gate["dispatch_id"])
    fingerprint = item.get("failing_checks") if isinstance(item, dict) else None
    if not isinstance(item, dict) or item.get("kind") != "verification" or not isinstance(fingerprint, dict):
        raise ValueError(f"{field}.dispatch_id must name a verification dispatch the runner ran and fingerprinted; "
                         + "a gate status the runner did not record never counts")
    if fingerprint["command_sha256"] != gate_command_digest(gate["command"]):
        raise ValueError(f"{field}.command is not the command the runner ran in that verification")
    if fingerprint.get("head_sha") != gate["head_sha"] or fingerprint.get("worktree_clean") is not True:
        raise ValueError(f"{field} was not verified by the runner at this PR head with a clean worktree; "
                         + "run the gate at that head")
    return "failed" if failed_verification(item) else "passed"


def _gate_progress(ledger: dict[str, Any], gate: dict[str, Any]) -> str:
    """The next step for a failed gate: `tier2`, `tier3`, `open`, `rerun` when its result predates the last retry, or `exhausted`."""
    unit = gate_command_digest(gate["command"])
    progress = escalation_progress(ledger, "gate_failure", unit)
    record = ledger.get("escalation_allowances", {}).get(escalation_key("gate_failure", unit))
    if record is not None and progress != "open":
        last = ledger["dispatches"][record["dispatches"][-1]["dispatch_id"]]
        # A completed retry changed the code, so a result recorded before it is stale. A failed one did not.
        if (last["outcome"] == "completed"
                and ledger["dispatches"][gate["dispatch_id"]]["failing_checks"]["recorded_at"] < last["completed_at"]):
            return "rerun"
    return progress


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


def _harness_gate(root: Path, raw: dict[str, Any], gate: dict[str, Any], field: str) -> None:
    """Add a harness_error result's attempts, evidence, and optional changed-environment proof to `gate`."""
    if set(raw) - {"environment_change"} != HARNESS_FIELDS:
        raise ValueError(f"{field} must have exactly gate, status, command, head_sha, attempts, "
                         + "and evidence, plus environment_change after the changed-environment attempt")
    if type(raw["attempts"]) is not int or raw["attempts"] < HARNESS_RETRY_BUDGET:
        raise ValueError(f"{field}.attempts must show the harness retry budget of "
                         + f"{HARNESS_RETRY_BUDGET} attempts was spent before reporting harness_error")
    gate.update(attempts=raw["attempts"], evidence=_harness_evidence(root, raw["evidence"], f"{field}.evidence"))
    if "environment_change" in raw:
        if (raw["environment_change"] not in ENVIRONMENT_CHANGES
                or raw["attempts"] < HARNESS_RETRY_BUDGET + HARNESS_ENVIRONMENT_ATTEMPTS):
            raise ValueError(f"{field}.environment_change must be one of {', '.join(ENVIRONMENT_CHANGES)} and "
                             + f"follow the {HARNESS_RETRY_BUDGET} budgeted attempts with one more attempt")
        gate["environment_change"] = raw["environment_change"]


def _verified_gate(ledger: dict[str, Any], raw: dict[str, Any], gate: dict[str, Any], field: str,
                   dispatches: set[str]) -> None:
    """Add a passed or failed result's runner dispatch to `gate`; its status must be the runner's record."""
    if set(raw) != VERIFIED_FIELDS:
        raise ValueError(f"{field} must have exactly gate, status, command, head_sha, and the "
                         + "dispatch_id of the verification the runner ran")
    gate["dispatch_id"] = _text(raw["dispatch_id"], f"{field}.dispatch_id")
    if gate["dispatch_id"] in dispatches:
        raise ValueError(f"{field}.dispatch_id already backs another gate result")
    dispatches.add(gate["dispatch_id"])
    derived = _derived_status(ledger, gate, field)
    if derived != gate["status"]:
        raise ValueError(f"{field}.status claims {gate['status']}, but the runner's verification record shows {derived}")


def _gates(root: Path, ledger: dict[str, Any], value: Any, heads: set[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("gates must list every final non-UAT gate result; a run never finalizes on no evidence")
    gates: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    dispatches: set[str] = set()
    for index, raw in enumerate(value):
        field = f"gates[{index}]"
        if not isinstance(raw, dict) or raw.get("status") not in GATE_STATUSES:
            raise ValueError(f"{field}.status must be passed, failed, or harness_error; only human UAT may be deferred")
        if not GATE_FIELDS <= set(raw):
            raise ValueError(f"{field} must have gate, status, command, and head_sha")
        gate: dict[str, Any] = {"gate": _text(raw["gate"], f"{field}.gate"), "status": raw["status"],
                                "command": _text(raw["command"], f"{field}.command"),
                                "head_sha": _head(raw["head_sha"], f"{field}.head_sha")}
        if raw["status"] == "harness_error":
            _harness_gate(root, raw, gate, field)
        else:
            _verified_gate(ledger, raw, gate, field, dispatches)
        if gate["head_sha"] not in heads:
            raise ValueError(f"{field}.head_sha is not the head of any listed pull request; "
                             + "evidence from another head never counts")
        if (gate["head_sha"], gate["gate"]) in seen:
            raise ValueError(f"{field} repeats gate {gate['gate']} at one head; pass its final result once")
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


def _exhausted_reason(ledger: dict[str, Any], unit_kind: str, unit: str) -> str:
    """`all_tiers_failed` after tier 3, `tier3_cap_reached` when the run's cap kept the unit from tier 3."""
    record = ledger["escalation_allowances"][escalation_key(unit_kind, unit)]
    return ALL_TIERS_FAILED if record["tier"] == 3 else TIER3_CAP_REACHED


def _exhausted_stop(ledger: dict[str, Any], unit_kind: str, unit: str) -> dict[str, str]:
    """The stop class and reason of an exhausted unit; a reason the stop policy does not know fails closed."""
    reason = _exhausted_reason(ledger, unit_kind, unit)
    return {"class": stop_class(reason), "reason_code": reason}


def _decision(ledger: dict[str, Any], entry: dict[str, Any], resume_command: str) -> dict[str, str]:
    """An exhausted ledger unit as a decision for the owner, with the ledger evidence that shows it."""
    unit = str(entry["unit"])
    record = ledger["escalation_allowances"][escalation_key(entry["unit_kind"], unit)]
    reached = ", ".join(f"tier {step['tier']} dispatch {step['dispatch_id']}" for step in record["dispatches"])
    return {
        "unit": f"{UNIT_LABELS.get(entry['unit_kind'], entry['unit_kind'])} {unit}",
        "reason": f"{REASON_TEXT.get(entry['reason'], 'Its correction allowance is spent.')} Its escalation tiers "
                  f"are exhausted. ({entry['reason']})",
        "finish": f"Reply approving one `authorize-corrective-exception` for {unit}, or a re-plan with "
                  f"`begin-replan-epoch`, then resume with: {resume_command}",
        "evidence": f"Ledger deferral {entry['dispatch_id']}; escalation reached tier {record['tier']} ({reached}).",
        **_exhausted_stop(ledger, entry["unit_kind"], unit),
    }


def _tier_steps(tier: str) -> str:
    if tier == "tier3":
        return ("tier 3: dispatch the strongest model at max effort with the full failure history, as one "
                f"implement-executor retry reserved with `escalation` tier 3 (the run allows {ESCALATION_TIER3_CAP})")
    return ("tier 2: dispatch a fresh agent with a different approach, guided by the consensus analysts' diagnosis of "
            "the failure evidence, as one implement-executor retry reserved with `escalation` tier 2")


def _unit_pending(entry: dict[str, Any], progress: str) -> str:
    unit = f"{UNIT_LABELS.get(entry['unit_kind'], entry['unit_kind'])} {entry['unit']}"
    if progress == "open":
        return f"Finish the escalation retry for {unit}, then run finalize-run again."
    return (f"Escalate {unit} to {_tier_steps(progress)}, unit_kind {entry['unit_kind']} and unit "
            f"{entry['unit']}. ({entry['reason']})")


def _gate_pending(where: dict[str, Any], gate: dict[str, Any], progress: str) -> str:
    label = f"gate {gate['gate']} at head {gate['head_sha']} of PR #{where['pull_request']}"
    if progress == "open":
        return f"Finish the escalation retry for {label}, then rerun it at the PR's head."
    if progress == "rerun":
        return f"Rerun {label} after its escalation retry: {gate['command']}"
    return (f"Escalate failed {label} to {_tier_steps(progress)}, unit_kind gate_failure and unit "
            f"{gate_command_digest(gate['command'])}, then rerun it: {gate['command']}")


def _harness_pending(where: dict[str, Any], gate: dict[str, Any]) -> str:
    return (f"Retry gate {gate['gate']} once in a changed environment ({' or '.join(ENVIRONMENT_CHANGES)}) at head "
            f"{gate['head_sha']} of PR #{where['pull_request']}, then report `attempts` "
            f"{HARNESS_RETRY_BUDGET + HARNESS_ENVIRONMENT_ATTEMPTS} with `environment_change`: {gate['command']}")


def _canonical(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Records in one order that does not depend on the order the caller listed them."""
    return sorted(records, key=lambda record: json.dumps(record, sort_keys=True))


def render_request(items: list[dict[str, str]], decisions: list[dict[str, str]], resume_command: str) -> str:
    """The end-of-run request of a finalized run, as plain text."""
    lines = ["The run is finished: every runnable task and gate is done, and the pull request stack is ready "
             + "for review. Nothing was merged."]
    if decisions:
        lines.extend(["", "Decisions for you (each spent every escalation tier):", ""])
        for number, decision in enumerate(decisions, start=1):
            lines.extend([f"{number}. {decision['unit']}: {decision['reason']}",
                          f"   Evidence: {decision['evidence']}", f"   To decide it: {decision['finish']}"])
    if items:
        lines.extend(["", "This human UAT is deferred and not verified:", ""])
        for number, item in enumerate(items, start=1):
            lines.extend([f"{number}. {item['item']}: {item['reason']}", f"   To finish it: {item['finish']}"])
    lines.extend(["", f"Reply in this thread with any finding. The run resumes with: {resume_command}"])
    return "\n".join(lines) + "\n"


def render_stop(stop: dict[str, list[dict[str, Any]]], resume_command: str) -> str:
    """The run's one human stop, as plain text."""
    lines = ["The run stopped because a required gate is not green, and its pull request stack stays in draft. "
             + "Nothing was merged.", ""]
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
    lines.extend(["", f"Reply in this thread with the fix or authorization. The run resumes with: {resume_command}"])
    return "\n".join(lines) + "\n"


def _units(ledger: dict[str, Any], resume_command: str) -> tuple[list[dict[str, str]], list[str]]:
    """Decisions for each exhausted ledger unit, and pending work for each unit with a tier left."""
    decisions: list[dict[str, str]] = []
    pending: list[str] = []
    for entry in _ledger_deferrals(ledger):
        progress = escalation_progress(ledger, entry["unit_kind"], entry["unit"])
        if progress == "exhausted":
            decisions.append(_decision(ledger, entry, resume_command))
        else:
            pending.append(_unit_pending(entry, progress))
    return decisions, pending


def _checked_inputs(inputs: Any) -> str:
    """The request's resume command, after its shape is proved: an object with no unknown input."""
    if not isinstance(inputs, dict):
        raise ValueError("inputs must be an object")
    unknown = sorted(set(inputs) - ALLOWED_INPUTS)
    if unknown:
        raise ValueError(f"unknown inputs: {', '.join(unknown)}")
    return _text(inputs.get("resume_command"), "resume_command")


def _pending_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("pending_items must list the runnable work still open, or be empty")
    return [_text(item, "pending_items") for item in value]


def _outcome(pending_items: list[str], stop: dict[str, list[dict[str, Any]]], has_handoff: bool) -> str:
    """`continue` while work is pending, `human_stop` for a red gate, else a finalized run."""
    if pending_items:
        return "continue"
    if any(stop.values()):
        return "human_stop"
    return "complete_with_deferred" if has_handoff else "complete"


def _gate_findings(ledger: dict[str, Any], gates: list[dict[str, Any]], numbers: dict[str, int],
                   counted: dict[str, int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[str]]:
    """Red-gate stops, harness stops, pending work, and the counts to record, from each gate's runner-proved state."""
    failed: list[dict[str, Any]] = []
    harness: list[dict[str, Any]] = []
    pending: list[str] = []
    observed: list[str] = []
    for gate in gates:
        where = {"gate": gate["gate"], "command": gate["command"], "pull_request": numbers[gate["head_sha"]],
                 "head_sha": gate["head_sha"]}
        if gate["status"] == "failed":
            progress = _gate_progress(ledger, gate)
            if progress == "exhausted":
                failed.append({**where, **_exhausted_stop(ledger, "gate_failure", gate_command_digest(gate["command"]))})
            else:
                pending.append(_gate_pending(where, gate, progress))
        elif gate["status"] == "harness_error":
            key = finalize_observation_key("harness_error", gate["head_sha"], gate["gate"])
            if "environment_change" in gate and counted.get(key, 0) >= 1:
                harness.append({**where, "class": EXHAUSTED, "attempts": gate["attempts"], "evidence": gate["evidence"]})
            else:
                pending.append(_harness_pending(where, gate))
                observed.append(key)
    return failed, harness, pending, observed


def _missing_findings(prs: list[dict[str, Any]], gates: list[dict[str, Any]],
                      counted: dict[str, int]) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """A gate missing at a head is pending until an earlier counted cycle also saw it missing, then a stop."""
    missing: list[dict[str, Any]] = []
    pending: list[str] = []
    observed: list[str] = []
    for entry in _missing(prs, gates):
        key = finalize_observation_key("missing_gate", entry["head_sha"], entry["gate"])
        if counted.get(key, 0) >= 1:
            missing.append({**entry, "class": EXHAUSTED})
        else:
            pending.append(f"Run gate {entry['gate']} at head {entry['head_sha']} of PR "
                           f"#{entry['pull_request']}: {entry['command']}")
            observed.append(key)
    return missing, pending, observed


def finalize_run(root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    """The run's terminal decision; raises ValueError on missing or malformed evidence.

    `observed` lists each head and gate this cycle left unfinished. The runner's `execution-control`
    `record-finalize-cycle` action counts them in the ledger, so this helper itself writes nothing.
    """
    resume_command = _checked_inputs(inputs)
    ledger = _ledger(root, inputs)
    decisions, unit_pending = _units(ledger, resume_command)
    unresolved = _records(inputs.get("unresolved_deferrals", []), "unresolved_deferrals", DEFERRAL_FIELDS)
    decisions += [{**item, "evidence": "Recorded as a deferred task by the orchestrator.", "class": AUTHORITY}
                  for item in unresolved]
    human_uat = _records(inputs.get("human_uat", []), "human_uat", UAT_FIELDS)
    prs = _pull_requests(inputs.get("pull_requests"))
    gates = _gates(root, ledger, inputs.get("gates"), {pr["head_sha"] for pr in prs})
    numbers = {pr["head_sha"]: pr["number"] for pr in prs}
    pending_items = _pending_items(inputs.get("pending_items")) + unit_pending
    counted = ledger.get("finalize_observations", {})
    failed, harness, gate_pending, observed = _gate_findings(ledger, gates, numbers, counted)
    missing, missing_pending, missing_observed = _missing_findings(prs, gates, counted)
    pending_items += gate_pending + missing_pending
    observed += missing_observed
    # Canonical order, so the same blocker listed another way has the same digest and request text.
    stop = {"gates": _canonical(failed), "missing": _canonical(missing), "harness_errors": _canonical(harness)}
    human_uat, decisions = _canonical(human_uat), _canonical(decisions)
    outcome = _outcome(pending_items, stop, bool(human_uat or decisions))
    finalized = outcome in {"complete", "complete_with_deferred"}
    request = (render_request(human_uat, decisions, resume_command) if finalized and (human_uat or decisions)
               else render_stop(stop, resume_command) if outcome == "human_stop" else "")
    digest = "sha256:" + hashlib.sha256(json.dumps([stop, human_uat, decisions], sort_keys=True).encode()).hexdigest()
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
        "decisions": decisions if finalized else [],
        "deferred_digest": digest,
        "end_of_run_request": request,
        "observed": sorted(observed),
        "writes_state": False,
    }


def run_run_finalization_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Runner helper entry point: reads one ledger, writes nothing. Counting a cycle is `execution-control`'s job."""
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
