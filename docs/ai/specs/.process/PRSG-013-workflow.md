# SpecKit Workflow: PRSG-013 — Non-stopping reviewability markers

**Template Version**: 1.0.0
**Created**: 2026-06-12
**Purpose**: Reusable template for executing SpecKit workflows. Copy-paste the prompts below into your AI coding agent.

---

## How to Use This Template

1. Start autopilot with this file:

   ```bash
   $speckit-autopilot docs/ai/specs/.process/PRSG-013-workflow.md
   ```

2. Keep `docs/ai/specs/.process/PRSG-013-design-concept.md` open as the source
   of truth for the Grill Me decisions behind this scaffold.

3. Track phase status in the table below as autopilot advances.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/PRSG-013-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. The
Specify and Clarify Prompts below were populated from that interview,
so the design concept doc is the source of truth for any decision
captured during scoping.

> **Note:** Grill Me is human-in-the-loop only. It is **not** part of
> the autopilot loop. Once the workflow file is populated and autopilot
> begins, clarifications happen via `/speckit-clarify` and the
> consensus protocol — never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ⏳ Pending | |
| Clarify | `/speckit-clarify` | ⏳ Pending | Optional but recommended |
| Plan | `/speckit-plan` | ⏳ Pending | |
| Checklist | `/speckit-checklist` | ⏳ Pending | Run for each domain |
| Tasks | `/speckit-tasks` | ⏳ Pending | |
| Analyze | `/speckit-analyze` | ⏳ Pending | |
| Implement | `/speckit-implement` | ⏳ Pending | |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates (SpecKit Best Practice)

Each phase requires **human review and approval** before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
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
|-----------|-------------|--------------|
| Plugin Structure Compliance | Preserve the `speckit-pro/` authoring layout, mirrored Codex skill layout, and `tests/speckit-pro/` sibling test suite. | `bash tests/speckit-pro/run-all.sh --layer 1` |
| Script Safety | Any changed Bash script keeps `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, and clear `jq` JSON handling. | `bash -n` on touched scripts plus targeted Layer 4 tests |
| Test Coverage Before Merge | PRSG-013 requires deterministic L4 coverage and L3 functional proof of the autopilot no-stop behavior. | Targeted L4 tests, L3 functional eval evidence, then `bash tests/speckit-pro/run-all.sh` |
| KISS, Simplicity & YAGNI | Keep marker storage and subdivision logic explicit; avoid a new abstraction layer unless the plan proves it removes real complexity. | Plan Complexity Tracking plus code review |

**Constitution Check:** ✅ / ❌ (mark before proceeding to G1)

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | PRSG-013 |
| **Name** | Non-stopping reviewability markers |
| **Branch** | `prsg-013-reviewability-markers` |
| **Dependencies** | PRSG-008 layer planner; PRSG-009 multi-PR emission; PRSG-010 final backstop ordering |
| **Enables** | PRSG-012 reviewer-ready PR packet contract |
| **Priority** | P1 |

### Success Criteria Summary

- [ ] Reviewability `block` results from the post-G5 task gate and final pre-PR backstop do not stop valid autopilot implementation or PR emission.
- [ ] Autopilot persists durable PR markers derived from Foundation plus user-story boundaries in `autopilot-state.json` and workflow evidence, not in `tasks.md`.
- [ ] Implement execution and checkpointing follow marker order so downstream PR emission has per-marker evidence.
- [ ] PR emission consumes persisted markers; oversized user stories subdivide only at safe task-cluster boundaries, and hard-atomic or release-sensitive hazards collapse emission to one warned PR.
- [ ] Layer 4 fixtures and a Layer 3 functional eval prove the behavior contract.

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/prsg-013-reviewability-markers/spec.md`

### Specify Prompt

```bash
/speckit-specify Fix autopilot reviewability sizing so it never stops implementation and instead persists PR markers at Foundation/user-story boundaries for scoped PR emission.
```

#### Detailed Prompt (for complex specs)

