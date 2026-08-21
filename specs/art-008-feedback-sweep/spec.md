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

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The sweep reads and classifies draft-PR feedback (Priority: P1)

The implement stage opens. Before any task work, the orchestrator looks at the
draft pull request the plan stage left behind. It collects every review thread
still marked unresolved and every comment in the pull-request conversation. It
keeps only the comments written by accounts with write access to the
repository, and it sets the rest aside as untrusted rather than acting on them.
Among the kept comments it recognizes the ones that are artifact exports,
because those begin with one of three known sentences. It ignores anything it
already handled on a previous run, and it ignores its own replies. What is left
gets a single label each: amended, answered, deferred, or no action.

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
3. **Given** a comment whose first line is one of the three shipped export lead
   sentences, **When** the sweep runs, **Then** the comment is recognized as an
   artifact export, and **Given** a comment whose first line matches none of
   them, **Then** it is treated as an ordinary comment.
4. **Given** a comment id that already appears in the Feedback Sweep Log, and a
   reply the sweep itself posted on an earlier run, **When** the sweep runs
   again, **Then** neither becomes a candidate and no duplicate record or reply
   is produced.

---

### User Story 2 - Amendments run through consensus, get recorded, and stop for re-review (Priority: P2)

For every comment the sweep labelled amended, it hands the item to the existing
category-routed consensus machinery, applies the agreed edit to the
specification, the plan, or the task list, and commits and pushes that change.
It then writes the durable record: one Feedback Sweep Log row for the comment,
plus a Consensus Resolution Log row for the amendment. It posts one reply on
the comment saying what class it got, which artifact and section moved, and
which commit carries it. Once every item is handled, the run stops and asks the
reviewer to look again. If nothing was amended, the sweep still writes its rows
and posts its replies, then walks straight into task work.

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
   the artifact and section touched, and the commit, and no review thread has
   been resolved by the sweep.
4. **Given** at least one amendment, **When** the sweep completes, **Then** the
   run stops before task work with a re-review report that names the comments
   swept, the amendments made, the commit range, and states that draft pages
   regenerate once slice 2 lands; **Given** zero amendments, **Then** the run
   proceeds directly into task execution.

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

- A trusted comment whose first line matches a registered export lead sentence
  but whose body carries no objections: recognized as an export, but there is
  nothing to classify beyond "no action".
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
- A consensus round on an amended item that reaches no agreement.
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

**Trust boundary**

- **FR-005**: The sweep MUST act only on comments whose author association is
  OWNER, MEMBER, or COLLABORATOR. Every other comment MUST appear in the run
  report as "not swept: untrusted author", MUST NOT be passed to the consensus
  protocol, and MUST NOT influence any artifact edit.
- **FR-006**: The sweep MUST exclude replies it posted itself from the
  candidate set on every run, so a reply written by one sweep never becomes
  input to a later one.

**Deterministic recognition**

- **FR-007**: The sweep MUST recognize an artifact-exported markdown block by
  matching the comment's lead sentence against a fixed registry holding the
  three shipped export lead sentences. A comment matching none of them MUST be
  treated as an ordinary comment, and recognition MUST NOT require editing any
  shipped gallery template or its payload copy.
- **FR-008**: Candidate filtering, export recognition, and candidate reporting
  MUST be deterministic: the same observed pull-request comment data MUST
  always yield the same candidate set. That behavior MUST be pinned by golden
  fixtures covering each registered lead sentence, the untrusted-author path,
  and the ordinary-comment path.

**Idempotency and classification**

- **FR-009**: The sweep MUST skip any comment whose id already appears in the
  Feedback Sweep Log. The skip key is the log's comment-id column and nothing
  else: the log is the sole source of "already handled", so a comment absent
  from it is a candidate even when a reply to it exists on the pull request.
- **FR-010**: Every trusted, unrecorded comment MUST be assigned exactly one
  class from the closed set: amended, answered, deferred, no action. No other
  value is permitted. The comment is the unit of classification, so a
  recognized export block carrying several distinct objections still yields one
  class, one log row, and one reply; the recognized anchors are carried as
  detail on that row. When one comment's objections would warrant different
  classes, `amended` MUST win over the other three, and every non-dominant
  objection MUST be named in the row's disposition text and in the reply, so
  nothing is silently dropped.
- **FR-011**: Only the `amended` class routes through the category-routed
  consensus protocol. The `answered`, `deferred`, and `no action` classes MUST
  NOT invoke consensus.

**Amendment**

- **FR-012**: For each amended item, the sweep MUST apply the
  consensus-resolved edit to `spec.md`, `plan.md`, or `tasks.md`, then commit
  and push that change as **one commit per amendment**. A single run-wide
  amendment commit is not permitted: FR-013 requires each log row to name its
  commit, FR-015 requires each reply to name the amending commit, and FR-017
  reports a commit range, none of which survive collapsing every amendment into
  one blob.
