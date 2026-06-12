# Tasks: Hazard Collapse Marker Fixture

## Phase 1: Foundation

- [ ] T001 Add marker schema coverage in speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json

## Phase 2: User Story 1 - Atomic Setup (Priority: P1)

- [ ] T002 [US1] Update atomic planner behavior in speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh

## Phase 3: User Story 2 - Atomic Validation (Priority: P2)

- [ ] T003 [US2] Validate atomic planner behavior in tests/speckit-pro/layer4-scripts/test-plan-layers.sh

## Dependencies & Execution Order

### Phase Dependencies

- **Foundation**: No prerequisites.
- **US1**: Depends on Foundation.
- **US2**: Depends on US1.

### Incremental Delivery

1. Complete Foundation: T001
2. Complete US1: T002
3. Complete US2: T003

### User Story Dependencies

- **US1**: Depends on Foundation only.
- **US2**: Depends on US1.