```bash
/speckit-specify

## Feature: Non-stopping reviewability markers

### Problem Statement
Autopilot currently treats reviewability sizing as a reason to stop after task
generation or before PR creation. That is the wrong product behavior: valid specs
should continue implementing, while reviewability findings shape the PR marker plan
used for scoped PR emission.

### Users
SpecKit operators, maintainers reviewing generated PRs, and downstream agents that
need predictable PR boundaries without manual re-slicing.

### User Stories
- US1: As an operator, I can run autopilot through reviewability sizing warnings
  without implementation stopping for size alone.
- US2: As a reviewer, I get PRs scoped to Foundation setup or user-story markers
  derived from the task structure.
- US3: As an autopilot maintainer, I can verify marker planning, persistence,
  implementation ordering, and emission behavior with deterministic fixtures and
  one functional eval.

### Constraints
- Keep the stable `reviewability-gate.sh tasks` contract; change autopilot handling
  unless planning proves a new compatibility-safe mode is required.
- Do not remove correctness stops for malformed plans, failed verification, invalid
  PR packets, or unsafe output.
- Persist markers in `autopilot-state.json` and workflow evidence, not by rewriting
  `tasks.md`.
- Preserve Codex mirror parity when touching mirrored autopilot guidance.

### Out of Scope
- PRSG-012 reviewer-ready title/body validation.
- A new O5 monster-epic model.
- A full live dogfood PR emission run as the required proof.
- Changing the lower-level reviewability gate exit-code contract just to avoid stops.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | Fill after Specify |
| User Stories | Expect 3 core stories: non-stopping gates, durable markers, marker-ordered emission |
| Acceptance Criteria | Seed from the success criteria above |

### Files Generated

- [ ] `specs/prsg-013-reviewability-markers/spec.md`

### SpecKit Traceability Markers

Use these markers in spec.md for traceability through later phases:

| Marker | Purpose | Example |
|--------|---------|---------|
| `[US1]`, `[US2]` | User story reference | `[US1] User searches by query` |
| `[FR-001]` | Functional requirement | `[FR-001] API returns paginated results` |
| `[NEEDS CLARIFICATION]` | Flag for Clarify phase | `Auth method [NEEDS CLARIFICATION]` |
| `[P]` | Parallel-safe task | `[P] Can run alongside other tasks` |
| `[Gap]` | Missing coverage | `[Gap] No task covers error handling` |

---

## Phase 2: Clarify (Optional but Recommended)

**When to run:** When spec has areas that could be interpreted multiple ways. 10-20 minutes here saves hours of rework later.

**Best Practice:** Maximum 5 targeted questions per Clarify session.

### Clarify Prompts

#### Session 1: Marker Schema Focus

```bash
/speckit-clarify Focus on marker persistence: exact `autopilot-state.json` schema, workflow evidence fields, marker IDs, marker order, and how Foundation/user-story/Polish phases map to persisted PR markers.
```

#### Session 2: Subdivision and Hazard Focus

```bash
/speckit-clarify Focus on oversized marker and hazard handling: when a single user-story marker may subdivide by task clusters, when hard-atomic or release-sensitive hazards collapse emission to one PR, and what warnings must be recorded.
```

#### Session 3: Gate Boundary Focus

```bash
/speckit-clarify Focus on gate semantics: which reviewability results become non-stopping marker input, which correctness failures still stop, and how final backstop evidence flows into multi-PR emission.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/prsg-013-reviewability-markers/plan.md`

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Runtime: Bash scripts and Markdown skill guidance in `speckit-pro/`
- JSON/state: `jq`, `autopilot-state.json`, workflow evidence blocks
- GitHub/PR flow: existing `gh`-based post-implementation and multi-PR emission scripts
- Codex/Claude parity: mirror any touched `speckit-autopilot` guidance across source and Codex skill surfaces
- Testing: Layer 4 shell fixtures, Layer 3 functional eval, default `bash tests/speckit-pro/run-all.sh`

## Constraints
- Reviewability sizing must not stop implementation for a valid spec.
- Correctness and safety gates still stop.
- Keep `reviewability-gate.sh tasks` behavior stable unless the plan identifies a compatibility-safe extension with tests.
- Persist PR markers in state/workflow evidence rather than mutating `tasks.md`.
- Implement/checkpoint in marker order so PR emission does not infer scope from one mixed diff.

## Architecture Notes
- Source decisions from `docs/ai/specs/.process/PRSG-013-design-concept.md`.
- Q1/Q8: both post-G5 and final reviewability gates become non-stopping marker inputs.
- Q2/Q10: markers come from Foundation plus user-story sections; small Polish folds into the nearest sensible marker.
- Q3: hard-atomic or release-sensitive hazards may collapse emission to one PR with warnings.
- Q4: oversized user stories subdivide only when safe task-cluster boundaries exist.
- Q5/Q6: marker state lives in `autopilot-state.json` and workflow evidence; keep the gate script contract stable.
- Q9: implementation proceeds and checkpoints in marker order.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Technical context, execution flow |
| `research.md` | ⏳ | Decision rationales (if needed) |
| `data-model.md` | ⏳ | Entities and types |
| `contracts/` | ⏳ | API specifications |
| `quickstart.md` | ⏳ | Developer onboarding |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates both spec AND plan together. Run multiple times for different domains.

**Best Practice:** Don't guess which domains to check. Analyze the spec first, then generate enriched prompts with spec-specific focus areas.

### Step 1: Analyze Spec for Recommended Domains

Before running any checklists, read `spec.md` and `plan.md` and identify which domains apply. Look for these signals:

| Signal in Your Spec/Plan | Recommended Domain |
|---|---|
| API endpoints, REST routes, request/response models | **api-contracts** |
| User-facing UI, components, forms, layouts | **ux** |
| Keyboard navigation, screen readers, WCAG, ARIA | **accessibility** |
| Auth, tokens, secrets, input validation, user roles | **security** |
| Response time budgets, caching, query performance | **performance** |
| Database schemas, migrations, data validation | **data-integrity** |
| LLM prompts, model calls, embeddings, token limits | **llm-integration** |
| SSE, WebSocket, streaming, real-time events | **streaming-protocol** |
| Error handling, retries, fallbacks, degradation | **error-handling** |
| State lifecycle, sessions, caching, persistence | **state-management** |

**Target: 2-4 domains.** For PRSG-013, start with the four domains below because
the risk is stateful orchestration, script contracts, and agent guidance drift.

### Step 2: Run Enriched Checklist Prompts

For each domain, include spec-specific focus areas in the prompt — not just the bare domain name.

#### 1. state-management Checklist

Marker persistence is the core contract. The checklist should catch stale state,
partial-resume, marker-order, and workflow-evidence drift.

```bash
/speckit-checklist state-management

