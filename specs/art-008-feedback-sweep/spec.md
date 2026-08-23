# Feature Specification: Feedback Sweep, slice 1 of 2 — the checkpoint

**Feature Branch**: `art-008-feedback-sweep`

**Created**: 2026-08-20

**Status**: Draft

**Input**: User description: "ART-008 slice 1 of 2, the checkpoint. The plan stage ends at an open draft pull request whose body indexes the planning artifacts, and the gallery's draft-stage pages export a reader's objections as markdown meant to be pasted into a pull-request comment. Nothing reads those comments back, so an implement-stage run starts task work without looking at the pull request and the checkpoint is decoration. Make the implement stage open with a feedback sweep that reads unresolved review threads and pull-request conversation comments, acts only on write-capable authors, recognizes exported markdown blocks by their lead sentence, classifies each comment as amended, answered, deferred, or no action, routes amendments through the existing consensus machinery, records every handled comment in a Feedback Sweep Log in the workflow file, replies once per comment, and then stops for re-review when anything was amended or proceeds into task work when nothing was. Artifact regeneration, stale-page detection, and the draft-description refresh belong to slice 2."

## Clarifications

### Session 1 — Feedback Sweep Log and commit protocol (2026-08-20)

- **Q: One commit per amendment or one per run, and where does the log write
  go?** → One commit per amendment. The Feedback Sweep Log and Consensus
  Resolution Log writes ride a separate bookkeeping commit, one per amendment,
  staging the workflow file alone under a `chore:` subject. A row that names
  its commit cannot exist until that commit's sha does, so the separation is
  forced rather than stylistic. Recorded as FR-012 and FR-012a.
- **Q: Which Consensus Resolution Log type value marks a sweep amendment, and
  how does the escape-rate metric treat it?** → `Sweep`, a fourth value beside
  `Clarify`, `Gap`, and `Finding`. Sweep rows count toward the Round-2
  escape-rate metric rather than being excluded from it. They come from the
  same category-routed protocol and can be mis-routed the same way, and the
  dispositions that would have distorted the metric never reach the log,
  because FR-011 keeps answered, deferred, and no-action items out of
  consensus. Recorded as FR-014.
- **Q: One class per comment, or one item per recognized objection?** → One
  class per comment. FR-015's one-reply-per-comment rule and FR-009's
  comment-id skip key both take the comment as the unit, and splitting a
  comment into several classified items would leave both undefined. When one
  comment's objections diverge, `amended` dominates and the non-dominant
  objections are named in the disposition and the reply. Recorded as FR-010.
- **Q: What is the Feedback Sweep Log's exact shape and placement?** → Header
  `| # | Comment ID | Surface | Author | Class | Disposition | Commit | CRL # |`
  under its own `### Feedback Sweep Log` heading, immediately after
  `### Consensus Resolution Log`. Placement is additive-safe: the phase-coverage
  guard's table reader is heading-anchored, breaks on any line starting with
  `#`, and carries no reference to the Consensus Resolution Log at all.
  Recorded as FR-013.
- **Q: What does a re-run read to skip, and what happens to an amendment whose
  log row never landed?** → The skip key is the log's comment-id column alone.
  An amendment that was pushed before its bookkeeping commit landed is
  re-processed on the next run, because the log is the only record and FR-006
  bars the sweep's own reply from serving as a fallback marker.
  Per-amendment bookkeeping bounds that window to one item. Recorded as
  FR-009, FR-012a, and an edge case.

**Correction carried into this session.** The design concept's rationale for
keeping the sweep record out of the Consensus Resolution Log leaned on an
aggregator script. That script does not exist: it was removed by an earlier
shipped-Bash purge and nothing replaced it. The decision it justified still
holds on its own terms, and the reasoning above is restated without the tool.

**Four sub-items went to consensus and all four resolved in Round 1**, with no
escalation, no human-review flag, and no escape-hatch keyword. Each is recorded
in the workflow file's Consensus Resolution Log.

- **Escape-rate inclusion.** Confirmed: sweep rows count. Two analysts agreed
  from independent directions. The project-decisions view found no record tying
  the 10% threshold to any phase-specific calibration, so the case for
  excluding sweep rows had no basis in this repository's history. The
  external-practice view reached the same place through control-limit design
  and selection bias, and added that a mixed population is answered by
  stratifying rather than excluding. That refinement needs no new field: the
  `Type` column already is the discriminator.
- **Divergent-objection dominance.** Confirmed. The rule turns out not to be
  invented: the roadmap's 2026-07-28 decision fixed that amendments always stop
  for re-review three weeks before the four-class vocabulary existed, and
  FR-003's cross-platform determinism requirement rules out any tie-break that
  is not a fixed explicit rule. Amended-dominance is the only rule satisfying
  both.
- **Log-to-log link.** Confirmed, and made bidirectional. Neither Markdown
  table reader in the codebase is anchored near these two tables, so a new
  table and a new column are invisible to both. Keying the reverse direction on
  the comment id rather than on a row position alone costs nothing and follows
  the idiom the codebase already uses for durable pointers.
- **Interrupt window.** Confirmed: per-amendment cadence, and the window is
  accepted rather than closed. The `Draft PR` repair rule does not port,
  because repair needs a live witness independent of the record and every
  candidate witness here is closed by FR-006, FR-012, or FR-016. Consensus also
  found three defects in this session's own first-pass text, all now fixed:
  FR-012a's rationale over-claimed (the ordering is forced, the cadence is a
  separate choice), the borrowed `Draft PR` write rules silently dropped the
  `repair` rule, and a run with zero amendments but handled comments had no
  commit to carry its rows.

### Session 2 — helper envelope and hidden coupling (2026-08-20)

This session also carried the unknown-unknowns search the scaffold's blind-spot
pass never ran. It changed the spec more than any other pass. The findings that
became requirements are recorded at FR-004a, FR-004b, FR-005, FR-007, FR-007a,
FR-008, FR-008a, FR-013, SC-005, and SC-008; the ones that became assumptions
are in the Assumptions section. Three sub-items went to consensus.

- **Q: Should the registry recognize the "Copy as Prompt" imperative
  variants?** → Yes, with the entry recording its kind, and recognition alone
  never forcing a class. Two of three analysts. The deciding argument inverts
  the intuition: leaving them unregistered is the *worse* posture, because the
  imperative text then reaches the analysts as unlabelled free text and the
  security-keyword routing matches none of that phrasing. Recorded as FR-007c
  and FR-007d.
- **Q: How does the sweep recognize its own reply?** → An anchored HTML-comment
  marker at the start of the body, **and** an author match, both required.
  Unanimous on the marker; the author half is an added filter that costs
  nothing and blocks another account from spoofing it. Matching the author
  alone was rejected because the sweep authenticates as the operator, who is
  the reviewer the checkpoint exists for. A visible sentence was rejected
  because a reviewer quoting a reply to disagree with it would copy that
  sentence and be silently skipped. Recorded as FR-006, FR-006a, FR-015, and
  FR-015a.
- **Q: Does corroboration status `skipped` stop or proceed?** → Stop. Both
  analysts, high confidence, and it turned out to be a vocabulary gap rather
  than an open question: User Story 3 and SC-006 already counted the
  unreachable-tool case as a fourth stop condition, while FR-019 named only
  three by token. The distinction that carries it: `no_record` means the gate
  does not apply, `skipped` means the gate applies and evaluation failed.
  Recorded as FR-019, FR-019a, and FR-019b.

**Dissent worth preserving.** On the prompt variants, the third analyst argued
for neutralizing rather than labelling — excluding a recognized prompt-variant
comment from the automated amend path and routing it to human review — on the
grounds that a tag nothing consumes changes nothing about what reaches the
agent. That objection is answered inside the chosen option rather than
dismissed: FR-007c requires the registered lead to be carried as matched
metadata rather than passed through as free text, which is the substance of
what marking is for. The remaining difference is only whether a recognized
prompt paste should additionally be barred from amending, and the majority
judged that too costly against honest mis-clicks.

**A scope correction the search produced.** The spec had said three templates
export. Ten do, and seven of those export a prompt kind as well. FR-007b widens
the registry to all of them and FR-008a derives the expected set from the
manifest, which makes the count a data question rather than a design one.

### Session 3 — settled-decision verification (2026-08-20)

Verification, not fresh design. **All eight settled interview decisions came
back encoded**, none partial and none missing, each traced to the requirement
carrying it. The spec did not drift from the interview across two sessions of
heavy editing. No sub-item needed consensus.

- **Q: Do exported blocks inside review threads need their own acceptance
  scenario?** → Extend the existing one rather than add a new one. The behavior
  is surface-independent by construction, so a standalone scenario would assert
  nothing FR-007 does not already force. But leaving it entirely to prose was
  wrong: no scenario named a surface for an export, the fixture list named
  shapes and paths but never a surface, and the promise rested on an assumption
  pointing at a runbook that does not exist yet. US1 Scenario 3 now carries the
  review-thread placement, and FR-008a pins a fixture on each surface.

**Fifteen consistency defects, all fixed.** The two that mattered most were
contradictions the spec had grown into:

- **FR-015 required every reply to name an artifact, a section, and a commit,
  across all four classes.** Only `amended` has any of those, so three of the
  four templates it mandates were unsatisfiable. Now scoped.
- **FR-015's "exactly one reply" had no qualifier**, while SC-002 and SC-003
  gained one in session 1 for exactly the same edge case. The requirement and
  the criterion measuring it disagreed. Now aligned.

Six requirements had no criterion or scenario reaching them. Two of those gaps
were serious enough to earn new criteria rather than a note: **FR-004b**, the
no-shell-argument injection boundary, had no verification anywhere despite
being the security boundary of the whole feature and being stated as a
correction to shipped precedent; and **FR-013's** pipe-escaping and
unresolvable-author rules, both found-and-fixed defects, had no test. Those are
now SC-009 and SC-010. FR-019b's four-cause reporting is now covered by SC-006.

One more stale count fell out: three shipped templates declare the identical
empty-export sentence, not two. Two figures were verified correct and left
alone: ten exporting templates with seven carrying a prompt kind, and the
six-value corroboration vocabulary, which matches the shipped classifier's six
returns exactly.

**The budget verdict is the finding to read.** See the Reviewability Budget
section: the slice no longer fits the ~330 it was scoped against, the honest
range at the time was 325 to 485, which Plan later corrected upward to 515 to
745 by re-measuring against the right precedents — and which later passes moved
again; the live figure has one home, that section's superseding note. The Plan
estimator is structurally blind to every one of those figures, because none of
this slice's paths satisfy its production-file test. It will report zero and
pass. Plan sizes this by hand.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The sweep reads and classifies draft-PR feedback (Priority: P1)

The implement stage opens. Before any task work, the orchestrator looks at the
draft pull request the plan stage left behind. It collects every review thread
still marked unresolved and every comment in the pull-request conversation. It
keeps only the comments written by accounts with write access to the
repository, and it sets the rest aside as untrusted rather than acting on them.
Among the kept comments it recognizes the ones that are artifact exports, by
finding one of a fixed set of known sentences among the comment's opening
lines. It ignores anything it already handled on a previous run, and it ignores
its own replies. What is left gets a single label each: amended, answered,
deferred, or no action.

**Why this priority**: Nothing else in the sweep can happen until the feedback
is read, filtered for trust, and sorted. This story alone converts the
checkpoint from decoration into an inventory the operator can see, and it is
the story that carries the security boundary.

**Independent Test**: Point the sweep at a draft pull request carrying a mix of
comments — a trusted plain comment, a trusted exported markdown block, an
untrusted comment, a comment already recorded from a prior run, and a resolved
thread. Confirm the run reports exactly the trusted, unrecorded, unresolved
items as classified candidates and names every excluded comment with its
exclusion reason.

**Acceptance Scenarios**:

1. **Given** a draft pull request with two unresolved review threads and one
   conversation comment, all from write-capable authors, **When** the sweep
   runs, **Then** all three appear as candidates, each carrying its surface and
   exactly one class from the closed set.
2. **Given** a conversation comment from an account with no write access,
   **When** the sweep runs, **Then** that comment is reported as "not swept:
   untrusted author", is not passed to the consensus protocol, and produces no
   artifact edit.
3. **Given** a verbatim export paste, whose registered sentence sits on line
   four behind the artifact header, **When** the sweep runs, **Then** the
   comment is recognized as an artifact export; **Given** the same paste with
   that header trimmed off, **Then** it is still recognized; **Given** the same
   recognized paste posted into a review thread rather than into the
   conversation, **Then** it is recognized identically and its row records the
   review-thread surface; and **Given** a comment carrying no registered
   sentence in its opening lines, **Then** it is treated as an ordinary
   comment.
4. **Given** a comment id that already appears in the Feedback Sweep Log, and a
   reply the sweep itself posted on an earlier run, **When** the sweep runs
   again, **Then** neither becomes a candidate and no duplicate record or reply
   is produced.

---

### User Story 2 - Amendments run through consensus, get recorded, and stop for re-review (Priority: P2)

For every comment the sweep labelled amended, it runs the existing consensus
round structure with its own scoped analyst, applies the agreed edit to the
specification, the plan, or the task list, and commits and pushes that change.
It then writes the durable record: one Feedback Sweep Log row for the comment,
plus a Consensus Resolution Log row for the amendment. It posts one reply on
the comment saying what class it got, which artifact and section moved, and
which commit carries it. Once every item is handled, the run stops and asks the
reviewer to look again. If nothing was amended, the sweep still writes its rows
and posts its replies, then walks straight into task work, unless a redaction
fired on the way out, in which case it stops after those writes and says so.

**Why this priority**: This is the roadmap's "sweep, amend, re-review" decision
made real. It is what makes the checkpoint worth stopping for, and it depends
on Story 1 having produced a trustworthy classified list.

**Independent Test**: Give the sweep one trusted comment that clearly warrants
a plan change and one that does not. Confirm exactly one amendment commit
lands, both comments get a reply and a log row, only the amendment gets a
Consensus Resolution Log row, and the run stops with a re-review report. Re-run
with no new comments and confirm it proceeds into task work instead.

**Acceptance Scenarios**:

1. **Given** one comment classified amended, **When** the sweep processes it,
   **Then** the consensus protocol resolves it, the edit lands in one of the
   three planning artifacts, and the change is committed and pushed.
2. **Given** a completed amendment, **When** the records are written, **Then**
   the Feedback Sweep Log holds a row with the comment id, surface, author,
   class, disposition, and commit, and a linked Consensus Resolution Log row
   exists; no state file outside the workflow file is written.
3. **Given** four handled comments across all four classes, **When** the sweep
   finishes, **Then** each comment carries exactly one reply naming its class,
   **and Given** the one classified `amended`, **Then** its reply additionally
   names the artifact, the section, and the commit, while the other three name
   none of those because none exists; and no review thread has been resolved by
   the sweep.
4. **Given** at least one amendment, **When** the sweep completes, **Then** the
   run stops before task work with a re-review report that names the comments
   swept, the amendments made, the commit range, and states that draft pages
   regenerate once slice 2 lands; **Given** zero amendments and zero redaction
   events, **Then** the run proceeds directly into task execution.

---

### User Story 3 - An unreadable draft pull request stops the stage (Priority: P3)

The workflow file says a draft pull request was opened, but the sweep cannot
read it: the GitHub CLI is unreachable, or the recorded pull request turns out
to be closed, missing, or pointing at something other than this feature. The
run does not guess and does not quietly continue. It stops before any task work
and reports which of those situations it hit and exactly what the operator must
do to resume. The one case that proceeds is the absence of a draft pull request
record at all, because then no checkpoint was ever opened and there is nothing
to sweep.

**Why this priority**: This is the integrity guard. Without it, a flaky tool or
a stale record silently downgrades the checkpoint to optional, which is the
failure this whole feature exists to remove. It is P3 only because the happy
paths must work first.

**Independent Test**: Run the sweep four times, once per unreadable condition,
and confirm each stops before task work with a report naming that condition and
a resume path. Then run it with no draft pull request record and confirm it
proceeds.

**Acceptance Scenarios**:

1. **Given** a Draft PR row is present and the GitHub CLI is unreachable,
   **When** the sweep runs, **Then** the stage stops before any task work with
   a report naming the failure and the resume path.
2. **Given** a Draft PR row is present and corroboration reports the pull
   request closed, missing, or belonging to another feature, **When** the sweep
   runs, **Then** the stage stops with a report naming that status and the
   resume path.
3. **Given** the workflow file carries no Draft PR row, **When** the sweep
   runs, **Then** it proceeds into task work without stopping and without
   reporting an error.

---

### Edge Cases

- An export pasted from a page where nothing was recorded: it carries no lead
  sentence at all, because the builder returns before pushing one, and instead
  carries a different sentence saying nothing was recorded and that the record
  is not an approval. FR-007a registers those sentences so the comment is
  recognized rather than mistaken for reviewer feedback, and it takes the class
  `no action`. Three templates ship the identical sentence, so the template id
  is reported as ambiguous.
- An export pasted with a body large enough to exceed the truncation budget:
  recognition still works, because the registered sentence sits in the opening
  lines, and the record carries the truncation flag so a reader knows the tail
  was not examined.
- A reply the sweep itself posted on an earlier run: the author is
  write-capable and the comment id is new, so the trust filter and the
  already-logged check both pass it. It must still be excluded, or every run
  sweeps the previous run's output.
- A review thread whose author is trusted but whose thread is already resolved:
  skipped, because only unresolved threads are read.
- A comment already recorded in the Feedback Sweep Log that the reviewer has
  since edited: the id is unchanged, so the sweep skips it and the edit is not
  seen until the reviewer posts a new comment.
- A recognized export block pasted into a review thread rather than the
  pull-request conversation: recognition is by lead sentence, so it must work
  identically on either surface.
- The Feedback Sweep Log table does not yet exist in the workflow file, because
  this is the first sweep on this feature.
- The pull request is readable and carries zero comments: a clean sweep with no
  rows written, which proceeds into task work.
- A consensus round on an amended item that reaches no agreement: it produces no
  edit and no class, writes a Consensus Resolution Log row and no sweep row, and
  stops the run under FR-011a. Because no sweep row exists, the comment is a
  candidate again once a human has resolved the disagreement.
- One comment surface reads cleanly and the other fails, or pagination fails on
  page three of five: the whole observation is discarded and the run stops under
  FR-004c. Nothing was written, so nothing is unwound, and the report says
  reading had begun so the operator can tell this from a gate failure.
- Phase 7's `git add -A` runs after the sweep, over whatever the sweep left in
  the worktree: the helper request carrying every observed body, and the
  reply body files. Under FR-004d those sit in an ignored directory the sweep
  removed before proceeding or stopping, so the add finds nothing of the
  sweep's; without both, the request would be committed with an excluded
  author's body in it and no leg would have touched it.
- An amendment committed locally whose push failed: the run stops before that
  amendment's bookkeeping commit, so no row and no reply exist, and the local
  commit stands. The next run treats the comment as a candidate again, which is
  the interrupt window FR-012a already bounds, reached by a different route.
- A reply that posts on the review-thread surface and fails on the conversation
  surface: each affected comment keeps its log row and is owed a reply, which
  FR-015b's reconciliation posts on the next run rather than the failure being
  permanent.
- An analyst that dies mid-round, which happened during this specification's own
  consensus: after the shipped protocol's single retry it becomes a human-review
  outcome and takes the FR-011a path, while the other items in the batch
  complete.
- A resolved edit, a disposition, or a reply that carries a secret-shaped
  span or a line over the per-line bound: the span is replaced by a
  placeholder naming its rule class before the write, the write proceeds,
  the row is written, the reply is posted, and the run report names the
  comment id, the leg, and the rule. Nothing is discarded, because a
  discarded row would leave the comment in the work set with the same
  prose regenerated on every re-run. Once every write has landed the run
  stops for re-review under FR-012f, in FR-017's report shape: the redacted
  text is already public when the stop fires, and the stop is what puts a
  human in front of the report before task work. The next run finds the
  rows and replies in place, fires no event, and proceeds.
- A trusted comment posted after the sweep read the pull request but before the
  run stops: it is not in this run's candidate set and is picked up on the next
  run.
- One comment carrying objections that pull in different directions, for
  example one worth amending and one worth deferring: it takes the single class
  `amended`, and the deferred objection is named in the disposition text and in
  the reply rather than dropped.
- An amendment committed and pushed whose bookkeeping commit never landed: the
  log has no row, so the skip key does not see it and the comment is a
  candidate again on the next run. Per-amendment bookkeeping bounds this to
  one item, and the sweep's own reply cannot serve as a fallback marker
  because FR-006 excludes it from the candidate set. The fresh consensus round
  then either recognizes the artifact already carries the edit and classifies
  the comment answered or no action — one new log row, one new reply, no
  second edit — or amends again, in which case FR-017 stops the run for
  re-review before any task work, the same as a first-time amendment. Neither
  path lets a duplicate edit reach task work unreviewed; this is why the
  window is accepted rather than closed with new detection machinery.
- Two interrupt windows in one run: the first two amendments commit, push, and
  record cleanly and the third amendment's push fails. The run stops with two
  rows written, **zero** replies posted, and one local unpushed commit. FR-015c
  fixes the reply point at end of run, which is what makes that state exact
  rather than ambiguous; the first two comments are owed replies FR-015b posts
  next run, and the third is a candidate again because it has no row.
- A reviewer adds a comment to a review thread whose earlier comment is already
  logged: the new comment carries a new id, matches no row, and is swept as an
  ordinary new item. The thread is not the key.
- A reviewer's comment sits in a thread the operator resolved between runs: the
  sweep never sees it, because FR-004 reads unresolved threads only. This is a
  property of the read, and resolving a thread is the operator's way of taking
  a comment permanently out of the sweep's reach.

## Requirements *(mandatory)*

### Functional Requirements

**Placement and parity**

- **FR-001**: The feedback sweep MUST run as the first setup step of the
  implement stage's task-execution phase, ahead of opening the
  Implementation-Notes Record, in both the Claude and the Codex phase-execution
  references.
- **FR-002**: The sweep MUST NOT add a row to the Workflow Overview table, and
  MUST NOT change the phase-coverage guard's governed phase-id list, the
  stage-to-phase map, or the workflow template.
- **FR-003**: The sweep MUST produce identical behavior in both platform
  variants for the same input.

**Reading the pull request**

- **FR-004**: When the workflow file carries a Draft PR row whose corroboration
  status is `match`, the sweep MUST read every review thread whose resolved
  flag is false and every pull-request conversation comment on that pull
  request. It MUST NOT read review summary bodies.
- **FR-004a**: Both reads MUST be **paginated to exhaustion**. The nearest
  shipped precedent caps its query at a fixed page of threads and a fixed page
  of comments per thread, with no pagination, and silent truncation at those
  caps would contradict SC-001's claim that every trusted, unrecorded comment
  carries a disposition. The reads MUST also request the author-association
  field explicitly; no shipped query requests it today, so FR-005's filter has
  no input unless this read supplies it.
- **FR-004b**: No comment text may reach a shell argument, in either direction.
  Reads pass their query by file or by structured argument, and every write
  passes its body by file path rather than inline. This is the constraint the
  nearest shipped precedent violates: it interpolates comment and reply text
  directly into a command string.
