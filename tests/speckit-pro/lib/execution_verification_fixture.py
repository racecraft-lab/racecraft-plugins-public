"""Shared fixture for execution-control verification tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from speckit_pro_runner.execution_control import execution_control, is_runner_byproduct
from speckit_pro_runner.verification_records import execute_verification, validate_execution_record


def unittest_output(*failing, ran=6):
    """Default (non-verbose) unittest output naming each failing test."""
    blocks = [f"FAIL: {name} (tests.test_sample.SampleTests.{name})\n" + "-" * 70 + "\nAssertionError\n"
              for name in failing]
    return ("=" * 70 + "\n").join(["", *blocks]) + "-" * 70 + f"\nRan {ran} tests in 0.010s\n\nFAILED (failures={len(failing)})\n"


def bun_output(failing, passing):
    """bun test output, which names every passing and failing test."""
    lines = [f"(pass) sample > {name} [0.10ms]" for name in passing]
    lines += [f"(fail) sample > {name} [0.20ms]" for name in failing]
    lines += ["", f" {len(passing)} pass", f" {len(failing)} fail",
              f"Ran {len(passing) + len(failing)} tests across 1 files. [5.00ms]"]
    return "tests/sample.test.ts:\n" + "\n".join(lines) + "\n"


def make_directory(path, mode=0o755):
    """Create a directory with an exact mode; mkdir(mode=) is masked by the umask."""
    path.mkdir()
    path.chmod(mode)


class VerificationFixture:
    """Temporary consumer repo with a reservable verification command."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        make_directory(self.root / "feature")
        commands = {"UNIT_TEST": f"{sys.executable} check.py"}
        (self.root / "feature/workflow.md").write_text("## PROJECT_COMMANDS\n```json\n" + json.dumps(commands) + "\n```\n")
        (self.root / "check.py").write_text("print('verified')\n")
        (self.root / "fixture.txt").write_text("dirty untracked fixture")
        self.inputs = {"workflow_file": "feature/workflow.md", "command_id": "UNIT_TEST"}
        self.run_id = None

    def produce(self):
        binding = {"expected_run_id": self.run_id} if self.run_id else {}
        started = execution_control(self.root, {"workflow_file": "feature/workflow.md", "action": "start", **binding}, "apply")
        run_id = started["ledger"]["run_id"]
        self.run_id = run_id
        dispatch = uuid.uuid4().hex
        execution_control(self.root, {"workflow_file": "feature/workflow.md", "action": "reserve",
                                      "dispatch_id": dispatch, "kind": "verification", "expected_run_id": run_id}, "apply")
        result = execute_verification(self.root, {**self.inputs, "dispatch_id": dispatch, "expected_run_id": run_id}, "apply")
        observation = {**result["observation_material"], "native_event_id": "actual-host-event-1"}
        return result, observation

    def validate(self, result, observation=None):
        return validate_execution_record(self.root, {**self.inputs, "record_path": result["record_path"], "native_observation": observation})

    def assert_directory_wide_add_never_stages_evidence(self):
        environment = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, env=environment)
        result, _ = self.produce()
        ledger = self.root / "feature/.process/execution-control"
        self.assertTrue(any(ledger.glob("*.json")) and (self.root / result["record_path"]).is_file())
        subprocess.run(["git", "-C", str(self.root), "add", "-A"], check=True, env=environment)
        staged = subprocess.run(["git", "-C", str(self.root), "diff", "--cached", "--name-only", "-z"], check=True,
                                capture_output=True, text=True, env=environment).stdout.split("\0")
        staged = [name for name in staged if name]
        self.assertIn("fixture.txt", staged)
        self.assertEqual([name for name in staged if is_runner_byproduct(name)], [])
        self.assertEqual([name for name in staged if "execution-control" in name or "verification" in name], [])
        for directory in (ledger, (self.root / result["record_path"]).parent):
            self.assertTrue(is_runner_byproduct((directory / ".gitignore").relative_to(self.root).as_posix()))
