# SpecKit Workflow: XPLAT-005 - Read-Only Helper Port

**Template Version**: 1.0.0
**Created**: 2026-07-01
**Purpose**: Prepare XPLAT-005 for autonomous execution from the cross-platform plugin runtime roadmap and the setup Grill Me decisions.

---

## How to Use This Workflow

Run this workflow from the XPLAT-005 worktree:

```text
$speckit-autopilot docs/ai/specs/.process/XPLAT-005-workflow.md
```

This file is already populated for XPLAT-005. Do not replace it with the
generic workflow template.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`$speckit-scaffold-spec XPLAT-005`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/XPLAT-005-design-concept.md
```

Re-read it before each phase. The design concept is the source of truth for the
accepted scope:

- One XPLAT-005 workflow with two internal implementation slices.
- Prerequisite/status helpers first, then planning/index/topology validators and
  late read-only PR-packet validation.
- Deterministic golden fixtures plus source-checkout Bash-reference comparisons
  before accepting Python output.
- No active Claude Code or Codex skill, hook, generated payload, install, or
  public documentation cutover.
- Python tests become authoritative per helper only after parity is accepted.
- Add local macOS source-checkout smoke evidence, but leave installed-cache and
  full native matrix UAT to XPLAT-007.
- Establish a small helper registry plus per-helper modules for later XPLAT-006
  reuse.

> Grill Me is human-in-the-loop only. It is not part of the autopilot loop.
> Once this workflow begins, clarifications happen via `$speckit-clarify` and
> consensus, never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|---|---|---|---|
| Specify | `$speckit-specify` | Complete | Created the read-only helper port spec and requirements checklist; G1 passed |
| Clarify | `$speckit-clarify` | Complete | Resolved helper grouping, parity comparison, gate promotion, read-only mixed-mode boundaries, and macOS smoke scope |
| Plan | `$speckit-plan` | Complete | Produced the two-slice architecture, helper registry plan, parity contracts, promotion matrix, and test strategy |
| Checklist | `$speckit-checklist` | Complete | Ran integration, error-handling, reliability, and security checklists; remediated all six true gaps |
| Tasks | `$speckit-tasks` | Complete | Generated 85 ordered tasks across the accepted two slices with 5 parallel-safe setup fixture tasks |
| Analyze | `$speckit-analyze` | Complete | Remediated metadata and scope-audit drift; G6 passed with no remaining findings |
| Implement | `$speckit-implement` | Complete | Ported helpers, tests, parity fixtures, metadata, and source-checkout smoke evidence |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|---|---|---|
| G1 | After Specify | Scope is read-only helper porting only; no active cutover, mutation helpers, or public support claims |
| G2 | After Clarify | Helper grouping, parity bar, `validate-pr-packet` boundary, gate promotion, and macOS smoke scope are unambiguous |
| G3 | After Plan | Plan records the reviewability warning, two-slice strategy, helper registry shape, and source-checkout proof boundary |
| G4 | After Checklist | All true integration, error-handling, reliability, and security gaps are remediated or explicitly out of scope |
| G5 | After Tasks | Tasks map to the accepted two slices and avoid mutation/helper cutover scope |
| G6 | After Analyze | No critical drift remains between roadmap, design concept, spec, plan, tasks, and XPLAT-004 runner contract |
| G7 | After Implementation | Python helper tests, golden fixtures, Bash-reference comparisons, local macOS smoke, spec-index check, diff hygiene, and relevant repo gates pass |

---

## Prerequisites

### Worktree and Branch

- Worktree: `.worktrees/xplat-005-read-only-helper-port`
- Branch: `codex/xplat-005-read-only-helper-port`
- Contract marker: `specs/xplat-005-read-only-helper-port/SPEC-MOC.md`
- Design concept: `docs/ai/specs/.process/XPLAT-005-design-concept.md`
- Workflow: `docs/ai/specs/.process/XPLAT-005-workflow.md`

Expected branch is `codex/xplat-005-read-only-helper-port`. Preset resolution
should use `.specify/presets/speckit-pro-reviewability/` unless a deliberate
higher-priority override exists.

### Grounded Source Truth

- Roadmap: `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
- Roadmap MOC: `docs/ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md`
- Product requirement: `docs/prd-cross-platform-plugin-runtime.md`
- Runtime inventory: `docs/ai/research/cross-platform-runtime-inventory.md`
- XPLAT-004 archive report: `.specify/memory/archive-reports/2026-07-01-xplat-004-post-merge-hygiene.md`
- XPLAT-004 runner package: `speckit-pro/speckit_pro_runner/`
- XPLAT-004 runner tests and fixtures: `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` and `tests/speckit-pro/layer4-scripts/fixtures/speckit-pro-runner/`
- Current Bash helper sources: `speckit-pro/skills/**/scripts/`, `speckit-pro/codex-skills/**/scripts/`, and `speckit-pro/scripts/`
- Current deterministic shell gates: `tests/speckit-pro/run-all.sh`, `tests/speckit-pro/layer1-structural/`, and `tests/speckit-pro/layer4-scripts/`
- Project constitution: `.specify/memory/constitution.md`
- Design concept source: `docs/ai/specs/.process/XPLAT-005-design-concept.md`

