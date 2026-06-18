# Tasks: Troubleshooting, Security, Trust, Update, And Rollback

**Input**: Design documents from `/specs/doc-008-troubleshooting-security-trust-update-rollback/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md, checklists, and `docs/ai/specs/.process/DOC-008-design-concept.md`

**Tests**: No new automated tests are requested for DOC-008. Required validation is the docs-site verification bundle plus manual source-reference review.

**Reviewability**: Keep implementation within the DOC-008 docs/process budget: three user-facing pages, sidebar/navigation, install-page links, and hand-authored reference-shell handoff. Do not edit plugin behavior, generated payload semantics, manifests, hooks, release automation, CI behavior, or generated reference subpages.

**Organization**: Tasks are grouped by user story so each page-level increment can be implemented and reviewed independently after the shared foundation.

## Acceptance Criteria Traceability

| PRD AC | User Story | Requirement / outcome coverage | Task IDs |
|--------|------------|--------------------------------|----------|
| AC-8.1 | US1 | Troubleshooting entries include symptom, likely cause, diagnostic command or file to inspect, recommended fix, platform label, follow-up link, and source citation. | T009-T014, T032-T034 |
| AC-8.2 | US2 | Security docs explain what SpecKit Pro can package or invoke on Claude Code and Codex, including skills, agents/subagents/custom agents, hooks, MCP/app integrations, settings/assets where applicable, and platform boundaries. | T015-T020, T034 |
| AC-8.3 | US2 | The trust model distinguishes repository source, generated payloads, installed cache/runtime state, user/project agents or custom agents, and managed-policy controls. | T015, T018-T020, T034 |
| AC-8.4 | US3 | Update/rollback docs cover marketplace refresh, payload rebuild, version sync, rollback, stale payload, stale cache, reinstall, remove, and stale install recovery cases. | T021-T027, T032, T034 |
| AC-8.5 | US1, US2, US3 | Browser docs state they do not grant permissions, run local plugin workflows, execute local diagnostics, inspect local filesystems, or modify configuration. | T009, T013, T015, T021, T033 |
| AC-8.6 | US2 | Security/evaluator pages cite official vendor docs for platform behavior and label repository-derived behavior separately from recommended practice. | T016-T020, T034 |

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or is read-only with no dependency on incomplete tasks
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Every task names the relevant repo-relative file path(s)

## Phase 1: Setup (Shared Docs Foundation)

**Purpose**: Resolve the docs route/sidebar plan, source inventory, page model, and validation setup before page implementation starts.

- [x] T001 Review declared DOC-008 file operations and docs-only scope in `specs/doc-008-troubleshooting-security-trust-update-rollback/plan.md` before editing docs-site files
- [x] T002 [P] Review existing route shells and sidebar placement in `docs-site/src/content/docs/troubleshooting.md`, `docs-site/src/content/docs/security-and-trust.md`, and `docs-site/astro.config.mjs`
- [x] T003 [P] Build the official-vendor and repository citation checklist from `specs/doc-008-troubleshooting-security-trust-update-rollback/spec.md`, `specs/doc-008-troubleshooting-security-trust-update-rollback/research.md`, and `docs/ai/specs/.process/DOC-008-design-concept.md`
- [x] T004 [P] Review generated DOC-007 reference coverage for manifests, skills, agents, hooks, scripts, tests, and source-vs-dist in `docs-site/src/content/docs/reference/`
- [x] T005 [P] Confirm validation commands and manual content checks from `specs/doc-008-troubleshooting-security-trust-update-rollback/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared content rules that all user-story pages must follow.

**CRITICAL**: Complete this phase before editing the three DOC-008 user-facing pages.

- [x] T006 Define the shared static-Markdown row/case pattern for troubleshooting rows, trust claims, recovery cases, read-only inspections, and manual recovery actions from `specs/doc-008-troubleshooting-security-trust-update-rollback/data-model.md`
- [x] T007 Verify the checklist guardrails for UX, security, error handling, and accessibility in `specs/doc-008-troubleshooting-security-trust-update-rollback/checklists/`
- [x] T008 Confirm that DOC-009 contributor workflow and DOC-010 docs CI hardening remain out of scope by reviewing `docs/ai/specs/.process/DOC-008-workflow.md`

