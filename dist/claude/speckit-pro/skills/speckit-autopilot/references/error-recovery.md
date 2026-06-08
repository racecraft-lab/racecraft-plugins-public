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

- **Subagent returns empty/incomplete summary:** Re-spawn with
  the same prompt. If it fails again, run the command directly
  via Bash and parse the output.
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
