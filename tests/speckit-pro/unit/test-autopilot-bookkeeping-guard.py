#!/usr/bin/env python3
"""Behavioural coverage for the autopilot bookkeeping guard.

Covers the surfaces that enforce the bookkeeping rule at run time: the
``workflow_status_evidence_errors`` and ``validate_state_status`` checks inside
the shipped phase-coverage validator, and its ``--rule`` exit-code scoping.

The rule's own CI gate asserts that the live corpus is clean, which cannot show
that the gate would *catch* a violation. These tests supply the negative
fixtures: each one constructs a workflow that is wrong in exactly one way and
asserts the specific error.

Python 3.11+ standard library only.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import uuid
from unittest import mock
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
LIB_DIR = TEST_DIR.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import privacy_patterns  # noqa: E402
from test_result import run_counted  # noqa: E402

SKILL_SCRIPTS = REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "scripts"
VALIDATOR = SKILL_SCRIPTS / "validate-autopilot-phase-coverage.py"
CLAUDE_AUTOPILOT_SKILL = REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "SKILL.md"
CODEX_AUTOPILOT_SKILL = REPO_ROOT / "speckit-pro" / "codex-skills" / "speckit-autopilot" / "SKILL.md"
BLOCKING_STATE_INVARIANT_KEYS = (
    "in_progress_errors",
    "duplicate_state_steps",
    "state_order_errors",
)

BLOCKING_STATUS_EVIDENCE_KEYS = (
    "workflow_status_evidence_errors",
    "state_status_errors",
    "autonomy_boundary_errors",
    "stage_mirror_errors",
    "workflow_authority_errors",
    "state_privacy_errors",
    "marker_evidence_privacy_errors",
)

PLAN_STEPS = (
    "Archive Sweep: previously merged specs dry-run/apply eligibility",
    "Phase 0: Prerequisites",
    "Phase 1: Specify",
    "Phase 2: Clarify",
    "Phase 3: Plan",
    "Phase 4: Domain Checklists",
    "Phase 5: Tasks",
    "Phase 6: Analyze",
    "Phase 6.5: Pre-Implement Confidence",
    "Phase 7: Implement",
)

# Repository-relative references inside the authority fixture's own temporary root.
SUPPLIED_WORKFLOW_REF = "docs/supplied-workflow.md"
OTHER_WORKFLOW_REF = "docs/a-different-workflow.md"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


validator = _load(VALIDATOR, "speckit_autopilot_phase_coverage_under_test")


def workflow(*rows: tuple[str, str], body: str = "") -> str:
    """A minimal workflow document with the given (phase, status) overview rows."""
    lines = ["# Workflow", "", "## Workflow Overview", "", "| Phase | Command | Status | Notes |", "|---|---|---|---|"]
    lines.extend(f"| {phase} | `/speckit-x` | {status} | |" for phase, status in rows)
    lines.extend(["", body])
    return "\n".join(lines)


def _clean_state_plan() -> list[dict[str, str]]:
    """A state plan with every validator-required step, once, in canonical order."""
    steps = [
        {"step": step, "status": "completed"}
        for step in validator.STATE_PREFIXES
    ]
    steps.extend(
        {"step": post, "status": "pending"}
        for post in validator.POST_STEPS
    )
    return steps


def _planning_fingerprints(root: Path) -> dict:
    feature = root / "specs" / "demo"
    feature.mkdir(parents=True)
    planning_fingerprints = {}
    for label, content in (("plan_md", b"# Plan\n"), ("tasks_md", b"# Tasks\n")):
        path = feature / ("plan.md" if label == "plan_md" else "tasks.md")
        path.write_bytes(content)
        planning_fingerprints[label] = {
            "path": path.relative_to(root).as_posix(),
            "sha256": validator._sha256_bytes(content),
            "size_bytes": len(content),
        }
    return planning_fingerprints


def _current_execution_boundary(root: Path) -> dict:
    return {
        "execution_environment": "local",
        "sandbox_mode": "workspace-write",
        "approval_reviewer": "auto_review",
        "writable_roots": [str(root)],
    }


def _execution_boundary(root: Path) -> dict:
    execution_scope = _current_execution_boundary(root)
    execution_boundary = {
        **execution_scope,
        "summary": "Repository writes are direct; system writes require approval.",
        "sha256": validator._canonical_json_sha256(execution_scope),
    }
    return execution_boundary


def _autonomy_action(execution_sha256: str) -> dict:
    action_scope = {
        "category": "privileged_command",
        "command_or_tool": "sudo install reviewed payload",
        "target": "/opt/redline",
        "effect": "persistent system-wide runtime installation",
        "execution_boundary_sha256": execution_sha256,
    }
    scope_sha256 = validator._canonical_json_sha256(action_scope)
    return {
        "action_id": "install-runtime",
        **action_scope,
        "scope_sha256": scope_sha256,
        "disposition": "ready",
        "authorization": {
            "status": "explicit_user",
            "evidence": "user approved the exact target and lasting effect",
            "scope_sha256": scope_sha256,
        },
    }


def _autonomy_boundary_state(root: Path) -> dict:
    execution_boundary = _execution_boundary(root)
    return {
        "status": "in_progress",
        "stage": "implement",
        "plan": [
            {"step": "Phase 6.5: Confidence Gate", "status": "completed"},
            {"step": "Phase 7: Implement", "status": "pending"},
        ],
        "autonomy_boundary": {
            "schema_version": "autonomy-boundary.v1",
            "status": "ready",
            "planning_fingerprints": _planning_fingerprints(root),
            "execution_boundary": execution_boundary,
            "actions": [_autonomy_action(execution_boundary["sha256"])],
        },
    }


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


def _autonomy_errors(state: dict, root: Path) -> list[str]:
    return validator.validate_autonomy_boundary(
        state,
        root,
        current_execution_boundary=_current_execution_boundary(root),
        require_boundary=True,
    )["autonomy_boundary_errors"]


def _clean_workflow() -> str:
    """A workflow document with the sections and table cells coverage expects."""
    lines = [
        "# Workflow",
        "",
        "## Workflow Overview",
        "",
        "| Phase | Command | Status | Notes |",
        "|---|---|---|---|",
        "| Specify | `/speckit-x` | ⏳ Pending | |",
        "",
        "| Confidence Gate | G6.5 | Status | Notes |",
        "|---|---|---|---|",
        "| G6.5 | Confidence Gate | ⏳ Pending | |",
        "",
    ]
    lines.extend(validator.WORKFLOW_SECTIONS)
    lines.extend([
        "",
        "| Post | Status | Notes |",
        "|---|---|---|",
    ])
    lines.extend(f"| Post | {post} | ⏳ Pending | |" for post in validator.POST_STEPS)
    return "\n".join(lines)


def clean_workflow_state_fixture(
    root: Path,
    *,
    state_workflow_ref: str | None = SUPPLIED_WORKFLOW_REF,
) -> tuple[Path, Path]:
    """Lay out one clean repository-shaped workflow/state pair.

    FR-009 negative controls mutate this pair one problem key at a time. FR-011
    uses it unchanged to prove the same scoped invocation can succeed.
    """
    (root / ".git").write_text("gitdir: ../elsewhere/.git/worktrees/fixture\n", encoding="utf-8")
    supplied = root / SUPPLIED_WORKFLOW_REF
    supplied.parent.mkdir(parents=True, exist_ok=True)
    supplied.write_text(_clean_workflow(), encoding="utf-8")
    state = supplied.parent / "autopilot-state.json"
    state.write_text(
        json.dumps({
            "workflow_file": state_workflow_ref,
            "plan": _clean_state_plan(),
        }),
        encoding="utf-8",
    )
    return supplied, state


def run_status_evidence_report(workflow_path: Path, state_path: Path) -> tuple[int, dict]:
    """Run the exact scoped invocation autopilot issues at phase transitions."""
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR),
         "--workflow", str(workflow_path), "--state", str(state_path),
         "--rule", "status-evidence"],
        text=True, capture_output=True, check=False,
    )
    return completed.returncode, json.loads(completed.stdout)


def status_evidence_guidance_paragraph(path: Path) -> str:
    """Return the source paragraph that explains the scoped bookkeeping guard."""
    paragraphs = [
        paragraph.replace("\n", " ")
        for paragraph in path.read_text(encoding="utf-8").split("\n\n")
    ]
    matches = [
        paragraph
        for paragraph in paragraphs
        if "status-evidence" in paragraph
        and "exit code" in paragraph
        and "full report" in paragraph
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected one status-evidence guidance paragraph in {path}")
    return matches[0]


def tracked_workflow_state_paths(repo_root: Path = REPO_ROOT) -> tuple[str, ...]:
    """Return tracked workflow/state paths from the git index in stable order."""
    try:
        completed = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=repo_root,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("git ls-files -z failed while enumerating tracked paths") from exc
    paths = completed.stdout.decode("utf-8").split("\0")
    return tuple(sorted(
        path for path in paths
        if path.endswith("-workflow.md") or path.endswith("/autopilot-state.json")
    ))


def _adjacent_state_path(workflow_path: str) -> str:
    if "/" not in workflow_path:
        return "autopilot-state.json"
    return workflow_path.rsplit("/", 1)[0] + "/autopilot-state.json"


def classify_authority_matched_pairs(repo_root: Path, tracked_paths: tuple[str, ...]) -> dict:
    """Classify tracked workflows by adjacent state authority."""
    tracked = frozenset(tracked_paths)
    eligible: list[tuple[str, str]] = []
    excluded: list[dict[str, str | None]] = []

    for workflow_path in sorted(path for path in tracked if path.endswith("-workflow.md")):
        state_ref = _adjacent_state_path(workflow_path)
        state_path = repo_root / state_ref
        if state_ref not in tracked:
            reason = "untracked-adjacent-state" if state_path.exists() else "missing-adjacent-state"
            excluded.append({
                "workflow": workflow_path,
                "state": state_ref,
                "reason": reason,
            })
            continue

        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"could not parse tracked state JSON: {state_ref}") from exc
        workflow_file = state.get("workflow_file") if isinstance(state, dict) else None
        if workflow_file == workflow_path:
            eligible.append((workflow_path, state_ref))
        else:
            excluded.append({
                "workflow": workflow_path,
                "state": state_ref,
                "reason": "workflow-file-mismatch",
                "workflow_file": workflow_file,
            })

    return {"eligible": tuple(eligible), "excluded": tuple(excluded)}


class StatusEvidenceReportAssertions:
    """Reusable checks for status-evidence report shape and isolated findings."""

    SELECTED_KEYS = frozenset(validator.RULE_PROBLEM_KEYS["status-evidence"])
    EXPECTED_KEYS = frozenset({
        "status",
        "workflow_file",
        "state_file",
        "plan_step_count",
        *validator.PROBLEM_KEY_INTENT,
    })

    def assertCompleteReport(self, report: dict) -> None:  # noqa: N802
        self.assertEqual(set(report), self.EXPECTED_KEYS)
        for key in validator.PROBLEM_KEY_INTENT:
            with self.subTest(report_key=key):
                self.assertIsInstance(report[key], list)

    def assertSelectedKeysEmpty(self, report: dict) -> None:  # noqa: N802
        for key in self.SELECTED_KEYS:
            with self.subTest(selected_key=key):
                self.assertEqual(report[key], [])

    def assertOnlySelectedProblemKeyPopulated(  # noqa: N802
        self,
        report: dict,
        target_key: str,
    ) -> None:
        self.assertIn(target_key, report)
        self.assertTrue(report[target_key], f"{target_key} should be populated")
        for key in self.SELECTED_KEYS - {target_key}:
            with self.subTest(selected_key=key):
                self.assertEqual(report[key], [])


class WorkflowStatusEvidenceTests(unittest.TestCase):
    """Negative fixtures for the rule this PR introduces."""

    def test_recorded_gate_pass_requires_a_terminal_row(self) -> None:
        text = workflow(("Tasks", "⏳ Pending"), body="**G5 gate:** ✅ PASS — 63 tasks found")
        errors = validator.workflow_status_evidence_errors(text)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("'Tasks'", errors[0])
        self.assertIn("G5 PASS", errors[0])

    def test_terminal_row_after_open_row_is_an_ordering_error(self) -> None:
        text = workflow(("Tasks", "⏳ Pending"), ("Implement", "✅ Complete"))
        errors = validator.workflow_status_evidence_errors(text)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("while earlier", errors[0])

    def test_clean_workflow_reports_nothing(self) -> None:
        text = workflow(("Tasks", "✅ Complete"), ("Implement", "✅ Complete"),
                        body="**G5 gate:** ✅ PASS")
        self.assertEqual(validator.workflow_status_evidence_errors(text), [])

    def test_unknown_status_is_reported(self) -> None:
        text = workflow(("Tasks", "mostly done"))
        errors = validator.workflow_status_evidence_errors(text)
        self.assertTrue(any("unsupported status" in e for e in errors), errors)

    def test_gate_criteria_table_is_not_evidence(self) -> None:
        """A '### Phase Gates' approval-criteria row must not count as a verdict."""
        text = workflow(
            ("Tasks", "⏳ Pending"),
            body="### Phase Gates\n\n| Gate | Checkpoint | Criteria |\n|---|---|---|\n"
                 "| G5 | After Tasks | Tests pass, coverage verified |",
        )
        self.assertEqual(validator.workflow_status_evidence_errors(text), [])

    def test_commented_out_evidence_is_not_evidence(self) -> None:
        text = workflow(("Tasks", "⏳ Pending"), body="<!-- **G5 gate:** ✅ PASS -->")
        self.assertEqual(validator.workflow_status_evidence_errors(text), [])

    def test_advisory_confidence_gate_does_not_bar_later_rows(self) -> None:
        """An advisory row the phase loop never drives must not cascade."""
        text = workflow(("Confidence Gate", "⏳ Pending"), ("Implement", "✅ Complete"))
        self.assertEqual(validator.workflow_status_evidence_errors(text), [])

    def test_missing_overview_table_is_reported(self) -> None:
        errors = validator.workflow_status_evidence_errors("# Workflow\n\nNo table here.\n")
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("no parseable", errors[0])


class StateStatusSchemaTests(unittest.TestCase):
    def test_retired_spelling_is_rejected(self) -> None:
        errors = validator.validate_state_status({"status": "complete_pr_open"})["state_status_errors"]
        self.assertTrue(any("enum" in e for e in errors), errors)

    def test_current_spellings_are_accepted(self) -> None:
        for status in ("in_progress", "completed", "completed_pr_open", "completed_archived"):
            with self.subTest(status=status):
                self.assertEqual(
                    validator.validate_state_status({"status": status})["state_status_errors"], []
                )

    def test_absent_status_is_accepted(self) -> None:
        """The canonical state shape carries no top-level status; absence is legal."""
        self.assertEqual(validator.validate_state_status({})["state_status_errors"], [])


class AutonomyBoundarySourceContractTests(unittest.TestCase):
    def test_source_contract_places_preflight_before_every_phase_seven_entry(self) -> None:
        skill = CODEX_AUTOPILOT_SKILL.read_text(encoding="utf-8")
        prerequisites = (
            CODEX_AUTOPILOT_SKILL.parent / "references" / "prerequisites-codex.md"
        ).read_text(encoding="utf-8")
        phase_execution = (
            CODEX_AUTOPILOT_SKILL.parent / "references" / "phase-execution-codex.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(phase_execution.split())

        boundary = phase_execution.index("### Autonomy Boundary Preflight")
        confidence = phase_execution.index("1. Read mode from `CONFIDENCE_GATE_MODE`", boundary)
        phase_seven = phase_execution.index("## Phase 7: Implement")
        self.assertLess(boundary, confidence)
        self.assertLess(confidence, phase_seven)
        self.assertIn("Autonomy Boundary Preflight, G6.5 confidence gate", normalized)
        self.assertIn("A `plan` run", phase_execution)
        self.assertIn("An `implement` or `full` run", phase_execution)
        self.assertIn("before its first Phase 7 dispatch", normalized)
        self.assertIn("Exact explicit user authorization persists", phase_execution)
        self.assertIn("no later user instruction revokes or narrows it", normalized)
        self.assertIn("Prior execution", prerequisites)
        self.assertIn("automatic review", prerequisites)
        self.assertIn("older task crossed the boundary", " ".join(prerequisites.split()))
        self.assertIn("`autonomy_boundary` record", skill)
        for flag in (
            "--require-autonomy-boundary",
            "--current-execution-environment",
            "--current-sandbox-mode",
            "--current-approval-reviewer",
            "--current-writable-root",
        ):
            self.assertIn(flag, skill)
            self.assertIn(flag, phase_execution)

    def test_resume_re_attests_a_stale_boundary_before_the_coverage_guard(self) -> None:
        """A new thread's writable roots make the persisted boundary stale (issue 747).

        The resume must re-attest it up front, before the Step 1.1 guard, for
        every stage, including a plan-stage resume. Since issue 764 a covered
        inventory asks no question and an uncovered action is deferred.
        """
        skill = " ".join(CODEX_AUTOPILOT_SKILL.read_text(encoding="utf-8").split())
        prerequisites = (
            CODEX_AUTOPILOT_SKILL.parent / "references" / "prerequisites-codex.md"
        ).read_text(encoding="utf-8")
        phase_execution = " ".join(
            (CODEX_AUTOPILOT_SKILL.parent / "references" / "phase-execution-codex.md")
            .read_text(encoding="utf-8")
            .split()
        )
        start = prerequisites.index("### 0.8c Resumed Autonomy Boundary Preflight")
        end = prerequisites.index("### 0.9", start)
        section = " ".join(prerequisites[start:end].split())

        self.assertIn("persisted `autonomy_boundary` receipt, at any stage", section)
        self.assertIn("including a plan-stage resume", section)
        self.assertIn("before the Step 1.1 coverage guard", section)
        self.assertIn(
            "current execution boundary does not match the persisted execution boundary",
            section,
        )
        self.assertIn("a branch, not a stop", section)
        self.assertIn("standing policy coverage", section)
        self.assertIn("the one end-of-run request", section)
        self.assertIn("never as a guard-failure repair", section)
        self.assertIn("A mismatch still blocks", section)
        self.assertIn("at any stage", skill)
        self.assertIn("before the Step 1.1 coverage guard", skill)
        self.assertIn("Step 0.8c", phase_execution)

    def test_preflight_inventories_data_egress_to_model_services(self) -> None:
        """A live model evaluation sends repository content off-machine (issue 748)."""
        skill = " ".join(CODEX_AUTOPILOT_SKILL.read_text(encoding="utf-8").split())
        phase = " ".join(
            (CODEX_AUTOPILOT_SKILL.parent / "references" / "phase-execution-codex.md")
            .read_text(encoding="utf-8")
            .split()
        )
        start = phase.index("### Autonomy Boundary Preflight")
        end = phase.index("For each action, record its category", start)
        inventory = phase[start:end]
        for phrase in (
            "data egress",
            "live model evaluation",
            "a push or PR to a remote",
            "exact destination",
        ):
            self.assertIn(phrase, inventory)
        self.assertIn("every data-egress destination and data class", phase)
        self.assertIn("is not egress authorization", phase)
        self.assertIn("data egress to a model service", skill)

    def test_consolidated_request_emits_egress_authorization_and_extra_policy(self) -> None:
        """The reviewer trusts user messages, not plugin text (issue 755).

        The one operator action carries a paste-ready authorization naming each
        payload and destination, plus an `auto_review.extra_policy` fragment the
        operator installs. The plugin never writes the reviewer's trusted files.
        """
        skill = " ".join(CODEX_AUTOPILOT_SKILL.read_text(encoding="utf-8").split())
        phase = " ".join(
            (CODEX_AUTOPILOT_SKILL.parent / "references" / "phase-execution-codex.md")
            .read_text(encoding="utf-8")
            .split()
        )
        prerequisites = " ".join(
            (CODEX_AUTOPILOT_SKILL.parent / "references" / "prerequisites-codex.md")
            .read_text(encoding="utf-8")
            .split()
        )
        start = phase.index("### Autonomy Boundary Preflight")
        end = phase.index("1. Read mode from `CONFIDENCE_GATE_MODE`", start)
        preflight = phase[start:end]

        for phrase in (
            "`render-egress-authorization`",
            "paste-ready authorization message",
            "Send <data class> from <repository> to <destination> for <purpose>",
            "`auto_review.extra_policy`",
            "never `auto_review.policy`",
            "replaces the default reviewer policy",
            "`git remote get-url --push origin`",
            "Outcome rule: deny",
            "autonomy-boundary files, their schema, or their recorded digests",
            "a push to the default branch",
            "a force push",
            "`--mirror`",
            "a remote change",
            "reaches the reviewer only when it escalates",
            "CI and the boundary validator",
            "never writes the authorization message or the fragment into `~/.codex`",
            "into the repository's `.codex/` directory, or into `AGENTS.md`",
            "`authorization_message_sha256`",
            "`authorization.evidence`",
        ):
            self.assertIn(phrase, preflight)
        self.assertIn("paste-ready authorization message", skill)
        self.assertIn("`auto_review.extra_policy`", skill)
        self.assertIn("paste-ready authorization message", prerequisites)

    def test_canonical_schema_excludes_automatic_and_prior_execution_authorization(self) -> None:
        schema = json.loads(
            validator.AUTONOMY_BOUNDARY_SCHEMA_PATH.read_text(
                encoding="utf-8"
            )
        )
        statuses = schema["$defs"]["authorization"]["properties"]["status"]["enum"]
        self.assertIn("explicit_user", statuses)
        self.assertIn("revoked", statuses)
        self.assertNotIn("auto_review", statuses)
        self.assertNotIn("prior_execution", statuses)


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def _section(text: str, heading: str, next_heading: str) -> str:
    start = text.index(heading)
    return text[start : text.index(next_heading, start + len(heading))]


BLOCKED_ACTION_HEADING = "Blocked Actions Mid-Run: Fall Back or Defer, Never Stop"


class BlockedActionDeferralSourceContractTests(unittest.TestCase):
    """One blocked action mid-run must not stop independent work (issue 752)."""

    def assert_deferral_rules(self, section: str, ask_tool: str) -> None:
        for phrase in (
            "approval-reviewer veto",
            "missing approval",
            "unavailable tool",
            "fallback that the task, `tasks.md`, or the spec itself defines",
            "auto-applied fallback",
            "defer that task",
            "every task and Post item that depends on it",
            "keep executing every independent task, gate, and Post check",
            "while runnable work remains",
            "reserves no execution-control budget",
            "one consolidated operator request",
            ask_tool,
            "plain text in the final message",
            "known_gaps",
            "every fallback taken and every deferred item",
            "never bypass",
            "never change approval, sandbox, or reviewer configuration",
            "unknown side effects",
            "`checkpoint_required`",
        ):
            self.assertIn(phrase, section)

    def test_codex_phase_seven_defers_a_blocked_action_and_continues(self) -> None:
        references = CODEX_AUTOPILOT_SKILL.parent / "references"
        phase = _flat(references / "phase-execution-codex.md")
        section = _section(
            phase, f"### {BLOCKED_ACTION_HEADING}", "## PR Packet and Body Boundary"
        )
        self.assertLess(phase.index("## Phase 7: Implement"), phase.index(section))
        self.assert_deferral_rules(section, "`request_user_input`")
        self.assertIn("even when `request_user_input` returns", section)
        # The late-discovery rule no longer routes a mid-run boundary into the
        # pre-Phase-7 stop.
        late = _section(phase, "If a worker discovers a predictable boundary", "```text")
        self.assertIn("defers only that task", late)
        self.assertIn(BLOCKED_ACTION_HEADING, late)

    def test_codex_entrypoint_and_post_audit_allow_an_honest_deferred_end(self) -> None:
        skill = _flat(CODEX_AUTOPILOT_SKILL)
        references = CODEX_AUTOPILOT_SKILL.parent / "references"
        post = _flat(references / "post-implementation-codex.md")
        recovery = _flat(references / "error-recovery-codex.md")
        self.assertIn(BLOCKED_ACTION_HEADING, skill)
        audit = _section(skill, "### 3.4 Pre-final completion audit", "Only after every Post item")
        self.assertIn("deferred items remain", audit)
        self.assertIn("plain text in the final message", audit)
        self.assertIn("deferred items remain", post)
        self.assertIn("known_gaps", post)
        self.assertIn("Action blocked mid-run", recovery)
        self.assertIn(BLOCKED_ACTION_HEADING, recovery)

    def test_claude_phase_seven_mirrors_the_deferral_rule(self) -> None:
        references = CLAUDE_AUTOPILOT_SKILL.parent / "references"
        phase = _flat(references / "phase-execution.md")
        section = _section(
            phase, f"#### {BLOCKED_ACTION_HEADING}", "#### Append Contract"
        )
        self.assertLess(phase.index("#### Never Yield With Nothing In Flight"), phase.index(section))
        self.assert_deferral_rules(section, "`AskUserQuestion`")
        never_yield = _section(
            phase, "#### Never Yield With Nothing In Flight", f"#### {BLOCKED_ACTION_HEADING}"
        )
        self.assertIn("A blocked action is not a stop condition", never_yield)

    def test_claude_entrypoint_and_recovery_mirror_the_deferred_end(self) -> None:
        skill = _flat(CLAUDE_AUTOPILOT_SKILL)
        recovery = _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "error-recovery.md")
        audit = _section(skill, "### 3.4 Pre-final completion audit", "## Workflow File Update Protocol")
        self.assertIn("deferred items remain", audit)
        self.assertIn("plain text in the final message", audit)
        self.assertIn(BLOCKED_ACTION_HEADING, audit)
        self.assertIn("Action blocked mid-run", recovery)
        self.assertIn(BLOCKED_ACTION_HEADING, recovery)


class RunFinalizationSourceContractTests(unittest.TestCase):
    """Only human UAT may be deferred; anything else left is one human stop (issue 804)."""

    STALE = (
        "honest incomplete checkpoint, never completion",
        "Never report completion while a deferred item remains",
        "may the rows holding deferred work move to `⚠ Blocked`",
        "reported as deferred, never green",
        "`attributed_units`",
        "instead of rerunning the full suite for every slice",
    )
    PER_HEAD = (
        "at each PR head, bottom-up",
        "`head_sha`",
        "`human_stop.missing`",
        "cites only the gate results listed under its own entry",
        "`status=harness_error`",
        "`attempts`",
        ".process/verification/harness/",
        "a harness error, never as a failure of the code under test",
        "never counts as passed",
    )
    STACK_PER_HEAD = (
        "at the slice's own head",
        "never carry another head's evidence",
        "propagate it upward by merge",
        "re-verify every affected head",
        "only the evidence produced at that slice's own head",
    )

    def assert_finalization_rules(self, section: str) -> None:
        for phrase in (
            "`finalize-run`",
            "Human UAT is the only gate a run may defer",
            "`human_uat`",
            "ready for review",
            "never merges",
            "`Deferred / not verified`",
            "`deferred_items`",
            "`ready_commands`",
            "`end_of_run_request`",
            "`outcome=human_stop`",
            "one human stop",
            "exact command",
            "retry with backoff",
            "reviewer veto despite a recorded chat authorization",
            "never lets a gate pass, be skipped, or be deferred",
            "at the end of the run an unresolved deferral is the human stop",
            "`deferred_digest`",
            "never re-checks an unchanged blocker",
            *self.PER_HEAD,
        ):
            self.assertIn(phrase, section)
        for phrase in self.STALE:
            self.assertNotIn(phrase, section)

    def test_codex_finalizes_a_deferred_run_and_completes_the_goal(self) -> None:
        references = CODEX_AUTOPILOT_SKILL.parent / "references"
        phase = _flat(references / "phase-execution-codex.md")
        section = _section(phase, f"### {BLOCKED_ACTION_HEADING}", "### Repeated Gate Failures")
        self.assert_finalization_rules(section)
        self.assertIn("marks the thread goal complete", section)
        self.assertIn("never set the thread goal blocked for it mid-run", phase)
        recovery = _flat(references / "error-recovery-codex.md")
        self.assertIn("never sets the thread goal blocked mid-run", recovery)
        self.assertNotIn("never sets the thread goal blocked.", recovery)
        hardener = _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "hardener-delegation.md")
        self.assertIn("It is a gate, so it never stays deferred", hardener)
        efficiency = _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "execution-efficiency.md")
        self.assertIn("the run never finalizes ready for review over it, a gate's included", efficiency)
        preflight = _section(phase, "### Autonomy Boundary Preflight", "1. Read mode from `CONFIDENCE_GATE_MODE`")
        for phrase in ("`check-gate-preflight-coverage`", "preflight defect", "at run start"):
            self.assertIn(phrase, preflight)
        skill = _flat(CODEX_AUTOPILOT_SKILL)
        audit = _section(skill, "### 3.4 Pre-final completion audit", "## Workflow File Update Protocol")
        self.assertIn("`finalize-run`", audit)
        for phrase in self.STALE:
            self.assertNotIn(phrase, skill)
        post = _flat(references / "post-implementation-codex.md")
        self.assertIn("`finalize-run`", post)
        self.assertIn("`deferred_items`", post)
        self.assertIn("every PR head", audit)
        for phrase in self.STACK_PER_HEAD:
            self.assertIn(phrase, post)
        for phrase in self.STALE:
            self.assertNotIn(phrase, post)

    def test_claude_mirrors_the_finalization(self) -> None:
        references = CLAUDE_AUTOPILOT_SKILL.parent / "references"
        phase = _flat(references / "phase-execution.md")
        section = _section(phase, f"#### {BLOCKED_ACTION_HEADING}", "#### Repeated Gate Failures")
        self.assert_finalization_rules(section)
        skill = _flat(CLAUDE_AUTOPILOT_SKILL)
        audit = _section(skill, "### 3.4 Pre-final completion audit", "## Workflow File Update Protocol")
        self.assertIn("`finalize-run`", audit)
        self.assertIn("every PR head", audit)
        for phrase in self.STALE:
            self.assertNotIn(phrase, skill)
        post = _flat(references / "post-implementation.md")
        for phrase in self.STACK_PER_HEAD:
            self.assertIn(phrase, post)

    def test_stack_manager_keeps_draft_status_only_until_finalization(self) -> None:
        stack = _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "stack-manager.md")
        self.assertIn("Preserve packet metadata, and draft status until finalization", stack)
        for phrase in ("at its own head", "bottom-up", "re-verify every affected head"):
            self.assertIn(phrase, stack)


FAILURE_CLASS_HEADING = "Repeated Gate Failures: Diagnose One Class, Approve It Once"


class FailureClassApprovalSourceContractTests(unittest.TestCase):
    """Repeated same-signature gate failures are one class with one approval (issue 785)."""

    def assert_class_rules(self, section: str) -> None:
        for phrase in (
            "same failure signature in the same test file",
            "even when the failing tests differ",
            "one failure class",
            "environment signal first",
            "host load and temp-directory size",
            "rerun the gate once, before proposing any timeout change",
            "one class-level fix",
            "never per-test diffs",
            "`failure_class`",
            "`authorize-corrective-exception`",
            "`reserve-class-correction`",
            "without a new question",
            "at most once",
            "production",
            "consolidated operator request",
        ):
            self.assertIn(phrase, section)

    def test_codex_phase_execution_states_the_class_rule(self) -> None:
        phase = _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / "phase-execution-codex.md")
        section = _section(phase, f"### {FAILURE_CLASS_HEADING}", "## PR Packet and Body Boundary")
        self.assert_class_rules(section)
        recovery = _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / "error-recovery-codex.md")
        self.assertIn(FAILURE_CLASS_HEADING, recovery)
        self.assertIn("`reserve-class-correction`", recovery)

    def test_claude_phase_execution_states_the_class_rule(self) -> None:
        references = CLAUDE_AUTOPILOT_SKILL.parent / "references"
        phase = _flat(references / "phase-execution.md")
        section = _section(phase, f"#### {FAILURE_CLASS_HEADING}", "#### Append Contract")
        self.assert_class_rules(section)
        recovery = _flat(references / "error-recovery.md")
        self.assertIn(FAILURE_CLASS_HEADING, recovery)
        self.assertIn("`reserve-class-correction`", recovery)
        skill = _flat(CLAUDE_AUTOPILOT_SKILL)
        self.assertIn("`reserve-class-correction`", _section(skill, "## Error Recovery", "## References"))

    def test_ledger_reference_documents_the_class_request_shape(self) -> None:
        efficiency = _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "execution-efficiency.md")
        section = _section(efficiency, "- `reserve-class-correction`:", "- `begin-replan-epoch`:")
        for phrase in ("`test_file`", "`failure_signature`", "`change_kind`", "`test_timeout`",
                       "`follow_up_dispatch_ids`", "completed", "two follow-ups"):
            self.assertIn(phrase, section)

AMBIGUOUS_WORDING_HEADING = "Ambiguous Task Wording: Apply the Recorded Decision, Else Defer"


class AmbiguousTaskWordingSourceContractTests(unittest.TestCase):
    """A recorded owner decision settles ambiguous task wording mid-run (issue 773)."""

    def assert_recorded_decision_rule(self, section: str) -> None:
        for phrase in (
            "wording is ambiguous",
            "recorded owner decision",
            "apply that decision",
            "record the interpretation with a reference to that decision",
            "then continue",
            "no recorded decision covers it",
            "defer the item",
            "end-of-run request",
            "Never ask the operator mid-run",
            BLOCKED_ACTION_HEADING,
        ):
            self.assertIn(phrase, section)

    def test_claude_phase_seven_applies_a_recorded_decision_to_ambiguous_wording(self) -> None:
        phase = _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "phase-execution.md")
        section = _section(phase, f"#### {AMBIGUOUS_WORDING_HEADING}", "#### Append Contract")
        self.assertLess(phase.index(f"#### {BLOCKED_ACTION_HEADING}"), phase.index(section))
        self.assert_recorded_decision_rule(section)

    def test_codex_phase_seven_applies_a_recorded_decision_to_ambiguous_wording(self) -> None:
        phase = _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / "phase-execution-codex.md")
        section = _section(phase, f"### {AMBIGUOUS_WORDING_HEADING}", "## PR Packet and Body Boundary")
        self.assertLess(phase.index(f"### {BLOCKED_ACTION_HEADING}"), phase.index(section))
        self.assert_recorded_decision_rule(section)


class GateTaskEvidenceLoopGuidanceTests(unittest.TestCase):
    """Tasks guidance splits a gate task instead of making it wait on its dependents (issue 773)."""

    def test_tasks_prompt_and_g5_guidance_split_gate_tasks(self) -> None:
        template = _flat(REPO_ROOT / "speckit-pro" / "skills" / "speckit-coach" / "templates" / "workflow-template.md")
        prompt = _section(template, "### Tasks Prompt", "### Tasks Results")
        gates = _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "gate-validation.md")
        g5 = _section(gates, "### G5 — After Tasks", "#### Post-G5 Reviewability Capture Matrix")
        claude = _section(
            _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "phase-execution.md"),
            "### Phase 5: Tasks", "### Phase 6: Analyze",
        )
        codex = _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / "phase-execution-codex.md")
        for text in (prompt, g5, claude, codex):
            self.assertIn("candidate check", text)
            self.assertIn("emission step", text)
        for text in (g5, claude, codex):
            self.assertIn("gate_task_loops", text)


GATE_DEFER_PHRASE = "run the repair loop within its allowance, then defer per the Failure Escalation Protocol"


class GateFailureDeferSourceContractTests(unittest.TestCase):
    """A gate failure repairs, then defers; it never stops for a human (issue 828)."""

    def gate_validation(self) -> str:
        return _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "gate-validation.md")

    def test_every_gate_failure_line_defers_instead_of_stopping(self) -> None:
        text = self.gate_validation()
        bounds = (("G0", "### G1"), ("G2", "### G3"), ("G3", "### G4"), ("G4", "### G5"),
                  ("G5", "#### Post-G5"), ("G6", "### G7"), ("G7", "## Gate Summary Table"))
        for gate_id, next_heading in bounds:
            self.assertIn(GATE_DEFER_PHRASE, _section(text, f"### {gate_id} ", next_heading), gate_id)
        for stale in ("Immediate STOP", "STOP. Present", "→ STOP", "The default `stop` path", "present to human"):
            self.assertNotIn(stale, text)

    def test_skip_and_log_is_not_a_gate_failure_option(self) -> None:
        text = self.gate_validation()
        g3 = _section(text, "### G3 ", "### G4 ")
        self.assertNotIn("skip-and-log", g3)
        self.assertNotIn("configured `gate-failure` behavior", g3)

    def test_gate_failure_default_is_defer_on_both_hosts(self) -> None:
        claude = _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "prerequisites.md")
        codex = _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / "prerequisites-codex.md")
        readme = _flat(REPO_ROOT / "speckit-pro" / "README.md")
        for text in (claude, codex):
            self.assertIn("`gate-failure` (default: `defer`)", text)
            self.assertNotIn("`gate-failure` (default: `stop`)", text)
        self.assertIn("gate-failure: defer", readme)
        self.assertNotIn("gate-failure: stop", readme)

    def test_codex_phase_seven_defers_a_persistent_gate_failure(self) -> None:
        phase = _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / "phase-execution-codex.md")
        self.assertNotIn('gate-failure == "stop"', phase)
        self.assertNotIn('gate-failure == "skip-and-log"', phase)
        self.assertIn("If still failing, defer per the Failure Escalation Protocol", phase)
        self.assertIn("A selected formal failure defers and names the Plan resume point", phase)

    def test_claude_phase_execution_defers_instead_of_following_a_stop_path(self) -> None:
        phase = _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / "phase-execution.md")
        self.assertIn("follows the Failure Escalation Protocol and defers", phase)
        self.assertNotIn("configured gate-failure/escalation path", phase)


PLUGIN_DRIFT_HEADING = "Plugin Update Mid-Run: Record, Re-resolve, Continue"


class MidRunPluginDriftSourceContractTests(unittest.TestCase):
    """A plugin update during a run is recorded, never a restart stop (issue 767)."""

    def assert_drift_rules(self, section: str) -> None:
        for phrase in (
            "at setup or run start",
            "changed or vanished",
            "re-resolve",
            "`plugin_root`",
            "Installed Runtime Contract",
            "retry each failed bookkeeping call once",
            "record the drift",
            "never a stop",
            "single end-of-run consolidated request",
            "not a deferred task",
            "correctness stops",
        ):
            self.assertIn(phrase, section)

    def test_codex_phase_seven_records_drift_and_continues(self) -> None:
        references = CODEX_AUTOPILOT_SKILL.parent / "references"
        phase = _flat(references / "phase-execution-codex.md")
        section = _section(
            phase, f"### {PLUGIN_DRIFT_HEADING}", "## PR Packet and Body Boundary"
        )
        self.assertLess(phase.index(f"### {BLOCKED_ACTION_HEADING}"), phase.index(section))
        self.assert_drift_rules(section)
        # Codex 0.158 re-reads a registered role file at spawn time, but the
        # role list is fixed when the session starts.
        self.assertIn("next `spawn_agent`", section)
        self.assertIn("when the session starts", section)

    def test_codex_restart_rule_is_scoped_to_setup_or_run_start(self) -> None:
        skill = _flat(CODEX_AUTOPILOT_SKILL)
        prerequisites = _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / "prerequisites-codex.md")
        recovery = _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / "error-recovery-codex.md")
        for text in (skill, prerequisites):
            self.assertNotIn("cannot reload changed custom agents safely", text)
            self.assertNotIn("cannot load refreshed custom-agent definitions safely", text)
        guard = _section(skill, "Do not translate this skill into Claude-only", "## Prerequisites — Model")
        mapping = _section(skill, "Concrete Codex mapping:", "Spawn each agent with")
        availability = _section(skill, "**Step 0.10: Codex Agent Availability Check**", "**Step 0.10b")
        preflight = _section(prerequisites, "### 0.10 Codex Agent Availability Check", "### 0.10b")
        for text in (guard, mapping, availability, preflight):
            self.assertIn("at setup or run start", text)
            self.assertIn(PLUGIN_DRIFT_HEADING, text)
        self.assertIn("next `spawn_agent`", preflight)
        self.assertIn("Plugin updated mid-run", recovery)
        self.assertIn(PLUGIN_DRIFT_HEADING, recovery)

    def test_claude_phase_seven_mirrors_the_drift_rule(self) -> None:
        references = CLAUDE_AUTOPILOT_SKILL.parent / "references"
        phase = _flat(references / "phase-execution.md")
        section = _section(phase, f"#### {PLUGIN_DRIFT_HEADING}", "#### Append Contract")
        self.assertLess(phase.index(f"#### {BLOCKED_ACTION_HEADING}"), phase.index(section))
        self.assert_drift_rules(section)
        self.assertIn("`validate-agent-install`", section)
        self.assertIn("`/reload-plugins`", section)
        prerequisites = _flat(references / "prerequisites.md")
        install_check = _section(prerequisites, "If the check fails, STOP.", "## Step 0.0c")
        self.assertIn("at setup or run start", install_check)
        self.assertIn(PLUGIN_DRIFT_HEADING, install_check)
        recovery = _flat(references / "error-recovery.md")
        self.assertIn("Plugin updated mid-run", recovery)
        self.assertIn(PLUGIN_DRIFT_HEADING, recovery)


class StandingPolicyPreflightSourceContractTests(unittest.TestCase):
    """A ratified plan's ordinary work needs no up-front question (issue 764)."""

    def setUp(self) -> None:
        references = CODEX_AUTOPILOT_SKILL.parent / "references"
        phase = _flat(references / "phase-execution-codex.md")
        self.preflight = _section(
            phase, "### Autonomy Boundary Preflight", "1. Read mode from `CONFIDENCE_GATE_MODE`"
        )
        self.resume = _section(
            _flat(references / "prerequisites-codex.md"),
            "### 0.8c Resumed Autonomy Boundary Preflight",
            "### 0.9",
        )
        self.skill = _flat(CODEX_AUTOPILOT_SKILL)

    def test_covered_inventory_asks_no_question_including_a_stage_change(self) -> None:
        for phrase in (
            "`render-egress-authorization`",
            "`scope=standing`",
            "standing policy",
            "the operator's autopilot invocation in this thread and the ratified plan",
            "only the standing policy's classes",
            "asks no question",
            "planning-to-implementation stage change",
        ):
            self.assertIn(phrase, self.preflight)
        for phrase in ("asks no question", "planning-to-implementation stage change"):
            self.assertIn(phrase, self.resume)
        self.assertNotIn("A denial or no answer stops the run", self.resume)
        self.assertIn("standing policy", self.skill)
        self.assertIn("asks no question", self.skill)
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

    def test_uncovered_egress_authorization_is_asked_as_a_chat_reply_at_run_start(self) -> None:
        for phrase in (
            "asks for it as a chat reply at run start",
            "normal chat message in this thread, never as a goal edit",
            "the helper's `delivery` line",
            "never waits for the reply",
            "reads goal text as user-provided data",
        ):
            self.assertIn(phrase, self.preflight)
        self.assertIn("never as a goal edit", self.skill)

    def test_reviewer_policy_change_reaches_only_new_threads(self) -> None:
        phrase = "reaches only threads started after the change"
        self.assertIn(phrase, self.preflight)
        self.assertIn("even after an app restart", self.preflight)
        for setup in ("speckit-install", "speckit-upgrade"):
            with self.subTest(setup=setup):
                self.assertIn(phrase, _flat(CODEX_AUTOPILOT_SKILL.parents[1] / setup / "SKILL.md"))

    def test_ratified_boundary_file_edit_is_deferred_not_a_start_blocker(self) -> None:
        for phrase in (
            "boundary-file edit named in the ratified plan",
            "never blocks the start of the run",
            "the reviewer trusts `AGENTS.md`",
            "never dispatch that task",
        ):
            self.assertIn(phrase, self.preflight)

    def test_missing_standing_policy_is_a_setup_gap_and_the_run_proceeds(self) -> None:
        for phrase in ("setup gap", "reported once", "The run still proceeds"):
            self.assertIn(phrase, self.preflight)
        for setup in ("speckit-install", "speckit-upgrade"):
            with self.subTest(setup=setup):
                text = _flat(CODEX_AUTOPILOT_SKILL.parents[1] / setup / "SKILL.md")
                self.assertIn("`render-egress-authorization`", text)
                self.assertIn("`scope=standing`", text)
                self.assertIn("never `auto_review.policy`", text)
                self.assertIn("never writes", text)

    def test_claude_autopilot_has_no_autonomy_preflight_to_mirror(self) -> None:
        references = CLAUDE_AUTOPILOT_SKILL.parent / "references"
        texts = [_flat(CLAUDE_AUTOPILOT_SKILL)] + [_flat(path) for path in sorted(references.glob("*.md"))]
        for text in texts:
            self.assertNotIn("Autonomy Boundary Preflight", text)
            self.assertNotIn("auto_review", text)

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


