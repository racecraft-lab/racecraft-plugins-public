# Tasks: TACD-002 Capability Discovery Directive and Agent Updates

**Input**: Design documents from `specs/tacd-002-capability-discovery-directive-and-agent-updates/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/capability-discovery-guidance.md`, `quickstart.md`, `checklists/`, and `docs/ai/specs/.process/TACD-002-design-concept.md`

**Tests**: Explicit verification tasks are included because the specification requires pointer coverage, generated payload refresh evidence, active guidance wording checks, preserved-ID review, source/dist evidence, and the default deterministic suite.

**Reviewability**: TACD-002 keeps projected production files at 0. The accepted setup warning remains bounded to docs/process guidance plus source-derived generated payload refresh. TACD-003 prerequisite/user-facing messaging and TACD-004 deterministic/eval enforcement remain deferred.

**Organization**: Tasks are grouped by user story, with shared directive setup first and generated payload/PR evidence after source guidance changes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other marked tasks in the same phase because it touches different files and has no dependency on incomplete tasks.
- **[Story]**: Maps to the user story from `spec.md`.
- Every task includes exact file paths or command paths.

## Phase 1: Setup and Reviewability Checkpoint

**Purpose**: Confirm scope, reviewability, and deferred work before implementation starts.

- [x] T001 Verify the TACD-002 reviewability checkpoint against `specs/tacd-002-capability-discovery-directive-and-agent-updates/spec.md`, `specs/tacd-002-capability-discovery-directive-and-agent-updates/plan.md`, and `docs/ai/specs/.process/TACD-002-design-concept.md`, preserving 0 projected production files and TACD-003/TACD-004 deferrals before editing source guidance.
- [x] T002 Confirm no TACD-003 prerequisite/user-facing messaging or TACD-004 enforcement/eval files are added to the implementation scope by reviewing `specs/tacd-002-capability-discovery-directive-and-agent-updates/contracts/capability-discovery-guidance.md` and `specs/tacd-002-capability-discovery-directive-and-agent-updates/quickstart.md`.

## Phase 2: Foundational Directive

**Purpose**: Create the shared source directive and narrow active reference strategy that all stories rely on.

- [x] T003 Create the shared capability-discovery directive in `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` with the capability categories, selection rule, fallback rule, compact evidence wording, inventory rule, and metadata policy from `specs/tacd-002-capability-discovery-directive-and-agent-updates/contracts/capability-discovery-guidance.md`.
- [x] T004 Update the active consensus pointer in `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md` to reference capability-first discovery without rewriting TACD-003 prerequisite docs or TACD-004 enforcement guidance.
- [x] T005 Update the active gate-validation pointer in `speckit-pro/skills/speckit-autopilot/references/gate-validation.md` to reference capability-first discovery without adding deterministic pointer enforcement.
- [x] T006 Verify the foundational directive wording in `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`, `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md`, and `speckit-pro/skills/speckit-autopilot/references/gate-validation.md` covers FR-001 through FR-008 before agent-surface updates.

**Checkpoint**: Shared source guidance is ready; user story implementation can now begin.

## Phase 3: User Story 1 - Agents Choose By Capability Need (Priority: P1) - MVP

**Goal**: Active agent guidance selects by task need and capability category instead of preferred named optional MCP tools.

**Independent Test**: Review scoped Claude and Codex guidance and confirm instructions identify the needed capability category, choose the best installed match by fit/evidence quality, and record the capability path.

### Implementation for User Story 1

