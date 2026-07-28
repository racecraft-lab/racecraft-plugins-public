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

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | | `true`, or `false` for a destructive-migration or concurrency-sensitive change (a passing CI run does not prove such a change is safe to release). |
| **Signals** | | The decisive detector findings behind the route and releasability reading (may be empty when the classifier abstains). |
| **Warnings** | | Any release-safety warning attached to the change (empty when there is no releasability risk). |

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
