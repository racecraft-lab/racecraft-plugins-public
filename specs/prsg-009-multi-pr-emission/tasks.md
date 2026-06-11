# Tasks: PRSG-009 multi-PR emission

**Input**: Design documents from `specs/prsg-009-multi-pr-emission/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`

**Tests**: Required for every new or changed bash script behavior. Add RED Layer 4 tests before implementation tasks that make them pass.

**Reviewability**: Infra exception accepted by the plan because this change coordinates SpecKit workflow scripts, fixtures, reviewer docs, and Claude/Codex parity mirrors under one durable state contract. Keep implementation bounded to the declared autopilot script/reference surfaces and do not add PRSG-010 routing heuristics.

Reviewability-Exception: infra

**Organization**: Tasks are grouped by foundation, user story, and polish so each user story remains independently testable after the shared foundation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches a different file or independent fixture set.
- **[Story]**: Required only for user-story phase tasks.
- Every task includes exact file paths and FR references.

## Scope Guardrails

- Consume PRSG-008 `plan-layers.sh` output; do not add PRSG-010 review-routing, atomicity, or slicing heuristics.
- Do not modify `.github/workflows/pr-checks.yml` for scoped CI.
- Do not use `gh-stack` for required PR creation; keep explicit `gh pr create --base --head --body-file`.
- Preserve Claude/Codex parity for mirrored behavior and refresh `dist/` mirrors when source plugin files change.
- Add developer-local Layer 3 functional eval coverage for the roadmap's multi-PR emission e2e expectation.
- Layer 7 is not planned because no new agent or dispatch graph behavior is introduced; record the not-applicable evidence during Polish.

---

## Phase 1: Foundation - contracts, fixtures, and state envelope

**Purpose**: Create the test and script foundation used by all three user stories.

- [x] T001 [P] Add PRSG-009 fixture roots for valid and invalid layer plans, slice packets, PRS manifests, emission state, scoped verification, and restack cases in `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/` (FR-001a, FR-008a, FR-010a, FR-015c, FR-017b)
- [x] T002 [P] Add RED Layer 4 tests for backward-compatible positional PR body generation plus invalid `--slice-packet` handling in `tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh` (FR-015a, FR-015c)
- [x] T003 [P] Add RED Layer 4 tests for schemaVersion 1 compatibility and schemaVersion 2 PRS row rendering in `tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh` (FR-008a, FR-008b, FR-009a)
- [x] T004 [P] Add RED Layer 4 tests for layer-plan validation, duplicate state-key rejection, candidate JSON writes, and resume-safe state shape in `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh` (FR-001a, FR-001b, FR-010a, FR-010b, FR-010c)
- [x] T005 [P] Add RED Layer 4 tests for dry-run default, CLI validation, output schema, and deterministic stderr in `tests/speckit-pro/layer4-scripts/test-restack.sh` (FR-017b, FR-017c, FR-017d)
- [x] T006 Create executable `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` with `#!/usr/bin/env bash`, `set -euo pipefail`, usage validation, jq availability checks, schema path constants, and no branch/PR mutation yet (FR-001a, FR-010c)
- [x] T007 Create executable `speckit-pro/skills/speckit-autopilot/scripts/restack.sh` with `#!/usr/bin/env bash`, `set -euo pipefail`, dry-run default, required option parsing, fixed exit-code names, and no mutation without `--apply` (FR-017b, FR-017c, FR-017d)
- [x] T008 Record the reviewability checkpoint and no-PRSG-010 scope boundary in `docs/ai/specs/.process/PRSG-009-workflow.md` before implementation begins (FR-002, PR Review Packet Requirements)

**Checkpoint**: Shared test fixtures and script entry points exist; user-story work can start.

---

## Phase 2: US1 - Emit ordered slice PRs from the PRSG-008 layer plan

**Goal**: Emit one Style B incremental-stack PR per PRSG-008 layer-plan increment, preserving order and declared file scope.

**Independent Test**: Run the multi-PR emission Layer 4 fixture with a valid three-slice plan and confirm branch/base order, explicit PR create args, and declared scope match the layer plan.

### Tests for US1

- [x] T009 [US1] Add RED Layer 4 assertions for valid three-slice and single-slice layer plans in `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh` (FR-001, FR-003, FR-004, FR-005, SC-001)
- [x] T010 [US1] Add RED Layer 4 assertions for invalid or input-error layer-plan statuses, warning preservation, explicit `gh pr create --base --head --body-file`, and declared file-scope guarding in `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh` (FR-001b, FR-004a, FR-006, SC-001)

### Implementation for US1

