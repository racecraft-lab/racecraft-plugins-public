# Feature Specification: Draft-PR Emission

**Feature Branch**: `art-007-draft-pr-emission`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "ART-007 Draft-PR Emission — end the plan stage at a
committed draft artifact set and an open draft pull request whose body indexes
the artifacts, then stop for human review. Covers artifact generation via a new
`artifact-author` subagent, a third draft mode on the pull-request packet
contract, draft-PR identity recorded on the workflow file, the plan-stage stop
report, and the inherited stage auto-detect corroboration limb."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Plan stage ends at an open draft pull request (Priority: P1)

The autopilot orchestrator finishes a plan stage. Once the final planning gate
resolves pass or warn, it commits the planning artifacts, opens a draft pull
request whose description indexes them, records the pull request's identity on
the workflow file, and stops with a report the operator can act on without
hunting: the link, the index, and how to resume.

Today the stage ends at a boundary commit and a STOP. Nothing durable reaches a
reviewer. This story is the whole point of the feature: it turns a private
branch state into a review surface.

**Why this priority**: Without it there is no draft pull request at all, and
every downstream capability (feedback sweep, ready flip, auto-detect
corroboration) has nothing to attach to. It is also independently valuable on
its own: even with zero generated artifacts the reviewer gets a pull request,
a scope statement, and a resume path.

**Independent Test**: Run a plan stage to completion with the final gate
resolving pass. Confirm a draft pull request exists for the branch, its
description carries an artifacts index and a resume/status block, the workflow
file carries the pull request's number and URL, and the stop report repeats the
URL, the index, and the resume instruction. This holds even when no artifacts
were generated.

**Acceptance Scenarios**:

1. **Given** a plan stage whose final gate resolves **pass**, **When** the
   terminal step runs, **Then** the generated artifacts are committed under the
   feature's `artifacts/` directory, a draft pull request opens with a
   final-shape conventional title, the pull request's number and URL are
   recorded on the workflow file, and the stop report carries the URL, the
   artifact index, and resume instructions.
2. **Given** a plan stage whose final gate resolves **warn**, **When** the
   terminal step runs, **Then** emission proceeds exactly as it does on pass.
3. **Given** a plan stage whose final gate resolves **blocked** under strict
   mode, **When** the terminal step runs, **Then** the existing contract is
   preserved unchanged — the boundary commit is taken, a non-terminal blocked
   row is recorded, and the stage STOPs — **and** no pull request is opened,
   with the stop report naming the blocked gate in place of a URL.
4. **Given** a draft pull request opened by this feature, **When** its title is
   checked against the repository's release-readiness title shape before any
   human edit, **Then** the title passes, and the description contains no
   release-note fence and no verification or final-writeup sections.

---

### User Story 2 - Planning artifacts are authored from the planning record (Priority: P2)

A dedicated authoring subagent reads the feature's specification, plan, tasks,
and design concept, picks which of the shipped draft-stage templates apply,
fills their marked regions, and writes the finished pages into the feature's
`artifacts/` directory so they ride the same commit as the rest of the stage.

Selection is conditional: two templates always apply, and two more apply only
when the feature carries the matching trait.

**Why this priority**: The artifacts are what makes the pull request worth
reviewing, but they are not what makes it exist. Emission (P1) already fails
open, so this story layers real content onto a hand-off that already works.

**Independent Test**: Point the authoring step at a feature whose planning
record is complete, run it alone, and confirm the expected set of pages is
written into the `artifacts/` directory with their marked regions filled from
the planning record and no placeholder text left behind. Force one template to
fail and confirm the remaining pages are still written.

**Acceptance Scenarios**:

1. **Given** a feature marked with neither competing approaches nor brownfield
   change, **When** artifact generation runs, **Then** exactly the two
   always-on pages (implementation plan and specification explainer) are filled
   and written.
2. **Given** a feature marked with competing approaches, **When** artifact
   generation runs, **Then** the code-approaches page is filled and written in
   addition to the two always-on pages.
