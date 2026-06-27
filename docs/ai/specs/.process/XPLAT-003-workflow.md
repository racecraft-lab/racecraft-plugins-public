# SpecKit Workflow: XPLAT-003 - Supply-Chain Security and Consumer Trust Model

**Template Version**: 1.0.0
**Created**: 2026-06-27
**Purpose**: Prepare XPLAT-003 for autonomous execution from the cross-platform plugin runtime roadmap, XPLAT-001 inventory rubric, XPLAT-002 runtime decision, and setup Grill Me decisions.

---

## How to Use This Workflow

Run this workflow from the XPLAT-003 worktree:

```bash
$speckit-autopilot docs/ai/specs/.process/XPLAT-003-workflow.md
```

This file is already populated for XPLAT-003. Do not replace it with the generic workflow template.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during `$speckit-scaffold-spec XPLAT-003`.
The full Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/XPLAT-003-design-concept.md
```

Re-read the design concept before each phase. It is the source of truth for setup decisions:

- Choose a practical first-release supply-chain baseline, not a maximal controls program.
- Require source-to-dist integrity evidence for generated Claude/Codex payloads.
- Require published checksums and consumer-local checksum verification for first release.
- Evaluate signatures, SBOM, and provenance as deferred hardening unless evidence proves one must ship before launch.
- Require vulnerability scans that fail on actionable high/critical findings, with documented exception handling.
- Limit public docs and release-note wording to controls that are implemented and verified.
- Split downstream ownership by surface: XPLAT-004 for runner/source controls, XPLAT-007 for cutover/generated-payload checks, and release/docs surfaces where they naturally belong.
- Keep this as one decision spike. The advisory slice estimate is `{"estimated_loc":0,"suggested_slices":1,"status":"ok"}`.

> Grill Me is human-in-the-loop only. It is not part of the autopilot loop. Once this workflow starts, clarifications happen through `$speckit-clarify` and consensus, never through grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `$speckit-specify` | Complete | Created decision-spike spec and requirements checklist; G1 passed with 0 clarification markers |
| Clarify | `$speckit-clarify` | In Progress | Resolve exact control boundaries, evidence formats, and claim wording |
| Plan | `$speckit-plan` | Pending | Produce research, policy/data model, contracts, quickstart, and handoff |
| Checklist | `$speckit-checklist` | Pending | Recommended domains: security, integration, reliability |
| Tasks | `$speckit-tasks` | Pending | Generate decision-spike tasks only; no runner implementation |
| Analyze | `$speckit-analyze` | Pending | Check drift across roadmap, design concept, XPLAT-001, XPLAT-002, spec, plan, and tasks |
| Implement | `$speckit-implement` | Pending | Record final decision artifacts and verification evidence |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | Scope is security/trust decision only; no runner build, helper port, payload rebuild, or public native-support claim |
| G2 | After Clarify | First-release vs deferred controls, checksum format, scan policy, consumer verification, and claim boundaries are unambiguous |
| G3 | After Plan | Plan uses XPLAT-001 supply-chain rubric, XPLAT-002 Go runner handoff, and records reviewability warning |
| G4 | After Checklist | All true requirement-quality gaps are remediated or explicitly out of scope |
| G5 | After Tasks | Tasks cover research, control matrix, acceptance gates, downstream ownership, public-claim audit, and verification |
| G6 | After Analyze | No critical drift remains between roadmap, design concept, prior XPLAT artifacts, spec, plan, and tasks |
| G7 | After Implementation | Decision record, control contract, handoff, spec-map check, diff hygiene, and relevant local validation pass |

---

## Prerequisites

### Worktree and Branch

- Worktree: `.worktrees/xplat-003-supply-chain-security-and-consumer-trust-model`
- Branch: `codex/xplat-003-supply-chain-security-and-consumer-trust-model`
- Contract marker: `specs/xplat-003-supply-chain-security-and-consumer-trust-model/SPEC-MOC.md`
- Design concept: `docs/ai/specs/.process/XPLAT-003-design-concept.md`

Before starting:

```bash
git rev-parse --abbrev-ref HEAD
git status --short
specify preset resolve spec-template
specify preset resolve plan-template
specify preset resolve tasks-template
```

Expected branch is `codex/xplat-003-supply-chain-security-and-consumer-trust-model`. Preset resolution should use `.specify/presets/speckit-pro-reviewability/` unless a deliberate higher-priority override exists.

### Constitution Validation

| Principle | XPLAT-003 Requirement | Verification |
|-----------|-----------------------|--------------|
| Plugin Structure Compliance | Do not add runner artifacts, generated payload changes, or plugin invocation changes in this decision spec | `git diff --name-only` review |
| Script Safety | Any proposed future shell/release commands must be recorded as policy or verification commands only; no new helper implementation lands here | command review and no new shipped helper |
| Test Coverage Before Merge | Static verification must prove the decision record, control matrix, spec-map freshness, and no placeholder drift | focused commands listed below |
| Conventional Commits | Setup and implementation commits must use conventional commit text | commit/PR review |
| KISS, Simplicity, YAGNI | Choose the minimum first-release controls that make public trust claims truthful; defer heavyweight controls unless justified | plan complexity table and decision record |

### Existing Source Truth

- Roadmap: `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
- XPLAT-001 inventory and supply-chain rubric: `docs/ai/research/cross-platform-runtime-inventory.md`
- XPLAT-002 runtime decision: `specs/xplat-002-runtime-implementation-options-contract-decision/runtime-decision.md`
- XPLAT-002 downstream handoff and implication matrix: `specs/xplat-002-runtime-implementation-options-contract-decision/handoff.md`
- Runner contract boundary: `specs/xplat-002-runtime-implementation-options-contract-decision/contracts/speckit-pro-runner-contract.md`
- Product requirement: `docs/prd-cross-platform-plugin-runtime.md`
- Release automation context: `.github/workflows/release.yml`, `.github/workflows/pr-checks.yml`, `release-please-config.json`, `.release-please-manifest.json`
- Payload source and generated mirrors: `speckit-pro/**`, `dist/claude/speckit-pro/**`, `dist/codex/speckit-pro/**`
- Public docs claim surfaces for later audit: `docs-site/src/content/docs/**`, `speckit-pro/README.md`, plugin manifests, marketplace manifests, release notes/changelog

