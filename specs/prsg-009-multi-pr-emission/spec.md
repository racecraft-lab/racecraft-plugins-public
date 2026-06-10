# Feature Specification: PRSG-009 multi-PR emission

**Feature Branch**: `prsg-009-multi-pr-emission`

**Created**: 2026-06-10

**Status**: Draft

**Input**: User description: "The current post-implementation flow flattens implementation output into one PR even when PRSG-008 has produced multiple reviewable slices. PRSG-009 must consume the PRSG-008 layer plan, emit ordered Style B incremental stack PRs after full implementation and verification, keep the spec MOC PR table durable, define scoped CI and restack behavior, stop before opening failed slice PRs, and preserve Codex parity for mirrored skill/reference changes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Emit ordered slice PRs from the layer plan (Priority: P1)

As a maintainer reviewing SpecKit-generated implementation work, I want the autopilot to create one ordered PR per PRSG-008 reviewable layer so each review unit stays small, dependency-aware, and aligned with the declared slice plan.

**Why this priority**: This is the primary governance fix. Without deterministic multi-PR emission, PRSG-008 can split work correctly but reviewers still receive one oversized PR.

**Independent Test**: Use a completed implementation with a PRSG-008 layer plan containing multiple layers, run the emission phase, and verify that the emitted branch and PR sequence exactly follows the layer order without adding new slicing heuristics.

**Acceptance Scenarios**:

1. **Given** a verified implementation and a `plan-layers.sh` output with three ordered layers, **When** the emission phase runs, **Then** it creates three ordered PRs whose branch bases and review order match the layer plan.
2. **Given** a layer plan containing a single layer, **When** the emission phase runs, **Then** it emits one PR using the same emission contract without falling back to the previous all-changes PR path.
3. **Given** a layer plan that includes file ownership for each slice, **When** slice branches are created, **Then** each branch contains only the declared file operations for that slice plus explicitly required shared bookkeeping.

---

### User Story 2 - Persist PR table and resume evidence after each slice (Priority: P2)

As an autopilot operator, I want the spec MOC PR table, workflow status, and `autopilot-state.json` updated after each successful slice PR so review navigation, resume behavior, and recovery evidence survive interruptions.

**Why this priority**: Multi-PR emission is only operable if partial progress is durable. Operators need to resume without duplicating PRs, losing ordering, or reopening already-failed slices.

**Independent Test**: Interrupt emission after a successful slice PR, resume the workflow, and verify that already-opened PRs are recognized from durable state while pending slices continue from the next unstarted layer.

**Acceptance Scenarios**:

1. **Given** slice PR 1 opens successfully, **When** the workflow records progress, **Then** the spec MOC PR table includes PR 1 with branch, base, scope, verification, status, and review order fields before slice PR 2 begins.
2. **Given** emission is interrupted after slice PR 2, **When** the operator resumes, **Then** the workflow reads durable MOC and state entries, skips already-opened slice PRs, and continues with the next pending slice.
3. **Given** a scoped verification command fails for a slice, **When** the emission phase handles the failure, **Then** no PR is opened for that slice and the workflow plus `autopilot-state.json` record the failed command, evidence location, and blocked slice identity.

---

### User Story 3 - Define stack topology, scoped CI, and restack behavior (Priority: P3)

As a maintainer, I want branch topology, scoped CI mapping, and restack behavior defined so stacked review remains usable through squash-merge review loops.

**Why this priority**: Reviewers need predictable branch bases and verification expectations after emission works. This makes the stack maintainable without expanding PRSG-009 into new routing logic.

**Independent Test**: Simulate a Style B incremental stack with at least two slice PRs, squash-merge the lower slice, and verify that the remaining branches can be restacked according to documented rules while preserving review scope.

**Acceptance Scenarios**:

1. **Given** a Style B incremental stack, **When** the first slice PR is opened, **Then** it targets the integration base branch and each later slice branch targets the immediately preceding slice branch.
2. **Given** the lower slice is squash-merged, **When** the stack is restacked, **Then** remaining open slice branches are rebased or retargeted in order without changing their declared file-operation scope.
3. **Given** a slice declares structural and script verification gates, **When** its PR packet is prepared, **Then** the PR includes the scoped command mapping and the successful evidence required for that slice.

### Edge Cases

