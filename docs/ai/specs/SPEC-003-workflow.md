# SpecKit Workflow: SPEC-003 — Release Automation

**Template Version**: 1.0.0
**Created**: 2026-04-01
**Purpose**: Create a GitHub Actions workflow that uses release-please to automate version bumps, changelog generation, GitHub Releases, git tags, and marketplace.json synchronization.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit.specify` | ✅ Complete | 10 FRs, 5 stories, 0 markers |
| Clarify | `/speckit.clarify` | ✅ Complete | 3 sessions, 15 questions, 0 markers |
| Plan | `/speckit.plan` | ✅ Complete | 5 artifacts, 6 research decisions, 6/6 constitution gates |
| Checklist | `/speckit.checklist` | ✅ Complete | 3 domains, 121 items, 33 gaps remediated |
| Tasks | `/speckit.tasks` | ⏳ Pending | |
| Analyze | `/speckit.analyze` | ⏳ Pending | |
| Implement | `/speckit.implement` | ⏳ Pending | |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates (SpecKit Best Practice)

Each phase requires **human review and approval** before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | All user stories clear, no `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | Ambiguities resolved, decisions documented |
| G3 | After Plan | Architecture approved, constitution gates pass, dependencies identified |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Task coverage verified, dependencies ordered |
| G6 | After Analyze | No `CRITICAL` issues, `WARNING` items reviewed |
| G7 | After Each Implementation Phase | Tests pass, manual verification complete |

---

## Prerequisites

### Constitution Validation

**Before starting any workflow phase**, verify alignment with the project constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| I. Plugin Structure | kebab-case names, required manifest fields, standard directory layout | `bash tests/run-all.sh --layer 1` |
| II. Script Safety | `#!/usr/bin/env bash`, `set -euo pipefail`, `chmod +x`, no unquoted vars | `validate-scripts.sh` |
| III. Semantic Versioning | plugin.json source of truth, semver format, release-please managed | `validate-plugin.sh` |
| IV. Test Coverage | Layer 4 unit tests for new scripts, zero failures | `bash tests/run-all.sh` |
| V. Conventional Commits | `type(scope): description` format | CI `validate-pr-title` |
| VI. KISS/Simplicity/YAGNI | Simplest approach, no speculative features, 30-second comprehension | Code review |

**Constitution Check:** ⏳ (mark before proceeding to G1)

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | SPEC-003 |
| **Name** | Release Automation |
| **Branch** | `003-release-automation` |
| **Dependencies** | SPEC-001 (Repository Foundation) — ✅ Complete |
| **Enables** | SPEC-004 (Integration & Verification) |
| **Priority** | P1 |

### Success Criteria Summary

- [ ] `.github/workflows/release.yml` exists and is valid YAML
- [ ] release-please action reads `release-please-config.json` and `.release-please-manifest.json` from SPEC-001
- [ ] release-please opens/updates Release PRs with bumped versions and generated changelogs on conventional commits to `main`
- [ ] On Release PR merge, release-please creates GitHub Releases and git tags (e.g., `speckit-pro-v1.1.0`)
- [ ] Marketplace sync step runs conditionally — only when `releases_created` is true
- [ ] `scripts/sync-marketplace-versions.sh` runs to sync plugin.json versions into marketplace.json
- [ ] Marketplace sync commit uses `chore: sync marketplace.json versions` message
- [ ] Marketplace sync commit does NOT re-trigger release-please (verified by `chore:` scope)
- [ ] Workflow has `contents: write` permission for pushing the sync commit
- [ ] All existing tests continue to pass (`bash tests/run-all.sh`)

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/003-release-automation/spec.md`

### Specify Prompt

```bash
/speckit.specify

## Feature: Release Automation