### Phase 0 Preflight Results

| Check | Result | Evidence |
|---|---|---|
| Codex agent install | Pass | `validate-agent-install.sh --surface codex --autoheal` reported `ok: codex: 10 bundled agents installed` |
| SpecKit CLI | Pass | `command -v specify` resolved to an installed local executable |
| Remote | Pass | `git remote -v` detected `origin` |
| Branch/worktree | Pass | Created worktree on `codex/xplat-005-read-only-helper-port` from `origin/main` at `9f5a32ae` |
| Reviewability setup gate | Warn/pass | `reviewability-gate.sh setup docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md` returned `status: warn`, `pass: true`, `reviewable_loc: 250`, `production_files: 4`, `total_files: 10`, warning: primary surfaces `docs/process` and `harness/adapter` exceed one-surface warning threshold |
| Grill Me | Complete | 8 picker questions; accepted two internal slices, prereq/status first, golden fixtures plus Bash comparison, no active cutover, late read-only `validate-pr-packet`, per-helper gate promotion after parity, local macOS source-checkout smoke, and registry plus modules |
| Preset resolution | Pass | `specify preset resolve spec-template`, `plan-template`, and `tasks-template` resolve to `speckit-pro-reviewability v1.0.0` |

### Constitution Validation

| Principle | XPLAT-005 Requirement | Verification |
|---|---|---|
| Plugin Structure Compliance | New runner helper ports stay inside the `speckit-pro/` plugin and preserve manifest validity | Layer 1 structural validation and manifest review |
| Script Safety | Do not introduce new Bash, PowerShell, `jq`, shell parsing, or shell-only helper logic as the replacement runtime | Code review, Python helper tests, Bash-reference parity, and source scans |
| Semantic Versioning | Do not edit plugin versions manually | Diff review |
| Test Coverage Before Merge | Add Python standard-library tests and fixture parity for each accepted read-only helper before promotion | Focused Python helper tests, Layer 4, Layer 1, and full deterministic suite before PR |
| Conventional Commits | Setup and implementation commits use conventional commit format | Commit and PR title review |
| KISS, Simplicity, YAGNI | Add a small helper registry plus per-helper modules; avoid a generic framework | Plan complexity table and G6 analysis |

---

## Specification Context

### Basic Information

| Field | Value |
|---|---|
| **Spec ID** | XPLAT-005 |
| **Name** | Read-Only Helper Port |
| **Branch** | `codex/xplat-005-read-only-helper-port` |
| **Feature directory** | `specs/xplat-005-read-only-helper-port` |
| **Dependencies** | XPLAT-004 complete/archived; Python 3.11+ runner foundation exists under `speckit-pro/speckit_pro_runner/` |
| **Enables** | XPLAT-007 and reduces XPLAT-006 risk |
| **Priority** | P1 |

### Success Criteria Summary

