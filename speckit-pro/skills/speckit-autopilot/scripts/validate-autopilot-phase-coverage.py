#!/usr/bin/env python3
"""Validate that an autopilot workflow/state pair keeps every phase visible.

Claude Code and Codex both run this script. Only `--require-autonomy-boundary` makes the
Codex Phase 6.5 autonomy record mandatory.

Maintainer notes on the ``workflow_file`` authority check
(``_workflow_authority_errors``), moved here from
``references/workflow-file-protocol.md``:

Three outcomes skip rather than fail: a state with no ``workflow_file`` key, no
resolvable repository root, and a supplied path that cannot be traversed. All
three leave the run indistinguishable from one that ran the comparison and
passed it, because a skip and a satisfied comparison both report no error and
both exit zero. The exit code carries the verdict, not whether the verdict was
computed.

This is the trap when reading corpus evidence. The report always carries
``workflow_authority_errors``, so an empty value proves only that this guard is
running, never that the comparison ran. Presence separates this code from older
code, where the key is absent entirely. It does not separate a satisfied
comparison from a skipped one. To prove a comparison ran, vary an input and show
the verdict change.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


WORKFLOW_SECTIONS = (
    "## Phase 1: Specify",
    "## Phase 2: Clarify",
    "## Phase 3: Plan",
    "## Phase 4: Domain Checklists",
    "## Phase 5: Tasks",
    "## Phase 6: Analyze",
    "## Phase 6.5:",
    "## Phase 7: Implement",
    "## Post-Implementation Checklist",
)

WORKFLOW_TOKENS = (
    "| Confidence Gate | G6.5 |",
    "| Post |",
    "| G6.5 |",
)

STATE_PREFIXES = (
    "Archive Sweep:",
    "Phase 0: Prerequisites",
    "Phase 1: Specify",
    "Phase 2: Clarify",
    "Phase 3: Plan",
    "Phase 4: Checklist",
    "Phase 5: Tasks",
    "Phase 6: Analyze",
    "Phase 6.5: Confidence Gate",
    "Phase 7: Implement",
)

POST_STEPS = (
    "Post: Doctor Extension Check",
    "Post: Verify Implementation",
    "Post: Verify Tasks Phantom Check",
    "Post: Code Review",
    "Post: Integration Suite",
    "Post: Reviewability Diff Gate",
    "Post: UAT Runbook Generation",
    "Post: PR Body Generation",
    "Post: PR Creation",
    "Post: Review Remediation",
    "Post: Retrospective",
)

ORDERED_STATE_CHECKPOINTS = (
    "Archive Sweep:",
    "Phase 0: Prerequisites",
    "Phase 1: Specify",
    "Phase 2: Clarify",
    "Phase 3: Plan",
    "Phase 4: Checklist",
    "Phase 5: Tasks",
    "Phase 6: Analyze",
    "Phase 6.5: Confidence Gate",
    "Phase 7: Implement",
    "Post: Doctor Extension Check",
    "Post: Retrospective",
)

TASK_LINE_RE = re.compile(r"^- \[[ xX]\] (T[0-9]+)\b")
UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
# The tracked state file stores decision fields only. These three patterns match
# the repository privacy scan's (tests/speckit-pro/lib/privacy_patterns.py), and a
# test holds them equal, so the state guard rejects what the scan would reject.
STATE_HOME_PATH_PATTERN = re.compile(
    r"(?:/(?:Users|home)/|[A-Za-z]:[\\/]+Users[\\/]+)[A-Za-z0-9_.\-]+",
    re.IGNORECASE,
)
STATE_HYPHENATED_HOME_PATH_PATTERN = re.compile(r"-Users-[A-Za-z0-9_.\-]+", re.IGNORECASE)
STATE_UUID_PATTERN = re.compile(
    r"[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}",
    re.IGNORECASE,
)
STATE_PRIVATE_KEYS = frozenset({"argv"})
# The plugin root is fixed by this script's own location, never by request input.
INSTALLED_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
# The plugin ships the runner beside its skills, so its validator is imported, not copied.
if str(INSTALLED_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(INSTALLED_PLUGIN_ROOT))
from speckit_pro_runner.json_schema import json_schema_failures, json_values_equal  # noqa: E402

_LIB_DIR = str(Path(__file__).resolve().parent / "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)
from phase_coverage_git import (  # noqa: E402
    _git_changed_paths,
    _git_commit_exists,
    _git_commit_is_ancestor,
    _git_commit_is_ancestor_of_head,
    _git_commit_is_strict_ancestor,
    _git_common_dir,
    _git_env,
    _git_file_at_commit,
    _git_path_introduction_commit,
    _git_tree_entries,
)
from phase_coverage_repo_files import (  # noqa: E402
    MAX_REPO_FILE_BYTES,
    WINDOWS_ABSOLUTE_PATH_RE,
    _is_normalized_repo_path,
    _read_repo_bytes,
    _repo_file,
    _repository_root,
)

SUPPORTED_MARKER_PLAN_VERSIONS = frozenset({"pr-marker-plan.v1", "pr-marker-plan.v2"})
MARKER_PLAN_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "contracts" / "pr-marker-plan.schema.json"
CHANGED_FILE_MANIFEST_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "contracts" / "changed-file-manifest.schema.json"
)
VERIFICATION_REPORT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "contracts" / "verification-report.schema.json"
)
MARKER_CHECKPOINT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "contracts" / "marker-checkpoint.schema.json"
)
MARKER_PLAN_STATUSES = frozenset({
    "planned", "checkpointing", "emission_ready", "emitting", "emitted",
    "collapsed", "stale", "invalid",
})
COMPLETE_CHECKPOINT_STRING_FIELDS = (
    "evidence_path",
    "checkpoint_evidence_sha",
    "checkpoint_evidence_commit_sha",
    "verification_evidence_path",
    "verification_evidence_sha",
    "commit_sha",
    "head_sha",
    "completed_at",
    "summary",
)
COMPLETE_CHECKPOINT_LIST_FIELDS = (
    "completed_task_ids", "required_verification_gate_ids", "validation",
)
COMPLETE_CHECKPOINT_OBJECT_FIELDS = ("freshness",)
PHASE_VERIFICATION_GATE_ALIASES = {
    "independent_critical_high_review": "independent_review",
}
PHASE_DIRECT_EVIDENCE_BINDINGS = {
    "baseline_commit": ("implementation_baseline_sha", "clean_collection_baseline_sha"),
    "candidate_freeze_id": ("candidate_freeze_id",),
    "capability_fixture_digest": ("capability_fixture_digest",),
    "checkpoint": ("implementation_checkpoint_sha",),
    "implementation_commit": ("implementation_checkpoint_sha",),
    "replay_digest": ("replay_digest",),
    "superseded_checkpoint": ("superseded_checkpoint_sha",),
    "telemetry_profile_id": ("telemetry_profile_id",),
    "treatment_fixture_digest": ("treatment_fixture_digest",),
    "treatment_contract_digest": ("treatment_contract_digest",),
}
PHASE_RESULT_PROJECTION_FIELDS = frozenset({
    "completed_at",
    "completed_task_ids",
    "evidence_finalization_scope",
    "implementation_completed_at",
    "independent_review_chat_id",
    "independent_review_findings",
    "marker_id",
    "pending_task_ids",
    "reviewability",
    "runtime_capability_snapshot_id",
    "status",
    "surface_matrix_id",
    "tasks_completed",
    "tasks_total",
    "updated_at",
})
INDEPENDENT_REVIEW_GATE_IDS = frozenset({
    "independent_critical_high_review",
    "independent_p0_p1_review",
})
WORKFLOW_CHECKPOINT_CLAIM_RE = re.compile(
    r"(?m)^-\s+(?:Implementation checkpoint|Current remediation source head)\s+\[([a-z0-9][a-z0-9_-]*)\]:\s+`([0-9a-f]{40})`\s*$"
)
WORKFLOW_SUPERSEDED_CHECKPOINT_CLAIM_RE = re.compile(
    r"(?m)^-\s+Superseded marker checkpoint\s+\[([a-z0-9][a-z0-9_-]*)\]:\s+`([0-9a-f]{40})`\s*$"
)
WORKFLOW_UNSCOPED_CHECKPOINT_CLAIM_RE = re.compile(
    r"(?m)^-\s+(?:Implementation checkpoint|Current remediation source head|Superseded marker checkpoint):\s+`[0-9a-f]{40}`\s*$"
)
WORKFLOW_PLAN_STATUS_RE = re.compile(
    r"(?m)^-\s+Plan status:\s+`([a-z][a-z0-9_-]*)`\s*$"
)
WORKFLOW_OVERVIEW_HEADING = "## Workflow Overview"
WORKFLOW_CRITERIA_HEADING_PREFIX = "### Phase Gates"
WORKFLOW_PHASE_GATE_IDS = {
    "Specify": "1",
    "Clarify": "2",
    "Plan": "3",
    "Checklist": "4",
    "Tasks": "5",
    "Analyze": "6",
    "Confidence Gate": "6.5",
    "Implement": "7",
}
# Rows the main phase loop never drives. A recorded gate PASS still forces them
# terminal, but leaving one open must not make every row below it read as out of
# order -- G6.5 is advisory by default, so Pending is its normal resting state.
WORKFLOW_ADVISORY_PHASES = frozenset({"Confidence Gate"})
WORKFLOW_TERMINAL_STATUSES = frozenset({
    "Complete",
    "✅ Complete",
    "Skipped",
    "✅ Skipped",
    # U+23ED with and without the U+FE0F variation selector; both render alike.
    "⏭ Skipped",
    "⏭️ Skipped",
})
WORKFLOW_OPEN_STATUSES = frozenset({
    "Pending",
    "⏳ Pending",
    "In Progress",
    "\U0001f504 In Progress",
    "Blocked",
    # U+26A0 with and without the U+FE0F variation selector; both render alike.
    "⚠ Blocked",
    "⚠️ Blocked",
})
WORKFLOW_STATUS_VALUES = WORKFLOW_TERMINAL_STATUSES | WORKFLOW_OPEN_STATUSES
# Markdown list, task-list, blockquote, and heading prefixes are stripped before
# matching so a gate recorded as `- G3 gate: PASS` is evidence like any other.
GATE_LINE_PREFIX_RE = re.compile(
    r"^[ \t]*(?:(?:[-*+]|[0-9]+\.)[ \t]+(?:\[[ xX]\][ \t]+)?|>[ \t]*|#{1,6}[ \t]+)+"
)
_GATE_ID = r"G(?P<gate>[0-9](?:\.5)?)"
_GATE_EMPHASIS = r"[ \t*_`]*"
_GATE_LABEL = r"(?:Gate|GATE|gate|Result|Status|Validation|Confidence[ \t]+[Gg]ate)"
_GATE_VERDICT = (
    r"(?:PASS(?:ED)?|Pass(?:ed)?|pass(?:ed)?)"
    r"(?![A-Za-z])"
    r"(?![ \t]+(?i:only|when|if|once|unless|after|requires|criteria)\b)"
)
# The check mark is allowed on either side of the gate id: `✅ G4 PASS` and
# `G4: ✅ PASS` are both recorded verdicts in the live corpus.
_GATE_TICK = r"(?:[✅✓][ \t]*)?"
GATE_RECORD_INLINE_RE = re.compile(
    r"(?:^|\||\*\*)" + _GATE_EMPHASIS + _GATE_TICK + _GATE_EMPHASIS
    + r"(?:Gate[ \t]+)?" + _GATE_ID + _GATE_EMPHASIS
    + r"(?:" + _GATE_LABEL + _GATE_EMPHASIS + r")?[:—–-]?" + _GATE_EMPHASIS
    + _GATE_TICK + _GATE_EMPHASIS + _GATE_VERDICT
)
GATE_RECORD_CELL_RE = re.compile(
    r"\|" + _GATE_EMPHASIS + _GATE_TICK + _GATE_EMPHASIS
    + r"(?:Gate[ \t]+)?" + _GATE_ID + _GATE_EMPHASIS
    + r"(?:" + _GATE_LABEL + r")?" + _GATE_EMPHASIS
    + r"\|[ \t]*" + _GATE_TICK + r"\*{0,2}" + _GATE_VERDICT
)
GATE_RECORD_JSON_RE = re.compile(
    r'"gate"[ \t]*:[ \t]*"' + _GATE_ID + r'"[^{}]*?"pass"[ \t]*:[ \t]*true'
)
GATE_RECORD_PATTERNS = (GATE_RECORD_INLINE_RE, GATE_RECORD_CELL_RE, GATE_RECORD_JSON_RE)
HTML_COMMENT_RE = re.compile(r"(?s)<!--.*?-->")
# Named rule groups for ``--rule``. A caller that only wants the bookkeeping
# rule enforced can gate on it without newly enforcing the structural coverage
# checks, which most of the existing workflow corpus predates.
RULE_PROBLEM_KEYS = {
    # A problem key absent from this map computes its result and reports it in
    # the emitted JSON, but cannot affect the exit code under the scoped
    # invocation the autopilot actually issues -- so it is inert as a gate.
    "status-evidence": (
        "workflow_status_evidence_errors",
        "state_status_errors",
        "autonomy_boundary_errors",
        "stage_mirror_errors",
        "workflow_authority_errors",
        "state_privacy_errors",
        "marker_evidence_privacy_errors",
        "formal_checkpoint_errors",
        "artifact_review_errors",
        "in_progress_errors",
        "duplicate_state_steps",
        "state_order_errors",
    ),
    "coverage": (
        "missing_workflow_sections",
        "missing_workflow_tokens",
        "missing_workflow_post_items",
        "missing_state_prefixes",
        "missing_state_post_items",
    ),
}
# Why every problem key is or is not armed, recorded per key rather than left to
# be inferred from ``RULE_PROBLEM_KEYS`` above. Verdicts are drawn from a closed
# three-value vocabulary. Two values would not do: an audit of this map's own
# subject found keys that are advisory by accident rather than by design, which
# is how an inert check survived unnoticed.
#
#   gated                -- reachable by a named rule, so it can move the exit code
#   advisory-deliberate  -- reported only, and that is the correct verdict for it
#   advisory-accidental  -- reported only, and that is a defect with a named follow-up
#
# A reason restating the key name records nothing. An ``advisory-deliberate``
# reason says what makes advisory status correct for that key; an
# ``advisory-accidental`` reason names the follow-up that will arm it.
#
# ``tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py`` derives the
# emitted key set from a real report and fails when a key is missing here, so a
# key cannot be added to the report without a verdict.
PROBLEM_KEY_INTENT: dict[str, dict[str, str]] = {
    "artifact_review_errors": {
        "verdict": "gated",
        "reason": (
            "A review handoff may claim verified delivery only with consistent "
            "rendered-page evidence. Pending, unavailable, and denied previews "
            "remain legal dispositions and never invalidate draft publication."
        ),
    },
    "formal_checkpoint_errors": {
        "verdict": "gated",
        "reason": (
            "Explicitly selected formal checks must have current content-bound "
            "evidence and an agreeing state mirror before phase advancement. "
            "Disabled workflows do not probe formal tools or add prerequisites."
        ),
    },
    # --- gated: armed by ``--rule status-evidence``, the invocation the
    # autopilot issues at every phase transition. ---
    "workflow_status_evidence_errors": {
        "verdict": "gated",
        "reason": (
            "The bookkeeping rule itself. An overview row may not claim a terminal "
            "status unless a gate verdict is recorded elsewhere in the same file, "
            "which is what keeps the status table honest across compactions and "
            "manual phase runs."
        ),
    },
    "state_status_errors": {
        "verdict": "gated",
        "reason": (
            "The state's top-level status is a closed enum with a contract schema. "
            "A retired spelling misreports the run's disposition to every consumer "
            "that reads the state file instead of the workflow."
        ),
    },
    "stage_mirror_errors": {
        "verdict": "gated",
        "reason": (
            "The workflow file is the durable authority and the state carries a "
            "mirror of it for the active run. Absence on either side is legal, so "
            "only a genuine two-sided disagreement reports, and that means the "
            "operator-facing document and the machine-readable record describe "
            "different runs."
        ),
    },
    "workflow_authority_errors": {
        "verdict": "gated",
        "reason": (
            "A state naming a workflow other than the one supplied means the run is "
            "proceeding against a different specification. This is the one key "
            "workflow-authority check, and the failure it exists to stop."
        ),
    },
    "state_privacy_errors": {
        "verdict": "gated",
        "reason": (
            "The state file is committed, so it may hold decision fields and "
            "digests only. A raw runner envelope, its argv, an absolute home path, "
            "or an external task or session UUID would publish machine-local "
            "identity with the next checkpoint commit."
        ),
    },
    "marker_evidence_privacy_errors": {
        "verdict": "gated",
        "reason": (
            "Marker checkpoint and verification evidence is committed with its "
            "checkpoint, so an external task, session, thread, or event id cited "
            "there must be a sha256 digest. A raw id or an absolute home path would "
            "publish machine-local identity and fail the repository privacy scan."
        ),
    },
    # --- gated: armed by ``--rule coverage``. Kept out of the status-evidence
    # tuple because most of the tracked workflow corpus predates these structural
    # requirements and a blocking guard would make those specifications
    # unresumable. Dropping ``--rule`` gates on them once a spec is migrated. ---
    "missing_workflow_sections": {
        "verdict": "gated",
        "reason": (
            "The workflow must carry a section for every phase the main loop drives, "
            "so a phase cannot be executed against a file with nowhere to record it. "
            "Scoped to the coverage rule because the pre-existing corpus predates the "
            "section list."
        ),
    },
    "missing_workflow_tokens": {
        "verdict": "gated",
        "reason": (
            "The workflow must carry the row and gate tokens the loop writes its "
            "verdicts into, or those verdicts land nowhere. Scoped to the coverage "
            "rule because the pre-existing corpus predates the token list."
        ),
    },
    "missing_workflow_post_items": {
        "verdict": "gated",
        "reason": (
            "The workflow must list every post-implementation step, or a step can be "
            "skipped without leaving a gap anyone can see. Scoped to the coverage rule "
            "because the pre-existing corpus predates the post-step list."
        ),
    },
    "missing_state_prefixes": {
        "verdict": "gated",
        "reason": (
            "The state plan must carry a step for every phase, or the run has no slot "
            "to record that phase's progress into. Scoped to the coverage rule because "
            "the pre-existing corpus predates the phase list."
        ),
    },
    "missing_state_post_items": {
        "verdict": "gated",
        "reason": (
            "The state plan must carry every post-implementation step for the same "
            "reason the workflow must list them: an absent slot cannot record a skip. "
            "Scoped to the coverage rule because the pre-existing corpus predates the "
            "post-step list."
        ),
    },
    "in_progress_errors": {
        "verdict": "gated",
        "reason": (
            "A current run can have only one in-progress state step. Multiple active "
            "steps make the machine-readable phase cursor ambiguous."
        ),
    },
    "duplicate_state_steps": {
        "verdict": "gated",
        "reason": (
            "A current-run state plan must name each step once. Duplicate steps create "
            "competing progress slots for the same phase or post item."
        ),
    },
    "state_order_errors": {
        "verdict": "gated",
        "reason": (
            "A current-run state plan must preserve phase order. Out-of-order steps "
            "can make the durable state advance or rewind relative to the workflow."
        ),
    },
    # --- advisory-deliberate: reported only, and correctly so. ---
    "workflow_checkpoint_errors": {
        "verdict": "advisory-deliberate",
        "reason": (
            "It carries the frozen pull-request-head byte comparison, which is only "
            "meaningful once a pr_marker_plan exists. Arming the key would arm every "
            "error folded into it at once, which is why the workflow-identity "
            "comparison was given its own key instead of being merged in here."
        ),
    },
    "changed_file_manifest_errors": {
        "verdict": "advisory-deliberate",
        "reason": (
            "The manifest is compared against external pull-request base and head "
            "authority passed in through --expected-base-commit and "
            "--expected-head-commit. The per-phase invocation supplies neither, so the "
            "comparison falls back to the local HEAD, which is exactly the self-sourced "
            "authority the marker-plan contract forbids. Reporting a self-sourced "
            "comparison is defensible; stopping a run on one is not."
        ),
    },
    "checkpoint_evidence_errors": {
        "verdict": "advisory-deliberate",
        "reason": (
            "It validates checkpoint evidence against the schema as committed at the "
            "authorized pull-request head. The per-phase invocation names no head, so "
            "the authority the check is written against is absent."
        ),
    },
    "checkpoint_file_errors": {
        "verdict": "advisory-deliberate",
        "reason": (
            "It reports where checkpoint evidence in the worktree differs from the same "
            "file at the authorized pull-request head. A worktree that has legitimately "
            "moved ahead of the last pushed head differs by construction, so the "
            "difference is a fact to surface rather than a stop."
        ),
    },
    "checkpoint_source_fingerprint_errors": {
        "verdict": "advisory-deliberate",
        "reason": (
            "Several of its checks compare a checkpoint's recorded tasks.md "
            "fingerprints against that file as it stands now, so the key goes non-empty "
            "whenever tasks.md changes after a checkpoint was written, which is what "
            "ordinary implementation does. It is a staleness signal to read, not a "
            "condition to halt on."
        ),
    },
    "emission_mapping_errors": {
        "verdict": "advisory-deliberate",
        "reason": (
            "Each marker's emission_mapping is validated against the stage that marker "
            "has reached, and several fields are valid only after emission. A plan read "
            "part-way through emission therefore carries mappings that do not yet "
            "satisfy the finished shape, by design."
        ),
    },
    "marker_plan_status_errors": {
        "verdict": "advisory-deliberate",
        "reason": (
            "It enforces the pr_marker_plan status contract, which models in-flight "
            "states explicitly: the emitting status requires both emitted and "
            "unfinished marker mappings to be present at once. The per-phase state "
            "carries no marker plan at all, and the multi-PR emission flow that owns "
            "one moves it through those in-flight values."
        ),
    },
    "projection_status_errors": {
        "verdict": "advisory-deliberate",
        "reason": (
            "It cross-checks the optional phase_results projection against the plan "
            "array. Nothing in the shipped skill writes phase_results and the tracked "
            "live state does not carry it, so the slot belongs to pull-request assembly "
            "rather than to the per-phase loop this invocation gates. stage_mirror_errors "
            "carries the gated half of the same idea, for the mirror the per-phase run "
            "does write."
        ),
    },
    "completed_phase_pending_fields": {
        "verdict": "advisory-deliberate",
        "reason": (
            "It flags a phase_results entry marked completed whose payload still "
            "contains the word pending, matched as a case-folded substring anywhere in "
            "free-form evidence prose. That is a drafting smell worth surfacing and a "
            "poor stop condition, because evidence legitimately mentioning a pending "
            "item trips it."
        ),
    },
}
PROBLEM_KEY_INTENT["autonomy_boundary_errors"] = {
    "verdict": "gated",
    "reason": (
        "An active run that can reach Phase 7 needs a current, versioned planning "
        "and execution-boundary record. Exact action scope preserves valid explicit "
        "authorization while any changed or revoked scope fails before dispatch."
    ),
}
STATE_STATUS_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "contracts" / "autopilot-state-status.schema.json"
)
AUTONOMY_BOUNDARY_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "contracts" / "autonomy-boundary.schema.json"
)

WORKFLOW_FINGERPRINT_FIELDS = (
    ("Feature spec", "feature_spec_sha"),
    ("Plan-declared scope", "plan_declared_scope_sha"),
    ("Tasks", "tasks_sha"),
    ("Reviewability evidence", "reviewability_sha"),
    ("Hazard route", "hazard_route_sha"),
    ("Changed-file manifest", "changed_file_manifest_sha"),
)


@dataclass(frozen=True)
class PlanStep:
    step: str
    status: str | None


@dataclass(frozen=True)
class ReportAuthority:
    expected_base_commit: str | None = None
    expected_head_commit: str | None = None
    current_execution_boundary: dict[str, Any] | None = None
    require_autonomy_boundary: bool = False


class ValidationError(Exception):
    def __init__(self, message: str, code: str = "input_error") -> None:
        super().__init__(message)
        self.code = code


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValidationError(f"could not read file: {path}: {exc}") from exc


def _strict_json_loads(value: str | bytes) -> Any:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = item
        return result

    def reject_non_finite_constant(constant: str) -> None:
        raise ValueError(f"non-finite JSON number is not allowed: {constant}")

    parsed = json.loads(
        value,
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_non_finite_constant,
    )
    pending: list[tuple[Any, int]] = [(parsed, 0)]
    while pending:
        item, depth = pending.pop()
        if not isinstance(item, (dict, list)):
            continue
        nested_depth = depth + 1
        if nested_depth > 256:
            raise ValueError("JSON nesting exceeds maximum depth of 256")
        children = item.values() if isinstance(item, dict) else item
        pending.extend((child, nested_depth) for child in children)
    return parsed


def load_state(path: Path) -> dict[str, Any]:
    try:
        state = _strict_json_loads(read_text(path))
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ValidationError(f"invalid state JSON: {path}: {exc}") from exc
    if not isinstance(state, dict):
        raise ValidationError("autopilot state must be a JSON object")
    return state


def extract_plan_steps(state: dict[str, Any]) -> list[PlanStep]:
    raw_plan = state.get("plan")
    if not isinstance(raw_plan, list):
        raise ValidationError("autopilot state must contain a plan array")
    steps: list[PlanStep] = []
    for index, item in enumerate(raw_plan):
        if not isinstance(item, dict):
            raise ValidationError(f"plan item {index} must be an object")
        step = item.get("step")
        if not isinstance(step, str) or not step.strip():
            raise ValidationError(f"plan item {index} must contain a non-empty step")
        status = item.get("status")
        if status is not None and not isinstance(status, str):
            raise ValidationError(f"plan item {index} status must be a string when present")
        steps.append(PlanStep(step=step, status=status))
    return steps


def first_index_with_prefix(steps: list[str], prefix: str) -> int | None:
    for index, step in enumerate(steps):
        if step.startswith(prefix):
            return index
    return None


def first_index_exact(steps: list[str], value: str) -> int | None:
    for index, step in enumerate(steps):
        if step == value:
            return index
    return None


def validate_workflow(text: str) -> dict[str, list[str]]:
    visible_text = _visible_markdown(text)
    visible_lines = [line.strip() for line in visible_text.splitlines()]
    table_rows = [
        line for line in visible_lines if line.startswith("|") and line.endswith("|")
    ]
    table_cells = {
        cell.strip()
        for row in table_rows
        for cell in row[1:-1].split("|")
    }
    missing_sections = [
        section
        for section in WORKFLOW_SECTIONS
        if not any(
            line.startswith(section) if section.endswith(":") else line == section
            for line in visible_lines
        )
    ]
    missing_tokens = [
        token for token in WORKFLOW_TOKENS
        if not any(row.startswith(token) for row in table_rows)
    ]
    missing_post_items = [post for post in POST_STEPS if post not in table_cells]
    return {
        "missing_workflow_sections": missing_sections,
        "missing_workflow_tokens": missing_tokens,
        "missing_workflow_post_items": missing_post_items,
    }


_RAW_HTML_BLOCK_STARTS: tuple[tuple[re.Pattern[str], re.Pattern[str] | None], ...] = (
    (re.compile(r"^[ \t]{0,3}<(script|pre|style|textarea)(?:[ \t>]|$)", re.IGNORECASE), None),
    (re.compile(r"^[ \t]{0,3}<\?"), re.compile(r"\?>")),
    (re.compile(r"^[ \t]{0,3}<![A-Z]"), re.compile(r">")),
    (re.compile(r"^[ \t]{0,3}<!\[CDATA\["), re.compile(r"\]\]>")),
    (
        re.compile(
            r"^[ \t]{0,3}</?(?:address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|nav|noframes|ol|optgroup|option|p|param|search|section|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul)(?:[ \t/>]|$)",
            re.IGNORECASE,
        ),
        re.compile(r"^$"),
    ),
    (
        re.compile(
            r"^[ \t]{0,3}(?:</[A-Za-z][A-Za-z0-9-]*[ \t]*>|<[A-Za-z][A-Za-z0-9-]*(?:[ \t]+[^<>]*)?[ \t]*/?>)[ \t]*$"
        ),
        re.compile(r"^$"),
    ),
)


def _raw_html_block_end(line: str) -> re.Pattern[str] | None | bool:
    for start, end in _RAW_HTML_BLOCK_STARTS:
        match = start.search(line)
        if match is None:
            continue
        if match.lastindex and match.group(1):
            return re.compile(rf"</{re.escape(match.group(1))}[ \t]*>", re.IGNORECASE)
        return end
    return False


def _visible_markdown(text: str) -> str:
    """Return Markdown outside comments, code blocks, and raw HTML blocks."""
    visible_lines: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    in_html_comment = False
    raw_html_end: re.Pattern[str] | None | bool = False
    for raw_line in text.splitlines():
        if raw_html_end is not False:
            if raw_html_end is None or raw_html_end.search(raw_line):
                raw_html_end = False
            continue
        if fence_character is not None:
            closing_fence = re.match(r"^[ \t]{0,3}(`{3,}|~{3,})[ \t]*$", raw_line)
            if (
                closing_fence
                and closing_fence.group(1)[0] == fence_character
                and len(closing_fence.group(1)) >= fence_length
            ):
                fence_character = None
                fence_length = 0
            continue

        line_parts: list[str] = []
        offset = 0
        while offset < len(raw_line):
            if in_html_comment:
                comment_end = raw_line.find("-->", offset)
                if comment_end < 0:
                    offset = len(raw_line)
                    break
                in_html_comment = False
                offset = comment_end + 3
                continue
            comment_start = raw_line.find("<!--", offset)
            if comment_start < 0:
                line_parts.append(raw_line[offset:])
                break
            line_parts.append(raw_line[offset:comment_start])
            in_html_comment = True
            offset = comment_start + 4
        line = "".join(line_parts)
        if re.match(r"^(?: {4}| {0,3}\t)", line):
            continue
        raw_html_end = _raw_html_block_end(line)
        if raw_html_end is not False:
            if raw_html_end is not None and raw_html_end.search(line):
                raw_html_end = False
            continue
        if fence_character is None:
            opening_fence = re.match(r"^[ \t]{0,3}(`{3,}|~{3,})", line)
            if opening_fence:
                fence_character = opening_fence.group(1)[0]
                fence_length = len(opening_fence.group(1))
                continue
            visible_lines.append(line)
    return "\n".join(visible_lines)


def _marker_phase_claims(phase_results: object, marker_id: str) -> list[tuple[str, str]]:
    """Phase-result fields for one marker that claim work beyond the plan projection."""
    phases = phase_results if isinstance(phase_results, dict) else {}
    return [
        (phase_name, phase_field)
        for phase_name, phase_result in phases.items()
        if isinstance(phase_name, str)
        and isinstance(phase_result, dict)
        and phase_result.get("marker_id") == marker_id
        for phase_field in phase_result
        if phase_field not in PHASE_RESULT_PROJECTION_FIELDS
    ]


def validate_workflow_checkpoint_bindings(
    text: str, state: dict[str, Any],
) -> dict[str, list[str]]:
    errors: list[str] = []
    marker_plan = state.get("pr_marker_plan")
    if not isinstance(marker_plan, dict):
        return {"workflow_checkpoint_errors": errors}
    markers = marker_plan.get("markers")
    if not isinstance(markers, list):
        return {"workflow_checkpoint_errors": errors}

    visible_text = _visible_markdown(text)
    expected: dict[str, str | None] = {}
    expected_superseded: dict[str, str] = {}
    # A marker awaits its first checkpoint while its checkpoint is pending, records
    # no commit, and no phase result claims work for it. Its workflow row reads
    # Pending and it has no current checkpoint claim yet.
    awaiting: set[str] = set()
    for marker in markers:
        if not isinstance(marker, dict) or not isinstance(marker.get("id"), str):
            continue
        checkpoint = marker.get("implementation_checkpoint")
        commit_sha = checkpoint.get("commit_sha") if isinstance(checkpoint, dict) else None
        expected[marker["id"]] = (
            commit_sha
            if isinstance(commit_sha, str) and re.fullmatch(r"[0-9a-f]{40}", commit_sha)
            else None
        )
        if (
            isinstance(checkpoint, dict)
            and checkpoint.get("status") == "pending"
            and expected[marker["id"]] is None
            and not _marker_phase_claims(state.get("phase_results"), marker["id"])
        ):
            awaiting.add(marker["id"])
        superseded_sha = (
            checkpoint.get("superseded_commit_sha")
            if isinstance(checkpoint, dict)
            else None
        )
        if isinstance(superseded_sha, str) and re.fullmatch(r"[0-9a-f]{40}", superseded_sha):
            expected_superseded[marker["id"]] = superseded_sha
    strict_contract = marker_plan.get("schema_version") == "pr-marker-plan.v2"
    if not strict_contract and not any(expected.values()):
        return {"workflow_checkpoint_errors": errors}

    checkpoint_claims = WORKFLOW_CHECKPOINT_CLAIM_RE.findall(visible_text)
    for marker_id, claimed_sha in checkpoint_claims:
        if expected.get(marker_id) != claimed_sha:
            errors.append(
                f"workflow checkpoint claim for marker {marker_id!r} does not match its pr_marker_plan commit_sha"
            )
    for marker_id, claimed_sha in WORKFLOW_SUPERSEDED_CHECKPOINT_CLAIM_RE.findall(visible_text):
        if expected_superseded.get(marker_id) != claimed_sha:
            errors.append(
                f"workflow superseded checkpoint claim for marker {marker_id!r} does not match its pr_marker_plan superseded_commit_sha"
            )
    if WORKFLOW_UNSCOPED_CHECKPOINT_CLAIM_RE.search(visible_text):
        errors.append("workflow checkpoint claims must name their marker")
    if strict_contract:
        for marker_id in expected:
            if marker_id in awaiting:
                continue
            claim_count = sum(
                claimed_marker_id == marker_id
                for claimed_marker_id, _claimed_sha in checkpoint_claims
            )
            if claim_count != 1:
                errors.append(
                    f"workflow must contain exactly one current checkpoint claim for marker {marker_id!r}"
                )

    section_token = "## PR Marker Plan Evidence"
    section_count = len(re.findall(r"(?m)^## PR Marker Plan Evidence\s*$", visible_text))
    if strict_contract and section_count != 1:
        errors.append("workflow must contain exactly one PR Marker Plan Evidence section")
    if section_count == 1:
        section = visible_text.split(section_token, 1)[1].split("\n## ", 1)[0]
        if strict_contract:
            expected_plan_status = marker_plan.get("status")
            plan_statuses = WORKFLOW_PLAN_STATUS_RE.findall(section)
            if plan_statuses != [expected_plan_status]:
                errors.append(
                    "workflow PR Marker Plan Evidence Plan status must exactly "
                    "match pr_marker_plan.status"
                )
        fingerprint_statuses = re.findall(
            r"(?m)^-\s+Fingerprint status:\s*([^\n]+?)\s*$", section,
        )
        if strict_contract and any(
            status.casefold() == "current" for status in fingerprint_statuses
        ):
            if fingerprint_statuses != ["Current"]:
                errors.append(
                    "workflow PR Marker Plan Evidence must contain exactly one exact "
                    "Fingerprint status: Current claim"
                )
            source_fingerprint = marker_plan.get("source_fingerprint")
            if not isinstance(source_fingerprint, dict):
                errors.append(
                    "workflow Current fingerprint claim requires "
                    "pr_marker_plan.source_fingerprint"
                )
            else:
                fingerprint_rows: dict[str, list[str]] = {
                    label: [] for label, _field in WORKFLOW_FINGERPRINT_FIELDS
                }
                for line in section.splitlines():
                    if not line.startswith("|") or not line.endswith("|"):
                        continue
                    cells = [cell.strip() for cell in line[1:-1].split("|")]
                    if len(cells) != 2 or cells[0] not in fingerprint_rows:
                        continue
                    fingerprint_rows[cells[0]].append(cells[1].strip("` "))
                for label, field in WORKFLOW_FINGERPRINT_FIELDS:
                    expected_value = source_fingerprint.get(field)
                    if fingerprint_rows[label] != [expected_value]:
                        errors.append(
                            f"workflow Current fingerprint {label!r} does not exactly "
                            f"match pr_marker_plan.source_fingerprint.{field}"
                        )
        marker_row_counts = {marker_id: 0 for marker_id in expected}
        for line in section.splitlines():
            if not line.startswith("|") or not line.endswith("|"):
                continue
            cells = [cell.strip() for cell in line[1:-1].split("|")]
            if len(cells) < 5:
                continue
            marker_id = cells[1].strip("` ")
            if marker_id not in expected:
                continue
            marker_row_counts[marker_id] += 1
            if marker_id in awaiting:
                if cells[4] != "Pending":
                    errors.append(
                        f"workflow PR Marker Plan Evidence marker {marker_id!r} checkpoint must read "
                        "Pending until its pr_marker_plan checkpoint records commit_sha"
                    )
                continue
            checkpoint_shas = set(re.findall(r"\b[0-9a-f]{40}\b", cells[4]))
            expected_sha = expected[marker_id]
            if expected_sha is None or expected_sha not in checkpoint_shas:
                expected_binding = (
                    expected_sha
                    if expected_sha is not None
                    else "its pr_marker_plan commit_sha"
                )
                errors.append(
                    f"workflow PR Marker Plan Evidence marker {marker_id!r} checkpoint does not bind {expected_binding}"
                )
        for marker_id, row_count in marker_row_counts.items():
            if row_count != 1:
                errors.append(
                    f"workflow PR Marker Plan Evidence must contain exactly one row for marker {marker_id!r}"
                )
    return {"workflow_checkpoint_errors": errors}


def validate_state(steps: list[PlanStep]) -> dict[str, list[str]]:
    names = [step.step for step in steps]
    missing_prefixes = [prefix for prefix in STATE_PREFIXES if first_index_with_prefix(names, prefix) is None]
    missing_posts = [post for post in POST_STEPS if first_index_exact(names, post) is None]

    duplicate_steps: list[str] = []
    seen: set[str] = set()
    for name in names:
        if name in seen and name not in duplicate_steps:
            duplicate_steps.append(name)
        seen.add(name)

    order_errors: list[str] = []
    last_index = -1
    for checkpoint in ORDERED_STATE_CHECKPOINTS:
        if checkpoint.startswith("Post:"):
            index = first_index_exact(names, checkpoint)
        else:
            index = first_index_with_prefix(names, checkpoint)
        if index is None:
            continue
        if index < last_index:
            order_errors.append(checkpoint)
        last_index = max(last_index, index)

    in_progress = [step.step for step in steps if step.status == "in_progress"]
    in_progress_errors: list[str] = []
    if len(in_progress) > 1:
        in_progress_errors = in_progress

    return {
        "missing_state_prefixes": missing_prefixes,
        "missing_state_post_items": missing_posts,
        "duplicate_state_steps": duplicate_steps,
        "state_order_errors": order_errors,
        "in_progress_errors": in_progress_errors,
    }


def _pending_value_paths(value: Any, path: str) -> list[str]:
    if isinstance(value, str):
        return [path] if "pending" in value.casefold() else []
    if isinstance(value, list):
        paths: list[str] = []
        for index, item in enumerate(value):
            paths.extend(_pending_value_paths(item, f"{path}[{index}]"))
        return paths
    if isinstance(value, dict):
        paths = []
        for key, item in value.items():
            paths.extend(_pending_value_paths(item, f"{path}.{key}"))
        return paths
    return []


def _sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _string_list(value: object) -> list[str] | None:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        return None
    return value


def _is_utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not UTC_TIMESTAMP_RE.fullmatch(value):
        return False
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ") == value


def _timestamp_errors(value: object, prefix: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else key
            if key.endswith("_at") and item is not None and not _is_utc_timestamp(item):
                errors.append(f"{child} must be an RFC 3339 UTC timestamp")
            errors.extend(_timestamp_errors(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_timestamp_errors(item, f"{prefix}[{index}]"))
    return errors


def _marker_plan_version_errors(marker_plan: object) -> list[str]:
    if marker_plan is None:
        return []
    if not isinstance(marker_plan, dict):
        return ["pr_marker_plan must be an object"]
    version = marker_plan.get("schema_version")
    if version not in SUPPORTED_MARKER_PLAN_VERSIONS:
        return ["pr_marker_plan.schema_version must be pr-marker-plan.v1 or pr-marker-plan.v2"]
    return []


def _json_schema_errors(
    value: object,
    schema: object,
    root: dict[str, Any],
    path: str,
) -> list[str]:
    """Validate with the runner's shared validator; one line per failure."""
    return [
        f"{failure['field']}: {failure['message']}"
        for failure in json_schema_failures(value, schema, root, path)
    ]


