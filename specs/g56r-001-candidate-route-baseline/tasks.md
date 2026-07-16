# Tasks: G56R-001 Candidate Route Baseline

**Input**: Design documents from `specs/g56r-001-candidate-route-baseline/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: This is a planning-evidence research spike. Verification tasks prove source authority, schema validity, exact counts, cross-references, historical dispositions, traceability, scope hygiene, and repository validation.

**Reviewability**: The original implementation output was one Markdown report with 0 projected production LOC and 0 production files. The 2026-07-16 parity amendment adds exactly one shared-schema planning manifest; it does not add a runtime or platform-specific schema. Review remediation also updates process artifacts, one observability checklist artifact, and one repository test guard allowlist. If implementation touches runtime, payload, cache, fixture payload, installer, generated artifact, helper script, platform-specific/runtime schema, or version files, stop and split or re-plan before continuing.

**Organization**: Tasks are grouped by user story so each story can be reviewed independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Not used in the original task list because report edits shared one file; amendment work remains sequential to keep the report and manifest synchronized.
- **[Story]**: Which user story the task belongs to.
- Every task names the exact target path.

## Phase 1: Setup

**Purpose**: Establish the canonical report structure and scope guardrails.

- [x] T001 Create the canonical report skeleton with required sections in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T002 Add scope, non-goals, evidence authority classes, snapshot metadata, and no-runtime-change boundaries to `docs/ai/research/codex-agent-route-candidates.md`
- [x] T003 Add stable ID conventions and record-count targets for source, role, candidate, fixture, traceability, and decision records in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T004 Add stable `ProjectInputRecord` inventory for PRD, roadmap, active Codex TOMLs, route-policy skill/runner surfaces, Claude parity files, fixture inputs, payload/cache references, and generated artifacts in `docs/ai/research/codex-agent-route-candidates.md`

---

## Phase 2: Foundational

**Purpose**: Add shared structures that all user stories require.

- [x] T005 Add the stable traceability matrix records and authority-class review rules to `docs/ai/research/codex-agent-route-candidates.md`
- [x] T006 Add the completeness matrix skeleton for 9 source records, 5 effort-surface records, 16 project-input records, 12 role contracts, 12 fixture records, 24 traceability records, 4 go/no-go decisions, 3 current fixtures, 9 missing fixtures, and 0 unsupported admitted seed candidates to `docs/ai/research/codex-agent-route-candidates.md`
- [x] T007 Add the G56R-002 capability-question and stable no-go decision records to `docs/ai/research/codex-agent-route-candidates.md`
- [x] T008 Verify the changed-file scope still matches the plan's declared implementation artifact before user story work continues in `docs/ai/research/codex-agent-route-candidates.md`

**Checkpoint**: The report has all shared structures needed by the four user stories.

---

## Phase 3: User Story 1 - Freeze Official Evidence (Priority: P1)

**Goal**: Produce a dated official-source ledger so every platform claim is traceable to current official OpenAI documentation.

**Independent Test**: Review the report and confirm every platform claim has an `official_source_ledger_id`, source family, retrieval method, requested URL, canonical URL, retrieval date, durable retrieval evidence, page or section locator, short excerpt anchor, bounded source-fact extract, extract hash, invalidation trigger, and claim binding.

- [x] T009 [US1] Retrieve current official OpenAI documentation and populate 9 `OfficialSourceLedgerRecord` entries in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T010 [US1] Record source family, retrieval method, requested URL, canonical URL, page or surface, retrieval timestamp, HTTP status, response-body hash, page or section locator, short excerpt anchor, 25 bounded source-fact extracts, extract hashes, documented facts, supported surfaces, and invalidation triggers for each source in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T011 [US1] Evaluate the roadmap seed and legacy project-input models against official documentation and record documented, deprecated, withdrawn, unsupported, or undocumented status in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T012 [US1] Add source-to-claim bindings for all model, effort, custom-agent, MCP, app, configuration, non-interactive, telemetry, and prompting claims in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T013 [US1] Verify every platform claim maps to `official_documentation` or `undocumented` and no project input establishes a platform fact in `docs/ai/research/codex-agent-route-candidates.md`

**Checkpoint**: User Story 1 is independently reviewable through the official-source ledger and claim bindings.

---

## Phase 4: User Story 2 - Define Twelve Role Contracts (Priority: P1)

**Goal**: Record one complete role contract for each target role without weakening source, safety, grounding, mutation, tool, skill, MCP, output, or client-surface boundaries.

**Independent Test**: Count exactly 12 `agent_contract_id` records: 10 active Codex TOML source records and 2 Claude parity-only comparison records.

- [x] T014 [US2] Inventory the 10 active Codex TOML role sources and 2 Claude parity-role source files as `project_input` in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T015 [US2] Compute instruction and full-file SHA256 hashes for each role source and record extraction rules, encoding rules, hash source details, and complete all-role validation evidence in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T016 [US2] Write 10 active Codex `AgentContractRecord` entries with declared TOML model, effort, sandbox, mutation, client surface, source bindings, and role boundaries in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T017 [US2] Write 2 parity-only `AgentContractRecord` entries for `consensus-synthesizer` and `gate-validator` with active Codex route absence in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T018 [US2] Complete safety, grounding, mutation, tool, skill, MCP, output, representative-task, and exact-treatment boundary fields for all 12 role contracts in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T019 [US2] Verify exactly 12 unique `agent_contract_id` records and confirm parity-only records remain `project_input` comparison records in `docs/ai/research/codex-agent-route-candidates.md`

**Checkpoint**: User Story 2 is independently reviewable through the twelve role contract records.

---

## Phase 5: User Story 3 - Publish Provisional Candidate Routes (Priority: P2)

**Goal**: Publish provisional candidate records that are source-bound for later discovery and block executable model/effort tuple admission until G56R-002, without claiming availability, executability, qualification, preference, efficiency, fallback behavior, or exact treatment.

**Independent Test**: Inspect each candidate record and verify every source-bound model candidate cites official sources, every unsupported fact is explicit, blocked model/effort tuple status is recorded where required, and no preferred or fallback order is selected.

- [x] T020 [US3] Add the versioned `agent_route_candidate_manifest` and candidate-status taxonomy to `docs/ai/research/codex-agent-route-candidates.md`
- [x] T021 [US3] Create source-bound `CandidateRouteRecord` entries from frozen official-source ledger facts, exact source facts, source fact extract hashes, role instruction hashes, candidate rationale, role contracts, and blocked model/effort tuple status where G56R-002 must discover supported efforts in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T022 [US3] Record rejected, deprecated, withdrawn, undocumented, or blocked seed and legacy project-input candidates and their unsupported facts in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T023 [US3] Add explicit per-candidate effort-surface record IDs, documented or explicitly undocumented per-surface effort/default records, required capabilities, required qualification artifacts, lifecycle fields, shutdown/replacement fields, capability questions, and invalidation rules to each candidate route in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T024 [US3] Verify no candidate claims availability, executability, qualification, preference, efficiency, fallback behavior, exact treatment, or installation readiness in `docs/ai/research/codex-agent-route-candidates.md`

**Checkpoint**: User Story 3 is independently reviewable through the provisional candidate manifest and rejected-candidate records.

---

## Phase 6: User Story 4 - Hand Off Fixture And Telemetry Gaps (Priority: P2)

**Goal**: Publish exact executable-fixture and telemetry backlog records for G56R-002 and later specs without creating or running fixture payloads.

**Independent Test**: Confirm the backlog contains exactly 3 current prompt-emulation fixtures and 9 missing executable role fixtures, each with executable specification, telemetry need, success oracle, blocking dependency, and priority.

- [x] T025 [US4] Inventory the current `fixtures-codex` prompt-emulation records and Claude prompt-emulation project inputs in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T026 [US4] Write 12 `FixtureBacklogRecord` entries with status, source path, non-release evidence label, executable specification, representative input, telemetry needs, success oracle, blocking dependency, owner spec, priority, and invalidation triggers in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T027 [US4] Add G56R-002 telemetry requirements for assigned route, effective route, model, effort, parent-child attribution, loaded tools, skills, MCP, sandbox, approvals, token vector, duration, retries, terminal state, and missing-field classification in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T028 [US4] Add G56R-002 capability questions for model listing, provider capabilities, supported efforts, documented surfaces, exact treatment, MCP/app/tool access, and rejected candidates in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T029 [US4] Add the strict go/no-go matrix with stable `decision_id` records, `GO` only for complete G56R-002 capability discovery, and `NO-GO` for executable candidate set, qualification, installation, resolver behavior, and fallback policy in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T030 [US4] Verify exactly 3 current prompt-emulation records, 9 missing executable fixture records, and no new fixture payloads in `docs/ai/research/codex-agent-route-candidates.md`

**Checkpoint**: User Story 4 is independently reviewable through fixture, telemetry, capability-question, and go/no-go records.

---

## Phase 7: Polish And Verification

**Purpose**: Prove the final report satisfies acceptance criteria and repository scope.

- [x] T031 Map every functional requirement and success criterion to stable traceability records, report sections, and verification evidence in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T032 Run unresolved marker search across `specs/g56r-001-candidate-route-baseline`, `docs/ai/research/codex-agent-route-candidates.md`, and the planning manifest
- [x] T033 Run exact count review for 9 source records, 5 effort-surface records, 16 project-input records, 12 role contracts, 23 candidate route records, 12 fixture records, 24 traceability records, 4 go/no-go decisions, 3 current fixtures, 9 missing fixtures, and 0 unsupported admitted seed candidates in `docs/ai/research/codex-agent-route-candidates.md`
- [x] T034 Run changed-file review and confirm no runtime, agent, installer, payload, cache, fixture payload, generated artifact, platform-specific/runtime schema, helper script, or version file changed; the shared planning schema/manifest pair is the sole packaging amendment
- [x] T035 Run `git diff --check` and record the result for `docs/ai/research/codex-agent-route-candidates.md`
- [x] T036 Run `python3 tests/speckit-pro/run-all.py --layer 1` and record the result for `docs/ai/research/codex-agent-route-candidates.md`
- [x] T037 Run `python3 tests/speckit-pro/run-all.py` and record the result for `docs/ai/research/codex-agent-route-candidates.md`
- [x] T038 Prepare PR review packet source covering what changed, why, non-goals, review order, scope budget, traceability, verification, known gaps, and rollback or flag notes in `docs/ai/research/codex-agent-route-candidates.md`

---

## Phase 8: 2026-07-16 Evidence-Parity Amendment

**Purpose**: Bring G56R-001 into structural parity with CAR-001 using current
official OpenAI documentation while preserving the completed v0.1 record.

- [x] T039 Adopt `docs/ai/specs/agent-routing-parity-contract.md` and `docs/ai/research/agent-route-candidate-manifest.schema.json` from the shared evidence foundation PR #362
- [x] T040 Retrieve and hash 21 current allowlisted official OpenAI documentation sources spanning every shared research-matrix family
- [x] T041 Add `docs/ai/research/codex-agent-route-candidate-manifest.json` with schema version `2.0.0`, 12 agent contracts, 23 candidates, and explicit dispositions for all 25 legacy source facts
- [x] T042 Amend the canonical report, design decision, workflow, spec, plan, research, data model, contract, quickstart, checklist, retrospective, and verification records without rewriting historical execution evidence
- [x] T043 Run `python3 tests/speckit-pro/unit/test-agent-route-research-parity.py` and confirm schema, authority-domain, cross-reference, legacy-disposition, and CAR/G56R structural-parity checks pass
- [ ] T044 Run diff hygiene, Layer 1, full repository validation, docs reference validation, then publish PR #360 as a clean stack on PR #362

---

## Dependencies And Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup.
- **US1 Freeze Official Evidence (Phase 3)**: Depends on Foundational and blocks candidate admission.
- **US2 Define Twelve Role Contracts (Phase 4)**: Depends on Foundational and can be reviewed after US1 source rules are established.
- **US3 Publish Provisional Candidate Routes (Phase 5)**: Depends on US1 and US2.
- **US4 Hand Off Fixture And Telemetry Gaps (Phase 6)**: Depends on US2 and benefits from US3 candidate status.
- **Polish And Verification (Phase 7)**: Depends on US1 through US4.

### User Story Dependencies

- **User Story 1 (P1)**: Required before candidate records can be source-bound or admitted.
- **User Story 2 (P1)**: Required before candidate and fixture records can bind role contracts.
- **User Story 3 (P2)**: Depends on US1 official source ledger and US2 role contracts.
- **User Story 4 (P2)**: Depends on US2 role contracts and should reflect US3 candidate status.

### Parallel Opportunities

No tasks are marked `[P]` because the implementation has a single shared report file. Read-only source review can be prepared in parallel outside the task list, but report edits should remain sequential to avoid cross-reference drift.

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 official-source ledger.
3. Stop and validate that platform claims have official source bindings before adding role, candidate, or fixture records.

### Incremental Delivery

1. Complete US1 source ledger and traceability.
2. Complete US2 role contracts.
3. Complete US3 provisional candidates.
4. Complete US4 fixture, telemetry, capability, and go/no-go handoff.
5. Complete polish and verification.

### Scope Guard

If any task requires runtime probing, route qualification, fallback ordering,
installer behavior, payload changes, cache proof changes, generated artifacts,
fixture payloads, helper scripts, platform-specific/runtime schema files, or
version edits, stop and return to planning. The shared planning schema and its
single G56R manifest are explicitly allowed by the parity amendment.