Focus on Non-stopping reviewability markers requirements:
- `autopilot-state.json` marker schema and resume behavior.
- Workflow evidence fields for reviewability sizing and marker decisions.
- Marker ordering across Foundation, user stories, subdivision, and Polish folding.
- Pay special attention to: avoiding drift between state, workflow evidence, and PR emission.
```

#### 2. error-handling Checklist

The central behavior is selective non-stopping. The checklist must distinguish
reviewability sizing from correctness failures that still stop.

```bash
/speckit-checklist error-handling

Focus on Non-stopping reviewability markers requirements:
- Post-G5 `reviewability-gate.sh tasks` block handling.
- Final pre-PR backstop handling.
- Correctness stops for malformed plans, failed verification, and invalid PR packets.
- Pay special attention to: preventing a blanket "continue on failure" behavior.
```

#### 3. api-contracts Checklist

The scripts and state files form internal APIs. The checklist should force exact
JSON shapes and compatibility boundaries before implementation.

```bash
/speckit-checklist api-contracts

Focus on Non-stopping reviewability markers requirements:
- Marker-plan JSON fields, status values, and evidence paths.
- Inputs/outputs for `plan-layers.sh`, `final-reviewability-backstop.sh`, and `multi-pr-emission.sh`.
- Backward compatibility for `reviewability-gate.sh tasks`.
- Pay special attention to: fixtures that prove stable machine-readable output.
```

#### 4. llm-integration Checklist

The behavior spans deterministic scripts and skill guidance. This checklist keeps
agent instructions aligned with the script contract and Codex parity.

```bash
/speckit-checklist llm-integration

Focus on Non-stopping reviewability markers requirements:
- Autopilot guidance for handling reviewability `block` results.
- Codex and Claude skill mirror parity for touched guidance.
- Evidence prompts that tell future agents not to stop implementation for size alone.
- Pay special attention to: avoiding wording that reintroduces a manual re-slicing stop.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| state-management | | | |
| error-handling | | | |
| api-contracts | | | |
| llm-integration | | | |
| **Total** | | | |

### Addressing Gaps

When checklist identifies `[Gap]` items:

1. Review the gap — is it a genuine missing requirement?
2. Update `spec.md` or `plan.md` to address it
3. Re-run the checklist to verify coverage
4. If the gap is intentionally out of scope, document why

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/prsg-013-reviewability-markers/tasks.md`

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: foundation → components → integration → validation
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story, not by technical layer

## Implementation Phases
1. Foundation — inspect existing gate/backstop/layer/emission scripts, define marker-plan schema, and add fixtures.
2. User Story 1 (P1) — non-stopping reviewability handling for post-G5 and final backstop.
3. User Story 2 (P1) — durable marker derivation and persistence from Foundation/user-story task structure.
4. User Story 3 (P1) — marker-ordered implementation/evidence and marker-consuming PR emission.
5. Polish & parity — Codex mirror updates, docs/evidence cleanup, and eval recording.

## Constraints
- Source changes stay in `speckit-pro/skills/speckit-autopilot/` and mirrored `speckit-pro/codex-skills/speckit-autopilot/` when guidance changes.
- Deterministic logic belongs in Bash scripts under `speckit-pro/skills/speckit-autopilot/scripts/`.
- Layer 4 fixtures belong under `tests/speckit-pro/layer4-scripts/`.
- Do not create authoritative marker comments in `tasks.md`.
- Do not implement PRSG-012 PR packet validation in this spec.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | |
| **Phases** | |
| **Parallel Opportunities** | |
| **User Stories Covered** | |

---

## Atomicity Route

**When this is filled:** After the Tasks phase / gate G5, the autopilot SKILL runs
the read-only atomicity classifier and records its decision here. This is a
**placeholder** until then — leave the cells blank during scoping. The classifier
emits one machine-readable decision; the SKILL is what writes it into this section
(the script never writes a file of its own). This route is recorded only here in the
workflow file — never in the spec map. It is read downstream by the layer-planner and
multi-PR emission work that builds on top of it; recording it now wires no PR creation
or branch splitting on its own.

The decision answers "can this change be split into multiple small PRs safely?" by
inspecting the change's structural seams (independent additive capabilities), not its
line count. Surface the four fields the SKILL extracts from the emitted decision:

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | | `true`, or `false` for a destructive-migration or concurrency-sensitive change (a passing CI run does not prove such a change is safe to release). |
| **Signals** | | The decisive detector findings behind the route and releasability reading (may be empty when the classifier abstains). |
| **Warnings** | | Any release-safety warning attached to the change (empty when there is no releasability risk). |

To produce the decision, run the classifier against the feature directory:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/prsg-013-reviewability-markers
```

