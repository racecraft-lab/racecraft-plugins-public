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

The autopilot reads prior artifacts from disk and continues from
the specified phase.

## Common Issues

- **Subagent returns an empty/incomplete summary:** Follow the persisted
  `partial_resume` strategy from `resolve-claude-subagent-runtime`. When the
  runtime supports partial results and the result includes an agent ID, send
  exactly one `SendMessage` continuation to that same agent and record
  `partial_resume_used=true`. That continuation consumes the reserved
  concurrency slot. If the resumed result is still partial, STOP and report
  the incomplete result; do not loop or silently replace it. On clients older
  than 2.1.246, make one fresh retry with the same prompt and then STOP on a
  second partial result.
- **A parallel wave exceeds capacity:** Dispatch deterministic waves of at most
  `SUBAGENT_WAVE_SIZE`, preserving task order in the final result regardless of
  completion order. The resolver reserves one slot for recovery. An invalid
  concurrency override forces wave size 1 and emits a warning.
- **Gate fails after 2 auto-fix attempts:** If `gate-failure`
  setting is `stop`, STOP and report. Show the gate script
  output so the user can diagnose.
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
- Auto-compaction preserves CLAUDE.md and system instructions
- If compacted, re-read the workflow file to restore state
