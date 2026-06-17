# Tasks: Safe Interactive Selector and Validation Aids

**Input**: Design documents from `/specs/doc-006-safe-interactive-selector-and-validation-aids/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/doc006-safe-aids.schema.json`, `quickstart.md`, `docs/ai/specs/.process/DOC-006-design-concept.md`

**Tests**: DOC-006 explicitly requires focused metadata/rendering validation plus docs validation and link validation.

**Reviewability**: Keep implementation within the plan's docs-site slice: one existing route, one Astro component, one source-derived data helper, and one focused validation script. If implementation exceeds 700 reviewable LOC, 6 production files, 9 total files, or adds another primary surface, stop and record a split decision before continuing.

**Organization**: Tasks are grouped by user story so selector guidance, repository metadata checker, and first-run safety aids can be reviewed independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches a separate file and has no dependency on incomplete tasks.
- **[Story]**: User story label for story-specific tasks.
- Each task includes exact file paths.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preserve the existing route, create the planned data/test surfaces, and keep the reviewability budget visible before story work begins.

- [x] T001 [P] Convert the existing route source from `docs-site/src/content/docs/choose-your-path.md` to `docs-site/src/content/docs/choose-your-path.mdx` while preserving the public `choose-your-path` route and frontmatter.
- [x] T002 [P] Create the DOC-006 source-derived metadata helper shell in `docs-site/src/data/safe-install-aids.ts` with typed exports for selector paths, checker comparisons, diagram nodes, first-run checkpoints, handoffs, and the six required manifest input paths.
- [x] T003 [P] Create the focused DOC-006 validation harness in `docs-site/scripts/validate-doc006-safe-aids.mjs` with fixture entry points for selector, checker, diagram, checklist, handoff, and command-surface assertions.
- [x] T004 Verify the plan's reviewability budget against the active file scope and record any split-triggering drift before production edits in `specs/doc-006-safe-interactive-selector-and-validation-aids/tasks.md`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish source-derived metadata and focused RED validation before rendering behavior depends on it.

**Critical**: No user story rendering work should begin until these tasks are complete.

