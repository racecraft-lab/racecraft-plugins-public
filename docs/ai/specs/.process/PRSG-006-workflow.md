# SpecKit Workflow: PRSG-006 — Plan-phase reviewability budget + gate threshold rework

**Template Version**: 1.0.0
**Created**: 2026-06-06
**Purpose**: Populated workflow guide for executing PRSG-006 autonomously via
`/speckit-pro:speckit-autopilot`. Phase prompts below were enriched from the Grill Me
interview captured in the design concept doc.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log (Q1–Q10), Goals, Non-goals, and
Open Questions live at:

```text
docs/ai/specs/.process/PRSG-006-design-concept.md
```

**Re-read it before each phase.** The design concept is the **source of truth** for
every scoping decision captured during the interview. Where a phase prompt cites
"Q3" / "Q7" etc., that refers to the numbered Q&A entries in that doc.

> **Note:** Grill Me is human-in-the-loop only. It is **not** part of the autopilot
> loop. Once autopilot begins, clarifications happen via `/speckit-clarify` and the
> consensus protocol — never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | spec.md: 15 FRs (FR-001–015), US1/US2, 0 `[NEEDS CLARIFICATION]`, G1 `pass:true`. Branch-aware override held (no derail). |
| Clarify | `/speckit-clarify` | ⏳ Pending | Sessions seeded from design-concept Open Questions |
| Plan | `/speckit-plan` | ⏳ Pending | |
| Checklist | `/speckit-checklist` | ⏳ Pending | error-handling + data-integrity |
| Tasks | `/speckit-tasks` | ⏳ Pending | Two user stories: US1 plan budget, US2 gate rework |
| Analyze | `/speckit-analyze` | ⏳ Pending | |
| Implement | `/speckit-implement` | ⏳ Pending | Scripts-first; TDD red→green |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates (SpecKit Best Practice)

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | US1/US2 clear, no `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | Ambiguities resolved, decisions traceable to the design concept |
| G3 | After Plan | Two-script architecture approved; constitution gates pass |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Every FR + both user stories have tasks; deterministic logic mapped to L4 |
| G6 | After Analyze | No `CRITICAL`; no drift from design-concept Goals/Non-goals |
| G7 | After Each Implementation Phase | L1/L4 green locally; L3/L8 recorded before merge |

**Required test layers (authoritative, per roadmap coverage table):
L1, L3, L4, L8. No L7** — PRSG-006 adds no new agent.

---

## Prerequisites

### Constitution Validation

Verify alignment with `.specify/memory/constitution.md` before G1:

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| II. Script Safety | New script uses `set -euo pipefail`, `bash`+`jq` only, no new dependency | `bash -n`, shellcheck, L4 fixture |
| IV. Test Coverage Before Merge | L1/L3/L4/L8 recorded passing before merge | `bash tests/run-all.sh` + developer-local L3 |
| VI. KISS / YAGNI | No differential per-class exception allowances; one tunable greenfield factor | Code review |

**Constitution Check:** ✅ (G0 baseline `bash speckit-pro/tests/run-all.sh` = 1509/1509 green: L1 348+417, L4 572, L5 172, on 2026-06-06 before any change). II/IV/VI verified pre-change; re-checked at G7.

**Autopilot Run Context (recorded Phase 0):**
- Branch `prsg-006-reviewability-budget` is non-`NNN-` → `on_feature_branch=false` by the regex, but it IS the deliberate feature branch. Orchestrator override: Specify is branch-aware (skip `create-new-feature.sh`); feature dir `specs/prsg-006-reviewability-budget/` pre-created.
- `.specify/feature.json` was stale (`specs/006a-uat-skeleton`) → repointed to `specs/prsg-006-reviewability-budget` so `get_feature_paths` resolves correctly for Plan/Tasks/gate; will be restored to base value before PR creation (local state, not a deliverable).
- `PROJECT_COMMANDS` auto-detect was blank (bash/shell repo) → overridden to `bash speckit-pro/tests/run-all.sh --layer {1,4,5}` (UNIT_TEST=L4, FULL_VERIFY=L1). TDD granularity is fixture-level.
- Archive sweep skipped (stacked branch; would pull complete 001–004 into this PR).
- Confidence gate mode: `advisory`. Settings: defaults (gate-failure=stop).

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | PRSG-006 |
| **Name** | Plan-phase reviewability budget + gate threshold rework |
| **Branch** | `prsg-006-reviewability-budget` |
| **Dependencies** | PRSG-001 (`.process/` relocation + the gate's `is_excluded_generated()` glob) |
| **Enables** | PRSG-007 (the atomicity router consumes the plan-time budget + surface signal) |
| **Priority** | P1 · Phase 3 |

### Success Criteria Summary

From the PR-Size Governance roadmap (Phase-3 definition of done) + the design concept:

- [ ] Plan phase **auto-approves under budget** (silent pass) and only surfaces/records
      when a slice is over budget — advisory in autonomous autopilot, a decision in
      interactive use (design concept Q1, Q3).
- [ ] The gate's LOC metric counts **production code only**; warn `400` / block `800`
      stay on that narrower metric (Q4).
- [ ] All-new slices get a **1.5× greenfield allowance** (Q5).
- [ ] **Surface-count is no longer a blocker** — downgraded to a warning (Q6).
- [ ] The one-keyword exception is replaced by a typed, fail-closed
      `Reviewability-Exception: {refactor|infra|upgrade}` pragma (Q7).
- [ ] The roadmap template's Reviewability Contract matches the reworked gate (Q8).
- [ ] Old exception keywords are no longer honored; the break is documented for
      PRSG-011 (Q9).
- [ ] The autopilot plan-phase change is mirrored in `codex-skills/speckit-autopilot`;
      scripts + template stay single-copy (Q10).

---

## Phase 1: Specify

**When to run:** Start of the feature. Focus on **WHAT** and **WHY**. Output:
`specs/prsg-006-reviewability-budget/spec.md`

### Specify Prompt

```bash
/speckit-specify

