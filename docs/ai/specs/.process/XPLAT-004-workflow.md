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
| Specify | `$speckit-specify` | Pending | Create the runner-foundation spec from the roadmap and design concept |
| Clarify | `$speckit-clarify` | Pending | Focus on package naming, fixture matrix, and metadata boundaries |
| Plan | `$speckit-plan` | Pending | Produce the small-package architecture, two-slice plan, and verification strategy |
| Checklist | `$speckit-checklist` | Pending | Recommended domains: integration, error-handling, security, reliability |
| Tasks | `$speckit-tasks` | Pending | Generate tasks grouped into the accepted two implementation slices |
| Analyze | `$speckit-analyze` | Pending | Check drift across roadmap, design concept, spec, plan, and tasks |
| Implement | `$speckit-implement` | Pending | Implement only runner foundation, contract fixtures, and metadata |

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
| SpecKit CLI | Pass | `command -v specify` resolved to `/Users/fredrickgabelmann/.local/bin/specify` |
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
| Functional Requirements | Pending |
| User Stories | 3 expected from setup |
| Acceptance Criteria | At least 8 roadmap/design-concept criteria |

### Files Generated

- [ ] `specs/xplat-004-cross-platform-runner-foundation/spec.md`
- [ ] `specs/xplat-004-cross-platform-runner-foundation/checklists/requirements.md`

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
| 1 | Package and entrypoint shape | Pending | |
| 2 | Contract fixture matrix | Pending | |
| 3 | Metadata and claim boundary | Pending | |

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
- Prefer a small package under `speckit-pro/scripts/` or another payload-relative source path that supports module-style invocation through discovered Python 3.11+.
- The runner core should own envelope parsing, response construction, diagnostics, typed path rendering, subprocess result records, prerequisite discovery, and preflight.
- The first helper surface is runtime-info/preflight plus contract smoke fixtures only.
- Checksum and manifest metadata should describe source runner files and remain payload-relative.
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
| `plan.md` | Pending | Must record small package, two-slice plan, and complexity tracking for any warning |
| `research.md` | Pending | Should record Python stdlib runner source layout and metadata decisions |
| `data-model.md` | Pending | Should define request/response, diagnostics, path values, prerequisites, and metadata records |
| `contracts/` | Pending | Should capture runner request/response/preflight/checksum/manifest contracts if useful |
| `quickstart.md` | Pending | Should give maintainer runner invocation and verification path |

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
| integration | Pending | Pending | |
| error-handling | Pending | Pending | |
| security | Pending | Pending | |
| reliability | Pending | Pending | |

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
| Total Tasks | Pending |
| Phases/Slices | 2 implementation slices expected |
| Parallel Opportunities | Pending |
| User Stories Covered | 3 expected |

---

## Atomicity Route

After Tasks phase, run:

```text
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/xplat-004-cross-platform-runner-foundation
```

| Field | Value | Meaning |
|---|---|---|
| Route | Pending | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope` |
| Releasable | Pending | `true`, or `false` for release-risk classes |
| Signals | Pending | Decisive detector findings |
| Warnings | Pending | Release-safety warnings |

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
| Pending | Pending | Pending | Pending |

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
| Slice 1 - Runner/preflight core | Pending | Pending | |
| Slice 2 - Contract parity and metadata | Pending | Pending | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in `tasks.md`.
- [ ] Runner unit/contract fixture tests pass.
- [ ] Runner manifest JSON validates.
- [ ] `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"` passes.
- [ ] `git diff --check` passes.
- [ ] Relevant Layer 1/Layer 4 checks pass when touched.
- [ ] `bash tests/speckit-pro/run-all.sh` passes or any inability to run is recorded.
- [ ] Final reviewability backstop passes or records accepted warnings with no blockers.
- [ ] UAT runbook is generated and validated if the implementation reaches PR packet flow.
- [ ] PR packet validates before PR creation.

---

## Self-Review

Before PR creation, record:

- Tests executed.
- Scope boundaries preserved.
- Known gaps.
- Whether native Windows/Linux execution happened or remains runbook-only for XPLAT-007.
- Review order for the two planned slices.

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
  layer4-scripts/
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
