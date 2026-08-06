# ART-006 Retrospective

## Outcome

Autopilot gained first-class stages — `plan`, `implement`, `full` — on both
distributions. A planning run now stops at a committed boundary; a later run, in
a new session or a different working copy, resumes into implementation; a bare
invocation resolves its own stage and says which it picked and why.

Shipped in PR #422. Suite `7226/7226` from a `7052` baseline. Codex body `7795`
of its `8000`-word cap. All 43 tasks complete, 33 normative items traced, zero
clarification markers.

The feature exists to prevent one failure: resolving the wrong stage silently.
Three independent routes to that failure were found and closed, and only one of
them was visible when the specification was written.

## What Worked

**The checklist phase paid for itself twice over.** Twenty defects were raised
across three domains and all twenty were remediated. Two would have broken the
implementation outright: a rejection step sited in a reference document that has
no opening-preparation section, so it would have run *after* phase work began;
and an exit-code table that folded a request-layer diagnostic into exit 2, which
would have taught the golden fixtures to assert a code the runner never emits.
Neither is the kind of thing a test catches — both would have been implemented
faithfully and been wrong.

**Verifying by execution rather than by reading.** The central claim of this
specification is that the new mirror check is not inert. That was proven by
running the guard against a mismatched state file and observing exit `1`, not by
reading the registration and believing it. The same habit caught that
`compose-release-notes.py --validate-pr` does not validate PR titles at all — a
negative control with an uppercase scope passed it — so title validation needed a
different gate entirely.

**Keeping the tree green between phases.** Regenerating artifacts after each
phase rather than only at the end meant every failure was attributable to the
phase that caused it. The alternative — accumulating eight failures behind stale
payloads and untangling them at the end — was the situation this run started in
and deliberately left.

## What Needed Correction

**The size estimator was blamed wrongly; the inputs were stale.** The first
reading of this was "the estimator underestimates" — three misses, all in the same
direction. Re-running it settles that differently.

`estimate-spec-size` computes `stories×25 + files×40 + frs×15`, halved for a
modify-weighted spec. At scaffold it was fed 3 stories, 12 files, 14 FRs and
returned **382, one slice**. Fed the spec's *final* signals — 3 stories, 17 files,
25 FRs — the same operation returns **565 with `status: warn`**. The requirement
count grew from 14 to 25 during clarification and the checklists, and nothing ever
re-fed it. The file signal, by contrast, was declared as 17 and came in at exactly
17.

So the model is not the problem and the inputs are. There is no re-estimation
trigger: the estimator runs at scoping time, and the G3 "re-estimate" was a
hand-authored figure in `plan.md` rather than a re-invocation with refreshed
signals.

The residual gap is a separate matter and is not an input problem. Actual
human-reviewable is 1999 lines, of which **992 are a single table-driven fixture
file** — half the diff in one file. A model whose file term is a flat 40 points
cannot express "one of these files is a 992-line fixture table." That is a real
limitation, but it is a limitation of what the signals *can* say, not of the
arithmetic.

**Two word-cap misses had a different owner entirely.** The Codex projection
assumed two capped-body edits when the contract checklist had established a third,
and then the three edits cost 124 words against a 54-word budget. Neither number
came from a tool — both were hand-authored prose in `plan.md` and `research.md`,
propagated into four documents promising downstream specs 275 words of headroom
that did not exist. The real figure is 205. Lumping these with the estimator
obscured that the fix is different: a measured value should never be restated by
hand in a second document.

**A published number was wrong and had to be corrected.** The first reviewability
measurement reported 29 files and claimed the result exceeded *both* block
thresholds. Twelve `installed-cache-proof*.json` fixtures had been counted as
authored tests when they are regenerated artifacts. The corrected count is 17
files — **warn, not block** — and matches the declaration exactly. The error was
caught only when the estimator question forced a recount, which is an argument for
recounting before publishing rather than after.

**"Inert as a gate" turned out to be systemic, not local.** The specification was
written around one inert check. Investigating it at the user's request revealed
that 11 of the guard's 19 problem keys cannot move the exit code under the rule
the autopilot actually invokes. Most of that is deliberate and documented. The
identity check is the anomaly because its documentation promises enforcement.
Scoping the fix required understanding the difference, which is why it became
ART-014 rather than a two-line patch.

**Phase executors reported nothing.** Every executor completed its work and went
idle without emitting a summary, so each phase had to be verified from the
artifacts and the diff instead of from a report. That worked — arguably better
than trusting a self-report — but it meant the orchestrator carried verification
that was supposed to be shared. Two executors also touched `dist/` after being
told not to; harmless because regeneration is authoritative, but it shows a
prompt-level instruction did not hold.

**A checklist artifact understated its own coverage.** The first domain left 33
of 39 items unchecked with no recorded verdict, which reads to a reviewer as
"not verified." The convention was fixed for the two remaining domains by
mandating a verdict tag on every item, and the first was repaired by spot-checking
eight of the 33 by hand and recording exactly which rested on the executor's
evaluation rather than an independent re-read.

## Follow-Up Boundaries

- **ART-014 — Phase-Guard Enforcement Repair.** Un-short-circuit the identity
  comparison, register it under a key the scoped rule consults, and audit which
  of the remaining advisory keys are advisory on purpose. Assess the blast radius
  first: registering `workflow_checkpoint_errors` wholesale would arm its sibling
  checks against a corpus that has never had to satisfy them.
- **Re-estimation trigger.** The estimator is accurate when fed current signals
  and is never re-fed. The cheap fix is to re-invoke `estimate-spec-size` at G3
  and G5 with the spec's actual requirement and file counts, and to record the
  operation's output rather than a hand-authored figure. Worth a roadmap item.
- **Stop hand-copying measured values.** The word-cap headroom was measured once
  and then restated by hand in four documents, three of which went stale. Any
  measured number should have one home and be referenced, not copied.
- **Draft-PR corroboration and scaffold-side chain implementation** remain with
  the downstream ART specifications, which is what kept this one slice.
- **A harness stop hook** stays out of scope, recorded with the re-entry and
  fail-open obligations it would carry if it were ever added.
