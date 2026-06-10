# Tasks: PRSG-008 Layer Planner

**Input**: Design documents from `specs/prsg-008-layer-planner/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `checklists/`

**Tests**: TDD-first. RED Layer 4 fixtures, schema assertions, exit-code checks, and read-only checks must be added before parser implementation.

**Reviewability**: Keep runtime changes to the planner script plus scoped autopilot prose. Fixture volume is intentional contract coverage; do not expand into PRSG-009 branch, PR body, restack, or stacked-PR emission behavior.

**Reviewability scope note (T020)**: `reviewability-gate.sh tasks specs/prsg-008-layer-planner` currently reports `status=block` for the full task plan (`reviewable_loc=1800`, `total_files=48`, `primary_surface_count=6`). Keep the implementation scope to one planner script plus scoped autopilot handoff prose, treat Layer 4 tests/fixtures as intentional contract coverage, and keep PRSG-009 branch, PR body, restack, and stacked-PR emission behavior out of scope.

**Organization**: Tasks are grouped by independently testable user story, with Foundation work completing the RED fixtures and contract harness before any production parser logic.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel after its dependencies because it touches different files or isolated fixtures.
- **[Story]**: Required for user story phase tasks only.
- Every task includes exact file paths.

## Phase 1: Setup (RED Fixtures and Contract Harness)

**Purpose**: Create the failing Layer 4 fixture and schema surface before implementing parser behavior.

- [x] T001 [P] Finalize the versioned planner envelope, exit-code mapping, diagnostic shape, and PRSG-009 non-goals in `specs/prsg-008-layer-planner/contracts/plan-layers.output.md`
- [x] T002 [P] Finalize the JSON Schema for status enums, status-specific `ok`/`invalid_plan`/`input_error` invariants, semantic increment IDs, diagnostic code/detail constraints, warning/error severity separation, and advisory counts in `specs/prsg-008-layer-planner/contracts/plan-layers.schema.json`
- [x] T003 Create the RED Layer 4 planner test harness with schema validation, stdout/stderr capture, exit-code assertions, determinism checks, generated 200-task performance input, and read-only snapshots in `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`
- [x] T004 [P] Add the valid real-task fixture with Foundation, user-story, Polish, dependency-order, incremental-delivery, `[P]`, file, and test references in `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/valid-real/tasks.md`
- [x] T005 [P] Add the missing required headings fixture for `missing_required_heading` coverage in `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/missing-headings/tasks.md`
- [x] T006 [P] Add the invalid dependency fixture for `unknown_increment` and contradictory dependency references in `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/invalid-dependency/tasks.md`
- [x] T007 [P] Add the dependency cycle fixture for stable `dependency_cycle.details.cycle` coverage in `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/dependency-cycle/tasks.md`
- [x] T008 [P] Add the empty increment fixture for `empty_increment` coverage in `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/empty-increment/tasks.md`
- [x] T009 [P] Add the missing file/test reference fixture for `reference_not_found` warning coverage in `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/invalid-reference/tasks.md`
- [x] T010 [P] Add the task-without-references fixture for `task_without_references` warning coverage in `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/missing-references/tasks.md`
- [x] T011 [P] Add the checkbox preservation fixture for `[ ]`, `[x]`, `[X]`, and `[P]` metadata coverage in `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/checkbox-state/tasks.md`
- [x] T012 [P] Add the path normalization fixture for worktree-relative paths, duplicate references, leading `./`, and out-of-tree references in `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/path-normalization/tasks.md`
- [x] T013 [P] Add the duplicate ID and malformed checkbox fixture for `duplicate_increment_id`, `duplicate_task_id`, and `malformed_task` coverage in `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/malformed-task/tasks.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Turn the fixtures into actionable RED tests and establish script safety requirements before implementation.

**CRITICAL**: No parser implementation should begin until these tests fail for the expected reasons.

