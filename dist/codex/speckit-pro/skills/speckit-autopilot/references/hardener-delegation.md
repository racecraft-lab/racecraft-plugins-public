# Hardener Delegation

The hardener is a bounded test-writing loop that runs once per spec, after
the MUTATION slot has run on the whole diff and before its result is allowed
to block. It kills surviving mutants by adding or strengthening tests; it
never edits source. The loop is delegated to the local Qwen worker when the
delegation gateway is healthy and runs on the primary model otherwise. Both
paths follow the same inputs, allowed writes, stop rule, and record.

## When it fires

Exactly once per spec, and only when all of these hold:

- `MUTATION` is `populated` in the Quality Gates table (not `unconfigured`,
  `skipped`, or `N/A`).
- The MUTATION run in Step 4 of Phase 7 produced a report.
- The Quality Gates table's `Hardener` line is still `not run`. A resumed run
  that finds any other value does not fire again; it reads the recorded
  outcome and continues.

The floor comes from `.specify/quality-gates.json`
(`thresholds.mutation_score_floor`). The hardener runs even when the first
score already clears the floor only if the operator asked for it in the
workflow file; by default a passing score records `not needed` and skips.

## Inputs, always the same three

1. **Mutation report**: the tool's output from the Step 4 run (cosmic-ray's
   `cr-report`/`cr-rate` text or StrykerJS's `reports/mutation/mutation.json`),
   pasted into the task, not referenced by path, so the worker never has to
   discover it.
2. **Changed files**: `git diff --name-only origin/main...HEAD`, source and
   tests, listed in full.
3. **Thresholds**: the floor, the current score, and the iteration cap.

## Allowed writes: tests only

`allowedPaths` is the list of existing test files that cover the changed
source files plus one new test file per changed source file under the
repository's test tree, named by its convention. Nothing under a source
directory is ever listed. A candidate that touches any other path is rejected
without apply; that is a scope violation, not something to fix by widening
the list.

## Stop rule

The loop ends when the re-run mutation score reaches the floor, or after the
iteration cap, three by default, whichever comes first. Each iteration is one
delegation with the report from the previous re-run. A cap exit is not a
failure of the hardener; it hands the still-failing MUTATION result back to
Step 4, which then blocks as it would have.

## Delegated path (Qwen)

Preconditions, checked in this order and recorded:

1. The `qwen_health`, `qwen_delegate`, `qwen_status`, `qwen_candidate`, and
   `qwen_apply` tools are present in this session (capability discovery).
2. `qwen_health` reports the sandbox boundary, default-deny policy, and the
   accepted Qwen profile as healthy. Any other result selects the fallback.
3. The live checkout is clean apart from the workflow and state files, so
   `qwen_apply` cannot fail on source drift.

Delegation request, one per iteration:

```text
qwen_delegate
  mode: "write"
  strategy: "direct"
  webPolicy: "disabled"
  sourceVisibility: "private"
  thinkingEffort: "medium"
  maxMinutes: 20
  repositoryRoot: <absolute path of the worktree>
  allowedPaths: <test files only, see above>
  validationCommands: [<UNIT_TEST>, <MUTATION with {paths} filled>]
  acceptanceCriteria:
    - "Mutation score for the changed files is at least <floor> percent"
    - "UNIT_TEST exits zero"
    - "No file outside allowedPaths is changed"
    - "Every new test asserts observable behavior a surviving mutant breaks; no test asserts implementation details or snapshots the mutant"
  task: |
    Harden the tests for the files below so surviving mutants are killed.
    Iteration <n> of <cap>. Current mutation score <score>%, floor <floor>%.

    Changed files:
    <list>

    Mutation report:
    <pasted report>

    Rules: edit only the listed test files; never change source; prefer one
    focused test per surviving mutant, named for the behavior it pins; keep
    existing tests passing; do not weaken or delete assertions.
```

Then:

1. Poll `qwen_status` until the state is terminal and `cleanupCompletedAt`
   is set. A paused task gets at most one `qwen_reply` with `approveOnce:
   true`; a second pause is a cancel and a fallback.
2. `qwen_candidate` with the returned candidate id. Inspect the patch before
   any apply decision: every changed path is in `allowedPaths`; no source
   path; no deleted or weakened assertion; the validation digests match the
   commands sent. Reject anything else, record why, and either delegate again
   with the objection in the task or fall back.
3. `qwen_apply` with the candidate id and the one-time review nonce.
4. Re-run `UNIT_TEST`, then `MUTATION` with the same `{paths}`. Record the
   new score. Apply the stop rule.

The delegation never runs with `webPolicy: "public-read"` for this loop; the
inputs contain repository source and the mutation report.

## Fallback path (primary model)

When any precondition fails, the orchestrator runs the same loop itself by
dispatching the implement-executor once per iteration with the same three
inputs, the same test-only write rule stated in the prompt, and the same
acceptance criteria; the executor's TDD protocol already forbids weakening
tests. Inspect the diff before the re-run exactly as the candidate is
inspected: any source change is reverted and counted as a failed iteration.

## Record

The Quality Gates table's `Hardener` line carries one of:

- `not run` (initial), `not needed (score N ≥ floor F)`,
- `qwen: iteration k of cap: N → M`, one entry per iteration, ending with
  `floor reached` or `cap reached`,
- `fallback (reason): iteration k of cap: N → M`, same endings,
- `rejected candidate: <reason>` when a candidate was refused.

Each applied iteration is committed on its own with the message
`test: harden <changed module> against surviving mutants (hardener k/cap)`, so
a reviewer can see exactly which tests the hardener added.
