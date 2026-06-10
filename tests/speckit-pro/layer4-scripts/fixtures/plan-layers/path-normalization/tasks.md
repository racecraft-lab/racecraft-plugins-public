# Tasks: Path Normalization Fixture

## Phase 1: Foundation

- [ ] T001 Normalize leading-dot paths in ./speckit-pro/skills/speckit-autopilot/SKILL.md
- [ ] T002 Deduplicate repeated references in speckit-pro/skills/speckit-autopilot/SKILL.md, ./speckit-pro/skills/speckit-autopilot/SKILL.md, and speckit-pro/./skills/speckit-autopilot/SKILL.md

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
