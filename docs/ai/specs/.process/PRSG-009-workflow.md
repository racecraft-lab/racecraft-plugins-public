# SpecKit Workflow: PRSG-009 - Multi-PR emission

**Template Version**: 1.0.0
**Created**: 2026-06-10
**Purpose**: Execute PRSG-009, replacing single-PR post-implementation output with ordered multi-PR emission from the PRSG-008 layer plan.

---

## How to Use This Workflow

1. Run the phases in order from inside the `prsg-009-multi-pr-emission` worktree.
2. Re-read `docs/ai/specs/.process/PRSG-009-design-concept.md` before each phase when a prompt depends on scoping decisions.
3. Keep workflow progress, reviewability records, and post-implementation PR emission evidence in this file.
4. Do not run Grill Me during autopilot. Clarifications after setup go through `/speckit-clarify`.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during `$speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/PRSG-009-design-concept.md
```

Load-bearing decisions:

- Branch topology: Style B incremental stack.
- Slice ordering: consume PRSG-008 `plan-layers.sh` dependency order.
- Emission timing: create PRs after full implementation and verification.
- Failure behavior: stop before opening a known-bad slice PR; record evidence in the workflow and `autopilot-state.json`.
- MOC state: update generated PR rows after each successfully created PR.
- Restack: prefer `gh-stack` when available, otherwise use a deterministic `restack.sh` fallback.
- Scope boundary: no new review-routing heuristics; PRSG-010 owns deeper routing/backstop work.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Complete | Created spec.md with 20 FRs, 3 user stories, 9 acceptance scenarios, and 0 clarification markers |
| Clarify | `/speckit-clarify` | Complete | Resolved state, PRS manifest, branch/PR, scoped verification, and restack contracts; G2 passed with 0 markers |
| Plan | `/speckit-plan` | Complete | Created plan, research, data model, quickstart, and 4 JSON contracts; G3 passed |
| Checklist | `/speckit-checklist` | Pending | Run focused checks for API/contracts, state management, error handling, and CI/release flow |
| Tasks | `/speckit-tasks` | Pending | Generate small story-oriented tasks with Layer 4, Layer 7 if needed, and Layer 8 parity coverage |
| Analyze | `/speckit-analyze` | Pending | Verify no drift from design concept and roadmap dependencies |
| Implement | `/speckit-implement` | Pending | Implement TDD-first with scoped tests and Codex parity |

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories cover Emit N PRs, MOC/restack, and branch topology/CI mapping |
| G2 | After Clarify | Passed: state schema, branch naming, PR creation order, CI/restack, and failure recovery are explicit |
| G3 | After Plan | Architecture honors PRSG-008/003/001 dependencies and constitution gates |
| G4 | After Checklist | All checklist gaps are resolved or explicitly scoped out |
| G5 | After Tasks | Tasks cover implementation, docs, tests, parity, and verification |
| G6 | After Analyze | No critical drift between roadmap, design concept, spec, plan, and tasks |
| G7 | After Implementation | Relevant test layers pass and generated PR emission evidence is recorded |

---

## Prerequisites

