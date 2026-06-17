# Tasks: TACD-001 Platform Mechanics Spike

**Input**: Design documents from `specs/tacd-001-platform-mechanics-spike/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, and `docs/ai/specs/.process/TACD-001-design-concept.md`

**Tests**: TACD-001 is a research spike. Include verification tasks for report completeness, probe sanitization, source citation review, and no-behavior-change scope review. Do not add final TACD-004 enforcement tests or functional eval updates.

**Reviewability**: Preserve the spec budget: one canonical report in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`, no production files, no active runtime guidance edits, no prerequisite behavior edits, no docs messaging edits, no generated payload semantic edits, and no edits to `CLAUDE.md` or `.claude` command surfaces.

**Organization**: Tasks are grouped by the TACD-001 research phases requested in the workflow while preserving user-story traceability.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel only when the task writes a separate report section or records independent appendix evidence.
- **[Story]**: Maps to the TACD-001 user stories from `spec.md`.
- Include exact file paths in descriptions.

## Phase 1: Setup and Audit Inventory Skeleton

**Purpose**: Create the report shell, inventory plan, and guardrails before any evidence classification begins.

- [x] T001 Create the report skeleton with required sections in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T002 Record TACD-001 scope, non-goals, and design-concept source reference in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T003 Add the confidence rubric and evidence-state definitions from `specs/tacd-001-platform-mechanics-spike/spec.md` to `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T004 Add the local source inventory command plan from `specs/tacd-001-platform-mechanics-spike/plan.md` to `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T005 Add a no-behavior-change guardrail checklist covering `CLAUDE.md`, `.claude/`, active guidance, prerequisite behavior, docs messaging, generated payload semantics, and final enforcement tests in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`

**Checkpoint**: The report can accept evidence without expanding beyond the TACD-001 spike boundary.

---

## Phase 2: User Story 1 - Runtime-Surface Audit and Mechanics Evidence (Priority: P1)

**Goal**: Audit Claude Code and Codex named-tool references and mechanics evidence for installed tools, MCP/app connectors, skills/plugins, and repo-local helpers.

**Independent Test**: Review the Claude Code and Codex sections of `docs/ai/research/tool-agnostic-capability-discovery-spike.md` and confirm every audited finding includes source path, line context, classification, and rationale.

### Phase 2a: Claude Code Evidence

- [x] T006 [P] [US1] Inventory Claude agent named-tool references and active guidance in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T007 [P] [US1] Inventory Claude skill, reference, prerequisite-script, and plugin-limitation named-tool references in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T008 [US1] Classify Claude generated payload duplicates from `dist/claude/speckit-pro/` in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T009 [US1] Fill Claude Code runtime-by-capability matrix cells with evidence state, confidence, confidence rationale, and absent-capability disposition in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T010 [US1] Add sanitized Claude Code probe appendix entries for mechanics that local source inspection cannot prove in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`

### Phase 3: Codex Evidence

- [x] T011 [P] [US1] Inventory Codex agent and skill named-tool references in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T012 [P] [US1] Inventory Codex dependency metadata, generated payload duplicates, and eval expectations in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T013 [US1] Classify Codex runtime/dependency metadata separately from named-tool prose preference in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T014 [US1] Fill Codex runtime-by-capability matrix cells with evidence state, confidence, confidence rationale, and absent-capability disposition in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T015 [US1] Add sanitized Codex probe appendix entries for mechanics that local source inspection cannot prove in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`

**Checkpoint**: Runtime audit and mechanics evidence are independently reviewable. Claude Code and Codex evidence retain separate Phase 2a and Phase 3 subsections while sharing the single parser-valid US1 marker.

---

## Phase 4: User Story 3 - Active-vs-Historical Allowlist Recommendation (Priority: P3)

**Goal**: Define the category set TACD-004 can later enforce without over-banning historical, provenance, generated duplicate, or fixture-only references.

**Independent Test**: Use the category table in `docs/ai/research/tool-agnostic-capability-discovery-spike.md` to draft a deterministic allowlist and confirm each category has allowed, blocked, or review status.

### Implementation for User Story 3

- [x] T016 [US3] Create the allowlist category table with allowed status, description, example surfaces, TACD owner, and false-positive guard in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T017 [US3] Map audited named-tool findings into active guidance, metadata, prerequisite messaging, eval expectation, generated duplicate, historical/provenance, fixture-only, ambiguous, or out-of-scope categories in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T018 [US3] Document TACD-004 deterministic-check recommendations without adding enforcement tests in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T019 [US3] Document TACD-004 functional eval-plan scenarios with observable behavior, required evidence, and failure signals for Claude Code and Codex in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`

**Checkpoint**: TACD-004 has a report-backed category and eval-plan handoff, but no enforcement files are changed.

---

