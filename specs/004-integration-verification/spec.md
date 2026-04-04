# Feature Specification: Integration & Verification

**Feature Branch**: `004-integration-verification`
**Created**: 2026-04-03
**Status**: Draft
**Input**: User description: "Integration & Verification — branch protection rules on main, Copilot review, squash-only merges, GitHub Actions bot exemption, end-to-end verification checklist, CLAUDE.md CI/CD documentation, recovery & rollback procedures."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Branch Protection Enforcement (Priority: P1)

As a solo maintainer, I need GitHub branch protection rules on `main` that require passing CI checks and enforce squash-only merges so that broken or non-conventional commits cannot reach the main branch.

**Why this priority**: Without branch protection, all other CI investments (SPEC-002, SPEC-003) can be bypassed by a careless merge. This is the foundational quality gate for the entire pipeline.

**Independent Test**: Can be fully tested by attempting to merge a PR with a failing status check or via a non-squash merge method — both must be blocked. Delivers immediate enforcement of the CI pipeline.

**Acceptance Scenarios**:

1. **Given** a PR where the `validate-plugins` check has failed, **When** a maintainer attempts to merge it, **Then** the merge is blocked until the check passes.
2. **Given** a PR where the `validate-pr-title` check has failed, **When** a maintainer attempts to merge it, **Then** the merge is blocked until the check passes.
3. **Given** branch protection is configured, **When** a maintainer attempts a non-squash merge (merge commit or rebase merge), **Then** the merge method is unavailable or blocked.
4. **Given** branch protection is configured with the GitHub Actions bot exempted, **When** the SPEC-003 release workflow pushes a `chore:` marketplace sync commit to `main`, **Then** the push succeeds without requiring a PR.
5. **Given** branch protection is applied, **When** a developer attempts to push directly to `main` (non-bot), **Then** the push is rejected.

---

### User Story 2 - Copilot Code Review on PRs (Priority: P2)

As a solo maintainer, I need Copilot code review automatically requested on every PR so that I receive automated code quality feedback before merging.

**Why this priority**: Copilot review provides a low-cost, automated quality signal that augments the CI checks. It catches issues that structural validation cannot, and it costs nothing beyond the existing GitHub Copilot subscription.

**Independent Test**: Can be tested by opening a new PR and observing that Copilot is automatically added as a reviewer. Delivers immediate automated review coverage.

**Acceptance Scenarios**:

1. **Given** Copilot code review is enabled on the repository, **When** a new PR is opened against `main`, **Then** Copilot is automatically added as a reviewer.
2. **Given** Copilot review is enabled, **When** Copilot completes its review, **Then** review comments appear inline on the PR diff.

---

### User Story 3 - End-to-End Verification Checklist (Priority: P3)

As a solo maintainer, I need a documented end-to-end verification checklist that walks through the complete workflow from feature branch creation to a user running `/plugin marketplace update`, so that I can verify the pipeline works correctly and diagnose issues.

**Why this priority**: The pipeline has never been run end-to-end. Without a checklist, verifying correctness requires reconstructing the full workflow from scattered docs. This checklist is the primary artifact for proving the system works.

**Independent Test**: Can be tested by executing the checklist steps in sequence after merging a test feature and confirming each step's expected output. Delivers a reusable verification protocol for every future release.

**Acceptance Scenarios**:

1. **Given** the verification checklist document exists in `docs/ai/specs/`, **When** a maintainer follows it step by step, **Then** each step has a clear expected outcome and a diagnostic note for failure.
2. **Given** a feature PR has been merged to `main`, **When** the maintainer follows the checklist through the release-please → GitHub Release → marketplace sync stages, **Then** the checklist confirms that `marketplace.json` version numbers have been updated and a plugin consumer running `/plugin marketplace update` would see the new version.
3. **Given** the checklist is followed on a clean run, **When** all steps pass, **Then** the checklist confirms the pipeline is functional end-to-end.

