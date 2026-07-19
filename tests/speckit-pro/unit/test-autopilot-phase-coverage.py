#!/usr/bin/env python3
"""Regression tests for autopilot canonical phase coverage validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "scripts" / "validate-autopilot-phase-coverage.py"
REPORT_SCHEMA = (
    REPO_ROOT
    / "tests"
    / "speckit-pro"
    / "unit"
    / "fixtures"
    / "mutation-helpers"
    / "contracts"
    / "autopilot-phase-coverage-report.schema.json"
)

POST_STEPS = [
    "Post: Doctor Extension Check",
    "Post: Verify Implementation",
    "Post: Verify Tasks Phantom Check",
    "Post: Code Review",
    "Post: Integration Suite",
    "Post: Reviewability Diff Gate",
    "Post: Self-Review",
    "Post: UAT Runbook Generation",
    "Post: PR Body Generation",
    "Post: PR Creation",
    "Post: Review Remediation",
    "Post: Retrospective",
]


def workflow_text(*, include_confidence: bool = True, include_post_table: bool = True) -> str:
    confidence_row = (
        "| Confidence Gate | G6.5 | Pending | Run the pre-implementation confidence gate after Analyze and before task execution |\n"
        if include_confidence
        else ""
    )
    confidence_gate = (
        "| G6.5 | After Analyze Consensus | Pre-implementation confidence gate records pass, advisory no-data, or advisory fail disposition before implementation begins |\n"
        if include_confidence
        else ""
    )
    confidence_section = (
        "\n## Phase 6.5: Confidence Gate\n\n"
        "### Confidence Gate Command\n\n"
        "```text\n"
        "python3 speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py --workflow docs/ai/specs/.process/SPEC-workflow.md --state docs/ai/specs/.process/autopilot-state.json\n"
        "```\n"
        if include_confidence
        else ""
    )
    post_rows = "\n".join(f"| {post} | Pending | Pending |" for post in POST_STEPS)
    post_table = (
        "\n| Item | Status | Evidence |\n|---|---|---|\n" + post_rows + "\n"
        if include_post_table
        else ""
    )
    return (
        "# SPEC Workflow\n\n"
        "## Workflow Overview\n\n"
        "| Phase | Command | Status | Notes |\n"
        "|---|---|---|---|\n"
        "| Specify | `$speckit-specify` | Pending | Pending |\n"
        "| Clarify | `$speckit-clarify` | Pending | Pending |\n"
        "| Plan | `$speckit-plan` | Pending | Pending |\n"
        "| Checklist | `$speckit-checklist` | Pending | Pending |\n"
        "| Tasks | `$speckit-tasks` | Pending | Pending |\n"
        "| Analyze | `$speckit-analyze` | Pending | Pending |\n"
        f"{confidence_row}"
        "| Implement | `$speckit-implement` | Pending | Pending |\n"
        "| Post | Autopilot post-implementation items | Pending | Pending |\n\n"
        "### Phase Gates\n\n"
        "| Gate | Checkpoint | Approval Criteria |\n"
        "|---|---|---|\n"
        "| G1 | After Specify | Pending |\n"
        "| G2 | After Clarify | Pending |\n"
        "| G3 | After Plan | Pending |\n"
        "| G4 | After Checklist | Pending |\n"
        "| G5 | After Tasks | Pending |\n"
        "| G6 | After Analyze | Pending |\n"
        f"{confidence_gate}"
        "| G7 | After Implementation | Pending |\n\n"
        "## Phase 1: Specify\n\n"
        "## Phase 2: Clarify\n\n"
        "## Phase 3: Plan\n\n"
        "## Phase 4: Domain Checklists\n\n"
        "## Phase 5: Tasks\n\n"
        "## Phase 6: Analyze\n"
        f"{confidence_section}\n"
        "## Phase 7: Implement\n\n"
        "## Post-Implementation Checklist\n"
        f"{post_table}"
    )


def state_json(*, include_confidence: bool = True, include_post: bool = True, collapsed: bool = False) -> dict[str, object]:
    if collapsed:
        plan = [
            {"step": "Phase 0: Prerequisites", "status": "completed"},
            {"step": "Phase 1: Specify", "status": "completed"},
            {"step": "Phase 2: Clarify", "status": "completed"},
            {"step": "Phase 3: Plan", "status": "pending"},
            {"step": "Phase 4: Tasks", "status": "pending"},
            {"step": "Phase 5: Implement tasks", "status": "pending"},
        ]
    else:
        plan = [
            {"step": "Archive Sweep: previously merged specs dry-run/apply eligibility", "status": "completed"},
            {"step": "Phase 0: Prerequisites", "status": "completed"},
            {"step": "Phase 1: Specify", "status": "completed"},
            {"step": "Phase 2: Clarify - Session 1", "status": "completed"},
            {"step": "Phase 2: Clarify - Session 1 Consensus", "status": "completed"},
            {"step": "Phase 3: Plan", "status": "pending"},
            {"step": "Phase 4: Checklist - Integration", "status": "pending"},
            {"step": "Phase 4: Checklist - Integration Consensus", "status": "pending"},
            {"step": "Phase 5: Tasks", "status": "pending"},
            {"step": "Phase 6: Analyze", "status": "pending"},
            {"step": "Phase 6: Analyze - Consensus", "status": "pending"},
        ]
        if include_confidence:
            plan.append({"step": "Phase 6.5: Confidence Gate", "status": "pending"})
        plan.append({"step": "Phase 7: Implement - Pending task decomposition", "status": "pending"})
        if include_post:
            plan.extend({"step": post, "status": "pending"} for post in POST_STEPS)
    return {
        "workflow_file": "docs/ai/specs/.process/SPEC-workflow.md",
        "feature_dir": "specs/spec-example",
        "active_step": "Phase 3: Plan",
        "plan": plan,
    }


class AutopilotPhaseCoverageTests(unittest.TestCase):
    def run_validator(self, workflow: str, state: dict[str, object] | str) -> tuple[int, dict[str, object]]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow_path = root / "workflow.md"
            state_path = root / "autopilot-state.json"
            workflow_path.write_text(workflow, encoding="utf-8")
            if isinstance(state, str):
                state_path.write_text(state, encoding="utf-8")
            else:
                state_path.write_text(json.dumps(state), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(VALIDATOR), "--workflow", str(workflow_path), "--state", str(state_path)],
                text=True,
                capture_output=True,
                shell=False,
                check=False,
            )
            self.assertEqual(completed.stderr, "")
            return completed.returncode, json.loads(completed.stdout)

    def projected_state(
        self,
        *,
        plan_status: str,
        phase_status: str,
        checkpoint: dict[str, object],
        emission: dict[str, object] | None = None,
        phase_fields: dict[str, object] | None = None,
    ) -> dict[str, object]:
        state = state_json()
        phase_name = "Phase 7: Implement - Pending task decomposition"
        phase_step = next(item for item in state["plan"] if item["step"] == phase_name)
        phase_step["status"] = plan_status
        state["phase_results"] = {
            phase_name: {
                "status": phase_status,
                "marker_id": "us1",
                **(phase_fields or {}),
            }
        }
        state["pr_marker_plan"] = {
            "markers": [
                {
                    "id": "us1",
                    "implementation_checkpoint": checkpoint,
                    "emission_mapping": emission or {"status": "pending"},
                }
            ]
        }
        return state

    def test_complete_workflow_and_state_pass(self) -> None:
        exit_code, report = self.run_validator(workflow_text(), state_json())
        self.assertEqual(exit_code, 0)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["missing_state_post_items"], [])

    def test_completed_phase_rejects_pending_verification_fields(self) -> None:
        state = self.projected_state(
            plan_status="completed",
            phase_status="completed",
            checkpoint={
                "status": "complete",
                "evidence_path": "specs/spec-example/.process/checkpoints/us1.json",
                "commit_sha": "a" * 40,
            },
            phase_fields={"focused_tests": "pending exact-head verification"},
        )
        exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(exit_code, 1)
        self.assertEqual(
            report["completed_phase_pending_fields"],
            ["phase_results.Phase 7: Implement - Pending task decomposition.focused_tests"],
        )

    def test_plan_phase_and_checkpoint_statuses_must_agree(self) -> None:
        state = self.projected_state(
            plan_status="completed",
            phase_status="in_progress",
            checkpoint={
                "status": "complete",
                "evidence_path": "specs/spec-example/.process/checkpoints/us1.json",
                "commit_sha": "b" * 40,
            },
        )
        exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(exit_code, 1)
        self.assertEqual(len(report["projection_status_errors"]), 2)

    def test_complete_checkpoint_requires_evidence_and_commit(self) -> None:
        state = self.projected_state(
            plan_status="completed",
            phase_status="completed",
            checkpoint={"status": "complete"},
        )
        exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(exit_code, 1)
        self.assertEqual(
            report["checkpoint_evidence_errors"],
            [
                "pr_marker_plan.markers[0].implementation_checkpoint.evidence_path",
                "pr_marker_plan.markers[0].implementation_checkpoint.commit_sha",
            ],
        )

    def test_emitted_mapping_requires_packet_and_pr_identity(self) -> None:
        state = self.projected_state(
            plan_status="in_progress",
            phase_status="in_progress",
            checkpoint={"status": "pending"},
            emission={"status": "emitted"},
        )
        exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(exit_code, 1)
        self.assertEqual(
            report["emission_mapping_errors"],
            [
                "pr_marker_plan.markers[0].emission_mapping.packet_path",
                "pr_marker_plan.markers[0].emission_mapping.pr_number",
                "pr_marker_plan.markers[0].emission_mapping.pr_url",
            ],
        )

    def test_missing_confidence_gate_in_workflow_fails(self) -> None:
        exit_code, report = self.run_validator(workflow_text(include_confidence=False), state_json())
        self.assertEqual(exit_code, 1)
        self.assertEqual(report["status"], "fail")
        self.assertIn("## Phase 6.5:", report["missing_workflow_sections"])
        self.assertIn("| Confidence Gate | G6.5 |", report["missing_workflow_tokens"])

    def test_missing_confidence_gate_in_state_fails(self) -> None:
        exit_code, report = self.run_validator(workflow_text(), state_json(include_confidence=False))
        self.assertEqual(exit_code, 1)
        self.assertEqual(report["status"], "fail")
        self.assertIn("Phase 6.5: Confidence Gate", report["missing_state_prefixes"])

    def test_missing_post_items_in_state_fails(self) -> None:
        exit_code, report = self.run_validator(workflow_text(), state_json(include_post=False))
        self.assertEqual(exit_code, 1)
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["missing_state_post_items"], POST_STEPS)

    def test_collapsed_later_phase_plan_fails(self) -> None:
        exit_code, report = self.run_validator(workflow_text(), state_json(collapsed=True))
        self.assertEqual(exit_code, 1)
        self.assertEqual(report["status"], "fail")
        self.assertIn("Phase 6.5: Confidence Gate", report["missing_state_prefixes"])
        self.assertEqual(report["missing_state_post_items"], POST_STEPS)

    def test_mislabeled_numbered_phases_fail_even_when_prefix_numbers_exist(self) -> None:
        state = state_json()
        state["plan"] = [
            {"step": "Archive Sweep: previously merged specs dry-run/apply eligibility", "status": "completed"},
            {"step": "Phase 0: Prerequisites", "status": "completed"},
            {"step": "Phase 1: Specify", "status": "completed"},
            {"step": "Phase 2: Clarify - Session 1", "status": "completed"},
            {"step": "Phase 3: Plan", "status": "pending"},
            {"step": "Phase 4: Tasks", "status": "pending"},
            {"step": "Phase 5: Implement tasks", "status": "pending"},
            {"step": "Phase 6: Analyze", "status": "pending"},
            {"step": "Phase 6.5: Confidence Gate", "status": "pending"},
            {"step": "Phase 7: Implement - Pending task decomposition", "status": "pending"},
            *({"step": post, "status": "pending"} for post in POST_STEPS),
        ]
        exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(exit_code, 1)
        self.assertEqual(report["status"], "fail")
        self.assertIn("Phase 4: Checklist", report["missing_state_prefixes"])
        self.assertIn("Phase 5: Tasks", report["missing_state_prefixes"])

    def test_malformed_state_is_input_error(self) -> None:
        exit_code, report = self.run_validator(workflow_text(), "{")
        self.assertEqual(exit_code, 2)
        self.assertEqual(report["status"], "input_error")
        self.assertEqual(report["code"], "input_error")
        self.assertIn("invalid state JSON", report["message"])

    def test_report_schema_allows_input_error_without_plan_fields(self) -> None:
        schema = json.loads(REPORT_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["required"], ["status"])
        input_error_branch = schema["allOf"][1]["then"]["required"]
        self.assertEqual(input_error_branch, ["code", "message"])
        exit_code, report = self.run_validator(workflow_text(), "{")
        self.assertEqual(exit_code, 2)
        for required in input_error_branch:
            self.assertIn(required, report)
        self.assertNotIn("workflow_file", report)
        self.assertNotIn("plan_step_count", report)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AutopilotPhaseCoverageTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed
    print(f"test-autopilot-phase-coverage: {passed}/{total} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