def _marker_plan_shape_errors(
    marker_plan: object,
    schema: dict[str, Any] | None = None,
) -> list[str]:
    if not isinstance(marker_plan, dict) or marker_plan.get("schema_version") != "pr-marker-plan.v2":
        return []
    if schema is None:
        try:
            schema = _strict_json_loads(read_text(MARKER_PLAN_SCHEMA_PATH))
        except (json.JSONDecodeError, ValueError):
            return ["canonical pr-marker-plan schema is malformed"]
    if not isinstance(schema, dict):
        return ["canonical pr-marker-plan schema root must be an object"]
    return _json_schema_errors(marker_plan, schema, schema, "pr_marker_plan")


def _marker_tasks_sha_text(tasks_text: str, task_ids: set[str]) -> str | None:
    selected: list[str] = []
    found: set[str] = set()
    for line in tasks_text.splitlines():
        match = TASK_LINE_RE.match(line)
        if match and match.group(1) in task_ids:
            selected.append(line)
            found.add(match.group(1))
    if found != task_ids:
        return None
    return _sha256_bytes(("\n".join(selected) + "\n").encode("utf-8"))


def _canonical_schema(
    schema_path: Path,
    label: str,
    *,
    repo_root: Path | None = None,
    expected_head_commit: str | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Load a canonical schema from the authorized head when one is supplied."""
    errors: list[str] = []
    schema_bytes: bytes | None = None
    exact_head = (
        repo_root is not None
        and isinstance(expected_head_commit, str)
        and re.fullmatch(r"[0-9a-f]{40}", expected_head_commit) is not None
    )
    if exact_head:
        try:
            schema_ref: str | None = (
                schema_path.resolve().relative_to(repo_root.resolve()).as_posix()
            )
        except ValueError:
            schema_ref = None
        if schema_ref is not None:
            schema_bytes = _git_file_at_commit(repo_root, expected_head_commit, schema_ref)
            if schema_bytes is None:
                return None, [f"canonical {label} schema is absent from the authorized PR head"]
            try:
                worktree_schema_bytes = schema_path.read_bytes()
            except OSError:
                worktree_schema_bytes = None
            if worktree_schema_bytes != schema_bytes:
                errors.append(f"canonical {label} schema differs from the authorized PR head")
        else:
            # An installed plugin runs from outside the repository, so its
            # contracts are trusted from the plugin root itself.
            try:
                schema_path.resolve(strict=True).relative_to(INSTALLED_PLUGIN_ROOT)
            except (OSError, ValueError):
                return None, [f"canonical {label} schema is outside the installed plugin root"]
            try:
                schema_bytes = schema_path.read_bytes()
            except OSError:
                schema_bytes = None
    else:
        try:
            schema_bytes = schema_path.read_bytes()
        except OSError:
            schema_bytes = None
    try:
        schema = (
            _strict_json_loads(schema_bytes.decode("utf-8"))
            if schema_bytes is not None
            else None
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        schema = None
    if not isinstance(schema, dict):
        errors.append(f"canonical {label} schema is malformed")
        return None, errors
    return schema, errors


def _workflow_authority_errors(
    workflow: Path,
    state_path: Path,
    state: dict[str, Any],
) -> list[str]:
    """Check the supplied workflow against the authority the state names.

    Branch order is fixed, because an earlier skip must win over a later failure.
    No branch raises: ``build_report`` has no handler, and an uncaught exception
    would print a traceback instead of the JSON report the autopilot parses.
    """
    # 1. Key membership, never ``.get(...) is None``. A state that names no
    # workflow asserts no authority, but an explicitly nulled field is malformed,
    # and ``.get`` collapses those two verdicts into a silent opt-out.
    if "workflow_file" not in state:
        return []
    # 2. No repository root, no boundary to resolve the supplied workflow against.
    repo_root = _repository_root(state_path)
    if repo_root is None:
        return []
    state_workflow_ref = state["workflow_file"]
    # 3. The whitespace check is explicit, and precedes branch 4, because a run of
    # spaces is a valid POSIX path part: ``_is_normalized_repo_path("  ")`` returns
    # True, so such a value would otherwise fall through to branch 6 and be
    # reported as an identity mismatch against a blank path.
    if not isinstance(state_workflow_ref, str) or not state_workflow_ref.strip():
        return [
            "autopilot state workflow_file is not a normalized repository-relative path"
        ]
    # 4. Case is deliberately not folded here, which is what keeps this consistent
    # with the byte-exact rule below rather than normalizing a mis-cased value
    # into a match.
    if not _is_normalized_repo_path(state_workflow_ref):
        return [
            "autopilot state workflow_file is not a normalized repository-relative path"
        ]
    # 5. Resolution is asymmetric: only the supplied side is resolved, because only
    # it has spelling freedom. The state value is machine-written and branch 4 has
    # already constrained it. A non-subpath raises ValueError, which is this
    # branch by design rather than an escape.
    #
    # ``resolve`` itself raises OSError or RuntimeError on a path it cannot
    # traverse, which is what ``_repository_root`` guards for the same reason. An
    # unresolvable supplied path is the same absence of information branch 2
    # covers -- one side of the comparison cannot be established, which is not
    # evidence of a mismatch -- so it skips rather than escaping into
    # ``build_report``, which has no handler.
    try:
        workflow_ref = workflow.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return ["workflow file is outside the authorized repository"]
    except (OSError, RuntimeError):
        return []
    # The sibling gated path re-checks ``_is_normalized_repo_path`` on its own
    # derived reference here; this branch deliberately does not, and the omission
    # is safe rather than missing. ``workflow`` is already a readable regular file
    # by this point, because ``read_text`` runs before this helper is called and
    # raises otherwise, and resolving both sides before ``relative_to`` leaves no
    # ``.``, ``..``, or empty segment able to survive into ``workflow_ref``. Stated
    # so the asymmetry with the gated path is not later "repaired" as a gap.
    # 6. Byte-exact, with no case folding and no ``samefile``: the only rule that
    # returns the same verdict on a case-insensitive filesystem and a
    # case-sensitive one, so the outcome does not depend on where it runs.
    if state_workflow_ref != workflow_ref:
        return [
            "supplied workflow does not match autopilot state workflow_file authority: "
            f"supplied {workflow_ref}, state names {state_workflow_ref}"
        ]
    # 7. The two references agree.
    return []


def _authorized_workflow_text(
    workflow: Path,
    state_path: Path,
    state: dict[str, Any],
    expected_head_commit: str | None,
) -> tuple[str, list[str], list[str]]:
    worktree_text = read_text(workflow)
    # Unconditional, and deliberately after the read above: a supplied workflow
    # that cannot be read has already raised, so nothing below can be reached with
    # an untraversable path. Everything from here down is the gated
    # pull-request-head comparison, whose preconditions and reporting key are
    # unchanged -- which is why these findings travel in their own slot rather
    # than folding into the gated one.
    authority_errors = _workflow_authority_errors(workflow, state_path, state)
    marker_plan = state.get("pr_marker_plan")
    if not (
        isinstance(marker_plan, dict)
        and marker_plan.get("schema_version") == "pr-marker-plan.v2"
    ):
        return worktree_text, [], authority_errors
    if expected_head_commit is None:
        return worktree_text, [], authority_errors
    repo_root = _repository_root(state_path)
    if repo_root is None:
        return worktree_text, ["workflow repository root is unavailable"], authority_errors
    if not isinstance(expected_head_commit, str) or not re.fullmatch(
        r"[0-9a-f]{40}", expected_head_commit
    ):
        return worktree_text, [
            "pr-marker-plan.v2 workflow validation requires external expected_head_commit authority"
        ], authority_errors
    try:
        workflow_ref = workflow.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return worktree_text, [
            "workflow file is outside the authorized repository"
        ], authority_errors
    if not _is_normalized_repo_path(workflow_ref):
        return worktree_text, [
            "workflow file reference is not repository-relative"
        ], authority_errors
    state_workflow_ref = state.get("workflow_file")
    if not _is_normalized_repo_path(state_workflow_ref):
        return worktree_text, [
            "autopilot state workflow_file is not a normalized repository-relative path"
        ], authority_errors
    if state_workflow_ref != workflow_ref:
        return worktree_text, [
            "supplied workflow does not match autopilot state workflow_file authority"
        ], authority_errors
    committed_bytes = _git_file_at_commit(repo_root, expected_head_commit, workflow_ref)
    if committed_bytes is None:
        return worktree_text, [
            "workflow is absent from the authorized PR head"
        ], authority_errors
    try:
        committed_text = committed_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return worktree_text, [
            "workflow at the authorized PR head is not UTF-8"
        ], authority_errors
    try:
        worktree_bytes = workflow.read_bytes()
    except OSError:
        worktree_bytes = None
    errors = []
    if worktree_bytes != committed_bytes:
        errors.append("workflow differs from the authorized PR head")
    return committed_text, errors, authority_errors


def _phase_evidence_owner(
    phase_field: str,
    evidence: dict[str, Any],
) -> tuple[str | None, Any]:
    candidates: list[tuple[str, Any, bool]] = []
    direct_fields = PHASE_DIRECT_EVIDENCE_BINDINGS.get(phase_field, ())
    for field in direct_fields:
        if field in evidence:
            candidates.append(
                (f"checkpoint_evidence.{field}", evidence[field], True)
            )
    if phase_field in evidence and phase_field not in direct_fields:
        candidates.append(
            (f"checkpoint_evidence.{phase_field}", evidence[phase_field], False)
        )

    evidence_gate_ids = [
        gate_id
        for gate_id, projected_field in PHASE_VERIFICATION_GATE_ALIASES.items()
        if projected_field == phase_field
    ]
    evidence_gate_ids.append(phase_field)
    for container_name in ("verification", "verification_details"):
        container = evidence.get(container_name)
        if not isinstance(container, dict):
            continue
        for gate_id in evidence_gate_ids:
            if gate_id not in container:
                continue
            value = container[gate_id]
            if isinstance(value, dict):
                value = value.get("evidence")
            candidates.append(
                (f"checkpoint_evidence.{container_name}.{gate_id}", value, True)
            )
    if len(candidates) != 1:
        return ("multiple" if candidates else None), None
    owner, value, permitted = candidates[0]
    return (owner, value) if permitted else (None, None)


def _load_json_bytes(value: bytes | None) -> dict[str, Any] | None:
    if value is None:
        return None
    try:
        parsed = _strict_json_loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _shared_checkpoint_content_errors(
    repo_root: Path,
    base_commit: str,
    authorized_tree: dict[str, str],
    verified_trees: dict[str, dict[str, str] | None],
    markers: list[Any],
    expected_owners: dict[str, set[str]],
    shared_paths: set[str],
) -> list[str]:
    base_tree = _git_tree_entries(repo_root, base_commit)
    if base_tree is None:
        return ["PR base tree is unavailable for shared marker content binding"]
    errors: list[str] = []
    for path in sorted(shared_paths):
        previous_commit = base_commit
        previous_blob = base_tree.get(path)
        if previous_blob is None:
            errors.append(f"shared marker path {path} is absent from the PR base")
            continue
        for marker_index, marker in enumerate(markers):
            if not isinstance(marker, dict):
                continue
            checkpoint = marker.get("implementation_checkpoint")
            if not isinstance(checkpoint, dict) or checkpoint.get("status") != "complete":
                continue
            current_commit = checkpoint.get("commit_sha")
            current_tree = (
                verified_trees.get(current_commit)
                if isinstance(current_commit, str)
                else None
            )
            if current_tree is None or not isinstance(current_commit, str):
                continue
            if not _git_commit_is_ancestor(repo_root, previous_commit, current_commit):
                errors.append(
                    f"shared marker path {path} checkpoint {marker_index} is out of commit order"
                )
                continue
            current_blob = current_tree.get(path)
            owns_path = marker.get("id") in expected_owners[path]
            if owns_path and current_blob is None:
                errors.append(
                    f"shared marker path {path} is missing at declared checkpoint {marker_index}"
                )
            elif owns_path and current_blob == previous_blob:
                errors.append(
                    f"shared marker path {path} is unchanged at declared checkpoint {marker_index}"
                )
            elif not owns_path and current_blob != previous_blob:
                errors.append(
                    f"shared marker path {path} changed at undeclared checkpoint {marker_index}"
                )
            previous_commit = current_commit
            previous_blob = current_blob
        if previous_blob != authorized_tree.get(path):
            errors.append(f"shared marker path {path} differs from the last complete checkpoint")
    return errors


def validate_changed_file_manifest(
    state: dict[str, Any],
    state_path: Path,
    *,
    expected_base_commit: str | None = None,
    expected_head_commit: str | None = None,
) -> dict[str, list[str]]:
    marker_plan = state.get("pr_marker_plan")
    repo_root = _repository_root(state_path)
    resolved_head = (
        subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--verify", "HEAD^{commit}"],
            text=True,
            capture_output=True,
            env=_git_env(),
            shell=False,
            check=False,
        )
        if repo_root
        else None
    )
    current_head = (
        resolved_head.stdout.strip()
        if resolved_head is not None and resolved_head.returncode == 0
        else None
    )
    authority_head = (
        expected_head_commit
        if isinstance(expected_head_commit, str)
        and re.fullmatch(r"[0-9a-f]{40}", expected_head_commit)
        else current_head
    )
    state_ref: str | None = None
    committed_state_bytes: bytes | None = None
    committed_state: dict[str, Any] | None = None
    if repo_root and isinstance(authority_head, str):
        try:
            state_ref = state_path.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            state_ref = None
        if state_ref and _is_normalized_repo_path(state_ref):
            committed_state_bytes = _git_file_at_commit(repo_root, authority_head, state_ref)
            committed_state = _load_json_bytes(committed_state_bytes)
    committed_marker_plan = (
        committed_state.get("pr_marker_plan") if isinstance(committed_state, dict) else None
    )
    strict_contract = any(
        isinstance(candidate, dict)
        and candidate.get("schema_version") == "pr-marker-plan.v2"
        for candidate in (marker_plan, committed_marker_plan)
    )
    authority_errors: list[str] = []
    if strict_contract:
        if committed_state_bytes is None or committed_state is None:
            authority_errors.append(
                "autopilot state is absent or invalid at the authorized PR head"
            )
        else:
            try:
                worktree_state_bytes = state_path.read_bytes()
            except OSError:
                worktree_state_bytes = None
            if worktree_state_bytes != committed_state_bytes:
                authority_errors.append(
                    "autopilot state differs from the authorized PR head"
                )
    manifest_ref = state.get("changed_file_manifest")
    if manifest_ref is None:
        if strict_contract:
            return {
                "changed_file_manifest_errors": [
                    "pr-marker-plan.v2 requires a changed_file_manifest reference",
                ],
            }
        return {"changed_file_manifest_errors": []}
    if not _is_normalized_repo_path(manifest_ref):
        return {"changed_file_manifest_errors": ["changed-file manifest reference is invalid"]}
    if repo_root is None:
        return {"changed_file_manifest_errors": ["repository root is unavailable"]}
    worktree_manifest_bytes = _read_repo_bytes(repo_root, manifest_ref)
    manifest = _load_json_bytes(worktree_manifest_bytes)
    if manifest is None:
        return {"changed_file_manifest_errors": ["changed-file manifest is missing or invalid"]}
    if strict_contract:
        committed_manifest_bytes = (
            _git_file_at_commit(repo_root, authority_head, manifest_ref)
            if isinstance(authority_head, str)
            else None
        )
        if committed_manifest_bytes is None:
            authority_errors.append(
                "changed-file manifest is absent from the authorized PR head"
            )
        elif worktree_manifest_bytes != committed_manifest_bytes:
            authority_errors.append(
                "changed-file manifest differs from the authorized PR head"
            )
    manifest_schema, manifest_schema_errors = _canonical_schema(
        CHANGED_FILE_MANIFEST_SCHEMA_PATH,
        "changed-file manifest",
        repo_root=repo_root if strict_contract else None,
        expected_head_commit=expected_head_commit if strict_contract else None,
    )
    authority_errors.extend(manifest_schema_errors)
    if manifest_schema is None:
        return {"changed_file_manifest_errors": authority_errors}
    schema_errors = _json_schema_errors(
        manifest,
        manifest_schema,
        manifest_schema,
        "changed_file_manifest",
    )
    expected_feature_id = state.get("spec_id")
    marker_feature_id = marker_plan.get("feature_id") if isinstance(marker_plan, dict) else None
    identity_errors: list[str] = []
    if not isinstance(expected_feature_id, str) or not expected_feature_id:
        identity_errors.append("autopilot state spec_id is invalid")
    if manifest.get("feature_id") != expected_feature_id:
        identity_errors.append("changed-file manifest feature_id does not match state authority")
    if manifest.get("feature_id") != marker_feature_id:
        identity_errors.append("changed-file manifest feature_id does not match marker-plan authority")
    if manifest.get("comparison_ref") != "HEAD":
        identity_errors.append("changed-file manifest comparison_ref must be HEAD")
    if schema_errors or identity_errors:
        return {
            "changed_file_manifest_errors": [
                *authority_errors,
                *(f"changed-file manifest schema: {error}" for error in schema_errors),
                *identity_errors,
            ],
        }
    base_commit = manifest.get("base_commit")
    entries = manifest.get("files")
    if not isinstance(base_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", base_commit):
        return {"changed_file_manifest_errors": ["changed-file manifest base_commit is invalid"]}
    if not isinstance(entries, list):
        return {"changed_file_manifest_errors": ["changed-file manifest files must be an array"]}
    base_errors: list[str] = []
    if strict_contract:
        if not isinstance(expected_base_commit, str) or not re.fullmatch(
            r"[0-9a-f]{40}", expected_base_commit
        ):
            base_errors.append(
                "pr-marker-plan.v2 changed-file manifest requires external expected_base_commit authority"
            )
        elif base_commit != expected_base_commit:
            base_errors.append(
                "changed-file manifest base_commit does not match external PR base authority"
            )
        if not isinstance(expected_head_commit, str) or not re.fullmatch(
            r"[0-9a-f]{40}", expected_head_commit
        ):
            base_errors.append(
                "pr-marker-plan.v2 changed-file manifest requires external expected_head_commit authority"
            )
        declared_base = state.get("changed_file_manifest_base_commit")
        if not isinstance(declared_base, str) or not re.fullmatch(r"[0-9a-f]{40}", declared_base):
            base_errors.append("pr-marker-plan.v2 requires changed_file_manifest_base_commit")
        elif declared_base != base_commit:
            base_errors.append("changed-file manifest base_commit does not match state authority")
    comparison_commit = expected_head_commit if strict_contract else "HEAD"
    if strict_contract and current_head != expected_head_commit:
        base_errors.append("repository HEAD does not match external PR head authority")
    if not _git_commit_exists(repo_root, base_commit):
        base_errors.append("changed-file manifest base_commit is not an existing commit")
    elif not isinstance(comparison_commit, str) or not _git_commit_exists(
        repo_root, comparison_commit
    ):
        base_errors.append("external PR head authority is not an existing commit")
    elif not _git_commit_is_ancestor(repo_root, base_commit, comparison_commit):
        base_errors.append("changed-file manifest base_commit is not an ancestor of the authorized head")
    if base_errors:
        return {"changed_file_manifest_errors": [*authority_errors, *base_errors]}

    declared: dict[str, tuple[str, str | None]] = {}
    expected_owners: dict[str, set[str]] = {}
    declared_owner_order: dict[str, list[str]] = {}
    expected_source_owners: dict[str, set[str]] = {}
    rename_sources: set[str] = set()
    structural_errors: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            structural_errors.append(f"files[{index}] must be an object")
            continue
        path = entry.get("path")
        operation = entry.get("operation")
        if not _is_normalized_repo_path(path) or path in declared:
            structural_errors.append(f"files[{index}].path is invalid, unsafe, or duplicated")
            continue
        if operation not in {"NEW", "MODIFIED", "DELETED", "RENAMED"}:
            structural_errors.append(f"files[{index}].operation is invalid")
            continue
        if entry.get("category") not in {
            "generated_artifact", "implementation", "plugin_source", "process", "research", "test",
        }:
            structural_errors.append(f"files[{index}].category is invalid")
        if entry.get("provenance") not in {"authored", "generated"}:
            structural_errors.append(f"files[{index}].provenance is invalid")
        marker_ids = entry.get("marker_ids")
        marker_values = _string_list(marker_ids)
        if marker_values is None or not marker_values:
            structural_errors.append(f"files[{index}].marker_ids must contain a marker owner")
        elif len(set(marker_values)) != len(marker_values):
            structural_errors.append(f"files[{index}].marker_ids must not repeat a marker owner")
        elif len(marker_values) > 1 and (
            operation != "MODIFIED" or entry.get("category") == "process"
        ):
            structural_errors.append(
                f"files[{index}].marker_ids shared ownership requires a MODIFIED non-process path"
            )
        source_path = entry.get("source_path")
        if operation == "RENAMED":
            if (
                not _is_normalized_repo_path(source_path)
                or source_path == path
                or source_path in rename_sources
            ):
                structural_errors.append(
                    f"files[{index}].source_path is invalid, unsafe, duplicated, or unchanged"
                )
            else:
                rename_sources.add(source_path)
                expected_source_owners[source_path] = set(marker_values or ())
        elif source_path is not None:
            structural_errors.append(f"files[{index}].source_path is only valid for RENAMED")
        declared[path] = (operation, source_path if isinstance(source_path, str) else None)
        expected_owners[path] = set(marker_values or ())
        declared_owner_order[path] = marker_values or []
    if rename_sources & set(declared):
        structural_errors.append("changed-file manifest rename source paths overlap destination paths")
    if structural_errors:
        return {
            "changed_file_manifest_errors": [*authority_errors, *structural_errors]
        }

    completed = subprocess.run(
        [
            "git", "-C", str(repo_root),
            "-c", "diff.renames=true",
            "-c", "diff.renameLimit=0",
            "diff", "--no-ext-diff", "--find-renames=50%",
            "--ignore-submodules=none", "--name-status",
            f"{base_commit}..{comparison_commit}",
        ],
        text=True,
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    if completed.returncode != 0:
        return {"changed_file_manifest_errors": ["git diff for changed-file manifest failed"]}
    observed: dict[str, tuple[str, str | None]] = {}
    status_map = {"A": "NEW", "M": "MODIFIED", "D": "DELETED"}
    for line in completed.stdout.splitlines():
        fields = line.split("\t")
        status = fields[0]
        if status.startswith("R") and len(fields) == 3:
            observed[fields[2]] = ("RENAMED", fields[1])
        elif status[:1] in status_map and len(fields) == 2:
            observed[fields[1]] = (status_map[status[:1]], None)
        else:
            return {"changed_file_manifest_errors": [f"unsupported git diff record: {line}"]}
    errors = list(authority_errors)
    if declared != observed:
        errors.append(
            f"declared changed-file manifest does not match {base_commit}..{comparison_commit}"
        )

    if worktree_manifest_bytes is None:
        return {"changed_file_manifest_errors": ["changed-file manifest is missing or invalid"]}
    expected_manifest_sha = _sha256_bytes(worktree_manifest_bytes)
    current_fingerprint = state.get("current_source_fingerprint")
    plan_fingerprint = marker_plan.get("source_fingerprint") if isinstance(marker_plan, dict) else None
    for label, fingerprint in (
        ("current_source_fingerprint", current_fingerprint),
        ("pr_marker_plan.source_fingerprint", plan_fingerprint),
    ):
        if not isinstance(fingerprint, dict) or fingerprint.get("changed_file_manifest_sha") != expected_manifest_sha:
            errors.append(f"{label}.changed_file_manifest_sha does not match the changed-file manifest")
    if isinstance(current_fingerprint, dict) and isinstance(plan_fingerprint, dict):
        if current_fingerprint != plan_fingerprint:
            errors.append("current and marker-plan source fingerprints do not match")

    markers = marker_plan.get("markers") if isinstance(marker_plan, dict) else None
    if not isinstance(markers, list):
        errors.append("changed-file manifest requires pr_marker_plan.markers")
        return {"changed_file_manifest_errors": errors}
    marker_operations: dict[str, tuple[str, str | None]] = {}
    actual_owners: dict[str, set[str]] = {}
    actual_source_owners: dict[str, set[str]] = {}
    declared_marker_ids = {
        marker.get("id") for marker in markers
        if isinstance(marker, dict) and isinstance(marker.get("id"), str)
    }
    marker_order = {
        marker.get("id"): index
        for index, marker in enumerate(markers)
        if isinstance(marker, dict) and isinstance(marker.get("id"), str)
    }
    for path, owners in expected_owners.items():
        if not owners <= declared_marker_ids:
            errors.append(f"changed-file manifest marker owner for {path} is not declared")
        owner_order = declared_owner_order[path]
        if (
            len(owner_order) > 1
            and all(owner in marker_order for owner in owner_order)
            and owner_order != sorted(owner_order, key=marker_order.__getitem__)
        ):
            errors.append(f"changed-file manifest marker owners for {path} are out of review order")
    for marker_index, marker in enumerate(markers):
        if not isinstance(marker, dict) or not isinstance(marker.get("id"), str):
            errors.append(f"pr_marker_plan.markers[{marker_index}] is invalid")
            continue
        marker_id = marker["id"]
        marker_files = marker.get("declared_files")
        if not isinstance(marker_files, list):
            errors.append(f"pr_marker_plan.markers[{marker_index}].declared_files must be an array")
            continue
        seen_marker_paths: set[str] = set()
        for file_index, record in enumerate(marker_files):
            if not isinstance(record, dict):
                errors.append(
                    f"pr_marker_plan.markers[{marker_index}].declared_files[{file_index}] must be an object"
                )
                continue
            path = record.get("path")
            operation = record.get("operation")
            source_path = record.get("source_path")
            if not isinstance(path, str) or not path or path in seen_marker_paths:
                errors.append(
                    f"pr_marker_plan.markers[{marker_index}].declared_files[{file_index}].path is invalid or duplicated"
                )
                continue
            seen_marker_paths.add(path)
            operation_record = (
                operation,
                source_path if isinstance(source_path, str) else None,
            )
            if operation_record != declared.get(path):
                errors.append(
                    f"pr_marker_plan marker {marker_id} operation/source for {path} does not match changed-file manifest"
                )
            if path in marker_operations and marker_operations[path] != operation_record:
                errors.append(f"pr_marker_plan declared operation conflict for {path}")
            marker_operations[path] = operation_record
            actual_owners.setdefault(path, set()).add(marker_id)
            if operation == "RENAMED" and isinstance(source_path, str):
                actual_source_owners.setdefault(source_path, set()).add(marker_id)
    if set(marker_operations) != set(declared):
        errors.append("pr_marker_plan declared_files union does not match changed-file manifest")
    for path, owners in expected_owners.items():
        if actual_owners.get(path, set()) != owners:
            errors.append(f"pr_marker_plan marker ownership for {path} does not match changed-file manifest")
    if set(actual_source_owners) != set(expected_source_owners):
        errors.append("pr_marker_plan rename source union does not match changed-file manifest")
    for source_path, owners in expected_source_owners.items():
        if actual_source_owners.get(source_path, set()) != owners:
            errors.append(
                f"pr_marker_plan marker ownership for rename source {source_path} does not match changed-file manifest"
            )
    if strict_contract:
        authorized_tree = _git_tree_entries(repo_root, comparison_commit)
        if authorized_tree is None:
            errors.append("authorized PR head tree is unavailable for checkpoint content binding")
        else:
            shared_paths = {
                path for path, owners in expected_owners.items() if len(owners) > 1
            }
            verified_trees: dict[str, dict[str, str] | None] = {}
            for marker_index, marker in enumerate(markers):
                if not isinstance(marker, dict):
                    continue
                checkpoint = marker.get("implementation_checkpoint")
                if not isinstance(checkpoint, dict) or checkpoint.get("status") != "complete":
                    continue
                marker_id = marker.get("id")
                verified_commit = checkpoint.get("commit_sha")
                if isinstance(verified_commit, str) and verified_commit not in verified_trees:
                    verified_trees[verified_commit] = _git_tree_entries(repo_root, verified_commit)
                verified_tree = (
                    verified_trees.get(verified_commit)
                    if isinstance(verified_commit, str)
                    else None
                )
                if verified_tree is None:
                    errors.append(
                        f"completed marker {marker_id or marker_index} verified commit tree is unavailable"
                    )
                    continue
                carrier_paths = {
                    path
                    for path in (
                        state_ref,
                        state.get("workflow_file"),
                        manifest_ref,
                        checkpoint.get("evidence_path"),
                        checkpoint.get("verification_evidence_path"),
                    )
                    if isinstance(path, str)
                }
                for carrier_marker in markers:
                    if not isinstance(carrier_marker, dict):
                        continue
                    carrier_checkpoint = carrier_marker.get(
                        "implementation_checkpoint"
                    )
                    carrier_reviewability = carrier_marker.get(
                        "reviewability"
                    )
                    if isinstance(carrier_checkpoint, dict):
                        carrier_paths.update(
                            path
                            for path in (
                                carrier_checkpoint.get("evidence_path"),
                                carrier_checkpoint.get(
                                    "verification_evidence_path"
                                ),
                            )
                            if isinstance(path, str)
                        )
                    if (
                        isinstance(carrier_reviewability, dict)
                        and isinstance(
                            carrier_reviewability.get("evidence_path"), str,
                        )
                    ):
                        carrier_paths.add(
                            carrier_reviewability["evidence_path"]
                        )
                reviewability = marker.get("reviewability")
                if (
                    isinstance(reviewability, dict)
                    and isinstance(reviewability.get("evidence_path"), str)
                ):
                    carrier_paths.add(reviewability["evidence_path"])
                corrections = checkpoint.get("corrections")
                if isinstance(corrections, list):
                    carrier_paths.update(
                        correction.get("evidence_path")
                        for correction in corrections
                        if isinstance(correction, dict)
                        and isinstance(correction.get("evidence_path"), str)
                    )
                marker_files = marker.get("declared_files")
                if not isinstance(marker_files, list):
                    continue
                for record in marker_files:
                    if not isinstance(record, dict):
                        continue
                    path = record.get("path")
                    if not isinstance(path, str) or path in carrier_paths:
                        continue
                    if path in shared_paths:
                        continue
                    if verified_tree.get(path) != authorized_tree.get(path):
                        errors.append(
                            f"completed marker {marker_id or marker_index} file {path} differs from its verified commit"
                        )
                    source_path = record.get("source_path")
                    if (
                        record.get("operation") == "RENAMED"
                        and isinstance(source_path, str)
                        and source_path not in carrier_paths
                        and verified_tree.get(source_path) != authorized_tree.get(source_path)
                    ):
                        errors.append(
                            f"completed marker {marker_id or marker_index} rename source {source_path} differs from its verified commit"
                        )
            if shared_paths:
                errors.extend(
                    _shared_checkpoint_content_errors(
                        repo_root, base_commit, authorized_tree, verified_trees,
                        markers, expected_owners, shared_paths,
                    )
                )
    return {"changed_file_manifest_errors": errors}


@dataclass
class _ProjectionContext:
    """State the projection integrity checks share.

    The first group describes the whole state file. The error lists fill in place as
    checks run. The last group is the marker under check, set as the walk reaches it.
    """

    state: dict[str, Any]
    state_path: Path
    expected_head_commit: str | None
    marker_plan: Any
    markers: Any
    plan_status: Any
    strict_contract: bool
    repo_root: Path | None
    feature_dir: Any
    phase_results: Any
    phases: dict[Any, Any]
    current_tasks_text: str | None
    current_tasks_sha: str | None
    phases_by_marker: dict[str, list[tuple[str, dict[str, Any]]]] = dataclass_field(default_factory=dict)
    checkpoint_evidence_schema: dict[str, Any] | None = None
    verification_report_schema: dict[str, Any] | None = None
    completed_phase_pending_fields: list[str] = dataclass_field(default_factory=list)
    projection_status_errors: list[str] = dataclass_field(default_factory=list)
    checkpoint_evidence_errors: list[str] = dataclass_field(default_factory=list)
    checkpoint_source_fingerprint_errors: list[str] = dataclass_field(default_factory=list)
    checkpoint_file_errors: list[str] = dataclass_field(default_factory=list)
    emission_mapping_errors: list[str] = dataclass_field(default_factory=list)
    marker_plan_status_errors: list[str] = dataclass_field(default_factory=list)
    seen_marker_ids: set[str] = dataclass_field(default_factory=set)
    seen_review_orders: set[int] = dataclass_field(default_factory=set)
    task_owners: dict[str, str] = dataclass_field(default_factory=dict)
    file_owners: dict[str, tuple[Any, Any]] = dataclass_field(default_factory=dict)
    index: Any = None
    raw_marker: Any = None
    marker_id: Any = None
    checkpoint: Any = None
    checkpoint_status: Any = None
    claimed_commit: Any = None
    committed_verification_bytes: Any = None
    correction_authority: Any = None
    correction_prefix: Any = None
    correction_projection_evidence: Any = None
    corrections: Any = None
    evidence: Any = None
    evidence_ref: Any = None
    expected_feature_id: Any = None
    projection_evidence: Any = None
    required_gate_ids: Any = None
    reviewed_head: Any = None
    superseded_evidence: Any = None
    verification: Any = None
    verification_report: Any = None


# Emission-mapping fields each emission status requires.
_EMISSION_REQUIRED_FIELDS = {
    "marker_split": ("packet_path",),
    "emitted": ("packet_path", "pr_number", "pr_url"),
}


def _emission_field_errors(
    ctx: _ProjectionContext, prefix: str, emission: dict[str, Any], status: Any,
) -> list[str]:
    """Missing required fields, a bad packet path, and fields that only an emitted mapping may carry."""
    errors: list[str] = []
    for required in _EMISSION_REQUIRED_FIELDS.get(status, ()):
        value = emission.get(required)
        if value is None or isinstance(value, str) and not value.strip():
            errors.append(f"{prefix}.{required}")
    packet_path = emission.get("packet_path")
    if packet_path is not None and (
        not _is_normalized_repo_path(packet_path)
        or ctx.repo_root and _repo_file(ctx.repo_root, packet_path) is None
    ):
        errors.append(f"{prefix}.packet_path is not a normalized repository-relative path")
    if status != "emitted":
        errors.extend(
            f"{prefix}.{field} is only valid after emission"
            for field in ("pr_number", "pr_url")
            if field in emission
        )
    return errors


def _check_marker_emission(ctx: _ProjectionContext) -> None:
    """Check the marker's emission mapping against its checkpoint."""
    emission = ctx.raw_marker.get("emission_mapping")
    if not ctx.strict_contract or not isinstance(emission, dict):
        return
    status = emission.get("status")
    prefix = f"pr_marker_plan.markers[{ctx.index}].emission_mapping"
    ctx.emission_mapping_errors.extend(_emission_field_errors(ctx, prefix, emission, status))
    if status in {"marker_split", "emitted", "hazard_collapsed"}:
        if not isinstance(ctx.checkpoint, dict) or ctx.checkpoint.get("status") != "complete":
            ctx.emission_mapping_errors.append(
                f"pr_marker_plan.markers[{ctx.index}] emission requires a complete checkpoint"
            )


def _check_phase_evidence_owners(ctx: _ProjectionContext) -> None:
    """Every phase result field must have exactly one matching checkpoint evidence owner."""
    for phase_name, phase_result in ctx.phases_by_marker.get(ctx.marker_id, []):
        for phase_field, phase_value in phase_result.items():
            if phase_field in PHASE_RESULT_PROJECTION_FIELDS:
                continue
            owner, evidence_value = _phase_evidence_owner(
                phase_field, ctx.projection_evidence,
            )
            if owner is None:
                ctx.checkpoint_evidence_errors.append(
                    f"pr_marker_plan.markers[{ctx.index}] phase_results[{phase_name}] {phase_field} has no checkpoint evidence owner"
                )
            elif owner == "multiple":
                ctx.checkpoint_evidence_errors.append(
                    f"pr_marker_plan.markers[{ctx.index}] phase_results[{phase_name}] {phase_field} has multiple checkpoint evidence owners"
                )
            elif not json_values_equal(phase_value, evidence_value):
                ctx.checkpoint_evidence_errors.append(
                    f"pr_marker_plan.markers[{ctx.index}] phase_results[{phase_name}] {phase_field} does not match checkpoint evidence"
                )


def _check_evidence_commit_binding(ctx: _ProjectionContext) -> None:
    """The checkpoint evidence status and implementation commit must agree with the checkpoint."""
    if ctx.evidence.get("status") != ctx.checkpoint_status:
        ctx.checkpoint_evidence_errors.append(
            f"pr_marker_plan.markers[{ctx.index}] checkpoint evidence status does not match checkpoint status"
        )
    ctx.claimed_commit = ctx.checkpoint.get("commit_sha")
    if ctx.claimed_commit != ctx.evidence.get("implementation_checkpoint_sha"):
        ctx.checkpoint_evidence_errors.append(
            f"pr_marker_plan.markers[{ctx.index}] checkpoint commit_sha does not match checkpoint evidence implementation_checkpoint_sha"
        )
    if ctx.repo_root is not None:
        if not _git_commit_exists(ctx.repo_root, ctx.claimed_commit):
            ctx.checkpoint_evidence_errors.append(
                f"pr_marker_plan.markers[{ctx.index}] checkpoint commit_sha is not an existing commit"
            )
        elif not (
            isinstance(ctx.expected_head_commit, str)
            and re.fullmatch(r"[0-9a-f]{40}", ctx.expected_head_commit)
            and _git_commit_is_ancestor(
                ctx.repo_root, ctx.claimed_commit, ctx.expected_head_commit,
            )
        ):
            ctx.checkpoint_evidence_errors.append(
                f"pr_marker_plan.markers[{ctx.index}] checkpoint commit_sha is not an ancestor of the authorized PR head"
            )


@dataclass
class _CorrectionChain:
    """The evidence the next correction must supersede, and the paths corrections already used."""

    path: Any
    commit: Any
    sha: Any
    used_paths: set[str]


def _error_count(ctx: _ProjectionContext) -> int:
    return len(ctx.checkpoint_evidence_errors) + len(ctx.checkpoint_file_errors)


def _check_correction_lineage(
    ctx: _ProjectionContext, chain: _CorrectionChain, prefix: str, position: int, correction: dict[str, Any],
) -> None:
    """A correction must be next in sequence, supersede the previous evidence, and descend from it in git."""
    if correction.get("sequence") != position + 1:
        ctx.checkpoint_evidence_errors.append(f"{prefix}.sequence must be append-only and contiguous")
    supersedes = (
        correction.get("supersedes_evidence_path"),
        correction.get("supersedes_evidence_commit_sha"),
        correction.get("supersedes_evidence_sha"),
    )
    if supersedes != (chain.path, chain.commit, chain.sha):
        ctx.checkpoint_evidence_errors.append(
            f"{prefix} does not supersede the previous authorized checkpoint evidence"
        )
    path = correction.get("evidence_path")
    if (
        not _is_normalized_repo_path(path)
        or path != f"{ctx.correction_prefix}{position + 1:03d}.json"
        or path == chain.path
        or path in chain.used_paths
    ):
        ctx.checkpoint_file_errors.append(f"{prefix}.evidence_path is invalid or reused")
    else:
        chain.used_paths.add(path)


def _check_correction_commit(
    ctx: _ProjectionContext, chain: _CorrectionChain, prefix: str, correction: dict[str, Any],
) -> None:
    """A correction's evidence commit must exist, introduce its path, and sit between the previous commit and the PR head."""
    commit = correction.get("checkpoint_evidence_commit_sha")
    commit_exists = _git_commit_exists(ctx.repo_root, commit)
    if not commit_exists:
        ctx.checkpoint_evidence_errors.append(
            f"{prefix}.checkpoint_evidence_commit_sha is not an existing commit"
        )
    introduction_commit = _git_path_introduction_commit(
        ctx.repo_root, correction.get("evidence_path"), ctx.expected_head_commit,
    )
    if introduction_commit != commit:
        ctx.checkpoint_evidence_errors.append(
            f"{prefix}.checkpoint_evidence_commit_sha is not the immutable path-introduction commit"
        )
    if commit_exists and not (
        isinstance(ctx.expected_head_commit, str)
        and _git_commit_is_ancestor(ctx.repo_root, commit, ctx.expected_head_commit)
    ):
        ctx.checkpoint_evidence_errors.append(
            f"{prefix}.checkpoint_evidence_commit_sha is not an ancestor of the authorized PR head"
        )
    if (
        commit_exists
        and isinstance(chain.commit, str)
        and not _git_commit_is_strict_ancestor(ctx.repo_root, chain.commit, commit)
    ):
        ctx.checkpoint_evidence_errors.append(
            f"{prefix} does not strictly descend from the superseded evidence commit"
        )


def _check_committed_evidence_bytes(
    ctx: _ProjectionContext, prefix: str, record: dict[str, Any], origin: str,
) -> bytes | None:
    """An evidence record's file must match its commit, the authorized PR head, and the worktree.

    `origin` names the record's commit in messages. Returns the bytes committed there.
    """
    path = record.get("evidence_path")
    commit = record.get("checkpoint_evidence_commit_sha")
    committed = _git_file_at_commit(ctx.repo_root, commit, path) if isinstance(path, str) else None
    if committed is None:
        ctx.checkpoint_file_errors.append(f"{prefix} evidence is absent from its {origin}")
        return None
    authorized = (
        _git_file_at_commit(ctx.repo_root, ctx.expected_head_commit, path) if isinstance(path, str) else None
    )
    if record.get("checkpoint_evidence_sha") != _sha256_bytes(committed):
        ctx.checkpoint_file_errors.append(f"{prefix}.checkpoint_evidence_sha")
    if authorized != committed:
        ctx.checkpoint_file_errors.append(f"{prefix} differs from the authorized PR head")
    if _read_repo_bytes(ctx.repo_root, path) != committed:
        ctx.checkpoint_file_errors.append(f"{prefix} worktree bytes differ from its {origin}")
    return committed


def _check_correction_record(
    ctx: _ProjectionContext, prefix: str, position: int, correction: dict[str, Any], committed: bytes | None,
) -> dict[str, Any] | None:
    """The committed correction record must satisfy the correction schema and repeat the marker's authority."""
    record = _load_json_bytes(committed)
    if not isinstance(record, dict):
        ctx.checkpoint_evidence_errors.append(f"{prefix} evidence must be a JSON object")
        return None
    if ctx.checkpoint_evidence_schema is None:
        ctx.checkpoint_evidence_errors.append(f"{prefix} schema authority is unavailable")
    else:
        schema_errors = _json_schema_errors(
            record,
            {"$ref": "#/$defs/checkpoint_correction_record"},
            ctx.checkpoint_evidence_schema,
            "checkpoint_correction",
        )
        ctx.checkpoint_evidence_errors.extend(f"{prefix} schema: {error}" for error in schema_errors)
    record_authority = (
        record.get("supersedes_evidence_path"),
        record.get("supersedes_evidence_commit_sha"),
        record.get("supersedes_evidence_sha"),
    )
    claimed_authority = (
        correction.get("supersedes_evidence_path"),
        correction.get("supersedes_evidence_commit_sha"),
        correction.get("supersedes_evidence_sha"),
    )
    if (
        record.get("feature_id") != ctx.marker_plan.get("feature_id")
        or record.get("marker_id") != ctx.marker_id
        or record.get("sequence") != position + 1
        or record_authority != claimed_authority
    ):
        ctx.checkpoint_evidence_errors.append(f"{prefix} evidence authority does not match marker state")
    return record


def _apply_owner_removals(ctx: _ProjectionContext, prefix: str, record: dict[str, Any]) -> None:
    """Drop the evidence owners a valid correction removes from the projected evidence."""
    removals = record.get("remove_evidence_owners")
    if not isinstance(removals, list):
        ctx.checkpoint_evidence_errors.append(f"{prefix}.remove_evidence_owners must be an array")
        return
    for removal in removals:
        container_name, separator, field_name = (
            removal.partition(".") if isinstance(removal, str) else ("", "", "")
        )
        if not separator or not container_name or not field_name:
            ctx.checkpoint_evidence_errors.append(
                f"{prefix} has an invalid evidence owner removal {removal!r}"
            )
            return
        container = ctx.correction_projection_evidence.get(container_name)
        if not isinstance(container, dict) or field_name not in container:
            ctx.checkpoint_evidence_errors.append(
                f"{prefix} removes a missing evidence owner {removal!r}"
            )
            return
        del container[field_name]


def _replay_correction(
    ctx: _ProjectionContext, chain: _CorrectionChain, position: int, correction: dict[str, Any],
) -> None:
    """Check one correction, apply its owner removals when it is valid, and advance the chain."""
    prefix = (
        f"pr_marker_plan.markers[{ctx.index}].implementation_checkpoint."
        f"corrections[{position}]"
    )
    errors_before = _error_count(ctx)
    _check_correction_lineage(ctx, chain, prefix, position, correction)
    _check_correction_commit(ctx, chain, prefix, correction)
    committed = _check_committed_evidence_bytes(ctx, prefix, correction, "correction commit")
    record = _check_correction_record(ctx, prefix, position, correction, committed)
    if _error_count(ctx) == errors_before and record is not None:
        _apply_owner_removals(ctx, prefix, record)
    chain.path = correction.get("evidence_path")
    chain.commit = correction.get("checkpoint_evidence_commit_sha")
    chain.sha = correction.get("checkpoint_evidence_sha")


def _check_checkpoint_corrections(ctx: _ProjectionContext) -> None:
    """Replay the append-only correction chain over the checkpoint evidence."""
    if ctx.checkpoint_status != "complete" or ctx.corrections is None:
        return
    if not isinstance(ctx.corrections, list) or ctx.superseded_evidence is None and not ctx.corrections:
        ctx.checkpoint_evidence_errors.append(
            f"pr_marker_plan.markers[{ctx.index}].implementation_checkpoint.corrections must be a non-empty array"
        )
        return
    if ctx.repo_root is None:
        return
    chain = _CorrectionChain(
        path=ctx.correction_authority.get("evidence_path"),
        commit=ctx.correction_authority.get("checkpoint_evidence_commit_sha"),
        sha=ctx.correction_authority.get("checkpoint_evidence_sha"),
        used_paths=set(),
    )
    for position, correction in enumerate(ctx.corrections):
        if isinstance(correction, dict):
            _replay_correction(ctx, chain, position, correction)
        else:
            ctx.checkpoint_evidence_errors.append(
                f"pr_marker_plan.markers[{ctx.index}].implementation_checkpoint."
                f"corrections[{position}] must be an object"
            )
    if ctx.superseded_evidence is None:
        ctx.projection_evidence = ctx.correction_projection_evidence
    elif (
        isinstance(chain.commit, str)
        and isinstance(ctx.checkpoint.get("checkpoint_evidence_commit_sha"), str)
        and not _git_commit_is_strict_ancestor(
            ctx.repo_root, chain.commit, ctx.checkpoint["checkpoint_evidence_commit_sha"],
        )
    ):
        ctx.checkpoint_evidence_errors.append(
            f"pr_marker_plan.markers[{ctx.index}].implementation_checkpoint.superseded_evidence correction chain does not strictly precede the current checkpoint evidence"
        )


def _check_superseded_commits(ctx: _ProjectionContext, prefix: str, superseded: dict[str, Any]) -> None:
    """Superseded evidence must sit in git history between its implementation and the current evidence."""
    path = superseded.get("evidence_path")
    commit = superseded.get("checkpoint_evidence_commit_sha")
    implementation = superseded.get("implementation_checkpoint_sha")
    if not _is_normalized_repo_path(path) or path == ctx.evidence_ref:
        ctx.checkpoint_file_errors.append(f"{prefix}.evidence_path is invalid or current")
    if not _git_commit_exists(ctx.repo_root, commit):
        ctx.checkpoint_evidence_errors.append(
            f"{prefix}.checkpoint_evidence_commit_sha is not an existing commit"
        )
    elif not (
        isinstance(ctx.expected_head_commit, str)
        and _git_commit_is_ancestor(ctx.repo_root, commit, ctx.expected_head_commit)
    ):
        ctx.checkpoint_evidence_errors.append(
            f"{prefix}.checkpoint_evidence_commit_sha is not an ancestor of the authorized PR head"
        )
    if not _git_commit_exists(ctx.repo_root, implementation):
        ctx.checkpoint_evidence_errors.append(
            f"{prefix}.implementation_checkpoint_sha is not an existing commit"
        )
    elif isinstance(commit, str) and not _git_commit_is_ancestor(ctx.repo_root, implementation, commit):
        ctx.checkpoint_evidence_errors.append(
            f"{prefix}.implementation_checkpoint_sha is not an ancestor of its evidence commit"
        )
    current_commit = ctx.checkpoint.get("checkpoint_evidence_commit_sha")
    if (
        isinstance(current_commit, str)
        and isinstance(commit, str)
        and _git_commit_exists(ctx.repo_root, current_commit)
        and not _git_commit_is_strict_ancestor(ctx.repo_root, commit, current_commit)
    ):
        ctx.checkpoint_evidence_errors.append(f"{prefix} does not precede the current checkpoint evidence")


def _check_superseded_record(
    ctx: _ProjectionContext, prefix: str, superseded: dict[str, Any], committed: bytes,
) -> None:
    """The superseded record must satisfy the checkpoint schema and name this marker; it seeds the correction replay."""
    parsed = _load_json_bytes(committed)
    if not isinstance(parsed, dict):
        ctx.checkpoint_evidence_errors.append(f"{prefix} evidence must be a JSON object")
        return
    ctx.correction_projection_evidence = parsed
    if ctx.checkpoint_evidence_schema is not None:
        schema_errors = _json_schema_errors(
            parsed,
            ctx.checkpoint_evidence_schema,
            ctx.checkpoint_evidence_schema,
            "superseded_checkpoint_evidence",
        )
        ctx.checkpoint_evidence_errors.extend(f"{prefix} schema: {error}" for error in schema_errors)
    if (
        parsed.get("feature_id") != ctx.marker_plan.get("feature_id")
        or parsed.get("marker_id") != ctx.marker_id
        or parsed.get("status") != "complete"
        or parsed.get("implementation_checkpoint_sha") != superseded.get("implementation_checkpoint_sha")
    ):
        ctx.checkpoint_evidence_errors.append(f"{prefix} identity does not match marker state")


def _check_superseded_evidence(ctx: _ProjectionContext) -> None:
    """Check the superseded evidence a corrected checkpoint replaced."""
    if ctx.superseded_evidence is None:
        return
    prefix = f"pr_marker_plan.markers[{ctx.index}].implementation_checkpoint.superseded_evidence"
    if not isinstance(ctx.superseded_evidence, dict):
        ctx.checkpoint_evidence_errors.append(f"{prefix} must be an object")
        return
    if ctx.repo_root is None:
        return
    _check_superseded_commits(ctx, prefix, ctx.superseded_evidence)
    committed = _check_committed_evidence_bytes(ctx, prefix, ctx.superseded_evidence, "evidence commit")
    if committed is not None:
        _check_superseded_record(ctx, prefix, ctx.superseded_evidence, committed)

def _gate_results_all_pass(results: dict[str, Any]) -> bool:
    return all(
        isinstance(result, dict)
        and set(result) == {"status", "evidence"}
        and result.get("status") == "pass"
        and isinstance(result.get("evidence"), str)
        and bool(result["evidence"].strip())
        for result in results.values()
    )


def _verification_gate_agreement(
    checkpoint: Any, evidence: Any, verification_report: Any,
) -> tuple[bool, bool, bool, bool, list[str] | None, Any]:
    """Compare the checkpoint's, the evidence's, and the verification report's required gates and results.

    Returns whether the gate sets match, the evidence results all pass, the report gate
    set matches, the report results match the evidence, then the required gate ids and
    the evidence's verification record.
    """
    required_gate_ids = _string_list(checkpoint.get("required_verification_gate_ids"))
    evidence_gate_ids = _string_list(evidence.get("required_verification_gate_ids"))
    verification = evidence.get("verification")
    report = verification_report if isinstance(verification_report, dict) else None
    report_gate_ids = _string_list(report.get("required_gate_ids")) if report is not None else None
    report_results = report.get("results") if report is not None else None
    gate_sets_match = (
        required_gate_ids is not None
        and evidence_gate_ids is not None
        and len(required_gate_ids) == len(set(required_gate_ids))
        and len(evidence_gate_ids) == len(set(evidence_gate_ids))
        and set(required_gate_ids) == set(evidence_gate_ids)
        and isinstance(verification, dict)
        and set(verification) == set(required_gate_ids)
    )
    passing_results = gate_sets_match and _gate_results_all_pass(verification)
    report_gate_sets_match = (
        gate_sets_match
        and report_gate_ids is not None
        and required_gate_ids == evidence_gate_ids == report_gate_ids
        and isinstance(report_results, dict)
        and set(report_results) == set(required_gate_ids)
    )
    report_passing_results = report_gate_sets_match and _gate_results_all_pass(report_results)
    report_results_match = report_passing_results and report_results == verification
    return (
        gate_sets_match, passing_results, report_gate_sets_match, report_results_match,
        required_gate_ids, verification,
    )


_REPORT_FIELDS = (
    "schema_version", "feature_id", "marker_id", "status", "generated_at", "verified_commit_sha",
)


def _verification_report_checks(
    ctx: _ProjectionContext, report_gate_sets_match: bool, report_results_match: bool,
) -> dict[str, bool]:
    """Whether each verification report field agrees with the marker, the commit, and the evidence."""
    report = ctx.verification_report
    if not isinstance(report, dict):
        return {
            **dict.fromkeys(_REPORT_FIELDS, False),
            "required_gate_ids": report_gate_sets_match,
            "results": report_results_match,
        }
    return {
        "schema_version": report.get("schema_version") == "verification-report.v1",
        "feature_id": report.get("feature_id") == ctx.expected_feature_id,
        "marker_id": report.get("marker_id") == ctx.marker_id,
        "status": report.get("status") == "pass",
        "generated_at": _is_utc_timestamp(report.get("generated_at")),
        "verified_commit_sha": report.get("verified_commit_sha") == ctx.claimed_commit,
        "required_gate_ids": report_gate_sets_match,
        "results": report_results_match,
    }


def _check_complete_verification_evidence(ctx: _ProjectionContext) -> None:
    """A complete checkpoint's evidence and verification report must agree gate by gate."""
    evidence = ctx.evidence
    ctx.expected_feature_id = ctx.marker_plan.get("feature_id") if isinstance(ctx.marker_plan, dict) else None
    (
        gate_sets_match, passing_results, report_gate_sets_match, report_results_match,
        ctx.required_gate_ids, ctx.verification,
    ) = _verification_gate_agreement(ctx.checkpoint, evidence, ctx.verification_report)
    evidence_checks = {
        "schema_version": evidence.get("schema_version") == "marker-checkpoint.v1",
        "feature_id": evidence.get("feature_id") == ctx.expected_feature_id,
        "marker_id": evidence.get("marker_id") == ctx.marker_id,
        "status": evidence.get("status") == "complete",
        "completed_at": _is_utc_timestamp(evidence.get("completed_at")),
        "tasks_sha": (
            isinstance(evidence.get("tasks_sha"), str)
            and re.fullmatch(r"sha256:[0-9a-f]{64}", evidence["tasks_sha"]) is not None
        ),
        "source_fingerprint_status": evidence.get("source_fingerprint_status") == "current",
        "verification_evidence_sha": (
            ctx.committed_verification_bytes is not None
            and evidence.get("verification_evidence_sha")
            == ctx.checkpoint.get("verification_evidence_sha")
            == _sha256_bytes(ctx.committed_verification_bytes)
        ),
        "required_verification_gate_ids": gate_sets_match,
        "verification": passing_results,
    }
    prefix = f"pr_marker_plan.markers[{ctx.index}]"
    ctx.checkpoint_evidence_errors.extend(
        f"{prefix} checkpoint evidence {field} is invalid"
        for field, passed in evidence_checks.items() if not passed
    )
    report_checks = _verification_report_checks(ctx, report_gate_sets_match, report_results_match)
    ctx.checkpoint_evidence_errors.extend(
        f"{prefix} verification report {field} is invalid"
        for field, passed in report_checks.items() if not passed
    )
    if evidence.get("implementation_checkpoint_sha") != ctx.claimed_commit:
        ctx.checkpoint_evidence_errors.append(
            f"{prefix} checkpoint/evidence implementation commit mismatch"
        )


# Where each marker's own checkpoint, verification, and reviewability carrier files live.
_GLOBAL_CARRIER_NAMESPACES = {
    "checkpoint": "checkpoints/",
    "verification": "verification/",
    "reviewability": "reviewability/",
}


def _marker_carrier_paths(marker: dict[str, Any]) -> dict[str, Any]:
    checkpoint = marker.get("implementation_checkpoint")
    reviewability = marker.get("reviewability")
    return {
        "checkpoint": checkpoint.get("evidence_path") if isinstance(checkpoint, dict) else None,
        "verification": checkpoint.get("verification_evidence_path") if isinstance(checkpoint, dict) else None,
        "reviewability": reviewability.get("evidence_path") if isinstance(reviewability, dict) else None,
    }


def _collect_global_carrier_paths(
    ctx: _ProjectionContext, feature_process_prefix: str | None, review_carrier_paths: set[str],
) -> None:
    """Every marker's own carrier files count as review carriers, so later markers may change them."""
    if feature_process_prefix is None:
        return
    for marker in ctx.markers or []:
        if not isinstance(marker, dict):
            continue
        for role, path in _marker_carrier_paths(marker).items():
            namespace = feature_process_prefix + _GLOBAL_CARRIER_NAMESPACES[role]
            if _is_normalized_repo_path(path) and path.startswith(namespace) and path.endswith(".json"):
                review_carrier_paths.add(path)
def _check_carrier_roles_unchanged(role_bindings: Any, reviewed_roles: Any, ctx: _ProjectionContext, role_namespace_checks: Any, review_carrier_paths: Any) -> None:
    """Each carrier role must still name the file it named at the independently reviewed head."""
    for role, current_path in role_bindings.items():
        reviewed_path = reviewed_roles.get(role)
        if (
            isinstance(reviewed_path, str)
            and reviewed_path != current_path
        ):
            ctx.checkpoint_evidence_errors.append(
                f"pr_marker_plan.markers[{ctx.index}] independent review carrier role {role!r} changed after review"
            )
        carrier_path = (
            reviewed_path
            if isinstance(reviewed_path, str)
            else current_path
        )
        if (
            role_namespace_checks.get(role)
            and isinstance(carrier_path, str)
        ):
            review_carrier_paths.add(
                carrier_path
            )


def _reviewed_marker(reviewed_state: dict[str, Any], marker_id: Any) -> Any:
    plan = reviewed_state.get("pr_marker_plan")
    markers = plan.get("markers") if isinstance(plan, dict) else None
    return next(
        (m for m in markers or [] if isinstance(m, dict) and m.get("id") == marker_id),
        None,
    )


def _reviewed_marker_roles(marker: dict[str, Any]) -> dict[str, Any]:
    roles: dict[str, Any] = {}
    checkpoint = marker.get("implementation_checkpoint")
    reviewability = marker.get("reviewability")
    if isinstance(checkpoint, dict):
        roles["checkpoint_evidence"] = checkpoint.get("evidence_path")
        roles["verification_evidence"] = checkpoint.get("verification_evidence_path")
    if isinstance(reviewability, dict):
        roles["reviewability_evidence"] = reviewability.get("evidence_path")
    return roles


def _reviewed_carrier_roles(ctx: _ProjectionContext, reviewed_state: Any) -> dict[str, Any]:
    """Read the carrier roles the independently reviewed head recorded."""
    if not isinstance(reviewed_state, dict):
        return {}
    reviewed_feature_dir = reviewed_state.get("feature_dir")
    if isinstance(reviewed_feature_dir, str) and reviewed_feature_dir != ctx.feature_dir:
        ctx.checkpoint_evidence_errors.append(
            f"pr_marker_plan.markers[{ctx.index}] feature_dir changed after independent review"
        )
    roles: dict[str, Any] = {
        "workflow_file": reviewed_state.get("workflow_file"),
        "changed_file_manifest": reviewed_state.get("changed_file_manifest"),
    }
    marker = _reviewed_marker(reviewed_state, ctx.marker_id)
    if isinstance(marker, dict):
        roles.update(_reviewed_marker_roles(marker))
    return roles
def _check_review_delta(authorized_head_valid: Any, ctx: _ProjectionContext, role_bindings: Any, role_namespace_checks: Any, feature_process_prefix: Any) -> None:
    """Every path changed after the independent review must be a review carrier file."""
    if authorized_head_valid:
        changed_after_review = _git_changed_paths(
            ctx.repo_root,
            ctx.reviewed_head,
            ctx.expected_head_commit,
        )
        try:
            state_ref = (
                ctx.state_path.resolve()
                .relative_to(ctx.repo_root.resolve())
                .as_posix()
            )
        except ValueError:
            state_ref = None
        reviewed_state = _load_json_bytes(
            _git_file_at_commit(
                ctx.repo_root,
                ctx.reviewed_head,
                state_ref,
            )
            if isinstance(state_ref, str)
            else None
        )
        reviewed_roles = _reviewed_carrier_roles(ctx, reviewed_state)
        review_carrier_paths = {
            state_ref
        } if isinstance(state_ref, str) else set()
        _check_carrier_roles_unchanged(role_bindings, reviewed_roles, ctx, role_namespace_checks, review_carrier_paths)
        _collect_global_carrier_paths(ctx, feature_process_prefix, review_carrier_paths)
        if changed_after_review is None:
            ctx.checkpoint_evidence_errors.append(
                f"pr_marker_plan.markers[{ctx.index}] independent review delta is unavailable"
            )
        else:
            for path in sorted(
                changed_after_review
                - review_carrier_paths
            ):
                ctx.checkpoint_evidence_errors.append(
                    f"pr_marker_plan.markers[{ctx.index}] unreviewed non-carrier path after independent review: {path}"
                )


def _check_review_gates_bind_head(review_gate_ids: Any, ctx: _ProjectionContext) -> None:
    """Each independent review gate's evidence must name the reviewed head."""
    for gate_id in review_gate_ids:
        gate_result = (
            ctx.verification.get(gate_id)
            if isinstance(ctx.verification, dict)
            else None
        )
        gate_evidence = (
            gate_result.get("evidence")
            if isinstance(gate_result, dict)
            else None
        )
        if (
            not isinstance(gate_evidence, str)
            or ctx.reviewed_head not in gate_evidence
        ):
            ctx.checkpoint_evidence_errors.append(
                f"pr_marker_plan.markers[{ctx.index}] independent review gate {gate_id!r} does not bind last_reviewed_head_sha"
            )


def _check_reviewability_evidence_binds_review(role_namespace_checks: Any, ctx: _ProjectionContext, reviewability_ref: Any) -> None:
    """The reviewability evidence file must bind the independently reviewed head."""
    if role_namespace_checks[
        "reviewability_evidence"
    ]:
        reviewability_evidence = _load_json_bytes(
            _git_file_at_commit(
                ctx.repo_root,
                ctx.expected_head_commit,
                reviewability_ref,
            )
        )
        if (
            not isinstance(
                reviewability_evidence, dict,
            )
            or reviewability_evidence.get(
                "schema_version"
            )
            != "reviewability-evidence.v1"
            or reviewability_evidence.get(
                "feature_id"
            )
            != ctx.expected_feature_id
            or reviewability_evidence.get(
                "marker_id"
            )
            != ctx.marker_id
            or reviewability_evidence.get("head_sha")
            != ctx.reviewed_head
        ):
            ctx.checkpoint_evidence_errors.append(
                f"pr_marker_plan.markers[{ctx.index}] reviewability evidence does not bind the independent review head"
            )


# Carrier roles that must name a file with a fixed suffix anywhere in the repository.
_CARRIER_FILE_SUFFIXES = {
    "workflow_file": "workflow.md",
    "changed_file_manifest": "changed-file-manifest.json",
}
# Carrier roles that must name a JSON file in one feature `.process/` subdirectory.
_CARRIER_NAMESPACES = {
    "checkpoint_evidence": "checkpoints/",
    "verification_evidence": "verification/",
    "reviewability_evidence": "reviewability/",
}


def _carrier_role_in_namespace(role: str, path: Any, feature_process_prefix: str | None) -> bool:
    if not _is_normalized_repo_path(path):
        return False
    if role in _CARRIER_FILE_SUFFIXES:
        return path.endswith(_CARRIER_FILE_SUFFIXES[role])
    return (
        feature_process_prefix is not None
        and path.startswith(feature_process_prefix + _CARRIER_NAMESPACES[role])
        and path.endswith(".json")
    )


def _review_carrier_role_checks(ctx: _ProjectionContext, reviewability_ref: Any, feature_process_prefix: str | None) -> tuple[dict[str, Any], dict[str, bool]]:
    """Each independent review carrier role must name a file inside its metadata namespace."""
    role_bindings = {
        "workflow_file": ctx.state.get("workflow_file"),
        "changed_file_manifest": ctx.state.get("changed_file_manifest"),
        "checkpoint_evidence": ctx.checkpoint.get("evidence_path"),
        "verification_evidence": ctx.checkpoint.get("verification_evidence_path"),
        "reviewability_evidence": reviewability_ref,
    }
    role_namespace_checks = {
        role: _carrier_role_in_namespace(role, path, feature_process_prefix)
        for role, path in role_bindings.items()
    }
    ctx.checkpoint_evidence_errors.extend(
        f"pr_marker_plan.markers[{ctx.index}] independent review carrier role {role!r} is missing or outside its metadata namespace"
        for role, passed in role_namespace_checks.items()
        if not passed
    )
    return role_bindings, role_namespace_checks


def _check_review_head_ancestry(ctx: _ProjectionContext) -> bool:
    """The reviewed head must cover the checkpoint commit and precede the authorized PR head.

    Returns whether the reviewed head is an ancestor of the authorized PR head.
    """
    if (
        not _git_commit_exists(ctx.repo_root, ctx.claimed_commit)
        or not _git_commit_is_ancestor(ctx.repo_root, ctx.claimed_commit, ctx.reviewed_head)
    ):
        ctx.checkpoint_evidence_errors.append(
            f"pr_marker_plan.markers[{ctx.index}] independent review does not cover the implementation checkpoint"
        )
    authorized_head_valid = (
        isinstance(ctx.expected_head_commit, str)
        and re.fullmatch(r"[0-9a-f]{40}", ctx.expected_head_commit) is not None
        and _git_commit_exists(ctx.repo_root, ctx.expected_head_commit)
        and _git_commit_is_ancestor(ctx.repo_root, ctx.reviewed_head, ctx.expected_head_commit)
    )
    if not authorized_head_valid:
        ctx.checkpoint_evidence_errors.append(
            f"pr_marker_plan.markers[{ctx.index}] independent review head is not an ancestor of the authorized PR head"
        )
    return authorized_head_valid


def _check_independent_review(ctx: _ProjectionContext) -> None:
    """Independent review gates must bind the reviewed head to the implementation and the authorized PR head."""
    review_gate_ids = sorted(set(ctx.required_gate_ids or ()) & INDEPENDENT_REVIEW_GATE_IDS)
    if not review_gate_ids:
        return
    ctx.reviewed_head = ctx.evidence.get("last_reviewed_head_sha")
    reviewed_head_valid = (
        isinstance(ctx.reviewed_head, str)
        and re.fullmatch(r"[0-9a-f]{40}", ctx.reviewed_head) is not None
        and _git_commit_exists(ctx.repo_root, ctx.reviewed_head)
    )
    if not reviewed_head_valid:
        ctx.checkpoint_evidence_errors.append(
            f"pr_marker_plan.markers[{ctx.index}] checkpoint evidence last_reviewed_head_sha is invalid"
        )
        return
    authorized_head_valid = _check_review_head_ancestry(ctx)
    reviewability = ctx.raw_marker.get("reviewability")
    projected_reviewed_head = (
        reviewability.get("head_sha") if isinstance(reviewability, dict) else None
    )
    if projected_reviewed_head != ctx.reviewed_head:
        ctx.checkpoint_evidence_errors.append(
            f"pr_marker_plan.markers[{ctx.index}] checkpoint/reviewability reviewed-head mismatch"
        )
    reviewability_ref = (
        reviewability.get("evidence_path") if isinstance(reviewability, dict) else None
    )
    feature_process_prefix = (
        f"{ctx.feature_dir}/.process/" if _is_normalized_repo_path(ctx.feature_dir) else None
    )
    role_bindings, role_namespace_checks = _review_carrier_role_checks(ctx, reviewability_ref, feature_process_prefix)
    _check_reviewability_evidence_binds_review(role_namespace_checks, ctx, reviewability_ref)
    _check_review_gates_bind_head(review_gate_ids, ctx)
    _check_review_delta(authorized_head_valid, ctx, role_bindings, role_namespace_checks, feature_process_prefix)


# Checkpoint and emission statuses each marker-plan status allows.
_PLAN_STATUS_CONSTRAINTS = {
    "planned": ({"pending"}, {"pending"}),
    "checkpointing": ({"pending", "complete"}, {"pending"}),
    "emission_ready": ({"complete"}, {"pending", "marker_split"}),
    "emitting": ({"complete"}, {"pending", "marker_split", "emitted"}),
    "emitted": ({"complete"}, {"emitted"}),
    "collapsed": ({"complete"}, {"hazard_collapsed"}),
    "stale": ({"pending", "complete"}, {"pending", "marker_split", "emitted", "hazard_collapsed"}),
    "invalid": ({"pending", "complete"}, {"pending", "marker_split", "emitted", "hazard_collapsed"}),
}


def _marker_status_pair(raw_marker: Any) -> tuple[Any, Any]:
    """The marker's checkpoint status and emission status, None where absent."""
    checkpoint = raw_marker.get("implementation_checkpoint") if isinstance(raw_marker, dict) else None
    emission = raw_marker.get("emission_mapping") if isinstance(raw_marker, dict) else None
    return (
        checkpoint.get("status") if isinstance(checkpoint, dict) else None,
        emission.get("status") if isinstance(emission, dict) else None,
    )


def _check_plan_status_constraints(ctx: _ProjectionContext) -> None:
    """The marker plan's own status limits which checkpoint and emission states its markers may hold."""
    if not ctx.strict_contract or ctx.plan_status not in _PLAN_STATUS_CONSTRAINTS:
        return
    allowed_checkpoints, allowed_emissions = _PLAN_STATUS_CONSTRAINTS[ctx.plan_status]
    for index, raw_marker in enumerate(ctx.markers):
        checkpoint_status, emission_status = _marker_status_pair(raw_marker)
        if checkpoint_status not in allowed_checkpoints:
            ctx.marker_plan_status_errors.append(
                f"pr_marker_plan.status {ctx.plan_status} rejects marker {index} checkpoint {checkpoint_status!r}"
            )
        if emission_status not in allowed_emissions:
            ctx.marker_plan_status_errors.append(
                f"pr_marker_plan.status {ctx.plan_status} rejects marker {index} emission {emission_status!r}"
            )
    if ctx.plan_status == "emitting":
        emission_statuses = {
            raw_marker.get("emission_mapping", {}).get("status")
            for raw_marker in ctx.markers
            if isinstance(raw_marker, dict) and isinstance(raw_marker.get("emission_mapping"), dict)
        }
        if "emitted" not in emission_statuses or emission_statuses <= {"emitted"}:
            ctx.marker_plan_status_errors.append(
                "pr_marker_plan.status emitting requires both emitted and unfinished marker mappings"
            )


def _check_pending_claims_and_paths(ctx: _ProjectionContext) -> None:
    """A strict checkpoint's pending claims and evidence paths must be well formed."""
    pending_phase_claims = _marker_phase_claims(ctx.phase_results, ctx.marker_id)
    if ctx.strict_contract and ctx.checkpoint_status == "pending" and pending_phase_claims:
        if not _is_normalized_repo_path(ctx.checkpoint.get("evidence_path")):
            ctx.checkpoint_evidence_errors.append(
                f"pr_marker_plan.markers[{ctx.index}] pending checkpoint with phase claims requires evidence_path"
            )
        if not isinstance(ctx.checkpoint.get("commit_sha"), str) or not re.fullmatch(
            r"[0-9a-f]{40}", ctx.checkpoint["commit_sha"]
        ):
            ctx.checkpoint_evidence_errors.append(
                f"pr_marker_plan.markers[{ctx.index}] pending checkpoint with phase claims requires commit_sha"
            )
    for path_field in ("evidence_path", "verification_evidence_path") if ctx.strict_contract else ():
        path_value = ctx.checkpoint.get(path_field)
        if path_value is not None and (
            not _is_normalized_repo_path(path_value)
            or ctx.repo_root and _repo_file(ctx.repo_root, path_value) is None
        ):
            ctx.checkpoint_file_errors.append(
                f"pr_marker_plan.markers[{ctx.index}].implementation_checkpoint.{path_field} is not a normalized repository-relative path"
            )


@dataclass(frozen=True)
class _BoundFileMessages:
    """The error text for one evidence file bound to a checkpoint commit."""

    absent: str
    sha: str
    worktree: str
    authorized: str | None = None


def _bound_file_messages(prefix: str, *, verification: bool, pending: bool) -> _BoundFileMessages:
    """The error text for a checkpoint's evidence file, or its verification file."""
    checkpoint = f"{prefix}.implementation_checkpoint"
    noun = "verification" if verification else "checkpoint"
    if verification:
        absent = f"{checkpoint} verification evidence is absent from checkpoint commit"
    else:
        absent = f"{checkpoint}.checkpoint_evidence_commit_sha"
    return _BoundFileMessages(
        absent=absent,
        sha=f"{checkpoint}.{noun}_evidence_sha",
        worktree=(
            f"{prefix} pending {noun} evidence worktree differs from checkpoint commit"
            if pending
            else f"{checkpoint} immutable {'verification ' if verification else ''}evidence differs from checkpoint commit"
        ),
        authorized=f"{prefix} pending {noun} evidence differs from checkpoint commit" if pending else None,
    )


def _check_bound_file(
    ctx: _ProjectionContext, ref: Any, expected_sha: Any, messages: _BoundFileMessages,
) -> bytes | None:
    """A checkpoint's evidence file must match the bytes committed at its evidence commit.

    Returns the committed bytes, or None when the commit does not hold the file.
    """
    commit = ctx.checkpoint.get("checkpoint_evidence_commit_sha")
    committed = _git_file_at_commit(ctx.repo_root, commit, ref) if isinstance(ref, str) else None
    if committed is None:
        ctx.checkpoint_file_errors.append(messages.absent)
        return None
    if expected_sha != _sha256_bytes(committed):
        ctx.checkpoint_file_errors.append(messages.sha)
    if messages.authorized is not None:
        authorized = (
            _git_file_at_commit(ctx.repo_root, ctx.expected_head_commit, ref) if isinstance(ref, str) else None
        )
        if authorized != committed:
            ctx.checkpoint_file_errors.append(messages.authorized)
    if _read_repo_bytes(ctx.repo_root, ref) != committed:
        ctx.checkpoint_file_errors.append(messages.worktree)
    return committed


def _check_evidence_commit_ancestry(ctx: _ProjectionContext, head: Any, head_label: str) -> None:
    """The evidence commit must exist, descend from the implementation commit, and precede `head`."""
    prefix = f"pr_marker_plan.markers[{ctx.index}]"
    commit = ctx.checkpoint.get("checkpoint_evidence_commit_sha")
    claimed = ctx.checkpoint.get("commit_sha")
    if not _git_commit_exists(ctx.repo_root, commit):
        ctx.checkpoint_evidence_errors.append(
            f"{prefix}.implementation_checkpoint.checkpoint_evidence_commit_sha is not an existing commit"
        )
    elif not (isinstance(head, str) and _git_commit_is_ancestor(ctx.repo_root, commit, head)):
        ctx.checkpoint_evidence_errors.append(
            f"{prefix}.implementation_checkpoint.checkpoint_evidence_commit_sha is not an ancestor of {head_label}"
        )
    elif _git_commit_exists(ctx.repo_root, claimed) and not _git_commit_is_ancestor(
        ctx.repo_root, claimed, commit,
    ):
        ctx.checkpoint_evidence_errors.append(
            f"{prefix} implementation commit is not an ancestor of evidence commit"
        )


def _is_unique_string_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item for item in value)
        and len(set(value)) == len(value)
    )


