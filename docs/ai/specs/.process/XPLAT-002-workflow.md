# SpecKit Workflow: XPLAT-002 — Runtime Implementation Options and Contract Decision

**Template Version**: 1.0.0
**Created**: 2026-06-26
**Status**: In Review (PR #266 pending merge)
**Purpose**: Prepare XPLAT-002 for autonomous execution from the cross-platform plugin runtime roadmap and the setup Grill Me decisions.

---

## How to Use This Workflow

Run this workflow from the XPLAT-002 worktree:

```bash
$speckit-autopilot docs/ai/specs/.process/XPLAT-002-workflow.md
```

This file is already populated for XPLAT-002. Do not replace it with the generic workflow template.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during `$speckit-scaffold-spec XPLAT-002`.
The full Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/XPLAT-002-design-concept.md
```

Re-read the design concept before each phase. It is the source of truth for setup decisions:

- Evaluate JavaScript/TypeScript, Python, and small per-platform binary runner candidates evenly against the XPLAT-001 runtime rubric.
- Use official/runtime documentation plus lightweight repo-local and installed-cache smoke probes where invocation behavior is uncertain.
- Select one canonical runtime and command contract; do not leave XPLAT-004 with a shortlist.
- Prefer a small stable CLI using JSON stdin/stdout, structured stderr diagnostics, and explicit exit-code mapping.
- Optimize for installed-cache first-run reliability with no per-user dependency installation or network fetch.
- Keep public support-claim changes out of this spec; XPLAT-007 owns truthful public release claims after validation.
- Keep this as one decision spike.

> Grill Me is human-in-the-loop only. It is not part of the autopilot loop. Once this workflow starts, clarifications happen through `$speckit-clarify` and consensus, never through grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `$speckit-specify` | Complete | Created the decision-spike spec and requirements quality checklist; G1 passed with zero clarification markers |
| Clarify | `$speckit-clarify` | Complete | Resolved candidate scoring, probe scope, command envelope, packaging, adapter, security handoff, and public-claim boundaries |
| Plan | `$speckit-plan` | Complete | Produced plan, research, data model, command contract, quickstart, and agent context pointer; G3 passed |
| Checklist | `$speckit-checklist` | Complete | Integration, error-handling, security, and reliability gaps remediated; G4 passed |
| Tasks | `$speckit-tasks` | Complete | Generated 33 decision-spike tasks after analysis remediation; G5/G6 passed |
| Analyze | `$speckit-analyze` | Complete | 3 findings (0C/0H/1M/2L), all remediated; G6 passed |
| Implement | `$speckit-implement` | Complete | Runtime decision, probe evidence, command contract, handoff, and G7 verification recorded; PR #266 remains pending merge |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | Candidate set, evidence bar, non-goals, and decision output are explicit; no runner build or public support claim scope creep |
| G2 | After Clarify | Ambiguities about probes, scoring/selection, packaging, and command-envelope details are resolved |
| G3 | After Plan | Plan uses XPLAT-001 rubric, keeps decision/probe scope reviewable, and records setup reviewability warning |
| G4 | After Checklist | All true requirement-quality gaps are remediated or explicitly out of scope |
| G5 | After Tasks | Tasks cover candidate evaluation, smoke probes, decision record, contract definition, and handoff evidence |
| G6 | After Analyze | No critical drift between the roadmap, design concept, spec, plan, and tasks |
| G7 | After Implementation | Decision record, probe evidence, spec-map check, diff hygiene, and relevant shell suite pass |

---

## Prerequisites

### Worktree and Branch

- Worktree: `.worktrees/xplat-002-runtime-implementation-options-contract-decision`
- Branch: `codex/xplat-002-runtime-implementation-options-contract-decision`
- Contract marker: `specs/xplat-002-runtime-implementation-options-contract-decision/SPEC-MOC.md`
- Design concept: `docs/ai/specs/.process/XPLAT-002-design-concept.md`

Before starting:

```bash
git rev-parse --abbrev-ref HEAD
git status --short
specify preset resolve spec-template
specify preset resolve plan-template
specify preset resolve tasks-template
```

Expected branch is `codex/xplat-002-runtime-implementation-options-contract-decision`. Preset resolution should use `.specify/presets/speckit-pro-reviewability/` unless a deliberate higher-priority override exists.

### Constitution Validation

| Principle | XPLAT-002 Requirement | Verification |
|-----------|-----------------------|--------------|
| Plugin Structure Compliance | Do not change installed plugin runtime behavior or generated payload invocation paths in this decision spec | `git diff --name-only` review |
| Script Safety | Any smoke probes added as durable artifacts must be simple, quoted, and non-mutating; no new shipped runtime helper belongs here | command review and `bash -n` for any committed shell probe |
| Test Coverage Before Merge | Static verification must prove the decision record, probe evidence, spec-map freshness, and no placeholder drift | focused commands listed below plus relevant shell suite |
| Conventional Commits | Setup and implementation commits must use conventional commit text | commit/PR review |
| KISS, Simplicity, YAGNI | Use the simplest evidence that can support a runtime decision; avoid speculative runner abstractions | plan complexity table and code review |

### Existing Source Truth

- Roadmap: `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
- XPLAT-001 report and rubrics: `docs/ai/research/cross-platform-runtime-inventory.md`
- Product requirement: `docs/prd-cross-platform-plugin-runtime.md`
- Roadmap MOC: `docs/ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md`
- Source runtime surfaces: `speckit-pro/skills/**`, `speckit-pro/codex-skills/**`, `speckit-pro/agents/**`, `speckit-pro/codex-agents/**`, `speckit-pro/hooks/**`, `speckit-pro/codex-hooks.json`, `speckit-pro/scripts/**`
- Generated payload surfaces for decision context only: `dist/claude/speckit-pro/**`, `dist/codex/speckit-pro/**`

### Reviewability Budget

Setup gate output:

```json
{"mode":"setup","status":"warn","pass":true,"reviewable_loc":250,"production_files":4,"total_files":10,"primary_surface_count":2,"primary_surfaces":["docs/process","harness/adapter"],"greenfield":false,"thresholds":{"warn":{"reviewable_loc":400,"production_files":6,"total_files":15,"primary_surfaces":1},"block":{"reviewable_loc":800,"production_files":8,"total_files":25,"primary_surfaces":1}},"exception_honored":false,"exception_class":null,"exceptions":{"accepted":[],"rejected":[]},"warnings":["primary surfaces 2 exceeds warn threshold 1"],"blockers":[]}
```

Record this warning in `plan.md`. It does not block setup.

### Phase 0 Preflight Results

| Check | Result | Evidence |
|-------|--------|----------|
| SpecKit CLI | Pass | `command -v specify` returned a local `specify` executable |
| Branch/worktree | Pass | Created worktree on `codex/xplat-002-runtime-implementation-options-contract-decision` from `origin/main` |
| Reviewability setup gate | Warn/pass | Two primary surfaces (`docs/process`, `harness/adapter`), no blockers |
| Grill Me | Complete | 8 questions; one decision spike accepted |
| Presets | Installed/refreshed | `ensure-reviewability-preset.sh` reported `status: installed`, changed `plan-template` |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | XPLAT-002 |
| **Name** | Runtime Implementation Options and Contract Decision |
| **Branch** | `codex/xplat-002-runtime-implementation-options-contract-decision` |
| **Feature directory** | `specs/xplat-002-runtime-implementation-options-contract-decision` |
| **Dependencies** | XPLAT-001 complete; use `docs/ai/research/cross-platform-runtime-inventory.md` |
| **Enables** | XPLAT-004, XPLAT-005, XPLAT-006, XPLAT-007 |
| **Priority** | P1 |

### Success Criteria Summary

- XPLAT-004 can build without reopening the runtime language/package decision.
- The selected command contract is precise enough for fixture parity tests.
- Rejected options are documented with enough rationale to avoid churn later.
- Decision evidence evaluates JavaScript/TypeScript, Python, and small binary candidates against the XPLAT-001 rubric.
- Lightweight probes or grounded documentation resolve installed-cache and invocation uncertainties.
- No public native-platform support claims are changed before XPLAT-007.

---

## Phase 1: Specify

**When to run:** At the start of XPLAT-002. Focus on what the decision must prove and what the selected contract must contain, not on building the runner. Output: `specs/xplat-002-runtime-implementation-options-contract-decision/spec.md`

### Specify Prompt

```bash
$speckit-specify

## Feature: Runtime Implementation Options and Contract Decision

### Problem Statement
SpecKit Pro's installed Claude and Codex workflows still depend on Bash, `.sh` helpers, `jq`, shell quoting, Unix paths, and shell-specific runtime behavior. XPLAT-001 proved the active runtime surface and produced runtime and supply-chain rubrics, but it deliberately did not choose a replacement runtime. XPLAT-002 must compare credible runtime implementation options and select one canonical runtime and command contract so XPLAT-004 can build without reopening the language/package decision.

### Users
- Maintainers deciding the cross-platform runtime strategy.
- Implementers of XPLAT-004 through XPLAT-007 who need a stable command contract.
- Reviewers who need to see why rejected runtime options were rejected.

### User Stories
1. As a maintainer, I can compare JavaScript/TypeScript, Python, and small per-platform binary runner candidates against the XPLAT-001 runtime rubric using grounded documentation and lightweight probe evidence.
2. As an implementer, I can read one selected runtime decision and a precise command contract covering entrypoint name, dispatch shape, JSON stdin/stdout, stderr diagnostics, exit-code mapping, path handling, subprocess rules, prerequisite reporting, and runtime version reporting.
3. As a reviewer, I can see rejected options, tie-breaker rationale, evidence gaps, and the exact handoff to XPLAT-003 and XPLAT-004 without any hidden public-support claim changes.

### Constraints
- Evaluate JavaScript/TypeScript, Python, and small per-platform binary options evenly before choosing.
- Use official/runtime documentation plus lightweight repo-local and installed-cache smoke probes where invocation behavior is uncertain.
- Select one canonical runtime and command contract; do not hand XPLAT-004 a ranked shortlist.
- Prefer a small stable CLI with JSON stdin/stdout, structured stderr diagnostics, and explicit exit-code mapping.
- Optimize for no per-user dependency installation or network fetch from the public installed plugin cache.
- Use install reliability and no-post-cache-install runtime-model reliability as the tie-breaker when candidates are otherwise close; actual installed-cache invocation proof belongs to XPLAT-004 because XPLAT-002 does not build the runner.
- Treat XPLAT-002 as a research/decision spike; the advisory size estimate is `status=ok`, `suggested_slices=1`.

### Out of Scope
- Building the runner.
- Porting helper behavior.
- Rewriting public docs or release notes beyond the decision record.
- Selecting supply-chain controls; only record runtime-specific implications for XPLAT-003.
- Native Windows/macOS/Linux release-readiness UAT, which remains XPLAT-007's gate.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 20 |
| User Stories | 3 |
| Acceptance Criteria | 6 |
| Quality Checklist | 16/16 passed |

### Files Generated

- [x] `specs/xplat-002-runtime-implementation-options-contract-decision/spec.md`
- [x] `specs/xplat-002-runtime-implementation-options-contract-decision/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** Spec has areas open to interpretation. Maximum 5 targeted questions per session.

### Clarify Prompts

#### Session 1: Candidate scoring and evidence

```bash
$speckit-clarify Focus on candidate scoring and evidence: confirm the rubric dimensions from `docs/ai/research/cross-platform-runtime-inventory.md`, how JavaScript/TypeScript, Python, and small binary candidates are compared without preselecting a winner, what counts as official/runtime documentation, and which lightweight repo-local or installed-cache smoke probes are required when invocation behavior is uncertain.
```

#### Session 2: Command contract envelope

```bash
$speckit-clarify Focus on the command contract: define the entrypoint name, helper dispatch shape, JSON stdin/stdout envelope, structured stderr diagnostics, exit-code mapping, path normalization, subprocess rules, prerequisite reporting, runtime version reporting, and fixture parity expectations that XPLAT-004 must implement.
```

#### Session 3: Packaging, adapters, and public-claim boundaries

```bash
$speckit-clarify Focus on packaging and boundaries: confirm the no-install/no-network installed-cache constraint, how temporary compatibility adapters are named and assigned to later removal specs, what runtime-specific implications should be handed to XPLAT-003, and how to avoid public Windows-support claim changes before XPLAT-007.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Candidate scoring and evidence | 5 | Gate-first weighted evidence matrix; three selectable runtime families only; official/runtime docs tier; bounded non-mutating smoke probes; doc/probe conflict handling |
| 2 | Command contract envelope | 5 | `speckit-pro-runner` accepted by consensus as the canonical entrypoint; JSON stdin/stdout envelope; line-delimited JSON stderr diagnostics; shared exit-code map with `legacy_exit_code`; typed path/subprocess rules; runtime-info/preflight and fixture parity expectations |
| 3 | Packaging, adapters, and public-claim boundaries | 5 | No-install/no-network installed-cache gate; owner-first compatibility adapter records with removal specs; per-candidate XPLAT-003 supply-chain matrix; XPLAT-004 receives only selected runtime, runner contract, fixture parity, and adapter records; no public support-claim surface changes before XPLAT-007 |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/xplat-002-runtime-implementation-options-contract-decision/plan.md`

### Plan Prompt

```bash
$speckit-plan

## Tech Stack and Current Runtime Surface
- Repository: Claude Code and Codex plugin marketplace with source under `speckit-pro/` and generated payloads under `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`.
- Current installed-runtime issue: active installed workflows depend on Bash-backed helpers, `jq`, shell quoting, Unix paths, and `.sh` dispatch.
- Decision source: `docs/ai/research/cross-platform-runtime-inventory.md`, especially the Runtime Evaluation Rubric for XPLAT-002.
- Package/update context: public plugin payloads are generated and consumed from installed plugin cache paths; XPLAT-002 should not require per-user network dependency installation.

## Constraints
- One decision spike, not implementation.
- Evaluate JavaScript/TypeScript, Python, and small per-platform binary options evenly.
- Gather official/runtime documentation and lightweight probe evidence where invocation behavior is uncertain.
- Select one canonical runtime and command contract.
- Use JSON stdin/stdout, structured stderr diagnostics, and explicit exit-code mapping as the preferred command-envelope shape unless Clarify records a better grounded reason.
- Record any compatibility adapter as temporary, with an owner spec and removal condition.
- Do not change public native-platform support claims.
- Record the setup reviewability warning: two primary surfaces, no blockers.

## Architecture Notes
- The decision record should include candidate comparison, selected contract, rejected options, evidence gaps, and handoff notes for XPLAT-003/XPLAT-004.
- Treat "no install step" as a first-class packaging criterion. The selected contract should be able to run from the installed plugin cache without per-user dependency installation or network fetch.
- Tie-breaker: user install reliability and no-post-cache-install runtime-model reliability outrank maintainer ergonomics when candidates are close; installed-cache invocation proof is deferred to XPLAT-004.
- XPLAT-003 receives runtime-specific dependency/security implications; XPLAT-002 does not choose first-release supply-chain controls.
- XPLAT-004 receives the precise command contract and fixture/probe expectations.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Technical context, decision method, constitution checks, and reviewability warning recorded |
| `research.md` | Complete | Gate-first matrix, evidence/probe decisions, command contract, adapter, supply-chain, and public-claim boundaries |
| `data-model.md` | Complete | Runtime candidate, evidence, rubric, command contract, adapter, supply-chain, and handoff entities |
| `contracts/` | Complete | `speckit-pro-runner` command envelope, diagnostics, exit-code, path, subprocess, preflight, adapter, and fixture parity contract |
| `quickstart.md` | Complete | Reviewer path for Plan artifacts, marker scan, diff hygiene, and implementation evidence expectations |

---

## Phase 4: Domain Checklists

**When to run:** After `$speckit-plan`, validate both spec and plan together.

### Recommended Domains

#### 1. Integration Checklist

Why: XPLAT-002 chooses the command contract that installed Claude/Codex payloads and later helper ports must call.

```bash
$speckit-checklist integration

Focus on XPLAT-002 requirements:
- Candidate evidence for installed Claude and Codex plugin-cache invocation
- Runtime entrypoint and helper dispatch contract
- Compatibility-adapter boundaries and owner/removal spec
- Handoff from XPLAT-001 inventory rows to XPLAT-004 implementation inputs
- Pay special attention to: any hidden assumption that requires a source checkout instead of an installed cache path
```

#### 2. Error Handling Checklist

Why: The selected contract must define stderr diagnostics, exit-code mapping, missing-prerequisite behavior, JSON parse failures, and subprocess failures before implementation.

```bash
$speckit-checklist error-handling

Focus on XPLAT-002 requirements:
- JSON input validation and malformed-envelope diagnostics
- Exit-code mapping for success, expected user error, helper failure, missing runtime, and unexpected exception
- Stderr and stdout separation
- Subprocess failure and missing-command behavior
- Pay special attention to: whether XPLAT-004 can build fixture parity tests from the requirement text alone
```

#### 3. Security Checklist

Why: XPLAT-002 does not select supply-chain controls, but the runtime choice constrains dependency, packaging, and local verification risks handed to XPLAT-003.

```bash
$speckit-checklist security

Focus on XPLAT-002 requirements:
- Runtime dependency footprint and bootstrap burden
- No-network/no-install package constraint and any exceptions
- Runtime-specific implications handed to XPLAT-003 without overclaiming controls
- Public-support claim boundary before XPLAT-007
- Pay special attention to: dependency or artifact assumptions that would force XPLAT-003 into an unreviewed security model
```

#### 4. Reliability Checklist

Why: First-run and installed-cache reliability are the accepted tie-breaker and must be measurable enough to choose between close candidates.

```bash
$speckit-checklist reliability

Focus on XPLAT-002 requirements:
- Installed-cache smoke probe expectations
- Offline behavior and first-run/bootstrap failure modes
- Runtime version reporting and diagnostics for user support
- Evidence gaps and fallback plan when a probe cannot be run locally
- Pay special attention to: tie-breaker criteria that are not objectively verifiable
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| integration | 32 | 3 found, 0 remaining | Host-specific installed-cache evidence, installed-payload helper dispatch boundaries, and XPLAT-001 row-derived XPLAT-004 input bundle added |
| error-handling | 24 | 1 found, 0 remaining | Malformed-envelope diagnostics and fixture-level stdout/stderr/exit assertions added |
| security | 29 | 1 found, 0 remaining | Dependency/artifact assumption classification added to prevent implicit XPLAT-003 security controls |
| reliability | 33 | 2 found, 0 remaining | Probe fallback records and objective close-candidate reliability tie-breaker rules added |

---

## Phase 5: Tasks

**When to run:** After checklists complete and all true gaps are resolved. Output: `specs/xplat-002-runtime-implementation-options-contract-decision/tasks.md`

### Tasks Prompt

```bash
$speckit-tasks

## Task Structure
- Keep this as one decision spike.
- Produce reviewable docs/process and probe-evidence tasks, not runner implementation tasks.
- Reference `spec.md`, `plan.md`, `research.md`, `data-model.md`, contracts, quickstart, and `docs/ai/specs/.process/XPLAT-002-design-concept.md`.
- Organize by user story: candidate comparison, selected contract, reviewer handoff.
- Include validation tasks for placeholder drift, spec-map freshness, diff hygiene, and relevant shell suite.

## Constraints
- Do not port helpers.
- Do not alter active installed invocation paths.
- Do not rebuild broad generated payloads.
- Do not change public native-platform support claims.
- Preserve the Q&A decisions: all three candidates evaluated, docs plus probes, one contract, JSON envelope, no install step, install reliability tie-breaker, one spike.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | 33 |
| **Phases** | 6 |
| **Parallel Opportunities** | 7 parallel tasks; batches T002-T005 and T010-T012 |
| **User Stories Covered** | US1 candidate comparison, US2 selected contract, US3 reviewer handoff |

---

## Atomicity Route

After tasks/G5, run the read-only classifier against the feature directory:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/xplat-002-runtime-implementation-options-contract-decision
```

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope` |
| **Releasable** | `true` | `true`, or `false` for release-risk classes |
| **Signals** | `change-shape:modify-heavy` | Decisive detector findings |
| **Warnings** | None | Release-safety warning, if any |

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks.

### Analyze Prompt

```bash
$speckit-analyze

Focus on:
1. Constitution alignment: no runner implementation, helper ports, active invocation changes, or public support-claim changes in XPLAT-002.
2. Coverage gaps: every FR, user story, success criterion, and contract entity has tasks.
3. Consistency with the XPLAT-001 runtime rubric and `docs/ai/specs/.process/XPLAT-002-design-concept.md`.
4. Decision integrity: all three runtime candidates are evaluated evenly, and one selected runtime contract is produced.
5. Probe integrity: lightweight probes are sufficient for uncertain invocation mechanics but do not become shipped runtime behavior.
6. Handoff integrity: XPLAT-003 gets security implications; XPLAT-004 gets the buildable command contract.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| A1 | MEDIUM | SC-008 lacked an explicit final diff reviewability verification task/quickstart command, leaving the completed-spike budget outcome under-covered. | Added T028 and quickstart validation for `reviewability-gate.sh diff origin/main...HEAD`. |
| A2 | LOW | Integration and reliability checklists still had unchecked rows even though rerun notes and current artifacts satisfied the questions. | Marked the satisfied checklist rows complete in `checklists/integration.md` and `checklists/reliability.md`. |
| A3 | LOW | `plan.md` Phase 0 Research Plan repeated list number `6`, making the ordered decision list inconsistent. | Renumbered the supply-chain implication item to `8`. |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed with no blocking coverage gaps.

### Implement Prompt

```bash
$speckit-implement

## Approach: Decision-Record Spike

For each task:
1. Gather grounded candidate evidence from official/runtime docs, repo-local context, and lightweight smoke probes where needed.
2. Compare candidates against the XPLAT-001 runtime rubric without preselecting a winner.
3. Select one canonical runtime and command contract.
4. Document rejected options and tie-breaker rationale.
5. Record handoff notes for XPLAT-003 and XPLAT-004.
6. Verify no runner implementation, helper port, active invocation-path change, generated payload cutover, or public native-platform support claim was introduced.

### Pre-Implementation Setup

```bash
git rev-parse --abbrev-ref HEAD
git status --short
specify preset resolve spec-template
specify preset resolve plan-template
specify preset resolve tasks-template
```

Expected branch: `codex/xplat-002-runtime-implementation-options-contract-decision`.

### Verification Targets

- `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"`
- `git diff --check`
- Focused probe commands recorded in the quickstart or research artifact
- Relevant deterministic shell suite, likely `bash tests/speckit-pro/run-all.sh --layer 1` for structural/spec-map changes, and broader suite if source/generator scripts change unexpectedly

### Implementation Notes

- The design concept is load-bearing: `docs/ai/specs/.process/XPLAT-002-design-concept.md`.
- XPLAT-001's runtime rubric is the evaluation backbone.
- If a candidate cannot be probed locally, record the evidence gap and why documentation is sufficient or insufficient.
- If the selected runtime implies supply-chain controls, hand them to XPLAT-003 rather than implementing them here.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Foundation | T001-T009 | Complete | Candidate evidence matrix, probe plan, and no-public-claim boundary recorded |
| Candidate evaluation | T010-T016 | Complete | JavaScript/TypeScript, Python, and Go binary evidence evaluated against the same rubric |
| Contract decision | T017-T019 | Complete | Go native binary selected; JSON envelope, stderr diagnostics, exit-code map, paths, subprocess, and preflight contract recorded |
| Handoff and verification | T020-T033 | Complete | XPLAT-003/XPLAT-004 handoff, spec-map, diff hygiene, reviewability gate, Layer 1, and PR packet content recorded |

---

## Post-Implementation Checklist

- [x] All tasks marked complete in `tasks.md`
- [x] No unresolved placeholders remain in generated artifacts
- [x] Spec-map check passes or stale generated zones are recorded with the required follow-up
- [x] Diff hygiene passes with `git diff --check`
- [x] Relevant shell suite passes: Layer 1 passed `1438/1438`; PR packet scope tests passed `93/93` and `17/17`; full default suite was attempted and is blocked by baseline DOC-014 privacy-scan terms already present on `origin/main`
- [x] Runtime decision record names selected and rejected options
- [x] Handoff notes for XPLAT-003 and XPLAT-004 are present
- [x] No public native-platform support claims changed

---

## Lessons Learned

### What Worked Well

- Gate-first candidate comparison kept JavaScript/TypeScript, Python, and Go
  native binaries evaluated evenly before selection.
- The `speckit-pro-runner` contract now gives XPLAT-004 enough detail for JSON
  I/O, stderr diagnostics, exit codes, typed paths, subprocess rules, preflight,
  and fixture parity.
- Evidence gaps were recorded explicitly instead of counted as successful
  installed-cache probes.

### Challenges Encountered

- The full default shell suite remains blocked by baseline DOC-014 privacy-scan
  terms already present on `origin/main`; XPLAT-owned privacy hits were removed.
- PR packet tooling had to be extended for `XPLAT-*` scopes before PR creation
  could pass the workflow contract.
- Reviewability required an accepted `infra` exception because the PR includes
  XPLAT PR tooling and synced Claude/Codex payload mirrors.

### Patterns to Reuse

- Use host-specific evidence-gap records with owner/expiry when local probes are
  unavailable.
- Keep compatibility adapters as owner-first temporary migration records rather
  than extra runtime candidates.
- Include a downstream handoff bundle mapping XPLAT-001 rows to runner inputs,
  fixtures, exclusions, and owner specs.

---

## Project Structure Reference

```text
docs/ai/research/
  cross-platform-runtime-inventory.md
docs/ai/specs/
  cross-platform-plugin-runtime-technical-roadmap.md
  .process/XPLAT-002-design-concept.md
  .process/XPLAT-002-workflow.md
specs/xplat-002-runtime-implementation-options-contract-decision/
  SPEC-MOC.md
  spec.md
  plan.md
  research.md
  data-model.md
  contracts/
  quickstart.md
speckit-pro/
  skills/
  codex-skills/
  agents/
  codex-agents/
  hooks/
dist/
  claude/speckit-pro/
  codex/speckit-pro/
```
