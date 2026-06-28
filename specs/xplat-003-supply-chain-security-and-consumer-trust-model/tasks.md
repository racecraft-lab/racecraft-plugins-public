# Tasks: Supply-Chain Security and Consumer Trust Model

**Input**: Design documents from `specs/xplat-003-supply-chain-security-and-consumer-trust-model/`, plus `docs/ai/specs/.process/XPLAT-003-workflow.md` and `docs/ai/specs/.process/XPLAT-003-design-concept.md`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/supply-chain-control-contract.md`, `checklists/security.md`, `checklists/integration.md`, `checklists/reliability.md`

**Tests**: No code tests are generated for this decision spike. Validation tasks cover marker counts, spec-map freshness, diff hygiene, reviewability, and the smallest relevant shell gate.

**Reviewability**: XPLAT-003 remains a decision spike. Tasks must update only XPLAT-003 decision artifacts unless a validation command refreshes `SPEC-MOC.md`. Do not implement `speckit-pro-runner`, port helpers, rebuild generated payloads, edit release automation, or edit public docs to make native-support or supply-chain claims.

**Organization**: Tasks are grouped by user story so each decision slice can be reviewed independently before the final verification pass.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can be researched or drafted independently before consolidation
- **[Story]**: User story traceability (`US1`, `US2`, `US3`)
- Include exact file paths in descriptions

## Phase 1: Foundation

**Purpose**: Establish source evidence, scope guardrails, and reviewability before user-story work.

- [x] T001 Re-read and preserve Grill Me decisions from `docs/ai/specs/.process/XPLAT-003-design-concept.md` before editing `specs/xplat-003-supply-chain-security-and-consumer-trust-model/research.md`
- [x] T002 [P] Collect source-truth references from `docs/ai/specs/.process/XPLAT-003-workflow.md`, `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`, and `specs/xplat-003-supply-chain-security-and-consumer-trust-model/plan.md` into the decision-evidence notes in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/research.md`
- [x] T003 [P] Cross-check required evidence record shapes in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/data-model.md` against `specs/xplat-003-supply-chain-security-and-consumer-trust-model/contracts/supply-chain-control-contract.md`
- [x] T004 Verify the implementation scope remains decision-only in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/plan.md` and record any reviewability checkpoint needed before broader artifact edits
- [x] T004a [P] Record official Anthropic Claude Code and OpenAI Codex plugin/skill/hook/MCP/script/custom-agent documentation findings in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/research.md`
- [x] T004b [P] Reopen the XPLAT-002 Go decision explicitly in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md` with rationale, Rust/Zig equivalence conditions, and official-doc runtime-boundary constraints

**Checkpoint**: Foundation evidence is ready; user-story work can proceed in parallel.

---

## Phase 2: User Story 1 - Maintainer Control Decision (Priority: P1)

**Goal**: A maintainer can review one decision record that separates first-release controls, deferred hardening, explicit non-claims, and out-of-scope work.

**Independent Test**: A reviewer can inspect `research.md` and confirm every evaluated control is classified with rationale, owner, evidence, and acceptance gate.

- [x] T005 [P] [US1] Validate checksum and runner manifest first-release decisions in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/research.md` against `specs/xplat-003-supply-chain-security-and-consumer-trust-model/contracts/supply-chain-control-contract.md`
- [x] T006 [P] [US1] Validate vulnerability scanning, freshness, and exception-policy decisions in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/research.md` against `specs/xplat-003-supply-chain-security-and-consumer-trust-model/checklists/security.md` and `specs/xplat-003-supply-chain-security-and-consumer-trust-model/checklists/reliability.md`
- [x] T007 [P] [US1] Validate SBOM, signature, provenance, reproducible-build, audit, marketplace-enforcement, and trust-chain feasibility decisions in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/research.md`
- [x] T008 [US1] Consolidate the first-release, deferred-hardening, explicit-non-claim, and out-of-scope control matrix in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/research.md`
- [x] T009 [US1] Verify `specs/xplat-003-supply-chain-security-and-consumer-trust-model/research.md` satisfies SC-001, SC-004, SC-007, SC-008, SC-010, SC-011, SC-012, and SC-013 from `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`
- [x] T009a [US1] Consolidate platform capability evidence and installed-user runtime dependency boundary decisions in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/research.md`

**Checkpoint**: User Story 1 is independently reviewable as the maintainer trust-baseline decision.

---

## Phase 3: User Story 2 - Implementer Downstream Ownership (Priority: P1)

**Goal**: XPLAT-004, XPLAT-007, release automation, and public wording owners can identify their inputs, evidence, and acceptance gates while preserving the reopened runtime-decision blocker.

**Independent Test**: A planner can map every first-release control to a downstream owner surface and find no ownerless or gate-less required control.

- [x] T010 [P] [US2] Validate XPLAT-004 runner source and artifact ownership in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/plan.md` against `specs/xplat-003-supply-chain-security-and-consumer-trust-model/contracts/supply-chain-control-contract.md`
- [x] T011 [P] [US2] Validate XPLAT-007 generated-payload integrity, metadata propagation, consumer guidance, native UAT, and cutover ownership in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/plan.md`
- [x] T012 [P] [US2] Validate release-automation acceptance evidence remains assigned-not-implemented and not-claimable in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/data-model.md` and `specs/xplat-003-supply-chain-security-and-consumer-trust-model/contracts/supply-chain-control-contract.md`
- [x] T013 [US2] Consolidate downstream handoff language for XPLAT-004, XPLAT-007, release automation, docs, and release-note surfaces in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/plan.md`
- [x] T014 [US2] Verify `specs/xplat-003-supply-chain-security-and-consumer-trust-model/plan.md` satisfies SC-002, SC-005, SC-006, SC-009, SC-016, and SC-017 from `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`
- [x] T014a [US2] Add platform capability, runtime dependency boundary, and install completeness evidence contracts to `specs/xplat-003-supply-chain-security-and-consumer-trust-model/data-model.md` and `specs/xplat-003-supply-chain-security-and-consumer-trust-model/contracts/supply-chain-control-contract.md`

**Checkpoint**: User Story 2 is independently reviewable as the downstream owner handoff.

---

## Phase 4: User Story 3 - Consumer and Public Trust Boundary (Priority: P2)

**Goal**: Consumers and reviewers can understand local verification behavior and which public trust guarantees are intentionally not claimed.

**Independent Test**: A reviewer can compare public wording or release-note drafts against the XPLAT-003 claim boundary and classify each claim as allowed, deferred, or forbidden until implemented.

- [x] T015 [P] [US3] Validate consumer-local verification command shapes, metadata lookup, and no Bash or jq constraints in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/contracts/supply-chain-control-contract.md`
- [x] T016 [P] [US3] Audit current public-claim surfaces without editing them and record allowed, deferred, and forbidden claim patterns in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/research.md`
- [x] T017 [US3] Consolidate checksum mismatch, unavailable metadata, and maintainer reacceptance behavior in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/data-model.md` and `specs/xplat-003-supply-chain-security-and-consumer-trust-model/contracts/supply-chain-control-contract.md`
- [x] T018 [US3] Verify consumer and public trust artifacts satisfy SC-003, SC-007, SC-014, SC-015, SC-016, and SC-017 from `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`
- [x] T018a [US3] Record Codex custom-agent TOML registration as an install-completeness gate distinct from Claude Code plugin agents in `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`, `data-model.md`, `contracts/supply-chain-control-contract.md`, and `quickstart.md`

