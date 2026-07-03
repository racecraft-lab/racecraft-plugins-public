# SpecKit Workflow: XPLAT-006 - Mutation, Install, and PR-Emission Helper Port

**Template Version**: 1.0.0
**Created**: 2026-07-03
**Purpose**: Prepare XPLAT-006 for autonomous execution from the cross-platform plugin runtime roadmap and the setup Grill Me decisions.

---

## How to Use This Workflow

Run this workflow from the XPLAT-006 worktree:

```text
$speckit-autopilot docs/ai/specs/.process/XPLAT-006-workflow.md
```

This file is already populated for XPLAT-006. Do not replace it with the
generic workflow template.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`$speckit-scaffold-spec XPLAT-006`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/XPLAT-006-design-concept.md
```

Re-read it before each phase. The design concept is the source of truth for the
accepted scope:

- One XPLAT-006 workflow with three internal implementation slices.
- Mutation safety foundation first, then manifest-driven install/doctor work,
  then PR-emission, restack, migration, relocation, UAT, and reviewability
  helpers.
- Deterministic fake repositories, fake `gh`, fake `specify`, and fake
  Claude/Codex homes by default.
- Golden fixtures plus source-checkout Bash-reference comparison before
  promoting Python behavior for each Bash-backed mutation helper.
- Mixed-mode helpers only bring forward deferred write/apply behavior; accepted
  XPLAT-005 read-only modes are not re-ported.
- No active Claude Code or Codex invocation-path, hook, generated-payload
  selection/cutover, install, or public documentation cutover; phase-coverage
  hardening may update autopilot instructions and generated mirrors only.
- Local source-checkout mutation proof and Windows-style path fixtures only;
  installed-cache launch and native matrix UAT remain XPLAT-008.

> Grill Me is human-in-the-loop only. It is not part of the autopilot loop.
> Once this workflow begins, clarifications happen via `$speckit-clarify` and
> consensus, never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|---|---|---|---|
| Specify | `$speckit-specify` | Complete | Created `spec.md` and requirements checklist; G1 passed with 0 clarification markers |
| Clarify | `$speckit-clarify` | Complete | Sessions 1-4 complete; G2 passed with 0 clarification markers |
| Plan | `$speckit-plan` | Complete | Created plan, research, data model, quickstart, and five contracts; G3 passed with 0 markers; hardening evidence passed |
| Checklist | `$speckit-checklist` | Complete | Integration, error-handling, reliability, and security checklists complete with no gaps; consensus skipped |
| Tasks | `$speckit-tasks` | Complete | Generated 61 total tasks; implementation completed with golden/deferred promotion boundaries and G5 passed |
| Analyze | `$speckit-analyze` | Complete | Found and resolved one AC-6.6 task coverage gap; consensus skipped after remediation |
| Confidence Gate | G6.5 | Complete | Advisory `NO_DATA` soft-skip: no confidence emit found; phase-coverage validator passed |
| Implement | `$speckit-implement` | Complete | Runner mutation primitives, fake-home doctor proof, PR command planning, registry-visible deferred helpers, and hardening tests completed |
| Post | Autopilot post-implementation items | Pending | Complete doctor, verification, review, PR packet, PR creation, remediation, and retrospective items |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|---|---|---|
| G1 | After Specify | Scope is mutation/install/PR-emission helper porting only; no active cutover, repo-local Bash gate migration, public support claims, or native matrix UAT |
| G2 | After Clarify | Helper/mode matrix, mutation request model, doctor inventory, parity bar, fake/live mutation boundary, and mixed-mode ownership are unambiguous |
| G3 | After Plan | Plan records the reviewability warning, three-slice strategy, mutation safety primitives, manifest-driven doctor design, and fake-fixture proof boundary |
| G4 | After Checklist | All true integration, error-handling, reliability, and security gaps are remediated or explicitly out of scope |
| G5 | After Tasks | Tasks map to the accepted three slices and avoid XPLAT-007 gate migration or XPLAT-008 active cutover scope |
| G6 | After Analyze | No critical drift remains between roadmap, design concept, spec, plan, tasks, and XPLAT-005 runner/helper contracts |
| G6.5 | After Analyze Consensus | Pre-implementation confidence gate records pass, advisory no-data, or advisory fail disposition before implementation begins |
| G7 | After Implementation | Python mutation-helper tests, golden fixtures, Bash-reference metadata, source-checkout proof, spec-index check, diff hygiene, and relevant repo gates pass; no Bash-backed helper becomes Python-authoritative in XPLAT-006 |

---

## Prerequisites

### Worktree and Branch

- Worktree: `.worktrees/xplat-006-mutation-install-pr-emission-helper-port`
- Branch: `codex/xplat-006-mutation-install-pr-emission-helper-port`
- Contract marker: `specs/xplat-006-mutation-install-pr-emission-helper-port/SPEC-MOC.md`
- Design concept: `docs/ai/specs/.process/XPLAT-006-design-concept.md`
- Workflow: `docs/ai/specs/.process/XPLAT-006-workflow.md`

Expected branch is `codex/xplat-006-mutation-install-pr-emission-helper-port`.
Preset resolution should use `.specify/presets/speckit-pro-reviewability/`
unless a deliberate higher-priority override exists.

### Grounded Source Truth

- Roadmap: `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
- Roadmap MOC: `docs/ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md`
- Product requirement: `docs/prd-cross-platform-plugin-runtime.md`
- Runtime inventory: `docs/ai/research/cross-platform-runtime-inventory.md`
- XPLAT-004 runner package: `speckit-pro/speckit_pro_runner/`
- XPLAT-005 design concept and workflow:
  `docs/ai/specs/.process/XPLAT-005-design-concept.md` and
  `docs/ai/specs/.process/XPLAT-005-workflow.md`
