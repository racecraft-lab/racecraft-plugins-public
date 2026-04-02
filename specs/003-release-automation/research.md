# Research: Release Automation

**Date**: 2026-04-01 | **Branch**: `003-release-automation`

## Research Tasks

### 1. release-please-action v4 Monorepo Output Format

**Decision**: Use path-prefixed output variables with double-dash separator: `steps.release.outputs['speckit-pro--release_created']`

**Rationale**: The v4 release-please-action uses the package path as a prefix for all outputs in monorepo mode. The top-level `releases_created` (plural) output is bugged in v4 and always returns `true`. The per-component `release_created` (singular) with path prefix is the reliable mechanism. Bracket notation is required when paths contain `/`, but since `speckit-pro` has no `/`, dot notation also works. Bracket notation is used consistently for clarity.

**Alternatives considered**:
- Top-level `releases_created` output: Rejected -- bugged in v4, always returns `true`
- `release_created` without path prefix: Rejected -- not available in monorepo mode

### 2. Workflow Authentication and Infinite-Loop Prevention

**Decision**: Use `GITHUB_TOKEN` with `permissions: contents: write` and `actions/checkout` default `persist-credentials: true`

**Rationale**: GITHUB_TOKEN provides dual infinite-loop protection: (1) commits made with GITHUB_TOKEN do not trigger subsequent workflow runs (GitHub built-in), and (2) the `chore:` commit type is ignored by release-please. Using a PAT or GitHub App token would lose protection (1) but retain protection (2) plus `[skip ci]` in the commit message.

**Alternatives considered**:
- Personal Access Token (PAT): Rejected -- loses GITHUB_TOKEN's built-in loop prevention
- GitHub App token: Rejected -- adds complexity without benefit for this use case
- Separate `actions/checkout` step with explicit token: Rejected -- default behavior is sufficient

### 3. Marketplace Sync Commit Strategy

**Decision**: Use inline bash steps within the workflow job (checkout, run sync, configure git, commit, push) rather than a separate composite action or reusable workflow

**Rationale**: Keeps the entire workflow in a single file per FR-010. The sync logic is straightforward: check if sync script produced changes, commit with the required message, push. No reuse need exists since this is the only workflow that performs marketplace sync.

**Alternatives considered**:
- Composite action: Rejected -- over-engineering for 5 lines of bash; violates KISS principle
- Reusable workflow: Rejected -- adds cross-file complexity for a single-use step
- Separate job: Rejected -- requires cross-job output passing; same-job step is simpler

### 4. release-please Action Version Pinning

**Decision**: Pin to major version tag `googleapis/release-please-action@v4` rather than full SHA

**Rationale**: Major version tags (`@v4`) receive security patches and bug fixes automatically. Full SHA pinning provides stronger supply-chain security but requires manual updates for patches. Given this is a first-party Google action with strong maintenance practices, major version pinning balances security with maintainability. FR-008 requires pinning to "a specific version (SHA or major version tag)."

**Alternatives considered**:
- Full SHA pin: Valid but rejected for maintenance burden; can be adopted later if supply-chain policy requires it
- Minor version pin (`@v4.1`): Not standard practice for GitHub Actions; not supported by release-please-action tagging scheme

### 5. Git Identity for Sync Commit

**Decision**: Use `github-actions[bot]` identity (`41898282+github-actions[bot]@users.noreply.github.com`) for the sync commit

**Rationale**: This is the standard identity for automated commits made by GitHub Actions workflows using GITHUB_TOKEN. It produces clean, attributable commits that are clearly automated. The bot identity is exempt from branch protection rules when SPEC-004 configures the bypass.

**Alternatives considered**:
- Custom bot identity: Rejected -- unnecessary complexity; standard identity is well-recognized
- No git config (use checkout defaults): Rejected -- `actions/checkout` does not configure user.name/user.email for commits

### 6. Handling `git diff` for Idempotent Sync Commits

**Decision**: Check `git diff --quiet` after running the sync script; only commit if changes exist

**Rationale**: The sync script itself is idempotent (exits 0 with no file write when versions match), but git operations should also be guarded. Checking `git diff --quiet` before committing prevents empty commits and ensures clean workflow runs when no version changes occurred.

**Alternatives considered**:
- Always commit (let git reject empty commits): Rejected -- `git commit` fails on empty diff without `--allow-empty`, causing workflow failure
- Check sync script exit code only: The sync script exits 0 in both changed/unchanged cases; cannot distinguish without file-level diff check
