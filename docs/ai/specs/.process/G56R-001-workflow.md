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
| Specify | /speckit-specify | ✅ Complete | 27 FRs, 10 outcomes, 0 clarification markers; G1 passed |
| Clarify | /speckit-clarify | ✅ Complete | 15 decisions applied across three sessions; G2 passed |
| Plan | /speckit-plan | ✅ Complete | Five design artifacts; G3 and reviewability estimator passed |
| Checklist | /speckit-checklist | ✅ Complete | 117/117 assessed; 9 gaps fixed; G4 passed |
| Tasks | /speckit-tasks | ✅ Complete | 26 ordered US1 tasks after Analyze remediation; G5 passed |
| Analyze | /speckit-analyze | ✅ Complete | Four initial findings resolved; rerun clean; G6 passed |
| Confidence Gate | G6.5 | ✅ Complete | Composite 0.99 exceeded the 0.90 advisory threshold |
| Implement | /speckit-implement | ✅ Complete | T001–T026 complete; terminal G56R-002 handoff is `go` |
| Post | Autopilot post-implementation items | ✅ Complete | All required Post items completed; exact head/base lookup verified PR #348 |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | AC-1.1 through AC-1.7 are testable; no unresolved requirement markers |
| G2 | After Clarify | Evidence classes, surface boundaries, canonical hashes, and terminal rules are explicit |
| G3 | After Plan | Constitution checks pass; the one-day sequence and focused validation are reviewable |
| G4 | After Checklists | All genuine gaps are resolved or explicitly scoped out |
| G5 | After Tasks | Every acceptance criterion and handoff artifact has ordered task coverage |
| G6 | After Analyze | No CRITICAL inconsistency or Design Concept drift remains |
| G6.5 | After Analyze Consensus | Confidence evidence and its advisory disposition are recorded before implementation |
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

### Autopilot Phase 0 Evidence

| Field | Result |
|-------|--------|
| Workflow binding | Current checkout and branch `g56r-001-candidate-route-baseline` verified by live git |
| Archive Sweep | `no_candidates`; current target excluded; no cleanup mutation |
| Runner prerequisites | `all_pass: true`; SpecKit CLI `0.11.8`; initialized worktree |
| Branch diagnostic | Runner returned an empty branch and `on_feature_branch: false`; live git is authoritative and Specify must not create a branch |
| Codex agents | Ten bundled agents current at user scope; dry-run install result `no_op` |
| Confidence mode | `advisory` |
| Project commands | Runner reported all generic slots `N/A`; repository validation remains Python-authoritative via `python3 tests/speckit-pro/run-all.py` |
| Preset | `speckit-pro-reviewability` v1.0.0 for spec, plan, and tasks |
| Focused baseline | `python3 tests/speckit-pro/run-all.py --layer 1` — 1427/1427 passed |
| Tier-2 relocation | Suppressed: the current spec already has `SPEC-MOC.md` `structureVersion: 1` |

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

**Constitution Check:** Verified at Phase 0 through the research-only scope,
structured-validation constraints, and the 1427/1427 Layer 1 baseline. Re-check
after Specify at G1, after Plan at G3, and during final closeout.

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
| Functional Requirements | 27 (FR-001 through FR-027) |
| User Stories | 1 P1 story with 9 independently testable scenarios |
| Measurable Outcomes | 10 (SC-001 through SC-010) |
| Acceptance Criteria | AC-1.1 through AC-1.7 traced in the requirements checklist |
| Quality Validation | 16/16 specification checklist items passed |
| G1 | PASS — `spec.md` exists with 0 `[NEEDS CLARIFICATION]` markers |
| Post-Specify Doctor | Core project health checks passed; missing plan/tasks are expected before later phases |
| Checkpoint Commit | `6cd17287` — `feat(g56r-001): complete specify phase` |

### Constitution Recheck at G1