- XPLAT-005 read-only helper fixtures:
  `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/`
- XPLAT-005 runner helper registry:
  `speckit-pro/speckit_pro_runner/helpers/registry.py` and
  `speckit-pro/speckit_pro_runner/helpers/read_only.py`
- Current Bash helper sources: `speckit-pro/skills/**/scripts/`,
  `speckit-pro/codex-skills/**/scripts/`, and `speckit-pro/scripts/`
- Current mutation-helper tests under `tests/speckit-pro/layer4-scripts/`
- Project constitution: `.specify/memory/constitution.md`
- Design concept source: `docs/ai/specs/.process/XPLAT-006-design-concept.md`

### Phase 0 Preflight Results

| Check | Result | Evidence |
|---|---|---|
| Codex agent install | Pass | `validate-agent-install.sh --surface codex --autoheal` reported `ok: codex: 10 bundled agents installed` |
| SpecKit CLI | Pass | `command -v specify` resolved to an installed `specify` executable; local absolute path intentionally omitted |
| Remote | Pass | `git remote -v` detected `origin` |
| Branch/worktree | Pass | Created worktree on `codex/xplat-006-mutation-install-pr-emission-helper-port` from `origin/main` at `b9fa4987` |
| Reviewability setup gate | Warn/pass | `reviewability-gate.sh setup docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md` returned `status: warn`, `pass: true`, `reviewable_loc: 250`, `production_files: 4`, `total_files: 10`, warning: primary surfaces `docs/process` and `harness/adapter` exceed one-surface warning threshold |
| Grill Me | Complete | 8 picker questions; accepted one workflow with three slices, mutation safety first, manifest-driven doctor, fixtures plus Bash comparison, fake mutation by default, no active cutover, write modes only for mixed helpers, and source-checkout platform proof |
| Preset resolution | Pass | `specify preset resolve spec-template`, `plan-template`, and `tasks-template` resolve to `speckit-pro-reviewability v1.0.0` |

### Constitution Validation

| Principle | XPLAT-006 Requirement | Verification |
|---|---|---|
| Plugin Structure Compliance | New runner helper ports stay inside the `speckit-pro/` plugin and preserve manifest validity | Layer 1 structural validation and manifest review |
| Script Safety | New replacement helper logic uses Python 3.11+ standard library and argv-list subprocess handling only where subprocesses are unavoidable | Python helper tests, parity fixtures, no-shell audits, and code review |
| Semantic Versioning | Do not edit plugin versions manually | Diff review |
| Test Coverage Before Merge | Add Python standard-library tests and fixture parity before promoting mutation helper behavior | Focused mutation-helper tests, Layer 4, Layer 1, and deterministic suite before PR |
| Conventional Commits | Setup and implementation commits use conventional commit format | Commit and PR title review |
| KISS, Simplicity, YAGNI | Extend the explicit helper registry and add small per-helper modules; avoid a generic mutation framework unless plan evidence proves reuse | Plan complexity table and G6 analysis |

---

## Specification Context

### Basic Information

| Field | Value |
|---|---|
| Spec ID | XPLAT-006 |
| Name | Mutation, Install, and PR-Emission Helper Port |
| Branch | `codex/xplat-006-mutation-install-pr-emission-helper-port` |
| Feature directory | `specs/xplat-006-mutation-install-pr-emission-helper-port` |
| Dependencies | XPLAT-004 complete/archived; XPLAT-005 complete/archived; Python runner, helper registry, and read-only parity fixtures exist |
| Enables | XPLAT-007 Python tooling and release-gate migration; XPLAT-008 Claude/Codex cutover and universal install release gate |
| Priority | P1 |

### Success Criteria Summary

- [ ] Every mutation-capable installed-runtime helper has a runner equivalent or
  an explicitly documented out-of-scope/deferred status.
- [ ] Dry-run/apply behavior, atomic writes, dirty-worktree checks, no-op paths,
  partial failures, rollback notes, and manual remediation outcomes are covered
  by deterministic fixtures.
- [ ] PR packet, workflow-contract, split-PR, restack, install, doctor, and
  relocation JSON schemas and diagnostics are preserved.
- [ ] Claude Code and Codex install helpers verify complete expected bundled
  agents, generated payload files, runner files, and metadata from a
  source-controlled manifest or generated inventory.
- [ ] Scaffold/status/autopilot have a shared doctor/preflight contract with
  deterministic safe-repair and unsafe-manual-remediation outcomes.
- [ ] Mutation-helper Python tests become authoritative only after fixture and
  Bash-reference parity are accepted per helper.
- [x] No active Claude/Codex invocation-path, generated-payload
  selection/cutover, install behavior, public documentation claim, repo-local
  Bash gate migration, or native matrix UAT lands in XPLAT-006; allowed
  phase-coverage hardening source/mirror changes are listed separately.

### Accepted Three-Slice Plan

