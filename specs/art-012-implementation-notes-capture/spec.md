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
- Writing the record fails: the containing directory cannot be created, the
  path is not writable, or the disk is full. The failure is recorded as a gap,
  the write is not retried, and the task and the phase carry on unaffected.
- The gap itself cannot be recorded, because the destination it would go to is
  unwritable too. Nothing further is attempted, nothing blocks, and the second
  failure shows up only in the run's own output. The fallback stops there, so
  the failure path cannot loop.
- One task's entry fails to append while its parallel run is being collected.
  Every other task in that run is still appended, and the next run is still
  dispatched. One unwritable entry costs one entry, not a run and not a phase.
- A task is re-run after an earlier attempt regressed. Two entries carry the
  same task ID, the first showing the failed attempt and the second the
  successful one, and both are kept as history.
- Several tasks run in parallel and finish out of order. Their entries are
  written together when the orchestrator collects that run, in the order the
  results are collected, which need not match the order the tasks appear in the
  task list. A task ID says which task an entry belongs to; an entry's position
  says when it was recorded, not where its task sits in the task list. Entries
  from an earlier run always precede entries from a later one, because the next
  run is not dispatched until the previous one has been recorded.
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
- An executor omits the reporting field entirely, or returns it in a form the
  orchestrator cannot read out of the summary. An entry for that task is
  still appended, recording that nothing was reported, so no task is silently
  missing from the record. Neither case is a write failure, so neither is
  recorded as a gap.
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
  the spec. If no record exists, it MUST be created with that header, and
  creating it MUST include creating its containing directory when that
  directory is absent, so an absent directory is not by itself a failure. If a
  record already exists — the case when a phase is resumed after a partial run —
  it MUST be re-opened and appended to. Whether a record already exists MUST be
  determined from the record's own path in the working copy the run executes in.
  It MUST NOT depend on a state file, an index, or anything carried over from
  the session that wrote the record, so a resume in a fresh session behaves
  exactly as a resume in the session that started it. The phase MUST NOT
  truncate an existing record and MUST NOT re-emit the header into it.
- **FR-003**: The orchestrator MUST append exactly one entry per completed task
  attempt to the record, under a fixed per-task heading with structured fields,
  identified by task ID alone and carrying that task's reported field. "Each
  task attempt" means every attempt the orchestrator dispatched, whichever agent
  or direct command executed it — including attempts whose executor returns no
  reporting field at all, and attempts whose reported field cannot be read out
  of the summary returned. Both record that nothing was reported. Neither is a
  failure to write, so neither takes FR-004's gap path.
  Timing depends on how the attempt was dispatched:
  - Dispatched singly or as part of a sequential run: the append MUST happen
    immediately after that attempt completes.
  - Dispatched as part of a parallel run: the append MUST happen no later than
    the orchestrator's next turn after that run — the point at which it regains
    control over any of that run's results — and MUST complete before the next
    run is dispatched.

  Writes MUST be additive only: a re-run task appends a further entry, and no
  entry already written MUST be rewritten, reordered, or removed. Every entry
  MUST be appended after everything already in the record, so the record's
  document order is the order entries were appended, which is the order the
  orchestrator collected the attempts. Entries carry no timestamp and no attempt
  number, so document order is the record's only ordering signal: where two
  entries share a task ID, the earlier-positioned entry MUST be the earlier
  attempt.
