#!/usr/bin/env python3
"""Guard: eval expectations never carry the retired stop-and-skip vocabulary.

Autopilot defers an exhausted gate and keeps running. Four phrases described
the older behavior: a `default stop path` that escalates a failed gate, a
`skip-and-log override`, a fixed `STOP: Layer planner returned` line for an invalid
plan, and `STOP before Phase 7`. This scans every eval root, the catalog, its
fixtures, and its audit ledgers for them. Opt-in `--strict` no longer stops
either: its low-confidence findings go to plan review.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
TESTS = TEST_DIR.parent
REPO_ROOT = TESTS.parents[1]
sys.path.insert(0, str(TESTS / "lib"))

from test_result import run_counted  # noqa: E402

ROOTS = (
    "layer2-trigger", "layer3-functional", "layer6-integration", "layer7-parity",
    "evals/catalog.json", "evals/fixtures", "evals/audit", "evals/README.md",
)
SUFFIXES = {".json", ".md", ".txt", ".jsonl"}
ALWAYS_STALE = ("default stop path", "skip-and-log override", "STOP: Layer planner returned",
                "STOP before Phase 7")


def eval_files() -> list[Path]:
    files: list[Path] = []
    for root in ROOTS:
        base = TESTS / root
        found = [base] if base.is_file() else sorted(base.rglob("*")) if base.is_dir() else []
        files += [p for p in found if p.is_file() and p.suffix in SUFFIXES and "__pycache__" not in p.parts]
    return files


def stale_hits(relative: str, text: str) -> list[str]:
    """Return one message per stale phrase in `text`."""
    return [f"{relative}: {phrase!r}" for phrase in ALWAYS_STALE if phrase in text]


class StaleStopPhraseTests(unittest.TestCase):
    def test_scan_reaches_every_eval_root(self) -> None:
        names = {str(path.relative_to(TESTS)) for path in eval_files()}
        for expected in ("layer3-functional/evals/speckit-autopilot-evals.json",
                         "layer3-functional/codex-evals/speckit-autopilot-evals.json",
                         "evals/catalog.json"):
            self.assertIn(expected, names)
        for prefix in ("layer2-trigger/", "layer6-integration/", "layer7-parity/",
                       "evals/fixtures/", "evals/audit/"):
            self.assertTrue(any(name.startswith(prefix) for name in names), prefix)

    def test_no_eval_file_carries_a_retired_stop_phrase(self) -> None:
        hits: list[str] = []
        for path in eval_files():
            hits += stale_hits(str(path.relative_to(TESTS)), path.read_text(encoding="utf-8"))
        self.assertEqual(hits, [])

    def test_the_always_stale_phrases_are_detected_anywhere(self) -> None:
        relative = "layer3-functional/evals/speckit-autopilot-evals.json"
        for phrase in ALWAYS_STALE:
            hits = stale_hits(relative, f"x {phrase} y")
            self.assertEqual(len(hits), 1, hits)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(StaleStopPhraseTests)


def main() -> int:
    return run_counted(build_suite(), label="test-autopilot-stale-stop-phrases")


if __name__ == "__main__":
    raise SystemExit(main())
