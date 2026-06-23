# SpecKit Workflow: DOC-011 - GitHub Pages Build-and-Deploy Pipeline

**Template Version**: 1.0.0
**Created**: 2026-06-22
**Purpose**: Prepare DOC-011 for autonomous execution from the interactive documentation roadmap and the setup Grill Me decisions.

---

## How to Use This Workflow

Run this workflow from the DOC-011 worktree:

```bash
$speckit-autopilot docs/ai/specs/.process/DOC-011-workflow.md
```

This file is already populated for DOC-011. Do not replace it with the generic workflow template.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during `$speckit-scaffold-spec DOC-011`.
The full Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/DOC-011-design-concept.md
```

Re-read the design concept before each phase. It is the source of truth for setup decisions:

- Deliver the Pages deploy workflow, staging noindex guard, and runbook notes together.
- Trigger deployment from `main` and `workflow_dispatch`; use broad path coverage so docs-impacting changes are not missed.
- Gate deployment on `pnpm --dir docs-site validate`.
- Use least-privilege Pages deploy permissions and a `github-pages` environment.
- Create the missing CI/CD verification runbook instead of leaving the roadmap/CLAUDE pointer broken.
- Keep DOC-011 as one vertical slice.

> Grill Me is human-in-the-loop only. It is not part of the autopilot loop. Once this workflow starts, clarifications happen through `$speckit-clarify` and consensus, never through grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `$speckit-specify` | Complete | Created spec.md and requirements checklist; G1 passed with 0 clarification markers |
| Clarify | `$speckit-clarify` | Complete | Resolved trigger paths, validation/artifact setup, staging visibility, Pages setup wording, and runbook split |
| Plan | `$speckit-plan` | Complete | Created plan/research/data-model/quickstart/workflow contract; G3 passed; reviewability estimate under budget |
| Checklist | `$speckit-checklist` | Complete | reliability/security/integration/maintainability complete; G4 passed with 0 gap markers |
| Tasks | `$speckit-tasks` | Complete | Generated 28 task lines with 7 parallel markers; G5 passed |
| Analyze | `$speckit-analyze` | Complete | Remediated one HIGH spec conflict; G6 passed with 0 findings |
| Implement | `$speckit-implement` | Complete | DOC-011 workflow, staging guard, runbook, CLAUDE.md pointer, and validation evidence complete |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | Requirements cover deploy workflow, noindex guard, runbook, Pages setting note, and do not include DOC-012 launch work |
| G2 | After Clarify | Broad path filter, browser install/setup, and one-time Pages setting wording are resolved |
| G3 | After Plan | Constitution gates pass and reviewability budget remains within the single-slice plan |
| G4 | After Checklist | All true gaps are remediated or explicitly scoped out with rationale |
| G5 | After Tasks | Tasks cover every user story and keep deploy/runbook/noindex work in one coherent review path |
| G6 | After Analyze | No critical drift between design concept, spec, plan, and tasks |
| G7 | After Implementation | Docs validation, workflow lint/review, spec-map check, and relevant repo tests pass |

---

## Prerequisites

### Worktree and Branch

- Worktree: `.worktrees/doc-011-github-pages-build-and-deploy-pipeline`
- Branch: `doc-011-github-pages-build-and-deploy-pipeline`
- Contract marker: `specs/doc-011-github-pages-build-and-deploy-pipeline/SPEC-MOC.md`
- Design concept: `docs/ai/specs/.process/DOC-011-design-concept.md`

Before starting:

```bash
git rev-parse --abbrev-ref HEAD
git status --short
specify preset resolve spec-template
specify preset resolve plan-template
specify preset resolve tasks-template
```

Expected branch is `doc-011-github-pages-build-and-deploy-pipeline`. Preset resolution should use `.specify/presets/speckit-pro-reviewability/` unless a deliberate higher-priority override exists.

### Constitution Validation

| Principle | DOC-011 Requirement | Verification |
|-----------|---------------------|--------------|
| Plugin Structure Compliance | Keep plugin runtime behavior unchanged; DOC-011 may reference plugin/generated sources only as docs reference inputs | `git diff --name-only` review |
| Script Safety | Any shell in workflow steps must use straightforward Bash and avoid unsafe interpolation | workflow source review |
| Test Coverage Before Merge | Pages deployment must be gated by existing docs validation and relevant repo checks | `pnpm --dir docs-site validate`, workflow review, relevant SpecKit checks |
| Conventional Commits | PR title and commits must use public-readable conventional commit text | PR Checks `validate-pr-title` |
| KISS, Simplicity, YAGNI | Use GitHub's standard Pages actions and existing docs-site validation; no custom deploy script unless required | Plan complexity table and code review |

### Existing Source Truth

- Roadmap: `docs/ai/specs/interactive-documentation-technical-roadmap.md`
- Product requirement: `docs/prd-interactive-documentation.md`
- Docs stack decision: `docs/ai/research/interactive-documentation-framework-spike.md`
- Current docs site config: `docs-site/astro.config.mjs`
- Current docs validation path: `docs-site/package.json`
- Current PR Checks workflow: `.github/workflows/pr-checks.yml`
- Current Release workflow: `.github/workflows/release.yml`
- Current CI/CD notes: `CLAUDE.md`

### Reviewability Budget

Setup gate output:

```json
{"mode":"setup","status":"warn","pass":true,"reviewable_loc":30,"production_files":0,"total_files":3,"primary_surface_count":5,"primary_surfaces":["docs/config","docs/content","docs/process","docs/UI","harness/CI"],"greenfield":false,"warnings":["primary surfaces 5 exceeds warn threshold 1"],"blockers":[]}
```

Grill Me slice-size estimator:

```json
{"estimated_loc":245,"suggested_slices":1,"status":"ok"}
```

The setup warning is non-blocking. Plan must record why DOC-011 remains one slice: deploy workflow, validation gate, noindex guard, and runbook notes form one observable staging capability.

---

## Specification Context

| Field | Value |
|-------|-------|
| Spec ID | DOC-011 |
| Name | GitHub Pages build-and-deploy pipeline |
| Branch | `doc-011-github-pages-build-and-deploy-pipeline` |
| Dependencies | DOC-010 complete and archived; docs site builds and validates |
| Enables | Staged noindex preview for DOC-013 through DOC-021; DOC-012 go-live |
| Priority | P1 |
| Primary surface | Harness/CI plus docs/process |

### Acceptance Criteria Summary

From the DOC-011 roadmap section:

- Deploy workflow exists at `.github/workflows/deploy-docs.yml`.
- Workflow uses GitHub Pages Actions: `actions/configure-pages`, `actions/upload-pages-artifact`, and `actions/deploy-pages`.
- Workflow has least-privilege permissions: `contents: read`, `pages: write`, and `id-token: write`.
- Workflow deploys to a `github-pages` environment and avoids overlapping deploy races with concurrency.
- Workflow triggers on `main` and `workflow_dispatch`, with broad enough path coverage to avoid missing docs-impacting changes.
- Workflow builds under Node >=22.12 with pnpm and gates upload/deploy on `pnpm --dir docs-site validate`.
- Pages one-time setup is documented; implementation does not automate repository admin settings.
- Staging search visibility is blocked with `robots.txt` disallow plus global noindex/nofollow meta in Starlight config.
- DOC-012 is the only spec allowed to remove noindex, attach `plugins.racecraft.co`, or flip to overt public launch.
- The missing CI/CD verification runbook is created and `CLAUDE.md` points to the correct deploy/runbook guidance.

### Scope

- Add `.github/workflows/deploy-docs.yml`.
- Add or update docs-site config/static files needed for the staging noindex guard.
- Create `docs/ai/specs/cicd-release-pipeline-verification.md` if still absent and add focused Pages deployment setup/recovery steps.
- Update `CLAUDE.md` CI/CD guidance for Pages deploy behavior and one-time setup.
- Keep `docs-site/package.json` validation semantics unless Plan finds a minimal CI-only setup command is required for Playwright browsers.
- Keep broad deploy trigger coverage per Q6, but make the exact `paths:` list intentional and reviewable.

### Out of Scope

- Custom domain, DNS, or base-path migration to `plugins.racecraft.co`.
- Removing noindex/robots disallow.
- Branding, SEO metadata, social cards, sitemap/llms.txt, analytics, Lighthouse CI, or branded 404.
- Plugin runtime behavior, generated payload semantics, marketplace versioning, or release-please behavior.
- GitHub API/CLI mutation of repository Pages settings.

---

## Phase 1: Specify

**When to run:** At the start of the new feature specification. Focus on what and why. Output: `specs/doc-011-github-pages-build-and-deploy-pipeline/spec.md`.

### Specify Prompt

```bash
$speckit-specify