- [x] T014 Encode RED success assertions for valid JSON, schema conformance, `status=ok`, ordered increments, embedded tasks, source lines, checkbox status, `[P]`, and advisory counts in `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`
- [x] T015 Encode RED determinism, no-write, and generated 200-task under-1-second performance assertions for five repeated valid runs in `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`
- [x] T016 Encode RED invalid-plan assertions for missing headings, invalid dependencies, dependency cycles, empty increments, duplicate IDs, contradictory order, and malformed task-like lines in `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`
- [x] T017 Encode RED warning assertions for `reference_not_found` and `task_without_references` without failing otherwise valid plans in `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`
- [x] T018 Encode RED input-error assertions for invalid invocation, missing feature directory, unreadable feature directory, missing `tasks.md`, unreadable `tasks.md`, structured stdout JSON, concise stderr, and exit `2` in `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`
- [x] T019 Add Bash safety and executable-bit assertions for `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh` to `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`
- [x] T020 Verify the planned runtime/test/docs scope against the speckit-pro-reviewability budget and record any required scope note in `specs/prsg-008-layer-planner/tasks.md`

**Checkpoint**: RED fixtures and Layer 4 assertions are committed in the task plan before production parser logic starts.

---

## Phase 3: User Story 1 - Emit a Stable Layer Plan (Priority: P1) MVP

**Goal**: `speckit-autopilot` can pass one feature directory to the planner and receive a stable, read-only JSON envelope on stdout.

**Independent Test**: Run `bash tests/speckit-pro/layer4-scripts/test-plan-layers.sh` against `valid-real` and confirm repeated planner output is byte-for-byte stable and no fixture files change.

### Tests for User Story 1

- [x] T021 [US1] Confirm the RED success, determinism, read-only, input-error, and script-safety assertions fail before implementation in `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`

### Implementation for User Story 1

- [x] T022 [US1] Create the executable Bash entrypoint with shebang, `set -euo pipefail`, strict arity handling, and no repository writes in `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`
- [x] T023 [US1] Implement feature-directory and `tasks.md` readability validation with `input_error` envelopes, required diagnostic details, concise stderr summaries, and exit `2` in `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`
- [x] T024 [US1] Implement repo-root discovery and repo-relative normalization for `feature_dir`, `tasks_file`, and `source.path` fields in `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`
- [x] T025 [US1] Implement stable JSON envelope assembly with `jq`, closed status values, summary counts, stdout/stderr separation, and exit-code mapping in `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`

**Checkpoint**: User Story 1 is independently testable with input-error and valid-envelope coverage.

---

## Phase 4: User Story 2 - Parse Ordered Increments from Tasks (Priority: P1)

**Goal**: PRSG-009 can consume Foundation, user-story, and Polish increments in deterministic dependency order without reparsing task prose.

**Independent Test**: Run the Layer 4 valid fixture assertions and verify increment IDs, dependency order, task membership, `[P]`, file/test references, and counts-only advisory size.

### Tests for User Story 2

- [x] T026 [US2] Confirm the RED parser assertions for heading discovery, dependency order, incremental delivery order, semantic increment IDs, task membership, `[P]`, and checkbox status fail before parser implementation in `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`

### Implementation for User Story 2

- [x] T027 [US2] Implement heading discovery for `## Dependencies & Execution Order`, `### Incremental Delivery`, Foundation, user-story, and Polish sections in `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`
- [x] T028 [US2] Implement task extraction for checkbox state, task ID, title, source line, story label, semantic increment ID, and `[P]` metadata in `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`
- [x] T029 [US2] Implement authoritative dependency and incremental-delivery parsing with deterministic `depends_on` ordering in `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`
- [x] T030 [US2] Implement file/test reference extraction, worktree-relative normalization, duplicate removal, out-of-tree warning detection, and `LC_ALL=C` lexical ordering in `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`
- [x] T031 [US2] Implement increment aggregation with embedded tasks, `files`, `tests`, and counts-only `advisory_size` in `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`

**Checkpoint**: User Story 2 produces ordered semantic increments with deterministic embedded task metadata.

---

## Phase 5: User Story 3 - Diagnose Malformed Plans (Priority: P2)

**Goal**: Maintainers receive structured JSON diagnostics and concise stderr summaries for invalid plans while warning-only plans still succeed.

**Independent Test**: Run malformed and warning fixtures and verify exit `1` for invalid plans, exit `0` for warnings, schema-conforming diagnostics, required details payloads, and no file changes.

### Tests for User Story 3

- [x] T032 [US3] Confirm the RED invalid-plan and warning assertions fail for malformed, missing-reference, and task-without-reference fixtures in `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`

