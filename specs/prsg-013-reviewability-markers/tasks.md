# Tasks: Non-Stopping Reviewability Markers

**Input**: Design documents from `specs/prsg-013-reviewability-markers/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Tests**: Required by FR-016, SC-006, SC-007, and SC-008. Write or update the Layer 4/Layer 3 coverage before implementation changes in each story.

**Organization**: Tasks are grouped by Foundation plus user story so each behavior can be implemented and verified independently.

**Marker-state note**: These tasks describe implementation work only. Do not make `tasks.md` the authoritative marker store, and do not add marker comments here for runtime PR emission.

## Phase 1: Foundation

**Purpose**: Establish the compatible contracts, schemas, and fixtures needed before user-story work starts.

- [x] T001 [P] [FND] Inspect `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh`, `speckit-pro/skills/speckit-autopilot/scripts/final-reviewability-backstop.sh`, `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`, and `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` before edits; acceptance: current exit/status behavior and side-effect boundaries are understood for FR-001, FR-013, and FR-014.
- [x] T002 [P] [FND] Add production marker-plan schema coverage in `speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json`; acceptance: schema includes the FR-006 and FR-007 fields from `specs/prsg-013-reviewability-markers/contracts/pr-marker-plan.schema.json`.
- [x] T003 [P] [FND] Add marker-planning fixture inputs under `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/` for Foundation plus user stories, Polish folding, safe subdivision, no safe boundary, stale fingerprint, and malformed marker state; acceptance: fixtures cover FR-003 through FR-009 and FR-014.
- [x] T004 [P] [FND] Add final-backstop and marker-emission fixture inputs under `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/` for `marker_split`, missing/stale/malformed plans, marker packets, and hazard collapse; acceptance: fixtures cover FR-010, FR-012, FR-014, and FR-016.
- [x] T005 [FND] Add or reuse shared Layer 4 fixture helpers in `tests/speckit-pro/layer4-scripts/` for repo-relative evidence paths, structured warnings, and schema assertions; acceptance: later story tests can assert FR-006, FR-007, FR-012, and FR-018 without duplicating large shell blocks.
- [x] T006 [FND] Validate planning contracts with `jq empty specs/prsg-013-reviewability-markers/contracts/*.schema.json`; acceptance: both spec contracts parse cleanly for FR-016.

**Checkpoint**: Foundation complete when schema and fixture scaffolding exist and no user-story implementation depends on undocumented script behavior.

## Phase 2: User Story 1 - Continue Through Reviewability Sizing (Priority: P1)

**Goal**: Autopilot continues through valid size-only reviewability warnings or blocks, while correctness and safety stops remain authoritative.

**Independent Test**: A valid task reviewability `status=block` size-only result becomes marker-planning input and a final full-diff size block with a current marker plan returns `marker_split`; malformed or stale evidence still stops.

### Tests for User Story 1

- [x] T007 [P] [US1] Add a Layer 4 fixture in `tests/speckit-pro/layer4-scripts/test-plan-layers.sh` or its marker helper for a task-mode size-only `status=block` that exits nonzero but emits valid JSON; acceptance: fixture proves FR-001, FR-002, FR-003, and FR-013.
- [x] T008 [P] [US1] Add correctness-stop fixtures in `tests/speckit-pro/layer4-scripts/test-plan-layers.sh` for invalid JSON, missing `status` or `mode`, unreadable evidence, non-size blockers, and unexpected exits; acceptance: each stops per FR-014 and SC-007.
- [x] T009 [P] [US1] Add a valid final-backstop `marker_split` fixture in `tests/speckit-pro/layer4-scripts/test-final-reviewability-backstop.sh`; acceptance: size-blocked full diff plus valid marker plan exits 0 with `status=proceed` and `outcome=marker_split` for FR-012.
- [x] T010 [P] [US1] Add missing, stale, malformed, and fingerprint-mismatched marker-plan fixtures in `tests/speckit-pro/layer4-scripts/test-final-reviewability-backstop.sh`; acceptance: each returns `correctness_stop`, exits nonzero, and performs no PR side effects for FR-012 and FR-014.

### Implementation for User Story 1

- [x] T011 [US1] Update `speckit-pro/skills/speckit-autopilot/references/gate-validation.md` and `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` with the guarded post-G5 task-gate capture pattern and allowlisted proceed/stop matrix; acceptance: guidance states valid current size-only `block` continues, while FR-014 stops remain blocking for FR-001, FR-002, FR-013, and FR-017.
- [x] T012 [US1] Update `speckit-pro/skills/speckit-autopilot/scripts/final-reviewability-backstop.sh` with marker-aware input handling and `marker_split` output; acceptance: valid full-diff size block plus current marker plan exits 0 and emits the FR-012 fields without changing legacy no-marker behavior.
- [x] T013 [US1] Update `speckit-pro/skills/speckit-autopilot/contracts/final-reviewability-gate-state.schema.json` for marker-aware final backstop evidence; acceptance: schema validates `status`, `outcome`, `mode`, full-diff evidence, marker count/order, emission handoff, and warnings required by FR-012 and FR-018.
- [x] T014 [US1] Ensure `final-reviewability-backstop.sh` rejects missing, stale, malformed, or fingerprint-mismatched marker plans before any PR body generation or PR side effect; acceptance: FR-014 correctness stops are enforced and warning-only rendering is not used for invalid marker state.
- [x] T015 [US1] Run targeted checks for US1: `bash -n speckit-pro/skills/speckit-autopilot/scripts/final-reviewability-backstop.sh` and the relevant final-backstop Layer 4 tests; acceptance: all US1 fixtures pass for FR-016.

**Checkpoint**: US1 complete when reviewability sizing is non-stopping only for valid size-only findings and final backstop can hand off `marker_split`.

## Phase 3: User Story 2 - Emit Scoped PRs From Durable Markers (Priority: P1)

**Goal**: Marker planning derives durable Foundation and user-story PR markers from task structure, persists a fingerprinted plan, folds Polish work, and subdivides oversized stories only at safe task-cluster boundaries.

**Independent Test**: Canonical tasks produce ordered markers and a valid `pr_marker_plan` without rewriting `tasks.md`; stale or malformed marker evidence stops.

### Tests for User Story 2

- [x] T016 [P] [US2] Add canonical Foundation plus user-story marker assertions in `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`; acceptance: marker IDs, task IDs, and one-based review order match FR-003, FR-004, FR-006, and FR-007.
- [x] T017 [P] [US2] Add Polish folding assertions in `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`; acceptance: no cleanup-only marker is emitted and fold target/reason are recorded for FR-005 and FR-007.
- [x] T018 [P] [US2] Add safe subdivision and no-safe-boundary assertions in `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`; acceptance: safe clusters become ordered `us<N>-part<M>` markers, unsafe clusters continue with structured warnings for FR-008 and FR-009.
- [x] T019 [P] [US2] Add source-fingerprint and stale-resume assertions in `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`; acceptance: fingerprint changes clear or reject stale marker evidence for FR-006 and FR-014.

### Implementation for User Story 2

- [x] T020 [US2] Extend `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh` with an explicit marker-aware mode that reads the feature directory, captured reviewability result, hazard route, current state path, and marker-plan output path; acceptance: legacy PRSG-008 stdout/exit behavior remains compatible while marker mode emits stable machine-readable output for FR-003, FR-004, FR-006, and FR-013.
- [x] T021 [US2] Implement marker derivation from Foundation and user-story sections in `plan-layers.sh`; acceptance: `foundation` is present only for shared setup, one marker exists per user story before subdivision, and marker order is stored in `markers[]` and `review_order` for FR-004 and FR-007.
- [x] T022 [US2] Implement source fingerprinting in `plan-layers.sh` for spec, plan-declared file/test scope, tasks, reviewability evidence, and hazard decision; acceptance: fingerprint mismatches mark plans stale or stop before reuse for FR-006 and FR-014.
- [x] T023 [US2] Implement safe task-cluster subdivision in `plan-layers.sh`; acceptance: contiguous in-story clusters with no crossing dependency, complete files/tests, and no hazard signal become child markers, while unsafe cases continue with structured warnings for FR-008 and FR-009.
- [x] T024 [US2] Implement deterministic Polish folding in `plan-layers.sh`; acceptance: small Polish tasks fold into the nearest eligible non-Polish marker and record the fold target and reason for FR-005 and FR-007.
- [x] T025 [US2] Update `speckit-pro/skills/speckit-autopilot/SKILL.md` and `speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md` so autopilot persists top-level `pr_marker_plan` state and mirrored workflow evidence, not authoritative marker state in `tasks.md`; acceptance: guidance covers FR-006, FR-017, and FR-018.
- [x] T026 [US2] Run targeted checks for US2: `bash -n speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh` and the marker-planning Layer 4 tests; acceptance: all US2 fixtures pass for FR-016.

**Checkpoint**: US2 complete when marker planning is durable, fingerprinted, ordered, and independent of task-prose mutations.

## Phase 4: User Story 3 - Verify Marker Planning And Emission Behavior (Priority: P1)

**Goal**: Implementation guidance checkpoints work in marker order and marker-aware PR emission consumes persisted markers, including hazard-collapsed output when release safety requires one PR.

**Independent Test**: A persisted marker plan drives implementation checkpoint evidence and marker-aware PR packets in review order; hazard collapse emits one `full-spec` packet with source marker evidence.

### Tests for User Story 3

- [x] T027 [P] [US3] Add non-hazard marker emission packet assertions in `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh`; acceptance: one packet per marker is emitted in `review_order` with declared files/tests and final-backstop evidence for FR-011, FR-012, and SC-003.
- [x] T028 [P] [US3] Add hazard-collapse packet assertions in `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh`; acceptance: `route == single-atomic-PR` or `releasable == false` emits one `full-spec` packet with ordered `source_marker_ids`, while `one-navigable-PR` and `releasable == true` does not collapse by itself for FR-010 and SC-004.
- [x] T029 [P] [US3] Add marker-packet shape validation assertions in `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh`; acceptance: invalid, stale, placeholder-filled, marker-mismatched, or scope-mismatched marker packets stop before PR side effects for FR-014 and FR-016, without implementing PRSG-012 title/body validation.
- [x] T030 [P] [US3] Add paired Claude and Codex Layer 3 eval cases in `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json` and `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json`; acceptance: both runtimes continue through a valid size-only block with marker evidence and no manual re-slicing stop for FR-015, FR-017, FR-018, and SC-008.

### Implementation for User Story 3

- [x] T031 [US3] Update `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` and `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` to execute, checkpoint, and record evidence in marker order when `pr_marker_plan` is available; acceptance: guidance requires marker checkpoint evidence for FR-011 and FR-018.
- [x] T032 [US3] Extend `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` with marker-aware mode that consumes a validated `pr_marker_plan` plus final `marker_split` result; acceptance: non-hazard output creates one scoped packet per emitted marker in review order for FR-011, FR-012, and FR-014.
- [x] T033 [US3] Implement hazard-collapsed emission in `multi-pr-emission.sh`; acceptance: one `full-spec` packet preserves original marker checkpoint evidence, warning objects, and ordered `source_marker_ids` for FR-010.
- [x] T034 [US3] Implement marker packet shape validation in `multi-pr-emission.sh`; acceptance: marker ID/order/scope/evidence mismatches stop before PR body generation or PR side effects, and the change explicitly does not add PRSG-012 reviewer-ready title/body validation for FR-014 and FR-016.
- [x] T035 [US3] Update `speckit-pro/skills/speckit-autopilot/contracts/multi-pr-emission-state.schema.json` for marker-aware packets and hazard-collapsed mapping; acceptance: schema covers `marker_id`, `source_marker_ids`, review order, final `marker_split` evidence path, warnings, and PR mapping fields required by FR-007, FR-010, FR-012, and FR-018.
- [x] T036 [US3] Run targeted checks for US3: `bash -n speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`, marker-emission Layer 4 tests, and available Layer 3 eval validation; acceptance: marker emission, hazard collapse, and guidance eval fixtures pass for FR-016.

**Checkpoint**: US3 complete when persisted markers drive implementation evidence and marker-aware PR emission without inferring scope from a mixed final diff.

## Phase 5: Polish & Parity

**Purpose**: Keep mirrored guidance equivalent, clean evidence, and run the deterministic validation path.

- [x] T037 [P] Mirror touched autopilot guidance into `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`, `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`, and `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md`; acceptance: Codex preserves the same non-stopping size-only block rule, correctness-stop boundaries, `marker_split` handoff, and evidence prompts for FR-015, FR-017, and FR-018.
- [x] T038 [P] Clean up runtime evidence examples and repo-relative path assertions in touched tests and guidance; acceptance: marker plans, final-backstop evidence, and emission packets do not use absolute runtime paths for FR-006 and FR-018.
- [x] T039 [P] Validate all changed JSON schemas with `jq empty specs/prsg-013-reviewability-markers/contracts/*.schema.json speckit-pro/skills/speckit-autopilot/contracts/*.schema.json`; acceptance: schema files parse cleanly for FR-016.
- [x] T040 Run `bash -n` on touched Bash scripts in `speckit-pro/skills/speckit-autopilot/scripts/`; acceptance: shell syntax remains valid for FR-016.
- [x] T041 Run targeted Layer 4 scripts for `test-plan-layers.sh`, `test-final-reviewability-backstop.sh`, and `test-multi-pr-emission.sh`; acceptance: marker planning, final backstop, and marker emission fixtures pass for FR-016.
- [x] T042 Run `bash tests/speckit-pro/run-all.sh --layer 1`; acceptance: structural validation passes for plugin layout, contracts, and mirrored surfaces for FR-015 and FR-016.
- [x] T043 Run `bash tests/speckit-pro/run-all.sh`; acceptance: default deterministic layers pass for FR-016.
- [x] T044 Run `bash tests/speckit-pro/run-all.sh --all` when Layer 3 prerequisites are installed, or record the missing prerequisite in workflow evidence; acceptance: functional eval evidence is present or explicitly deferred for FR-016 and SC-006.
- [x] T045 Update `docs/ai/specs/.process/PRSG-013-workflow.md` with Phase 5 metrics and implementation/eval evidence, without editing `docs/ai/specs/.process/autopilot-state.json`; acceptance: workflow summarizes task count, phase count, parallel opportunities, user-story coverage, and validation status for FR-006 and FR-018.

**Checkpoint**: Polish complete when source and Codex guidance stay semantically equivalent and the required deterministic validation is recorded.

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Foundation**: No dependencies. Blocks user-story implementation.
- **Phase 2 US1**: Depends on Phase 1. Establishes the non-stopping reviewability proceed/stop behavior.
- **Phase 3 US2**: Depends on Phase 1 and benefits from US1 fixtures. Produces durable marker planning.
- **Phase 4 US3**: Depends on US1 and US2. Consumes marker plans for checkpointing and PR emission.
- **Phase 5 Polish & Parity**: Depends on desired story implementation and validation evidence.

### User Story Dependencies

- **US1**: Can start after Foundation. It does not depend on marker derivation internals except for marker-plan fixture inputs.
- **US2**: Can start after Foundation. It can proceed in parallel with US1 tests once shared fixtures exist, but final backstop integration depends on US1 outputs.
- **US3**: Depends on current marker plans from US2 and final `marker_split` behavior from US1.

### Within Each Story

- Test/fixture tasks come before implementation tasks.
- Script schema and fixture assertions come before shell implementation.
- Guidance updates come after the deterministic contract is clear.
- Validation tasks close each story before moving to broader parity checks.

## Parallel Opportunities

- Foundation fixture/schema tasks: T001, T002, T003, T004.
- US1 tests: T007, T008, T009, T010.
- US2 tests: T016, T017, T018, T019.
- US3 tests and eval setup: T027, T028, T029, T030.
- Polish/parity cleanup: T037, T038, T039.

## Implementation Strategy

### MVP First

1. Complete Phase 1.
2. Complete Phase 2 and verify US1 independently.
3. Stop and validate that size-only reviewability findings no longer block valid implementation flow.

### Incremental Delivery

1. Add US2 marker planning and persistence.
2. Validate marker plans without mutating `tasks.md`.
3. Add US3 marker-ordered checkpointing and marker-aware emission.
4. Finish parity and deterministic validation.

### Scope Guardrails

- Do not modify `docs/ai/specs/.process/autopilot-state.json`.
- Do not turn `tasks.md` into runtime marker state.
- Do not implement PRSG-012 reviewer-ready PR packet validation.
- Keep deterministic logic in Bash under `speckit-pro/skills/speckit-autopilot/scripts/`.
- Mirror touched guidance under `speckit-pro/codex-skills/speckit-autopilot/`.
