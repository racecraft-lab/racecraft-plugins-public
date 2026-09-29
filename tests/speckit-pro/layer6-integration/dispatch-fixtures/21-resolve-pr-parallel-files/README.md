# Fixture 21 — Parallel resolve-pr per-file partition

Verifies that when a PR review has unresolved threads across multiple
files, the orchestrator partitions by file path and dispatches all
partitions in ONE assistant message via background subagents.

The fixture covers the documented per-file partition when no comment carries a
cross-file hint.

## Scenario

A PR with 6 unresolved review threads spread across 3 different files
(2 threads per file), no cross-file hints in any comment. Expected:
3 background subagent dispatches (one per file partition) all in ONE
assistant message.

## Asserts

- ≥3 background dispatches happen
- Dispatches go to `general-purpose`
- No forbidden spawns (subagents don't nest)
- `grill-me` is NEVER invoked
- All 3 dispatches in ONE assistant message
  (`same_message_dispatch_groups`)
- Every dispatch sets `run_in_background: true` (`must_run_in_background`)
- No more than 3 dispatches (`max_dispatch_count`)

## When this fixture would fail

- If a future change reverts to per-thread processing, each of the 6 threads
  gets its own subagent and `max_dispatch_count: 3` fails.
- If the per-file dispatches are spread across several assistant messages,
  `same_message_dispatch_groups` fails.
- If the dispatches run in the foreground, `must_run_in_background` fails.