### Implementation for User Story 3

- [x] T033 [US3] Implement `missing_required_heading`, `empty_increment`, `unknown_increment`, `duplicate_increment_id`, `duplicate_task_id`, and `malformed_task` diagnostics with closed details payloads in `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`
- [x] T034 [US3] Implement deterministic `dependency_cycle` and `contradictory_increment_order` diagnostics with stable cycle/order details in `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`
- [x] T035 [US3] Implement `task_without_references` and `reference_not_found` warning diagnostics with severity `warning`, shared shape, concise stderr, and successful exit `0` in `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`
- [x] T036 [US3] Validate every planner outcome and status-specific schema invariant against `specs/prsg-008-layer-planner/contracts/plan-layers.schema.json` from `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`

**Checkpoint**: User Story 3 handles valid, warning, invalid-plan, and input-error outcomes with one schema-backed envelope.

---

## Phase 6: User Story 4 - Gate Autopilot Before Implementation (Priority: P2)

**Goal**: `speckit-autopilot` runs the layer planner after PRSG-007 route recording and before Analyze or implementation only when the recorded route is `split-PR`.

**Independent Test**: Review the Claude and Codex skill surfaces and run targeted test/eval coverage to confirm split routes stop or continue based on planner exit status while non-split routes skip layer planning.

### Tests for User Story 4

- [x] T037 [US4] Add RED autopilot fixture or eval coverage for `split-PR` planner success, invalid-plan stop, input-error stop, warning carry-forward, and non-split skip behavior in `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json`

### Implementation for User Story 4

- [x] T038 [US4] Wire the Claude autopilot flow to run `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh <feature-dir>` after post-G5 atomicity route recording and before Analyze or implementation when route is exactly `split-PR` in `speckit-pro/skills/speckit-autopilot/SKILL.md`
- [x] T039 [US4] Add Claude autopilot handling for planner exit `0`, warning carry-forward, full envelope persistence to `autopilot-state.json`, workflow `## Layer Plan` summary, invalid-plan fixed stop line, input-error stop message, and non-split skip behavior in `speckit-pro/skills/speckit-autopilot/SKILL.md`
- [x] T040 [US4] Mirror the same Codex autopilot layer-plan gate, state persistence, workflow summary, warning carry-forward, stop lines, and non-split skip behavior in `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`

**Checkpoint**: User Story 4 integrates the planner after atomicity routing and before implementation without adding PRSG-009 emission behavior.

---

## Phase 7: Polish and Validation

**Purpose**: Verify the complete PRSG-008 slice and keep release notes scoped to planner behavior.