## Feature: GitHub Pages build-and-deploy pipeline

### Problem Statement
The Astro/Starlight docs site exists and passes `pnpm --dir docs-site validate`, but it has never shipped to a live URL. There is no `.github/workflows/deploy-docs.yml`, GitHub Pages is not documented as enabled from Actions, and the repository still references a missing CI/CD verification runbook. DOC-011 must make the docs reachable at the staging github.io URL while preserving the public-exposure policy: previewable for maintainers, not indexed or discoverable until DOC-012.

### Users
- Maintainers who need an automatic Pages deployment after docs-impacting changes reach `main`.
- Reviewers who need a staging URL for DOC-013 through DOC-021 work.
- Contributors who need a documented deploy setup/recovery path.
- Future launch operators who need a clear boundary between staging deploy and DOC-012 public go-live.

### User Stories
1. As a maintainer, I can merge docs-impacting changes to `main` and have GitHub Actions validate and deploy the docs site to GitHub Pages.
2. As a maintainer, I can manually dispatch the deploy workflow to recover from transient Pages or Actions failures.
3. As a launch operator, I can preview the staging site while search indexing is blocked until DOC-012 removes the guard.
4. As a contributor or reviewer, I can read a CI/CD verification runbook that explains the deploy workflow, one-time Pages setting, validation gate, and rollback/retry path.

