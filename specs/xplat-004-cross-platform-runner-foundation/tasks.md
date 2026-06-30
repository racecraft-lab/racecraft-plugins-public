# Tasks: Cross-Platform Runner Foundation

**Input**: `spec.md`, `plan.md`, `data-model.md`, `contracts/`, `checklists/`, and `docs/ai/specs/.process/XPLAT-004-design-concept.md`

**Tests**: Required by the feature. Runner-specific tests use Python stdlib through the Layer 4 shell test orchestrator.

**Organization**: Tasks are grouped by the accepted two-slice implementation plan. Slice 1 delivers the runner/preflight core. Slice 2 delivers contract fixture parity plus metadata and runbook evidence.

**Format**: `- [ ] T### [P?] [US#] Description (FR-###, SC-###)`

- `[P]` means the task can run in parallel with other `[P]` tasks in the same phase because it touches different files or independent fixture/test sections.
- Tasks stay within XPLAT-004 scope: no real helper ports, no active skill/hook updates, no generated payload or `dist/**` copy, no repo-wide Bash gate replacement, and no public native-platform support claims.

## Slice 1: Runner/preflight core

**Goal**: Establish `<python> -m speckit_pro_runner` for source-checkout `runtime-info` and `preflight`, preserving the XPLAT-002 envelope/status/exit vocabulary and XPLAT-003 Python runtime boundary.

**Primary user story**: US1 - Structured runner preflight.

### Phase 1: Slice 1 Setup

**Purpose**: Create the minimal runner package and hook runner-specific tests into the existing Layer 4 gate without changing active plugin invocation surfaces.

- [ ] T001 [P] [US1] Create `speckit-pro/speckit_pro_runner/__init__.py` with runner identity constants for `runner_name`, `runner_contract_id`, `selected_runtime_name`, `contract_version`, and `runner_version` (FR-001, FR-003, FR-017)
- [ ] T002 [P] [US1] Create `speckit-pro/speckit_pro_runner/__main__.py` as the module entrypoint for `<python> -m speckit_pro_runner`; reserve CLI argv for `--help` and `--version` only (FR-001, FR-011, FR-017)
- [ ] T003 [P] [US1] Create empty implementation modules `speckit-pro/speckit_pro_runner/envelope.py` and `speckit-pro/speckit_pro_runner/runtime.py` for envelope/diagnostic logic and runtime/preflight logic (FR-001, FR-014, FR-017)
- [ ] T004 [P] [US1] Create `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh` as a thin Layer 4 wrapper that calls the Python test entrypoint with argv form and does not launch the runner through shell-specific quoting (FR-001, FR-012)
- [ ] T005 [P] [US1] Create `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` with stdlib-only helpers for invoking `<python> -m speckit_pro_runner` through `subprocess.run(..., shell=False)` (FR-001, FR-009)
- [ ] T006 [US1] Update `tests/speckit-pro/run-all.sh` to include only the new runner-specific Layer 4 wrapper, preserving the existing shell orchestrator rather than replacing repo-wide Bash gates (FR-009, FR-012)

### Phase 2: Tests First For Runtime-Info And Preflight

**Purpose**: Define failing tests for the Slice 1 runner/preflight contract before filling in implementation behavior.

- [ ] T007 [US1] Add a `runtime-info` module-invocation test in `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` that asserts one JSON stdout response with `status: "ok"`, exit code `0`, XPLAT-002 wire vocabulary, runner identities, Python version, platform, architecture, `source_checkout`, plugin root, and typed metadata pointer fields (FR-001, FR-002, FR-003, SC-001)
- [ ] T008 [US1] Add a valid `preflight` test in `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` using test-controlled prerequisite discovery to assert Python 3.11+, `specify`, plugin root, and metadata readiness are all reported before returning `ok` (FR-003, FR-004, FR-005, FR-010, SC-001)
- [ ] T009 [US1] Add fail-closed preflight tests for `python_too_old`, `specify_missing`, and `plugin_root_missing`, asserting `status: "missing_prerequisite"`, process exit code `3`, strict Diagnostic shape, and remediation object presence (FR-004, FR-005, FR-015, FR-019, SC-002)
- [ ] T010 [US1] Add validation tests for malformed JSON, structurally invalid envelope, unsupported schema version, and missing required fields, asserting `input_error`, exit code `2`, `legacy_exit_code: null`, line-delimited stderr JSON diagnostics, and codes `invalid_json`, `invalid_envelope`, `unsupported_schema_version`, and `missing_required_field` (FR-002, FR-006, FR-019, FR-020)