- [x] T011 [US1] Implement PRSG-008 layer-plan envelope parsing and status handling in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` (FR-001, FR-001a, FR-001b, FR-002)
- [x] T012 [US1] Implement deterministic slice ID slugging, zero-padded branch names, and `git check-ref-format --branch` validation in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` (FR-007, FR-007a)
- [x] T013 [US1] Implement Style B branch/base planning so slice 1 targets the integration base and later slices target the previous slice branch in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` (FR-004, SC-001)
- [x] T014 [US1] Implement slice branch creation/push stubs, declared file-scope validation, explicit PR body-file handoff, and explicit `gh pr create --base --head --body-file` invocation in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` (FR-004a, FR-005, FR-006)
- [x] T015 [US1] Require pre-emission full regression evidence and copy its path into each slice packet from `specs/prsg-009-multi-pr-emission/.process/emission/` in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` (FR-003, FR-016c, SC-004)
- [x] T016 [US1] Run the focused US1 Layer 4 fixture path and record command output in `docs/ai/specs/.process/PRSG-009-workflow.md` (FR-001, FR-004, FR-005, SC-001)

**Checkpoint**: US1 emits the correct ordered stack plan and PR creation contract without adding new slicing rules.

---

## Phase 3: US2 - Persist PR table, per-slice PR bodies, and resume evidence

**Goal**: After each successful slice PR, update durable reviewer and machine state so interruption and resume do not duplicate work.

**Independent Test**: Interrupt after a successful slice PR in the fixture and verify resume reconciles existing PR state, backfills missing reviewer surfaces, and continues with the next pending slice.

### Tests for US2

- [x] T017 [US2] Add RED Layer 4 assertions for valid slice-packet PR body sections, full regression evidence rendering, and invalid packet exit code 2 in `tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh` (FR-015a, FR-015c, FR-015d, FR-016c, SC-004)
- [x] T018 [US2] Add RED Layer 4 assertions for schemaVersion 2 PRS table columns, link-free rendering, open `head_sha`, merged `merged_sha`, and v1 backward compatibility in `tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh` (FR-008a, FR-008b, FR-009, FR-009a, SC-002)
- [x] T019 [US2] Add RED Layer 4 assertions for successful-slice persistence order, resume reconciliation, closed PR blocking, `gh pr create` failure reconciliation, and post-PR PRS/MOC/workflow persistence failure in `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh` (FR-010d, FR-011a, FR-011b, FR-011c, FR-011d, FR-011e, SC-002)

### Implementation for US2

- [x] T020 [US2] Extend `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh` to accept optional `--slice-packet <json-file>`, validate packet JSON, and preserve existing positional single-PR behavior (FR-015a, FR-015c)
- [x] T021 [US2] Render `Slice summary`, `Review order`, `Scope`, `Verification`, `Traceability`, `Restack or rollback`, `Known gaps`, and `Full regression evidence` sections from slice packets in `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh` (FR-015d, FR-016, FR-016a, FR-016c)
- [x] T022 [US2] Extend `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh` to render schemaVersion 2 `.process/prs.json` rows while keeping schemaVersion 1 behavior intact (FR-008a, FR-008b, FR-009, FR-009a)
- [x] T023 [US2] Implement same-directory temp-file writes, jq validation, schema checks, and uniqueness checks for `docs/ai/specs/.process/autopilot-state.json` and `specs/prsg-009-multi-pr-emission/.process/prs.json` in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` (FR-010a, FR-010b, FR-010c)
- [x] T024 [US2] Implement successful-slice persistence order, PR lookup by expected head/base, PRS manifest update, Spec MOC regeneration, workflow evidence update, and `next_slice_id` advancement in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` (FR-008, FR-010, FR-010d, SC-002)
- [x] T025 [US2] Implement resume reconciliation for expected local branches, remote branches, open/closed/merged PRs, stale `.process/prs.json`, stale `SPEC-MOC.md`, and stale workflow evidence in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` (FR-011, FR-011a, FR-011b, FR-011c)
- [x] T026 [US2] Implement `gh pr create` failure reconciliation and post-PR reviewer-surface failure blocking in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` (FR-011d, FR-011e, FR-019)
- [x] T027 [US2] Run the focused US2 Layer 4 fixture path and record PRS/MOC/state evidence in `docs/ai/specs/.process/PRSG-009-workflow.md` (FR-008, FR-010, FR-011, SC-002)

**Checkpoint**: US2 can persist and resume slice PR emission without duplicate PRs or stale reviewer navigation.

---

## Phase 4: US3 - Define topology, scoped CI mapping, and restack behavior

**Goal**: Record scoped verification per slice and provide dry-run-first restack behavior after lower stack PRs are squash-merged.

**Independent Test**: Use fixture state with an opened lower slice and remaining upper slices, then verify scoped verification evidence, failed-slice blocking, and restack dry-run/apply output.

### Tests for US3

- [x] T028 [US3] Add RED Layer 4 assertions for scoped verification command selection, required `no_scoped_tests` evidence, later-slice failure isolation, and no PR creation for failed scoped verification in `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh` (FR-012, FR-012a, FR-013, FR-013a, FR-013b, FR-014, FR-015, FR-016a, FR-016b, SC-003)
- [x] T029 [US3] Add RED Layer 4 assertions for restack dry-run ordering, `--apply` mutation guard, optional safe `gh-stack` inspection, JSON stdout schema, exit-code mapping, and deterministic stderr in `tests/speckit-pro/layer4-scripts/test-restack.sh` (FR-017, FR-017a, FR-017b, FR-017c, FR-017d, FR-017f, SC-005)

### Implementation for US3

- [x] T030 [US3] Implement scoped verification command mapping from PRSG-008 tests plus project commands in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` (FR-015, FR-015b, FR-016, FR-016a)
- [x] T031 [US3] Implement required `no_scoped_tests` evidence files under `specs/prsg-009-multi-pr-emission/.process/emission/<slice_id>/` in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` (FR-016b)
- [x] T032 [US3] Implement scoped verification failure handling that records failed-slice evidence, keeps `next_slice_id` on the failed slice, and stops before PR creation in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` (FR-012, FR-012a, FR-013, FR-013a, FR-013b, FR-014, SC-003)
- [x] T033 [US3] Implement restack state/manifest parsing, dry-run operation planning, branch order preservation, and scope-preservation reporting in `speckit-pro/skills/speckit-autopilot/scripts/restack.sh` (FR-017, FR-017b, FR-017f, FR-018)
- [x] T034 [US3] Implement `restack.sh --apply` mutation path, fixed exit codes, JSON `exit_code` parity, deterministic stderr diagnostics, and recovery evidence output in `speckit-pro/skills/speckit-autopilot/scripts/restack.sh` (FR-017b, FR-017c, FR-017d, FR-017e)
- [x] T035 [US3] Implement optional non-mutating `gh-stack` availability and active-stack inspection fallback behavior in `speckit-pro/skills/speckit-autopilot/scripts/restack.sh` (FR-017a)
- [x] T036 [US3] Run the focused US3 Layer 4 fixture path and record scoped verification/restack evidence in `docs/ai/specs/.process/PRSG-009-workflow.md` (FR-012, FR-017, FR-018, SC-003, SC-005)

