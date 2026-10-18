"""The harm-halt record: local state that stops runner writes while it stands (ADR 0010).

A harm halt means the next action could cause damage a later review cannot undo, so after
the trigger no commit, push, PR edit or publish may follow. The runner writes one record
(reason, redacted evidence, last safe state) and refuses state-changing dispatch.
Recording a halt mints a one-time clear token. The record keeps only its SHA-256 digest, and the
token goes only to the owner's terminal: the outermost terminal in the runner's process ancestry,
never one the runner's own streams use. A clear needs that token. When no such terminal exists,
nobody receives it and the halt stands until a human recovers it by hand.
The record sits in a runner-owned directory
that git ignores, so it can never be committed or pushed.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import stat
import subprocess
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response
from ..execution_control import LEDGER_LOCKED, confined_path, durable_json, exclusive_ledger
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
DIGEST_FIELD = "clear_token_sha256"
RECORD_FIELDS = {"schema_version", "reason", "evidence", "last_safe_state", DIGEST_FIELD}
SHA256_HEX = re.compile(r"[0-9a-f]{64}")
# A terminal name as `ps` prints it: ttys001 on macOS, pts/3 on Linux; anything else is no terminal.
TERMINAL_NAME = re.compile(r"(?:tty[A-Za-z0-9]+|pts/[0-9]+)")
MAX_ANCESTORS = 64
# "off" only withholds the token (test suites set it); no setting can send it anywhere else.
TERMINAL_SWITCH = "SPECKIT_HARM_HALT_TERMINAL"
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
        if lock_held(path) or (path.parent / ".gitignore").is_dir():
            raise SelectionError("halt publication is active, interrupted or unsafe; a human must inspect it")
        return None
    return public(parsed_record(path))


def lock_held(path: Path) -> bool:
    """Whether any entry, even a dangling link, holds the publication lock that `mkdir` would refuse."""
    lock = path.with_suffix(".lock")
    return lock.exists() or lock.is_symlink()


def parsed_record(path: Path) -> dict[str, Any]:
    """The full stored record, digest included; only the halt owner reads the digest."""
    try:
        record = require_fields(json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object),
                                RECORD_FIELDS, "halt record")
    except (ValueError, OSError) as error:
        raise SelectionError(f"the harm-halt record is unreadable; a human must inspect it: {error}") from error
    if (record["schema_version"] != SCHEMA_VERSION or STOP_REASONS.get(record["reason"]) != HARM_HALT
            or not isinstance(record[DIGEST_FIELD], str) or not SHA256_HEX.fullmatch(record[DIGEST_FIELD])):
        raise SelectionError("the harm-halt record is malformed; a human must inspect it")
    return record


def public(record: dict[str, Any]) -> dict[str, Any]:
    """The record as helpers report it: never the token digest."""
    shown = dict(record)
    shown.pop(DIGEST_FIELD, None)
    return shown


def digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def record_halt(root: Any, reason: str, evidence: str, last_safe_state: str) -> dict[str, Any]:
    """Validate before locking; once locked, leave either a record or a blocking lock, even on failure.

    A trigger refused because a halt already stands changed nothing, so it releases the lock.
    Only after the record is published does the clear token go to the owner's terminal."""
    reason = require_text(reason, "reason")
    if STOP_REASONS.get(reason) != HARM_HALT:
        raise SelectionError(f"reason must be a harm halt: {sorted(r for r, c in STOP_REASONS.items() if c == HARM_HALT)}")
    token = secrets.token_urlsafe(32)
    record = {"schema_version": SCHEMA_VERSION, "reason": reason, "evidence": redacted(reason, require_text(evidence, "evidence")),
              "last_safe_state": require_text(last_safe_state, "last_safe_state")[:MAX_TEXT], DIGEST_FIELD: digest(token)}
    path = confined_path(root, RECORD_PATH)
    try:
        with exclusive_ledger(path, retain_on_error=True):
            standing = path.exists() and stored_halt(root) is not None
            if not standing:
                durable_json(path, record)
        if standing:
            raise SelectionError("a harm halt already stands; the second trigger is refused")
    except ValueError as error:
        raise SelectionError(f"harm-halt trigger {reason} refused: {error}") from error
    shown = show_on_owner_terminal(token)
    return {**public(record), "clear_token": "shown_on_owner_terminal" if shown else "not_delivered"}


def clear_refusal(record: dict[str, Any] | None, token: Any) -> str | None:
    """Why this token cannot clear the halt, or None when it can; the text never repeats the token."""
    if record is None:
        return "no harm halt stands, so there is nothing to clear; a used token clears nothing"
    if not isinstance(token, str) or not token:
        return "a clear needs the one-time token shown on the owner's terminal; the halt stands"
    if not hmac.compare_digest(digest(token), record[DIGEST_FIELD]):
        return "the clear token does not match the standing halt; the halt stands"
    return None


