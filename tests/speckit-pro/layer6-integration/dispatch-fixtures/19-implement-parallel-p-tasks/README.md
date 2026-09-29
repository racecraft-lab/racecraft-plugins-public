# Fixture 19 — Phase 7 parallel batch dispatch

Verifies that when `partition-phase7-tasks` returns one wave of
dependency-ready batches whose tasks declare disjoint file ownership, the
orchestrator dispatches the whole wave in ONE assistant message via
background subagents that share the current feature checkout, with no
per-agent worktree isolation.

## Scenario

A Phase 7 group with 3 `[P]`-tagged implementation tasks (all routed to
`implement-executor`). Each task declares its own test file, so ownership is
disjoint. Tasks without declared disjoint ownership would serialize; this
fixture covers the case where they do not. The partition helper returned one
wave of 3 batches (`B001` to `B003`). Expected: 3 background dispatches in
ONE assistant message, each with `run_in_background: true` and no `isolation`
field (`agent-teams-integration.md` forbids per-agent worktree isolation for
Phase 7).

## Asserts

- 3 background dispatches happen (`min_dispatch_count`,
  `max_dispatch_count`, `must_run_in_background`)
- All 3 sit in ONE assistant message (`same_message_dispatch_groups`)
- No dispatch sets `isolation: "worktree"` (`forbidden_isolation`)
- Dispatches go to `speckit-pro:implement-executor`
- No forbidden spawns (subagents don't nest)
- `grill-me` is NEVER invoked

## What this fixture catches

- Regression to per-batch serial dispatch: the same 3 batches spread across
  several assistant messages fail `same_message_dispatch_groups`
- Foreground calls: a dispatch without `run_in_background: true` fails
  `must_run_in_background`
- Per-agent worktree isolation on a Phase 7 worker: fails
  `forbidden_isolation`, so the parser's recorded `isolation` field is
  asserted absent
- Wrong agent routing (e.g., orchestrator-direct instead of
  implement-executor), caught by `must_dispatch_to`

See `phase-execution.md` §Phase 7 Steps 3a-3c for the partition helper,
batch execution and the Agent prompt template, and
`agent-teams-integration.md` §Use site 3 for the ownership rule.
