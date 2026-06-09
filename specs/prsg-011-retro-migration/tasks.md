# Tasks: Retro-migration - Version Marker and State-Keyed Backfill/Relocate

**Input**: Design documents from `/specs/prsg-011-retro-migration/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required. PRSG-011 changes deterministic shell scripts, generated navigation, skill guidance, and Claude Code/Codex parity, so RED fixtures come before implementation.

**Reviewability**: Warning accepted in plan.md. Implementation must preserve the two ordered internal vertical increments: first Tier-1/Tier-0 repository migration, then Tier-2 relocation plus scaffold/autopilot registration. Run the explicit reviewability checkpoint before implementation and stop for a ratified split if the scope grows past the accepted budget.

Reviewability-Exception: upgrade

**Organization**: Tasks are grouped by setup/foundation and then by user story. User-story phases preserve the two vertical increments rather than grouping by horizontal layer.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because file ownership does not conflict
- **[Story]**: Which user story this task belongs to
- Include exact file paths in every task description

## Phase 1: Setup and Reviewability

**Purpose**: Establish script fixture contracts, helper reuse expectations, and reviewability checkpoint before implementation.

- [x] T001 [P] Create RED repository migration fixture scaffold covering helper reuse of `moc-id-normalize.sh` and `moc-frontmatter.sh` in `tests/speckit-pro/layer4-scripts/test-migrate-structure.sh`
- [x] T002 [P] Create RED Tier-2 relocation fixture scaffold covering shared JSON-report and backup override contracts in `tests/speckit-pro/layer4-scripts/test-relocate-process-artifacts.sh`
- [x] T003 Run `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh tasks specs/prsg-011-retro-migration` and record the pre-implementation checkpoint in `docs/ai/specs/.process/PRSG-011-workflow.md`

---

## Phase 2: Foundational Test Contracts

**Purpose**: Complete deterministic RED coverage that blocks both implementation increments.

- [x] T004 Add RED dry-run no-mutation, dirty-tree apply block, active-feature invalid, and frozen/in-flight fixtures in `tests/speckit-pro/layer4-scripts/test-migrate-structure.sh`
- [x] T005 Add RED marker write, current no-op, idempotency, generated-index backfill, one-row-per-file multi-ID/gappy legacy inputs, archive-memory target, out-of-scope namespace, live-project roadmap de-boilerplate, `.gitattributes`/reviewability-gate separation, and false-join fixtures in `tests/speckit-pro/layer4-scripts/test-migrate-structure.sh`
- [x] T006 Add RED PROCESS allow-list, CONTRACT protection, already-normalized no-op, missing MOC, and target collision fixtures in `tests/speckit-pro/layer4-scripts/test-relocate-process-artifacts.sh`
- [x] T007 Add RED evidence normalization, review-packet canonicalization, docs-side design/workflow relocation including deterministic PRSG-001 deferred scaffold artifact cases, dirty-tree apply block, frozen/in-flight, out-of-scope, and idempotency fixtures in `tests/speckit-pro/layer4-scripts/test-relocate-process-artifacts.sh`

**Checkpoint**: Layer 4 fixtures fail for missing PRSG-011 implementation before user story work begins.

---

## Phase 3: User Story 1 - Run Repository Structure Migration Safely (Priority: P1) - MVP

**Goal**: Maintainers can preview and apply the repository-level structure migration safely, with a repo marker and Tier-0 navigation backfill through the existing generator.

**Independent Test**: In a fixture repository, `migrate-structure.sh --dry-run` reports pending work without mutations, `--apply` blocks on dirty trees, clean apply writes the marker and regenerates navigation, and reruns report no-op.

### Implementation for User Story 1

- [x] T008 [US1] Implement `migrate-structure.sh` mode parsing, repo-root resolution, active-feature tri-state parsing, dirty-tree reporting, and compact JSON envelope in `speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh`
- [x] T009 [US1] Implement marker detection, no-op detection, forced backup planning/creation, marker write, failure status, and recovery fields in `speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh`
- [x] T010 [US1] Update marker-gated legacy roadmap-row discovery, one-row-per-file handling for multi-ID/gappy legacy inputs, durable target selection, out-of-scope namespace reporting, in-flight skip handling, no `.gitattributes` parser changes to reviewability logic, and helper reuse in `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`
- [x] T011 [US1] Wire `migrate-structure.sh` to delegate generated-zone updates through `generate-spec-index.sh` without maintaining a second INDEX renderer in `speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh`
- [x] T012 [US1] Add repository migration dry-run/apply guidance, backup/restore wording, and no Tier-2 auto-run guarantee in `speckit-pro/skills/speckit-upgrade/SKILL.md`
- [x] T013 [US1] Mirror repository migration guidance and no Tier-2 auto-run guarantee in `speckit-pro/codex-skills/speckit-upgrade/SKILL.md`

**Checkpoint**: User Story 1 is complete when the repository migration fixtures pass and upgrade guidance exposes the exact FR-028 command sequence on both runtime surfaces.

---

## Phase 4: User Story 2 - Relocate PROCESS Artifacts for a Thawed Legacy Spec (Priority: P2)

**Goal**: Maintainers can preview and apply explicit Tier-2 PROCESS relocation for one thawed legacy spec while CONTRACT artifacts remain visible and recoverable.

**Independent Test**: In a legacy spec fixture, `relocate-process-artifacts.sh --dry-run` reports moves/protections/collisions without mutations, clean apply creates a backup, relocates only allowed PROCESS artifacts, stamps the MOC, normalizes evidence, regenerates links, and reruns no-op.

### Implementation for User Story 2

- [x] T014 [US2] Implement `relocate-process-artifacts.sh` mode parsing, required `--spec`, repo/spec path resolution, active-feature handling, candidate eligibility, and compact JSON envelope in `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh`
- [x] T015 [US2] Implement PROCESS allow-list discovery, CONTRACT protection, already-normalized no-op reporting, missing/non-regular MOC block, and deterministic move-set sorting in `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh`
- [x] T016 [US2] Implement evidence normalization, review-packet canonicalization, collision detection, and dual PROCESS anchors for matching docs-side design/workflow files including PRSG-001 deferred scaffold artifact cases in `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh`
- [x] T017 [US2] Implement apply clean-tree block, forced backup, `git mv` moves, `SPEC-MOC.md` `structureVersion: 1` stamp, generator delegation, idempotent no-op, and post-backup recovery statuses in `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh`

**Checkpoint**: User Story 2 is complete when relocation fixtures pass and the script never mutates dirty, in-flight, out-of-scope, missing-MOC, or collision states.

---

## Phase 5: User Story 3 - Suggest Tier-2 Codemod Without Auto-Running It (Priority: P3)

**Goal**: Scaffold and autopilot surfaces statically suggest the exact Tier-2 dry-run/apply sequence for eligible thawed legacy specs without executing either command.

**Independent Test**: Layer 3 fixtures for thawed, frozen/in-flight, already-current, no-candidate, and out-of-scope cases show the correct suggestion or suppression text and no codemod side effects on Claude Code and Codex surfaces.

### Tests for User Story 3

- [x] T018 [P] [US3] Add Claude scaffold Tier-2 suggestion fixture coverage in `tests/speckit-pro/layer3-functional/evals/speckit-scaffold-spec-evals.json`
- [x] T019 [P] [US3] Add Claude autopilot Tier-2 suggestion fixture coverage in `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json`
- [x] T020 [P] [US3] Add Codex scaffold Tier-2 suggestion fixture coverage in `tests/speckit-pro/layer3-functional/codex-evals/speckit-scaffold-spec-evals.json`
- [x] T021 [P] [US3] Add Codex autopilot Tier-2 suggestion fixture coverage in `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json`

### Implementation for User Story 3

- [x] T022 [US3] Add static Tier-2 relocation suggestion wording, skip/no-op cases, exact FR-026 commands, and no-auto-run guarantee in `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`
- [x] T023 [US3] Mirror static Tier-2 relocation suggestion wording, skip/no-op cases, exact FR-026 commands, and no-auto-run guarantee in `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`
- [x] T024 [US3] Add static Tier-2 relocation suggestion behavior, frozen/in-flight and out-of-scope suppression, exact FR-026 commands, and no-auto-run guarantee in `speckit-pro/skills/speckit-autopilot/SKILL.md`
- [x] T025 [US3] Mirror static Tier-2 relocation suggestion behavior, frozen/in-flight and out-of-scope suppression, exact FR-026 commands, and no-auto-run guarantee in `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`
- [x] T026 [US3] Update autopilot phase execution guidance for static Tier-2 suggestions and no automatic relocation in `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`
- [x] T027 [US3] Mirror autopilot phase execution guidance for static Tier-2 suggestions and no automatic relocation in `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`

**Checkpoint**: User Story 3 is complete when Layer 3 fixtures prove the suggestion-only behavior and Claude Code/Codex skill wording remains behavior-equivalent.

---

## Phase 6: Polish and Verification

**Purpose**: Prove default suites, affected functional fixtures, parity, and operator docs before implementation is marked complete.

- [x] T028 Add PRSG-011 Layer 8 parity fixture for mirrored repository migration guidance and Tier-2 suggestion guarantees under `tests/speckit-pro/layer8-parity/02-prsg-011-migration-guidance/`
- [x] T029 Register the PRSG-011 Layer 8 parity fixture in `tests/speckit-pro/layer8-parity/run-parity-fixtures.sh` if the runner does not auto-discover the new fixture directory
- [x] T030 Run Layer 1 structural validation, including `.process` `.gitattributes` structural guards, with `bash tests/speckit-pro/run-all.sh --layer 1` and record relevant output in `docs/ai/specs/.process/PRSG-011-workflow.md`
- [x] T031 Run Layer 4 script validation, including reviewability-gate `.process` exclusion regression coverage, with `bash tests/speckit-pro/run-all.sh --layer 4` and record relevant output in `docs/ai/specs/.process/PRSG-011-workflow.md`
- [x] T032 Run the default suite with `bash tests/speckit-pro/run-all.sh` and record relevant output in `docs/ai/specs/.process/PRSG-011-workflow.md`
- [x] T033 Update operator quickstart examples and final verification notes in `specs/prsg-011-retro-migration/quickstart.md`
- [x] T034 Prepare the PR review packet content with review order, scope budget, traceability, verification evidence, known gaps, and rollback notes in `docs/ai/specs/.process/PRSG-011-workflow.md`

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup and Reviewability (Phase 1)**: No dependencies.
- **Foundational Test Contracts (Phase 2)**: Depends on Phase 1 and blocks implementation.
- **User Story 1 (Phase 3)**: Depends on Phase 2. This is the MVP and first internal vertical increment.
- **User Story 2 (Phase 4)**: Depends on Phase 3 because Tier-2 depends on repo-marker and generator behavior.
- **User Story 3 (Phase 5)**: Depends on Phase 4 script contracts so suggestions name the implemented explicit codemod and suppression states.
- **Polish and Verification (Phase 6)**: Depends on desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: MVP. Must complete before Tier-2 relocation work.
- **US2 (P2)**: Depends on US1 generator/marker behavior and supplies the explicit relocation codemod.
- **US3 (P3)**: Depends on US2 command contract and must not execute the codemod automatically.

### Parallel Opportunities

- T001 and T002 can run in parallel because they create different Layer 4 test files.
- T018, T019, T020, and T021 can run in parallel because they update separate Layer 3 fixture files.
- No `[P]` markers are used inside US1 or US2 implementation because those tasks intentionally serialize edits to the same scripts/generator and preserve the two internal increments.

---

## Parallel Example: Foundation

```text
Task: "Create RED repository migration fixture scaffold in tests/speckit-pro/layer4-scripts/test-migrate-structure.sh"
Task: "Create RED Tier-2 relocation fixture scaffold in tests/speckit-pro/layer4-scripts/test-relocate-process-artifacts.sh"
```

## Parallel Example: User Story 3

```text
Task: "Add Claude scaffold fixture in tests/speckit-pro/layer3-functional/evals/speckit-scaffold-spec-evals.json"
Task: "Add Claude autopilot fixture in tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json"
Task: "Add Codex scaffold fixture in tests/speckit-pro/layer3-functional/codex-evals/speckit-scaffold-spec-evals.json"
Task: "Add Codex autopilot fixture in tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2 RED fixture work.
2. Complete Phase 3 for `migrate-structure.sh`, marker-gated `generate-spec-index.sh`, and upgrade guidance mirrors.
3. Stop and validate US1 independently with the repository migration Layer 4 fixtures.

