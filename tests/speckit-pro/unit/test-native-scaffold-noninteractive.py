#!/usr/bin/env python3
"""Provider-free evidence for the non-interactive scaffold diagnostic candidate."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
sys.path.insert(0, str(TEST_ROOT / "lib"))

from native_eval_catalog import validate_catalog  # noqa: E402
from native_eval_fixture_setup import materialize_workspace, snapshot_git_repository_controls  # noqa: E402
from native_eval_git_observation import (  # noqa: E402
    observe_git_state,
    observe_registered_worktrees,
    snapshot_git_topology,
)
from native_eval_grading import grade_observation  # noqa: E402
from test_result import run_counted  # noqa: E402


FIXTURE_ROOT = "tests/speckit-pro/evals/fixtures/functional/scaffold-noninteractive"
ROADMAP = "docs/ai/current-technical-roadmap.md"
DESIGN_CONCEPT = "docs/ai/specs/.process/SPEC-009-design-concept.md"
WORKFLOW = "docs/ai/specs/.process/SPEC-009-workflow.md"
CHILD = ".worktrees/spec-009"
EXPECTED_RESPONSE = {
    "worktrees": [
        {"path": ".", "branch": "feature"},
        {"path": CHILD, "branch": "scenario/spec-009"},
    ],
    "artifact_paths": [],
    "reason": "The earlier automation had no interactive question surface for Grill Me.",
    "next_action": "retry_interactively",
}


def fixture(source: str, destination: str) -> dict[str, str]:
    payload = (REPO_ROOT / source).read_bytes()
    return {
        "source": source,
        "destination": destination,
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def catalog_fixture(source: str, destination: str) -> dict[str, str]:
    return {"source": source, "destination": destination}


def scaffold_case() -> dict[str, object]:
    baseline = f"{FIXTURE_ROOT}/baseline/README.md"
    roadmap = f"{FIXTURE_ROOT}/feature/{ROADMAP}"
    hosts = ("claude", "codex")
    return {
        "id": "functional.speckit-scaffold-spec.case-7",
        "layer": "functional",
        "capability": "Diagnoses an already-stopped non-interactive scaffold from actual retained workspace state without restarting it.",
        "timeout_seconds": 300,
        "resource_class": "ordinary",
        "requirements": [
            {"id": "selection", "description": "The host-native speckit-scaffold-spec capability is activated."},
            {"id": "diagnosis", "description": "The response diagnoses the prior no-TTY Grill Me stop from retained state and directs an interactive retry without restarting setup."},
            {"id": "preservation", "description": "The feature checkout and registered child remain clean and contain no generated design or workflow artifact."},
        ],
        "prompt": (
            "An earlier non-interactive setup attempt for SPEC-009 stopped at the Grill Me step "
            "when its codex exec-style runtime had no TTY. Use {{skill}} only to diagnose why "
            "that earlier attempt stopped and inspect the remaining workspace. Report every "
            "registered worktree using workspace-relative path and attached branch, sorted by "
            "relative path; report any existing "
            "SPEC-009 design-concept or workflow artifact paths, the reason for the stop, and the "
            "next action. Return exactly one JSON object with worktrees, artifact_paths, reason, "
            "and next_action; next_action must be one of retry_interactively or resume_automation. "
            "Do not restart setup, run the interview, create files, branches, "
            "worktrees, or commits, or claim actions from the earlier attempt that retained state "
            "does not prove."
        ),
        "fixtures": [catalog_fixture(roadmap, ROADMAP)],
        "git_fixture": {
            "recipe": "baseline-feature-origin-main/v1",
            "baseline": [catalog_fixture(baseline, "README.md")],
            "worktrees": [{
                "path": CHILD,
                "branch": "scenario/spec-009",
                "revision": "feature",
            }],
        },
        "hosts": {
            "claude": {
                "skill": "speckit-pro:speckit-scaffold-spec",
                "allowed_tools": ["Skill", "Read", "Glob", "Grep", "Bash"],
                "modes": ["plugin"],
            },
            "codex": {
                "skill": "speckit-scaffold-spec",
                "allowed_tools": ["read_file", "list_files", "search_files", "command_execution"],
                "modes": ["project"],
            },
        },
        "checks": [
            {"id": "selection", "requirement": "selection", "type": "selection", "expected": ["speckit-scaffold-spec"], "allowed_extra": []},
            {"id": "reported-worktrees", "requirement": "diagnosis", "type": "response_json_field", "field_path": ["worktrees"], "expected_by_host": {host: copy.deepcopy(EXPECTED_RESPONSE["worktrees"]) for host in hosts}},
            {"id": "reported-artifacts", "requirement": "diagnosis", "type": "response_json_field", "field_path": ["artifact_paths"], "expected_by_host": {host: [] for host in hosts}},
            {"id": "next-action", "requirement": "diagnosis", "type": "response_json_field", "field_path": ["next_action"], "expected_by_host": {host: EXPECTED_RESPONSE["next_action"] for host in hosts}},
            {
                "id": "diagnostic-rubric",
                "requirement": "diagnosis",
                "type": "semantic",
                "rubric": (
                    "PASS only if retained native evidence shows actual inspection of the root and "
                    "registered child worktree plus both possible artifact locations, and the response "
                    "explains all four legacy requirements: Grill Me requires an interactive runtime "
                    "and the earlier no-TTY automation therefore stopped; scaffold is HITL-gated and "
                    "must not synthesize design-concept content; the exact remaining local worktrees "
                    "and empty artifact set are reported; and the user is directed to retry in an "
                    "interactive session. FAIL for a response-only state claim, invented historical "
                    "actions, a restarted interview or scaffold, new work, or any contradicted field."
                ),
            },
            {"id": "no-root-design-concept", "requirement": "preservation", "type": "file_exists", "path": DESIGN_CONCEPT, "exists": False},
            {"id": "no-root-workflow", "requirement": "preservation", "type": "file_exists", "path": WORKFLOW, "exists": False},
            {"id": "no-child-design-concept", "requirement": "preservation", "type": "file_exists", "path": f"{CHILD}/{DESIGN_CONCEPT}", "exists": False},
            {"id": "no-child-workflow", "requirement": "preservation", "type": "file_exists", "path": f"{CHILD}/{WORKFLOW}", "exists": False},
            {
                "id": "preservation-boundary",
                "requirement": "preservation",
                "type": "native_git_final_state",
                "head_equals_initial_feature": True,
                "branch": "feature",
                "commit_count": 0,
                "commits_added": [],
                "changed_tracked_paths_from_initial_feature": [],
                "status": {
                    "clean": True,
                    "tracked_dirty": False,
                    "untracked_dirty": False,
                    "tracked": [],
                    "untracked": [],
                },
                "registered_worktrees_unchanged": True,
            },
        ],
        "native_differences": [
            "Claude uses its plugin Skill surface and Codex uses its project skill; both perform only retained-state diagnosis.",
            "The controller creates the same real feature checkout and registered child worktree for both hosts before the read-only diagnostic.",
            "The historical no-TTY failure is supplied by the request; neither arm reruns or fabricates that earlier attempt.",
        ],
        "provenance": [
            "tests/speckit-pro/layer3-functional/codex-evals/speckit-scaffold-spec-evals.json#eval-7",
            "tests/speckit-pro/evals/fixtures/functional/legacy-selection.json#functional.speckit-scaffold-spec.case-7",
            "speckit-pro/skills/speckit-scaffold-spec/SKILL.md#4",
            "speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md#4",
        ],
    }


def materialization_plan(case: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "native-eval-fixtures/v2",
        "source_root": str(REPO_ROOT),
        "fixtures": [fixture(row["source"], row["destination"]) for row in case["fixtures"]],
        "git_repository": {
            "recipe": case["git_fixture"]["recipe"],
            "baseline": [fixture(row["source"], row["destination"])
                         for row in case["git_fixture"]["baseline"]],
            "worktrees": copy.deepcopy(case["git_fixture"]["worktrees"]),
        },
    }


def grading_case() -> dict[str, object]:
    value = scaffold_case()
    value["checks"] = [
        row for row in value["checks"] if row["type"] != "native_git_final_state"
    ]
    return value


def observation(response: dict[str, object], artifacts: dict[str, str] | None = None) -> dict[str, object]:
    return {
        "completed": True,
        "error": None,
        "final_text": json.dumps(response, sort_keys=True),
        "activations": ["speckit-scaffold-spec"],
        "tool_calls": [],
        "artifacts": artifacts or {},
        "usage": {},
    }


def _skill_variants(skill_name: str) -> list[str]:
    roots = (
        REPO_ROOT / "speckit-pro" / "skills",
        REPO_ROOT / "speckit-pro" / "codex-skills",
    )
    return [(root / skill_name / "SKILL.md").read_text(encoding="utf-8") for root in roots]


class ShippedSkillContractTests(unittest.TestCase):
    def test_shipped_skill_contracts(self) -> None:
        expected = {
            "speckit-autopilot": (
                "deep dives", "populated workflow", "remains an autopilot execution request",
            ),
            "speckit-coach": (
                "`## Progress Tracking` is mandatory",
                "Grill Me never creates a branch, worktree, workflow",
                "A declared extension command is not evidence that a hook runs",
                "`specs/<branch-name>/SPEC-MOC.md`",
                "actual dedicated spec branch",
            ),
            "speckit-status": (
                "This standalone status skill",
                "from beginning to end before answering",
                "another skill's report",
            ),
        }
        for skill_name, needles in expected.items():
            for text in _skill_variants(skill_name):
                compact = " ".join(text.split())
                with self.subTest(skill=skill_name):
                    for needle in needles:
                        self.assertIn(needle, compact)

        for text in _skill_variants("speckit-scaffold-spec"):
            compact, lowered = " ".join(text.split()), text.lower()
            for needle in (
                "Before `git worktree add` or any artifact or roadmap write, invoke the read-only",
                "after worktree creation and again",
                "before bootstrap or Grill Me",
                "immediately before every commit and push",
                "`docs/ai/specs/.process/SPEC-<ID>-workflow.md`",
                "actual dedicated branch",
                "<absolute-workflow-file> --stage plan",
            ):
                self.assertIn(needle, compact)
            self.assertIn("never commit or push", lowered)
            self.assertTrue(
                "human-in-the-loop" in lowered or "strictly interactive" in lowered
            )
            self.assertTrue(
                "do not synthesize design-concept content" in lowered
                or "do not attempt to skip grilling" in lowered
            )


class NativeScaffoldNoninteractiveTests(unittest.TestCase):
    def test_candidate_is_schema_valid_and_remains_an_ordinary_diagnostic(self) -> None:
        catalog = {"schema_version": "native-eval-catalog/v1", "cases": [scaffold_case()]}
        accepted = validate_catalog(catalog, REPO_ROOT)["cases"][0]
        self.assertEqual(accepted["resource_class"], "ordinary")
        self.assertEqual(accepted["git_fixture"]["worktrees"], [{
            "path": CHILD, "branch": "scenario/spec-009", "revision": "feature",
        }])
        self.assertFalse(any(row["type"] == "native_subagent_dispatch" for row in accepted["checks"]))

    def test_real_materialization_proves_exact_root_and_registered_child_state(self) -> None:
        case = scaffold_case()
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            workspace.mkdir()
            result = materialize_workspace(materialization_plan(case), workspace)
            exclusion = workspace / ".git" / "info" / "exclude"
            exclusion.parent.mkdir(exist_ok=True)
            exclusion.write_text(f"/{CHILD}/\n", encoding="utf-8")
            controls = snapshot_git_repository_controls(workspace)

            topology = snapshot_git_topology(
                workspace, controls, result["git_repository"],
            )
            self.assertEqual(
                [(row["path"], row["branch"]) for row in topology["worktrees"]],
                [(".", "feature"), (CHILD, "scenario/spec-009")],
            )
            self.assertTrue(all(
                row["head"] == result["git_repository"]["feature_commit"]
                for row in topology["worktrees"]
            ))
            registered = observe_registered_worktrees(
                workspace, controls, result["git_repository"], result["worktrees"],
            )
            self.assertEqual(
                registered["worktrees"][0]["initial"],
                {"path": CHILD, "branch": "scenario/spec-009", "revision": "feature",
                 "head": result["git_repository"]["feature_commit"], "clean": True},
            )
            self.assertTrue(registered["worktrees"][0]["status"]["clean"])
            self.assertTrue(observe_git_state(
                workspace, controls, result["git_repository"],
            )["status"]["clean"])
            for root in (workspace, workspace / CHILD):
                self.assertIn("SPEC-009", (root / ROADMAP).read_text(encoding="utf-8"))
                self.assertFalse((root / DESIGN_CONCEPT).exists())
                self.assertFalse((root / WORKFLOW).exists())

    def test_each_wrong_report_field_fails_even_with_positive_semantic_judgment(self) -> None:
        case = grading_case()
        semantic = {"diagnostic-rubric": {"passed": True, "evidence": ["positive-control"]}}
        variants = {
            "reported-worktrees": {**EXPECTED_RESPONSE, "worktrees": [
                {"path": ".", "branch": "feature"},
                {"path": CHILD, "branch": "wrong"},
            ]},
            "reported-artifacts": {**EXPECTED_RESPONSE, "artifact_paths": [DESIGN_CONCEPT]},
            "next-action": {**EXPECTED_RESPONSE, "next_action": "restart_automatically"},
        }
        for host in ("claude", "codex"):
            self.assertEqual(
                grade_observation(case, observation(EXPECTED_RESPONSE), semantic, host=host)["status"],
                "pass",
            )
            for check_id, response in variants.items():
                with self.subTest(host=host, check_id=check_id):
                    result = grade_observation(case, observation(response), semantic, host=host)
                    self.assertEqual(result["status"], "fail")
                    self.assertEqual(
                        next(row for row in result["checks"] if row["id"] == check_id)["verdict"],
                        "fail",
                    )

    def test_fabricated_artifacts_in_root_or_child_fail_both_hosts(self) -> None:
        case = grading_case()
        semantic = {"diagnostic-rubric": {"passed": True, "evidence": ["positive-control"]}}
        paths = (DESIGN_CONCEPT, WORKFLOW, f"{CHILD}/{DESIGN_CONCEPT}", f"{CHILD}/{WORKFLOW}")
        for host in ("claude", "codex"):
            for path in paths:
                with self.subTest(host=host, path=path):
                    result = grade_observation(
                        case, observation(EXPECTED_RESPONSE, {path: "invented"}), semantic, host=host,
                    )
                    self.assertEqual(result["status"], "fail")

    def test_subject_fixture_contains_no_grading_answer_or_generated_output(self) -> None:
        subject_bytes = b"\n".join(
            path.read_bytes() for path in (REPO_ROOT / FIXTURE_ROOT).rglob("*") if path.is_file()
        ).lower()
        for forbidden in (
            b"retry_interactively", b"human-in-the-loop", b"grill-me",
            b"design-concept.md", b"workflow.md", b"scenario/spec-009",
        ):
            self.assertNotIn(forbidden, subject_bytes)


if __name__ == "__main__":
    suite = unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromTestCase(ShippedSkillContractTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeScaffoldNoninteractiveTests),
    ])
    raise SystemExit(run_counted(suite, label="test-native-scaffold-noninteractive"))