class RuleScopingTests(unittest.TestCase):
    """`--rule` must scope the exit code without hiding anything from the report."""

    def _run(self, extra: list[str], state_overrides: dict | None = None) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            wf = root / "workflow.md"
            # Fails coverage (no Post items / sections) but passes status-evidence.
            wf.write_text(workflow(("Specify", "✅ Complete"), body="G1 gate: PASS"), encoding="utf-8")
            state = root / "autopilot-state.json"
            state_data = {
                "workflow_file": str(wf),
                "plan": [{"step": s, "status": "pending"} for s in PLAN_STEPS],
            }
            if state_overrides:
                state_data.update(state_overrides)
            state.write_text(json.dumps(state_data), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(VALIDATOR), "--workflow", str(wf), "--state", str(state), *extra],
                text=True, capture_output=True, check=False,
            )
            return completed.returncode, json.loads(completed.stdout)

    def test_full_gate_fails_on_pre_existing_coverage_debt(self) -> None:
        code, report = self._run([])
        self.assertEqual(code, 1)
        self.assertTrue(report["missing_workflow_post_items"])

    def test_status_evidence_rule_ignores_coverage_debt(self) -> None:
        code, report = self._run(["--rule", "status-evidence"])
        self.assertEqual(code, 0)
        self.assertEqual(report["workflow_status_evidence_errors"], [])

    def test_status_evidence_rule_blocks_implement_without_boundary_record(self) -> None:
        code, report = self._run(
            [
                "--rule", "status-evidence",
                "--require-autonomy-boundary",
                "--current-execution-environment", "local",
                "--current-sandbox-mode", "workspace-write",
                "--current-approval-reviewer", "auto_review",
                "--current-writable-root", "/",
            ],
            state_overrides={"status": "in_progress", "stage": "implement"},
        )
        self.assertEqual(code, 1, report)
        self.assertTrue(report["autonomy_boundary_errors"], report)

    def test_scoped_run_still_reports_every_list(self) -> None:
        """Scoping the exit code must not hide the debt from the report."""
        _code, report = self._run(["--rule", "status-evidence"])
        self.assertTrue(report["missing_workflow_post_items"])


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