- [x] T041 [P] Run `bash -n speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh` and executable-bit checks for `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`
- [x] T042 [P] Run `bash tests/speckit-pro/run-all.sh --layer 4` and capture planner fixture coverage plus the 200-task performance assertion for `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`
- [x] T043 [P] Run `bash tests/speckit-pro/run-all.sh --layer 1` to verify structural plugin packaging for `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`
- [x] T044 Run `bash tests/speckit-pro/run-all.sh` to verify the deterministic default suite from the repository root
- [x] T045 Update implementation evidence, FR traceability, validation commands, warning behavior, and PRSG-009 non-goals in `docs/ai/specs/.process/PRSG-008-workflow.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No prerequisites. Creates contract docs, fixtures, and RED harness scaffold.
- **Foundational (Phase 2)**: Depends on Setup. Converts fixtures into RED assertions and safety checks.
- **US1 (Phase 3)**: Depends on Foundational. Provides executable planner shell, input handling, stable envelope, and read-only behavior.
- **US2 (Phase 4)**: Depends on US1. Adds task parsing, dependency parsing, DAG output, reference extraction, and advisory counts.
- **US3 (Phase 5)**: Depends on US1 and US2. Adds invalid-plan and warning diagnostics.
- **US4 (Phase 6)**: Depends on US1, US2, and US3. Wires planner results into autopilot only after the script contract is green.
- **Polish (Phase 7)**: Depends on US4. Runs validation and records evidence.

### Incremental Delivery

1. Complete Foundation: T001-T020
2. Complete MVP planner envelope: T021-T025
3. Complete ordered increment parser: T026-T031
4. Complete malformed-plan diagnostics: T032-T036
5. Complete autopilot handoff: T037-T040
6. Complete validation and evidence: T041-T045

### User Story Dependencies

- **US1**: Depends on Foundation only.
- **US2**: Depends on US1 because parser output uses the shared envelope and path helpers.
- **US3**: Depends on US1 and US2 because diagnostics validate parser state and dependency graph failures.
- **US4**: Depends on US1, US2, and US3 because autopilot must consume all planner statuses.

---

## Parallel Execution Examples

### Foundation

Run T001-T002 in parallel with fixture creation T004-T013 after T003 establishes the test harness target path. RED assertion tasks T014-T019 should run after the fixtures exist.

### User Story 1

T023 and T024 can be implemented in parallel after T022 creates the executable script shell; T025 should follow once input errors and path normalization are available.

### User Story 2

T027 and T028 can be developed together inside `plan-layers.sh`; T029 depends on heading/task extraction, and T030-T031 can follow once increment IDs and task metadata exist.

### User Story 3

T033 and T034 can be implemented in parallel because they cover different diagnostic classes; T035 can follow once reference extraction is available, and T036 should run after all diagnostic shapes exist.

### User Story 4

T038 and T040 can be edited in parallel if one executor owns Claude skill prose and another owns Codex skill prose; T039 should be serialized with T038 because both touch `speckit-pro/skills/speckit-autopilot/SKILL.md`.

---

## Implementation Strategy

### MVP First

1. Complete Foundation through T020.
2. Complete US1 through T025.
3. Run the Layer 4 harness for valid/input-error/read-only behavior before adding parser complexity.

### Incremental Rollout

1. Add US2 parser behavior and keep valid fixture output deterministic.
2. Add US3 malformed/warning diagnostics and schema validation.
3. Wire US4 only after the script contract is green.
4. Run Layer 4, Layer 1, then the default deterministic suite.

### Non-Goals

- Do not create branches.
- Do not generate PR bodies.
- Do not restack changes.
- Do not emit stacked-PR topology.
- Do not add PRSG-006 LOC hints, thresholds, or budget verdicts to planner output.

---

## FR Coverage

| Requirement(s) | Covered by tasks |
|----------------|------------------|
| FR-001, FR-002, FR-014k, FR-015 | T018, T022-T023 |
| FR-003, FR-004, FR-005, FR-014a, FR-014b, FR-020 | T003, T014-T015, T021-T025 |
| FR-006, FR-007, FR-008, FR-010, FR-010a | T004, T014, T026-T031 |
| FR-009, FR-014g, FR-014i, FR-014j, FR-014l, FR-014m, FR-014n, FR-014o | T005-T008, T013, T016, T032-T034, T036 |
| FR-011, FR-012, FR-014c, FR-014d, FR-014f, FR-014p | T011-T012, T026-T031 |
| FR-013, FR-014e, FR-014h | T009-T010, T017, T032, T035-T036 |
| FR-014 | T001-T002, T003, T036 |
| FR-016, FR-017, FR-017a, FR-017b, FR-018, FR-018a, FR-018b, FR-018c | T037-T040 |
| FR-019 | T001, T020, T038-T040, T045 |

## Success Criteria Coverage

| Success Criterion | Covered by tasks | Verification focus |
|-------------------|------------------|--------------------|
| SC-001 | T015, T042 | Five repeated valid runs produce byte-identical JSON. |
| SC-002 | T003, T015, T042 | Generated 200-task input completes in under 1 second on a typical development machine. |
| SC-003 | T005-T008, T013, T016, T032-T034, T036 | Malformed-plan fixtures return exit `1`, structured JSON errors, and concise stderr. |
| SC-004 | T018, T023 | Usage/input fixtures return exit `2`, structured JSON errors, and no repository writes. |
| SC-005 | T009-T010, T017, T032, T035-T036 | Missing-reference fixtures return exit `0` with warning diagnostics. |
| SC-006 | T011-T012, T014, T026-T031 | Emitted tasks retain source line and checkbox-state traceability. |
| SC-007 | T037-T040 | Split-relevant autopilot runs stop before implementation on planner failure. |
| SC-008 | T001, T020, T038-T040, T045 | PRSG-009 owns branch, PR body, restack, and multi-PR emission work. |
