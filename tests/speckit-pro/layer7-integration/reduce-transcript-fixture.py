#!/usr/bin/env python3
"""Reduce a scrubbed transcript to the fields required for parser replay."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO


JsonObject = dict[str, Any]


def load_jsonl(path: Path) -> list[JsonObject]:
    events: list[JsonObject] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"event {line_number} is not a JSON object")
        events.append(value)
    return events


def _blocks(event: JsonObject) -> list[JsonObject]:
    message = event.get("message")
    content = message.get("content", []) if isinstance(message, dict) else []
    return [block for block in content if isinstance(block, dict)] if isinstance(content, list) else []


def empty_if_none(value: Any) -> Any:
    return "" if value is None else value


def response_keywords(expected: JsonObject, subagent_type: Any) -> list[str]:
    keywords: list[str] = []
    assertions = expected.get("response_assertions", [])
    if not isinstance(assertions, list):
        return keywords
    for assertion in assertions:
        if not isinstance(assertion, dict) or assertion.get("subagent_type") != subagent_type:
            continue
        must_contain_any = assertion.get("must_contain_any", [])
        if isinstance(must_contain_any, list):
            keywords.extend(str(value) for value in must_contain_any[:1])
        section_keywords = assertion.get("must_contain_section_keywords", [])
        if isinstance(section_keywords, list):
            keywords.extend(str(value) for value in section_keywords)
    return keywords


def reduced_response(expected: JsonObject, subagent_type: Any) -> str:
    prefix = f"Reduced parser fixture response for {subagent_type}"
    keywords = response_keywords(expected, subagent_type)
    return f"{prefix}: {' '.join(keywords)}" if keywords else prefix


def reduce_transcript(events: list[JsonObject], expected: JsonObject) -> list[JsonObject]:
    reduced: list[JsonObject] = []
    id_map: dict[str, str] = {}
    agent_for: dict[str, Any] = {}
    sequence = 0

    for event in events:
        if event.get("type") == "assistant":
            output_blocks: list[JsonObject] = []
            for block in _blocks(event):
                if block.get("type") != "tool_use" or block.get("name") not in {"Agent", "Skill"}:
                    continue
                sequence += 1
                new_id = f"tool-{sequence:03d}"
                old_id = block.get("id")
                if isinstance(old_id, str):
                    id_map[old_id] = new_id
                inputs = block.get("input") if isinstance(block.get("input"), dict) else {}
                if block.get("name") == "Agent":
                    subagent_type = empty_if_none(inputs.get("subagent_type", ""))
                    agent_for[new_id] = subagent_type
                    output_blocks.append(
                        {
                            "type": "tool_use",
                            "id": new_id,
                            "name": "Agent",
                            "input": {
                                "subagent_type": subagent_type,
                                "description": empty_if_none(inputs.get("description", "")),
                                "prompt": "",
                            },
                        }
                    )
                else:
                    output_blocks.append(
                        {
                            "type": "tool_use",
                            "id": new_id,
                            "name": "Skill",
                            "input": {"skill": empty_if_none(inputs.get("skill", "")), "args": ""},
                        }
                    )
            if output_blocks:
                reduced.append(
                    {
                        "type": "assistant",
                        "isSidechain": bool(event.get("isSidechain", False)),
                        "message": {"role": "assistant", "content": output_blocks},
                    }
                )
            continue

        if event.get("type") == "user":
            output_results: list[JsonObject] = []
            for block in _blocks(event):
                if block.get("type") != "tool_result":
                    continue
                old_id = block.get("tool_use_id")
                new_id = id_map.get(old_id) if isinstance(old_id, str) else None
                if new_id is None:
                    continue
                subagent_type = agent_for.get(new_id, "")
                output_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": new_id,
                        "content": reduced_response(expected, subagent_type),
                    }
                )
            if output_results:
                reduced.append(
                    {
                        "type": "user",
                        "isSidechain": bool(event.get("isSidechain", False)),
                        "message": {"role": "user", "content": output_results},
                    }
                )
    return reduced


def write_jsonl(events: list[JsonObject], destination: TextIO) -> None:
    for event in events:
        json.dump(event, destination, ensure_ascii=False, separators=(",", ":"))
        destination.write("\n")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: reduce-transcript-fixture.py <scrubbed-transcript.jsonl> <expected.json>", file=sys.stderr)
        return 2
    transcript_path = Path(argv[0])
    expected_path = Path(argv[1])
    if not transcript_path.is_file():
        print(f"reduce-transcript-fixture.py: transcript not found: {transcript_path}", file=sys.stderr)
        return 1
    if not expected_path.is_file():
        print(f"reduce-transcript-fixture.py: expected.json not found: {expected_path}", file=sys.stderr)
        return 1
    try:
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        if not isinstance(expected, dict):
            raise ValueError("expected JSON must be an object")
        write_jsonl(reduce_transcript(load_jsonl(transcript_path), expected), sys.stdout)
        return 0
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"reduce-transcript-fixture.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
