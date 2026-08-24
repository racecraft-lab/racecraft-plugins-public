# Tasks: Capability-aware Resolver, Materializer, Installer, and Strict Override

**Input**: Design documents from `specs/g56r-006-resolver-materializer-installer-strict-override/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, and `docs/ai/specs/.process/G56R-006-design-concept.md`

**Tests**: Required. Every behavior-changing implementation task below is paired with a focused RED test task and names its RED->GREEN pair.

**Reviewability**: Preserve the plan budget: one vertical framework slice, approximately 4 production files and 8 authored implementation files. Generated payloads, installed-cache mirrors, proof fixtures, docs references, and PR evidence are follow-through outputs, not additional design surfaces.

**Non-goals carried into implementation**: no production route qualification, no live model calls, no real-user-home writes, no Claude install path behavior, no per-agent override map, no arbitrary effort map, no route-policy cohort expansion, no downstream G56R-007 through G56R-011 cohort assignment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel only when files and state do not overlap
- **[Story]**: User story label for story phases only
- Every task names an exact repository path

## Phase 1: Setup (Shared Orientation)

**Purpose**: Confirm scope, source-of-truth files, and the deterministic fake-home acceptance boundary before edits.

- [X] T001 [P] Reconfirm the G56R-006 requirements, non-goals, Q&A decisions, and downstream roster-reconciliation note in `specs/g56r-006-resolver-materializer-installer-strict-override/spec.md`
- [X] T002 [P] Reconfirm implementation surfaces, generated-artifact follow-through, and reviewability budget in `specs/g56r-006-resolver-materializer-installer-strict-override/plan.md`
- [X] T003 [P] Reconfirm manifest and route-aware response contracts in `specs/g56r-006-resolver-materializer-installer-strict-override/contracts/route-policy-manifest.schema.md` and `specs/g56r-006-resolver-materializer-installer-strict-override/contracts/install-codex-agents-route-aware.md`
- [X] T004 [P] Reconfirm deterministic-only validation commands and fake-home constraints in `specs/g56r-006-resolver-materializer-installer-strict-override/quickstart.md`
- [X] T005 Verify the current static installer baseline and strict bundled source inventory by running `python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` against `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the shared closed manifest fixture corpus and validation scaffolding that every user-story slice depends on.

**CRITICAL**: No user story implementation begins until this phase is complete.

