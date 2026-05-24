# Fixture 21 — Parallel resolve-pr per-file partition (WS-F1)

Verifies that when a PR review has unresolved threads across multiple
files, the orchestrator partitions by file path and dispatches all
partitions in ONE assistant message via background subagents.

This is the regression safety net for **Use site 6** in the
[Agent Teams integration map](../../../../skills/speckit-autopilot/references/agent-teams-integration.md)
— the WS-F1 pattern. Per
[`commands/resolve-pr.md`](../../../../commands/resolve-pr.md) §4 and
[`post-implementation.md`](../../../../skills/speckit-autopilot/references/post-implementation.md)
§3.3, threads are partitioned by file (no cross-file race) and
dispatched in parallel across partitions.

## Scenario

A PR with 6 unresolved review threads spread across 3 different files
(2 threads per file), no cross-file hints in any comment. Expected:
3 background subagent dispatches (one per file partition) all in ONE
assistant message.

## Asserts

- ≥3 background dispatches happen
- Dispatches go to `general-purpose` (the WS-F1 worker type)
- No forbidden spawns (subagents don't nest)
- `grill-me` is NEVER invoked
- All 3 dispatches in ONE assistant message (parser-fixture transcript
  shape captures this)

## When this fixture would fail

- If a future change reverts to per-thread serial processing
  (pre-WS-F1 state), only 0-1 subagent dispatches would happen and
  `min_dispatch_count: 3` fails.
- If partitioning breaks and each thread gets its own subagent (6
  dispatches instead of 3 per-file), `max_dispatch_count: 6` allows
  it but the design note in the fixture description would flag the
  inefficiency.

See `agent-teams-integration.md` §Use site 6 for the design rationale
and the audit B3 finding that originally surfaced this optimization.
