---
description: "Task list for DOC-007 command, workflow, manifest, and file-layout reference"
---

# Tasks: Command, workflow, manifest, and file-layout reference

**Input**: Design documents from `/specs/doc-007-command-workflow-manifest-and-file-layout-reference/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/reference-generator.md`, `contracts/reference-inventory.schema.json`, `quickstart.md`

**Tests**: Include test-first/check-first tasks for generator behavior, check mode, freshness diagnostics, citation validation, and docs-site validation because DOC-007 explicitly requires deterministic generate/check behavior.

**Reviewability**: Keep the slice inside the accepted DOC-007 budget: primary surface `docs/process`, secondary surfaces `docs-site` generated reference pages, link-only existing docs updates, and local docs validation. Generated `docs-site/src/content/docs/reference/*.md` pages are generated output; generator behavior, source boundaries, citation rules, and validation behavior remain reviewable.

**Organization**: Tasks are grouped by user story so each story can be implemented, reviewed, and tested independently after the shared foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches a different file or only performs an independent validation/read step.
- **[Story]**: Maps to the user story from `spec.md`.
- Every task names the exact file path or path group it changes or validates.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the docs-site entry points and navigation slots that all generated reference pages rely on.

- [x] T001 Create the generator entry point at `docs-site/scripts/generate-reference-pages.mjs`
- [x] T002 [P] Add `reference:generate`, `reference:check`, and `validate` script wiring in `docs-site/package.json`
- [x] T003 [P] Add the ordered Reference sidebar entries for `reference`, `reference/skills`, `reference/agents`, `reference/manifests`, `reference/hooks`, `reference/scripts`, `reference/tests`, `reference/source-vs-dist`, and `glossary` in `docs-site/astro.config.mjs`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the source boundary, renderer, validation helpers, and reviewability checkpoint before any user-story page work.

**Critical**: No user story work should begin until this phase is complete.

- [x] T004 Define normalized repo-relative source allowlist and excluded-path checks in `docs-site/scripts/generate-reference-pages.mjs`
- [x] T005 Define generator error categories, stdout/stderr routing, and exit-code helpers for source, parse, output-write, and internal failures in `docs-site/scripts/generate-reference-pages.mjs`
- [x] T006 Define `ReferencePage`, `ReferenceRecord`, command/skill reference, manifest field-set, source citation, inferred-note, platform-mapping, and file-classification validation helpers in `docs-site/scripts/generate-reference-pages.mjs`
- [x] T007 Define deterministic Markdown rendering helpers, generated notice text and validation, GitHub citation URL construction, and stable sorting in `docs-site/scripts/generate-reference-pages.mjs`
- [x] T008 Verify the planned file scope remains within the accepted DOC-007 reviewability budget using `specs/doc-007-command-workflow-manifest-and-file-layout-reference/plan.md` and `specs/doc-007-command-workflow-manifest-and-file-layout-reference/tasks.md`

**Checkpoint**: Foundation ready; user-story implementation can now proceed in priority order or in parallel by story with separate owners.

---

## Phase 3: User Story 1 - Understand available plugin surfaces (Priority: P1) [MVP]

**Goal**: Users can open generated reference pages for Claude Code and Codex skills, agents, hooks, and manifests, then identify purpose, runtime differences, and checked-in source citations.

**Independent Test**: Generate the P1 pages and review `docs-site/src/content/docs/reference/skills.md`, `agents.md`, `hooks.md`, and `manifests.md` to confirm parallel Claude Code/Codex presentation, runtime-specific differences, command/skill invocation and output fields, manifest required/optional field groupings, source facts, visible `Sources`, visible `Inferred notes`, and visible generated notices.

### Tests and Checks for User Story 1

- [x] T009 [US1] Add source-existence, citation, generated-notice, command/skill reference field, manifest field-set, and source-fact-vs-inferred-note validation checks for skills, agents, hooks, and manifests in `docs-site/scripts/generate-reference-pages.mjs`

### Implementation for User Story 1

- [x] T010 [US1] Implement skills inventory collection and rendering for Claude Code and Codex surfaces, including invocation form, purpose, prerequisites, and expected output artifact fields, in `docs-site/scripts/generate-reference-pages.mjs`
- [x] T011 [US1] Implement agents inventory collection and rendering for Claude Code and Codex surfaces in `docs-site/scripts/generate-reference-pages.mjs`
- [x] T012 [US1] Implement hooks inventory collection and rendering for Claude Code and Codex configuration surfaces in `docs-site/scripts/generate-reference-pages.mjs`
- [x] T013 [US1] Implement manifest inventory collection and rendering for marketplace, plugin, integration, and generated distribution manifest categories, including runtime-specific required and optional plugin manifest fields, in `docs-site/scripts/generate-reference-pages.mjs`
- [x] T014 [US1] Generate and review the committed P1 Markdown outputs in `docs-site/src/content/docs/reference/skills.md`, `docs-site/src/content/docs/reference/agents.md`, `docs-site/src/content/docs/reference/hooks.md`, and `docs-site/src/content/docs/reference/manifests.md` for generated notices, source-backed command/skill fields, manifest field groupings, and citation visibility
- [x] T015 [US1] Expand the canonical landing page to orient readers to generated subpages in `docs-site/src/content/docs/reference.md`

