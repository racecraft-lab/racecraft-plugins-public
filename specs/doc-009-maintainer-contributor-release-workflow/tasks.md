# Tasks: Maintainer and Contributor Release Workflow

**Input**: Design documents from `specs/doc-009-maintainer-contributor-release-workflow/`

**Prerequisites**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [quickstart.md](quickstart.md), and domain checklists under `checklists/`

**Tests**: No new automated tests are required for DOC-009. Validation tasks run existing docs-site and repository checks.

**Reviewability**: DOC-009 remains within budget: one public docs route, SpecKit artifacts, zero production files, and no CI/release/script/manifest/generated-payload edits.

**Organization**: Tasks are grouped by user story so each story has an independent review target.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or is read-only evidence collection
- **[Story]**: User story from [spec.md](spec.md)
- Each task names exact repository paths

## Phase 1: Setup and Source-Fact Audit

**Purpose**: Confirm the current route shell, source evidence, and reviewability boundaries before editing the public page.

- [x] T001 [P] Review the existing DOC-002 shell and target route in `docs-site/src/content/docs/contribute-and-release.md`.
- [x] T002 [P] Review generated reference contract and target links in `docs-site/scripts/generate-reference-pages.mjs` and `docs-site/src/content/docs/reference/{source-vs-dist,scripts,tests,manifests}.md`.
- [x] T003 [P] Review release and validation source files: `.github/workflows/pr-checks.yml`, `.github/workflows/release.yml`, `release-please-config.json`, `.release-please-manifest.json`, `scripts/build-plugin-payloads.sh`, `scripts/sync-marketplace-versions.sh`, `tests/speckit-pro/run-all.sh`, and `docs-site/package.json`.
- [x] T004 Verify reviewability boundaries from `specs/doc-009-maintainer-contributor-release-workflow/plan.md` before editing: no CI workflow, release automation, script, manifest, generated payload, marketplace registry, or version-field changes.

**Checkpoint**: Source facts are verified and the public docs edit can begin.

---

## Phase 2: User Story 1 - Classify the Change Path (Priority: P1)

**Goal**: Contributors can classify docs-only, plugin source, generated payload/dist, marketplace registry, and release automation changes and name required evidence for each.

**Independent Test**: Review the page with one example from each change type and confirm the reader can identify source surface, generated/synchronized surface, required checks, and PR evidence.

- [x] T005 [US1] Replace the DOC-002 shell intro in `docs-site/src/content/docs/contribute-and-release.md` with DOC-009 purpose, audience, and route ownership context.
- [x] T006 [US1] Add a source-of-truth map to `docs-site/src/content/docs/contribute-and-release.md` covering authoring source, generated payloads, marketplace registries, release scripts, tests, docs-site files, and generated reference pages.
- [x] T007 [US1] Add the change-type decision matrix to `docs-site/src/content/docs/contribute-and-release.md` for docs-only, plugin source, generated payload/dist, marketplace registry, and release automation changes.
- [x] T008 [US1] Add source-vs-generated guidance to `docs-site/src/content/docs/contribute-and-release.md`, including when generated payloads and generated reference pages should not be hand-edited.

**Checkpoint**: US1 can be reviewed independently against AC-9.1.

---

## Phase 3: User Story 2 - Complete Release Readiness (Priority: P1)

**Goal**: Maintainers can use the page to prepare or review a release-ready PR with source/dist, marketplace, version, generated payload, and validation evidence.

**Independent Test**: Apply the checklist to a hypothetical plugin source PR and a docs-site PR and confirm all required parity and validation evidence is present.

- [x] T009 [US2] Add one consolidated release-readiness command block to `docs-site/src/content/docs/contribute-and-release.md` with `bash scripts/build-plugin-payloads.sh`, `bash scripts/sync-marketplace-versions.sh`, `bash tests/speckit-pro/run-all.sh`, `pnpm --dir docs-site reference:check`, and `pnpm --dir docs-site validate`.
- [x] T010 [US2] Add payload rebuild and marketplace sync guidance to `docs-site/src/content/docs/contribute-and-release.md` sourced from `scripts/build-plugin-payloads.sh`, `scripts/sync-marketplace-versions.sh`, and generated reference links.
- [x] T011 [US2] Add version-field ownership guidance to `docs-site/src/content/docs/contribute-and-release.md` covering release-please-owned source manifests, generated payload manifests, and synchronized marketplace versions.
- [x] T012 [US2] Add observable release automation flow to `docs-site/src/content/docs/contribute-and-release.md` covering release-please PRs, release PR payload sync, manual PR Checks dispatch, GitHub Release publication, and post-release sync PR behavior.
- [x] T013 [US2] Add the final release-readiness checklist to `docs-site/src/content/docs/contribute-and-release.md` covering source/dist parity, Claude/Codex marketplace parity, manifest version consistency, generated payload validation, full shell suite, and docs-site validation when relevant.

**Checkpoint**: US2 can be reviewed independently against AC-9.2, AC-9.3, and AC-9.4.

---

## Phase 4: User Story 3 - Review PR Metadata and Evidence (Priority: P2)

