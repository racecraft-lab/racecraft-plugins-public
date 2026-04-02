# Implementation Plan: Release Automation

**Branch**: `003-release-automation` | **Date**: 2026-04-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-release-automation/spec.md`

## Summary

Create a single GitHub Actions workflow (`.github/workflows/release.yml`) that automates the entire release pipeline: release-please detects conventional commits, manages Release PRs, creates GitHub Releases with component-prefixed tags, and a conditional marketplace sync step updates `marketplace.json` from `plugin.json` versions. The workflow leverages existing SPEC-001 infrastructure (config files, sync script) and requires zero manual intervention for the commit-to-marketplace-sync lifecycle.

## Technical Context

**Language/Version**: YAML (GitHub Actions workflow syntax) + Bash (inline sync step)
**Primary Dependencies**: `googleapis/release-please-action@v4`, `actions/checkout@v4`, `jq` (pre-installed on `ubuntu-latest`)
**Storage**: N/A (git-managed config files only)
**Testing**: Manual integration testing via GitHub Actions runs; existing `bash speckit-pro/tests/run-all.sh` for regression
**Target Platform**: GitHub Actions (`ubuntu-latest` runner)
**Project Type**: CI/CD workflow (infrastructure-as-code)
**Performance Goals**: Complete full release cycle (commit to marketplace sync) within 5 minutes
**Constraints**: Single workflow file; GITHUB_TOKEN (not PAT) for infinite-loop prevention; branch protection exemption required from SPEC-004 for sync push
**Scale/Scope**: Single plugin (`speckit-pro`) with registry-driven sync supporting future multi-plugin expansion

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Plugin Structure Compliance | PASS | No plugin structure changes; workflow file lives in `.github/` outside plugin directories |
| II. Script Safety | PASS | No new scripts created; existing `sync-marketplace-versions.sh` already has `set -euo pipefail` and passes validation |
| III. Semantic Versioning | PASS | release-please manages all version bumps; workflow enforces automated versioning per constitution |
| IV. Test Coverage Before Merge | PASS | No new bash scripts requiring Layer 4 tests; workflow is tested via GitHub Actions integration |
| V. Conventional Commits | PASS | Sync commit uses `chore: sync marketplace.json versions [skip ci]` -- valid conventional commit format |
| VI. KISS, Simplicity & YAGNI | PASS | Single workflow file, two sequential steps, no abstractions or wrapper layers; reuses existing sync script |

**Gate result**: PASS -- no violations, no complexity tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/003-release-automation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
.github/
└── workflows/
    └── release.yml          # The single deliverable for SPEC-003

# Existing files (NOT modified by SPEC-003):
release-please-config.json           # Package config (from SPEC-001)
.release-please-manifest.json        # Version tracker (from SPEC-001)
scripts/sync-marketplace-versions.sh # Marketplace sync (from SPEC-001)
speckit-pro/.claude-plugin/plugin.json   # Updated by release-please
.claude-plugin/marketplace.json          # Updated by sync script
```

**Structure Decision**: Single file delivery. The workflow file at `.github/workflows/release.yml` is the only new file. All supporting infrastructure (config files, sync script) already exists from SPEC-001.

## Error Handling Design

**Failure isolation**: The release-please step and marketplace sync step fail independently. A release-please failure prevents the sync step from running (sequential dependency). A sync failure does not affect the already-created release and tag.

**Visibility**: The sync step uses default `continue-on-error: false` (FR-012), so any sync failure marks the entire workflow run as failed. This ensures GitHub Actions UI shows a red X and configured notifications fire.

**Job timeout**: The job sets `timeout-minutes: 10` (FR-013) to prevent hung runs. The target completion time is under 5 minutes.

**Self-healing sync**: The sync script is registry-driven and idempotent -- it reads the current version from each plugin's `plugin.json` and writes it to `marketplace.json` regardless of prior state. A failed sync on release N is automatically corrected by a successful sync on release N+1. No manual version correction is needed.

**No partial state persistence**: GitHub Actions runners are ephemeral. If the sync script writes to `marketplace.json` but the git commit/push fails, the workspace is discarded. The on-disk `marketplace.json` on main remains at its prior state.

**Push independence**: Workflow runs are asynchronous post-push events (FR-014). A failed workflow never blocks `git push` to main. Release-please is resumable from its persisted manifest and tag state.

## Security Design

**Least-privilege permissions**: The workflow declares exactly two permission scopes (`contents: write`, `pull-requests: write`) via the `permissions:` block (SEC-002). All unspecified scopes default to `none`. No PAT or GitHub App token is used.

**Script injection prevention**: The workflow YAML does not interpolate any user-controlled context values (`github.event.head_commit.message`, PR titles, branch names) into `run:` blocks via `${{ }}` expressions (SEC-001). The sync step's commit message is a hardcoded string. The release-please action handles commit message parsing internally without shell interpolation.

**Supply chain pinning**: Both `googleapis/release-please-action` and `actions/checkout` are pinned to specific versions (FR-008). The plan targets major version tags (`@v4`) for both actions; SHA pinning is recommended for third-party actions in production but major version tags are acceptable for the initial implementation given the high reputation of both action maintainers (Google, GitHub).

**Credential isolation**: The GITHUB_TOKEN is persisted by `actions/checkout` in `.git/config` for the sync push step (SEC-004). No untrusted third-party actions run after checkout. The sync script does not execute git commands or access credentials directly. Runner ephemerality ensures credentials are destroyed after each job.

**Log safety**: The sync script uses `set -euo pipefail` without `set -x` and outputs only version change summaries to stdout (SEC-003). GitHub Actions automatically masks the GITHUB_TOKEN in all log output.

## Complexity Tracking

> No constitution violations identified. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none)    | --         | --                                  |
