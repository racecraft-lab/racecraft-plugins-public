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
| Specify | `/speckit-specify` | ✅ Complete | G1 pass — 4 FRs, 2 user stories, 6 success criteria, 0 markers |
| Clarify | `/speckit-clarify` | ✅ Complete | G2 pass — 2 verification sessions, 7 findings, 2 consensus rounds, 0 markers |
| Plan | `/speckit-plan` | ✅ Complete | G3 pass — 6 artifacts, 11 research decisions, 8 declared file ops |
| Checklist | `/speckit-checklist` | ✅ Complete | G4 pass — 2 domains, 58 items, 14 gaps found and all remediated |
| Tasks | `/speckit-tasks` | ✅ Complete | G5 pass — 13 tasks, 5 [P], route one-navigable-PR |
| Analyze | `/speckit-analyze` | ✅ Complete | G6 pass — 13 findings, 0 CRITICAL, all remediated in 1 loop |
| Confidence Gate | G6.5 | ✅ Complete | Advisory, composite 0.93 ≥ 0.90 → proceed |
| Implement | `/speckit-implement` | ⏳ Pending | Out of stage — this run resolved `plan`; runs on `--stage implement` |
| Post | Post-Implementation | ⏳ Pending | Out of stage — belongs to the implement stage |

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

### Feature State (namespaced branch)

| Field | Value |
|-------|-------|
| Feature dir | pinned via `.specify/feature.json` (gitignored) to `specs/art-012-implementation-notes-capture` |
| `ON_FEATURE_BRANCH` | **true** — the 2.23.0 runner's `check-prerequisites` reports `on_feature_branch: true` for this namespaced branch (`branch` check detail: `worktree=true,feature=true`). The `feature.json` pin still serves the vendored `check-prerequisites.sh` path the `/speckit-*` phase commands call internally, whose `^[0-9]{3}-` regex does not match this repo's namespaced spec IDs. |
| `before_specify` → `speckit.git.feature` (`optional: false`) | **SKIP** — the branch already exists and is checked out in this worktree; the hook's purpose is satisfied |

### Reviewability Setup Gate (recorded at scaffold time)

Runner helper `reviewability-gate` in setup mode against the technical roadmap
returned `status: "warn", pass: true` with the single warning
`primary surfaces 3 exceeds warn threshold 1`. That count comes from the
helper's whole-roadmap scan; ART-012's own recorded budget is one primary
surface (harness/adapter). Warnings may proceed when the workflow records the
scope budget and split decision, which the rest of this subsection does.

**Scope budget:** projected ~162 reviewable production LOC (modify-weighted),
5 production files, ~8 total files, one primary surface. Modify-weighted work
carries no greenfield allowance (warn 400 / block 800). *Amended 2026-08-10 at
Clarify session 1; the scaffold-time figures were ~115 LOC over ~3 production
files, computed before the three-copy Task Result fact was known. See
"Verified Repository Facts" under the Plan Prompt.* Every dimension remains
under the warn line (400 LOC / 6 production files / 15 total files / 1 primary
surface).

**Split decision (grill-me slice-sizing, re-confirmed at Clarify):** one
vertical slice, no split. `estimate-spec-size` re-run with the corrected
signals (2 user stories, 5 production files, 4 FRs, modify-weighted) returned
`{"estimated_loc": 162, "suggested_slices": 1, "status": "ok"}` for the
spec's current shape (2 user stories, 5 production files, 5 FRs, modify) —
verbatim output at every step, never a hand adjustment. The figure moved
115 → 155 → 162 as the inputs were corrected: 155 when Clarify session 1 fixed
the file count to 5, then 162 when session 2 added FR-005. The scope (reporting
contract → orchestrator append → consumer hand-off) still has no horizontal
layering to re-slice, and 162 sits far under the 400 warn ceiling.

### Phase 0 Prerequisites (recorded at run time, 2026-08-10)

Stage resolution (Step 0.6c): `Stage: plan (auto-detect) — auto-detect: the
first non-terminal planning phase is Specify, which is ⏳ Pending`. The state
slot was reclaimed from `docs/ai/specs/.process/ART-006-workflow.md`
(prior status: `completed_archived`).

| Check | Result |
|-------|--------|
| `check-prerequisites` | `all_pass: true` — CLI `specify 0.11.8`, project initialized, constitution present, all SpecKit commands installed, workflow file exists, `branch: art-012-implementation-notes-capture` (`worktree=true,feature=true`) |
| `detect-commands` | stack `python`; `UNIT_TEST` / `FULL_VERIFY` = `python3 tests/speckit-pro/run-all.py`; `BUILD` / `TYPECHECK` / `LINT` = `N/A` (evidence: `tests/speckit-pro/run-all.py`) |
| `detect-presets` | `speckit-pro-reviewability` v1.0.0 resolves spec/plan/tasks templates; 18 hook events configured |
| `resolve-confidence-mode` | `advisory` (no `--strict` / `--advisory` flag, no local config file) |
| Settings | no `.claude/speckit-pro.local.md` — defaults: consensus `tier-a`, gate-failure `stop`, auto-commit on |
| Extensions installed | `archive`, `checkpoint`, `git`, `retrospective`, `speckit-utils`, `verify`, `verify-tasks` (all enabled) |
| `PROJECT_IMPLEMENTATION_AGENT` | none detected in `.claude/agents/` (only `plugin-release-auditor`, `speckit-skill-reviewer`) → fallback `speckit-pro:phase-executor` |
| Archive sweep | no-op — `specs/` holds only this run's current target, which the sweep excludes by contract; every prior spec is already archived |

