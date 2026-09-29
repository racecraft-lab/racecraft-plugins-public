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
        with self.subTest(msg="catalog modes must be an object, not a list of names"):
            with tempfile.TemporaryDirectory() as tmp:
                bad = Path(tmp) / "catalog.json"
                bad.write_text(json.dumps({**catalog, "modes": list(scorer.MODES)}))
                with self.assertRaises(scorer.InputError):
                    scorer.load_catalog(bad)
        good = {"case_id": "queue-public-api", "mode": "strict", "seed": 1, "mutation_score": 74.0,
                "wall_seconds": 10.0, "review_findings": 2, "gate_iterations": 1}
        for label, patch in {
            "mutation_score above 100": {"mutation_score": 101},
            "negative wall_seconds": {"wall_seconds": -1},
            "fractional review_findings": {"review_findings": 1.5},
            "boolean gate_iterations": {"gate_iterations": True},
            "negative seed": {"seed": -1},
            "fractional seed": {"seed": 1.0},
        }.items():
            with self.subTest(msg=f"result domain rejected: {label}"):
                with tempfile.TemporaryDirectory() as tmp:
                    (Path(tmp) / "r.json").write_text(json.dumps({**good, **patch}))
                    with self.assertRaises(scorer.InputError):
                        scorer.load_results(Path(tmp), {"queue-public-api"})
        with self.subTest(msg="CLI exits 1 and names a malformed result document"):
            with tempfile.TemporaryDirectory() as tmp:
                (Path(tmp) / "bad.json").write_text(json.dumps({"case_id": "queue-public-api", "mode": "strict"}))
                proc = subprocess.run([sys.executable, str(SCORER), "--results", tmp], capture_output=True, text=True, env=env, check=False)
                self.assertEqual(1, proc.returncode)
                self.assertIn("bad.json: missing", proc.stderr)


class ScorerInputContractTests(unittest.TestCase):
    """The scorer promises exit 1 for malformed input and never scores a short run set silently."""

    GOOD = {"case_id": "queue-public-api", "mode": "strict", "seed": 1, "mutation_score": 74.0,
            "wall_seconds": 10.0, "review_findings": 2, "gate_iterations": 1}

    def setUp(self) -> None:
        self.scorer = load_scorer()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)

    def write_results(self, *documents) -> None:
        for index, document in enumerate(documents):
            (self.directory / f"r{index}.json").write_text(json.dumps(document))

    def run_cli(self):
        env = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}
        return subprocess.run([sys.executable, str(SCORER), "--results", str(self.directory)],
                              capture_output=True, text=True, env=env, check=False)

    def test_non_object_result_documents_are_input_errors(self) -> None:
        for label, value in {"list": [], "number": 3, "null": None, "string": "x"}.items():
            with self.subTest(document=label):
                self.write_results(value)
                with self.assertRaises(self.scorer.InputError):
                    self.scorer.load_results(self.directory, {"queue-public-api"})
                proc = self.run_cli()
                self.assertEqual(1, proc.returncode, proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)
                self.assertIn("r0.json", proc.stderr)

    def test_duplicate_case_mode_seed_is_an_input_error(self) -> None:
        self.write_results(self.GOOD, {**self.GOOD, "wall_seconds": 99.0})
        with self.assertRaisesRegex(self.scorer.InputError, "duplicate"):
            self.scorer.load_results(self.directory, {"queue-public-api"})
        self.assertEqual(1, self.run_cli().returncode)

    def test_non_object_catalogs_and_cases_are_input_errors(self) -> None:
        catalog = json.loads(CATALOG.read_text())
        for label, value in {"list catalog": [], "string case": {**catalog, "cases": ["x"]}}.items():
            with self.subTest(catalog=label):
                bad = self.directory / "catalog.json"
                bad.write_text(json.dumps(value))
                with self.assertRaises(self.scorer.InputError):
                    self.scorer.load_catalog(bad)

    def test_catalog_repeats_must_be_a_positive_integer(self) -> None:
        catalog = json.loads(CATALOG.read_text())
        for label, value in {"missing": None, "zero": 0, "float": 3.0, "bool": True}.items():
            with self.subTest(repeats=label):
                bad = self.directory / "catalog.json"
                broken = {key: item for key, item in catalog.items() if key != "repeats"}
                if value is not None:
                    broken["repeats"] = value
                bad.write_text(json.dumps(broken))
                with self.assertRaisesRegex(self.scorer.InputError, "repeats"):
                    self.scorer.load_catalog(bad)

    def test_short_run_sets_are_reported_not_scored_silently(self) -> None:
        catalog = self.scorer.load_catalog(CATALOG)
        results = self.scorer.load_results(FIXTURES / "results", {c["id"] for c in catalog["cases"]})
        complete = self.scorer.score(catalog, results, alpha=0.05, mutation_tolerance=2.0, mutation_floor=None)
        self.assertEqual([], complete["shortfalls"])
        short = [r for r in results if not (r["case_id"] == "queue-public-api" and r["mode"] == "boundary" and r["seed"] == 3)]
        report = self.scorer.score(catalog, short, alpha=0.05, mutation_tolerance=2.0, mutation_floor=None)
        self.assertEqual([{"case_id": "queue-public-api", "mode": "boundary", "expected": 3, "found": 2}],
                         report["shortfalls"])

    def test_cli_prints_each_shortfall(self) -> None:
        for seed in (1, 2):
            (self.directory / f"s{seed}.json").write_text(json.dumps({**self.GOOD, "seed": seed}))
        proc = self.run_cli()
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertIn("shortfall: queue-public-api strict has 2 of 3 seeds", proc.stdout)


def build_suite() -> unittest.TestSuite:
    return unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromTestCase(ExecutorModeScorerTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(ScorerInputContractTests),
    ])


def main() -> int:
    return run_counted(build_suite(), label="test-executor-mode-scorer")


if __name__ == "__main__":
    raise SystemExit(main())
