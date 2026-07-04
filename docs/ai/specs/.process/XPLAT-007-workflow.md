# SpecKit Workflow: XPLAT-007 - Python Tooling and Release-Gate Migration

**Template Version**: 1.0.0
**Created**: 2026-07-04
**Purpose**: Prepare XPLAT-007 for autonomous execution from the cross-platform plugin runtime roadmap and the setup Grill Me decisions.

---

## How to Use This Workflow

Run this workflow from the XPLAT-007 worktree:

```text
$speckit-autopilot docs/ai/specs/.process/XPLAT-007-workflow.md
```

This file is already populated for XPLAT-007. Do not replace it with the
generic workflow template.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`$speckit-scaffold-spec XPLAT-007`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/XPLAT-007-design-concept.md
```

Re-read it before each phase. The design concept is the source of truth for the
accepted scope:

- One XPLAT-007 workflow with three internal implementation slices.
- Test/eval runner gates first, then payload/install/release helpers, then
  active-path guardrails and cleanup.
- Runner module commands are the primary Python command surface where
  practical.
- Golden fixtures plus source-checkout Bash-reference comparison are required
  until a gate is promoted as Python-authoritative.
- Target zero active repo-local shell scripts or shell-specific command paths.
- Rebuild test payloads as evidence only; release payload cutover remains
  XPLAT-008.
- Active Claude/Codex invocation cutover, public docs, release notes, and native
  installed-plugin UAT remain XPLAT-008.

> Grill Me is human-in-the-loop only. It is not part of the autopilot loop.
> Once this workflow begins, clarifications happen via `$speckit-clarify` and
> consensus, never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|---|---|---|---|
| Specify | `$speckit-specify` | Complete | Created `spec.md` and requirements checklist for active repo-local Python tooling and release-gate migration |
| Clarify | `$speckit-clarify` | In Progress | Resolve gate inventory, command taxonomy, no-shell guard scope, payload boundary, docs boundary, and platform proof |
| Plan | `$speckit-plan` | Pending | Produce technical plan, research, data model, contracts, and quickstart for the three-slice migration |
| Checklist | `$speckit-checklist` | Pending | Recommended domains: integration, reliability, security, and release-readiness |
| Tasks | `$speckit-tasks` | Pending | Generate tasks ordered by test/eval gates, payload/release helpers, then active-path guardrails |
| Analyze | `$speckit-analyze` | Pending | Check drift across roadmap, PRD AC-7.*, design concept, spec, plan, and tasks |
| Confidence Gate | G6.5 | Pending | Resolve confidence mode and record pass/advisory disposition before implementation |
| Implement | `$speckit-implement` | Pending | Execute Python gate migration with fixture parity, promotion records, and no-shell guard evidence |
| Post | Autopilot post-implementation items | Pending | Complete doctor, verification, review, PR packet, PR creation, remediation, and retrospective items |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|---|---|---|
| G1 | After Specify | Scope is active repo-local Python tooling and release-gate migration only; no active Claude/Codex cutover, public support claim, release payload cutover, or native installed-plugin UAT |
| G2 | After Clarify | Gate inventory, command taxonomy, Bash comparison retirement, no-shell guard definition, test payload boundary, active-doc boundary, and platform proof are unambiguous |
| G3 | After Plan | Plan records the reviewability warning, three-slice strategy, runner command surface, parity/promotion model, no-shell guard, and XPLAT-008 handoff |
| G4 | After Checklist | All true integration, reliability, security, and release-readiness gaps are remediated or explicitly out of scope |
| G5 | After Tasks | Tasks map to the accepted three slices and avoid active Claude/Codex cutover or broad public documentation scope |
| G6 | After Analyze | No critical drift remains between roadmap, PRD AC-7.*, design concept, spec, plan, tasks, XPLAT-005 read-only gates, and XPLAT-006 mutation-helper contracts |
| G6.5 | After Analyze Consensus | Confidence gate records pass, advisory no-data, or advisory fail disposition before implementation begins |
| G7 | After Implementation | Python test/eval/payload/release gates, parity fixtures, test payload evidence, no-shell active-path guard, spec-index check, diff hygiene, and relevant repo gates pass |

---

## Prerequisites

### Worktree and Branch

- Worktree: `.worktrees/xplat-007-python-tooling-and-release-gate-migration`
- Branch: `codex/xplat-007-python-tooling-and-release-gate-migration`
- Contract marker: `specs/xplat-007-python-tooling-and-release-gate-migration/SPEC-MOC.md`
- Design concept: `docs/ai/specs/.process/XPLAT-007-design-concept.md`
- Workflow: `docs/ai/specs/.process/XPLAT-007-workflow.md`

Expected branch is `codex/xplat-007-python-tooling-and-release-gate-migration`.
Preset resolution should use `.specify/presets/speckit-pro-reviewability/`
unless a deliberate higher-priority override exists.

### Grounded Source Truth

- Roadmap: `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
- Roadmap MOC: `docs/ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md`
- Product requirement: `docs/prd-cross-platform-plugin-runtime.md`
- Runtime inventory: `docs/ai/research/cross-platform-runtime-inventory.md`
- XPLAT-004 runner package: `speckit-pro/speckit_pro_runner/`
- XPLAT-005 read-only helper registry and fixtures:
  `speckit-pro/speckit_pro_runner/helpers/`,
  `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/`
