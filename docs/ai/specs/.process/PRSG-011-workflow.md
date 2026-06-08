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
| Specify | `/speckit-specify` | Pending | |
| Clarify | `/speckit-clarify` | Pending | Use only if Specify leaves markers or the three focus areas below need narrowing |
| Plan | `/speckit-plan` | Pending | |
| Checklist | `/speckit-checklist` | Pending | Recommended: data-integrity, error-handling, backward-compatibility, developer-experience |
| Tasks | `/speckit-tasks` | Pending | Must preserve two internal vertical increments |
| Analyze | `/speckit-analyze` | Pending | |
| Implement | `/speckit-implement` | Pending | |

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

**Constitution Check:** Pending.

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

- [ ] `migrate-structure.sh --dry-run` prints ordered pending migrations and mutates nothing, including on dirty trees.
- [ ] `migrate-structure.sh --apply` hard-fails on dirty trees before backup or mutation, applies idempotent Tier-1 repo edits, writes `.specify/structure-version.json` with `{"structureVersion":1}`, and drives Tier-0 navigation backfill.
- [ ] Tier-0 backfill reuses or composes with `generate-spec-index.sh` to emit roadmap-MOC rows for completed/archived ID-normalizable specs without stamping or moving legacy spec files.
- [ ] In-flight specs from `.specify/feature.json` are skipped in every tier and reported as frozen/in-flight in dry-run output.
- [ ] `relocate-process-artifacts.sh` supports real `--dry-run` and `--apply`, forced backup, dirty-tree guard, idempotent re-run, `git mv`, link/index regeneration, and `structureVersion: 1` stamping only for Tier-2 thawed specs.
- [ ] PROCESS relocation allow-list includes `retrospective.md`, `*-report.md`, `uat-*`, `pr-review-packet.md`, legacy `peer-review-*`, `cleanup-report.md`, `analysis.md`, `evidence/`, `verification-evidence.md` normalized into `evidence/verification-evidence.md`, `design-concept.md`, `*-design-concept.md`, `workflow.md`, and `*-workflow.md`.
- [ ] CONTRACT artifacts stay visible: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/**`, `checklists/**`, and `SPEC-MOC.md`.
- [ ] `speckit-upgrade` exposes the Tier-1/Tier-0 migration behavior; `speckit-scaffold-spec` and `speckit-autopilot` suggest, but never auto-run, the Tier-2 codemod when a thawed legacy spec has relocatable PROCESS files.
- [ ] Tests cover Layer 1, Layer 3, Layer 4 dry-run/idempotency/move-set/ID-normalization fixtures, and Layer 8 Codex parity.

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
| Functional Requirements | Pending |
| User Stories | Expected: US1, US2, US3 |
| Acceptance Criteria | Pending |

### Files Generated

- [ ] `specs/prsg-011-retro-migration/spec.md`
- [ ] `specs/prsg-011-retro-migration/checklists/requirements.md`

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
| 1 | Migration CLI and backup model | Pending | |
| 2 | ID normalization and Tier-0 backfill | Pending | |
| 3 | Tier-2 allow-list and registration | Pending | |

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
- Tests: add L4 fixtures for dry-run no-mutation, apply dirty-tree block, idempotency, move-set allow-list, evidence normalization, in-flight skip, and ID normalization. Add L3 skill behavior fixtures and L8 parity checks when mirrored skill prose changes.

## Constraints
- `migrate-structure.sh --dry-run`: read-only and allowed on dirty trees.
- `migrate-structure.sh --apply`: clean tree required before backup/mutation.
- `relocate-process-artifacts.sh --dry-run` and `--apply`: clean tree required before backup/mutation because Tier-2 reasons about git moves and target paths.
- Every apply path creates a forced, non-skippable backup before mutation and prints the backup path.
- Tier-0 touches only generated navigation zones; no file moves and no frontmatter stamps.
- Tier-2 moves only PROCESS allow-list files; CONTRACT files remain in place.
- In-flight specs from `.specify/feature.json` are skipped in every tier.
- Reviewability warning accepted by Grill Me Q11: keep as one spec with two internal vertical increments and record the split decision in plan.md.

## Architecture Notes
- Treat `.specify/structure-version.json` as a repo-level high-water marker:
  `{"structureVersion":1}` for the first migration; future migrations are 2+.
- Treat SPEC-MOC `structureVersion: 1` as the per-spec version-gate carrier already used by lints and templates.
- Keep script output deterministic enough for byte-stable fixtures. Prefer compact JSON or stable plain text for dry-run output; whichever is chosen must be documented in contracts/tests.
- Do not parse `.gitattributes` from reviewability logic; PRSG-001 already decided the gate keeps its hardcoded `.process/` glob.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Pending | |
| `research.md` | Pending | Use only for unresolved implementation tradeoffs, not to re-litigate Grill Me decisions |
| `data-model.md` | Pending | Likely useful for migration tiers, marker state, and artifact classification |
| `contracts/` | Pending | Recommended for script CLIs and dry-run output |
| `quickstart.md` | Pending | Recommended for operator migration flow |

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
| data-integrity | Pending | Pending | |
| error-handling | Pending | Pending | |
| backward-compatibility | Pending | Pending | |
| developer-experience | Pending | Pending | |

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
| Total Tasks | Pending |
| Phases | Expected: foundation, Tier-1/Tier-0, Tier-2/register, polish |
| Parallel Opportunities | Pending |
| User Stories Covered | Expected: US1, US2, US3 |

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
| Pending | Pending | Pending | Pending |

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
| Foundation | Pending | Pending | |
| Tier-1/Tier-0 | Pending | Pending | |
| Tier-2/register | Pending | Pending | |
| Polish | Pending | Pending | |

---

## Post-Implementation Checklist

- [ ] `bash tests/speckit-pro/run-all.sh --layer 1`
- [ ] `bash tests/speckit-pro/run-all.sh --layer 4`
- [ ] `bash tests/speckit-pro/run-all.sh`
- [ ] Affected Layer 3 functional evals recorded
- [ ] Layer 8 parity run recorded for mirrored Codex skill changes
- [ ] `migrate-structure.sh --dry-run` fixture proves no mutation
- [ ] `relocate-process-artifacts.sh` fixture proves allow-list, backup, idempotency, and CONTRACT protection
- [ ] PR body documents review order, scope budget, traceability, verification, known gaps, and rollback

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