- [x] All accepted read-only helpers have runner equivalents with fixture parity.
- [x] Python helper outputs preserve current JSON stdout schemas, stderr diagnostics, and documented exit-code behavior.
- [x] Bash-reference comparisons pass for helpers where current behavior is deterministic enough to compare.
- [x] Windows-style path fixtures and no-Bash behavior are covered without requiring native Windows UAT.
- [x] A local macOS source-checkout smoke proves the accepted runner/helper path without installed-cache or public support claims.
- [x] Python tests become authoritative for each helper only after parity is accepted; Bash helpers remain temporary references until XPLAT-007.
- [x] No active Claude/Codex invocation, generated payload, install behavior, or public documentation claim is switched in this spec.

### Accepted Two-Slice Plan

| Slice | Scope | Explicit Boundary |
|---|---|---|
| Slice 1 | Helper registry/dispatch shape plus prerequisite, detection, marker, validation, and confidence helpers | No planning/index/topology helpers until the foundational port pattern and parity harness are accepted |
| Slice 2 | Spec-index, topology, atomicity/layer-planning, workflow-contract validation, and late read-only `validate-pr-packet` | No PR body generation, PR emission, split state, restack mutation, install repair, active cutover, or public claims |

---

## Phase 1: Specify

**When to run:** At the start of XPLAT-005. Focus on what the read-only helper
ports must preserve and what cutover is deliberately deferred. Output:
`specs/xplat-005-read-only-helper-port/spec.md`.

### Specify Prompt

```text
$speckit-specify

## Feature: Read-Only Helper Port

### Problem Statement
SpecKit Pro now has a Python 3.11+ standard-library runner foundation from
XPLAT-004, but the active read-only and advisory helper behavior is still
implemented through Bash helpers, shell parsing, and in some cases `jq`,
`grep`, `sed`, arrays, process substitution, and Unix-path assumptions. Before
mutation helpers or active Claude/Codex cutover can proceed, XPLAT-005 must port
the read-only helper surface to the runner with fixture parity and stable tests.

### Users
- Maintainers who need read-only helper behavior to work without Bash as the
  long-term implementation substrate.
- XPLAT-006 implementers who need a small shared registry/dispatch pattern and
  per-helper module convention for mutation helper ports.
- XPLAT-007 release reviewers who need proof that read-only helper gates can run
  through Python standard-library tests before active cutover.

### User Stories
1. As a maintainer, I can run Python runner equivalents for prerequisite,
   detection, marker, validation, confidence, index, topology, and planning
   helpers and receive the same JSON, diagnostic, and exit semantics as the
   current helpers.
2. As a helper-port implementer, I can add a read-only helper through a small
   registry plus per-helper module pattern and prove parity through golden
   fixtures and Bash-reference comparisons.
3. As a release reviewer, I can see which helpers have been promoted to Python
   release gates, which Bash helpers remain temporary references, and why no
   active Claude/Codex cutover or platform support claim happened in XPLAT-005.

### Constraints
- Follow the design concept decisions in
  `docs/ai/specs/.process/XPLAT-005-design-concept.md`.
- Use Python 3.11+ standard library only for new runner helper logic; no new
  runtime dependency, `jq`, Bash, PowerShell, Node, Go, Rust, Zig, package
  install, or virtualenv restore.
- Preserve current stdout JSON schemas, stderr diagnostics, and documented exit
  codes for each ported helper.
- Use deterministic golden fixtures plus source-checkout Bash-reference
  comparisons before accepting Python output.
- Promote Python tests as authoritative per helper only after parity is
  accepted.
- Add local macOS source-checkout smoke evidence without claiming installed
  plugin or native matrix support.
- Keep one workflow with two internal slices unless planning proves the scope is
  not reviewable.

### Out of Scope
- Active Claude Code or Codex skill, hook, generated payload, install, or public
  documentation cutover.
- Mutation helpers that write files, install agents, generate PR bodies, emit
  split PR state, perform restack changes, relocate artifacts, or mutate
  repository/user-local state.
- Full native Windows/macOS/Linux installed-plugin UAT.
- Removing Bash helpers globally before XPLAT-007.
- Public native-platform support claims.
```

### Specify Results

| Metric | Value |
|---|---|
| Functional Requirements | 22 |
| User Stories | 3 |
| Acceptance Criteria | 10 |

