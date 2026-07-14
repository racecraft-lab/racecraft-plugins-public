# SpecKit Workflow: G56R-001 — Candidate Route Baseline and Role Contracts

**Template Version**: 1.0.0
**Created**: 2026-07-14
**Purpose**: Execute a one-working-day, research-only spike that produces the cited candidate-route baseline and role-contract handoff required before capability discovery.

---

## How to Use This Workflow

1. Run this workflow only from the dedicated worktree on branch
   g56r-001-candidate-route-baseline.
2. Start with Phase 1 and checkpoint each gate before moving forward.
3. Treat the Design Concept as the source of truth for all scoping decisions.
4. Keep G56R-001 research-only. Record discovered production defects without
   fixing them in this spec.
5. Stop after one working day with either a complete go packet or a precise
   no-go packet for G56R-002.

---

## Design Concept

This workflow was enriched from the fresh Grill Me interview at:

~~~text
docs/ai/specs/.process/G56R-001-design-concept.md
~~~

The Design Concept records 23 answered questions, Goals, Non-goals, the
evidence-authority clarification, the one-spike sizing decision, and the
downstream open questions. Re-read it before each phase. Once autopilot begins,
clarifications use /speckit-clarify and consensus, never grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | /speckit-specify | ⏳ Pending | Define the research artifact contract |
| Clarify | /speckit-clarify | ⏳ Pending | Resolve evidence, identity, and handoff precision |
| Plan | /speckit-plan | ⏳ Pending | Plan a one-day evidence-first spike |
| Checklist | /speckit-checklist | ⏳ Pending | Four requirement-quality domains |
| Tasks | /speckit-tasks | ⏳ Pending | Order research, reconciliation, validation, and handoff |
| Analyze | /speckit-analyze | ⏳ Pending | Cross-check all artifacts against the Design Concept |
| Implement | /speckit-implement | ⏳ Pending | Produce the narrative, manifest, and go/no-go packet |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | AC-1.1 through AC-1.7 are testable; no unresolved requirement markers |
| G2 | After Clarify | Evidence classes, surface boundaries, canonical hashes, and terminal rules are explicit |
| G3 | After Plan | Constitution checks pass; the one-day sequence and focused validation are reviewable |
| G4 | After Checklists | All genuine gaps are resolved or explicitly scoped out |
| G5 | After Tasks | Every acceptance criterion and handoff artifact has ordered task coverage |
| G6 | After Analyze | No CRITICAL inconsistency or Design Concept drift remains |
| G7 | During Implement | Each artifact increment is grounded, reconciled, and verified before continuing |

---

## Prerequisites

### Worktree and Bootstrap

- **Branch:** g56r-001-candidate-route-baseline
- **Worktree:** dedicated linked worktree created from current origin/main
- **Bootstrap:** no documented bootstrap
- **Commands run:** none
- **Health check:** not applicable because AGENTS.md and CLAUDE.md document no
  worktree install, build, code-index, MCP, or bootstrap procedure

### Reviewability Setup Decision

The authoritative setup gate ran against
docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md.

| Field | Result |
|-------|--------|
| Status | warn; pass true |
| Full-roadmap forward reading | 395 reviewable LOC, 2 production files, 15 total files |
| Warning | Three primary roadmap surfaces exceed the single-surface warning threshold |
| Blockers | None |
| G56R-001 entry budget | Research spike, 0 projected production LOC, approximately 3 files |
| Split decision | One time-boxed spike; no split |
| Grill Me estimator | estimated_loc 0, suggested_slices 1, status ok with spike true |

The workflow must preserve this evidence. The roadmap-wide surface warning does
not expand G56R-001 beyond its docs/process research boundary.

### Constitution Validation

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Cross-Platform Runtime and Script Safety | Python 3.11+ standard library; no Bash, jq, shell fallback, or package dependency | Inspect plan and tasks; use structured JSON parsing and shell false for any subprocess |
| Test Coverage Before Merge | Focused artifact invariants plus the smallest relevant Python-authoritative repository gate | Record exact commands and zero failures before implementation closeout |
| KISS, Simplicity, and YAGNI | No reusable validator framework, router, installer, or schema package for this one-off spike | Plan complexity review and changed-file inspection |
| Conventional Commits | Focused conventional commit and public-readable PR title | Validate commit and eventual PR title |
| Plugin Structure Compliance | Research artifacts remain outside the shipped plugin directory | Changed-file scope check |

