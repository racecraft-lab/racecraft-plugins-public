# Feature Specification: Optional gh-stack stack manager integration

**Feature Branch**: `prsg-014-optional-gh-stack-stack-manager-integration`

**Created**: 2026-06-14

**Status**: Draft

**Input**: User description: "Add optional gh-stack stack-manager integration so autopilot can use native stack create/sync/restack when deterministic support checks pass, while preserving explicit gh base/head fallback everywhere else."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Detect support before mutation (Priority: P1)

As a SpecKit operator running autopilot on a split-PR spec, I can see whether optional `gh-stack` support is available, supported, compatible, and safe before any branch or PR topology is changed.

**Why this priority**: Operators need deterministic pre-mutation evidence before trusting an optional stack manager. This is the safety gate for every other behavior in this feature.

**Independent Test**: Can be tested by running stack-manager detection against supported, missing, unsupported, ambiguous, topology-incompatible, and read-only-proof-failed environments and confirming the selected manager and reason are recorded before mutation.

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

1. **Given** support detection passes and all planned PR packets have validated title/body content, **When** autopilot emits stacked PRs, **Then** it creates or updates PRs from packet-owned `gh pr create/edit` metadata before using `gh stack` only for stack topology linking or sync and records the resulting topology evidence.
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
- `gh-stack` status or read-only proof behavior is ambiguous and cannot prove safe execution.
- The repository or branch topology is incompatible with stack-aware create, sync, or restack behavior.
- PR packet title/body validation fails before PR creation.
- PRSG-013 marker ordering or branch naming would be changed by the selected path.
- A `gh-stack` command partially mutates topology and a later command fails.
- A `gh-stack` command times out, crashes, or returns ambiguous output after a topology-changing command has been attempted, leaving side effects unknown.
- A retry could duplicate PRs or retarget branches incorrectly without recoverable evidence.
- Claude Code and Codex guidance drift from the shared stack-manager behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Autopilot MUST determine whether optional `gh-stack` support is available through the GitHub CLI extension invocation (`gh stack`), supported, repository-compatible, topology-compatible, and safe before any stack-manager command mutates branch or PR topology.
- **FR-002**: Autopilot MUST record a deterministic `stack_manager_decision` object containing schema version, selected manager, reason, fallback reason when applicable, mutation boundary, `gh_stack.available`, `gh_stack.supported`, `gh_stack.reason`, support status, version/invocation details, repository compatibility, topology compatibility, read-only proof status, command plan, PR/branch topology, and repo-relative evidence path.
- **FR-003**: Autopilot MUST select `gh-stack` only when all support and safety checks pass.
- **FR-004**: Autopilot MUST fall back to the explicit `gh` base/head path before mutation when `gh-stack` is missing, unsupported, ambiguous, incompatible, or unsafe.
- **FR-005**: Autopilot MUST preserve the explicit `gh` base/head path as the canonical fallback and MUST NOT make `gh-stack` a required dependency.
- **FR-006**: Autopilot MUST preserve PRSG-012 PR packet title/body generation and validation before any PR creation or sync action; for stack-wide `gh stack` mutations, every planned marker packet, branch, base, checkpoint SHA, and scoped verification record MUST be valid before the first mutating `gh stack` command.
- **FR-007**: Autopilot MUST preserve PRSG-013 marker order, branch names, and explicit base topology across both selected stack-manager and fallback paths.
- **FR-008**: Autopilot MUST support stack-aware PR creation and sync when support checks pass by keeping packet-owned `gh pr create/edit --base --head --title --body-file` metadata authoritative, then using `gh stack link` or another proven version-supported `gh stack` operation only for stack topology linking or sync.
- **FR-009**: Autopilot MUST support post-squash restack through `gh stack rebase --upstack <first-remaining-branch>` plus any required proven sync/push step only when the installed version matrix proves exact noninteractive scope support; otherwise it MUST use the existing `restack.sh --apply` / `gh pr edit --base` fallback before mutation.
- **FR-010**: Autopilot MUST treat the first attempted topology-changing stack-manager command as the no-fallback mutation boundary, including local branch creation or update, remote branch push, PR create/edit/sync, rebase/restack, or stack metadata write.
- **FR-011**: Autopilot MUST NOT mix stack managers after any mutating `gh stack` command has been attempted unless same-manager reconciliation proves the operation left no topology changes.
- **FR-012**: Autopilot MUST block with recoverable evidence when a partial or unknown `gh stack` mutation has occurred and continuing would require switching managers or risk ambiguous topology.
- **FR-013**: Autopilot MUST classify failed `gh stack` commands with unproven side effects as `partial_mutation_unknown` and set `fallback_allowed=false` until an operator or same-manager reconciliation proves a safe resume boundary.
- **FR-014**: Autopilot MUST avoid duplicate PRs on retry by reconciling current state against expected slice ID, head branch, base branch, PR number or URL when known, head SHA, and the current validated PR packet before any create or sync operation.
- **FR-015**: Autopilot MUST keep stack-manager detection, emission, and restack decisions in shared behavior used by both emission and restack flows.
- **FR-016**: Claude Code and Codex operator guidance MUST describe the same supported, fallback, and blocked stack-manager behaviors and MUST reference the shared stack-manager scripts/contracts. PRSG-014 MUST NOT duplicate stack-manager implementation, schemas, or validators under `codex-skills/`.
- **FR-017**: Verification evidence MUST cover supported, missing, unsupported, ambiguous, read-only-proof-failed, topology-incompatible, fallback-before-mutation, partial-mutation, unknown-side-effect, duplicate-PR retry, supported restack, fallback restack, schema compatibility, Layer 7 live-safe replay, and Layer 8 operator guidance parity scenarios.
- **FR-018**: The feature MUST NOT add unrelated stack-manager capabilities beyond create, sync, restack, fallback, evidence, and safety.
- **FR-019**: Stack-manager operations MUST store and execute command plans only as argv arrays. The implementation MUST NOT use `eval`, `bash -c`, `sh -c`, or any joined command string as an executable source for `gh stack`, `gh pr`, `git`, or fake-CLI fixture invocations. Human-readable command text MAY be rendered from argv for review evidence only and MUST NOT be re-parsed for execution.
- **FR-020**: Before any argv element is included in a stack-manager command, branch names and PR body paths MUST be validated against the applicable PRSG-012/PRSG-013 packet and topology contracts. Invalid values MUST block before command capture or mutation.
- **FR-021**: Stack-manager command evidence MUST capture exit status plus bounded stdout/stderr tails, with the byte or line limit defined in Plan, rather than unbounded command output.
- **FR-022**: The stack-manager decision contract MUST be versioned in a shared schema and referenced through explicit schema fields in emission command logs, persisted multi-PR emission state, and restack output/recovery evidence. PRS v2 topology records MUST remain topology-focused unless they reference a stack-manager evidence path.
- **FR-023**: Layer 7 PRSG-014 replay coverage MUST be orchestration proof only: phase/consensus routing, no `grill-me`, and operator-facing stack-manager evidence terms. It MUST NOT require real `gh`, real `gh stack`, network PR creation, or committed live transcript refresh.
- **FR-024**: Stack-manager decision, read-only proof, command execution, recovery, and workflow evidence paths MUST be deterministic repo-relative paths under the target feature `.process/stack-manager/` directory or `docs/ai/specs/.process/` workflow directory. Evidence path values MUST NOT depend on timestamps, random temporary names, absolute host paths, or shell display strings.
- **FR-025**: Resume after a blocked stack-manager operation MUST reload the prior decision and recovery evidence, revalidate current topology, PR identity, base/head refs, head SHA, and packet identity before any resumed create/sync/restack command, and supersede stale blocked workflow events through a deterministic event id instead of appending ambiguous duplicates.
- **FR-026**: Stack-manager executable positions and command shapes MUST be allowlisted before command capture. Runtime command plans MAY contain only canonical `["gh", "stack", ...]`, explicit `["gh", "pr", ...]`, `["git", ...]`, or repo-local validator argv shapes required by PRSG-014. Fake CLI fixtures MUST be injected only through test-scoped PATH shims or controlled executable paths and MUST NOT replace the persisted runtime argv shape.
- **FR-027**: Stack-manager argv elements MUST be non-empty bounded strings and MUST reject NUL, newline, carriage return, and other control characters before command capture. Branch/base operands used by `gh stack` MUST pass git ref validation and MUST NOT be accepted as option-looking operands unless the selected command shape provides an explicit operand delimiter or uses PR-number operands instead.
- **FR-028**: Security verification MUST include fixture coverage proving that malicious branch/base refs, PR body path traversal or absolute paths, evidence path traversal, fake CLI override abuse, and display command strings containing shell metacharacters all block before command capture or mutation.

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
- **Stack Manager Decision Contract**: The shared versioned schema for stack-manager decisions, referenced by emission, restack, and recovery evidence so existing schemas can reject unknown fields while still accepting the new decision record explicitly.
- **Command Plan**: The ordered set of stack create, sync, or restack actions represented as array-of-argv operation records with action, manager, argv, mutation status, slice ID, review order, preconditions, and reason. Each `argv` field is the sole executable representation; joined command strings are non-authoritative display text only and must not be executed or parsed back into argv.
- **Executable Command Shape**: The allowlisted argv prefix and argument layout for a planned operation. Runtime stack-manager shapes are limited to canonical `gh stack`, explicit `gh pr`, scoped `git`, and repo-local validator invocations; fake CLI test shims may simulate those executables but must not become persisted executable state.
- **Topology Evidence**: The observable branch and PR base/head relationships before and after stack-manager operations, derived from SpecKit PRS/marker state rather than inferred ad hoc from branch count alone.
- **PR Packet Evidence**: The validated title/body and traceability material that must exist before PR creation or sync.
- **Stack-Manager Evidence Path**: A repo-relative `.process` path that points to the persisted decision, read-only proof, command execution, recovery, or workflow event evidence. The path is derived from feature id, phase, operation, slice or review-order identity when present, and boundary command id when present.
- **Recoverable Block State**: The evidence emitted after partial or unknown mutation that allows an operator to inspect, repair, or resume without mixing managers or duplicating PRs. It includes the stack-manager decision, selected manager, failed operation action and argv, mutation boundary, per-operation status, pre-mutation topology, observed post-failure topology when available, prior successful PRs, next slice or resume boundary, PR numbers or URLs, head/base branches, head SHA, stdout/stderr tail, deterministic evidence paths, blocked workflow event id, resume preflight checks, stale-result policy, retry policy, and `fallback_allowed=false`.

