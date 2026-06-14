# Tasks: Optional gh-stack stack manager integration

**Input**: Design documents from `specs/prsg-014-optional-gh-stack-stack-manager-integration/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/stack-manager-decision.schema.json`, and `docs/ai/specs/.process/PRSG-014-design-concept.md`

**Tests**: Required and test-first. PRSG-014 explicitly requires Layer 4 fake `gh`/`gh stack` fixtures, schema/evidence assertions, Layer 7 replay coverage, and Layer 8 Claude/Codex guidance parity before implementation is complete.

**Reviewability**: Plan declares 325 projected reviewable LOC, 5 production files, and 14 total files. The post-G5 task reviewability gate recorded a size-only block (`reviewable_loc=2840`, `total_files=111`) with no correctness or safety blocker, so implementation proceeds through the PRSG-013 marker plan `foundation -> us1 -> us2 -> us3 -> us4`; T066-T071 are folded into `us4` as polish. If implementation expands beyond 400 reviewable LOC, 6 production files, 15 total files, or one primary surface, run the reviewability checkpoint before continuing. If it expands beyond 800 reviewable LOC, 8 production files, 25 total files, or more than one primary surface without a ratified exception, stop and split the spec.

## Phase 1: Setup (Shared Test Scaffolding)

**Purpose**: Prepare deterministic fixture locations and reviewability guardrails used by all story tests.

- [x] T001 [P] Create stack-manager fake CLI fixture index in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/README.md`
- [x] T002 [P] Create shared PRS/marker topology fixture in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/topology/prsg-014-prs.json`
- [x] T003 [P] Create shared PRSG-012 packet fixture set in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/packets/valid-prsg-014/`
- [x] T004 [P] Create expected stack-manager decision fixture skeleton in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/expected/decision-supported.json`
- [x] T005 Verify declared PRSG-014 file scope against the reviewability budget in `specs/prsg-014-optional-gh-stack-stack-manager-integration/plan.md`

---

## Phase 2: Foundational (Shared Contracts and Harness)

**Purpose**: Add shared contract and harness prerequisites that block all user stories.

**Critical**: No user story implementation should begin until these shared schema and harness tasks are complete.

### Tests and Fixtures