**Constitution Check:** Pending at G1 and required again at G3.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | G56R-001 |
| **Name** | Candidate Route Baseline and Role Contracts |
| **Branch** | g56r-001-candidate-route-baseline |
| **Dependencies** | None |
| **Enables** | G56R-002 |
| **Priority** | P1 |
| **Slice type** | One-working-day research spike |
| **Primary surface** | docs/process |
| **Roadmap tools** | No tool count or named tool list recorded |

### Success Criteria Summary

- [ ] AC-1.1: Inventory all twelve named agents and every active producer or
  consumer of route policy.
- [ ] AC-1.2: Cite current official OpenAI sources with URL, retrieval date,
  Codex surface, applicability, and explicit conflict handling.
- [ ] AC-1.3: Record immutable production routes or absence, semantic role
  contracts, all evidence-supported candidates, justified prompt/context
  variants, and per-agent fixture contracts.
- [ ] AC-1.4: Separate platform facts, project facts, inferences, proposed
  SpecKit Pro policies, assumptions, and unresolved claims.
- [ ] AC-1.5: End within one working day with a complete go packet or precise
  no-go packet independent of later executable evidence.
- [ ] AC-1.6: Publish a versioned agent-centric JSON manifest with readable
  IDs, canonical hashes, capabilities, rationale, incompatibilities,
  qualification requirements, invalidation triggers, and eligibility separate
  from installation-time availability.
- [ ] AC-1.7: Inventory the three current and nine missing fixtures and label
  historical prompt-emulation results as non-release evidence.

---

## Phase 1: Specify

**Output:** specs/g56r-001-candidate-route-baseline/spec.md

### Specify Prompt

~~~text
/speckit-specify

## Feature: Candidate Route Baseline and Role Contracts

Define a one-working-day, research-only spike that produces a dated, cited
Markdown narrative and a separate JSON agent_route_candidate_manifest for all
twelve named agents.

### Goals
- Inventory the ten current Codex agents and derive semantic parity contracts
  for consensus-synthesizer and gate-validator, whose current Codex production
  routes are absent.
- Enumerate all evidence-supported project-level model-and-effort candidates.
- Use current official OpenAI documentation exclusively for platform facts.
  Use repository files only for project facts, and keep tracked source, cached
  source, and sanitized installed-state evidence distinct.
- Separate CLI, desktop/app, app-server, and non-interactive records.
- Use agent-centric records with readable IDs plus canonical instruction and
  contract hashes.
- Define per-agent fixture contracts, telemetry requirements, classified
  unknowns, and an objective G56R-002 go/no-go handoff.

### Primary User
SpecKit Pro maintainers who need a trustworthy candidate catalog and immutable
role-contract baseline before capability discovery, qualification, resolution,
installation, and installed UAT.

### User Story
As a SpecKit Pro maintainer, I can review one cited research narrative and a
structured twelve-agent manifest so G56R-002 can freeze an executable candidate
set without rediscovering scope or silently changing production behavior.

### Constraints
- Stop at one working day. Incomplete objective criteria produce a precise
  no-go packet rather than an extension.
- Record source conflicts and leave them unresolved when authority or
  applicability cannot be established.
- Exclude candidates with evidenced hard-contract incompatibility.
- Include prompt or context variants only when an evidence-backed overhead
  hypothesis justifies them; retain the unchanged prompt as the control.
- Sanitize installed-state facts and hashes; never publish home paths,
  credentials, or unrelated local configuration.
- Use Python 3.11+ standard-library structured checks only. Do not add Bash,
  jq, package dependencies, or a reusable validator framework.

### Out of Scope
- Runtime capability probes, live scoring, qualification, or final fallback
  ordering.
- Agent, installer, prompt, payload, cache, installed-state, default-route, or
  version mutations.
- Fixing defects discovered during inventory.
- Excluding a project candidate only because this machine lacks it.

