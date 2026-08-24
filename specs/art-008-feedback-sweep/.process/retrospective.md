# Retrospective: ART-008 Feedback Sweep (slice 1 of 2)

111 shipped tasks plus 2 added during implementation. Full gate 14011/14011.
PR #464, ready for review.

## What the process caught that a single pass would not have

**Four tasks had a code half and a documentation half where only the code half
was tracked.** T051 and T086 were marked complete on their code and caught as
phantom completions; T106 and T089 turned out roughly two thirds pre-documented.
The orchestrator caused the first two by telling a code worker "the documentation
half is NOT yours" and then marking the whole task done. A later worker found it
by checking rather than trusting the checkbox.

**Two registration touch points existed that no task owned.** `HELPER_CASES`,
without which every added helper raises `KeyError`, and the Codex fallback roster
fixture, which any new agent TOML restales. Two workers found the first
independently. Both became tasks rather than silent fixes.

**Three tautological assertions were caught by their own authors.** Tests that
compared an expectation to itself, rewritten to read live output. Two remained
vacuously green and were declared as such rather than counted as coverage.

**An independent code review found three blocking defects after the feature was
green**, two of them security-relevant, both in surfaces with zero test coverage.
A green suite was not evidence those paths worked; it was evidence nothing
exercised them.

## The most instructive failure

**The suite count was wrong for the entire run.** The parse test emitted no house
summary, so the runner counted zero units from it. This feature's 6028 units were
absent from the number whose whole job is to prove the feature was tested. G7's
increase from 7659 to 7983 came entirely from other layers.

It hid because the number kept moving for other reasons: merged `main` alone took
the live count from 7659 to 7912. The tell only appeared when six new regression
tests failed to move the total at all.

Failures were never at risk, since a nonzero exit fails regardless of the summary.
The measurement was. This is the same defect class the checklist caught three
times inside the spec, except the thing it fooled was the gate.

## What to change next time

1. **A task with two halves needs two checkboxes.** Four instances in one
   `tasks.md` is a pattern, not bad luck.
2. **Verify a new test file contributes to the suite count**, not just that it
   passes. `PASS (no summary)` reads like success and measures nothing.
3. **Keep worker batches under about ten tasks.** Three workers hit the tool-use
   ceiling mid-verification and lost their reports; the work survived, the
   evidence did not.
4. **Dispatch as plain async subagents, never named teammates.** Named teammates
   route their report to their own pane and strand it, and must be reaped by hand.
5. **Compare parity whitespace-normalized.** Six workers, and the orchestrator,
   hit false gaps from line-based greps where a phrase wrapped.
6. **Regenerate last.** The zero-bash guard caught prose that only existed after
   the documentation waves landed.

## Carried forward

- **T098's binding probe is unrun**, and cannot run from a branch: plugin agents
  load from the versioned cache, not worktree source. Discharge after release and
  cache refresh.
- **T111 will restale again** on the next Codex agent definition. That is the
  fail-closed control working.
- The `materialized_workflow` path still has the concurrent-run hazard that made
  one worker's fixture flaky.
