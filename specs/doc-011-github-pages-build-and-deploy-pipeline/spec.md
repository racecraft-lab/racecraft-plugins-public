# Feature Specification: GitHub Pages Build-And-Deploy Pipeline

**Feature Branch**: `doc-011-github-pages-build-and-deploy-pipeline`

**Created**: 2026-06-23

**Status**: Draft

**Input**: User description: "GitHub Pages build-and-deploy pipeline for the existing Astro/Starlight docs site, including staging deployment, indexing protection, CI/CD runbook repair, and future DOC-012 launch boundary."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deploy Docs After Main Merge (Priority: P1)

Maintainers can merge docs-impacting changes to `main` and receive an automatic staging deployment for the docs site after validation passes.

**Why this priority**: This is the core value of DOC-011: reviewers and maintainers need the docs reachable at a staging URL after approved changes land.

**Independent Test**: Can be tested by inspecting the deploy workflow contract and confirming it validates the docs site before publishing the docs build artifact to the staging Pages environment.

**Acceptance Scenarios**:

1. **Given** a docs-impacting change reaches `main`, **When** the deploy workflow runs, **Then** it validates the docs site before any deployment occurs.
2. **Given** validation succeeds on `main`, **When** the workflow reaches the deployment step, **Then** the docs site is published to the configured staging GitHub Pages environment.
3. **Given** validation fails on `main`, **When** the workflow runs, **Then** no new staging deployment is published.

---

### User Story 2 - Manually Retry A Deploy (Priority: P2)

Maintainers can manually dispatch the deploy workflow to recover from transient Pages, dependency installation, or Actions failures without creating a code-only retry commit.

**Why this priority**: Deployment recovery must be available when the source state is already correct but external service execution failed.

**Independent Test**: Can be tested by verifying the workflow exposes a main-only manual dispatch retry path with the same validation and deployment gates as the automatic path.

**Acceptance Scenarios**:

1. **Given** a transient deployment failure occurred on `main`, **When** a maintainer manually dispatches the deploy workflow from `main`, **Then** the workflow repeats validation and deploys only if validation passes.
2. **Given** a manual deploy is already in progress, **When** another deploy run starts for the same staging target, **Then** overlapping publication is prevented or superseded predictably.

---

### User Story 3 - Preview Staging Without Public Discovery (Priority: P3)

Launch operators and reviewers can preview the staging site while search indexing and crawler discovery remain blocked until DOC-012 removes the guard.

**Why this priority**: The staging site needs to be reachable for review, but the project explicitly defers public go-live and discoverability to DOC-012.

**Independent Test**: Can be tested by confirming the staging docs build exposes crawler-blocking policy and global noindex/nofollow guidance while keeping pages directly accessible to maintainers and reviewers.

**Acceptance Scenarios**:

1. **Given** the staging site is deployed, **When** a crawler requests indexing guidance, **Then** the site communicates that indexing is disallowed.
2. **Given** a reviewer opens a known staging URL, **When** the docs page loads, **Then** the page remains previewable while carrying noindex/nofollow protection.

---

### User Story 4 - Follow Deploy Setup And Recovery Runbook (Priority: P4)

Contributors and reviewers can read a CI/CD verification runbook that explains the deploy workflow, one-time Pages setting, validation gate, retry path, rollback path, and DOC-012 launch boundary.

**Why this priority**: The repository currently references a missing CI/CD verification runbook, and future DOC work needs a clear operating path.

**Independent Test**: Can be tested by opening the runbook and confirming it gives enough information to verify setup, recover failures, and understand what remains deferred to DOC-012.

**Acceptance Scenarios**:

1. **Given** a contributor needs to understand docs deployment, **When** they read the runbook, **Then** they can identify the deploy trigger, validation gate, Pages setting, retry path, rollback path, and staging-versus-launch boundary.
2. **Given** a future launch operator prepares DOC-012, **When** they read the DOC-011 runbook and guidance, **Then** they can see that custom-domain, base-path, and public indexing changes remain out of scope for DOC-011.