**G0 test-count baseline (preserve; do not recompute):** `python3
tests/speckit-pro/run-all.py` → **7226/7226 passed** (L1 1447, L4 5593,
L5 186), toolchain preflight ok. G7 verifies the count *increased* against
this number, so a later `--stage implement` run in a fresh session MUST read
it from here rather than re-measuring a tree that already contains this
spec's additions.

**Constitution validation:** the only runnable `PROJECT_COMMANDS` gate for
this stack is the test suite, and it passes at the baseline above.
`TYPECHECK`, `LINT`, and `BUILD` are `N/A` for a Markdown-plus-stdlib-Python
surface, so no principle has an unrun check. Principles I–VI show no conflict
with this spec's scope; re-verify after Plan.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | ART-012 |
| **Name** | Implementation-Notes Capture |
| **Branch** | `art-012-implementation-notes-capture` |
| **Stage** | plan |
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
- [ ] The orchestrator appends one entry per dispatched task attempt — for a
      singly or sequentially dispatched task, immediately after it completes;
      for a task inside a parallel run, when that run is collected, before the
      next run dispatches. Never batched to phase end, never overwritten on
      retry, never truncated on resume.
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

## Feature: Implementation-Notes Capture (ART-012)

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
- Reviewability budget: ~162 reviewable LOC (modify-weighted), 5
  production files, ~8 total files, primary surface harness/adapter.
  Advisory `estimate-spec-size` re-run at Clarify session 1 (2 in-scope
  user stories, 5 production files, 4 FRs, modify-weighted) returned
  `{"estimated_loc": 162, "suggested_slices": 1, "status": "ok"}` — one
  vertical slice, no split.
  *Corrected 2026-08-10 at Analyze: this prompt was authored at scaffold
  time and read "~115 reviewable LOC ... ~3 production files, ~6 total
  files" from a scoping run fed 3 production files, which returned
  `{"estimated_loc": 115, "status": "ok", "suggested_slices": 1}`. That
  premise was superseded by the three-copy Task Result finding.*

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

| Metric | Value |
|--------|-------|
| Functional Requirements | FR-001 through FR-005 (5) — *the table first recorded FR-001 through FR-004 (4); Clarify session 2 added FR-005, the platform-parity clause. Corrected 2026-08-10 at Analyze.* |
| User Stories | 2 (US1 durable per-task record, P1; US2 one reporting field, P2) |
| Acceptance Criteria | 10 acceptance scenarios (7 under US1, 3 under US2) + 12 edge cases — *first recorded as 8 scenarios (5 under US1) + 7 edge cases; Clarify session 2's resume, retry, and fail-open reconciliations added the rest. Corrected 2026-08-10 at Analyze.* |
| Success Criteria | SC-001 through SC-006 (6) |
| `[NEEDS CLARIFICATION]` markers | 0 |

**G1 PASS.** Runner `validate-gate` returned
`{"gate":"G1","pass":true,"reason":"spec.md exists with 0 markers","markers":0,"details":[]}`.
An independent grep confirms zero markers, and a privacy grep confirms no
absolute home-directory path leaked into the authored spec.

The spec's own reviewability budget re-derives the same figures this workflow
records under the Reviewability Setup Gate: primary surface harness/adapter, 162
projected reviewable LOC (modify-weighted), 5 production files, 8 total files,
within budget, one slice, no exception claimed.

*Corrected 2026-08-10 at Analyze. This paragraph was written at G1, before
Clarify session 1 found the three-copy Task Result fact, and read "115 projected
reviewable LOC (modify-weighted), 3 production files, 6 total files". Those are
the superseded scaffold-time figures. The amendment itself is recorded in the
Consensus Resolution Log item 1 and in spec.md's Reviewability Budget; this row
had simply not been carried forward with the rest.*

### Files Generated

- [x] `specs/art-012-implementation-notes-capture/spec.md`

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

Both sessions ran even though G1 recorded **zero** `[NEEDS CLARIFICATION]`
markers. The default routing makes Clarify conditional on markers, but this
workflow authored its sessions as *verification* passes — checking spec.md's
wording against the settled Q1–Q8 decisions — and that intent is what they
executed. Session 1 confirmed spec.md faithful on every check and still found
a real defect, in the workflow file rather than the spec.

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|---------------|
| 1 | Reporting Contract Wording | 2 raised (1 routed to consensus, 1 resolved from evidence) | spec.md verified faithful on all five session-1 checks: one combined field, existing block, literal "None", both platforms, nothing else changed. FR-001 needs no edit — naming `tdd-protocol.md:139` in a spec would violate the repo's own WHAT-not-HOW rule, and the Plan Prompt already pins the WHERE. **Defect found in the workflow file, not the spec:** the recorded "one shared edit / 3 production files" premise was wrong. Budget restated 115 → 155 LOC, 3 → 5 production files, from a re-run estimator. Field order settled: append after `**Errors:**`. |
| 2 | Append Semantics | 5 raised (1 routed to consensus, 4 resolved from evidence) | spec.md verified faithful on all four session-2 probes (Q8 header-before-dispatch → FR-002; Q2 cadence → FR-003; Q5 retry-appends → FR-003 + SC-005; Q4 fail-open → FR-004). Five reconciliation gaps the interview never reached, all now closed: **FR-002 would have truncated the record on resume** (now create-if-absent); **"each task" excluded two routing branches** that never emit a task-result block (now every dispatched attempt, three append sites); **FR-004/SC-004 named no destination** so SC-004 was uncheckable (now named at WHAT level); **FR-002/003/004 carried no parity clause** while FR-001 did (new FR-005, parity owed on the record, not the wording); and the consensus item below. |

