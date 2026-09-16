#!/usr/bin/env python3
"""Scrub machine-specific and sensitive fields from stream-JSON transcripts."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, TextIO


FIELD_REPLACEMENTS = {
    "cwd": "<scrubbed>",
    "sessionId": "<scrubbed-session>",
    "session_id": "<scrubbed-session>",
    "gitBranch": "<scrubbed-branch>",
    "requestId": "<scrubbed>",
    "hook_id": "<scrubbed-hook>",
    "uuid": "<scrubbed-uuid>",
    "timestamp": "<scrubbed-timestamp>",
    "signature": "<scrubbed-signature>",
    "partial_json": "<scrubbed-partial-json>",
    "ttft_ms": "<scrubbed-duration>",
    "duration_ms": "<scrubbed-duration>",
    "duration_api_ms": "<scrubbed-duration>",
    "userType": "<scrubbed>",
    "origin": "<scrubbed>",
    "entrypoint": "<scrubbed>",
    "inference_geo": "<scrubbed>",
    "usage": "<scrubbed-usage>",
    "modelUsage": "<scrubbed>",
    "rate_limit_info": "<scrubbed>",
    "total_cost_usd": "<scrubbed>",
    "outputFile": "<scrubbed-path>",
    "output_file": "<scrubbed-path>",
    "agentId": "<scrubbed-agent>",
    "tools": "<scrubbed>",
    "mcp_servers": "<scrubbed>",
    "slash_commands": "<scrubbed>",
    "agents": "<scrubbed>",
    "skills": "<scrubbed>",
    "plugins": "<scrubbed>",
    "memory_paths": "<scrubbed>",
    "apiKeySource": "<scrubbed>",
    "analytics_disabled": "<scrubbed>",
}


STRING_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"), "<scrubbed-uuid>"),
    (re.compile(r'"session_id":"[^"]+"'), '"session_id":"<scrubbed-session>"'),
    (re.compile(r'"sessionId":"[^"]+"'), '"sessionId":"<scrubbed-session>"'),
    (re.compile(r'"requestId":"[^"]+"'), '"requestId":"<scrubbed>"'),
    (re.compile(r'"hook_id":"[^"]+"'), '"hook_id":"<scrubbed-hook>"'),
    (re.compile(r'"uuid":"[^"]+"'), '"uuid":"<scrubbed-uuid>"'),
    (re.compile(r'"signature":"[^"]*"'), '"signature":"<scrubbed-signature>"'),
    (re.compile(r'"partial_json":"[^"]*"'), '"partial_json":"<scrubbed-partial-json>"'),
    (re.compile(r'"timestamp":"[^"]+"'), '"timestamp":"<scrubbed-timestamp>"'),
    (re.compile(r'"agentId":"[^"]+"'), '"agentId":"<scrubbed-agent>"'),
    (re.compile(r'"outputFile":"[^"]+"'), '"outputFile":"<scrubbed-path>"'),
    (re.compile(r'"output_file":"[^"]+"'), '"output_file":"<scrubbed-path>"'),
    (re.compile(r'"total_cost_usd":[0-9.]+'), '"total_cost_usd":"<scrubbed>"'),
    (re.compile(r'"total_cost_usd":"[^"]+"'), '"total_cost_usd":"<scrubbed>"'),
    (re.compile(r'"usage":\{[^\n]*\}'), '"usage":"<scrubbed-usage>"'),
    (re.compile(r'"modelUsage":\{[^\n]*\}'), '"modelUsage":"<scrubbed>"'),
    (re.compile(r'"rate_limit_info":\{[^\n]*\}'), '"rate_limit_info":"<scrubbed>"'),
    (re.compile(r'"tools":\[[^\]]*\]'), '"tools":"<scrubbed>"'),
    (re.compile(r'"mcp_servers":\[[^\]]*\]'), '"mcp_servers":"<scrubbed>"'),
    (re.compile(r'"slash_commands":\[[^\]]*\]'), '"slash_commands":"<scrubbed>"'),
    (re.compile(r'"agents":\[[^\]]*\]'), '"agents":"<scrubbed>"'),
    (re.compile(r'"skills":\[[^\]]*\]'), '"skills":"<scrubbed>"'),
    (re.compile(r'"plugins":\[[^\]]*\]'), '"plugins":"<scrubbed>"'),
    (re.compile(r'"memory_paths":\{[^}]*\}'), '"memory_paths":"<scrubbed>"'),
    (re.compile(r'<TMP>-[^\s"]+'), "<TMP>"),
    (re.compile(r'/private/var/folders/[^\s"]+'), "<TMP>"),
    (re.compile(r'[A-Za-z]:\\Users\\[^\s"]+', re.IGNORECASE), "<HOME>"),
    (re.compile(r'/Users/[^/\s"]+'), "<HOME>"),
    (re.compile(r'/home/[^/\s"]+'), "<HOME>"),
    (re.compile(r'<HOME>/Documents/[^\s"]*/racecraft-plugins-public'), "<REPO>"),
    (re.compile(r'<HOME>/Documents/[^\s"]+'), "<PROJECTS>"),
    (re.compile(r'-Users-[^\s"]+'), "<HOME>"),
    (re.compile(r'[A-Za-z0-9]{2,}[-_ ]documents', re.IGNORECASE), "<PATH>"),
    (re.compile(r'agentId: [A-Za-z0-9_-]+'), "agentId: <scrubbed-agent>"),
    (re.compile(r'agent [0-9A-Fa-f]{16}'), "agent <scrubbed-agent>"),
    (re.compile(r'Command running in background with ID: [A-Za-z0-9_-]+'), "Command running in background with ID: <scrubbed-job>"),
    (re.compile(r'Use SendMessage with to: [^\s]+'), "Use SendMessage with to: <scrubbed-agent>"),
    (re.compile(r'msg_[A-Za-z0-9]+'), "msg_<scrubbed>"),
)


def scrub_string(value: str, extra_pattern: re.Pattern[str] | None) -> str:
    if "<system-reminder>" in value and re.search(r"transcript\.jsonl", value):
        return "<scrubbed-transcript-dump>"
    for pattern, replacement in STRING_REPLACEMENTS:
        value = pattern.sub(replacement, value)
    if extra_pattern is not None:
        value = extra_pattern.sub("<USER>", value)
    return value


def scrub_value(value: Any, extra_pattern: re.Pattern[str] | None) -> Any:
    if isinstance(value, dict):
        scrubbed = {key: scrub_value(item, extra_pattern) for key, item in value.items()}
        for key, replacement in FIELD_REPLACEMENTS.items():
            if key in scrubbed:
                scrubbed[key] = replacement
        return scrubbed
    if isinstance(value, list):
        return [scrub_value(item, extra_pattern) for item in value]
    if isinstance(value, str):
        return scrub_string(value, extra_pattern)
    return value


def scrub_event(event: Any, extra_pattern: re.Pattern[str] | None = None) -> Any:
    if isinstance(event, dict) and event.get("type") == "system":
        event = {"type": "system", "subtype": event.get("subtype", "")}
    elif isinstance(event, dict) and event.get("type") == "stream_event":
        nested = event.get("event")
        subtype = nested.get("type", "") if isinstance(nested, dict) else ""
        event = {"type": "stream_event", "subtype": subtype}
    return scrub_value(event, extra_pattern)


def scrub_stream(source: TextIO, destination: TextIO, extra_pattern: re.Pattern[str] | None = None) -> None:
    for line in source:
        if not line.strip():
            continue
        value = json.loads(line)
        json.dump(scrub_event(value, extra_pattern), destination, ensure_ascii=False, separators=(",", ":"))
        destination.write("\n")


def scrub_file(path: Path, extra_pattern: re.Pattern[str] | None = None) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"{path}: not a file")
    temporary_name = ""
    try:
        with path.open("r", encoding="utf-8") as source, tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as destination:
            temporary_name = destination.name
            scrub_stream(source, destination, extra_pattern)
        os.replace(temporary_name, path)
    except Exception:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
        raise


def main(argv: list[str]) -> int:
    extra_expression = os.environ.get("TRANSCRIPT_SCRUB_EXTRA_REGEX", "")
    try:
        extra_pattern = re.compile(extra_expression) if extra_expression else None
        if not argv:
            scrub_stream(sys.stdin, sys.stdout, extra_pattern)
            return 0
        for value in argv:
            path = Path(value)
            scrub_file(path, extra_pattern)
            print(f"scrubbed: {path}")
        return 0
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError, re.error) as exc:
        print(f"scrub-transcript.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
