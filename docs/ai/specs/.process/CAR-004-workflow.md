# SpecKit Workflow: CAR-004 — Policy Controls and Adaptive Comparators

**Template Version**: 1.0.0
**Created**: 2026-07-27
**Purpose**: Executable workflow for CAR-004. Phase prompts below are populated
from the technical roadmap scope and the grill-me design concept; the autopilot
consumes them phase by phase.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/CAR-004-design-concept.md
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
| Specify | `/speckit-specify` | ✅ Complete | 36 FRs, 23 scenarios; 6 adversarially-verified findings applied, incl. the AC-2.19 authentication correction |
| Clarify | `/speckit-clarify` | ✅ Complete | 2 sessions, all 5 markers resolved by 3-analyst consensus (4 unanimous/majority, 1 split at medium confidence) |
| Plan | `/speckit-plan` | ✅ Complete | plan/research/data-model/quickstart + 3 contract docs; 15 file operations, 0 production LOC |
| Checklist | `/speckit-checklist` | ✅ Complete | 3 domains sequential: 135 items, 57 gaps found, 57 remediated, 12 escalated to consensus |
| Tasks | `/speckit-tasks` | ✅ Complete | 64 tasks, 4 phases, 18 `[P]`, 25 RED→GREEN pairs, all 15 file ops covered |
| Analyze | `/speckit-analyze` | ✅ Complete | 3-lens audit: 19 findings, all 19 reproduced and applied; G6 pass, 0 CRITICAL/HIGH |
| Implement | `/speckit-implement` | ✅ Complete | 63/64 tasks (T062 is the manual operator smoke); suite 4909/4909, L7 257/257, L8 12/12; 0 phantoms |

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
| II. Cross-Platform Runtime & Script Safety | Repository tooling stays on Python 3.11+ standard library; no new Bash or `jq` dependency | Review imports in new `lib/` and `unit/` files |
| IV. Test Coverage Before Merge | Every new contract, validator, and fixture path covered by the repository suite | `python3 tests/speckit-pro/run-all.py --layer 1` while iterating; full suite per `tests/speckit-pro/suite-manifest.json` before PR |
| VI. KISS, Simplicity & YAGNI | Additive-only schemas; no speculative control variants beyond the three frozen by AC-2.17 | Code review against the design concept's Non-goals |

