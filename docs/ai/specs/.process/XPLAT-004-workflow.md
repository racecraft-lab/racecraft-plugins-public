# SpecKit Workflow: XPLAT-004 - Cross-Platform Runner Foundation

**Template Version**: 1.0.0
**Created**: 2026-06-30
**Purpose**: Prepare and execute XPLAT-004 from the cross-platform plugin runtime roadmap with the Grill Me decisions captured in `docs/ai/specs/.process/XPLAT-004-design-concept.md`.

---

## How to Use This Workflow

Run this workflow from the XPLAT-004 worktree:

```text
$speckit-autopilot docs/ai/specs/.process/XPLAT-004-workflow.md
```

This file is already populated for XPLAT-004. Do not replace it with the generic workflow template.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during `$speckit-scaffold-spec XPLAT-004`. The full Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/XPLAT-004-design-concept.md
```

Re-read it before each phase. The design concept is the source of truth for the accepted scope:

- Preflight-only runner foundation; no real helper ports.
- Small Python stdlib package with module-style invocation.
- Contract fixture parity, not `generate-spec-index.sh` or broader helper parity.
- Local macOS proof plus deterministic Windows/Linux runbook fixtures; full native matrix UAT remains XPLAT-007.
- Source runner files plus checksum/manifest metadata; generated payload propagation and active cutover remain XPLAT-007.
- Fail-closed Python 3.11+ and `specify` preflight.
- Runner unit/contract fixture tests only.
- Runner identity/preflight plus checksum and manifest controls.
- Accepted two-slice plan inside one XPLAT-004 workflow, not child specs.

> **Note:** Grill Me is human-in-the-loop only. It is not part of the autopilot loop. Once this workflow begins, clarifications happen via `$speckit-clarify` and the consensus protocol, never via `$grill-me`.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|---|---|---|---|
| Specify | `$speckit-specify` | Complete | Created runner-foundation spec and requirements checklist; G1 passed with zero clarification markers |
| Clarify | `$speckit-clarify` | Complete | G2 passed after package naming, fixture matrix, metadata, and claim-boundary decisions |
| Plan | `$speckit-plan` | Complete | Created small-package architecture, two-slice plan, contracts, data model, research, and quickstart; G3 passed |
| Checklist | `$speckit-checklist` | Complete | Integration, error-handling, security, and reliability checklists complete; G4 passed with zero gap markers |
| Tasks | `$speckit-tasks` | Complete | Generated 47 tasks across two implementation slices; G5 passed |
| Analyze | `$speckit-analyze` | Complete | Found and remediated roadmap/design-concept drift; G6 passed |
| Implement | `$speckit-implement` | Complete | Runner foundation, contract fixtures, metadata, and runbook fixture evidence implemented; G7 passed |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|---|---|---|
| G1 | After Specify | Scope is runner foundation only; no real helper ports, generated payload cutover, or public native-platform claims |
| G2 | After Clarify | Package/module naming, fixture parity matrix, fail-closed preflight, and metadata ownership are unambiguous |
| G3 | After Plan | Plan records the accepted reviewability warning and two-slice implementation strategy |
| G4 | After Checklist | All true integration, error-handling, security, and reliability gaps are remediated or explicitly out of scope |
| G5 | After Tasks | Tasks map to the two accepted slices and avoid XPLAT-005/XPLAT-006/XPLAT-007 behavior |
| G6 | After Analyze | No critical drift remains between roadmap, design concept, spec, plan, and tasks |
| G7 | After Implementation | Runner tests, contract fixtures, spec-index check, diff hygiene, and relevant repo gates pass |

---

## Prerequisites

### Worktree and Branch

- Worktree: `.worktrees/xplat-004-cross-platform-runner-foundation`
- Branch: `codex/xplat-004-cross-platform-runner-foundation`
- Contract marker: `specs/xplat-004-cross-platform-runner-foundation/SPEC-MOC.md`
- Design concept: `docs/ai/specs/.process/XPLAT-004-design-concept.md`
- Workflow: `docs/ai/specs/.process/XPLAT-004-workflow.md`

Expected branch is `codex/xplat-004-cross-platform-runner-foundation`. Preset resolution should use `.specify/presets/speckit-pro-reviewability/` unless a deliberate higher-priority override exists.

### Grounded Source Truth

- Roadmap: `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
- Product requirement: `docs/prd-cross-platform-plugin-runtime.md`
- Runtime inventory: `docs/ai/research/cross-platform-runtime-inventory.md`
- XPLAT-003 archive report: `.specify/memory/archive-reports/2026-06-29-xplat-003-post-merge-hygiene.md`
- Completed XPLAT-001/XPLAT-002 archive report: `.specify/memory/archive-reports/2026-06-29-completed-active-specs-post-merge-hygiene.md`
- Project constitution: `.specify/memory/constitution.md`
- Design concept source: `docs/ai/specs/.process/XPLAT-004-design-concept.md`

