# Fixture 19 — Phase 7 `[P]` parallel task dispatch

Verifies that when tasks.md contains consecutive `[P]`-tagged tasks of
the same agent type, the orchestrator dispatches them as a parallel
run in ONE assistant message via background subagents that share the
current feature checkout, with no per-agent worktree isolation.

## Scenario

A Phase 7 group with 3 consecutive `[P]`-tagged implementation tasks
(all routed to `implement-executor`). Expected: 3 background dispatches
in ONE assistant message, each with `run_in_background: true` and no
`isolation` worktree (`agent-teams-integration.md` forbids per-agent
worktree isolation for Phase 7).

## Asserts

- ≥3 background dispatches happen (`must_run_in_background`)
- All 3 sit in ONE assistant message (`same_message_dispatch_groups`)
- No dispatch sets `isolation: "worktree"` (`forbidden_isolation`)
- Dispatches go to `speckit-pro:implement-executor`
- No forbidden spawns (subagents don't nest)
- `grill-me` is NEVER invoked

## What this fixture catches

- Regression to per-task serial dispatch: the same 3 tasks spread across
  several assistant messages fail `same_message_dispatch_groups`
- Foreground calls: a dispatch without `run_in_background: true` fails
  `must_run_in_background`
- Per-agent worktree isolation on a Phase 7 worker: fails
  `forbidden_isolation`
- Wrong agent routing (e.g., orchestrator-direct instead of
  implement-executor) — caught by `must_dispatch_to`

See `phase-execution.md` §Phase 7 Step 3 for the partitioning algorithm
and `agent-teams-integration.md` §Use site 3 for the design rationale.
