# Feature Specification: Integration & Verification

**Feature Branch**: `004-integration-verification`
**Created**: 2026-04-03
**Status**: Draft
**Input**: User description: "Integration & Verification — branch protection rules on main, Copilot review, squash-only merges, GitHub Actions bot exemption, end-to-end verification checklist, CLAUDE.md CI/CD documentation, recovery & rollback procedures."

## Clarifications

### Session 2026-04-03

- Q: Which GitHub API should configure branch protection — legacy branch protection API or the newer repository rulesets API? → A: Legacy branch protection API (`PUT /repos/{owner}/{repo}/branches/{branch}/protection`). Simpler to script with `gh api`, sufficient for a single-repo solo-maintainer setup, and does not require an organization account. Required status checks and squash enforcement are fully supported. Rulesets add complexity without benefit at this scale.
- Q: How does the GitHub Actions bot bypass direct pushes to `main` — and what is the mechanism? → A: [CONSENSUS RESOLVED] The `bypass_pull_request_allowances.apps` field and rulesets bypass actors are **organization-only** features — they do not work on personal repositories (per GitHub docs: "Actors may only be added to bypass lists when the repository belongs to an organization"). Since this is a personal repo, the correct approach is: configure classic branch protection with `enforce_admins: false` (the default). By default, branch protection restrictions do not apply to admin-context pushes, and `GITHUB_TOKEN` from the repo owner's workflows runs with admin-equivalent permissions. This allows the SPEC-003 marketplace sync `git push` to succeed while still requiring PRs for developer merges. If the repo migrates to an organization in the future, upgrade to a custom GitHub App + ruleset bypass actor pattern.
- Q: What is the correct required status check name for the plugin test job — is it `validate-plugins` or something else? → A: The actual job name is `validate-pr-title` (for the title check) and `test (speckit-pro)` for the matrix test job (dynamic, per `name: "test (${{ matrix.plugin }})"` in pr-checks.yml). The static required check that should be registered is `validate-pr-title`. For the matrix test job, a sentinel/aggregator job named `validate-plugins` should be added to pr-checks.yml to provide a stable, static check name that branch protection can require.
- Q: Does the `test` matrix job need a sentinel/aggregator job to provide a stable required status check name? → A: Yes. The matrix job name `test (speckit-pro)` is dynamic and would need to be registered as `test (speckit-pro)` specifically — it does not generalize. A sentinel job named `validate-plugins` should be added that depends on the `test` matrix job and always runs, passing only if all matrix jobs passed or were skipped, and failing if any matrix job failed or was cancelled. This provides the stable `validate-plugins` check name referenced in FR-001.
- Q: What happens when a docs-only PR causes the `test` matrix job to be skipped — does it block the merge via a pending required check? → A: No. The `test` job uses a job-level `if:` conditional (`if: needs.detect.outputs.plugins != '[]'`). When this condition is false the job is skipped, and GitHub reports a skipped job as "Success" — it does not remain pending and does not block the merge. A workflow-level path filter would cause the check to remain pending, but job-level skipping correctly resolves as passing. The sentinel `validate-plugins` job must be designed to also pass (not fail) when the matrix job is skipped.
- Q: How is Copilot automatic code review configured — via GitHub REST API or only through the GitHub UI? → A: UI-only. Copilot automatic code review is configured exclusively through the GitHub web UI: repository Settings → Rules → Rulesets → New branch ruleset → "Automatically request Copilot code review". There is no REST API endpoint to enable this setting programmatically. Adding Copilot as a PR reviewer via the GitHub reviewer API is also unsupported (Copilot is not a GitHub user or team entity). Once the ruleset is created via UI, it applies automatically to all matching PRs without further action.
- Q: Is Copilot code review advisory only or can it be made a required check that blocks merges? → A: Advisory only. Copilot posts inline review comments but cannot issue "Request changes" verdicts or pass/fail status signals. It is not a status check and cannot be registered as a required check in branch protection. It never blocks PR merges. The branch protection required checks (`validate-plugins`, `validate-pr-title`) are CI status checks — completely separate from Copilot's advisory review. No merge-blocking enforcement via Copilot is possible or needed for this feature.
- Q: Does Copilot code review work on a personal repository with a Copilot Pro or Pro+ plan? → A: Yes. Copilot code review (automatic, via repository ruleset) is available on personal repositories for maintainers with a Copilot Pro or Copilot Pro+ subscription. The spec assumption referring to "existing GitHub organization plan" is a misnomer — the correct requirement is a Copilot Pro/Pro+ individual plan. No organization account is needed. Configuration is via repository ruleset (not organization-level policy).
- Q: What repository settings are needed beyond creating the branch ruleset to enable Copilot automatic code review? → A: None required. The only mandatory step is creating a branch ruleset with "Automatically request Copilot code review" enabled. Optionally: enable "Review new pushes" (so Copilot re-reviews on each push, not just PR open) and/or create `.github/copilot-instructions.md` for custom review guidelines (aligns Copilot toward project-specific standards such as naming conventions, test coverage, and security checks). No other repository settings, branch protection changes, or permissions are required.
- Q: Should the verification checklist be automated (a script that checks each step) or a manual walkthrough document? → A: Manual walkthrough document. The end-to-end pipeline involves GitHub UI actions (Copilot review, PR merge), GitHub Actions execution, and release-please PR creation — none of which can be fully scripted or asserted in a deterministic test. A manual markdown checklist with expected outputs and failure diagnostics per step is the correct artifact. This matches FR-007/FR-008 and SC-004 ("followed by the maintainer in a single session"). No shell script verification harness is needed.
- Q: How detailed should the CLAUDE.md CI/CD section be — just the workflow overview or also include troubleshooting? → A: Workflow overview plus essential troubleshooting inline. SC-005 requires a new contributor to understand the complete workflow from CLAUDE.md alone without consulting other files. That means the branching strategy, PR requirements, release process, and key recovery steps must all be present in CLAUDE.md. Deep diagnostic walkthroughs belong in the standalone verification checklist (docs/ai/specs/cicd-release-pipeline-verification.md), not in CLAUDE.md. CLAUDE.md should include one-liner troubleshooting pointers (e.g., "if sync fails, re-run the Release workflow manually") that link or reference the checklist for deeper investigation.
- Q: Should recovery procedures reference specific `gh` commands or just describe the concepts? → A: Specific `gh` commands and copy-pasteable syntax. SC-006 requires resolution in under 15 minutes without consulting external documentation. Conceptual descriptions alone do not meet that bar. Recovery procedures must include: exact `gh workflow run` commands for re-triggering the sync, the `Release-As: X.Y.Z` commit footer syntax (not a `gh` command — it is a git commit trailer), and `fix:` commit examples for patch-forward rollback. All commands must be copy-pasteable with only `<owner>/<repo>` substitution needed.
- Q: What sections of CLAUDE.md need updating vs. which are new sections? → A: All CI/CD content is new sections. The existing CLAUDE.md sections ("What This Repo Is", "Plugin Architecture", "Running Tests", "speckit-pro Plugin", "Active Technologies", "Recent Changes") contain no CI/CD workflow, branching strategy, release process, or recovery information. New sections to add: "## Contributing & Branching Strategy", "## CI/CD Workflow", "## Release Process", "## Adding a New Plugin to Release Automation", "## Recovery & Rollback Procedures". The "Recent Changes" entry and "Active Technologies" list get minor appends for SPEC-004. No existing section content is modified.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Branch Protection Enforcement (Priority: P1)