### Files Generated

- [x] `specs/xplat-005-read-only-helper-port/spec.md`
- [x] `specs/xplat-005-read-only-helper-port/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** After Specify, if any helper grouping, parity, or gate-promotion
boundary remains ambiguous. Use the design concept open questions first.

### Clarify Prompts

#### Session 1: Slice and Helper Grouping

```text
$speckit-clarify Focus on the exact Slice 1 and Slice 2 helper groups: confirm which prerequisite, detection, marker, validation, confidence, index, topology, atomicity, layer-planning, workflow-contract, and PR-packet validation helpers belong in each slice; keep all mutation helpers out of scope.
```

#### Session 2: Parity and Gate Promotion

```text
$speckit-clarify Focus on parity proof and gate promotion: decide which helpers require Bash-reference comparison, which fixtures are golden-only, how environment-sensitive fields are normalized, and how the workflow records when Python tests become authoritative per helper.
```

#### Session 3: Platform Smoke and Cutover Boundary

```text
$speckit-clarify Focus on local macOS source-checkout smoke and cutover boundaries: define the smallest smoke command, what it proves, what it does not prove, and how the spec prevents active Claude/Codex invocation, generated payload, install, or public support-claim changes.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---|---|---|---|
| 1 | Slice and helper grouping | 5 | Slice 1 includes registry/dispatch, prerequisite/detection/marker/validation/reviewability/confidence helpers; Slice 2 includes `generate-spec-index --check`, topology, atomicity, layer-planning, workflow-contract validation, and late read-only PR-packet validation; `detect-stack-manager`, write/regenerate modes, marker-plan output, and persistence writes are deferred |
| 2 | Parity and gate promotion | 5 | Every promoted Bash-backed helper requires golden fixtures plus source-checkout Bash comparison; golden-only fixtures are limited to runner/synthetic safety cases; normalization is allowlisted; promotion uses a per-helper matrix |
| 3 | Platform smoke and cutover boundary | 4 | Smallest smoke is `runtime-info` through the source-checkout runner; it proves local source-checkout launch/envelope/metadata only and does not prove installed-cache launch, helper parity, active cutover, mutation safety, or native matrix support |

### Clarify Consensus

| Item | Resolution | Evidence |
|---|---|---|
| `generate-spec-index` write mode | XPLAT-005 ports only read-only `--check` parity; default write/regenerate behavior is deferred because it mutates `SPEC-MOC.md` artifacts | Codebase and spec-context consensus agreed with high confidence |
| `validate-pr-packet` persistence writes | XPLAT-005 ports only read-only validation output, diagnostics, and exit-code parity; validation-result files and workflow-event upserts remain out of scope | Codebase and spec-context consensus agreed with high confidence |

---

## Phase 3: Plan

**When to run:** After the spec is finalized. Generate the technical
implementation blueprint. Output: `specs/xplat-005-read-only-helper-port/plan.md`.

### Plan Prompt

```text
$speckit-plan

## Tech Stack
- Runtime: Python 3.11+ standard library through the XPLAT-004 runner package
  under `speckit-pro/speckit_pro_runner/`.
- Existing reference implementations: Bash helpers under
  `speckit-pro/skills/**/scripts/`, `speckit-pro/codex-skills/**/scripts/`, and
  `speckit-pro/scripts/`.
- Tests: Python standard-library helper tests plus existing shell-layer gates
  during migration.
- Docs/process: SpecKit CONTRACT artifacts under
  `specs/xplat-005-read-only-helper-port/` and EXHAUST artifacts under
  `docs/ai/specs/.process/`.
- Generated payloads: Out of scope for XPLAT-005.

## Constraints
- Record the setup reviewability warning: `status=warn`, `pass=true`, two
  primary surfaces (`docs/process`, `harness/adapter`), no blockers.
- Implement as one workflow with two internal slices unless planning proves a
  split is required.
- Keep helper ports read-only. No writes to repository/user-local state except
  test fixtures and generated spec artifacts created by this workflow.
- Preserve current JSON stdout, stderr diagnostics, and exit-code semantics.
- Normalize environment-sensitive comparison fields before Bash-reference
  parity checks.
- Add local macOS source-checkout smoke only; installed-cache launch and full
  native matrix UAT remain XPLAT-007.

## Architecture Notes
- Reuse the XPLAT-004 runner envelope, diagnostics, typed path, and preflight
  primitives instead of inventing a parallel helper runtime.
- Add a small helper registry/dispatch pattern plus per-helper modules. Do not
  build a generic framework.
- Plan Slice 1 around foundational prereq/status helpers. Plan Slice 2 around
  planning/index/topology validators and late read-only PR-packet validation.
- Keep Bash helpers as temporary reference implementations until XPLAT-007.
- Reference `docs/ai/specs/.process/XPLAT-005-design-concept.md` for the
  accepted Grill Me decisions and non-goals.
```