- [x] T006 [P] Add schema fixture cases for accepted and rejected stack-manager decisions in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/schema/stack-manager-decision-cases.json`
- [x] T007 Add schema compatibility assertions for emission, restack, and PRS evidence path references in `tests/speckit-pro/layer4-scripts/test-detect-stack-manager.sh`

### Implementation

- [x] T008 [P] Create shared production stack-manager decision schema in `speckit-pro/skills/speckit-autopilot/contracts/stack-manager-decision.schema.json`
- [x] T009 [P] Add explicit `stack_manager_decision` and `stack_manager_evidence_path` fields to `speckit-pro/skills/speckit-autopilot/contracts/multi-pr-emission-state.schema.json`
- [x] T010 [P] Add explicit `stack_manager_decision` and `stack_manager_evidence_path` fields to `speckit-pro/skills/speckit-autopilot/contracts/restack-output.schema.json`
- [x] T011 [P] Add optional stack-manager evidence path reference to `speckit-pro/skills/speckit-autopilot/contracts/prs-v2.schema.json`
- [x] T012 Create executable shell skeleton for shared detection in `speckit-pro/skills/speckit-autopilot/scripts/detect-stack-manager.sh`

**Checkpoint**: Shared contract and detector entrypoint exist; user story tasks can now proceed.

---

## Phase 3: User Story 1 - Detect support before mutation (Priority: P1) MVP

**Goal**: Operators can see whether optional `gh-stack` is available, supported, compatible, and safe before any branch or PR topology mutation.

**Independent Test**: Run detection fixtures for supported, missing, unsupported, ambiguous, read-only-proof-failed, topology-incompatible, and injection cases and confirm decision evidence is emitted before mutation.

### Tests for User Story 1

- [x] T013 [P] [US1] Add supported fake `gh stack` fixture executable in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/fake-gh/supported/gh`
- [x] T014 [P] [US1] Add missing `gh stack` fixture executable in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/fake-gh/missing/gh`
- [x] T015 [P] [US1] Add unsupported-version fake `gh stack` fixture executable in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/fake-gh/unsupported/gh`
- [x] T016 [P] [US1] Add ambiguous, read-only-proof-failed, and topology-incompatible detection case matrix in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/cases/detection-matrix.json`
- [x] T017 [US1] Add detection matrix assertions for supported, missing, unsupported, ambiguous, read-only-proof-failed, and topology-incompatible cases in `tests/speckit-pro/layer4-scripts/test-detect-stack-manager.sh`
- [x] T018 [US1] Add selected manager, reason, fallback reason, command plan, topology, and bounded stdout/stderr assertions in `tests/speckit-pro/layer4-scripts/test-detect-stack-manager.sh`
- [x] T019 [US1] Add FR-024 deterministic decision, read-only proof, command execution, recovery, and workflow evidence path assertions in `tests/speckit-pro/layer4-scripts/test-detect-stack-manager.sh`
- [x] T020 [US1] Add FR-026 and FR-027 executable allowlist, argv string, branch operand, and bounded argument assertions in `tests/speckit-pro/layer4-scripts/test-detect-stack-manager.sh`
- [x] T021 [US1] Add FR-028 injection guard assertions for malicious refs, PR body paths, evidence paths, fake CLI controls, and display strings in `tests/speckit-pro/layer4-scripts/test-detect-stack-manager.sh`

### Implementation for User Story 1

- [x] T022 [US1] Implement `gh stack` availability, version, repository support, read-only proof, and topology compatibility checks in `speckit-pro/skills/speckit-autopilot/scripts/detect-stack-manager.sh`
- [x] T023 [US1] Implement `selected_manager`, `reason`, `fallback_reason`, `mutation_boundary`, and argv-only `command_plan` output in `speckit-pro/skills/speckit-autopilot/scripts/detect-stack-manager.sh`
- [x] T024 [US1] Implement deterministic repo-relative evidence path derivation and persistence under `specs/prsg-014-optional-gh-stack-stack-manager-integration/.process/stack-manager/` in `speckit-pro/skills/speckit-autopilot/scripts/detect-stack-manager.sh`
- [x] T025 [US1] Implement argv shape, branch ref, body path, evidence path, fake CLI control, and bounded stdout/stderr validation in `speckit-pro/skills/speckit-autopilot/scripts/detect-stack-manager.sh`
- [x] T026 [US1] Run `bash tests/speckit-pro/layer4-scripts/test-detect-stack-manager.sh` and record the result for `tests/speckit-pro/layer4-scripts/test-detect-stack-manager.sh`

**Checkpoint**: US1 is independently testable with `bash tests/speckit-pro/layer4-scripts/test-detect-stack-manager.sh`.

---

## Phase 4: User Story 2 - Use supported stack manager with fallback (Priority: P2)

**Goal**: Autopilot uses `gh-stack` for stack-aware create/sync only after support checks pass; unsupported repositories continue to use explicit `gh pr create/edit --base --head --body-file`.

**Independent Test**: Run supported and fallback emission fixtures and confirm branch names, explicit base topology, PR packet validation, marker order, decision evidence, and retry reconciliation are preserved.

### Tests for User Story 2

- [x] T027 [P] [US2] Add supported create/sync emission fixture data in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/emission/supported/`
- [x] T028 [P] [US2] Add fallback-before-mutation emission fixture data in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/emission/fallback/`
- [x] T029 [P] [US2] Add partial-mutation and unknown-side-effect emission fixture data in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/emission/partial-mutation/`
- [x] T030 [P] [US2] Add duplicate-retry reconciliation emission fixture data in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/emission/duplicate-retry/`
- [x] T031 [US2] Add supported `gh stack link`, fallback explicit-`gh` create/sync, and invalid/stale packet hard-block assertions in `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh`
- [x] T032 [US2] Add fallback-before-mutation, partial-mutation, and `partial_mutation_unknown` blocked recovery assertions in `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh`
- [x] T033 [US2] Add duplicate retry reconciliation assertions for slice ID, head branch, base branch, PR number or URL, head SHA, and packet hash in `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh`
- [x] T034 [US2] Add emission FR-024, FR-026, FR-027, and FR-028 evidence path, argv, ref, body path, fake CLI, and injection assertions in `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh`

### Implementation for User Story 2

- [x] T035 [US2] Update emission to call shared detection before mutation and load the stack-manager decision in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`
- [x] T036 [US2] Preserve PRSG-012 packet-owned explicit `gh pr create/edit --base --head --title --body-file` behavior before `gh stack` linking, and block invalid or stale packets before either manager can create, edit, link, or sync in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`
- [x] T037 [US2] Implement supported `gh stack link` and proven sync command execution after PR reconciliation in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`
- [x] T038 [US2] Implement explicit-`gh` fallback before mutation and blocked recovery after partial or unknown `gh-stack` mutation in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`
- [x] T039 [US2] Implement duplicate retry reconciliation before create or sync operations in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`
- [x] T040 [US2] Persist `stack_manager_decision`, `stack_manager_evidence_path`, command plan, fallback reason, and topology evidence in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`
- [x] T041 [US2] Run `bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh` and record the result for `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh`

**Checkpoint**: US2 is independently testable with `bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh`.

---

## Phase 5: User Story 3 - Restack safely after squash merges (Priority: P3)

**Goal**: Maintainers can restack through `gh-stack` when safe or through the existing fallback before mutation when it is not, while blocked resumes reload and revalidate recovery evidence.

**Independent Test**: Run supported-restack, fallback-restack, partial-mutation, and blocked-resume fixtures and confirm selected manager, fallback policy, recovery evidence, and deterministic blocked event supersede behavior.

### Tests for User Story 3

- [x] T042 [P] [US3] Add supported restack fake `gh stack rebase --upstack` fixture data in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/restack/supported/`
- [x] T043 [P] [US3] Add fallback restack unsupported, missing, ambiguous, and topology-incompatible fixture data in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/restack/fallback/`
- [x] T044 [P] [US3] Add restack partial-mutation and unknown-side-effect fixture data in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/restack/partial-mutation/`
- [x] T045 [P] [US3] Add blocked-resume fixture matrix for no-change reconciliation, topology drift, stale packet identity, and missing recovery evidence in `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/restack/blocked-resume/`
- [x] T046 [US3] Add supported and fallback restack assertions in `tests/speckit-pro/layer4-scripts/test-restack.sh`
- [x] T047 [US3] Add partial-mutation and `partial_mutation_unknown` blocked recovery assertions in `tests/speckit-pro/layer4-scripts/test-restack.sh`
- [x] T048 [US3] Add FR-025 blocked resume preflight, stale event supersede, and no explicit-`gh` fallback assertions in `tests/speckit-pro/layer4-scripts/test-restack.sh`
- [x] T049 [US3] Add restack selected manager, reason, command plan, topology, recovery, deterministic evidence path, and bounded output assertions in `tests/speckit-pro/layer4-scripts/test-restack.sh`