| Slice | Scope | Explicit Boundary |
|---|---|---|
| Slice 1 | Mutation safety foundation, runner mutation request/response model, atomic-write primitives, fake fixture harness, path and dirty-worktree guards | No helper-specific install, PR-emission, restack, migration, or relocation behavior until shared mutation semantics are accepted |
| Slice 2 | Manifest-driven install completeness, `install-codex-agents`, `install-curated-set`, coach/preset write helpers, doctor/preflight safe repair and manual remediation | No active skill/hook/install-guidance cutover; fake Codex/Claude homes by default |
| Slice 3 | `generate-pr-body`, `generate-uat-skeleton`, `final-reviewability-backstop`, `multi-pr-emission`, `restack`, `migrate-structure`, `relocate-process-artifacts`, deferred mixed write modes | No live GitHub mutation by default; fake `gh` and dry-run proof before any approved live path |

---

## Phase 1: Specify

**When to run:** At the start of XPLAT-006. Focus on what mutation/install/PR
helpers must preserve, what safety semantics they must add, and what cutover is
deliberately deferred. Output:
`specs/xplat-006-mutation-install-pr-emission-helper-port/spec.md`.

### Specify Prompt

```text
$speckit-specify

## Feature: Mutation, Install, and PR-Emission Helper Port

### Problem Statement
SpecKit Pro now has a Python 3.11+ standard-library runner foundation and
read-only helper registry from XPLAT-004 and XPLAT-005, but helpers that write
files, install agents, generate PR packets, emit split-PR state, relocate
process artifacts, migrate structure, restack PRs, or repair installs still rely
on Bash helper behavior. XPLAT-006 must port those state-mutating helper paths
to the runner with explicit dry-run/apply semantics, atomic write behavior,
manifest-driven install completeness, deterministic fixture parity, and safe
approval boundaries before XPLAT-007 removes Bash from active repo-local gates.

### Users
- Maintainers who need mutation-capable helpers to behave consistently without
  Bash as the long-term implementation substrate.
- SpecKit operators who need dry-run, apply, rollback, and manual remediation
  outcomes to be deterministic before any helper mutates repo or user-local
  state.
- Claude/Codex install maintainers who need expected bundled agents, generated
  payload files, runner files, and release metadata verified from source truth.
- XPLAT-007 and XPLAT-008 implementers who need mutation helper behavior,
  doctor/preflight contracts, and install completeness evidence before gate
  migration and active cutover.

### User Stories
1. As a maintainer, I can invoke Python runner equivalents for mutation helpers
   and get the same JSON, diagnostic, exit-code, dry-run, apply, no-op,
   dirty-worktree, and partial-failure semantics as current shipped helpers.
2. As an install maintainer, I can run a manifest-driven doctor/preflight check
   that detects stale releases, missing bundled agents, missing runner files,
   missing generated payload files, and safe versus unsafe repair cases.
3. As a release reviewer, I can inspect deterministic fixtures and
   Bash-reference comparisons proving mutation helper parity without requiring
   live GitHub mutation, real user-home writes, or active Claude/Codex cutover.

### Constraints
- Follow the design concept decisions in
  `docs/ai/specs/.process/XPLAT-006-design-concept.md`.
- Use Python 3.11+ standard library only for new runner helper logic; no new
  runtime dependency, package install, virtualenv restore, `jq`, Bash,
  PowerShell, Node, Go, Rust, or Zig for promoted helper execution.
- Reuse the XPLAT-005 helper registry and per-helper module pattern where it is
  still appropriate, but extend it explicitly for mutation-safe modes rather
  than forcing mutation behavior through `read_only`.
- Preserve current stdout JSON schemas, stderr diagnostics, human-readable
  remediation, and documented exit codes.
- Require deterministic fake repositories, fake `gh`, fake `specify`, and fake
  Claude/Codex homes by default.
- Require golden fixtures plus source-checkout Bash-reference comparisons
  before promoting each Bash-backed mutation helper.
- Keep live repo/user-local/GitHub mutation behind explicit approval and prior
  dry-run evidence.
- Keep one workflow with three internal slices unless planning proves a split is
  required.

### Out of Scope
- Active Claude Code or Codex invocation-path, hook, generated-payload
  selection/cutover, install, or public documentation cutover, except the
  explicit phase-coverage hardening source and generated mirror.
- Replacing repo-local Bash tests, evals, payload builders, release scripts,
  install-verification scripts, or release-readiness gates; that is XPLAT-007.
- Full native Windows/macOS/Linux installed-plugin UAT; that is XPLAT-008.
- Re-porting accepted XPLAT-005 read-only helper modes.
- Public native-platform support claims.
```

### Specify Results

| Metric | Value |
|---|---|
| Functional Requirements | 34 |
| User Stories | 3 |
| Acceptance Criteria | 11 acceptance scenarios |

### Files Generated

