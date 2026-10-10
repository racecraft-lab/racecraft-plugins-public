#!/usr/bin/env python3
"""One suite at a time per checkout: the quick and CI suite entry points share a lock."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
for directory in (REPO_ROOT / "scripts", REPO_ROOT / "speckit-pro", REPO_ROOT / "tests" / "speckit-pro" / "lib"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from runner_invocation import run_runner  # noqa: E402
from script_loader import load_script  # noqa: E402
from test_result import run_counted  # noqa: E402

import speckit_pro_runner.suite_checkout_lock as lock  # noqa: E402

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


CI_REQUEST = REPO_ROOT / "tests/speckit-pro/unit/fixtures/runner-gates/requests/run-ci-suite.json"


def runner_checkout(case: unittest.TestCase) -> Path:
    """A checkout the runner accepts as a repository root, with its own git directory."""
    root = fresh_checkout(case)
    (root / "speckit-pro" / "speckit_pro_runner").mkdir(parents=True)
    (root / "tests" / "speckit-pro").mkdir(parents=True)
    return root


def ci_request_with_sentinels(sentinel: Path) -> dict:
    """The CI suite request, each command replaced by one that records it started."""
    request = json.loads(CI_REQUEST.read_text(encoding="utf-8"))
    record = f"open({str(sentinel)!r}, 'a').write('started\\n')"
    command_ids = ["toolchain", "layer-1", "layer-4", "layer-5", "layer-6", "layer-7"]
    request["inputs"]["test_commands"] = {
        command_id: {"argv": [sys.executable, "-c", record], "timeout_seconds": 30} for command_id in command_ids
    }
    return request


# Writes its pid where the test can find it, then outlives the parent that started it.
SLEEPER = (
    "import os, sys, time; from pathlib import Path; pid = Path(sys.argv[1]);"
    "pid.with_suffix('.tmp').write_text(str(os.getpid())); pid.with_suffix('.tmp').replace(pid);"
    "time.sleep(120)"
)
TESTS_LIB = REPO_ROOT / "tests" / "speckit-pro" / "lib"
CI_WRAPPER_DRIVER = """
import sys
from pathlib import Path
sys.path[:0] = [sys.argv[1], sys.argv[2]]
from script_loader import load_script
wrapper = load_script("run_ci_suite_driven", Path(sys.argv[1]) / "run-ci-suite.py")
wrapper.REPO_ROOT = Path(sys.argv[3])
wrapper.REQUEST_FILE = Path(sys.argv[4])
raise SystemExit(wrapper.main([]))
"""
QUICK_SUITE_DRIVER = """
import json, sys
from pathlib import Path
from unittest import mock
sys.path.insert(0, sys.argv[1])
from script_loader import load_script
run_all = load_script("run_all_driven", Path(sys.argv[2]))
root, manifest = Path(sys.argv[3]), json.loads(sys.argv[4])
with mock.patch.object(run_all, "repo_root", return_value=root), mock.patch.object(run_all, "load_manifest", return_value=manifest):
    raise SystemExit(run_all.main(["--layer", "4"]))
"""
LAYER_DISPATCHER_DRIVER = """
import sys
from pathlib import Path
from unittest import mock
sys.path.insert(0, sys.argv[1])
from script_loader import load_script
dispatcher = load_script("run_layer_scripts_driven", Path(sys.argv[2]))
with mock.patch.object(dispatcher, "resolve_repo_root", return_value=Path(sys.argv[3])):
    raise SystemExit(dispatcher.main(["--layer", "4"]))