def _invalid_complete_fields(checkpoint: dict[str, Any]) -> list[str]:
    """The required fields a complete checkpoint lacks or carries in the wrong shape."""
    return [
        *(
            field for field in COMPLETE_CHECKPOINT_STRING_FIELDS
            if not isinstance(checkpoint.get(field), str) or not checkpoint[field].strip()
        ),
        *(
            field for field in COMPLETE_CHECKPOINT_LIST_FIELDS
            if not _is_unique_string_list(checkpoint.get(field))
        ),
        *(
            field for field in COMPLETE_CHECKPOINT_OBJECT_FIELDS
            if not isinstance(checkpoint.get(field), dict)
        ),
    ]


def _check_complete_field_presence(ctx: _ProjectionContext) -> None:
    """A complete checkpoint must carry its required fields, cover the marker's tasks, and name one commit."""
    prefix = f"pr_marker_plan.markers[{ctx.index}]"
    ctx.checkpoint_evidence_errors.extend(
        f"{prefix}.implementation_checkpoint.{field}" for field in _invalid_complete_fields(ctx.checkpoint)
    )
    task_ids = _string_list(ctx.raw_marker.get("task_ids"))
    folded_task_ids = _string_list(ctx.raw_marker.get("folded_polish_task_ids"))
    expected_tasks = set(task_ids or ()) | set(folded_task_ids or ())
    completed_tasks = _string_list(ctx.checkpoint.get("completed_task_ids"))
    if task_ids is None or folded_task_ids is None:
        ctx.checkpoint_evidence_errors.append(f"{prefix} marker task coverage")
    elif completed_tasks is not None and set(completed_tasks) != expected_tasks:
        ctx.checkpoint_evidence_errors.append(
            f"{prefix}.implementation_checkpoint.completed_task_ids coverage"
        )
    if ctx.checkpoint.get("commit_sha") != ctx.checkpoint.get("head_sha"):
        ctx.checkpoint_evidence_errors.append(f"{prefix}.implementation_checkpoint commit/head mismatch")