- [x] `specs/xplat-006-mutation-install-pr-emission-helper-port/spec.md`
- [x] `specs/xplat-006-mutation-install-pr-emission-helper-port/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** After Specify, if helper grouping, mutation semantics, parity,
or safe-repair boundaries remain ambiguous. Use the design concept open
questions first.

### Clarify Prompts

#### Session 1: Helper And Mode Matrix

```text
$speckit-clarify Focus on the exact XPLAT-006 helper and mode matrix: classify generate-pr-body, generate-uat-skeleton, final-reviewability-backstop, multi-pr-emission, restack, detect-stack-manager mutation-adjacent modes, migrate-structure, relocate-process-artifacts, install-curated-set, install-codex-agents, coach/preset write helpers, doctor/install-completeness helpers, and deferred mixed write modes into Slice 1, Slice 2, Slice 3, deferred, or out of scope. Preserve XPLAT-005 read-only modes without re-porting them.
```

#### Session 2: Mutation Safety And Atomicity

```text
$speckit-clarify Focus on mutation safety semantics: define dry-run versus apply response fields, planned and applied operation records, atomic write policy, dirty-worktree behavior, no-op behavior, partial-failure recovery, rollback notes, path-boundary checks, symlink handling, and line-ending behavior for helpers that write files.
```

#### Session 3: Install Completeness And Doctor

```text
$speckit-clarify Focus on install completeness and doctor/preflight: choose the source-controlled manifest or generated inventory for expected Claude/Codex agents, runner files, generated payload files, checksums, and version metadata; define stale release detection, safe auto-repair cases, unsafe manual-remediation cases, and fake-home fixture coverage.
```

#### Session 4: PR, Restack, Relocation, And Approval Boundary

```text
$speckit-clarify Focus on PR-emission, restack, migration, relocation, and approval boundaries: decide which behavior is dry-run only, which behavior can have fake `gh` apply fixtures, how live GitHub/user-local/repo mutation approval is represented, and how the PR review packet reports known gaps without active cutover.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---|---|---|---|
| 1 | Helper and mode matrix | 5 resolved | Slice 1 is shared mutation foundation only; Slice 2 owns install/doctor/coach/preset writes; Slice 3 owns PR/restack/migration/relocation/generated write modes plus `detect-stack-manager` support; XPLAT-005 read-only modes are not re-ported |
| 2 | Mutation safety and atomicity | 5 resolved | Stable mutation response model, per-file atomic replace policy, strict dirty-worktree default, boundary/symlink rejection for writes, and deterministic LF generated-output policy |
| 3 | Install completeness and doctor | 5 resolved | Committed generated install inventory is the doctor source of truth; doctor/preflight is read-only by default; repair is separate approved apply-mode; stale detection is offline and deterministic; safe repair is limited to fake or explicitly approved declared boundaries with fake-home fixture coverage |
| 4 | PR/restack/relocation and approval boundary | 6 resolved | Candidate PR emission is dry-run command capture; fake PR/restack fixtures may exercise apply paths; live GitHub/repo mutation requires structured approval evidence after dry-run and clean-worktree checks; `detect-stack-manager` emits decisions only; known gaps must separate unpromoted helpers, XPLAT-007/XPLAT-008 cutover, and live-coverage limits |

### Clarify Gate And Hardening Evidence

| Check | Result | Evidence |
|---|---|---|
| G2 | Pass | `validate-gate.sh G2 specs/xplat-006-mutation-install-pr-emission-helper-port` returned 0 markers |
| Autopilot phase coverage regression | Pass | `python3 tests/speckit-pro/layer4-scripts/test-autopilot-phase-coverage.py` returned 6/6 passed |
| Current workflow/state phase coverage | Pass | `validate-autopilot-phase-coverage.py --workflow docs/ai/specs/.process/XPLAT-006-workflow.md --state docs/ai/specs/.process/autopilot-state.json` returned `status: pass` with 37 plan steps |
| Layer 4 suite | Pass | `bash tests/speckit-pro/run-all.sh --layer 4` returned 2141/2141 passed |
| Layer 1 suite | Pass | `bash tests/speckit-pro/run-all.sh --layer 1` returned 1443/1443 passed |

---

## Phase 3: Plan

**When to run:** After the spec is finalized. Generate the technical
implementation blueprint. Output:
`specs/xplat-006-mutation-install-pr-emission-helper-port/plan.md`.

### Plan Prompt