3. **Given** a feature marked as a brownfield change, **When** artifact
   generation runs, **Then** the module-map page is filled and written in
   addition to the two always-on pages.
4. **Given** one selected page fails to generate, **When** generation
   completes, **Then** the pages that succeeded are written, the failed page
   appears as a gap-marked row in the pull request's artifacts index, and
   emission continues to completion.
5. **Given** every selected page fails to generate, **When** the terminal step
   runs, **Then** the draft pull request still opens with a gap-marked index,
   and the shortfall is noted in both the stop report and the workflow file's
   draft-PR record.

---

### User Story 3 - Stage auto-detect corroborates the recorded pull request (Priority: P3)

When the workflow resumes, stage auto-detect reads the draft-PR record from the
workflow file and checks it against the live pull request. If the two disagree,
it logs the discrepancy and proceeds using the workflow file's value, which is
the authoritative record.

**Why this priority**: It closes a limb deferred from the previous feature,
which had no draft pull requests to corroborate against. It improves confidence
in resume behavior but nothing else depends on it.

**Independent Test**: Seed a workflow file with a draft-PR record, run stage
auto-detect against a matching live pull request, and confirm the stage
resolves with no discrepancy logged. Repeat against a record that cannot be
corroborated and confirm a discrepancy is logged while the workflow file's
value is the one used.

**Acceptance Scenarios**:

1. **Given** a workflow file carrying a draft-PR record whose live pull request
   matches, **When** stage auto-detect runs, **Then** the stage resolves and no
   discrepancy is logged.
2. **Given** a workflow file carrying a draft-PR record that the live check
   cannot corroborate, **When** stage auto-detect runs, **Then** a discrepancy
   is logged and the workflow file's recorded value is the one the stage acts
   on.
3. **Given** a workflow file carrying no draft-PR record, **When** stage
   auto-detect runs, **Then** the stage resolves from the workflow file alone,
   no corroboration is attempted, and no discrepancy is logged.
4. **Given** a workflow file carrying a draft-PR record and a live check that
   cannot be completed — the query tool absent, unauthenticated, cancelled, or
   failing for any reason — **When** stage auto-detect runs, **Then** the stage
   resolves from the workflow file, the outcome is reported as skipped with its
   reason, and no discrepancy is logged.

---

### Edge Cases

- **Zero artifacts generated.** The draft pull request still opens, its index
  carries a gap row instead of artifact rows, and the shortfall is recorded in
  the stop report and on the workflow file's draft-PR record. Nothing about a
  generation failure can prevent the review hand-off.
- **Partial generation.** Some pages succeed and some fail. The successful ones
  are indexed normally, the failed ones appear as gap rows, and the run is not
  treated as a failure.
- **Gate blocked under strict mode.** No pull request is opened at all. The
  existing blocked-stop contract is preserved byte-for-byte, and the re-run
  that resolves pass is the run that emits the pull request.
- **Re-entering a stage that already emitted.** The workflow file already
  carries a draft-PR record for an open pull request. The run must not open a
  second pull request for the same feature. See FR-007.
- **Re-entering a stage whose recorded pull request was closed or merged.**
  The run does not reopen the pull request and does not open a second one.
  It logs the discrepancy, leaves the workflow file's `Draft PR` row
  unchanged, and the stop report names the discrepancy and the resume path.
  See FR-011.
- **Re-entering a stage whose recorded pull request cannot be observed.**
  The record names a pull request the successful live query does not return
  (`pr_missing`). The run creates nothing and rewrites nothing; it logs the
  discrepancy, and the stop report names the recorded identity and the
  manual resume path (correct or clear the row, then re-run). See FR-011.
- **Re-entering a stage whose branch carries a different open pull request.**
  The live query returns an open pull request whose number differs from the
  recorded one (`identity_mismatch`). The run creates nothing and rewrites
  nothing; it logs the discrepancy, and the stop report names both identities
  and the manual resume path. See FR-011.
