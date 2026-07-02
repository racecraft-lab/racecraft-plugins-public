# Tasks: XPLAT-005 Read-Only Helper Port

**Input**: Design documents from `specs/xplat-005-read-only-helper-port/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, and `docs/ai/specs/.process/XPLAT-005-design-concept.md`

**Tests**: Required. Write failing Python tests, golden fixtures, rejected-input fixtures, and Bash-reference comparison cases before each helper port.

**Reviewability**: XPLAT-005 remains one workflow with two internal slices. Re-check the accepted reviewability warning before implementation starts; if helper registry plus read-only parity work expands beyond the accepted planned scope, record the split point before source edits continue.

**Guardrails**:

- Promote a Bash-backed helper only after golden fixture parity and source-checkout Bash-reference comparison both pass.
- Keep Python tests authoritative per helper only after parity is accepted for that helper.
- Preserve stdout JSON schemas, stderr diagnostics, deterministic remediation text/actions, and exact exit-code semantics for accepted and rejected inputs.
- Define rejected-input fixtures per applicable failure class: `invalid_input`, `missing_input`, `malformed_json`, `missing_file`, `unsupported_path`, `missing_prerequisite`, `validation_failure`, `subprocess_failure`, and `preflight_failure`.
- Use argv-only subprocess calls in the Bash-reference harness; do not use `shell=True`, shell-command strings, `os.system`, shell interpolation, or unbounded subprocess input.
- Resolve filesystem inputs against repo/plugin trust boundaries and reject traversal or symlink escapes before helper logic reads files.
- Do not generate PR bodies, emit split-PR state, install agents, relocate artifacts, mutate repository/user-local state, update active Claude/Codex invocations, or update generated payloads.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel because it touches independent files and does not compete for shared registry, harness, or manifest files.
- **[US1]**: Maintainer-facing helper parity behavior.
- **[US2]**: Helper-port implementer registry/module pattern.
- **[US3]**: Release-review promotion evidence and scope boundaries.

## Phase 1: Setup And Reviewability Check

**Purpose**: Prepare the feature workspace and enforce the accepted two-slice boundary before source edits.

- [ ] T001 Re-check the accepted reviewability scope and record the continue-or-split decision in `specs/xplat-005-read-only-helper-port/tasks.md`
- [ ] T002 Create the helper package and fixture directories at `speckit-pro/speckit_pro_runner/helpers/` and `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/`
- [ ] T003 [P] Add the local source-checkout runtime-info smoke request fixture in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/smoke-runtime-info-request.json`
- [ ] T004 [P] Add synthetic Windows, no-Bash, spaces-in-paths, traversal, and symlink-escape fixture cases in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/synthetic-paths.json`
- [ ] T005 [P] Add explicit normalization allowlist cases in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/normalization-cases.json`
- [ ] T006 [P] Add the helper fixture manifest skeleton with helper ids, failure-class mappings, rejected-input stdout schema expectations, deterministic remediation fields, subprocess policy, path-boundary policy, and promotion status fields in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T007 [P] Add the Bash-reference manifest skeleton with source-checkout script paths, argv-only subprocess metadata, bounded-input flags, stdout/stderr/exit comparison modes, and comparison ids in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`

---

## Phase 2: Foundational Registry And Harness

**Purpose**: Build the shared dispatch, test harness, comparison, and safety primitives that block all helper ports.

**Independent Test**: Run the registry-only and harness-safety tests without any Bash-backed helper promotion.

- [ ] T008 [US2] Add failing shared harness tests for request envelope validation, semantic JSON comparison, exact stderr/exit comparison, drift diagnostics, rejected stdout schemas, deterministic remediation, per-class failure mappings, argv-only subprocess enforcement, bounded subprocess input, and trust-boundary path rejection in `tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py`
- [ ] T009 [US2] Implement the explicit read-only helper registry with known helper ids, operation metadata, mode checks, unknown-helper rejection, and mutation-mode rejection in `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [ ] T010 [US2] Wire helper dispatch from the runner envelope into the registry without changing existing runtime-info or preflight behavior in `speckit-pro/speckit_pro_runner/__main__.py`
- [ ] T011 [US2] Implement shared read-only helper request validation, diagnostic mapping, and repo/plugin trust-boundary path resolution in `speckit-pro/speckit_pro_runner/helpers/read_only.py`
- [ ] T012 [US2] Implement the Bash-reference comparison harness using explicit argv sequences, captured stdout/stderr, bounded input, and no shell invocation in `tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py`
- [ ] T013 [US2] Promote `helper-registry-dispatch` only after its golden registry fixtures pass and update the registry promotion record in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

