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
- What happens when `git diff --name-only` returns files at the repository root (e.g., `.gitignore`, `CLAUDE.md`) or in non-plugin infrastructure directories (e.g., `.specify/`, `.github/`, `.worktrees/`)? These should not be treated as plugin directories. The `test -f "$dir/.claude-plugin/plugin.json"` filter in the detect job ensures only actual plugin directories are selected -- infrastructure directories like `.specify/` do not contain a plugin manifest and are automatically excluded.
- What happens when the PR title contains unicode characters or special characters in the scope? The regex should handle standard ASCII type prefixes while allowing flexible scope and description content.
- What happens when the PR has no changed files (empty PR)? The plugin test job should skip gracefully.
- What happens when a plugin's test suite has a non-zero exit code due to a test runner error (not a test failure)? The CI job should still report failure so the issue is surfaced.
- Multi-line PR titles are not possible -- GitHub enforces single-line titles at the platform level, so the regex does not need multi-line handling.
- Draft PRs do not trigger the workflow. When a draft is marked ready for review, the `ready_for_review` event fires and triggers both validation jobs.
- What happens when the detect job fails (e.g., `git diff` command errors out)? The test job depends on detect via `needs: [detect]`. GitHub Actions' default behavior is that if a `needs` job fails, dependent jobs are skipped. This is the desired behavior: a broken detect job should not allow tests to silently pass.
- What happens when `actions/checkout` fails (e.g., network error, insufficient permissions)? The step failure propagates via `set -e` and the job fails. No special handling is required beyond the standard `set -euo pipefail` error propagation, since checkout is the first step in each job.
- What exit code does validate-pr-title return on regex match failure vs. script error? The script uses `exit 1` for a non-matching title (expected failure) and relies on `set -e` to propagate unexpected errors with their original exit codes. Both cases surface as a failed check in the GitHub UI, which is the correct behavior -- the distinction between "title invalid" and "script crashed" is visible in the job logs but does not require separate exit code handling.
- What happens when the `edited` event fires due to a PR description change (not a title change)? The `pull_request.edited` activity type fires for any PR metadata edit (title, description, labels, etc.), not just title changes. The validate-pr-title job will re-run and pass (since the title did not change). This is acceptable: the job completes in seconds and the idempotent regex check produces the same result. No filtering is needed to distinguish title edits from description edits (YAGNI).
- What happens when `git diff` returns paths for deleted files? The detect job extracts only the first path component (top-level directory name) via `cut -d'/' -f1`. Deleted files still appear in `git diff --name-only` output with their full path, and the top-level directory extraction works identically for added, modified, and deleted files. The subsequent `test -f "$dir/.claude-plugin/plugin.json"` check validates the directory still exists and contains a plugin manifest.
- What happens when a plugin's `tests/run-all.sh` exists but is not executable? The test job invokes the test runner with `bash tests/run-all.sh` (explicit `bash` invocation), not `./tests/run-all.sh` (which requires execute permission). Therefore, the execute bit is not required and this scenario is not a failure mode. The `bash` prefix ensures the script runs regardless of file permissions.
- What happens when the workflow is manually re-run after a transient failure? All jobs are idempotent: the detect job re-reads the git diff (deterministic), the test job re-runs test suites (deterministic for the same code), and the validate-pr-title job re-checks the current title. Manual re-runs produce correct results with no side effects.
- What happens when the detect job's JSON output is malformed? The detect job constructs the JSON array using `jq` (pre-installed on `ubuntu-latest`). If `jq` is unavailable or the script produces invalid JSON, `fromJSON()` in the test job's matrix strategy will fail with a GitHub Actions parsing error. This is an infrastructure failure that surfaces as a failed workflow run, which is the correct behavior -- it cannot silently pass.
- What happens when a contributor force-pushes to the PR branch? A force push to the PR's head branch triggers the `synchronize` event type (FR-001), which re-runs both the detect+test pipeline and the title validation job. The three-dot diff (`origin/${{ github.base_ref }}...HEAD`) correctly handles force-pushed branches because Git recomputes the merge base on each run: `HEAD` now points to the new (rewritten) tip, and `git merge-base` finds the correct divergence point from the base branch. The detect job will re-evaluate which plugin directories changed based on the force-pushed content. The title validation job re-checks the (unchanged) title idempotently.
- What happens when a `synchronize` event fires (new commits pushed) but the PR title has not changed? The title validation job re-runs and passes, since the regex check is idempotent. This is the same behavior as described for the `edited` event on description-only changes -- the job completes in seconds with no side effects.

