# Error Recovery — Codex

How the Codex autopilot resumes after interruption and handles common
runtime failures. Codex-specific mirror of `error-recovery.md` — same recovery logic, Codex-specific primitives (`update_plan`, `autopilot-state.json`, `spawn_agent`).

## Contents

- [Resuming After Interruption](#resuming-after-interruption) — `--from-phase` + state-file reconciliation
- [Common Issues](#common-issues) — subagent retry, gate failure, consensus deadlock, MCP unavailable
- [Context Window Management](#context-window-management) — workflow-file-as-truth, compaction recovery

## Resuming After Interruption

The workflow file persists phase artifacts. `autopilot-state.json`
persists orchestration state. To resume:

```text
$speckit-autopilot workflow.md --from-phase <next-pending-phase>
```

**Resume protocol:**

1. Read `autopilot-state.json` next to the workflow file
2. Rebuild `update_plan` from its `plan` array
3. Re-read the workflow file to verify artifact status and prompt content
4. If the state file is missing, reconstruct it from the workflow file,
   immediately call `update_plan`, then continue from the requested phase
5. If all seven SDD phases are complete but any canonical `Post:` item is
   missing, `pending`, or `in_progress`, resume at the first incomplete Post
   item. Do not summarize completion from a `Phase 7: Implement Complete`
   state.
6. Never assume subagents from a previous interrupted session still exist. If
   `list_agents` is exposed, match current-tree entries to the workflow target
   and current incomplete plan item's canonical task name/prompt. Manage or
   reuse only agents confirmed present and owned by this autopilot run. Without
   inspection, treat prior-session effects as unknown; do not spawn fresh. Use
   the shared execution-control ledger's one read-only reconciliation. Loop
   bounded `wait_agent` calls until each required result is
   actually consumed; use `close_agent` only when exposed and only for
   run-owned agents confirmed present, including reconciled agents.

## Common Issues

- **Subagent returns empty/incomplete summary:** Use one read-only reconciliation
  through `execution-control action=reconcile` to inspect retained output and
  owned effects. Unknown effects require a checkpoint, not a replacement agent
  or direct shell retry. Retain verified partial task results; reserve only
  unfinished work after reconciliation proves it is safe.
- **Gate needs repair:** Diagnose through the consensus agents, fix through
  the executor, rerun verification, and keep remediating while each round
  converges: the ledger admits the next correction in a family with no
  operator event when the previous one shrank the runner-recorded failing set,
  or moved it with every earlier failure passing. On non-convergence (no
  measurable progress, a return to an earlier failing set, unparsed output, or
  a spec change), reserve against the same durable failure-family/spec
  budget used by every nested worker. An exhausted allowance returns
  `disposition=defer`: record the deferral with the exact output, keep
  executing every independent task, increment, and gate, and list it in the
  one end-of-run consolidated request. It is never a mid-run question and
  never sets the thread goal blocked mid-run; at the end of the run an
  unresolved deferral is the one human stop. `authorize-corrective-exception` (one
  operator-approved application correction) and `begin-replan-epoch` are
  end-of-run tools that act on the operator's answer to that request. An
  explicit `--stage implement` opens the implement stage's own allowance
  through `begin-stage-epoch`. Never reset or bypass the ledger otherwise;
  `checkpoint_required` and ledger integrity errors still stop. Repeated
  failures with one signature in one test file are one class: one approval
  covers its follow-ups through `reserve-class-correction`. See
  [Repeated Gate Failures: Diagnose One Class, Approve It Once](./phase-execution-codex.md#repeated-gate-failures-diagnose-one-class-approve-it-once).
- **Consensus agents all disagree:** Flag `[HUMAN REVIEW NEEDED]`.
  In an interactive task, ask the operator in place with
  `request_user_input` (the analysts' positions as options, the synthesizer's
  recommendation first, and a `Stop the run` option), apply the answer with
  the `human answer` label, and continue. In an unattended run, or when
  `request_user_input` is absent, STOP and present all 3 perspectives. See
  [consensus-protocol.md §Human Review Needed](consensus-protocol.md#human-review-needed).
- **MCP tool unavailable:** Skip research that depends on it. Use
  file search and read fallbacks for codebase analysis. Log warning.
- **Action blocked mid-run:** An approval-reviewer veto, a missing approval,
  or an unavailable tool inside Phase 7 or Post is not a stop. Take the task's
  own fallback, or defer that task and keep executing independent work, then
  ask once at the end. See
  [Blocked Actions Mid-Run: Fall Back or Defer, Never Stop](./phase-execution-codex.md#blocked-actions-mid-run-fall-back-or-defer-never-stop).
- **Plugin updated mid-run:** A plugin cache that changed or vanished, or an
  agent refreshed after phase work began, is not a stop. Re-resolve the plugin
  root, retry the failed bookkeeping calls once, record the drift, and
  continue; any restart goes into the end-of-run request. See
  [Plugin Update Mid-Run: Record, Re-resolve, Continue](./phase-execution-codex.md#plugin-update-mid-run-record-re-resolve-continue).
- **Lifecycle action unavailable, or a subagent appears stuck/frozen:** Missing
  `close_agent` is expected on hosted Responses Multi-agent and MUST NOT stop
  the run. When explicit closure is exposed but returns already-gone, log and
  continue without retry-looping. Bound each `wait_agent` poll with
  `timeout_ms`, but treat one timeout only as a poll boundary: continue waiting
  and inspect `list_agents` when possible. Use `interrupt_agent` only when
  exposed and a separate deadline or repeated no-progress check confirms the
  turn is stuck. Interruption preserves context and is not closure or a result;
  reconcile its effects and checkpoint if unknown. Interruption never grants
  a replacement launch or resets the same workflow's execution-control budget.

## Context Window Management

For large specs, the context window may fill across 7 phases.
Mitigations:

- Keep subagent results concise (summaries, not full artifacts)
- The workflow file is the persistent record — read it rather than
  relying on conversation memory
- Auto-compaction preserves CLAUDE.md and system instructions
- If compacted, re-read the workflow file to restore state
