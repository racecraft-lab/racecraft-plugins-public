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
3. **Given** hard-atomic or release-sensitive hazards are detected, **When** PR emission is planned, **Then** autopilot keeps implementation non-stopping, checkpoints the original markers in order, and emits one hazard-collapsed PR with marker evidence and a warning.

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
- A post-task reviewability check exits nonzero while still emitting valid `status=block` JSON.
- Tasks contain user-story sections but one story exceeds the reviewability budget.
- A large story has no safe internal task-cluster boundary for subdivision, so the original story marker must continue with a structured warning.
- Tasks include Foundation but no meaningful Polish section, or Polish contains only cleanup items.
- Hard-atomic or release-sensitive hazards conflict with the default split-by-marker plan.
- Existing autopilot state contains marker data from an earlier run of the same feature and must be validated against current task, reviewability, and hazard-decision fingerprints.
- Final backstop evidence is size-blocked but the marker plan is missing, stale, malformed, or fingerprint-mismatched.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Autopilot MUST treat parseable reviewability sizing results (`pass`, `warn`, honored `exception`, and size-only `block`) as marker-planning input when the spec, plan, tasks, verification evidence, and PR packets are otherwise valid.
- **FR-002**: Autopilot MUST continue toward implementation when post-task reviewability sizing returns a warning or valid size-only `status=block` JSON, even if the underlying gate command exits nonzero for caller compatibility.
- **FR-003**: Autopilot MUST convert reviewability sizing findings into a PR marker plan after task generation.
- **FR-004**: The PR marker plan MUST derive its default boundaries from the task structure's Foundation and user-story sections.
- **FR-005**: The marker plan MUST include a Foundation marker when shared setup work exists and MUST fold small Polish work into the nearest appropriate non-Polish marker rather than creating a separate cleanup-only PR marker. Polish folding MUST prefer the last preceding non-Polish marker whose dependencies and declared file/test scope cover the cleanup; if no preceding marker can own it, it MUST fold into the next eligible non-Polish marker and record the fold target and reason.
- **FR-006**: The marker plan MUST be persisted as top-level `pr_marker_plan` state in `autopilot-state.json` and workflow evidence without rewriting `tasks.md` as the authoritative marker store. Workflow evidence MUST mirror the same schema version, source fingerprint, ordered marker IDs, review order, statuses, warnings, and evidence paths used by `autopilot-state.json`; human-readable workflow summaries MUST be derived from that mirrored state, not maintained as a parallel source of truth.
- **FR-007**: Each persisted marker MUST identify its stable marker ID, one-based review order, marker kind, source task boundary, parent marker ID when subdivided, task IDs, folded Polish task IDs, folded Polish target reason, intended review scope, declared files, declared tests, reviewability sizing status, hazard notes, subdivision notes, implementation checkpoint, and emission mapping.
- **FR-008**: If a user-story marker exceeds the reviewability budget, autopilot MUST subdivide within that story when safe task-cluster boundaries exist. A safe task cluster is a contiguous task group inside the same user story with no dependency edge crossing the boundary, complete declared files and tests, no shared mutation or hazard signal, and preserved task order. Safe subdivision replaces the parent `us<N>` marker in the emitted marker sequence with ordered `us<N>-part<M>` child markers; the parent marker MUST NOT also emit a PR packet unless hazard collapse maps all source markers into `full-spec`.
- **FR-009**: If an oversized user-story marker has no safe internal boundary, autopilot MUST continue with the original story marker and record an explicit structured reviewability warning.
- **FR-010**: If hard-atomic or release-sensitive hazards require one PR, autopilot MUST collapse PR emission to one PR while preserving marker evidence and continuing implementation. Hazard collapse is triggered only when the recorded Atomicity Route has `route == single-atomic-PR` or `releasable == false`; `one-navigable-PR` with `releasable == true` MUST NOT trigger hazard collapse by itself.
- **FR-011**: The Implement phase MUST execute, checkpoint, and record evidence in PR-marker order when markers are available.
- **FR-012**: The final pre-PR reviewability backstop MUST consume the persisted marker plan for scoped PR emission instead of stopping on full-diff size alone. When the full diff is size-blocked and the current `pr_marker_plan` is valid, the backstop MUST emit a marker-aware proceed outcome named `marker_split`, exit successfully, and pass its evidence to marker-based PR emission.
- **FR-013**: The stable `reviewability-gate.sh tasks` contract MUST remain compatible unless planning proves that a compatibility-safe mode is necessary; autopilot owns the captured stdout/exit-code interpretation for valid task-mode `status=block` JSON.
- **FR-014**: Correctness and safety stops MUST remain authoritative for malformed plans, failed verification, invalid PR packets, unsafe output, unusable gate evidence, invalid JSON, unreadable task or plan artifacts, missing reviewability status or mode, stale fingerprints, and malformed marker plans. Marker-plan fingerprints MUST cover the current spec, plan-declared file/test scope, task document, reviewability evidence, and hazard decision so plan-scope drift cannot reuse stale marker evidence.
- **FR-015**: Codex mirror guidance MUST remain behaviorally equivalent when mirrored autopilot guidance is touched. Parity is semantic equivalence, not byte-identical prose: Claude and Codex guidance may use runtime-specific voice and mechanics, but MUST preserve the same non-stopping size-only block rule, the same correctness-stop boundaries, the same final `marker_split` handoff, and the same required evidence fields.
- **FR-016**: Verification MUST cover marker planning, state persistence, implementation ordering, hazard collapse, marker-based PR emission, non-stopping reviewability handling, and Claude/Codex guidance parity for the non-stopping decision matrix.
- **FR-017**: Agent-facing autopilot guidance MUST state that a valid, current, size-only reviewability `status=block` is not a manual stop condition. The guidance MUST instruct future agents to continue implementation by persisting marker evidence, checkpointing in marker order, and using marker-based PR emission. It MUST NOT instruct agents to stop, ask the operator to manually re-slice, rewrite task boundaries, or wait for manual re-scope solely because the full feature or final diff is too large.
- **FR-018**: Agent-facing evidence prompts MUST require future agents to record the proof of every non-stopping size-only block decision: captured reviewability status/mode/exit code/evidence path, the reason it is size-only, marker-plan schema version and evidence path, source-fingerprint validation result, ordered marker IDs, per-marker checkpoint evidence, structured warning objects, final-backstop `marker_split` evidence path, marker-packet validation status, and emitted PR mapping when present.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: docs/process, scheduler/runtime
- **Projected reviewable LOC**: 700-1,200
- **Projected production files**: 7-11
- **Projected total files**: 13-19
- **Budget result**: warning accepted
- **Split decision**: Keep PRSG-013 as one prerequisite spec because the behavior spans one product outcome, but require implementation PR markers for Foundation, each user story, and safe in-story subdivisions when a story is oversized.
- **Exception provenance, if any**: None. This is not a typed reviewability exception; the spec requires marker-based PR emission evidence rather than a single oversized PR.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Marker warnings MUST be rendered into PR packet warnings while preserving structured warning evidence in state.
- Marker-aware PR packets MUST be validated before PR body generation, `gh pr create`, or any equivalent PR side effect; invalid, stale, placeholder-filled, or marker-mismatched packets MUST stop rather than being converted into PR-body warnings.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Reviewability Finding**: A parseable sizing result from task or final reviewability checks, including status, reason, mode, scope, metrics, evidence path, and whether the finding is marker-planning input or correctness-blocking evidence.
- **PR Marker Plan**: The top-level `pr_marker_plan` state for the current feature, including schema version, kind, status, source fingerprint, ordered marker array, warnings, and workflow-evidence mirror.
- **PR Marker**: A single review scope derived from Foundation, a user story, a safe in-story subdivision, or a hazard-collapsed full-spec scope. Stable IDs are `foundation`, `us<N>`, `us<N>-part<M>`, or `full-spec` for hazard collapse; subdivided child markers carry `parent_marker_id=us<N>` and replace the parent marker for scoped emission.
- **Safe Task Cluster**: A contiguous group of tasks inside one user story that can be reviewed independently because dependencies, declared files, tests, and hazard signals do not cross the boundary.
- **Marker Evidence**: Workflow and state evidence that explains each marker's source tasks, reviewability status, hazards, verification, final-backstop status, metrics, evidence path, emitted PR mapping, and structured warnings with `code`, `severity`, `message`, `source`, and `details`. Workflow evidence and state evidence must use the same marker IDs, one-based review order, source fingerprint, warning objects, and emission mapping values.
- **Emission Packet**: The final PR creation payload associated with one marker or with one hazard-collapsed PR. A scoped packet carries its marker's final-backstop `marker_split` evidence and warning objects; a hazard-collapsed packet maps back to the original marker IDs and their implementation checkpoints.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of deterministic fixtures where reviewability size is the only negative finding, autopilot continues past task generation toward implementation.
- **SC-002**: In 100% of canonical task-structure fixtures, marker planning records ordered Foundation and user-story markers without modifying the task document.
- **SC-003**: In non-hazard fixtures with multiple markers, PR emission creates one scoped PR packet per persisted marker in marker order.
- **SC-004**: In hazard fixtures, PR emission creates exactly one hazard-collapsed PR packet while preserving marker evidence and reviewability warnings.
- **SC-005**: In oversized-story fixtures with safe internal boundaries, marker planning creates at least two ordered sub-markers inside that story; without safe boundaries, it records a warning and continues.
- **SC-006**: Deterministic script-level coverage and one functional eval pass for marker planning, persistence, implementation ordering, emission behavior, and non-stopping reviewability handling.
- **SC-007**: Correctness-stop fixtures continue to stop in 100% of cases for malformed plans, failed verification, invalid PR packets, unsafe output, unusable gate evidence, stale marker fingerprints, missing marker plans at final emission, or malformed marker state.
- **SC-008**: Paired Claude and Codex autopilot guidance coverage passes for the same valid size-only block scenario, proving both runtimes continue with marker evidence and neither runtime reintroduces a manual re-slicing stop for size alone.