- **Pull request creation itself fails.** The artifacts are already committed on
  the branch, so the planning work is not lost. The stop report must say the
  pull request could not be opened and name the resume path, rather than
  reporting a hand-off that did not happen.
- **The branch push fails.** The push sits between the boundary commit and
  creation, so a failure there leaves the artifacts and the boundary commit on
  the local branch and nothing on the remote. No pull request is created, no
  `Draft PR` row is written, and the stop report names the failed push and the
  resume path. See FR-013.
- **The bookkeeping commit or its push fails.** The pull request already exists,
  so it is neither closed nor recreated. The stop report carries its URL and says
  the record did not reach the remote; the re-run finds the open pull request
  through FR-007's existence test and repairs the record. See FR-013.
- **A later reviewability split.** If final reviewability requires slicing the
  work into multiple pull requests, the draft pull request becomes the first
  slice rather than being closed, so the review thread already collected on it
  survives.
- **Existing finished-implementation pull requests.** Adding a draft mode to the
  packet contract must leave the two existing modes behaving identically, so no
  already-shipped flow changes behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a dedicated artifact-authoring subagent
  that reads the feature's specification, plan, tasks, and design concept as its
  source material. It MUST ship on both supported agent platforms with identical
  instructions.
- **FR-002**: Artifact selection MUST follow the shipped gallery manifest's
  routing for draft-stage templates: the implementation-plan and
  specification-explainer pages are always selected; the code-approaches page is
  selected only when the feature is marked as having competing approaches; the
  module-map page is selected only when the feature is marked as a brownfield
  change.
- **FR-003**: Each selected page MUST have its marked fill regions populated
  from the planning record, and the finished pages MUST be written into the
  feature's `artifacts/` directory and committed so they are visible in review.
- **FR-004**: Artifact generation MUST fail open. A generation failure, whether
  partial or total, MUST NOT block emission; it MUST instead be recorded as a
  gap-marked row in the pull request's artifacts index, a note in the stop
  report, and a note on the workflow file's draft-PR record. A run that produces
  zero artifacts MUST still open the pull request. A page whose marked fill
  regions are not all populated counts as a generation failure for that page
  rather than as a partial success. Every gap-marked row MUST name what is
  missing — the individual page, or the whole set when selection itself could
  not run — and the reason it is missing, so the same shortfall is legible in
  all three sinks.

  Each sink binds only the runs that reach it. A run that stops at
  create-or-refresh under an FR-011 discrepancy, or before creation under an
  FR-013 sequence failure, writes no pull-request description and no draft-PR
  record, so its shortfall reaches the stop report alone; a run whose
  bookkeeping commit failed after creation has written the description but not
  the record. In each case the unwritten sinks are a consequence of the run not
  reaching them and MUST NOT be treated as a fail-open violation. The stop
  report is the one sink every such run reaches, and it MUST carry the shortfall
  on all of them.
- **FR-005**: The pull-request packet contract MUST gain a third mode
  representing a draft pull request, whose implementation-evidence requirements
  (verification evidence, changed-file scope evidence, and hands-on acceptance
  instructions) are conditionally relaxed for that mode only. Validation
  behavior for the two pre-existing modes MUST be unchanged.
  The conditionality is not confined to those three evidence requirements.
  Because FR-008 gives a draft description its own two-block body, every packet
  field that pins the reviewer-packet body shape MUST become conditional on mode
  as well — the required-heading set, the editable-prose field set, and the
  declared acceptance-runbook heading. A draft packet that relaxed only the
  three evidence requirements would still be rejected by its own validator, so
  this is one requirement rather than two.
- **FR-006**: Draft-PR emission MUST run only when the plan stage's final gate
  resolves pass or warn. On a strict-mode block, the existing terminal-step
  contract — boundary commit, non-terminal blocked row, STOP — MUST be preserved
  unchanged and no pull request MUST be opened. The terminal step MUST
  short-circuit before artifact generation on that block, so a blocked stage
  generates no artifact pages and the blocked path never fails open into a pull
  request.