- [x] T007 [P] [US1] Update capability-first behavior wording for `codebase-analyst` in `speckit-pro/agents/codebase-analyst.md`.
- [x] T008 [P] [US1] Update capability-first behavior wording for `domain-researcher` in `speckit-pro/agents/domain-researcher.md`.
- [x] T009 [P] [US1] Update capability-first behavior wording for `clarify-executor` in `speckit-pro/agents/clarify-executor.md`.
- [x] T010 [P] [US1] Update capability-first behavior wording for `checklist-executor` in `speckit-pro/agents/checklist-executor.md`.
- [x] T011 [P] [US1] Update capability-first behavior wording for `analyze-executor` in `speckit-pro/agents/analyze-executor.md`.
- [x] T012 [P] [US1] Update capability-first behavior wording for `implement-executor` in `speckit-pro/agents/implement-executor.md`.
- [x] T013 [P] [US1] Update capability-first Codex TOML instructions for `codebase-analyst` in `speckit-pro/codex-agents/codebase-analyst.toml`.
- [x] T014 [P] [US1] Update capability-first Codex TOML instructions for `domain-researcher` in `speckit-pro/codex-agents/domain-researcher.toml`.
- [x] T015 [P] [US1] Update capability-first Codex TOML instructions for `clarify-executor` in `speckit-pro/codex-agents/clarify-executor.toml`.
- [x] T016 [P] [US1] Update capability-first Codex TOML instructions for `checklist-executor` in `speckit-pro/codex-agents/checklist-executor.toml`.
- [x] T017 [P] [US1] Update capability-first Codex TOML instructions for `analyze-executor` in `speckit-pro/codex-agents/analyze-executor.toml`.
- [x] T018 [P] [US1] Update capability-first Codex TOML instructions for `implement-executor` in `speckit-pro/codex-agents/implement-executor.toml`.
- [x] T019 [US1] Verify active behavior wording in `speckit-pro/agents/`, `speckit-pro/codex-agents/`, `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md`, and `speckit-pro/skills/speckit-autopilot/references/gate-validation.md` no longer describes named optional MCP tools as default preferred behavior.

**Checkpoint**: User Story 1 is independently testable through active source guidance review.

## Phase 4: User Story 2 - Agents Work Without Optional Capabilities (Priority: P1)

**Goal**: Active guidance preserves normal operation when optional capabilities are missing, unavailable, or unusable, with lower-confidence fallback disclosure.

**Independent Test**: Inspect the shared directive and scoped agent guidance for local, native platform, and repo-local fallback behavior with medium/low confidence disclosure.

### Implementation for User Story 2

- [x] T020 [US2] Add or verify fallback behavior in `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` for missing, unavailable, or unusable installed capabilities using the exact fallback wording from `specs/tacd-002-capability-discovery-directive-and-agent-updates/contracts/capability-discovery-guidance.md`.
- [x] T021 [P] [US2] Verify Claude agents in `speckit-pro/agents/codebase-analyst.md`, `speckit-pro/agents/domain-researcher.md`, `speckit-pro/agents/clarify-executor.md`, `speckit-pro/agents/checklist-executor.md`, `speckit-pro/agents/analyze-executor.md`, and `speckit-pro/agents/implement-executor.md` point to the fallback behavior through the shared directive.
- [x] T022 [P] [US2] Verify Codex agents in `speckit-pro/codex-agents/codebase-analyst.toml`, `speckit-pro/codex-agents/domain-researcher.toml`, `speckit-pro/codex-agents/clarify-executor.toml`, `speckit-pro/codex-agents/checklist-executor.toml`, `speckit-pro/codex-agents/analyze-executor.toml`, and `speckit-pro/codex-agents/implement-executor.toml` include the compact equivalent fallback semantics or a stable directive pointer.
- [x] T023 [US2] Verify evidence wording in `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` includes `Capability path: <need> -> <selected capability/source>; Evidence: <citations or local file refs>; Confidence: <high|medium|low> (<brief reason>)` and constrains fallback confidence to medium or low.

**Checkpoint**: User Story 2 is independently testable through fallback and evidence wording review.

## Phase 5: User Story 3 - Runtime Guidance Stays Semantically Aligned (Priority: P2)

**Goal**: Claude and Codex runtime guidance share one semantic directive or approved runtime-specific equivalent.

**Independent Test**: Compare each scoped Claude and Codex surface and confirm it points to `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` or carries the approved Codex compact equivalent marker with matching behavior requirements.

### Implementation for User Story 3