## Feature: Plan-phase reviewability budget + gate threshold rework (PRSG-006)

### Problem Statement
Reviewable-PR sizing today is DETECTIVE: the only enforcement is an end-stage
`reviewability-gate.sh` whose escape hatch (any of three magic phrases anywhere in a
doc) makes it a defeated no-op, and whose metrics are wrong (it counts total reviewable
LOC including docs/tests, and treats multi-surface as a hard block). PRSG-006 makes
sizing PREVENTIVE — decided at plan time — and corrects the gate's metrics and
exception model. (See design concept Goals.)

### Users
The speckit-pro autopilot (which runs the plan-phase budget) and the human reviewer /
maintainer who reads the resulting PRs and audits exceptions.

### User Stories
[US1] Preventive plan-phase budget. During the autopilot PLAN phase, a deterministic
estimator projects each slice's production-LOC footprint FROM plan.md's planned-file
structure (plan runs before tasks.md exists — design concept Q1), auto-approves under
budget (silent pass), and surfaces only when over — recorded-and-continue in the
autonomous run, a human decision interactively (Q3).

[US2] Threshold + exception rework on reviewability-gate.sh:
  - Recount LOC as PRODUCTION code only (is_production_file & not excluded); keep
    warn=400 / block=800 on that narrower metric (Q4).
  - Apply a 1.5x greenfield allowance when a slice adds only net-new files (Q5).
  - Downgrade primary-surface-count from a blocker to a warning; keep it in the JSON
    output for downstream consumers (Q6).
  - Replace the loose 3-phrase exception keyword with a typed, fail-closed
    `Reviewability-Exception: {refactor|infra|upgrade}` pragma (Q7).
  - Update the roadmap template's Reviewability Contract to match the reworked gate, so
    setup-mode parsing stays consistent (Q8).

### Constraints
- Deterministic logic MUST be bash+jq scripts with an L4 determinism fixture
  (same inputs -> byte-identical output), NOT LLM reasoning (constitution II;
  scripts-first mandate).
- estimate-reviewable-loc.sh is a SEPARATE script; the gate keeps its setup/tasks/diff
  modes; the production-LOC-per-file constant is shared via a copied "keep in sync"
  comment, the repo's established pattern (Q2).
- Greenfield detection is deterministic: plan.md NEW-file list at plan time; git
  A-status at diff time (Q5).

### Out of Scope
- The split-PR engine (PRSG-007/008/009). PRSG-006 is upstream sizing only — it does
  not split anything.
- Making an over-budget result BLOCK or trigger re-slicing — that is PRSG-010
  ("harden the hatch LAST"). The plan budget stays advisory; the gate stays
  detective-but-correct (Q3).
- Removing the exception boilerplate from the template entirely (PRSG-010) and
  retro-migrating legacy roadmaps / old keywords (PRSG-011). Old keywords stop being
  honored here, new-specs-only; document the break for PRSG-011 (Q9).
- Aligning is_excluded_generated() to the .process/ glob (that is PRSG-001).
- Differential per-class exception allowances (YAGNI — all three classes flip a block
  equally in v1).