```text
$speckit-plan

## Tech Stack
- Runtime: Python 3.11+ standard library through the XPLAT-004 runner package
  under `speckit-pro/speckit_pro_runner/`.
- Existing runner/helper pattern: XPLAT-005 helper registry and read-only helper
  modules under `speckit-pro/speckit_pro_runner/helpers/`.
- Existing reference implementations: Bash helpers under
  `speckit-pro/skills/**/scripts/`, `speckit-pro/codex-skills/**/scripts/`, and
  `speckit-pro/scripts/`.
- Tests: Python standard-library mutation-helper tests plus existing shell-layer
  gates as temporary migration/reference evidence until XPLAT-007.
- Hardening: Python standard-library autopilot phase-coverage validator and
  regression tests for missing Phase 6.5, missing Post items, collapsed later
  phases, and malformed state JSON.
- Docs/process: SpecKit CONTRACT artifacts under
  `specs/xplat-006-mutation-install-pr-emission-helper-port/` and EXHAUST
  artifacts under `docs/ai/specs/.process/`.
- Generated-payload selection/cutover and active install guidance: Out of scope
  for XPLAT-006, except the generated mirror required to prove phase-coverage
  hardening parity.

## Constraints
- Record the setup reviewability warning: `status=warn`, `pass=true`, two
  primary surfaces (`docs/process`, `harness/adapter`), no blockers.
- Implement as one workflow with three internal slices unless planning proves a
  split is required.
- Start with shared mutation safety primitives before helper-specific ports.
- Default to deterministic fake repositories, fake CLI tools, and fake
  Claude/Codex homes. Do not require real user-home writes or live GitHub
  mutation for deterministic tests.
- Preserve current JSON stdout, human-readable diagnostics, stderr behavior, and
  exit-code semantics.
- Use golden fixtures plus source-checkout Bash-reference comparison before
  promotion for every Bash-backed mutation helper.
- Keep helper ports Python 3.11+ standard-library only.
- Keep active Claude/Codex cutover, generated-payload selection/cutover, public
  docs, and native matrix UAT out of scope; only the autopilot hardening source
  and generated mirror may change.
- Do not assume instruction text is enough to harden autopilot phase tracking;
  include deterministic validator/test proof in the plan and PR packet.

## Architecture Notes
- Reuse the XPLAT-004 runner envelope, diagnostics, typed path, source metadata,
  and preflight primitives.
- Extend the XPLAT-005 helper registry pattern explicitly for mutation-capable
  modes. Do not force write/apply semantics through `read_only`.
- Model mutation results with planned operations, applied operations,
  dry-run/apply status, touched paths, rollback/manual-remediation notes, and
  deterministic failure classes.
- Build install completeness from source-controlled manifests or generated
  inventory, not stale hardcoded bundled-agent lists.
- Require argv-list subprocess handling and fake CLIs for parity fixtures.
- Include the phase-coverage validator in the plan as a shipped hardening path:
  workflow/state validation must fail before a run advances if Phase 6.5 or
  canonical Post items are missing.
- Reference `docs/ai/specs/.process/XPLAT-006-design-concept.md` for the
  accepted Grill Me decisions and non-goals.
```

### Plan Results

| Artifact | Status | Notes |
|---|---|---|
| `plan.md` | Complete | Records technical context, declared file operations, reviewability warning, three-slice strategy, helper/mode matrix, safety model, and scope-boundary hardening |
| `research.md` | Complete | Captures runner mutation model, manifest source, parity strategy, fake/live boundary, hardening rationale, and cutover deferral decisions |
| `data-model.md` | Complete | Defines mutation helper request/result, planned/applied operation, safe-repair result, fixture, comparison, promotion record, scope audit, and phase-coverage report entities |
| `contracts/` | Complete | Includes mutation-helper request/result, doctor/preflight result, helper-promotion record, and autopilot phase-coverage report schemas |
| `quickstart.md` | Complete | Includes maintainer commands for hardening validation, fake fixture runs, source-checkout mutation proof, focused tests, and scope audit |

### Plan Verification Evidence

| Check | Result |
|---|---|
| G3 | Pass: `validate-gate.sh G3` reported `pass=true`, 0 markers |
| Phase coverage hardening | Pass: regression test 6/6 and live workflow/state validator `status=pass` with 37 plan steps |
| Scope audit hardening | Pass: `test-speckit-pro-runner.py` 9/9 after allowing only exact phase-coverage hardening source/mirror files |
| Layer 1 | Pass: `bash tests/speckit-pro/run-all.sh --layer 1` reported 1443/1443 |
| Layer 4 | Pass: `bash tests/speckit-pro/run-all.sh --layer 4` reported 2141/2141 |
| Index/diff hygiene | Pass: spec-index check current, MOC stale-index check clean, privacy scan 10/10, `git diff --check` clean |

---

## Phase 4: Domain Checklists

**When to run:** After `$speckit-plan`, validate both the spec and plan. Run the
domains below because this work writes state, crosses install/PR boundaries, and
is release-gate-adjacent.

### Checklist Prompts

#### 1. Integration Checklist

```text
$speckit-checklist integration

Focus on XPLAT-006 requirements:
- XPLAT-004 runner envelope, diagnostics, typed path, preflight, and metadata reuse.
- XPLAT-005 registry/module pattern reuse without forcing mutation behavior through read-only mode.
- Helper/mode matrix across install, doctor, PR-emission, restack, migration, relocation, UAT, reviewability, and mixed write modes.
- Manifest-driven install completeness for Claude/Codex bundled agents, generated payload files, runner files, and metadata.
- Pay special attention to avoiding active Claude/Codex invocation behavior, generated-payload selection/cutover, install-guidance, public-doc, or release-gate migration scope; allowed phase-coverage hardening source/mirror changes must be listed separately.
```

#### 2. Error-Handling Checklist

```text
$speckit-checklist error-handling

Focus on XPLAT-006 requirements:
- Preservation of current helper exit codes, stdout JSON, stderr diagnostics, and remediation text.
- Dry-run/apply divergence, no-op, dirty worktree, missing prerequisite, invalid input, malformed JSON, path escape, write failure, partial failure, and rollback/manual-remediation cases.
- Doctor safe-repair versus unsafe manual-remediation outcomes.
- Pay special attention to deterministic failure classes and partial writes.
```

#### 3. Reliability Checklist

```text
$speckit-checklist reliability

Focus on XPLAT-006 requirements:
- Deterministic fake repositories, fake `gh`, fake `specify`, and fake Claude/Codex homes.
- Golden fixtures plus Bash-reference comparisons before helper promotion.
- Atomic write behavior, backup/rollback notes, repeatability, and environment-sensitive normalization.
- Pay special attention to tests that must not depend on network, installed-cache state, mutable user-local state, or real GitHub mutation.
```

