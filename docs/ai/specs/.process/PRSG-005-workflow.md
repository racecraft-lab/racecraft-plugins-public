# SpecKit Workflow: PRSG-005 — Vertical-slice sizing heuristics in PRD/grill-me

**Template Version**: 1.0.0
**Created**: 2026-06-06
**Purpose**: Autopilot-executable workflow for PRSG-005. The phase prompts below encode the locked decisions from the Grill Me interview (Q1–Q10).

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/PRSG-005-design-concept.md
```

The design concept is the **source of truth** for every scoping decision below.
Re-read it before each phase to disambiguate a prompt. Q-numbers (Q1–Q10) below refer
to that doc's Design Tree.

> **Note:** Grill Me is human-in-the-loop only and is **not** part of the autopilot
> loop. Once autopilot begins, clarifications happen via `/speckit-clarify` and the
> consensus protocol — never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | spec.md: 16 FRs, US1+US2, 6 SCs, advisory-only (FR-011/SC-004). G1 pass (0 markers). 1 deferred [NEEDS CLARIFICATION] = OQ#1 spike handling → Clarify S1. |
| Clarify | `/speckit-clarify` | ✅ Complete | S1: spike = exempt slice type via input flag → FR-017; at-ceiling boundary pinned (ok at ceiling). S2: shared homes LOCKED (coach/scripts + coach/references); boundary + advisory-only confirmed. 0 markers. No consensus needed. |
| Plan | `/speckit-plan` | ✅ Complete | plan.md + data-model + contracts/estimate-spec-size.md + quickstart. Constitution 6/6 PASS. Budget ~200 LOC, 1 surface. G3 pass. 6 surfaces + Codex parity captured. |
| Checklist | `/speckit-checklist` | ✅ Complete | data-integrity (28 items, 1 gap→bad-input status pinned ok) + error-handling (20 items, 2 gaps→caller-side unavailable/exit-code invariant + prd US1 AS5). 0 gaps. No consensus. |
| Tasks | `/speckit-tasks` | ✅ Complete | tasks.md: 23 tasks, FR 17/17, TDD T004 (L4 fixture RED)→T005 (estimator GREEN), 8 [P], Codex mirrors paired (T009/T013/T015). G5 pass. Reviewability tasks-mode = transition_exception/pass (projection over-counts SDD artifacts; authoritative = pre-PR diff gate). T021–T023 (L2/L3/L8) are developer-local follow-ups, not autopilot-run. |
| Analyze | `/speckit-analyze` | ✅ Complete | 3 findings (0 CRIT, 0 HIGH, 1 MED, 2 LOW): F1 requirements.md stale note + F2 data-model.md new_vs_modify→optional fixed; F3 deferred (non-defect). SC→task + Codex parity complete; no drift from 10 decisions; advisory-only holds. G6 pass. 📊 Confidence: 0.96 |
| Implement | `/speckit-implement` | ✅ Complete | 4 groups (Foundation TDD RED→GREEN, US1 prd, US2 grill-me, Polish triggers). Full suite **1694/1694** green (validate-scripts 60, validate-skills 98, validate-codex-skills 140, validate-codex-parity 76, L4 estimator 39). G7 substantive PASS; 19/23 task checkboxes ticked — T019 (PR packet) + T021–T023 (developer-local L2/L3/L8) complete/record in post-impl. |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | Both user stories clear; no `[NEEDS CLARIFICATION]` remain; advisory-only scope explicit. |
| G2 | After Clarify | The 10 locked decisions reflected; no drift from the design concept; Open Questions resolved or deferred. |
| G3 | After Plan | Script home, shared-doc home, two skill surfaces + Codex mirrors identified; Codex parity planned. |
| G4 | After Checklist | All `[Gap]` markers addressed. |
| G5 | After Tasks | Every FR maps to a task; L4 estimator fixture + L2/L3 eval surfaces enumerated; Codex edits paired. |
| G6 | After Analyze | No `CRITICAL`; no contradiction with the design concept's Goals/Non-goals/decisions. |
| G7 | After Implementation | `bash tests/run-all.sh` green; estimator deterministic on fixtures; L2/L3 recorded; Codex parity green. |

---

## Prerequisites

### Constitution Validation

This repo is a Claude Code plugin marketplace (bash + jq + markdown; no compiled runtime).
Constitution: `.specify/memory/constitution.md`.

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| KISS / YAGNI | Advisory-only sizing; no gate logic; reuse existing Budget line; no new schema (Q3, Q4, Q9) | Diff review; reviewability gate |
| Scripts-first | Deterministic sizing math lives in `estimate-spec-size.sh` (bash+jq), not LLM reasoning (Q2, Q8) | `tests/run-all.sh --layer 4` |
| Codex parity | Every CC skill change mirrored in `codex-skills/`; shared doc+script runtime-agnostic | `validate-codex-skills.sh`, Layer-8 parity |
| Test-first | L4 estimator fixture RED before GREEN; L2/L3 evals recorded before merge | `bash tests/run-all.sh` + developer-local `claude -p` evals |

**Constitution Check:** mark ✅ before G1.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | PRSG-005 |
| **Name** | Vertical-slice sizing heuristics in PRD/grill-me |
| **Branch** | `prsg-005-slice-sizing-heuristics` |
| **Dependencies** | None (parallelizable with Phase 2) |
| **Enables** | Keeps N small for PRSG-007/008/009 (split-PR engine); complements PRSG-006 (plan-phase budget) |
| **Priority** | P1 (Phase 3 — Upstream sizing) |

### Success Criteria Summary

- [ ] `speckit-prd` emits a SPEC catalog of **thin vertical slices by construction**, each
      with a populated `Budget: ~N LOC` line from `estimate-spec-size.sh` and a one-line
      INVEST/vertical-slice rationale (Q1, Q4).
- [ ] `grill-me` gains a **slice-sizing design-tree branch**: it runs the estimator on the
      single spec and, when over budget or horizontally sliced, asks a split question via
      `AskUserQuestion` recommending N vertical slices; the result lands in the design
      concept (Q1, Q5).
- [ ] `estimate-spec-size.sh` is a single shared, runtime-agnostic bash+jq script invoked
      via `${CLAUDE_PLUGIN_ROOT}`; takes structured size signals and returns
      `{estimated_loc, suggested_slices, status: ok|warn}` against the shared ~400-LOC
      ceiling; byte-identical on fixtures (Q2, Q8).
- [ ] Canonical SPIDR + INVEST + vertical-slicing guidance lives in **one shared reference
      doc**; both skills carry a short inline summary + a link (Q6).
- [ ] PRSG-005 is **advisory-only** — it never blocks. No plan-phase gate, threshold, or
      exit-code logic (that is PRSG-006); the ~400-LOC ceiling is a shared documented
      constant only (Q3).
- [ ] No roadmap-template schema change — reuse the existing per-SPEC `Budget` line (Q9).
- [ ] Light trigger touch on both skills (new sizing/slicing phrases) with **no over/under-
      trigger regression** on existing phrases (Q7).
- [ ] Codex parity: both skill mirrors + shared doc reference updated; `bash tests/run-all.sh`
      (L1+L4+L5) green; L2/L3/L8 recorded before merge (Q10).

---

## Phase 1: Specify

**When to run:** Start of the feature. Focus on WHAT and WHY. Output: `specs/prsg-005-slice-sizing-heuristics/spec.md`

### Specify Prompt

```bash
/speckit-specify