**Checkpoint**: User Story 1 should be independently reviewable from the generated Markdown pages and `/reference/` landing page.

---

## Phase 4: User Story 2 - Check source-vs-dist responsibilities (Priority: P2)

**Goal**: Maintainers can inspect generated file-layout, scripts, tests, and source-vs-dist pages to distinguish source, generated payload, test-only, release infrastructure, documentation infrastructure, and related repository roles.

**Independent Test**: Generate the P2 pages and sample `docs-site/src/content/docs/reference/scripts.md`, `tests.md`, and `source-vs-dist.md` to confirm every row has a classification, source path, source fact or inferred note boundary, and no unsupported plugin behavior claim.

### Tests and Checks for User Story 2

- [x] T016 [US2] Add file-classification validation checks for source, generated-payload, test-only, release-infrastructure, documentation-infrastructure, and other roles in `docs-site/scripts/generate-reference-pages.mjs`

### Implementation for User Story 2

- [x] T017 [US2] Implement scripts inventory collection and role classification for `speckit-pro/scripts/`, `speckit-pro/skills/speckit-autopilot/scripts/`, root `scripts/`, and validation helpers in `docs-site/scripts/generate-reference-pages.mjs`
- [x] T018 [US2] Implement tests inventory collection and validation-only classification for `tests/speckit-pro/` in `docs-site/scripts/generate-reference-pages.mjs`
- [x] T019 [US2] Implement source-vs-dist responsibility mapping across source, generated payload, test, release, and docs-site paths in `docs-site/scripts/generate-reference-pages.mjs`
- [x] T020 [US2] Generate and review the committed P2 Markdown outputs in `docs-site/src/content/docs/reference/scripts.md`, `docs-site/src/content/docs/reference/tests.md`, and `docs-site/src/content/docs/reference/source-vs-dist.md`

**Checkpoint**: User Story 2 should be independently reviewable from generated Markdown without changing plugin source, generated payload, release automation, or marketplace files.

---

## Phase 5: User Story 3 - Detect stale generated references (Priority: P3)

**Goal**: Reviewers and agents can run local generate/check commands that prove generated reference pages are current, distinguish stale output from source/parsing/internal failures, and leave the working tree unchanged in check mode.

**Independent Test**: Run `pnpm --dir docs-site reference:check` on current output, intentionally make one generated page stale, rerun check to confirm exit `1` without file rewrites, then restore/regenerate and confirm docs validation passes.

### Tests and Checks for User Story 3

- [x] T021 [US3] Add check-mode contract checks for current output, stale output, read-only behavior, exit `1` stdout, and exit `2` stderr categories in `docs-site/scripts/generate-reference-pages.mjs`

### Implementation for User Story 3

- [x] T022 [US3] Implement generate mode to collect, parse, validate, and render all reference data in memory before writing `docs-site/src/content/docs/reference/*.md`
- [x] T023 [US3] Implement read-only `--check` mode byte comparison against `docs-site/src/content/docs/reference/*.md` in `docs-site/scripts/generate-reference-pages.mjs`
- [x] T024 [US3] Implement stale-output diagnostics that list stale paths and `pnpm --dir docs-site reference:generate` on stdout in `docs-site/scripts/generate-reference-pages.mjs`
- [x] T025 [US3] Implement source, parse, output-write, and internal error diagnostics with repo-relative path or phase context on stderr in `docs-site/scripts/generate-reference-pages.mjs`
- [x] T026 [US3] Validate `pnpm --dir docs-site reference:generate` creates exactly seven generated outputs under `docs-site/src/content/docs/reference/`
- [x] T027 [US3] Validate `pnpm --dir docs-site reference:check` succeeds on current output and fails read-only on an intentionally stale `docs-site/src/content/docs/reference/skills.md`
- [x] T028 [US3] Validate `pnpm --dir docs-site validate` runs `reference:check` before Astro check/build using `docs-site/package.json`
- [x] T029 [US3] Validate `pnpm --dir docs-site validate:links` covers public `/racecraft-plugins-public/reference/<slug>/` links from `docs-site/src/content/docs/reference/*.md`

**Checkpoint**: User Story 3 should prove generated reference freshness locally and preserve check-mode immutability.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Add bounded contextual deep links, final citation/readability checks, and review packet evidence without expanding into DOC-008, DOC-009, or DOC-010 scope.