## Clarifications

### Session 2026-04-01

- Q: How should the workflow detect which top-level directories are plugins vs. non-plugin directories? → A: Use `.claude-plugin/plugin.json` as the sole detection signal. This aligns with Constitution Principle I which mandates every plugin MUST have this file. The presence or absence of `tests/run-all.sh` is a separate validation concern handled by FR-012.
- Q: Should the workflow trigger on PR title edits to re-run title validation? → A: Yes, add `edited` to the `pull_request` event types. Without it, fixing a PR title after a validation failure does not re-trigger the workflow, forcing contributors to push empty commits or close/reopen the PR.
- Q: What `git diff` strategy should the workflow use (fetch-depth, ref syntax, two-dot vs three-dot)? → A: Use `actions/checkout` with `fetch-depth: 0` and three-dot diff `git diff --name-only origin/${{ github.base_ref }}...HEAD`. Three-dot diff shows only changes in the PR branch relative to the merge base, avoiding false positives from base branch changes. `fetch-depth: 0` is acceptable for this small repo.
- Q: How should the workflow execute tests across multiple changed plugins (matrix vs sequential)? → A: Use a two-job pattern with dynamic matrix. Job 1 (detect) outputs changed plugin directories as a JSON array. Job 2 (test) uses `matrix.plugin` from `fromJSON()`. Each plugin gets its own parallel job with independent status reporting, satisfying FR-011.
- Q: How should the workflow handle the case when no plugin directories have changed (empty matrix)? → A: Use a conditional `if: needs.detect.outputs.plugins != '[]'` on the test matrix job. When no plugins changed, the detect job outputs an empty array `[]` and the test job skips entirely, satisfying User Story 4.

### Session 2026-04-01 (Session 2)