## Feature: Vertical-slice sizing heuristics in PRD/grill-me (PRSG-005)

### Problem Statement
~68% of a feature diff is code+tests; PRs stay big until specs themselves are born
PR-sized. The cheapest moment to right-size is during the PRD/scoping interview, before
any code exists. PRSG-005 bakes SPIDR (Spike, Path, Interface, Data, Rules — story
splitting) + INVEST (Independent, Negotiable, Valuable, Estimable, Small, Testable —
story quality) + vertical-slicing (each slice cuts end-to-end through all layers) into
the two scoping skills so the SPEC catalog is composed of thin, end-to-end slices by
construction.

### Users
Plugin maintainers and any consuming project that runs `speckit-prd` to author a roadmap
or `grill-me`/`speckit-scaffold-spec` to scope a single spec; downstream reviewers who
benefit from smaller PRs.

### User Stories
- US1 — Catalog-level decomposition (speckit-prd). `speckit-prd` owns decomposing an idea
  into the SPEC catalog using SPIDR story-splitting + vertical slicing, so the emitted
  catalog is thin vertical slices by construction. Each catalog entry's existing
  `Budget: ~N LOC` line is populated from `estimate-spec-size.sh`, plus a one-line
  INVEST/vertical-slice rationale. (Decision: Q1 "prd decomposes, grill-me validates";
  Q4 "Light per-SPEC annotation + guidance".)
- US2 — Per-spec validation + split (grill-me). `grill-me` owns validating the single spec
  it is scoping: it gains a dedicated slice-sizing design-tree branch that runs
  `estimate-spec-size.sh` on the spec's signals and, when the result is over budget or the
  spec is horizontally sliced, asks a split question via AskUserQuestion recommending N
  thin vertical slices. The chosen split is recorded in the design concept (Goals / Open
  Questions) for scaffold-spec/autopilot to act on. (Decision: Q1, Q5 "Active split branch".)

