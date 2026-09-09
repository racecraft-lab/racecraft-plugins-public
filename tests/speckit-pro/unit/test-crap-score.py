#!/usr/bin/env python3
"""Contract tests for the shipped CRAP-score gate script.

The join runs on pre-generated tool output so no external tool is needed.
Fixtures freeze the documented radon, coverage.py, ESLint, and Istanbul
JSON shapes; a change in what the script accepts must change them too.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SHARED_LIB = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))

from test_result import run_counted  # noqa: E402

SCRIPT = REPO_ROOT / "speckit-pro" / "scripts" / "crap-score.py"
FIXTURES = Path("tests/speckit-pro/unit/fixtures/crap-score")
ENV = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}


def run(*args: str) -> tuple[int, dict, str]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, env=ENV, cwd=REPO_ROOT, check=False,
    )
    report = json.loads(result.stdout) if result.stdout.strip().startswith("{") else {}
    return result.returncode, report, result.stderr


class CrapScoreTests(unittest.TestCase):
    def test_crap_score_gate(self) -> None:
        py = ("--language", "python", "--radon-json", f"{FIXTURES}/radon.json",
              "--coverage-json", f"{FIXTURES}/coverage-py.json")
        ts = ("--language", "typescript", "--eslint-json", f"{FIXTURES}/eslint.json",
              "--coverage-json", f"{FIXTURES}/coverage-istanbul.json")
        tight = ("--ceiling", "30", "--complexity-ceiling", "8")

        with self.subTest(msg="empty path list checks nothing and passes"):
            code, report, _ = run("--language", "python", *tight, "--")
            self.assertEqual((0, 0, []), (code, report["checked"], report["violations"]))

        with self.subTest(msg="python: methods are flattened out of classes and CRAP uses line coverage"):
            code, report, stderr = run(*py, *tight, "--", f"{FIXTURES}/sample.py")
            by_name = {f["name"]: f for f in report["functions"]}
            self.assertEqual({"simple", "method", "tangled"}, set(by_name))
            self.assertEqual((1, 1.0, 1.0), (by_name["simple"]["complexity"], by_name["simple"]["coverage"], by_name["simple"]["crap"]))
            self.assertEqual(9, by_name["tangled"]["complexity"])
            self.assertEqual(1, code)
            self.assertIn("tangled", stderr)
            self.assertEqual(["tangled"], [v["name"] for v in report["violations"]])

        with self.subTest(msg="python: lenient ceilings pass the same input"):
            code, report, _ = run(*py, "--ceiling", "500", "--complexity-ceiling", "20", "--", f"{FIXTURES}/sample.py")
            self.assertEqual((0, 3), (code, report["checked"]))

        with self.subTest(msg="typescript: only complexity messages count and coverage joins on fnMap spans"):
            code, report, _ = run(*ts, *tight, "--", f"{FIXTURES}/sample.ts")
            by_name = {f["name"]: f for f in report["functions"]}
            self.assertEqual({"Function 'simple'", "Function 'tangled'"}, set(by_name))
            self.assertEqual(1.0, by_name["Function 'simple'"]["coverage"])
            self.assertAlmostEqual(2 / 7, by_name["Function 'tangled'"]["coverage"], places=3)
            self.assertEqual(1, code)

        with self.subTest(msg="typescript: unrecognised complexity wording is a parse failure, not a pass"):
            bad = FIXTURES / "eslint-bad-message.json"
            code, _, stderr = run("--language", "typescript", "--eslint-json", str(bad),
                                  "--coverage-json", f"{FIXTURES}/coverage-istanbul.json", *tight, "--", f"{FIXTURES}/sample.ts")
            self.assertEqual(2, code)
            self.assertIn("unrecognised", stderr)

        with self.subTest(msg="missing tool exits 2 and names it"):
            code, _, stderr = run("--language", "python", *tight, "--", f"{FIXTURES}/sample.py")
            self.assertEqual(2, code)
            self.assertIn("radon", stderr)

        with self.subTest(msg="report file is written when asked"):
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "report.json"
                run(*py, *tight, "--report", str(out), "--", f"{FIXTURES}/sample.py")
                self.assertEqual(3, json.loads(out.read_text(encoding="utf-8"))["checked"])


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(CrapScoreTests)


def main() -> int:
    return run_counted(build_suite(), label="test-crap-score")


if __name__ == "__main__":
    raise SystemExit(main())