Use docs/ai/specs/.process/G56R-001-design-concept.md as the source of truth
for the 23 accepted scoping decisions and their rationale.
~~~

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | Pending |
| User Stories | 1 planned |
| Acceptance Criteria | AC-1.1 through AC-1.7 |

### Files Generated

- [ ] specs/g56r-001-candidate-route-baseline/spec.md

### Traceability Markers

Use US1 for the maintainer handoff story, FR identifiers for each artifact
invariant, NEEDS CLARIFICATION only for Clarify-owned ambiguity, Gap for missing
requirement coverage, and P only for genuinely disjoint research tasks.

---

## Phase 2: Clarify

**Best Practice:** Maximum five targeted questions per session.

### Clarify Prompts

#### Session 1: Evidence Authority and Surface Applicability

~~~text
/speckit-clarify

Resolve only evidence-boundary ambiguities for G56R-001:
- Define the official OpenAI source hierarchy for platform facts.
- Define repository evidence allowed for project-only facts.
- Keep CLI, desktop/app, app-server, and non-interactive applicability separate.
- Specify URL, retrieval date, surface, version or feature applicability, and
  conflict handling.
- Define the terminal treatment for unresolved authority conflicts.

Preserve Design Concept Q3-Q6 and Q17: official sources are exclusive for
platform facts; project files may establish project facts; unsupported
synthesis is prohibited.
~~~

#### Session 2: Agent Contract, Identity, and Manifest Completeness

~~~text
/speckit-clarify

Resolve the agent_route_candidate_manifest contract:
- Define the agent-centric top-level structure and manifest version.
- Define readable agent_contract_id and candidate_route_id formats.
- Define canonical instruction and contract hashing inputs.
- Specify every required production-route, candidate, capability, rationale,
  incompatibility, qualification, provenance, and invalidation field.
- Define Markdown/JSON agreement and objective twelve-agent completeness.

Preserve Design Concept Q2, Q8-Q10, Q16, Q19, and Q23. Project eligibility and
installation-time availability are separate; semantic parity does not imply a
current production route.
~~~

#### Session 3: Local Evidence, Fixture Backlog, and Go/No-Go

~~~text
/speckit-clarify

Resolve the downstream handoff boundary:
- Define sanitized source, cache, and installed-state evidence fields.
- Define the three-current/nine-missing fixture inventory and each per-agent
  fixture contract.
- Define focused artifact checks without a reusable framework.
- Classify documentation, inventory, capability-probe, and scored unknowns by
  owning spec.
- Define the objective one-day go/no-go rule and exact no-go payload.

Preserve Design Concept Q7, Q11-Q15, Q18, Q20-Q22. Discovered defects are
recorded with owners and are not fixed in G56R-001.
~~~

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Evidence and surfaces | Pending | Pending |
| 2 | Manifest and identities | Pending | Pending |
| 3 | Local evidence and handoff | Pending | Pending |

---

## Phase 3: Plan

**Output:** specs/g56r-001-candidate-route-baseline/plan.md and supporting research artifacts.

### Plan Prompt

~~~text
/speckit-plan

## Tech Stack
- Deliverables: Markdown research narrative plus standard JSON manifest.
- Validation: Python 3.11+ standard library, deterministic UTF-8, structured
  JSON parsing, and shell false for any subprocess.
- Platform evidence: current official OpenAI documentation selected through
  runtime capability discovery.
- Project evidence: tracked repository files plus separately classified,
  sanitized cache and installed-state observations.
- Repository gates: smallest relevant Python-authoritative checks, with the
  default deterministic suite before final closeout when changed-file scope
  requires it.

## Constraints
- One working day; research spike sized by timebox, not LOC.
- Zero production files and no source, runtime, install, payload, cache, or
  default-route mutation.
- No runtime capability probe, scored run, final preferred route, or ordered
  fallback policy.
- No reusable schema package, validator framework, router, installer, or new
  dependency.
- Every external platform claim must cite an official OpenAI URL, retrieval
  date, Codex surface, and applicability.
- Every project claim must cite a repository path or sanitized local evidence
  record and must not be promoted into a platform claim.

