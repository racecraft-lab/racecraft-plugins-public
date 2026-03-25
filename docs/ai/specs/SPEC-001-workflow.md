# SpecKit Workflow: SPEC-001 — Repository Foundation

**Template Version**: 1.0.0
**Created**: 2026-03-24
**Purpose**: Set up release-please configuration, version sync script, and fix version duplication so automated versioning infrastructure is ready for CI workflows.

---

## Workflow Overview

| Phase | Command | Status | Notes |
| ------- | --------- | -------- | ------- |
| Specify | `/speckit.specify` | ✅ Complete | 12 FRs, 4 US, 13 scenarios, G1 passed |
| Clarify | `/speckit.clarify` | ✅ Complete | 10 questions resolved, 3/3 consensus on path resolution, G2 passed |
| Plan | `/speckit.plan` | ✅ Complete | 4 artifacts, 7 research topics, G3 passed |
| Checklist | `/speckit.checklist` | ✅ Complete | 3 domains, 107 items, 41 gaps remediated, G4 passed |
| Tasks | `/speckit.tasks` | ✅ Complete | 26 tasks, 4 phases, 14 parallel, G5 passed |
| Analyze | `/speckit.analyze` | ✅ Complete | 8 findings (0C/1H/5M/2L), all remediated, G6 passed |
| Implement | `/speckit.implement` | ⏳ Pending | |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates (SpecKit Best Practice)

Each phase requires **human review and approval** before proceeding:

| Gate | Checkpoint | Approval Criteria |
| ------ | ------------ | ------------------- |
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
| ----------- | ------------- | -------------- |
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
| ------- | ------- |
| **Spec ID** | SPEC-001 |
| **Name** | Repository Foundation |
| **Branch** | `001-repository-foundation` |
| **Dependencies** | None |
| **Enables** | SPEC-002 (PR Checks), SPEC-003 (Release Automation), SPEC-004 (Integration) |
| **Priority** | P1 |

### Success Criteria Summary

- [ ] `release-please-config.json` exists with correct GenericJson updater format for speckit-pro
- [ ] `.release-please-manifest.json` exists tracking `speckit-pro: "1.0.0"`
- [ ] `scripts/sync-marketplace-versions.sh` reads plugin.json versions and updates marketplace.json
- [ ] Sync script handles missing plugin.json gracefully (skip with warning)
- [ ] Sync script is idempotent (running twice produces same result)
- [ ] Layer 4 unit tests exist and pass for the sync script
- [ ] Version duplication is resolved (plugin.json is source of truth)
- [ ] All existing tests continue to pass (`bash tests/run-all.sh`)

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/001-repository-foundation/spec.md`

### Specify Prompt

```bash
/speckit.specify

## Feature: Repository Foundation for CI/CD Pipeline

### Problem Statement
The racecraft-plugins-public marketplace repo has no automated versioning infrastructure. Versions are hardcoded in both plugin.json and marketplace.json, which Anthropic warns against — plugin.json always wins silently, making the marketplace version misleading. As the marketplace grows from 1 to 2-4 plugins, manual version management will not scale for a solo maintainer.

### Users
- Solo maintainer (Fredrick) who needs automated version management
- Future plugin consumers who need accurate version information in marketplace.json

### User Stories
1. As a maintainer, I need release-please configuration files so that conventional commits on main automatically trigger version bumps and changelog generation for each plugin independently.
2. As a maintainer, I need a sync script that reads each plugin's plugin.json version and updates the matching entry in marketplace.json, so version information stays consistent without manual intervention.
3. As a maintainer, I need the version duplication problem fixed so that plugin.json is the unambiguous source of truth, aligned with Anthropic's documented behavior.
4. As a maintainer, I need Layer 4 unit tests for the sync script so that regressions are caught before merge.

### Constraints
- release-please-config.json must use `release-type: "simple"` (not a standard language package)
- extra-files must use GenericJson updater format: `{"type": "json", "path": ".claude-plugin/plugin.json", "jsonpath": "$.version"}`
- extra-files paths are relative to the package directory (speckit-pro/)
- bump-minor-pre-major: true (protect pre-1.0 plugins from premature major bumps)
- Sync script must follow existing conventions: #!/usr/bin/env bash, set -euo pipefail
- Sync script must use jq for JSON manipulation (not sed/awk hacks per constitution Principle VI)
- Tests must use shared assertions library at tests/lib/assertions.sh
- Tests must follow naming convention: test-<script-name>.sh

### Out of Scope
- GitHub Actions workflows (SPEC-002, SPEC-003)
- Branch protection configuration (SPEC-004)
- Changelog generation (automatic via release-please in SPEC-003)
- npm or registry publishing (plugins are git-based)