- **FR-004c**: The two reads are **one observation, taken all or nothing**. It
  succeeds only when both surfaces have been read to exhaustion; any read error
  at any point fails the whole observation. This covers the case FR-019 does
  not: FR-019's statuses are observed at the gate, **before** these reads begin,
  so a pull request that corroborated `match` can still fail once reading
  starts. Three failures fall under this rule — one surface readable and the
  other not, a page of either surface failing partway through pagination, and a
  read that returns output that cannot be parsed.

  **A failed observation is discarded rather than swept.** The partial data MUST
  NOT reach classification. The run writes no Feedback Sweep Log rows, posts no
  replies, takes no commit, and stops with the FR-020 report. Nothing needs
  unwinding, because every read precedes every write.

  The reason is FR-019a's principle applied one step later. At the gate,
  treating "could not observe" as "observed nothing" would make the checkpoint
  silently optional; here, sweeping the half that was read would make it
  silently partial, and a half-swept pull request that reported success is worse
  than one that reported failure, because only the second gets re-run.
  SC-001's claim that every trusted, unrecorded comment carries a disposition
  cannot be evaluated against a candidate set that is missing an unknown number
  of comments, so a partial set has no verifiable relationship to the criterion
  the sweep exists to satisfy.

  **The report distinguishes this from the gate stop.** Both draw on the same
  four causes FR-019b names — absent, unauthenticated, rate-limited, or
  unparseable output — so the report MUST also name that reading had begun, and
  which surface failed. An operator who cannot tell a gate failure from a
  mid-read failure cannot tell whether the pull request was ever reachable. The
  resume path is FR-019b's: fix the tool and re-run. The observation is retaken
  fresh on every invocation, so a re-run needs no repair step.
- **FR-004d**: Every file the sweep writes for its own transport MUST live
  under `specs/<feature>/.process/feedback-sweep/` and nowhere else: every
  reply body file FR-004b passes by path; the outbound-leg request files; the
  captured commands; and any scratch the run makes. **The observation is not
  among them.** FR-010a pipes the two `gh` reads straight into the runner on
  stdin, so the document that carried every observed body is never a file at
  all, which is a stronger control than ignoring it and is why the pipe is
  specified rather than left to the implementation. The directory ignores
  itself: the sweep's first write
  into it, before any byproduct, is a `.gitignore` inside it whose whole
  content is `*`, which git honors in whatever repository the worktree belongs
  to, so Phase 7's `git add -A` cannot stage the directory or the ignore file,
  by construction rather than by care. This repository's root `.gitignore`
  carries `specs/*/.process/feedback-sweep/` as well, so the directory is
  ignored here even before the sweep has written into it. The sweep also
  removes the directory before it proceeds into task work or stops, on every
  path, and the run report names it as removed.

  **These files are an outbound path of their own, and the strongest of them
  no longer exists.** FR-004b puts every reply body on disk, and the
  outbound-leg requests carry the text about to be published. The sweep is a
  Phase 7 setup step whose existing commit path is `git add -A` over the
  worktree, so left where they fell each would be committed and pushed. The
  control is placement and an ignore entry. What used to sit here beside them
  was the helper request carrying every observed body, untrusted authors
  included and nothing redacted, which no leg could have redacted without
  blinding the parse it fed; the pipe removes that file rather than protecting
  it, and the fenced-sentinel fixture below is what keeps it removed.

  **Carried with the directory, not with the repository.** The sweep is
  shipped in `phase-execution.md` and runs in any consumer repository that has
  initialized the Spec Kit integration, and a consumer's root `.gitignore`
  carries no entry for this directory. A control that lived only in this
  repository's configuration would therefore protect only this repository,
  and a consumer run whose removal step never ran — a session that hit its
  context limit between the first reply body write and removal, then resumed —
  would stage a reply body and an outbound-leg request. The self-ignore file is
  what closes that: it travels with the directory because the sweep writes it
  wherever it creates the directory. The nearest prior art is the pull-request
  packet directory, which this repository excludes through
  `.git/info/exclude`, a file a fresh clone does not carry; that precedent is
  cited for the shape and not copied for the mechanism. The root entry is one
  authored line of repository configuration, declared in the plan under its
  own category; it is not production, so the production-file count is
  unchanged.

  **Removal is hygiene; the ignore entry is the control.** The entry keeps
  the files out of every commit. Removal keeps them out of everything else
  that reads the worktree, and one such reader is named: the spec-index
  generator scans the filesystem rather than the git index, so live byproducts
  would contaminate a regeneration. A stopping run removes the directory too,
  because nothing in it is needed to resume — the observation is retaken fresh
  on every invocation (FR-004c), and an owed reply is regenerated from its row
  on the next run (FR-015b).

  **Five fixtures, each of which can fail.** A scratch-repository test creates
  a throwaway git repository with no root `.gitignore`, creates the directory
  the way the sweep does — self-ignore file first, then a byproduct — and
  asserts that `git add -A --dry-run` stages nothing under it; it goes red
  when the self-ignore write is removed from the sequence, which is the
  consumer-repository case pinned directly. A repository test asserts this
  repository's root `.gitignore` carries the entry, and goes red when that line
  is removed. The captured-command fixture asserts that the observation read is
  a `gh` command piped into the runner and that no captured argv and no
  captured stdin path names an observation or comment-body file anywhere, and
  that every byproduct path a captured command does name — each body file path,
  each outbound-leg request, the capture files themselves — resolves under the
  directory, so a file written anywhere else is a red test rather than a pushed
  body. A **fenced sentinel** case seeds a distinctive string inside a
  candidate's fenced span, which FR-007g withholds from every block, and
  asserts it absent from every file the run leaves and every captured argv, so
  spooling the observation through a file first is red. And the run-report
  fixture asserts the report names the directory as removed on every path,
  stopping or proceeding.

**Trust boundary**

- **FR-005**: The sweep MUST act only on comments whose author association is
  OWNER, MEMBER, or COLLABORATOR. Every other comment MUST appear in the run
  report as "not swept: untrusted author", MUST NOT be passed to the consensus
  protocol, and MUST NOT influence any artifact edit. The source vocabulary is
  a closed eight-value enum — OWNER, MEMBER, COLLABORATOR, CONTRIBUTOR,
  FIRST_TIMER, FIRST_TIME_CONTRIBUTOR, MANNEQUIN, NONE — and every one of the
  five excluded values MUST have a fixture. The allowlist is a **proxy** for
  write access rather than a statement of it: COLLABORATOR can be a read-only
  invitation and MEMBER is organization membership, which does not imply write
  on this repository. The allowlist stays exactly as stated; the proxy is named
  here so no later reader mistakes it for a permissions check.
- **FR-006**: The sweep MUST exclude replies it posted itself from the
  candidate set on every run, so a reply written by one sweep never becomes
  input to a later one. A comment is the sweep's own reply when **both** hold:
  its body begins with the fixed HTML-comment prefix FR-015 requires, matched
  anchored at the start rather than anywhere in the body, and its author is the
  account this run authenticated as. Both conditions are needed. The marker
  alone would silently skip a reviewer who quoted a sweep reply while
  disagreeing with it, since a quote copies the raw body; the author alone
  would skip that account's every genuine comment, because the sweep
  authenticates as the operator rather than as a bot, and the operator is the
  reviewer this checkpoint exists for. Anchoring defeats the quote case, which
  prefixes the copied text. Every self-reply exclusion MUST be named in the run
  report the way an untrusted-author exclusion is, so a marker collision drops
  a candidate visibly rather than silently.
- **FR-006a**: Without a working self-reply exclusion the loop cannot converge:
  each run's reply is a new comment with a new id, which the FR-009 skip key
  never matches, so it becomes the next run's candidate and produces another
  reply without end. SC-003 would be unreachable rather than merely delayed.
  This is why FR-006 is a requirement and not hygiene.
- **FR-006b**: FR-006's author half depends on an input — the account this run
  authenticated as — and that input has two failure modes the requirement must
  name, because both silently disable the exclusion FR-006a says the loop
  depends on.

  **Provenance.** The orchestrator MUST read that account from the live
  authenticated session at call time, the same way FR-004a requires the
  author-association field be read fresh rather than assumed. It MUST NOT come
  from configuration or a remembered value. This is the same shape of
  dependency FR-004a already names, and it needs saying because no shipped
  reference in this repository documents how the orchestrator learns its own
  login, so nothing today guarantees the value arrives correct.

  **Validation.** The value MUST be a non-empty string after surrounding
  whitespace is stripped. Absent, empty, or whitespace-only MUST return an input
  error rather than proceed. The deterministic parse cannot go further than
  presence: its contract forbids it from reaching the network, so it has no
  second, independently sourced value to compare against, and verification is
  therefore the orchestrator's job through provenance rather than the parse's
  through checking.

  That input error **stops the run**, and it stops it with the FR-020 report
  like every other stop rather than as a bare error return. The condition named
  is the missing authenticated account, and the resume path is to supply it from
  the live session and re-run. Naming it as a stop matters because the parse
  returning an error and the run halting are two different events, and only the
  first was stated: an orchestrator reading this requirement alone could log the
  error and continue, which is the exact outcome FR-006a says the loop cannot
  survive. The stop occurs before any read, so nothing has landed and the
  report's what-landed line is empty.

  **What actually breaks, stated correctly.** An empty value does not reduce the
  test to its marker half. Comparison is exact, so an empty account matches no
  real comment author, the author condition is permanently false, and the whole
  conjunction is therefore always false — meaning **no comment is ever excluded
  as a self-reply**, including the sweep's own. The endless-reply outcome
  FR-006a describes follows, by disabling the rule rather than by narrowing it.
  The distinction matters because the two failures have opposite shapes and a
  reader who expects the wrong one would test for the wrong thing.
- **FR-006c**: FR-006a asserts the loop converges. This states the invariant
  that makes the assertion true and names the one path that does not satisfy
  it, because an asserted convergence nobody can check is not a requirement.

  **The invariant.** A run's **work set** is the comments that pass FR-005's
  trust filter, are absent from the Feedback Sweep Log, and are not excluded as
  self-replies under FR-006. Every run MUST either shrink that set or leave it
  unchanged. **No run may grow it.** Three rules produce this and each is
  necessary: FR-013 writes a row for every handled comment, which removes it
  permanently because FR-009 keys on a comment id that never changes; FR-006
  excludes the replies the run posts, which are the only comments the run adds
  to the surfaces it reads; and FR-011a's no-row outcome leaves its item in the
  set rather than adding a second one. The loop terminates when the work set is
  empty, which is FR-018's proceed condition read as a fixed point. Stating the
  invariant is what makes FR-006a checkable: any future rule that writes to
  either comment surface MUST be tested against it, and a rule that adds an
  unexcluded comment breaks convergence no matter how reasonable it looks
  locally.

  **The one path that does not shrink.** A comment whose consensus round
  returns a human-review outcome takes no class and writes no row, so it is in
  the work set again on the next run and stops that run too. The set does not
  grow, so this is not divergence; but it does not shrink either, and re-running
  without operator action reproduces the same stop indefinitely. This is chosen
  rather than overlooked — FR-011a rejected recording the failure as a
  disposition because that makes it permanent — and it is bounded by a human
  instead of by a counter.

  **What the operator does, and why the report must say it.** For this stop the
  resume path is **not** "re-run": re-running alone re-enters the same round,
  and FR-012a already records that consensus is not proven deterministic beyond
  routing, so a repeat may resolve or may not. The operator either resolves the
  substance and re-runs, or takes the comment out of the run's reach by
  resolving its thread, which FR-004's unresolved-only read turns into permanent
  exclusion. The FR-020 report for a human-review stop MUST name both, because a
  resume path reading only "re-run" would be wrong here in a way it is not wrong
  for any other stop this document defines.

  **No attempt counter is introduced.** A per-comment counter would need a
  durable store keyed by comment id, which is the state-file mirror FR-013
  forbids, and the stop already prevents the run from proceeding on an
  unresolved item — which is the whole of what a counter would protect.

**Deterministic recognition**

- **FR-007**: The sweep MUST recognize an artifact-exported block by matching
  the registry's sentences against the comment's **first ten lines**, as a
  whole-line exact match after normalizing line endings and stripping trailing
  whitespace. The lead sentence is **not** the comment's first line: the
  shipped builder emits `Artifact: <title>`, a feature line, and a blank line
  ahead of it, so the lead lands on line four of a verbatim paste. The
  ten-line window also survives a reviewer trimming that header, and a
  template later adding one. A comment matching no registered sentence MUST be
  treated as an ordinary comment, and recognition MUST NOT require editing any
  shipped gallery template or its payload copy.
- **FR-007a**: The registry MUST also hold the **empty-export** sentences the
  same builder emits when nothing was recorded. On that path the builder
  returns before the lead is ever pushed, so an empty export carries no
  registered lead and would otherwise reach the sweep as ordinary reviewer
  feedback. A recognized empty export takes the class `no action`. Empty
  sentences are not unique per template — **three** shipped templates declare
  the identical string, and three share its companion — so an empty export MUST
  report its template id as ambiguous whenever the matched sentence is shared,
  rather than guessing between the templates that share it.
- **FR-007b**: The registry MUST cover **every shipped template that declares
  an export**, in every kind it declares, not only the draft-stage pages. The
  gallery ships ten exporting templates today and seven of them export a
  `prompt` kind beside the `markdown` kind. Each recognized entry records its
  template id and its kind.

  **Shipped is the operative word, and it costs one exclusion.** The manifest
  declares **eleven** entries as exporting, eight of them in both kinds. The
  eleventh is `uat-walkthrough`, which declares both kinds but has **no template
  file**, so it emits no lead sentence for the registry to carry and none for a
  test to derive. Excluding it is what turns the manifest's eleven and eight
  into the ten and seven above. The exclusion is named here rather than left to
  arithmetic because FR-008a derives the expected set from the manifest, and a
  derivation that did not know about it would demand an entry that cannot exist.
- **FR-007c**: The `prompt` kind matters for safety, not completeness. Its lead
  is an imperative addressed to a coding agent, and an unregistered one reaches
  the consensus analysts as ordinary free text carrying an instruction. The
  security-keyword routing that would otherwise force a full fan-out matches
  none of that phrasing, so leaving these unregistered hides the pattern from
  the mechanism meant to catch it. Recognition is labelling, not distrust: a
  recognized comment still passes the FR-005 filter first and is still
  classified normally by FR-010. What recognition changes is that a registered
  lead is matched as a known constant and carried as metadata, so it does not
  reach an analyst as free instruction text.
- **FR-007d**: Recognition MUST NOT by itself force a class. A reviewer who
  clicks the wrong copy button still meant their objections, and discarding
  them over a button choice would reproduce the "feedback becomes decoration"
  outcome this feature exists to remove. The one exception is the empty-export
  form in FR-007a, which carries no objections to act on.
- **FR-007e**: FR-007c's "carried as metadata" is a claim about the payload
  handed to a consensus analyst, so the payload MUST be specified rather than
  left to the implementation. For a recognized comment, the orchestrator builds
  that payload from two parts: the helper's export record — template id, kind,
  and anchors — and the comment body **with every registered line the helper
  matched removed**. A fixed placeholder stands where the removed line was and
  the export record stands beside the block; the replacement is performed by
  the redaction surface (FR-007g, step 3), which is handed the parse's
  `matched_lines` for that comment. The registered lead therefore never appears
  in an analyst prompt as text, which is the whole of FR-007c's safety claim.

  **Anchors are bounded, because they are reviewer bytes that stand outside
  the frame.** An anchor is the parenthesised value that ends an export line —
  `(#phase-2)` in the shipped builders' output — and a pasted export is
  editable text, so that value is reviewer-controlled. It conforms when the
  whole of it matches `#[a-z0-9-]{1,64}`: a `#`, then one to sixty-four
  characters from `a-z0-9-`, and nothing else. The record carries the run
  after the `#`, as the contract's example does. **An export record holds at
  most sixty-four anchors.** A non-conforming anchor is dropped and counted,
  never carried: it reaches no record, no payload, no row, and no report
  text, and the export record's `anchors_dropped` counts it. A conforming
  anchor past the sixty-fourth is dropped and counted the same way. The
  export record that stands beside the block therefore carries only
  grammar-conforming bytes — a template id and a kind from the registry's
  closed sets, and anchors drawn from a thirty-seven-character alphabet, at
  most sixty-four of them, each at most sixty-four long. Nothing a reviewer
  typed reaches the trusted voice except through that grammar, and by that
  grammar no anchor carries a pipe, a newline, a space, or an instruction.
  The cost is detail alone: a dropped anchor loses its hunk reference, while
  the line that carried it still reaches the analyst inside the frame and the
  objection is still named under FR-010. A fixture pins the drop and the
  count.

  **A registry entry that only tags the comment while the raw body still
  reaches the analyst does not satisfy FR-007c.** That arrangement would leave
  the imperative addressed to a coding agent sitting in the analyst prompt
  exactly as it does today, with a label attached that nothing acts on, and the
  security-keyword routing still matches none of its phrasing. Recognition
  would then be bookkeeping rather than a defense. This paragraph exists
  because that reading is available from FR-007c's wording alone, and one
  consensus analyst took it.

  The remainder of the body still reaches the analyst, because FR-007d keeps
  the reviewer's genuine objections in play. It MUST be delimited and labelled
  as reviewer-supplied data rather than concatenated into the prompt as
  instruction.

  **Delimiting is the strongest in-prompt layer; removal is defence in depth.**
  The two are not equals and the spec says which is which, because a later
  reader deciding what to cut under pressure must cut the right one. Delimiting
  is the control that works against text the registry has never seen, which is
  every adversarial case; removal only ever handles the fixed strings this
  product itself ships. Removal is nonetheless worth keeping, because
  recognition already computes the match span, so stripping it reuses work
  already paid for. **If cost ever forces one of the two out, removal goes and
  delimiting stays.** FR-007g's span replacement ranks **with removal**, not
  with delimiting: both are bounded passes over the body rather than a change
  to how the prompt frames it, so the replacement goes before the frame does —
  and since one surface produces both, cutting the replacement is a change to
  the surface, not to where the frame comes from.

  **None of the three is a boundary, and nothing deterministic stands behind
  them on the forward path.** All three are model-layer controls: they change
  what the prompt says about the text, and whether that holds is a
  probabilistic property of the model reading it. It would be convenient to say
  the deterministic boundary is FR-005's allowlist, and it is not true. The
  helper deterministically **classifies**: it returns a candidate list and an
  exclusion list, and its records carry no body. What is forwarded is still
  decided by the orchestrator, which forwards a candidate's shaped block onward
  only for an id on the candidate list because the phase-execution reference
  tells it to. That forwarding discipline is orchestrator prose, checked
  against FR-008b's second fixture rather than enforced by a type. **There is
  no deterministic boundary on the forward
  path.** FR-005 is still the security boundary Assumptions names, in the sense
  that matters — it fixes whose posting may cause the sweep to act, whatever
  text that posting relays — but at the forward point it is applied by
  judgment, and FR-005 itself records that the allowlist is a proxy that can
  admit a read-only COLLABORATOR. This is stated
  so that a later reader weighing whether the delimiting can be cheapened, or
  the filter relaxed, does not answer yes on the strength of a deterministic
  control that does not exist. The ranking above still holds — delimiting is
  the strongest control available inside a prompt and the one published
  guidance prescribes — and it is a ranking among probabilistic controls.

  **What is deterministic is the consumer, and that is a different claim.**
  The two agents that read a forwarded block — `sweep-classifier`, which
  returns the class, and `sweep-analyst`, which returns a proposed edit — are
  defined by this feature, used by this sequence alone, and neither inherits
  the operator's session. On Claude each pins a `tools:` allowlist — `Read`
  for the classifier; `Read`, `Grep`, and `Glob` for the analyst — and each
  denies `Agent`, `TeamCreate`, `SendMessage`, and `Skill`, so neither holds
  `Bash`, a network tool, a write tool, or the ability to delegate to an agent
  that holds one. The Layer 5 tool-scoping test asserts the exact allowlist for
  each and the exact membership of the exempt pair, so widening either list, or
  adding a third agent to the exemption, fails a test rather than passing
  review. That is a deterministic control, checked in this repository, over
  **what a reviewer body can reach once it is forwarded**. It is not a control
  over what is forwarded, and the two must not be read as one: the sentence
  above still stands. FR-008c is where the assertion is specified.

  **The Codex half of the claim is narrower, and is stated narrower.** The
  Codex agent format carries no tool list and no network field, so the only
  lever there is `sandbox_mode = "read-only"`, which bounds the filesystem.
  For Codex this spec therefore claims a read-only filesystem and network per
  Codex defaults, and claims nothing about tools. Neither runtime sandboxes an
  MCP server process from inside an agent definition; that is curated at the
  profile, outside this feature. Parity of outcome under SC-007 is parity of
  the sweep's behavior, not parity of the two runtimes' enforcement strength.

  **The orchestrator is the residual, and it is bounded by construction rather
  than by enforcement.** It remains a model holding the operator's full
  surface, `Bash` included. What keeps a reviewer body away from that surface
  is that the orchestrator is never handed one to reason over: the observation
  is piped into the runner, the shaped blocks pass through it unread, the class
  comes from the classifier, and the edit comes from the analyst, each as a
  structured record whose only free text is bounded and passed through FR-012f
  before use. That is a property of how the sequence is written, not something
  a type enforces, and an edit that had the orchestrator read a body back for
  itself would undo it quietly. FR-008a's captured-dispatch corpus is what
  turns that edit into a failed count instead of an unnoticed regression.
- **FR-007f**: Removal MUST cover **every** matched registered line, not the
  first. This is not a hypothetical: the registry holds each template's markdown
  and prompt leads as separate entries, so a reviewer who pastes both copy
  outputs from one page into one comment — an ordinary workflow this feature's
  own design invites — produces two matches in the same window. Removing only
  the first leaves the second sitting inside the delimited block, which is the
  first-match sanitization failure that recurs across input-validation defects.
  The helper's export record therefore reports **all** matched line numbers in
  ascending order rather than a single one.

  One implementation constraint, because getting it wrong silently corrupts the
  body: removal indexes the line-ending-normalized **original** lines, never the
  trailing-whitespace-stripped copies matching uses for comparison. The two
  differ, and indexing the wrong one misaligns the reconstructed remainder. The
  removal is executed by the redaction surface (FR-007g, step 3), and the
  carriage-return fixture is what pins that the normalized array is the one
  indexed.
