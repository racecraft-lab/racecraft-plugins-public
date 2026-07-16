# SpecKit Workflow: HRNS-001 — Harness Surface Inventory and Gap Taxonomy

**Template Version**: 1.0.0
**Created**: 2026-07-15
**Purpose**: Drive HRNS-001 through SpecKit as one docs/process slice that establishes the durable harness surface inventory and gap taxonomy used by downstream HRNS specs.

---

## Design Concept

This workflow was enriched from a Grill Me interview run during
`$speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/HRNS-001-design-concept.md
```

The design concept is the source of truth for these scoping decisions:

- Use verified merged `origin/main` as the authoritative current-state cutoff;
  CAR and G56R do not block HRNS-001.
- Keep one canonical Markdown planning artifact rather than a runtime registry.
- Give every retained gap one stable `HRNS-GAP` identity and canonical row.
- Keep the artifact living and review-controlled through later HRNS specs.
- Evaluate external candidates from dated primary evidence without installing,
  prototyping, or adopting dependencies in HRNS-001.
- Treat an unclear self-improvement approval boundary as unknown and
  non-promotable.
- Cross-reference CAR/G56R ownership instead of omitting or absorbing their work.
- Complete the spec with traceable documentation proof, not new validator code.

> **Note:** Grill Me is human-in-the-loop only. It is not part of the autopilot
> loop. Once autopilot begins, clarifications happen through
> `/speckit-clarify` and the consensus protocol.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | Created spec.md and requirements checklist; G1 routed to Clarify |
| Clarify | `/speckit-clarify` | ✅ Complete | Resolved row schema, research boundaries, proof commands, and lifecycle updates |
| Plan | `/speckit-plan` | ✅ Complete | Created plan, research, data model, quickstart, and MOC refresh |
| Checklist | `/speckit-checklist` | ✅ Complete | Data integrity, security, integration, and reliability checklists generated; G4 passed |
| Tasks | `/speckit-tasks` | ✅ Complete | 35 evidence-first docs tasks generated; G5 passed |
| Analyze | `/speckit-analyze` | ✅ Complete | A1 parallel marker issue resolved; no open findings |
| Confidence Gate | G6.5 | ✅ Complete | Advisory confidence gate passed: 0.97 >= 0.90 |
| Implement | `/speckit-implement` | ✅ Complete | Taxonomy artifact created; 35/35 tasks complete; validation passed |
| Post | post-implementation | 🔄 In Progress | PR packet/body generation and draft PR creation complete; review remediation and retrospective remain pending |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | One independently testable story covers AC-1.1 through AC-1.10; no unresolved critical markers |
| G2 | After Clarify | Gap-row semantics, candidate evidence boundary, and completion proof are explicit |
| G3 | After Plan | Canonical artifact structure, source hierarchy, research method, and reviewability budget are approved |
| G4 | After Checklist | Every true requirement gap is fixed or recorded as an explicit non-goal/deferment |
| G5 | After Tasks | Tasks trace to every functional requirement and preserve the docs/process boundary |
| G6 | After Analyze | No CRITICAL or HIGH inconsistency remains across Design Concept, spec, plan, and tasks |
| G6.5 | Confidence Gate | Pre-Implement confidence is recorded and evaluated in advisory or strict mode |
| G7 | After Implementation | AC crosswalk, surface coverage, candidate evidence, links, and applicable repo checks pass |

---

## Prerequisites

### Constitution Validation

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin Structure Compliance | Treat `speckit-pro/` and `tests/speckit-pro/` as inventory evidence without relocating plugin or test files | Scope review plus `python3 tests/speckit-pro/run-all.py --layer 1` when applicable |
| Cross-Platform Runtime & Script Safety | Add no active repository tooling, Bash, `jq`, package, or runtime dependency | Changed-file review and constitution check |
| Test Coverage Before Merge | Use existing documentation/structural checks; do not create code solely to validate this planning artifact | Plan-selected targeted checks plus applicable Layer 1 validation |
| Conventional Commits | Use repository commit and PR-title conventions | `git log --oneline` and CI title validation |
| KISS, Simplicity & YAGNI | Keep one canonical Markdown artifact; do not add a machine registry without a consumer | Design Concept Q2/Q5 review |

**Constitution Check:** Pending G1 review.

### Worktree Bootstrap

- No bootstrap, install, build, or index command is documented in root
  `AGENTS.md` or `CLAUDE.md`.
- No package install, build, or code-index command was run during scaffolding.
- Any later command in those categories requires explicit operator approval.

### SpecKit Template Resolution