### Problem Statement
The racecraft-plugins-public marketplace repo has no automated release process. Version bumps, changelog generation, GitHub Releases, and git tags are all manual operations. When a conventional commit lands on main (via squash merge), there is no automated system to detect the commit type, bump the version in plugin.json, generate a changelog entry, create a GitHub Release, or sync the updated version into marketplace.json. This means users running `/plugin marketplace update racecraft-public-plugins` may not see new versions until manual steps are completed.

### Users
- Solo maintainer (Fredrick) who needs automated versioning and release creation after merging PRs
- Plugin consumers who need marketplace.json to reflect the latest published versions
- SPEC-004 (Integration & Verification) which depends on this workflow being operational to verify the end-to-end pipeline

### User Stories
1. As a maintainer, I need release-please to automatically detect conventional commits on main and open a Release PR with the correct version bump and generated changelog, so I don't have to manually track what changed.
2. As a maintainer, I need merging a Release PR to automatically create a GitHub Release with a git tag (e.g., `speckit-pro-v1.1.0`), so releases are discoverable and tagged in the git history.
3. As a maintainer, I need marketplace.json to automatically sync with the updated plugin.json version after a release is created, so that plugin consumers see the latest version without manual intervention.
4. As a maintainer, I need the marketplace sync commit to NOT re-trigger release-please, so there is no infinite loop of commits and releases.
5. As a maintainer, I need the workflow to distinguish between release-please updating an existing Release PR (no sync needed) and merging a Release PR (sync needed), so the sync step only runs at the right time.

### Constraints
- Workflow file: `.github/workflows/release.yml`
- Trigger: `push` to `main` branch
- Uses `googleapis/release-please-action` (official GitHub Action)
- Config: `release-please-config.json` and `.release-please-manifest.json` (created by SPEC-001)
- Marketplace sync: runs `bash scripts/sync-marketplace-versions.sh` (created by SPEC-001)
- Sync commit message: `chore: sync marketplace.json versions` (release-please ignores `chore:` commits)
- GITHUB_TOKEN permissions: `contents: write` (needed for sync commit push)
- GitHub Actions bot must be able to push to main (branch protection exemption handled by SPEC-004)
- Must follow GitHub Actions best practices (pinned action versions, minimal permissions)
- Workflow must be a single file with sequential steps (release-please first, then conditional sync)

### Out of Scope
- PR validation (handled by SPEC-002)
- Branch protection configuration (handled by SPEC-004)
- The sync script itself (created in SPEC-001 — `scripts/sync-marketplace-versions.sh`)
- npm or registry publishing (plugins are git-based per design decision)
- Stable/latest release channels (deferred — can be added later)
- Copilot code review configuration (handled by SPEC-004)

### Key Technical Decisions (Already Made)
- Release-Please Action: Using `googleapis/release-please-action` rather than CLI. The action handles token management, PR creation, and release creation as a single step.
- Marketplace Sync Timing: Sync marketplace.json as a post-release step (after tag creation), not as part of the Release PR. This keeps the Release PR clean and avoids circular commit issues.
- No Re-trigger Risk: The sync commit uses `chore:` scope, which release-please ignores by default. This prevents an infinite loop.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | FR-001 through FR-010 (10 total) |
| User Stories | 5 (P1: 3, P2: 2) |
| Acceptance Criteria | 14 scenarios + 6 success criteria |

### Files Generated

- [x] `specs/003-release-automation/spec.md`
- [x] `specs/003-release-automation/checklists/requirements.md`

---

## Phase 2: Clarify (Optional but Recommended)

**When to run:** When spec has areas that could be interpreted multiple ways.

### Clarify Prompts

#### Session 1: Release-Please Configuration

```bash
/speckit.clarify Focus on release-please configuration: How does release-please-action detect which packages changed in a monorepo? Does it use the `packages` config from release-please-config.json? How does it handle the `simple` release type with `extra-files`? What outputs does the action provide (releases_created, tag_name, etc.)? How does the manifest file get updated after a release?
```

#### Session 2: Marketplace Sync Lifecycle