### Reviewability Budget

Setup gate output:

```json
{
  "mode": "setup",
  "status": "warn",
  "pass": true,
  "reviewable_loc": 250,
  "production_files": 4,
  "total_files": 10,
  "primary_surface_count": 2,
  "primary_surfaces": [
    "docs/process",
    "harness/adapter"
  ],
  "greenfield": false,
  "thresholds": {
    "warn": {
      "reviewable_loc": 400,
      "production_files": 6,
      "total_files": 15,
      "primary_surfaces": 1
    },
    "block": {
      "reviewable_loc": 800,
      "production_files": 8,
      "total_files": 25,
      "primary_surfaces": 1
    }
  },
  "exception_honored": false,
  "exception_class": null,
  "exceptions": {
    "accepted": [],
    "rejected": []
  },
  "warnings": [
    "primary surfaces 2 exceeds warn threshold 1"
  ],
  "blockers": []
}
```

Record this warning in `plan.md`. It does not block setup.

### Phase 0 Preflight Results

| Check | Result | Evidence |
|-------|--------|----------|
| SpecKit CLI | Pass | `command -v specify` returned `/Users/fredrickgabelmann/.local/bin/specify` |
| Branch/worktree | Pass | Created worktree on `codex/xplat-003-supply-chain-security-and-consumer-trust-model` from `origin/main` |
| XPLAT-002 merge state | Pass | `main` contains merge commit `fff4d6b5` for PR #266; roadmap and MOC status now mark XPLAT-002 complete and XPLAT-003 in progress |
| Reviewability setup gate | Warn/pass | Two primary surfaces (`docs/process`, `harness/adapter`), no blockers |
| Grill Me | Complete | 7 questions; one decision spike accepted |
| Presets | Installed/refreshed | `ensure-reviewability-preset.sh` reported `status: installed`, changed `plan-template` |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | XPLAT-003 |
| **Name** | Supply-Chain Security and Consumer Trust Model |
| **Branch** | `codex/xplat-003-supply-chain-security-and-consumer-trust-model` |
| **Feature directory** | `specs/xplat-003-supply-chain-security-and-consumer-trust-model` |
| **Dependencies** | XPLAT-001 complete; XPLAT-002 merged on `main` via PR #266 |
| **Enables** | XPLAT-004, XPLAT-007 |
| **Priority** | P1 |

### Success Criteria Summary

- XPLAT-004 knows which first-release controls must be built into the Go runner source, build inputs, artifacts, and preflight metadata.
- XPLAT-007 knows which generated payload integrity, release readiness, and public claim gates must pass before cutover.
- The decision record separates first-release requirements from deferred hardening for checksums, signatures, SBOM, provenance, vulnerability scanning, generated-payload integrity, and consumer verification.
- Public docs and release-note wording is bounded to implemented, verified controls only.
- No runner implementation, helper port, generated-payload rebuild, or public native-support claim changes land in XPLAT-003.

