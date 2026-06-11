# Tasks: PRSG-010 Harden the Hatch + O5 Monster Epics

**Input**: Design documents from `specs/prsg-010-harden-the-hatch/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`

**Tests**: Required. PRSG-010 implementation is TDD-first: write or update the focused Layer 4 and parity tests before changing production scripts, schemas, skills, or docs.

**Reviewability**: Split required. Do not ship PRSG-010 as one implementation PR. Preserve the ordered split stack: PRSG-010A final hatch, PRSG-010B contextual router, PRSG-010C O5, PRSG-010D docs/parity/polish. Each implementation slice targets 700 or fewer reviewable LOC and must remain independently reviewable.

**Traceability**: Task descriptions include FR/SC coverage where practical. Phase 4 G4 checklist remediation coverage is carried through the no-PR backstop, weak-context safety checks, O5 flat-topology checks, generated-exception cleanup, and Claude/Codex parity tasks.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or only reads shared feature artifacts.
- **[Story]**: User-story tasks only. Setup, Foundational, and Polish tasks do not use story labels.
- Every task names the exact file or directory path it acts on.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the generated task plan stays aligned with the PRSG-010 split plan before implementation starts.

- [ ] T001 Verify the ordered PRSG-010A -> PRSG-010B -> PRSG-010C -> PRSG-010D split and per-slice reviewability budget in `specs/prsg-010-harden-the-hatch/plan.md`
- [ ] T002 [P] Review final gate state fields for FR-001 through FR-009 in `specs/prsg-010-harden-the-hatch/contracts/final-reviewability-gate-state.schema.json`
- [ ] T003 [P] Review re-slicing packet fields for FR-005 through FR-008 in `specs/prsg-010-harden-the-hatch/contracts/reslicing-packet.schema.json`
- [ ] T004 [P] Review O5 and routing contract fields for FR-010 through FR-022 in `specs/prsg-010-harden-the-hatch/contracts/o5-parent-manifest.schema.json` and `specs/prsg-010-harden-the-hatch/contracts/routing-decision.schema.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Apply shared constraints that must hold for every slice before user-story work begins.

**Critical**: No implementation slice should begin until this phase confirms the planned files remain inside the reviewability budget and plugin structure.

- [ ] T005 Validate that planned production, test, docs, and mirror paths still match the declared file operations in `specs/prsg-010-harden-the-hatch/plan.md`
- [ ] T006 [P] Confirm script safety, KISS, and test-before-merge obligations from `.specify/memory/constitution.md` before creating `speckit-pro/skills/speckit-autopilot/scripts/final-reviewability-backstop.sh` or `speckit-pro/skills/speckit-autopilot/scripts/o5-topology.sh`

**Checkpoint**: Foundation ready. Proceed in ordered split-stack sequence unless a slice is explicitly split further.

---

## Phase 3: User Story 1 - Stop Unreviewable PRs Before Creation (Priority: P1, Slice PRSG-010A)

**Goal**: Add a final reviewability backstop that stops before PR body generation, single PR creation, or multi-PR emission when the final gate blocks without a valid typed exception.

**Independent Test**: Run the final-backstop Layer 4 fixtures and confirm an unexcepted final gate block records state plus a re-slicing packet while leaving all PR creation assertions false.

### Tests for User Story 1

- [ ] T007 [P] [US1] Add failing block-without-exception fixture for FR-001, FR-002, FR-005, and FR-007 in `tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/block-no-exception/gate-result.json`
- [ ] T008 [P] [US1] Add failing valid typed exception fixture for FR-003 and FR-009 in `tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/valid-refactor-exception/exception.md`
- [ ] T009 [P] [US1] Add failing generated-boilerplate rejection fixture for FR-004 and SC-003 in `tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/generated-boilerplate/template.md`
- [ ] T010 [P] [US1] Add failing gate-error fixture for FR-002 in `tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/gate-error/gate-result.json`
- [ ] T011 [US1] Write failing Layer 4 assertions for no PR body, no `gh pr create`, no `multi-pr-emission.sh`, state output, and packet output in `tests/speckit-pro/layer4-scripts/test-final-reviewability-backstop.sh`
- [ ] T012 [P] [US1] Extend typed-exception compatibility assertions for invalid class, casing, trailing prose, and generated provenance in `tests/speckit-pro/layer4-scripts/test-reviewability-gate.sh`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Add the production final gate state schema for FR-005 and FR-009 in `speckit-pro/skills/speckit-autopilot/contracts/final-reviewability-gate-state.schema.json`
- [ ] T014 [P] [US1] Add the production re-slicing packet schema for FR-006 and FR-007 in `speckit-pro/skills/speckit-autopilot/contracts/reslicing-packet.schema.json`
- [ ] T015 [US1] Implement the final reviewability backstop orchestration and schema validation in `speckit-pro/skills/speckit-autopilot/scripts/final-reviewability-backstop.sh`
- [ ] T016 [US1] Wire the stop-before-PR boundary into Claude autopilot post-implementation guidance in `speckit-pro/skills/speckit-autopilot/references/post-implementation.md`
- [ ] T017 [US1] Mirror the stop-before-PR boundary into Codex autopilot post-implementation guidance in `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md`
- [ ] T018 [US1] Update Claude autopilot entry guidance so PR body generation and PR creation depend on the final backstop result in `speckit-pro/skills/speckit-autopilot/SKILL.md`
- [ ] T019 [US1] Mirror the autopilot entry guidance in `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`
- [ ] T020 [US1] Update phase execution guidance for resume/status handoff from `reslicing_required` state in `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`
- [ ] T021 [US1] Mirror the phase execution handoff guidance in `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`

### Validation for User Story 1

- [ ] T022 [US1] Run final backstop tests with `bash tests/speckit-pro/layer4-scripts/test-final-reviewability-backstop.sh`
- [ ] T023 [US1] Run typed-exception regression tests with `bash tests/speckit-pro/layer4-scripts/test-reviewability-gate.sh`

**Checkpoint**: PRSG-010A is independently testable when the backstop blocks unexcepted PR creation, honors valid typed exceptions, rejects generated boilerplate, and emits concrete PRSG-007/008/009 operator steps.

---

## Phase 4: User Story 3 - Route From Strong Contextual Evidence Only (Priority: P3, Slice PRSG-010B)

**Goal**: Promote flag-system, release-cadence, and consumer-locality evidence only when deterministic high-confidence criteria are met; weak evidence remains advisory and conservative.

**Independent Test**: Run atomicity-router fixtures showing high-confidence contextual evidence changes route or strategy as specified while weak, fixture-only, stale, conflicting, or shallow evidence never enters `signals[]`.

### Tests for User Story 3

- [ ] T024 [P] [US3] Add guarded cutover fixture for FR-017 and FR-018 in `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-guarded-cutover/tasks.md`
- [ ] T025 [P] [US3] Add release-held cutover fixture for FR-017 and FR-019 in `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-release-held/tasks.md`
- [ ] T026 [P] [US3] Add weak evidence fixture for FR-021 and SC-006 in `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-weak-evidence/tasks.md`
- [ ] T027 [P] [US3] Add consumer-locality and conflict fixture coverage for FR-020 and FR-021 in `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-consumer-locality/tasks.md`
- [ ] T028 [US3] Write failing contextual-probe assertions and schema checks in `tests/speckit-pro/layer4-scripts/test-atomicity-route.sh`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Add the production routing decision schema for FR-022 in `speckit-pro/skills/speckit-autopilot/contracts/routing-decision.schema.json`
- [ ] T030 [US3] Implement high-confidence contextual probe routing while preserving hard-atomic and releasability precedence in `speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh`
- [ ] T031 [US3] Ensure weak, conflicting, fixture-only, code-fence-only, and shallow keyword evidence emits only closed-enum hints in `speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh`

### Validation for User Story 3

- [ ] T032 [US3] Run contextual router and compatibility tests with `bash tests/speckit-pro/layer4-scripts/test-atomicity-route.sh`, `bash tests/speckit-pro/layer4-scripts/test-plan-layers.sh`, and `bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh`

**Checkpoint**: PRSG-010B is independently testable when high-confidence context uses documented signal vocabulary, weak evidence leaves the conservative route unchanged, and PRSG-007/008/009 compatibility remains intact.

---

## Phase 5: User Story 2 - Model Genuine Monster Epics Without Nested Specs (Priority: P2, Slice PRSG-010C)

**Goal**: Add an O5 parent manifest and deterministic status/scaffold support for flat sibling child specs without changing the existing flat `specs/*` scan model.

**Independent Test**: Run O5 topology fixtures and confirm valid parents roll up deterministically, invalid topology blocks rollup, and generated MOC zones remain owned by `generate-spec-index.sh`.

### Tests for User Story 2

- [ ] T033 [P] [US2] Add the valid flat-parent O5 fixture for FR-011 through FR-015 in `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/valid-parent/o5-parent-manifest.json`
- [ ] T034 [P] [US2] Add invalid topology fixtures for missing child, duplicate child, nested child path, unknown dependency, later dependency, and cycle cases in `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/invalid-topology/o5-parent-manifest.json`
- [ ] T035 [P] [US2] Add mixed child state rollup fixture for blocked, failed, in-progress, pending, complete, archived, and missing-state rows in `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/mixed-child-states/o5-parent-manifest.json`
- [ ] T036 [US2] Write failing O5 topology and rollup assertions for FR-010 through FR-016 and SC-005 in `tests/speckit-pro/layer4-scripts/test-o5-topology.sh`
- [ ] T037 [P] [US2] Extend flat-spec scan regression coverage so ordinary `specs/*/SPEC-MOC.md` output stays stable in `tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh`

### Implementation for User Story 2

- [ ] T038 [P] [US2] Add the production O5 parent manifest schema for FR-011 through FR-014 in `speckit-pro/skills/speckit-autopilot/contracts/o5-parent-manifest.schema.json`
- [ ] T039 [US2] Implement O5 parent/child topology validation and deterministic rollup in `speckit-pro/skills/speckit-autopilot/scripts/o5-topology.sh`
- [ ] T040 [US2] Update Claude scaffold guidance so normal PRSG-007/008/009 split-PR remains default and O5 is fallback only in `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`
- [ ] T041 [US2] Mirror scaffold O5 fallback guidance in `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`
- [ ] T042 [US2] Update Claude status guidance for topology-first O5 rollup and final-gate re-slicing status in `speckit-pro/skills/speckit-status/SKILL.md`
- [ ] T043 [US2] Mirror status guidance for topology-first O5 rollup and final-gate re-slicing status in `speckit-pro/codex-skills/speckit-status/SKILL.md`

### Validation for User Story 2

- [ ] T044 [US2] Run O5 topology tests with `bash tests/speckit-pro/layer4-scripts/test-o5-topology.sh`
- [ ] T045 [US2] Run flat spec index regression tests with `bash tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh`

**Checkpoint**: PRSG-010C is independently testable when O5 uses flat sibling specs, invalid topology is actionable, status emits one row per declared child, and ordinary flat spec indexing remains compatible.

---

## Phase 6: Polish & Cross-Cutting Concerns (Slice PRSG-010D)

**Purpose**: Remove generated exception boilerplate, complete docs/template parity, prove Claude/Codex mirror consistency, and run final verification.

- [ ] T046 [P] Add PRSG-010 Layer 8 parity fixture overview for backstop, O5, routing, and generated-exception education in `tests/speckit-pro/layer8-parity/03-prsg-010-backstop-o5-routing/README.md`
- [ ] T047 [P] Add PRSG-010 Layer 8 parity workflow fixture for Claude/Codex mirror checks in `tests/speckit-pro/layer8-parity/03-prsg-010-backstop-o5-routing/workflow.md`
- [ ] T048 Update roadmap guidance for final backstop, O5 fallback, contextual router probes, and accepted exception provenance in `docs/ai/specs/pr-size-governance-technical-roadmap.md`
- [ ] T049 Remove live copy-pasteable exception pragma examples while preserving accepted classes and provenance education in `.specify/presets/speckit-pro-reviewability/templates/spec-template.md` and `.specify/templates/spec-template.md`
- [ ] T050 Update structural assertions for new scripts, contracts, executable bits, and generated-exception safety checks in `tests/speckit-pro/layer1-structural/validate-scripts.sh`
- [ ] T051 Run Layer 8 parity checks for changed Claude/Codex surfaces with `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh`
- [ ] T052 Run Layer 1 structural checks with `bash tests/speckit-pro/run-all.sh --layer 1`
- [ ] T053 Run Layer 4 script tests with `bash tests/speckit-pro/run-all.sh --layer 4`
- [ ] T054 Run default deterministic verification with `bash tests/speckit-pro/run-all.sh`
- [ ] T055 Run generated spec index drift check with `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
- [ ] T056 Run whitespace and patch hygiene validation with `git diff --check`
- [ ] T057 Confirm the PR review packet source includes what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback notes in `specs/prsg-010-harden-the-hatch/plan.md` and `specs/prsg-010-harden-the-hatch/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup and blocks all implementation slices.
- **PRSG-010A / US1 (Phase 3)**: First implementation slice and MVP. Blocks later slices because it establishes the final backstop contract.
- **PRSG-010B / US3 (Phase 4)**: Depends on Foundational and should land after PRSG-010A in the stack to preserve design-concept review order.
- **PRSG-010C / US2 (Phase 5)**: Depends on PRSG-010A for shared status/re-slicing language and should land after PRSG-010B in the stack; O5 tests and fixtures can still be prepared independently after Foundational.
- **PRSG-010D / Polish (Phase 6)**: Depends on all selected implementation slices.

### User Story Dependencies

- **User Story 1 (P1, PRSG-010A)**: MVP scope. No dependency on other user stories after Foundational.
- **User Story 3 (P3, PRSG-010B)**: Depends on Foundational and should be reviewed after PRSG-010A.
- **User Story 2 (P2, PRSG-010C)**: Depends on Foundational and should be reviewed after PRSG-010B.

### Within Each User Story

- Write or update tests first and confirm they fail for the missing behavior.
- Add or promote contract schemas before production script behavior depends on them.
- Implement scripts before updating skill prose that instructs operators to use them.
- Update Claude and Codex mirrors in the same slice when behavior-facing prose changes.
- Run focused Layer 4 tests before broader Layer 1, Layer 8, or default verification.

---

## Parallel Execution Examples

### User Story 1 / PRSG-010A

```bash
Task: "Add failing block-without-exception fixture in tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/block-no-exception/gate-result.json"
Task: "Add failing valid typed exception fixture in tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/valid-refactor-exception/exception.md"
Task: "Add the production final gate state schema in speckit-pro/skills/speckit-autopilot/contracts/final-reviewability-gate-state.schema.json"
Task: "Add the production re-slicing packet schema in speckit-pro/skills/speckit-autopilot/contracts/reslicing-packet.schema.json"
```

### User Story 3 / PRSG-010B

```bash
Task: "Add guarded cutover fixture in tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-guarded-cutover/tasks.md"
Task: "Add release-held cutover fixture in tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-release-held/tasks.md"
Task: "Add weak evidence fixture in tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-weak-evidence/tasks.md"
Task: "Add the production routing decision schema in speckit-pro/skills/speckit-autopilot/contracts/routing-decision.schema.json"
```

### User Story 2 / PRSG-010C

```bash
Task: "Add valid O5 parent fixture in tests/speckit-pro/layer4-scripts/fixtures/o5-topology/valid-parent/o5-parent-manifest.json"
Task: "Add invalid O5 topology fixture in tests/speckit-pro/layer4-scripts/fixtures/o5-topology/invalid-topology/o5-parent-manifest.json"
Task: "Add the production O5 parent manifest schema in speckit-pro/skills/speckit-autopilot/contracts/o5-parent-manifest.schema.json"
Task: "Extend flat-spec scan regression coverage in tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh"
```

---

## Implementation Strategy

### MVP First (PRSG-010A Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 / User Story 1.
3. Stop and validate `bash tests/speckit-pro/layer4-scripts/test-final-reviewability-backstop.sh` and `bash tests/speckit-pro/layer4-scripts/test-reviewability-gate.sh`.
4. Review PRSG-010A independently before continuing the stack.

### Incremental Delivery

1. PRSG-010A: final backstop and re-slicing packet.
2. PRSG-010B: contextual router probes and production routing schema.
3. PRSG-010C: O5 manifest, flat child validation, and status/scaffold guidance.
4. PRSG-010D: docs, generated-exception cleanup, parity, and final verification.

### Final Verification Gate

Before PRSG-010D is considered complete, run:

```bash
jq empty docs/ai/specs/.process/autopilot-state.json specs/prsg-010-harden-the-hatch/contracts/*.json
bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .
bash tests/speckit-pro/run-all.sh --layer 1
bash tests/speckit-pro/run-all.sh --layer 4
bash tests/speckit-pro/run-all.sh
git diff --check
```

---

## Task Count

- Total tasks: 57
- Setup tasks: 4
- Foundational tasks: 2
- User Story 1 / PRSG-010A tasks: 17
- User Story 3 / PRSG-010B tasks: 9
- User Story 2 / PRSG-010C tasks: 13
- Polish / PRSG-010D tasks: 12

## MVP Scope

PRSG-010A / User Story 1 is the MVP. It is complete when an unexcepted final gate block cannot generate a PR body, cannot invoke any `gh pr create` variant, cannot invoke `multi-pr-emission.sh`, and records the state plus re-slicing packet required to resume through PRSG-007/008/009.
