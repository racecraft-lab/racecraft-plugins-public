#!/usr/bin/env python3
"""Behavior tests for the advisory ubiquitous-language lint.

The lint runs on frozen terms and diff fixtures so no git history is needed;
one case drives the real git path against a scratch repository.
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

SCRIPT = REPO_ROOT / "speckit-pro" / "scripts" / "ubiquitous-language-lint.py"
FIXTURES = REPO_ROOT / "tests" / "speckit-pro" / "unit" / "fixtures" / "ubiquitous-language"
ENV = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": "/nonexistent",
       "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "support@openai.com",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "support@openai.com",
       "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}


def run(*args: str, cwd: Path = REPO_ROOT) -> tuple[int, dict]:
    result = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=ENV, cwd=cwd, check=False)
    return result.returncode, json.loads(result.stdout)


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, env=ENV, check=True)


class UbiquitousLanguageLintTests(unittest.TestCase):
    def test_lint_is_advisory_and_maps_terms(self) -> None:
        code, report = run("--terms", str(FIXTURES / "terms.md"), "--diff", str(FIXTURES / "sample.diff"))
        with self.subTest(msg="always exits 0 and declares itself advisory"):
            self.assertEqual(0, code)
            self.assertIs(True, report["advisory"])
        with self.subTest(msg="parses every table row including one with no identifiers"):
            self.assertEqual(3, report["terms"])
        with self.subTest(msg="declarations come from added source lines only, not Markdown"):
            self.assertEqual(6, report["declared"])
        with self.subTest(msg="identifiers map by the Identifiers column or by a shared term word"):
            self.assertEqual(["rebuild_cache", "scheduleReminder"], [u["identifier"] for u in report["unmapped"]])
        with self.subTest(msg="unmapped entries carry file and line from the hunk header"):
            self.assertEqual({"file": "src/billing.py", "line": 6, "identifier": "rebuild_cache"}, report["unmapped"][0])
            self.assertEqual({"file": "src/api.ts", "line": 6, "identifier": "scheduleReminder"}, report["unmapped"][1])
        with self.subTest(msg="note summarises the count"):
            self.assertEqual("2 of 6 declared identifiers map to no term", report["note"])
        with self.subTest(msg="missing terms document lints nothing and still exits 0"):
            code, report = run("--terms", str(FIXTURES / "absent.md"), "--diff", str(FIXTURES / "sample.diff"))
            self.assertEqual((0, "no terms document; nothing linted", 0), (code, report["note"], report["declared"]))
        with self.subTest(msg="report file is written when asked"):
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "r.json"
                run("--terms", str(FIXTURES / "terms.md"), "--diff", str(FIXTURES / "sample.diff"), "--report", str(out))
                self.assertEqual(2, len(json.loads(out.read_text(encoding="utf-8"))["unmapped"]))
        with self.subTest(msg="git path: diff against a base ref in a scratch repository"):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                git(root, "init", "-q", "-b", "main")
                (root / "a.py").write_text("x = 1\n", encoding="utf-8")
                git(root, "add", "a.py"); git(root, "commit", "-q", "-m", "base")
                git(root, "checkout", "-q", "-b", "feature")
                (root / "a.py").write_text("x = 1\nclass InvoiceLedger:\n    pass\ndef reindex_all():\n    pass\n", encoding="utf-8")
                git(root, "add", "a.py"); git(root, "commit", "-q", "-m", "feature")
                code, report = run("--terms", str(FIXTURES / "terms.md"), "--base", "main", cwd=root)
                self.assertEqual((0, 2), (code, report["declared"]))
                self.assertEqual(["reindex_all"], [u["identifier"] for u in report["unmapped"]])
        with self.subTest(msg="an unavailable diff is reported, not raised"):
            with tempfile.TemporaryDirectory() as tmp:
                code, report = run("--terms", str(FIXTURES / "terms.md"), "--base", "nonexistent-ref", cwd=Path(tmp))
                self.assertEqual(0, code)
                self.assertTrue(report["note"].startswith("diff unavailable"))


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(UbiquitousLanguageLintTests)


def main() -> int:
    return run_counted(build_suite(), label="test-ubiquitous-language-lint")


if __name__ == "__main__":
    raise SystemExit(main())