---

## Phase 1: Specify

**When to run:** At the start of XPLAT-003. Focus on what the supply-chain and consumer-trust model must decide, not on implementing the controls. Output: `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`

### Specify Prompt

```bash
$speckit-specify

## Feature: Supply-Chain Security and Consumer Trust Model

### Problem Statement
XPLAT-002 selected a Go native binary runner and the `speckit-pro-runner` command contract, but deliberately did not choose checksum, signature, SBOM, provenance, vulnerability-scan, generated-artifact, or consumer-local verification controls. XPLAT-003 must choose the practical first-release security baseline and the deferred hardening backlog before XPLAT-004 builds the runner and before XPLAT-007 can make public release claims.

### Users
- Maintainers deciding what the project must verify before publishing native runner artifacts.
- Implementers of XPLAT-004 who need exact runner/source/artifact controls and acceptance gates.
- Implementers of XPLAT-007 who need generated-payload integrity gates and truthful docs/release-note boundaries.
- Plugin consumers who need to know what they can verify locally after install.

### User Stories
1. As a maintainer, I can read one decision record that distinguishes first-release controls from deferred hardening for the Go native runner.
2. As an implementer, I can see which controls belong to XPLAT-004, XPLAT-007, release automation, and public documentation.
3. As a consumer or reviewer, I can understand what local verification is possible and which trust guarantees are intentionally not claimed.

### Constraints
- Use the XPLAT-001 supply-chain rubric and XPLAT-002 Go-native-binary implication matrix as source truth.
- First-release baseline from Grill Me: pinned Go/release inputs, vulnerability scan policy, generated-payload integrity, checksums, consumer verification, and truthful claims.
- Generated Claude/Codex payload integrity must include a source-to-dist gate.
- First-release binary artifact integrity must include published checksums and consumer-local checksum verification.
- Vulnerability scans must fail on actionable high/critical findings, with documented exception handling.
- Public docs and release notes may claim only implemented and verified controls; do not claim signing, provenance, reproducible builds, audit, or native support before those are real.
- Assign controls to the downstream spec that owns the surface.

### Out of Scope
- Building the Go runner or adding `scripts/speckit-pro-runner`.
- Porting helpers or changing active invocation paths.
- Rebuilding generated payloads.
- Implementing CI/release automation changes.
- Selecting the runtime independently of XPLAT-002.
- Formal third-party security audit procurement.
- Public native Windows/macOS/Linux support claims before XPLAT-007 UAT.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 18 |
| User Stories | 3 |
| Acceptance Criteria | 9 acceptance scenarios; 9 success criteria |

### Files Generated

- [x] `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`
- [x] `specs/xplat-003-supply-chain-security-and-consumer-trust-model/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** Spec has areas open to interpretation. Maximum 5 targeted questions per session.

### Clarify Prompts

#### Session 1: First-release control boundaries

```bash
$speckit-clarify Focus on first-release control boundaries: confirm the minimum controls required before public cutover, which controls are deferred hardening, and what evidence can move signatures, SBOM, or provenance from deferred to first-release required.
```

#### Session 2: Artifact integrity and consumer verification

```bash
$speckit-clarify Focus on artifact integrity and consumer verification: define checksum file naming, checksum algorithm, artifact manifest fields, generated payload source-to-dist evidence, runner runtime-info/preflight requirements, and the local consumer verification command shape.
```

#### Session 3: Vulnerability policy and claim wording

```bash
$speckit-clarify Focus on vulnerability policy and public claims: define actionable high/critical finding criteria, exception record requirements, scan evidence retention, release-blocking behavior, and exact docs/release-note claim boundaries for implemented versus unimplemented controls.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | First-release control boundaries | Pending | |
| 2 | Artifact integrity and consumer verification | Pending | |
| 3 | Vulnerability policy and claim wording | Pending | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/xplat-003-supply-chain-security-and-consumer-trust-model/plan.md`

### Plan Prompt

