# SpecKit Workflow: SPEC-004 — Integration & Verification

**Template Version**: 1.0.0
**Created**: 2026-04-03
**Purpose**: Configure GitHub branch protection rules, enable Copilot code review, and verify the complete end-to-end workflow from feature branch to user-visible release.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit.specify` | ⏳ Pending | |
| Clarify | `/speckit.clarify` | ⏳ Pending | Optional but recommended |
| Plan | `/speckit.plan` | ⏳ Pending | |
| Checklist | `/speckit.checklist` | ⏳ Pending | Run for each domain |
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
| **Spec ID** | SPEC-004 |
| **Name** | Integration & Verification |
| **Branch** | `004-integration-verification` |
| **Dependencies** | SPEC-001 (Repository Foundation) — ✅ Complete, SPEC-002 (PR Checks Workflow) — ✅ Complete, SPEC-003 (Release Automation) — ✅ Complete |
| **Enables** | Complete feature — CI/CD pipeline fully operational |
| **Priority** | P1 |

### Success Criteria Summary

- [ ] Branch protection configured on `main`: require PR, require CI checks (`validate-plugins`, `validate-pr-title`), squash-only merges
- [ ] Copilot code review enabled in repository settings
- [ ] GitHub Actions bot exempted from branch protection for marketplace sync pushes
- [ ] End-to-end verification checklist created and documented
- [ ] CLAUDE.md updated with CI/CD workflow documentation (branching strategy, PR requirements, release process, adding new plugins)
- [ ] Recovery & rollback procedures documented (re-run sync, revert bad release, `Release-As`)
- [ ] AGENTS.md updated if needed to reflect CI/CD conventions
- [ ] All existing tests continue to pass (`bash tests/run-all.sh`)

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/004-integration-verification/spec.md`

### Specify Prompt

