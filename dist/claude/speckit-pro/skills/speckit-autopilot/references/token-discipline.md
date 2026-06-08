# Token-Discipline Reference (opt-in)

This reference defines a compressed vocabulary for inter-agent
transcripts inside the speckit-pro autopilot. It is **opt-in**
and ships **disabled** by default. When enabled, the autopilot
substitutes short symbols and fragment patterns for verbose
English in subagent-to-orchestrator messages — reducing per-turn
token usage on the parts of the workflow no human reads
directly.

The vocabulary is adapted from
[SuperClaude_Framework](https://github.com/SuperClaude-Org/SuperClaude_Framework)'s
`MODE_Token_Efficiency.md`. We use a smaller symbol set than
SuperClaude because the SDD workflow's vocabulary is already
narrow (phases, gates, findings, artifacts).

## Hard Scope — What Token Discipline Touches

Token discipline applies **only** to:

- Subagent → orchestrator return summaries (the "result"
  payload of an `Agent(...)` / `spawn_agent` call)
- Orchestrator → subagent dispatch prompts (the "prompt"
  argument)
- Internal multi-agent debate transcripts (consensus rounds)

Token discipline does **not** touch:

- PR bodies, PR titles, commit messages, CHANGELOG entries
  — these are public-readable, governed by
  [CLAUDE.md §Contributing](../../../../CLAUDE.md#contributing--branching-strategy)
- Workflow log entries that a human reviews
  (Self-Review block, Consensus Resolution Log, gate decisions)
- Operator-facing status output, error messages, or progress
  reports
- Any text that lands in `spec.md`, `plan.md`, `tasks.md`,
  `data-model.md`, or `contracts/*`
- TaskUpdate `subject` / `description` fields, since the
  TaskList tool surfaces them to the operator

If a transcript could end up in front of a human — directly or
via a future PR body generation step — it is **not eligible** for
compression. When in doubt, write full English.

## Enabling Token Discipline

In `.claude/speckit-pro.local.md` (or `.codex/speckit-pro.local.md`):

```yaml
token_discipline: on
```

Default: `off`. The autopilot's prerequisites step
(`detect-presets.sh` / Step 0.6) reads this value and sets
`TOKEN_DISCIPLINE` for every subsequent subagent dispatch.

When `token_discipline: on`, the orchestrator's dispatch prompt
includes a one-line directive:

> Return your summary using the compressed vocabulary in
> [token-discipline.md](../references/token-discipline.md). Apply
> to your return payload only — never to text you would write
> into an artifact, log, or commit message.

Subagents that don't understand the vocabulary fall back to
plain English without penalty. The vocabulary is an
optimization, not a requirement.

## Symbol Vocabulary

These are the symbols an agent may substitute for the listed
phrases in eligible transcripts.

| Symbol | Meaning | Use instead of |
|--------|---------|----------------|
| `→` | leads to, results in, then | "leads to", "results in", "next step", "and then" |
| `⇒` | implies, therefore | "therefore", "this implies" |
| `∵` | because, since | "because", "since", "the reason is" |
| `∴` | so, thus | "thus", "so", "as a result" |
| `&` | with, joined to | "with", "alongside", "in conjunction with" |
| `+` | and (joining items) | "and" in lists |
| `Δ` | change, delta, diff | "the change is", "delta", "the difference" |
| `✓` | passed, done, satisfied | "passed", "completed", "satisfied", "done" |
| `✗` | failed, blocked | "failed", "blocked", "did not pass" |
| `?` | unknown, unresolved | "unknown", "unresolved", "TBD" |
| `↑` | improved, increased | "improved", "increased", "up" |
| `↓` | regressed, decreased | "regressed", "decreased", "down" |
| `~` | approximately, around | "approximately", "around", "roughly" |

Use a symbol when the phrase is the entire semantic content of
the message. Do not pile up symbols where a short noun is
clearer. `✓ G6` is better than `✓✓ G6 ↑`.

## Fragment Patterns

When token discipline is on, subagent return summaries may use
bullet fragments instead of full sentences:

```text
G6: ✓
findings: 0 unresolved
edge cases: T015, T022, T030 cover non-happy paths
remediation: none needed
→ ready for G6.5
```

Compare to the same content in plain English:

```text
G6 passed. There are 0 unresolved findings. Edge cases are
covered by tests T015, T022, and T030, which exercise the
non-happy paths. No remediation is needed. The workflow is
ready to proceed to G6.5.
```

The compressed form is ~5x shorter and conveys the same
information when the reader is another agent that has the full
SDD vocabulary loaded.

### Permitted abbreviations

These are SDD-specific shortenings that are unambiguous in
context:

- `req` for "requirement" (FR-XXX)
- `tsk` for "task" (T###)
- `art` for "artifact" (spec.md, plan.md, etc.)
- `crit` for "criterion" / "criteria"
- `imp` for "implementation"
- `ver` for "verification"
- `rem` for "remediation"

Avoid abbreviating SpecKit phase names. `specify`, `plan`,
`tasks`, `analyze`, `implement`, `clarify`, `checklist` are
already short and have hard meanings.

## Anti-Patterns

Three patterns to actively avoid even when token discipline is
on:

1. **Don't compress when the message contains a quote.** If you
   are surfacing the exact text of a finding, requirement, or
   spec excerpt, render it verbatim. Compression is for the
   agent's own summary, not for the source material it cites.

2. **Don't invent new symbols mid-conversation.** Use only the
   table above. A symbol the orchestrator doesn't know is worse
   than a verbose phrase.

3. **Don't compress error messages.** If a subagent encountered
   a failure, the full error message (stderr, stack trace,
   command output) is part of the return payload. Compressing
   it makes debugging impossible.

## Disabling

To turn token discipline off after enabling it, set
`token_discipline: off` in the same config file. No restart
needed — the next autopilot invocation re-reads the config at
Step 0.6 (or 0.6b for Codex).

## Why Opt-In

The autopilot's quality bar (every agent at `effort: max` per
the speckit-coach policy) is the primary design choice. Token
discipline trades some agent-to-agent legibility for fewer
tokens. For operators running headless overnight with budget
caps, that trade is often worth it; for interactive sessions
where readable transcripts aid debugging, it usually is not.
Keeping it opt-in respects both preferences.

The Layer 6 efficiency benchmarks
(`tests/layer6-efficiency/`) do not currently measure
token-discipline impact. If a future PR demonstrates a
quality-neutral cost savings, the default may flip. Until then,
the default is `off` and operators choose.