### Functional Requirements
- Add `.github/workflows/deploy-docs.yml` using standard GitHub Pages Actions.
- The workflow must use least-privilege permissions: `contents: read`, `pages: write`, and `id-token: write`.
- The workflow must deploy through a `github-pages` environment and use concurrency to avoid overlapping deploys.
- The workflow must trigger on `workflow_dispatch` and on `push` to `main` with broad path coverage that avoids missing docs-impacting changes.
- The workflow must install Node >=22.12 and pnpm 10.25.0, install docs-site dependencies with the lockfile, run `pnpm --dir docs-site validate`, then upload the built site artifact.
- The deploy artifact path must match the Astro output for `docs-site/`.
- Add staging indexing protection: `docs-site/public/robots.txt` disallow plus a global Starlight/Astro noindex/nofollow meta guard.
- Document that DOC-012 removes the noindex guard and performs the custom-domain/base-path launch.
- Create or repair `docs/ai/specs/cicd-release-pipeline-verification.md` with Pages setup, verification, retry, and rollback notes.
- Update `CLAUDE.md` CI/CD guidance so future agents understand the deploy workflow and runbook path.

### Constraints
- Use the existing Astro/Starlight docs site and `docs-site/package.json` validation path.
- Do not automate GitHub repository Pages settings through CLI/API.
- Do not remove the existing `site` and `base` assumptions; DOC-012 owns final-domain migration.
- Do not introduce a custom deployment script unless GitHub's standard Pages actions cannot satisfy the spec.
- Keep the diff reviewable; if Plan discovers workflow/browser setup expands the slice, trim path-filter or runbook scope before splitting.

