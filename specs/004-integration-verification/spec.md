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
- GitHub CLI (`gh`) v2.0+ is required to run the `gh api` branch protection setup command. No earlier version of the `gh` CLI supports the `gh api` subcommand with JSON `--input` piping reliably. This is an environmental prerequisite for the implementer, not a runtime dependency of the repository.

## Supplemental Requirement Clarifications

This section resolves requirement gaps identified during checklist review. All items are additive to the FRs above.

### User Story to Requirement Traceability

| User Story | Maps to FRs |
|------------|-------------|
| US1 — Branch Protection Enforcement | FR-001, FR-002, FR-003, FR-004, FR-005, FR-013 |
| US2 — Copilot Code Review | FR-006 |
| US3 — End-to-End Verification Checklist | FR-007, FR-008 |
| US4 — CI/CD Workflow Documentation in CLAUDE.md | FR-009, FR-011 |
| US5 — Recovery & Rollback Procedures | FR-010 |
| Cross-cutting constraints | FR-011, FR-012 |

### FR-002 — Squash-Only Merge API Fields

The `gh api` branch protection `PUT` request body MUST set `allow_squash_merge: true`, `allow_merge_commit: false`, and `allow_rebase_merge: false` at the repository level (these are repository-level settings, not part of the branch protection payload itself — they are set via `PATCH /repos/{owner}/{repo}`). In the branch protection payload, no merge-method field is present; the merge method restriction is enforced at the repository settings level.

### FR-003 — Exempt Actors Definition

"Non-exempt actors" in FR-003 means: any human user (including the repo owner acting as a developer), any third-party app, and any workflow using a PAT not scoped to admin. The only actor considered exempt in this configuration is the repository owner's own GitHub Actions workflow token (`GITHUB_TOKEN`) when `enforce_admins: false` is set — because `GITHUB_TOKEN` on a personal repo inherits admin-equivalent scope, and `enforce_admins: false` means admin-context direct pushes bypass the restriction. No explicit bypass list is configured. The full list of exempt actors is: `GITHUB_TOKEN` in owner-context workflows only.

### FR-004 — Platform Dependency Acknowledgment

The statement that "`GITHUB_TOKEN` runs with admin-equivalent permissions" on personal repositories is documented GitHub platform behavior (ref: GitHub docs on `enforce_admins` and default branch protection). This behavior is not guaranteed by a formal API contract and could change with GitHub platform updates. The spec acknowledges this dependency: if GitHub changes `GITHUB_TOKEN` permission semantics on personal repos, the bypass mechanism will need to be revisited. This risk is accepted for the current solo-maintainer personal-repo context.

### FR-005 — Idempotency and Security

The legacy branch protection `PUT /repos/{owner}/{repo}/branches/{branch}/protection` endpoint is a full-overwrite operation (not a PATCH). Re-running the `gh api` setup command replaces all branch protection settings with the values in the request body. This means the command is safe to re-run (idempotent in outcome) only if the full desired configuration is included in the payload each time. Partial re-runs with a subset of settings will overwrite and discard unspecified settings. Implementers MUST include all protection fields in every call. The `gh api` command MUST rely on `GITHUB_TOKEN` from the environment — no embedded credentials or PATs are permitted in committed scripts. The command is invoked manually by the maintainer with appropriate admin scope, not from a workflow file.

### FR-005 — Auditability

The exact `gh api` command used to configure branch protection MUST be documented in the verification checklist (`docs/ai/specs/cicd-release-pipeline-verification.md`) under Stage 1. This serves as the Infrastructure-as-Code record for the configuration. No separate script file is required. The verification checklist is the authoritative record.

### FR-006 — Copilot Review Fallback

If Copilot code review is not triggered on a PR (e.g., branch ruleset misconfigured, Copilot Pro subscription expired, or review does not fire on a particular push), the fallback behavior is: no review is posted, no failure signal is emitted, and the PR is not blocked. Copilot review failure is silent. The verification checklist (FR-007) MUST include a step to confirm Copilot review was triggered, with a diagnostic note explaining how to check ruleset status and subscription state in the GitHub UI. There is no programmatic recovery path — the maintainer must verify the ruleset configuration manually.

### FR-007 — Verification Checklist Stage Count