#### 4. Security Checklist

```text
$speckit-checklist security

Focus on XPLAT-006 requirements:
- No shell injection, shell=True subprocess behavior, `os.system`, command-string interpolation, or unbounded path writes in new Python helper ports.
- Safe path handling for Windows-style paths, spaces, symlinks, relative components, line endings, and repo/plugin/user-home trust boundaries.
- No new package installs, runtime dependencies, virtualenv restore, `jq`, Bash, PowerShell, Node, Go, Rust, or Zig for promoted helper execution.
- Pay special attention to mutation approval boundaries and prevention of accidental active cutover.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|---|---|---|---|
| Integration | 12 complete | 0 | FR-001 through FR-036; SC-001, SC-005, SC-006; `checklists/integration.md` |
| Error-handling | 12 complete | 0 | FR-004 through FR-021; FR-035 through FR-036; SC-002 through SC-004; `checklists/error-handling.md` |
| Reliability | 13 complete | 0 | FR-012 through FR-019; FR-027 through FR-031; FR-035 through FR-036; SC-001 through SC-004; `checklists/reliability.md` |
| Security | 11 complete | 0 | FR-007 through FR-013; FR-032 through FR-036; SC-005; `checklists/security.md` |

Consensus: skipped for all four domains because no checklist reported a true
gap.

---

## Phase 5: Tasks

**When to run:** After checklists complete and all true gaps are resolved.
Output: `specs/xplat-006-mutation-install-pr-emission-helper-port/tasks.md`.

### Tasks Prompt

```text
$speckit-tasks

## Task Structure
- Organize by independently testable mutation behavior and accepted slices.
- Write failing Python fixtures/tests before each helper port.
- Preserve Bash-reference comparison tasks before gate-promotion tasks.
- Mark parallel-safe tasks with [P] only when they touch independent helpers,
  fixture files, docs, or fake-home cases and do not compete for shared mutation
  primitives, registry entries, manifests, or promotion records.
- Reference `spec.md`, `plan.md`, and
  `docs/ai/specs/.process/XPLAT-006-design-concept.md`.

## Implementation Slices
1. Mutation safety foundation: runner mutation mode contract, dry-run/apply
   request/response model, atomic-write helpers, path and dirty-worktree guards,
   fake fixture harness, failure classes, and promotion records.
2. Install completeness and doctor/preflight: manifest or generated inventory,
   install-curated-set, install-codex-agents, coach/preset write helpers, safe
   repair, unsafe manual remediation, fake Claude/Codex homes, and generated
   payload/runner-file completeness checks.
3. PR-emission, restack, migration, and relocation: generate-pr-body,
   generate-uat-skeleton, final-reviewability-backstop, multi-pr-emission,
   restack, migrate-structure, relocate-process-artifacts, deferred mixed write
   modes, fake `gh` fixtures, and handoff evidence.

## Constraints
- Do not update active Claude/Codex invocation behavior, generated-payload
  selection/cutover, install guidance, public docs, release notes, or native
  UAT artifacts; allowed phase-coverage hardening source/mirror changes must be
  listed separately.
- Do not replace repo-local Bash test/eval/build/payload/release gates in this
  spec.
- Keep live repo/user-local/GitHub mutation out of deterministic tests unless
  explicitly approved after dry-run evidence.
- Keep Python tests authoritative only after parity is accepted per helper.
- Keep the final task list reviewable; if task generation proves the work is too
  large, record the split point before implementation starts.
```

### Tasks Results

| Metric | Value |
|---|---|
| Total Tasks | 61 total; 55 open tasks reported by G5 because 6 hardening tasks are already complete |
| Phases | Three accepted implementation slices plus setup and handoff |
| Parallel Opportunities | Fixture seeds, independent failing test groups, US2/US3 after shared mutation primitives, and final hardening/scope checks |
| User Stories Covered | HARD baseline, US1 mutation safety, US2 install/doctor, US3 PR-emission/reviewability, HANDOFF |
| G5 | Pass: `validate-gate.sh G5` reported 55 open tasks and 0 markers |

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
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/xplat-006-mutation-install-pr-emission-helper-port
```

---

## Phase 6: Analyze

**When to run:** Always run after tasks to catch drift and coverage gaps before
implementation.

### Analyze Prompt

