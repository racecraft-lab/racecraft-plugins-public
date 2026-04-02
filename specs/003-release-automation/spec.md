# Feature Specification: Release Automation

**Feature Branch**: `003-release-automation`  
**Created**: 2026-04-01  
**Status**: Draft  
**Input**: User description: "Automated release workflow using release-please to handle version bumps, changelog generation, GitHub Releases, git tags, and marketplace.json synchronization on the racecraft-plugins-public repository."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automated Release PR Creation (Priority: P1)

As a maintainer, when I merge a PR with conventional commits (e.g., `feat:`, `fix:`) into main, release-please automatically opens or updates a Release PR that proposes the correct version bump and includes a generated changelog. I do not need to manually determine what changed or what the next version should be.

**Why this priority**: This is the foundational automation -- without automatic Release PR creation, no downstream steps (tagging, releasing, syncing) can occur. It eliminates the most time-consuming manual step.

**Independent Test**: Can be fully tested by pushing a conventional commit to main and verifying a Release PR is opened with the correct version bump and changelog content.

**Acceptance Scenarios**:

1. **Given** a `feat:` commit is pushed to main, **When** the release workflow runs, **Then** release-please opens a Release PR proposing a minor version bump with the feature listed in the changelog.
2. **Given** a `fix:` commit is pushed to main, **When** the release workflow runs, **Then** release-please opens a Release PR proposing a patch version bump with the fix listed in the changelog.
3. **Given** a Release PR already exists and a new conventional commit is pushed to main, **When** the release workflow runs, **Then** release-please updates the existing Release PR with the new commit included in the changelog and adjusts the version bump if necessary.
4. **Given** a `chore:` commit is pushed to main, **When** the release workflow runs, **Then** release-please does not create or update a Release PR (chore commits are ignored by default).

---

### User Story 2 - GitHub Release and Tag Creation (Priority: P1)

As a maintainer, when I merge the Release PR into main, release-please automatically creates a GitHub Release with a git tag (e.g., `speckit-pro-v1.1.0`). The release includes the generated changelog notes. I do not need to manually create tags or releases.

**Why this priority**: Tags and releases are the canonical way users and downstream systems discover new versions. Without this, the Release PR is just a formality with no artifact.

**Independent Test**: Can be fully tested by merging a Release PR and verifying a GitHub Release and git tag are created with the correct version and changelog content.

**Acceptance Scenarios**:

1. **Given** a Release PR exists with a proposed version bump, **When** the maintainer merges the Release PR, **Then** the release workflow creates a GitHub Release with the version tag (e.g., `speckit-pro-v1.1.0`) and the changelog as the release body.
2. **Given** the Release PR proposes version `1.2.0`, **When** it is merged, **Then** the git tag follows the component-prefixed format `speckit-pro-v1.2.0`.
3. **Given** a Release PR is merged, **When** the GitHub Release is created, **Then** the `.release-please-manifest.json` is updated to reflect the new version.

---

### User Story 3 - Marketplace Version Synchronization (Priority: P2)

As a maintainer, after a release is created, the workflow automatically runs the marketplace sync script to update marketplace.json with the new version from plugin.json. Plugin consumers running `/plugin marketplace update` see the latest version immediately.

**Why this priority**: This is the consumer-facing step that ensures marketplace visibility. It depends on the release being created first (Stories 1-2) but is essential for the end-to-end value proposition.

**Independent Test**: Can be fully tested by triggering the sync step after a release and verifying marketplace.json reflects the updated plugin.json version.

**Acceptance Scenarios**:

1. **Given** a GitHub Release was just created by the workflow, **When** the marketplace sync step runs, **Then** `scripts/sync-marketplace-versions.sh` is executed and marketplace.json is updated to match the version in plugin.json.
2. **Given** the marketplace sync updates marketplace.json, **When** the sync commit is created, **Then** the commit message is `chore: sync marketplace.json versions [skip ci]`.
3. **Given** the marketplace sync commit is pushed to main, **When** the release workflow triggers again, **Then** release-please ignores the `chore:` commit and does not create a new Release PR.

---

### User Story 4 - Conditional Sync Execution (Priority: P2)