- **FR-007g**: Every body forwarded to **any** agent MUST be shaped before it
  reaches that agent, **whether the comment was recognized or not**, and the
  shaping MUST be performed by code: the **analyst-payload leg of the redaction
  surface**, the second named surface of `sweep-pr-feedback`. FR-007e specifies
  the payload only for a recognized comment, and the common case is the
  opposite one: FR-011 routes `amended` into consensus, and most `amended`
  comments match no registered sentence and reach an analyst as ordinary
  reviewer prose. For an ordinary comment the payload is the block the surface
  returns and nothing else; for a recognized comment it is that block with the
  helper's export record beside it, which is the two-part assembly FR-007e
  already describes.

  **The population is every candidate, not only the routed ones, and the leg
  runs inside the piped observation call.** FR-010a moves classification into
  `sweep-classifier`, which reads a block for every candidate whose export kind
  is not `empty`, so the trigger above is agent-wide rather than
  consensus-wide. The leg is invoked once per such candidate, and it is invoked
  **inside the piped `sweep-pr-feedback` call that consumes the observation**,
  because FR-004's read is piped into the runner and that invocation is the
  only place a raw body exists. Its response therefore carries the bodiless
  candidate records, each candidate's block, and each candidate's shaping
  report together. Everything inside the block is code's work, and that is the
  point of this requirement: an earlier reading placed the shaping in
  orchestrator prose and forbade the helper from doing it, which left every
  rule below with no producer and therefore no fixture that could fail. A
  requirement nothing executes is not a requirement.

  **What the surface takes and what it returns.** It takes one body — the
  capture-truncated copy the parse validated, as captured, with the line
  endings it arrived with, as one text value — together with the comment id,
  the `truncated` flag the parse echoed for that comment, and the
  `matched_lines` the parse reported for it, empty for an ordinary comment. The
  two extra values are the parse's own record for that comment handed back, not
  new data. The body arrives as one string rather than as the array of lines
  FR-012f's outbound legs take, because this leg normalizes line endings itself
  and the parse has already bounded the body far below the runner's per-string
  limit. It returns the delimited block as one text value and a structured
  report: the budget, whether the body is truncated, the count of registered
  leads removed, the count of spans withheld, the count of those that were
  unclosed, and one entry per span naming its kind, its first line, its line
  count, and whether it was unclosed. A `matched_lines` index beyond the body's
  line count is `invalid_input` naming the comment id, never a silent skip: the
  indices were computed over this body, so a miss means the orchestrator handed
  over a different one.

  **This widens nothing.** FR-008b's first assertion is about the parse
  envelope: candidate records carry no body, and they still do not. The
  surface is networkless and write-less like the parse, and it receives one
  body at a time, for an id the parse itself put on the candidate list inside
  the same invocation — which is a narrower entitlement than the earlier one,
  because the orchestrator no longer holds a body to hand back.
  Registration stays one operation; the Known Interface Gap in `tasks.md`
  sanctions named surfaces of that one operation, and this is the second. What
  the surface does not do is decide whether a shaped block is forwarded — that
  is orchestrator prose, and no deterministic boundary stands on the forward
  path — and it does not make the agent honour the frame, which is a
  property of the model reading it. The surface makes the payload's **shape**
  provable. It proves nothing about what is done with it.

  **The order is defined, and there is one order.** Five steps, in place,
  over one line array:

  1. **Normalize line endings**, CRLF and CR to LF, by the rule the parse
     uses. This is what makes `matched_lines` index the array they were
     computed against (FR-007f), and it is why the orchestrator hands over the
     copy as captured rather than a normalized copy of its own: there is no
     second copy to get wrong.
  2. **Bound at 8192 bytes**, the budget `data-model.md` and the contract fix
     for comment bodies — FR-008 requires a budget and names no number —
     cutting on a character boundary so the result is valid text. On a
     conforming input this is a no-op. On a body over budget it is the cut,
     and the surface cuts rather than rejects, because its output is the
     bound: the payload cannot exceed the budget whatever was handed in. The
     report's `truncated` is the input flag **or** the surface's own cut, and
     the two cannot disagree, because the bound is one number and cutting an
     already-cut body at that number changes nothing. The bound runs
     **before** the scan on purpose: a cut that lands inside a fence leaves an
     unclosed opener, the scan then withholds to the end of the body, and the
     report says both things — truncated, and one span withheld, unclosed.
     Neither rule is argued in isolation; this is their composition.
  3. **Replace each matched registered line in place** with the fixed
     placeholder `[registered export lead removed]`. Replacement keeps one
     line as one line, so nothing shifts under the scan. This runs before the
     scan because the scan collapses many lines into one placeholder and
     would move the indices. A lead a reviewer pasted inside a fence is
     replaced here and then withheld with its fence in the next step; the
     report still counts it as removed.
  4. **One left-to-right span scan.** Two opener shapes. A **fence** opens on
     a line whose first non-whitespace run is three or more backticks or three
     or more tildes; its info string is the rest of that line, trimmed. An
     **HTML comment** opens at `<!--` anywhere in the text. At each point the
     **earliest opener by byte offset wins**; a fence's offset is its first
     fence character, which is the first non-whitespace byte of its line, so
     a `<!--` later on the same line never outranks it. A span closes only on
     its own closer: a fence closes at the first later line whose first
     non-whitespace run is the same character, at least as long, with nothing
     but whitespace after it; an HTML comment closes at the first `-->` found
     when the search begins after the opener's own four bytes. **Spans do not
     nest**: inside a span no opener of either kind is recognized. When a
     span closes the scan resumes at the next byte, and because a fence opener
     is recognized only at the start of a line, the remainder of a line after
     a `-->` is never one. **An unclosed opener runs to the end of the body**
     and its placeholder says so. A fence's placeholder replaces the opener
     line through the closer line; a comment's placeholder replaces exactly
     the bytes from `<!--` through `-->`, so prose beside it on the same line
     survives. That is the whole rule, so the overlapping case has one
     answer. The body `<!-- draft note` / ```` ``` ```` / `--> keep this` /
     ```` ``` ```` / `The real objection is X.` yields a comment placeholder
     for lines one to three, ` keep this`, and an unclosed-fence placeholder
     for lines four and five. The objection is withheld, the counts say two
     spans and one unclosed, and two conforming implementations produce the
     same bytes. An unclosed opener withholding trailing prose is the stated
     cost of failing closed, and the counts are what disclose it.
  5. **Frame and label.** The block is an opening delimiter line carrying the
     comment id; one fixed statement line; the shaped body; and a closing
     delimiter line carrying the id again. The statement line says the block
     is reviewer-supplied data and not instruction, whether the body was
     truncated and at what budget, how many spans were withheld and how many
     of those were unclosed, how many leads were removed, that a bracketed
     placeholder marks each point where the reviewer's text is not visible,
     and that the full comment is on the pull request. The exact strings are
     fixed in the contract and pinned by the golden envelope, and the counts
     the statement carries MUST equal the counts the report carries.

  **The scan runs after the parse, so FR-006 is untouched.** The parse's
  exclusions ran over the observed body before the surface exists in the
  flow, so the self-reply marker's anchored match at position 0 is
  unaffected, and a reviewer's quoted sweep reply is still admitted as a
  candidate before any span is replaced. Inside a candidate that quoted
  marker is an HTML comment like any other and is withheld like any other,
  which costs nothing: the marker renders as nothing and carries no
  objection.

  **Placeholders are bounded, and they stand inside the frame.** The grammar
  is fixed: `[withheld: fenced block, info "<echo>", <n> lines]` or
  `[withheld: fenced block, no info string, <n> lines]` for a fence,
  `[withheld: html comment, <n> lines]` for a comment, `1 line` when the count
  is one, with `, unclosed` before the closing bracket when the span ran to
  the end. The echoed info string is reviewer-controlled text and is cut at
  **32 bytes** on a character boundary; a comment's placeholder echoes
  nothing. No placeholder therefore exceeds **96 bytes**, and the worst case
  is stated rather than left to arithmetic: the smallest span is seven bytes
  (`<!---->`) or eight (a minimal fence pair), so a body at the budget holds
  at most roughly 1170 spans, and the shaped body is at most roughly six
  times the budget under adversarial input and a few placeholders long under
  any real comment. Placeholders stand inside the delimiter, never outside
  it, because a fence's info string is reviewer bytes and a placeholder
  written outside the frame would move them into the trusted voice the frame
  exists to keep them out of. The export record beside the block is the one
  other thing outside the frame, and FR-007e bounds it to grammar-conforming
  bytes for the same reason.

  **What the shaping is for, stated so nothing more is read into it.** Volume
  bounding and machine-span removal, only. A fenced block is where pasted
  machine content sits — logs, diffs, configuration, the credential nobody
  meant to paste — and where a body's volume is least bounded; an HTML
  comment renders as nothing on the pull request, so the Assumptions rule
  that a trusted author endorses what their body carries does not reach it,
  because an author cannot endorse text their own view never showed them.
  Neither rule detects an instruction. An imperative sentence written as
  ordinary prose passes through the surface unchanged and reaches the analyst
  inside the frame, and a fixture pins that it does, so nobody later mistakes
  the span rule for a filter. The controls against that text remain the frame
  itself, FR-005's author allowlist, and FR-017's checkpoint, and none of the
  three is detection. The trade is real and is named: a reviewer who fences
  the replacement text they are proposing loses it from the analyst's view,
  the placeholder tells the analyst where, and the reply's last line under
  FR-015 tells the reviewer so. Indented code blocks — four leading spaces,
  no delimiter — are **out of scope**: they are not a span, they pass
  through, and a fixture pins that too. The bound on volume is the byte
  budget in step 2, not the span rule, and the span rule is not claimed to be
  complete over code-shaped content. Nor is the scan CommonMark: a backtick
  run inside an indented block, a line markdown reads as inline code, and an
  HTML comment inside inline code are all spans to the surface and visible
  text to the author, so the surface can withhold what the author's view
  showed, and that over-withholding is accepted for the one deterministic
  rule the fixtures pin.

  **Both readers are told, and what follows from telling is not overstated.**
  The statement line tells the analyst it is reading a reduced body and what
  kind of reduction it is; the disposition cell records the truncation and
  the span count — orchestrator prose under T083, with no fixture of its own
  — and the reply's fixed last line under FR-015, which is fixtured, carries
  both to the reviewer, who reads the pull request and not the workflow
  file, so the reviewer whose comment was cut can see why the sweep answered
  only the part it saw. What the analyst does with the notice is model
  judgment. No defined outcome follows from it: FR-011a's three triggers do
  not include an analyst noticing that it lacks information, three analysts
  can agree confidently on a reduced body, and this document does not claim
  otherwise. What holds is FR-017 — an amendment built on a reduced body
  still stops the run for re-review before anything merges — and the reply's
  truncation line, which is where the reviewer learns their fence was not
  read.

  **Delimiter forgery is disclosed, not solved.** A body line identical to
  one of the delimiter lines passes through unchanged, and a fixture pins
  that it does, so no implementation escapes it "helpfully" and breaks the
  byte-exact envelope. The frame is a model-layer control, as FR-007e says of
  every in-prompt control, and a forged delimiter is the same residual by
  another route. The comment id in both delimiter lines is what a forger has
  to know; it is not a defense.

  **Ranking is unchanged.** The span replacement ranks with FR-007f's removal
  — a bounded pass over the body — and the frame ranks as FR-007e's
  delimiting. If cost ever forces a cut, the replacement goes and the frame
  stays, and because one surface produces both, cutting the replacement is a
  change to the surface and not to where the frame comes from.
- **FR-008**: Candidate filtering, export recognition, and candidate reporting
  MUST be deterministic: the same observed pull-request comment data MUST
  always yield the same candidate set. Determinism requires two normalizations
  stated here rather than left to the implementation: line endings are
  normalized before matching, and each comment body is truncated at a fixed
  byte budget well below the runner's 32 KiB bounded-input limit, with the
  truncation flagged per comment. Truncating is not optional — the limit is
  enforced over every string in a request and rejects the **whole** request, so
  one oversized comment would otherwise fail an entire sweep rather than
  degrading that one item.
- **FR-008a**: Golden fixtures MUST pin: every registered sentence, in both the
  verbatim payload shape and a header-trimmed paste; a body delimited with
  carriage returns; an oversized body that truncates; the untrusted-author path
  **for each of the five excluded association values**; one recognized export
  on each of the two comment surfaces; a disposition cell containing a pipe and
  a newline; a comment whose author cannot be resolved; a comment carrying the
  self-reply marker, and one carrying the marker with a **different** comment
  id after its fixed prefix, asserting the FR-006 anchor still matches and
  FR-015b's reconciliation reads the id rather than the prefix; a body carrying
  **two** registered lines, asserting both are reported and both removed; an
  export carrying a malformed anchor and one carrying sixty-five conforming
  anchors, each asserting the non-conforming or surplus anchor is absent from
  `anchors` and counted in `anchors_dropped`; an empty and a whitespace-only
  authenticated account, each returning an input
  error; and — each as a request to the redaction surface's analyst-payload
  leg, asserted against the block and report it returns rather than against a
  hand-written payload — a body carrying a fenced code block and one carrying
  an HTML comment, each asserting the seeded span never reaches the block
  while its placeholder does, inside the frame; an unclosed fence and an
  unclosed HTML comment, each running to the end of the body and saying so;
  the overlapping-span body, returning the one block FR-007g defines; the body
  truncated inside a fence, whose report and statement line both say truncated
  and both count one unclosed span; a carriage-return body with a matched
  line, removed only when the normalized array is indexed; an indented code
  block, a plain-prose imperative, and a delimiter-shaped line, each passing
  through unchanged; and every block carrying its originating comment id in
  both delimiter lines; and the ordinary-comment path, pinned as a payload
  shape as well as a candidate one — the returned block alone, with no export
  record beside it.

  The failure paths MUST be pinned too, or the requirements grow while the
  corpus stays where the happy path left it: a read that fails on the second
  surface and one that fails mid-pagination, both asserting zero rows, zero
  replies, and zero commits; a corroboration value outside the six; a push
  failure after an amendment commit, asserting no row and no reply followed it;
  a reply that fails on one surface, asserting the comment is owed a reply and
  that a re-run posts exactly one; a comment already carrying a sweep reply,
  asserting no second one; and a human-review consensus outcome, asserting a
  Consensus Resolution Log row, no Feedback Sweep Log row, and a stop. Each of
  these is a stop or a recovery whose whole value is that it behaves correctly
  when something else has already gone wrong, which is exactly the condition a
  hand-run check never reaches.

  The outbound path MUST be pinned on the redaction surface, because every
  rule in it is a MUST that a hand-run check never exercises: one case per hit
  class on the amendment leg, six in all, each asserting the seeded span is
  replaced by its placeholder, the surrounding text and the line count are
  unchanged, the report carries exactly one event naming that rule, and the
  write proceeds; one seeded string carried across all three legs, asserting
  the same on the log-row and reply legs and that line 1 of the reply is
  still the marker, alone and byte-identical; the marker-line case, the
  marker carrying a node id as the sole line of a `reply` request, asserting
  zero events and byte-identical output; the ordered bound case — a line over
  8192 bytes whose tail carries a bearer token, asserting one
  `over_bound_line` event and no `bearer_token` event — beside its sibling at
  8188 bytes, the longest line whose bearer replacement still fits the bound,
  asserting the reverse; the
  key-span cases, a header with body and END line asserting a placeholder on
  every line, a header with body and no END asserting placeholders to the end
  of the text, and a body with no header asserting **no** redaction, which
  pins the residual as a known miss rather than coverage; the negative cases,
  each asserting zero events and byte-identical output — `bearer
  authentication_credentials`, `bearer credentials/authorization-header`, the
  phrase `bearer token`, a bare `GITHUB_TOKEN`,
  `RELEASE_PLEASE_TOKEN=${{ secrets.RELEASE_PLEASE_TOKEN }}`,
  `GH_TOKEN=<your-token>`, a `_TOKEN=` value of twenty `x`s, and a bare
  GitHub node id, which is a token-shaped run with no trigger before it; the
  corpus-scan case, every line of this feature's seven documents — `spec.md`,
  `plan.md`, `tasks.md`, `data-model.md`, the contract, `quickstart.md`, and
  `research.md` — through the amendment leg, one request per document,
  asserting zero events and byte-identical output, so no rule fires on the
  prose that describes it; the idempotence case, every positive case's output
  fed back through the surface and returned unchanged with zero events; the
  boundary case, an 8189-byte line ending in a bearer hit, asserting the whole
  output line is the `over_bound_line` placeholder, the report carries the
  `bearer_token` event and then the `over_bound_line` event on that line, and
  the placeholder fed back returns unchanged; the transport cases, a 9 KB line
  and the same line cut to 8193 bytes asserting byte-identical output and a
  byte-identical report, and a request carrying a 33 KiB line asserting the
  runner's `invalid_input` naming the field; a `leg` outside the four,
  returning an input error; and the no-echo search, the seeded string absent
  from every captured output in the corpus.

  The byproduct rule is pinned by the three fixtures FR-004d names: the root
  `.gitignore` carrying `specs/*/.process/feedback-sweep/`, red when the line
  is removed; every byproduct path in every captured command resolving under
  that directory; and the run report naming the directory as removed on every
  path.

  The orchestrator half of the surface MUST be pinned the way SC-009 pins the
  shell boundary: every invocation of the surface is captured — leg, comment
  id, and the request and response as sent — beside the captured commands,
  and a fixture asserts per-leg call counts derived from the corpus
  expectations rather than typed beside them. The derivation is fixed by the
  call granularity FR-012f and FR-007g state: one `amendment` call per
  amendment; one `log_row` call per prose cell, which is three for an amended
  item, two for a human-review item, and one for any other class; one `reply`
  call per reply the run posts, which is every comment handled this run plus
  every owed reply FR-015b reconciles this run, both read from the case's
  expectations, so a re-run case that classifies nothing and posts one owed
  reply derives one; and one `analyst_payload` call per **candidate whose
  export kind is not `empty`**, not per comment routed to consensus, because
  FR-010a hands the surface's block to `sweep-classifier` for every such
  candidate and hands that same block to the analysts when the item takes
  `amended`. A second call for the same comment id fails the count, and by
  SC-005 it would return the same block anyway. A forgotten call fails the
  count, which is the failure a
  response-only corpus cannot see. The same capture makes the report
  checkable: the disposition text the run report carries for a comment MUST
  be byte-identical to the `log_row` response for that comment's
  `Disposition` cell, taken before FR-013's escaping, so a report built from
  the orchestrator's pre-redaction copy fails by comparison rather than by
  inspection.

  **The agent dispatches are captured on the same terms as the surface calls**,
  because the whole trust claim of the sequence is that a block reaches only the
  two scoped agents, and a claim about who was handed what is unmeasurable
  against responses alone. Every dispatch is captured — the agent name, the
  comment id, the prompt as sent, and the structured record returned — and a
  fixture asserts per-agent counts derived from the corpus expectations rather
  than typed beside them: one `sweep-classifier` dispatch per candidate whose
  export kind is not `empty`, and for each item classified `amended`, three
  `sweep-analyst` dispatches, one per perspective, plus one `sweep-analyst`
  synthesis dispatch, which is four. A case with six such candidates of which
  two amend therefore derives six classifier dispatches and eight analyst
  dispatches. The same capture makes two negatives checkable that nothing else
  here can see: **no dispatch names an agent outside the two**, so a block
  routed to a shared consensus role or to `consensus-synthesizer` fails rather
  than working; and **no captured orchestrator step carries a comment body**,
  because the observation is piped into the runner under FR-004d's transport and
  every orchestrator request beside it carries ids, enum values, and
  surface-shaped or surface-redacted text alone, so classification performed in
  the orchestrator fails a count instead of passing review. SC-015 measures
  both.

  A separate test MUST derive the expected set from the gallery manifest and
  the templates themselves — every template the manifest says exports, in
  every kind it declares, **less the FR-007b exclusion** — and assert the
  registry matches. That exclusion is a pinned list of exactly one entry,
  `uat-walkthrough`, which the manifest declares as exporting both kinds but
  which ships no template file to read a lead from.

  **The skip MUST be conditional in both directions, not a bare name.** An entry
  is skipped only when it is on that list **and** its template file is still
  absent. A template that goes missing by accident is therefore not silently
  tolerated — it is not on the list, so it fails. And an entry that later ships
  its file stops being skipped and must be derived, which matters more than it
  looks: `uat-walkthrough` declares a `prompt` kind, so a name-only skip that
  outlived the missing file would leave that imperative lead unregistered, which
  is exactly the exposure FR-007c exists to close. A bare name closes the
  registry against the gallery growing back. Deriving rather than hardcoding is what keeps the registry
  correct as the gallery grows: a template that changes its wording, or a new
  exporting template, fails a test rather than silently disabling recognition.
  It also makes the registry's size a data question rather than a design one,
  so covering ten templates costs the same machinery as covering three. That
  test reads the templates and edits none of them, so it does not cross the
  no-template-edits boundary and triggers no payload regeneration.
- **FR-008b**: Two assertions pin the trust boundary itself rather than any one
  behavior, because both guard a leak that would otherwise be invisible.

  First, **no comment body appears anywhere in the parse's own output**. The
  records it returns carry the id, the surface, the author and association, the
  truncation flag, and the export metadata, and no body field at all. That is
  already how the contract is shaped; a fixture asserting it turns an implicit
  shape into a tested invariant, so a later field addition cannot quietly
  reintroduce the most dangerous leak path.

  Second, **an excluded comment's body and every registered line never appear in
  any payload dispatched to an agent**, asserted against a captured payload the
  way SC-009's boundary is asserted against captured commands. This is the half
  that cannot be made structural: the parse decides which ids get a shaped
  block, and the orchestrator decides which of those blocks it forwards and to
  whom, so what must be proven is that no block is produced or forwarded for an
  id the parse excluded. That is judgment checked against a fixture rather than
  a type the runner can enforce, and saying so is more honest than implying a
  guarantee that does not exist.