- [x] T005 Add RED validation assertions for required selector fields, supported platform/scope records, Claude/Codex command-surface separation, and unsupported or ambiguous selector states in `docs-site/scripts/validate-doc006-safe-aids.mjs`.
- [x] T006 Add RED validation assertions for the six repository manifest inputs, pass/mismatch/unavailable checker states, compared values, consistency rules, and informational packaging-difference rows in `docs-site/scripts/validate-doc006-safe-aids.mjs`.
- [x] T007 Add RED validation assertions for no pasted JSON input, no local user diagnostic UI, no browser-side command execution claims, lightweight handoff links, payload diagram node coverage, and first-run checkpoint coverage in `docs-site/scripts/validate-doc006-safe-aids.mjs`.
- [x] T008 Implement manifest loading or JSON imports for `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `speckit-pro/.claude-plugin/plugin.json`, `speckit-pro/.codex-plugin/plugin.json`, `dist/claude/speckit-pro/.claude-plugin/plugin.json`, and `dist/codex/speckit-pro/.codex-plugin/plugin.json` in `docs-site/src/data/safe-install-aids.ts`.
- [x] T009 Implement curated selector path records that combine manifest-backed values with command labels, prerequisites, success signals, next docs links, and unsupported/unavailable/ambiguous state metadata in `docs-site/src/data/safe-install-aids.ts`.
- [x] T010 Implement repository-only checker comparison records for stable source/dist name, version, marketplace source/path, and counterpart presence rules in `docs-site/src/data/safe-install-aids.ts`.
- [x] T011 Run `node docs-site/scripts/validate-doc006-safe-aids.mjs` and confirm failures are limited to missing rendering integration before editing `docs-site/src/components/SafeInstallAids.astro`.

**Checkpoint**: Source-derived data and focused RED checks are ready for user-story implementation.

---

## Phase 3: User Story 1 - Choose the correct install path (Priority: P1)

**Goal**: Users can select a supported Claude Code or Codex platform/scope path and see only the relevant commands, prerequisites, success signals, and next docs links.

**Independent Test**: Review each selector choice on `choose-your-path` and confirm the visible command sequence, labels, prerequisites, success signals, and handoff links match the selected path while unrelated path content stays hidden or clearly inactive.

### Tests for User Story 1

- [x] T012 [US1] Turn the selector RED checks GREEN for required path fields, command-surface leakage, unsupported/ambiguous states, and selected/current state exposure in `docs-site/scripts/validate-doc006-safe-aids.mjs`.

### Implementation for User Story 1

- [x] T013 [US1] Render platform and install-scope selector controls with native form controls or programmatic selected/current state for any custom controls in `docs-site/src/components/SafeInstallAids.astro`.
- [x] T014 [US1] Render the complete static fallback table for every supported selector path, including platform, scope, prerequisites, command sequence, success signals, and next links in `docs-site/src/components/SafeInstallAids.astro`.
- [x] T015 [US1] Render the selected path output with visible copyable command blocks, platform labels, scope labels, prerequisite notes, success signals, and next documentation links in `docs-site/src/components/SafeInstallAids.astro`.
- [x] T016 [US1] Render explicit unsupported, unavailable, and ambiguous selector-state messages that keep supported static guidance reachable and avoid local diagnostic or repair claims in `docs-site/src/components/SafeInstallAids.astro`.
- [x] T017 [US1] Import and place the safe install aids component in the preserved route content in `docs-site/src/content/docs/choose-your-path.mdx`.

**Checkpoint**: User Story 1 is independently reviewable by selector state and copyable command output.

---

## Phase 4: User Story 2 - Inspect repository metadata consistency (Priority: P2)

**Goal**: Maintainers and evaluators can inspect repository-only manifest/version consistency with clear pass, mismatch, unavailable, and informational states.

**Independent Test**: Change focused fixture inputs and confirm the checker reports matching and mismatching states with compared values, expected rules, and lightweight handoffs without accepting user JSON or diagnosing local files.

### Tests for User Story 2

- [x] T018 [US2] Turn the checker RED checks GREEN for pass, mismatch, unavailable, compared values, six manifest sources, no pasted JSON, no local config inspection, and no local diagnostic UI in `docs-site/scripts/validate-doc006-safe-aids.mjs`.

### Implementation for User Story 2

- [x] T019 [US2] Render repository manifest/version checker pass rows with compared values and expected consistency rules in `docs-site/src/components/SafeInstallAids.astro`.
- [x] T020 [US2] Render mismatch checker rows with both values, the expected consistency rule, and lightweight install or maintainer handoff links in `docs-site/src/components/SafeInstallAids.astro`.
- [x] T021 [US2] Render unavailable checker rows for missing source or generated payload metadata without stale output, pasted JSON input, local user file inspection, or repair claims in `docs-site/src/components/SafeInstallAids.astro`.
- [x] T022 [US2] Render informational rows for intentional Claude/Codex packaging differences without marking them as failed consistency checks in `docs-site/src/components/SafeInstallAids.astro`.

**Checkpoint**: User Story 2 is independently reviewable by checker state and manifest comparison rows.

---

## Phase 5: User Story 3 - Review safe first-run checkpoints (Priority: P3)

**Goal**: Users can review generated payload boundaries and safe first-run checkpoints without browser-side local execution.

**Independent Test**: Disable scripting or use keyboard-only navigation and confirm diagram nodes, checklist items, safe handoffs, and command-safety copy remain readable, reachable, and complete.

### Tests for User Story 3

- [x] T023 [US3] Turn the diagram, checklist, handoff, keyboard, and no-local-execution RED checks GREEN in `docs-site/scripts/validate-doc006-safe-aids.mjs`.

### Implementation for User Story 3

- [x] T024 [US3] Render an accessible generated-payload diagram fallback with semantic nodes for source tree, Claude distribution, Codex distribution, marketplace entries, and Codex cache in `docs-site/src/components/SafeInstallAids.astro`.
- [x] T025 [US3] Render the first-run checklist with platform route, Spec Kit CLI exists/version, constitution, roadmap or SPEC-ID, GitHub CLI, `jq`, branch/worktree clean-state, scaffold output, and docs validation checkpoints in `docs-site/src/components/SafeInstallAids.astro`.
- [x] T026 [US3] Render safe handoff copy explaining that commands are visible copyable guidance only and browser behavior never runs shell commands, reads local files, writes config, installs plugins, or invokes local workflows in `docs-site/src/components/SafeInstallAids.astro`.
- [x] T027 [US3] Verify keyboard focus order, visible focus, and selected/current state behavior across selector, checker, diagram, and checklist controls in `docs-site/src/components/SafeInstallAids.astro`.

**Checkpoint**: User Story 3 is independently reviewable by static diagram fallback, checklist coverage, and no-local-execution safety copy.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete docs slice and prepare review evidence.

- [x] T028 Run `node docs-site/scripts/validate-doc006-safe-aids.mjs` and resolve any focused validation failures in `docs-site/scripts/validate-doc006-safe-aids.mjs`.
- [x] T029 Run `pnpm --dir docs-site validate` and resolve docs build/content failures in `docs-site/src/content/docs/choose-your-path.mdx`.
- [x] T030 Run `pnpm --dir docs-site validate:links` and resolve broken handoff links in `docs-site/src/components/SafeInstallAids.astro`.
- [x] T031 Run `pnpm --dir docs-site validate && pnpm --dir docs-site validate:links` and capture final verification evidence against `specs/doc-006-safe-interactive-selector-and-validation-aids/quickstart.md`.
- [x] T032 Perform manual command-safety and static-fallback review for the selector, checker, payload diagram, first-run checklist, and copyable command blocks, then verify the PR review packet requirements, non-goals, rollback/feature-flag note, and FR traceability against `specs/doc-006-safe-interactive-selector-and-validation-aids/spec.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion.
- **User Story 2 (Phase 4)**: Depends on Foundational completion and may be reviewed independently after checker rendering is complete.
- **User Story 3 (Phase 5)**: Depends on Foundational completion and may be reviewed independently after diagram/checklist rendering is complete.
- **Polish (Phase 6)**: Depends on desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: MVP scope; no dependency on US2 or US3 after Foundation.
- **User Story 2 (P2)**: No dependency on US1 behavior, but shares `docs-site/src/components/SafeInstallAids.astro`.
- **User Story 3 (P3)**: No dependency on US1 or US2 behavior, but shares `docs-site/src/components/SafeInstallAids.astro`.

