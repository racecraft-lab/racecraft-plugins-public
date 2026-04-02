# SpecKit Workflow: SPEC-002 — PR Checks Workflow

**Template Version**: 1.0.0
**Created**: 2026-04-01
**Purpose**: Create a GitHub Actions workflow that validates every PR with scoped plugin tests and conventional commit PR title enforcement.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit.specify` | ✅ Complete | 12 FRs, 4 US, 14 scenarios, G1 passed |
| Clarify | `/speckit.clarify` | ✅ Complete | 10 questions resolved, 2 sessions, G2 passed |
| Plan | `/speckit.plan` | ✅ Complete | 5 artifacts, 7 research topics, G3 passed |
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
| **Spec ID** | SPEC-002 |
| **Name** | PR Checks Workflow |
| **Branch** | `002-pr-checks-workflow` |
| **Dependencies** | SPEC-001 (Repository Foundation) — ✅ Complete |
| **Enables** | SPEC-004 (Integration & Verification) |
| **Priority** | P1 |

### Success Criteria Summary

- [ ] `.github/workflows/pr-checks.yml` exists and is valid YAML
- [ ] `validate-plugins` job detects changed plugin directories via `git diff` and runs scoped tests
- [ ] `validate-plugins` job skips testing when no plugin directories changed (e.g., README-only PRs)
- [ ] `validate-pr-title` job validates PR title matches Conventional Commits pattern
- [ ] `validate-pr-title` job provides clear error message with example format on failure
- [ ] Both jobs run in parallel (no inter-job dependencies)
- [ ] Workflow triggers on `pull_request` events: `opened`, `reopened`, `synchronize`
- [ ] All existing tests continue to pass (`bash tests/run-all.sh`)

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/002-pr-checks-workflow/spec.md`

### Specify Prompt

```bash
/speckit.specify

## Feature: PR Checks Workflow

### Problem Statement
The racecraft-plugins-public marketplace repo has no CI validation on pull requests. PRs can be merged without running the test suite or verifying conventional commit formatting. This means broken plugins can reach main, and non-conventional commit messages can break the release-please automation (SPEC-003). As the marketplace grows from 1 to 2-4 plugins, manual PR review alone will not catch test regressions across all plugins.

### Users
- Solo maintainer (Fredrick) who needs automated quality gates on PRs
- Future contributors who need clear feedback on PR requirements
- release-please automation (SPEC-003) which depends on conventional commit titles

### User Stories
1. As a maintainer, I need a CI job that detects which plugins changed in a PR and runs only their test suites (Layers 1, 4, 5), so I get fast feedback without testing unchanged plugins.
2. As a maintainer, I need a CI job that validates the PR title matches the Conventional Commits pattern (`type(scope): description`), so that release-please can correctly parse squash-merged commits on main.
3. As a contributor, I need clear error messages when my PR title doesn't match the expected format, including an example of the correct format.
4. As a maintainer, I need the workflow to skip testing entirely when no plugin directories changed (e.g., docs-only PRs), so CI doesn't waste time on irrelevant runs.

### Constraints
- Workflow file: `.github/workflows/pr-checks.yml`
- Runner: `ubuntu-latest` with `bash` shell
- Plugin detection: use `git diff --name-only` against the base branch to identify changed top-level plugin directories
- Test runner: `bash tests/run-all.sh` within each changed plugin directory (runs Layers 1, 4, 5 by default)
- PR title regex: `^(feat|fix|chore|docs|refactor|test)(\(.+\))?!?: .+$`
- Both jobs must be independent (no `needs:` dependencies) to run in parallel
- Trigger events: `pull_request` with types `[opened, reopened, synchronize]`
- Must follow GitHub Actions best practices (pinned action versions, minimal permissions)

### Out of Scope
- Layers 2/3 AI evals (local only, per design decision)
- Copilot code review configuration (handled by SPEC-004 — it's a GitHub repo setting, not a workflow)
- Release automation (handled by SPEC-003)
- Branch protection rules (handled by SPEC-004)
- Testing against multiple OS versions (solo maintainer, ubuntu-latest is sufficient)

### Key Technical Decisions (Already Made)
- Test Scoping: Only run tests for changed plugins, not all plugins. This keeps CI fast as the marketplace grows.
- PR Title Validation: Validate PR title format but NOT scope against actual plugin directories. A typo like `feat(spekit-pro):` passes validation but release-please ignores it — accepted risk for solo maintainer.
- No matrix builds: Single ubuntu-latest runner is sufficient for bash scripts and shell tests.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | FR-001 through FR-012 |
| User Stories | 4 (2x P1, 2x P2) |
| Acceptance Criteria | 14 scenarios, 5 edge cases, 6 success criteria |

### Files Generated

- [x] `specs/002-pr-checks-workflow/spec.md`

---

## Phase 2: Clarify (Optional but Recommended)

**When to run:** When spec has areas that could be interpreted multiple ways.

### Clarify Prompts

#### Session 1: Plugin Detection Logic

```bash
/speckit.clarify Focus on plugin detection: How should the workflow detect which top-level directories are plugins vs. non-plugin directories like `docs/`, `scripts/`, `.specify/`? Should it rely on the presence of `.claude-plugin/plugin.json` or `tests/run-all.sh`? What if a plugin exists but has no test suite? How does `git diff --name-only` work with squash merges vs. regular merges?
```

#### Session 2: PR Title Validation Edge Cases

```bash
/speckit.clarify Focus on PR title validation: Should the regex allow breaking change indicator (`!`)? Should scope be optional or required? How should multi-line PR titles be handled (only first line matters)? Should the validation run on draft PRs? What about Dependabot or other bot PRs that may not follow conventional commits?
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1       | Plugin Detection Logic | 5 | plugin.json as sole signal, fetch-depth 0, three-dot diff, dynamic matrix, empty matrix handling |
| 2       | PR Title Validation Edge Cases | 5 | skip drafts, no bot exemptions, ! placement confirmed, multi-line not a concern, ci type out of scope |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/002-pr-checks-workflow/plan.md`

### Plan Prompt

```bash
/speckit.plan

