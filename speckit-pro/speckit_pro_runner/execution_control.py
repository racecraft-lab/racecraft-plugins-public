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


def _validate_workflow_identity(value: Any) -> dict[str, Any]:
    keys = {"original_workflow_file", "current_workflow_file", "relocation_event_ids"}
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("execution ledger has no valid workflow identity")
    workflow_files = [require_text(value.get(key), key) for key in keys if key.endswith("_workflow_file")]
    if any(Path(item).is_absolute() or Path(item).as_posix() != item or
           any(part in {"..", ".git"} for part in Path(item).parts) for item in workflow_files):
        raise ValueError("execution ledger workflow identity is not canonical")
    event_ids = value.get("relocation_event_ids")
    if not isinstance(event_ids, list) or not all(isinstance(event_id, str) and event_id.strip() for event_id in event_ids):
        raise ValueError("invalid workflow relocation event registry")
    if len(event_ids) != len(set(event_ids)):
        raise ValueError("duplicate workflow relocation event")
    return value


def _validate_invariant_binding(ledger: dict[str, Any]) -> None:
    if "invariant_binding" not in ledger:
        return
    binding = ledger["invariant_binding"]
    if (not isinstance(binding, dict) or set(binding) != {"spec_file", "spec_sha256", "bound_at"}
            or not ledger["approved_invariants"]):
        raise ValueError("invalid invariant binding")
    bound_spec = require_text(binding["spec_file"], "bound spec_file")
    if (Path(bound_spec).is_absolute() or Path(bound_spec).as_posix() != bound_spec
            or any(part in {"..", ".git"} for part in Path(bound_spec).parts)
            or not isinstance(binding["spec_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", binding["spec_sha256"])):
        raise ValueError("invalid invariant binding provenance")
    if (type(binding["bound_at"]) not in (int, float)
            or not ledger["started_at"] <= binding["bound_at"] < float("inf")):
        raise ValueError("invalid invariant binding clock")


def validate_ledger(value: Any) -> None:
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA:
        raise ValueError("invalid execution ledger schema")
    require_text(value.get("run_id"), "run_id")
    _validate_workflow_identity(value.get("workflow_identity"))
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
    _validate_invariant_binding(value)
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
    validate_recovery_records(value)
    validate_continuation_records(value)


def validate_recovery_records(ledger: dict[str, Any]) -> None:
    sources: set[str] = set()
    events: set[str] = set()
    keys = {"recovery_of", "failure_event_id", "operator_recovery_event_id"}
    for dispatch_id, item in ledger["dispatches"].items():
        present = keys & item.keys()
        if not present:
            continue
        if present != keys:
            raise ValueError("incomplete corrective recovery record")
        failed_id = require_text(item["recovery_of"], "recovery_of")
        failed_event_id = require_text(item["failure_event_id"], "failure_event_id")
        approval_event_id = require_text(item["operator_recovery_event_id"], "operator_recovery_event_id")
        failed = ledger["dispatches"].get(failed_id)
        if not isinstance(failed, dict):
            raise ValueError("invalid corrective recovery source")
        if (dispatch_id == failed_id or failed_id in sources or approval_event_id in events or
                approval_event_id == failed_event_id):
            raise ValueError("duplicate corrective recovery event")
        reservation = item.get("reservation_id")
        binding = (item["kind"], failed.get("kind"), failed.get("outcome"), failed.get("reservation_id"),
                   ledger["reservations"].get(reservation, {}).get("dispatch_id"),
                   failed.get("resolution_event_id"), ledger["corrective_cycles"])
        expected = ("corrective", "corrective", "failed", reservation, failed_id, failed_event_id, 2)
        if binding != expected:
            raise ValueError("invalid corrective recovery binding")
        sources.add(failed_id)
        events.add(approval_event_id)


def validate_continuation_records(ledger: dict[str, Any]) -> None:
    keys = {"continuation_of", "operator_continuation_event_id", "continuation_purpose"}
    events: set[str] = set()
    reservations: set[str] = set()
    other_events = set(ledger["workflow_identity"]["relocation_event_ids"])
    other_events.update(event for interval in ledger["excluded_intervals"]
                        for event in (interval["start_event"], interval["end_event"]))
    if ledger.get("active_wait"):
        other_events.add(ledger["active_wait"]["start_event"])
    other_events.update(record["resolution_event_id"] for record in ledger["dispatches"].values()
                        if "resolution_event_id" in record)
    other_events.update(record["operator_recovery_event_id"] for record in ledger["dispatches"].values()
                        if "operator_recovery_event_id" in record)
    for dispatch_id, item in ledger["dispatches"].items():
        present = keys & item.keys()
        if not present:
            continue
        if present != keys:
            raise ValueError("incomplete corrective continuation record")
        source_id = require_text(item["continuation_of"], "continuation_of")
        event_id = require_text(item["operator_continuation_event_id"], "operator_continuation_event_id")
        reservation = item.get("reservation_id")
        source = ledger["dispatches"].get(source_id)
        owner_id = ledger["reservations"].get(reservation, {}).get("dispatch_id")
        owner = ledger["dispatches"].get(owner_id)
        if (item.get("continuation_purpose") != "task_metadata_reconciliation" or
                item.get("kind") != "corrective" or not isinstance(source, dict) or
                source.get("kind") != "corrective" or source.get("outcome") != "completed" or
                source.get("reservation_id") != reservation or ledger["corrective_cycles"] != 2 or
                reservation in reservations or event_id in events or event_id in other_events):
            raise ValueError("invalid corrective continuation binding")
        recovered = source_id != owner_id and source.get("recovery_of") == owner_id and isinstance(owner, dict) and owner.get("outcome") == "failed"
        if source_id != owner_id and not recovered:
            raise ValueError("continuation source is not the completed reservation owner or its recovery")
        members = {key for key, record in ledger["dispatches"].items()
                   if record.get("reservation_id") == reservation}
        if members != {owner_id, source_id, dispatch_id}:
            raise ValueError("corrective continuation has unrelated reservation work")
        events.add(event_id)
        reservations.add(reservation)


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
    if ledger.get("active_wait"):
        reasons.append("awaiting_external_event")
    if any(item["outcome"] == "unknown" for item in ledger["dispatches"].values()):
        reasons.append("unknown_side_effects_require_operator_reconciliation")
    return reasons


def _consumed_native_event_ids(ledger: dict[str, Any]) -> set[str]:
    consumed = set(ledger["workflow_identity"]["relocation_event_ids"])
    consumed.update(event for interval in ledger["excluded_intervals"]
                    for event in (interval["start_event"], interval["end_event"]))
    if ledger.get("active_wait"):
        consumed.add(ledger["active_wait"]["start_event"])
    consumed.update(item["resolution_event_id"] for item in ledger["dispatches"].values()
                    if "resolution_event_id" in item)
    consumed.update(item["operator_recovery_event_id"] for item in ledger["dispatches"].values()
                    if "operator_recovery_event_id" in item)
    consumed.update(item["operator_continuation_event_id"] for item in ledger["dispatches"].values()
                    if "operator_continuation_event_id" in item)
    return consumed


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


def authorize_corrective_retry(ledger: dict[str, Any], inputs: dict[str, Any], now: float) -> dict[str, Any]:
    dispatch_id = require_text(inputs.get("dispatch_id"), "dispatch_id")
    failed_id = require_text(inputs.get("failed_dispatch_id"), "failed_dispatch_id")
    reservation = require_text(inputs.get("reservation_id"), "reservation_id")
    event = inputs.get("native_observation")
    keys = {"native_event_id", "run_id", "action", "failed_dispatch_id", "failed_native_event_id",
            "retry_dispatch_id", "reservation_id", "failure_kind"}
    if not isinstance(event, dict) or set(event) != keys:
        raise ValueError("corrective retry requires one bounded operator native event")
    event_id = require_text(event.get("native_event_id"), "native_event_id")
    failed = ledger["dispatches"].get(failed_id)
    binding = (event.get("run_id"), event.get("action"), event.get("failed_dispatch_id"),
               event.get("retry_dispatch_id"), event.get("reservation_id"), event.get("failure_kind"))
    expected = (ledger["run_id"], "corrective_retry_approved", failed_id, dispatch_id,
                reservation, "infrastructure")
    if binding != expected or event_id in _consumed_native_event_ids(ledger):
        raise ValueError("operator recovery event does not match this run or was consumed")
    if (dispatch_id in ledger["dispatches"] or ledger["corrective_cycles"] != 2 or
            not isinstance(failed, dict) or failed.get("kind") != "corrective" or
            failed.get("outcome") != "failed" or failed.get("reservation_id") != reservation or
            failed.get("resolution_event_id") != event.get("failed_native_event_id") or
            ledger["reservations"].get(reservation, {}).get("dispatch_id") != failed_id or
            any(item.get("reservation_id") == reservation for item_id, item in ledger["dispatches"].items()
                if item_id != failed_id)):
        raise ValueError("failed corrective dispatch is not eligible for a one-time infrastructure retry")
    ledger["dispatches"][dispatch_id] = {"kind": "corrective", "outcome": "reserved", "reserved_at": now,
                                         "reservation_id": reservation, "reconciliations": 0,
                                         "recovery_of": failed_id, "failure_event_id": event["failed_native_event_id"],
                                         "operator_recovery_event_id": event_id}
    return {"reservation_id": reservation, "dispatch_id": dispatch_id, "recovery_of": failed_id}


def authorize_corrective_continuation(ledger: dict[str, Any], inputs: dict[str, Any], now: float) -> dict[str, Any]:
    dispatch_id = require_text(inputs.get("dispatch_id"), "dispatch_id")
    source_id = require_text(inputs.get("completed_dispatch_id"), "completed_dispatch_id")
    reservation = require_text(inputs.get("reservation_id"), "reservation_id")
    event = inputs.get("native_observation")
    keys = {"native_event_id", "run_id", "action", "completed_dispatch_id",
            "continuation_dispatch_id", "reservation_id", "purpose"}
    if not isinstance(event, dict) or set(event) != keys:
        raise ValueError("corrective continuation requires one bounded operator native event")
    event_id = require_text(event.get("native_event_id"), "native_event_id")
    expected = (ledger["run_id"], "corrective_continuation_approved", source_id, dispatch_id,
                reservation, "task_metadata_reconciliation")
    binding = (event.get("run_id"), event.get("action"), event.get("completed_dispatch_id"),
               event.get("continuation_dispatch_id"), event.get("reservation_id"), event.get("purpose"))
    if binding != expected or event_id in _consumed_native_event_ids(ledger):
        raise ValueError("operator continuation event does not match this run or was consumed")
    source = ledger["dispatches"].get(source_id)
    owner_id = ledger["reservations"].get(reservation, {}).get("dispatch_id")
    owner = ledger["dispatches"].get(owner_id)
    recovered = isinstance(source, dict) and source.get("recovery_of") == owner_id and isinstance(owner, dict) and owner.get("outcome") == "failed"
    members = {key for key, item in ledger["dispatches"].items() if item.get("reservation_id") == reservation}
    if (dispatch_id in ledger["dispatches"] or ledger["corrective_cycles"] != 2 or
            not isinstance(source, dict) or source.get("kind") != "corrective" or
            source.get("outcome") != "completed" or source.get("reservation_id") != reservation or
            (source_id != owner_id and not recovered) or
            members != {owner_id, source_id}):
        raise ValueError("completed corrective dispatch is not eligible for one metadata continuation")
    ledger["dispatches"][dispatch_id] = {"kind": "corrective", "outcome": "reserved", "reserved_at": now,
                                         "reservation_id": reservation, "reconciliations": 0,
                                         "continuation_of": source_id,
                                         "operator_continuation_event_id": event_id,
                                         "continuation_purpose": "task_metadata_reconciliation"}
    return {"reservation_id": reservation, "dispatch_id": dispatch_id, "continuation_of": source_id}


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
        if event["native_event_id"] in _consumed_native_event_ids(ledger):
            raise ValueError("native event was already consumed")
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
    if event_id in _consumed_native_event_ids(ledger):
        raise ValueError("native event was already consumed")
    kind = event.get("kind")
    if kind not in {"human_uat", "external_approval"}:
        raise ValueError("only human UAT or external approval waits can exclude wall time")
    active = ledger.get("active_wait")
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


def _relocate_workflow(ledger: dict[str, Any], inputs: dict[str, Any], workflow_file: str) -> None:
    event = inputs.get("native_observation")
    keys = {"native_event_id", "run_id", "action", "previous_workflow_file", "workflow_file"}
    if not isinstance(event, dict) or set(event) != keys:
        raise ValueError("workflow relocation requires one bounded parent native event")
    event_id = require_text(event.get("native_event_id"), "native_event_id")
    identity = ledger["workflow_identity"]
    # The parent-native trust boundary supplies this observation; matching
    # fixture-shaped data here is validation, not authentication.
    binding = (event.get("run_id"), event.get("action"), event.get("previous_workflow_file"),
               event.get("workflow_file"))
    expected = (ledger["run_id"], "workflow_relocated", identity["current_workflow_file"], workflow_file)
    if binding != expected or workflow_file == identity["current_workflow_file"]:
        raise ValueError("workflow relocation event does not match this run and workflow transition")
    if event_id in _consumed_native_event_ids(ledger):
        raise ValueError("native event was already consumed")
    identity["current_workflow_file"] = workflow_file
    identity["relocation_event_ids"].append(event_id)


def _bind_invariants_if_requested(root: Path, inputs: dict[str, Any], spec: Path,
                                  ledger: dict[str, Any], now: float, reasons: list[str]) -> None:
    if inputs.get("action") != "bind-invariants":
        return
    if inputs.get("spec_file") is None:
        raise ValueError("bind-invariants requires an explicit spec_file")
    if reasons:
        return
    if ledger["approved_invariants"] or "invariant_binding" in ledger:
        raise ValueError("invariant registry is already frozen for this run")
    spec_bytes = spec.read_bytes()
    invariants = sorted(set(re.findall(r"\b(?:FR|NFR|INV)-[A-Za-z0-9]+\b",
                                       spec_bytes.decode("utf-8"))))
    if not invariants:
        raise ValueError("spec_file contains no requirement or invariant IDs")
    ledger["approved_invariants"] = invariants
    ledger["invariant_binding"] = {
        "spec_file": spec.relative_to(root.resolve()).as_posix(),
        "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(), "bound_at": now,
    }


def execution_control(root: Path, inputs: dict[str, Any], mode: str) -> dict[str, Any]:
    """Runner adapter returns a disposition without changing autopilot top-state."""
    workflow_name = require_text(inputs.get("workflow_file"), "workflow_file")
    workflow = confined_path(root, workflow_name)
    if not workflow.is_file():
        raise ValueError("workflow_file must exist")
    workflow_name = workflow.relative_to(root.resolve()).as_posix()
    spec_name = inputs.get("spec_file")
    spec = confined_path(root, spec_name) if spec_name is not None else workflow.with_name("spec.md")
    if spec_name is not None and not spec.is_file():
        raise ValueError("spec_file must be an existing contained file")
    action = inputs.get("action", "status")
    if action not in {"start", "status", "bind-invariants", "reserve", "authorize-corrective-retry", "authorize-corrective-continuation", "begin-verification", "complete", "reconcile", "checkpoint", "pause", "resume", "relocate-workflow"}:
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
        existing_ledger = ledger is not None
        if ledger is None:
            if action != "start" or expected_run_id is not None:
                raise ValueError("known run ledger missing; recover its owned ledger without resetting the budget")
            ledger = initial_ledger(spec, now)
            ledger["workflow_identity"] = {"original_workflow_file": workflow_name,
                                           "current_workflow_file": workflow_name,
                                           "relocation_event_ids": []}
        validate_ledger(ledger)
        if existing_ledger and expected_run_id is None:
            raise ValueError("expected_run_id is required for every existing execution ledger action")
        if expected_run_id is not None and ledger["run_id"] != expected_run_id:
            raise ValueError("execution ledger does not match the parent expected_run_id")
        ledger = copy.deepcopy(ledger)
        identity = ledger["workflow_identity"]
        if action == "relocate-workflow":
            _relocate_workflow(ledger, inputs, workflow_name)
        elif identity["current_workflow_file"] != workflow_name:
            raise ValueError("execution ledger belongs to a different workflow")
        reasons = clock_reasons(ledger, now)
        extra: dict[str, Any] = {}
        if "clock_moved_backwards" in reasons and action not in {"status", "start"}:
            raise ValueError("clock moved backwards; preserve the ledger and reconcile time before continuing")
        _bind_invariants_if_requested(root, inputs, spec, ledger, now, reasons)
        if action == "reserve" and not reasons:
            extra = reserve(ledger, inputs, now)
        elif action == "authorize-corrective-retry" and not reasons:
            extra = authorize_corrective_retry(ledger, inputs, now)
        elif action == "authorize-corrective-continuation" and not reasons:
            extra = authorize_corrective_continuation(ledger, inputs, now)
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
    from .task_results import task_results

    root = resolve_repo_root(request.inputs)
    if isinstance(root, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[root])
    error = validate_bounded_inputs(entry.helper_id, request.inputs, root)
    if error:
        return response("input_error", request_id=request.request_id, diagnostics=[error])
    inputs = canonicalize_inputs(entry.helper_id, request.inputs, root)
    try:
        handler = {"execution-control": execution_control, "execute-verification": execute_verification,
                   "task-results": task_results}[entry.helper_id]
        result = handler(root, inputs, request.mode)
    except (ValueError, OSError, TypeError) as exc:
        return response("input_error", request_id=request.request_id,
                        diagnostics=[diagnostic("invalid_execution_request", str(exc))])
    failed = result.get("helper_exit_code") == 1 if entry.helper_id == "task-results" else result.get("disposition") == "checkpoint_required"
    status = "expected_failure" if failed else "ok"
    result.update(helper_id=entry.helper_id, operation=entry.operation, mode=request.mode,
                  promotion_status=entry.promotion_status)
    return response(status, request_id=request.request_id, data=result)
