# Tasks: SPEC-FIXTURE-TASKS — Add `--quiet` Flag to CLI Tool

**Input**: Design documents from `speckit-pro/tests/layer7-integration/dispatch-fixtures/12-tasks-phase/`
**Prerequisites**: plan.md (inlined in sample-spec.md), spec.md (sample-spec.md)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — no structural changes needed for a flag addition; verify existing CLI entry point.

- [ ] T001 Locate CLI entry point and confirm argument-parsing module at src/cli.py (or equivalent)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user stories can be implemented.

- [ ] T002 Add `--quiet` flag definition to the argument parser in src/cli.py
- [ ] T003 Thread the `quiet` boolean through to the print/output layer (pass as parameter or set module-level flag) in src/output.py

**Checkpoint**: Foundation ready — quiet-mode guard is wired end-to-end; user story implementation can begin.

---

## Phase 3: User Story 1 — Quiet Mode Suppresses Non-Error Output (Priority: P1) 🎯 MVP

**Goal**: When `tool --quiet` is invoked, the tool exits 0 with no stdout.

**Independent Test**: Run `tool --quiet` and assert exit code is 0 and stdout is empty; run `tool` (no flag) and assert normal output appears.

### Implementation for User Story 1

- [ ] T004 [US1] Wrap every non-error `print` / logging call in a quiet-mode guard in src/output.py
- [ ] T005 [P] [US1] Write test for normal output mode (no flag) in tests/test_quiet_flag.py
- [ ] T006 [P] [US1] Write test for quiet mode (`--quiet` suppresses stdout) in tests/test_quiet_flag.py

**Checkpoint**: User Story 1 is fully functional — `tool --quiet` exits 0 with no stdout; `tool` prints normally.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and final clean-up.

- [ ] T007 [P] Update CLI help text / README to document `--quiet` flag in README.md
- [ ] T008 Run full test suite and confirm no regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS User Story 1
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **Polish (Phase 4)**: Depends on Phase 3 completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories

### Within User Story 1

- T002 → T003 (flag definition before threading)
- T003 → T004 (guard depends on threaded quiet value)
- T005 and T006 can be written in parallel once T004 is complete

### Parallel Opportunities

- T005 and T006 (tests) are independent of each other — run in parallel

---

## Parallel Example: User Story 1

```bash
# After T004 is complete, launch tests in parallel:
Task: "Write test for normal output mode in tests/test_quiet_flag.py"   # T005
Task: "Write test for quiet mode in tests/test_quiet_flag.py"           # T006
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002–T003)
3. Complete Phase 3: User Story 1 (T004–T006)
4. **STOP and VALIDATE**: `tool --quiet` exits 0, no stdout; `tool` prints normally
5. Proceed to Polish if validation passes

### Incremental Delivery

1. T001 — confirm entry point
2. T002–T003 — wire the flag
3. T004 — add quiet guard
4. T005–T006 — add tests (parallel)
5. T007–T008 — docs and final check

---

## Notes

- [P] tasks = different files or no mutual dependencies, safe to parallelize
- [US1] label maps task to User Story 1 for traceability
- Tests (T005, T006) are included because the plan explicitly calls for them
- Each phase checkpoint should be validated before proceeding
