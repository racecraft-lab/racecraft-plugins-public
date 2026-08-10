# Contract: Implementation-Notes Record

**Feature**: ART-012 | **Covers**: FR-002, FR-003, FR-004, FR-005, US1,
SC-001 to SC-006 | **Producer**: the autopilot orchestrator, Phase 7 |
**Consumers**: ART-010's PR writeup, the optional retrospective extension

This is the exact file the orchestrator produces. The Layer 4 test asserts that
both platforms' phase-execution documents describe this format and these rules.

## Location

```text
specs/<feature-dir>/.process/implementation-notes.md
```

One per spec, alongside the rest of the feature's autopilot exhaust. UTF-8, LF
line endings, trailing newline.

## Header

Written once, when the record is created, as the file's first line:

```text
# Implementation Notes: <SPEC_ID>
```

`<SPEC_ID>` is the run's spec identifier, for example `ART-012`. Nothing else
goes in the header. It is deliberately minimal, per Design Concept Q8: its job
is to prove the file and its `.process/` directory exist even if the phase never
dispatches a task.

## Entry

One per dispatched task attempt, appended after everything already in the file:

```text
### <TASK_ID>

**Deviations/Edge cases/Surprises:** <reported text, or None>
```

Separated from the preceding content by one blank line.

`<TASK_ID>` is the task's ID exactly as `tasks.md` writes it, for example `T007`.

## Worked example

```text
# Implementation Notes: ART-012

### T001

**Deviations/Edge cases/Surprises:** None

### T002

**Deviations/Edge cases/Surprises:** The Task Result block turned out to have
three authored homes, not one. Patched all three plus the Terminal Deliverable
enumeration.

### T002

**Deviations/Edge cases/Surprises:** None
```

Two `T002` entries is correct, not a defect. The first attempt regressed and the
second succeeded; both are kept as history.

## Rules

### Lifecycle (FR-002)

| Condition at Phase 7 start | Action |
|---|---|
| Record absent | Create it with the header. |
| Record present | Leave every byte as found. Append after the existing content. |

Never truncate. Never write a second header. The present case is a resumed
phase, and its existing entries are the whole point of the feature.

This step runs **before the first task is dispatched**, not lazily on first
append, so an interrupted-before-any-task run still leaves a header-only record.

### Append cadence (FR-003)

| Dispatch shape | When the entry is appended |
|---|---|
| Singly, or as part of a sequential run | Immediately after that attempt's result is read, before the next dispatch |
| Inside a parallel run | When the run is collected, every task in the run, in collection order, before the next run is dispatched |
| Serial re-run after a regression | Immediately, as a further entry under the same task ID |

Never batched to phase end.

### Coverage (FR-003, SC-001)

Every attempt the orchestrator dispatched gets an entry, whichever route
executed it:

| Route | Emits a Task Result block? | Entry value |
|---|---|---|
| Implementation executor | Yes | The executor's reported text, or `None` |
| Research task routed to a researcher agent | No | `None` |
| Verification task run orchestrator-direct | No | `None` |
| Executor that omitted the field | Yes, but incomplete | `None` |

`None` is the single value for every nothing-to-report case. A distinct marker
for "no field returned" would break SC-003, which requires 100% of entries to
read `None` in a run where nothing is reported. Research R6 records the full
reasoning.

### Additive only (FR-003, SC-005)

Writes append. No entry already written is rewritten, reordered, or removed, and
the record is never read back to update a counter or to find a previous entry.
The record read at any later moment still begins with everything it contained
earlier, byte for byte.

### Fail-open (FR-004, SC-004)

A failure to create the record or append an entry is recorded as a gap in the
run's workflow file at `docs/ai/specs/.process/<SPEC_ID>-workflow.md`, and the
task and phase outcomes are exactly what they would have been had the write
succeeded. The record is exhaust; nothing downstream depends on it to make
progress.

### Platform parity (FR-005)

Both platforms produce the same header, the same entry format, and the same
additive-only and fail-open behavior. The *moment* of append may differ where
dispatch mechanics differ: one platform collects a parallel run at a barrier,
the other harvests each result as it arrives and keeps its stronger per-result
cadence. Parity is owed on this file, not on the instruction wording that
produces it.

### Not in this contract

* No per-marker attribution. A consumer needing it cross-references the task ID
  against the marker plan (Design Concept Q7).
* No running spec-level summary or counter. The per-task `None` entries make the
  empty case explicit without forcing every write to read the file first
  (Design Concept Q3).
* No schema version, no machine schema, no parser contract. Consumers read plain
  text.
* No deduplication of retried tasks.

## What the Layer 4 test asserts

1. Both `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` and
   `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`
   describe the record at `.process/implementation-notes.md`, the
   `# Implementation Notes: <SPEC_ID>` header, and the `### <TASK_ID>` entry
   heading carrying the `**Deviations/Edge cases/Surprises:**` field.
2. Both describe the lifecycle step as create-if-absent, and both forbid
   truncating an existing record or writing a second header.
3. Both place the lifecycle step before the first task dispatch in Phase 7.
4. Both describe appends as additive only, with a retry appending a further
   entry rather than replacing one.
5. Both describe the failure path as fail-open with a gap recorded in the
   workflow file.
6. The Claude document describes the two-branch cadence, per-attempt for
   singleton and sequential dispatch and at-collection for a parallel run.
7. Both cover all three routing branches, so research and verification attempts
   are not silently missing from the record.
