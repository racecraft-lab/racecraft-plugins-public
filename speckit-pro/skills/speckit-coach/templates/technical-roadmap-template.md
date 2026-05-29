# {{FEATURE_NAME}} Implementation Roadmap

**{{FEATURE_DESCRIPTION}}**

This document defines the **SPEC catalog** for {{FEATURE_NAME}}: an ordered set of specifications derived from the source PRD. Each SPEC corresponds 1:1 to a Feature / Acceptance-Criteria group in the PRD (`AC-N.*`), preserving traceability from PRD → roadmap → spec. Each specification is executed end-to-end through the SpecKit workflow (specify → clarify → plan → checklist → tasks → analyze → implement) before moving to the next, and is prepared for autopilot with `/speckit-pro:speckit-scaffold-spec SPEC-NNN`, which reads this roadmap as its input.

**Source PRD:** {{PRD_LINK}} <!-- the PRD whose Features become the SPEC catalog below -->
**Branch:** `{{BRANCH_NAME}}`
**Tracker:** {{TRACKER_LINK}}

---

## Table of Contents

1. [Roadmap Overview](#roadmap-overview)
2. [Dependency Graph](#dependency-graph)
3. [Progress Tracking](#progress-tracking)
4. [Specification Sections](#specification-sections)

---

## Roadmap Overview

The feature is decomposed into **{{N}} specifications** across **{{M}} dependency tiers**:

| Tier | Specs | Purpose | Parallelization |
|------|-------|---------|-----------------|
| **1** | SPEC-001 | <!-- e.g., Backend foundation --> | Sequential |
| **2** | SPEC-002, SPEC-003 | <!-- e.g., Tool integration, UI components --> | Parallel possible |
| **3** | SPEC-004 | <!-- e.g., Full-stack integration --> | Sequential (depends on all above) |

**Execution Order:** SPEC-001 → SPEC-002 → SPEC-003 → SPEC-004

**Dependency Constraints:**
<!-- List which specs depend on which -->
- SPEC-002 requires SPEC-001 (reason)
- SPEC-003 can start in parallel with SPEC-002 (uses mock data)
- SPEC-004 requires ALL previous specs (integration spec)

## Reviewability Contract

Every spec must fit a human review budget before setup and again before PR
creation.

- Warn above 400 reviewable LOC, 6 production files, 15 total files, or more
  than one primary surface.
- Block above 800 reviewable LOC, 8 production files, 25 total files, or more
  than one primary surface unless this roadmap records a ratified split
  exception.
- Primary surfaces are schema/migration, API, UI, scheduler/runtime,
  harness/adapter, seed/config, and docs/process.
- PR descriptions are review packets. They must include what changed, why,
  non-goals, review order, scope budget, traceability, verification evidence,
  known gaps, and rollback/flag notes.

---

## Dependency Graph

```text
SPEC-001 ({{SPEC_001_NAME}})
    │
    └──► SPEC-002 ({{SPEC_002_NAME}})
              │
              └──────────────────────────┐
                                         │
SPEC-003 ({{SPEC_003_NAME}}) ───────────►│
                                         │
                                         ▼
                              SPEC-004 ({{SPEC_004_NAME}})
                                         │
                              ─── FEATURE COMPLETE ───
```

<!-- Adjust the graph to match your actual dependency structure -->

---

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|------|------|--------|---------------|------------|
| SPEC-001 | {{SPEC_001_NAME}} | ⏳ Pending | [SPEC-001-workflow.md](SPEC-001-workflow.md) | Specify |
| SPEC-002 | {{SPEC_002_NAME}} | ⏳ Pending | [SPEC-002-workflow.md](SPEC-002-workflow.md) | Blocked by SPEC-001 |
| SPEC-003 | {{SPEC_003_NAME}} | ⏳ Pending | [SPEC-003-workflow.md](SPEC-003-workflow.md) | Specify (can start with mock data) |
| SPEC-004 | {{SPEC_004_NAME}} | ⏳ Pending | [SPEC-004-workflow.md](SPEC-004-workflow.md) | Blocked by all |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

---

## Specification Sections

### SPEC-001: {{SPEC_001_NAME}}

**Priority:** P1 | **Depends On:** None | **Enables:** SPEC-002, SPEC-004

**Goal:** <!-- One sentence describing what this spec achieves -->

**Reviewability Budget:** Primary surface: <!-- e.g., API --> |
Projected reviewable LOC: <!-- e.g., 320 --> |
Production files: <!-- e.g., 4 --> |
Total files: <!-- e.g., 9 --> |
Budget result: <!-- within budget / warning accepted / split exception -->

**Scope:**
<!--
  Write scope descriptions detailed enough to drive /speckit-specify.
  BAD:  "Backend API endpoint"
  GOOD: "FastAPI POST /chat endpoint with SSE streaming, Pydantic v2
         request/response models, conversation state management (in-memory for MVP)"
-->
- <!-- Specific deliverable with technology and approach -->
- <!-- Another specific deliverable -->
- <!-- Another specific deliverable -->

**Out of Scope:**
<!-- Explicitly list what this spec does NOT include, and where it's handled -->
- <!-- Item (handled by SPEC-002) -->
- <!-- Item (handled by SPEC-004) -->

**Key Decisions:**
<!-- Document significant technical decisions for this spec. Remove if none yet. -->
<!--
**[Decision Name] Decision ([Date]):** [What was decided and why.]
Alternatives considered: [What was rejected and why.]
-->

**Key Files:**
<!-- List the main files this spec will create or modify -->
- `path/to/file1` — Description
- `path/to/file2` — Description

---

### SPEC-002: {{SPEC_002_NAME}}

**Priority:** P1 | **Depends On:** SPEC-001 | **Enables:** SPEC-004

**Goal:** <!-- One sentence -->

**Reviewability Budget:** Primary surface: <!-- e.g., UI --> |
Projected reviewable LOC: <!-- e.g., 300 --> |
Production files: <!-- e.g., 3 --> |
Total files: <!-- e.g., 8 --> |
Budget result: <!-- within budget / warning accepted / split exception -->

**Scope:**
- <!-- Specific deliverable with technology and approach -->
- <!-- Another specific deliverable -->

**Out of Scope:**
- <!-- Item (handled by SPEC-004) -->

**Key Decisions:**
<!-- Document significant technical decisions. Remove if none yet. -->

**Key Files:**
- `path/to/file1` — Description

---

### SPEC-003: {{SPEC_003_NAME}}

**Priority:** P1 | **Depends On:** None (mock data) | **Enables:** SPEC-004

**Goal:** <!-- One sentence -->

**Reviewability Budget:** Primary surface: <!-- e.g., docs/process --> |
Projected reviewable LOC: <!-- e.g., 200 --> |
Production files: <!-- e.g., 0 --> |
Total files: <!-- e.g., 5 --> |
Budget result: <!-- within budget / warning accepted / split exception -->

**Scope:**
- <!-- Specific deliverable with technology and approach -->
- <!-- Another specific deliverable -->

**Out of Scope:**
- <!-- Item (handled by SPEC-004) -->

**Key Decisions:**
<!-- Document significant technical decisions. Remove if none yet. -->

**Key Files:**
- `path/to/file1` — Description

---

### SPEC-004: {{SPEC_004_NAME}}

**Priority:** P1 | **Depends On:** SPEC-001, SPEC-002, SPEC-003 | **Enables:** Complete feature

**Goal:** <!-- One sentence -->

**Reviewability Budget:** Primary surface: <!-- e.g., scheduler/runtime --> |
Projected reviewable LOC: <!-- e.g., 450 --> |
Production files: <!-- e.g., 5 --> |
Total files: <!-- e.g., 12 --> |
Budget result: <!-- within budget / warning accepted / split exception -->

**Scope:**
- <!-- Specific deliverable with technology and approach -->
- <!-- Another specific deliverable -->

**Out of Scope:**
- <!-- Item (post-launch optimization) -->

**Key Decisions:**
<!-- Document significant technical decisions. Remove if none yet. -->

**Key Files:**
- `path/to/file1` — Description

---

## Decomposition Principles

When breaking a feature into specs:

1. **Each spec is independently executable** through the full SpecKit workflow (specify → implement)
2. **Minimize cross-spec dependencies** — prefer sequential over deeply nested
3. **Backend foundations first** — establish APIs before frontend integration
4. **Mock data for blocked specs** — UI specs can use static data while backend specs complete
5. **Integration spec last** — wire everything together as the final spec
6. **Each spec gets its own directory**: `specs/<number>-<name>/`

## Environment & Deployment Context

<!--
  Document infrastructure, existing resources, and setup requirements
  that are relevant to ALL specs. This prevents each spec from having
  to rediscover the same context independently.
-->

### Existing Infrastructure (No Changes Needed)

<!-- List resources that already exist and can be used as-is -->

| Resource | Detail |
|----------|--------|
| <!-- e.g., Compute --> | <!-- e.g., ECS Fargate 8 CPU, 32GB RAM --> |
| <!-- e.g., Database --> | <!-- e.g., Aurora PostgreSQL with pgvector --> |
| <!-- e.g., IAM/Auth --> | <!-- e.g., Task role has bedrock:InvokeModel --> |

### Changes Required

<!-- List infrastructure changes needed for the feature -->

| Change | Where | Detail |
|--------|-------|--------|
| <!-- e.g., Add dependency --> | <!-- e.g., pyproject.toml --> | <!-- e.g., claude-agent-sdk --> |
| <!-- e.g., Add env var --> | <!-- e.g., ECS task definition --> | <!-- e.g., CLAUDE_CODE_USE_BEDROCK=1 --> |

### Local Development Setup

| Requirement | How |
|-------------|-----|
| <!-- e.g., CLI tool --> | <!-- e.g., curl -fsSL https://example.com/install.sh | bash --> |
| <!-- e.g., Database access --> | <!-- e.g., SSM tunnel to RDS on port 5433 --> |
| <!-- e.g., Model weights --> | <!-- e.g., Download to ~/.models/ (~5GB) --> |
| <!-- e.g., Frontend deps --> | <!-- e.g., cd frontend && npm install --> |

---

## References

- **Source PRD:** {{PRD_LINK}} — the SPEC catalog above is derived from its Features / Acceptance Criteria
- **PRD Template:** `prd-template.md` (same `templates/` directory) — author with `/speckit-pro:speckit-prd`
- **SpecKit Workflow Template:** `docs/ai/speckit-workflow-template.md`
- **Constitution:** `.specify/memory/constitution.md`
- **Project Standards:** <!-- Link to AGENTS.md, CLAUDE.md, or equivalent -->
<!-- Add references to key documentation, SDKs, design tools, related branches, etc. -->
