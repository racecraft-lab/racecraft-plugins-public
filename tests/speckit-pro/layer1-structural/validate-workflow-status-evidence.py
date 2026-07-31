#!/usr/bin/env python3
"""Validate that every autopilot workflow file's status table agrees with its own gate evidence.

This is the agent-independent half of the autopilot bookkeeping guarantee. The
shipped phase-coverage validator enforces the same rule during a run, but only
if an agent actually invokes it; this gate runs in CI regardless, so a workflow
file whose Workflow Overview contradicts its own recorded gate verdicts cannot
merge.

Python 3.11+ standard library only.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

WORKFLOW_DIR = REPO_ROOT / "docs" / "ai" / "specs" / ".process"
COVERAGE_VALIDATOR = (
    REPO_ROOT
    / "speckit-pro"
    / "skills"
    / "speckit-autopilot"
    / "scripts"
    / "validate-autopilot-phase-coverage.py"
)
OVERVIEW_HEADING = "## Workflow Overview"
CRITERIA_HEADING_PREFIX = "### Phase Gates"

GATE_ID = r"G(?P<gate>[0-9](?:\.5)?)"
EMPHASIS = r"[ \t*_`]*"
GATE_LABEL = r"(?:Gate|GATE|gate|Result|Status|Validation|Confidence[ \t]+[Gg]ate)"
VERDICT = (
    r"(?:PASS(?:ED)?|Pass(?:ed)?|pass(?:ed)?)"
    r"(?![A-Za-z])"
    r"(?![ \t]+(?:only|when|if|once|unless|after|requires|criteria)\b)"
)
GATE_RECORD_INLINE = re.compile(
    r"(?:^|\||\*\*)" + EMPHASIS + r"(?:Gate[ \t]+)?" + GATE_ID + EMPHASIS
    + r"(?:" + GATE_LABEL + EMPHASIS + r")?[:—–-]?" + EMPHASIS
    + r"(?:[✅✓][ \t]*)?" + EMPHASIS + VERDICT
)
GATE_RECORD_CELL = re.compile(
    r"\|" + EMPHASIS + r"(?:Gate[ \t]+)?" + GATE_ID + EMPHASIS + r"(?:" + GATE_LABEL + r")?"
    + EMPHASIS + r"\|[ \t]*(?:[✅✓][ \t]*)?\*{0,2}" + VERDICT
)
GATE_RECORD_JSON = re.compile(
    r'"gate"[ \t]*:[ \t]*"' + GATE_ID + r'"[^{}]*?"pass"[ \t]*:[ \t]*true'
)
GATE_RECORD_PATTERNS = (GATE_RECORD_INLINE, GATE_RECORD_CELL, GATE_RECORD_JSON)

PHASE_GATE_IDS = {
    "Specify": "1",
    "Clarify": "2",
    "Plan": "3",
    "Checklist": "4",
    "Tasks": "5",
    "Analyze": "6",
    "Confidence Gate": "6.5",
    "Implement": "7",
}
TERMINAL_STATUSES = frozenset({
    "Complete",
    "✅ Complete",
    "Skipped",
    "✅ Skipped",
    "⏭️ Skipped",
})
OPEN_STATUSES = frozenset({
    "Pending",
    "⏳ Pending",
    "In Progress",
    "\U0001f504 In Progress",
    "Blocked",
    "⚠️ Blocked",
})
KNOWN_STATUSES = TERMINAL_STATUSES | OPEN_STATUSES

GATE_RECORD_POSITIVE_CASES = (
    "**G5 gate:** ✅ PASS — `validate-gate G5`, \"63 tasks found\".",
    "Completed 2026-07-24. **G3: PASS** (`plan.md exists with 0 unresolved markers`).",
    "**Gate G1: ✅ PASS** — `validate-gate` returned",
    "**G2 Gate:** Passed — 0 `[NEEDS CLARIFICATION]` markers remain.",
    "**G2 Result:** ✅ Passed. The authoritative gate reported",
    "**G6:** ✅ pass — 0 CRITICAL (1 MEDIUM found and remediated via consensus).",
    "**G6.5 Confidence Gate**: Pass: composite 0.98",
    "| Gate G5 | Passed: 32 tasks found and 0 unresolved markers |",
    "| G5 Gate | Passed: 39 tasks found, 0 markers. |",
    "| G1 Gate | ✅ Passed: `spec.md` exists with 0 markers |",
    "| G5 Gate | ✅ PASS (37 tasks; every FR has ≥1 task) |",
    "| G3 gate | Passed |",
    "| G3 | Pass: `validate-gate.sh G3` reported `pass=true`, 0 markers |",
    "| G5 Validation | Passed; 28 tasks detected |",
    "| **G5 Status** | Pass: tasks cover implementation |",
    "| **G5** | ✅ pass (30 tasks, 0 markers) |",
    "| Gate G1 | PASS — runner validate-gate: `spec.md exists with 0 markers` |",
    "| **Gate G5** | PASS — runner-verified: 136 tasks found, 0 markers |",
    "| G7 | Passed | `run-all` passed `2937/2937` |",
    '{"gate":"G5","pass":true,"reason":"40 tasks found","markers":0,"task_count":40}',
)
GATE_RECORD_NEGATIVE_CASES = (
    "| G7 | After Each Implementation Phase | Tests pass, manual verification complete |",
    "| G3 | After Plan | Architecture approved, constitution gates pass, dependencies identified |",
    "reads Tasks and Analyze as Pending while the same file records G5 and G6 PASS at",
    "**G2 Gate:** Pass only when zero unresolved requirement markers remain.",
    "| Analyze | `/speckit-analyze` | Complete | 3 findings remediated; G6 ready |",
    "Doctor health (after G0): 4 PASS, 1 WARN, 0 FAIL",
    "**G5 gate:** ❌ FAIL — 0 tasks found.",
    "| G6 | recommended pass once the analyzer reruns |",
    '{"gate":"G5","pass":false,"reason":"0 tasks found"}',
)


def workflow_files(directory: Path) -> list[Path]:
    """Every autopilot workflow markdown file, in deterministic order."""
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*-workflow.md"), key=lambda path: path.name)


def _table_row_indexes(lines: list[str], start: int) -> list[int]:
    rows: list[int] = []
    for index in range(start, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            rows.append(index)
        elif rows:
            break
    return rows


def overview_row_indexes(lines: list[str]) -> list[int]:
    """Row indexes of the '## Workflow Overview' table, header and separator included."""
    for index, line in enumerate(lines):
        if line.strip() == OVERVIEW_HEADING:
            return _table_row_indexes(lines, index + 1)
    return []


def criteria_row_indexes(lines: list[str]) -> set[int]:
    """Row indexes of every '### Phase Gates' approval-criteria table."""
    rows: set[int] = set()
    for index, line in enumerate(lines):
        if line.strip().startswith(CRITERIA_HEADING_PREFIX):
            rows.update(_table_row_indexes(lines, index + 1))
    return rows


def row_cells(line: str) -> list[str]:
    stripped = line.strip()
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def gate_record_ids(line: str) -> set[str]:
    """Gate ids this line records a PASS verdict for."""
    return {
        match.group("gate")
        for pattern in GATE_RECORD_PATTERNS
        for match in pattern.finditer(line)
    }


def recorded_gates(lines: list[str], excluded: set[int]) -> dict[str, int]:
    """Map gate id -> 1-indexed line of its first PASS record outside the excluded rows."""
    found: dict[str, int] = {}
    for index, line in enumerate(lines):
        if index in excluded:
            continue
        for gate in gate_record_ids(line):
            found.setdefault(gate, index + 1)
    return found


def collect_errors(directory: Path) -> dict[str, list[str]]:
    """Return each violation class as plain-English `file:line` strings."""
    missing_table: list[str] = []
    unknown_status: list[str] = []
    evidence: list[str] = []
    ordering: list[str] = []
    for path in workflow_files(directory):
        display = path.relative_to(REPO_ROOT).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        rows = overview_row_indexes(lines)
        if len(rows) < 3:
            missing_table.append(f"{display}: no parseable '{OVERVIEW_HEADING}' table")
            continue
        excluded = set(rows) | criteria_row_indexes(lines)
        records = recorded_gates(lines, excluded)
        first_open: tuple[int, str, str] | None = None
        for index in rows[2:]:
            cells = row_cells(lines[index])
            if len(cells) < 3:
                continue
            phase, status = cells[0], cells[2]
            number = index + 1
            if status not in KNOWN_STATUSES:
                unknown_status.append(
                    f"{display}:{number}: {phase!r} status {status!r} is outside the closed vocabulary"
                )
            gate = PHASE_GATE_IDS.get(phase)
            if gate is not None and gate in records and status not in TERMINAL_STATUSES:
                evidence.append(
                    f"{display}:{number}: {phase!r} reads {status!r} but the file records a"
                    f" G{gate} PASS at :{records[gate]}"
                )
            if status in TERMINAL_STATUSES:
                if first_open is not None:
                    ordering.append(
                        f"{display}:{number}: {phase!r} reads {status!r} after"
                        f" {first_open[1]!r} at :{first_open[0]} still reads {first_open[2]!r}"
                    )
            elif first_open is None:
                first_open = (number, phase, status)
    return {
        "missing_table": missing_table,
        "unknown_status": unknown_status,
        "evidence": evidence,
        "ordering": ordering,
    }


def load_coverage_validator():
    """Import the shipped phase-coverage validator so the vocabulary lock reads real bytes."""
    spec = importlib.util.spec_from_file_location(
        "speckit_autopilot_phase_coverage", COVERAGE_VALIDATOR
    )
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ValidateWorkflowStatusEvidence(unittest.TestCase):
    def test_workflow_status_tables_agree_with_gate_evidence(self) -> None:
        files = workflow_files(WORKFLOW_DIR)
        with self.subTest(msg="autopilot workflow files are discoverable"):
            self.assertTrue(files, f"no *-workflow.md files under {WORKFLOW_DIR}")

        errors = collect_errors(WORKFLOW_DIR)

        with self.subTest(msg="every workflow file exposes a parseable Workflow Overview table"):
            self.assertFalse(errors["missing_table"], "\n".join(errors["missing_table"]))

        with self.subTest(msg="every Workflow Overview status cell uses the closed vocabulary"):
            self.assertFalse(errors["unknown_status"], "\n".join(errors["unknown_status"]))

        with self.subTest(msg="a recorded gate PASS implies its Workflow Overview row is terminal"):
            self.assertFalse(errors["evidence"], "\n".join(errors["evidence"]))

        with self.subTest(msg="no terminal Workflow Overview row follows a non-terminal row"):
            self.assertFalse(errors["ordering"], "\n".join(errors["ordering"]))

        with self.subTest(msg="gate-record matcher accepts every recorded evidence form"):
            unmatched = [case for case in GATE_RECORD_POSITIVE_CASES if not gate_record_ids(case)]
            self.assertEqual([], unmatched, "\n".join(unmatched))

        with self.subTest(msg="gate-record matcher rejects criteria prose, citations, and FAIL records"):
            matched = [case for case in GATE_RECORD_NEGATIVE_CASES if gate_record_ids(case)]
            self.assertEqual([], matched, "\n".join(matched))

        with self.subTest(msg="status vocabulary matches the shipped phase-coverage validator"):
            module = load_coverage_validator()
            self.assertIsNotNone(module, f"could not import {COVERAGE_VALIDATOR}")
            self.assertEqual(
                sorted(TERMINAL_STATUSES),
                sorted(module.WORKFLOW_TERMINAL_STATUSES),
                "CI vocabulary drifted from the shipped validator",
            )
            self.assertEqual(
                dict(PHASE_GATE_IDS),
                dict(module.WORKFLOW_PHASE_GATE_IDS),
                "CI phase-to-gate map drifted from the shipped validator",
            )


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateWorkflowStatusEvidence)


def main() -> int:
    return run_counted(build_suite(), label="validate-workflow-status-evidence")


if __name__ == "__main__":
    raise SystemExit(main())