**Checkpoint**: User Story 3 is independently reviewable as the consumer verification and public-claim boundary.

---

## Phase 5: Polish & Verification

**Purpose**: Confirm the decision-spike task set and final artifacts remain clean, traceable, and within scope.

- [x] T019 [P] Re-run marker and gate checks for `specs/xplat-003-supply-chain-security-and-consumer-trust-model/` after official-doc/rejected-runtime additions: `bash speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh all specs/xplat-003-supply-chain-security-and-consumer-trust-model`, `bash speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh G7 specs/xplat-003-supply-chain-security-and-consumer-trust-model`, and `bash speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh tasks specs/xplat-003-supply-chain-security-and-consumer-trust-model`, recording the size-only tasks-mode block and actual diff-mode no-blocker result
- [x] T020 [P] Re-run spec-map and diff hygiene checks for `specs/xplat-003-supply-chain-security-and-consumer-trust-model/` after official-doc/rejected-runtime additions: `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"`, `git diff --check`, and `git diff --name-only`, then refresh only `SPEC-MOC.md` if the index check requires it and confirm no implementation, generated-payload, release-workflow, or public-claim files changed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundation (Phase 1)**: No dependencies.
- **User Stories (Phases 2-4)**: Depend on Phase 1. US1, US2, and US3 can proceed in parallel after foundation because they cover separate decision views.
- **Polish & Verification (Phase 5)**: Depends on the selected user-story artifacts being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundation; does not depend on US2 or US3.
- **User Story 2 (P1)**: Can start after Foundation; consumes the same source truth but remains independently testable through owner and gate mapping.
- **User Story 3 (P2)**: Can start after Foundation; public-surface audit is read-only and must not edit public docs.

### Parallel Opportunities

- T002 and T003 can run in parallel during Foundation.
- T005, T006, and T007 can run in parallel for US1 evidence classification.
- T010, T011, and T012 can run in parallel for US2 ownership checks.
- T015 and T016 can run in parallel for US3 consumer and public trust review.
- T019 and T020 can run in parallel after artifact edits are complete, except `SPEC-MOC.md` refresh must be serialized if the index check fails.

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 Foundation.
2. Complete Phase 2 User Story 1 so maintainers have the control baseline decision.
3. Stop and validate User Story 1 independently before expanding downstream handoff or public-claim artifacts.

### Incremental Delivery

1. Foundation evidence and scope guard.
2. US1 maintainer control decision.
3. US2 downstream ownership handoff.
4. US3 consumer and public trust boundary.
5. Polish and verification.

### Decision-Spike Guardrails

- Do not build `speckit-pro-runner`.
- Do not port helpers or change active invocation paths.
- Do not rebuild generated Claude or Codex payloads.
- Do not edit release workflows.
- Do not edit public docs or release notes to make new native-support or supply-chain claims.
- Preserve the Grill Me decisions in `docs/ai/specs/.process/XPLAT-003-design-concept.md`.

## Notes

- [P] tasks identify independent research, audit, or validation work; consolidation tasks remain serial.
- Each user story has an independent review target and acceptance check.
- Deferred controls remain deferred unless implementation evidence and claim necessity promote them in a later spec.
