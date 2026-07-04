# Tasks: XPLAT-006 Mutation, Install, and PR-Emission Helper Port

**Input**: Design documents from `specs/xplat-006-mutation-install-pr-emission-helper-port/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, and domain checklists.

**Tests**: Required. XPLAT-006 must write failing Python standard-library tests or fixture assertions before each promoted helper implementation, and Bash-reference comparison must pass before a helper becomes Python-authoritative.

**Reviewability**: Warning accepted for one workflow with three implementation slices. If implementation exceeds the task/file scope below or a slice cannot produce a reviewable PR packet, stop before coding that slice and record a split point.

Reviewability-Exception: infra

**Completion Note**: XPLAT-006 does not make any Bash-backed mutation helper Python-authoritative. The PR lands runner-side mutation primitives, doctor/preflight fake-home proof, PR-body and command-plan golden fixtures, registry-visible deferred entries for the remaining mutation helpers, and hardening tests that run in Layer 4. Bash parity and active Claude/Codex cutover remain XPLAT-007/XPLAT-008 work.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches independent files or fixture cases and does not compete for shared mutation primitives, registry entries, manifests, or promotion records.
- **[Story]**: `HARD` for already completed autopilot hardening, `US1` for mutation safety, `US2` for install/doctor, `US3` for PR-emission/reviewability, and `HANDOFF` for final proof.

---

## Phase 1: Completed Hardening Baseline

**Purpose**: Preserve the user-required autopilot hardening that prevents missing phases from recurring. These tasks are already complete in this PR and must stay proven by tests.

- [x] T001 [HARD] Add `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` to validate workflow Markdown and `docs/ai/specs/.process/autopilot-state.json`.
- [x] T002 [HARD] Add `tests/speckit-pro/layer4-scripts/test-autopilot-phase-coverage.py` with passing complete workflow/state fixture and failing fixtures for missing Phase 6.5, missing Post items, collapsed or semantically mislabeled later phases, and malformed state JSON.
- [x] T003 [HARD] Wire Python `.py` Layer 4 script tests into `tests/speckit-pro/run-all.sh` so hardening runs in the standard script suite.
- [x] T004 [HARD] Mirror the validator and phase-coverage instructions into allowed Codex/generated payload surfaces under `speckit-pro/codex-skills/` and `dist/`.
- [x] T005 [HARD] Tighten `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` so scope audit allows only exact phase-coverage hardening source/mirror files and still rejects active cutover surfaces.
- [x] T006 [HARD] Record hardening proof in `docs/ai/specs/.process/XPLAT-006-workflow.md`, `docs/ai/specs/.process/autopilot-state.json`, `spec.md`, `plan.md`, `research.md`, `data-model.md`, and `quickstart.md`.

---

## Phase 2: Foundational Blocking Work

**Purpose**: Establish shared mutation contracts, fixture roots, promotion records, and reviewability controls before any helper-specific port.

- [x] T007 [HANDOFF] Verify current reviewability scope against `plan.md` declared file operations and record split decision in `specs/xplat-006-mutation-install-pr-emission-helper-port/tasks.md` if the implementation scope expands.
- [x] T008 [P] [US1] Add mutation request/result fixture cases to `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/fixture-manifest.json`.
- [x] T009 [P] [US1] Add Bash-reference comparison metadata to `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/bash-reference-manifest.json`.
- [x] T010 [P] [US1] Add initial helper promotion records to `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/promotion-records.json`.
- [x] T011 [P] [US2] Add install inventory fixture cases to `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/install-inventory-fixtures.json`.
- [x] T012 [US1] Add failing mutation-foundation tests in `tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py` for dry-run no-op, apply writes, dirty worktree, path escape, symlink rejection, write failure, and partial failure.
- [x] T013 [US1] Extend `speckit-pro/speckit_pro_runner/helpers/registry.py` with mutation-capable helper registration separate from accepted XPLAT-005 read-only modes.
- [x] T014 [US1] Add `speckit-pro/speckit_pro_runner/helpers/mutation.py` with request/result normalization, operation records, repository boundary checks, fail-closed dirty-worktree guards, and deterministic failure classes.
- [x] T015 [US1] Add atomic write primitives to `speckit-pro/speckit_pro_runner/helpers/mutation.py` using same-directory temp files, validation, flush/fsync, and `os.replace`.
- [x] T016 [US1] Add path-boundary and dirty-worktree guards to `speckit-pro/speckit_pro_runner/helpers/mutation.py` using argv-list subprocess calls only.
- [x] T017 [US1] Add `speckit-pro/speckit_pro_runner/helpers/promotion.py` for fixture ids, Bash-reference ids, normalized fields, promotion state, and rollback/manual remediation notes.
- [x] T018 [US1] Update `speckit-pro/speckit_pro_runner/__main__.py` to dispatch mutation helper requests while preserving the XPLAT-004 response envelope and diagnostics.
- [x] T019 [HANDOFF] Update `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` and `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` after runner-owned Python files change.

**Checkpoint**: Mutation primitives, registry dispatch, promotion records, and base fixture harness exist before helper-specific ports begin.

---

## Phase 3: User Story 1 - Safe Mutation Foundation

**Goal**: SpecKit operators can preview and apply mutation-helper behavior safely in fake repos without touching real user-local or GitHub state.

**Independent Test**: `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py` passes with dry-run/apply, no-op, dirty-worktree, path-boundary, symlink, write-failure, and partial-failure coverage.

- [x] T020 [P] [US1] Add failing tests for mutation dry-run leaving target files unchanged and PR command planning reporting `live_mutation=false` in `test-speckit-pro-mutation-helpers.py`.
- [x] T021 [P] [US1] Add failing tests for apply-mode atomic generated JSON and Markdown writes in `test-speckit-pro-mutation-helpers.py`.
- [x] T022 [P] [US1] Add failing tests for path-boundary and symlink rejection in `test-speckit-pro-mutation-helpers.py`; Windows-style and external absolute handling are enforced by the shared path guard.
- [x] T023 [US1] Implement dry-run planned-operation reporting in `speckit-pro/speckit_pro_runner/helpers/mutation.py`.
- [x] T024 [US1] Implement apply-mode operation recording, skipped/no-op handling, and rollback/manual remediation notes in `speckit-pro/speckit_pro_runner/helpers/mutation.py`.
- [x] T025 [US1] Implement deterministic promotion-record normalization for fixture ids, Bash-reference ids, promotion state, and rollback text in `speckit-pro/speckit_pro_runner/helpers/promotion.py`.
- [x] T026 [US1] Record Slice 1 promotion evidence in `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/promotion-records.json`.
- [x] T027 [US1] Run the mutation foundation focused test group and record evidence in the PR packet section of `docs/ai/specs/.process/XPLAT-006-workflow.md`.

**Checkpoint**: US1 is independently testable and provides the shared mutation substrate for US2 and US3.

---

## Phase 4: User Story 2 - Manifest-Driven Install Completeness And Doctor

**Goal**: Install maintainers can run deterministic doctor/preflight checks and safe repair fixtures for Claude/Codex installs without touching real homes.

**Independent Test**: `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py` passes for missing install state, safe repair, and real-home refusal using fake-home fixtures.

- [x] T028 [P] [US2] Add failing doctor/preflight fixture tests for missing expected files and safe-repair classification.
- [x] T029 [P] [US2] Add failing safe-repair fixture tests for fake-home repair and real-home refusal.
- [x] T030 [US2] Add `speckit-pro/speckit_pro_runner/install_inventory.json` with expected Claude agents, Codex agents, runner files, generated payload files, checksums, plugin versions, marketplace versions, runner metadata, and release metadata.
- [x] T031 [US2] Add `speckit-pro/speckit_pro_runner/helpers/install.py` with read-only doctor/preflight classifications and deterministic remediation text.
- [x] T032 [US2] Register `install-codex-agents` as a deferred mutation helper with rollback/handoff metadata; existing Bash remains authoritative until XPLAT-007/XPLAT-008.
- [x] T033 [US2] Register `install-curated-set` as a deferred mutation helper with Bash-reference metadata and rollback/handoff metadata.
- [x] T034 [US2] Register `project-fixup apply` and `ensure-reviewability-preset` as deferred mutation-safe helper operations.
- [x] T035 [US2] Expose doctor/preflight operation ids through `speckit-pro/speckit_pro_runner/helpers/registry.py` so scaffold/status/autopilot can call the shared contract without active invocation cutover.
- [x] T036 [US2] Record Slice 2 promotion evidence in `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/promotion-records.json`.
- [x] T037 [HANDOFF] Update runner manifest/checksum metadata after install helper and inventory changes.
- [x] T038 [US2] Run the install-doctor focused test group and record evidence in the PR packet section of `docs/ai/specs/.process/XPLAT-006-workflow.md`.

**Checkpoint**: US2 is independently testable with fake install state and no real user-home writes.

---

## Phase 5: User Story 3 - PR-Emission, Restack, Relocation, And Reviewability Proof

**Goal**: Release reviewers can inspect deterministic PR-emission, restack, migration, relocation, and review-packet proof without live GitHub mutation or active cutover.

**Independent Test**: `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py` passes for PR body generation, dry-run PR command capture, and deferred registry coverage for remaining PR-emission/restack/relocation helpers.

- [x] T039 [P] [US3] Add failing PR-emission fixture tests for `generate-pr-body` golden output and authoritative command fixtures.
- [x] T040 [P] [US3] Add failing fake `gh` command-plan fixture tests for `multi-pr-emission`; register restack, migration, and relocation as deferred helper entries.
- [x] T041 [P] [US3] Add generated-output fixture coverage for authoritative request fixtures; register generated-index, `plan-layers`, `validate-pr-packet`, and workflow-contract write modes as deferred helper entries.
- [x] T042 [US3] Add `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` with atomic generated artifact writes and preserved packet/body content contracts.
- [x] T043 [US3] Implement PR-body golden output in `helpers/pr_emission.py` and register UAT-skeleton, final-reviewability-backstop, PR-packet, and workflow-contract output helpers as deferred/generated-output entries.
- [x] T044 [US3] Implement dry-run `multi-pr-emission` command planning and register restack, split-PR, migration, and relocation helper behavior as deferred command/generated-output entries.
- [x] T045 [US3] Register generated-index write/regenerate modes, `plan-layers` marker-plan output, `validate-pr-packet` persistence/workflow-event upserts, and `validate-pr-workflow-contract` write mode as deferred mutation helper entries.
- [x] T046 [US3] Keep `detect-stack-manager` to decision and command-plan evidence only; verify mutating command execution remains owned by `multi-pr-emission` and `restack` apply paths.
- [x] T047 [US3] Record Slice 3 promotion evidence in `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/promotion-records.json`.
- [x] T048 [HANDOFF] Update runner manifest/checksum metadata after PR-emission helper changes.
- [x] T049 [US3] Run the PR-emission focused test group and record evidence in the PR packet section of `docs/ai/specs/.process/XPLAT-006-workflow.md`.

**Checkpoint**: US3 is independently testable with fake repos and no live GitHub mutation.

---

## Phase 6: Cross-Cutting Verification And Handoff

**Purpose**: Prove all promoted helper behavior, hardening, and scope boundaries before final implementation acceptance.

- [x] T050 [HANDOFF] Run `python3 tests/speckit-pro/layer4-scripts/test-autopilot-phase-coverage.py` and record 6/6 hardening result.
- [x] T051 [HANDOFF] Run `python3 speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py --workflow docs/ai/specs/.process/XPLAT-006-workflow.md --state docs/ai/specs/.process/autopilot-state.json` and record `status=pass`.
- [x] T052 [HANDOFF] Run `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` and record the scope-audit test result.
- [x] T053 [HANDOFF] Run `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py` and record promoted helper coverage.
- [x] T054 [HANDOFF] Record Bash-reference comparison metadata from `bash-reference-manifest.json`; no Bash-backed helper is promoted to Python-authoritative by this PR.
- [x] T055 [HANDOFF] Run `bash tests/speckit-pro/run-all.sh --layer 4` and record Layer 4 totals.
- [x] T056 [HANDOFF] Run `bash tests/speckit-pro/run-all.sh --layer 1` and record Layer 1 totals.
- [x] T057 [HANDOFF] Run `bash tests/speckit-pro/run-all.sh` and record default deterministic suite totals.
- [x] T058 [HANDOFF] Run `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check $PWD` and `bash tests/speckit-pro/layer1-structural/validate-moc-stale-index.sh specs`.
- [x] T059 [HANDOFF] Run `git diff --name-only origin/main...HEAD` and scope-audit the diff for forbidden active cutover surfaces, listing the allowed hardening source/mirror separately.
- [x] T060 [HANDOFF] Update `docs/ai/specs/.process/XPLAT-006-workflow.md` with verification evidence, known gaps, approval boundaries, rollback/manual remediation notes, and XPLAT-007/XPLAT-008 handoff.
- [x] T061 [HANDOFF] Ensure the PR packet states that active Claude/Codex invocation cutover, generated-payload selection/cutover, repo-local release-gate migration, native matrix UAT, and public native-platform support claims are not delivered by XPLAT-006.

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