def clear_halt(root: Any, token: Any) -> None:
    """Remove the record only for its own token; the check and the removal hold the publication lock."""
    path = confined_path(root, RECORD_PATH)
    try:
        with exclusive_ledger(path):
            refusal = clear_refusal(parsed_record(path) if path.exists() else None, token)
            if refusal is not None:
                raise SelectionError(refusal)
            path.unlink()
    except ValueError as error:
        raise SelectionError(f"harm-halt clear refused: {error}") from error


def planned_clear(root: Any, token: Any) -> dict[str, Any]:
    """What an apply clear would do with this token, checked in apply's order; it reads only and spends nothing."""
    path = confined_path(root, RECORD_PATH)
    standing = stored_halt(root) is not None
    if standing and lock_held(path):
        refusal: str | None = LEDGER_LOCKED
    else:
        refusal = clear_refusal(parsed_record(path) if standing else None, token)
    return {"would_clear": refusal is None, "clear_refusal": refusal}


def process_row(pid: int) -> tuple[int, str]:
    """One process's parent and terminal name, read with the system `ps`; a failure raises."""
    shown = subprocess.run(["/bin/ps", "-o", "ppid=,tty=", "-p", str(pid)], capture_output=True, text=True,
                           timeout=5, check=True).stdout.split()
    return int(shown[0]), shown[1]


def runner_terminals() -> set[int]:
    """Terminal devices the runner's own streams or controlling terminal use; output there is agent-visible."""
    devices = {os.fstat(fd).st_rdev for fd in (0, 1, 2) if os.isatty(fd)}
    try:
        descriptor = os.open("/dev/tty", os.O_RDONLY | os.O_NOCTTY)
    except OSError:
        return devices
    try:
        return devices | {os.fstat(descriptor).st_rdev}
    finally:
        os.close(descriptor)


def outermost_terminal() -> str | None:
    """The terminal of the farthest ancestor that has one: the human's, when agents run beneath it.

    An ancestry deeper than the walk returns None: the farthest terminal seen may not be the outermost."""
    outermost, pid = None, os.getpid()
    for _ in range(MAX_ANCESTORS):
        parent, name = process_row(pid)
        if TERMINAL_NAME.fullmatch(name):
            outermost = "/dev/" + name
        if parent <= 1:
            return outermost
        pid = parent
    return None


def write_terminal_payload(descriptor: int, payload: bytes) -> bool:
    """Complete the terminal frame, refusing a write that makes no progress."""
    while payload:
        written = os.write(descriptor, payload)
        if written <= 0:
            return False
        payload = payload[written:]
    return True


def show_on_owner_terminal(token: str) -> bool:
    """Write the token to the owner's terminal only; True when written. Any doubt withholds it."""
    if os.environ.get(TERMINAL_SWITCH) == "off":
        return False
    try:
        path = outermost_terminal()
        if path is None:
            return False
        descriptor = os.open(path, os.O_WRONLY | os.O_NOCTTY | os.O_NOFOLLOW)
        try:
            device = os.fstat(descriptor)
            if not stat.S_ISCHR(device.st_mode) or device.st_rdev in runner_terminals():
                return False
            return write_terminal_payload(descriptor, (
                "\r\n\r\nspeckit-pro harm halt: one-time clear token (shown once, only here):\r\n"
                f"{token}\r\n\r\n").encode("ascii"))
        finally:
            os.close(descriptor)
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return False


def harm_halt(root: Any, inputs: dict[str, Any], mode: str) -> dict[str, Any]:
    """Report the halt, record it, or clear it with its one-time token; dry_run changes nothing."""
    request = {key: value for key, value in inputs.items() if key != "repo_root"}
    extra: dict[str, Any] = {}
    if mode == "read_only":
        require_fields(request, set(), "inputs")
    else:
        action = request.get("action")
        fields = {"halt": {"action", "reason", "evidence", "last_safe_state"}, "clear": {"action", "token"}}
        if action not in fields:
            raise SelectionError(f"action must be one of {sorted(fields)}")
        request = require_fields(request, fields[action], "inputs")
        if mode == "apply" and action == "halt":
            recorded = record_halt(root, request["reason"], require_text(request["evidence"], "evidence"),
                                   request["last_safe_state"])
            extra["clear_token"] = recorded["clear_token"]
        elif mode == "apply":
            clear_halt(root, request["token"])
        elif action == "clear":
            extra = planned_clear(root, request["token"])
    record = stored_halt(root)
    return {"halted": record is not None, "resume": "refused" if record else "allowed", "record": record,
            "writes_state": mode == "apply", **extra}


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
        remediation_actions=["Read the record with harm-halt in read_only mode.",
                             "Resolve the cause; only the one-time token shown on the owner's terminal clears it."])])


REFUSAL = Refusal(
    "invalid_harm_halt_request",
    "Send no inputs to read; to record, action halt with a harm-halt reason, evidence and the last safe state; "
    "to clear, action clear with the one-time token shown on the owner's terminal.",
    ["Correct the named field.",
     "Rerun harm-halt; a refused request keeps any standing record or publication lock for a human to inspect."],
)


def run_harm_halt_helper(entry: Any, request: Any) -> dict[str, Any]:
    return run_contained_helper(entry, request, harm_halt, REFUSAL)
