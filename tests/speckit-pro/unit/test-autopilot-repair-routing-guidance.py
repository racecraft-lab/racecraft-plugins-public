#!/usr/bin/env python3
"""Guidance pins: a fixable helper result routes to its owner instead of stopping (issue 835).

Once a run starts, a fixable condition goes to the owning agent, is retried within
the shared allowance, and defers only when repair fails. Only authority and
exhausted-tier reasons involve a human (`references/stop-policy.md`). Each pin
below holds one case from the audit on both hosts, so a stop line cannot return.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TEST_DIR.parent / "lib"))

from guide_text import assert_guides_say, host_guides  # noqa: E402
from test_result import run_counted  # noqa: E402

CLAUDE = "skills/speckit-autopilot/"
REPAIR_THEN_DEFER = "run the repair loop within its allowance, then defer per the Failure Escalation Protocol"

# The autopilot's shared files, as each host receives them.
CLAUDE_SKILL, CODEX_SKILL = host_guides(CLAUDE + "SKILL.md")
CLAUDE_PHASE, CODEX_PHASE = host_guides(CLAUDE + "references/phase-execution.md")
CLAUDE_POST, CODEX_POST = host_guides(CLAUDE + "references/post-implementation.md")
CLAUDE_PREREQ, CODEX_PREREQ = host_guides(CLAUDE + "references/prerequisites.md")
GATES = CLAUDE + "references/gate-validation.md"
EFFICIENCY = CLAUDE + "references/execution-efficiency.md"
STACK_MANAGER = CLAUDE + "references/stack-manager.md"

STALE_POST_STOPS = (
    "stop before PR creation", "stop before PR side effects", "stop before `generate-pr-body`",
    "stop before branch or PR mutation", "must stop before `gh pr create`", "STOP before PR-body generation",
    "or stop blocked with the validator output", "stop with state only", "stop-before-PR boundary",
)
SKILLS = (CLAUDE_SKILL, CODEX_SKILL)
POSTS = (CLAUDE_POST, CODEX_POST)
PREREQS = (CLAUDE_PREREQ, CODEX_PREREQ)
PHASES = (CLAUDE_PHASE, CODEX_PHASE)

# Each pin is (case, guides, phrases the guides carry, phrases they no longer carry).
PINS = (
    ("a layer planner invalid_plan or input_error routes to its owner", SKILLS,
     ("route the planner's `repair` record to the phase-executor", "rerun `plan-layers-feature-dir`",
      "`tasks_file_missing`", REPAIR_THEN_DEFER),
     ("STOP: Layer planner returned invalid_plan", "STOP before implementation", "STOP separately")),
    ("a nonzero coverage guard exit is repaired, not a stop", SKILLS,
     ("On a nonzero exit, route the report's `repair` record to the orchestrator", "`failing_keys`", REPAIR_THEN_DEFER),
     ("guard and STOP on a nonzero exit", "guard and STOP on nonzero exit", "any other failing gated key, is a stop")),
    ("Codex plan state validation repairs before phase one", (CODEX_SKILL,),
     ("Before Phase 1 starts, validate all of the following or repair it",),
     ("Before Phase 1 starts, validate all of the following or STOP",)),
    ("a spec index write exit two routes the stderr line to the phase-executor", PHASES,
     ("Route the actionable stderr line to the phase-executor", "rerun `generate-spec-index-write` once",
      "Do NOT commit a broken regeneration", REPAIR_THEN_DEFER),
     ("Surface the actionable stderr line and STOP",)),
    ("no post-implementation file stops the run before a PR", (*POSTS, GATES, CODEX_PHASE), (), STALE_POST_STOPS),
    ("an invalid packet goes to the packet regenerator", POSTS,
     ("regenerate it with `pr-packet-output` from the validator diagnostics", "No PR is created until",
      REPAIR_THEN_DEFER), ()),
    ("a failing scoped command goes to the implement-executor", POSTS,
     ("route the failing command to the implement-executor", "keep `next_slice_id` on the blocked slice"), ()),
    ("an invalid runbook goes to the uat-runbook-author", POSTS,
     ("route the validator diagnostics to the uat-runbook-author", "hold PR-body generation"), ()),
    ("missing reviewability evidence and checkpoint SHAs are repaired", POSTS,
     ("regenerate the committed reviewability evidence", "record the marker checkpoint commit SHAs"), ()),
    ("a red baseline goes to the implement-executor", PHASES,
     ("route the failing check to the implement-executor", REPAIR_THEN_DEFER),
     ("If any check or populated blocking gate fails, STOP", "report each failed check's `message` and STOP")),
    ("a failing step zero check routes to its owner", (*PREREQS, CODEX_SKILL), ("route the failure to its owner",),
     ("check fails, STOP with the error message from the script's JSON output",
      "check fails, STOP with the error message from the JSON output")),
    ("a red baseline gate goes to the implement-executor in the phase guide", (CLAUDE_PHASE,),
     ("route the failing gate to the implement-executor", REPAIR_THEN_DEFER), ("If any fail, STOP; a missing or",)),
    ("each failing prerequisite check goes to the implement-executor", (CLAUDE_SKILL,),
     ("route each failing check to the implement-executor",), ("workflow's Prerequisites table. STOP on any failure.",)),
    ("a missing quality tool defaults to its install hint, then skip (spec)", PREREQS,
     ("default to the recorded install hint, then `skip (spec)`", "never asks", "Decisions for you"),
     ("one question per tool per repository", "STOP naming the tool and the three options",
      "If it is still false, STOP.", "ask once with `AskUserQuestion`", "ask once with `request_user_input`")),
    ("a failed archive sweep defers and the Claude run continues to phase zero", (CLAUDE_SKILL,),
     ("defer the Archive Sweep with that discovery evidence and continue to Phase 0",),
     ("STOP pre-flight with that discovery evidence",)),
    ("a failed archive sweep defers and the Codex run continues to phase zero", (CODEX_PREREQ,),
     ("defer the Archive Sweep with the exact failed path or operation and continue to Phase 0",
      "Retry the failed archive run once"),
     ("Then STOP before Phase 0 with the exact failed path", "then STOP before Phase 0.")),
    ("PR split findings repair and only scope changes stay with the operator", PHASES,
     ("regenerate the split evidence from the layer plan", "`decision=reslice_required`",
      "`stop_reason:scope_changing_pr_split`", "never ratify it yourself"),
     ("An `input_error`, a missing budget, or unreadable evidence also goes to the operator",)),
    ("unfinished task results redispatch to the batch agent", (*PHASES, EFFICIENCY),
     ("`disposition=redispatch`", "`repair` record", "unfinished task IDs"), ()),
    ("the efficiency guide no longer checkpoints unfinished task results", (EFFICIENCY,), (),
     ("persisted with `helper_exit_code=1` and `disposition=checkpoint_required`",)),
    ("a partial stack mutation is reverified and retried before it defers", (STACK_MANAGER, CODEX_POST),
     ("`reverify_recovery=true`", "retry the existing-PR link"), ()),
    ("a blocked stack stays blocked and defers only on a real failure", (STACK_MANAGER,),
     ("stays blocked and defers only when", "recreate PRs, or erase the attempted boundary"), ()),
)


class RepairRoutingGuidanceTests(unittest.TestCase):
    def test_each_fixable_result_routes_to_its_owner_and_no_stop_line_returns(self) -> None:
        for case, guides, present, absent in PINS:
            with self.subTest(case=case):
                assert_guides_say(self, guides, present, absent)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RepairRoutingGuidanceTests)
    return run_counted(suite, label="test-autopilot-repair-routing-guidance")


if __name__ == "__main__":
    raise SystemExit(main())
