# Layer 7 — Behavioral Parity

## Automated gate and interactive verification

The automated release gate compares Claude Code and Codex against the same
behavioral requirements. Each client must independently satisfy its required
outcomes before comparison: matching incorrect results never constitute a pass.
Native tools may differ, but normalization must preserve ownership, ordering,
required work, and side effects.

Claude runs through the official plugin evaluation runner; Codex runs through
native `codex exec`. The shared evaluation entrypoint and canonical catalog are
being integrated under `../evals/`. Their contract tests are not evidence that
the full behavioral corpus has passed.

Genuine Claude agent teams require an interactive session. They are **separate
manual verification**, not an automated parity arm, not a claimed live pass,
and not a blocker for this PR under the approved scope amendment. This exception
does not waive other interactive skill requirements, such as interviewing the
user. See [Anthropic's agent-team documentation](https://code.claude.com/docs/en/agent-teams).

For separate team verification, record the client version, enabled capability,
workflow input, actual team/task/message evidence, resulting artifacts, and each
independent workflow invariant. Compare with the automated workflow only after
both satisfy those invariants. An environment variable, ordinary background
subagent, or final claim of team execution does not prove a genuine team ran.

## Legacy fixture migration boundary

The material below describes the retained legacy fixture format and runner.
Its headless teams-versus-fallback procedure cannot establish genuine team
execution on the current client. Preserve it for audit and deterministic parser
regression coverage while replacements are qualified; do not use its live
command as the new Layer 7 release gate. The audit and replacement mapping live
in `../evals/audit/integration-parity-audit.md`.

## Why this layer exists

Layer 6 dispatch fixtures verify the **shape** of the orchestrator's
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
the autopilot auto-routes based on capability detection. Layer 7 is
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
- **PR packet boundary**: identical feature-local packet lookup and deferred
  blocker behavior. A missing current packet stops both paths before PR body or
  PR creation side effects.

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
  fixture should be capped (suggest `$L7_FIXTURE_BUDGET_USD=$20` per
  fixture pair).
- **Opt-in for the developer running tests** (not user opt-in for the
  product) — Layer 7 must NOT run in CI default. It requires
  developer opt-in via
  `python3 tests/speckit-pro/layer7-parity/run-parity-fixtures.py --live`.

## Status

The Python runner, extractor helpers, four fixture cases, and portable JSON
environment contracts are implemented. Dry-run validation is deterministic
and free. It validates the versioned expected/tolerance schemas, cross-checks
every compare source and tolerance key, and evaluates declared required
invariants against `workflow.md`. Live mode evaluates the same invariants
independently against both captured outputs before parity comparison. Live
validation remains developer-triggered because it runs two budgeted
`claude -p` processes per fixture.

## Fixture: `01-post-impl-parity`

The first parity fixture tests the capability-driven post-impl
group end-to-end:

```
01-post-impl-parity/
├── README.md                  # Intent
├── workflow.md                # Tiny synthetic spec with all 7 phases pre-populated
├── env-fallback.json          # Environment values to set/unset for Path B
├── env-teams.json             # Environment values to set/unset for Path A
├── tolerance.json             # Per-field tolerance config
└── expected-equivalence.json  # Fields that must match byte-for-byte
```

The runner:

1. Run autopilot with Agent Teams disabled → capture artifacts (Path B)
2. Reset, run autopilot with Agent Teams enabled → capture (Path A)
3. Diff per `expected-equivalence.json`
4. Report PASS if all required fields match within tolerance; FAIL
   with field-level diff otherwise

## Related references

- `skills/speckit-autopilot/references/post-implementation.md` §Post-Implementation Parallel Group
- `skills/speckit-autopilot/references/prerequisites.md` §Agent Teams capability probe
- Anthropic: [Agent Teams](https://code.claude.com/docs/en/agent-teams)