- [X] T006 Add the shared deterministic route-policy fixture corpus for valid, invalid, strict-override, helper, probe, filesystem-failure, and rollback cases in `tests/speckit-pro/unit/fixtures/mutation-helpers/codex-agent-routing/cases.json`
- [X] T007 RED for T008: add failing strict 13-source inventory, closed manifest schema, supported-version, trusted-path, source-roster digest, and exact 12-required-plus-one-optional roster validation tests in `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` (FR-001, FR-003, FR-004, FR-005, FR-006)
- [X] T008 GREEN for T007: implement manifest loading, trusted safe-file validation, source-roster digest binding, closed schema rejection, required roster constants, and optional-helper metadata in `speckit-pro/speckit_pro_runner/helpers/install.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [X] T009 RED for T010: add failing shared fake-home, capability adapter injection, manifest writer, routing-response assertion, and no-real-home guard tests in `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` (FR-008, FR-028)
- [X] T010 GREEN for T009: add the injectable observation adapter boundary and test-only injection plumbing through existing runner-owned helpers in `speckit-pro/speckit_pro_runner/helpers/install.py`
- [X] T011 Run focused foundation validation with `python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` for `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`

**Checkpoint**: Foundation ready. User-story work can proceed, but shared installer, materializer, registry, fixture, suite manifest, generated payload, runner metadata, and docs-reference changes stay serialized.

---

## Phase 3: User Story 1 - Route-aware Batch Installation Plan (Priority: P1) MVP

**Goal**: Route-aware dry-run and apply resolve every required Codex agent from one fresh capability snapshot and trusted manifest, materialize byte-proven destination TOMLs, and preserve static no-manifest compatibility.

**Independent Test**: Run deterministic dry-run and apply cases with a fake Codex agents home and verify complete 12-required routing evidence, materialization proofs, zero source TOML mutations, and unchanged static 13-file behavior.

### RED->GREEN Tasks for User Story 1

- [X] T012 [US1] RED for T013: add failing materializer tests for explicit model/effort rendering, original source byte digest binding, destination byte digest proof, and unchanged non-route fields in `tests/speckit-pro/unit/test-agent-materialization.py` (FR-011, FR-012, FR-013, FR-014; US1-S1)
- [X] T013 [US1] GREEN for T012: extend canonical materialization to render selected explicit model and effort while proving source-byte binding and non-route field immutability in `speckit-pro/speckit_pro_runner/agent_materialization.py`
- [X] T014 [US1] RED for T015: add failing route-aware dry-run success and static no-manifest compatibility tests in `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` (FR-002, FR-007, FR-010, FR-015, FR-016, FR-017; US1-S1, US1-S3)
- [X] T015 [US1] GREEN for T014: implement route-aware activation, one fresh runtime snapshot, normal preferred-then-fallback required-agent resolution, complete top-level `routing` evidence, and static response omission of `routing` in `speckit-pro/speckit_pro_runner/helpers/install.py`
- [X] T016 [US1] RED for T017: add failing route-aware apply success tests for missing and stale required destination TOMLs in a fake home in `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` (FR-017; US1-S2)
- [X] T017 [US1] GREEN for T016: implement complete-plan-before-write dry-run/apply planning, required destination byte verification, and no bundled-source mutation checks in `speckit-pro/speckit_pro_runner/helpers/install.py`
- [X] T018 [US1] Run the US1 focused RED->GREEN validation with `python3 tests/speckit-pro/unit/test-agent-materialization.py` and `python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` for `tests/speckit-pro/unit/test-agent-materialization.py` and `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`

**Checkpoint**: US1 independently proves acceptance scenarios 1.1, 1.2, and 1.3.

---

## Phase 4: User Story 2 - Strict Global Override Validation (Priority: P1)

**Goal**: Strict global override validates the complete required roster before mutation, never falls back after required override misses, and applies to the optional helper only when compatible.

**Independent Test**: Run deterministic strict-override manifest cases for compatible required routes, incompatible required routes, compatible helper tuple, incompatible helper tuple, and invalid no-helper continuation.

### RED->GREEN Tasks for User Story 2

- [X] T019 [US2] RED for T020: add failing strict required-override tests that verify exactly one override-derived tuple per required agent, complete diagnostics for all 12 required agents, suppressed fallback, zero writes on required miss, `writes_state=false`, and `restart_required=false` in `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` (FR-019, FR-020; US2-S1, US2-S2)
- [X] T020 [US2] GREEN for T019: implement strict global override required-agent resolution, evaluated tuple evidence, fallback suppression, and pre-mutation required-miss failure handling in `speckit-pro/speckit_pro_runner/helpers/install.py`
- [X] T021 [US2] RED for T022: add failing optional-helper strict-override tests for compatible helper install, incompatible helper validated no-helper continuation, and incompatible helper unresolved pre-mutation failure in `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` (FR-021, FR-022, FR-023; US2-S3, US2-S4)
- [X] T022 [US2] GREEN for T021: implement optional-helper strict-override compatibility handling, no-helper validation, unresolved helper failure, and `strict_override` helper evidence in `speckit-pro/speckit_pro_runner/helpers/install.py`
- [X] T023 [US2] Run the US2 focused RED->GREEN validation with `python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` for `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`

**Checkpoint**: US2 independently proves acceptance scenarios 2.1, 2.2, 2.3, and 2.4.

---

## Phase 5: User Story 3 - Optional Helper Omitted or Removed Safely (Priority: P2)

**Goal**: An unavailable optional helper is omitted or removed only with plugin ownership proof, while same-named user-modified files are preserved with manual-remediation evidence.

**Independent Test**: Run fake-home cases with no helper file, trusted runner provenance, exact known rendered-byte match, parsed-equivalent-only helper, and user-modified same-name helper.

### RED->GREEN Tasks for User Story 3

- [X] T024 [US3] RED for T025: add failing helper-unavailable tests for no helper present, helper omitted with validated no-helper continuation, and required roster success in `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` (FR-023; US3-S1)
- [X] T025 [US3] GREEN for T024: implement optional-helper omitted state and validated no-helper continuation in `speckit-pro/speckit_pro_runner/helpers/install.py`
- [X] T026 [US3] RED for T027: add failing managed-helper removal tests for trusted runner-owned install provenance and exact known rendered-byte digest match in `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` (FR-024; US3-S2)
- [X] T027 [US3] GREEN for T026: implement managed-helper ownership proof using trusted runner provenance and exact known rendered-byte digest matching in `speckit-pro/speckit_pro_runner/helpers/install.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [X] T028 [US3] RED for T029: add failing helper preservation tests for filename-only, syntactic TOML, parsed-equivalent, normalized-content, and user-modified same-name helpers with manual-remediation evidence in `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` (FR-025; US3-S3)
- [X] T029 [US3] GREEN for T028: implement helper preservation and bounded manual-remediation evidence when managed ownership proof is absent in `speckit-pro/speckit_pro_runner/helpers/install.py`
- [X] T030 [US3] Run the US3 focused RED->GREEN validation with `python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` for `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`

