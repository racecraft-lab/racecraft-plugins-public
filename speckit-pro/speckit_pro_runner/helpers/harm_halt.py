"""The harm-halt record: a local file that stops all runner writes until a human clears it (ADR 0010).

A harm halt means the next action could cause damage a later review cannot undo, so after
the trigger no commit, push, PR edit or publish may follow. The runner writes one record
(reason, redacted evidence, last safe state) and refuses every apply-mode helper until the
`clear` action runs with the recorded reason. The record sits in a runner-owned directory
that git ignores, so it can never be committed or pushed.
"""

from __future__ import annotations

import json
import re
from typing import Any

from ..envelope import diagnostic, response
from ..execution_control import confined_path, durable_json
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


def redacted(reason: str, evidence: str) -> str:
    """The evidence safe to keep: withheld for a secret exposure, otherwise masked and bounded."""
    if reason == "secret_exposure":
        return WITHHELD
    return SECRET_SHAPES.sub("[redacted]", evidence)[:MAX_TEXT]


def stored_halt(root: Any) -> dict[str, Any] | None:
    """The active record, None when there is none; an unreadable or malformed record raises, so callers fail closed."""
    path = confined_path(root, RECORD_PATH)
    if not path.exists():
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
    existing = stored_halt(root)
    if existing is not None:
        return existing
    record = {"schema_version": SCHEMA_VERSION, "reason": reason, "evidence": redacted(reason, evidence),
              "last_safe_state": require_text(last_safe_state, "last_safe_state")[:MAX_TEXT]}
    durable_json(confined_path(root, RECORD_PATH), record)
    return record


def clear_halt(root: Any, confirm_reason: str) -> None:
    """Remove the record, once the caller names the recorded reason."""
    existing = stored_halt(root)
    if existing is None:
        raise SelectionError("there is no harm-halt record to clear")
    if confirm_reason != existing["reason"]:
        raise SelectionError(f"confirm_reason must name the recorded reason, {existing['reason']}")
    confined_path(root, RECORD_PATH).unlink()


def harm_halt(root: Any, inputs: dict[str, Any], mode: str) -> dict[str, Any]:
    """Report the halt, or (apply) record or clear it."""
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
    """The refusal for an apply-mode helper while a halt stands, or None. A record that cannot be read refuses too."""
    if request.mode != "apply" or entry.helper_id == HELPER_ID:
        return None
    root = resolve_repo_root(request.inputs)
    if isinstance(root, dict):
        return None
    try:
        record = stored_halt(root)
    except (SelectionError, ValueError, OSError) as error:
        message = str(error)
    else:
        if record is None:
            return None
        message = f"a harm halt ({record['reason']}) stands: {record['evidence']}"
    return response("expected_failure", request_id=request.request_id, diagnostics=[diagnostic(
        "harm_halt_active", message, details={"helper_id": entry.helper_id},
        remediation_summary="Nothing was written. A human clears the halt with the harm-halt helper, action clear.",
        remediation_actions=["Read the record with harm-halt in read_only mode.", "Resolve the cause, then clear the halt."])])


REFUSAL = Refusal(
    "invalid_harm_halt_request",
    "Send no inputs to read; to record, action halt with a harm-halt reason, evidence and the last safe state; to clear, action clear with confirm_reason.",
    ["Correct the named field.", "Rerun harm-halt; nothing was written."],
)


def run_harm_halt_helper(entry: Any, request: Any) -> dict[str, Any]:
    return run_contained_helper(entry, request, harm_halt, REFUSAL)
