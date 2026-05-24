# Layer 8 — Parity Fixtures (subagents-mode vs teams-mode)

## Why this layer exists

Layer 7 dispatch fixtures verify the **shape** of the orchestrator's
dispatch graph: which subagents are spawned, in what order, with what
arguments. They do NOT verify that two different dispatch strategies
produce equivalent **outcomes**.

The D3-with-Teams pilot introduces an opt-in `post-impl-mode: teams`
that delegates the post-implementation parallel group (tasks 10/11/12/
13/14) to an Agent Team instead of sequential `Agent()` calls. The user-
visible contract is that **teams mode and subagents mode produce
equivalent post-implementation outcomes** for the same workflow input.

Layer 8 is the harness that proves it.

## What a parity fixture asserts

For each fixture, run the same workflow twice:

1. **subagents-mode baseline run** (`post-impl-mode: subagents` or unset)
2. **teams-mode run** (`post-impl-mode: teams`, env var set, Claude
   Code ≥ 2.1.32)

Then compare:

- **Artifact byte-identity** (with tolerance): `spec.md`, `plan.md`,
  `tasks.md` must be byte-identical OR semantically equivalent under
  a markdown-normalizing diff (ignore trailing whitespace, list-item
  ordering inside `[Gap]` enumerations).
- **Workflow-file Post-Implementation Checklist**: row count identical,
  same task status per row (pass/fail/skipped), same Findings column
  modulo LLM-driven prose variance.
- **Gate results**: every gate G0–G7 returns identical PASS/FAIL.
- **PR body content**: byte-identical (PR body generation is
  deterministic post-implementation).

Tolerance band:
- 0 difference for spec content (FRs, acceptance criteria, user stories)
- ≤1 row difference in Consensus Resolution Log (LLM non-determinism)
- Prose differences in Findings are allowed; semantic equivalence required

## Why this is a separate layer

- **Live mode only** — both runs invoke `claude -p` against real LLMs.
  Replay mode is not meaningful because the whole point is to test that
  parallel-vs-serial execution produces equivalent answers from the
  model, not the parser.
- **Cost** — each fixture is two full autopilot runs. Budget per
  fixture should be capped (suggest `$L8_FIXTURE_BUDGET_USD=$20` per
  fixture pair).
- **Opt-in** — Layer 8 must NOT run in CI default. It requires
  developer opt-in via `bash tests/run-all.sh --parity` (proposed).

## Status — scaffolding only

This directory currently contains only this README. The runner script,
fixture format, normalizing-diff helper, and at least one initial
fixture (`01-post-impl-parity`) are follow-up work.

**Why scaffold now**: documenting the harness pattern lets the
D3-with-Teams pilot ship the design + opt-in plumbing in this PR
without committing to immediate parity validation. The runner and
fixture authoring belong in a dedicated PR where they can be reviewed
and budgeted independently.

## Planned fixture: `01-post-impl-parity`

The first parity fixture would test the D3-with-Teams pilot end-to-end:

```
01-post-impl-parity/
├── README.md            # Intent
├── workflow.md          # Tiny synthetic spec with all 7 phases pre-populated
├── settings-subagents.md  # .claude/speckit-pro.local.md for baseline
├── settings-teams.md      # .claude/speckit-pro.local.md for teams mode
├── tolerance.json         # Per-field tolerance config
└── expected-equivalence.json  # Fields that must match byte-for-byte
```

The runner would:

1. Set `post-impl-mode: subagents`, run autopilot, capture artifacts
2. Reset, set `post-impl-mode: teams` + env var, run autopilot, capture
3. Diff per `expected-equivalence.json`
4. Report PASS if all required fields match within tolerance; FAIL with
   field-level diff otherwise

## Related references

- `skills/speckit-autopilot/references/post-implementation.md` §Mode Selection
- `skills/speckit-autopilot/references/prerequisites.md` §post-impl-mode probe
- Anthropic: [Agent Teams](https://code.claude.com/docs/en/agent-teams)