**Goal**: Reviewers can evaluate PR titles, bodies, validation evidence, traceability, known gaps, and rollback notes from the page.

**Independent Test**: Compare sample PR titles and bodies against the page guidance and confirm invalid titles, internal-only descriptions, and missing evidence are caught.

- [x] T014 [US3] Add contributor PR preparation guidance to `docs-site/src/content/docs/contribute-and-release.md` covering smallest source surface, Conventional Commit title, public-readable body, and validation evidence.
- [x] T015 [US3] Add reviewer evidence guidance to `docs-site/src/content/docs/contribute-and-release.md` covering what changed, why, non-goals, review order, scope budget, traceability, verification, known gaps, and rollback/flag notes.

**Checkpoint**: US3 can be reviewed independently against AC-9.5.

---

## Phase 5: User Story 4 - Understand Docs-Only CI and DOC-010 Handoff (Priority: P3)

**Goal**: Docs maintainers can distinguish current docs-only PR Checks behavior, local docs-site validation expectations, and future DOC-010 hardening.

**Independent Test**: Read the docs-only section and confirm it explains current PR Checks behavior, docs-site validation expectations, and the DOC-010 boundary without promising future CI.

- [x] T016 [US4] Add current PR Checks behavior to `docs-site/src/content/docs/contribute-and-release.md`, including changed-plugin detection, skipped plugin matrix behavior, `validate-plugins`, and `validate-pr-title`.
- [x] T017 [US4] Add docs-site validation and DOC-010 handoff language to `docs-site/src/content/docs/contribute-and-release.md` covering local validation, current CI boundaries, and future site build, search, accessibility, deep-link, responsive, manifest/payload consistency, and safe command-snippet validation.

**Checkpoint**: US4 can be reviewed independently against AC-9.6.

---

## Phase 6: Polish, Validation, and PR Packet Evidence

**Purpose**: Validate the page, confirm traceability, and prepare review evidence.

- [x] T018 [P] Run `pnpm --dir docs-site reference:check` and record the result in `docs/ai/specs/.process/DOC-009-workflow.md`.
- [x] T019 Run `pnpm --dir docs-site validate` and record the result in `docs/ai/specs/.process/DOC-009-workflow.md`.
- [x] T020 Run `bash tests/speckit-pro/run-all.sh` and record the result in `docs/ai/specs/.process/DOC-009-workflow.md`.
- [x] T021 Review `docs-site/src/content/docs/contribute-and-release.md` against AC-9.1 through AC-9.6 and record traceability notes in `docs/ai/specs/.process/DOC-009-workflow.md`.
- [x] T022 Update task completion checkboxes in `specs/doc-009-maintainer-contributor-release-workflow/tasks.md` after implementation and validation.
- [x] T023 Generate or update PR review packet evidence from `docs/ai/specs/.process/DOC-009-workflow.md`, `specs/doc-009-maintainer-contributor-release-workflow/spec.md`, and `specs/doc-009-maintainer-contributor-release-workflow/plan.md`.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup and Source-Fact Audit**: No dependencies.
- **US1**: Depends on T001-T004.
- **US2**: Depends on US1 source map and matrix, especially T006-T008.
- **US3**: Depends on US1 classification language and can proceed after T008.
- **US4**: Depends on T003 and can proceed after T008.
- **Polish and Validation**: Depends on public page content tasks T005-T017.

### User Story Dependencies

- **US1**: First deliverable and MVP review target.
- **US2**: Builds on US1 source/generated distinctions.
- **US3**: Can be reviewed after contributor and maintainer evidence expectations are present.
- **US4**: Can be reviewed after current PR Checks and docs-site validation source facts are captured.

### Parallel Opportunities

- T001, T002, and T003 are read-only source-fact audit tasks and can run in parallel.
- T018 can run independently after generated-reference-related page edits are complete.
- US3 and US4 wording tasks can be drafted in parallel after US1 establishes shared terminology, but final edits must be serialized because they touch the same Markdown file.

## Coverage Matrix

| Requirement | Tasks |
|-------------|-------|
| FR-001, existing route | T005 |
| FR-002, source/generated map | T006, T008 |
| FR-003, change-type matrix | T007 |
| FR-004, per-change evidence | T007, T013 |
| FR-005, contributor path and PR expectations | T014, T015 |
| FR-006, maintainer release readiness | T009-T013 |
| FR-007, shell suite expectation | T009, T020 |
| FR-008, docs-site validation | T009, T017-T019 |
| FR-009, current PR Checks behavior | T016 |
| FR-010, release automation behavior | T012 |
| FR-011, version ownership and marketplace sync | T010, T011 |
| FR-012, deeper guidance links | T006, T008 |
| FR-013, generated references remain generated | T002, T008, T018 |
| FR-014, DOC-010 handoff | T017 |
| FR-015, final checklist | T013, T021 |

## Notes

- `[P]` tasks are limited to read-only source audit or validation that does not edit the same page section.
- No task edits CI workflows, release automation, scripts, manifests, generated payloads, marketplace registries, or version fields.
- Validation evidence belongs in the workflow file and PR packet; implementation remains a docs-only route update.
