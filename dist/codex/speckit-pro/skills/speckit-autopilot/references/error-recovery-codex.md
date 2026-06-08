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
6. Do NOT try to `close_agent` or `wait_agent` on subagents from the previous
   (interrupted) session — those threads are gone, and a close attempt will
   error harmlessly. Resume with a clean `spawn_agent` → `wait_agent` →
   `close_agent` lifecycle for newly spawned agents only. Keep closing the new
   agents you spawn — do not conclude from one stale-agent close error that
   closing is unsafe.

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
- **`close_agent` errors, or a subagent appears stuck/frozen:** On the Codex
  app especially, `close_agent` can report `thread not found` on an
  already-gone agent, and a stuck subagent can leave the main thread spinning
  (openai/codex#23219, #23292). Treat a failed close as already-closed — log
  and continue; never retry-loop it, and never stop closing future agents.
  Abandoning cleanup is what lets orphaned threads exhaust the cap and freeze
  the session (openai/codex#19197). Bound `wait_agent` with a `timeout_ms` so
  a stuck subagent cannot hang the orchestrator; on a hang, stop waiting, mark
  the item for re-spawn, and continue.

## Context Window Management

For large specs, the context window may fill across 7 phases.
Mitigations:

- Keep subagent results concise (summaries, not full artifacts)
- The workflow file is the persistent record — read it rather than
  relying on conversation memory
- Auto-compaction preserves CLAUDE.md and system instructions
- If compacted, re-read the workflow file to restore state
