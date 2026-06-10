# Tasks: PRSG-008 Valid Layer Planner Fixture

## Phase 1: Foundation

- [ ] T001 Finalize the output contract in speckit-pro/skills/speckit-autopilot/SKILL.md
- [ ] T002 [P] Finalize the schema contract in speckit-pro/codex-skills/speckit-autopilot/SKILL.md
- [x] T003 Create the RED planner harness in tests/speckit-pro/layer4-scripts/test-plan-layers.sh

## Phase 2: User Story 1 - Emit Stable Plan (Priority: P1)

- [ ] T004 [P] [US1] Create speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh and cover it with tests/speckit-pro/layer4-scripts/test-plan-layers.sh
- [ ] T005 [US1] Preserve feature path metadata in speckit-pro/codex-skills/speckit-autopilot/SKILL.md

## Phase 3: User Story 2 - Parse Ordered Increments (Priority: P1)

- [ ] T006 [P] [US2] Parse dependency order from speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh and validate tests/speckit-pro/layer4-scripts/test-plan-layers.sh
- [ ] T007 [US2] Preserve file references in speckit-pro/skills/speckit-autopilot/SKILL.md

## Phase 4: Polish and Validation

- [ ] T008 Run tests/speckit-pro/layer4-scripts/test-plan-layers.sh and update speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh

## Dependencies & Execution Order

### Phase Dependencies

- **Foundation**: No prerequisites.
- **US1**: Depends on Foundation.
- **US2**: Depends on US1.
- **Polish**: Depends on US2.

### Incremental Delivery

1. Complete Foundation: T001-T003
2. Complete US1: T004-T005
3. Complete US2: T006-T007
4. Complete Polish: T008

### User Story Dependencies

- **US1**: Depends on Foundation only.
- **US2**: Depends on US1.
