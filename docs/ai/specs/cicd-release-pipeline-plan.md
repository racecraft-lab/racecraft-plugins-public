# CI/CD & Release Pipeline Implementation Roadmap

**Implement a CI/CD pipeline, trunk-based development workflow, and automated plugin versioning for the racecraft-plugins-public marketplace, aligned with official Anthropic plugin documentation.**

This document defines the specification roadmap for the CI/CD & Release Pipeline. Each specification is executed end-to-end through the SpecKit workflow (specify → clarify → plan → checklist → tasks → analyze → implement) before moving to the next.

**Branch:** `feat/cicd-release-pipeline`
**Design Spec:** [2026-03-24-cicd-versioning-release-pipeline-design.md](../superpowers/specs/2026-03-24-cicd-versioning-release-pipeline-design.md)

---

## Table of Contents

1. [Roadmap Overview](#roadmap-overview)
2. [Dependency Graph](#dependency-graph)
3. [Progress Tracking](#progress-tracking)
4. [Specification Sections](#specification-sections)

---

## Roadmap Overview

The feature is decomposed into **4 specifications** across **3 dependency tiers**:

| Tier | Specs | Purpose | Parallelization |
|------|-------|---------|-----------------|
| **1** | SPEC-001 | Repository foundation — config files, sync script, version dedup fix | Sequential |
| **2** | SPEC-002, SPEC-003 | PR checks workflow, Release automation workflow | Parallel possible |
| **3** | SPEC-004 | Branch protection, Copilot review, end-to-end integration verification | Sequential (depends on all above) |

**Execution Order:** SPEC-001 → (SPEC-002 ‖ SPEC-003) → SPEC-004

**Dependency Constraints:**
- SPEC-002 requires SPEC-001 (PR checks need the config files and test runner to exist)
- SPEC-003 requires SPEC-001 (release workflow needs release-please config and sync script)
- SPEC-002 and SPEC-003 can run in parallel (independent GitHub Actions workflows)
- SPEC-004 requires SPEC-002 and SPEC-003 (branch protection rules reference CI check names; end-to-end verification needs all workflows operational)

---

## Dependency Graph

```text
SPEC-001 (Repository Foundation)
    │
    ├──► SPEC-002 (PR Checks Workflow) ────────► ┐
    │                                             │
    └──► SPEC-003 (Release Automation) ──────────►│
                                                  ▼
                                   SPEC-004 (Integration & Verification)
                                                  │
                                       ─── FEATURE COMPLETE ───
```

---

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|------|------|--------|---------------|------------|
| SPEC-001 | Repository Foundation | ✅ Complete | [SPEC-001-workflow.md](SPEC-001-workflow.md) | Done |
| SPEC-002 | PR Checks Workflow | 🔄 In Progress | [SPEC-002-workflow.md](SPEC-002-workflow.md) | Specify |
| SPEC-003 | Release Automation | 🔄 In Progress | [SPEC-003-workflow.md](SPEC-003-workflow.md) | Specify |
| SPEC-004 | Integration & Verification | ⏳ Pending | [SPEC-004-workflow.md](SPEC-004-workflow.md) | Blocked by SPEC-002, SPEC-003 |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

---

## Specification Sections

### SPEC-001: Repository Foundation

**Priority:** P1 | **Depends On:** None | **Enables:** SPEC-002, SPEC-003, SPEC-004

**Goal:** Set up the release-please configuration, version sync script, and fix the version duplication problem so that automated versioning infrastructure is ready for CI workflows.

**Scope:**
- Create `release-please-config.json` at the repo root with `release-type: "simple"`, per-plugin package configuration for `speckit-pro`, and `extra-files` using the GenericJson updater format (`type: "json"`, `path: ".claude-plugin/plugin.json"`, `jsonpath: "$.version"`) with paths relative to the package directory
- Create `.release-please-manifest.json` at the repo root tracking the current version per plugin (`{ "speckit-pro": "1.0.0" }`)
- Create `scripts/sync-marketplace-versions.sh` — a bash script that reads each plugin's `.claude-plugin/plugin.json` version field and updates the matching entry's `version` field in `.claude-plugin/marketplace.json`. Must follow existing script conventions: `#!/usr/bin/env bash`, `set -euo pipefail`, handle the case where a plugin exists in `marketplace.json` but has no `plugin.json` (skip with warning)
- Fix version duplication: currently `version: "1.0.0"` is set in both `speckit-pro/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`. Per Anthropic docs, `plugin.json` always wins silently. Resolution: keep `version` in `plugin.json` as source of truth, and have the sync script manage the `marketplace.json` version field. The initial state should match (both `1.0.0`)
- Add Layer 4 unit tests for `sync-marketplace-versions.sh` following the existing pattern in `speckit-pro/tests/layer4-scripts/` using the shared assertions library at `tests/lib/assertions.sh`. Tests should cover: single plugin sync, multi-plugin sync, missing plugin.json handling, and idempotency

**Out of Scope:**
- GitHub Actions workflows (handled by SPEC-002, SPEC-003)
- Branch protection configuration (handled by SPEC-004)
- Changelog generation (handled automatically by release-please in SPEC-003)

**Key Decisions:**

**[Version Source of Truth] Decision (2026-03-24):** `plugin.json` is the version source of truth, synced to `marketplace.json` by a script. This aligns with Anthropic's documented behavior where `plugin.json` always takes precedence over `marketplace.json`.
Alternatives considered: marketplace.json as source of truth (contradicts Anthropic docs); removing version from marketplace.json entirely (loses discoverability).

**[Release Type] Decision (2026-03-24):** Using `release-type: "simple"` because this is not a standard language package (Node/Python/Java). The `simple` type works with `extra-files` for custom version file locations.
Alternatives considered: `node` type (would require package.json, which doesn't exist); `generic` type (deprecated in favor of `simple`).

**Key Files:**
- `release-please-config.json` — New: per-plugin release configuration
- `.release-please-manifest.json` — New: current version tracker
- `scripts/sync-marketplace-versions.sh` — New: reads plugin.json versions, updates marketplace.json
- `.claude-plugin/marketplace.json` — Modified: version field now managed by sync script
- `speckit-pro/.claude-plugin/plugin.json` — Unchanged (already correct as source of truth)
- `tests/layer4-scripts/test-sync-marketplace-versions.sh` — New: unit tests for sync script

---

### SPEC-002: PR Checks Workflow

**Priority:** P1 | **Depends On:** SPEC-001 | **Enables:** SPEC-004

**Goal:** Create a GitHub Actions workflow that validates every PR with scoped plugin tests and conventional commit PR title enforcement.

**Scope:**
- Create `.github/workflows/pr-checks.yml` triggered on `pull_request` targeting `main` with two parallel jobs:
  - **`validate-plugins` job:** Use `git diff` against the base branch to detect which top-level plugin directories were modified. For each changed plugin that has a `tests/run-all.sh`, run `bash tests/run-all.sh` (which executes Layers 1, 4, 5 by default). Skip testing entirely if no plugin directories changed (e.g., README-only PRs). The job should use `ubuntu-latest` and `bash` shell.
  - **`validate-pr-title` job:** Check that the PR title matches the Conventional Commits pattern `^(feat|fix|chore|docs|refactor|test)(\(.+\))?!?: .+$`. This is required for release-please to correctly parse squashed commits on main. Fail the job with a clear error message if the title doesn't match, including an example of the expected format.
- Both jobs must be independently runnable (no job dependencies between them) so they execute in parallel
- The workflow must handle the `synchronize` event (new commits pushed to PR) in addition to `opened` and `reopened`

**Out of Scope:**
- Layers 2/3 AI evals (local only, per design decision)
- Copilot code review configuration (handled by SPEC-004 — it's a GitHub repo setting, not a workflow)
- Release automation (handled by SPEC-003)
- Branch protection rules (handled by SPEC-004)

**Key Decisions:**

**[Test Scoping] Decision (2026-03-24):** Only run tests for changed plugins, not all plugins. This keeps CI fast as the marketplace grows to 2-4 plugins.
Alternatives considered: running all tests regardless of changes (would slow CI unnecessarily); per-file test scoping (too granular, plugin is the right unit).

**[PR Title Validation] Decision (2026-03-24):** Validate PR title format but NOT scope against actual plugin directories. A typo like `feat(spekit-pro):` passes validation but release-please ignores it. This is an accepted risk documented in the design spec — adding directory validation adds complexity for marginal benefit with a solo maintainer.
Alternatives considered: validating scope against directory names (more complex, diminishing returns for solo maintainer).

**Key Files:**
- `.github/workflows/pr-checks.yml` — New: PR validation workflow with two parallel jobs

---

### SPEC-003: Release Automation

**Priority:** P1 | **Depends On:** SPEC-001 | **Enables:** SPEC-004

**Goal:** Create a GitHub Actions workflow that uses release-please to automate version bumps, changelog generation, GitHub Releases, git tags, and marketplace.json synchronization.

**Scope:**
- Create `.github/workflows/release.yml` with two sequential steps triggered on push to `main`:
  - **Step 1 — release-please:** Use the `googleapis/release-please-action` to detect conventional commits on `main`, open/update Release PRs per plugin with bumped versions and generated changelogs, and on Release PR merge, create GitHub Releases and git tags (e.g., `speckit-pro-v1.1.0`). Configure with `config-file: release-please-config.json` and `manifest-file: .release-please-manifest.json`.
  - **Step 2 — marketplace sync:** Conditional on release-please creating a release (not just updating a PR). Run `bash scripts/sync-marketplace-versions.sh` to read the updated `plugin.json` version(s) and sync into `.claude-plugin/marketplace.json`. Commit the change with message `chore: sync marketplace.json versions` and push to `main`. This push requires `GITHUB_TOKEN` permissions configured with `contents: write` and the GitHub Actions bot must be exempted from branch protection rules (configured in SPEC-004).
- The workflow must handle the case where release-please updates an existing Release PR (no sync needed) vs. merges a Release PR (sync needed). Use the `releases_created` output from the release-please action to gate the sync step.
- The marketplace sync commit must NOT re-trigger release-please (release-please ignores its own commits by default, but verify this behavior)

**Out of Scope:**
- PR validation (handled by SPEC-002)
- Branch protection configuration (handled by SPEC-004)
- The sync script itself (created in SPEC-001)
- npm or registry publishing (plugins are git-based per design decision)

**Key Decisions:**

**[Release-Please Action] Decision (2026-03-24):** Using the official `googleapis/release-please-action` GitHub Action rather than the CLI directly. The action handles token management, PR creation, and release creation as a single step.
Alternatives considered: release-please CLI in a custom script (more flexible but more maintenance); changesets (different philosophy, less aligned with conventional commits).

**[Marketplace Sync Timing] Decision (2026-03-24):** Sync marketplace.json as a post-release step (after tag creation), not as part of the Release PR. This keeps the Release PR clean (only version bumps and changelogs) and avoids circular commit issues.
Alternatives considered: including marketplace.json in the Release PR (risk of circular updates); manual sync (defeats automation goal).

**Key Files:**
- `.github/workflows/release.yml` — New: release-please + marketplace sync workflow

---

### SPEC-004: Integration & Verification

**Priority:** P1 | **Depends On:** SPEC-001, SPEC-002, SPEC-003 | **Enables:** Complete feature

**Goal:** Configure GitHub branch protection rules, enable Copilot code review, and verify the complete end-to-end workflow from feature branch to user-visible release.

**Scope:**
- Configure GitHub branch protection on `main` via `gh api` or GitHub UI (document the exact settings):
  - Require pull request before merging (no direct pushes)
  - Require status checks to pass: `validate-plugins` and `validate-pr-title` (the job names from SPEC-002)
  - Require Copilot code review (enable in repository settings → Code review → Copilot)
  - Allow only squash merges (disable merge commits and rebase merges)
  - Exempt the GitHub Actions bot from branch protection (needed for SPEC-003's marketplace sync push)
- Create a verification checklist script or document that walks through the complete workflow end-to-end:
  1. Create a feature branch with a test change
  2. Open a PR with a conventional commit title
  3. Verify CI runs Layers 1, 4, 5 and PR title validation
  4. Verify Copilot review appears
  5. Squash merge the PR
  6. Verify release-please opens/updates a Release PR
  7. Merge the Release PR
  8. Verify GitHub Release created with correct tag
  9. Verify marketplace.json synced with updated version
  10. Verify `/plugin marketplace update racecraft-public-plugins` sees the new version
- Update `CLAUDE.md` to document the new workflow: branching strategy, PR requirements, release process, how to add new plugins to the release-please config, and the user update path (`/plugin marketplace update racecraft-public-plugins`)
- Update `AGENTS.md` if needed to reflect the new CI/CD conventions
- Document recovery & rollback procedures in `CLAUDE.md`: re-running the sync workflow (`gh workflow run release.yml`), reverting a bad release via a `fix()` commit, and using `Release-As: X.Y.Z` to force a specific version

**Out of Scope:**
- Stable/latest release channels (out of scope per design decision — can be added later)
- Community contribution workflows (solo maintainer per design decision)
- Modifying any existing plugin code or tests

**Key Decisions:**

**[Branch Protection Bypass] Decision (2026-03-24):** The GitHub Actions bot is exempted from branch protection to allow the marketplace sync commit to push directly to `main`. This is a standard pattern for CI-generated commits. The bot's commits are `chore:` scoped, which release-please ignores (no infinite loop risk).
Alternatives considered: opening a follow-up PR for the sync (adds noise and manual merge step); using a GitHub App token (more complex setup for same result).

**Key Files:**
- `CLAUDE.md` — Modified: add CI/CD workflow documentation
- `AGENTS.md` — Modified: add CI/CD conventions if needed
- `docs/ai/specs/cicd-verification-checklist.md` — New: end-to-end verification steps

---

## Environment & Deployment Context

### Existing Infrastructure (No Changes Needed)

| Resource | Detail |
|----------|--------|
| GitHub Repository | `racecraft-lab/racecraft-plugins-public` on GitHub with `origin` remote |
| Test Suite | 5-layer shell-based test suite in `speckit-pro/tests/` (346 tests passing) |
| Conventional Commits | Already in use (`feat(scope):`, `fix(scope):`, `chore:`) |
| SpecKit CLI | Installed via `uv tool install specify-cli` |
| GitHub Copilot Pro+ | Available for code review on PRs |

### Changes Required

| Change | Where | Detail |
|--------|-------|--------|
| Add release-please config | Repo root | `release-please-config.json`, `.release-please-manifest.json` |
| Add sync script | `scripts/` | `sync-marketplace-versions.sh` |
| Add CI workflows | `.github/workflows/` | `pr-checks.yml`, `release.yml` |
| Configure branch protection | GitHub repo settings | Require PR, CI checks, Copilot review, squash-only |
| Exempt Actions bot | GitHub repo rulesets | Allow CI bot to push marketplace sync commits |

### Local Development Setup

| Requirement | How |
|-------------|-----|
| GitHub CLI | `brew install gh` (for branch protection config and PR workflows) |
| SpecKit CLI | `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git` |
| Claude Code | Required for local plugin testing via `claude --plugin-dir` |
| jq | `brew install jq` (used by sync-marketplace-versions.sh) |

---

## References

- **Design Spec:** [2026-03-24-cicd-versioning-release-pipeline-design.md](../superpowers/specs/2026-03-24-cicd-versioning-release-pipeline-design.md)
- **SpecKit Workflow Template:** `docs/ai/speckit-workflow-template.md`
- **Project Standards:** [CLAUDE.md](../../../CLAUDE.md), [AGENTS.md](../../../AGENTS.md)
- **Anthropic Plugin Docs:** [Plugins Reference](https://code.claude.com/docs/en/plugins-reference), [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- **release-please:** [GitHub](https://github.com/googleapis/release-please), [Action](https://github.com/googleapis/release-please-action)
- **Conventional Commits:** [Specification](https://www.conventionalcommits.org/)
