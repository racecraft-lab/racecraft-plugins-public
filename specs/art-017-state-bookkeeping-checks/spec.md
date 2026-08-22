# Feature Specification: Arm The Accidentally-Advisory State Bookkeeping Checks

**Feature Branch**: `art-017-state-bookkeeping-checks`

**Created**: 2026-08-22

**Status**: Draft

**Input**: User description: "Define ART-017 so three current-run state invariants independently fail the exact status-evidence invocation that already reports them, while legacy coverage debt remains advisory."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Halt Contradictory Current-Run State (Priority: P1)

[US1] As an autopilot operator, I need a run with multiple in-progress steps, duplicate steps, or reordered checkpoints to stop at the same status-evidence gate that already reports those problems, so the autopilot cannot advance from contradictory bookkeeping.

**Why this priority**: This is the defect ART-017 repairs. The current report can name malformed state while the scoped gate still returns success, which makes resumed or phase-transitioned runs look healthier than they are.

**Independent Test**: Can be fully tested by starting from one clean workflow/state pair, applying one isolated mutation for each of the three current-run invariants, and confirming the exact status-evidence check fails for each mutation while the full diagnostic report is still emitted.

**Acceptance Scenarios**:

1. **Given** a state with more than one in-progress step and no duplicate-step or ordering violation, **When** the status-evidence gate runs, **Then** the run fails and reports `in_progress_errors`.
2. **Given** a state with duplicate step entries and no in-progress or ordering violation, **When** the status-evidence gate runs, **Then** the run fails and reports `duplicate_state_steps`.
3. **Given** a state with reordered checkpoints and no in-progress or duplicate-step violation, **When** the status-evidence gate runs, **Then** the run fails and reports `state_order_errors`.
4. **Given** a clean workflow/state pair, **When** the status-evidence gate runs, **Then** the run succeeds and emits the same report shape consumers already receive.

---

### User Story 2 - Keep Rule Intent And Evidence Honest (Priority: P2)

[US2] As a SpecKit Pro maintainer, I need each newly blocking problem key's rule membership, intent record, negative control, and corpus evidence to agree, so an accidentally advisory state invariant cannot survive as a green gate.

**Why this priority**: The implementation is only trustworthy if the behavioral gate, classification record, and regression evidence move together. This prevents future maintainers from reading an advisory classification that no longer matches runtime behavior.

**Independent Test**: Can be fully tested by comparing the intent classification for the three named keys with their status-evidence rule membership, checking every tracked workflow that has an adjacent state file, and verifying legacy coverage advisories remain nonblocking.

**Acceptance Scenarios**:

1. **Given** the three ART-017 problem keys, **When** maintainers inspect their intent records and rule membership, **Then** each key is classified as gated under status-evidence with a reason tied to current-run state integrity.
2. **Given** any other advisory problem key, **When** the status-evidence gate runs, **Then** that key remains advisory unless separately authorized by another spec.
3. **Given** a tracked workflow with an adjacent `autopilot-state.json`, **When** the tracked-pair corpus regression runs, **Then** the pair succeeds without synthesizing state for workflows that do not have an adjacent state file.
4. **Given** a reviewer opens the PR, **When** they follow the review packet, **Then** they can trace every requirement to changed files, generated artifact refreshes, and verification evidence.

### Edge Cases

