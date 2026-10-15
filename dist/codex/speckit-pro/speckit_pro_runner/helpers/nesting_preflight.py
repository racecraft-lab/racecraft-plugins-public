"""Nesting preflight: pick the plan-stage dispatch mode from an observed nested spawn (ADR 0026).

The orchestrator dispatches one probe two levels deep and reports whether the nested spawn
worked. A configured depth is recorded but never decides: Codex's `agents.max_depth` is ignored
by its V2 backend. Depth never fails a run, so every probe input answers `ok`, and anything short
of an observed allowed spawn means flat mode. Apply mode alone can refuse, and only when it
cannot write the run's existing autopilot-state.json.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import autopilot_state
from ..atomic_write import AtomicWriteInterrupted
from ..envelope import diagnostic, response
from ..json_schema import json_values_equal
from ..strict_input import require_text
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


def nesting_evidence_matches(data: dict[str, Any]) -> bool:
    """Accept only a result the nesting policy can actually produce.

    Shape and types are checked by the state schema first. Replaying all probe
    outcomes (including an invalid probe) keeps reason/mode/prerequisite rules
    here with their producer, rather than copying them into the consumer.
    """
    inputs = {"host": data.get("host")}
    if data.get("configured_depth") is not None:
        inputs["configured_depth"] = data["configured_depth"]
    return any(
        json_values_equal(data, nesting_mode({**inputs, "nested_spawn": outcome}))
        for outcome in (*SPAWN_OUTCOMES, None)
    )


def persist_nesting_mode(root: Path, state_file: Any, envelope: dict[str, Any]) -> None:
    """Preserve the current state and replace only its nesting record, refusing stale writes."""
    autopilot_state.update(root, state_file, lambda state: state.update(nesting_mode=envelope))


def apply_nesting_preflight_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Resolve and publish the complete envelope before root response compaction."""
    root = resolve_repo_root(request.inputs)
    if isinstance(root, dict):
        return response("input_error", request_id=request.request_id, data={"writes_state": False}, diagnostics=[root])
    inputs = {key: value for key, value in request.inputs.items() if key not in {"repo_root", "state_file"}}
    envelope = response("ok", request_id=request.request_id, data=nesting_mode(inputs))
    try:
        request_id = require_text(request.request_id, "request_id")
        if autopilot_state.UUID_PATTERN.search(request_id):
            raise ValueError("request_id must be a public slug without a raw UUID")
        persist_nesting_mode(root, request.inputs.get("state_file"), envelope)
    except (ValueError, RecursionError) as error:
        return response("input_error", request_id=request.request_id, data={"writes_state": False}, diagnostics=[diagnostic(
            "nesting_state_invalid", str(error), remediation_summary="Correct request_id and state_file, then retry the nesting preflight.")])
    except OSError as error:
        return response("internal_failure", request_id=request.request_id,
                        data={"writes_state": isinstance(error, AtomicWriteInterrupted)}, diagnostics=[diagnostic(
                            "nesting_state_write_failed", str(error),
                            remediation_summary="Inspect the current state and write failure before one repair attempt.")])
    return envelope
