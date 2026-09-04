# SpecKit Workflow: {{SPEC_ID}} — {{SPEC_NAME}}

**Template Version**: 1.0.0
**Created**: {{DATE}}
**Purpose**: Reusable template for executing SpecKit workflows. Copy-paste the prompts below into your AI coding agent.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/{{SPEC_ID}}-design-concept.md
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
| Confidence Gate | G6.5 | ⏳ Pending | Pre-Implement composite confidence |
| Implement | `/speckit-implement` | ⏳ Pending | |
| Post | Post-Implementation | ⏳ Pending | Canonical 12-item closeout |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

G6.5 is advisory by default, so no phase of the main loop flips its row. Leaving
it Pending is legitimate and does not make the rows below it read as out of
order; record the verdict in [Phase 6.5](#phase-65-confidence-gate) when the
gate runs.

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
| G6.5 | Before Implement | Composite confidence meets the autonomous implementation threshold |
| G7 | After Each Implementation Phase | Tests pass, manual verification complete |

---

## Prerequisites

### Constitution Validation

**Before starting any workflow phase**, verify alignment with the project constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| <!-- e.g., Type Safety --> | <!-- e.g., All functions typed --> | <!-- e.g., `pyright .` --> |
| <!-- e.g., Test-First --> | <!-- e.g., TDD Red→Green --> | <!-- e.g., `pytest` --> |
| <!-- e.g., Simplicity --> | <!-- e.g., YAGNI --> | <!-- Code review --> |

**Constitution Check:** ✅ / ❌ (mark before proceeding to G1)

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | {{SPEC_ID}} |
| **Name** | {{SPEC_NAME}} |
| **Branch** | `{{BRANCH_NAME}}` |
| **Dependencies** | <!-- List prerequisite specs --> |
| **Enables** | <!-- List specs this unblocks --> |
| **Priority** | <!-- P1/P2/P3 --> |

### Success Criteria Summary

<!-- Copy or reference the acceptance criteria from the technical roadmap -->

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/{{BRANCH_NAME}}/spec.md`

### Specify Prompt

```text
/speckit-specify {{SPEC_DESCRIPTION}}
```

#### Detailed Prompt (for complex specs)

```text
/speckit-specify

## Feature: {{SPEC_NAME}}

### Problem Statement
<!-- What problem does this solve? -->

### Users
<!-- Who benefits from this feature? -->

### User Stories
<!-- List the key user stories -->

### Constraints
<!-- Non-functional requirements, performance budgets, accessibility -->

### Out of Scope
<!-- What this spec explicitly does NOT include -->
```

### Specify Results

<!-- Fill in after running the command -->

| Metric | Value |
|--------|-------|
| Functional Requirements | <!-- e.g., FR-001 through FR-020 --> |
| User Stories | <!-- Count --> |
| Acceptance Criteria | <!-- Count --> |

### Files Generated

- [ ] `specs/{{BRANCH_NAME}}/spec.md`

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

## Phase 2: Clarify

**When to run:** When spec has areas that could be interpreted multiple ways. 10-20 minutes here saves hours of rework later.

**Best Practice:** Maximum 5 targeted questions per Clarify session.

### Clarify Prompts

#### Session 1: UX Focus

```text
/speckit-clarify Focus on UX: user flows, interactions, loading states, error states
```

#### Session 2: API Focus

```text
/speckit-clarify Focus on API: endpoint contracts, error responses, streaming behavior, rate limiting
```

#### Session 3: Integration Focus

```text
/speckit-clarify Focus on integration: external services, data dependencies, authentication
```

<!-- Add or modify sessions based on your project's domains -->

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/{{BRANCH_NAME}}/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack
<!-- Populate with your project's tech stack from the constitution or project docs -->
- Backend: <!-- e.g., FastAPI with async handlers -->
- Frontend: <!-- e.g., React 19 + TypeScript strict mode -->
- Styling: <!-- e.g., Tailwind CSS -->
- State: <!-- e.g., React Context (no external state library) -->
- Database: <!-- e.g., PostgreSQL with pgvector -->
- Testing: <!-- e.g., pytest + vitest -->

## Constraints
<!-- Add spec-specific constraints -->

## Architecture Notes
<!-- Add any architectural decisions or patterns to follow -->
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

**Target: 2-4 domains.** Prioritize domains where the spec has the most complexity or risk.

<!-- After analyzing, fill in the recommended domains and enriched prompts below -->

### Step 2: Run Enriched Checklist Prompts

For each domain, include spec-specific focus areas in the prompt — not just the bare domain name.

#### 1. <!-- DOMAIN_1 --> Checklist

<!-- Why this domain: [1-2 sentence justification from spec analysis] -->

```text
/speckit-checklist <!-- DOMAIN_1 -->

Focus on {{SPEC_NAME}} requirements:
- <!-- Specific area from your spec this domain should validate -->
- <!-- Another specific area -->
- <!-- Another specific area -->
- Pay special attention to: <!-- The riskiest or most ambiguous part -->
```

#### 2. <!-- DOMAIN_2 --> Checklist

<!-- Why this domain: [1-2 sentence justification from spec analysis] -->

```text
/speckit-checklist <!-- DOMAIN_2 -->

Focus on {{SPEC_NAME}} requirements:
- <!-- Specific area from your spec this domain should validate -->
- <!-- Another specific area -->
- <!-- Another specific area -->
- Pay special attention to: <!-- The riskiest or most ambiguous part -->
```

#### 3. <!-- DOMAIN_3 --> Checklist (if needed)

<!-- Why this domain: [1-2 sentence justification from spec analysis] -->

```text
/speckit-checklist <!-- DOMAIN_3 -->

Focus on {{SPEC_NAME}} requirements:
- <!-- Specific area from your spec this domain should validate -->
- <!-- Another specific area -->
- Pay special attention to: <!-- The riskiest or most ambiguous part -->
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| <!-- DOMAIN_1 --> | | | |
| <!-- DOMAIN_2 --> | | | |
| <!-- DOMAIN_3 --> | | | |
| **Total** | | | |

### Addressing Gaps

When checklist identifies `[Gap]` items:

1. Review the gap — is it a genuine missing requirement?
2. Update `spec.md` or `plan.md` to address it
3. Re-run the checklist to verify coverage
4. If the gap is intentionally out of scope, document why

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/{{BRANCH_NAME}}/tasks.md`

### Tasks Prompt

```text
/speckit-tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: foundation → components → integration → validation
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story, not by technical layer

## Implementation Phases
1. Foundation (types, shared infrastructure)
2. User Story 1 (P1) — independently testable
3. User Story 2 (P2) — independently testable
4. Polish & cross-cutting concerns

## Constraints
<!-- Add project-specific file layout constraints -->
<!-- e.g., Backend tests in tests/, Frontend components in src/components/ -->
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

```text
runner helper atomicity-route specs/{{BRANCH_NAME}}
```

See the classifier script at
[`speckit-autopilot/scripts/atomicity-route`](../../speckit-autopilot/scripts/atomicity-route).

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```text
/speckit-analyze

Focus on:
1. Constitution alignment — verify coding standards compliance
2. Coverage gaps — ensure all FRs and user stories have tasks
3. Consistency between task file paths and actual project structure
4. Verify P1 user stories have complete task coverage
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

## Phase 6.5: Confidence Gate

**When to run:** After Phase 6 commits and before Phase 7 begins. Gate semantics
are unchanged; this section records the verdict so a later session can read it.

| Field | Value |
|-------|-------|
| Mode | <!-- advisory (default) or strict --> |
| Composite confidence | <!-- 0.00-1.00 --> |
| Verdict | <!-- proceed / remediate / stop --> |
| Evidence | <!-- what the score was computed from --> |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed (no coverage gaps).

### Implement Prompt

```text
/speckit-implement

## Approach: TDD-First

For each task, follow this cycle:

1. **RED**: Write failing test defining expected behavior
2. **GREEN**: Implement minimum code to make test pass
3. **REFACTOR**: Clean up while tests still pass
4. **VERIFY**: Manual verification of acceptance criteria

### Pre-Implementation Setup

Before starting any task:
<!-- Populate with your project's setup commands -->
1. Ensure development environment is running
2. Verify all tests pass before making changes
3. Create a clean branch or verify you're on the right one

### Implementation Notes
<!-- Add project-specific implementation guidance -->
<!-- e.g., naming conventions, patterns to follow, tools to use -->
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

The canonical closeout. Every row must reach Complete or an explicit
`Skipped` before the run may report completion.

| Canonical Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | ⏳ Pending | |
| Post: Verify Implementation | ⏳ Pending | |
| Post: Verify Tasks Phantom Check | ⏳ Pending | |
| Post: Code Review | ⏳ Pending | |
| Post: Integration Suite | ⏳ Pending | |
| Post: Reviewability Diff Gate | ⏳ Pending | |
| Post: Self-Review | ⏳ Pending | |
| Post: UAT Runbook Generation | ⏳ Pending | |
| Post: PR Body Generation | ⏳ Pending | |
| Post: PR Creation | ⏳ Pending | |
| Post: Review Remediation | ⏳ Pending | |
| Post: Retrospective | ⏳ Pending | |

<!-- Populate with your project's quality gates from the constitution -->

- [ ] All tasks marked complete in tasks.md
- [ ] Linting passes: <!-- e.g., `scripts/lint` -->
- [ ] Tests pass: <!-- e.g., `pytest` -->
- [ ] Build succeeds: <!-- e.g., `npm run build` -->
- [ ] Manual verification complete
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

<!-- Populate with your project's directory structure for quick reference during implementation -->

```
project/
├── src/                    # Source code
├── tests/                  # Test files
├── docs/                   # Documentation
└── specs/                  # SpecKit specifications
```

---