### Phase 3: Implement Runtime-Info And Preflight Core

**Purpose**: Implement only the foundation runner behavior needed by Slice 1 tests; do not port production helpers.

- [ ] T011 [US1] Implement the XPLAT-002 status and exit-code map in `speckit-pro/speckit_pro_runner/envelope.py`: `ok`/0, `expected_failure`/1, `input_error`/2, `missing_prerequisite`/3, `subprocess_failure`/4, and `internal_failure`/5 (FR-002)
- [ ] T012 [US1] Implement request parsing and validation in `speckit-pro/speckit_pro_runner/envelope.py` for `schema_version: "1.0"`, `helper_id: "runner"`, `operation: "preflight"` or `"runtime-info"`, `mode: "read_only"`, and `inputs` object (FR-001, FR-006, FR-017)
- [ ] T013 [US1] Implement response construction and line-delimited stderr diagnostic emission in `speckit-pro/speckit_pro_runner/envelope.py`, ensuring every diagnostic has `severity`, `source`, `code`, `message`, `remediation`, and bounded optional `details` (FR-006, FR-019, FR-020)
- [ ] T014 [US1] Implement `speckit-pro/speckit_pro_runner/__main__.py` to read JSON from stdin, dispatch only `runtime-info` and `preflight`, write exactly one JSON object to stdout, mirror diagnostics to stderr as LDJSON, and exit with the response `exit_code` (FR-001, FR-002, FR-006, FR-011)
- [ ] T015 [US1] Implement plugin-root detection in `speckit-pro/speckit_pro_runner/runtime.py` by walking ancestors from the resolved runner package file to the nearest `.claude-plugin/plugin.json` or `.codex-plugin/plugin.json`, failing closed with `plugin_root_missing` instead of guessing from cwd (FR-003, FR-015)
- [ ] T016 [US1] Implement typed path rendering in `speckit-pro/speckit_pro_runner/runtime.py` for plugin root, runner package, manifest file, and checksum file using `plugin_relative` values rooted at the detected plugin root, with stored values such as `speckit_pro_runner/...`, reader `display` values, and no absolute metadata paths (FR-003, FR-007, FR-016)
- [ ] T017 [US1] Implement `runtime-info` in `speckit-pro/speckit_pro_runner/runtime.py` with runner identities, Python version, platform, architecture, `source_vs_installed_context: "source_checkout"`, prerequisite records, and metadata pointer records without claiming preflight readiness when checks are not performed (FR-003, FR-010, FR-016)
- [ ] T018 [US1] Implement `preflight` in `speckit-pro/speckit_pro_runner/runtime.py` with Python 3.11+ and `specify` fail-closed checks, using test-controlled discovery hooks and diagnostics `python_too_old` and `specify_missing` as applicable (FR-004, FR-005, SC-002)
- [ ] T019 [US1] Run Slice 1 verification: `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh`, `bash tests/speckit-pro/run-all.sh --layer 4`, and `git diff --check` (FR-009, SC-001, SC-002)

## Slice 2: Contract parity and metadata

**Goal**: Add the fixture runway, metadata integrity surface, and platform runbook evidence while keeping installed workflows unchanged.

**Primary user stories**: US2 - Contract fixture runway for helper ports; US3 - Inspectable runner identity and source metadata.

### Phase 4: Tests First For Contract Fixture Parity

**Purpose**: Define the fixture matrix and assertions before extending the runner primitives.

