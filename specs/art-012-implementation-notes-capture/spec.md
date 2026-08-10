# Feature Specification: Implementation-Notes Capture (ART-012)

**Feature Branch**: `art-012-implementation-notes-capture`

**Created**: 2026-08-10

**Status**: Draft

**Input**: User description: "Autopilot's implement stage returns a per-task result summary but nothing captures deviations from the plan, discovered edge cases, or surprises an executor ran into. That information is lost the moment the task summary is read and discarded. Give every implementation executor one combined field in its existing task summary for deviations, edge cases, and surprises, and have the orchestrator append one durable entry per task to a per-spec notes record immediately after each task completes, so the record survives a mid-phase interruption and the downstream PR writeup and retrospective have something real to draw from."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Durable Per-Task Record Survives Interruption (Priority: P1)

The autopilot orchestrator runs the implement phase. Before it dispatches any
task it opens a notes record for the spec with a header naming that spec,
creating it if absent and re-opening it if a previous partial run already
started one. As each task finishes, it writes that task's entry straight into
the record rather than holding results in memory until the phase ends. Where
tasks are dispatched as a parallel group, the orchestrator regains control only
once the whole group returns, so that group's entries are written together at
that point, before the next group is dispatched. If the run is interrupted,
everything from every group already collected is already on disk.

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
   **When** an individually or sequentially dispatched task completes, **Then**
   one entry for that task is appended to the record immediately, identified by
   that task's ID.
3. **Given** a phase with ten sequentially dispatched tasks is interrupted after
   four of them have completed, **When** the record is read afterwards, **Then**
   it contains the header and exactly four entries, one per completed task.
4. **Given** a group of tasks dispatched together as one parallel run, **When**
   that run's results are collected, **Then** every task in the run has its
   entry appended before the next run is dispatched; and **When** the phase is
   interrupted before that run is collected, **Then** the record contains no
   entry for any task in it, including tasks that had already finished.
5. **Given** a task is re-run after an earlier attempt regressed, **When** the
   second attempt completes, **Then** a second entry for that task ID is
   appended and the earlier entry is left exactly as written.
6. **Given** the notes record cannot be written for any reason, **When** the
   phase attempts to create it or append an entry, **Then** a gap is recorded
   and neither the task nor the phase changes its outcome.
7. **Given** a phase is resumed after a partial run left a record with entries
   in it, **When** the resumed phase starts, **Then** the existing record and
   all its entries survive unchanged, no second header is written, and new
   entries are appended after the existing ones.

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
- Several tasks run in parallel and finish out of order. Their entries are
  written together when the orchestrator collects that run, in the order the
  results are collected, which need not match the order the tasks appear in the
  task list. Task IDs, not position, identify the entries. Entries from an
  earlier run always precede entries from a later one, because the next run is
  not dispatched until the previous one has been recorded.
- The phase is interrupted while a parallel run is still in flight. That run
  contributes no entries at all, including for tasks inside it that had already
  finished, because the orchestrator never regained control to write them.
  Every earlier collected run is intact. This is the one place the record is
  lossier than per-task writing would be; it is bounded by a single run.
- A task is dispatched to a path that returns no reporting field at all — a
  verification-only command or a research task, neither of which produces the
  task-result block the field lives in. An entry is still appended, recording
  that nothing was reported, so those tasks are not silently missing.
- The phase is resumed after an earlier partial run. The existing record is
  re-opened and appended to, never truncated and never given a second header.
  A task re-executed by the resumed run appends another entry, which is the
  same accurate-history behavior a retry produces.
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
- **FR-002**: Before it dispatches any task, the implement phase MUST ensure the
  spec's implementation-notes record exists, carrying a header that identifies
  the spec. If no record exists, it MUST be created with that header. If a
  record already exists — the case when a phase is resumed after a partial run —
  it MUST be re-opened and appended to. The phase MUST NOT truncate an existing
  record and MUST NOT re-emit the header into it.
- **FR-003**: The orchestrator MUST append exactly one entry per completed task
  attempt to the record, under a fixed per-task heading with structured fields,
  identified by task ID alone and carrying that task's reported field. "Each
  task attempt" means every attempt the orchestrator dispatched, whichever agent
  or direct command executed it — including attempts whose executor returns no
  reporting field at all, whose entries record that nothing was reported.
  Timing depends on how the attempt was dispatched:
  - Dispatched singly or as part of a sequential run: the append MUST happen
    immediately after that attempt completes.
  - Dispatched as part of a parallel run: the append MUST happen no later than
    the orchestrator's next turn after that run — the point at which it regains
    control over any of that run's results — and MUST complete before the next
    run is dispatched.

  Writes MUST be additive only: a re-run task appends a further entry, and no
  entry already written MUST be rewritten, reordered, or removed.