As a maintainer, the marketplace sync step only runs when a Release PR is merged (i.e., a release was actually created), not when release-please merely updates an existing Release PR. This prevents unnecessary sync commits on every push to main.

**Why this priority**: Without this conditional logic, every push to main would attempt to run the sync script, creating noise commits or errors when no release exists.

**Independent Test**: Can be tested by pushing a regular conventional commit (not merging a Release PR) and verifying the sync step is skipped.

**Acceptance Scenarios**:

1. **Given** a conventional commit is pushed to main and release-please updates an existing Release PR, **When** the workflow evaluates the sync condition, **Then** the marketplace sync step is skipped.
2. **Given** a Release PR is merged and release-please creates a GitHub Release, **When** the workflow evaluates the sync condition, **Then** the marketplace sync step runs.
3. **Given** a `chore:` commit (e.g., the sync commit itself) is pushed to main, **When** the workflow runs, **Then** neither release-please nor the sync step produce any new commits or PRs.

---

### User Story 5 - No Infinite Loop (Priority: P1)

As a maintainer, the marketplace sync commit must not re-trigger release-please, ensuring there is no infinite loop of commits and releases. Two independent mechanisms prevent this: (1) **Primary**: commits made with `GITHUB_TOKEN` do not trigger subsequent workflow runs (GitHub's built-in infinite-loop protection); (2) **Secondary**: the `chore:` commit type guarantees release-please ignores the commit even if triggered by a PAT or other token.

**Why this priority**: An infinite loop would be a critical failure, generating unlimited commits, releases, and workflow runs. This is a safety-critical requirement.

**Independent Test**: Can be tested by verifying that after a sync commit is pushed, release-please does not open or update a Release PR.

**Acceptance Scenarios**:

1. **Given** the sync step pushes a `chore: sync marketplace.json versions [skip ci]` commit, **When** the push event occurs, **Then** no workflow runs are triggered due to `[skip ci]` and GITHUB_TOKEN's built-in loop prevention.
2. **Given** a full release cycle completes (conventional commit -> Release PR -> merge -> release -> sync), **When** the cycle ends, **Then** exactly one sync commit exists and no additional workflow runs produce changes.

---

### Edge Cases

- What happens when release-please runs but no releasable conventional commits exist since the last release (no-op)? Release-please silently does nothing -- no Release PR is created or updated, no error is emitted. Only `feat:`, `fix:`, and `deps:` prefixed commits are releasable units. Non-releasable commits (`chore:`, `docs:`, `refactor:`, `test:`) are ignored. The workflow completes successfully with all `release_created` outputs as `false`, and the marketplace sync step is skipped (conditional on `release_created`).
- What happens if a Release PR is closed without merging -- does release-please recreate it on the next push? No. release-please will NOT automatically create a new PR if a closed PR still has the `autorelease: pending` label. This is a known release-please behavior. Recovery: remove the `autorelease: pending` label from the closed PR, then trigger release-please again (push a new commit to main or manually re-run the workflow). On the next run, release-please creates a fresh Release PR incorporating all releasable commits since the last release tag.
- What happens when `scripts/sync-marketplace-versions.sh` fails (e.g., jq not available, marketplace.json malformed)? The workflow step fails visibly with a clear error in the GitHub Actions log, but the release and tag remain intact (they were created in a prior step). No automatic retry -- the script's failure modes are deterministic (structural issues, not transient). Recovery: fix the root cause and re-run the workflow via the GitHub Actions UI. The sync step uses the default `continue-on-error: false`, so a failure marks the entire workflow run as failed, providing clear signal to maintainers.
- What happens when the sync step fails -- is marketplace.json left permanently out of sync? No. The sync script is registry-driven and idempotent: it reads the current version from each plugin's `plugin.json` and writes it to `marketplace.json` regardless of prior state. The next successful release triggers the sync step again, which will correct any stale version. There is no accumulation of drift -- each sync invocation computes the full correct state from source-of-truth files. This self-healing property means a single sync failure is a temporary condition, not a permanent inconsistency.
- What happens when the sync script succeeds but the subsequent git commit or git push fails (partial completion)? The sync script writes to `marketplace.json` in the runner workspace, but the change is not committed or pushed. Since GitHub Actions runners are ephemeral, the workspace is discarded after the run. The on-disk `marketplace.json` on main remains at its prior state. The next successful release and sync cycle will produce the correct update. No partial state persists between workflow runs.
- What happens when marketplace.json is already up to date (sync script finds no changes)? The sync script compares the computed JSON with the existing file content. If identical, it exits 0 immediately with no file write and no git commit. The workflow step succeeds with no side effects. This idempotent behavior is implemented in `sync-marketplace-versions.sh` (lines 140-145).
- What happens when multiple conventional commits are pushed to main in rapid succession? Release-please batches them into a single Release PR update, and only one sync runs after the eventual merge.
- What happens if the GITHUB_TOKEN lacks `contents: write` permission? The sync commit push fails with a clear permissions error in the workflow log.
- What happens if branch protection prevents the GitHub Actions bot from pushing to main? The sync step fails; this is documented as a dependency on SPEC-004 to configure the exemption.
- What happens when a breaking change commit (`feat!:`, `fix!:`, or `BREAKING CHANGE` footer) is pushed to main? release-please detects the breaking change via the `!` suffix or `BREAKING CHANGE` footer and proposes a MAJOR version bump in the Release PR. With `bump-minor-pre-major: true` in the config, breaking changes would bump MINOR while version < 1.0.0, but since the current version is 1.0.0 (at/past major), breaking changes trigger a MAJOR bump (e.g., 1.0.0 -> 2.0.0). Both `!` suffix and `BREAKING CHANGE` footer are equivalent detection methods.
- What happens if the workflow is changed from GITHUB_TOKEN to a PAT or GitHub App token? The GITHUB_TOKEN's built-in loop prevention (commits don't trigger workflows) is lost, but two independent protections remain: (1) `chore:` commit type is ignored by release-please (no Release PR created), and (2) `[skip ci]` in the commit message prevents any workflow from running. This is a safe degradation requiring no spec or workflow changes.
- What happens when the release-please action itself fails (e.g., GitHub API error, network timeout, malformed config)? The workflow step fails and no subsequent steps (including marketplace sync) execute. The failure is visible in the GitHub Actions log. This does not block future pushes to main -- pushes are accepted by git regardless of workflow status. The next push to main re-triggers the workflow, and release-please resumes from its last known state (manifest file). Release-please is inherently resumable: it reads `.release-please-manifest.json` and the git tag history to determine current state, so a transient failure loses no progress.
- What happens when `release-please-config.json` or `.release-please-manifest.json` is malformed or missing? release-please fails immediately with a configuration error. The workflow step fails, the sync step is skipped (sequential dependency), and the failure is visible in the GitHub Actions log. Since these files are committed artifacts from SPEC-001, malformation indicates a merge conflict or accidental edit. Recovery: fix the JSON syntax or restore the file from git history, then push to main to re-trigger the workflow. release-please validates config on every run -- there is no silent degradation from bad configuration.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST trigger the release workflow on every push to the `main` branch. Manual triggering via `workflow_dispatch` is explicitly out of scope for this spec; the workflow is designed for push-event-driven automation only. The `push` trigger is scoped to the `main` branch only, which inherently prevents workflow execution from arbitrary branches. Fork pushes do not trigger workflows on the upstream repository's `main` branch (GitHub's fork security model); external contributions arrive via PRs and only trigger on merge to main.
- **FR-002**: System MUST run `googleapis/release-please-action` as the first step of the workflow to detect conventional commits and manage Release PRs.
- **FR-003**: System MUST create a GitHub Release with a component-prefixed git tag (e.g., `speckit-pro-v1.1.0`) when a Release PR is merged. The tag prefix derives from the `component` field in `release-please-config.json` (currently `"speckit-pro"`), producing tags in the format `<component>-v<version>`.
- **FR-004**: System MUST run `bash scripts/sync-marketplace-versions.sh` as a subsequent step in the same job as release-please, conditioned on `steps.release.outputs['speckit-pro--release_created']` (NOT the bugged `releases_created` plural output, which always returns true in v4). The sync script is registry-driven and handles all plugins in a single invocation; when a second plugin is added, its output check should be added with OR logic.
- **FR-005**: System MUST commit the marketplace sync changes with the message `chore: sync marketplace.json versions [skip ci]` to prevent re-triggering release-please and skip unnecessary workflow runs.
- **FR-006**: System MUST NOT run the marketplace sync step when release-please merely updates an existing Release PR without creating a release.
- **FR-007**: System MUST request `contents: write` and `pull-requests: write` permissions for the workflow token. `contents: write` enables creating GitHub Releases, git tags, and pushing the sync commit. `pull-requests: write` enables release-please to create and update Release PRs. Authentication is handled via `actions/checkout` with default `persist-credentials: true`, which configures git with the GITHUB_TOKEN automatically. Using GITHUB_TOKEN (not a PAT or GitHub App token) preserves the built-in infinite-loop prevention.
- **FR-008**: System MUST pin all third-party actions (`googleapis/release-please-action`, `actions/checkout`) to a specific major version tag (e.g., `@v4`) at minimum. Full-length commit SHA pinning is preferred for supply chain security (mitigates tag mutation, compromised upstream maintainer, and repository takeover attacks) but major version tags are acceptable for first-party GitHub actions (`actions/*`). Action version updates SHOULD be managed via Dependabot or manual review of upstream changelogs.
- **FR-009**: System MUST use existing configuration files (`release-please-config.json` and `.release-please-manifest.json`) created by SPEC-001. The `simple` release type will automatically create `speckit-pro/version.txt` in the first Release PR (no pre-existing file required). The `extra-files` config with `jsonpath: "$.version"` additionally updates `speckit-pro/.claude-plugin/plugin.json`.
- **FR-010**: System MUST contain the entire release workflow in a single file at `.github/workflows/release.yml`.
- **FR-011**: System MUST use path-prefixed output variables for release-please monorepo outputs. For the `speckit-pro` package, all outputs use the format `speckit-pro--<output_name>` (e.g., `speckit-pro--release_created`, `speckit-pro--tag_name`, `speckit-pro--version`). Outputs containing `/` in the path require bracket notation: `steps.release.outputs['path--output']`.
- **FR-012**: The marketplace sync step MUST use the default `continue-on-error: false` so that a sync failure marks the workflow run as failed, providing clear visibility to maintainers in the GitHub Actions UI and any configured notifications.
- **FR-013**: The workflow MUST set a `timeout-minutes` value on the job to prevent hung runs from consuming Actions minutes indefinitely. A 10-minute timeout is sufficient for the release-please + sync pipeline (target completion under 5 minutes per SC-001/SC-002/SC-003).
- **FR-014**: A release-please action failure MUST NOT block future pushes to main. The workflow runs asynchronously after the push event; git push acceptance is independent of workflow status. The next push re-triggers the workflow, and release-please resumes from its persisted state.
- **FR-015**: The workflow MUST define a concurrency group to prevent concurrent release runs from racing. The concurrency group MUST be scoped to the workflow name (e.g., `release-${{ github.ref_name }}`), and `cancel-in-progress` MUST be `false` so that in-progress release runs complete rather than being cancelled by subsequent pushes. At most one running and one pending run may exist at any time.

