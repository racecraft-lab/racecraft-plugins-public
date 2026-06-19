# Tasks: TACD-003 Prerequisite and Documentation Messaging

**Input**: Design documents from `specs/tacd-003-prerequisite-and-documentation-messaging/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `quickstart.md`, `checklists/`

**Tests**: Required for this slice. Use TDD for prerequisite script output changes: focused test or fixture first, prerequisite script update second, docs third, `bash -n` and focused validation last.

**Reviewability**: Keep the implementation inside the declared file operations in `plan.md`. Do not edit archives, hand-edit generated payloads, installers, marketplace integration, broad scanners, or evals; source-derived `dist/` regeneration is allowed when required by declared source changes. If the implementation must exceed the declared file set, stop and amend the plan before continuing.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches a different file and does not depend on final script output wording.
- **[Story]**: User story from `spec.md` (`US1`, `US2`, `US3`).
- Every implementation task includes exact file paths and traceability to AC-3.1 through AC-3.4 or the approved validation task mapping below. FR-001 through FR-014 and SC-001 through SC-008 references provide finer-grained coverage.

## Phase 1: Setup and Scope Guard

**Purpose**: Confirm the implementation boundary before editing source files.

- [x] T001 Review `specs/tacd-003-prerequisite-and-documentation-messaging/plan.md` declared file operations and confirm implementation remains limited to the planned script, focused Layer 4 test, and declared active guidance files. (FR-007, FR-009, FR-010, SC-005)
- [x] T002 Review `docs/ai/specs/.process/TACD-003-design-concept.md` Goals, Non-goals, and Q1-Q6 before editing so advisory wording stays capability-first, non-blocking, and within one slice. (AC-3.1, AC-3.2, AC-3.3, AC-3.4)
- [x] T003 Inspect `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh` and `tests/speckit-pro/layer4-scripts/test-check-prerequisites.sh` to identify the current optional-tool report and one existing true prerequisite blocker path before adding tests. (FR-001, FR-011, FR-014, SC-007, SC-008)

**Checkpoint**: Scope is confirmed; no archive, hand-edited generated payload, installer, marketplace, scanner, or eval file is in the edit plan. Source-derived `dist/` regeneration remains allowed when required by declared source changes.

---

## Phase 2: Foundational TDD Coverage

**Purpose**: Add focused failing coverage before changing prerequisite output.

**Critical**: Complete this phase before updating `check-prerequisites.sh`.

- [x] T004 [US1] Add focused assertions in `tests/speckit-pro/layer4-scripts/test-check-prerequisites.sh` that expect exactly one successful `capability_coverage` check with stable `check`, `pass`, `message`, and `detail` fields. (AC-3.1, FR-001, FR-011, FR-013, SC-001, SC-007)
- [x] T005 [US1] Add focused assertions in `tests/speckit-pro/layer4-scripts/test-check-prerequisites.sh` that the missing optional research/context capability path remains `all_pass=true`, has no per-tool available/missing inventory, and communicates confidence or fallback impact. (AC-3.1, AC-3.4, FR-002, FR-003, FR-012, SC-001, SC-006)
- [x] T006 [US1] Add focused assertions in `tests/speckit-pro/layer4-scripts/test-check-prerequisites.sh` for at least one true prerequisite blocker path that remains `all_pass=false` with an actionable failure message. (FR-014, SC-008)
- [x] T007 [US1] Add JSON parseability assertions in `tests/speckit-pro/layer4-scripts/test-check-prerequisites.sh` that stdout is one JSON document with stable top-level pass state, branch context, worktree context, feature-branch context, and checks fields. (FR-013, SC-007)
- [x] T008 [US1] Run `bash tests/speckit-pro/run-all.sh --layer 4` and confirm the new focused assertions fail for the old optional-tool report before implementing the script change. (FR-008, SC-004)

**Checkpoint**: Layer 4 captures the desired advisory contract and still protects true blocker behavior.

---

## Phase 3: User Story 1 - Non-blocking Capability Advisory (Priority: P1) MVP

**Goal**: Prerequisite checks report optional research/context coverage as one successful generic advisory and preserve true blockers.

**Independent Test**: Run the focused Layer 4 prerequisite tests and confirm missing optional capability coverage succeeds while a true prerequisite blocker fails.

### Implementation for User Story 1

- [x] T009 [US1] Replace the hardcoded optional-tool report in `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh` with one successful `capability_coverage` result. (AC-3.1, FR-001, FR-011, SC-001)
- [x] T010 [US1] Update `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh` advisory message/detail text to name the four capability categories: codebase context, library documentation, web/domain research, and source extraction. (AC-3.1, AC-3.3, FR-003, FR-011, SC-003)
- [x] T011 [US1] Preserve JSON-only stdout and stable output shape in `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh` while moving any failure diagnostics out of stdout. (FR-013, SC-007)
- [x] T012 [US1] Preserve blocking behavior in `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh` for true prerequisites such as missing SpecKit CLI, project initialization, constitution, phase command installation, or workflow-file inputs. (AC-3.4, FR-012, FR-014, SC-006, SC-008)
- [x] T013 [US1] Run `bash -n speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh` and `bash tests/speckit-pro/run-all.sh --layer 4`, then confirm the prerequisite output assertions pass after the script update. (FR-008, SC-004, SC-007, SC-008)

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Capability-first User Guidance (Priority: P2)

**Goal**: Active prerequisite, limitation, coach, and autopilot guidance explains capability-first discovery, fallback behavior, and the allowed concrete-identifier boundary.

**Independent Test**: Review changed active guidance and confirm it avoids a fixed optional-tool installation contract while retaining only allowed concrete identifiers.

### Implementation for User Story 2

- [x] T014 [US2] Update `speckit-pro/skills/speckit-autopilot/references/prerequisites.md` so Claude prerequisite guidance describes `capability_coverage`, the four capability categories, fallback behavior, and true escalation boundaries without per-tool inventory wording. (AC-3.2, AC-3.3, AC-3.4, FR-004, FR-006, FR-012, SC-002, SC-003, SC-006)
- [x] T015 [US2] Update `speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md` so Codex prerequisite guidance matches the Claude capability-first contract, category set, fallback/escalation boundary, and concrete-identifier exception policy. (AC-3.2, AC-3.3, AC-3.4, FR-004, FR-006, FR-012, SC-002, SC-003, SC-006)
- [x] T016 [P] [US2] Update `speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md` to describe optional research/context support as capability coverage with built-in fallbacks, not as a preferred named optional-tool set. (AC-3.2, AC-3.3, FR-004, FR-006, SC-002, SC-003)
- [x] T017 [P] [US2] Update `speckit-pro/skills/speckit-coach/references/autopilot-guide.md` so coaching guidance explains capability-first discovery, confidence impact, and fallback behavior without adding installer or marketplace guidance. (AC-3.2, AC-3.3, AC-3.4, FR-005, FR-007, SC-002, SC-003, SC-006)
- [x] T018 [P] [US2] Update adjacent active preflight or limitation wording in `speckit-pro/skills/speckit-autopilot/SKILL.md` only where it repeats the old optional-tool framing. (AC-3.2, AC-3.3, FR-005, FR-006, FR-007, SC-002, SC-003)
- [x] T019 [P] [US2] Update adjacent active preflight or limitation wording in `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` only where it repeats the old optional-tool framing. (AC-3.2, AC-3.3, FR-005, FR-006, FR-007, SC-002, SC-003)
- [x] T020 [US2] Review declared active guidance files `speckit-pro/skills/speckit-autopilot/references/prerequisites.md`, `speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md`, `speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md`, `speckit-pro/skills/speckit-coach/references/autopilot-guide.md`, `speckit-pro/skills/speckit-autopilot/SKILL.md`, and `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` for any remaining concrete optional-tool names and classify each as platform metadata, exact repository file reference, generated source-derived duplicate, historical provenance, or a wording issue to remove. (AC-3.3, FR-006, FR-010, SC-003, SC-005)
- [x] T021 [US2] Compare `git diff --name-only` against `specs/tacd-003-prerequisite-and-documentation-messaging/plan.md` declared file operations and confirm no archive, changelog, fixture-only, installer, marketplace, broad scanner, or eval file was edited while completing the docs pass; allow source-derived `dist/` payload copies only when regenerated from declared source changes. (FR-007, FR-009, FR-010, SC-005)

**Checkpoint**: User Story 2 is independently reviewable against the active guidance contract.

---

## Phase 5: User Story 3 - Focused Regression Coverage (Priority: P3)

**Goal**: Maintainers have deterministic coverage for TACD-003 without absorbing TACD-004 broad enforcement.

**Independent Test**: Run focused Layer 4 coverage plus the default structural and deterministic validation commands from `quickstart.md`.

### Implementation for User Story 3

- [x] T022 [US3] Add narrow changed-doc assertions to `tests/speckit-pro/layer4-scripts/test-check-prerequisites.sh` only if they stay focused on the declared active guidance files and do not become broad named-tool enforcement. (FR-008, FR-009, SC-002, SC-003, SC-004)
- [x] T023 [US3] Run `bash -n speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh` and `bash tests/speckit-pro/run-all.sh --layer 4`, then record evidence for `capability_coverage`, JSON parseability, missing-optional success, true-blocker failure, and any narrow changed-doc assertions. (FR-008, FR-013, FR-014, SC-004, SC-007, SC-008)
- [x] T024 [US3] Run `bash tests/speckit-pro/run-all.sh --layer 1` and confirm structural validation still passes with the active guidance changes. (FR-004, FR-005, FR-008, SC-004)
- [x] T025 [US3] Run `bash tests/speckit-pro/run-all.sh` and confirm the default deterministic suite passes without Layer 3 eval changes or Layer 5 pointer-coverage expansion. (FR-008, FR-009, SC-004)
- [x] T026 [US3] Confirm `git diff --name-only` stays inside the TACD-003 declared file set plus `specs/tacd-003-prerequisite-and-documentation-messaging/tasks.md` and regenerated source-derived `dist/` payload copies; if not, stop and update the plan before continuing. (FR-007, FR-009, FR-010, SC-005)

**Checkpoint**: User Story 3 is independently verified with focused deterministic coverage.

---

## Phase 6: Polish and PR Packet Readiness

**Purpose**: Prepare review evidence without expanding implementation scope.

- [x] T027 Build PR packet traceability from `specs/tacd-003-prerequisite-and-documentation-messaging/tasks.md` that maps AC-3.1 through AC-3.4, FR-001 through FR-014, and SC-001 through SC-008 to changed files and verification evidence. (AC-3.1, AC-3.2, AC-3.3, AC-3.4, SC-005)
- [x] T028 Include a PR packet section based on `specs/tacd-003-prerequisite-and-documentation-messaging/spec.md` stating that missing optional research or context capabilities remain non-blocking when acceptable fallback evidence exists and escalate only when no acceptable evidence path exists or a true gate fails. (AC-3.4, FR-002, FR-003, FR-012, FR-014, SC-001, SC-006, SC-008)
- [x] T029 Include a `Repo vs Platform Evidence` PR packet section based on `specs/tacd-003-prerequisite-and-documentation-messaging/plan.md` that separates repository-specific guidance backed by Racecraft sources or generated artifacts from platform/vendor behavior backed by official vendor evidence. (FR-004, FR-006, SC-005)
- [x] T030 Include a PR packet exception inventory from the changed active guidance paths listed in `specs/tacd-003-prerequisite-and-documentation-messaging/plan.md` for any remaining concrete optional-tool names, limited to platform metadata, exact repository file references, generated source-derived duplicates, or historical provenance. (AC-3.3, FR-006, FR-010, SC-003, SC-005)
- [x] T031 Include a TACD-004 handoff in the PR packet from `specs/tacd-003-prerequisite-and-documentation-messaging/spec.md` for broad static or eval enforcement, Layer 3 expectation updates, Layer 5 pointer coverage, and broad named-tool detection. (FR-009, SC-005)
- [x] T032 Record rollback notes in the PR packet using `specs/tacd-003-prerequisite-and-documentation-messaging/quickstart.md`: revert the prerequisite script advisory change, focused Layer 4 assertions, and active guidance edits together because the docs describe the script contract. (FR-001, FR-004, FR-008, SC-005)

**Checkpoint**: Review packet evidence is ready and broad TACD-004 work remains explicitly deferred.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup and Scope Guard** has no dependencies.
- **Phase 2: Foundational TDD Coverage** depends on Phase 1 and blocks script implementation.
- **Phase 3: User Story 1** depends on Phase 2.
- **Phase 4: User Story 2** depends on Phase 3 so docs can describe the final script contract.
- **Phase 5: User Story 3** depends on Phases 3 and 4.
- **Phase 6: Polish and PR Packet Readiness** depends on all user stories.

### User Story Dependencies

- **US1 (P1)**: Must complete first because docs and validation depend on the final prerequisite output contract.
- **US2 (P2)**: Starts after US1 and can be reviewed independently against the active guidance files.
- **US3 (P3)**: Starts after US1 and US2 because it validates both changed output and changed guidance.

### Parallel Opportunities

- **T016-T019** are parallel-safe docs-only tasks because they touch different files and do not depend on final script output wording.
- After T014 and T015 establish the shared prerequisite contract, T016-T019 can be assigned concurrently.
- PR packet tasks T027-T032 should remain sequential because they depend on final changed files and verification evidence.

---

### Incremental Delivery

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 for US1.
3. Stop and validate `bash tests/speckit-pro/run-all.sh --layer 4`.

### Full Delivery

1. Complete US1 script behavior and focused tests.
2. Complete US2 active guidance updates in the declared file set only.
3. Complete US3 focused validation.
4. Prepare PR packet evidence and TACD-004 handoff.

### Scope Boundaries

- Do not edit archives, changelogs, fixture-only prose, hand-edit generated payloads, installers, marketplace integration, broad scanners, or evals; allow source-derived `dist/` regeneration only when required by declared source changes.
- Do not add broad named-tool static enforcement, Layer 3 eval expectation updates, Layer 5 pointer coverage, or broad named-tool detection in TACD-003.
- Do not introduce a fixed recommended optional-tool set.

## Requirement Coverage Summary

| Coverage Target | Tasks |
|-----------------|-------|
| AC-3.1 | T004, T005, T009, T010, T027 |
| AC-3.2 | T014, T015, T016, T017, T018, T019, T027 |
| AC-3.3 | T010, T014, T015, T016, T017, T018, T019, T020, T027, T030 |
| AC-3.4 | T005, T012, T014, T015, T017, T027, T028 |
| FR-001 | T004, T009, T027, T032 |
| FR-002 | T005, T028 |
| FR-003 | T005, T010, T028 |
| FR-004 | T014, T015, T016, T023, T024, T029, T032 |
| FR-005 | T017, T018, T019, T024 |
| FR-006 | T014, T015, T016, T018, T019, T020, T029, T030 |
| FR-007 | T001, T017, T018, T019, T021, T026 |
| FR-008 | T008, T013, T022, T023, T024, T025, T032 |
| FR-009 | T001, T021, T022, T025, T026, T031 |
| FR-010 | T001, T020, T021, T026, T030 |
| FR-011 | T004, T009, T010 |
| FR-012 | T005, T012, T014, T015, T028 |
| FR-013 | T004, T007, T011, T023 |
| FR-014 | T003, T006, T012, T023, T028 |
| SC-001 | T004, T005, T009, T028 |
| SC-002 | T014, T015, T016, T017, T018, T019, T022 |
| SC-003 | T010, T014, T015, T016, T017, T018, T019, T020, T022, T030 |
| SC-004 | T008, T013, T022, T023, T024, T025 |
| SC-005 | T001, T020, T021, T026, T027, T029, T030, T031, T032 |
| SC-006 | T005, T012, T014, T015, T017, T028 |
| SC-007 | T004, T007, T011, T023 |
| SC-008 | T006, T012, T023, T028 |

## Approved Validation Task Mapping

| Validation Target | Tasks | Why approved |
|-------------------|-------|--------------|
| Scope and design guard | T001, T002, T003 | Confirms the edit set, design concept, and existing prerequisite/test surfaces before source changes. |
| Script safety and focused regression evidence | T006, T007, T008, T011, T013, T022, T023, T024, T025 | Validates true-blocker preservation, JSON parseability, `bash -n`, focused Layer 4 assertions, structural validation, and the default deterministic suite without adding TACD-004 enforcement. |
| Scope drift and review packet evidence | T021, T026, T027, T028, T029, T030, T031, T032 | Confirms the diff stays inside the declared TACD-003 file set and records traceability, repo/platform evidence, concrete-name exceptions, TACD-004 handoff, and rollback notes. |

## Metrics

- Total tasks: 32
- Phases: 6
- Parallel opportunities: 4 tasks marked `[P]`
- User stories covered: 3
