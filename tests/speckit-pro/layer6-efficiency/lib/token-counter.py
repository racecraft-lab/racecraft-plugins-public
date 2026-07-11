#!/usr/bin/env python3
"""Parse Claude JSON token usage for Layer-6 efficiency benchmarks."""

from __future__ import annotations

import json
import sys
from typing import Any


ZERO_TOKEN_FALLBACK = {
    "input_tokens": 0,
    "output_tokens": 0,
    "cache_read": 0,
    "cache_write": 0,
}


def count_tokens(payload: dict[str, Any]) -> dict[str, int]:
    """Return the Layer-6 token summary for a Claude JSON response."""
    usage = payload.get("usage", {})
    if not usage and isinstance(payload.get("result"), dict):
        usage = payload["result"].get("usage", {})
    if not isinstance(usage, dict):
        usage = {}

    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    cache_read = int(usage.get("cache_read_input_tokens", 0) or 0)
    cache_write = int(usage.get("cache_creation_input_tokens", 0) or 0)
    total_input = input_tokens + cache_read + cache_write
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read": cache_read,
        "cache_write": cache_write,
        "total_input": total_input,
        "total_tokens": total_input + output_tokens,
    }


def parse_token_text(text: str) -> tuple[dict[str, int], bool]:
    """Parse JSON text and return ``(summary, parsed_ok)``."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return dict(ZERO_TOKEN_FALLBACK), False
    if not isinstance(payload, dict):
        return dict(ZERO_TOKEN_FALLBACK), False
    return count_tokens(payload), True


def main() -> int:
    summary, parsed = parse_token_text(sys.stdin.read())
    print(json.dumps(summary))
    if not parsed:
        print("WARNING: Could not parse token usage from claude output", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