### Security Requirements

- **SEC-001**: The workflow MUST NOT interpolate user-controlled values (`github.event.head_commit.message`, PR titles, branch names) directly into `run:` shell commands via `${{ }}` expression syntax. All user-controlled inputs MUST be passed through environment variables (using `env:` block) to prevent script injection attacks. The sync step's git commit message is a hardcoded string literal (`chore: sync marketplace.json versions [skip ci]`), not derived from user input.
- **SEC-002**: The workflow MUST declare only the minimum required permissions (`contents: write`, `pull-requests: write`). No additional permission scopes are required or permitted for this workflow. The explicit `permissions:` block at the workflow level restricts the GITHUB_TOKEN to only these scopes, following the principle of least privilege.
- **SEC-003**: The sync step MUST NOT echo, print, or log authentication tokens, git credential URLs, or the GITHUB_TOKEN value. GitHub Actions automatically masks the GITHUB_TOKEN in logs, and `actions/checkout` configures git credentials via the `http.extraheader` config which is not printed by standard git operations. The sync script (`sync-marketplace-versions.sh`) uses `set -euo pipefail` without `set -x` (which would echo commands including credential-bearing URLs) and does not execute any git commands itself (git operations are handled by inline workflow steps). Credential cleanup is handled implicitly by runner ephemerality -- GitHub Actions runners are destroyed after each job, eliminating persisted credential risk.
- **SEC-004**: The `actions/checkout` step uses default `persist-credentials: true` so that the GITHUB_TOKEN is available for the sync commit push. While `persist-credentials: false` would be more restrictive, it would prevent the sync step from pushing. The token is stored in `.git/config` as an `http.extraheader` entry, accessible only to subsequent steps within the same job. This is acceptable because: (1) the workflow contains no untrusted third-party actions after checkout, (2) the sync step uses only the existing `sync-marketplace-versions.sh` script and inline git commands, and (3) the runner is ephemeral.

