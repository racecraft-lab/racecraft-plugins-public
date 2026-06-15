# Tasks: Codex marketplace installation path

**Input**: Design documents from the DOC-004 feature directory

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, the content contract, `quickstart.md`, and completed checklists

**Tests**: No TDD tasks are required because DOC-004 is documentation-only. Validation tasks are included in the final phase.

**Reviewability**: Keep DOC-004 within the documented docs process budget: 250-500 reviewable documentation LOC, 0 production-code files, 3 implementation documentation entry points, and 4-6 total files including SpecKit artifacts. If implementation pressure expands beyond this, stop before editing non-docs files and update the plan with an explicit split or narrow-source-correction decision.

**Organization**: Tasks are grouped by user story so each story can be implemented and reviewed independently after foundation work completes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches a different file or is read-only after dependencies complete
- **[Story]**: User story label from `spec.md`
- Every task names an exact repo-relative file path or validation target

## Phase 1: Setup (Source Refresh And Scope Gate)

**Purpose**: Refresh source truth before any docs copy is written.

- [x] T001 Refresh official OpenAI Codex plugin, build-plugin, skills, subagents, permissions, approvals, security, and local CLI help evidence, then update `specs/doc-004-codex-marketplace-installation-path/research.md` (FR-006, FR-007, FR-017, AC-4.1)
- [x] T002 Audit repo marketplace, generated payload, install skill, bundled custom-agent TOML, and hook payload evidence, then update `specs/doc-004-codex-marketplace-installation-path/research.md` (FR-002, FR-004, FR-005, FR-009, FR-010, FR-011, FR-013, AC-4.2, AC-4.3, AC-4.4, AC-4.5)
- [x] T003 Reconcile refreshed source evidence against `specs/doc-004-codex-marketplace-installation-path/spec.md`, `specs/doc-004-codex-marketplace-installation-path/plan.md`, `specs/doc-004-codex-marketplace-installation-path/data-model.md`, and the content contract; stop for explicit approval before any non-docs source correction (FR-016)

---

## Phase 2: Foundational (Blocking Documentation Structure)

**Purpose**: Establish the detailed Codex page structure and review bounds before user-story copy lands.

**Critical**: No user-story documentation edits should begin until this phase is complete.

- [x] T004 Replace the DOC-002 shell in `docs-site/src/content/docs/install/codex.md` with a task-first DOC-004 outline covering install decision, source and generated payload and cache distinction, install paths, custom-agent registration, verification, stale-update checkpoint, safety, source evidence, and DOC-007 plus DOC-008 boundaries (FR-001, FR-014, FR-018)

**Checkpoint**: Foundation ready; each user story can now be implemented and reviewed independently.

---

## Phase 3: User Story 1 - Choose The Correct Install Path (Priority: P1)

**Goal**: A Codex user can choose repo-scoped, personal or local, or CLI marketplace setup without confusing source tree, generated payload, marketplace metadata, and installed cache.

**Independent Test**: Review only `docs-site/src/content/docs/install/codex.md` and confirm a first-time Codex user can select the correct install context and identify which path is source, generated payload, marketplace metadata, or installed cache.

### Implementation for User Story 1

- [x] T005 [US1] Add an accessible install path matrix plus compact list alternative to `docs-site/src/content/docs/install/codex.md` for repo-scoped, personal or local, and CLI marketplace flows (FR-003, FR-018, SC-002, SC-006, AC-4.1)
- [x] T006 [US1] Document repo-scoped marketplace installation, personal or local generated-payload layout, and source-backed CLI marketplace examples in `docs-site/src/content/docs/install/codex.md`, including `owner/repo`, `owner/repo@ref`, HTTP or HTTPS Git URLs, SSH Git URLs, `--ref`, repeatable Git-only `--sparse`, and `--json`; explicitly warn against installing Codex from the mixed authoring source tree (FR-002, FR-003, FR-004, FR-006, FR-007, FR-008, SC-002, AC-4.1, AC-4.6)
- [x] T007 [US1] Explain installed plugin cache behavior and add the bounded stale-after-update checkpoint to `docs-site/src/content/docs/install/codex.md`, including DOC-007 and DOC-008 next links (FR-005, FR-019, SC-007, AC-4.2)

**Checkpoint**: User Story 1 is independently reviewable against AC-4.1, AC-4.2, AC-4.6, SC-002, and SC-007.

---

## Phase 4: User Story 2 - Install And Verify Custom Agents (Priority: P1)

**Goal**: A Codex user can install SpecKit Pro, run the Codex-only install skill, restart Codex, and verify the expected custom-agent TOML files.