- `specify preset resolve spec-template` → `speckit-pro-reviewability` v1.0.0
- `specify preset resolve plan-template` → `speckit-pro-reviewability` v1.0.0
- `specify preset resolve tasks-template` → `speckit-pro-reviewability` v1.0.0

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | HRNS-001 |
| **Name** | Harness Surface Inventory and Gap Taxonomy |
| **Branch** | `hrns-001-harness-surface-inventory-gap-taxonomy` |
| **Feature directory** | `specs/hrns-001-harness-surface-inventory-gap-taxonomy` |
| **Design Concept** | `docs/ai/specs/.process/HRNS-001-design-concept.md` |
| **Canonical deliverable** | `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md` |
| **Dependencies** | None |
| **Enables** | HRNS-002, HRNS-003, HRNS-005, HRNS-009 |
| **Priority** | P1 |
| **Roadmap-declared tools** | None; no tool count or tool names are recorded |
| **Advisory size estimate** | 335 LOC, one suggested slice, status `ok` |

### Reviewability Setup Evidence

- Runner helper: `reviewability-gate`, mode `setup`.
- Target: `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md`.
- Result: `warn`, pass `true`, no blockers.
- Roadmap-wide parsed values: 330 reviewable LOC, 7 production files, 17
  total files, and 2 primary surfaces (`docs/process`, `harness/adapter`).
- Warnings: production files exceeded 6, total files exceeded 15, and primary
  surfaces exceeded 1. These values came from the full 14-spec roadmap target,
  not the isolated HRNS-001 entry.
- HRNS-001 entry-specific budget: primary surface `docs/process`, 260 projected
  reviewable LOC, 4 production files, 8 total files, result `within budget`.
- Grill Me estimator inputs: 1 user story, 4 files, 10 functional requirements,
  net-new work. Output: `{"estimated_loc":335,"suggested_slices":1,"status":"ok"}`.
- Split decision: keep one thin docs/process spec. O5 is not indicated.

### Success Criteria Summary

- [ ] The canonical artifact covers every harness surface named by AC-1.1 and
      tags every retained gap to at least one surface.
- [ ] Each retained gap has a stable identity, state, evidence, owner workflow,
      dependency posture, and downstream ownership.
- [ ] Evidence classes distinguish authoritative repository sources from
      generated distributions, caches, fixtures, raw transcripts, unreviewed
      chat, and derived indexes.
- [ ] The external-candidate matrix has dated primary evidence and the required
      fit, dependency, telemetry/privacy, license/supply-chain, maturity,
      compatibility, and recommendation fields.
- [ ] The OKF row records the pinned normative revision, draft maturity,
      reference-tooling posture, compatibility gaps, extension posture, and
      blocking/advisory/deferred status.
- [ ] Every discovered self-improvement loop has a closure classification;
      unclear boundaries are unknown and non-promotable, while open-ended
      recursive/self-modifying control loops are disallowed.
- [ ] AC-1.1 through AC-1.10 have an explicit crosswalk and the PR packet names
      the artifact, review scope, verification, and intentional deferrals.

---

## Phase 1: Specify

**When to run:** At the start of HRNS-001. Focus on what evidence and decisions
the taxonomy must expose, not implementation of later harness controls. Output:
`specs/hrns-001-harness-surface-inventory-gap-taxonomy/spec.md`.

### Specify Prompt

