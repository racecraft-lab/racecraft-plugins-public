# Tasks: Path Normalization Fixture

## Phase 1: Foundation

- [ ] T001 Normalize leading-dot paths in ./specs/prsg-008-layer-planner/contracts/plan-layers.output.md
- [ ] T002 Deduplicate repeated references in specs/prsg-008-layer-planner/contracts/plan-layers.output.md, ./specs/prsg-008-layer-planner/contracts/plan-layers.output.md, and specs/./prsg-008-layer-planner/contracts/plan-layers.output.md

## Phase 2: User Story 1 - Emit Stable Plan (Priority: P1)

- [ ] T003 [US1] Normalize test paths in ./tests/speckit-pro/layer4-scripts/test-plan-layers.sh
- [ ] T004 [US1] Preserve out-of-tree warning details for ../outside-worktree-plan.md

## Dependencies & Execution Order

### Phase Dependencies

- **Foundation**: No prerequisites.
- **US1**: Depends on Foundation.

### Incremental Delivery

1. Complete Foundation: T001-T002
2. Complete US1: T003-T004

### User Story Dependencies

- **US1**: Depends on Foundation.