- [ ] T020 [US2] Create `tests/speckit-pro/layer4-scripts/fixtures/speckit-pro-runner/contract-fixtures.json` with valid envelope, invalid JSON, invalid envelope, unsupported schema version, and missing-field cases, each carrying expected status, exit code, diagnostic code, and remediation expectations (FR-006, FR-009, FR-020, SC-003)
- [ ] T021 [US2] Add typed-path fixture cases to `tests/speckit-pro/layer4-scripts/fixtures/speckit-pro-runner/contract-fixtures.json` for paths with spaces, Windows separators, accepted in-bound traversal, rejected out-of-bound traversal, and rejection of untyped path values (FR-007, FR-009, SC-003)
- [ ] T022 [US2] Add subprocess fixture cases to `tests/speckit-pro/layer4-scripts/fixtures/speckit-pro-runner/contract-fixtures.json` for nonzero exit, timeout, and stderr-only failure, with explicit `timeout_seconds` no greater than `5` and expected 16 KiB stdout/stderr capture bounds (FR-008, FR-021, SC-003, SC-007)
- [ ] T023 [US2] Extend `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` to load contract fixtures and assert every non-`ok` fixture has expected status, process exit code, diagnostic codes, and remediation object presence (FR-009, FR-020, SC-003)
- [ ] T024 [US2] Extend `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` to assert fixture subprocess results use `shell=False`, preserve argv as an array, record `timeout_seconds`, `duration_ms`, bounded stdout/stderr byte counts, `limit_bytes: 16384`, and truncation flags (FR-008, FR-021, SC-003, SC-007)
- [ ] T025 [US2] Extend `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` to assert contract fixture operations stay synthetic and do not call `generate-spec-index.sh`, scaffold/status/autopilot helpers, install helpers, PR packet helpers, or any other real production helper behavior (FR-011, FR-018)

### Phase 5: Implement Contract Fixture Primitives

**Purpose**: Implement only fixture primitives required for downstream helper ports; do not introduce real helper IDs or helper-specific CLI arguments.

- [ ] T026 [US2] Extend `speckit-pro/speckit_pro_runner/runtime.py` with typed-path validation helpers that accept only typed path objects, preserve `kind`, `value`, and `display`, keep spaces intact, tolerate Windows separators, and reject traversal only when it escapes the declared trust boundary (FR-007, FR-017)
- [ ] T027 [US2] Extend `speckit-pro/speckit_pro_runner/runtime.py` with a fixture-only subprocess result primitive using `shell=False`, explicit timeout, stdout/stderr capture limits of 16 KiB per stream, byte counts, truncation flags, `duration_ms`, and distinct diagnostics for `subprocess_nonzero`, `subprocess_timeout`, and `subprocess_stderr_only_failure` (FR-008, FR-019, FR-021)
- [ ] T028 [US2] Extend `speckit-pro/speckit_pro_runner/envelope.py` and `runtime.py` so fixture requests can exercise envelope, typed-path, subprocess, diagnostics, runtime-info, and preflight categories without adding production helper operations beyond `runtime-info` and `preflight` (FR-009, FR-011, FR-018)
- [ ] T029 [US2] Run contract fixture verification: `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh`, `bash tests/speckit-pro/run-all.sh --layer 4`, and `git diff --check` (FR-009, FR-020, FR-021, SC-003)

### Phase 6: Tests First For Metadata And Runbook Evidence

**Purpose**: Define metadata/readiness and non-claim evidence before adding reviewer-facing integrity files.

