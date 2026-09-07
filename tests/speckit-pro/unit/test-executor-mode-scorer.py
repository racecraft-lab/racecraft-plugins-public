#!/usr/bin/env python3
"""Lock the executor-mode paired scorer: classification, pairing, sign test, verdicts."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SHARED_LIB = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))
from test_result import run_counted  # noqa: E402

SCORER = REPO_ROOT / "tests" / "speckit-pro" / "layer3-functional" / "executor-modes" / "score-executor-modes.py"
CATALOG = SCORER.with_name("catalog.json")
FIXTURES = REPO_ROOT / "tests" / "speckit-pro" / "unit" / "fixtures" / "executor-modes"


def load_scorer():
    spec = importlib.util.spec_from_file_location("score_executor_modes", SCORER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ExecutorModeScorerTests(unittest.TestCase):
    def test_scorer(self) -> None:
        scorer = load_scorer()
        catalog = scorer.load_catalog(CATALOG)

        with self.subTest(msg="shipped catalog validates and covers both classes and a no-deltas plan"):
            classes = {c["id"]: scorer.is_boundary_task(c["files"], c["deltas"]) for c in catalog["cases"]}
            self.assertEqual({"queue-public-api": True, "queue-internal-compaction": False, "report-formatter": False}, classes)

        with self.subTest(msg="removed delta lines never make a boundary task"):
            self.assertFalse(scorer.is_boundary_task(["src/x.py"], ["- `src/x.py` — [removed: gone]"]))
        with self.subTest(msg="a file under a changed directory is a boundary task"):
            self.assertTrue(scorer.is_boundary_task(["src/api/v2/users.py"], ["- `src/api` — [new: public API package]"]))
        with self.subTest(msg="unrecognised delta line is an input error, not a silent inside task"):
            with self.assertRaises(scorer.InputError):
                scorer.is_boundary_task(["a"], ["* src/a.py changed"])

        with self.subTest(msg="exact sign test"):
            self.assertEqual(1.0, scorer.sign_test_p(1, 1))
            self.assertAlmostEqual(2 / 2**5, scorer.sign_test_p(5, 0))
            self.assertIsNone(scorer.sign_test_p(0, 0))

        results = scorer.load_results(FIXTURES / "results", {c["id"] for c in catalog["cases"]})
        report = scorer.score(catalog, results, alpha=0.05, mutation_tolerance=2.0, mutation_floor=None)
        with self.subTest(msg="median per (case, mode) pairs by task and drops null mutation pairs only"):
            ff = report["comparisons"]["function_first"]["metrics"]
            self.assertEqual(2, ff["mutation_score"]["pairs"])
            self.assertEqual(3, ff["wall_seconds"]["pairs"])
            self.assertEqual(600.0, ff["wall_seconds"]["rows"][0]["baseline"])
        with self.subTest(msg="function_first loses on mutation beyond tolerance"):
            self.assertEqual("loses", report["verdicts"]["function_first"])
        with self.subTest(msg="boundary is inconclusive at alpha 0.05 with three tasks"):
            self.assertEqual("inconclusive", report["verdicts"]["boundary"])
        with self.subTest(msg="boundary beats strict when alpha admits three wins"):
            loose = scorer.score(catalog, results, alpha=0.25, mutation_tolerance=2.0, mutation_floor=None)
            self.assertEqual("beats", loose["verdicts"]["boundary"])
        with self.subTest(msg="a case below the mutation floor makes the candidate lose"):
            floored = scorer.score(catalog, results, alpha=0.25, mutation_tolerance=2.0, mutation_floor=78.0)
            self.assertEqual("loses", floored["verdicts"]["boundary"])

        with self.subTest(msg="a missing mode result drops the task from the pair, never a loss"):
            partial = [r for r in results if not (r["case_id"] == "queue-public-api" and r["mode"] == "boundary")]
            rep = scorer.score(catalog, partial, alpha=0.05, mutation_tolerance=2.0, mutation_floor=None)
            self.assertEqual(2, rep["comparisons"]["boundary"]["metrics"]["wall_seconds"]["pairs"])

        env = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}
        with self.subTest(msg="CLI writes the report and exits 0 on a decision"):
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "report.json"
                proc = subprocess.run([sys.executable, str(SCORER), "--results", str(FIXTURES / "results"), "--report", str(out)],
                                      capture_output=True, text=True, env=env, check=False)
                self.assertEqual(0, proc.returncode, proc.stderr)
                self.assertIn("function_first vs strict: loses", proc.stdout)
                self.assertEqual("1.0", json.loads(out.read_text())["schema_version"])
        with self.subTest(msg="CLI exits 1 and names a malformed result document"):
            with tempfile.TemporaryDirectory() as tmp:
                (Path(tmp) / "bad.json").write_text(json.dumps({"case_id": "queue-public-api", "mode": "strict"}))
                proc = subprocess.run([sys.executable, str(SCORER), "--results", tmp], capture_output=True, text=True, env=env, check=False)
                self.assertEqual(1, proc.returncode)
                self.assertIn("bad.json: missing", proc.stderr)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ExecutorModeScorerTests)


def main() -> int:
    return run_counted(build_suite(), label="test-executor-mode-scorer")


if __name__ == "__main__":
    raise SystemExit(main())
