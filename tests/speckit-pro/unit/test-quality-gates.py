#!/usr/bin/env python3
"""Contract tests for the quality-gates thresholds file, its validator, and the recommender.

The schema file must agree with the validator's enums, every rule must reject
a minimal negative case, and the recommended complexity ceiling must let
about 90 percent of measured functions pass, or fall back to Bob's six.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
SHARED_LIB = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for _root in (SHARED_LIB, PLUGIN_ROOT):
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from speckit_pro_runner import quality_gates  # noqa: E402
from test_result import run_counted  # noqa: E402

SCHEMA_PATH = PLUGIN_ROOT / "speckit_pro_runner" / "contracts" / "quality-gates.schema.json"


def valid() -> dict:
    return {
        "schema_version": "1.0",
        "thresholds": {"complexity": 8, "crap": 30, "mutation_score_floor": 60},
        "skips": {"MUTATION": {"reason": "no mutation harness yet", "recorded": "2026-09-06"}},
        "basis": {"method": "percentile-90", "measured_functions": 120},
    }


def mutated(path: str, value: object) -> dict:
    data = valid()
    parts = path.split(".")
    target = data
    for part in parts[:-1]:
        target = target[part]
    if value is None:
        target.pop(parts[-1], None)
    else:
        target[parts[-1]] = value
    return data


class QualityGatesTests(unittest.TestCase):
    def test_quality_gates_contract(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        with self.subTest(msg="schema agrees with the validator"):
            self.assertEqual(quality_gates.SCHEMA_VERSION, schema["properties"]["schema_version"]["const"])
            self.assertEqual(list(quality_gates.THRESHOLD_FIELDS), schema["properties"]["thresholds"]["required"])
            self.assertEqual(list(quality_gates.SLOTS), schema["properties"]["skips"]["propertyNames"]["enum"])
            self.assertEqual(list(quality_gates.BASIS_METHODS), schema["properties"]["basis"]["properties"]["method"]["enum"])
            self.assertIn(quality_gates.FILE_PATH, schema["description"])
        with self.subTest(msg="valid file passes"):
            self.assertEqual([], quality_gates.validate(valid()))
        with self.subTest(msg="thresholds alone are enough"):
            self.assertEqual([], quality_gates.validate({"schema_version": "1.0", "thresholds": valid()["thresholds"]}))

        negatives = {
            "top level not an object": [],
            "wrong schema_version": mutated("schema_version", "2.0"),
            "unknown top-level key": {**valid(), "extra": 1},
            "thresholds missing": mutated("thresholds", None),
            "thresholds missing field": mutated("thresholds.crap", None),
            "thresholds unknown field": mutated("thresholds.halstead", 1),
            "complexity zero": mutated("thresholds.complexity", 0),
            "complexity bool": mutated("thresholds.complexity", True),
            "complexity float": mutated("thresholds.complexity", 8.5),
            "crap zero": mutated("thresholds.crap", 0),
            "floor above 100": mutated("thresholds.mutation_score_floor", 101),
            "floor string": mutated("thresholds.mutation_score_floor", "60"),
            "skips not an object": mutated("skips", []),
            "skips unknown slot": mutated("skips", {"FORMAL_CHECK": {"reason": "x"}}),
            "skip without reason": mutated("skips", {"MUTATION": {}}),
            "skip unknown field": mutated("skips", {"MUTATION": {"reason": "x", "until": "2027"}}),
            "basis unknown method": mutated("basis.method", "guess"),
            "basis negative count": mutated("basis.measured_functions", -1),
        }
        for label, data in negatives.items():
            with self.subTest(msg=f"rejects: {label}"):
                self.assertTrue(quality_gates.validate(data), label)

        with self.subTest(msg="substitutions map onto the discovery placeholders"):
            self.assertEqual(
                {"ceiling": "30", "complexity_ceiling": "8", "floor": "60", "survival_ceiling": "40"},
                quality_gates.substitutions(valid()["thresholds"]),
            )
            self.assertEqual("37.5", quality_gates.substitutions({"complexity": 8, "crap": 30, "mutation_score_floor": 62.5})["survival_ceiling"])

        with self.subTest(msg="recommend: ceiling lets about 90 percent of measured functions pass"):
            report = {"functions": [{"complexity": c} for c in [1, 1, 2, 2, 3, 3, 4, 5, 9, 15]]}
            out = quality_gates.recommend(report)
            self.assertEqual(9, out["thresholds"]["complexity"])
            self.assertEqual({"method": "percentile-90", "measured_functions": 10}, out["basis"])
            self.assertEqual([], quality_gates.validate(out))
        with self.subTest(msg="recommend: nothing measured falls back to Bob's six"):
            out = quality_gates.recommend({"functions": []})
            self.assertEqual(quality_gates.BOBS_SIX, out["thresholds"]["complexity"])
            self.assertEqual("bobs-six", out["basis"]["method"])
            self.assertEqual([], quality_gates.validate(out))
        with self.subTest(msg="recommend: single function passes at its own complexity"):
            self.assertEqual(4, quality_gates.recommend({"functions": [{"complexity": 4}]})["thresholds"]["complexity"])

        env = {"PYTHONPATH": str(PLUGIN_ROOT), "PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good.json"
            good.write_text(json.dumps(valid()), encoding="utf-8")
            bad = Path(tmp) / "bad.json"
            bad.write_text(json.dumps(mutated("thresholds.complexity", 0)), encoding="utf-8")
            report = Path(tmp) / "report.json"
            report.write_text(json.dumps({"functions": []}), encoding="utf-8")
            with self.subTest(msg="CLI validate exits 0 on a valid file"):
                result = subprocess.run([sys.executable, "-m", "speckit_pro_runner.quality_gates", "validate", str(good)],
                                        capture_output=True, text=True, env=env, cwd=REPO_ROOT, check=False)
                self.assertEqual(0, result.returncode, result.stderr)
            with self.subTest(msg="CLI validate exits 1 and names the violation"):
                result = subprocess.run([sys.executable, "-m", "speckit_pro_runner.quality_gates", "validate", str(bad)],
                                        capture_output=True, text=True, env=env, cwd=REPO_ROOT, check=False)
                self.assertEqual(1, result.returncode)
                self.assertIn("thresholds.complexity", result.stderr)
            with self.subTest(msg="CLI validate exits 1 when the file is absent"):
                result = subprocess.run([sys.executable, "-m", "speckit_pro_runner.quality_gates", "validate", str(Path(tmp) / "none.json")],
                                        capture_output=True, text=True, env=env, cwd=REPO_ROOT, check=False)
                self.assertEqual(1, result.returncode)
            with self.subTest(msg="CLI recommend prints a valid file body"):
                result = subprocess.run([sys.executable, "-m", "speckit_pro_runner.quality_gates", "recommend", str(report)],
                                        capture_output=True, text=True, env=env, cwd=REPO_ROOT, check=False)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual([], quality_gates.validate(json.loads(result.stdout)))
            with self.subTest(msg="CLI usage error exits 2"):
                result = subprocess.run([sys.executable, "-m", "speckit_pro_runner.quality_gates", "bogus"],
                                        capture_output=True, text=True, env=env, cwd=REPO_ROOT, check=False)
                self.assertEqual(2, result.returncode)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(QualityGatesTests)


def main() -> int:
    return run_counted(build_suite(), label="test-quality-gates")


if __name__ == "__main__":
    raise SystemExit(main())