**Checkpoint**: US3 independently proves acceptance scenarios 3.1, 3.2, and 3.3.

---

## Phase 6: User Story 4 - Complete Failure Evidence with Preservation (Priority: P2)

**Goal**: Route-aware failures return complete structured diagnostics, preserve the previous known-good installation when possible, and report restart/manual remediation only when state is changed or uncertain.

**Independent Test**: Run deterministic injected route misses, discovery/probe failures, unsafe destination entries, write failures, verification failures, rollback success, and rollback failure cases in fake homes.

### RED->GREEN Tasks for User Story 4

- [X] T031 [US4] RED for T032: add failing required-route-miss tests that keep resolving all 12 required agents in stable canonical order, return all attempts and rejection reasons, report zero planned/applied writes and removals, set `writes_state=false`, set `restart_required=false`, and preserve previous known-good fake-home state in `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` (FR-010, FR-018, FR-027; US4-S1)
- [X] T032 [US4] GREEN for T031: implement required-route-miss zero-write diagnostics, stable canonical roster ordering, complete attempt evidence, and no-mutation recovery evidence in `speckit-pro/speckit_pro_runner/helpers/install.py`
- [X] T033 [US4] RED for T034: add failing bounded discovery/probe failure tests for native discovery unavailable, manifest-admitted probe success/failure, insufficient probe result, no candidate widening, and one snapshot child-probe evidence in `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` (FR-007, FR-008, FR-009; US4-S1)
- [X] T034 [US4] GREEN for T033: implement bounded native-discovery fallback probing as child evidence of the one runtime capability snapshot without widening manifest-admitted candidates in `speckit-pro/speckit_pro_runner/helpers/install.py`
- [X] T035 [US4] RED for T036: add failing apply-failure rollback-success tests that capture prior bytes and file modes, record staged/applied/rolled-back/cleanup actions, prove pre/final state identities, set `rollback_outcome=restored`, `writes_state=false`, and `restart_required=false`, and avoid verification success in `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` (FR-026, FR-027; US4-S2)
- [X] T036 [US4] GREEN for T035: implement one rollback-backed apply batch with prior bytes/modes capture, restored-state verification, cleanup action evidence, and failed-apply verification suppression in `speckit-pro/speckit_pro_runner/helpers/install.py`
- [X] T037 [US4] RED for T038: add failing rollback-failure tests that report every unrestored action and error, mark `writes_state` true or uncertain, set `restart_required=true`, include bounded manual remediation, and avoid verification success in `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` (FR-026, FR-027; US4-S3)
- [X] T038 [US4] GREEN for T037: implement rollback-failure recovery evidence, restart guidance, failed/cleanup/manual-remediation records, and uncertain state reporting in `speckit-pro/speckit_pro_runner/helpers/install.py`
- [X] T039 [US4] Run the US4 focused RED->GREEN validation with `python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` for `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`

**Checkpoint**: US4 independently proves acceptance scenarios 4.1, 4.2, and 4.3.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Refresh generated artifacts, docs, metadata, and release evidence after all independently testable story slices pass.