### Plan Results

| Artifact | Status | Notes |
|---|---|---|
| `plan.md` | Complete | Technical context, declared file operations, reviewability warning, two-slice strategy, 16 in-scope helper/mode rows, and 4 out-of-scope rows |
| `research.md` | Complete | Runner reuse, registry, parity, normalization, two-slice, Bash-reference, and smoke decisions |
| `data-model.md` | Complete | Helper registry entries, invocation requests/results, fixtures, comparisons, normalization, promotion records, smoke evidence, and scope audit |
| `contracts/` | Complete | `read-only-helper-request.schema.json` and `helper-promotion-record.schema.json` |
| `quickstart.md` | Complete | Maintainer commands for source-checkout smoke, helper parity tests, Layer 4, deterministic gate, scope audit, and promotion evidence |

---

## Phase 4: Domain Checklists

**When to run:** After `$speckit-plan`, validate both the spec and plan. Run the
domains below because this work is cross-helper, parity-sensitive, and
release-gate-adjacent.

### Checklist Prompts

#### 1. Integration Checklist

```text
$speckit-checklist integration

Focus on XPLAT-005 requirements:
- XPLAT-004 runner envelope, diagnostics, typed path, preflight, and metadata reuse.
- Helper registry plus per-helper module integration.
- Bash-reference comparison harnesses and fixture locations.
- Slice 1 to Slice 2 handoff and XPLAT-006 handoff.
- Pay special attention to avoiding active Claude/Codex invocation, generated payload, install, or docs cutover.
```

#### 2. Error-Handling Checklist

```text
$speckit-checklist error-handling

Focus on XPLAT-005 requirements:
- Preservation of current helper exit codes, stdout JSON, and stderr diagnostics.
- Invalid input, missing input, malformed JSON, missing file, unsupported path, and prerequisite failures.
- Environment-sensitive output normalization for parity comparisons.
- Pay special attention to deterministic remediation text and nonzero exit mapping.
```

#### 3. Reliability Checklist

```text
$speckit-checklist reliability

Focus on XPLAT-005 requirements:
- Deterministic golden fixtures and Bash-reference comparisons.
- Per-helper promotion from Bash reference to Python authoritative gate.
- Local macOS source-checkout smoke command and repeatability.
- Pay special attention to tests that should not depend on network, installed-cache state, or mutable user-local state.
```

#### 4. Security Checklist

```text
$speckit-checklist security

Focus on XPLAT-005 requirements:
- No shell injection or shell=True subprocess behavior in new helper ports.
- Safe path handling for Windows-style paths, spaces, symlinks where relevant, and repo-root boundaries.
- No new dependency, package install, or supply-chain surface beyond Python standard library.
- Pay special attention to read-only guarantees and the boundary between validation helpers and mutation helpers.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|---|---|---|---|
| Integration | 24 | 0 | Runner foundation reuse, registry/module integration, parity harness, slice handoff, and cutover exclusions |
| Error-handling | 24 | 4 found, 4 remediated | Added rejected-input stdout schema, failure-class exit mapping, deterministic remediation, and per-class fixture requirements |
| Reliability | 20 | 0 | Deterministic parity evidence, promotion gates, source-checkout smoke repeatability, environment isolation, and regression boundaries |
| Security | 22 | 2 found, 2 remediated | Added argv-only subprocess policy and repo/plugin trust-boundary path requirements |

---

## Phase 5: Tasks

**When to run:** After checklists complete and all true gaps are resolved.
Output: `specs/xplat-005-read-only-helper-port/tasks.md`.

### Tasks Prompt

```text
$speckit-tasks

