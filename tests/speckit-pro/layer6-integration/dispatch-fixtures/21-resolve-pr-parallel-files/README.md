# Fixture 21 — Parallel resolve-pr per-file partition

Verifies that when a PR review has unresolved threads across multiple
files, the orchestrator partitions by file path and dispatches all
partitions in ONE assistant message via background subagents.

The fixture covers the documented per-file partition when no comment carries a
cross-file hint. The contract is `skills/speckit-resolve-pr/SKILL.md` §4c.
It dispatches only when there are 2 or more partitions and the fixes are
large enough to repay each worker's setup cost, and the prompt states that
both conditions hold.

## Scenario

A PR with 6 unresolved review threads spread across 3 different files
(2 threads per file), no cross-file hints in any comment. Expected:
3 background subagent dispatches (one per file partition) all in ONE
assistant message. Each thread needs a multi-line fix, so the dispatch is
worth its setup cost.

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