### Edge Cases

- A docs-impacting change outside `docs-site/src/content/docs/**` must still be eligible for automatic deployment if it can affect the rendered docs site.
- Multiple deploy runs for the same branch or environment must not publish overlapping artifacts unpredictably.
- A validation failure must leave the currently published staging site unchanged.
- A transient GitHub Pages or Actions failure on `main` must be recoverable through manual dispatch from `main` without changing source files.
- The staging site must remain directly previewable even while indexing and crawler discovery are blocked.
- The runbook must not imply that repository Pages settings are automated; maintainers perform one-time setup manually.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST define a docs deploy workflow at `.github/workflows/deploy-docs.yml`.
- **FR-002**: The deploy workflow MUST use least-privilege access limited to source read access, Pages publication access, and identity-token access required for Pages deployment.
- **FR-003**: The deploy workflow MUST publish through a `github-pages` deployment environment.
- **FR-004**: The deploy workflow MUST prevent overlapping deploys for the same staging publication target.
- **FR-005**: The deploy workflow MUST run automatically after pushes to `main` when files with plausible docs-site impact change.
- **FR-006**: The deploy workflow MUST support manual dispatch by maintainers from `main` for retrying the shared staging deployment.
- **FR-007**: The deploy workflow MUST install the repository's docs-site toolchain using the checked-in lockfile before validation.
- **FR-008**: The deploy workflow MUST validate the docs site with the existing docs validation path before uploading any deploy artifact.
- **FR-009**: The deploy workflow MUST upload the generated docs-site output that corresponds to the existing docs build output location.
- **FR-010**: The deploy workflow MUST use the standard GitHub Pages deployment path unless standard Pages deployment cannot satisfy a stated DOC-011 requirement.
- **FR-011**: The staging docs site MUST include crawler guidance that disallows indexing before DOC-012.
- **FR-012**: The staging docs site MUST include a global noindex/nofollow guard before DOC-012.
- **FR-013**: The feature MUST document that DOC-012 owns removal of the indexing guard and final custom-domain or base-path launch work.
- **FR-014**: The repository MUST provide or repair `docs/ai/specs/cicd-release-pipeline-verification.md` with Pages setup, verification, retry, and rollback notes.
- **FR-015**: `CLAUDE.md` CI/CD guidance MUST point future agents to the deploy workflow and CI/CD verification runbook.
- **FR-016**: The feature MUST NOT automate repository Pages settings through CLI or API.
- **FR-017**: The feature MUST preserve existing site and base assumptions until DOC-012.
- **FR-018**: The feature MUST avoid new custom deployment scripts unless standard Pages deployment cannot satisfy DOC-011.
- **FR-019**: The deploy workflow MUST NOT require or reference repository or organization secrets, deploy keys, personal access tokens, GitHub App installation tokens, or other long-lived deploy credentials; it MUST rely only on the GitHub-provided workflow token/OIDC flow with the explicit least-privilege permissions in FR-002.

### Clarifications

#### Deploy Trigger Coverage

- The deploy workflow MUST use an explicit `push.paths` list rather than triggering on every `main` push.
- The positive path list MUST cover rendered docs sources, docs-site validation/config files, generated-reference source inputs, marketplace manifests, plugin source surfaces, root scripts, and generated payload directories.
- The positive path list MUST include `tests/speckit-pro/**` because test harness files feed the generated tests reference page.
- The path list MUST use ordered negative `!` patterns for fixture-heavy test paths such as `tests/speckit-pro/**/fixtures/**`, `tests/speckit-pro/**/fixtures-codex/**`, and explicit layer7/layer8 fixture directories when those exclusions avoid deploy churn without hiding normal harness changes.
- The path list MUST exclude non-rendered process/archive state such as `docs/ai/specs/**`, `specs/**`, and `.specify/memory/**` unless a file is explicitly identified as a docs-site or generated-reference input.
- Negative exclusions MUST be encoded inside `paths:` after the relevant positive patterns; the workflow MUST NOT combine `paths` and `paths-ignore` for the same event.

