# Implementation Plan: Implementation-Notes Capture (ART-012)

**Branch**: `art-012-implementation-notes-capture` | **Date**: 2026-08-10 | **Spec**: `specs/art-012-implementation-notes-capture/spec.md`

**Input**: Feature specification from `specs/art-012-implementation-notes-capture/spec.md`

## Summary

Autopilot's implement phase already returns a structured `## Task Result: <TASK_ID>`
summary for every task, and already throws away everything in it the moment the
orchestrator reads it. This feature adds one field to that summary and one
durable file to catch it.

The change is two halves of a single thin slice, both expressed as instruction
text in the plugin's Markdown and TOML surface rather than as code:

1. **Executor reporting contract.** A new
   `**Deviations/Edge cases/Surprises:**` line becomes the last line of the Task
   Result block, reading `None` when there is nothing to report. The block has
   three authored homes and one of them states the contract twice, so this is
   four touchpoints across three files (research R1).
2. **Orchestrator append contract.** Phase 7 opens
   `specs/<feature-dir>/.process/implementation-notes.md` with a header before
   it dispatches anything, creating it only if absent, then appends one
   fixed-heading entry per dispatched task attempt at three routing call sites.
   Appends are additive only and fail open. This lands in both platforms'
   phase-execution reference documents (research R3, R4, R5, R7).

A new Layer 4 unit test pins the record format, the entry format, the field's
position after `**Errors:**`, and the create-if-absent rule across all five
files. Because all five ship as plugin payload, the work is not complete until
the install payloads and the installed-cache proof are regenerated (research
R9).

Nothing here changes how Phase 7 dispatches or how long it waits before its
verification barrier. Workers are still spawned together and the post-run
TYPECHECK + UNIT_TEST safety net still runs where it always did. What changes is
only when each notes entry is written: on the turn that worker's own result
arrives, because the platform delivers background-subagent completions and
teammate reports per worker rather than as a batch.

## Technical Context

**Language/Version**: Markdown instruction and reference documents plus one TOML
agent definition, all shipped as plugin payload. Verification is Python 3.11+
standard library only. No application code and no new runtime dependency.

**Primary Dependencies**: None at runtime. The orchestrator and the executors
are language models following these documents, not scripts interpreting them.
Build and verification use `python3 scripts/refresh-release-artifacts.py` and
`python3 tests/speckit-pro/run-all.py`, both standard library.

**Storage**: One plain UTF-8 Markdown file per spec at
`specs/<feature-dir>/.process/implementation-notes.md`. Append-only. No
database, no schema version, no parser contract.

**Testing**: `python3 tests/speckit-pro/run-all.py` (Layers 1, 4, 5, zero
failures). The new coverage is one Layer 4 unit test registered in
`tests/speckit-pro/suite-manifest.json`. Layer 1 payload validators catch a
missed payload rebuild; the Layer 4 gates test catches a stale installed-cache
proof hash.

**Target Platform**: The speckit-pro plugin on both supported agent runtimes,
Claude Code (`speckit-pro/skills/`, `speckit-pro/agents/`) and Codex CLI
(`speckit-pro/codex-skills/`, `speckit-pro/codex-agents/`).

**Project Type**: Agent-plugin instruction surface. Single primary review
surface: harness/adapter.

**Performance Goals**: Not applicable. The added work is one small file append
per dispatched task attempt, ordered inside a loop that already waits on
model-latency-bound agent dispatches.

**Constraints**: Modify-only on the five production files; no new template or
schema file. Appends are additive only, never a read-modify-write. Failure to
write is fail-open and must not change any task or phase outcome. Parity is owed
on the produced record, not on identical wording, because the two platforms'
dispatch mechanics differ (FR-005). Generated payloads and installed-cache
proofs are regenerated, never hand-edited.

**Scale/Scope**: 5 production files modified across 4 reporting-contract
touchpoints and 2 orchestrator touchpoints, 1 new test, 1 manifest
registration, 1 regenerated docs reference page, plus the generated payload and
proof surfaces listed below.

**Reviewability Budget**: Primary surface harness/adapter; 162 projected
reviewable LOC (modify-weighted); 5 production files; 8 total files; within
budget on every dimension.

## Declared File Operations

Eight tracked files change, five of them production. The two orchestrator files
are a source and its platform mirror; the three reporting-contract files are the
shared injected template plus the two agent definitions that hard-code their own
copy of it.

