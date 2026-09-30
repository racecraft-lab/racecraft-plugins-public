#!/usr/bin/env python3
"""Standing-policy preflight and run-start authorization guidance for both hosts.

Python 3.11+ standard library only.
"""

from __future__ import annotations

import tempfile
import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
LIB_DIR = TEST_DIR.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from autopilot_bookkeeping_support import (
    BLOCKED_ACTION_HEADING,
    CLAUDE_AUTOPILOT_SKILL,
    CODEX_AUTOPILOT_SKILL,
    PHRASES,
    SKILL_DIR,
    _CodexGuides,
    _assert_absent,
    _assert_phrases,
    _autonomy_boundary_state,
    _autonomy_errors,
    _flat,
)  # noqa: E402
from test_result import run_counted  # noqa: E402


class _ClaudeGuides(_CodexGuides):
    HOST_SKILL = CLAUDE_AUTOPILOT_SKILL
    PREREQUISITES = "prerequisites.md"
    PHASE = "phase-execution.md"


class StandingPolicyPreflightSourceContractTests(_CodexGuides):
    """A ratified plan's ordinary work needs no up-front question (issue 764)."""

    SECTIONS = {
        "preflight": ("phase", "### Autonomy Boundary Preflight", "1. Read mode from `CONFIDENCE_GATE_MODE`"),
        "resume": ("prerequisites", "## Step 0.8c: Resumed Autonomy Boundary Preflight", "## Step 0.9"),
    }

    def test_covered_inventory_asks_no_question_including_a_stage_change(self) -> None:
        for phrase in PHRASES["StandingPolicyPreflightSourceContractTests.test_covered_inventory_asks_no_question_including_a_stage_change#1"]:
            self.assertIn(phrase, self.preflight)
        for phrase in ("asks no question", "planning-to-implementation stage change"):
            self.assertIn(phrase, self.resume)
        self.assertNotIn("A denial or no answer stops the run", self.resume)
        _assert_phrases(self, self.skill, ("standing policy", "asks no question"))
        self.assertNotIn("re-attest it with one operator request up front", self.skill)

    def test_uncovered_destination_is_deferred_to_the_end_of_run_request(self) -> None:
        for phrase in (
            "a new destination or data class",
            "never an up-front question",
            "the one end-of-run request",
            BLOCKED_ACTION_HEADING,
        ):
            self.assertIn(phrase, self.preflight)
        self.assertNotIn("STOP before Phase 7", self.preflight)
        self.assertNotIn("A blocked result stops before Phase 7", self.skill)
        self.assertIn("never an up-front question", self.resume)

    def test_uncovered_plan_derived_egress_is_asked_as_a_chat_reply(self) -> None:
        for phrase in PHRASES["StandingPolicyPreflightSourceContractTests.test_uncovered_plan_derived_egress_is_asked_as_a_chat_reply#1"]:
            self.assertIn(phrase, self.preflight)
        self.assertIn("never as a goal edit", self.skill)

    def test_reviewer_policy_change_reaches_only_new_threads(self) -> None:
        phrase = "reaches only threads started after the change"
        _assert_phrases(self, self.preflight, (phrase, "even after an app restart"))
        for setup in ("speckit-install", "speckit-upgrade"):
            with self.subTest(setup=setup):
                self.assertIn(phrase, _flat(CODEX_AUTOPILOT_SKILL.parents[1] / setup / "SKILL.md"))

    def test_ratified_boundary_file_edit_is_deferred_not_a_start_blocker(self) -> None:
        for phrase in PHRASES["StandingPolicyPreflightSourceContractTests.test_ratified_boundary_file_edit_is_deferred_not_a_start_blocker#1"]:
            self.assertIn(phrase, self.preflight)

    def test_missing_standing_policy_is_the_single_up_front_ask_not_a_setup_gap(self) -> None:
        for phrase in PHRASES["StandingPolicyPreflightSourceContractTests.test_missing_standing_policy_is_the_single_up_front_ask_not_a_setup_gap#1"]:
            self.assertIn(phrase, self.preflight)
        for text in (self.preflight, self.skill):
            _assert_absent(self, text, ("setup gap", "The run still proceeds"))
        for setup in ("speckit-install", "speckit-upgrade"):
            with self.subTest(setup=setup):
                text = _flat(CODEX_AUTOPILOT_SKILL.parents[1] / setup / "SKILL.md")
                _assert_phrases(self, text, PHRASES["StandingPolicyPreflightSourceContractTests.test_missing_standing_policy_is_the_single_up_front_ask_not_a_setup_gap#2"])


