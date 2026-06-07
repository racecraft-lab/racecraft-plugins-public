# Fixture 20 — Multi-item consensus batched dispatch (WS-D1)

Verifies that when a consensus phase (Clarify / Checklist / Analyze)
produces multiple unresolved items, the orchestrator dispatches all
routed analysts for all items in **ONE assistant message** (background
fan-out), not per-item sequentially.

This is the regression safety net for **Use site 5** in the
[Agent Teams integration map](../../../../skills/speckit-autopilot/references/agent-teams-integration.md)
— the batched-parallel-subagents path that's the default consensus
dispatch shape. Per
[`consensus-protocol.md`](../../../../skills/speckit-autopilot/references/consensus-protocol.md)
§Batched Dispatch, the canonical 3-stage flow is:

1. Stage 1 — all routed analysts for all items in ONE assistant message
2. Stage 2 — all synthesizers in ONE message
3. Stage 3 — apply Artifact Edits serially

The fixture asserts the Stage 1 shape (the most regression-prone stage).
Synthesizer batching (Stage 2) and serial application (Stage 3) are
behavior the orchestrator handles after the parser-fixture's recorded
dispatches; testing them live would require an end-to-end fixture
(Layer 8 parity territory).

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
- All 9 dispatches occur in the same assistant message (parser checks
  this implicitly via the single `tool_use` block list)

## When this fixture would fail

- If a future change reverts to per-item serial dispatch (the
  WS-D1-pre-shipped state), the fixture would still see 9 dispatches —
  but they'd be in 3 separate assistant messages, not 1. The
  parser-fixture's transcript shape captures this.
- If routing breaks and only 1 analyst per item is spawned (3 total)
  instead of 3 per `[ambiguous]` item, the dispatch count check fails.

See `agent-teams-integration.md` §Use site 5 for the design rationale
and the audit B2 finding that originally surfaced this optimization.
