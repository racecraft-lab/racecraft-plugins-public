# Tasks: Repository Foundation for CI/CD Pipeline

**Feature Branch**: `001-repository-foundation`
**Generated**: 2026-03-24
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Phase 1: Foundation (release-please config files)

**Goal**: Establish the release-please configuration files that enable automated versioning for all plugins.

**Independent Test**: Validate both config files are valid JSON with correct structure and values matching current plugin.json versions.

- [ ] T001 [P] Create `release-please-config.json` at repository root with `speckit-pro` package entry using `release-type: "simple"`, `bump-minor-pre-major: true`, and `extra-files` GenericJson updater targeting `.claude-plugin/plugin.json` at `$.version` (FR-001, FR-002, FR-003)
- [ ] T002 [P] Create `.release-please-manifest.json` at repository root pre-populated with `{"speckit-pro": "1.0.0"}` matching current `speckit-pro/.claude-plugin/plugin.json` version (FR-004)

## Phase 2: Sync Script (scripts/sync-marketplace-versions.sh)

**Goal**: Implement the marketplace version sync script that reads plugin.json versions and updates marketplace.json entries.

**Independent Test**: Run script against repo with intentionally mismatched versions and verify marketplace.json is corrected.

**Depends on**: None (independent of Phase 1)

- [ ] T003 Create `scripts/` directory at repository root and create `scripts/sync-marketplace-versions.sh` with shebang `#!/usr/bin/env bash`, `set -euo pipefail`, and `chmod +x` (FR-007)
- [ ] T004 Implement prerequisite checks: jq dependency detection via `command -v jq` and working directory validation via `.claude-plugin/marketplace.json` existence check, with error messages to stderr (FR-007, FR-008a)
- [ ] T005 Implement marketplace.json parsing: validate `plugins` array exists via `jq -e`, handle empty array with informational stderr message and exit 0 (FR-005, FR-006)
- [ ] T006 Implement plugin iteration loop: extract `source` field from each entry, skip non-relative sources with stderr message, resolve relative paths to `<source>/.claude-plugin/plugin.json`, exit with error if source field missing (FR-005, FR-008)
- [ ] T007 Implement version reading and validation: read `version` field from each plugin.json, validate semver pattern `^[0-9]+\.[0-9]+\.[0-9]+$`, exit with descriptive error on missing file/field/invalid semver (FR-005, FR-008, FR-008a)
- [ ] T008 Implement in-memory JSON update: build complete updated marketplace.json using `jq --arg` for version injection, preserving all existing fields and key ordering (FR-005, FR-006)
- [ ] T009 Implement idempotent write: compare updated JSON with existing file content, skip write if identical, print sync summary to stdout only when changes made (FR-009, FR-008a)

## Phase 3: Tests (Layer 4 unit tests for sync script)

**Goal**: Create comprehensive unit tests for the sync script covering happy-path and error scenarios.

**Independent Test**: Run test suite via `bash speckit-pro/tests/run-all.sh --layer 4` and verify all assertions pass.

**Depends on**: Phase 2 (sync script must exist to test)

- [ ] T010 Create `speckit-pro/tests/layer4-scripts/test-sync-marketplace-versions.sh` with shebang, `set -euo pipefail`, shared assertions library source, temp fixture directory with trap cleanup (FR-010, FR-011)
- [ ] T011 [P] Implement test: version mismatch correction -- fixture with plugin.json at 0.6.0 and marketplace.json at 0.5.0, assert marketplace updated to 0.6.0 (FR-012)
- [ ] T012 [P] Implement test: already-matching versions (no-op) -- fixture with matching versions, assert marketplace.json unchanged and no stdout output (FR-012)
- [ ] T013 [P] Implement test: missing plugin.json error handling -- fixture with marketplace entry but no plugin.json file, assert non-zero exit and stderr error message (FR-012)
- [ ] T014 [P] Implement test: multi-plugin sync -- fixture with 2+ plugins having different version mismatches, assert all corrected independently (FR-012)
- [ ] T015 [P] Implement test: malformed JSON input -- fixture with invalid marketplace.json, assert non-zero exit; separate fixture with invalid plugin.json, assert non-zero exit (FR-012)
- [ ] T016 [P] Implement test: missing jq dependency detection -- temporarily override PATH to hide jq, assert non-zero exit and stderr error message (FR-012)
- [ ] T017 [P] Implement test: wrong working directory detection -- run script from temp dir without marketplace.json, assert non-zero exit and stderr error message (FR-012)
- [ ] T018 [P] Implement test: non-relative source skipping -- fixture with external git repo source entry, assert entry is skipped without error (FR-012)
- [ ] T019 [P] Implement test: missing version field in plugin.json -- fixture with plugin.json without version field, assert non-zero exit and stderr error message (FR-012)
- [ ] T020 [P] Implement test: invalid semver format in plugin.json -- fixture with version "1.0" or "abc", assert non-zero exit and stderr error message (FR-012)
- [ ] T021 [P] Implement test: stderr-only error output -- for each error scenario, assert stdout is empty and stderr contains error message (FR-012)
- [ ] T022 [P] Implement test: all error scenarios exit with code 1 -- verify each error test uses assert_eq for exit code 1 specifically (FR-012)

## Phase 4: Validation (end-to-end verification)

**Goal**: Verify all artifacts work together and existing tests still pass.

**Independent Test**: Full test suite passes, sync script works against real repo, release-please configs are valid.

**Depends on**: Phase 1, Phase 2, Phase 3

- [ ] T023 Run `bash speckit-pro/tests/run-all.sh` to verify all existing tests (Layers 1, 4, 5) still pass with new artifacts in place
- [ ] T024 Run `bash scripts/sync-marketplace-versions.sh` against the real repository and verify it is a no-op (versions already match, exit 0, no file changes)
- [ ] T025 Validate `release-please-config.json` and `.release-please-manifest.json` are valid JSON with correct structure via `jq . release-please-config.json` and `jq . .release-please-manifest.json`
- [ ] T026 Verify `scripts/sync-marketplace-versions.sh` has executable permission (`chmod +x` applied)

## Dependencies

```text
Phase 1 (T001-T002) ──┐
                       ├──> Phase 4 (T023-T026)
Phase 2 (T003-T009) ──┤
         │             │
         v             │
Phase 3 (T010-T022) ──┘
```

- Phase 1 and Phase 2 are independent and can execute in parallel
- Phase 3 depends on Phase 2 (script must exist before testing)
- Phase 4 depends on all prior phases (integration verification)

## Parallel Execution Opportunities

| Phase | Parallel Tasks | Notes |
|-------|---------------|-------|
| Phase 1 | T001, T002 | Independent config files, no shared state |
| Phase 2 | None | Sequential dependency chain (each step builds on previous) |
| Phase 3 | T011-T022 | All test functions are independent after T010 scaffold |
| Phase 4 | None | Sequential validation checks |
| Cross-phase | Phase 1 + Phase 2 | Can execute simultaneously |

## Implementation Strategy

**MVP Scope**: Phase 1 + Phase 2 (T001-T009) -- delivers the configuration files and sync script, which is the minimum viable foundation for CI/CD versioning. Phase 3 adds test coverage, Phase 4 confirms integration.

**Incremental Delivery**:
1. Phase 1: Ship config files (reviewable independently)
2. Phase 2: Ship sync script (testable manually)
3. Phase 3: Ship tests (automated regression protection)
4. Phase 4: Final validation pass

**Total Tasks**: 26
**Estimated Duration**: Phase 1 (~30 min), Phase 2 (~2 hours), Phase 3 (~2 hours), Phase 4 (~30 min)
