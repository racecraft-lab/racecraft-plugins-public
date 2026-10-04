#!/usr/bin/env python3
"""The plain CI-suite and PR-title scripts match the raw AGENTS.md commands."""

from __future__ import annotations

import io
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from script_loader import load_script  # noqa: E402
from test_result import run_counted  # noqa: E402

REQUESTS = REPO_ROOT / "tests/speckit-pro/unit/fixtures/runner-gates/requests"
CI_REQUEST = REQUESTS / "run-ci-suite.json"
TITLE_REQUEST = REQUESTS / "validate-pr-title-live.json"
TITLE = "chore(repo): plain entry points for the CI suite and title gate"

# The raw AGENTS.md section 2 commands set exactly these variables.
RAW_CI_ENV = {
    "SPECKIT_SKIP_TOOLCHAIN_CHECK": "1",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
    "GIT_CONFIG_NOSYSTEM": "1",
    "PYTHONPATH": str(REPO_ROOT / "speckit-pro"),
}
RAW_TITLE_ENV = {"TITLE": TITLE, "PYTHONPATH": str(REPO_ROOT / "speckit-pro")}


def completed(code: int = 0) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess(args=[], returncode=code)


class PlainEntryPointCase(unittest.TestCase):
    script_name = ""
    module_name = ""

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_script(cls.module_name, REPO_ROOT / "scripts" / cls.script_name)

    def run_script(self, argv: list[str], code: int = 0):
        with mock.patch.dict(os.environ, {"KEEP_ME": "yes"}, clear=False):
            with mock.patch.object(
                self.module.subprocess, "run", return_value=completed(code)
            ) as run:
                status = self.module.main(argv)
        return status, run

    def assert_runner_invocation(self, run) -> None:
        self.assertEqual(run.call_args.args[0], [sys.executable, "-m", "speckit_pro_runner"])
        self.assertEqual(Path(run.call_args.kwargs["cwd"]), REPO_ROOT)
        self.assertIs(run.call_args.kwargs["shell"], False)

    def assert_env_adds_exactly(self, run, raw_env: dict[str, str]) -> None:
        env = run.call_args.kwargs["env"]
        for key, value in raw_env.items():
            self.assertEqual(env[key], value)
        self.assertEqual(env["KEEP_ME"], "yes")
        # Everything else is inherited unchanged; nothing extra is added.
        for key in set(env) - set(raw_env) - {"KEEP_ME"}:
            self.assertEqual(env[key], os.environ[key])
        unexpected = set(env) - set(os.environ) - {"KEEP_ME"} - set(raw_env)
        self.assertEqual(unexpected, set())


class RunCiSuiteTests(PlainEntryPointCase):
    script_name = "run-ci-suite.py"
    module_name = "run_ci_suite_script"

    def test_sends_the_same_request_the_raw_command_reads(self) -> None:
        _, run = self.run_script([])
        self.assertEqual(run.call_args.kwargs["input"], CI_REQUEST.read_bytes())

    def test_child_environment_sets_exactly_the_raw_command_variables(self) -> None:
        _, run = self.run_script([])
        self.assert_env_adds_exactly(run, RAW_CI_ENV)

    def test_runs_the_runner_module_from_the_repository_root(self) -> None:
        _, run = self.run_script([])
        self.assert_runner_invocation(run)

    def test_returns_the_runner_exit_status(self) -> None:
        status, _ = self.run_script([], code=3)
        self.assertEqual(status, 3)


class CheckPrTitleTests(PlainEntryPointCase):
    script_name = "check-pr-title.py"
    module_name = "check_pr_title_script"

    def test_builds_the_request_the_raw_command_reads(self) -> None:
        _, run = self.run_script([TITLE])
        self.assertEqual(run.call_args.kwargs["input"], TITLE_REQUEST.read_bytes())

    def test_child_environment_sets_exactly_the_raw_command_variables(self) -> None:
        _, run = self.run_script([TITLE])
        self.assert_env_adds_exactly(run, RAW_TITLE_ENV)

    def test_runs_the_runner_module_from_the_repository_root(self) -> None:
        _, run = self.run_script([TITLE])
        self.assert_runner_invocation(run)

    def test_returns_the_runner_exit_status(self) -> None:
        status, _ = self.run_script([TITLE], code=1)
        self.assertEqual(status, 1)

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