| Principle | Status | Evidence |
|-----------|--------|----------|
| Cross-Platform Runtime and Script Safety | PASS | FR-026 requires Python 3.11+ structured checks and prohibits Bash, jq, packages, and reusable validation tooling |
| Test Coverage Before Merge | PASS | Requirements checklist 16/16; Layer 1 baseline remains 1427/1427 |
| KISS, Simplicity, and YAGNI | PASS | One research spike, focused disposable checks, 0 production LOC, and no reusable framework |
| Conventional Commits | PASS | Phase checkpoint uses the repository Conventional Commit format |
| Plugin Structure Compliance | PASS | All delivery surfaces remain under `docs/` and `specs/`, outside the shipped plugin |

### Files Generated

- [x] specs/g56r-001-candidate-route-baseline/spec.md
- [x] specs/g56r-001-candidate-route-baseline/checklists/requirements.md

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
| 1 | Evidence and surfaces | 5 | Source precedence, repository evidence roles, surface isolation, provenance fields, and conflict terminal rules added; Consensus skipped with 0 unresolved items |
| 2 | Manifest and identities | 5 | Manifest envelope, readable IDs, canonical hashes, complete per-agent records, and cross-artifact agreement rules added; Consensus skipped with 0 unresolved items |
| 3 | Local evidence and handoff | 5 | Sanitized evidence fields, exact 3/9 fixture inventory, focused checks, downstream ownership, and exact go/no payload added; Consensus skipped with 0 unresolved items |

### Clarify Gate Result

| Field | Result |
|-------|--------|
| G2 | PASS — 0 `[NEEDS CLARIFICATION]` markers |
| Consensus | Skipped after each session; 0 unresolved items |
| Fixture evidence | Exactly 3 current Codex fixtures and 9 missing role fixtures confirmed from the live repository |
| Security disposition | Explicit maintainer review required only if retained local fields or accepted security-relevant boundaries change |
| Human review | Normative field and no-go payload names require artifact review; no Clarify blocker remains |
| Post-Clarify hook | Optional git commit hook skipped because autopilot owns the per-phase checkpoint commit |
| Spec index | Regeneration completed as a no-op; index was current |
| Checkpoint Commit | `d2ed988b` — `feat(g56r-001): complete clarify phase` |

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
| plan.md | ✅ Complete | Evidence sequence, three delivery operations, validation, and terminal handoff |
| research.md | ✅ Complete | Ratified decision rationale without unresolved platform claims |
| data-model.md | ✅ Complete | Agent, contract, candidate, provenance, fixture, unknown, and handoff entities |
| contracts/ | ✅ Complete | Review-visible manifest contract; no reusable schema package |
| quickstart.md | ✅ Complete | Reviewer validation guide and expected outcomes |

### Plan Gate Result

| Field | Result |
|-------|--------|
| G3 | PASS — `plan.md` exists with 0 unresolved markers |
| Reviewability estimate | PASS — projected 0 production LOC, 3 new delivery files, 0 production files |
| Constitution recheck | PASS — Layer 1 structural validation 1427/1427; pre/post-design checks pass |
| Delivery boundary | Narrative, JSON manifest, and feature-local focused checker only |
| Post-Plan hooks | Optional traceability validator not invoked; optional git hook skipped because autopilot owns checkpoint commits |
| Spec index | Regenerated; `SPEC-MOC.md` now links all Plan artifacts |
| Checkpoint Commit | `26799d11` — `feat(g56r-001): complete plan phase` |

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
| llm-integration | 26/26 assessed | 0 | FR-006, FR-008–FR-020, FR-023–FR-027; no remediation required; Consensus skipped |
| integration | 29/29 assessed | 3 → 0 | FR-004, FR-006–FR-007, FR-013, FR-023–FR-025; resolved through spec-context consensus |
| reliability | 30/30 assessed | 2 → 0 | FR-005, FR-008, FR-016–FR-025; workday deadline and evidence invalidation rules added; Consensus skipped |
| security | 32/32 assessed | 4 → 0 | FR-006–FR-007, FR-010–FR-012, FR-021, FR-023–FR-024, FR-027; Consensus skipped |
| **Total** | **117/117 assessed** | **9 → 0** | All requirement-quality markers resolved |

### Consensus Resolution Log

