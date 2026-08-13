# ART-014 Retrospective

## Outcome

The autopilot phase guard's workflow-identity check now enforces the authority
its own documentation had promised since before ART-006 found the defect. A state
naming a different specification exits `1` under `--rule status-evidence`, where
the identical run exited `0` before. Every problem key the guard emits carries a
recorded verdict, and a future key cannot be added without one.

Shipped in PR #433. Suite `7393/7393` from a `7378` baseline, zero failures. All
27 tasks complete, 32 normative items traced (24 functional requirements, 8
success criteria, no NFRs), zero clarification markers after Clarify.

The defect was two independent short-circuits, and either alone kept the check
inert: the comparison never ran under the invocation the autopilot issues, and its
errors were reported under a key the selected rule does not consult. The run
recorded the intermediate stage rather than reasoning about it — after the key was
merged but before it was registered, the mismatch was **fully reported and the run
still exited 0**. That is the row a reviewer who reverts one half returns to, and
it is the clearest single statement of why both halves were required.

## Spec Adherence, Measured

| Measure | Value |
|---|---|
| Task completion | 27 of 27, 100% |
| Total normative items | 32 (FR 24, NFR 0, SC 8) |
| Implemented | 32 |
| Partial / Not implemented / Modified | 0 / 0 / 0 |
| **Spec adherence** | **100%** |
| Unspecified implementations | 1 (see below) |
| Constitution violations | None |

Every functional requirement carries at least two task references in `tasks.md`;
none is orphaned. All eight success criteria have recorded evidence: SC-001 the
flipped canary, SC-002 the 54-of-54 corpus run in both directions, SC-003 the
message carrying both paths, SC-004 and SC-006 the re-derived key counts, SC-005
the completeness bite proof, SC-007 the thirty-hit documentation read-through,
SC-008 the full gate.

The gate was re-run during this retrospective rather than quoted from the run's
record: `7393/7393`, exit 0, zero failures, L1 `1447`, L4 `5760`, L5 `186`. The
entire `+15` over the `7378` baseline lands in one file —
`test-autopilot-bookkeeping-guard` moves from `17/17` to `32/32` — so the delta is
attributable rather than diffuse. No drift to report.

Four further claims were re-derived here rather than read from the run's own record:
`PROBLEM_KEY_INTENT` holds 21 entries split 9 `gated` / 9 `advisory-deliberate` /
3 `advisory-accidental`; `RULE_PROBLEM_KEYS["status-evidence"]` carries four keys
including `workflow_authority_errors`; and neither changed Python file adds a
single import, which is constitution principle II satisfied by inspection rather
than by assertion. Layer 4 coverage is declared at
`tests/speckit-pro/suite-manifest.json:130`.

### The one deviation, and it is an addition

Post-implementation review added two controls the specification does not name:
FR-005's malformed branch and FR-004c's out-of-boundary branch, plus a second
direction to the completeness test. FR-012 declares only the negative/positive
pair sharing one fixture builder, plus the absent-field method. Its verb is
`MUST include`, so nothing is violated — but the shipped test set is now wider
than the text that describes it.

Two spec claims were also overstated at Implement and corrected in `3c58f0ef`
before this retrospective ran: FR-006b said root resolution is shared with two
other call sites when there are three, and asserted safety for every existing
caller without bounding the claim.

## What Worked

### The canary, not the corpus

Fifty-four passing corpus files were never the evidence. A skipped comparison and
a satisfied comparison both exit `0`, so the 54 could only ever prove that nothing
broke. The run's evidence of record is the one file whose verdict had to change:
the canary that exited `0` before and `1` after, and whose `workflow_authority_errors`
key went from **absent** to non-empty. Absence-to-message is the flip that shows
the repair took.

This discipline generalized twice inside the same run. The corpus harness had to
write its state *inside* the repository or the root would not resolve and all 54
would pass vacuously. The negative-control fixture had to write a `.git` marker or
both controls would pass and the negative one would prove nothing. Both hazards
were found before the evidence was collected, not after.

### Every phase re-examined an earlier one, and each pass found something

The findings below exist only because a later phase went back over an earlier
one's work. They are listed with the phase that found each.

- **Clarify S2 — the corpus proof would have been vacuous.** The repository root
  derives from the *state* path, not the workflow path. A harness writing its
  state to a scratch directory outside the tree resolves no root, the comparison
  skips, and 54 files report success while nothing runs. This forced the canary.
- **Clarify S2 — the negative control would have passed for the wrong reason.**
  Same cause, different fixture: a `tempfile` root with no repository marker.
  Produced FR-012's `.git`-marker-as-a-file requirement, which arms the check and
  exercises the worktree case at once.
