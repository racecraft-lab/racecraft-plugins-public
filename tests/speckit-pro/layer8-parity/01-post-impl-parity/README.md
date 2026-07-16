# Parity Fixture 01 — Post-Implementation Equivalence (Use site 1)

Proves that the **Agent Teams path (Path A)** and **parallel-subagents
fallback path (Path B)** of the post-implementation parallel group
(`post-implementation.md` §Post-Implementation Parallel Group) produce
equivalent post-impl outcomes for the same workflow input.

This is the first fixture in Layer 8 — proving capability-driven
dispatch is **outcome-equivalent** across paths, not just shape-correct
(which Layer 7 already enforces).

## Test scenario

A tiny synthetic workflow.md with all 7 phases pre-populated (no real
LLM work in phases 1-7 — they short-circuit on the `--from-phase post`
marker). Post-impl tasks 10-14 are stubbed to no-op extensions that
return canned summaries.

The test:

1. **Path B run**: `env-fallback.json` unsets `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`;
   invokes autopilot; captures artifacts.
2. **Path A run**: `env-teams.json` sets `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
   (live mode also requires Claude Code ≥ 2.1.32); invokes autopilot;
   captures artifacts.
3. **Diff**: per `expected-equivalence.json` with tolerances from
   `tolerance.json`. PASS if all required fields match within
   tolerance; FAIL with field-level diff otherwise.

The PRSG-012 packet boundary is part of the parity surface. This fixture starts
without a current packet at
`specs/parity-01-post-impl/.process/pr-packets/<packet-id>.json`. Both paths must
use the active `pr-packet-output` helper to emit or refresh the packet before
any PR creation side effect, then validate it with `validate-pr-packet-read-only`
and persist current validation with `validate-pr-packet-write`. They must not ask
`generate-pr-body` to create packet JSON or claim that read-only validation
persisted a validation file. Codex guidance must use the same boundary rather
than introducing a Codex-only packet path or validator copy.

## Mode

This fixture is **live-mode only** — the whole point is to verify that
two different real execution paths produce equivalent answers from the
model. Replay mode is not meaningful.

The dry-run validation (`python3 run-parity-fixtures.py --dry-run`)
verifies the fixture structure, versioned JSON contracts, compare/tolerance
cross-references, and every row in `## Required Invariants` without invoking
claude -p. Live mode enforces those rows against both captured workflow
outputs before comparing the two paths.

## Cost

Per-fixture-pair budget: \$20 (configurable via
`L8_FIXTURE_BUDGET_USD`). A typical 7-phase + post-impl autopilot run
on this synthetic workflow.md costs \$3-5 in subagents mode and \$5-10
in teams mode (additional teammate context windows). Two runs per
fixture invocation.

## Status

**Ready.** The fixture structure validates via dry-run, including the
feature-local packet path, active packet-emission expectation, no read-only
persistence claim, and no post-create repair fallback invariant. Live execution
is explicit and budgeted; `semantic-equivalent` comparisons remain skipped with
a warning.