- **FR-007**: The system MUST open the pull request in draft state with a
  final-shape conventional title that it self-validates against the repository's
  release-readiness title shape before creation. Exactly one draft pull request
  MUST exist per feature branch. Before creating one, the system MUST test for an
  existing one two ways — the workflow file's draft-PR record, and a live query
  for an open pull request on the head branch — and MUST treat either positive as
  proof that one exists, because the record is written after creation and a run
  interrupted between the two leaves a pull request with no record. When an open
  pull request exists for the branch, the system MUST refresh its description, and
  its title if the title changed, repair or write the workflow file's record, and
  report that existing URL as the emission outcome. It MUST NOT open a second pull
  request. Creation runs only when no open pull request exists for the head
  branch. A recorded pull request that is closed or merged is a discrepancy under
  FR-011, not grounds to open a second one. When the title fails its
  self-validation, the system MUST NOT create the pull request and MUST report
  through FR-010's could-not-be-opened path, rather than creating a pull request
  whose title a human would have to repair.
- **FR-008**: The draft pull request's description MUST contain exactly two
  blocks: an artifacts index table listing each artifact with its purpose and a
  copy-paste command to open it locally, and a resume/status block. It MUST NOT
  contain a release-note fence, verification sections, or placeholder final
  writeup content. When no artifact was generated, the index table MUST still be
  present under its heading and MUST carry gap rows — one per selected page, or
  a single whole-set row when selection itself could not run — rather than being
  omitted or left as a table with no rows.
- **FR-009**: The draft pull request's identity MUST be recorded on the workflow
  file as a single scalar row keyed `Draft PR` in the
  `## Specification Context` → `### Basic Information` table, the same key/value
  table that carries `Branch` and `Stage`. No row MUST be added to the
  `## Workflow Overview` table, whose rows are phase status records. The row's
  value MUST begin with the pull request's number and URL as one linked
  reference — link text `#<number>`, link target the URL — and MUST carry an
  artifact-shortfall note after that link in the same cell whenever generation
  fell short under FR-004; with no shortfall the cell carries the link alone.
  The workflow file MUST be the only place this identity is stored. Before a
  pull request exists the row MUST be absent; an absent row means no pull
  request has been opened, is legal, and MUST NOT be reported as an error, and
  the scaffold workflow template MUST NOT ship a placeholder row. The record
  MUST be written only after creation or refresh succeeds, and MUST be
  committed by the bookkeeping commit described in FR-013.

  Every write of the row MUST rewrite its whole value from the current run's
  outcome. A refresh whose shortfall differs from the recorded one MUST replace
  the note, and a refresh that generated every selected page MUST leave the cell
  carrying the link alone. A note describing an earlier run's shortfall MUST NOT
  survive a later refresh that no longer fell short.

  Writing this row is independent of the `Stage` row that shares the table. It
  MUST NOT count against, defer, or re-trigger the `Stage` row's own write
  cadence, and it MUST NOT require a state-file write, because this identity has
  no mirror to keep in step. Both rows are matched by key, so neither writer
  disturbs the other's value.

  The sole-store rule binds this feature's draft-PR identity. It does not forbid
  the shipped multi-pull-request slice manifest from recording the same pull
  request in its own slice role once FR-012's split makes it the first slice.
  That entry is a slice record written by a later stage's flow, not a second
  copy of the draft-PR record, and nothing in this feature writes it.
- **FR-010**: The plan-stage stop report MUST carry the pull request URL, the
  artifact index, and resume instructions when emission ran; when the gate
  blocked, it MUST name the blocked gate in place of a URL; when emission was
  attempted but the pull request could not be opened, it MUST say so and name
  the resume path; when the branch push that precedes creation failed, it MUST
  name the failed push, state that no pull request was opened and no draft-PR
  record was written, and name the resume path; when the bookkeeping commit or
  its push failed after the pull request was created or refreshed, it MUST carry
  the pull request URL and say that the draft-PR record did not reach the
  remote; and when a corroboration discrepancy ended the emission attempt, it
  MUST carry the discrepancy shape FR-011 specifies for that status. In each of
  these failure cases the report MUST name the step that failed, the state it
  left behind, and the resume path.
