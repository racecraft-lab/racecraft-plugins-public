#!/usr/bin/env python3
"""Contract tests for the shipped mutation-score floor script.

StrykerJS never fails a run on its default thresholds (`break: null`), so the
MUTATION slot chains this script after the run. Reports are written inline in
the mutation-testing-report-schema shape (`files.<path>.mutants[].status`).
"""

from __future__ import annotations

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

SCRIPT = REPO_ROOT / "speckit-pro" / "scripts" / "mutation-score.py"
ENV = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}


def report(*statuses: str) -> dict:
    return {
        "schemaVersion": "2",
        "thresholds": {"high": 80, "low": 60},
        "files": {
            "src/a.ts": {"language": "typescript", "source": "", "mutants": [
                {"id": str(i), "mutatorName": "x", "location": {}, "status": status}
                for i, status in enumerate(statuses)
            ]},
        },
    }


def run(cwd: Path, *args: str) -> tuple[int, dict, str]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, env=ENV, cwd=cwd, check=False,
    )
    summary = json.loads(result.stdout) if result.stdout.strip().startswith("{") else {}
    return result.returncode, summary, result.stderr


class MutationScoreTests(unittest.TestCase):
    def test_mutation_score_floor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "reports" / "mutation" / "mutation.json"
            path.parent.mkdir(parents=True)

            def write(data: object) -> None:
                path.write_text(json.dumps(data) if not isinstance(data, str) else data, encoding="utf-8")

            with self.subTest(msg="score counts killed and timeout over valid mutants"):
                # 3 detected of 5 valid = 60; ignored, pending, and error mutants are not valid.
                write(report("Killed", "Killed", "Timeout", "Survived", "NoCoverage",
                             "Ignored", "Pending", "CompileError", "RuntimeError"))
                code, summary, stderr = run(root, "--floor", "60")
                self.assertEqual(0, code, stderr)
                self.assertEqual(60.0, summary["score"])
                self.assertEqual({"detected": 3, "valid": 5}, {k: summary[k] for k in ("detected", "valid")})
                self.assertEqual("reports/mutation/mutation.json", summary["report"])
            with self.subTest(msg="below the floor fails with exit 1"):
                code, summary, stderr = run(root, "--floor", "60.5")
                self.assertEqual(1, code)
                self.assertIn("below the floor 60.5", stderr)
            with self.subTest(msg="an explicit report path is honored"):
                other = root / "custom.json"
                other.write_text(json.dumps(report("Killed")), encoding="utf-8")
                code, summary, _ = run(root, "--report", "custom.json", "--floor", "100")
                self.assertEqual((0, 100.0), (code, summary["score"]))
            with self.subTest(msg="a missing report fails closed, never a pass"):
                code, _, stderr = run(root, "--report", "absent.json", "--floor", "60")
                self.assertEqual(2, code)
                self.assertIn("absent.json", stderr)
            with self.subTest(msg="an unparseable report fails closed"):
                write("{not json")
                code, _, stderr = run(root, "--floor", "60")
                self.assertEqual(2, code)
                self.assertIn("cannot read", stderr)
            for label, data in {
                "no files object": {"schemaVersion": "2"},
                "mutants not a list": {"files": {"a.ts": {"mutants": {}}}},
                "unknown status": report("Killed", "Exploded"),
            }.items():
                with self.subTest(msg=f"malformed report fails closed: {label}"):
                    write(data)
                    code, _, _ = run(root, "--floor", "60")
                    self.assertEqual(2, code)
            with self.subTest(msg="zero valid mutants is not a pass"):
                write(report("Ignored", "CompileError"))
                code, _, stderr = run(root, "--floor", "0")
                self.assertEqual(2, code)
                self.assertIn("no valid mutants", stderr)
            with self.subTest(msg="a floor outside 0-100 is a usage error"):
                write(report("Killed"))
                code, _, _ = run(root, "--floor", "101")
                self.assertEqual(2, code)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(MutationScoreTests)


def main() -> int:
    return run_counted(build_suite(), label="test-mutation-score")


if __name__ == "__main__":
    raise SystemExit(main())