class CleanStatusEvidenceControlTests(StatusEvidenceReportAssertions, unittest.TestCase):
    """FR-007/FR-011: the clean builder succeeds under the exact scoped gate."""

    def test_clean_builder_status_evidence_run_exits_zero_with_complete_report(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            supplied, state = clean_workflow_state_fixture(Path(raw))
            code, report = run_status_evidence_report(supplied, state)

        self.assertEqual(code, 0, report)
        self.assertCompleteReport(report)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["plan_step_count"], len(_clean_state_plan()))
        self.assertSelectedKeysEmpty(report)


class LegacyCoverageAdvisoryTests(StatusEvidenceReportAssertions, unittest.TestCase):
    """FR-004: legacy coverage debt stays visible without blocking status-evidence."""

    def test_missing_state_coverage_lists_remain_visible_but_nonblocking(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            supplied, state = clean_workflow_state_fixture(Path(raw))
            planted = json.loads(state.read_text(encoding="utf-8"))
            planted["plan"] = [planted["plan"][0]]
            state.write_text(json.dumps(planted), encoding="utf-8")

            code, report = run_status_evidence_report(supplied, state)

        self.assertEqual(code, 0, report)
        self.assertCompleteReport(report)
        self.assertTrue(report["missing_state_prefixes"], report)
        self.assertTrue(report["missing_state_post_items"], report)
        self.assertSelectedKeysEmpty(report)


class StatusEvidenceSourceGuidanceTests(unittest.TestCase):
    """The shipped source skills must describe the same scoped-gate contract."""

    def test_source_guidance_names_every_gated_key_and_the_nonblocking_rest(self) -> None:
        """Both skills must name all seven gated keys, not a subset.

        ``--rule status-evidence`` arms four workflow/state status-evidence
        checks plus the three current-run state-plan invariants; the guidance
        that names only the invariants understates what stops a run.
        """
        for label, path in (
            ("Claude", CLAUDE_AUTOPILOT_SKILL),
            ("Codex", CODEX_AUTOPILOT_SKILL),
        ):
            with self.subTest(skill=label):
                guidance = status_evidence_guidance_paragraph(path)
                folded = guidance.lower()
                self.assertIn("status-evidence checks", folded)
                self.assertIn("state-plan invariants", folded)
                self.assertIn("structural coverage checks", folded)
                self.assertIn("visible but never block", folded)
                for key in BLOCKING_STATUS_EVIDENCE_KEYS + BLOCKING_STATE_INVARIANT_KEYS:
                    self.assertIn(key, guidance)


class TrackedPathEnumerationTests(unittest.TestCase):
    """FR-013: tracked workflow/state discovery comes from the git index."""

    def test_tracked_workflow_state_paths_use_git_index_contract(self) -> None:
        stdout = (
            "specs/zeta/FEATURE-999-workflow.md\0"
            "docs/unrelated.md\0"
            "specs/alpha/autopilot-state.json\0"
            "specs/alpha/FEATURE-001-workflow.md\0"
        ).encode("utf-8")
        completed = subprocess.CompletedProcess(
            args=["git", "ls-files", "-z"],
            returncode=0,
            stdout=stdout,
            stderr=b"",
        )

        with mock.patch("subprocess.run", return_value=completed) as run:
            paths = tracked_workflow_state_paths(REPO_ROOT)

        run.assert_called_once_with(
            ["git", "ls-files", "-z"],
            cwd=REPO_ROOT,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        self.assertEqual(
            paths,
            (
                "specs/alpha/FEATURE-001-workflow.md",
                "specs/alpha/autopilot-state.json",
                "specs/zeta/FEATURE-999-workflow.md",
            ),
        )

    def test_git_index_enumeration_failure_is_not_silently_skipped(self) -> None:
        failure = subprocess.CalledProcessError(
            returncode=128,
            cmd=["git", "ls-files", "-z"],
            stderr=b"fatal: not a git repository",
        )

        with mock.patch("subprocess.run", side_effect=failure):
            with self.assertRaisesRegex(RuntimeError, "git ls-files -z failed"):
                tracked_workflow_state_paths(REPO_ROOT)


class AuthorityMatchedPairClassificationTests(unittest.TestCase):
    """FR-012/FR-015: only tracked adjacent workflow/state authority pairs qualify."""

    @staticmethod
    def _write_state(root: Path, rel_path: str, workflow_file: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"workflow_file": workflow_file, "plan": _clean_state_plan()}),
            encoding="utf-8",
        )

    def test_authority_pair_classification_matrix(self) -> None:
        cases = (
            (
                "eligible exact adjacent tracked pair",
                (
                    "specs/alpha/autopilot-state.json",
                    "specs/alpha/FEATURE-001-workflow.md",
                ),
                (
                    "specs/alpha/FEATURE-001-workflow.md",
                    "specs/alpha/autopilot-state.json",
                ),
                ((
                    "specs/alpha/FEATURE-001-workflow.md",
                    "specs/alpha/autopilot-state.json",
                ),),
                (),
                True,
            ),
            (
                "missing adjacent state",
                None,
                ("specs/missing/FEATURE-002-workflow.md",),
                (),
                ({
                    "workflow": "specs/missing/FEATURE-002-workflow.md",
                    "state": "specs/missing/autopilot-state.json",
                    "reason": "missing-adjacent-state",
                },),
                False,
            ),
            (
                "mismatched workflow authority",
                (
                    "specs/mismatch/autopilot-state.json",
                    "specs/other/FEATURE-003-workflow.md",
                ),
                (
                    "specs/mismatch/FEATURE-003-workflow.md",
                    "specs/mismatch/autopilot-state.json",
                ),
                (),
                ({
                    "workflow": "specs/mismatch/FEATURE-003-workflow.md",
                    "state": "specs/mismatch/autopilot-state.json",
                    "reason": "workflow-file-mismatch",
                    "workflow_file": "specs/other/FEATURE-003-workflow.md",
                },),
                False,
            ),
            (
                "untracked adjacent state",
                (
                    "specs/untracked/autopilot-state.json",
                    "specs/untracked/FEATURE-004-workflow.md",
                ),
                ("specs/untracked/FEATURE-004-workflow.md",),
                (),
                ({
                    "workflow": "specs/untracked/FEATURE-004-workflow.md",
                    "state": "specs/untracked/autopilot-state.json",
                    "reason": "untracked-adjacent-state",
                },),
                False,
            ),
            (
                "matching but non-adjacent state",
                (
                    "specs/elsewhere/autopilot-state.json",
                    "specs/synthetic/FEATURE-005-workflow.md",
                ),
                (
                    "specs/elsewhere/autopilot-state.json",
                    "specs/synthetic/FEATURE-005-workflow.md",
                ),
                (),
                ({
                    "workflow": "specs/synthetic/FEATURE-005-workflow.md",
                    "state": "specs/synthetic/autopilot-state.json",
                    "reason": "missing-adjacent-state",
                },),
                False,
            ),
        )

        for label, state_record, tracked, eligible, excluded, assert_whole in cases:
            with self.subTest(case=label):
                with tempfile.TemporaryDirectory() as raw:
                    root = Path(raw)
                    if state_record is not None:
                        state_path, workflow_file = state_record
                        self._write_state(root, state_path, workflow_file)
                    result = classify_authority_matched_pairs(root, tracked)

                if assert_whole:
                    self.assertEqual(
                        result,
                        {"eligible": eligible, "excluded": excluded},
                    )
                else:
                    self.assertEqual(result["eligible"], eligible)
                    self.assertEqual(result["excluded"], excluded)

    def test_tracked_state_failure_matrix(self) -> None:
        cases = (
            (
                "tracked-state read OSError including path",
                "specs/read/FEATURE-006-workflow.md",
                "specs/read/autopilot-state.json",
                OSError,
                "directory",
            ),
            (
                "tracked-state JSON ValueError including path",
                "specs/bad-json/FEATURE-007-workflow.md",
                "specs/bad-json/autopilot-state.json",
                ValueError,
                "invalid-json",
            ),
        )

        for label, workflow, state_path, error_type, fixture_kind in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                state = root / state_path
                state.parent.mkdir(parents=True, exist_ok=True)
                if fixture_kind == "directory":
                    state.mkdir()
                else:
                    state.write_text("{not-json", encoding="utf-8")

                with self.assertRaisesRegex(error_type, state_path):
                    classify_authority_matched_pairs(
                        root,
                        (workflow, state_path),
                    )