## Tech Stack
- Language: YAML (GitHub Actions workflow) + Bash (inline scripts)
- CI Platform: GitHub Actions
- Runner: ubuntu-latest
- Shell: bash
- Testing: Shell-based test suite with shared assertions library (`tests/lib/assertions.sh`)
- JSON processing: jq (if needed for output parsing)

## Constraints
- Workflow must be a single `.github/workflows/pr-checks.yml` file
- Two independent jobs: `validate-plugins` and `validate-pr-title`
- Plugin detection via `git diff --name-only ${{ github.event.pull_request.base.sha }}...${{ github.sha }}`
- Must handle the case where `tests/run-all.sh` exists in a changed plugin but fails (job should fail, not silently continue)
- PR title validation uses bash regex matching, not an external action (KISS principle)
- All scripts follow Constitution Principle II: set -euo pipefail

## Architecture Notes
- validate-plugins job: checkout → detect changed dirs → filter to plugin dirs (those with tests/run-all.sh) → run tests for each → aggregate results
- validate-pr-title job: read PR title from github context → regex match → pass/fail with clear message
- No job dependencies — both run in parallel
- Workflow permissions should be minimal (contents: read for checkout)

## Existing Infrastructure
- speckit-pro/tests/run-all.sh exists and runs Layers 1, 4, 5 by default (369 tests passing)
- .claude-plugin/marketplace.json lists registered plugins
- SPEC-001 established release-please config and sync script
- Convention: all scripts use #!/usr/bin/env bash + set -euo pipefail

## Prior Art
- SPEC-001 workflow file: docs/ai/specs/SPEC-001-workflow.md (completed workflow for reference)
- Design spec: docs/ai/specs/cicd-release-pipeline-plan.md (master plan with SPEC-002 scope)
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ | Workflow structure, 3 jobs, execution flow |
| `research.md` | ✅ | 7 research topics resolved |
| `data-model.md` | ✅ | 3 job entities, event payload structure |
| `quickstart.md` | ✅ | Developer guide for PR workflow |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit.plan` — validates both spec AND plan together.

### Recommended Domains

Based on SPEC-002's scope (GitHub Actions workflow, bash scripts, CI validation):

#### 1. Script Safety Checklist

Why this domain: The workflow contains inline bash scripts for plugin detection and PR title validation. Script safety is a constitution principle and inline CI scripts are a common source of subtle bugs (unquoted variables, missing error handling).

```bash
/speckit.checklist script-safety

