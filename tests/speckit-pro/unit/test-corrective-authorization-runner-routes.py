#!/usr/bin/env python3
"""Replay the ledger's operator-approved corrective scenarios through the real runner.

Each fixture under `evals/fixtures/functional/corrective-authorization/` is an
ordered list of execution-control request envelopes with their expected
outcomes. The test stages the fixture workflow and spec in a consumer repository
built at run time and sends every step to `python -m speckit_pro_runner`, the way
an autopilot parent does. Values the ledger mints at run time are fixture tokens:
`$run_id`, `$reservation:<dispatch_id>`, `$spec_sha256`, and `$spec_file`.
Every refused step must leave the ledger bytes unchanged.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
FIXTURE_ROOT = TEST_ROOT / "evals" / "fixtures" / "functional" / "corrective-authorization"
sys.path.insert(0, str(TEST_ROOT / "lib"))

from test_result import run_counted  # noqa: E402


WORKFLOW = "feature/workflow.md"
SPEC = "feature/spec.md"
SCENARIOS = (
    "bind-invariants.json",
    "corrective-retry.json",
    "corrective-continuation.json",
    "corrective-exception.json",
    "deferral-resolution.json",
    "test-fix.json",
)
CONVERGENCE_SCENARIOS = ("convergence-go-test.json",)
CHECK_FIXTURES = TEST_ROOT / "unit" / "fixtures" / "failing-checks"
APPROVAL_SCENARIOS = tuple(name for name in SCENARIOS if name != "test-fix.json")
REFUSED = {"exit_code": 2, "status": "input_error"}


def _field(value: object, dotted: str) -> object:
    for part in dotted.split("."):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


class CorrectiveAuthorizationReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.reset_repository()

    def reset_repository(self) -> None:
        """Give each scenario a fresh consumer repository and no ledger."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / ".specify").mkdir()
        (self.root / "feature").mkdir()
        shutil.copyfile(FIXTURE_ROOT / "workflow.md", self.root / WORKFLOW)
        self.ledger: dict | None = None
        self.ledger_path: Path | None = None

    def resolve(self, value: object) -> object:
        if isinstance(value, dict):
            return {key: self.resolve(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self.resolve(item) for item in value]
        if not isinstance(value, str) or not value.startswith("$"):
            return value
        if value == "$run_id":
            return self.ledger["run_id"]
        if value == "$spec_file":
            return SPEC
        if value == "$check_command":
            return f"{sys.executable} check.py"
        if value == "$head_sha":
            return subprocess.run(["git", "-C", str(self.root), "rev-parse", "HEAD"], check=True, text=True,
                                  capture_output=True).stdout.strip()
        if value == "$spec_sha256":
            return self.ledger["invariant_binding"]["spec_sha256"]
        if value.startswith("$reservation:"):
            return self.ledger["dispatches"][value.split(":", 1)[1]]["reservation_id"]
        raise AssertionError(f"unknown fixture token {value}")

    def run_runner(self, request: dict) -> tuple[int, dict]:
        environment = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "speckit-pro"),
                       "PYTHONDONTWRITEBYTECODE": "1"}
        completed = subprocess.run(
            [sys.executable, "-B", "-m", "speckit_pro_runner"], cwd=self.root,
            env=environment, input=json.dumps(request), text=True,
            capture_output=True, timeout=60, check=False, shell=False,
        )
        return completed.returncode, json.loads(completed.stdout)

    def send(self, step: dict) -> tuple[int, dict]:
        binding = {"expected_run_id": self.ledger["run_id"]} if self.ledger else {}
        request = {
            "schema_version": "1.0", "helper_id": step.get("helper", "execution-control"),
            "operation": step.get("helper", "execution-control"), "mode": step.get("mode", "apply"),
            "inputs": {"workflow_file": WORKFLOW, "action": step["action"], **binding,
                       **self.resolve(step.get("inputs", {}))},
        }
        return self.run_runner(request)

    def finalize(self, step: dict) -> None:
        """Send the run's end-of-run request through the read-only `finalize-run` helper."""
        inputs = {"ledger_path": self.ledger_path.relative_to(self.root).as_posix(),
                  "expected_run_id": self.ledger["run_id"], **self.resolve(step["finalize"])}
        code, envelope = self.run_runner({
            "schema_version": "1.0", "helper_id": "finalize-run", "operation": "finalize-run",
            "mode": "read_only", "inputs": inputs,
        })
        self.assertEqual((code, envelope["status"]), (0, "ok"), envelope)
        result = envelope["data"]
        for key, expected in step["expect"].get("result", {}).items():
            self.assertEqual(result[key], expected, key)
        for text in step["expect"].get("request_omits", []):
            self.assertNotIn(text, result["end_of_run_request"])

    def place_spec(self, name: str) -> None:
        target = self.root / SPEC
        if name == "absent":
            target.unlink(missing_ok=True)
        else:
            shutil.copyfile(FIXTURE_ROOT / name, target)

    def place_check(self, fixture: str, exit_code: int = 1) -> None:
        """Stage a verification command that prints one captured test-runner output and exits, as the runner would run it."""
        commands = {"UNIT_TEST": f"{sys.executable} check.py"}
        (self.root / WORKFLOW).write_text("# Workflow\n\n## PROJECT_COMMANDS\n```json\n" + json.dumps(commands) + "\n```\n",
                                          encoding="utf-8")
        output = (CHECK_FIXTURES / fixture).read_text(encoding="utf-8")
        (self.root / "check.py").write_text(f"import sys\nsys.stdout.write({output!r})\nsys.exit({exit_code})\n", encoding="utf-8")

    def stage(self, files: dict[str, str]) -> None:
        """Copy frozen fixture files into the consumer repository."""
        for destination, source in files.items():
            target = self.root / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(FIXTURE_ROOT / source, target)

    def git_baseline(self) -> None:
        """Commit the staged files so HEAD holds the task-definition baseline."""
        environment = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        if not (self.root / ".git").exists():
            subprocess.run(["git", "init", "-q", str(self.root)], check=True, env=environment)
        subprocess.run(["git", "-C", str(self.root), "add", "-A"], check=True, env=environment)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=fixture", "-c", "user.email=git@github.com",
                        "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "baseline"],
                       check=True, env=environment)

    def write(self, files: dict[str, str]) -> None:
        for destination, text in files.items():
            (self.root / destination).parent.mkdir(parents=True, exist_ok=True)
            (self.root / destination).write_text(text, encoding="utf-8")

    def check_step(self, step: dict) -> None:
        before_ledger = self.ledger
        before_bytes = self.ledger_path.read_bytes() if self.ledger_path else None
        code, envelope = self.send(step)
        data = envelope.get("data") or {}
        if "refused" in step:
            self.assertEqual({"exit_code": code, "status": envelope["status"]}, REFUSED, envelope)
            diagnostic = envelope["diagnostics"][0]
            self.assertEqual(diagnostic["code"], "invalid_execution_request", envelope)
            self.assertTrue(step["refused"], "a refusal step must name its expected reason")
            self.assertIn(step["refused"], diagnostic["message"])
            self.assertEqual(self.ledger_path.read_bytes(), before_bytes, "a refusal mutated the ledger")
            return
        expect = step["expect"]
        self.assertEqual((code, envelope["status"]), (expect["exit_code"], expect["status"]), envelope)
        for key in ("disposition", "reasons"):
            if key in expect:
                self.assertEqual(data[key], expect[key], envelope)
        for key, expected in expect.get("data", {}).items():
            self.assertEqual(data[key], expected, key)
        if "ledger" not in data:
            return
        ledger = data["ledger"]
        for dotted, expected in expect.get("ledger", {}).items():
            self.assertEqual(_field(ledger, dotted), expected, dotted)
        for key in expect.get("preserves", []):
            self.assertEqual(ledger[key], before_ledger[key], key)
        self.ledger = ledger
        self.ledger_path = self.root / data["ledger_path"]

    def replay(self, names: tuple[str, ...]) -> None:
        for name in names:
            scenario = json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))
            self.assertEqual(scenario["schema"], "corrective-authorization-replay/v1")
            self.reset_repository()
            for step in scenario["steps"]:
                with self.subTest(scenario=name, step=step["id"]):
                    if "place_spec" in step:
                        self.place_spec(step["place_spec"])
                    elif "place_check" in step:
                        self.place_check(step["place_check"], step.get("exit_code", 1))
                    elif "stage" in step:
                        self.stage(step["stage"])
                    elif "write" in step:
                        self.write(step["write"])
                    elif "finalize" in step:
                        self.finalize(step)
                    elif "git" in step:
                        self.assertEqual(step["git"], "baseline")
                        self.git_baseline()
                    else:
                        self.check_step(step)

    def test_fixture_scenarios_replay_against_the_shipped_runner(self) -> None:
        self.replay(SCENARIOS)

    def test_test_runner_output_lets_a_converging_correction_continue_its_family(self) -> None:
        self.replay(CONVERGENCE_SCENARIOS)

    def test_each_scenario_refuses_a_replayed_or_second_approval(self) -> None:
        for name in APPROVAL_SCENARIOS:
            steps = json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))["steps"]
            refused = [step["id"] for step in steps if "refused" in step]
            accepted = [step["id"] for step in steps if step.get("action", "").startswith(
                ("bind-invariants", "authorize-corrective-")) and "expect" in step]
            with self.subTest(scenario=name):
                self.assertTrue(accepted, "a scenario must reach its accepted path")
                self.assertTrue(any(step in refused for step in (
                    "second-bind", "second-retry", "second-continuation", "second-exception")))
                if name != "bind-invariants.json":
                    self.assertIn("replayed-approval", refused)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CorrectiveAuthorizationReplayTests)
    raise SystemExit(run_counted(suite, label="test-corrective-authorization-runner-routes"))