```text
$speckit-analyze

Focus on:
1. Drift between the roadmap, PRD AC-6.*, XPLAT-006 design concept, spec.md, plan.md, and tasks.md.
2. Scope leakage into active Claude/Codex cutover, generated-payload selection/cutover, public docs, native matrix UAT, or XPLAT-007 repo-local Bash gate migration, with phase-coverage hardening source/mirror changes listed separately.
3. Coverage of each accepted mutation helper group, dry-run/apply behavior, atomic write rule, dirty-worktree guard, fake/live mutation boundary, parity fixture, Bash-reference comparison, and per-helper promotion rule.
4. Consistency with XPLAT-004 runner envelope/preflight/source metadata and XPLAT-005 helper registry/parity patterns.
5. Reviewability risk: verify the three-slice task plan remains reviewable or records a concrete split before implementation starts.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|---|---|---|---|
| AN-001 | Medium | AC-6.6 requires scaffold/status/autopilot to be able to call a shared doctor/preflight contract before workflow execution, but `tasks.md` only required the contract implementation and did not explicitly require registry-exposed callable operation ids. | Resolved by adding T035 to expose doctor/preflight operation ids through `speckit-pro/speckit_pro_runner/helpers/registry.py` without active invocation cutover; G5 now passes with 55 open tasks and 0 markers. |

Consensus: skipped after remediation because no unresolved Analyze issues remain.

---

## Phase 6.5: Confidence Gate

**When to run:** After Analyze consensus completes and before Phase 7 task
execution begins.

### Confidence Gate Command

```text
bash speckit-pro/skills/speckit-autopilot/scripts/resolve-confidence-mode.sh "$PWD"
bash speckit-pro/skills/speckit-autopilot/scripts/confidence-gate.sh specs/xplat-006-mutation-install-pr-emission-helper-port
```

### Confidence Gate Results

| Mode | Exit | Result | Notes |
|---|---|---|---|
| advisory | 1 | `NO_DATA` soft-skip | `confidence-gate.sh docs/ai/specs/.process/XPLAT-006-workflow.md --mode advisory` found no confidence emit; phase-coverage validator passed, so implementation may proceed |

---

## Phase 7: Implement

**When to run:** After tasks are generated and analyzed with no blocking
coverage gaps.

### Implement Prompt

```text
$speckit-implement

## Approach: Test, Safety, And Parity First

For each helper or helper group:
1. RED: Add the deterministic fake fixture and Python test that defines expected
   dry-run/apply behavior, stdout JSON, diagnostics, exit code, touched paths,
   rollback/remediation notes, and failure class.
2. REFERENCE: Add or update the source-checkout Bash-reference comparison where
   current Bash behavior is deterministic enough to compare.
3. GREEN: Implement the smallest Python runner helper module, registry entry,
   and mutation primitive needed to satisfy the fixture and comparison.
4. PROMOTE: Mark the Python test authoritative for that helper only after golden
   fixture parity and Bash-reference comparison pass.
5. VERIFY: Run focused mutation-helper tests, Layer 4, Layer 1, spec-index
   check, diff hygiene, source-checkout proof, and scope audit.

### Pre-Implementation Setup

1. Verify branch: `git rev-parse --abbrev-ref HEAD` should return
   `codex/xplat-006-mutation-install-pr-emission-helper-port`.
2. Verify clean worktree before each phase: `git status --short`.
3. Run current baseline gates before helper changes:
   - `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"`
   - `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh`
   - `tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.sh`
   - `bash tests/speckit-pro/run-all.sh --layer 1`
   - `bash tests/speckit-pro/run-all.sh --layer 4`

### Implementation Notes

- Prefer structured parsing and Python standard-library APIs over shell-output
  string manipulation.
- Keep helper modules small and explicit. Avoid a generic mutation framework
  unless the plan proves shared behavior is necessary across multiple helpers.
- Use argv-list subprocesses only when subprocesses are unavoidable; never use
  shell command strings or shell interpolation.
- Normalize volatile paths, timestamps, platform names, git metadata, and
  environment-specific fields in parity comparisons before asserting equality.
- Keep Bash helpers available as temporary source-checkout references until
  XPLAT-007 removes or archives them from active release gates.
- Do not update active invocation behavior, hook config, generated-payload
  selection/cutover, install docs, public support claims, or release-readiness
  gates in this spec; the only allowed skill/payload updates are the
  phase-coverage hardening source and generated mirror.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|---|---|---|---|
| Mutation safety foundation | Complete | T007-T027 | Added mutation registry dispatch, dry-run/apply operation records, atomic writes, dirty-worktree guard, path/symlink/external path rejection, partial-failure reporting, promotion metadata, and manifest/checksum refresh |
| Install completeness and doctor/preflight | Complete | T028-T038 | Added committed install inventory, doctor-preflight safe-repair/complete/malformed-inventory classifications, fake-home repair, real-home refusal, and deferred install helper entries |
| PR-emission, restack, migration, and relocation | Complete | T039-T049 | Added PR-body golden output, dry-run PR command planning, authoritative request fixtures, and deferred entries for restack, relocation, generated-index, PR-packet, and workflow-contract write modes |
| Smoke and handoff | Complete | T050-T061 | Focused mutation/runner/read-only tests passed; full Layer 4 now includes mutation-helper hardening and passed 2157/2157 |

### Implementation Evidence

| Check | Result | Evidence |
|---|---|---|
| Mutation helper hardening red state | Failed before implementation | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py` initially failed 9/10 because mutation helper modes and dispatch were missing |
| Mutation helper hardening green state | Pass | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py` passed 15/15 after remediation, including schema contract drift checks, dry-run no-write, apply write, dirty-worktree refusal, git-status fail-closed refusal, no-op apply, path/symlink/external escape rejection, preflight parent-file rejection, partial failure, fake-home boundary repair, malformed inventory, PR body output, and deferred PR command-plan apply |
| Runner compatibility | Pass | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` passed 9/9 after manifest/checksum refresh |
| Read-only compatibility | Pass | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py` passed 32/32; XPLAT-005 read-only registry still reports no mutation modes |
| Layer 4 aggregate | Pass | `bash tests/speckit-pro/run-all.sh --layer 4` passed 2157/2157 and now includes `test-speckit-pro-mutation-helpers (15/15)` |