Focus on PR Checks Workflow requirements:
- Inline bash scripts in GitHub Actions must use `set -euo pipefail` via `shell: bash` default
- Plugin detection via git diff must handle filenames with spaces or special characters
- PR title regex must not be vulnerable to ReDoS
- Exit codes must propagate correctly through the workflow
- Pay special attention to: proper quoting of shell variables in GitHub Actions context expressions
```

#### 2. Error Handling Checklist

Why this domain: CI workflows must provide clear, actionable feedback when they fail. Silent failures or cryptic error messages waste maintainer time.

```bash
/speckit.checklist error-handling

Focus on PR Checks Workflow requirements:
- validate-plugins must clearly report which plugin's tests failed
- validate-pr-title must show the expected format when the title doesn't match
- Git diff failures (e.g., missing base SHA) must be caught and reported
- The workflow must handle the case where no plugins changed (skip gracefully, not error)
- Pay special attention to: ensuring CI failure messages are actionable for the PR author
```

#### 3. Requirements Checklist

Why this domain: The workflow must correctly implement the scoped testing and title validation requirements without gaps.

```bash
/speckit.checklist requirements

Focus on PR Checks Workflow requirements:
- All four user stories must have corresponding workflow logic
- The `synchronize` event type must be included (not just `opened` and `reopened`)
- Plugin detection must correctly identify top-level plugin directories
- PR title regex must match all valid conventional commit types (feat, fix, chore, docs, refactor, test)
- Pay special attention to: edge cases like empty diffs, force-pushed PRs, and draft PRs
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| script-safety | | | |
| error-handling | | | |
| requirements | | | |
| **Total** | | | |

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/002-pr-checks-workflow/tasks.md`

### Tasks Prompt

```bash
/speckit.tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: workflow skeleton → plugin detection → title validation → testing → documentation
- Mark parallel-safe tasks explicitly with [P]
- Organize by job (validate-plugins, validate-pr-title)

## Implementation Phases
1. Foundation (workflow file skeleton with triggers and permissions)
2. validate-plugins job (checkout, plugin detection, scoped test execution)
3. validate-pr-title job (title extraction, regex validation, error messages)
4. Validation (manual testing with a real PR, existing tests still pass)

## Constraints
- Single workflow file: `.github/workflows/pr-checks.yml`
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
1. Constitution alignment — verify all 6 principles are respected (especially II. Script Safety, V. Conventional Commits, VI. KISS)
2. Coverage gaps — ensure all FRs and user stories have tasks
3. Consistency between task file paths and actual project structure
4. Verify the PR title regex matches the design spec exactly
5. Verify plugin detection logic handles edge cases (no changes, docs-only changes, new plugin added)
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
1. Verify you're on branch 002-pr-checks-workflow
2. Verify all existing tests pass: bash speckit-pro/tests/run-all.sh
3. Create .github/workflows/ directory if it doesn't exist

### Implementation Notes
- GitHub Actions YAML: use 2-space indentation consistently
- Pin action versions to full SHA for security (e.g., actions/checkout@v4)
- Use `${{ github.event.pull_request.title }}` for PR title access
- Use `${{ github.event.pull_request.base.sha }}` for diff base
- Inline bash scripts should be readable — use comments for non-obvious logic
- Test the workflow by opening a real PR after implementation
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Workflow Skeleton | | | |
| 2 - validate-plugins | | | |
| 3 - validate-pr-title | | | |
| 4 - Validation | | | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in tasks.md
- [ ] `.github/workflows/pr-checks.yml` is valid YAML
- [ ] Inline bash scripts pass `bash -n` syntax check
- [ ] validate-plugins job correctly detects changed plugins
- [ ] validate-plugins job skips when no plugins changed
- [ ] validate-pr-title job validates conventional commit format
- [ ] validate-pr-title job shows clear error with example on failure
- [ ] Both jobs run independently in parallel
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
│       └── pr-checks.yml              # NEW: PR validation workflow
├── .claude-plugin/
│   └── marketplace.json               # Registry (unchanged)
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
└── docs/ai/specs/
    ├── cicd-release-pipeline-plan.md  # Master plan
    ├── SPEC-001-workflow.md           # Completed
    └── SPEC-002-workflow.md           # This file
```

---

Template based on SpecKit best practices. Populated with SPEC-002 PR Checks Workflow context from the CI/CD Release Pipeline master plan.
