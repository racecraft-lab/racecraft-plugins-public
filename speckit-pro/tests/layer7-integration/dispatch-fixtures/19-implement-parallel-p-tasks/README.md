# Fixture 19 — Phase 7 `[P]` parallel task dispatch (WS-D2)

Verifies that when tasks.md contains consecutive `[P]`-tagged tasks of
the same agent type, the orchestrator dispatches them as a parallel
run in ONE assistant message via background subagents with
`isolation: worktree`.

This is the regression safety net for **Use site 3** in the
[Agent Teams integration map](../../../../skills/speckit-autopilot/references/agent-teams-integration.md)
and closes the audit B1 "documented-vs-shipped" gap (the prior
implementation described `[P]` parallelism in phase-execution.md
but never authorized the orchestrator to execute it).

## Scenario

A Phase 7 group with 3 consecutive `[P]`-tagged implementation tasks
(all routed to `implement-executor`). Expected: 3 background dispatches
in ONE assistant message, each with `isolation: "worktree"` and
`run_in_background: true`.

## Asserts

- ≥3 background dispatches happen
- Dispatches go to `speckit-pro:implement-executor`
- No forbidden spawns (subagents don't nest)
- `grill-me` is NEVER invoked

## What this fixture catches

- Regression to per-task serial dispatch (the pre-WS-D2 state) — only
  0-1 dispatches in the parser-fixture's first assistant message
- Missing `isolation: "worktree"` — flagged by description content
  in the parser fixture
- Wrong agent routing (e.g., orchestrator-direct instead of
  implement-executor) — caught by `must_dispatch_to`

See `phase-execution.md` §Phase 7 Step 3 for the partitioning algorithm
and `agent-teams-integration.md` §Use site 3 for the design rationale.