- MODIFIED speckit-pro/skills/speckit-autopilot/references/tdd-protocol.md
- MODIFIED speckit-pro/agents/implement-executor.md
- MODIFIED speckit-pro/codex-agents/implement-executor.toml
- MODIFIED speckit-pro/skills/speckit-autopilot/references/phase-execution.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md
- NEW tests/speckit-pro/unit/test-implementation-notes-record.py
- MODIFIED tests/speckit-pro/suite-manifest.json
- MODIFIED docs-site/src/content/docs/reference/tests.md

**Generated surfaces that change as a consequence.** These are outputs, not
edits. They are excluded from the counts above because the repository forbids
hand-editing them and the reviewability budget excludes generated artifacts.
Regenerate them; never author them.

* `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/` payload copies of the
  five production files.
* `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/{claude,codex}/speckit-pro/`,
  refreshed from `dist/`.
* The `source_payload_tree_hash` values in
  `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and its
  byte-identical mirror
  `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json`.

All three are regenerated by one idempotent command,
`python3 scripts/refresh-release-artifacts.py`. Not
`python3 scripts/build-plugin-payloads.py` on its own: that builder covers the
payload surface only and leaves the fixtures and the proof hashes stale
(research R9).

**Reading the estimator's output.** `estimate-reviewable-loc` will report
`production: 0`, `projected: 0`, `status: pass`, `greenfield: false` for this
block. That is a heuristic mismatch, not a measurement: the helper counts a file
as production only when its path starts with `src/`, `app/`, `lib/`, or
`scripts/`, or ends in a JavaScript, TypeScript, or SQL extension, and this
repository's plugin surface is Markdown and TOML under `speckit-pro/`. The
authoritative figure is 162, from `estimate-spec-size` with this spec's
corrected signals. Research R11 records the full reasoning so a later phase does
not read `projected: 0` as either a pass to celebrate or a bug to fix.

## Constitution Check

*GATE: evaluated before Phase 0 research and re-evaluated after Phase 1 design.
Both evaluations pass. Constitution v1.2.0.*

| Principle | Requirement as it applies here | Verdict |
|---|---|---|
| I. Plugin Structure Compliance | No new component. Existing agents, skills, and references keep their layout; the new test lives under `tests/speckit-pro/unit/`, outside the install-facing plugin directory. | Pass. Gate: `run-all.py --layer 1`. |
| II. Cross-Platform Runtime & Script Safety | Both platforms get the contract. No Bash and no `jq` is added anywhere. The new test is Python 3.11+ standard library. Parity is owed on the produced record, not on identical wording, per FR-005 and research R10. | Pass. Gate: `run-all.py --layer 4`, plus `validate-codex-skills` and `validate-codex-parity` at Layer 1. |
| III. Semantic Versioning | No manual version edit. release-please owns the bump. | Pass, not exercised. |
| IV. Test Coverage Before Merge | One new Layer 4 unit test under `tests/speckit-pro/unit/`, declared in `tests/speckit-pro/suite-manifest.json` as principle IV requires. Regenerated payloads must pass Layer 1 structural validation. | Pass. Gate: `python3 tests/speckit-pro/run-all.py`, zero failures, count above the recorded 7226 baseline. |
| V. Conventional Commits | PR title and commits follow `type(scope): description` with scope `speckit-pro`. | Pass, verified at PR time. |
| VI. KISS, Simplicity & YAGNI | One combined field, not a taxonomy of three. One literal `None` value covering both empty cases rather than a second marker or a route field (research R6). No summary counter, no marker attribution, no second reporting block. No new file format, no schema, no version stamp. | Pass. |

**Reviewability budget, per the constitution's plan requirement.**

* Primary review surface: harness/adapter. No secondary surface. The second
  platform's mirror is the same surface expressed twice, not a distinct one.
* Within budget on every dimension: 162 reviewable LOC against a 400 warn line
  and an 800 block line; 5 production files against warn 6 and block 8; 8 total
  files against warn 15 and block 25; 1 primary surface.
* Split decision: one spec, no split. The slice is already a single vertical
  path, reporting contract to orchestrator append to consumer hand-off, with no
  horizontal layering to cut along. No follow-up spec ID is owed for a split.
* Per-task durability inside a parallel run is delivered here, not deferred.
  An earlier draft deferred it on the belief that a parallel run's results
  arrived as one batch; the platform documentation says otherwise, and the
  behaviour was observed directly. See the Design Concept's Q2 revision note 2.
  Delivering it required no change to dispatch machinery — only to when each
  entry is written, plus the teammate report obligation of FR-006.
* PR review packet source: `specs/art-012-implementation-notes-capture/spec.md`
  (what changed, why, non-goals, scope budget, traceability), this plan (review
  order and verification), and `specs/art-012-implementation-notes-capture/quickstart.md`
  (verification evidence). Known gaps and rollback notes come from the fail-open
  design: the feature has no flag and needs none, because reverting the five
  file edits removes it completely and leaves no state behind.

## Project Structure

### Documentation (this feature)

```text
specs/art-012-implementation-notes-capture/
├── plan.md                              # This file
├── research.md                          # Phase 0 decisions R1-R11
├── data-model.md                        # Phase 1 entities
├── quickstart.md                        # Phase 1 verification guide
├── contracts/
│   ├── task-result-reporting-field.md   # The executor-side field
│   └── implementation-notes-record.md   # The orchestrator-side record
├── spec.md                              # Contract artifact (Specify phase)
├── SPEC-MOC.md                          # Spec map
├── checklists/                          # Phase 4 output
└── tasks.md                             # Phase 5 output, not created here
```

### Source Code (repository root)

```text
speckit-pro/
├── agents/
│   └── implement-executor.md            # Summary Format template + Terminal
│                                        # Deliverable enumeration (2 touchpoints)
├── codex-agents/
│   └── implement-executor.toml          # Summary Format template (1 touchpoint)
├── skills/speckit-autopilot/references/
│   ├── tdd-protocol.md                  # Shared injected Summary Format
│   └── phase-execution.md               # Phase 7 lifecycle + append call sites
└── codex-skills/speckit-autopilot/references/
    └── phase-execution-codex.md         # Codex mirror of the same two steps

