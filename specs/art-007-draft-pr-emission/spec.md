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
- **Pull request creation itself fails.** The artifacts are already committed on
  the branch, so the planning work is not lost. The stop report must say the
  pull request could not be opened and name the resume path, rather than
  reporting a hand-off that did not happen.
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
  zero artifacts MUST still open the pull request.
- **FR-005**: The pull-request packet contract MUST gain a third mode
  representing a draft pull request, whose implementation-evidence requirements
  (verification evidence, changed-file scope evidence, and hands-on acceptance
  instructions) are conditionally relaxed for that mode only. Validation
  behavior for the two pre-existing modes MUST be unchanged.
- **FR-006**: Draft-PR emission MUST run only when the plan stage's final gate
  resolves pass or warn. On a strict-mode block, the existing terminal-step
  contract — boundary commit, non-terminal blocked row, STOP — MUST be preserved
  unchanged and no pull request MUST be opened.
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
  FR-011, not grounds to open a second one.
- **FR-008**: The draft pull request's description MUST contain exactly two
  blocks: an artifacts index table listing each artifact with its purpose and a
  copy-paste command to open it locally, and a resume/status block. It MUST NOT
  contain a release-note fence, verification sections, or placeholder final
  writeup content.
- **FR-009**: The draft pull request's identity MUST be recorded on the workflow
  file as a single scalar row keyed `Draft PR` in the
  `## Specification Context` → `### Basic Information` table, the same key/value
  table that carries `Branch` and `Stage`. No row MUST be added to the
  `## Workflow Overview` table, whose rows are phase status records. The row's
  value MUST begin with the pull request's number and URL as one linked
  reference — link text `#<number>`, link target the URL — and MAY carry an
  artifact-shortfall note after that link in the same cell. The workflow file
  MUST be the only place this identity is stored. Before a pull request exists
  the row MUST be absent; an absent row means no pull request has been opened,
  is legal, and MUST NOT be reported as an error, and the scaffold workflow
  template MUST NOT ship a placeholder row. The record MUST be written only
  after creation or refresh succeeds, and MUST be committed by the bookkeeping
  commit described in FR-013.
- **FR-010**: The plan-stage stop report MUST carry the pull request URL, the
  artifact index, and resume instructions when emission ran; when the gate
  blocked, it MUST name the blocked gate in place of a URL; when emission was
  attempted but the pull request could not be opened, it MUST say so and name
  the resume path.
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
  user stories, ten production files, twelve functional requirements, and a
  modify-weighted profile, returned `{"estimated_loc": 327, "status": "ok",
  "suggested_slices": 1}`.
- **Projected production files**: ~10
- **Projected total files**: ~14
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
  recorded pull request was closed or merged outside automation — end with a
  logged discrepancy and an operator-actionable stop report naming the
  resume path.
- **SC-002**: A reviewer can open every generated artifact directly from the
  pull request description without searching the branch: the index lists 100% of
  generated artifacts, each with a copy-paste open command.
- **SC-003**: A generation failure never prevents the review hand-off. 100% of
  pass or warn runs open the pull request, including runs that produce zero
  artifacts, and every shortfall is visible in all three places: the index, the
  stop report, and the workflow record.
- **SC-004**: 100% of strict-mode blocked plan stages produce no pull request,
  and their stop report names the blocking gate.
- **SC-005**: Resuming the workflow locates the feature's pull request from the
  recorded identity on the first attempt, with no manual search, in 100% of runs
  where a record exists.
- **SC-006**: The operator needs no follow-up action to hand off for review: the
  stop report alone carries the link, the artifact index, and the resume
  instruction.
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
