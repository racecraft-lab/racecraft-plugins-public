# SpecKit Workflow: XPLAT-009 - Plugin Source and Payload Bash Eradication

**Template Version:** 1.0.0
**Created:** 2026-07-07
**Purpose:** Prepare and execute the XPLAT-009 workflow from roadmap scope plus
the HITL Design Concept decisions.

---

## How to Use This Workflow

Run this workflow from the dedicated worktree:

```text
.worktrees/xplat-009-plugin-source-and-payload-bash-eradication
```

Each phase prompt below is already seeded from the technical roadmap and the
Grill Me design concept. Re-read the design concept before each phase:

```text
docs/ai/specs/.process/XPLAT-009-design-concept.md
```

---

## Design Concept

This workflow was enriched from the required Grill Me interview for
`$speckit-scaffold-spec XPLAT-009`.

Accepted decisions:

- Use one workflow with two vertical, PR-ready slices.
- Port active Bash behavior into Python runner/helper/gate paths, then remove
  live `.sh` files from `speckit-pro/`.
- Start with active references users can still hit, then rebuild payloads and
  add guard proof.
- Keep no live Bash fallback in source, generated payloads, or installed guidance.
- Use Python-backed gates with narrow historical/archive allowlists.
- Rebuild Claude/Codex payloads and prove an installed-cache artifact has zero
  Bash scripts.
- Seed integration, reliability, and security checklist focus.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|---|---|---|---|
| Specify | `$speckit-specify` | Complete | Generated `spec.md` with 3 user stories, 12 FRs, 6 acceptance scenarios, 7 success criteria, and no clarification markers |
| Clarify | `$speckit-clarify` | Complete | Resolved helper ownership, guard contracts, payload rebuild, installed-cache proof, release-readiness, and bounded proof policy |
| Plan | `$speckit-plan` | Complete | Created the two-slice technical plan, no-shell guard architecture, contracts, data model, research, and quickstart; G3 passed |
| Checklist | `$speckit-checklist` | Complete | Integration, reliability, and security checklists completed with 63 total items and 0 gaps |
| Tasks | `$speckit-tasks` | Complete | Generated 31 tasks ordered by the accepted two vertical slices |
| Analyze | `$speckit-analyze` | Complete | Fixed active-scope and post-cleanup no-live-fallback drift; marker counter reports 0 findings |
| Confidence Gate | G6.5 | Complete | Advisory gate returned `NO_DATA` with `recommended_action: soft_skip`; proceed to implementation |
| Implement | `$speckit-implement` | Complete | Removed 35 plugin Bash scripts, rebuilt payloads, and proved zero-Bash gates |
| Post | Post | Complete | PR #297 is open; final review remediation is complete, RepoPrompt returned no actionable findings, required GitHub checks are green, merge state is clean, and review threads are resolved/outdated in the live PR state. |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|---|---|---|
| G1 | After Specify | User stories cover plugin source Bash removal, active-instruction cleanup, generated payload/cache proof, and no-shell/no-jq guards without unresolved clarification markers |
| G2 | After Clarify | Helper ownership, no-live-fallback policy, historical/archive allowlists, payload proof, and installed-cache proof are explicit |
| G3 | After Plan | Plan records the reviewability warning, accepted two-slice strategy, Python runner operation choices, and guard architecture |
| G4 | After Checklist | Integration, reliability, and security gaps are remediated or explicitly out of scope |
| G5 | After Tasks | Tasks map to the accepted two slices and include tests before deleting scripts or changing generated payloads |
| G6 | After Analyze | No critical drift remains between roadmap, Design Concept, spec, plan, tasks, XPLAT-008 installed-runtime behavior, and XPLAT-010 boundaries |
| G6.5 | Confidence Gate | Advisory pre-Implement confidence evidence is recorded before implementation starts |
| G7 | After Implementation | `speckit-pro/`, generated payloads, and installed-cache proof contain zero live Bash scripts; active instructions contain no Bash or `jq` invocation path outside the narrow allowlist |

---

## Prerequisites

### Worktree and Branch

- Worktree: `.worktrees/xplat-009-plugin-source-and-payload-bash-eradication`
- Branch: `codex/xplat-009-plugin-source-and-payload-bash-eradication`
- Contract marker: `specs/xplat-009-plugin-source-and-payload-bash-eradication/SPEC-MOC.md`
- Design concept: `docs/ai/specs/.process/XPLAT-009-design-concept.md`
- Workflow: `docs/ai/specs/.process/XPLAT-009-workflow.md`

Expected branch is
`codex/xplat-009-plugin-source-and-payload-bash-eradication`. Preset resolution
should use `.specify/presets/speckit-pro-reviewability/` unless a deliberate
higher-priority override exists.

### Grounded Source Truth

- Roadmap: `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
- Roadmap MOC: `docs/ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md`
- XPLAT-008 workflow/design/release evidence:
  `docs/ai/specs/.process/XPLAT-008-workflow.md`,
  `docs/ai/specs/.process/XPLAT-008-design-concept.md`,
  `docs/ai/specs/.process/XPLAT-008-release-readiness.md`, and
  `docs/ai/specs/.process/XPLAT-008-uat-matrix.md`
- Runner package: `speckit-pro/speckit_pro_runner/`
- Current plugin-source Bash inventory:
  `find speckit-pro -type f -name '*.sh'` returns 35 files at scaffold time.
- Current generated payload Bash inventory:
  `find dist/claude/speckit-pro dist/codex/speckit-pro -type f -name '*.sh'`
  returns zero files at scaffold time.
- XPLAT-010 boundary: repository-wide Bash confinement outside plugin source,
  generated payloads, and installed-cache proof is explicitly out of scope.

### Phase 0 Preflight Results

| Check | Result | Notes |
|---|---|---|
| Codex agent install | Pass | `validate-agent-install.sh --surface codex --autoheal` reported 10 bundled agents installed |
| SpecKit CLI | Pass | `specify 0.11.8` available on `PATH` |
| Branch/worktree | Pass | Created dedicated worktree from `origin/main` |
| Reviewability setup gate | Warn/pass | `reviewable_loc: 400`, `production_files: 6`, `total_files: 15`, primary surfaces `docs/process` and `harness/adapter`; warning accepted by two-slice plan |
| Grill Me | Complete | 8 picker questions; accepted one workflow, port-then-remove, active references first, no live fallback, Python gates with allowlist, rebuild plus cache proof, two slices, integration/reliability/security checklists |
| Preset resolution | Pass | `spec-template`, `plan-template`, and `tasks-template` resolve to `.specify/presets/speckit-pro-reviewability/` |

### Constitution Validation

| Principle | Requirement | Verification |
|---|---|---|
| Plugin Structure Compliance | Source and generated plugin packages remain structurally valid after script removal and payload rebuilds | Layer 1 structural validation and payload conformance checks |
| Script Safety | XPLAT-009 removes plugin Bash scripts rather than adding or retaining live Bash implementations | Zero `.sh` guard for `speckit-pro/` and generated payloads |
| Semantic Versioning | Version metadata remains release-please managed; no manual version drift | Existing version triplet/release checks |
| Test Coverage Before Merge | Helper/gate behavior has focused tests before script deletion or guard tightening | Focused Python runner/helper tests plus Layer 4 gate coverage |
| Conventional Commits | PR title and commits use repo convention | PR workflow contract validation |
| KISS, Simplicity & YAGNI | Prefer direct Python helper/gate ports and explicit allowlists over broad wrapper layers | Plan complexity table and code review |

---

## Specification Context

### Basic Information

| Field | Value |
|---|---|
| Spec ID | XPLAT-009 |
| Name | Plugin Source and Payload Bash Eradication |
| Branch | `codex/xplat-009-plugin-source-and-payload-bash-eradication` |
| Feature directory | `specs/xplat-009-plugin-source-and-payload-bash-eradication` |
| Dependencies | XPLAT-008 complete/archived; public native release remains blocked by XPLAT-008 UAT matrix |
| Enables | XPLAT-010 and public Bash-free release readiness |
| Priority | P1 |

### Scope Summary

XPLAT-009 removes remaining plugin-source Bash scripts and active Bash/`jq`
instructions from source and generated payloads while preserving XPLAT-008's
installed-runtime behavior. It must prove `speckit-pro/`, generated
Claude/Codex payloads, and an installed-cache artifact have zero live Bash script
files. It must also guard active instructions against Bash, `.sh`, `jq`, shell
interpolation, or Unix-only assumptions outside historical/archive prose.

### Success Criteria Summary

- [x] `find speckit-pro -type f -name '*.sh'` returns zero files.
- [x] `find dist/claude/speckit-pro dist/codex/speckit-pro -type f -name '*.sh'`
  returns zero files after payload rebuild.
- [x] Installed-cache proof from rebuilt payloads contains zero Bash script files.
- [x] Active source and generated plugin instructions contain no Bash or `jq`
  invocation path outside a narrow historical/archive allowlist.
- [x] Focused runner/helper tests and release-readiness gates pass with the new
  no-shell guard enabled.

### Implementation Evidence

| Evidence | Result |
|---|---|
| Source inventory | `docs/ai/specs/.process/XPLAT-009-source-inventory.md` records 35 deleted source scripts and Python ownership mapping |
| Source `.sh` scan | `find speckit-pro -type f -name '*.sh'` returned zero files |
| Payload `.sh` scan | `find dist/claude/speckit-pro dist/codex/speckit-pro -type f -name '*.sh'` returned zero files |
| Payload completeness | `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`; Claude hash `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6`, Codex hash `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e`, both `script_file_count: 0` |
| Installed-cache proof | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`; source-derived, immutable fixture proof, `script_file_count: 0` for Claude and Codex |
| Zero-Bash guard | `docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json`; `gate_status: pass`, `blocking_count: 0`, `script_file_count: 0` |
| Release readiness | `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`; `gate_status: pass` |
| Final default suite | `bash tests/speckit-pro/run-all.sh` -> `2017/2017 passed` after RepoPrompt review remediation |