class TrackedPairCorpusTests(StatusEvidenceReportAssertions, unittest.TestCase):
    """FR-012/FR-014: live tracked authority-matched pairs stay valid."""

    def test_tracked_authority_matched_pair_corpus_reconciles_and_passes(self) -> None:
        tracked_paths = tracked_workflow_state_paths(REPO_ROOT)
        workflow_candidates = tuple(
            path for path in tracked_paths if path.endswith("-workflow.md")
        )
        classified = classify_authority_matched_pairs(REPO_ROOT, tracked_paths)
        eligible = classified["eligible"]
        exclusions = classified["excluded"]

        invoked: list[tuple[str, str]] = []
        passed: list[tuple[str, str]] = []
        for workflow_ref, state_ref in eligible:
            code, report = run_status_evidence_report(REPO_ROOT / workflow_ref, REPO_ROOT / state_ref)
            invoked.append((workflow_ref, state_ref))
            self.assertCompleteReport(report)
            if code == 0:
                passed.append((workflow_ref, state_ref))
            else:
                self.fail(f"tracked pair {workflow_ref} failed status-evidence: {report}")

        self.assertGreater(len(workflow_candidates), 0)
        self.assertGreater(len(eligible), 0)
        self.assertEqual(len(invoked), len(eligible))
        self.assertEqual(len(passed), len(eligible))
        self.assertEqual(len(eligible) + len(exclusions), len(workflow_candidates))
        self.assertEqual(
            {entry["workflow"] for entry in exclusions},
            set(workflow_candidates) - {workflow for workflow, _state in eligible},
        )
        for entry in exclusions:
            with self.subTest(workflow=entry["workflow"]):
                self.assertIn("reason", entry)
                self.assertTrue(entry["reason"])