### Key Technical Decisions (Already Made)
- Version Source of Truth: plugin.json (per Anthropic docs)
- Release Type: "simple" (not node/python/java)
- Marketplace sync: post-release script, not part of Release PR
```

### Specify Results

| Metric | Value |
| -------- | ------- |
| Functional Requirements | |
| User Stories | |
| Acceptance Criteria | |

### Files Generated

- [ ] `specs/001-repository-foundation/spec.md`

---

## Phase 2: Clarify (Optional but Recommended)

**When to run:** When spec has areas that could be interpreted multiple ways.

### Clarify Prompts

#### Session 1: Sync Script Behavior

```bash
/speckit.clarify Focus on sync script behavior: How should the script discover plugins? Should it scan for all plugin.json files or use a hardcoded list? What happens when marketplace.json has a plugin entry but no corresponding plugin.json exists? What about new plugins not yet in marketplace.json?
```

#### Session 2: Release-Please Configuration

```bash
/speckit.clarify Focus on release-please configuration: Is the extra-files jsonpath format correct for nested package directories? Does bump-minor-pre-major apply globally or per-package? How does release-please handle the initial run when no prior releases exist?
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1       |            |           |              |
| 2       |            |           |              |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/001-repository-foundation/plan.md`

### Plan Prompt

```bash
/speckit.plan

## Tech Stack
- Language: Bash (shell scripts)
- JSON processing: jq
- Testing: Shell-based test suite with shared assertions library
- Package format: Claude Code plugin (plugin.json manifest)
- Version management: release-please (Google)

## Constraints
- All scripts must start with #!/usr/bin/env bash and set -euo pipefail (Constitution Principle II)
- All scripts must be chmod +x (Constitution Principle II)
- JSON manipulation must use jq, not sed/awk (Constitution Principle VI — KISS)
- Tests must use tests/lib/assertions.sh shared library (Constitution Principle IV)
- Test naming: test-<script-name>.sh (Constitution Principle IV)
- plugin.json is version source of truth (Anthropic docs, Constitution Principle III)

## Architecture Notes
- release-please-config.json at repo root configures per-plugin release behavior
- .release-please-manifest.json at repo root tracks current versions
- scripts/sync-marketplace-versions.sh is a standalone script called by CI (SPEC-003) but testable independently
- Layer 4 tests go in speckit-pro/tests/layer4-scripts/ following existing patterns
- The sync script must be robust: handle missing files, multiple plugins, idempotent execution

## Existing Infrastructure
- speckit-pro/.claude-plugin/plugin.json exists with version "1.0.0"
- .claude-plugin/marketplace.json exists with plugin entries including version fields
- speckit-pro/tests/ has existing Layer 4 tests as reference patterns
- tests/lib/assertions.sh provides assert_equals, assert_contains, assert_file_exists, etc.

## Design Spec Reference
- docs/superpowers/specs/2026-03-24-cicd-versioning-release-pipeline-design.md
```

### Plan Results

| Artifact | Status | Notes |
| ---------- | -------- | ------- |
| `plan.md` | ⏳ | Technical context, execution flow |
| `research.md` | ⏳ | Decision rationales (if needed) |
| `data-model.md` | ⏳ | File format specifications |
| `quickstart.md` | ⏳ | Developer onboarding |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit.plan` — validates both spec AND plan together.

### Recommended Domains

Based on SPEC-001's scope (config files, bash scripts, JSON processing, version management):

#### 1. Script Safety Checklist

Why this domain: SPEC-001 creates a new bash script (sync-marketplace-versions.sh) that manipulates JSON files. Script safety is a constitution principle and the highest-risk area.

```bash
/speckit.checklist script-safety

Focus on Repository Foundation requirements:
- sync-marketplace-versions.sh must handle missing plugin.json files gracefully
- All variables must be quoted, all command results checked
- jq filters must handle malformed JSON without silent failures
- Script must be idempotent (safe to run multiple times)
- Pay special attention to: error handling when marketplace.json or plugin.json is missing or malformed
```

#### 2. Data Integrity Checklist

Why this domain: The sync script modifies marketplace.json based on plugin.json values. Data integrity between these two files is critical for users to get correct version information.

```bash
/speckit.checklist data-integrity

Focus on Repository Foundation requirements:
- Version strings must be valid semver in both plugin.json and marketplace.json
- Sync script must not corrupt marketplace.json structure (preserve all non-version fields)
- release-please-config.json jsonpath must correctly target the version field
- .release-please-manifest.json must accurately reflect current plugin versions
- Pay special attention to: race conditions or partial writes that could leave marketplace.json in an invalid state
```