```text
/speckit-specify

## Feature: Harness Surface Inventory and Gap Taxonomy

### Problem Statement
Downstream harness-engineering specs currently risk rediscovering SpecKit Pro
surfaces, evidence boundaries, gap ownership, dependency posture, and safety
constraints. HRNS-001 must establish one durable, reviewable planning artifact
that gives later HRNS work a common factual baseline without becoming a runtime
registry or absorbing work already owned by CAR/G56R.

### User
The primary user is a SpecKit Pro maintainer or downstream HRNS spec author who
needs to determine what harness surfaces exist, which gaps remain, what evidence
is authoritative, who owns each gap, and whether an external candidate is only a
reference, a future spike, deferred, or unsuitable.

### P1 User Story
As a SpecKit Pro maintainer planning downstream HRNS work, I can use one
source-grounded taxonomy to trace every relevant harness surface and retained
gap to its state, evidence, owner workflow, dependency posture, safety closure,
and downstream spec ownership so that I do not duplicate work or make an
ungrounded dependency decision.

### Functional Requirements
1. Inventory current skills, agents, commands, helpers, runner surfaces,
   generated payloads, docs, workflow files, PR packets, tests, evals, and
   release gates from the verified merged baseline.
2. Give each retained gap one stable HRNS-GAP identity and surface tags.
3. Classify gaps as context, tool contract, permission, sandbox, memory/state,
   orchestration, verification, observability, HITL, security, garbage
   collection, or an explicitly justified extension.
4. Classify each gap as implemented, planned, deferred, duplicate, obsolete, or
   unknown; cross-reference CAR/G56R ownership without blocking or absorbing it.
5. Record repo-local, runner/helper, generated-doc/test, or future explicit
   dependency posture for every retained gap.
6. Create an external-candidate matrix for relevant schema, orchestration, eval,
   trace/observability, guardrail, workflow-runtime, coding-agent harness, and
   knowledge-format references using dated primary evidence only.
7. Record human-in-the-loop, human-on-the-loop, fully automated, disallowed, or
   unknown/non-promotable closure for workflows that influence future harness
   behavior.
8. Classify authoritative source evidence and explicitly exclude generated
   distributions, caches, fixtures, raw transcripts, unreviewed chat, and
   derived indexes as factual authority.
9. Cover the knowledge lifecycle concerns named by AC-1.9 as distinct gaps and
   downstream ownership areas.
10. Record the normative OKF revision, maturity, reference-tooling evidence,
    mismatches, extension posture, and blocking/advisory/deferred disposition.

### User-validated Decisions
- "Merged baseline": use verified origin/main as current state; unmerged work is
  planned reference evidence.
- "One Markdown artifact": the taxonomy is canonical planning documentation,
  not a runtime registry.
- "Stable gap IDs": one canonical row per retained gap.
- "Evidence matrix only": no candidate installation or prototype in HRNS-001.
- "Living reviewed artifact": later specs update the document through review.
- "Unknown and non-promotable": fail closed when a loop boundary lacks proof.
- "Traceable docs proof": use an AC crosswalk and coverage evidence, not a new
  validator.
- "Cross-reference owner": CAR/G56R gaps stay with their existing owner.
- "Dated primary sources": unsupported candidate fields are `unknown`.

### Constraints
- Keep implementation within docs/process and the declared reviewability budget.
- Cite repository paths/commits for local facts and current official primary
  sources for external facts; include an as-of date.
- Treat source artifacts as authoritative when generated or derived copies
  conflict, and record the conflict as a drift/gap finding.
- Do not edit runtime helpers, policies, eval gates, trace behavior, generated
  payloads, installed caches, or vendored content.
- Do not install, prototype, or make any external candidate required.
- Preserve the one-artifact design and stable identities without inventing a
  machine schema that has no consumer.

### Out of Scope
- Runtime helper, runner, policy, permission, trace, eval, orchestration,
  knowledge-lifecycle, indexing, or self-modification behavior.
- A generated or machine-readable taxonomy registry.
- CAR/G56R implementation or treating unmerged branches as current truth.
- External-candidate spikes, package installation, telemetry, or networked
  repository-content submission.
- Open-ended recursive self-improvement or automatic promotion of unclear loops.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 13 requirements; AC-1.1 through AC-1.10 coverage carried into Clarify |
| User Stories | 1 P1 story |
| Acceptance Scenarios | 5 scenarios |
| G1 Result | 3 `[NEEDS CLARIFICATION]` markers remain; proceed to Clarify |

### Files Generated

- [x] `specs/hrns-001-harness-surface-inventory-gap-taxonomy/spec.md`
- [x] `specs/hrns-001-harness-surface-inventory-gap-taxonomy/checklists/requirements.md`

### SpecKit Traceability Markers

| Marker | Purpose | Example |
|--------|---------|---------|
| `[US1]` | Primary maintainer story | `[US1] Maintainer traces a gap to its owner` |
| `[FR-001]` | Functional requirement | `[FR-001] Inventory all named harness surfaces` |
| `[NEEDS CLARIFICATION]` | Explicit unresolved choice | Candidate field semantics `[NEEDS CLARIFICATION]` |
| `[P]` | Parallel-safe evidence task | Independent surface inventory `[P]` |
| `[Gap]` | Missing requirement coverage | `[Gap] No OKF maturity disposition` |

---

## Phase 2: Clarify

**When to run:** After Specify if any row semantics, research boundary, or proof
command remains ambiguous. Keep each session to at most five questions.

### Clarify Prompts

#### Session 1: Canonical Gap Row

```text
/speckit-clarify Focus on the canonical HRNS-GAP row: finalize stable ID format,
required title/description, surface tags, taxonomy type, lifecycle state,
authoritative evidence, owner workflow, cross-roadmap owner, dependency posture,
downstream HRNS ownership, safety closure, and closure evidence. Preserve one
canonical row per retained gap and no machine-readable registry.
```

#### Session 2: Candidate Matrix Boundary

```text
/speckit-clarify Focus on the external-candidate matrix: define the starting
candidate set from PRD OQ-6, allowed primary-source types, as-of/version fields,
unknown-field handling, recommendation vocabulary, OKF normative revision
evidence, and the rule that HRNS-001 cannot authorize a required dependency or
run a prototype.
```

#### Session 3: Completion Proof

```text
/speckit-clarify Focus on completion proof: define how surface coverage,
evidence-class coverage, self-improvement-loop coverage, AC-1.1 through AC-1.10
traceability, Markdown links, intentionally deferred gaps, and the smallest
applicable repository documentation checks will be demonstrated in the artifact
and PR packet without adding validator code.
```

#### Session 4: Cross-lane and Living Updates

```text
/speckit-clarify Focus on cross-lane ownership and lifecycle: define how a CAR-
or G56R-owned gap is marked planned/external-owner, what evidence may be linked,
how unmerged work is kept non-authoritative, and how later HRNS specs update
states while preserving stable IDs and reviewed history.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Canonical gap row | 1 | `HRNS-GAP-###` IDs and canonical row fields are explicit |
| 2 | Candidate matrix | 1 | Evidence-matrix-only boundary, starting candidate set, primary-source types, and recommendation vocabulary are explicit |
| 3 | Completion proof | 1 | AC crosswalk, coverage proof, link review, deferment proof, and no-new-validator rule are explicit |
| 4 | Cross-lane lifecycle | 1 | CAR/G56R external-owner handling, unmerged reference evidence, and stable-ID update rules are explicit |