### Phase 0 Preflight Results

| Check | Result | Evidence |
|---|---|---|
| Codex agent install | Pass | `validate-agent-install.sh --surface codex --autoheal` reported `ok: codex: 10 bundled agents installed` |
| SpecKit CLI | Pass | `command -v specify` resolved to a local `specify` executable |
| Remote | Pass | `git remote -v` detected `origin` |
| Branch/worktree | Pass | Created worktree on `codex/xplat-004-cross-platform-runner-foundation` from `origin/main` |
| Reviewability setup gate | Warn/pass | `reviewability-gate.sh setup docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md` returned `status: warn`, `pass: true`, `reviewable_loc: 250`, `production_files: 4`, `total_files: 10`, warning: primary surfaces `docs/process` and `harness/adapter` exceed one-surface warning threshold |
| Grill Me | Complete | 11 picker questions; accepted preflight-only scope and two planned PR slices inside one workflow |
| Size estimate | Warn/advisory | `estimate-spec-size.sh --user-stories 3 --files 6 --frs 7 --new-vs-modify new` returned `estimated_loc: 420`, `suggested_slices: 2`, `status: warn`; user accepted a two-slice plan |
| Preset resolution | Pass | `specify preset resolve spec-template`, `plan-template`, and `tasks-template` resolve to `speckit-pro-reviewability v1.0.0` |

### Constitution Validation

| Principle | XPLAT-004 Requirement | Verification |
|---|---|---|
| Plugin Structure Compliance | New runner source and metadata stay inside the `speckit-pro/` plugin and preserve manifest validity | Layer 1 structural validation and manifest review |
| Script Safety | Do not introduce Bash, PowerShell, `jq`, or shell helper logic as the new runtime substrate | Code review, runner contract tests, and source scan |
| Semantic Versioning | Do not edit plugin versions manually | Diff review |
| Test Coverage Before Merge | Add Python stdlib runner unit/contract fixture tests and run relevant deterministic repo gates | Runner test command, Layer 1, focused Layer 4 if affected, and full deterministic suite before PR |
| Conventional Commits | Setup and implementation commits use conventional commit format | Commit and PR title review |
| KISS, Simplicity & YAGNI | Keep the package small, avoid speculative adapters, and defer real helper ports | Plan complexity table and G6 cross-artifact analysis |

---

## Specification Context

### Basic Information

| Field | Value |
|---|---|
| **Spec ID** | XPLAT-004 |
| **Name** | Cross-Platform Runner Foundation |
| **Branch** | `codex/xplat-004-cross-platform-runner-foundation` |
| **Feature directory** | `specs/xplat-004-cross-platform-runner-foundation` |
| **Dependencies** | XPLAT-002 and XPLAT-003 complete/archived; current runtime decision is Python 3.11+ stdlib |
| **Enables** | XPLAT-005, XPLAT-006, XPLAT-007 |
| **Priority** | P1 |

### Success Criteria Summary