### Within Each User Story

- Focused validation starts RED before dependent rendering behavior.
- Data helper work precedes component rendering.
- Static fallback content must be present before progressive enhancement behavior.
- Story checkpoint should pass before moving to polish.

---

## Parallel Opportunities

- T001, T002, and T003 can run in parallel because they touch separate files.
- After Foundation, US1, US2, and US3 can be assigned separately only if workers coordinate ownership of `docs-site/src/components/SafeInstallAids.astro`; individual component edits are not marked [P] because they share that file.
- Focused validation edits in `docs-site/scripts/validate-doc006-safe-aids.mjs` are intentionally sequential because they share one script.

---

## Parallel Example: Setup

```text
Task: "Convert the existing route source from docs-site/src/content/docs/choose-your-path.md to docs-site/src/content/docs/choose-your-path.mdx"
Task: "Create the DOC-006 source-derived metadata helper shell in docs-site/src/data/safe-install-aids.ts"
Task: "Create the focused DOC-006 validation harness in docs-site/scripts/validate-doc006-safe-aids.mjs"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational RED checks and metadata helper.
3. Complete Phase 3: User Story 1.
4. Stop and validate selector output independently with `node docs-site/scripts/validate-doc006-safe-aids.mjs`.

### Incremental Delivery

1. Complete Setup and Foundation.
2. Deliver US1 selector guidance and copyable command output.
3. Deliver US2 repository manifest/version checker states.
4. Deliver US3 payload diagram, first-run checklist, and safe handoff copy.
5. Run focused validation, docs validation, and link validation.

### Full Verification

```bash
node docs-site/scripts/validate-doc006-safe-aids.mjs
pnpm --dir docs-site validate
pnpm --dir docs-site validate:links
pnpm --dir docs-site validate && pnpm --dir docs-site validate:links
```

---

## Functional Requirement Coverage

- **FR-001**: T001, T017, T029
- **FR-002**: T009, T013, T014, T017
- **FR-003**: T005, T009, T013, T016
- **FR-004**: T009, T014, T015, T017
- **FR-005**: T005, T012, T015
- **FR-006**: T009, T015, T012
- **FR-007**: T002, T006, T008, T010, T018
- **FR-008**: T007, T008, T032
- **FR-009**: T006, T008, T010, T018
- **FR-010**: T006, T010, T019, T020, T022
- **FR-011**: T007, T018, T021, T026
- **FR-012**: T007, T023, T024
- **FR-013**: T007, T023, T025
- **FR-014**: T013, T014, T024, T025, T027, T032
- **FR-015**: T007, T021, T026, T032
- **FR-016**: T007, T016, T020, T021, T026
- **FR-017**: T003, T005, T006, T007, T012, T018, T023, T028, T032
