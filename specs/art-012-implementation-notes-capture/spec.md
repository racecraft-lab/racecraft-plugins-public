# Feature Specification: Implementation-Notes Capture (ART-012)

**Feature Branch**: `art-012-implementation-notes-capture`

**Created**: 2026-08-10

**Status**: Draft

**Input**: User description: "Autopilot's implement stage returns a per-task result summary but nothing captures deviations from the plan, discovered edge cases, or surprises an executor ran into. That information is lost the moment the task summary is read and discarded. Give every implementation executor one combined field in its existing task summary for deviations, edge cases, and surprises, and have the orchestrator append one durable entry per task to a per-spec notes record immediately after each task completes, so the record survives a mid-phase interruption and the downstream PR writeup and retrospective have something real to draw from."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Durable Per-Task Record Survives Interruption (Priority: P1)

The autopilot orchestrator runs the implement phase. Before it dispatches any
task it opens a notes record for the spec with a header naming that spec. Each
time a task finishes, it writes one entry for that task straight into the
record, rather than holding the results in memory until the phase ends. If the
run is interrupted halfway through, everything learned up to that point is
already on disk.

**Why this priority**: This is the durability the whole feature exists to
deliver. Without it, deviations discovered during implementation vanish when
the phase ends or the run is interrupted, and the downstream writeup has
nothing to read. The reporting field in User Story 2 has no value until there
is somewhere durable for its content to land.

**Independent Test**: Run the implement phase for a spec with several tasks,
interrupt it partway, and inspect the record. It exists, carries its header,
and holds exactly one entry per task that completed before the interruption.
This can be exercised with the reporting field of User Story 2 absent, in
which case each entry simply records that nothing was reported.

**Acceptance Scenarios**:

1. **Given** the implement phase is about to start and no notes record exists
   for this spec, **When** the phase begins, **Then** the record exists with a
   header identifying the spec, before any task has been dispatched.
2. **Given** the implement phase is running with the record already created,
   **When** an individual task completes, **Then** one entry for that task is
   appended to the record immediately, identified by that task's ID.
3. **Given** a phase with ten tasks is interrupted after four of them have
   completed, **When** the record is read afterwards, **Then** it contains the
   header and exactly four entries, one per completed task.
4. **Given** a task is re-run after an earlier attempt regressed, **When** the
   second attempt completes, **Then** a second entry for that task ID is
   appended and the earlier entry is left exactly as written.
5. **Given** the notes record cannot be written for any reason, **When** the
   phase attempts to create it or append an entry, **Then** a gap is recorded
   and neither the task nor the phase changes its outcome.

---

### User Story 2 - One Reporting Field, No Second Format (Priority: P2)

An implementation executor finishes its task and writes the summary it already
writes today. That summary now carries one more field, alongside the fields it
already reports, holding anything worth knowing: where the work deviated from
the plan, what edge cases turned up, what was surprising. When the task went
exactly as planned, the executor writes the single word "None" there. The
executor learns no second reporting format and fills in no second block.

**Why this priority**: This is what gives the record content worth reading, but
it depends on User Story 1 having somewhere to put that content. It is second
because a record of task IDs with nothing reported is still a working record;
a stream of well-written deviation reports with nowhere durable to land is not.

**Independent Test**: Dispatch a single implementation task and inspect the
summary it returns. The combined deviations field is present, sits inside the
existing task-result block rather than a new one, and reads "None" when the
task was uneventful.

**Acceptance Scenarios**:

1. **Given** an executor completes a task that deviated from the plan, **When**
   it writes its task summary, **Then** the summary contains one combined field
   describing the deviations, edge cases, and surprises, inside the existing
   task-result block.
2. **Given** an executor completes a task with nothing at all worth reporting,
   **When** it writes its task summary, **Then** the same field is present and
   reads "None" rather than being left out.
3. **Given** the same task is dispatched on either supported agent platform,
   **When** the executor writes its task summary, **Then** the reporting
   contract it follows is identical on both.

---

### Edge Cases

- The implement phase is interrupted before any task completes. The record
  still exists and holds its header alone, so "the run stopped early" is
  distinguishable from "this feature never ran".
- The spec has no implementation tasks at all. The same header-only record is
  produced, for the same reason.
- Writing the record fails: the containing directory is missing, the path is
  not writable, or the disk is full. The failure is recorded as a gap and the
  task and the phase carry on unaffected.
- A task is re-run after an earlier attempt regressed. Two entries carry the
  same task ID, the first showing the failed attempt and the second the
  successful one, and both are kept as history.
- Several tasks run in parallel and finish out of order. Entries appear in the
  order tasks completed, which need not match the order they appear in the
  task list. Task IDs, not position, identify the entries.
- An executor omits the reporting field entirely. An entry for that task is
  still appended, recording that nothing was reported, so no task is silently
  missing from the record.
- Reported text spans multiple paragraphs or contains markdown headings. The
  entry's own fixed heading still delimits it unambiguously from the entries
  either side.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every implementation task summary MUST carry exactly one combined
  field reporting deviations from the plan, discovered edge cases, and
  surprises. That field MUST sit inside the existing per-task result block, no
  second reporting block MUST be introduced, and the field MUST read "None"
  when the executor has nothing to report. Both supported agent platforms MUST
  receive an identical reporting contract.