### Constitution Validation

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin Structure Compliance | Keep plugin files under the established `speckit-pro/` layout and mirrored dist surfaces when required | `bash tests/speckit-pro/run-all.sh --layer 1` |
| Script Safety | New or changed bash scripts use `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, and executable permissions | Layer 1 script validation plus targeted Layer 4 tests |
| Semantic Versioning | Do not manually edit plugin versions; release-please owns version bumps | Review plugin manifests and release files |
| Test Coverage Before Merge | Add Layer 4 tests for new scripts, Layer 8 parity for Codex mirrors, and Layer 7 only if dispatch graph behavior changes | `bash tests/speckit-pro/run-all.sh` or focused layers during development |
| Conventional Commits | Setup and implementation commits use conventional commit format | `git log --oneline -1` and CI PR title validation |
| KISS, Simplicity & YAGNI | Consume PRSG-008 layer plans; do not add new review-routing heuristics in PRSG-009 | Plan review and Analyze phase |

**Constitution Check:** Plan constitution check passed. Implementation constitution gates remain pending.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | PRSG-009 |
| **Name** | Multi-PR emission |
| **Branch** | `prsg-009-multi-pr-emission` |
| **Dependencies** | PRSG-008 layer planner, PRSG-003 MOC PR table, PRSG-001 exhaust relocation |
| **Enables** | PRSG-010 hardening/backstop and monster-epic routing |
| **Priority** | P1 |
| **Budget** | Approximately 450 LOC |
| **Tests** | Layer 4, Layer 7 if new dispatch graph behavior is introduced, Layer 8 parity |

### Roadmap Scope Summary

- Rewrite post-implementation section 3.2 from one `gh pr create` to N PRs in dependency order.
- Use Style B incremental stack branch topology.
- Generate per-slice PR bodies and attach each slice's scoped tests.
- Update the spec-MOC generated PR table with `slice -> PR# -> SHA` on each PR.
- Handle squash-only restack using `gh-stack` when available and a deterministic fallback helper otherwise.
- Map CI so slice PRs run scoped tests and the full regression suite gates only the base or final merge point.

### Success Criteria Summary

- [ ] Given a layer plan with multiple slices, post-implementation creates ordered PRs for each slice instead of one flattened PR.
- [ ] Given a successful PR creation, the spec MOC generated PR table records the slice, PR number, and SHA before continuing.
- [ ] Given a slice scoped-test failure, emission stops before opening that slice PR and records failure evidence.
- [ ] Given a squash merge of an earlier slice, operators can restack the remaining stack with `gh-stack` or the fallback helper.
- [ ] Given Codex mirrored surfaces change, Layer 8 parity remains green.

---

## Phase 1: Specify

**When to run:** Start of PRSG-009. Focus on what behavior changes for users and maintainers, not implementation mechanics. Output: `specs/prsg-009-multi-pr-emission/spec.md`.

### Specify Prompt

```bash
/speckit-specify

## Feature: PRSG-009 multi-PR emission

### Problem Statement
The current post-implementation flow flattens implementation output into one PR even when PRSG-008 has produced multiple reviewable slices. This defeats the PR-size governance goal because reviewers still see one large review surface.

### Users
- Maintainers reviewing SpecKit-generated implementation work.
- Autopilot operators who need deterministic multi-PR emission, resume behavior, and recovery evidence.
- Future specs that rely on PRSG-009 to turn layer plans into reviewable stacks.

### User Stories
1. As a maintainer, I want the autopilot to create N ordered PRs from the PRSG-008 layer plan so each review unit stays small and dependency-aware.
2. As a maintainer, I want the spec MOC PR table updated after each successful PR so resume and review navigation are durable.
3. As a maintainer, I want branch topology, scoped CI mapping, and restack behavior defined so squash-merge review loops remain operable.

### Constraints
- Consume PRSG-008 `plan-layers.sh` output as the ordering source.
- Use Style B incremental stack branches.
- Create slice PRs only after full implementation and verification.
- Stop before opening a failed slice PR and record failed scoped-test evidence in the workflow and `autopilot-state.json`.
- Keep PRSG-009 scoped to emission/restack behavior; do not add new review-routing heuristics.
- Preserve Codex parity for mirrored skill/reference changes.

### Out of Scope
- New atomicity or slicing heuristics; PRSG-010 owns deeper backstop/routing changes.
- Manual-only PR table updates.
- Opening known-bad draft PRs for failed slices.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 20 |
| User Stories | 3 |
| Acceptance Criteria | 9 acceptance scenarios |

### Files Generated

- [x] `specs/prsg-009-multi-pr-emission/spec.md`

---

## Phase 2: Clarify

**When to run:** After Specify if state, branch naming, or recovery behavior can be interpreted multiple ways.

### Clarify Prompts

#### Session 1: State and Resume Contract

```bash
/speckit-clarify Focus on state and resume behavior: exact `autopilot-state.json` keys for slice PR emission, failed scoped-test evidence, created PR records, and recovery after partial emission.
```

#### Session 2: Branch and PR Contract

```bash
/speckit-clarify Focus on branch and PR contracts: branch naming for incremental stacks, PR base/head selection, per-slice PR body inputs, and how the spec MOC `slice -> PR# -> SHA` rows are generated.
```

#### Session 3: CI and Restack Contract

```bash
/speckit-clarify Focus on CI and restack behavior: scoped tests per slice PR, full-suite gate on base/final merge, `gh-stack` detection, and fallback `restack.sh` command contract.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | State and resume contract | 5 | Accepted `multi_pr_emission` top-level state, PRS manifest schema v2 for reviewer rows, state-before-MOC persistence order, branch/PR reconciliation by expected head/base, and compact failed-slice evidence with logs by path. |
| 2 | Branch and PR contract | 5 | Accepted `<feature-branch>/<NN>-<slice-id>` branch names, explicit PR base/head/body-file arguments, optional `--slice-packet`, GitHub head/base reconciliation, and schema v2 SHA display as `merged_sha` when available else `head_sha`. |
| 3 | CI and restack contract | 5 | Accepted scoped verification evidence without Actions changes, structured `scoped_verification.commands[]`, optional `gh-stack` for safe restack/sync only, dry-run-first `restack.sh`, and full-suite evidence before emission plus after restack. |