### Consensus Resolution Log

| # | Item | Categories | Analysts | Round | Outcome | Artifacts Edited |
|---|------|-----------|----------|-------|---------|------------------|
| 1 | Which authored copies of the `## Task Result: <TASK_ID>` block are in scope for the new reporting field? | `[codebase]`, `[spec]` | codebase-analyst, spec-context-analyst | 1 | **Both agree, high confidence → Option A: all three copies.** N=2 both-agree, no escape-hatch keyword, no `[security]` tag, so Round 2 was not triggered. Rule-out for a partial fix is FR-001's own sentence ("Both supported agent platforms MUST receive an identical reporting contract") plus the G6 drift check, **not** CI: `validate-codex-parity.py` checks agent-file existence, not template content, so a partial fix would pass green. Decisive precedent: commit `bb01ef28` patched this same Summary Format contract in both agent definitions in one commit because "agents follow their own output template over referenced contract prose." | `spec.md` Reviewability Budget; roadmap Reviewability Budget + Key Files; workflow Verified Repository Facts, Scope budget, Split decision, Architecture Notes, Tasks Prompt |

| 2 | When does the append happen during a `[P]` parallel run, and do FR-003/SC-002 need restating to match the shipped Claude loop? | `[codebase]`, `[spec]` | codebase-analyst, spec-context-analyst | 1 | **Both agree, high confidence → Option B: two-branch cadence.** Singleton and sequential dispatch appends per task; a parallel run appends at collection, before the next run dispatches. Codex keeps its stronger per-result append unchanged. The decisive argument is not merely that no per-completion hook exists, but that `agent-teams-integration.md:325-328` (Design Principle #2) requires the parallel-subagents fallback to deliver "the same contract (same parallelism, same outputs)" as the Agent Teams path — so even a Teams-only hook could not become the contract. Background dispatch is documented at `:75-76` as "The next user message returns all N results together." Precedent for amending a settled grill-me answer mid-run via consensus rather than a new interview: `CAR-005-workflow.md:1348`, where a recorded guarantee was found unachievable and restated with a design-concept revision note. | Design Concept Q2 revision note + Goals bullet; `spec.md` US1 narrative, acceptance scenarios, FR-002/003/004, new FR-005, SC-001/002/004, edge cases, assumptions; workflow Success Criteria Summary, Architecture Notes, state-management checklist prompt |

**Escalation call for item 2, recorded because it is a judgment, not a rule.**
This narrows a durability guarantee the user personally selected in Q2 with a
stated rationale, so I checked the stop conditions directly rather than taking
either analyst's word. `consensus-protocol.md:299` reads
"Security/**data-integrity** keyword detected → Always flag for human", and
SC-002 is a data-durability criterion — but the section that defines that row
is titled **Security Keywords** and enumerates a closed list (auth, token,
secret, encryption, PII, credential, permission, password, authentication,
authorization, session, cookie, jwt, api-key, access-control, `:315-322`).
None fire here. The checkable contract therefore does not mandate a stop, and
neither analyst recommended one. Proceeding was the call; the cost is stated
in full in the Q2 revision note rather than smoothed over, and the plan stage
ends before any code is written, so the operator can veto it at that boundary.

Three caveats the analysts flagged rather than asserted were closed by direct
check, not left open: `tests/speckit-pro/layer6-efficiency/fixtures-codex/implement-executor/fixture.json`
does **not** pin the Task Result text (no `Task Result` or `**Errors:**`
substring), so Layer 6 is not at risk; a tree-wide grep confirms the three
authored copies of the Task Result block are the complete set; and Design
Principle #2 plus the "returns all N results together" line were both read
verbatim before being treated as decisive.

One caveat is left open on purpose, because it is genuinely undocumented:
`isolation: "worktree"` merge-back semantics are not described anywhere in this
repo. It does not change the outcome — an executor-side append is unsafe for a
shared file regardless, since N isolated copies each fork from the same
pre-run state — but the orchestrator-writes-it decision rests on that reasoning
rather than on a citable platform guarantee.

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
- Reviewability budget ~162 LOC (modify-weighted), primary surface
  harness/adapter, 5 production files, ~8 total files (see the Reviewability
  Setup Gate above for the full budget and estimator output).
  *Corrected 2026-08-10 at Analyze: this prompt was authored at scaffold time
  and read "~115 LOC ... ~3 production files, ~6 total files", the figures
  Clarify session 1 superseded. Consensus Resolution Log item 1 lists the blocks
  the amendment was meant to reach; this one was missed.*
- Modify-only: this spec edits `phase-execution.md` and `tdd-protocol.md`
  in place; it does not add new template/schema files.
- Reference the Design Concept doc
  (docs/ai/specs/.process/ART-012-design-concept.md) if planning needs
  context beyond this prompt — it is the source of truth for every
  scoping decision (Q1–Q8) captured during grill-me.

## Verified Repository Facts (recorded at Phase 0, 2026-08-10)

Both were confirmed by reading the tree; plan against these, not against
assumptions.

- **The reporting contract is THREE edits, not one. The append logic is two.
  Five production files total.**

  *Corrected 2026-08-10 by Clarify session 1 consensus. The superseded claim
  read "The reporting contract is one shared edit… That is 3 production files."
  It was wrong, and the rationale is preserved here because the error is
  instructive: the injected copy is shared, but two agent definitions hard-code
  their own duplicate of the same block.*

  `grep -rln "Task Result: <TASK_ID>" speckit-pro/` returns exactly three
  authored homes, and FR-001 requires *every* implementation task summary to
  carry the new field, so all three are in scope:

  | File | What changes | Note |
  |---|---|---|
  | `speckit-pro/skills/speckit-autopilot/references/tdd-protocol.md` | Summary Format block (`:124-140`); add the line after `**Errors:**` at `:139` | Shared. Injected verbatim into every implementation dispatch prompt (`phase-execution.md:826-829`, `:918-925`); Codex reaches this same file via `codex-skills/speckit-autopilot/SKILL.md:921`. It is the only copy an implementation-routed agent without its own local block ever sees. |
  | `speckit-pro/agents/implement-executor.md` | Summary Format block (`:139-158`) **and** the Terminal Deliverable enumeration at `:164` | **Two touchpoints.** `:164` is a hard `MUST` listing exactly four fields ("TDD Evidence / Test commands used / Files created/modified / Errors"). Patching the template alone ships a self-contradictory agent. This agent is the default implementation fallback (`phase-execution.md:911`) and the routed agent for test tasks. |
  | `speckit-pro/codex-agents/implement-executor.toml` | Summary Format block (`:121-139`) only | Codex mirror. Confirmed to carry no Terminal Deliverable enumeration, so one touchpoint. |

  Precedent: commit `bb01ef28` added a required line to this same Summary
  Format contract in **both** agent definitions in one commit, for exactly this
  reason — "Agents follow their own output template over referenced contract
  prose." No Layer 1 test diffs Summary Format content across platforms
  (`validate-codex-parity.py` checks agent-file existence, not content), so a
  partial fix would pass CI and still violate FR-001. Enforcement here is
  FR-001 plus the G6 Design-Concept drift check, not a red test.

- **The append logic is mirrored, so it is two edits.** `phase-execution.md` is
  **not** shared the way `tdd-protocol.md` is: Codex carries its own
  `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`.
  The Phase 7 file-lifecycle and append steps must be written into **both**
  `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`
  (`### Phase 7: Implement (Task-Level Dispatch)` at `:788`) and that mirror.

- **Field placement (Clarify Q2, resolved without consensus):** append the new
  `**Deviations/Edge cases/Surprises:**` line **after** `**Errors:**`, making it
  the block's last line in all three copies. `**Errors:**` is currently terminal
  everywhere, so appending leaves every existing line byte-stable and
  position-stable; inserting before it would shift an existing line for no gain.
  No test anchors the field order, so the Layer 4 fixture test defines it.

- **Editing plugin source requires a payload rebuild.** `dist/claude/speckit-pro/`
  and `dist/codex/speckit-pro/` are generated install payloads that mirror these
  files (`dist/claude/speckit-pro/skills/speckit-autopilot/references/tdd-protocol.md`
  and `.../phase-execution.md` both exist; the Codex payload flattens
  `codex-skills/.../references/*` into
  `dist/codex/speckit-pro/skills/speckit-autopilot/references/`). Layer 1
  enforces them via `validate-plugin-payload`, `validate-payload-completeness`,
  and `validate-payload-conformance`. Regenerate with
  `python3 scripts/refresh-release-artifacts.py` — never hand-edit `dist/`
  (AGENTS.md Editing Boundaries). Plan a task for this, or Layer 1 fails.
  *Corrected 2026-08-10 at Analyze: this line named
  `python3 scripts/build-plugin-payloads.py`, which rebuilds the payloads only
  and leaves the installed-cache fixtures and proof hashes stale. See
  "Generated-artifact regeneration chain" under Plan Results, which found the
  second and third surfaces and named the one command that covers surfaces 1
  and 2.*

## Architecture Notes
- **File location:** `specs/<branch>/.process/implementation-notes.md` —
  already decided by the roadmap as "exhaust," not re-litigated here.
- **Field placement (Q6):** extend the existing
  `## Task Result: <TASK_ID>` block with a new
  `**Deviations/Edge cases/Surprises:**` line placed after `**Errors:**` —
  do not introduce a second block. This lands in all three authored copies
  of that block, not just `tdd-protocol.md`; see "Verified Repository Facts".
- **Append cadence (Q2, as amended at Clarify session 2):** the orchestrator
  appends inside the existing Phase 7 Step 3 task loop in `phase-execution.md`,
  not batched at phase end. Two call-site shapes, because the loop has two:
  the singleton/sequential branch waits on one result at a time
  (`phase-execution.md:900-914`, `Wait for result.`), so it appends per task;
  the parallel branch waits on the whole run
  (`:888` `Wait for ALL to complete.`, `:875` for the Agent Teams path), so it
  appends every task in the run at collection, before the next run dispatches.
  The serial re-run fallback after a regression (`:894-898`) is per-task by
  construction and needs no special handling. There are **three** append sites
  in the routing, not one: the executor branch, the research branch, and the
  orchestrator-direct verification branch — the latter two never carry the
  reporting field, and their entries record that nothing was reported.
- **Resume (new at Clarify session 2):** the file-lifecycle step is
  create-if-absent, not create. A resumed Phase 7 re-opens the existing record
  and appends; it must not truncate it or write a second header.
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

**G3 PASS.** `validate-gate` returned
`{"gate":"G3","pass":true,"reason":"plan.md exists with 0 unresolved markers","markers":0,"details":[]}`.

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ | Technical context, execution flow, 8 Declared File Operations |
| `research.md` | ✅ | 11 decisions (R1–R11), zero unresolved unknowns |
| `data-model.md` | ✅ | Notes record, notes entry, task-result summary |
| `contracts/task-result-reporting-field.md` | ✅ | Pins the new line across 4 touchpoints in 3 files |
| `contracts/implementation-notes-record.md` | ✅ | Record format, lifecycle, append cadence |
| `quickstart.md` | ✅ | Scenarios incl. the regeneration chain |

**Constitution re-check after Plan:** pass on all six principles (v1.2.0);
Complexity Tracking table empty, no violation to justify.

#### Plan-phase reviewability budget (step 7b, advisory)

`estimate-reviewable-loc` returned
`{"status":"pass","projected":0,"declared_files":{"production":0,"new":1,"modified":7,"total_entries":8},"greenfield":false}`.

**Read that `0` correctly — it is a classifier limitation, not a measurement.**
All 8 declared entries parsed, but the helper's production-file heuristic only
recognises `src/`, `app/`, `lib/`, `scripts/` prefixes or JS/TS/SQL extensions,
and this spec's entire surface is Markdown and TOML under `speckit-pro/`. The
authoritative projection remains **162** reviewable LOC from `estimate-spec-size`
(recorded under the Reviewability Setup Gate above). Recorded as research R11 so
neither number is read as the other. The helper is advisory and never blocks.

#### Generated-artifact regeneration chain (three surfaces, two commands)

Editing the five production files restales **three** generated surfaces, not
one. The Plan phase found the second and third; both are real, and both were
verified directly:

1. **Install payloads** — `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`
   mirror all five files. Layer 1 enforces via `validate-plugin-payload`,
   `validate-payload-completeness`, `validate-payload-conformance`.
2. **Installed-cache fixture and its proof hashes** —
   `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/{claude,codex}/speckit-pro/`
   carries byte copies of all five files, pinned by the per-product
   `source_payload_tree_hash` values inside `proofs[]` in
   `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`.
3. **Docs reference** — `docs-site/src/content/docs/reference/tests.md` restales
   when the new Layer 4 test file is added.

**One command covers surfaces 1 and 2**, and it is *not*
`scripts/build-plugin-payloads.py` alone:

```text
python3 scripts/refresh-release-artifacts.py
```

Its own docstring enumerates six steps — runner trust metadata, rebuild both
payloads (the same `build_xplat008_payloads` the standalone builder calls),
sync marketplace versions, content-sync the installed-cache fixtures, refresh
the proof tree hashes, regenerate gate evidence — and states it is idempotent.
It explicitly does **not** regenerate the docs reference, so surface 3 needs its
own command after a `pnpm --dir docs-site install --frozen-lockfile`:

```text
pnpm --dir docs-site reference:generate
```

Never hand-edit `dist/`, the installed-cache fixture, or the proof JSON.

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
- Does spec.md require appends at the right granularity — immediately after
  each singly or sequentially dispatched task, and at run collection for a
  task inside a parallel run — and never batched to phase end? (FR-003 was
  amended at Clarify session 2 to this two-branch cadence; the amendment is
  deliberate and recorded in the Design Concept's Q2 revision note, so do
  NOT report the two-branch wording as drift.)
- Does spec.md require a retried task (parallel-run regression → serial
  re-run) to append a second entry rather than overwrite the first?
- `--from-phase` resume behavior was resolved at Clarify session 2: FR-002 is
  create-if-absent, and no already-recorded-task detection is wanted — a
  re-executed task appends another entry. Verify spec.md actually says both,
  rather than re-opening the question.
```

### Checklist Results

**G4 PASS.** `validate-gate` returned
`{"gate":"G4","pass":true,"reason":"0 [Gap] markers","markers":0,"details":[]}`,
cross-checked by an independent tree-wide grep. Layer 1 re-run green at
1447/1447 after both domains' edits.

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| error-handling | 28 (CHK001–CHK028) | 6 found, 6 remediated, 0 outstanding | FR-002, FR-003, FR-004, SC-001, SC-004, Edge Cases; plan §Failure behavior; record contract Lifecycle/Coverage/Fail-open |
| state-management | 30 | 8 found, 8 remediated, 0 outstanding (+1 `[Conflict]` closed by the same work) | FR-002, FR-003, SC-006, Edge Cases, 3 new Assumptions; plan §Orchestrator file lifecycle |
| **Total** | **58** | **14 found, 14 remediated, 0 outstanding** | |

**What error-handling changed.** Six gaps, each closed against repo precedent
rather than invention: a failed write is now explicitly never retried (an
implementer could otherwise have added a blocking retry loop on a file the
phase does not depend on); FR-004's gap destination was circular and could be
read as the very record that just failed; the gap's required *content* was
unspecified, so SC-004 was checkable only as "some gap exists somewhere"; a
field present but unreadable was uncovered, distinct from a field absent, and
neither is a write failure; **the fail-open path's own failure was untraced**,
now bounded to exactly one fallback level so the failure path cannot loop; and
**failure isolation inside a collected parallel run was unspecified**, so one
failing append could plausibly have aborted the rest of the batch.

**What state-management changed.** Eight gaps in three clusters. **Entry order
was never a requirement** — it lived only in Edge Cases and `data-model.md`,
both of which derive from spec.md rather than bind it, and SC-006 promised a
reader could recover an entry's task ID and text but never its sequence, which
is the whole question once two entries share a task ID. FR-003 now makes
document order append order, and states that entries carry no timestamp and no
attempt number, so position is the only ordering signal. **The ordering
guarantee silently assumed a single writer**: the run-state guard deliberately
does not block a second run that finds one in progress
(`SKILL.md:389-392` — the state file carries no pid, heartbeat, or lease), so
two runs can interleave appends; a new Assumption scopes the guarantee to the
owning orchestrator and records that nothing coordinates concurrent writers. No
lock was added — it would contradict the no-block rule and is unjustified for
exhaust. **What a resume checks was unstated**: FR-002 now requires existence
to be determined from the record's own path in the working copy the run
executes in, never from a state file or anything carried from the session that
wrote it, because the documented resume protocol reconstructs from the workflow
file, which never mentions this record. And **the read window was unbounded**:
archive cleanup removes the feature directory from active `specs/` after merge,
so a new Assumption pins the path's lifetime to the feature directory's,
records that consumers read it in place pre-merge, and points post-archive
readers at commit history.

Three items were verified without change rather than edited: FR-003's parallel
bound still excludes phase-end batching even for a phase's final run, because
"no later than the orchestrator's next turn after that run" binds when "before
the next run is dispatched" goes vacuous; a task ID stale against a regenerated
`tasks.md` costs a cross-reference but never legibility, since SC-006 keeps
entries readable without lookup; and the record stays out of resume-critical
state because Key Entities classifies it as exhaust nothing depends on.

A security-keyword sweep over the remediated text hit only `session`, three
times, every one in the CLI-session sense ("a resume in a fresh session"). No
`[security]` routing was warranted.

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
3. User Story 2 (executor reporting contract, P1) — wire the new field into
   every authored copy of the `## Task Result: <TASK_ID>` block. There are
   THREE, and this is four touchpoints, not one shared edit: the injected
   `tdd-protocol.md` template; `speckit-pro/agents/implement-executor.md`'s own
   template **and** its Terminal Deliverable four-field enumeration at `:164`;
   and `speckit-pro/codex-agents/implement-executor.toml`'s own template. See
   "Verified Repository Facts" above for the full table and the `bb01ef28`
   precedent. Independently testable via Layer 1 + Codex parity.
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

**G5 PASS.** `validate-gate` returned
`{"gate":"G5","pass":true,"reason":"13 tasks found","markers":0,"task_count":13}`.

| Metric | Value |
|--------|-------|
| **Total Tasks** | 13 (T001–T013) |
| **Phases** | 4 populated — Foundational (1), US1 (4), US2 (4), Polish (4). Setup is deliberately 0: modify-only change, no bootstrap. |
| **Parallel Opportunities** | 5 `[P]` — T007/T008/T009 (three separate reporting-contract files), T010/T011 (disjoint generated surfaces, different toolchains). Four deliberate exclusions are tabulated: T003/T004 same file, T002/T006 same file, T005 mirror-content dependency, T012 depends on both regenerations. |
| **User Stories Covered** | US1 (P1, MVP) and US2 (P2); a Requirement Coverage table maps all 5 FRs and all 6 SCs to tasks |

All five production files have tasks: `phase-execution.md` (T003 + T004),
`phase-execution-codex.md` (T005), `tdd-protocol.md` (T007),
`implement-executor.toml` (T008), `implement-executor.md` (T009, both
touchpoints including the Terminal Deliverable enumeration). The new Layer 4
test is T002, registered in `suite-manifest.json` by the same task — without
that registration it would never run. Both regeneration commands have tasks
(T010, T011), and no task invokes `build-plugin-payloads.py` alone.

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

Recorded 2026-08-10 after G5. Classifier output, verbatim:
`{"route":"one-navigable-PR","releasable":true,"signals":["change-shape:modify-heavy"],"hints":[],"warnings":[]}`

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | `true` | `true`, or `false` for a destructive-migration or concurrency-sensitive change (a passing CI run does not prove such a change is safe to release). |
| **Signals** | `change-shape:modify-heavy` | The decisive detector findings behind the route and releasability reading (may be empty when the classifier abstains). |
| **Warnings** | none | Any release-safety warning attached to the change (empty when there is no releasability risk). |

## Layer Plan

**Status: `skipped` — the route is not `split-PR`.** The layer planner runs only
for a split route. `one-navigable-PR` means this ships as a single reviewable PR,
so no layer plan is produced and no PR marker plan is required. Recorded as
`layer_plan.status = "skipped"` in `autopilot-state.json`, and the run continues
with route context.

## Tasks-Phase Reviewability Boundary

**The runner's `reviewability-gate` tasks mode is deferred on this installation.**
Confirmed once, not retried: a `read_only` request with `mode_name: "tasks"`
returned `code: "invalid_input"`, `message: "read-only helper rejected the request
inputs"`, `details.exit_code: 2`. Setup mode is the only active mode. Per the
autopilot contract this is recorded and the run continues on the committed
fallback evidence chain rather than treating the deferral as a gate failure.

| Deferred-mode diagnostic | Value |
|---|---|
| Helper ID | `reviewability-gate` |
| Requested mode | `tasks` |
| Result | `invalid_input`, exit code 2, inputs rejected |
| Deferral reason | tasks mode is not implemented on the installed runner; setup mode only |

**Fallback evidence chain, all three current and all non-blocking:**

1. **Setup-mode gate at scaffold** — `status: "warn", pass: true`, single warning
   `primary surfaces 3 exceeds warn threshold 1`, which is a whole-roadmap scan
   artifact rather than this spec's own count. Recorded above with the scope
   budget and split decision the warning requires.
2. **Plan-phase `estimate-reviewable-loc`** — `status: "pass"`, 8 declared entries
   parsed. Its `projected: 0` is a classifier limitation on a Markdown/TOML
   surface, not a measurement; the authoritative projection is 162 LOC.
3. **Split decision** — one vertical slice, no split, from `estimate-spec-size`
   re-run at Clarify with corrected signals.

`pass`, `warn`, and honoured exceptions are all marker-planning inputs, so the
boundary is satisfied and no manual re-slicing stop applies. No correctness stop
condition is present: marker state is not malformed or stale, no verification
failed, no packet is invalid, and there is no non-size safety finding.

To produce the decision, run the classifier against the feature directory:

```text
runner helper atomicity-route specs/art-012-implementation-notes-capture
```

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

**G6 PASS.** 13 findings, zero CRITICAL, all 13 remediated in one loop.
`count-markers` in findings mode over `specs/art-012-implementation-notes-capture`
returned `{"type":"findings","total":0,"critical":0,"high":0,"medium":0,"low":0}`
before and after remediation. Constitution v1.2.0 re-checked: pass on all six
principles, no new violation, Complexity Tracking still empty. Coverage
re-confirmed: all 5 FRs and all 6 SCs map to tasks, all 8 of plan.md's Declared
File Operations have a task, and every path named in tasks.md exists in the tree
or is correctly marked NEW. Layer 1 re-run after the edits: 1447/1447, unchanged
from the G0 baseline.

Neither authorised amendment was reported as drift: Q2's two-branch cadence
(dated revision note under Q2) and the 3 → 5 production files / 115 → 155 LOC
restatement (Consensus Resolution Log item 1) are both correctly carried.

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| A1 | HIGH | `quickstart.md` Scenario 4 ran `scripts/build-plugin-payloads.py` and then described refreshing the installed-cache fixture and both proof hashes by hand — the exact command T010 forbids, and a hand-edit of generated artifacts that AGENTS.md treats as blocking. T012 requires the quickstart scenarios to pass, so the two artifacts could not both be satisfied. | Scenario 4 now runs `python3 scripts/refresh-release-artifacts.py` and states why the standalone builder is insufficient. |
| A2 | HIGH | `research.md` R9's Decision still recorded the superseded two-step regeneration (builder, then refresh fixture and hash). `plan.md` cites R9 as the authority for the opposite rule. | R9's Decision restated on `refresh-release-artifacts.py`, with the builder's actual scope (one `build_xplat008_payloads` call) as the reason it is not sufficient alone. |
| A3 | HIGH | `plan.md` named `scripts/build-plugin-payloads.py` as the build command in Technical Context and again in the Declared File Operations generated-surfaces block. | Both now name `scripts/refresh-release-artifacts.py`; the generated-surfaces block states that one idempotent command covers all three listed outputs. |
| A4 | HIGH | T004's "Where" listed three dispatch anchors and omitted the Agent Teams parallel path (`Wait for all teammates to complete.`, `phase-execution.md:875`). That is the `AGENT_TEAMS_AVAILABLE` branch of the same parallel run; tasks dispatched through it would have produced no entries at all, which SC-001 counts as a violation. The Design Concept's Q2 revision note and research R3 both cite `:875` alongside `:888`. | T004's "Where" now lists four dispatch-shape anchors including the Agent Teams path, names the `# Safety net for either path` convergence where one instruction covers both parallel paths, and separates dispatch-shape anchors from the three routing call sites. |
| A5 | HIGH | Three blocks in this workflow file still carried the superseded budget (115 LOC / 3 production files / 6 total): the Specify Prompt Constraints, the G1 Specify Results paragraph, and the Plan Prompt Constraints. `spec.md` and the roadmap both said 155 / 5 / 8. | All three restated to 155 / 5 / ~8, each with a dated correction note preserving the superseded figures and pointing at Consensus Resolution Log item 1. |
| A6 | MEDIUM | `contracts/task-result-reporting-field.md` assertion 4 and T006 item (4) required "the set of files carrying a `## Task Result: <TASK_ID>` block is still exactly those three" with no scope. Tree-wide the block also appears in 2 `dist/` payload copies and 2 installed-cache fixture copies, so the assertion is false on a clean tree and the Layer 4 test would fail the moment it ran. `quickstart.md` already scoped its grep to `speckit-pro/`. | Both now scope the assertion to `speckit-pro/` and name the generated copies as the reason. |
| A7 | MEDIUM | `quickstart.md` Scenario 2 expected the fail-open rule with "its three properties", omitting the property that the gap names the attempt or lifecycle step plus the failed operation. FR-004, `plan.md`, both contracts, T004 and T005 all state four, and the omitted one is exactly what SC-004 checks. | Scenario 2 now expects four properties, naming the gap-identifiability property first. |
| A8 | MEDIUM | SC-001's fail-open exclusion covered only a failed append, while SC-002 and SC-003 both covered "creating the record or appending an entry". A run whose record could never be created left SC-001 asserting an entry count against a file that does not exist. | SC-001's clause now matches SC-002 and SC-003's wording and states that such a run is measured by its gaps. |
| A9 | MEDIUM | The Specify Results metrics table recorded "FR-001 through FR-004 (4)" and "8 acceptance scenarios (5 under US1, 3 under US2) + 7 edge cases". `spec.md` now carries 5 FRs, 10 acceptance scenarios (7 under US1) and 12 edge cases after Clarify session 2. | Both rows corrected to the counted values, each with a dated note naming the superseded figures and the session that changed them. |
| A10 | LOW | `spec.md`'s Reviewability Budget described the 155 estimator run as using "this spec's corrected shape — 2 user stories, 5 production files, 4 functional requirements". That run predates FR-005, so the spec now carries 5. | The clause now dates the run to Clarify session 1, notes FR-005 is a parity clause adding no production file, and records the verbatim 5-FR re-run `{"estimated_loc": 162, "suggested_slices": 1, "status": "ok"}` — same verdict, same single slice. **Orchestrator override:** the executor re-ran the estimator, got 162, then kept 155 "so every artifact quotes one number". That inverts the rule it was applying — the roadmap's own ART-015 precedent is that the estimator is re-fed rather than hand-held, and this run had already corrected a stale 102 to 115 at scaffold review for the same reason. Re-running with the spec's current shape (2 stories, 5 files, 5 FRs, modify) returns `{"estimated_loc": 162, "suggested_slices": 1, "status": "ok"}`, so **162 is now the recorded figure in all three homes** and consistency is preserved by updating them together. The verdict is unchanged: one slice, `ok`, far under the 400 warn line. |
| A11 | LOW | The roadmap's ART-012 status row read "(estimator: 115 LOC, ok)" with no pointer to the amendment, though the roadmap's own Reviewability Budget block was already correct. | Row now reads "scaffold estimator: 115 LOC, ok; re-estimated 155 at Clarify session 1" and points at the budget block. |
| A12 | LOW | Verified Repository Facts still said "Regenerate with `python3 scripts/build-plugin-payloads.py`", superseded ~90 lines later by the Plan Results regeneration chain. | Corrected in place with a dated note pointing at that chain. |
| A13 | LOW | `plan.md` introduced its routing table as "three call sites" and then listed four rows; the fourth is a value case on the first site. | Lead-in now says so explicitly. |

---

## Phase 6.5: Confidence Gate

**When to run:** After Phase 6 commits and before Phase 7 begins. Gate semantics
are unchanged; this section records the verdict so a later session can read it.

| Field | Value |
|-------|-------|
| Mode | advisory (resolved at Step 0.6b: no `--strict` / `--advisory` flag, no local config) |
| Composite confidence | 0.93 |
| Verdict | proceed |
| Threshold | 0.90 |
| Evidence | Six planning gates green (G1–G6), full suite 7226/7226 at the G0 baseline, 5 FRs and 6 SCs all task-mapped, 8/8 declared file operations tasked, three consensus rounds resolved, 14 checklist gaps and 13 analyze findings all remediated |

Orchestrator synthesis. The per-criterion scores below are the gate's input; the
one below 0.90 is deliberate and explained.

📊 Confidence: 0.93
- Task understanding: 0.97
- Approach clarity: 0.95
- Requirements alignment: 0.95
- Risk assessment: 0.85
- Completeness: 0.94

**Why risk assessment is the lowest score.** Not because a risk is unmanaged —
each identified one is bounded and recorded — but because one carries an open
question only the operator can close. The two-branch append cadence narrows a
durability guarantee the operator personally chose in Design Concept Q2, and
that narrowing was resolved by consensus rather than ratified by them. The
checkable stop conditions did not fire and both analysts recommended proceeding,
so the run continued; but until the operator reads the Q2 revision note and
either accepts it or asks for the lossless alternative, the risk is open rather
than closed. The plan stage ends here, before any code is written, which is
exactly the boundary where that call belongs.

The other risks are bounded and recorded, not open: the parallel-run loss window
is one run rather than the whole phase; concurrent writers are documented as
uncoordinated by design, with no lock added because it would contradict the
no-block rule for exhaust; the three generated surfaces each have a task and two
commands cover them; and the plan-phase estimator's `projected: 0` is a
documented classifier limitation, not a measurement.

**Gate result.** Composite 0.93 ≥ threshold 0.90 → `pass: true`,
`recommended_action: "proceed"`. In advisory mode this would not have blocked
even below threshold, so the score is recorded as information for the operator
rather than as a hurdle the run cleared.

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
