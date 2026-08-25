# Retrospective: ART-008 slice 2 — Artifact Freshness

Written at the close of the implement stage, before human review of PR #502.

## What shipped

One read-only runner helper with three named surfaces, 51 Layer 4 fixture
cases, and the reference prose on both platform surfaces that turns the helper's
verdict into a regeneration sequence. Slice 1's promise that draft pages would
regenerate "once slice 2 lands" is gone from both surfaces, because they now do.

Full suite 14179/14179, exit 0. G7 satisfied at +167 over the recorded baseline.

## What worked

**Fixtures before implementation, enforced by a measured red list.** Every one
of the 51 cases was red before the code that satisfies it existed, and each red
list was recorded rather than asserted: 29 red at T025, 11 at T032, 9 at T036.
When two cases were added later without a red phase, their non-vacuity was
proven by mutation instead of assumed.

**Splitting each phase into fixtures-then-implementation.** Two separate
dispatches per surface kept each worker's context small. The one dispatch that
died of context exhaustion in the plan stage had no equivalent here.

**Verifying claims instead of accepting reports.** Three findings came from
re-running the check rather than reading the summary: the executable-surface
audit, the pure-insertion check on every prose phase, and the fixture audit
before committing the verdict surface. Every executor reported honestly, but the
checks were cheap and the failure mode they guard against is silent.

## What was harder than expected

**Executors went idle without reporting, four times out of eight.** The work was
complete and correct on disk each time; only the summary was missing. Verifying
from the orchestrator and asking for the report afterwards cost little, but a
run that trusted the absence of a report would have stalled.

**The planning artifacts disagreed with each other in three places**, and none
was caught by Analyze:

1. `plan.md`'s step-5 commit gate still carried the pre-consensus wording,
   which would have permitted a removal-only commit and stranded pages
   permanently. Corrected, with a revision note.
2. `data-model.md` had no home for the `unusable_observation` reason, no
   condition for `missing_commit_cell`, and an echo rule that contradicted its
   own "read at all" rule. Reconciled after the fixtures settled all three.
3. `plan.md`'s declared generated surface names the Codex reference's
   installed-cache path under `codex-skills/`; the real path is under
   `skills/`. Recorded rather than corrected.

**Two quickstart scenarios were not executable as written**, and validating them
is what surfaced it. One could not flip the verdict it claimed to flip, because
the file it named carries no log rows to join against. The other asserted a word
count that had moved.

## What to reuse

**Pin the contract, not just the task.** Each implementation dispatch carried
the judgment calls the previous dispatch had settled, stated as binding. That is
what kept three separate workers from each inventing a different envelope shape.

**Name the ordering hazards in the prompt.** Both hazards this slice turns on —
a short row's `cells[-2]` being the literal `amended` token, and the escaped-pipe
row splitting into nine cells — were measured by the fixture author and handed
to the implementer as constraints. Neither was discovered by a failing test,
which is the point.

**Ask what a check would prove before running it.** The two added fixture cases
passed on their first run, which is exactly the shape of a vacuous test. The
mutation check cost one minute and converted an assumption into evidence.

## The one thing to decide before merge

The realized production diff is **1226 lines against a declared ~730 midpoint
and an 800 block**. The executable surface landed inside its estimate; the
overrun is entirely reference prose on both platforms, and it is density rather
than unplanned scope.

`plan.md` named a split lever that no longer matches where the overrun is: it
deferred the description-refresh half, worth 95–155 lines, while the overrun is
spread across all three user stories' prose. The seam that would actually work
is the platform one — land the Claude surface and the helper, defer the 408-line
Codex mirror — which buys reviewability by opening a window in which the two
platforms disagree. SC-008 exists to prevent exactly that window.

No gate produced a block verdict, so none was recorded. The decision belongs to
the operator at this checkpoint, which is the decision point this spec family
was built to create.