- **FR-012a**: The Feedback Sweep Log and Consensus Resolution Log writes MUST
  ride a separate bookkeeping commit and MUST NOT be folded into an amendment
  commit. The ordering is forced, not stylistic: a row that names its commit
  cannot exist until that commit's sha does, so an amendment's bookkeeping
  commit MUST land after that amendment's own commit. The bookkeeping commit
  stages the workflow file path alone, never the workflow directory, and takes
  a `chore:` subject, borrowing the `Draft PR` row's staging shape and subject
  convention but not its `repair` rule: repair depends on a live witness
  independent of the record, and none exists here. FR-012 defines no
  commit-message convention that recovers a comment id from `git log`, FR-006
  excludes the sweep's own reply from the candidate set so it cannot serve as
  a fallback marker, and FR-016 forecloses thread resolution as a signal, so
  there is no second leg to corroborate against and no repair rule is
  defined. One bookkeeping commit is taken per amendment, not per run — a
  cadence choice, not a consequence of the ordering rule, justified
  separately: it bounds the window in which an amendment is pushed but
  unrecorded to a single item, which matters because the consensus protocol
  producing the resolved edit is not proven deterministic beyond routing and
  log aggregation, so a comment reprocessed inside that window is not
  guaranteed to resolve the same way twice. A run with zero amendments but at
  least one handled comment MUST still take exactly one bookkeeping commit,
  carrying every `answered`, `deferred`, and `no action` row FR-018 requires;
  a run with no handled comments writes no rows and takes no bookkeeping
  commit.

**Durable record**

- **FR-013**: The sweep MUST write one Feedback Sweep Log row per handled
  comment, carrying comment id, surface, author, class, disposition, and
  commit. The table sits under its own `### Feedback Sweep Log` heading
  immediately after `### Consensus Resolution Log` in the workflow file, with
  the header `| # | Comment ID | Surface | Author | Class | Disposition |
  Commit | CRL # |`. The workflow file MUST be the sole store; no state-file
  mirror of the sweep record may be written.
- **FR-014**: Each amended item MUST additionally produce a Consensus
  Resolution Log row linked to its Feedback Sweep Log row. The link is
  bidirectional and costs no extra column: the sweep row's `CRL #` names the
  Consensus Resolution Log row, and that row's item cell — the column naming
  what was resolved, `Question/Gap/Finding` in the canonical header and `Item`
  or `Question` in several committed workflow files — names the comment id, the
  way existing rows already name their source label. Naming the id rather than
  only a row position keys the reverse direction on an immutable value. The
  row's `Type`
  value is `Sweep`, a fourth value beside the shipped `Clarify`, `Gap`, and
  `Finding`. Sweep rows COUNT toward the Round-2 escape-rate metric the log is
  the data source for: they are produced by the same category-routed protocol
  and can be mis-routed the same way, so excluding them would blind the metric
  precisely where the input is least controlled. The dispositions that could
  distort that metric — answered, deferred, no action — never reach the log at
  all, because FR-011 keeps them out of consensus. Inclusion is not the same as
  losing attribution: the `Type` column is itself the source discriminator, so
  a breach of the threshold can be attributed to sweep rows or to phase rows
  without either being excluded from the rate.

**Reviewer-facing replies**

- **FR-015**: The sweep MUST post exactly one reply per handled comment, naming
  the class, the artifact and section touched, and the amending commit. Each
  class MUST use one fixed reply template, and reply text MUST be plain,
  public-readable English.
- **FR-016**: The sweep MUST NOT resolve any review thread.

**Stop or proceed**

- **FR-017**: When one or more comments were classified `amended`, the run MUST
  stop for re-review before any task work, with a report shaped like the
  plan-stage stop report that names the comments swept, the amendments made,
  the commit range, and states that draft pages regenerate once slice 2 lands.
- **FR-018**: When no comment was classified `amended`, the sweep MUST write
  its records, post its replies, and proceed directly into task execution
  without stopping.
- **FR-019**: When a Draft PR row is present but the pull request cannot be
  read — the GitHub CLI is unreachable, or corroboration reports `pr_closed`,
  `pr_missing`, or `identity_mismatch` — the run MUST stop before any task work
  with a report naming the status and the resume path. When the workflow file
  carries no Draft PR row (`no_record`), the sweep MUST proceed without
  stopping.

### Reviewability Notes *(if applicable)*

- No typed reviewability exception is claimed for this slice. Typed exceptions
  are rare operator-owned overrides. Accepted classes are refactor, infra, and
  upgrade, but generated templates, generated zones, `.process` files, PR
  bodies, and code fences are not valid provenance.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter — the deterministic comment-parse
  behavior and its unit coverage.
- **Secondary surfaces, if any**: docs/process — both phase-execution
  references and the workflow-file protocol entry for the Feedback Sweep Log.
