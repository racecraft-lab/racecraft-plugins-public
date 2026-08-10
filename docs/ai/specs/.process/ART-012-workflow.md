# SpecKit Workflow: ART-012 — Implementation-Notes Capture

**Template Version**: 1.0.0
**Created**: 2026-08-10
**Purpose**: Executable workflow for the ART-012 autopilot run. The prompts below are what each phase executes.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/ART-012-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. The
Specify and Clarify Prompts below were populated from that interview,
so the design concept doc is the source of truth for any decision
captured during scoping.

> **Note:** Grill Me is human-in-the-loop only. It is **not** part of
> the autopilot loop. Once the workflow file is populated and autopilot
> begins, clarifications happen via `/speckit-clarify` and the
> consensus protocol — never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ⏳ Pending | |
| Clarify | `/speckit-clarify` | ⏳ Pending | Optional but recommended |
| Plan | `/speckit-plan` | ⏳ Pending | |
| Checklist | `/speckit-checklist` | ⏳ Pending | Run for each domain |
| Tasks | `/speckit-tasks` | ⏳ Pending | |
| Analyze | `/speckit-analyze` | ⏳ Pending | |
| Confidence Gate | G6.5 | ⏳ Pending | Pre-Implement composite confidence |
| Implement | `/speckit-implement` | ⏳ Pending | |
| Post | Post-Implementation | ⏳ Pending | Canonical 12-item closeout |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