**Checkpoint**: US3 records scoped evidence per slice and provides deterministic restack recovery without changing declared slice scope.

---

## Phase 5: Polish - docs, parity, dist mirrors, and final verification

**Purpose**: Make the behavior operable in Claude and Codex surfaces and verify the full deterministic suite.

- [x] T037 [P] Update the Claude post-implementation workflow reference for multi-PR emission, scoped verification, durable PRS rows, resume, failure blocking, and restack in `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` (FR-001, FR-008, FR-010, FR-012, FR-017, FR-020)
- [x] T038 [P] Update the Codex post-implementation mirror with equivalent multi-PR emission behavior in `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md` (FR-020)
- [x] T039 Refresh generated distribution mirrors for changed autopilot scripts and references under `dist/claude/speckit-pro/skills/speckit-autopilot/` and `dist/codex/speckit-pro/skills/speckit-autopilot/` (FR-020)
- [x] T040 [P] Update Layer 8 post-implementation parity fixture expectations for multi-PR emission in `tests/speckit-pro/layer8-parity/01-post-impl-parity/` (FR-020, SC-006)
- [x] T041 Run Layer 8 parity dry-run `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run` and record results in `docs/ai/specs/.process/PRSG-009-workflow.md` (FR-020, SC-006)
- [x] T042 Run structural validation `bash tests/speckit-pro/run-all.sh --layer 1` and record results in `docs/ai/specs/.process/PRSG-009-workflow.md` (SC-006)
- [x] T043 Run script-unit validation `bash tests/speckit-pro/run-all.sh --layer 4` and record results in `docs/ai/specs/.process/PRSG-009-workflow.md` (SC-006)
- [x] T044 Run default verification `bash tests/speckit-pro/run-all.sh`, update PR review packet evidence in `docs/ai/specs/.process/PRSG-009-workflow.md`, and confirm no `.github/workflows/pr-checks.yml` or PRSG-010 heuristic changes were introduced (FR-002, FR-015b, SC-006)
- [x] T045 [P] Add developer-local Layer 3 functional eval coverage for PRSG-009 multi-PR emission in `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json` and `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json`, asserting N ordered PRs from a PRSG-008 layer-plan fixture, no legacy flattened-PR fallback, and no new slicing heuristics (FR-001, FR-002, SC-001, SC-006)
- [x] T046 Run the PRSG-009 Layer 3 functional eval case when developer-local prerequisites are available, or record `DEV-LOCAL — not run here` with the case IDs and missing prerequisite reason in `docs/ai/specs/.process/PRSG-009-workflow.md`; also record that Layer 7 remains not applicable unless implementation introduces a new agent or dispatch graph behavior (SC-006)
- [x] T047 Record the `speckit-scaffold-spec` topology audit in `docs/ai/specs/.process/PRSG-009-workflow.md`: setup still creates/reuses one initial feature worktree branch, while Style B slice branches are emitted only by post-implementation `multi-pr-emission.sh`; confirm no scaffold-time review-routing or PRSG-010 backstop behavior was added (FR-002, FR-004, SC-006)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundation (Phase 1)**: No dependencies; creates fixtures and script entry points.
- **US1 (Phase 2)**: Depends on Foundation; produces ordered slice branch/PR emission contract.
- **US2 (Phase 3)**: Depends on US1 branch/PR emission contract; produces durable PRS/MOC/state resume behavior.
- **US3 (Phase 4)**: Depends on Foundation and can share some implementation timing with US2 after US1 branch topology exists; produces scoped verification and restack behavior.
- **Polish (Phase 5)**: Depends on desired user-story phases and runs final parity/regression checks.