```

### SpecKit Traceability Markers

Use `[US1]`/`[US2]`, `[FR-001]`, `[NEEDS CLARIFICATION]`, `[P]`, `[Gap]` in spec.md.

### Files Generated

- [ ] `specs/prsg-006-reviewability-budget/spec.md`

---

## Phase 2: Clarify

**Best Practice:** Max 5 targeted questions per session. The interview already resolved
the major branches (design concept Q1–Q10); these sessions target what it deferred
(Open Questions) plus implementation-edge ambiguity.

### Clarify Prompts

#### Session 1: Plan-phase estimation mechanics

```bash
/speckit-clarify Focus on the plan-phase estimator: the exact per-file LOC heuristic
that maps a plan.md planned-file entry to projected production-LOC (flat ×40, as the
gate's measure_feature_dir uses, vs weighted by file type); how plan.md must declare
its planned files so the parse is deterministic; and what the estimator does when
plan.md lists no files yet. Keep the determinism contract fixed (same plan.md ->
byte-identical output). See design-concept Open Questions.
```

#### Session 2: Gate metric + greenfield semantics

```bash
/speckit-clarify Focus on the gate rework: confirm the production-file predicate used
for the LOC recount (reuse is_production_file & is_excluded_generated); where the 1.5×
greenfield factor lives (hardcoded vs one named variable); how greenfield is detected
in diff mode (git A-status) vs at plan time (plan.md NEW-file list); and that warn/block
stay 400/800 on the production-only metric.
```

#### Session 3: Exception pragma + backward-compat break

```bash
/speckit-clarify Focus on the typed exception: the exact pragma syntax
(`Reviewability-Exception: <class>`), the closed enum {refactor, infra, upgrade}, the
fail-closed behavior for unknown/missing classes, and where the pragma is read from in
each mode (setup parses the roadmap/template; diff parses the PR/commit). Confirm old
keywords (split/transition/ratified exception) are no longer honored and the break is
recorded for PRSG-011.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Estimator mechanics | 2 (both → consensus) | **Q1 (declaration format):** split (codebase-analyst: add planned-files block to preset plan-template; spec-context-analyst: out-of-scope, parse existing tree). **Synthesis (altitude reconcile):** spec sets constraints, Plan picks the parse convention — added to spec Deferred (deterministic, enumerate prod files + new/modified, no unflagged template-surface expansion). **Q2 (empty plan):** unanimous (domain + spec-context + executor) → "not estimated" (3-value status `{pass,over_budget,not_estimated}`, `projected:null`, non-blocking). Folded in: ×40 is per-task→estimator declares own per-file constant (FR-007); `is_production_file` doesn't match repo `.sh` (known limit, PRSG-001); L4 fixture must assert known LOC value (FR-002). Edits: FR-002/003/007, Edge Case, Key Entities, Assumptions, Deferred. |
| 2 | Gate metric + greenfield | | |
| 3 | Exception pragma + back-compat | | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output:
`specs/prsg-006-reviewability-budget/plan.md`

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Runtime: Bash (macOS/Linux), jq for JSON. No new dependency (CLAUDE.md rule 2).
- Surface: speckit-pro plugin skills + scripts + templates. No product code.
- Tests: shell-script test layers (L1 structural, L3 functional eval, L4 script-unit
  determinism, L8 Codex parity). Run from speckit-pro/: `bash tests/run-all.sh`.

## Files in scope (from the design concept)
- speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh — rework:
  production-LOC metric, 1.5× greenfield, surface-count -> warning, typed pragma.
- speckit-pro/skills/speckit-autopilot/scripts/estimate-reviewable-loc.sh — NEW
  standalone plan-phase estimator (Q1, Q2). Parses plan.md planned-file structure;
  shares the LOC-per-file constant with the gate via a copied "keep in sync" comment.
- speckit-pro/skills/speckit-autopilot/SKILL.md + references/phase-execution.md —
  wire the plan-phase budget step (auto-approve under budget; record-and-proceed when
  over in autonomous; surface interactively — Q3).
- speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md — update
  the Reviewability Contract to match the reworked gate (Q8).
- speckit-pro/codex-skills/speckit-autopilot/{SKILL.md,references/phase-execution-codex.md}
  — mirror ONLY the plan-phase change (Q10). Scripts + template are single-copy.

## Architecture Notes
- TWO scripts, not a 4th gate mode (Q2). Gate keeps setup/tasks/diff. The estimator is
  a new entry point the plan phase calls directly.
- Reuse, don't reinvent: the gate already has is_production_file, is_excluded_generated,
  surface_for_path, emit_result, and a tasks×40 LOC heuristic. The recount changes WHICH
  files feed the LOC sum (production-only) and removes the surface-count BLOCKER line
  while keeping the warning. The estimator reuses the same predicates.
- Plan phase precedes tasks.md (Q1) — the estimator's input is plan.md's planned-file
  list, not a task count.

## Constraints
- Determinism: same plan.md / same diff -> byte-identical JSON (constitution II).
- Sequencing (non-negotiable): over-budget is ADVISORY here; blocking/re-slicing is
  PRSG-010. Do not wire a hard block (Q3).
- Re-read docs/ai/specs/.process/PRSG-006-design-concept.md for any decision the prompt
  did not capture.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Two-script design; plan-phase wiring |
| `research.md` | ⏳ | Only if a genuinely open decision needs it |
| `data-model.md` | ⏳ | N/A (no data model) |
| `contracts/` | ⏳ | The estimator/gate JSON output shape is the contract |
| `quickstart.md` | ⏳ | Optional |

---

## Phase 4: Domain Checklists

**Recommended domains (2):** the spec is a deterministic-script + control-flow change,
so the standard UI/API/accessibility domains don't apply. Prioritize:

### 1. error-handling Checklist

<!-- Why: the gate is a control with exit codes + a fail-closed exception path; wrong
error handling silently rubber-stamps or wrongly blocks. -->

```bash
/speckit-checklist error-handling

Focus on PRSG-006 reviewability-gate + estimator requirements:
- Fail-closed exception: an unknown/missing Reviewability-Exception class must NOT
  flip a block (stays block); only {refactor, infra, upgrade} are honored.
- Exit-code contract: 0 within budget, 1 block, 2 usage/unreadable — unchanged and
  asserted; the new estimator's exit codes are defined and tested.
- Over-budget at plan phase records-and-proceeds in autonomous mode (never crashes the
  run) and surfaces a decision interactively.
- Malformed / empty plan.md and missing planned-file list degrade gracefully.
- Pay special attention to: the boundary where surface-count stops blocking but still
  warns.
```

### 2. data-integrity Checklist

<!-- Why: the whole value is a trustworthy, deterministic number; a non-deterministic
or double-counted estimate defeats preventive sizing. -->

```bash
/speckit-checklist data-integrity

Focus on PRSG-006 estimation correctness:
- Determinism: same plan.md / same diff -> byte-identical JSON (L4 fixture).
- Production-LOC metric counts production files only (is_production_file &
  not is_excluded_generated); docs/tests/config excluded; no double counting.
- The shared LOC-per-file constant stays in sync between gate and estimator
  (keep-in-sync comment) — drift is caught.
- Greenfield detection is exact: all-new-files -> 1.5×; any modified existing file ->
  no multiplier. git A-status (diff) and plan.md NEW-list (plan) agree.
- Pay special attention to: backward-compat — old exception keywords no longer counted;
  the break is documented for PRSG-011.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| error-handling | | | |
| data-integrity | | | |
| **Total** | | | |

---

## Phase 5: Tasks

**When to run:** After checklists (gaps resolved). Output:
`specs/prsg-006-reviewability-budget/tasks.md`

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Small, testable chunks. Each deterministic behavior gets an L4 fixture
  (same inputs -> byte-identical output) BEFORE the implementation (TDD red first).
- Organize by user story: US1 (plan-phase budget) and US2 (gate rework), not by layer.
- Mark parallel-safe tasks [P]. The estimator (US1) and the gate rework (US2) share the
  LOC constant but are otherwise independent files — much of US1/US2 is [P].

## Implementation Phases
1. Foundation — shared LOC-per-file constant + keep-in-sync comment; production-file
   predicate confirmed reusable.
2. US1 — estimate-reviewable-loc.sh (plan.md parse -> production-LOC projection;
   greenfield 1.5×; JSON output) + plan-phase wiring in autopilot SKILL/phase-execution
   + Codex mirror.
3. US2 — gate rework: production-LOC recount; surface-count blocker -> warning; typed
   fail-closed exception pragma; roadmap-template Reviewability Contract update.
4. Polish — L1 structural asserts (script exists; template vocabulary matches gate;
   validate-codex-skills); L3 functional eval; L8 parity; document the back-compat break.

## Constraints (bound tasks by the design-concept Non-goals)
- NO task may add split-PR emission, a hard plan-phase block, re-slicing wiring, or
  legacy migration — those are PRSG-007/008/009/010/011. Flag any such task as
  out-of-scope.
- Required layers: L1, L3, L4, L8. NO L7 (no new agent) — do not generate L7 tasks.
- Reference docs/ai/specs/.process/PRSG-006-design-concept.md for the "why" behind each
  decision when writing test specs.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | |
| **Phases** | |
| **Parallel Opportunities** | |
| **User Stories Covered** | US1, US2 |

---

## Phase 6: Analyze

```bash
/speckit-analyze

Focus on:
1. Constitution alignment — II (script safety / scripts-first), IV (L1/L3/L4/L8 before
   merge), VI (KISS/YAGNI — no per-class allowances, one greenfield factor).
2. Coverage — every FR + US1 + US2 has tasks; every deterministic behavior has an L4
   fixture; the Codex mirror change has L8.
3. Cross-artifact consistency across spec.md, plan.md, tasks.md AND
   docs/ai/specs/.process/PRSG-006-design-concept.md. Flag ANY drift from the design
   concept's Goals / Non-goals / decisions (Q1–Q10). The design concept is the source
   of truth for scoping; a downstream artifact that contradicts it is wrong unless an
   explicit revision note exists.
4. Boundary leakage — flag any task that crosses into PRSG-007/008/009/010/011 territory
   (splitting, hard blocking, re-slicing, legacy migration).
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| | | | |

---

## Phase 7: Implement

```bash
/speckit-implement

## Approach: TDD-First (scripts-first)
For each deterministic behavior:
1. RED: write the L4 fixture (committed input -> expected byte-identical output); verify
   it FAILS.
2. GREEN: minimum bash+jq to pass.
3. REFACTOR: clean up while the fixture stays green.
4. VERIFY: run `bash tests/run-all.sh --layer 1` and `--layer 4` from speckit-pro/.

### Implementation Notes
- Extend the existing tests/layer4-scripts/test-reviewability-gate.sh for the reworked
  metric/surface/exception behavior; add a new determinism test for
  estimate-reviewable-loc.sh.
- Keep `set -euo pipefail`; bash+jq only. Match the gate's existing style.
- Mirror the autopilot plan-phase wording change into codex-skills/speckit-autopilot
  and keep validate-codex-skills.sh (L1) + L8 parity green. Run speckit-skill-reviewer
  as a pre-commit gate on any changed mirrored SKILL.md.
- Consult docs/ai/specs/.process/PRSG-006-design-concept.md Q&A for the "why" behind
  each edge case. Any decision in the design concept not reflected in tasks.md is a gap
  to surface BEFORE coding, not silently drop.

### Verification (Definition of Done)
- L1 + L4 green in CI (`bash tests/run-all.sh`).
- L3 functional eval (plan auto-approves under budget; surfaces/records when over) and
  L8 parity recorded passing developer-local BEFORE merge (constitution IV).
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation | | | shared LOC constant |
| 2 - US1 plan budget | | | estimator + wiring + Codex mirror |
| 3 - US2 gate rework | | | metric/surface/exception + template |
| 4 - Polish | | | L1/L3/L4/L8 + doc the break |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in tasks.md
- [ ] L1 structural: `bash tests/run-all.sh --layer 1` green
- [ ] L4 script-unit: `bash tests/run-all.sh --layer 4` green (gate + estimator fixtures)
- [ ] L3 functional eval recorded passing (developer-local, `claude -p`)
- [ ] L8 Codex parity recorded passing
- [ ] Back-compat break (old exception keywords) documented for PRSG-011
- [ ] PR created (plain-English title with conventional-commits prefix) and reviewed

---

## Project Structure Reference

```
speckit-pro/
├── skills/
│   ├── speckit-autopilot/
│   │   ├── SKILL.md                         # plan-phase budget wiring (US1)
│   │   ├── references/phase-execution.md    # plan-phase budget step
│   │   └── scripts/
│   │       ├── reviewability-gate.sh        # rework (US2)
│   │       └── estimate-reviewable-loc.sh   # NEW (US1)
│   └── speckit-coach/
│       └── templates/technical-roadmap-template.md  # Reviewability Contract (US2/Q8)
├── codex-skills/speckit-autopilot/          # mirror plan-phase change only (Q10)
└── tests/
    ├── layer1-structural/                   # L1
    ├── layer4-scripts/test-reviewability-gate.sh  # extend; + estimator test
    └── layer8-parity/                       # L8
```

---

Populated from the PRSG-006 design concept (10 Q&A entries). The design concept doc is
the source of truth for any decision captured during scoping.