**Checkpoint**: Foundation ready - user story implementation can start by page owner without changing plugin/runtime surfaces.

---

## Phase 3: User Story 1 - Diagnose A Failure Symptom (Priority: P1) MVP

**Goal**: Users can match failure symptoms to likely causes, read-only diagnostics, safe fixes, platform labels, citations, and follow-up links.

**Independent Test**: Open `docs-site/src/content/docs/troubleshooting.md` and verify every in-scope failure class has symptom, platform label, likely cause, read-only inspect command/file, recommended fix, follow-up link, and source citation.

### Implementation for User Story 1

- [x] T009 [US1] Replace the DOC-002 troubleshooting shell with a browser-safe introduction, stable support anchors, and the required matrix field headers in `docs-site/src/content/docs/troubleshooting.md`
- [x] T010 [US1] Add troubleshooting rows for install failure, marketplace source, generated payload, installed cache/runtime state, and permissions/approvals in `docs-site/src/content/docs/troubleshooting.md`
- [x] T011 [US1] Add troubleshooting rows for missing or outdated Spec Kit CLI, GitHub CLI, jq, path confusion, version drift, and source-vs-generated-payload mismatch in `docs-site/src/content/docs/troubleshooting.md`
- [x] T012 [US1] Add the Codex custom-agent troubleshooting row and platform-specific diagnostic text where Claude Code and Codex behavior differs in `docs-site/src/content/docs/troubleshooting.md`
- [x] T013 [US1] Verify every inspect command/file cell is read-only and contains no login, install, remove, reload, restart, approve, edit, set, unset, delete, rebuild, config-write, cache-edit, or token/secret-printing command in `docs-site/src/content/docs/troubleshooting.md`
- [x] T014 [US1] Add source citations and descriptive follow-up links to install, reference, security/trust, and update/rollback destinations in `docs-site/src/content/docs/troubleshooting.md`

**Checkpoint**: User Story 1 is independently reviewable by checking `docs-site/src/content/docs/troubleshooting.md` against FR-003 through FR-006 and SC-002.

---

## Phase 4: User Story 2 - Evaluate Security And Trust Boundaries (Priority: P2)

**Goal**: Evaluators can distinguish official vendor behavior, checked-in Racecraft repository facts, and recommended practice without audit or certification overclaims.

**Independent Test**: Open `docs-site/src/content/docs/security-and-trust.md` and confirm every platform-behavior claim cites current official vendor docs while every Racecraft-specific claim cites checked-in files or generated DOC-007 references.

### Implementation for User Story 2

- [x] T015 [US2] Expand the security/trust shell with explicit non-audit, non-certification, non-threat-model, and non-control-attestation positioning in `docs-site/src/content/docs/security-and-trust.md`
- [x] T016 [US2] Add official Claude Code behavior coverage and narrow citations for plugins, marketplaces, settings, environment variables, permissions, sandboxing/security, hooks, subagents, and managed MCP in `docs-site/src/content/docs/security-and-trust.md`
- [x] T017 [US2] Add official OpenAI Codex behavior coverage and narrow citations for plugins, build plugins, skills, subagents/custom agents, hooks, MCP/app integrations, config, environment variables, CLI, sandboxing, permissions, approvals/security, managed configuration, and AGENTS.md in `docs-site/src/content/docs/security-and-trust.md`
- [x] T018 [US2] Add Racecraft repository fact coverage for source tree, generated payloads, marketplace manifests, skills, agents/custom agents, hooks, scripts, tests, and source-vs-dist evidence in `docs-site/src/content/docs/security-and-trust.md`
- [x] T019 [US2] Add recommended-practice boundaries for installed runtime/cache state, managed policy, update flow, rollback boundaries, and not editing generated payloads or caches directly in `docs-site/src/content/docs/security-and-trust.md`
- [x] T020 [US2] Perform a source-reference review so every official platform claim and every Racecraft repository fact has an appropriate citation in `docs-site/src/content/docs/security-and-trust.md`

**Checkpoint**: User Story 2 is independently reviewable by checking `docs-site/src/content/docs/security-and-trust.md` against FR-007 through FR-010 and SC-003 through SC-005.

---

## Phase 5: User Story 3 - Recover From Stale Or Incorrect Installs (Priority: P3)