---

### User Story 4 - CI/CD Workflow Documentation in CLAUDE.md (Priority: P3)

As a solo maintainer (and any future contributor), I need CLAUDE.md updated with the CI/CD workflow documentation — branching strategy, PR requirements, release process, adding new plugins to release-please config, and the user update path — so that all conventions are discoverable in one place.

**Why this priority**: CLAUDE.md is the primary project reference loaded by Claude Code automatically. Without this documentation, the workflow exists only implicitly in GitHub Actions files and is not discoverable for future maintenance or onboarding.

**Independent Test**: Can be tested by reading CLAUDE.md alone and verifying a new contributor could understand the full branching and release workflow without consulting any other file. Delivers immediately useful documentation.

**Acceptance Scenarios**:

1. **Given** CLAUDE.md is updated, **When** a contributor reads it, **Then** they can find the branching strategy (`NNN-feature-name`), PR title requirements (conventional commits), and merge policy (squash only) without consulting any other file.
2. **Given** CLAUDE.md is updated, **When** a contributor wants to add a new plugin to the release automation, **Then** CLAUDE.md contains accurate instructions for updating `release-please-config.json` and `.release-please-manifest.json`.
3. **Given** CLAUDE.md is updated, **When** a plugin consumer wants to know how to get the latest version, **Then** CLAUDE.md documents the `/plugin marketplace update` command.

---

### User Story 5 - Recovery & Rollback Procedures (Priority: P4)

As a solo maintainer, I need recovery and rollback procedures documented — re-running the sync workflow, reverting a bad release via a `fix:` commit, and forcing a version with `Release-As: X.Y.Z` — so that I can handle edge cases without researching release-please documentation each time.

**Why this priority**: Edge cases in the release pipeline are rare but high-stress. Pre-documented recovery procedures reduce time-to-resolution and prevent destructive workarounds.

**Independent Test**: Can be tested by reviewing the procedures for completeness and accuracy against actual release-please behavior. Delivers immediate value as a reference document.

**Acceptance Scenarios**:

1. **Given** a `chore:` marketplace sync commit failed mid-workflow, **When** a maintainer consults the recovery procedures, **Then** they find step-by-step instructions for manually re-triggering the sync workflow via the GitHub Actions UI.
2. **Given** a bad release was published (wrong version, broken plugin), **When** a maintainer consults the rollback procedures, **Then** they find instructions for pushing a `fix:` commit to patch forward rather than reverting history.
3. **Given** a maintainer needs to force a specific version number, **When** they consult the procedures, **Then** they find the `Release-As: X.Y.Z` commit footer syntax and an explanation of when to use it.

---

### Edge Cases