- **FR-008c**: The repository test that pins agent tool scoping MUST carry a
  named carve-out for the two agents that read reviewer text, and the carve-out
  MUST be tight enough that every way of widening it is red.

  **The rule being carved out, and why it is right everywhere else.** Layer 5
  asserts today that no Claude agent definition declares a `tools:` allowlist,
  with the message that availability is operator-owned and role denials belong
  in `disallowedTools`. That rule is correct for every agent the plugin ships
  today, all of which act on operator input, spec text, and repository content
  — trusted material, where inheriting whatever the operator installed is the
  feature. It is wrong for the two agents this slice adds, whose input is
  reviewer-derived and therefore attacker-controllable. Capability inheritance
  is right for an agent acting on trusted input and wrong for an agent reading
  text an attacker can write. Reversing a repository-wide rule for two named
  agents is a policy change, it is taken here deliberately, and it is the only
  policy change this slice makes.

  **The carve-out is a tuple, not a pattern.** A new
  `UNTRUSTED_INPUT_CONSUMERS = ("sweep-classifier", "sweep-analyst")` sits
  beside the validator's existing role tuples, and three assertions bind it:
  1. **Exemption from one rule, not from the file.** Members MUST be exempt
     from the no-allowlist assertion and from nothing else. The second
     assertion in that same test method — no vendor-qualified `mcp__` token
     anywhere in the frontmatter — still binds them, as does every other check
     in the file, including the session-shape metadata rule and the named-tool
     regression guard that scans prose on both platforms. The exemption is by
     membership rather than by pattern, so it does not generalize: adding
     `tools: Read` to a non-member's definition is red on the unchanged rule.
  2. **Each member pins exactly its stated allowlist.** `sweep-classifier`
     exactly `Read`; `sweep-analyst` exactly `Read, Grep, Glob`. The
     comparison MUST be equality over the parsed set, never containment, for
     the reason FR-012c gives for the three-file check: a containment test
     passes anything that also contains the allowed values, which is every
     widening this assertion exists to catch. Appending `Bash` to
     `sweep-analyst` is red, and so is dropping `Grep`, so the assertion is a
     pin in both directions rather than a ceiling. `Read` is on the
     classifier's line because the runtime refuses a subagent that resolves
     zero tools and `Read` is the narrowest tool a subagent can be given.
     **The empty-list question is deliberately not probed, and this clause
     says so rather than leaving the tightening open.** A bare `tools:` key is
     YAML null and reads as omitted, so an agent carrying one inherits the
     operator's whole surface, `Bash` included, and the dispatch succeeds. The
     probe would therefore look like success at the exact moment it disarmed
     the control, which is why the implementation task forbids it outright.
     `Read` is the floor and stands. What the implementation task probes
     instead is that the allowlist **binds**, so this assertion stays pinned
     at the two stated allowlists rather than held open against a tightening
     that has no safe way to be tested.
  3. **The tuple's membership is asserted exactly.** The assertion MUST
     compare `UNTRUSTED_INPUT_CONSUMERS` against its literal two-name value
     and MUST assert it disjoint from the open-executor tuple. Appending an
     open executor to it is red. Without this assertion the carve-out is a
     door rather than a window: a future editor facing the no-allowlist rule
     could buy an exemption for an open executor by adding one name to a tuple
     whose whole justification is that its members read attacker-controllable
     text, and nothing would notice.

  **Members MUST also deny the orchestration set and `Skill`**, asserted in the
  shape the read-only roles are already asserted in: `Agent`, `TeamCreate`,
  `SendMessage`, and `Skill` each present in `disallowedTools`. Removing
  `Agent` from `sweep-analyst`'s line is red. The allowlist alone would not be
  enough without this, and the reason is one hop out: an agent that can spawn
  another agent hands the reviewer's text to whatever it spawned, and the
  spawned agent's surface is the operator's, not this one's. A closed allowlist
  that can delegate is not closed.

  **The Codex half is `sandbox_mode` and nothing else, and the claim is
  narrowed to match.** The validator MUST assert `sandbox_mode = "read-only"`
  for both members' Codex definitions directly, keyed off
  `UNTRUSTED_INPUT_CONSUMERS` rather than by adding the two names to the
  existing Codex read-only tuple, which would also assert a model and a
  reasoning effort that this design never fixed for these agents and that no
  requirement here justifies. Flipping either definition to `workspace-write`
  is red. The honest limit belongs in the same breath: the Codex agent format
  carries no tool allowlist and no network field. The installer reads exactly
  two keys and copies the rest through byte-for-byte, the Layer 1 Codex
  validator rejects the Claude-only frontmatter fields outright, and the only
  place `network` appears anywhere in the repository is a descriptive corpus
  manifest that nothing reads back from an agent definition. So the spec claims
  for the Codex variants only **read-only filesystem; network per Codex
  defaults**, and it does not claim the network is closed there. The install
  skill's own operator note adds the second limit: a read-only sandbox does not
  sandbox MCP server processes, so write-capable MCP servers are curated out at
  profile level rather than by anything this slice ships.

  **The rationale is recorded in the validator's module docstring**, in one
  sentence: capability inheritance is right for agents acting on trusted input
  and wrong for agents reading attacker-controllable text. A tuple whose reason
  lives only in a spec is a tuple the next editor deletes as dead weight.

  One implementation constraint, because getting it wrong makes the whole
  carve-out silently inert: the validator's suite builder iterates its ordered
  tuple of test-method names and nothing else, so a method added to the class
  but not to that tuple never runs and nothing counts its absence. Every method
  the carve-out adds is appended there in the same change.

  **The subtest count moves, and that is fine.** The parity baseline recorded
  for this validator is capture tooling with no run-time consumer — nothing
  compares the live count against it — so the new subtests change the total
  freely and no baseline file needs regenerating for them.

  **What this pins, and what it leaves standing.** FR-008b's second assertion
  ends by admitting that the forward path has no deterministic boundary,
  because the orchestrator decides what it forwards and that discipline is
  prose checked against a fixture. FR-008c does not change that. It changes
  what a laundered instruction reaches once forwarded: a consumer with three
  read tools, no shell, no network, and no fan-out, held there by an equality
  assertion. The residual is the orchestrator itself, which keeps `Bash` and
  applies every write. Its control is that it is never handed a comment body —
  the observation is piped into the runner rather than written to disk, the
  shaped blocks pass through unread, and classification moved out of it
  entirely — which is a property of how the sequence is built rather than
  something a test enforces, and this requirement claims no more than that.

**Idempotency and classification**

- **FR-009**: The sweep MUST skip any comment whose id already appears in the
  Feedback Sweep Log. The skip key is the log's comment-id column and nothing
  else: the log is the sole source of "already handled", so a comment absent
  from it is a candidate even when a reply to it exists on the pull request.
- **FR-009a**: FR-009's skip is scoped to **classification**, not to
  observation. A logged comment is still read, still carries a disposition in
  the FR-018a report, and is still visible to FR-015b's reply reconciliation.
  What the skip suppresses is re-classifying it, re-routing it through
  consensus, and writing a second row.

  The scope is load-bearing rather than pedantic. FR-015b recovers a lost reply
  by finding a comment that **has** a log row and carries no reply, so a skip
  read as "drop from the run" would put every recoverable comment out of
  reach and make that rule unreachable — the reply would be permanently lost,
  which is the exact outcome FR-015b exists to prevent. The two rules read the
  same comments from opposite ends and must agree that it is the same set.

  **A new comment on an already-logged thread is a new item.** The key is the
  comment id, never the thread id, so a comment a reviewer adds to a thread
  whose earlier comment is logged has an id matching no row and is a candidate
  like any other. This follows from FR-009 as written; it is stated because the
  thread is the unit a human sees on the pull request, and a reader who carried
  that unit into the skip key would suppress every later comment in the thread
  and silently reproduce the "feedback becomes decoration" outcome one level
  down.

  **A thread the operator resolves stops producing candidates.** FR-004 reads
  only unresolved threads, so once a thread is resolved neither its logged
  comments nor anything added to it afterwards reaches a later run. FR-015b
  already names this consequence for replies; it is the same consequence for
  candidates, and it is a property of the read rather than a defect. Resolving
  threads is **not** a precondition for the run to proceed — FR-018 turns on
  handled comments alone — but it does end that thread's participation, and an
  operator who resolves a thread to tidy the pull request should know that is
  what they are doing.

  **A log row whose comment-id cell cannot be read stops the run** under FR-020,
  naming the row. Fail-closed is forced by the reasoning FR-019 already gives
  for an unrecognized corroboration value: the row is text in a file a human
  edits, an unreadable key is indistinguishable from an absent one, and the two
  guesses fail in opposite directions — reading it as absent re-processes a
  handled comment, reading it as present skips an unhandled one. Neither guess
  is safe, so neither is taken.
- **FR-010**: Every trusted, unrecorded comment MUST be assigned exactly one
  class from the closed set: amended, answered, deferred, no action. No other
  value is permitted. The comment is the unit of classification, so a
  recognized export block carrying several distinct objections still yields one
  class, one log row, and one reply; the recognized anchors — the conforming
  ones FR-007e keeps, which carry no pipe by grammar — are carried as detail
  on that row. When one comment's objections would warrant different
  classes, `amended` MUST win over the other three, and every non-dominant
  objection MUST be named in the row's disposition text and in the reply, so
  nothing is silently dropped. This order is forced, not stylistic: the
  roadmap's "sweep, amend, re-review" decision rejected leaving re-run
  responsibility to manual judgment because that lets feedback become
  decoration, and a classifier that let a mixed comment escape `amended`
  would recreate that same rejected path one layer down; FR-003's
  cross-platform determinism requirement rules out any non-fixed tie-break
  as the alternative.
- **FR-010a**: FR-010 fixes the classes, the unit, and the tie-break, and says
  nothing about **who** assigns them. Today that is the orchestrator, which
  holds the observation, reads a body for every candidate, and carries the
  operator's whole tool surface — `Bash`, `WebFetch`, `WebSearch`, and every
  installed MCP server. That is the trust-boundary review's F-1 and F-2 stated
  once each: the participant that reads reviewer-controlled text is the one
  participant that can act on it anywhere. Classification MUST therefore be
  performed by **`sweep-classifier`**, a scoped agent this feature ships on both
  platforms and only the sweep dispatches, **one dispatch per candidate**, and
  the orchestrator MUST NOT read a comment body or a shaped block on any path.

  **What bounds the classifier.** On Claude Code its frontmatter MUST pin
  `tools: Read` and MUST deny `Write`, `Edit`, `MultiEdit`, `NotebookEdit`,
  `Skill`, `Agent`, `TeamCreate`, and `SendMessage`; on Codex the definition
  MUST declare `sandbox_mode = "read-only"`. FR-008c specifies the assertions
  that pin all of it, and states the honest Codex limit: `read-only` filesystem,
  network per Codex defaults, nothing claimed about tools. `Read` rather than
  nothing, because the runtime refuses a subagent that resolves zero tools and
  `Read` is the narrowest tool a subagent can hold. The empty-list question is
  deliberately not probed, for the reason FR-008c records: a bare `tools:` key
  is YAML null and reads as omitted, so the probe would look like success at
  the moment it disarmed the control. The implementation task probes that the
  allowlist binds instead. This is a **reversal of a repository-wide rule**, taken deliberately, and
  the reason is the sentence FR-008c records: capability inheritance is right
  for an agent acting on trusted input and wrong for one reading text an
  attacker can write.

  **What it receives.** One prompt, one candidate: the comment id; **one**
  sanitized, delimited block, which MUST be the output FR-007g's
  analyst-payload leg produced for that comment and nothing else; the closed
  class vocabulary and the three-file target set FR-012b fixes; and, for a
  recognized comment, the parse's export record, which FR-007e already bounds to
  grammar-conforming bytes. FR-007d still holds: recognition tells the classifier
  what the comment is, never what class it takes. **A candidate whose export
  kind is `empty` is never dispatched**, because FR-007a already forces
  `no action` for that form from the parse alone and dispatching an agent to
  re-decide a forced class would reopen what FR-007a closed. This widens
  FR-007g's trigger from every body forwarded to a consensus analyst to every
  body forwarded to any agent, and moves that leg's call site inside the piped
  observation call, which supersedes its entitled-orchestrator rationale; those
  two edits are the whole of this requirement's ripple into it.

  **What it returns.** One structured record, four fields, fixed by
  `contracts/sweep-classifier-output.md`: the echoed `comment_id`; `class`, from
  FR-010's closed set; `target`, one of `spec.md`, `plan.md`, `tasks.md`, or
  null, which MUST be null for every class except `amended`; and `reason`, a
  string of at most **512 bytes** as UTF-8 carrying neither pipe nor newline.
  The target is advisory — FR-012b rule 2 is still the write-point check, so a
  target the analysts contradict widens nothing. A record carrying a fifth
  field, a fifth class value, a target outside that set, a non-null target on a
  class other than `amended`, or a reason over the cap is **malformed**, and a
  malformed record MUST stop the run under FR-020 naming the comment id, with no
  coercion and no re-prompt. Coercion would have the orchestrator decide which
  of the four a fifth value meant, which is classification moving back into the
  orchestrator one record at a time, and a re-prompt is the orchestrator
  negotiating with a model over attacker-shaped input, which is the loop the
  frame exists to avoid. The cap fails the record rather than cutting it for a
  reason worth stating: a cut lands anywhere, and a cut inside a token-shaped
  run leaves the run under the twenty characters the deny-set requires, so
  nineteen bytes of a secret would publish behind a `bearer` trigger whose rule
  no longer fires. One rule, one outcome, and the byte-identity below stays
  exact.

  **Where the classification rules now execute.** FR-010's amended-wins
  tie-break and FR-012b rule 1, an out-of-scope target taking `deferred` with
  the refused target named, move into the classifier's definition unchanged in
  content. They are stated once, there, and both phase-execution references
  carry the dispatch, the payload, and the record's shape and point at the
  definition for the rules rather than restating them, so the two cannot drift
  and the budget is not spent twice.

  **The observation is piped, not filed.** The two `gh` reads' output MUST be
  piped into the runner on stdin, and the sweep MUST NOT write, and MUST NOT
  compose, any file or any argument carrying an observed body. FR-004b keeps
  comment text out of a shell argument; this extends the same rule to disk and
  to the orchestrator's judgment, and it replaces FR-004d's first named
  byproduct — the request file that carried the observation — leaving the reply
  body files, the outbound-leg request files, and the captures behind it. One
  call still reads both surfaces, so FR-004c's all-or-nothing observation is
  unchanged. The piped call shapes every dispatched candidate inside itself, so
  its response carries the bodiless candidate records, each candidate's block,
  and each candidate's shaping report together. **The orchestrator is a conduit
  for a block and never a reader of one**: it hands each block to the classifier
  unchanged, and for an amended item hands that same block to the analysts, and
  no path asks it to read one.

  **What the orchestrator acts on, and what it may do with it.** From the parse
  response: ids, surfaces, authors, associations, truncation flags, export
  metadata, and the shaping counts — `truncated`, `spans_withheld`,
  `leads_removed` — which are what FR-013's disposition and FR-015's reply need,
  taken from the report rather than from a model's transcription. From each
  dispatch: the enum, the target, and the bounded reason. Nothing else, on any
  path. The reason is reviewer-derived text a model rewrote, so it MUST pass
  FR-012f's `log_row` leg before any use, and the string that leg returns is the
  only form that reaches the `Disposition` cell, the run report, and any reply
  text derived from it — never the orchestrator's copy of what the classifier
  said. FR-012f already fixes that identity for the report; this extends it to
  the reply and leaves the raw reason with no sink of its own.

  **Two residuals, stated rather than implied.** `Read` is not path-scoped: the
  classifier can open any file in the worktree, so "one dispatch, one block" is
  a claim about what the dispatch hands over and never about what the agent
  could open. What bounds it is the absence of a shell and of a network tool, so
  nothing it reads leaves except through its own output, and that output is a
  closed enum, a null-or-three target, and a capped reason redacted before use.
  And nothing prevents the orchestrator from running `gh` itself and reading a
  body it was not handed: the control is that it is never handed one, which is
  construction rather than enforcement. FR-008b's second assertion checks
  payload assembly against a captured payload; no fixture proves a negative over
  a model's tool use, and this document claims none.

  **Seven fixtures, each of which can fail.** The Layer 5 carve-out FR-008c
  specifies asserts the tuple's membership exactly, each member's allowlist
  exactly, and the denials, so adding `Bash` to the classifier or adding an open
  executor to the tuple is red. The Codex parity check goes red when either
  platform's definition is absent, and the install helper's bundle-inventory
  test goes red when a shipped Codex definition is missing from the required
  set. The byproduct assertions gain a **fenced** sentinel: a corpus body whose
  fenced span carries a distinctive string, asserted absent from every file the
  run leaves and every captured argv — the span is withheld from every block, so
  the string reaches disk only if the raw observation was persisted, and writing
  the observation to a request file first is what turns it red. The transport
  assertion re-attaches FR-008b's first assertion to what the orchestrator
  actually acts on: the parse response's candidate records carry no body field,
  and adding one is red. Each candidate's block is compared byte for byte
  against the golden block for that case, so a run that forwards the raw body,
  or wraps the block in prose of its own, is red. The captured-call fixture
  derives the new inventory from the corpus — one piped parse call per run, one
  `analyst_payload` leg call per dispatched candidate, one classifier dispatch
  per dispatched candidate — and a run that shapes blocks only for amended items
  fails the count. And three malformed-record cases — a fifth class value, a
  non-null target on `answered`, a 513-byte reason — each expect a stop with
  zero rows, zero replies, and zero commits, beside a deny-set string seeded in
  a reason and asserted absent from the row, the report, and the reply with the
  placeholder in its place, which is red the moment the orchestrator uses its
  own copy.
- **FR-011**: Only the `amended` class routes into consensus. The `answered`,
  `deferred`, and `no action` classes MUST NOT invoke consensus.
- **FR-011a**: Consensus does not always return an answer, and the three ways it
  fails to MUST all land on one specified behavior. The shipped protocol raises
  its human-review outcome from each of them: all three analysts
  disagreeing after Round 2, a Round-1 escape whose Round 2 still cannot
  resolve, and an analyst that fails its single retry. Behavior does not branch
  on which occurred; only the report names it. The third is not hypothetical —
  an analyst died mid-round during this specification's own consensus.

  **No edit, no class, no sweep row.** A human-review outcome MUST NOT produce
  an artifact edit, and the comment MUST NOT be given a class. `amended` is
  wrong because no edit was resolved, and the other three are wrong because each
  asserts a disposition nobody reached. The closed set of four stands unchanged;
  this outcome does not mint a fifth. The comment therefore gets **no Feedback
  Sweep Log row**, and that is the load-bearing consequence: FR-009's skip key is
  that log's comment-id column and nothing else, so writing no row is what makes
  the comment a candidate again on the next run, after a human has resolved it.
  A row here would record the sweep's failure as its disposition and make the
  outcome permanent.

  **It surfaces in the Consensus Resolution Log instead**, one row, `Type`
  `Sweep`, its item cell naming the comment id the way FR-014 requires, its
  disposition naming the human-review outcome and which of the three ways
  produced it. The two logs differ in what they key: the Consensus Resolution
  Log is the record of consensus rounds and feeds no skip key, so a row there
  costs no idempotency. FR-014's bidirectional link degrades to one direction
  here, by design — the comment id still names the item, and there is no sweep
  row for the `CRL #` to point back from, because none was written. The row
  COUNTS toward the Round-2 escape-rate metric, for FR-014's stated reason: it
  is exactly the escape the metric exists to measure.

  **It stops the run, whether or not anything was amended.** This is the part
  that would otherwise go wrong. FR-018 proceeds when no comment was classified
  `amended`, and a human-review item takes no class at all, so a run whose only
  unresolved item was this one would read as nothing-to-act-on and walk into task
  work — the proceed-versus-stop collapse this feature forecloses everywhere
  else. A human-review outcome stops the run under FR-020, naming every affected
  comment id. When other items amended in the same run, FR-017's stop and this
  one are the same stop and produce one report, not two.

  **Other items in the batch still complete.** The shipped protocol's
  do-not-block-the-batch rule holds: items that resolved are edited, committed,
  recorded, **and replied to** normally, and the run stops after that.
  Discarding resolved work because a sibling item failed would waste consensus
  rounds that already succeeded, and the stop happens either way.

  **The stop sits exactly where FR-017's does** — after this run's rows and
  replies for every handled comment, before any task work. Saying so is what
  makes "the same stop, one report" literally true rather than approximately
  true, and it settles the sibling replies: they post. When nothing was amended,
  this stop replaces FR-018's proceed at that same point, which is the whole of
  FR-011a's effect on a run that would otherwise have continued.
- **FR-011b**: The consensus work for an `amended` item MUST be performed by
  `sweep-analyst`, a scoped agent this slice ships on both platforms, and MUST
  NOT be performed by the three shared analysts or by `consensus-synthesizer`.
  Four calls per item: three perspective calls and one synthesis call, all to
  the same definition.

  **Why a fourth analyst rather than the three that already exist.** The three
  shared analysts and the synthesizer declare no `tools:` allowlist, so each
  inherits the operator's full surface — `Bash`, `WebFetch`, `WebSearch`, and
  every installed MCP server — and under FR-011 every one of them would be
  reading reviewer-derived prose with that surface in hand. That is the F-1
  exposure named in the trust-boundary review, and this requirement is where it
  is closed rather than disclosed. `sweep-analyst` declares `tools: Read, Grep,
  Glob` on Claude Code and `sandbox_mode = "read-only"` on Codex, and denies
  `Agent`, `TeamCreate`, `SendMessage`, and `Skill`. FR-008c pins that
  allowlist as an equality, so the day someone adds `Bash` to it the suite goes
  red rather than the boundary going quiet. This is the first deterministic
  control on this path's **consumers**: FR-007e says plainly that delimiting
  and removal are model-layer controls and that nothing deterministic stands
  behind them, and that remains true of the *forwarding decision*. What changes
  here is the *consumer*. An instruction that survives the frame now arrives at
  an agent that has three read tools, no shell, no network, and no way to spawn
  anything that has them.

  **Two residuals, stated the way FR-010a states the classifier's.** First,
  `Read`, `Grep`, and `Glob` are permission-scoped and never path-scoped. A
  plugin agent cannot set `permissionMode` and inherits the parent session's,
  and the autopilot requires a permissive one, so `sweep-analyst` can open any
  file the operator's session can rather than only this repository. That is a
  sharper residual than the classifier's, because the classifier's output is a
  closed enum and a capped reason while the analyst's is up to 8192 bytes of
  prose that the run commits and pushes to a public remote, and FR-012f's
  deny-set is a secret-shaped filter rather than a general one. What bounds it
  is the absence of a shell and of a network tool, the deny-set on the
  `amendment` leg, and the human checkpoint FR-017 stops for; the shipped agent
  body MUST NOT claim a repository boundary it does not have. Second, only the
  synthesis record's `replacement` crosses a redaction leg. The three
  perspective records return `finding` prose and an `evidence` array that cross
  none, and they land in the orchestrator's context, which holds the full
  surface. The plan discloses that as an open item rather than a closed one.

  **The perspective is supplied in the prompt, so the routing table is
  untouched.** `sweep-analyst` is dispatched three times per amended item, once
  for each perspective in the closed set `codebase`, `spec-context`, `domain`.
  The perspective is a prompt input, not an agent identity; the same definition
  serves all three. The Category-Routed Dispatch table in the shipped consensus
  protocol maps a category tag onto one of the three shared analysts, and the
  sweep never emits a category-tagged unresolved item, so the table is never
  consulted and none of its rows change. The precise claim is **the routing
  table is untouched**, not that the file is: FR-014's `Sweep` value is added to
  that same file's Consensus Resolution Log `Type` column, and stating the
  narrow claim is what keeps the two from reading as a contradiction. The
  sweep's own dispatch lives in the sweep sequence inside Phase 7 of both
  phase-execution references, which is exactly where the seam sits: Clarify,
  Checklist, and Analyze reach consensus through the routing table and the
  three phase-specific flows precisely as they do today, and no edit in this
  slice reaches them.

  **Two adjacent phrases narrow with it.** FR-011 and FR-014 each called the
  sweep's consensus *category-routed*, which was accurate while the sweep
  called the shared roles. What the sweep reuses is the protocol's round
  structure, its agreement rule, and its outcomes; what it no longer reuses is
  the table that decides which shared analyst runs. Both phrases drop the
  routing qualifier and keep everything else, and FR-014's escape-rate argument
  survives the narrowing intact — sweep rows count because the same round
  structure produces them and because the input is least controlled exactly
  there.

  **Synthesis is a fourth `sweep-analyst` call, not a `consensus-synthesizer`
  call.** `consensus-synthesizer` declares no allowlist either, so routing the
  three recommendations to it would reopen F-1 one hop downstream — three
  scoped agents handing reviewer-derived findings to an agent holding the full
  surface. A boundary that holds for three calls and fails on the fourth is not
  a boundary, and the fourth call is the one that composes the edit, which is
  the most reviewer-shaped output in the sequence. The synthesis prompt
  therefore goes to the same scoped definition. The cost is stated rather than
  hidden: `sweep-analyst` carries no synthesizer role prose of its own, so the
  synthesis prompt supplies the agreement rule and the confidence vocabulary at
  the call site. In exchange the shipped synthesizer keeps its existing callers
  and its wording unchanged, which is the same trade FR-007e makes against the
  shared prompt templates — fix it locally, leave the shared surface to a spec
  that owns it.

  **Only the synthesis call returns an edit, and that fixes the call counts.**
  The three perspective calls return recommendations and nothing writable. The
  synthesis call returns the structured edit below. FR-008a's captured-call
  fixture derives its per-item expectation from that granularity — four
  `sweep-analyst` dispatches per amended item, three perspectives and one
  synthesis, and zero dispatches naming `codebase-analyst`,
  `spec-context-analyst`, `domain-researcher`, or `consensus-synthesizer` for a
  sweep item, with the three perspective values appearing exactly once each. A
  corpus case whose amended item records three dispatches is red on the count;
  one that records `codebase` twice is red on the perspective set; one that
  records a `consensus-synthesizer` synthesis dispatch is red on the identity
  assertion. The identity half is what makes the seam testable rather than
  merely asserted in prose.

  **What the synthesis call returns.** One structured record whose `edit`
  object carries three fields, fixed by `contracts/sweep-classifier-output.md`
  beside the classifier's own record:
  1. `file` — one of `spec.md`, `plan.md`, and `tasks.md` in the current
     feature directory, FR-012b's three-member set and no other value. A
     record naming any fourth path MUST stop the run and MUST NOT write, and
     FR-012b rule 2 still runs at the write regardless, because a decision made
     once upstream is not a check made at the point of use.
  2. `anchor` — a verbatim excerpt of the target file's current bytes, bounded
     at **512 bytes** by `contracts/sweep-classifier-output.md`, that MUST
     resolve to exactly one occurrence in that file. The orchestrator applies
     the edit serially, the way the shipped protocol applies every Artifact
     Edit, and that application requires a unique match. Zero matches and two
     matches are both defects and both MUST stop the run before any write, and
     so is an anchor over the cap. The cap is stated because every other string
     an untrusted-input consumer returns carries one — the `reason` at 512
     bytes and the `replacement` at 8192 — and an unbounded third would be the
     one field that could push the assembled request past the runner's 32 KiB
     string limit. Like the `replacement`, an over-cap anchor stops rather than
     being cut: a cut anchor is a different anchor, and a different anchor
     matches different bytes.
  3. `replacement` — bounded at **8192 bytes**, the one text budget this
     feature already carries rather than a third number minted here. Over
     budget MUST stop the run and MUST NOT write. This is the one place the
     sweep bounds an untrusted volume by stopping rather than by cutting, and
     the asymmetry is deliberate: FR-007g cuts because its output *is* the
     bound and a cut payload is still a valid payload, while a cut replacement
     writes half an amendment into a committed artifact. The budget binds the
     record as the analyst returned it, which is the volume control; what is
     actually written is whatever the redaction surface returns for it.

  All four stops are fixtured in the same corpus, one red case per stop: a
  synthesis response naming a fourth file, one whose anchor resolves twice, one
  whose anchor is a single byte over 512, and one whose replacement is a single
  byte over 8192. Each case is red unless the
  run stops having written nothing and having captured no `amendment` leg call
  for that item, so a stop that leaks a partial write or a redaction request
  fails as loudly as no stop at all.

  **The replacement passes the redaction surface before any write.** The
  `amendment` leg of FR-012f takes the synthesis call's `replacement`, and the
  write proceeds with the text that leg returns. No separate rule is needed for
  the reviewer-derived content inside it, because FR-012f already governs every
  byte the sweep carries outward and an amendment commit is one of its three
  outbound legs. FR-008a's per-leg capture is what pins it end to end: the
  `amendment` request MUST be byte-identical to the synthesis call's
  `replacement`, and the bytes written MUST be byte-identical to the response.
  A captured case in which the write bytes differ from the response is red,
  which is the failure a response-only corpus cannot see.

  **The `domain` perspective runs without web access, and that is accepted.**
  The shared `domain-researcher` serves that perspective with `WebFetch` and
  `WebSearch`. `sweep-analyst` has neither, and FR-008c's equality assertion is
  what keeps it that way — red the moment `WebFetch` joins the line. The trade
  is deliberate and it is the direct form of the F-1 exposure: an agent that
  can fetch a URL while reading reviewer prose turns a pasted link into a fetch
  instruction, and no in-prompt frame is a control against that. So the domain
  perspective here is repository-grounded — the constitution, the roadmap, the
  sibling specs, and the shipped references, all reachable with `Read`, `Grep`,
  and `Glob` — and it is weaker than the shared role by exactly the amount the
  network would have added. Where a genuine external question decides an
  amendment, the perspectives disagree or the synthesis cannot resolve them,
  which is the path below, and a human answers it. Stating the gap is the
  point: a later reader must not assume this agent researched anything
  off-repository.

  **The failure modes map onto FR-011a unchanged.** All three of FR-011a's ways
  of failing to return an answer still apply, with `sweep-analyst` in the place
  of the shared roles: all three perspectives disagreeing after Round 2, a
  Round-1 escape whose Round 2 still cannot resolve, and a `sweep-analyst` that
  fails its single retry. Each lands on FR-011a's human-review outcome exactly
  as that requirement already writes it: no edit, no class, no Feedback Sweep
  Log row, one Consensus Resolution Log row with `Type` `Sweep` naming which of
  the three occurred, sibling items in the batch completing, and the run
  stopping under FR-020. Behavior does not branch on which occurred; only the
  report names it. This requirement changes who performs the round, not what a
  failed round does, and restating FR-011a's outcome here in different words
  would create a reconciliation bug rather than a clarification.

