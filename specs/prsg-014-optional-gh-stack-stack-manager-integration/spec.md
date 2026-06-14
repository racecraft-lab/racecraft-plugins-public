# Feature Specification: Optional gh-stack stack manager integration

**Feature Branch**: `prsg-014-optional-gh-stack-stack-manager-integration`

**Created**: 2026-06-14

**Status**: Draft

**Input**: User description: "Add optional gh-stack stack-manager integration so autopilot can use native stack create/sync/restack when deterministic support checks pass, while preserving explicit gh base/head fallback everywhere else."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Detect support before mutation (Priority: P1)

As a SpecKit operator running autopilot on a split-PR spec, I can see whether optional `gh-stack` support is available, supported, compatible, and safe before any branch or PR topology is changed.

**Why this priority**: Operators need deterministic pre-mutation evidence before trusting an optional stack manager. This is the safety gate for every other behavior in this feature.

**Independent Test**: Can be tested by running stack-manager detection against supported, missing, unsupported, ambiguous, topology-incompatible, and dry-run-failed environments and confirming the selected manager and reason are recorded before mutation.

**Acceptance Scenarios**:

1. **Given** a repository with supported `gh-stack` behavior and compatible stack topology, **When** autopilot evaluates stack-manager support, **Then** it records `gh-stack` as supported with version/support evidence and a command plan before any mutation.
2. **Given** a repository where `gh-stack` is missing, unsupported, ambiguous, or unsafe, **When** autopilot evaluates stack-manager support, **Then** it records the fallback reason and selects the explicit `gh` path before any mutation.
3. **Given** a repository where the stack topology is incompatible with `gh-stack`, **When** autopilot evaluates support, **Then** it blocks `gh-stack` selection and records enough topology evidence for the operator to understand the decision.

---

### User Story 2 - Use supported stack manager with fallback (Priority: P2)

As a SpecKit operator, I can let autopilot use `gh-stack` for stack-aware PR creation and sync when support checks pass, while unsupported repositories continue to use explicit base/head PR commands.

**Why this priority**: This delivers the main operator value while preserving the canonical deterministic fallback for every repository that cannot safely use `gh-stack`.

**Independent Test**: Can be tested by creating or syncing a small stacked PR set in both supported and fallback environments and confirming the same branch names, explicit base topology, PR packet validation, and marker order are preserved.

**Acceptance Scenarios**:

1. **Given** support detection passes and the PR packet has validated title/body content, **When** autopilot emits stacked PRs, **Then** it uses the selected `gh-stack` command plan and records the resulting topology evidence.
2. **Given** support detection does not pass and no stack-manager mutation has occurred, **When** autopilot emits stacked PRs, **Then** it uses the explicit `gh pr create/edit` base/head fallback with the same validated PR packet content.
3. **Given** PRSG-013 markers and branch names have been generated, **When** either manager path emits or syncs PRs, **Then** marker order, branch names, and explicit base relationships remain unchanged.

---

### User Story 3 - Restack safely after squash merges (Priority: P3)

As a maintainer, I can restack later PRs after earlier squash merges through `gh-stack` when it is safe, or through the existing restack fallback when it is not.

**Why this priority**: Maintainers need the same safety and evidence guarantees during post-merge restacking as during initial stack emission.

**Independent Test**: Can be tested by simulating an earlier PR squash merge and confirming later PRs are retargeted through the selected safe manager, with fallback before mutation and recoverable blocking after partial mutation.

**Acceptance Scenarios**:

1. **Given** a stack with an earlier squash-merged PR and supported `gh-stack` restack behavior, **When** the maintainer applies restack, **Then** later PRs are retargeted through the selected stack manager and evidence records the selected manager, command plan, and topology.
2. **Given** the same stack but unsupported, missing, ambiguous, or unsafe `gh-stack` behavior, **When** the maintainer applies restack before mutation, **Then** the existing fallback path retargets later PRs and records the fallback reason.
3. **Given** a `gh-stack` operation has already partially mutated branch or PR topology, **When** a subsequent step fails, **Then** autopilot blocks instead of switching managers and emits recoverable state for operator repair.

---

### User Story 4 - Review stack-manager evidence (Priority: P4)

As a reviewer, I can inspect emitted evidence showing the command plan, selected stack manager, fallback reason, version/support outcome, and resulting topology.

**Why this priority**: Reviewers and autopilot maintainers need enough evidence to verify behavior, diagnose failures, and confirm Claude Code and Codex guidance remain aligned.

**Independent Test**: Can be tested by reviewing emitted artifacts from supported, fallback, and blocked runs and confirming the evidence answers which manager was chosen, why, which commands were planned, and what topology resulted.

**Acceptance Scenarios**:

1. **Given** any stack-manager run, **When** a reviewer opens the emitted evidence, **Then** they can identify selected manager, fallback reason if any, version/support outcome, command plan, and PR/branch topology without rerunning the operation.
2. **Given** Claude Code and Codex operator guidance are updated, **When** reviewers compare supported, fallback, and blocked flows, **Then** both surfaces describe the same stack-manager decision behavior without duplicate script implementations.

### Edge Cases

