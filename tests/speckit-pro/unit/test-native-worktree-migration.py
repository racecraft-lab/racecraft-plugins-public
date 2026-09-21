#!/usr/bin/env python3
"""Provider-free evidence for the registered-worktree migration proposal."""

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

from native_eval_catalog import validate_catalog  # noqa: E402
from native_eval_fixture_setup import materialize_workspace, snapshot_git_repository_controls  # noqa: E402
from native_eval_git_observation import observe_git_state, observe_registered_worktrees  # noqa: E402
from native_eval_grading import grade_observation  # noqa: E402
from test_result import run_counted  # noqa: E402


FIXTURE_ROOT = "tests/speckit-pro/evals/fixtures/functional/registered-worktree-migration"
WORKFLOW = "docs/ai/specs/.process/SPEC-107-workflow.md"
REQUEST_SOURCE = f"{FIXTURE_ROOT}/ambiguous/binding-request.json"


def fixture(source: str, destination: str) -> dict[str, str]:
    payload = (REPO_ROOT / source).read_bytes()
    return {"source": source, "destination": destination, "sha256": hashlib.sha256(payload).hexdigest()}


def ambiguity_case() -> dict[str, object]:
    baseline = f"{FIXTURE_ROOT}/ambiguous/baseline/{WORKFLOW}"
    feature = f"{FIXTURE_ROOT}/ambiguous/feature/{WORKFLOW}"
    return {
        "id": "functional.speckit-autopilot.case-107",
        "layer": "functional",
        "capability": "Stops on an ambiguous relative workflow path across a real registered descendant worktree.",
        "timeout_seconds": 300,
        "resource_class": "ordinary",
        "required_tools": ["specify"],
        "requirements": [
            {"id": "selection", "description": "The native host activates speckit-autopilot."},
            {"id": "binding", "description": "An ambiguous relative workflow binding stops before workflow reads or mutation, lists both canonical candidates, and requests an unambiguous absolute workflow path."},
            {"id": "preservation", "description": "The prepared feature checkout and registered child worktree remain unchanged after the stopped run."},
        ],
        "prompt": "Use {{skill}} for workflow docs/ai/specs/.process/SPEC-107-workflow.md. Complete its workflow-binding preflight with the protected installed runner using exactly {{resolved_python}} -m speckit_pro_runner < scenario-inputs/binding-request.json. Run that invocation as one default-shell command with no shell variable, prefix, suffix, pipe, or output redirection other than the required input redirection; use the command result as the response evidence. Interpret its returned status, including an expected-failure exit, rather than replacing its response. Output only raw JSON: exactly one top-level object with binding_result (the complete actual helper response), decision (proceed or stop), candidates (canonical worktree roots), and next_action (continue_workflow or provide_absolute_workflow_path), with no diagnostic prefix, prose, Markdown, or code fences. Stop at the preflight decision; do not start later workflow phases.",
        "fixtures": [
            {"source": feature, "destination": WORKFLOW},
            {"source": REQUEST_SOURCE, "destination": "scenario-inputs/binding-request.json"},
        ],
        "git_fixture": {
            "recipe": "baseline-feature-origin-main/v1",
            "baseline": [
                {"source": baseline, "destination": WORKFLOW},
                {"source": "tests/speckit-pro/evals/fixtures/functional/autopilot-scenarios/common/project.json", "destination": ".specify/project.json"},
            ],
            "worktrees": [{"path": ".worktrees/ambiguous", "branch": "scenario/ambiguous", "revision": "baseline"}],
        },
        "hosts": {
            "claude": {"skill": "speckit-pro:speckit-autopilot", "allowed_tools": ["Skill", "Read", "Glob", "Grep", "Bash"], "modes": ["plugin"]},
            "codex": {"skill": "speckit-autopilot", "allowed_tools": ["read_file", "list_files", "search_files", "command_execution"], "modes": ["project"]},
        },
        "checks": [
            {"id": "selection", "requirement": "selection", "type": "selection", "expected": ["speckit-autopilot"], "allowed_extra": []},
            {"id": "native-binding-result", "requirement": "binding", "type": "native_runner_result", "request_path": "scenario-inputs/binding-request.json", "helper_id": "resolve-workflow-binding", "operation": "resolve-workflow-binding", "mode": "read_only", "expected_status": "expected_failure", "expected_exit_code": 1, "stdout_field_path": ["binding_status"], "expected_stdout_value": "ambiguous", "response_field_path": ["binding_result"]},
            {"id": "reported-binding-status", "requirement": "binding", "type": "response_json_field", "field_path": ["binding_result", "data", "stdout_json", "binding_status"], "expected_by_host": {"claude": "ambiguous", "codex": "ambiguous"}},
            {"id": "decision", "requirement": "binding", "type": "response_json_field", "field_path": ["decision"], "expected_by_host": {"claude": "stop", "codex": "stop"}},
            {"id": "next-action", "requirement": "binding", "type": "response_json_field", "field_path": ["next_action"], "expected_by_host": {"claude": "provide_absolute_workflow_path", "codex": "provide_absolute_workflow_path"}},
            {"id": "binding-rubric", "requirement": "binding", "type": "semantic", "rubric": "PASS only if the subject lists both actual canonical candidates and stops without reading workflow content, choosing either candidate, invoking Archive Sweep, dispatching a phase, updating state, or mutating Git, and requests an absolute workflow path. FAIL for an omitted candidate or any contradicted stop boundary. The separate native-binding-result check is authoritative for the real runner response; semantic grading cannot replace it or waive a failure."},
            {"id": "preservation-boundary", "requirement": "preservation", "type": "native_git_final_state", "head_equals_initial_feature": True, "branch": "feature", "commit_count": 0, "commits_added": [], "changed_tracked_paths_from_initial_feature": [], "status": {"clean": True, "tracked_dirty": False, "untracked_dirty": False, "tracked": [], "untracked": []}, "registered_worktrees_unchanged": True},
        ],
        "native_differences": [
            "The host-native skill mechanisms normalize to the same canonical activation name.",
            "Both hosts receive one controller-created real confined descendant worktree; no copied directory is treated as registration evidence.",
            "No plugin-host legacy row exists for eval 107; its host arm is a parity addition and does not replace the Codex legacy mapping.",
        ],
        "provenance": ["tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json#eval-107"],
    }


