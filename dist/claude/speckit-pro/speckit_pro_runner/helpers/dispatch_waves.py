"""Dispatch waves for the planning phases (ADR 0018, decision P4): which agents a host launches together."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from ..strict_input import require_text
from .read_only import consensus_route

ModelFor = Callable[[str], dict[str, dict[str, str]]]

CHECKLIST_PHASE = "Checklist"
CONSENSUS_PHASES = frozenset({"Clarify", "Checklist", "Analyze"})
DOMAIN_NAME = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")
MAX_DOMAINS, MAX_ITEMS, MAX_LINE = 12, 100, 2000
ITEM_FIELDS = {"line", "confidence"}


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


def dispatch(agent: str, model_for: ModelFor, **inputs: Any) -> dict[str, Any]:
    return {"agent": agent, "inputs": inputs, "model": model_for(agent)}


def consensus_waves(items: list[dict[str, Any]], model_for: ModelFor) -> list[list[dict[str, Any]]]:
    """The analysts of a security round form one wave and the single analysts of low-confidence items another.

    Items the executor answered with confidence (tier `recommendation`) have no analysts. `item` is the 1-based
    position in the supplied list, the order the Consensus Resolution Log keeps.
    """
    waves: dict[str, list[dict[str, Any]]] = {"security": [], "low_confidence": [], "recommendation": []}
    for number, item in enumerate(items, 1):
        route = consensus_route(item)
        waves[route["tier"]] += [dispatch(analyst.removeprefix("speckit-pro:"), model_for, item=number, line=item["line"])
                                 for analyst in route["analysts"]]
    return [waves["security"], waves["low_confidence"]]


def checklist_waves(domains: list[str], model_for: ModelFor) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Every domain's executor in one wave, and the verify re-run of each domain in the wave that follows."""
    return ([dispatch("checklist-executor", model_for, domain=name) for name in domains],
            [dispatch("checklist-executor", model_for, domain=name, **{"pass": "verify"}) for name in domains])


def compose_waves(domains: list[str], items: list[dict[str, Any]], model_for: ModelFor) -> list[list[dict[str, Any]]]:
    """Domain wave, then the consensus waves for the items, then the verify wave; a wave with no agents is dropped."""
    run, verify = checklist_waves(domains, model_for) if domains else ([], [])
    return [wave for wave in [run, *consensus_waves(items, model_for), verify] if wave]