### Verification Scope

- Layer 4 fake-CLI fixtures are the authoritative behavior proof for stack-manager selection, fallback, mutation boundaries, retry reconciliation, and restack. Runtime fixtures MUST fake canonical `gh stack` through fake `gh` argv dispatch; standalone `gh-stack` fakes MAY exist only for legacy or override compatibility tests.
- Fake CLI fixtures MUST be test-local and deterministic: canonical `gh stack` behavior is faked through PATH-scoped fake `gh` dispatch, while any legacy standalone override path must resolve to a test fixture executable under the test sandbox or committed fixture tree. Runtime evidence must still record the canonical argv shape, not the fake executable path as the selected command.
- Layer 7 PRSG-014 fixtures prove orchestration shape and live-safe replay terms only. CLI behavior remains a Layer 4 responsibility, and live-safe replay must not create real PRs or require real networked GitHub operations.
- Layer 8 verifies operator guidance parity for Claude Code and Codex: both surfaces describe equivalent supported, fallback, and blocked stack-manager flows and point to the same shared scripts/contracts. Transcript-level Claude/Codex parity is out of scope until a stable Codex replay/transcript harness and schema exist.
- Plan MUST resolve the exact `gh stack` command/version capability matrix and make fixtures matrix-driven so unsupported or unproven capabilities fall back before mutation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of stack create, sync, and restack attempts emit stack-manager decision evidence before any topology mutation.
- **SC-002**: In supported-path verification, stack-aware create/sync/restack preserves branch names, explicit base topology, PRSG-013 marker order, and validated packet-owned PR title/body content.
- **SC-003**: In 100% of missing, unsupported, ambiguous, incompatible, or unsafe cases, autopilot selects the explicit fallback before mutation and records the reason.
- **SC-004**: In 100% of partial-mutation or unknown-side-effect failure cases, autopilot blocks instead of mixing managers and emits recoverable state with enough detail to prevent duplicate PRs.
- **SC-005**: A reviewer can identify selected manager, command plan, fallback reason, version/support outcome, and resulting topology from emitted evidence in under 2 minutes.
- **SC-006**: Layer 8 parity verification shows Claude Code and Codex guidance expose equivalent supported, fallback, and blocked stack-manager flows and reference the same shared scripts/contracts; executable behavior is verified through shared-script Layer 4/Layer 7 coverage and Layer 1 Codex structural parity.
- **SC-007**: In 100% of blocked stack-manager resume fixtures, stale recovery/workflow evidence is revalidated or superseded before mutation, and the run either resumes through proven same-manager reconciliation or remains blocked without duplicate PR creation or explicit-`gh` fallback.

