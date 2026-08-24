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
| Specify | `/speckit-specify` | ✅ Complete | 32 FRs, 3 stories, 13 scenarios, 0 markers; G1 pass |
| Clarify | `/speckit-clarify` | ✅ Complete | 3 sessions, 15 questions; 7 consensus items resolved (all Round 1); spec 32→46 FRs; G2 pass, 0 markers |
| Plan | `/speckit-plan` | ✅ Complete | plan.md + research + data-model + quickstart + contract; hand-sized ~690 LOC (556–825) WARN, split lever named; G3 pass |
| Checklist | `/speckit-checklist` | ✅ Complete | 3 domains, 130 items; 34 gaps closed; spec 46→54 FRs; consensus items 8–12; G4 pass |
| Tasks | `/speckit-tasks` | ✅ Complete | 81 tasks (T001–T081), 54/54 FR coverage both directions, 16 [P]; G5 pass |
| Analyze | `/speckit-analyze` | ✅ Complete | 5 findings (0C/1H/1M/3L), all remediated; coverage 54/54 bidirectional; constitution 6/6; G6 pass; 📊 0.92 |
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

**Constitution Check:** ✅ PASS (2026-08-24) — full suite 14012/14012 (L1 1511, L4 12282, L5 219), exit 0.

**G0 test-count baseline:** 14012 total (L1 1511, L4 12282, L5 219) — captured pre-planning 2026-08-24; G7 verifies the count increased against this number.

### Pre-flight Record (Step 0, 2026-08-24)

- `check-prerequisites`: all_pass=true; branch `art-008-feedback-sweep-slice-2` (worktree, non-numeric — `.specify/feature.json` written per slice-1 precedent); SpecKit CLI 0.11.8.
- PROJECT_COMMANDS: FULL_VERIFY=`python3 tests/speckit-pro/run-all.py`; UNIT_TEST same; TYPECHECK/LINT/BUILD=N/A (python stack, test_runner_script evidence).
- PRESET_CONVENTIONS: `speckit-pro-reviewability` v1.0.0 (spec/plan/tasks templates); 18 hook events configured.
- Settings: none — defaults (gate-failure=stop, auto-commit=per-phase, consensus-mode=moderate). CONFIDENCE_GATE_MODE=advisory (resolver, no flag).
- Stage resolution: `plan` (argv) — explicit --stage plan. Draft PR corroboration: no_record (no Draft PR row; no observation taken).
- State slot reclaimed from `docs/ai/specs/.process/ART-008-workflow.md` (prior status: completed).
- Archive Sweep (report-only): `specs/art-008-feedback-sweep` merged via PR #464 (`8db22a420`) — archival operator-deferred until slice 2 merges; current target excluded; no mutation.
- `before_specify` hooks: git.feature satisfied by the existing feature branch `art-008-feedback-sweep-slice-2` + `.specify/feature.json` (script not run; branch verified unchanged before/after Specify); archive sweep discharged report-only at Step -1.
- AGENT_TEAMS_AVAILABLE=false (no TeamCreate in session surface) — parallel work uses batched background subagents.

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
| **Stage** | plan |

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

| Metric | Value |
|--------|-------|
| Functional Requirements | 32 (FR-001–FR-032, contiguous; reverse-citation clean) |
| User Stories | 3 (P1 amended-sweep regeneration, P2 clean-sweep recovery, P3 honest report) |
| Acceptance Criteria | 13 scenarios (4/4/5); 8 success criteria; 10 edge cases |

G1: ✅ pass — `validate-gate` G1 exit 0, 0 markers (bracket and colon forms both grepped by the orchestrator). Privacy scan clean. Preset sections (Reviewability Budget, PR Review Packet Requirements) filled; zero template placeholders. Zero-marker outcome is deliberate: seven settled interview decisions carried "quote on conflict" standing; residual gaps recorded as Assumptions (8).

### Files Generated