- **FR-002**: The implement phase MUST create the spec's implementation-notes
  record, carrying a header that identifies the spec, before it dispatches any
  task.
- **FR-003**: Immediately after each task completes, the system MUST append
  exactly one entry for that task to the record, under a fixed per-task heading
  with structured fields, identified by task ID alone and carrying that task's
  reported field. Writes MUST be additive only: a re-run task appends a further
  entry, and no entry already written MUST be rewritten, reordered, or removed.
- **FR-004**: Any failure to create the record or to append an entry MUST be
  recorded as a gap and MUST NOT change the outcome of the task or of the
  phase.

### Reviewability Notes *(if applicable)*

- No reviewability exception is claimed. The slice is within budget on every
  dimension, so no `refactor`, `infra`, or `upgrade` provenance applies.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: N/A — the second agent platform's mirror is
  the same harness/adapter surface expressed twice, not a distinct surface.
- **Projected reviewable LOC**: 115 (modify-weighted; excludes tests, docs, and
  generated artifacts). Advisory estimator run with this spec's final shape —
  2 user stories, 3 production files, 4 functional requirements,
  modify-weighted — returns `{"estimated_loc": 115, "suggested_slices": 1,
  "status": "ok"}`, reproducing the figure recorded in the technical roadmap
  and the Design Concept.
- **Projected production files**: 3
- **Projected total files**: 6
- **Budget result**: within budget
- **Split decision**: Remains one spec. The scope is already a single thin
  vertical slice — executor reporting contract, then orchestrator append, then
  hand-off to the downstream consumer — with no horizontal layering to cut
  along. The estimate sits far under the 400 reviewable-LOC ceiling and the
  estimator suggests one slice.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Implementation-Notes Record**: The per-spec durable record of what happened
  during implementation, held as plain readable text under the feature's
  process directory. It opens with a header naming the spec and is followed by
  entries in the order tasks completed. It is exhaust: downstream consumers
  read it, nothing depends on it to make progress.
- **Notes Entry**: One fixed-heading block per completed task attempt. Carries
  the task ID and the text that task's executor reported for deviations, edge
  cases, and surprises. Entries are never edited after they are written, so a
  task attempted twice has two entries.
- **Task Result Summary**: The summary an executor already returns for each
  task, covering test evidence, files touched, and errors. This feature adds
  one combined reporting field to it and changes nothing else about it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After an implement phase in which N task attempts complete, the
  record contains exactly N entries, and 100% of them are identified by a task
  ID.
- **SC-002**: An implement phase interrupted after k of N task attempts leaves
  a record containing the header and exactly k entries; a phase interrupted
  before any task completes leaves the header alone.
- **SC-003**: In a run where every executor reports nothing, 100% of entries
  read "None". The record is never absent, and never empty of entries, for a
  spec whose tasks completed.
- **SC-004**: With record writing forced to fail, the task outcomes and the
  phase outcome are identical to a run where writing succeeds, and the failure
  is visible as a recorded gap.
- **SC-005**: Across a full run, no entry's text changes after it is written:
  the record read at any later moment still begins with everything it contained
  earlier, byte for byte.
- **SC-006**: A reader can recover the task ID and reported text of every entry
  from the record's headings alone, with no lookup against any other file.

## Assumptions

- The Design Concept at `docs/ai/specs/.process/ART-012-design-concept.md`
  (questions Q1 through Q8) is the source of truth for every scoping decision
  here, and its answers are treated as settled.
- The implement phase already dispatches tasks individually and already
  receives a structured per-task result summary from each executor. This
  feature extends that existing contract rather than creating it.
- The feature's process directory, `specs/<feature-directory>/.process/`, is
  the established home for autopilot exhaust, and the notes record belongs
  there alongside it.
- Downstream consumers read the record as plain readable text. No machine
  schema, schema version, or parser contract is defined or shipped here.
- Both supported agent platforms receive the reporting contract through the
  shared mechanism already used to brief every implementation agent, per the
  project's standing convention that both platforms get the same agents.
- Failing open matches how sibling specs in the same roadmap treat their own
  generated artifacts, and the roadmap itself classifies this record as
  exhaust rather than load-bearing output.
- Scope boundary: generating the pull-request writeup is out of scope and
  belongs to ART-010. This feature produces only the raw record ART-010 reads.
- Scope boundary: entries carry no per-marker attribution. A spec split across
  several pull-request markers is recorded flat, and a consumer needing
  per-marker attribution cross-references the task ID against the marker plan
  itself.
- Scope boundary: no running spec-level summary counter is written. The
  per-task "None" entries make the empty case explicit without one, and a
  counter would force every write to read the file back first, which the
  append-only design exists to avoid.
- Scope boundary: retried tasks are not deduplicated. A second attempt appends
  a second entry, kept as accurate history.
- Scope boundary: the behavior of the optional retrospective extension, a
  second downstream consumer of this record, is out of scope here.
