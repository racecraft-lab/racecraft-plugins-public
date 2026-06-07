# SpecKit Workflow: PRSG-001 — Artifact relocation: tiering, .process/, collapse

**Template Version**: 1.0.0
**Created**: 2026-06-05
**Purpose**: Tier spec artifacts into CONTRACT vs EXHAUST and collapse the auto-generated exhaust under `.process/` via `linguist-generated`, removing the ~32% process-artifact tax from the review diff at the source.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`, itself grounded by a four-agent pass over the
plugin source. The full Q&A log, Goals, Non-goals, Open Questions, and an
evidence-backed implementation map live at:

```text
docs/ai/specs/PRSG-001-design-concept.md
```

Re-read it before each phase. The locked decisions from that interview (Q1–Q5):

1. **Redirect path = dual `.process/` anchor.** scaffold-spec writes
   `docs/ai/specs/.process/`, autopilot writes `specs/<NNN>/.process/`; one
   `.gitattributes` rule `**/.process/** linguist-generated=true` collapses both.
2. **Reach = both repos.** A static `.gitattributes` in this plugin repo PLUS an
   idempotent consumer-side ensure-step (patterned on `ensure-reviewability-preset.sh`)
   so consuming projects collapse their new specs too.
3. **`uat-runbook.md` = EXHAUST.** Move it to `.process/` and repoint
   `generate-pr-body.sh` so the PR body's UAT section still renders.
4. **Extension-authored exhaust = out of scope; the `archive` extension owns it.**
   PRSG-001 is the **review-window** half: it collapses only what speckit-pro authors
   (design-concept, workflow, uat-runbook). retrospective / verify-tasks-report are
   written by external extensions and stay visible at review; their **post-merge**
   cleanup is already owned by the installed `archive` extension (distill to
   `.specify/memory/` + gated whole-dir removal). Do **not** build a `git mv` sweep —
   that duplicates `archive`. (`verify` writes no file; `peer-review`/`analyze` are
   speckit-pro's own, not extensions.) The roadmap already designed this split
   (locked: collapse-only v1, post-merge relocation deferred to v2; PRSG-011 mirrors
   the archive extension's gated-safety pattern).

> **Note:** Grill Me is human-in-the-loop only and is **not** part of the autopilot
> loop. Once autopilot begins, clarifications happen via `/speckit-clarify` and the
> consensus protocol — never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | spec.md: 14 FRs, US1/US2, 8 ACs, 6 SCs; 0 `[NEEDS CLARIFICATION]`; ext-authored exhaust scoped out (commit 58c03ab) |
| Clarify | `/speckit-clarify` | ✅ Complete | **Skipped** — 0 markers after Specify; the 4 big decisions are locked in the design concept and the 3 session mechanics are carried verbatim in the Plan prompt's grounded map. G6/Analyze verifies design-concept ↔ spec/plan/tasks consistency. |
| Plan | `/speckit-plan` | ✅ Complete | plan.md (20KB) + research.md (pointer); bash+jq+markdown; US1→US2 sequencing; Codex parity identified; constitution PASS via ratified split exception (commit 45ee7cf). Garbled `update-agent-context.sh` CLAUDE.md append reverted. |
| Checklist | `/speckit-checklist` | ✅ Complete | 3 domains; 7 gaps → 0; 1 consensus (safe-write mechanism). Spec hardened FR-009/010/013/015, SC-007 (commit 98a2238) |
| Tasks | `/speckit-tasks` | ✅ Complete | tasks.md: 20 tasks, 4 phases, 3 [P]; full FR/AC/SC coverage; G5 + reviewability tasks gate (excepted) pass (commit cfbd081) |
| Analyze | `/speckit-analyze` | ✅ Complete | 3 MEDIUM findings (plan FR/SC drift ×2 + Out-of-Scope symmetry), all remediated; 0 CRITICAL → G6 pass; consensus not needed (0 unresolved) |
| Implement | `/speckit-implement` | ✅ Complete | 4 groups, all TDD RED→GREEN; G7 full suite 1527/1527 (L1 770 + L4 585 + L5 172) + L8 parity 3/3. Commits: 4ab227e, 5c22e2e, b5fbbb0 |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates (SpecKit Best Practice)

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories clear; no `[NEEDS CLARIFICATION]`; acceptance criteria match the (Q4-narrowed) scope |
| G2 | After Clarify | Redirect/ensure-step/uat mechanics resolved |
| G3 | After Plan | bash+jq+markdown approach; constitution gates pass; Codex-parity work identified |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | US1/US2 tasks cover all ACs; Codex mirror + L1/L4 tasks present |
| G6 | After Analyze | No `CRITICAL`; design-concept ↔ spec/plan/tasks consistent |
| G7 | After Each Implementation Phase | `run-all.sh --layer 1/4` green; Codex parity green; collapse verified on a real diff |

---

## Prerequisites

### Constitution Validation

Verify against `.specify/memory/constitution.md` (v1.1.0) before G1:

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| I. Plugin Structure Compliance | Skill/template edits keep valid structure | `bash tests/run-all.sh --layer 1` |
| II. Script Safety | New/edited `bash` is `set -euo pipefail`, quoted, `jq` for JSON | `validate-scripts.sh` |
| IV. Test Coverage Before Merge | New logic carries L1/L4 tests; AI evals recorded | `bash tests/run-all.sh` (Layers 1,4,5) |
| V. Conventional Commits | `feat(speckit-pro): …` on the PR | CI `validate-pr-title` |
| VI. KISS / YAGNI | Path-string edits, one gate arm — no new abstraction/flags for one call site | Plan review |

**Constitution Check:** ☐ (mark before proceeding to G1)

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | PRSG-001 |
| **Name** | Artifact relocation: tiering, .process/, collapse |
| **Branch** | `007-artifact-relocation` |
| **Dependencies** | None (orthogonal precondition) |
| **Enables** | PRSG-002 (MOC skeleton under `.process/`-aware tree), PRSG-006 (gate threshold rework reuses the aligned exclusion), PRSG-011 (consumes the `.process/` glob + gate fix) |
| **Priority** | P1 (Phase 1, MVP) |
| **Status** | ✅ All 7 phases + post-implementation complete |
| **PR** | [#111](https://github.com/racecraft-lab/racecraft-plugins-public/pull/111) — open, awaiting human review (autopilot does not merge) |

### Success Criteria Summary

From PRD §3.1, narrowed by interview Q4 (scope = speckit-pro-authored exhaust;
extension-authored exhaust documented as future work):

- [ ] **AC-1.1 (scoped):** scaffold-spec/autopilot write the exhaust **speckit-pro
      authors** — `design-concept`, `workflow.md`, and `uat-runbook.md` — under a
      `.process/` directory (`docs/ai/specs/.process/` for scaffold-time files;
      `specs/<NNN>/.process/` for autopilot post-impl files). The CONTRACT set
      (`spec`/`plan`/`tasks`/`research`/`data-model`/`contracts`/`checklists`/`SPEC-MOC`)
      stays at the visible spec root. spec.md documents that extension-authored exhaust
      (retrospective, verify-tasks-report) is not redirected by this spec — it stays
      visible at review and is cleaned up post-merge by the `archive` extension.
- [ ] **AC-1.2:** a repo-root `.gitattributes` marks `**/.process/**` as
      `linguist-generated=true` so a fresh autopilot run's `.process/` diff collapses in
      the GitHub UI yet stays loadable on demand; an idempotent ensure-step writes the
      same rule into a consuming project's `.gitattributes`.
- [ ] **AC-1.3:** a Layer-1 lint asserts every `linguist-generated` line is scoped to a
      `/.process/` segment and never matches a CONTRACT path.
- [ ] **Gate alignment:** `reviewability-gate.sh` `is_excluded_generated()` excludes
      `.process/` paths so relocated exhaust drops out of diff-mode `reviewable_loc`.
- [ ] **Codex parity:** every `skills/*/SKILL.md` prose edit mirrored in
      `codex-skills/`; `validate-codex-skills.sh` (L1) + L8 parity green.

---

## Phase 1: Specify

**When to run:** Start here. Focus on **WHAT** and **WHY**. Output: `specs/007-artifact-relocation/spec.md`

### Specify Prompt

```bash
/speckit-specify