### Incremental Delivery

1. Deliver US1 as the safe repository migration MVP.
2. Deliver US2 as explicit Tier-2 relocation for thawed legacy specs.
3. Deliver US3 as suggestion-only scaffold/autopilot discoverability.
4. Complete Layer 1, Layer 4, default suite, affected Layer 3 fixtures, Layer 8 parity, and quickstart/PR review documentation.

### Reviewability Guard

If implementation expands beyond the accepted warning budget or introduces another primary surface, stop before adding more production tasks and record a split/exception decision in `docs/ai/specs/.process/PRSG-011-workflow.md`.

---

## Requirement Coverage

- **US1 / T001-T005, T008-T013**: FR-001 through FR-009, FR-021 through FR-024, FR-027 through FR-032, SC-001 through SC-003, SC-007, SC-008.
- **US2 / T002, T006-T007, T014-T017**: FR-010 through FR-018, FR-021, FR-022, FR-025, FR-027, SC-001, SC-002, SC-004, SC-005, SC-007.
- **US3 / T018-T027**: FR-019, FR-020, FR-026, FR-027, FR-029, SC-006, SC-008.
- **Polish / T028-T034**: Reviewability budget, PR review packet requirements, Layer 1/4/default verification, affected Layer 3 fixtures, Layer 8 parity, and quickstart/operator documentation.
