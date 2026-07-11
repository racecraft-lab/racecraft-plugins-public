#!/usr/bin/env python3
"""Layer-4 contracts for the Python Layer-8 parity judge.

Port target for ``test-l8-judge.sh`` (XPLAT-010 T074). The retired LLM-shim
inventory and truthful deterministic replacement inventory are both pinned at
``TOTAL: 16``. Their intentional name divergence records T074's boundary guard.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
JUDGE = TESTS_ROOT / "layer8-parity" / "lib" / "judge.py"
BASELINE = TESTS_ROOT / "parity" / "xplat-010" / "test-l8-judge-baseline.txt"
BASH_BASELINE = TESTS_ROOT / "parity" / "xplat-010" / "test-l8-judge-bash-baseline.txt"
LIB_DIR = TESTS_ROOT / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


CURRENT_INVENTORY = [
    "current and retired judge inventories are explicit",
    "deterministic judge module imports",
    "local comparison arms are byte-identical exact tolerance-1",
    "byte-identical files pass",
    "byte-identical passing result is matched",
    "byte-identical files with different bytes fail",
    "exact values pass",
    "different exact values fail",
    "tolerance-1 difference of one passes",
    "tolerance-1 difference of two fails",
    "tolerance-1 rejects nonnumeric values",
    "semantic-equivalent returns skip",
    "semantic-equivalent result is marked skipped",
    "semantic-equivalent remains a supported skip-only tolerance",
    "semantic-equivalent CLI exits zero with warning",
    "CLI emits pass fail skip JSON without an LLM subprocess path",
]


def import_judge():
    spec = importlib.util.spec_from_file_location("l8_judge", JUDGE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(JUDGE), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=env,
        shell=False,
        check=False,
    )


def baseline_inventory(path: Path) -> list[str]:
    names: list[str] = []
    total: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("TOTAL: "):
            total = int(line.removeprefix("TOTAL: "))
            continue
        _ordinal, name = line.split(" ", 1)
        names.append(name)
    if total != len(names):
        raise AssertionError(f"baseline TOTAL {total} does not match {len(names)} names")
    return names


class Layer8JudgeTests(unittest.TestCase):
    def test_judge_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            same_a = root / "same-a.txt"
            same_b = root / "same-b.txt"
            drift_b = root / "drift-b.txt"
            same_a.write_bytes(b"alpha\n")
            same_b.write_bytes(b"alpha\n")
            drift_b.write_bytes(b"alpha\r\n")

            one = root / "one.txt"
            two = root / "two.txt"
            three = root / "three.txt"
            word = root / "word.txt"
            one.write_text("1\n", encoding="utf-8")
            two.write_text("2\n", encoding="utf-8")
            three.write_text("3\n", encoding="utf-8")
            word.write_text("two\n", encoding="utf-8")
            judge = import_judge()

            checks = [
                (CURRENT_INVENTORY[0], lambda: self._assert_inventory_contract()),
                (CURRENT_INVENTORY[1], lambda: self.assertIsNotNone(judge)),
                (
                    CURRENT_INVENTORY[2],
                    lambda: self.assertEqual(
                        judge.COMPARISON_ARMS,
                        ("byte-identical", "exact", "tolerance-1"),
                    ),
                ),
                (
                    CURRENT_INVENTORY[3],
                    lambda: self.assertEqual(judge.judge_files(same_a, same_b, "byte-identical").status, "pass"),
                ),
                (
                    CURRENT_INVENTORY[4],
                    lambda: self.assertTrue(judge.judge_files(same_a, same_b, "byte-identical").matched),
                ),
                (
                    CURRENT_INVENTORY[5],
                    lambda: self.assertEqual(judge.judge_files(same_a, drift_b, "byte-identical").status, "fail"),
                ),
                (
                    CURRENT_INVENTORY[6],
                    lambda: self.assertEqual(judge.judge_values("PASS\nPASS", "PASS\nPASS", "exact").status, "pass"),
                ),
                (
                    CURRENT_INVENTORY[7],
                    lambda: self.assertEqual(judge.judge_values("PASS\nPASS", "FAIL\nPASS", "exact").status, "fail"),
                ),
                (
                    CURRENT_INVENTORY[8],
                    lambda: self.assertEqual(judge.judge_files(one, two, "tolerance-1").status, "pass"),
                ),
                (
                    CURRENT_INVENTORY[9],
                    lambda: self.assertEqual(judge.judge_files(one, three, "tolerance-1").status, "fail"),
                ),
                (
                    CURRENT_INVENTORY[10],
                    lambda: self.assertEqual(judge.judge_files(one, word, "tolerance-1").status, "fail"),
                ),
                (
                    CURRENT_INVENTORY[11],
                    lambda: self.assertEqual(judge.judge_values("doctor clean", "doctor passes", "semantic-equivalent").status, "skip"),
                ),
                (
                    CURRENT_INVENTORY[12],
                    lambda: self.assertTrue(judge.judge_values("doctor clean", "doctor passes", "semantic-equivalent").skipped),
                ),
                (
                    CURRENT_INVENTORY[13],
                    lambda: self.assertEqual(judge.SUPPORTED_TOLERANCES, ("byte-identical", "exact", "tolerance-1", "semantic-equivalent")),
                ),
                (
                    CURRENT_INVENTORY[14],
                    lambda: self.assertEqual(run_cli("semantic-equivalent", str(same_a), str(three)).returncode, 0),
                ),
                (CURRENT_INVENTORY[15], lambda: self._assert_cli_contract(same_a, same_b, three)),
            ]

            self.assertEqual([name for name, _check in checks], CURRENT_INVENTORY)
            for name, check in checks:
                with self.subTest(msg=name):
                    check()

    def _assert_inventory_contract(self) -> None:
        current = baseline_inventory(BASELINE)
        retired = baseline_inventory(BASH_BASELINE)
        self.assertEqual(current, CURRENT_INVENTORY)
        self.assertEqual(len(retired), len(current))
        self.assertNotEqual(retired, current)

    def _assert_cli_contract(self, same_a: Path, same_b: Path, three: Path) -> None:
        passing = run_cli("exact", str(same_a), str(same_b))
        self.assertEqual(passing.returncode, 0, passing.stderr)
        self.assertEqual(json.loads(passing.stdout)["status"], "pass")

        failing = run_cli("tolerance-1", str(same_a), str(three))
        self.assertEqual(failing.returncode, 1, failing.stdout + failing.stderr)
        self.assertEqual(json.loads(failing.stdout)["status"], "fail")

        skipped = run_cli("semantic-equivalent", str(same_a), str(three))
        self.assertEqual(skipped.returncode, 0, skipped.stderr)
        self.assertEqual(json.loads(skipped.stdout)["status"], "skip")
        self.assertIn("WARNING", skipped.stderr)

        source = JUDGE.read_text(encoding="utf-8")
        self.assertNotIn("claude", source.lower())
        self.assertNotIn("--json-schema", source)
        self.assertNotIn("subprocess", source)
        self.assertNotIn("shell=True", source)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Layer8JudgeTests)
    return run_counted(suite, label="test-l8-judge")


if __name__ == "__main__":
    raise SystemExit(main())
