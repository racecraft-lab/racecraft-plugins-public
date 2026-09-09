# Executor mode paired eval design

Date: 2026-09-06. Status: design and harness scaffolding only. No change to
the implement-executor protocol, the TDD protocol, or any autopilot
reference lands with this record. The three modes below are candidates; the
shipped executor keeps strict red-green-refactor until the eval says
otherwise.

This is the "Quality Gauntlet" memo's item 8: decide, with evidence rather
than preference, whether strict red-green-refactor is the right default for
every task the autopilot dispatches.

## The three modes

| Mode | Name | Rule |
| --- | --- | --- |
| `strict` | Strict red-green-refactor | The shipped protocol. Write the failing test, prove it fails, write the minimum code, refactor. Every task. |
| `function_first` | Function-then-test with a mutation floor | Write the function, then its tests. The task passes only if the diff's mutation score clears the repository floor from `.specify/quality-gates.json`. |
| `boundary` | Strict at module boundaries, function-first inside | Classify each task from the plan's Module and Interface Deltas section. A task whose files carry a `new` or `changed` public interface runs `strict`; every other task runs `function_first`. |

### Classification for `boundary`

The plan template's Module and Interface Deltas section is one line per
module or public interface:

```text
- `module/or/interface` — [new / changed / removed: one-line delta]
```

A task is a **boundary task** when any file it names (from `tasks.md`) is
under, or equals, a path in a `new` or `changed` line. `removed` lines do
not make a task a boundary task, because the interface will not exist to
test. A plan that says "No module or interface changes." makes every task
an inside task. The classifier in the harness reads only these two
artifacts, so the same task always classifies the same way.

## Paired design

The unit of comparison is one task. Every mode runs the same task from the
same base commit with the same model and the same PROJECT_COMMANDS, and the
scorer pairs results by task id. A task with a missing mode result is
dropped from every pair, never scored as a loss.

- **Roster:** the case catalog at
  `tests/speckit-pro/layer3-functional/executor-modes/catalog.json`. Each
  case is a frozen task with its plan deltas, the files it touches, and the
  language. The catalog ships with three cases that cover a boundary task,
  an inside task, and a task under a plan with no deltas. Add cases by
  freezing real tasks from merged specs, never by pointing at a live
  `specs/<feature>/` path.
- **Repeats:** each (task, mode) pair runs `repeats` times (default 3) with
  distinct seeds. The scorer takes the median per (task, mode) before
  pairing, so one slow or lucky run does not decide a task.
- **Blinding:** the executor prompt for a run names the mode only in the
  TDD protocol block it receives. The reviewer that produces review findings
  never sees the mode.

## Metrics

| Metric | Source | Direction |
| --- | --- | --- |
| `mutation_score` | The MUTATION slot's report for the task diff, 0 to 100. Missing when the slot is unconfigured for the language. | higher is better |
| `wall_seconds` | Dispatch to Task Result, from the Phase 7 append record. | lower is better |
| `review_findings` | Count of findings the blinded reviewer posts on the task's diff at any severity. | lower is better |
| `gate_iterations` | Number of phase-group verification runs before the group passed, from the workflow log. 1 means first try. | lower is better |

Each run writes one JSON document per the schema in the scorer's docstring.
The scorer refuses a document that is missing any metric except
`mutation_score`, which may be `null` when the slot is unconfigured; a null
excludes that task from the mutation comparison only.

## Scoring

For each metric and each pair of modes, the scorer computes the paired
differences over tasks with both results, then reports:

- the median difference and the count of tasks where each mode won;
- an exact two-sided sign test p-value on the wins (binomial, stdlib
  `math.comb`), because the sample is small and the differences are not
  normal;
- the per-task table so a reader can see which task drove the result.

A mode **beats** the shipped `strict` on the roster when both hold:

1. `mutation_score` is not worse: the median difference is at or above
   `-mutation_tolerance` points (default 2) and no task drops below the
   repository floor.
2. At least one of `wall_seconds`, `review_findings`, or `gate_iterations`
   improves with sign-test p at or below `alpha` (default 0.05), and none of
   the other two gets worse at the same alpha.

The scorer prints the verdict per mode and exits 0 on a decision either
way; a roster too small to reach `alpha` on any metric is reported as
`inconclusive`, still exit 0. Exit 1 is reserved for malformed input.

## What lands when the eval decides

- If `strict` holds: nothing changes; the record notes the result.
- If `boundary` wins: the implement-executor gains the classification step
  and two protocol blocks, selected by the orchestrator per task from the
  plan deltas. That is a protocol change and goes through its own spec.
- If `function_first` wins outright: the mutation floor becomes a hard
  per-task gate before any protocol relaxation ships, since the floor is
  what stands in for the failing test.

## Harness scaffolding in this layer

- `tests/speckit-pro/layer3-functional/executor-modes/catalog.json`: the
  frozen roster and the mode definitions, validated by the scorer.
- `tests/speckit-pro/layer3-functional/executor-modes/score-executor-modes.py`:
  stdlib scorer. `--catalog`, `--results <dir>`, `--report <file>`,
  `--alpha`, `--mutation-tolerance`. Classifies boundary tasks from the
  catalog's deltas, pairs results, computes the tables and verdicts.
- `tests/speckit-pro/unit/test-executor-mode-scorer.py`: locks the
  classifier, the pairing, the sign test, and the verdict rule against
  fixtures under `tests/speckit-pro/unit/fixtures/executor-modes/`.

Not in this layer: running the three executors. The live run is an
operator-only Layer 3 pass that writes the result documents; it needs a
model, a mutation tool, and a blinded reviewer, and none of those belong in
the deterministic suite.
