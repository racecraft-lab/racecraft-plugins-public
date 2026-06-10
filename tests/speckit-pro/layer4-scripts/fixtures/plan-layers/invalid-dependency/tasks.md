# Tasks: Invalid Dependency Fixture

## Phase 1: Foundation

- [ ] T001 Prepare the planner schema in speckit-pro/codex-skills/speckit-autopilot/SKILL.md

## Phase 2: User Story 1 - Emit Stable Plan (Priority: P1)

- [ ] T002 [US1] Implement stable output in speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh

## Phase 3: User Story 2 - Parse Ordered Increments (Priority: P1)

- [ ] T003 [US2] Parse ordered tasks in tests/speckit-pro/layer4-scripts/test-plan-layers.sh

## Dependencies & Execution Order

### Phase Dependencies

- **Foundation**: No prerequisites.
- **US1**: Depends on US3.
- **US2**: Depends on US1.

### Incremental Delivery

1. Complete Foundation: T001
2. Complete US2: T003
3. Complete US1: T002

### User Story Dependencies

- **US1**: Depends on unknown US3.
- **US2**: Depends on US1.
