# Error Recovery Reference

## Contents

- [Resuming After Interruption](#resuming-after-interruption) — `--from-phase` flag, workflow-file as durable state
- [Common Issues](#common-issues) — empty subagent summary, gate auto-fix exhaustion, all-disagree consensus, missing MCP tools
- [Context Window Management](#context-window-management) — concise summaries, workflow-file as persistent record, post-compaction recovery

## Resuming After Interruption

The workflow file persists all state. To resume:

```text
$speckit-pro:speckit-autopilot workflow.md --from-phase <next-pending-phase>
```

The autopilot reads prior artifacts and recovers the same execution-control
ledger per [Bounded Execution](./execution-efficiency.md), then continues only
when its disposition permits. Resume and agent replacement never reset budget.

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

- **Subagent returns an empty/incomplete summary:** Reserve the one read-only
  reconciliation with `execution-control action=reconcile`. Inspect retained
  output and owned effects. An unknown outcome blocks
  only its own unit: spawn a read-only reconciler over the unit's owned paths
  and settle it with `execution-control action=reconcile-unit` (see
  [Bounded Execution](./execution-efficiency.md)). The reconciler reports
  `no_effect`, `partial`, or `complete`, and the runner verifies the class from
  git state under the unit's owned paths. `no_effect` allows a new dispatch of
  that unit with no operator event; `partial` and `complete` need a
  `kind=verification` dispatch (`verifies_dispatch_id`) before the unit is
  released. Never use a direct-command fallback. Proven partial results retain
  completed tasks; only unfinished work may be reserved.
- **Gate needs repair:** Diagnose through the consensus agents, fix through
  the executor, rerun verification, and keep remediating while each round
  converges: the ledger admits the next correction in a family with no
  operator event when the previous one shrank the runner-recorded failing set,
  or moved it with every earlier failure passing. On non-convergence (no
  measurable progress, a return to an earlier failing set, unparsed output, or
  a spec change) the shared one-cycle-per-family/two-cycle-per-spec
  reservation limits apply to every nested worker. An exhausted allowance
  returns `disposition=defer`: record the deferral with the exact gate output,
  keep executing every independent task, increment, and gate, and list it in
  the one end-of-run consolidated request. It is never a mid-run question.
  It never sets the thread goal blocked mid-run.
  `authorize-corrective-exception` (one operator-approved application
  correction) and `begin-replan-epoch` are end-of-run tools that act on the
  operator's answer to that request. Before that request, use the agent-issued
  paths in [Bounded Execution](./execution-efficiency.md): `agent_authorized:
  true` on `authorize-corrective-retry`, `begin-replan-epoch`, or
  `authorize-corrective-continuation`, each capped and runner-proved. An
  explicit `--stage implement` opens the implement stage's own allowance
  through `begin-stage-epoch`. A task-verb fix that only reroutes a task to
  verification reserves with `metadata_only: true`; the runner proves it
  against the committed baseline and spends no cycle. Never reset or bypass
  the ledger otherwise; `checkpoint_required` and ledger integrity errors
  still stop. Repeated failures with one signature in one test file are one
  class: one approval covers its follow-ups through `reserve-class-correction`.
  See
  [Repeated Gate Failures: Diagnose One Class, Approve It Once](./phase-execution.md#repeated-gate-failures-diagnose-one-class-approve-it-once).
- **Consensus agents cannot agree:** The synthesizer flags
  `[ROUND_3_TIEBREAK]`, which starts the Round 3 tiebreak: a fresh analyst
  and a max-effort `consensus-tiebreaker` return the most conservative option
  that satisfies the spec. Apply it as an assumption with the dissent logged,
  in an interactive and an unattended run alike, and continue. An analyst that
  fails its retry is replaced by a fresh analyst. A choice that changes
  product scope the spec and roadmap do not settle is deferred to the
  end-of-run request, never a mid-run stop. See
  [consensus-protocol.md §Round 3 Tiebreak](./consensus-protocol.md#round-3-tiebreak).
- **MCP tool unavailable:** Skip research that depends on it. Use
  file search and read fallbacks for codebase analysis. Log warning.
- **Action blocked mid-run:** An approval-reviewer veto, a missing approval,
  or an unavailable tool inside Phase 7 or Post is not a stop. Take the task's
  own fallback, or defer that task and keep executing independent work, then
  ask once at the end. See
  [Blocked Actions Mid-Run: Fall Back or Defer, Never Stop](./phase-execution.md#blocked-actions-mid-run-fall-back-or-defer-never-stop).
- **Plugin updated mid-run:** A plugin cache that changed or vanished, or an
  agent refreshed after phase work began, is not a stop. Re-resolve the plugin
  root, retry the failed bookkeeping calls once, record the drift, and
  continue; any restart goes into the end-of-run request. See
  [Plugin Update Mid-Run: Record, Re-resolve, Continue](./phase-execution.md#plugin-update-mid-run-record-re-resolve-continue).
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

- Keep sub-agent results concise (summaries, not full artifacts)
- The workflow file is the persistent record — read it rather than
  relying on conversation memory
- If compacted, re-read the workflow file to restore state
