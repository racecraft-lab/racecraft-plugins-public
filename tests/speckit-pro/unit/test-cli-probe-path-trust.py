#!/usr/bin/env python3
"""cli_probe rejects runner-owned or runner-writable PATH entries, in the source and in both host payloads."""

from __future__ import annotations

import itertools
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
OPERATOR_CLIS = ("git", "gh")


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

    def test_runner_owned_docker_and_host_executables_are_rejected(self) -> None:
        assert_probe(self, ("docker", *HOSTS), owned="file")

    def test_runner_owned_operator_executable_is_accepted(self) -> None:
        assert_probe(self, OPERATOR_CLIS, owned="file", accepted=True)

    def test_runner_writable_executable_is_rejected(self) -> None:
        assert_probe(self, writable="file")

    def test_runner_writable_host_path_directory_is_rejected(self) -> None:
        assert_probe(self, HOSTS, writable="directory")

    def test_runner_owned_host_path_directory_is_rejected(self) -> None:
        assert_probe(self, HOSTS, owned="directory")

    def test_other_cli_path_directory_stays_outside_the_directory_rule(self) -> None:
        assert_probe(self, ("git", "gh", "docker"), writable="directory", accepted=True)


@contextmanager
def operator_tree():
    """A worktree and a sole PATH directory beside it, both real and owned by the test user."""
    with tempfile.TemporaryDirectory(prefix="cli-probe-operator-") as scratch:
        base = Path(scratch).resolve()
        root, directory = base / "worktree", base / "bin"
        root.mkdir()
        directory.mkdir()
        with patch.dict(os.environ, {"PATH": str(directory)}):
            yield base, root, directory


def write_stub(path, cli, mode=0o755):
    path.write_text(f"#!/bin/sh\necho {cli}-operator-stub\n", encoding="utf-8")
    path.chmod(mode)


@contextmanager
def operator_install(cli, mode=0o755, alias=None):
    """A real PATH directory outside the worktree, owned by the test user, holding an executable stub.

    `alias` names where a second hardlink to the stub lives: "outside" or "worktree".
    """
    with operator_tree() as (base, root, directory):
        stub = directory / cli
        write_stub(stub, cli, mode)
        if alias:
            os.link(stub, {"outside": base, "worktree": root}[alias] / f"alias-{cli}")
        yield root, directory


def symlink_to_worktree_aliased_file(base, root, directory, cli):
    target = base / f"installed-{cli}"
    write_stub(target, cli)
    os.link(target, root / f"alias-{cli}")
    (directory / cli).symlink_to(target)


def symlink_chain_into_worktree(base, root, directory, cli):
    payload = root / f"payload-{cli}"
    write_stub(payload, cli)
    (base / "hop").symlink_to(payload)
    (directory / cli).symlink_to(base / "hop")


def helper_hardlinked_from_worktree(_base, root, directory, cli):
    write_stub(directory / cli, cli)
    write_stub(root / "helper", "helper")
    os.link(root / "helper", directory / "helper")


ALIAS_FORMS = (symlink_to_worktree_aliased_file, symlink_chain_into_worktree, helper_hardlinked_from_worktree)


class OperatorInstalledCliTest(unittest.TestCase):
    """A user-owned install outside the worktree (Homebrew on Apple silicon) serves git and gh, unmocked."""

    def test_operator_owned_git_and_gh_are_found_and_run(self) -> None:
        for cli, alias in itertools.product(OPERATOR_CLIS, (None, "outside")):
            with operator_install(cli, alias=alias) as (root, directory):
                for name in COPIES:
                    with self.subTest(copy=name, cli=cli, alias=alias):
                        module = load(name)
                        self.assertEqual(str(directory), module.probe_search_path(root, cli))
                        result = module.probe(root, [cli, "--version"], allowed=(cli,), timeout=10)
                        self.assertEqual((0, f"{cli}-operator-stub"), (result["exit_status"], result["stdout_tail"]))

    def assert_rejected(self, cli, **install) -> None:
        with operator_install(cli, **install) as (root, _directory):
            for name in COPIES:
                with self.subTest(copy=name, cli=cli, **install), self.assertRaisesRegex(ValueError, NO_SEARCH_DIRECTORY):
                    load(name).probe_search_path(root, cli)

    def test_operator_owned_docker_and_host_installs_stay_rejected(self) -> None:
        for cli in ("docker", *HOSTS):
            self.assert_rejected(cli)

    def test_operator_owned_install_shared_with_other_writers_is_rejected(self) -> None:
        for cli, mode in itertools.product(OPERATOR_CLIS, (0o775, 0o757)):
            self.assert_rejected(cli, mode=mode)

    def test_operator_owned_install_aliased_by_a_worktree_name_is_rejected(self) -> None:
        for cli in OPERATOR_CLIS:
            self.assert_rejected(cli, alias="worktree")

    def test_every_retained_name_gets_the_worktree_alias_check(self) -> None:
        """Symlink hops, symlink targets and helper names beside the CLI are all checked for git and gh."""
        for cli, form in itertools.product(OPERATOR_CLIS, ALIAS_FORMS):
            with operator_tree() as (base, root, directory):
                form(base, root, directory, cli)
                for name in COPIES:
                    with self.subTest(copy=name, cli=cli, form=form.__name__), \
                            self.assertRaisesRegex(ValueError, NO_SEARCH_DIRECTORY):
                        load(name).probe_search_path(root, cli)

    def test_unreadable_worktree_fails_closed_for_an_aliased_operator_install(self) -> None:
        real_scandir = os.scandir

        def unreadable(path=".", *args, **kwargs):
            if Path(path).resolve().is_relative_to(root):
                raise PermissionError(13, "Permission denied", str(path))
            return real_scandir(path, *args, **kwargs)

        for cli in OPERATOR_CLIS:
            with operator_install(cli, alias="outside") as (root, _directory), patch("os.scandir", unreadable):
                for name in COPIES:
                    with self.subTest(copy=name, cli=cli), self.assertRaisesRegex(ValueError, NO_SEARCH_DIRECTORY):
                        load(name).probe_search_path(root, cli)


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    return unittest.TestSuite([loader.loadTestsFromTestCase(CliProbePathTrustTest),
                               loader.loadTestsFromTestCase(OperatorInstalledCliTest)])


def main() -> int:
    return run_counted(build_suite(), label="test-cli-probe-path-trust")


if __name__ == "__main__":
    raise SystemExit(main())