- **FR-004**: Any failure to create the record or to append an entry MUST be
  recorded as a gap in the run's durable, operator-visible record of the run,
  which is that record of the run and never the implementation-notes record
  that just failed, and MUST NOT change the outcome of the task or of the
  phase. The gap MUST name the attempt or lifecycle step it belongs to and the
  operation that failed, so a reader can tell which write was lost. A failed
  write MUST NOT be retried. Recording the gap is itself fail-open and has
  exactly one fallback level: if the gap cannot be recorded either, because its
  destination is the unwritable path, the orchestrator MUST surface that second
  failure in its own run output, carry on, and MUST NOT retry, escalate, or
  block. Entries are written independently, so a failure recorded for one
  attempt MUST NOT stop the remaining attempts in the same collection batch
  from being appended, and MUST NOT stop the next run from being dispatched.
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
- **Projected reviewable LOC**: 162 (modify-weighted; excludes tests, docs, and
  generated artifacts). Advisory estimator run against this spec's current shape
  — 2 user stories, 5 production files, 5 functional requirements,
  modify-weighted — returns `{"estimated_loc": 162, "suggested_slices": 1,
  "status": "ok"}`, quoted verbatim.

  *Amendment history, so no reader mistakes a superseded figure for a
  correction.* Scoping recorded 115 over 3 production files, on the wrong
  premise that the per-task Task Result block had one authored home; it has
  three. Clarify session 1 corrected the file count to 5 and the projection to
  155. Clarify session 2 then added FR-005, a platform-parity clause carrying no
  further production file, which moves the projection to 162. Each figure is the
  estimator's own output for the inputs true at the time, never a hand
  adjustment. The verdict never changed: one slice, `ok`, far under the 400 warn
  line.
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
  verification-only and research attempts that carry no reporting field. Where
  creating the record or appending an entry failed and was recorded as a gap
  under FR-004, the gap stands in the record's or the entry's place: an attempt
  whose append failed is excluded from N, and a run whose record could never be
  created is measured by its gaps rather than by this count. A fail-open run is
  not read as a violation of this criterion.
- **SC-002**: An implement phase interrupted after k of N task attempts leaves
  a record containing the header and one entry for every attempt whose dispatch
  run the orchestrator had already collected at the moment of interruption —
  exactly k entries when every completed attempt ran singly or sequentially. A
  phase interrupted before any run is collected leaves the header alone. Where
  creating the record or appending an entry failed and was recorded as a gap
  under FR-004, the gap stands in the record's or the entry's place, so a
  fail-open run is not read as a violation of this criterion.
- **SC-003**: In a run where every executor reports nothing, 100% of entries
  read "None". The record is never absent, and never empty of entries, for a
  spec whose tasks completed. Where creating the record or appending its
  entries failed and was recorded as a gap under FR-004, the gap stands in the
  record's or the entry's place, so a fail-open run is not read as a violation
  of this criterion.
- **SC-004**: With record writing forced to fail, the task outcomes and the
  phase outcome are identical to a run where writing succeeds, and the failure
  is readable afterwards as a recorded gap in the run's durable,
  operator-visible record — the same place a reader would look to find out what
  the run did — naming the attempt or lifecycle step and the operation that
  failed. The same holds with that gap destination also forced to fail: the
  outcomes are still identical, nothing in the run blocks, and the second
  failure is visible in the run's own output.
- **SC-005**: Across a full run, no entry's text changes after it is written:
  the record read at any later moment still begins with everything it contained
  earlier, byte for byte.
- **SC-006**: A reader can recover the task ID and reported text of every entry
  from the record's headings alone, with no lookup against any other file, and
  can recover the order in which entries were recorded from their order in the
  file. Where a task ID appears more than once, reading the record top to bottom
  gives that task's attempts in the order they happened.

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
- Scope boundary: the record has one writer, the orchestrator of the run that
  owns the implement phase, and FR-003's ordering guarantee holds for that one
  writer. The run-state guard deliberately does not block a second run that
  finds one already in progress, so two runs against the same spec could
  interleave their appends. Nothing here coordinates them: no lock, no
  detection of interleaving, and no repair.
- Scope boundary: a resumed run finds an existing record only if the working
  copy it runs in holds one. The run's own checkpoint commits are what carry the
  record between working copies, so entries written since the last checkpoint
  exist only in the copy that wrote them. A resume in a working copy without the
  record takes FR-002's create path and starts a fresh header-only record.
  Earlier entries are neither recovered nor merged in, and no reconciliation
  across working copies is specified.
- Scope boundary: the record's path is stable for exactly as long as the feature
  directory is. Consumers read it in place during the run that produced it,
  before the spec is archived. Archive cleanup removes the feature directory
  from active `specs/`, taking the record with it, after which the record is
  recoverable the way every other artifact in that directory is, through the
  commit history that carried it. This feature copies the record nowhere else
  and maintains no index to it.
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
