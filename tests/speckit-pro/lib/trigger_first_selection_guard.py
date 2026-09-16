#!/usr/bin/env python3
"""Stop a Claude Layer 2 run after its first successful Skill call."""
from __future__ import annotations

import json
import sys


RECEIPT_PREFIX = "L2_FIRST_SELECTION_GUARD/v1"
HOOK_EVENT = "PostToolUse"
HOOK_NAME = "PostToolUse:Skill"


def guard_response(raw: bytes) -> dict[str, object]:
    """Return a fail-closed stop response and attribute valid Skill input."""
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        value = None
    tool_use_id = value.get("tool_use_id") if isinstance(value, dict) else None
    tool_input = value.get("tool_input") if isinstance(value, dict) else None
    skill = tool_input.get("skill") if isinstance(tool_input, dict) else None
    valid = (
        isinstance(value, dict)
        and value.get("hook_event_name") == HOOK_EVENT
        and value.get("tool_name") == "Skill"
        and isinstance(tool_use_id, str)
        and bool(tool_use_id)
        and not any(character.isspace() for character in tool_use_id)
        and isinstance(skill, str)
        and bool(skill)
        and "tool_response" in value
    )
    receipt = (
        f"{RECEIPT_PREFIX}:{tool_use_id}"
        if valid
        else f"{RECEIPT_PREFIX}:invalid-input"
    )
    return {"continue": False, "stopReason": receipt}


def main() -> int:
    response = guard_response(sys.stdin.buffer.read())
    sys.stdout.write(json.dumps(response, ensure_ascii=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