def _synthetic_home_path(*parts: str) -> str:
    """A home-style path built at run time, so this file never commits one."""
    return "/".join(("", "home", "synthoperator", *parts))


def _redacted_stage_resolution() -> dict:
    return {
        "stage": "implement",
        "source": "argv",
        "basis": "explicit --stage implement",
        "recorded_stage": "plan",
        "planning_complete": True,
        "confidence_gate_status": "Complete",
    }


class StatePrivacyTests(StatusEvidenceReportAssertions, unittest.TestCase):
    """Issue 770: the tracked state file holds decision fields, never private values."""

    def _report_for(self, extra: dict) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as raw:
            supplied, state = clean_workflow_state_fixture(Path(raw))
            planted = json.loads(state.read_text(encoding="utf-8"))
            planted.update(extra)
            state.write_text(json.dumps(planted), encoding="utf-8")
            return run_status_evidence_report(supplied, state)

    def test_private_values_fail_the_status_evidence_gate(self) -> None:
        interpreter = _synthetic_home_path(".venv", "bin", "python3")
        windows_home = "C:" + "\\" + "Users" + "\\" + "synthoperator" + "\\" + "repo"
        task_uuid = str(uuid.uuid4())
        cases = (
            (
                "raw runner envelope with argv",
                {"stage_resolution": {**_redacted_stage_resolution(), "argv": ["--stage", "implement"]}},
                "argv",
                "autopilot_state.stage_resolution.argv",
            ),
            (
                "absolute home path value",
                {"stage_resolution": {**_redacted_stage_resolution(), "interpreter": interpreter}},
                interpreter,
                "autopilot_state.stage_resolution.interpreter",
            ),
            (
                "windows home path inside a list",
                {"notes": ["ok", windows_home]},
                windows_home,
                "autopilot_state.notes[1]",
            ),
            (
                "raw delegation task id",
                {"delegation": {"task_id": task_uuid}},
                task_uuid,
                "autopilot_state.delegation.task_id",
            ),
            (
                "home path used as a key",
                {"evidence": {interpreter: "seen"}},
                interpreter,
                "autopilot_state.evidence",
            ),
        )
        for label, extra, private_value, location in cases:
            with self.subTest(case=label):
                code, report = self._report_for(extra)
                self.assertEqual(code, 1, report)
                self.assertCompleteReport(report)
                self.assertOnlySelectedProblemKeyPopulated(report, "state_privacy_errors")
                joined = "\n".join(report["state_privacy_errors"])
                self.assertIn(location, joined)
                if private_value != "argv":
                    self.assertNotIn(private_value, joined)

    def test_private_key_error_names_the_key_by_its_digest(self) -> None:
        """#800 review: a private key is identified by its digest, never echoed, one error per key."""
        first, second = str(uuid.uuid4()), str(uuid.uuid4())
        code, report = self._report_for({"evidence": {first: "a", second: "b", "ok": "c"}})
        self.assertEqual(code, 1, report)
        errors = report["state_privacy_errors"]
        self.assertEqual(len(errors), 2, errors)
        for key in (first, second):
            digest = "sha256:" + hashlib.sha256(key.encode("utf-8")).hexdigest()
            self.assertEqual(sum(digest in error for error in errors), 1, errors)
            self.assertFalse(any(key in error for error in errors), errors)

    def test_redacted_decision_fields_pass(self) -> None:
        code, report = self._report_for({
            "stage": "implement",
            "stage_resolution": _redacted_stage_resolution(),
            "delegation": {"task_ref": "sha256:" + "0" * 64, "run_ref": uuid.uuid4().hex},
        })
        self.assertEqual(code, 0, report)
        self.assertEqual(report["state_privacy_errors"], [])

    def test_native_event_id_error_names_the_digest_remedy(self) -> None:
        """#800: the error names the field and the exact in-place remedy; the digest form passes."""
        event_id = "msg_" + str(uuid.uuid4())
        field = {"implementation_startup": {"active_batch": {"operator_approval_event_id": event_id}}}
        code, report = self._report_for(field)
        self.assertEqual(code, 1, report)
        self.assertOnlySelectedProblemKeyPopulated(report, "state_privacy_errors")
        [error] = report["state_privacy_errors"]
        self.assertIn("autopilot_state.implementation_startup.active_batch.operator_approval_event_id", error)
        self.assertIn("sha256:", error)
        self.assertIn("rerun this guard", error)
        self.assertNotIn(event_id, error)
        digest = "sha256:" + hashlib.sha256(event_id.encode("utf-8")).hexdigest()
        field["implementation_startup"]["active_batch"]["operator_approval_event_id"] = digest
        code, report = self._report_for(field)
        self.assertEqual(code, 0, report)
        self.assertEqual(report["state_privacy_errors"], [])

    def test_both_hosts_digest_event_ids_and_remediate_privacy_errors_once(self) -> None:
        """#800: store native event ids as digests; a privacy-only failure is fixed in place, once."""
        for skill_path in (CLAUDE_AUTOPILOT_SKILL, CODEX_AUTOPILOT_SKILL):
            with self.subTest(skill=skill_path.parent.parent.name):
                skill = _flat(skill_path)
                self.assertIn("native or operator event id", skill)
                self.assertIn("`sha256:<digest>`", skill)
                self.assertIn("When `state_privacy_errors` is the only failing gated key", skill)
                self.assertIn("rerun the guard once", skill)
                self.assertIn("A second failure, or any other failing gated key, is a stop", skill)

    def test_both_hosts_account_for_the_implementation_notes_record(self) -> None:
        """#801: the notes record is committed, exempt from the path budget, and never dirties apply."""
        for name in ("skills/speckit-autopilot/references/phase-execution.md",
                     "codex-skills/speckit-autopilot/references/phase-execution-codex.md"):
            with self.subTest(file=name):
                text = _flat(REPO_ROOT / "speckit-pro" / name)
                self.assertIn("stage it with each marker checkpoint commit", text)
                self.assertIn("`declared_files.implementation_notes`", text)
                self.assertIn("clean-worktree check ignores it", text)

    def test_validator_patterns_match_the_repository_privacy_scan(self) -> None:
        self.assertEqual(
            validator.STATE_HOME_PATH_PATTERN.pattern,
            privacy_patterns.HOME_PATH_PATTERN.pattern,
        )
        self.assertEqual(
            validator.STATE_HYPHENATED_HOME_PATH_PATTERN.pattern,
            privacy_patterns.HYPHENATED_HOME_PATH_PATTERN.pattern,
        )
        self.assertEqual(
            validator.STATE_UUID_PATTERN.pattern,
            privacy_patterns.UUID_PATTERN.pattern,
        )