**Checkpoint**: Registry dispatch, harness safety, and manifest validation are ready; Slice 1 helper ports may begin.

---

## Phase 3: Slice 1 - Prerequisite, Detection, Marker, Validation, Reviewability, And Confidence Helpers

**Purpose**: Promote Slice 1 helpers after fixture parity and Bash-reference comparison.

**Independent Test**: For each Slice 1 helper, run `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper <helper-id>` and verify golden parity, Bash-reference parity, rejected-input failure classes, stdout JSON schema expectations, stderr diagnostics, deterministic remediation, and exit-code mappings.

### `check-prerequisites`

- [ ] T014 [US1] Add accepted and rejected `check-prerequisites` fixtures with stdout schemas, stderr diagnostics, deterministic remediation, and exact nonzero exit mappings in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T015 [US1] Add source-checkout Bash-reference comparison cases for `check-prerequisites.sh` in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- [ ] T016 [US1] Port and register `check-prerequisites` read-only behavior in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [ ] T017 [US3] Mark `check-prerequisites` as `python_authoritative` only after parity passes and record normalized fields, failure mappings, subprocess policy, path-boundary policy, authoritative command, and deferred follow-up in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

### `detect-commands`

- [ ] T018 [US1] Add accepted and rejected `detect-commands` fixtures with stdout schemas, stderr diagnostics, deterministic remediation, Windows/path coverage, and exact nonzero exit mappings in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T019 [US1] Add source-checkout Bash-reference comparison cases for `detect-commands.sh` in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- [ ] T020 [US1] Port and register `detect-commands` read-only behavior in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [ ] T021 [US3] Mark `detect-commands` as `python_authoritative` only after parity passes and record normalized fields, failure mappings, subprocess policy, path-boundary policy, authoritative command, and deferred follow-up in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

### `detect-presets`

- [ ] T022 [US1] Add accepted and rejected `detect-presets` fixtures with stdout schemas, stderr diagnostics, deterministic remediation, spaces-in-paths coverage, and exact nonzero exit mappings in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T023 [US1] Add source-checkout Bash-reference comparison cases for `detect-presets.sh` in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- [ ] T024 [US1] Port and register `detect-presets` read-only behavior in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [ ] T025 [US3] Mark `detect-presets` as `python_authoritative` only after parity passes and record normalized fields, failure mappings, subprocess policy, path-boundary policy, authoritative command, and deferred follow-up in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

### `count-markers`

- [ ] T026 [US1] Add accepted and rejected `count-markers` fixtures with duplicate marker, needs-clarification marker, gap marker, critical marker, stdout schema, stderr diagnostic, deterministic remediation, and exact nonzero exit coverage in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T027 [US1] Add source-checkout Bash-reference comparison cases for `count-markers.sh` in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- [ ] T028 [US1] Port and register `count-markers` read-only behavior in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [ ] T029 [US3] Mark `count-markers` as `python_authoritative` only after parity passes and record normalized fields, failure mappings, subprocess policy, path-boundary policy, authoritative command, and deferred follow-up in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

### `validate-gate`

- [ ] T030 [US1] Add accepted and rejected `validate-gate` fixtures with gate pass/fail, usage, missing tasks/spec states, stdout schemas, stderr diagnostics, deterministic remediation, and exact nonzero exit mappings in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T031 [US1] Add source-checkout Bash-reference comparison cases for `validate-gate.sh` in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- [ ] T032 [US1] Port and register `validate-gate` read-only behavior in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [ ] T033 [US3] Mark `validate-gate` as `python_authoritative` only after parity passes and record normalized fields, failure mappings, subprocess policy, path-boundary policy, authoritative command, and deferred follow-up in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

