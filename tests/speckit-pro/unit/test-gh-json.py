#!/usr/bin/env python3
"""Tests for the shared gh JSON runner used by repository scripts."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from script_loader import load_script  # noqa: E402
from test_result import run_counted  # noqa: E402

gh_json = load_script("gh_json", REPO_ROOT / "scripts" / "gh_json.py")


class CallerError(RuntimeError):
    """Stands in for a calling script's own error type."""


def completed(returncode: int, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["gh"], returncode, stdout, stderr)


class RunGhJsonTests(unittest.TestCase):
    def run_with(self, result: subprocess.CompletedProcess[str]) -> object:
        with mock.patch.object(gh_json.subprocess, "run", return_value=result) as run:
            value = gh_json.run_gh_json(["api", "graphql", "-f", "query=x"], CallerError)
        run.assert_called_once_with(
            ["gh", "api", "graphql", "-f", "query=x"], text=True, capture_output=True, check=False, shell=False
        )
        return value

    def test_returns_the_parsed_payload(self) -> None:
        self.assertEqual(self.run_with(completed(0, '{"data": [1]}')), {"data": [1]})
        self.assertEqual(self.run_with(completed(0, "[]")), [])

    def test_a_failed_call_raises_the_callers_error_with_gh_detail(self) -> None:
        cases = {"stderr wins": ("out", "HTTP 404"), "stdout fallback": ("out", ""), "no detail": ("", "")}
        expected = {"stderr wins": "HTTP 404", "stdout fallback": "out", "no detail": "unknown gh error"}
        for name, (stdout, stderr) in cases.items():
            with self.assertRaises(CallerError, msg=name) as caught:
                self.run_with(completed(1, stdout, stderr))
            self.assertEqual(str(caught.exception), f"gh api graphql failed: {expected[name]}")

    def test_malformed_json_raises_the_callers_error(self) -> None:
        with self.assertRaisesRegex(CallerError, "^gh returned malformed JSON$"):
            self.run_with(completed(0, "{not json"))


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(RunGhJsonTests)


def main() -> int:
    return run_counted(build_suite(), label="test-gh-json")


if __name__ == "__main__":
    raise SystemExit(main())
