# Layer 7 — Integration Fixtures (Dispatch Graph)

## Why this layer exists

Layer 3 functional evals test each agent in isolation: "does the
clarify-executor produce the right output for input X?" That is
necessary but not sufficient. The **multi-agent system** has a separate
class of bugs that only surface when agents are composed:

- The orchestrator routes a `[codebase]` consensus tag to the wrong
  analyst.
- A subagent (forbidden by Anthropic's no-subagent-spawning-subagents
  rule) spawns another `Agent()`.
- The orchestrator fails to regain control between subagent calls
  (no redelegation chain).
- One agent's response format drifts in a way that breaks another
  agent's parsing.
- Autopilot phase agents accidentally invoke `grill-me` (HITL
  forbidden in autopilot).

These are all **dispatch graph** failures. Layer 7 exists to catch them.

## Three fixture classes

| Class | Goal | Runner |
|-------|------|--------|
| **1 — Dispatch fixtures** | Verify the orchestrator routes specific inputs to the right subagent(s) | `run-dispatch-fixtures.sh` |
| **2 — Return-format fixtures** | Verify cross-agent parsing — one agent's output is parseable by its consumer | `run-return-format-fixtures.sh` |
| **3 — End-to-end fixtures** | Verify the dispatch graph for a real autopilot run has the expected shape | `run-e2e-fixtures.sh` |

## Two execution modes

Each runner supports two modes:

| Mode | What it tests | Cost |
|------|---------------|------|
| `--replay` (default) | The **parser**: extracts dispatch info from a committed `transcript.jsonl`. Catches "the parser stopped finding `subagent_type`" or "the JSONL schema changed." Does **not** verify routing — the routing decision was made and frozen at capture time. | Free, fast, deterministic |
| `--live` | The **routing**: invokes `claude -p`, captures a fresh transcript, then asserts. Catches "the orchestrator stopped routing `[codebase]` to codebase-analyst." | Real LLM tokens (capped per fixture via `--max-budget-usd`) |

The committed `transcript.jsonl` files are seed transcripts that may be
synthetic. They prove the parser+assertions work. Running `--live`
overwrites them with real captures and **then** the same assertions
become true routing tests.

## Quick start

```bash
# Replay all fixtures (free)
bash tests/layer7-integration/run-all-fixtures.sh

# Replay just Class 1
bash tests/layer7-integration/run-dispatch-fixtures.sh

# Replay one fixture, verbose
VERBOSE=true bash tests/layer7-integration/run-dispatch-fixtures.sh 03-redelegation-chain

# Live capture for one fixture (costs LLM tokens)
bash tests/layer7-integration/run-dispatch-fixtures.sh --live 01-clarify-codebase-only

# Live capture across the whole layer
bash tests/layer7-integration/run-all-fixtures.sh --live
```

## Fixture format

```text
<class>-fixtures/<NN-name>/
├── prompt.txt          # input given to claude -p (or to the orchestrator under test)
├── expected.json       # structural assertions about the dispatch graph
├── transcript.jsonl    # captured stream-json output (seed or real)
└── README.md           # what this fixture proves and why
```

### `expected.json` schema

```jsonc
{
  "fixture_id": "...",
  "purpose": "human-readable",

  // Class 1 + 3
  "must_dispatch_to": ["speckit-pro:codebase-analyst", ...],
  "must_dispatch_to_at_least_one_of": [...],
  "must_not_dispatch_to": [...],
  "must_not_have_forbidden_spawns": true,
  "min_dispatch_count": 1,
  "max_dispatch_count": 3,
  "dispatch_order_constraints": [
    { "before": "...", "after": "...", "reason": "..." }
  ],

  // Class 2
  "response_assertions": [
    {
      "subagent_type": "speckit-pro:consensus-synthesizer",
      "must_contain_any": ["bcrypt", "argon2"],
      "must_contain_section_keywords": ["decision", "rationale"]
    }
  ]
}
```

All assertion keys are optional — include only the ones relevant to the
fixture.

## Assertion philosophy

Per the dispatch architecture audit (PR #26), Layer 7 uses **structural
assertions**, not exact matches. LLMs are non-deterministic: a fixture
that asserts *exactly* `{codebase-analyst}` was called fails when an
LLM reroll picks `{codebase-analyst, domain-researcher}` for non-bug
reasons. Structural assertions ("for `[codebase]` tag, codebase-analyst
is in the dispatch set") survive that variance.

If you find yourself wanting an exact match, ask whether L3 functional
evals would catch it instead. L7 is for the dispatch graph; L3 is for
agent behavior.

## Cost guards

`--live` mode wraps each `claude -p` invocation with `--max-budget-usd`.
Defaults:

| Class | Default cap | Override env var |
|-------|-------------|------------------|
| 1 | $1.00 | `DISPATCH_FIXTURE_BUDGET_USD` |
| 2 | $1.00 | `RETURN_FORMAT_FIXTURE_BUDGET_USD` |
| 3 | $5.00 | `E2E_FIXTURE_BUDGET_USD` |

## How this fits with the other layers

| Layer | Tests | Speed |
|-------|-------|-------|
| L1 | File structure / frontmatter | Fast |
| L2 | Trigger evals (does the right skill activate?) | Slow (AI) |
| L3 | Functional evals (does each skill produce the right output?) | Slow (AI) |
| L4 | Shell script unit tests (incl. `transcript-helpers.sh`) | Fast |
| L5 | Agent tool-scoping | Fast |
| L6 | Agent efficiency benchmarks | Slow (AI) |
| **L7** | **Multi-agent dispatch graph** | **Fast (replay) / Slow (live)** |

L7 replay is fast enough to run with the default test suite. L7 live
is developer-local and runs only when explicitly requested via
`run-all.sh --integration --live`.

## Codex side

Layer 7 covers Claude Code dispatch only. Per the parity research at
`docs/ai/research/codex-parity-research-*.md`, OpenAI Codex has no
multi-agent / subagent primitive analogous to Claude Code's `Agent` tool
with `subagent_type`, so there is no dispatch graph to assert on. Codex
dispatch behavior, when it lands, will need a separate Layer 7 mirror
(or this directory will need to grow Codex fixtures next to the Claude
ones).

## When to add a new fixture

Add a new fixture when:

1. A new agent or subagent is introduced — verify the orchestrator can
   reach it.
2. A new consensus category or routing rule is added — verify it
   dispatches the right analyst(s).
3. A bug surfaces in the dispatch graph that would not be caught by
   L3 functional evals (e.g., wrong subagent selected, redelegation
   chain breaks, forbidden spawn).

Avoid adding a fixture for:

- Behavior already covered by L3 (single-agent input → output)
- Trigger drift (use L2)
- Tool scoping (use L5)