- `gh-stack` is not installed or is not discoverable in the operator environment.
- `gh-stack` is installed but reports an unsupported, unknown, or unparsable version.
- `gh-stack` status or dry-run behavior is ambiguous and cannot prove safe execution.
- The repository or branch topology is incompatible with stack-aware create, sync, or restack behavior.
- PR packet title/body validation fails before PR creation.
- PRSG-013 marker ordering or branch naming would be changed by the selected path.
- A `gh-stack` command partially mutates topology and a later command fails.
- A retry could duplicate PRs or retarget branches incorrectly without recoverable evidence.
- Claude Code and Codex guidance drift from the shared stack-manager behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Autopilot MUST determine whether optional `gh-stack` support is available, supported, repository-compatible, topology-compatible, and safe before any stack-manager command mutates branch or PR topology.
- **FR-002**: Autopilot MUST record a deterministic stack-manager decision containing availability, support outcome, reason, selected manager, fallback reason when applicable, command plan, version/support outcome, and PR/branch topology.
- **FR-003**: Autopilot MUST select `gh-stack` only when all support and safety checks pass.
- **FR-004**: Autopilot MUST fall back to the explicit `gh` base/head path before mutation when `gh-stack` is missing, unsupported, ambiguous, incompatible, or unsafe.
- **FR-005**: Autopilot MUST preserve the explicit `gh` base/head path as the canonical fallback and MUST NOT make `gh-stack` a required dependency.
- **FR-006**: Autopilot MUST preserve PRSG-012 PR packet title/body generation and validation before any PR creation or sync action.
- **FR-007**: Autopilot MUST preserve PRSG-013 marker order, branch names, and explicit base topology across both selected stack-manager and fallback paths.
- **FR-008**: Autopilot MUST support stack-aware PR creation and sync through `gh-stack` when support checks pass.
- **FR-009**: Autopilot MUST support post-squash restack through `gh-stack` when safe, or through the existing restack fallback before mutation otherwise.
- **FR-010**: Autopilot MUST NOT mix stack managers after any partial `gh-stack` mutation.
- **FR-011**: Autopilot MUST block with recoverable evidence when a partial `gh-stack` mutation has occurred and continuing would require switching managers or risk ambiguous topology.
- **FR-012**: Autopilot MUST keep stack-manager detection, emission, and restack decisions in shared behavior used by both emission and restack flows.
- **FR-013**: Claude Code and Codex operator guidance MUST describe the same supported, fallback, and blocked behaviors without duplicating stack-manager scripts under `codex-skills/`.
- **FR-014**: Verification evidence MUST cover supported, missing, unsupported, ambiguous, dry-run-failed, fallback, and partial-mutation scenarios.
- **FR-015**: The feature MUST NOT add unrelated stack-manager capabilities beyond create, sync, restack, fallback, evidence, and safety.

### Reviewability Notes *(if applicable)*

- No typed reviewability exception is expected.
- Generated or fixture evidence may be excluded from reviewable LOC only when it is clearly marked as generated or test fixture content.
- Any deferred work must name a follow-up spec or issue in the PR packet.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: docs/process
- **Projected reviewable LOC**: 325
- **Projected production files**: 5
- **Projected total files**: 14
- **Budget result**: within budget
- **Split decision**: Keep as one spec because the design concept estimated one slice and the create/sync/restack work shares one stack-manager decision contract. Split only if planning discovers incompatible `gh-stack` command behavior that requires a separate compatibility spec.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.
- PR packet evidence MUST identify the selected stack manager, fallback reason when applicable, command plan, version/support outcome, mutation boundary, and PR/branch topology.

### Key Entities *(include if feature involves data)*

- **Stack Manager Decision**: The pre-mutation decision record that identifies available managers, selected manager, support status, fallback reason, and confidence in safe execution.
- **Command Plan**: The ordered set of stack create, sync, or restack actions that will be executed or used to explain fallback/blocking behavior.
- **Topology Evidence**: The observable branch and PR base/head relationships before and after stack-manager operations.
- **PR Packet Evidence**: The validated title/body and traceability material that must exist before PR creation or sync.
- **Recoverable Block State**: The evidence emitted after partial mutation that allows an operator to inspect, repair, or resume without mixing managers or duplicating PRs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of stack create, sync, and restack attempts emit stack-manager decision evidence before any topology mutation.
- **SC-002**: In supported-path verification, stack-aware create/sync/restack preserves branch names, explicit base topology, PRSG-013 marker order, and validated PR packet content.
- **SC-003**: In 100% of missing, unsupported, ambiguous, incompatible, or unsafe cases, autopilot selects the explicit fallback before mutation and records the reason.
- **SC-004**: In 100% of partial-mutation failure cases, autopilot blocks instead of mixing managers and emits recoverable state with enough detail to prevent duplicate PRs.
- **SC-005**: A reviewer can identify selected manager, command plan, fallback reason, version/support outcome, and resulting topology from emitted evidence in under 2 minutes.
- **SC-006**: Claude Code and Codex guidance describe equivalent stack-manager behavior for supported, fallback, and blocked paths in parity verification.

## Out of Scope

- Making `gh-stack` a required dependency.
- Duplicating stack-manager scripts under `codex-skills/`.
- Adding stack-manager features beyond create, sync, restack, fallback, evidence, and safety.
- Retrying the explicit `gh` path after partial `gh-stack` mutation.
- Changing PRSG-012 packet semantics or PRSG-013 marker semantics outside what is required to preserve them.

## Assumptions

- The explicit `gh` base/head path remains the canonical behavior for unsupported or unsafe environments.
- Support detection includes command availability, version/support outcome, repository compatibility, branch topology compatibility, and a safe pre-mutation confidence check.
- The exact `gh-stack` command/version capability matrix will be resolved during planning without changing the feature scope.
- Final evidence field names will be chosen during planning to minimize schema churn while preserving the required decision content.
- Repository full verification remains `bash tests/speckit-pro/run-all.sh`.
