"""Dispatch waves for the planning phases (ADR 0018, decision P4): which agents a host launches together."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any, NamedTuple

from ..strict_input import require_text
from .read_only import consensus_route

ModelFor = Callable[[str], dict[str, dict[str, str]]]

CHECKLIST_PHASE = "Checklist"
CONSENSUS_PHASES = frozenset({"Clarify", "Checklist", "Analyze"})
DOMAIN_NAME = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")
MAX_DOMAINS, MAX_ITEMS, MAX_LINE = 12, 100, 2000
ITEM_FIELDS = {"line", "confidence"}
WAVE_INPUTS = ("domains", "items", "max_agents")
MAX_AGENTS = 1000
# Checklist executors still edit spec.md and plan.md themselves, so concurrent domain runs could drop each other's
# edits. False gives each domain run a wave of its own. Flip it once executors only propose edits (#1201).
CHECKLIST_DOMAINS_PARALLEL = False


def checked_domains(phase: str, raw: Any) -> list[str]:
    """Checklist domain names in dispatch order; ValueError when the phase has no domains or the list is unusable."""
    if phase != CHECKLIST_PHASE:
        raise ValueError("domains apply to the Checklist phase only")
    if not isinstance(raw, list) or not 0 < len(raw) <= MAX_DOMAINS:
        raise ValueError(f"domains must list 1 to {MAX_DOMAINS} names")
    names = [require_text(name, "domain") for name in raw]
    if len(set(names)) != len(names) or not all(DOMAIN_NAME.fullmatch(name) for name in names):
        raise ValueError("domains must be distinct lowercase names of letters, digits, hyphens and underscores")
    return names


def checked_items(phase: str, raw: Any) -> list[dict[str, Any]]:
    """Unresolved consensus items in executor order, each with its line and optional confidence."""
    if phase not in CONSENSUS_PHASES:
        raise ValueError("items apply to the Clarify, Checklist and Analyze phases only")
    if not isinstance(raw, list) or len(raw) > MAX_ITEMS:
        raise ValueError(f"items must be a list of at most {MAX_ITEMS} records")
    for item in raw:
        if not isinstance(item, dict) or not {"line"} <= item.keys() <= ITEM_FIELDS:
            raise ValueError("each item must be an object with a line and an optional confidence")
        if len(require_text(item["line"], "item line")) > MAX_LINE:
            raise ValueError(f"item line must be at most {MAX_LINE} characters")
        consensus_route(item)
    return raw


class WaveRequest(NamedTuple):
    domains: list[str]
    items: list[dict[str, Any]]
    max_agents: int


def checked_wave_request(phase: str, raw: dict[str, Any]) -> WaveRequest:
    """The optional wave inputs the caller supplied. `max_agents`, the host's concurrent-agent limit, is required with
    `domains` or `items`: Claude Code's SUBAGENT_WAVE_SIZE, Codex's subagent_slots (1 when the host exposes no count)."""
    domains = checked_domains(phase, raw["domains"]) if "domains" in raw else []
    items = checked_items(phase, raw["items"]) if "items" in raw else []
    limit = raw.get("max_agents", 1)
    if ("domains" in raw or "items" in raw) and "max_agents" not in raw:
        raise ValueError("max_agents is required with domains or items")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 0 < limit <= MAX_AGENTS:
        raise ValueError(f"max_agents must be a whole number from 1 to {MAX_AGENTS}")
    return WaveRequest(domains, items, limit)


def dispatch(agent: str, model_for: ModelFor, **inputs: Any) -> dict[str, Any]:
    return {"agent": agent, "inputs": inputs, "model": model_for(agent)}


def consensus_waves(items: list[dict[str, Any]], model_for: ModelFor) -> list[list[dict[str, Any]]]:
    """The analysts of a security round form one wave and the single analysts of low-confidence items another.

    Items the executor answered with confidence (tier `recommendation`) have no analysts. `item` is the 1-based
    position in the supplied list, the order the Consensus Resolution Log keeps. An entry never repeats the item's
    text: the orchestrator already holds it, so no item text passes through the helper into a dispatch prompt.
    """
    waves: dict[str, list[dict[str, Any]]] = {"security": [], "low_confidence": [], "recommendation": []}
    for number, item in enumerate(items, 1):
        route = consensus_route(item)
        waves[route["tier"]] += [dispatch(analyst.removeprefix("speckit-pro:"), model_for, item=number)
                                 for analyst in route["analysts"]]
    return [waves["security"], waves["low_confidence"]]


def checklist_waves(domains: list[str], model_for: ModelFor) -> tuple[list[list[dict[str, Any]]], list[dict[str, Any]]]:
    """The domain-run waves, one per domain unless CHECKLIST_DOMAINS_PARALLEL, and the verify wave of every domain.

    A verify pass keeps spec.md and plan.md unchanged, so its entries can share a wave either way.
    """
    runs = [dispatch("checklist-executor", model_for, domain=name) for name in domains]
    verify = [dispatch("checklist-executor", model_for, domain=name, **{"pass": "verify"}) for name in domains]
    return ([runs] if CHECKLIST_DOMAINS_PARALLEL else [[run] for run in runs]), verify


def compose_waves(request: WaveRequest, model_for: ModelFor) -> list[list[dict[str, Any]]]:
    """Domain waves ({domain}), the security and low-confidence waves ({item}), then the verify wave
    ({domain, pass: "verify"}); a wave with no agents is dropped, so no domains and no items give no waves.

    A wave larger than the host's limit becomes consecutive sub-waves of at most `max_agents`, in entry order.
    """
    runs, verify = checklist_waves(request.domains, model_for)
    size = request.max_agents
    return [wave[start:start + size] for wave in [*runs, *consensus_waves(request.items, model_for), verify]
            for start in range(0, len(wave), size)]