- XPLAT-006 mutation-helper contracts and fixtures:
  `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/`,
  `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/contracts/`
- Current active test/eval gates: `tests/speckit-pro/**`
- Current payload/release helpers: `scripts/build-plugin-payloads.sh`,
  `scripts/refresh-local-plugin.sh`, and
  `scripts/sync-marketplace-versions.sh`
- Current helper script surfaces: `speckit-pro/skills/**/scripts/**`,
  `speckit-pro/codex-skills/**/scripts/**`, and `speckit-pro/scripts/**`
- Current CI dispatch context: `.github/workflows/**`
- Project constitution: `.specify/memory/constitution.md`
- Design concept source: `docs/ai/specs/.process/XPLAT-007-design-concept.md`

### Phase 0 Preflight Results

| Check | Result | Evidence |
|---|---|---|
| Codex agent install | Pass | `validate-agent-install.sh --surface codex --autoheal` reported `ok: codex: 10 bundled agents installed` |
| SpecKit CLI | Pass | `command -v specify` resolved to an installed `specify` executable |
| Remote | Pass | `git remote -v` detected `origin` |
| Branch/worktree | Pass | Created worktree on `codex/xplat-007-python-tooling-and-release-gate-migration` from `origin/main` at `038f7751` |
| Reviewability setup gate | Warn/pass | `reviewability-gate.sh setup docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md` returned `status: warn`, `pass: true`, `reviewable_loc: 250`, `production_files: 4`, `total_files: 10`, warning: primary surfaces `docs/process` and `harness/adapter` exceed one-surface warning threshold |
| Grill Me | Complete | 10 picker questions; accepted one workflow with three slices, test/eval gates first, runner module commands, Python plus Bash comparison, no active shell command paths, full repo-local release gates, test payload rebuilds only, source-checkout platform proof, active Bash reference deletion, and active-code-only historical boundary |
| Preset resolution | Pass | `specify preset resolve spec-template`, `plan-template`, and `tasks-template` resolve to `speckit-pro-reviewability v1.0.0` |

### Constitution Validation

| Principle | XPLAT-007 Requirement | Verification |
|---|---|---|
| Plugin Structure Compliance | New command surfaces stay inside the `speckit-pro/` plugin and preserve manifest/payload structure | Layer 1 structural validation and manifest review |
| Script Safety | Migrated active gates use Python 3.11+ standard-library commands and remove active Bash command paths; any remaining CI mechanics must contain no validation logic | No-shell guard, Python tests, and code review |
| Semantic Versioning | Do not edit plugin versions manually | Diff review |
| Test Coverage Before Merge | Add Python tests, fixtures, and promotion evidence before replacing active gates | Focused Python gates, Layer 1, Layer 4, and deterministic suite before PR |
| Conventional Commits | Setup and implementation commits use conventional commit format | Commit and PR title review |
| KISS, Simplicity & YAGNI | Prefer explicit runner operations and small Python modules over broad frameworks; justify any standalone command outside runner registry | Plan complexity table and G6 analysis |

---

## Specification Context

### Basic Information

