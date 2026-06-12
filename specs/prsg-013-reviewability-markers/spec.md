# Feature Specification: Non-Stopping Reviewability Markers

**Feature Branch**: `prsg-013-reviewability-markers`

**Created**: 2026-06-12

**Status**: Draft

**Input**: User description: "Autopilot must continue through reviewability sizing warnings, use those findings to create durable PR markers, and emit scoped PRs at Foundation or user-story boundaries."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Continue Through Reviewability Sizing (Priority: P1)

As a SpecKit operator, I can run autopilot through reviewability sizing warnings or blocks without implementation stopping for size alone.

**Why this priority**: This fixes the product bug directly. Reviewability sizing should guide PR shaping, not prevent valid specs from being implemented.

**Independent Test**: Run autopilot on a valid task set whose only negative finding is reviewability size. The run continues into implementation and records reviewability evidence for PR planning.

**Acceptance Scenarios**:

1. **Given** a valid spec with a task reviewability result that reports size over budget, **When** autopilot completes task generation, **Then** it records the sizing result and continues toward implementation.
2. **Given** a final pre-PR reviewability backstop sees the full change as too large, **When** a persisted marker plan exists, **Then** autopilot uses the marker plan for PR emission instead of stopping for manual re-slicing.
3. **Given** a malformed plan, failed verification, invalid PR packet, unsafe output, or unreadable gate evidence, **When** the relevant correctness gate fails, **Then** autopilot stops and reports the blocking condition.

---

### User Story 2 - Emit Scoped PRs From Durable Markers (Priority: P2)

As a reviewer, I receive PRs scoped to Foundation setup or user-story boundaries derived from the task structure, with reviewability evidence attached to each PR scope.

**Why this priority**: Reviewers need bounded, explainable PRs. Durable markers make scope predictable without requiring manual task rewrites.

**Independent Test**: Generate a marker plan from canonical task sections and verify PR emission follows the recorded Foundation and user-story order.

**Acceptance Scenarios**:

1. **Given** tasks organized into Foundation and user-story sections, **When** marker planning runs, **Then** the marker plan contains an ordered Foundation marker when shared setup exists and one marker per user story.
2. **Given** small polish or cleanup tasks, **When** marker planning assigns PR scopes, **Then** those tasks are folded into the nearest appropriate marker instead of becoming a cleanup-only PR.
3. **Given** hard-atomic or release-sensitive hazards are detected, **When** PR emission is planned, **Then** autopilot keeps implementation non-stopping and emits one hazard-collapsed PR with marker evidence and a warning.

---

### User Story 3 - Verify Marker Planning And Emission Behavior (Priority: P3)

As an autopilot maintainer, I can verify marker planning, persistence, implementation ordering, and emission behavior with deterministic fixtures and one functional eval.

**Why this priority**: The behavior spans several autopilot phases. Regression coverage is required so future guidance does not turn reviewability sizing back into a stop.

**Independent Test**: Run deterministic fixtures plus one functional eval that exercise non-stopping reviewability handling, marker persistence, marker-ordered implementation, and marker-based PR emission.

**Acceptance Scenarios**:

1. **Given** fixtures covering pass, warning, and block reviewability results, **When** the deterministic suite runs, **Then** only malformed or unsafe evidence stops the run.
2. **Given** a persisted marker plan, **When** implementation guidance is evaluated, **Then** implementation checkpoints and evidence are produced in marker order.
3. **Given** a functional eval for a valid oversized spec, **When** autopilot is evaluated, **Then** the expected behavior is to continue implementation and emit scoped PRs from the marker plan.

### Edge Cases

