"""Autopilot stage arguments and the workflow-file stage and analysis signals."""

from __future__ import annotations

import re
from typing import Any

from .sweep_export import sweep_is_table_rule, sweep_table_cells


# Closed stage vocabulary: exactly three literal lowercase tokens, no aliases and
# no alternate casing. Consumed by downstream specifications, so the spelling is a
# cross-spec contract rather than local prose.
AUTOPILOT_STAGES = ("plan", "implement", "full")
AUTOPILOT_PLANNING_PHASES = ("specify", "clarify", "plan", "checklist", "tasks", "analyze")
AUTOPILOT_STAGE_PHASES = {
    "plan": AUTOPILOT_PLANNING_PHASES,
    "implement": ("implement",),
    "full": AUTOPILOT_PLANNING_PHASES + ("implement",),
}
STAGE_VALUES_SUFFIX = "accepted values: " + ", ".join(AUTOPILOT_STAGES)


def parse_stage_args(args: list[str]) -> dict[str, Any]:
    """Read --stage and --from-phase out of the autopilot invocation argv.

    Returns ``{"stage", "from_phase", "error"}``; ``error`` is the one-line
    ``error:`` diagnostic the operation prints on stderr before exiting 2, or
    None. Arguments are read by name, never by position, so the two
    distributions' synopsis orderings resolve identically.
    """
    stage_values: list[str] = []
    from_phase: str | None = None
    tokens = [arg for arg in args if isinstance(arg, str)]
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in {"--stage", "--from-phase"}:
            value = tokens[index + 1] if index + 1 < len(tokens) else None
            if value is None or value.startswith("-"):
                if token == "--from-phase":
                    # --from-phase is the autopilot's own argument; this operation
                    # only range-checks a value it can see.
                    index += 1
                    continue
                return stage_args_error(f"error: --stage requires a value — {STAGE_VALUES_SUFFIX}")
            if token == "--stage":
                if value not in AUTOPILOT_STAGES:
                    return stage_args_error(f"error: unrecognized stage {value!r} — {STAGE_VALUES_SUFFIX}")
                stage_values.append(value)
            else:
                from_phase = value
            index += 2
            continue
        index += 1
    distinct = list(dict.fromkeys(stage_values))
    if len(distinct) > 1:
        return stage_args_error(
            "error: --stage given more than once with different values: " + ", ".join(distinct)
        )
    stage = distinct[0] if distinct else None
    # The range conflict is scoped to an EXPLICITLY named stage. An auto-detected
    # stage never conflicts with --from-phase: after a strict-mode gate stop
    # auto-detection resolves `plan`, and rejecting the documented
    # `--from-phase implement` resume would strand the operator at the one
    # boundary the argument exists to cross.
    if (
        stage is not None
        and from_phase in AUTOPILOT_STAGE_PHASES["full"]
        and from_phase not in AUTOPILOT_STAGE_PHASES[stage]
    ):
        return stage_args_error(
            f"error: --stage {stage} and --from-phase {from_phase} are mutually exclusive"
        )
    return {"stage": stage, "from_phase": from_phase, "error": None}


def stage_args_error(message: str) -> dict[str, Any]:
    return {"stage": None, "from_phase": None, "error": message}


# The terminal half of the closed phase-status vocabulary the shipped
# phase-coverage validator publishes; the new unit test locks the two together so
# neither can drift alone.
AUTOPILOT_TERMINAL_STATUSES = frozenset({
    "Complete",
    "✅ Complete",
    "Skipped",
    "✅ Skipped",
    # U+23ED with and without the U+FE0F variation selector; both render alike.
    "⏭ Skipped",
    "⏭️ Skipped",
})
# Planning is complete only when every one of these rows is terminal. The
# `Confidence Gate` row is deliberately included: the validator excludes it from
# the ORDERING rule because the phase loop does not drive it, and that exclusion
# does not carry over to whether planning finished. Inheriting it would resolve
# `implement` straight after a strict-mode gate stop.
AUTOPILOT_PLANNING_PREDICATE_PHASES = (
    "Specify",
    "Clarify",
    "Plan",
    "Checklist",
    "Tasks",
    "Analyze",
    "Confidence Gate",
)
AUTOPILOT_GATE_PHASE = "Confidence Gate"
AUTOPILOT_OVERVIEW_HEADING = "## Workflow Overview"
ANALYSIS_OPEN_FINDINGS_STATUS = "open CRITICAL/HIGH findings"
AUTOPILOT_BASIC_INFO_HEADING = "### Basic Information"
HTML_COMMENT_RE = re.compile(r"(?s)<!--.*?-->")


def workflow_table_rows(lines: list[str], heading: str) -> list[list[str]]:
    """Cells of the markdown table under `heading`, header and separator dropped."""
    for index, line in enumerate(lines):
        if line.strip() != heading:
            continue
        rows: list[list[str]] = []
        for candidate in lines[index + 1:]:
            stripped = candidate.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                rows.append([cell.strip() for cell in stripped[1:-1].split("|")])
            elif rows or stripped.startswith("#"):
                break
        return rows[2:] if len(rows) >= 3 else []
    return []


