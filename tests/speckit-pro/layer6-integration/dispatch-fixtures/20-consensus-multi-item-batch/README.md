# Fixture 20 — Multi-item consensus batched dispatch

Verifies that when a consensus phase (Clarify / Checklist / Analyze)
produces multiple unresolved items, the orchestrator dispatches all
routed analysts for all items in **ONE assistant message** (background
fan-out), not per-item sequentially.

The fixture asserts only the recorded Stage-1 dispatch shape. It does not
qualify subsequent synthesis or serial application behavior.

## Scenario

3 unresolved items in a Clarify session, each tagged `[ambiguous]` (so
all 3 analysts are routed per item). Expected: 9 background analyst
dispatches (3 items × 3 analysts) all in ONE assistant message.

## Asserts

- ≥9 background dispatches happen
- Dispatches include `codebase-analyst`, `spec-context-analyst`, and
  `domain-researcher`
- No forbidden spawns (subagents don't nest)
- `grill-me` is NEVER invoked (autopilot HITL boundary)
- All 9 dispatches occur in the same assistant message
  (`same_message_dispatch_groups`)
- Every dispatch sets `run_in_background: true` (`must_run_in_background`)

## When this fixture would fail

- If a future change reverts to per-item serial dispatch, the fixture still
  sees 9 dispatches, but they land in 3 separate assistant messages, so
  `same_message_dispatch_groups` fails.
- If the analysts run in the foreground, `must_run_in_background` fails.
- If routing breaks and only 1 analyst per item is spawned (3 total)
  instead of 3 per `[ambiguous]` item, the dispatch count check fails.