---

## Consensus Resolution Log

| Phase | Item | Round | Routed Categories | Outcome | Analysts Used |
|-------|------|-------|-------------------|---------|---------------|
| Clarify Session 1 | PRS manifest schema | 1 | codebase, spec | Use `.process/prs.json` schemaVersion 2 for bounded reviewer-facing MOC rows while keeping v1 backward-compatible; keep resume-only details in `autopilot-state.json`. | codebase-analyst, spec-context-analyst |
| Clarify Session 2 | Open PR SHA display | 1 | codebase, spec | SchemaVersion 2 PRS rows display `head_sha` while open and prefer `merged_sha` after merge; open PR heads must not be written into `merged_sha`. | codebase-analyst, spec-context-analyst |
| Clarify Session 3 | Scoped CI semantics | 1 | codebase, spec | Treat scoped CI as recorded scoped verification evidence in slice packets/PR bodies/MOC evidence pointers/workflow/state; do not modify `.github/workflows/pr-checks.yml` in PRSG-009. | codebase-analyst, spec-context-analyst |
| Clarify Session 3 | gh-stack usage | 1 | domain, codebase | Use `gh-stack` only when safely detected for restack/sync of existing active stacks; keep explicit `gh pr create --base --head --body-file` as the emission path. | domain-researcher, codebase-analyst |

---

## Phase 3: Plan

**When to run:** After spec and clarifications are stable. Output: `specs/prsg-009-multi-pr-emission/plan.md`.

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Runtime: Bash and Markdown in the existing `speckit-pro` plugin.
- CLI tools: `git`, `gh`, `jq`; optional `gh-stack` for restack convenience.
- Test harness: shell-based Layer 1, Layer 4, Layer 5, Layer 8 parity; Layer 7 only if dispatch graph behavior changes.
- State surfaces: workflow file, `autopilot-state.json`, spec MOC generated PR table, and git branches.

## Constraints
- Reuse PRSG-008 layer plan output and do not duplicate slice-routing heuristics.
- Keep post-implementation changes in the existing autopilot reference/script surfaces.
- Preserve Claude and Codex parity for mirrored skill/reference files.
- Keep full regression verification separate from per-slice scoped tests.

## Architecture Notes
- Post-implementation section 3.2 should iterate layer-plan slices in dependency order and create one PR per slice.
- Each slice branch should be based on the previous slice branch to form an incremental stack.
- `generate-pr-body.sh` may need per-slice inputs or mode flags; keep behavior backward-compatible for single-PR specs.
- The generated PRS table in `SPEC-MOC.md` should be updated after each successful PR creation.
- Failure before opening a slice PR must persist enough state for resume without duplicating earlier PRs.
- `restack.sh` should be deterministic, script-safe, and tested if added.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Technical context, execution flow, declared file operations, and verification gates |
| `research.md` | Complete | Restack, gh-stack, scoped verification, and PRS v2 tradeoffs |
| `data-model.md` | Complete | Multi-PR emission state, slice packet, PRS v2, and restack entities |
| `contracts/` | Complete | 4 JSON schemas: state, slice packet, PRS v2, restack output |
| `quickstart.md` | Complete | Operator flow for emission, resume, scoped evidence, and restack |