tests/speckit-pro/
├── suite-manifest.json                  # Layer 4 registration for the new test
└── unit/
    └── test-implementation-notes-record.py   # New Layer 4 coverage

dist/                                    # Generated install payloads, rebuilt
docs-site/src/content/docs/reference/    # Generated test reference, regenerated
```

**Structure Decision**: No new directory and no new module. Every production
change is an in-place edit to an existing plugin file, matching the repository's
Markdown-plus-TOML instruction surface. The two-directory split between
`skills/` and `codex-skills/`, and between `agents/` and `codex-agents/`, is the
repository's existing platform-mirror convention; this feature follows it rather
than introducing a shared include, because `phase-execution.md` has never been
shared the way `tdd-protocol.md` is.

## Design Overview

This section states what the implementation must produce. The literal strings
live in `contracts/`, and the entity definitions in `data-model.md`; both are
the authority for the Layer 4 test's assertions.

### Executor reporting contract (US2, FR-001)

Append one line to the Task Result block, after `**Errors:**`, making it the
block's last line:

```text
**Deviations/Edge cases/Surprises:** None (or describe)
```

Four touchpoints, three files, listed with their anchors in research R1. The
fourth is the prose enumeration at `speckit-pro/agents/implement-executor.md:164`,
which names exactly four required fields and must name five after this change.
Patching the templates and leaving that line is the one partial fix that passes
CI green and still breaks FR-001.

### Orchestrator file lifecycle (US1, FR-002)

At the very start of Phase 7, before any task is dispatched, both
phase-execution documents gain a step that ensures
`<FEATURE_DIR>/.process/implementation-notes.md` exists:

* Absent: create `<FEATURE_DIR>/.process/` if that directory is not there
  either, then create the file with the single-line header
  `# Implementation Notes: <SPEC_ID>`. An absent directory is a thing to create,
  not a failure to report.
* Present: leave every existing byte as found. Do not truncate. Do not write a
  second header. This is the resume case. "Present" means the file is at that
  path in the working copy this run executes in. The check is the path itself,
  never a state file and never anything carried from the session that wrote it,
  so a fresh session resumes exactly as the original one would.
* Failure: record a gap in the workflow file, do not retry, and continue.

### Orchestrator append contract (US1, FR-003)

Both phase-execution documents gain append instructions at three call sites in
the Phase 7 Step 3 routing. The table's fourth row is a value case on the first
call site, not a fourth site:

| Route | Emits a Task Result block? | Entry value |
|---|---|---|
| Implementation executor (default fallback and test tasks) | Yes | The executor's reported text, or `None` |
| Research task routed to `domain-researcher` | No | `None` |
| Verification task run orchestrator-direct | No | `None` |
| Executor that omitted the field, or returned it unreadable | Yes, but incomplete | `None` |

One cadence, every dispatch shape:

* **Append on arrival.** Whenever an attempt's own result reaches the
  orchestrator, that attempt's entry is written before anything else is
  dispatched or answered. This is identical for a singleton, a sequential run,
  and a member of a parallel run — a parallel run's members report
  independently, so there is nothing to wait for.
* **Never on a bare idle signal.** A worker that stops without delivering a task
  summary has not produced a result. Treat that as a cue to request the summary;
  appending on it would write an empty entry and would double-count an attempt
  when the worker is later woken and finishes.
* **Serial re-run after a regression**: unchanged, and it appends a second entry
  under the same task ID rather than touching the first.

Writes are additive only. No entry already written is rewritten, reordered, or
removed, which is what makes SC-005 checkable. Each entry is also written
independently of every other. An append that fails costs that one entry: every
other attempt's entry is still written as its own result arrives, and the next
dispatch still happens.

### Failure behavior (FR-004)

Any failure to create the record or append an entry is recorded as a gap in the
run's workflow file at `docs/ai/specs/.process/<SPEC_ID>-workflow.md` and
changes no task or phase outcome. That file is the destination for every gap
this feature records; it is never the implementation-notes record, which is the
file that just failed. The record is exhaust; nothing downstream depends on it
to make progress.

Four properties make the fail-open path safe to rely on.

* **The gap is identifiable.** It names the task ID whose append failed, or the
  lifecycle step when creation failed, plus which operation failed. Without
  that, SC-004's "readable afterwards" cannot be checked against anything.
* **The write is not retried.** One attempt, then the gap. A retry ladder on a
  file the phase does not depend on is the one way this path could stall the
  phase it exists to protect, so there is none.
* **The fallback is one level deep.** Recording the gap is itself fail-open. If
  the workflow file is the unwritable path, the orchestrator surfaces that
  second failure in its own run output and carries on. It does not try a third
  destination, retry, or escalate, so the failure path cannot recurse.
* **Failures do not spread.** Each append stands alone. A failure recorded for
  one attempt does not stop any other attempt's entry from being appended, and
  does not stop the next dispatch.

This shape matches the repository's existing failure semantics rather than
inventing one. `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md`
handles a failed item by surfacing that item and explicitly not blocking the
rest of its batch, and
`speckit-pro/agents/uat-runbook-author.md` requires its fail-open path to never
error in a way that would block the step it precedes.

### Platform parity (FR-005)

Both platforms produce the same header, the same entry format, the same
per-arrival timing, and the same additive-only and fail-open behavior. Codex
already harvests each result as it arrives, so its document needs only the
append instruction, not a cadence change. Claude's document gains the same
per-arrival instruction on both of its parallel paths. Parity now holds in the
strong direction: neither platform is capped to the weaker of the two.

Within Claude, the two parallel paths need different wiring for the same
outcome. Background subagents return their summaries to the orchestrator, so
their arrival is the trigger directly. Agent Teams teammates are independent
sessions that report to each other, not to the caller, so FR-006 requires them
to be told at dispatch to send their task summary to the lead on completion;
the lead appends on that message. Without it the record would be structurally
empty on the Teams path while identical on paper.

## Review Order

For a reviewer reading the diff cold:

1. `contracts/task-result-reporting-field.md` and
   `contracts/implementation-notes-record.md` — the two literal formats
   everything else asserts against.
2. The three reporting-contract touchpoint files, smallest first:
   `speckit-pro/skills/speckit-autopilot/references/tdd-protocol.md`,
   `speckit-pro/codex-agents/implement-executor.toml`,
   `speckit-pro/agents/implement-executor.md` (two touchpoints).
3. `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` — the
   lifecycle step and the three append call sites.
4. `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`
   — the same two steps in that platform's terms.
5. `tests/speckit-pro/unit/test-implementation-notes-record.py` and its
   `tests/speckit-pro/suite-manifest.json` registration.
6. Generated surfaces last, as regeneration output only.

## Complexity Tracking

No constitution violation. This table stays empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | — | — |
