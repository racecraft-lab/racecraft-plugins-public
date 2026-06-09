# SpecKit Workflow: PRSG-011 - Retro-migration: version marker + state-keyed backfill/relocate

**Template Version**: 1.0.0
**Created**: 2026-06-08
**Purpose**: Add the backward/contract half for PR-size governance: a deterministic repo-level structure migration runner, navigation backfill for historical specs, and an explicit on-demand codemod for thawed legacy PROCESS artifacts.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`$speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/PRSG-011-design-concept.md
```

Re-read it before each phase. The locked decisions from that interview:

1. Treat the six PRD/roadmap defaults as accepted.
2. Canonical review packet filename: `pr-review-packet.md`; recognize legacy `peer-review-*`.
3. Canonical evidence shape: `evidence/`; migrate `verification-evidence.md` into `evidence/verification-evidence.md`.
4. Include exact and prefixed design concept/workflow files in the PROCESS relocation allow-list.
5. Dogfood deferred PRSG-001 artifact cases through deterministic fixtures, not by moving real historical docs.
6. Allow dirty-tree `--dry-run`; hard-fail every mutating mode on a dirty tree before backup or mutation.
7. Include completed/archived ID-normalizable specs in Tier-0 navigation backfill without stamping or moving them.
8. Skip in-flight specs from `.specify/feature.json` in every tier and print a frozen/in-flight reason.
9. Scaffold/autopilot only suggest the Tier-2 codemod; they never auto-run it.
10. Use `structureVersion` 1 for the first repo-level marker and stamps.
11. Keep PRSG-011 as one spec, ordered as two internal vertical increments.

> **Note:** Grill Me is human-in-the-loop only and is not part of the autopilot
> loop. Once autopilot begins, clarifications happen via `/speckit-clarify` and
> the consensus protocol, never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Complete | 3 user stories, 22 functional requirements, 12 acceptance scenarios, 0 clarification markers |
| Clarify | `/speckit-clarify` | Complete | 3 sessions resolved; 5 consensus rows logged; 0 clarification markers |
| Plan | `/speckit-plan` | Complete | plan.md + research/data-model/quickstart + 3 contracts. Declared file operations filled; reviewability warning preserved with two internal vertical increments; G3 pass. |
| Checklist | `/speckit-checklist` | Complete | 4 domains complete; 11 gaps found and remediated; G4 pass |
| Tasks | `/speckit-tasks` | Complete | 34 tasks; 6 parallel-safe; reviewability gate exception/pass honored |
| Analyze | `/speckit-analyze` | Complete | 2 semantic findings remediated; G6 pass; confidence gate 0.94/pass |
| Implement | `/speckit-implement` | Complete | 34/34 tasks complete; post-implementation tail in progress |

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories clear; no unresolved `[NEEDS CLARIFICATION]`; migration tiers and frozen-spec behavior explicit |
| G2 | After Clarify | Script CLI, allow-list, and registration behavior resolved |
| G3 | After Plan | Bash+jq approach approved; reviewability warning accepted; Codex parity identified |
| G4 | After Checklist | All `[Gap]` markers addressed or explicitly scoped out |
| G5 | After Tasks | Tasks cover Tier-1/Tier-0 first, then Tier-2/register; reviewability checkpoint recorded |
| G6 | After Analyze | No `CRITICAL`; design-concept decisions match spec, plan, and tasks |
| G7 | After Each Implementation Phase | Layer 1/4 checks green; affected Layer 3/8 work recorded |

---

## Prerequisites

### Constitution Validation

Verify against `.specify/memory/constitution.md` v1.1.0 before G1:

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| I. Plugin Structure Compliance | New scripts, tests, skill docs, and mirrored Codex skill docs keep the plugin layout valid | `bash tests/speckit-pro/run-all.sh --layer 1` |
| II. Script Safety | New bash scripts use `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, and `jq` for JSON | `bash tests/speckit-pro/layer1-structural/validate-scripts.sh` and Layer 4 tests |
| IV. Test Coverage Before Merge | New deterministic logic has Layer 4 fixtures; skill behavior changes have Layer 3; Codex parity has Layer 8 | `bash tests/speckit-pro/run-all.sh`; targeted L3/L8 local runs as applicable |
| V. Conventional Commits | Setup and implementation commits use `type(scope): description` | Git log / PR title |
| VI. KISS, Simplicity & YAGNI | Deterministic migration logic stays script-first; no agent or abstraction for one-off decisions | Plan review |

**Constitution Check:** Verified.

**Autopilot Preflight:** Verified 2026-06-09.

| Check | Result | Evidence |
|-------|--------|----------|
| Prerequisites | Verified | `check-prerequisites.sh` returned `all_pass=true`; branch `prsg-011-retro-migration`; worktree=true |
| MCP availability | Fallbacks available | Missing: tavily-mcp, context7, RepoPrompt |
| Command detection | Recorded | Build/typecheck/lint/test auto-detection returned `N/A`; workflow-specific gates remain authoritative |
| Preset detection | Recorded | `speckit-pro-reviewability` preset active for spec/plan/tasks templates |
| Extension detection | Recorded | archive, verify, verify-tasks, retrospective, speckit-utils, git enabled; review/cleanup not installed |
| Archive sweep | Recorded | Current target `specs/prsg-011-retro-migration` excluded; cleanup disabled because no executable sweep script is vendored |
| Constitution validation | Verified | `bash tests/speckit-pro/run-all.sh --layer 1` passed 887/887; `validate-scripts.sh` passed 83/83 |

**PROJECT_COMMANDS:** BUILD=N/A; TYPECHECK=N/A; LINT=N/A; UNIT_TEST=N/A; INTEGRATION_TEST=N/A; FULL_VERIFY=N/A.

**PRESET_CONVENTIONS:** Use `speckit-pro-reviewability` templates for spec, plan, and tasks; preserve reviewability declared-file structure and SPEC-MOC conventions.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | PRSG-011 |
| **Name** | Retro-migration: version marker + state-keyed backfill/relocate |
| **Branch** | `prsg-011-retro-migration` |
| **Dependencies** | PRSG-001 (`.process` glob), PRSG-002 (MOC contract + version-gated lints), PRSG-003 (index generator) |
| **Enables** | Legacy project upgrade path; future structure migrations via `structureVersion` 2+ |
| **Priority** | P2, Phase 6 |
| **Reviewability Budget** | Warning accepted: Grill Me estimator returned 440 estimated LOC, 2 suggested slices; keep as one spec with two internal vertical increments |

### Success Criteria Summary

- [x] `migrate-structure.sh --dry-run` prints ordered pending migrations and mutates nothing, including on dirty trees.
- [x] `migrate-structure.sh --apply` hard-fails on dirty trees before backup or mutation, applies idempotent Tier-1 repo edits, writes `.specify/structure-version.json` with `{"structureVersion":1}`, and drives Tier-0 navigation backfill.
- [x] Tier-0 backfill reuses or composes with `generate-spec-index.sh` to emit roadmap-MOC rows for completed/archived ID-normalizable specs without stamping or moving legacy spec files.
- [x] In-flight specs from `.specify/feature.json` are skipped in every tier and reported as frozen/in-flight in dry-run output.
- [x] `relocate-process-artifacts.sh` supports real read-only `--dry-run` including on dirty trees, `--apply` with forced backup and clean-tree guard before mutation, idempotent re-run, `git mv`, link/index regeneration, and `structureVersion: 1` stamping only for Tier-2 thawed specs.
- [x] PROCESS relocation allow-list includes `retrospective.md`, `*-report.md`, `uat-*`, `pr-review-packet.md`, legacy `peer-review-*`, `cleanup-report.md`, `analysis.md`, `evidence/`, `verification-evidence.md` normalized into `evidence/verification-evidence.md`, `design-concept.md`, `*-design-concept.md`, `workflow.md`, and `*-workflow.md`.
- [x] CONTRACT artifacts stay visible: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/**`, `checklists/**`, and `SPEC-MOC.md`.
- [x] `speckit-upgrade` exposes the Tier-1/Tier-0 migration behavior; `speckit-scaffold-spec` and `speckit-autopilot` suggest, but never auto-run, the Tier-2 codemod when a thawed legacy spec has relocatable PROCESS files.
- [x] Tests cover Layer 1, Layer 3, Layer 4 dry-run/idempotency/move-set/ID-normalization fixtures, and Layer 8 Codex parity.

---

## Phase 1: Specify

**When to run:** Start here. Focus on what the migration must guarantee, not implementation internals. Output: `specs/prsg-011-retro-migration/spec.md`.

### Specify Prompt

```bash
/speckit-specify

## Feature: Retro-migration - version marker and state-keyed backfill/relocate

### Problem Statement
PRSG-001 through PRSG-010 are new-specs-only. Existing projects would otherwise keep
legacy spec layouts forever, creating split-brain behavior: new specs carry MOC
markers and `.process` exhaust, while historical specs either remain invisible to the
roadmap-MOC spine or stay exempt from version-gated lints. Add a deterministic,
operator-safe migration path that upgrades repository structure without mass-stamping
or moving legacy specs unless the operator explicitly thaws a spec.

### Users
- Maintainers upgrading existing SpecKit projects with historical specs.
- Reviewers who need legacy specs navigable without noisy process artifacts in future
  PRs.
- Autopilot/scaffold operators who need an explicit codemod suggestion when they thaw
  a legacy spec.

### User Stories
- [US1] As an upgrader, I can run `migrate-structure.sh --dry-run` to see ordered
  pending structure migrations without mutations, then `--apply` on a clean tree to
  create `.specify/structure-version.json`, apply Tier-1 repo edits, and perform
  Tier-0 navigation backfill.
- [US2] As an upgrader of a thawed legacy spec, I can run
  `relocate-process-artifacts.sh --dry-run` and `--apply` to move only PROCESS
  artifacts into `.process/`, stamp the spec MOC with `structureVersion: 1`, regenerate
  links/index, and recover from the forced backup.
- [US3] As a scaffold/autopilot operator, I see an explicit suggested next action for
  the Tier-2 codemod when a thawed legacy spec has relocatable PROCESS files, but the
  flow never auto-runs the codemod.

### Constraints
- Use plain bash + jq only.
- Keep deterministic logic in scripts, not agents or LLM reasoning.
- Allow dirty-tree dry-run only when it is read-only; hard-fail all mutation paths on
  dirty trees before backup or file changes.
- Skip in-flight specs listed in `.specify/feature.json` in every tier.
- Do not stamp or move completed historical specs during Tier-0.
- Canonical marker value for the first migration is `structureVersion` 1.
- Canonical review packet filename is `pr-review-packet.md`; recognize legacy
  `peer-review-*`.
- Canonical evidence shape is `evidence/`; normalize `verification-evidence.md` into
  `evidence/verification-evidence.md` during Tier-2.
- Keep this as one spec with two ordered internal vertical increments:
  1. Tier-1/Tier-0 `migrate-structure.sh`.
  2. Tier-2 `relocate-process-artifacts.sh` plus scaffold/autopilot registration.

### Out of Scope
- Non-SpecKit/date-named legacy namespaces in v1.
- Auto-running Tier-2 from scaffold/autopilot.
- History rewrite or cleanup outside the explicit PROCESS allow-list.
- Splitting this roadmap entry into PRSG-011A/PRSG-011B unless implementation proves
  the accepted warning budget unworkable.
```

### Specify Results

Fill in after running the command:

| Metric | Value |
|--------|-------|
| Functional Requirements | 32 |
| User Stories | US1, US2, US3 |
| Acceptance Criteria | 12 acceptance scenarios; 7 measurable success criteria |

### Files Generated

- [x] `specs/prsg-011-retro-migration/spec.md`
- [x] `specs/prsg-011-retro-migration/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** Run only if Specify leaves markers or if these implementation mechanics remain ambiguous. Maximum 5 targeted questions per session.

### Clarify Prompts

#### Session 1: Migration CLI and backup model

```bash
/speckit-clarify Focus on the migration CLI: exact arguments for migrate-structure.sh and relocate-process-artifacts.sh, backup location/naming, dry-run output schema, apply behavior, dirty-tree detection, and recovery instructions.
```

#### Session 2: ID normalization and Tier-0 backfill

```bash
/speckit-clarify Focus on ID normalization and Tier-0 backfill: how to reuse speckit-pro/skills/speckit-autopilot/scripts/lib/moc-id-normalize.sh and generate-spec-index.sh, how completed/archived historical specs are discovered, and how in-flight specs from .specify/feature.json are skipped with clear dry-run reasons.
```

#### Session 3: Tier-2 allow-list and registration

```bash
/speckit-clarify Focus on Tier-2 relocation: exact PROCESS allow-list, verification-evidence.md normalization into evidence/verification-evidence.md, CONTRACT path protections, link/index regeneration, SPEC-MOC structureVersion stamping, and how speckit-scaffold-spec plus speckit-autopilot suggest but do not auto-run the codemod.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Migration CLI and backup model | 5 | Resolved exact script invocation contracts, JSON report shape, outside-repo backup path, porcelain dirty-tree detection, and dirty-tree-safe Tier-2 dry-run |
| 2 | ID normalization and Tier-0 backfill | 5 | Resolved Tier-0 link targets, active/archive discovery sources, repo-marker-gated generator behavior, strict `.specify/feature.json` parsing, and direct reuse of `moc-id-normalize.sh` |
| 3 | Tier-2 allow-list and registration | 5 | Resolved dual-anchor relocation, root-only allow-list matching with CONTRACT precedence, evidence collision handling, existing-MOC stamping/generator delegation, and static suggestion-only scaffold/autopilot behavior |

### Consensus Resolution Log

| Phase | Item | Round | Routed Categories | Outcome | Analysts Used |
|-------|------|-------|-------------------|---------|---------------|
| Clarify Session 1 | Tier-2 dry-run dirty-tree behavior | 1 | spec | Allow read-only dirty-tree dry-run; clean-tree guard applies to `--apply` before backup or mutation | spec-context-analyst |
| Clarify Session 2 | Tier-0 link targets for no-MOC or archive-memory specs | 1 | codebase, spec | Use home-note-relative target matrix: gated `SPEC-MOC.md`, legacy `spec.md`, archive memory section; skip and report when no durable target resolves | codebase-analyst, spec-context-analyst |
| Clarify Session 2 | Tier-0 durability after `structureVersion` 1 | 1 | codebase, spec | Extend `generate-spec-index.sh` with repo-marker-gated legacy-row discovery; `migrate-structure.sh` creates or advances the marker and delegates generation; pre-marker behavior continues to skip legacy/non-version-marked specs | codebase-analyst, spec-context-analyst |
| Clarify Session 2 | `.specify/feature.json` parse/match for frozen skips | 1 | codebase, spec | Missing file means no active frozen target; present invalid state is reported in dry-run and blocks every mutating mode; valid `feature_directory` canonicalizes under repo root and freezes candidates by exact path or existing namespace-aware `moc_id_match` only | codebase-analyst, spec-context-analyst |
| Clarify Session 3 | Tier-2 design-concept/workflow anchor scope | 1 | codebase, spec | Use dual-anchor relocation: spec-root PROCESS files move under `<spec-dir>/.process/`; matching scaffold-time `docs/ai/specs/<SPEC-ID>-design-concept.md` and `<SPEC-ID>-workflow.md` move under `docs/ai/specs/.process/`; unrelated docs files do not move | codebase-analyst, spec-context-analyst |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/prsg-011-retro-migration/plan.md`.

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Runtime: shell scripts, bash 3.2 compatible where existing scripts require it.
- JSON: jq only; no sed/awk JSON parsing.
- Plugin docs: Markdown SKILL.md files under both skills/ and codex-skills/ where mirrors exist.
- Existing helpers: inspect and reuse `speckit-pro/skills/speckit-autopilot/scripts/lib/moc-id-normalize.sh`, `moc-frontmatter.sh`, and `generate-spec-index.sh` before adding any helper.
- Tests: shell-based Layer 1/4 default suite, Layer 3 functional evals for skill behavior, Layer 8 Codex parity for mirrored skill changes.

## Grounded Implementation Map
- `speckit-pro/skills/speckit-upgrade/SKILL.md` and `speckit-pro/codex-skills/speckit-upgrade/SKILL.md`: add migration-runner behavior or operator handoff for Tier-1/Tier-0; preserve backup/restore language.
- New deterministic scripts: `migrate-structure.sh`, `relocate-process-artifacts.sh`, and any shared ID-normalization wrapper only if existing `moc-id-normalize.sh` is insufficient.
- `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`: reuse for generated index zones; do not duplicate whole-zone regen logic.
- `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` plus Codex mirror: add explicit suggested next action for thawed legacy specs with relocatable PROCESS files; never auto-run.
- `speckit-pro/skills/speckit-autopilot/SKILL.md` plus Codex mirror and relevant phase references: same suggested next action behavior; never invoke the codemod autonomously.
- Tests: add L4 fixtures for dry-run no-mutation, apply dirty-tree block, idempotency, move-set allow-list, dual-anchor design/workflow relocation, evidence normalization, in-flight skip, and ID normalization. Add L3 skill behavior fixtures and L8 parity checks when mirrored skill prose changes.

## Constraints
- `migrate-structure.sh --dry-run`: read-only and allowed on dirty trees.
- `migrate-structure.sh --apply`: clean tree required before backup/mutation.
- `relocate-process-artifacts.sh --dry-run`: read-only and allowed on dirty trees; it reports proposed git moves, target-path collisions, protected CONTRACT artifacts, generated-link/index updates, stamp decisions, and backup path without changing files.
- `relocate-process-artifacts.sh --apply`: clean tree required before backup/mutation because Tier-2 performs git moves, target-path changes, stamps, and generated-link/index updates.
- Every apply path creates a forced, non-skippable backup before mutation and prints the backup path.
- Tier-0 touches only generated navigation zones; no file moves and no frontmatter stamps.
- Tier-2 moves only PROCESS allow-list files; CONTRACT files remain in place.
- In-flight specs from `.specify/feature.json` are skipped in every tier.
- Reviewability warning accepted by Grill Me Q11: keep as one spec with two internal vertical increments and record the split decision in plan.md.

## Architecture Notes
- Treat `.specify/structure-version.json` as a repo-level high-water marker:
  `{"structureVersion":1}` for the first migration; future migrations are 2+.
- Treat SPEC-MOC `structureVersion: 1` as the per-spec version-gate carrier already used by lints and templates.
- Keep script output deterministic enough for byte-stable fixtures. Use compact JSON reports for dry-run and apply output, documented in contracts/tests.
- Do not parse `.gitattributes` from reviewability logic; PRSG-001 already decided the gate keeps its hardcoded `.process/` glob.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Uses speckit-pro-reviewability fields, declared file operations, accepted warning budget, and two-increment split decision |
| `research.md` | Complete | Resolves helper reuse, repo-marker gating, compact JSON reports, backup ordering, dual anchors, and static suggestions |
| `data-model.md` | Complete | Covers structure markers, active-feature state, migration tiers, artifact classification, move operations, backup plans, reports, and suggestions |
| `contracts/` | Complete | 3 contracts: shared JSON report, repository migration CLI, Tier-2 relocation CLI |
| `quickstart.md` | Complete | Operator dry-run/apply flows, recovery note, and focused verification commands |

---

## Phase 4: Domain Checklists

**Target domains:** data-integrity, error-handling, backward-compatibility, and developer-experience.

### Recommended domains

| Signal in this spec | Domain |
|---|---|
| Migration must never move/stamp the wrong legacy files | data-integrity |
| Dirty-tree, backup, idempotency, and recovery behavior are central | error-handling |
| Legacy specs are grandfathered; in-flight specs are frozen | backward-compatibility |
| Operators need clear dry-run/apply instructions and scaffold/autopilot suggestions | developer-experience |

### Checklist Prompts

#### 1. data-integrity Checklist

```bash
/speckit-checklist data-integrity

Focus on PRSG-011 migration requirements:
- Tier-0 must not stamp or move historical specs.
- Tier-2 must move only PROCESS allow-list files into .process/.
- CONTRACT files stay in place: spec.md, plan.md, tasks.md, research.md, data-model.md, quickstart.md, contracts/**, checklists/**, SPEC-MOC.md.
- ID normalization must avoid false joins such as PRSG-013A vs PRSG-013A1.
- Pay special attention to evidence normalization and legacy peer-review-* recognition.
```

#### 2. error-handling Checklist

```bash
/speckit-checklist error-handling

Focus on PRSG-011 migration requirements:
- Dry-run and apply modes are clearly separated.
- Apply paths hard-fail on dirty trees before backup or mutation.
- Backup is forced and non-skippable before any mutation.
- Re-running apply after a completed migration is idempotent.
- Pay special attention to partial failure recovery instructions and backup path reporting.
```

#### 3. backward-compatibility Checklist

```bash
/speckit-checklist backward-compatibility

Focus on PRSG-011 migration requirements:
- Legacy specs without markers remain exempt by absence.
- Completed/archived historical specs become navigable without mass file moves.
- In-flight specs from .specify/feature.json are skipped in every tier.
- Non-SpecKit/date-named legacy namespaces stay out of scope.
- Pay special attention to existing MOC lints and generate-spec-index.sh behavior.
```

#### 4. developer-experience Checklist

```bash
/speckit-checklist developer-experience

Focus on PRSG-011 migration requirements:
- Dry-run output clearly lists pending migrations, skipped frozen specs, and no-op states.
- Apply output prints what changed and where the backup lives.
- speckit-upgrade, scaffold-spec, and autopilot wording tells operators the exact safe next command.
- Scaffold/autopilot suggestions are explicit but never auto-run Tier-2.
- Pay special attention to Codex and Claude skill parity.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| data-integrity | 22 | 4 found, 0 remaining | Canonicalized evidence/review packet relocation into `.process/`, added collision/no-overwrite rules, and verified no remaining markers |
| error-handling | 22 | 4 found, 0 remaining | Generalized forced backups across apply modes, clarified idempotent no-op reruns, and added post-backup failure statuses/recovery |
| backward-compatibility | 23 | 1 found, 0 remaining | Added deterministic out-of-scope handling for non-SpecKit/date-named namespaces and preserved marker-absence behavior |
| developer-experience | 24 | 2 found, 0 remaining | Added exact `speckit-upgrade` migration sequence and explicit Claude/Codex parity requirements |

---

## Phase 5: Tasks

**When to run:** After checklists complete. Output: `specs/prsg-011-retro-migration/tasks.md`.

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Organize by user story and by the two internal vertical increments, not by horizontal layer.
- TDD first for deterministic scripts: write Layer 4 fixtures before implementation.
- Mirror every changed `skills/*/SKILL.md` into the matching `codex-skills/*/SKILL.md` in the same story.
- Mark [P] only when files do not conflict.

## Required Implementation Order
1. Foundation: script contracts/fixtures, ID-normalization reuse decision, and reviewability checkpoint.
2. Internal increment 1: Tier-1/Tier-0 `migrate-structure.sh`.
   - RED: dry-run no-mutation, dirty-tree apply block, marker write, idempotency, in-flight skip, generated-index backfill fixtures.
   - GREEN: implement the runner and wire `speckit-upgrade`/Codex wording.
3. Internal increment 2: Tier-2 `relocate-process-artifacts.sh` plus registration.
   - RED: move-set allow-list, CONTRACT protection, evidence normalization, design-concept/workflow relocation, backup/dirty-tree/idempotency fixtures.
   - GREEN: implement codemod and scaffold/autopilot suggestion wording in both runtime variants.
4. Polish: Layer 1/4 default suite, affected L3 functional eval fixtures, Layer 8 parity, quickstart/operator documentation.

## Constraints
- Do not auto-run Tier-2 from scaffold/autopilot.
- Do not stamp or move legacy completed specs during Tier-0.
- Do not mutate in-flight specs in any tier.
- Do not add an agent for deterministic migration logic.
- Preserve PRSG-011 as one spec unless the implementation phase produces a new ratified split decision.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | 34 |
| Phases | Setup/reviewability, foundational RED contracts, US1 Tier-1/Tier-0, US2 Tier-2 relocation, US3 suggestion-only registration, polish |
| Parallel Opportunities | 6 `[P]` tasks |
| User Stories Covered | US1, US2, US3 |

**Reviewability Checkpoint:** `reviewability-gate.sh tasks specs/prsg-011-retro-migration` returned `status=exception`, `pass=true`, `exception_class=upgrade`. Warnings/blockers are accepted under the explicit upgrade exception and two internal vertical increments remain preserved.

---

## Phase 6: Analyze

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Design-concept consistency: Q1-Q11 decisions must appear in spec.md, plan.md, and tasks.md.
2. Coverage: every success criterion and user story has tasks and tests.
3. Migration safety: dirty-tree, backup, dry-run/apply separation, idempotency, and recovery are complete.
4. Data integrity: PROCESS allow-list cannot move CONTRACT files; evidence normalization and review-packet dual recognition are covered.
5. Backward compatibility: legacy marker-absence exemption and in-flight frozen skip are preserved.
6. Codex parity: every mirrored skill behavior/prose change has a paired Codex update and Layer 8 coverage.
7. Reviewability: accepted warning remains bounded to two internal vertical increments.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| A1 | HIGH | Q1 default decisions were not fully explicit across spec, plan, and tasks | Added FR-030 through FR-032 plus plan/task coverage for one-row-per-file legacy rows, no `.gitattributes` parser in reviewability logic, and live-roadmap de-boilerplate |
| A2 | MEDIUM | PRSG-001 deferred scaffold artifact fixture coverage was implicit | Added deterministic PRSG-001 deferred scaffold artifact fixture coverage to plan/tasks |

**Analyze Verification:** G6 passed with 0 CRITICAL/HIGH findings after remediation. Layer 1 remained green at 887/887.

📊 Confidence: 0.94

- Task understanding: 0.96
- Approach clarity: 0.94
- Requirements alignment: 0.93
- Risk assessment: 0.95
- Completeness: 0.93

---

## Phase 7: Implement

### Implement Prompt

```bash
/speckit-implement

## Approach: TDD-first
For each deterministic script behavior:
1. RED: write or extend the Layer 4 fixture and confirm it fails.
2. GREEN: implement the smallest bash+jq behavior that passes.
3. REFACTOR: keep scripts readable and bash-3.2-compatible where existing helpers are.
4. VERIFY: run targeted Layer 4 tests, then Layer 1, then default run-all.

## Implementation Notes
- Start with `git status --short --branch` and confirm branch `prsg-011-retro-migration`.
- Reuse existing helper style under `speckit-pro/skills/speckit-autopilot/scripts/`.
- Keep skill docs explicit: Codex skills use `$skill-name`; Claude skills use `/speckit-pro:<skill>`.
- Record backup paths and dry-run examples in quickstart/operator docs.
- Do not merge or push main; implementation happens on this spec branch only.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Foundation | T001-T003 | Complete | RED scaffold tests created; reviewability gate still `exception/pass` under upgrade exception |
| Tier-1/Tier-0 | T001-T013 | Complete | `migrate-structure.sh` implemented with marker-gated generator delegation; `test-migrate-structure.sh` 69/69 passed and `test-generate-spec-index.sh` 76/76 passed |
| Tier-2/register | T014-T027 | Complete | `relocate-process-artifacts.sh` implemented; `test-relocate-process-artifacts.sh` 104/104 passed; Layer 3 Claude/Codex scaffold and autopilot fixtures cover Tier-2 suggestions/suppression; Claude and Codex guidance now expose exact FR-026 commands, skip/no-op reasons, and no-auto-run guarantees |
| Polish | T028-T034 | Complete | Layer 8 fixture added and auto-discovered; Layer 1, Layer 4, default suite, affected Layer 3 helpers, and Layer 8 dry-run recorded |

---

## Post-Implementation Checklist

- [x] `bash tests/speckit-pro/run-all.sh --layer 1`
- [x] `bash tests/speckit-pro/run-all.sh --layer 4`
- [x] `bash tests/speckit-pro/run-all.sh`
- [x] Affected Layer 3 functional evals recorded
- [x] Layer 8 parity run recorded for mirrored Codex skill changes
- [x] `migrate-structure.sh --dry-run` fixture proves no mutation
- [x] `relocate-process-artifacts.sh` fixture proves allow-list, backup, idempotency, and CONTRACT protection
- [x] PR body documents review order, scope budget, traceability, verification, known gaps, and rollback

---

## Verification Evidence

| Command | Result | Notes |
|---------|--------|-------|
| `bash tests/speckit-pro/run-all.sh --layer 1` | 887/887 passed | Includes plugin payload, `.process` gitattributes, MOC lint, Codex structural, and Codex parity checks |
| `bash tests/speckit-pro/run-all.sh --layer 4` | 881/881 passed | Includes reviewability gate, migration/index helpers, Layer 8 extractor/judge helpers, and script unit tests |
| `bash tests/speckit-pro/run-all.sh` | 1958/1958 passed | Default deterministic suite: Layer 1, Layer 4, and Layer 5 |
| `bash tests/speckit-pro/layer3-functional/run-functional-evals.sh speckit-scaffold-spec` | 1 eval discovered | Claude scaffold Tier-2 suggestion fixture |
| `bash tests/speckit-pro/layer3-functional/run-functional-evals.sh speckit-autopilot` | 23 evals discovered | Claude autopilot Tier-2 suggestion fixture included |
| `bash tests/speckit-pro/layer3-functional/run-functional-evals-codex.sh speckit-scaffold-spec` | 8 evals discovered | Codex scaffold Tier-2 suggestion fixture included |
| `bash tests/speckit-pro/layer3-functional/run-functional-evals-codex.sh speckit-autopilot` | 29 evals discovered | Codex autopilot Tier-2 suggestion fixture included |
| `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run` | 6 passed, 0 failed, 0 skipped | Fixture 02 auto-discovered; live Layer 8 not run because it is opt-in and token-costly |
| `git diff --check origin/main` | Passed | Working-tree diff is whitespace-clean after Layer 8 EOF cleanup |

## Post-Implementation Results

| Item | Status | Evidence |
|------|--------|----------|
| Doctor Extension Check | Completed with local Codex fallback | `.specify/templates` has 6 non-empty templates; `.claude/commands` has 9 speckit command docs; no non-executable `.specify/scripts/bash/*.sh`; constitution is present. `.codex/commands` is absent in this worktree, so no Codex extension command was directly invocable. |
| Verify Implementation | Completed | Verification evidence table above; default deterministic suite passed 1958/1958. |
| Verify Tasks Phantom Check | Completed | `rg -n "^- \[ \]" specs/prsg-011-retro-migration/tasks.md` found no unchecked tasks; task file maps all FR groups to completed task ranges. |
| Code Review | Completed with parent fallback | Review extension was not installed. Parent review found no blocking code issues; fresh whitespace check initially found six Layer 8 trailing blank-line errors, now fixed in the working tree. |
| Integration Suite | Completed | `bash tests/speckit-pro/run-all.sh` passed 1958/1958. |
| Cleanup | Skipped | Cleanup extension was not installed during preflight; no cleanup command is available in this Codex surface. |
| Reviewability Diff Gate | Completed | `reviewability-gate.sh diff origin/main...HEAD` returned `status=exception`, `pass=true`, `exception_class=upgrade`, 57 files, 0 reviewable LOC, and the ratified upgrade exception. |
| Self-Review | Completed | See `## Self-Review` below. |
| UAT Runbook Generation | Completed | `generate-uat-skeleton.sh` wrote `specs/prsg-011-retro-migration/.process/uat-runbook.md`; `uat-runbook-author` is not registered in this Codex session, so the parent rewrote the runbook into concrete acceptance commands and expected results. |
| PR Body Generation | Completed | Generated with `generate-pr-body.sh` to `/private/tmp/prsg-011-speckit-pr-body.md` because this checkout is a linked worktree where `.git` is a file. Verified `speckit-pro-review-packet-source` marker and `## UAT Runbook` heading are present, then replaced only the top plain-English sections. |
| PR Creation | Completed | Draft PR #132 opened: https://github.com/racecraft-lab/racecraft-plugins-public/pull/132 |
| Review Remediation | Completed | Initial PR poll found no comments and no reviews. `validate-plugins` passed, PR matrix jobs were skipped, and CodeQL was still pending; no actionable remediation was available. |
| Retrospective | Completed with parent fallback | Retrospective extension command was not callable in this Codex surface, so the parent wrote `specs/prsg-011-retro-migration/.process/retrospective.md`. |

## Self-Review

1. **Tests executed?** Build/typecheck/lint are N/A for this plugin marketplace repo. The required test commands did run and exit zero: Layer 1 887/887, Layer 4 881/881, default suite 1958/1958, affected Layer 3 discovery checks, Layer 8 dry-run 6 passed, and `git diff --check origin/main` passed on 2026-06-09T03:24:16Z after the EOF cleanup.
2. **Edge cases?** Covered. Repository migration non-happy paths are in `tests/speckit-pro/layer4-scripts/test-migrate-structure.sh:312` through schema/dry-run checks, `:405` through dirty-tree apply blocking, and `:473` through marker/backfill assertions. Tier-2 relocation non-happy paths are in `tests/speckit-pro/layer4-scripts/test-relocate-process-artifacts.sh:162` through schema checks, `:217` through evidence normalization, `:245` through already-normalized no-op, `:469` through collision handling, `:496` through frozen/out-of-scope coverage, and `:572` through dirty-tree blocking. Suggestion-only behavior is covered by Layer 3 Claude/Codex fixtures and Layer 8 fixture `02-prsg-011-migration-guidance`.
3. **Requirements matched?** Covered. `specs/prsg-011-retro-migration/tasks.md` maps US1 to FR-001 through FR-009, FR-021 through FR-024, FR-027 through FR-032; US2 to FR-010 through FR-018, FR-021, FR-022, FR-025, FR-027; US3 to FR-019, FR-020, FR-026, FR-027, FR-029; and polish to verification and PR evidence. All T001-T034 rows are checked and implementation evidence is committed through `1d6b151`.
4. **Follow-up?** No silent follow-up markers found. `rg -n "\[TODO\]|\[DEFERRED\]|\[OUT-OF-SCOPE\]|TODO|DEFERRED|OUT-OF-SCOPE" specs/prsg-011-retro-migration docs/ai/specs/.process/PRSG-011-workflow.md` returned no matches.

## PR Review Packet Draft

**Review order**:
1. `speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh`
2. `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh`
3. `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`
4. Claude and Codex skill guidance plus dist payload mirrors
5. Layer 4, Layer 3, and Layer 8 fixtures
6. Spec/quickstart/workflow evidence updates

**Scope budget**: Reviewability warning accepted. Primary surface remains
schema/migration; secondary surfaces are docs/process and harness/adapter. The
work stayed within the ratified one-spec migration scope and preserved the two
internal increments: Tier-1/Tier-0 first, then Tier-2/register.

**Traceability**:
- FR-001 through FR-009, FR-023, FR-024, FR-028, FR-030, FR-031, FR-032:
  repository migration script, marker-gated generator, upgrade guidance, and
  Layer 4 migration/index fixtures.
- FR-010 through FR-018, FR-025, FR-027: Tier-2 relocation script and Layer 4
  relocation fixtures for allow-list, CONTRACT protection, dual anchors,
  evidence normalization, backups, idempotency, frozen/in-flight, and
  out-of-scope skips.
- FR-019, FR-020, FR-026, FR-029: Layer 3 suggestion fixtures, scaffold/autopilot
  guidance mirrors, phase-execution references, dist payload rebuild, and Layer 8
  parity fixture 02.
- SC-001 through SC-008: covered by the verification evidence table above.

**Known gaps**:
- Layer 8 live mode was not run; only dry-run fixture structure and JSON were
  validated. Live mode is explicitly opt-in because it invokes `claude -p` twice
  per fixture and consumes LLM budget.
- No browser UAT applies; PRSG-011 is shell tooling and skill documentation.

**Rollback**:
- Plugin changes can be reverted by reverting the PR commits.
- Operator migration commands are explicit and not auto-run by scaffold/autopilot.
- If a maintainer uses an apply command in a downstream project, the JSON report
  names the forced backup path and restore hint for file-state recovery.

---

## Project Structure Reference

```text
speckit-pro/
  skills/
    speckit-upgrade/
    speckit-scaffold-spec/
    speckit-autopilot/
      scripts/
        generate-spec-index.sh
        lib/moc-id-normalize.sh
        lib/moc-frontmatter.sh
  codex-skills/
    speckit-upgrade/
    speckit-scaffold-spec/
    speckit-autopilot/
tests/speckit-pro/
  layer1-structural/
  layer3-functional/
  layer4-scripts/
  layer8-parity/
specs/prsg-011-retro-migration/
  SPEC-MOC.md
```
