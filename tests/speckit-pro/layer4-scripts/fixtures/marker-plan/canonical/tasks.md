# Tasks: Canonical Marker Plan Fixture

## Phase 1: Foundation

- [ ] T001 Add marker schema coverage in speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json
- [ ] T002 Add marker planner tests in tests/speckit-pro/layer4-scripts/test-plan-layers.sh

## Phase 2: User Story 1 - Build Marker Plan (Priority: P1)

- [ ] T003 [P] [US1] Build marker mode in speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh and tests/speckit-pro/layer4-scripts/test-plan-layers.sh
- [ ] T004 [US1] Validate reviewability evidence in speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh

## Phase 3: User Story 2 - Persist Plan Candidate (Priority: P2)

- [ ] T005 [P] [US2] Emit candidate marker plans from speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh
- [ ] T006 [US2] Validate fingerprint fields in speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json

## Phase 4: Polish and Validation

- [ ] T007 Run tests/speckit-pro/layer4-scripts/test-plan-layers.sh and update speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh

## Dependencies & Execution Order

### Phase Dependencies

- **Foundation**: No prerequisites.
- **US1**: Depends on Foundation.
- **US2**: Depends on US1.
- **Polish**: Depends on US2.

### Incremental Delivery

1. Complete Foundation: T001-T002
2. Complete US1: T003-T004
3. Complete US2: T005-T006
4. Complete Polish: T007

### User Story Dependencies

- **US1**: Depends on Foundation only.
- **US2**: Depends on US1.
