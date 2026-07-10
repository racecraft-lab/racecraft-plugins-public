#!/usr/bin/env python3
"""Score Layer-6 model output against a markdown baseline."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def score_text(actual: str, expected: str) -> dict[str, float]:
    """Return structural/content/overall quality scores in the shell-port shape."""
    expected_sections = re.findall(r"^##\s+(.+)$", expected, re.MULTILINE)
    actual_sections = re.findall(r"^##\s+(.+)$", actual, re.MULTILINE)

    if expected_sections:
        found = sum(
            1
            for expected_section in expected_sections
            if any(expected_section.lower() in actual_section.lower() for actual_section in actual_sections)
        )
        structural = found / len(expected_sections)
    else:
        structural = 1.0 if actual.strip() else 0.0

    expected_phrases = re.findall(r"^[\-\*]\s+\*?\*?(.+?)\*?\*?\s*$", expected, re.MULTILINE)
    if expected_phrases:
        matches = 0
        actual_lower = actual.lower()
        for phrase in expected_phrases:
            words = [word.lower() for word in re.findall(r"\w+", phrase) if len(word) > 3]
            if not words:
                continue
            found_words = sum(1 for word in words if word in actual_lower)
            if found_words / len(words) >= 0.5:
                matches += 1
        content = matches / len(expected_phrases)
    else:
        content = 1.0 if actual.strip() else 0.0

    overall = (structural + content) / 2
    return {
        "structural_score": round(structural, 2),
        "content_score": round(content, 2),
        "overall": round(overall, 2),
    }


def score_files(actual_path: Path, expected_path: Path) -> tuple[dict[str, float | str], int]:
    """Score two files, returning ``(payload, exit_code)``."""
    if not actual_path.is_file() or not expected_path.is_file():
        return {"structural_score": 0, "content_score": 0, "overall": 0, "error": "missing files"}, 1
    return score_text(
        actual_path.read_text(encoding="utf-8"),
        expected_path.read_text(encoding="utf-8"),
    ), 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: quality-scorer.py <actual_output_file> <expected_output_file>", file=sys.stderr)
        return 1
    payload, exit_code = score_files(Path(argv[0]), Path(argv[1]))
    print(json.dumps(payload))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