- [ ] T030 [US3] Add manifest validation tests in `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` for `runner_name`, `runner_contract_id`, `selected_runtime_name`, `contract_version`, `plugin_version`, `runner_version`, `source_revision`, `python_minimum_version: "3.11"`, `specify_required: true`, `checksum_algorithm: "sha256"`, and `runner_files[]` (FR-010, SC-004)
- [ ] T031 [US3] Add checksum coverage tests in `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` requiring every runner-owned `speckit-pro/speckit_pro_runner/**.py` file to be listed with a SHA-256 digest while excluding `speckit-pro-runner.manifest.json` and `speckit-pro-runner.sha256` from their own checksum set (FR-010, SC-004)
- [ ] T032 [US3] Add metadata readiness failure tests for missing, incomplete, mismatched/stale, and skipped metadata checks, asserting `missing_prerequisite`, exit code `3`, verification statuses `missing_metadata`, `incomplete_metadata`, `mismatch`, and `not_checked`, and diagnostics `runner_metadata_missing`, `runner_metadata_incomplete`, `runner_metadata_mismatch`, and `runner_metadata_not_checked` (FR-010, FR-019, FR-020, SC-002)
- [ ] T033 [US3] Add runbook fixture checks in `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` for `specs/xplat-004-cross-platform-runner-foundation/contracts/platform-runbook-fixtures.md`, requiring at least one Windows and one Linux `source_checkout` fixture with launcher command family, expected status/exit/diagnostic, metadata verification expectation, and explicit non-claim language (FR-022, SC-007)
- [ ] T034 [US3] Add no-cutover scope assertions in `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` that fail if XPLAT-004 changed `dist/**`, active Claude/Codex skills, hooks, generated payloads, install behavior, or public docs to invoke or claim the runner (FR-012, FR-013, SC-005)

### Phase 7: Implement Metadata And Runbook Evidence

**Purpose**: Add source-checkout integrity metadata and bounded platform guidance without implying installed-cache proof or public platform readiness.

- [ ] T035 [US3] Create `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` with the manifest identities, contract/runtime versions, plugin version, source revision, Python minimum, `specify_required`, checksum algorithm, and `runner_files[]` using `plugin_relative` paths such as `speckit_pro_runner/__main__.py` (FR-010, FR-016, SC-004)
- [ ] T036 [US3] Create `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` with SHA-256 records for runner-owned Python source files only, excluding the manifest and checksum files themselves (FR-010, SC-004)
- [ ] T037 [US3] Implement metadata loading and verification in `speckit-pro/speckit_pro_runner/runtime.py`, returning `verified`, `mismatch`, `missing_metadata`, `incomplete_metadata`, or `not_checked` based on actual checks and failing preflight closed when required metadata is not verified (FR-010, FR-019, FR-020)
- [ ] T038 [P] [US3] Populate `specs/xplat-004-cross-platform-runner-foundation/contracts/platform-runbook-fixtures.md` with deterministic Windows and Linux source-checkout fixture rows, host-level `python_launcher_unavailable` guidance where appropriate, metadata verification expectations, and non-claim statements that installed-cache launch proof, native UAT, release-readiness, and public support claims remain XPLAT-007 scope (FR-004, FR-022, SC-007)
- [ ] T039 [US3] Update `runtime-info` and `preflight` output in `speckit-pro/speckit_pro_runner/runtime.py` so metadata pointers and verification status align with the manifest/checksum files and never use `verified` unless current metadata was actually checked (FR-003, FR-010, FR-016)
- [ ] T040 [US3] Validate metadata and runner evidence with `python3 -m json.tool speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`, `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh`, and `git diff --check` (FR-010, SC-004)

### Phase 8: Final Verification And Review Packet

**Purpose**: Prove both slices are reviewable, traceable, and bounded to XPLAT-004.

- [ ] T041 [US1] Run focused runner verification: `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh` (FR-001, FR-009, SC-001, SC-003)
- [ ] T042 [US2] Run the full Layer 4 deterministic suite: `bash tests/speckit-pro/run-all.sh --layer 4` (FR-009, FR-020, FR-021, SC-003)
- [ ] T043 [US3] Run structural verification for changed plugin/test files: `bash tests/speckit-pro/run-all.sh --layer 1` (FR-012, FR-013, SC-005)
- [ ] T044 [US3] Run generated index verification without copying payloads: `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"` (FR-012, FR-013, SC-005)
- [ ] T045 [US3] Run the final deterministic suite when feasible: `bash tests/speckit-pro/run-all.sh` (FR-009, SC-001, SC-003, SC-005)
- [ ] T046 [US3] Review `git diff --name-only` and confirm no XPLAT-004 changes under `dist/**`, active skill/hook/generated payload/install/public-doc cutover surfaces, or public native-platform claim surfaces (FR-012, FR-013, SC-005)
- [ ] T047 [US3] Prepare the PR review packet with both planned slices, review order, changed surfaces, traceability, verification evidence, known gaps, rollback notes, and deferred boundaries for XPLAT-005, XPLAT-006, and XPLAT-007 (FR-014, FR-018, FR-022, SC-006)

