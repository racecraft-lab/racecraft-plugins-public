# SpecKit Workflow: {{SPEC_ID}} — {{SPEC_NAME}}

**Template Version**: 1.0.0
**Created**: {{DATE}}
**Purpose**: Reusable template for executing SpecKit workflows. Copy-paste the prompts below into your AI coding agent.

---

## How to Use This Template

1. **Copy this template** to create a new workflow guide:

   ```bash
   cp .github/skills/speckit/templates/workflow-template.md docs/ai/specs/{{SPEC_ID}}-workflow.md
   ```

2. **Replace placeholders** throughout the document:
   - `{{SPEC_ID}}` → Your spec identifier (e.g., `SPEC-001`)
   - `{{SPEC_NAME}}` → Human-readable name (e.g., `User Authentication`)
   - `{{SPEC_DESCRIPTION}}` → One-line description
   - `{{BRANCH_NAME}}` → Feature branch name (e.g., `feature/user-auth`)

3. **Populate the prompts** in each phase section with your project-specific details (tech stack, constraints, project structure, checklist domains)

4. **Copy-paste prompts** into your AI coding agent as you execute each phase

5. **Track progress** using the status table below

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit.specify` | ⏳ Pending | |
| Clarify | `/speckit.clarify` | ⏳ Pending | Optional but recommended |
| Plan | `/speckit.plan` | ⏳ Pending | |
| Checklist | `/speckit.checklist` | ⏳ Pending | Run for each domain |
| Tasks | `/speckit.tasks` | ⏳ Pending | |
| Analyze | `/speckit.analyze` | ⏳ Pending | |
| Implement | `/speckit.implement` | ⏳ Pending | |

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

```bash
/speckit.specify {{SPEC_DESCRIPTION}}
```

#### Detailed Prompt (for complex specs)

```bash
/speckit.specify

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

## Phase 2: Clarify (Optional but Recommended)

**When to run:** When spec has areas that could be interpreted multiple ways. 10-20 minutes here saves hours of rework later.

**Best Practice:** Maximum 5 targeted questions per Clarify session.

### Clarify Prompts

#### Session 1: UX Focus

```bash
/speckit.clarify Focus on UX: user flows, interactions, loading states, error states
```

#### Session 2: API Focus

```bash
/speckit.clarify Focus on API: endpoint contracts, error responses, streaming behavior, rate limiting
```

#### Session 3: Integration Focus

```bash
/speckit.clarify Focus on integration: external services, data dependencies, authentication
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

```bash
/speckit.plan

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

**When to run:** After `/speckit.plan` — validates both spec AND plan together. Run multiple times for different domains.

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

```bash
/speckit.checklist <!-- DOMAIN_1 -->

Focus on {{SPEC_NAME}} requirements:
- <!-- Specific area from your spec this domain should validate -->
- <!-- Another specific area -->
- <!-- Another specific area -->
- Pay special attention to: <!-- The riskiest or most ambiguous part -->
```

#### 2. <!-- DOMAIN_2 --> Checklist

<!-- Why this domain: [1-2 sentence justification from spec analysis] -->

```bash
/speckit.checklist <!-- DOMAIN_2 -->

Focus on {{SPEC_NAME}} requirements:
- <!-- Specific area from your spec this domain should validate -->
- <!-- Another specific area -->
- <!-- Another specific area -->
- Pay special attention to: <!-- The riskiest or most ambiguous part -->
```

#### 3. <!-- DOMAIN_3 --> Checklist (if needed)

<!-- Why this domain: [1-2 sentence justification from spec analysis] -->

```bash
/speckit.checklist <!-- DOMAIN_3 -->

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

```bash
/speckit.tasks

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

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```bash
/speckit.analyze

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

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed (no coverage gaps).

### Implement Prompt

```bash
/speckit.implement

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

<!-- Populate with your project's quality gates from the constitution -->

- [ ] All tasks marked complete in tasks.md
- [ ] Linting passes: <!-- e.g., `scripts/lint.sh` -->
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

Template based on SpecKit best practices. Populate the prompts above with your project-specific tech stack, domains, and constraints.
