# Tasks: Safe Subdivision Marker Fixture

## Phase 1: Foundation

- [ ] T001 Prepare schema harness in speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json

## Phase 2: User Story 1 - Split Safely (Priority: P1)

- [ ] T002 [US1] Implement first marker cluster in speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh
- [ ] T003 [US1] Test first marker cluster in tests/speckit-pro/layer4-scripts/test-plan-layers.sh
- [ ] T004 [US1] Implement second marker cluster in speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh
- [ ] T005 [US1] Test second marker cluster in tests/speckit-pro/layer4-scripts/test-reviewability-gate.sh

## Dependencies & Execution Order

### Phase Dependencies

- **Foundation**: No prerequisites.
- **US1**: Depends on Foundation.

### Incremental Delivery

1. Complete Foundation: T001
2. Complete US1: T002-T005

### User Story Dependencies

- **US1**: Depends on Foundation only.