- **FR-011**: Stage auto-detect MUST corroborate the workflow file's draft-PR
  record against the live pull request and MUST treat the workflow file as
  authoritative in every outcome: corroboration MUST NOT change the resolved
  stage, MUST NOT block stage resolution, and MUST NOT stop the run.
  Corroboration MUST be attempted only when the `Draft PR` row is present. The
  live observation MUST be taken by the orchestrator as one read-only query
  scoped to the feature's head branch and returning pull requests in every
  state; the classification MUST be performed by the same stage-resolution step
  that already parses the workflow file's rows, from that observation supplied
  to it as input, so the record is parsed in exactly one place. The outcome
  MUST be exactly one of six statuses: `match`, `no_record`, `skipped`,
  `pr_closed`, `pr_missing`, `identity_mismatch`. The last three are
  discrepancies; the first three are not. Classification MUST run in this
  order, first match winning, and only against a successful observation: an
  open pull request on the head branch whose number differs from the recorded
  number, or a recorded number that is open but whose live URL differs from the
  recorded URL, is `identity_mismatch`; a recorded number whose live state is
  closed or merged is `pr_closed`, carrying whether it was merged; a recorded
  number absent from the observation is `pr_missing`; anything else is `match`.
  This status vocabulary is shared with the emission-time existence test in
  FR-007.

  The stage-resolution result MUST always carry the corroboration status, the
  recorded identity, the observed identity, and a reason when the check could
  not run, so a run that could not check is distinguishable from a run that
  checked and agreed. The run report MUST carry one line naming the status
  alongside the stage-resolution line it already prints. Only the three
  discrepancy statuses MUST be recorded durably, as that same line, in the
  workflow file's run-time Step 0.6c record, written in the same edit turn as
  the `Stage` row so it lands in the same commit. `match`, `no_record`, and
  `skipped` MUST write nothing durable, and the scaffold workflow template MUST
  NOT ship a placeholder line.

  A discrepancy MUST be classified only from a query that succeeded and
  returned a parseable result. Any other outcome — the query tool absent,
  unauthenticated, cancelled, rate-limited, failing for any reason, or
  returning output that cannot be parsed — MUST resolve to `skipped` with the
  reason recorded, MUST degrade to the workflow file, and MUST NOT be reported
  or recorded as a discrepancy.

  When the classification is `pr_closed` (`merged` true or false, carried on
  the same class per the classification paragraph above), the terminal step
  MUST NOT reopen the pull request and MUST NOT create a second one for the
  branch; the workflow file's `Draft PR` row MUST be left unchanged as the
  pointer to the closed pull request. The discrepancy MUST be logged through
  the sink named above, and the stop report MUST name the discrepancy, the
  closed pull request's number and URL, and the resume path — reopen the
  pull request manually (for example `gh pr reopen <number>`) if the close
  was unintended, then re-run the stage. This is a fail-open response: it
  ends the emission attempt for the run without invoking FR-006's
  strict-mode blocked-stop contract.

  When the classification is `pr_missing`, the terminal step MUST NOT create
  a pull request for the branch and MUST NOT rewrite the `Draft PR` row; the
  discrepancy MUST be logged through the sinks named above, and the stop
  report MUST name the discrepancy, the recorded number and URL, and the
  resume path — correct or clear the row manually, then re-run the stage.
  Like `pr_closed`, this is a fail-open response and does not invoke FR-006's
  strict-mode blocked-stop contract.

  When the classification is `identity_mismatch`, the terminal step MUST NOT
  create a pull request for the branch and MUST NOT rewrite the `Draft PR` row;
  the discrepancy MUST be logged through the sinks named above, and the stop
  report MUST name both identities — the recorded number and URL, and the
  observed one — and the resume path: correct or clear the row so it names the
  pull request the branch actually carries, then re-run the stage. Like
  `pr_closed` and `pr_missing`, this is a fail-open response and does not invoke
  FR-006's strict-mode blocked-stop contract.

  All three discrepancy responses MUST end the emission attempt at the same
  point in FR-013's sequence. The run generates the artifacts, takes the
  stage-boundary commit, and pushes the branch exactly as it always does, then
  stops at create-or-refresh without creating, refreshing, or recording
  anything, and takes no bookkeeping commit. It MUST NOT end earlier than that.
  Ending earlier would strand the durable discrepancy record, which is written
  at stage resolution and reaches version history only in a commit this stage
  goes on to take. This is the opposite of FR-006's strict-mode block, which
  short-circuits before generation.

  Corroboration is scoped by the presence of the row, not by the stage or by how
  the stage was resolved. It MUST run on every invocation whose `Draft PR` row
  is present, including one whose stage was named by an explicit argument rather
  than auto-detected, and including one that resolves a stage other than plan.
  On a run whose resolved stage has no emission terminal step, the status MUST
  still be reported and a discrepancy MUST still be recorded durably; the
  terminal-step consequences do not arise, because such a run opens, refreshes,
  and records nothing.

  The resolution-time observation and FR-007's emission-time existence test are
  two separate reads. The observation is taken once per run, at stage
  resolution, and only when the row is present. FR-007's live by-branch query is
  taken later, at the terminal step, and is what a `no_record` run falls through
  to, since no observation was taken for it at resolution. The terminal step
  MUST NOT treat the resolution-time observation as current evidence of the pull
  request's state, because the whole stage runs between the two reads.

  The three non-discrepancy statuses MUST carry terminal-step consequences too.
  On `match` the run refreshes the recorded pull request and reports its URL. On
  `no_record` the run falls through to FR-007's live existence test and creates
  or refreshes from that result. On `skipped` the `Draft PR` row is present by
  definition, so it still stands as a positive under FR-007's two-way existence
  test: the run MUST NOT create a second pull request, it refreshes the recorded
  pull request when it can, and when the tool cannot be reached at all it reports
  through FR-010's could-not-be-opened path. A `skipped` corroboration is never
  grounds for creation.