**Goal**: Returning users can update, refresh, reinstall, remove, rollback, handle stale payload/cache state, and version-sync safely without hand-editing generated payloads or installed caches.

**Independent Test**: Open `docs-site/src/content/docs/update-and-rollback.md` and verify all eight recovery cases include checkpoint, manual action, side effect, reload/restart expectation, and source citation.

### Implementation for User Story 3

- [x] T021 [US3] Create `docs-site/src/content/docs/update-and-rollback.md` with frontmatter, title `Update & Rollback`, page introduction, browser-safety boundary, and definitions for update, refresh, reinstall, remove, rollback, stale payload, stale cache, and version sync
- [x] T022 [US3] Add recovery cases for update, refresh, reinstall, and remove with checkpoint, manual action, expected side effect, reload/restart need, and source citation in `docs-site/src/content/docs/update-and-rollback.md`
- [x] T023 [US3] Add recovery cases for rollback, stale payload, stale cache, and version sync with checkpoint, manual action, expected side effect, reload/restart need, and source citation in `docs-site/src/content/docs/update-and-rollback.md`
- [x] T024 [US3] Add Codex-specific recovery guidance that separates plugin installation, bundled skill loading, marketplace add/remove/list/upgrade, custom-agent registration through `@SpecKit Pro -> install` or `$install`, and Codex restart in `docs-site/src/content/docs/update-and-rollback.md`
- [x] T025 [US3] Add Claude Code-specific recovery guidance that separates marketplace update/remove, plugin install/uninstall, `/reload-plugins`, plugin detail inspection, managed policy, installed runtime state, and cache behavior in `docs-site/src/content/docs/update-and-rollback.md`
- [x] T026 [US3] Verify stale-cache guidance is last-resort only and direct cache edits, direct cache deletion, or cache directory removal are not default fixes in `docs-site/src/content/docs/update-and-rollback.md`
- [x] T027 [US3] Add source citations and descriptive follow-up links from all recovery cases to install, reference, troubleshooting, and security/trust destinations in `docs-site/src/content/docs/update-and-rollback.md`

**Checkpoint**: User Story 3 is independently reviewable by checking `docs-site/src/content/docs/update-and-rollback.md` against FR-011 through FR-016 and SC-006.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Wire route visibility, cross-links, accessibility, citations, scope checks, and docs-site validation.

- [x] T028 [P] Add the top-level `update-and-rollback` route to the existing How-to/support sidebar near troubleshooting in `docs-site/astro.config.mjs`
- [x] T029 [P] Add descriptive troubleshooting and update/rollback follow-up links to the Claude Code install guide in `docs-site/src/content/docs/install/claude-code.md`
- [x] T030 [P] Add descriptive troubleshooting and update/rollback follow-up links to the Codex install guide in `docs-site/src/content/docs/install/codex.md`
- [x] T031 [P] Add the hand-authored reference-shell handoff to troubleshooting, security/trust, and update/rollback without editing generated reference subpages in `docs-site/src/content/docs/reference.md`
- [x] T032 Verify cross-links use descriptive destination-identifying text and resolve among `docs-site/src/content/docs/troubleshooting.md`, `docs-site/src/content/docs/security-and-trust.md`, `docs-site/src/content/docs/update-and-rollback.md`, `docs-site/src/content/docs/install/claude-code.md`, `docs-site/src/content/docs/install/codex.md`, and `docs-site/src/content/docs/reference.md`
- [x] T033 Verify static Markdown accessibility: semantic table headers or section labels, readable row/case labels, stable headings or anchors, and no interactive-only controls in `docs-site/src/content/docs/troubleshooting.md`, `docs-site/src/content/docs/security-and-trust.md`, and `docs-site/src/content/docs/update-and-rollback.md`
- [x] T034 Perform a final source-citation review across `docs-site/src/content/docs/troubleshooting.md`, `docs-site/src/content/docs/security-and-trust.md`, and `docs-site/src/content/docs/update-and-rollback.md`
- [x] T035 Run `pnpm --dir docs-site reference:check` from the repository root and record the result for `specs/doc-008-troubleshooting-security-trust-update-rollback/quickstart.md` validation
- [x] T036 Run `pnpm --dir docs-site validate` from the repository root and record the result for `specs/doc-008-troubleshooting-security-trust-update-rollback/quickstart.md` validation
- [x] T037 Run `pnpm --dir docs-site validate:links` from the repository root and record the result for `specs/doc-008-troubleshooting-security-trust-update-rollback/quickstart.md` validation
- [x] T038 Run `pnpm --dir docs-site validate && pnpm --dir docs-site validate:links` from the repository root and record the result for `specs/doc-008-troubleshooting-security-trust-update-rollback/quickstart.md` validation
- [x] T039 Review `git diff --name-only` for docs/process-only scope after edits to `docs-site/src/content/docs/troubleshooting.md`, `docs-site/src/content/docs/security-and-trust.md`, and `docs-site/src/content/docs/update-and-rollback.md`; run `bash tests/speckit-pro/run-all.sh --layer 1` only if implementation unexpectedly touches plugin/spec surfaces, manifests, scripts, hooks, tests, generated payload paths, release automation, or CI behavior
- [x] T040 Prepare PR review packet evidence from `specs/doc-008-troubleshooting-security-trust-update-rollback/spec.md`, `specs/doc-008-troubleshooting-security-trust-update-rollback/plan.md`, and the DOC-008 docs-site diff

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - blocks user-story implementation
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on Foundational completion
- **User Story 3 (Phase 5)**: Depends on Foundational completion
- **Polish (Phase 6)**: Depends on the user-story pages targeted for the PR

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - owns `docs-site/src/content/docs/troubleshooting.md`
- **User Story 2 (P2)**: Can start after Foundational - owns `docs-site/src/content/docs/security-and-trust.md`
- **User Story 3 (P3)**: Can start after Foundational - owns `docs-site/src/content/docs/update-and-rollback.md`

