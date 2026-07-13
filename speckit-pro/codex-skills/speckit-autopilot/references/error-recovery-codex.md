# Error Recovery — Codex

How the Codex autopilot resumes after interruption and handles common
runtime failures. Codex-specific mirror of `../../skills/speckit-autopilot/references/error-recovery.md` — same recovery logic, Codex-specific primitives (`update_plan`, `autopilot-state.json`, `spawn_agent`).

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
   inspection, treat prior-session references as stale and spawn fresh. In
   either case, loop bounded `wait_agent` calls until each required result is
   actually consumed; use `close_agent` only when exposed and only for
   run-owned agents confirmed present, including reconciled agents.

## Common Issues

- **Subagent returns empty/incomplete summary:** Re-spawn with the
  same prompt via `spawn_agent`. If it fails again, run the command
  directly via shell and parse the output.
- **Gate fails after 2 auto-fix attempts:** If `gate-failure`
  setting is `stop`, STOP and report. Show the gate script output
  so the user can diagnose.
- **Consensus agents all disagree:** Flag `[HUMAN REVIEW NEEDED]`
  and STOP. Present all 3 perspectives to the user.
- **MCP tool unavailable:** Skip research that depends on it. Use
  file search and read fallbacks for codebase analysis. Log warning.
- **Lifecycle action unavailable, or a subagent appears stuck/frozen:** Missing
  `close_agent` is expected on hosted Responses Multi-agent and MUST NOT stop
  the run. When explicit closure is exposed but returns already-gone, log and
  continue without retry-looping. Bound each `wait_agent` poll with
  `timeout_ms`, but treat one timeout only as a poll boundary: continue waiting
  and inspect `list_agents` when possible. Use `interrupt_agent` only when
  exposed and a separate deadline or repeated no-progress check confirms the
  turn is stuck. Interruption preserves context and is not closure or a result;
  re-spawn the required item and consume its real result before completion.

## Context Window Management

For large specs, the context window may fill across 7 phases.
Mitigations:

- Keep subagent results concise (summaries, not full artifacts)
- The workflow file is the persistent record — read it rather than
  relying on conversation memory
- Auto-compaction preserves CLAUDE.md and system instructions
- If compacted, re-read the workflow file to restore state
