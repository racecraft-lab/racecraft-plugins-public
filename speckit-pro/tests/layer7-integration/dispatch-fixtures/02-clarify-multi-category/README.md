# Fixture 02 — Clarify, multi-category dispatch

## What this fixture proves

A multi-category tag like `[codebase, domain]` must dispatch BOTH analysts
in Round 1, not just one. If the orchestrator fan-outs only to the first
listed category, dispatch is broken — this fixture catches that.

This also verifies the partial fan-out boundary: `spec-context-analyst`
must NOT be dispatched because `[spec]` is absent from the tag.

## Assertions

- `codebase-analyst` is dispatched at least once
- `domain-researcher` is dispatched at least once
- `spec-context-analyst` is **never** dispatched
- `grill-me` is **never** dispatched (HITL guard)
- No subagent spawns another `Agent()` (Anthropic constraint)
- Dispatch count in [2, 3]
