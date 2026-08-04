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
WORKFLOW_FILE = "docs/ai/specs/.process/ART-006-workflow.md"
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
    (["--from-phase", "tasks", "--spec", "ART-006", "--stage", "plan"], "plan", "tasks"),
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
    ("stage plan with a spec and --advisory", None, "ART-006", "plan", "--advisory"),
    ("stage plan with an in-range --from-phase", "analyze", None, "plan", "--strict"),
    ("stage implement with an in-range --from-phase", "implement", None, "implement", "--advisory"),
    # No stage named: rank 2 decides, and the mode flag must not perturb it.
    ("auto-detect with --from-phase implement", "implement", None, None, "--strict"),
    ("auto-detect with a spec and a mode flag", None, "ART-006", None, "--advisory"),
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


def overview_table(rows: tuple[tuple[str, str], ...]) -> str:
    lines = [
        "## Workflow Overview",
        "",
        "| Phase | Command | Status | Notes |",
        "|-------|---------|--------|-------|",
    ]
    lines.extend(f"| {phase} | `/speckit-run` | {status} | |" for phase, status in rows)
    return "\n".join(lines) + "\n"


def workflow_document(rows: tuple[tuple[str, str], ...], stage_row: str = "") -> str:
    return (
        "# Test Workflow\n\n"
        + overview_table(rows)
        + "\n### Basic Information\n\n| Field | Value |\n|-------|-------|\n"
        + "| **Branch** | `test-branch` |\n"
        + stage_row
    )


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


def resolve_stage(text: str, args: list[str] | None = None) -> dict[str, object]:
    """Run the operation against a workflow file written under its own root.

    The root is resolved because the descriptor-guarded reader resolves the repo
    root but not the target, so an unresolved symlinked temp path (macOS `/var`
    -> `/private/var`) would fail the containment check on its own.
    """
    with tempfile.TemporaryDirectory() as root:
        repo_root = Path(root).resolve()
        (repo_root / "stage-workflow.md").write_text(text, encoding="utf-8")
        return read_only.resolve_autopilot_stage(
            {"workflow_file": "stage-workflow.md", "autopilot_args": args or []},
            repo_root,
        )


def resolve_envelope(text: str, args: list[str] | None = None) -> dict[str, object]:
    """The exit-0 JSON envelope of a resolution, asserted to have succeeded."""
    result = resolve_stage(text, args)
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
        # The shipped ART-006 row carries `composite 0.88, verdict **proceed**`
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
                        distribution, spec="ART-006", stage="plan", mode="--strict"
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
