#!/usr/bin/env python3
"""Golden fixtures for the shared ``resolve-autopilot-stage`` runner operation.

Stage resolution exists once, as a registered read-only runner operation both
distributions reach by operation identifier (FR-012). These fixtures are the
executable statement of that surface: the closed stage vocabulary, the argv
precedence rules, the four pre-flight rejections, and the workflow-file reader
that drives auto-detection.

Two layers reject and they are asserted separately. The runner validates the
*request* and returns a diagnostic envelope — ``invalid_input`` for a malformed
``autopilot_args``, ``unsupported_path`` for a path outside the trust boundary —
and ``unsupported_path`` has no entry in the runner's exit-code map at all. Only
the operation's own rejections are exit 2.

Python 3.11+ standard library only.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = TEST_DIR.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from test_result import run_counted  # noqa: E402

from speckit_pro_runner.helpers import read_only  # noqa: E402

COVERAGE_VALIDATOR = (
    PLUGIN_ROOT
    / "skills"
    / "speckit-autopilot"
    / "scripts"
    / "validate-autopilot-phase-coverage.py"
)
# A real, durable workflow file: the workflow record survives archiving of its
# `specs/<id>/` directory, which is why it and not the state file is the
# authoritative per-spec store (data-model.md:29-32).
WORKFLOW_FILE = "tests/speckit-pro/unit/fixtures/autopilot-stage/workflow.md"
OUTSIDE_TRUST_BOUNDARY = "../outside-the-trust-boundary-workflow.md"

# --- Stage vocabulary (FR-001) -------------------------------------------
# Exactly three literal lowercase tokens; no aliases, no alternate casing, no
# long-form spellings (data-model.md:10-24).
STAGE_VOCABULARY = ("plan", "implement", "full")
STAGE_PHASE_RANGES = {
    "plan": ("specify", "clarify", "plan", "checklist", "tasks", "analyze"),
    "implement": ("implement",),
    "full": ("specify", "clarify", "plan", "checklist", "tasks", "analyze", "implement"),
}

# --- Argv resolution: explicit `--stage` always reports source "argv" -----
# (argv, expected stage, expected from_phase)
ARGV_RESOLUTION_CASES = (
    (["--stage", "plan"], "plan", None),
    (["--stage", "implement"], "implement", None),
    (["--stage", "full"], "full", None),
    # The workflow path is a positional argument and never a flag value.
    ([WORKFLOW_FILE, "--stage", "plan"], "plan", None),
    # Argument order in a synopsis is presentation only: the resolver reads argv
    # by name, so the Claude ordering and the Codex ordering agree.
    (["--from-phase", "tasks", "--spec", "FEATURE-001", "--stage", "plan"], "plan", "tasks"),
    (["--stage", "plan", "--strict", "--from-phase", "tasks"], "plan", "tasks"),
    # `--from-phase` inside the named stage's range moves only the start point.
    (["--stage", "plan", "--from-phase", "analyze"], "plan", "analyze"),
    (["--stage", "implement", "--from-phase", "implement"], "implement", "implement"),
    # Repeated with the SAME value is not a conflict.
    (["--stage", "plan", "--stage", "plan"], "plan", None),
    # No stage named at all: rank 2 decides, so the parser reports nothing.
    ([WORKFLOW_FILE], None, None),
    (["--from-phase", "implement"], None, "implement"),
)

# --- Pre-flight rejections, exit 2 (contracts/stage-invocation.md:166-169) -
# (argv, expected one-line diagnostic)
ARGV_REJECTION_CASES = (
    (
        ["--stage", "planning"],
        "error: unrecognized stage 'planning' — accepted values: plan, implement, full",
    ),
    (
        ["--stage", "Plan"],
        "error: unrecognized stage 'Plan' — accepted values: plan, implement, full",
    ),
    (
        ["--stage", "plan", "--stage", "implement"],
        "error: --stage given more than once with different values: plan, implement",
    ),
    (
        ["--stage", "plan", "--from-phase", "implement"],
        "error: --stage plan and --from-phase implement are mutually exclusive",
    ),
    (
        ["--stage", "implement", "--from-phase", "tasks"],
        "error: --stage implement and --from-phase tasks are mutually exclusive",
    ),
    (
        ["--stage"],
        "error: --stage requires a value — accepted values: plan, implement, full",
    ),
    (
        ["--stage", "--advisory"],
        "error: --stage requires a value — accepted values: plan, implement, full",
    ),
)

# The range conflict is scoped to an EXPLICITLY named stage (FR-007). After a
# strict-mode gate stop, auto-detection resolves `plan` and the shipped stop
# guidance tells the operator to resume at the implementation phase; rejecting
# that pair would strand the operator at the one boundary the argument exists to
# cross (contracts/stage-invocation.md:175-183).
AUTO_DETECTED_FROM_PHASE_CASES = (
    ["--from-phase", "implement"],
    ["--from-phase", "analyze"],
)


# --- Cross-distribution argv parity (FR-015a, SC-007) --------------------
# Both distributions publish the same flag set in two different synopsis
# orderings: Claude names `--stage` before the `--strict | --advisory` pair
# (contracts/stage-invocation.md:15-19), Codex names it after (`:39-43`).
# Argument order in a synopsis is presentation only — the parser reads argv by
# name, never by position (speckit_pro_runner/helpers/read_only.py:1111-1112) —
# so both orderings must reach the one registered `resolve-autopilot-stage`
# operation and resolve identically. That is asserted here, by execution, rather
# than in the structural parity validator, whose checks are existence-only.
#
# Neither form carries the leading `/speckit-pro:speckit-autopilot` command
# token: each distribution's `## Input` block documents the argv the skill
# *receives*, which on both sides begins at the workflow path, and parity is
# over the flag set, its values, and its precedence — never over that token,
# which has no Codex counterpart (contracts/stage-invocation.md:24-34).
#
# (label, from_phase, spec, stage, mode)
PARITY_INVOCATIONS = (
    ("bare invocation", None, None, None, None),
    ("stage plan", None, None, "plan", None),
    ("stage implement", None, None, "implement", None),
    ("stage full", None, None, "full", None),
    # The two orderings differ only when a stage AND a mode flag are both
    # present; these are the cases that actually exercise the divergence.
    ("stage plan with --strict", None, None, "plan", "--strict"),
    ("stage implement with --advisory", None, None, "implement", "--advisory"),
    ("stage full with --strict", None, None, "full", "--strict"),
    ("stage plan with a spec and --advisory", None, "FEATURE-001", "plan", "--advisory"),
    ("stage plan with an in-range --from-phase", "analyze", None, "plan", "--strict"),
    ("stage implement with an in-range --from-phase", "implement", None, "implement", "--advisory"),
    # No stage named: rank 2 decides, and the mode flag must not perturb it.
    ("auto-detect with --from-phase implement", "implement", None, None, "--strict"),
    ("auto-detect with a spec and a mode flag", None, "FEATURE-001", None, "--advisory"),
)

# Rejections must be byte-identical across the two orderings too: a run rejected
# in one distribution and accepted in the other is the divergence FR-015a exists
# to prevent. (label, stage, from_phase)
PARITY_REJECTIONS = (
    ("unrecognized stage value", "planning", None),
    ("alternate casing is not an alias", "Plan", None),
    ("--from-phase outside the named stage's range", "plan", "implement"),
    ("implement stage with a planning --from-phase", "implement", "tasks"),
)


# --- Workflow-file reader fixtures (FR-006a, FR-008a) --------------------
PLANNING_ROWS_TERMINAL = (
    ("Specify", "✅ Complete"),
    ("Clarify", "✅ Complete"),
    ("Plan", "✅ Complete"),
    ("Checklist", "✅ Complete"),
    ("Tasks", "✅ Complete"),
    ("Analyze", "✅ Complete"),
)
GATE_TERMINAL = ("Confidence Gate", "✅ Complete")
GATE_SKIPPED = ("Confidence Gate", "⏭ Skipped")
GATE_BLOCKED = ("Confidence Gate", "⚠️ Blocked")
IMPLEMENT_PENDING = ("Implement", "⏳ Pending")

# (label, overview rows, planning_complete, confidence_gate_status, first_open)
PLANNING_PREDICATE_CASES = (
    (
        "every predicate row terminal",
        PLANNING_ROWS_TERMINAL + (GATE_TERMINAL, IMPLEMENT_PENDING),
        True,
        "✅ Complete",
        None,
    ),
    (
        # Legacy files predate the gate row entirely; absence must not block.
        "confidence gate row absent",
        PLANNING_ROWS_TERMINAL + (IMPLEMENT_PENDING,),
        True,
        None,
        None,
    ),
    (
        # The flagship case. A strict-mode gate stop leaves the six planning rows
        # terminal and this row blocked. Inheriting the validator's
        # ADVISORY_PHASES exclusion here would resolve `implement` straight after
        # the stop — the exact FR-006a defect.
        "confidence gate present but blocked",
        PLANNING_ROWS_TERMINAL + (GATE_BLOCKED, IMPLEMENT_PENDING),
        False,
        "⚠️ Blocked",
        ("Confidence Gate", "⚠️ Blocked"),
    ),
    (
        "confidence gate skipped is terminal",
        PLANNING_ROWS_TERMINAL + (GATE_SKIPPED, IMPLEMENT_PENDING),
        True,
        "⏭ Skipped",
        None,
    ),
    (
        "a planning row is still pending",
        PLANNING_ROWS_TERMINAL[:5] + (("Analyze", "⏳ Pending"), IMPLEMENT_PENDING),
        False,
        None,
        ("Analyze", "⏳ Pending"),
    ),
    (
        "a planning row is blocked",
        PLANNING_ROWS_TERMINAL[:3] + (("Checklist", "⚠ Blocked"),) + PLANNING_ROWS_TERMINAL[4:],
        False,
        None,
        ("Checklist", "⚠ Blocked"),
    ),
    (
        # A missing planning row is not a parse failure; it means the phase has
        # not run, so planning is not complete.
        "a planning row is absent",
        PLANNING_ROWS_TERMINAL[:3] + PLANNING_ROWS_TERMINAL[4:] + (IMPLEMENT_PENDING,),
        False,
        None,
        ("Checklist", None),
    ),
)

# (label, `### Basic Information` block, expected recorded_stage)
RECORDED_STAGE_CASES = (
    ("bold field name", "| **Stage** | plan |\n", "plan"),
    ("plain field name", "| Stage | implement |\n", "implement"),
    ("backticked value", "| **Stage** | `full` |\n", "full"),
    # Absence is legal and is not an error: it means "no run yet" (FR-008a).
    ("no Stage row at all", "", None),
)

# --- The `Draft PR` row (FR-009) -----------------------------------------
# The pull-request identity lives in the same `### Basic Information` table as
# `Stage`, never in `## Workflow Overview`, whose rows are phase status records.
# The number and the URL are one linked reference, not two columns: readers take
# the number from the link text and the URL from the link target
# (contracts/draft-pr-row.md:14-40). The record types are pinned by
# data-model.md:105-109 — `number` is an integer, `url` a string, `gap_note` a
# string or null.
DRAFT_PR_URL = "https://github.com/owner/repo/pull/438"
DRAFT_PR_PRESENT_ROW = f"| **Draft PR** | [#438]({DRAFT_PR_URL}) |\n"
DRAFT_PR_IDENTITY = {"number": 438, "url": DRAFT_PR_URL, "gap_note": None}

# (label, `### Basic Information` row, expected record)
DRAFT_PR_ROW_CASES = (
    ("bold field name", DRAFT_PR_PRESENT_ROW, DRAFT_PR_IDENTITY),
    ("plain field name", f"| Draft PR | [#438]({DRAFT_PR_URL}) |\n", DRAFT_PR_IDENTITY),
    ("backticked field name", f"| `Draft PR` | [#438]({DRAFT_PR_URL}) |\n", DRAFT_PR_IDENTITY),
    # The key is compared case-insensitively after stripping `*`, backticks, and
    # spaces — the same normalization the shipped `Stage` row already uses.
    ("lowercased field name", f"| draft pr | [#438]({DRAFT_PR_URL}) |\n", DRAFT_PR_IDENTITY),
    ("uppercased field name", f"| **DRAFT PR** | [#438]({DRAFT_PR_URL}) |\n", DRAFT_PR_IDENTITY),
    (
        "a shortfall note follows the link",
        f"| **Draft PR** | [#438]({DRAFT_PR_URL}) — 2 of 4 artifacts missing |\n",
        {"number": 438, "url": DRAFT_PR_URL, "gap_note": "2 of 4 artifacts missing"},
    ),
    # Nothing in the grammar bounds the width of the number.
    (
        "a wider number",
        "| **Draft PR** | [#1024](https://github.com/owner/repo/pull/1024) |\n",
        {"number": 1024, "url": "https://github.com/owner/repo/pull/1024", "gap_note": None},
    ),
)

# (label, prose written after the link, expected `gap_note`)
# The grammar template is `[#<number>](<url>) — <gap note>`, which places the
# separator outside the placeholder: the note is the prose, not the dash.
DRAFT_PR_GAP_NOTE_CASES = (
    ("a plain shortfall note", "— 2 of 4 artifacts missing", "2 of 4 artifacts missing"),
    # A note carrying its own parentheses. A greedy link-target capture would
    # swallow the rest of the cell into `url` and lose the identity entirely,
    # which is the failure FR-011 corroboration would then blame on GitHub.
    (
        "a note containing parentheses",
        "— selection failed (no pages chosen)",
        "selection failed (no pages chosen)",
    ),
    # A note carrying a second Markdown link, for the same reason.
    (
        "a note containing another link",
        "— see [the index](docs/ai/specs/.process/FEATURE-007-index.md)",
        "see [the index](docs/ai/specs/.process/FEATURE-007-index.md)",
    ),
)

# (label, the `Draft PR` value cell as written)
# None of these is one `[#<number>](<url>)` link. The reader reports absence
# rather than raising: a workflow file is operator-edited prose, and a traceback
# there would stop a run over a typo (contracts/draft-pr-row.md:117).
MALFORMED_DRAFT_PR_VALUES = (
    ("an empty value", ""),
    ("a bare number with no link", "#438"),
    ("a bare URL with no link", DRAFT_PR_URL),
    ("link text missing the `#`", f"[438]({DRAFT_PR_URL})"),
    ("non-numeric link text", f"[#pending]({DRAFT_PR_URL})"),
    ("a link with no target", "[#438]"),
    ("a link with an empty target", "[#438]()"),
    ("prose instead of a link", "not opened yet"),
)

# --- Recorded confidence-gate verdict (FR-010a) --------------------------
# The gate record written under `## Phase 6.5: Confidence Gate` is prose, and it
# is not a verdict source. Real workflow files spell the record three different
# ways — `Verdict | **proceed**`, `Decision | Pass; proceed to Phase 7`,
# `Result | Soft-skip` — so no single prose field name exists to read. The
# composite score is not a verdict either: the same score proceeds under advisory
# mode and stops under strict, so an identical prose block accompanies both
# outcomes. Only the status row records which of the two actually happened.
GATE_RECORD_PROSE = (
    "\n## Phase 6.5: Confidence Gate\n\n"
    "| Field | Value |\n"
    "|-------|-------|\n"
    "| Mode | **advisory** |\n"
    "| Composite confidence | **0.88** |\n"
    "| Verdict | **proceed** |\n"
)

# (label, overview rows, expected confidence_gate_status, expected planning_complete)
CONFIDENCE_GATE_VERDICT_CASES = (
    (
        "terminal verdict is echoed verbatim",
        PLANNING_ROWS_TERMINAL + (GATE_TERMINAL, IMPLEMENT_PENDING),
        "✅ Complete",
        True,
    ),
    (
        "a skipped gate is terminal",
        PLANNING_ROWS_TERMINAL + (GATE_SKIPPED, IMPLEMENT_PENDING),
        "⏭ Skipped",
        True,
    ),
    (
        # The state a strict-mode stop leaves behind: the six planning rows are
        # terminal and the gate refused. The verdict an implementation-stage run
        # reads instead of re-running the gate (FR-010a).
        "non-terminal verdict is echoed and does not complete planning",
        PLANNING_ROWS_TERMINAL + (GATE_BLOCKED, IMPLEMENT_PENDING),
        "⚠️ Blocked",
        False,
    ),
    (
        # Absence is null, never an error and never inferred from the prose
        # record: nearly every workflow file in the tree predates the row.
        "an absent row is null",
        PLANNING_ROWS_TERMINAL + (IMPLEMENT_PENDING,),
        None,
        True,
    ),
)

# --- Auto-detection (FR-006, SC-004) -------------------------------------
PLANNING_INCOMPLETE = PLANNING_ROWS_TERMINAL[:5] + (("Analyze", "⏳ Pending"), IMPLEMENT_PENDING)
PLANNING_COMPLETE = PLANNING_ROWS_TERMINAL + (GATE_TERMINAL, IMPLEMENT_PENDING)
# The state a strict-mode gate stop leaves behind: every planning row terminal,
# the gate refused. Resolving `implement` here is the flagship silent failure —
# it would start the very phase the gate just refused.
STRICT_MODE_STOP = PLANNING_ROWS_TERMINAL + (GATE_BLOCKED, IMPLEMENT_PENDING)

# The workflow states whose auto-detected outcomes differ, so cross-distribution
# parity is asserted across every branch of the reader, not one happy path.
PARITY_WORKFLOWS = (
    ("planning incomplete", PLANNING_INCOMPLETE),
    ("planning complete", PLANNING_COMPLETE),
    ("strict-mode gate stop", STRICT_MODE_STOP),
    ("confidence gate row absent", PLANNING_ROWS_TERMINAL + (IMPLEMENT_PENDING,)),
    ("confidence gate skipped", PLANNING_ROWS_TERMINAL + (GATE_SKIPPED, IMPLEMENT_PENDING)),
)

# (label, overview rows, argv, expected stage, expected source, basis must name)
AUTO_DETECTION_CASES = (
    (
        "planning incomplete resolves plan",
        PLANNING_INCOMPLETE,
        [],
        "plan",
        "auto-detect",
        ("Analyze", "⏳ Pending"),
    ),
    (
        "every predicate row terminal resolves implement",
        PLANNING_COMPLETE,
        [],
        "implement",
        "auto-detect",
        (),
    ),
    (
        # An explicitly named stage always overrides auto-detection, including
        # when it disagrees with what auto-detection would have chosen.
        "explicit --stage overrides auto-detection",
        PLANNING_INCOMPLETE,
        ["--stage", "implement"],
        "implement",
        "argv",
        (),
    ),
    (
        "strict-mode gate stop resolves plan, never implement",
        STRICT_MODE_STOP,
        [],
        "plan",
        "auto-detect",
        ("Confidence Gate", "⚠️ Blocked"),
    ),
    (
        # A planning row absent from the table has no status to name, so the
        # basis names the phase and says the row is missing rather than
        # printing a bare `None`.
        "an absent planning row is named without a status",
        PLANNING_ROWS_TERMINAL[:3] + PLANNING_ROWS_TERMINAL[4:] + (IMPLEMENT_PENDING,),
        [],
        "plan",
        "auto-detect",
        ("Checklist",),
    ),
)

# Text that must be rejected as exit 2 rather than degraded to a default: with no
# parseable table, auto-detection has no input, and every degraded default
# resolves the planning stage — which would re-run finished work whenever the
# file is merely transiently unreadable (FR-007).
UNPARSEABLE_WORKFLOW_TEXTS = (
    ("no Workflow Overview heading", "# Workflow\n\nNo table here.\n"),
    ("heading with no table", "## Workflow Overview\n\nThe table was removed.\n"),
    ("header row only", "## Workflow Overview\n\n| Phase | Command | Status |\n"),
)


# --- Planning-stage canonical task list (FR-011) -------------------------
# The canonical list is NEVER truncated per stage. An entry outside the resolved
# stage keeps its byte-identical canonical name and takes `skipped: <reason>` in
# its STATUS field (data-model.md:96-110).
TASK_LIST_CANONICAL_DOC = (
    PLUGIN_ROOT / "skills" / "speckit-autopilot" / "references" / "task-list-canonical.md"
)
OUT_OF_STAGE_STATUS = "skipped: out of stage — resolved stage is plan"
IN_STAGE_ENTRIES = (
    "Archive Sweep: previously merged specs dry-run/apply eligibility",
    "Phase 0: Prerequisites",
    "Phase 1: Specify",
    "Phase 2: Clarify - Stage State Representation",
    "Phase 2: Clarify - Stage State Representation Consensus",
    "Phase 3: Plan",
    "Phase 4: Checklist - state-management",
    "Phase 4: Checklist - state-management Consensus",
    "Phase 5: Tasks",
    "Phase 6: Analyze",
    "Phase 6: Analyze - Consensus",
    "Phase 6.5: Confidence Gate",
)
CANONICAL_POST_ENTRIES = (
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
)
# A planning-stage run marks the Implement phase AND every `Post:` entry; the
# post-implementation family is where the pre-final audit actually blocks.
OUT_OF_STAGE_ENTRIES = ("Phase 7: Implement",) + CANONICAL_POST_ENTRIES

# The marking rules the canonical-list reference must state, so the two
# distributions mark out-of-stage entries the same way rather than each
# inventing a shape the shipped guard rejects.
TASK_LIST_OUT_OF_STAGE_RULES = (
    "`skipped: <reason>` in the **status** field",
    "the entry name never changes",
    "MUST NOT contain the substring `pending` in any casing",
    "every `Post:` entry",
)


# --- Draft PR corroboration (FR-011) -------------------------------------
# The orchestrator takes ONE read-only `gh pr list --head <branch> --state all
# --json number,url,state,isDraft,headRefName` observation and passes it in as
# JSON; this operation parses the `Draft PR` row, classifies, and reports. No
# helper in the runner shells out to `gh`, and this contract preserves that,
# which is what leaves the classification deterministic and offline-testable
# (contracts/stage-corroboration.md:11-19).
CORROBORATION_STATUSES = (
    "match",
    "no_record",
    "skipped",
    "pr_closed",
    "pr_missing",
    "identity_mismatch",
)
# The last three are discrepancies; the first three are not
# (contracts/stage-corroboration.md:141-145).
CORROBORATION_DISCREPANCIES = ("pr_closed", "pr_missing", "identity_mismatch")

# The eight keys that predate this contract, in the order the envelope writes
# them. `corroboration` is added as a ninth and never displaces one of these
# (contracts/stage-corroboration.md:91-114).
PRE_EXISTING_ENVELOPE_KEYS = (
    "tool",
    "stage",
    "source",
    "basis",
    "recorded_stage",
    "planning_complete",
    "confidence_gate_status",
    "from_phase",
)
ENVELOPE_KEYS = PRE_EXISTING_ENVELOPE_KEYS + ("corroboration",)

# Separates "the request carried no `pr_observation` key at all" from "it
# carried one" in the tables below. In the operation's own input that
# distinction is the JSON key's presence (contracts/stage-corroboration.md:77).
OBSERVATION_ABSENT = object()

# `recorded` is the identity pair the `Draft PR` row stores, and only that pair:
# the row's `gap_note` is FR-004 shortfall prose about the run, never part of the
# pull request's identity (contracts/stage-corroboration.md:105).
RECORDED_IDENTITY = {"number": 438, "url": DRAFT_PR_URL}
# A repository transfer moves a pull request without changing its number, so the
# live URL of the recorded number can differ from the recorded URL — rule 2.
TRANSFERRED_URL = "https://github.com/owner/renamed-repo/pull/438"
SECOND_PR_URL = "https://github.com/owner/repo/pull/512"

# `--json number,url,state,isDraft,headRefName` entries, on the head branch the
# `### Basic Information` table names. `gh` spells the three live states `OPEN`,
# `CLOSED`, and `MERGED`; the query returns no `merged` field of its own, so
# `merged` is read off `state` (contracts/stage-corroboration.md:28-34).
OPEN_438 = {
    "number": 438,
    "url": DRAFT_PR_URL,
    "state": "OPEN",
    "isDraft": True,
    "headRefName": "test-branch",
}
CLOSED_438 = {**OPEN_438, "state": "CLOSED", "isDraft": False}
MERGED_438 = {**OPEN_438, "state": "MERGED", "isDraft": False}
TRANSFERRED_438 = {**OPEN_438, "url": TRANSFERRED_URL}
OPEN_512 = {
    "number": 512,
    "url": SECOND_PR_URL,
    "state": "OPEN",
    "isDraft": True,
    "headRefName": "test-branch",
}
CLOSED_512 = {**OPEN_512, "state": "CLOSED", "isDraft": False}

# `observed` carries the three fields the classification actually reads. The
# query's `isDraft` and `headRefName` decide nothing — the query is already
# scoped to the head branch — so neither is echoed
# (contracts/stage-corroboration.md:106).
OBSERVED_438_OPEN = {"number": 438, "url": DRAFT_PR_URL, "state": "OPEN"}
OBSERVED_438_CLOSED = {"number": 438, "url": DRAFT_PR_URL, "state": "CLOSED"}
OBSERVED_438_MERGED = {"number": 438, "url": DRAFT_PR_URL, "state": "MERGED"}
OBSERVED_438_TRANSFERRED = {"number": 438, "url": TRANSFERRED_URL, "state": "OPEN"}
OBSERVED_512_OPEN = {"number": 512, "url": SECOND_PR_URL, "state": "OPEN"}

# CONTRACT GAP — these two strings are this file's pin, not the contract's.
# §5.1 says an absent or unsuccessful observation yields `skipped` "with a
# `reason`", and §6 shows one being printed, but neither names a reason for the
# two cases where the request supplies none: the key was absent, or it was
# present and unusable. Both wordings below are chosen to read correctly in §6's
# run-report line (`Draft PR: skipped — no observation supplied`). If T036-T038
# choose different wording, change it HERE — every fixture in this section reads
# these two constants, and nothing else pins them. An `ok: false` observation
# that DOES carry a reason echoes that reason verbatim instead
# (contracts/stage-corroboration.md:80, :122-124, :169-172).
NO_OBSERVATION_REASON = "no observation supplied"
UNUSABLE_OBSERVATION_REASON = "observation unusable"

# `corroboration` carries the same five keys for every status; the ones a status
# has nothing to say about are null rather than absent, so every consumer reads
# one shape (contracts/stage-corroboration.md:103-109).
CORROBORATION_MATCH = {
    "status": "match",
    "recorded": RECORDED_IDENTITY,
    "observed": OBSERVED_438_OPEN,
    "merged": None,
    "reason": None,
}
# No row means no recorded identity to carry, and no observation was taken.
CORROBORATION_NO_RECORD = {
    "status": "no_record",
    "recorded": None,
    "observed": None,
    "merged": None,
    "reason": None,
}
# The row IS present on a `skipped` run, and §7 needs its identity: the terminal
# step refreshes that pull request once the tool can be reached again.
CORROBORATION_SKIPPED_NO_OBSERVATION = {
    "status": "skipped",
    "recorded": RECORDED_IDENTITY,
    "observed": None,
    "merged": None,
    "reason": NO_OBSERVATION_REASON,
}
CORROBORATION_SKIPPED_UNUSABLE = {
    **CORROBORATION_SKIPPED_NO_OBSERVATION,
    "reason": UNUSABLE_OBSERVATION_REASON,
}
CORROBORATION_PR_CLOSED = {
    "status": "pr_closed",
    "recorded": RECORDED_IDENTITY,
    "observed": OBSERVED_438_CLOSED,
    "merged": False,
    "reason": None,
}
CORROBORATION_PR_MERGED = {
    **CORROBORATION_PR_CLOSED,
    "observed": OBSERVED_438_MERGED,
    "merged": True,
}
CORROBORATION_PR_MISSING = {
    "status": "pr_missing",
    "recorded": RECORDED_IDENTITY,
    "observed": None,
    "merged": None,
    "reason": None,
}
CORROBORATION_IDENTITY_MISMATCH_SECOND_PR = {
    "status": "identity_mismatch",
    "recorded": RECORDED_IDENTITY,
    "observed": OBSERVED_512_OPEN,
    "merged": None,
    "reason": None,
}
CORROBORATION_IDENTITY_MISMATCH_URL = {
    **CORROBORATION_IDENTITY_MISMATCH_SECOND_PR,
    "observed": OBSERVED_438_TRANSFERRED,
}

# One witness per status, in the §5.3 order, so the closed vocabulary is proved
# by construction rather than by inspection.
# (label, status, `Draft PR` row, observation, expected corroboration object)
STATUS_WITNESS_CASES = (
    (
        "the recorded pull request is open at the recorded URL",
        "match",
        DRAFT_PR_PRESENT_ROW,
        {"ok": True, "pull_requests": [OPEN_438]},
        CORROBORATION_MATCH,
    ),
    (
        "no `Draft PR` row has been written yet",
        "no_record",
        "",
        OBSERVATION_ABSENT,
        CORROBORATION_NO_RECORD,
    ),
    (
        "the row is present but no observation reached the operation",
        "skipped",
        DRAFT_PR_PRESENT_ROW,
        OBSERVATION_ABSENT,
        CORROBORATION_SKIPPED_NO_OBSERVATION,
    ),
    (
        "the recorded number is closed without having been merged",
        "pr_closed",
        DRAFT_PR_PRESENT_ROW,
        {"ok": True, "pull_requests": [CLOSED_438]},
        CORROBORATION_PR_CLOSED,
    ),
    (
        "the branch carries no pull request at all",
        "pr_missing",
        DRAFT_PR_PRESENT_ROW,
        {"ok": True, "pull_requests": []},
        CORROBORATION_PR_MISSING,
    ),
    (
        "the only open pull request is not the recorded one",
        "identity_mismatch",
        DRAFT_PR_PRESENT_ROW,
        {"ok": True, "pull_requests": [OPEN_512]},
        CORROBORATION_IDENTITY_MISMATCH_SECOND_PR,
    ),
)

# The rest of §5.2, against a `Draft PR` row that is always present.
# (label, observation, expected corroboration object)
SUCCESSFUL_OBSERVATION_CASES = (
    (
        # `isDraft` and `headRefName` decide nothing, so an entry without them
        # is complete rather than malformed. Requiring them would make the
        # operation reject an observation it can classify perfectly well.
        "an entry carries only the three fields the classification reads",
        {"ok": True, "pull_requests": [OBSERVED_438_OPEN]},
        CORROBORATION_MATCH,
    ),
    (
        # Rule 1 names an OPEN pull request. A closed one with another number is
        # this branch's own history, not a competing identity.
        "a closed pull request with another number is not a competing identity",
        {"ok": True, "pull_requests": [OPEN_438, CLOSED_512]},
        CORROBORATION_MATCH,
    ),
    (
        "the recorded number was merged",
        {"ok": True, "pull_requests": [MERGED_438]},
        CORROBORATION_PR_MERGED,
    ),
    (
        # Rule 4, reached because rule 1 found nothing open to conflict with.
        "the branch carries only a closed pull request with another number",
        {"ok": True, "pull_requests": [CLOSED_512]},
        CORROBORATION_PR_MISSING,
    ),
    (
        "the recorded number is open beside a second open pull request",
        {"ok": True, "pull_requests": [OPEN_438, OPEN_512]},
        CORROBORATION_IDENTITY_MISMATCH_SECOND_PR,
    ),
    (
        # `gh` orders its array by recency, which is not a fact about identity.
        "the second open pull request is listed first",
        {"ok": True, "pull_requests": [OPEN_512, OPEN_438]},
        CORROBORATION_IDENTITY_MISMATCH_SECOND_PR,
    ),
    (
        # Rule 2: the number still resolves, but not to the recorded URL.
        "the recorded number is open at a transferred URL",
        {"ok": True, "pull_requests": [TRANSFERRED_438]},
        CORROBORATION_IDENTITY_MISMATCH_URL,
    ),
)

# Rule 1 runs before rules 2, 3, and 4, and the order is load-bearing: a branch
# that grew a second pull request must report the conflict rather than the
# absence, the closure, or the moved URL. Every observation below satisfies a
# later rule too, so a resolver that evaluated them in any other order would
# report a different status (contracts/stage-corroboration.md:128-140).
# (label, observation, the rule an extra open pull request outranks)
PRECEDENCE_CASES = (
    (
        "an extra open pull request outranks a missing recorded number",
        {"ok": True, "pull_requests": [OPEN_512]},
        "rule 4",
    ),
    (
        "an extra open pull request outranks a closed recorded number",
        {"ok": True, "pull_requests": [CLOSED_438, OPEN_512]},
        "rule 3",
    ),
    (
        "an extra open pull request outranks a transferred recorded URL",
        {"ok": True, "pull_requests": [TRANSFERRED_438, OPEN_512]},
        "rule 2",
    ),
)

# Fail-closed on evidence, fail-open on outcome. The tool being absent,
# unauthenticated, cancelled, rate-limited, or emitting unparseable output are
# all the same class, and none of them is evidence that a recorded pull request
# is gone (contracts/stage-corroboration.md:82-85).
# (label, the reason the orchestrator reports)
UNSUCCESSFUL_OBSERVATION_REASONS = (
    ("the tool is not installed", "gh: command not found"),
    ("the tool is not authenticated", "gh not authenticated"),
    ("the operator cancelled the query", "cancelled by the operator"),
    ("the API rate limit was reached", "API rate limit exceeded"),
    ("the output did not parse as JSON", "gh output did not parse as JSON"),
)

# An absent row is decided before any observation is looked at, so a supplied
# observation is never read — `observed` stays null even when the array would
# otherwise classify as a discrepancy (contracts/stage-corroboration.md:120-126).
# (label, observation)
NO_RECORD_OBSERVATIONS = (
    ("no observation was supplied", OBSERVATION_ABSENT),
    ("an observation that would otherwise match", {"ok": True, "pull_requests": [OPEN_438]}),
    (
        "an observation naming a competing open pull request",
        {"ok": True, "pull_requests": [OPEN_512]},
    ),
    ("an unsuccessful query", {"ok": False, "reason": "gh not authenticated"}),
)

# Anything that is not `ok: true` with a parseable array. Every entry is a
# single-element array so each case pins one malformed shape rather than also
# deciding what a good entry beside a junk sibling means, which the contract
# does not address. (label, observation)
MALFORMED_OBSERVATIONS = (
    ("the observation is a string", "ok"),
    ("the observation is an array", []),
    ("the observation is a number", 0),
    ("the observation is an empty object", {}),
    ("`ok` is absent", {"pull_requests": [OPEN_438]}),
    ('`ok` is the string "true"', {"ok": "true", "pull_requests": [OPEN_438]}),
    (
        # JSON `1` is not JSON `true`, and Python's `1 == True` makes a
        # truthiness check accept it silently. §3 admits `ok: true` and nothing
        # else, which is what forbids the loose check.
        "`ok` is 1 rather than true",
        {"ok": 1, "pull_requests": [OPEN_438]},
    ),
    ("`pull_requests` is absent", {"ok": True}),
    ("`pull_requests` is an object", {"ok": True, "pull_requests": {"number": 438}}),
    ("`pull_requests` is a string", {"ok": True, "pull_requests": "[]"}),
    ("an entry is a string", {"ok": True, "pull_requests": ["#438"]}),
    ("an entry is null", {"ok": True, "pull_requests": [None]}),
    (
        "an entry carries no `number`",
        {"ok": True, "pull_requests": [{"url": DRAFT_PR_URL, "state": "OPEN"}]},
    ),
    (
        "an entry carries no `url`",
        {"ok": True, "pull_requests": [{"number": 438, "state": "OPEN"}]},
    ),
    (
        "an entry carries no `state`",
        {"ok": True, "pull_requests": [{"number": 438, "url": DRAFT_PR_URL}]},
    ),
    (
        # The recorded number is an int precisely so it can be compared against
        # the number a `--json` query returns. A string here would never equal
        # it, and `pr_missing` drawn from that would be the false negative the
        # fail-closed rule exists to prevent
        # (speckit_pro_runner/helpers/read_only.py:1276-1277).
        "an entry's `number` is a string",
        {
            "ok": True,
            "pull_requests": [{"number": "438", "url": DRAFT_PR_URL, "state": "OPEN"}],
        },
    ),
)

# The workflow states whose resolved stages differ, so stage invariance is
# asserted across auto-detection and argv alike rather than one happy path.
# (label, overview rows, argv)
CORROBORATION_STAGE_CASES = (
    ("auto-detected plan", PLANNING_INCOMPLETE, []),
    ("auto-detected implement", PLANNING_COMPLETE, []),
    ("an explicitly named stage", PLANNING_INCOMPLETE, ["--stage", "full"]),
)

# One observation per outcome class: agreement, a discrepancy that would stop
# the terminal step, a discrepancy of a different shape, and a query that could
# not answer. (label, observation)
STAGE_INVARIANCE_OBSERVATIONS = (
    ("a corroborated identity", {"ok": True, "pull_requests": [OPEN_438]}),
    ("a closed recorded number", {"ok": True, "pull_requests": [CLOSED_438]}),
    ("a competing open pull request", {"ok": True, "pull_requests": [OPEN_512]}),
    ("an unsuccessful query", {"ok": False, "reason": "gh not authenticated"}),
)

# (label, `Draft PR` row, observation)
ENVELOPE_KEY_CASES = (
    ("a corroborated run", DRAFT_PR_PRESENT_ROW, {"ok": True, "pull_requests": [OPEN_438]}),
    ("a run with no row to corroborate", "", OBSERVATION_ABSENT),
    ("a run that could not check", DRAFT_PR_PRESENT_ROW, OBSERVATION_ABSENT),
)

# The row's presence is the trigger, not the stage: a run carrying the row
# corroborates even when its stage came from an explicit `--stage`, and even
# when it resolves a stage with no emission terminal step at all
# (contracts/stage-corroboration.md:44-46, :204-207).
# (argv, the stage it resolves against a planning-complete workflow file)
CORROBORATION_TRIGGER_CASES = (
    ([], "implement"),
    (["--stage", "plan"], "plan"),
    (["--stage", "implement"], "implement"),
    (["--stage", "full"], "full"),
)


def overview_table(rows: tuple[tuple[str, str], ...]) -> str:
    lines = [
        "## Workflow Overview",
        "",
        "| Phase | Command | Status | Notes |",
        "|-------|---------|--------|-------|",
    ]
    lines.extend(f"| {phase} | `/speckit-run` | {status} | |" for phase, status in rows)
    return "\n".join(lines) + "\n"


def workflow_document(
    rows: tuple[tuple[str, str], ...], stage_row: str = "", draft_pr_row: str = ""
) -> str:
    return (
        "# Test Workflow\n\n"
        + overview_table(rows)
        + "\n### Basic Information\n\n| Field | Value |\n|-------|-------|\n"
        + "| **Branch** | `test-branch` |\n"
        + stage_row
        + draft_pr_row
    )


def draft_pr_document(draft_pr_row: str) -> str:
    """A workflow file whose `### Basic Information` also carries `Stage`.

    The sibling row is deliberate: the reader has to select by key, not by
    position, in a table that always holds more than one row.
    """
    return workflow_document(
        PLANNING_ROWS_TERMINAL + (GATE_TERMINAL,),
        stage_row="| **Stage** | implement |\n",
        draft_pr_row=draft_pr_row,
    )


def read_draft_pr_row(text: str) -> dict[str, object] | None:
    """Read the `Draft PR` row through the preprocessing every consumer applies.

    `workflow_stage_signals` blanks HTML comment spans before it splits, so a
    commented-out example can never become evidence. `workflow_draft_pr_row`
    takes those same `lines` and inherits the obligation rather than re-deriving
    it, which is what keeps it a near-duplicate of `workflow_recorded_stage`
    instead of a second parser (contracts/draft-pr-row.md:80-90).
    """
    return read_only.workflow_draft_pr_row(read_only.HTML_COMMENT_RE.sub("", text).splitlines())


def distribution_argv(
    distribution: str,
    *,
    from_phase: str | None = None,
    spec: str | None = None,
    stage: str | None = None,
    mode: str | None = None,
) -> list[str]:
    """One distribution's documented synopsis ordering of the same invocation.

    Claude names `--stage` before the `--strict | --advisory` pair; Codex names
    it after. Both begin at the workflow path and neither carries the leading
    command token (contracts/stage-invocation.md:15-19, :39-43, :24-34).
    """
    argv: list[str] = [WORKFLOW_FILE]
    if from_phase is not None:
        argv += ["--from-phase", from_phase]
    if spec is not None:
        argv += ["--spec", spec]
    stage_tokens = ["--stage", stage] if stage is not None else []
    mode_tokens = [mode] if mode is not None else []
    if distribution == "claude":
        return argv + stage_tokens + mode_tokens
    if distribution == "codex":
        return argv + mode_tokens + stage_tokens
    raise ValueError(f"unknown distribution: {distribution!r}")


def resolve_stage(
    text: str,
    args: list[str] | None = None,
    *,
    observation: object = OBSERVATION_ABSENT,
) -> dict[str, object]:
    """Run the operation against a workflow file written under its own root.

    The root is resolved because the descriptor-guarded reader resolves the repo
    root but not the target, so an unresolved symlinked temp path (macOS `/var`
    -> `/private/var`) would fail the containment check on its own.

    `observation` is the optional `inputs.pr_observation` FR-011 corroboration
    reads. The sentinel default leaves the key out of the request entirely,
    which is the state every invocation predating that contract is in, and the
    state the operation must still resolve a stage from
    (contracts/stage-corroboration.md:52-81).
    """
    with tempfile.TemporaryDirectory() as root:
        repo_root = Path(root).resolve()
        (repo_root / "stage-workflow.md").write_text(text, encoding="utf-8")
        inputs: dict[str, object] = {
            "workflow_file": "stage-workflow.md",
            "autopilot_args": args or [],
        }
        if observation is not OBSERVATION_ABSENT:
            inputs["pr_observation"] = observation
        return read_only.resolve_autopilot_stage(inputs, repo_root)


def resolve_envelope(
    text: str,
    args: list[str] | None = None,
    *,
    observation: object = OBSERVATION_ABSENT,
) -> dict[str, object]:
    """The exit-0 JSON envelope of a resolution, asserted to have succeeded."""
    result = resolve_stage(text, args, observation=observation)
    if result["exit_code"] != 0:
        raise AssertionError(f"expected exit 0, got {result['exit_code']}: {result['stderr']}")
    return json.loads(result["stdout"])


def runner_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(PLUGIN_ROOT) if not existing else f"{PLUGIN_ROOT}{os.pathsep}{existing}"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_runner(inputs: dict[str, object]) -> dict[str, object]:
    """Dispatch a `resolve-autopilot-stage` request through the real runner."""
    request = {
        "schema_version": "1.0",
        "request_id": "test-resolve-autopilot-stage",
        "helper_id": "resolve-autopilot-stage",
        "operation": "resolve-autopilot-stage",
        "mode": "read_only",
        "inputs": inputs,
    }
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=json.dumps(request),
        cwd=REPO_ROOT,
        env=runner_env(),
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )
    return json.loads(completed.stdout)


def load_coverage_validator():
    """Import the shipped phase-coverage validator so vocabulary locks read real bytes."""
    spec = importlib.util.spec_from_file_location(
        "speckit_autopilot_phase_coverage_stage_lock", COVERAGE_VALIDATOR
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class StageVocabularyAndArgvTests(unittest.TestCase):
    """T003 — the closed vocabulary, the phase ranges, and argv resolution."""

    def test_stage_vocabulary_is_closed_to_three_lowercase_tokens(self) -> None:
        self.assertEqual(read_only.AUTOPILOT_STAGES, STAGE_VOCABULARY)

    def test_stage_phase_ranges_match_the_data_model(self) -> None:
        self.assertEqual(dict(read_only.AUTOPILOT_STAGE_PHASES), STAGE_PHASE_RANGES)

    def test_explicit_stage_argument_resolves_from_argv(self) -> None:
        for argv, stage, from_phase in ARGV_RESOLUTION_CASES:
            with self.subTest(argv=argv):
                parsed = read_only.parse_stage_args(argv)
                self.assertIsNone(parsed["error"], parsed["error"])
                self.assertEqual(parsed["stage"], stage)
                self.assertEqual(parsed["from_phase"], from_phase)

    def test_invalid_stage_arguments_are_rejected_before_any_phase_work(self) -> None:
        for argv, message in ARGV_REJECTION_CASES:
            with self.subTest(argv=argv):
                self.assertEqual(read_only.parse_stage_args(argv)["error"], message)

    def test_from_phase_never_conflicts_with_an_auto_detected_stage(self) -> None:
        for argv in AUTO_DETECTED_FROM_PHASE_CASES:
            with self.subTest(argv=argv):
                parsed = read_only.parse_stage_args(argv)
                self.assertIsNone(parsed["error"], parsed["error"])
                self.assertIsNone(parsed["stage"])


class RequestLayerDiagnosticTests(unittest.TestCase):
    """T004 — request-layer diagnostics are not exit codes."""

    def test_malformed_autopilot_arguments_yield_an_invalid_input_diagnostic(self) -> None:
        response = run_runner({"workflow_file": WORKFLOW_FILE, "autopilot_args": "--stage plan"})
        self.assertEqual(response["status"], "input_error")
        self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["invalid_input"])

    def test_path_outside_the_trust_boundary_yields_a_diagnostic_and_no_exit_code(self) -> None:
        response = run_runner({"workflow_file": OUTSIDE_TRUST_BOUNDARY})
        self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["unsupported_path"])
        # `unsupported_path` never reaches the helper, so no helper exit code is
        # recorded, and it has no entry in the runner's exit-code map. A fixture
        # asserting exit 2 for a trust-boundary path would be asserting against
        # the wrong surface entirely.
        self.assertIsNone(response["data"].get("exit_code"))
        self.assertNotIn("unsupported_path", read_only.EXIT_DIAGNOSTIC.values())

    def test_operation_rejections_are_the_only_exit_two(self) -> None:
        response = run_runner(
            {"workflow_file": WORKFLOW_FILE, "autopilot_args": ["--stage", "planning"]}
        )
        self.assertEqual(response["data"]["exit_code"], 2)
        self.assertEqual(
            response["data"]["stderr"]["text"],
            "error: unrecognized stage 'planning' — accepted values: plan, implement, full\n",
        )

    def test_registered_operation_resolves_an_explicit_stage_through_the_runner(self) -> None:
        response = run_runner(
            {"workflow_file": WORKFLOW_FILE, "autopilot_args": ["--stage", "plan"]}
        )
        self.assertEqual(response["status"], "ok")
        envelope = response["data"]["stdout_json"]
        self.assertEqual(envelope["tool"], "resolve-autopilot-stage")
        self.assertEqual(envelope["stage"], "plan")
        self.assertEqual(envelope["source"], "argv")


class WorkflowStageSignalTests(unittest.TestCase):
    """T007 — the workflow-file reader and the FR-006a planning predicate."""

    def test_planning_predicate_covers_the_six_rows_plus_the_confidence_gate(self) -> None:
        for label, rows, complete, gate_status, first_open in PLANNING_PREDICATE_CASES:
            with self.subTest(case=label):
                signals = read_only.workflow_stage_signals(workflow_document(rows))
                self.assertTrue(signals["parsed"])
                self.assertEqual(signals["planning_complete"], complete)
                self.assertEqual(signals["confidence_gate_status"], gate_status)
                self.assertEqual(signals["first_open"], first_open)

    def test_recorded_stage_reads_the_basic_information_row(self) -> None:
        for label, stage_row, expected in RECORDED_STAGE_CASES:
            with self.subTest(case=label):
                text = workflow_document(
                    PLANNING_ROWS_TERMINAL + (GATE_TERMINAL,), stage_row=stage_row
                )
                signals = read_only.workflow_stage_signals(text)
                self.assertTrue(signals["parsed"])
                self.assertEqual(signals["recorded_stage"], expected)

    def test_absent_stage_row_is_not_an_error(self) -> None:
        result = resolve_stage(
            workflow_document(PLANNING_ROWS_TERMINAL + (GATE_TERMINAL,)),
            ["--stage", "plan"],
        )
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["stderr"], "")
        self.assertIsNone(json.loads(result["stdout"])["recorded_stage"])

    def test_unparseable_overview_table_is_rejected_rather_than_defaulted(self) -> None:
        for label, text in UNPARSEABLE_WORKFLOW_TEXTS:
            with self.subTest(case=label):
                self.assertFalse(read_only.workflow_stage_signals(text)["parsed"])
                result = resolve_stage(text)
                self.assertEqual(result["exit_code"], 2)
                self.assertTrue(result["stderr"].startswith("error: "), result["stderr"])
                self.assertEqual(result["stdout"], "")

    def test_unreadable_workflow_file_is_rejected_rather_than_defaulted(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            result = read_only.resolve_autopilot_stage(
                {"workflow_file": "no-such-workflow.md"}, Path(root).resolve()
            )
        self.assertEqual(result["exit_code"], 2)
        self.assertTrue(result["stderr"].startswith("error: "), result["stderr"])

    def test_commented_out_table_is_not_read_as_evidence(self) -> None:
        text = "<!--\n" + overview_table(PLANNING_ROWS_TERMINAL) + "-->\n"
        self.assertFalse(read_only.workflow_stage_signals(text)["parsed"])

    def test_terminal_status_vocabulary_matches_the_shipped_validator(self) -> None:
        module = load_coverage_validator()
        self.assertEqual(
            sorted(read_only.AUTOPILOT_TERMINAL_STATUSES),
            sorted(module.WORKFLOW_TERMINAL_STATUSES),
            "runner terminal-status vocabulary drifted from the shipped validator",
        )

    def test_confidence_gate_is_in_the_predicate_despite_being_advisory_for_ordering(
        self,
    ) -> None:
        module = load_coverage_validator()
        # The shipped validator excludes the row from the ORDERING rule because
        # the phase loop does not drive it. That exclusion is scoped to ordering
        # and must not be inherited here: whether the loop drives the row is a
        # different question from whether planning finished.
        self.assertIn("Confidence Gate", module.WORKFLOW_ADVISORY_PHASES)
        self.assertIn("Confidence Gate", read_only.AUTOPILOT_PLANNING_PREDICATE_PHASES)


class DraftPrRowTests(unittest.TestCase):
    """T012 — the `Draft PR` row of `### Basic Information` (FR-009).

    The row is the sole store of the pull-request identity: there is no
    state-file mirror, so whatever this reader gets wrong is wrong everywhere.
    """

    def test_present_row_parses_number_url_and_gap_note(self) -> None:
        for label, row, expected in DRAFT_PR_ROW_CASES:
            with self.subTest(case=label):
                self.assertEqual(read_draft_pr_row(draft_pr_document(row)), expected)

    def test_absent_row_returns_none_and_is_not_an_error(self) -> None:
        # Absence means no pull request has been opened for this feature. That
        # is information, never a fault — the same shape `Stage` already uses
        # for "no run yet" (contracts/draft-pr-row.md:44-52). The scaffold
        # template ships no placeholder row, so this is the common state.
        for label, text in (
            ("a Basic Information table carrying only Branch and Stage", draft_pr_document("")),
            ("no Basic Information table at all", overview_table(PLANNING_ROWS_TERMINAL)),
            ("an empty document", ""),
        ):
            with self.subTest(case=label):
                self.assertIsNone(read_draft_pr_row(text))

    def test_commented_out_row_is_not_read_as_present(self) -> None:
        # Comment spans are blanked before the table is parsed, which is why a
        # commented-out example row in the scaffold template would not help:
        # it could never be read as evidence (contracts/draft-pr-row.md:54-58).
        # `test_commented_out_table_is_not_read_as_evidence` above proves the
        # same property for the `## Workflow Overview` table.
        self.assertEqual(
            read_draft_pr_row(draft_pr_document(DRAFT_PR_PRESENT_ROW)), DRAFT_PR_IDENTITY
        )
        for label, row in (
            ("the row alone is commented out", f"<!-- {DRAFT_PR_PRESENT_ROW.rstrip()} -->\n"),
            ("the row sits inside a multi-line comment", f"<!--\n{DRAFT_PR_PRESENT_ROW}-->\n"),
        ):
            with self.subTest(case=label):
                self.assertIsNone(read_draft_pr_row(draft_pr_document(row)))

    def test_gap_note_after_the_link_still_parses_the_identity(self) -> None:
        # FR-004 makes a shortfall visible in this row, so the note is ordinary
        # rather than exceptional. The identity has to survive it intact: a
        # number or URL corrupted by the prose beside it would send FR-011
        # corroboration at the wrong pull request.
        for label, note, expected_note in DRAFT_PR_GAP_NOTE_CASES:
            with self.subTest(case=label):
                record = read_draft_pr_row(
                    draft_pr_document(f"| **Draft PR** | [#438]({DRAFT_PR_URL}) {note} |\n")
                )
                self.assertEqual(
                    record, {"number": 438, "url": DRAFT_PR_URL, "gap_note": expected_note}
                )

    def test_malformed_value_yields_none_rather_than_a_traceback(self) -> None:
        # A raised exception fails these subTests as errors, which is exactly
        # the outcome the contract forbids (contracts/draft-pr-row.md:117).
        for label, value in MALFORMED_DRAFT_PR_VALUES:
            with self.subTest(case=label):
                text = draft_pr_document(f"| **Draft PR** | {value} |\n")
                self.assertIsNone(read_draft_pr_row(text))


class DraftPrCorroborationTests(unittest.TestCase):
    """T035 — FR-011: corroborating the recorded identity against one observation.

    The orchestrator takes the observation; this operation only classifies it.
    Corroboration never changes the resolved stage, never blocks resolution, and
    never stops the run — a discrepancy is reported here and acted on at the
    terminal step, which is the only place a pull request is ever written
    (contracts/stage-corroboration.md:176-210).
    """

    def corroboration(
        self,
        text: str,
        args: list[str] | None = None,
        *,
        observation: object = OBSERVATION_ABSENT,
    ) -> object:
        """The `corroboration` object of an exit-0 envelope, or None when absent.

        `.get` rather than `[...]`: until the object exists the key is simply
        not there, and `None != {...}` reports the missing surface far more
        legibly than a KeyError traceback, which reads like a broken fixture.
        """
        return resolve_envelope(text, args, observation=observation).get("corroboration")

    def test_the_status_vocabulary_is_closed_to_six_lowercase_tokens(self) -> None:
        # Named on the module, the way the stage vocabulary is: a set collected
        # from whatever the fixtures happen to produce could never prove that a
        # seventh status does not exist (contracts/stage-corroboration.md:141-145).
        self.assertEqual(read_only.AUTOPILOT_CORROBORATION_STATUSES, CORROBORATION_STATUSES)
        self.assertEqual(
            tuple(status for _label, status, *_rest in STATUS_WITNESS_CASES),
            CORROBORATION_STATUSES,
            "every status in the closed vocabulary needs its own witness input",
        )

    def test_each_status_is_produced_by_its_own_input(self) -> None:
        for label, _status, row, observation, expected in STATUS_WITNESS_CASES:
            with self.subTest(case=label):
                self.assertEqual(
                    self.corroboration(draft_pr_document(row), observation=observation),
                    expected,
                )

    def test_a_successful_observation_is_classified_against_the_recorded_identity(self) -> None:
        for label, observation, expected in SUCCESSFUL_OBSERVATION_CASES:
            with self.subTest(case=label):
                self.assertEqual(
                    self.corroboration(
                        draft_pr_document(DRAFT_PR_PRESENT_ROW), observation=observation
                    ),
                    expected,
                )

    def test_an_extra_open_pull_request_outranks_every_later_rule(self) -> None:
        # Each observation below also satisfies the later rule its label names,
        # so a resolver evaluating the rules in any other order reports a
        # different status here rather than passing by luck.
        for label, observation, outranked in PRECEDENCE_CASES:
            with self.subTest(case=label):
                self.assertEqual(
                    self.corroboration(
                        draft_pr_document(DRAFT_PR_PRESENT_ROW), observation=observation
                    ),
                    CORROBORATION_IDENTITY_MISMATCH_SECOND_PR,
                    f"rule 1 must be evaluated before {outranked}",
                )

    def test_an_unsuccessful_observation_is_skipped_and_never_a_discrepancy(self) -> None:
        for label, reason in UNSUCCESSFUL_OBSERVATION_REASONS:
            with self.subTest(case=label):
                record = self.corroboration(
                    draft_pr_document(DRAFT_PR_PRESENT_ROW),
                    observation={"ok": False, "reason": reason},
                )
                # The supplied reason is echoed verbatim: §6 prints it, and the
                # operator acts on which failure it was, not on the fact of one.
                self.assertEqual(
                    record, {**CORROBORATION_SKIPPED_NO_OBSERVATION, "reason": reason}
                )
                # None of these is evidence the recorded pull request is gone,
                # which is precisely what a discrepancy status would assert.
                self.assertNotIn(record["status"], CORROBORATION_DISCREPANCIES)

    def test_an_absent_observation_is_skipped_with_the_recorded_identity_intact(self) -> None:
        # A `skipped` run still knows which pull request it failed to reach, and
        # §7 needs that: the terminal step refreshes the recorded one when the
        # tool can be reached, and never treats `skipped` as grounds to create a
        # second (contracts/stage-corroboration.md:182).
        for label, observation in (
            ("the request carries no `pr_observation` key", OBSERVATION_ABSENT),
            # An explicit JSON null supplies no observation either, and the two
            # are indistinguishable to any reader that asks for the key's value.
            ("the request carries an explicit null", None),
        ):
            with self.subTest(case=label):
                self.assertEqual(
                    self.corroboration(
                        draft_pr_document(DRAFT_PR_PRESENT_ROW), observation=observation
                    ),
                    CORROBORATION_SKIPPED_NO_OBSERVATION,
                )

    def test_an_absent_draft_pr_row_yields_no_record_and_reads_no_observation(self) -> None:
        # The row's presence is what triggers the observation, so a run without
        # one has nothing to corroborate and falls through to FR-007's separate
        # emission-time existence test instead (…:25-27, :36-41).
        for label, observation in NO_RECORD_OBSERVATIONS:
            with self.subTest(case=label):
                self.assertEqual(
                    self.corroboration(draft_pr_document(""), observation=observation),
                    CORROBORATION_NO_RECORD,
                )

    def test_a_malformed_observation_is_skipped_rather_than_a_traceback(self) -> None:
        # A raised exception fails these subTests as errors, which is exactly
        # the outcome the fail-closed rule forbids: the operation must survive
        # whatever the orchestrator hands it, because a traceback here would
        # stop a run over a shape `gh` changed (…:82-85).
        for label, observation in MALFORMED_OBSERVATIONS:
            with self.subTest(case=label):
                self.assertEqual(
                    self.corroboration(
                        draft_pr_document(DRAFT_PR_PRESENT_ROW), observation=observation
                    ),
                    CORROBORATION_SKIPPED_UNUSABLE,
                )

    def test_the_resolved_stage_is_identical_with_and_without_the_observation(self) -> None:
        # Corroboration reports; it never decides. The eight pre-existing keys
        # are compared whole, so a stage, source, or basis perturbed by the
        # observation fails here rather than surfacing later as a run that
        # started the wrong phase (…:206-210).
        for label, rows, argv in CORROBORATION_STAGE_CASES:
            text = workflow_document(rows, draft_pr_row=DRAFT_PR_PRESENT_ROW)
            baseline = resolve_envelope(text, argv)
            for observation_label, observation in STAGE_INVARIANCE_OBSERVATIONS:
                with self.subTest(case=f"{label} / {observation_label}"):
                    envelope = resolve_envelope(text, argv, observation=observation)
                    # Both runs corroborate; only their verdicts may differ.
                    self.assertIn("corroboration", baseline)
                    self.assertIn("corroboration", envelope)
                    self.assertEqual(
                        {key: envelope[key] for key in PRE_EXISTING_ENVELOPE_KEYS},
                        {key: baseline[key] for key in PRE_EXISTING_ENVELOPE_KEYS},
                    )

    def test_the_envelope_adds_corroboration_as_a_ninth_key(self) -> None:
        # The object is ALWAYS present, so a run that could not check stays
        # distinguishable from one that checked and agreed (…:112-114).
        # Asserted on the operation's own stdout, which writes the keys in
        # source order; the runner re-serializes its envelope with sorted keys,
        # so key order is not a property to assert over there.
        for label, row, observation in ENVELOPE_KEY_CASES:
            with self.subTest(case=label):
                envelope = resolve_envelope(draft_pr_document(row), observation=observation)
                self.assertEqual(tuple(envelope), ENVELOPE_KEYS)

    def test_the_row_and_not_the_stage_triggers_corroboration(self) -> None:
        # Four different resolved stages, one verdict: `plan` is the only stage
        # with an emission terminal step, and corroboration is reported on the
        # other three all the same (…:44-46, :204-207).
        for argv, stage in CORROBORATION_TRIGGER_CASES:
            with self.subTest(argv=argv):
                envelope = resolve_envelope(
                    draft_pr_document(DRAFT_PR_PRESENT_ROW),
                    argv,
                    observation={"ok": True, "pull_requests": [OPEN_438]},
                )
                self.assertEqual(envelope["stage"], stage)
                self.assertEqual(envelope.get("corroboration"), CORROBORATION_MATCH)

    def test_the_registered_operation_carries_the_observation_through_the_runner(self) -> None:
        # The new input is one optional key on the same stdin request; argv
        # stays reserved for `--help` and `--version` (…:52-55). The real runner
        # has to hand it through untouched and carry the ninth key back. The
        # The workflow fixture omits the `Draft PR` row, so `no_record` is
        # the honest verdict for it — and that premise is asserted, not assumed,
        # so a row added there later fails loudly instead of mysteriously.
        observation = {"ok": True, "pull_requests": [OPEN_438]}
        self.assertIsNone(
            read_draft_pr_row((REPO_ROOT / WORKFLOW_FILE).read_text(encoding="utf-8"))
        )
        response = run_runner(
            {
                "workflow_file": WORKFLOW_FILE,
                "autopilot_args": ["--stage", "plan"],
                "pr_observation": observation,
            }
        )
        self.assertEqual(response["status"], "ok")
        self.assertEqual(
            response["data"]["stdin_request"]["inputs"]["pr_observation"], observation
        )
        self.assertEqual(
            response["data"]["stdout_json"].get("corroboration"), CORROBORATION_NO_RECORD
        )


class ConfidenceGateVerdictTests(unittest.TestCase):
    """T024 — `confidence_gate_status` echoes the status row, never the prose."""

    def test_envelope_echoes_the_confidence_gate_status_row(self) -> None:
        for label, rows, expected, complete in CONFIDENCE_GATE_VERDICT_CASES:
            with self.subTest(case=label):
                envelope = resolve_envelope(
                    workflow_document(rows) + GATE_RECORD_PROSE, ["--stage", "implement"]
                )
                self.assertEqual(envelope["confidence_gate_status"], expected)
                self.assertEqual(envelope["planning_complete"], complete)

    def test_identical_gate_prose_records_two_opposite_verdicts(self) -> None:
        # One prose block, two outcomes. A composite of 0.88 proceeds under
        # advisory mode and stops under strict, so the record below is a truthful
        # description of BOTH runs. Reading it as the verdict would report
        # `proceed` for the run that was refused.
        proceeded = resolve_envelope(
            workflow_document(PLANNING_ROWS_TERMINAL + (GATE_TERMINAL,)) + GATE_RECORD_PROSE
        )
        stopped = resolve_envelope(
            workflow_document(PLANNING_ROWS_TERMINAL + (GATE_BLOCKED,)) + GATE_RECORD_PROSE
        )
        self.assertEqual(proceeded["confidence_gate_status"], "✅ Complete")
        self.assertEqual(stopped["confidence_gate_status"], "⚠️ Blocked")
        for envelope in (proceeded, stopped):
            with self.subTest(verdict=envelope["confidence_gate_status"]):
                self.assertNotIn("proceed", str(envelope["confidence_gate_status"]))
                self.assertNotIn("0.88", str(envelope["confidence_gate_status"]))

    def test_the_rows_own_notes_cell_is_not_the_verdict(self) -> None:
        # A notes cell may carry `composite 0.88, verdict **proceed**`
        # in its Notes cell, immediately beside the status. The status cell is
        # the verdict; the cell next to it is commentary about the same run.
        blocked_row_with_proceed_notes = (
            "## Workflow Overview\n\n"
            "| Phase | Command | Status | Notes |\n"
            "|-------|---------|--------|-------|\n"
            + "".join(
                f"| {phase} | `/speckit-run` | {status} | |\n"
                for phase, status in PLANNING_ROWS_TERMINAL
            )
            + "| Confidence Gate | G6.5 | ⚠️ Blocked |"
            " Advisory mode, composite 0.88, verdict **proceed** |\n"
        )
        envelope = resolve_envelope(blocked_row_with_proceed_notes)
        self.assertEqual(envelope["confidence_gate_status"], "⚠️ Blocked")
        self.assertFalse(envelope["planning_complete"])

    def test_absent_row_is_null_even_when_the_prose_record_names_a_verdict(self) -> None:
        envelope = resolve_envelope(
            workflow_document(PLANNING_ROWS_TERMINAL + (IMPLEMENT_PENDING,)) + GATE_RECORD_PROSE
        )
        self.assertIsNone(envelope["confidence_gate_status"])

    def test_the_field_is_the_same_row_the_planning_predicate_reads(self) -> None:
        # FR-006a's predicate and this field must never disagree: a run told the
        # gate is blocked while the predicate reports planning complete would
        # cross the boundary the gate refused.
        for label, rows, expected, _complete in CONFIDENCE_GATE_VERDICT_CASES:
            with self.subTest(case=label):
                text = workflow_document(rows) + GATE_RECORD_PROSE
                signals = read_only.workflow_stage_signals(text)
                self.assertEqual(signals["confidence_gate_status"], expected)
                self.assertEqual(resolve_envelope(text)["confidence_gate_status"], expected)

    def test_a_non_terminal_verdict_is_the_open_row_the_predicate_reports(self) -> None:
        text = workflow_document(PLANNING_ROWS_TERMINAL + (GATE_BLOCKED, IMPLEMENT_PENDING))
        signals = read_only.workflow_stage_signals(text)
        self.assertEqual(
            signals["first_open"],
            (read_only.AUTOPILOT_GATE_PHASE, signals["confidence_gate_status"]),
        )
        self.assertNotIn(
            signals["confidence_gate_status"], read_only.AUTOPILOT_TERMINAL_STATUSES
        )


class AutoDetectionTests(unittest.TestCase):
    """T030 — FR-006/SC-004: a bare invocation resolves and reports its stage."""

    def test_auto_detection_resolves_the_expected_stage_and_source(self) -> None:
        for label, rows, argv, stage, source, _named in AUTO_DETECTION_CASES:
            with self.subTest(case=label):
                envelope = resolve_envelope(workflow_document(rows), argv)
                self.assertEqual(envelope["stage"], stage)
                self.assertEqual(envelope["source"], source)

    def test_the_basis_names_the_first_non_terminal_phase_and_its_status(self) -> None:
        # The basis is what the orchestrator prints before phase work begins
        # (FR-006). "auto-detected plan" is not a reason; naming the row that
        # decided it is, and it is what an operator needs to act on.
        for label, rows, argv, _stage, source, named in AUTO_DETECTION_CASES:
            if source != "auto-detect" or not named:
                continue
            with self.subTest(case=label):
                basis = str(resolve_envelope(workflow_document(rows), argv)["basis"])
                for token in named:
                    self.assertIn(token, basis, f"basis does not name {token!r}: {basis!r}")

    def test_a_strict_mode_gate_stop_never_auto_detects_implement(self) -> None:
        envelope = resolve_envelope(workflow_document(STRICT_MODE_STOP))
        self.assertEqual(envelope["stage"], "plan")
        self.assertEqual(envelope["source"], "auto-detect")
        self.assertFalse(envelope["planning_complete"])
        self.assertEqual(envelope["confidence_gate_status"], "⚠️ Blocked")
        # The six planning rows really are terminal — `plan` is decided by the
        # gate row alone, which is the whole point of FR-006a's predicate set.
        signals = read_only.workflow_stage_signals(workflow_document(PLANNING_ROWS_TERMINAL))
        self.assertTrue(signals["planning_complete"])

    def test_an_explicit_stage_reports_argv_and_a_basis_naming_the_flag(self) -> None:
        for stage in STAGE_VOCABULARY:
            with self.subTest(stage=stage):
                envelope = resolve_envelope(
                    workflow_document(PLANNING_INCOMPLETE), ["--stage", stage]
                )
                self.assertEqual(envelope["stage"], stage)
                self.assertEqual(envelope["source"], "argv")
                self.assertEqual(envelope["basis"], f"explicit --stage {stage}")

    def test_the_basis_reports_completion_when_no_row_is_open(self) -> None:
        envelope = resolve_envelope(workflow_document(PLANNING_COMPLETE))
        self.assertEqual(envelope["stage"], "implement")
        self.assertNotIn("None", str(envelope["basis"]))
        self.assertTrue(str(envelope["basis"]).startswith("auto-detect"), envelope["basis"])


class PlanningStageCanonicalListTests(unittest.TestCase):
    """T013 — FR-011: out-of-stage entries are marked, never truncated."""

    def planning_stage_state(self, *, prefix_the_name: bool = False) -> dict[str, object]:
        """A planning-stage `autopilot-state.json` plan array.

        Every canonical entry is present. The Implement phase and every `Post:`
        entry carry the out-of-stage marker. With ``prefix_the_name`` the marker
        is (wrongly) moved into the name field, which is the negative control for
        constraint (a).
        """
        plan: list[dict[str, str]] = [
            {"step": name, "status": "completed"} for name in IN_STAGE_ENTRIES
        ]
        for name in OUT_OF_STAGE_ENTRIES:
            plan.append(
                {
                    "step": f"skipped: {name}" if prefix_the_name else name,
                    "status": OUT_OF_STAGE_STATUS,
                }
            )
        return {"plan": plan}

    def test_marked_entries_keep_byte_identical_canonical_names(self) -> None:
        module = load_coverage_validator()
        state = self.planning_stage_state()
        result = module.validate_state(module.extract_plan_steps(state))
        for key, values in sorted(result.items()):
            with self.subTest(check=key):
                self.assertEqual([], values, f"{key}: {values}")

    def test_a_skipped_prefixed_name_reads_as_a_missing_checkpoint(self) -> None:
        # The coverage guard matches post-implementation checkpoints by exact
        # name equality (validate-autopilot-phase-coverage.py:616), so moving the
        # marker into the name is not a cosmetic difference — it fails every
        # planning-stage run at the pre-final audit.
        module = load_coverage_validator()
        result = module.validate_state(
            module.extract_plan_steps(self.planning_stage_state(prefix_the_name=True))
        )
        self.assertEqual(list(CANONICAL_POST_ENTRIES), result["missing_state_post_items"])
        self.assertEqual(["Phase 7: Implement"], result["missing_state_prefixes"])

    def test_the_marker_occupies_the_status_field_with_a_skipped_reason_shape(self) -> None:
        plan = self.planning_stage_state()["plan"]
        marked = [item for item in plan if item["status"] != "completed"]
        self.assertEqual(list(OUT_OF_STAGE_ENTRIES), [item["step"] for item in marked])
        for item in marked:
            with self.subTest(entry=item["step"]):
                self.assertTrue(item["status"].startswith("skipped: "), item["status"])
                self.assertTrue(item["status"].removeprefix("skipped: ").strip())

    def test_the_marker_text_carries_no_pending_substring_in_any_casing(self) -> None:
        module = load_coverage_validator()
        plan = self.planning_stage_state()["plan"]
        self.assertEqual([], module._pending_value_paths(plan, "plan"))
        # The guard flags any string value containing `pending` case-insensitively,
        # so a marker naming the work as pending would be reported as a violation.
        self.assertEqual(
            ["plan"], module._pending_value_paths("skipped: implementation Pending", "plan")
        )

    def test_task_list_canonical_documents_the_out_of_stage_marking_rules(self) -> None:
        text = TASK_LIST_CANONICAL_DOC.read_text(encoding="utf-8")
        missing = [rule for rule in TASK_LIST_OUT_OF_STAGE_RULES if rule not in text]
        self.assertEqual(
            [],
            missing,
            "references/task-list-canonical.md does not state: " + "; ".join(missing),
        )


class CrossDistributionArgvParityTests(unittest.TestCase):
    """T034 — FR-015a/SC-007: both synopsis orderings resolve identically."""

    def argv_pair(self, case: tuple[object, ...]) -> tuple[list[str], list[str]]:
        _label, from_phase, spec, stage, mode = case
        kwargs = {"from_phase": from_phase, "spec": spec, "stage": stage, "mode": mode}
        return distribution_argv("claude", **kwargs), distribution_argv("codex", **kwargs)

    def test_the_two_orderings_are_genuinely_different_token_sequences(self) -> None:
        # Negative control. If the builder emitted one sequence for both
        # distributions, every parity assertion below would hold vacuously.
        differing = [case[0] for case in PARITY_INVOCATIONS if len(set(map(tuple, self.argv_pair(case)))) > 1]
        # The orderings diverge exactly when a stage and a mode flag co-occur.
        expected = [label for label, _fp, _spec, stage, mode in PARITY_INVOCATIONS if stage and mode]
        self.assertEqual(expected, differing)
        self.assertTrue(differing, "no fixture exercises the ordering difference")

    def test_both_orderings_parse_to_the_same_stage_and_from_phase(self) -> None:
        for case in PARITY_INVOCATIONS:
            label, from_phase, _spec, stage, _mode = case
            with self.subTest(case=label):
                claude_argv, codex_argv = self.argv_pair(case)
                claude = read_only.parse_stage_args(claude_argv)
                codex = read_only.parse_stage_args(codex_argv)
                self.assertIsNone(claude["error"], claude["error"])
                self.assertEqual(claude, codex)
                # Pin the absolute result too, so a parser that degraded both
                # orderings to the same wrong answer is still caught.
                self.assertEqual(claude["stage"], stage)
                self.assertEqual(claude["from_phase"], from_phase)

    def test_both_orderings_resolve_identically_through_the_one_operation(self) -> None:
        for workflow_label, rows in PARITY_WORKFLOWS:
            document = workflow_document(rows)
            for case in PARITY_INVOCATIONS:
                with self.subTest(workflow=workflow_label, case=case[0]):
                    claude_argv, codex_argv = self.argv_pair(case)
                    self.assertEqual(
                        resolve_envelope(document, claude_argv),
                        resolve_envelope(document, codex_argv),
                    )

    def test_both_orderings_reject_identically_before_any_phase_work(self) -> None:
        # A run rejected under one ordering and accepted under the other is the
        # silent divergence FR-015a exists to prevent, so the rejection text is
        # compared as a whole, not merely its presence.
        for label, stage, from_phase in PARITY_REJECTIONS:
            with self.subTest(case=label):
                kwargs = {"stage": stage, "from_phase": from_phase, "mode": "--strict"}
                claude = read_only.parse_stage_args(distribution_argv("claude", **kwargs))
                codex = read_only.parse_stage_args(distribution_argv("codex", **kwargs))
                self.assertIsNotNone(claude["error"])
                self.assertEqual(claude, codex)

    def test_the_registered_runner_resolves_both_orderings_identically(self) -> None:
        # Parity is over the one operation both distributions reach by identifier
        # (FR-012), asserted through the real runner rather than the helper alone.
        envelopes = []
        for distribution in ("claude", "codex"):
            response = run_runner(
                {
                    "workflow_file": WORKFLOW_FILE,
                    "autopilot_args": distribution_argv(
                        distribution, spec="FEATURE-001", stage="plan", mode="--strict"
                    ),
                }
            )
            self.assertEqual(response["status"], "ok")
            envelopes.append(response["data"]["stdout_json"])
        self.assertEqual(envelopes[0], envelopes[1])
        self.assertEqual(envelopes[0]["tool"], "resolve-autopilot-stage")
        self.assertEqual(envelopes[0]["stage"], "plan")
        self.assertEqual(envelopes[0]["source"], "argv")


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for case in (
        StageVocabularyAndArgvTests,
        RequestLayerDiagnosticTests,
        WorkflowStageSignalTests,
        DraftPrRowTests,
        DraftPrCorroborationTests,
        ConfidenceGateVerdictTests,
        AutoDetectionTests,
        PlanningStageCanonicalListTests,
        CrossDistributionArgvParityTests,
    ):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-autopilot-stage-resolution")


if __name__ == "__main__":
    raise SystemExit(main())