- **Clarify S2 — whitespace slips past the malformed branch.** Verified by direct
  call: `_is_normalized_repo_path("  ")` returns `True`, because a run of spaces
  is a valid POSIX path part. Without an explicit check the value clears the
  malformed branch and lands in the mismatch branch, printing a blank path — the
  right exit code for the wrong reason, with an unreadable message.
- **Plan — `.get("workflow_file") is None` would have reintroduced the bug.** It
  collapses absent (skip) and explicit `null` (malformed, fail) into one value, so
  a nulled field becomes a silent opt-out. Only the membership test distinguishes
  them.
- **Plan — the return-shape seam.** Re-keying the whole function's return is the
  small diff and is wrong twice: it moves the gated comparison's reporting key,
  which FR-002 forbids, and it arms every gated-path error under `status-evidence`
  for the Codex flow, which is exactly the blast radius FR-008 exists to prevent.
- **error-handling checklist — the guard will carry two identity messages.**
  `test-autopilot-phase-coverage.py` asserts the bare sentence against a *list*,
  making it an exact element match, so appending paths to the gated message would
  have broken a committed test. Found by re-reading Plan's FR-009 against the
  existing suite rather than against the spec.
- **error-handling checklist — Plan's own fixture story was wrong.** Plan argued
  existing fixtures stay green because no repository marker resolves above a
  system temporary directory. True for one file, false for
  `test-autopilot-phase-coverage.py`, which runs `git init`. It stays green for a
  better reason, and that file owns the only committed coverage of the FR-002
  gated paths, so identifying it mattered.
- **data-integrity checklist — a claim this run had already asserted was false.**
  The spec said both tracked state slots must remain valid; the legacy
  `.specify/autopilot-state.json` exits `2` today on a missing plan array, and did
  before this change. Replaced with the narrower true claim.
- **Tasks — the plan declared five authored files and FR-013c needs a sixth.** A
  scope gap in the plan, surfaced by decomposing it into tasks.
- **Implement, T022 — the Step 0.6d false statement.** `SKILL.md` asserted the
  identity check "is inert under every invocation the phase loop issues", which
  this change makes false. The record is explicit that Clarify missed it: FR-013a's
  inventory was scoped to the authority block, while T022 enumerated by search. The
  clearest instance in the run of a later phase catching an earlier phase's
  *scoping* rather than its content.
- **Post-implementation review — two requirements shipped enforcement no test
  exercised.** FR-005's malformed branch and FR-004c's out-of-boundary branch were
  both reachable and both returned a distinct operator-facing string with zero
  coverage; the completeness test checked only one direction. Became `3c58f0ef`,
  which took the gate from 7385 to 7393.
- **Post-implementation diff gate — the 337-versus-687 overrun.** Only a phase
  that measures the real diff could find it. Every forward estimate agreed with
  itself.

The strongest single item is none of these. **Specify's own gate reported a false
pass and the run declined to accept it.** G1 returned `pass: true, markers: 0`
against a spec carrying two. Phase 2 is conditional on G1 detecting markers, so
taking the gate at its word would have skipped Clarify entirely — and every
Clarify finding above with it. The run's most valuable phase was the one an
automated gate said was unnecessary.

### Verifying by execution rather than by reading

Every branch of the five-branch truth table was walked one input at a time and
recorded, including the two rows that could have passed for the wrong reason. The
whitespace row's verdict was attributed to the explicit check *preceding* the
normalization check, not to the normalization check catching it. The `null` row's
verdict was attributed to key membership rather than `.get`. Both attributions
were established by running the alternative, not by reading the branch order.

## What Needed Correction

### The estimator missed by roughly double, and it is not ART-015's defect

Declared 337 projected reviewable LOC. The real authored diff at the measured
commit was 687 added across six files, 2.04x the projection; at HEAD, after the
review remediation, it is 773 added and 31 removed, 2.29x. Every framing — six
files or five, added-only or added-plus-removed — lands over 337 and over the warn
threshold of 400, and every framing stays under block 800.

**ART-015 does not cover this, and says so in its own text.** Its Problem states:

> `estimate-spec-size` computes `user_stories*25 + files*40 + frs*15`, halved when
> `new_vs_modify` is `modify` […]. It is accurate when fed current signals and it
> is only ever fed *scoping-time* signals.

That defect is input staleness, and this run did not have it. The estimator was
re-invoked at every amendment: 195 at the first grill-me pass, 235 once Q8 and Q11
added authored files, 317 at the security consensus once Clarify and the checklists
had grown the requirement set from 13 to 24, and finally 337 once Tasks found the
sixth authored file FR-013c needs — `(3x25 + 6x40 + 24x15) / 2 = 337.5`. ART-015's
fix, applied faithfully and ahead of its own schedule, produces exactly the number
that was wrong by a factor of two. That rules ART-015 out empirically rather than
by argument.

