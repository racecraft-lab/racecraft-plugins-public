# Tasks: Claude Code Marketplace Installation Path

**Input**: Design documents from `specs/doc-003-claude-code-marketplace-installation-path/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, checklists under `checklists/`, and `docs/ai/specs/.process/DOC-003-design-concept.md`

**Tests**: Docs-only validation. Required command: `pnpm --dir docs-site validate`

**Reviewability**: DOC-003 stays within the `speckit-pro-reviewability` budget: docs/process primary surface, install-relevant README/AGENTS wording only as secondary surface, 0 production runtime files, no generated payload regeneration, no version changes, and no release automation changes.

**Organization**: Tasks are grouped by user-visible docs outcome and user story so each outcome can be reviewed independently.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel because the task is read-only or touches different Markdown files
- **[Story]**: Maps to user stories from `spec.md`
- Every task names exact file paths or directories

## Phase 1: Source Audit

**Purpose**: Collect official Claude Code docs links and repository source/generated evidence before editing the canonical route.

- [x] T001 [P] Audit official Claude Code plugin, marketplace, settings, and hook documentation URLs listed in `specs/doc-003-claude-code-marketplace-installation-path/research.md` for platform-backed add, install, reload, update, uninstall, remove, managed marketplace, settings, and hook claims
- [x] T002 [P] Audit Racecraft marketplace and plugin manifest evidence in `.claude-plugin/marketplace.json` and `speckit-pro/.claude-plugin/plugin.json` for the exact marketplace name, plugin name, and SpecKit Pro metadata
- [x] T003 [P] Audit source trust surfaces in `speckit-pro/skills/`, `speckit-pro/agents/`, and `speckit-pro/hooks/hooks.json` for the installed skill, agent, and hook inventory
- [x] T004 [P] Audit generated Claude payload evidence in `dist/claude/speckit-pro/` and keep this directory read-only for DOC-003
- [x] T005 [P] Audit install-relevant command-vs-skill terminology in `README.md`, `AGENTS.md`, `speckit-pro/README.md`, and `docs-site/src/content/docs/install/claude-code.md`
- [x] T006 Review DOC-003 non-goals in `docs/ai/specs/.process/DOC-003-design-concept.md` against declared file operations in `specs/doc-003-claude-code-marketplace-installation-path/plan.md`

## Phase 2: Scope And Reviewability Gate

**Purpose**: Confirm the task set stays docs-only before user story work begins.

- [x] T007 Verify the reviewability budget and declared file operations in `specs/doc-003-claude-code-marketplace-installation-path/plan.md` before modifying docs
- [x] T008 Inspect the current DOC-002 shell and target route structure in `docs-site/src/content/docs/install/claude-code.md`

**Checkpoint**: Source evidence and scope boundaries are ready for page work.

## Phase 3: User Story 1 - Install SpecKit Pro From The Racecraft Marketplace (Priority: P1)

**Goal**: A Claude Code user can add the Racecraft marketplace, install SpecKit Pro, reload plugins, and verify the initial plugin surface from the canonical page.

**Independent Test**: A reviewer can open `docs-site/src/content/docs/install/claude-code.md` and find an ordered add, install, reload, and `/plugin` visibility path with source-backed commands and expected signals.

- [x] T009 [US1] Replace the DOC-002 shell opening in `docs-site/src/content/docs/install/claude-code.md` with the canonical Claude-only install route, source authority summary, and Codex cross-link boundary
- [x] T010 [US1] Add ordered Racecraft marketplace add and SpecKit Pro install commands as standalone copyable code blocks in `docs-site/src/content/docs/install/claude-code.md`
- [x] T011 [US1] Add `/reload-plugins` and `/plugin` visibility verification steps with plain-language success signals in `docs-site/src/content/docs/install/claude-code.md`
- [x] T012 [US1] Structure the first-time install flow in `docs-site/src/content/docs/install/claude-code.md` with descriptive headings, ordered lists, meaningful link text, inline literal command names, and no dense command tables
- [x] T013 [US1] Add a concise pre-skill trust note with a jump link in `docs-site/src/content/docs/install/claude-code.md` after `/plugin` visibility and before running namespaced SpecKit Pro skills

**Checkpoint**: First-time install flow is complete and independently reviewable.

## Phase 4: User Story 2 - Verify The Namespaced Skill Surface (Priority: P1)

**Goal**: A Claude Code user can verify the current namespaced skill surface without deprecated command-folder confusion.

**Independent Test**: A reviewer can compare the verification section with repository-controlled plugin surfaces and confirm it names `/plugin`, `/speckit-pro:speckit-status`, and `/speckit-pro:speckit-coach` with expected success signals.

- [x] T014 [US2] Add `/speckit-pro:speckit-status` as a standalone verification command with expected success signals in `docs-site/src/content/docs/install/claude-code.md`
- [x] T015 [US2] Add `/speckit-pro:speckit-coach` as a standalone verification command with expected success signals in `docs-site/src/content/docs/install/claude-code.md`
- [x] T016 [US2] Clarify current namespaced skill usage and remove install-facing deprecated command-folder language from `docs-site/src/content/docs/install/claude-code.md`

**Checkpoint**: Installed plugin and namespaced skill verification are complete.

## Phase 5: User Story 3 - Manage Plugin Lifecycle Without Guessing Commands (Priority: P2)

**Goal**: A Claude Code user can update, uninstall, remove the marketplace when appropriate, and reinstall SpecKit Pro from one lifecycle section.

**Independent Test**: A reviewer can validate that lifecycle guidance covers update, uninstall, marketplace removal, and reinstall with exact commands, decision points, and post-action checks.

- [x] T017 [US3] Add marketplace or plugin update guidance with exact commands, reload guidance, and post-update verification in `docs-site/src/content/docs/install/claude-code.md`
- [x] T018 [US3] Add SpecKit Pro uninstall guidance with exact commands and a clear distinction from marketplace removal in `docs-site/src/content/docs/install/claude-code.md`
- [x] T019 [US3] Add Racecraft marketplace removal and clean reinstall sequences with exact commands and decision points in `docs-site/src/content/docs/install/claude-code.md`
- [x] T020 [US3] Add concise basic recovery guidance for wrong marketplace source, stale marketplace listing, missing `speckit-pro`, failed `/plugin` visibility, missing namespaced skills after reload, failed update, failed uninstall, failed marketplace removal, and failed reinstall in `docs-site/src/content/docs/install/claude-code.md`
- [x] T021 [US3] Add recovery stopping rules that route to DOC-008 troubleshooting after one clean retry or when managed policy, permissions, network access, cache clearing, rollback, incident response, undocumented platform behavior, or Codex-specific failures appear in `docs-site/src/content/docs/install/claude-code.md`

**Checkpoint**: Lifecycle and basic recovery coverage are complete without becoming a troubleshooting matrix.

## Phase 6: User Story 4 - Inspect Trust Surfaces Before Running Plugin Skills (Priority: P2)

**Goal**: An evaluator can identify source-backed trust surfaces before installing or running SpecKit Pro skills.

**Independent Test**: A reviewer can find marketplace metadata, plugin manifest metadata, skills, agents, hooks, MCP/settings implications, generated Claude payloads, source/generated path distinctions, and security claim boundaries from the canonical page in under 5 minutes.

- [x] T022 [US4] Add marketplace metadata and plugin manifest trust inventory entries for `.claude-plugin/marketplace.json` and `speckit-pro/.claude-plugin/plugin.json` in `docs-site/src/content/docs/install/claude-code.md`
- [x] T023 [US4] Add skills, agents, hooks, MCP/settings, and managed marketplace trust inventory entries for `speckit-pro/skills/`, `speckit-pro/agents/`, `speckit-pro/hooks/hooks.json`, and official Claude Code settings documentation in `docs-site/src/content/docs/install/claude-code.md`
- [x] T024 [US4] Add source-vs-generated path mapping for source files and `dist/claude/speckit-pro/` generated payloads in `docs-site/src/content/docs/install/claude-code.md`
- [x] T025 [US4] Add security claim boundaries that avoid unsupported sandboxing, isolation, harmlessness, blocking, hook safety, and managed marketplace safety guarantees in `docs-site/src/content/docs/install/claude-code.md`
- [x] T026 [US4] Bound managed marketplace guidance to official settings behavior, source inspection, add/update/remove implications, and user/project/local/managed scope distinctions in `docs-site/src/content/docs/install/claude-code.md`

**Checkpoint**: Trust guidance is source-backed, progressively disclosed, and bounded.

## Phase 7: User Story 5 - Maintain Source And Generated Payload Clarity (Priority: P3)

**Goal**: Maintainers can update install-relevant docs without leaving command-vs-skill confusion or implying runtime changes.

**Independent Test**: A reviewer can inspect the canonical page and install-relevant README/AGENTS wording and find no contradictions about current skill-based usage.

- [x] T027 [P] [US5] Update install-relevant skills terminology in `README.md` without rewriting unrelated maintainer guidance
- [x] T028 [P] [US5] Update install-relevant skills terminology in `AGENTS.md` without rewriting unrelated maintainer guidance
- [x] T029 [P] [US5] Update install-relevant skills terminology in `speckit-pro/README.md` without rewriting unrelated maintainer guidance
- [x] T030 [US5] Recheck source/generated path wording across `README.md`, `AGENTS.md`, `speckit-pro/README.md`, and `docs-site/src/content/docs/install/claude-code.md` so source paths and generated payload paths are not conflated

**Checkpoint**: Install-relevant terminology is consistent across supporting docs.

## Phase 8: Cross-Links And Boundary Clarity

**Purpose**: Keep DOC-003 connected to adjacent routes without implementing out-of-scope content.

- [x] T031 Confirm the Codex route is linked only as `/install/codex/` and no Codex install, verification, custom-agent, cache, sandbox, approval, or runtime recovery commands are embedded in `docs-site/src/content/docs/install/claude-code.md`
- [x] T032 Confirm full troubleshooting, rollback, cache cleanup, incident response, policy design, network debugging, and permission repair are routed to DOC-008 rather than implemented in `docs-site/src/content/docs/install/claude-code.md`
- [x] T033 Inspect `docs-site/src/content/docs/reference.md`, `docs-site/src/content/docs/security-and-trust.md`, and `docs-site/src/content/docs/troubleshooting.md` only for navigation or boundary contradictions, and modify them only if required to keep DOC-003 links accurate

## Phase 9: Validation

**Purpose**: Prove the docs-only implementation satisfies functional requirements, success criteria, and scope boundaries.

- [x] T034 Run planning artifact validation from `specs/doc-003-claude-code-marketplace-installation-path/quickstart.md`
- [x] T035 Run command coverage validation for install, reload, `/plugin`, `/speckit-pro:speckit-status`, and `/speckit-pro:speckit-coach` in `docs-site/src/content/docs/install/claude-code.md`
- [x] T036 Run lifecycle, Codex boundary, trust inventory, terminology, and runtime-surface checks from `specs/doc-003-claude-code-marketplace-installation-path/quickstart.md`
- [x] T037 Run `pnpm --dir docs-site validate` for `docs-site/src/content/docs/install/claude-code.md`
- [x] T038 Inspect `git diff --name-only` to confirm no changes under `dist/`, `speckit-pro/skills/`, `speckit-pro/agents/`, `speckit-pro/hooks/`, `speckit-pro/.claude-plugin/`, release automation files, or other runtime/generated payload paths
- [x] T039 Prepare PR review packet details from `docs-site/src/content/docs/install/claude-code.md`, `README.md`, `AGENTS.md`, `speckit-pro/README.md`, and validation evidence, covering what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Source Audit**: No dependencies; read-only audit tasks marked `[P]` can run in parallel.
- **Phase 2 Scope And Reviewability Gate**: Depends on Phase 1 evidence and blocks page edits.
- **Phase 3 User Story 1**: Depends on Phase 2 and establishes the canonical first-time install flow.
- **Phase 4 User Story 2**: Depends on Phase 3 because skill verification follows `/plugin` visibility and the pre-skill trust note.
- **Phase 5 User Story 3**: Depends on Phases 3-4 because lifecycle checks reuse installed-surface verification.
- **Phase 6 User Story 4**: Depends on Phase 1 source audit and can be drafted after Phase 3 establishes progressive disclosure placement.
- **Phase 7 User Story 5**: Depends on Phase 1 terminology audit and can run in parallel across different README/AGENTS files.
- **Phase 8 Cross-Links And Boundary Clarity**: Depends on canonical page content from Phases 3-6.
- **Phase 9 Validation**: Depends on all implementation phases.

### User Story Dependencies

- **US1 (P1)**: Foundation for the install path; no dependency on other user stories after Phase 2.
- **US2 (P1)**: Depends on US1 because namespaced skill verification should occur after `/plugin` visibility and trust note placement.
- **US3 (P2)**: Depends on US1 and US2 for lifecycle verification reuse.
- **US4 (P2)**: Depends on Phase 1 evidence; content placement depends on US1 progressive disclosure.
- **US5 (P3)**: Depends on Phase 1 terminology audit; supporting file edits can run in parallel because they touch different Markdown files.

## Parallel Opportunities

- T001, T002, T003, T004, and T005 are parallel-safe source audits because they are read-only and inspect different evidence sets.
- T027, T028, and T029 are parallel-safe terminology edits because each touches a different Markdown file.
- No tasks that edit `docs-site/src/content/docs/install/claude-code.md` are marked `[P]` because they share the canonical page.

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 and US2 so first-time install and verification work end to end.
3. Validate the canonical route has source-backed add, install, reload, `/plugin`, `/speckit-pro:speckit-status`, and `/speckit-pro:speckit-coach` coverage.

### Incremental Delivery

1. Add lifecycle and basic recovery guidance from US3.
2. Add trust inventory and source/security boundaries from US4.
3. Patch install-relevant terminology in supporting docs from US5.
4. Run validation and prepare PR packet evidence.

## Requirement Coverage Evidence

| Requirement | Covered by tasks |
|-------------|------------------|
| FR-001 | T009, T037 |
| FR-002 | T010, T011, T035 |
| FR-003 | T010, T014, T015, T017, T018, T019, T035 |
| FR-004 | T011, T014, T015, T035 |
| FR-005 | T011, T014, T015, T035 |
| FR-006 | T017, T018, T019, T036 |
| FR-007 | T018, T019, T036 |
| FR-008 | T013, T022, T023, T024, T026 |
| FR-009 | T024, T030, T036 |
| FR-010 | T001, T002, T003, T004, T022, T023, T025 |
| FR-011 | T005, T016, T027, T028, T029, T030 |
| FR-012 | T009, T031 |
| FR-013 | T004, T006, T007, T038 |
| FR-014 | T037 |
| FR-015 | T012, T037 |
| FR-016 | T010, T014, T015, T017, T018, T019 |
| FR-017 | T012, T022, T023, T024, T026 |
| FR-018 | T012, T031 |
| FR-019 | T025, T036 |
| FR-020 | T023, T025 |
| FR-021 | T021, T026, T032 |
| FR-022 | T020, T036 |
| FR-023 | T021, T032, T036 |
| FR-024 | T021, T031, T032 |
| SC-001 | T010, T011, T014, T015, T035 |
| SC-002 | T001, T002, T003, T004, T010, T014, T015, T017, T018, T019 |
| SC-003 | T022, T023, T024, T026 |
| SC-004 | T005, T016, T027, T028, T029, T030 |
| SC-005 | T037 |
| SC-006 | T004, T007, T038 |
| SC-007 | T012, T031, T037 |
| SC-008 | T020, T021, T036 |
