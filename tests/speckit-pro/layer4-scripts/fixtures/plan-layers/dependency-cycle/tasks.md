# Tasks: Dependency Cycle Fixture

## Phase 1: Foundation

- [ ] T001 Define the planner contract in specs/prsg-008-layer-planner/contracts/plan-layers.output.md

## Phase 2: User Story 1 - Emit Stable Plan (Priority: P1)

- [ ] T002 [US1] Emit foundation-dependent JSON in speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh

## Phase 3: User Story 2 - Parse Ordered Increments (Priority: P1)

- [ ] T003 [US2] Parse the US2 increment in tests/speckit-pro/layer4-scripts/test-plan-layers.sh

## Phase 4: User Story 3 - Validate Longer Cycles (Priority: P2)

- [ ] T004 [US3] Parse the US3 increment in tests/speckit-pro/layer4-scripts/test-plan-layers.sh

## Dependencies & Execution Order

### Phase Dependencies

- **Foundation**: No prerequisites.
- **US1**: Depends on US2.
- **US2**: Depends on US3.
- **US3**: Depends on US1.

### Incremental Delivery

1. Complete Foundation: T001
2. Complete US1: T002
3. Complete US2: T003
4. Complete US3: T004

### User Story Dependencies

- **US1**: Depends on US2.
- **US2**: Depends on US3.
- **US3**: Depends on US1.