### Implementation for User Story 3

- [x] T050 [US3] Update restack to call shared detection and select `gh-stack` only after exact support proof in `speckit-pro/skills/speckit-autopilot/scripts/restack.sh`
- [x] T051 [US3] Preserve existing fallback `restack.sh --apply` and explicit `gh pr edit --base` behavior before mutation in `speckit-pro/skills/speckit-autopilot/scripts/restack.sh`
- [x] T052 [US3] Implement `gh stack rebase --upstack <first-remaining-branch>` plus proven sync or push command plan in `speckit-pro/skills/speckit-autopilot/scripts/restack.sh`
- [x] T053 [US3] Emit blocked recoverable state with `fallback_allowed=false` after partial or unknown `gh stack` mutation in `speckit-pro/skills/speckit-autopilot/scripts/restack.sh`
- [x] T054 [US3] Implement blocked resume preflight revalidation and deterministic workflow event supersede in `speckit-pro/skills/speckit-autopilot/scripts/restack.sh`
- [x] T055 [US3] Persist `stack_manager_decision`, `stack_manager_evidence_path`, command plan, recovery, and topology evidence in `speckit-pro/skills/speckit-autopilot/scripts/restack.sh`
- [x] T056 [US3] Run `bash tests/speckit-pro/layer4-scripts/test-restack.sh` and record the result for `tests/speckit-pro/layer4-scripts/test-restack.sh`

**Checkpoint**: US3 is independently testable with `bash tests/speckit-pro/layer4-scripts/test-restack.sh`.

---

## Phase 6: User Story 4 - Review stack-manager evidence (Priority: P4)

