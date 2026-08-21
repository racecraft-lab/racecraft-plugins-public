# Feature Specification: Feedback Sweep, slice 1 of 2 — the checkpoint

**Feature Branch**: `art-008-feedback-sweep`

**Created**: 2026-08-20

**Status**: Draft

**Input**: User description: "ART-008 slice 1 of 2, the checkpoint. The plan stage ends at an open draft pull request whose body indexes the planning artifacts, and the gallery's draft-stage pages export a reader's objections as markdown meant to be pasted into a pull-request comment. Nothing reads those comments back, so an implement-stage run starts task work without looking at the pull request and the checkpoint is decoration. Make the implement stage open with a feedback sweep that reads unresolved review threads and pull-request conversation comments, acts only on write-capable authors, recognizes exported markdown blocks by their lead sentence, classifies each comment as amended, answered, deferred, or no action, routes amendments through the existing consensus machinery, records every handled comment in a Feedback Sweep Log in the workflow file, replies once per comment, and then stops for re-review when anything was amended or proceeds into task work when nothing was. Artifact regeneration, stale-page detection, and the draft-description refresh belong to slice 2."

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
  Feedback Sweep Log.
- **FR-010**: Every trusted, unrecorded comment MUST be assigned exactly one
  class from the closed set: amended, answered, deferred, no action. No other
  value is permitted. [NEEDS CLARIFICATION: when one recognized export block
  carries several distinct objections that merit different dispositions, for
  example one amended and one deferred, does the sweep assign a single class to
  the whole comment, or one classified item per recognized objection with the
  log keyed by comment id plus anchor?]
- **FR-011**: Only the `amended` class routes through the category-routed
  consensus protocol. The `answered`, `deferred`, and `no action` classes MUST
  NOT invoke consensus.

**Amendment**

- **FR-012**: For each amended item, the sweep MUST apply the
  consensus-resolved edit to `spec.md`, `plan.md`, or `tasks.md`, then commit
  and push that change. [NEEDS CLARIFICATION: does the sweep make one commit
  per amendment or one commit for the whole run, and is the Feedback Sweep Log
  write its own bookkeeping commit separate from the amendment commits?]

**Durable record**

- **FR-013**: The sweep MUST write one Feedback Sweep Log row per handled
  comment, carrying comment id, surface, author, class, disposition, and
  commit. The workflow file MUST be the sole store; no state-file mirror of the
  sweep record may be written.
- **FR-014**: Each amended item MUST additionally produce a Consensus
  Resolution Log row linked to its Feedback Sweep Log row.
  [NEEDS CLARIFICATION: which Consensus Resolution Log type value marks a
  sweep amendment, and how must the existing round and escape-rate aggregation
  treat that value so sweep rows do not distort the metric?]

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
  row per handled comment — comment id, surface, author, class, disposition,
  commit. It is the sole record of what the sweep has already handled and the
  basis for skipping on re-runs.
- **Export lead registry**: the fixed set of three lead sentences that identify
  an artifact-exported markdown block. Adding a future exporting page costs one
  more entry.
- **Classification**: the closed four-value vocabulary — amended, answered,
  deferred, no action — assigned to every trusted, unrecorded comment.
- **Consensus Resolution Log row**: the existing record that already governs
  consensus outcomes. Amendments add a row here in addition to the Feedback
  Sweep Log row, linked by number.
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
- **SC-002**: Every handled comment receives exactly one reply. Across the
  fixture corpus, no handled comment has zero replies and none has two.
- **SC-003**: Re-running the sweep with no new comments produces zero new log
  rows, zero new replies, and zero amendments, and proceeds into task work.
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
- Pending the FR-010 clarification, the working default is one class per
  comment, with recognized export anchors carried as detail on that comment's
  record.
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