**Constitution Check:** ✅ (verified at scaffold — the spec surface is repository-only validation; no plugin runtime, payload, or shipped-default change)

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | CAR-004 |
| **Name** | Policy Controls and Adaptive Comparators |
| **Branch** | `car-004-policy-controls-comparators` |
| **Dependencies** | CAR-003 (merged, PR #385) — evaluation runner, contracts, corpus, analysis machinery |
| **Enables** | CAR-005 (availability/fallback simulation); CAR-011 consumes the frozen controls for its comparison |
| **Priority** | P1 |

### Success Criteria Summary

From the technical roadmap scope and AC-2.17:

- [ ] Three controls — unpinned, adaptive, orchestration-changing — are defined, content-addressed, and frozen as evaluation fixtures (no fourth arm; Q2)
- [ ] Each control's execution contract, parameters, observable escalation signals, retry and cancellation bounds, and evidence requirements are frozen; adaptive controls cannot choose a model or effort outside the frozen candidate set
- [ ] Control-eligibility floors, dominance metrics and margins (Pareto + 10% relative per component; Q6/Q13), confidence method, multiplicity position, and the untouched CAR-011 comparison partition are frozen
- [ ] The messaging consequence is encoded as a machine-readable verdict-to-claim-class mapping (Q9)
- [ ] Control execution and telemetry validate through synthetic replay plus one bounded live smoke per control (Q10/Q15) without consuming selection or confirmation partitions
- [ ] A partition guard test proves the reserved CAR-011 partition is untouched (Q8)
- [ ] A CAR-004 twin-handoff doc records every new contract member G56R-004 must mirror (Q1)

### Reviewability Budget (setup gate, 2026-07-27)

Recorded from the authoritative `reviewability-gate` setup run against the
CAR-004 roadmap section: **pass** — reviewable LOC 250, production files 0,
total files 10, primary surface `harness/fixtures` (1). Estimator
(`estimate-spec-size`, roadmap signal convention): 250 LOC, 1 slice, status
ok. Single vertical slice; no split decision required.

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/car-004-policy-controls-comparators/spec.md`

### Specify Prompt

```text
/speckit-specify

## Feature: CAR-004 Policy Controls and Adaptive Comparators

### Problem Statement

The CAR program will ship one static twelve-agent routing policy. Before that
policy exists, the program must freeze the policy-level comparators that bound
its final efficiency claim — otherwise the comparators could be constructed
after the static core's results are known, and the release wording could not
be trusted. CAR-004 defines, exact-treatment validates, and freezes the three
AC-2.17 controls (unpinned, adaptive, orchestration-changing) plus the
dominance rule, margins, comparison partition, and messaging consequence that
CAR-011 will later apply. CAR-004 itself concludes nothing about dominance.

### Users

- CAR-011 (primary consumer): compares the final frozen static core against
  these controls on predeclared secondary arms.
- CAR-005 through CAR-010: inherit the frozen candidate-set boundary and the
  reserved-partition guard.
- G56R-004 (Codex twin): mirrors the new contract members via the CAR-004
  twin-handoff doc.
- Release reviewers: read the machine-readable messaging mapping to validate
  release wording.

### User Story

One story (single vertical slice, estimator status ok): as the routing
program, freeze the three policy controls and their comparison rules as
content-addressed, replay-validated contracts so the CAR-011 comparison is
predeclared and tamper-evident.

### Design decisions to encode (from the design concept Q&A log)

- Exactly three controls per AC-2.17; no justified-high-effort fourth arm —
  the all-max immutable production comparator already fills that role on the
  Claude side; record as sanctioned divergence in the twin-handoff (Q2).
- Contracts are new additive schemas in
  tests/speckit-pro/layer6-efficiency/contracts-claude/ referencing frozen
  CAR-003 schemas by $id/digest; no edit to any mirrored member (Q1, Q7).
- Adaptive signals bind only to existing stable trace/score-bundle members:
  terminal state, failure plane/code, retry count, raw-token/duration budget
  thresholds; no new telemetry (Q3).
- Adaptive discipline: at most one escalation per objective to the
  next-higher qualified route; de-escalation only between objectives after
  N = 3 consecutive clean passes; never mid-objective; always inside the
  frozen candidate set (Q11, Q14).
- Unpinned control: one arm bound to the environment contract's pinned
  parent-session model/effort; different parent = different control version
  by content-address (Q4).
- Orchestration-changing control: parent-plus-children aggregate accounting
  (raw token vector, duration, retries summed across every automatically
  spawned child) under a content-addressed topology descriptor; policy-level
  only (Q5).
- Dominance: CAR-003's environment-independent Pareto rule with a 10%
  relative per-component practical margin; retries and compaction may not
  worsen; mixed or inconclusive means no dominance and no messaging
  restriction (Q6, Q13).
- Reserved CAR-011 comparison partition: named content-addressed registry
  entry plus a unit-test guard proving non-consumption (Q8).
- Messaging consequence: machine-readable verdict-to-claim-class mapping in
  the control-comparison contract (Q9).
- Validation: synthetic replay for all three controls plus one bounded
  live smoke each — subscription-authenticated, never API-key, per PRD AC-2.19
  as amended 2026-07-26 (max 5 non-reserved objectives, 1 repetition,
  1M raw-token ceiling, 30-minute wall-clock) proving a real dispatch-time
  escalation, a real inherit resolution, and a real parallel child
  aggregation respectively (Q10, Q15).

### Constraints

- Python 3.11+ standard library only; repository-only surface (no plugin
  runtime, payload, or shipped-default change).
- No outcome-bearing scored evidence; no consumption of selection or
  confirmation partitions; smoke rows are non-scored.
- Durable file names (never coupled to the spec ID) for scripts and tests.
- Per-run smoke outputs stay git-ignored; only consolidated/contract
  artifacts commit.

### Out of Scope

- Concluding dominance (CAR-011 owns the comparison).
- Any production adaptive-routing or orchestration feature.
- Edits to frozen CAR-003 schemas, including CAR-012-listed mirrored members.
- New telemetry fields or reopening CAR-002's telemetry profile.
- Unpinned-control matrix over multiple parent sessions.
- Subscription-authenticated smoke rows.
```

### Specify Results

<!-- Fill in after running the command -->

| Metric | Value |
|--------|-------|
| Functional Requirements | |
| User Stories | |
| Acceptance Criteria | |

### Files Generated

- [ ] `specs/car-004-policy-controls-comparators/spec.md`

### SpecKit Traceability Markers

Use these markers in spec.md for traceability through later phases:

| Marker | Purpose | Example |
|--------|---------|---------|
| `[US1]`, `[US2]` | User story reference | `[US1] Freeze the three controls` |
| `[FR-001]` | Functional requirement | `[FR-001] Adaptive signals bind to stable trace members` |
| `[NEEDS CLARIFICATION]` | Flag for Clarify phase | `Smoke token ceiling [NEEDS CLARIFICATION]` |
| `[P]` | Parallel-safe task | `[P] Can run alongside other tasks` |
| `[Gap]` | Missing coverage | `[Gap] No task covers the partition guard` |

---

## Phase 2: Clarify (Optional but Recommended)

**When to run:** When spec has areas that could be interpreted multiple ways. 10-20 minutes here saves hours of rework later.

**Best Practice:** Maximum 5 targeted questions per Clarify session.

### Clarify Prompts

#### Session 1: Twin parity and contract membership

Seeded from design-concept Open Question 1.

```text
/speckit-clarify Focus on the twin-handoff contract surface: exactly which new
schema members, enums, and identifiers G56R-004 must mirror; how the
sanctioned third-control divergence (orchestration-changing here,
justified-high-effort there) is recorded so it does not read as parity drift;
and what happens to any member the twin cannot mirror (CAR-012-class listing).
```

#### Session 2: Numeric registry freeze

Seeded from design-concept Open Question 2.

```text
/speckit-clarify Focus on the frozen numeric registry entries: the
per-component 10% relative dominance margin map serialization; the N = 3
de-escalation threshold; the smoke caps (5 objectives / 1 rep / 1M raw
tokens / 30 min — the token and time ceilings were flagged
moderate-confidence at scoping); and the multiplicity/alpha position of the
CAR-011 secondary control arms.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Twin parity | | |
| 2 | Numeric registry | | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/car-004-policy-controls-comparators/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack

- Language: Python 3.11+ standard library only (constitution principle II)
- Surface: repository-only validation under
  tests/speckit-pro/layer6-efficiency/ and tests/speckit-pro/unit/
- Contracts: JSON Schema documents in
  tests/speckit-pro/layer6-efficiency/contracts-claude/ (draft/convention
  matching the CAR-003 schemas they sit beside)
- Validators: modules in tests/speckit-pro/layer6-efficiency/lib/ following
  the claude_*.py naming convention
- Testing: unit tests in tests/speckit-pro/unit/ registered through
  tests/speckit-pro/suite-manifest.json; layer runner
  python3 tests/speckit-pro/run-all.py

## Constraints

- Additive only: reference frozen CAR-003 schemas by $id/digest; never edit a
  mirrored member (the joint-change rule from the CAR-012 record).
- Durable names: no script or test filename coupled to the CAR-004 spec ID.
- Per-run smoke outputs stay git-ignored; follow the existing layer6
  .gitignore allow-rule pattern if any consolidated artifact must commit.
- No new telemetry fields; every adaptive signal binds an existing stable
  member of the CAR-003 trace/score-bundle contracts.
- The reserved CAR-011 partition is registry-declared and guard-tested; no
  CAR-004 evidence row may reference its members.

## Architecture Notes

- Follow the established schema + lib + replay-fixture pattern: each new
  contract gets a schema in contracts-claude/, a validator in lib/, synthetic
  replay fixtures under
  tests/speckit-pro/layer6-efficiency/fixtures-controls/, and unit coverage.
- Content-address every control (execution contract, parameters, signals,
  bounds, topology descriptor) so any change produces a new control identity.
- The control-comparison contract carries: eligibility floors (identical to
  the candidate mandatory gates per AC-2.17), the Pareto dominance rule with
  the per-component relative margin map, the confidence method and
  multiplicity position (predeclared secondary arms for CAR-011), the
  reserved-partition binding, and the verdict-to-claim-class messaging
  mapping (dominant / not-dominant / inconclusive -> permitted wording
  classes).
- Orchestration-changing aggregation: define the child-work summation rule
  over the complete raw token vector, duration, and retries; replay fixtures
  must include a multi-child case proving the aggregate equals the sum.
- Re-read docs/ai/specs/.process/CAR-004-design-concept.md for the rationale
  behind any decision the prompts compress.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Technical context, execution flow |
| `research.md` | ⏳ | Decision rationales (if needed) |
| `data-model.md` | ⏳ | Entities and types |
| `contracts/` | ⏳ | Control-contract specifications |
| `quickstart.md` | ⏳ | Developer onboarding |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates both spec AND plan together. Run multiple times for different domains.

**Best Practice:** Don't guess which domains to check. Analyze the spec first, then generate enriched prompts with spec-specific focus areas.

### Step 1: Analyze Spec for Recommended Domains

Domain signals for this spec: JSON contract schemas and content-addressing
(**data-integrity**), escalation/failure/retry semantics and bounded recovery
(**error-handling**), and dispatch-time model-parameter behavior with
token-vector accounting (**llm-integration**). UI, API-endpoint, streaming,
and security domains do not apply to a repository-only evaluation-contract
surface.

### Step 2: Run Enriched Checklist Prompts

#### 1. data-integrity Checklist

Why this domain: the spec's core output is frozen, content-addressed contract
data whose integrity CAR-011 depends on.

```text
/speckit-checklist data-integrity

Focus on CAR-004 Policy Controls and Adaptive Comparators requirements:
- Content-address completeness: every control identity covers its execution
  contract, parameters, signals, bounds, and (for orchestration) topology
  descriptor — nothing hash-relevant left outside the address.
- Additive-only discipline: new schemas reference frozen CAR-003 schemas by
  $id/digest and no mirrored member is edited.
- Reserved-partition registry entry: membership is content-addressed and the
  guard test's failure condition actually covers replay AND smoke rows.
- Pay special attention to: the verdict-to-claim-class messaging mapping —
  it must be unambiguous and total over dominance verdict states.
```

#### 2. error-handling Checklist

Why this domain: the adaptive control is entirely defined by its response to
failure signals, and the smoke runs must prove bounded behavior.

```text
/speckit-checklist error-handling

Focus on CAR-004 Policy Controls and Adaptive Comparators requirements:
- Escalation discipline: one step per objective, de-escalation only between
  objectives after N = 3 clean passes, no oscillation, no route outside the
  frozen candidate set.
- Signal totality: every escalation-relevant terminal state and failure
  plane/code maps to exactly one policy response; no unmapped signal.
- Retry and cancellation bounds are explicit and replay-provable.
- Pay special attention to: interaction between adaptive escalation and the
  platform route-change rule — a platform-initiated route change must stay
  non-scorable and must not be read as policy escalation.
```

#### 3. llm-integration Checklist

Why this domain: controls are exercised through real dispatch-time model
parameters and metered by the raw token vector.

```text
/speckit-checklist llm-integration

Focus on CAR-004 Policy Controls and Adaptive Comparators requirements:
- Exact treatment for smoke runs: real dispatch-time model switching for
  adaptive, real inherit resolution for unpinned, real parallel dispatch with
  child aggregation for orchestration-changing.
- Raw-token-vector accounting: cache-write TTL classes and cache-read
  components preserved through the parent+children aggregation.
- Smoke bounds: 5 objectives / 1 rep / 1M tokens / 30 min recorded through
  the experiment-policy budget fields; non-scored labeling explicit.
- Pay special attention to: cache isolation between arms so one control's
  smoke cannot warm another arm's cache (CAR-003's crossover-distortion rule).
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| data-integrity | | | |
| error-handling | | | |
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

**When to run:** After checklists complete (all gaps resolved). Output: `specs/car-004-policy-controls-comparators/tasks.md`

### Tasks Prompt

```text
/speckit-tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: contracts -> validators -> fixtures -> guard test ->
  smoke harness -> twin-handoff doc
- Mark parallel-safe tasks explicitly with [P]
- Organize by the single user story; TDD-first (schema/validator tests
  precede implementations)

## Implementation Phases
1. Foundation: control-contract schemas + content-addressing (additive only)
2. Validators and replay fixtures per control (unpinned, adaptive,
   orchestration-changing) — the multi-child aggregation fixture is required
3. Comparison contract: floors, Pareto margins, partition registry entry +
   guard test, messaging mapping
4. Bounded smoke harness entries + twin-handoff doc + suite-manifest
   registration

## Constraints
- Unit tests live in tests/speckit-pro/unit/ with durable (non-spec-ID)
  filenames; register in tests/speckit-pro/suite-manifest.json.
- Fixtures live under tests/speckit-pro/layer6-efficiency/fixtures-controls/.
- Bound task generation by the design concept's Non-goals: no scored
  campaign tasks, no production routing feature tasks, no CAR-003 schema
  edits, no new telemetry. Flag any task that would cross these boundaries.
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

Recorded 2026-07-28 from the read-only classifier run against
`specs/car-004-policy-controls-comparators`.

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | `true` | `true`, or `false` for a destructive-migration or concurrency-sensitive change (a passing CI run does not prove such a change is safe to release). |
| **Signals** | `change-shape:modify-heavy` | The decisive detector findings behind the route and releasability reading (may be empty when the classifier abstains). |
| **Warnings** | *(none)* | Any release-safety warning attached to the change (empty when there is no releasability risk). |

## Layer Plan

**Status: `skipped` — non-split route.** The layer planner runs only when the
atomicity route is exactly `split-PR`. This change classified as
`one-navigable-PR`, so no layer-plan envelope is produced and the run continues
with route context only. No PR emission or branch splitting is wired.

## Reviewability Evidence Chain

The installed runner registers `reviewability-gate` tasks mode as **deferred**,
so it was not invoked. Deferral recorded: helper `reviewability-gate`, requested
mode `tasks`, reason *deferred on the installed runner — setup mode only*. The
fallback evidence chain is current and all-passing:

| Source | Result |
|---|---|
| Setup-mode gate at scaffold (2026-07-27) | `pass` — 250 LOC, 0 production files, 10 total, 1 surface |
| Plan-phase `estimate-reviewable-loc` (2026-07-28) | `pass` — projected 0 production LOC, 15 declared file operations (13 new, 2 modified) |
| Operator-ratified split decision | none required; single vertical slice |

To produce the decision, run the classifier against the feature directory:

```text
runner helper atomicity-route specs/car-004-policy-controls-comparators
```

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```text
/speckit-analyze

Focus on:
1. Constitution alignment — Python 3.11+ stdlib only, additive-only schema
   discipline, durable filenames
2. Coverage gaps — every FR and the AC-2.17 clauses (three controls, floors,
   dominance rule, margins, multiplicity, partition, messaging) have tasks
3. Consistency between task file paths and the layer6 harness structure
4. Design-concept drift — docs/ai/specs/.process/CAR-004-design-concept.md is
   the source of truth for scoping decisions; if spec.md, plan.md, or
   tasks.md contradicts it (control count, margin value, N = 3 threshold,
   smoke caps, additive-only rule) the downstream artifact is wrong unless a
   dated revision note says otherwise
5. Verify no task edits a frozen CAR-003 schema or consumes a reserved
   partition member
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
1. Run `python3 tests/speckit-pro/run-all.py --layer 1` and confirm green
   before making changes
2. Verify you are on `car-004-policy-controls-comparators` (never main)
3. Re-read docs/ai/specs/.process/CAR-004-design-concept.md — decisions
   captured there but missing from tasks.md are gaps to surface before
   coding, not silently drop

### Implementation Notes
- Match the CAR-003 conventions in contracts-claude/ and lib/claude_*.py —
  schema style, validator structure, error taxonomy discipline.
- Replay fixtures are deterministic: no timestamps or randomness that break
  byte-stable replays.
- The bounded live smokes are developer-local, run on the supported subscription
  authentication path (never API-key, per PRD AC-2.19 as amended 2026-07-26), and
  non-scored; their per-run outputs stay git-ignored.
- The smallest useful check while iterating is the affected unit test file;
  run the broader suite (per suite-manifest.json) before the PR.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Contract schemas | | | |
| 2 - Validators + replay fixtures | | | |
| 3 - Comparison contract + partition guard | | | |
| 4 - Smoke harness + twin-handoff | | | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in tasks.md
- [ ] Full repository suite passes per `tests/speckit-pro/suite-manifest.json`
- [ ] New unit tests registered in the suite manifest
- [ ] Docs reference regenerated (`pnpm --dir docs-site install` once per worktree, then `pnpm --dir docs-site reference:generate`) — new `.py` files under `tests/speckit-pro/` stale the generated `reference/tests.md`, and CI's validate-docs job runs `reference:check` against it
- [ ] No frozen CAR-003 schema modified (additive-only verified in the diff)
- [ ] Partition guard test proves the reserved CAR-011 partition untouched
- [ ] Twin-handoff doc lists every member G56R-004 must mirror
- [ ] PR title passes the release-readiness gate (`<type>(<lowercase-scope>): <plain English description>`)
- [ ] PR created and reviewed
- [ ] Merged to main branch

---

## UAT Runbook (fail-open; logged)

**Outcome: SKIPPED — deferred helper. No skeleton was generated, and none was
fabricated.**

`generate-uat-skeleton` is **registered but deferred on the installed runner**.
Deferred helpers must not be invoked, so it was not called and no UAT skeleton
exists for CAR-004. The `uat-runbook-author` subagent was therefore **not**
spawned either: it only runs against an existing skeleton. This is the documented
deferred contract, not a workaround, and it matches the record CAR-003 kept for
the same helper.

**A committed source-derived runbook already exists and is reused instead:**
`specs/car-004-policy-controls-comparators/quickstart.md`. It is the
operator-facing acceptance runbook — numbered commands runnable from the worktree
root, explicit prerequisites, a per-section expected-outcome table traced to
success criteria, and every operator-only section marked as such. It states the
subscription-only authentication path and the no-API-key guarantee up front.

**Plus one addition made in this step.** CAR-004 carries exactly one genuinely
manual task, T062 — the three bounded live smokes, developer-local and never CI —
so a short plain-English operator runbook was written for it at
`docs/ai/specs/.process/CAR-004-live-smoke-runbook.md`.
It is written for someone who did not build the feature: numbered steps with
observable expected results, the supported subscription path (never an API key),
the four bounds each run must stay inside (at most 5 non-reserved objectives, 1
repetition, a 1,000,000 raw-token ceiling, a 30-minute elapsed wall clock), the
observable that proves each control (an inherit resolution for `unpinned`, a
one-rung dispatch-time escalation for `adaptive`, a parallel dispatch with child
aggregation for `orchestration-changing`), the record template the seal step
requires, and how to seal and cross-check the evidence. It supplements
`quickstart.md` §5 rather than replacing it.

No acceptance evidence was fabricated, and T062 remains open and honestly
unticked.

---

## Self-Review

**Date**: 2026-07-28 · **Scope**: the CAR-004 change as a whole (`origin/main...HEAD`,
9 commits, 33 files, ~18k insertions, 0 production LOC). Reporting only; this
section gates nothing.

**Method**: read the diff and the three new library/test surfaces directly;
re-ran `python3 tests/speckit-pro/run-all.py` in this session (**4909/4909** —
L1 1428, L4 3295, L5 186, with the three new files at 518/125/26); executed
`run-control-smoke.py --control adaptive --plan` to exercise the operator path
that exists; scanned every changed file for absolute home-directory paths (none).

### 1. What a reviewer should trust without re-deriving

| Claim | Evidence |
|---|---|
| The surface really is repository-only, 0 production LOC | Every changed path is under `tests/`, `specs/`, `docs/`, plus the regenerated `docs-site/src/content/docs/reference/tests.md`. No plugin source, manifest, payload, or shipped default is touched. |
| The suite is green, not assumed green | Re-run this session: 4909/4909. The three new files are registered in `tests/speckit-pro/suite-manifest.json:122-124`, so they run in CI rather than only by hand. |
| Frozen enums and derivations are read from the frozen bytes, not transcribed | `candidate_code_for()` derives the candidate-plane pairing from the frozen `failure_code` enum and fails closed when the derived code is absent (`claude_policy_controls.py:607-620`); the failure-plane derivation is imported read-only from `claude_score_bundle` (`:42-45`, used at `:688`); `FROZEN_EFFORT_LADDER` is read out of `successor-capability-freeze.schema.json`'s own tuple definition (`:760`); `claude_control_comparison.py:122-130` refuses to import at all if its verdict enum disagrees with the committed schema's `messaging_map` required set. |
| Content-addressing is verified against shipped bytes | `registry_digest`, every `control_digest`, the `topology_digest`, and every CAR-003 binding recompute over the committed instance, and a seeded byte change fails closed — `test-policy-control-contracts.py:2282-2337`. |
| The twin-handoff is derived, not narrated | Categories 1-6 (146 of 167 members) diff to zero in **both** directions against the artifacts, with negative controls for a dropped member, an invented member, and a drifted fact (`test-twin-handoff-completeness.py:56-57, 622-668`). Membership: 156 `mirror_required`, 10 `car_owned`, 1 `sanctioned_divergence`, and the divergence set is test-closed at exactly one (`:739-760`). |
| The raw-token ceiling is machine-checked, not prose | `max_input_tokens + max_cached_input_tokens + max_output_tokens == raw_token_ceiling`, asserted against declared members, with all three cache ceilings barred from the identity — `contracts/policy-control-registry.md` R12, enforced in the validator. |
| An operator cannot be handed a reserved objective | The plan path re-registers the partitions through the frozen consumption path, re-checks each objective individually, then runs the reserved-partition guard last (`run-control-smoke.py:98-138`). Verified live: `--plan` printed only the five `CAR-004-SMOKE-OBJ-*` objectives. |
| The known CI trap was handled | `docs-site/src/content/docs/reference/tests.md` is regenerated in the diff, so `validate-docs` / `reference:check` will not go stale on the new `.py` files. |

### 2. Weakest parts, ranked

**W1 — Seven frozen numbers are judgement calls hardened into a content address, and no live run has ever tested them.**
`tests/speckit-pro/layer6-efficiency/fixtures-controls/policy-control-registry.json:314+`
freezes `max_cache_read_tokens: 1200000`, `ephemeral_5m: 160000`,
`ephemeral_1h: 40000`, `max_cached_input_tokens: 150000`, `max_input_tokens: 800000`,
`max_output_tokens: 50000`, `max_duration_seconds: 1800`. The derivation
(`spec.md:1912-1950`) is "per-attempt allowance from the frozen CAR-003 campaign
budget, carried over five attempts, sit just under twice that, round down". The
*basis* (attempts, not input) is genuinely argued from two repository instances;
the *doubling* is invented. The only test that pins the values
(`test-policy-control-contracts.py:2308`) compares the fixture to
`synthetic_smoke_bounds()`, whose literals are the same numbers (`:339-353`) — a
change detector, which is the right shape for a freeze, but it proves nothing
about whether the numbers are livable. Cost if wrong: `smoke_bounds` is
hash-relevant to the registry, so the first real smoke that trips a diagnostic
ceiling forces a new `registry_digest`, which moves every recorded binding and the
twin-handoff `sha256` entries with it. This is the highest-cost thing here to get
wrong. Related: the per-objective cancellation bound is `1800000` ms, exactly equal
to the whole-run `max_duration_seconds: 1800`, so inside a five-objective smoke the
run-level ceiling always binds first and the cancellation-breach path is
unreachable by the smoke as bounded.

**W2 — T062 has never run, and the operator path is thinner than everything around it.**
Three specific gaps, all in `tests/speckit-pro/layer6-efficiency/run-control-smoke.py`:
(a) the docstring says `--plan` "prints the bounded command set" (`:13`, repeated at
`:159`), but what it prints is identifiers, objectives, bounds, and one prose
demonstration line — no commands; (b) nothing in the repository states *how* to
induce a dispatch-time escalation, an inherit resolution, or a parallel child
dispatch. `quickstart.md:101` says "Execute the printed plan by hand", and `grep -n
induce spec.md` returns only unrelated aggregation prose; (c) `--seal` consumes a
hand-authored JSON record with no template, example, or skeleton emitter — its shape
must be reverse-engineered from `validate_smoke_record` (`claude_policy_controls.py:2083+`)
or from the test's builders. Also asymmetric refusal fidelity: an observed `api_key`
returns normally and keeps a full `bound_reading`, while a bound breach *raises*
(`claude_policy_controls.py:2178`) and is caught at `run-control-smoke.py:250-258`,
leaving `bound_reading` null and `demonstration` uncomputed. Both records are still
written, so FR-030c.3 holds, but a breached record carries strictly less structured
evidence than a refused-auth one.

**W3 — Twin-handoff categories 7 and 8 (21 of 167 entries) are authored, not derived.**
`test-twin-handoff-completeness.py:56-57` splits `DERIVED_CATEGORIES = (1..6)` from
`AUTHORED_CATEGORIES = (7, 8)`, and the authored half is only presence-checked
(`:614-620`). If a decision semantic changes in `claude_policy_controls.py` — the
precedence order, the streak reset, the acceptance-floor precedence — nothing forces
the matching category-7 prose to move. The twin can be handed stale semantics while
the suite stays green.

**W4 — `signal_precedence` is frozen by `const` with only one of its four orderings argued.**
The schema pins the exact array (`policy-control-registry.schema.json`
`$defs/adaptiveControl/properties/signal_precedence`) and the validator independently
enforces set-equality plus `terminal_state` last (`claude_policy_controls.py:657-667`).
Only that last clause has a proof behind it (terminal state is always valued, so
ranking it earlier makes lower sources unreachable). `failure_code` before
`failure_plane` is safe because the two maps are proven consistent (`:684-699`), so
they cannot disagree. `retry_count` before `budget_threshold` is asserted and, as far
as I can find, argued nowhere. Reordering it later changes the adaptive
`control_digest` — cheap to settle now, expensive once CAR-011 binds.

**W5 — The double-breach severity preference is coherent by coincidence, not by invariant.**
Retry breach maps to `failed`/`candidate_failed`, cancellation breach to
`cancelled`/`candidate_cancelled` (fixture `:35-58`). On a double breach,
`evaluate_bounds` prefers the cancellation outcome as "more severe"
(`claude_policy_controls.py:1019-1027`). That agrees with the declared
`terminal_state_severity` array, where `cancelled` outranks `failed` (fixture
`:289-296`) — but that array belongs to the **orchestration** control while the
preference is applied to all three, and nothing enforces agreement between them. A
future control declaring a contradicting severity order would not fail any test.

**W6 — Workflow bookkeeping in this very file is stale.**
Every per-phase Results table above is empty (Specify, Clarify, Plan, Checklist,
Tasks, Analysis, Implementation Progress); the Workflow Overview table carries the
summary instead. The Success Criteria checkboxes (lines 96-102) are all unticked
despite the work being done. `docs/ai/specs/.process/autopilot-state.json` still names
`G56R-003` as its `workflow_file` and was never advanced to CAR-004. Nothing shipped
is affected, but a reader auditing provenance from this file alone gets less than git
history holds. In particular, the Overview's "1 split at medium confidence" clarify
outcome is recorded nowhere here: the *result* landed in `spec.md:1867-1990` (the
serialization decision, with the ceilings explicitly kept at moderate confidence), but
the split itself and the dissenting position are not written down.

### 3. Deliberate omissions

| Omitted | Recorded where | Correctly scoped? |
|---|---|---|
| Concluding dominance (CAR-011 owns it) | `spec.md:1823-1825` | Yes — the whole point of freezing first |
| Any production adaptive-routing or orchestration feature | `spec.md:1826-1828` | Yes |
| Edits to frozen CAR-003 schemas | `spec.md:1829-1830`; enforced by `$ref`-local-only resolution and `{id, digest}` bindings | Yes, and mechanically enforced rather than promised |
| New telemetry fields | `spec.md:1831-1832` | Yes — every adaptive signal binds an existing stable member |
| Unpinned matrix over multiple parent sessions | `spec.md:1833-1834` | Yes — a different parent is a different control version by content address |
| Scored smoke rows / scored mini-campaigns | `spec.md:1835-1839` | Yes, and `scored is not False` is checked by identity (`claude_policy_controls.py:2109`) |
| A fourth (justified-high-effort) control arm | `spec.md` Out of Scope + twin-handoff "Sanctioned platform divergences", test-closed at one entry | Yes — recorded twice, once as prose and once as a tested invariant |
| Layer plan / PR split | "Layer Plan" section above: `skipped`, non-split route | Yes |
| `reviewability-gate` tasks mode | "Reviewability Evidence Chain" above: deferred on the installed runner, fallback chain all-passing | Yes |
| **T062's three live smokes** | `tasks.md:205` (unchecked), `verify-tasks-report.md` (out of assessment scope) | **Recorded, but under-stated.** It is correctly outside an agent's reach. What is not stated plainly anywhere is the consequence: SC-009, SC-026, SC-027, SC-029, SC-030, and SC-031 ship with **no** evidence behind them, automated or manual, and the PR will otherwise read as complete. The PR body should name those six success criteria as unevidenced, not merely note that T062 is a manual step. |

### 4. What the human reviewer should look at personally, in priority order

1. **The seven frozen numbers in `smoke_bounds`** (fixture `:314+`, rationale
   `spec.md:1912-1950`). Cheapest to change today, most expensive after the digest is
   consumed downstream. Ask specifically whether "just under twice the per-attempt
   allowance" is the headroom you want, and whether the 30-minute per-objective
   cancellation bound should be smaller than the 30-minute run ceiling.
2. **T062 — run it, or accept the gap in writing.** Running all three smokes is the
   only thing that converts W1 and W2 from open risk into evidence. If it is not run
   before merge, say in the PR body which six SCs are unevidenced.
3. **`signal_precedence` middle ordering and the double-breach severity preference**
   (`claude_policy_controls.py:657-667` and `:1019-1027` against fixture `:289-296`).
   Both are frozen into content addresses; both are one-line decisions.
4. **Twin-handoff categories 7 and 8** — spot-check a few of the 21 authored entries
   against the validator behavior they describe. No test will catch drift there.
5. **The verdict-to-claim-class messaging map** in `control-comparison.json`. It is
   release-facing wording; totality and single-valuedness are tested
   (`claude_control_comparison.py:324-336`) but the wording itself is a human call.
6. **Bookkeeping** (W6) — the empty Results tables, the unticked Success Criteria
   boxes, and the stale `autopilot-state.json`. Cheap, and it is what the next spec
   inherits.

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
tests/speckit-pro/
├── layer6-efficiency/
│   ├── contracts-claude/          # CAR-003 frozen schemas + new CAR-004 control schemas (additive)
│   ├── contracts-codex-specification/  # twin mirrors (read-only here)
│   ├── fixtures/                  # CAR-003 replay fixtures + role corpus
│   ├── fixtures-controls/         # NEW: control replay fixtures (multi-child aggregation case required)
│   └── lib/                       # claude_*.py validators (new control modules follow this convention)
├── unit/                          # durable-named unit tests incl. the partition guard
└── suite-manifest.json            # test registration
docs/ai/specs/.process/
├── CAR-004-design-concept.md      # grill-me output — source of truth for scoping decisions
└── CAR-004-workflow.md            # this file
specs/car-004-policy-controls-comparators/
└── SPEC-MOC.md                    # navigation marker (contract artifact)
```

---

Populated from the CAR-004 roadmap section and the 2026-07-27 grill-me design
concept during `/speckit-pro:speckit-scaffold-spec`.