### Key Entities

- **Release PR**: An automatically generated pull request proposing a version bump and changelog update, managed by release-please.
- **GitHub Release**: A tagged release artifact on GitHub containing changelog notes, created when a Release PR is merged.
- **Marketplace Manifest** (`marketplace.json`): The registry file that plugin consumers read to discover available plugin versions.
- **Plugin Manifest** (`plugin.json`): The per-plugin version file that release-please updates during a release.
- **Release Configuration** (`release-please-config.json`, `.release-please-manifest.json`): Configuration files controlling release-please behavior, including component naming and versioning strategy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After a conventional commit is merged to main, a Release PR is opened or updated within 5 minutes without manual intervention.
- **SC-002**: After a Release PR is merged, a GitHub Release with the correct git tag is created within 5 minutes without manual intervention.
- **SC-003**: After a release is created, marketplace.json reflects the updated version within 5 minutes without manual intervention.
- **SC-004**: The sync commit does not trigger any additional release-please activity (zero infinite-loop incidents).
- **SC-005**: The entire release pipeline (commit to marketplace sync) completes end-to-end with zero manual steps.
- **SC-006**: Non-release pushes to main (e.g., `chore:` commits) complete the workflow without producing unnecessary commits or PRs.

## Clarifications

### Session 2026-04-01