```bash
/speckit.specify

## Feature: Integration & Verification

### Problem Statement
The racecraft-plugins-public marketplace repo now has CI workflows (SPEC-002: PR checks, SPEC-003: release automation) and versioning infrastructure (SPEC-001: release-please config, sync script), but there are no GitHub branch protection rules to enforce these workflows. PRs can still be merged without passing CI checks, without Copilot review, and via non-squash merges that would break release-please's commit parsing. Additionally, the CI/CD pipeline has never been verified end-to-end — from feature branch creation through to a user running `/plugin marketplace update` and seeing the new version. Finally, the project documentation (CLAUDE.md, AGENTS.md) does not describe the new workflow, leaving future contributors (or the solo maintainer after a break) without guidance on how to use the pipeline.

### Users
- Solo maintainer (Fredrick) who needs branch protection to enforce CI quality gates
- Solo maintainer who needs documentation of the workflow for future reference
- Future contributors who need to understand PR requirements and the release process
- Plugin consumers who benefit from the verified end-to-end pipeline ensuring marketplace.json accuracy

### User Stories
1. As a maintainer, I need branch protection rules on `main` that require passing CI checks (`validate-plugins` and `validate-pr-title`) before merging, so that broken code and non-conventional commit titles cannot reach the main branch.
2. As a maintainer, I need Copilot code review enabled on PRs, so that I get automated code quality feedback before merging.
3. As a maintainer, I need squash-only merges enforced, so that each merged PR produces exactly one conventional commit on main for release-please to parse.
4. As a maintainer, I need the GitHub Actions bot exempted from branch protection, so that the marketplace sync commit from SPEC-003's release workflow can push directly to main without being blocked.
5. As a maintainer, I need a documented end-to-end verification checklist that walks through the complete workflow (feature branch → PR → CI → merge → release-please → GitHub Release → marketplace sync → user update), so that I can verify the pipeline works correctly and diagnose any issues.
6. As a maintainer, I need CLAUDE.md updated with the CI/CD workflow documentation (branching strategy, PR requirements, release process, how to add new plugins to release-please config, and the user update path), so that all conventions are discoverable in one place.
7. As a maintainer, I need recovery & rollback procedures documented (re-running sync workflow, reverting a bad release via `fix()` commit, using `Release-As: X.Y.Z` to force a version), so I can handle edge cases without researching release-please docs each time.

### Constraints
- Branch protection configuration via `gh api` commands (scriptable and reproducible)
- Copilot review is a repository setting, not a workflow — enabled via GitHub UI or API
- Branch protection must allow the GitHub Actions bot to push (needed for SPEC-003 marketplace sync)
- Squash merge only (disable merge commits and rebase merges)
- Required status checks reference the exact job names from SPEC-002: `validate-plugins`, `validate-pr-title`
- Verification checklist should be a markdown document in `docs/ai/specs/`
- CLAUDE.md changes must follow the existing document structure
- All documentation changes must be accurate to the actual implemented workflows from SPEC-001, SPEC-002, SPEC-003
- No changes to any existing plugin code, tests, or CI workflows

### Out of Scope
- Stable/latest release channels (deferred — can be added later)
- Community contribution workflows (solo maintainer per design decision)
- Modifying any existing plugin code, tests, or CI workflows
- GitHub Environments or deployment protection rules
- Code owners file (CODEOWNERS) — solo maintainer
- Issue templates or PR templates (nice-to-have, not in scope)

### Key Technical Decisions (Already Made)
- Branch Protection Bypass: The GitHub Actions bot is exempted from branch protection to allow the marketplace sync commit to push directly to main. This is a standard pattern for CI-generated commits. The bot's commits are `chore:` scoped, which release-please ignores.
- Squash-Only Merges: Required so that each PR produces exactly one conventional commit, which release-please can reliably parse for version bumps.
- Documentation in CLAUDE.md: CI/CD workflow docs go in CLAUDE.md (not a separate docs/ file) because CLAUDE.md is the primary project reference that Claude Code loads automatically.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | |
| User Stories | |
| Acceptance Criteria | |

### Files Generated

- [ ] `specs/004-integration-verification/spec.md`

---

## Phase 2: Clarify (Optional but Recommended)

**When to run:** When spec has areas that could be interpreted multiple ways.

### Clarify Prompts

#### Session 1: Branch Protection Configuration

```bash
/speckit.clarify Focus on branch protection configuration: What exact GitHub API endpoints are needed to configure branch protection rules vs. rulesets? Should we use the legacy branch protection API or the newer repository rulesets API? How does the GitHub Actions bot exemption work — is it by actor type or by specific app? Does the `validate-plugins` job need special handling since it uses a dynamic matrix (the job name may differ)? What happens if a required status check is pending but the PR has no relevant changes (e.g., docs-only PR where validate-plugins skips)?
```

#### Session 2: Copilot Code Review Setup

```bash
/speckit.clarify Focus on Copilot code review: Is Copilot code review configurable via API or only through the GitHub UI? Can it be made a required check or is it advisory only? Does it work with the current GitHub plan (Pro+)? Are there any repository settings needed beyond enabling it? How does it interact with branch protection — is it a separate check or part of the PR review requirement?
```

#### Session 3: Documentation & Verification Scope

```bash
/speckit.clarify Focus on documentation and verification: Should the verification checklist be automated (a script that checks each step) or a manual walkthrough document? How detailed should the CLAUDE.md CI/CD section be — just the workflow overview or also include troubleshooting? Should recovery procedures reference specific `gh` commands or just describe the concepts? What sections of CLAUDE.md need updating vs. which are new sections?
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/004-integration-verification/plan.md`

### Plan Prompt

```bash
/speckit.plan

## Tech Stack
- Language: Bash (gh CLI commands for branch protection), Markdown (documentation)
- CLI Tools: GitHub CLI (`gh`) for API interactions
- Platform: GitHub repository settings, branch protection rules
- Testing: Manual end-to-end verification (no new automated tests — this spec is configuration + documentation)

## Constraints
- Branch protection configured via `gh api` for reproducibility (not just UI clicks)
- Copilot review may require GitHub UI configuration (verify API availability)
- Required status checks must match exact job names from SPEC-002's pr-checks.yml: `detect`, `test`, `validate-pr-title`
- GitHub Actions bot exemption must not weaken protection for human users
- CLAUDE.md updates must integrate with existing document structure (not a separate document)
- Verification checklist must reference actual CI job names and workflow files from SPEC-001, SPEC-002, SPEC-003
- No new test files — this spec creates configuration and documentation only

## Architecture Notes
- This spec is primarily configuration (GitHub settings) and documentation (CLAUDE.md, verification checklist)
- Branch protection uses either the legacy Branch Protection API (`/repos/{owner}/{repo}/branches/{branch}/protection`) or the newer Repository Rulesets API — research which is appropriate
- The verification checklist is a manual walkthrough, not an automated script — the end-to-end flow involves GitHub UI, CI, and release-please which cannot be fully automated in a test
- Recovery procedures should include actual `gh` commands that can be copy-pasted