**Amendment**

- **FR-012**: For each amended item, the sweep MUST apply the
  consensus-resolved edit to `spec.md`, `plan.md`, or `tasks.md`, then commit
  and push that change as **one commit per amendment**. A single run-wide
  amendment commit is not permitted: FR-013 requires each log row to name its
  commit, FR-015 requires each reply to name the amending commit, and FR-017
  reports a commit range, none of which survive collapsing every amendment into
  one blob.

  **The amendment commit's subject is fixed-shape and carries no reviewer
  byte.** It is `docs(<feature-id>): amend <artifact> for <comment-id>`, with
  no body: the scope is the feature's roadmap id in lowercase, `art-008` for
  this feature; `<artifact>` is one of `spec.md`, `plan.md`, and `tasks.md`;
  and `<comment-id>` is the id the observation carries for the comment
  amended. Every slot is an id or an enum, so no byte derived from a comment
  or a resolution reaches `git log`, and the subject is not an outbound leg
  of FR-012f because nothing in it ever passed through a reviewer. It
  satisfies the repository release-readiness title regex,
  `^(feat|fix|chore|docs|test|refactor)\([a-z0-9-]+\): .+`, which the runner
  applies to pull-request titles, so a reader who checks the subject against
  the gate this repository already runs finds it in shape. The
  captured-command fixture SC-009 rests on asserts every amendment commit's
  argv carries a subject of exactly that shape and nothing outside its slots.
- **FR-012a**: The Feedback Sweep Log and Consensus Resolution Log writes MUST
  ride a separate bookkeeping commit and MUST NOT be folded into an amendment
  commit. The ordering is forced, not stylistic: a row that names its commit
  cannot exist until that commit's sha does, so an amendment's bookkeeping
  commit MUST land after that amendment's own commit. The bookkeeping commit
  stages the workflow file path alone, never the workflow directory, and takes
  a `chore:` subject, borrowing the `Draft PR` row's staging shape and subject
  convention but not its `repair` rule: repair depends on a live witness
  independent of the record, and none is used here. FR-012's fixed subject
  does name the comment id, so `git log` could say which comment an
  unrecorded amendment belonged to, but this slice builds no repair rule on
  it: the subject says which comment, not whether that comment's row landed,
  and reading history back to decide is the detection machinery the Edge
  Cases accept the window instead of. FR-006 excludes the sweep's own reply
  from the candidate set so it cannot serve as a fallback marker, and FR-016
  forecloses thread resolution as a signal, so no repair rule is defined and
  the re-candidacy path stands. One bookkeeping commit is taken per
  amendment, not per run — a
  cadence choice, not a consequence of the ordering rule, justified
  separately: it bounds the window in which an amendment is pushed but
  unrecorded to a single item, which matters because the consensus protocol
  producing the resolved edit is not proven deterministic beyond routing and
  log aggregation, so a comment reprocessed inside that window is not
  guaranteed to resolve the same way twice.

  **The trigger is rows, not handled comments.** A run takes a bookkeeping
  commit when it wrote at least one row to **either** log, and takes none when
  it wrote none. Handled comments were only ever a proxy for that: every handled
  comment produces exactly one Feedback Sweep Log row, so the proxy held until
  FR-011a introduced a Consensus Resolution Log row with no Feedback Sweep Log
  counterpart. Stating the trigger as rows subsumes the proxy rather than adding
  a second condition beside it, so the two cannot drift apart.

  Three consequences follow, and each is a case a reader would otherwise have to
  derive. A run with zero amendments but at least one handled comment takes
  exactly one bookkeeping commit, carrying every `answered`, `deferred`, and
  `no action` row FR-018 requires. **A run that handles no comment but is
  required by FR-011a to write one or more Consensus Resolution Log rows also
  takes exactly one, carrying every such row** — that run is not the case the
  no-rows rule protects against, because comments were observed, read, and
  routed to consensus, and a row is the required output. A run that wrote no row
  to either log takes no bookkeeping commit; that is the comment-free sweep, and
  an empty commit there would record nothing.

  When one run has both handled comments and FR-011a rows, they ride the same
  single bookkeeping commit. Nothing here mints a second per-item cadence beside
  the existing one.

  The ordering rationale above does not constrain this case. It binds rows that
  name their own commit, and the Consensus Resolution Log schema carries no
  commit column at all, so there is no value that has to exist before the commit
  does.
- **FR-012b**: The three artifacts FR-012 names are the sweep's whole
  **amendment** edit surface, and that MUST be enforced rather than assumed.

  **The word amendment is load-bearing, and the check MUST be scoped to it.**
  This rule governs writes that carry reviewer-derived content into the
  planning artifacts. It does **not** govern the sweep's own bookkeeping, which
  writes the workflow file under FR-012a, FR-013, and FR-014 — a path that is
  deliberately not one of the three. An implementation that applied the rule-2
  membership test to every write rather than to amendment writes would stop the
  run on its own first log row, because the workflow file fails a three-member
  equality test by construction, and it would take FR-013's durable record and
  FR-009's skip key down with it. The two write classes are already separated by
  commit — FR-012a puts bookkeeping in its own commit, staging the workflow file
  alone, while an amendment commit stages the one artifact it amended — and that
  separation is what the check keys off.

  Two rules, at two different points, because they catch different failures:
  1. **At classification.** A comment whose requested change lies outside
     `spec.md`, `plan.md`, and `tasks.md` in the current feature directory MUST
     NOT take `amended`. It takes `deferred`, and the refused target MUST be
     named in the row's disposition and in the reply, so the reviewer learns
     their request was understood and declined rather than silently ignored.
     No new class is introduced: `deferred` already means recorded and not
     acted on now, already routes nowhere, and already stops nothing. Under
     FR-010a this rule is a **field rather than prose**: `sweep-classifier`
     returns `target` from a closed enum of these three names or null, so it
     cannot express a fourth path, and the refused target is named in the
     bounded `reason` that becomes the disposition and the reply.
  2. **At the write.** Before any amendment write, the resolved edit's target
     path MUST be checked against that same three-entry set, in code rather
     than in judgment. A target outside it MUST stop the run and MUST NOT be
     written, partially or otherwise. Reaching this check means classification
     already failed, so it is a defect report and not a routine path — which is
     why it stops rather than downgrading quietly.
  Each amendment commit MUST stage exactly the one artifact path it amended,
  never a directory, so a stray file cannot ride along on an amendment. This
  borrows the path-not-directory staging FR-012a already fixes for the
  bookkeeping commit, for the same reason.

  Rule 1 alone would be prose a mis-routed item walks past; rule 2 alone would
  turn an ordinary out-of-scope request into a stopped run. Together the
  ordinary case is handled gracefully and the defect case fails closed. Of the
  two, **rule 2 is the enforcement boundary and rule 1 is disposition**: a
  decision made once upstream is not a check made at the point of use, and only
  the check at the point of use survives a future caller that skips the
  classifier.

  This is the least-privilege half of the trust boundary: FR-005 governs
  **whose** text is acted on, and FR-012b governs **what that text can reach**.
  The repository security policy treats a write grant broader than the job
  requires as a finding in its own right, so an amendment step able to write any
  path would be one even if FR-005 never failed.
- **FR-012c**: Rule 2's comparison MUST be exact membership over resolved
  paths, never containment. Resolve the candidate target and all three allowed
  paths, then test the candidate for equality against that three-member set. A
  containment or prefix test would admit anything beneath the feature
  directory — its checklists, its contracts — which is not the stated surface,
  and prefix comparison against an unresolved path is a recurring traversal
  defect in its own right. The check MUST also reject a target that is a
  symbolic link, and reject one whose every parent up to the feature directory
  is not, following the hardening the repository's existing pre-write path
  validator already performs; that validator checks repository boundary and
  traversal safety but not job-scoped file identity, so this reuses its shape
  rather than its predicate. The feature directory MUST arrive as an explicit
  input rather than being inferred: the one inference mechanism available keys
  off a branch-name pattern that **this feature's own branch does not match**,
  so inference would resolve to the wrong specification or to nothing.
- **FR-012d**: The write-point stop MUST report under the FR-020 contract,
  naming the defect — the refused target and the comment id — and the resume
  path, which is to fix the classification and re-run. Every stop this document
  defines names a report; one that halted without one would read as a bare
  failure beside them.

  The `deferred` reply for rule 1 MUST NOT imply future action. This document
  elsewhere requires deferred work to name a follow-up owner, and rule 1 has
  none: the request is declined, not scheduled. Word it as recorded and not
  acted on, with the target outside the sweep's edit surface.
- **FR-012e**: The push is part of the amendment step, not a step after it, so
  an amendment whose commit succeeded and whose push failed MUST have a
  specified outcome. It is a different failure from the one under Edge Cases:
  there, the amendment reached the remote and its bookkeeping never did; here,
  the amendment never reached the remote at all, and the local branch carries a
  commit the pull request has never seen.

  **The run stops immediately, before that amendment's bookkeeping commit is
  taken**, under FR-020, naming the unpushed commit's sha and the comment id.
  Ordering does the work: FR-012a already fixes the bookkeeping commit after the
  amendment's own commit, so stopping between them means no log row is written
  and — because FR-015 gates replies on bookkeeping commits having landed — no
  reply is posted.

  **The local commit stands and MUST NOT be unwound.** The edit is correct work
  that consensus resolved; discarding it would throw away a completed round to
  tidy a state that is already recoverable. Recovery follows the path Edge Cases
  already accepts, reached by a different route: no row means FR-009's skip key
  does not see the comment, so it is a candidate again next run, and the fresh
  consensus round either recognizes the artifact already carries the edit and
  classifies it `answered` or `no action`, or amends again and stops for
  re-review under FR-017. Per-amendment cadence bounds the exposure to one item,
  exactly as FR-012a intends it to. No new detection machinery is defined, for
  the reason FR-012a gives: there is no witness independent of the record to
  corroborate against.

  **A bookkeeping commit whose push fails stops the run the same way**, and
  differs in one consequence worth stating. Its row is already in the local
  workflow file, and the sweep reads that file locally, so FR-009's skip key
  **does** see the comment on the next run and skips it. The reply is what would
  otherwise be lost, and FR-015b's reconciliation rule is what recovers it.

  **No automatic retry.** A failed push stops and the operator re-runs, matching
  the resume path FR-019b fixes for a tool that could not be reached. Retrying
  inside the run would multiply the window in which an amendment is pushed but
  unrecorded, which is the window FR-012a's cadence exists to bound.
