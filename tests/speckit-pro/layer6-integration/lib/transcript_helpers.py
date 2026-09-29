#!/usr/bin/env python3
"""Parse Claude stream-JSON transcripts for Layer 6 fixtures."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


JsonObject = dict[str, Any]
VALID_SCOPES = frozenset({"all", "orchestrator", "sidechain"})


def load_events(transcript: str | Path) -> list[JsonObject]:
    events: list[JsonObject] = []
    for line_number, line in enumerate(Path(transcript).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"event {line_number} is not a JSON object")
        events.append(value)
    return events


def event_blocks(event: JsonObject) -> list[JsonObject]:
    message = event.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    return [item for item in content if isinstance(item, dict)] if isinstance(content, list) else []


def _in_scope(event: JsonObject, scope: str) -> bool:
    if scope not in VALID_SCOPES:
        raise ValueError(f"invalid scope: {scope}")
    sidechain = bool(event.get("isSidechain", False))
    return scope == "all" or (scope == "sidechain" and sidechain) or (scope == "orchestrator" and not sidechain)


def extract_orchestrator_dispatches(transcript: str | Path) -> list[JsonObject]:
    dispatches: list[JsonObject] = []
    for event in load_events(transcript):
        if event.get("type") != "assistant" or not _in_scope(event, "orchestrator"):
            continue
        for block in event_blocks(event):
            if block.get("type") != "tool_use" or block.get("name") != "Agent":
                continue
            inputs = block.get("input") if isinstance(block.get("input"), dict) else {}
            dispatches.append(
                {
                    "subagent_type": inputs.get("subagent_type"),
                    "description": inputs.get("description", ""),
                    "prompt": inputs.get("prompt", ""),
                    "id": block.get("id"),
                }
            )
    return dispatches


def extract_dispatch_order(transcript: str | Path) -> list[str]:
    return [str(item.get("subagent_type", "")) for item in extract_orchestrator_dispatches(transcript)]


def count_dispatches_to(transcript: str | Path, subagent_type: str) -> int:
    return sum(item.get("subagent_type") == subagent_type for item in extract_orchestrator_dispatches(transcript))


def assert_dispatched_to(transcript: str | Path, subagent_type: str) -> bool:
    return count_dispatches_to(transcript, subagent_type) > 0


def assert_not_dispatched_to(transcript: str | Path, subagent_type: str) -> bool:
    return count_dispatches_to(transcript, subagent_type) == 0


def find_forbidden_agent_spawns(transcript: str | Path) -> list[JsonObject]:
    matches: list[JsonObject] = []
    for event in load_events(transcript):
        if event.get("type") != "assistant" or not _in_scope(event, "sidechain"):
            continue
        for block in event_blocks(event):
            if block.get("type") != "tool_use" or block.get("name") != "Agent":
                continue
            inputs = block.get("input") if isinstance(block.get("input"), dict) else {}
            matches.append({"subagent_type": inputs.get("subagent_type"), "id": block.get("id")})
    return matches


def assert_no_forbidden_spawns(transcript: str | Path) -> bool:
    return not find_forbidden_agent_spawns(transcript)


def _result_content(block: JsonObject) -> str:
    content = block.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
    return ""


def extract_subagent_responses(transcript: str | Path) -> list[JsonObject]:
    events = load_events(transcript)
    dispatches = [
        {"id": item.get("id"), "subagent_type": item.get("subagent_type")}
        for item in extract_orchestrator_dispatches(transcript)
    ]
    results: list[JsonObject] = []
    for event in events:
        if event.get("type") != "user" or not _in_scope(event, "orchestrator"):
            continue
        for block in event_blocks(event):
            if block.get("type") == "tool_result":
                results.append({"tool_use_id": block.get("tool_use_id"), "content": _result_content(block)})

    paired: list[JsonObject] = []
    for dispatch in dispatches:
        for result in results:
            if result.get("tool_use_id") == dispatch.get("id"):
                paired.append({"subagent_type": dispatch.get("subagent_type"), "content": result.get("content", "")})
    return paired


def get_response_content(transcript: str | Path, subagent_type: str) -> str:
    return "\n---\n".join(
        str(item.get("content", ""))
        for item in extract_subagent_responses(transcript)
        if item.get("subagent_type") == subagent_type
    )


def assert_response_contains(transcript: str | Path, subagent_type: str, substring: str) -> bool:
    return substring in get_response_content(transcript, subagent_type)


def extract_skill_invocations(transcript: str | Path, scope: str = "all") -> list[JsonObject]:
    invocations: list[JsonObject] = []
    for event in load_events(transcript):
        if event.get("type") != "assistant" or not _in_scope(event, scope):
            continue
        for block in event_blocks(event):
            if block.get("type") != "tool_use" or block.get("name") != "Skill":
                continue
            inputs = block.get("input") if isinstance(block.get("input"), dict) else {}
            invocations.append(
                {
                    "skill": inputs.get("skill", ""),
                    "args": inputs.get("args", ""),
                    "isSidechain": bool(event.get("isSidechain", False)),
                }
            )
    return invocations


def count_skill_invocations(transcript: str | Path, skill_pattern: str, scope: str = "all") -> int:
    pattern = re.compile(skill_pattern, re.IGNORECASE)
    return sum(bool(pattern.search(str(item.get("skill", "")))) for item in extract_skill_invocations(transcript, scope))


def assert_skill_not_invoked(transcript: str | Path, skill_pattern: str, scope: str = "all") -> bool:
    return count_skill_invocations(transcript, skill_pattern, scope) == 0


def assert_skill_invoked(transcript: str | Path, skill_pattern: str, scope: str = "all") -> bool:
    return count_skill_invocations(transcript, skill_pattern, scope) > 0


def assert_transcript_contains_term(transcript: str | Path, term: str) -> bool:
    return term in Path(transcript).read_text(encoding="utf-8")


def assert_transcript_not_contains_term(transcript: str | Path, term: str) -> bool:
    return not assert_transcript_contains_term(transcript, term)


def extract_tool_uses(transcript: str | Path, scope: str = "all") -> list[JsonObject]:
    tool_uses: list[JsonObject] = []
    for event in load_events(transcript):
        if event.get("type") != "assistant" or not _in_scope(event, scope):
            continue
        for block in event_blocks(event):
            if block.get("type") == "tool_use":
                tool_uses.append(
                    {
                        "name": block.get("name"),
                        "id": block.get("id"),
                        "isSidechain": bool(event.get("isSidechain", False)),
                    }
                )
    return tool_uses


def extract_tool_use_names(transcript: str | Path, scope: str = "all") -> list[str]:
    return sorted({str(item.get("name", "")) for item in extract_tool_uses(transcript, scope)})


def tool_invoked(transcript: str | Path, name: str, scope: str = "all") -> bool:
    return name in extract_tool_use_names(transcript, scope)


def _emit_json(value: Any) -> int:
    json.dump(value, sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


def _usage() -> int:
    print(
        "usage: transcript_helpers.py extract-orchestrator-dispatches <transcript.jsonl>\n"
        "       transcript_helpers.py assert-dispatched-to <transcript.jsonl> <subagent_type>",
        file=sys.stderr,
    )
    return 2


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        return _usage()
    command, transcript, *args = argv
    try:
        if command == "extract-orchestrator-dispatches" and not args:
            return _emit_json(extract_orchestrator_dispatches(transcript))
        if command == "assert-dispatched-to" and len(args) == 1:
            return 0 if assert_dispatched_to(transcript, args[0]) else 1
        return _usage()
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"transcript_helpers.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
