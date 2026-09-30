#!/usr/bin/env python3
"""Autonomy-boundary contracts: the source guidance and the receipt validation that
bind an autopilot run to the boundary its operator authorized.

Python 3.11+ standard library only.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
LIB_DIR = TEST_DIR.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from autopilot_bookkeeping_support import (
    PHRASES,
    VALIDATOR,
    _CodexGuides,
    _assert_absent,
    _assert_phrases,
    _autonomy_boundary_state,
    _autonomy_errors,
    _current_execution_boundary,
    validator,
    workflow,
)  # noqa: E402
from test_result import run_counted  # noqa: E402


def _refresh_action_scope(action: dict) -> None:
    action["scope_sha256"] = validator._canonical_json_sha256({
        key: action[key]
        for key in (
            "category",
            "command_or_tool",
            "target",
            "effect",
            "execution_boundary_sha256",
        )
    })


class AutonomyBoundarySourceContractTests(_CodexGuides):
    SECTIONS = {
        "preflight": ("phase", "### Autonomy Boundary Preflight", "1. Read mode from `CONFIDENCE_GATE_MODE`"),
        "inventory": ("phase", "### Autonomy Boundary Preflight", "For each action, record its category"),
        "resume": ("prerequisites", "### 0.8c Resumed Autonomy Boundary Preflight", "### 0.9"),
    }

    def test_source_contract_places_preflight_before_every_phase_seven_entry(self) -> None:
        phase = self.phase
        boundary = phase.index("### Autonomy Boundary Preflight")
        confidence = phase.index("1. Read mode from `CONFIDENCE_GATE_MODE`", boundary)
        self.assertLess(boundary, confidence)
        self.assertLess(confidence, phase.index("## Phase 7: Implement"))
        _assert_phrases(self, phase, (
            "Autonomy Boundary Preflight, G6.5 confidence gate",
            "A `plan` run",
            "An `implement` or `full` run",
            "before its first Phase 7 dispatch",
            "Exact explicit user authorization persists",
            "no later user instruction revokes or narrows it",
        ))
        _assert_phrases(self, self.prerequisites, ("Prior execution", "automatic review", "older task crossed the boundary"))
        self.assertIn("`autonomy_boundary` record", self.skill)
        for flag in PHRASES["AutonomyBoundarySourceContractTests.test_source_contract_places_preflight_before_every_phase_seven_entry#1"]:
            self.assertIn(flag, self.skill)
            self.assertIn(flag, phase)

    def test_resume_inventory_and_request_sections_carry_their_rules(self) -> None:
        """Resume re-attests a stale boundary (issue 747), the inventory names model-service egress (issue 748),
        and the one operator request carries a paste-ready authorization plus an extra policy (issue 755)."""
        for attribute, key in (
            ("resume", "test_resume_re_attests_a_stale_boundary_before_the_coverage_guard"),
            ("inventory", "test_preflight_inventories_data_egress_to_model_services"),
            ("preflight", "test_consolidated_request_emits_egress_authorization_and_extra_policy"),
        ):
            _assert_phrases(self, getattr(self, attribute), PHRASES[f"AutonomyBoundarySourceContractTests.{key}#1"])
        _assert_phrases(self, self.skill, (
            "at any stage", "before the Step 1.1 coverage guard", "data egress to a model service",
            "paste-ready authorization message", "`auto_review.extra_policy`",
        ))
        _assert_phrases(self, self.phase, ("every data-egress destination and data class", "is not egress authorization", "Step 0.8c"))
        self.assertIn("paste-ready authorization message", self.prerequisites)

    def test_canonical_schema_excludes_automatic_and_prior_execution_authorization(self) -> None:
        schema = json.loads(
            validator.AUTONOMY_BOUNDARY_SCHEMA_PATH.read_text(
                encoding="utf-8"
            )
        )
        statuses = schema["$defs"]["authorization"]["properties"]["status"]["enum"]
        _assert_phrases(self, statuses, ("explicit_user", "revoked"))
        _assert_absent(self, statuses, ("auto_review", "prior_execution"))


class AutonomyBoundaryAuthorizationTests(unittest.TestCase):
    def test_matching_explicit_authorization_remains_valid_on_resume(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            state = _autonomy_boundary_state(root)

            self.assertEqual(
                _autonomy_errors(state, root),
                [],
            )
            resumed = json.loads(json.dumps(state))
            self.assertEqual(
                _autonomy_errors(resumed, root),
                [],
            )


class AutonomyBoundaryFreshnessTests(unittest.TestCase):
    def test_writable_roots_are_sorted_strings_and_malformed_input_never_crashes(self) -> None:
        for roots, expected in (
            (["/z", "/a"], "deterministic sorted order"),
            (["/a", 1], "must contain absolute paths"),
        ):
            with self.subTest(roots=roots), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                state = _autonomy_boundary_state(root)
                execution = state["autonomy_boundary"]["execution_boundary"]
                execution["writable_roots"] = roots
                errors = _autonomy_errors(state, root)
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_changed_scope_and_stale_planning_bytes_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            state = _autonomy_boundary_state(root)
            action = state["autonomy_boundary"]["actions"][0]
            action["target"] = "/opt/other"
            _refresh_action_scope(action)
            errors = _autonomy_errors(state, root)
            self.assertTrue(any("authorization.scope_sha256" in error for error in errors), errors)

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            state = _autonomy_boundary_state(root)
            boundary = state["autonomy_boundary"]
            execution = boundary["execution_boundary"]
            execution["writable_roots"] = ["/different/root"]
            execution["sha256"] = validator._canonical_json_sha256({
                key: execution[key]
                for key in (
                    "execution_environment",
                    "sandbox_mode",
                    "approval_reviewer",
                    "writable_roots",
                )
            })
            action = boundary["actions"][0]
            action["execution_boundary_sha256"] = execution["sha256"]
            _refresh_action_scope(action)
            errors = _autonomy_errors(state, root)
            self.assertTrue(any("authorization.scope_sha256" in error for error in errors), errors)

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            state = _autonomy_boundary_state(root)
            (root / "specs/demo/plan.md").write_text("# Changed plan\n", encoding="utf-8")
            errors = _autonomy_errors(state, root)
            self.assertTrue(any("plan_md" in error for error in errors), errors)

    def test_unchanged_record_is_stale_under_a_different_current_execution_boundary(self) -> None:
        for field, value in (
            ("sandbox_mode", "read-only"),
            ("approval_reviewer", "user"),
            ("writable_roots", ["/different/root"]),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                state = _autonomy_boundary_state(root)
                current = _current_execution_boundary(root)
                current[field] = value
                errors = validator.validate_autonomy_boundary(
                    state,
                    root,
                    current_execution_boundary=current,
                    require_boundary=True,
                )["autonomy_boundary_errors"]
                self.assertTrue(
                    any("current execution boundary" in error for error in errors),
                    errors,
                )

    def test_required_boundary_fails_closed_when_current_surface_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            state = _autonomy_boundary_state(root)
            errors = validator.validate_autonomy_boundary(
                state,
                root,
                current_execution_boundary=None,
                require_boundary=True,
            )["autonomy_boundary_errors"]
            self.assertTrue(any("current execution boundary" in error for error in errors), errors)


class AutonomyBoundaryMalformedExecutionTests(unittest.TestCase):
    def test_non_serializable_execution_boundary_does_not_cascade_digest_errors(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            state = _autonomy_boundary_state(root)
            boundary = state["autonomy_boundary"]
            boundary["execution_boundary"]["execution_environment"] = object()
            action = boundary["actions"][0]
            action["target"] = "/opt/other"

            errors = _autonomy_errors(state, root)

        self.assertEqual(
            [error for error in errors if "execution_boundary sha256" in error],
            [],
            errors,
        )
        self.assertEqual(
            [
                error
                for error in errors
                if "execution_boundary scope cannot be canonicalized/serialized for sha256" in error
            ],
            [
                "autonomy boundary execution_boundary scope cannot be canonicalized/serialized for sha256"
            ],
            errors,
        )
        self.assertFalse(
            any("current execution boundary does not match" in error for error in errors),
            errors,
        )
        self.assertFalse(
            any("execution_boundary_sha256 is stale" in error for error in errors),
            errors,
        )
        self.assertTrue(any("scope_sha256 does not match its action scope" in error for error in errors), errors)
        self.assertTrue(any("authorization.scope_sha256 does not match its action scope" in error for error in errors), errors)


class AutonomyBoundaryNegativeAuthorizationTests(unittest.TestCase):
    def test_automatic_review_and_prior_execution_are_not_authorization(self) -> None:
        for status in ("auto_review", "prior_execution", "not_required"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                state = _autonomy_boundary_state(root)
                state["autonomy_boundary"]["actions"][0]["authorization"]["status"] = status
                errors = _autonomy_errors(state, root)
                self.assertTrue(any("authorization" in error for error in errors), errors)

    def test_revocation_forces_operator_action_required(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            state = _autonomy_boundary_state(root)
            boundary = state["autonomy_boundary"]
            action = boundary["actions"][0]
            boundary["status"] = "operator_action_required"
            action["disposition"] = "operator_action_required"
            authorization = action["authorization"]
            authorization["status"] = "revoked"
            authorization["revocation_evidence"] = "a later user instruction revoked authorization"
            self.assertEqual(
                _autonomy_errors(state, root),
                [],
            )

            state["autonomy_boundary"]["status"] = "ready"
            errors = _autonomy_errors(state, root)
            self.assertTrue(any("status" in error for error in errors), errors)


class AutonomyBoundaryStageTests(unittest.TestCase):
    def test_reachability_requires_boundary_independent_of_optional_run_status(self) -> None:
        cases = (
            ("plan", "pending", "in_progress", False),
            ("plan", "in_progress", "in_progress", True),
            ("implement", "completed", None, True),
            ("implement", "completed", "completed", True),
            ("full", "pending", "in_progress", False),
            ("full", "completed", "in_progress", True),
        )
        for stage, phase_65_status, run_status, required in cases:
            with self.subTest(stage=stage, phase_65_status=phase_65_status, run_status=run_status):
                state = {
                    "stage": stage,
                    "plan": [
                        {"step": "Phase 6.5: Confidence Gate", "status": phase_65_status},
                        {"step": "Phase 7: Implement", "status": "pending"},
                    ],
                }
                if run_status is not None:
                    state["status"] = run_status
                errors = validator.validate_autonomy_boundary(
                    state,
                    Path("."),
                    current_execution_boundary=_current_execution_boundary(Path(".")),
                    require_boundary=True,
                )["autonomy_boundary_errors"]
                self.assertEqual(bool(errors), required, errors)


class AutonomyBoundaryCliTests(unittest.TestCase):
    def test_root_level_workflow_uses_its_nested_repository_for_planning_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            outer = Path(raw)
            (outer / ".git").mkdir()
            root = outer / "nested"
            root.mkdir()
            (root / ".git").mkdir()
            workflow_path = root / "workflow.md"
            workflow_path.write_text(
                workflow(("Specify", "✅ Complete"), body="G1 gate: PASS"),
                encoding="utf-8",
            )
            state_path = root / "autopilot-state.json"
            state = _autonomy_boundary_state(root)
            state["workflow_file"] = "workflow.md"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            report = validator.build_report(
                workflow_path,
                state_path,
                authority=validator.ReportAuthority(
                    current_execution_boundary=_current_execution_boundary(root),
                    require_autonomy_boundary=True,
                ),
            )

        self.assertEqual(report["autonomy_boundary_errors"], [], report)

    def test_cli_rejects_a_valid_record_under_a_different_current_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            workflow_path = root / "workflow.md"
            workflow_path.write_text(
                workflow(("Specify", "✅ Complete"), body="G1 gate: PASS"),
                encoding="utf-8",
            )
            state_path = root / "autopilot-state.json"
            state = _autonomy_boundary_state(root)
            state["workflow_file"] = str(workflow_path)
            state_path.write_text(json.dumps(state), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable, str(VALIDATOR),
                    "--workflow", str(workflow_path), "--state", str(state_path),
                    "--require-autonomy-boundary",
                    "--current-execution-environment", "local",
                    "--current-sandbox-mode", "workspace-write",
                    "--current-approval-reviewer", "auto_review",
                    "--current-writable-root", "/different/root",
                    "--rule", "status-evidence",
                ],
                text=True, capture_output=True, check=False,
            )
            report = json.loads(completed.stdout)

        self.assertEqual(completed.returncode, 1, report)
        self.assertTrue(
            any(
                "current execution boundary" in error
                for error in report["autonomy_boundary_errors"]
            ),
            report,
        )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-autopilot-autonomy-boundary"))
