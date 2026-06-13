# Tasks: Static docs framework and IA spike

**Input**: Design documents from `specs/doc-001-static-docs-framework-and-ia-spike/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`

**Tests**: No TDD tasks are generated. DOC-001 is a research spike; verification is source-evidence review, diff-scope review, and optional repository structural checks.

**Reviewability**: Keep DOC-001 within the declared docs/process surface. Do not create `package.json`, lockfiles, site config, prototype components, CI workflows, marketplace files, generated payloads, or plugin behavior changes.

**Organization**: Tasks are grouped by user story and research deliverable, not by framework layer.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because the task updates only a bounded research-report section or reads independent source evidence
- **[Story]**: Which user story the task traces to
- Include exact file paths in descriptions

## Phase 1: Foundation - Research Artifact Structure

**Purpose**: Create the report shell, source register, and research-only guardrails before evidence gathering.

- [x] T001 Create `docs/ai/research/interactive-documentation-framework-spike.md` with sections for recommendation, source evidence, candidate matrix, IA skeleton, command handoff, fallback rules, DOC-002 consumption, scope boundary, and verification notes
- [x] T002 Add the official-source list and retrieval-date convention for framework/platform claims in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T003 Add local source-input references from `docs/prd-interactive-documentation.md`, `docs/roadmap-interactive-documentation.md`, `docs/ai/specs/.process/DOC-001-design-concept.md`, and `specs/doc-001-static-docs-framework-and-ia-spike/spec.md` to `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T004 Record the DOC-001 research-only boundary and forbidden implementation surfaces in `docs/ai/research/interactive-documentation-framework-spike.md`

**Checkpoint**: Research report structure and source list are ready for independent evidence refresh.

---

## Phase 2: User Story 1 - Candidate Comparison (Priority: P1)

**Goal**: A maintainer can review source-backed evidence for each candidate stack.

**Independent Test**: Open `docs/ai/research/interactive-documentation-framework-spike.md` and confirm Docusaurus/MDX, VitePress, Astro/Starlight, and repo-native fallback are each compared across the required criteria with current source evidence.

### Research Deliverable: Source Refresh and Candidate Scoring

- [x] T005 [P] [US1] Refresh official Docusaurus/MDX source evidence for static output, GitHub Pages deployment, MDX/React interactivity, versioning, search, broken-link handling, accessibility posture, and package/build/test command roles in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T006 [P] [US1] Refresh official VitePress source evidence for static output, GitHub Pages deployment, Vue/Markdown interactivity, versioning support, search, link checking, accessibility posture, and package/build/test command roles in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T007 [P] [US1] Refresh official Astro/Starlight source evidence for static output, GitHub Pages deployment, MDX/component interactivity, versioning support, search, link checking, accessibility posture, and package/build/test command roles in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T008 [P] [US1] Refresh official GitHub Pages hosting evidence for repository-hosted static HTML/CSS/JS, build publication, and same-repository deployment assumptions in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T009 [P] [US1] Compare search support classes across Docusaurus/MDX, VitePress, Astro/Starlight, and repo-native fallback in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T010 [P] [US1] Compare accessibility and static or keyboard-usable fallback support across Docusaurus/MDX, VitePress, Astro/Starlight, and repo-native fallback in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T011 [P] [US1] Compare versioning, link checking, docs-as-code workflow fit, and maintenance load across all candidates in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T012 [P] [US1] Record package manager, setup, install, dev preview, production build, static preview, minimum validation/test, and deployment command roles for each framework candidate in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T013 [US1] Score each candidate against hard blockers, high-weight tradeoffs, medium-weight tradeoffs, and maintenance tie-breakers in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T014 [US1] Record support class values for each candidate criterion using the report legend, including built-in, official, official third-party hosted, community, community listed by official docs, external/manual, unsupported/blocked, unknown/weak, process-only, or qualitative in `docs/ai/research/interactive-documentation-framework-spike.md`

**Checkpoint**: Candidate comparison is complete enough to support a recommendation.

---

## Phase 3: User Story 2 - IA Skeleton and DOC-002 Command Handoff (Priority: P2)

**Goal**: DOC-002 can create the docs-site shell without reopening stack selection or route-level IA.

**Independent Test**: A DOC-002 implementer can identify route path, Diataxis mode, audience, source evidence, success criterion, package manager, and minimum command roles using only `docs/ai/research/interactive-documentation-framework-spike.md`.

### Research Deliverable: Route-Level Diataxis IA Skeleton

- [x] T015 [US2] Write the route-level Diataxis IA skeleton covering Start, Install: Claude Code, Install: Codex, First Run, Choose Your Path, Reference, Troubleshooting, Security & Trust, Contribute & Release, Spec Kit Lifecycle, and Glossary in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T016 [US2] Add route path, primary Diataxis mode, optional secondary modes, target audience, route purpose, source evidence, success criterion, `shell_owner_doc`, and `full_content_owner_doc` for every IA route in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T017 [US2] Record the selected stack's report-only package manager plus setup, install, development preview, production build, local static preview, minimum validation/test, and deployment command roles for DOC-002 in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T018 [US2] Record DOC-002 consumption guidance, script-name normalization guidance, and selected-stack hard-blocker fallback rules in `docs/ai/research/interactive-documentation-framework-spike.md`

**Checkpoint**: IA and command handoff are ready for DOC-002.

---

## Phase 4: Recommendation Record (Priority: P1)

**Goal**: A maintainer can identify one default stack and understand rejected alternatives quickly.

**Independent Test**: Open `docs/ai/research/interactive-documentation-framework-spike.md` and confirm exactly one default stack is recommended unless a hard blocker is recorded, and every non-selected option has a source-backed rejection or deferral rationale.

### Research Deliverable: Default Stack and Rejected Alternatives

- [x] T019 [US1] Choose one default static docs stack for DOC-002 or record a hard blocker in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T020 [US1] Record rejection or deferral rationale for each non-selected alternative in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T021 [US1] Record known tradeoffs for search, versioning, link checking, accessibility, and maintenance burden in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T022 [US1] Map FR-001 through FR-006 and SC-001, SC-002, SC-004, and SC-006 to evidence in `docs/ai/research/interactive-documentation-framework-spike.md`

**Checkpoint**: Recommendation is complete and traceable.

---

## Phase 5: User Story 3 - Verification and Scope Boundary (Priority: P3)

**Goal**: Reviewers can confirm DOC-001 stayed research-only.

**Independent Test**: Inspect the final diff and verify only the research report and SpecKit planning artifacts changed, with no docs-site scaffold or runtime behavior changes.

### Research Deliverable: Verification Evidence

- [x] T023 [US3] Verify no site scaffold, package files, lockfiles, site config, prototype components, CI workflows, marketplace files, generated payloads, README/plugin README migration files, or plugin behavior files were modified by inspecting `git diff --name-only` and recording the result in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T024 [US3] Validate the IA skeleton covers all 11 required route labels with no placeholder route fields and record the result in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T025 [US3] Validate the report maps FR-007 through FR-011 and SC-003 through SC-005 to changed files and verification evidence in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T026 [US3] Run `bash tests/speckit-pro/run-all.sh --layer 1` from the repository root and record the structural validation result in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T027 [US3] Run `bash tests/speckit-pro/run-all.sh` from the repository root and record the default deterministic verification result in `docs/ai/research/interactive-documentation-framework-spike.md`
- [x] T028 [US3] Add PR review packet source notes covering what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback in `docs/ai/research/interactive-documentation-framework-spike.md`

**Checkpoint**: DOC-001 is ready for review as a research-only spike.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundation (Phase 1)**: No dependencies; must complete before source-refresh tasks
- **Candidate Comparison (Phase 2)**: Depends on Foundation
- **IA Skeleton (Phase 3)**: Depends on Foundation and local source-input references
- **Recommendation Record (Phase 4)**: Depends on Candidate Comparison
- **Verification (Phase 5)**: Depends on the completed report

### User Story Dependencies

- **User Story 1 (P1)**: Candidate comparison can start after Foundation; recommendation depends on comparison evidence
- **User Story 2 (P2)**: Can start after Foundation; final command handoff depends on selected-stack recommendation
- **User Story 3 (P3)**: Starts after the report is complete

### Parallel Opportunities

- T005, T006, T007, and T008 can run in parallel as independent official-source refreshes
- T009, T010, T011, and T012 can run in parallel after candidate evidence is available because each updates a bounded comparison section
- T015 and T016 should stay sequential because route records depend on the skeleton
- Verification tasks T023 through T028 should run sequentially after the report is complete

---

## Parallel Example: Candidate Source Refresh

```bash
Task: "Refresh official Docusaurus/MDX source evidence in docs/ai/research/interactive-documentation-framework-spike.md"
Task: "Refresh official VitePress source evidence in docs/ai/research/interactive-documentation-framework-spike.md"
Task: "Refresh official Astro/Starlight source evidence in docs/ai/research/interactive-documentation-framework-spike.md"
Task: "Refresh official GitHub Pages hosting evidence in docs/ai/research/interactive-documentation-framework-spike.md"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1 to create the report structure and source register.
2. Complete Phase 2 to gather and score framework evidence.
3. Complete Phase 4 to record one default stack and rejected alternatives.
4. Stop and validate that a maintainer can review the recommendation independently.

### Incremental Delivery

1. Add the source-backed candidate comparison.
2. Add the route-level Diataxis IA skeleton and command handoff.
3. Add the recommendation and fallback rules.
4. Add verification evidence and PR review packet source notes.

### Parallel Research Strategy

With multiple researchers:

1. One researcher owns Docusaurus/MDX and GitHub Pages evidence.
2. One researcher owns VitePress and search evidence.
3. One researcher owns Astro/Starlight and accessibility evidence.
4. One reviewer integrates scoring, recommendation, IA, and final verification.

---

## Notes

- DOC-001 writes `docs/ai/research/interactive-documentation-framework-spike.md` plus normal SpecKit artifacts only.
- Package/build/test commands are report-only recommendations; do not create or modify package scripts in DOC-001.
- Do not edit PRD, roadmap, design concept, README, plugin README, or migration content unless scope is explicitly amended.
- Do not create docs-site scaffolding, package files, lockfiles, site config, prototype components, CI workflows, marketplace files, generated payloads, or plugin behavior changes.
