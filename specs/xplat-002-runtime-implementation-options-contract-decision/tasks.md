# Tasks: Runtime Implementation Options and Contract Decision

**Input**: Design documents from `specs/xplat-002-runtime-implementation-options-contract-decision/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/speckit-pro-runner-contract.md`, `quickstart.md`, `docs/ai/specs/.process/XPLAT-002-design-concept.md`

**Tests**: Validation tasks are included for marker drift, spec-map freshness, diff hygiene, and the relevant deterministic shell suite. No runner implementation tests are added because XPLAT-002 is a decision spike.

**Organization**: Tasks are grouped by user story so the candidate comparison, selected contract, and reviewer handoff are independently reviewable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks.
- **[Story]**: Which user story the task belongs to.
- Every task includes an exact file path or command output target.

## Phase 1: Setup (Shared Decision Spike Structure)

**Purpose**: Prepare bounded docs/process and probe-evidence artifacts without changing active runtime surfaces.

- [x] T001 Create the decision record shell in `specs/xplat-002-runtime-implementation-options-contract-decision/runtime-decision.md` using `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/speckit-pro-runner-contract.md`, `quickstart.md`, and `docs/ai/specs/.process/XPLAT-002-design-concept.md`
- [x] T002 [P] Create the JavaScript/TypeScript evidence record in `specs/xplat-002-runtime-implementation-options-contract-decision/evidence/javascript-typescript.md`
- [x] T003 [P] Create the Python evidence record in `specs/xplat-002-runtime-implementation-options-contract-decision/evidence/python.md`
- [x] T004 [P] Create the small per-platform binary evidence record in `specs/xplat-002-runtime-implementation-options-contract-decision/evidence/small-per-platform-binary.md`
- [x] T005 [P] Create the downstream handoff record in `specs/xplat-002-runtime-implementation-options-contract-decision/handoff.md`

---

## Phase 2: Foundational (Shared Rubric, Scope, and Probe Rules)

**Purpose**: Establish the common evaluation baseline before any user story is finalized.

**CRITICAL**: No user story can be completed until the shared rubric, evidence standard, and scope boundary are recorded.

- [x] T006 Extract the XPLAT-001 must-have gates and weighted criteria from `docs/ai/research/cross-platform-runtime-inventory.md` into `specs/xplat-002-runtime-implementation-options-contract-decision/runtime-decision.md`
- [x] T007 Record the no-runner, no-helper-port, no-active-invocation-change, no-generated-payload-cutover, and no-public-support-claim boundaries in `specs/xplat-002-runtime-implementation-options-contract-decision/runtime-decision.md`
- [x] T008 Define the required non-mutating probe categories and evidence-gap fallback fields in `specs/xplat-002-runtime-implementation-options-contract-decision/evidence/javascript-typescript.md`, `specs/xplat-002-runtime-implementation-options-contract-decision/evidence/python.md`, and `specs/xplat-002-runtime-implementation-options-contract-decision/evidence/small-per-platform-binary.md`
- [x] T009 Record the accepted reviewability warning and one-spike split decision in `specs/xplat-002-runtime-implementation-options-contract-decision/runtime-decision.md`

**Checkpoint**: Shared decision rules are ready and candidate work can proceed in parallel.

---

## Phase 3: User Story 1 - Compare Runtime Candidates (Priority: P1) MVP

**Goal**: Maintainers can compare JavaScript/TypeScript, Python, and small per-platform binary runner candidates against the same XPLAT-001 rubric using grounded documentation and lightweight probe evidence.

**Independent Test**: Review `runtime-decision.md` and the three files under `evidence/` and confirm all candidate families are evaluated against the same gates, weights, documentation standard, probe expectations, and evidence-gap rules.

### Implementation for User Story 1

- [x] T010 [P] [US1] Record official/runtime documentation evidence, repo-local source evidence, installed-cache probe results or host-specific evidence gaps, gate results, weighted scores, and supply-chain implications for JavaScript/TypeScript in `specs/xplat-002-runtime-implementation-options-contract-decision/evidence/javascript-typescript.md`
- [x] T011 [P] [US1] Record official/runtime documentation evidence, repo-local source evidence, installed-cache probe results or host-specific evidence gaps, gate results, weighted scores, and supply-chain implications for Python in `specs/xplat-002-runtime-implementation-options-contract-decision/evidence/python.md`
- [x] T012 [P] [US1] Record official/runtime documentation evidence, repo-local source evidence, installed-cache probe results or host-specific evidence gaps, gate results, weighted scores, and supply-chain implications for small per-platform binaries in `specs/xplat-002-runtime-implementation-options-contract-decision/evidence/small-per-platform-binary.md`
- [x] T013 [US1] Synthesize the gate-first weighted comparison across all three candidates in `specs/xplat-002-runtime-implementation-options-contract-decision/runtime-decision.md`
- [x] T014 [US1] Record documentation/probe conflicts, unrun probes, and evidence gaps without scoring evidence gaps as installed-cache probe passes in `specs/xplat-002-runtime-implementation-options-contract-decision/runtime-decision.md`

