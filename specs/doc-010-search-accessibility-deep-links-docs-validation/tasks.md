# Tasks: Search, Accessibility, Deep Links, Docs Validation

**Input**: Design documents from `/specs/doc-010-search-accessibility-deep-links-docs-validation/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `checklists/`, and `docs/ai/specs/.process/DOC-010-design-concept.md`

**Tests**: Required by DOC-010 because the feature scope is docs validation, docs-quality checks, safe-aids validation, PR Checks behavior, and minimal Playwright smoke coverage.

**Reviewability**: Preserve the plan budget: primary surface `docs/process`, secondary surfaces `UI` and `harness/adapter`, projected reviewable LOC 275-395, projected production files 0-6, projected total files 6-10. If implementation exceeds 400 reviewable LOC, 6 production files, 15 total files, or adds undeclared primary surfaces, stop for a reviewability checkpoint before continuing.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently after shared foundation work.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the shared command names, dependency surface, and route/test configuration used by every story.

- [X] T001 Define the DOC-010 focused script names and combined docs validation command chain in `docs-site/package.json` for `validate`, `validate:quality`, `validate:safe-aids`, and `validate:smoke` (FR-007, FR-008)
- [X] T002 Add the minimal Playwright dev dependency needed for `validate:smoke` in `docs-site/package.json` and update `docs-site/pnpm-lock.yaml` (FR-010)
- [X] T003 [P] Create the focused docs-quality validator entrypoint with repo-relative diagnostics and safety-boundary constants in `docs-site/scripts/validate-docs-quality.mjs` (FR-007, FR-011)
- [X] T004 [P] Create Playwright configuration with local preview baseURL ownership, `/racecraft-plugins-public` base path handling, desktop/mobile projects, and compact artifact output in `docs-site/playwright.config.mjs` (FR-010, FR-013)
- [X] T005 [P] Create the initial browser smoke spec scaffold with the six logical DOC-010 routes in `docs-site/tests/docs-smoke.spec.mjs` (FR-010)
- [X] T006 Verify the setup file list still matches the declared DOC-010 budget in `specs/doc-010-search-accessibility-deep-links-docs-validation/plan.md` before user-story implementation starts (FR-013)

**Checkpoint**: Shared command names, validator entrypoints, and smoke configuration exist.

---

## Phase 2: User Story 1 - Find And Share Support Guidance (Priority: P1) MVP

**Goal**: Search, glossary entries, support-heavy headings, generated reference sections, and release workflow links are discoverable and shareable from existing routes.

**Independent Test**: Open the docs site, search for install/recovery/glossary/reference/release topics, copy representative anchors, and confirm deterministic validation reports broken or stale deep links.

### Validation for User Story 1

- [X] T007 [US1] Add failing support-anchor inventory checks for install, recovery, troubleshooting, glossary, generated reference, and release workflow anchors in `docs-site/scripts/validate-docs-quality.mjs` (FR-002, FR-003, FR-007, FR-012)
- [X] T008 [US1] Add failing source-update guidance checks for external platform claims touched by DOC-010 in `docs-site/scripts/validate-docs-quality.mjs` (FR-012)

### Implementation for User Story 1

- [X] T009 [P] [US1] Add stable glossary term anchors and support-oriented cross-links in `docs-site/src/content/docs/glossary.md` (FR-003, FR-004)
- [X] T010 [P] [US1] Add support-link and static fallback anchor guidance for install decisions in `docs-site/src/content/docs/choose-your-path.mdx` (FR-002, FR-004)
- [X] T011 [US1] Finish docs-quality anchor, glossary, generated-reference, release workflow, and source-update validation logic in `docs-site/scripts/validate-docs-quality.mjs` (FR-002, FR-003, FR-007, FR-012)

### Verification for User Story 1

- [X] T012 [US1] Run `pnpm --dir docs-site validate:quality` and confirm failures or output cite repo-relative paths from `docs-site/scripts/validate-docs-quality.mjs` (FR-007, FR-011, FR-012)
- [X] T013 [US1] Run `pnpm --dir docs-site reference:check` and confirm generated reference anchors remain deterministic from `docs-site/scripts/generate-reference-pages.mjs` (FR-003, FR-007)

**Checkpoint**: User Story 1 is searchable, linkable, and protected by deterministic validation.

---

## Phase 3: User Story 2 - Use Interactive Aids Accessibly (Priority: P2)

**Goal**: Keyboard and screen-reader-oriented users can use the interactive aids or their static fallbacks without pointer-only or inaccessible dynamic behavior.

**Independent Test**: Navigate the install and lifecycle aids with keyboard review, inspect accessible labels and status text, and verify static fallback content preserves essential guidance on desktop and mobile-sized layouts.

### Validation for User Story 2

- [X] T014 [US2] Add failing DOC-010 guardrails for labels, status regions, keyboard reachability, fallback content, and forbidden local-state behavior in `docs-site/scripts/validate-doc006-safe-aids.mjs` (FR-005, FR-006, FR-011)

### Implementation for User Story 2

- [X] T015 [US2] Update install-aid static fallback and guidance text on `docs-site/src/content/docs/choose-your-path.mdx` so essential guidance remains available without dynamic behavior (FR-005)
- [X] T016 [P] [US2] Improve semantic lifecycle content, fallback readability, focus/reflow behavior, and responsive layout in `docs-site/src/components/LifecycleFlow.astro` (FR-006)
- [X] T017 [US2] Finish `SafeInstallAids.astro` source-backed validation coverage in `docs-site/scripts/validate-doc006-safe-aids.mjs` without executing snippets or reading local user state (FR-005, FR-011)

### Verification for User Story 2

- [X] T018 [US2] Run `pnpm --dir docs-site validate:safe-aids` and confirm `docs-site/scripts/validate-doc006-safe-aids.mjs` reports sanitized repo-relative diagnostics (FR-005, FR-006, FR-011)
- [X] T019 [US2] Record manual keyboard, screen-reader-oriented, responsive, and static fallback evidence using the checklist in `specs/doc-010-search-accessibility-deep-links-docs-validation/quickstart.md` (FR-013)

**Checkpoint**: User Story 2 has validator coverage plus reviewer-visible accessibility evidence.

---

## Phase 4: User Story 3 - Run One Matching Docs Validation Path (Priority: P3)

**Goal**: Maintainers and contributors can run one local validation path, and PR Checks expose a matching `validate-docs` gate using job-level changed-file detection.

**Independent Test**: Run the local docs validation command and confirm PR Checks docs-gate logic distinguishes rendered docs-site changes, generated-reference source changes, docs-validation contract changes, and plugin-only changes without altering plugin matrix semantics.

### Validation for User Story 3

- [X] T020 [US3] Add failing command-chain checks in `docs-site/scripts/validate-docs-quality.mjs` so `docs-site/package.json` must include `reference:check`, `check`, `build`, `validate:safe-aids`, `validate:quality`, and `validate:smoke` under the DOC-010 validation path (FR-007, FR-008)
- [X] T021 [US3] Add failing CI docs-surface detection expectations for rendered docs-site, generated-reference source, docs-validation contract, and plugin-only changes in `.github/workflows/pr-checks.yml` comments or job logic review points (FR-009, FR-011)

### Implementation for User Story 3

- [X] T022 [US3] Update `docs-site/package.json` so `pnpm --dir docs-site validate` runs generated reference checks, Astro checks, build/link validation, safe-aids validation, docs-quality validation, and `validate:smoke` (FR-007, FR-008)
- [X] T023 [US3] Update `.github/workflows/pr-checks.yml` with a stable `validate-docs` job using job-level changed-file detection and successful skip behavior for unrelated changes (FR-009)
- [X] T024 [US3] Keep existing `detect`, `test`, `validate-pr-title`, and `validate-plugins` plugin matrix semantics intact while adding docs validation logic in `.github/workflows/pr-checks.yml` (FR-009)

### Verification for User Story 3

- [X] T025 [US3] Run `pnpm --dir docs-site reference:check` and confirm generated reference drift is caught before review (FR-003, FR-007)
- [X] T026 [US3] Run `pnpm --dir docs-site validate` and confirm the full DOC-010 local validation path includes `validate:smoke` (FR-007, FR-008)
- [X] T027 [US3] Run `bash tests/speckit-pro/run-all.sh --layer 1` after `.github/workflows/pr-checks.yml` or structural spec-marker surfaces change (FR-009, FR-013)

**Checkpoint**: User Story 3 has one local docs validation path and a conditional CI docs gate without plugin matrix fan-out for docs-only changes.

---

## Phase 5: User Story 4 - Review Minimal Browser Evidence (Priority: P4)

**Goal**: Reviewers can inspect compact browser smoke evidence for critical existing docs routes across desktop and mobile without reviewing a broad visual snapshot suite.

**Independent Test**: Run smoke coverage for the six logical routes on desktop and mobile, verify search/deep-link/interactive assertions, and confirm CI publishes compact `docs-site-smoke-evidence` with 7-day retention.

### Validation for User Story 4

- [ ] T028 [US4] Add failing route-load and viewport smoke assertions for `/`, `/choose-your-path/`, `/spec-kit-lifecycle/`, `/glossary/`, `/reference/skills/`, and `/contribute-and-release/` in `docs-site/tests/docs-smoke.spec.mjs` (FR-010)

### Implementation for User Story 4

- [ ] T029 [US4] Implement desktop and mobile route heading or landmark assertions in `docs-site/tests/docs-smoke.spec.mjs` (FR-010)
- [ ] T030 [US4] Implement one support-oriented search smoke from `/` plus representative deep-link samples in `docs-site/tests/docs-smoke.spec.mjs` (FR-002, FR-004, FR-010)
- [ ] T031 [US4] Implement focused `SafeInstallAids` and `LifecycleFlow` smoke checks without browser-side local command execution in `docs-site/tests/docs-smoke.spec.mjs` (FR-005, FR-006, FR-011)
- [ ] T032 [US4] Add `docs-site-smoke-evidence` artifact upload with 7-day retention in `.github/workflows/pr-checks.yml` when smoke artifacts exist (FR-013)

### Verification for User Story 4

- [ ] T033 [US4] Run `pnpm --dir docs-site validate:smoke` and confirm `docs-site/playwright.config.mjs` keeps smoke limited to the configured baseURL, route set, and compact artifacts (FR-010, FR-011, FR-013)

**Checkpoint**: User Story 4 produces compact, bounded smoke evidence for reviewer use.

---

## Phase 6: Polish & Cross-Cutting Verification

**Purpose**: Final validation, generated reference checks, PR evidence, and review packet readiness.

- [ ] T034 Run `pnpm --dir docs-site reference:check` for generated reference drift from `docs-site/scripts/generate-reference-pages.mjs` (FR-003, FR-007)
- [ ] T035 Run `pnpm --dir docs-site validate:quality` and `pnpm --dir docs-site validate:safe-aids` for focused docs quality and safe-aids validation in `docs-site/scripts/` (FR-005, FR-006, FR-007, FR-011, FR-012)
- [ ] T036 Run `pnpm --dir docs-site validate:smoke` for minimal browser smoke coverage in `docs-site/tests/docs-smoke.spec.mjs` (FR-010, FR-013)
- [ ] T037 Run `pnpm --dir docs-site validate` for the complete local DOC-010 docs validation path from `docs-site/package.json` (FR-007, FR-008)
- [ ] T038 Run `git diff --check` for all DOC-010 changes listed in `specs/doc-010-search-accessibility-deep-links-docs-validation/plan.md` (FR-013)
- [ ] T039 Run `bash tests/speckit-pro/run-all.sh --layer 1` because DOC-010 changes `.github/workflows/pr-checks.yml`, docs-site scripts, and validation surfaces (FR-009, FR-013)
- [ ] T040 Prepare PR packet evidence from `specs/doc-010-search-accessibility-deep-links-docs-validation/quickstart.md`, including review order, scope budget, traceability, validation output, manual accessibility evidence, compact smoke artifact summary, known gaps, automation-safety notes, and rollback/fallback notes (FR-011, FR-013)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; establishes command names and validator entrypoints.
- **User Story 1 (Phase 2)**: Depends on Setup. MVP for search, glossary, stable anchors, and source-update validation.
- **User Story 2 (Phase 3)**: Depends on Setup. Can proceed after Setup, but coordinate edits to `docs-site/src/content/docs/choose-your-path.mdx` with US1.
- **User Story 3 (Phase 4)**: Depends on Setup. Can proceed after Setup, but coordinate `docs-site/package.json` edits with Setup and docs-quality validator edits with US1.
- **User Story 4 (Phase 5)**: Depends on Setup. Can proceed after Setup, but coordinate `.github/workflows/pr-checks.yml` edits with US3.
- **Polish (Phase 6)**: Depends on all selected user stories.

### User Story Dependencies

- **User Story 1 (P1)**: MVP; no dependency on other user stories after Setup.
- **User Story 2 (P2)**: Independent after Setup, except shared `choose-your-path.mdx` coordination with US1.
- **User Story 3 (P3)**: Independent after Setup, except shared `package.json`, docs-quality validator, and workflow coordination.
- **User Story 4 (P4)**: Independent after Setup, except shared smoke config and workflow artifact coordination.

### Parallel Opportunities

- **Setup**: T003, T004, and T005 can run in parallel because they create different files.
- **US1**: T009 and T010 can run in parallel after T007-T008 because they touch different docs content files.
- **US2**: T016 can run in parallel with T015 after T014 because it touches a different component file.
- **US3**: T023 and T024 must be coordinated in the same workflow file; do not run them in parallel. Package script work in T022 can be done separately after T020.
- **US4**: Smoke spec tasks T028-T031 all touch the same file and should remain serial. T032 coordinates with US3 workflow edits.
- **Cross-story**: Parallelize only after confirming file ownership, especially for `docs-site/package.json`, `docs-site/scripts/validate-docs-quality.mjs`, `docs-site/src/content/docs/choose-your-path.mdx`, `.github/workflows/pr-checks.yml`, and `docs-site/tests/docs-smoke.spec.mjs`.

---

## Parallel Example: User Story 1

```text
Task: "Add stable glossary term anchors and support-oriented cross-links in docs-site/src/content/docs/glossary.md"
Task: "Add support-link and static fallback anchor guidance for install decisions in docs-site/src/content/docs/choose-your-path.mdx"
```

## Parallel Example: Setup

```text
Task: "Create the focused docs-quality validator entrypoint with repo-relative diagnostics and safety-boundary constants in docs-site/scripts/validate-docs-quality.mjs"
Task: "Create Playwright configuration with local preview baseURL ownership, /racecraft-plugins-public base path handling, desktop/mobile projects, and compact artifact output in docs-site/playwright.config.mjs"
Task: "Create the initial browser smoke spec scaffold with the six logical DOC-010 routes in docs-site/tests/docs-smoke.spec.mjs"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: User Story 1.
3. Stop and validate with `pnpm --dir docs-site validate:quality` and `pnpm --dir docs-site reference:check`.
4. Confirm the MVP preserves non-goals: no new top-level docs route and no new search provider.