### `reviewability-gate`

- [ ] T034 [US1] Add accepted and rejected `reviewability-gate` fixtures with pass, warn, block, unsupported path, stdout schema, stderr diagnostics, deterministic remediation, and exact nonzero exit mappings in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T035 [US1] Add source-checkout Bash-reference comparison cases for `reviewability-gate.sh` in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- [ ] T036 [US1] Port and register `reviewability-gate` read-only behavior in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [ ] T037 [US3] Mark `reviewability-gate` as `python_authoritative` only after parity passes and record normalized fields, failure mappings, subprocess policy, path-boundary policy, authoritative command, and deferred follow-up in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

### `estimate-reviewable-loc`

- [ ] T038 [US1] Add accepted and rejected `estimate-reviewable-loc` fixtures with typical, not-estimated, bad-input, stdout schema, stderr diagnostics, deterministic remediation, and exact nonzero exit mappings in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T039 [US1] Add source-checkout Bash-reference comparison cases for `estimate-reviewable-loc.sh` in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- [ ] T040 [US1] Port and register `estimate-reviewable-loc` read-only behavior in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [ ] T041 [US3] Mark `estimate-reviewable-loc` as `python_authoritative` only after parity passes and record normalized fields, failure mappings, subprocess policy, path-boundary policy, authoritative command, and deferred follow-up in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

### `resolve-confidence-mode`

- [ ] T042 [US1] Add accepted and rejected `resolve-confidence-mode` fixtures with default, explicit, invalid, stdout schema, stderr diagnostics, deterministic remediation, and exact nonzero exit mappings in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T043 [US1] Add source-checkout Bash-reference comparison cases for `resolve-confidence-mode.sh` in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- [ ] T044 [US1] Port and register `resolve-confidence-mode` read-only behavior in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [ ] T045 [US3] Mark `resolve-confidence-mode` as `python_authoritative` only after parity passes and record normalized fields, failure mappings, subprocess policy, path-boundary policy, authoritative command, and deferred follow-up in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

### `confidence-gate`

- [ ] T046 [US1] Add accepted and rejected `confidence-gate` fixtures with pass, warn, block, stdout schema, stderr diagnostics, deterministic remediation, and exact nonzero exit mappings in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T047 [US1] Add source-checkout Bash-reference comparison cases for `confidence-gate.sh` in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- [ ] T048 [US1] Port and register `confidence-gate` read-only behavior in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [ ] T049 [US3] Mark `confidence-gate` as `python_authoritative` only after parity passes and record normalized fields, failure mappings, subprocess policy, path-boundary policy, authoritative command, and deferred follow-up in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

- [ ] T050 [US1] Run the complete Slice 1 helper parity set and keep the authoritative command surface in `tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py`
- [ ] T051 [US3] Verify Slice 1 promotion evidence distinguishes Python-authoritative helpers from Bash-reference-only and out-of-scope helpers in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

**Checkpoint**: Slice 1 helpers are independently testable and promotion evidence is complete before Slice 2 starts.

---

## Phase 4: Slice 2 - Spec Index, Topology, Atomicity, Layer Planning, Workflow Contract, And PR-Packet Validation

**Purpose**: Promote Slice 2 read-only/advisory helper modes without enabling write/regenerate, marker-plan output, persistence, workflow-event upserts, PR body generation, PR emission, split state, restack, relocation, install repair, autoheal, or active Claude/Codex cutover.

**Independent Test**: For each Slice 2 helper, run `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper <helper-id>` and verify golden parity, Bash-reference parity, rejected-input coverage, and mode-boundary rejection.

### `generate-spec-index --check`