"""


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
            "import speckit_pro_runner.suite_checkout_lock as l; from pathlib import Path;"
            "cm = l.hold_suite_lock(Path(sys.argv[2])); cm.__enter__();"
            "print('held', flush=True); time.sleep(60)"
        )
        child = subprocess.Popen(
            [sys.executable, "-c", code, str(REPO_ROOT / "speckit-pro"), str(self.root)],
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
            with lock.hold_suite_lock(root) as first, lock.hold_suite_lock(root):
                pass
        # The runner's stderr is a JSON channel: the module never prints, callers do.
        self.assertEqual(err.getvalue(), "")
        self.assertIn("running without the one-suite guard", first.unguarded_warning)
        self.assertEqual(first.environment({}), {})

    def test_unwritable_lock_file_refuses_execution(self) -> None:
        root = fresh_checkout(self)
        err = io.StringIO()
        with (
            mock.patch("builtins.open", side_effect=PermissionError(13, "Permission denied")),
            contextlib.redirect_stderr(err),
        ):
            with self.assertRaises(lock.SuiteLockUnavailable) as raised:
                with lock.hold_suite_lock(root):
                    self.fail("the suite must not start without a lock")
        self.assertIn("Permission denied", str(raised.exception))


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

    def test_each_entry_point_refuses_without_an_exclusive_checkout_lock(self) -> None:
        cases = (
            (lock.hold_suite_lock(self.root), "another suite is already running"),
            (mock.patch("builtins.open", side_effect=PermissionError(13, "Permission denied")), "cannot open the lock file"),
            (mock.patch.object(lock.fcntl, "flock", side_effect=OSError(95, "Operation not supported")), "flock failed"),
        )
        for guard, message in cases:
            with self.subTest(reason=message), guard:
                quick_status, _, quick_err = self.quick_suite()
                ci_status, ci_err, ci_run = self.ci_suite()
            for status, err in ((quick_status, quick_err), (ci_status, ci_err)):
                self.assertEqual(status, 75)
                self.assertIn(message, err)
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
        status, out, err = self.quick_suite()
        self.assertEqual(status, 1)  # the empty layer fails on its own, not on the lock
        self.assertIn("no test scripts discovered", out)
        with lock.hold_suite_lock(self.root):
            pass


@needs_flock
class RawRunnerRequestTests(unittest.TestCase):
    """The runner's suite gate takes the lock, so the raw CI command cannot bypass it."""

    def setUp(self) -> None:
        self.root = runner_checkout(self)
        self.sentinel = self.root / "started.txt"
        self.request = ci_request_with_sentinels(self.sentinel)

    def test_raw_ci_request_is_refused_while_another_suite_holds_the_checkout(self) -> None:
        with lock.hold_suite_lock(self.root):
            completed, response, stderr_records = run_runner(self.request, cwd=self.root)
        self.assertFalse(self.sentinel.exists(), "a CI command started despite the held lock")
        self.assertEqual(response["status"], "missing_prerequisite")
        self.assertEqual(completed.returncode, 3)
        self.assertEqual([record["code"] for record in stderr_records], ["suite_lock_held"])
        self.assertIn("another suite is already running", response["diagnostics"][0]["message"])

    def test_raw_ci_request_runs_once_the_checkout_is_free(self) -> None:
        completed, response, _ = run_runner(self.request, cwd=self.root)
        self.assertEqual(response["status"], "ok", completed.stderr)
        self.assertEqual(self.sentinel.read_text(encoding="utf-8").count("started"), 6)

    def test_a_suite_holding_the_lock_can_still_send_its_own_runner_requests(self) -> None:
        with lock.hold_suite_lock(self.root) as held:
            completed, response, _ = run_runner(self.request, cwd=self.root, extra_env=held.environment({}))
        self.assertEqual(response["status"], "ok", completed.stderr)
        self.assertEqual(self.sentinel.read_text(encoding="utf-8").count("started"), 6)


