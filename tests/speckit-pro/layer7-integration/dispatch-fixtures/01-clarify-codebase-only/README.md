# Fixture 01 — Clarify, codebase-only category

## What this fixture proves

When the orchestrator encounters a `[codebase]`-tagged unresolved item from
a clarify session, the Tier A category-routed dispatch protocol fires
exactly one analyst — `codebase-analyst` — and not the other two.

This is the simplest single-category routing case. If the orchestrator
fans out to all 3 analysts on a single-category tag, this fixture fails
and signals dispatch protocol drift.

## Assertions

- `codebase-analyst` is dispatched at least once
- `domain-researcher` is **never** dispatched
- `spec-context-analyst` is **never** dispatched
- `grill-me` is **never** dispatched (HITL guard)
- No subagent spawns another `Agent()` (Anthropic constraint)
- Total dispatches in [1, 2] (Round 2 escape may add synthesizer)

## How to run

```bash
# Replay against committed transcript (parser regression test)
bash tests/layer7-integration/run-dispatch-fixtures.sh --replay 01-clarify-codebase-only

# Live capture (real routing test, costs ~$0.10–0.50)
bash tests/layer7-integration/run-dispatch-fixtures.sh --live 01-clarify-codebase-only
```