The verification checklist MUST cover a minimum of 8 stages: (1) feature branch creation, (2) PR submission and CI check execution, (3) Copilot review trigger confirmation, (4) PR merge (squash), (5) release-please PR creation, (6) release-please PR merge and GitHub Release publication, (7) marketplace sync commit push to `main`, and (8) end-user plugin update confirmation. Each stage is a distinct, checkable step with its own expected output and diagnostic note per FR-008. The partial pipeline state (release-please PR exists but not merged) is addressed by Stage 5: the checklist must note that the maintainer may pause here and that the pipeline resumes when the release-please PR is merged. The checklist does not define a time constraint for the pause.

### FR-008 — Diagnostic Note Definition

A "diagnostic note" in FR-008 means a human-readable note that includes: (a) the most likely cause of failure at that stage, and (b) one specific corrective action (either a `gh` CLI command to run, a GitHub UI location to inspect, or a file to check). Diagnostic notes do not need to cover all possible failure modes — only the most common one. Example format: "If Copilot review does not appear within 2 minutes: navigate to repository Settings → Rules → Rulesets and confirm the branch ruleset targets `main` and has 'Automatically request Copilot code review' enabled."

### FR-009 — CLAUDE.md Sync Convention

When any future PR modifies `.github/workflows/pr-checks.yml` or `.github/workflows/release-please.yml`, the PR description MUST include a note confirming whether CLAUDE.md's CI/CD sections require updates. This is a process convention, not an automated check. It is documented in the "CI/CD Workflow" section of CLAUDE.md (FR-009) as a maintenance reminder. SC-005 (a contributor reading only CLAUDE.md understands the workflow) defines the bar: if CLAUDE.md becomes inaccurate after a workflow change, SC-005 is violated.

### FR-011 — Accuracy Before End-to-End Run

"Accurately reflect actual implemented workflows" in FR-011 means: the documentation must faithfully describe the workflow as designed and configured by SPEC-001, SPEC-002, and SPEC-003 — not as empirically observed from a live run. The verification checklist (FR-007) documents the expected behavior; if the end-to-end run reveals discrepancies between expected and actual behavior, those discrepancies are bugs in the implementation, not in the documentation. FR-011 accuracy is validated by cross-referencing CLAUDE.md and the verification checklist against the actual GitHub Actions workflow YAML files and release-please configuration — not by waiting for a live run to complete.

### FR-013 — Sentinel Job Exact Logic and Dependency Matrix

The `validate-plugins` sentinel job MUST use `if: always()` so it runs regardless of whether the `test` matrix job ran, was skipped, or failed. The `needs:` field MUST list `[detect, test]`. The sentinel job exit logic MUST follow this shell expression:

```
if [[ "${{ needs.test.result }}" == "failure" || "${{ needs.test.result }}" == "cancelled" ]]; then
  exit 1
fi
```