- `specs/art-008-feedback-sweep-slice-2/spec.md`
- `specs/art-008-feedback-sweep-slice-2/checklists/requirements.md` (spec-template checklist)

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
| 1 | Refresh-failure semantics | 5 | Fresh live observation at the refresh call site (FR-033); six statuses mapped to ART-007 terminal-step behavior (FR-034); refresh failure ends the attempt only, never stop-or-proceed (FR-035); refresh-only failure is manual recovery, report must say so (FR-036); whole-set gap still refreshes (FR-037); join repairs interrupted not gapped runs (FR-038); Draft PR cell rides the machinery's own record commit (FR-039); artifacts-commit push leg-split (FR-019a); FR-014 false premise corrected (first Phase 7 caller); FR-016/018/022/023 amended. Spec now 40 FRs, reverse-citation clean, 0 markers |
| 2 | Helper contract | 5 | Helper reads the workflow file itself via the shipped heading-anchored table read; git facts + page inventory supplied as data (FR-004 revised, 2/2 analysts). Ancestry encoding, never sha strings or timestamps (FR-004a, FR-008, FR-009). Closed 4-verdict set with fixed precedence (FR-005); undeterminable reports and never acts (FR-005a). Pages-on-disk-no-commit reads stale (FR-007a). Removal diff = second named surface, subtrahend includes gap outcomes (FR-012a). Clarifications section added. Spec now 44 FRs |
| 3 | Report & parity | 5 | One run report on every leg — no separate proceed report; page outcomes land in the what-already-landed part, resume paths in the resume-path part (FR-024/025/026 amended); `removed` added to the outcome enum (FR-024, US3); FR-026/SC-006 collapse scoped to the freshness line; sink #2 at Phase 7 = the run report (FR-021); BOTH promise passages removed on both surfaces (FR-027); parity validator binds nothing at prose level — SC-008 reworded, Claude-only-vocab + pinned-strings authoring rule added (FR-029); Codex SKILL.md measured 7998/8000 (FR-030); fresh `--state all` observation + verbatim classifier reuse (FR-033a/b). Spec now 46 FRs |

### Consensus Resolution Log

| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |
|---|------|----------------------|------------|-------|---------|------------|----------------|
| 1 | Clarify | Refresh-only failure never self-repairs — which record is right? | [spec] | 1 | Resolved (high) | Manual recovery; design concept's Open-Question expectation superseded by spec mechanics; FR-036 with tightened report text | spec-context-analyst |
| 2 | Clarify | Which commit carries a `Draft PR` cell change post-refresh? | [spec] | 1 | Resolved (high) | Reuse the plan-stage record commit verbatim (FR-039); "bookkeeping commit" lexical collision identified; FR-020 unchanged | spec-context-analyst |
| 3 | Clarify | Artifacts-commit push semantics unspecified | [spec] | 1 | Resolved (medium; executor + analyst convergent) | Settle now as FR-019a: push is part of the step; failed push ends emission sequence on both legs; amended leg stops (SC-001), clean leg proceeds (FR-017) | spec-context-analyst |
| 4 | Clarify | Helper reads workflow file vs orchestrator passes rows as data | [spec] [codebase] | 1 | Resolved (high, 2/2 agree) | Helper reads the file (FR-004 revised); shipped sweep-parse precedent + FR-031 fixture mandate; Commit cell must anchor from row end (write-time note for Plan) | spec-context-analyst, codebase-analyst |
| 5 | Clarify | What does `undeterminable` trigger? | [spec] | 1 | Resolved (high) | Report loudly, act never (FR-005a); regeneration on undeterminable livelocks — unjoinable rows never self-repair | spec-context-analyst |
| 6 | Clarify | What "page set" does the helper return? | [spec] [codebase] | 1 | Resolved (high, 2/2 agree) | Echo supplied inventory; selection stays with emission machinery; removal diff = second named surface, gap outcomes stay selected (FR-004, FR-012a, Key Entities) | spec-context-analyst, codebase-analyst |
| 7 | Clarify | FR-033 observation query shape + classifying surface | [spec] [codebase] | 1 | Resolved (high, 2/2 agree) | Entry-gate `--state all` five-field query; six-status classification reused verbatim (pure function already shipped); registration homing left to Plan; entry-gate sentences scoped (FR-033a, FR-033b) | spec-context-analyst, codebase-analyst |
| 8 | Checklist | CHK044: redaction stop vs regeneration ordering | [codebase] [spec] | 1 | Resolved (high, 2/2 agree) | Regenerate first; redaction stop rides the leg's own stop-or-proceed point (new FR-015d); not a fourth leg — FR-016 evaluation still runs | codebase-analyst, spec-context-analyst |
| 9 | Checklist | CHK002/016/036: FR-012b delete-superseded-file + FR-037 withholding | [codebase] [spec] | 1 | Upheld (high, 2/2) + refinement | Delete upheld (shipped verification precedent; keep-and-report has no precedent and strands pages); FR-018 gate re-keyed to ≥1 verified `generated` page, closing the verification-zeroed stranding route | codebase-analyst, spec-context-analyst |
| 10 | Checklist | CHK008: FR-034a unreachable statuses (security keyword) | [security] | 1 | Upheld (high, 3/3) + wording | Fail-closed posture confirmed (OWASP/CWE/RFC-grounded); headline corrected (skipped classifies, one live branch); defensive no_record reported as orchestrator invariant violation | codebase-analyst, spec-context-analyst, domain-researcher |
| 11 | Checklist | CHK014-017/030: FR-018a restoration mechanism | [codebase] [spec] | 1 | Resolved (high, N=1 — codebase analyst lost to transient API 403) | FR-018a stands unamended; mechanism stays with Plan; uniform snapshot-and-replay recorded as plan.md guidance (slice-1 FR-004d transport precedent, FR-003 untouched); SC-001 exception widened to both zero-generated sub-shapes | spec-context-analyst |
| 12 | Checklist | CHK019/020: FR-024a "one-line report" scope reading | [codebase] [spec] | 1 | Resolved (high, 2/2 agree) | Narrow reading upheld — the shipped sentence scopes to per-comment dispositions (paragraph topic-sentence structure; the shipped three-part report was never one line); FR-024a unmodified; FR-026's Clarify amendment is the in-document precedent | codebase-analyst, spec-context-analyst |

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

- **Files**: plan.md (834 lines), research.md, data-model.md, quickstart.md,
  contracts/check-artifact-freshness.md; spec.md §Reviewability Budget
  corrected to the hand-derived figure.
- **Budget (hand-derived, step 7b)**: ~690 production-only reviewable LOC
  (range 556–825) — **WARN** (over 400, under the 800 block); the split lever
  is named in plan.md §"The split lever" should the high end be realized.
  Two derivations (shipped-analogue anchoring; slice-1 realized density)
  corroborate. `estimate-reviewable-loc` returned projected=0 production=0
  status=pass — the known false zero on non-production-classified paths;
  recorded as an absent measurement, advisory only, hand figure governs.
- **Architecture**: one new registration `check-artifact-freshness` with three
  named surfaces (freshness verdict; removal diff per FR-012a; refresh-site
  corroboration classification per FR-033a reusing the shipped pure
  classifier). Dual-anchored Commit-cell read (row-end anchoring) for the
  Disposition pipe hazard. Three commit shapes kept disjoint (artifacts /
  bookkeeping / record).
- **Gate G3**: ✅ pass — `validate-gate` exit 0, 0 markers; privacy scan
  clean; executor hit its tool-use ceiling during the final verification
  sweep, so the orchestrator ran it: markers 0, no absolute paths, contract
  file present.

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

- **error-handling** (44 items): 15 gaps found, 15 closed (14 by the executor,
  CHK044 by consensus as FR-015d). Spec 46 → 51 FRs (new FR-012b, FR-015a,
  FR-015b, FR-015d, FR-034a; amended FR-018, FR-019a, FR-034a, FR-036,
  FR-037, FR-038, FR-039, SC-001). Consensus items 8–10; full suite green at
  the executor's verification (14012/14012).