def _check_complete_evidence_files(ctx: _ProjectionContext) -> None:
    """A complete checkpoint's evidence and verification files must exist and match their commit."""
    prefix = f"pr_marker_plan.markers[{ctx.index}]"
    ctx.evidence_ref = ctx.checkpoint.get("evidence_path")
    verification_ref = ctx.checkpoint.get("verification_evidence_path")
    for required, ref in (("evidence_path", ctx.evidence_ref), ("verification_evidence_path", verification_ref)):
        if _read_repo_bytes(ctx.repo_root, ref) is None:
            ctx.checkpoint_file_errors.append(f"{prefix}.implementation_checkpoint.{required}")
    if ctx.evidence_ref == verification_ref:
        ctx.checkpoint_evidence_errors.append(
            f"{prefix} checkpoint and verification evidence paths must differ"
        )
    _check_bound_file(
        ctx, ctx.evidence_ref, ctx.checkpoint.get("checkpoint_evidence_sha"),
        _bound_file_messages(prefix, verification=False, pending=False),
    )
    ctx.committed_verification_bytes = _check_bound_file(
        ctx, verification_ref, ctx.checkpoint.get("verification_evidence_sha"),
        _bound_file_messages(prefix, verification=True, pending=False),
    )


def _check_complete_checkpoint_fields(ctx: _ProjectionContext) -> None:
    """A complete checkpoint must carry every required field and its evidence commit and files."""
    if ctx.checkpoint_status != "complete" or not ctx.strict_contract:
        return
    _check_complete_field_presence(ctx)
    if ctx.repo_root:
        _check_evidence_commit_ancestry(ctx, "HEAD", "HEAD")
        _check_complete_evidence_files(ctx)