## Feature: Artifact relocation — tiering, .process/, collapse

### Problem Statement
~32% of every feature PR is auto-generated process exhaust (the design concept,
the workflow file, the UAT runbook, and post-impl reports), which buries the
contract artifacts and code a reviewer actually needs to read. Remove that exhaust
from the review diff at the source, by construction, without deleting it (audit and
provenance must survive).

### Users
Reviewers of speckit-pro-generated PRs (in this plugin repo AND in consuming
projects), and the maintainers who rely on the reviewability gate's LOC accounting.

### User Stories
- [US1] Tier + redirect: define CONTRACT (review-visible) vs EXHAUST taxonomy, and
  redirect the exhaust speckit-pro itself authors into a `.process/` directory —
  scaffold-spec's design-concept + workflow into `docs/ai/specs/.process/`, and
  autopilot's uat-runbook into `specs/<NNN>/.process/`. Mirror every SKILL.md prose
  edit into the Codex variant.
- [US2] Collapse + align + lint: ship a repo-root `.gitattributes`
  (`**/.process/** linguist-generated=true`) plus an idempotent ensure-step that writes
  the same rule into a consuming project's repo root; align
  `reviewability-gate.sh is_excluded_generated()` to exclude `.process/`; add a Layer-1
  lint that the glob is scoped to `.process/` only and never a CONTRACT path.

