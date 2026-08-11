---
description: "Task list for ART-012 Implementation-Notes Capture"
---

# Tasks: Implementation-Notes Capture (ART-012)

**Input**: Design documents from `specs/art-012-implementation-notes-capture/`

**Prerequisites**: plan.md (required), spec.md (required for user stories),
research.md, data-model.md, contracts/, quickstart.md

**Tests**: Test tasks ARE included. Constitution principle IV requires Layer 4
coverage before merge, the workflow's Tasks Prompt names a Layer 4 fixture test
as the verification for this feature, and the Implement Prompt is TDD-first. The
test is written before the production edits it asserts against.

**Organization**: Tasks are grouped by user story so each story can be
implemented, tested, and delivered independently.

**Reviewability**: Generated tasks MUST preserve the spec's reviewability
budget. If task generation expands beyond 400 reviewable LOC, 6 production
files, 15 total files, or more than one primary surface, add an explicit
reviewability checkpoint task before implementation. If it expands beyond
800 reviewable LOC, 8 production files, 25 total files, or more than one
primary surface without a ratified exception, stop and split the spec instead
of adding more implementation tasks.

This list stays inside the recorded budget: **162 projected reviewable LOC**
(modify-weighted), **5 production files**, **8 total tracked files**, **1
primary surface** (harness/adapter). Split decision: one spec, no split. No
reviewability exception is claimed. T001 verifies this before any production
edit.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Plugin source (production)**: `speckit-pro/skills/`, `speckit-pro/agents/`,
  `speckit-pro/codex-skills/`, `speckit-pro/codex-agents/`
- **Repository tests**: `tests/speckit-pro/unit/`, registered in
  `tests/speckit-pro/suite-manifest.json`
- **Generated, never hand-edited**: `dist/claude/`, `dist/codex/`, the
  installed-cache fixture and its proof JSONs, and
  `docs-site/src/content/docs/reference/tests.md`
- Every path in this file is repository-relative. No absolute path.

## Verification Protocol During Implementation

Read this before running any task. It prevents the one mistake this change
invites.

**Per-task GREEN evidence is the single test file plus targeted greps, not the
full suite:**

```bash
python3 tests/speckit-pro/unit/test-implementation-notes-record.py
```

**The full suite is expected to be RED from the first production edit until
T010 completes.** Editing plugin source restales the generated install payloads
(Layer 1 `validate-plugin-payload`, `validate-payload-completeness`,
`validate-payload-conformance`) and the installed-cache proof hashes (Layer 4
gates test). That is the generated-artifact contract working as designed, not a
regression to chase.

**Never repair that redness by hand.** Do not edit `dist/`, do not edit
`tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/`, and
do not edit either proof JSON. T010 regenerates all of it with one command.
`python3 tests/speckit-pro/run-all.py` is T012's job and T012's alone.

**RED verification for T002 and T006**: run the test file directly and confirm
it fails with real assertion errors naming the missing contract, not with an
import error or a file-not-found error.

---

## Phase 1: Setup (Shared Infrastructure)

**No setup tasks.** This is a modify-only change to an existing plugin surface:
no new directory, no new module, no dependency, and no bootstrap. Per AGENTS.md
Worktree Preflight the test suite runs directly in a fresh worktree. The one
install this feature needs, `pnpm --dir docs-site install --frozen-lockfile`,
is scoped to T011, the only task that runs a docs command.

The clean-baseline run (`python3 tests/speckit-pro/run-all.py` = 7226 passed) is
the Implement Prompt's pre-implementation step, already recorded at G0 in
`docs/ai/specs/.process/ART-012-workflow.md`. It is not repeated as a task.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm the scope this task list commits to before any production
file is touched.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T001 Verify the reviewability budget against this task list's file scope and record the split decision in `docs/ai/specs/.process/ART-012-workflow.md` before implementation

**Acceptance criteria**

- The tracked files this list touches match `specs/art-012-implementation-notes-capture/plan.md`'s
  eight Declared File Operations one for one: five production files, one new
  test, one manifest registration, one regenerated docs reference. No task
  introduces a ninth tracked file.
- Every budget dimension is under the warn line: 162 reviewable LOC against 400,
  5 production files against 6, 8 total files against 15, 1 primary surface
  against 1.
