#!/usr/bin/env python3
"""One suite at a time per checkout: the quick and CI suite entry points share a lock."""

from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
for directory in (REPO_ROOT / "scripts", REPO_ROOT / "tests" / "speckit-pro" / "lib"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from script_loader import load_script  # noqa: E402
from test_result import run_counted  # noqa: E402

import suite_checkout_lock as lock  # noqa: E402

run_all = load_script("run_all_for_lock", REPO_ROOT / "tests" / "speckit-pro" / "run-all.py")
run_ci_suite = load_script("run_ci_suite_for_lock", REPO_ROOT / "scripts" / "run-ci-suite.py")

EMPTY_LAYER = {
    "layers": [
        {
            "id": "4",
            "label": "Script unit tests",
            "default": True,
            "live_only": False,
            "integration": False,
            "execution": "execute",
            "scripts": [],
        }
    ]
}


def fresh_checkout(case: unittest.TestCase, *, git_dir: bool = True) -> Path:
    """Return a directory standing in for a checkout; removed after the test."""
    root = Path(tempfile.mkdtemp(prefix="suite-lock-")).resolve()
    case.addCleanup(shutil.rmtree, root, ignore_errors=True)
    if git_dir:
        (root / ".git").mkdir()
    return root


needs_flock = unittest.skipIf(lock.fcntl is None, "flock is unavailable on this platform")


@needs_flock
class SuiteCheckoutLockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = fresh_checkout(self)

    def test_second_holder_in_the_same_checkout_is_refused(self) -> None:
        with lock.hold_suite_lock(self.root):
            with self.assertRaises(lock.SuiteLockHeld) as raised:
                with lock.hold_suite_lock(self.root):
                    self.fail("the second suite must not start")
        self.assertIn(str(os.getpid()), str(raised.exception))

    def test_lock_is_released_when_the_suite_exits(self) -> None:
        with lock.hold_suite_lock(self.root):
            pass
        with lock.hold_suite_lock(self.root):
            pass

    def test_lock_is_released_when_the_suite_raises(self) -> None:
        with self.assertRaises(RuntimeError):
            with lock.hold_suite_lock(self.root):
                raise RuntimeError("suite crashed")
        with lock.hold_suite_lock(self.root):
            pass

    def test_other_checkouts_do_not_block_each_other(self) -> None:
        other = fresh_checkout(self)
        with lock.hold_suite_lock(self.root), lock.hold_suite_lock(other):
            pass

    def test_worktree_git_file_resolves_to_its_own_git_directory(self) -> None:
        real = fresh_checkout(self)
        linked = fresh_checkout(self, git_dir=False)
        (linked / ".git").write_text(f"gitdir: {real / '.git'}\n", encoding="utf-8")
        with lock.hold_suite_lock(linked):
            self.assertTrue((real / ".git" / lock.LOCK_NAME).is_file())
            with self.assertRaises(lock.SuiteLockHeld):
                with lock.hold_suite_lock(linked):
                    pass

    def test_released_lock_does_not_leave_a_stale_holder(self) -> None:
        with lock.hold_suite_lock(self.root):
            pass
        self.assertEqual((self.root / ".git" / lock.LOCK_NAME).read_text(encoding="utf-8"), "")

    def test_lock_dies_with_a_killed_holder(self) -> None:
        code = (
            "import sys, time; sys.path.insert(0, sys.argv[1]);"
            "import suite_checkout_lock as l; from pathlib import Path;"
            "cm = l.hold_suite_lock(Path(sys.argv[2])); cm.__enter__();"
            "print('held', flush=True); time.sleep(60)"
        )
        child = subprocess.Popen(
            [sys.executable, "-c", code, str(REPO_ROOT / "scripts"), str(self.root)],
            stdout=subprocess.PIPE,
            text=True,
        )
        self.addCleanup(child.wait)
        self.addCleanup(child.kill)
        self.assertEqual(child.stdout.readline().strip(), "held")
        with self.assertRaises(lock.SuiteLockHeld) as raised:
            with lock.hold_suite_lock(self.root):
                pass
        self.assertIn(str(child.pid), str(raised.exception))
        child.kill()
        child.wait()
        with lock.hold_suite_lock(self.root):
            pass


@needs_flock
class UnguardedCheckoutTests(unittest.TestCase):
    def test_checkout_without_a_git_directory_runs_unguarded_with_a_warning(self) -> None:
        root = fresh_checkout(self, git_dir=False)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            with lock.hold_suite_lock(root), lock.hold_suite_lock(root):
                pass
        self.assertIn("running without the one-suite guard", err.getvalue())

    def test_unwritable_lock_file_runs_unguarded_with_a_warning(self) -> None:
        root = fresh_checkout(self)
        err = io.StringIO()
        with (
            mock.patch("builtins.open", side_effect=PermissionError(13, "Permission denied")),
            contextlib.redirect_stderr(err),
        ):
            with lock.hold_suite_lock(root):
                pass
        self.assertIn("Permission denied", err.getvalue())


@needs_flock
class EntryPointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = fresh_checkout(self)

    def quick_suite(self) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with (
            mock.patch.object(run_all, "repo_root", return_value=self.root),
            mock.patch.object(run_all, "load_manifest", return_value=EMPTY_LAYER),
            mock.patch.dict(run_all.os.environ, {"SPECKIT_SKIP_TOOLCHAIN_CHECK": "1"}),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            status = run_all.main(["--layer", "4"])
        return status, out.getvalue(), err.getvalue()

    def ci_suite(self, returncode: int = 0) -> tuple[int, str, mock.MagicMock]:
        err = io.StringIO()
        finished = subprocess.CompletedProcess(args=[], returncode=returncode)
        with (
            mock.patch.object(run_ci_suite, "REPO_ROOT", self.root),
            mock.patch.object(run_ci_suite.subprocess, "run", return_value=finished) as run,
            contextlib.redirect_stderr(err),
        ):
            status = run_ci_suite.main([])
        return status, err.getvalue(), run

    def test_each_entry_point_refuses_while_another_suite_holds_the_checkout(self) -> None:
        with lock.hold_suite_lock(self.root):
            quick_status, quick_out, quick_err = self.quick_suite()
            ci_status, ci_err, ci_run = self.ci_suite()
        for status, err in ((quick_status, quick_err), (ci_status, ci_err)):
            self.assertEqual(status, lock.REFUSED_STATUS)
            self.assertIn("another suite is already running", err)
        self.assertNotIn("Layer 4", quick_out)
        ci_run.assert_not_called()

    def test_quick_suite_refuses_while_the_ci_suite_runs(self) -> None:
        results: list[tuple[int, str, str]] = []

        def during_ci_run(*_args, **_kwargs):
            results.append(self.quick_suite())
            return subprocess.CompletedProcess(args=[], returncode=0)

        err = io.StringIO()
        with (
            mock.patch.object(run_ci_suite, "REPO_ROOT", self.root),
            mock.patch.object(run_ci_suite.subprocess, "run", side_effect=during_ci_run),
            contextlib.redirect_stderr(err),
        ):
            self.assertEqual(run_ci_suite.main([]), 0)
        self.assertEqual(results[0][0], lock.REFUSED_STATUS)
        self.assertIn("another suite is already running", results[0][2])

    def test_lock_is_free_after_each_suite_even_when_it_fails(self) -> None:
        status, err, _ = self.ci_suite(returncode=3)
        self.assertEqual(status, 3)
        self.assertNotIn("already running", err)
        status, out, err = self.quick_suite()
        self.assertEqual(status, 1)  # the empty layer fails on its own, not on the lock
        self.assertIn("no test scripts discovered", out)
        self.assertNotIn("already running", err)
        with lock.hold_suite_lock(self.root):
            pass


if __name__ == "__main__":
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(case)
        for case in (SuiteCheckoutLockTests, UnguardedCheckoutTests, EntryPointTests)
    )
    raise SystemExit(run_counted(suite, label="test-suite-checkout-lock"))