**Goal**: Reviewers can inspect evidence and guidance showing selected manager, fallback reason, command plan, version/support outcome, topology, and Claude/Codex parity without duplicate Codex implementation.

**Independent Test**: Run Layer 7 and Layer 8 fixtures and confirm no `grill-me`, no live `gh`, equivalent Claude/Codex guidance, and shared script/contract references.

### Tests for User Story 4

- [x] T057 [P] [US4] Add Layer 7 PRSG-014 replay fixture files in `tests/speckit-pro/layer7-integration/dispatch-fixtures/22-prsg-014-stack-manager-replay/README.md`, `tests/speckit-pro/layer7-integration/dispatch-fixtures/22-prsg-014-stack-manager-replay/prompt.txt`, `tests/speckit-pro/layer7-integration/dispatch-fixtures/22-prsg-014-stack-manager-replay/parser-fixture.jsonl`, and `tests/speckit-pro/layer7-integration/dispatch-fixtures/22-prsg-014-stack-manager-replay/expected.json`
- [x] T058 [P] [US4] Add Layer 8 guidance parity fixture files in `tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/README.md`, `tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/workflow.md`, `tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/env-teams.sh`, `tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/env-fallback.sh`, `tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/expected-equivalence.json`, and `tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/tolerance.json`
- [x] T059 [US4] Add Layer 7 expected assertions for phase routing, consensus routing, no `grill-me`, no live `gh`, and operator-facing stack-manager evidence terms in `tests/speckit-pro/layer7-integration/dispatch-fixtures/22-prsg-014-stack-manager-replay/expected.json`
- [x] T060 [US4] Add Layer 8 expected equivalence assertions for supported, fallback, blocked, recovery, shared script, and shared contract guidance in `tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/expected-equivalence.json`

### Implementation for User Story 4

- [x] T061 [US4] Update Claude Code operator guidance for supported, fallback, blocked, and resume behavior in `speckit-pro/skills/speckit-autopilot/references/post-implementation.md`
- [x] T062 [US4] Update Codex operator guidance with mirrored behavior and shared script/contract references in `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`
- [x] T063 [US4] Verify Codex guidance does not duplicate stack-manager scripts, schemas, or validators under `speckit-pro/codex-skills/speckit-autopilot/`
- [x] T064 [US4] Run `bash tests/speckit-pro/layer7-integration/run-dispatch-fixtures.sh` and record the result for `tests/speckit-pro/layer7-integration/dispatch-fixtures/22-prsg-014-stack-manager-replay/expected.json`
- [x] T065 [US4] Run `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run` and record the result for `tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/expected-equivalence.json`

**Checkpoint**: US4 is independently testable with Layer 7 dispatch fixtures and Layer 8 parity fixtures.

---

## Phase 7: Polish & Cross-Cutting Verification

**Purpose**: Final proof, traceability, and PR packet readiness.

- [x] T066 [P] Update PRSG-014 PR packet traceability, rollback, feature-flag, and known-gap notes in `specs/prsg-014-optional-gh-stack-stack-manager-integration/.process/pr-packet.md`
- [x] T067 Run structural validation with `bash tests/speckit-pro/run-all.sh --layer 1` and record the result for `tests/speckit-pro/run-all.sh`
- [x] T068 Run Layer 4 validation with `bash tests/speckit-pro/run-all.sh --layer 4` and record the result for `tests/speckit-pro/run-all.sh`
- [x] T069 Run Layer 7 validation with `bash tests/speckit-pro/layer7-integration/run-all-fixtures.sh` and record the result for `tests/speckit-pro/layer7-integration/run-all-fixtures.sh`
- [x] T070 Run Layer 8 parity validation with `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run` and record the result for `tests/speckit-pro/layer8-parity/run-parity-fixtures.sh`
- [x] T071 Run default repository verification with `bash tests/speckit-pro/run-all.sh` and record the result for `tests/speckit-pro/run-all.sh`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; fixture files can be created immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 and blocks all user stories.
- **US1 (Phase 3)**: Depends on Phase 2 and is the MVP because shared detection is required by emission and restack.
- **US2 (Phase 4)**: Depends on US1 because emission consumes the shared decision record.
- **US3 (Phase 5)**: Depends on US1 because restack consumes the shared decision record; can proceed in parallel with US2 after US1 when edits are coordinated.
- **US4 (Phase 6)**: Depends on the shared behavior from US1-US3 for final guidance wording, but Layer 7/8 fixture scaffolding can begin after Phase 2.
- **Polish (Phase 7)**: Depends on all selected user stories.