As a solo maintainer, I need GitHub branch protection rules on `main` that require passing CI checks and enforce squash-only merges so that broken or non-conventional commits cannot reach the main branch.

**Why this priority**: Without branch protection, all other CI investments (SPEC-002, SPEC-003) can be bypassed by a careless merge. This is the foundational quality gate for the entire pipeline.

**Independent Test**: Can be fully tested by attempting to merge a PR with a failing status check or via a non-squash merge method — both must be blocked. Delivers immediate enforcement of the CI pipeline.

**Acceptance Scenarios**:

1. **Given** a PR where the `validate-plugins` sentinel check has failed (meaning at least one `test` matrix job failed), **When** a maintainer attempts to merge it, **Then** the merge is blocked until the check passes.
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

1. **Given** Copilot code review is enabled on the repository via a branch ruleset, **When** a new PR is opened against `main` and commits are pushed to it, **Then** Copilot is automatically added as a reviewer and posts its review (note: review may trigger on push rather than at PR open due to ruleset timing).
2. **Given** Copilot review is enabled, **When** Copilot completes its review, **Then** review comments appear inline on the PR diff as advisory feedback — Copilot does not issue "Request changes" and the PR can be merged regardless of Copilot's findings.
3. **Given** Copilot review is enabled with "Review new pushes" option active, **When** a new commit is pushed to an open PR, **Then** Copilot automatically re-reviews the updated diff.

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
- **Resolved**: When a docs-only PR causes the `test` matrix job to be skipped (no plugin files changed), the sentinel `validate-plugins` job must also pass (not fail). The sentinel job must handle the case where `test` was skipped and report success in that case. This is required so docs-only PRs are not blocked by a failing `validate-plugins` check.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST have branch protection rules applied to the `main` branch that require status checks `validate-plugins` and `validate-pr-title` to pass before a PR can be merged. The `validate-plugins` check is provided by a sentinel job (see FR-013) that aggregates the dynamic `test` matrix job results. The `validate-pr-title` check maps directly to the `validate-pr-title` job in pr-checks.yml.
- **FR-002**: The branch protection rules MUST enforce squash-only merges by disabling merge commits and rebase merges on the repository.
- **FR-003**: The branch protection rules MUST prevent direct pushes to `main` by non-exempt actors.
- **FR-004**: Branch protection MUST be configured with `enforce_admins: false` (the default) so that `GITHUB_TOKEN`-based pushes from the SPEC-003 marketplace sync workflow can push directly to `main`. On a personal repository, `GITHUB_TOKEN` runs with admin-equivalent permissions and bypasses branch protection when admin enforcement is not enabled. The `bypass_pull_request_allowances.apps` and rulesets bypass actors are organization-only features and MUST NOT be relied upon. Required status checks apply only to PR merges, not direct pushes, so no separate status-check bypass is needed.
- **FR-005**: The branch protection configuration MUST be applied via the legacy GitHub branch protection REST API (`PUT /repos/{owner}/{repo}/branches/{branch}/protection`) using `gh api` commands so it is scriptable and reproducible.
- **FR-013**: A sentinel job named `validate-plugins` MUST be added to the pr-checks.yml workflow. It MUST depend on the `test` matrix job and MUST always run. It MUST pass if all `test` matrix jobs passed or were skipped (no plugin changes), and MUST fail if any `test` matrix job failed or was cancelled. This provides the stable static check name `validate-plugins` required by branch protection (FR-001).
- **FR-006**: Copilot code review MUST be enabled on the repository so that Copilot is automatically requested as a reviewer on new PRs. Configuration is UI-only: repository Settings → Rules → Rulesets → New branch ruleset → "Automatically request Copilot code review" targeting the default branch, with "Review new pushes" enabled. No REST API exists for this configuration. Copilot review is advisory only — it posts inline comments but cannot issue "Request changes" verdicts, is not a status check, and does not block PR merges. It is entirely separate from the branch protection required checks in FR-001. Requires an active Copilot Pro or Copilot Pro+ subscription on the maintainer account (not an organization plan).
- **FR-007**: A verification checklist document MUST be created at `docs/ai/specs/cicd-release-pipeline-verification.md` as a manual walkthrough markdown document (not an automated script). It covers all stages: feature branch creation, PR submission, CI check execution, PR merge, release-please PR creation and merge, GitHub Release publication, marketplace sync commit, and end-user plugin update. The manual format is required because pipeline stages involve GitHub UI actions and release-please PR creation that cannot be scripted deterministically.
- **FR-008**: The verification checklist MUST include expected outputs for each stage and diagnostic guidance for common failure modes. Each stage entry must have: (1) the action to take, (2) expected output/state, and (3) a diagnostic note if the expected state is not observed.
- **FR-009**: `CLAUDE.md` MUST be extended with new sections (not modifications to existing sections) documenting: the branching strategy (naming convention `NNN-feature-name`), PR requirements (conventional commit titles, squash merge policy), the release process (release-please automation, GitHub Release, marketplace sync), how to add new plugins to `release-please-config.json`, and the end-user update path (`/plugin marketplace update`). New sections to add: "## Contributing & Branching Strategy", "## CI/CD Workflow", "## Release Process", "## Adding a New Plugin to Release Automation", "## Recovery & Rollback Procedures". Each section must be self-contained so a new contributor reading CLAUDE.md alone understands the full workflow (SC-005). Inline troubleshooting pointers (one-liners) are included in each section; deep diagnostic walkthroughs are in the verification checklist (FR-007).
- **FR-010**: `CLAUDE.md` MUST document recovery and rollback procedures with specific, copy-pasteable commands — not just conceptual descriptions. Required content: (1) exact `gh workflow run` command for manually re-triggering the marketplace sync workflow, (2) the `Release-As: X.Y.Z` git commit footer syntax for forcing a specific version, (3) a `fix:` commit example for patching forward after a bad release. Commands must require only `<owner>/<repo>` substitution. This level of specificity is required so SC-006 (resolution in under 15 minutes) is achievable.
- **FR-011**: All documentation in `CLAUDE.md` and the verification checklist MUST accurately reflect the actual implemented workflows from SPEC-001, SPEC-002, and SPEC-003 — no aspirational or inaccurate descriptions.
- **FR-012**: No existing plugin code or plugin test files MUST be modified as part of this feature. The only permitted CI workflow change is the addition of the `validate-plugins` sentinel job to `.github/workflows/pr-checks.yml` (FR-013); all other CI workflow logic remains unchanged.