```bash
/speckit.clarify Focus on marketplace sync lifecycle: When exactly does the sync step run relative to release-please outputs? How should the workflow handle a multi-plugin release where multiple plugins are bumped simultaneously? What happens if sync-marketplace-versions.sh fails — should the release be rolled back or just the sync retried? How does the GITHUB_TOKEN authenticate the sync commit push? Does the GitHub Actions bot identity prevent branch protection from blocking the push?
```

#### Session 3: Edge Cases & Failure Modes

```bash
/speckit.clarify Focus on edge cases: What happens if release-please is run but no conventional commits exist since the last release (no-op)? What if the Release PR is closed without merging — does release-please recreate it on the next push? What if marketplace.json is already in sync (idempotent run)? How does release-please handle breaking changes (`feat!:` or `BREAKING CHANGE` footer)?
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Release-Please Configuration | 5 | Output variable format (path-prefixed), version.txt auto-creation, dual+skip-ci loop protection, tag format from component field |
| 2 | Marketplace Sync Lifecycle | 5 | Same-job sequential step, registry-driven multi-plugin sync, fail-visible no-rollback, GITHUB_TOKEN via persisted credentials, branch protection deferred to SPEC-004 |
| 3 | Edge Cases & Failure Modes | 5 | No-op when no releasable commits, closed PR label recovery, idempotent sync, breaking changes bump major at v1.0.0+, bump-minor-pre-major only applies pre-1.0 |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/003-release-automation/plan.md`

### Plan Prompt

```bash
/speckit.plan

## Tech Stack
- Language: YAML (GitHub Actions workflow) + Bash (inline sync step)
- CI Platform: GitHub Actions
- Runner: ubuntu-latest
- Shell: bash
- Release Tooling: googleapis/release-please-action (official Google action)
- JSON processing: jq (used by sync-marketplace-versions.sh from SPEC-001)
- Version management: release-please with `simple` release type

## Constraints
- Workflow must be a single `.github/workflows/release.yml` file
- Two sequential steps: release-please action, then conditional marketplace sync
- release-please reads `release-please-config.json` (per-plugin package config) and `.release-please-manifest.json` (version tracker) — both created by SPEC-001
- Marketplace sync is conditional on `releases_created` output from release-please
- Sync commit must use `chore: sync marketplace.json versions` to avoid re-triggering release-please
- GITHUB_TOKEN needs `contents: write` permission
- The sync script (`scripts/sync-marketplace-versions.sh`) already exists from SPEC-001 — do not modify it

## Architecture Notes
- Trigger: `push` to `main` (catches both regular merges and squash merges)
- Step 1 (release-please): Runs on every push to main. Either opens/updates a Release PR, or creates a release if a Release PR was just merged
- Step 2 (marketplace sync): Only runs when `releases_created == 'true'`. Checks out main, runs sync script, commits, and pushes
- The sync push goes directly to main — branch protection exemption for the GitHub Actions bot is configured in SPEC-004
- release-please automatically ignores its own commits and `chore:` commits — no infinite loop risk

## Existing Infrastructure
- release-please-config.json: configures speckit-pro package with `simple` release type and `extra-files` for plugin.json
- .release-please-manifest.json: tracks current version (`{ "speckit-pro": "1.0.0" }`)
- scripts/sync-marketplace-versions.sh: reads plugin.json versions, updates marketplace.json (from SPEC-001)
- speckit-pro/tests/run-all.sh: existing test suite (369 tests passing)

## Prior Art
- SPEC-001 workflow file: docs/ai/specs/SPEC-001-workflow.md (completed workflow for reference)
- SPEC-002 workflow file: docs/ai/specs/SPEC-002-workflow.md (parallel spec for PR checks)
- Design spec: docs/ai/specs/cicd-release-pipeline-plan.md (master plan with SPEC-003 scope)
- release-please-action docs: https://github.com/googleapis/release-please-action
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ | Workflow structure, step definitions, conditional logic |
| `research.md` | ✅ | 6 decisions resolved, release-please v4 outputs, GITHUB_TOKEN |
| `data-model.md` | ✅ | 4 entities: workflow, steps, outputs, config files |
| `quickstart.md` | ✅ | Developer guide for release workflow |
| `contracts/workflow-contract.md` | ✅ | Workflow YAML contract |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit.plan` — validates both spec AND plan together.

