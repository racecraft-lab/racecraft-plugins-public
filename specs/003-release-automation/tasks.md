# Tasks: Release Automation

**Input**: Design documents from `/specs/003-release-automation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No new test files are required for this workflow. Existing tests at `speckit-pro/tests/` are used for regression validation only.

**Organization**: Tasks are grouped by workflow step (foundation, release-please, marketplace sync, validation) per the user-specified structure, with user story traceability via FR-xxx references.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Workflow file**: `.github/workflows/release.yml` (single deliverable)
- **Existing configs**: `release-please-config.json`, `.release-please-manifest.json` (NOT modified)
- **Existing script**: `scripts/sync-marketplace-versions.sh` (NOT modified)

---

## Phase 1: Foundation (Workflow Skeleton)

**Purpose**: Create the workflow file with trigger, permissions, concurrency, and job scaffold

- [x] T001 Create `.github/workflows/` directory and workflow file `.github/workflows/release.yml` with workflow `name: Release`, trigger `on: push: branches: [main]`, permissions block (`contents: write`, `pull-requests: write` per FR-007/SEC-002), concurrency group (`release-${{ github.ref_name }}` with `cancel-in-progress: false` per FR-015), and job scaffold (`release` job with `runs-on: ubuntu-latest` and `timeout-minutes: 10` per FR-013)

**Checkpoint**: Workflow file exists with valid YAML structure, correct trigger, permissions, concurrency, and empty steps array. Validate with `python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"` or equivalent YAML linter.

---

## Phase 2: Release-Please Step (US1, US2, US5)

**Purpose**: Add the release-please action step that handles Release PR creation, version bumps, changelog generation, GitHub Release creation, and tag generation

**Goal**: When a conventional commit is pushed to main, release-please opens/updates a Release PR (US1). When a Release PR is merged, release-please creates a GitHub Release with a component-prefixed tag (US2). The workflow uses GITHUB_TOKEN to prevent infinite loops (US5).

**Independent Test**: Push a `feat:` commit to main after merging the workflow -- verify a Release PR is opened with correct version bump and changelog.

- [x] T002 [US1] [US2] [US5] Add release-please action step to `.github/workflows/release.yml`: step with `id: release`, `uses: googleapis/release-please-action@v4` (FR-002/FR-008), no additional `with:` inputs needed (release-please reads `release-please-config.json` and `.release-please-manifest.json` automatically per FR-009). Verify the step ID is `release` for output references (FR-011). No user-controlled values are interpolated into shell commands (SEC-001).

**Checkpoint**: Workflow has release-please step with correct action version and step ID. YAML remains valid. The step references existing config files without modification.

**Acceptance criteria**:
- FR-001: Workflow triggers on push to main
- FR-002: release-please-action@v4 is the first step
- FR-003: Tag format derives from component field in config (e.g., `speckit-pro-v1.1.0`)
- FR-008: Action pinned to `@v4`
- FR-009: Uses existing config files
- FR-010: Everything in single workflow file
- FR-011: Outputs use `speckit-pro--` prefix format

---

## Phase 3: Marketplace Sync Step (US3, US4, US5)

**Purpose**: Add conditional marketplace sync steps that run only when a release is created, update marketplace.json, and commit/push with loop-prevention safeguards

**Goal**: After a release is created, the sync script updates marketplace.json (US3). The sync only runs when `release_created` is true, not on regular pushes (US4). The sync commit uses `chore:` prefix and `[skip ci]` to prevent infinite loops (US5).

**Independent Test**: After a release is created, verify marketplace.json is updated. After a regular push (no release), verify the sync step is skipped.

- [x] T003 [US3] [US4] Add conditional checkout step to `.github/workflows/release.yml`: `actions/checkout@v4` (FR-008) with `if: steps.release.outputs['speckit-pro--release_created'] == 'true'` condition (FR-004/FR-006/FR-011). Default `persist-credentials: true` provides GITHUB_TOKEN for subsequent push (SEC-004). No `ref:` override needed -- checks out the commit that triggered the workflow.

- [x] T004 [US3] Add sync script execution step to `.github/workflows/release.yml`: `run: bash scripts/sync-marketplace-versions.sh` with same `if` condition as T003 (FR-004). The script is registry-driven and handles all plugins (FR-004). No modifications to the script itself.

- [x] T005 [US3] [US5] Add git identity configuration, diff check, commit, and push step to `.github/workflows/release.yml`: configure git user as `github-actions[bot]` with email `41898282+github-actions[bot]@users.noreply.github.com` (per research.md decision 5). Check `git diff --quiet .claude-plugin/marketplace.json` -- if changes exist, run `git add .claude-plugin/marketplace.json && git commit -m "chore: sync marketplace.json versions [skip ci]" && git push` (FR-005/FR-012). Same `if` condition as T003. Commit message is hardcoded string literal, not interpolated from user input (SEC-001/SEC-003). Uses GITHUB_TOKEN via persisted checkout credentials for push (FR-007/SEC-004).

**Checkpoint**: Workflow has complete sync pipeline: conditional checkout, sync script execution, and guarded commit/push. All sync steps share the same `if` condition. YAML remains valid. No existing files modified.

**Acceptance criteria**:
- FR-004: Sync conditioned on `speckit-pro--release_created`
- FR-005: Commit message is exactly `chore: sync marketplace.json versions [skip ci]`
- FR-006: Sync skipped when release-please only updates a Release PR
- FR-007: `contents: write` permission enables push
- FR-011: Uses path-prefixed output variable with bracket notation
- FR-012: Default `continue-on-error: false` ensures failure visibility
- SEC-001: No user-controlled values in `run:` blocks
- SEC-003: No token logging; sync script uses `set -euo pipefail` without `set -x`

