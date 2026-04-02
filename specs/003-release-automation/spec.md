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
2. **Given** the marketplace sync updates marketplace.json, **When** the sync commit is created, **Then** the commit message is `chore: sync marketplace.json versions`.
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

As a maintainer, the marketplace sync commit must not re-trigger release-please, ensuring there is no infinite loop of commits and releases. The `chore:` commit scope guarantees release-please ignores it.

**Why this priority**: An infinite loop would be a critical failure, generating unlimited commits, releases, and workflow runs. This is a safety-critical requirement.

**Independent Test**: Can be tested by verifying that after a sync commit is pushed, release-please does not open or update a Release PR.

**Acceptance Scenarios**:

1. **Given** the sync step pushes a `chore: sync marketplace.json versions` commit, **When** the release workflow triggers on that push, **Then** release-please produces no Release PR and the sync step is not triggered (no release was created).
2. **Given** a full release cycle completes (conventional commit -> Release PR -> merge -> release -> sync), **When** the cycle ends, **Then** exactly one sync commit exists and no additional workflow runs produce changes.

---

### Edge Cases

- What happens when `scripts/sync-marketplace-versions.sh` fails (e.g., jq not available, marketplace.json malformed)? The workflow should fail visibly with a clear error in the GitHub Actions log, but the release and tag remain intact.
- What happens when marketplace.json is already up to date (sync script finds no changes)? The sync step should skip the commit (no empty commits).
- What happens when multiple conventional commits are pushed to main in rapid succession? Release-please batches them into a single Release PR update, and only one sync runs after the eventual merge.
- What happens if the GITHUB_TOKEN lacks `contents: write` permission? The sync commit push fails with a clear permissions error in the workflow log.
- What happens if branch protection prevents the GitHub Actions bot from pushing to main? The sync step fails; this is documented as a dependency on SPEC-004 to configure the exemption.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST trigger the release workflow on every push to the `main` branch.
- **FR-002**: System MUST run `googleapis/release-please-action` as the first step of the workflow to detect conventional commits and manage Release PRs.
- **FR-003**: System MUST create a GitHub Release with a component-prefixed git tag (e.g., `speckit-pro-v1.1.0`) when a Release PR is merged.
- **FR-004**: System MUST run `bash scripts/sync-marketplace-versions.sh` only when a release was created in the current workflow run (i.e., the release-please action output indicates a release was created).
- **FR-005**: System MUST commit the marketplace sync changes with the message `chore: sync marketplace.json versions` to prevent re-triggering release-please.
- **FR-006**: System MUST NOT run the marketplace sync step when release-please merely updates an existing Release PR without creating a release.
- **FR-007**: System MUST request `contents: write` permission for the workflow token to enable pushing the sync commit.
- **FR-008**: System MUST pin the release-please action to a specific version (SHA or major version tag) following GitHub Actions best practices.
- **FR-009**: System MUST use existing configuration files (`release-please-config.json` and `.release-please-manifest.json`) created by SPEC-001.
- **FR-010**: System MUST contain the entire release workflow in a single file at `.github/workflows/release.yml`.

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

## Assumptions

- The `specify` CLI and release-please configuration files (`release-please-config.json`, `.release-please-manifest.json`) were already created by SPEC-001 and are present on the main branch.
- The `scripts/sync-marketplace-versions.sh` script was already created by SPEC-001 and correctly updates marketplace.json from plugin.json.
- The repository uses conventional commit format for all squash-merged PRs (enforced by developer discipline or CI validation in SPEC-002).
- GitHub Actions is enabled on the repository with sufficient minutes for workflow execution.
- Branch protection rules allowing the GitHub Actions bot to push to main will be configured by SPEC-004; until then, the sync step may fail on protected branches.
- The repository has a single releasable component (`speckit-pro`) as configured in `release-please-config.json`.
- The `jq` utility is available in the GitHub Actions runner environment (standard on `ubuntu-latest`).
