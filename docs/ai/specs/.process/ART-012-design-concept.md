---
topic: "Implementation-Notes Capture: durable deviations record for the implement stage"
slug: "art-012-design-concept"
date: "2026-08-10"
mode: "setup"
spec_id: "ART-012"
source_input:
  type: "topic"
  ref: "ART-012 scope description from docs/ai/specs/html-artifacts-technical-roadmap.md"
question_count: 8
stop_reason: "natural"
---

# Design Concept: ART-012 Implementation-Notes Capture

> **Source:** ART-012 scope in `docs/ai/specs/html-artifacts-technical-roadmap.md`
> **Date:** 2026-08-10
> **Questions asked:** 8
> **Stop reason:** natural (no critical open branches remained)

## Goals

- Every implementation executor reports deviations from plan, discovered edge
  cases, and surprises as part of its existing task summary — one combined
  field, not three mandatory sub-fields.
- The orchestrator durably appends one entry per task to
  `specs/<branch>/.process/implementation-notes.md` — immediately after each
  task completes when that task is dispatched singly or sequentially, and no
  later than its parallel run's collection point otherwise, never batched at
  phase end — so the record survives a mid-phase interruption. See the Q2
  revision note for why the parallel case differs and what it costs.
- A task with nothing to report still gets an entry — its field literally
  reads "None" — so the record is never silently absent for the whole spec.
- The file is created with a header at the start of Phase 7, before any task
  dispatches, so its existence doesn't depend on how far the phase gets.
- A failed append never blocks the task or the phase (fail-open), consistent
  with ART-007's artifact generation and ART-009's UAT artifact in this same
  roadmap.
- The record feeds ART-010's PR writeup and the optional retrospective
  extension — both read it as plain markdown text, not a machine schema.
- Both platforms (Claude, Codex) get identical behavior via the shared
  `tdd-protocol.md` injection mechanism already used for every implementation
  agent, per the project's standing same-agents-both-platforms convention.

## Non-goals

- Generating the PR writeup itself — that's ART-010's job; ART-012 only
  produces the raw record it reads.
- Per-marker attribution in the notes file. Multi-PR specs (via
  `pr_marker_plan`) are not tagged per entry — Q7 decided ART-010 can
  cross-reference task ID against the marker plan itself if it needs that,
  rather than ART-012 duplicating the mapping.
- A separate reporting block. Q6 decided the deviation field extends the
  existing `## Task Result: <TASK_ID>` block in tdd-protocol.md rather than
  adding a second block executors must learn.
- A running spec-level summary counter (e.g. "Deviations reported: 0" at the
  top of the file). Q3 decided the per-task "None" entries already make the
  empty case explicit without breaking pure-append semantics.
- Deduplicating retried tasks. Q5 decided a serial retry after a parallel-run
  regression appends a second entry rather than overwriting the first — kept
  as accurate history, not collapsed.

## Design Tree (Q&A log)

### Q1. What shape should each implementation-notes.md entry take?

**Branch:** Notes-record format

**Recommended answer:** Fixed heading per task, structured fields.
> Mirrors the existing `## Task Result: <TASK_ID>` convention in
> tdd-protocol.md's Summary Format — executors already produce fixed-heading
> blocks, and a Layer 4 fixture test needs something fixed to assert against.

**Alternatives offered:**
- Free prose paragraph per task: reads more naturally but nothing fixed for
  the fixture test or ART-010's extraction to key off.
- Single running bullet log, no per-task structure: loses task traceability
  entirely.

**User's answer:** Fixed heading per task, structured fields (Recommended).

---

### Q2. When should the orchestrator append a task's notes entry to the file?

**Branch:** Append cadence

**Recommended answer:** Immediately after each task completes.
> Durable against a mid-phase interruption, the same concern PRs #416/#417
> fixed for stage state generally during ART-006. A crash after task 5 of 12
> still leaves 5 real entries.

**Alternatives offered:**
- Batched once at the end of Phase 7: simpler, but loses every deviation if
  the run is interrupted before the phase finishes.

**User's answer:** Immediately after each task completes (Recommended).

> **Revision note — 2026-08-10, Clarify session 2 consensus.** The answer above
> stands and is preserved verbatim; what follows fixes a granularity this
> question never reached, and it narrows the guarantee, so read it before
> relying on the "task 5 of 12" line.
>
> Q2 chose between "immediately after each task" and "batched once at the end
> of Phase 7." That axis is unchanged: the chosen side wins, and the rejected
> option's failure mode (losing every deviation when the phase is interrupted)
> stays excluded. What the interview never surfaced is that Phase 7 dispatches
> consecutive `[P]` parallel-safe tasks as one run and gives the orchestrator
> **no turn until the whole run returns** — `phase-execution.md:888` "Wait for
> ALL to complete." and `:875` "Wait for all teammates to complete." on the
> Agent Teams path. So for a parallel run, appending per task is not
> achievable, and no hook exists on either path.
>
> **Revised cadence:** a task dispatched singly or sequentially still appends
> immediately. A task dispatched inside a parallel run has its entry appended
> when that run is collected, before the next run dispatches.
>
> **What this costs, stated plainly:** the "a crash after task 5 of 12 still
> leaves 5 real entries" illustration assumed sequential dispatch. If task 5 is
> the first task of a three-task parallel run, a crash mid-run loses all three,
> including task 5's own finished work. The loss window is bounded by one run
> rather than the whole phase, which is why this is a narrowing rather than a
> reversal — but it is a real narrowing, not a wording tidy-up.
>
> Codex is unaffected and keeps the literal stronger guarantee: its
> `implement-executor` records each result as it arrives
> (`codex-skills/speckit-autopilot/SKILL.md:322`). Making Claude match it would
> mean rewriting Phase 7's parallel wait itself, which is outside this spec's
> budget and Key Files; that is named as deferred follow-up work in spec.md's
> Assumptions instead.