_PENDING_AUTHORITY_FIELDS = (
    "checkpoint_evidence_sha",
    "checkpoint_evidence_commit_sha",
    "verification_evidence_path",
    "verification_evidence_sha",
)


def _check_pending_checkpoint_authority(ctx: _ProjectionContext) -> None:
    """A pending checkpoint that names evidence must bind it to a commit and files."""
    if not (
        ctx.checkpoint_status == "pending"
        and ctx.strict_contract
        and ctx.repo_root
        and any(field in ctx.checkpoint for field in _PENDING_AUTHORITY_FIELDS)
    ):
        return
    prefix = f"pr_marker_plan.markers[{ctx.index}]"
    ctx.evidence_ref = ctx.checkpoint.get("evidence_path")
    verification_ref = ctx.checkpoint.get("verification_evidence_path")
    _check_evidence_commit_ancestry(ctx, ctx.expected_head_commit, "the authorized PR head")
    if ctx.evidence_ref == verification_ref:
        ctx.checkpoint_evidence_errors.append(
            f"{prefix} checkpoint and verification evidence paths must differ"
        )
    _check_bound_file(
        ctx, ctx.evidence_ref, ctx.checkpoint.get("checkpoint_evidence_sha"),
        _bound_file_messages(prefix, verification=False, pending=True),
    )
    _check_bound_file(
        ctx, verification_ref, ctx.checkpoint.get("verification_evidence_sha"),
        _bound_file_messages(prefix, verification=True, pending=True),
    )


