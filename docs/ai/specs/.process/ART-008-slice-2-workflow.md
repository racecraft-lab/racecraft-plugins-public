# SpecKit Workflow: ART-008 slice 2 — Artifact Freshness

**Template Version**: 1.0.0
**Created**: 2026-08-24
**Purpose**: Execute ART-008 slice 2 (artifact freshness) through the SpecKit workflow. The prompts below are what each phase executes.

---

## How to Use This Template

1. **Scope: slice 2 only.** ART-008 ships as two stacked slices. Slice 1 (the
   checkpoint) merged in PR #464 on 2026-08-24 at `8db22a420` and is part of
   `main`, so this branch is cut from `main`, not from a live slice-1 branch.
   This workflow drives slice 2: whole-set regeneration after amendments,
   stale-page detection on a clean sweep, and the draft-description refresh.

2. This file was authored from a fresh grill-me interview (7 questions,
   2026-08-24) recorded in `ART-008-slice-2-design-concept.md`, layered on the
   slice-1 decisions in `ART-008-design-concept.md`, which are carried, not
   re-asked.

3. **Track progress** using the status table below.

---

## Design Concept

Two records govern this slice, in priority order:

```text
docs/ai/specs/.process/ART-008-slice-2-design-concept.md   (this slice's decisions)
docs/ai/specs/.process/ART-008-design-concept.md           (whole-spec decisions, carried)
```