### User Story Dependencies

- **US1 (P1)**: MVP. Can start after Foundation.
- **US2 (P2)**: Depends on US1 branch and PR records because it persists and resumes emitted slice PRs.
- **US3 (P3)**: Depends on US1 branch topology and Foundation fixtures; scoped verification failure handling touches the emission script and should be coordinated with US2 edits.

### Within Each User Story

- Add Layer 4 RED tests before implementation.
- Implement the smallest script change that passes the focused fixture.
- Run the focused Layer 4 test path before moving to the next story.
- Preserve exact FR references in workflow evidence and PR packet traceability.

### Parallel Opportunities

- T001-T005 can run in parallel because they touch separate fixture/test surfaces.
- T037, T038, T040, and T045 can run in parallel after script behavior is stable.
- Different story implementation should not edit `multi-pr-emission.sh` concurrently unless split by clearly owned functions.

---

## Parallel Example: Foundation

```bash
Task: "Add PRSG-009 fixture roots in tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/"
Task: "Add RED PR body tests in tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh"
Task: "Add RED PRS renderer tests in tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh"
Task: "Add RED emission tests in tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh"
Task: "Add RED restack tests in tests/speckit-pro/layer4-scripts/test-restack.sh"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1 Foundation.
2. Complete Phase 2 US1.
3. Validate ordered branch/base planning and explicit PR creation arguments with the focused Layer 4 fixture.

### Incremental Delivery

1. Foundation gives shared fixtures and script entry points.
2. US1 emits ordered slice PRs from the PRSG-008 plan.
3. US2 makes opened PR state durable and resumable.
4. US3 adds scoped verification and restack recovery.
5. Polish updates docs, mirrors, parity fixtures, and final verification evidence.

### Validation Commands

- `bash tests/speckit-pro/run-all.sh --layer 1`
- `bash tests/speckit-pro/run-all.sh --layer 4`
- `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run`
- `bash tests/speckit-pro/run-all.sh`

## Traceability Summary

| Story | Tasks | Key FRs | Independent Test |
|-------|-------|---------|------------------|
| US1 | T009-T016 | FR-001-FR-007a, FR-016c | Three-slice fixture emits ordered Style B stack with explicit PR args |
| US2 | T017-T027 | FR-008-FR-011e, FR-015a-FR-015d, FR-019 | Interrupted emission resumes from durable state without duplicate PRs |
| US3 | T028-T036 | FR-012-FR-018 | Scoped verification blocks failed slice PRs and restack preserves scope |
| Polish | T037-T047 | FR-001, FR-002, FR-004, FR-015b, FR-020, SC-001, SC-006 | Parity, structural, script-unit, developer-local L3, scaffold-spec topology audit, and default suites pass |

## Notes

- `[P]` means different files or independent fixture sets with no dependency on incomplete work.
- Layer 7 is intentionally absent because PRSG-009 does not add agent dispatch graph behavior; T046 records the not-applicable evidence during Polish.
- PRSG-010 review-routing heuristics are out of scope for all tasks.