## Phase 5: User Story 2 - Directive-Home Recommendation and TACD-002/TACD-003/TACD-004 Handoff (Priority: P2)

**Goal**: Recommend the directive home only after audit evidence, mechanics evidence, and verification inputs exist.

**Independent Test**: Review the recommendation section in `docs/ai/research/tool-agnostic-capability-discovery-spike.md` and verify it explains Claude Code and Codex mechanics, proof bar, pass/fail rationale, and fallback path.

### Implementation for User Story 2

- [x] T020 [US2] Summarize static pointer coverage requirements for Claude Code and Codex in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T021 [US2] Summarize pointer target resolution and approved runtime-specific equivalent rules in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T022 [US2] Verify report evidence from T006-T019 before selecting shared reference with pointers or runtime-specific equivalents in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T023 [US2] Write the directive-home recommendation with pass/fail rationale and fallback plan in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T024 [US2] Record TACD-002, TACD-003, and TACD-004 downstream handoffs with scope, inputs, non-goals, and validation needed in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`

**Checkpoint**: The directive-home recommendation is evidence-backed and ready for TACD-002 planning.

---

## Phase 6: Polish - Verification, Source Citation Review, and No-Behavior-Change Scope Review

**Purpose**: Prove the report is complete, sanitized, cited, and scoped to TACD-001 only.

- [x] T025 Run required section check from `specs/tacd-001-platform-mechanics-spike/quickstart.md` and record the result in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T026 Run probe sanitization review from `specs/tacd-001-platform-mechanics-spike/quickstart.md` and record the result in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T027 Review every source citation for path, line context, classification, and rationale completeness in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T028 Run marker and G3 checks for `specs/tacd-001-platform-mechanics-spike` and record the result in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T029 Run `git diff --name-only` scope review and confirm no active runtime guidance, prerequisite behavior, docs messaging, generated payload semantics, final enforcement tests, `CLAUDE.md`, or `.claude` command surfaces changed in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- [x] T030 Generate the PR review packet notes covering review order, scope budget, traceability, verification evidence, known gaps, and rollback/flag notes in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`

**Checkpoint**: TACD-001 is ready for implementation review as a report-only spike.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: No dependencies; creates the report skeleton and guardrails.
- **Phase 2**: Depends on Phase 1; Claude Code and Codex audit/mechanics evidence. Runtime subsections preserve the requested Phase 2a Claude Code and Phase 3 Codex work while sharing the single US1 marker.
- **Phase 4**: Depends on Phase 2; categories require audited findings from both runtimes.
- **Phase 5**: Depends on Phases 2 and 4; directive-home recommendation must not be final until mechanics evidence and allowlist recommendations are available.
- **Phase 6**: Depends on Phases 1-5; verifies report completeness, citation quality, sanitization, and no-behavior-change scope.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Phase 1; split into Claude Code and Codex audit subsections for independent review within the single US1 marker.
- **User Story 2 (P2)**: Starts after audit evidence and category recommendations exist; no dependency on implementation changes.
- **User Story 3 (P3)**: Starts after audit evidence exists; provides TACD-004 category and eval-plan inputs.

### Within Each Story

- Inventory before classification.
- Classification before recommendation.
- Mechanics evidence before directive-home recommendation.
- Verification before finalizing the report.

---

## Parallel Opportunities

- T006 and T007 can run in parallel after T001-T005 because they update separate Claude report sections.
- T011 and T012 can run in parallel after T001-T005 because they update separate Codex report sections.
- Claude Code and Codex evidence subsections can run in parallel after Phase 1 if contributors reserve separate report sections.
- T018 and T019 can run in parallel after T016-T017 because deterministic-check recommendations and functional eval-plan recommendations are separate report sections.

## Parallel Example: Audit Sections

```text
Task: "Inventory Claude agent named-tool references and active guidance in docs/ai/research/tool-agnostic-capability-discovery-spike.md"
Task: "Inventory Codex agent and skill named-tool references in docs/ai/research/tool-agnostic-capability-discovery-spike.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup and report skeleton.
2. Complete Phase 2a Claude Code and Phase 3 Codex audit/mechanics evidence within the US1 marker.
3. Stop and validate that every audited finding has source path, line context, classification, and rationale.

### Incremental Delivery

1. Complete audit inventory and mechanics evidence for both runtimes.
2. Add active-vs-historical allowlist recommendations.
3. Add directive-home recommendation and downstream handoffs.
4. Complete verification and no-behavior-change scope review.

### Scope Guard

- Do not implement TACD-002 agent guidance changes.
- Do not implement TACD-003 prerequisite or docs messaging changes.
- Do not implement TACD-004 enforcement tests or functional eval updates.
- Do not edit active runtime guidance, prerequisite behavior, generated payload semantics, `CLAUDE.md`, or `.claude` command surfaces.
- Keep probes as sanitized appendix evidence in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`.
