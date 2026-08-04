# Feature Specification: Autopilot Staging

**Feature Branch**: `art-006-autopilot-staging`

**Created**: 2026-08-03

**Status**: Draft

**Input**: User description: "Autopilot runs all seven SDD phases as one unbroken sequence. There is no supported way to stop after planning, let a human review the result, and later resume into implementation. Give autopilot first-class stages — `plan`, `implement`, `full` — with auto-detection from the workflow file and durable stage state, on both the Claude and Codex distributions. Gate semantics are unchanged; only stage ownership of G6.5 is decided."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stop cleanly after planning (Priority: P1)

A maintainer starts autopilot on a workflow file and asks for the planning stage
only. Autopilot works through specification, clarification, planning, checklists,
task generation, and analysis, finishes with the confidence gate, records that the
planning stage is done, commits that boundary, and stops. It does not begin
implementation. The maintainer now has a complete, reviewable planning result and
can walk away.

**Why this priority**: This is the boundary the whole staged-review workflow rests
on. Without a supported stop-after-planning, there is no human checkpoint to
review, and every downstream spec that consumes the stage vocabulary is blocked.
Delivered alone it is already useful: a maintainer gets reviewable planning output
without an unattended run continuing into code changes.

**Independent Test**: Run autopilot against a workflow file with the planning
stage requested. Confirm the analysis phase and the confidence gate both complete,
that no implementation phase work started, that the recorded stage reads as the
planning stage, and that the stage boundary exists as a commit rather than as
uncommitted working-tree state.

**Acceptance Scenarios**:

1. **Given** a workflow file whose phases have not been run, **When** the
   maintainer requests the planning stage, **Then** autopilot runs specification
   through analysis, runs the confidence gate as the stage's terminal step, and
   stops before the implementation phase.
2. **Given** the planning stage has just finished, **When** the maintainer
   inspects version history, **Then** the stage boundary is a commit that includes
   the workflow file's status updates and its recorded stage, not uncommitted
   changes.
3. **Given** the planning stage has just finished, **When** the maintainer reads
   the workflow file, **Then** its recorded stage and its per-phase status entries
   agree with the gate evidence captured in the same file.
4. **Given** the planning stage is requested, **When** autopilot reaches the point
   where implementation would begin, **Then** it terminates with a clear report of
   what completed and what remains, and no implementation task is started.

---

### User Story 2 - Resume into implementation later (Priority: P2)

Some time after the planning stage finished — in a brand-new session, possibly
from a different working copy — the maintainer asks autopilot for the
implementation stage. Autopilot picks up where the planning stage left off,
rebuilding what it needs from the workflow file, and runs implementation through
the post-implementation steps without redoing planning work.

**Why this priority**: Stopping is only half the boundary. A checkpoint a
maintainer cannot cross is a dead end. This depends on Story 1 having produced
durable state, so it follows it.

**Independent Test**: With a workflow file left at the completed planning stage,
start a fresh session and request the implementation stage. Confirm autopilot
resumes at the implementation phase, does not re-run planning phases, and that the
planning stage's recorded results are still intact and used.

**Acceptance Scenarios**:

1. **Given** a workflow file whose planning stage is recorded complete, **When**
   the maintainer requests the implementation stage from a new session, **Then**
   autopilot begins at the implementation phase and runs through the
   post-implementation steps.
2. **Given** a resumed implementation stage, **When** autopilot runs, **Then** it
   does not re-run the specification, clarification, planning, checklist, task, or
   analysis phases.
3. **Given** the resume happens in a different working copy from the one that ran
   the planning stage, **When** autopilot starts, **Then** it reconstructs the
   context it needs from the workflow file alone and proceeds.
4. **Given** an implementation stage is requested, **When** autopilot performs its
   opening preparation, **Then** it re-derives project commands and conventions,
   and any baseline recorded when the work first started remains the reference
   point for end-of-run comparison.

---

### User Story 3 - Bare invocation resolves its own stage (Priority: P3)

A maintainer runs autopilot on a workflow file without naming a stage. Autopilot
reads the workflow file's own status table and decides which stage is appropriate:
if the planning phases are all complete it proceeds as the implementation stage,
otherwise as the planning stage. The maintainer is told which stage was chosen and
why before work begins.