- [ ] T052 [US1] Add accepted and rejected `generate-spec-index-check` fixtures for fresh, stale, malformed, write-mode rejection, stdout schema, stderr diagnostics, deterministic remediation, and exact nonzero exit mappings in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T053 [US1] Add source-checkout Bash-reference comparison cases for `generate-spec-index.sh --check` in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- [ ] T054 [US1] Port and register only `generate-spec-index --check` read-only behavior in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [ ] T055 [US3] Mark `generate-spec-index-check` as `python_authoritative` only after parity passes and record write/regenerate mode as out of scope in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

### `o5-topology`

- [ ] T056 [US1] Add accepted and rejected `o5-topology` fixtures with valid parent, invalid topology, mixed child states, stdout schema, stderr diagnostics, deterministic remediation, and exact nonzero exit mappings in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T057 [US1] Add source-checkout Bash-reference comparison cases for `o5-topology.sh` in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- [ ] T058 [US1] Port and register `o5-topology` read-only behavior in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [ ] T059 [US3] Mark `o5-topology` as `python_authoritative` only after parity passes and record normalized fields, failure mappings, subprocess policy, path-boundary policy, authoritative command, and deferred follow-up in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

### `atomicity-route`

- [ ] T060 [US1] Add accepted and rejected `atomicity-route` fixtures with single-additive, hard-atomic, context-conflict, missing/empty tasks, stdout schema, stderr diagnostics, deterministic remediation, and exact nonzero exit mappings in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T061 [US1] Add source-checkout Bash-reference comparison cases for `atomicity-route.sh` in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- [ ] T062 [US1] Port and register `atomicity-route` read-only behavior in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [ ] T063 [US3] Mark `atomicity-route` as `python_authoritative` only after parity passes and record mutation routing as out of scope in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

### `plan-layers <feature-dir>`

- [ ] T064 [US1] Add accepted and rejected `plan-layers-feature-dir` fixtures with valid real tasks, dependency cycle, malformed task, invalid reference, missing references, missing tasks, stdout schema, stderr diagnostics, deterministic remediation, and exact nonzero exit mappings in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T065 [US1] Add source-checkout Bash-reference comparison cases for `plan-layers.sh <feature-dir>` in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- [ ] T066 [US1] Port and register only `plan-layers <feature-dir>` read-only analysis in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [ ] T067 [US3] Mark `plan-layers-feature-dir` as `python_authoritative` only after parity passes and record marker-plan output mode as out of scope in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

### `validate-pr-workflow-contract`

- [ ] T068 [US1] Add accepted and rejected `validate-pr-workflow-contract` fixtures with valid, missing, invalid, stdout schema, stderr diagnostics, deterministic remediation, and exact nonzero exit mappings in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T069 [US1] Add source-checkout Bash-reference comparison cases for `validate-pr-workflow-contract.sh` in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- [ ] T070 [US1] Port and register `validate-pr-workflow-contract` read-only behavior in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [ ] T071 [US3] Mark `validate-pr-workflow-contract` as `python_authoritative` only after parity passes and record workflow-event mutation as out of scope in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

### `validate-pr-packet` read-only validation

- [ ] T072 [US1] Add accepted and rejected `validate-pr-packet-read-only` fixtures with valid single packet, invalid missing evidence, invalid protected edit, stdout schema, stderr diagnostics, deterministic remediation, and exact nonzero exit mappings in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T073 [US1] Add source-checkout Bash-reference comparison cases for read-only `validate-pr-packet.sh` validation output, diagnostics, and exit behavior in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- [ ] T074 [US1] Port and register only `validate-pr-packet` read-only validation behavior in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py`
- [ ] T075 [US3] Mark `validate-pr-packet-read-only` as `python_authoritative` only after parity passes and record persistence, workflow-event upserts, PR body generation, PR emission, and restack as out of scope in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`

- [ ] T076 [US1] Run the complete Slice 2 helper parity set and keep the authoritative command surface in `tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py`

**Checkpoint**: Slice 2 helpers are independently testable and no write or mutation mode has been promoted.

---

## Phase 5: Handoff Evidence And Verification

**Purpose**: Verify the accepted source-checkout runner path, promotion evidence, scope boundaries, and release-gate commands without PR body generation or PR emission.

