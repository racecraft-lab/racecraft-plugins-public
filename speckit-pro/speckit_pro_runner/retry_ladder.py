"""The retry ladder (ADR 0004): three attempts for a failing check, for the whole run.

A check is identified by the command digest the runner fingerprinted as failing.
Its rungs, in order, are the current agent, a fresh agent guided by a consensus
diagnosis, and the strongest model at max effort with the full failure history.
The count lives in the ledger's own dispatch records and never resets: a check
that passes and later fails again resumes at its next unspent rung.

An interrupted dispatch (an analyst turn limit, a compaction, a lost session)
spends no rung the first time it is rerun. A second interruption of the same
rung spends it. The functions here take plain dispatch dicts and know nothing of
the ledger file.
"""

from __future__ import annotations

from typing import Any, NamedTuple

RUNGS = 3
INTERRUPTIONS_PER_RUNG = 2  # the first is free; the second spends the rung


class RungSettings(NamedTuple):
    """Who runs a rung: `role` names the agent; a None model or effort is the current agent's own."""

    role: str
    model: str | None
    effort: str | None


# Rung 2 matches the shipped `implement-executor` on each host and rung 3 raises it to max effort;
# a test pins both to the agent files, so this table cannot drift from them.
HOST_RUNGS: dict[str, tuple[RungSettings, ...]] = {
    "claude": (RungSettings("current_agent", None, None), RungSettings("fresh_agent", "opus", "xhigh"),
               RungSettings("strongest_model", "opus", "max")),
    "codex": (RungSettings("current_agent", None, None), RungSettings("fresh_agent", "gpt-6-sol", "xhigh"),
              RungSettings("strongest_model", "gpt-6-sol", "max")),
}


def rung_settings(host: Any, rung: int) -> RungSettings:
    """The role, model and effort the given host runs a rung with."""
    if host not in HOST_RUNGS:
        raise ValueError("retry ladder host must be claude or codex")
    return HOST_RUNGS[host][rung - 1]


def is_interrupted(item: dict[str, Any]) -> bool:
    """True for a dispatch the host cut short: still unknown, or reported failed as interrupted."""
    return item["outcome"] == "unknown" or item.get("interrupted") is True


def next_rung(earlier: list[dict[str, Any]]) -> int | None:
    """The rung a check's next dispatch runs, or None when the ladder is spent.

    `earlier` is the check's settled and interrupted ladder dispatches, oldest first.
    """
    for rung in range(1, RUNGS + 1):
        at_rung = [item for item in earlier if item["retry_ladder"]["rung"] == rung]
        settled = any(item["outcome"] in {"completed", "failed"} and not is_interrupted(item) for item in at_rung)
        if not settled and sum(map(is_interrupted, at_rung)) < INTERRUPTIONS_PER_RUNG:
            return rung
    return None


def replay_rungs(dispatches: list[dict[str, Any]]) -> bool:
    """True when each dispatch ran the rung `next_rung` gives once the dispatches before it had settled."""
    for index, item in enumerate(dispatches):
        earlier = dispatches[:index]
        if any(prior["outcome"] in {"reserved", "running"} for prior in earlier):
            return False
        if item["retry_ladder"]["rung"] != next_rung(earlier):
            return False
    return True