def workflow_stage_signals(text: str) -> dict[str, Any]:
    """Read the durable `Stage` entry and the planning-complete predicate.

    Returns ``parsed=False`` when the `## Workflow Overview` table is missing or
    unparseable; the caller rejects that rather than degrading to a default,
    because every degraded default resolves the planning stage and would re-run
    finished work whenever the file is merely transiently unreadable.
    """
    # Blank HTML comment spans so a commented-out example cannot become evidence,
    # matching the at-rest validator's treatment of the same tables.
    lines = HTML_COMMENT_RE.sub("", text).splitlines()
    overview = workflow_table_rows(lines, AUTOPILOT_OVERVIEW_HEADING)
    if not overview:
        return {
            "parsed": False,
            "recorded_stage": None,
            "planning_complete": False,
            "confidence_gate_status": None,
            "first_open": None,
        }
    statuses: dict[str, str] = {}
    for cells in overview:
        if len(cells) >= 3:
            statuses.setdefault(cells[0], cells[2])
    first_open: tuple[str, str | None] | None = None
    for phase in AUTOPILOT_PLANNING_PREDICATE_PHASES:
        status = statuses.get(phase)
        if status is None:
            # An absent gate row does not block: it predates most workflow files.
            # An absent planning row means that phase has not run.
            if phase == AUTOPILOT_GATE_PHASE:
                continue
            first_open = (phase, None)
            break
        if status not in AUTOPILOT_TERMINAL_STATUSES:
            first_open = (phase, status)
            break
    from .formal.evidence import checkpoint_signal
    formal = checkpoint_signal(text)
    if first_open is None and not formal["complete"]:
        first_open = ("Formal Check", formal["verdict"])
    if first_open is None:
        # A terminal Analyze label is not evidence that its findings are closed.
        # A missing table does not block: legacy workflows predate it.
        findings = open_analysis_findings(text)
        open_count = findings["critical"] + findings["high"] if findings else 0
        if open_count:
            first_open = ("Analyze", f"{open_count} {ANALYSIS_OPEN_FINDINGS_STATUS}")
    return {
        "parsed": True,
        "recorded_stage": workflow_recorded_stage(lines),
        "planning_complete": first_open is None,
        "confidence_gate_status": statuses.get(AUTOPILOT_GATE_PHASE),
        "first_open": first_open,
        **({"formal_checkpoint": formal} if formal["required"] else {}),
    }


def workflow_recorded_stage(lines: list[str]) -> str | None:
    """The `Stage` row of `### Basic Information`, or None when absent (legal)."""
    for cells in workflow_table_rows(lines, AUTOPILOT_BASIC_INFO_HEADING):
        if len(cells) >= 2 and cells[0].strip("*` ").casefold() == "stage":
            return cells[1].strip("*` ") or None
    return None


ANALYSIS_SEVERITY_COLUMN = "severity"
ANALYSIS_RESOLUTION_COLUMN = "resolution"
ANALYSIS_OPEN_SEVERITIES = ("CRITICAL", "HIGH")


def analysis_results_rows(text: str) -> tuple[list[str], list[list[str]]]:
    """Header cells and data rows of the most recent Analysis Results table.

    The table is found by its columns rather than by a heading, because the
    severity legend above it carries the word `Severity` too and only the
    findings table also carries `Resolution`. A Phase 6 log can hold one table
    per Analyze pass, and only the last one describes the current state, so each
    header seen resets the rows. Anything that is not a table row ends the run,
    which is where a Markdown table ends. HTML comment spans are blanked first,
    as `workflow_stage_signals` does, so a commented-out example is not evidence.
    """
    header: list[str] = []
    rows: list[list[str]] = []
    collecting = False
    for raw in HTML_COMMENT_RE.sub("", text).splitlines():
        stripped = raw.strip()
        if not stripped.startswith("|"):
            collecting = False
            continue
        cells = sweep_table_cells(stripped)
        labels = [cell.casefold().strip("*` ") for cell in cells]
        if ANALYSIS_SEVERITY_COLUMN in labels and ANALYSIS_RESOLUTION_COLUMN in labels:
            header, rows, collecting = labels, [], True
            continue
        if not collecting or sweep_is_table_rule(cells):
            continue
        rows.append(cells)
    return header, rows


def open_analysis_findings(text: str) -> dict[str, int] | None:
    """Unresolved CRITICAL and HIGH rows of the workflow's Analysis Results table.

    A `[CRITICAL]` or `[HIGH]` marker in the log body cannot answer this. The
    workflow file is an append-only log, so the same bracket text appears in
    prose asserting zero findings and in a finding the run already remediated,
    and the count would never fall across a G6.5 iteration. The Analysis Results
    table carries the discriminator the log otherwise lacks: remediation fills
    the row's Resolution cell, as the shipped workflow template records it. A row
    whose cell count disagrees with its header is skipped rather than guessed at,
    which fails toward no deduction. Returns None when the text has no Analysis
    Results table, so a caller can tell missing evidence from zero open rows.
    """
    header, rows = analysis_results_rows(text)
    if not header:
        return None
    counts = {"critical": 0, "high": 0}
    severity_index = header.index(ANALYSIS_SEVERITY_COLUMN)
    resolution_index = header.index(ANALYSIS_RESOLUTION_COLUMN)
    for cells in rows:
        if len(cells) != len(header):
            continue
        severity = cells[severity_index].strip("*` ").upper()
        if severity in ANALYSIS_OPEN_SEVERITIES and not cells[resolution_index].strip("*` "):
            counts[severity.casefold()] += 1
    return counts
