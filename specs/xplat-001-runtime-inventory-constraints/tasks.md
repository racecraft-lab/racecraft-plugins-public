# Tasks: Runtime Inventory and Constraints

**Input**: Design documents from `specs/xplat-001-runtime-inventory-constraints/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `checklists/*.md`, `docs/ai/specs/.process/XPLAT-001-workflow.md`

**Tests**: No runtime tests are requested for XPLAT-001. Verification is static and source-traceable.

**Reviewability**: Preserve the accepted `speckit-pro-reviewability` warning. Keep XPLAT-001 as one report-focused docs/process spike unless implementation expands past the recorded budget or adds runtime behavior.

**Organization**: Tasks are grouped by foundation, user story, and polish so each user story can be reviewed independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches an independent report section, roadmap note, or validation evidence path
- **[Story]**: User story label from `spec.md`
- **File paths**: Every task names the target file or evidence path

---

## Phase 1: Setup and Foundation

**Purpose**: Establish the durable report target, report outline, scan command set, row schema, and owner buckets before story work starts.

- [x] T001 Create the report skeleton with scope, non-goals, review order, and handoff sections in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T002 Record the whole-repo tracked-text scan boundary and explicit exclusion rules in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T003 Record the accepted reviewability warning, split decision, and no-runtime-change constraint in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T004 Define the reproducible scan command set for Bash, `.sh`, `jq`, shell quoting, Unix paths, `chmod`, and line-ending assumptions in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T005 Define the inventory row schema with required fields from `data-model.md` in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T006 Define allowed `classification`, `active_runtime_status`, `owner_bucket`, and `follow_up_spec` values in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T007 Define aggregation and match-summary rules that preserve scan-command traceability, match counts, ownership, proof state, and rationale in `docs/ai/research/cross-platform-runtime-inventory.md`

**Checkpoint**: Foundation ready. User story work can begin after the report outline and schema are in place.

---

## Phase 2: User Story 1 - Review Runtime Inventory (Priority: P1)

**Goal**: A maintainer can review one Markdown inventory report and understand every whole-repo Bash or Unix-runtime assumption by category, active-runtime proof state, and owner bucket.

**Independent Test**: A reviewer can rerun the documented scan commands, compare results to the report, and verify that every represented or excluded finding has evidence, runtime relevance, owner bucket, follow-up spec, active runtime status, and classification rationale.

### Implementation for User Story 1

- [x] T008 [US1] Run the tracked-text universe command and record the file-count scope summary in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T009 [US1] Run each recorded scan command and capture the result-count summary by pattern family in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T010 [P] [US1] Classify installed source references from `speckit-pro/skills/`, `speckit-pro/codex-skills/`, `speckit-pro/agents/`, `speckit-pro/codex-agents/`, `speckit-pro/hooks/`, `speckit-pro/codex-hooks.json`, and `speckit-pro/scripts/` in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T011 [P] [US1] Classify generated payload references from `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/` in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T012 [P] [US1] Classify public documentation claims from `docs-site/src/content/docs/`, `speckit-pro/README.md`, and marketplace metadata in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T013 [P] [US1] Classify tests, fixtures, expected outputs, and historical/archive references from `tests/`, `specs/`, and `.specify/memory/` in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T014 [US1] Add static caller-to-callee invocation traces for every `proven-active-runtime` row in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T015 [US1] Document evidence gaps for every `unproven-active-runtime` row in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T016 [US1] Split mixed-mode helper findings by traced invocation mode and assign row-level owner buckets in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T017 [US1] Add explicit exclusion rows and `exclusion_or_exception_detail` coverage for non-text, binary, untracked, vendor cache, other excluded inputs, and any `follow-up-exception` rows, including reason, evidence gap, expiry or removal condition, and named follow-up decision where applicable in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T018 [US1] Reconcile summary counts by `classification`, `active_runtime_status`, `owner_bucket`, and `follow_up_spec` in `docs/ai/research/cross-platform-runtime-inventory.md`

**Checkpoint**: User Story 1 is independently reviewable when the inventory table and summary counts reconcile to the recorded scan results.

---

## Phase 3: User Story 2 - Use Runtime Evaluation Rubric (Priority: P2)

**Goal**: A runtime decision-maker can use a weighted runtime evaluation rubric for XPLAT-002 without XPLAT-001 choosing a runtime.

**Independent Test**: A reviewer can inspect the runtime rubric and confirm it includes must-have gates, criteria weights totaling 100, and candidate evidence targets without scores, rankings, sample scoring, or selection.

### Implementation for User Story 2

- [x] T019 [P] [US2] Add runtime must-have gates for installed-cache invocation, native platform behavior, structured filesystem, path, JSON, subprocess, stdout, stderr, exit-code behavior, packaging, and update path in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T020 [P] [US2] Add runtime weighted criteria totaling 100 for native platform behavior, installed-cache invocation, dependency footprint, packaging, offline behavior, diagnostics, maintainability, and compatibility adapters in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T021 [US2] Add candidate evidence targets for XPLAT-002 without candidate scores, ranking, sample scoring, or winner selection in `docs/ai/research/cross-platform-runtime-inventory.md`

**Checkpoint**: User Story 2 is independently reviewable when the runtime rubric is complete and remains non-scoring.

---

## Phase 4: User Story 3 - Use Supply-Chain Evaluation Rubric (Priority: P3)

**Goal**: A security/trust decision-maker can use a weighted supply-chain evaluation rubric for XPLAT-003 without XPLAT-001 choosing a security model or control set.

**Independent Test**: A reviewer can inspect the supply-chain rubric and confirm it includes must-have gates, criteria weights totaling 100, artifact/control evidence targets, and first-release versus deferred-hardening boundaries without selecting controls.

### Implementation for User Story 3

- [x] T022 [P] [US3] Add supply-chain must-have gates for maintainer verification, consumer-local verification, truthful guarantees, generated payload integrity, and provenance evidence in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T023 [P] [US3] Add supply-chain weighted criteria totaling 100 for dependency policy, lockfiles, generated payload integrity, vulnerability scanning, provenance, checksums/signatures, SBOMs, consumer-local verification, and release documentation truthfulness in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T024 [US3] Add artifact and control evidence targets for XPLAT-003 with `first-release-gate-question`, `deferred-hardening-evidence`, or `not-claimed-guarantee` boundaries in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T025 [US3] Verify the supply-chain section does not select a required security model or mandatory control set in `docs/ai/research/cross-platform-runtime-inventory.md`

**Checkpoint**: User Story 3 is independently reviewable when the supply-chain rubric is complete and remains non-selecting.

---

## Phase 5: Polish and Cross-Cutting Concerns

**Purpose**: Static verification, spec-map checks, roadmap handoff, and PR review packet evidence.

- [x] T026 [P] Re-run every scan command recorded in the report and update coverage reconciliation notes in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T027 [P] Review every `proven-active-runtime` row for caller-to-callee trace evidence and update verification notes in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T028 [P] Review docs-only, generated payload, tests/fixtures, archive, and repository-only rows for false active-runtime promotion and update verification notes in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T029 Run `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"` and record the spec-map check result in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T030 Run `git diff --check` and record the diff hygiene result in `docs/ai/research/cross-platform-runtime-inventory.md`
- [x] T031 Update XPLAT-001 progress, handoff notes, and deferred follow-up specs in `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
- [x] T032 Add PR review packet evidence covering what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback notes in `docs/ai/research/cross-platform-runtime-inventory.md`

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup and Foundation (Phase 1)**: No dependencies.
- **User Story 1 (Phase 2)**: Depends on Phase 1 because classification requires the scan commands, row schema, and owner buckets.
- **User Story 2 (Phase 3)**: Depends on Phase 1 and can proceed after the report outline is stable.
- **User Story 3 (Phase 4)**: Depends on Phase 1 and can proceed after the report outline is stable.
- **Polish (Phase 5)**: Depends on all desired user story sections being complete.

### User Story Dependencies

- **US1 (P1)**: Required MVP. No dependency on US2 or US3.
- **US2 (P2)**: Independent rubric section after foundation; may run alongside US1 classification work if report sections are coordinated.
- **US3 (P3)**: Independent rubric section after foundation; may run alongside US2.

### Parallel Opportunities

- T010, T011, T012, and T013 can run in parallel because they classify distinct source categories.
- T019 and T020 can run in parallel because they fill distinct runtime rubric subsections.
- T022 and T023 can run in parallel because they fill distinct supply-chain rubric subsections.
- T026, T027, and T028 can run in parallel after all report sections exist because they validate distinct evidence dimensions.

---

## Parallel Example: User Story 1

```text
Task: "T010 [P] [US1] Classify installed source references from installed plugin surfaces in docs/ai/research/cross-platform-runtime-inventory.md"
Task: "T011 [P] [US1] Classify generated payload references from dist payloads in docs/ai/research/cross-platform-runtime-inventory.md"
Task: "T012 [P] [US1] Classify public documentation claims in docs/ai/research/cross-platform-runtime-inventory.md"
Task: "T013 [P] [US1] Classify tests, fixtures, expected outputs, and historical/archive references in docs/ai/research/cross-platform-runtime-inventory.md"
```

---

## Parallel Example: User Story 2

```text
Task: "T019 [P] [US2] Add runtime must-have gates in docs/ai/research/cross-platform-runtime-inventory.md"
Task: "T020 [P] [US2] Add runtime weighted criteria totaling 100 in docs/ai/research/cross-platform-runtime-inventory.md"
```

---

## Parallel Example: User Story 3

```text
Task: "T022 [P] [US3] Add supply-chain must-have gates in docs/ai/research/cross-platform-runtime-inventory.md"
Task: "T023 [P] [US3] Add supply-chain weighted criteria totaling 100 in docs/ai/research/cross-platform-runtime-inventory.md"
```

---

## Implementation Strategy

### MVP First: User Story 1

1. Complete Phase 1 to establish the report schema and scan commands.
2. Complete Phase 2 to produce the whole-repo inventory and classification table.
3. Stop and validate the inventory independently against the recorded scan commands.

### Incremental Delivery

1. Add US1 inventory coverage and summary counts.
2. Add US2 runtime rubric and XPLAT-002 candidate evidence targets.
3. Add US3 supply-chain rubric and XPLAT-003 artifact/control evidence targets.
4. Complete polish with static verification, roadmap handoff, and PR packet evidence.

### Out-of-Scope Guard

Do not add tasks that port helpers to a replacement runtime, modify active installed Claude or Codex invocation paths, perform broad `dist/` rebuilds, run native platform probes, score candidates, rank candidates, select a runtime, or select a security model. A post-PR review remediation may synchronize generated payload copies of an existing helper fix.
