# Tasks: No Safe Boundary Marker Fixture

## Phase 1: Foundation

- [ ] T001 Prepare marker schema in speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json

## Phase 2: User Story 1 - Shared Mutation (Priority: P1)

- [ ] T002 [US1] Update shared marker dispatcher in speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh
- [ ] T003 [US1] Extend shared marker parser in speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh
- [ ] T004 [US1] Validate shared marker output in tests/speckit-pro/layer4-scripts/test-plan-layers.sh
- [ ] T005 [US1] Harden shared marker output in tests/speckit-pro/layer4-scripts/test-plan-layers.sh

## Dependencies & Execution Order

### Phase Dependencies

- **Foundation**: No prerequisites.
- **US1**: Depends on Foundation.

### Incremental Delivery

1. Complete Foundation: T001
2. Complete US1: T002-T005

### User Story Dependencies

- **US1**: Depends on Foundation only.