| Domain / Item | Route | Resolution | Confidence |
|---------------|-------|------------|------------|
| integration CHK008 | spec-context | Added exact route-policy inventory entry fields, reciprocal lineage, authority, mismatch ownership, and objective set-completeness failure rules | High |
| integration CHK020 | spec-context | Added per-field Claude parity mappings with source locators, mapping states, justification, normalized-value agreement, and fail-closed handling | High |
| integration CHK025 | spec-context | Added G56R-002 admission binding, eligibility preservation, versioned capability snapshot, rejection, drift invalidation, and re-admission rules | High |

Round 1 resolved all three items without a security-boundary change. No Round 2
or human ambiguity review was required.

### Checklist Gate Result

| Field | Result |
|-------|--------|
| G4 | PASS — 0 `[Gap]` markers |
| Remediation | 9 genuine gaps fixed: 3 integration, 2 reliability, 4 security |
| Consensus | Integration items CHK008, CHK020, and CHK025 resolved in Round 1; all other domains had 0 unresolved items |
| Post-Checklist hook | Optional git commit hook skipped because autopilot owns the phase checkpoint |
| Spec index | Regenerated to link all four domain checklists |
| Checkpoint Commit | `73cd7d6d` — `feat(g56r-001): complete checklist phase` |

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
| **Total Tasks** | 26 (T001–T026) after Analyze remediation |
| **Phases** | 5 ordered research phases |
| **Parallel Opportunities** | 0; shared outputs and frozen-evidence dependencies make parallel edits unsafe |
| **User Stories Covered** | US1; all tasks map to one or more of AC-1.1 through AC-1.7 |
| **G5** | PASS — 26 tasks found on remediation rerun |
| **Post-Tasks hook** | Optional git commit hook skipped because autopilot owns checkpoint commits |
| **Spec index** | Regenerated to link `tasks.md` |
| **Initial task checkpoint** | `703080b8` — 22 tasks (T001–T022) generated by the Tasks phase |
| **Remediated checkpoint** | `b03c4438` — 26 tasks (T001–T026) after Analyze added the four missing validation/handoff tasks |
| **Analyze remediation** | Started the clock before checker/evidence work and added three focused RED/GREEN checker increments, the required Layer 4 test, and its suite-manifest declaration |
| **Tasks reviewability helper** | `reviewability-gate` tasks mode deferred because the installed runner supports setup mode only |
| **Reviewability fallback** | Setup evidence `warn` with `pass: true`; plan estimator `pass`; one atomic navigable PR; no marker plan required |

---

## Atomicity Route

This table remains blank until G5. The read-only classifier records the route;
scaffolding does not create PR slices from this placeholder.

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | one-navigable-PR | The three research delivery files plus three required validation paths remain atomic |
| **Releasable** | true | Classifier found a navigable single-PR shape |
| **Signals** | `change-shape:modify-heavy` | Advisory shape signal |
| **Warnings** | none | No classifier warning |

Layer planning is skipped because the route is not `split-PR`.

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
| C1 | CRITICAL | The checked-in checker lacked constitution-required focused Layer 4 coverage and suite membership | Added FR-026 coverage requirements, one focused test path, one Layer 4 suite declaration, and explicit RED/GREEN tasks |
| I1 | HIGH | Checker work preceded `started_at` and `deadline_at` | Reordered T001 so both timestamps are recorded before checker or evidence work |
| U1 | HIGH | The manifest content hash was self-referential and underspecified | Defined lowercase SHA-256 over canonical normalized JSON with `handoff.admission_binding.manifest_content_hash` omitted |
| I2 | HIGH | Capability-snapshot ownership conflicted with the G56R-002 dependency boundary | G56R-001 now records only the snapshot requirement; G56R-002 creates or selects and binds the runtime snapshot during admission |