- The layer plan is missing, unreadable, empty, or not parseable.
- The layer plan references files not changed by the completed implementation.
- A slice contains only shared bookkeeping files needed for durable emission state.
- A slice branch already exists locally or remotely from a previous interrupted run.
- A slice PR already exists, was closed, or was merged before resume.
- A lower stack PR is squash-merged while higher slice PRs remain open.
- Scoped verification passes for an earlier slice but fails for a later slice.
- GitHub PR creation succeeds but state persistence fails immediately afterward.
- Codex and Claude mirrored skill/reference files differ for the same emission behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST consume PRSG-008 `plan-layers.sh` output as the authoritative ordering source for multi-PR emission.
- **FR-002**: The system MUST NOT introduce new atomicity, routing, or slicing heuristics in PRSG-009; layer membership must come from the existing PRSG-008 plan.
- **FR-003**: The system MUST emit slice PRs only after full implementation and required verification have completed for the overall feature.
- **FR-004**: The system MUST use Style B incremental stack branches, where the first slice targets the integration base and each later slice targets the previous slice branch.
- **FR-005**: The system MUST create one slice branch and one PR per planned layer when scoped verification for that slice succeeds.
- **FR-006**: The system MUST ensure each slice branch contains only that slice's declared file operations plus explicitly required shared workflow or state updates.
- **FR-007**: The system MUST define deterministic branch naming for emitted slice branches so resume can identify them without ambiguity.
- **FR-008**: The system MUST update the spec MOC PR table after each successful PR creation before attempting the next slice.
- **FR-009**: The spec MOC PR table MUST record, for each slice PR, the review order, branch, base branch, PR URL or number, layer identity, declared file scope, scoped verification evidence, and current status.
- **FR-010**: The system MUST persist resume state in `autopilot-state.json` after each successful PR creation, including completed slice identity and pending next slice identity.
- **FR-011**: The system MUST detect already-created slice branches or PRs during resume and reconcile them with the spec MOC PR table before creating additional PRs.
- **FR-012**: The system MUST stop before opening a slice PR when that slice's scoped verification fails.
- **FR-013**: On scoped verification failure, the system MUST record the failed slice identity, failed command, exit status, and evidence location in the workflow record and `autopilot-state.json`.
- **FR-014**: The system MUST NOT open known-bad draft PRs for slices with failed scoped verification.
- **FR-015**: The system MUST map each slice to the scoped verification gates required by the project command table, including structural and script-unit checks where applicable.
- **FR-016**: The system MUST include scoped CI or verification mapping in each slice PR packet so reviewers can see which commands protect that review unit.
- **FR-017**: The system MUST define restack behavior for squash-merge review loops, including how remaining branches are rebased or retargeted after a lower slice merges.
- **FR-018**: Restack behavior MUST preserve the declared file-operation scope of each unmerged slice.
- **FR-019**: The system MUST record enough recovery evidence to distinguish pending, opened, failed, closed, and merged slice states.
- **FR-020**: The system MUST preserve Codex parity for mirrored skill and reference changes that implement or document multi-PR emission behavior.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: harness/adapter, seed/config
- **Projected reviewable LOC**: 350-650 excluding generated distribution mirrors
- **Projected production files**: 3-6
- **Projected total files**: 8-14 including mirrored Codex/Claude references and focused tests
- **Budget result**: warning accepted
- **Split decision**: This remains one spec because the scope is constrained to emission, resume, scoped verification mapping, and restack behavior that depend on one contract. New review-routing heuristics and deeper atomicity backstops are explicitly deferred to PRSG-010.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Layer Plan**: Ordered PRSG-008 output that identifies reviewable layers, declared file operations, and verification expectations used by PRSG-009 as input.
- **Slice Branch**: A deterministic branch for one layer in the Style B incremental stack, with a known base, review order, and file-operation scope.
- **Slice PR**: The GitHub pull request opened from a slice branch, containing PR packet metadata, scoped verification evidence, and review navigation.
- **Spec MOC PR Table**: Durable per-spec navigation table that records emitted PRs, statuses, branch topology, scope, and evidence after each successful slice.
- **Autopilot State Entry**: Machine-readable resume and recovery state that records slice progress, pending work, failed evidence, and reconciliation facts.
- **Restack Operation**: The ordered recovery action that updates remaining slice branches after a lower stack PR is squash-merged.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Given a valid three-layer PRSG-008 plan, emission creates three PRs in the same order with branch bases matching Style B incremental stack rules.
- **SC-002**: After each successful slice PR, the spec MOC PR table and `autopilot-state.json` contain enough data to resume without duplicating that PR.
- **SC-003**: If a later slice fails scoped verification, zero PRs are opened for that failed slice and the failed command evidence is recorded in both durable workflow state surfaces.
- **SC-004**: Each emitted slice PR includes review order, scope budget, declared file-operation scope, scoped verification evidence, traceability, non-goals, known gaps, and rollback or restack notes.
- **SC-005**: After a lower slice is squash-merged, remaining slice branches can be restacked or retargeted in documented order while preserving their declared review scope.
- **SC-006**: Structural validation and script-unit tests cover the multi-PR emission contract, resume reconciliation, failed-slice stop behavior, and Codex parity checks.

## Assumptions

- PRSG-008 already produces a deterministic layer plan with enough file-operation data for emission.
- The implementation phase has already completed before PRSG-009 emission begins.
- The existing project verification commands are limited to structural and script-unit shell checks for this repository.
- GitHub remains the PR host for emitted slice PRs.
- `autopilot-state.json` is the durable machine-readable resume surface, while the spec MOC PR table is the durable reviewer-facing navigation surface.
- Generated or mirrored distribution files may be included when needed for parity, but they do not change the behavioral scope of PRSG-009.
