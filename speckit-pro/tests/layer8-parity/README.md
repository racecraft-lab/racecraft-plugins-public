# Layer 8 — Parity Fixtures (teams-when-available vs parallel-subagents-fallback)

## Why this layer exists

Layer 7 dispatch fixtures verify the **shape** of the orchestrator's
dispatch graph: which subagents are spawned, in what order, with what
arguments. They do NOT verify that two different dispatch strategies
produce equivalent **outcomes**.

The capability-driven post-impl design has two code paths:

- **Path A (Agent Teams):** when Anthropic's Agent Teams is detected
  (env var + version), the post-implementation parallel group
  dispatches as a 3-teammate team with shared task list and
  inter-teammate messaging.
- **Path B (Parallel subagents):** when Agent Teams is unavailable,
  the same 3 tracks dispatch as background `Agent(..., run_in_background:
  true)` calls in one tool turn.

Both paths deliver the same contract: 3 parallel tracks (Doctor /
Code Review / Verify-chain), lead synthesizes findings into the
workflow file, serial tail from task 15. Users do not opt-in —
the autopilot auto-routes based on capability detection. Layer 8 is
the harness that proves the two paths produce equivalent outcomes
for the same workflow input.

## What a parity fixture asserts

For each fixture, run the same workflow twice on the same machine:

1. **Subagents-fallback run** — env var unset, Claude Code on any
   supported version. Forces Path B.
2. **Teams run** — env var set, Claude Code ≥ 2.1.32. Forces Path A.

Then compare:

- **Artifact byte-identity** (with tolerance): `spec.md`, `plan.md`,
  `tasks.md` must be byte-identical OR semantically equivalent under
  a markdown-normalizing diff (ignore trailing whitespace, list-item
  ordering inside `[Gap]` enumerations).
- **Workflow-file Post-Implementation Checklist**: row count
  identical, same task status per row (pass/fail/skipped), same
  Findings column modulo LLM-driven prose variance.
- **Gate results**: every gate G0–G7 returns identical PASS/FAIL.
- **PR body content**: byte-identical (PR body generation is
  deterministic post-implementation).

Tolerance band:
- 0 difference for spec content (FRs, acceptance criteria, user stories)
- ≤1 row difference in Consensus Resolution Log (LLM non-determinism)
- Prose differences in Findings are allowed; semantic equivalence required

## Why this is a separate layer

- **Live mode only** — both runs invoke `claude -p` against real LLMs.
  Replay mode is not meaningful because the whole point is to test
  that two different execution strategies produce equivalent answers
  from the model, not the parser.
- **Cost** — each fixture is two full autopilot runs. Budget per
  fixture should be capped (suggest `$L8_FIXTURE_BUDGET_USD=$20` per
  fixture pair).
- **Opt-in for the developer running tests** (not user opt-in for the
  product) — Layer 8 must NOT run in CI default. It requires
  developer opt-in via `bash tests/run-all.sh --parity` (proposed).

## Status — scaffolding only

This directory currently contains only this README. The runner script,
fixture format, normalizing-diff helper, and at least one initial
fixture (`01-post-impl-parity`) are follow-up work.

**Why scaffold now**: documenting the harness pattern lets the
capability-driven post-impl design ship now without committing to
immediate parity validation. The runner and fixture authoring belong
in a dedicated PR where they can be reviewed and budgeted independently.

## Planned fixture: `01-post-impl-parity`

The first parity fixture would test the capability-driven post-impl
group end-to-end:

```
01-post-impl-parity/
├── README.md                  # Intent
├── workflow.md                # Tiny synthetic spec with all 7 phases pre-populated
├── env-fallback.sh            # Unset env var, invoke autopilot
├── env-teams.sh               # Set CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1, invoke
├── tolerance.json             # Per-field tolerance config
└── expected-equivalence.json  # Fields that must match byte-for-byte
```

The runner would:

1. Run autopilot with Agent Teams disabled → capture artifacts (Path B)
2. Reset, run autopilot with Agent Teams enabled → capture (Path A)
3. Diff per `expected-equivalence.json`
4. Report PASS if all required fields match within tolerance; FAIL
   with field-level diff otherwise

## Related references

- `skills/speckit-autopilot/references/post-implementation.md` §Post-Implementation Parallel Group
- `skills/speckit-autopilot/references/prerequisites.md` §Agent Teams capability probe
- Anthropic: [Agent Teams](https://code.claude.com/docs/en/agent-teams)
