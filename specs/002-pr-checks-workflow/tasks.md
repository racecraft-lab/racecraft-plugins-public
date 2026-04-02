# Tasks: PR Checks Workflow

**Input**: Design documents from `/specs/002-pr-checks-workflow/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No new test files are required for this feature. The workflow is validated by running it on a real PR and verifying existing tests still pass.

**Organization**: Tasks are grouped by job (validate-plugins pipeline, validate-pr-title) aligned to user stories for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Workflow Skeleton)

**Purpose**: Create the workflow file with triggers, permissions, and shell defaults (FR-001, FR-008, FR-009, FR-010)

- [ ] T001 Create workflow file `.github/workflows/pr-checks.yml` with workflow `name: PR Checks`, trigger `on.pull_request.types: [opened, reopened, synchronize, edited, ready_for_review]`, top-level `permissions: {}`, and `defaults.run.shell: bash`
- [ ] T002 Look up the latest stable SHA for `actions/checkout` and record it for use in FR-008 pinned action versions (determine current version at implementation time)

**Checkpoint**: Workflow file exists with correct triggers, permissions, and shell defaults. YAML is valid.

---

## Phase 2: Foundational (Job Stubs)

**Purpose**: Add all three job stubs with draft-skip conditions and correct dependency wiring so the workflow structure is complete before implementing job logic

- [ ] T003 Add `detect` job stub in `.github/workflows/pr-checks.yml` with `runs-on: ubuntu-latest`, `if: github.event.pull_request.draft == false`, `permissions: contents: read`, `outputs.plugins` declaration, and placeholder step
- [ ] T004 Add `test` job stub in `.github/workflows/pr-checks.yml` with `name: test (${{ matrix.plugin }})`, `runs-on: ubuntu-latest`, `if: needs.detect.outputs.plugins != '[]'`, `needs: [detect]`, `permissions: contents: read`, `strategy.matrix.plugin: ${{ fromJSON(needs.detect.outputs.plugins) }}`, `strategy.fail-fast: false`, and placeholder step (FR-006, FR-018)
- [ ] T005 Add `validate-pr-title` job stub in `.github/workflows/pr-checks.yml` with `runs-on: ubuntu-latest`, `if: github.event.pull_request.draft == false`, `permissions: {}`, and placeholder step (FR-005 -- no `needs:` dependency on detect/test pipeline)

**Checkpoint**: All three jobs defined with correct conditions, dependencies, and permissions. YAML is valid. No job logic yet.

---

## Phase 3: User Story 1 - Changed Plugin Test Execution (Priority: P1) -- MVP

**Goal**: Detect changed plugin directories and run their test suites independently via dynamic matrix

**Independent Test**: Open a PR modifying files in `speckit-pro/` and verify CI runs `bash tests/run-all.sh` for that plugin

### Implementation for User Story 1

- [ ] T006 [US1] Implement detect job plugin detection step in `.github/workflows/pr-checks.yml`: checkout with `fetch-depth: 0` using SHA-pinned `actions/checkout`, inline bash script with `set -euo pipefail` that runs `git diff --name-only origin/${{ github.base_ref }}...HEAD`, extracts unique top-level directories via `cut -d'/' -f1 | sort -u`, filters to directories containing `.claude-plugin/plugin.json`, and sets the `plugins` output as a JSON array using `jq` (FR-002, FR-010, FR-011, FR-014)
- [ ] T007 [US1] Implement detect job logging in `.github/workflows/pr-checks.yml`: log `Changed plugin directories: ...` when plugins are found, or `No plugin directories changed in this PR. Test job will be skipped.` when none are found (FR-019)
- [ ] T008 [US1] Implement test job steps in `.github/workflows/pr-checks.yml`: checkout with `fetch-depth: 0` using SHA-pinned `actions/checkout`, inline bash script with `set -euo pipefail` that validates `${{ matrix.plugin }}/tests/run-all.sh` exists with `::error::` annotation and human-readable error message on missing (exit 2, FR-012, FR-017, FR-020), then execute `bash tests/run-all.sh` from the plugin directory (FR-003, FR-010)
- [ ] T009 [US1] Pass `github.base_ref` to the detect job script via `env: BASE_REF: ${{ github.base_ref }}` and reference as `"$BASE_REF"` in the script body for consistency with FR-013 script injection prevention pattern

**Checkpoint**: detect + test pipeline is complete. Plugin changes trigger scoped test execution. Empty plugin changes skip the test job.

---

## Phase 4: User Story 2 - PR Title Conventional Commit Validation (Priority: P1)

**Goal**: Validate PR title matches Conventional Commits format for release-please compatibility

**Independent Test**: Open a PR with title `Update readme` and verify the check fails; update to `docs: update readme` and verify it passes

### Implementation for User Story 2

- [ ] T010 [P] [US2] Implement validate-pr-title job step in `.github/workflows/pr-checks.yml`: pass title via `env: TITLE: ${{ github.event.pull_request.title }}` (FR-013), inline bash script with `set -euo pipefail` that matches `"$TITLE"` against regex `^(feat|fix|chore|docs|refactor|test)(\(.+\))?!?: .+$` stored in a `PATTERN` variable, echo success message on match (FR-004, FR-010)

**Checkpoint**: Title validation works for both valid and invalid titles. Script injection prevention is in place.

---

## Phase 5: User Story 3 - Clear Error Messages for Contributors (Priority: P2)

**Goal**: Provide actionable error output when PR title validation fails

**Independent Test**: Open a PR with an invalid title and verify the error output includes the rejected title, expected format, valid types, and at least one example

### Implementation for User Story 3

- [ ] T011 [US3] Implement error message output in the validate-pr-title job failure branch in `.github/workflows/pr-checks.yml`: emit `::error::` annotation (FR-020), echo the rejected title with `Your title: "$TITLE"` (FR-016), show expected format pattern, list valid type prefixes, and provide concrete examples per the error template in contracts/workflow-contract.md (FR-007, SC-005)

**Checkpoint**: Error messages contain all four required elements: rejected title, format pattern, valid types, examples.

---

## Phase 6: User Story 4 - Skip Testing for Non-Plugin Changes (Priority: P2)

**Goal**: CI completes quickly for docs-only PRs by skipping test execution

**Independent Test**: Open a PR modifying only `README.md` and verify the test job is skipped while validate-pr-title still runs

### Implementation for User Story 4

- [ ] T012 [US4] Verify the `if: needs.detect.outputs.plugins != '[]'` condition on the test job in `.github/workflows/pr-checks.yml` correctly causes the job to be skipped when the detect job outputs an empty array `[]` (FR-006). This should already work from T004 + T006; this task is explicit verification and any fix if needed

**Checkpoint**: Docs-only PRs complete CI without running any plugin test suites.

---

## Phase 7: Validation & Polish

**Purpose**: End-to-end validation and cross-cutting concerns

- [ ] T013 Validate workflow YAML syntax by running `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pr-checks.yml'))"` or equivalent YAML linter
- [ ] T014 Verify all existing tests still pass by running `bash speckit-pro/tests/run-all.sh` from the repository root
- [ ] T015 Review `.github/workflows/pr-checks.yml` against the full FR list (FR-001 through FR-020) and SC list (SC-001 through SC-006) to confirm complete coverage
- [ ] T016 Verify `actions/checkout` is SHA-pinned with a version comment in `.github/workflows/pr-checks.yml` (FR-008)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies -- can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 -- BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 -- detect + test pipeline
- **US2 (Phase 4)**: Depends on Phase 2 -- can run in PARALLEL with US1 [P]
- **US3 (Phase 5)**: Depends on Phase 4 (US2) -- extends the title validation error branch
- **US4 (Phase 6)**: Depends on Phase 3 (US1) -- verifies empty matrix skip behavior
- **Validation (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 -- no dependencies on other stories
- **User Story 2 (P1)**: Can start after Phase 2 -- no dependencies on other stories [P] with US1
- **User Story 3 (P2)**: Depends on US2 (extends the error branch of title validation)
- **User Story 4 (P2)**: Depends on US1 (verifies the detect+test skip behavior)

### Within Each User Story

- Core logic before error handling
- Script injection prevention before title matching
- Detection before test execution

### Parallel Opportunities

- T003, T004, T005 (job stubs) can be created in parallel within Phase 2
- US1 (Phase 3) and US2 (Phase 4) can be implemented in parallel -- they modify different jobs in the same file but different sections
- T013 and T014 (validation tasks) can run in parallel [P]

---

## Parallel Example: Phase 3 + Phase 4

```bash
# US1 and US2 modify independent job sections in pr-checks.yml:
Task: "T006 [US1] Implement detect job plugin detection step"
Task: "T010 [US2] Implement validate-pr-title job step"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (workflow skeleton)
2. Complete Phase 2: Foundational (job stubs with wiring)
3. Complete Phase 3: US1 -- detect + test pipeline
4. Complete Phase 4: US2 -- title validation
5. **STOP and VALIDATE**: Both core jobs functional
6. Push branch, open PR to trigger workflow self-test

### Incremental Delivery

1. Setup + Foundational -> Workflow structure ready
2. Add US1 -> Plugin test detection works -> MVP for test scoping
3. Add US2 -> Title validation works -> MVP for commit enforcement
4. Add US3 -> Error messages improved -> Better contributor experience
5. Add US4 -> Skip behavior verified -> Efficiency optimization
6. Validation phase -> Full coverage confirmed

---

## Notes

- [P] tasks = different files or independent sections, no dependencies
- [Story] label maps task to specific user story for traceability
- Single file deliverable: all tasks modify `.github/workflows/pr-checks.yml`
- No new test files needed -- workflow is validated by running on a real PR
- Commit after each phase for clean git history
