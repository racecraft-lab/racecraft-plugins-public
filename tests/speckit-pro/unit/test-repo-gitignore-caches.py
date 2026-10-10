#!/usr/bin/env python3
"""The repository .gitignore covers the pnpm store and Python tool caches."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from test_result import run_counted

REPO_ROOT = Path(__file__).resolve().parents[3]
CACHE_PROBES = (
    ".pnpm-store/v10/files/00/probe",
    ".mypy_cache/3.12/probe.json",
    ".ruff_cache/probe",
)


class RepoGitignoreCacheTests(unittest.TestCase):
    def test_pnpm_store_and_python_tool_caches_are_ignored(self):
        for probe in CACHE_PROBES:
            with self.subTest(path=probe):
                result = subprocess.run(
                    ["git", "-C", str(REPO_ROOT), "check-ignore", "-q", probe],
                    check=False,
                )
                self.assertEqual(result.returncode, 0, f"{probe} is not ignored")


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(RepoGitignoreCacheTests), label="test-repo-gitignore-caches"))