## Architecture and Data Model Decisions
- Quote and implement the selected decisions: "Markdown + JSON", "All eligible
  routes", "Separate surface records", "Record separately", "Semantic parity",
  "Readable IDs + hashes", "Only evidence-justified variants", "Focused
  artifact checks", "Hypotheses, no final order", "Classify and hand off",
  "Objective completeness gate", "Stop at one day", "Exclude the candidate",
  "Record and leave unresolved", "Per-agent fixture contracts", "Agent-centric
  records", "Sanitized facts and hashes", "URL + date + applicability", "Record
  only, do not fix", and "Keep eligibility separate".
- Treat Q5 as the final evidence-authority decision: official OpenAI
  documentation is exclusive for platform facts; repository evidence is
  allowed for project-only facts.
- Plan one evidence matrix keyed by claim, source, date, surface, applicability,
  classification, conflict status, and invalidation trigger.
- Plan one twelve-agent role-contract catalog and one agent-centric JSON
  manifest whose readable IDs bind to canonical hashes.
- Plan focused checks for JSON parseability, manifest version, twelve-agent
  coverage, required fields, unique IDs, deterministic hashes, provenance,
  sanitization, and Markdown/JSON agreement.
- End with an objective go/no-go packet plus unknowns assigned to G56R-002 or
  G56R-003.

## Required References
- docs/ai/specs/.process/G56R-001-design-concept.md
- docs/prd-codex-gpt-5-6-agent-routing.md, AC-1.1 through AC-1.7
- docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md
- .specify/memory/constitution.md
- CLAUDE.md
~~~

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| plan.md | ⏳ Pending | Evidence sequence, data model, validation, handoff |
| research.md | ⏳ Pending | Spec-local decision rationale if needed |
| data-model.md | ⏳ Pending | Agent, contract, candidate, provenance, fixture, handoff entities |
| contracts/ | ⏳ Pending | Only if Plan proves a review-visible data contract is necessary |
| quickstart.md | ⏳ Pending | Reviewer verification steps if useful |

---

## Phase 4: Domain Checklists

Run four requirements-quality checklists after spec.md and plan.md exist.

### 1. LLM Integration Checklist

~~~text
/speckit-checklist llm-integration

Focus on Candidate Route Baseline and Role Contracts requirements:
- Complete model-and-effort candidate eligibility and exclusion evidence.
- Prompt and contract hashing plus evidence-justified prompt/context variants.
- Separation of candidate hypotheses from executable or qualified routes.
- Null, unavailable, and unresolved handling for undocumented capabilities.
- Pay special attention to unsupported claims of executability, fallback, or
  optimality entering the baseline.
~~~

### 2. Integration Checklist

~~~text
/speckit-checklist integration

Focus on Candidate Route Baseline and Role Contracts requirements:
- CLI, desktop/app, app-server, and non-interactive evidence boundaries.
- Producer and consumer inventory across source, installer, skills, tests,
  generated payloads, cache, and installed state.
- Tracked source versus sanitized cache and installed-state evidence.
- Claude-to-Codex semantic parity for the two missing roles.
- G56R-001 artifact contract consumed by G56R-002.
- Pay special attention to evidence-class or client-surface conflation.
~~~

### 3. Reliability Checklist

~~~text
/speckit-checklist reliability

Focus on Candidate Route Baseline and Role Contracts requirements:
- Source freshness, applicability, conflicting-source handling, and invalidation.
- Deterministic twelve-agent completeness and Markdown/JSON agreement.
- Per-agent fixture backlog, telemetry requirements, and classified unknowns.
- One-day objective go/no-go terminal behavior.
- Pay special attention to stale or unverifiable claims presented as facts.
~~~

### 4. Security Checklist

~~~text
/speckit-checklist security

Focus on Candidate Route Baseline and Role Contracts requirements:
- Preservation of every safety, grounding, mutation, sandbox, approval, tool,
  skill, MCP, and output boundary.
- Hard exclusion of evidenced incompatible candidates.
- Sanitization of machine-local evidence and prohibition on credentials or
  home paths.
- No mutation of source, installed files, payloads, defaults, or unrelated
  configuration.
- Pay special attention to model or effort changes that silently alter
  authorization or mutation contracts.
~~~

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| llm-integration | Pending | Pending | Pending |
| integration | Pending | Pending | Pending |
| reliability | Pending | Pending | Pending |
| security | Pending | Pending | Pending |
| **Total** | Pending | Pending | Pending |