The miss is the *second* limitation, which ART-015 names and then defers:

> **Out of Scope** […] Teaching the model about per-file size. A single 992-line
> table-driven fixture file was half of ART-006's human-reviewable diff, and a flat
> per-file term cannot express that. It is a real limit of signal-based estimation,
> recorded in `ART-006-retrospective.md` and deliberately not addressed here.

ART-014 is the second worked example. Two MODIFIED files priced at roughly 20
effective LOC each delivered, between them, the `PROBLEM_KEY_INTENT` map — a
208-line literal, 225 lines with the header comment that explains its vocabulary,
which is the figure the run's own record uses — and 328 lines of new test classes.

This run sharpens the statement of that limitation, which is the durable part.
ART-006's instance was incidental — a fixture table that happened to be large.
ART-014's was **required by a named requirement**: FR-010 asks for a classification
record covering every emitted key, so its size is a function of the key count (21),
not of the file count (1). A signal set carrying requirement *count* but not
requirement *shape* cannot see that. The gap is therefore narrower and more
tractable than "teach the model per-file size": it is a requirement whose
deliverable is bulk inside an existing file. Recorded against ART-015's deferral
rather than as a new entry, because ART-015 already owns the limitation and only
its worked examples are new.

### Four governance checks report clean or blind, three of them the same class

This run found four checks that cannot fail, three of which are the same defect
class ART-014 exists to repair. Each was overridden by hand and none was filed.

1. **`validate-gate` counts `[NEEDS CLARIFICATION]`**, with the closing bracket
   immediately after the word. The preset spec template prescribes the colon form
   and demonstrates it twice in its own example requirements. Measured against this
   spec: the gate's pattern matched 0, the template's form matched 2.
2. **`count-markers` counts a literal `[Gap]`.** The combined forms `[Gap, Spec §A]`
   and `[Coverage, Gap]` — the second demonstrated by the checklist skill's own
   examples — both count as zero, so the documentation teaches the invisible form.
   An executor hit this live: its first count returned `total: 0` against seven real
   gaps.
3. **`estimate-reviewable-loc` scores every Python file in this repository as
   non-production.** `is_production_file` prefix-matches `src/`, `app/`, `lib/`,
   `scripts/` plus JS, TS and SQL extensions. This repository's guard lives under
   `speckit-pro/skills/speckit-autopilot/scripts/`, which does not *start* with
   `scripts/`, and `.py` is absent from the extension list. The plan-phase budget
   gate is structurally blind to the repository's primary language, and returned
   `projected: 0, production: 0` against five declared files.
4. **Three accidentally-advisory state keys**, already filed as ART-017 and left
   where they are: they live inside the guard rather than in the gate helpers, and
   ART-014 armed exactly one key by design.

**Assessment: one entry, three items — not three entries.** Items 1 and 2 are the
same defect verbatim, a counter whose pattern is narrower than the form the
authoring template or skill itself teaches. They share a fix (widen the pattern to
the taught forms) and a test (feed the template's and the skill's own example
strings as fixtures). Splitting them would put two identical patches in two pull
requests. Item 3 has a different mechanism — a classifier, not a counter — and a
different consumer, and on mechanism alone it would stand apart.

Mechanism is the wrong discriminator here. What decides whether the three ship
together is the verification each one lacks, and it is identical in all three:
**none has a negative control.** Each reports a clean or empty result, and nothing
anywhere proves it can produce a dirty one.

**Strongest single framing: a check that reports zero must be able to prove it can
detect one.** That is this run's own lesson, established before any of the three
were found. Fifty-four corpus passes proved nothing until a canary separated a
satisfied comparison from a skipped one. All three helpers sit in exactly the
corpus's position — a green number with no canary behind it — and ART-014 is that
thesis applied to one guard. The entry applies it to the gate helpers that judge
the guard's own workflow. It also writes the verification section by itself: items
1 and 2 need a canary built from the template's and the skill's own example
markers; item 3 needs a canary asserting that this repository's primary language
scores as production.

One caveat, because the run's own rule pointed the other way. All three were left
unfiled on the rule "nothing shipped cites them", which is correct for the deferred
documentation pin and wrong here. ART-015 was itself opened from ART-006's
retrospective with no in-tree referent, so a retrospective is this project's
sanctioned vehicle for exactly this. And unlike the documentation pin, these three
are live false negatives in the gate path every spec runs through: this run had to
override two of them by hand to avoid dropping real findings.

### Three agent-collaboration failures, each reproducible

**An executor left a probe artifact in shipped source and terminated before
removing it.** It was caught only because the test that executor had just written
detected it, which is ordering luck rather than a control.