**Checkpoint**: Candidate comparison is complete and reviewable without selecting by unstated preference.

---

## Phase 4: User Story 2 - Read the Selected Command Contract (Priority: P2)

**Goal**: Implementers of XPLAT-004 through XPLAT-007 can read one selected runtime decision and one precise `speckit-pro-runner` command contract.

**Independent Test**: Review `runtime-decision.md` and `contracts/speckit-pro-runner-contract.md` and confirm exactly one runtime is selected and the contract defines entrypoint, dispatch, JSON input/output, stderr diagnostics, exit codes, paths, subprocesses, prerequisites, and runtime version reporting.

### Implementation for User Story 2

- [x] T015 [US2] Select exactly one canonical runtime model and record why it is viable without post-cache dependency setup while deferring actual installed-cache invocation proof to XPLAT-004 in `specs/xplat-002-runtime-implementation-options-contract-decision/runtime-decision.md`
- [x] T016 [US2] Apply the objective close-candidate definition and install-reliability tie-breaker order in `specs/xplat-002-runtime-implementation-options-contract-decision/runtime-decision.md`
- [x] T017 [US2] Update `specs/xplat-002-runtime-implementation-options-contract-decision/contracts/speckit-pro-runner-contract.md` with the selected runtime, default `speckit-pro-runner` entrypoint, and payload-relative `scripts/speckit-pro-runner` path without implementing the runner
- [x] T018 [US2] Finalize the JSON request and response envelope, line-delimited JSON stderr diagnostics, shared exit-code map, path value rules, shell-disabled subprocess rules, prerequisite reporting, and runtime-info or preflight requirements in `specs/xplat-002-runtime-implementation-options-contract-decision/contracts/speckit-pro-runner-contract.md`
- [x] T019 [US2] Record XPLAT-004 fixture parity expectations for success, invalid JSON, missing required field, path with spaces, Windows separators, missing prerequisite, subprocess nonzero, subprocess timeout, stderr-only failure, runtime-info or preflight, and one read-only legacy-helper comparison in `specs/xplat-002-runtime-implementation-options-contract-decision/contracts/speckit-pro-runner-contract.md`

**Checkpoint**: The selected contract is build-ready for XPLAT-004 but contains no runner implementation.

---

## Phase 5: User Story 3 - Review Rejections and Handoff (Priority: P3)

**Goal**: Reviewers can trace rejected options, tie-breaker rationale, evidence gaps, and downstream responsibilities without hidden public support-claim changes.

**Independent Test**: Review `runtime-decision.md`, `handoff.md`, and `quickstart.md` and confirm each rejection and follow-up item traces to a criterion, tie-breaker, evidence gap, or downstream spec responsibility.

### Implementation for User Story 3

- [x] T020 [US3] Record rejection rationale for each non-selected candidate, including gate failures, weighted criteria, evidence gaps, documentation/probe conflicts, or tie-breaker results, in `specs/xplat-002-runtime-implementation-options-contract-decision/runtime-decision.md`
- [x] T021 [US3] Record the selected and rejected candidate supply-chain implication matrix for XPLAT-003, without selecting controls, in `specs/xplat-002-runtime-implementation-options-contract-decision/handoff.md`
- [x] T022 [US3] Record the XPLAT-004 implementation input bundle with XPLAT-001 row IDs, owner buckets, active invocation modes, runner helper IDs, operations, modes, fixture expectations, adapter records, and explicit exclusions in `specs/xplat-002-runtime-implementation-options-contract-decision/handoff.md`
- [x] T023 [US3] Record compatibility adapter records only as temporary migration evidence with owner-first adapter IDs, explicit `owner_spec`, `removal_spec`, and removal conditions in `specs/xplat-002-runtime-implementation-options-contract-decision/handoff.md`
- [x] T024 [US3] Update `specs/xplat-002-runtime-implementation-options-contract-decision/quickstart.md` with the final review order, evidence review checklist, validation commands, known evidence gaps, and no-public-claim boundary check
- [x] T025 [US3] Update `specs/xplat-002-runtime-implementation-options-contract-decision/SPEC-MOC.md` to link the decision record, evidence files, contract, handoff, and quickstart without adding public support claims

