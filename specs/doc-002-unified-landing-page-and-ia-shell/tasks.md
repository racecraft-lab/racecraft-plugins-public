# Tasks: DOC-002 Unified landing page and IA shell

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/route-shell-manifest.json`, `quickstart.md`, `docs/ai/specs/.process/DOC-002-design-concept.md`

**Review order**:
1. Slice 1 - Shell/routes: Foundation, User Story 1, and User Story 2.
2. Slice 2 - Validation/config: User Story 3 and Polish.

**Scope guardrails**:
- Allowed implementation surface: `docs-site/**` plus DOC-002 process/spec evidence updates.
- Forbidden surface: `.github/workflows/**`, `README.md`, `speckit-pro/README.md`, `speckit-pro/**`, `dist/claude/**`, `dist/codex/**`, `.claude-plugin/**`, marketplace manifests, generated payloads, hooks, agents, and release automation.
- README files are source evidence only.

**Task format**: `- [ ] T### [P] [US#] Description with exact file path`

## Phase 1: Foundation - Slice 1 Shell Baseline

**Purpose**: Establish the docs app root and baseline Starlight shell without adding validation hardening or deployment workflow.

- [x] T001 Refresh current Astro/Starlight/package evidence and update `specs/doc-002-unified-landing-page-and-ia-shell/research.md` and `specs/doc-002-unified-landing-page-and-ia-shell/plan.md` only if package pins or hard-blocker evidence changed. Covers FR-015, FR-017.
- [x] T002 Validate the path guardrails in `specs/doc-002-unified-landing-page-and-ia-shell/contracts/route-shell-manifest.json` against planned DOC-002 changes before scaffolding `docs-site/`. Covers FR-014, FR-016, FR-017.
- [x] T003 Create `docs-site/package.json` with docs-site-scoped `pnpm` metadata, Astro/Starlight dependencies, and `dev`, `check`, `build`, and `preview` scripts. Covers FR-001, FR-002.
- [x] T004 [P] Create `docs-site/tsconfig.json` for the Astro/Starlight docs app. Covers FR-001.
- [x] T005 [P] Create `docs-site/src/content.config.ts` for the Starlight docs content collection. Covers FR-001.
- [x] T006 Create `docs-site/astro.config.mjs` with Astro/Starlight configured for `site: "https://racecraft-lab.github.io"`, `base: "/racecraft-plugins-public"`, and `trailingSlash: "always"`. Covers FR-001, FR-013.
- [x] T007 Create `docs-site/src/content/docs/` and `docs-site/src/content/docs/install/` as the route-shell content targets. Covers FR-006.

## Phase 2: User Story 1 - Landing Page And Platform Choice

**Goal**: A first-time visitor understands the marketplace, `speckit-pro`, supported platforms, source versus generated payloads, and the next action from the first screen.

**Independent test**: Open the landing page and confirm the first screen includes the marketplace purpose, current plugin, supported Claude Code and Codex paths, source-vs-payload distinction, and static next actions without later-DOC content depth.

- [x] T008 [US1] Validate the landing-page acceptance contract in `specs/doc-002-unified-landing-page-and-ia-shell/spec.md` and `specs/doc-002-unified-landing-page-and-ia-shell/contracts/route-shell-manifest.json` before editing `docs-site/src/content/docs/index.mdx`. Covers FR-003, FR-004, FR-005, FR-009, FR-018.
- [x] T009 [US1] Create `docs-site/src/content/docs/index.mdx` with Starlight frontmatter, page title, marketplace purpose, `speckit-pro`, concise value statement, and Claude Code/Codex platform choices. Covers FR-003, FR-004, FR-009, FR-018.
- [x] T010 [US1] Add a concise source-vs-generated-payload summary to `docs-site/src/content/docs/index.mdx` naming `speckit-pro/`, `dist/claude/**`, and `dist/codex/**` without changing those source or payload paths. Covers FR-005, FR-018, FR-020.
- [x] T011 [US1] Add descriptive native links from `docs-site/src/content/docs/index.mdx` to `/install/claude-code/`, `/install/codex/`, and `/reference/` as static next actions. Covers FR-009, FR-020, FR-021.
- [x] T012 [US1] Verify `docs-site/src/content/docs/index.mdx` excludes full install procedures, long command matrices, testimonials, pricing or generic marketing claims, analytics prompts, and DOC-003 through DOC-010 content depth. Covers FR-003, FR-018.

## Phase 3: User Story 2 - Eleven Route Shells And Diataxis Navigation

**Goal**: A user can navigate all 11 top-level IA routes and see each route's purpose, owner DOC, success criterion, source evidence, deferred boundary, and useful next step.

**Independent test**: Inspect the Starlight sidebar and every route shell to confirm all routes exist, appear in one Diataxis group, and expose the route shell fields as visible semantic content.

- [x] T013 [US2] Validate all route paths, slugs, labels, groups, owner DOCs, success criteria, and source evidence from `specs/doc-002-unified-landing-page-and-ia-shell/contracts/route-shell-manifest.json` before creating route pages. Covers FR-006, FR-007, FR-008.
- [x] T014 [P] [US2] Create `docs-site/src/content/docs/install/claude-code.md` with audience, purpose, DOC-002 shell owner, DOC-003 full-content owner, success criterion, source evidence, deferred boundary, and one static next step. Covers FR-006, FR-007, FR-019, FR-020.
- [x] T015 [P] [US2] Create `docs-site/src/content/docs/install/codex.md` with audience, purpose, DOC-002 shell owner, DOC-004 full-content owner, success criterion, source evidence, deferred boundary, and one static next step. Covers FR-006, FR-007, FR-019, FR-020.
- [x] T016 [P] [US2] Create `docs-site/src/content/docs/first-run.md` with audience, purpose, DOC-002 shell owner, DOC-005 full-content owner, success criterion, source evidence, deferred boundary, and one static next step. Covers FR-006, FR-007, FR-019, FR-020.
- [x] T017 [P] [US2] Create `docs-site/src/content/docs/choose-your-path.md` with static selector fallback guidance, audience, purpose, DOC-002 shell owner, DOC-006/DOC-010 full-content owners, success criterion, source evidence, deferred boundary, and one static next step. Covers FR-006, FR-007, FR-019, FR-020, FR-021.
- [x] T018 [P] [US2] Create `docs-site/src/content/docs/reference.md` with audience, purpose, DOC-002 shell owner, DOC-007 full-content owner, success criterion, source evidence, deferred boundary, one static next step, and source-vs-generated-payload explanation. Covers FR-006, FR-007, FR-010, FR-019, FR-020.
- [x] T019 [P] [US2] Create `docs-site/src/content/docs/troubleshooting.md` with audience, purpose, DOC-002 shell owner, DOC-008 full-content owner, success criterion, source evidence, deferred boundary, and one static next step. Covers FR-006, FR-007, FR-019, FR-020.
- [x] T020 [P] [US2] Create `docs-site/src/content/docs/security-and-trust.md` with audience, purpose, DOC-002 shell owner, DOC-008 full-content owner, success criterion, source evidence, deferred boundary, and one static next step. Covers FR-006, FR-007, FR-019, FR-020.
- [x] T021 [P] [US2] Create `docs-site/src/content/docs/contribute-and-release.md` with audience, purpose, DOC-002 shell owner, DOC-009 full-content owner, success criterion, source evidence, deferred boundary, and one static next step. Covers FR-006, FR-007, FR-019, FR-020.
- [x] T022 [P] [US2] Create `docs-site/src/content/docs/spec-kit-lifecycle.md` with audience, purpose, DOC-002 shell owner, DOC-005/DOC-010 full-content owners, success criterion, source evidence, deferred boundary, and one static next step. Covers FR-006, FR-007, FR-019, FR-020.
- [x] T023 [P] [US2] Create `docs-site/src/content/docs/glossary.md` with audience, purpose, DOC-002 shell owner, DOC-010 full-content owner, success criterion, source evidence, deferred boundary, and one static next step. Covers FR-006, FR-007, FR-019, FR-020.
- [x] T024 [US2] Update `docs-site/astro.config.mjs` Starlight sidebar with Tutorials, How-to, Reference, and Explanation groups and every route slug exactly once. Covers FR-006, FR-008.
- [x] T025 [US2] Verify every route shell under `docs-site/src/content/docs/` displays route purpose, shell owner DOC, full content owner DOC when distinct, success criterion, source evidence, and one static next step as visible page content. Covers FR-007, FR-019, FR-020.
- [x] T026 [US2] Verify the static accessibility shell contract across `docs-site/src/content/docs/index.mdx` and route pages: semantic headings, native links, descriptive link text, keyboard-reachable source order, no JavaScript-only core choices, non-color-only meaning, and DOC-006 fallback boundary. Covers FR-020, FR-021.

## Phase 4: User Story 3 - Build, Links, Pages Config, And Quickstart

**Goal**: A maintainer can install, check, build, preview, and validate internal links from `docs-site/` without adding deployment workflow or broad docs CI hardening.

**Independent test**: From `docs-site/`, run `pnpm check`, `pnpm build`, `pnpm validate`, and `pnpm validate:links` after dependency setup; inspect config for Pages assumptions and no publish workflow.

- [ ] T027 [US3] Validate Slice 2 entry by reviewing the Slice 1 diff for shell/routes only before adding link-validation or final Pages config hardening. Covers FR-017.
- [ ] T028 [P] [US3] Update `docs-site/package.json` with `validate`, `validate:links`, and the selected `starlight-links-validator` dependency if not already present. Covers FR-002, FR-011, FR-022.
- [ ] T029 [P] [US3] Update `docs-site/astro.config.mjs` to enable internal-link validation while preserving `site`, `base`, `trailingSlash`, and Starlight sidebar behavior. Covers FR-011, FR-013, FR-022.
- [ ] T030 [US3] Run `cd docs-site && pnpm install` to create or refresh `docs-site/pnpm-lock.yaml`; if setup fails, apply the documented FR-023 setup next action before considering any framework fallback. Covers FR-002, FR-022, FR-023.
- [ ] T031 [US3] Verify no `.github/workflows/**` file is created while hardening Pages-ready config. Covers FR-014.
- [ ] T032 [US3] Run `cd docs-site && pnpm check` and fix only docs-site-local Astro, TypeScript, content typing, or schema diagnostics. Covers FR-012, FR-022, FR-023.
- [ ] T033 [US3] Run `cd docs-site && pnpm build` and fix only docs-site-local config, content, route, sidebar, or Pages path/base failures. Covers FR-012, FR-013, FR-022, FR-023.
- [ ] T034 [US3] Run `cd docs-site && pnpm validate:links` and fix only internal Markdown/MDX route, anchor, trailing-slash, same-site, or base-path failures. Covers FR-011, FR-022, FR-023.
- [ ] T035 [US3] Run `cd docs-site && pnpm validate` after check/build/link fixes and record command evidence for the final PR review packet. Covers FR-012, FR-022.
- [ ] T036 [US3] Update `specs/doc-002-unified-landing-page-and-ia-shell/quickstart.md` only if actual package scripts, Pages settings, or failure next actions differ from the plan. Covers FR-002, FR-013, FR-022, FR-023.

## Phase 5: Polish - Reviewability And Final Evidence

**Purpose**: Prove route coverage, non-goal boundaries, deterministic validation, and PR review packet readiness.

- [ ] T037 Verify route coverage against `specs/doc-002-unified-landing-page-and-ia-shell/contracts/route-shell-manifest.json`: all 11 paths have content files and all four sidebar groups appear in `docs-site/astro.config.mjs`. Covers FR-006, FR-008.
- [ ] T038 Verify `docs-site/src/content/docs/index.mdx` and `docs-site/src/content/docs/reference.md` both distinguish `speckit-pro/` authoring source from `dist/claude/**` and `dist/codex/**` generated payloads, and verify README files remain unchanged source evidence only. Covers FR-005, FR-010, FR-016.
- [ ] T039 Verify repository diff excludes plugin behavior, marketplace manifests, generated payloads, hooks, agents, release automation, README files, and `.github/workflows/**`. Covers FR-014, FR-016.
- [ ] T040 Build final PR traceability evidence mapping landing, route shells, navigation, source-vs-payload, build/link validation, Pages-ready config, and non-goals to changed files and command outputs. Covers FR-017 and PR review packet requirements.
- [ ] T041 Prepare PR review packet text with what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes. Covers FR-017 and PR review packet requirements.
- [ ] T042 Run or record the reviewability checkpoint if implementation scope expands beyond the accepted warning threshold; preserve shell/routes first and validation/config second instead of adding new DOC-002 scope. Covers FR-017.
- [ ] T043 Run `git diff --name-only` and attach final scope evidence to the workflow or PR packet notes before handoff. Covers FR-014, FR-016, FR-017.

## Dependencies

- Phase 1 blocks all user stories.
- User Story 1 and User Story 2 make up Slice 1 and should be reviewed before Slice 2.
- User Story 3 depends on the shell and routes existing.
- Polish depends on all user stories and validation commands.
- Tasks T014 through T023 are parallel-safe after T013 because they touch separate route files.
- Tasks T028 and T029 are parallel-safe after T027 because they touch separate config/control files.

## Parallel Examples

```text
After T013:
Task: T014 create install/claude-code route shell
Task: T015 create install/codex route shell
Task: T016 create first-run route shell
Task: T017 create choose-your-path route shell
Task: T018 create reference route shell
Task: T019 create troubleshooting route shell
Task: T020 create security-and-trust route shell
Task: T021 create contribute-and-release route shell
Task: T022 create spec-kit-lifecycle route shell
Task: T023 create glossary route shell

After T027:
Task: T028 update docs-site/package.json validation scripts and dependency
Task: T029 update docs-site/astro.config.mjs link-validation config
```

## Coverage Matrix

| Requirement | Task coverage |
|-------------|---------------|
| FR-001 | T003, T004, T005, T006 |
| FR-002 | T003, T028, T030, T036 |
| FR-003 | T008, T009, T012 |
| FR-004 | T008, T009 |
| FR-005 | T008, T010, T038 |
| FR-006 | T007, T013, T014, T015, T016, T017, T018, T019, T020, T021, T022, T023, T024, T037 |
| FR-007 | T013, T014, T015, T016, T017, T018, T019, T020, T021, T022, T023, T025 |
| FR-008 | T013, T024, T037 |
| FR-009 | T008, T009, T011 |
| FR-010 | T018, T038 |
| FR-011 | T028, T029, T034 |
| FR-012 | T032, T033, T035 |
| FR-013 | T006, T029, T033, T036 |
| FR-014 | T002, T031, T039, T043 |
| FR-015 | T001 |
| FR-016 | T002, T038, T039, T043 |
| FR-017 | T001, T002, T027, T040, T041, T042, T043 |
| FR-018 | T008, T009, T010, T012 |
| FR-019 | T014, T015, T016, T017, T018, T019, T020, T021, T022, T023, T025 |
| FR-020 | T010, T011, T014, T015, T016, T017, T018, T019, T020, T021, T022, T023, T025, T026 |
| FR-021 | T011, T017, T026 |
| FR-022 | T028, T029, T030, T032, T033, T034, T035, T036 |
| FR-023 | T030, T032, T033, T034, T036 |

## Acceptance Coverage Matrix

| Acceptance criterion | Task coverage | Verification note |
|----------------------|---------------|-------------------|
| AC-2.1 Landing page states marketplace purpose, current plugin, primary value, and supported platforms in one screen | T008, T009, T010, T011, T012 | Landing first-screen content is implemented and bounded before later-DOC content depth. |
| AC-2.2 IA exposes Tutorials, How-to, Reference, and Explanation sections | T013, T024, T037 | Route manifest and Starlight sidebar groups are checked for all four Diataxis groups. |
| AC-2.3 Claude Code and Codex paths are selectable from the first interaction | T008, T009, T011 | Landing page includes static native links to both platform route shells. |
| AC-2.4 Docs distinguish `speckit-pro/` source from generated install payloads under `dist/claude/**` and `dist/codex/**` | T010, T018, T038 | Landing and Reference shell both carry the source-vs-payload explanation while README and payload files remain unchanged. |
| AC-2.5 Every top-level nav label has a stated purpose and success criterion | T013, T014, T015, T016, T017, T018, T019, T020, T021, T022, T023, T024, T025, T037 | Each route shell is created from the route contract and then verified for visible purpose, owner DOC, success criterion, source evidence, and next step. |

## Task Summary

- Total tasks: 43
- Phase groups: 5
- User stories covered: 3
- Parallel-safe tasks: 14
- Slice 1 tasks: T001-T026
- Slice 2 tasks: T027-T043
- Unresolved items for consensus: None
