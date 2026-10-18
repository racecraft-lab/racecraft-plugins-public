"""Shared fixture and runner support for the planning helper tests."""

import tempfile
import unittest
from pathlib import Path

from git_fixture import git
from runner_invocation import run_runner


class PlanningHelperFixture(unittest.TestCase):
    feature_dir = "specs/demo"
    workflow_name = "workflow.md"
    workflow_text = "## Project Commands\n"
    runner_root = Path(__file__).resolve().parents[3] / "speckit-pro"

    @property
    def workflow_file(self):
        return (Path(self.feature_dir) / self.workflow_name).as_posix()

    def helper_inputs(self, **inputs):
        return dict(feature_dir=self.feature_dir, workflow_file=self.workflow_file, **inputs)

    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        git(self.root, "init", "--quiet")
        (self.root / ".specify").mkdir()
        self.feature = self.root / self.feature_dir
        self.feature.mkdir(parents=True)
        for name, text in {
            "spec.md": "A feature",
            "plan.md": "A plan",
            "tasks.md": "- [ ] T001 Build a thing",
            self.workflow_name: self.workflow_text,
        }.items():
            (self.feature / name).write_text(text)

    def run_helper(self, helper_id, inputs, mode="read_only"):
        request = dict(schema_version="1.0", helper_id=helper_id, operation=helper_id,
                       mode=mode, inputs=inputs)
        _, reply, _ = run_runner(request, cwd=self.root, extra_env={"PYTHONPATH": str(self.runner_root)})
        return reply

    def assertRefused(self, reply, reason):
        self.assertEqual(reply["status"], "input_error", reply)
        self.assertIn(reason, reply["diagnostics"][0]["message"])