class CodexRunStartAuthorizationSourceContractTests(_CodexGuides):
    """Codex settles permissions and egress once, before Phase 1 (issue 833)."""

    SECTIONS = {
        "step": ("prerequisites", "## Step -2: Run-Start Authorization", "## Step -1: Archive Sweep Startup"),
        "binding": ("prerequisites", "## Workflow Worktree Binding", "## Step -2: Run-Start Authorization"),
    }
    GUIDES = {"policy": SKILL_DIR + "references/stop-policy.md"}

    def test_step_runs_before_archive_sweep_and_on_every_resume(self) -> None:
        _assert_phrases(self, self.step, PHRASES["CodexRunStartAuthorizationSourceContractTests.test_step_runs_before_archive_sweep_and_on_every_resume#1"])
        self.assertLess(self.skill.index("run the Step -2 run-start authorization"),
                        self.skill.index("**Archive Sweep**"))

    def test_policy_classes_derive_from_the_gate_coverage_output(self) -> None:
        _assert_phrases(self, self.step, PHRASES["CodexRunStartAuthorizationSourceContractTests.test_policy_classes_derive_from_the_gate_coverage_output#1"])

    def test_each_class_and_write_surface_is_probed_before_phase_one(self) -> None:
        _assert_phrases(self, self.step, PHRASES["CodexRunStartAuthorizationSourceContractTests.test_each_class_and_write_surface_is_probed_before_phase_one#1"])

    def test_a_missing_policy_or_denied_probe_is_one_plain_text_request(self) -> None:
        _assert_phrases(self, self.step, PHRASES["CodexRunStartAuthorizationSourceContractTests.test_a_missing_policy_or_denied_probe_is_one_plain_text_request#1"])

    def test_binding_guard_defers_the_external_root_denial_to_the_probe(self) -> None:
        self.assertIn("Step -2 probes that root for write access before any phase work", self.binding)
        self.assertNotIn("STOP with the denied path and operation if access remains unavailable", self.binding)

    def test_phase_six_five_rechecks_the_standing_policy_with_the_derived_classes(self) -> None:
        _assert_phrases(self, self.phase, (
            "Step -2's `policy_classes` verbatim as `derived_classes`",
            "a correctly installed policy reads as missing",
        ))
        self.assertIn("rerun the standing check with Step -2's `derived_classes`",
                      _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / "prerequisites.md"))
        _assert_phrases(self, self.step, (
            "A base class's probe sends no repository content",
            "A derived class's probe is its gate command run once",
        ))

    def test_phase_six_five_cites_the_run_start_result_and_inventories_the_private_write(self) -> None:
        _assert_phrases(self, self.phase, PHRASES["CodexRunStartAuthorizationSourceContractTests.test_phase_six_five_cites_the_run_start_result_and_inventories_the_private_write#1"])

    def test_shared_reference_states_the_run_start_grant_for_both_hosts(self) -> None:
        _assert_phrases(self, self.policy, PHRASES["CodexRunStartAuthorizationSourceContractTests.test_shared_reference_states_the_run_start_grant_for_both_hosts#1"])
        self.assertIn("stop-policy.md#run-start-grants", self.skill)


class ClaudeRunStartPermissionProbeSourceContractTests(_ClaudeGuides):
    """Claude settles runner and Git permissions once, before any phase work (issue 833)."""

    SECTIONS = {"step": ("prerequisites", "## Step -2: Run-Start Permission Probe", "## Workflow Worktree Binding")}
    GUIDES = {"limitations": SKILL_DIR + "references/plugin-limitations.md"}

    def test_one_no_op_runner_request_and_one_git_status_run_first(self) -> None:
        _assert_phrases(self, self.step, PHRASES["ClaudeRunStartPermissionProbeSourceContractTests.test_one_no_op_runner_request_and_one_git_status_run_first#1"])

    def test_a_prompt_or_denial_prints_the_exact_allow_rule_and_stops_once(self) -> None:
        _assert_phrases(self, self.step, PHRASES["ClaudeRunStartPermissionProbeSourceContractTests.test_a_prompt_or_denial_prints_the_exact_allow_rule_and_stops_once#1"])
        # The zero-shell guard rejects the shell tool's name in shipped guidance.
        self.assertNotIn("Ba" + "sh", self.step)
        self.assertIn("print nothing and continue", self.step)

    def test_the_skill_and_references_point_at_the_probe(self) -> None:
        _assert_phrases(self, self.skill, PHRASES["ClaudeRunStartPermissionProbeSourceContractTests.test_the_skill_and_references_point_at_the_probe#1"])
        _assert_phrases(self, self.limitations, (
            "so the run checks them once at start",
            "prints the exact allow rule and stops once",
        ))
        _assert_phrases(self, self.phase, ("Step -2 run-start permission probe", "declared pre-PR command"))
        self.assertNotIn("an unattended run must prepare them before launch", self.skill)
        self.assertNotIn("needs no run-start inventory", self.phase)


    def test_claude_autopilot_has_no_autonomy_preflight_to_mirror(self) -> None:
        references = CLAUDE_AUTOPILOT_SKILL.parent / "references"
        texts = [_flat(CLAUDE_AUTOPILOT_SKILL)] + [_flat(path) for path in sorted(references.glob("*.md"))]
        for text in texts:
            _assert_absent(self, text, ("Autonomy Boundary Preflight", "auto_review"))

    def test_deferred_action_record_passes_the_phase_seven_guard(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            state = _autonomy_boundary_state(root)
            boundary = state["autonomy_boundary"]
            action = boundary["actions"][0]
            action["disposition"] = "operator_action_required"
            action["authorization"]["status"] = "missing"
            boundary["status"] = "operator_action_required"
            state["plan"][1]["status"] = "in_progress"
            self.assertEqual(_autonomy_errors(state, root), [])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-autopilot-standing-policy-preflight"))
