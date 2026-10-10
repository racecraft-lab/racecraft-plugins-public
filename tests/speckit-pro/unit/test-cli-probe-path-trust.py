#!/usr/bin/env python3
"""cli_probe rejects runner-owned or runner-writable PATH entries, in the source and in both host payloads."""

from __future__ import annotations

import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
sys.path.insert(0, str(TEST_DIR.parent / "lib"))

from test_result import run_counted  # noqa: E402

COPIES = {
    "source": REPO_ROOT / "speckit-pro/speckit_pro_runner/cli_probe.py",
    "claude": REPO_ROOT / "dist/claude/speckit-pro/speckit_pro_runner/cli_probe.py",
    "codex": REPO_ROOT / "dist/codex/speckit-pro/speckit_pro_runner/cli_probe.py",
}
OTHER_IDENTITY = -1  # no file is owned by it, so only the write-access rule can reject
NO_SEARCH_DIRECTORY = "no external absolute CLI search directory"


def load(name: str):
    spec = importlib.util.spec_from_file_location(f"cli_probe_{name}", COPIES[name])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CliProbePathTrustTest(unittest.TestCase):
    """Each test runs once per copy. The runner identity is modeled at the two inputs the rule reads."""

    def setUp(self) -> None:
        self.root = self.scratch_dir("worktree")
        self.bin = self.scratch_dir("bin")
        self.tool = self.install(self.bin, "codex")

    def scratch_dir(self, name: str) -> Path:
        directory = Path(tempfile.mkdtemp(prefix=f"cli-probe-{name}-")).resolve()
        self.addCleanup(shutil.rmtree, directory, True)
        return directory

    @staticmethod
    def install(directory: Path, name: str) -> Path:
        tool = directory / name
        tool.write_text("#!/bin/sh\n", encoding="utf-8")
        tool.chmod(0o555)
        return tool

    def identity(self, *, euid: int, writable: set[Path]):
        """Pretend the runner is `euid` and can write exactly the paths in `writable`."""
        paths = {path.resolve() for path in writable}
        return (patch("os.geteuid", return_value=euid),
                patch("os.access", side_effect=lambda path, mode, **options:
                      mode == os.W_OK and Path(path).resolve() in paths))

    def search(self, module, cli: str = "codex") -> str:
        with patch.dict(os.environ, {"PATH": str(self.bin)}):
            return module.probe_search_path(self.root, cli)

    def each_copy(self):
        for name in COPIES:
            with self.subTest(copy=name):
                yield load(name)

    def test_root_owned_read_only_executable_is_accepted(self) -> None:
        owner, access = self.identity(euid=OTHER_IDENTITY, writable=set())
        with owner, access:
            for module in self.each_copy():
                self.assertEqual(str(self.bin), self.search(module))

    def test_runner_owned_executable_is_rejected(self) -> None:
        owner, access = self.identity(euid=self.tool.stat().st_uid, writable=set())
        with owner, access:
            for module in self.each_copy():
                with self.assertRaisesRegex(ValueError, NO_SEARCH_DIRECTORY):
                    self.search(module)

    def test_runner_writable_executable_is_rejected(self) -> None:
        owner, access = self.identity(euid=OTHER_IDENTITY, writable={self.tool})
        with owner, access:
            for module in self.each_copy():
                with self.assertRaisesRegex(ValueError, NO_SEARCH_DIRECTORY):
                    self.search(module)

    def test_runner_writable_host_path_directory_is_rejected(self) -> None:
        owner, access = self.identity(euid=OTHER_IDENTITY, writable={self.bin})
        with owner, access:
            for module in self.each_copy():
                with self.assertRaisesRegex(ValueError, NO_SEARCH_DIRECTORY):
                    self.search(module)

    def test_runner_owned_host_path_directory_is_rejected(self) -> None:
        owner, access = self.identity(euid=self.bin.stat().st_uid, writable=set())
        with owner, access:
            for module in self.each_copy():
                with self.assertRaisesRegex(ValueError, "mutable directory"):
                    module.reject_mutable_probe_alias(self.bin.lstat(), self.bin, host=True)

    def test_other_cli_path_directory_stays_outside_the_directory_rule(self) -> None:
        # Pins the documented split: only host lookups require a protected directory.
        owner, access = self.identity(euid=OTHER_IDENTITY, writable={self.bin})
        self.install(self.bin, "git")
        with owner, access:
            for module in self.each_copy():
                self.assertEqual(str(self.bin), self.search(module, "git"))


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(CliProbePathTrustTest)


def main() -> int:
    return run_counted(build_suite(), label="test-cli-probe-path-trust")


if __name__ == "__main__":
    raise SystemExit(main())