- The split decision is recorded as: one spec, no split, no exception claimed
  (`spec.md` Reviewability Notes and Reviewability Budget).
- **Do not invoke `reviewability-gate` in tasks mode.** That mode is deferred on
  the installed runner, per `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`
  (Phase 7: Implement). Record the deferred-mode diagnostics, then read the
  committed fallback evidence chain instead: the setup-mode result recorded in
  the workflow file, the plan-phase `estimate-reviewable-loc` verdict, and the
  operator split decision.
- The plan-phase estimator's `projected: 0` is recorded as a heuristic mismatch,
  not a measurement. Its production-file heuristic recognises only `src/`,
  `app/`, `lib/`, `scripts/` prefixes and JS/TS/SQL extensions, and this surface
  is Markdown and TOML under `speckit-pro/`. The authoritative figure is 162
  (research R11).
- No task in this list crosses a Design Concept non-goal: no per-marker
  attribution (Q7), no running spec-level summary counter (Q3), no second
  reporting block (Q6). Confirm each before proceeding.

**Checkpoint**: Scope confirmed - user story implementation can now begin

---

## Phase 3: User Story 1 - Durable Per-Task Record Survives Interruption (Priority: P1) 🎯 MVP

**Goal**: Phase 7 opens `specs/<feature-dir>/.process/implementation-notes.md`
with a header before it dispatches anything, then appends one entry per
dispatched task attempt, additively and fail-open, on both agent platforms.

**Independent Test**: `python3 tests/speckit-pro/unit/test-implementation-notes-record.py`
passes its record-contract assertion group against both platform documents.
Manually: run autopilot's implement phase for a spec with several tasks,
interrupt it partway, and read the record. It exists, carries its header, and
holds exactly one entry per attempt whose dispatch run was already collected.
This story is verifiable with User Story 2 absent, in which case every entry
reads `None`.

### Tests for User Story 1 ⚠️

> **NOTE: Write this test FIRST and verify it FAILS before implementation**

- [ ] T002 [US1] Create the Layer 4 record-contract test at `tests/speckit-pro/unit/test-implementation-notes-record.py` and register it in `tests/speckit-pro/suite-manifest.json`

**Acceptance criteria**

- Python 3.11+ standard library only, no third-party import (AGENTS.md Editing
  Boundaries, constitution principle II). Follow the shape of
  `tests/speckit-pro/unit/test-reviewability-marker-guidance.py`, the working
  precedent for a Layer 4 test asserting reference-document prose across both
  platform copies of `phase-execution*.md` (research R8).
- Asserts, against both `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`
  and `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`,
  items 1 through 5 and item 7 of "What the Layer 4 test asserts" in
  `specs/art-012-implementation-notes-capture/contracts/implementation-notes-record.md`,
  plus item 6 against the Claude document only. That contract file is the
  authority for every literal string asserted.
- Registered in `tests/speckit-pro/suite-manifest.json` under layer `4` as
  `{"path": "tests/speckit-pro/unit/test-implementation-notes-record.py", "label": "test-implementation-notes-record", "baseline": null}`,
  matching the shape of the neighbouring layer-4 entries. An unregistered test
  is invisible to the runner and never runs.
- The filename describes durable behavior and carries no spec ID.
- **RED verified**: running the file directly fails with real assertion errors
  naming the absent record contract.
- **Registration verified**: `python3 -c "import json; m=json.load(open('tests/speckit-pro/suite-manifest.json')); print([s['label'] for L in m['layers'] if L['id']=='4' for s in L['scripts'] if 'implementation-notes' in s['path']])"`
  prints exactly one label, not an empty list.
- Covers FR-002, FR-003, FR-004, FR-005; SC-001, SC-002, SC-004, SC-005, SC-006.
- Not `[P]`: it is the RED precondition for T003, T004, and T005.

### Implementation for User Story 1

- [ ] T003 [US1] Add the Phase 7 record-lifecycle step to `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`

**Where**: a new step at the start of the Phase 7 section headed
`Phase 7: Implement (Task-Level Dispatch)`, ahead of the
`Step 1: Parse tasks.md` heading, so it runs before any task is dispatched.
Anchor by heading text, not by line number.

**Acceptance criteria**

- Names the record path `<FEATURE_DIR>/.process/implementation-notes.md` and the
  single-line header `# Implementation Notes: <SPEC_ID>`.