G6.5 is advisory by default, so no phase of the main loop flips its row. Leaving
it Pending is legitimate and does not make the rows below it read as out of
order; record the verdict in [Phase 6.5](#phase-65-confidence-gate) when the
gate runs.

### Phase Gates (SpecKit Best Practice)

Each phase requires **human review and approval** before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | All user stories clear, no `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | Ambiguities resolved, decisions documented |
| G3 | After Plan | Architecture approved, constitution gates pass, dependencies identified |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Task coverage verified, dependencies ordered |
| G6 | After Analyze | No `CRITICAL` issues, `WARNING` items reviewed |
| G6.5 | Before Implement | Composite confidence meets the autonomous implementation threshold |
| G7 | After Each Implementation Phase | Tests pass, manual verification complete |

---

## Prerequisites

### Constitution Validation

**Before starting any workflow phase**, verify alignment with the project constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| VI. KISS, Simplicity & YAGNI | No abstraction beyond what the reporting contract needs — one combined field, not a taxonomy | Code review against Design Concept Q1/Q6 |
| II. Cross-Platform Runtime & Script Safety | Claude and Codex autopilot skills stay behaviorally identical | Codex parity checks (validate-codex-skills / validate-codex-parity) |
| IV. Test Coverage Before Merge | Notes-record format and fixed-heading empty case both covered before merge | Layer 4 fixture test for the notes-record format |

**Constitution Check:** ✅ (no conflicts identified during scoping; verify again after Plan)

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | ART-012 |
| **Name** | Implementation-Notes Capture |
| **Branch** | `art-012-implementation-notes-capture` |
| **Dependencies** | ART-006 (Autopilot Staging) — complete, PR #422 |
| **Enables** | ART-010 (Final-PR Writeup, Companions & Ready Flip) — writeup depth |
| **Priority** | P2 |

### Success Criteria Summary

- [ ] Every implementation executor's task summary includes a
      `**Deviations/Edge cases/Surprises:**` field (extends the existing
      `## Task Result: <TASK_ID>` block in `tdd-protocol.md`), literally
      reading "None" when there is nothing to report.
- [ ] `specs/<branch>/.process/implementation-notes.md` is created with a
      header at the start of Phase 7, before any task dispatches.
- [ ] The orchestrator appends one entry per task, immediately after each
      task completes — never batched, never overwritten on retry.
- [ ] A failed append logs a gap and never blocks the task or the phase
      (fail-open, matching ART-007 and ART-009's precedent).
- [ ] Both `speckit-pro/skills/speckit-autopilot/` and its
      `speckit-pro/codex-skills/speckit-autopilot/` mirror carry identical
      instructions.

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/art-012-implementation-notes-capture/spec.md`

### Specify Prompt

```text
/speckit-specify Capture deviations from plan, discovered edge cases, and
surprises during the implement stage as a durable per-spec notes record.
```

#### Detailed Prompt (for complex specs)

```text
/speckit-specify

## Feature: Implementation-Notes Capture

### Problem Statement
Autopilot's implement stage (Phase 7, task-level dispatch) currently returns
a `## Task Result: <TASK_ID>` summary per task (TDD Evidence, test commands,
files created/modified, Errors) but nothing captures deviations from the
plan, discovered edge cases, or surprises an executor ran into. That
information is currently lost the moment the task summary is read and
discarded — ART-010's PR writeup and the optional retrospective extension
both need a durable record to draw from, and today there is none.

### Users
- The autopilot orchestrator (Phase 7), which appends to the record.
- Every implementation executor / project agent dispatched during Phase 7,
  which reports into the record via its existing task summary.
- ART-010's PR-writeup generation (downstream consumer, out of scope here).
- The optional retrospective extension, when installed (downstream
  consumer, out of scope here).

### User Stories
- As the autopilot orchestrator, I append one durable notes entry per task
  immediately after that task completes, so the record survives a
  mid-phase interruption.
- As an implementation executor, I report deviations, edge cases, and
  surprises as one field in my existing task summary — literally "None"
  when there is nothing to report — so I don't need a second reporting
  format.
- As ART-010 (downstream, out of scope for this spec), I can read a
  complete, per-task record of what happened during implementation.

### Constraints
- Fail-open: an append failure logs a gap and never blocks the task or the
  phase (Design Concept Q4).
- Pure append-only: no read-modify-write of the file to update a running
  counter or to overwrite a retried task's earlier entry (Design Concept
  Q3, Q5).
- The reporting field extends the existing `## Task Result: <TASK_ID>`
  block in `tdd-protocol.md` — it does not introduce a second block
  (Design Concept Q6).
- No per-marker attribution — flat file, task ID only (Design Concept Q7).
- File is created with a header at the start of Phase 7, before any task
  dispatches (Design Concept Q8).
- Reviewability budget: ~115 reviewable LOC (modify-weighted), ~3
  production files, ~6 total files, primary surface harness/adapter.
  Advisory `estimate-spec-size` run during scoping (2 in-scope user
  stories, 3 production files, 4 FRs, modify-weighted) returned
  `{"estimated_loc": 115, "status": "ok", "suggested_slices": 1}` — one
  vertical slice, no split.

### Out of Scope
- Generating the PR writeup itself (ART-010).
- Per-marker attribution in the notes file (ART-010 cross-references task
  ID against `pr_marker_plan.json` if it needs that).
- A running spec-level summary counter — the per-task "None" entries make
  the empty case explicit without one.
- Deduplicating retried tasks — a serial retry after a parallel-run
  regression appends a second entry, kept as history.
```

### Specify Results

<!-- Fill in after running the command -->

| Metric | Value |
|--------|-------|
| Functional Requirements | <!-- e.g., FR-001 through FR-020 --> |
| User Stories | <!-- Count --> |
| Acceptance Criteria | <!-- Count --> |

### Files Generated

- [ ] `specs/art-012-implementation-notes-capture/spec.md`

### SpecKit Traceability Markers

Use these markers in spec.md for traceability through later phases:

| Marker | Purpose | Example |
|--------|---------|---------|
| `[US1]`, `[US2]` | User story reference | `[US1] User searches by query` |
| `[FR-001]` | Functional requirement | `[FR-001] API returns paginated results` |
| `[NEEDS CLARIFICATION]` | Flag for Clarify phase | `Auth method [NEEDS CLARIFICATION]` |
| `[P]` | Parallel-safe task | `[P] Can run alongside other tasks` |
| `[Gap]` | Missing coverage | `[Gap] No task covers error handling` |

---

## Phase 2: Clarify

**When to run:** When spec has areas that could be interpreted multiple ways. 10-20 minutes here saves hours of rework later.

**Best Practice:** Maximum 5 targeted questions per Clarify session.

The Design Concept interview converged naturally with **zero deferred Open
Questions** — every branch that came up (format, cadence, empty case,
fail-open, retry dedup, marker tagging, field placement, file lifecycle) was
resolved to a specific answer during scoping. Clarify sessions here should
therefore focus on verifying spec.md's wording matches those decisions
exactly, not on discovering new ambiguity.

### Clarify Prompts

#### Session 1: Reporting Contract Wording

```text
/speckit-clarify Focus on the executor reporting contract: does spec.md's
wording for the new Task Result field match Design Concept Q6 exactly (one
combined "Deviations/Edge cases/Surprises" field, not three separate
mandatory fields; literally "None" when empty, per Q1/Q3)? Does it specify
which existing block in tdd-protocol.md gets the new line, and next to
which existing field (Errors)?
```

#### Session 2: Append Semantics

```text
/speckit-clarify Focus on append semantics: does spec.md specify the file is
created with a header at Phase 7 start before any dispatch (Q8), that
appends happen immediately after each task (Q2), that retries append a
second entry rather than overwrite (Q5), and that a write failure is
fail-open and logs a gap without blocking (Q4)?
```

<!-- Add a third session only if spec.md review surfaces a genuine gap the
     Design Concept doc doesn't already answer. -->

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|---------------|
| 1 | Reporting Contract Wording | | |
| 2 | Append Semantics | | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/art-012-implementation-notes-capture/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack
- Runtime: speckit-pro plugin skills (Markdown SKILL.md + reference docs),
  no application code — this spec edits prompt/instruction text, not
  Python. Any orchestrator-side file-write logic added to phase-execution.md
  stays prose-level (the orchestrator is an LLM following the reference doc,
  not a script).
- Test suite: Python 3.11+ stdlib only (`python3 tests/speckit-pro/run-all.py`),
  per this repo's tooling constraint — the Layer 4 fixture test for the
  notes-record format is a stdlib Python test, not a shell script.
- Platforms: Claude Code (`speckit-pro/skills/`) and Codex CLI
  (`speckit-pro/codex-skills/`) — both must carry identical instructions
  per the project's standing same-agents-both-platforms convention.

## Constraints
- Reviewability budget ~115 LOC (modify-weighted), primary surface
  harness/adapter, ~3 production files, ~6 total files (see Specify
  Prompt's Constraints section for the full budget and estimator output).
- Modify-only: this spec edits `phase-execution.md` and `tdd-protocol.md`
  in place; it does not add new template/schema files.
- Reference the Design Concept doc
  (docs/ai/specs/.process/ART-012-design-concept.md) if planning needs
  context beyond this prompt — it is the source of truth for every
  scoping decision (Q1–Q8) captured during grill-me.

## Architecture Notes
- **File location:** `specs/<branch>/.process/implementation-notes.md` —
  already decided by the roadmap as "exhaust," not re-litigated here.
- **Field placement (Q6):** extend the existing
  `## Task Result: <TASK_ID>` block in `tdd-protocol.md` with a new
  `**Deviations/Edge cases/Surprises:**` line next to `**Errors:**` —
  do not introduce a second block.
- **Append cadence (Q2):** the orchestrator appends inside the existing
  Phase 7 Step 3 task loop in `phase-execution.md`, immediately after
  processing each task's summary — not batched at phase end.
- **Empty case (Q1/Q3):** every task always gets an entry with a fixed
  `### <TASK_ID>` heading; when nothing to report, the field literally
  reads "None." No separate whole-file summary marker.
- **Retry (Q5):** a task re-run (e.g., the Step 3b serial retry after a
  parallel-run regression) appends a second entry under the same task
  ID — never overwrites the first.
- **Fail-open (Q4):** a write/append failure logs a gap to the workflow
  file and never blocks the task or the phase, matching ART-007's
  artifact generation and ART-009's UAT artifact.
- **No marker tagging (Q7):** entries are flat, task-ID only; no
  `pr_marker_plan` cross-reference is embedded.
- **File lifecycle (Q8):** create the file with a
  `# Implementation Notes: <SPEC_ID>` header at the very start of Phase 7,
  before any task dispatch, so it exists even if the phase is interrupted
  after zero tasks complete.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Technical context, execution flow |
| `research.md` | ⏳ | Decision rationales (if needed) |
| `data-model.md` | ⏳ | Entities and types |
| `contracts/` | ⏳ | API specifications |
| `quickstart.md` | ⏳ | Developer onboarding |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates both spec AND plan together. Run multiple times for different domains.

**Best Practice:** Don't guess which domains to check. Analyze the spec first, then generate enriched prompts with spec-specific focus areas.

### Step 1: Analyze Spec for Recommended Domains

Recommended from the Design Concept's design-tree branches — this is a
narrow, harness-level change with no API/UI/auth/DB surface, so most
catalog domains don't apply. Two domains carry real risk:

| Signal in Design Concept | Recommended Domain |
|---|---|
| Fail-open append (Q4); "no deviations" empty case (Q1/Q3) | **error-handling** |
| Durable per-task append across mid-phase interruption and retry (Q2/Q5); file lifecycle (Q8) | **state-management** |

**Target: 2 domains** — the spec's complexity is entirely in failure and
persistence semantics, not in the other catalog domains.

### Step 2: Run Enriched Checklist Prompts

#### 1. error-handling Checklist

Why this domain: the entire failure contract (Q4) is new — a wrong or
missing fail-open path here could let a formatting glitch in one task's
summary block the whole implement phase, which the Design Concept
explicitly rules out.

```text
/speckit-checklist error-handling

Focus on Implementation-Notes Capture requirements:
- Does spec.md require that a failed append (write error, unparseable
  executor summary) logs a gap and proceeds, never blocking the task or
  phase?
- Is the "log a gap" destination specified (the workflow file, per the
  fail-open precedent in ART-007/ART-009)?
- Pay special attention to: what happens if the executor's task summary
  omits the new field entirely (older prompt version, or a
  PROJECT_IMPLEMENTATION_AGENT that doesn't follow the injected
  tdd-protocol.md exactly) — does the orchestrator treat a missing field
  the same as an explicit "None," or does it need its own fail-open path?
```

#### 2. state-management Checklist

Why this domain: the append-only, immediate-write, no-overwrite design
(Q2/Q3/Q5/Q8) is the load-bearing part of this spec — every other decision
follows from it.

```text
/speckit-checklist state-management

Focus on Implementation-Notes Capture requirements:
- Does spec.md require the file to exist (with header) from the very
  start of Phase 7, before any task dispatch, independent of how many
  tasks eventually run?
- Does spec.md require appends to happen immediately after each task,
  not batched at phase end?
- Does spec.md require a retried task (parallel-run regression → serial
  re-run) to append a second entry rather than overwrite the first?
- Pay special attention to: `--from-phase` resume behavior — if Phase 7
  is resumed after a prior partial run, does the resumed run re-open the
  existing file and continue appending, or does it need to detect and
  skip already-completed tasks' entries to avoid a third duplicate?
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| error-handling | | | |
| state-management | | | |
| **Total** | | | |

### Addressing Gaps

When checklist identifies `[Gap]` items:

1. Review the gap — is it a genuine missing requirement?
2. Update `spec.md` or `plan.md` to address it
3. Re-run the checklist to verify coverage
4. If the gap is intentionally out of scope, document why

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/art-012-implementation-notes-capture/tasks.md`

### Tasks Prompt

```text
/speckit-tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: foundation → components → integration → validation
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story, not by technical layer

## Implementation Phases
1. Foundation — extend tdd-protocol.md's Task Result block with the new
   field (Q6); add the file-lifecycle header step to phase-execution.md
   (Q8)
2. User Story 1 (orchestrator append contract, P1) — implement the
   immediate-append-per-task logic in phase-execution.md's Step 3 loop
   (Q2), including the fail-open path (Q4) and no-overwrite-on-retry
   behavior (Q5) — independently testable via the Layer 4 fixture
3. User Story 2 (executor reporting contract, P1) — wire the new field
   into every implementation-agent prompt path (implement-executor and
   PROJECT_IMPLEMENTATION_AGENT both receive the shared tdd-protocol.md
   injection, so this should be one shared edit, not two) — independently
   testable via Layer 1 + Codex parity
4. Polish — Codex mirror parity pass (`speckit-pro/codex-skills/speckit-autopilot/`),
   dispatch-prompt wording covered by Layer 1

## Constraints
- Stay within the Design Concept's Non-goals: no marker tagging (Q7), no
  running summary counter (Q3), no separate reporting block (Q6). Flag
  any task that would cross those boundaries before implementing it.
- Verification per the roadmap: Layer 4 fixture test for the notes-record
  format (including the explicit "None" entry); dispatch-prompt wording
  covered by Layer 1 + Codex parity checks (validate-codex-skills /
  validate-codex-parity).
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | |
| **Phases** | |
| **Parallel Opportunities** | |
| **User Stories Covered** | |

---

## Atomicity Route

**When this is filled:** After the Tasks phase / gate G5, the autopilot SKILL runs
the read-only atomicity classifier and records its decision here. This is a
**placeholder** until then — leave the cells blank during scoping. The classifier
emits one machine-readable decision; the SKILL is what writes it into this section
(the script never writes a file of its own). This route is recorded only here in the
workflow file — never in the spec map. It is read downstream by the layer-planner and
multi-PR emission work that builds on top of it; recording it now wires no PR creation
or branch splitting on its own.

The decision answers "can this change be split into multiple small PRs safely?" by
inspecting the change's structural seams (independent additive capabilities), not its
line count. Surface the four fields the SKILL extracts from the emitted decision:

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | | `true`, or `false` for a destructive-migration or concurrency-sensitive change (a passing CI run does not prove such a change is safe to release). |
| **Signals** | | The decisive detector findings behind the route and releasability reading (may be empty when the classifier abstains). |
| **Warnings** | | Any release-safety warning attached to the change (empty when there is no releasability risk). |

To produce the decision, run the classifier against the feature directory:

```text
runner helper atomicity-route specs/art-012-implementation-notes-capture
```

See the classifier script at
[`speckit-autopilot/scripts/atomicity-route`](../../speckit-autopilot/scripts/atomicity-route).

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```text
/speckit-analyze

Focus on:
1. Constitution alignment — verify coding standards compliance
2. Coverage gaps — ensure all FRs and user stories have tasks
3. Consistency between task file paths and actual project structure
4. Verify P1 user stories have complete task coverage
5. Design Concept drift — cross-check spec.md, plan.md, and tasks.md
   against docs/ai/specs/.process/ART-012-design-concept.md's Goals,
   Non-goals, and Q1–Q8 decisions. The Design Concept is the source of
   truth for scoping decisions captured during grill-me; if a downstream
   artifact contradicts it (e.g., a task that adds marker tagging, or a
   field placement that introduces a second block), the downstream
   artifact is wrong unless there is an explicit revision note.
```

### Analyze Severity Levels

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| `CRITICAL` | Blocks implementation, violates constitution | **Must fix before G6 gate** |
| `HIGH` | Significant gap, impacts quality | Should fix |
| `MEDIUM` | Improvement opportunity | Review and decide |
| `LOW` | Minor inconsistency | Note for future |

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| | | | |

---

## Phase 6.5: Confidence Gate

**When to run:** After Phase 6 commits and before Phase 7 begins. Gate semantics
are unchanged; this section records the verdict so a later session can read it.

| Field | Value |
|-------|-------|
| Mode | <!-- advisory (default) or strict --> |
| Composite confidence | <!-- 0.00-1.00 --> |
| Verdict | <!-- proceed / remediate / stop --> |
| Evidence | <!-- what the score was computed from --> |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed (no coverage gaps).

### Implement Prompt

```text
/speckit-implement

## Approach: TDD-First

For each task, follow this cycle:

1. **RED**: Write failing test defining expected behavior
2. **GREEN**: Implement minimum code to make test pass
3. **REFACTOR**: Clean up while tests still pass
4. **VERIFY**: Manual verification of acceptance criteria

### Pre-Implementation Setup

Before starting any task:
1. Confirm on branch `art-012-implementation-notes-capture` in
   `.worktrees/art-012-implementation-notes-capture/`, not main
2. Run `python3 tests/speckit-pro/run-all.py` once to confirm a clean
   baseline before making changes (no bootstrap required for this
   surface — see AGENTS.md Worktree Preflight)
3. Re-read docs/ai/specs/.process/ART-012-design-concept.md if a task's
   "why" needs the original Q&A reasoning

### Implementation Notes
- Consult the Q&A log (Q1–Q8) for the "why" behind each decision before
  writing tests — this informs edge-case handling (e.g., Q5's retry
  entries, Q8's zero-task interruption case) and refactor choices.
- Any decision captured in the Design Concept that isn't reflected in
  tasks.md should be surfaced as a gap before coding, not silently
  dropped (see Analyze Prompt's Design Concept drift check).
- Deviations, edge cases, or surprises encountered while implementing
  ART-012 itself get reported the same way this spec teaches every other
  executor to report them — dogfood the contract.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation | | | |
| 2 - User Story 1 | | | |
| 3 - User Story 2 | | | |
| 4 - Polish | | | |

---

## Post-Implementation Checklist

The canonical closeout. Every row must reach Complete or an explicit
`Skipped` before the run may report completion.

| Canonical Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | ⏳ Pending | |
| Post: Verify Implementation | ⏳ Pending | |
| Post: Verify Tasks Phantom Check | ⏳ Pending | |
| Post: Code Review | ⏳ Pending | |
| Post: Integration Suite | ⏳ Pending | |
| Post: Reviewability Diff Gate | ⏳ Pending | |
| Post: Self-Review | ⏳ Pending | |
| Post: UAT Runbook Generation | ⏳ Pending | |
| Post: PR Body Generation | ⏳ Pending | |
| Post: PR Creation | ⏳ Pending | |
| Post: Review Remediation | ⏳ Pending | |
| Post: Retrospective | ⏳ Pending | |

- [ ] All tasks marked complete in tasks.md
- [ ] Linting passes: N/A (no lint config for Markdown reference docs beyond structural tests)
- [ ] Tests pass: `python3 tests/speckit-pro/run-all.py`
- [ ] Build succeeds: N/A (no build step; payload/proof regeneration accounted per the generated artifact contract)
- [ ] Manual verification complete
- [ ] PR created and reviewed
- [ ] Merged to main branch

---

## Lessons Learned

### What Worked Well

-

### Challenges Encountered

-

### Patterns to Reuse

-

---

## Project Structure Reference

```
racecraft-plugins-public/
├── speckit-pro/
│   ├── skills/speckit-autopilot/references/
│   │   ├── phase-execution.md      # dispatch template, Phase 7 task loop
│   │   └── tdd-protocol.md         # executor reporting contract, Summary Format
│   └── codex-skills/speckit-autopilot/   # Codex mirror — identical instructions
├── tests/speckit-pro/               # Layer 1/4/5 test suite (Python 3.11+ stdlib)
└── specs/art-012-implementation-notes-capture/
    ├── spec.md / plan.md / tasks.md # CONTRACT artifacts (this spec's own workflow)
    └── .process/
        └── implementation-notes.md  # what this spec teaches every OTHER spec's
                                      # Phase 7 to produce (not this spec's own —
                                      # see Post-Implementation for this run's record)
```

---

Template based on SpecKit best practices. Populate the prompts above with your project-specific tech stack, domains, and constraints.