### Constraints
- LOCKED: `linguist-generated` ONLY (no `-diff`) — artifacts stay diffable/loadable.
- LOCKED: new-specs-only — do NOT migrate existing `specs/<NNN>/` dirs (PRSG-011 owns that).
- LOCKED: the gate hardcodes the `.process/` glob (does not parse `.gitattributes`);
  duplication is intentional and guarded by the L1 lint.
- Scripts are plain `bash`+`jq` (CLAUDE.md / constitution principle II); no new
  abstractions or flags for single call sites (principle VI).
- Budget: ~250 production LOC (target, not a ceiling; the consumer ensure-step + uat
  repoint add a little).

### Out of Scope
- Redirecting extension-authored exhaust (retrospective, verify-tasks-report) — they
  are written by external SpecKit extensions; they stay visible in the review window
  and their POST-MERGE cleanup is owned by the installed `archive` extension (distill
  to `.specify/memory/` + gated whole-dir removal). Do NOT wire a `git mv` sweep — it
  duplicates `archive` and the roadmap already defers post-merge relocation to v2.
- Moving the CONTRACT set or any legacy spec.
- `-diff`, retro-migration, MOC templates (PRSG-002), gate threshold rework (PRSG-006).
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 14 (FR-001…FR-014) |
| User Stories | 2 (US1, US2) |
| Acceptance Criteria | AC-1.1, AC-1.2, AC-1.3, AC-1.4 (Codex parity); AC-2.1, AC-2.2 (gate alignment), AC-2.3, AC-2.4 + SC-001…SC-006 |

### Files Generated

- [x] `specs/007-artifact-relocation/spec.md`
- [x] `specs/007-artifact-relocation/checklists/requirements.md`

---

## Phase 2: Clarify (light — most decisions are locked)

The four big decisions are already resolved in the design concept. Use Clarify only
to pin implementation mechanics, max 5 questions per session.

### Clarify Prompts

#### Session 1: Redirect mechanics

```bash
/speckit-clarify Focus on the redirect: exact path strings to change in speckit-scaffold-spec/SKILL.md (mkdir, grill-me output_path, workflow Write target, git add paths) and its Codex mirror; whether the workflow-template self-reference paths move too; how autopilot's workflow-path argument is updated.
```

#### Session 2: Consumer ensure-step + gate

```bash
/speckit-clarify Focus on the consumer-side .gitattributes ensure-step (idempotent append, PROJECT_ROOT from $PWD, where scaffold-spec invokes it) and the exact is_excluded_generated() case arm + which measured number it moves (diff-mode reviewable_loc only).
```

#### Session 3: uat-runbook repoint

```bash
/speckit-clarify Focus on relocating uat-runbook.md to specs/<NNN>/.process/: repointing generate-pr-body.sh (read path + ./uat-runbook.md link) and post-implementation.md (generator output path + git add) so the PR body's "## UAT Runbook" section still renders.
```

### Clarify Results