```bash
$speckit-plan

## Tech Stack and Runtime Context
- Repository: Claude Code and Codex plugin marketplace with source under `speckit-pro/` and generated payloads under `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`.
- Selected runtime from XPLAT-002: Go native executable packaged as small per-platform binaries.
- Runner contract: `speckit-pro-runner`, default payload-relative path `scripts/speckit-pro-runner`, JSON stdin/stdout, structured stderr diagnostics, explicit exit-code map, typed paths, shell-disabled subprocess rules, runtime-info/preflight.
- Current release automation: release-please plus GitHub Actions workflows. XPLAT-003 records required controls and acceptance gates; it does not implement CI changes.

## Constraints
- One decision spike, not implementation.
- Use the XPLAT-001 supply-chain rubric: dependency policy, generated payload integrity, vulnerability scanning, provenance/attestation options, checksums/signatures, SBOM feasibility, consumer-local verification, release automation, and documentation truthfulness.
- Use the XPLAT-002 handoff: Go native binary is selected; checksums, signatures, SBOM/provenance, vulnerability scanning, generated-payload integrity, and consumer-local verification remain undecided until this spec.
- First-release baseline selected by Grill Me: practical baseline with source-to-dist gate, checksums now, actionable high/critical scan failures, version+checksum consumer verification, strict implemented-claims-only docs, and split ownership.
- Record the setup reviewability warning: two primary surfaces, no blockers.

## Architecture Notes
- Produce a decision record with a control matrix: first-release required, deferred hardening, explicitly not claimed, owner spec, evidence source, and acceptance gate.
- Treat checksums as first-release required. Evaluate signatures, SBOM, and provenance explicitly, but leave them deferred unless evidence justifies promoting them.
- Define generated payload integrity as source-to-dist evidence that XPLAT-007 can run before cutover.
- Define vulnerability scan policy in terms of actionable high/critical findings and documented exceptions.
- Define consumer-local verification in terms of runner version/preflight plus checksum comparison; do not imply marketplace-enforced signatures unless implemented.
- Assign runner/source/artifact controls to XPLAT-004, generated payload cutover to XPLAT-007, and release/docs controls to the downstream surface that owns them.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Pending | Technical context, decision method, constitution checks, and reviewability warning |
| `research.md` | Pending | Control evaluation and rationale |
| `data-model.md` | Pending | Control, artifact, evidence, exception, and claim-boundary entities |
| `contracts/` | Pending | Supply-chain control record and consumer verification contract if useful |
| `quickstart.md` | Pending | Reviewer path and verification commands |

---

## Phase 4: Domain Checklists

**When to run:** After `$speckit-plan`, validate both spec and plan together.

### Recommended Domains

#### 1. Security Checklist

Why: XPLAT-003 selects the security baseline for native runner artifacts and public trust claims.

```bash
$speckit-checklist security

Focus on XPLAT-003 requirements:
- First-release versus deferred control boundaries
- Checksum, vulnerability scanning, generated-payload integrity, and consumer verification requirements
- Public claim restrictions for signing, provenance, reproducible builds, audits, and native platform support
- Pay special attention to: controls that are described as implemented before any downstream spec actually implements them
```

#### 2. Integration Checklist

Why: The selected controls must hand off cleanly to XPLAT-004 runner work, XPLAT-007 cutover, release automation, and docs surfaces.

```bash
$speckit-checklist integration

Focus on XPLAT-003 requirements:
- Ownership split across XPLAT-004, XPLAT-007, release automation, and docs/release notes
- Generated payload source-to-dist gate and artifact metadata flow
- Runner runtime-info/preflight fields needed for consumer verification
- Pay special attention to: any control assigned to a downstream spec that lacks an acceptance gate
```

#### 3. Reliability Checklist

Why: Release gates, scan failures, checksum mismatches, and exception handling need deterministic failure behavior.

```bash
$speckit-checklist reliability

Focus on XPLAT-003 requirements:
- Vulnerability scan failure policy and exception records
- Checksum mismatch handling and consumer-facing remediation
- Evidence retention for release verification and public claim audit
- Pay special attention to: ambiguous handling of non-actionable findings, stale checksums, or partial artifact publication
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| security | Pending | Pending | Pending |
| integration | Pending | Pending | Pending |
| reliability | Pending | Pending | Pending |

---

## Phase 5: Tasks

**When to run:** After checklists complete. Output: `specs/xplat-003-supply-chain-security-and-consumer-trust-model/tasks.md`

### Tasks Prompt

