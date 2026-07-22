#!/usr/bin/env python3
"""Regression tests for autopilot canonical phase coverage validation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "scripts" / "validate-autopilot-phase-coverage.py"
CANONICAL_SCHEMA_PATHS = tuple(
    VALIDATOR.parents[1] / "contracts" / name
    for name in (
        "pr-marker-plan.schema.json",
        "changed-file-manifest.schema.json",
        "verification-report.schema.json",
    )
)
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


def load_validator_module() -> object:
    spec = importlib.util.spec_from_file_location(
        "speckit_autopilot_phase_coverage_validator",
        VALIDATOR,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load autopilot phase coverage validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR_MODULE = load_validator_module()

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
        local_validator = state_path.parent / VALIDATOR.relative_to(REPO_ROOT)
        command = [
            sys.executable,
            str(local_validator if local_validator.is_file() else VALIDATOR),
            "--workflow",
            str(workflow_path),
            "--state",
            str(state_path),
        ]
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, RecursionError):
            state = {}
        expected_base = getattr(self, "_expected_manifest_base_commit", None)
        if state.get("changed_file_manifest") is not None and expected_base is not None:
            expected_head = subprocess.run(
                ["git", "-C", str(state_path.parent), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            command.extend(
                [
                    "--expected-base-commit",
                    expected_base,
                    "--expected-head-commit",
                    expected_head,
                ]
            )
        completed = subprocess.run(
            command,
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
            "verification_evidence_sha": "sha256:" + "d" * 64,
            "commit_sha": commit_sha,
            "head_sha": commit_sha,
            "completed_at": "2026-07-19T00:00:00Z",
            "completed_task_ids": ["T001"],
            "required_verification_gate_ids": ["focused_tests"],
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
        state["spec_id"] = "SPEC-EXAMPLE"
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
            "kind": "pr_marker_plan",
            "feature_id": "SPEC-EXAMPLE",
            "status": "checkpointing",
            "source_fingerprint": {
                "feature_spec_sha": "sha256:" + "a" * 64,
                "plan_declared_scope_sha": "sha256:" + "b" * 64,
                "tasks_sha": "sha256:" + "c" * 64,
                "reviewability_sha": "sha256:" + "d" * 64,
                "hazard_route_sha": "sha256:" + "e" * 64,
                "changed_file_manifest_sha": "sha256:" + "f" * 64,
            },
            "markers": [
                {
                    "id": "us1",
                    "review_order": 1,
                    "kind": "user_story",
                    "parent_marker_id": None,
                    "source_boundary": {
                        "section": "User Story 1",
                        "story_id": 1,
                        "start_task_id": "T001",
                        "end_task_id": "T001",
                    },
                    "task_ids": ["T001"],
                    "folded_polish_task_ids": [],
                    "folded_polish_target_reason": "",
                    "declared_files": [],
                    "declared_tests": [],
                    "reviewability": {
                        "status": "pass",
                        "mode": "implementation",
                        "scope": "us1",
                        **(
                            {"head_sha": checkpoint["head_sha"]}
                            if isinstance(checkpoint.get("head_sha"), str)
                            else {}
                        ),
                    },
                    "hazards": [],
                    "subdivision": {"status": "none", "details": {}},
                    "implementation_checkpoint": checkpoint,
                    "emission_mapping": emission or {"status": "pending"},
                    "warnings": [],
                }
            ],
            "warnings": [],
        }
        return state

    def test_complete_workflow_and_state_pass(self) -> None:
        exit_code, report = self.run_validator(workflow_text(), state_json())
        self.assertEqual(exit_code, 0)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["missing_state_post_items"], [])

    def test_repo_reader_accepts_regular_files_and_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            source = root / "safe.json"
            source.write_bytes(b'{"safe":true}')
            self.assertEqual(
                VALIDATOR_MODULE._read_repo_bytes(root, "safe.json"),
                b'{"safe":true}',
            )
            outside = Path(tmp) / "outside.json"
            outside.write_bytes(b'{"outside":true}')
            link = root / "link.json"
            try:
                link.symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            self.assertIsNone(
                VALIDATOR_MODULE._read_repo_bytes(root, "link.json")
            )

    @unittest.skipUnless(
        getattr(VALIDATOR_MODULE, "HAS_DESCRIPTOR_RELATIVE_IO", False),
        "requires descriptor-relative no-follow reads",
    )
    def test_repo_reader_rejects_directory_swap_during_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / "evidence"
            directory.mkdir()
            source = directory / "record.json"
            source.write_bytes(b'{"original":true}')
            moved_directory = root / "evidence-original"
            original_open = VALIDATOR_MODULE.os.open
            swapped = False

            def replace_directory(
                path: object,
                flags: int,
                *args: object,
                **kwargs: object,
            ) -> int:
                nonlocal swapped
                if (
                    path == "record.json"
                    and kwargs.get("dir_fd") is not None
                    and not swapped
                ):
                    swapped = True
                    directory.rename(moved_directory)
                    directory.mkdir()
                    (directory / "record.json").write_bytes(b'{"replacement":true}')
                return original_open(path, flags, *args, **kwargs)

            with mock.patch.object(
                VALIDATOR_MODULE.os,
                "open",
                side_effect=replace_directory,
            ):
                self.assertIsNone(
                    VALIDATOR_MODULE._read_repo_bytes(
                        root,
                        "evidence/record.json",
                    )
                )
            self.assertTrue(swapped)

    def test_hidden_full_workflow_does_not_satisfy_visible_contract(self) -> None:
        complete_workflow = workflow_text()
        compact_workflow = "\n".join(
            line for line in complete_workflow.splitlines() if line.strip()
        )
        hidden_workflows = {
            "fenced": f"# Wrapper\n\n````markdown\n{complete_workflow}\n````\n",
            "closed_comment": f"# Wrapper\n\n<!--\n{complete_workflow}\n-->\n",
            "unclosed_comment": f"# Wrapper\n\n<!--\n{complete_workflow}",
            "four_space_indented": "# Wrapper\n\n" + "\n".join(
                f"    {line}" for line in complete_workflow.splitlines()
            ),
            "tab_indented": "# Wrapper\n\n" + "\n".join(
                f"\t{line}" for line in complete_workflow.splitlines()
            ),
            "script_html": f"# Wrapper\n\n<script>\n{complete_workflow}\n</script>\n",
            "style_html": f"# Wrapper\n\n<style>\n{complete_workflow}\n</style>\n",
            "textarea_html": f"# Wrapper\n\n<textarea>\n{complete_workflow}\n</textarea>\n",
            "pre_html": f"# Wrapper\n\n<pre>\n{complete_workflow}\n</pre>\n",
            "processing_instruction": f"# Wrapper\n\n<?hidden\n{complete_workflow}\n?>\n",
            "declaration": f"# Wrapper\n\n<!HIDDEN\n{complete_workflow}\n>\n",
            "cdata": f"# Wrapper\n\n<![CDATA[\n{complete_workflow}\n]]>\n",
            "block_tag": f"# Wrapper\n\n<div>\n{compact_workflow}\n</div>\n\n",
            "complete_tag": f"# Wrapper\n\n<hidden>\n{compact_workflow}\n</hidden>\n\n",
        }
        for hidden_kind, workflow in hidden_workflows.items():
            with self.subTest(hidden_kind=hidden_kind):
                exit_code, report = self.run_validator(workflow, state_json())
                self.assertEqual(exit_code, 1)
                self.assertEqual(len(report["missing_workflow_sections"]), 9)
                self.assertEqual(len(report["missing_workflow_tokens"]), 3)
                self.assertEqual(len(report["missing_workflow_post_items"]), 12)

    def test_workflow_checkpoint_claims_bind_marker_plan_commits(self) -> None:
        expected_commit = "a" * 40
        wrong_commit = "b" * 40
        expected_superseded = "c" * 40
        wrong_superseded = "d" * 40
        checkpoint = self.complete_checkpoint(commit_sha=expected_commit)
        checkpoint["superseded_commit_sha"] = expected_superseded
        state = self.projected_state(
            plan_status="completed",
            phase_status="completed",
            checkpoint=checkpoint,
        )
        workflow = workflow_text() + (
            f"\n- Implementation checkpoint [us1]: `{wrong_commit}`\n"
            f"- Current remediation source head [us2]: `{expected_commit}`\n"
            f"- Superseded marker checkpoint [us1]: `{wrong_superseded}`\n"
            f"- Implementation checkpoint: `{expected_commit}`\n\n"
            "## PR Marker Plan Evidence\n\n"
            "- Plan status: `checkpointing`\n\n"
            "| Review order | Marker | Tasks | Reviewability | Checkpoint | Warning |\n"
            "|---|---|---|---|---|---|\n"
            f"| 1 | `us1` | T001 | Pass | Complete at `{wrong_commit}` | None |\n"
        )
        exit_code, report = self.run_validator(workflow, state)
        self.assertEqual(exit_code, 1)
        self.assertEqual(
            report["workflow_checkpoint_errors"],
            [
                "workflow checkpoint claim for marker 'us1' does not match its pr_marker_plan commit_sha",
                "workflow checkpoint claim for marker 'us2' does not match its pr_marker_plan commit_sha",
                "workflow superseded checkpoint claim for marker 'us1' does not match its pr_marker_plan superseded_commit_sha",
                "workflow checkpoint claims must name their marker",
                f"workflow PR Marker Plan Evidence marker 'us1' checkpoint does not bind {expected_commit}",
            ],
        )
        corrected_workflow = workflow.replace(wrong_commit, expected_commit).replace(
                wrong_superseded, expected_superseded,
            ).replace(
                f"- Current remediation source head [us2]: `{expected_commit}`\n", "",
            ).replace(
                f"- Implementation checkpoint: `{expected_commit}`\n", "",
            )
        _, corrected = self.run_validator(corrected_workflow, state)
        self.assertEqual(corrected["workflow_checkpoint_errors"], [])

        mismatched_status_workflow = corrected_workflow.replace(
            "- Plan status: `checkpointing`",
            "- Plan status: `emission_ready`",
        )
        _, mismatched_status = self.run_validator(
            mismatched_status_workflow, state,
        )
        self.assertIn(
            "workflow PR Marker Plan Evidence Plan status must exactly match pr_marker_plan.status",
            mismatched_status["workflow_checkpoint_errors"],
        )

        missing_section_workflow = corrected_workflow.split(
            "## PR Marker Plan Evidence", 1,
        )[0]
        _, missing_section = self.run_validator(missing_section_workflow, state)
        self.assertIn(
            "workflow must contain exactly one PR Marker Plan Evidence section",
            missing_section["workflow_checkpoint_errors"],
        )
        missing_claim_workflow = corrected_workflow.replace(
            f"- Implementation checkpoint [us1]: `{expected_commit}`\n", "",
        )
        _, missing_claim = self.run_validator(missing_claim_workflow, state)
        self.assertIn(
            "workflow must contain exactly one current checkpoint claim for marker 'us1'",
            missing_claim["workflow_checkpoint_errors"],
        )

        prefix, evidence_section = corrected_workflow.split(
            "## PR Marker Plan Evidence", 1,
        )
        fenced_section_workflow = (
            prefix
            + "```markdown\n## PR Marker Plan Evidence"
            + evidence_section
            + "\n```\n"
        )
        _, fenced_section = self.run_validator(fenced_section_workflow, state)
        self.assertIn(
            "workflow must contain exactly one PR Marker Plan Evidence section",
            fenced_section["workflow_checkpoint_errors"],
        )

        claim = f"- Implementation checkpoint [us1]: `{expected_commit}`\n"
        commented_claim_workflow = corrected_workflow.replace(
            claim, f"<!-- {claim.strip()} -->\n",
        )
        _, commented_claim = self.run_validator(commented_claim_workflow, state)
        self.assertIn(
            "workflow must contain exactly one current checkpoint claim for marker 'us1'",
            commented_claim["workflow_checkpoint_errors"],
        )

    def test_pending_phase_claim_requires_checkpoint_authority(self) -> None:
        state = self.projected_state(
            plan_status="pending",
            phase_status="pending",
            checkpoint={"status": "pending"},
            phase_fields={"focused_tests": "not independently evidenced"},
        )
        exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(exit_code, 1)
        self.assertTrue(
            any(
                "implementation_checkpoint is missing required fields: commit_sha, evidence_path"
                in error
                for error in report["marker_plan_status_errors"]
            )
        )
        self.assertIn(
            "pr_marker_plan.markers[0] pending checkpoint with phase claims requires evidence_path",
            report["checkpoint_evidence_errors"],
        )
        self.assertIn(
            "pr_marker_plan.markers[0] pending checkpoint with phase claims requires commit_sha",
            report["checkpoint_evidence_errors"],
        )
        self.assertIn(
            "workflow must contain exactly one current checkpoint claim for marker 'us1'",
            report["workflow_checkpoint_errors"],
        )

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

    def test_every_implementation_phase_requires_a_declared_marker_owner(self) -> None:
        state = self.projected_state(
            plan_status="pending",
            phase_status="pending",
            checkpoint={"status": "pending"},
        )
        state["phase_results"]["Phase 7: Implement - Integration and Polish"] = {
            "status": "pending",
        }
        exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(exit_code, 1)
        self.assertIn(
            "phase_results[Phase 7: Implement - Integration and Polish] must declare exactly one marker_id",
            report["marker_plan_status_errors"],
        )

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
                "pr_marker_plan.markers[0].implementation_checkpoint.verification_evidence_sha",
                "pr_marker_plan.markers[0].implementation_checkpoint.commit_sha",
                "pr_marker_plan.markers[0].implementation_checkpoint.head_sha",
                "pr_marker_plan.markers[0].implementation_checkpoint.completed_at",
                "pr_marker_plan.markers[0].implementation_checkpoint.summary",
                "pr_marker_plan.markers[0].implementation_checkpoint.completed_task_ids",
                "pr_marker_plan.markers[0].implementation_checkpoint.required_verification_gate_ids",
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

    def test_legacy_v1_stale_and_invalid_plans_are_correctness_stops(self) -> None:
        for plan_status, warning_code, severity in (
            ("stale", "MARKER_PLAN_STALE", "warning"),
            ("invalid", "MARKER_PLAN_INVALID", "error"),
        ):
            state = self.projected_state(
                plan_status="completed",
                phase_status="completed",
                checkpoint={
                    "status": "complete",
                    "evidence_path": "legacy-checkpoint.json",
                },
            )
            state["pr_marker_plan"].update(
                {
                    "schema_version": "pr-marker-plan.v1",
                    "status": plan_status,
                    "warnings": [
                        {
                            "code": warning_code,
                            "severity": severity,
                            "message": "Legacy plan is not executable.",
                            "source": "unit-test",
                            "details": {},
                        }
                    ],
                }
            )
            for marker_shape in ("valid", "missing", "malformed"):
                with self.subTest(
                    plan_status=plan_status,
                    marker_shape=marker_shape,
                ):
                    candidate = json.loads(json.dumps(state))
                    if marker_shape == "missing":
                        candidate["pr_marker_plan"].pop("markers")
                    elif marker_shape == "malformed":
                        candidate["pr_marker_plan"]["markers"] = {}
                    exit_code, report = self.run_validator(
                        workflow_text(),
                        candidate,
                    )
                    self.assertEqual(exit_code, 1)
                    self.assertEqual(report["status"], "fail")
                    self.assertEqual(
                        report["marker_plan_status_errors"],
                        [f"pr_marker_plan.status {plan_status} is a correctness stop"],
                    )

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
            [
                "pr_marker_plan.markers[0].emission_mapping.status does not match its schema constant",
                "pr_marker_plan.status emitted rejects marker 0 emission 'pending'",
            ],
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
                    checkpoint={
                        "status": "pending",
                        "evidence_path": "specs/spec-example/.process/checkpoints/us1.json",
                        "commit_sha": "a" * 40,
                    },
                )
                state["pr_marker_plan"].update({"status": plan_status, "warnings": []})
                _exit_code, report = self.run_validator(workflow_text(), state)
                self.assertIn(
                    f"pr_marker_plan.status {plan_status} requires diagnostic warning {warning_code}",
                    report["marker_plan_status_errors"],
                )
                state["pr_marker_plan"]["warnings"] = [
                    {
                        "code": warning_code,
                        "severity": severity,
                        "message": "Test diagnostic.",
                        "source": "unit-test",
                        "details": {},
                    },
                ]
                exit_code, report = self.run_validator(workflow_text(), state)
                self.assertEqual(exit_code, 1)
                self.assertEqual(report["status"], "fail")
                self.assertEqual(
                    report["marker_plan_status_errors"],
                    [f"pr_marker_plan.status {plan_status} is a correctness stop"],
                )

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
                        "warnings": [{
                            "code": warning_code,
                            "severity": severity,
                            "message": "Test diagnostic.",
                            "source": "unit-test",
                            "details": {},
                        }],
                    }
                )
                exit_code, report = self.run_validator(workflow_text(), state)
                self.assertEqual(exit_code, 1)
                self.assertEqual(
                    report["marker_plan_status_errors"],
                    [f"pr_marker_plan.status {plan_status} is a correctness stop"],
                )
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
                "source_boundary": {
                    "section": "User Story 2",
                    "story_id": 2,
                    "start_task_id": "T002",
                    "end_task_id": "T002",
                },
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

    def test_marker_contract_rejects_gapped_and_reordered_review_orders(self) -> None:
        state = self.projected_state(
            plan_status="in_progress",
            phase_status="in_progress",
            checkpoint={"status": "pending"},
        )
        first = state["pr_marker_plan"]["markers"][0]
        second = json.loads(json.dumps(first))
        second.update(
            {
                "id": "us2",
                "review_order": 2,
                "source_boundary": {
                    "section": "User Story 2",
                    "story_id": 2,
                    "start_task_id": "T002",
                    "end_task_id": "T002",
                },
                "task_ids": ["T002"],
            }
        )
        state["pr_marker_plan"]["markers"] = [first, second]
        for review_orders, expected in (
            (
                (1, 3),
                "pr_marker_plan.markers[1].review_order must equal its contiguous marker array position 2",
            ),
            (
                (2, 1),
                "pr_marker_plan.markers[0].review_order must equal its contiguous marker array position 1",
            ),
        ):
            with self.subTest(review_orders=review_orders):
                candidate = json.loads(json.dumps(state))
                for marker, review_order in zip(
                    candidate["pr_marker_plan"]["markers"],
                    review_orders,
                ):
                    marker["review_order"] = review_order
                exit_code, report = self.run_validator(workflow_text(), candidate)
                self.assertEqual(exit_code, 1)
                self.assertIn(expected, report["marker_plan_status_errors"])

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
            alternate_workflow_path = root / "alternate-workflow.md"
            state_path = root / "autopilot-state.json"
            tracked_path = root / "tracked.txt"
            rename_source_path = root / "rename-source.txt"
            rename_target_path = root / "rename-target.txt"
            deleted_path = root / "deleted.txt"
            new_path = root / "new.txt"
            manifest_path = root / "changed-file-manifest.json"
            tasks_path = root / "specs/spec-example/tasks.md"
            checkpoint_schema_path = (
                root / "specs/spec-example/contracts/marker-checkpoint.schema.json"
            )
            evidence_path = root / "specs/spec-example/.process/checkpoints/us1.json"
            verification_path = root / "specs/spec-example/.process/verification/us1.json"
            workflow_path.write_text(workflow_text(), encoding="utf-8")
            alternate_workflow_path.write_text(workflow_text(), encoding="utf-8")
            state = state_json()
            state["workflow_file"] = "workflow.md"
            state["spec_id"] = "SPEC-EXAMPLE"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            tracked_path.write_text("base\n", encoding="utf-8")
            rename_source_path.write_text("rename payload " * 20 + "\n", encoding="utf-8")
            deleted_path.write_text("deleted content " * 20 + "\n", encoding="utf-8")
            tasks_path.parent.mkdir(parents=True)
            tasks_path.write_text("# Tasks\n\n- [x] T001 Marker task\n- [ ] T002 Other task\n", encoding="utf-8")
            checkpoint_schema_path.parent.mkdir(parents=True)
            checkpoint_schema_path.write_text(
                json.dumps(
                    {
                        "type": "object",
                        "required": [
                            "schema_version", "feature_id", "marker_id", "status",
                            "task_ids", "implementation_checkpoint_sha", "verification",
                            "source_fingerprint_status", "tasks_sha",
                        ],
                        "properties": {
                            "schema_version": {"const": "marker-checkpoint.v1"},
                            "feature_id": {"const": "SPEC-EXAMPLE"},
                            "marker_id": {"const": "us1"},
                            "status": {"enum": ["pending", "complete"]},
                            "task_ids": {"type": "array", "minItems": 1},
                            "implementation_checkpoint_sha": {
                                "type": "string", "pattern": "^[0-9a-f]{40}$",
                            },
                            "verification": {"type": "object", "minProperties": 1},
                            "source_fingerprint_status": {"type": "string"},
                            "tasks_sha": {
                                "type": "string", "pattern": "^sha256:[0-9a-f]{64}$",
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            local_validator = root / VALIDATOR.relative_to(REPO_ROOT)
            local_validator.parent.mkdir(parents=True)
            shutil.copy2(VALIDATOR, local_validator)
            local_schema_paths: list[Path] = []
            for source_schema in CANONICAL_SCHEMA_PATHS:
                local_schema = root / source_schema.relative_to(REPO_ROOT)
                local_schema.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_schema, local_schema)
                local_schema_paths.append(local_schema)
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
            initial_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            subprocess.run(
                [
                    "git", "-C", str(root), "update-index", "--add", "--cacheinfo",
                    f"160000,{initial_commit},vendor/submodule",
                ],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "base gitlink",
                ],
                check=True,
            )
            base_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            self._expected_manifest_base_commit = base_commit
            tracked_path.write_text("changed\n", encoding="utf-8")
            rename_source_path.rename(rename_target_path)
            rename_target_path.write_text(
                rename_target_path.read_text(encoding="utf-8") + "changed\n",
                encoding="utf-8",
            )
            deleted_path.unlink()
            new_path.write_text("new content " * 20 + "\n", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "config", "diff.renames", "false"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "config", "diff.renameLimit", "1"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "config", "diff.ignoreSubmodules", "all"],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "add", "-A", "tracked.txt",
                    "rename-source.txt", "rename-target.txt", "deleted.txt", "new.txt",
                ],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "update-index", "--cacheinfo",
                    f"160000,{base_commit},vendor/submodule",
                ],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "implementation",
                ],
                check=True,
            )
            implementation_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            workflow_path.write_text(
                workflow_text()
                + f"\n- Implementation checkpoint [us1]: `{implementation_commit}`\n\n"
                + "## PR Marker Plan Evidence\n\n"
                + "| Review order | Marker | Tasks | Reviewability | Checkpoint | Warning |\n"
                + "|---|---|---|---|---|---|\n"
                + f"| 1 | `us1` | T001-T002 | Pass | Complete at `{implementation_commit}` | None |\n",
                encoding="utf-8",
            )
            state["changed_file_manifest"] = "changed-file-manifest.json"
            state["changed_file_manifest_base_commit"] = base_commit
            task_bytes = tasks_path.read_bytes()
            tasks_sha = f"sha256:{hashlib.sha256(task_bytes).hexdigest()}"
            marker_sha = "sha256:" + hashlib.sha256(
                b"- [x] T001 Marker task\n- [ ] T002 Other task\n"
            ).hexdigest()
            evidence_path.parent.mkdir(parents=True)
            verification_path.parent.mkdir(parents=True)
            verification_gate_ids = [
                "focused_tests", "independent_critical_high_review",
            ]
            verification_results = {
                "focused_tests": {"status": "pass", "evidence": "pass"},
                "independent_critical_high_review": {
                    "status": "pass",
                    "evidence": (
                        "independent review clean at "
                        f"{implementation_commit}"
                    ),
                },
            }
            verification_path.write_text(
                json.dumps(
                    {
                        "schema_version": "verification-report.v1",
                        "feature_id": "SPEC-EXAMPLE",
                        "marker_id": "us1",
                        "status": "pass",
                        "generated_at": "2026-07-19T00:00:00Z",
                        "verified_commit_sha": implementation_commit,
                        "required_gate_ids": verification_gate_ids,
                        "results": verification_results,
                    }
                ),
                encoding="utf-8",
            )
            verification_evidence_sha = (
                "sha256:" + hashlib.sha256(verification_path.read_bytes()).hexdigest()
            )
            evidence_path.write_text(
                json.dumps(
                    {
                        "schema_version": "marker-checkpoint.v1",
                        "feature_id": "SPEC-EXAMPLE",
                        "marker_id": "us1",
                        "status": "complete",
                        "task_ids": ["T001", "T002"],
                        "implementation_checkpoint_sha": implementation_commit,
                        "last_reviewed_head_sha": implementation_commit,
                        "verification": verification_results,
                        "verification_evidence_sha": verification_evidence_sha,
                        "required_verification_gate_ids": verification_gate_ids,
                        "source_fingerprint_status": "current",
                        "tasks_sha": tasks_sha,
                        "completed_at": "2026-07-19T00:00:00Z",
                    }
                ),
                encoding="utf-8",
            )
            marker_files = [
                {"path": "autopilot-state.json", "operation": "MODIFIED"},
                {"path": "workflow.md", "operation": "MODIFIED"},
                {"path": "changed-file-manifest.json", "operation": "NEW"},
                {
                    "path": "specs/spec-example/.process/checkpoints/us1.json",
                    "operation": "NEW",
                },
                {
                    "path": "specs/spec-example/.process/verification/us1.json",
                    "operation": "NEW",
                },
                {"path": "tracked.txt", "operation": "MODIFIED"},
                {
                    "source_path": "rename-source.txt",
                    "path": "rename-target.txt",
                    "operation": "RENAMED",
                },
                {"path": "deleted.txt", "operation": "DELETED"},
                {"path": "new.txt", "operation": "NEW"},
                {"path": "vendor/submodule", "operation": "MODIFIED"},
            ]
            state["pr_marker_plan"] = {
                "schema_version": "pr-marker-plan.v2",
                "kind": "pr_marker_plan",
                "feature_id": "SPEC-EXAMPLE",
                "status": "emission_ready",
                "source_fingerprint": {},
                "markers": [
                    {
                        "id": "us1",
                        "review_order": 1,
                        "kind": "user_story",
                        "parent_marker_id": None,
                        "source_boundary": {
                            "section": "User Story 1",
                            "story_id": 1,
                            "start_task_id": "T001",
                            "end_task_id": "T002",
                        },
                        "task_ids": ["T001"],
                        "folded_polish_task_ids": ["T002"],
                        "folded_polish_target_reason": "Fold test coverage.",
                        "declared_files": marker_files,
                        "declared_tests": ["python3 tests.py"],
                        "reviewability": {
                            "status": "pass",
                            "mode": "implementation",
                            "scope": "us1",
                            "head_sha": implementation_commit,
                        },
                        "hazards": [],
                        "subdivision": {"status": "none", "details": {}},
                        "implementation_checkpoint": {
                            "status": "complete",
                            "evidence_path": "specs/spec-example/.process/checkpoints/us1.json",
                            "checkpoint_evidence_sha": "pending manifest setup",
                            "checkpoint_evidence_commit_sha": "pending evidence commit",
                            "verification_evidence_path": "specs/spec-example/.process/verification/us1.json",
                            "verification_evidence_sha": verification_evidence_sha,
                            "commit_sha": implementation_commit,
                            "head_sha": implementation_commit,
                            "completed_at": "2026-07-19T00:00:00Z",
                            "completed_task_ids": ["T001", "T002"],
                            "required_verification_gate_ids": verification_gate_ids,
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
                        "warnings": [],
                    }
                ],
                "warnings": [],
            }
            state_path.write_text(json.dumps(state), encoding="utf-8")
            manifest = {
                "schema_version": "changed-file-manifest.v1",
                "feature_id": "SPEC-EXAMPLE",
                "base_commit": base_commit,
                "comparison_ref": "HEAD",
                "files": [
                    {
                        "path": "autopilot-state.json",
                        "operation": "MODIFIED",
                        "category": "process",
                        "provenance": "authored",
                        "marker_ids": ["us1"],
                    },
                    {
                        "path": "workflow.md",
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
                        "path": "specs/spec-example/.process/verification/us1.json",
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
                    {
                        "source_path": "rename-source.txt",
                        "path": "rename-target.txt",
                        "operation": "RENAMED",
                        "category": "implementation",
                        "provenance": "authored",
                        "marker_ids": ["us1"],
                    },
                    {
                        "path": "deleted.txt",
                        "operation": "DELETED",
                        "category": "implementation",
                        "provenance": "authored",
                        "marker_ids": ["us1"],
                    },
                    {
                        "path": "new.txt",
                        "operation": "NEW",
                        "category": "implementation",
                        "provenance": "authored",
                        "marker_ids": ["us1"],
                    },
                    {
                        "path": "vendor/submodule",
                        "operation": "MODIFIED",
                        "category": "implementation",
                        "provenance": "authored",
                        "marker_ids": ["us1"],
                    },
                ],
            }
            tracked_manifest_entry = next(
                entry for entry in manifest["files"] if entry["path"] == "tracked.txt"
            )
            tracked_manifest_index = manifest["files"].index(tracked_manifest_entry)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            manifest_sha = "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            evidence_sha = "sha256:" + hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            fingerprint = {
                "feature_spec_sha": "sha256:" + "a" * 64,
                "plan_declared_scope_sha": "sha256:" + "b" * 64,
                "tasks_sha": tasks_sha,
                "reviewability_sha": "sha256:" + "c" * 64,
                "hazard_route_sha": "sha256:" + "d" * 64,
                "changed_file_manifest_sha": manifest_sha,
            }
            fingerprint_rows = (
                ("Feature spec", "feature_spec_sha"),
                ("Plan-declared scope", "plan_declared_scope_sha"),
                ("Tasks", "tasks_sha"),
                ("Reviewability evidence", "reviewability_sha"),
                ("Hazard route", "hazard_route_sha"),
                ("Changed-file manifest", "changed_file_manifest_sha"),
            )
            fingerprint_table = (
                "- Plan status: `emission_ready`\n"
                "- Fingerprint status: Current\n\n"
                "| Fingerprint input | SHA-256 |\n"
                "|---|---|\n"
                + "".join(
                    f"| {label} | `{fingerprint[field]}` |\n"
                    for label, field in fingerprint_rows
                )
                + "\n"
            )
            workflow_path.write_text(
                workflow_path.read_text(encoding="utf-8").replace(
                    "## PR Marker Plan Evidence\n\n",
                    "## PR Marker Plan Evidence\n\n" + fingerprint_table,
                    1,
                ),
                encoding="utf-8",
            )
            state["current_source_fingerprint"] = fingerprint
            state["pr_marker_plan"]["source_fingerprint"] = dict(fingerprint)
            state["pr_marker_plan"]["markers"][0]["implementation_checkpoint"][
                "checkpoint_evidence_sha"
            ] = evidence_sha
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(
                [
                    "git", "-C", str(root), "add",
                    "autopilot-state.json",
                    "workflow.md",
                    "changed-file-manifest.json",
                    "specs/spec-example/.process/checkpoints/us1.json",
                    "specs/spec-example/.process/verification/us1.json",
                ],
                check=True,
            )
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

            current_workflow = workflow_path.read_bytes()
            workflow_path.write_text(
                workflow_path.read_text(encoding="utf-8").replace(
                    fingerprint["reviewability_sha"],
                    "sha256:" + "0" * 64,
                    1,
                ),
                encoding="utf-8",
            )
            subprocess.run(["git", "-C", str(root), "add", "workflow.md"], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "stale visible workflow fingerprint",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "workflow Current fingerprint 'Reviewability evidence' does not exactly "
                "match pr_marker_plan.source_fingerprint.reviewability_sha",
                report["workflow_checkpoint_errors"],
            )
            workflow_path.write_bytes(current_workflow)
            subprocess.run(["git", "-C", str(root), "add", "workflow.md"], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "restore visible workflow fingerprint",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 0, report)

            schema_error_buckets = (
                "marker_plan_status_errors",
                "changed_file_manifest_errors",
                "checkpoint_evidence_errors",
            )
            schema_labels = (
                "pr-marker-plan",
                "changed-file manifest",
                "verification report",
            )
            for schema_path, error_bucket, schema_label in zip(
                local_schema_paths, schema_error_buckets, schema_labels,
            ):
                clean_schema_bytes = schema_path.read_bytes()
                schema_path.write_bytes(clean_schema_bytes + b"\n")
                exit_code, report = self.run_validator_paths(workflow_path, state_path)
                self.assertEqual(exit_code, 1)
                self.assertIn(
                    f"canonical {schema_label} schema differs from the authorized PR head",
                    report[error_bucket],
                )
                schema_path.write_bytes(clean_schema_bytes)

            committed_workflow = workflow_path.read_bytes()
            workflow_path.write_bytes(committed_workflow + b"\nmutable worktree claim\n")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "workflow differs from the authorized PR head",
                report["workflow_checkpoint_errors"],
            )
            workflow_path.write_bytes(committed_workflow)

            exit_code, report = self.run_validator_paths(
                alternate_workflow_path, state_path,
            )
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "supplied workflow does not match autopilot state workflow_file authority",
                report["workflow_checkpoint_errors"],
            )

            phase_name = "Phase 7: Implement - Pending task decomposition"
            phase_step = next(
                item for item in state["plan"] if item["step"] == phase_name
            )
            phase_step["status"] = "completed"
            state["phase_results"] = {
                phase_name: {
                    "status": "completed",
                    "marker_id": "us1",
                    "independent_review": "fabricated pass",
                },
            }
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "autopilot-state.json"], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "fabricated completed review claim",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                f"pr_marker_plan.markers[0] phase_results[{phase_name}] independent_review does not match checkpoint evidence",
                report["checkpoint_evidence_errors"],
            )
            phase_step["status"] = "pending"
            state.pop("phase_results")
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "autopilot-state.json"], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "restore phase projection",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 0, report)

            state["phase_results"] = {
                phase_name: {
                    "status": "pending",
                    "marker_id": "us1",
                    "focused_tests": "stale result",
                    "implementation_commit": "f" * 40,
                },
                "Phase 7: Implement - Integration and Polish": {
                    "status": "pending",
                    "marker_id": "us1",
                    "focused_tests": "folded stale result",
                },
            }
            checkpoint = state["pr_marker_plan"]["markers"][0]["implementation_checkpoint"]
            checkpoint["status"] = "pending"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "autopilot-state.json"], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "stale pending phase evidence",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                f"pr_marker_plan.markers[0] phase_results[{phase_name}] focused_tests does not match checkpoint evidence",
                report["checkpoint_evidence_errors"],
            )
            self.assertIn(
                f"pr_marker_plan.markers[0] phase_results[{phase_name}] implementation_commit does not match checkpoint evidence",
                report["checkpoint_evidence_errors"],
            )
            self.assertIn(
                "pr_marker_plan.markers[0] phase_results[Phase 7: Implement - Integration and Polish] focused_tests does not match checkpoint evidence",
                report["checkpoint_evidence_errors"],
            )
            committed_evidence = evidence_path.read_bytes()
            forged_evidence = json.loads(committed_evidence)
            forged_evidence["verification"]["focused_tests"]["evidence"] = "stale result"
            forged_evidence["implementation_checkpoint_sha"] = "f" * 40
            evidence_path.write_text(json.dumps(forged_evidence), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0] checkpoint evidence differs from the authorized PR head",
                report["checkpoint_file_errors"],
            )
            self.assertIn(
                f"pr_marker_plan.markers[0] phase_results[{phase_name}] focused_tests does not match checkpoint evidence",
                report["checkpoint_evidence_errors"],
            )
            evidence_path.write_bytes(committed_evidence)

            pending_evidence = json.loads(committed_evidence)
            pending_evidence["status"] = "pending"
            pending_evidence.pop("completed_at")
            pending_evidence.update(checkpoint["freshness"])
            pending_evidence["verification"]["full_suite"] = "all pass"
            state["phase_results"][phase_name].update(
                {
                    "focused_tests": "pass",
                    "implementation_commit": implementation_commit,
                    "full_suite": "all pass",
                }
            )
            state["phase_results"]["Phase 7: Implement - Integration and Polish"][
                "focused_tests"
            ] = "pass"
            state["pr_marker_plan"]["status"] = "checkpointing"
            workflow_path.write_text(
                workflow_path.read_text(encoding="utf-8").replace(
                    "- Plan status: `emission_ready`",
                    "- Plan status: `checkpointing`",
                ),
                encoding="utf-8",
            )
            evidence_path.write_text(json.dumps(pending_evidence), encoding="utf-8")
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(
                [
                    "git", "-C", str(root), "add", str(evidence_path),
                    "autopilot-state.json", "workflow.md",
                ],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "bind valid pending phase evidence",
                ],
                check=True,
            )
            pending_evidence_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            checkpoint["checkpoint_evidence_commit_sha"] = pending_evidence_commit
            checkpoint["checkpoint_evidence_sha"] = (
                "sha256:" + hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            )
            checkpoint["verification_evidence_sha"] = (
                "sha256:" + hashlib.sha256(verification_path.read_bytes()).hexdigest()
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", "autopilot-state.json"],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "bind pending evidence authority",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 0, report)

            valid_pending_evidence_sha = checkpoint["checkpoint_evidence_sha"]
            valid_pending_evidence_commit = checkpoint[
                "checkpoint_evidence_commit_sha"
            ]
            checkpoint["checkpoint_evidence_sha"] = "sha256:" + "0" * 64
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", "autopilot-state.json"], check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "forge pending evidence digest",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0].implementation_checkpoint.checkpoint_evidence_sha",
                report["checkpoint_file_errors"],
            )

            checkpoint["checkpoint_evidence_sha"] = valid_pending_evidence_sha
            checkpoint["checkpoint_evidence_commit_sha"] = "f" * 40
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", "autopilot-state.json"], check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "forge pending evidence commit",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0].implementation_checkpoint.checkpoint_evidence_commit_sha is not an existing commit",
                report["checkpoint_evidence_errors"],
            )

            checkpoint["checkpoint_evidence_commit_sha"] = valid_pending_evidence_commit
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", "autopilot-state.json"], check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "restore pending evidence claims",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 0, report)

            typed_pending_evidence = json.loads(json.dumps(pending_evidence))
            typed_pending_evidence["verification"]["full_suite"] = 1
            state["phase_results"][phase_name]["full_suite"] = True
            evidence_path.write_text(
                json.dumps(typed_pending_evidence), encoding="utf-8",
            )
            subprocess.run(
                ["git", "-C", str(root), "add", str(evidence_path)], check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "bind JSON-distinct pending evidence",
                ],
                check=True,
            )
            typed_evidence_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            checkpoint["checkpoint_evidence_commit_sha"] = typed_evidence_commit
            checkpoint["checkpoint_evidence_sha"] = (
                "sha256:" + hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", "autopilot-state.json"], check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "bind typed pending evidence authority",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                f"pr_marker_plan.markers[0] phase_results[{phase_name}] full_suite does not match checkpoint evidence",
                report["checkpoint_evidence_errors"],
            )

            state["phase_results"][phase_name]["full_suite"] = "all pass"
            evidence_path.write_text(json.dumps(pending_evidence), encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", str(evidence_path)], check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "restore JSON-distinct pending evidence",
                ],
                check=True,
            )
            pending_evidence_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            checkpoint["checkpoint_evidence_commit_sha"] = pending_evidence_commit
            checkpoint["checkpoint_evidence_sha"] = (
                "sha256:" + hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", "autopilot-state.json"], check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "restore pending evidence authority",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 0, report)

            checkpoint["commit_sha"] = base_commit
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "autopilot-state.json"], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "mismatch pending checkpoint commit",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0] checkpoint commit_sha does not match checkpoint evidence implementation_checkpoint_sha",
                report["checkpoint_evidence_errors"],
            )

            checkpoint["commit_sha"] = "f" * 40
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "autopilot-state.json"], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "nonexistent pending checkpoint commit",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0] checkpoint commit_sha is not an existing commit",
                report["checkpoint_evidence_errors"],
            )

            unrelated_commit = subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit-tree", "HEAD^{tree}", "-m", "unrelated checkpoint commit",
                ],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            checkpoint["commit_sha"] = unrelated_commit
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "autopilot-state.json"], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "unrelated pending checkpoint commit",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0] checkpoint commit_sha is not an ancestor of the authorized PR head",
                report["checkpoint_evidence_errors"],
            )

            checkpoint["commit_sha"] = implementation_commit
            top_level_shadow = json.loads(json.dumps(pending_evidence))
            top_level_shadow["full_suite"] = "all pass"
            evidence_path.write_text(json.dumps(top_level_shadow), encoding="utf-8")
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", str(evidence_path), "autopilot-state.json"],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "shadow pending verification owner",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                f"pr_marker_plan.markers[0] phase_results[{phase_name}] full_suite has multiple checkpoint evidence owners",
                report["checkpoint_evidence_errors"],
            )

            duplicate_container = json.loads(json.dumps(pending_evidence))
            duplicate_container["verification_details"] = {"full_suite": "all pass"}
            evidence_path.write_text(json.dumps(duplicate_container), encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", str(evidence_path)], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "duplicate pending verification containers",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                f"pr_marker_plan.markers[0] phase_results[{phase_name}] full_suite has multiple checkpoint evidence owners",
                report["checkpoint_evidence_errors"],
            )

            evidence_path.write_text(json.dumps(pending_evidence), encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", str(evidence_path)], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "restore unique pending evidence owners",
                ],
                check=True,
            )
            restored_pending_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            checkpoint["checkpoint_evidence_commit_sha"] = restored_pending_commit
            checkpoint["checkpoint_evidence_sha"] = (
                "sha256:" + hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", "autopilot-state.json"],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "bind restored pending evidence authority",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 0, report)

            missing_pending_evidence = json.loads(json.dumps(pending_evidence))
            missing_pending_evidence.pop("implementation_checkpoint_sha")
            missing_pending_evidence["verification"].pop("full_suite")
            evidence_path.write_text(
                json.dumps(missing_pending_evidence), encoding="utf-8",
            )
            subprocess.run(["git", "-C", str(root), "add", str(evidence_path)], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "remove pending evidence owners",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertTrue(
                any(
                    "implementation_checkpoint_sha" in error
                    for error in report["checkpoint_evidence_errors"]
                )
            )
            self.assertIn(
                f"pr_marker_plan.markers[0] phase_results[{phase_name}] implementation_commit has no checkpoint evidence owner",
                report["checkpoint_evidence_errors"],
            )
            self.assertIn(
                f"pr_marker_plan.markers[0] phase_results[{phase_name}] full_suite has no checkpoint evidence owner",
                report["checkpoint_evidence_errors"],
            )

            evidence_path.write_bytes(committed_evidence)
            state.pop("phase_results")
            checkpoint["status"] = "complete"
            checkpoint["checkpoint_evidence_commit_sha"] = evidence_commit
            checkpoint["checkpoint_evidence_sha"] = evidence_sha
            checkpoint["verification_evidence_sha"] = verification_evidence_sha
            state["pr_marker_plan"]["status"] = "emission_ready"
            workflow_path.write_text(
                workflow_path.read_text(encoding="utf-8").replace(
                    "- Plan status: `checkpointing`",
                    "- Plan status: `emission_ready`",
                ),
                encoding="utf-8",
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(
                [
                    "git", "-C", str(root), "add", str(evidence_path),
                    "autopilot-state.json", "workflow.md",
                ],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "restore current phase evidence",
                ],
                check=True,
            )

            tracked_path.write_text("changed after verification\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "unverified content change",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "completed marker us1 file tracked.txt differs from its verified commit",
                report["changed_file_manifest_errors"],
            )
            tracked_path.write_text("changed\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "restore verified content",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 0, report)

            replacement_head = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            subprocess.run(
                ["git", "-C", str(root), "replace", replacement_head, base_commit],
                check=True,
            )
            try:
                exit_code, report = self.run_validator_paths(workflow_path, state_path)
                self.assertEqual(exit_code, 0, report)
            finally:
                subprocess.run(
                    ["git", "-C", str(root), "replace", "-d", replacement_head],
                    check=True,
                )

            clean_state_bytes = state_path.read_bytes()
            dirty_state = json.loads(clean_state_bytes)
            dirty_state["branch"] = "forged-worktree-state"
            state_path.write_text(json.dumps(dirty_state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "autopilot state differs from the authorized PR head",
                report["changed_file_manifest_errors"],
            )
            state_path.write_bytes(clean_state_bytes)
            state = json.loads(clean_state_bytes)

            clean_manifest_bytes = manifest_path.read_bytes()
            dirty_manifest = json.loads(clean_manifest_bytes)
            dirty_manifest["files"][4]["category"] = "test"
            manifest_path.write_text(json.dumps(dirty_manifest), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "changed-file manifest differs from the authorized PR head",
                report["changed_file_manifest_errors"],
            )
            manifest_path.write_bytes(clean_manifest_bytes)

            missing_authority = subprocess.run(
                [
                    sys.executable,
                    str(local_validator),
                    "--workflow",
                    str(workflow_path),
                    "--state",
                    str(state_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            missing_authority_report = json.loads(missing_authority.stdout)
            self.assertEqual(missing_authority.returncode, 1)
            self.assertTrue(
                any(
                    "requires external expected_base_commit authority" in error
                    for error in missing_authority_report["changed_file_manifest_errors"]
                )
            )
            self.assertTrue(
                any(
                    "requires external expected_head_commit authority" in error
                    for error in missing_authority_report["changed_file_manifest_errors"]
                )
            )

            stale_head_authority = subprocess.run(
                [
                    sys.executable,
                    str(local_validator),
                    "--workflow",
                    str(workflow_path),
                    "--state",
                    str(state_path),
                    "--expected-base-commit",
                    base_commit,
                    "--expected-head-commit",
                    base_commit,
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            stale_head_report = json.loads(stale_head_authority.stdout)
            self.assertEqual(stale_head_authority.returncode, 1)
            self.assertIn(
                "repository HEAD does not match external PR head authority",
                stale_head_report["changed_file_manifest_errors"],
            )

            manifest_authority_cases = (
                ("schema_version", "changed-file-manifest.v999", "schema constant"),
                ("feature_id", "OTHER-999", "feature_id does not match state authority"),
                ("comparison_ref", "BASE", "comparison_ref"),
                ("unexpected", True, "unsupported fields"),
            )
            for field, value, expected_error in manifest_authority_cases:
                with self.subTest(manifest_authority=field):
                    mutated_manifest = json.loads(json.dumps(manifest))
                    mutated_manifest[field] = value
                    manifest_path.write_text(json.dumps(mutated_manifest), encoding="utf-8")
                    mutated_sha = (
                        "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest()
                    )
                    state["current_source_fingerprint"]["changed_file_manifest_sha"] = mutated_sha
                    state["pr_marker_plan"]["source_fingerprint"][
                        "changed_file_manifest_sha"
                    ] = mutated_sha
                    state_path.write_text(json.dumps(state), encoding="utf-8")
                    exit_code, report = self.run_validator_paths(workflow_path, state_path)
                    self.assertEqual(exit_code, 1)
                    self.assertTrue(
                        any(expected_error in error for error in report["changed_file_manifest_errors"]),
                        report,
                    )

            mutated_manifest = json.loads(json.dumps(manifest))
            next(
                entry
                for entry in mutated_manifest["files"]
                if entry.get("operation") == "RENAMED"
            )["source_path"] = "wrong-source.txt"
            manifest_path.write_text(json.dumps(mutated_manifest), encoding="utf-8")
            mutated_sha = "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            state["current_source_fingerprint"]["changed_file_manifest_sha"] = mutated_sha
            state["pr_marker_plan"]["source_fingerprint"]["changed_file_manifest_sha"] = mutated_sha
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertTrue(
                any("operation/source" in error for error in report["changed_file_manifest_errors"]),
                report,
            )

            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            state["current_source_fingerprint"]["changed_file_manifest_sha"] = manifest_sha
            state["pr_marker_plan"]["source_fingerprint"]["changed_file_manifest_sha"] = manifest_sha
            state_path.write_text(json.dumps(state), encoding="utf-8")

            checkpoint = state["pr_marker_plan"]["markers"][0]["implementation_checkpoint"]
            valid_evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            valid_verification_report = json.loads(
                verification_path.read_text(encoding="utf-8")
            )
            failed_verification_report = json.loads(json.dumps(valid_verification_report))
            failed_verification_report["status"] = "fail"
            failed_verification_report["results"]["focused_tests"] = {
                "status": "fail",
                "evidence": "focused tests failed",
            }
            verification_path.write_text(
                json.dumps(failed_verification_report),
                encoding="utf-8",
            )
            failed_verification_sha = (
                "sha256:" + hashlib.sha256(verification_path.read_bytes()).hexdigest()
            )
            contradictory_evidence = json.loads(json.dumps(valid_evidence))
            contradictory_evidence["verification_evidence_sha"] = failed_verification_sha
            evidence_path.write_text(json.dumps(contradictory_evidence), encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", str(evidence_path), str(verification_path)],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "contradictory verification report",
                ],
                check=True,
            )
            contradictory_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            checkpoint["checkpoint_evidence_commit_sha"] = contradictory_commit
            checkpoint["checkpoint_evidence_sha"] = (
                "sha256:" + hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            )
            checkpoint["verification_evidence_sha"] = failed_verification_sha
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0] verification report status is invalid",
                report["checkpoint_evidence_errors"],
            )
            self.assertIn(
                "pr_marker_plan.markers[0] verification report results is invalid",
                report["checkpoint_evidence_errors"],
            )

            verification_path.write_text(
                json.dumps(valid_verification_report),
                encoding="utf-8",
            )
            evidence_path.write_text(json.dumps(valid_evidence), encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", str(evidence_path), str(verification_path)],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "restore verification report",
                ],
                check=True,
            )
            evidence_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            evidence_sha = "sha256:" + hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            checkpoint["checkpoint_evidence_commit_sha"] = evidence_commit
            checkpoint["checkpoint_evidence_sha"] = evidence_sha
            checkpoint["verification_evidence_sha"] = verification_evidence_sha
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", "autopilot-state.json"],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "bind restored verification evidence",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 0, report)

            checkpoint["verification_evidence_path"] = "late-verification.json"
            late_verification = root / "late-verification.json"
            late_verification.write_text('{"status":"pass"}\n', encoding="utf-8")
            checkpoint["verification_evidence_sha"] = (
                "sha256:" + hashlib.sha256(late_verification.read_bytes()).hexdigest()
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0].implementation_checkpoint verification evidence is absent from checkpoint commit",
                report["checkpoint_file_errors"],
            )
            checkpoint["verification_evidence_path"] = (
                "specs/spec-example/.process/verification/us1.json"
            )
            checkpoint["verification_evidence_sha"] = verification_evidence_sha
            late_verification.unlink()

            original_verification = verification_path.read_bytes()
            verification_path.write_bytes(
                original_verification + b"\nmutated after checkpoint\n"
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0].implementation_checkpoint immutable verification evidence differs from checkpoint commit",
                report["checkpoint_file_errors"],
            )
            verification_path.write_bytes(original_verification)

            evidence_tree = subprocess.run(
                ["git", "-C", str(root), "rev-parse", f"{evidence_commit}^{{tree}}"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            checkpoint["checkpoint_evidence_commit_sha"] = evidence_tree
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0].implementation_checkpoint.checkpoint_evidence_commit_sha is not an existing commit",
                report["checkpoint_evidence_errors"],
            )

            unrelated_evidence_commit = subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "commit-tree", "HEAD^{tree}",
                ],
                input="unrelated evidence commit\n",
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            checkpoint["checkpoint_evidence_commit_sha"] = unrelated_evidence_commit
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0].implementation_checkpoint.checkpoint_evidence_commit_sha is not an ancestor of HEAD",
                report["checkpoint_evidence_errors"],
            )

            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "--allow-empty", "-qm", "post-evidence head",
                ],
                check=True,
            )
            current_head = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            checkpoint["checkpoint_evidence_commit_sha"] = evidence_commit
            checkpoint["commit_sha"] = current_head
            checkpoint["head_sha"] = current_head
            state["pr_marker_plan"]["markers"][0]["reviewability"]["head_sha"] = current_head
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0] implementation commit is not an ancestor of evidence commit",
                report["checkpoint_evidence_errors"],
            )
            checkpoint["commit_sha"] = implementation_commit
            checkpoint["head_sha"] = implementation_commit
            state["pr_marker_plan"]["markers"][0]["reviewability"][
                "head_sha"
            ] = implementation_commit

            valid_evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            failed_evidence = json.loads(json.dumps(valid_evidence))
            failed_evidence["verification"]["focused_tests"] = {
                "status": "failed",
                "evidence": "focused tests failed",
            }
            evidence_path.write_text(json.dumps(failed_evidence), encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", str(evidence_path)], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "failed verification evidence",
                ],
                check=True,
            )
            failed_evidence_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            checkpoint["checkpoint_evidence_commit_sha"] = failed_evidence_commit
            checkpoint["checkpoint_evidence_sha"] = (
                "sha256:" + hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0] checkpoint evidence verification is invalid",
                report["checkpoint_evidence_errors"],
            )

            pending_evidence = json.loads(json.dumps(valid_evidence))
            pending_evidence["status"] = "pending"
            pending_evidence.pop("completed_at")
            evidence_path.write_text(json.dumps(pending_evidence), encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", str(evidence_path)], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "pending evidence",
                ],
                check=True,
            )
            pending_evidence_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            checkpoint["checkpoint_evidence_commit_sha"] = pending_evidence_commit
            checkpoint["checkpoint_evidence_sha"] = (
                "sha256:" + hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0] checkpoint evidence status is invalid",
                report["checkpoint_evidence_errors"],
            )

            evidence_path.write_text(json.dumps(valid_evidence), encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", str(evidence_path)], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "restore complete evidence",
                ],
                check=True,
            )
            evidence_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            checkpoint["checkpoint_evidence_commit_sha"] = evidence_commit
            checkpoint["checkpoint_evidence_sha"] = evidence_sha
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", "autopilot-state.json"],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "bind restored complete evidence",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 0, report)

            unrelated_commit = subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "-c",
                    "user.name=SpecKit Tests",
                    "-c",
                    "user.email=git@github.com",
                    "commit-tree",
                    f"{base_commit}^{{tree}}",
                ],
                input="unrelated manifest base\n",
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            manifest["base_commit"] = unrelated_commit
            state["changed_file_manifest_base_commit"] = unrelated_commit
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            unrelated_manifest_sha = "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            state["current_source_fingerprint"]["changed_file_manifest_sha"] = unrelated_manifest_sha
            state["pr_marker_plan"]["source_fingerprint"]["changed_file_manifest_sha"] = unrelated_manifest_sha
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "changed-file manifest base_commit does not match external PR base authority",
                report["changed_file_manifest_errors"],
            )

            manifest["base_commit"] = base_commit
            state["changed_file_manifest_base_commit"] = unrelated_commit
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            state["current_source_fingerprint"]["changed_file_manifest_sha"] = manifest_sha
            state["pr_marker_plan"]["source_fingerprint"]["changed_file_manifest_sha"] = manifest_sha
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "changed-file manifest base_commit does not match state authority",
                report["changed_file_manifest_errors"],
            )
            state["changed_file_manifest_base_commit"] = base_commit
            state_path.write_text(json.dumps(state), encoding="utf-8")

            checkpoint = state["pr_marker_plan"]["markers"][0]["implementation_checkpoint"]
            checkpoint["commit_sha"] = evidence_commit
            checkpoint["head_sha"] = evidence_commit
            state["pr_marker_plan"]["markers"][0]["reviewability"]["head_sha"] = evidence_commit
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0] checkpoint/evidence implementation commit mismatch",
                report["checkpoint_evidence_errors"],
            )

            missing_commit = "f" * 40
            checkpoint["commit_sha"] = missing_commit
            checkpoint["head_sha"] = missing_commit
            state["pr_marker_plan"]["markers"][0]["reviewability"]["head_sha"] = missing_commit
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0].implementation_checkpoint.commit_sha is not an existing commit",
                report["checkpoint_evidence_errors"],
            )

            checkpoint["commit_sha"] = unrelated_commit
            checkpoint["head_sha"] = unrelated_commit
            state["pr_marker_plan"]["markers"][0]["reviewability"]["head_sha"] = unrelated_commit
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0].implementation_checkpoint.commit_sha is not an ancestor of HEAD",
                report["checkpoint_evidence_errors"],
            )

            checkpoint["commit_sha"] = base_commit
            checkpoint["head_sha"] = base_commit
            state["pr_marker_plan"]["markers"][0]["reviewability"]["head_sha"] = base_commit
            state_path.write_text(json.dumps(state), encoding="utf-8")

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

            tracked_manifest_entry["category"] = "test"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "current_source_fingerprint.changed_file_manifest_sha does not match the changed-file manifest",
                report["changed_file_manifest_errors"],
            )
            tracked_manifest_entry["category"] = "implementation"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            tracked_manifest_entry["operation"] = "NEW"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertTrue(
                any(
                    error.startswith("declared changed-file manifest does not match ")
                    for error in report["changed_file_manifest_errors"]
                ),
                report,
            )
            self.assertIn(
                "pr_marker_plan marker us1 operation/source for tracked.txt does not match changed-file manifest",
                report["changed_file_manifest_errors"],
            )

            tracked_manifest_entry["operation"] = "MODIFIED"
            tracked_manifest_entry["marker_ids"] = ["us2"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan marker ownership for tracked.txt does not match changed-file manifest",
                report["changed_file_manifest_errors"],
            )

            tracked_manifest_entry["marker_ids"] = ["us1", "us2"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "changed-file manifest schema: "
                f"changed_file_manifest.files[{tracked_manifest_index}].marker_ids has too many items",
                report["changed_file_manifest_errors"],
            )

            tracked_manifest_entry["marker_ids"] = ["us1"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            tasks_path.write_text(
                "# Tasks\n\n- [x] T001 Marker task\n- [ ] T002 Changed folded task\n",
                encoding="utf-8",
            )
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
            evidence_path.write_bytes(committed_evidence)

            subprocess.run(
                ["git", "-C", str(root), "add", str(tasks_path)], check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "update completed marker scope",
                ],
                check=True,
            )
            replacement_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            replacement_evidence_path = (
                root / "specs/spec-example/.process/checkpoints/us1-current.json"
            )
            replacement_verification_path = (
                root / "specs/spec-example/.process/verification/us1-current.json"
            )
            replacement_tasks_sha = (
                "sha256:" + hashlib.sha256(tasks_path.read_bytes()).hexdigest()
            )
            replacement_marker_sha = "sha256:" + hashlib.sha256(
                b"- [x] T001 Marker task\n- [ ] T002 Changed folded task\n"
            ).hexdigest()
            replacement_verification_results = json.loads(
                json.dumps(verification_results)
            )
            replacement_verification_results[
                "independent_critical_high_review"
            ]["evidence"] = (
                "independent review clean at "
                f"{replacement_commit}"
            )
            replacement_verification_path.write_text(
                json.dumps(
                    {
                        "schema_version": "verification-report.v1",
                        "feature_id": "SPEC-EXAMPLE",
                        "marker_id": "us1",
                        "status": "pass",
                        "generated_at": "2026-07-20T00:00:00Z",
                        "verified_commit_sha": replacement_commit,
                        "required_gate_ids": verification_gate_ids,
                        "results": replacement_verification_results,
                    }
                ),
                encoding="utf-8",
            )
            replacement_verification_sha = (
                "sha256:"
                + hashlib.sha256(replacement_verification_path.read_bytes()).hexdigest()
            )
            replacement_evidence_path.write_text(
                json.dumps(
                    {
                        "schema_version": "marker-checkpoint.v1",
                        "feature_id": "SPEC-EXAMPLE",
                        "marker_id": "us1",
                        "status": "complete",
                        "task_ids": ["T001", "T002"],
                        "implementation_checkpoint_sha": replacement_commit,
                        "last_reviewed_head_sha": replacement_commit,
                        "verification": replacement_verification_results,
                        "verification_evidence_sha": replacement_verification_sha,
                        "required_verification_gate_ids": verification_gate_ids,
                        "source_fingerprint_status": "current",
                        "tasks_sha": replacement_tasks_sha,
                        "completed_at": "2026-07-20T00:00:00Z",
                    }
                ),
                encoding="utf-8",
            )
            replacement_evidence_sha = (
                "sha256:"
                + hashlib.sha256(replacement_evidence_path.read_bytes()).hexdigest()
            )
            checkpoint = state["pr_marker_plan"]["markers"][0][
                "implementation_checkpoint"
            ]
            checkpoint.update(
                {
                    "evidence_path": "specs/spec-example/.process/checkpoints/us1-current.json",
                    "checkpoint_evidence_sha": replacement_evidence_sha,
                    "checkpoint_evidence_commit_sha": "pending replacement evidence commit",
                    "verification_evidence_path": "specs/spec-example/.process/verification/us1-current.json",
                    "verification_evidence_sha": replacement_verification_sha,
                    "commit_sha": replacement_commit,
                    "head_sha": replacement_commit,
                    "completed_at": "2026-07-20T00:00:00Z",
                    "freshness": {
                        "source_fingerprint_status": "current_marker_scope",
                        "source_fingerprint_contract": "marker-task-lines.v2",
                        "tasks_sha_scope": "checkpoint_time_whole_file",
                        "current_tasks_sha": replacement_tasks_sha,
                        "checkpoint_marker_tasks_sha": replacement_marker_sha,
                        "current_marker_tasks_sha": replacement_marker_sha,
                        "validated_at": "2026-07-20T00:00:00Z",
                    },
                    "superseded_evidence": {
                        "evidence_path": "specs/spec-example/.process/checkpoints/us1.json",
                        "checkpoint_evidence_commit_sha": evidence_commit,
                        "checkpoint_evidence_sha": evidence_sha,
                        "implementation_checkpoint_sha": implementation_commit,
                        "corrections": [],
                    },
                }
            )
            state["pr_marker_plan"]["markers"][0]["reviewability"][
                "head_sha"
            ] = replacement_commit
            for path in (
                "specs/spec-example/tasks.md",
                "specs/spec-example/.process/checkpoints/us1-current.json",
                "specs/spec-example/.process/verification/us1-current.json",
            ):
                operation = "MODIFIED" if path.endswith("tasks.md") else "NEW"
                state["pr_marker_plan"]["markers"][0]["declared_files"].append(
                    {"path": path, "operation": operation}
                )
                manifest["files"].append(
                    {
                        "path": path,
                        "operation": operation,
                        "category": "process",
                        "provenance": "authored",
                        "marker_ids": ["us1"],
                    }
                )
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            replacement_manifest_sha = (
                "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            )
            for target in (
                state["current_source_fingerprint"],
                state["pr_marker_plan"]["source_fingerprint"],
            ):
                target["tasks_sha"] = replacement_tasks_sha
                target["changed_file_manifest_sha"] = replacement_manifest_sha
            workflow_path.write_text(
                workflow_path.read_text(encoding="utf-8")
                .replace(implementation_commit, replacement_commit)
                .replace(tasks_sha, replacement_tasks_sha)
                .replace(manifest_sha, replacement_manifest_sha),
                encoding="utf-8",
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(
                [
                    "git", "-C", str(root), "add", "autopilot-state.json",
                    "workflow.md", "changed-file-manifest.json",
                    str(replacement_evidence_path),
                    str(replacement_verification_path),
                ],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "record replacement checkpoint evidence",
                ],
                check=True,
            )
            replacement_evidence_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            checkpoint["checkpoint_evidence_commit_sha"] = replacement_evidence_commit
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", "autopilot-state.json"], check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "bind replacement checkpoint authority",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 0, report)
            self.assertEqual(report["checkpoint_source_fingerprint_errors"], [])

            reviewed_tracked_bytes = tracked_path.read_bytes()
            tracked_path.write_text("unreviewed change\n", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", str(tracked_path)], check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "unreviewed non-carrier change",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0] unreviewed non-carrier path after independent review: tracked.txt",
                report["checkpoint_evidence_errors"],
            )

            tracked_path.write_bytes(reviewed_tracked_bytes)
            subprocess.run(
                ["git", "-C", str(root), "add", str(tracked_path)], check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "restore reviewed non-carrier content",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 0, report)

            checkpoint["superseded_evidence"]["implementation_checkpoint_sha"] = (
                "f" * 40
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0].implementation_checkpoint.superseded_evidence identity does not match marker state",
                report["checkpoint_evidence_errors"],
            )
            checkpoint["superseded_evidence"]["implementation_checkpoint_sha"] = (
                implementation_commit
            )

            checkpoint["corrections"] = []
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0].implementation_checkpoint must not declare both corrections and superseded_evidence",
                report["checkpoint_evidence_errors"],
            )
            checkpoint.pop("corrections")

            correction_path = (
                root
                / "specs/spec-example/.process/checkpoint-corrections/us1-001.json"
            )
            correction_path.parent.mkdir(parents=True, exist_ok=True)
            correction_path.write_text(
                json.dumps(
                    {
                        "schema_version": "marker-checkpoint-correction.v1",
                        "feature_id": "SPEC-EXAMPLE",
                        "marker_id": "us1",
                        "sequence": 1,
                        "supersedes_evidence_path": "specs/spec-example/.process/checkpoints/us1.json",
                        "supersedes_evidence_commit_sha": evidence_commit,
                        "supersedes_evidence_sha": evidence_sha,
                        "remove_evidence_owners": [1],
                        "reason": "Exercise correction chronology.",
                    }
                ),
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "-C", str(root), "add", str(correction_path)], check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "late historical correction",
                ],
                check=True,
            )
            correction_commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            correction_sha = (
                "sha256:" + hashlib.sha256(correction_path.read_bytes()).hexdigest()
            )
            checkpoint["superseded_evidence"]["corrections"] = [
                {
                    "sequence": 1,
                    "evidence_path": "specs/spec-example/.process/checkpoint-corrections/us1-001.json",
                    "checkpoint_evidence_commit_sha": correction_commit,
                    "checkpoint_evidence_sha": correction_sha,
                    "supersedes_evidence_path": "specs/spec-example/.process/checkpoints/us1.json",
                    "supersedes_evidence_commit_sha": evidence_commit,
                    "supersedes_evidence_sha": evidence_sha,
                }
            ]
            state_path.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", "autopilot-state.json"], check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "declare late historical correction",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0].implementation_checkpoint.superseded_evidence correction chain does not strictly precede the current checkpoint evidence",
                report["checkpoint_evidence_errors"],
            )

            checkpoint["superseded_evidence"]["corrections"][0][
                "checkpoint_evidence_commit_sha"
            ] = evidence_commit
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0].implementation_checkpoint.corrections[0] does not strictly descend from the superseded evidence commit",
                report["checkpoint_evidence_errors"],
            )

            checkpoint["superseded_evidence"]["corrections"][0][
                "checkpoint_evidence_commit_sha"
            ] = replacement_evidence_commit
            state_path.write_text(json.dumps(state), encoding="utf-8")
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0].implementation_checkpoint.superseded_evidence correction chain does not strictly precede the current checkpoint evidence",
                report["checkpoint_evidence_errors"],
            )

            checkpoint["superseded_evidence"]["corrections"][0][
                "checkpoint_evidence_commit_sha"
            ] = correction_commit
            state_path.write_text(json.dumps(state), encoding="utf-8")
            checkpoint_schema_path.write_text("{", encoding="utf-8")
            subprocess.run(
                [
                    "git", "-C", str(root), "add", "autopilot-state.json",
                    str(checkpoint_schema_path),
                ],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=SpecKit Tests",
                    "-c", "user.email=git@github.com", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "malformed correction schema authority",
                ],
                check=True,
            )
            exit_code, report = self.run_validator_paths(workflow_path, state_path)
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "pr_marker_plan.markers[0].implementation_checkpoint.corrections[0] schema authority is unavailable",
                report["checkpoint_evidence_errors"],
            )

    def test_v2_marker_plan_requires_changed_file_manifest_reference(self) -> None:
        state = self.projected_state(
            plan_status="in_progress",
            phase_status="in_progress",
            checkpoint={"status": "pending"},
        )
        state["pr_marker_plan"]["status"] = "checkpointing"
        state.pop("changed_file_manifest", None)
        state.pop("current_source_fingerprint", None)
        state["pr_marker_plan"].pop("source_fingerprint", None)
        exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(exit_code, 1)
        self.assertEqual(
            report["changed_file_manifest_errors"],
            ["pr-marker-plan.v2 requires a changed_file_manifest reference"],
        )

    def test_v2_marker_plan_requires_complete_closed_shape(self) -> None:
        state = self.projected_state(
            plan_status="in_progress",
            phase_status="in_progress",
            checkpoint={"status": "pending"},
        )
        state["pr_marker_plan"].pop("status")
        marker = state["pr_marker_plan"]["markers"][0]
        marker.pop("implementation_checkpoint")
        marker["unexpected"] = True
        exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(exit_code, 1)
        self.assertIn(
            "pr_marker_plan is missing required fields: status",
            report["marker_plan_status_errors"],
        )
        self.assertTrue(any(
            "implementation_checkpoint" in error and "missing required fields" in error
            for error in report["marker_plan_status_errors"]
        ))
        self.assertTrue(any(
            "unsupported fields: unexpected" in error
            for error in report["marker_plan_status_errors"]
        ))

    def test_v2_marker_plan_enforces_every_nested_schema_contract(self) -> None:
        state = self.projected_state(
            plan_status="in_progress",
            phase_status="in_progress",
            checkpoint={"status": "pending"},
        )
        state["pr_marker_plan"]["source_fingerprint"] = {
            "changed_file_manifest_sha": "sha256:" + "a" * 64,
        }
        marker = state["pr_marker_plan"]["markers"][0]
        marker["declared_tests"] = [False]
        marker["reviewability"] = {}
        marker["subdivision"] = {}
        marker["warnings"] = [{}]
        exit_code, report = self.run_validator(workflow_text(), state)
        self.assertEqual(exit_code, 1)
        errors = report["marker_plan_status_errors"]
        self.assertTrue(any(
            "source_fingerprint is missing required fields" in error
            for error in errors
        ))
        self.assertTrue(any(
            "declared_tests[0] has the wrong schema type" in error
            for error in errors
        ))
        self.assertTrue(any(
            "reviewability is missing required fields" in error
            for error in errors
        ))
        self.assertTrue(any(
            "subdivision is missing required fields" in error
            for error in errors
        ))
        self.assertTrue(any(
            "warnings[0] is missing required fields" in error
            for error in errors
        ))

    def test_marker_plan_rejects_missing_or_unsupported_schema_version(self) -> None:
        for version in (None, "pr-marker-plan.v3"):
            with self.subTest(version=version):
                state = self.projected_state(
                    plan_status="in_progress",
                    phase_status="in_progress",
                    checkpoint={"status": "pending"},
                )
                if version is None:
                    state["pr_marker_plan"].pop("schema_version")
                else:
                    state["pr_marker_plan"]["schema_version"] = version
                exit_code, report = self.run_validator(workflow_text(), state)
                self.assertEqual(exit_code, 1)
                self.assertIn(
                    "pr_marker_plan.schema_version must be pr-marker-plan.v1 or pr-marker-plan.v2",
                    report["marker_plan_status_errors"],
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

    def test_duplicate_state_authority_keys_are_input_errors(self) -> None:
        base = json.dumps(state_json())[:-1]
        duplicates = (
            ', "pr_marker_plan": {"schema_version": "pr-marker-plan.v2", '
            '"schema_version": "pr-marker-plan.v1"}}',
            ', "changed_file_manifest": "first.json", '
            '"changed_file_manifest": "second.json"}',
        )
        for duplicate in duplicates:
            with self.subTest(duplicate=duplicate):
                exit_code, report = self.run_validator(
                    workflow_text(), base + duplicate,
                )
                self.assertEqual(exit_code, 2)
                self.assertEqual(report["status"], "input_error")
                self.assertIn("duplicate JSON key", report["message"])

    def test_non_finite_state_numbers_are_input_errors(self) -> None:
        base = json.dumps(state_json())[:-1]
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                exit_code, report = self.run_validator(
                    workflow_text(), f'{base}, "task_ids": [{constant}]}}',
                )
                self.assertEqual(exit_code, 2)
                self.assertEqual(report["status"], "input_error")
                self.assertIn("non-finite JSON number", report["message"])

    def test_excessively_nested_state_is_input_error(self) -> None:
        nested = "[" * 4096 + "0" + "]" * 4096
        exit_code, report = self.run_validator(
            workflow_text(), f'{{"plan": {nested}}}',
        )
        self.assertEqual(exit_code, 2)
        self.assertEqual(report["status"], "input_error")
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
