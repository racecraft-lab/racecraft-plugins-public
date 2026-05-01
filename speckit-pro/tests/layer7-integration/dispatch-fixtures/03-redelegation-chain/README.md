# Fixture 03 — Redelegation chain (multi-hop)

## What this fixture proves

This is the core L7 test: the orchestrator must hand off to a subagent,
**regain control when that subagent returns**, then dispatch a different
subagent based on what was returned. Single-hop tests cannot prove this.

Specifically, this fixture exercises:

1. orchestrator → `clarify-executor` (hop 1)
2. clarify-executor returns with category-tagged unresolved items
3. orchestrator (back in control) → analyst(s) (hop 2)
4. analysts return findings
5. orchestrator (back in control) → `consensus-synthesizer` (hop 3)

If the orchestrator stayed inside the clarify-executor's context (no
return), or if clarify-executor itself spawned analysts (forbidden by
Anthropic's no-subagent-spawning-subagents rule), the chain is broken.
This fixture detects both failure modes.

## Assertions

- `clarify-executor` is dispatched
- `consensus-synthesizer` is dispatched
- At least one consensus analyst is dispatched
- Order: `clarify-executor` precedes `consensus-synthesizer`
- No subagent spawns another `Agent()`
- `grill-me` is never dispatched

## Caveats

This fixture requires a SpecKit fixture spec at
`.specify/fixtures/spec-fixture-003/spec.md`. Capture-time setup is
handled by the runner.
