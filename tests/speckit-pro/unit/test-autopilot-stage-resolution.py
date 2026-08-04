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

    def resolve(self, text: str, args: list[str] | None = None) -> dict[str, object]:
        """Run the operation against a workflow file written under its own root.

        The root is resolved because the descriptor-guarded reader resolves the
        repo root but not the target, so an unresolved symlinked temp path (macOS
        `/var` -> `/private/var`) would fail the containment check on its own.
        """
        with tempfile.TemporaryDirectory() as root:
            repo_root = Path(root).resolve()
            (repo_root / "stage-workflow.md").write_text(text, encoding="utf-8")
            return read_only.resolve_autopilot_stage(
                {"workflow_file": "stage-workflow.md", "autopilot_args": args or []},
                repo_root,
            )

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
        result = self.resolve(
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
                result = self.resolve(text)
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


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for case in (
        StageVocabularyAndArgvTests,
        RequestLayerDiagnosticTests,
        WorkflowStageSignalTests,
        PlanningStageCanonicalListTests,
    ):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-autopilot-stage-resolution")


if __name__ == "__main__":
    raise SystemExit(main())