### Accepted Two-Slice Plan

| Slice | Scope | Review Boundary |
|---|---|---|
| Slice 1 | Port or remove active plugin-source Bash behavior and active source guidance under `speckit-pro/skills/**`, `speckit-pro/codex-skills/**`, `speckit-pro/agents/**`, `speckit-pro/codex-agents/**`, `speckit-pro/hooks/**`, `speckit-pro/codex-hooks.json`, `speckit-pro/scripts/**`, `speckit-pro/README.md`, `README.md`, and current install guidance | Ends with source-level active references no longer depending on Bash or `jq`; generated payloads may still need rebuild |
| Slice 2 | Rebuild Claude/Codex payloads, prove generated payload and installed-cache zero-Bash state, and add/tighten Python-backed zero-Bash/active-instruction guards | Ends with release-ready guard evidence for plugin source, generated payloads, and installed cache |

---

## Phase 1: Specify

**When to run:** At the start of XPLAT-009. Focus on what must be removed,
what behavior must be preserved, and what proof blocks XPLAT-010. Output:
`specs/xplat-009-plugin-source-and-payload-bash-eradication/spec.md`.

### Specify Prompt

```text
$speckit-specify

## Feature: Plugin Source and Payload Bash Eradication

### Problem Statement
XPLAT-008 cut installed Claude/Codex runtime paths over to Python and rebuilt
generated payloads with zero `.sh` files, but the source plugin still contains
35 Bash scripts and active source/generated instructions still reference Bash or
`jq`. XPLAT-009 must remove that plugin-source Bash substrate and prove rebuilt
payloads and installed-cache artifacts remain Bash-free before XPLAT-010 can
confine repository-wide Bash to GitHub CI/CD dispatch glue.

### Users
- Maintainers who need `speckit-pro/` source to match the installed-runtime
  Python-only contract.
- Claude and Codex users whose generated/installed plugin payloads must not
  include Bash scripts or Bash-oriented active guidance.
- Reviewers who need deterministic evidence that Bash references are historical,
  archived, or explicitly out of release behavior.
- Release maintainers who need gates that block reintroduced `.sh`, Bash, or
  `jq` paths in plugin source and generated payloads.

### User Stories
1. As a maintainer, I can run source-level checks and see zero live `.sh` files
   under `speckit-pro/`.
2. As a Claude or Codex plugin user, the generated and installed plugin payload
   contains no Bash scripts and active guidance points only at Python runner
   behavior.
3. As a reviewer, I can inspect a narrow historical/archive allowlist and
   deterministic guard evidence proving active instructions do not depend on
   Bash, `.sh`, `jq`, shell interpolation, or Unix-only assumptions.

### Constraints
- Follow `docs/ai/specs/.process/XPLAT-009-design-concept.md`.
- Preserve XPLAT-008 installed-runtime behavior: Python 3.11+ direct
  `speckit_pro_runner` invocation with no Bash, Git Bash, WSL,
  PowerShell-specific command language, or `jq` requirement.
- Use one workflow with two vertical slices: source cleanup first, then
  payload/cache proof and guards.
- Port active behavior before deleting scripts; do not leave Python wrappers
  around live `.sh` files.
- Allow historical/archive prose only through a narrow documented allowlist that
  cannot satisfy release readiness.

### Out of Scope
- Repository-wide Bash cleanup under `tests/**`, top-level `scripts/**`,
  hooks outside the plugin package, `.specify/**`, or GitHub Actions dispatch
  glue. XPLAT-010 owns that.
- Completing XPLAT-008 native operator UAT rows.
- Replacing GitHub Actions workflow YAML or CI/CD dispatch snippets.
- Rewriting historical/archive prose solely to remove old Bash wording.
```

### Specify Results

| Metric | Value |
|---|---|
| Functional Requirements | 12 |
| User Stories | 3 |
| Acceptance Criteria | 6 |
| Success Criteria | 7 |
| G1 Gate | Pass: `spec.md` exists with 0 `[NEEDS CLARIFICATION]` markers |

### Files Generated

- [x] `specs/xplat-009-plugin-source-and-payload-bash-eradication/spec.md`
- [x] `specs/xplat-009-plugin-source-and-payload-bash-eradication/checklists/requirements.md`

### SpecKit Traceability Markers

| Marker | Purpose |
|---|---|
| `[US1]`, `[US2]`, `[US3]` | User story references for source cleanup, payload/cache proof, and active-instruction guard evidence |
| `[FR-001]` | Functional requirement reference |
| `[NEEDS CLARIFICATION]` | Flag for Clarify phase; none should remain after G2 |
| `[P]` | Parallel-safe task marker |
| `[Gap]` | Missing coverage item from checklists or analyze |

---

## Phase 2: Clarify

**When to run:** After Specify, before Plan. XPLAT-009 has helper ownership,
allowlist, guard, and payload/cache proof ambiguity that should be resolved
before implementation tasks are generated.

### Clarify Prompts

#### Session 1: Active Helper and Instruction Inventory

```text
$speckit-clarify

Focus on active helper and instruction inventory for XPLAT-009:
- Classify every `.sh` file under `speckit-pro/` by active behavior, historical
  reference, install support, generated-payload support, or deletion candidate.
- Identify active source and generated instructions that tell maintainers,
  agents, or installed workflows to call Bash, `.sh`, `jq`, shell interpolation,
  Git Bash, WSL, PowerShell-specific command language, or Unix-only paths.
- Decide which existing Python runner/helper/gate operation owns each active
  behavior and which new operation, if any, is required.
- Preserve the Q2/Q4 decision: port then remove, with no live Bash fallback.
```

#### Session 2: Guard and Allowlist Contract

```text
$speckit-clarify

Focus on zero-Bash guard and allowlist contracts for XPLAT-009:
- Define guard inputs for `speckit-pro/`, `dist/claude/speckit-pro`,
  `dist/codex/speckit-pro`, and installed-cache proof.
- Define the active-instruction scan scope and the narrow historical/archive
  allowlist that can mention Bash without satisfying release readiness.
- Specify the failure shape for `.sh`, Bash, `jq`, shell interpolation, or
  Unix-only active guidance regressions.
- Decide how these guards plug into existing Python runner gates and release
  readiness without adding shell fallback paths.
```

#### Session 3: Payload Rebuild and Installed-Cache Proof

```text
$speckit-clarify

Focus on generated payload and installed-cache proof for XPLAT-009:
- Define the source-to-dist rebuild path for Claude and Codex payloads after
  plugin-source Bash removal.
- Define the installed-cache artifact proof that shows payload installation or
  extraction produces zero Bash script files.
- Confirm which XPLAT-008 UAT evidence remains out of scope and which release
  readiness evidence XPLAT-009 must update.
- Pay special attention to keeping generated payloads source-derived rather than
  hand-edited.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---|---|---|---|
| 1 | Active helper and instruction inventory | 5 | Live source baseline is 35 `.sh` files; active/deferred helpers need Python runner/helper/gate ownership before deletion; active registries must expose Python operation IDs, with old `.sh` names only as inactive provenance or historical allowlist entries excluded from release readiness |
| 2 | Guard and allowlist contract | 5 | One Python runner guard request covers source, generated payload, and installed-cache proof inputs; active scope includes installed/user/maintainer-facing source and generated mirrors; failures use bounded runner-envelope findings; release readiness consumes the gate in-process and blocks on missing proof, blocking findings, or allowlist evidence misuse |
| 3 | Payload rebuild and installed-cache proof | 5 | Rebuild Claude/Codex payloads through Python runner `payload-completeness` apply mode, prove source-derived payloads with file inventory and tree hashes, create bounded source-derived installed-cache proof, keep XPLAT-008 native UAT out of scope, and reject mutable real-user-cache-only evidence for release readiness |

### Consensus Resolution Log

| Item | Round | Categories | Resolution | Evidence |
|---|---:|---|---|---|
| Phase 2 Session 1 Q2 | 1 | `[codebase]` | Accepted: port active deferred or unmapped shell helper behavior to explicit Python runner/helper/gate ownership before deletion; classify delete-only only when no active owner or current reference remains. | `codebase-analyst` helper-family review |
| Phase 2 Session 1 Q3 | 1 | `[codebase, spec]` | Accepted: active registries and active outputs expose Python operation IDs after shell removal; legacy `.sh` names may remain only as inactive provenance or historical allowlist entries excluded from release readiness. | `codebase-analyst` registry review and `spec-context-analyst` design/spec policy review |
| Phase 2 Session 2 | 0 | none | Consensus not required: clarify executor resolved all five guard and allowlist questions with high confidence from repo-local evidence. | `clarify-executor` guard contract review |
| Phase 2 Session 3 Q5 | 1 | `[codebase, security]` | Accepted: release readiness must require bounded, source-derived installed-cache proof; mutable real-user-cache evidence is supplemental UAT context only and cannot satisfy the blocking proof requirement. | `codebase-analyst` and `domain-researcher` proof-boundary reviews |

---

## Phase 3: Plan

**When to run:** After spec and clarification are approved. Output:
`specs/xplat-009-plugin-source-and-payload-bash-eradication/plan.md`.

### Plan Prompt

```text
$speckit-plan

## Tech Stack
- Runtime substrate: Python 3.11+ standard-library runner via
  `speckit-pro/speckit_pro_runner/`.
- Source plugin surfaces: `speckit-pro/skills/**`,
  `speckit-pro/codex-skills/**`, `speckit-pro/agents/**`,
  `speckit-pro/codex-agents/**`, `speckit-pro/hooks/**`,
  `speckit-pro/codex-hooks.json`, and `speckit-pro/scripts/**`.
- Generated payloads: `dist/claude/speckit-pro/**` and
  `dist/codex/speckit-pro/**`, rebuilt from source.
- Verification: Python runner/helper/gate tests, Layer 1 structural validation,
  focused Layer 4 tests, generated payload checks, installed-cache zero-Bash
  proof, active-instruction no-shell/no-jq guard, and spec-index checks.

## Constraints
- Preserve the accepted two-slice strategy from
  `docs/ai/specs/.process/XPLAT-009-design-concept.md`.
- Record the setup reviewability warning and explain why two vertical slices are
  sufficient unless Plan or Tasks proves child specs are required.
- Do not keep a live Bash fallback, Python wrapper around `.sh`, hidden shell
  dispatch, or staged deprecation path in active source or generated payloads.
- Keep XPLAT-010 scope out of this plan: repository-wide test harnesses,
  top-level scripts, `.specify/**`, hooks outside the plugin package, and
  GitHub workflow dispatch glue.
- Keep XPLAT-008 native operator UAT out of this plan except as preserved
  release-readiness blocker context.

## Architecture Notes
- Slice 1 should inventory active references, map each live script behavior to
  Python runner/helper/gate ownership, add focused tests, and remove live source
  `.sh` files plus active Bash-oriented guidance.
- Slice 2 should rebuild Claude/Codex payloads from source, prove generated and
  installed-cache zero-Bash state, and wire Python-backed guards into the
  release-readiness path.
- Use explicit allowlists for historical/archive prose. Allowlisted historical
  references must not count as active behavior or release-ready proof.
- Use the Design Concept Q&A as the source of truth for why child specs,
  live fallback, docs exceptions, simple scan-only gates, and full native UAT
  were rejected.
```

### Plan Results

| Artifact | Status | Notes |
|---|---|---|
| `plan.md` | Complete | Technical context, accepted two-slice execution flow, constitution check, accepted reviewability warning, declared implementation footprint, and zero-Bash guard architecture |
| `research.md` | Complete | 8 decisions covering 35-script baseline, helper ownership, registry operation IDs, guard architecture, allowlist policy, payload rebuild, installed-cache proof, and XPLAT-008 UAT boundary |
| `data-model.md` | Complete | Source inventory records, Python operation ownership, active-instruction findings, allowlist entries, payload rebuild records, installed-cache proof records, and guard results |
| `contracts/` | Complete | Added request/result schemas for `active-path-guard/zero-bash-guard`, historical allowlist entries, and bounded installed-cache proof |
| `quickstart.md` | Complete | Maintainer flow for source cleanup, payload rebuild, installed-cache proof, and final release-readiness guard verification |

### Plan Gate Results

| Check | Result | Notes |
|---|---|---|
| G3 | Pass | `validate-gate.sh G3 specs/xplat-009-plugin-source-and-payload-bash-eradication` returned `pass: true` with 0 unresolved markers |
| Plan reviewability estimator | Pass/advisory | `estimate-reviewable-loc.sh` returned `status: pass`, `projected: 0`, `total_entries: 27`; plan preserves the setup reviewability warning because this estimator does not classify plugin Python/source paths as production LOC |
| Marker scan | Clean | New Plan artifacts contain 0 `[NEEDS CLARIFICATION]`, 0 `[Gap]`, 0 `[CRITICAL]`, and 0 `[HIGH]` markers |

---

## Phase 4: Domain Checklists

**When to run:** After Plan. Validate both `spec.md` and `plan.md`.

### Recommended Domains

1. **integration** - Source plugin behavior, generated payloads, installed-cache
   proof, and release gates must agree on one no-shell runtime path.
2. **reliability** - Guard failures, allowlist handling, payload rebuilds, and
   installed-cache proof must fail clearly and deterministically.
3. **security** - No live fallback or unsafe public trust/support claim may be
   introduced while removing Bash.

### Enriched Checklist Prompts

#### 1. Integration Checklist

```text
$speckit-checklist integration

Focus on XPLAT-009 requirements:
- Every active plugin-source Bash behavior has a Python runner/helper/gate owner
  or is explicitly deleted as inactive.
- Source plugin surfaces, generated Claude/Codex payloads, and installed-cache
  proof all use the same no-shell runtime contract.
- Payload rebuild evidence is source-derived, not hand-edited.
- Pay special attention to: drift between `speckit-pro/**`, `dist/**`, and
  installed-cache proof after `.sh` removal.
```

#### 2. Reliability Checklist

```text
$speckit-checklist reliability

Focus on XPLAT-009 requirements:
- Zero-Bash and active-instruction guards fail on `.sh`, Bash, `jq`, shell
  interpolation, and Unix-only active guidance.
- Historical/archive allowlist entries are narrow, deterministic, and cannot
  satisfy release readiness.
- The two slices have independent verification and clear rollback points.
- Pay special attention to: guard false negatives that allow a live Bash path to
  remain in source or generated payloads.
```

#### 3. Security Checklist

```text
$speckit-checklist security

Focus on XPLAT-009 requirements:
- No Bash fallback, `jq` path, Git Bash, WSL, or PowerShell-specific command
  language is presented as current installed-runtime guidance.
- Public docs, README, and release-readiness evidence do not overclaim native
  support or consumer trust beyond XPLAT-008 and XPLAT-003 evidence.
- Installed-cache proof cannot hide unsafe drift or count historical/archive
  references as active runtime compliance.
- Pay special attention to: support or trust wording that implies Bash-free
  public release readiness before XPLAT-008 UAT and XPLAT-010 are complete.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|---|---|---|---|
| integration | 24 | 0 found, 0 remaining | Source behavior ownership, cross-surface runtime contract, payload/cache proof integration, release gate alignment |
| reliability | 19 | 0 found, 0 remaining | Guard failure determinism, allowlist and release readiness, payload/cache proof reliability, slice recovery |
| security | 20 | 0 found, 0 remaining | Runtime guidance, public trust/support claims, payload/cache proof, allowlist boundaries, release-readiness behavior |
| Total | 63 | 0 found, 0 remaining | FR-001 through FR-012 and SC-001 through SC-007 |

G4 validation: integration, reliability, and security checklist artifacts are
complete with 0 `[Gap]` markers and no consensus escalations.

---

## Phase 5: Tasks

**When to run:** After checklists complete and true gaps are resolved. Output:
`specs/xplat-009-plugin-source-and-payload-bash-eradication/tasks.md`.

### Tasks Prompt

```text
$speckit-tasks

## Task Structure
- Organize tasks by the accepted two slices, not by broad technical layer.
- Every task should reference user stories and functional requirements from
  `spec.md`.
- Mark parallel-safe tasks with [P] only when file ownership and dependencies
  are actually independent.
- Include tests or deterministic verification before deleting `.sh` files,
  changing active guidance, rebuilding payloads, or tightening release gates.

## Required Slice Ordering
1. Active plugin-source Bash removal:
   - Inventory all `speckit-pro/**/*.sh` files and active Bash/`jq`
     instructions.
   - Map live behavior to Python runner/helper/gate ownership.
   - Add focused tests for replacement behavior before deleting scripts.
   - Remove live `.sh` files and active Bash-oriented source guidance.
2. Payload rebuild and zero-Bash proof:
   - Rebuild Claude and Codex payloads from updated source.
   - Prove `dist/claude/speckit-pro/**` and `dist/codex/speckit-pro/**`
     contain zero `.sh` files.
   - Produce installed-cache zero-Bash proof from rebuilt payloads.
   - Add or tighten Python-backed active-instruction and no-shell/no-jq guards.

## Constraints
- Reference `docs/ai/specs/.process/XPLAT-009-design-concept.md`, `spec.md`,
  and `plan.md` in task-generation rationale.
- Use Non-goals to avoid XPLAT-010 repository-wide cleanup, XPLAT-008 native
  UAT completion, live Bash fallback, and historical/archive prose rewrites.
- Keep generated payload tasks tied to source rebuild commands and completeness
  gates; do not hand-edit `dist/**` as source of truth.
```

### Tasks Results

| Metric | Value |
|---|---|
| Total Tasks | 31 |
| Phases | 2 slice phases: active plugin-source Bash removal; payload rebuild and zero-Bash proof |
| Parallel Opportunities | 2 groups: `T003`-`T005` and `T021`-`T022` |
| User Stories Covered | US1, US2, US3; FR-001 through FR-012 |

---

## Atomicity Route

After Tasks/G5, run the read-only atomicity classifier and record its decision:

```text
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/xplat-009-plugin-source-and-payload-bash-eradication
```

| Field | Value | Meaning |
|---|---|---|
| Route | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope` |
| Releasable | `true` | `true`, or `false` for a destructive-migration or concurrency-sensitive change |
| Signals | `change-shape:modify-heavy` | Decisive detector findings behind the route and releasability reading |
| Warnings | none | Release-safety warning attached to the change |

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```text
$speckit-analyze

Focus on XPLAT-009:
1. Constitution alignment: plugin structure, versioning, test coverage, and KISS.
2. Scope drift: verify XPLAT-010 repository-wide Bash cleanup and XPLAT-008
   native UAT completion are not pulled into this spec.
3. Coverage gaps: ensure every `.sh` removal, active-instruction cleanup,
   payload rebuild, installed-cache proof, and guard requirement has tasks.
4. Consistency: compare roadmap, Design Concept, spec, plan, tasks, and
   release-readiness evidence for no-live-fallback drift.
5. Safety: verify historical/archive allowlists cannot satisfy active runtime or
   release-readiness proof.
```

### Analyze Severity Levels

| Severity | Meaning | Action Required |
|---|---|---|
| CRITICAL | Blocks implementation, violates constitution, or leaves a live Bash fallback | Must fix before G6 gate |
| HIGH | Significant gap that could let Bash or `jq` remain active | Should fix |
| MEDIUM | Improvement opportunity or reviewability risk | Review and decide |
| LOW | Minor inconsistency | Note for future |

### Analysis Results

| ID | Severity | Issue | Resolution |
|---|---|---|---|
| A1 | HIGH | Active-instruction cleanup tasks were narrower than the spec/plan active-source scan scope, which includes skills, Codex skills, agents, Codex agents, hooks, `codex-hooks.json`, plugin scripts, README, root install guidance, and generated mirrors. | Broadened `tasks.md` T011, `plan.md` declared file operations, and the workflow Slice 1 scope to cover every scan-identified active guidance file in those surfaces. |
| A2 | CRITICAL | The post-implementation checklist still invoked `generate-spec-index.sh` even though XPLAT-009 tasks delete that source script after Python ownership is established. | Replaced the post-implementation Bash command with a Python-owned spec-index check and amended `tasks.md` T031 to forbid invoking a deleted `.sh` path. |

---

## Phase 6.5: Confidence Gate

Run the advisory confidence gate before implementation starts. The gate should
confirm the spec, plan, tasks, and Design Concept are coherent enough to execute
without re-opening major scope decisions.

```text
bash speckit-pro/skills/speckit-autopilot/scripts/confidence-gate.sh docs/ai/specs/.process/XPLAT-009-workflow.md --mode advisory
```

| Decision | Status | Notes |
|---|---|---|
| Proceed to implementation | Soft-skip/proceed | `confidence-gate.sh docs/ai/specs/.process/XPLAT-009-workflow.md --mode advisory` returned `NO_DATA`, `mode: advisory`, and `recommended_action: soft_skip` |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed.

### Implement Prompt

```text
$speckit-implement

## Approach: TDD-First

For each task:
1. RED: Add or update focused tests or guard fixtures defining the expected
   no-shell behavior.
2. GREEN: Port active behavior into Python runner/helper/gate paths or remove
   inactive Bash source.
3. REFACTOR: Keep the implementation simple and avoid wrapper layers around
   deleted `.sh` behavior.
4. VERIFY: Run focused tests, payload/cache proof, and guard checks before
   moving to the next slice.

### Pre-Implementation Setup

1. Verify branch:
   `git rev-parse --abbrev-ref HEAD` should be
   `codex/xplat-009-plugin-source-and-payload-bash-eradication`.
2. Read `docs/ai/specs/.process/XPLAT-009-design-concept.md`, `spec.md`,
   `plan.md`, and `tasks.md`.
3. Re-run source and payload inventories:
   `find speckit-pro -type f -name '*.sh'`
   and
   `find dist/claude/speckit-pro dist/codex/speckit-pro -type f -name '*.sh'`.
4. Run the smallest focused tests before each helper or gate edit.

### Implementation Notes

- Slice 1 owns active plugin-source Bash removal and source guidance cleanup.
- Slice 2 owns payload rebuild, installed-cache zero-Bash proof, and guard
  enforcement.
- Do not delete tests or historical evidence simply to hide references. Classify
  historical/archive text through an allowlist and keep it out of active
  release-readiness proof.
- Do not change GitHub Actions dispatch glue or repo-wide test harness scripts
  unless Plan proves a file is inside XPLAT-009's plugin-source boundary.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|---|---|---|---|
| Slice 1 - Active plugin-source Bash removal | Complete | All scoped tasks | Source Bash scripts removed and active source guidance cured |
| Slice 2 - Payload/cache proof and guards | Complete | All scoped tasks | Payloads rebuilt, installed-cache proof refreshed, and zero-Bash guards tightened |
| Polish and release packet | Complete | All scoped tasks | Verification, PR packet, PR creation, retrospective evidence, and post-review remediation recorded |

---

## Post-Implementation Checklist

- [x] All tasks marked complete in `tasks.md`
- [x] `find speckit-pro -type f -name '*.sh'` returns zero files
- [x] `find dist/claude/speckit-pro dist/codex/speckit-pro -type f -name '*.sh'`
  returns zero files after payload rebuild
- [x] Installed-cache proof from rebuilt payloads contains zero Bash script files
- [x] Active source and generated plugin instructions contain no Bash or `jq`
  invocation path outside the accepted historical/archive allowlist
- [x] Focused Python runner/helper/gate tests pass
- [x] Layer 1 structural validation passes
- [x] Layer 4 focused tests pass for changed helper/gate behavior
- [x] Python-owned spec-index check established by the source-cleanup tasks
  passes without invoking a deleted `.sh` path
- [x] PR packet includes summary, affected plugin paths, test commands, payload
  proof, installed-cache proof, and XPLAT-010 handoff

### Canonical Post Items

| Item | Status | Notes |
|---|---|---|
| Post: Doctor Extension Check | Skipped in Codex / equivalent checks complete | `.specify/extensions/speckit-utils/commands/doctor.md` exists for Claude/SpecKit, but no callable Codex doctor skill is exposed. Equivalent local checks: toolchain preflight passed, full suite passed. |
| Post: Verify Implementation | Complete | `bash tests/speckit-pro/run-all.sh` passed `2016/2016` after merging `origin/main`; focused helper/gate/runner tests and privacy scan passed. |
| Post: Verify Tasks Phantom Check | Complete | `tasks.md` has zero open `- [ ] T...` checkboxes; all T001-T031 are complete. |
| Post: Code Review | Complete with local remediation | RepoPrompt review-agent launch failed with `Transport closed`; parent review found the XPLAT-004/XPLAT-008 runner guard regression and fixed it. |
| Post: Integration Suite | Complete | Full deterministic suite passed: `2016/2016` after merging `origin/main`; `git diff --check` passed. |
| Post: Reviewability Diff Gate | Warn/proceed | Final diff is 166 files / 5,741 insertions / 16,526 deletions; accepted route remains `one-navigable-PR` because source deletion, Python ownership, payload rebuilds, and proof must land together. Evidence: `specs/xplat-009-plugin-source-and-payload-bash-eradication/.process/final-reviewability/gate-state.json`. |
| Post: Self-Review | Complete | Self-review found no remaining blocking issue after the runner guard fix; residual risk is PR/CI feedback after publication. |
| Post: UAT Runbook Generation | Complete | Generated `specs/xplat-009-plugin-source-and-payload-bash-eradication/.process/uat-runbook.md`; it explicitly excludes XPLAT-008 native operator UAT. |
| Post: PR Body Generation | Complete | Generated `docs/ai/specs/.process/XPLAT-009-pr-packet.json` and `docs/ai/specs/.process/XPLAT-009-pr-body.md`. |
| Post: PR Creation | Complete | Opened PR #297: https://github.com/racecraft-lab/racecraft-plugins-public/pull/297 |
| Post: Review Remediation | Complete | Final pushed head `558a255b0863ebf9e0fbacd860347322c8960149` has RepoPrompt clean-gate chat `untitled-chat-5AF444` -> `NO FINDINGS`; `gh pr checks 297` reports all checks passing including CodeQL and `test (speckit-pro)`; GraphQL reports `mergeStateStatus: CLEAN`; prior CodeQL review threads are resolved and outdated. |
| Post: Retrospective | Complete | Captured XPLAT-010 handoff, autopilot stop correction, PR URL, and PR-check remediation in `docs/ai/specs/.process/XPLAT-009-retrospective.md`. |

### Post Verification Evidence

| Check | Result |
|---|---|
| `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` | `34/34 passed` |
| `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` | `17/17 passed` |
| `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` | `50/50 passed` |
| `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` | `10/10 passed` |
| `bash tests/speckit-pro/unit/test-privacy-scan.sh` | `10/10 passed` |
| `bash tests/speckit-pro/run-all.sh` | `2016/2016 passed` after merging `origin/main` |
| `git diff --check origin/main...HEAD` | Passed |
| PR creation | PR #297 opened: https://github.com/racecraft-lab/racecraft-plugins-public/pull/297 |
| PR title remediation | Corrected live PR title to `feat(xplat): eradicate plugin Bash runtime surface`; release-readiness title gate passed locally. |
| Docs reference remediation | `node docs-site/scripts/generate-reference-pages.mjs --check` passed after replacing the deleted `validate-gate.sh` citation with `validate-autopilot-phase-coverage.py`. |
| Docs quality remediation | `node docs-site/scripts/validate-docs-quality.mjs` passed. |
| Post-remediation full suite | `bash tests/speckit-pro/run-all.sh` passed `2021/2021`. |
| GitHub PR checks after remediation | `validate-docs`, `validate-pr-title`, `test (speckit-pro)`, `validate-plugins`, `validate-workflows`, `detect`, and CodeQL passed on PR #297 after commit `d7346195`. |
| `rp-review-cli` remediation guard | Review chat `xplat-009-review-F05E58` reported active deferred-helper guidance, zero-Bash scan coverage, installed-cache proof trust, release check identity, stale spec-index wording, and replacement coverage gaps; all were remediated in source, payloads, proof fixtures, and tests. |
| XPLAT-009 zero-Bash guard after `rp-review-cli` remediation | `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/plugin-bash-confinement/requests/zero-bash-guard-final.json` passed with zero blocking findings. |
| Focused gate/runner remediation checks | `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `48/48 passed`; `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/layer1-structural/validate-spec-index-determinism.sh` -> `16/16 passed`; `bash tests/speckit-pro/unit/test-post-implementation-reference.sh` -> `35/35 passed`. |
| Full suite after `rp-review-cli` remediation | `bash tests/speckit-pro/run-all.sh` passed `2021/2021`. |
| Second `rp-review-cli` remediation guard | Review chat `pr297-review-F9A56A` reported active-guidance blind spots, installed-cache proof trust gaps, and XPLAT-009 contract drift; remediation now scans references/templates/contracts for all forbidden categories, prevents nearby tool declarations from masking active guidance, requires both Claude and Codex source-derived installed-cache proofs, and aligns the XPLAT-009 JSON schemas with runner fixtures. |
| Installed-cache proof after second remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after second remediation | `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `48/48 passed`; `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `git diff --check` passed. |
| Full suite after second remediation | `bash tests/speckit-pro/run-all.sh` passed `2021/2021`. |
| Third `rp-review-cli` remediation guard | Review chat `pr297-review-CEF9EE` reported request schema mode drift, broad negative-policy masking, installed-cache proof spoof/empty-root gaps, and stale zero-Bash evidence; remediation removed unsupported `dry_run` from the contract, added XPLAT-009-specific negative-policy classification, required product/root consistency and non-empty payload inventories, added source-tree/root-mismatch/empty-root coverage, and regenerated final zero-Bash evidence. |
| Focused checks after third remediation | `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `49/49 passed`; `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `git diff --check` passed. |
| Full suite after third remediation | `bash tests/speckit-pro/run-all.sh` passed `2022/2022`. |
| Fourth `rp-review-cli` remediation guard | Review chat `pr297-review-AE9227` reported remaining guard false-negatives for nearby negative prose, Python argv/alias subprocess calls, and uppercase script suffixes; remediation made active guidance line-local while preserving wrapped negative policy context, added alias/argv subprocess scanning, normalized script suffix checks, and added focused regression fixtures. |
| Focused checks after fourth remediation | `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `49/49 passed`; `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `git diff --check` passed. |
| Full suite after fourth remediation | `bash tests/speckit-pro/run-all.sh` passed `2022/2022`. |
| Fifth `rp-review-cli` remediation guard | Review chat `untitled-chat-843DF0` reported remaining false-negatives for mixed active guidance near negative prose, Windows-style Bash/jq argv paths, physical uppercase script files, and partial/traversal-shaped installed-cache proof roots; remediation made active guidance clause-local, normalized Windows argv basenames, made real filesystem suffix scans case-insensitive, required canonical full product payload roots, added partial-root proof fixtures, and added a physical uppercase `.SH` regression test. |
| Focused checks after fifth remediation | `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `50/50 passed`; `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; final zero-Bash guard evidence regenerated. |
| Full suite after fifth remediation | `bash tests/speckit-pro/run-all.sh` passed `2023/2023`. |
| Sixth `rp-review-cli` remediation guard | Review chat `untitled-chat-89546F` reported remaining proof trust and argv gaps for same-product traversal/absolute roots, missing `mutable_user_cache`, and env-wrapped Bash/jq argv delegation; remediation now requires raw proof roots to be exact normalized repo-relative product payload roots, requires `mutable_user_cache: false`, treats missing mutable-cache evidence as untrusted in the proof summary, and catches `/usr/bin/env`/`env` delegated Bash and jq calls. |
| Focused checks after sixth remediation | `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `50/50 passed`; `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; final zero-Bash guard evidence regenerated. |
| Full suite after sixth remediation | `bash tests/speckit-pro/run-all.sh` passed `2023/2023`. |
| Seventh `rp-review-cli` remediation guard | Review chat `untitled-chat-9A0777` reported remaining guard false-negatives for `env -S`/`--split-string` argv delegation, broad negative-policy masking, and stale payload-completeness evidence; remediation now parses `env` split-string payloads with `shlex`, keeps comma-separated negative-policy lists intact, blocks misleading `do not run without Bash` / `do not skip Bash` language, and refreshes payload proof/evidence hashes. |
| Focused checks after seventh remediation | `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `50/50 passed`; `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `git diff --check` passed; final payload, zero-Bash, and release-readiness evidence regenerated. |
| Full suite after seventh remediation | `bash tests/speckit-pro/run-all.sh` passed `2023/2023`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` passed `10/10` after sanitizing generated local runtime paths. |
| Eighth `rp-review-cli` remediation guard | Review chat `xplat-009-review-74E76D` reported read-only helper runner invocation metadata, active-path allowlist trust, and mixed `allowed-tools:` guidance false-negative issues; remediation added executable stdin request metadata, rejects non-historical allowlist paths, checks active guidance before strict tool declarations, and adds regression fixtures/tests. |
| Focused checks after eighth remediation | `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` -> `34/34 passed`; `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `50/50 passed`; `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `git diff --check` passed. |
| Full suite after eighth remediation | `bash tests/speckit-pro/run-all.sh` passed `2024/2024`; L4 now includes `498/498` script tests with read-only helper stdin replay coverage. |
| Ninth `rp-review-cli` remediation guard | Review chat `xplat009-review-AD6447` reported remaining P1s for XPLAT-008 active runtime masking by nearby `allowed-tools` declarations and optional installed-cache proof requests still producing missing-proof blockers; remediation made the XPLAT-008 tool-declaration exemption single-line only and skips installed-cache proof validation when proof is explicitly optional. |
| Focused checks after ninth remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` -> `34/34 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `git diff --check` passed. |
| Full suite after ninth remediation | `bash tests/speckit-pro/run-all.sh` passed `2025/2025`; L4 now includes `499/499` script tests with optional-proof and multiline tool-declaration regression coverage. |
| Upstream merge remediation | Merged `origin/main` (`c9176902`) with upstream changes authoritative except Bash mentions; cured the upstream Bash-specific references in `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` and synced both generated payload mirrors. |
| Focused checks after upstream merge | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `git diff --check` passed; no conflict markers remain. |
| Full suite after upstream merge | `bash tests/speckit-pro/run-all.sh` passed `2016/2016`; L4 remained `499/499` and Layer 5 tool scoping passed `191/191`. |
| Final clean-gate remediation | Review chat `untitled-chat-5AE660` reported two remaining P1 gaps: the promoted zero-Bash final scan did not include root `README.md`, and Python subprocess scanning missed static argv variables plus `sh -c` payloads. Remediation added `README.md` to `final-current-implementation.scan_roots`, added static argv and shell-payload detection to `active_path_guard.py`, added regression fixture coverage, synced generated payload mirrors, and refreshed payload/cache proof evidence. |
| Installed-cache proof after final clean-gate remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after final clean-gate remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `git diff --check` passed; generated JSON evidence parsed successfully. |
| Full suite after final clean-gate remediation | `bash tests/speckit-pro/run-all.sh` passed `2016/2016`; L4 remained `499/499` and Layer 5 tool scoping passed `191/191`. |
| Second final clean-gate remediation | Review chat `untitled-chat-E38C46` reported two remaining P1 gaps: `env -S` / `--split-string` could delegate to `sh -c` payloads that hid `jq` or script paths, and fixture `scan_roots` were not trust-bound before traversal/pathspec use. Remediation recursively inspects env-split delegated argv payloads, rejects absolute/traversal scan roots before traversal and changed-line pathspecs, and added regression fixture coverage. |
| Focused checks after second final clean-gate remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `git diff --check` passed. |
| Full suite after second final clean-gate remediation | `bash tests/speckit-pro/run-all.sh` passed `2016/2016`; L4 remained `499/499` and Layer 5 tool scoping passed `191/191`. |
| Third final clean-gate remediation | Review chat `untitled-chat-D7EB89` reported one remaining P1 gap: malformed `scan_roots` entries could silently weaken zero-Bash coverage by falling back to default roots or skipping invalid entries. Remediation now blocks non-string, empty, absolute, and traversal scan roots before traversal/pathspec use, avoids default-root fallback for malformed configured roots, applies the same validation to active-runtime changed-source scanning, and adds malformed-scan-root regression coverage. |
| Installed-cache proof after third final clean-gate remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after third final clean-gate remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `validate-autopilot-phase-coverage.py` -> `status: pass`; `git diff --check` passed; no conflict markers remain. |
| Full suite after third final clean-gate remediation | `bash tests/speckit-pro/run-all.sh` passed `2016/2016`; L4 remained `499/499` and Layer 5 tool scoping passed `191/191`. |
| Fourth final clean-gate remediation | Review chat `untitled-chat-1CABD2` reported remaining P1 gaps for present-but-invalid `scan_roots` containers: empty arrays and non-list values could still weaken zero-Bash or active-runtime coverage. Remediation now treats present empty/non-list `scan_roots` as blocking scan-root findings, avoids default fallback whenever malformed `scan_roots` is present, adds XPLAT-008 active-runtime fixture coverage, adds XPLAT-009 zero-Bash empty/non-list fixture coverage, and refreshes payload/proof evidence hashes. |
| Installed-cache proof after fourth final clean-gate remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after fourth final clean-gate remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `validate-autopilot-phase-coverage.py` -> `status: pass`; `git diff --check` passed; no conflict markers remain. |
| Full suite after fourth final clean-gate remediation | `bash tests/speckit-pro/run-all.sh` passed `2016/2016`; L4 remained `499/499` and Layer 5 tool scoping passed `191/191`. |
| Fifth final clean-gate remediation | Review chat `untitled-chat-F5F78B` reported remaining P1 gaps in Python argv subprocess scanning: attached `env -S...` split-string arguments were skipped, and shell `-c` wrappers only blocked when their payload contained Bash/jq/script markers. Remediation parses attached `-S...` payloads, treats any shell `-c` wrapper as a blocked live shell dependency, adds direct parser assertions, extends the zero-Bash fixture with attached `env -S` and Python-only shell-wrapper cases, and refreshes payload/proof evidence hashes. |
| Installed-cache proof after fifth final clean-gate remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after fifth final clean-gate remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `validate-autopilot-phase-coverage.py` -> `status: pass`; `git diff --check` passed; no conflict markers remain. |
| Full suite after fifth final clean-gate remediation | `bash tests/speckit-pro/run-all.sh` passed `2016/2016`; L4 remained `499/499` and Layer 5 tool scoping passed `191/191`. |
| Sixth final clean-gate remediation | Review chat `untitled-chat-D283B7` reported one remaining P1 gap: non-Python text/JSON/TOML scans could miss `sh -c` / `zsh -c` live shell wrappers when no Bash/jq/script marker appeared in the payload. Remediation adds a generic `shell_command_wrapper` forbidden pattern for shell command names followed by `-c`-style flags, adds a `codex-hooks.json` JSON argv regression fixture, extends expected zero-Bash categories, and refreshes payload/proof evidence hashes. |
| Installed-cache proof after sixth final clean-gate remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after sixth final clean-gate remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `validate-autopilot-phase-coverage.py` -> `status: pass`; `git diff --check` passed; no conflict markers remain. |
| Full suite after sixth final clean-gate remediation | `bash tests/speckit-pro/run-all.sh` passed `2016/2016`; L4 remained `499/499` and Layer 5 tool scoping passed `191/191`. |
| Seventh final clean-gate remediation | Review chat `untitled-chat-59B696` reported three remaining P1 gaps: multiline JSON/TOML shell-wrapper argv arrays could evade line-by-line scans, nearby negative-policy prose could mask hard runtime shell wrappers, and extensionless shell scripts were not scanned or counted. Remediation adds content-window shell-wrapper scanning, blocks hard runtime categories unless historical or allowlisted, scans extensionless plugin/payload files, counts extensionless shell shebangs, adds pretty JSON hook and extensionless script fixtures, and refreshes payload/proof evidence hashes. |
| Installed-cache proof after seventh final clean-gate remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after seventh final clean-gate remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `validate-autopilot-phase-coverage.py` -> `status: pass`; `git diff --check` passed; no conflict markers remain; payload, zero-Bash, and release-readiness evidence parsed as `ok/pass`. |
| Full suite after seventh final clean-gate remediation | `bash tests/speckit-pro/run-all.sh` passed `2016/2016`; L4 remained `499/499` and Layer 5 tool scoping passed `191/191`. |
| Eighth final clean-gate remediation | Review chat `untitled-chat-44B3DD` reported one remaining P1 gap: path-qualified shell wrappers such as `"/bin/sh", "-c"` or `"/usr/bin/zsh", "-c"` could evade text/JSON/TOML shell-wrapper scans. Remediation extends same-line and multiline shell-wrapper patterns to accept optional path prefixes before shell basenames, adds `/bin/sh` and `/usr/bin/zsh` regression fixtures, syncs generated payload mirrors, and refreshes payload/proof evidence hashes. |
| Installed-cache proof after eighth final clean-gate remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after eighth final clean-gate remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `validate-autopilot-phase-coverage.py` -> `status: pass`; `git diff --check` passed; no conflict markers remain; no local path leaks; payload, zero-Bash, and release-readiness evidence parsed as `ok/pass`. |
| Full suite after eighth final clean-gate remediation | `bash tests/speckit-pro/run-all.sh` passed `2016/2016`; L4 remained `499/499` and Layer 5 tool scoping passed `191/191`. |
| Ninth final clean-gate remediation | Review chat `untitled-chat-D67DD8` reported remaining shell-flag, script-reference, and metadata gaps: TOML/YAML `shell = true` / `shell: true` escaped `shell_true`, `.sh` references inside parentheses or Markdown links escaped `script_file`, and zero-Bash repo-root prerequisite failures returned XPLAT-007 metadata. Remediation broadens `shell_true`, broadens script path boundary handling, returns XPLAT-009 base data for zero-Bash repo-root errors, adds TOML/YAML and punctuation/link script fixtures, adds a zero-Bash missing-prerequisite metadata assertion, syncs payload mirrors, and refreshes evidence hashes. |
| Installed-cache proof after ninth final clean-gate remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after ninth final clean-gate remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `validate-autopilot-phase-coverage.py` -> `status: pass`; `git diff --check` passed; no conflict markers remain; no local path leaks; payload, zero-Bash, and release-readiness evidence parsed as `ok/pass`. |
| Full suite after ninth final clean-gate remediation | `bash tests/speckit-pro/run-all.sh` passed `2016/2016`; L4 remained `499/499` and Layer 5 tool scoping passed `191/191`. |
| Tenth final clean-gate remediation | Review chat `untitled-chat-F1735C` reported partially-static Python subprocess argv gaps and stale workflow status. Remediation now scans inline and assigned argv lists even when only some elements are static, blocks static forbidden executables, shell `-c` wrappers, and script suffix arguments inside otherwise dynamic argv lists, adds regression fixtures, syncs payload mirrors, and refreshes workflow/process evidence. |
| Installed-cache proof after tenth final clean-gate remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after tenth final clean-gate remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `validate-autopilot-phase-coverage.py` -> `status: pass`; `git diff --check` passed; no conflict markers remain; no local path leaks; payload, zero-Bash, release-readiness, and installed-cache proof evidence parsed successfully. |
| Full suite after tenth final clean-gate remediation | `bash tests/speckit-pro/run-all.sh` passed `2016/2016`; L4 remained `499/499` and Layer 5 tool scoping passed `191/191`. |
| Eleventh final clean-gate remediation | Review chat `untitled-chat-D49579` reported one remaining P1: partially-resolved Python argv forms could hide shell execution through static string variables, dynamic `env -S` / `--split-string` payloads, or prior unsafe argv assignments. Remediation resolves static string variables inside argv arrays, treats unresolved env split-string payloads as blocking, blocks any prior unsafe argv assignment for a subprocess argv variable, adds exact regression fixtures, syncs payload mirrors, and refreshes proof/evidence hashes. |
| Installed-cache proof after eleventh final clean-gate remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after eleventh final clean-gate remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `validate-autopilot-phase-coverage.py` -> `status: pass`; `git diff --check` passed; no conflict markers remain; no local path leaks; payload, zero-Bash, release-readiness, and installed-cache proof evidence parsed successfully. |
| Full suite after eleventh final clean-gate remediation | `bash tests/speckit-pro/run-all.sh` passed `2016/2016`; L4 remained `499/499` and Layer 5 tool scoping passed `191/191`. |
| Twelfth final clean-gate remediation | Review chat `untitled-chat-33C3BE` reported one remaining P1: extensionless plugin/payload files with `sh` or `zsh` shebangs were counted as prohibited script files but not emitted as blocking source findings. Remediation now emits a blocking `script_file` finding for prohibited extensionless shebang content, adds `sh` and `zsh` regression fixtures, updates expected guard categories, syncs payload mirrors, and refreshes proof/evidence hashes. |
| Installed-cache proof after twelfth final clean-gate remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after twelfth final clean-gate remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `validate-autopilot-phase-coverage.py` -> `status: pass`; `git diff --check` passed; no conflict markers remain; no local path leaks after release-readiness evidence scrub; payload, zero-Bash, release-readiness, and installed-cache proof evidence parsed successfully. |
| Full suite after twelfth final clean-gate remediation | `bash tests/speckit-pro/run-all.sh` passed `2016/2016`; L4 remained `499/499` and Layer 5 tool scoping passed `191/191`. |
| Thirteenth final clean-gate remediation | Review chat `untitled-chat-C04511` reported two remaining P1 gaps: active `$SHELL` / `${SHELL}` guidance was not detected outside command substitution, and YAML list-style shell wrappers could evade multiline detection. Remediation adds targeted `$SHELL` shell-interpolation detection with negative-policy preservation, adds YAML list shell-wrapper detection, adds zero-Bash and active-runtime regression fixtures, syncs payload mirrors, and refreshes proof/evidence hashes. |
| Installed-cache proof after thirteenth final clean-gate remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after thirteenth final clean-gate remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `validate-autopilot-phase-coverage.py` -> `status: pass`; `git diff --check` passed; no conflict markers remain; no local path leaks; payload, zero-Bash, release-readiness, and installed-cache proof evidence parsed successfully. |
| Full suite after thirteenth final clean-gate remediation | `bash tests/speckit-pro/run-all.sh` passed `2016/2016`; L4 remained `499/499` and Layer 5 tool scoping passed `191/191`. |
| GitHub CodeQL remediation | GitHub checks on pushed head `94d86d4f` reported inefficient regex findings in generated Claude/Codex payload mirrors for the multiline shell-wrapper pattern. Remediation replaces the repeated newline/whitespace group with a single explicit newline pattern in source, syncs generated payload mirrors, and refreshes proof/evidence hashes. |
| Installed-cache proof after GitHub CodeQL remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after GitHub CodeQL remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `validate-autopilot-phase-coverage.py` -> `status: pass`; `git diff --check` passed; no conflict markers remain; no local path leaks; payload, zero-Bash, release-readiness, and installed-cache proof evidence parsed successfully. |
| Full suite after GitHub CodeQL remediation | `bash tests/speckit-pro/run-all.sh` passed `2016/2016`; L4 remained `499/499` and Layer 5 tool scoping passed `191/191`. |
| Fourteenth final clean-gate remediation | Review chat `untitled-chat-E1D178` reported one remaining P1: shell-wrapper detection missed JSON/YAML/TOML argv lists with intervening shell flags before `-c`. Remediation keeps the regex bounded while allowing up to three non-`-c` shell flags before the command flag, adds same-line JSON and multiline YAML regression fixtures with `-e`/`-f`, syncs payload mirrors, and refreshes proof/evidence hashes. |
| Installed-cache proof after fourteenth final clean-gate remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after fourteenth final clean-gate remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `51/51 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `validate-autopilot-phase-coverage.py` -> `status: pass`; `git diff --check` passed; no conflict markers remain; no local path leaks; payload, zero-Bash, release-readiness, and installed-cache proof evidence parsed successfully. |
| Full suite after fourteenth final clean-gate remediation | `bash tests/speckit-pro/run-all.sh` passed `2016/2016`; L4 remained `499/499` and Layer 5 tool scoping passed `191/191`. |
| RepoPrompt review remediation | Review chat `xplat009-review-2F683E` reported remaining gaps in replay helper contracts, oversized script scanning, executable structural validators, extensionless payload script counting, and extensionless structural script detection. Remediation makes helper replay commands explicit, scans prohibited suffixes and extensionless shell shebangs before size caps, restores the structural validator executable bit, counts extensionless shell shebangs in payload completeness, adds focused regressions, syncs payload mirrors, and refreshes proof/evidence hashes. |
| Installed-cache proof after RepoPrompt review remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after RepoPrompt review remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` -> `34/34 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `52/52 passed`; `bash tests/speckit-pro/run-all.sh --layer 1` -> `1326/1326 passed`; no local path leaks; no stale current payload hashes remain; payload, zero-Bash, release-readiness, and installed-cache proof evidence parsed successfully. |
| Full suite after RepoPrompt review remediation | `bash tests/speckit-pro/run-all.sh` passed `2017/2017`; L4 is `500/500` and Layer 5 tool scoping passed `191/191`. |
| Second RepoPrompt review remediation | Review chat `xplat-009-review-3B4AA5` reported remaining gaps in active `allowed-tools: Bash` grants, symlink scan trust boundaries, release-readiness acceptance of nonzero payload `script_file_count`, and weakened Layer 4 discovery assertions. Remediation removes active Bash tool grants from Claude skill source, rebuilds generated payload mirrors, skips symlinked scan candidates that resolve outside the repo trust boundary, blocks release-readiness payload completeness when any payload reports script files, and replaces the weak Layer 4 threshold with explicit canonical script assertions. |
| Installed-cache proof after second RepoPrompt review remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after second RepoPrompt review remediation | No source or generated skill `allowed-tools: Bash` declarations remain; payload, zero-Bash, release-readiness, installed-cache proof, and fixture JSON parsed successfully; `docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json` reports `status: pass`, `blocking_count: 0`, `script_file_count: 0`; `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json` reports `status: pass`, `blocking_count: 0`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `52/52 passed`. |
| Full suite after second RepoPrompt review remediation | `bash tests/speckit-pro/run-all.sh` passed `2017/2017`; L4 is `500/500` and Layer 5 tool scoping passed `191/191`. |
| Third RepoPrompt review remediation | Review chat `pr297-review-2D0090` reported remaining gaps where payload-completeness status could pass with nonzero payload script files, and broad `instead of` / `rather than` negative-policy handling could mask active Bash or `jq` guidance. Remediation makes payload completeness fail whenever `script_file_count` is nonzero, treats active shell invocations as blocking before broad contrast-policy classification, adds focused regressions, rebuilds generated payload mirrors, and refreshes proof/evidence hashes. |
| Installed-cache proof after third RepoPrompt review remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after third RepoPrompt review remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `52/52 passed`; `git diff --check` passed; no conflict markers remain; no local path leaks; no active `allowed-tools: Bash` declarations remain; payload, zero-Bash, release-readiness, installed-cache proof, and fixture JSON parsed successfully. |
| Full suite after third RepoPrompt review remediation | `bash tests/speckit-pro/run-all.sh` passed `2017/2017`; L4 is `500/500` and Layer 5 tool scoping passed `191/191`. |
| Fourth RepoPrompt review remediation | Review chat `untitled-chat-D29EF0` reported remaining P1 gaps where shell-wrapper scans missed long shell flags or `-o <arg>` before `-c`, and where active `/bin/sh` or `zsh` command tokens without `-c` still represented Unix-shell runtime requirements. Remediation adds bounded long-flag and option-argument wrapper detection, adds a distinct hard-runtime `shell_runtime` category for structured `sh`/`zsh` command tokens, blocks `sh`/`zsh` subprocess argv and `env` delegation, adds JSON/YAML/Python regressions, rebuilds generated payload mirrors, and refreshes proof/evidence hashes. |
| Installed-cache proof after fourth RepoPrompt review remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after fourth RepoPrompt review remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `52/52 passed`; `git diff --check` passed; no conflict markers remain; no local path leaks; no active `allowed-tools: Bash` declarations remain; payload, zero-Bash, release-readiness, installed-cache proof, and fixture JSON parsed successfully. |
| Full suite after fourth RepoPrompt review remediation | `bash tests/speckit-pro/run-all.sh` passed `2017/2017`; L4 is `500/500` and Layer 5 tool scoping passed `191/191`. |
| Fifth RepoPrompt review remediation | Review chat `untitled-chat-B73C57` reported that multiline YAML command-list detection needed explicit coverage. The detector already emitted `shell_command_wrapper` and `shell_runtime` findings for the multiline YAML fixture; remediation adds exact category/line assertions for `command`, `long_command`, and `runtime_command` blocks so that multiline command-list behavior is locked down. |
| Focused checks after fifth RepoPrompt review remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `52/52 passed`; `git diff --check` passed; no conflict markers remain; no local path leaks; XPLAT-009 JSON parsed successfully. |
| Full suite after fifth RepoPrompt review remediation | `bash tests/speckit-pro/run-all.sh` passed `2017/2017`; L4 is `500/500` and Layer 5 tool scoping passed `191/191`. |
| Sixth RepoPrompt review remediation | Review chat `untitled-chat-87DFD0` reported that the XPLAT-008 active-runtime scan path still used line-oriented matching and could miss multiline YAML command-list shell wrappers. Remediation runs content-level forbidden-pattern scans in both legacy active-path and XPLAT-008 active-runtime paths, adds exact active-runtime YAML assertion coverage, syncs generated payload mirrors, and refreshes proof/evidence hashes. |
| Installed-cache proof after sixth RepoPrompt review remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after sixth RepoPrompt review remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `52/52 passed`; `git diff --check` passed; no conflict markers remain; no local path leaks; payload, zero-Bash, release-readiness, and installed-cache proof evidence parsed successfully. |
| Full suite after sixth RepoPrompt review remediation | `bash tests/speckit-pro/run-all.sh` passed `2017/2017`; L4 is `500/500` and Layer 5 tool scoping passed `191/191`. |
| Seventh RepoPrompt review remediation | Review chat `pr297-review-74CB77` reported two remaining P1 gaps: bare `sh`/`zsh` runtime declarations could evade the active-path guard, and Python shell execution detection did not fail closed for dynamic truthy `shell` values or shell-backed helper APIs. Remediation broadens `shell_runtime` coverage for structured command/tool declarations, adds content-level multiline command-list detection, treats dynamic/truthy shell keywords as blocking, blocks `subprocess.getoutput`, `subprocess.getstatusoutput`, and `os.popen`, adds focused fixture coverage, syncs generated payload mirrors, and refreshes proof/evidence hashes. |
| Installed-cache proof after seventh RepoPrompt review remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0`. |
| Focused checks after seventh RepoPrompt review remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `52/52 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; payload, zero-Bash, release-readiness, and installed-cache proof evidence parsed successfully; `git diff --check` passed; no conflict markers remain; no local path leaks. |
| Full suite after seventh RepoPrompt review remediation | `bash tests/speckit-pro/run-all.sh` passed `2017/2017`; L4 is `500/500` and Layer 5 tool scoping passed `191/191`. |
| Eighth RepoPrompt review remediation | Review chat `xplat009-review-DF77AC` reported three remaining P1 gaps: suffixful `.zsh`/`.bash` runtime-shell scripts could evade script counts, installed-cache proof compared `dist` to itself, and allowlist validation did not require reviewer-facing `reason` and `scope`. Remediation expands prohibited script suffixes and shebang scanning, removes suffixful scripts from payloads, requires non-empty allowlist reason/scope, rejects same-root installed-cache proof, adds a bounded source-derived installed-cache fixture copy, and adds focused regression fixtures. |
| Installed-cache proof after eighth RepoPrompt review remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0` and distinct installed roots under `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/`. |
| Focused checks after eighth RepoPrompt review remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `52/52 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; payload, zero-Bash, release-readiness, and installed-cache proof evidence parsed successfully; `git diff --check` passed; no conflict markers remain; no local path leaks. |
| Full suite after eighth RepoPrompt review remediation | `bash tests/speckit-pro/run-all.sh` passed `2017/2017`; L4 is `500/500` and Layer 5 tool scoping passed `191/191`. |
| Ninth RepoPrompt review remediation | Review chat `pr297-xplat009-1D455C` reported remaining gaps in the active payload builder, final scan-root coverage, allowlist validation, and `max_findings` bounds. Remediation removes the shell payload builder, adds the Python builder entry point, updates refresh/validation/docs references, includes the builder in final zero-Bash scan roots, deletes shell-shebang files during payload builds, rejects unsupported/traversal/invalid allowlist entries, caps findings at 500, and syncs source, dist, installed-cache fixtures, and promotion metadata away from the deleted builder. |
| Installed-cache proof after ninth RepoPrompt review remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0` and distinct installed roots under `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/`. |
| Focused checks after ninth RepoPrompt review remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `52/52 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `node docs-site/scripts/generate-reference-pages.mjs --check` passed; `git diff --check` passed; stale builder reference sweep found no active matches outside intentionally blocking fixtures. |
| Full suite after ninth RepoPrompt review remediation | `bash tests/speckit-pro/run-all.sh` passed `2017/2017`; L4 is `500/500` and Layer 5 tool scoping passed `191/191`. |
| Tenth RepoPrompt review remediation | Review chat `untitled-chat-C2163E` reported remaining gaps in active installed-agent `Bash` declarations, `env` shell-wrapper proof coverage, stale installed-cache proof hashes, and negative proof isolation. Remediation removes active Claude agent `Bash` denial tokens, makes future `disallowedTools: Bash` declarations block zero-Bash proof, adds `env -i` and env-assignment shell-wrapper regressions, refreshes source/dist/installed-cache proof hashes, and makes installed-cache negative fixture category assertions exact. |
| Installed-cache proof after tenth RepoPrompt review remediation | `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and XPLAT-009 fixtures use source payload tree hashes `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` for Claude and `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e` for Codex, both with `script_file_count: 0` and distinct installed roots under `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/`. |
| Focused checks after tenth RepoPrompt review remediation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `52/52 passed`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `bash tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh` -> `186/186 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; `node docs-site/scripts/generate-reference-pages.mjs --check` passed; `git diff --check` passed; no conflict markers or active `disallowedTools: Bash` declarations remain. |
| Full suite after tenth RepoPrompt review remediation | `bash tests/speckit-pro/run-all.sh` passed `2012/2012`; L4 is `500/500` and Layer 5 tool scoping passed `186/186`. |
| Suite gate shell-dispatch relocation (2026-07-08) | Moved the suite gate layer-1/4 shell dispatch out of the shipped runner (`speckit-pro/speckit_pro_runner/gates/suite.py`) into repo-side `tests/speckit-pro/run-layer-scripts.py`, so the installed payload stays Bash-free; regenerated the Claude and Codex payloads, the runner manifest and checksum, the installed-cache proofs, and the payload/release/zero-Bash evidence hashes. An adversarial review of the relocation also confirmed and fixed a status-mapping defect: a missing repo-side dispatcher now reports `missing_prerequisite` instead of `input_error`, with a regression test, and the dispatcher maps its own unexpected exceptions to exit code 4 (`subprocess_failure`). Claude source payload tree hash is now `6139fa87858bbe8ddba02c1c1abe5c43646fe07df02a6306526558fcef7f03c6` and Codex `d332ed2327683fcb9aab83d7e89349c7afdce97b8096f7b0000bdc57b1c12f0e`. |
| Focused checks after suite-gate shell-dispatch relocation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `54/54 passed` (adds the missing-dispatcher `missing_prerequisite` regression test); `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-runner.py` -> `10/10 passed`; `python3 tests/speckit-pro/run-layer-scripts.py --layer 1` -> `24/24 passed` and `--layer 4` -> `17/17 passed`; `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`; runner default-suite request `ok` with `6/6` passed; zero-Bash guard `ok` with zero blocking findings and zero script files; XPLAT-007 and XPLAT-008 release-readiness requests `ok`; committed-dist payload drift check `ok`; `git diff --check` passed. |
| Full suite after suite-gate shell-dispatch relocation | `bash tests/speckit-pro/run-all.sh` passed `2014/2014`; L4 is `502/502` and Layer 5 tool scoping passed `186/186`. |
| Final review gate | Pending fresh RepoPrompt and GitHub review-state verification after the tenth remediation. |

---

## Project Structure Reference

```text
specs/xplat-009-plugin-source-and-payload-bash-eradication/
  SPEC-MOC.md
  spec.md
  plan.md
  tasks.md
  research.md
  data-model.md
  contracts/
  checklists/
docs/ai/specs/.process/
  XPLAT-009-design-concept.md
  XPLAT-009-workflow.md
```

---

## Lessons Learned

### What Worked Well

- Zero-Bash proof worked best when source, generated payloads, and bounded
  installed-cache evidence were checked together instead of treating payloads as
  manually reviewed output.
- Updating Layer 1 validators away from deleted plugin Bash libraries exposed
  the remaining true harness issues quickly.

### Challenges Encountered

- The post-implementation run initially stopped too early. The resumed run
  restored every canonical post item in the visible plan and autopilot state.
- The XPLAT-004/XPLAT-008 runner guard assumed generated payload and active skill
  surfaces should not change. XPLAT-009 intentionally owns those surfaces, so
  the guard now allows declared XPLAT-009 paths while requiring changed `.sh`
  paths to be deletions.
- The RepoPrompt review-agent tool failed with `Transport closed`, so review was
  completed in the parent session.

### Patterns to Reuse

- Keep one atomic PR when a plugin-source deletion, Python ownership migration,
  payload rebuild, and release-readiness proof must land together to keep the
  install/runtime surface coherent.
- For future no-shell work, require both source inventory proof and payload/cache
  proof before PR body generation.
- Preserve native operator UAT boundaries explicitly so release-readiness work
  does not overclaim platform support.