**Phase skipped** — Specify produced 0 `[NEEDS CLARIFICATION]` markers (the design concept pre-resolved the 4 big decisions). Autopilot Clarify is marker-gated; the 3 session focuses below are implementation mechanics already carried verbatim in the Plan prompt's grounded map, so nothing is lost. Drift is caught at G6 (Analyze checks design-concept ↔ spec/plan/tasks consistency + the ext-authored-exhaust scope cut).

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Redirect mechanics | — (skipped) | Carried in Plan prompt (path-string edits) |
| 2 | Ensure-step + gate | — (skipped) | Carried in Plan prompt (gate arm + ensure-step pattern) |
| 3 | uat repoint | — (skipped) | Carried in Plan prompt (generate-pr-body.sh + post-implementation.md) |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/007-artifact-relocation/plan.md`

### Plan Prompt

```bash
/speckit-plan

## Tech Stack (this is a Claude Code plugin marketplace, NOT an app)
- Skills: Markdown SKILL.md instruction docs (LLM follows literal path strings)
- Scripts: plain bash + jq (set -euo pipefail; quoted; constitution principle II)
- Config: repo-root .gitattributes (new); GitHub linguist collapses linguist-generated
- Tests: shell scripts, 8 layers; CI runs Layers 1/4/5 via `bash tests/run-all.sh`
- Codex parity: codex-skills/ mirrors of skills/ (validate-codex-skills.sh + L8 fixtures)

## Grounded implementation map (from design concept; verify file:line before editing)
US1 (prose; mirror to Codex in the SAME PR):
- speckit-scaffold-spec/SKILL.md — change mkdir, grill-me output_path, workflow Write
  target, and git add paths from docs/ai/specs/ to docs/ai/specs/.process/
- codex-skills/speckit-scaffold-spec/SKILL.md — identical edits (parity mandate)
- speckit-coach/templates/workflow-template.md — design-concept/workflow self-ref paths
- uat-runbook.md -> specs/<NNN>/.process/: repoint generate-pr-body.sh (read path + link)
  and post-implementation.md (generator output path + git add); keep the PR-body
  "## UAT Runbook" section rendering
- autopilot already `git add specs/`; scaffold-spec's explicit add must include .process/

US2:
- NEW repo-root .gitattributes: `**/.process/** linguist-generated=true`
- consumer ensure-step: append that rule idempotently to the consuming repo's
  .gitattributes (model on ensure-reviewability-preset.sh: PROJECT_ROOT=${1:-$PWD},
  write-if-absent), invoked from scaffold-spec