- Q: Which release-please-action output variable should FR-004 use for the marketplace sync condition? → A: Use path-prefixed `steps.release.outputs['speckit-pro--release_created']` (NOT bugged plural `releases_created` which always returns true in v4).
- Q: Does the `simple` release type require a pre-existing `version.txt` in `speckit-pro/`? → A: No. The `simple` type automatically creates `speckit-pro/version.txt` in the first Release PR. The `extra-files` config additionally updates `plugin.json` via jsonpath.
- Q: What is the primary mechanism preventing infinite workflow loops from the sync commit? → A: Dual protection: (1) Primary -- GITHUB_TOKEN commits do not trigger subsequent workflow runs (GitHub built-in); (2) Secondary -- `chore:` commit type is ignored by release-please even if triggered by a PAT.
- Q: What is the exact output variable format for monorepo packages in the workflow YAML? → A: Path-prefixed with double-dash separator: `speckit-pro--release_created`, `speckit-pro--tag_name`, `speckit-pro--version`. Access via bracket notation when path contains `/`.
- Q: How does release-please determine the git tag format for releases? → A: The `component` field in `release-please-config.json` sets the tag prefix. With `"component": "speckit-pro"`, tags follow the format `speckit-pro-v<version>`.
- Q: When does the marketplace sync step execute relative to release-please in the workflow? → A: Same job, subsequent step conditioned on `steps.release.outputs['speckit-pro--release_created']`. Step-level outputs are immediately available within the same job; no cross-job output forwarding needed.
- Q: How should the workflow handle a multi-plugin release where multiple plugins are bumped simultaneously? → A: Run `sync-marketplace-versions.sh` once per workflow run. The script is registry-driven (iterates all entries in `marketplace.json`), so a single invocation handles any number of plugins. For the release condition, keep the per-component output check; when a second plugin is added, add its output check with OR logic (since top-level `releases_created` is bugged in v4).
- Q: What happens if `sync-marketplace-versions.sh` fails -- should the release be rolled back or the sync retried? → A: Fail the workflow step visibly with no rollback and no automatic retry. The release/tag are already created and remain intact. The script's failure modes (missing jq, malformed JSON, missing plugin.json) are deterministic -- retrying won't fix them. Manual re-run via GitHub Actions UI after fixing the root cause.
- Q: How does the GITHUB_TOKEN authenticate the sync commit push? → A: Via `actions/checkout` persisted credentials (default `persist-credentials: true`). The workflow declares `permissions: contents: write`, and `actions/checkout` configures git with the token automatically. Using GITHUB_TOKEN (not a PAT or App token) preserves the critical infinite-loop prevention: GITHUB_TOKEN commits do not trigger subsequent workflow runs.
- Q: Does the GitHub Actions bot identity prevent branch protection from blocking the push? → A: Yes, branch protection can block the push. This is an existing documented dependency on SPEC-004, which will configure the specific bypass mechanism (rulesets, GitHub App, or legacy branch protection settings). SPEC-003 documents the dependency without prescribing the mechanism.
- Q: What happens when release-please runs but no releasable conventional commits exist since the last release? → A: Clean no-op. Only `feat:`, `fix:`, and `deps:` are releasable commit types. When none exist since the last release tag, release-please does not create or update a Release PR. The workflow completes successfully with `release_created` output as `false`. No error, no warning.
- Q: What happens if a Release PR is closed without merging -- does release-please recreate it on the next push? → A: No. release-please will NOT create a new PR if an existing PR (even closed) retains the `autorelease: pending` label. Recovery requires removing the `autorelease: pending` label from the closed PR, then triggering release-please again via a new push or manual workflow re-run.
- Q: What happens if marketplace.json is already in sync (idempotent run)? → A: The sync script compares updated JSON with existing file content and exits 0 with no commit if identical. The workflow step succeeds with no side effects. This is already implemented in `sync-marketplace-versions.sh` (lines 140-145) and requires no workflow-level handling.
- Q: How does release-please handle breaking changes (`feat!:` or `BREAKING CHANGE` footer), and how does `bump-minor-pre-major: true` interact? → A: Breaking changes are detected via `!` suffix (e.g., `feat!:`, `fix!:`) or `BREAKING CHANGE` footer. With `bump-minor-pre-major: true` in the config, breaking changes bump MINOR while version < 1.0.0. Since the current version is 1.0.0 (at/past major), breaking changes will trigger a MAJOR version bump (e.g., 1.0.0 -> 2.0.0). Both detection methods are equivalent.
- Q: Should the spec document Release PR lifecycle labels and recovery for closed-without-merge? → A: Document only the closed-without-merge recovery in Edge Cases (most impactful). Full label lifecycle (`autorelease: pending` -> `autorelease: tagged`) is operational runbook content outside spec scope.