Address genuine gaps in spec.md or plan.md, rerun the affected checklist, and
document intentional scope cuts with rationale.

---

## Phase 5: Tasks

**Output:** specs/g56r-001-candidate-route-baseline/tasks.md

### Tasks Prompt

~~~text
/speckit-tasks

Create one ordered research-spike task sequence grounded in spec.md, plan.md,
and docs/ai/specs/.process/G56R-001-design-concept.md.

## Task Structure
- Use small, verifiable research tasks with explicit source and output paths.
- Map every task to AC-1.1 through AC-1.7 and the single maintainer user story.
- Define focused artifact invariants before finalizing the narrative or
  manifest; use those invariants as the research equivalent of test-first
  specifications.
- Mark a task P only when its source set and output are disjoint and its result
  can be reconciled deterministically.

## Required Ordering
1. Freeze evidence classes, surface boundaries, date and version pins, claim
   labels, sanitization, and conflict rules.
2. Inventory all active route-policy producers and consumers.
3. Build ten current role contracts and two semantic parity contracts.
4. Enumerate all evidence-supported candidates and justified prompt/context
   variants without runtime probing.
5. Define per-agent fixture contracts and classify the three current and nine
   missing fixtures.
6. Write the agent-centric JSON manifest and cited Markdown narrative.
7. Run focused parsing, coverage, ID, hash, provenance, sanitization, and
   cross-artifact agreement checks.
8. Classify unresolved capability and scoring questions and publish the
   objective G56R-002 go/no-go packet.

## Non-goals That Bound Tasks
- No agent, installer, prompt, payload, cache, installed-state, default-route,
  version, or unrelated configuration mutation.
- No executable capability probe, live scoring, qualification, final fallback
  order, or reusable validator framework.
- No work beyond one working day; incomplete objective criteria become a
  precise no-go with evidence and ownership.

Use the Q&A rationale when ordering tasks, especially Q3-Q5 for evidence
authority, Q14-Q15 for terminal behavior, Q16 for hard-contract exclusion, and
Q20-Q23 for local evidence and availability boundaries.
~~~

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | Pending |
| **Phases** | Pending |
| **Parallel Opportunities** | Pending |
| **User Stories Covered** | Pending |

---

## Atomicity Route

This table remains blank until G5. The read-only classifier records the route;
scaffolding does not create PR slices from this placeholder.

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | | Expected to reflect one research-only spike after task evidence exists |
| **Releasable** | | Filled by the classifier |
| **Signals** | | Filled by the classifier |
| **Warnings** | | Filled by the classifier |

~~~text
runner helper atomicity-route specs/g56r-001-candidate-route-baseline
~~~

---

## Phase 6: Analyze

### Analyze Prompt

~~~text
/speckit-analyze

Cross-check docs/prd-codex-gpt-5-6-agent-routing.md AC-1.1 through AC-1.7,
docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md,
docs/ai/specs/.process/G56R-001-design-concept.md, spec.md, plan.md, tasks.md,
and every supporting artifact.

Focus on:
1. Coverage: all twelve agents, every producer and consumer surface, every
   manifest field, per-agent fixture contracts, and all handoff artifacts have
   requirements and tasks.
2. Grounding: every platform claim uses current official OpenAI evidence; every
   project claim cites project evidence; facts, inferences, policies,
   assumptions, and unresolved claims remain distinct.
3. Consistency: Markdown and JSON agree on IDs, hashes, production routes,
   candidates, eligibility, availability, provenance, and unresolved items.
4. Scope: no task mutates production or installed state, probes runtime
   capability, performs qualification, orders fallbacks, fixes discovered
   defects, or adds reusable tooling.
5. Design drift: flag any conflict with Design Concept Goals, Non-goals, or
   Q1-Q23, especially the Q5 evidence-authority resolution.
6. Timebox: executable and scored unknowns are handed off rather than expanding
   the one-day spike.
~~~

### Analyze Severity Levels

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| CRITICAL | Blocks the handoff or violates the constitution or Design Concept | Must fix before G6 |
| HIGH | Significant coverage, grounding, or consistency gap | Fix unless explicitly scoped out |
| MEDIUM | Improvement opportunity | Review and decide |
| LOW | Minor inconsistency | Record if deferred |

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| Pending | Pending | Pending | Pending |