- reviewability-gate.sh is_excluded_generated(): add one arm
  `*/.process/*|*.process/*) return 0 ;;` (anchored on .process/; covers worktree
  prefixes); keep hardcoded (open-decision #6); moves only diff-mode reviewable_loc
- pre-existing dead code at gate line ~54 (docs/ai/workflows/*/exports/*): mention,
  do NOT delete (CLAUDE.md rule 3)

## Constraints
linguist-generated only; new-specs-only; gate hardcodes the glob; bash+jq; no new
flags/abstractions for single call sites; ~250 LOC target.

## Architecture Notes
US2 is INERT until US1 actually moves writes under .process/. Sequence US1 before
US2 verification. is_excluded_generated() does NOT change total_files or
production_files for markdown — only diff-mode reviewable_loc.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ | bash+jq+markdown; redirect map; US1→US2 sequencing; split exception ratified for surface budget |
| `research.md` | ✅ | Thin pointer to design concept (no re-derivation; all decisions locked) |
| `data-model.md` | N/A | Correctly omitted — no data model (taxonomy is prose in spec.md) |
| `contracts/` | N/A | Correctly omitted — no API/CLI/machine interface |
| `quickstart.md` | N/A | Correctly omitted — no user-facing runtime |

---

## Phase 4: Domain Checklists

**Target 2–3 domains.** This is a tooling/process change, so the relevant domains are
about regression safety, not UI/API.

### Recommended domains (from spec analysis)

| Signal in this spec | Domain |
|---|---|
| A glob/lint must NEVER collapse a CONTRACT path; gate must move only the intended number | **data-integrity** (regression safety) |
| Idempotent consumer write; missing/dirty `.gitattributes`; re-run = no-op | **error-handling** |
| new-specs-only must not break existing `specs/<NNN>/` or legacy `docs/ai/specs/` | **backward-compatibility** |

### Step 2: Enriched Checklist Prompts

#### 1. data-integrity Checklist

<!-- Why: the whole feature hinges on collapsing exhaust WITHOUT ever collapsing a review-visible CONTRACT artifact, and on the gate moving only diff-mode reviewable_loc. -->

```bash
/speckit-checklist data-integrity

Focus on Artifact relocation requirements:
- The .gitattributes glob and the gate arm match `.process/` paths ONLY — never spec.md,
  plan.md, tasks.md, research.md, data-model.md, contracts/**, checklists/**, SPEC-MOC.md,
  or *-technical-roadmap.md.
- The L1 lint proves the scoping textually (every linguist-generated line contains /.process/).
- The L4 test asserts .process/ lines drop out of diff-mode reviewable_loc AND a non-.process
  spec file's additions still count (negative control).
- Pay special attention to: the dual-tree anchor (docs/ai/specs/.process/ AND
  specs/<NNN>/.process/) not accidentally matching docs/ai/specs/*-technical-roadmap.md.
```

#### 2. error-handling Checklist

<!-- Why: the consumer-side ensure-step writes into someone else's repo and must be safe and idempotent. -->

```bash
/speckit-checklist error-handling

Focus on Artifact relocation requirements:
- The consumer ensure-step is idempotent (re-run = no-op; line appended only if absent).
- Behavior when the consuming repo has no .gitattributes (create) vs an existing one (append).
- The gate arm degrades safely when no .process/ paths exist (no false exclusions).
- Pay special attention to: never corrupting an existing consumer .gitattributes.
```

#### 3. backward-compatibility Checklist

<!-- Why: new-specs-only is locked; the change must not red-fail existing specs or legacy artifacts. -->

```bash
/speckit-checklist backward-compatibility

Focus on Artifact relocation requirements:
- Existing specs/001..004,006a and legacy docs/ai/specs/SPEC-*-workflow.md are untouched.
- No frontmatter stamp / file move on legacy specs (that is PRSG-011).
- `bash tests/run-all.sh --layer 1` passes on the repo as-is after the change.
- Pay special attention to: the Codex mirror staying in lockstep so L1/L8 don't break.
```

### Checklist Results

| Checklist | Items | Gaps (found→remaining) | Spec References |
|-----------|-------|------|-----------------|
| data-integrity | 22 | 1 → 0 | Key Entities (CONTRACT set enumerated; `*-technical-roadmap.md` named as same-tree, protected) |
| error-handling | 13 | 4 → 0 | FR-009 (create/append-only/idempotent), FR-010 (no-false-exclusion), Edge Cases |
| backward-compatibility | 19 | 2 → 0 | FR-013 (legacy-doc protection), FR-015 + SC-007 (no-regression) |
| **Total** | **54** | **7 → 0** | + 1 consensus item resolved |

**Consensus Resolution Log:**

| Phase / Domain | Item | Categories | Round | N | Outcome | Confidence | Applied to |
|---|---|---|---|---|---|---|---|
| Checklist / error-handling | CHK012 — consumer `.gitattributes` safe-write mechanism | `[codebase]` `[domain]` | 1 | 2 | Temp-file + atomic `mv` (same-dir `mktemp`), fixed-string `grep -qxF` presence guard, trailing-newline normalize before append | High (both analysts agree) | spec.md Edge Case + plan.md (mechanism pinned) |

---

## Phase 5: Tasks

**When to run:** After checklists. Output: `specs/007-artifact-relocation/tasks.md`

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Organize by user story (US1 redirect, US2 collapse+lint), not by technical layer.
- TDD for the deterministic scripts/lints: write the L4/L1 test first (RED), then the
  gate arm / .gitattributes / ensure-step (GREEN).
- Every SKILL.md prose edit gets a paired Codex-mirror task in the same story.
- Mark [P] only for genuinely independent files.

## Implementation Phases
1. Foundation: NEW repo-root .gitattributes (`**/.process/** linguist-generated=true`)
   + L1 lint validate-process-gitattributes.sh + run-all.sh array entry.
2. US1 (redirect): scaffold-spec/SKILL.md + Codex mirror + workflow-template self-refs
   to docs/ai/specs/.process/; uat-runbook -> specs/<NNN>/.process/ with
   generate-pr-body.sh + post-implementation.md repoint; spec.md note on ext-authored
   exhaust being out of scope.
3. US2 (collapse/align): gate is_excluded_generated() arm + extend
   test-reviewability-gate.sh (diff-mode) ; consumer ensure-step + its L4 test.
4. Polish: run-all.sh --layer 1/4/5 green; validate-codex-skills + L8 parity; verify
   collapse on a real fixture diff; PR body still shows the UAT section.

## Constraints (bound tasks by the design-concept Non-goals)
- No task may redirect extension-authored exhaust, add `-diff`, migrate legacy specs,
  make the gate parse .gitattributes, or add a flag/abstraction for one call site.
- L4 must be diff-mode (markdown is never a production_file, so a tasks-mode test is vacuous).
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | 20 (T001-T004, T009A, T010-T024) |
| **Phases** | 4 (Foundation, US1 redirect, US2 collapse/align, Polish) |
| **Parallel Opportunities** | 3 ([P]: T013, T017, T019) |
| **User Stories Covered** | US1, US2 |

---

## Phase 6: Analyze

```bash
/speckit-analyze

Focus on:
1. Constitution alignment — principle II (script safety) and VI (KISS/YAGNI) especially.
2. Coverage — every AC (1.1 scoped, 1.2, 1.3, gate alignment, Codex parity) has a task.
3. Design-concept consistency — the four locked decisions and the grounded map are
   reflected in spec/plan/tasks; flag any drift (the design concept is the source of
   truth for scoping decisions).
4. The ext-authored-exhaust scope cut (Q4) is documented in spec.md, not silently dropped
   or silently expanded into a sweep.
5. US2-before-US1 hazard — verification tasks must not assert collapse before the redirect lands.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| F1 | MEDIUM | plan.md said "14 FRs" — spec now has 15 | plan.md → "15 FRs" |
| F2 | MEDIUM | plan.md traceability "FR-001…FR-014 / SC-001…SC-006" stale | plan.md → "FR-001…FR-015 / SC-001…SC-007" |
| F3 | MEDIUM | Out-of-Scope "migrating legacy spec" named only `specs/<NNN>/`, asymmetric with broadened FR-013 | spec.md Out-of-Scope bullet extended to cover legacy `docs/ai/specs/` files (consistent with FR-013) |
| — | — | **0 CRITICAL, 0 HIGH** → G6 PASS; locked decisions intact; US2-before-US1 holds | Unresolved for consensus: NONE |

---

## Phase 7: Implement

```bash
/speckit-implement

## Approach: TDD-First (for the deterministic pieces)
1. RED: write the L1 lint + L4 gate/ensure-step tests; confirm they FAIL.
2. GREEN: .gitattributes, the gate arm, the consumer ensure-step, the prose redirects.
3. REFACTOR: keep edits surgical; match existing script/skill style.
4. VERIFY: collapse on a real diff; PR body UAT section renders.

### Pre-Implementation Setup
1. Work in the worktree on branch 007-artifact-relocation.
2. Baseline green: `bash speckit-pro/tests/run-all.sh` (Layers 1,4,5).
3. Keep the Codex mirror edits in the SAME commits as their skills/ counterparts.

### Project commands (run from speckit-pro/)
- Layer 1: `bash tests/run-all.sh --layer 1`
- Layer 4: `bash tests/run-all.sh --layer 4`
- Codex parity: part of `--layer 1` (validate-codex-skills.sh); L8: `bash tests/layer8-parity/run-parity-fixtures.sh --dry-run`

### Implementation Notes
- Edit literal path strings in SKILL.md (LLM follows them); no helper layer.
- Gate arm anchored on `.process/`; do not delete the pre-existing stale exports arm.
- uat repoint must keep the PR-body "## UAT Runbook" section rendering (regression risk).
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation (.gitattributes + L1) | T001-T004, T009A | ✅ | .gitattributes rule + scope lint (5 checks); RED→GREEN proven; L1 765→770 (4ab227e) |
| 2 - US1 (redirect + Codex mirror) | T010-T016 | ✅ | scaffold-spec + Codex mirror lockstep + post-impl mirror + uat repoint; codex-parity 72/72 (5c22e2e) |
| 3 - US2 (gate + ensure-step + L4) | T017-T020 | ✅ | gate .process/ arm + consensus safe-write ensure-step; both TDD; L4 572→585 (b5fbbb0) |
| 4 - Polish (parity, collapse verify) | T021-T024 | ✅ | real-fixture collapse (reviewable_loc 5, .process/ excluded) + UAT renders from .process/ + zero data loss; verification-only |

---

## Post-Implementation Checklist

- [ ] All tasks complete in tasks.md
- [ ] `bash speckit-pro/tests/run-all.sh` green (Layers 1, 4, 5)
- [ ] `validate-codex-skills.sh` green; L8 parity dry-run green
- [ ] `.process/` diff collapses on a real autopilot/fixture PR; files load on demand
- [ ] PR body still renders the UAT Runbook section
- [ ] spec.md documents the extension-authored-exhaust scope cut
- [ ] PR title `feat(speckit-pro): collapse generated spec exhaust under .process/` (Conventional Commits; public-readable)
- [ ] PR created and reviewed (human merges — not the agent)

---

## Self-Review (4-question audit — reporting only, does not gate)

1. **Does the implementation satisfy every spec requirement?** Yes. All 15 FRs / 8 ACs / 7 SCs are covered and fixture-verified: the repo-root collapse rule + scope lint (FR-007/008/012, AC-2.1/2.4, SC-005), the gate `.process/` exclusion arm (FR-010/011, AC-2.2, SC-003), the crash-safe consumer ensure-step (FR-009, AC-2.3, SC-004), the US1 redirects with byte-identical Codex mirrors (FR-001–006, AC-1.1–1.4, SC-001/002/006), and no-regression (FR-015, SC-007). A real-fixture run showed `.process/` lines drop from reviewable LOC (5 vs 35), the PR-body UAT section renders from the relocated runbook, and no artifact is lost.
2. **Any shortcuts / TODOs / tech debt?** None introduced. The consumer write uses the consensus-decided crash-safe pattern (same-dir temp + atomic rename + trailing-newline normalize + fixed-string guard), not a naive append. One **pre-existing** defect was discovered (not introduced, not fixed here, out of scope): `count-markers.sh` errors when ≥2 scanned files emit `[]` — flagged as a separate follow-up.
3. **Is the change surgical?** Yes. Every changed line traces to a task/requirement. New-specs-only is honored (no legacy spec/doc moved). The pre-existing dead-code arm in the gate was left untouched. The SpecKit 0.9.4 integration refresh is isolated in its own commit, not mixed into feature commits.
4. **Are tests adequate?** Yes. New Layer-1 scope lint (RED-proven, incl. the broadening case), extended Layer-4 gate test (diff-mode + no-false-exclusion negative controls), extended Layer-4 ensure-step test (create/append/idempotent/newline-normalize/byte-preserve/convergence), Codex parity (Layer-1 + Layer-8), and an end-to-end fixture. Full suite green at 1527/1527.

## Lessons Learned

### What Worked Well
- Pre-resolving decisions in the design concept made Clarify a no-op (0 markers) and kept Checklist/Analyze focused on real gaps.
- Isolating the SpecKit 0.9.4 integration refresh in its own commit kept the feature diff legible.
- Two-analyst consensus settled the one genuinely-open design choice (consumer-file safe-write) with a crash-safe, repo-idiomatic mechanism.

### Challenges Encountered
- Two subagent runs hit transport/socket interruptions mid-task; independent on-disk verification confirmed their work and recovered the summaries (no rework needed).
- The reviewability gate's tasks-mode file count (105) was a path-token artifact; the real diff is far smaller — verified against `origin/main` after fetching (local main was stale).

### Patterns to Reuse
- For consumer-file edits, the same-dir `mktemp` + atomic `mv` + trailing-newline-normalize + `grep -qxF` guard is the crash-safe, idempotent idiom.
- Always recompute PR scope against a freshly-fetched `origin/main`, not local main.

---

## Project Structure Reference

```
speckit-pro/
├── skills/
│   ├── speckit-scaffold-spec/SKILL.md      # US1 redirect edits
│   ├── speckit-autopilot/
│   │   ├── references/post-implementation.md # uat repoint
│   │   └── scripts/
│   │       ├── reviewability-gate.sh        # US2 gate arm
│   │       └── generate-pr-body.sh          # uat read path + link
│   └── speckit-coach/
│       ├── templates/workflow-template.md   # self-ref paths
│       └── scripts/ensure-reviewability-preset.sh # ensure-step pattern
├── codex-skills/speckit-scaffold-spec/SKILL.md # parity mirror
└── tests/
    ├── layer1-structural/validate-process-gitattributes.sh # NEW (US2)
    └── layer4-scripts/test-reviewability-gate.sh           # extend (US2)
.gitattributes                                # NEW repo-root (US2)
```

---

Populated from the PRSG-001 design concept and a grounded source pass. The design
concept doc is the source of truth for any scoping decision captured during the interview.