#### Pages Validation And Artifact Setup

- The deploy workflow MUST use Node 22 and activate pnpm 10.25.0 through Corepack before installing dependencies.
- The deploy workflow MUST install docs-site dependencies with `pnpm --dir docs-site install --frozen-lockfile`.
- The deploy workflow MUST install only the Chromium Playwright browser/dependencies needed by the docs smoke test before running `pnpm --dir docs-site validate`.
- The deploy workflow MUST treat `pnpm --dir docs-site validate` as the build and quality gate before upload.
- The deploy workflow MUST upload `docs-site/dist` as the Pages artifact because the existing Astro config does not override the default output directory and `validate` already runs the docs build.
- The deploy workflow MUST keep build/upload and deploy as separate jobs where the deploy job depends on the validated build job.

#### Reliability, Retry, Failure Visibility, And Rollback

- The deploy workflow MUST apply the same dependency install, validation, clean build-output, artifact upload, and deploy sequence for both `push` and `workflow_dispatch` runs on `main`.
- A manually dispatched retry MUST create and validate a new artifact for the `main` ref; it MUST NOT deploy an artifact produced by an earlier workflow run or from an unmerged branch.
- The build/upload job MUST remove any pre-existing `docs-site/dist` before validation and MUST upload only the `docs-site/dist` generated after the current run's successful validation.
- The deploy job MUST depend on the build/upload job and MUST NOT checkout source, rebuild, or upload an artifact itself.
- The workflow MUST use one fixed staging concurrency group for `main` runs that target the `github-pages` publication environment and MUST set `cancel-in-progress: true` for those runs so a newer push or main-branch manual retry supersedes any older in-progress or pending staging deploy run.
- A manually dispatched non-`main` run MUST use no-op concurrency behavior that cannot cancel an in-progress `main` deploy.
- Dependency installation failure, validation failure, Pages artifact upload failure, and Pages deployment failure MUST surface as failed workflow steps/jobs without being masked by `continue-on-error` or unconditional success handling.
- The runbook MUST describe how to identify the source ref/SHA, validation result, artifact upload result, deploy result, and deployed URL from the workflow run summary/logs and GitHub deployment history.
- The runbook MUST distinguish retry from rollback: use `workflow_dispatch` from `main` for transient external failures when merged source remains correct; use a normal revert or fix-forward PR followed by a fresh deploy when bad source content was published.

#### Credential And Token Boundaries

- The deploy workflow MUST NOT reference `${{ secrets.* }}`, deploy keys, personal access tokens, GitHub App installation tokens, or custom `token:` inputs for the Pages deploy path.
- The deploy workflow MUST NOT request `contents: write`, `actions: write`, `deployments: write`, `pull-requests: write`, `packages: write`, or broad/default write permissions for DOC-011.
- The deploy workflow MUST use only the GitHub-provided workflow token/OIDC context made available by the explicit `contents: read`, `pages: write`, and `id-token: write` permissions.
- If a future implementation needs credentials beyond the standard GitHub Pages Actions path, that work is out of scope for DOC-011 and MUST be handled by a later spec before implementation.

#### Staging Visibility And Operator Documentation

- The noindex guard MUST be a single Starlight `head` entry equivalent to `{ tag: 'meta', attrs: { name: 'robots', content: 'noindex, nofollow' } }`.
- `docs-site/public/robots.txt` MUST contain exactly `User-agent: *` and `Disallow: /`.
- The runbook MUST explain that, on a GitHub Pages project site, `robots.txt` is policy/signaling because crawlers look for it at the host root, while the rendered-page `noindex,nofollow` meta tag is the primary DOC-011 guard.
- The runbook MUST phrase crawler behavior accurately: `robots.txt` blocks crawling, while `noindex` blocks indexing when crawlers can see the page.
- The noindex meta entry and runbook MUST identify DOC-012 as the spec that removes staging indexing protection for launch; `robots.txt` MUST remain the exact two-line crawler policy and the runbook MUST document its DOC-012 removal boundary.
- The one-time Pages setup guidance MUST say: in GitHub repository settings, go to `Settings -> Pages -> Build and deployment`, set `Source` to `GitHub Actions`, do not select branch-based publishing, and verify the workflow deploys through the `github-pages` environment.
- The runbook MUST carry the full setup, retry, rollback, deployment-history, and DOC-012 handoff steps; `CLAUDE.md` MUST only summarize the workflow and point to the runbook.