## Dependencies And Execution Order

### Slice Dependencies

- **Slice 1** must land first because Slice 2 fixtures and metadata tests call the runner package, module entrypoint, envelope builder, diagnostics, and runtime/preflight primitives.
- **Slice 2** depends on Slice 1 and adds fixture breadth, checksum/manifest metadata, runbook fixture evidence, and final no-cutover verification.

### Phase Dependencies

- **Phase 1** has no prerequisites.
- **Phase 2** depends on Phase 1 test scaffolding.
- **Phase 3** depends on Phase 2 tests.
- **Phase 4** depends on Slice 1 runner invocation and test helpers.
- **Phase 5** depends on Phase 4 fixture tests.
- **Phase 6** depends on Slice 1 runtime metadata pointer shape and Slice 2 fixture test helpers.
- **Phase 7** depends on Phase 6 metadata/runbook tests.
- **Phase 8** depends on both slices.

### User Story Dependencies

- **US1** is the MVP and must complete before helper-port implementers can use the runner foundation.
- **US2** depends on the Slice 1 runner core but is independently testable through the contract fixture suite.
- **US3** depends on the Slice 1 metadata pointer shape and Slice 2 metadata files; it is independently testable through manifest/checksum/runbook/no-cutover checks.

## Parallel Opportunities

- In Phase 1, T001-T005 can proceed in parallel because each task owns a distinct new source or test file.
- In Phase 7, T038 can proceed in parallel with metadata file creation because it owns the runbook fixture contract file.
- After Slice 1 is complete, US2 fixture work and US3 runbook population can be split across implementers if edits to shared test files are serialized.

## Requirements Coverage

| Requirement | Covered by tasks |
|---|---|
| FR-001 | T001, T002, T005, T007, T012, T014, T041 |
| FR-002 | T007, T010, T011, T014 |
| FR-003 | T001, T007, T008, T015, T016, T017, T039 |
| FR-004 | T008, T009, T018, T038 |
| FR-005 | T008, T009, T018 |
| FR-006 | T010, T012, T013, T014, T020 |
| FR-007 | T016, T021, T026 |
| FR-008 | T022, T024, T027 |
| FR-009 | T005, T006, T019, T020, T023, T029, T041, T042 |
| FR-010 | T008, T017, T030, T031, T032, T035, T036, T037, T039, T040 |
| FR-011 | T002, T014, T025, T028 |
| FR-012 | T004, T006, T034, T043, T044, T046 |
| FR-013 | T034, T043, T044, T046 |
| FR-014 | T003, T047 |
| FR-015 | T009, T015 |
| FR-016 | T016, T035, T039 |
| FR-017 | T001, T002, T003, T012, T026 |
| FR-018 | T025, T028, T047 |
| FR-019 | T009, T010, T013, T027, T032, T037 |
| FR-020 | T009, T010, T020, T023, T029, T032, T037 |
| FR-021 | T022, T024, T027, T029 |
| FR-022 | T033, T038, T047 |

## Success Criteria Coverage

| Success criterion | Covered by tasks |
|---|---|
| SC-001 | T007, T008, T019, T041 |
| SC-002 | T009, T018, T032 |
| SC-003 | T020, T021, T022, T023, T024, T025, T029, T041, T042 |
| SC-004 | T030, T031, T035, T036, T037, T040 |
| SC-005 | T034, T043, T044, T046 |
| SC-006 | T047 |
| SC-007 | T022, T024, T033, T038 |

## Out Of Scope For These Tasks

- No real helper ports for read-only or mutation helpers.
- No active Claude Code or Codex skill invocation updates.
- No hook cutover and no install-behavior cutover.
- No generated payload copy into `dist/**`.
- No repo-wide Bash gate replacement.
- No public native Windows, macOS, or Linux support claims.
- No installed-cache launch proof, native matrix UAT, release-readiness, signatures, SBOMs, provenance attestations, reproducible builds, or formal audit evidence.