- **FR-004**: Any failure to create the record or to append an entry MUST be
  recorded as a gap in the run's durable, operator-visible record of the run,
  and MUST NOT change the outcome of the task or of the phase.
- **FR-005**: Both supported agent platforms MUST produce the same *record*:
  the same header, the same per-task entry format, and the same additive-only
  and fail-open behavior of FR-002 through FR-004. The *moment* of append MAY
  differ where the platforms' dispatch mechanics differ. Identical instructions
  are not required and are not achievable: one platform collects a parallel run
  at a barrier while the other harvests each result as it arrives, so parity is
  owed on the artifact, not on the wording.

### Reviewability Notes *(if applicable)*

- No reviewability exception is claimed. The slice is within budget on every
  dimension, so no `refactor`, `infra`, or `upgrade` provenance applies.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: N/A — the second agent platform's mirror is
  the same harness/adapter surface expressed twice, not a distinct surface.
- **Projected reviewable LOC**: 155 (modify-weighted; excludes tests, docs, and
  generated artifacts). Advisory estimator re-run at Clarify with this spec's
  corrected shape — 2 user stories, 5 production files, 4 functional
  requirements, modify-weighted — returns `{"estimated_loc": 155,
  "suggested_slices": 1, "status": "ok"}`.
- **Projected production files**: 5
- **Projected total files**: 8
- **Budget result**: within budget

  *Amended 2026-08-10 (Clarify session 1 consensus).* Scoping recorded 115 LOC
  over 3 production files, on the premise that the per-task Task Result block
  had one authored home. It has three: the shared, injected
  `speckit-pro/skills/speckit-autopilot/references/tdd-protocol.md`, plus
  independent hard-coded copies in `speckit-pro/agents/implement-executor.md`
  and `speckit-pro/codex-agents/implement-executor.toml`. FR-001 requires
  *every* implementation task summary to carry the field, so all three are in
  scope, and the two orchestrator-side files bring the total to 5. The figures
  above are the estimator's verbatim output for the corrected signals, not a
  hand-adjustment of the old ones. Every dimension stays under the warn line
  (400 LOC / 6 production files / 15 total files / 1 primary surface); the two
  added files are further instances of the same harness/adapter surface, so the
  primary-surface count is unchanged.
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

- **SC-001**: After an implement phase in which N dispatched task attempts
  complete, the record contains exactly N entries, and 100% of them are
  identified by a task ID. N counts every dispatched attempt, including
  verification-only and research attempts that carry no reporting field.
- **SC-002**: An implement phase interrupted after k of N task attempts leaves
  a record containing the header and one entry for every attempt whose dispatch
  run the orchestrator had already collected at the moment of interruption —
  exactly k entries when every completed attempt ran singly or sequentially. A
  phase interrupted before any run is collected leaves the header alone.
- **SC-003**: In a run where every executor reports nothing, 100% of entries
  read "None". The record is never absent, and never empty of entries, for a
  spec whose tasks completed.
- **SC-004**: With record writing forced to fail, the task outcomes and the
  phase outcome are identical to a run where writing succeeds, and the failure
  is readable afterwards as a recorded gap in the run's durable,
  operator-visible record — the same place a reader would look to find out what
  the run did.
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
  a second entry, kept as accurate history. The same applies to a resumed
  phase: no detection of already-recorded tasks is needed or wanted, so a task
  re-executed after a resume appends a further entry.
- Scope boundary: making a parallel run's per-task results durable *before* the
  run completes would require changing how the implement phase waits for
  parallel work, which is dispatch machinery this feature does not touch. It is
  named here as deferred follow-up work rather than absorbed into this spec.
- The fail-open precedent this spec follows is recorded intent rather than
  shipped code: the sibling specs whose artifact generation is described as
  fail-open are themselves not yet implemented. The behavior is still the right
  one, but it is being established here rather than copied from a working
  example.
- Scope boundary: the behavior of the optional retrospective extension, a
  second downstream consumer of this record, is out of scope here.