See the classifier script at
[`speckit-autopilot/scripts/atomicity-route.sh`](../../speckit-autopilot/scripts/atomicity-route.sh).

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Constitution alignment: plugin layout, Bash safety, KISS, and test coverage.
2. Scope drift against `docs/ai/specs/.process/PRSG-013-design-concept.md` Goals and Non-goals.
3. Coverage gaps for non-stopping post-G5 handling, final backstop behavior, marker persistence, marker-ordered implementation, subdivision, and hazard collapse.
4. Contract drift: `reviewability-gate.sh tasks` remains stable, `tasks.md` is not the marker store, and correctness gates still stop.
5. Test proof: L4 fixtures plus L3 functional eval are explicitly represented in tasks.
```

### Analyze Severity Levels

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| `CRITICAL` | Blocks implementation, violates constitution | **Must fix before G6 gate** |
| `HIGH` | Significant gap, impacts quality | Should fix |
| `MEDIUM` | Improvement opportunity | Review and decide |
| `LOW` | Minor inconsistency | Note for future |

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| | | | |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed (no coverage gaps).

### Implement Prompt

```bash
/speckit-implement

## Approach: TDD-First

For each task, follow this cycle:

1. **RED**: Write failing test defining expected behavior
2. **GREEN**: Implement minimum code to make test pass
3. **REFACTOR**: Clean up while tests still pass
4. **VERIFY**: Manual verification of acceptance criteria

### Pre-Implementation Setup

Before starting any task:
1. Verify branch and worktree:
   `git status --short --branch`
2. Run a targeted baseline before script edits:
   `bash tests/speckit-pro/run-all.sh --layer 1`
3. Inspect current contracts before editing:
   `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh`,
   `speckit-pro/skills/speckit-autopilot/scripts/final-reviewability-backstop.sh`,
   `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`, and
   `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`.

### Implementation Notes
- Use Bash plus `jq` for deterministic marker planning and state writes.
- Treat reviewability `block` as marker-sizing evidence only; do not catch and ignore correctness failures.
- Make marker-order implementation explicit in guidance/evidence so emission is not inferred from one mixed diff.
- Keep user-story marker behavior explainable in PR evidence: Foundation marker when shared setup exists, one marker per user story, safe subdivision inside oversized stories, and hazard collapse to one warned PR.
- Mirror touched autopilot guidance into Codex surfaces and run the parity checks required by the roadmap.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation | | | |
| 2 - User Story 1 | | | |
| 3 - User Story 2 | | | |
| 4 - Polish | | | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in tasks.md
- [ ] Structural validation passes: `bash tests/speckit-pro/run-all.sh --layer 1`
- [ ] Targeted Layer 4 script fixtures pass for marker planning and non-stopping gate handling
- [ ] Default deterministic suite passes: `bash tests/speckit-pro/run-all.sh`
- [ ] Layer 3 functional eval evidence is recorded
- [ ] Layer 8 parity is run or explicitly marked not applicable based on touched mirrored files
- [ ] Workflow evidence records reviewability sizing as marker input, not implementation stop
- [ ] PR created and reviewed
- [ ] Merged to main branch

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

```
speckit-pro/
├── skills/speckit-autopilot/
│   ├── SKILL.md
│   ├── references/
│   └── scripts/
├── codex-skills/speckit-autopilot/
├── agents/
└── README.md
tests/
└── speckit-pro/
    ├── layer1-structural/
    └── layer4-scripts/
docs/ai/specs/
├── pr-size-governance-technical-roadmap.md
└── .process/PRSG-013-workflow.md
specs/
└── prsg-013-reviewability-markers/
```

---