- **FR-012f**: FR-012b bounds **where** an amendment writes and nothing bounds
  **what** the sweep carries outward. Three writes leave the run: an amendment
  commit pushed to a public repository, a bookkeeping commit carrying the log
  rows, and a public reply. The files the sweep writes for its own transport
  are not a fourth, because FR-004d keeps them in a directory that ignores itself in any repository and
  removes them before the run ends; the amendment commit's subject is not a
  fourth either, because FR-012 fixes it from ids and enums alone, so no
  reviewer byte reaches it. Every one of the three is prose the sweep composed
  from a reviewer's comment and an analyst's recommendation, so every byte in
  either already has a complete outbound path. Before each is written, its
  text MUST pass through one redaction surface, and the write MUST proceed
  with the text that surface returns. This requirement prevents no write and
  discards nothing, and it runs after classification on every leg, so it
  touches neither the class nor the skip key. What it does once every write
  has landed is stated below, under **Any event stops the run after
  publication**.

  **Why redact rather than refuse.** A refusal at the commit would be a denial
  of service on ordinary input. FR-013 puts reviewer-derived prose in the
  `Disposition` cell, and the Assumptions name quoting — a reviewer relaying a
  bug report, a stack trace, an issue excerpt — as the expected route for
  untrusted text, so a pasted `Authorization` header in a disposition is
  ordinary reviewer input rather than an attack. FR-012a then batches every row
  of a zero-amendment run into one bookkeeping commit, so refusing that commit
  over one cell discards every row in the run, FR-009's skip key sees none of
  them, and the next run regenerates the same disposition and refuses again.
  That is a permanent livelock, and no operator action short of hand-writing
  the rows breaks it. Replacing the span and writing the row keeps FR-006c's
  invariant intact, which is the whole of convergence; SC-013 measures it.

  **What redact-and-proceed publishes that refuse-and-stop would not.** The
  choice above is a trade, and its cost is stated here rather than left to be
  found. A rule replaces its span and nothing beside it, so everything around
  a hit is committed, pushed, and posted: for `bearer_token` and
  `assigned_token` the rest of the hit's own line, and for every rule the
  neighbouring lines of the same text. Take the relayed bug report the
  Assumptions call ordinary reviewer input — a 401 against an internal vault
  host, quoted with its header: the token is replaced, and the hostname, the
  path, the service account, and the rotation date publish beside the
  placeholder. The surface does not catch a password written in prose, a
  connection string, an internal URL or hostname, an account name, a value
  split across a line break, an encoded value, or a key body whose header was
  omitted; the paragraph **What the rules still miss** below records the
  rule-level residuals, and nothing in this requirement narrows either list.
  Under refuse-and-stop none of those bytes reaches the remote; under this
  requirement they reach it before any human reads them, and the stop under
  **Any event stops the run after publication** is what puts a human in front
  of the result afterwards, not before.

  **The surface.** It is a second named surface of the `sweep-pr-feedback`
  operation, beside the write-point path check FR-012b rule 2 runs through, and
  it MUST NOT become a second registered operation. It takes three inputs — a
  `leg` from the closed set `amendment`, `log_row`, `reply`, `analyst_payload`,
  of which the first three are this requirement's outbound legs and the fourth
  is FR-007g's inbound one; the originating comment id; and the text as an
  array of lines — and returns the transformed lines plus a report: one event
  per redaction, each naming the rule and the line it fired on, and never the
  bytes it replaced. The shape and the leg values are fixed here; the field
  names settle with the contract at Plan. The text arrives as lines rather than
  as one string because the runner's bounded-input limit is enforced per
  string, and a line is the unit the bound below is defined over. **One line in
  is one line out**: every input line maps to exactly one output line, so a
  caller writes the result back where the input came from without re-aligning
  anything. The surface validates the leg against its closed set, requires a
  non-empty comment id, and requires an array of strings on an outbound leg;
  anything else returns `invalid_input`.

  This widens nothing FR-008b guards. FR-008b's first assertion is that the
  **parse** envelope carries no body, and mechanism 1's guarantee is that
  **candidate records** carry no body; both stand, because this is a different
  named surface with its own request and response. The helper remains
  networkless and write-less, so handing it one text at a time, after
  classification, gives it nothing it can do with that text except return it.
  FR-007g's inbound shaping runs on this same surface, on the `analyst_payload`
  leg, with the body as one string and the parse's own record beside it; that
  leg is FR-007g's to define, and the deny-set below never runs on it.

  **Six hit classes and no more.** Five are the secret-shaped deny-set; the
  sixth is a length bound. Each names the span it replaces, because a rule that
  named a match but not a span would leave the value beside it standing.
  1. **The bound runs first.** A line longer than **8192 bytes** as UTF-8 is
     `over_bound_line`: the whole line is replaced, and it is never scanned,
     never truncated, and never split. The figure is the one `data-model.md`
     and the contract fix for a comment body — FR-008 requires a budget and
     names no number — reused so the feature carries one number rather than
     two. Replacing whole rather than cutting is deliberate: a cut could carry
     a secret past the scan, and scanning only the head fails open on the
     tail. Two costs on the amendment leg follow and are accepted: a
     legitimate single-line rewrite that crosses the bound — `tasks.md`
     already carries task lines several kilobytes long — lands as the
     placeholder, committed and pushed, and is restored by hand at the FR-017
     stop from the resolution text; and in the pushed-but-unrecorded window a
     redacted amendment never reads as an artifact that already carries the
     edit, so the fresh round lands a second placeholder commit before that
     stop.
  2. **The deny-set**, applied after the bound in this order, every
     non-overlapping occurrence left to right. Every rule requires a value
     beside its trigger and never fires on a name, a phrase, or a quoted
     header alone, which is why this specification's own prose about the rules
     matches none of them; a fixture scans all seven feature documents to
     prove it.
     - `private_key_header` — a line that is **exactly** a PEM header and
       nothing else: `-----BEGIN `, optionally a run of uppercase letters,
       digits, and spaces ending in a space, then `PRIVATE KEY-----` or
       `PRIVATE KEY BLOCK-----`, case sensitive, with nothing on the line but
       the header and surrounding whitespace. One rule covers the OPENSSH,
       RSA, EC, DSA, PKCS#8, and PGP headers without enumerating them, and a
       header quoted inside a sentence, inside backticks, or beside other text
       is not the line and matches nothing. **Its span is multi-line**: from
       that line through the first later line that is exactly the matching
       `-----END` form, or to the end of the text when none is, every line of
       the span becoming the placeholder. A header alone would leave the key
       body it introduces standing beneath a placeholder.
     - `aws_secret_key` — a key name beginning `AWS_SECRET`, case-insensitive,
       continuing through any run of letters, digits, and underscores;
       optional spaces or tabs; `=` or `:`; optional spaces or tabs; an
       optional single `"` or `'`; then a **token-shaped run**. The span is
       the run alone. The name by itself — in a sentence, a heading, or this
       bullet — matches nothing, because the rule requires the value that
       matters, and the credentials-file form `aws_secret_access_key = …` is
       why the name is case-insensitive.
     - `aws_access_key` — the same shape with a name beginning
       `AWS_ACCESS_KEY`; the same span.
     - `bearer_token` — `bearer`, case-insensitive, then one or more spaces or
       tabs, then a token-shaped run; the span is the run alone, and the rest
       of the line publishes, as **Why redact rather than refuse** states.
     - `assigned_token` — a name of one or more characters from `A-Z0-9_`
       ending `_TOKEN`, immediately followed by `=`, then an optional single
       `"` or `'`, then a token-shaped run; the span is the run alone. A
       placeholder value needs no exclusion list: `${{ … }}` and `<…>` begin
       with a character outside the run's class, and a row of `x`s carries no
       digit, so none of them is a run.

     A **token-shaped run** is twenty or more consecutive characters from
     `A-Za-z0-9._~+/=-`, extending to the first character outside that class
     or to the end of the line, **at least one of them a digit**. The length
     floor keeps the phrase "bearer token" out; the digit keeps `bearer
     authentication_credentials` and a row of `x` placeholders out, since a
     word is not a token; and the class keeps every placeholder shape out,
     because `$`, `<`, and `{` begin none of its runs, so
     `${{ secrets.RELEASE_PLEASE_TOKEN }}` and `<your-token>` never match. A
     bare reference to `GITHUB_TOKEN` still matches nothing, because the
     assignment is required. A GitHub node id **is** a token-shaped run —
     twenty or more characters from the class with a digit among them — and
     it matches nothing for the same reason: no trigger precedes it. The rules
     fire on the trigger, never on the run alone.
  3. **The bound runs again, on the same pass.** A placeholder can be longer
     than the span it replaces — `[redacted: bearer_token]` is 24 bytes for a
     20-byte run, and the `aws_*` and `assigned_token` placeholders are 26 —
     so a line that arrived under the bound can leave over it. After the
     deny-set has run on a line, the surface measures the output line against
     the same 8192 bytes, and a line that grew past it takes
     `over_bound_line` whole, with the deny-set event and then the bound event
     both reported on that line. This is what makes the next paragraph's
     claim true at the boundary and not only away from it.

  **The placeholder is `[redacted: <rule>]`**, with the rule name from the
  closed set of six and nothing else, so it carries zero reviewer bytes,
  contains neither a pipe nor a newline, and matches no rule. With step 3 in
  place the surface's first-pass output is a fixpoint by construction: every
  output line is either under the bound with placeholders where its spans
  were — and a placeholder begins and ends with a bracket outside the run
  class, so it can join no run beside it — or it is the over-bound
  placeholder alone. Run on its own output the surface returns that output
  unchanged with zero events, and a fixture asserts so at the boundary as
  well as away from it: an 8189-byte line ending in a bearer hit returns the
  `over_bound_line` placeholder, and that placeholder fed back returns
  unchanged. Replaced spans are never rescanned.

  **What the rules still miss, stated so nobody later treats this as coverage.**
  **It is not a secret scanner, and both phase-execution references say so in
  those words**; a test greps them for the phrase and fails on any occurrence
  outside that denial. It is line-anchored and literal, so a value split
  across a line break, an encoded value, a key body whose header was omitted,
  and `AWS_` and `SECRET` on adjacent lines all pass. The value-required
  rules add residuals of their own: a prose run after `bearer` that happens
  to carry a digit, such as `authentication_credentials_v2`, is redacted; a
  genuine token with no digit is missed; a token carrying a character outside
  the class is cut short at that character, so the rest of it passes; a key
  name on one line with its value on the next matches nothing, because
  trigger and run must share a line; and a PEM header with anything else on
  its line is not a header line and passes, together with the key body
  beneath it. A header on a line of its own inside an amendment — an example
  in a fenced block, say — opens a span to the END line or the end of that
  text, which is the rule working as written; the corpus scan pins that no
  feature document carries one today. It catches the paste nobody thought
  about on the way out; FR-005 is still the boundary, and this is the last
  gate rather than the first.

  **Three legs, and where each is called.**
  1. **Amendment.** After consensus resolves the edit and before the
     orchestrator writes it, the text the edit **introduces** into the artifact
     — the replacement or inserted lines the orchestrator is about to write —
     passes through the surface, and the orchestrator writes what comes back,
     stages the one path, commits, and pushes exactly as FR-012 and FR-012b
     require. Only text the edit authored is ever passed: never the file around
     it, and never a diff read back from the worktree, so a context line or a
     removed line cannot reach the surface because no diff exists to carry one.
     This requirement therefore reads no staged path list back; FR-012b's
     single-path staging rule and the `git add -A` hazard the plan flags remain
     the controls on what a commit stages, and they remain prose. A redacted
     amendment is still an amendment: FR-017 stops the run for re-review, so
     the placeholder in the committed text is put in front of a human before
     task work continues; the stop enforces no reading, its resume path is a
     re-run, and the post-publication stop below is that same stop and that
     same report.
  2. **Log row.** The cells the sweep fills with prose rather than an id, an
     enum, a sha, or a count — the Feedback Sweep Log `Disposition` cell, the
     disposition text of the Consensus Resolution Log row FR-014 and FR-011a
     write, and that row's item cell, which names the comment id and then
     summarizes the item in prose the way every shipped row does — pass
     through the surface **before** FR-013's pipe and newline escaping, **one
     call per cell**. An amended item therefore makes three calls on this
     leg, a human-review item two, and any other class one, and FR-008a's
     captured-call fixture counts them. Redaction can remove a pipe only by
     replacing a whole line, which the bound and the key-header rule do, and
     never adds one, and the placeholder contains neither, so escaping never
     splits a placeholder and `CRL #` stays in its column.
  3. **Reply.** The filled reply body, marker included, passes through the
     surface before it is written to the file FR-004b passes by path. The
     marker survives by construction, and the reason is where it stands, not
     what it carries: the comment id in it **is** a token-shaped run — a node
     id such as `IC_kwDOKQ7tDs5vXkZ9Aq` is twenty-plus characters from the class
     with digits among them — and what keeps every rule off it is that FR-015
     puts the marker alone on line 1. That line is far under the bound, and no
     deny-set trigger — a PEM header, an `AWS_` key name, `bearer`, `_TOKEN=`
     — appears on it, so no within-line rule fires; `over_bound_line`
     replaces only the line it measured, and `private_key_header`'s span runs
     forward from its own header line, so neither reaches line 1 from a hit
     on line 2 or later. An over-bound disposition therefore costs line 2
     onward and never the marker: FR-006 still excludes the reply, FR-015b
     still reads its id, the work set does not grow, and the reply is not
     posted again. A fixture passes the marker line alone through the `reply`
     leg and asserts it returns unchanged with zero events, and it can fail,
     because the id is token-shaped: a rule loosened to fire without its
     trigger would redact it.

  **Any event stops the run after publication.** A run in which the surface
  fired on any leg — one event, any rule, any leg — MUST stop for re-review
  once every write the run owes has landed: after every amendment commit and
  bookkeeping commit is pushed, and after every reply is posted at the point
  FR-015c fixes. This is notification after publication, never prevention.
  The redacted reply is already on the pull request and the redacted row is
  already on the remote when the stop fires; what the stop adds is a human
  reading the report before task work starts, which is the reader the proceed
  path otherwise has nowhere to require. The stop is a ninth FR-020 condition
  and the second that is not a failure. It reuses FR-017's report shape — the
  comments swept, the amendments made, the commit range — with, per affected
  comment, the leg, the rule, and the count, and its resume path is re-run.
  When FR-017 or FR-011a also holds, the conditions are one stop and one
  report, as FR-020 requires. When nothing was amended, this stop replaces
  FR-018's proceed at that same point, the way FR-011a's does. It sits after
  the reply point, so FR-015c's list of stops that post replies grows by
  exactly this one and its list of stops that post none is untouched. It is
  convergent: the rows exist and the replies exist, so the next run skips
  every affected comment under FR-009, finds zero new work, fires no event,
  and proceeds. SC-013 sees a clean terminal state, and T084's re-run case
  asserts it.

  **The run report carries the event, never the match.** The run report every
  run produces (FR-018a) names, per affected comment, the leg, the rule, and
  the count, and nothing else about the match. It MUST NOT carry the matched
  line, an excerpt of it, a redacted or truncated copy, or any encoded form of
  it, and neither may any log row, any reply, or the surface's own report. The
  report's sink is the operator's, as FR-018a states, and the rule holds there
  too: a report that quoted the match to be helpful would hand the operator
  the secret the redaction kept out of the pull request, inside a report whose
  every other line names public state. The disposition the report carries per
  comment is the string the `log_row` leg returned for that comment's
  `Disposition` cell, before FR-013's escaping, never the orchestrator's copy
  from before the call; FR-008a's captured-call fixture asserts the two are
  byte-identical, so the report can never carry more than the committed row
  does. This extends FR-008b's first assertion — no body in the parse's
  output — to the matches themselves. The placeholder in the written text is
  the in-place evidence; the report is the index to it.

  **The runner's bound still sits above the surface's, and the surface's
  bound makes it unreachable.** The runner rejects any single string over 32
  KiB at the framework boundary, before the surface runs, with a field name
  and no comment id. No line needs to get there. For any line over 8192 bytes
  the surface's output is the `over_bound_line` placeholder, and nothing past
  byte 8193 can change that: byte 8193 is what proves the line is over, and
  an over-bound line is never scanned. Cutting such a line at the first
  character boundary at or past byte 8193 before transport is therefore
  outcome-equivalent — the same placeholder, the same one event, the same
  report — and the orchestrator cuts there. No line is ever split, so one line
  in is still one line out. The cut is orchestrator prose, and two fixtures
  bound it from both sides. On the surface, a 9 KB line and the same line cut
  to 8193 bytes return byte-identical output and a byte-identical report. At
  the runner, a request carrying a 33 KiB line returns `invalid_input` naming
  the field, which pins the failure shape a skipped cut produces: loud, at the
  boundary, before any write, rather than a line that reached the remote
  unscanned.

**Durable record**

- **FR-013**: The sweep MUST write one Feedback Sweep Log row per handled
  comment, carrying comment id, surface, author, class, disposition, and
  commit. A comment is **handled** when it was assigned a class under FR-010,
  which is the definition every "handled" in this document carries. It excludes
  a comment the trust filter or the self-reply rule dropped, and — since FR-011a
  — a comment whose consensus round returned no answer, because that comment
  takes no class. The term was load-bearing before it was defined; stating it
  here keeps FR-018's proceed condition and FR-015's reply count reading off the
  same set. The table sits under its own `### Feedback Sweep Log` heading
  immediately after `### Consensus Resolution Log` in the workflow file, with
  the header `| # | Comment ID | Surface | Author | Class | Disposition |
  Commit | CRL # |`. Because FR-010 puts reviewer-derived prose in the
  `Disposition` cell, that cell MUST escape any pipe as `\|` and any newline as
  a line break: the table readers in this codebase split rows on the bare pipe
  with no escape handling, so one unescaped pipe would shift `CRL #` out of
  position and make FR-014's link read the wrong column. The comment-id key
  sits ahead of the disposition and so survives regardless, which keeps FR-009
  safe. When a comment's author cannot be resolved — the account was deleted,
  and the author field is nullable where the association field is not — the
  `Author` cell records that explicitly rather than being left blank. The
  workflow file MUST be the sole store; no state-file mirror of the sweep
  record may be written.
- **FR-013a**: FR-013 says where the table sits and what it holds. It does not
  say what **creates** it, and the Edge Cases record that it does not exist
  before the first sweep, so the first run has nothing to append to. Four rules
  close that, and the first two matter most because the log is the idempotency
  key: a table created twice, or created empty, corrupts FR-009's skip key
  rather than merely looking untidy.

  **The sweep creates it.** When the workflow file carries no Feedback Sweep Log,
  the sweep writes the heading and the header row itself. It cannot come from
  the workflow template, because FR-002 forbids this feature from changing that
  template, and the template carries no such heading today.

  **Creation and the first rows are one write, in one bookkeeping commit.** The
  heading, the header row, and every row that run writes land together in the
  single FR-012a bookkeeping commit, never in a commit of their own ahead of it.
  Two writes would put a commit carrying an empty table into history, and an
  empty table is not a harmless intermediate state here: FR-009 reads a present
  log with no rows as "nothing has been handled", which is indistinguishable
  from a genuine clean first run, so a crash between the two writes would leave
  a record that lies in the one direction the skip key cannot tolerate.

  **Placement matches the anchor's level rather than assuming one.** FR-013
  places the table immediately after `### Consensus Resolution Log`. That anchor
  is **not guaranteed to exist and not guaranteed to be at that level**: of the
  69 workflow files committed in this repository, 33 carry no Consensus
  Resolution Log heading at all, and of the 36 that do, 31 write it at `###` and
  5 at `##` — including this feature's own workflow file. So the rule is: match
  the anchor by its heading text at any level, and write `Feedback Sweep Log` at
  **the same level**, so the two are siblings. When no anchor exists, append
  `## Feedback Sweep Log` at the end of the file. FR-013's `###` describes the
  common case, not an invariant, and the sibling relationship rather than the
  specific level is what Clarify session 1's additive-safety argument rests on:
  the phase-coverage guard's table reader breaks on any line beginning with `#`,
  which terminates the preceding table correctly at every level. A fixed `###`
  written under a `##` anchor would nest the sweep log inside the consensus
  section, which reads as subordinate to it and is not what FR-014's
  cross-reference describes.

  **Rows number sequentially and continue across runs.** The leading `#` column
  starts at 1 and each new row takes one more than the highest number already in
  the table, so numbering is stable under append and never restarts per run.
  FR-014's `CRL #` link points into the Consensus Resolution Log, not into this
  column, so a row number here is a reading aid rather than a key — which is why
  a simple monotone counter is enough and no durable counter is stored.

  **An inherited table is already foreclosed upstream, and the residue is
  named.** A workflow file copied from another feature would carry that
  feature's rows, and appending to them would let a foreign comment id suppress
  a genuine candidate. That case does not reach the log: FR-004 sweeps only when
  corroboration returns `match`, and a copied file's `Draft PR` row names the
  other feature's pull request, which corroborates `identity_mismatch` or
  `pr_missing` and stops the run under FR-019. The residual case is narrow — an
  operator who corrected the `Draft PR` row but left the old rows behind — and
  the sweep treats the rows it finds as authoritative rather than trying to
  attribute them. Attribution would need per-row provenance the settled
  eight-column shape has no room for, and the gate already covers the case that
  arises without human intervention.
- **FR-014**: Each amended item MUST additionally produce a Consensus
  Resolution Log row linked to its Feedback Sweep Log row. The link is
  bidirectional and costs no extra column: the sweep row's `CRL #` names the
  Consensus Resolution Log row, and that row's item cell — the column naming
  what was resolved, `Question/Gap/Finding` in the canonical header and `Item`
  or `Question` in several committed workflow files — names the comment id, the
  way existing rows already name their source label. Naming the id rather than
  only a row position keys the reverse direction on an immutable value. The
  cell carries prose after the id, the way every shipped row does, so it is
  one of the cells FR-012f's log-row leg enumerates. The row's `Type` value
  is `Sweep`, a fourth value beside the shipped `Clarify`, `Gap`, and
  `Finding`. Sweep rows COUNT toward the Round-2 escape-rate metric the log is
  the data source for: they are produced by the same round structure and
  agreement rule and can escape the same way, so excluding them would blind the
  metric
  precisely where the input is least controlled. The dispositions that could
  distort that metric — answered, deferred, no action — never reach the log at
  all, because FR-011 keeps them out of consensus. Inclusion is not the same as
  losing attribution: the `Type` column is itself the source discriminator, so
  a breach of the threshold can be attributed to sweep rows or to phase rows
  without either being excluded from the rate. A human-review outcome under
  FR-011a also writes one row here and no Feedback Sweep Log row, so the
  bidirectional link degrades to one direction on that path alone; FR-011a
  states why.

**Reviewer-facing replies**

- **FR-015**: Following a sweep run whose bookkeeping commits all landed, the
  sweep MUST post exactly one reply per handled comment. The qualifier is the
  same one SC-002 and SC-003 carry and for the same reason: an amendment pushed
  before its bookkeeping commit landed is re-processed, and the edge case that
  documents it produces a second reply on that one comment. Every reply names
  its class. **Only an `amended` reply names an artifact, a section, and a
  commit**, because only `amended` routes through consensus and produces an
  edit; the other three classes have none of those to name, so requiring them
  of all four would make three of the four templates unsatisfiable. Each class
  MUST use one fixed reply template, and reply text MUST be plain,
  public-readable English. Every template MUST open with an HTML comment whose
  **prefix** is the same fixed string in every reply, which renders as nothing
  and is what FR-006 anchors its match on. **The marker is the whole of line
  1, alone**: the comment opens at position 0 and closes on that same line,
  and the disposition starts on line 2 — no class word, no disposition text,
  nothing else shares the marker's line. The placement is load-bearing, not
  tidiness: FR-012f's reply leg works per line, so a marker that shares no
  line with anything can never be inside a span, and a fixture there asserts
  the marker line passes every rule unchanged. The prefix is what is fixed,
  not the whole comment: FR-015b appends the answered comment's id after it,
  so two replies are not byte-identical to each other. Saying "the same fixed
  marker" without that distinction would contradict FR-015b.
  A marker rather than a visible sentence, because a visible sentence is
  exactly what a reviewer quotes when they disagree, and quoting it would make
  their genuine objection invisible to the next run. The repository already
  treats HTML-comment markers in author-facing pull-request text as contract
  rather than convenience, so this reuses a shipped idiom under a distinct
  name that no existing reader matches.

  **The reply tells the reviewer what the sweep did not read.** Every
  template carries one more fixed-shape line, the last line of the reply,
  present only when the parse reported that comment `truncated` or its
  analyst-payload report carries `spans_withheld` above zero: `Body truncated
  at 8192 bytes; N spans withheld.`, with `N` the report's `spans_withheld`
  count — zero for a comment never routed to consensus, which has no such
  report — and nothing else in the line. It passes through the `reply` leg
  with the rest of the body and matches no rule. SC-008 fixes the pull
  request as the place a reviewer learns what happened, and the disposition
  cell sits in the workflow file that criterion says they need not open, so
  this line is the channel FR-007g needs and the cell is not: a reviewer
  whose fenced proposal was withheld, or whose comment was cut, reads so in
  the reply that answers it. The captured-command fixture asserts the line is
  present, with the report's count, in the reply for a corpus comment whose
  body truncates inside a fence, and absent from the reply for a plain body.
- **FR-015a**: The two surfaces need different writes. A review-thread reply is
  posted into its thread. The pull-request conversation has no threading, so a
  reply there is a new top-level comment that MUST name the comment it answers,
  keeping one-reply-per-comment legible to a human reading the conversation in
  order. Neither shipped reply-writer in this repository posts to the
  conversation surface at all, so that write is new work with no prior art to
  copy.
- **FR-015b**: A reply write can fail, and without a rule for it the failure is
  permanent and silent. The sequence is what makes it so: FR-013's row is
  written and its bookkeeping commit lands **before** any reply is posted, and
  FR-009's skip key is that row. A reply that fails after its row landed
  therefore leaves a comment the next run skips as already handled and never
  replies to, and SC-002 becomes unsatisfiable rather than merely violated. The
  failure needs no unusual conditions: FR-015a records that the
  conversation-surface write has no prior art in this repository, so it is the
  least proven write the sweep makes.

  **Replies are reconciled against the pull request, not assumed from the log.**
  Before posting, the sweep MUST determine which handled comments already carry
  one of its replies, and post only to those that do not. A comment is owed a
  reply when it is **present in this run's observation**, has a Feedback Sweep
  Log row, and carries no sweep reply answering it. On the next run this closes
  the gap; within a run it is what makes a retry safe.

  The observation qualifier is load-bearing, not throat-clearing. FR-004 reads
  only unresolved review threads, so a thread a human resolved between runs is
  invisible to the next one — both the comment and the reply inside it. Keying
  the rule on log rows alone would read that invisibility as a missing reply and
  post a second one into a thread someone had deliberately closed, turning a
  recovery rule into a duplicate-reply generator and breaking SC-002 from the
  other direction. A comment the sweep cannot see this run is not owed anything
  this run.

  **The witness is machinery FR-006 already defines.** The sweep identifies its
  own replies by the same two-condition test — the anchored marker and the
  authenticated account — and it already observes every comment on both
  surfaces, so no new read and no new record is needed. To make the
  correspondence exact rather than positional, **the fixed HTML-comment marker
  MUST carry the answered comment's id**. FR-006 continues to anchor on the
  marker's fixed prefix, which is unchanged; the id follows it inside the same
  HTML comment, so it renders as nothing and a reviewer never sees it. Without
  the id, a review thread carrying more than one comment gives no way to tell
  which one a reply answered.

  This deliberately adds no column to the Feedback Sweep Log, whose shape is
  settled, and writes no state mirror, which FR-013 forbids. It also does not
  contradict FR-012a's finding that no witness exists for the bookkeeping
  window: there, the question is which comment an unrecorded amendment belonged
  to, and no reply exists yet to answer it; here, the question is whether a
  reply exists, and the reply is its own direct evidence.

  **A failed reply is reported and does not by itself stop the run.** It MUST
  appear in the FR-018a run report naming the comment id and the surface, so a
  lost reply is visible rather than silent. It does not stop, and the
  distinction from FR-004c is principled rather than convenient: an observation
  that failed means the substantive work never happened, while a reply that
  failed means the work landed and only the notification did not. Stopping task
  work over an undelivered notification that the next run re-sends would let
  flakiness in the least-proven write block a run whose every durable record is
  correct.

  **Per-comment granularity handles the split-surface case.** A run where
  replies post on one surface and fail on the other is many per-comment
  failures, not a distinct condition: each comment is owed a reply or is not,
  and the reconciliation rule reads the same on both surfaces.
- **FR-015c**: **When** replies are posted MUST be fixed, not left to the
  implementation. Two orders are defensible — one reply immediately after each
  amendment's own bookkeeping commit, or all replies once at the end of the run
  — and FR-003 requires both platform variants to produce identical behavior for
  the same input, which two orders cannot.

  **The rule: replies post once, at the end of the run, after every bookkeeping
  commit this run takes has landed.** No reply is posted before that point. This
  is what FR-015's qualifier already says, read literally — "a sweep run whose
  bookkeeping commits **all** landed" is scoped to the run, not to the item — and
  it is restated here as an ordering requirement because FR-012a's per-amendment
  cadence describes a repeating commit sequence, and a reader can carry that
  cadence into the replies without noticing FR-015 does not.

  **This is what makes the interrupt windows compose.** Take the case the two
  earlier passes each covered separately but never together: a run amends three
  items, the first two commit, push, and record cleanly, and the third
  amendment's push fails. FR-012e stops the run before the third bookkeeping
  commit. Under the run-scoped rule the state is exact rather than ambiguous —
  two rows written, **zero** replies posted, one local unpushed commit, and no
  row for the third item. Every part of it is already covered: the first two
  comments are skipped from classification by FR-009 and owed replies by
  FR-015b, which posts them on the next run; the third has no row, so it is a
  candidate again under FR-009 and re-enters consensus. The next run reaches a
  terminal state for all three, and no rule is silent about any of them.

  Under the per-item reading the same run would leave the first two replied and
  the third not — also recoverable, but a **different** observable outcome from
  the same input, which is the thing FR-003 forbids. That is why the order is
  fixed rather than noted.

  **It also makes FR-012e's "no reply is posted" literally true.** That sentence
  is correct only under the run-scoped reading; under a per-item reading two
  replies would already be on the pull request when it claims none are, and the
  FR-020 what-landed line built from it would be wrong.

  A reply failure inside the batch is unchanged: FR-015b handles it per comment
  and it does not stop the run.

  **Which stops post replies follows from where the reply point sits, and the
  two kinds MUST NOT be collapsed.** FR-017's re-review stop, FR-011a's
  human-review stop, and FR-012f's post-publication stop occur **after** the
  end-of-run reply point, so a run reaching any of them has already posted
  every reply it owes — which is where FR-011a places its sibling replies.
  Every other stop this document defines
  aborts **before** that point and therefore posts none: an invalid
  authenticated account (FR-006b), a corroboration failure (FR-019), a failed
  observation (FR-004c), an unreadable log row (FR-009a), a refused edit target
  (FR-012b rule 2), and a failed push (FR-012e). That split is what keeps
  FR-012e's "no reply is posted" true without exception. A blanket rule that a
  stopping run first posts what it owes would contradict it directly: in the
  worked case above the two recorded comments **are** owed replies by FR-015b's
  definition at the moment the push fails, so the blanket rule would post them,
  produce two replies where this requirement fixes zero, and leave the FR-020
  what-landed line naming replies that are not on the pull request.