---

## Phase 7: Implement

### Implement Prompt

~~~text
/speckit-implement

Execute tasks.md and plan.md as a one-working-day, evidence-first research
spike. Use docs/ai/specs/.process/G56R-001-design-concept.md for the rationale
behind every scoping decision.

For each artifact increment:
1. EVIDENCE: invoke the selected capability and capture source, retrieval date,
   locator, Codex surface, applicability, and evidence class.
2. RECORD: add only claims supported by that evidence; label facts,
   inferences, proposed policies, assumptions, conflicts, and unresolved items.
3. STRUCTURE: keep agent-centric IDs, canonical hashes, production routes,
   candidates, capabilities, rationale, incompatibilities, qualification
   needs, provenance, and invalidation triggers aligned across Markdown and
   JSON.
4. VERIFY: run the planned focused checks for parseability, twelve-agent
   coverage, required fields, unique IDs, deterministic hashes, provenance,
   sanitization, and Markdown/JSON agreement.
5. HAND OFF: declare go only when the objective completeness rule passes;
   otherwise publish a precise no-go with missing evidence and its owning spec.

Keep platform facts official-docs-only. Use repository evidence only for
project facts. Sanitize local evidence. Record discovered defects without
fixing them. Stop at the one-day boundary and do not mutate agent definitions,
installers, prompts, payloads, cache, installed files, defaults, version
metadata, generated release artifacts, or unrelated configuration.
~~~

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Evidence and inventory | Pending | Pending | Official platform sources plus classified project evidence |
| Role contracts and candidates | Pending | Pending | Twelve-agent completeness |
| Narrative and manifest | Pending | Pending | Markdown plus JSON |
| Validation and handoff | Pending | Pending | Focused checks plus objective go/no-go |

---

## Post-Implementation Checklist

- [ ] All tasks are complete or explicitly handed to the owning downstream spec.
- [ ] docs/ai/research/codex-agent-route-candidates.md exists.
- [ ] docs/ai/research/codex-agent-route-candidate-manifest.json parses as JSON.
- [ ] Exactly twelve unique agents have complete semantic contract records.
- [ ] Candidate and contract IDs are readable, unique, and bound to canonical hashes.
- [ ] Every candidate has provenance, capabilities, rationale, incompatibilities,
  qualification requirements, and invalidation triggers.
- [ ] Official platform claims carry URL, date, surface, and applicability.
- [ ] Project, cache, and sanitized installed-state evidence remain distinct.
- [ ] No home path, credential, or unrelated local configuration appears.
- [ ] Markdown and JSON agree on identities, candidates, hypotheses, and unknowns.
- [ ] Historical prompt-emulation evidence is labeled non-release evidence.
- [ ] No final fallback ordering or executable-candidate claim appears.
- [ ] No production, install, payload, cache, version, or generated-release file changed.
- [ ] Focused artifact checks and the smallest relevant Python gate pass.
- [ ] The G56R-002 handoff records objective go/no-go, fixture backlog,
  telemetry needs, and every probe-dependent or score-dependent open question.

---

## Lessons Learned

### What Worked Well

- Pending

### Challenges Encountered

- Pending

### Patterns to Reuse

- Pending

---

## Project Structure Reference

~~~text
docs/
├── ai/research/
│   ├── codex-agent-route-candidates.md
│   └── codex-agent-route-candidate-manifest.json
├── ai/specs/.process/
│   ├── G56R-001-design-concept.md
│   └── G56R-001-workflow.md
├── ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md
└── prd-codex-gpt-5-6-agent-routing.md
specs/
└── g56r-001-candidate-route-baseline/
    ├── SPEC-MOC.md
    ├── spec.md
    ├── plan.md
    ├── tasks.md
    └── .process/
speckit-pro/
├── codex-agents/              # read-only current Codex source inventory
└── agents/                    # read-only Claude parity-contract source
tests/speckit-pro/
└── layer6-efficiency/         # read-only fixture-gap inventory
~~~

---

Template based on the installed shared SpecKit workflow template and populated
for G56R-001 from the fresh Grill Me Design Concept.