## Task Structure
- Organize by independently testable helper behavior and accepted slices.
- Write failing Python tests or fixtures before each helper port.
- Preserve Bash-reference comparison tasks before gate-promotion tasks.
- Mark parallel-safe tasks with [P] only when they touch independent helpers,
  fixtures, or docs and do not compete for shared registry or harness files.
- Reference `spec.md`, `plan.md`, and
  `docs/ai/specs/.process/XPLAT-005-design-concept.md`.

## Implementation Slices
1. Foundation and Slice 1: helper registry/dispatch, fixture harness,
   prerequisite/detection/marker/validation/confidence helpers, and parity proof.
2. Slice 2: spec-index, topology, atomicity/layer-planning,
   workflow-contract validation, read-only `validate-pr-packet`, local macOS
   source-checkout smoke, and handoff evidence.

## Constraints
- Do not generate PR bodies, emit split-PR state, install agents, relocate
  artifacts, or mutate repository/user-local state outside test fixtures and
  expected spec artifacts.
- Do not update active Claude/Codex invocations or generated payloads.
- Keep Python tests authoritative only after parity is accepted per helper.
- Keep the final task list reviewable; if task generation proves the work is too
  large, record the split point before implementation starts.
```

### Tasks Results

| Metric | Value |
|---|---|
| Total Tasks | 85 |
| Phases | 5 |
| Parallel Opportunities | 5 `[P]` setup fixture tasks only |
| User Stories Covered | US1: 47 tasks; US2: 6 tasks; US3: 24 tasks; setup/unlabeled: 7 tasks |

---

## Atomicity Route

This section is populated after the Tasks phase by the autopilot skill. The
classifier output is recorded here only; it does not create PRs or split
branches by itself.

| Field | Value | Meaning |
|---|---|---|
| Route | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope` |
| Releasable | `true` | `true`, or `false` for destructive/concurrency-sensitive work |
| Signals | `change-shape:modify-heavy`; hint `hint:release-cadence:weak` | Detector findings behind the route |
| Warnings | None | Release-safety warnings |

Classifier command:

```text
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/xplat-005-read-only-helper-port
```

---

## Phase 6: Analyze

**When to run:** Always run after tasks to catch drift and coverage gaps before
implementation.

### Analyze Prompt

```text
$speckit-analyze

Focus on:
1. Drift between the roadmap, XPLAT-005 design concept, spec.md, plan.md, and tasks.md.
2. Scope leakage into mutation helpers, active Claude/Codex cutover, generated payloads, install behavior, or public platform claims.
3. Coverage of each accepted read-only helper group, parity fixture, Bash-reference comparison, and per-helper gate-promotion rule.
4. Consistency with XPLAT-004 runner envelope, diagnostics, typed paths, preflight, checksum/manifest metadata, and Python standard-library boundary.
5. Reviewability risk: verify the two-slice task plan remains reviewable or records a concrete split before implementation starts.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|---|---|---|---|
| A1 | HIGH | Runner source files were planned without runner manifest/checksum metadata updates | Added `FR-028`, `SC-007`, metadata file operations, metadata verification, and task T077 |
| A2 | MEDIUM | Final scope audit did not explicitly cover generated payload directories and related active surfaces | Expanded final scope audit task to cover `dist/claude/speckit-pro/`, `dist/codex/speckit-pro/`, agents, hooks, `.agents/`, scripts, and related surfaces |

---

## Phase 7: Implement

**When to run:** After tasks are generated and analyzed with no blocking
coverage gaps.

### Implement Prompt

```text
$speckit-implement

## Approach: Test and Parity First

For each helper or helper group:
1. RED: Add the golden fixture and Python test that defines expected output,
   diagnostics, and exit behavior.
2. REFERENCE: Add or update the source-checkout Bash-reference comparison when
   current Bash behavior is deterministic enough to compare.
