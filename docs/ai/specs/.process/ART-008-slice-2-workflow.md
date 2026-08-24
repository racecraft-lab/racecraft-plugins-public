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
| Confidence Gate | G6.5 | ✅ Complete | Composite 0.92 ≥ 0.90, advisory mode — PASS, proceed; plan stage ends here |
| Implement | `/speckit-implement` | 🔄 In Progress | 81 tasks (T001–T081); TDD; started 2026-08-24 |
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

### Pre-flight Record (Step 0, implement stage, 2026-08-24)

- Stage resolution: `implement` (argv) — explicit --stage implement. Draft PR
  corroboration: **match** — #502 recorded, #502 observed (OPEN, draft).
- `check-prerequisites`: all_pass=true; branch `art-008-feedback-sweep-slice-2`
  (worktree, feature=true); SpecKit CLI 0.11.8. PROJECT_COMMANDS and
  PRESET_CONVENTIONS unchanged from the plan-stage record.
- CONFIDENCE_GATE_MODE=advisory (resolver, no flag). G6.5 already recorded
  PASS at 0.92; it is not re-run.
- **G0 baseline preserved, not recomputed** (Step 0.6e): the recorded 14012
  stands. Any newly observed count is a non-blocking drift diagnostic.
- **Installed plugin version: 2.27.0.** As the Installed-plugin note above
  anticipated, 2.27.0 carries ART-007's draft-PR emission but **not** slice
  1's feedback sweep, which merged after 2.27.0 was cut. This implement stage
  therefore opens the pre-ART-008 way: **no automated feedback sweep of #502
  ran.** Substituted a read-only observation in its place —
  `gh pr view 502 --json reviews,comments` returned **0 reviews, 0 comments**,
  so there was no feedback to sweep and nothing to amend. Report-only; no
  sweep machinery was invoked and no artifact was amended on its account.