- Q: Should the workflow run on draft PRs, or skip until the PR is marked ready for review? → A: Skip draft PRs. Add `ready_for_review` to event types and add `if: github.event.pull_request.draft == false` condition on all jobs. When a draft is marked ready, the `ready_for_review` event fires and triggers the workflow. This saves CI resources and is standard industry practice.
- Q: Should Dependabot or other bot PRs be exempt from conventional commit title validation? → A: No exemption -- all PRs must comply, including bot PRs. Dependabot can be configured to produce compliant titles via `commit-message.prefix: "chore(deps)"` in `dependabot.yml`. This aligns with Constitution Principle V (all PR titles must be conventional commits) and Principle VI (YAGNI -- no bot exemption until bots are configured).
- Q: Is the `!` breaking change indicator placement in FR-004's regex intentional and correct? → A: Yes, confirmed correct per Conventional Commits v1.0.0 spec. The `!?` is positioned after the optional scope `(\(.+\))?` and before the colon `: `, matching the spec requirement that `!` appears "immediately before the `:`". This enables release-please to detect breaking changes for major version bumps. Both `feat!: desc` and `feat(scope)!: desc` are valid.
- Q: Should multi-line PR title input be a concern for title validation? → A: Not a concern. GitHub enforces single-line PR titles at the platform level -- the API and web UI do not allow newline characters in PR titles. The `^...$` anchors in the regex are sufficient. No multi-line handling is needed.
- Q: Should the `ci` commit type be added to the valid types list for CI infrastructure changes? → A: No. The types list (`feat|fix|chore|docs|refactor|test`) is governed by Constitution Principle V. Adding `ci` requires a constitution amendment, which is out of scope for SPEC-002. CI changes are adequately covered by `chore`. The regex must stay aligned with the constitution.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST trigger the workflow on `pull_request` events with types `opened`, `reopened`, `synchronize`, `edited`, and `ready_for_review`. All jobs MUST include a condition `if: github.event.pull_request.draft == false` to skip execution on draft PRs. Each event type serves a distinct purpose: `opened` triggers on initial PR creation; `reopened` triggers when a previously closed PR is reopened; `synchronize` triggers when new commits are pushed to the PR's head branch (including force pushes), ensuring checks re-run against the updated code; `edited` is required so that PR title changes re-trigger the title validation job; `ready_for_review` is required so that marking a draft PR as ready triggers the workflow.
- **FR-002**: System MUST run a plugin test job that detects changed top-level plugin directories by: (a) checking out with `fetch-depth: 0` to ensure full history, (b) running `git diff --name-only origin/${{ github.base_ref }}...HEAD` (three-dot diff against the merge base), (c) extracting unique top-level directory names, and (d) filtering to only those directories containing a `.claude-plugin/plugin.json` manifest.
- **FR-003**: System MUST execute `bash tests/run-all.sh` within each detected changed plugin directory.
- **FR-004**: System MUST run a PR title validation job that checks the PR title against the regex pattern `^(feat|fix|chore|docs|refactor|test)(\(.+\))?!?: .+$`. The optional `!` breaking change indicator is positioned per the Conventional Commits v1.0.0 specification (immediately before the colon) and enables release-please to detect breaking changes for major version bumps.
- **FR-005**: System MUST run the plugin test pipeline (detect + test jobs) and the PR title validation job independently, with no dependency between the title validation job and the detect/test pipeline. The detect and test jobs have an internal dependency (`needs: [detect]`) per FR-011, but neither depends on nor blocks the title validation job.
- **FR-006**: System MUST skip test execution when no plugin directories have changed files in the PR diff, implemented via a conditional `if: needs.detect.outputs.plugins != '[]'` on the test matrix job so that an empty plugin list causes the job to be skipped rather than failing due to an empty matrix.
- **FR-007**: System MUST display a clear error message when the PR title fails validation, including the expected format pattern, valid type prefixes, and at least one example of a correct title.
- **FR-008**: System MUST use pinned action versions (not floating tags like `@latest` or `@v4`) for all GitHub Actions used in the workflow.
- **FR-009**: System MUST configure minimal permissions for the workflow (read-only where possible).
- **FR-010**: System MUST run on `ubuntu-latest` with `bash` as the default shell. The workflow MUST set `defaults.run.shell: bash` at the workflow level so all `run:` steps inherit bash. Each inline script block MUST include `set -euo pipefail` as its first executable line to satisfy Constitution Principle II. Note: GitHub Actions' default bash template applies `-eo pipefail` but does NOT include `-u` (nounset); the explicit `set -euo pipefail` line is required to add `-u` and make the safety contract visible in the workflow file.
- **FR-011**: System MUST report individual test results per plugin directory using a two-job pattern: a detect job outputs changed plugin directories as a JSON array, and a test job uses a dynamic `matrix.plugin` strategy via `fromJSON()` so each plugin gets its own parallel job with independent pass/fail status visible in the GitHub Checks UI.
- **FR-012**: System MUST fail the plugin test job if any changed plugin directory does not contain a `tests/run-all.sh` script.
- **FR-013**: System MUST pass all user-controlled GitHub Actions context expressions (specifically `${{ github.event.pull_request.title }}`) to inline bash scripts via intermediate environment variables, never by direct interpolation in the script body. This prevents script injection attacks where malicious PR title content could execute arbitrary commands. The pattern is: set `env: TITLE: ${{ github.event.pull_request.title }}` at the step level, then reference `"$TITLE"` (double-quoted) inside the script. See: [GitHub Docs - Script Injections](https://docs.github.com/en/actions/concepts/security/script-injections).
- **FR-014**: System MUST process `git diff --name-only` output safely for filenames containing spaces or special characters. The detect job script MUST NOT rely on default IFS word splitting to parse filenames. Since plugin directories in this repository are constrained to top-level directories with kebab-case names (per Constitution Principle I: `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`), the current risk from special characters in plugin directory names is zero. However, changed files may reside in subdirectories with arbitrary names. The script MUST extract only the first path component (top-level directory name) using `cut -d'/' -f1` or equivalent, and pipe through `sort -u` for deduplication, ensuring that line-oriented processing is safe for the top-level directory extraction even when full file paths contain spaces.
- **FR-015**: The PR title regex `^(feat|fix|chore|docs|refactor|test)(\(.+\))?!?: .+$` MUST be evaluated for ReDoS (Regular Expression Denial of Service) safety. Analysis: the pattern is ReDoS-safe because (a) it contains no nested quantifiers (patterns like `(a+)+` that cause exponential backtracking), (b) the `.+` inside the scope group `(\(.+\))` is bounded by literal parenthesis characters that prevent ambiguous matching paths, (c) the trailing `.+$` is a single unbounded quantifier with no overlapping alternatives, and (d) the anchors `^...$` prevent partial matching loops. Bash `[[ =~ ]]` uses the system's POSIX Extended Regular Expression (ERE) engine which does use backtracking, but this pattern's structure avoids catastrophic backtracking scenarios. This analysis MUST be documented in the plan.
- **FR-016**: System MUST display the contributor's actual invalid PR title in the error output alongside the expected format, so the contributor can see exactly what was rejected. The error message MUST echo the title value (e.g., `Your title: "Update readme"`) before showing the format guidance.
- **FR-017**: System MUST display a human-readable error message (not just a non-zero exit code) when a changed plugin directory does not contain a `tests/run-all.sh` script. The message MUST include the plugin directory name and the expected file path (e.g., `ERROR: Plugin 'my-plugin' has no test runner at my-plugin/tests/run-all.sh`).
- **FR-018**: System MUST name each dynamic matrix test job to include the plugin directory name (e.g., `test (speckit-pro)`) so that the GitHub Checks UI shows per-plugin pass/fail status at a glance without expanding job logs. This is achieved by setting the `name:` field on the test job to include `${{ matrix.plugin }}`.
- **FR-019**: System MUST log a summary message in the detect job when zero plugin directories are found in the diff, explaining why the test job will be skipped (e.g., `No plugin directories changed in this PR. Test job will be skipped.`). When plugins are found, the detect job MUST log the list of detected plugin directories.
- **FR-020**: System MUST use GitHub Actions `::error::` workflow commands in the validate-pr-title and test jobs to surface failure messages as annotations in the PR Checks summary view. This ensures error messages are visible in the Checks tab without requiring the contributor to expand individual job logs. See: [GitHub Docs - Workflow Commands](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands).

### Key Entities

- **Workflow File**: The GitHub Actions workflow definition at `.github/workflows/pr-checks.yml` that orchestrates all CI checks on pull requests.
- **Plugin Directory**: A top-level directory in the repository that contains a plugin, identified solely by the presence of a `.claude-plugin/plugin.json` manifest (per Constitution Principle I). The presence of `tests/run-all.sh` is a separate validation concern: FR-012 fails the job if a detected plugin directory lacks a test runner.
- **PR Title**: The title of the pull request, which must conform to the Conventional Commits format for downstream release-please compatibility.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every pull request receives automated test feedback within 5 minutes of opening or updating.
- **SC-002**: No PR with failing plugin tests can appear to have passing CI checks (test failures are always surfaced).
- **SC-003**: Non-conventional PR titles are caught and rejected with actionable feedback before merge.
- **SC-004**: Documentation-only PRs complete CI checks within 1 minute by skipping unnecessary test execution.
- **SC-005**: The error message for invalid PR titles MUST contain all information needed for self-correction: the rejected title, the expected format pattern, all valid type prefixes, and at least one concrete example. This is measured by verifying the error output includes these four elements (see FR-007, FR-016).
- **SC-006**: The workflow correctly identifies and tests all changed plugins when multiple plugins are modified in a single PR.

## Assumptions

- The repository uses GitHub as the hosting platform and GitHub Actions as the CI system.
- Each plugin directory contains a `tests/run-all.sh` script that runs Layers 1, 4, and 5 by default and exits with a non-zero code on failure.
- The `ubuntu-latest` runner has `bash` available and no additional tooling is required to run the test suites (no Python, Node.js, or other runtimes needed beyond what ubuntu-latest provides).
- Plugin directories are top-level directories in the repository (not nested) and are identified by the presence of a `.claude-plugin/plugin.json` manifest. The detect job filters `git diff` output to only include directories matching this criterion.
- The PR title is the sole source of truth for conventional commit validation (individual commit messages within the PR are not validated, since the repo uses squash merging).
- release-please (SPEC-003) will be configured separately and depends on this workflow's title validation to ensure parseable commit messages on main.
- The `specify` CLI tool (SpecKit dependency) is not required on the CI runner -- only `bash` is needed to execute the test scripts.
- PR title validation does not verify that the scope matches an actual plugin directory name -- a typo in the scope is accepted as a known risk for a solo maintainer workflow.
- Bot PRs (e.g., Dependabot, Renovate) are not exempt from conventional commit title validation. When configuring dependency update bots in the future, they MUST be configured with a conventional commit prefix (e.g., `commit-message.prefix: "chore(deps)"` in `dependabot.yml`) to produce compliant PR titles.