### Out of Scope
- Custom domain/DNS/final base path.
- SEO, sitemap, social cards, analytics, branding, Lighthouse CI.
- Plugin runtime behavior, release publication semantics, and repository Pages settings automation.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 18 |
| User Stories | 4 |
| Acceptance Criteria | 9 |

### Files Generated

- [x] `specs/doc-011-github-pages-build-and-deploy-pipeline/spec.md`
- [x] `specs/doc-011-github-pages-build-and-deploy-pipeline/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** After Specify if any implementation-affecting ambiguity remains. Keep each session targeted.

### Clarify Prompts

#### Session 1: Deploy trigger and changed paths

```bash
$speckit-clarify Focus on DOC-011 deploy trigger coverage: define the exact `paths:` list for `deploy-docs.yml`, preserving the user's Q6 choice to prefer broad coverage over missed docs-impacting deploys while avoiding clearly irrelevant archive/test-fixture churn.
```

#### Session 2: Pages validation and artifact setup

```bash
$speckit-clarify Focus on the Pages workflow implementation: confirm Node/pnpm setup, dependency install command, whether Playwright browsers must be installed for `pnpm --dir docs-site validate`, the Astro build output path, and the correct order for configure-pages/upload-pages-artifact/deploy-pages.
```

#### Session 3: Public exposure and runbook wording

```bash
$speckit-clarify Focus on staging visibility and operator documentation: define the exact noindex/nofollow meta shape, `robots.txt` contents, DOC-012 removal note, one-time GitHub Pages setting wording, retry/rollback steps, and how CLAUDE.md should summarize the deploy workflow without duplicating the runbook.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Deploy trigger and changed paths | 5 | Use explicit `push.paths`; include generated-reference sources, plugin surfaces, dist payloads, and `tests/speckit-pro/**`; exclude fixture-heavy test paths and non-rendered process/archive churn with ordered `!` patterns. |
| 2 | Pages validation and artifact setup | 5 | Use Node 22, Corepack pnpm 10.25.0, `pnpm --dir docs-site install --frozen-lockfile`, Chromium-only Playwright install, `pnpm --dir docs-site validate`, upload `docs-site/dist`, and deploy from a dependent Pages job. |
| 3 | Public exposure and runbook wording | 5 | Use one Starlight robots meta entry, `robots.txt` with `User-agent: *` and `Disallow: /`, DOC-012 removal notes near both guards, manual Pages Source = GitHub Actions setup wording, full operator steps in runbook with concise `CLAUDE.md` pointer. |

### Consensus Resolution Log

| Round | Routed Categories | Outcome | Analysts Used |
|-------|-------------------|---------|---------------|
| 1 | `[codebase, spec]` | Include `tests/speckit-pro/**` because generated reference docs consume test harness files; add fixture-heavy exclusions as a pragmatic noise filter, with the tradeoff documented. | codebase-analyst, spec-context-analyst |
| 1 | `[domain, spec]` | Use `User-agent: *` plus `Disallow: /` for `docs-site/public/robots.txt`; document that on project Pages this is policy/signaling and page-level `noindex,nofollow` is the primary rendered-page guard. | domain-researcher, spec-context-analyst |
| 1 | `[security, domain]` | Document manual Pages setup only: Settings -> Pages -> Build and deployment -> Source = GitHub Actions; do not use branch publishing or CLI/API mutation; deploy through `github-pages`. | codebase-analyst, spec-context-analyst, domain-researcher |
| 1 | `[security, domain]` | Security checklist credential boundary approved: prohibit secret-backed or custom deploy credentials and broad write scopes while allowing the standard GitHub-provided workflow token/OIDC flow. | codebase-analyst, spec-context-analyst, domain-researcher |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/doc-011-github-pages-build-and-deploy-pipeline/plan.md` and supporting artifacts.

### Plan Prompt

```bash
$speckit-plan

## Tech Stack
- Docs site: Astro 6.4.6 and Starlight 0.40.0 under `docs-site/`.
- Package manager: pnpm 10.25.0 from `docs-site/package.json`.
- Runtime: Node >=22.12 in GitHub Actions.
- CI/CD: GitHub Actions, existing PR Checks workflow, existing Release workflow, new Pages deploy workflow.
- Validation: `pnpm --dir docs-site validate`.

