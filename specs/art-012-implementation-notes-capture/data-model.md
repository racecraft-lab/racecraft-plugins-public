# Data Model: Implementation-Notes Capture (ART-012)

**Date**: 2026-08-10 | **Plan**: `specs/art-012-implementation-notes-capture/plan.md`

Three entities, all of them plain text. Nothing here is a schema in the machine
sense: spec.md's Assumptions state that downstream consumers read the record as
plain readable text, and no schema version or parser contract is shipped. What
follows is the fixed shape the Layer 4 test asserts and the two platform
documents must describe.

---

## 1. Implementation-Notes Record

The per-spec durable record of what happened during the implement phase.

| Property | Value |
|---|---|
| Location | `specs/<feature-dir>/.process/implementation-notes.md`, one per spec |
| Encoding | UTF-8, LF line endings, trailing newline |
| Owner | The autopilot orchestrator, Phase 7 |
| Consumers | ART-010's PR writeup; the optional retrospective extension. Both read it as text. |
| Classification | Exhaust. Nothing depends on it to make progress. |

**Composition**: exactly one Header, followed by zero or more Notes Entries in
the order the orchestrator collected them.

**Validation rules**

| Rule | Source |
|---|---|
| The header appears exactly once, as the file's first line. | FR-002 |
| The record exists before the first task is dispatched. | FR-002, SC-002 |
| An existing record is re-opened, never truncated and never given a second header. | FR-002, US1 scenario 7 |
| Content is only ever appended. No entry is rewritten, reordered, or removed. | FR-003, SC-005 |
| Entry count equals the number of dispatched task attempts the orchestrator collected. | SC-001 |
| A failure to create or append is a recorded gap, not a phase outcome change. | FR-004, SC-004 |

**Lifecycle**

| From | Event | To |
|---|---|---|
| Absent | Phase 7 starts | Header only |
| Header only | Phase 7 is interrupted before any run is collected | Header only, and that is the correct terminal state |
| Header only, or Header + N entries | A singly or sequentially dispatched attempt completes | Header + N+1 entries |
| Header only, or Header + N entries | A parallel run of k tasks is collected | Header + N+k entries, written before the next run dispatches |
| Header + N entries | Phase 7 resumes from a partial run | Header + N entries, then appended to |

There is no delete transition and no truncate transition. A spec whose tasks
completed never has an absent or entry-less record (SC-003).

---

## 2. Notes Entry

One block per dispatched task attempt.

| Field | Type | Rule |
|---|---|---|
| Task ID | Heading text | The task's ID exactly as `tasks.md` writes it. Identifies the entry on its own (SC-006). Not unique across the file: a retried task has two entries. |
| Reported text | Free text | The executor's reported deviations, edge cases, and surprises, preserved verbatim, or the literal `None`. |

**Validation rules**

| Rule | Source |
|---|---|
| Every dispatched attempt gets an entry, including routes that emit no task-result block. | FR-003, SC-001 |
| An entry is identified by task ID alone. No marker, phase, or route attribution is embedded. | Design Concept Q7 |
| The field reads exactly `None` when there is nothing to report, whether the executor said `None` or returned no field at all. | FR-003, SC-003, research R6 |
| An entry is immutable once written. A second attempt appends a second entry; the first stays exactly as written. | FR-003, SC-005, Design Concept Q5 |
| Entries appear in collection order, which need not match task-list order. Entries from an earlier run always precede entries from a later one. | spec.md Edge Cases |

**Delimitation**: an entry runs from its own heading to the next entry heading,
or to end of file. That rule is what lets reported text span paragraphs without
bleeding into the neighbouring entry.

The literal format is pinned in
`specs/art-012-implementation-notes-capture/contracts/implementation-notes-record.md`.

---

## 3. Task Result Summary

The summary an executor already returns per task. This feature adds one field
and changes nothing else about it.

| Field | Status |
|---|---|
| `**TDD Evidence:**` | Unchanged |
| `**Test commands used:**` | Unchanged |
| `**Files created/modified:**` | Unchanged |
| `**Errors:**` | Unchanged, and no longer the block's last line |
| `**Deviations/Edge cases/Surprises:**` | **New.** Last line of the block. |

**Validation rules**

| Rule | Source |
|---|---|
| Exactly one combined field, not three separate mandatory fields. | FR-001, Design Concept Q6 |
| It sits inside the existing block. No second reporting block is introduced. | FR-001, Design Concept Q6 |
| It reads `None` when the executor has nothing to report, rather than being omitted. | FR-001, US2 scenario 2 |
| Both supported agent platforms receive an identical reporting contract. | FR-001, US2 scenario 3 |
| Every existing line of the block keeps its text and its position. | Research R2 |

The literal format and the four touchpoints that carry it are pinned in
`specs/art-012-implementation-notes-capture/contracts/task-result-reporting-field.md`.

---

## Relationships

```text
Task Result Summary  ──(one field, read once)──▶  Notes Entry  ──(append)──▶  Implementation-Notes Record
        │                                              ▲
        │ absent on research and                       │
        └─ verification routes ────────────────────────┘
                    (entry is still written, value `None`)
```

The arrow is one-way and lossy by design. The orchestrator reads the field out
of the summary, writes the entry, and never reads the record back. That is what
keeps appends pure: no read-modify-write, no running counter, and therefore no
failure mode where a corrupted record blocks the next write.