- **FR-016**: The sweep MUST NOT resolve any review thread.

**Stop or proceed**

- **FR-017**: When one or more comments were classified `amended`, the run MUST
  stop for re-review before any task work, with a report shaped like the
  plan-stage stop report that names the comments swept, the amendments made,
  the commit range, and states that draft pages regenerate once slice 2 lands.
- **FR-018**: When no comment was classified `amended` but at least one comment
  was handled, the sweep MUST write its records, post its replies, and proceed
  directly into task execution without stopping, unless a redaction event
  fired, in which case FR-012f's post-publication stop follows the last reply
  and the next run proceeds. When no comment was handled at
  all, it writes no rows, posts no replies, takes no bookkeeping commit, and
  proceeds. The two cases are separated so the first does not read as requiring
  an empty commit on a pull request that carried no comments.
- **FR-018a**: The run report FR-005 requires exists on **every** path the
  sweep takes, not only the stopping one. FR-017 defines a report for the
  amended path and FR-018 proceeds without stopping, which would otherwise
  leave the proceed path with nowhere for FR-005's "not swept: untrusted
  author" line to appear — and the proceed path is exactly where a run that
  swept nothing but untrusted comments lands. Every run therefore reports each
  observed comment's disposition, candidates and exclusions alike, with every
  exclusion naming its reason. Stopping and proceeding differ in what follows
  the report, never in whether one is produced. A run that observed no comments
  at all reports that, which is a one-line report rather than an absent one.

  **The report is operator-facing, and its dispositions are the redacted
  ones.** It is emitted to the sink the plan-stage stop report reaches — the
  report an operator reads to decide what to do next — in FR-017's shape,
  which is that report's shape under FR-020's three-part contract, on a
  stopping path, and on the proceed path with the per-comment dispositions
  alone, since there is no condition and no resume path to name. It is never
  posted to the pull request and never committed. Every disposition it
  carries is the string the `log_row` leg returned for that comment's
  `Disposition` cell, before FR-013's escaping, so the report never carries
  more than the committed row does; FR-012f states the rule and FR-008a's
  captured-call fixture checks it.
- **FR-019**: When a Draft PR row is present but the pull request cannot be
  read, the run MUST stop before any task work with a report naming the status
  and the resume path. That covers **four** of the six corroboration statuses
  by name: `skipped`, `pr_closed`, `pr_missing`, and `identity_mismatch`. When
  the workflow file carries no Draft PR row (`no_record`), the sweep MUST
  proceed without stopping, and on `match` it sweeps. The six are exhaustive
  and each maps to exactly one behavior.

  **Each stopping status names its own resume path**, because the four have
  different fixes and a shared wording would send the operator to the wrong one.
  `skipped`: fix the tool and re-run, per FR-019b. `pr_closed`: reopen the pull
  request, or clear the `Draft PR` row if the checkpoint is genuinely abandoned,
  then re-run. `pr_missing`: clear the `Draft PR` row, which is the one status
  where the row's absence would match reality. `identity_mismatch`: correct the
  row to name the right pull request, then re-run.

  **The sweep never writes the `Draft PR` row on any path**, including these
  stops. Clearing or correcting it is an operator action named in a resume path,
  never something the run does for itself. A run that repaired the record it had
  just failed to corroborate would destroy the evidence of the discrepancy.

  **A value outside the six is a malformed record and MUST stop**, reported as
  such rather than mapped onto one of the six. The vocabulary being exhaustive
  is a statement about what the preceding spec emits, not a guarantee about what
  this one will read: the row is text in a workflow file that a human edits.
  Fail-closed is forced here rather than chosen: exactly one status proceeds, an
  unrecognized value is not that one, and a default that proceeded would make a
  corrupted record the cheapest way past the checkpoint.
- **FR-019a**: `skipped` stops, and the distinction it turns on must be stated
  rather than left to a reader. `no_record` means the gate does not apply,
  because no checkpoint was ever opened; `skipped` means the gate applies and
  the observation failed. Treating "could not observe" as "observed nothing"
  would make the checkpoint silently optional exactly when the tool is
  unreliable, which is when unread feedback is most likely. Nothing in this
  repository treats an unreachable tool as evidence of a clean state.
- **FR-019b**: The `skipped` stop MUST read differently from the three
  discrepancy stops, and MUST name which of its causes occurred — the tool was
  absent, unauthenticated, rate-limited, or returned output that could not be
  parsed. Collapsing it into the discrepancy wording costs the operator the
  ability to tell a broken tool from a real discrepancy, and those have
  different fixes. Behavior does not branch on the cause; only the report does.
  The resume path for `skipped` is to fix the tool and re-run, because the
  observation is retaken fresh on every invocation. Clearing the `Draft PR` row
  is **not** a resume path here: that path exists for `pr_missing`, where the
  row's absence would match reality, and reusing it for `skipped` would erase a
  probably-true record to manufacture a `no_record` reading.
- **FR-020**: Every stop uses **one report contract**, with three parts: the
  **condition** that stopped the run, **what already landed** before it did, and
  the **resume path**. Stops accumulated one requirement at a time as this
  specification grew, each naming a report in its own words, and by the end no
  single place said how many there were or what they had in common. This
  requirement is that place.

  The **what-landed** part is the one that has to be stated, because it is the
  part a per-stop wording keeps omitting and the part an operator needs most: it
  names the commits pushed, the log rows written, and the replies posted so far
  in the run, so recovery starts from what is true rather than from a guess. On
  stops that occur before any write it is empty, and saying so explicitly is
  cheaper than leaving the reader to infer it.

  The complete set of stop conditions is: an invalid authenticated account
  (FR-006b), a corroboration status that is not `match` or `no_record`, or one
  outside the six (FR-019), a failed observation (FR-004c), an unreadable
  Feedback Sweep Log row (FR-009a), a consensus outcome requiring human review
  (FR-011a), a resolved edit target outside the three artifacts (FR-012b rule
  2), a failed push (FR-012e), one or more amendments requiring re-review
  (FR-017), and one or more redaction events in the run, reported after every
  write landed (FR-012f). The last two are the only ones that are not
  failures, and they use the same contract because an operator reading a
  report should not have to know which kind it is to find the resume path.

  One stop needs more than the shared contract. A human-review stop (FR-011a)
  MUST name both operator actions FR-006c identifies — resolve the substance and
  re-run, or resolve the thread — because it is the only stop whose resume path
  is not satisfied by re-running.

  Two stops MUST NOT produce two reports. When several conditions hold in one
  run — most commonly a human-review item alongside a completed amendment — the
  run emits one report naming every condition. FR-018a's per-comment
  dispositions appear in that same report rather than in a second one, so every
  run produces exactly one report on every path, stopping or proceeding.

### Reviewability Notes *(if applicable)*

- No typed reviewability exception is claimed for this slice. Typed exceptions
  are rare operator-owned overrides. Accepted classes are refactor, infra, and
  upgrade, but generated templates, generated zones, `.process` files, PR
  bodies, and code fences are not valid provenance.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter — the deterministic comment-parse
  behavior and its unit coverage.
- **Secondary surfaces, if any**: docs/process — both phase-execution
  references, the workflow-file protocol entry for the Feedback Sweep Log, and
  the two sweep agent definitions on both platforms, which are authored role
  prose the harness reads rather than a second executable surface.
- **Projected reviewable LOC**: **515 to 830, midpoint near 630, superseded.**
  That is the plan-time figure as the error-handling pass left it, kept as
  history. The live figure has one home, the second superseding note below, and
  every
  other site — `plan.md` Technical Context and its budget-result table,
  `tasks.md`, and the workflow file's Phase 5 fallback evidence chain — either
  repeats that figure or says it is superseded and points there. The bullets
  below record how the plan-time number got where it did, because the low end
  and the midpoint did not move between Plan and the error-handling pass and
  only the high end did.

  Plan derived 515 to 745 by hand from its Declared File Operations block, and
  that **corrected an earlier estimate in this section upward** rather than
  confirming it. Two anchors in that earlier estimate were measured against the
  wrong precedent: the parse was sized against a 35-line function body when the
  comparable behavior — closed vocabulary, record builder, observation
  validators, classifier — is 162 lines in this codebase's style, and a
  protocol entry was allowed 15 to 25 lines when the only comparable shipped
  entry is 58. The trust-boundary requirements added after that correction moved
  the high end to roughly 775, and the error-handling pass moved it again to the
  810-to-830 recorded in the next bullet but one.
- **Projected production files**: **7 at plan time, 12 live.** Not the 8 or 9 an
  earlier draft of this section carried, and not the 11 the consumer-scoping
  pass first projected: the closed Codex agent inventory in the install helper
  forces a line into a shipped production file, so the two sweep agents cost
  five production paths rather than four. The second superseding note below
  carries the live count and the block it crosses. The plan-time 7 held because
  neither `SKILL.md` is edited at all: the Codex variant sits three words below
  its 8000-word cap, so it cannot take a line, and the Claude variant is left
  alone to keep the two in step. That is still true, and neither `SKILL.md` is
  among the twelve.
- **The error-handling checklist moved this again.** Five more requirements put
  the high end at roughly **810 to 830**, which **crosses the 800 block**. The
  midpoint of about 630 does not. This is the fourth revision of the number and
  every one has been a hand estimate, because no code exists yet to measure.
  Superseded; the live figure is in the superseding note below.
- **Superseding note: the live figure, and its only home.** The plan-time
  range in the bullets above is left as written because it records what was
  true when those bullets were. Two later passes moved it. The artifact
  verification repair recorded in the workflow file added 80 authored lines to
  the two phase-execution references, for **595 to 910**. The trust-boundary
  remediation then made two requirements into helper code rather than prose,
  and the delta below is derived from that code, not from the prose estimate it
  replaces. **FR-012f** and **FR-007g** share one named surface of
  `sweep-pr-feedback` that takes one body and a comment id and returns the
  transformed text with a report. Its line items, in this codebase's
  comment-dense style: the five deny-set patterns with the tightened
  `bearer_token` and `assigned_token` forms, and the in-place replacement loop
  with its over-bound line class, **30 to 45**; truncation at the budget, the
  single left-to-right span scan with its bounded placeholder, and delimiting
  under the comment id label, **40 to 60**; the surface's input validation,
  report assembly, and dispatch inside the existing operation, **15 to 25**;
  and the orchestrator half in both phase-execution references — the four
  legs' call sites, the report line, and the disposition line — **25 to 40**,
  with the Codex mirror at roughly 70% of the Claude text. Fixtures and test
  assertions are authored but are not reviewable LOC, matching the plan's
  derivation table, which counts production paths only. The disclosure and
  wording siblings — the plan's seventh trust-boundary item, the quoting note
  in Assumptions, the delimiting reword, and the adaptive-attempt line — add
  **zero**, because none of them is implementation. The delta is **110 to 170
  reviewable lines**, and the live figure is **705 to 1080, midpoint near
  890**. **Production files are unchanged at 7**: every line lands inside paths
  the Declared File Operations block already names, and the surface is a
  second named surface of the one registered operation, not a second
  registration. Authored files move from 15 to **16**: FR-004d's `.gitignore`
  entry is one authored line of repository configuration, declared in the
  plan under its own category, and the gate warns strictly above 15 and
  blocks above 25, so it is a third warn and not a block. FR-004d also adds
  roughly 5 to 10 reference lines for the directory, the removal, and the
  report line; the range above is not re-derived for a delta that size, and
  the midpoint and the block crossing are unchanged by it. **The midpoint now
  crosses the 800 block, not only the high end.** T014's lever decision is
  taken against this figure, and the size-crossing rule two bullets below is
  what lets the run continue past it. This note was the live figure's only
  home; **superseded in turn by the note below, which is now the live figure's
  only home.**
- **Second superseding note: the consumer-scoping pass, and the live figure it
  leaves.** The note above is left as written; this one supersedes it, and
  supersedes nothing else. The operator chose to mitigate F-1 and F-2 inside
  this slice — recorded as Q13 in the design concept and as an amendment in the
  workflow file — rather than accept them as disclosed or move them to a later
  slice. Two agents that read reviewer text ship on both platforms and are used
  only by this sweep, and the Layer 5 no-allowlist rule gains a two-name
  carve-out. The delta is derived from the shipped agent definitions this
  repository already carries, not from a prose estimate. Its line items, each
  against a measured anchor:

  The Claude classifier definition, **80 to 120**. The narrowest shipped
  read-only agent definition is 123 lines; this role is narrower still — one
  sanitized block in, a four-field record out — but carries the same mandatory
  pointer block Layer 1 requires of every agent on both runtimes: the
  capability-discovery pointer, the grounding pointer, and a capability-path
  line.

  The Claude analyst definition, **110 to 150**. The two comparable shipped
  analysts are 135 and 144 lines; this one carries three perspectives selected
  from the prompt, a synthesis mode, and the structured edit's shape.

  The two Codex mirrors, **70 to 110** and **100 to 135**. Agent definition
  mirrors run at roughly **90%** of their Claude counterparts — 123 against
  135, 112 against 123, 121 against 135 — and **not** at the 70% ratio that
  holds for the reference documents. Using 70% here would undercount by about
  forty lines, which is why the ratio is stated rather than reused.

  The install helper's closed Codex agent inventory, **2 to 4**. Two names into
  a tuple whose loader rejects both a missing and an unexpected definition. The
  precedent added one such name in one line.

  The Claude phase-execution reference, **30 to 60**, net. The classifier
  dispatch per candidate, `sweep-analyst` three times plus a synthesis call per
  amended item, and the piped transport. This is stated net of displacement
  rather than silently offset: it **replaces** the orchestrator
  classification-loop prose and the category-routed dispatch instruction that
  the 705-to-1080 figure already carried.

  The Codex phase-execution reference, **20 to 45**, at the measured 70%
  reference ratio.

  The redaction surface's host file, **5 to 15**. The classifier's bounded
  `reason` crosses FR-012f's `log_row` leg before the orchestrator acts on it,
  which reuses an existing leg rather than adding a fifth, and lands in a file
  the Declared File Operations block already names.

  **Three things in this pass are authored and add zero reviewable LOC**, named
  so they read as counted-and-excluded rather than overlooked: the new planning
  contract `contracts/sweep-classifier-output.md`, which fixes the classifier's
  structured record and the analyst's structured edit and follows the
  agent-contract precedent in ART-007 in appearing in no count; the Layer 5
  carve-out; and the captured-call fixture extensions. The plan's derivation
  table counts production paths only and this pass is counted the same way.

  **The delta is 415 to 640 reviewable lines, and the live figure is 1120 to
  1720, midpoint near 1420.**

  **Production files move from 7 to 12, and 12 crosses the 8-file block.** The
  count is the seven already declared, plus two Claude agent definitions, two
  Codex mirrors, and the install helper whose closed inventory a new shipped
  Codex definition forces open. **Authored files move from 16 to 22**: those
  five production paths plus the Layer 5 validator, which is authored
  verification. Twenty-two is over the warn of 15 and under the block of 25, so
  the authored-file dimension stays a warn. The generated surface grows by
  thirteen paths, exactly the ripple the precedent produced for one agent,
  doubled where the agent count doubles and including the generated agents
  reference page; generated paths are not reviewable and not authored.

  **Both crossings are size-only and both are OPERATOR-ACCEPTED.** The reason is
  not that the numbers are tolerable but that the boundary is not separable
  from the feature: F-1 and F-2 are properties of the agents this feature
  dispatches, so mitigating them means shipping those agents, and a slice that
  ships the sweep without them ships the disclosed exposure and defers the fix
  behind the thing that creates it. The alternatives were offered and rejected
  on that ground, and both are recorded in the design concept's Q13. The
  precedent for a recorded block that continued is the prior spec named in the
  size-crossing bullet below, which recorded a size-only block at 1800
  reviewable LOC and continued with the crossing captured as marker-planning
  input rather than becoming a manual re-slicing stop. The live midpoint of
  1420 is under that 1800. **This note is the live figure's only home**: every
  other site either repeats it or says it is superseded and points here.
- **Budget result**: **a block on production files, a block on reviewable LOC
  at the live midpoint, and a warn on authored files.** Over the 400
  reviewable-LOC warn and the 800 block at the live midpoint of about 1420;
  over the 6 production-file warn and the 8-file block at 12; over the 15
  authored-file warn at 22 and under its block of 25; on a single primary
  surface. The file count matters more than it looks and it has now crossed:
  the block fires above 8, so the 7 this slice carried through the
  trust-boundary remediation was a warn and the 12 it carries after the
  consumer-scoping pass is a block. Both blocks are size-only and both are
  operator-accepted, per the second superseding note above.
- **A size crossing does not stop this run, and the reason is not optimism.**
  Every gate that could measure it is either advisory by contract or deferred on
  the installed runner, and the shipped rule for the ones that are deferred is
  explicit: a size-only block continues into marker planning rather than
  becoming a manual re-slicing stop. Only a **correctness** block halts. There
  is direct precedent in this repository: a prior spec recorded a size-only
  block at 1800 reviewable LOC, 2.25 times over the threshold, and the run
  continued with the crossing captured as marker-planning input. That precedent
  now covers two size-only crossings in this slice rather than one, and 1420 is
  under the 1800 it records.
- **What would actually stop a run is stale evidence, so the figure has one
  home.** Three generations of this number — 745, roughly 775, and 810 to 830 —
  were once live across the spec and the plan at the same time, with six
  separate places still asserting zero blocks, and the artifact verification
  repair's 595 to 910 then joined them. That is the condition the correctness
  stops exist for. The fix is not to erase the history but to give the live
  figure exactly one home, the second superseding note above. The
  consumer-scoping pass adds a fifth generation, 1120 to 1720, and moves the one
  home to that note. Every other site that
  states a number either repeats that figure or says it is superseded and
  points there, and a sentence claiming "that is the live figure" about any
  other number is a defect, not a lag.
- **The crossing is accepted and recorded rather than re-sliced, and each
  rejected lever is rejected for a stated reason.**
  - *Re-slice.* No split reaches 400 while still shipping a working checkpoint.
    The parse and the two phase-execution references are the irreducible core,
    and the split that would fit — records in one slice, consensus and replies
    and stop-or-proceed in another — ships a checkpoint that reads feedback and
    acts on none of it. That is the "feedback becomes decoration" outcome this
    feature exists to remove, reproduced one layer down.
  - *Defer the three serialization-family registry rows.* Rejected on
    arithmetic, not on principle: it saves an estimated 15 to 30 lines against a
    10 to 30 line overage, so it may not even close the gap, and it costs
    FR-007b's completeness guarantee and the manifest-derived parity test
    FR-008a depends on. Worth stating precisely, because it is easy to overstate
    the cost in the other direction: those three templates carry **no** prompt
    kind, so deferring them would not reopen the imperative-text exposure
    FR-007c closes. That exposure belongs to the seven templates that do carry
    one, a different set.
  - *Claim a typed exception.* Does not fit. The accepted classes are refactor,
    infra, and upgrade, and this slice is net-new feature work: a new read-only
    parse, a new phase-execution sequence, a new consensus-routed comment class.
    Ratification is a roadmap-level pragma rather than a spec-level assertion,
    and none exists for ART-008. Stretching a class to fit would be worse than
    carrying the crossing honestly.
  Re-slicing remains the operator's call, made against real numbers rather than
  a rounded-down one, and the draft pull request this stage opens is where that
  call belongs.
- **The Plan estimator cannot check this, and must not be read as if it had.**
  `estimate-reviewable-loc` projects from production files only, and it counts
  a file as production only when its path sits under `src/`, `app/`, `lib/`, or
  `scripts/`, or when it ends in a JavaScript, TypeScript, or SQL extension.
  Every path this slice touches — the runner helpers under
  `speckit-pro/speckit_pro_runner/`, both phase-execution references, both
  protocol references — matches none of those. The estimator will return a
  projection of zero and a status of `pass` no matter how large the real diff
  is. Plan MUST size this slice by hand from its Declared File Operations block
  and record that hand figure, treating the helper's verdict as an absent
  measurement rather than a passing one.
- **Split decision**: ART-008 is split into two stacked vertical slices along a
  Path seam. This spec is slice 1, the checkpoint: the comment-driven path. It
  is followed by slice 2, artifact freshness, specified separately on a branch
  stacked on this one. The estimator's `suggested_slices` was 2, and each slice
  cuts end to end through both platform variants.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Swept comment**: one pull-request comment the sweep considered. Carries its
  id, the surface it came from (review thread or pull-request conversation),
  its author association and, where resolvable, its author, whether it was
  recognized as an artifact export together with that export's form and
  template id, whether its body was truncated before matching, and its assigned
  class.
- **Feedback Sweep Log**: the durable table in the workflow file holding one
  row per handled comment. Header: `| # | Comment ID | Surface | Author |
  Class | Disposition | Commit | CRL # |`. It sits under its own
  `### Feedback Sweep Log` heading immediately after the Consensus Resolution
  Log. `CRL #` carries the linked Consensus Resolution Log row number and is
  empty for every class but `amended`. The table is the sole record of what the
  sweep has already handled and the basis for skipping on re-runs.
- **Export lead registry**: the set of sentences that identify an
  artifact-exported block, matched as a whole line within the comment's opening
  lines rather than against its first line. It covers every shipped template
  the manifest says exports, in every kind it declares, plus the empty-export
  sentences the same builder emits when nothing was recorded. Each entry
  carries its template id and kind. The set is derived from the manifest and
  the templates by a test rather than hand-maintained, so a new exporting page
  or a reworded lead fails that test instead of silently disabling
  recognition.
- **Classification**: the closed four-value vocabulary — amended, answered,
  deferred, no action — assigned to every trusted, unrecorded comment. Exactly
  one value per comment, with `amended` dominant when a single comment's
  objections would warrant different values.
- **Consensus Resolution Log row**: the existing record that already governs
  consensus outcomes. Amendments add a row here in addition to the Feedback
  Sweep Log row. The two are linked both ways: the sweep row's `CRL #` names
  this row, and this row's item text names the comment id, so the join works
  from either side and is keyed on an immutable GitHub id rather than on a
  table position alone. Sweep rows take `Sweep` as their `Type`, which doubles
  as the source discriminator for the escape-rate metric.
- **Draft PR row**: the existing workflow-file record naming the draft pull
  request, together with its corroboration status. The sweep reads it and never
  writes it.

## Non-Goals

Named owners, so none of these is a silent omission.

- **Owned by ART-008 slice 2 (artifact freshness, stacked on this branch)**:
  regenerating the whole draft page set after amendments; detecting stale pages
  from git history on a clean sweep; and refreshing the draft pull-request
  description, including the Resume block wording. Slice 1's stop report states
  that draft pages regenerate once slice 2 lands.
- **Owned by ART-010**: flipping the draft pull request to ready, and the final
  writeup.
- **Owned by the existing post-implementation loop**: remediating review
  comments left after implementation. That machinery is unchanged.
- **Deliberately not built**: resolving review threads; reading review summary
  bodies; a state-file mirror of the sweep record; a new Workflow Overview
  phase row; edits to any shipped gallery template; and edits to any of the
  twelve governed Layer 6 corpus agent definitions.