## Source Evidence
- Roadmap: `docs/ai/specs/interactive-documentation-technical-roadmap.md` DOC-011.
- Design concept: `docs/ai/specs/.process/DOC-011-design-concept.md`.
- Product requirement: `docs/prd-interactive-documentation.md`.
- Docs stack decision: `docs/ai/research/interactive-documentation-framework-spike.md`.
- Current docs config: `docs-site/astro.config.mjs`.
- Current docs scripts and package manager: `docs-site/package.json`.
- Existing workflows: `.github/workflows/pr-checks.yml`, `.github/workflows/release.yml`.
- Project guidance: `CLAUDE.md`.

## Architecture Notes
- Use standard GitHub Pages Actions; do not invent a custom deploy script.
- Keep Pages settings as operator documentation, not an API mutation.
- Preserve the staging URL and noindex guard until DOC-012.
- Treat the missing CI/CD verification runbook as part of DOC-011 scope.
- Translate Q6's "Broad repo paths" answer into explicit workflow paths and explain the tradeoff.
- Record the setup gate warning: primary surface count exceeded warn threshold, but the slice remains one deploy-ready capability.

## Expected Artifacts
- `.github/workflows/deploy-docs.yml`
- `docs-site/public/robots.txt`
- `docs-site/astro.config.mjs`
- `docs/ai/specs/cicd-release-pipeline-verification.md`
- `CLAUDE.md`
- Any minimal spec/process artifacts under `specs/doc-011-github-pages-build-and-deploy-pipeline/`
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Technical context, declared file operations, constitution check, reviewability WARN rationale |
| `research.md` | Complete | GitHub Pages, Astro artifact path, Playwright, path filters, noindex/robots decisions |
| `data-model.md` | Complete | Configuration artifacts and operator-state relationships |
| `contracts/` | Complete | `deploy-docs-workflow.md` workflow/runbook contract |
| `quickstart.md` | Complete | Maintainer verification commands and setup notes |

Plan reviewability estimate:

```json
{"tool":"estimate-reviewable-loc","status":"pass","projected":40,"declared_files":{"production":1,"new":3,"modified":2,"total_entries":5}}
```

---

## Phase 4: Domain Checklists

**When to run:** After Plan validates both spec and plan together.

### Recommended Checklist Domains

#### Reliability / Observability

```bash
$speckit-checklist reliability

Focus on DOC-011 requirements:
- Deploy retry path through `workflow_dispatch`.
- Concurrency behavior for overlapping Pages deploys.
- Failure visibility when validation, artifact upload, or deploy fails.
- Runbook recovery and rollback notes.
- Pay special attention to: avoiding a successful deploy of stale or unvalidated docs output.
```

#### Security

```bash
$speckit-checklist security

Focus on DOC-011 requirements:
- Least-privilege Actions permissions.
- No repository admin mutation through CLI/API.
- No secrets or broad token permissions.
- Staging noindex/nofollow and robots disallow guard.
- Pay special attention to: preserving DOC-012 as the only public launch gate.
```

#### Docs Operations

```bash
$speckit-checklist integration

Focus on DOC-011 docs operations requirements:
- Pages workflow integrates with existing docs-site pnpm scripts.
- Broad path trigger covers generated-reference inputs without making the workflow unreadable.
- Runbook and CLAUDE.md guidance agree with the workflow.
- Pay special attention to: the missing CI/CD verification runbook path and the one-time Pages setting.
```

#### Maintainability

```bash
$speckit-checklist maintainability

Focus on DOC-011 requirements:
- The workflow is small, standard, and reviewable.
- No custom deployment helper is added unless clearly justified.
- The noindex guard is easy for DOC-012 to remove.
- Pay special attention to: avoiding duplicated long-form runbook content in `CLAUDE.md`.
```

### Checklist Results

