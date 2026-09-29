#!/usr/bin/env python3
"""Reduce a scrubbed transcript to the fields required for replay.

Replay checks such as ``must_include_terms`` read dispatch prompts and the
orchestrator's own text, so both are kept, redacted with the privacy scan's
patterns. Each subagent response is kept as real text (redacted and capped),
never rebuilt from ``expected.json``, so replay response assertions can fail.
Skill arguments and subagent (sidechain) text are not kept.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO

TEST_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(TEST_LIB) not in sys.path:
    sys.path.insert(0, str(TEST_LIB))

from privacy_patterns import redact_private_text  # noqa: E402

from lib.transcript_helpers import event_blocks, load_events  # noqa: E402

JsonObject = dict[str, Any]


def jq_coalesce_empty(value: Any) -> Any:
    return "" if value is None or value is False else value


def boolean_or_default(value: Any, default: bool = False) -> bool:
    return value if isinstance(value, bool) else default


RESPONSE_LIMIT = 8000


def reduced_response(block: JsonObject) -> str:
    content = block.get("content", "")
    if isinstance(content, list):
        content = "\n".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
    if not isinstance(content, str):
        return ""
    return redact_private_text(content)[:RESPONSE_LIMIT]


def reduced_agent_input(inputs: JsonObject) -> JsonObject:
    reduced_input: JsonObject = {
        "subagent_type": jq_coalesce_empty(inputs.get("subagent_type", "")),
        "description": jq_coalesce_empty(inputs.get("description", "")),
        "prompt": redact_private_text(str(jq_coalesce_empty(inputs.get("prompt", "")))),
    }
    # Keep the dispatch-shape fields the Layer 6 dispatch assertions read.
    for shape_key in ("run_in_background", "isolation"):
        if shape_key in inputs:
            reduced_input[shape_key] = inputs[shape_key]
    return reduced_input


def reduced_assistant_message(
    event: JsonObject, output_blocks: list[JsonObject], message_ids: dict[str, str]
) -> JsonObject:
    message: JsonObject = {"role": "assistant", "content": output_blocks}
    source_message = event.get("message") if isinstance(event.get("message"), dict) else {}
    source_id = source_message.get("id")
    if isinstance(source_id, str):
        # Stream events of one assistant message share an id; keep that link, not the raw id.
        message["id"] = message_ids.setdefault(source_id, f"msg-{len(message_ids) + 1:03d}")
    return message


def reduce_transcript(events: list[JsonObject]) -> list[JsonObject]:
    reduced: list[JsonObject] = []
    id_map: dict[str, str] = {}
    message_ids: dict[str, str] = {}
    sequence = 0

    for event in events:
        if event.get("type") == "assistant":
            output_blocks: list[JsonObject] = []
            is_sidechain = boolean_or_default(event.get("isSidechain", False))
            for block in event_blocks(event):
                if block.get("type") == "text" and not is_sidechain and isinstance(block.get("text"), str):
                    output_blocks.append({"type": "text", "text": redact_private_text(block["text"])})
                    continue
                if block.get("type") != "tool_use" or block.get("name") not in {"Agent", "Skill"}:
                    continue
                sequence += 1
                new_id = f"tool-{sequence:03d}"
                old_id = block.get("id")
                if isinstance(old_id, str):
                    id_map[old_id] = new_id
                inputs = block.get("input") if isinstance(block.get("input"), dict) else {}
                if block.get("name") == "Agent":
                    output_blocks.append(
                        {"type": "tool_use", "id": new_id, "name": "Agent", "input": reduced_agent_input(inputs)}
                    )
                else:
                    output_blocks.append(
                        {
                            "type": "tool_use",
                            "id": new_id,
                            "name": "Skill",
                            "input": {"skill": jq_coalesce_empty(inputs.get("skill", "")), "args": ""},
                        }
                    )
            if output_blocks:
                message = reduced_assistant_message(event, output_blocks, message_ids)
                reduced.append({"type": "assistant", "isSidechain": is_sidechain, "message": message})
            continue

        if event.get("type") == "user":
            output_results: list[JsonObject] = []
            for block in event_blocks(event):
                if block.get("type") != "tool_result":
                    continue
                old_id = block.get("tool_use_id")
                new_id = id_map.get(old_id) if isinstance(old_id, str) else None
                if new_id is None:
                    continue
                output_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": new_id,
                        "content": reduced_response(block),
                    }
                )
            if output_results:
                reduced.append(
                    {
                        "type": "user",
                        "isSidechain": boolean_or_default(event.get("isSidechain", False)),
                        "message": {"role": "user", "content": output_results},
                    }
                )
    return reduced


def write_jsonl(events: list[JsonObject], destination: TextIO) -> None:
    for event in events:
        json.dump(event, destination, ensure_ascii=False, separators=(",", ":"))
        destination.write("\n")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("Usage: reduce-transcript-fixture.py <scrubbed-transcript.jsonl>", file=sys.stderr)
        return 2
    transcript_path = Path(argv[0])
    if not transcript_path.is_file():
        print(f"reduce-transcript-fixture.py: transcript not found: {transcript_path}", file=sys.stderr)
        return 1
    try:
        write_jsonl(reduce_transcript(load_events(transcript_path)), sys.stdout)
        return 0
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"reduce-transcript-fixture.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
