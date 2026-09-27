# Error Recovery Reference

## Contents

- [Resuming After Interruption](#resuming-after-interruption) — `--from-phase` flag, workflow-file as durable state
- [Common Issues](#common-issues) — empty subagent summary, gate auto-fix exhaustion, all-disagree consensus, missing MCP tools
- [Context Window Management](#context-window-management) — concise summaries, workflow-file as persistent record, post-compaction recovery

## Resuming After Interruption

The workflow file persists all state. To resume:

```text
/speckit-pro:speckit-autopilot workflow.md --from-phase <next-pending-phase>
```

The autopilot reads prior artifacts and recovers the same execution-control
ledger per [Bounded Execution](./execution-efficiency.md), then continues only
when its disposition permits. Resume and agent replacement never reset budget.

## Common Issues

- **Subagent returns an empty/incomplete summary:** Reserve the one read-only
  reconciliation with `execution-control action=reconcile`. Inspect retained
  output and owned effects; a supported `SendMessage` may request only the
  already-produced result, not continuing writes. Unknown effects require an
  honest checkpoint, never a fresh retry or direct-command fallback. Proven
  partial results retain completed tasks; only unfinished work may be reserved.
- **A parallel wave exceeds capacity:** Dispatch deterministic waves of at most
  `SUBAGENT_WAVE_SIZE`, preserving task order in the final result regardless of
  completion order. The resolver reserves one slot for recovery. An invalid
  concurrency override forces wave size 1 and emits a warning.
- **Gate needs repair:** Use the shared one-cycle-per-family/two-cycle-per-spec
  reservation limits. On exhaustion, checkpoint and show the gate output. An
  explicit `--stage implement` opens the implement stage's own allowance
  through `begin-stage-epoch`. After an operator-ordered re-plan,
  `begin-replan-epoch` opens a fresh allowance with the operator's approval
  ([Bounded Execution](./execution-efficiency.md)).
- **Consensus agents all disagree:** Flag `[HUMAN REVIEW NEEDED]`.
  In an interactive session, ask the operator in place with
  `AskUserQuestion` (the analysts' positions as options, the synthesizer's
  recommendation first, and a `Stop the run` option), apply the answer with
  the `human answer` label, and continue. In an unattended run, STOP and
  present all 3 perspectives. See
  [consensus-protocol.md §Human Review Needed](./consensus-protocol.md#human-review-needed).
- **MCP tool unavailable:** Skip research that depends on it.
  Use Read/Grep fallback for codebase analysis. Log warning.
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

## Context Window Management

For large specs, the context window may fill across 7 phases.
Mitigations:

- Keep sub-agent results concise (summaries, not full artifacts)
- The workflow file is the persistent record — read it rather than
  relying on conversation memory
- If compacted, re-read the workflow file to restore state