### Recommended Domains

Based on SPEC-003's scope (GitHub Actions workflow, release-please automation, version management):

#### 1. Error Handling Checklist

Why this domain: The release workflow has multiple failure points — release-please action failures, sync script failures, git push failures. Each must be handled gracefully without leaving the repo in an inconsistent state.

```bash
/speckit.checklist error-handling

Focus on Release Automation requirements:
- release-please action failure must not block future pushes to main
- sync-marketplace-versions.sh failure must be surfaced clearly in the Actions log
- Git push failure for the sync commit must be reported (may indicate branch protection issue)
- The workflow must handle the case where release-please creates no release (no conventional commits since last release)
- Pay special attention to: ensuring a failed sync step does not leave marketplace.json out of sync permanently — the next release should re-sync
```

#### 2. Requirements Checklist

Why this domain: The workflow must correctly implement the two-step release process with proper conditional logic. Missing the `releases_created` gate or misconfiguring permissions would cause silent failures.

```bash
/speckit.checklist requirements

Focus on Release Automation requirements:
- All five user stories must have corresponding workflow logic
- The `releases_created` output must be correctly referenced to gate the sync step
- GITHUB_TOKEN permissions must include `contents: write`
- The sync commit message must be exactly `chore: sync marketplace.json versions`
- release-please-config.json and .release-please-manifest.json must be correctly referenced
- Pay special attention to: the distinction between release-please updating a PR vs. creating a release — the sync must only run on release creation
```

#### 3. Security Checklist

Why this domain: The workflow pushes directly to main using GITHUB_TOKEN. Token permissions must be minimal and the workflow must not expose secrets or allow unauthorized pushes.

```bash
/speckit.checklist security

Focus on Release Automation requirements:
- GITHUB_TOKEN permissions should be scoped to minimum required (`contents: write`)
- Action versions must be pinned to specific versions or SHA for supply chain security
- The sync step must not expose any secrets in logs
- The workflow must not allow arbitrary code execution through crafted commit messages
- Pay special attention to: ensuring the GITHUB_TOKEN scope is correct — `contents: write` is needed for both release creation and sync commit push
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| error-handling | 32 | 14 remediated | FR-012, FR-013, FR-014, edge cases |
| requirements | 56 | 4 remediated | FR-007 (permissions), FR-015 (concurrency), FR-001 scope |
| security | 33 | 15 remediated | SEC-001–SEC-004, FR-008 (pinning threats) |
| **Total** | **121** | **33 remediated** | 6 new FRs + 4 security requirements |

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/003-release-automation/tasks.md`

### Tasks Prompt

```bash
/speckit.tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: workflow skeleton → release-please step → sync step → testing → documentation
- Mark parallel-safe tasks explicitly with [P]
- Organize by workflow step (release-please, marketplace sync)

## Implementation Phases
1. Foundation (workflow file skeleton with trigger and permissions)
2. Release-Please Step (action configuration, config file references, output capture)
3. Marketplace Sync Step (conditional execution, checkout, sync script, commit and push)
4. Validation (manual testing by pushing a conventional commit, existing tests still pass)

## Constraints
- Single workflow file: `.github/workflows/release.yml`
- Must not modify scripts/sync-marketplace-versions.sh (from SPEC-001)
- Must not modify release-please-config.json or .release-please-manifest.json (from SPEC-001)
- Tests at: speckit-pro/tests/ (existing, no new test files needed for the workflow itself)
- Must verify workflow YAML is valid before committing
- Document any new CI-specific patterns in CLAUDE.md if needed
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | |
| **Phases** | |
| **Parallel Opportunities** | |
| **User Stories Covered** | |

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```bash
/speckit.analyze