- [X] T040 Update the Codex install skill documentation for explicit route-policy manifest activation, static no-manifest compatibility, deterministic-only G56R-006 evidence, and no real-home writes in `speckit-pro/codex-skills/install/SKILL.md`
- [X] T041 Regenerate payload mirrors and runner trust metadata with `python3 scripts/refresh-release-artifacts.py`, updating `dist/codex/speckit-pro/`, `dist/claude/speckit-pro/`, and `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- [X] T042 Regenerate installed-cache fixture mirrors and proof evidence through the payload refresh, updating `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/` and `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof*.json`
- [X] T043 Run focused materializer tests with `python3 tests/speckit-pro/unit/test-agent-materialization.py` for `tests/speckit-pro/unit/test-agent-materialization.py`
- [X] T044 Run focused installer tests with `python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` for `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`
- [X] T045 Run Layer 4 runtime and script-safety validation with `python3 tests/speckit-pro/run-all.py --layer 4` for `tests/speckit-pro/suite-manifest.json`
- [X] T046 Run Layer 5 tool-scoping validation with `python3 tests/speckit-pro/run-all.py --layer 5` for `tests/speckit-pro/suite-manifest.json`
- [X] T047 Run Layer 1 structural validation after generated payload refresh with `python3 tests/speckit-pro/run-all.py --layer 1` for `tests/speckit-pro/suite-manifest.json`
- [X] T048 Install docs-site dependencies if needed with `pnpm --dir docs-site install --frozen-lockfile` for `docs-site/pnpm-lock.yaml`
- [X] T049 Regenerate docs reference output with `pnpm --dir docs-site reference:generate`, updating `docs-site/src/content/docs/reference/tests.md`
- [X] T050 Check docs reference output with `pnpm --dir docs-site reference:check` for `docs-site/src/content/docs/reference/tests.md`
- [X] T051 Run the full Python-authoritative suite with `python3 tests/speckit-pro/run-all.py` for `tests/speckit-pro/suite-manifest.json`
- [X] T052 Record release-readiness evidence and PR review packet inputs covering what changed, why, non-goals, review order, scope budget, traceability, verification, known gaps, and rollback or feature-flag notes in `docs/ai/specs/.process/G56R-006-release-readiness-result.json`
- [X] T053 Verify the final implementation references the downstream roster reconciliation inputs without assigning cohorts by checking `specs/g56r-006-resolver-materializer-installer-strict-override/spec.md` and `docs/ai/specs/.process/G56R-006-design-concept.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup and blocks all story phases.
- **US1 (Phase 3)**: depends on Foundational; delivers the MVP route-aware batch and static compatibility.
- **US2 (Phase 4)**: depends on Foundational and the US1 resolver/evidence surface.
- **US3 (Phase 5)**: depends on Foundational and the US1 optional-helper decision surface.
- **US4 (Phase 6)**: depends on Foundational and the US1 apply/recovery surface; it can begin once US1 exposes the route-aware apply boundary.
- **Polish (Phase 7)**: depends on all desired story phases.

### User Story Dependencies

- **User Story 1 (P1)**: MVP. No dependency on other stories after Foundation.
- **User Story 2 (P1)**: can be tested independently with strict-override fixtures after Foundation, but implementation depends on US1 route resolution and evidence structures.
- **User Story 3 (P2)**: can be tested independently with helper fake-home fixtures after Foundation, but implementation depends on US1 helper decision structure.
- **User Story 4 (P2)**: can be tested independently with failure fake-home fixtures after Foundation, but implementation depends on US1 apply/recovery boundary.

### RED->GREEN Pairing

- T007 -> T008: manifest trust, source roster, and closed 12+1 validation.
- T009 -> T010: injectable observation adapter and fake-home guard.
- T012 -> T013: materialization proof.
- T014 -> T015: route-aware dry-run and static compatibility response.
- T016 -> T017: complete plan before apply.
- T019 -> T020: strict required override.
- T021 -> T022: helper strict override and no-helper validation.
- T024 -> T025: helper omitted state.
- T026 -> T027: managed helper removal.
- T028 -> T029: helper preservation.
- T031 -> T032: required miss zero-write diagnostics.
- T033 -> T034: bounded discovery/probe evidence.
- T035 -> T036: rollback success preservation.
- T037 -> T038: rollback failure evidence.

### Parallel Opportunities

- T001, T002, T003, and T004 can run in parallel because they only read separate planning artifacts.
- After T006 creates the shared fixture corpus and T009/T010 establish test helpers, T012 can be prepared while T014 and T016 are drafted, but the GREEN implementation tasks T013, T015, and T017 must be serialized because they touch shared materializer and installer state.
- US2, US3, and US4 RED tests can be drafted by separate workers after Foundation when they coordinate on `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`; actual edits to that shared file must be serialized.
- T043 and T044 can be run independently after implementation, but T045 through T051 must run in the listed order because generated artifacts and docs references share repository state.