User stories can run in parallel by separate page owners after Phase 2 because their primary files are distinct. Cross-page links, sidebar updates, install links, reference handoff, and validation are deferred to Phase 6 to avoid write contention.

### Within Each User Story

- Confirm the source evidence before writing claims.
- Add or update the smallest relevant page section.
- Keep read-only inspection/checkpoint fields separate from mutating recovery actions.
- Add citations before considering the story complete.
- Verify the independent test before moving to cross-link and validation tasks.

---

## Parallel Opportunities

- Phase 1 read-only setup tasks T002, T003, T004, and T005 can run in parallel.
- After Phase 2, US1 tasks T009-T014, US2 tasks T015-T020, and US3 tasks T021-T027 can run in parallel by separate page owners because they primarily edit different files.
- Polish tasks T028, T029, T030, and T031 can run in parallel because they edit different files.
- Final validation tasks T035-T039 should run after all content and navigation edits are complete.

---

## Parallel Example: Page Owners After Foundation

```bash
Task: "T009-T014 [US1] Update troubleshooting matrix in docs-site/src/content/docs/troubleshooting.md"
Task: "T015-T020 [US2] Update trust model in docs-site/src/content/docs/security-and-trust.md"
Task: "T021-T027 [US3] Create update/rollback guidance in docs-site/src/content/docs/update-and-rollback.md"
```

## Parallel Example: Polish Links

```bash
Task: "T029 Add Claude Code install follow-up links in docs-site/src/content/docs/install/claude-code.md"
Task: "T030 Add Codex install follow-up links in docs-site/src/content/docs/install/codex.md"
Task: "T031 Add reference handoff in docs-site/src/content/docs/reference.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 for `docs-site/src/content/docs/troubleshooting.md`.
3. Independently verify the troubleshooting matrix covers all required failure classes and read-only inspection boundaries.
4. Continue to US2, US3, and Polish before final docs-site validation because cross-links and sidebar depend on the full DOC-008 route set.

### Incremental Delivery

1. Complete Setup + Foundational so source policy and row models are fixed.
2. Add US1 troubleshooting matrix and verify it independently.
3. Add US2 security/trust model and verify citations independently.
4. Add US3 update/rollback page and verify recovery cases independently.
5. Add sidebar/install/reference cross-links and run the docs-site validation bundle.

### Scope Guard

- Do not edit `speckit-pro/`, `dist/`, plugin manifests, hooks, release automation, CI workflows, or generated `docs-site/src/content/docs/reference/*.md` subpages for DOC-008.
- If implementation unexpectedly touches plugin/spec surfaces beyond normal task/status updates, add `bash tests/speckit-pro/run-all.sh --layer 1` to verification and record why.