### Deterministic helper (scripts-first)
`estimate-spec-size.sh` — a single shared, runtime-agnostic bash+jq script invoked by both
skills (and both Codex mirrors) via `${CLAUDE_PLUGIN_ROOT}`. Input: structured size signals
(e.g. # user stories, # files/surfaces touched, # FRs, new-vs-modify flag) as args/JSON.
Output: JSON `{estimated_loc, suggested_slices, status: ok|warn}` against the shared
~400-LOC ceiling. The LLM gathers inputs and interprets; the script does the deterministic
math + threshold. (Decision: Q2, Q8.)

### Shared guidance
Canonical SPIDR + INVEST + vertical-slicing guidance lives in ONE shared reference doc;
`speckit-prd` and `grill-me` each carry a short inline summary + a link (DRY, single source
of truth). (Decision: Q6.)

### Constraints
- ADVISORY-ONLY: PRSG-005 never blocks. No gate, threshold, or exit-code logic — that is
  PRSG-006. The ~400-LOC ceiling is a shared documented constant only. (Q3.)
- No roadmap-template schema change — reuse the existing `Budget: ~N LOC` catalog line. (Q9.)
- Light trigger touch only — add a few sizing/slicing phrases; keep all existing triggers
  intact; no over/under-trigger regression. (Q7.)
- Codex parity is mandatory: mirror both skill edits in `codex-skills/`; the shared doc +
  script are runtime-agnostic single copies.
- Budget ~200 production LOC; bash + jq only.

### Out of Scope
- Plan-phase reviewability budget, gate threshold rework, typed exceptions (PRSG-006).
- Atomicity routing (PRSG-007), layer-planner (PRSG-008), multi-PR emission (PRSG-009).
- Formal structured catalog fields (size_estimate/invest_check/slice_of) (Q4 rejected).
- A machine-readable size budget artifact written for a downstream gate to consume (Q3 rejected).
- Roadmap-template schema changes (Q9 rejected).
```

---

## Phase 2: Clarify

Decisions are already locked in the design concept (Q1–Q10). Clarify should **verify
consistency, not reopen** them. Flag any spec wording that contradicts a locked decision.
The two sessions below are seeded from the design concept's Open Questions.

#### Session 1: Estimator semantics

```bash
/speckit-clarify Focus on estimate-spec-size.sh semantics:
confirm it takes structured size signals (# user stories, # surfaces, # FRs, new-vs-modify)
as args/JSON and returns {estimated_loc, suggested_slices, status: ok|warn} against a shared
~400-LOC ceiling constant; resolve SPIDR "Spike" handling — a research-only slice has
near-zero production LOC, so decide whether a spike is flagged as a distinct slice TYPE
exempt from the LOC threshold rather than sized by LOC; confirm the "forward estimate is
approximate, NOT the authoritative count" caveat is documented (the authoritative count is
PRSG-006's estimate-reviewable-loc.sh); confirm how the skill collects the estimator inputs
during the interview.
```

#### Session 2: Responsibility boundary + final paths + advisory-only

```bash
/speckit-clarify Focus on the responsibility split and homes:
confirm speckit-prd owns catalog-level decomposition and grill-me owns per-spec validation
with NO duplicated guidance prose (Q1); confirm the exact home of the shared slicing
reference doc and the shared estimate-spec-size.sh script (direction locked: one shared doc
+ one shared script invoked via ${CLAUDE_PLUGIN_ROOT}; finalize the precise dir against the
plugin layout — mirror where PRSG-002 placed its shared normalizer); confirm PRSG-005 emits
NO gate/exit-code logic and never blocks (advisory-only; PRSG-006 owns the gate), sharing
only the ~400-LOC ceiling constant.
```

---

## Phase 3: Plan

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Runtime: bash + jq (deterministic shell); Markdown skill prose. No compiled build.
- Skill surfaces (CC): speckit-pro/skills/speckit-prd/SKILL.md and
  speckit-pro/skills/grill-me/SKILL.md — short inline SPIDR/INVEST/vertical-slice summary
  + link to the shared doc; prd populates the Budget line from the estimator; grill-me adds
  the slice-sizing branch + split sub-interview.
- Codex mirrors: codex-skills/speckit-prd/SKILL.md and codex-skills/grill-me/SKILL.md must
  carry the same guidance (the Codex variants use a free-text Q&A loop instead of
  AskUserQuestion — adapt the split-question mechanism accordingly).
- Shared reference doc: ONE canonical slicing-heuristics doc — LOCKED (Clarify S2) to
  speckit-pro/skills/speckit-coach/references/slicing-heuristics.md.
- Shared script: estimate-spec-size.sh — single runtime-agnostic bash+jq script — LOCKED
  (Clarify S2) to speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh, invoked by
  both skills + both Codex mirrors via ${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/scripts/;
  one committed L4 fixture set (same inputs → byte-identical JSON output).
- Tests: L1 (structural + codex skills), L4 (estimator determinism fixtures), L5 (no agent
  scoping change expected). Developer-local: L2 (trigger), L3 (functional), L8 (parity).

## Architecture Notes
- estimate-spec-size.sh: pure function of its inputs; ~400-LOC ceiling as a single hardcoded
  constant with a "keep in sync with the documented ceiling" comment; emits compact JSON via
  jq; deterministic (no clocks/randomness). status=warn when estimated_loc exceeds the
  ceiling; suggested_slices = ceil(estimated_loc / ceiling) (or similar documented formula).
- Division of labor (Q1): prd = catalog decomposition; grill-me = per-spec validation/split;
  both call the same script; guidance prose lives once in the shared doc, summarized inline.
- Advisory-only (Q3): no exit-code gate; status=warn is informational. Nothing here blocks a
  run. The ~400-LOC ceiling constant is shared with PRSG-006 by documentation, not by a
  consumed artifact.
- No template/schema change (Q4, Q9): reuse the existing per-SPEC Budget line.
- Codex parity: skill prose mirrored CC↔Codex; shared doc + script are single copies.
- Reviewability budget ~200 LOC, single primary surface (skills + docs/process).
```

---

## Phase 4: Domain Checklists

### Recommended Domains

| Domain | Why |
|---|---|
| **data-integrity** | The estimator's input→`{estimated_loc, suggested_slices, status}` mapping and the shared ~400-LOC ceiling constant are correctness-critical: a wrong formula or an inconsistent ceiling produces misleading size signals. Validate the math, the threshold boundary, and JSON shape. |
| **error-handling** | The estimator must behave sanely on malformed/missing/zero inputs (incl. the SPIDR spike near-zero case), and grill-me's split branch must degrade gracefully when the estimate is borderline/unavailable — and NEVER block (advisory-only invariant). |

#### 1. data-integrity Checklist

```bash
/speckit-checklist data-integrity

Focus on PRSG-005 requirements:
- estimate-spec-size.sh: deterministic input→output mapping; same inputs → byte-identical
  JSON; the ~400-LOC ceiling is a single source-of-truth constant; suggested_slices formula
  is correct at and around the threshold boundary.
- The Budget line in the emitted catalog reflects the estimator output (no drift between the
  number prd writes and what the script returns).
- Pay special attention to: the status=ok/warn boundary at exactly the ceiling, and integer
  rounding in suggested_slices.
```

#### 2. error-handling Checklist

```bash
/speckit-checklist error-handling

Focus on PRSG-005 requirements:
- Estimator on malformed/missing/zero/negative inputs and on the SPIDR spike near-zero-LOC
  case → correct, non-crashing behavior and a sensible status.
- grill-me split branch when the estimate is borderline or the estimator is unavailable →
  degrades to advisory note, never blocks the interview (advisory-only invariant, Q3/Q5).
- Pay special attention to: never converting a warn into a hard stop anywhere in PRSG-005.
```

---

## Phase 5: Tasks

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Small, testable chunks; each references a success criterion.
- TDD: write the Layer-4 estimator determinism fixture (RED) before the script logic (GREEN).
- Mark parallel-safe tasks [P]; keep each Codex-mirror edit paired with its CC edit.

## Implementation Phases
1. Foundation — shared slicing-heuristics reference doc (SPIDR + INVEST + vertical-slicing,
   canonical text) + estimate-spec-size.sh (with its L4 fixtures).
2. US1 — speckit-prd: inline summary + link; populate Budget line from the estimator; emit
   thin vertical slices by construction (CC) + Codex mirror.
3. US2 — grill-me: slice-sizing design-tree branch + split sub-interview using the estimator
   (CC, AskUserQuestion) + Codex mirror (free-text adaptation).
4. Tests + polish — light trigger-phrase touch on both descriptions; L4 estimator fixtures;
   confirm L1 + codex-skills green; record L2/L3/L8 developer-local results.

## Constraints
- Bound by Non-goals (Q3/Q4/Q9): no gate/exit-code logic, no structured catalog fields, no
  roadmap-template schema change, no consumed size-budget artifact for PRSG-006.
- Shared script via ${CLAUDE_PLUGIN_ROOT}; shared doc single source; ~200 LOC budget.
```

---

## Phase 6: Analyze

```bash
/speckit-analyze

Focus on:
1. Consistency with the design concept (docs/ai/specs/.process/PRSG-005-design-concept.md)
   — flag ANY drift from the 10 locked decisions (Q1–Q10) and the Open Questions.
2. Coverage — every success criterion maps to a task; the estimator has an L4 determinism
   fixture; trigger changes have an L2 plan; the catalog/split behavior has an L3 plan.
3. Codex parity — each CC skill edit has a matching Codex SKILL.md edit; shared doc + script
   are single copies referenced by both runtimes.
4. Scope — nothing strays into PRSG-006 (gate/threshold), PRSG-007/008/009 (engine), or
   roadmap-template schema territory. Confirm advisory-only: no blocking/exit-code logic.
```

---

## Phase 7: Implement

```bash
/speckit-implement

## Approach: TDD-First (RED → GREEN → REFACTOR → VERIFY)

Consult the design concept Q&A for the "why" behind each decision. Key invariants:
- estimate-spec-size.sh is the ONLY home for the sizing math; deterministic; ~400-LOC ceiling
  as a single constant; emits {estimated_loc, suggested_slices, status: ok|warn} (Q2, Q8).
- prd decomposes (catalog-level thin vertical slices, populated Budget line); grill-me
  validates (slice-sizing branch + split sub-interview); guidance prose lives once in the
  shared doc, summarized inline in each skill (Q1, Q4, Q5, Q6).
- ADVISORY-ONLY: nothing blocks; status=warn is informational; no gate/exit-code (Q3).
- No roadmap-template schema change; reuse the existing Budget line (Q9).
- Light trigger touch only; no over/under-trigger regression (Q7).
- Codex parity: mirror both skill edits; shared doc + script runtime-agnostic single copies.

### Verification
1. `bash tests/run-all.sh` (L1 + L4 + L5) green.
2. estimate-spec-size.sh byte-identical on its fixtures (L4); status boundary correct at the
   ceiling.
3. Developer-local evals recorded before merge: L2 (new trigger phrases route; no regression),
   L3 (a fixture idea → thin sliced catalog via prd; a fat single spec → split branch via
   grill-me), L8 (Codex parity).
4. validate-codex-skills.sh + Layer-8 parity green; run speckit-skill-reviewer as a pre-commit
   gate on the changed SKILL.md files.
```

---

## Post-Implementation Checklist

- [ ] All tasks complete in tasks.md.
- [ ] `bash tests/run-all.sh` green (L1 + L4 + L5).
- [ ] estimate-spec-size.sh deterministic on fixtures; advisory-only invariant holds (no blocking).
- [ ] Codex parity: `validate-codex-skills.sh` + Layer-8 parity pass; both skill mirrors updated.
- [ ] Developer-local L2 (trigger) + L3 (functional) recorded as passing.
- [ ] Reviewability gate passes (~200 LOC primary surface).
- [ ] PR created with a plain-English body + UAT runbook.

## Self-Review (post-implementation 4-question audit — reporting only, never gates)

1. **Spec satisfied?** Yes — 17/17 FRs implemented and mapped to tasks; the estimator was read and verified against `contracts/estimate-spec-size.md` (spike short-circuit, FR-016 single normalize path, at-ceiling `-gt` boundary, ceil-min-1 slices, always `exit 0`); quickstart behavior confirmed live; SC-001..006 covered.
2. **Regressions?** None — full suite **1694/1694** green (baseline + new estimator/L4/fixtures).
3. **Conventions/constitution?** Yes — Script Safety (validate-scripts 60/60 incl. the new script, `bash -n` clean, `set -euo pipefail`, chmod +x); KISS heuristic; single-source-of-truth (T017); advisory-only (T018); Codex parity (validate-codex-parity 76/76); conventional commits.
4. **Security / scope / known gaps?** No security surface (bash+jq + markdown). No scope creep — no gate/threshold/exit-code, no split engine, no roadmap-schema change; estimator always exits 0. **Known gaps (reproduced in PR body):** (a) L2/L3/L8 evals (T021–T023) are developer-local pre-merge follow-ups, NOT executed in autopilot; (b) the LOC weights (25/40/15) are a documented first-pass heuristic, tunable later; (c) the tasks-mode reviewability gate over-counted committed SDD artifacts (transition_exception) — the pre-PR diff gate is authoritative.