- **Projected reviewable LOC**: ~330, re-derived at Plan from the Declared File
  Operations block. The whole-spec advisory estimate before splitting was
  `{"estimated_loc":452,"suggested_slices":2,"status":"warn"}` from 3 user
  stories, 14 files, and 18 functional requirements, modify-weighted.
- **Projected production files**: 7
- **Projected total files**: 10
- **Budget result**: within budget (projected). Plan re-measures from its own
  Declared File Operations block and records the result there.
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
  its author and that author's association, whether it was recognized as an
  artifact export, and its assigned class.
- **Feedback Sweep Log**: the durable table in the workflow file holding one
  row per handled comment. Header: `| # | Comment ID | Surface | Author |
  Class | Disposition | Commit | CRL # |`. It sits under its own
  `### Feedback Sweep Log` heading immediately after the Consensus Resolution
  Log. `CRL #` carries the linked Consensus Resolution Log row number and is
  empty for every class but `amended`. The table is the sole record of what the
  sweep has already handled and the basis for skipping on re-runs.
- **Export lead registry**: the fixed set of three lead sentences that identify
  an artifact-exported markdown block. Adding a future exporting page costs one
  more entry.
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
- **Deferred pending a concrete case**: an operator flag to skip the sweep. No
  case has surfaced, so the stop report's resume path is the only route.
  Clarify may revisit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a draft pull request carrying reviewer feedback, task work
  never begins until 100% of trusted, unrecorded comments carry a recorded
  disposition.
- **SC-002**: Following a sweep run whose bookkeeping commits all landed, every
  handled comment receives exactly one reply. Across the fixture corpus, no
  handled comment has zero replies and none has two.
- **SC-003**: Following a sweep run whose bookkeeping commits all landed,
  re-running the sweep with no new comments produces zero new log rows, zero
  new replies, and zero amendments, and proceeds into task work. When a prior
  run's amendment was pushed but its bookkeeping commit did not land, the next
  run's handling of that one item is the edge case documented under Edge
  Cases, not a violation of this criterion.
- **SC-004**: Zero artifact edits across the fixture corpus are attributable to
  an author outside the write-capable set.
- **SC-005**: The same observed comment data yields the same candidate set on
  every run, demonstrated by golden fixtures covering all three registered
  export lead sentences, the untrusted-author path, and the ordinary-comment
  path.
- **SC-006**: All four unreadable draft-pull-request conditions stop the run
  before any task work, each with a report naming the condition and a resume
  path; the no-record condition proceeds.
- **SC-007**: Both platform variants produce the same sweep outcome for the
  same input, with no behavioral difference between them.
- **SC-008**: After an amendment run stops, a reviewer can tell from the pull
  request alone what changed and where, without opening the workflow file.

## Assumptions

- The Draft PR row and its corroboration vocabulary (`match`, `pr_closed`,
  `pr_missing`, `identity_mismatch`, `no_record`) already ship from the
  preceding spec. This slice reads that record and reuses that vocabulary
  rather than defining its own.
- The category-routed consensus machinery and its four existing roles are
  reused unchanged. This slice adds a caller, not a new protocol.
- The three shipped export lead sentences are stable strings on the shipped
  pages. Recognition depends on them, so a page that changes its lead sentence
  needs a registry entry updated in the same change.
- Recognized export blocks may arrive on either comment surface. The acceptance
  runbook exercises both placements: one export pasted as a conversation
  comment, one pasted into a review thread.
- One class per comment is settled, not a working default. Recognized export
  anchors are carried as detail on that comment's record.
- The dominance rule ranks `amended` above the other three and stops there. It
  does not order `answered`, `deferred`, and `no action` against each other,
  because those three are behaviorally identical at both points classification
  controls: none route through consensus and none stop the run. A comment
  mixing only an answered point and a deferred point therefore has no stated
  headline class. That gap has no effect on stop-or-proceed or on routing, so
  it is left open rather than closed with a ranking that would carry no
  behavioral consequence.
- No aggregator script computes the Round-2 escape rate. The tool the design
  concept named was removed by an earlier shipped-Bash purge, and nothing
  replaced it, so the Consensus Resolution Log table is the metric's only data
  source and a reader computes it from the `Round` column and the
  `escape-hatch` outcome value.
- The shape of the deterministic parse — what it is called and exactly which
  fields it reports — is a Plan-phase decision, mirroring the shipped
  observation-input pattern and the closed corroboration vocabulary already in
  use.
- One fixed reply template per class, with the exact wording settled at Plan.
- The scoping interview's blind-spot pass did not run, so coupling in the
  corroboration input path this slice reuses has not been independently
  searched. Clarify reads that input contract before Plan commits to the parse
  shape.
- Reviewers inside the write-capable set act in good faith. The author-
  association filter is the security boundary; it is not a judgement about any
  individual reviewer's intent.
- Slice 2 is stacked on this branch, so this slice's records and report wording
  are the interface slice 2 builds on.