- **Owned by no spec yet, and deliberately so**: an operator flag to skip the
  sweep. Clarify surfaced the case that was missing at scoping — a fail-closed
  gate on a mandatory path normally ships with a documented override, and
  FR-019 is one. The case is real but the flag stays out of this slice: the
  resume path for every stop is to repair the tool or the record and re-run,
  the observation is retaken on every invocation, and a skip flag on a
  checkpoint whose whole purpose is to be unskippable deserves its own scoping
  rather than an addition here. No owner is named because none exists, which is
  the honest alternative to assigning it to a spec that has not agreed to it.
  The next spec to touch the sweep inherits the case rather than rediscovering
  it.
- **Owned by no spec yet**: hardening the shared consensus prompt templates so
  every caller delimits external text as reviewer-supplied data. All three of
  those templates interpolate their content raw today, with no delimiter and no
  treat-as-data instruction, and all three analyst roles describe their input by
  source rather than by trust level. FR-007e supplies that control **locally**,
  in how this slice builds its own payload, and deliberately does not rewrite
  the shared template that three other callers also use. Recorded so this
  slice's local fix is not mistaken for having closed the general case.
- **Owned by no spec yet**: extracting a reviewer's objection into structured
  fields before it reaches an analyst. The published guidance for carrying
  external text between agent steps is to forward only validated structure —
  enums, ids, checked JSON — rather than free prose, and this slice forwards
  prose on purpose. FR-007g bounds it instead of restructuring it: one byte
  budget, a fixed set of replaced spans, and an originating comment id, all
  produced by the redaction surface's analyst-payload leg, and all of it
  volume bounding and machine-span removal rather than a content control —
  an imperative written as prose reaches the analyst inside the frame, and
  FR-007g says so. The reason the stronger control stays out is the reason
  FR-007d gives for not letting recognition force a class — **the reviewer's
  argument is the payload**. An objection reduced to a class and a target path
  is the "feedback becomes decoration" outcome this feature exists to remove,
  reached by a different route: nothing would be discarded over a button
  choice, and everything would be discarded over a schema. The helper's parse
  envelope is closed-vocabulary because every field in it is an enum, an id,
  or a count, and a reviewer's reasoning is none of those; the one surface
  that returns text returns it framed as data, not parsed into fields.
  Recorded so shaping is not mistaken for structuring, and so a later spec
  that finds a structured subset genuinely worth extracting inherits the case
  rather than rediscovering it.
- **Owned by no spec yet**: a job-scoped edit-target guard on the shared
  consensus write path. The component that proposes an edit emits a free-form
  file path and nothing validates it; the three-file enumeration in the shared
  protocol turns out to be justified by write contention rather than by scope
  safety. FR-012b guards only the sweep's own caller into that path. The general
  surface predates this slice and stays open.
- **Owned by no spec yet, pending a concrete case**: which class heads the log
  row and reply when a single comment mixes only `answered` and `deferred`
  points, with nothing amend-worthy present. Neither class routes to consensus
  or changes stop-or-proceed, so the choice has no behavioral consequence and
  no owner is assigned.
- **Owned by no spec yet, and deliberately so**: qualifying `sweep-classifier`
  and `sweep-analyst` into the governed Layer 6 corpus. The two agents ship
  outside it. The corpus binds exactly twelve roles through a four-level sha256
  digest chain over agent source bytes, it has no regeneration script, and
  editing any governed definition restales the chain with an error that names a
  digest rather than a file. The `artifact-author` agent is the precedent and it
  is recent: it shipped on both platforms, outside the corpus, with a green
  suite. This entry does not disturb the **Deliberately not built** bullet above
  — no governed definition is edited here, and the twelve stay twelve; two new
  agents simply ship beside them ungoverned. The disclosure is that a security
  boundary nothing digest-binds is a gap: FR-008c pins these two definitions at
  Layer 5, which catches a widened allowlist, and Layer 6 is the layer that
  would catch a substituted definition. The destination is a future G56R-series
  spec, because corpus qualification is its own workstream with its own
  calibration run, and bolting two roles onto a hand-maintained digest chain
  inside a slice that already crosses its file budget is how that chain gets
  left broken. No spec is named because none has agreed to it, which is the
  honest alternative to assigning it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a draft pull request carrying reviewer feedback, task work
  never begins until 100% of trusted, unrecorded comments carry a recorded
  disposition.
- **SC-002**: Following a sweep run whose bookkeeping commits all landed, every
  handled comment receives exactly one reply. Across the fixture corpus, no
  handled comment has zero replies and none has two. When a reply write itself
  failed, that comment is owed a reply the next run posts under FR-015b's
  reconciliation rule, and the criterion is met across the pair of runs rather
  than within the first — the same shape of qualifier SC-003 carries, and for
  the same reason.
- **SC-003**: Following a sweep run whose bookkeeping commits all landed,
  re-running the sweep with no new comments produces zero new log rows, zero
  new replies, and zero amendments, and proceeds into task work. When a prior
  run's amendment was pushed but its bookkeeping commit did not land, the next
  run's handling of that one item is the edge case documented under Edge
  Cases, not a violation of this criterion.
- **SC-004**: Zero artifact edits across the fixture corpus are attributable to
  an author outside the write-capable set.
- **SC-005**: The same observed comment data yields the same candidate set
  **and the same returned analyst block** on every run, and the second half is
  provable for the same reason as the first: the block is produced by the
  redaction surface's analyst-payload leg, a fixture-pinned Python surface,
  rather than assembled in prose. Demonstrated by golden fixtures covering
  every registered sentence in both the verbatim and header-trimmed shapes, a
  carriage-return body, an oversized body that truncates, every excluded
  author-association value, the ordinary-comment path, and — against the
  surface's returned block and report, never against a hand-written expected
  string — a body carrying a fenced code block and one carrying an HTML
  comment, each asserting the seeded span is absent and its placeholder
  present inside the frame; the overlapping-span body, asserting the one
  block FR-007g's scan defines for it; the body truncated inside a fence,
  asserting the report and the statement line both say truncated and both
  count the one unclosed span; and every block carrying its originating
  comment id in both delimiter lines.
- **SC-006**: All four unreadable draft-pull-request conditions stop the run
  before any task work, each with a report naming the condition and a resume
  path, and the could-not-observe stop is distinguishable in that report from
  the three discrepancy stops **and names which of its four causes occurred**;
  the no-record condition proceeds. Every one of the six corroboration statuses
  has exactly one specified behavior, with none left to prose alone.
- **SC-007**: Both platform variants produce the same sweep outcome for the
  same input, with no behavioral difference between them.
- **SC-008**: After an amendment run stops, a reviewer can tell from the pull
  request alone what changed and where, without opening the workflow file.
  This rests entirely on the FR-015 replies, and deliberately so: slice 1 makes
  no write to the pull-request description, and a draft description is fully
  fingerprint-protected with no editable region, so there is nowhere safe to
  put an amendment summary there. Slice 2 owns the description refresh and MUST
  NOT weaken the replies on the assumption that the description carries this.

- **SC-009**: No comment text reaches a shell argument on any path, read or
  write, demonstrated by inspecting every command the sweep issues. This is the
  injection boundary for a feature that carries public pull-request text into
  agents that edit the planning artifacts, and it is stated as a correction to
  shipped precedent rather than a restatement of it, so it needs evidence of
  its own rather than inheriting anyone else's.
- **SC-010**: The Feedback Sweep Log survives reviewer-derived prose:
  a disposition containing a pipe and a newline leaves every later column,
  including `CRL #`, readable in its own position, and a comment whose author
  cannot be resolved still produces a complete row. Both are found-and-fixed
  defects rather than hypotheticals, which is why they carry a criterion.
- **SC-011**: No failure leaves the sweep having acted on part of the feedback
  while reporting success. Across the fixture corpus, a run that failed to read
  either surface completely writes zero rows, posts zero replies, and takes zero
  commits; every stop carries a report naming the condition, what already
  landed, and a resume path; and no path reaches task work after a stop
  condition held. This is the criterion the whole error-handling surface exists
  to satisfy, and it is stated separately from SC-006 because SC-006 covers only
  the four conditions observable at the gate, before any work has been done.
- **SC-012**: The Feedback Sweep Log's lifecycle is correct end to end. On a
  workflow file that has never carried one, the first sweep handling at least
  one comment produces the heading, the header row, and its data rows in a
  single bookkeeping commit, with no commit anywhere in history carrying the
  heading and no rows. A later sweep appends to that same table and creates no
  second one. Placement holds against a Consensus Resolution Log heading written
  at `##`, at `###`, and absent entirely — the three shapes the committed
  workflow corpus actually contains. The creation path needs its own criterion
  because every other criterion here measures rows in a table that already
  exists, and the log is the idempotency key: a table created twice, or
  committed empty, corrupts the skip key rather than merely looking untidy.
- **SC-013**: The loop provably converges. Across the fixture corpus no run
  grows the work set FR-006c defines, and the run following any single interrupt
  window — an amendment pushed without its bookkeeping row, a bookkeeping commit
  whose push failed, a row written whose reply failed — reaches a terminal state
  for every comment that window touched. The composed case is included: a run
  that records two amendments and fails to push a third leaves zero replies
  posted, and the next run posts both owed replies and re-enters consensus on
  the third. The post-publication redaction stop FR-012f defines is included
  too: the run after it finds every affected comment's row and reply in
  place, fires no event, and proceeds. Convergence was asserted by FR-006a
  before it was measurable anywhere; this is where it becomes measurable.
- **SC-014**: Nothing the sweep writes outward carries a span the deny-set
  names or a line over the per-line bound. Across the fixture corpus — each
  of the six hit classes on the amendment leg, the text an amendment
  introduces, and one seeded class carried across each of the other two legs,
  the prose cells of a log row and a reply body — the seeded string is absent
  from every captured output: the surface's response,
  the committed artifact text, the Feedback Sweep Log row, the reply body, and
  the run report; the placeholder naming the rule stands in its place; the row
  is written, the commit is taken, and the reply is posted exactly as they
  would be without the hit; and the run report names the comment id, the leg,
  the rule, and a count, and nothing else about the match. The negative half
  is measured too: the false-positive shapes FR-012f names pass through
  byte-identical with zero events, which is what makes the tightened rules
  falsifiable rather than merely narrower. The seeded string is present in the
  surface's request by construction, which is why the search runs over outputs.
  The classifier's `reason` is measured on the other side of the same boundary,
  by identity rather than by search: the reason text the orchestrator acts on,
  and the reason text it carries into a `Disposition` cell, a reply, or the run
  report, is byte-identical to the redaction surface's response for that
  reason, asserted against the captured-dispatch corpus FR-008a defines. A
  reason taken from `sweep-classifier`'s raw record — the one field where
  reviewer-derived text could re-enter the outbound path after the surface ran
  — therefore fails by comparison rather than by inspection, which is the same
  identity check FR-008a fixes for a disposition cell, applied to the one free
  text field a scoped agent returns.
  It needs evidence of its own because nothing else here measures what the
  sweep carries outward — SC-009 covers shell arguments, SC-004 covers
  authorship, and SC-011 covers atomicity — and a run that commits to a public
  repository and then posts a public reply is an outbound path none of the
  three inspects.
- **SC-015**: The agents that read reviewer text hold only what their role
  needs, and the orchestrator holds no reviewer text at all. Two measurements
  together, and the split between them is stated first because it is what keeps
  this criterion falsifiable. **The declaration is pinned by Layer 5**: each
  agent's frontmatter carries exactly its stated allowlist — `Read` for the
  classifier; `Read`, `Grep`, and `Glob` for the analyst — with `Bash`, every
  network tool, and every write tool absent from both by equality rather than
  by containment, the orchestration set and `Skill` denied, and the exempt pair
  fixed at those two names, all as FR-008c specifies. **The routing is
  measured over the captured corpus**: no dispatch carrying a block names an
  agent outside the two, and no captured orchestrator step reads a comment body
  out of the observation, which is piped into the runner rather than held for
  the orchestrator to interpret. Demonstrated by two fixtures that can fail,
  both over the capture FR-008a defines: the per-agent dispatch fixture, red
  when a block reaches a third agent or a per-agent dispatch count is wrong;
  and the orchestrator-read fixture, red when any captured orchestrator step
  carries a body rather than an id, an enum, or surface-shaped text.

  **What this criterion deliberately does not claim.** It does not assert that
  every tool call a dispatched agent made names a tool on its allowlist. The
  capture FR-008a defines records the agent name, the comment id, the prompt as
  sent, and the structured record returned; it does not record an agent's own
  tool calls, and the fixture corpus is a deterministic harness with no live
  agent in it. The repository is not blind to a dispatched agent's own calls:
  the Layer 7 transcript harness carries a `sidechain` scope and its grounding
  runner already asserts that named tools were not invoked. That instrument
  still cannot produce this claim. It records no per-agent attribution, no
  committed fixture carries a sidechain event, and the evidence would cost a
  live capture over a real pull request, so this slice does not buy it. The
  reason the claim is dropped is cost and attribution, not the absence of any
  observer. Claiming it would
  be the defect this spec names elsewhere — a rule nothing executes has no
  fixture that can fail. What stands in its place is the pair above: the
  declaration, pinned by equality in the repository, and the routing, measured
  against a run.
  **Neither half substitutes for the other.** Layer 5 would pass unchanged if
  the sequence routed a block to an unscoped role, because it never looks at a
  run; the captured corpus would pass unchanged if a definition's allowlist
  were widened, because it never looks at frontmatter. It needs evidence of its own because nothing else here measures
  the consumers' capability surface or the orchestrator's read discipline:
  SC-009 covers shell arguments, SC-004 covers authorship, and SC-014 covers
  what the run carries outward, and the failure this one guards against leaves
  no outbound artifact for any of the three to search. One honest limit is
  recorded with it: a capture records the calls a run made, and what prevents
  a denied call is the harness that spawns the agent, so this criterion
  measures the record and Layer 5 pins the declaration — neither is a proof
  that the harness enforced anything, and the spec does not claim one. That
  limit and the no-tool-call-evidence limit above are the same limit seen from
  two sides, and both are recorded rather than argued away.

  **One enforcement observation is produced, and it is named here so that
  removing it is visible.** The implementation task that ships the classifier
  runs a binding probe once, before any later work depends on the answer: the
  agent is dispatched with its pinned allowlist in a session with an MCP server
  connected, asked for a tool outside that allowlist, and the runtime's refusal
  text is recorded verbatim in the workflow file; the slice stops if either
  tool is reachable. That refusal is what tells a bound allowlist from an
  inherited one. It is a slice gate rather than a standing per-run fixture,
  which is why it stands beside this criterion rather than inside it.

  **The declaration half rests on a stated platform assumption.** Claude Code
  enforces `tools:` as an allowlist and `disallowedTools` as a denylist, so
  pinning the declaration by equality verifies the configuration of an
  enforcing control rather than a hint. A bare or emptied `tools:` inherits the
  full pool, which is why the assertion is an equality and not a containment.

## Assumptions

- The Draft PR row and its corroboration vocabulary already ship from the
  preceding spec. That vocabulary is **six** values, not five: `match`,
  `no_record`, `skipped`, `pr_closed`, `pr_missing`, and `identity_mismatch`.
  This slice reads that record and reuses the whole vocabulary rather than
  defining its own, and FR-019 assigns a behavior to every one of the six.
- SC-004's phrase "write-capable set" is shorthand for the author-association
  allowlist FR-005 defines. The association is a proxy for write access rather
  than a permissions check, as FR-005 states.
- The author allowlist and the content controls answer two different questions
  and neither substitutes for the other. FR-005 is an **authorization** gate: it
  decides who may cause the sweep to act at all, and gating elevated processing
  on the poster's standing is ordinary practice. FR-007e is a **content** control
  and stays in force regardless of who posted. Letting the first silently
  upgrade the second — treating a trusted author's relayed text as vetted
  because the relayer is trusted — is the documented failure mode behind
  real-world indirect-injection incidents, so the spec keeps the two axes
  separate on purpose.
- **The unit of trust is the comment, not the text inside it.** FR-005 is
  evaluated once per comment, against that comment's author association. A
  trusted author who quotes, pastes, or forwards text from an untrusted source
  is treated as endorsing it, and the sweep makes no attempt to attribute
  quoted spans inside a trusted body. This is an accepted residual rather than
  an oversight, and naming it is what keeps it accepted: it bounds the
  untrusted-input surface to social engineering of a write-capable account,
  which is the same bound the platform's own agent controls draw when they
  ignore events from users without write access. The expected route to that
  residual is quoting rather than a compromised account: a reviewer pastes an
  anonymous bug report, a stack trace, or an issue excerpt into a comment, and
  the rule above trusts every word of it verbatim. That is ordinary reviewer
  behavior rather than an attack, which is both why it is the likely path and
  why a content filter is a poor answer to it — relayed text arrives anchored
  to a genuine reviewer intent, with nothing anomalous in the surrounding
  comment for a classifier to key on. **The compensating control is the
  checkpoint, and the checkpoint gates merge, not disclosure.** FR-017 stops
  the run for re-review before any task work whenever anything was classified
  `amended`, and SC-001 makes that gate measurable, so an amendment that a
  quoted instruction induced is put in front of the human whose comment
  carried it before task work continues. The stop enforces no reading — a
  re-run is its resume path — and what keeps the induced amendment out of
  `main` is the pull request's draft state and a human merge action. Read the
  order: that amendment is committed, pushed to
  a public repository, and replied to on a public pull request **before** that
  human sees it. For the whole interval between the push and the re-review the
  induced content is public, in the branch history, and in a comment, and
  nothing in this slice shortens that interval. What the checkpoint controls
  is whether the content survives into the merged artifact; what it does not
  control is who saw it first. The sweep does not have to recognize a relayed
  instruction; it has to make what the instruction produced visible to the
  person who relayed it, and it makes it visible to everyone else at the same
  moment. The residual is why FR-012b constrains the edit surface, why FR-012f
  redacts secret-shaped text from the three outbound legs before they are
  public, and why FR-007c keeps a registered imperative out of an analyst
  prompt — none of the three assumes the body is clean, only that the account
  vouching for it is write-capable.

  **What the residual can produce is now bounded, though the residual itself is
  unchanged.** Laundered text still arrives, still passes FR-005 on the
  relayer's standing, and the sweep still makes no attempt to attribute it. What
  it reaches is no longer an agent carrying the operator's session. The only
  readers are `sweep-classifier` and `sweep-analyst`, each scoped to the
  read-only allowlist FR-007e states and FR-008c pins, and each receives the
  sanitized, delimited block the FR-007g surface produced rather than a raw
  body. What either returns is a structured record: a class from the closed
  vocabulary, a target from FR-012b's three-file set, a bounded reason, and a
  byte-capped replacement, each passed through FR-012f before any use. So a
  quoted instruction can no longer reach a shell, the network, or a path
  outside the three artifacts through the agent that read it; at most it argues
  for an edit inside them, in a shape a person reads at the FR-017 checkpoint.
  **None of that shortens the interval above.** The amendment is still
  committed, pushed, and replied to in public before the human sees it. Scoping
  the consumers changes what the induced content can be, not who saw it first,
  and the two are recorded separately so a later reader does not trade one for
  the other.
- A fail-closed gate on a mandatory path is normally expected to ship with a
  documented override, and this slice ships none. That is recorded as a gap
  under Non-Goals rather than resolved here, and it is explicitly **not** a
  reason to weaken FR-019: the fix for a stopped run is to repair the tool, and
  the observation is retaken on every invocation.
- The consensus machinery's **round structure, agreement rule, and outcomes**
  are reused unchanged. Its four existing roles are not: FR-011b performs the
  sweep's rounds with `sweep-analyst`, three perspective calls and one
  synthesis call, because the shared roles and `consensus-synthesizer` inherit
  the operator's tool surface and would read reviewer text with it. The
  category-routed routing table is never consulted and never edited, so
  Clarify, Checklist, and Analyze are untouched. This slice adds a caller and
  two scoped roles, not a new protocol.
- The registered sentences are stable strings on the shipped pages. Recognition
  depends on them, so a page that changes one needs its registry entry updated
  in the same change; FR-008a's parity test is what makes that failure loud
  instead of silent.
- The replies FR-015 requires are an orchestrator write, not a runner one. The
  runner's command-plan apply mode is deferred by design and returns an
  expected failure, so no part of the reply path may be built on it. That also
  means the reply behavior sits outside the runner's determinism guarantees, so
  SC-002 is provable only against a captured-command fixture rather than a
  golden helper response.
- Adding a read-only helper restales the byte-identical installed-cache copies
  of the runner sources under the test fixtures, and shipping an agent restales
  the installed-cache copies of the agent definitions on both platforms the
  same way. Regenerating them is a required step, not an optional one, and the
  plan counts those copies as generated rather than authored.
- Recognized export blocks may arrive on either comment surface. The acceptance
  runbook exercises both placements: one export pasted as a conversation
  comment, one pasted into a review thread.
- One class per comment is settled, not a working default. Recognized export
  anchors are carried as detail on that comment's record.
- The dominance rule ranks `amended` above the other three and stops there. It
  does not order `answered`, `deferred`, and `no action` against each other,
  because those three are behaviorally identical at both points classification
  controls: none route through consensus and none stop the run. The one case
  that leaves open is recorded under Non-Goals as deferred pending a concrete
  case, beside the operator-flag deferral it resembles.
- No aggregator script computes the Round-2 escape rate. The tool the design
  concept named was removed by an earlier shipped-Bash purge, and nothing
  replaced it, so the Consensus Resolution Log table is the metric's only data
  source and a reader computes it from the `Round` column and the
  `escape-hatch` outcome value.
- The deterministic parse is one read-only runner operation registered the way
  the stage resolver already is. Its exact name and field list stay a
  Plan-phase decision, but Clarify has grounded the shape: it reports the
  surfaces read, trusted and untrusted counts, per-comment candidates carrying
  the export form and its anchors, and an explicit exclusion list naming each
  excluded comment's reason. It **reports and never decides**, mirroring the
  corroboration helper: assigning a class stays orchestrator judgment, because
  `amended` is what routes an item into consensus.
- Registering a read-only operation touches seven places, three of which fail
  in ways that name a digest or a JSON blob rather than the mistake: the
  argument-derivation branch rejects a helper that adds no explicit entry, the
  harness manifest compares its helper list in order rather than sorted, and a
  helper not declared as having no shell ancestor is required to name a shell
  script that no longer exists. The remediation and rollback text in that
  manifest also may not contain the substring `bash` in any casing. Plan
  accounts for these; they are recorded here so a later reader does not
  rediscover them by failing.
- One fixed reply template per class, with the exact wording settled at Plan.
- The scoping interview's blind-spot pass did not run. Clarify session 2 did
  that search instead and it changed the spec: it found that the export lead
  does not sit on a comment's first line, that an empty export carries no lead
  at all, that the runner rejects an entire request over one oversized string,
  that a draft description has no editable region, that the runner cannot post
  the replies, and that an unescaped pipe in the disposition text would break
  the log-to-log link. Those are recorded as requirements above rather than
  left as an unsearched gap.
- Reviewers inside the write-capable set act in good faith. The author-
  association filter is the security boundary; it is not a judgement about any
  individual reviewer's intent.
- Slice 2 is stacked on this branch, so this slice's records and report wording
  are the interface slice 2 builds on.