- **FR-012**: When final reviewability later requires splitting the work across
  multiple pull requests, the draft pull request MUST become the first slice
  pull request of the stack rather than being closed or superseded, so the
  review thread collected on it is preserved.
- **FR-013**: Once the final gate resolves pass or warn, the plan stage's
  terminal step MUST run in this order: generate the artifacts, take the
  existing stage-boundary commit, push the branch, create or refresh the draft
  pull request, write the draft-PR record, then take a separate bookkeeping
  commit carrying that record and push it. The stage-boundary commit's own
  contract — its message, its staged path set, and its non-emptiness — MUST be
  unchanged, and the draft-PR record MUST NOT be folded into it.

  Each step in that order is a precondition for the next, and a failed step
  MUST NOT be retried automatically; the operator re-run is the recovery path,
  and FR-007's two-way existence test is what makes that re-run safe. If the
  branch push fails, the terminal step MUST stop before creation: the generated
  artifacts and the boundary commit remain on the local branch, no pull request
  is created, no `Draft PR` row is written, and the stop report carries the
  FR-010 push-failure shape. If the bookkeeping commit or its push fails after
  the pull request was created or refreshed, the pull request MUST NOT be
  closed or recreated and the record MUST NOT be discarded; the stop report
  carries the FR-010 record-not-pushed shape, and the re-run finds the open
  pull request through FR-007's existence test and repairs the record instead
  of opening a second one.

  The bookkeeping commit MUST stage the workflow file, which is where the record
  lives and is the only file this step writes. Like the stage-boundary commit it
  MUST NOT stage the workflow directory, which also holds untracked run
  byproducts a directory-wide add would sweep in, and its message MUST follow the
  repository's conventional-commit shape.

  A re-run reaching a step whose content is already committed has nothing left
  to stage there. Such a commit is a no-op, not a failed step, and the sequence
  MUST continue past it. This does not weaken the boundary commit's preserved
  contract above, which describes what a first pass produces: that pass's
  non-emptiness comes from the gate row advancing off its pending state, and a
  re-run of an already-resolved stage does not repeat that advance. Treating the
  resulting empty commit as a failure would strand the operator re-run this
  requirement names as the only recovery path.

  Because the push precedes creation and FR-009's record is written only after
  creation succeeds, a written `Draft PR` row always names a pull request whose
  branch reached the remote. No ordering this requirement permits can leave the
  row pointing at a pull request that was never pushed.

