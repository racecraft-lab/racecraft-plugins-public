# Research: PR Checks Workflow

**Feature Branch**: `002-pr-checks-workflow`
**Date**: 2026-04-01

## Research Topics

### 1. GitHub Actions Dynamic Matrix Strategy

**Decision**: Use a two-job pattern where a `detect` job outputs a JSON array of changed plugin directories, and a `test` job consumes it via `matrix.plugin: ${{ fromJSON(needs.detect.outputs.plugins) }}`.

**Rationale**: Dynamic matrix allows each plugin to get its own parallel job with independent pass/fail status in the GitHub Checks UI. This satisfies FR-011's requirement for individual test results per plugin directory. The `fromJSON()` function is the standard GitHub Actions mechanism for dynamic matrices.

**Alternatives considered**:
- Sequential loop in a single job: simpler but all plugins share one pass/fail status, violating FR-011
- Hardcoded matrix: does not scale as new plugins are added
- Reusable workflow per plugin: over-engineered for the current 1-4 plugin scope

### 2. Three-Dot Diff for Changed File Detection

**Decision**: Use `git diff --name-only origin/${{ github.base_ref }}...HEAD` with `fetch-depth: 0` checkout.

**Rationale**: Three-dot diff (`A...B`) shows changes introduced on the PR branch relative to the merge base with the target branch. This avoids false positives from changes that happened on the base branch after the PR was created. Two-dot diff (`A..B`) would include base branch changes, potentially triggering tests for plugins not modified in the PR.

**Alternatives considered**:
- Two-dot diff: includes base branch changes, causing false positives
- `github.event.pull_request.base.sha...${{ github.sha }}`: the base SHA can be stale if the base branch has advanced; `origin/${{ github.base_ref }}` is more reliable with three-dot
- GitHub API changed files endpoint: adds API call complexity, limited to 300 files

### 3. Plugin Directory Detection Strategy

**Decision**: Extract unique top-level directory names from `git diff` output, then filter to only those containing `.claude-plugin/plugin.json`.

**Rationale**: Using `.claude-plugin/plugin.json` as the sole plugin detection signal aligns with Constitution Principle I, which mandates every plugin MUST have this file. The presence of `tests/run-all.sh` is a separate validation concern -- FR-012 fails the job if a detected plugin directory lacks a test runner, rather than silently skipping it.

**Alternatives considered**:
- Detecting by `tests/run-all.sh` presence: would silently skip plugins without tests rather than failing
- Reading `.claude-plugin/marketplace.json`: adds a dependency on the marketplace registry, which may not include newly added plugins
- Hardcoded list of plugin directories: does not scale

### 4. Empty Matrix Handling

**Decision**: Use `if: needs.detect.outputs.plugins != '[]'` on the test matrix job. When no plugins changed, the detect job outputs an empty array `[]` and the test job is skipped.

**Rationale**: GitHub Actions treats an empty matrix as an error by default. The conditional skip pattern avoids this error while allowing the overall workflow to succeed for non-plugin PRs (documentation-only changes).

**Alternatives considered**:
- `fail-fast: false` with empty matrix: still errors on empty matrix
- Always including a no-op entry: adds unnecessary complexity
- Separate workflow for plugin vs non-plugin changes: violates KISS principle

### 5. PR Title Regex Pattern

**Decision**: Use bash regex `^(feat|fix|chore|docs|refactor|test)(\(.+\))?!?: .+$` with `[[ "$TITLE" =~ $PATTERN ]]`.

**Rationale**: Bash regex matching via `[[ =~ ]]` is simple, requires no external dependencies, and handles the Conventional Commits v1.0.0 specification correctly. The pattern supports: required type prefix, optional scope in parentheses, optional `!` breaking change indicator positioned per spec (immediately before the colon), required colon-space separator, and required description.

**Alternatives considered**:
- External action (e.g., `amannn/action-semantic-pull-request`): adds a dependency for a simple regex check, violates KISS
- Node.js script: over-engineered for a regex match
- grep/sed: less readable than bash built-in regex

### 6. Pinned Action Versions

**Decision**: Use commit SHA pins for all third-party actions, with version comments for readability.

**Rationale**: SHA pins are immune to tag re-pointing attacks (supply chain security). FR-008 requires pinned versions. The SHA should reference the latest stable release at implementation time, with a comment noting the version for maintainability.

**Alternatives considered**:
- Floating tags (`@v4`): vulnerable to supply chain attacks if tag is re-pointed
- Minor version tags (`@v4.1`): slightly better but still mutable
- Vendoring actions: over-engineered for this use case

### 7. Workflow Permissions

**Decision**: Set top-level `permissions: {}` (no permissions) and grant `contents: read` only at the job level where needed.

**Rationale**: FR-009 requires minimal permissions. The `contents: read` permission is needed only for `actions/checkout`. PR title validation does not require any permissions beyond the default `github.event` context. Setting empty top-level permissions and granting per-job is the principle of least privilege.

**Alternatives considered**:
- Top-level `contents: read`: grants read to all jobs including title validation which does not need it
- No explicit permissions: defaults vary by repository settings, making behavior non-deterministic