def _authorized_evidence_bytes(ctx: _ProjectionContext) -> bytes | None:
    """The checkpoint evidence bytes at the authorized PR head, checked against the worktree."""
    if not (ctx.strict_contract and ctx.repo_root and isinstance(ctx.evidence_ref, str)):
        return None
    prefix = f"pr_marker_plan.markers[{ctx.index}]"
    authorized = _git_file_at_commit(ctx.repo_root, ctx.expected_head_commit, ctx.evidence_ref)
    if authorized is None:
        ctx.checkpoint_file_errors.append(f"{prefix} checkpoint evidence is absent from the authorized PR head")
    elif _read_repo_bytes(ctx.repo_root, ctx.evidence_ref) != authorized:
        ctx.checkpoint_file_errors.append(f"{prefix} checkpoint evidence differs from the authorized PR head")
    return authorized


def _load_checkpoint_evidence(ctx: _ProjectionContext) -> None:
    """Load the checkpoint evidence from the authorized head, or the commit or worktree for legacy plans."""
    ctx.evidence_ref = ctx.checkpoint.get("evidence_path")
    authorized = _authorized_evidence_bytes(ctx)
    if ctx.strict_contract:
        source = authorized
    elif ctx.checkpoint_status == "complete":
        source = (
            _git_file_at_commit(
                ctx.repo_root, ctx.checkpoint.get("checkpoint_evidence_commit_sha"), ctx.evidence_ref,
            )
            if ctx.repo_root and isinstance(ctx.evidence_ref, str)
            else None
        )
    else:
        source = _read_repo_bytes(ctx.repo_root, ctx.evidence_ref) if ctx.repo_root is not None else None
    ctx.evidence = _load_json_bytes(source)
    if (
        ctx.strict_contract
        and ctx.repo_root is not None
        and ctx.expected_head_commit is not None
        and isinstance(ctx.evidence_ref, str)
        and not isinstance(ctx.evidence, dict)
    ):
        ctx.checkpoint_evidence_errors.append(
            f"pr_marker_plan.markers[{ctx.index}] checkpoint evidence must be a JSON object"
        )
    ctx.projection_evidence = ctx.evidence


def _prepare_corrections(ctx: _ProjectionContext) -> None:
    """Find the correction authority and check the declared corrections cover the committed correction files."""
    ctx.superseded_evidence = ctx.checkpoint.get("superseded_evidence")
    prefix = f"pr_marker_plan.markers[{ctx.index}]"
    if ctx.superseded_evidence is not None and ctx.checkpoint.get("corrections") is not None:
        ctx.checkpoint_evidence_errors.append(
            f"{prefix}.implementation_checkpoint must not declare both corrections and superseded_evidence"
        )
    ctx.correction_authority = (
        ctx.superseded_evidence if isinstance(ctx.superseded_evidence, dict) else ctx.checkpoint
    )
    ctx.corrections = ctx.correction_authority.get("corrections")
    ctx.correction_prefix = f"{ctx.feature_dir}/.process/checkpoint-corrections/{ctx.marker_id}-"
    authorized_tree = (
        _git_tree_entries(ctx.repo_root, ctx.expected_head_commit) if ctx.repo_root is not None else None
    )
    correction_file = re.compile(rf"{re.escape(ctx.correction_prefix)}[0-9]{{3}}\.json")
    discovered_corrections = sorted(
        path for path in authorized_tree or {} if correction_file.fullmatch(path)
    )
    declared_corrections = (
        [c.get("evidence_path") for c in ctx.corrections if isinstance(c, dict)]
        if isinstance(ctx.corrections, list)
        else []
    )
    if discovered_corrections != declared_corrections:
        ctx.checkpoint_evidence_errors.append(
            f"{prefix} checkpoint correction state does not cover the authorized append-only correction files"
        )


def _check_checkpoint_evidence_body(ctx: _ProjectionContext) -> None:
    """Check strict checkpoint evidence against its schema, corrections, commits, and phase results."""
    if not (ctx.strict_contract and isinstance(ctx.evidence, dict)):
        return
    if ctx.checkpoint_evidence_schema is not None:
        ctx.checkpoint_evidence_errors.extend(
            f"pr_marker_plan.markers[{ctx.index}] checkpoint evidence schema: {error}"
            for error in _json_schema_errors(
                ctx.evidence,
                ctx.checkpoint_evidence_schema,
                ctx.checkpoint_evidence_schema,
                "checkpoint_evidence",
            )
        )
    _prepare_corrections(ctx)
    ctx.correction_projection_evidence = json.loads(json.dumps(ctx.evidence))
    _check_superseded_evidence(ctx)
    _check_checkpoint_corrections(ctx)
    _check_evidence_commit_binding(ctx)
    _check_phase_evidence_owners(ctx)


def _check_complete_verification_report(ctx: _ProjectionContext) -> None:
    """A complete checkpoint's verification report must be an object that matches the evidence."""
    if ctx.checkpoint_status == "complete" and ctx.strict_contract and ctx.repo_root:
        ctx.claimed_commit = ctx.checkpoint.get("commit_sha")
        ctx.verification_report = _load_json_bytes(ctx.committed_verification_bytes)
        if not isinstance(ctx.verification_report, dict):
            ctx.checkpoint_evidence_errors.append(
                f"pr_marker_plan.markers[{ctx.index}] verification report must be a JSON object"
            )
        elif ctx.verification_report_schema is not None:
            ctx.checkpoint_evidence_errors.extend(
                f"pr_marker_plan.markers[{ctx.index}] verification report schema: {error}"
                for error in _json_schema_errors(
                    ctx.verification_report,
                    ctx.verification_report_schema,
                    ctx.verification_report_schema,
                    "verification_report",
                )
            )
        if not isinstance(ctx.evidence, dict):
            ctx.checkpoint_evidence_errors.append(
                f"pr_marker_plan.markers[{ctx.index}] checkpoint evidence must be a JSON object"
            )
        else:
            _check_complete_verification_evidence(ctx)
            _check_independent_review(ctx)
        if ctx.repo_root:
            if not _git_commit_exists(ctx.repo_root, ctx.claimed_commit):
                ctx.checkpoint_evidence_errors.append(
                    f"pr_marker_plan.markers[{ctx.index}].implementation_checkpoint.commit_sha is not an existing commit"
                )
            elif not _git_commit_is_ancestor_of_head(ctx.repo_root, ctx.claimed_commit):
                ctx.checkpoint_evidence_errors.append(
                    f"pr_marker_plan.markers[{ctx.index}].implementation_checkpoint.commit_sha is not an ancestor of HEAD"
                )


def _checkpoint_tasks_bytes(ctx: _ProjectionContext) -> bytes | None:
    """The feature's tasks.md as committed at the checkpoint's implementation commit."""
    if not (ctx.repo_root and isinstance(ctx.feature_dir, str)):
        return None
    return _git_file_at_commit(
        ctx.repo_root, ctx.evidence.get("implementation_checkpoint_sha"), f"{ctx.feature_dir}/tasks.md",
    )


def _freshness_field_checks(
    ctx: _ProjectionContext, freshness: dict[str, Any], expected_checkpoint: Any, expected_current: Any,
) -> dict[str, bool]:
    """Whether the freshness record names the current tasks file and the marker's task-line fingerprints."""
    return {
        "source_fingerprint_contract": freshness.get("source_fingerprint_contract") == "marker-task-lines.v2",
        "source_fingerprint_status": freshness.get("source_fingerprint_status") == "current_marker_scope",
        "tasks_sha_scope": freshness.get("tasks_sha_scope") == "checkpoint_time_whole_file",
        "current_tasks_sha": freshness.get("current_tasks_sha") == ctx.current_tasks_sha,
        "checkpoint_marker_tasks_sha": freshness.get("checkpoint_marker_tasks_sha") == expected_checkpoint,
        "current_marker_tasks_sha": freshness.get("current_marker_tasks_sha") == expected_current,
        "marker_scope_unchanged": expected_checkpoint is not None and expected_checkpoint == expected_current,
    }


def _check_source_fingerprint_freshness(ctx: _ProjectionContext) -> None:
    """Checkpoint evidence must record the marker's current task fingerprint."""
    if not (
        ctx.strict_contract
        and ctx.evidence is not None
        and ctx.current_tasks_text is not None
        and ctx.current_tasks_sha
    ):
        return
    primary_task_values = _string_list(ctx.raw_marker.get("task_ids"))
    folded_task_values = _string_list(ctx.raw_marker.get("folded_polish_task_ids"))
    marker_task_values = (
        [*primary_task_values, *folded_task_values]
        if primary_task_values is not None and folded_task_values is not None
        else None
    )
    marker_task_ids = set(marker_task_values or ())
    evidence_task_values = _string_list(ctx.evidence.get("task_ids"))
    freshness = ctx.checkpoint.get("freshness") if ctx.checkpoint_status == "complete" else ctx.evidence
    freshness = freshness if isinstance(freshness, dict) else {}
    expected_current = (
        _marker_tasks_sha_text(ctx.current_tasks_text, marker_task_ids)
        if marker_task_values is not None
        else None
    )
    checkpoint_tasks_bytes = _checkpoint_tasks_bytes(ctx)
    checkpoint_tasks_text = _decoded_or_none(checkpoint_tasks_bytes or None)
    expected_checkpoint = (
        _marker_tasks_sha_text(checkpoint_tasks_text, marker_task_ids)
        if checkpoint_tasks_text is not None and marker_task_values is not None
        else None
    )
    checkpoint_tasks_sha = _sha256_bytes(checkpoint_tasks_bytes) if checkpoint_tasks_bytes is not None else None
    checks = {
        "marker_id": ctx.evidence.get("marker_id") == ctx.marker_id,
        "task_ids": (
            marker_task_values is not None
            and evidence_task_values is not None
            and set(evidence_task_values) == marker_task_ids
        ),
        "tasks_sha": ctx.evidence.get("tasks_sha") == checkpoint_tasks_sha,
        **_freshness_field_checks(ctx, freshness, expected_checkpoint, expected_current),
    }
    ctx.checkpoint_source_fingerprint_errors.extend(
        f"pr_marker_plan.markers[{ctx.index}] checkpoint {field}"
        for field, passed in checks.items() if not passed
    )


def _check_phase_checkpoint_agreement(ctx: _ProjectionContext) -> None:
    """A phase result is completed exactly when its marker's checkpoint is complete."""
    matching_phases = [
        (phase_name, result)
        for phase_name, result in ctx.phases.items()
        if isinstance(result, dict) and result.get("marker_id") == ctx.marker_id
    ]
    for phase_name, result in matching_phases:
        phase_complete = result.get("status") == "completed"
        checkpoint_complete = ctx.checkpoint_status == "complete"
        if phase_complete != checkpoint_complete:
            ctx.projection_status_errors.append(
                f"marker {ctx.marker_id!r} checkpoint={ctx.checkpoint_status!r} "
                f"does not match phase_results[{phase_name}].status={result.get('status')!r}"
            )


def _check_marker_checkpoint(ctx: _ProjectionContext) -> None:
    """Check one marker's implementation checkpoint and its evidence."""
    if not isinstance(ctx.checkpoint, dict):
        return
    ctx.checkpoint_status = ctx.checkpoint.get("status")
    _check_pending_claims_and_paths(ctx)
    _check_complete_checkpoint_fields(ctx)

    _check_pending_checkpoint_authority(ctx)

    _load_checkpoint_evidence(ctx)
    _check_checkpoint_evidence_body(ctx)
    _check_complete_verification_report(ctx)
    _check_source_fingerprint_freshness(ctx)
    _check_phase_checkpoint_agreement(ctx)


def _check_marker_reviewability_path(ctx: _ProjectionContext) -> None:
    """A strict marker's reviewability evidence path must be a normalized repository file."""
    reviewability = ctx.raw_marker.get("reviewability")
    if ctx.strict_contract and isinstance(reviewability, dict) and "evidence_path" in reviewability:
        evidence_path_value = reviewability.get("evidence_path")
        if not _is_normalized_repo_path(evidence_path_value) or ctx.repo_root and _repo_file(ctx.repo_root, evidence_path_value) is None:
            ctx.marker_plan_status_errors.append(
                f"pr_marker_plan.markers[{ctx.index}].reviewability.evidence_path is not a normalized repository-relative path"
            )


def _repo_path_unusable(ctx: _ProjectionContext, path: Any) -> bool:
    """Whether a strict marker names a path that is not a normalized repository file."""
    return ctx.strict_contract and (
        not _is_normalized_repo_path(path)
        or bool(ctx.repo_root and _repo_file(ctx.repo_root, path) is None)
    )


def _claim_owned_path(ctx: _ProjectionContext, path_kind: str, owned_path: Any, operation: Any) -> None:
    """A path belongs to one marker, except that later markers may modify what an earlier one modified."""
    owner = ctx.file_owners.get(owned_path)
    sequential_modify = (
        path_kind == "file"
        and operation == "MODIFIED"
        and owner is not None
        and owner[1] == "MODIFIED"
        and owner[0] != ctx.marker_id
    )
    if owner is not None and not sequential_modify:
        ctx.marker_plan_status_errors.append(
            f"pr_marker_plan {path_kind} {owned_path!r} is owned by both {owner[0]!r} and {ctx.marker_id!r}"
        )
    else:
        ctx.file_owners[owned_path] = (ctx.marker_id, operation)


def _check_declared_file(ctx: _ProjectionContext, file_index: int, record: Any) -> None:
    fields = record if isinstance(record, dict) else {}
    path, operation, source_path = fields.get("path"), fields.get("operation"), fields.get("source_path")
    prefix = f"pr_marker_plan.markers[{ctx.index}].declared_files[{file_index}]"
    if _repo_path_unusable(ctx, path):
        ctx.marker_plan_status_errors.append(
            f"{prefix}.path is not a normalized repository-relative path"
        )
        return
    owned_paths = [("file", path)]
    if operation == "RENAMED":
        if ctx.strict_contract and (source_path == path or _repo_path_unusable(ctx, source_path)):
            ctx.marker_plan_status_errors.append(
                f"{prefix}.source_path is not a normalized repository-relative rename source"
            )
            return
        owned_paths.append(("rename source", source_path))
    elif source_path is not None:
        ctx.marker_plan_status_errors.append(f"{prefix}.source_path is only valid for RENAMED")
    for path_kind, owned_path in owned_paths:
        _claim_owned_path(ctx, path_kind, owned_path, operation)


def _check_marker_declared_files(ctx: _ProjectionContext) -> None:
    """Declared files must be repository paths that no other marker owns."""
    declared_files = ctx.raw_marker.get("declared_files")
    if isinstance(declared_files, list):
        for file_index, record in enumerate(declared_files):
            _check_declared_file(ctx, file_index, record)


def _check_marker_task_ownership(ctx: _ProjectionContext) -> None:
    """A marker's task ids must be unique and owned by that marker alone."""
    task_values = _string_list(ctx.raw_marker.get("task_ids"))
    folded_values = _string_list(ctx.raw_marker.get("folded_polish_task_ids"))
    if task_values is not None and len(set(task_values)) != len(task_values):
        ctx.marker_plan_status_errors.append(
            f"pr_marker_plan.markers[{ctx.index}].task_ids contains duplicates"
        )
    if folded_values is not None and len(set(folded_values)) != len(folded_values):
        ctx.marker_plan_status_errors.append(
            f"pr_marker_plan.markers[{ctx.index}].folded_polish_task_ids contains duplicates"
        )
    for task_id in (task_values or []) + (folded_values or []):
        owner = ctx.task_owners.get(task_id)
        if owner is not None:
            ctx.marker_plan_status_errors.append(
                f"pr_marker_plan task {task_id!r} is owned by both {owner!r} and {ctx.marker_id!r}"
            )
        else:
            ctx.task_owners[task_id] = ctx.marker_id


# Marker kinds whose id is fixed, with that id.
_FIXED_MARKER_IDS = {"foundation": "foundation", "full_spec": "full-spec", "polish": "polish"}


def _check_story_part(ctx: _ProjectionContext, story_id: int, parent_marker_id: Any) -> None:
    """A user-story part is named us<N>-part<M> and hangs off us<N>."""
    prefix = f"pr_marker_plan.markers[{ctx.index}] user_story_part"
    if not isinstance(ctx.marker_id, str) or not re.fullmatch(fr"us{story_id}-part[0-9]+", ctx.marker_id):
        ctx.marker_plan_status_errors.append(f"{prefix} id does not match story_id {story_id}")
    if parent_marker_id != f"us{story_id}":
        ctx.marker_plan_status_errors.append(f"{prefix} parent does not match story_id {story_id}")