### Promotion Boundary

- No Bash-backed mutation helper is Python-authoritative in XPLAT-006.
- `mutation-foundation`, `doctor-preflight`, `doctor-repair`, `generate-pr-body`, and `multi-pr-emission` have golden fixture proof.
- Install, restack, relocation, generated-index, PR-packet, workflow-contract write, and remaining mixed-mode helpers are registry-visible with deferred/out-of-scope promotion metadata and rollback notes.
- Bash-reference metadata is recorded for future comparison, but active gate migration and cutover remain XPLAT-007/XPLAT-008.

---

## Post-Implementation Checklist

These items are canonical autopilot phases and must remain visible in
`docs/ai/specs/.process/autopilot-state.json` and the active progress plan until
each item is completed or explicitly skipped by its extension rule.

| Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | Complete | Doctor/preflight and fake-home repair covered by `test-speckit-pro-mutation-helpers.py` 15/15 |
| Post: Verify Implementation | Complete | `bash tests/speckit-pro/run-all.sh` passed 3800/3800 |
| Post: Verify Tasks Phantom Check | Complete | G7 passed: all 61 tasks complete |
| Post: Code Review | Complete | Self-review found and fixed deterministic `write_failure` handling before final suite run |
| Post: Integration Suite | Complete | Default deterministic suite passed Layer 1, Layer 4, and Layer 5 |
| Post: Reviewability Diff Gate | Complete | `reviewability-gate.sh diff origin/main...HEAD` returned `status=exception`, `pass=true`, `exception_honored=true`; final backstop proceeded with collapsed full-spec marker plan |
| Post: Self-Review | Complete | No active invocation cutover, generated-payload cutover, repo-local Bash gate migration, native matrix UAT, or public support claim shipped |
| Post: UAT Runbook Generation | Complete | Authored `.process/uat-runbook.md`; `test-validate-uat-runbook.sh` passed 12/12 |
| Post: PR Body Generation | Complete | Generated repo-relative packet/body under `.process/pr-packets/xplat-006-pr-packet/`; `validate-pr-packet.sh` passed |
| Post: PR Creation | Complete | https://github.com/racecraft-lab/racecraft-plugins-public/pull/281 |
| Post: Review Remediation | Complete | RepoPrompt review findings remediated with fail-closed apply checks, fake-home boundary enforcement, deferred command-plan apply, schema contract tests, canonical phase-label tests, and refreshed verification |
| Post: Retrospective | Pending | Final post item before completion can be reported |

### Final Verification Targets

- [x] All tasks marked complete in `tasks.md`.
- [x] Python mutation-helper tests pass for accepted helper ports.
- [x] Bash-reference metadata is recorded; no Bash-backed helper is Python-authoritative in XPLAT-006.
- [x] Source-checkout mutation proof and path-boundary fixtures are recorded.
- [x] `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` passes.
- [x] `tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py` still passes.
- [x] `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"` passes.
- [x] `bash tests/speckit-pro/run-all.sh --layer 1` passes.
- [x] `bash tests/speckit-pro/run-all.sh --layer 4` passes.
- [x] `bash tests/speckit-pro/run-all.sh` passes with 3800/3800.
- [x] `python3 tests/speckit-pro/layer4-scripts/test-autopilot-phase-coverage.py` passes.
- [x] `python3 speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py --workflow docs/ai/specs/.process/XPLAT-006-workflow.md --state docs/ai/specs/.process/autopilot-state.json` passes.
- [x] No active Claude/Codex invocation-path, generated-payload
  selection/cutover, install behavior, public platform claim, repo-local Bash
  gate migration, or native matrix UAT changed; allowed phase-coverage
  hardening source/mirror changes are separately recorded.
- [x] PR packet includes review order, scope budget, parity evidence,
  per-helper gate-promotion state, known gaps, deferred live-mutation boundaries, rollback
  notes, and XPLAT-007/XPLAT-008 handoff.

---

## Project Structure Reference

```text
speckit-pro/
  speckit_pro_runner/             # XPLAT runner package and helper modules
  skills/**/scripts/              # Current Bash helper references
  codex-skills/**/scripts/        # Current Codex helper references
  scripts/                        # Current plugin helper references
tests/speckit-pro/
  layer1-structural/              # Structural validation
  layer4-scripts/                 # Script/helper tests and fixtures
  layer4-scripts/fixtures/read-only-helpers/
                                  # XPLAT-005 fixture and parity patterns
docs/ai/specs/.process/
  XPLAT-006-design-concept.md
  XPLAT-006-workflow.md
specs/xplat-006-mutation-install-pr-emission-helper-port/
  SPEC-MOC.md
  spec.md
  plan.md
  tasks.md
```

### PR packet validation events
- <!-- speckit-pro-pr-packet-validation:event-id=xplat-006-pr-packet --> Blocked PR packet validation for `xplat-006-pr-packet`; result `specs/xplat-006-mutation-install-pr-emission-helper-port/.process/pr-packets/xplat-006-pr-packet/validation.json`; rules: `unknown`.
- <!-- speckit-pro-pr-packet-validation:event-id=packet --> Blocked PR packet validation for `packet`; result `specs/xplat-006-mutation-install-pr-emission-helper-port/.process/pr-packets/packet/validation.json`; rules: `unknown`.
