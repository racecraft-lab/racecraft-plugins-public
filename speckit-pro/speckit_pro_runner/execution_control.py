"""Durable run accounting. This is a budget gate, never an authorization grant.

Native orchestration still owns approvals, dispatch, and recovered tool events.
No user-supplied boolean can exclude wall time or reset a consumed reservation.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .formal.selection import require_text as require_nonempty_text

SCHEMA = "execution-control/v1"
KINDS = {"implementation", "corrective", "verification", "infrastructure"}
OUTCOMES = {"completed", "failed", "unknown", "expected_tdd_red"}


def confined_path(root: Path, value: str) -> Path:
    """Reject traversal and every symlink component, including dangling links."""
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError("path must be a nonempty repository-relative path")
    parts = Path(value).parts
    if any(part in {"..", ".git"} for part in parts):
        raise ValueError("path traversal or git metadata is not permitted")
    path = root.resolve()
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("symlink paths are not permitted")
    return path


def durable_json(path: Path, value: dict[str, Any]) -> None:
    """Publish a complete record, with data and containing directory flushed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".execution-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        if os.name == "posix":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)


@contextmanager
def exclusive_ledger(path: Path):
    """Concurrent or interrupted writers fail closed; never steal a stale lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix(".lock")
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise ValueError("ledger locked; reconcile the prior owner before retrying") from exc
    try:
        yield
    finally:
        lock.rmdir()


def require_text(value: Any, name: str) -> str:
    text = require_nonempty_text(value, name)
    if len(text) > 240:
        raise ValueError(f"{name} exceeds 240 characters")
    return text


def initial_ledger(spec: Path, now: float) -> dict[str, Any]:
    text = spec.read_text(encoding="utf-8") if spec.is_file() else ""
    invariants = sorted(set(re.findall(r"\b(?:FR|NFR|INV)-[A-Za-z0-9]+\b", text)))
    return {"schema_version": SCHEMA, "run_id": uuid.uuid4().hex,
            "started_at": now, "slice_started_at": now, "last_observed_at": now,
            "checkpoint_at": now, "approved_invariants": invariants,
            "corrective_cycles": 0, "reservations": {}, "dispatches": {},
            "excluded_intervals": [], "active_wait": None, "authorization_granted": False}


def validate_ledger(value: Any) -> None:
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA:
        raise ValueError("invalid execution ledger schema")
    for key in ("started_at", "slice_started_at", "last_observed_at", "checkpoint_at"):
        if type(value.get(key)) not in (int, float) or not 0 <= value[key] < float("inf"):
            raise ValueError(f"invalid ledger clock: {key}")
    if type(value.get("corrective_cycles")) is not int or not 0 <= value["corrective_cycles"] <= 2:
        raise ValueError("invalid corrective counter")
    if value.get("authorization_granted") is not False:
        raise ValueError("budget gates cannot grant authorization")
    validate_intervals(value)
    if not isinstance(value.get("approved_invariants"), list) or not all(isinstance(v, str) for v in value["approved_invariants"]):
        raise ValueError("invalid invariant registry")
    if not isinstance(value.get("reservations"), dict) or not isinstance(value.get("dispatches"), dict):
        raise ValueError("invalid execution reservations")
    if len(value["reservations"]) != value["corrective_cycles"]:
        raise ValueError("reservation counter disagrees with ledger")
    families = [item.get("family") for item in value["reservations"].values() if isinstance(item, dict)]
    if len(families) != len(value["reservations"]) or len(set(families)) != len(families):
        raise ValueError("duplicate or malformed corrective family")
    for item in value["dispatches"].values():
        if not isinstance(item, dict) or item.get("kind") not in KINDS or item.get("outcome") not in OUTCOMES | {"reserved", "running"}:
            raise ValueError("invalid dispatch record")
        if type(item.get("reconciliations")) is not int or not 0 <= item["reconciliations"] <= 1:
            raise ValueError("invalid reconciliation counter")
        reservation = item.get("reservation_id")
        if item["kind"] == "corrective" and reservation not in value["reservations"]:
            raise ValueError("corrective dispatch has no reservation")


def validate_intervals(ledger: dict[str, Any]) -> None:
    intervals = ledger.get("excluded_intervals")
    if not isinstance(intervals, list):
        raise ValueError("invalid excluded clock intervals")
    previous_end = ledger["started_at"]
    for interval in intervals:
        if not isinstance(interval, dict) or interval.get("kind") not in {"human_uat", "external_approval"}:
            raise ValueError("invalid excluded interval kind")
        for key in ("start", "end"):
            if type(interval.get(key)) not in (int, float) or not 0 <= interval[key] < float("inf"):
                raise ValueError("invalid excluded clock interval")
        if interval["start"] < previous_end or interval["end"] < interval["start"]:
            raise ValueError("overlapping or inverted excluded intervals")
        require_text(interval.get("start_event"), "start_event")
        require_text(interval.get("end_event"), "end_event")
        previous_end = interval["end"]
    active = ledger.get("active_wait")
    if active is not None:
        if not isinstance(active, dict) or active.get("kind") not in {"human_uat", "external_approval"}:
            raise ValueError("invalid active wait")
        if type(active.get("start")) not in (int, float) or not previous_end <= active["start"] < float("inf"):
            raise ValueError("invalid active wait clock")
        require_text(active.get("start_event"), "start_event")


def elapsed(ledger: dict[str, Any], now: float, since: float) -> float:
    intervals = list(ledger["excluded_intervals"])
    if ledger.get("active_wait"):
        intervals.append({**ledger["active_wait"], "end": now})
    excluded = sum(max(0, min(now, item["end"]) - max(since, item["start"])) for item in intervals)
    return max(0, now - since - excluded)


def clock_reasons(ledger: dict[str, Any], now: float) -> list[str]:
    reasons = []
    if now < ledger["last_observed_at"]:
        reasons.append("clock_moved_backwards")
    if elapsed(ledger, now, ledger["started_at"]) >= 7200:
        reasons.append("full_run_budget_exhausted")
    if elapsed(ledger, now, ledger["slice_started_at"]) >= 5400:
        reasons.append("slice_budget_exhausted")
    if ledger.get("active_wait"):
        reasons.append("awaiting_external_event")
    if any(item["outcome"] == "unknown" for item in ledger["dispatches"].values()):
        reasons.append("unknown_side_effects_require_operator_reconciliation")
    return reasons


def reserve(ledger: dict[str, Any], inputs: dict[str, Any], now: float) -> dict[str, Any]:
    dispatch_id = require_text(inputs.get("dispatch_id"), "dispatch_id")
    kind = inputs.get("kind")
    if kind not in KINDS:
        raise ValueError("unknown execution kind")
    if dispatch_id in ledger["dispatches"]:
        return {"reasons": ["dispatch_already_reserved_no_relaunch"]}
    reservation = inputs.get("reservation_id")
    if kind == "corrective":
        if reservation is not None:
            if reservation not in ledger["reservations"]:
                raise ValueError("nested correction requires an existing run reservation")
            owner = ledger["reservations"][reservation]["dispatch_id"]
            if ledger["dispatches"][owner]["outcome"] != "reserved":
                return {"reasons": ["corrective_cycle_already_closed"]}
            if any(item.get("reservation_id") == reservation and item["outcome"] in {"failed", "unknown"}
                   for item in ledger["dispatches"].values()):
                return {"reasons": ["corrective_cycle_failed_no_nested_retry"]}
        else:
            invariant = inputs.get("failure_invariant")
            family = invariant if invariant in ledger["approved_invariants"] else "unresolved"
            if any(item["family"] == family for item in ledger["reservations"].values()):
                return {"reasons": ["failure_family_budget_exhausted"]}
            if ledger["corrective_cycles"] >= 2:
                return {"reasons": ["corrective_run_budget_exhausted"]}
            reservation = uuid.uuid4().hex
            ledger["reservations"][reservation] = {"family": family, "dispatch_id": dispatch_id, "reserved_at": now}
            ledger["corrective_cycles"] += 1
    elif reservation is not None:
        raise ValueError("only corrective dispatches use corrective reservations")
    ledger["dispatches"][dispatch_id] = {"kind": kind, "outcome": "reserved", "reserved_at": now,
                                        "reservation_id": reservation, "reconciliations": 0}
    return {"reservation_id": reservation, "dispatch_id": dispatch_id}


def record_result(ledger: dict[str, Any], inputs: dict[str, Any], now: float) -> dict[str, Any]:
    dispatch_id = require_text(inputs.get("dispatch_id"), "dispatch_id")
    if dispatch_id not in ledger["dispatches"]:
        raise ValueError("dispatch was not reserved")
    item = ledger["dispatches"][dispatch_id]
    if inputs["action"] == "reconcile":
        allowed = item["reconciliations"] == 0 and item["outcome"] in {"reserved", "running", "unknown"}
        if allowed:
            item["reconciliations"] = 1
            item["outcome"] = "unknown"
        return {"reconciliation_allowed": allowed, "relaunch_allowed": False,
                "reasons": [] if allowed else ["reconciliation_budget_exhausted"]}
    outcome = inputs.get("outcome")
    if outcome not in OUTCOMES or (outcome == "expected_tdd_red" and item["kind"] != "implementation"):
        raise ValueError("invalid outcome for dispatch kind")
    if item["outcome"] == "unknown":
        event = inputs.get("native_observation")
        if not isinstance(event, dict) or not isinstance(event.get("native_event_id"), str) or not event["native_event_id"].strip():
            return {"reasons": ["missing_independent_native_result"]}
        if event.get("run_id") != ledger["run_id"] or event.get("dispatch_id") != dispatch_id or event.get("action") != "dispatch_result" or event.get("outcome") != outcome or outcome == "unknown":
            return {"reasons": ["native_result_binding_mismatch"]}
        item["resolution_event_id"] = event["native_event_id"]
    elif item["outcome"] not in {"reserved", "running"}:
        return {"reasons": ["recorded_outcome_cannot_be_overwritten"]}
    item.update(outcome=outcome, completed_at=now)
    return {"reasons": ["unknown_side_effects_require_operator_reconciliation"] if outcome == "unknown" else []}


def begin_verification(ledger: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    dispatch_id = require_text(inputs.get("dispatch_id"), "dispatch_id")
    item = ledger["dispatches"].get(dispatch_id)
    if not isinstance(item, dict) or item.get("kind") != "verification":
        raise ValueError("verification requires a reserved verification dispatch")
    if item["outcome"] != "reserved":
        return {"reasons": ["dispatch_already_started_no_relaunch"]}
    item["outcome"] = "running"
    return {"dispatch_id": dispatch_id}


def checkpoint_or_wait(ledger: dict[str, Any], inputs: dict[str, Any], now: float) -> dict[str, Any]:
    action = inputs["action"]
    if action == "checkpoint":
        completed = [name for name, item in ledger["dispatches"].items() if item["outcome"] == "completed"]
        if not completed:
            return {"reasons": ["no_completed_work_to_checkpoint"]}
        ledger["checkpoint_at"] = now
        return {"completed_dispatch_ids": completed}
    event = inputs.get("native_observation")
    if not isinstance(event, dict) or event.get("run_id") != ledger["run_id"]:
        raise ValueError("wait accounting requires an independent parent native event bound to this run")
    event_id = require_text(event.get("native_event_id"), "native_event_id")
    kind = event.get("kind")
    if kind not in {"human_uat", "external_approval"}:
        raise ValueError("only human UAT or external approval waits can exclude wall time")
    active = ledger.get("active_wait")
    consumed = {event for interval in ledger["excluded_intervals"] for event in (interval["start_event"], interval["end_event"])}
    if event_id in consumed:
        raise ValueError("native wait event was already consumed")
    if action == "pause":
        if active is not None or event.get("action") != "wait_started":
            raise ValueError("pause requires a new native wait-start event")
        ledger["active_wait"] = {"start": now, "kind": kind, "start_event": event_id}
    else:
        if active is None or active["kind"] != kind or event.get("action") != "wait_ended" or event_id == active["start_event"] or event.get("wait_start_event_id") != active["start_event"]:
            raise ValueError("resume requires the matching independent native wait-end event")
        ledger["excluded_intervals"].append({**active, "end": now, "end_event": event_id})
        ledger["active_wait"] = None
    return {}


def execution_control(root: Path, inputs: dict[str, Any], mode: str) -> dict[str, Any]:
    """Runner adapter returns a disposition without changing autopilot top-state."""
    workflow_name = require_text(inputs.get("workflow_file"), "workflow_file")
    workflow = confined_path(root, workflow_name)
    if not workflow.is_file():
        raise ValueError("workflow_file must exist")
    spec_name = inputs.get("spec_file")
    spec = confined_path(root, spec_name) if spec_name is not None else workflow.with_name("spec.md")
    if spec_name is not None and not spec.is_file():
        raise ValueError("spec_file must be an existing contained file")
    action = inputs.get("action", "status")
    if action not in {"start", "status", "reserve", "begin-verification", "complete", "reconcile", "checkpoint", "pause", "resume"}:
        raise ValueError("unsupported action; pauses/resets require verified native authorization")
    if mode not in {"read_only", "dry_run", "apply"} or (mode == "read_only" and action != "status"):
        raise ValueError("ledger mutations require dry_run or apply")
    expected_run_id = inputs.get("expected_run_id")
    if expected_run_id is not None:
        require_text(expected_run_id, "expected_run_id")
    elif action != "start":
        raise ValueError("expected_run_id is required after the explicit first kickoff")
    workflow_key = hashlib.sha256(workflow_name.encode("utf-8")).hexdigest()[:24]
    relative = inputs.get("ledger_path") or (Path(workflow_name).parent / ".process/execution-control" / f"{workflow_key}.json").as_posix()
    if Path(relative).parent.name != "execution-control" or Path(relative).suffix != ".json":
        raise ValueError("ledger_path must reference an owned execution-control JSON record")
    path = confined_path(root, relative)

    def update() -> dict[str, Any]:
        now = time.time()
        ledger = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        if ledger is None:
            if action != "start" or expected_run_id is not None:
                raise ValueError("known run ledger missing; recover its owned ledger without resetting the budget")
            ledger = initial_ledger(spec, now)
        validate_ledger(ledger)
        if expected_run_id is not None and ledger["run_id"] != expected_run_id:
            raise ValueError("execution ledger does not match the parent expected_run_id")
        ledger = copy.deepcopy(ledger)
        reasons = clock_reasons(ledger, now)
        extra: dict[str, Any] = {}
        if "clock_moved_backwards" in reasons and action not in {"status", "start"}:
            raise ValueError("clock moved backwards; preserve the ledger and reconcile time before continuing")
        if action == "reserve" and not reasons:
            extra = reserve(ledger, inputs, now)
        elif action == "begin-verification" and not reasons:
            extra = begin_verification(ledger, inputs)
        elif action in {"complete", "reconcile"}:
            extra = record_result(ledger, inputs, now)
            reasons = clock_reasons(ledger, now)
        elif action in {"checkpoint", "pause", "resume"}:
            extra = checkpoint_or_wait(ledger, inputs, now)
            reasons = clock_reasons(ledger, now)
        reasons.extend(extra.pop("reasons", []))
        if mode == "apply":
            ledger["last_observed_at"] = max(now, ledger["last_observed_at"])
            durable_json(path, ledger)
        return {"ledger": ledger, "ledger_path": relative, "disposition": "checkpoint_required" if reasons else "continue",
                "reasons": reasons, "elapsed_seconds": elapsed(ledger, now, ledger["started_at"]),
                "checkpoint_due": elapsed(ledger, now, ledger["checkpoint_at"]) >= 2700,
                "authorization_granted": False, "writes_state": mode == "apply", **extra}

    if mode == "apply":
        with exclusive_ledger(path):
            return update()
    return update()


def run_execution_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Existing runner envelope adapter; apply remains a host-authorized action."""
    from .envelope import diagnostic, response
    from .helpers.read_only import canonicalize_inputs, resolve_repo_root, validate_bounded_inputs
    from .verification_records import execute_verification

    root = resolve_repo_root(request.inputs)
    if isinstance(root, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[root])
    error = validate_bounded_inputs(entry.helper_id, request.inputs, root)
    if error:
        return response("input_error", request_id=request.request_id, diagnostics=[error])
    inputs = canonicalize_inputs(entry.helper_id, request.inputs, root)
    try:
        handler = execution_control if entry.helper_id == "execution-control" else execute_verification
        result = handler(root, inputs, request.mode)
    except (ValueError, OSError, TypeError) as exc:
        return response("input_error", request_id=request.request_id,
                        diagnostics=[diagnostic("invalid_execution_request", str(exc))])
    status = "expected_failure" if result.get("disposition") == "checkpoint_required" else "ok"
    result.update(helper_id=entry.helper_id, operation=entry.operation, mode=request.mode,
                  promotion_status=entry.promotion_status)
    return response(status, request_id=request.request_id, data=result)