| Domain | Status | Gap Count | Notes |
|--------|--------|-----------|-------|
| reliability | Complete | 8 remediated, 0 remaining | Added same-run validation/artifact provenance, fixed concurrency group, failure visibility, retry-vs-rollback, deployment history, and stale-output assumptions. |
| security | Complete | 1 remediated, 0 remaining | Added explicit credential/token boundary: no secrets, deploy keys, PATs, GitHub App tokens, custom token inputs, or broad write permissions; default GitHub token/OIDC remains allowed for standard Pages Actions. |
| integration | Complete | 0 | No gaps; docs-site validation, generated-reference path coverage, runbook repair, `CLAUDE.md` pointer, one-time Pages setting, and DOC-012 boundary are already covered. |
| maintainability | Complete | 0 | No gaps; standard Pages workflow, no custom helper, easy DOC-012 guard removal, and concise `CLAUDE.md` pointer already covered. |

---

## Phase 5: Tasks

**When to run:** After checklists complete and all real gaps are resolved. Output: `specs/doc-011-github-pages-build-and-deploy-pipeline/tasks.md`.

### Tasks Prompt

```bash
$speckit-tasks

Generate tasks for DOC-011 using:
- `specs/doc-011-github-pages-build-and-deploy-pipeline/spec.md`
- `specs/doc-011-github-pages-build-and-deploy-pipeline/plan.md`
- `docs/ai/specs/.process/DOC-011-design-concept.md`

Preserve these scoping decisions:
- One vertical slice.
- Deploy workflow, noindex guard, runbook, and CLAUDE update stay together.
- Use standard GitHub Pages Actions.
- Gate deploy on `pnpm --dir docs-site validate`.
- Keep broad path coverage per Q6.
- Do not automate GitHub repo Pages settings.
- Do not implement DOC-012 custom domain or remove noindex.

Task ordering should start with tests/checks and source inspection, then workflow/noindex/runbook edits, then validation and reviewability evidence.
```

### Expected Task Groups

1. Source inspection and validation baseline.
2. Pages workflow implementation.
3. Staging noindex/robots guard.
4. CI/CD verification runbook and CLAUDE.md guidance.
5. Reviewability, spec-map, and final verification.

### Tasks Results

| Metric | Value |
|--------|-------|
| Task Count | 28 |
| Parallel-safe tasks | 7 |
| Reviewability Route | Task gate size-block recorded; marker plan generated; atomicity route one-navigable-PR |

### Post-G5 Reviewability Evidence

| Item | Result |
|------|--------|
| Task Reviewability Gate | `status=block`, `mode=tasks`, size-only proceed; evidence `specs/doc-011-github-pages-build-and-deploy-pipeline/.process/reviewability/tasks-gate.json` |
| Atomicity Route | `one-navigable-PR`, releasable, signal `change-shape:modify-heavy`; evidence `specs/doc-011-github-pages-build-and-deploy-pipeline/.process/reviewability/atomicity-route.json` |
| Layer Plan | Skipped because route is not `split-PR` |
| PR Marker Plan | Generated 5 markers: `foundation`, `us1`, `us2`, `us3`, `us4`; evidence `specs/doc-011-github-pages-build-and-deploy-pipeline/.process/reviewability/pr-marker-plan.json` |

The task gate block is treated as marker-planning input, not a manual stop, because it is size-only and has current feature evidence.

---

## Phase 6: Analyze

**When to run:** After tasks are generated. Output should identify artifact drift before implementation.

### Analyze Prompt

```bash
$speckit-analyze

Analyze DOC-011 for cross-artifact consistency across:
- `docs/ai/specs/.process/DOC-011-design-concept.md`
- `specs/doc-011-github-pages-build-and-deploy-pipeline/spec.md`
- `specs/doc-011-github-pages-build-and-deploy-pipeline/plan.md`
- `specs/doc-011-github-pages-build-and-deploy-pipeline/tasks.md`

Focus on:
- Any drift from the user's Q6 answer to use broad deploy path coverage.
- Any accidental inclusion of DOC-012 custom-domain or launch work.
- Any missing noindex/nofollow or robots guard.
- Any workflow permission broader than Pages deploy requires.
- Any hidden dependency on admin/API mutation for Pages settings.
- Any task list that omits runbook creation for the currently missing CI/CD verification file.
```