## Out of Scope

- Making `gh-stack` a required dependency.
- Duplicating stack-manager scripts under `codex-skills/`.
- Duplicating stack-manager schemas or validators under `codex-skills/`.
- Adding stack-manager features beyond create, sync, restack, fallback, evidence, and safety.
- Retrying the explicit `gh` path after partial `gh-stack` mutation.
- Treating an ambiguous failed `gh stack` operation as safe to fallback without same-manager or operator reconciliation.
- Treating Layer 8 as transcript-level Claude/Codex replay before a stable Codex replay/transcript harness and schema exist.
- Changing PRSG-012 packet semantics or PRSG-013 marker semantics outside what is required to preserve them.

## Assumptions

- The explicit `gh` base/head path remains the canonical behavior for unsupported or unsafe environments.
- Support detection treats `gh stack` as the canonical GitHub CLI extension invocation. Test fixtures may use controlled fake command paths, but runtime detection should not require a standalone `gh-stack` binary.
- Supported emission keeps PRSG-012 packet-owned metadata authoritative: packets are rendered and validated first, PRs are created or updated with explicit `gh pr create/edit`, and `gh stack link` or another proven supported `gh stack` command is used only after that for stack topology.
- Support detection includes command availability, version/support outcome, repository compatibility, branch topology compatibility, and a safe pre-mutation confidence check.
- Safe pre-mutation `gh-stack` proof means read-only discovery only: command availability/version/support evidence plus parseable `gh stack view --json` topology output checked against SpecKit PRS/marker topology. Because mutating stack commands are not a safe detection dry-run, detection records a synthetic command plan instead and falls back before mutation when read-only proof is missing, unparseable, ambiguous, or topology-incompatible.
- Fallback to explicit `gh` is allowed after read-only detection or planning failures, but not after a topology-changing `gh stack` command has been attempted unless same-manager reconciliation proves no topology change occurred.
- Retries use deterministic reconciliation before mutation: current state is matched by slice ID, expected head branch, expected base branch, PR number or URL when known, head SHA, and current validated PR packet before creating or syncing anything.
- Supported restack uses `gh stack rebase --upstack <first-remaining-branch>` only when Plan proves the installed command version supports exact noninteractive upstack scope and any required sync/push behavior; otherwise `restack.sh --apply` remains the fallback before mutation.
- The exact `gh-stack` command/version capability matrix will be resolved during planning without changing the feature scope.
- Final evidence field names will be chosen during planning to minimize schema churn while preserving the required decision content, but the stack-manager decision must land through explicit schema fields instead of informal unknown properties.
- Evidence paths use the existing PRSG `.process` convention: generated machine evidence stays under `specs/<feature>/.process/`, reader-facing workflow events stay under `docs/ai/specs/.process/`, and all persisted references are repo-relative so resume works across machines and worktrees.
- Repository full verification remains `bash tests/speckit-pro/run-all.sh`.