- **state-management** (43 items): 9 gaps found, 9 closed (new FR-007b,
  FR-018a; ancestry/joinable definitions mirrored into data-model.md, plan.md,
  and the contract's fixture list; spec 51 → 53 FRs). Consensus item 11.
- **requirements** (43 items, written to requirements-domain.md — the
  spec-template checklist owns requirements.md): 10 gaps found, 10 closed
  (new FR-024a; FR-022 revised — the shipped sole-writer sentence survives
  verbatim with an added scoping sentence; slice-1 SC-008 inheritance
  recorded in Assumptions; spec 53 → 54 FRs). Consensus item 12 (narrow
  reading upheld 2/2). Clarifications header corrected to sessions 1-3.

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

- **tasks.md**: 81 tasks — Setup 3, Foundational 11, US1 35, US2 7, US3 15,
  Polish 10; 16 `[P]`; TDD throughout (17 fixture tasks + 9 red/green runs).
  Coverage 54/54 FRs forward, zero dangling reverse. Generated-artifact tail
  present as T075–T078. Non-goals guard table with per-task citations. Five
  named ordering hazards, including the mid-phase full-suite ban.
- **G5**: ✅ pass — `validate-gate` exit 0, 81 tasks, 0 markers.
- **Step 8, tasks-phase reviewability boundary**: runner `reviewability-gate`
  tasks mode is deferred on the installed runner — not invoked. Deferral
  diagnostics: helper_id=reviewability-gate, requested mode=tasks,
  reason=deferred for installed workflows (setup mode only). Fallback
  evidence chain: (1) scaffold setup-mode gate — warnings only, no blockers
  (roadmap-wide primary-surfaces warning is a known false positive);
  (2) plan-phase `estimate-reviewable-loc` — projected=0 status=pass, the
  recorded false zero, an absent measurement; (3) hand-derived budget ~690
  (556–825, ~730 midpoint after checklist deltas) = **WARN**, under the 800
  block; (4) no operator split decision — slice ratified as slice 2 of an
  operator-approved two-slice split. WARN is a marker-planning input but the
  route below keeps a single PR, so no `pr_marker_plan` is persisted; T014 is
  the binding pre-implementation checkpoint.

## Atomicity Route

- `atomicity-route` (read-only, advisory): **route=one-navigable-PR**,
  releasable=true, signals=[change-shape:modify-heavy], no hints, no
  warnings. Recorded 2026-08-24.

## Layer Plan

- `layer_plan.status=skipped` — route is one-navigable-PR, not split-PR; the
  planner runs only on split routes.


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

- **Findings**: 5 (0 CRITICAL, 1 HIGH, 1 MEDIUM, 3 LOW) — all remediated in
  the same pass; zero unresolved for consensus.
  - F1 HIGH: FR-018a snapshot location + lifecycle vs slice-1 byproduct
    removal — pinned to the `.process/feedback-sweep/` transport precedent,
    replay ordered before removal (plan.md + T042 + ordering hazard 7).
  - F2 MEDIUM: shipped prose is hard-wrapped, quoted-sentence greps return
    zero — fragment table added to tasks.md for the 8 affected tasks.
  - F3 LOW: design-concept 8000/8000 figure superseded by measured 7998/8000
    — revision note on FR-030.
  - F4 LOW: FR-015c never existed — numbering note added, no renumbering.
  - F5 LOW: SC traceability — SC-003/SC-008 cited on T055/T071, preamble
    points at quickstart §Traceability.
- **Coverage**: FRs 54/54 bidirectional; stories 3/3; both report paths;
  constitution 6/6 PASS; all 7 settled + 4 carried decisions honored, 2
  recorded supersessions confirmed legitimate; slice-1 inheritance items
  discharged.
- **G6**: ✅ pass — `validate-gate` exit 0, 0 CRITICAL/HIGH markers.
- **Synthesizer emit**: 📊 Confidence: 0.92


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