### Analyze Results

| Finding Level | Count | Notes |
|---------------|-------|-------|
| Critical | 0 | |
| High | 1 remediated | `robots.txt` exact two-line content conflicted with a requirement to place DOC-012 removal wording in the file; spec now keeps `robots.txt` exact and moves DOC-012 boundary wording to runbook/meta guidance. |
| Medium | 0 | |
| Low | 0 | |

### Pre-Implement Confidence

📊 Confidence: 0.94

- Task understanding: 0.96
- Approach clarity: 0.94
- Requirements alignment: 0.93
- Risk assessment: 0.94
- Completeness: 0.93

Rationale: G1-G6 passed, checklist/analyze findings are remediated, the task gate size block has current marker-plan evidence, and implementation tasks map to the declared DOC-011 file operations.

---

## Phase 7: Implement

**When to run:** After Analyze passes and the user approves implementation.

### Implement Prompt

```bash
$speckit-implement

Implement DOC-011 on branch `doc-011-github-pages-build-and-deploy-pipeline`.

Before editing:
1. Re-read `docs/ai/specs/.process/DOC-011-design-concept.md`.
2. Re-read `specs/doc-011-github-pages-build-and-deploy-pipeline/tasks.md`.
3. Confirm the worktree branch with `git rev-parse --abbrev-ref HEAD`.

Implementation constraints:
- Add `.github/workflows/deploy-docs.yml` using GitHub's standard Pages actions.
- Use least-privilege permissions and concurrency.
- Gate deploy on `pnpm --dir docs-site validate`.
- Add staging noindex/nofollow and robots disallow.
- Create/update `docs/ai/specs/cicd-release-pipeline-verification.md`.
- Update `CLAUDE.md` with a concise CI/CD note.
- Do not automate Pages repo settings.
- Do not include DOC-012 launch/domain work.

Verification should include:
- `pnpm --dir docs-site validate` when dependencies are available.
- Workflow YAML/source review for permissions, trigger, environment, and artifact path.
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
- `git diff --check`
- Relevant SpecKit structural checks if workflow/docs changes touch guarded paths.
```

### Implementation Results

| Area | Status | Evidence |
|------|--------|----------|
| Deploy workflow | Complete | Added `.github/workflows/deploy-docs.yml` with `push` to `main`, `workflow_dispatch`, explicit broad paths plus fixture exclusions, least-privilege Pages permissions, fixed staging concurrency, validate-before-upload build job, and dependent `github-pages` deploy job. |
| Noindex guard | Complete | Added one Starlight robots meta head entry with `noindex, nofollow` and DOC-012 removal comment; added `docs-site/public/robots.txt` with exactly `User-agent: *` and `Disallow: /`; extended docs-quality validation to enforce both guard surfaces. |
| Runbook and CLAUDE.md | Complete | Created `docs/ai/specs/cicd-release-pipeline-verification.md` with Pages setup, validation, retry, rollback, deployment-history, crawler-policy, and DOC-012 handoff; updated `CLAUDE.md` with a concise deploy pointer. |
| Validation | Complete | `actionlint .github/workflows/*.yml`; `pnpm --dir docs-site install --frozen-lockfile`; `pnpm --dir docs-site exec playwright install --with-deps chromium`; `pnpm --dir docs-site validate:quality`; `pnpm --dir docs-site validate` passed after rerun with elevated permissions because sandbox blocked localhost preview binding. |

### Post-Implementation Checklist

