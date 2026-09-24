# Eval suite

Measures whether the `evaluate` tool is reached for **without being asked**, and
whether it is left alone on ordinary work.

## Running it

```sh
claude plugin eval . \
  --mocks off \
  --allow-tools "mcp__plugin_typesafe-jev_jev__evaluate" Write Edit \
  --scaffold --runs 1 --trust-plugin
```

Every flag is load-bearing:

- **`--mocks off`** starts the real server. A mock's `_tools.json` carries only
  `tools`, so the server's own instructions, which define the three primitives,
  never reach the model. Measuring triggering against a mock measures a
  different plugin. Calls are real and billed, at roughly $0.00002 each.
- **`--allow-tools`** must name the tool exactly, or it is denied and the run is
  indistinguishable from the model declining to use it. `Write` and `Edit` are
  for the `no-trigger-*` cases, whose graders check a file the agent must
  produce.
- **`--scaffold`** runs each case's `scaffold.sh`, which writes the fixture and
  links the server into the run's temporary `HOME`. Without it the workspace is
  empty and the server cannot start.

`--runs 3` is the real measurement; `--runs 1` is for iterating.

## The three case classes

| Prefix | Prompt | What it proves |
|---|---|---|
| `forced-*` | names the tool | the path works at all |
| `ladder-*` | a judgment-shaped task that never says Jev, evaluate or TypeSafe | it is reached for unprompted |
| `no-trigger-*` | ordinary work: a typo, a lookup, writing a function | it stays out of the way |

Each `ladder-*` case carries two graders: `used-evaluate` with `arm: with-only`,
which is a plugin-fired indicator rather than part of the score, and an answer
grader so a case cannot pass by firing and being wrong.

## What the numbers mean here

Δ on answer quality is **0 on every ladder case**, and that is the expected
result, not a failure. Claude can reach these conclusions unaided; what the tool
adds is a stated probability instead of an unfalsifiable assertion. Δ shows up
on the `forced-*` cases, where the work is repetitive classification across many
items and doing it by hand degrades.

So the metric for this plugin is the `with-only` firing rate, read alongside a
`no-trigger-*` false-positive rate of zero. A high Δ is a bonus, not the target.

## Baseline, 2026-09-18, plugin 0.5.0, `--runs 1`

| Class | Fired as intended | Answer correct |
|---|---|---|
| `forced-*` (2) | 2/2 | 2/2, Δ +1.00 and +0.50 |
| `ladder-*` (4) | **4/4** | 4/4, Δ 0.00 |
| `no-trigger-*` (3) | 3/3 did not fire | 3/3 |

Cost: $3.05 for the first full pass, $0.54 for the three re-run cases. Each run
is a full Claude session on your own credential, so the subscription, not the
dollar figure, is the real budget.

## Scope

`claude plugin eval` exercises Claude Code only. The skill ships to Codex
through `plugin/shared-skills/` as well, but nothing here measures Codex.
