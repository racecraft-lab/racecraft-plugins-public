#!/usr/bin/env python3
"""Regression tests for autopilot canonical phase coverage validation."""

from __future__ import annotations

import hashlib
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
    def run_validator_paths(self, workflow_path: Path, state_path: Path) -> tuple[int, dict[str, object]]:
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR), "--workflow", str(workflow_path), "--state", str(state_path)],
            text=True,
            capture_output=True,
            shell=False,
            check=False,
        )
        self.assertEqual(completed.stderr, "")
        return completed.returncode, json.loads(completed.stdout)

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
            return self.run_validator_paths(workflow_path, state_path)

    @staticmethod
    def complete_checkpoint(*, commit_sha: str = "a" * 40) -> dict[str, object]:
        return {
            "status": "complete",
            "evidence_path": "specs/spec-example/.process/checkpoints/us1.json",
            "checkpoint_evidence_sha": "sha256:" + "a" * 64,
            "checkpoint_evidence_commit_sha": commit_sha,
            "verification_evidence_path": "docs/ai/specs/.process/SPEC-workflow.md",
            "commit_sha": commit_sha,
            "head_sha": commit_sha,
            "completed_at": "2026-07-19T00:00:00Z",
            "completed_task_ids": ["T001"],
            "summary": "Implemented marker us1.",
            "validation": ["focused tests passed"],
            "freshness": {
                "source_fingerprint_status": "current_marker_scope",
                "source_fingerprint_contract": "marker-task-lines.v2",
                "tasks_sha_scope": "checkpoint_time_whole_file",
                "current_tasks_sha": "sha256:" + "b" * 64,
                "checkpoint_marker_tasks_sha": "sha256:" + "c" * 64,
                "current_marker_tasks_sha": "sha256:" + "c" * 64,
                "validated_at": "2026-07-19T00:00:00Z",
            },
        }

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
            "schema_version": "pr-marker-plan.v2",
            "markers": [
                {
                    "id": "us1",
                    "review_order": 1,
                    "kind": "user_story",
                    "parent_marker_id": None,
                    "source_boundary": {"story_id": 1},
                    "task_ids": ["T001"],
                    "folded_polish_task_ids": [],
                    "declared_files": [],
                    "reviewability": {
                        "head_sha": checkpoint.get("head_sha"),
                    },
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
            checkpoint=self.complete_checkpoint(),
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
            checkpoint=self.complete_checkpoint(commit_sha="b" * 40),
        )
        exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(exit_code, 1)
        self.assertEqual(len(report["projection_status_errors"]), 2)

    def test_checkpointing_phase_must_not_project_as_completed(self) -> None:
        state = self.projected_state(
            plan_status="completed",
            phase_status="checkpointing",
            checkpoint={"status": "pending"},
        )
        exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(exit_code, 1)
        self.assertEqual(len(report["projection_status_errors"]), 1)

    def test_complete_checkpoint_requires_terminal_evidence(self) -> None:
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
                "pr_marker_plan.markers[0].implementation_checkpoint.checkpoint_evidence_sha",
                "pr_marker_plan.markers[0].implementation_checkpoint.checkpoint_evidence_commit_sha",
                "pr_marker_plan.markers[0].implementation_checkpoint.verification_evidence_path",
                "pr_marker_plan.markers[0].implementation_checkpoint.commit_sha",
                "pr_marker_plan.markers[0].implementation_checkpoint.head_sha",
                "pr_marker_plan.markers[0].implementation_checkpoint.completed_at",
                "pr_marker_plan.markers[0].implementation_checkpoint.summary",
                "pr_marker_plan.markers[0].implementation_checkpoint.completed_task_ids",
                "pr_marker_plan.markers[0].implementation_checkpoint.validation",
                "pr_marker_plan.markers[0].implementation_checkpoint.freshness",
            ],
        )

    def test_legacy_v1_plan_remains_readable_without_v2_evidence_fields(self) -> None:
        state = self.projected_state(
            plan_status="completed",
            phase_status="completed",
            checkpoint={"status": "complete", "evidence_path": "legacy-checkpoint.json"},
        )
        state["pr_marker_plan"].update(
            {
                "schema_version": "pr-marker-plan.v1",
                "status": "emission_ready",
                "updated_at": "legacy timestamp accepted by v1",
            }
        )
        exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(exit_code, 0, report)

    def test_complete_checkpoint_binds_task_coverage_and_reviewed_head(self) -> None:
        checkpoint = self.complete_checkpoint(commit_sha="b" * 40)
        checkpoint["head_sha"] = "c" * 40
        checkpoint["completed_task_ids"] = ["T999"]
        state = self.projected_state(
            plan_status="completed",
            phase_status="completed",
            checkpoint=checkpoint,
        )
        exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(exit_code, 1)
        self.assertEqual(
            report["checkpoint_evidence_errors"],
            [
                "pr_marker_plan.markers[0].implementation_checkpoint.completed_task_ids coverage",
                "pr_marker_plan.markers[0].implementation_checkpoint commit/head mismatch",
            ],
        )

    def test_malformed_marker_task_arrays_fail_without_crashing(self) -> None:
        state = self.projected_state(
            plan_status="completed",
            phase_status="completed",
            checkpoint=self.complete_checkpoint(),
        )
        state["pr_marker_plan"]["markers"][0]["task_ids"] = "T001"
        exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(exit_code, 1)
        self.assertEqual(
            report["checkpoint_evidence_errors"],
            ["pr_marker_plan.markers[0] marker task coverage"],
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
                "pr_marker_plan.markers[0] emission requires a complete checkpoint",
            ],
        )

    def test_top_level_emitted_requires_every_marker_mapping_emitted(self) -> None:
        state = self.projected_state(
            plan_status="completed",
            phase_status="completed",
            checkpoint=self.complete_checkpoint(),
        )
        state["pr_marker_plan"]["status"] = "emitted"
        exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(exit_code, 1)
        self.assertEqual(
            report["marker_plan_status_errors"],
            ["pr_marker_plan.status emitted rejects marker 0 emission 'pending'"],
        )

    def test_marker_plan_statuses_constrain_checkpoint_and_emission_states(self) -> None:
        cases = (
            ("planned", self.complete_checkpoint(), {"status": "pending"}, "checkpoint 'complete'"),
            ("checkpointing", self.complete_checkpoint(), {"status": "marker_split", "packet_path": "packet.json"}, "emission 'marker_split'"),
            ("emission_ready", {"status": "pending"}, {"status": "pending"}, "checkpoint 'pending'"),
            ("collapsed", self.complete_checkpoint(), {"status": "pending"}, "emission 'pending'"),
            ("emitting", self.complete_checkpoint(), {"status": "pending"}, "requires both emitted and unfinished"),
        )
        for plan_status, checkpoint, emission, expected in cases:
            with self.subTest(plan_status=plan_status):
                state = self.projected_state(
                    plan_status="completed" if checkpoint.get("status") == "complete" else "in_progress",
                    phase_status="completed" if checkpoint.get("status") == "complete" else "in_progress",
                    checkpoint=checkpoint,
                    emission=emission,
                )
                state["pr_marker_plan"]["status"] = plan_status
                exit_code, report = self.run_validator(workflow_text(), state)
                self.assertEqual(exit_code, 1)
                self.assertTrue(any(expected in error for error in report["marker_plan_status_errors"]))

    def test_stale_and_invalid_statuses_require_diagnostic_warnings(self) -> None:
        for plan_status, warning_code, severity in (
            ("stale", "MARKER_PLAN_STALE", "warning"),
            ("invalid", "MARKER_PLAN_INVALID", "error"),
        ):
            with self.subTest(plan_status=plan_status):
                state = self.projected_state(
                    plan_status="in_progress",
                    phase_status="in_progress",
                    checkpoint={"status": "pending"},
                )
                state["pr_marker_plan"].update({"status": plan_status, "warnings": []})
                _exit_code, report = self.run_validator(workflow_text(), state)
                self.assertIn(
                    f"pr_marker_plan.status {plan_status} requires diagnostic warning {warning_code}",
                    report["marker_plan_status_errors"],
                )
                state["pr_marker_plan"]["warnings"] = [
                    {"code": warning_code, "severity": severity},
                ]
                _exit_code, report = self.run_validator(workflow_text(), state)
                self.assertEqual(report["marker_plan_status_errors"], [])

    def test_stale_and_invalid_plans_preserve_terminal_emission_mappings(self) -> None:
        cases = (
            (
                "stale",
                "MARKER_PLAN_STALE",
                "warning",
                {"status": "emitted", "packet_path": "packet.json", "pr_number": 42, "pr_url": "https://example.test/pr/42"},
            ),
            ("invalid", "MARKER_PLAN_INVALID", "error", {"status": "hazard_collapsed"}),
        )
        for plan_status, warning_code, severity, emission in cases:
            with self.subTest(plan_status=plan_status):
                state = self.projected_state(
                    plan_status="completed",
                    phase_status="completed",
                    checkpoint=self.complete_checkpoint(),
                    emission=emission,
                )
                state["pr_marker_plan"].update(
                    {
                        "status": plan_status,
                        "warnings": [{"code": warning_code, "severity": severity}],
                    }
                )
                _exit_code, report = self.run_validator(workflow_text(), state)
                self.assertEqual(report["marker_plan_status_errors"], [])
                self.assertEqual(report["emission_mapping_errors"], [])

    def test_emitting_plan_supports_partial_monotonic_emission(self) -> None:
        state = self.projected_state(
            plan_status="completed",
            phase_status="completed",
            checkpoint=self.complete_checkpoint(),
            emission={"status": "emitted", "packet_path": "us1.json", "pr_number": 41, "pr_url": "https://example.test/pr/41"},
        )
        second = json.loads(json.dumps(state["pr_marker_plan"]["markers"][0]))
        second.update(
            {
                "id": "us2",
                "review_order": 2,
                "source_boundary": {"story_id": 2},
                "task_ids": ["T002"],
                "implementation_checkpoint": self.complete_checkpoint(commit_sha="b" * 40),
                "emission_mapping": {"status": "pending", "packet_path": "us2.json"},
            }
        )
        second["implementation_checkpoint"]["completed_task_ids"] = ["T002"]
        second["reviewability"]["head_sha"] = "b" * 40
        state["pr_marker_plan"].update({"status": "emitting", "markers": [state["pr_marker_plan"]["markers"][0], second]})
        _exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(report["marker_plan_status_errors"], [])
        self.assertEqual(report["emission_mapping_errors"], [])

    def test_marker_contract_rejects_duplicate_identity_task_and_file_ownership(self) -> None:
        state = self.projected_state(
            plan_status="in_progress",
            phase_status="in_progress",
            checkpoint={"status": "pending"},
        )
        first = state["pr_marker_plan"]["markers"][0]
        first["declared_files"] = [{"operation": "MODIFIED", "path": "src/shared.py"}]
        second = json.loads(json.dumps(first))
        state["pr_marker_plan"]["markers"].append(second)
        _exit_code, report = self.run_validator(workflow_text(), state)
        errors = report["marker_plan_status_errors"]
        self.assertIn("pr_marker_plan marker id 'us1' is duplicated", errors)
        self.assertIn("pr_marker_plan review_order 1 is duplicated", errors)
        self.assertIn("pr_marker_plan task 'T001' is owned by both 'us1' and 'us1'", errors)
        self.assertIn("pr_marker_plan file 'src/shared.py' is owned by both 'us1' and 'us1'", errors)

    def test_marker_contract_rejects_unsafe_paths_invalid_identity_and_non_utc_timestamps(self) -> None:
        state = self.projected_state(
            plan_status="in_progress",
            phase_status="in_progress",
            checkpoint={"status": "pending", "evidence_path": "../outside.json"},
            emission={"status": "pending", "packet_path": "C:/outside.json", "pr_number": 7},
        )
        marker = state["pr_marker_plan"]["markers"][0]
        marker["id"] = "us1-part1"
        marker["declared_files"] = [{"operation": "MODIFIED", "path": "../outside.py"}]
        marker["reviewability"]["evidence_path"] = "/tmp/evidence.json"
        state["pr_marker_plan"]["updated_at"] = "2026-07-19 00:00:00"
        _exit_code, report = self.run_validator(workflow_text(), state)
        self.assertTrue(any("id, kind, story_id" in error for error in report["marker_plan_status_errors"]))
        self.assertTrue(any("declared_files[0].path" in error for error in report["marker_plan_status_errors"]))
        self.assertTrue(any("reviewability.evidence_path" in error for error in report["marker_plan_status_errors"]))
        self.assertIn(
            "pr_marker_plan.updated_at must be an RFC 3339 UTC timestamp",
            report["marker_plan_status_errors"],
        )
        self.assertTrue(any("implementation_checkpoint.evidence_path" in error for error in report["checkpoint_file_errors"]))
        self.assertTrue(any("emission_mapping.packet_path" in error for error in report["emission_mapping_errors"]))
        self.assertTrue(any("pr_number is only valid after emission" in error for error in report["emission_mapping_errors"]))

    def test_changed_file_manifest_must_match_base_to_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow_path = root / "workflow.md"
            state_path = root / "autopilot-state.json"
            tracked_path = root / "tracked.txt"
            manifest_path = root / "changed-file-manifest.json"
            tasks_path = root / "specs/spec-example/tasks.md"
            evidence_path = root / "specs/spec-example/.process/checkpoints/us1.json"
            workflow_path.write_text(workflow_text(), encoding="utf-8")
            state = state_json()
            state_path.write_text(json.dumps(state), encoding="utf-8")
            tracked_path.write_text("base\n", encoding="utf-8")
            tasks_path.parent.mkdir(parents=True)
            tasks_path.write_text("# Tasks\n\n- [x] T001 Marker task\n- [ ] T002 Other task\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "-c",
                    "user.name=SpecKit Tests",
                    "-c",
                    "user.email=git@github.com",
                    "-c",
                    "commit.gpgsign=false",
                    "commit",
                    "-qm",
                    "base",
                ],
                check=True,
            )
            base_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            tracked_path.write_text("changed\n", encoding="utf-8")
            state["changed_file_manifest"] = "changed-file-manifest.json"
            task_bytes = tasks_path.read_bytes()
            tasks_sha = f"sha256:{hashlib.sha256(task_bytes).hexdigest()}"
            marker_sha = "sha256:" + hashlib.sha256(b"- [x] T001 Marker task\n").hexdigest()
            evidence_path.parent.mkdir(parents=True)
            evidence_path.write_text(
                json.dumps(
                    {
                        "schema_version": "marker-checkpoint.v1",
                        "feature_id": "SPEC-EXAMPLE",
                        "marker_id": "us1",
                        "status": "complete",
                        "task_ids": ["T001"],
                        "implementation_checkpoint_sha": base_commit,
                        "verification": {"focused_tests": "pass"},
                        "source_fingerprint_status": "current",
                        "tasks_sha": tasks_sha,
                        "completed_at": "2026-07-19T00:00:00Z",
                    }
                ),
                encoding="utf-8",
            )
            marker_files = [
                {"path": "autopilot-state.json", "operation": "MODIFIED"},
                {"path": "changed-file-manifest.json", "operation": "NEW"},
                {
                    "path": "specs/spec-example/.process/checkpoints/us1.json",
                    "operation": "NEW",
                },
                {"path": "tracked.txt", "operation": "MODIFIED"},
            ]
            state["pr_marker_plan"] = {
                "schema_version": "pr-marker-plan.v2",
                "status": "emission_ready",
                "markers": [
                    {
                        "id": "us1",
                        "review_order": 1,
                        "kind": "user_story",
                        "parent_marker_id": None,
                        "source_boundary": {"story_id": 1},
                        "task_ids": ["T001"],
                        "folded_polish_task_ids": [],
                        "declared_files": marker_files,
                        "reviewability": {"head_sha": base_commit},
                        "implementation_checkpoint": {
                            "status": "complete",
                            "evidence_path": "specs/spec-example/.process/checkpoints/us1.json",
                            "checkpoint_evidence_sha": "pending manifest setup",
                            "checkpoint_evidence_commit_sha": "pending evidence commit",
                            "verification_evidence_path": "workflow.md",
                            "commit_sha": base_commit,
                            "head_sha": base_commit,
                            "completed_at": "2026-07-19T00:00:00Z",
                            "completed_task_ids": ["T001"],
                            "summary": "Completed us1.",
                            "validation": ["focused tests passed"],
                            "freshness": {
                                "source_fingerprint_status": "current_marker_scope",
                                "source_fingerprint_contract": "marker-task-lines.v2",
                                "tasks_sha_scope": "checkpoint_time_whole_file",
                                "current_tasks_sha": tasks_sha,
                                "checkpoint_marker_tasks_sha": marker_sha,
                                "current_marker_tasks_sha": marker_sha,
                                "validated_at": "2026-07-19T00:00:00Z",
                            },
                        },
                        "emission_mapping": {"status": "pending"},
                    }
                ],
            }
            state_path.write_text(json.dumps(state), encoding="utf-8")
            manifest = {
                "schema_version": "changed-file-manifest.v1",
                "base_commit": base_commit,
                "files": [
                    {
                        "path": "autopilot-state.json",
                        "operation": "MODIFIED",
                        "category": "process",
                        "provenance": "authored",
                        "marker_ids": ["us1"],
                    },
                    {
                        "path": "changed-file-manifest.json",
                        "operation": "NEW",
                        "category": "process",
                        "provenance": "authored",
                        "marker_ids": ["us1"],
                    },
                    {
                        "path": "specs/spec-example/.process/checkpoints/us1.json",
                        "operation": "NEW",
                        "category": "process",
                        "provenance": "authored",
                        "marker_ids": ["us1"],
                    },
                    {
                        "path": "tracked.txt",
                        "operation": "MODIFIED",
                        "category": "implementation",
                        "provenance": "authored",
                        "marker_ids": ["us1"],
                    },
                ],
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            manifest_sha = "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            evidence_sha = "sha256:" + hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            fingerprint = {"changed_file_manifest_sha": manifest_sha}
            state["current_source_fingerprint"] = fingerprint
            state["pr_marker_plan"]["source_fingerprint"] = dict(fingerprint)
            state["pr_marker_plan"]["markers"][0]["implementation_checkpoint"][
                "checkpoint_evidence_sha"
            ] = evidence_sha
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "-c",
                    "user.name=SpecKit Tests",
                    "-c",
                    "user.email=git@github.com",
                    "-c",
                    "commit.gpgsign=false",
                    "commit",
                    "-qm",
                    "evidence",
                ],
                check=True,
            )
            evidence_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            state["pr_marker_plan"]["markers"][0]["implementation_checkpoint"][
                "checkpoint_evidence_commit_sha"
            ] = evidence_commit
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "autopilot-state.json"], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "-c",
                    "user.name=SpecKit Tests",
                    "-c",
                    "user.email=git@github.com",
                    "-c",
                    "commit.gpgsign=false",
                    "commit",
                    "-qm",
                    "head",
                ],
                check=True,
            )

            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 0, report)
            self.assertEqual(report["changed_file_manifest_errors"], [])
            self.assertEqual(report["checkpoint_source_fingerprint_errors"], [])

            checkpoint_evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            checkpoint_evidence["verification"]["focused_tests"] = "changed"
            evidence_path.write_text(json.dumps(checkpoint_evidence), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0].implementation_checkpoint immutable evidence differs from checkpoint commit",
                report["checkpoint_file_errors"],
            )
            checkpoint_evidence["verification"]["focused_tests"] = "pass"
            evidence_path.write_text(json.dumps(checkpoint_evidence), encoding="utf-8")

            checkpoint = state["pr_marker_plan"]["markers"][0]["implementation_checkpoint"]
            checkpoint["checkpoint_evidence_sha"] = "sha256:" + "0" * 64
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0].implementation_checkpoint.checkpoint_evidence_sha",
                report["checkpoint_file_errors"],
            )
            checkpoint["checkpoint_evidence_sha"] = evidence_sha
            state_path.write_text(json.dumps(state), encoding="utf-8")

            manifest["files"][3]["category"] = "test"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "current_source_fingerprint.changed_file_manifest_sha does not match the changed-file manifest",
                report["changed_file_manifest_errors"],
            )
            manifest["files"][3]["category"] = "implementation"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            manifest["files"][3]["operation"] = "NEW"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                f"declared changed-file manifest does not match {base_commit}..HEAD",
                report["changed_file_manifest_errors"],
            )
            self.assertIn(
                "pr_marker_plan marker us1 operation for tracked.txt does not match changed-file manifest",
                report["changed_file_manifest_errors"],
            )

            manifest["files"][3]["operation"] = "MODIFIED"
            manifest["files"][3]["marker_ids"] = ["us2"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan marker ownership for tracked.txt does not match changed-file manifest",
                report["changed_file_manifest_errors"],
            )

            manifest["files"][3]["marker_ids"] = ["us1", "us2"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "files[3].marker_ids must contain exactly one marker owner",
                report["changed_file_manifest_errors"],
            )

            manifest["files"][3]["marker_ids"] = ["us1"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            tasks_path.write_text("# Tasks\n\n- [x] T001 Changed marker task\n- [ ] T002 Other task\n", encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0] checkpoint current_marker_tasks_sha",
                report["checkpoint_source_fingerprint_errors"],
            )
            self.assertIn(
                "pr_marker_plan.markers[0] checkpoint marker_scope_unchanged",
                report["checkpoint_source_fingerprint_errors"],
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
