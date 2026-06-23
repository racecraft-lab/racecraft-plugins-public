# Tasks: GitHub Pages Build-And-Deploy Pipeline

**Input**: Design documents from `specs/doc-011-github-pages-build-and-deploy-pipeline/` and `docs/ai/specs/.process/DOC-011-design-concept.md`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/deploy-docs-workflow.md`, `quickstart.md`

**Tests**: No new automated test files are requested. DOC-011 uses source inspection, workflow contract checks, and the existing `pnpm --dir docs-site validate` gate.

**Reviewability**: Keep the slice bounded to the declared file operations: `.github/workflows/deploy-docs.yml`, `docs-site/public/robots.txt`, `docs-site/astro.config.mjs`, `docs-site/scripts/validate-docs-quality.mjs`, `docs/ai/specs/cicd-release-pipeline-verification.md`, `CLAUDE.md`, and DOC-011 process evidence. Do not add DOC-012 launch, custom-domain, base-path, SEO, analytics, Lighthouse, plugin behavior, or custom deploy-script work.

**Organization**: Tasks are grouped by user story for traceability, but DOC-011 remains one vertical slice. The deploy workflow, noindex guard, runbook, and CLAUDE guidance must all land together.

## Phase 1: Setup and Source Inspection

**Purpose**: Start with checks and source inspection before editing workflow, docs-site, or runbook files.

- [x] T001 [P] Inspect docs validation and package-manager commands in `docs-site/package.json` before writing `.github/workflows/deploy-docs.yml`
- [x] T002 [P] Inspect existing GitHub Actions conventions in `.github/workflows/pr-checks.yml` and `.github/workflows/release.yml` before writing `.github/workflows/deploy-docs.yml`
- [x] T003 [P] Inspect existing Starlight config shape in `docs-site/astro.config.mjs` before adding the DOC-011 robots head guard
- [x] T004 [P] Inspect existing agent CI/CD guidance in `CLAUDE.md` before adding the DOC-011 deploy pointer
- [x] T005 Review workflow contract and validation checklist in `specs/doc-011-github-pages-build-and-deploy-pipeline/contracts/deploy-docs-workflow.md` and `specs/doc-011-github-pages-build-and-deploy-pipeline/quickstart.md`

---

## Phase 2: Foundational Scope Checks

**Purpose**: Confirm the bounded DOC-011 scope before implementation starts.

- [x] T006 Verify reviewability budget and declared file operations in `specs/doc-011-github-pages-build-and-deploy-pipeline/plan.md`
- [x] T007 Confirm DOC-011 keeps DOC-012 launch, custom-domain, base-path, and noindex removal work out of scope using `docs/ai/specs/.process/DOC-011-design-concept.md`
- [x] T008 Build a path-filter checklist from `specs/doc-011-github-pages-build-and-deploy-pipeline/contracts/deploy-docs-workflow.md` for `.github/workflows/deploy-docs.yml`

**Checkpoint**: Scope and source evidence are ready. Implementation can begin without expanding the review surface.

---

## Phase 3: User Story 1 - Deploy Docs After Main Merge (Priority: P1)

**Goal**: Maintainers can merge docs-impacting changes to `main` and receive a staging GitHub Pages deployment after validation passes.

**Independent Test**: Inspect `.github/workflows/deploy-docs.yml` and confirm it validates docs before uploading `docs-site/dist` to the `github-pages` deployment environment.

### Implementation for User Story 1

- [x] T009 [US1] Create `.github/workflows/deploy-docs.yml` with `Deploy Docs`, `push` to `main`, explicit broad `paths`, and ordered fixture-heavy negative exclusions
- [x] T010 [US1] Add least-privilege `contents: read`, `pages: write`, and `id-token: write` permissions plus main deploy concurrency with non-`main` no-op isolation in `.github/workflows/deploy-docs.yml`
- [x] T011 [US1] Add the build/upload job in `.github/workflows/deploy-docs.yml` with checkout, Node 22, Corepack pnpm 10.25.0, frozen docs-site install, Chromium-only Playwright install, `rm -rf docs-site/dist`, `pnpm --dir docs-site validate`, and `docs-site/dist` upload
- [x] T012 [US1] Add the dependent deploy job in `.github/workflows/deploy-docs.yml` with `github-pages` environment, `actions/deploy-pages`, page URL output, and no checkout, rebuild, or artifact upload
- [x] T013 [US1] Check `.github/workflows/deploy-docs.yml` against `specs/doc-011-github-pages-build-and-deploy-pipeline/contracts/deploy-docs-workflow.md` for validation-before-upload, standard Pages actions, and no broad deploy credentials

**Checkpoint**: User Story 1 is testable by workflow contract inspection.

---

## Phase 4: User Story 2 - Manually Retry A Deploy (Priority: P2)

**Goal**: Maintainers can manually dispatch a deploy retry without creating a source-only retry commit.

**Independent Test**: Verify `workflow_dispatch` uses the same validation, artifact, and deploy sequence as `push` runs and that staging concurrency supersedes older runs.

### Implementation for User Story 2

- [x] T014 [US2] Add `workflow_dispatch` to `.github/workflows/deploy-docs.yml` so manual retries use the same build/upload and deploy jobs as `push` runs
- [x] T015 [US2] Check retry and concurrency behavior in `.github/workflows/deploy-docs.yml` against `specs/doc-011-github-pages-build-and-deploy-pipeline/data-model.md`

**Checkpoint**: User Story 2 is testable by workflow trigger and concurrency inspection.

---

## Phase 5: User Story 3 - Preview Staging Without Public Discovery (Priority: P3)

**Goal**: Reviewers can preview the staging docs site while crawler discovery and indexing remain blocked until DOC-012.

**Independent Test**: Confirm the rendered pages receive one global noindex/nofollow guard and `robots.txt` contains the DOC-011 crawler policy.

### Implementation for User Story 3

- [x] T016 [P] [US3] Add one DOC-011 Starlight robots meta guard with `noindex, nofollow` and DOC-012 removal boundary in `docs-site/astro.config.mjs`
- [x] T017 [P] [US3] Create `docs-site/public/robots.txt` with exactly `User-agent: *` and `Disallow: /`
- [x] T018 [US3] Check staging indexing guard content in `docs-site/astro.config.mjs`, `docs-site/public/robots.txt`, and `docs-site/scripts/validate-docs-quality.mjs` against `specs/doc-011-github-pages-build-and-deploy-pipeline/quickstart.md`

**Checkpoint**: User Story 3 is testable by static file and config inspection.

---

## Phase 6: User Story 4 - Follow Deploy Setup And Recovery Runbook (Priority: P4)

**Goal**: Contributors and reviewers can follow a CI/CD runbook for Pages setup, validation, retry, rollback, deployment history, and DOC-012 handoff.

**Independent Test**: Open the runbook and confirm it explains the deploy trigger, validation gate, one-time Pages setting, retry path, rollback path, and DOC-012 staging-versus-launch boundary.

### Implementation for User Story 4

- [x] T019 [US4] Create or repair `docs/ai/specs/cicd-release-pipeline-verification.md` with Pages setup, validation gate, source ref/SHA evidence, artifact upload result, deploy result, deployed URL, retry, rollback, and DOC-012 handoff
- [x] T020 [US4] Document crawler-policy nuance and the GitHub Pages project-site `robots.txt` limitation in `docs/ai/specs/cicd-release-pipeline-verification.md`
- [x] T021 [US4] Update `CLAUDE.md` with concise Deploy Docs workflow guidance and a pointer to `docs/ai/specs/cicd-release-pipeline-verification.md`
- [x] T022 [US4] Check `CLAUDE.md` summarizes rather than duplicates the runbook and names `.github/workflows/deploy-docs.yml`

**Checkpoint**: User Story 4 is testable by runbook and CLAUDE guidance inspection.

---

## Phase 7: Validation and Reviewability Evidence

**Purpose**: Validate the one vertical slice and prepare review evidence.

- [x] T023 Run `pnpm --dir docs-site install --frozen-lockfile` for `docs-site/package.json`
- [x] T024 Run `pnpm --dir docs-site exec playwright install --with-deps chromium` for `docs-site/package.json` smoke prerequisites
- [x] T025 Remove `docs-site/dist` and run `pnpm --dir docs-site validate` for `docs-site/package.json`
- [x] T026 Check `.github/workflows/deploy-docs.yml` for no `${{ secrets.* }}`, no custom `token:`, no broad write permissions, and no `continue-on-error`
- [x] T027 Check changed files stay within declared operations in `specs/doc-011-github-pages-build-and-deploy-pipeline/plan.md` and update `specs/doc-011-github-pages-build-and-deploy-pipeline/tasks.md` task states as work completes
- [x] T028 Prepare PR review packet content from `specs/doc-011-github-pages-build-and-deploy-pipeline/spec.md`, `specs/doc-011-github-pages-build-and-deploy-pipeline/plan.md`, `specs/doc-011-github-pages-build-and-deploy-pipeline/quickstart.md`, and validation evidence

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup and Source Inspection (Phase 1)**: No dependencies; start here.
- **Foundational Scope Checks (Phase 2)**: Depends on Phase 1; blocks implementation.
- **User Story 1 (Phase 3)**: Depends on Phase 2; creates the deploy workflow.
- **User Story 2 (Phase 4)**: Depends on the workflow file from User Story 1.
- **User Story 3 (Phase 5)**: Depends on Phase 2; can be implemented after source inspection, but must ship with the workflow.
- **User Story 4 (Phase 6)**: Depends on the workflow and indexing-guard decisions from User Stories 1-3.
- **Validation and Reviewability Evidence (Phase 7)**: Depends on all implementation phases.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Phase 2.
- **User Story 2 (P2)**: Depends on User Story 1 because it extends the same deploy workflow.
- **User Story 3 (P3)**: Starts after Phase 2 and can proceed independently of User Story 2.
- **User Story 4 (P4)**: Depends on User Stories 1 and 3 so the runbook documents the implemented workflow and guard.

### Parallel Opportunities

- T001-T004 can run in parallel because they inspect different files.
- T003 and T004 can continue while workflow source inspection happens.
- T016 and T017 touch different docs-site paths and can run in parallel after Phase 2.
- User Story 3 can proceed while User Story 2 workflow retry checks are completed.

---

## Parallel Example: Setup Inspection

```text
Task: "Inspect docs validation and package-manager commands in docs-site/package.json before writing .github/workflows/deploy-docs.yml"
Task: "Inspect existing GitHub Actions conventions in .github/workflows/pr-checks.yml and .github/workflows/release.yml before writing .github/workflows/deploy-docs.yml"
Task: "Inspect existing Starlight config shape in docs-site/astro.config.mjs before adding the DOC-011 robots head guard"
Task: "Inspect existing agent CI/CD guidance in CLAUDE.md before adding the DOC-011 deploy pointer"
```

## Parallel Example: Staging Guard

```text
Task: "Add one DOC-011 Starlight robots meta guard with noindex, nofollow and DOC-012 removal boundary in docs-site/astro.config.mjs"
Task: "Create docs-site/public/robots.txt with exactly User-agent: * and Disallow: /"
```

---

## Implementation Strategy

### Incremental Delivery

### DOC-011 Vertical Slice

1. Complete Phase 1 source inspection and Phase 2 scope checks.
2. Implement User Story 1 workflow deployment and User Story 2 manual retry support in `.github/workflows/deploy-docs.yml`.
3. Implement User Story 3 noindex and robots staging guard.
4. Implement User Story 4 runbook and CLAUDE guidance.
5. Run Phase 7 validation and prepare PR reviewability evidence.

### MVP Scope

DOC-011 MVP is the full vertical slice through User Stories 1-4. Do not treat User Story 1 alone as merge-ready because a staging deploy without indexing protection and runbook guidance violates the DOC-011 scope.

### Review Strategy

Review in this order:

1. `.github/workflows/deploy-docs.yml`
2. `docs-site/astro.config.mjs`
3. `docs-site/public/robots.txt`
4. `docs-site/scripts/validate-docs-quality.mjs`
4. `docs/ai/specs/cicd-release-pipeline-verification.md`
5. `CLAUDE.md`
6. `specs/doc-011-github-pages-build-and-deploy-pipeline/tasks.md`

### Notes

- `[P]` tasks use different files and have no dependency on incomplete edits.
- `[US1]`, `[US2]`, `[US3]`, and `[US4]` labels map to the user stories in `spec.md`.
- Keep all GitHub Pages repository settings manual; do not add CLI or API automation for Pages setup.
- Keep DOC-012 launch work deferred; do not remove the noindex guard or change custom-domain/base-path assumptions.