def _check_marker_identity(ctx: _ProjectionContext) -> None:
    """A marker's id, kind, story, and parent must agree."""
    source_boundary = ctx.raw_marker.get("source_boundary")
    story_id = source_boundary.get("story_id") if isinstance(source_boundary, dict) else None
    kind = ctx.raw_marker.get("kind")
    parent_marker_id = ctx.raw_marker.get("parent_marker_id")
    expected_identity: tuple[str, object, object] | None = None
    if kind == "user_story" and isinstance(story_id, int):
        expected_identity = (f"us{story_id}", story_id, None)
    elif kind == "user_story_part" and isinstance(story_id, int):
        _check_story_part(ctx, story_id, parent_marker_id)
    elif isinstance(kind, str) and kind in _FIXED_MARKER_IDS:
        expected_identity = (_FIXED_MARKER_IDS[kind], None, None)
    else:
        ctx.marker_plan_status_errors.append(
            f"pr_marker_plan.markers[{ctx.index}] kind/story_id combination is invalid"
        )
    if expected_identity is not None:
        expected_id, expected_story_id, expected_parent = expected_identity
        if ctx.marker_id != expected_id or story_id != expected_story_id or parent_marker_id != expected_parent:
            ctx.marker_plan_status_errors.append(
                f"pr_marker_plan.markers[{ctx.index}] id, kind, story_id, and parent_marker_id are inconsistent"
            )


def _check_marker_position(ctx: _ProjectionContext) -> None:
    """A marker needs a unique id and a unique contiguous review order."""
    ctx.marker_id = ctx.raw_marker.get("id")
    if not isinstance(ctx.marker_id, str) or not ctx.marker_id:
        ctx.marker_plan_status_errors.append(f"pr_marker_plan.markers[{ctx.index}].id is invalid")
        ctx.marker_id = f"marker[{ctx.index}]"
    elif ctx.marker_id in ctx.seen_marker_ids:
        ctx.marker_plan_status_errors.append(f"pr_marker_plan marker id {ctx.marker_id!r} is duplicated")
    else:
        ctx.seen_marker_ids.add(ctx.marker_id)
    review_order = ctx.raw_marker.get("review_order")
    if not isinstance(review_order, int) or isinstance(review_order, bool) or review_order < 1:
        ctx.marker_plan_status_errors.append(
            f"pr_marker_plan.markers[{ctx.index}].review_order is invalid"
        )
    elif review_order in ctx.seen_review_orders:
        ctx.marker_plan_status_errors.append(
            f"pr_marker_plan review_order {review_order} is duplicated"
        )
    else:
        ctx.seen_review_orders.add(review_order)
    if (
        isinstance(review_order, int)
        and not isinstance(review_order, bool)
        and review_order >= 1
        and review_order != ctx.index + 1
    ):
        ctx.marker_plan_status_errors.append(
            f"pr_marker_plan.markers[{ctx.index}].review_order must equal its "
            f"contiguous marker array position {ctx.index + 1}"
        )


def _decoded_or_none(data: bytes | None) -> str | None:
    try:
        return data.decode("utf-8") if data is not None else None
    except UnicodeDecodeError:
        return None


def _new_projection_context(
    state: dict[str, Any], state_path: Path, expected_head_commit: str | None,
) -> _ProjectionContext:
    """Gather what every projection check reads from the state file and the repository."""
    marker_plan = state.get("pr_marker_plan")
    phase_results = state.get("phase_results")
    repo_root = _repository_root(state_path)
    feature_dir = state.get("feature_dir")
    tasks_bytes = (
        _read_repo_bytes(repo_root, f"{feature_dir}/tasks.md")
        if repo_root is not None and isinstance(feature_dir, str)
        else None
    )
    return _ProjectionContext(
        state=state,
        state_path=state_path,
        expected_head_commit=expected_head_commit,
        marker_plan=marker_plan,
        markers=marker_plan.get("markers") if isinstance(marker_plan, dict) else None,
        plan_status=marker_plan.get("status") if isinstance(marker_plan, dict) else None,
        strict_contract=(
            isinstance(marker_plan, dict) and marker_plan.get("schema_version") == "pr-marker-plan.v2"
        ),
        repo_root=repo_root,
        feature_dir=feature_dir,
        phase_results=phase_results,
        phases=phase_results if isinstance(phase_results, dict) else {},
        current_tasks_text=_decoded_or_none(tasks_bytes),
        current_tasks_sha=_sha256_bytes(tasks_bytes) if tasks_bytes is not None else None,
    )


def _load_marker_plan_schemas(ctx: _ProjectionContext) -> None:
    """Validate the marker plan's shape and load the verification report schema."""
    ctx.marker_plan_status_errors.extend(_marker_plan_version_errors(ctx.marker_plan))
    if not ctx.strict_contract:
        ctx.marker_plan_status_errors.extend(_marker_plan_shape_errors(ctx.marker_plan))
        return
    marker_plan_schema, marker_schema_errors = _canonical_schema(
        MARKER_PLAN_SCHEMA_PATH,
        "pr-marker-plan",
        repo_root=ctx.repo_root,
        expected_head_commit=ctx.expected_head_commit,
    )
    ctx.marker_plan_status_errors.extend(marker_schema_errors)
    if marker_plan_schema is not None:
        ctx.marker_plan_status_errors.extend(_marker_plan_shape_errors(ctx.marker_plan, marker_plan_schema))
    ctx.verification_report_schema, verification_schema_errors = _canonical_schema(
        VERIFICATION_REPORT_SCHEMA_PATH,
        "verification report",
        repo_root=ctx.repo_root,
        expected_head_commit=ctx.expected_head_commit,
    )
    ctx.checkpoint_evidence_errors.extend(verification_schema_errors)


# Marker-plan statuses that stop the run, with the warning code and severities that must explain them.
_DIAGNOSTIC_WARNINGS = {
    "stale": ("MARKER_PLAN_STALE", {"warning", "error"}),
    "invalid": ("MARKER_PLAN_INVALID", {"error"}),
}


def _check_plan_status_diagnostics(ctx: _ProjectionContext) -> None:
    """A stale or invalid plan is a correctness stop, and a strict plan must carry the matching warning."""
    if ctx.plan_status not in _DIAGNOSTIC_WARNINGS:
        return
    ctx.marker_plan_status_errors.append(f"pr_marker_plan.status {ctx.plan_status} is a correctness stop")
    if not ctx.strict_contract:
        return
    code, severities = _DIAGNOSTIC_WARNINGS[ctx.plan_status]
    warnings = ctx.marker_plan.get("warnings")
    if not isinstance(warnings, list) or not any(
        isinstance(warning, dict)
        and warning.get("code") == code
        and warning.get("severity") in severities
        for warning in warnings
    ):
        ctx.marker_plan_status_errors.append(
            f"pr_marker_plan.status {ctx.plan_status} requires diagnostic warning {code}"
        )


def _load_checkpoint_schema(ctx: _ProjectionContext) -> None:
    """Load the checkpoint evidence schema from the authorized head, else the plugin's own contract."""
    if not (ctx.strict_contract and ctx.repo_root):
        return
    if not _is_normalized_repo_path(ctx.feature_dir):
        ctx.checkpoint_evidence_errors.append(
            "pr-marker-plan.v2 checkpoint evidence requires a normalized feature_dir"
        )
        return
    schema_ref = f"{ctx.feature_dir}/contracts/marker-checkpoint.schema.json"
    committed = _git_file_at_commit(ctx.repo_root, ctx.expected_head_commit, schema_ref)
    worktree = _read_repo_bytes(ctx.repo_root, schema_ref)
    if committed is None:
        # No feature-local schema: validate against the plugin's own contract.
        ctx.checkpoint_evidence_schema, schema_errors = _canonical_schema(
            MARKER_CHECKPOINT_SCHEMA_PATH,
            "marker-checkpoint",
            repo_root=ctx.repo_root,
            expected_head_commit=ctx.expected_head_commit,
        )
        ctx.checkpoint_evidence_errors.extend(schema_errors)
        if worktree is not None:
            ctx.checkpoint_file_errors.append(
                "feature-local checkpoint evidence schema exists in the worktree but not "
                "at the authorized PR head; commit it or remove it to use the plugin schema"
            )
        return
    if worktree != committed:
        ctx.checkpoint_file_errors.append("checkpoint evidence schema differs from the authorized PR head")
    ctx.checkpoint_evidence_schema = _load_json_bytes(committed)
    if ctx.checkpoint_evidence_schema is None:
        ctx.checkpoint_evidence_errors.append(
            "checkpoint evidence schema at the authorized PR head is malformed"
        )


def _check_phase_marker_binding(ctx: _ProjectionContext, phase_name: str, phase_marker_id: Any) -> None:
    """An implement phase must name exactly one marker, and the plan must declare it."""
    if not ctx.strict_contract or not phase_name.startswith("Phase 7: Implement"):
        return
    declared_marker_ids = {
        marker.get("id")
        for marker in ctx.markers or []
        if isinstance(marker, dict) and isinstance(marker.get("id"), str) and marker["id"]
    }
    if not isinstance(phase_marker_id, str) or not phase_marker_id:
        ctx.marker_plan_status_errors.append(
            f"phase_results[{phase_name}] must declare exactly one marker_id"
        )
    elif phase_marker_id not in declared_marker_ids:
        ctx.marker_plan_status_errors.append(
            f"phase_results[{phase_name}] marker_id {phase_marker_id!r} is not declared by pr_marker_plan"
        )


def _check_phase_plan_agreement(
    ctx: _ProjectionContext, steps: list[PlanStep], phase_name: str, result_status: Any,
) -> None:
    """A phase result's status must match its plan step."""
    matching_steps = [
        step for step in steps if step.step == phase_name or step.step.startswith(f"{phase_name} (")
    ]
    if result_status not in {"completed", "in_progress", "pending", "checkpointing"} or not matching_steps:
        return
    expected_plan_status = "completed" if result_status == "completed" else result_status
    if matching_steps[0].status != expected_plan_status:
        ctx.projection_status_errors.append(
            f"plan[{matching_steps[0].step}]={matching_steps[0].status!r} "
            f"does not match phase_results[{phase_name}].status={result_status!r}"
        )


def _check_phase_result(
    ctx: _ProjectionContext, steps: list[PlanStep], phase_name: str, raw_result: dict[str, Any],
) -> None:
    """One phase result must bind to its marker, agree with the plan step, and carry no pending values once done."""
    phase_marker_id = raw_result.get("marker_id")
    if isinstance(phase_marker_id, str) and phase_marker_id:
        ctx.phases_by_marker.setdefault(phase_marker_id, []).append((phase_name, raw_result))
    _check_phase_marker_binding(ctx, phase_name, phase_marker_id)
    result_status = raw_result.get("status")
    _check_phase_plan_agreement(ctx, steps, phase_name, result_status)
    if result_status == "completed":
        ctx.completed_phase_pending_fields.extend(
            _pending_value_paths(raw_result, f"phase_results.{phase_name}")
        )


def _check_phase_results(ctx: _ProjectionContext, steps: list[PlanStep]) -> None:
    for phase_name, raw_result in ctx.phases.items():
        if isinstance(phase_name, str) and isinstance(raw_result, dict):
            _check_phase_result(ctx, steps, phase_name, raw_result)


def _check_marker(ctx: _ProjectionContext) -> None:
    """Every check one marker of the plan must pass."""
    _check_marker_position(ctx)
    _check_marker_identity(ctx)
    _check_marker_task_ownership(ctx)
    _check_marker_declared_files(ctx)
    _check_marker_reviewability_path(ctx)
    ctx.checkpoint = ctx.raw_marker.get("implementation_checkpoint")
    _check_marker_checkpoint(ctx)
    _check_marker_emission(ctx)


def _check_markers(ctx: _ProjectionContext) -> None:
    if not isinstance(ctx.markers, list):
        return
    if ctx.strict_contract:
        ctx.marker_plan_status_errors.extend(_timestamp_errors(ctx.marker_plan, "pr_marker_plan"))
    for position, marker in enumerate(ctx.markers):
        ctx.index, ctx.raw_marker = position, marker
        if isinstance(marker, dict):
            _check_marker(ctx)
    _check_plan_status_constraints(ctx)


def validate_projection_integrity(
    state: dict[str, Any],
    steps: list[PlanStep],
    state_path: Path,
    *,
    expected_head_commit: str | None = None,
) -> dict[str, list[str]]:
    ctx = _new_projection_context(state, state_path, expected_head_commit)
    _load_marker_plan_schemas(ctx)
    _check_plan_status_diagnostics(ctx)
    _load_checkpoint_schema(ctx)
    _check_phase_results(ctx, steps)
    _check_markers(ctx)
    return {
        "completed_phase_pending_fields": ctx.completed_phase_pending_fields,
        "projection_status_errors": ctx.projection_status_errors,
        "checkpoint_evidence_errors": ctx.checkpoint_evidence_errors,
        "checkpoint_source_fingerprint_errors": ctx.checkpoint_source_fingerprint_errors,
        "checkpoint_file_errors": ctx.checkpoint_file_errors,
        "emission_mapping_errors": ctx.emission_mapping_errors,
        "marker_plan_status_errors": ctx.marker_plan_status_errors,
    }