- **Create if absent**: when the record is absent, create its `.process/`
  directory if that directory is absent too, then create the file with the
  header. An absent directory is a thing to create, never a failure to report.
- **Never truncate**: when the record is present, leave every existing byte as
  found and append after the existing content. Do not write a second header.
  This is the resumed-phase case, and its existing entries are the point of the
  feature.
- **Existence is checked from the record's own path** in the working copy this
  run executes in. Never from a state file, an index, or anything carried over
  from the session that wrote the record, so a resume in a fresh session behaves
  exactly as a resume in the session that started it.
- Positioned before the first dispatch, so a phase interrupted before any task
  completes still leaves a header-only record, and a spec with no
  implementation tasks produces the same header-only record.
- Failure to create is fail-open: record a gap in
  `docs/ai/specs/.process/<SPEC_ID>-workflow.md` naming the lifecycle step and
  the operation that failed, do not retry, and continue. The task and phase
  outcomes are unchanged.
- Covers FR-002; SC-002, SC-003.
- **Verify**: `python3 tests/speckit-pro/unit/test-implementation-notes-record.py`
  turns the Claude document's lifecycle assertions GREEN. The cadence,
  fail-open, and Codex-document assertions stay RED until T004 and T005.
- Not `[P]`: same file as T004.

- [ ] T004 [US1] Add the Phase 7 append contract to `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`

**Where**: inside the Step 3 heading `Task-Level Execution Loop` and the
`Agent Routing Table` heading that follows it. Four **dispatch-shape** anchors,
which are a different set from the three **routing** call sites in the
acceptance criteria below — the dispatch shape decides *when* an entry is
appended, the routing branch decides *what value* it carries:

1. The singleton and sequential branch that reads `Wait for result.`
2. The parallel background-subagent path that reads `Wait for ALL to complete.`
3. The parallel Agent Teams path that reads
   `Wait for all teammates to complete.` — **do not skip this one.** It is the
   `AGENT_TEAMS_AVAILABLE` branch of the same parallel run, so tasks dispatched
   through it would otherwise produce no entries at all, which SC-001 counts as
   a violation. Both parallel paths converge at the
   `# Safety net for either path` comment, so one append instruction placed at
   that convergence covers both.
4. The serial re-run fallback after a parallel-run regression.

Anchor by that text, not by line number: T003 shifts this file's numbering.

**Acceptance criteria**

- **Entry format**, exactly as pinned in
  `specs/art-012-implementation-notes-capture/contracts/implementation-notes-record.md`:
  a `### <TASK_ID>` heading, a blank line, then
  `**Deviations/Edge cases/Surprises:** <reported text, or None>`, separated
  from the preceding content by one blank line. `<TASK_ID>` is the task's ID
  exactly as `tasks.md` writes it.
- **Three append call sites in the routing, not one**: the implementation
  executor branch, which carries the executor's reported text; the research
  branch routed to `domain-researcher`; and the orchestrator-direct verification
  branch. The latter two never emit a `## Task Result: <TASK_ID>` block, and
  their entries record that nothing was reported. Appending only on the executor
  branch leaves research and verification attempts silently missing, which
  SC-001 counts as a violation.
- **Two-branch cadence**, because the loop has two branches. Dispatched singly
  or as part of a sequential run: append immediately after that attempt's result
  is read, before the next dispatch. Dispatched inside a parallel run: append
  every task in that run when the run is collected, in collection order, and
  always before the next run is dispatched. Never batched to phase end.
- **Serial re-run after a regression**: appends a further entry under the same
  task ID and leaves the earlier entry exactly as written.
- **The literal `None`** is the single value for every nothing-to-report case:
  the executor reported `None`, the executor omitted the field, the field cannot
  be read out of the summary returned, or the route emits no task-result block
  at all. No distinct marker and no route field: a second value would break
  SC-003 the moment a run contains one research task (research R6).
- **Additive only**: no entry already written is rewritten, reordered, or
  removed, and the record is never read back to update a counter or to find a
  previous entry.
- **Ordering**: document order is append order, which is the order the
  orchestrator collected the attempts. Entries carry no timestamp and no attempt
  number, so position is the record's only ordering signal. Where two entries
  share a task ID, the earlier-positioned entry is the earlier attempt.