> **Practice: a probe never edits shipped source.** Exercise the behavior by
> importing the module and injecting into the test process. T015 did exactly this
> after the incident — run "as a probe against the module rather than by editing
> shipped source, so the guard carries no residue." Because the practice cannot be
> enforced on an agent that terminates, it needs a backstop the orchestrator owns:
> `git diff --stat` against the phase's Declared File Operations before every
> commit, with any path outside that set a stop.

**A stopped agent's byte-exact restore silently undid an orchestrator fix.**

> **Practice: treat an agent stop as a write-invalidation event, not a pause.** Any
> file a stopped agent held is of unknown vintage, and a restore from its in-memory
> copy is a write from a stale snapshot carrying a fresh timestamp. That is the one
> regression class no test suite flags, because it produces a file that was correct
> five minutes ago. A stopping agent never restores; the orchestrator re-derives
> the correct state from the diff and from its own record of what it changed. Then
> diff every file that agent owned before building on any of them.

**Reading a file while an executor was flushing produced a torn read that looked
like a reversion.**

> **Practice: single-writer discipline with a read barrier.** One writer per file
> at a time, and the orchestrator reads an executor's files only after that
> executor's completion signal, never while it is live. When a read does look like
> a reversion, re-read before acting: a torn read and a real reversion are
> indistinguishable from one sample and trivially distinguishable from two. The
> second read costs nothing; acting on the first writes an unnecessary "fix" over
> correct content, converting a transient artifact into a durable one.

The three share a shape worth naming once. **Each was a write whose provenance the
orchestrator could not see** — an undeclared probe write, a restore write from a
stale copy, and a partial write read as a whole one. One cheap control sees all
three: the diff against the declared file operations.

### Executors under-reported, again

Two of the three noted executor incidents are the same pattern ART-006 recorded:
the `clarify-executor` signalled idle twice without returning its question set, and
the US2 executor stopped mid-verification after T013 and T014. In both cases the
orchestrator re-derived the work in the main session and nothing was assumed from an
incomplete report, which is the right recovery. It is also verification the
orchestrator was not supposed to be carrying alone, and it is now the second
consecutive run in which it did.

## Follow-Up Boundaries

- **Recommended, not created: one roadmap entry for gate-helper negative
  controls**, carrying `validate-gate`'s marker pattern, `count-markers`'s marker
  pattern, and `estimate-reviewable-loc`'s production classifier as three items
  under the framing above. No entry was created; this is a recommendation only.
- **ART-015 gains a second worked example, not a scope change.** The formula's
  inability to price a requirement whose deliverable is bulk inside an existing
  file is already in its Out of Scope. ART-014 is the second instance and sharpens
  the statement from "per-file size" to "requirement shape".
- **ART-016 and ART-017 stand as filed.** ART-016 owns the Claude-side live PR OID
  fetch and is cited by the shipped caveat; ART-017 owns the three
  `advisory-accidental` keys and is cited by their verdict strings.
- **FR-006b's safety claim for the three pre-existing `_repository_root` callers
  remains untested.** Those callers now resolve a root for inputs that previously
  resolved none, so they evaluate where they used to skip. This cannot move the exit
  code under the autopilot's scoped invocation and can under an unscoped one.
  Already in the pull request's known gaps.
- **Known gaps carried deliberately**, all in the pull request: the authority
  sentence is unpinned by any test (consensus NO-ASSERT, with a real 1,070-to-500
  line trim on record as the risk); `--rule` selection still bypasses the newly
  armed key (accepted, and 12 of 20 pre-existing keys already carried it); the UAT
  skeleton was skipped fail-open, with `quickstart.md`'s seven scenarios as the
  acceptance basis.
- **The corpus regression and the flipped canary are a one-time recorded run**, by
  design, so nothing in CI re-proves them. That was Q10's answer at scoping and it
  remains correct — a committed corpus walk would turn CI red on unrelated pull
  requests whenever another spec is mid-repair — but it means the strongest single
  piece of evidence for this change lives in a document rather than in the suite.

### Proposed spec change, not applied

One was identified and it was declined for want of approval. **FR-012's declared
control set is narrower than what ships.** FR-012 names the negative/positive pair
sharing one fixture builder, plus the absent-field method; `3c58f0ef` added a
branch-3 (malformed value) control, a branch-4 (out-of-boundary) control, and a
second direction to the FR-011 completeness test. The edit would extend FR-012's
enumeration to name all three, and state that each asserts *attribution* rather
than only the exit code — a whitespace-only value reported as an identity mismatch
must fail the test instead of passing by accident. FR-012's verb is `MUST include`,
so the shipped suite does not violate it and nothing here is blocking.

`spec.md` was **not** modified. This retrospective carried no approval to change
it, and no other spec edit was identified.
