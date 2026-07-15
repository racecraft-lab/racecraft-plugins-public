"""Shared prompt-preview helpers for Layer 3 functional eval runners."""

from __future__ import annotations

import json
from pathlib import Path


def eval_count(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(len(data.get("evals", [])))
    except Exception:
        return "?"


def print_eval_prompts(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    for item in data.get("evals", []):
        print(f"  [{item['id']}] {item['prompt'][:100]}...")
        for expectation in item.get("expectations", []):
            print(f"      - {expectation[:80]}")
        print()