- A reviewability sizing result is missing, malformed, or cannot be tied to the current feature.
- Tasks contain user-story sections but one story exceeds the reviewability budget.
- A large story has no safe internal task-cluster boundary for subdivision.
- Tasks include Foundation but no meaningful Polish section, or Polish contains only cleanup items.
- Hard-atomic or release-sensitive hazards conflict with the default split-by-marker plan.
- Existing autopilot state contains marker data from an earlier run of the same feature.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Autopilot MUST treat reviewability sizing results as non-stopping advisory input when the spec, plan, tasks, verification evidence, and PR packets are otherwise valid.
- **FR-002**: Autopilot MUST continue toward implementation when post-task reviewability sizing returns a warning or block caused by size alone.
- **FR-003**: Autopilot MUST convert reviewability sizing findings into a PR marker plan after task generation.
- **FR-004**: The PR marker plan MUST derive its default boundaries from the task structure's Foundation and user-story sections.
- **FR-005**: The marker plan MUST include a Foundation marker when shared setup work exists and MUST avoid separate cleanup-only PR markers for small Polish work.
- **FR-006**: The marker plan MUST be persisted in `autopilot-state.json` and workflow evidence without rewriting `tasks.md` as the authoritative marker store.
- **FR-007**: Each persisted marker MUST identify its source task boundary, ordered position, intended review scope, reviewability sizing status, and any hazard or subdivision note needed for review.
- **FR-008**: If a user-story marker exceeds the reviewability budget, autopilot MUST subdivide within that story when safe task-cluster boundaries exist.
- **FR-009**: If an oversized user-story marker has no safe internal boundary, autopilot MUST continue with the story marker and record an explicit reviewability warning.
- **FR-010**: If hard-atomic or release-sensitive hazards require one PR, autopilot MUST collapse PR emission to one PR while preserving marker evidence and continuing implementation.
- **FR-011**: The Implement phase MUST execute, checkpoint, and record evidence in PR-marker order when markers are available.
- **FR-012**: The final pre-PR reviewability backstop MUST consume the persisted marker plan for scoped PR emission instead of stopping on full-diff size alone.
- **FR-013**: The stable `reviewability-gate.sh tasks` contract MUST remain compatible unless planning proves that a compatibility-safe mode is necessary.
- **FR-014**: Correctness and safety stops MUST remain authoritative for malformed plans, failed verification, invalid PR packets, unsafe output, and unusable gate evidence.
- **FR-015**: Codex mirror guidance MUST remain behaviorally equivalent when mirrored autopilot guidance is touched.
- **FR-016**: Verification MUST cover marker planning, state persistence, implementation ordering, hazard collapse, marker-based PR emission, and non-stopping reviewability handling.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: docs/process, scheduler/runtime
- **Projected reviewable LOC**: 700-1,200
- **Projected production files**: 6-10
- **Projected total files**: 12-18
- **Budget result**: warning accepted
- **Split decision**: Keep PRSG-013 as one prerequisite spec because the behavior spans one product outcome, but require implementation PR markers for Foundation, each user story, and safe in-story subdivisions when a story is oversized.
- **Exception provenance, if any**: None. This is not a typed reviewability exception; the spec requires marker-based PR emission evidence rather than a single oversized PR.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Reviewability Finding**: A sizing result from task or final reviewability checks, including status, reason, scope, and whether the finding is advisory or correctness-blocking.
- **PR Marker Plan**: The ordered set of PR scopes that guides implementation checkpoints and PR emission for the current feature.
- **PR Marker**: A single review scope derived from Foundation, a user story, a safe in-story subdivision, or a hazard-collapsed full-spec scope.
- **Marker Evidence**: Workflow and state evidence that explains each marker's source tasks, reviewability status, hazards, verification, and emitted PR mapping.
- **Emission Packet**: The final PR creation payload associated with one marker or with one hazard-collapsed PR.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of deterministic fixtures where reviewability size is the only negative finding, autopilot continues past task generation toward implementation.
- **SC-002**: In 100% of canonical task-structure fixtures, marker planning records ordered Foundation and user-story markers without modifying the task document.
- **SC-003**: In non-hazard fixtures with multiple markers, PR emission creates one scoped PR packet per persisted marker in marker order.
- **SC-004**: In hazard fixtures, PR emission creates exactly one hazard-collapsed PR packet while preserving marker evidence and reviewability warnings.
- **SC-005**: In oversized-story fixtures with safe internal boundaries, marker planning creates at least two ordered sub-markers inside that story; without safe boundaries, it records a warning and continues.
- **SC-006**: Deterministic script-level coverage and one functional eval pass for marker planning, persistence, implementation ordering, emission behavior, and non-stopping reviewability handling.
- **SC-007**: Correctness-stop fixtures continue to stop in 100% of cases for malformed plans, failed verification, invalid PR packets, unsafe output, or unusable gate evidence.

## Assumptions

- "Valid spec" means the spec, plan, tasks, verification evidence, and PR packet data are structurally usable and do not trigger correctness or safety stops.
- The task structure continues to expose Foundation, user-story, and Polish sections as the primary source for reviewable PR boundaries.
- Marker schema details and the exact in-story subdivision heuristic will be finalized during planning and validated with deterministic fixtures.
- PRSG-013 is a prerequisite to resuming PRSG-012 reviewer-ready title/body validation.
- A full live dogfood PR emission run is useful evidence but is not required proof for this spec.
- Existing lower-level reviewability gate callers may continue depending on the current task-mode exit-code contract.