| Verification | Result |
|--------------|--------|
| Analyze rerun | PASS — 0 CRITICAL, 0 HIGH, and no new CRITICAL/HIGH inconsistency |
| Consensus | Skipped — 0 unresolved items after deterministic local-contract remediation |
| G5 rerun | PASS — 26 tasks, 0 markers |
| G6 helper | PASS — 0 CRITICAL/HIGH findings, 0 markers |
| Reviewability re-estimate | PASS — projected 0 production LOC; final boundary is 4 new plus 2 modified declared implementation paths |
| Spec index | Current; regeneration was a no-op |
| Checkpoint Commit | `b03c4438` — `fix(g56r-001): resolve analyze findings` |

📊 Confidence: 0.99

- Task understanding: 0.99
- Approach clarity: 0.98
- Requirements alignment: 0.99
- Risk assessment: 1.00
- Completeness: 1.00

---

## Phase 6.5: Confidence Gate

### Confidence Gate Command

~~~text
runner helper confidence-gate
workflow_file: docs/ai/specs/.process/G56R-001-workflow.md
mode_name: resolved during Phase 0 (default advisory)
~~~

Record the confidence score, criterion breakdown, helper disposition, and any
focused remediation before Phase 7 begins.

| Field | Result |
|-------|--------|
| Composite | 0.99 |
| Threshold | 0.90 |
| Mode | advisory |
| Helper result | PASS; recommended action `proceed` |
| Lowest criterion | Approach clarity, 0.98 |
| Iterations | 1; no remediation required |

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
| Clock and checker TDD | T001–T008 | Complete | RED/GREEN: `0/4`→`7/7`, `7/14`→`14/14`, `14/20`→`20/20`, review `20/42`→`42/42`, recheck `42/45`→`45/45`; final review accepted |
| Evidence and inventory | T009–T013 | Complete | Reconciled official, project, and environment evidence; no blocking conflict; three owned downstream defects; focused test 45/45; completed tasks: T001–T013 |
| Role contracts and candidates | T014–T019 | Complete | Twelve immutable semantic contracts, canonical identities, candidates, fixtures, telemetry, and owned unknowns recorded; completed tasks: T014–T019 |
| Narrative and manifest | T020–T022 | Complete | Twelve lexical agent records and the exact normalized Markdown projection agree; focused test 45/45; completed tasks: T020–T022 |
| Validation and handoff | T023–T026 | Complete | Terminal `go`; focused 56/56; checker PASS twice; final uninterrupted default suite 2834/2834; completed tasks: T023–T026 |

---

## Post-Implementation Checklist

