#!/usr/bin/env python3
"""Judge whether the capability notes in a Claude transcript are grounded.

The evidence note contract lives in ``capability-discovery.md`` (Evidence
Output) and ``grounding.md``:

    Capability path: <need> -> <source>; Evidence: <citations>; Confidence: <high|medium|low> (<reason>)

``Evidence`` may hold several citations, so it may contain semicolons. The
``source`` is one of three kinds. A tool source names a capability and is
grounded only when that tool completed without error. A local source names a
repository file, and a fallback source discloses that no installed capability
was used. Neither of the last two has a tool call to match.
"""

from __future__ import annotations

import re
from pathlib import Path

from .transcript_helpers import event_blocks, load_events

GROUNDING_NOTE_RE = re.compile(
    r"Capability path:[^\n]*?->\s*(?P<source>[^;\n]+?)\s*;"
    r"\s*Evidence:[^\n]*?;\s*Confidence:\s*(?:high|medium|low)\b",
    re.IGNORECASE,
)
LOCAL_SOURCE_RE = re.compile(r"[/\\]|\.[A-Za-z0-9]{1,5}$")


def source_kind(source: str) -> str:
    """Classify a note's source as ``fallback``, ``local`` or ``tool``."""
    if "fallback" in source.lower():
        return "fallback"
    if not source.startswith("mcp__") and LOCAL_SOURCE_RE.search(source):
        return "local"
    return "tool"


def extract_completed_tool_names(transcript: str | Path) -> list[str]:
    events = load_events(transcript)
    completed_ids = {
        block.get("tool_use_id")
        for event in events
        if event.get("type") == "user"
        for block in event_blocks(event)
        if block.get("type") == "tool_result" and not bool(block.get("is_error", False))
    }
    return sorted(
        {
            str(block.get("name", ""))
            for event in events
            if event.get("type") == "assistant"
            for block in event_blocks(event)
            if block.get("type") == "tool_use" and block.get("id") in completed_ids
        }
    )


def extract_assistant_text(transcript: str | Path) -> list[str]:
    return [
        str(block.get("text", ""))
        for event in load_events(transcript)
        if event.get("type") == "assistant"
        for block in event_blocks(event)
        if block.get("type") == "text"
    ]


def extract_capability_citations(transcript: str | Path) -> list[str]:
    return sorted({match.group("source") for text in extract_assistant_text(transcript) for match in GROUNDING_NOTE_RE.finditer(text)})


def has_malformed_citation(transcript: str | Path) -> bool:
    text = "\n".join(extract_assistant_text(transcript))
    return text.count("Capability path:") > len(GROUNDING_NOTE_RE.findall(text))


def grounding_verdict(transcript: str | Path) -> str:
    if has_malformed_citation(transcript):
        return "ungrounded"
    completed = set(extract_completed_tool_names(transcript))
    tool_sources = {source for source in extract_capability_citations(transcript) if source_kind(source) == "tool"}
    return "grounded" if tool_sources <= completed else "ungrounded"
