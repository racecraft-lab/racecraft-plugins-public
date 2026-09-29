#!/usr/bin/env python3
"""Layer-4 contracts for the Python Layer-7 parity judge."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
JUDGE = TESTS_ROOT / "layer7-parity" / "lib" / "judge.py"
LIB_DIR = TESTS_ROOT / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


CURRENT_INVENTORY = [
    "deterministic judge module imports",
    "local comparison arms are exact tolerance-1",
    "exact values pass",
    "different exact values fail",
    "tolerance-1 difference of one passes",
    "tolerance-1 difference of two fails",
    "tolerance-1 rejects nonnumeric values",
    "semantic-equivalent returns skip",
    "semantic-equivalent result is marked skipped",
    "semantic-equivalent remains a supported skip-only tolerance",
    "byte-identical is not a judge arm",
    "judge source has no model or subprocess path",
]


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from script_loader import load_script  # noqa: E402


def import_judge():
    return load_script("l7_judge", JUDGE)


class Layer7JudgeTests(unittest.TestCase):
    def test_judge_contract(self) -> None:
        judge = import_judge()
        names = iter(CURRENT_INVENTORY)
        checks = [
            (next(names), lambda: self.assertIsNotNone(judge)),
            (next(names), lambda: self.assertEqual(judge.COMPARISON_ARMS, ("exact", "tolerance-1"))),
            (next(names), lambda: self.assertEqual(judge.judge_values("PASS\nPASS", "PASS\nPASS", "exact").status, "pass")),
            (next(names), lambda: self.assertEqual(judge.judge_values("PASS\nPASS", "FAIL\nPASS", "exact").status, "fail")),
            (next(names), lambda: self.assertEqual(judge.judge_values("1", "2", "tolerance-1").status, "pass")),
            (next(names), lambda: self.assertEqual(judge.judge_values("1", "3", "tolerance-1").status, "fail")),
            (next(names), lambda: self.assertEqual(judge.judge_values("1", "two", "tolerance-1").status, "fail")),
            (
                next(names),
                lambda: self.assertEqual(judge.judge_values("doctor clean", "doctor passes", "semantic-equivalent").status, "skip"),
            ),
            (
                next(names),
                lambda: self.assertTrue(judge.judge_values("doctor clean", "doctor passes", "semantic-equivalent").skipped),
            ),
            (
                next(names),
                lambda: self.assertEqual(judge.SUPPORTED_TOLERANCES, ("exact", "tolerance-1", "semantic-equivalent")),
            ),
            (next(names), lambda: self.assertRaises(ValueError, judge.judge_values, "a", "a", "byte-identical")),
            (
                next(names),
                lambda: [self.assertNotIn(word, JUDGE.read_text(encoding="utf-8").lower()) for word in ("claude", "subprocess")],
            ),
        ]
        for name, check in checks:
            with self.subTest(msg=name):
                check()


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Layer7JudgeTests)
    return run_counted(suite, label="test-parity-judge")


if __name__ == "__main__":
    raise SystemExit(main())