**Independent Test**: A reviewer can inspect helper promotion records, run the smoke/parity commands, and confirm zero active cutover or mutation-helper leakage.

- [ ] T077 [US3] Run the local source-checkout runtime-info smoke using `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/smoke-runtime-info-request.json`
- [ ] T078 [US3] Run the focused helper parity suite from `tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py`
- [ ] T079 [US3] Run the focused Layer 4 script gate using `tests/speckit-pro/run-all.sh`
- [ ] T080 [US3] Run the default deterministic gate using `tests/speckit-pro/run-all.sh`
- [ ] T081 [US3] Audit the implementation diff for zero active Claude/Codex skill, hook, generated payload, install, marketplace/public-doc, mutation-helper, PR-emission, split-state, restack, relocation, install repair, or autoheal cutover edits across `.claude/`, `speckit-pro/skills/`, `speckit-pro/hooks/`, `speckit-pro/codex-skills/`, `speckit-pro/codex-agents/`, `docs-site/`, and `.claude-plugin/`
- [ ] T082 [US3] Verify every in-scope and out-of-scope helper has an unambiguous promotion status, review order, known gap, Bash-reference retention note, rollback/deferred follow-up, and authoritative command in `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- [ ] T083 [US3] Prepare the orchestrator handoff evidence from `specs/xplat-005-read-only-helper-port/quickstart.md`, `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`, and `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json` without generating a PR body or emitting PR state
- [ ] T084 [US3] Validate the task artifact with `speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh G5 specs/xplat-005-read-only-helper-port` so `specs/xplat-005-read-only-helper-port/tasks.md` is checked by the gate script

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: No dependencies.
- **Phase 2**: Depends on Phase 1 directories and fixture skeletons.
- **Phase 3 / Slice 1**: Depends on Phase 2 registry, harness, path-boundary, and Bash-reference comparison primitives.
- **Phase 4 / Slice 2**: Depends on Slice 1 checkpoint so reviewers can inspect foundational helper parity before later planning and PR-packet validators.
- **Phase 5**: Depends on all intended helper promotions and evidence updates.

### Helper Promotion Order

For each helper:

1. Add golden and rejected-input fixtures in `fixture-manifest.json`.
2. Add source-checkout Bash-reference comparison cases in `bash-reference-manifest.json`.
3. Port and register the helper in `read_only.py` and `registry.py`.
4. Run the helper-specific parity command.
5. Mark the helper `python_authoritative` only after fixture parity and Bash-reference comparison pass.

### Parallel Opportunities

- T003, T004, T005, T006, and T007 can run in parallel after T002 because they seed independent fixture files.
- Helper implementation and promotion tasks are intentionally serial because they share `read_only.py`, `registry.py`, `fixture-manifest.json`, `bash-reference-manifest.json`, and the shared Python harness.
- Final smoke and gate commands can be scheduled close together by the orchestrator, but they are not marked `[P]` because they verify shared repository state.

## Implementation Strategy

### MVP First: Foundation Plus Slice 1

1. Complete Phase 1 and Phase 2.
2. Complete Slice 1 helper fixture, Bash comparison, port, and promotion tasks.
3. Stop and validate Slice 1 parity and promotion evidence before starting Slice 2.

### Incremental Delivery

1. Add each helper's failing fixtures and Bash-reference cases before porting that helper.
2. Keep the Python authoritative gate helper-by-helper; do not batch-promote helpers without accepted parity.
3. Preserve Bash helpers as temporary references through XPLAT-005.
4. Use Phase 5 evidence to hand off review without active Claude/Codex cutover or PR-emission behavior.

## Out Of Scope

- `detect-stack-manager`
- `generate-spec-index` write/regenerate mode
- `plan-layers marker-plan` output mode
- `validate-pr-packet` persistence, workflow-event upserts, PR body generation, PR emission, and restack behavior
- Split PR state, artifact relocation, install repair, autoheal, generated payload changes, active Claude Code/Codex skill or hook cutover, marketplace/public documentation claims, and full native installed-plugin UAT