### Plan Reviewability Estimate

| Field | Value |
|-------|-------|
| Status | pass |
| Projected production LOC | 0 |
| Declared production files | 0 |
| Declared total entries | 6 |
| Note | Advisory estimate under-counts plugin shell paths by current estimator rules; accepted because G3 is advisory-only and implementation verification owns actual diff risk. |

---

## Phase 4: Domain Checklists

**When to run:** After Plan. Run focused checklists against `spec.md` and `plan.md`.

### Recommended Domains

#### 1. API/contracts Checklist

Why this domain: PRSG-009 changes script/CLI-style contracts for PR body generation, restacking, and layer-plan consumption.

```bash
/speckit-checklist api-contracts

Focus on PRSG-009 requirements:
- Per-slice PR body inputs and outputs.
- `restack.sh` invocation, exit codes, and failure output.
- Layer-plan schema consumed from PRSG-008.
- Spec MOC generated PR table row shape.
```

#### 2. State-management Checklist

Why this domain: Partial multi-PR emission must be resumable without duplicate PRs or stale MOC rows.

```bash
/speckit-checklist state-management

Focus on PRSG-009 requirements:
- `autopilot-state.json` slice PR records.
- Workflow file evidence after successful and failed slices.
- Resume behavior after process interruption.
- Idempotency when earlier PRs already exist.
```

#### 3. Error-handling Checklist

Why this domain: The highest-risk path is a slice failing scoped tests or PR creation halfway through a stack.

```bash
/speckit-checklist error-handling

Focus on PRSG-009 requirements:
- Scoped-test failure before opening a PR.
- `gh pr create` failure after branch creation.
- MOC update failure after PR creation.
- Restack failure after squash merge.
```

#### 4. CI/release-flow Checklist

Why this domain: PRSG-009 changes how scoped tests and full regression tests map to PRs in an incremental stack.

```bash
/speckit-checklist ci-release-flow

Focus on PRSG-009 requirements:
- Scoped tests on each slice PR.
- Full regression gate only on the base or final merge point.
- Later-slice tests must not block earlier slice PRs before their code merges.
- GitHub branch and PR base behavior for stacked branches.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| api-contracts | Pending | Pending | |
| state-management | Pending | Pending | |
| error-handling | Pending | Pending | |
| ci-release-flow | Pending | Pending | |

---

## Phase 5: Tasks

**When to run:** After checklists complete and gaps are resolved. Output: `specs/prsg-009-multi-pr-emission/tasks.md`.

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Use small, testable chunks with explicit FR references.
- Organize by user story, not by technical layer.
- Mark independent tasks with [P].
- Include tests before implementation for new script behavior.

## Implementation Phases
1. Foundation: contracts, fixtures, backward-compatible state envelope.
2. US1: emit N PRs from PRSG-008 layer plan in incremental stack order.
3. US2: update generated PR table and per-slice PR bodies.
4. US3: branch topology, scoped CI mapping, and restack helper.
5. Polish: docs, parity, dist mirrors, and final verification.

## Constraints
- Layer 4 tests for any new or changed bash scripts.
- Layer 8 parity for Claude/Codex mirrored skill/reference changes.
- Layer 7 only if new agent/dispatch graph behavior is introduced.
- Do not add PRSG-010 review-routing heuristics.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | Pending |
| **Phases** | Pending |
| **Parallel Opportunities** | Pending |
| **User Stories Covered** | Pending |

---

## Atomicity Route

The autopilot records the read-only atomicity classifier decision here after Tasks/G5. PRSG-009 itself must consume the PRSG-008 layer plan and must not add new routing heuristics.

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | Pending | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, or `out-of-scope` |
| **Releasable** | Pending | `true` or `false` based on release safety |
| **Signals** | Pending | Decisive classifier findings |
| **Warnings** | Pending | Release-safety warnings |

To produce the decision, run:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/prsg-009-multi-pr-emission
```