### Reviewability Notes *(if applicable)*

- Final file operations include creating one deploy workflow, adding PR workflow lint coverage, extending PR Checks docs/workflow detection, aligning release PR docs-reference regeneration with Node 22, adding staging indexing protection in docs-site public/head configuration, repairing one CI/CD verification runbook, updating `CLAUDE.md`, hardening the shared spec-index roadmap-MOC guard with synced `dist/` copies and focused tests, and updating DOC-011 process artifacts.
- No plugin runtime behavior, release publication semantics, repository Pages settings automation, custom domain setup, SEO launch work, analytics, social cards, or Lighthouse CI changes are included.
- The release workflow change is limited to checked-in docs-reference regeneration/runtime alignment for release PRs; it does not change release publication semantics.
- The shared spec-index generator hardening was added during PR review because DOC-011 touched generated reference inputs and exposed a stale roadmap-MOC guard case.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: infra, harness/CI, shared SpecKit generator maintenance
- **Final production reviewable LOC**: 36 according to the production-only reviewability gate
- **Final production files**: 2 according to the production-only reviewability gate
- **Final total files**: 54
- **Budget result**: size-blocked by total-file count; final marker emission proceeds as one atomic PR marker with explicit evidence
- **Split decision**: Remains one PR because the deploy workflow, workflow validation, release docs-reference runtime alignment, staging indexing guard, runbook repair, generator guard fix, and agent guidance now form one already-reviewed staging-deploy/review-remediation slice. Splitting after PR review would misrepresent the coupled validation and evidence refresh.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name DOC-012 for public launch, indexing, custom-domain, and base-path migration work.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Maintainers can identify a single deploy workflow that validates and publishes the docs staging site after docs-impacting changes reach `main`.
- **SC-002**: Maintainers can manually retry the deploy workflow without creating a source-only retry commit.
- **SC-003**: Reviewers can reach a staging docs URL after a successful deploy while the site still communicates non-indexing policy to crawlers.
- **SC-004**: Contributors can use the CI/CD verification runbook to identify the Pages setup prerequisite, validation command, retry procedure, rollback procedure, and DOC-012 handoff in under 5 minutes.
- **SC-005**: The DOC-011 review packet can trace every deployment, indexing guard, runbook, and agent-guidance requirement to changed files and verification evidence.

## Assumptions

- Maintainers will manually enable GitHub Pages deployment from Actions in repository settings before expecting the workflow to publish successfully.
- The staging URL is the repository's GitHub Pages URL until DOC-012 changes custom-domain, base-path, or public launch settings.
- Direct staging preview access is acceptable for maintainers and reviewers even though indexing and crawler discovery remain blocked.
- Existing docs-site validation remains the authoritative local quality gate for this feature.
- GitHub's standard Pages deployment actions are sufficient for the DOC-011 staging deployment path.
- Deploy triggers intentionally favor broad generated-reference coverage over missed docs-impacting deploys, but fixture-heavy test and non-rendered SpecKit process/archive churn should not publish a no-op staging artifact.
- GitHub-hosted runners are expected to provide a fresh VM per job, but DOC-011 still requires deleting `docs-site/dist` before validation so stale local or future runner state cannot become the uploaded Pages artifact.
- Pages artifacts are treated as run-scoped deployment inputs, not rollback assets; rollback relies on source revert/fix-forward plus a fresh validated deploy.
