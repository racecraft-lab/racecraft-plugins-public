# Feature Specification: PR Checks Workflow

**Feature Branch**: `002-pr-checks-workflow`
**Created**: 2026-04-01
**Status**: Draft
**Input**: User description: "Add CI validation workflow for pull requests with plugin test scoping and PR title conventional commit validation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Changed Plugin Test Execution (Priority: P1)

As a maintainer, I need a CI job that detects which plugins changed in a PR and runs only their test suites (Layers 1, 4, 5), so I get fast feedback without testing unchanged plugins.

**Why this priority**: This is the core value of the workflow -- catching broken plugins before they reach main. Without automated testing, regressions can silently ship. As the marketplace grows from 1 to 2-4 plugins, manual review alone cannot reliably catch test failures across all plugins.

**Independent Test**: Can be fully tested by opening a PR that modifies files within a plugin directory (e.g., `speckit-pro/`) and verifying that the CI job runs the test suite for that plugin and reports pass/fail status.

**Acceptance Scenarios**:

1. **Given** a PR that modifies files in `speckit-pro/`, **When** the PR is opened, **Then** the CI job runs `bash tests/run-all.sh` within the `speckit-pro/` directory and reports the result as a GitHub check.
2. **Given** a PR that modifies files in two different plugin directories, **When** the PR is opened, **Then** the CI job runs the test suite for each changed plugin directory independently and reports individual results.
3. **Given** a PR that modifies files in a plugin directory where tests fail, **When** the CI job completes, **Then** the overall check status is "failure" and the log output identifies which plugin and which tests failed.

---

### User Story 2 - PR Title Conventional Commit Validation (Priority: P1)

As a maintainer, I need a CI job that validates the PR title matches the Conventional Commits pattern (`type(scope): description`), so that release-please can correctly parse squash-merged commits on main.

**Why this priority**: PR title validation is equally critical because incorrect titles break the release-please automation (SPEC-003). If non-conventional titles reach main via squash merge, release-please cannot generate changelogs or version bumps, creating a cascading failure in the release pipeline.

**Independent Test**: Can be fully tested by opening a PR with a non-conforming title and verifying the check fails with a clear error message, then updating the title to a valid format and verifying the check passes.

**Acceptance Scenarios**:

1. **Given** a PR with title `feat(speckit-pro): add new coaching command`, **When** the PR title check runs, **Then** the check passes.
2. **Given** a PR with title `fix: resolve session timeout`, **When** the PR title check runs, **Then** the check passes (scope is optional).
3. **Given** a PR with title `feat(speckit-pro)!: breaking API change`, **When** the PR title check runs, **Then** the check passes (breaking change indicator is valid).
4. **Given** a PR with title `Update readme`, **When** the PR title check runs, **Then** the check fails with a clear error message.
5. **Given** a PR with title `added new feature`, **When** the PR title check runs, **Then** the check fails.

---

### User Story 3 - Clear Error Messages for Contributors (Priority: P2)

As a contributor, I need clear error messages when my PR title does not match the expected format, including an example of the correct format, so I can fix it without guessing.

**Why this priority**: Good error messages reduce friction for contributors and prevent back-and-forth in PR reviews. While the repo currently has a solo maintainer, clear messaging supports future contributors and serves as self-documenting CI.

**Independent Test**: Can be tested by opening a PR with an invalid title and verifying the CI output includes the expected format pattern and at least one concrete example.

**Acceptance Scenarios**:

1. **Given** a PR with an invalid title, **When** the title validation check fails, **Then** the error output includes the expected regex pattern.
2. **Given** a PR with an invalid title, **When** the title validation check fails, **Then** the error output includes at least one example of a valid PR title (e.g., `feat(speckit-pro): add new command`).
3. **Given** a PR with an invalid title, **When** the title validation check fails, **Then** the error output lists the valid type prefixes (`feat`, `fix`, `chore`, `docs`, `refactor`, `test`).

---

### User Story 4 - Skip Testing for Non-Plugin Changes (Priority: P2)

As a maintainer, I need the workflow to skip testing entirely when no plugin directories changed (e.g., docs-only PRs), so CI does not waste time on irrelevant runs.

**Why this priority**: Efficiency optimization that prevents unnecessary CI runs. While not as critical as catching bugs, it avoids false expectations (green check on untested code) and keeps CI fast for documentation and configuration changes.

**Independent Test**: Can be tested by opening a PR that only modifies root-level files (e.g., `README.md`, `CLAUDE.md`) or files outside any plugin directory, and verifying the test job either skips or passes without running any plugin test suites.

**Acceptance Scenarios**:

1. **Given** a PR that only modifies `README.md`, **When** the CI workflow runs, **Then** the plugin test job completes successfully without executing any test suites.
2. **Given** a PR that modifies both `README.md` and files in `speckit-pro/`, **When** the CI workflow runs, **Then** only the `speckit-pro/` test suite is executed (not skipped entirely).
3. **Given** a PR that only modifies `.github/workflows/` files, **When** the CI workflow runs, **Then** the plugin test job completes without executing any test suites.

---

### Edge Cases

- What happens when a new plugin directory is added that does not yet have a `tests/run-all.sh` script? The CI job should fail gracefully with a clear message indicating the missing test runner.
- What happens when `git diff --name-only` returns files at the repository root (e.g., `.gitignore`, `CLAUDE.md`)? These should not be treated as plugin directories.
- What happens when the PR title contains unicode characters or special characters in the scope? The regex should handle standard ASCII type prefixes while allowing flexible scope and description content.
- What happens when the PR has no changed files (empty PR)? The plugin test job should skip gracefully.
- What happens when a plugin's test suite has a non-zero exit code due to a test runner error (not a test failure)? The CI job should still report failure so the issue is surfaced.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST trigger the workflow on `pull_request` events with types `opened`, `reopened`, and `synchronize`.
- **FR-002**: System MUST run a plugin test job that detects changed top-level plugin directories using `git diff --name-only` against the PR base branch.
- **FR-003**: System MUST execute `bash tests/run-all.sh` within each detected changed plugin directory.
- **FR-004**: System MUST run a PR title validation job that checks the PR title against the regex pattern `^(feat|fix|chore|docs|refactor|test)(\(.+\))?!?: .+$`.
- **FR-005**: System MUST run the plugin test job and PR title validation job independently (in parallel, with no dependency between them).
- **FR-006**: System MUST skip test execution when no plugin directories have changed files in the PR diff.
- **FR-007**: System MUST display a clear error message when the PR title fails validation, including the expected format pattern, valid type prefixes, and at least one example of a correct title.
- **FR-008**: System MUST use pinned action versions (not floating tags like `@latest` or `@v4`) for all GitHub Actions used in the workflow.
- **FR-009**: System MUST configure minimal permissions for the workflow (read-only where possible).
- **FR-010**: System MUST run on `ubuntu-latest` with `bash` as the default shell.
- **FR-011**: System MUST report individual test results per plugin directory so failures are attributable to specific plugins.
- **FR-012**: System MUST fail the plugin test job if any changed plugin directory does not contain a `tests/run-all.sh` script.

### Key Entities

- **Workflow File**: The GitHub Actions workflow definition at `.github/workflows/pr-checks.yml` that orchestrates all CI checks on pull requests.
- **Plugin Directory**: A top-level directory in the repository that contains a plugin (identified by having a `.claude-plugin/plugin.json` manifest or a `tests/run-all.sh` script).
- **PR Title**: The title of the pull request, which must conform to the Conventional Commits format for downstream release-please compatibility.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every pull request receives automated test feedback within 5 minutes of opening or updating.
- **SC-002**: No PR with failing plugin tests can appear to have passing CI checks (test failures are always surfaced).
- **SC-003**: Non-conventional PR titles are caught and rejected with actionable feedback before merge.
- **SC-004**: Documentation-only PRs complete CI checks within 1 minute by skipping unnecessary test execution.
- **SC-005**: Contributors can self-correct invalid PR titles on the first attempt using the error message guidance alone, without needing to consult external documentation.
- **SC-006**: The workflow correctly identifies and tests all changed plugins when multiple plugins are modified in a single PR.

## Assumptions

- The repository uses GitHub as the hosting platform and GitHub Actions as the CI system.
- Each plugin directory contains a `tests/run-all.sh` script that runs Layers 1, 4, and 5 by default and exits with a non-zero code on failure.
- The `ubuntu-latest` runner has `bash` available and no additional tooling is required to run the test suites (no Python, Node.js, or other runtimes needed beyond what ubuntu-latest provides).
- Plugin directories are top-level directories in the repository (not nested) and can be identified by the presence of changed files in `git diff` output.
- The PR title is the sole source of truth for conventional commit validation (individual commit messages within the PR are not validated, since the repo uses squash merging).
- release-please (SPEC-003) will be configured separately and depends on this workflow's title validation to ensure parseable commit messages on main.
- The `specify` CLI tool (SpecKit dependency) is not required on the CI runner -- only `bash` is needed to execute the test scripts.
- PR title validation does not verify that the scope matches an actual plugin directory name -- a typo in the scope is accepted as a known risk for a solo maintainer workflow.