**Why this priority**: A convenience layer over Stories 1 and 2. Explicitly naming
a stage always works, so this can ship last without blocking the boundary itself.

**Independent Test**: Run autopilot with no stage named against two workflow files
— one with planning phases incomplete, one with them all complete — and confirm
each resolves to the expected stage and reports the resolution before starting.

**Acceptance Scenarios**:

1. **Given** a workflow file with planning phases incomplete and no stage named,
   **When** autopilot starts, **Then** it resolves to the planning stage and
   reports that choice.
2. **Given** a workflow file with all planning phases complete and no stage named,
   **When** autopilot starts, **Then** it resolves to the implementation stage and
   reports that choice.
3. **Given** a stage is named explicitly, **When** it disagrees with what
   auto-detection would have chosen, **Then** the explicitly named stage wins.

---

### Edge Cases

- **Unrecognized stage name.** A stage outside the accepted set is rejected during
  opening preparation, before any phase work begins, with a message naming the
  accepted values.
- **Mutually exclusive arguments.** A stage argument that conflicts with another
  argument in the same invocation is rejected during opening preparation rather
  than midway through a run.
- **Recorded stage disagrees with phase evidence.** When the workflow file's
  recorded stage contradicts its own per-phase status and gate evidence, the
  contradiction is surfaced as a failure rather than silently resolved.
- **Mirror disagrees with the authoritative record.** When the running session's
  mirrored copy of the stage disagrees with the workflow file, the workflow file
  wins and the mirror is corrected.
- **Implementation stage requested before planning finished.** Autopilot reports
  that the planning stage is incomplete and names the phases still outstanding
  rather than starting implementation against missing planning artifacts.
- **Resuming at a specific phase inside a stage.** Asking to start from a
  particular phase continues to work and only changes the starting point; it does
  not widen or narrow the resolved stage's phase range.
- **A stage whose phases are all already complete.** Autopilot reports the stage
  as already satisfied instead of re-running finished work.
- **Workflow file predating this feature.** A workflow file with no recorded stage
  entry is treated as "no run yet" and resolves through ordinary auto-detection.
  It is not an error and does not require a fourth stage value. This is the common
  case, not the exception: of the workflow files in this repository today, all but
  one carry no stage entry.
- **State file names a different specification.** When the single-slot state file
  points at another specification's workflow file, opening preparation reclaims
  the slot from the target workflow file before the coverage guard runs, rather
  than failing. The guard cannot currently be relied on to detect this itself: run
  against a mismatched slot it exits zero and reports a pass, so re-initialisation
  must not be ordered after it.
- **Archived specification.** Because the workflow file survives archiving, the
  recorded stage remains readable after the specification directory is archived.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define a closed set of exactly three stage names —
  the literal lowercase tokens `plan`, `implement`, and `full` — and MUST reject
  any other value. The same three literals MUST be used for the invocation
  argument value and for the recorded `Stage` entry; no aliases, no alternate
  casing, and no long-form spellings. (Clarify S1/Q2: the roadmap, this spec's
  own workflow file, and ART-011's dependency on "the autopilot plan stage per
  the ART-006 contract" all already use the short tokens, so the spelling is a
  cross-spec contract rather than prose.)
- **FR-002**: Both the Claude and the Codex distributions MUST accept an explicit
  stage argument on the autopilot invocation, using the same argument name and the
  same accepted values. The same change MUST repair the pre-existing divergence
  between the two usage synopses, where the Claude side omits the confidence-mode
  flags the Codex side advertises. That omission is stale documentation rather
  than missing capability — the Claude side already resolves those flags from the
  invocation arguments — and the same synopsis line is edited anyway to add the
  stage argument, so the repair costs one line and changes no gate behaviour.
  (Clarify S2/R3, Round 2 tiebreak.)
- **FR-003**: The planning stage MUST run the specification, clarification,
  planning, checklist, task-generation, and analysis phases, MUST run the
  confidence gate as its terminal step, and MUST stop without starting the
  implementation phase.
- **FR-004**: The implementation stage MUST run the implementation phase and the
  post-implementation steps, and MUST NOT re-run any planning-stage phase.
- **FR-005**: The full stage MUST run every phase end to end, preserving the
  existing single-sequence behavior for callers who want it.