- [x] T024 [P] [US3] Verify pointer coverage for Claude source agents in `speckit-pro/agents/codebase-analyst.md`, `speckit-pro/agents/domain-researcher.md`, `speckit-pro/agents/clarify-executor.md`, `speckit-pro/agents/checklist-executor.md`, `speckit-pro/agents/analyze-executor.md`, and `speckit-pro/agents/implement-executor.md`.
- [x] T025 [P] [US3] Verify pointer or compact-equivalent coverage for Codex TOML agents in `speckit-pro/codex-agents/codebase-analyst.toml`, `speckit-pro/codex-agents/domain-researcher.toml`, `speckit-pro/codex-agents/clarify-executor.toml`, `speckit-pro/codex-agents/checklist-executor.toml`, `speckit-pro/codex-agents/analyze-executor.toml`, and `speckit-pro/codex-agents/implement-executor.toml`.
- [x] T026 [US3] Verify Codex TOML compact equivalents use the exact marker `Capability discovery equivalent: mirrors speckit-pro/skills/speckit-autopilot/references/capability-discovery.md for installed Codex TOML runtime.` in `speckit-pro/codex-agents/*.toml` where direct pointer resolution would break.
- [x] T027 [US3] Build the preserved-ID review table for the PR packet covering `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml`, Claude frontmatter `tools:` fields in `speckit-pro/agents/*.md`, and any generated manifest/path rewrite metadata, with file, field, classification, and behavior-scan result.
- [x] T028 [US3] Verify preserved exact IDs in `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml` and `speckit-pro/agents/*.md` are metadata, historical, provenance, or generated rewrite evidence rather than active preferred-tool behavior.

**Checkpoint**: User Story 3 is independently testable through source pointer/equivalent coverage and preserved-ID classification.

## Phase 6: User Story 4 - Generated Payloads Match Source Guidance (Priority: P2)

**Goal**: Generated Claude and Codex payloads are refreshed from source guidance and trace back to source changes.

**Independent Test**: Run the payload refresh path, review source-to-`dist/**` diffs, run a second rebuild, and confirm no hand-edited payload-only behavior changes remain.

### Implementation for User Story 4

- [x] T029 [US4] Run `bash scripts/build-plugin-payloads.sh` from the repository root to refresh `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/` from source.
- [x] T030 [US4] Verify generated directive copies exist at `dist/claude/speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` and `dist/codex/speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`.
- [x] T031 [US4] Review source/dist evidence with `git diff -- speckit-pro dist/claude/speckit-pro dist/codex/speckit-pro` and confirm generated payload changes trace back to source guidance rather than direct `dist/**` edits.
- [x] T032 [US4] Run `bash scripts/build-plugin-payloads.sh` a second time and verify `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/` do not gain unintended additional changes.
- [x] T033 [US4] Verify generated payload pointer coverage in `dist/claude/speckit-pro/agents/`, `dist/codex/speckit-pro/codex-agents/`, `dist/claude/speckit-pro/skills/speckit-autopilot/references/`, and `dist/codex/speckit-pro/skills/speckit-autopilot/references/`.

**Checkpoint**: User Story 4 is independently testable through generated payload refresh and source/dist diff evidence.

## Phase 7: Polish, Verification, and PR Packet

**Purpose**: Run cross-cutting verification and prepare the review packet without implementing TACD-003 or TACD-004.

- [x] T034 Verify all FR-001 through FR-015 and SC-001 through SC-006 map to completed tasks and changed files using `specs/tacd-002-capability-discovery-directive-and-agent-updates/spec.md` and the final diff under `speckit-pro/`, `dist/claude/speckit-pro/`, and `dist/codex/speckit-pro/`.
- [x] T035 Verify active guidance wording and scope guard against `specs/tacd-002-capability-discovery-directive-and-agent-updates/checklists/llm-integration.md`, `specs/tacd-002-capability-discovery-directive-and-agent-updates/checklists/error-handling.md`, and `specs/tacd-002-capability-discovery-directive-and-agent-updates/checklists/integration.md`.
- [x] T036 Run the default deterministic suite with `bash tests/speckit-pro/run-all.sh`.
- [x] T037 Prepare the PR review packet content from `specs/tacd-002-capability-discovery-directive-and-agent-updates/spec.md`, `specs/tacd-002-capability-discovery-directive-and-agent-updates/plan.md`, final diffs under `speckit-pro/`, `dist/claude/speckit-pro/`, and `dist/codex/speckit-pro/`, with what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, rollback/flag notes, preserved-ID review table, payload refresh evidence, and explicit TACD-003/TACD-004 deferrals.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. Must complete before source edits.
- **Foundational Directive (Phase 2)**: Depends on Setup. Blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational Directive. MVP behavior change.
- **User Story 2 (Phase 4)**: Depends on Foundational Directive and should run after US1 because it verifies overlapping guidance surfaces.
- **User Story 3 (Phase 5)**: Depends on US1 and US2 source guidance being stable.
- **User Story 4 (Phase 6)**: Depends on all source guidance changes from US1 through US3.
- **Polish and Verification (Phase 7)**: Depends on all desired user stories and generated payload refresh.

