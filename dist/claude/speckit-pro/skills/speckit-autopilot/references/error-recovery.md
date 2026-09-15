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
  reservation limits. On exhaustion, checkpoint and show the gate output.
- **Consensus agents all disagree:** Flag `[HUMAN REVIEW NEEDED]`
  and STOP. Present all 3 perspectives to the user.
- **MCP tool unavailable:** Skip research that depends on it.
  Use Read/Grep fallback for codebase analysis. Log warning.

## Context Window Management

For large specs, the context window may fill across 7 phases.
Mitigations:

- Keep sub-agent results concise (summaries, not full artifacts)
- The workflow file is the persistent record — read it rather than
  relying on conversation memory
- If compacted, re-read the workflow file to restore state
