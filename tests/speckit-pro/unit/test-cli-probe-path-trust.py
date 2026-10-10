#!/usr/bin/env python3
"""cli_probe rejects runner-owned or runner-writable PATH entries, in the source and in both host payloads."""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from functools import partial
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
sys.path.insert(0, str(TEST_DIR.parent / "lib"))

from script_loader import load_script  # noqa: E402
from test_result import run_counted  # noqa: E402

COPIES = {
    "source": REPO_ROOT / "speckit-pro/speckit_pro_runner/cli_probe.py",
    "claude": REPO_ROOT / "dist/claude/speckit-pro/speckit_pro_runner/cli_probe.py",
    "codex": REPO_ROOT / "dist/codex/speckit-pro/speckit_pro_runner/cli_probe.py",
}
OTHER_IDENTITY = -1  # the modeled runner uid: geteuid returns it and an owned inode reports it, so no real file matches
NO_SEARCH_DIRECTORY = "no external absolute CLI search directory"


def load(name: str):
    return load_script(f"cli_probe_{name}", COPIES[name])


CLIS = ("codex", "claude", "git", "gh", "docker")
HOSTS = ("codex", "claude")


@contextmanager
def probe_fixture(cli, layout):
    """Keep only the requested CLI in PATH, including when it has an external alias."""
    with tempfile.TemporaryDirectory(prefix="cli-probe-") as scratch:
        base = Path(scratch).resolve()
        root, directory = base / "worktree", base / "bin"
        root.mkdir()
        directory.mkdir()
        tool = directory / cli
        target = base / cli if layout in ("symlink", "hardlink") else tool
        target.write_text("#!/bin/sh\n", encoding="utf-8")
        target.chmod(0o555)
        if layout == "symlink":
            tool.symlink_to(target)
        elif layout == "hardlink":
            tool.hardlink_to(target)
        yield root, directory, target


@contextmanager
def probe_identity(directory, target, owned, writable):
    """Ownership and access follow inode identity, modeled on os.stat and os.lstat so every interpreter's Path reads reach it."""
    selected = {"file": target, "directory": directory}
    owned_info = selected[owned].stat() if owned else None
    writable_info = selected[writable].stat() if writable else None
    real_stat, real_lstat = os.stat, os.lstat

    def owned_as_runner(read, path, *args, **options):
        info = read(path, *args, **options)
        if not (owned_info and (info.st_dev, info.st_ino) == (owned_info.st_dev, owned_info.st_ino)):
            return info
        return os.stat_result([*info[:4], OTHER_IDENTITY, *info[5:]])

    def can_write(path, mode, **options):
        info = real_stat(path)
        return mode == os.W_OK and writable_info is not None and (
            info.st_dev, info.st_ino) == (writable_info.st_dev, writable_info.st_ino)

    with patch("os.geteuid", return_value=OTHER_IDENTITY), patch("os.access", side_effect=can_write), \
            patch("os.stat", partial(owned_as_runner, real_stat)), \
            patch("os.lstat", partial(owned_as_runner, real_lstat)):
        yield


def assert_probe(test, clis=CLIS, owned=None, writable=None, accepted=False):
    """Exercise each assertion at the public lookup boundary in every shipped copy."""
    for cli in clis:
        for layout in ("file", "symlink", "hardlink"):
            with probe_fixture(cli, layout) as (root, directory, target):
                for name in COPIES:
                    with test.subTest(copy=name, cli=cli, layout=layout):
                        module = load(name)
                        with probe_identity(directory, target, owned, writable), \
                                patch.dict(os.environ, {"PATH": str(directory)}):
                            if accepted:
                                test.assertEqual(str(directory), module.probe_search_path(root, cli))
                            else:
                                with test.assertRaisesRegex(ValueError, NO_SEARCH_DIRECTORY):
                                    module.probe_search_path(root, cli)
                            if owned == "directory":
                                with test.assertRaisesRegex(ValueError, "mutable directory"):
                                    module.reject_mutable_probe_alias(directory.lstat(), directory, host=True)


class CliProbePathTrustTest(unittest.TestCase):
    """The same public lookup contract covers source and both shipped hosts."""

    def test_root_owned_read_only_executable_is_accepted(self) -> None:
        assert_probe(self, accepted=True)

    def test_runner_owned_executable_is_rejected(self) -> None:
        assert_probe(self, owned="file")

    def test_runner_writable_executable_is_rejected(self) -> None:
        assert_probe(self, writable="file")

    def test_runner_writable_host_path_directory_is_rejected(self) -> None:
        assert_probe(self, HOSTS, writable="directory")

    def test_runner_owned_host_path_directory_is_rejected(self) -> None:
        assert_probe(self, HOSTS, owned="directory")

    def test_other_cli_path_directory_stays_outside_the_directory_rule(self) -> None:
        assert_probe(self, ("git", "gh", "docker"), writable="directory", accepted=True)



def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(CliProbePathTrustTest)


def main() -> int:
    return run_counted(build_suite(), label="test-cli-probe-path-trust")


if __name__ == "__main__":
    raise SystemExit(main())