| Field | Value |
|---|---|
| Spec ID | XPLAT-007 |
| Name | Python Tooling and Release-Gate Migration |
| Branch | `codex/xplat-007-python-tooling-and-release-gate-migration` |
| Feature directory | `specs/xplat-007-python-tooling-and-release-gate-migration` |
| Dependencies | XPLAT-006 complete/archived; Python runner helper contracts, fixture tree, install inventory, and deferred-live-mutation boundaries exist |
| Enables | XPLAT-008 Claude/Codex cutover and universal install release gate |
| Priority | P1 |

### Success Criteria Summary

- [ ] Active plugin build, test, eval, payload, install-verification,
  repository-helper, and release-readiness commands have Python 3.11+
  standard-library entrypoints.
- [ ] Python runner module commands are the primary migrated command surface
  where practical, with any standalone Python command justified in the plan.
- [ ] Active tests, evals, payload builders, release checks, install
  verification, and repo helper tooling no longer require Bash, `.sh`, `jq`,
  Git Bash, WSL, PowerShell helper scripts, shell interpolation, or shell-only
  parsing.
- [ ] Bash parity fixtures from XPLAT-005/XPLAT-006 are removed from active
  release gates or preserved only as inactive historical/parity evidence.
- [ ] Deterministic guards fail when active repo-local command paths reintroduce
  shell-specific dependencies.
- [ ] Test payload rebuild evidence exists without release payload cutover.
- [ ] XPLAT-008 receives a clear handoff for active Claude/Codex cutover,
  installed-cache UAT, public docs, release notes, update, autoheal, and public
  release readiness.

### Accepted Three-Slice Plan

| Slice | Scope | Explicit Boundary |
|---|---|---|
| Slice 1 | Top-level test runner, Layer 1 structural checks, Layer 4 helper tests, AI-eval runners, tool-scoping, integration, and parity suites | No payload/release helper replacement until Python test/eval gates can validate later work |
| Slice 2 | Payload builders, local plugin refresh, marketplace/version sync, install verification, release checks, release-readiness checks, and test payload rebuild evidence | No generated release payload cutover, active Claude/Codex payload selection, public docs, or native installed-plugin UAT |
| Slice 3 | Active-path no-shell/no-jq guard, active Bash command-path cleanup, CI mechanics review, promotion records, and XPLAT-008 handoff | Do not rewrite archive/provenance history solely for wording; do not create thin Bash transition wrappers |

---

## Phase 1: Specify

**When to run:** At the start of XPLAT-007. Focus on what active repo-local
tooling and release gates must migrate, what parity evidence is required, and
what cutover is deliberately deferred. Output:
`specs/xplat-007-python-tooling-and-release-gate-migration/spec.md`.

### Specify Prompt

```text
$speckit-specify

## Feature: Python Tooling and Release-Gate Migration

### Problem Statement
SpecKit Pro now has a Python runner foundation, read-only helper ports, and
mutation-helper contracts, but active repo-local tests, evals, payload builders,
install-verification scripts, release checks, release-readiness gates, and
helper tooling still include Bash-backed command paths. XPLAT-007 must replace
those active gates with Python 3.11+ standard-library commands before XPLAT-008
can switch Claude/Codex surfaces or make public cross-platform claims.

### Users
- Maintainers who need to run the active verification and release-readiness
  suite without Bash, `jq`, Git Bash, WSL, or PowerShell helper scripts.
- XPLAT-008 implementers who need Python-authoritative gates before active
  Claude/Codex invocation cutover and native installed-plugin UAT.
- Reviewers who need fixture parity, promotion records, and test payload
  evidence before Bash references leave active gates.

### User Stories
1. As a maintainer, I can run the repo-local test/eval suite through Python
   standard-library commands and get equivalent pass/fail behavior to the
   current active Bash gates.
2. As a release maintainer, I can build test payloads, refresh local plugin
   fixtures, check marketplace/version sync, verify installs, and run
   release-readiness checks through Python commands without relying on Bash or
   `jq`.
3. As a reviewer, I can inspect a deterministic active-path guard that fails if
   active build, test, eval, payload, install-verification, repo-helper, or
   release-readiness gates still use Bash, `.sh`, `jq`, shell interpolation, or
   shell-only parsing.

### Constraints
- Follow the design concept decisions in
  `docs/ai/specs/.process/XPLAT-007-design-concept.md`.
- Use Python 3.11+ standard library only for promoted repo-local gates.
- Prefer `python -m speckit_pro_runner` operations where practical; justify any
  standalone Python command in the plan.
- Use golden fixtures plus source-checkout Bash-reference comparisons until
  each migrated gate is promoted as Python-authoritative.
- Target zero active repo-local shell scripts or shell-specific command paths.
- Rebuild test payloads only; release payload cutover is out of scope.
- Keep platform proof to source-checkout fixtures, Windows-style path fixtures,
  and local macOS smoke.
- Preserve archive/provenance history unless it is part of an active gate.

### Out of Scope
- Active Claude Code or Codex skill, agent, hook, install-guidance, generated
  release payload, public docs, release notes, update, autoheal, or public
  platform support cutover.
- Native Windows/macOS/Linux installed-plugin UAT.
- Changing GitHub Spec Kit's generated `.specify/scripts/bash/` helpers in
  consumer repositories.
- Keeping thin local Bash wrappers as transition entrypoints.
```