The sentinel MUST pass when `needs.test.result` is `success` or `skipped`. The sentinel MUST fail when `needs.test.result` is `failure` or `cancelled`. If the `detect` job fails (result = `failure`), the `test` job will also fail to start (result = `skipped` or `cancelled` depending on GitHub's behavior) — in this case the sentinel MUST also fail, because a `detect` failure indicates a broken workflow, not a clean skip. To handle this: the sentinel MUST additionally check `needs.detect.result` and fail if `detect` did not succeed. Sentinel behavior when `detect` is skipped (draft PR scenario): `detect` uses `if: github.event.pull_request.draft == false`, so on draft PRs, `detect` is skipped, `test` is skipped, and `validate-plugins` MUST also be skipped (not fail) — this is achieved by adding `if: needs.detect.result != 'skipped'` or by using `if: always()` combined with the result-check expression that treats all-skipped as pass.

### SC-001 — Manual Test Definition

"Merge is blocked 100% of the time" in SC-001 is verified manually during the verification checklist run. In the manual walkthrough context, the maintainer confirms that: (a) when a test PR with a failing check exists, the GitHub UI shows the merge button as disabled, and (b) the GitHub API confirms the branch protection rules include the required checks. No automated assertion is required. "100% of the time" means: the configuration is correct such that no merge is possible through normal UI or API paths when a required check is failing — it is a configuration property, not a statistical claim.

### SC-004 — Session Duration Bound

"Single session" in SC-004 means a continuous working session with an estimated duration of 1–3 hours. The verification checklist assumes the full pipeline (feature merge → release-please PR → GitHub Release → marketplace sync → user update) completes within one working day. The maintainer may need to wait for GitHub Actions to complete between steps, but does not need to return on a separate day. If a release-please PR does not appear within 30 minutes of the feature PR merge, this is treated as a pipeline failure (diagnostic step).

### SC-005 — Objective Verification Method

SC-005 is objectively verified by the following test scenario: a person who is familiar with GitHub and GitHub Actions but has not previously worked on this repository reads only CLAUDE.md and must be able to answer these five questions without consulting any other file: (1) What naming convention do feature branches use? (2) What format must PR titles follow? (3) How does a release get published? (4) How do I add a new plugin to release automation? (5) How does a plugin consumer get the latest version? If CLAUDE.md's new sections (FR-009) answer all five questions, SC-005 is satisfied.

### SC-006 — Clock Start Definition

"Under 15 minutes" in SC-006 begins when the maintainer first observes the failure symptom (e.g., a failed GitHub Actions run, a missing marketplace sync commit, or an incorrect version number). The 15-minute target assumes the maintainer opens CLAUDE.md's "Recovery & Rollback Procedures" section as the first corrective action. The clock does not include time spent diagnosing whether a failure occurred — only the time from failure recognition to corrective action initiated.

### Edge Case Resolutions

- **Release-please bot PRs and CI checks**: When release-please opens its own PR against `main` using `GITHUB_TOKEN`, the `on: pull_request` workflow in pr-checks.yml will NOT be triggered (GitHub prevents recursive workflow runs from `GITHUB_TOKEN`-created PRs). This means `validate-plugins` and `validate-pr-title` checks will not run on release-please PRs, and the PR will have no required status checks to pass. Branch protection with `required_status_checks` is satisfied vacuously (no checks reported = no checks to require passing). This is expected behavior and acceptable for a solo-maintainer repo — release-please PRs are reviewed manually before merging. This behavior does not need to be worked around.
- **New plugin not in release-please-config.json**: If a plugin directory exists in the repository but is not listed in `release-please-config.json`, CI (pr-checks.yml) will test the plugin as normal (if files changed), but release-please will not create a release entry for it. This is silent from CI's perspective — there is no check that validates alignment between plugin directories and release-please config. This gap is intentional (KISS principle); the verification checklist documents the step to manually confirm `release-please-config.json` includes all plugins when adding a new one.
- **Who re-runs the sync**: If the GitHub Actions bot push to `main` is blocked for any reason, the sole responsible party is the repository owner (Fredrick Gabelmann). The recovery procedure is documented in CLAUDE.md's "Recovery & Rollback Procedures" section (FR-010): re-trigger the Release workflow manually via `gh workflow run`.
- **Sentinel workflow syntax error risk**: FR-012 constrains the pr-checks.yml change to adding only the sentinel job. The sentinel job is a small, well-defined addition. If the sentinel job has a YAML syntax error, the entire pr-checks.yml workflow will fail to parse, and no checks will run on any PR. This is detectable immediately on the first PR after the change and is mitigated by reviewing the YAML before merging the SPEC-004 implementation PR.

### FR-005 — Full Branch Protection API Payload Fields

The legacy branch protection `PUT /repos/{owner}/{repo}/branches/{branch}/protection` endpoint treats four fields as **required** in the request body: `required_status_checks`, `enforce_admins`, `required_pull_request_reviews`, and `restrictions`. Omitting any of these fields results in a 422 validation error. The implementer MUST include all four in every call.

For this solo-maintainer personal repository, the correct values for the two fields not covered elsewhere in this spec are:

- `required_pull_request_reviews: null` — No required PR approvals. The solo maintainer self-merges. Setting this to null disables required review counts and dismissal restrictions, which is correct for this context.
- `restrictions: null` — No push-actor restriction list. Push restrictions via this field are an organization-only feature and cannot be used on a personal repository. Setting this to null disables the restriction list entirely; the `enforce_admins: false` mechanism is the only push bypass needed.
- `allow_force_pushes: false` — Force pushes to `main` MUST be disabled. The bypass mechanism (`enforce_admins: false`) exempts the `GITHUB_TOKEN` from the direct-push restriction but does NOT need to allow force-pushes. Disabling force-pushes closes the history-rewriting attack surface.
- `allow_deletions: false` — Branch deletion of `main` MUST be disabled to prevent accidental or malicious removal of the protected branch.

These values MUST be included in the verification checklist (FR-005 Supplemental — Auditability) as part of the documented `gh api` command.

### FR-008 — Configuration Drift Diagnostic [CONSENSUS RESOLVED]

The verification checklist MUST include a read-back step immediately after Stage 1 (branch protection setup) that runs `gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection` and confirms the returned JSON includes `required_status_checks.contexts` containing `["validate-plugins", "validate-pr-title"]` and `enforce_admins.enabled: false`. This read-back step also serves as the detection method if branch protection is later accidentally weakened via the GitHub UI. No periodic re-verification workflow is required — re-running Stage 1 of the verification checklist is the documented recovery path. Configuration drift detection beyond this manual read-back is accepted as unaddressed risk for a solo-maintainer personal repository (Constitution Principle VI — YAGNI).

### FR-010 — enforce_admins Drift Recovery [CONSENSUS RESOLVED]

A fourth recovery scenario MUST be documented in CLAUDE.md under "Recovery & Rollback Procedures": if the marketplace sync `git push` fails with a 403 "Protected branch" error despite `GITHUB_TOKEN` having `contents: write` permissions, the most likely cause is that `enforce_admins` was accidentally set to `true` via the GitHub UI (Settings → Branches → Edit protection rule → "Do not allow bypassing the above settings"). Detection: run `gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection --jq '.enforce_admins.enabled'` — if output is `true`, the bypass is broken. Recovery: re-run the Stage 1 setup command from the verification checklist, which resets `enforce_admins: false` via the full-overwrite `PUT` endpoint. This MUST include the exact `gh api GET` detection command and the reference to the Stage 1 re-run.

### FR-004 — GITHUB_TOKEN Permissions Block in Release Workflow

The release.yml workflow (SPEC-003) explicitly declares `permissions: contents: write` and `permissions: pull-requests: write` at the workflow level. This explicit declaration is required because GitHub changed the default `GITHUB_TOKEN` permissions for new personal repositories to read-only in February 2023. The `permissions:` block in release.yml MUST NOT be removed — without it, the `git push` step in the marketplace sync job would fail with a 403 error even though `enforce_admins: false` is set. The bypass mechanism (`enforce_admins: false`) determines whether a push is allowed past branch protection rules; the `permissions:` block determines whether `GITHUB_TOKEN` has the write scope to attempt the push at all. These are two independent controls. FR-011 accuracy requirement extends to this: CLAUDE.md and the verification checklist MUST NOT describe the GITHUB_TOKEN bypass as relying solely on `enforce_admins: false` without also noting the required `contents: write` permission in the workflow.

### FR-004 — GITHUB_TOKEN Permissions Recovery [ERROR-HANDLING SUPPLEMENT]

A fifth recovery scenario MUST be documented in CLAUDE.md under "Recovery & Rollback Procedures": if the marketplace sync `git push` fails with a 403 error and `enforce_admins.enabled` is confirmed to be `false` (the drift recovery scenario returns `false`), the next most likely cause is that the `permissions: contents: write` declaration was removed from `release.yml`. Detection: inspect the workflow file via `gh api /repos/racecraft-lab/racecraft-plugins-public/contents/.github/workflows/release.yml --jq '.content' | base64 -d | grep -A3 'permissions'` to confirm the block is present. Recovery: restore the `permissions: contents: write` and `permissions: pull-requests: write` block at the workflow level in `.github/workflows/release.yml`, merge the fix as a `fix:` commit, and re-run the Release workflow. This addresses CHK069 by providing a distinct, actionable recovery path for the permissions failure mode separate from the `enforce_admins` drift recovery defined in FR-010 Supplemental — enforce_admins Drift.

### FR-007 — Verification Checklist Stage 5 Diagnostic (Release-Please No Commits) [ERROR-HANDLING SUPPLEMENT]

The verification checklist Stage 5 diagnostic note MUST distinguish between two observable failure modes that share the same symptom (no release-please PR appears within 30 minutes of the feature PR merge): (a) release-please ran successfully but found no releasable conventional commits (`fix:`, `feat:`, etc.) in the merge — in this case release-please is silent and takes no action; (b) the release-please GitHub Actions job itself failed — in this case the Actions tab shows a failed run. Detection for case (a): navigate to the GitHub Actions tab, find the most recent "Release Please" workflow run triggered by the merge, expand the run log, and look for a message indicating no changes were detected. Detection for case (b): the workflow run shows a red failure icon. Recovery for case (a): push a conventional commit (`fix: trigger release` with an explanation in the body) to `main` — release-please will pick it up on the next push. Recovery for case (b): inspect the workflow log for the specific error and address it, then re-run via `gh workflow run release.yml --repo racecraft-lab/racecraft-plugins-public`. The diagnostic note MUST explicitly state that a `chore:` commit type alone does NOT trigger a release-please PR — only `fix:`, `feat:`, or breaking-change commits do.

### FR-010 — Release-Please No Conventional Commits Recovery [ERROR-HANDLING SUPPLEMENT]

A fifth category of recovery scenario MUST be documented in CLAUDE.md under "Recovery & Rollback Procedures": if the maintainer needs to trigger a new release-please PR but no releasable commits have been merged (e.g., only `chore:` or `docs:` commits exist since the last release), the recovery is to push a minimal conventional commit that explicitly signals intent. The commit MUST use `fix:`, `feat:`, or include a `BREAKING CHANGE:` footer to register as releasable. Example copy-pasteable recovery: `git commit --allow-empty -m "fix: trigger release for <speckit-pro>"` followed by `git push origin main`. This is distinct from the `Release-As: X.Y.Z` mechanism (which overrides the inferred version) — the no-commits recovery is for situations where release-please simply has nothing to process. Both mechanisms may be combined: an empty `fix:` commit with a `Release-As: X.Y.Z` footer will trigger a release PR at the specified version. This addresses CHK065.

### FR-010 — Stale marketplace.json Recovery [ERROR-HANDLING SUPPLEMENT]

A sixth recovery scenario MUST be documented in CLAUDE.md under "Recovery & Rollback Procedures": if the marketplace sync workflow completes (green Actions run) but `marketplace.json` still shows old version numbers, the recovery procedure is: (1) Detection: run `gh api /repos/racecraft-lab/racecraft-plugins-public/contents/.claude-plugin/marketplace.json --jq '.content' | base64 -d` to read the live file from the default branch — if versions do not match the GitHub Release tags, the sync produced incorrect output. (2) Root cause check: view the sync workflow run log (Actions tab → Release → marketplace-sync job → "Update marketplace.json" step) to identify whether `jq` produced an unexpected value. (3) Automated re-try: re-trigger the sync via `gh workflow run release.yml --repo racecraft-lab/racecraft-plugins-public`. (4) Manual last-resort: if re-triggering fails, manually edit `.claude-plugin/marketplace.json` to set the correct version strings and push a `chore: sync marketplace.json versions [skip ci]` commit directly to `main` (this matches the format used by the automated sync and will not trigger a new release). The detection time threshold is: if the Actions run is still in-progress, wait for completion before treating the state as stale; if the run completed (green) and the file is still stale, treat as a sync failure. This addresses CHK066 and CHK084 and CHK085 and CHK086.

### FR-010 — Release-As Footer Monorepo Syntax [ERROR-HANDLING SUPPLEMENT]

The `Release-As: X.Y.Z` git commit footer used for forcing a specific version MUST be documented in CLAUDE.md with the following clarification for the monorepo context: in this repository, release-please manages individual plugins as separate components (configured in `release-please-config.json`). The `Release-As:` footer is scoped to a component based on which files the commit touches — a commit that modifies files under `speckit-pro/` will only affect the `speckit-pro` component's version. To force the `speckit-pro` component to version `X.Y.Z`, the commit MUST touch at least one file under `speckit-pro/` (e.g., a version comment in `speckit-pro/.claude-plugin/plugin.json`). A commit that touches no component files will not target any component. The documented example in CLAUDE.md MUST show both the commit footer syntax AND a concrete example of touching a file to scope it: `git commit -m "chore: force speckit-pro version\n\nRelease-As: 1.2.0" speckit-pro/.claude-plugin/plugin.json`. This addresses CHK068.

### FR-001 / FR-009 — Status Check Name Drift [ERROR-HANDLING SUPPLEMENT]

The CLAUDE.md "CI/CD Workflow" section (FR-009) MUST include an explicit maintenance warning: if any workflow job in `.github/workflows/pr-checks.yml` is renamed, the corresponding required status check name in branch protection MUST be updated to match — GitHub does NOT automatically update branch protection when a job is renamed, and it does NOT block or warn when a required check name no longer matches any running check. The observable symptom of a stale required check name is that PRs become mergeable without the renamed check passing (the check is simply absent from the PR status panel, not failing). Detection: run `gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection --jq '[.required_status_checks.contexts[]]'` and compare the output against the actual job names in `pr-checks.yml`. Recovery: re-run the Stage 1 branch protection setup command from the verification checklist with the updated check names in the payload — this is a full-overwrite `PUT` so the entire payload must be included. This requirement addresses CHK077, CHK078, CHK079, and CHK080. The status-check-drift detection command MUST appear in the verification checklist under a dedicated "Periodic Health Check" note at the end of the checklist.

### FR-001 — Required Check Name Silently Stale (GitHub Platform Behavior) [ERROR-HANDLING SUPPLEMENT]

For the purposes of this spec, it is documented as accepted behavior that: GitHub's legacy branch protection API does NOT automatically remove or invalidate a required status check name when the corresponding workflow job is renamed or deleted. The branch protection rules persist with the old check name indefinitely. A PR will not be blocked by a missing check name — a check that never reports status is treated the same as if no check is required for that name. This means check name drift silently degrades protection. The only mitigation in this spec is the manual detection command (`gh api ... --jq '[.required_status_checks.contexts[]]'`) documented per FR-001/FR-009 supplement above. No automated drift detection is required (YAGNI / KISS for a solo-maintainer personal repository). This behavior aligns with GitHub documentation on troubleshooting required status checks. This addresses CHK079 definitively by confirming there is no automated detection requirement — only a manual periodic check convention.

### FR-007 — Verification Checklist Expected Output Precision [ERROR-HANDLING SUPPLEMENT]

The expected output for each verification stage MUST be specified with the following minimum precision in the verification checklist document (FR-007): (a) Stage 1: the `gh api` read-back response MUST show `required_status_checks.contexts` containing exactly `["validate-plugins", "validate-pr-title"]` and `enforce_admins.enabled` equal to `false` — any other values indicate incorrect configuration; (b) Stage 7: the marketplace sync commit is expected on `main` with commit message matching the pattern `chore: sync marketplace.json versions [skip ci]`, with `.claude-plugin/marketplace.json` showing version numbers that match the GitHub Release tags for each component; (c) Stage 8: a plugin consumer running `/plugin marketplace update` in Claude Code should see a confirmation that the plugin registry was refreshed with the new version, or the maintainer can confirm by inspecting the raw `marketplace.json` via `gh api` as documented in the stale marketplace.json detection step. This addresses CHK056, CHK057, and CHK058.

### FR-008 — Stage 2 Sentinel Job Absent Diagnostic [ERROR-HANDLING SUPPLEMENT]

The verification checklist Stage 2 diagnostic note MUST distinguish between two `validate-plugins` failure modes: (a) the sentinel job appears as a status check but shows as failing — this means the sentinel job ran and detected a matrix test failure; (b) the sentinel job does not appear at all in the PR status checks panel — this means the `pr-checks.yml` workflow failed to parse or the sentinel job was not added. Diagnostic for case (b): navigate to the repository's Actions tab, find the most recent `pr-checks.yml` workflow run for the PR, and check if the workflow run itself shows a YAML parse error. If the workflow shows no runs at all for the PR, the workflow YAML syntax is likely invalid. Recovery for case (b): inspect `.github/workflows/pr-checks.yml` for YAML syntax errors and push a fix. This is distinct from the normal sentinel job failure diagnostic and addresses CHK061.