MARKER_CHECKPOINT_REF = "specs/demo/.process/checkpoints/M1.json"
MARKER_VERIFICATION_REF = "specs/demo/.process/verification/M1.json"


class MarkerEvidencePrivacyTests(StatusEvidenceReportAssertions, unittest.TestCase):
    """#819: committed marker evidence cites external ids as digests, never raw."""

    def _report_for(self, checkpoint: bytes | None, verification: bytes | None) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            supplied, state = clean_workflow_state_fixture(root)
            planted = json.loads(state.read_text(encoding="utf-8"))
            planted["feature_dir"] = "specs/demo"
            planted["pr_marker_plan"] = {"markers": [{"marker_id": "M1", "implementation_checkpoint": {
                "evidence_path": MARKER_CHECKPOINT_REF, "verification_evidence_path": MARKER_VERIFICATION_REF}}]}
            state.write_text(json.dumps(planted), encoding="utf-8")
            for ref, content in ((MARKER_CHECKPOINT_REF, checkpoint), (MARKER_VERIFICATION_REF, verification)):
                if content is not None:
                    (root / ref).parent.mkdir(parents=True, exist_ok=True)
                    (root / ref).write_bytes(content)
            return run_status_evidence_report(supplied, state)

    def test_raw_task_id_in_checkpoint_evidence_names_the_field_and_digest_remedy(self) -> None:
        task_id = str(uuid.uuid4())
        evidence = {"verification": {"G7": {"status": "pass", "evidence": f"delegated audit {task_id} passed"}}}
        code, report = self._report_for(json.dumps(evidence).encode("utf-8"), b"{}")
        self.assertEqual(code, 1, report)
        self.assertCompleteReport(report)
        self.assertOnlySelectedProblemKeyPopulated(report, "marker_evidence_privacy_errors")
        [error] = report["marker_evidence_privacy_errors"]
        self.assertIn(MARKER_CHECKPOINT_REF, error)
        self.assertIn("verification.G7.evidence", error)
        self.assertIn("a raw UUID", error)
        self.assertIn("sha256:", error)
        self.assertIn("rerun this guard", error)
        self.assertNotIn(task_id, error)

    def test_raw_event_id_in_verification_evidence_fails(self) -> None:
        event_id = str(uuid.uuid4())
        code, report = self._report_for(b"{}", json.dumps({"results": [{"event_id": event_id}]}).encode("utf-8"))
        self.assertEqual(code, 1, report)
        self.assertOnlySelectedProblemKeyPopulated(report, "marker_evidence_privacy_errors")
        [error] = report["marker_evidence_privacy_errors"]
        self.assertIn(MARKER_VERIFICATION_REF, error)
        self.assertIn("results[0].event_id", error)
        self.assertNotIn(event_id, error)

    def test_unparseable_evidence_is_scanned_as_text(self) -> None:
        home = _synthetic_home_path("repo")
        code, report = self._report_for(f"not json {home}".encode("utf-8"), None)
        self.assertEqual(code, 1, report)
        [error] = report["marker_evidence_privacy_errors"]
        self.assertIn(MARKER_CHECKPOINT_REF, error)
        self.assertIn("an absolute home path", error)
        self.assertNotIn(home, error)

    def test_digest_form_and_pending_marker_without_files_pass(self) -> None:
        task_id = str(uuid.uuid4())
        digest = "sha256:" + hashlib.sha256(task_id.encode("utf-8")).hexdigest()
        evidence = json.dumps({"verification": {"G7": {"status": "pass", "evidence": f"audit {digest}"}}})
        for label, checkpoint, verification in (("digest", evidence.encode("utf-8"), b"{}"), ("pending", None, None)):
            with self.subTest(case=label):
                code, report = self._report_for(checkpoint, verification)
                self.assertEqual(code, 0, report)
                self.assertEqual(report["marker_evidence_privacy_errors"], [])

    def test_both_hosts_digest_external_ids_in_every_committed_record(self) -> None:
        for skill_path in (CLAUDE_AUTOPILOT_SKILL, CODEX_AUTOPILOT_SKILL):
            with self.subTest(skill=skill_path.parent.parent.name):
                skill = _flat(skill_path)
                self.assertIn("external task, session, thread, or event id cited in a committed record", skill)
                self.assertIn("`marker_evidence_privacy_errors`", skill)
        for name in ("skills/speckit-autopilot/references/phase-execution.md",
                     "codex-skills/speckit-autopilot/references/phase-execution-codex.md"):
            with self.subTest(file=name):
                text = _flat(REPO_ROOT / "speckit-pro" / name)
                self.assertIn("external task, session, thread, or event id", text)
                for record in ("marker checkpoint", "verification report", "workflow file", "implementation notes",
                               "PR body"):
                    self.assertIn(record, text)