Re-read the slice-2 doc before each phase if a prompt needs disambiguation. The
Specify and Clarify Prompts below were populated from its Q&A log, so it is the
source of truth for any decision captured during scoping. Carried slice-1
decisions this slice builds on: Q8 (a clean sweep with stale pages regenerates,
refreshes, and proceeds), Q9 (whole-set regeneration), Q11 (the description
refreshes through ART-007's create-or-refresh path).

> **Note:** Grill Me is human-in-the-loop only. It is **not** part of
> the autopilot loop. Once the workflow file is populated and autopilot
> begins, clarifications happen via `/speckit-clarify` and the
> consensus protocol — never via grill-me.

---

## Slice Plan

| Slice | Branch | Base | State |
|---|---|---|---|
| 1, the checkpoint | `art-008-feedback-sweep` | `main` | **Merged, PR #464, `8db22a420`** |
| 2, artifact freshness | `art-008-feedback-sweep-slice-2` | `main` (slice 1 already in) | **this run** |

**Stacked in sequence, not in branches.** The roadmap's slice table predates the
slice-1 merge and says "from slice 1"; slice 1 is in `main` now, so basing on
`main` is the same content with a simpler PR.

### Reviewability budget — estimator distrusted by prior measurement

Runner `estimate-spec-size` with slice-2 signals (3 user stories, ~10 files,
~14 FRs, modify-weighted) returned:

```text
{"estimated_loc": 75, "suggested_slices": 1, "status": "ok"}
```

**Treat that number as advisory noise, not a measurement.** The estimator
classifies none of this slice's paths as production (blind-spot finding 3): it
false-zeroed on slice 1, which shipped 515–830 measured LOC against a
whole-spec estimate of 452. **Plan MUST size this slice by hand from its
Declared File Operations block**, exactly as slice 1's Plan did, and re-declare
the budget in `spec.md` §Reviewability Budget.

```text
Projected reviewable LOC: re-measure at Plan (hand-derived; estimator returns a false zero on these paths)
```

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ⏳ Pending | |
| Clarify | `/speckit-clarify` | ⏳ Pending | Sessions seeded from the design concept's Open Questions |
| Plan | `/speckit-plan` | ⏳ Pending | Hand-size the budget here; estimator is a false zero |
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

**Installed-plugin note.** The plan stage of this run executes from the
installed plugin. If that plugin is 2.27.0, it carries ART-007's draft-PR
emission (the plan stage ends at an open draft PR) but **not** slice 1's
feedback sweep, which merged after 2.27.0 was cut — so this run's implement
stage opens the pre-ART-008 way unless a newer release lands and the cache
refreshes first. Record at Step 0 which plugin version actually ran.

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
| I. Plugin Structure Compliance | Manifests valid, loader frontmatter well-formed | `python3 tests/speckit-pro/run-all.py --layer 1` |
| II. Cross-Platform Runtime & Script Safety | Python 3.11+ stdlib only; no new Bash/`jq` dependency | Layer 1 interpreter-contract tests |
| III. Semantic Versioning | No hand-edited versions; release-please owns bumps | `git diff` review |
| IV. Test Coverage Before Merge | Full suite zero failures | `python3 tests/speckit-pro/run-all.py` |

**Constitution Check:** ⏳ (mark before proceeding to G1)

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | ART-008 (slice 2 of 2) |
| **Name** | Feedback Sweep — Artifact Freshness |
| **Branch** | `art-008-feedback-sweep-slice-2` |
| **Dependencies** | ART-007 (shipped, PR #445); ART-008 slice 1 (shipped, PR #464) |
| **Enables** | The trusted human checkpoint reviews CURRENT pages; closes ART-008 |
| **Priority** | P1 |

### Success Criteria Summary

- [ ] After a sweep amends planning artifacts, the whole draft page set is
      regenerated and the draft description refreshed **before** the re-review
      stop, in the same run.
- [ ] On a clean sweep, stale pages (amendment commits newer than the last
      `artifacts/` commit) are detected deterministically, regenerated,
      refreshed, and the run proceeds — no stop (slice-1 Q8).
- [ ] Page selection is re-derived from the gallery manifest against the
      amended record; removals are reported, never silent.
- [ ] Regeneration gaps land in ART-007's three sinks through the emission
      machinery; the sweep itself still never writes the `Draft PR` row.
- [ ] The stop report's slice-1 promise sentence is replaced by outcome lines
      (per-page outcomes, regeneration commit, refresh result).
- [ ] The staleness verdict is a deterministic read-only runner helper with
      Layer 4 fixtures; Codex parity validators pass.

---

## Phase 1: Specify

**When to run:** At the start. Focus on **WHAT** and **WHY**. Output: `specs/art-008-feedback-sweep-slice-2/spec.md`

### Specify Prompt

```text
/speckit-specify

## Feature: ART-008 slice 2 — Artifact Freshness

### Problem Statement
Slice 1 (merged, PR #464) sweeps draft-PR feedback and amends planning
artifacts through consensus, but the draft artifact pages and the draft
pull-request description still describe the pre-amendment plan. Its stop
report apologizes with a promise: "draft artifact pages regenerate once
slice 2 lands" — a sentence phase-execution.md:1874 marks as "an interface
slice 2 replaces." This slice replaces it: the re-reviewer at the checkpoint
must read pages that match the amendments beside them.

### Users
The operator re-reviewing a draft PR after a sweep amended the plan; the
reviewer reading draft artifact pages; the next autopilot run deciding
whether pages are current.

### User Stories
1. [US1] After amendments, the run regenerates the whole draft page set and
   refreshes the description BEFORE stopping for re-review (interview Q3), so
   the checkpoint reviews the current plan.
2. [US2] On a clean sweep, the run detects pages left stale by a prior run
   (the recovery path: a run that died between amending and regenerating),
   regenerates, refreshes, and proceeds without stopping (slice-1 Q8 carried).
3. [US3] The operator reads one honest report: per-page outcomes
   (generated/gap with reason), the regeneration commit sha, and the refresh
   result; on a fresh clean sweep, one line stating pages are current as of
   the named commit (interview Q7).

### Settled design decisions (from the slice-2 grill-me, quote on conflict)
- Staleness primitive (Q1): git-history join — pages are stale when any
  Feedback Sweep Log row with class `amended` names a Commit newer than the
  last commit touching specs/<feature>/artifacts/. No content hashing: pages
  are agent-authored prose, identical inputs yield different bytes.
- Gap reporting (Q2): regeneration rides the same ART-007 emission machinery
  the description refresh uses (slice-1 Q11), and that machinery owns all
  three shortfall sinks — the description's gap rows, the Draft PR row's
  note, the run report. The sweep itself NEVER writes the Draft PR row.
- Timing (Q3): amend → regenerate → refresh → stop. The clean-sweep path is
  recovery, not the primary path.
- Commit shape (Q4): one dedicated docs: commit staging
  specs/<feature>/artifacts/ alone. This is what makes the Q1 join exact.
- Set semantics (Q5): re-select from the gallery manifest against the amended
  record; author every selected page fresh; remove deselected pages on disk,
  reported, never silent.
- Testability (Q6): the staleness decision is a new deterministic read-only
  runner helper (observation in, verdict + page set out) with Layer 4
  fixtures, on the sweep-pr-feedback pattern.
- Report (Q7): outcome lines replace the promise sentence.

### Constraints
- Python 3.11+ standard library only for runner code; no new Bash/jq.
- Both platforms: Claude references and codex-skills mirrors stay in step.
- The Codex autopilot SKILL.md body has ZERO headroom (8000/8000 words);
  slice-2 behavior lands in references/, never in SKILL.md, unless words are
  freed first.
- Generated artifact contract: any speckit-pro/ source change requires
  payload + proof regeneration before the work is done.

### Out of Scope
- Any change to slice 1's sweep: reading, trust filter, classification,
  consensus amendment, log rows, replies, stop-or-proceed.
- Content-hash staleness; any new bookkeeping store beside the Feedback
  Sweep Log; a second writer of the Draft PR row.
- Post-implementation review remediation (existing /loop machinery).
```

### Specify Results

<!-- Fill in after running the command -->

| Metric | Value |
|--------|-------|
| Functional Requirements | |
| User Stories | |
| Acceptance Criteria | |

### Files Generated

- [ ] `specs/art-008-feedback-sweep-slice-2/spec.md`

---

## Phase 2: Clarify

**Best Practice:** Maximum 5 targeted questions per session. Sessions are
seeded from the design concept's Open Questions.

### Clarify Prompts

#### Session 1: Refresh-failure semantics

```text
/speckit-clarify Focus on failure semantics of the regenerate-and-refresh
sequence: what happens when the description refresh fails mid-Phase-7 (tool
unreachable, rate-limited, identity mismatch, pr_closed/pr_missing)? The
design concept's expectation is to inherit ART-007's rule — a failed step
stops the sequence where it failed, the operator re-run is the recovery, and
the Q1 staleness join is exactly what makes that re-run converge — but the
interview ended before walking it. Settle each corroboration status against
phase-execution.md §create-or-refresh, and settle what a failed regeneration
dispatch (as opposed to a per-page gap) does.
```

#### Session 2: Helper contract and observation shape

```text
/speckit-clarify Focus on the staleness helper's exact contract: the
observation fields the orchestrator gathers (last artifacts/ commit, Feedback
Sweep Log rows, ancestry facts), how commit recency is established from
observation data alone (the helper must stay offline and deterministic — it
never runs git), the verdict schema, and how the page set to regenerate is
represented. Follow the sweep-pr-feedback precedent: orchestrator observes,
helper classifies, golden fixtures assert.
```

#### Session 3: Report and parity surface

```text
/speckit-clarify Focus on where the outcome lines land (stop report on the
amended path, proceed report on the clean-stale path), the exact sentences
that replace the slice-1 promise at phase-execution.md:1874 and its Codex
mirror, and which files under codex-skills/ must change to keep
validate-codex-parity green. The Codex SKILL.md body is at 8000/8000 words:
if any SKILL.md sentence must change, words must be freed first.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Refresh-failure semantics | | |
| 2 | Helper contract | | |
| 3 | Report & parity | | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/art-008-feedback-sweep-slice-2/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack
- Runner helpers: Python 3.11+ standard library only
  (speckit-pro/speckit_pro_runner/helpers/read_only.py + registry.py)
- Orchestrator behavior: Markdown skill references
  (speckit-pro/skills/speckit-autopilot/references/phase-execution.md,
   workflow-file-protocol.md) with byte-parity Codex mirrors under
  speckit-pro/codex-skills/
- Tests: tests/speckit-pro/ (Layer 4 unit fixtures; Layer 1 structural)
- No new Bash or jq dependency; no shell fallback

## Constraints
- HAND-SIZE THE BUDGET. The estimator returns a false zero on these paths
  (it did on slice 1: estimated 452 whole-spec, slice 1 alone shipped
  515-830). Derive the reviewable-LOC declaration from this plan's own
  Declared File Operations block and record it in spec.md §Reviewability
  Budget, with the split lever named if the high end approaches 800.
- The regeneration commit stages specs/<feature>/artifacts/ alone (Q4);
  the bookkeeping commit stages the workflow file path alone (slice-1 rule);
  neither may be merged into the other.
- The staleness helper is offline and deterministic: the orchestrator
  gathers every git fact and passes it as data. The helper never executes
  git, gh, or the network.
- Adding a helper restales the installed-cache fixture copies of the runner
  sources; plan the regeneration step (slice-1's Assumptions record this as
  required, not optional).
- Payload regeneration (scripts/refresh-release-artifacts.py) and docs-site
  reference regeneration are required before the gate.

## Architecture Notes
- Reuse, do not fork: page authoring is the artifact-author dispatch
  (manifest-driven selection); description refresh and shortfall sinks are
  ART-007's create-or-refresh machinery. Slice 2 adds the trigger sites and
  the staleness verdict, not new generation or emission code.
- The design concept (ART-008-slice-2-design-concept.md) is the source of
  truth for the seven settled decisions; re-read it before drafting.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | |
| `research.md` | ⏳ | |
| `data-model.md` | ⏳ | |
| `contracts/` | ⏳ | |
| `quickstart.md` | ⏳ | |

---

## Phase 4: Domain Checklists

**Target: 2-4 domains.** Chosen from the slice's risk profile.

### Step 2: Run Enriched Checklist Prompts

#### 1. error-handling Checklist

Why this domain: the slice's whole surface is failure paths — per-page gaps,
failed regeneration dispatch, failed refresh, and the recovery loop.

```text
/speckit-checklist error-handling

Focus on ART-008 slice 2 requirements:
- Per-page gap outcomes vs a failed regeneration dispatch: different
  severities, different sinks, both reported
- Every create-or-refresh corroboration status has exactly one behavior
- The clean-sweep-stale path proceeds; the amended path stops; a died run
  is recoverable through the Q1 join on re-run
- Pay special attention to: a partial regeneration followed by a successful
  refresh — the description must tell the truth about the gap
```

#### 2. state-management Checklist

Why this domain: staleness is derived state from git history plus the
Feedback Sweep Log, with strict commit-ordering rules.

```text
/speckit-checklist state-management

Focus on ART-008 slice 2 requirements:
- The Q1 join's ordering facts: what exactly makes an amendment commit
  "newer" than the last artifacts/ commit, and how the observation encodes it
- The dedicated regeneration commit is what stamps generation time; nothing
  else may touch artifacts/ in the sweep's command set
- Re-selection semantics: removed pages, newly selected pages, and what the
  log records about each
- Pay special attention to: idempotence — a re-run after a completed
  regenerate-refresh cycle must find pages fresh and do nothing
```

#### 3. requirements Checklist

Why this domain: the slice replaces a shipped interface sentence and touches
a merged spec's contracts; drift between slice-1 text and slice-2 behavior is
the likeliest silent defect.

```text
/speckit-checklist requirements

Focus on ART-008 slice 2 requirements:
- Every slice-1 sentence that promises slice-2 behavior is either replaced
  or still true (the stop-report promise, the quickstart inheritance notes,
  SC-008's standing guarantee)
- The sweep-never-writes-the-Draft-PR-row invariant survives verbatim
- Pay special attention to: FR coverage for the outcome-lines report on BOTH
  paths (stop and proceed)
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| error-handling | | | |
| state-management | | | |
| requirements | | | |
| **Total** | | | |

---

## Phase 5: Tasks

**When to run:** After checklists complete. Output: `specs/art-008-feedback-sweep-slice-2/tasks.md`

### Tasks Prompt

```text
/speckit-tasks

## Task Structure
- Small, testable chunks; TDD for every helper change (fixture first, red,
  then implement)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: helper + fixtures → reference prose (both platforms)
  → regeneration/refresh wiring → report sentences → payload + proof + docs
  regeneration
- Mark parallel-safe tasks with [P]
- Organize by user story

## Constraints
- Bound by the design concept's Non-goals: no slice-1 behavior change, no
  content-hash staleness, no second bookkeeping store, no second Draft PR
  row writer. Flag any task that would cross these.
- Include the generated-artifact tail explicitly as tasks: installed-cache
  fixture regeneration, scripts/refresh-release-artifacts.py, docs-site
  reference:generate, and the full-suite gate.
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
the read-only atomicity classifier and records its decision here. Leave blank
during scoping.

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | | `true`, or `false` for a destructive-migration or concurrency-sensitive change. |
| **Signals** | | The decisive detector findings (may be empty). |
| **Warnings** | | Any release-safety warning (empty when none). |

```text
runner helper atomicity-route specs/art-008-feedback-sweep-slice-2
```

---

## Phase 6: Analyze

### Analyze Prompt

```text
/speckit-analyze

Focus on:
1. Constitution alignment — stdlib-only helper, no new Bash/jq, versioning
   untouched
2. Coverage gaps — every FR and user story has tasks; both report paths
   (stop and proceed) covered
3. Drift against the design concept (ART-008-slice-2-design-concept.md):
   the seven settled decisions and the carried slice-1 decisions are the
   source of truth; a downstream artifact contradicting them is wrong unless
   an explicit revision note says otherwise
4. Drift against shipped slice-1 text: the promise sentence replacement,
   the quickstart inheritance notes, SC-008, and the
   sweep-never-writes-the-row invariant
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| | | | |

---

## Phase 6.5: Confidence Gate

| Field | Value |
|-------|-------|
| Mode | <!-- advisory (default) or strict --> |
| Composite confidence | |
| Verdict | |
| Evidence | |

---

## Phase 7: Implement

### Implement Prompt

```text
/speckit-implement

## Approach: TDD-First

For each task: RED (failing test/fixture) → GREEN (minimum implementation)
→ REFACTOR → VERIFY.

### Pre-Implementation Setup
1. Verify the suite baseline: python3 tests/speckit-pro/run-all.py
2. PYTHONPATH=speckit-pro for every runner probe — the installed plugin
   cache reports a tree you did not edit
3. Gate on the changed test file while iterating; a speckit-pro/ edit
   stales the payload and reds ~6 unrelated gate tests with an opaque
   AssertionError: 1 != 0 until regeneration — noise, not signal

### Implementation Notes
- Consult the design concept's Q&A log for the "why" behind each decision;
  surface any tasks.md gap against it before coding, never silently drop it
- Both platforms move together: Claude reference edit + codex-skills mirror
  in the same task
- Before done: installed-cache fixture regen, refresh-release-artifacts.py,
  pnpm --dir docs-site reference:generate (install already bootstrapped in
  this worktree), full suite zero failures
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation (helper + fixtures) | | | |
| 2 - US1 (regenerate-refresh-stop) | | | |
| 3 - US2 (clean-sweep staleness) | | | |
| 4 - US3 (reports) + Polish | | | |

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
- [ ] Full suite passes: `python3 tests/speckit-pro/run-all.py` (zero failures)
- [ ] Payload + proofs regenerated: `python3 scripts/refresh-release-artifacts.py`
- [ ] Docs reference regenerated: `pnpm --dir docs-site reference:generate`
- [ ] Codex parity validators pass (Layer 1)
- [ ] PR created and reviewed
- [ ] Merged to main branch

**Discharge note carried from slice 1:** the end-to-end sweep→regenerate loop
is prompt-level orchestrator behavior with no automated eval; live evidence
requires an installed plugin carrying BOTH slices, which exists only after a
release cuts from this merge and the cache refreshes. Record what a manual UAT
can and cannot exercise, as slice 1's T098 record did — honestly, not
back-filled.

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
│   ├── speckit_pro_runner/helpers/   # read_only.py: staleness helper lands here
│   ├── skills/speckit-autopilot/references/   # phase-execution.md, workflow-file-protocol.md
│   ├── codex-skills/speckit-autopilot/        # byte-parity mirrors
│   └── artifact-gallery/             # manifest + templates (input, never output)
├── tests/speckit-pro/                # Layer 1/4/5 suites, fixtures
├── docs-site/                        # generated reference pages
└── specs/art-008-feedback-sweep-slice-2/   # this slice's CONTRACT artifacts
```

---

Populated by `/speckit-pro:speckit-scaffold-spec ART-008` (slice 2) on 2026-08-24
from the technical roadmap, the slice-2 grill-me interview, and the blind-spot
pass (ran — 3 findings surfaced, 0 set aside).