- A malformed state may contain more than one existing diagnostic key; the report still includes all diagnostics, while status-evidence authority changes only for the three ART-017 keys.
- A tracked workflow without an adjacent `autopilot-state.json` is outside the pair corpus and must not receive silently synthesized state.
- Legacy coverage advisories such as missing state-prefix or missing post-item coverage can still appear in the report, but they must not become blocking under status-evidence.
- Final integration may occur after ART-008 lands; ART-017 remains independently developed and serializes only the final rebase, artifact regeneration, and verification boundary.
- Existing consumers may depend on problem-key names and JSON report shape; ART-017 must preserve those contracts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: [US1] The status-evidence rule MUST treat `in_progress_errors` as a blocking current-run state invariant.
- **FR-002**: [US1] The status-evidence rule MUST treat `duplicate_state_steps` as a blocking current-run state invariant.
- **FR-003**: [US1] The status-evidence rule MUST treat `state_order_errors` as a blocking current-run state invariant.
- **FR-004**: [US2] The system MUST NOT add any other advisory problem key to status-evidence as part of ART-017.
- **FR-005**: [US2] Each of the three ART-017 problem keys MUST have an intent verdict that matches its blocking status-evidence rule membership.
- **FR-006**: [US2] Each updated intent reason MUST explain the current-run state invariant protected by that problem key.
- **FR-007**: [US1] The diagnostic report MUST preserve its existing shape and problem-key values when one of the three ART-017 keys fails.
- **FR-008**: [US1] The scoped return result MUST change only for status-evidence authority and the three updated intent verdicts.
- **FR-009**: [US1] Regression evidence MUST include one clean workflow/state builder and exactly three isolated mutations, one per ART-017 problem key.
- **FR-010**: [US1] Each isolated mutation MUST prove that its target problem key alone makes the exact status-evidence gate fail while the other two ART-017 problem lists remain empty.
- **FR-011**: [US1] The clean control MUST prove that a valid workflow/state pair succeeds under the same status-evidence gate.
- **FR-012**: [US2] Regression evidence MUST cover every tracked workflow that has an adjacent `autopilot-state.json`.
- **FR-013**: [US2] Workflows without adjacent state files MUST be excluded from the pair corpus rather than supplied with synthetic state.
- **FR-014**: [US2] The authored autopilot guidance MUST distinguish legacy coverage debt from the three blocking current-run state invariants in one source of truth.
- **FR-015**: [US2] Generated mirrors, payloads, proofs, and reference outputs MUST be refreshed by repository tooling rather than hand-edited.
- **FR-016**: [US2] The PR review packet MUST include scope budget, traceability, verification evidence, generated-artifact status, known gaps, and final integration notes.

### Reviewability Notes *(if applicable)*

- ART-017 repairs one behavioral gate and its evidence. Generated release, installed-cache, and reference surfaces are derived outputs and are reviewable only through the regeneration evidence, not by hand inspection as authored source.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter, seed/config, docs/process
- **Secondary surfaces, if any**: Generated mirrors, release payloads, installed-cache proofs, and docs references as derived verification surfaces
- **Projected reviewable LOC**: 125
- **Projected production files**: 3
- **Projected total files**: 5
- **Budget result**: warning accepted
- **Split decision**: One vertical slice. Rule membership, intent classification, isolated controls, tracked-pair corpus evidence, and the narrow authored explanation are one independently testable repair. Splitting membership from verdicts would create a misleading intermediate state.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.
- ART-017 review order MUST start with authored rule and intent changes, then isolated negative controls, then tracked-pair corpus evidence, then authored prose, and finally generated artifact refreshes.
- The review packet MUST call out that ART-008 is independent and that ART-017 must rebase and regenerate shared derived artifacts before ready or merge if ART-008 lands first.

### Key Entities *(include if feature involves data)*

- **State Diagnostic Key**: A named problem list emitted by state validation. ART-017 changes blocking authority only for `in_progress_errors`, `duplicate_state_steps`, and `state_order_errors`.
- **Rule Intent Record**: The maintained classification that explains whether a diagnostic key is advisory or gated and why.
- **Workflow/State Pair**: A tracked workflow file and its adjacent `autopilot-state.json` used as real corpus evidence for the status-evidence gate.
- **Review Packet**: The PR-facing evidence bundle that lets reviewers trace requirements to changed files, generated outputs, and verification commands.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 3 of 3 ART-017 diagnostic keys are explicit status-evidence members, and 0 additional advisory keys are newly armed.
- **SC-002**: 3 of 3 ART-017 intent records are classified as gated with reasons tied to current-run state integrity.
- **SC-003**: 3 of 3 isolated negative controls fail the exact status-evidence gate with only their target ART-017 problem list populated among the three new keys.
- **SC-004**: 1 clean workflow/state control succeeds under the same status-evidence gate.
- **SC-005**: 100% of tracked workflows with adjacent state files succeed in the tracked-pair corpus regression.
- **SC-006**: Legacy coverage advisories remain nonblocking under status-evidence in at least one explicit regression case.
- **SC-007**: The diagnostic report keeps the same top-level shape and existing problem-key names before and after the ART-017 behavior change.
- **SC-008**: The PR evidence bundle lists targeted checks, generated-artifact refreshes, and the full repository verification command needed before ready or merge.

## Assumptions

- ART-014 is complete and remains the dependency that identified the three accidentally advisory state bookkeeping keys.
- ART-017 is independent from ART-008 until the final integration boundary, where rebasing and derived-artifact regeneration settle shared outputs.
- The existing status-evidence gate remains the correct operator-facing authority for autopilot phase-transition state checks.
- The nine remaining advisory keys are outside ART-017 unless a future spec reclassifies them.
- Repository governance requires strict test-first evidence, generated-artifact regeneration through tooling, and final verification before merge.