**Checkpoint**: Reviewers have the selected decision, rejected rationale, downstream handoff, and validation path.

---

## Phase 6: Polish & Cross-Cutting Validation

**Purpose**: Prove the decision spike stayed bounded, reviewable, and clean.

- [x] T026 Run `bash speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh gaps specs/xplat-002-runtime-implementation-options-contract-decision` and record the zero-marker result in `specs/xplat-002-runtime-implementation-options-contract-decision/quickstart.md`
- [x] T027 Run `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"` and record the spec-map freshness result in `specs/xplat-002-runtime-implementation-options-contract-decision/quickstart.md`
- [x] T028 Run `bash speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh diff origin/main...HEAD` and record the final diff reviewability status, warnings, blockers, reviewable LOC, production file count, total file count, and primary surfaces in `specs/xplat-002-runtime-implementation-options-contract-decision/quickstart.md`
- [x] T029 Run `git diff --name-only` and confirm `README.md`, `docs-site/`, marketplace metadata, changelog, release notes, active installed invocation paths, and broad generated payloads are not changed; record the review in `specs/xplat-002-runtime-implementation-options-contract-decision/quickstart.md`
- [x] T030 Run `git diff --check` and record the diff hygiene result in `specs/xplat-002-runtime-implementation-options-contract-decision/quickstart.md`
- [x] T031 Run `bash tests/speckit-pro/run-all.sh --layer 1` as the relevant structural shell suite and record the result in `specs/xplat-002-runtime-implementation-options-contract-decision/quickstart.md`
- [x] T032 If source, generator scripts, or durable probe scripts changed unexpectedly, either return scope to docs/process only or run `bash tests/speckit-pro/run-all.sh` and record the result in `specs/xplat-002-runtime-implementation-options-contract-decision/quickstart.md`
- [x] T033 Prepare the PR review packet content in `specs/xplat-002-runtime-implementation-options-contract-decision/handoff.md` with what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion.
- **User Story 2 (Phase 4)**: Depends on User Story 1 comparison evidence.
- **User Story 3 (Phase 5)**: Depends on User Story 2 selected runtime and contract.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 Compare Runtime Candidates (P1)**: MVP. Can complete once the rubric and evidence files exist.
- **US2 Read the Selected Command Contract (P2)**: Depends on US1 because the selected runtime must come from the comparison.
- **US3 Review Rejections and Handoff (P3)**: Depends on US2 because handoff must name the selected runtime and rejected options.

### Parallel Opportunities

- T002, T003, T004, and T005 can run in parallel after T001 because they touch different files.
- T010, T011, and T012 can run in parallel after Phase 2 because each candidate evidence record has its own file.
- Validation tasks T026 through T030 are ordered for readable evidence capture, but T027 and T028 can be inspected independently before final recording in `quickstart.md`.

---

## Parallel Example: User Story 1

```bash
Task: "Record JavaScript/TypeScript evidence in specs/xplat-002-runtime-implementation-options-contract-decision/evidence/javascript-typescript.md"
Task: "Record Python evidence in specs/xplat-002-runtime-implementation-options-contract-decision/evidence/python.md"
Task: "Record small per-platform binary evidence in specs/xplat-002-runtime-implementation-options-contract-decision/evidence/small-per-platform-binary.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 candidate evidence and comparison.
3. Stop and validate that all three candidates use the same rubric and evidence standard.

### Incremental Delivery

1. Add US1 candidate comparison.
2. Add US2 selected runtime and command contract.
3. Add US3 rejections, XPLAT-003/XPLAT-004 handoff, and review packet.
4. Run Phase 6 validation and record results.

### Scope Guardrails

- Do not port helpers.
- Do not implement `speckit-pro-runner`.
- Do not alter active installed invocation paths.
- Do not rebuild broad generated payloads.
- Do not change public native-platform support claims.
- Preserve the setup Q&A decisions: all three candidates evaluated, docs plus probes, one contract, JSON envelope, no install step, install reliability tie-breaker, and one spike.