- [ ] Python stdlib runner core can process a versioned JSON request and emit one JSON stdout response plus line-delimited JSON stderr diagnostics.
- [ ] Runtime-info/preflight reports platform, architecture, plugin root, Python 3.11+ status, `specify` status, runner identity, and metadata pointers.
- [ ] Missing Python 3.11+, missing `specify`, invalid JSON, missing fields, subprocess failure, and internal failure all fail closed with deterministic statuses and exit codes.
- [ ] Contract fixtures cover envelope validation, typed paths, path-with-spaces behavior, Windows separator behavior, subprocess records, and preflight.
- [ ] Runner source checksum and manifest metadata exist for source runner files.
- [ ] A Python stdlib test entrypoint exists for runner unit/contract fixtures.
- [ ] No active skill, hook, generated payload, or public docs claim is switched to the runner in this spec.
- [ ] Implementation is delivered as two planned PR slices inside one XPLAT-004 workflow.

### Accepted Two-Slice Plan

| Slice | Scope | Explicit Boundary |
|---|---|---|
| Slice 1 | Small Python package, module-style entrypoint, JSON envelope, path/subprocess primitives, runtime-info/preflight, fail-closed prerequisite handling, and runner unit tests | No real helper ports; no generated payload propagation |
| Slice 2 | Contract fixture parity harness, checksum file, manifest file, metadata validation, runbook fixtures for Windows/Linux, and maintainer invocation notes | No active Claude/Codex cutover; no public claims; no repo-wide Bash gate replacement |

---

## Phase 1: Specify

**When to run:** At the start of XPLAT-004. Focus on what the runner foundation must provide and what it must not port. Output: `specs/xplat-004-cross-platform-runner-foundation/spec.md`.

### Specify Prompt