| Item | Status | Evidence |
|------|--------|----------|
| Post: Doctor Extension Check | Complete | PASS: 5 checks; 5 PASS, 0 WARN, 0 FAIL |
| Post: Verify Implementation | Complete | 26/26 tasks; checker PASS twice; focused 56/56; final uninterrupted default suite 2834/2834 |
| Post: Verify Tasks Phantom Check | Complete | 26 VERIFIED, 0 flagged after adversarial reconciliation |
| Post: Code Review | Complete | Three adversarial agents approved; five RepoPrompt review passes closed every cited defect and the final source verdict was `ZERO FINDINGS` |
| Post: Integration Suite | Complete | Layer 1 1427/1427; Layer 4 1221/1221; Layer 5 186/186; integration 257/257; default 2834/2834 |
| Post: Reviewability Diff Gate | Complete | User-authorized single combined PR; typed `Reviewability-Exception: infra` recorded without correctness/test waivers |
| Post: Self-Review | Complete | 0 edge-case gaps, requirement/task orphans, silent markers, or tidiness findings |
| Post: UAT Runbook Generation | Skipped | `skipped: generate-uat-skeleton deferred`; no committed source-derived runbook exists |
| Post: PR Body Generation | Complete | Schema 1.1 draft packet/body passed committed read-only validation with an independently authorized source-commit trailer; final artifacts are regenerated from this reconciled state |
| Post: PR Creation | Complete | Unique live PR [#348](https://github.com/racecraft-lab/racecraft-plugins-public/pull/348) verified with head `g56r-001-candidate-route-baseline` and base `main` |
| Post: Review Remediation | Complete | PR #348 threads are resolved; RepoPrompt findings closed source binding, body authorization, atomic no-clobber/durability reporting, secure capability preflight, UTF-8 handling, title validation, and exact 12-row Claude/Codex parity; final verdict `ZERO FINDINGS` |
| Post: Retrospective | Complete | 26/26 tasks, 100% spec adherence, 0 unresolved findings, and final adversarial remediation evidence recorded |

### Reviewability Diff Gate

| Field | Result |
|-------|--------|
| Status | WARN; `pass: true` |
| Full branch snapshot | final packet projection: 134 changed files under the user-authorized combined-PR exception |
| Original G56R boundary | Six paths: three delivery plus three validation; 0 production LOC/files |
| Shared plugin source | 13 reviewable `speckit-pro/` source paths, 1,702 changed lines; generated payloads and trust metadata are counted separately |
| Generated parity | Claude, Codex, and installed-cache payload/proof copies are generator-owned and independently parity-checked |
| Gate taxonomy | The legacy estimator reports 0 production files because plugin Python/Markdown/JSON paths are outside its `src/app/lib/scripts` taxonomy; the explicit source counts above prevent that result from hiding plugin impact |
| Atomicity | User-required `one-navigable-PR`; research evidence exposes the terminal failure and the shared repair proves the recovered path |
| Split disposition | Typed `Reviewability-Exception: infra`; file-count only, with no correctness, test, source-freshness, or PR-verification waiver |

### Original G56R Checkpoint Self-Review

This records the pre-recovery G56R slice and is retained as historical phase
evidence. It does not certify the later user-authorized combined plugin repair;
that diff receives a fresh final review and suite run before PR creation.

1. **Tests executed?** Yes. At `2026-07-14T23:58:19Z`, the final uninterrupted
   default run passed preflight plus L1 1427/1427, L4 1200/1200, and L5
   186/186 for 2813/2813 total. The direct integration command passed 257/257;
   focused artifacts passed 55/55 at that checkpoint; the historical
   checkpoint runner guard passed 11/11. The
   initial direct Layer 4 command also ran and passed before the final expanded
   suite. BUILD, TYPECHECK, and LINT are explicitly `N/A` in PROJECT_COMMANDS,
   not inferred successes.
2. **Edge cases?** No `[edge-case-gap]` finding.
   - AC-1.1 inventory, exact sets, and evidence references:
     `test-g56r-001-artifacts.py:688`, `:717`, `:915`, `:1108`.
   - AC-1.2 official evidence, surface isolation, and applicability:
     `:936`, `:1223`, `:1240`.
   - AC-1.3 contracts, routes, candidates, parity, and fixtures:
     `:825`, `:852`, `:865`, `:888`, `:981`, `:1007`.
   - AC-1.4 classification, sanitization, policy prohibitions, and source
     mismatches: `:736`, `:755`, `:1091`, `:1155`.
   - AC-1.5 timestamps, agreement, prose drift, and terminal handoff:
     `:736`, `:1033`, `:1050`, `:1070`.
   - AC-1.6 schema, IDs, hashes, bindings, projection, and malformed JSON:
     `:688`, `:806`, `:825`, `:837`, `:852`, `:1033`, `:1050`, `:1257`.
   - AC-1.7 fixture split, telemetry, and non-release evidence:
     `:1007`, `:1192`.
3. **Requirements matched?** Yes. FR-001–FR-027 all trace to completed tasks:
   FR-001→T020–T022; FR-002→T004/T020; FR-003→T014/T015/T020;
   FR-004→T011; FR-005→T012; FR-006→T014/T015; FR-007→T015;
   FR-008→T005/T006/T016; FR-009→T020/T021;
   FR-010→T005/T006/T017/T021; FR-011–FR-015→T017; FR-016→T010;
   FR-017→T009/T010; FR-018–FR-020→T009/T010/T013;
   FR-021→T009/T012; FR-022→T018; FR-023→T019/T021;
   FR-024→T007/T008/T025/T026; FR-025→T001/T025;
   FR-026→T002–T008/T023/T024; FR-027→T009/T017/T023. All T001–T026
   are checked and implemented by `a0c955d5`, with review hardening in
   `bd0d692c` and final evidence synchronization in `a7beee1e`; the fresh
   phantom report records 26 VERIFIED and no orphans.
4. **Follow-up and tidiness?** No `[TODO]`, `[DEFERRED]`, or
   `[OUT-OF-SCOPE]` markers occur in spec, plan, tasks, or branch commit
   subjects. The independent review and diff scan found no debug scaffolding,
   commented-out implementation, temporary fixture, or orphan file. Remaining
   research unknowns are explicitly owned by G56R-002, G56R-003, G56R-008,
   and G56R-009 in the handoff.

### UAT and PR Boundary

- UAT is `skipped: generate-uat-skeleton deferred`; no committed
  `specs/g56r-001-candidate-route-baseline/.process/uat-runbook.md` exists, so
  no author agent or unavailable validator was invoked.
- The original six-path G56R research slice remains 0 production LOC. The
  user subsequently required one PR that also contains the durable SpecKit Pro
  autopilot repair; the typed `infra` reviewability exception documents that
  combined route and waives no correctness or verification gate.
- The failure mode was that `pr-packet-output` could be deferred and PR
  creation could terminate as a skip. A packet could also outlive the source
  revision it described or self-authorize changed protected prose. The shared
  Python runner now emits revision-bound schema 1.1 packets whose protected
  body is independently authorized by the immutable source commit. Both Codex
  and Claude use the same 12-row Post inventory and make packet validation,
  push, idempotent PR reconciliation, and verified PR creation non-skippable.
- Draft source authorization commit `5b67f594` produced packet commit
  `8b3743d5`; committed read-only validation passed with `pr_blocked=false`.
  The rebased branch was pushed with an explicit OID lease,
  exact-head/base reconciliation returned no existing PR, and GitHub created
  [PR #348](https://github.com/racecraft-lab/racecraft-plugins-public/pull/348).
- A post-create lookup returned exactly one open PR with the recorded number,
  URL, title, head, and base. The mandatory review sweep found 0 unresolved
  threads. Packet artifacts are regenerated from this durable closeout state
  before final handoff so later state writes cannot invalidate source binding.

### PR #348 Review and Check Remediation

- `validate-docs` failed because
  `docs-site/src/content/docs/reference/tests.md` did not include the current
  test inventory. The repository generator refreshed that page and
  `pnpm --dir docs-site reference:check` now passes.
- Ten code-quality threads duplicated two intentional empty handlers across the
  shared runner, Claude/Codex distributions, and installed-cache fixtures. Two
  source comments now explain the benign directory-create race and best-effort
  temp cleanup; generator-owned copies and hashes were refreshed.
- One Copilot thread proposed a check-then-replace fallback when descriptor-
  relative no-follow writes are unavailable. That change was rejected because
  it restores the symlink-swap TOCTOU the repair closes. The intentional
  fail-closed behavior remains explicit and is shared by both client payloads.
- Remediation verification: focused mutation 37/37, read-only 49/49,
  spec-index 12/12, Post parity 48/48, payload confinement
  121/121, docs reference current, generated release artifacts current,
  integration 257/257, and final uninterrupted default suite 2834/2834.

### Final RepoPrompt Adversarial Remediation

- The first full pass found stale base binding, self-authorizing protected body
  evidence, a no-overwrite race, ambiguous committed durability state, platform
  prerequisite gaps, mutable Git snapshots, non-UTF-8 crashes, and multiline
  title acceptance. A focused lifecycle pass also found Claude/Codex resume and
  Post-ownership drift.
- The next source pass found four residual gaps: committed protected-body
  tampering, spec-index committed-state and platform-preflight behavior, and
  contradictory Post inventories. The following pass found one missing
  rename-at capability probe. Commits `ee1e6874` and `f7ad883a` closed them.
- The final clean-source review at `f7ad883a` returned `ZERO FINDINGS`.

### Final Research-Pin Remediation

- The final spec adversary found that the narrative, manifest, and normalized
  projection still named pre-rebase revision `7f8c1736…`, which is not present
  in the rebased branch history.
- The equivalent frozen checkpoint is `b03c4438…`; it resolves to a commit and
  is an ancestor of the current branch head. Every repeated project-evidence
  revision and both artifact hashes were refreshed around that checkpoint.
- Focused Layer 4 validation now fails unless the pinned revision exists and is
  a `HEAD` ancestor. The PR test job fetches full history so a shallow checkout
  cannot bypass this proof. The checker itself remains offline, read-only, and
  subprocess-free as required by the accepted plan.

- [x] All tasks are complete or explicitly handed to the owning downstream spec.
- [x] docs/ai/research/codex-agent-route-candidates.md exists.
- [x] docs/ai/research/codex-agent-route-candidate-manifest.json parses as JSON.
- [x] Exactly twelve unique agents have complete semantic contract records.
- [x] Candidate and contract IDs are readable, unique, and bound to canonical hashes.
- [x] Every candidate has provenance, capabilities, rationale, incompatibilities,
  qualification requirements, and invalidation triggers.
- [x] Official platform claims carry URL, date, surface, and applicability.
- [x] Project, cache, and sanitized installed-state evidence remain distinct.
- [x] No home path, credential, or unrelated local configuration appears.
- [x] Markdown and JSON agree on identities, candidates, hypotheses, and unknowns.
- [x] Historical prompt-emulation evidence is labeled non-release evidence.
- [x] No final fallback ordering or executable-candidate claim appears.
- [x] The original six-path G56R slice changed no production, install, payload,
  cache, version, or generated-release file; the later shared-runtime recovery
  is separately authorized by the user and typed exception.
- [x] Focused artifact checks and the smallest relevant Python gate pass.
- [x] The G56R-002 handoff records objective go/no-go, fixture backlog,
  telemetry needs, and every probe-dependent or score-dependent open question.

---

## Lessons Learned

### What Worked Well

- The feature-local checker, normalized projection, and human-prose hash made
  the terminal `go` reproducible from both machine and human review surfaces.
- Independent Post tracks found and resolved evidence-integrity and scope gaps
  before closeout; the final review disposition is APPROVE with low risk.

### Challenges Encountered

- The existing committed-path guard exposed a sixth implementation path only
  after the first implementation checkpoint; exact guard coverage and all
  scope declarations were then reconciled in `bd0d692c`.
- Adding the mandated verify-tasks report and durable recovery regressions
  increased the manifest-driven Layer 4 count, requiring repeated evidence
  refreshes before the final uninterrupted 2834/2834 run.
- Codex.app archived the outer worktree during two verification attempts. Both
  interrupted runs failed only after the checkout disappeared and are invalid
  infrastructure evidence; the worktree was unarchived, Git registration was
  restored, and the full suite then completed uninterrupted.
- The first Post closeout treated missing packet support as a deferred boundary
  and marked PR creation skipped. Adversarial recovery showed that completion
  must fail closed, and that packet source freshness must be cryptographically
  bound before any GitHub side effect.
- A packet-owned checksum was insufficient because a clean packet commit could
  change protected prose and recompute the checksum. The final flow dry-runs
  the body, records its digest on an otherwise packet-free source commit, and
  validates the committed packet against that independent authorization.
- Rebase reconciliation updated phase checkpoint fields but missed the repeated
  research-wide immutable revision. The final gate now verifies Git object
  reachability and ancestry after history rewrites.
- Official documentation describes reasoning controls differently across
  configuration, Subagents, App Server, and non-interactive surfaces. The final
  evidence record preserves that distinction: Subagents is the narrower
  CLI/desktop custom-agent authority, while App Server and non-interactive
  records use their own documented features. No undocumented intersection is
  promoted to platform fact.

### Patterns to Reuse

- Exercise existing committed-path guards before freezing a file-operation
  budget, and create mandatory verification artifacts before recording final
  manifest-driven suite totals.
- Keep candidate evidence local and surface/feature matched, use adversarial
  reference and sanitization cases in the first RED matrix, and prefer exact
  file allowances over directory prefixes.
- Track research-data volume separately from production LOC while preserving
  atomicity when narrative, manifest, checker, and tests mutually validate.

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