- What happens when a PR is opened by the release-please bot itself — should CI checks run on release PRs the same as feature PRs?
- What happens if the GitHub Actions bot push is blocked because it lacks the bypass actor permission — who is responsible for re-running the sync?
- What happens when a new plugin is added to the repository but has not yet been added to `release-please-config.json` — will CI pass silently or fail?
- How does the verification checklist handle a partial pipeline run where release-please opens a PR but the maintainer has not merged it yet?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST have branch protection rules applied to the `main` branch that require status checks `validate-plugins` and `validate-pr-title` to pass before a PR can be merged.
- **FR-002**: The branch protection rules MUST enforce squash-only merges by disabling merge commits and rebase merges on the repository.
- **FR-003**: The branch protection rules MUST prevent direct pushes to `main` by non-exempt actors.
- **FR-004**: The GitHub Actions bot (`github-actions[bot]`) MUST be listed as a bypass actor in the branch protection configuration so that automated commits from SPEC-003's marketplace sync workflow can push directly to `main`.
- **FR-005**: The branch protection configuration MUST be scriptable and reproducible via `gh api` commands so it can be re-applied after repository changes.
- **FR-006**: Copilot code review MUST be enabled on the repository so that Copilot is automatically requested as a reviewer on new PRs.
- **FR-007**: A verification checklist document MUST be created at `docs/ai/specs/cicd-release-pipeline-verification.md` that covers all stages: feature branch creation, PR submission, CI check execution, PR merge, release-please PR creation and merge, GitHub Release publication, marketplace sync commit, and end-user plugin update.
- **FR-008**: The verification checklist MUST include expected outputs for each stage and diagnostic guidance for common failure modes.
- **FR-009**: `CLAUDE.md` MUST be updated to document the branching strategy (naming convention `NNN-feature-name`), PR requirements (conventional commit titles, squash merge policy), the release process (release-please automation, GitHub Release, marketplace sync), how to add new plugins to `release-please-config.json`, and the end-user update path (`/plugin marketplace update`).
- **FR-010**: `CLAUDE.md` MUST document recovery and rollback procedures including: re-triggering the marketplace sync workflow manually, patching a bad release via a `fix:` commit, and forcing a specific version with the `Release-As: X.Y.Z` commit footer.
- **FR-011**: All documentation in `CLAUDE.md` and the verification checklist MUST accurately reflect the actual implemented workflows from SPEC-001, SPEC-002, and SPEC-003 — no aspirational or inaccurate descriptions.
- **FR-012**: No existing plugin code, tests, or CI workflow files MUST be modified as part of this feature.

### Key Entities

- **Branch Protection Rule**: A GitHub repository setting applied to `main` that enforces required status checks, merge method restrictions, and bypass actor exemptions.
- **Bypass Actor**: The `github-actions[bot]` identity that is granted permission to push to `main` without satisfying branch protection rules, enabling automated CI commits.
- **Verification Checklist**: A markdown document in `docs/ai/specs/` that serves as the operational runbook for validating the end-to-end CI/CD pipeline.
- **Recovery Procedure**: A documented step-by-step procedure for resolving edge-case failures in the release pipeline (sync failure, bad release, version forcing).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A PR with a failing `validate-plugins` or `validate-pr-title` check cannot be merged to `main` — merge is blocked 100% of the time.
- **SC-002**: A PR merged to `main` always produces exactly one squash commit — non-squash merge methods are unavailable in the repository UI.
- **SC-003**: The GitHub Actions bot can push a `chore:` commit to `main` without a PR — automated sync commits succeed without manual intervention.
- **SC-004**: The verification checklist can be followed by the maintainer in a single session and confirms pipeline correctness end-to-end within one release cycle.
- **SC-005**: A new contributor reading only `CLAUDE.md` can understand the complete branching, PR, and release workflow without consulting any other documentation file.
- **SC-006**: Recovery procedures allow the maintainer to resolve a sync failure, a bad release, or a version conflict in under 15 minutes without consulting external documentation.

## Assumptions

- The repository is `racecraft-lab/racecraft-plugins-public` on GitHub and the maintainer has Admin access required to configure branch protection rules.
- The exact job names for required status checks are `validate-plugins` and `validate-pr-title` as defined in SPEC-002's PR checks workflow — these names must match exactly.
- Copilot code review is available under the existing GitHub organization plan and can be enabled via repository settings.
- The GitHub Actions bot identity used for bypass is `github-actions[bot]` — this is the standard GitHub-managed identity for workflow-generated commits.
- The `release-please-config.json` already contains the `speckit-pro` plugin configuration from SPEC-001; documentation of adding new plugins is instructional, not a new implementation.
- The verification checklist will be executed manually by the maintainer in a real repository context (not a dry run), requiring an actual PR merge cycle to complete.
- CLAUDE.md follows the existing heading and section structure already established in the file; new CI/CD sections are appended or inserted without restructuring existing content.
- Release-please version 4 (`googleapis/release-please-action@v4`) is the automation tool in use, as configured in SPEC-003.
- The worktree is at `.worktrees/004-integration-verification/` and the branch `004-integration-verification` already exists — no new branch creation is needed.