Focus on:
1. Constitution alignment — verify all 6 principles are respected (especially III. Semantic Versioning, V. Conventional Commits, VI. KISS)
2. Coverage gaps — ensure all FRs and user stories have tasks
3. Consistency between task file paths and actual project structure
4. Verify release-please-action configuration matches SPEC-001's release-please-config.json
5. Verify the sync step correctly gates on releases_created output
6. Verify the sync commit message is exactly `chore: sync marketplace.json versions`
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
|    |          |       |            |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed (no coverage gaps).

### Implement Prompt

```bash
/speckit.implement

## Approach

For each task, follow this cycle:
1. Write the workflow YAML per the task description
2. Validate YAML syntax (basic structure check)
3. Verify inline scripts with bash -n where possible
4. Run existing tests to ensure nothing is broken: bash speckit-pro/tests/run-all.sh
5. Commit after each logical unit of work

### Pre-Implementation Setup

Before starting any task:
1. Verify you're on branch 003-release-automation
2. Verify all existing tests pass: bash speckit-pro/tests/run-all.sh
3. Create .github/workflows/ directory if it doesn't exist

### Implementation Notes
- GitHub Actions YAML: use 2-space indentation consistently
- Pin release-please-action to a specific version (e.g., `googleapis/release-please-action@v4`)
- Use `${{ steps.release.outputs.releases_created }}` to gate the sync step
- The sync step must: checkout main, run sync script, git add/commit/push
- Git config for the sync commit: use GitHub Actions bot identity (`github-actions[bot]`)
- Test the workflow by pushing a conventional commit to main after implementation
- The sync script already handles edge cases (missing plugin.json, idempotency) — trust it
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Workflow Skeleton | | | |
| 2 - Release-Please Step | | | |
| 3 - Marketplace Sync Step | | | |
| 4 - Validation | | | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in tasks.md
- [ ] `.github/workflows/release.yml` is valid YAML
- [ ] release-please-action correctly references config and manifest files
- [ ] Sync step is gated on `releases_created == 'true'`
- [ ] Sync commit uses `chore: sync marketplace.json versions` message
- [ ] GITHUB_TOKEN has `contents: write` permission
- [ ] No modification to SPEC-001 artifacts (sync script, release-please configs)
- [ ] All existing tests pass: `bash speckit-pro/tests/run-all.sh`
- [ ] PR created with conventional commit title
- [ ] PR reviewed and merged

---

## Lessons Learned

### What Worked Well

-

### Challenges Encountered

-

### Patterns to Reuse

-

---

## Project Structure Reference

```text
racecraft-plugins-public/
├── .github/
│   └── workflows/
│       ├── pr-checks.yml              # From SPEC-002
│       └── release.yml                # NEW: Release automation workflow
├── .claude-plugin/
│   └── marketplace.json               # Updated by sync script post-release
├── scripts/
│   └── sync-marketplace-versions.sh   # From SPEC-001 (runs in sync step)
├── speckit-pro/
│   ├── .claude-plugin/
│   │   └── plugin.json                # Version source of truth (bumped by release-please)
│   └── tests/
│       ├── lib/assertions.sh          # Shared test assertions
│       ├── layer4-scripts/            # Script unit tests
│       └── run-all.sh                 # Test orchestrator (Layers 1, 4, 5)
├── release-please-config.json         # From SPEC-001 (read by release-please-action)
├── .release-please-manifest.json      # From SPEC-001 (updated by release-please)
└── docs/ai/specs/
    ├── cicd-release-pipeline-plan.md  # Master plan
    ├── SPEC-001-workflow.md           # Completed
    ├── SPEC-002-workflow.md           # Parallel spec (PR checks)
    └── SPEC-003-workflow.md           # This file
```

---

Template based on SpecKit best practices. Populated with SPEC-003 Release Automation context from the CI/CD Release Pipeline master plan.
