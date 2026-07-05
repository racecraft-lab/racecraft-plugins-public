# Tasks: Python Tooling and Release-Gate Migration

**Input**: Design documents from `specs/xplat-007-python-tooling-and-release-gate-migration/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, and `docs/ai/specs/.process/XPLAT-007-design-concept.md`

**Tests**: Required. Write failing Python fixtures/tests before each migrated gate replacement. Preserve Bash-reference comparison evidence before promoting any Python operation as authoritative.

**Reviewability**: The setup warning for two surfaces (`harness/adapter`, `docs/process`) is accepted for one workflow with three internal slices. Before implementation starts, confirm the planned diff still fits the XPLAT-007 plan envelope; if it expands beyond the roadmap reviewability budget, split after Slice 1 before payload/release helper implementation.

**Foundation split confirmation (T007, 2026-07-04)**: The foundation marker stays within the planned `harness/adapter` and `docs/process` surfaces. It adds gate package scaffolding, planned-operation metadata, dispatch rejection behavior, fixtures, tests, and runner metadata only; active US1/US2/US3 gate rewrites remain deferred to later markers.

**Organization**: Tasks are grouped by independently testable user story and accepted implementation slice. `[P]` marks only tasks that touch independent fixtures, command adapters, docs/process evidence, or guard cases and do not compete for shared runner registration, promotion records, payload fixtures, or release-readiness summaries.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other `[P]` tasks in the same phase because files and state do not overlap.
- **[Story]**: Maps to `spec.md` user stories (`US1`, `US2`, `US3`).
- Every task names the exact file or path family it changes.

---

## Phase 1: Setup (Shared Structure)

**Purpose**: Create the XPLAT-007 runner gate and fixture scaffolding without changing active command behavior.

- [x] T001 Create `speckit-pro/speckit_pro_runner/gates/__init__.py` and export the gate package without registering active operations.
- [x] T002 Create `speckit-pro/speckit_pro_runner/gates/registry.py` with planned gate operation metadata for suite, payload, release, install, and guard groups.
- [x] T003 Create empty implementation modules `speckit-pro/speckit_pro_runner/gates/suite.py`, `speckit-pro/speckit_pro_runner/gates/payloads.py`, `speckit-pro/speckit_pro_runner/gates/release.py`, and `speckit-pro/speckit_pro_runner/gates/active_path_guard.py`.
- [x] T004 Create `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/` and the XPLAT-007 fixture root expected by `plan.md`.
- [x] T005 Create `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json` with schema-valid planned records for each migrated gate group.
- [x] T006 Add the initial XPLAT-007 test harness skeleton in `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py`.
- [x] T007 Confirm the implementation split decision against the reviewability budget in `specs/xplat-007-python-tooling-and-release-gate-migration/tasks.md` before active gate rewrites begin.

**Checkpoint**: Fixture roots, gate modules, and promotion-record scaffolding exist; no active Bash path has been retired yet.

---

## Phase 2: Foundational Runner Contracts (Blocking Prerequisites)

**Purpose**: Wire shared runner behavior needed by every migrated gate while preserving the XPLAT-004 envelope and exit-code contract.

**Critical**: User story implementation must not promote any Python gate until this phase is complete.

- [x] T008 Implement shared operation lookup and validation in `speckit-pro/speckit_pro_runner/gates/registry.py` for the operation groups named in `plan.md`.
- [x] T009 Wire gate operation dispatch into `speckit-pro/speckit_pro_runner/runtime.py` without changing existing helper operation behavior.
- [x] T010 Extend `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` with reusable assertions for runner stdout JSON, stderr diagnostics, status-to-exit mapping, and artifact path checks.
- [x] T011 Update `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` to include new gate package files after the skeleton dispatch is present.
- [x] T012 Update `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` after manifest-covered runner files are added.
- [x] T013 Validate all schemas under `specs/xplat-007-python-tooling-and-release-gate-migration/contracts/` with Python JSON parsing before adding gate-specific fixtures.

**Checkpoint**: Runner can reject unknown gate operations deterministically through the JSON envelope; user-story work can start.

---

## Phase 3: User Story 1 - Run Repo-Local Gates Through Python (Priority: P1)

**Goal**: Maintainers can run active repo-local test/eval gates through Python runner operations with equivalent pass/fail meaning.

**Independent Test**: Run the XPLAT-007 default-suite request through `python -m speckit_pro_runner` and verify top-level, layer, eval, integration, and parity gate results are represented without Bash as an active entrypoint.

### Tests and Fixtures for User Story 1

> Write these fixtures/tests first and confirm they fail before implementation.

- [x] T014 [P] [US1] Add the default suite request fixture in `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-default-suite.json` covering top-level, Layer 1, Layer 4, Layer 5, Layer 7, and Layer 8 gate dispatch.
- [x] T015 [US1] Add failing suite-runner tests in `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` for `run-default-suite` and `run-layer` success, expected failure, stdout, stderr, and exit-code behavior.
- [x] T016 [US1] Add Bash-reference comparison expectations in `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json` for `tests/speckit-pro/run-all.sh`, `tests/speckit-pro/check-toolchain.sh`, Layer 1, Layer 4, Layer 5, Layer 7, and Layer 8.
- [x] T017 [US1] Add failing tests in `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` that reject shell command strings, `shell=True`, `os.system`, and command-string subprocess use in promoted suite operations.
- [x] T018 [US1] Add failing tests in `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` for AI-eval dispatch and missing-prerequisite diagnostics for Layer 2, Layer 3, and Layer 6.

### Implementation for User Story 1

- [x] T019 [US1] Implement `run-default-suite` in `speckit-pro/speckit_pro_runner/gates/suite.py` with deterministic aggregation for the current default deterministic layers.
- [x] T020 [US1] Implement `run-layer` in `speckit-pro/speckit_pro_runner/gates/suite.py` for Layer 1 structural checks, Layer 4 helper tests, Layer 5 tool-scoping checks, Layer 7 integration, and Layer 8 parity.
- [x] T021 [US1] Implement `run-ai-evals` in `speckit-pro/speckit_pro_runner/gates/suite.py` for opt-in Layer 2, Layer 3, and Layer 6 dispatch with stable missing-prerequisite results.
- [x] T022 [US1] Implement `run-integration-suite` and `run-parity-suite` in `speckit-pro/speckit_pro_runner/gates/suite.py` using argv-list subprocesses only where subprocesses are unavoidable.
- [x] T023 [US1] Register `run-default-suite`, `run-layer`, `run-ai-evals`, `run-integration-suite`, and `run-parity-suite` in `speckit-pro/speckit_pro_runner/gates/registry.py`.
- [x] T024 [US1] Update `speckit-pro/speckit_pro_runner/runtime.py` to expose the US1 operations through the runner envelope.
- [x] T025 [US1] Record Bash-reference comparison results for US1 gates in `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json`.
- [x] T026 [US1] Promote US1 gates in `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json` only after fixture parity, exit-code, stream, and artifact comparisons pass.
- [x] T027 [US1] Remove US1 Bash command paths from active runner or workflow invocations, or reclassify retained references as inactive parity evidence in `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json`.
- [x] T028 [US1] Update `specs/xplat-007-python-tooling-and-release-gate-migration/quickstart.md` with the Python suite-gate request and explicit US1 non-goals.

**Checkpoint**: User Story 1 is independently testable through Python runner requests and has promotion evidence for the migrated test/eval gates.

---

## Phase 4: User Story 2 - Run Payload, Install, And Release Checks Through Python (Priority: P2)

**Goal**: Release maintainers can build test payload evidence, refresh local plugin fixtures, verify installs, check version sync, and run release-readiness checks through Python runner operations.

**Independent Test**: Run XPLAT-007 payload, install-verification, and release-readiness requests against deterministic fixtures and verify no release payload cutover, real `HOME` mutation, public install/runtime docs or support-claim change, or native installed-plugin UAT claim occurs.

### Tests and Fixtures for User Story 2

> Write these fixtures/tests first and confirm they fail before implementation.

- [ ] T029 [P] [US2] Add `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/test-payload-evidence.json` for Claude/Codex test payload evidence only.
- [ ] T030 [P] [US2] Add `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/payload-evidence-cases.json` covering fingerprints, output roots, stale generated files, and `release_payload_cutover=false`.
- [ ] T031 [P] [US2] Add `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/install-verification.json` for fake-home local refresh and install verification.
- [ ] T032 [P] [US2] Add `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/install-verification-cases.json` covering stubbed CLIs, bundled-agent inventory, safe repair plans, Windows-style paths, spaces, traversal rejection, and line-ending normalization.
- [ ] T033 [P] [US2] Add `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/release-readiness.json` for changed-plugin detection, suite result aggregation, marketplace/version sync, PR title, workflow contract, payload evidence, release-PR payload-sync parsing, post-release drift checks, and release-readiness aggregation.
- [ ] T034 [P] [US2] Add `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/release-readiness-cases.json` covering stale version data, missing promotion records, stale payload evidence, changed-plugin false positives, suite aggregation failures, release-PR payload-sync parse failures, post-release drift, workflow contract failures, and XPLAT-008 handoff items.
- [ ] T035 [US2] Add failing payload evidence tests in `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` for `build-test-payload-evidence` read-only, dry-run, and fixture-scoped apply modes.
- [ ] T036 [US2] Add failing install verification tests in `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` for `refresh-local-plugin-fixture` and `verify-install` with fake-home roots only.
- [ ] T037 [US2] Add failing release-readiness tests in `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` for `detect-changed-plugin`, `aggregate-suite-results`, `check-marketplace-version-sync`, `validate-pr-title`, `validate-workflow-contract`, `check-payload-evidence`, `parse-release-pr-payload-sync`, `check-post-release-drift`, and `release-readiness`.
- [ ] T038 [US2] Add Bash-reference comparison expectations in `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json` for `scripts/build-plugin-payloads.sh`, `scripts/refresh-local-plugin.sh`, `scripts/sync-marketplace-versions.sh`, and release workflow checks.

### Implementation for User Story 2

- [ ] T039 [US2] Implement `build-test-payload-evidence` in `speckit-pro/speckit_pro_runner/gates/payloads.py` with fixture or temporary output roots only.
- [ ] T040 [US2] Implement `refresh-local-plugin-fixture` in `speckit-pro/speckit_pro_runner/gates/payloads.py` using read-only and dry-run command plans against fixture roots.
- [ ] T041 [US2] Implement `verify-install` in `speckit-pro/speckit_pro_runner/gates/payloads.py` using `speckit-pro/speckit_pro_runner/install_inventory.json` and XPLAT-006 bundled-agent boundaries without native UAT claims.
- [ ] T042 [US2] Register `build-test-payload-evidence`, `refresh-local-plugin-fixture`, and `verify-install` in `speckit-pro/speckit_pro_runner/gates/registry.py`.
- [ ] T043 [US2] Implement `detect-changed-plugin`, `aggregate-suite-results`, `check-marketplace-version-sync`, `validate-pr-title`, `validate-workflow-contract`, `check-payload-evidence`, `parse-release-pr-payload-sync`, `check-post-release-drift`, and `release-readiness` in `speckit-pro/speckit_pro_runner/gates/release.py`.
- [ ] T044 [US2] Register all release-readiness operations named in `plan.md` in `speckit-pro/speckit_pro_runner/gates/registry.py`.
- [ ] T045 [US2] Update `speckit-pro/speckit_pro_runner/runtime.py` to expose US2 operations while preserving existing helper behavior.
- [ ] T046 [US2] Record Bash-reference comparison results for payload, install, version-sync, and release-readiness gates in `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json`.
- [ ] T047 [US2] Promote US2 gates in `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json` only after parity, artifact hash, stream, and exit-code results pass.
- [ ] T048 [US2] Remove `scripts/build-plugin-payloads.sh`, `scripts/refresh-local-plugin.sh`, and `scripts/sync-marketplace-versions.sh` from active release gate paths, or classify retained references as inactive parity evidence.
- [ ] T049 [US2] Rebuild XPLAT-007 test payload evidence through the Python runner into fixture or temporary output roots and verify `release_payload_cutover=false`.
- [ ] T050 [US2] Update `specs/xplat-007-python-tooling-and-release-gate-migration/quickstart.md` with fixture-bound payload, install, and release-readiness commands.

**Checkpoint**: User Stories 1 and 2 are independently testable through Python runner requests; release cutover remains deferred.

---

## Phase 5: User Story 3 - Review Active No-Shell Guardrails (Priority: P3)

**Goal**: Reviewers can run a deterministic guard that blocks active Bash, `.sh`, `jq`, shell interpolation, shell parsing, and unsafe subprocess usage while classifying non-active evidence correctly.

**Independent Test**: Run the active-path guard request and verify blocking fixtures fail with path/category/remediation detail while final clean implementation exits successfully with zero blocking findings.

### Tests and Fixtures for User Story 3

> Write these fixtures/tests first and confirm they fail before implementation.

- [ ] T051 [P] [US3] Add `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/active-path-guard.json` for clean and expected-failure guard runs.
- [ ] T052 [P] [US3] Add `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/active-path-guard-cases.json` covering active Bash, `.sh`, `jq`, Git Bash, WSL, PowerShell helper, shell parsing, shell interpolation, `shell=True`, `os.system`, and command-string subprocess findings.
- [ ] T053 [US3] Add failing active-path guard tests in `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` for blocking active gate findings and runner exit `1`.
- [ ] T054 [US3] Add failing active-path guard tests in `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` for nonblocking classifications: archive provenance, temporary parity evidence, consumer Spec Kit helper, generated payload mirror, docs out of scope, CI dispatch glue, and XPLAT-008 cutover surface.
- [ ] T055 [US3] Add failing workflow-dispatch tests in `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` proving CI shell is allowed only when it directly invokes Python gates and contains no plugin validation, packaging, install, release, loop, `jq`, or parsing logic.

### Implementation for User Story 3

- [ ] T056 [US3] Implement active-path discovery and role classification in `speckit-pro/speckit_pro_runner/gates/active_path_guard.py` for `tests/speckit-pro/**`, `scripts/*`, reachable `speckit-pro/**/scripts/**`, and `.github/workflows/**`.
- [ ] T057 [US3] Implement forbidden-pattern detection in `speckit-pro/speckit_pro_runner/gates/active_path_guard.py` for Bash, `.sh`, `jq`, Git Bash, WSL, PowerShell helpers, shell parsing, shell interpolation, `shell=True`, `os.system`, and command-string subprocess use.
- [ ] T058 [US3] Implement nonblocking classifications in `speckit-pro/speckit_pro_runner/gates/active_path_guard.py` for archive/provenance, temporary parity evidence, consumer Spec Kit helpers, generated payload mirrors, docs out of scope, CI dispatch glue, and XPLAT-008 cutover surfaces.
- [ ] T059 [US3] Register `active-path-guard` and `classify-shell-finding` in `speckit-pro/speckit_pro_runner/gates/registry.py`.
- [ ] T060 [US3] Update `.github/workflows/pr-checks.yml` so plugin validation and release-readiness steps dispatch directly to Python runner gates without Bash or `jq` validation logic.
- [ ] T061 [US3] Update `.github/workflows/release.yml` so release checks dispatch directly to Python runner gates without Bash or `jq` release logic.
- [ ] T062 [US3] Remove active Bash command paths from `tests/speckit-pro/**`, `scripts/*.sh`, `speckit-pro/skills/**/scripts/**`, `speckit-pro/codex-skills/**/scripts/**`, and `speckit-pro/scripts/**` after their Python replacements are promoted, or reclassify retained files as inactive parity evidence.
- [ ] T063 [US3] Update `CLAUDE.md` and `docs-site/src/content/docs/contribute-and-release.md` only for maintainer-facing repo-local Python gate commands required by XPLAT-007.
- [ ] T064 [US3] Record XPLAT-008 handoff items for active Claude/Codex invocation cutover, generated release payloads, public docs, release notes, installed-cache UAT, native platform UAT, update, autoheal, and public release readiness in release-readiness evidence.
- [ ] T065 [US3] Verify the final active-path guard emits `status=ok`, exit `0`, and `data.blocking_count=0` for the implementation.

**Checkpoint**: All user stories are independently functional, promoted gates have retirement evidence, and the active-path guard blocks active shell regressions.

---

## Phase 6: Cross-Cutting Validation and PR Evidence

**Purpose**: Refresh runner metadata, validate task coverage, and prepare review evidence without committing.

- [ ] T066 Update `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` after final gate, workflow, and metadata changes.
- [ ] T067 Update `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` after final manifest-covered file changes.
- [ ] T068 Validate every XPLAT-007 contract schema in `specs/xplat-007-python-tooling-and-release-gate-migration/contracts/` with Python JSON parsing.
- [ ] T069 Run focused gate fixture tests in `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py`.
- [ ] T070 Run the source-checkout `runtime-info` and `preflight` runner smoke commands from `specs/xplat-007-python-tooling-and-release-gate-migration/quickstart.md` after manifest/checksum updates.
- [ ] T071 Run the Python default suite, active-path guard, test payload evidence, install-verification, and release-readiness requests from `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/`, including changed-plugin, payload-sync, and post-release drift cases.
- [ ] T072 Run the migrated Layer 1, Layer 4, and deterministic suite through Python-authoritative paths after promotion.
- [ ] T073 Run the spec index and stale-MOC checks for `specs/xplat-007-python-tooling-and-release-gate-migration/`.
- [ ] T074 Run `git diff --check` and inspect the diff for accidental active Claude/Codex invocation, generated release payload cutover, public install docs, release notes, update, autoheal, or native UAT changes.
- [ ] T075 Generate the PR review packet with review order, scope budget, FR/SC traceability, promotion evidence, parity evidence, no-shell guard evidence, test payload evidence, maintainer-doc update notes, known gaps, rollback notes, and XPLAT-008 handoff.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundation**: Depends on Phase 1.
- **US1**: Depends on Foundation.
- **US2**: Depends on US1.
- **US3**: Depends on US2.
- **Phase 6 Validation**: Depends on US3.

### Story Dependencies

- **US1**: Depends on Foundation only.
- **US2**: Depends on US1.
- **US3**: Depends on US2.

US1 remains the MVP verification base. US2 fixture preparation can start after
Foundation, but US2 promotion waits for US1 gate evidence. US3 guard fixture
work can start after Foundation, but final cleanup waits for promoted US1 and
US2 replacements.

### Within Each Gate Group

1. Add failing request fixtures and Python tests.
2. Add Bash-reference comparison expectations.
3. Implement the Python runner operation.
4. Register the operation through the shared runner gate registry.
5. Run fixture and Bash-reference comparison.
6. Promote Python as authoritative in `promotion-records.json`.
7. Remove active Bash references or reclassify retained references as inactive evidence.
8. Re-run the active-path guard.

---

## Parallel Opportunities

- T014 can run in parallel with US2 fixture tasks T029-T034 and US3 fixture tasks T051-T052 after Phase 2 because they touch separate request/case files.
- T029-T034 can run in parallel with each other because they create independent payload, install, and release fixture files.
- T051-T052 can run in parallel with US2 fixture work because guard fixtures are independent from payload and release-readiness fixture files.
- T028, T050, and T063 can run in parallel when limited to separate documentation sections and after the corresponding command behavior is defined.
- Do not run shared registry tasks T008, T023, T042, T044, or T059 in parallel with each other.
- Do not run promotion-record tasks T016, T025-T027, T038, T046-T048, or T064 in parallel with each other.
- Do not run workflow cleanup T060-T061 before US1 and US2 operations are registered and promotion evidence is available.

---

## Implementation Strategy

### MVP First: US1

1. Complete Phase 1 and Phase 2.
2. Complete US1 fixtures, tests, Bash-reference comparison, Python operations, registration, and promotion records.
3. Stop and validate the Python suite gate independently before starting US2 promotion.

### Incremental Delivery

1. US1 establishes Python-authoritative repo-local test/eval gates.
2. US2 migrates payload, install, and release-readiness gates using the US1 verification base.
3. US3 enforces active-path guardrails and removes or reclassifies active Bash references.
4. Phase 6 produces the review packet and final validation evidence.

### Reviewability Split Point

If implementation expands beyond the planned XPLAT-007 envelope before active gate rewrites begin, split after US1:

- Keep US1 as the Python test/eval gate migration.
- Move US2 payload/install/release helper migration and US3 final cleanup into follow-up specs.
- Do not start US2 promotion until the split is recorded and accepted.

---

## User Story Coverage

| User Story | Covered By Tasks | Independent Validation |
|---|---|---|
| US1 Run repo-local gates through Python | T014-T028, T069, T071-T072 | `run-default-suite`, `run-layer`, `run-ai-evals`, `run-integration-suite`, and `run-parity-suite` runner requests |
| US2 Run payload, install, and release checks through Python | T029-T050, T071 | `test-payload-evidence`, `install-verification`, and `release-readiness` runner requests |
| US3 Review active no-shell guardrails | T051-T065, T071, T074 | `active-path-guard` request with zero final blocking findings and expected-failure fixtures |

---

## Notes

- `[P]` tasks are parallel-safe only where files and shared state do not overlap.
- Do not update active Claude/Codex invocation behavior, generated release payload selection or cutover, public install docs, release notes, update, autoheal, or native UAT artifacts in XPLAT-007.
- Do not keep thin local Bash wrappers as active transition entrypoints.
- Bash-reference comparison is temporary migration proof and must be retired from active gates after Python promotion.