## Assumptions

- The `specify` CLI and release-please configuration files (`release-please-config.json`, `.release-please-manifest.json`) were already created by SPEC-001 and are present on the main branch.
- The `scripts/sync-marketplace-versions.sh` script was already created by SPEC-001 and correctly updates marketplace.json from plugin.json.
- The repository uses conventional commit format for all squash-merged PRs (enforced by developer discipline or CI validation in SPEC-002).
- GitHub Actions is enabled on the repository with sufficient minutes for workflow execution.
- Branch protection rules allowing the GitHub Actions bot to push to main will be configured by SPEC-004; until then, the sync step may fail on protected branches.
- The repository has a single releasable component (`speckit-pro`) as configured in `release-please-config.json`. The sync script handles multi-plugin releases natively (registry-driven iteration), but the workflow condition checks only `speckit-pro--release_created`; adding a second plugin requires an OR condition in the workflow.
- The `jq` utility is available in the GitHub Actions runner environment (standard on `ubuntu-latest`). The `ubuntu-latest` label is a moving target (GitHub periodically updates it to newer Ubuntu LTS versions); the workflow relies only on `jq` and standard git, which are present on all `ubuntu-*` runner images. No integrity validation of pre-installed runner tools is needed beyond GitHub's own runner image provenance controls.