### User Story Dependencies

- **US1 (P1)**: MVP after Phase 2.
- **US2 (P1)**: Same priority as US1 but serial after US1 to avoid overlapping edits in the same agent guidance files.
- **US3 (P2)**: After US1 and US2 so pointer/equivalent coverage reflects final behavior wording.
- **US4 (P2)**: After US1 through US3 because generated payloads must be refreshed from final source.

### Parallel Opportunities

- T007 through T018 can run in parallel after T003 through T006 because each task updates a different source agent file.
- T021 and T022 can run in parallel after T020 because they verify different runtime families.
- T024 and T025 can run in parallel because they verify different runtime families.
- Within T027/T028 review, metadata rows can be collected independently by file family, but the final preserved-ID table must be consolidated once.
- Generated payload tasks T029 through T033 are serial because the builder output and idempotence checks depend on the previous step.

## Parallel Example: User Story 1

```bash
# Parallel source guidance updates after the shared directive exists:
Task: "T007 [US1] Update speckit-pro/agents/codebase-analyst.md"
Task: "T008 [US1] Update speckit-pro/agents/domain-researcher.md"
Task: "T013 [US1] Update speckit-pro/codex-agents/codebase-analyst.toml"
Task: "T014 [US1] Update speckit-pro/codex-agents/domain-researcher.toml"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate the independent US1 behavior review before moving to fallback, parity, or generated payload work.

### Incremental Delivery

1. Shared directive and narrow active pointers.
2. US1 capability-first selection.
3. US2 fallback and evidence disclosure.
4. US3 Claude/Codex semantic alignment and preserved-ID classification.
5. US4 generated payload refresh from source.
6. Final verification and PR packet.

### Autopilot Implementation Groups For Phase 7 Replacement

- **Group A: Directive foundation**: T001-T006
- **Group B: Claude guidance**: T007-T012, T021, T024
- **Group C: Codex guidance and metadata**: T013-T018, T022, T025-T028
- **Group D: Generated payload refresh**: T029-T033
- **Group E: Verification and PR packet**: T034-T037

## Requirement Coverage

| Requirement | Covered by tasks |
|-------------|------------------|
| FR-001 | T003, T007-T019 |
| FR-002 | T003, T006, T019 |
| FR-003 | T004, T005, T021, T024 |
| FR-004 | T013-T018, T022, T025, T026 |
| FR-005 | T003, T007-T019 |
| FR-006 | T020-T023 |
| FR-007 | T003, T020, T023 |
| FR-008 | T003, T019, T035 |
| FR-009 | T003, T019, T027, T028 |
| FR-010 | T027, T028 |
| FR-011 | T027, T028, T035 |
| FR-012 | T029-T033 |
| FR-013 | T001, T002, T035, T037 |
| FR-014 | T001, T002, T005, T035, T037 |
| FR-015 | T027, T031, T034, T037 |
| SC-001 | T019, T035 |
| SC-002 | T024-T026, T033 |
| SC-003 | T020-T023 |
| SC-004 | T029-T033 |
| SC-005 | T027, T028 |
| SC-006 | T001, T002, T035, T037 |

## Notes

- Source guidance under `speckit-pro/` is authoritative.
- Generated `dist/**` payloads are source-derived outputs and must be refreshed through `bash scripts/build-plugin-payloads.sh`.
- Do not hand-edit `dist/**` as durable source.
- Do not implement TACD-003 prerequisite/user-facing messaging in this task list.
- Do not implement TACD-004 deterministic checks, static pointer enforcement, Layer 3 eval changes, or final tool-scoping enforcement in this task list.
