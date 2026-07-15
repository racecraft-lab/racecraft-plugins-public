"""Shared prompt-preview helpers for Layer 3 functional eval runners."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def read_eval_data(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def eval_count(path: Path) -> str:
    try:
        data = read_eval_data(path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "?"
    if not isinstance(data, dict):
        return "?"
    evals = data.get("evals", [])
    if not isinstance(evals, list):
        return "?"
    return str(len(evals))


def print_eval_prompts(path: Path) -> None:
    try:
        data = read_eval_data(path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        print(f"ERROR: Unable to read eval file {path}: {error}", file=sys.stderr)
        return
    if not isinstance(data, dict) or not isinstance(data.get("evals", []), list):
        print(f"ERROR: Eval file has invalid shape: {path}", file=sys.stderr)
        return

    for index, item in enumerate(data.get("evals", []), start=1):
        if not isinstance(item, dict):
            print(f"ERROR: Skipping eval entry {index}: expected object", file=sys.stderr)
            continue
        eval_id = item.get("id")
        prompt = item.get("prompt")
        expectations = item.get("expectations", [])
        if not isinstance(eval_id, (int, str)) or not isinstance(prompt, str) or not isinstance(expectations, list):
            print(f"ERROR: Skipping eval entry {index}: invalid id, prompt, or expectations", file=sys.stderr)
            continue

        print(f"  [{eval_id}] {prompt[:100]}...")
        for expectation in expectations:
            if not isinstance(expectation, str):
                print(f"ERROR: Skipping eval entry {index} expectation: expected string", file=sys.stderr)
                continue
            print(f"      - {expectation[:80]}")
        print()
