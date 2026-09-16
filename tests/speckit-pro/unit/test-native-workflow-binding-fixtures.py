#!/usr/bin/env python3
"""Prove evaluation worktree fixtures exercise the real workflow-binding helper."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
sys.path.insert(0, str(TEST_ROOT / "lib"))

from native_eval_fixture_setup import materialize_workspace  # noqa: E402
from test_result import run_counted  # noqa: E402

WORKFLOW = "docs/ai/specs/.process/SPEC-025-workflow.md"


class WorkflowBindingFixtureTests(unittest.TestCase):
    def test_real_runner_distinguishes_all_declared_binding_relations(self) -> None:
        fixtures = TEST_ROOT / "evals" / "fixtures" / "functional"
        def record(source: str, destination: str) -> dict[str, str]:
            payload = (fixtures / source).read_bytes()
            return {"source": source, "destination": destination,
                    "sha256": hashlib.sha256(payload).hexdigest()}

        plan = {
            "schema_version": "native-eval-fixtures/v2", "source_root": str(fixtures),
            "fixtures": [record("coach-redirect/workflow.md", WORKFLOW)],
            "git_repository": {
                "recipe": "baseline-feature-origin-main/v1",
                "baseline": [record("autopilot-scenarios/common/project.json", ".specify/project.json")],
                "worktrees": [
                    {"path": ".worktrees/task", "branch": "scenario/task", "revision": "baseline"},
                    {"path": ".worktrees/feature", "branch": "scenario/feature", "revision": "feature"},
                ],
            },
        }
        with tempfile.TemporaryDirectory(prefix="native-binding-fixture-") as temporary:
            workspace = Path(temporary).resolve()
            materialize_workspace(plan, workspace)
            task = workspace / ".worktrees/task"
            feature = workspace / ".worktrees/feature"
            original = (workspace / WORKFLOW).read_bytes()
            environment = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "speckit-pro"),
                           "PYTHONDONTWRITEBYTECODE": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                           "GIT_CONFIG_NOSYSTEM": "1"}
            scenarios = (
                ("same", workspace, str(workspace / WORKFLOW), "resolved", workspace, 0),
                ("descendant", workspace, str(feature / WORKFLOW), "resolved", feature, 0),
                ("external", task, str(feature / WORKFLOW), "resolved", feature, 0),
                ("ambiguous", workspace, WORKFLOW, "ambiguous", None, 1),
            )
            for relation, cwd, path, status, owner, code in scenarios:
                with self.subTest(relation=relation):
                    request = {"schema_version": "1.0", "request_id": "native-binding-fixture",
                               "helper_id": "resolve-workflow-binding", "operation": "resolve-workflow-binding",
                               "mode": "read_only", "inputs": {"workflow_file": path}}
                    completed = subprocess.run(
                        [sys.executable, "-B", "-m", "speckit_pro_runner"], cwd=cwd,
                        env=environment, input=json.dumps(request), text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False,
                    )
                    self.assertEqual(completed.returncode, code, completed.stderr)
                    envelope = json.loads(completed.stdout)
                    result = envelope["data"]["stdout_json"]
                    self.assertEqual(result["binding_status"], status)
                    self.assertEqual(result["task_root"], str(cwd))
                    if owner is not None:
                        self.assertEqual(result["relation"], relation)
                        self.assertEqual(result["workflow_root"], str(owner))
                        self.assertEqual(result["workflow_file"], str(owner / WORKFLOW))
                    else:
                        self.assertEqual(set(result["candidates"]), {str(workspace), str(feature)})
                    self.assertEqual((workspace / WORKFLOW).read_bytes(), original)
                    self.assertEqual((feature / WORKFLOW).read_bytes(), original)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(
        WorkflowBindingFixtureTests), label="test-native-workflow-binding-fixtures"))