---

## Traceability

### Functional Requirements

- **FR-001**: T006, T007, T008, T014, T015
- **FR-002**: T005, T014, T015, T018
- **FR-003**: T005, T007, T008
- **FR-004**: T006, T007, T008, T014, T015, T031, T032
- **FR-005**: T006, T007, T008, T024, T025
- **FR-006**: T007, T008, T024, T025
- **FR-007**: T009, T010, T014, T015, T033, T034
- **FR-008**: T009, T010, T033, T034
- **FR-009**: T033, T034
- **FR-010**: T014, T015, T031, T032
- **FR-011**: T012, T013, T014, T015
- **FR-012**: T012, T013, T019, T020
- **FR-013**: T012, T013
- **FR-014**: T012, T013
- **FR-015**: T014, T015, T019, T020, T021, T022, T024, T025, T026, T027, T028, T029, T031, T032, T035, T036, T037, T038
- **FR-016**: T014, T015, T035, T036
- **FR-017**: T016, T017, T035, T036
- **FR-018**: T019, T020, T031, T032
- **FR-019**: T019, T020
- **FR-020**: T019, T020
- **FR-021**: T021, T022
- **FR-022**: T021, T022
- **FR-023**: T021, T022, T024, T025
- **FR-024**: T026, T027
- **FR-025**: T028, T029
- **FR-026**: T035, T036, T037, T038
- **FR-027**: T031, T032, T035, T036, T037, T038
- **FR-028**: T006, T009, T010, T018, T023, T030, T039
- **FR-029**: T001, T052, T053

### Acceptance Scenarios

- **US1-S1**: T012, T013, T014, T015, T018
- **US1-S2**: T016, T017, T018
- **US1-S3**: T005, T014, T015, T018
- **US2-S1**: T019, T020, T023
- **US2-S2**: T019, T020, T023
- **US2-S3**: T021, T022, T023
- **US2-S4**: T021, T022, T023
- **US3-S1**: T024, T025, T030
- **US3-S2**: T026, T027, T030
- **US3-S3**: T028, T029, T030
- **US4-S1**: T031, T032, T033, T034, T039
- **US4-S2**: T035, T036, T039
- **US4-S3**: T037, T038, T039

### Success Criteria

- **SC-001**: T014, T015, T018
- **SC-002**: T016, T017, T018
- **SC-003**: T005, T014, T015, T018
- **SC-004**: T019, T020, T023
- **SC-005**: T024, T025, T026, T027, T028, T029, T030
- **SC-006**: T031, T032, T039
- **SC-007**: T035, T036, T039
- **SC-008**: T037, T038, T039
- **SC-009**: T006, T009, T010, T018, T023, T030, T039, T051

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete US1 tests and implementation: T012 through T018.
3. Stop and validate US1 independently with focused materializer and installer tests.
4. Keep static no-manifest compatibility as the fallback path.

### Incremental Delivery

1. Foundation: manifest trust, source roster, fixture corpus, and adapter injection.
2. US1: normal route-aware dry-run/apply and static compatibility.
3. US2: strict override semantics.
4. US3: optional-helper omitted/removed/preserved states.
5. US4: failure evidence, rollback, and restart guidance.
6. Polish: generated artifacts, docs, Layer 1/4/5 gates, full suite, and PR evidence.

### Parallel Team Strategy

Multiple workers may read Setup artifacts in parallel. After Foundation, workers may draft story-specific RED tests in coordination, but edits to `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` must be merged serially. All GREEN tasks touching `speckit-pro/speckit_pro_runner/helpers/install.py`, `speckit-pro/speckit_pro_runner/agent_materialization.py`, `speckit-pro/speckit_pro_runner/helpers/registry.py`, generated payloads, runner metadata, docs reference output, and suite manifest state must remain serialized.

### Review Packet Notes

The PR packet should lead reviewers through contracts/data model, materializer, installer route planning, strict override, helper ownership, rollback/recovery, tests/fixtures, generated payloads, and docs. It must state the route-aware feature flag/rollback posture: route-aware mode requires an explicit trusted manifest, and static no-manifest mode remains compatible.