### Incremental Delivery

1. Add User Story 1 for searchable and shareable support anchors.
2. Add User Story 2 for accessible interactive aids and static fallback evidence.
3. Add User Story 3 for the single validation path and `validate-docs` PR gate.
4. Add User Story 4 for compact browser smoke evidence.
5. Finish Phase 6 verification and PR packet evidence.

### Non-goals To Preserve

- Do not add a new top-level docs route.
- Do not add a new search provider.
- Do not add a full visual snapshot suite.
- Do not add live install tests in CI.
- Do not add browser-side local command execution or user JSON inspection.

---

## Traceability

| Requirement | Covered by tasks |
|-------------|------------------|
| FR-001 | T006, T040 |
| FR-002 | T007, T010, T011, T030 |
| FR-003 | T007, T009, T011, T013, T025, T034 |
| FR-004 | T009, T010, T030 |
| FR-005 | T014, T015, T017, T018, T031, T035 |
| FR-006 | T014, T016, T018, T031, T035 |
| FR-007 | T001, T003, T007, T011, T012, T013, T020, T022, T025, T026, T034, T035, T037 |
| FR-008 | T001, T020, T022, T026, T037 |
| FR-009 | T021, T023, T024, T027, T039 |
| FR-010 | T002, T004, T005, T028, T029, T030, T031, T033, T036 |
| FR-011 | T003, T012, T014, T017, T018, T021, T031, T033, T035, T040 |
| FR-012 | T007, T008, T011, T012, T035 |
| FR-013 | T004, T006, T019, T027, T032, T033, T036, T038, T039, T040 |
