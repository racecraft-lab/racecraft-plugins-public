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

## Required setup

The fixture is **self-contained**. The minimal spec lives at
`sample-spec.md` next to this README, and `prompt.txt` references it
by an in-repo path. No external setup needed for either replay or live
mode.