### Key Entities

- **Branch Protection Rule**: A GitHub repository setting applied to `main` via the legacy REST API (`PUT /repos/{owner}/{repo}/branches/{branch}/protection`) that enforces required status checks, merge method restrictions, and bypass actor exemptions.
- **Bypass Mechanism**: Branch protection is configured with `enforce_admins: false` (the default). On a personal repository, `GITHUB_TOKEN` from the repo owner's workflows has admin-equivalent permissions and bypasses branch protection rules. This allows the SPEC-003 marketplace sync commit to push directly to `main`. No explicit bypass actor configuration is needed — the bypass is implicit via admin permissions. If the repo migrates to an organization, this must be upgraded to a custom GitHub App + ruleset bypass actor pattern.
- **Sentinel Job**: A job named `validate-plugins` added to pr-checks.yml that aggregates the results of the dynamic `test` matrix job and provides a stable, static check name that branch protection can require. It passes when all matrix jobs pass or are skipped, and fails when any matrix job fails or is cancelled.
- **Copilot Code Review**: An advisory automated review configured via a GitHub branch ruleset (UI-only, no API). Posts inline comments on PR diffs but cannot block merges or act as a required status check. Requires Copilot Pro or Pro+ on the maintainer account. Configured at: repository Settings → Rules → Rulesets → branch ruleset with "Automatically request Copilot code review" and "Review new pushes" enabled. Completely independent of branch protection required status checks.
- **Verification Checklist**: A manual walkthrough markdown document at `docs/ai/specs/cicd-release-pipeline-verification.md` that serves as the operational runbook for validating the end-to-end CI/CD pipeline. Format: each stage has an action, expected output, and diagnostic note. Cannot be automated because pipeline stages involve GitHub UI and release-please PR creation.
- **Recovery Procedure**: Documented step-by-step procedures with specific, copy-pasteable `gh` commands and git commit syntax for resolving edge-case failures: re-triggering the marketplace sync workflow, patching a bad release via `fix:` commit, and forcing a version with `Release-As: X.Y.Z` commit footer. Lives in CLAUDE.md under "## Recovery & Rollback Procedures".
- **CLAUDE.md CI/CD Sections**: Five new sections added to CLAUDE.md (not modifications to existing sections): "## Contributing & Branching Strategy", "## CI/CD Workflow", "## Release Process", "## Adding a New Plugin to Release Automation", "## Recovery & Rollback Procedures". Each section is self-contained. Inline troubleshooting pointers are included; deep diagnostics are deferred to the verification checklist.

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
- The required status check names are `validate-plugins` (provided by a new sentinel job in pr-checks.yml) and `validate-pr-title` (existing job in pr-checks.yml) — these names must match exactly. The `validate-plugins` check does not yet exist in pr-checks.yml and must be added as part of this feature (FR-013).
- Copilot code review is available under the maintainer's Copilot Pro or Copilot Pro+ individual subscription (not an organization plan — the repo is personal). It is configured via a repository branch ruleset in the GitHub UI (no API path exists). Copilot review is advisory only and does not interact with branch protection required status checks.
- The GitHub Actions bot bypass relies on `enforce_admins: false` in the legacy branch protection API. On a personal repository, `GITHUB_TOKEN` has admin-equivalent permissions and bypasses branch protection when admin enforcement is disabled (the default). The `bypass_pull_request_allowances.apps` field and rulesets bypass actors are organization-only features and are not available on personal repositories. If the repo migrates to an organization, the bypass mechanism must be upgraded to a custom GitHub App + ruleset bypass actor pattern.
- The legacy branch protection API is used (not rulesets) because the repository is a personal repo managed by a solo maintainer, and the legacy API is simpler to script and does not require organization-level configuration.
- The `release-please-config.json` already contains the `speckit-pro` plugin configuration from SPEC-001; documentation of adding new plugins is instructional, not a new implementation.
- The verification checklist will be executed manually by the maintainer in a real repository context (not a dry run), requiring an actual PR merge cycle to complete.
- CLAUDE.md follows the existing heading and section structure already established in the file. All CI/CD content is added as new sections appended after the existing sections. Existing section content ("What This Repo Is", "Plugin Architecture", "Running Tests", "speckit-pro Plugin") is not modified. "Active Technologies" and "Recent Changes" receive minor appends only. No existing section is restructured or removed.
- Release-please version 4 (`googleapis/release-please-action@v4`) is the automation tool in use, as configured in SPEC-003.
- The worktree is at `.worktrees/004-integration-verification/` and the branch `004-integration-verification` already exists — no new branch creation is needed.