def _markdown_without_comments(text: str) -> str:
    """Blank HTML comment spans while preserving line numbering."""
    return HTML_COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def _workflow_table_rows(lines: list[str], start: int) -> list[int]:
    rows: list[int] = []
    for index in range(start, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            rows.append(index)
        elif rows:
            break
        elif stripped.startswith("#"):
            # A section with no table of its own must not adopt a later one.
            break
    return rows


def workflow_overview_rows(lines: list[str]) -> list[int]:
    for index, line in enumerate(lines):
        if line.strip() == WORKFLOW_OVERVIEW_HEADING:
            return _workflow_table_rows(lines, index + 1)
    return []


def workflow_criteria_rows(lines: list[str]) -> set[int]:
    rows: set[int] = set()
    for index, line in enumerate(lines):
        if line.strip().startswith(WORKFLOW_CRITERIA_HEADING_PREFIX):
            rows.update(_workflow_table_rows(lines, index + 1))
    return rows


def gate_record_ids(line: str) -> set[str]:
    unprefixed = GATE_LINE_PREFIX_RE.sub("", line)
    return {
        match.group("gate")
        for pattern in GATE_RECORD_PATTERNS
        for match in pattern.finditer(unprefixed)
    }


def workflow_status_evidence_errors(text: str) -> list[str]:
    """Report Workflow Overview rows contradicted by the file's own gate records.

    Fenced blocks are deliberately NOT stripped: runner gate output is routinely
    recorded as fenced JSON, so it is evidence rather than illustration. HTML
    comments are blanked so a commented-out example cannot become evidence.
    """
    lines = _markdown_without_comments(text).splitlines()
    rows = workflow_overview_rows(lines)
    if len(rows) < 3:
        return ["workflow has no parseable Workflow Overview table"]
    excluded = set(rows) | workflow_criteria_rows(lines)
    records: dict[str, int] = {}
    for index, line in enumerate(lines):
        if index in excluded:
            continue
        for gate in gate_record_ids(line):
            records.setdefault(gate, index + 1)
    errors: list[str] = []
    first_open: tuple[int, str, str] | None = None
    for index in rows[2:]:
        stripped = lines[index].strip()
        cells = [cell.strip() for cell in stripped[1:-1].split("|")]
        if len(cells) < 3:
            continue
        phase, status = cells[0], cells[2]
        number = index + 1
        if status not in WORKFLOW_STATUS_VALUES:
            errors.append(
                f"workflow status row {number} for {phase!r} uses unsupported status {status!r}"
            )
        gate = WORKFLOW_PHASE_GATE_IDS.get(phase)
        if gate is not None and gate in records and status not in WORKFLOW_TERMINAL_STATUSES:
            errors.append(
                f"workflow status row {number} for {phase!r} reads {status!r} but the workflow"
                f" records a G{gate} PASS at line {records[gate]}"
            )
        if status in WORKFLOW_TERMINAL_STATUSES:
            if first_open is not None:
                errors.append(
                    f"workflow status row {number} for {phase!r} reads {status!r} while earlier"
                    f" row {first_open[0]} for {first_open[1]!r} still reads {first_open[2]!r}"
                )
        elif first_open is None and phase not in WORKFLOW_ADVISORY_PHASES:
            first_open = (number, phase, status)
    return errors


def validate_workflow_status_evidence(text: str) -> dict[str, list[str]]:
    return {"workflow_status_evidence_errors": workflow_status_evidence_errors(text)}


def validate_state_status(state: dict[str, Any]) -> dict[str, list[str]]:
    """Validate the top-level autopilot run status against its canonical schema.

    The check closes the status vocabulary; it does not mandate the field, so a
    legacy state that predates ``status`` still validates. When the canonical
    schema is not readable beside this script -- which happens whenever the
    validator is copied out of the repository -- the check is skipped rather
    than failed, so an extracted copy cannot manufacture a false violation.
    """
    if not STATE_STATUS_SCHEMA_PATH.is_file():
        return {"state_status_errors": []}
    schema, errors = _canonical_schema(STATE_STATUS_SCHEMA_PATH, "autopilot-state status")
    if schema is None:
        return {"state_status_errors": errors}
    errors.extend(_json_schema_errors(state, schema, schema, "autopilot_state"))
    return {"state_status_errors": errors}


def _state_private_value_reason(value: str) -> str | None:
    if STATE_HOME_PATH_PATTERN.search(value) or STATE_HYPHENATED_HOME_PATH_PATTERN.search(value):
        return "an absolute home path"
    if STATE_UUID_PATTERN.search(value):
        return "a raw UUID"
    return None


def _private_value_errors(
    root_location: str,
    root: object,
    *,
    private_keys: frozenset[str] = frozenset(),
    remedy: str = "",
) -> list[str]:
    """Name every private key or value under ``root`` by its location, never echoing it."""
    errors: list[str] = []
    pending: list[tuple[str, object]] = [(root_location, root)]
    while pending:
        location, value = pending.pop()
        if isinstance(value, dict):
            for key, child in value.items():
                child_location = f"{location}.{key}"
                if key in private_keys:
                    errors.append(
                        f"{child_location} stores a raw runner argv; remove this key, keep only "
                        + "decision fields, and rerun this guard"
                    )
                    continue
                reason = _state_private_value_reason(key)
                if reason is not None:
                    key_digest = "sha256:" + hashlib.sha256(key.encode("utf-8")).hexdigest()
                    errors.append(
                        f"{location} has a key holding {reason} (key {key_digest}); replace that key "
                        + f"with {key_digest}{remedy}, and rerun this guard"
                    )
                    continue
                pending.append((child_location, child))
        elif isinstance(value, list):
            pending.extend((f"{location}[{index}]", item) for index, item in enumerate(value))
        elif isinstance(value, str):
            reason = _state_private_value_reason(value)
            if reason is not None:
                errors.append(
                    f"{location} holds {reason}; replace the value with sha256: plus the hex "
                    + f"SHA-256 of the value{remedy}, and rerun this guard"
                )
    return errors


def state_privacy_errors(state: object) -> dict[str, list[str]]:
    """Reject private values in the committed autopilot state file.

    The state stores decision fields such as ``stage``, ``source``, ``basis``,
    and ``planning_complete``. It never stores a raw runner envelope, an
    ``argv`` key, an absolute home path, or an external task or session UUID.
    Errors name the JSON location and the in-place remedy (#800), and never
    echo the value. A non-object root fails rather than passing on nothing.
    """
    if not isinstance(state, dict):
        return {"state_privacy_errors": ["autopilot_state must be a JSON object"]}
    errors = _private_value_errors("autopilot_state", state, private_keys=STATE_PRIVATE_KEYS)
    return {"state_privacy_errors": sorted(errors)}


def marker_evidence_privacy_errors(state: object, state_path: Path) -> dict[str, list[str]]:
    """Reject private values in committed marker checkpoint and verification evidence (#819).

    Each marker's ``implementation_checkpoint.evidence_path`` and
    ``verification_evidence_path`` name committed JSON records. They cite an
    external task, session, thread, or event id only as ``sha256:<digest>``,
    and hold no absolute home path. Errors name the file and JSON location
    with the digest remedy, and never echo the value. A record that is not
    JSON is scanned as text. A file not yet written, such as a pending
    marker's, is skipped here; the checkpoint checks own its existence.
    """
    marker_plan = state.get("pr_marker_plan") if isinstance(state, dict) else None
    markers = marker_plan.get("markers") if isinstance(marker_plan, dict) else None
    repo_root = _repository_root(state_path)
    if not isinstance(markers, list) or repo_root is None:
        return {"marker_evidence_privacy_errors": []}
    refs: list[str] = []
    for marker in markers:
        checkpoint = marker.get("implementation_checkpoint") if isinstance(marker, dict) else None
        if not isinstance(checkpoint, dict):
            continue
        for field in ("evidence_path", "verification_evidence_path"):
            ref = checkpoint.get(field)
            if isinstance(ref, str) and ref not in refs:
                refs.append(ref)
    remedy = " or omit it"
    errors: list[str] = []
    for ref in refs:
        content = _read_repo_bytes(repo_root, ref)
        if content is None:
            continue
        try:
            evidence = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            reason = _state_private_value_reason(content.decode("utf-8", errors="replace"))
            if reason is not None:
                errors.append(
                    f"{ref} holds {reason}; write each such value as sha256: plus the hex SHA-256 "
                    + f"of the value{remedy}, and rerun this guard"
                )
            continue
        errors.extend(_private_value_errors(f"{ref} $", evidence, remedy=remedy))
    return {"marker_evidence_privacy_errors": sorted(errors)}


def _canonical_json_sha256(value: object) -> str | None:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (RecursionError, TypeError, ValueError):
        return None
    return _sha256_bytes(encoded)


def _autonomy_boundary_required(
    state: dict[str, Any],
    require_boundary: bool,
) -> bool:
    if not require_boundary:
        return False
    stage = state.get("stage")
    if stage == "implement":
        return True
    plan = state.get("plan")
    if not isinstance(plan, list):
        return False
    phase_65_started = any(
        isinstance(item, dict)
        and isinstance(item.get("step"), str)
        and item["step"].startswith("Phase 6.5:")
        and item.get("status") in {"in_progress", "completed"}
        for item in plan
    )
    phase_7_started = any(
        isinstance(item, dict)
        and isinstance(item.get("step"), str)
        and item["step"].startswith("Phase 7:")
        and item.get("status") in {"in_progress", "completed"}
        for item in plan
    )
    return phase_7_started or (stage in {"plan", "full"} and phase_65_started)


AUTONOMY_RECEIPT_VERSION = "autonomy-boundary-receipt.v1"
AUTONOMY_LEGACY_RECEIPT_KEY = "autonomy_boundary_private_receipt"
AUTONOMY_EXECUTION_FIELDS = (
    "execution_environment",
    "sandbox_mode",
    "approval_reviewer",
    "writable_roots",
)
AUTONOMY_ACTION_FIELDS = (
    "category",
    "command_or_tool",
    "target",
    "effect",
    "execution_boundary_sha256",
)


def _autonomy_scope(record: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {key: record.get(key) for key in fields}


def _autonomy_file_errors(
    label: str,
    record: object,
    repo_root: Path,
) -> tuple[list[str], str | None]:
    if not isinstance(record, dict):
        return [], None
    errors: list[str] = []
    raw_path = record.get("path")
    expected_name = "plan.md" if label == "plan_md" else "tasks.md"
    parent: str | None = None
    if not isinstance(raw_path, str) or PurePosixPath(raw_path).name != expected_name:
        errors.append(f"autonomy boundary {label} path must name {expected_name}")
    elif _is_normalized_repo_path(raw_path):
        parent = PurePosixPath(raw_path).parent.as_posix()
    content = _read_repo_bytes(repo_root, raw_path)
    if content is None:
        errors.append(f"autonomy boundary {label} path is missing or unsafe")
        return errors, parent
    if record.get("size_bytes") != len(content):
        errors.append(f"autonomy boundary {label} size_bytes is stale")
    if record.get("sha256") not in _autonomy_file_digests(label, content):
        errors.append(f"autonomy boundary {label} sha256 is stale")
    return errors, parent


def _autonomy_file_digests(label: str, content: bytes) -> set[str]:
    """Digests that keep a planning fingerprint current.

    plan.md binds its raw bytes. tasks.md also accepts the digest of its task
    definitions, the checkbox-insensitive text task fingerprints use, so marking a
    task complete never stales the boundary. When the runner is not importable or
    the file is not UTF-8, only the raw digest counts, so the check fails closed.
    """
    digests = {_sha256_bytes(content)}
    if label != "tasks_md":
        return digests
    plugin_root = str(Path(__file__).resolve().parents[3])
    if plugin_root not in sys.path:
        sys.path.insert(0, plugin_root)
    try:
        from speckit_pro_runner.task_execution import task_definitions  # noqa: PLC0415

        digests.add(_sha256_bytes(task_definitions(content.decode("utf-8")).encode("utf-8")))
    except (ImportError, UnicodeDecodeError):
        # Fail closed: without the runner or valid UTF-8, only the raw digest counts.
        return digests
    return digests


def _autonomy_planning_errors(
    boundary: dict[str, Any],
    repo_root: Path | None,
) -> list[str]:
    if repo_root is None:
        return ["autonomy boundary planning fingerprints have no resolvable repository root"]
    fingerprints = boundary.get("planning_fingerprints")
    if not isinstance(fingerprints, dict):
        return []
    errors: list[str] = []
    parents: list[str] = []
    for label in ("plan_md", "tasks_md"):
        file_errors, parent = _autonomy_file_errors(label, fingerprints.get(label), repo_root)
        errors.extend(file_errors)
        if parent is not None:
            parents.append(parent)
    if len(parents) == 2 and len(set(parents)) != 1:
        errors.append("autonomy boundary plan.md and tasks.md must share one feature directory")
    return errors


def _autonomy_execution_errors(
    boundary: dict[str, Any],
    receipt: bool = False,
) -> tuple[list[str], object]:
    execution = boundary.get("execution_boundary")
    if not isinstance(execution, dict):
        return [], None
    if receipt:
        # The public receipt omits the roots, so its digest cannot be recomputed
        # from the record itself. The recorded digest is replayed against the
        # current execution boundary instead, which is the check that matters.
        recorded = execution.get("sha256")
        if isinstance(recorded, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", recorded):
            return [], recorded
        return [], None
    errors: list[str] = []
    roots = execution.get("writable_roots")
    roots_are_strings = isinstance(roots, list) and all(
        isinstance(root, str) for root in roots
    )
    if roots_are_strings and roots != sorted(roots):
        errors.append("autonomy boundary writable_roots must use deterministic sorted order")
    if isinstance(roots, list) and any(
        not isinstance(root, str)
        or not (root.startswith("/") or WINDOWS_ABSOLUTE_PATH_RE.match(root))
        for root in roots
    ):
        errors.append("autonomy boundary writable_roots must contain absolute paths")
    execution_sha = _canonical_json_sha256(_autonomy_scope(execution, AUTONOMY_EXECUTION_FIELDS))
    if execution_sha is None:
        errors.append(
            "autonomy boundary execution_boundary scope cannot be canonicalized/serialized for sha256"
        )
    elif execution.get("sha256") != execution_sha:
        errors.append("autonomy boundary execution_boundary sha256 does not match its current scope")
    return errors, execution_sha


def _autonomy_current_execution_errors(
    current: object,
    recorded_sha: object,
    required: bool,
) -> list[str]:
    if current is None:
        return ["current execution boundary is unavailable"] if required else []
    if not isinstance(current, dict):
        return ["current execution boundary must be an object"]
    values = _autonomy_scope(current, AUTONOMY_EXECUTION_FIELDS)
    roots = values.get("writable_roots")
    strings = (
        values.get("execution_environment"),
        values.get("sandbox_mode"),
        values.get("approval_reviewer"),
    )
    if any(not isinstance(value, str) or not value for value in strings):
        return ["current execution boundary is incomplete or malformed"]
    if (
        not isinstance(roots, list)
        or not roots
        or any(
            not isinstance(root, str)
            or not (root.startswith("/") or WINDOWS_ABSOLUTE_PATH_RE.match(root))
            for root in roots
        )
        or len(roots) != len(set(roots))
    ):
        return ["current execution boundary writable_roots are incomplete or malformed"]
    values["writable_roots"] = sorted(roots)
    if _canonical_json_sha256(values) != recorded_sha:
        return ["current execution boundary does not match the persisted execution boundary"]
    return []


AUTONOMY_RUN_ID_RE = re.compile(r"[0-9a-f]{32}")


def _read_private_record_bytes(path: Path) -> bytes | None:
    """Read a regular, non-symlink private record file, or None."""
    try:
        # O_NOFOLLOW closes the race where it exists; the lstat check keeps the
        # symlink refusal on platforms that lack it.
        if stat.S_ISLNK(os.lstat(path).st_mode):
            return None
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError:
        return None
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_REPO_FILE_BYTES:
            return None
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            content = handle.read(MAX_REPO_FILE_BYTES + 1)
    except OSError:
        return None
    finally:
        os.close(descriptor)
    return content if len(content) <= MAX_REPO_FILE_BYTES else None


def _autonomy_private_record_errors(
    state: dict[str, Any],
    boundary: dict[str, Any],
    repo_root: Path | None,
) -> list[str]:
    """Check the private record behind a receipt still hashes to its digest.

    The record lives at `<git-common-dir>/speckit-pro/autonomy-boundary/<run-id>.json`,
    where `<run-id>` is the execution-control ledger's run id mirrored in state.
    Errors never name the path or the run id, which are machine-local.
    """
    control = state.get("execution_control")
    run_id = control.get("run_id") if isinstance(control, dict) else None
    if not isinstance(run_id, str) or not AUTONOMY_RUN_ID_RE.fullmatch(run_id):
        return [
            "autonomy boundary private record cannot be located: "
            "autopilot_state.execution_control.run_id is missing or malformed"
        ]
    common_dir = _git_common_dir(repo_root) if repo_root is not None else None
    if common_dir is None:
        return [
            "autonomy boundary private record cannot be located: "
            "the git common directory is unavailable"
        ]
    path = common_dir / "speckit-pro" / "autonomy-boundary" / f"{run_id}.json"
    content = _read_private_record_bytes(path)
    if content is None:
        return ["autonomy boundary private record is missing or unreadable"]
    try:
        record = _strict_json_loads(content)
    except (RecursionError, ValueError):
        return ["autonomy boundary private record is not valid JSON"]
    digest = _canonical_json_sha256(record)
    if digest is None or digest != boundary.get("private_record_sha256"):
        return ["autonomy boundary private record does not match private_record_sha256"]
    return []


def _autonomy_authorization_errors(
    prefix: str,
    authorization: object,
    disposition: object,
    scope_sha: object,
    receipt: bool = False,
) -> list[str]:
    if not isinstance(authorization, dict):
        return []
    errors: list[str] = []
    status = authorization.get("status")
    if authorization.get("scope_sha256") != scope_sha:
        errors.append(f"{prefix}.authorization.scope_sha256 does not match its action scope")
    allowed = {
        "ready": {"explicit_user"},
        "rerouted": {"not_required"},
        "operator_action_required": {"missing", "revoked"},
    }
    if disposition in allowed and status not in allowed[disposition]:
        errors.append(f"{prefix}.authorization status cannot support disposition {disposition!r}")
    revocation = authorization.get("revocation_evidence")
    # A receipt keeps revocation evidence in the private record only.
    if status == "revoked" and not receipt and not (
        isinstance(revocation, str) and revocation.strip()
    ):
        errors.append(f"{prefix}.authorization requires revocation_evidence")
    if status != "revoked" and revocation is not None:
        errors.append(f"{prefix}.authorization has unexpected revocation_evidence")
    return errors


def _autonomy_action_errors(
    action: dict[str, Any],
    index: int,
    execution_sha: object,
    receipt: bool = False,
) -> list[str]:
    prefix = f"autopilot_state.autonomy_boundary.actions[{index}]"
    errors: list[str] = []
    if execution_sha is not None and action.get("execution_boundary_sha256") != execution_sha:
        errors.append(f"{prefix}.execution_boundary_sha256 is stale")
    if receipt:
        # The scope fields stay private; the receipt binds authorization to the
        # recorded scope digest instead of recomputing it.
        scope_sha = action.get("scope_sha256")
    else:
        scope_sha = _canonical_json_sha256(_autonomy_scope(action, AUTONOMY_ACTION_FIELDS))
        if action.get("scope_sha256") != scope_sha:
            errors.append(f"{prefix}.scope_sha256 does not match its action scope")
    errors.extend(
        _autonomy_authorization_errors(
            prefix,
            action.get("authorization"),
            action.get("disposition"),
            scope_sha,
            receipt,
        )
    )
    return errors


def _autonomy_actions_errors(
    boundary: dict[str, Any],
    execution_sha: object,
    receipt: bool = False,
) -> list[str]:
    actions = boundary.get("actions")
    if not isinstance(actions, list):
        return []
    errors: list[str] = []
    records = [action for action in actions if isinstance(action, dict)]
    for index, action in enumerate(actions):
        if isinstance(action, dict):
            errors.extend(_autonomy_action_errors(action, index, execution_sha, receipt))
    action_ids = [action.get("action_id") for action in records]
    comparable = [action_id for action_id in action_ids if isinstance(action_id, str)]
    if len(comparable) != len(set(comparable)):
        errors.append("autonomy boundary action_id values must be unique")
    dispositions = [action.get("disposition") for action in records]
    expected = "operator_action_required" if "operator_action_required" in dispositions else "ready"
    if boundary.get("status") != expected:
        errors.append("autonomy boundary status does not match its ordered action dispositions")
    return errors


def validate_autonomy_boundary(
    state: dict[str, Any],
    repo_root: Path | None,
    *,
    current_execution_boundary: dict[str, Any] | None = None,
    require_boundary: bool = False,
) -> dict[str, list[str]]:
    """Validate the durable Phase 6.5 execution and authorization boundary."""
    boundary_required = _autonomy_boundary_required(state, require_boundary)
    boundary = state.get("autonomy_boundary")
    if boundary is None:
        errors = []
        if boundary_required and AUTONOMY_LEGACY_RECEIPT_KEY in state:
            errors.append(
                f"autopilot_state.{AUTONOMY_LEGACY_RECEIPT_KEY} has no execution-boundary "
                "digest to replay against the current execution boundary; migrate it to an "
                f"{AUTONOMY_RECEIPT_VERSION} autopilot_state.autonomy_boundary projected "
                "from the private record before this active run can reach Phase 7"
            )
        elif boundary_required:
            errors.append(
                "autopilot_state.autonomy_boundary is required before this active run can reach Phase 7"
            )
        return {"autonomy_boundary_errors": errors}
    if not isinstance(boundary, dict):
        return {"autonomy_boundary_errors": ["autopilot_state.autonomy_boundary must be an object"]}
    if not AUTONOMY_BOUNDARY_SCHEMA_PATH.is_file():
        return {"autonomy_boundary_errors": ["autonomy boundary schema is unavailable"]}
    schema, errors = _canonical_schema(AUTONOMY_BOUNDARY_SCHEMA_PATH, "autonomy boundary")
    if schema is None:
        return {"autonomy_boundary_errors": errors}
    errors.extend(_json_schema_errors(boundary, schema, schema, "autopilot_state.autonomy_boundary"))
    errors.extend(_autonomy_planning_errors(boundary, repo_root))
    receipt = boundary.get("schema_version") == AUTONOMY_RECEIPT_VERSION
    execution_errors, execution_sha = _autonomy_execution_errors(boundary, receipt)
    errors.extend(execution_errors)
    if receipt and boundary_required:
        errors.extend(_autonomy_private_record_errors(state, boundary, repo_root))
    if execution_sha is not None:
        errors.extend(
            _autonomy_current_execution_errors(
                current_execution_boundary,
                execution_sha,
                boundary_required,
            )
        )
    errors.extend(_autonomy_actions_errors(boundary, execution_sha, receipt))
    return {"autonomy_boundary_errors": errors}


def _stage_reader():
    """The shared resolver's `Stage` reader, or None when it is not importable.

    The plugin root is ``parents[3]`` from this script in both the repository and
    an installed tree, so one expression works in both layouts. A package import
    is required rather than file-location loading because the resolver module
    uses a relative import that only resolves inside its package.
    """
    plugin_root = str(Path(__file__).resolve().parents[3])
    if plugin_root not in sys.path:
        sys.path.insert(0, plugin_root)
    try:
        from speckit_pro_runner.helpers.read_only import (  # noqa: PLC0415
            AUTOPILOT_STAGES,
            HTML_COMMENT_RE as STAGE_HTML_COMMENT_RE,
            workflow_recorded_stage,
        )
    except ImportError:
        return None
    return AUTOPILOT_STAGES, STAGE_HTML_COMMENT_RE, workflow_recorded_stage


def stage_mirror_errors(workflow_text: str, state: dict[str, Any]) -> dict[str, list[str]]:
    """Report a state `stage` mirror that disagrees with the workflow file.

    The workflow file is the authoritative durable store; `autopilot-state.json`
    carries a mirror for the active run only, and on disagreement the workflow
    file wins and the mirror is repaired from it. Absence on either side is
    legal, so only a genuine two-sided disagreement is reported.

    When the shared resolver is not importable -- which happens whenever this
    validator is copied out of a tree that ships it -- the check is skipped
    rather than failed, the same posture ``validate_state_status`` already takes
    so an extracted copy cannot manufacture a false violation.
    """
    reader = _stage_reader()
    if reader is None:
        return {"stage_mirror_errors": []}
    stages, comment_re, recorded_stage = reader
    lines = comment_re.sub("", workflow_text).splitlines()
    authority = recorded_stage(lines)
    mirror = state.get("stage")
    if not isinstance(mirror, str) or not mirror:
        return {"stage_mirror_errors": []}
    errors: list[str] = []
    if mirror not in stages:
        errors.append(
            f"autopilot state stage {mirror!r} is outside the closed stage"
            f" vocabulary {list(stages)}"
        )
    if authority is not None and mirror != authority:
        errors.append(
            f"autopilot state stage {mirror!r} does not match the workflow file"
            f" Stage authority {authority!r}; repair the mirror from the workflow file"
        )
    return {"stage_mirror_errors": errors}


def formal_checkpoint_errors(workflow: Path, workflow_text: str, state: dict[str, Any], steps: list[PlanStep]) -> dict[str, list[str]]:
    plugin_root = str(Path(__file__).resolve().parents[3])
    if plugin_root not in sys.path:
        sys.path.insert(0, plugin_root)
    try:
        from speckit_pro_runner.formal.lifecycle import coverage_errors
        from speckit_pro_runner.formal.selection import selection_from_workflow

        selection = selection_from_workflow(workflow_text)
        if selection["status"] != "enabled":
            return {"formal_checkpoint_errors": []}
        root = _repository_root(workflow)
        if root is None:
            return {"formal_checkpoint_errors": ["Cannot resolve WORKFLOW_ROOT for selected formal evidence"]}
        relative = workflow.resolve().relative_to(root).as_posix()
        if selection_from_workflow(read_text(workflow)) != selection:
            return {"formal_checkpoint_errors": ["Selected formal authority differs from the local workflow"]}
        errors = coverage_errors(root, relative, state, [(step.step, step.status) for step in steps])
    except ImportError:
        errors = ["Selected formal checkpoint support is unavailable"] if "## Formal Methods" in workflow_text else []
    except (ValueError, KeyError, TypeError, OSError) as exc:
        errors = [f"Invalid selected formal checkpoint: {exc}"]
    return {"formal_checkpoint_errors": errors}


def artifact_review_errors(workflow: Path, workflow_text: str) -> dict[str, list[str]]:
    errors: list[str] = []
    if "## Artifact Review Handoff" not in workflow_text:
        return {"artifact_review_errors": errors}
    plugin_root = str(Path(__file__).resolve().parents[3])
    if plugin_root not in sys.path:
        sys.path.insert(0, plugin_root)
    try:
        from speckit_pro_runner.artifact_review import record_from_workflow, review_handoff
        from speckit_pro_runner.helpers.read_only import trusted_bytes

        if record_from_workflow(workflow_text) is not None:
            root = _repository_root(workflow)
            if root is None:
                raise ValueError("Cannot resolve WORKFLOW_ROOT for artifact review evidence")
            review_handoff(workflow_text, root, trusted_bytes)
    except (ImportError, ValueError, KeyError, TypeError, OSError) as exc:
        errors.append(f"Invalid artifact review evidence: {exc}")
    return {"artifact_review_errors": errors}


def _repair_request(problems: dict[str, Any]) -> dict[str, Any] | None:
    """The orchestrator owns the workflow and state files, so a failure is its to repair, not a stop."""
    failing = sorted(key for key, values in problems.items() if values)
    return {"owner": "orchestrator", "failing_keys": failing, "retry": "validate-autopilot-phase-coverage"} if failing else None


def build_report(
    workflow: Path, state: Path, *, authority: ReportAuthority | None = None,
) -> dict[str, Any]:
    authority = authority or ReportAuthority()
    state_data = load_state(state)
    workflow_text, workflow_checkpoint_errors, workflow_authority_errors = _authorized_workflow_text(
        workflow, state, state_data, authority.expected_head_commit,
    )
    plan_steps = extract_plan_steps(state_data)

    workflow_result = validate_workflow(workflow_text)
    workflow_checkpoint_result = validate_workflow_checkpoint_bindings(
        workflow_text, state_data,
    )
    workflow_checkpoint_result["workflow_checkpoint_errors"].extend(workflow_checkpoint_errors)
    state_result = validate_state(plan_steps)
    status_result = validate_state_status(state_data)
    privacy_result = state_privacy_errors(state_data)
    marker_privacy_result = marker_evidence_privacy_errors(state_data, state)
    autonomy_result = validate_autonomy_boundary(
        state_data, _repository_root(workflow),
        current_execution_boundary=authority.current_execution_boundary,
        require_boundary=authority.require_autonomy_boundary,
    )
    stage_result = stage_mirror_errors(workflow_text, state_data)
    formal_result = formal_checkpoint_errors(workflow, workflow_text, state_data, plan_steps)
    artifact_result = artifact_review_errors(workflow, workflow_text)
    workflow_status_result = validate_workflow_status_evidence(workflow_text)
    projection_result = validate_projection_integrity(
        state_data,
        plan_steps,
        state,
        expected_head_commit=authority.expected_head_commit,
    )
    manifest_result = validate_changed_file_manifest(
        state_data,
        state,
        expected_base_commit=authority.expected_base_commit,
        expected_head_commit=authority.expected_head_commit,
    )
    problems = {
        **workflow_result,
        **workflow_status_result,
        **status_result,
        **privacy_result,
        **marker_privacy_result,
        **autonomy_result,
        **stage_result,
        **formal_result,
        **artifact_result,
        **workflow_checkpoint_result,
        # Its own key, never folded into the gated path's. Folding would report it
        # under a frozen key, and would newly arm every gated-path error
        # along with it. Present on every run, empty on a skip and on a pass, so
        # the classification record can never see it conditionally absent.
        "workflow_authority_errors": workflow_authority_errors,
        **state_result,
        **projection_result,
        **manifest_result,
    }
    passed = all(not values for values in problems.values())

    return {
        "status": "pass" if passed else "fail",
        "workflow_file": str(workflow),
        "state_file": str(state),
        "plan_step_count": len(plan_steps),
        "repair": _repair_request(problems),
        **problems,
    }


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", required=True, type=Path, help="Autopilot workflow markdown file")
    parser.add_argument("--state", required=True, type=Path, help="autopilot-state.json file")
    parser.add_argument(
        "--expected-base-commit",
        help="live PR baseRefOid authority required when pr-marker-plan.v2 uses a changed-file manifest",
    )
    parser.add_argument(
        "--expected-head-commit",
        help="live PR headRefOid authority required when pr-marker-plan.v2 uses a changed-file manifest",
    )
    parser.add_argument(
        "--require-autonomy-boundary",
        action="store_true",
        help="require the Codex Phase 6.5 autonomy record when the plan can reach Phase 7",
    )
    parser.add_argument(
        "--current-execution-environment",
        help="current trusted execution environment supplied by the orchestrator",
    )
    parser.add_argument(
        "--current-sandbox-mode",
        help="current trusted sandbox mode supplied by the orchestrator",
    )
    parser.add_argument(
        "--current-approval-reviewer",
        help="current trusted approval reviewer supplied by the orchestrator",
    )
    parser.add_argument(
        "--current-writable-root",
        action="append",
        help="current trusted absolute writable root; repeat for every root",
    )
    parser.add_argument(
        "--rule",
        action="append",
        choices=sorted(RULE_PROBLEM_KEYS),
        help=(
            "Limit the exit code to the named rule. The full report is always printed; "
            "only which problem lists decide pass/fail changes. Repeatable. "
            "Omit to gate on every check."
        ),
    )
    return parser


def _current_execution_boundary_from_args(
    args: argparse.Namespace,
) -> dict[str, Any] | None:
    current_boundary_values = (
        args.current_execution_environment,
        args.current_sandbox_mode,
        args.current_approval_reviewer,
        args.current_writable_root,
    )
    current_execution_boundary = None
    if any(value is not None for value in current_boundary_values):
        current_execution_boundary = {
            "execution_environment": args.current_execution_environment,
            "sandbox_mode": args.current_sandbox_mode,
            "approval_reviewer": args.current_approval_reviewer,
            "writable_roots": args.current_writable_root,
        }
    return current_execution_boundary


def main(argv: list[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    authority = ReportAuthority(
        expected_base_commit=args.expected_base_commit,
        expected_head_commit=args.expected_head_commit,
        current_execution_boundary=_current_execution_boundary_from_args(args),
        require_autonomy_boundary=args.require_autonomy_boundary,
    )

    try:
        report = build_report(
            args.workflow,
            args.state,
            authority=authority,
        )
    except ValidationError as exc:
        print(json.dumps({"status": "input_error", "code": exc.code, "message": str(exc)}, sort_keys=True))
        return 2

    print(json.dumps(report, sort_keys=True))
    if args.rule:
        selected: list[str] = []
        for rule in args.rule:
            selected.extend(RULE_PROBLEM_KEYS[rule])
        return 0 if all(not report.get(key) for key in selected) else 1
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