- **FR-006**: When no stage is named, the system MUST resolve the stage from the
  workflow file's own phase status table — all planning phases complete resolves
  to the implementation stage, otherwise the planning stage — and MUST report the
  resolved stage and its basis before phase work begins. An explicitly named stage
  MUST override this resolution.
- **FR-007**: An unrecognized stage value, or a stage argument that conflicts with
  another argument in the same invocation, MUST be rejected during opening
  preparation with a non-zero exit and a message naming the problem, before any
  phase work begins.
- **FR-008**: The workflow file MUST be the authoritative durable store of the
  stage, recorded as a `Stage` entry in its basic-information table. The running
  session's state file MUST carry a mirrored copy for the active run only and MUST
  NOT be treated as authoritative; on disagreement the workflow file MUST win and
  the state mirror MUST be repaired from it. This authority MUST be recorded as
  its own clause in the autopilot's store-precedence documentation. It MUST NOT be
  added to that document's existing two-item exception list, because that list
  enumerates the fields for which the *state file* wins, which is the opposite
  direction. (Clarify S1/Q1, both analysts.)
- **FR-008a**: The `Stage` entry MUST record the last *resolved* stage of the most
  recent run, not stage completion. Within-stage progress remains derived from the
  workflow file's phase status table, so no additional token is required to
  express "planning finished". A workflow file carrying no `Stage` entry MUST be
  treated as "no run yet" and MUST resolve through the auto-detection rule in
  FR-006; absence MUST NOT be treated as a fourth stage value and MUST NOT be
  reported as an error. (Clarify S1/Q2. 57 workflow files exist in this repository
  and exactly one carries the entry, so a required-everywhere rule would fail the
  suite against 56 pre-existing files on the day it ships. The shipped validator
  already establishes the "absence is legal" pattern for its sibling `status`
  field.)
- **FR-008b**: The `Stage` entry MUST be written at most twice per run — once when
  the stage is resolved during opening preparation, and again at the planning
  stage's terminal commit only if the resolved stage changed. It MUST NOT be
  refreshed on every phase transition. The authoritative entry and its state
  mirror MUST be written in the same edit turn and MUST land in the same commit,
  so an interrupted run cannot leave a committed disagreement between the two
  stores. (Clarify S1/Q5.) The planning stage's terminal commit is non-empty
  independent of whether the `Stage` entry changed, because the confidence-gate row
  always advances off its pending state — so the conditional second write needs no
  empty-commit escape. (Clarify S3/Q1.)
- **FR-009**: The stage boundary MUST be durably committed — per-phase bookkeeping
  MUST be staged as each phase completes rather than only at the end of a run, and
  the planning stage MUST close with an explicit terminal commit that makes the
  boundary identifiable in version history. That terminal commit MUST be taken
  *after* the confidence gate resolves, MUST stage the same enumerated path set as
  the per-phase commits, and MUST carry a message naming the stage boundary rather
  than a phase. It is a distinct commit, not a renamed analysis-phase commit,
  because the confidence gate runs after that phase's commit and its verdict must
  be captured. (Clarify S3/Q1.)
- **FR-009a**: The per-phase staged path set MUST be an explicit enumeration of the
  specification directory, the workflow file, and the state file. It MUST NOT be
  expressed as the workflow *directory*, because that directory also holds
  untracked run byproducts that a directory-wide add would sweep into phase
  commits — a failure that passes locally and fails only on a clean checkout.
  (Clarify S3/Q2.)