#### 3. Error Handling Checklist

Why this domain: The sync script will run in CI (SPEC-003) where failures need clear diagnostics. Silent failures would leave marketplace.json out of sync without anyone knowing.

```bash
/speckit.checklist error-handling

Focus on Repository Foundation requirements:
- Sync script must exit with non-zero status on any failure
- Error messages must identify which plugin/file caused the failure
- Missing jq dependency must be detected early with a clear message
- Partial sync failures (some plugins updated, others not) must be handled
- Pay special attention to: ensuring CI will detect and report sync failures rather than silently succeeding
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
| ----------- | ------- | ------ | ----------------- |
| script-safety | | | |
| data-integrity | | | |
| error-handling | | | |
| **Total** | | | |

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/001-repository-foundation/tasks.md`

### Tasks Prompt

```bash
/speckit.tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: config files → sync script → tests → validation
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story

## Implementation Phases
1. Foundation (release-please config files)
2. Sync Script (scripts/sync-marketplace-versions.sh)
3. Tests (Layer 4 unit tests for sync script)
4. Validation (end-to-end verification, existing tests still pass)

## Constraints
- Config files at repo root: release-please-config.json, .release-please-manifest.json
- Script at: scripts/sync-marketplace-versions.sh
- Tests at: speckit-pro/tests/layer4-scripts/test-sync-marketplace-versions.sh
- Must follow existing test patterns in speckit-pro/tests/layer4-scripts/
```

### Tasks Results

| Metric | Value |
| -------- | ------- |
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
1. Constitution alignment — verify all 6 principles are respected (especially II. Script Safety, III. Semver, IV. Test Coverage, VI. KISS)
2. Coverage gaps — ensure all FRs and user stories have tasks
3. Consistency between task file paths and actual project structure
4. Verify release-please-config.json format matches the design spec exactly (GenericJson updater format)
5. Verify sync script test coverage includes edge cases (missing files, malformed JSON, multi-plugin)
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
1. Write the file/script per the task description
2. Verify script syntax with bash -n (Constitution Principle II)
3. Ensure chmod +x on all scripts
4. Run relevant tests after each task
5. Verify existing tests still pass: bash speckit-pro/tests/run-all.sh

### Pre-Implementation Setup

Before starting any task:
1. Verify you're on branch 001-repository-foundation
2. Verify all existing tests pass: bash speckit-pro/tests/run-all.sh
3. Verify jq is installed: which jq

### Implementation Notes
- release-please-config.json: Use exact format from design spec (GenericJson updater)
- .release-please-manifest.json: Simple JSON object mapping package names to current versions
- sync-marketplace-versions.sh: Use jq for all JSON operations, no sed/awk
- Tests: Follow patterns in existing Layer 4 tests, use assertions.sh library
- All file paths in config are relative to package directory (speckit-pro/)
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
| ------- | ------- | ----------- | ------- |
| 1 - Config Files | | | |
| 2 - Sync Script | | | |
| 3 - Unit Tests | | | |
| 4 - Validation | | | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in tasks.md
- [ ] Script passes bash -n syntax check
- [ ] Script is executable (chmod +x)
- [ ] All variables quoted, all command results checked
- [ ] Layer 4 tests pass for sync script
- [ ] All existing tests pass: `bash speckit-pro/tests/run-all.sh`
- [ ] release-please-config.json validated against design spec format
- [ ] .release-please-manifest.json has correct initial versions
- [ ] PR created with conventional commit title: `feat(speckit-pro): add release-please config and marketplace sync script`
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
├── .claude-plugin/
│   └── marketplace.json          # Registry — version managed by sync script
├── scripts/
│   └── sync-marketplace-versions.sh  # NEW: reads plugin.json → updates marketplace.json
├── speckit-pro/
│   ├── .claude-plugin/
│   │   └── plugin.json           # Version source of truth (managed by release-please)
│   └── tests/
│       ├── lib/assertions.sh     # Shared test assertions
│       ├── layer4-scripts/       # Script unit tests
│       │   └── test-sync-marketplace-versions.sh  # NEW
│       └── run-all.sh            # Test orchestrator
├── release-please-config.json    # NEW: per-plugin release configuration
├── .release-please-manifest.json # NEW: current version tracker
└── docs/ai/specs/
    └── cicd-release-pipeline-plan.md  # Master plan
```

---

Template based on SpecKit best practices. Populated with SPEC-001 Repository Foundation context from the CI/CD Release Pipeline master plan.