## Assumptions

- "Valid spec" means the spec, plan, tasks, verification evidence, and PR packet data are structurally usable and do not trigger correctness or safety stops.
- The task structure continues to expose Foundation, user-story, and Polish sections as the primary source for reviewable PR boundaries.
- Marker schema details and the exact in-story subdivision heuristic will be finalized during planning and validated with deterministic fixtures.
- PRSG-013 is a prerequisite to resuming PRSG-012 reviewer-ready title/body validation.
- A full live dogfood PR emission run is useful evidence but is not required proof for this spec.
- Existing lower-level reviewability gate callers may continue depending on the current task-mode exit-code contract.
- Marker ordering is determined by the ordered `markers[]` array and one-based `review_order`, not by JSON object key order.
- On resume, marker implementation and emission evidence may be preserved only when the marker ID, source boundary, task IDs, folded Polish task IDs, and source fingerprint still match. Any changed source fingerprint, marker membership, order, or fold target clears checkpoint/emission evidence for affected markers and replaces stale marker plans before implementation or PR emission continues.
- Marker plans are created before implementation; final PR emission does not invent review boundaries if the current marker plan is absent or invalid.
- Claude and Codex guidance may differ in UI mechanics and wording, but they must expose the same proceed/stop matrix and evidence requirements for PRSG-013 reviewability marker handling.