class StatusEvidenceNegativeTests(StatusEvidenceReportAssertions, unittest.TestCase):
    """FEATURE-017 isolated state-invariant controls for the status-evidence gate."""

    def test_isolated_state_invariant_failure_matrix(self) -> None:
        def plant_in_progress_errors(plan: list[dict]) -> None:
            plan[0]["status"] = "in_progress"
            plan[1]["status"] = "in_progress"

        def plant_duplicate_state_steps(plan: list[dict]) -> None:
            plan.append(dict(plan[0]))

        def plant_state_order_errors(plan: list[dict]) -> None:
            plan[0], plan[1] = plan[1], plan[0]

        cases = (
            (
                "in-progress invariant only",
                "in_progress_errors",
                plant_in_progress_errors,
            ),
            (
                "duplicate-step invariant only",
                "duplicate_state_steps",
                plant_duplicate_state_steps,
            ),
            (
                "state-order invariant only",
                "state_order_errors",
                plant_state_order_errors,
            ),
        )

        for label, problem_key, plant_fault in cases:
            with self.subTest(case=label):
                with tempfile.TemporaryDirectory() as raw:
                    supplied, state = clean_workflow_state_fixture(Path(raw))
                    planted = json.loads(state.read_text(encoding="utf-8"))
                    plant_fault(planted["plan"])
                    state.write_text(json.dumps(planted), encoding="utf-8")

                    code, report = run_status_evidence_report(supplied, state)

                self.assertCompleteReport(report)
                self.assertOnlySelectedProblemKeyPopulated(report, problem_key)
                self.assertEqual(code, 1, report)


class WorkflowAuthorityTests(unittest.TestCase):
    """`autopilot-state.json.workflow_file` is the authority on which workflow a run may touch.

    The FR-012 controlled pair shares one fixture builder whose only parameter is
    the state's ``workflow_file`` value, so each failure names its own claim
    rather than the fixture.
    """

    #: FR-009 fixes the opening sentence. Assert the prefix and never the full
    #: string, so the appended paths can be reformatted without breaking this.
    AUTHORITY_PREFIX = (
        "supplied workflow does not match autopilot state workflow_file authority"
    )

    @staticmethod
    def _plant(root: Path, state_workflow_ref: str) -> tuple[Path, Path]:
        """Lay out a repository-shaped fixture and return (supplied workflow, state)."""
        # Repository-relative against this root. An absolute value is rejected
        # as malformed before the comparison is ever reached.
        return clean_workflow_state_fixture(root, state_workflow_ref=state_workflow_ref)

    def _run(self, state_workflow_ref: str) -> tuple[int, dict]:
        """Invoke the guard exactly as the autopilot does, varying one value.

        The autopilot's own invocation is `--rule status-evidence` with no commit
        flags and a state carrying no `pr_marker_plan`.
        """
        with tempfile.TemporaryDirectory() as raw:
            supplied, state = self._plant(Path(raw), state_workflow_ref)
            completed = subprocess.run(
                [sys.executable, str(VALIDATOR),
                 "--workflow", str(supplied), "--state", str(state),
                 "--rule", "status-evidence"],
                text=True, capture_output=True, check=False,
            )
            return completed.returncode, json.loads(completed.stdout)

    def test_state_naming_a_different_workflow_halts_the_run(self) -> None:
        """FR-012's negative control: the run this specification exists to stop."""
        code, report = self._run(OTHER_WORKFLOW_REF)
        self.assertEqual(code, 1, report)
        self.assertIn("workflow_authority_errors", report)
        errors = report["workflow_authority_errors"]
        self.assertTrue(errors, report)
        self.assertTrue(errors[0].startswith(self.AUTHORITY_PREFIX), errors[0])

    def test_state_naming_the_supplied_workflow_allows_the_run(self) -> None:
        """FR-012's positive control: the same fixture, one value different.

        It differs from the negative control in exactly one value, the state's
        ``workflow_file``, and it is a separate method rather than a parameter so
        each failure names its own claim. This is what proves the negative
        control detects a mismatch rather than failing everything.
        """
        code, report = self._run(SUPPLIED_WORKFLOW_REF)
        self.assertEqual(code, 0, report)
        self.assertIn("workflow_authority_errors", report)
        self.assertEqual(report["workflow_authority_errors"], [])

    def test_state_named_relatively_from_a_subdirectory_is_still_compared(self) -> None:
        """FR-006b: evaluating depends on where the state *is*, not how it is spelled.

        This state sits inside the repository fixture exactly as the controlled
        pair's does, and names a mismatching workflow exactly as the negative
        control's does. Only the spelling differs: it is named by a relative path
        from a subdirectory. Root resolution walked the parents of the path *as
        supplied*, whose chain terminated at the working directory, so no marker
        was found and the comparison skipped while the state file sat untouched
        inside the tree.

        This control is what separates FR-006b's repair from a no-op. The FR-006
        verdict for a state genuinely outside any repository is deliberately
        unchanged: there is still no marker to find, so it still skips.
        """
        with tempfile.TemporaryDirectory() as raw:
            supplied, state = self._plant(Path(raw), OTHER_WORKFLOW_REF)
            completed = subprocess.run(
                [sys.executable, str(VALIDATOR),
                 "--workflow", str(supplied), "--state", state.name,
                 "--rule", "status-evidence"],
                cwd=str(state.parent),
                text=True, capture_output=True, check=False,
            )
            report = json.loads(completed.stdout)
        self.assertIn("workflow_authority_errors", report)
        self.assertTrue(report["workflow_authority_errors"], report)
        # The exit code too, and not only the report key. Reporting a finding the
        # scoped invocation does not gate on is the defect this specification
        # exists to close, so a control that stops at the key would still pass if
        # the key left the ``status-evidence`` tuple.
        self.assertEqual(completed.returncode, 1, report)

    def test_state_without_a_workflow_file_key_skips_the_comparison(self) -> None:
        """FR-003: a state that names no workflow asserts no authority.

        Deliberately outside the FR-012 pair, so that pair keeps differing in
        exactly one value. This is the one branch neither control reaches: both
        set ``workflow_file``, and ``RuleScopingTests`` sets it too while
        reaching the unresolvable-root skip rather than this one. The fixture
        root carries its repository marker, so the skip is attributable to the
        absent field rather than to a root that could not be resolved. It is the
        branch that keeps the tracked state slot carrying no ``workflow_file``
        validating, and the one the corpus evidence structurally cannot cover,
        because every synthesized corpus state sets the field.
        """
        with tempfile.TemporaryDirectory() as raw:
            supplied, state = self._plant(Path(raw), SUPPLIED_WORKFLOW_REF)
            # Remove the key itself, never null it: an explicitly nulled field is
            # malformed, and only key membership distinguishes the two.
            planted = json.loads(state.read_text(encoding="utf-8"))
            del planted["workflow_file"]
            state.write_text(json.dumps(planted), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(VALIDATOR),
                 "--workflow", str(supplied), "--state", str(state),
                 "--rule", "status-evidence"],
                text=True, capture_output=True, check=False,
            )
            report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, report)
        self.assertIn("workflow_authority_errors", report)
        self.assertEqual(report["workflow_authority_errors"], [])

    def test_malformed_workflow_file_fails_as_malformed_not_as_a_mismatch(self) -> None:
        """FR-005: a garbage value cannot become a silent opt-out.

        Branch 3 of FR-004d's ordering, which no other test reaches. The two
        assertions that matter are the exit code and the *attribution*: the
        whitespace-only case must be caught by the explicit malformed check
        rather than falling through to the identity branch, because
        ``_is_normalized_repo_path`` accepts a run of spaces as a valid path
        part. If it fell through, the operator would see the identity message
        with a blank path in it and the verdict would be right by accident.
        """
        for label, value in (
            ("whitespace only", "   "),
            ("empty string", ""),
            ("absolute path", "/etc/workflow.md"),
            ("parent traversal", "../outside-workflow.md"),
            ("explicit null", None),
            ("non-string", 42),
        ):
            with self.subTest(malformed=label):
                code, report = self._run(value)
                self.assertEqual(code, 1, report)
                errors = report["workflow_authority_errors"]
                self.assertTrue(errors, report)
                self.assertFalse(
                    errors[0].startswith(self.AUTHORITY_PREFIX),
                    f"{label} was reported as an identity mismatch rather than as "
                    f"malformed: {errors[0]}",
                )

    def test_supplied_workflow_outside_the_repository_fails(self) -> None:
        """FR-004c: a completed evaluation with an out-of-boundary result fails.

        Branch 4 of FR-004d's ordering, which no other test reaches. This is the
        branch a unanimous three-lens consensus settled as a failure rather than
        a skip, on the grounds that a path escaping the root is an affirmative
        anomaly and not the absence of information FR-006 covers. It reuses the
        sentence the guard already emitted for this condition, so the assertion
        deliberately checks that the identity prefix is *not* used.
        """
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "repo"
            root.mkdir()
            _, state = self._plant(root, SUPPLIED_WORKFLOW_REF)
            # A workflow that exists but resolves outside the resolved root.
            outside = Path(raw) / "outside-workflow.md"
            outside.write_text(
                workflow(("Specify", "✅ Complete"), body="G1 gate: PASS"), encoding="utf-8"
            )
            completed = subprocess.run(
                [sys.executable, str(VALIDATOR),
                 "--workflow", str(outside), "--state", str(state),
                 "--rule", "status-evidence"],
                text=True, capture_output=True, check=False,
            )
            report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1, report)
        errors = report["workflow_authority_errors"]
        self.assertTrue(errors, report)
        self.assertIn("outside the authorized repository", errors[0])
        self.assertFalse(errors[0].startswith(self.AUTHORITY_PREFIX), errors[0])