## Existing Infrastructure
- `.github/workflows/pr-checks.yml` — PR validation with `detect`, `test`, `validate-pr-title` jobs (SPEC-002)
- `.github/workflows/release.yml` — Release-please + marketplace sync (SPEC-003)
- `scripts/sync-marketplace-versions.sh` — Marketplace version sync script (SPEC-001)
- `release-please-config.json` — Per-plugin release configuration (SPEC-001)
- `.release-please-manifest.json` — Version tracker (SPEC-001)
- `CLAUDE.md` — Project instructions (needs CI/CD section added)
- `AGENTS.md` — Agent instructions (may need CI/CD conventions added)
- `speckit-pro/tests/run-all.sh` — Test suite (369 tests passing, must remain passing)

## Prior Art
- SPEC-001 workflow: docs/ai/specs/SPEC-001-workflow.md (completed — config + sync script)
- SPEC-002 workflow: docs/ai/specs/SPEC-002-workflow.md (completed — PR checks)
- SPEC-003 workflow: docs/ai/specs/SPEC-003-workflow.md (completed — release automation)
- Technical roadmap: docs/ai/specs/cicd-release-pipeline-technical-roadmap.md (master plan with SPEC-004 scope)
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Configuration steps, documentation structure |
| `research.md` | ⏳ | Branch protection API vs. rulesets, Copilot review API |
| `data-model.md` | ⏳ | Protection rule entities, documentation sections |
| `quickstart.md` | ⏳ | Developer guide for the CI/CD workflow |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit.plan` — validates both spec AND plan together.

### Recommended Domains

Based on SPEC-004's scope (GitHub configuration, documentation, end-to-end verification):

#### 1. Requirements Checklist

Why this domain: SPEC-004 ties together all three prior specs into a complete pipeline. Missing a required status check name or misconfiguring the bot exemption would silently break the workflow.

```bash
/speckit.checklist requirements

Focus on Integration & Verification requirements:
- All seven user stories must have corresponding implementation tasks
- Branch protection must reference the exact CI job names from SPEC-002 (`detect`, `test`, `validate-pr-title`)
- GitHub Actions bot exemption must allow SPEC-003's marketplace sync push
- Verification checklist must cover all 10 steps from the master plan scope
- CLAUDE.md must document: branching strategy, PR requirements, release process, adding new plugins, user update path
- Recovery procedures must cover: re-run sync, revert bad release, force version
- Pay special attention to: ensuring required status check names exactly match the job names in pr-checks.yml
```

#### 2. Security Checklist

Why this domain: Branch protection is a security control. Misconfiguration could allow unauthorized pushes to main or weaken the CI gates that protect code quality.

```bash
/speckit.checklist security

Focus on Integration & Verification requirements:
- Branch protection must not allow direct pushes to main for human users
- The GitHub Actions bot exemption must be narrowly scoped (only the bot, not all apps)
- Squash-only merge enforcement prevents commit history manipulation
- Required status checks cannot be bypassed by repository admins (or document if admin bypass is intentional)
- Pay special attention to: ensuring the bot exemption doesn't create a security hole that could be exploited
```

#### 3. Error Handling Checklist

Why this domain: The verification checklist and recovery procedures must handle failure modes gracefully. If the pipeline breaks, the maintainer needs clear diagnostic steps.

```bash
/speckit.checklist error-handling

Focus on Integration & Verification requirements:
- Verification checklist must include expected outcomes AND failure diagnostics for each step
- Recovery procedures must handle: failed sync push (branch protection blocking bot), failed release-please (no conventional commits), stale marketplace.json
- Documentation must explain what to do if a required status check is renamed or removed
- Pay special attention to: ensuring recovery procedures are actionable (copy-pasteable `gh` commands) not just conceptual descriptions
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| requirements | | | |
| security | | | |
| error-handling | | | |
| **Total** | | | |

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/004-integration-verification/tasks.md`

### Tasks Prompt

```bash
/speckit.tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: branch protection config → Copilot setup → verification checklist → CLAUDE.md docs → recovery docs → final validation
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story

## Implementation Phases
1. Branch Protection (configure rules via gh API, verify enforcement)
2. Copilot Review (enable in repository settings, verify it appears on PRs)
3. Verification Checklist (create end-to-end walkthrough document)
4. Documentation (update CLAUDE.md with CI/CD workflow, recovery procedures)
5. Validation (run existing tests, verify branch protection works, verify docs accuracy)