- [x] T030 [P] Add context-specific reference deep links in `docs-site/src/content/docs/install/claude-code.md`
- [x] T031 [P] Add context-specific reference deep links in `docs-site/src/content/docs/install/codex.md`
- [x] T032 [P] Add context-specific skills, scripts, and tests reference links in `docs-site/src/content/docs/first-run.md`
- [x] T033 [P] Add context-specific source-vs-dist, manifests, and hooks reference links in `docs-site/src/content/docs/troubleshooting.md`
- [x] T034 [P] Add context-specific hooks, agents, manifests, and source-vs-dist reference links in `docs-site/src/content/docs/security-and-trust.md`
- [x] T035 [P] Add context-specific source-vs-dist, scripts, tests, and manifests reference links in `docs-site/src/content/docs/contribute-and-release.md`
- [x] T036 Verify generated page heading hierarchy, visible generated notice on all seven pages, visible citation link text with distinguishing context, source-fact separation, inferred-note `Based on:` fields, command/skill invocation/prerequisite/output fields, manifest required/optional field groupings, and static Markdown readability across `docs-site/src/content/docs/reference/*.md`
- [x] T037 Run final scope review with `git diff --name-only` and confirm no `.github/workflows/*`, plugin behavior, manifest semantics, generated payload content, marketplace behavior, install flow, hook semantics, or release automation files changed
- [x] T038 Assemble PR review packet evidence from `specs/doc-007-command-workflow-manifest-and-file-layout-reference/spec.md`, `plan.md`, `tasks.md`, `quickstart.md`, `docs-site` validation output, and final `git diff --name-only`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; `docs-site/package.json` and `docs-site/astro.config.mjs` changes may be done in parallel with generator file creation.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user-story implementation because source boundaries and renderer rules must exist first.
- **User Story 1 (Phase 3)**: Depends on Foundational; MVP scope.
- **User Story 2 (Phase 4)**: Depends on Foundational; can proceed in parallel with User Story 1 after shared helpers exist, but generator-file edits require coordination.
- **User Story 3 (Phase 5)**: Depends on generated page rendering from User Stories 1 and 2.
- **Polish (Phase 6)**: Depends on generated subpage paths being stable.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational; no dependency on User Story 2 or User Story 3.
- **User Story 2 (P2)**: Can start after Foundational; no dependency on User Story 1 for classification logic, but final review should use the same renderer and citation helpers.
- **User Story 3 (P3)**: Depends on generated output definitions from User Story 1 and User Story 2 because check mode compares all seven generated pages.

### Dependency Boundaries

- Do not edit `.github/workflows/*`; CI hardening belongs to DOC-010.
- Do not edit plugin behavior, manifest semantics, generated payload content, marketplace behavior, install flow, hook semantics, or release automation; those files are source evidence only for DOC-007.
- Do not read generated `docs-site/src/content/docs/reference/*.md` files as source evidence; they are writable outputs only.
- Do not use `.git`, repo-relative `.worktrees`, `node_modules`, user-local plugin installs, network sources, or user-pasted JSON as source evidence.
- Keep existing-doc updates link-only plus brief lead-in text; DOC-008 owns troubleshooting/security depth and DOC-009 owns contributor/release workflow depth.

---

## Parallel Opportunities

- T002 and T003 can run in parallel after T001 because they touch separate docs-site config files.
- T030 through T035 can run in parallel after generated reference slugs are stable because each touches a separate existing docs page.
- User Story 1 and User Story 2 can be staffed in parallel after Phase 2 if owners coordinate edits to `docs-site/scripts/generate-reference-pages.mjs`.
- Generated Markdown review can be split by page after T014 and T020 because each output file is independent review surface.

## Parallel Example: Existing Docs Deep Links

```bash
Task: "Add context-specific reference deep links in docs-site/src/content/docs/install/claude-code.md"
Task: "Add context-specific reference deep links in docs-site/src/content/docs/install/codex.md"
Task: "Add context-specific skills, scripts, and tests reference links in docs-site/src/content/docs/first-run.md"
Task: "Add context-specific source-vs-dist, manifests, and hooks reference links in docs-site/src/content/docs/troubleshooting.md"
Task: "Add context-specific hooks, agents, manifests, and source-vs-dist reference links in docs-site/src/content/docs/security-and-trust.md"
Task: "Add context-specific source-vs-dist, scripts, tests, and manifests reference links in docs-site/src/content/docs/contribute-and-release.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundation.
3. Complete Phase 3 User Story 1.
4. Stop and validate generated skills, agents, hooks, manifests, sidebar, and landing-page behavior independently.

### Incremental Delivery

1. Add User Story 1 user-facing surface references.
2. Add User Story 2 maintainer source-vs-dist, scripts, and tests references.
3. Add User Story 3 generate/check validation and stale-output behavior.
4. Add link-only polish updates and final validation evidence.

### Review Strategy

1. Review `docs-site/scripts/generate-reference-pages.mjs` first for source boundary, deterministic ordering, source-fact handling, inferred notes, and exit diagnostics.
2. Review `docs-site/package.json` and `docs-site/astro.config.mjs` for local validation and sidebar routing.
3. Review generated `docs-site/src/content/docs/reference/*.md` pages as generated output for citation visibility and public readability.
4. Review existing docs updates only for contextual deep-link scope.
5. Review validation output and `git diff --name-only` for no-goal compliance.
