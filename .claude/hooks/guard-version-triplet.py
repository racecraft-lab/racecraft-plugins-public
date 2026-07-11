#!/usr/bin/env python3
"""PreToolUse hook warning for version-load-bearing JSON edits."""

from __future__ import annotations

import json
import sys
from typing import Any


BLOCKED_SUFFIXES = (
    "/release-please-config.json",
    "/.release-please-manifest.json",
    "/.claude-plugin/marketplace.json",
)

WARNING = """Warning: Editing version-load-bearing file

This file is normally only written by release-please or the marketplace-sync workflow.
Manual edits cascade silently; see CLAUDE.md:
  - "Adding a New Plugin to Release Automation" (legitimate manual edit)
  - "Recovery & Rollback" Scenarios 1-6 (recovery from a bad state)

If this is intentional, ask the user to confirm before retrying the edit.
"""


def file_path_from_payload(text: str) -> str:
    try:
        payload: Any = json.loads(text)
    except json.JSONDecodeError:
        return ""
    if not isinstance(payload, dict):
        return ""
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    file_path = tool_input.get("file_path")
    return file_path if isinstance(file_path, str) else ""


def should_block(file_path: str) -> bool:
    normalized = file_path.replace("\\", "/")
    return any(normalized.endswith(suffix) for suffix in BLOCKED_SUFFIXES)


def main() -> int:
    file_path = file_path_from_payload(sys.stdin.read())
    if not file_path:
        return 0
    if should_block(file_path):
        print(WARNING, file=sys.stderr, end="")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
