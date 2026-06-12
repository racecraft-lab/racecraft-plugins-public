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

1. **Path B run**: env-fallback.sh unsets `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`;
   invokes autopilot; captures artifacts.
2. **Path A run**: env-teams.sh sets `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
   (live mode also requires Claude Code ≥ 2.1.32); invokes autopilot;
   captures artifacts.
3. **Diff**: per `expected-equivalence.json` with tolerances from
   `tolerance.json`. PASS if all required fields match within
   tolerance; FAIL with field-level diff otherwise.

The PRSG-012 packet contract is part of the parity surface. Both paths
must render the same `.git/speckit-pr-packet.json`, use the shared
`speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`,
validate with the shared
`speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh`,
and write the same packet validation JSON before any PR creation side
effect. Codex guidance must reference those shared artifacts rather than
introducing duplicate Codex-only schema or validator copies.

## Mode

This fixture is **live-mode only** — the whole point is to verify that
two different real execution paths produce equivalent answers from the
model. Replay mode is not meaningful.

The dry-run validation (`bash run-parity-fixtures.sh --dry-run`)
verifies the fixture structure (required files present, JSON
well-formed) without invoking claude -p.

## Cost

Per-fixture-pair budget: \$20 (configurable via
`L8_FIXTURE_BUDGET_USD`). A typical 7-phase + post-impl autopilot run
on this synthetic workflow.md costs \$3-5 in subagents mode and \$5-10
in teams mode (additional teammate context windows). Two runs per
fixture invocation.

## Status

**Scaffolded.** Live execution logic is intentionally deferred in
`run-parity-fixtures.sh` — implementing it requires LLM token budget
approval and tested infrastructure for `claude -p` invocation. The
fixture structure validates today via dry-run, including packet/body
artifact paths, validator evidence, explicit PR create argument parity,
and the no post-create repair fallback invariant.