```text
$speckit-specify

## Feature: Cross-Platform Runner Foundation

### Problem Statement
SpecKit Pro installed Claude Code and Codex workflows still depend on Bash-backed helpers, `jq`, shell quoting, Unix paths, and shell-specific behavior. XPLAT-001 mapped active runtime assumptions, XPLAT-002 defined the durable runner command envelope, and XPLAT-003 amended the selected implementation substrate to Python 3.11+ standard-library source through the official Spec Kit / `specify` prerequisite boundary. XPLAT-004 must create the minimal runner foundation that later helper ports can safely build on.

### Users
- Maintainers who need a small, reviewable runner core before helper ports begin.
- XPLAT-005 and XPLAT-006 implementers who need stable JSON, path, subprocess, preflight, and test-fixture primitives.
- Release reviewers who need source integrity metadata and clear proof boundaries before XPLAT-007 cutover.

### User Stories
1. As a maintainer, I can run a Python stdlib runner preflight and receive structured JSON describing runtime, platform, plugin root, prerequisites, runner identity, and metadata pointers.
2. As a helper-port implementer, I can use contract fixtures for envelope validation, typed paths, subprocess behavior, and diagnostics before porting real helpers.
3. As a release reviewer, I can inspect runner source checksum and manifest metadata without treating XPLAT-004 as public native-platform support.

### Constraints
- Follow the design concept decisions in `docs/ai/specs/.process/XPLAT-004-design-concept.md`.
- Use Python 3.11+ standard library only; no package installation, no virtualenv restore, no Node, no Go/Rust/Zig/native binary runner, no Bash/PowerShell helper logic, no `jq`.
- Implement module-style invocation through discovered Python 3.11+ and JSON stdin/stdout.
- Fail closed when Python 3.11+ or `specify` is missing.
- Keep source under `speckit-pro/` and preserve plugin manifest validity.
- Record the two-slice plan and reviewability warning.

### Out of Scope
- Porting real helper behavior beyond runtime-info/preflight and contract smoke fixtures.
- Switching active Claude/Codex skills, hooks, generated payloads, or public docs to the runner.
- Copying runner files into `dist/**`.
- Replacing all Bash test/eval/release gates.
- Public native-platform support claims.
- Scan automation, release automation, signatures, SBOMs, provenance, reproducible builds, or formal audit.
```

### Specify Results

| Metric | Value |
|---|---|
| Functional Requirements | 14 |
| User Stories | 3 |
| Acceptance Criteria | 8 acceptance scenarios; 6 measurable success criteria |
| Requirements Checklist | 16/16 passed |
| Clarification Markers | 0 |
| Gate | G1 passed |

### Files Generated

- [x] `specs/xplat-004-cross-platform-runner-foundation/spec.md`
- [x] `specs/xplat-004-cross-platform-runner-foundation/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** After Specify, if any runner contract detail remains ambiguous. Use the design concept open questions first.

### Clarify Prompts

#### Session 1: Package and Entrypoint Shape

```text
$speckit-clarify Focus on package and entrypoint shape: exact source paths under speckit-pro, module invocation command, Python discovery order, payload-relative path conventions, and how tests invoke the runner without shell launchers.
```

#### Session 2: Contract Fixture Matrix

```text
$speckit-clarify Focus on contract fixture parity: invalid JSON, invalid envelope, unsupported schema version, missing fields, typed path values, paths with spaces, Windows separators, missing prerequisites, subprocess nonzero, subprocess timeout, stderr-only failure, and runtime-info/preflight response shape.
```

#### Session 3: Metadata and Claim Boundary

```text
$speckit-clarify Focus on runner metadata and claim boundaries: checksum file path, manifest fields, runner identity/preflight metadata pointers, source-only versus installed-cache context, what XPLAT-004 proves locally, and which generated payload and public-claim work remains XPLAT-007.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---|---|---|---|
| 1 | Package and entrypoint shape | 5 | Locked `speckit-pro/speckit_pro_runner/`, `<python> -m speckit_pro_runner`, Python 3.11+ discovery, `plugin_relative` source metadata, Python Layer 4 runner test entrypoint, and XPLAT-002 preflight/runtime-info envelope |
| 2 | Contract fixture matrix | 5 | Locked separate input-error fixtures, typed path object behavior, deterministic prerequisite simulation, distinct subprocess failure fixtures, and Python/source-checkout runtime-info shape |
| 3 | Metadata and claim boundary | 5 | Locked source-checkout metadata under `speckit-pro/speckit_pro_runner/`, source-file checksum coverage, split runner/contract/runtime identities, typed metadata pointers with checked verification status, and XPLAT-007 boundaries for payload propagation, installed-cache proof, native UAT, and public claim audit |

### Consensus Resolution Log

| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |
|---|---|---|---|---|---|---|---|
| 1 | Clarify | Runner source package path and module invocation | [codebase, spec] | 1 | both-agree | Use `speckit-pro/speckit_pro_runner/` with `<python> -m speckit_pro_runner`; avoid `speckit-pro/scripts/` because current payload build copies it into `dist/**` | codebase-analyst, spec-context-analyst |
| 2 | Clarify | Layer 4 runner test invocation without shell launchers | [codebase, spec] | 1 | both-agree | Keep `run-all.sh --layer 4` as outer gate, add a Python stdlib runner test entrypoint, and launch runner via argv + `shell=False` inside that test | codebase-analyst, spec-context-analyst |
| 3 | Clarify | Runtime-info/preflight shape after Python amendment | [spec] | 1 | high-confidence | Preserve XPLAT-002 envelope mechanics, use XPLAT-003 Python identity, and mark XPLAT-004 context as `source_checkout` with installed-cache proof deferred to XPLAT-007 | spec-context-analyst |
| 4 | Clarify | Source-checkout metadata file placement | [codebase, spec] | 1 | both-agree | Place `speckit-pro-runner.manifest.json` and `speckit-pro-runner.sha256` under `speckit-pro/speckit_pro_runner/`; treat archived `speckit-pro/scripts/` examples as stale for XPLAT-004 source layout | codebase-analyst, spec-context-analyst |
| 5 | Clarify | Runner identity split after module-invocation amendment | [codebase, spec] | 1 | both-agree | Use `runner_name: "speckit_pro_runner"`, `runner_contract_id: "speckit-pro-runner"`, and `selected_runtime_name: "python-stdlib-runner"` to preserve the durable contract while reflecting the Python module | codebase-analyst, spec-context-analyst |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/xplat-004-cross-platform-runner-foundation/plan.md`.

### Plan Prompt

```text
$speckit-plan

## Tech Stack and Runtime Context
- Existing plugin source is under `speckit-pro/`, with Claude source skills in `speckit-pro/skills/`, Codex source skills in `speckit-pro/codex-skills/`, and generated payloads under `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`.
- Current active helper runtime surfaces are Bash-backed scripts under `speckit-pro/skills/speckit-autopilot/scripts/` and generated payload mirrors. XPLAT-004 does not port these real helpers.
- Selected runtime boundary is Python 3.11+ standard-library source through official Spec Kit / `specify` prerequisites. This supersedes older native-binary wording in the archived XPLAT-002 contract.
- Durable command contract comes from XPLAT-002: versioned JSON stdin request, one versioned JSON stdout response, line-delimited JSON stderr diagnostics, typed paths, stable status/exit-code map, and shell-disabled subprocess records.
- XPLAT-003 adds runner identity/preflight metadata, checksum file, manifest file, source-only versus installed-cache context distinctions, and fail-closed prerequisite behavior.

## Constraints
- Follow `docs/ai/specs/.process/XPLAT-004-design-concept.md`.
- Keep implementation in two planned slices:
  1. Runner/preflight core.
  2. Contract fixture parity plus checksum/manifest metadata.
- Preserve the reviewability setup warning: primary surfaces are `docs/process` and `harness/adapter`.
- Use Python stdlib only and shell-disabled subprocess execution.
- Do not copy runner files into `dist/**`, do not switch active skills/hooks, and do not make public support claims.

## Architecture Notes
- Use the clarified small package under `speckit-pro/speckit_pro_runner/` with module-style invocation through discovered Python 3.11+.
- The runner core should own envelope parsing, response construction, diagnostics, typed path rendering, subprocess result records, prerequisite discovery, and preflight.
- The first helper surface is runtime-info/preflight plus contract smoke fixtures only.
- Checksum and manifest metadata should live under `speckit-pro/speckit_pro_runner/`, describe source runner files, and use `plugin_relative` source-checkout paths.
- Windows/Linux evidence in this spec is deterministic runbook/fixture guidance unless native hosts are available; XPLAT-007 owns full matrix UAT.

## Verification Strategy
- Python runner unit/contract fixture command for the new runner tests.
- `python3 -m json.tool` or equivalent stdlib validation for any manifest JSON.
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"`.
- `git diff --check`.
- Relevant focused Layer 1/Layer 4 checks when source or structural files change.
- Full deterministic suite before PR when feasible: `bash tests/speckit-pro/run-all.sh`.
```

### Plan Results

| Artifact | Status | Notes |
|---|---|---|
| `plan.md` | Complete | Records `speckit-pro/speckit_pro_runner/`, Python 3.11+ stdlib, accepted two-slice plan, reviewability warning, and deferred XPLAT-007 boundaries |
| `research.md` | Complete | Records package layout, runtime substrate, envelope ownership, preflight, metadata placement, fixture shape, and two-slice delivery decisions |
| `data-model.md` | Complete | Defines request/response envelopes, diagnostics, typed paths, preflight report, prerequisites, subprocess results, metadata manifest, and fixtures |
| `contracts/` | Complete | Added runner envelope and manifest JSON schemas |
| `quickstart.md` | Complete | Documents planned source-checkout invocation, tests, metadata validation, index/whitespace checks, and scope boundaries |

---

## Phase 4: Domain Checklists

**When to run:** After Plan. Use spec-specific checklist prompts.

### Recommended Domains

| Domain | Why |
|---|---|
| integration | Runner invocation bridges skills, installed payload roots, prerequisite discovery, and downstream helper-port expectations |
| error-handling | Fail-closed diagnostics and exit-code mapping are central to the runner contract |
| security | XPLAT-003 first-release controls require identity, checksum, manifest, and explicit non-claim boundaries |
| reliability | Platform preflight, metadata freshness, deterministic fixtures, and runbook proof must not overclaim readiness |

### Checklist Prompts

#### 1. Integration Checklist

```text
$speckit-checklist integration

Focus on XPLAT-004 requirements:
- Module-style Python invocation from source and future installed payload contexts.
- JSON stdin/stdout envelope compatibility with XPLAT-002.
- Plugin root detection and payload-relative runner file metadata.
- Boundaries that keep real helper ports in XPLAT-005/XPLAT-006 and generated payload cutover in XPLAT-007.
- Pay special attention to: whether downstream helper ports can use the runner contract without reopening package or invocation decisions.
```

#### 2. Error-Handling Checklist

```text
$speckit-checklist error-handling

Focus on XPLAT-004 requirements:
- Invalid JSON, invalid envelopes, unsupported schema versions, and missing fields.
- Missing Python 3.11+, missing `specify`, missing runner metadata, subprocess nonzero, timeout, and stderr-only failure categories.
- Deterministic stdout/stderr separation and exit-code mapping.
- Pay special attention to: fail-closed behavior with structured remediation when prerequisites are unavailable.
```

#### 3. Security Checklist

```text
$speckit-checklist security

Focus on XPLAT-004 requirements:
- Python stdlib-only dependency boundary.
- Runner identity, preflight, checksum file, and manifest metadata.
- Explicit exclusion of signatures, SBOMs, provenance, reproducible builds, formal audit, public support claims, and generated payload cutover.
- Pay special attention to: preventing source metadata from being described as public release readiness.
```

#### 4. Reliability Checklist

```text
$speckit-checklist reliability

Focus on XPLAT-004 requirements:
- Platform and architecture reporting.
- Deterministic contract fixtures for path separators, paths with spaces, subprocess records, and preflight.
- Local execution plus Windows/Linux runbook fixtures.
- Pay special attention to: avoiding false confidence when full native matrix UAT is deferred to XPLAT-007.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|---|---|---|---|
| integration | 20 | 0 current; 5 remediated | FR-002, FR-015, FR-016, FR-017, FR-018 |
| error-handling | 20 | 0 current; 7 remediated | FR-004, FR-005, FR-006, FR-008, FR-010, FR-019, FR-020 |
| security | 20 | 0 | FR-010, FR-012, FR-013 |
| reliability | 20 | 0 current; 3 remediated | FR-021, FR-022, SC-007 |

---

## Phase 5: Tasks

**When to run:** After checklists complete and all true gaps are resolved. Output: `specs/xplat-004-cross-platform-runner-foundation/tasks.md`.

### Tasks Prompt

```text
$speckit-tasks

## Task Structure
- Organize tasks by the accepted two-slice plan from `docs/ai/specs/.process/XPLAT-004-design-concept.md`.
- Keep each task small, testable, and traceable to user stories and functional requirements.
- Mark parallel-safe tasks with [P].
- Include tests before implementation where practical.

## Implementation Slices
1. Slice 1 - Runner/preflight core:
   - Small Python stdlib package and module-style entrypoint.
   - JSON request validation and response construction.
   - Line-delimited JSON diagnostics.
   - Typed path values and shell-disabled subprocess records.
   - Python 3.11+ and `specify` fail-closed preflight.
   - Runner unit tests.
2. Slice 2 - Contract parity and metadata:
   - Contract fixture parity harness for envelope, path, subprocess, and preflight cases.
   - Runner checksum file and manifest metadata.
   - Metadata validation tests.
   - Windows/Linux runbook fixture guidance.
   - Maintainer invocation notes.

## Constraints
- Do not port real helpers.
- Do not update active Claude/Codex skill invocation surfaces.
- Do not copy generated payloads into `dist/**`.
- Do not replace repo-wide Bash gates.
- Do not make public native-platform support claims.
- Keep XPLAT-005, XPLAT-006, and XPLAT-007 ownership clean.
```

### Tasks Results

| Metric | Value |
|---|---|
| Total Tasks | 47 |
| Phases/Slices | 8 task phases across 2 implementation slices |
| Parallel Opportunities | 6 task-level `[P]` markers; primary safe parallelism is Phase 1 setup plus runbook fixture population |
| User Stories Covered | 3/3 |

---

## Atomicity Route

After Tasks phase, run:

```text
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/xplat-004-cross-platform-runner-foundation
```

| Field | Value | Meaning |
|---|---|---|
| Route | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope` |
| Releasable | `true` | `true`, or `false` for release-risk classes |
| Signals | `change-shape:modify-heavy` | Decisive detector findings |
| Warnings | none | Release-safety warnings |

The Grill Me sizing branch already accepted two planned PR slices. The atomicity classifier still controls the final route after real tasks exist.

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch cross-artifact drift.

### Analyze Prompt

```text
$speckit-analyze

Focus on:
1. Cross-artifact consistency between `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`, `docs/ai/specs/.process/XPLAT-004-design-concept.md`, `spec.md`, `plan.md`, and `tasks.md`.
2. Scope boundaries: no real helper ports, no generated payload cutover, no active skill/hook cutover, no public support claims.
3. Reviewability: tasks preserve the accepted two-slice plan and address the setup warning.
4. Contract coverage: invalid input, diagnostics, exit codes, typed paths, subprocess records, preflight, checksum, and manifest behavior.
5. Downstream ownership: XPLAT-005, XPLAT-006, and XPLAT-007 remain cleanly unblocked without absorbing their work into XPLAT-004.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|---|---|---|---|
| A1 | High | Roadmap XPLAT-004 scope still described a broader shared runner, support library, and parity harness. | Narrowed roadmap scope to the minimal source-checkout Python runner foundation, `runtime-info`/`preflight`, synthetic contract fixtures, source metadata, and XPLAT-007 claim boundaries. |
| A2 | Medium | Design concept open questions still suggested `speckit-pro/scripts/` and deferred the fixture matrix after clarify/plan had already resolved both. | Replaced open-question next steps with resolution notes for `speckit-pro/speckit_pro_runner/`, `<python> -m speckit_pro_runner`, and the accepted fixture matrix. |

### Pre-Implement Confidence

📊 Confidence: 0.94

- Task understanding: 0.95
- Approach clarity: 0.94
- Requirements alignment: 0.96
- Risk assessment: 0.91
- Completeness: 0.94

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed with no blocking gaps.

### Implement Prompt

```text
$speckit-implement

## Approach: Foundation First
Implement the tasks from `specs/xplat-004-cross-platform-runner-foundation/tasks.md` in the accepted slice order. Re-read:
- `docs/ai/specs/.process/XPLAT-004-design-concept.md`
- `specs/xplat-004-cross-platform-runner-foundation/spec.md`
- `specs/xplat-004-cross-platform-runner-foundation/plan.md`
- `specs/xplat-004-cross-platform-runner-foundation/tasks.md`

### Pre-Implementation Setup
1. Verify branch: `codex/xplat-004-cross-platform-runner-foundation`.
2. Confirm preset resolution still uses `speckit-pro-reviewability`.
3. Run the existing deterministic baseline that is feasible before editing.

### Implementation Notes
- Prefer Python stdlib modules only.
- Keep subprocess calls shell-disabled with explicit argv arrays.
- Keep stdout to one JSON response; keep diagnostics as line-delimited JSON on stderr.
- Preserve typed path values across spaces and Windows/macOS/Linux separators.
- Keep checksum and manifest paths payload-relative.
- Document source-only context explicitly; do not imply generated payload or public release readiness.
```

### Implementation Progress

| Slice | Tasks | Completed | Notes |
|---|---|---|---|
| Slice 1 - Runner/preflight core | T001-T019 | Complete | Added `speckit-pro/speckit_pro_runner/`, module entrypoint, runtime-info/preflight, fail-closed diagnostics, and focused tests |
| Slice 2 - Contract parity and metadata | T020-T047 | Complete | Added contract fixtures, typed-path/subprocess primitives, manifest/checksum metadata, runbook fixture rows, no-cutover assertions, and review packet preparation |

---

## Post-Implementation Checklist

- [x] All tasks marked complete in `tasks.md`.
- [x] Runner unit/contract fixture tests pass.
- [x] Runner manifest JSON validates.
- [x] `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"` passes.
- [x] `git diff --check` passes.
- [x] Relevant Layer 1/Layer 4 checks pass when touched.
- [x] `bash tests/speckit-pro/run-all.sh` passes or any inability to run is recorded.
- [x] Final reviewability backstop passes or records accepted warnings with no blockers.
- [x] UAT runbook is generated and validated if the implementation reaches PR packet flow.
- [x] PR packet validates before PR creation.

### Post-Implementation Results

| Task | Status | Findings | Action Needed |
|---|---|---|---|
| Doctor Extension Check | Pass | Required scripts and repo gates are present; no extension blocker found | None |
| Verify Implementation | Pass | G7 reports 47/47 tasks complete; runner manifest JSON validates; spec index current; diff hygiene clean | None |
| Verify Tasks Phantom Check | Pass | No incomplete task markers remain; task heading repaired for canonical marker-plan compatibility | None |
| Code Review | Pass | Scope guard tightened so no-cutover assertion checks `origin/main...HEAD`; generated bytecode removed from tracking and ignored | None |
| Integration Suite | Pass | `bash tests/speckit-pro/run-all.sh` passed 3713/3713 from current head | None |
| Reviewability Diff Gate | Pass with exception | Final diff is size/file-count blocked but accepted through the branch-added typed `infra` reviewability exception; blocked operations are empty | Evidence: `specs/xplat-004-cross-platform-runner-foundation/.process/final-reviewability-state.json` |
| UAT Runbook Generation | Pass | Feature-local UAT runbook generated, authored with concrete XPLAT-004 checks, and validated | Evidence: `specs/xplat-004-cross-platform-runner-foundation/.process/uat-runbook.md` |
| PR Body Generation | Pass | Single-PR packet/body generated and validation passed | Evidence: `specs/xplat-004-cross-platform-runner-foundation/.process/pr-packets/xplat-004-runner-foundation/validation.json` |
| PR Creation | Pass | Opened PR #274 from `codex/xplat-004-cross-platform-runner-foundation` into `main` | https://github.com/racecraft-lab/racecraft-plugins-public/pull/274 |
| Review Remediation | Pass | Initial PR inspection found no comments and no reviews at creation time; checks were pending | None |
| Retrospective | Pass | Runner source metadata must be refreshed after any source-byte cleanup; final diff reviewability should be rerun after post packet commits | None |

---

## Self-Review

Before PR creation, record:

- **Tests executed:** `tests/speckit-pro/unit/test-speckit-pro-runner.sh` (9/9), `bash tests/speckit-pro/run-all.sh --layer 1` (1438/1438), `bash tests/speckit-pro/run-all.sh --layer 4` (2075/2075), `bash tests/speckit-pro/run-all.sh` (3713/3713), G7, spec-index check, branch-range `git diff --check`, UAT validation, PR packet validation, and PR workflow title validation.
- **Scope boundaries preserved:** No `dist/**` payload copy, active Claude/Codex skill or hook cutover, install behavior change, real helper port, or public native-platform support claim landed in XPLAT-004.
- **Known gaps:** Installed-cache launch proof, generated payload propagation, native matrix UAT, release-readiness, and public claim audit remain XPLAT-007.
- **Native Windows/Linux:** Not performed; XPLAT-004 provides deterministic source-checkout runbook fixture evidence only.
- **Review order:** Review the runner package and manifest/checksum first, then the Layer 4 runner tests and fixtures, then the spec/process evidence and PR packet.

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
speckit-pro/
  .claude-plugin/
  .codex-plugin/
  codex-skills/
  skills/
  skills/speckit-autopilot/scripts/
  scripts/
tests/speckit-pro/
  layer1-structural/
  unit/
  layer7-integration/
  layer8-parity/
docs/ai/specs/
  cross-platform-plugin-runtime-technical-roadmap.md
  .process/XPLAT-004-design-concept.md
  .process/XPLAT-004-workflow.md
specs/xplat-004-cross-platform-runner-foundation/
  SPEC-MOC.md
```

---

Template based on SpecKit best practices and populated for XPLAT-004 from the technical roadmap, XPLAT-001/XPLAT-002/XPLAT-003 archive evidence, current XPLAT-003 Python runtime boundary, and the setup Grill Me interview.