- **FR-010**: A fresh session, including one in a different working copy, MUST be
  able to reconstruct the stage identity, per-phase completion state, and
  confidence-gate verdict it needs to resume a stage from the workflow file alone,
  without depending on the previous session's state file. This requirement does
  NOT extend to pull-request marker-plan evidence. That evidence is reached during
  the implementation stage's post-implementation steps, so it is not outside this
  stage; it is governed by its own pre-existing and stricter rule, which requires
  stopping rather than inferring from workflow prose when the evidence is missing,
  malformed, or stale. That rule shipped with the discharged prerequisite, is
  unchanged by this specification, and MUST NOT be relaxed to satisfy this
  requirement. (Clarify S1/Q4. Both analysts agreed the contradiction is real; the
  resolution is a specification-text carve-out costing zero implementation lines,
  not a new rehydration path, which would spend the declared budget margin on a
  subsystem this spec's key files do not claim.)
- **FR-010a**: An implementation-stage invocation MUST NOT re-run the pre-implement
  confidence gate; it MUST read the recorded verdict from the workflow file, which
  FR-010 already places in scope. Opening preparation MUST preserve an
  already-recorded prerequisite test-count baseline rather than overwriting it,
  because the later gate verifies an increase against that baseline and a
  post-planning recount would make the comparison vacuous. A newly observed count
  that differs MUST be recorded as a non-blocking drift diagnostic instead of
  replacing the baseline. An implementation-stage invocation MUST still accept the
  confidence-mode flags rather than rejecting them, because the Codex surface
  already advertises them unconditionally and FR-013 confines Codex changes to
  additive ones. It MUST emit an explicit diagnostic stating that the confidence
  gate is not run in this stage and that the recorded verdict is read instead, so
  an accepted flag never silently does nothing. (Clarify S3/Q4, settled once the
  Round 2 tiebreak established that both distributions already accept those flags
  behaviourally.)
- **FR-011**: The canonical task list MUST NOT be truncated per stage. Entries
  outside the resolved stage MUST be marked with a `skipped:` status, which is the
  only non-complete status the existing pre-final audit tolerates. Four constraints
  govern that marker, three verified against the shipped validator:
  (a) the marker MUST occupy the entry's **status** field, and the entry's **name
  MUST remain byte-identical** to its canonical name, because the coverage guard
  matches post-implementation checkpoints by exact name equality — a name carrying
  a `skipped:` prefix is reported as a *missing* checkpoint, which would fail every
  planning-stage run at the pre-final audit;
  (b) the marker text MUST NOT contain the substring `pending` in any casing,
  because the guard flags any string value containing it case-insensitively;
  (c) it MUST reuse the established `skipped: <reason>` shape already used for
  absent extensions, so one search finds both kinds of skip; and
  (d) a planning-stage run marks the implementation phase **and every
  post-implementation entry** out of stage — the post-implementation family is
  where the audit actually blocks. (Clarify S3/Q3.)
- **FR-012**: Stage resolution MUST be implemented once as shared logic that both
  distributions execute, rather than as two independent prose descriptions of the
  same rule, and that shared logic MUST be a registered runner operation reached
  by operation identifier from both distributions — the mechanism the
  pre-implement confidence-mode resolver already uses at the same
  opening-preparation step. It MUST NOT live in the shipped phase-coverage guard:
  that guard accepts only a workflow path, a state path, two expected-commit
  arguments, and a rule selector, and is a consistency checker over two
  already-resolved inputs rather than a resolver. Siting resolution there would
  also contradict the opening-preparation directive to reach helper behaviour
  through the runner rather than a plugin-local script file. The guard MAY consume
  the resolver as an imported library, which is how the agent-independent
  validator already reuses shared logic. (Clarify S2/R1, Round 2 tiebreak.)
  The resume protocol MUST likewise be shared: today the Codex
  distribution documents recovery only for a *missing* state file and the Claude
  distribution documents none at all, which is a parity gap this requirement
  closes. (Clarify S1/Q3.)
- **FR-012a**: When an implementation-stage invocation targets a workflow file
  that the single-slot state file does not currently name, opening preparation
  MUST reclaim the slot from the target workflow file — rewriting the active
  workflow identity, specification identity, feature directory, branch, run
  status, resolved stage, and plan list — BEFORE the coverage guard runs.
  Reclaiming the slot is normal operation, not an error: the state file is defined
  as a per-run pointer and the previous specification's durable record is its own
  workflow file. Any field used to note the reclaimed predecessor MUST be part of
  the documented state contract rather than ad hoc. (Clarify S1/Q3. The field name
  used by hand during this run has zero occurrences elsewhere in the repository
  and MUST NOT be treated as established precedent.)
- **FR-013**: Changes to the Codex distribution MUST be additive: the four
  string-pinned sentences enforced by the structural suite MUST survive verbatim,
  the stage prose MUST live in the referenced phase-execution document rather than
  the skill body, and the skill body MUST remain within its enforced word cap.
- **FR-014**: Stage correctness MUST be enforced in two places, which are two
  different checks rather than the same check twice: (a) an in-run check in the
  shipped phase-coverage guard, which both distributions already invoke with both
  stores on one command line, asserting that the state mirror equals the
  authoritative entry; and (b) an agent-independent check in the already-shipped
  workflow status-evidence validator, which runs in the suite whether or not an
  agent invokes anything. Neither may be a new third validator.
- **FR-014a**: The in-run check MUST register its own problem key in the guard's
  rule-to-problem-key map. A check whose key is absent from that map computes its
  result and reports it in the emitted JSON, but CANNOT affect the exit code under
  the scoped invocation the autopilot actually issues, and is therefore inert as a
  gate. This is not hypothetical: the existing workflow-identity check is inert in
  exactly this way today — run against a state file naming a different
  specification, the guard exits 0 and reports `pass`, both with and without the
  scoping flag, because its error key appears in no rule tuple and its body
  short-circuits unless a v2 marker-plan schema and an expected-head-commit
  argument are both supplied. (Clarify S1/Q1, verified by direct execution.)
- **FR-015**: A unit test MUST carry golden fixtures for both explicit and
  auto-detected stage resolution, including a planning-stage state fixture whose
  post-implementation entries carry the out-of-stage skipped status with canonical
  names intact. No new test or script filename may contain a live specification
  family token.
- **FR-015a**: The cross-distribution argument-parity assertion MUST live in that
  same unit test, exercising resolution behaviour on both distributions. It MUST
  NOT be added to the structural cross-platform parity validator, whose checks are
  existence-only by design, whose counted baseline would need regenerating, and
  which this specification's own record already names as unable to catch this
  class of divergence. (Clarify S2/R2, Round 2 tiebreak.)
- **FR-016**: The specification MUST document a scaffold-to-autopilot chain
  contract enumerating five things the downstream scaffold-integration
  specification cannot derive on its own: the handoff artifact (the workflow file
  path, the sole handoff token); the entry precondition (at scaffold time the stage
  entry is absent, and absence means "no run yet"); the per-platform invocation
  form and the closed stage vocabulary; the workflow-file-observable completion
  signal for the planning stage; and an explicit statement that the scaffold-side
  implementation is out of scope here. The contract is documentation only — this
  specification ships no scaffold-side code. (Clarify S3/Q5.)

### Reviewability Notes *(if applicable)*

- No typed reviewability exception is claimed. The declared budget is within
  limits without one.
- The generated distribution mirrors and installed-cache proofs that this change
  necessarily refreshes are declared generated artifacts and are excluded from the
  reviewable line count below. They are regenerated by the repository's artifact
  refresh tooling and are never hand-edited.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: docs/process
- **Projected reviewable LOC**: 382 (estimator, modify-weighted, excluding
  declared generated mirrors and proofs)
- **Projected production files**: ~12 modified
- **Projected total files**: ~14 including the new unit test and its fixtures
- **Budget result**: within budget
- **Split decision**: Remains one slice. The work is genuinely vertical — one
  capability cutting end to end through argument parsing, stage resolution, the
  stage-bounded phase loop, durable stage state, and both distributions. Deferring
  the draft-pull-request corroboration limb to the downstream spec is what keeps
  this within budget; with that limb included the estimator returns 452 LOC and
  suggests two slices, and the remaining auto-detect half is too thin to stand as
  its own slice. The planning phase re-checks the estimate against real artifacts.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Stage**: One of exactly three literal lowercase tokens — `plan`, `implement`, `full`.
  Determines which contiguous range of phases an autopilot run executes.
- **Workflow file**: The durable, per-specification record of a run. Holds the
  authoritative stage, the per-phase status table, and the gate evidence. Survives
  archiving of the specification directory.
- **Session state file**: The in-flight pointer for the currently running session.
  Carries a mirrored copy of the stage for the active run only; derived, never
  authoritative.
- **Phase status entry**: One row per phase in the workflow file, recording
  completion and the evidence supporting it. The input to stage auto-detection.
- **Canonical task list**: The full, never-truncated set of tasks for the
  specification. Entries outside the resolved stage carry the `skipped:` status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can obtain a complete, reviewable planning result and a
  committed stage boundary from a single invocation, with zero implementation-phase
  work performed — verified on 100% of planning-stage runs.
- **SC-002**: A planning stage followed later by an implementation stage produces
  the same end result as one uninterrupted full run, for the same workflow file.
- **SC-003**: An implementation stage resumed in a fresh session, from a different
  working copy, succeeds without any manually re-supplied stage identity,
  phase-completion state, or confidence-gate verdict — 100% of *that* context
  comes from the workflow file. Pull-request marker-plan evidence is excluded from
  this guarantee and continues to follow its already-shipped stop-rather-than-infer
  behavior, unchanged by this specification (see FR-010).
- **SC-004**: Stage auto-detection selects the expected stage on 100% of the
  golden fixture cases covering both the planning-incomplete and
  planning-complete conditions.
- **SC-005**: Every invalid or conflicting stage argument is rejected before any
  phase work begins, so a rejected run leaves no partial phase output — 100% of
  invalid-argument cases.
- **SC-006**: The recorded stage and the workflow file's own phase evidence never
  silently disagree: any contradiction across every workflow file in the tree is
  caught by the automated gate, with no reliance on an agent choosing to run it.
- **SC-007**: Both distributions resolve identical stages for identical inputs
  across the full fixture set, with no case where the two diverge.
- **SC-008**: Gate outcomes are unchanged by this feature — a run that passed or
  failed a given gate before staging existed reaches the same verdict after.

## Assumptions

- **Stage vocabulary is closed at three values.** `plan`, `implement`, and
  full cover the boundary this feature exists to create; no additional stage names
  are introduced, and downstream specs consume these three.
- **The confidence gate belongs to the planning stage.** It sits between analysis
  and implementation, its remediation acts on planning artifacts, and its existing
  stop guidance already tells operators to resume at the implementation phase. A
  planning stage ending on a recorded confidence verdict is what a human checkpoint
  is meant to read.
- **The stage is recorded when it is resolved and again when it completes**, rather
  than being rewritten on every phase transition. Per-phase status entries already
  carry within-stage progress.
- **The mirrored copy in the session state file is derived, not a second source of
  truth.** Only the workflow file is read when deciding a stage; the mirror exists
  for the running session's convenience. This is the shape that prevented the
  earlier drift, where two stores were written with neither designated
  authoritative.
- **Requesting the implementation stage re-runs opening preparation.** That
  preparation is unconditional and cheap, and it re-derives project commands and
  conventions each invocation. Where a value was resolved once per session and a
  baseline was captured at the start of the work, the existing baseline stays
  authoritative for end-of-run comparison.
- **The scaffold-to-autopilot chain contract is documentation only** in this slice;
  the scaffold-side implementation belongs to the downstream spec that consumes it.
- **Both orchestrators can run shell commands.** The permission field that
  previously suggested otherwise is a pre-approval list, not a restriction, so
  shared stage-resolution logic is executable from both distributions.
- **Editing either distribution's skill dirties the generated mirrors, installed
  cache trees, and proof files.** These are regenerated with the repository's
  artifact refresh tooling and verified in continuous integration; documentation
  reference regeneration is a separate step.
- **The Codex skill body has 329 words of headroom** against its enforced cap as
  measured on the current file, which is why the stage prose lives in the
  uncapped referenced document and the skill body receives only the argument line
  and a pointer.
- **Nothing currently compares the two distributions' skill bodies**, so parity
  must come from shared executable logic rather than from a comparison test.

## Dependencies

- The bookkeeping-durability prerequisite is **discharged**. It shipped ahead of
  this specification and released to consumers, and two of its outputs are
  load-bearing here: the state-file-versus-workflow-file contract that establishes
  which store is durable, and the workflow status-evidence validator that this
  specification extends rather than duplicates.
- Enables the downstream ART specifications that consume the stage vocabulary.

## Out of Scope

- Draft-pull-request corroboration for stage auto-detection — deferred to the
  downstream spec that creates the draft pull requests it would corroborate
  against. During this specification no such pull requests exist, so only the
  absent branch would be exercised.
- Draft-pull-request creation, the review feedback sweep, and the scaffold-side
  chain implementation, each owned by a named downstream specification.
- Any change to what a gate passes or fails on. Gate semantics are untouched;
  only which stage owns the confidence gate is decided here.
- Truncating the canonical task list per stage.
- Per-agent user override features.
- New shell-script dependencies. Repository tooling stays on the Python standard
  library.