| Task | Status | Findings | Action Needed |
|------|--------|----------|---------------|
| Doctor Extension Check | Complete with advisory | Templates, scripts, constitution, feature artifacts, and Claude command registration are present. The stock `.specify/scripts/bash/check-prerequisites.sh` rejected the `doc-011-...` branch because it expects numeric branch prefixes; the autopilot wrapper already accepted this DOC worktree. | None for DOC-011; keep the branch-name advisory visible. |
| Verify Implementation | Complete | 28/28 tasks complete, 17 referenced project paths checked, 0 missing project paths. Requirements are represented by the deploy workflow, staging guard, docs-quality assertions, runbook, CLAUDE.md pointer, and validation evidence. | None. |
| Verify Tasks Phantom Check | Complete | `specs/doc-011-github-pages-build-and-deploy-pipeline/verify-tasks-report.md` reports 28 verified tasks and no flagged items. | None. |
| Code Review | Skipped | Review extension is not installed. Self-review remains in the serial post-implementation tail. | Run manual self-review before PR creation. |
| Integration Suite | Complete | `bash tests/speckit-pro/run-all.sh` passed `3478/3478`. | None. |
| UAT Runbook | Complete | Generated `specs/doc-011-github-pages-build-and-deploy-pipeline/.process/uat-runbook.md` for PR packet inclusion. | None. |

### Self-Review

- Checked `.github/workflows/deploy-docs.yml` for the required push/manual triggers, explicit broad paths, ordered fixture exclusions, least-privilege Pages permissions, fixed concurrency, validate-before-upload ordering, same-run `docs-site/dist` artifact upload, and deploy-only `github-pages` job.
- Checked staging protection in source, docs-quality assertions, and generated output: `docs-site/public/robots.txt` has exactly the two required policy lines, and built HTML contains the `noindex, nofollow` meta guard.
- Checked runbook and CLAUDE guidance for manual Pages setup, retry/rollback distinction, deployment-history evidence, crawler-policy nuance, and DOC-012 launch boundary.
- No blocking self-review findings remain.

### PR Emission

| Area | Status | Evidence |
|------|--------|----------|
| Final reviewability backstop | Complete | `specs/doc-011-github-pages-build-and-deploy-pipeline/.process/final-reviewability/gate-state.json` records a size-only block for 54 files, one `full-spec` marker, and the `hazard_collapsed` route. |
| PR packet and workflow contract | Complete | `validate-pr-packet.sh specs/doc-011-github-pages-build-and-deploy-pipeline/.process/pr-packet/speckit-pr-packet.json` passed; `validate-pr-workflow-contract.sh --title "docs(DOC-011): add GitHub Pages deploy pipeline" --changed-files specs/doc-011-github-pages-build-and-deploy-pipeline/.process/emission/changed-files.txt` passed. |
| GitHub PR | Opened | PR #243: https://github.com/racecraft-lab/racecraft-plugins-public/pull/243 from `doc-011-github-pages-build-and-deploy-pipeline` into `main`; initial GitHub checks were queued/in progress at creation. |

---

## Expected File Tree

```text
.github/
  workflows/
    deploy-docs.yml
docs-site/
  astro.config.mjs
  public/
    robots.txt
docs/
  ai/
    specs/
      .process/
        DOC-011-design-concept.md
        DOC-011-workflow.md
      cicd-release-pipeline-verification.md
specs/
  doc-011-github-pages-build-and-deploy-pipeline/
    SPEC-MOC.md
    spec.md
    plan.md
    tasks.md
```

---

## Ready for Autopilot

When the scaffold commit is pushed, start the workflow with:

```bash
$speckit-autopilot docs/ai/specs/.process/DOC-011-workflow.md
```

Template based on SpecKit best practices. Populated for DOC-011 from the interactive documentation roadmap and the DOC-011 design concept doc.

### PR packet validation events
- <!-- speckit-pro-pr-packet-validation:event-id=speckit-pr-packet --> Blocked PR packet validation for `speckit-pr-packet`; result `specs/doc-011-github-pages-build-and-deploy-pipeline/.process/pr-packets/speckit-pr-packet/validation.json`; rules: `unknown`.