- **Fail-open, with all four properties.** A failure to append is recorded as a
  gap in `docs/ai/specs/.process/<SPEC_ID>-workflow.md`, never in the
  implementation-notes record that just failed, and it names the attempt and the
  operation that failed so a reader can tell which write was lost. The write is
  not retried: one attempt, then the gap. The fallback is exactly one level
  deep, so if the workflow file is itself the unwritable path the orchestrator
  surfaces that second failure in its own run output and carries on, with no
  third destination, no retry, no escalation, and no recursion. The blast radius
  is one entry: the remaining attempts in the same collection batch are still
  appended, and the next run is still dispatched.
- **A reporting-content problem is not a write failure.** A missing or unreadable
  field produces a `None` entry and takes no gap path.
- **Non-goals held**: no per-marker attribution (Q7), no running summary counter
  (Q3), no second reporting block (Q6).
- Covers FR-003, FR-004; SC-001, SC-003, SC-004, SC-005, SC-006.
- **Verify**: the Claude document's cadence, coverage, additive-only, and
  fail-open assertions turn GREEN. The Codex-document assertions stay RED until
  T005.
- Not `[P]`: same file as T003, and it builds on the step T003 adds.

- [ ] T005 [US1] Mirror the lifecycle and append steps into `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`

**Where**: inside `## Phase 7: Implement` in that file.

**Acceptance criteria**

- Same record path, same header, same `### <TASK_ID>` entry heading, and same
  `**Deviations/Edge cases/Surprises:**` field as T003 and T004.
- Same create-if-absent lifecycle, before the first dispatch, never truncating
  and never writing a second header, with existence determined from the record's
  own path in the current working copy.
- Same three routing branches, same literal `None` for every nothing-to-report
  case, same additive-only rule, and same ordering guarantee.
- Same fail-open contract with all four properties: gap in the workflow file
  naming the attempt or lifecycle step and the failed operation, no retry,
  exactly one fallback level, blast radius of one entry.
- **Cadence wording differs by design.** Codex keeps its existing, stronger
  per-result cadence and does not adopt the Claude document's barrier language,
  which would describe dispatch machinery Codex does not have. FR-005 owes
  parity on the produced record, not on identical wording (research R10).
- Covers FR-002, FR-003, FR-004, FR-005; SC-001 through SC-006 on the Codex
  platform.
- **Verify**: the Codex-document assertions turn GREEN and the whole
  record-contract group passes.
- Not `[P]`: although it is a different file, it must mirror the exact rules
  T003 and T004 land, so it runs after both.

**Checkpoint**: User Story 1 is complete and independently verifiable. The
record-contract test passes on both platforms. The full suite is still RED on
stale generated payloads and proof hashes until T010; that is expected.

---

## Phase 4: User Story 2 - One Reporting Field, No Second Format (Priority: P2)

**Goal**: every authored copy of the `## Task Result: <TASK_ID>` block carries
one new combined reporting field as its last line, and the agent definition that
also enumerates its required fields in prose names five instead of four.

**Independent Test**: `python3 tests/speckit-pro/unit/test-implementation-notes-record.py`
passes its reporting-field assertion group, and quickstart Scenario 1's scoped
grep returns four hits across the three files. Manually: dispatch a single
implementation task and read the summary it returns. The combined field is
present, sits inside the existing task-result block rather than a new one, and
reads `None` when the task was uneventful.

### Tests for User Story 2 ⚠️

> **NOTE: Write these assertions FIRST and verify they FAIL before implementation**

- [ ] T006 [US2] Add the reporting-field assertion group to `tests/speckit-pro/unit/test-implementation-notes-record.py`

**Acceptance criteria**

- Asserts all four items of "What the Layer 4 test asserts" in
  `specs/art-012-implementation-notes-capture/contracts/task-result-reporting-field.md`:
  (1) all three files contain the exact line
  `**Deviations/Edge cases/Surprises:** None (or describe)`; (2) in each file
  that line follows the file's own `**Errors:**` line and is the last field of
  the Task Result block; (3)
  `speckit-pro/agents/implement-executor.md`'s Terminal Deliverable enumeration
  names `Deviations/Edge cases/Surprises` alongside the four existing fields;
  (4) the set of files carrying a `## Task Result: <TASK_ID>` block **under
  `speckit-pro/`** is still exactly those three, so a fourth copy added later
  cannot silently skip the field. Scope that assertion to `speckit-pro/`: a
  tree-wide search also matches the generated `dist/` payload copies and the
  installed-cache fixture copies, so an unscoped "exactly three" fails on a
  clean tree.
