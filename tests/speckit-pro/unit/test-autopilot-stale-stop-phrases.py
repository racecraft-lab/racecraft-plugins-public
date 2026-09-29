#!/usr/bin/env python3
"""Guard: eval expectations never carry the retired stop-and-skip vocabulary.

Autopilot defers an exhausted gate and keeps running. Four phrases described
the older behavior: a `default stop path` that escalates a failed gate, a
`skip-and-log override`, a fixed `STOP: Layer planner returned` line for an invalid
plan, and an unconditional `STOP before Phase 7`. This scans
every eval root, the catalog, its fixtures, and its audit ledgers for them. The
only allowed hit is `STOP before Phase 7` inside a strict-mode case, because
the opt-in `--strict` confidence mode still stops before Phase 7.
"""

from __future__ import annotations

import json
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
ALWAYS_STALE = ("default stop path", "skip-and-log override", "STOP: Layer planner returned")
STRICT_ONLY = "STOP before Phase 7"
# The strict-mode confidence case in each eval file, by entry id.
STRICT_CASES = {
    "layer3-functional/evals/speckit-autopilot-evals.json": {20},
    "layer3-functional/codex-evals/speckit-autopilot-evals.json": {24},
    "evals/catalog.json": {"functional.speckit-autopilot.case-24"},
}


def eval_files() -> list[Path]:
    files: list[Path] = []
    for root in ROOTS:
        base = TESTS / root
        found = [base] if base.is_file() else sorted(base.rglob("*")) if base.is_dir() else []
        files += [p for p in found if p.is_file() and p.suffix in SUFFIXES and "__pycache__" not in p.parts]
    return files


def stale_hits(relative: str, text: str) -> list[str]:
    """Return one message per stale phrase in `text`, honoring the strict-mode cases."""
    hits = [f"{relative}: {phrase!r}" for phrase in ALWAYS_STALE if phrase in text]
    if STRICT_ONLY not in text:
        return hits
    allowed = STRICT_CASES.get(relative)
    if allowed is None:
        return hits + [f"{relative}: {STRICT_ONLY!r}"]
    entries = json.loads(text)
    for entry in entries.get("evals", entries.get("cases", [])):
        if STRICT_ONLY in json.dumps(entry) and entry["id"] not in allowed:
            hits.append(f"{relative}: {STRICT_ONLY!r} in entry {entry['id']!r}")
    return hits


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

    def test_strict_mode_cases_are_the_only_exemption(self) -> None:
        relative = "layer3-functional/evals/speckit-autopilot-evals.json"
        strict = json.dumps({"evals": [{"id": 20, "expectations": [STRICT_ONLY]}]})
        other = json.dumps({"evals": [{"id": 21, "expectations": [STRICT_ONLY]}]})
        self.assertEqual(stale_hits(relative, strict), [])
        self.assertEqual(len(stale_hits(relative, other)), 1)
        self.assertEqual(len(stale_hits("layer6-integration/README.md", STRICT_ONLY)), 1)

    def test_the_always_stale_phrases_are_detected_anywhere(self) -> None:
        for phrase in ALWAYS_STALE:
            with self.subTest(phrase=phrase):
                self.assertEqual(len(stale_hits(next(iter(STRICT_CASES)), f"x {phrase} y")), 1)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(StaleStopPhraseTests)


def main() -> int:
    return run_counted(build_suite(), label="test-autopilot-stale-stop-phrases")


if __name__ == "__main__":
    raise SystemExit(main())
