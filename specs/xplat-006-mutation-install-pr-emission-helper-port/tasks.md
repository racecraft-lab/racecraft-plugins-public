# Tasks: XPLAT-006 Mutation, Install, and PR-Emission Helper Port

**Input**: Design documents from `specs/xplat-006-mutation-install-pr-emission-helper-port/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, and domain checklists.

**Tests**: Required. XPLAT-006 must write failing Python standard-library tests or fixture assertions before each promoted helper implementation, and Bash-reference comparison must pass before a helper becomes Python-authoritative.

**Reviewability**: Warning accepted for one workflow with three implementation slices. If implementation exceeds the task/file scope below or a slice cannot produce a reviewable PR packet, stop before coding that slice and record a split point.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches independent files or fixture cases and does not compete for shared mutation primitives, registry entries, manifests, or promotion records.
- **[Story]**: `HARD` for already completed autopilot hardening, `US1` for mutation safety, `US2` for install/doctor, `US3` for PR-emission/reviewability, and `HANDOFF` for final proof.

---

## Phase 1: Completed Hardening Baseline

**Purpose**: Preserve the user-required autopilot hardening that prevents missing phases from recurring. These tasks are already complete in this PR and must stay proven by tests.

- [x] T001 [HARD] Add `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` to validate workflow Markdown and `docs/ai/specs/.process/autopilot-state.json`.
- [x] T002 [HARD] Add `tests/speckit-pro/layer4-scripts/test-autopilot-phase-coverage.py` with passing complete workflow/state fixture and failing fixtures for missing Phase 6.5, missing Post items, collapsed later phases, and malformed state JSON.
- [x] T003 [HARD] Wire Python `.py` Layer 4 script tests into `tests/speckit-pro/run-all.sh` so hardening runs in the standard script suite.
- [x] T004 [HARD] Mirror the validator and phase-coverage instructions into allowed Codex/generated payload surfaces under `speckit-pro/codex-skills/` and `dist/`.
- [x] T005 [HARD] Tighten `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` so scope audit allows only exact phase-coverage hardening source/mirror files and still rejects active cutover surfaces.
- [x] T006 [HARD] Record hardening proof in `docs/ai/specs/.process/XPLAT-006-workflow.md`, `docs/ai/specs/.process/autopilot-state.json`, `spec.md`, `plan.md`, `research.md`, `data-model.md`, and `quickstart.md`.

---

## Phase 2: Foundational Blocking Work

**Purpose**: Establish shared mutation contracts, fixture roots, promotion records, and reviewability controls before any helper-specific port.

- [ ] T007 [HANDOFF] Verify current reviewability scope against `plan.md` declared file operations and record split decision in `specs/xplat-006-mutation-install-pr-emission-helper-port/tasks.md` if the implementation scope expands.
- [ ] T008 [P] [US1] Add mutation request/result fixture cases to `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/fixture-manifest.json`.
- [ ] T009 [P] [US1] Add Bash-reference comparison metadata to `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/bash-reference-manifest.json`.
- [ ] T010 [P] [US1] Add initial helper promotion records to `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/promotion-records.json`.
- [ ] T011 [P] [US2] Add install inventory fixture cases to `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/install-inventory-fixtures.json`.
- [ ] T012 [US1] Add failing mutation-foundation tests in `tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py` for invalid mode, dry-run no-op, dirty worktree, path escape, symlink rejection, write failure, and partial failure.
- [ ] T013 [US1] Extend `speckit-pro/speckit_pro_runner/helpers/registry.py` with mutation-capable helper registration separate from accepted XPLAT-005 read-only modes.
- [ ] T014 [US1] Add `speckit-pro/speckit_pro_runner/helpers/mutation.py` with request/result normalization, operation records, boundary records, approval evidence parsing, and deterministic failure classes.
- [ ] T015 [US1] Add atomic write primitives to `speckit-pro/speckit_pro_runner/helpers/mutation.py` using same-directory temp files, validation, flush/fsync, and `os.replace`.
- [ ] T016 [US1] Add path-boundary and dirty-worktree guards to `speckit-pro/speckit_pro_runner/helpers/mutation.py` using argv-list subprocess calls only.
- [ ] T017 [US1] Add `speckit-pro/speckit_pro_runner/helpers/promotion.py` for fixture ids, Bash-reference ids, normalized fields, promotion state, and rollback/manual remediation notes.
- [ ] T018 [US1] Update `speckit-pro/speckit_pro_runner/__main__.py` to dispatch mutation helper requests while preserving the XPLAT-004 response envelope and diagnostics.
- [ ] T019 [HANDOFF] Update `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` and `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` after runner-owned Python files change.

**Checkpoint**: Mutation primitives, registry dispatch, promotion records, and base fixture harness exist before helper-specific ports begin.

---

## Phase 3: User Story 1 - Safe Mutation Foundation

**Goal**: SpecKit operators can preview and apply mutation-helper behavior safely in fake repos without touching real user-local or GitHub state.

**Independent Test**: `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py --group mutation-foundation` passes with dry-run/apply, no-op, dirty-worktree, invalid input, path-boundary, write-failure, and partial-failure coverage.

- [ ] T020 [P] [US1] Add failing tests for mutation dry-run leaving repo, home, cache, network, and GitHub state unchanged in `test-speckit-pro-mutation-helpers.py`.
- [ ] T021 [P] [US1] Add failing tests for apply-mode atomic generated JSON and Markdown writes in `test-speckit-pro-mutation-helpers.py`.
- [ ] T022 [P] [US1] Add failing tests for Windows-style paths, spaces, relative components, symlink rejection, and external absolute paths in `test-speckit-pro-mutation-helpers.py`.
- [ ] T023 [US1] Implement dry-run planned-operation reporting in `speckit-pro/speckit_pro_runner/helpers/mutation.py`.
- [ ] T024 [US1] Implement apply-mode operation recording, skipped/no-op handling, and rollback/manual remediation notes in `speckit-pro/speckit_pro_runner/helpers/mutation.py`.
- [ ] T025 [US1] Implement deterministic normalization for volatile paths, timestamps, git metadata, platform names, and environment-sensitive fields in `speckit-pro/speckit_pro_runner/helpers/promotion.py`.
- [ ] T026 [US1] Record Slice 1 promotion evidence in `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/promotion-records.json`.
- [ ] T027 [US1] Run the mutation foundation focused test group and record evidence in the PR packet section of `docs/ai/specs/.process/XPLAT-006-workflow.md`.

**Checkpoint**: US1 is independently testable and provides the shared mutation substrate for US2 and US3.

---

## Phase 4: User Story 2 - Manifest-Driven Install Completeness And Doctor

**Goal**: Install maintainers can run deterministic doctor/preflight checks and safe repair fixtures for Claude/Codex installs without touching real homes.

**Independent Test**: `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py --group install-doctor` passes for complete install, stale/missing install state, safe repair, unsafe manual remediation, and blocked states.

- [ ] T028 [P] [US2] Add failing doctor/preflight fixture tests for complete install, missing Codex agent, missing Claude agent, stale plugin cache, downgrade refusal, missing runner file, checksum mismatch, missing generated payload file, malformed inventory, and blocked repair.
- [ ] T029 [P] [US2] Add failing safe-repair fixture tests for fake Claude homes, fake Codex homes, fake plugin caches, orphan plugin-owned file removal, unrelated-file preservation, and real-home refusal.
- [ ] T030 [US2] Add `speckit-pro/speckit_pro_runner/install_inventory.json` with expected Claude agents, Codex agents, runner files, generated payload files, checksums, plugin versions, marketplace versions, runner metadata, and release metadata.
- [ ] T031 [US2] Add `speckit-pro/speckit_pro_runner/helpers/install.py` with read-only doctor/preflight classifications and deterministic remediation text.
- [ ] T032 [US2] Port `install-codex-agents` behavior into `helpers/install.py`, preserving bundled-agent completeness, model fallback, marketplace snapshot sync semantics, and stale install diagnostics.
- [ ] T033 [US2] Port `install-curated-set` check/install/upgrade behavior into `helpers/install.py`, preserving pinned release/tag resolution, provenance logging, and fake `gh`/`specify` fixtures.
- [ ] T034 [US2] Port `project-fixup apply` and `ensure-reviewability-preset` write behavior into mutation-safe install helper operations.
- [ ] T035 [US2] Expose doctor/preflight operation ids through `speckit-pro/speckit_pro_runner/helpers/registry.py` so scaffold/status/autopilot can call the shared contract without active invocation cutover.
- [ ] T036 [US2] Record Slice 2 promotion evidence in `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/promotion-records.json`.
- [ ] T037 [HANDOFF] Update runner manifest/checksum metadata after install helper and inventory changes.
- [ ] T038 [US2] Run the install-doctor focused test group and record evidence in the PR packet section of `docs/ai/specs/.process/XPLAT-006-workflow.md`.

**Checkpoint**: US2 is independently testable with fake install state and no real user-home writes.

---

## Phase 5: User Story 3 - PR-Emission, Restack, Relocation, And Reviewability Proof

**Goal**: Release reviewers can inspect deterministic PR-emission, restack, migration, relocation, and review-packet proof without live GitHub mutation or active cutover.

**Independent Test**: `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py --group pr-emission` passes for PR body, UAT skeleton, final-reviewability, PR packet, workflow contract, split PR, restack, migration, relocation, generated-index write modes, and fake `gh` command capture.

- [ ] T039 [P] [US3] Add failing PR-emission fixture tests for `generate-pr-body`, `generate-uat-skeleton`, `final-reviewability-backstop`, PR-packet output, and workflow-contract output.
- [ ] T040 [P] [US3] Add failing fake `gh` and fake repo fixture tests for `multi-pr-emission`, `restack`, split-PR state, migration, and relocation apply boundaries.
- [ ] T041 [P] [US3] Add failing generated-output fixture tests for generated-index write/regenerate modes, `plan-layers` marker-plan output, `validate-pr-packet` workflow-event persistence, and `validate-pr-workflow-contract` write mode.
- [ ] T042 [US3] Add `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` with atomic generated artifact writes and preserved packet/body content contracts.
- [ ] T043 [US3] Port PR-body, UAT-skeleton, final-reviewability-backstop, PR-packet, and workflow-contract output helpers into `helpers/pr_emission.py`.
- [ ] T044 [US3] Port `multi-pr-emission`, `restack`, split-PR state, migration, and relocation helper behavior using fake repos and fake `gh` by default.
- [ ] T045 [US3] Port generated-index write/regenerate modes, `plan-layers` marker-plan output, `validate-pr-packet` persistence/workflow-event upserts, and `validate-pr-workflow-contract` write mode.
- [ ] T046 [US3] Keep `detect-stack-manager` to decision and command-plan evidence only; verify mutating command execution remains owned by `multi-pr-emission` and `restack` apply paths.
- [ ] T047 [US3] Record Slice 3 promotion evidence in `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/promotion-records.json`.
- [ ] T048 [HANDOFF] Update runner manifest/checksum metadata after PR-emission helper changes.
- [ ] T049 [US3] Run the PR-emission focused test group and record evidence in the PR packet section of `docs/ai/specs/.process/XPLAT-006-workflow.md`.

**Checkpoint**: US3 is independently testable with fake repos and no live GitHub mutation.

---

## Phase 6: Cross-Cutting Verification And Handoff

**Purpose**: Prove all promoted helper behavior, hardening, and scope boundaries before final implementation acceptance.

- [ ] T050 [HANDOFF] Run `python3 tests/speckit-pro/layer4-scripts/test-autopilot-phase-coverage.py` and record 6/6 hardening result.
- [ ] T051 [HANDOFF] Run `python3 speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py --workflow docs/ai/specs/.process/XPLAT-006-workflow.md --state docs/ai/specs/.process/autopilot-state.json` and record `status=pass`.
- [ ] T052 [HANDOFF] Run `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` and record the scope-audit test result.
- [ ] T053 [HANDOFF] Run `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py` and record promoted helper coverage.
- [ ] T054 [HANDOFF] Run Bash-reference comparison fixtures from `bash-reference-manifest.json` and record comparison ids for every Bash-backed promoted helper.
- [ ] T055 [HANDOFF] Run `bash tests/speckit-pro/run-all.sh --layer 4` and record Layer 4 totals.
- [ ] T056 [HANDOFF] Run `bash tests/speckit-pro/run-all.sh --layer 1` and record Layer 1 totals.
- [ ] T057 [HANDOFF] Run `bash tests/speckit-pro/run-all.sh` and record default deterministic suite totals.
- [ ] T058 [HANDOFF] Run `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check $PWD` and `bash tests/speckit-pro/layer1-structural/validate-moc-stale-index.sh specs`.
- [ ] T059 [HANDOFF] Run `git diff --name-only origin/main...HEAD` and scope-audit the diff for forbidden active cutover surfaces, listing the allowed hardening source/mirror separately.
- [ ] T060 [HANDOFF] Update `docs/ai/specs/.process/XPLAT-006-workflow.md` with verification evidence, known gaps, approval boundaries, rollback/manual remediation notes, and XPLAT-007/XPLAT-008 handoff.
- [ ] T061 [HANDOFF] Ensure the PR packet states that active Claude/Codex invocation cutover, generated-payload selection/cutover, repo-local release-gate migration, native matrix UAT, and public native-platform support claims are not delivered by XPLAT-006.

---

## Dependencies And Execution Order

- T001-T006 are complete and prove the autopilot hardening baseline.
- T007-T019 are blocking foundation tasks. Do not start helper-specific implementation before T012-T019 pass.
- US1 tasks T020-T027 must complete before US2 or US3 apply-mode helper behavior can rely on shared mutation primitives.
- US2 tasks T028-T038 depend on T007-T019 and may run after US1 mutation primitives are stable.
- US3 tasks T039-T049 depend on T007-T019 and may run after US1 mutation primitives are stable.
- Cross-cutting verification T050-T061 depends on all promoted helper tasks and promotion records.

## Parallel Opportunities

- T008-T011 can run in parallel because they seed independent fixture files.
- T020-T022 can run in parallel because they add independent US1 failing test groups.
- T028-T029 can run in parallel because they add independent US2 fixture groups.
- T039-T041 can run in parallel because they add independent US3 fixture groups.
- US2 and US3 implementation can run in parallel only after T007-T019 and the US1 shared mutation primitives are accepted, and only if separate owners avoid shared registry, manifest, and promotion-record edits.
- T049-T051 can run in parallel with PR packet drafting after all implementation tasks are complete.

## Reviewability Checkpoints

- Checkpoint A after T019: shared mutation foundation is reviewable and no helper-specific port has hidden scope expansion.
- Checkpoint B after T037: install/doctor slice has fake-home proof and no real user-home writes.
- Checkpoint C after T048: PR-emission/restack/relocation slice has fake GitHub proof and no live mutation.
- Checkpoint D before T060: PR packet maps every promoted helper to changed files, fixtures, Bash-reference evidence, promotion state, known gaps, and rollback/manual remediation notes.
