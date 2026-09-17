# PARITY-01 Tasks

These implementation tasks describe only the two product increments. The
complete host-native Post contract and its evidence obligations remain in
`spec.md`, `plan.md`, and `workflow.md`; this task topology does not replace or
abbreviate them.

## Phase 1: User Story 1 - Alpha capability (Priority: P1)

- [x] T001 [P] [US1] Add the Alpha capability in `src/capability_alpha.py`.
- [x] T002 [US1] Verify Alpha independently in `tests/test_capability_alpha.py`.

## Phase 2: User Story 2 - Beta capability (Priority: P1)

- [x] T003 [P] [US2] Add the Beta capability in `src/capability_beta.py`.
- [x] T004 [US2] Verify Beta independently in `tests/test_capability_beta.py`.

## Dependencies & Execution Order

### Phase Dependencies

- **US1**: Depends on No prerequisites.
- **US2**: Depends on No prerequisites.

### Incremental Delivery

1. Complete US1 independently: T001-T002.
2. Complete US2 independently: T003-T004.

### User Story Dependencies

- **US1**: Independent.
- **US2**: Independent; no dependency on US1.