### Reviewability Notes *(if applicable)*

- No typed reviewability exception is claimed for this feature. Typed
  reviewability exceptions are rare operator-owned overrides. Accepted classes
  are refactor, infra, and upgrade, but generated templates, generated zones,
  `.process` files, PR bodies, and code fences are not valid provenance.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: docs/process
- **Projected reviewable LOC**: ~287 (modify-weighted, excluding generated
  payloads and installed-cache proofs). The advisory size estimator, given three
  user stories, ten production files, thirteen functional requirements, and a
  modify-weighted profile, returns `{"estimated_loc": 335, "status": "ok",
  "suggested_slices": 1}`. The twelve-FR run recorded at specify time returned
  327; FR-013 was added in Clarify session 1 and moves neither the status nor
  the slice count.
- **Projected production files**: ~10
- **Projected total files**: ~14
- **Plan-phase refinement**: the three figures above are the projections made at
  specification time, and they are what produced the 335 estimate. Planning
  discovered two further entries and declared eleven production files and
  sixteen total. Re-running the advisory estimator at eleven production files,
  with the same three user stories and thirteen functional requirements on a
  modify-weighted profile, returns `{"estimated_loc": 355, "status": "ok",
  "suggested_slices": 1}` — the status and the slice count are unchanged, so the
  split decision below stands on the refined counts as well as the projected
  ones. The plan itemises both new entries.
- **Budget result**: within budget
- **Split decision**: Remains one spec. The work is a single vertical slice —
  artifact generation, then commit, then draft pull request, then stop report —
  and every part is inert without the others. Both the declared estimate and the
  advisory estimator sit under the warn ceiling, and the estimator returned one
  suggested slice.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Draft artifact set**: The pages written into the feature's `artifacts/`
  directory for one plan stage. Zero or more pages, each traceable to the
  template it was filled from and to the feature trait that selected it.
- **Draft review packet**: The structured record describing the pull request
  being opened. Carries a mode marking it as a draft, which relaxes the
  evidence a finished implementation would have to supply.
- **Draft-PR record**: The row on the workflow file's status surface holding the
  pull request's number and URL, plus any gap note. The single authoritative
  answer to "which pull request belongs to this feature".
- **Artifacts index**: The table in the pull request description mapping each
  artifact to its purpose and a copy-paste command that opens it locally.
  Carries gap rows when generation fell short.
- **Stop report**: The plan stage's terminal message to the operator. Carries
  the pull request URL, the artifact index, and resume instructions, or names
  the blocked gate when no pull request was opened.
- **Corroboration outcome**: The result of comparing the draft-PR record
  against the live pull request. One status from a closed set, the recorded
  and observed identities, and a reason when the check could not run. Always
  reported; durably recorded only when it is a discrepancy.

## Out of Scope

- Reading or acting on pull-request review feedback. That is ART-008.
- Flipping the draft pull request to ready for review, and authoring the final
  pull-request writeup. That is ART-010.
- Governed-corpus membership for the new artifact-authoring subagent. It ships
  outside the corpus as a tracked deferral to ART-009, which must already open
  the corpus for its own rename work. This feature MUST NOT edit any of the
  twelve governed agent definitions.
- Any hosting layer for the artifacts. They are committed so they are visible in
  review and opened locally from the filesystem.
