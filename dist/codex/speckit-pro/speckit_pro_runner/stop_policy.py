"""The closed set of reasons a speckit-pro autopilot run may involve a human.

Every human item in `finalize-run` and the execution-control ledger names one
of these reasons. The shared stop-policy reference and the parity test cite
this set, so guidance cannot name a reason the runner does not know.

Each reason has exactly one class:

- ``authority``: the next step needs a power agents do not hold.
- ``exhausted``: the problem failed every escalation tier, or the tier-3 cap.
- ``harm_halt``: continuing could compound harm, so the whole run halts now.
"""

from __future__ import annotations

AUTHORITY = "authority"
EXHAUSTED = "exhausted"
HARM_HALT = "harm_halt"

STOP_CLASSES = frozenset({AUTHORITY, EXHAUSTED, HARM_HALT})

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
                "all_tiers_failed": EXHAUSTED,
                "tier3_cap_reached": EXHAUSTED,
                "tampering_or_forged_evidence": HARM_HALT,
                "secret_exposure": HARM_HALT,
                "integrity_failure": HARM_HALT}


def stop_class(reason: str) -> str:
    """Return the class of a stop reason; an unknown reason fails closed."""
    try:
        return STOP_REASONS[reason]
    except KeyError:
        raise ValueError(f"unknown stop reason: {reason!r}") from None
