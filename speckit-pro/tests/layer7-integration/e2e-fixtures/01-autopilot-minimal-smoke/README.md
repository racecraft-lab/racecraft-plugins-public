# Fixture E2E-01 — Autopilot minimal smoke

## What this fixture proves

A real autopilot run through phases G0-G3 produces a dispatch graph
that:

- Dispatches `phase-executor` (the canonical phase agent)
- Never dispatches `grill-me` (HITL forbidden inside autopilot)
- Never dispatches `implement-executor` or `analyze-executor` (out of
  scope for G0-G3)
- Never spawns an Agent inside a subagent (Anthropic constraint)

This is structural — it does not assert *which specific decisions* were
made. Layer 3 functional evals own that. Layer 7 e2e owns the dispatch
graph shape.

## Cost

`--live` mode runs a real, multi-phase autopilot session. Budget cap
defaults to **$5.00** for this fixture (override with
`E2E_FIXTURE_BUDGET_USD`). Run sparingly — it is the most expensive
fixture in the test suite.

## Required setup for `--live` mode

> **Setup gap (TODO before first `--live` run):** the prompt references
> `.specify/fixtures/spec-minimal/spec.md`. That fixture spec is **not
> committed** in this PR. Before running `--live`, the developer must:
>
> 1. Create a minimal spec at `.specify/fixtures/spec-minimal/spec.md`
>    (one or two paragraphs describing a trivial feature).
> 2. Either copy that path into the live workspace or update
>    `prompt.txt` to a path that exists.
>
> Replay mode does not need the fixture spec — the committed
> `transcript.jsonl` is a synthetic seed.