class NativeWorktreeMigrationTests(unittest.TestCase):
    def grade_preservation(self, workspace: Path, result: dict[str, object]) -> str:
        controls = snapshot_git_repository_controls(workspace)
        observed = observe_git_state(workspace, controls, result["git_repository"])
        observed["registered_worktrees"] = observe_registered_worktrees(
            workspace, controls, result["git_repository"], result["worktrees"],
        )
        payload = json.dumps(observed, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode() + b"\n"
        evidence = {"completed": True, "error": None, "final_text": "{}",
                    "activations": [], "tool_calls": [], "artifacts": {}, "usage": {},
                    "native_metadata": {"controller_git_observation": {
                        "schema": "native-eval-controller-git-observation/v1", "authority": "controller",
                        "observation": observed, "evidence": {"path": "raw-git.json",
                        "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)},
                    }}}
        case = ambiguity_case()
        case["requirements"] = [row for row in case["requirements"] if row["id"] == "preservation"]
        case["checks"] = [row for row in case["checks"] if row["requirement"] == "preservation"]
        verdicts = [grade_observation(case, evidence, host=host)["status"] for host in ("claude", "codex")]
        self.assertEqual(verdicts[0], verdicts[1])
        return verdicts[0]

    def run_binding(self, workspace: Path) -> dict[str, object]:
        environment = {
            **os.environ, "PYTHONPATH": str(REPO_ROOT / "speckit-pro"),
            "PYTHONSAFEPATH": "1", "PYTHONDONTWRITEBYTECODE": "1",
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
        }
        request = (REPO_ROOT / REQUEST_SOURCE).read_text(encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, "-B", "-m", "speckit_pro_runner"], cwd=workspace,
            env=environment, input=request, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=30, check=False,
        )
        self.assertIn(completed.returncode, {0, 1}, completed.stderr)
        envelope = json.loads(completed.stdout)
        self.assertEqual(envelope["request_id"], "workflow-binding-preflight")
        expected_request = json.loads(request)
        expected_request.pop("request_id")
        self.assertEqual(envelope["data"]["stdin_request"], expected_request)
        return {"exit_code": completed.returncode,
                "stdout": json.dumps(envelope["data"]["stdout_json"])}

    def test_ambiguity_candidate_is_schema_valid(self) -> None:
        catalog = {"schema_version": "native-eval-catalog/v1", "cases": [ambiguity_case()]}
        accepted = validate_catalog(catalog, REPO_ROOT)["cases"][0]
        self.assertEqual(accepted["git_fixture"]["worktrees"][0]["path"], ".worktrees/ambiguous")

    def test_real_materialization_exposes_distinct_parent_and_registered_candidates(self) -> None:
        case = ambiguity_case()
        plan = {
            "schema_version": "native-eval-fixtures/v2",
            "source_root": str(REPO_ROOT),
            "fixtures": [fixture(row["source"], row["destination"]) for row in case["fixtures"]],
            "git_repository": {
                "recipe": case["git_fixture"]["recipe"],
                "baseline": [fixture(row["source"], row["destination"]) for row in case["git_fixture"]["baseline"]],
                "worktrees": case["git_fixture"]["worktrees"],
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            workspace.mkdir()
            result = materialize_workspace(plan, workspace)
            child = workspace / ".worktrees/ambiguous"
            self.assertIn("Registered Worktree", (workspace / WORKFLOW).read_text(encoding="utf-8"))
            self.assertIn("Parent Workflow", (child / WORKFLOW).read_text(encoding="utf-8"))
            observed = observe_registered_worktrees(
                workspace, snapshot_git_repository_controls(workspace), result["git_repository"], result["worktrees"],
            )
            self.assertEqual(observed["worktrees"][0]["initial"]["path"], ".worktrees/ambiguous")
            self.assertTrue(observed["worktrees"][0]["status"]["clean"])
            self.assertEqual(self.grade_preservation(workspace, result), "pass")
            binding = self.run_binding(workspace)
            self.assertEqual(binding["exit_code"], 1)
            payload = json.loads(binding["stdout"])
            self.assertEqual(payload["binding_status"], "ambiguous")
            self.assertEqual(set(payload["candidates"]), {
                str(workspace.resolve()), str(child.resolve()),
            })

            # Removing either candidate must change the actual helper outcome;
            # registration or a copied filename alone cannot prove ambiguity.
            child_workflow = child / WORKFLOW
            child_bytes = child_workflow.read_bytes()
            child_workflow.unlink()
            self.assertEqual(self.grade_preservation(workspace, result), "fail")
            same = self.run_binding(workspace)
            self.assertEqual(same["exit_code"], 0)
            self.assertEqual(json.loads(same["stdout"])["relation"], "same")
            child_workflow.write_bytes(child_bytes)
            (workspace / WORKFLOW).unlink()
            descendant = self.run_binding(workspace)
            self.assertEqual(descendant["exit_code"], 0)
            self.assertEqual(json.loads(descendant["stdout"])["relation"], "descendant")

    def test_current_contract_rejects_external_and_temporal_revalidation_shapes(self) -> None:
        external = ambiguity_case()
        external["git_fixture"]["worktrees"][0]["path"] = "../external"
        with self.assertRaisesRegex(ValueError, "confined .worktrees child"):
            validate_catalog({"schema_version": "native-eval-catalog/v1", "cases": [external]}, REPO_ROOT)
        temporal = ambiguity_case()
        temporal["git_fixture"]["revalidation"] = {"before": "artifact-author"}
        with self.assertRaisesRegex(ValueError, "malformed git_fixture"):
            validate_catalog({"schema_version": "native-eval-catalog/v1", "cases": [temporal]}, REPO_ROOT)
        undeclared = ambiguity_case()
        del undeclared["git_fixture"]["worktrees"]
        with self.assertRaisesRegex(ValueError, "preservation requires declared worktrees"):
            validate_catalog({"schema_version": "native-eval-catalog/v1", "cases": [undeclared]}, REPO_ROOT)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeWorktreeMigrationTests)
    raise SystemExit(run_counted(suite, label="test-native-worktree-migration"))