- Synced `origin/main` before implementing (3 commits: #499, #500, #501). One
  conflict, in `html-artifacts-technical-roadmap.md` §Progress Tracking, whose
  two sides each carried facts the other lacked; resolved by combining them and
  advancing the Next cell to the implement stage. `refresh-release-artifacts.py`
  reported the generated tree already consistent after the merge.
- State slot: already this workflow; no reclaim.
- **T001 baseline (post-merge): 14025/14025, exit 0** (L1 1511, L4 12295,
  L5 219). Non-blocking **drift diagnostic**: +13 against the recorded G0
  baseline of 14012, all in Layer 4, from the cases PR #501 brought in on the
  `origin/main` merge. The recorded baseline is **preserved**, not replaced —
  G7 verifies the count increased against 14012.
- T002 `pnpm --dir docs-site install --frozen-lockfile`: exit 0.
- T003 generated-artifact merge driver configured for this clone.

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
| **Stage** | implement |
| **Draft PR** | [#502](https://github.com/racecraft-lab/racecraft-plugins-public/pull/502) — draft; 4/4 pages generated (implementation-plan, spec-explainer, code-approaches, module-map), no gaps |

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
- **Synthesizer emit** (standalone line below for the gate reader):

📊 Confidence: 0.92


| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| | | | |

---

## Phase 6.5: Confidence Gate

| Field | Value |
|-------|-------|
| Mode | advisory (resolver default; no flag) |
| Composite confidence | 0.92 |
| Verdict | PASS — at or above the 0.90 threshold; recommended_action=proceed |
| Evidence | `confidence-gate` helper exit 0 against this file's synthesizer emit; per-criteria breakdown not emitted (composite-only form) |

The resolved stage for this run is `plan` (argv), so the run ends at this
gate. Implement and Post-Implementation were not started; resume with
`--stage implement` (or `full`) in a fresh invocation.

---

## Phase 7: Implement

### T014 — Reviewability checkpoint, recorded before task work

The binding figure is `plan.md` §"Reviewability Budget, derived by hand":

| Dimension | Declared | Threshold | Verdict |
|---|---|---|---|
| Production reviewable LOC | **~690** (range 556–825, ~730 midpoint after the checklist deltas) | 400 warn / 800 block | **WARN** |
| Production files | 5 | 6 warn | within |
| Authored files | 12 | 15 warn | within |
| Primary surfaces | 1 | — | within |

**One warn, no block.** The plan-phase `estimate-reviewable-loc` result
(`{"status":"pass","projected":0}`) is an **absent measurement**, not evidence
of fitness, and is not cited as one anywhere in this run. The estimator
classifies none of this slice's paths as production and false-zeroed the same
way on slice 1, which shipped 515–830 measured against a whole-spec estimate of
452.

The route recorded at G5 is `one-navigable-PR`, so the WARN is a marker-planning
input that keeps a single pull request; no `pr_marker_plan` is persisted. The
split lever, if the realized diff approaches the 800 block, is named in
`plan.md`: the US3 report prose (T057–T071) separates cleanly from the helper
and its US1/US2 trigger sites.

Recorded 2026-08-24, before the first implementation task ran.

### Implementation log

**Phase 1, Setup (T001–T003)** — complete. Baseline 14025/14025 exit 0; the
recorded G0 baseline of 14012 preserved with the +13 drift recorded above.

**Phase 2, Foundational (T004–T013)** — complete. Registered
`check-artifact-freshness` as one read-only, `python_authoritative`,
`python_only` helper and stood up its Layer 4 harness.

- New: the request fixture, `test-artifact-freshness.py` (264 lines, harness
  only), and the empty-but-valid `freshness-cases.json` /
  `expected-envelopes.json` pair.
- Modified: `EXPECTED_HELPERS` + `NO_BASH_ANCESTOR` + `HELPER_CASES`, the
  fixture manifest at the **same index**, the suite manifest Layer 4 entry, the
  registry entry beside `sweep-pr-feedback`, and `read_only.py`'s four touch
  points with a surface-routing stub.
- **T010 red, measured**: 82/84 — `test_registry_dispatch_lists_only_read_only_helpers`
  (id absent from the dispatch listing) and
  `test_helper_python_authoritative_records` (KeyError `shell`, no helper
  record for an unregistered id).
- **T013 green**: 84/84, `test_fixture_manifests_cover_registered_helpers`
  included. **No expected remaining failure.** `tasks.md` predicted
  `test_helper_python_authoritative_records` would stay red until T028; it
  passes, because that test asserts response plumbing (`shell`, argv tail,
  `python_operation`, capture limits, exit-code/status parity) and never
  verdict content, all of which a well-formed exit-0 stub satisfies. Recorded
  as measured rather than as predicted.
- Surface routing verified against the **source tree**
  (`PYTHONPATH=speckit-pro`): absent and explicit-null both reach `verdict`;
  `removal_diff` and `corroborate_refresh` reach their own; `""` and a fourth
  value are input errors at exit 2. The default is decided with `is None`, so
  the empty string stays an error rather than a silent default.
- One deliberate deviation: the T005 harness omits the parse test's
  non-empty-corpus assertion, which would be red before T015 while saying
  nothing about the helper. Both comparison paths (ok-envelope and exit-2
  `error:` line) are already in place, since T015–T024 are fixture-only.
- Privacy scan clean across every created and modified path.

**Phase 3, User Story 1 — verdict surface (T015–T029)** — complete.
`FRESHNESS_TEST` **88/88**, `HELPER_TEST` **84/84**, both re-run by the
orchestrator rather than taken on report.

- 29 fixture cases cover every bullet of the contract's Layer 4 verdict list:
  the four verdicts on their own conditions, both precedence pairs, FR-007a/b
  including the pinned `false` ancestry encoding, FR-008's abbreviated-cell
  equality, FR-009 both directions, one case per closed FR-006 reason, the
  three unusable-observation shapes, both structural cases, six input errors,
  and the dual-anchoring regression.
- **T025 red, measured**: 59/88 — all 29 result assertions failed (23 on
  envelope mismatch against the stub's two keys, 6 on `input_error` status).
  The 59 green were the three meta-tests over fixture form, which check shape
  rather than the helper.

#### Four contract refinements the fixtures settled

The planning artifacts left four points underdetermined. Each was settled
against shipped precedent, pinned into the fixtures, and implemented to; none
is drift.

1. **A uniform nine-key envelope with a top-level `reason`.** The contract
   returns `undeterminable` "with reason `unusable_observation`", but that token
   is not in the closed per-row reason set and is not a row, so `data-model.md`
   §3 had no home for it. Every key is present on every case, null where a case
   has nothing to say, following `corroboration_record`'s shipped rule.
2. **An unusable observation echoes nothing** — `pages: []`,
   `last_artifacts_commit: null`, `amended_rows_read: 0`. §2 says `ok` must be
   the literal `true` "to be read at all", which collides with §3's echo rule;
   resolved toward §2, since reading nothing cannot produce an echo.
3. **`missing_commit_cell` means the header carries no `Commit` column**, which
   is the condition §1's validation table left unassigned while §1 and §2
   between them accounted for the other four reasons. Consequence, honored in
   the implementation: **the header row is located by `Class`, never by
   `Commit`.**
4. **Five diagnostic strings**, phrased to mirror the shipped `sweep_error`
   house strings rather than invented.

#### Two ordering hazards, measured rather than discovered by failing

- A short row against the eight-cell header has `cells[-2] == "amended"`, the
  Class token itself. The malformed-short-row guard therefore runs **before**
  the `-2` read, or the join takes the Class cell.
- The escaped-pipe row splits into **nine** cells. A left-anchored `Commit`
  read takes the disposition prose, matches no record, and returns
  `undeterminable` where the truth is `stale` — the silent wrong-direction
  failure that leaves stale pages unregenerated. This is the regression the
  dual-anchoring rule exists for.

**Phase 3, User Story 1 — removal-diff and corroboration surfaces (T030–T038)**
— complete. `FRESHNESS_TEST` **154/154** over 51 cases, `HELPER_TEST`
**84/84**, both re-run by the orchestrator.

- **Removal diff** is a pure set difference over the supplied stems, ordered by
  `observed_pages` so the output is stable and diffable. It reads no file and
  deletes nothing. The FR-012b disjointness case pins the point the surface
  exists for: a page whose regeneration returned a `gap` is still selected, so
  it must **not** appear in the removal set.
- **Corroboration** calls the two shipped pure functions verbatim —
  `workflow_draft_pr_row` and `corroborate_draft_pr` — behind the same
  HTML-comment blanking the shipped call site uses, with **zero added
  branches**. The orchestrator inspected the function body to confirm this
  rather than accepting the claim: literal reuse is the requirement, because
  FR-034's guarantee that each status keeps its ART-007 behavior holds only
  while the same code decides the status in both places.
- **T032 red**: 110/121, exactly the 11 new removal cases. **T036 red**:
  139/148, exactly the 9 new corroboration cases. No existing verdict case
  moved at any point in either cycle.
- **T038 LAYER4**: `test-artifact-freshness` passes; the suite carries **7
  known stale-payload failures** — one runner sha256 manifest case and six
  installed-release payload/readiness cases, one of them named
  `current_dist_passes_after_runner_rebuild`. Every one is the predicted
  consequence of editing `speckit-pro/` source before the generated tail runs,
  none touches a freshness surface, and all seven must clear at T075.
- **Coverage gap closed by the orchestrator**: the contract's Surface 3
  failure-mode table makes a missing or unreadable `workflow_file` an input
  error, but its Layer 4 list did not enumerate a case for it, so the shared
  prologue's reach across surfaces was asserted nowhere. Two cases were added
  and passed immediately, which is the evidence that the prologue governs every
  surface rather than the default one alone.
- Underdetermined points settled: one diagnostic per key rather than per
  condition (three conditions still exercised separately per key); `observed`
  is validated before `reselected`; the echo keys follow `data-model.md` §4's
  `observed` / `reselected` spelling; removal cases carry no `workflow_file`,
  because routing reaches the surface before any path read and the surface
  reads nothing; and both `skipped` cases carry a well-formed `Draft PR` row,
  since the shipped classifier short-circuits to `no_record` on an absent row
  before any observation is read.

**Phase 3, User Story 1 — Claude reference prose (T039–T045)** — complete.
`LAYER1` **1511/1511**, re-run by the orchestrator on the final bytes.

- **229 insertions, 0 deletions.** Verified by `git diff --numstat`, not taken
  on report: the slice's non-goals guard permits deletion only of the two
  FR-027 promise passages, and those belong to T048. Both are still present.
- Seven new sections landed as one block immediately before
  `Phase 7 Setup: Stop or Proceed`, so document order equals runtime order:
  reply point → regeneration sequence → stop-or-proceed → byproduct removal.
- Covered: the nine-step regeneration sequence with step 0 as a placement
  rather than a step; step 3b's superseded-file deletion reported inside the
  page's own `gap` outcome; the three commit shapes in a table with the rule
  that none absorbs another; FR-018a's two-directional exclusivity with
  snapshot-and-replay under `.process/feedback-sweep/`, replay ordered before
  removal, restoration reported as a run-level line rather than a fourth page
  outcome; FR-019a's push inside step 6; the refresh's own live observation
  with the pinned five-field query; and FR-034a's two statuses that cannot
  classify here, neither reachable as a fallthrough to creation.
- A visible tension between T043's push rule and two shipped enumerations is
  **left standing deliberately** — T052 is the task that scopes them, and
  scoping early would have meant editing shipped text out of turn.

#### One artifact disagreement, reconciled rather than papered over

`plan.md`'s nine-step block gated the regeneration commit at step 5 on "step 3,
3b, or the regeneration changed something under it". `tasks.md` T041 gates it
on **at least one verified `generated` page**. These part company on a
zero-generated run carrying only deselection removals.

The task list is right and the plan was stale: Checklist consensus item 9
re-keyed the FR-018 gate to the verified-`generated` form precisely to close a
permanent-stranding route, and FR-018a's replay fires when that count is zero
and calls the gate its own. The any-change reading would take a removal-only
commit, moving the FR-001 join past pages that were never generated. The
shipped prose carries the re-keyed wording, and **`plan.md` step 5 was
corrected to match, with a revision note recording why**, so the two artifacts
no longer contradict each other.

#### The generated tree was refreshed early

Layer 1's preflight auto-synced `dist/`, so the orchestrator ran
`refresh-release-artifacts.py` to completion rather than leave a half-synced
tree. Every generated path is a mirror of authored bytes — the `dist/` prose
deltas match the authored 229 lines exactly, and the runner deltas are the
already-committed helper catching up. T075 re-runs this after the last source
edit; running it early neither substitutes for that nor invalidates it.

**Phase 3, User Story 1 — Codex mirror and the promise removal (T046–T049)** —
complete. `LAYER1` **1511/1511**.

- **T046**: 208 inserted lines on `phase-execution-codex.md`, describing the
  same behavior in that surface's own vocabulary rather than by copying
  Claude's sentences.
- **T048/T049**: both slice-1 promise passages are gone from **both**
  surfaces. All four greppable fragments now return **zero matches**, verified
  by the orchestrator. On the Claude surface the removal is `+1/-6`: the
  stop-report clause was cut and its sentence reflowed to end at "commit
  range", and the meta-paragraph was removed whole. No orphaned connective, no
  empty heading, no double blank line.
- These are the **only two deletions this slice permits**, and slice 1 itself
  declared them an interface slice 2 replaces. US1 acceptance scenario 4 is
  discharged.
- Two invariants re-checked rather than assumed: the shipped sentence "The
  sweep never writes the `Draft PR` row" survives on both surfaces, and
  `codex-skills/speckit-autopilot/SKILL.md` is **byte-unchanged**, so its two
  words of headroom under the 8000-word cap are intact.

**Phase 4, User Story 2 — the clean sweep repairs stale pages (T050–T056)** —
complete. `LAYER1` **1511/1511**. **116 insertions on the Claude surface, 93 on
the Codex mirror, 0 deletions on either**, verified by `git diff --numstat`.

- **T052 scopes rather than rewrites, which was the whole point.** Both shipped
  enumerations survive verbatim — the reply-point dichotomy and the six
  run-ending conditions — and each gained a sentence saying only *which* push
  its "failed push" member means. Each closes by disclaiming any effect on
  membership: "the members themselves stand as written." This is what resolves
  the tension US1's T043 deliberately left standing.
- **T050** pins that the verdict is evaluated on every leg the run reaches,
  then scopes that claim honestly: the evaluation sits inside the sweep, so the
  entry gate governs it. On the four statuses that stop the sweep, no
  evaluation occurs and stale pages stay stale — recorded as a **deferral, not
  a lost repair**, because the join is durable and reads the same `amended`
  rows on the first `match` run after the operator clears the gate.
- **T051** carries slice-1 Q8: on `stale`, the leg that amended nothing
  regenerates, refreshes, and proceeds. Repairing stale pages never converts a
  proceed into a stop.
- **T054** records why a whole-set gap **withholds the deselection removal**
  even though it is computable: withholding is what keeps the commit untaken,
  and the untaken commit is the only thing keeping the join reading `stale` so
  the next leg retries. A removal landing alone would mark the whole set
  current and strand every gapped page permanently, to delete one file.
- **T055** states the repairability line exactly: what decides whether a later
  leg retries is **whether the artifacts commit was taken, never the shape of
  the shortfall**. A whole-set gap takes no commit and is retried; a per-page
  gap rides a commit that marks the set current and is retried by nothing, so
  it is the operator's to act on from the report.
- **T053** places the redaction stop after the sequence's terminal outcome on
  the amended-nothing leg, and argues it from the shipped trigger's own
  wording: the stop replaces the proceed *at the same point*, so when the
  proceed moved later the stop moved with it. It adds no stop condition and
  changes no decision.

**Phase 5, User Story 3 — the report (T057–T069)** — complete on the Claude
surface. `LAYER1` **1511/1511**. **110 insertions on the reference, 4 on
`SKILL.md`, 0 deletions on either.**

- The what-already-landed enumeration is extended **once, in the shared
  report-shape section**, so page outcomes are stated in one place rather than
  per leg. `removed` is in the outcome enum, and every removal is named as its
  own outcome and never silent.
- Run-level lines carry the regeneration commit's short sha and the refresh
  outcome, with the manual resume path below a failure. The freshness
  contribution **collapses to a single line** on a sweep that amended nothing
  and found the pages already current.
- Two gap shapes are tabled apart because they differ in **repairability**, not
  severity. Resume paths are **per stopping status**, not one shared line.
- `undeterminable` triggers no regeneration, no refresh, no commit, and moves
  stop-or-proceed in neither direction. A record-commit failure is reported
  through the refresh outcome and never blocks the run.

#### The four scoping edits leave every shipped sentence verbatim

Each shipped sentence still matches exactly once and gained a paragraph beside
it. The orchestrator read all four rather than accepting the claim.

- **FR-022** — "The sweep never writes the `Draft PR` row on any path" stands
  untouched. Beside it: that invariant is about the sweep's **own** writes; the
  refresh changes the cell through the emission machinery, which keeps exactly
  one writer, and this slice supplies only the trigger and the timing. Its
  ground is restated unchanged — a run must not repair a record it just failed
  to corroborate.
- **FR-024a** — the one-line-report characterization is scoped to the
  per-comment dispositions its own paragraph is about, leaving the freshness
  lines free to contribute to the same leg's report.
- **FR-033b** — the sweep's reuse of Step 0.6c's report is scoped to the entry
  gate's sweep-or-not decision, which is the decision that observation was
  taken for, and does not forbid the refresh's own later live read.
- **FR-033b in `SKILL.md`** — "one read-only observation per run" is scoped to
  Step 0.6c's own step rather than read as a cap on every corroboration read a
  run may take.

**Phase 5, User Story 3 — the Codex mirror (T070–T071)** — complete.
**107 insertions, 0 deletions.** `LAYER1` **1511/1511**, with
`validate-codex-skills` 163/163 and `validate-codex-parity` 87/87. The Codex
`SKILL.md` is byte-unchanged: T069 has no Codex counterpart, because that file
already carries the scoping FR-033b asks for inside its own Step 0.6c bullet,
and its body has two words of headroom.

All three shipped sentences the scoping edits sit beside still match exactly
once on this surface too.

#### T071 semantic parity, checked by the orchestrator

The structural validators confirm file-level parity only, so SC-008's claim
needed a separate check. Every load-bearing concept in this slice was counted
on both surfaces and the occurrence counts agree: the three helper surface
names, all four verdict tokens, the snapshot and replay mechanism, the removal
outcome, the repairability rule, the whole-set gap, the record commit, the
pinned `--state all` query, and the `artifact-author` dispatch. One phrasing
difference is benign — "three sinks" reads 7 times on Claude and 6 on Codex,
which is wording density rather than a missing behavior.


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
