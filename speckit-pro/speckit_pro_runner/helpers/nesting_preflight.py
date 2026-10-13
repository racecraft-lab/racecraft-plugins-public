"""Nesting preflight: pick the plan-stage dispatch mode from an observed nested spawn (ADR 0026).

The orchestrator dispatches one probe two levels deep and reports whether the nested spawn
worked. A configured depth is recorded but never decides: Codex's `agents.max_depth` is ignored
by its V2 backend. Depth never fails a run, so every input answers `ok`, and anything short of
an observed allowed spawn means flat mode.
"""

from __future__ import annotations

from typing import Any

from ..envelope import response

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
    return raw if isinstance(raw, int) and not isinstance(raw, bool) and raw >= 0 else None


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
        "prerequisite": PREREQUISITES[known_host] if known_host and mode == "flat" else None,
    }


def run_nesting_preflight_helper(entry: Any, request: Any) -> dict[str, Any]:
    return response("ok", request_id=request.request_id, data=nesting_mode(request.inputs))
