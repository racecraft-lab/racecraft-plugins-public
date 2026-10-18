"""The closed set of reasons a speckit-pro run may involve a human.

Every human item in `finalize-run` and the execution-control ledger names one
of these reasons. The shared stop-policy reference and the parity test cite
this set, so guidance cannot name a reason the runner does not know.

Each reason has exactly one class:

- ``authority``: the next step needs a power agents do not hold.
- ``exhausted``: the problem failed every escalation tier, or the tier-3 cap.
- ``harm_halt``: continuing could compound harm, so the whole run halts now.

A run may end only in one of the ``END_STATES`` (a terminal state or the security
interrupt) or on a harm halt (ADR 0010). ``may_end`` is the one query for that.
"""

from __future__ import annotations

from typing import Any

AUTHORITY = "authority"
EXHAUSTED = "exhausted"
HARM_HALT = "harm_halt"

STOP_CLASSES = frozenset({AUTHORITY, EXHAUSTED, HARM_HALT})

TERMINAL = "terminal"
INTERRUPT = "interrupt"
# state -> kind. The two terminal states and the security interrupt are the only non-harm ends.
END_STATES = {"planning_ready_for_review": TERMINAL,
              "ready_for_uat": TERMINAL,
              "security_interrupt": INTERRUPT}

ALL_TIERS_FAILED = "all_tiers_failed"
TIER3_CAP_REACHED = "tier3_cap_reached"

# reason -> class. Authority reasons follow the owner's Q6 list.
STOP_REASONS = {"merge": AUTHORITY,
                "publish": AUTHORITY,
                "protected_push": AUTHORITY,
                "secrets": AUTHORITY,
                "destructive_action": AUTHORITY,
                "human_uat": AUTHORITY,
                "scope_changing_pr_split": AUTHORITY,
                "boundary_file_edit": AUTHORITY,
                "veto_bypass": AUTHORITY,
                "reopen_closed_pr": AUTHORITY,
                "tool_unavailable": AUTHORITY,
                "ambiguous_pr_record": AUTHORITY,
                "plan_stage_boundary": AUTHORITY,
                "scaffold_complete": AUTHORITY,
                "speckit_cli_older": AUTHORITY,
                ALL_TIERS_FAILED: EXHAUSTED,
                TIER3_CAP_REACHED: EXHAUSTED,
                "tampering_or_forged_evidence": HARM_HALT,
                "secret_exposure": HARM_HALT,
                "identity_mismatch": HARM_HALT,
                "concurrent_writer": HARM_HALT}


def stop_class(reason: str) -> str:
    """Return the class of a stop reason; an unknown reason fails closed."""
    try:
        return STOP_REASONS[reason]
    except KeyError:
        raise ValueError(f"unknown stop reason: {reason!r}") from None


def may_end(state: str) -> bool:
    """Whether a run may end in `state`: an end state or a harm halt; anything else, unknown included, may not."""
    return state in END_STATES or STOP_REASONS.get(state) == HARM_HALT


def publication_pending(state: dict[str, Any], dispatches: dict[str, Any]) -> bool:
    """Only evidenced pending work defers the terminal unpushed-commit check."""
    plan = state.get("plan")
    pending_plan = isinstance(plan, list) and any(
        isinstance(row, dict) and row.get("status") in ("pending", "in_progress") for row in plan
    )
    return (pending_plan
            or any(item.get("outcome") in {"reserved", "running", "unknown"} for item in dispatches.values()))
