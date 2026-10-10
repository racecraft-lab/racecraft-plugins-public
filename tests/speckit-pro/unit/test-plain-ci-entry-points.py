#!/usr/bin/env python3
"""The plain CI-suite and PR-title scripts match the raw AGENTS.md commands."""

from __future__ import annotations

import contextlib
import io
import os
import re
import shlex
import signal
import subprocess
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
for directory in (REPO_ROOT / "scripts", REPO_ROOT / "speckit-pro", REPO_ROOT / "tests" / "speckit-pro" / "lib"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from script_loader import load_script  # noqa: E402
from speckit_pro_runner.suite_checkout_lock import SuiteLock  # noqa: E402
from test_result import run_counted  # noqa: E402

TITLE = "chore(repo): plain entry points for the CI suite and title gate"
BASE_ENV = {"KEEP_ME": "yes", "PATH": "inherited-path"}


def documented_raw_command(check: str) -> tuple[dict[str, str], bytes]:
    """Read the environment and stdin operand from the section 2 command."""
    documentation = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    section = documentation.split("## 2. Commands\n", 1)[1].split("\n## 3.", 1)[0]
    row = next(line for line in section.splitlines() if line.startswith(f"| {check}"))
    commands = re.findall(r"`([^`]+)`", row)
    command = next((value for value in commands if " -m speckit_pro_runner < " in value), None)
    if command is None:
        raise AssertionError(f"{check}: copyable raw runner command is missing")
    tokens = shlex.split(command.replace("'<title>'", shlex.quote(TITLE)))
    environment = {}
    while tokens and "=" in tokens[0]:
        key, value = tokens.pop(0).split("=", 1)
        environment[key] = value
    if tokens[:4] != ["python3", "-m", "speckit_pro_runner", "<"] or len(tokens) != 5:
        raise AssertionError(f"{check}: unexpected raw runner invocation")
    if "PYTHONPATH" in environment:
        environment["PYTHONPATH"] = str(REPO_ROOT / environment["PYTHONPATH"])
    return environment, (REPO_ROOT / tokens[4]).read_bytes()


def completed(code: int = 0) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess(args=[], returncode=code)


class PlainEntryPointCase(unittest.TestCase):
    script_name = ""
    module_name = ""
    documented_check = ""
    argv: list[str] = []

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_script(cls.module_name, REPO_ROOT / "scripts" / cls.script_name)

    def suite_lock_patch(self):
        return contextlib.nullcontext()

    def run_script(self, argv: list[str], code: int = 0, base: dict[str, str] | None = None):
        with mock.patch.dict(os.environ, BASE_ENV if base is None else base, clear=True):
            with mock.patch.object(
                self.module.subprocess, "run", return_value=completed(code)
            ) as run, self.suite_lock_patch():
                status = self.module.main(argv)
        return status, run

    def assert_runner_invocation(self, run) -> None:
        self.assertEqual(run.call_args.args[0], [sys.executable, "-m", "speckit_pro_runner"])
        self.assertEqual(Path(run.call_args.kwargs["cwd"]), REPO_ROOT)
        self.assertIs(run.call_args.kwargs["shell"], False)

    def assert_env_adds_exactly(self, run, raw_env: dict[str, str]) -> None:
        self.assertEqual(run.call_args.kwargs["env"], BASE_ENV | raw_env)

    def test_overrides_existing_variables_without_changing_the_parent(self) -> None:
        raw_env, _ = documented_raw_command(self.documented_check)
        base = BASE_ENV | dict.fromkeys(raw_env, "old-value")
        with mock.patch.dict(os.environ, base, clear=True):
            _, run = self.run_script(self.argv, base=base)
            self.assertEqual(dict(os.environ), base)
        self.assertEqual(run.call_args.kwargs["env"], base | raw_env)

    def test_returns_shell_status_for_a_child_killed_by_a_signal(self) -> None:
        for signum in (signal.SIGTERM, signal.SIGINT):
            with self.subTest(signum=signum):
                status, _ = self.run_script(self.argv, code=-signum)
                self.assertEqual(status, 128 + signum)


class RunCiSuiteTests(PlainEntryPointCase):
    script_name = "run-ci-suite.py"
    module_name = "run_ci_suite_script"
    documented_check = "CI suite:"

    def suite_lock_patch(self):
        # The suite running this test already holds the lock on this checkout.
        return mock.patch.object(
            self.module, "hold_suite_lock", return_value=contextlib.nullcontext(SuiteLock())
        )

    def test_sends_the_same_request_the_raw_command_reads(self) -> None:
        _, run = self.run_script([])
        _, request = documented_raw_command(self.documented_check)
        self.assertEqual(run.call_args.kwargs["input"], request)

    def test_child_environment_sets_exactly_the_raw_command_variables(self) -> None:
        _, run = self.run_script([])
        raw_env, _ = documented_raw_command(self.documented_check)
        self.assert_env_adds_exactly(run, raw_env)

    def test_runs_the_runner_module_from_the_repository_root(self) -> None:
        _, run = self.run_script([])
        self.assert_runner_invocation(run)

    def test_returns_the_runner_exit_status(self) -> None:
        for code in (0, 1, 3, 255):
            with self.subTest(code=code):
                status, _ = self.run_script([], code=code)
                self.assertEqual(status, code)


class CheckPrTitleTests(PlainEntryPointCase):
    script_name = "check-pr-title.py"
    module_name = "check_pr_title_script"
    documented_check = "PR title |"
    argv = [TITLE]

    def test_builds_the_request_the_raw_command_reads(self) -> None:
        _, run = self.run_script([TITLE])
        _, request = documented_raw_command(self.documented_check)
        self.assertEqual(run.call_args.kwargs["input"], request)

    def test_child_environment_sets_exactly_the_raw_command_variables(self) -> None:
        _, run = self.run_script([TITLE])
        raw_env, _ = documented_raw_command(self.documented_check)
        self.assert_env_adds_exactly(run, raw_env)

    def test_runs_the_runner_module_from_the_repository_root(self) -> None:
        _, run = self.run_script([TITLE])
        self.assert_runner_invocation(run)

    def test_returns_the_runner_exit_status(self) -> None:
        for code in (0, 1, 3, 255):
            with self.subTest(code=code):
                status, _ = self.run_script([TITLE], code=code)
                self.assertEqual(status, code)

    def test_requires_exactly_one_title(self) -> None:
        for argv in ([], [TITLE, TITLE]):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                self.module.main(argv)


if __name__ == "__main__":
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(case)
        for case in (RunCiSuiteTests, CheckPrTitleTests)
    )
    raise SystemExit(run_counted(suite, label="test-plain-ci-entry-points"))
