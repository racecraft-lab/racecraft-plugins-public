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

## Coverage matrix

L7 covers every named subagent and every routing branch in
`/speckit-pro:autopilot`. The fixtures are organized by what they
exercise:

### Consensus routing (Class 1, fixtures 01–11)

| Fixture | Routing tag | Expected dispatch |
|---|---|---|
| 01 | `[codebase]` | codebase-analyst |
| 02 | `[codebase, domain]` | codebase-analyst + domain-researcher |
| 03 | `[codebase, domain]` (in clarify→analyst chain) | redelegation chain |
| 04 | `[domain]` | domain-researcher |
| 05 | `[spec]` | spec-context-analyst |
| 06 | `[security]` | all 3 (defense-in-depth) |
| 07 | `[ambiguous]` | all 3 (uncertainty fan-out) |
| 08 | `[codebase, spec]` | codebase-analyst + spec-context-analyst |
| 09 | `[domain, spec]` | domain-researcher + spec-context-analyst |
| 10 | `[codebase, domain, spec]` | all 3 (explicit fan-out) |
| 11 | Round 1 escape-hatch | Round 2 fans out remaining analysts |

### Phase agents (Class 1, fixtures 12–16)

| Fixture | Phase | Expected agent |
|---|---|---|
| 12 | Tasks | phase-executor |
| 13 | Implement (per task) | implement-executor |
| 14 | Analyze | analyze-executor |
| 15 | Checklist (per domain) | checklist-executor |
| 16 | Gate validation | gate-validator |

### Failure paths (Class 1, fixture 17)

| Fixture | Scenario |
|---|---|
| 17 | Phase-executor returns error → orchestrator does not retry blindly, does not escalate to grill-me |

### Cross-agent parsing (Class 2, fixtures 01–03)

| Fixture | Cross-agent flow |
|---|---|
| 01 | analysts disagree → synthesizer emits no-majority result |
| 02 | analysts agree → synthesizer emits majority decision |
| 03 | checklist-executor output → orchestrator parses gaps + remediations |

### End-to-end (Class 3, fixtures 01–02)

Both Class 3 fixtures share the same `E2E_FIXTURE_BUDGET_USD` default
of $10.00. Fixture 01 typically uses ~$1; fixture 02 typically uses
~$1.30; the cap exists for runs that take longer paths.

| Fixture | Phases covered |
|---|---|
| 01 | G1–G3 (Specify → Clarify → Plan) |
| 02 | G1–G7 (Specify → Clarify → Plan → Checklist → Tasks → Analyze → Implement) |

### Subagents reached

Every named subagent appears in at least one fixture:

- ✅ `phase-executor` — fixtures 12, 16 (gate); E2E 01, 02
- ✅ `clarify-executor` — fixture 03 (redelegation); E2E 01, 02
- ✅ `checklist-executor` — fixture 15; Class 2 fixture 03
- ✅ `analyze-executor` — fixture 14; E2E 02
- ✅ `implement-executor` — fixture 13; E2E 02
- ✅ `codebase-analyst` — fixtures 01, 02, 03, 06, 07, 08, 10
- ✅ `domain-researcher` — fixtures 02, 03, 04, 06, 07, 09, 10, 11
- ✅ `spec-context-analyst` — fixtures 05, 06, 07, 08, 09, 10, 11
- ✅ `consensus-synthesizer` — Class 2 fixtures 01, 02
- ✅ `gate-validator` — fixture 16

### What is asserted negative on every fixture

- **`grill-me` is never invoked** (HITL boundary). Asserted two ways:
  1. `must_not_dispatch_to: ["speckit-pro:grill-me"]` — catches the
     unlikely-but-possible case where an orchestrator tries to
     dispatch grill-me as if it were an `Agent` subagent_type. The
     plugin does not register grill-me as an agent, so this should
     never match — but the assertion is cheap insurance.
  2. `must_not_invoke_skill: ["grill-me"]` — the **canonical** check.
     `grill-me` is a Skill, not an Agent. It is invoked via the
     `Skill` tool (`Skill('speckit-pro:grill-me')`) or by typing
     `/speckit-pro:grill-me` in chat. The parser scans every
     `Skill` `tool_use` block in the transcript (orchestrator and
     sidechain scope) and asserts none match the `grill-me` regex.
- No subagent spawns another `Agent()` (Anthropic constraint).

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

## Transcript PII scrubbing

Raw `claude -p --output-format stream-json` transcripts contain
machine-specific metadata: `cwd` under `/Users/<username>/...`,
session UUIDs, request IDs, git branch names, and full plugin/tool
inventories. None of that is needed for the L7 parser, and committing
it leaks developer-machine information.

Every committed transcript in this directory has been scrubbed via
`scrub-transcript.sh`. The runners now invoke the scrubber
**automatically** after every `--live` capture, so a live re-run
produces a scrubbed transcript on disk in one step.

What the scrubber preserves (parser-essential):

- `type`, `subtype`, `isSidechain`
- `message.role`, `message.content` (`tool_use` and `tool_result` blocks)
- `input.subagent_type`, `input.skill`, `input.prompt`, `input.description`,
  `input.args`
- `tool_use_id` and tool_use `id` (for joining dispatch → response)

What the scrubber strips/replaces:

| Field | Replacement |
|---|---|
| `cwd`, `sessionId`/`session_id`, `gitBranch`, `requestId`, `userType`, `origin`, `entrypoint`, `inference_geo` | `"<scrubbed>"` |
| Any `/Users/<x>/...` or `/home/<x>/...` substring inside any string | `<HOME>` |
| `system` events (which carry plugin/tool inventories) | reduced to `{type, subtype}` |

To manually scrub a transcript:

```bash
bash tests/layer7-integration/scrub-transcript.sh path/to/transcript.jsonl
# in-place; or pass nothing to read stdin → stdout
```

## Live-mode side effects (read this before running `--live`)

`--live` invocations spawn real subagents that may produce real
artifacts in the working directory. Observed examples:

- `phase-executor` running the Tasks phase has been observed writing
  a real `tasks.md` next to the fixture's `sample-spec.md`.
- `implement-executor` doing a TDD cycle has been observed writing
  test files into the project's actual test directory.
- `phase-executor` invoked with a "re-run Specify with corrective
  prompt" instruction (fixture 17 error-handling path) has been
  observed creating a real `specs/00X-...` directory.

These artifacts are not part of the committed fixture set. Before
running `--live`:

1. Commit or stash any unrelated work.
2. After the run, review `git status` for unexpected new files and
   `git clean -fd` (or selectively delete) the side-effect artifacts.
3. Or run from an isolated git worktree (recommended for the
   `02-autopilot-extended-pipeline` fixture, which dispatches
   implement-executor).

The committed fixture transcripts capture only the dispatch graph
(stream-json events) — not the side-effect files. So these artifacts
have no influence on `--replay` results; they are purely working-tree
litter from the live capture process.

## Cost guards

`--live` mode wraps each `claude -p` invocation with `--max-budget-usd`.
Defaults:

| Class | Default cap | Override env var |
|-------|-------------|------------------|
| 1 | $1.00 | `DISPATCH_FIXTURE_BUDGET_USD` |
| 2 | $1.00 | `RETURN_FORMAT_FIXTURE_BUDGET_USD` |
| 3 | $10.00 | `E2E_FIXTURE_BUDGET_USD` |

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