## Constraints
- Configuration via `gh api` commands (scriptable, reproducible)
- Verification checklist at: docs/ai/specs/cicd-verification-checklist.md
- CLAUDE.md updates must integrate with existing structure
- AGENTS.md updates only if CI/CD conventions are needed for agent behavior
- No new test files — validation is manual verification + existing test suite
- Must not modify any SPEC-001, SPEC-002, or SPEC-003 artifacts
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
1. Constitution alignment — verify all 6 principles are respected (especially V. Conventional Commits, VI. KISS)
2. Coverage gaps — ensure all FRs and user stories have tasks
3. Verify branch protection configuration references correct CI job names from SPEC-002
4. Verify CLAUDE.md documentation accurately reflects SPEC-001, SPEC-002, SPEC-003 implementations
5. Verify recovery procedures reference correct release-please commands and conventions
6. Ensure no tasks modify existing SPEC-001/002/003 artifacts
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| | | | |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed (no coverage gaps).

### Implement Prompt

```bash
/speckit.implement

## Approach

For each task, follow this cycle:
1. Execute the configuration command or write the documentation
2. Verify the change took effect (e.g., `gh api` to read back protection rules)
3. Run existing tests to ensure nothing is broken: bash speckit-pro/tests/run-all.sh
4. Commit after each logical unit of work

### Pre-Implementation Setup

Before starting any task:
1. Verify you're on branch 004-integration-verification
2. Verify all existing tests pass: bash speckit-pro/tests/run-all.sh
3. Verify `gh` CLI is authenticated: gh auth status
4. Verify you have admin access to the repository (needed for branch protection)

### Implementation Notes
- Branch protection: Use `gh api` with JSON payloads for reproducibility
- Document the exact `gh api` commands used so they can be re-run if needed
- Copilot review: Check if configurable via API; if not, document the UI steps
- CLAUDE.md: Add a new "## CI/CD Workflow" section (or similar) — follow existing section patterns
- Verification checklist: Create as a standalone markdown file in docs/ai/specs/
- Recovery procedures: Include actual `gh` commands that can be copy-pasted
- Test the branch protection by attempting a direct push to main (should fail)
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Branch Protection | | | |
| 2 - Copilot Review | | | |
| 3 - Verification Checklist | | | |
| 4 - Documentation | | | |
| 5 - Validation | | | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in tasks.md
- [ ] Branch protection active on `main` with required status checks
- [ ] Copilot code review enabled
- [ ] GitHub Actions bot exempted from branch protection
- [ ] Squash-only merges enforced
- [ ] Verification checklist document created
- [ ] CLAUDE.md updated with CI/CD workflow documentation
- [ ] Recovery & rollback procedures documented
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
│       ├── pr-checks.yml              # From SPEC-002 (required status checks reference these jobs)
│       └── release.yml                # From SPEC-003 (marketplace sync needs bot exemption)
├── .claude-plugin/
│   └── marketplace.json               # Updated by sync script post-release
├── scripts/
│   └── sync-marketplace-versions.sh   # From SPEC-001
├── speckit-pro/
│   ├── .claude-plugin/
│   │   └── plugin.json                # Version source of truth
│   └── tests/
│       ├── lib/assertions.sh          # Shared test assertions
│       ├── layer4-scripts/            # Script unit tests
│       └── run-all.sh                 # Test orchestrator (Layers 1, 4, 5)
├── release-please-config.json         # From SPEC-001
├── .release-please-manifest.json      # From SPEC-001
├── CLAUDE.md                          # MODIFIED: add CI/CD workflow section
├── AGENTS.md                          # MODIFIED: add CI/CD conventions if needed
└── docs/ai/specs/
    ├── cicd-release-pipeline-technical-roadmap.md  # Master plan (status updated)
    ├── cicd-verification-checklist.md  # NEW: end-to-end verification steps
    ├── SPEC-001-workflow.md            # Completed
    ├── SPEC-002-workflow.md            # Completed
    ├── SPEC-003-workflow.md            # Completed
    └── SPEC-004-workflow.md            # This file
```

---

Template based on SpecKit best practices. Populated with SPEC-004 Integration & Verification context from the CI/CD Release Pipeline technical roadmap.