**Independent Test**: Follow the custom-agent section in `docs-site/src/content/docs/install/codex.md` and confirm it covers `@SpecKit Pro -> install`, `$install`, destination choice, expected files, rerun triggers, restart, and observational verification without changing installer behavior.

### Implementation for User Story 2

- [x] T008 [US2] Add the Codex-only custom-agent registration checklist with `@SpecKit Pro -> install`, `$install`, default user destination, explicit project destination override, and the exact nine installer-copied TOML files to `docs-site/src/content/docs/install/codex.md` (FR-009, FR-011, FR-013, SC-003, AC-4.3)
- [x] T009 [US2] Explain bundled skills, OpenAI agent metadata sidecars, TOML custom-agent registration, observational verification, no manual cache or TOML edits, restart triggers, and rerun triggers in `docs-site/src/content/docs/install/codex.md` (FR-010, FR-012, FR-019, SC-007, AC-4.4)

**Checkpoint**: User Story 2 is independently reviewable against AC-4.3, AC-4.4, SC-003, and SC-007.

---

## Phase 5: User Story 3 - Keep Install Guidance Consistent (Priority: P2)

**Goal**: Maintainers can compare the root README, plugin README, and docs-site Codex page and find no contradictory Codex install guidance.

**Independent Test**: Compare `README.md`, `speckit-pro/README.md`, and `docs-site/src/content/docs/install/codex.md` for consistent marketplace surfaces, generated payload target, installed cache behavior, install skill, restart, verification, stale-update checkpoint, and bounded safety language.

### Implementation for User Story 3

- [x] T010 [P] [US3] Align the root `README.md` Codex install section with the docs-site guide on repo marketplace, generated payload, installed cache, `$install`, restart, nine-file verification, stale-update checkpoint, and bounded install safety (FR-001, FR-004, FR-005, FR-009, FR-012, FR-013, FR-019, AC-4.6)
- [x] T011 [P] [US3] Align `speckit-pro/README.md` Codex install, troubleshooting, and packaging sections with the docs-site guide on repo marketplace, generated payload, installed cache, `$install`, restart, nine-file verification, stale-update checkpoint, and bounded install safety (FR-001, FR-004, FR-005, FR-009, FR-012, FR-013, FR-019, AC-4.6)
- [x] T012 [US3] Preserve explicit DOC-003, DOC-007, and DOC-008 boundaries while removing or revising any Claude Code command leakage across `README.md`, `speckit-pro/README.md`, and `docs-site/src/content/docs/install/codex.md` (FR-014, FR-015)
- [x] T013 [US3] Perform a three-entry-point consistency pass across `README.md`, `speckit-pro/README.md`, and `docs-site/src/content/docs/install/codex.md`, fixing contradictory path, command, cache, custom-agent, restart, verification, stale-update, or safety statements (FR-001, SC-001, AC-4.6)

**Checkpoint**: User Story 3 is independently reviewable against AC-4.6 and SC-001.

---

## Phase 6: User Story 4 - Evaluate Install Safety (Priority: P2)

**Goal**: A security-minded Codex user sees bounded sandbox, approvals, network, cache, hook payload, external authentication, and trust implications before first install.

**Independent Test**: Review the safety section in `docs-site/src/content/docs/install/codex.md` and confirm it explains first-install safety without becoming the DOC-008 troubleshooting, update, rollback, managed-policy, or full trust model.

### Implementation for User Story 4

- [x] T014 [US4] Add a text-visible install-safety warning to `docs-site/src/content/docs/install/codex.md` covering sandbox mode, approval prompts, network access, installed cache and source distinction, destination permissions, user-scoped destination, project-scoped override, and outside-workspace writes (FR-013, FR-018, SC-004, SC-006, AC-4.5)
- [x] T015 [US4] Identify Codex hooks as bundled plugin payload configuration and defer hook trust analysis, managed policy, external authentication, permission troubleshooting, update, remove, rollback, and stale-cache forensics to DOC-008 in `docs-site/src/content/docs/install/codex.md` (FR-013, FR-014, AC-4.5)
- [x] T016 [US4] Verify safety copy in `docs-site/src/content/docs/install/codex.md` does not promise silent hook execution, sandbox bypass, approval bypass, unrestricted network access, or automatic external authentication (FR-013, FR-016, AC-4.5)

**Checkpoint**: User Story 4 is independently reviewable against AC-4.5, SC-004, and SC-006.

---

## Phase 7: Polish & Cross-Cutting Validation

**Purpose**: Validate traceability, accessibility, source backing, and docs-only scope after user stories are implemented.