- Python 3.11+ standard library only. No new manifest entry: T002 already
  registered this file.
- **RED verified**: running the file directly fails with real assertion errors
  on the absent field, while User Story 1's record-contract group stays GREEN.
- Covers FR-001; SC-003.
- Not `[P]`: same file as T002.

### Implementation for User Story 2

- [ ] T007 [P] [US2] Add the reporting field to the shared Summary Format block in `speckit-pro/skills/speckit-autopilot/references/tdd-protocol.md`

**Acceptance criteria**

- Adds exactly `**Deviations/Edge cases/Surprises:** None (or describe)` as the
  last line of the Summary Format block, immediately after that file's
  `**Errors:** None (or describe)` line, separated by one blank line like every
  other field, inside the existing fenced block.
- Every existing line of the block keeps its exact text and its position. No
  second reporting block is introduced (Design Concept Q6).
- This is the shared copy injected verbatim into every implementation dispatch
  prompt, and the only copy an implementation-routed agent without its own local
  block ever sees. Both platforms reach it through the same mechanism.
- Covers FR-001; User Story 2 acceptance scenarios 1 and 2.
- `[P]`: different file from T008 and T009, with no ordering dependency between
  the three.

- [ ] T008 [P] [US2] Add the reporting field to the Summary Format block in `speckit-pro/codex-agents/implement-executor.toml`

**Acceptance criteria**

- Adds the same exact line in the same position, immediately after that file's
  `**Errors:** None (or describe)` line, inside the Summary Format fence of the
  TOML prompt string.
- One touchpoint only: this file carries no Terminal Deliverable enumeration,
  confirmed by grep (research R1).
- Covers FR-001; User Story 2 acceptance scenario 3, the identical contract on
  both platforms. This is the half of the feature where identical wording both
  is required and is achievable, because the field is a static template line
  rather than a description of dispatch mechanics.
- `[P]`: different file from T007 and T009.

- [ ] T009 [P] [US2] Add the reporting field to both touchpoints in `speckit-pro/agents/implement-executor.md`

**Acceptance criteria**

- **Touchpoint 1, the template**: the same exact line
  `**Deviations/Edge cases/Surprises:** None (or describe)` as the last line of
  the Summary Format block, immediately after that file's
  `**Errors:** None (or describe)` line.
- **Touchpoint 2, the prose enumeration**: the Terminal Deliverable sentence
  that currently reads
  `the complete structured Task Result above (TDD Evidence / Test commands used / Files created/modified / Errors)`
  must name five fields, ending with `Deviations/Edge cases/Surprises`.
- Both touchpoints are in this one task because they are in the same file.
  **Patching the template alone ships an agent whose hard `MUST` contradicts its
  own template**, and it is the one partial fix that passes CI green and still
  violates FR-001: no Layer 1 test diffs Summary Format content across
  platforms. Precedent: commit `bb01ef28` patched this same Summary Format
  contract in both agent definitions in one commit, because agents follow their
  own output template over referenced contract prose (research R1).
- This agent is the default implementation fallback and the routed agent for
  test tasks, so it executes most of what this feature records.
- Covers FR-001; User Story 2 acceptance scenarios 1, 2, and 3.
- `[P]`: different file from T007 and T008.

**Checkpoint**: both user stories are complete.
`python3 tests/speckit-pro/unit/test-implementation-notes-record.py` passes in
full. Run quickstart Scenario 1's two greps to confirm four hits across three
files and that exactly three files still carry a `## Task Result: <TASK_ID>`
block.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: regenerate the three generated surfaces the five production edits
restale, then verify the whole change end to end.

- [ ] T010 [P] Regenerate the install payloads, installed-cache fixtures, and proof hashes by running `python3 scripts/refresh-release-artifacts.py`

**Acceptance criteria**

- Run exactly that command. **Do not run `python3 scripts/build-plugin-payloads.py`
  on its own**: it covers only the payload surface and leaves the installed-cache
  fixtures and the proof hashes stale.