- A second, mirrored copy of the draft-PR identity in a state file.
- Changes to the final planning gate's semantics, its thresholds, or the
  boundary-commit contract.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of plan stages whose final gate resolves pass or warn
  either end with an open draft pull request for the feature, or — when the
  recorded pull request was closed, merged, no longer observable outside
  automation, or contradicted by a different open pull request on the branch, or
  when a step of the FR-013 emission sequence failed — end with a logged
  discrepancy or failure note and an operator-actionable stop report naming the
  resume path.
- **SC-002**: A reviewer can open every generated artifact directly from the
  pull request description without searching the branch: the index lists 100% of
  generated artifacts, each with a copy-paste open command.
- **SC-003**: A generation failure never prevents the review hand-off. No pass
  or warn run is prevented from opening the pull request by a generation
  failure, including runs that produce zero artifacts (the only non-opening
  cases are the FR-011 discrepancy responses and the FR-013 emission-sequence
  failures, none of which are generation failures), and every shortfall is
  visible in all three places — the index, the stop report, and the workflow
  record — on every run that reaches all three. On a run that ended at an
  FR-011 discrepancy or an FR-013 sequence failure, the sinks that run never
  reached are not written, and the stop report carries the shortfall in every
  case, per FR-004.
- **SC-004**: 100% of strict-mode blocked plan stages produce no pull request,
  and their stop report names the blocking gate.
- **SC-005**: Resuming the workflow locates the feature's pull request from the
  recorded identity on the first attempt, with no manual search, in 100% of runs
  where a record exists.
- **SC-006**: The operator needs no follow-up action to hand off for review: the
  stop report alone carries the link, the artifact index, and the resume
  instruction; when FR-011 records a discrepancy instead, the stop report alone
  carries the discrepancy, the recorded pull request's identity, and the manual
  resume path; and when a step of the FR-013 sequence failed instead, the stop
  report alone carries the step that failed, the state it left behind, and the
  resume path.
- **SC-007**: 100% of emitted pull-request titles pass the repository's
  release-readiness title shape check at creation time, before any human edit.
- **SC-008**: Pull-request flows for completed implementations are unaffected:
  validation outcomes for the two pre-existing packet modes are identical before
  and after this change across the existing test corpus.

## Assumptions

- The authoring subagent's model, effort, and permitted-tool declarations mirror
  the closest shipped analogue, the existing acceptance-runbook author, which is
  also a fail-open content-authoring role dispatched at pull-request time. The
  pattern is confirmed by reading that file during planning, not from memory.
- Committed artifact pages do not need a generated-artifact merge-driver entry.
  Sibling per-feature files such as the plan and tasks documents are not marked
  generated either and do not hit the merge pain the driver exists for. Revisit
  only if a real conflict appears.
- The repository's pull-request checks skip every job while a pull request is in
  draft state, so the draft description needs no release-note fence and nothing
  goes red before the later ready flip.
- The branch is not pushed by any earlier step of the plan stage: the
  stage-boundary commit stages and commits but does not push. The terminal step
  MUST push the branch itself, after the boundary commit and before pull-request
  creation. That push is what makes creation possible.
- The command-line tool used to open and query pull requests is installed and
  authenticated in the environment where the stage runs. If it is not, emission
  fails open per FR-010 rather than failing the stage. The same applies to
  corroboration: when the tool cannot be reached or cannot answer,
  corroboration is skipped rather than treated as evidence that the recorded
  pull request is gone.
- The workflow file is the authoritative record of workflow state, inherited
  from the prior feature's OQ-4 decision. Live pull-request data corroborates it
  but never overrides it.
- The four draft-stage templates and their gallery manifest routing already ship
  and are consumed as-is. This feature authors into them; it does not change
  them.
- The draft pull request becoming the first slice of a later stack is a settled
  decision carried in from the design concept's OQ-1 resolution. Clarify encodes
  it; it does not reopen it.
- At most one plan-stage run is in flight for a feature branch at a time. The
  stage is human-paced and stops for review, so FR-007's existence test is not
  required to be safe against two runs racing between the test and creation.
  Concurrent runs of the same stage are out of scope.