---

## Phase 6: Analyze

**When to run:** Always after generating tasks.

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Constitution alignment: script safety, test coverage, KISS/YAGNI, and conventional commits.
2. Coverage gaps: every PRSG-009 user story and roadmap bullet has tasks.
3. Consistency: spec, plan, tasks, design concept, and roadmap all agree on Style B incremental stack, PRSG-008 ordering, failure stop behavior, MOC PR updates, and restack fallback.
4. Parity: Claude and Codex mirrored surfaces are both covered where changed.
5. Scope control: no new review-routing heuristics or PRSG-010 backstop behavior slipped into PRSG-009.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| Pending | Pending | Pending | Pending |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated, analyzed, and approved.

### Implement Prompt

```bash
/speckit-implement

## Approach: TDD-First

For each task:
1. RED: Add or update focused tests first.
2. GREEN: Implement the smallest behavior change that passes.
3. REFACTOR: Simplify while keeping tests green.
4. VERIFY: Run focused layer tests, then the repo suite needed for the touched surfaces.

### Pre-Implementation Setup
1. Confirm branch: `git rev-parse --abbrev-ref HEAD` should be `prsg-009-multi-pr-emission`.
2. Confirm clean state before implementation edits: `git status --short`.
3. Review `docs/ai/specs/.process/PRSG-009-design-concept.md`.
4. Run focused existing checks for touched surfaces before large edits when useful.

### Implementation Notes
- Modify `speckit-autopilot/references/post-implementation.md` and Codex mirror surfaces in lockstep when runtime docs change.
- Extend `generate-pr-body.sh` only with backward-compatible options or clear single-PR fallback behavior.
- Add `restack.sh` only if Plan keeps the fallback helper; it must be script-safe and Layer 4 tested.
- Keep generated dist mirrors synchronized if source plugin files are mirrored there by the repo workflow.
- Record PR emission state in both the workflow and `autopilot-state.json`.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation | Pending | 0 | |
| 2 - US1 Emit N PRs | Pending | 0 | |
| 3 - US2 MOC + restack records | Pending | 0 | |
| 4 - US3 Branch topology + CI mapping | Pending | 0 | |
| 5 - Polish | Pending | 0 | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in `tasks.md`.
- [ ] Layer 4 tests pass for changed scripts.
- [ ] Layer 8 parity passes for mirrored Codex/Claude surfaces.
- [ ] Layer 1 structural checks pass.
- [ ] Full relevant suite passes before PR creation.
- [ ] Spec MOC generated PR table records successful slice PRs.
- [ ] Failed slice behavior records evidence and stops before opening known-bad PRs.
- [ ] Manual verification notes are recorded when GitHub PR creation/restack behavior is exercised.

---

## Lessons Learned

### What Worked Well

- Pending.

### Challenges Encountered

- Pending.

### Patterns to Reuse

- Pending.

---

## Project Structure Reference

```text
racecraft-plugins-public/
├── speckit-pro/
│   ├── skills/
│   │   ├── speckit-autopilot/
│   │   │   ├── references/
│   │   │   └── scripts/
│   │   └── speckit-scaffold-spec/
│   ├── codex-skills/
│   └── tests/
├── tests/speckit-pro/
│   ├── layer1-structural/
│   ├── layer4-scripts/
│   └── layer8-codex-parity/
├── docs/ai/specs/
│   ├── .process/PRSG-009-design-concept.md
│   ├── .process/PRSG-009-workflow.md
│   └── pr-size-governance-technical-roadmap.md
└── specs/prsg-009-multi-pr-emission/
    └── SPEC-MOC.md
```

---

Template based on SpecKit best practices. This workflow has been populated for PRSG-009 and is ready for `$speckit-autopilot`.
