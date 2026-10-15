"""Nesting preflight: pick the plan-stage dispatch mode from an observed nested spawn (ADR 0026).

The orchestrator dispatches one probe two levels deep and reports whether the nested spawn
worked. A configured depth is recorded but never decides: Codex's `agents.max_depth` is ignored
by its V2 backend. Depth never fails a run, so every input answers `ok`, and anything short of
an observed allowed spawn means flat mode.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ..atomic_write import file_identity, open_safe_parent_fd, snapshot_write_target_fd, write_bytes_atomic
from ..envelope import diagnostic, response
from ..strict_input import require_text, unique_object
from ..trusted_io import resolve_repo_root

SCHEMA_VERSION = "nesting-mode/v1"
# Pinned to the `mode` enum in the canary receipt schema by test-nesting-preflight.py.
MODES = ("flat", "nested")
INPUTS = frozenset({"host", "nested_spawn", "configured_depth"})
SPAWN_OUTCOMES = frozenset({"allowed", "refused", "not_run"})
PREREQUISITES = {
    "claude-code": (
        "Claude Code withholds the Agent tool from a subagent at its depth limit. Set "
        "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH to 2 or more (the default is 3 from Claude Code 2.1.219; "
        "1 turns nesting off), then start a new run for nested mode. This run continues in flat mode."
    ),
    "codex": (
        "This Codex backend refused a nested spawn. agents.max_depth applies only to V1 agent threads "
        "and is ignored by V2, so changing it may not enable nesting. This run continues in flat mode."
    ),
}


def configured_depth(raw: Any) -> int | None:
    """Record a sane depth for the receipt; a bad value is dropped, never an error."""
    return raw if type(raw) is int and raw >= 0 else None  # an exact int, so bool is out


def nesting_mode(inputs: dict[str, Any]) -> dict[str, Any]:
    host = inputs.get("host")
    outcome = inputs.get("nested_spawn", "not_run")
    valid = (isinstance(host, str) and host in PREREQUISITES and not set(inputs) - INPUTS
             and isinstance(outcome, str) and outcome in SPAWN_OUTCOMES
             and ("configured_depth" not in inputs or configured_depth(inputs["configured_depth"]) is not None))
    if not valid:
        reason, mode = "probe_invalid", MODES[0]
    elif outcome == "allowed":
        reason, mode = "nested_spawn_allowed", MODES[1]
    else:
        reason, mode = ("nested_spawn_refused" if outcome == "refused" else "probe_not_run"), MODES[0]
    known_host = host if isinstance(host, str) and host in PREREQUISITES else None
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "reason": reason,
        "host": known_host,
        "configured_depth": configured_depth(inputs.get("configured_depth")),
        "prerequisite": PREREQUISITES[known_host] if known_host and reason == "nested_spawn_refused" else None,
    }


def run_nesting_preflight_helper(entry: Any, request: Any) -> dict[str, Any]:
    return response("ok", request_id=request.request_id, data=nesting_mode(request.inputs))


def persist_nesting_mode(root: Path, state_file: Any, envelope: dict[str, Any]) -> None:
    """Preserve the current state and replace only its nesting record, refusing stale writes."""
    relative = Path(require_text(state_file, "state_file"))
    if relative.is_absolute() or any(part.casefold() == ".git" for part in relative.parts):
        raise ValueError("state_file must be a repository-relative state path outside .git")
    target = root / relative
    opened = open_safe_parent_fd(target, root, create=False)
    if opened is None:
        raise ValueError("state_file parent is missing")
    parent_fd, name, _ = opened
    try:
        snapshot = snapshot_write_target_fd(parent_fd, name)
        snapshot["parent"] = file_identity(os.fstat(parent_fd))
    finally:
        os.close(parent_fd)
    if not snapshot["exists"]:
        raise ValueError("state_file must already exist")
    state = json.loads(snapshot["content"], object_pairs_hook=unique_object)
    if not isinstance(state, dict):
        raise ValueError("state_file must hold a JSON object")
    state["nesting_mode"] = envelope
    content = (json.dumps(state, indent=2, allow_nan=False) + "\n").encode("utf-8")
    write_bytes_atomic(target, content, trust_root=root, expected_snapshot=snapshot)


def apply_nesting_preflight_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Resolve and publish the complete envelope before root response compaction."""
    root = resolve_repo_root(request.inputs)
    if isinstance(root, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[root])
    inputs = {key: value for key, value in request.inputs.items() if key not in {"repo_root", "state_file"}}
    envelope = response("ok", request_id=request.request_id, data=nesting_mode(inputs))
    try:
        persist_nesting_mode(root, request.inputs.get("state_file"), envelope)
    except (ValueError, OSError, RecursionError) as error:
        return response("input_error", request_id=request.request_id, diagnostics=[diagnostic(
            "nesting_state_invalid", str(error), remediation_summary="Correct state_file and retry the nesting preflight.")])
    return envelope