---

## Phase 3: Plan

**When to run:** After spec clarification. Output:
`specs/hrns-001-harness-surface-inventory-gap-taxonomy/plan.md`.

### Plan Prompt

```text
/speckit-plan

## Delivery Surface
- Canonical artifact: Markdown at
  docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md.
- Local evidence: current repository source, tests, root/nested agent guidance,
  constitution, PRDs, roadmaps/MOCs, workflows, ADRs, and approved issue/PR
  evidence.
- External evidence: dated official specifications, documentation,
  repositories, release/maturity material, and license sources.
- Runtime/code: none. Add no helper, script, schema registry, package, generated
  payload, or required dependency.
- Verification: existing Python-authoritative repository checks selected during
  Plan plus explicit document crosswalk and link review.

## Architecture Notes
- Quote and implement the Design Concept choice "One Markdown artifact": use a
  single document with explicit sections for baseline metadata, surface
  inventory, evidence authority, taxonomy definitions, canonical gap register,
  external-candidate matrix, self-improvement loop register, downstream
  ownership, and AC-1.* crosswalk.
- Quote and implement "Stable gap IDs": one canonical row owns each retained
  gap's identity and state; surface-oriented summaries link to those rows rather
  than duplicating them.
- Anchor local current-state claims to verified merged source. Record the
  baseline commit/as-of date and treat unmerged CAR/G56R evidence as planned
  references only.
- Quote and implement "Living reviewed artifact": define update rules that
  preserve IDs, make state transitions reviewable, and avoid silent deletion or
  renumbering.
- Quote and implement "Dated primary sources": every external recommendation
  has row-level evidence; unsupported fields remain `unknown`.
- Keep candidate recommendations non-binding. Required dependency adoption,
  telemetry, package installation, or prototypes need a later dedicated spec
  and supply-chain decision.
- Quote and implement "Unknown and non-promotable": missing loop-control
  evidence cannot be interpreted as HITL approval.
- Prefer explicit Markdown tables and short definitions over new abstraction or
  generated data. Preserve KISS/YAGNI.

## Constraints
- Re-read `docs/ai/specs/.process/HRNS-001-design-concept.md` before planning.
- Trace the plan to AC-1.1 through AC-1.10 and the single P1 user story.
- Keep the primary surface `docs/process`; explain any proposed file outside the
  roadmap's four-production/eight-total-file budget before adding it.
- Do not modify runtime helpers, policy, eval gates, traces, generated payloads,
  installed caches, or vendored `.specify/**` content.
- Do not use raw transcripts, unreviewed chat, caches, fixtures, generated
  distributions, or derived indexes as factual authority.
- Mark source conflicts and missing external evidence explicitly; never fill a
  matrix cell from memory or inference without labeling it.

## Reviewability Budget
- Setup gate on full roadmap: warn/pass with no blockers; parsed 330 LOC,
  7 production files, 17 total files, and 2 surfaces.
- HRNS-001 roadmap entry: 260 projected reviewable LOC, 4 production files,
  8 total files, docs/process primary surface, within budget.
- Grill Me advisory estimate: 335 LOC, 1 suggested slice, status ok.
- Split decision: one thin docs/process spec; O5 not selected.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ | Canonical document structure and evidence workflow |
| `research.md` | ✅ | Primary-source candidate and OKF evidence decisions |
| `data-model.md` | ✅ | Conceptual Markdown row/field semantics only, not runtime schema |
| `contracts/` | Skipped | No runtime/API/helper contract in HRNS-001 |
| `quickstart.md` | ✅ | Reproducible inventory and docs-verification procedure |

---

## Phase 4: Domain Checklists

**When to run:** After Plan. Run enriched prompts against both `spec.md` and
`plan.md`; these check requirement quality rather than implementation behavior.

### Recommended Domains

#### 1. Data Integrity Checklist

Why this domain: stable identities, canonical rows, lifecycle states, and
authoritative-evidence precedence are the core information-integrity contract.

```text
/speckit-checklist data-integrity

Focus on HRNS-001 requirements:
- One canonical row and stable identity for every retained gap.
- Exact allowed gap states, transition evidence, owner workflow, and downstream ownership.
- Source-authority precedence and conflict handling for generated or derived copies.
- AC-1.* crosswalk completeness and no duplicate row ownership.
- Pay special attention to: whether later specs can update a gap without renumbering, silently deleting, or forking its state.
```

#### 2. Security Checklist

Why this domain: the matrix records telemetry/privacy and supply-chain posture,
and self-improvement loops must fail closed when approval evidence is unclear.

```text
/speckit-checklist security

Focus on HRNS-001 requirements:
- Telemetry/privacy and licensing/supply-chain evidence for every external candidate.
- Disallowed open-ended recursive and self-modifying harness-control loops.
- Unknown/non-promotable handling when approval boundaries lack proof.
- Exclusion of raw transcripts, unreviewed chat, caches, and generated outputs as authority.
- Pay special attention to: language that could accidentally authorize network submission, package adoption, or automated promotion.
```

#### 3. Integration Checklist

Why this domain: HRNS-001 compares external specifications/tools and maps them
to downstream HRNS surfaces without establishing a runtime dependency.

```text
/speckit-checklist integration

Focus on HRNS-001 requirements:
- Candidate categories and mapped HRNS surfaces from PRD OQ-6.
- Primary-source version, maturity, license, compatibility, and local-first evidence.
- Normative OKF revision, reference-tooling mismatch, and extension-preservation posture.
- Explicit reference-only, future-spike, deferred, or unsuitable recommendation semantics.
- Pay special attention to: preventing a descriptive matrix row from being interpreted as dependency approval.
```

#### 4. Reliability Checklist

Why this domain: the artifact is intended to remain useful as later specs close
gaps, external sources drift, and CAR/G56R ownership changes.

```text
/speckit-checklist reliability

Focus on HRNS-001 requirements:
- Baseline commit/as-of metadata and reproducible local evidence paths.
- Living-update rules, stable identity preservation, and explicit state transitions.
- Unknown and obsolete findings, stale external evidence, and link maintenance.
- Cross-lane CAR/G56R references without treating unmerged state as authoritative.
- Pay special attention to: how a reviewer detects stale evidence or ownership drift without a new runtime registry.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| data-integrity | 12 | 0 | FR-001, FR-003, FR-005, FR-006, FR-010, SC-001, SC-004 |
| security | 12 | 0 | FR-008, FR-009, FR-010, PR Review Packet Requirements |
| integration | 12 | 0 | FR-006, FR-008, FR-012, SC-001 |
| reliability | 12 | 0 | FR-005, FR-009, FR-013, Assumptions, Independent Test |
| **Total** | 48 | 0 | G4 passed with 0 `[Gap]` markers |

### Addressing Gaps

1. Decide whether each finding is a true missing requirement.
2. Update `spec.md` or `plan.md` and cite the Design Concept decision involved.
3. Re-run the affected checklist.
4. If intentionally outside HRNS-001, record the owner/deferment rather than
   silently dropping the finding.

---

## Phase 5: Tasks

**When to run:** After all checklist gaps are resolved. Output:
`specs/hrns-001-harness-surface-inventory-gap-taxonomy/tasks.md`.

### Tasks Prompt

```text
/speckit-tasks

## Required Inputs
- specs/hrns-001-harness-surface-inventory-gap-taxonomy/spec.md
- specs/hrns-001-harness-surface-inventory-gap-taxonomy/plan.md
- docs/ai/specs/.process/HRNS-001-design-concept.md
- docs/prd-harness-engineering-uplift.md
- docs/ai/specs/harness-engineering-uplift-technical-roadmap.md

## Task Structure
- Organize all work under one independently testable P1 maintainer story.
- Start with baseline/evidence enumeration before writing conclusions.
- Use small tasks with explicit input paths, expected table/section output, and
  validation evidence.
- Mark independent surface or candidate research tasks `[P]` only when they do
  not write the same canonical section concurrently.
- Require dated primary evidence for every external fact and `unknown` for any
  unsupported matrix field.
- Reference the Design Concept Q&A for why merged-main authority, stable gap
  IDs, one Markdown artifact, cross-lane ownership, and loop fail-closed rules
  were chosen.

## Implementation Phases
1. Foundation: freeze baseline metadata, define canonical row semantics, and
   enumerate authoritative/non-authoritative evidence classes.
2. US1 inventory: map every named harness surface and create the canonical gap
   register with stable IDs, states, owner workflows, dependency posture, and
   downstream ownership.
3. US1 candidate/safety evidence: build the dated external-candidate and OKF
   rows plus self-improvement loop closure register.
4. US1 proof: complete AC-1.1 through AC-1.10 crosswalk, link review, deferred
   gap list, and PR-packet evidence.
5. Polish: run Plan-selected documentation/structural checks and reconcile only
   evidence-backed omissions.

## Non-goal Guardrails
- No runtime helper, runner, policy, eval, trace, generated-payload, or vendored
  file edits.
- No machine-readable taxonomy registry or new validator.
- No external package installation, prototype, required dependency, telemetry,
  or repository-content submission.
- No CAR/G56R implementation or unmerged-branch facts promoted to current state.
- No automatic promotion of unknown or open-ended self-improvement loops.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | 35 |
| Phases | Setup, Foundational, US1 implementation, Polish & Validation |
| Parallel Opportunities | None; one canonical artifact keeps implementation writes serialized |
| User Stories Covered | US1 |

---

## Atomicity Route

Fill this section after Tasks/G5 by running the read-only classifier against the
feature directory. Leave it blank during scoping; this records a decision but
does not create PRs or branches.

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | `one-navigable-PR` | `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope` |
| **Releasable** | `true` | `true`, or `false` when release safety requires it |
| **Signals** | `change-shape:modify-heavy` | Decisive structural findings |
| **Warnings** | none | Release-safety warnings, if any |

```text
runner helper atomicity-route specs/hrns-001-harness-surface-inventory-gap-taxonomy
```

---

## Phase 6: Analyze

**When to run:** Always run after Tasks.

### Analyze Prompt

```text
/speckit-analyze

Cross-check these four source-of-truth layers:
1. docs/ai/specs/.process/HRNS-001-design-concept.md
2. specs/hrns-001-harness-surface-inventory-gap-taxonomy/spec.md
3. specs/hrns-001-harness-surface-inventory-gap-taxonomy/plan.md
4. specs/hrns-001-harness-surface-inventory-gap-taxonomy/tasks.md

Focus on:
- Drift from the Design Concept Goals, Non-goals, and nine chosen answers.
- Complete AC-1.1 through AC-1.10 coverage and one P1 story traceability.
- One canonical Markdown artifact and one canonical row per retained gap.
- Merged-main authority versus planned CAR/G56R references.
- Candidate research tasks that require dated primary evidence and never imply
  dependency authorization.
- Unknown/non-promotable and disallowed loop semantics.
- Task paths that stay inside the docs/process scope and declared budget.
- Missing verification, link, PR-packet, or intentional-deferment evidence.
```

### Analyze Severity Levels

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| `CRITICAL` | Violates source authority, safety boundary, or core scope | Must fix before G6 |
| `HIGH` | Omits AC coverage, ownership, evidence, or a required matrix field | Must fix before implementation |
| `MEDIUM` | Weakens clarity, traceability, or reproducibility | Review and resolve or defer explicitly |
| `LOW` | Minor wording or navigation issue | Record for polish |

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| A1 | MEDIUM | Initial tasks used `[P]` markers for work that writes the same canonical Markdown artifact, creating a potential shared-file write conflict. | Resolved by removing `[P]` markers and recording serialized implementation in `tasks.md`. |

📊 Confidence: 0.97

- Task understanding: 0.96
- Approach clarity: 0.94
- Requirements alignment: 0.95
- Risk assessment: 1.00
- Completeness: 1.00

---

## Phase 6.5: Confidence Gate

**When to run:** After Analyze and before Implement.

| Field | Value |
|-------|-------|
| Mode | advisory |
| Threshold | 0.90 |
| Status | Pass |
| Evidence | `confidence-gate` request `hrns-001-g65-confidence-gate-retry`: composite 0.97; recommended action `proceed` |

The confidence gate records whether the spec, plan, tasks, and analyze results
are clear enough for implementation. In advisory mode, a low score is logged
with remediation notes but does not block Phase 7 unless a true G6 issue remains.

---

## Phase 7: Implement

**When to run:** After Analyze has no CRITICAL or HIGH findings and the Phase
6.5 confidence gate has been recorded.

### Implement Prompt

```text
/speckit-implement

## Evidence-first Approach
For each task:
1. READ: inspect the authoritative repository or dated primary source named by
   the task; do not rely on memory for factual claims.
2. RECORD: capture the minimal path/version/as-of evidence needed to reproduce
   the finding.
3. WRITE: update only the canonical taxonomy artifact or explicitly approved
   roadmap/PRD crosswalk surface.
4. REVIEW: compare the row against the Design Concept decision and relevant
   AC-1.* requirement.
5. VERIFY: run the smallest Plan-selected check, link review, or crosswalk proof.

## Required Inputs
- tasks.md and plan.md in
  specs/hrns-001-harness-surface-inventory-gap-taxonomy/
- docs/ai/specs/.process/HRNS-001-design-concept.md
- docs/prd-harness-engineering-uplift.md
- docs/ai/specs/harness-engineering-uplift-technical-roadmap.md

## Guardrails
- Produce one canonical Markdown planning artifact at
  docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md.
- Preserve stable gap IDs and one canonical row; do not fork state into
  per-surface duplicates.
- Treat repository source as current authority and unmerged CAR/G56R work as
  planned reference evidence only.
- Cite every external recommendation to dated primary evidence and use
  `unknown` where evidence is absent.
- Do not install, prototype, adopt dependencies, submit repository content,
  modify runtime controls, or hand-edit generated/vendored files.
- Consult the Design Concept Q&A for the rationale behind each boundary before
  resolving an apparent conflict.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Foundation | T001-T010 | 10/10 | Baseline authority, artifact skeleton, source/evidence schemas, row semantics, matrix schema, and loop rules recorded |
| US1 inventory | T011-T019 | 9/9 | Current-state boundary, surface rows, canonical gap register, owners, knowledge lifecycle gaps, and loop closures recorded |
| US1 candidate/safety evidence | T020-T025 | 6/6 | External candidate and OKF evidence matrix populated from dated primary sources |
| US1 proof | T026-T027 | 2/2 | AC-1.1 through AC-1.10 crosswalk and non-adoption guardrail review completed |
| Polish | T028-T035 | 8/8 | Placeholder sweep, link/evidence review, spec-index check, `git diff --check`, Layer 1, workflow/state, PR packet, and PR creation completed |

---

## Post-Implementation Checklist

### Canonical Post Rows

- [x] Post: Doctor Extension Check
- [x] Post: Verify Implementation
- [x] Post: Verify Tasks Phantom Check
- [x] Post: Code Review
- [x] Post: Integration Suite
- [x] Post: Reviewability Diff Gate
- [x] Post: Self-Review
- [x] Post: UAT Runbook Generation
- [x] Post: Final Reviewability Backstop
- [x] Post: PR Packet/Body Generation
- [x] Post: PR Body Generation
- [x] Post: PR Creation
- [ ] Post: Review Remediation
- [ ] Post: Retrospective

### HRNS-001 Completion Checks

- [x] All tasks are complete and trace to US1 plus AC-1.1 through AC-1.10.
- [x] `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md` is the only
      canonical taxonomy artifact.
- [x] Every retained gap has one stable ID, required tags/state/evidence,
      owner workflow, dependency posture, and downstream ownership.
- [x] Every external row has dated primary evidence or an explicit `unknown`.
- [x] OKF normative/maturity/compatibility/extension posture is explicit.
- [x] Every self-improvement loop has a safe closure classification.
- [x] Generated distributions, caches, fixtures, raw transcripts, unreviewed
      chat, and derived indexes are not presented as authoritative evidence.
- [x] CAR/G56R-owned gaps are cross-referenced without duplicated ownership.
- [x] Markdown links and the AC crosswalk have been reviewed.
- [x] Plan-selected documentation checks pass.
- [x] Applicable structural validation passes:
      `python3 tests/speckit-pro/run-all.py --layer 1`.
- [x] The PR packet names review scope, verification, and intentional deferrals.
- [x] HRNS taxonomy scope remains docs/process; the post-gate PR-packet failure
      required an intentional SpecKit Pro plugin fix, with generated release
      artifacts and installed-cache fixtures refreshed for both Claude Code and
      Codex.
- [ ] PR is created; review remains required before merge.

### Post Results

| Post Item | Status | Evidence |
|-----------|--------|----------|
| Doctor Extension Check | Pass with warnings | 3 pass, 2 warnings: `.specify/init-options.json` lacks `ai_assistant`; HRNS feature dir naming differs from numbered-feature convention |
| Verify Implementation | Pass | Placeholder sweep pass; spec index current; `git diff --check` pass; link/evidence review pass |
| Verify Tasks Phantom Check | Pass | `specs/hrns-001-harness-surface-inventory-gap-taxonomy/verify-tasks-report.md`: 35 verified, 0 partial/weak/not_found/skipped |
| Code Review | Pass after remediation | Review reported 2 HIGH and 3 MEDIUM issues; remediated closure evidence, candidate evidence fields, tracked counts, portable quickstart, lifecycle vocabulary, and roadmap/MOC status |
| Integration Suite | Pass via fallback | `FULL_VERIFY=N/A`; Layer 1 fallback passed 1428/1428 |
| Reviewability Diff Gate | Pass | Docs/process-only diff; no runtime/plugin source, generated payload, installed-cache, docs-site, or vendored changes |
| Self-Review | Complete | See self-review block below |
| UAT Runbook Generation | Skipped | No committed feature-local UAT runbook; `generate-uat-skeleton` is deferred |
| Final Reviewability Backstop | Proceed | Current reviewability evidence is committed and docs/process bounded |
| PR Packet/Body Generation | Pass | `speckit-pro-runner helpers pr-packet-output apply` emitted `specs/hrns-001-harness-surface-inventory-gap-taxonomy/.process/pr-packets/hrns-001.json`, body markdown, and validation result |
| PR Body Generation | Pass | PR body committed at `specs/hrns-001-harness-surface-inventory-gap-taxonomy/.process/pr-packets/hrns-001/body.md` |
| PR Creation | Pass | Draft PR opened: https://github.com/racecraft-lab/racecraft-plugins-public/pull/357 |

### Self-Review

1. **Tests executed?** `BUILD`, `TYPECHECK`, `LINT`, `UNIT_TEST`, and
   `INTEGRATION_TEST` are `N/A` from detected project commands. Executed checks:
   placeholder sweep, link/evidence review, `generate-spec-index-check`,
   `git diff --check`, verify-tasks, and `python3 tests/speckit-pro/run-all.py
   --layer 1` with 1428/1428 passing.
2. **Edge cases?** HRNS-001 is docs/process only. Edge cases from `spec.md`
   are covered in the taxonomy by CAR/G56R reference-only ownership,
   multi-surface canonical rows, `unknown` external evidence handling,
   unknown/non-promotable loop closure, and source-authority precedence.
3. **Requirements matched?** FR-001 through FR-013 and SC-001 through SC-005
   trace to completed tasks T001 through T035 and to the taxonomy AC crosswalk.
   Verify-tasks found 35 verified tasks and no flagged items.
4. **Follow-up & tidiness?** No actionable TODO/DEFERRED/OUT-OF-SCOPE markers
   were found in HRNS-001 artifacts. Intentional deferrals are explicitly named
   in the taxonomy and PR packet draft. Diff is docs/process scoped.

### PR Packet Draft

**What changed**

- Added `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md` as the
  canonical HRNS-001 surface inventory, gap taxonomy, external-candidate matrix,
  self-improvement loop register, OKF posture record, and AC-1.* crosswalk.
- Completed and marked HRNS-001 tasks/checklists and refreshed workflow/state
  evidence.

**Why**

- Downstream HRNS specs need a shared source-grounded baseline before changing
  context, helper/tool contracts, permissions, evals, traces, orchestration,
  OKF knowledge, or drift repair behavior.

**Non-goals**

- No runtime helper, runner, policy, eval, trace, generated-payload,
  installed-cache, vendored, or docs-site changes.
- No external package installation, prototype, dependency adoption, telemetry,
  or repository-content submission.
- No CAR/G56R implementation or promotion of unmerged branch state as current
  authority.

**Review order**

1. Review the taxonomy current-state boundary and evidence classes.
2. Review the surface inventory and `HRNS-GAP-###` canonical rows.
3. Review the external-candidate matrix and OKF posture.
4. Review the AC-1.1 through AC-1.10 crosswalk and deferment ownership.
5. Review workflow/state/task/checklist evidence.

**Scope budget**

- Primary surface: docs/process.
- New canonical artifact: `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`.
- Runtime/plugin source changes: none.
- Atomicity route: `one-navigable-PR`, releasable `true`.

**Traceability**

- AC-1.1 maps to the surface inventory.
- AC-1.2 through AC-1.5 map to the canonical gap register.
- AC-1.6 and AC-1.10 map to the external-candidate matrix and OKF posture.
- AC-1.7 maps to the self-improvement loop register.
- AC-1.8 maps to evidence classes.
- AC-1.9 maps to HRNS-GAP-008 through HRNS-GAP-013.

**Verification**

- Placeholder sweep: pass with quickstart exclusions for self-referential files.
- Link/evidence review: taxonomy Markdown links enumerated and reviewed.
- Spec index: `generate-spec-index-check` current.
- Whitespace: `git diff --check` pass.
- Layer 1: `python3 tests/speckit-pro/run-all.py --layer 1` pass,
  1428/1428.

**Known gaps and intentional deferrals**

- Runtime/helper/capability contract work remains HRNS-003.
- Permission/sandbox enforcement remains HRNS-004.
- Eval readiness remains HRNS-005.
- Trace/debug packets remain HRNS-006.
- Long-horizon orchestration remains HRNS-007.
- Drift/garbage collection remains HRNS-008.
- OKF bundle initialization, ingest, query, lint, index interop, and exchange
  remain HRNS-009 through HRNS-014.
- CAR/G56R routing work remains in CAR/G56R lanes.

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
docs/
├── prd-harness-engineering-uplift.md
└── ai/specs/
    ├── harness-engineering-uplift-technical-roadmap.md
    ├── harness-engineering-uplift-roadmap-MOC.md
    ├── harness-engineering-uplift-gap-taxonomy.md
    └── .process/
        ├── HRNS-001-design-concept.md
        └── HRNS-001-workflow.md
specs/
└── hrns-001-harness-surface-inventory-gap-taxonomy/
    ├── SPEC-MOC.md
    ├── spec.md
    ├── plan.md
    └── tasks.md
speckit-pro/               # Inventory evidence; no HRNS-001 runtime edits
tests/speckit-pro/         # Inventory/verification evidence; no new validator
```

---

Template based on the shared SpecKit workflow template and populated for
HRNS-001 from the roadmap, constitution, and Design Concept.