---

## Phase 4: Validation

**Purpose**: Verify the complete workflow is correct and existing tests still pass

- [x] T006 [P] Validate `.github/workflows/release.yml` YAML syntax using a YAML parser (e.g., `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"`) and verify all required fields are present: `name`, `on.push.branches`, `permissions.contents`, `permissions.pull-requests`, `concurrency.group`, `concurrency.cancel-in-progress`, `jobs.release.runs-on`, `jobs.release.timeout-minutes`, and all step IDs/conditions

- [x] T007 [P] Run existing test suite `bash speckit-pro/tests/run-all.sh` from the repository root to verify no regressions from the workflow file addition

- [x] T008 Review `.github/workflows/release.yml` against all functional requirements (FR-001 through FR-015), security requirements (SEC-001 through SEC-004), and the workflow contract in `specs/003-release-automation/contracts/workflow-contract.md` -- verify every requirement is satisfied

- [x] T009 Verify the workflow does not modify any SPEC-001 files: `release-please-config.json`, `.release-please-manifest.json`, `scripts/sync-marketplace-versions.sh`, `.claude-plugin/marketplace.json`, `speckit-pro/.claude-plugin/plugin.json` -- confirm these files are unchanged in the git diff

---

## Phase 5: Polish and Cross-Cutting Concerns

**Purpose**: Documentation updates and final cleanup

- [x] T010 Update `CLAUDE.md` at repository root if any new CI-specific patterns need documentation (e.g., workflow file location, how to manually re-run the release workflow). Only add entries if genuinely needed per the constraint.

- [x] T011 Run quickstart verification: walk through each step in `specs/003-release-automation/quickstart.md` and confirm the implementation matches the documented steps and file inventory

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 (Foundation)**: No dependencies -- can start immediately
- **Phase 2 (Release-Please Step)**: Depends on Phase 1 (T001 must complete before T002)
- **Phase 3 (Marketplace Sync Step)**: Depends on Phase 2 (T002 must complete before T003-T005)
  - T003, T004, T005 are sequential within Phase 3 (all modify the same file in order)
- **Phase 4 (Validation)**: Depends on Phase 3 (all implementation must be complete)
  - T006 and T007 are parallel [P] (different validation targets)
  - T008 depends on T006 passing (YAML must be valid before requirement review)
  - T009 depends on T006 passing
- **Phase 5 (Polish)**: Depends on Phase 4 (validation must pass first)

### User Story Dependencies

- **US1 (Release PR Creation, P1)**: Covered by T001 + T002 -- foundational, no dependencies on other stories
- **US2 (GitHub Release and Tag, P1)**: Covered by T002 -- same step as US1 (release-please handles both)
- **US3 (Marketplace Sync, P2)**: Covered by T003 + T004 + T005 -- depends on US1/US2 outputs
- **US4 (Conditional Sync, P2)**: Covered by T003 condition -- depends on US1/US2 outputs
- **US5 (No Infinite Loop, P1)**: Covered by T001 (GITHUB_TOKEN permissions) + T005 (chore: commit message) -- cross-cutting

### Within Each Phase

- Phase 1: Single task (T001)
- Phase 2: Single task (T002), depends on T001
- Phase 3: Sequential tasks (T003 -> T004 -> T005), all modify same file
- Phase 4: T006 [P] and T007 [P] can run in parallel; T008 and T009 depend on T006
- Phase 5: T010 and T011 can proceed independently

### Parallel Opportunities

- T006 and T007 in Phase 4 can run in parallel (YAML validation vs test suite)
- T010 and T011 in Phase 5 can proceed independently
- All other tasks are sequential due to single-file delivery constraint

---

## Parallel Example: Phase 4 Validation

```bash
# Launch validation tasks in parallel:
Task T006: "Validate release.yml YAML syntax and required fields"
Task T007: "Run existing test suite for regression check"

# Then sequentially:
Task T008: "Review against all FR/SEC requirements" (after T006 passes)
Task T009: "Verify no SPEC-001 files modified" (after T006 passes)
```

---

## Implementation Strategy

### MVP First (Phases 1-3)

1. Complete Phase 1: Create workflow skeleton (T001)
2. Complete Phase 2: Add release-please step (T002)
3. Complete Phase 3: Add marketplace sync steps (T003-T005)
4. **STOP and VALIDATE**: Run Phase 4 checks before committing

### Incremental Delivery

1. T001 -> Workflow file exists with valid structure
2. T002 -> Release-please automation is functional (US1, US2 deliverable)
3. T003-T005 -> Full pipeline with marketplace sync (US3, US4, US5 deliverable)
4. T006-T009 -> Validated and regression-checked
5. T010-T011 -> Documentation aligned

### Single-Developer Flow

All tasks are sequential for a single developer working on a single file. The total estimated effort is 1-2 hours for the entire feature, given that the workflow is a single YAML file leveraging existing infrastructure.

---

## Notes

- All tasks modify or validate a single file: `.github/workflows/release.yml`
- No new scripts, no new test files, no modifications to SPEC-001 artifacts
- The workflow is tested via GitHub Actions integration (push to main), not via local unit tests
- Existing test suite (`bash speckit-pro/tests/run-all.sh`) is run for regression only
- Total: 11 tasks across 5 phases covering all 5 user stories and 15 functional requirements