- [x] T017 Review every changed Codex command and path snippet in `README.md`, `speckit-pro/README.md`, and `docs-site/src/content/docs/install/codex.md` against official OpenAI docs, local CLI help, or checked-in source, including the contract's CLI source-form checklist for `owner/repo@ref`, SSH Git URLs, repeatable Git-only `--sparse`, and `--json`; then record source-backed snippet review in `docs/ai/specs/.process/DOC-004-workflow.md` implementation evidence (FR-017)
- [x] T018 Review accessibility requirements in `docs-site/src/content/docs/install/codex.md`: semantic headings, descriptive links, labeled command groups, text-visible warnings, and mobile-readable or screen-reader-friendly matrix alternative (FR-018, SC-006)
- [x] T019 Run `cd docs-site && pnpm validate`, then `cd docs-site && pnpm validate:links`, and record both results in `docs/ai/specs/.process/DOC-004-workflow.md` (FR-017, SC-005)
- [x] T020 Run `bash tests/speckit-pro/run-all.sh`, review `git diff --name-only` for docs-only scope, and prepare PR evidence from `spec.md`, `plan.md`, `tasks.md`, and validation outputs (FR-014, FR-016, FR-017, SC-005)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start here.
- **Foundational (Phase 2)**: Depends on Phase 1 source refresh and audit.
- **User Stories (Phases 3-6)**: Depend on Phase 2 foundation.
- **Polish & Cross-Cutting Validation (Phase 7)**: Depends on all implemented user stories.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundation and should land before README consistency work because it establishes the detailed docs-site guide.
- **User Story 2 (P1)**: Starts after Foundation and can be reviewed independently from US1 once the page outline exists.
- **User Story 3 (P2)**: Depends on the detailed docs-site guide from US1 and US2 so README alignment has a stable source.
- **User Story 4 (P2)**: Starts after Foundation and should finish before final README consistency validation because safety invariants must agree across entry points.

### Parallel Opportunities

- T010 and T011 can run in parallel after US1, US2, and US4 docs-site copy is stable because they modify different README files.
- Manual review tasks T017 and T018 may be performed by different reviewers after implementation, but only one final evidence update should be recorded in `docs/ai/specs/.process/DOC-004-workflow.md`.

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete User Story 1 and User Story 2.
3. Stop and review `docs-site/src/content/docs/install/codex.md` for AC-4.1 through AC-4.4 before README alignment.

### Incremental Delivery

1. Source refresh and evidence audit.
2. Detailed docs-site install path and custom-agent guide.
3. README and plugin README consistency pass.
4. Bounded safety and stale-update pass.
5. Full validation and PR evidence.

### Scope Guard

- Do not modify manifests, generated payloads, installer behavior, custom-agent TOML templates, hooks, release automation, marketplace behavior, or runtime code.
- Do not turn DOC-004 into DOC-007 reference depth or DOC-008 troubleshooting, security, update, or rollback depth.
- Do not add docs-site scripts, install scripts, hooks, agents, generated payload changes, or new interactive selector components.

---

## Requirement Coverage

| Requirement / Criterion | Covered by tasks |
|-------------------------|------------------|
| AC-4.1 | T001, T005, T006 |
| AC-4.2 | T002, T007 |
| AC-4.3 | T002, T008 |
| AC-4.4 | T002, T009 |
| AC-4.5 | T002, T014, T015, T016 |
| AC-4.6 | T006, T010, T011, T013 |
| FR-001 | T004, T010, T011, T013 |
| FR-002 | T002, T006 |
| FR-003 | T005, T006 |
| FR-004 | T002, T006, T010, T011 |
| FR-005 | T002, T007, T010, T011 |
| FR-006 | T001, T006 |
| FR-007 | T001, T006 |
| FR-008 | T006 |
| FR-009 | T002, T008, T010, T011 |
| FR-010 | T002, T009 |
| FR-011 | T002, T008 |
| FR-012 | T009, T010, T011 |
| FR-013 | T002, T008, T010, T011, T014, T015, T016 |
| FR-014 | T004, T012, T015, T020 |
| FR-015 | T012 |
| FR-016 | T003, T016, T020 |
| FR-017 | T001, T017, T019, T020 |
| FR-018 | T004, T005, T014, T018 |
| FR-019 | T007, T009, T010, T011 |
| SC-001 | T010, T011, T013 |
| SC-002 | T005, T006 |
| SC-003 | T008 |
| SC-004 | T014, T015, T016 |
| SC-005 | T019, T020 |
| SC-006 | T004, T005, T014, T018 |
| SC-007 | T007, T009, T010, T011 |