### Specify Results

| Metric | Value |
|---|---|
| Functional Requirements | 18 |
| User Stories | 3 |
| Acceptance Criteria | 7 acceptance scenarios; 7 measurable success criteria |

G1 validation: `validate-gate.sh G1 specs/xplat-007-python-tooling-and-release-gate-migration`
passed with `markers=0`. Phase 1 executor reported `0` `[NEEDS CLARIFICATION]`
markers, `0` `[Gap]` markers, and `0` `[CRITICAL]` markers.

### Files Generated

- [x] `specs/xplat-007-python-tooling-and-release-gate-migration/spec.md`
- [x] `specs/xplat-007-python-tooling-and-release-gate-migration/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** After Specify, if gate ownership, command shape, shell-removal,
payload evidence, or platform proof remains ambiguous. Use the design concept
open questions first.

### Clarify Prompts

#### Session 1: Active Gate Inventory And Ownership

```text
$speckit-clarify Focus on the exact XPLAT-007 active gate inventory: classify tests/speckit-pro/**, scripts/build-plugin-payloads.sh, scripts/refresh-local-plugin.sh, scripts/sync-marketplace-versions.sh, speckit-pro/skills/**/scripts/**, speckit-pro/codex-skills/**/scripts/**, speckit-pro/scripts/**, and .github/workflows/** as active release gate, active helper command, temporary parity fixture, inactive historical evidence, XPLAT-008 cutover surface, or out of scope.
```

#### Session 2: Runner Command Surface And Promotion Rules

```text
$speckit-clarify Focus on Python command taxonomy and gate promotion: decide which migrated commands become python -m speckit_pro_runner operations, which if any need standalone Python commands, what JSON/stdout/stderr/exit semantics each command preserves, and what fixture plus Bash-reference comparison evidence promotes Python as authoritative.
```

#### Session 3: No-Shell Guard And Legacy Cleanup

```text
$speckit-clarify Focus on the no-shell/no-jq active-path guard: define the scan scope, allowlist, false-positive exclusions, treatment of archive/provenance text, treatment of vendored Spec Kit consumer helpers, treatment of CI platform mechanics, and exact failure output when active Bash, .sh, jq, shell interpolation, or shell-only parsing remains.
```

#### Session 4: Payload, Install, Release, And Platform Proof

```text
$speckit-clarify Focus on payload/release helpers and proof boundaries: decide which test payloads are rebuilt as evidence, how local plugin refresh and install verification are tested, which release-readiness checks move to Python, which active maintainer docs or runbooks must change, and which source-checkout/macOS smoke plus Windows-style path fixtures are enough without installed-cache UAT.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---|---|---|---|
| 1 | Active gate inventory and ownership | 5 resolved | Classify by invocation role: active runner/workflow/release/helper entrypoints are XPLAT-007 gates; fixtures and Bash-reference manifests are temporary parity evidence; installed Claude/Codex invocation cutover remains XPLAT-008. Consensus skipped because the clarify executor reported no unresolved items. |
| 2 | Runner command surface and promotion rules | Pending | Pending |
| 3 | No-shell guard and legacy cleanup | Pending | Pending |
| 4 | Payload, install, release, and platform proof | Pending | Pending |

---

## Phase 3: Plan

**When to run:** After the spec is finalized. Generate the technical
implementation blueprint. Output:
`specs/xplat-007-python-tooling-and-release-gate-migration/plan.md`.

### Plan Prompt

```text
$speckit-plan

## Tech Stack
- Runtime: Python 3.11+ standard library through the XPLAT-004 runner package
  under `speckit-pro/speckit_pro_runner/`.
- Existing helper patterns: XPLAT-005 read-only registry/modules and XPLAT-006
  mutation-helper contracts, fixtures, install inventory, doctor/preflight
  proof, PR-body output, and command-plan diagnostics.
- Existing active Bash gate surfaces: `tests/speckit-pro/**`,
  `scripts/build-plugin-payloads.sh`, `scripts/refresh-local-plugin.sh`,
  `scripts/sync-marketplace-versions.sh`, `speckit-pro/skills/**/scripts/**`,
  `speckit-pro/codex-skills/**/scripts/**`, `speckit-pro/scripts/**`, and
  `.github/workflows/**`.
- Tests: Python standard-library tests and fixtures become authoritative after
  golden fixture and Bash-reference comparison promotion.
- Payload evidence: test payload rebuilds only; release payload cutover remains
  XPLAT-008.
- Docs/process: SpecKit CONTRACT artifacts under
  `specs/xplat-007-python-tooling-and-release-gate-migration/` and EXHAUST
  artifacts under `docs/ai/specs/.process/`.

## Constraints
- Record the setup reviewability warning: `status=warn`, `pass=true`, two
  primary surfaces (`docs/process`, `harness/adapter`), no blockers.
- Implement as one workflow with three internal slices unless planning proves a
  split is required.
- Start with Python-authoritative test/eval gates before payload/release helper
  migration.
- Prefer runner module commands; justify any standalone Python command.
- Use Bash-reference comparison only as temporary migration proof, not as a
  long-term active release gate.
- Target zero active repo-local shell scripts or shell-specific command paths.
- Keep active Claude/Codex invocation cutover, generated release payload
  cutover, public docs, release notes, update, autoheal, and native installed
  UAT out of scope.
- Keep broad historical/archive rewrites out of scope unless the file is part
  of an active gate.

## Architecture Notes
- Reuse the XPLAT runner envelope, diagnostics, path handling, manifest/checksum
  metadata, helper registry, and promotion-record concepts.
- Model migrated gates as explicit Python operations with stable stdout/stderr,
  exit-code, and artifact-output contracts.
- Build a no-shell/no-jq guard that classifies active paths separately from
  archive/provenance, inactive fixtures, and XPLAT-008 cutover surfaces.
- Preserve deterministic fixtures for path normalization, generated payload
  output, local plugin refresh, install verification, release metadata, and CI
  dispatch review.
- Reference `docs/ai/specs/.process/XPLAT-007-design-concept.md` for the
  accepted Grill Me decisions and non-goals.
```

### Plan Results

| Artifact | Status | Notes |
|---|---|---|
| `plan.md` | Pending | Must record technical context, file operations, reviewability warning, three-slice strategy, command surface, parity model, and no-shell guard |
| `research.md` | Pending | Should capture command taxonomy, promotion rules, guard scope, payload boundary, CI mechanics, and platform proof rationale |
| `data-model.md` | Pending | Should define migrated gate, command operation, parity comparison, promotion record, active-path guard finding, payload evidence, and release-readiness result entities |
| `contracts/` | Pending | Should include relevant command/result schemas or fixture contracts for migrated gates |
| `quickstart.md` | Pending | Should include maintainer commands for Python gates, no-shell guard, test payload evidence, and local smoke |

---

## Phase 4: Domain Checklists

**When to run:** After `$speckit-plan`, validate both the spec and plan. Run the
domains below because this work changes active gates, release tooling, and
shell-removal guardrails.

### Checklist Prompts

#### 1. Integration Checklist

```text
$speckit-checklist integration

Focus on XPLAT-007 requirements:
- Migration of active tests, evals, payload builders, install verification, repo helpers, and release-readiness gates to Python commands.
- Reuse of XPLAT-004 runner contracts, XPLAT-005 read-only helper patterns, and XPLAT-006 mutation-helper contracts where appropriate.
- Compatibility with current Layer 1, Layer 4, AI-eval, tool-scoping, integration, parity, payload, local refresh, marketplace/version sync, and install-verification flows.
- Pay special attention to not switching active Claude/Codex skill/hook/generated release payload/install behavior that belongs to XPLAT-008.
```

#### 2. Reliability Checklist

```text
$speckit-checklist reliability

Focus on XPLAT-007 requirements:
- Golden fixtures and Bash-reference comparison before Python gate promotion.
- Deterministic command output, exit codes, stderr diagnostics, artifact paths, test payload rebuild evidence, and local macOS smoke.
- Stability across Windows-style paths, spaces, line endings, missing prerequisites, stale generated files, and CI/local environment differences.
- Pay special attention to promotion records that let Bash references leave active gates without losing review evidence.
```

#### 3. Security Checklist

```text
$speckit-checklist security

Focus on XPLAT-007 requirements:
- No shell command strings, shell=True subprocess behavior, os.system, jq dependency, shell interpolation, or shell-only parsing in promoted Python gates.
- Safe path handling and bounded file writes for payload, local refresh, install-verification, and release-readiness helpers.
- Guard scope that prevents active Bash reintroduction without rewriting archive/provenance history.
- Pay special attention to accidental active Claude/Codex cutover or public support claims.
```

#### 4. Release-Readiness Checklist

```text
$speckit-checklist release-readiness

Focus on XPLAT-007 requirements:
- Python-authoritative release checks, marketplace/version sync, payload builder validation, install verification, and active-path no-shell guard.
- Evidence that test payload rebuilds are only test evidence and not release payload cutover.
- Clear XPLAT-008 handoff for generated release payloads, installed-cache UAT, public docs, update, autoheal, and public release readiness.
- Pay special attention to release blockers that must remain impossible to publish with active Bash or jq dependencies.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|---|---|---|---|
| Integration | Pending | Pending | Pending |
| Reliability | Pending | Pending | Pending |
| Security | Pending | Pending | Pending |
| Release-readiness | Pending | Pending | Pending |

---

## Phase 5: Tasks

**When to run:** After checklists complete and all true gaps are resolved.
Output: `specs/xplat-007-python-tooling-and-release-gate-migration/tasks.md`.

### Tasks Prompt

```text
$speckit-tasks

## Task Structure
- Organize by independently testable migrated gate behavior and accepted
  slices.
- Write failing Python fixtures/tests before each gate replacement.
- Preserve Bash-reference comparison tasks before Python promotion tasks.
- Mark parallel-safe tasks with [P] only when they touch independent fixtures,
  command adapters, docs/process evidence, or guard cases and do not compete
  for shared runner operation registration, promotion records, payload fixtures,
  or release-readiness summaries.
- Reference `spec.md`, `plan.md`, and
  `docs/ai/specs/.process/XPLAT-007-design-concept.md`.

## Implementation Slices
1. Test/eval runner gates: top-level test runner, Layer 1 structural checks,
   Layer 4 helper tests, AI-eval runners, tool-scoping checks, integration and
   parity suites, fixture migration, and promotion records.
2. Payload/install/release helpers: payload builder, local plugin refresh,
   marketplace/version sync, install verification, release checks,
   release-readiness checks, and test payload rebuild evidence.
3. Active-path guardrails and cleanup: no-shell/no-jq guard, active Bash
   command-path removal, CI mechanics review, historical/parity evidence
   classification, and XPLAT-008 handoff.

## Constraints
- Do not update active Claude/Codex invocation behavior, generated release
  payload selection/cutover, public install docs, release notes, update,
  autoheal, or native UAT artifacts.
- Do not keep thin local Bash wrappers as active transition entrypoints.
- Keep Bash-reference comparison temporary and explicitly retire it from active
  gates after Python promotion.
- Keep the final task list reviewable; if task generation proves the work is
  too large, record the split point before implementation starts.
```

### Tasks Results

| Metric | Value |
|---|---|
| Total Tasks | Pending |
| Phases | Pending |
| Parallel Opportunities | Pending |
| User Stories Covered | Pending |

---

## Atomicity Route

This section is populated after the Tasks phase by the autopilot skill. The
classifier output is recorded here only; it does not create PRs or split
branches by itself.

| Field | Value | Meaning |
|---|---|---|
| Route | Pending | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope` |
| Releasable | Pending | `true`, or `false` for destructive/concurrency-sensitive work |
| Signals | Pending | Detector findings behind the route |
| Warnings | Pending | Release-safety warnings |

Classifier command:

```text
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/xplat-007-python-tooling-and-release-gate-migration
```

---

## Phase 6: Analyze

**When to run:** Always run after tasks to catch drift and coverage gaps before
implementation.

### Analyze Prompt

```text
$speckit-analyze

Focus on:
1. Drift between the roadmap, PRD AC-7.*, XPLAT-007 design concept, spec.md, plan.md, and tasks.md.
2. Scope leakage into active Claude/Codex skill/hook/generated release payload/install cutover, public docs, release notes, native installed-plugin UAT, update, autoheal, or public support claims.
3. Coverage of active test/eval gates, payload builders, local plugin refresh, marketplace/version sync, install verification, release-readiness checks, no-shell guard, and active Bash command-path cleanup.
4. Consistency with XPLAT-004 runner envelope/preflight/source metadata, XPLAT-005 read-only helper patterns, and XPLAT-006 mutation-helper contracts/install inventory.
5. Reviewability risk: verify the three-slice task plan remains reviewable or records a concrete split before implementation starts.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|---|---|---|---|
| Pending | Pending | Pending | Pending |

---

## Phase 6.5: Confidence Gate

**When to run:** After Analyze consensus completes and before Phase 7 task
execution begins.

### Confidence Gate Command

```text
bash speckit-pro/skills/speckit-autopilot/scripts/resolve-confidence-mode.sh "$PWD"
bash speckit-pro/skills/speckit-autopilot/scripts/confidence-gate.sh specs/xplat-007-python-tooling-and-release-gate-migration
```

### Confidence Gate Results

| Mode | Exit | Result | Notes |
|---|---|---|---|
| Pending | Pending | Pending | Pending |

---

## Phase 7: Implement

**When to run:** After tasks are generated and analyzed with no blocking
coverage gaps.

### Implement Prompt

```text
$speckit-implement

## Approach: Test, Parity, Promotion, Cleanup

For each migrated gate or helper group:
1. RED: Add the deterministic fixture and Python test defining expected stdout,
   stderr, exit code, artifact output, path handling, and failure behavior.
2. REFERENCE: Add or update source-checkout Bash-reference comparison while the
   Bash gate still exists and is deterministic enough to compare.
3. GREEN: Implement the smallest Python runner operation or justified Python
   command needed to satisfy the fixture and comparison.
4. PROMOTE: Mark Python authoritative only after fixture parity and comparison
   pass. Remove the Bash command path from active gates or reclassify it as
   inactive historical evidence.
5. GUARD: Run the active-path no-shell/no-jq guard and fix any active command
   path that still depends on Bash, `.sh`, `jq`, shell interpolation, or
   shell-only parsing.
6. VERIFY: Run focused Python gates, test payload evidence, local smoke,
   spec-index check, diff hygiene, Layer 1, Layer 4, and the deterministic
   suite once available.

### Pre-Implementation Setup

1. Verify branch: `git rev-parse --abbrev-ref HEAD` should return
   `codex/xplat-007-python-tooling-and-release-gate-migration`.
2. Verify clean worktree before each phase: `git status --short`.
3. Run current baseline gates before migrating command paths:
   - `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"`
   - `bash tests/speckit-pro/run-all.sh --layer 1`
   - `bash tests/speckit-pro/run-all.sh --layer 4`
   - `bash tests/speckit-pro/run-all.sh`
4. Record which baseline gates are still Bash-backed so the task list can
   convert them intentionally.

### Implementation Notes

- Prefer structured Python APIs over shell-output string parsing.
- Use argv-list subprocesses only when subprocesses are unavoidable; never use
  shell command strings or shell interpolation.
- Keep migrated command modules small and explicit. Avoid a generic command
  framework unless the plan proves shared behavior is necessary across multiple
  gates.
- Normalize volatile paths, timestamps, platform names, git metadata,
  executable paths, and environment-specific fields in parity comparisons.
- Keep Bash-reference comparison temporary. It is migration evidence, not the
  final active gate.
- Do not update active Claude/Codex invocation behavior, generated release
  payload selection/cutover, install docs, public support claims, update,
  autoheal, or native installed-plugin UAT.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|---|---|---|---|
| Test/eval runner gates | Pending | Pending | Pending |
| Payload/install/release helpers | Pending | Pending | Pending |
| Active-path guardrails and cleanup | Pending | Pending | Pending |
| Smoke and handoff | Pending | Pending | Pending |

---

## Post-Implementation Checklist

These items are canonical autopilot phases and must remain visible in
`docs/ai/specs/.process/autopilot-state.json` and the active progress plan until
each item is completed or explicitly skipped by its extension rule.

| Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | Pending | Verify doctor/preflight extension state if invoked by this workflow |
| Post: Verify Implementation | Pending | Focused Python gates, no-shell guard, test payload evidence, and deterministic suite evidence |
| Post: Verify Tasks Phantom Check | Pending | G7 task completion proof |
| Post: Code Review | Pending | Self-review and optional delegated review findings |
| Post: Integration Suite | Pending | Relevant Layer 1, Layer 4, and default suite evidence after migration |
| Post: Reviewability Diff Gate | Pending | Reviewability gate result and any honored exception |
| Post: Self-Review | Pending | Confirm no active Claude/Codex cutover, release payload cutover, public support claim, update/autoheal, or native installed-plugin UAT shipped |
| Post: UAT Runbook Generation | Pending | Source-checkout smoke/runbook only; native installed-plugin UAT remains XPLAT-008 |
| Post: PR Body Generation | Pending | PR packet/body generated and validated |
| Post: PR Creation | Pending | PR URL |
| Post: Review Remediation | Pending | Review thread status and remediation summary |
| Post: Retrospective | Pending | Final retrospective before completion |

### Final Verification Targets

- [ ] All tasks marked complete in `tasks.md`.
- [ ] Python test/eval gates pass for migrated active gates.
- [ ] Python payload/install/release helper gates pass for migrated helpers.
- [ ] Test payload rebuild evidence is recorded without release payload cutover.
- [ ] Active-path no-shell/no-jq guard passes.
- [ ] Bash-reference comparison has been retired from active release gates or
  reclassified as inactive historical evidence.
- [ ] `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"` passes until the spec-index helper itself is migrated.
- [ ] Layer 1, Layer 4, and the deterministic suite pass through their
  Python-authoritative paths once implemented.
- [ ] No active Claude/Codex invocation-path, generated release payload
  selection/cutover, install behavior, public platform claim, update/autoheal,
  or native installed-plugin UAT changed.
- [ ] PR packet includes review order, scope budget, parity evidence, per-gate
  promotion state, no-shell guard evidence, test payload evidence, known gaps,
  rollback notes, and XPLAT-008 handoff.

---

## Project Structure Reference

```text
speckit-pro/
  speckit_pro_runner/             # XPLAT runner package and migrated operation surface
  skills/**/scripts/              # Current helper references to classify and migrate/remove
  codex-skills/**/scripts/        # Current Codex helper references to classify and migrate/remove
  scripts/                        # Current plugin helper references to classify and migrate/remove
scripts/
  build-plugin-payloads.sh        # Payload builder replacement candidate
  refresh-local-plugin.sh         # Local refresh replacement candidate
  sync-marketplace-versions.sh    # Version sync replacement candidate
tests/speckit-pro/
  run-all.sh                      # Top-level active test runner replacement candidate
  layer1-structural/              # Structural validation migration target
  layer4-scripts/                 # Helper test migration target
  layer4-scripts/fixtures/read-only-helpers/
                                  # XPLAT-005 fixture and parity patterns
  layer4-scripts/fixtures/mutation-helpers/
                                  # XPLAT-006 mutation fixture and contract patterns
docs/ai/specs/.process/
  XPLAT-007-design-concept.md
  XPLAT-007-workflow.md
specs/xplat-007-python-tooling-and-release-gate-migration/
  SPEC-MOC.md
  spec.md
  plan.md
  tasks.md
```