---

### Q3. How should the "no deviations" empty case be recorded, given every task already gets its own fixed-heading entry?

**Branch:** Empty-case semantics

**Recommended answer:** Per-task entry literally reads "None" when nothing to
report.
> No separate whole-file marker needed. A reader scanning for all-"None"
> entries sees the explicit empty case directly, and appends stay pure — no
> re-reading the file to update a running counter.

**Alternatives offered:**
- Per-task "None" entries plus a running spec-level summary line: faster
  at-a-glance read, but every write now reads the whole file first, adding a
  failure mode the append-only design otherwise avoids.

**User's answer:** Per-task entry literally reads "None" (Recommended).

---

### Q4. If the append to implementation-notes.md itself fails, should that block the task/phase?

**Branch:** Failure mode

**Recommended answer:** Fail-open — log a gap, never block.
> Matches ART-007's artifact generation and ART-009's UAT artifact, both
> explicitly fail-open in this same roadmap. The roadmap's own Key Decision
> calls the notes record "exhaust" — a byproduct, not load-bearing for the
> implementation itself.

**Alternatives offered:**
- Fail-closed: treats the record as load-bearing, inconsistent with how the
  roadmap frames it and with the sibling specs' precedent.

**User's answer:** Fail-open (Recommended).

---

### Q5. If a task is re-run (e.g. the Step 3b serial retry after a parallel-run regression), should its second attempt's entry append alongside the first, or replace it?

**Branch:** Retry/dedup semantics

**Recommended answer:** Append a second entry, never overwrite.
> Keeps the pure-append design from Q2/Q3 — overwriting a specific task's
> entry means reading the whole file back to find and replace it. Two entries
> for the same task ID is accurate history (first attempt regressed, second
> succeeded), useful for the retrospective, not noise.

**Alternatives offered:**
- Hold the entry until the task's run is fully settled, write once: cleaner
  (one entry per task, ever) but requires buffering a parallel attempt's
  summary and discarding it on retry — contradicts the "append immediately"
  cadence from Q2.

**User's answer:** Append a second entry, never overwrite (Recommended).

---

### Q6. Where should the reporting instruction live: a new field inside the existing Task Result block, or a separate block?

**Branch:** Field placement / executor reporting contract

**Recommended answer:** New field inside the existing Task Result block.
> Add a `**Deviations/Edge cases/Surprises:**` line to tdd-protocol.md's
> existing `## Task Result: <TASK_ID>` template, next to `**Errors:**`. One
> block to parse instead of two, fits the ~115 LOC modify-weighted budget, and
> rides the existing Layer 1/Codex-parity coverage for that template.

**Alternatives offered:**
- A separate `## Implementation Notes: <TASK_ID>` block: cleaner separation
  of concerns but doubles the parsing surface for a tightly budgeted spec.

**User's answer:** New field inside the existing Task Result block
(Recommended).

---

### Q7. For specs split across multiple PR markers (pr_marker_plan), should each notes entry record which marker its task belongs to?

**Branch:** Marker-plan interaction

**Recommended answer:** No — task ID only, flat file.
> The marker plan already maps task IDs to markers; ART-010 (the consumer)
> can cross-reference task ID against pr_marker_plan.json when it needs
> per-marker attribution. Duplicating that mapping into every notes entry
> grows scope beyond "executor reporting contract → orchestrator append" and
> the roadmap's Key Files don't list marker-aware logic.

**Alternatives offered:**
- Yes, tag each entry with its marker ID: saves ART-010 a cross-reference
  step but couples ART-012 to the marker-plan schema.

**User's answer:** No — task ID only, flat file (Recommended).

---

### Q8. Does specs/<branch>/.process/implementation-notes.md get created with a header the first time Phase 7 starts, or only lazily on the first append?

**Branch:** File lifecycle

**Recommended answer:** Create with a header at Phase 7 start.
> Write a minimal `# Implementation Notes: <SPEC_ID>` header before any task
> dispatches. Guarantees the file and its `.process/` directory exist even if
> the phase is interrupted after zero tasks complete, and gives the fixture
> test a fixed anchor regardless of append count.

**Alternatives offered:**
- Lazy creation on first append: less code, but an interrupted-before-any-
  append run leaves no trace, making "nothing happened yet" indistinguishable
  from "the feature isn't wired up."

**User's answer:** Create with a header at Phase 7 start (Recommended).

## Slice-Sizing (advisory)

Ran `estimate-spec-size` with the spec's scoping signals (2 in-scope user
stories — orchestrator append, executor reporting — 3 production files, 4
FRs, modify-weighted). Operation output, verbatim:
**`{"estimated_loc": 115, "status": "ok", "suggested_slices": 1}`** —
reproducing the roadmap's own 115 figure and well under the 400-LOC warn
ceiling. (An earlier run during the interview fed 1 user story and returned
102/ok/1; corrected here because the spec carries two in-scope stories.) The
scope is already a single thin vertical slice (reporting contract →
orchestrator append → consumer hand-off) with no horizontal layering — no
split warranted, no question asked.

## Open Questions

None — the interview reached a natural stop. Every branch that came up during
the session (format, cadence, empty case, fail-open, retry dedup, marker
tagging, field placement, file lifecycle) was resolved to a specific answer
above.

## Recommended Next Step

Setup mode — this section is informational only. `/speckit-pro:speckit-scaffold-spec`
has already created the worktree and will write the workflow file next, using
the Goals and Q&A log above to enrich the Specify and Clarify prompts.