@needs_flock
class KilledParentTests(unittest.TestCase):
    """Killing the process that took the lock leaves it held while a suite child still runs."""

    def setUp(self) -> None:
        self.root = runner_checkout(self)
        self.pid_file = self.root / "child.pid"
        self.environment = dict(os.environ, SPECKIT_SKIP_TOOLCHAIN_CHECK="1", PYTHONDONTWRITEBYTECODE="1")
        sleeper = self.root / "sleeper.py"
        sleeper.write_text(f"import sys; sys.argv[1:] = [{str(self.pid_file)!r}]\n{SLEEPER}\n", encoding="utf-8")
        self.layer = {
            "id": "4",
            "key": "unit",
            "label": "Script unit tests",
            "default": True,
            "live_only": False,
            "integration": False,
            "dispatch": "python-module",
            "execution": "execute",
            "scripts": [{"path": "sleeper.py"}],
        }

    def sleeper_request(self) -> dict:
        command = {"argv": [sys.executable, "-c", SLEEPER, str(self.pid_file)], "timeout_seconds": 120}
        return {
            "schema_version": "1.0",
            "request_id": "killed-parent",
            "helper_id": "suite-gate",
            "operation": "run-layer",
            "mode": "read_only",
            "inputs": {"repo_root": ".", "layer": "4", "test_commands": {"layer-4": command}},
        }

    def start(self, argv: list[str], *, stdin: bytes | None = None) -> subprocess.Popen:
        # A new session puts the parent and every child it starts in one group the cleanup can kill.
        parent = subprocess.Popen(
            argv,
            cwd=self.root,
            env=self.environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        self.addCleanup(self.kill_group, parent.pid)
        parent.stdin.write(stdin or b"")
        parent.stdin.close()
        return parent

    def kill_group(self, group: int) -> None:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(group, signal.SIGKILL)

    def wait_for_child(self, parent: subprocess.Popen) -> int:
        deadline = time.monotonic() + 60
        while not self.pid_file.exists():
            if parent.poll() is not None or time.monotonic() > deadline:
                self.fail(f"the suite child never started (parent exit {parent.returncode})")
            time.sleep(0.05)
        return int(self.pid_file.read_text(encoding="utf-8"))

    def assert_lock_outlives_killed_parent(self, parent: subprocess.Popen) -> None:
        child = self.wait_for_child(parent)
        parent.kill()
        parent.wait()
        os.kill(child, 0)  # the suite child is still running
        with self.assertRaises(lock.SuiteLockHeld, msg="a second suite started beside a running suite child"):
            with lock.hold_suite_lock(self.root):
                pass
        self.kill_group(parent.pid)
        deadline = time.monotonic() + 30
        while True:
            try:
                with lock.hold_suite_lock(self.root):
                    return
            except lock.SuiteLockHeld:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.05)

    def test_killing_the_ci_wrapper_keeps_the_lock_while_its_runner_child_runs(self) -> None:
        request = self.root / "request.json"
        request.write_text(json.dumps(self.sleeper_request()), encoding="utf-8")
        parent = self.start(
            [sys.executable, "-c", CI_WRAPPER_DRIVER, str(REPO_ROOT / "scripts"), str(TESTS_LIB), str(self.root), str(request)]
        )
        self.assert_lock_outlives_killed_parent(parent)

    def test_killing_the_runner_keeps_the_lock_while_its_suite_command_runs(self) -> None:
        environment = dict(self.environment, PYTHONPATH=str(REPO_ROOT / "speckit-pro"))
        self.environment = environment
        parent = self.start(
            [sys.executable, "-m", "speckit_pro_runner"], stdin=json.dumps(self.sleeper_request()).encode()
        )
        self.assert_lock_outlives_killed_parent(parent)

    def test_killing_the_quick_suite_keeps_the_lock_while_its_test_child_runs(self) -> None:
        manifest = {"layers": [self.layer]}
        parent = self.start(
            [
                sys.executable,
                "-c",
                QUICK_SUITE_DRIVER,
                str(TESTS_LIB),
                str(REPO_ROOT / "tests" / "speckit-pro" / "run-all.py"),
                str(self.root),
                json.dumps(manifest),
            ]
        )
        self.assert_lock_outlives_killed_parent(parent)

    def test_killing_the_layer_dispatcher_keeps_the_lock_while_its_test_child_runs(self) -> None:
        manifest = self.root / "tests" / "speckit-pro" / "suite-manifest.json"
        manifest.write_text(json.dumps({"layers": [self.layer]}), encoding="utf-8")
        parent = self.start(
            [
                sys.executable,
                "-c",
                LAYER_DISPATCHER_DRIVER,
                str(TESTS_LIB),
                str(REPO_ROOT / "tests" / "speckit-pro" / "run-layer-scripts.py"),
                str(self.root),
            ]
        )
        self.assert_lock_outlives_killed_parent(parent)


if __name__ == "__main__":
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(case)
        for case in (
            SuiteCheckoutLockTests,
            UnguardedCheckoutTests,
            EntryPointTests,
            RawRunnerRequestTests,
            KilledParentTests,
        )
    )
    raise SystemExit(run_counted(suite, label="test-suite-checkout-lock"))
