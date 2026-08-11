#!/usr/bin/env python3
"""Contracts for the autopilot implementation-notes record.

Two assertion groups live in this file. They pass or fail independently and
each failure names its own group, so a regression in one never masks the other:

* ``RECORD CONTRACT`` — Phase 7 documents the record described in
  ``specs/art-012-implementation-notes-capture/contracts/implementation-notes-record.md``
  on both agent platforms, and the Agent Teams reference no longer contradicts
  its per-arrival cadence.
* ``REPORTING FIELD`` — every authored ``## Task Result: <TASK_ID>`` block
  carries the combined reporting field described in
  ``specs/art-012-implementation-notes-capture/contracts/task-result-reporting-field.md``.
  Its check table covers the field's text and position in the three authored
  copies; a companion test guards the set of copies itself, because that one
  asserts over the file tree rather than over any single document body.

**Every body is whitespace-normalized before matching.** Runs of whitespace
collapse to one space, so an asserted phrase may be hard-wrapped across lines in
the source document exactly like the prose around it. Section boundaries are
resolved on the raw text first, and the extractor ignores headings that sit
inside a fenced code block so a fenced record example cannot truncate a section.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
LIB_DIR = TEST_DIR.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402


CLAUDE_PHASE_EXECUTION = "speckit-pro/skills/speckit-autopilot/references/phase-execution.md"
CODEX_PHASE_EXECUTION = (
    "speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md"
)
AGENT_TEAMS_INTEGRATION = (
    "speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md"
)
TDD_PROTOCOL = "speckit-pro/skills/speckit-autopilot/references/tdd-protocol.md"
CLAUDE_IMPLEMENT_EXECUTOR = "speckit-pro/agents/implement-executor.md"
CODEX_IMPLEMENT_EXECUTOR = "speckit-pro/codex-agents/implement-executor.toml"

CLAUDE_PHASE_7_HEADING = "### Phase 7: Implement (Task-Level Dispatch)"
CODEX_PHASE_7_HEADING = "## Phase 7: Implement"
USE_SITE_3_HEADING = "### Use site 3: Phase 7 `[P]` task team"
SUMMARY_FORMAT_HEADING = "## Summary Format"
TERMINAL_DELIVERABLE_HEADING = "### Terminal Deliverable"

# Target key -> (repository-relative file, section heading or None for whole file).
TARGETS = {
    "claude_phase7": (CLAUDE_PHASE_EXECUTION, CLAUDE_PHASE_7_HEADING),
    "codex_phase7": (CODEX_PHASE_EXECUTION, CODEX_PHASE_7_HEADING),
    "agent_teams": (AGENT_TEAMS_INTEGRATION, None),
    "agent_teams_use_site_3": (AGENT_TEAMS_INTEGRATION, USE_SITE_3_HEADING),
    # The Task Result block itself cannot be a section target: it sits inside a
    # ``` fence in all three copies, and _section ignores fenced headings. Its
    # enclosing "## Summary Format" heading can, and occurs once per file.
    "tdd_protocol_summary": (TDD_PROTOCOL, SUMMARY_FORMAT_HEADING),
    "claude_executor_summary": (CLAUDE_IMPLEMENT_EXECUTOR, SUMMARY_FORMAT_HEADING),
    "codex_executor_summary": (CODEX_IMPLEMENT_EXECUTOR, SUMMARY_FORMAT_HEADING),
    "claude_executor_terminal": (
        CLAUDE_IMPLEMENT_EXECUTOR,
        TERMINAL_DELIVERABLE_HEADING,
    ),
}

RECORD_CONTRACT_GROUP = "RECORD CONTRACT"
REPORTING_FIELD_GROUP = "REPORTING FIELD"

# The record's own literals, quoted from the contract so a drifting document
# fails rather than a drifting test.
RECORD_PATH = ".process/implementation-notes.md"
RECORD_HEADER = "# Implementation Notes: <SPEC_ID>"
ENTRY_HEADING = "### <TASK_ID>"
ENTRY_FIELD = "**Deviations/Edge cases/Surprises:**"
TASK_RESULT_BLOCK = "## Task Result: <TASK_ID>"
WORKFLOW_FILE = "docs/ai/specs/.process/<SPEC_ID>-workflow.md"

# First-dispatch anchors. The lifecycle step has to be documented ahead of these.
CLAUDE_FIRST_DISPATCH = "Step 1: Parse tasks.md"
CODEX_FIRST_DISPATCH = "Use `implement-executor`"

# The reporting field's own literals, quoted from
# specs/art-012-implementation-notes-capture/contracts/task-result-reporting-field.md
# for the same reason: a drifting document fails, not a drifting test.
ERRORS_LINE = "**Errors:** None (or describe)"
REPORTING_FIELD_LINE = "**Deviations/Edge cases/Surprises:** None (or describe)"
# The five fields the Claude agent's Terminal Deliverable prose must enumerate.
# Four of them ship today; the fifth is what this feature adds.
TERMINAL_DELIVERABLE_FIELDS = (
    "TDD Evidence / Test commands used / Files created/modified / Errors"
    " / Deviations/Edge cases/Surprises"
)

# Item 4's scope and expected answer: exactly these authored files under
# speckit-pro/ carry a Task Result block. The generated copies under dist/ and
# under the installed-cache fixture tree are regenerated from these three and
# are never authored, so the scan must never leave speckit-pro/.
PLUGIN_SOURCE_DIR = "speckit-pro"
AUTHORED_TASK_RESULT_FILES = tuple(
    sorted((TDD_PROTOCOL, CLAUDE_IMPLEMENT_EXECUTOR, CODEX_IMPLEMENT_EXECUTOR))
)


def _phase_execution_checks(target: str, platform: str) -> tuple[tuple[str, str, str, object], ...]:
    """Contract items 1-5, 6, and 7, which both platform documents owe."""
    first_dispatch = CLAUDE_FIRST_DISPATCH if target == "claude_phase7" else CODEX_FIRST_DISPATCH
    heading = CLAUDE_PHASE_7_HEADING if target == "claude_phase7" else CODEX_PHASE_7_HEADING
    return (
        # Section presence: a missing heading empties the body, so name it first.
        (f"{platform} exposes a Phase 7 section", target, "contains", heading),
        # Item 1 — record location, header, entry heading, entry field.
        (f"{platform} names the record path", target, "contains", RECORD_PATH),
        (f"{platform} names the record header", target, "contains", RECORD_HEADER),
        (f"{platform} names the entry heading", target, "contains", ENTRY_HEADING),
        (f"{platform} names the entry field", target, "contains", ENTRY_FIELD),
        # Item 2 — create-if-absent, never truncate, never a second header.
        (f"{platform} states create-if-absent lifecycle", target, "regex", r"(?i)create[- ]if[- ]absent"),
        (f"{platform} forbids truncating an existing record", target, "regex", r"(?i)(never|do not|not) truncate"),
        (f"{platform} forbids a second header", target, "regex", r"(?i)(never|not|no)\b[^.]{0,40}second header"),
        # Item 3 — the lifecycle step runs before the first task dispatch.
        (f"{platform} states the step runs before the first dispatch", target, "regex",
         r"(?i)before\s+(the\s+)?first\s+(task|dispatch)"),
        (f"{platform} places the record ahead of its first dispatch", target, "before",
         (RECORD_PATH, first_dispatch)),
        # Item 4 — additive only.
        (f"{platform} states appends are additive only", target, "regex", r"(?i)additive[- ]only"),
        (f"{platform} forbids rewriting, reordering, or removing an entry", target, "regex",
         r"(?i)rewritten,\s*reordered,\s*or removed"),
        (f"{platform} appends a further entry on a re-run", target, "regex",
         r"(?i)(further|another|additional|new|second) entry under the same task ID"),
        # Item 5 — fail-open.
        (f"{platform} states the failure path is fail-open", target, "regex", r"(?i)fail[- ]open"),
        (f"{platform} sends the gap to the workflow file", target, "contains", WORKFLOW_FILE),
        (f"{platform} forbids retrying a failed write", target, "regex",
         r"(?i)(do not retry|not retried|no retry|one attempt, then the gap|without retry)"),
        (f"{platform} bounds the fallback to one level", target, "regex",
         r"(?i)(exactly one level|one fallback level|one level deep|exactly one fallback)"),
        (f"{platform} bounds the blast radius to one entry", target, "regex",
         r"(?i)blast radius[^.]{0,24}one entry"),
        # Item 6 — per-arrival cadence on every dispatch shape, never on idle.
        (f"{platform} names the per-arrival cadence", target, "regex", r"(?i)per[- ]arrival"),
        (f"{platform} appends on the turn the result arrives", target, "regex",
         r"(?i)on the turn[^.]{0,80}result"),
        (f"{platform} applies the cadence to every dispatch shape", target, "regex",
         r"(?i)(every|each|any|whatever the|whichever)\s+dispatch\s+shape"),
        (f"{platform} does not wait for the rest of a parallel run", target, "regex",
         r"(?i)(does not wait for|do not wait for|without waiting for|never waits for)\s+the rest of"),
        (f"{platform} forbids batching entries to phase end", target, "regex", r"(?i)(never|not) batched"),
        (f"{platform} never appends on a bare idle signal", target, "regex",
         r"(?i)never\s+append[^.]{0,60}idle|idle[^.]{0,80}never"),
        # Item 7 — all three routing branches, and the single None value.
        (f"{platform} covers the executor routing branch", target, "contains", "implement-executor"),
        (f"{platform} covers the research routing branch", target, "contains", "domain-researcher"),
        (f"{platform} covers the verification routing branch", target, "contains", "orchestrator-direct"),
        (f"{platform} states all three branches append", target, "regex",
         r"(?i)three\s+(append\s+)?(call sites|routing branches|branches|routes)"),
        (f"{platform} names the literal None value", target, "regex", r"(?i)literal\s+.?None"),
        (f"{platform} states None covers every nothing-to-report case", target, "regex",
         r"(?i)nothing[- ]to[- ]report"),
    )


def _reporting_field_checks(target: str, label: str) -> tuple[tuple[str, str, str, object], ...]:
    """Contract items 1 and 2, which all three authored copies owe."""
    return (
        # Item 1 — the exact line.
        (f"{label} carries the reporting field line", target, "contains", REPORTING_FIELD_LINE),
        # Item 2, first half — it follows this file's own **Errors:** line.
        # Normalization collapses the blank line between them to one space.
        (f"{label} places the field immediately after its Errors line", target, "regex",
         re.escape(ERRORS_LINE) + " " + re.escape(REPORTING_FIELD_LINE)),
        # Item 2, second half — nothing follows it inside the block, so the
        # fence that closes the block is the next thing after it.
        (f"{label} makes the field the last field of the block", target, "regex",
         re.escape(REPORTING_FIELD_LINE) + " ```"),
    )


# ---------------------------------------------------------------------------
# GROUP 1 of 2 — RECORD CONTRACT (contract items 1, 2, 3, 4, 5, 6, 6b, 6c, 7 of
# specs/art-012-implementation-notes-capture/contracts/implementation-notes-record.md).
# ---------------------------------------------------------------------------
RECORD_CONTRACT_CHECKS: tuple[tuple[str, str, str, object], ...] = (
    *_phase_execution_checks("claude_phase7", "Claude phase-execution"),
    *_phase_execution_checks("codex_phase7", "Codex phase-execution"),
    # Item 6b — the Claude document alone owes the FR-006 teammate report
    # obligation, because Agent Teams is a Claude-platform mechanism.
    (
        "Claude phase-execution obliges teammates to send their summary to the lead",
        "claude_phase7",
        "regex",
        r"(?i)teammates?\s+must\s+send[^.]{0,140}to the lead",
    ),
    (
        "Claude phase-execution names the task-result block teammates must send",
        "claude_phase7",
        "contains",
        TASK_RESULT_BLOCK,
    ),
    # Item 6c — the Agent Teams reference must stop asserting batched delivery.
    (
        "Agent Teams reference drops the batched within-message claim",
        "agent_teams",
        "absent",
        "returns all N results together",
    ),
    (
        "Agent Teams reference drops the batched axes-of-parallelism claim",
        "agent_teams",
        "absent",
        "all results in next message",
    ),
    (
        "Agent Teams reference states per-completion delivery where it claimed batching",
        "agent_teams",
        "count_at_least",
        (r"(?i)per[- ]completion", 2),
    ),
    (
        "Agent Teams Use site 3 names the implementation-notes record",
        "agent_teams_use_site_3",
        "regex",
        r"(?i)implementation[- ]notes",
    ),
    (
        "Agent Teams Use site 3 names the per-arrival append",
        "agent_teams_use_site_3",
        "regex",
        r"(?i)\bappend",
    ),
    (
        "Agent Teams Use site 3 keeps the barrier merge into COMPLETED_TASKS",
        "agent_teams_use_site_3",
        "contains",
        "COMPLETED_TASKS",
    ),
)


# ---------------------------------------------------------------------------
# GROUP 2 of 2 — REPORTING FIELD (contract items 1, 2, and 3 of
# specs/art-012-implementation-notes-capture/contracts/task-result-reporting-field.md).
#
# Item 4 of that contract asserts over the *set* of files carrying the block
# rather than over any single document body, so it cannot take the
# (name, target, kind, value) shape this table is keyed on. It lives in its own
# test below and reports under this same group name.
# ---------------------------------------------------------------------------
REPORTING_FIELD_CHECKS: tuple[tuple[str, str, str, object], ...] = (
    *_reporting_field_checks("tdd_protocol_summary", "tdd-protocol Summary Format"),
    *_reporting_field_checks(
        "claude_executor_summary", "Claude implement-executor Summary Format"
    ),
    *_reporting_field_checks(
        "codex_executor_summary", "Codex implement-executor Summary Format"
    ),
    # Item 3 — the Claude agent alone repeats its required fields in prose, and
    # an agent follows its own hard MUST over a template it also carries. Left
    # at four fields that MUST contradicts the template this group just fixed.
    (
        "Claude implement-executor Terminal Deliverable enumerates all five fields",
        "claude_executor_terminal",
        "regex",
        r"Task Result above \(" + re.escape(TERMINAL_DELIVERABLE_FIELDS) + r"\)",
    ),
)


def _section(body: str, heading_prefix: str) -> str:
    """Return the section a heading introduces, ignoring fenced code blocks.

    The section runs from the heading line to the next heading of the same or a
    shallower level that is not inside a ``` fence, or to end of file. Returns
    ``""`` when the heading is absent, so the caller reports a named assertion
    failure rather than an index error.
    """
    level = len(heading_prefix) - len(heading_prefix.lstrip("#"))
    terminator = re.compile(rf"^#{{1,{level}}} ")
    lines = body.splitlines(keepends=True)
    start = None
    in_fence = False
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if start is None:
            if line.rstrip("\n").startswith(heading_prefix):
                start = index
            continue
        if terminator.match(line):
            return "".join(lines[start:index])
    return "" if start is None else "".join(lines[start:])


def _normalize(body: str) -> str:
    """Collapse whitespace so hard-wrapped prose matches a single-line phrase."""
    return re.sub(r"\s+", " ", body)


def _task_result_files() -> tuple[str, ...]:
    """Repository-relative paths under speckit-pro/ that carry a Task Result block.

    A copy counts only when the block heading opens a line at column 0. Prose
    that names the block inline in backticks is a reference to the contract, not
    a copy of it, and owes nothing; both phase-execution.md and
    agent-teams-integration.md mention it that way.
    """
    found = []
    for path in (REPO_ROOT / PLUGIN_SOURCE_DIR).rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # a binary or unreadable asset cannot carry the block
        if any(line.startswith(TASK_RESULT_BLOCK) for line in text.splitlines()):
            found.append(path.relative_to(REPO_ROOT).as_posix())
    return tuple(sorted(found))


class ImplementationNotesRecordTests(unittest.TestCase):
    """Keep the implementation-notes record contract documented where it runs."""

    @classmethod
    def setUpClass(cls) -> None:
        raw: dict[str, str] = {}
        cls.bodies = {}
        cls.labels = {}
        for key, (relative_path, heading) in TARGETS.items():
            if relative_path not in raw:
                raw[relative_path] = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
            text = raw[relative_path] if heading is None else _section(raw[relative_path], heading)
            cls.bodies[key] = _normalize(text)
            cls.labels[key] = relative_path if heading is None else f"{relative_path} §{heading}"

    def _assert_group(self, group: str, checks: tuple[tuple[str, str, str, object], ...]) -> None:
        for name, target, kind, value in checks:
            with self.subTest(msg=f"[{group}] {name}"):
                body = self.bodies[target]
                label = self.labels[target]
                if kind == "contains":
                    satisfied = value in body
                    detail = f"missing literal {value!r}"
                elif kind == "absent":
                    satisfied = value not in body
                    detail = f"still contains the withdrawn claim {value!r}"
                elif kind == "regex":
                    satisfied = re.search(value, body) is not None
                    detail = f"no match for {value!r}"
                elif kind == "count_at_least":
                    pattern, minimum = value
                    found = len(re.findall(pattern, body))
                    satisfied = found >= minimum
                    detail = f"{pattern!r} matched {found} time(s), needs at least {minimum}"
                elif kind == "before":
                    earlier, later = value
                    earlier_at = body.find(earlier)
                    later_at = body.find(later)
                    satisfied = earlier_at >= 0 and later_at >= 0 and earlier_at < later_at
                    detail = (
                        f"{earlier!r} (at {earlier_at}) must appear before "
                        f"{later!r} (at {later_at}); -1 means absent"
                    )
                else:  # pragma: no cover - guards a typo in the check table
                    self.fail(f"[{group}] {name}: unknown check kind {kind!r}")
                    return
                if not satisfied:
                    self.fail(f"[{group}] {name}: {label}: {detail}")

    def test_record_contract_is_documented_on_both_platforms(self) -> None:
        self._assert_group(RECORD_CONTRACT_GROUP, RECORD_CONTRACT_CHECKS)

    def test_reporting_field_is_documented_in_every_task_result_block(self) -> None:
        self._assert_group(REPORTING_FIELD_GROUP, REPORTING_FIELD_CHECKS)

    def test_authored_task_result_copies_are_still_exactly_three(self) -> None:
        """Reporting-field item 4: no fourth copy can skip the field unnoticed.

        Scoped to speckit-pro/. Tree-wide the same block also appears in the
        dist/ payload copies, the installed-cache fixture copies, and the
        contract document's own worked example, none of which are authored
        plugin source, so an unscoped count of three is false on a clean tree.
        """
        self.assertEqual(
            _task_result_files(),
            AUTHORED_TASK_RESULT_FILES,
            f"[{REPORTING_FIELD_GROUP}] the authored Task Result copies under "
            f"{PLUGIN_SOURCE_DIR}/ changed. Every copy owes the reporting field, so "
            "add the new one to TARGETS and to REPORTING_FIELD_CHECKS, or drop the "
            "removed one from AUTHORED_TASK_RESULT_FILES",
        )


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ImplementationNotesRecordTests)


def main() -> int:
    return run_counted(build_suite(), label="test-implementation-notes-record")


if __name__ == "__main__":
    raise SystemExit(main())
