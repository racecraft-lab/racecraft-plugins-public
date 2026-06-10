# Tasks: Invalid Reference Warning Fixture

## Phase 1: Foundation

- [ ] T001 Keep the valid contract in speckit-pro/skills/speckit-autopilot/SKILL.md

## Phase 2: User Story 1 - Emit Stable Plan (Priority: P1)

- [ ] T002 [US1] Reference a missing script speckit-pro/skills/speckit-autopilot/scripts/no-such-plan-layers-helper.sh
- [ ] T003 [US1] Reference a missing test tests/speckit-pro/layer4-scripts/no-such-plan-layers-test.sh

## Phase 3: Polish and Validation

- [ ] T004 Validate warnings with tests/speckit-pro/layer4-scripts/test-plan-layers.sh

## Dependencies & Execution Order

### Phase Dependencies

- **Foundation**: No prerequisites.
- **US1**: Depends on Foundation.
- **Polish**: Depends on US1.

### Incremental Delivery

1. Complete Foundation: T001
2. Complete US1: T002-T003
3. Complete Polish: T004

### User Story Dependencies

- **US1**: Depends on Foundation.