class RepositoryRootResolutionTests(unittest.TestCase):
    """A resolution failure must skip, never escape as a traceback."""

    def test_unresolvable_path_returns_none_instead_of_raising(self) -> None:
        """`main()` catches only ValidationError, so anything else prints a
        traceback where the autopilot expects a JSON report. Today this is hard
        to reach because ``load_state`` reads the state file first, but that is
        a property of the caller, not of this function, and four call sites rely
        on it. The guard makes the function safe on its own terms.
        """
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            target = root / "unresolvable" / "state.json"
            original_resolve = Path.resolve
            for error in (OSError("unresolvable"), RuntimeError("unresolvable")):
                with self.subTest(error=type(error).__name__):
                    def resolve(path, *args, **kwargs):
                        if path == target:
                            raise error
                        return original_resolve(path, *args, **kwargs)

                    with mock.patch.object(Path, "resolve", resolve):
                        self.assertIsNone(validator._repository_root(target))

    def test_an_unresolvable_supplied_workflow_skips_instead_of_raising(self) -> None:
        """The authority helper resolves a second path, and it must not raise either.

        ``_repository_root`` is guarded, so the same fixture that proves that
        guard also reaches the helper's own ``workflow.resolve()``. The state
        file here is a real readable path inside a marked root, so the helper
        gets past branches 1 and 2 and reaches the resolution of the *supplied*
        workflow. A raise there escapes ``build_report``, which has no handler,
        and then ``main()``, which catches only ``ValidationError`` -- printing a
        traceback where the autopilot expects the JSON report.
        """
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".git").write_text(
                "gitdir: ../elsewhere/.git/worktrees/fixture\n", encoding="utf-8"
            )
            state = root / "autopilot-state.json"
            state.write_text(
                json.dumps({"workflow_file": SUPPLIED_WORKFLOW_REF, "plan": []}),
                encoding="utf-8",
            )
            supplied = root / "unresolvable" / "supplied-workflow.md"
            original_resolve = Path.resolve
            for error in (OSError("unresolvable"), RuntimeError("unresolvable")):
                with self.subTest(error=type(error).__name__):
                    def resolve(path, *args, **kwargs):
                        if path == supplied:
                            raise error
                        return original_resolve(path, *args, **kwargs)

                    with mock.patch.object(Path, "resolve", resolve):
                        self.assertEqual(
                            validator._workflow_authority_errors(
                                supplied,
                                state,
                                {"workflow_file": SUPPLIED_WORKFLOW_REF},
                            ),
                            [],
                        )


class ProblemKeyClassificationTests(unittest.TestCase):
    """FR-011: every problem key the guard emits carries a recorded verdict.

    The emitted set is derived from a real report and never from a second
    hardcoded list, because a parallel list drifts out of step exactly as the
    classification record itself could -- which is the failure mode being closed.
    """

    #: FR-010 fixes a closed three-value vocabulary. Spelled out here rather than
    #: read back from the guard: deriving it from the module under test would let
    #: a fourth verdict added there pass unnoticed, and "closed" is precisely the
    #: property this test exists to hold.
    VERDICTS = frozenset({"gated", "advisory-deliberate", "advisory-accidental"})

    #: Report fields that describe the run rather than name a finding.
    METADATA_KEYS = frozenset({"status", "workflow_file", "state_file", "plan_step_count"})

    @classmethod
    def setUpClass(cls) -> None:
        cls.emitted = cls._emitted_problem_keys()

    @classmethod
    def _emitted_problem_keys(cls) -> set[str]:
        """Every problem key of a real report, minus the metadata fields.

        One report is the complete set rather than a sample because every
        per-check function returns its full key set on every return path,
        including its early returns, so no key is ever conditionally absent.
        That is a property of the guard this test relies on rather than one it
        checks. The limit follows directly: a future key emitted only under some
        state shapes would be absent from this fixture's report and would pass
        unclassified. The response then is to extend this fixture to a state
        shape that emits it, never to relax the assertion.

        The fixture carries a repository marker so the checks that resolve a
        root evaluate for real instead of taking their unresolvable-root skip.
        """
        with tempfile.TemporaryDirectory() as raw:
            supplied, state = clean_workflow_state_fixture(Path(raw))
            # The autopilot's own invocation. The full report prints under every
            # rule, so scoping changes the exit code and never the key set.
            completed = subprocess.run(
                [sys.executable, str(VALIDATOR),
                 "--workflow", str(supplied), "--state", str(state),
                 "--rule", "status-evidence"],
                text=True, capture_output=True, check=False,
            )
        report = json.loads(completed.stdout)
        return set(report) - cls.METADATA_KEYS

    def test_every_emitted_problem_key_carries_a_verdict(self) -> None:
        """SC-005: adding a problem key without recording a verdict fails here."""
        missing = sorted(self.emitted - set(validator.PROBLEM_KEY_INTENT))
        self.assertFalse(
            missing,
            "the guard emits problem keys with no PROBLEM_KEY_INTENT verdict: "
            + ", ".join(missing),
        )

    def test_the_record_classifies_nothing_the_guard_never_emits(self) -> None:
        """The other direction, which the completeness check alone does not cover.

        A verdict recorded for a key the report never emits is dead weight that
        reads as coverage. Checking only ``emitted - intent`` would let the record
        accumulate entries for keys that were renamed or removed, and the record
        would still look complete. Both directions together are what make the
        record an accurate census rather than a superset.
        """
        extraneous = sorted(set(validator.PROBLEM_KEY_INTENT) - self.emitted)
        self.assertFalse(
            extraneous,
            "PROBLEM_KEY_INTENT classifies keys the guard never emits: "
            + ", ".join(extraneous),
        )

    def test_the_gated_verdict_agrees_with_the_rule_map(self) -> None:
        """A `gated` verdict is a claim about ``RULE_PROBLEM_KEYS``, so check it there.

        ``verdict == "gated"`` says a named rule can move the exit code on that
        key, which is decided entirely by membership in ``RULE_PROBLEM_KEYS``.
        Recording it by hand in a second place is how the two drift: arm a key in
        the rule map and leave it advisory here, or retire it from the rule map
        and leave the verdict behind, and every other assertion in this class
        still passes. The record would then misdescribe exactly the property it
        exists to make visible.
        """
        gated_by_record = {
            key
            for key, entry in validator.PROBLEM_KEY_INTENT.items()
            if entry["verdict"] == "gated"
        }
        gated_by_rules = {
            key for keys in validator.RULE_PROBLEM_KEYS.values() for key in keys
        }
        self.assertEqual(
            gated_by_record,
            gated_by_rules,
            "PROBLEM_KEY_INTENT and RULE_PROBLEM_KEYS disagree about which keys are "
            f"gated; recorded-only {sorted(gated_by_record - gated_by_rules)}, "
            f"rule-only {sorted(gated_by_rules - gated_by_record)}",
        )

    def test_every_verdict_is_drawn_from_the_closed_vocabulary(self) -> None:
        """FR-010: three values, and a fourth is not a value."""
        outside = sorted(
            f"{key}={entry['verdict']!r}"
            for key, entry in validator.PROBLEM_KEY_INTENT.items()
            if entry["verdict"] not in self.VERDICTS
        )
        self.assertFalse(
            outside,
            "verdicts outside the closed vocabulary " + repr(sorted(self.VERDICTS)) + ": "
            + ", ".join(outside),
        )

    def test_every_entry_carries_a_reason(self) -> None:
        """FR-010a: a verdict without a stated reason records nothing."""
        reasonless = sorted(
            key
            for key, entry in validator.PROBLEM_KEY_INTENT.items()
            if not isinstance(entry["reason"], str) or not entry["reason"].strip()
        )
        self.assertFalse(
            reasonless,
            "classification entries carrying no reason: " + ", ".join(reasonless),
        )


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for case in (
        WorkflowStatusEvidenceTests,
        StateStatusSchemaTests,
        AutonomyBoundarySourceContractTests,
        BlockedActionDeferralSourceContractTests,
        FailureClassApprovalSourceContractTests,
        AmbiguousTaskWordingSourceContractTests,
        GateFailureDeferSourceContractTests,
        GateTaskEvidenceLoopGuidanceTests,
        MidRunPluginDriftSourceContractTests,
        StandingPolicyPreflightSourceContractTests,
        AutonomyBoundaryAuthorizationTests,
        AutonomyBoundaryFreshnessTests,
        AutonomyBoundaryMalformedExecutionTests,
        AutonomyBoundaryNegativeAuthorizationTests,
        AutonomyBoundaryStageTests,
        RuleScopingTests,
        AutonomyBoundaryCliTests,
        CleanStatusEvidenceControlTests,
        LegacyCoverageAdvisoryTests,
        StatusEvidenceSourceGuidanceTests,
        TrackedPathEnumerationTests,
        AuthorityMatchedPairClassificationTests,
        TrackedPairCorpusTests,
        StatusEvidenceNegativeTests,
        StatePrivacyTests,
        MarkerEvidencePrivacyTests,
        WorkflowAuthorityTests,
        RepositoryRootResolutionTests,
        ProblemKeyClassificationTests,
        RunFinalizationSourceContractTests,
    ):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-autopilot-bookkeeping-guard")


if __name__ == "__main__":
    raise SystemExit(main())