```bash
$speckit-tasks

## Task Structure
- Generate small, decision-spike tasks, not runner implementation tasks.
- Cover every user story independently: maintainer control decision, implementer downstream ownership, consumer/public trust boundary.
- Include research/evidence tasks for checksums, vulnerability scanning, generated payload integrity, SBOM/signature/provenance feasibility, consumer verification, and public claim audit.
- Mark parallel-safe tasks explicitly with [P] when they can be researched or drafted independently.

## Expected Artifact Groups
1. Foundation: spec references, control taxonomy, and source evidence collection.
2. First-release control matrix: required controls, deferred hardening, non-claims, owner spec, evidence, acceptance gate.
3. Consumer/public trust contract: local verification behavior and allowed/prohibited claims.
4. Downstream handoff: exact XPLAT-004 and XPLAT-007 inputs.
5. Verification: marker counts, spec-map freshness, diff hygiene, reviewability check, and relevant shell suite.

## Constraints
- Do not build `speckit-pro-runner`.
- Do not port helpers.
- Do not rebuild generated payloads.
- Do not edit public docs to make new native support or supply-chain claims.
- Preserve the Grill Me decisions in `docs/ai/specs/.process/XPLAT-003-design-concept.md`.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | Pending |
| Phases | Pending |
| Parallel Opportunities | Pending |
| User Stories Covered | Pending |

---

## Atomicity Route

After the Tasks phase, run the read-only classifier:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/xplat-003-supply-chain-security-and-consumer-trust-model
```

| Field | Value | Meaning |
|-------|-------|---------|
| Route | Pending | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope` |
| Releasable | Pending | `true`, or `false` for a destructive-migration or concurrency-sensitive change |
| Signals | Pending | Detector findings |
| Warnings | Pending | Release-safety warnings |

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks.

### Analyze Prompt

```bash
$speckit-analyze

Focus on:
1. Drift between the roadmap, XPLAT-001 supply-chain rubric, XPLAT-002 runtime decision/handoff/contract, XPLAT-003 Design Concept, spec.md, plan.md, and tasks.md.
2. Any task that implements runner, helper-port, generated-payload rebuild, CI/release changes, or public support claims in this decision spike.
3. Missing coverage for first-release controls, deferred hardening, consumer-local verification, vulnerability exception policy, generated payload integrity, and public claim boundaries.
4. Ownership gaps where a selected control does not name the downstream spec or surface that must implement it.
5. Constitution alignment: KISS/YAGNI, test coverage before merge, conventional commit expectations, and no speculative guarantees.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| Pending | Pending | Pending | Pending |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed.

### Implement Prompt

```bash
$speckit-implement

## Approach: Decision Artifact First

For each task:
1. Read the Design Concept, roadmap section, XPLAT-001 rubric, and XPLAT-002 handoff before editing.
2. Draft the minimum decision artifact that satisfies the task.
3. Verify the artifact says what is required now, what is deferred, what is not claimed, who owns it, and how it will be verified.
4. Re-check that no runner implementation, helper port, generated payload rebuild, release automation mutation, or public support-claim change slipped in.

### Pre-Implementation Setup

```bash
git rev-parse --abbrev-ref HEAD
git status --short
specify preset resolve spec-template
specify preset resolve plan-template
specify preset resolve tasks-template
```

### Implementation Notes

- Primary deliverable should be the XPLAT-003 control decision and handoff artifacts under `specs/xplat-003-supply-chain-security-and-consumer-trust-model/`.
- Keep public-doc changes out unless the task is a non-claim audit note inside the spec artifacts.
- Use the selected runtime contract from XPLAT-002; do not reopen the runtime choice.
- Verification should include at least marker counts, spec-map freshness, `git diff --check`, and the smallest relevant shell suite. Run broader validation only if files outside the spec/process surface change.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Foundation | Pending | Pending | |
| Control decision | Pending | Pending | |
| Consumer/public trust | Pending | Pending | |
| Handoff and verification | Pending | Pending | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in `tasks.md`
- [ ] No placeholder markers remain in spec artifacts
- [ ] `bash speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh gaps specs/xplat-003-supply-chain-security-and-consumer-trust-model` passes
- [ ] `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"` passes
- [ ] `git diff --check` passes
- [ ] Relevant SpecKit shell tests pass
- [ ] Reviewability diff gate result is recorded
- [ ] PR packet is generated and validated if PR creation follows

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
docs/ai/specs/
  cross-platform-plugin-runtime-technical-roadmap.md
  .process/XPLAT-003-design-concept.md
  .process/XPLAT-003-workflow.md
docs/ai/research/
  cross-platform-runtime-inventory.md
specs/
  xplat-002-runtime-implementation-options-contract-decision/
  xplat-003-supply-chain-security-and-consumer-trust-model/
speckit-pro/
  skills/
  codex-skills/
dist/
  claude/speckit-pro/
  codex/speckit-pro/
```

Template based on SpecKit best practices and populated for XPLAT-003 from the technical roadmap, XPLAT-001/XPLAT-002 source artifacts, and the setup Grill Me interview.
