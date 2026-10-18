"""The harm-halt record: local state that stops runner writes while it stands (ADR 0010).

A harm halt means the next action could cause damage a later review cannot undo, so after
the trigger no commit, push, PR edit or publish may follow. The runner writes one record
(reason, redacted evidence, last safe state) and refuses state-changing dispatch.
Agent clear requests are refused until the host can authenticate an operator.
The record sits in a runner-owned directory
that git ignores, so it can never be committed or pushed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response
from ..execution_control import confined_path, durable_json, exclusive_ledger
from ..path_utils import find_repo_root as find_payload_root
from ..stop_policy import HARM_HALT, STOP_REASONS
from ..strict_input import SelectionError, require_fields, require_text, unique_object
from ..trusted_io import resolve_repo_root
from .execution_requests import Refusal, run_contained_helper

SCHEMA_VERSION = "harm-halt/v1"
HELPER_ID = "harm-halt"
RECORD_PATH = ".specify/harm-halt/halt.json"
MAX_TEXT = 300
WITHHELD = "withheld: the evidence may hold the secret"
# A key=value pair that names a credential, or any long unbroken token (keys, hashes, URLs with tokens).
SECRET_SHAPES = re.compile(r"(?i)\b(?:token|secret|password|passwd|api[_-]?key)\b\s*[:=]\s*\S+|[A-Za-z0-9_+/=-]{32,}")
RECORD_FIELDS = {"schema_version", "reason", "evidence", "last_safe_state"}
# Audited pure reads only. Other nominal read/dry-run paths can launch processes,
# create sessions or probes, repair state, or persist failure records.
HALTED_READ_HELPERS = frozenset({"helper-registry-dispatch", "mutation-registry-dispatch",
                                 "count-markers", "parse-consensus-categories", "aggregate-crl", "sweep-pr-feedback"})


def redacted(reason: str, evidence: str) -> str:
    """The evidence safe to keep: withheld for a secret exposure, otherwise masked and bounded."""
    if reason == "secret_exposure":
        return WITHHELD
    return SECRET_SHAPES.sub("[redacted]", evidence)[:MAX_TEXT]


def stored_halt(root: Any) -> dict[str, Any] | None:
    """The active record, None when there is none; an unreadable or malformed record raises, so callers fail closed."""
    path = confined_path(root, RECORD_PATH)
    if path.parent.exists() and not path.parent.is_dir():
        raise SelectionError("halt storage is not a directory; a human must inspect it")
    if not path.exists():
        if path.with_suffix(".lock").exists() or (path.parent / ".gitignore").is_dir():
            raise SelectionError("halt publication is active, interrupted or unsafe; a human must inspect it")
        return None
    try:
        record = require_fields(json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object),
                                RECORD_FIELDS, "halt record")
    except (ValueError, OSError) as error:
        raise SelectionError(f"the harm-halt record is unreadable; a human must inspect it: {error}") from error
    if record["schema_version"] != SCHEMA_VERSION or STOP_REASONS.get(record["reason"]) != HARM_HALT:
        raise SelectionError("the harm-halt record is malformed; a human must inspect it")
    return record


def record_halt(root: Any, reason: str, evidence: str, last_safe_state: str) -> dict[str, Any]:
    """Write the halt record; the first trigger stands, so a later one never rewrites the evidence."""
    if STOP_REASONS.get(reason) != HARM_HALT:
        raise SelectionError(f"reason must be a harm halt: {sorted(r for r, c in STOP_REASONS.items() if c == HARM_HALT)}")
    path = confined_path(root, RECORD_PATH)
    try:
        with exclusive_ledger(path):
            existing = stored_halt(root) if path.exists() else None
            if existing is not None:
                raise SelectionError("a harm halt already stands; the second trigger is refused")
            record = {"schema_version": SCHEMA_VERSION, "reason": reason, "evidence": redacted(reason, evidence),
                      "last_safe_state": require_text(last_safe_state, "last_safe_state")[:MAX_TEXT]}
            durable_json(path, record)
    except ValueError as error:
        raise SelectionError(f"harm-halt trigger {reason} refused: {error}") from error
    return record


def clear_halt(root: Any, confirm_reason: str) -> None:
    """Refuse until the host can authenticate an operator; reason matching is not authorization."""
    raise SelectionError("agent clear is refused: no authenticated operator halt-clear event is available; "
                         "a human must inspect the halt outside the agent runner")


def harm_halt(root: Any, inputs: dict[str, Any], mode: str) -> dict[str, Any]:
    """Report the halt or record it in apply mode; agent clearance is refused."""
    request = {key: value for key, value in inputs.items() if key != "repo_root"}
    if mode == "read_only":
        require_fields(request, set(), "inputs")
    else:
        action = request.get("action")
        fields = {"halt": {"action", "reason", "evidence", "last_safe_state"}, "clear": {"action", "confirm_reason"}}
        if action not in fields:
            raise SelectionError(f"action must be one of {sorted(fields)}")
        request = require_fields(request, fields[action], "inputs")
        if mode == "apply":
            if action == "halt":
                record_halt(root, request["reason"], require_text(request["evidence"], "evidence"), request["last_safe_state"])
            else:
                clear_halt(root, request["confirm_reason"])
    record = stored_halt(root)
    return {"halted": record is not None, "resume": "refused" if record else "allowed", "record": record,
            "writes_state": mode == "apply"}


def apply_refusal(entry: Any, request: Any) -> dict[str, Any] | None:
    """Refuse dispatch unless its code path is an audited pure read or the halt helper itself."""
    if entry.helper_id == HELPER_ID:
        return None
    if request.mode == "read_only" and (entry.helper_id in HALTED_READ_HELPERS or
                                        (entry.helper_id == "runner" and request.operation == "runtime-info")):
        return None
    root = resolve_repo_root(request.inputs)
    if entry.helper_id == "payload-gate":
        root = find_payload_root(Path.cwd()) or root
    if isinstance(root, dict):
        return None
    status = "expected_failure"
    try:
        record = stored_halt(root)
    except (SelectionError, ValueError, OSError) as error:
        message = str(error)
        status = "internal_failure"
    else:
        if record is None:
            return None
        message = f"a harm halt ({record['reason']}) stands: {record['evidence']}"
    return response(status, request_id=request.request_id, diagnostics=[diagnostic(
        "harm_halt_active", message, details={"helper_id": entry.helper_id},
        remediation_summary="Nothing was written. A human must inspect the halt outside the agent runner.",
        remediation_actions=["Read the record with harm-halt in read_only mode.", "Resolve the cause; agent clear requests are refused."])])


REFUSAL = Refusal(
    "invalid_harm_halt_request",
    "Send no inputs to read; to record, action halt with a harm-halt reason, evidence and the last safe state. Agent clear requests are refused.",
    ["Correct the named field.", "Rerun harm-halt; nothing was written."],
)


def run_harm_halt_helper(entry: Any, request: Any) -> dict[str, Any]:
    return run_contained_helper(entry, request, harm_halt, REFUSAL)