### User Story Dependencies

- **US1 (P1)**: No user-story dependency; required for MVP support detection.
- **US2 (P2)**: Depends on US1 detector and contract output.
- **US3 (P3)**: Depends on US1 detector and contract output; independent of US2 except shared schema fields.
- **US4 (P4)**: Depends on US1-US3 behavior for final guidance parity.

### Parallel Opportunities

- T001-T004 can run in parallel because they create separate setup fixture paths.
- T006 and T008-T011 can run in parallel after setup because they touch separate schema or fixture paths.
- T013-T016 can run in parallel because they create separate detection fixture paths.
- T027-T030 can run in parallel because they create separate emission fixture paths.
- T042-T045 can run in parallel because they create separate restack fixture paths.
- T057 and T058 can run in parallel because Layer 7 and Layer 8 fixture paths are independent.
- T066 can run in parallel with final verification preparation after implementation outputs exist.

---

## Parallel Example: Detection Fixtures

```bash
Task: "Add supported fake gh stack fixture executable in tests/speckit-pro/layer4-scripts/fixtures/stack-manager/fake-gh/supported/gh"
Task: "Add missing gh stack fixture executable in tests/speckit-pro/layer4-scripts/fixtures/stack-manager/fake-gh/missing/gh"
Task: "Add unsupported-version fake gh stack fixture executable in tests/speckit-pro/layer4-scripts/fixtures/stack-manager/fake-gh/unsupported/gh"
Task: "Add ambiguous, read-only-proof-failed, and topology-incompatible detection case matrix in tests/speckit-pro/layer4-scripts/fixtures/stack-manager/cases/detection-matrix.json"
```

## Parallel Example: Emission and Restack Fixture Matrices

```bash
Task: "Add supported create/sync emission fixture data in tests/speckit-pro/layer4-scripts/fixtures/stack-manager/emission/supported/"
Task: "Add duplicate-retry reconciliation emission fixture data in tests/speckit-pro/layer4-scripts/fixtures/stack-manager/emission/duplicate-retry/"
Task: "Add supported restack fake gh stack rebase --upstack fixture data in tests/speckit-pro/layer4-scripts/fixtures/stack-manager/restack/supported/"
Task: "Add blocked-resume fixture matrix in tests/speckit-pro/layer4-scripts/fixtures/stack-manager/restack/blocked-resume/"
```

## Implementation Strategy

### MVP First (US1)

1. Complete Phase 1 and Phase 2.
2. Complete US1 tests and detector implementation.
3. Validate with `bash tests/speckit-pro/layer4-scripts/test-detect-stack-manager.sh`.

### Incremental Delivery

1. US1: Shared support detection and decision evidence.
2. US2: Create/sync emission path consuming the shared decision.
3. US3: Restack path consuming the shared decision and blocked recovery state.
4. US4: Reviewer evidence, Layer 7 replay, and Layer 8 Claude/Codex guidance parity.

### Verification Bundle

```bash
bash tests/speckit-pro/layer4-scripts/test-detect-stack-manager.sh
bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
bash tests/speckit-pro/layer4-scripts/test-restack.sh
bash tests/speckit-pro/layer7-integration/run-dispatch-fixtures.sh
bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run
bash tests/speckit-pro/run-all.sh --layer 1
bash tests/speckit-pro/run-all.sh --layer 4
bash tests/speckit-pro/run-all.sh
```

## Notes

- Tests and fixtures come before the implementation tasks they verify.
- `gh-stack` remains optional and selected only after deterministic support, repository, topology, and read-only proof checks pass.
- Explicit `gh pr create/edit --base --head --body-file` remains the canonical fallback before mutation.
- After any attempted topology-changing `gh stack` command with partial or unknown side effects, fallback is not allowed; the flow blocks with recoverable state.
- Runtime command plans execute argv arrays only. Display command text is review evidence only and must never be executed or parsed back into argv.
- Shared behavior stays in `speckit-pro/skills/speckit-autopilot/scripts/` and `speckit-pro/skills/speckit-autopilot/contracts/`; Codex changes are guidance/parity only.