3. GREEN: Implement the smallest Python runner helper module and registry entry
   that satisfies the fixture and comparison.
4. PROMOTE: Mark the Python test authoritative for that helper only after
   fixture and Bash-reference parity pass.
5. VERIFY: Run focused helper tests, Layer 4, Layer 1, spec-index check,
   diff hygiene, and the local macOS source-checkout smoke when available.

### Pre-Implementation Setup

1. Verify branch: `git rev-parse --abbrev-ref HEAD` should return
   `codex/xplat-005-read-only-helper-port`.
2. Verify clean worktree before each phase: `git status --short`.
3. Run current baseline gates before helper changes:
   - `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"`
   - `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh`
   - `bash tests/speckit-pro/run-all.sh --layer 1`
   - `bash tests/speckit-pro/run-all.sh --layer 4`

### Implementation Notes

- Prefer structured parsing and Python standard-library APIs over shell-output
  string manipulation.
- Keep helper modules small and explicit. Do not build a generic framework.
- Normalize volatile paths, timestamps, platform names, and environment-specific
  fields in parity comparisons before asserting equality.
- Keep Bash helpers available as references until XPLAT-007 removes or archives
  them.
- Do not update active skill text, hook config, generated payloads, install docs,
  or public support claims in this spec.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|---|---|---|---|
| Foundation and Slice 1 | 51 | 51 | Registry/dispatch plus prerequisite, detection, marker, validation, reviewability, and confidence helpers implemented and covered |
| Slice 2 | 25 | 25 | Spec-index, topology, atomicity, layer-planning, workflow-contract, and read-only PR-packet helper paths implemented and covered |
| Smoke and Handoff | 9 | 9 | Local source-checkout smoke, metadata refresh, diff hygiene, default suite, and XPLAT-006/XPLAT-007 handoff evidence completed |

---

## Post-Implementation Checklist

- [x] All tasks marked complete in `tasks.md`.
- [x] Python helper tests pass for accepted helper ports.
- [x] Bash-reference comparison passes for helpers requiring direct comparison.
- [x] `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh` passes.
- [x] `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"` passes.
- [x] `bash tests/speckit-pro/run-all.sh --layer 1` passes.
- [x] `bash tests/speckit-pro/run-all.sh --layer 4` passes.
- [x] Local macOS source-checkout smoke evidence is recorded.
- [x] No active Claude/Codex invocation, generated payload, install behavior, or
  public platform claim changed.
- [x] PR packet includes review order, scope budget, parity evidence,
  per-helper gate-promotion state, known gaps, rollback notes, and XPLAT-006/
  XPLAT-007 handoff.

### Final Verification Evidence

Recorded `2026-07-02T16:59:00Z`:

- `bash tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.sh` -> `7/7 passed`
- `bash tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh` -> `9/9 passed`
- `speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh G5 specs/xplat-005-read-only-helper-port` -> `pass: true`, `task_count: 85`
- `speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh G7 specs/xplat-005-read-only-helper-port` -> `pass: true`, `done: 85`
- `bash tests/speckit-pro/run-all.sh --layer 4` -> `2108/2108 passed`
- `bash tests/speckit-pro/run-all.sh` -> `3751/3751 passed`

---

## Project Structure Reference

```text
speckit-pro/
  speckit_pro_runner/             # XPLAT runner package and new helper modules
  skills/**/scripts/              # Current Bash helper references
  codex-skills/**/scripts/        # Current Codex helper references
tests/speckit-pro/
  layer1-structural/              # Structural validation
  layer4-scripts/                 # Script/helper tests and fixtures
docs/ai/specs/.process/
  XPLAT-005-design-concept.md
  XPLAT-005-workflow.md
specs/xplat-005-read-only-helper-port/
  SPEC-MOC.md
  spec.md
  plan.md
  tasks.md
```

### PR packet validation events
- <!-- speckit-pro-pr-packet-validation:event-id=xplat-005-read-only-helper-port --> Blocked PR packet validation for `xplat-005-read-only-helper-port`; result `specs/xplat-005-read-only-helper-port/.process/pr-packets/xplat-005-read-only-helper-port/validation.json`; rules: `unknown`.