- The refresh rebuilds `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`,
  content-syncs
  `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/{claude,codex}/speckit-pro/`,
  and refreshes the per-product `source_payload_tree_hash` values in
  `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and its
  byte-identical mirror
  `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json`.
  It is idempotent: a second run on the same source makes no further change.
- `git status --short dist/` shows the five production files' payload copies
  modified under both products. The Codex payload keeps the agent at
  `dist/codex/speckit-pro/codex-agents/implement-executor.toml` and flattens the
  `codex-skills/.../references/*` documents into
  `dist/codex/speckit-pro/skills/speckit-autopilot/references/`.
- **Never hand-edit** `dist/`, the installed-cache fixture, or either proof JSON
  (AGENTS.md Editing Boundaries). If a copy looks unchanged when it should not
  be, the comparison used timestamps rather than contents; compare by checksum.
- Depends on T003, T004, T005, T007, T008, and T009, the five production files.
- `[P]` with T011: disjoint outputs and different toolchains. This script
  explicitly does not regenerate the docs reference.

- [ ] T011 [P] Regenerate the generated docs test reference at `docs-site/src/content/docs/reference/tests.md`

**Acceptance criteria**

- Run `pnpm --dir docs-site install --frozen-lockfile` once in this worktree
  first. AGENTS.md Worktree Preflight makes `docs-site/` the only surface with
  dependencies, and the install is required before any docs command. Node 22.12
  or newer.
- Then run `pnpm --dir docs-site reference:generate`.
- `git status --short docs-site/src/content/docs/reference/` shows `tests.md`
  modified, listing the new Layer 4 test. Never hand-edit the generated page.
- Depends on T002, which creates the test file and its manifest entry.
- `[P]` with T010.

- [ ] T012 Run the full verification gate and the quickstart scenarios in `specs/art-012-implementation-notes-capture/quickstart.md`

**Acceptance criteria**

- `python3 tests/speckit-pro/run-all.py` reports zero failures and a total
  strictly above the recorded G0 baseline of 7226 (Layer 1 1447, Layer 4 5593,
  Layer 5 186). **Read that baseline from
  `docs/ai/specs/.process/ART-012-workflow.md`**; do not recompute it against a
  tree that already contains this feature's additions.
- Layer 1 `validate-plugin-payload`, `validate-payload-completeness`,
  `validate-payload-conformance`, `validate-codex-skills`, and
  `validate-codex-parity` all pass.
- Quickstart Scenarios 1 through 5 all produce their expected output.
- Path hygiene: `grep -rnE '/(Users|home)/' specs/art-012-implementation-notes-capture/`
  returns no output. Absolute home-directory paths fail the repository privacy
  scan.
- Depends on T010 and T011. This is the first and only task that runs the full
  suite.

- [ ] T013 Verify the PR review packet inputs are complete and current in `specs/art-012-implementation-notes-capture/plan.md`, `specs/art-012-implementation-notes-capture/spec.md`, and `specs/art-012-implementation-notes-capture/quickstart.md`

**Acceptance criteria**

- The packet's sources are present and current: `plan.md`'s six-step Review
  Order, `spec.md`'s Reviewability Budget and PR Review Packet Requirements,
  and `quickstart.md`'s verification evidence including the T012 results.
- Traceability maps FR-001 through FR-005 and SC-001 through SC-006 onto the
  changed files and the verification evidence above.
- Rollback note: the feature has no flag and needs none. Reverting the five
  production file edits removes it completely and leaves no state behind,
  because the record is exhaust that nothing depends on to make progress.
- Deferred work is named rather than absorbed: making a parallel run's per-task
  results durable before the run completes would mean rewriting how Phase 7
  waits for parallel work, which is dispatch machinery this spec does not touch.
- **Do not hand-author the packet body.** Packet generation and its protected
  fingerprint belong to the Post-Implementation Checklist's PR Body Generation
  step and the runner's packet helper. This task verifies inputs only.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no tasks
- **Foundational (Phase 2)**: T001 blocks all user story work
- **User Story 1 (Phase 3)**: depends on T001. No dependency on User Story 2
- **User Story 2 (Phase 4)**: depends on T001. Independent of User Story 1 on
  the production files it touches; sequenced second because it is P2 and
  because its test assertions live in the file T002 creates
- **Polish (Phase 5)**: depends on both stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: the durability the feature exists to deliver. Testable
  on its own with User Story 2 absent, in which case every entry reads `None`
- **User Story 2 (P2)**: gives the record content worth reading. It has no value
  until User Story 1 has somewhere durable for that content to land, which is
  why it is second

### Within Each User Story

- The test task is written first and verified RED before its implementation
  tasks
- T003 before T004: both edit `phase-execution.md`, and the append contract
  builds on the lifecycle step
- T005 after T003 and T004: it mirrors the exact rules those two land
- T007, T008, and T009 in any order, or together

### Parallel Opportunities

- **User Story 2 implementation**: T007, T008, and T009 are three separate
  files with no ordering dependency between them
- **Polish regeneration**: T010 and T011 target disjoint surfaces with different
  toolchains

Tasks that are deliberately **not** `[P]`, so an executor does not batch them:

| Tasks | Why not parallel |
|---|---|
| T003, T004 | Both edit `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` |
| T002, T006 | Both edit `tests/speckit-pro/unit/test-implementation-notes-record.py` |
| T005 | Different file, but it must mirror the text T003 and T004 land |
| T012 | Depends on both regeneration tasks completing |

---

## Parallel Example: User Story 2

```bash
# Launch all three reporting-contract edits together:
Task: "Add the reporting field to the shared Summary Format block in speckit-pro/skills/speckit-autopilot/references/tdd-protocol.md"
Task: "Add the reporting field to the Summary Format block in speckit-pro/codex-agents/implement-executor.toml"
Task: "Add the reporting field to both touchpoints in speckit-pro/agents/implement-executor.md"
```

## Parallel Example: Polish

```bash
# Launch both regeneration commands together:
Task: "Regenerate the install payloads, installed-cache fixtures, and proof hashes with python3 scripts/refresh-release-artifacts.py"
Task: "Regenerate the generated docs test reference at docs-site/src/content/docs/reference/tests.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: T001, the reviewability checkpoint
2. Complete Phase 3: T002 through T005
3. **STOP and VALIDATE**: `python3 tests/speckit-pro/unit/test-implementation-notes-record.py`
   passes its record-contract group on both platform documents. The record is
   durable even with no executor reporting anything, because every entry reads
   `None`
4. Regenerating (T010, T011) and the full gate (T012) can be run at this point
   if the MVP is to be shipped on its own

### Incremental Delivery

1. T001 → scope confirmed
2. Add User Story 1 → the record exists, survives interruption, and carries one
   entry per collected attempt (MVP)
3. Add User Story 2 → those entries carry real content instead of `None`
4. Regenerate the three generated surfaces, then run the full gate

### Parallel Team Strategy

The two stories touch disjoint production files, so with more than one executor
User Story 2's three edits (T007, T008, T009) can run alongside User Story 1's
work once T001 and T002 are done. Sequential priority order is the default,
because User Story 1 is the MVP.

---

## Requirement Coverage

| Requirement | Tasks |
|---|---|
| FR-001 reporting field, one combined field, literal `None`, both platforms | T006, T007, T008, T009 |
| FR-002 record exists with header before dispatch, create-if-absent, never truncate | T002, T003, T005 |
| FR-003 one entry per dispatched attempt, two-branch cadence, additive only, ordering | T002, T004, T005 |
| FR-004 fail-open gap, no retry, one fallback level, blast radius of one entry | T002, T004, T005 |
| FR-005 both platforms produce the same record | T002, T005, T008 |
| SC-001 N attempts produce N entries, all task-ID identified | T002, T004, T005 |
| SC-002 interrupted phase leaves header plus collected entries | T002, T003, T004 |
| SC-003 100% of entries read `None` when nothing is reported | T003, T004, T006, T007, T008, T009 |
| SC-004 forced write failure changes no outcome and is readable as a gap | T002, T004, T005 |
| SC-005 no entry's text changes after it is written | T002, T004, T005 |
| SC-006 task ID and text recoverable from headings, order from position | T002, T004, T005 |
| Generated-artifact contract | T010, T011, T012 |
| Reviewability budget and PR packet | T001, T013 |

---

## Notes

- `[P]` tasks = different files, no dependencies
- `[Story]` label maps task to a specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
- The full suite is RED between the first production edit and T010, on stale
  generated payloads and proof hashes. Never repair that by hand
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break
  independence
- Avoid: expanding a task list past the reviewability budget instead of
  splitting the spec
