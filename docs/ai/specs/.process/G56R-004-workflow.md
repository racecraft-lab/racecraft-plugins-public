# SpecKit Workflow: G56R-004 — Policy Controls and Adaptive Comparators

**Template Version**: 1.0.0
**Created**: 2026-07-28
**Purpose**: Executable workflow for G56R-004, populated from the technical
roadmap, the CAR-004 twin handoff, the frozen G56R-003/CAR-003 evidence
boundary, and the human-validated Grill Me design concept.

---

## Design Concept

This workflow was enriched from the required Grill Me interview. The complete
Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/G56R-004-design-concept.md
```

The design concept is the source of truth for the scoping decisions captured
during setup. Re-read it before every phase. Once autopilot begins, later
clarifications use `/speckit-clarify` and the consensus protocol; Grill Me is
not part of the autonomous phase loop.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ⏳ Pending | Encode the complete mirror and policy boundary |
| Clarify | `/speckit-clarify` | ⏳ Pending | Resolve exact Codex IDs, route binding, and any concrete mirror mismatch |
| Plan | `/speckit-plan` | ⏳ Pending | Design additive contracts, validators, replay, and smoke proof |
| Checklist | `/speckit-checklist` | ⏳ Pending | Run four enriched requirement-quality domains |
| Tasks | `/speckit-tasks` | ⏳ Pending | One vertical slice, strict RED→GREEN ordering |
| Analyze | `/speckit-analyze` | ⏳ Pending | Check CAR-003/CAR-004 alignment and cross-artifact drift |
| Implement | `/speckit-implement` | ⏳ Pending | TDD implementation; do not run live smokes without operator authorization |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | All user stories clear; no unresolved `[NEEDS CLARIFICATION]` markers |
| G2 | After Clarify | Exact route/ID bindings and every mirror disposition documented |
| G3 | After Plan | Architecture approved; constitution and reviewability gates pass |
| G4 | After Checklist | Every `[Gap]` resolved or explicitly scoped out |
| G5 | After Tasks | Complete FR coverage, dependency order, and TDD pairs verified |
| G6 | After Analyze | No CRITICAL/HIGH consistency or parity findings remain |
| G7 | After each implementation group | Relevant tests pass and evidence is recorded |

---

## Prerequisites

### Worktree and Branch

- Worktree root:
  `/Users/fredrickgabelmann/Documents/Business_Documents/RSE_Documents/Projects/racecraft-plugins-public/.worktrees/g56r-004-policy-controls-adaptive-comparators`
- Branch: `g56r-004-policy-controls-adaptive-comparators`
- Base at scaffold: `origin/main` commit `8b224ce8` (CAR-004 PR #401 merge)
- Remote: `origin`
- Never execute this workflow from `main`, a detached checkout, or a different
  feature worktree.

### Worktree Bootstrap

No scaffold bootstrap command was run. Root `AGENTS.md` states that the
repository test suite needs no bootstrap and runs directly with
`python3 tests/speckit-pro/run-all.py`. The only dependency-bearing surface is
`docs-site/`; if implementation changes a tracked `.md`, `.py`, or `.sh` under
`tests/speckit-pro/` and therefore needs a docs reference command, first obtain
operator approval and run the documented
`pnpm --dir docs-site install --frozen-lockfile` once in this worktree.

### Grounded Source Truth

Treat these sources in this order for G56R-004:

1. `docs/ai/specs/.process/G56R-004-design-concept.md` — human-validated scope
   and decisions for this spec.
2. `docs/ai/specs/.process/CAR-004-twin-handoff.md` — complete mirror contract,
   including categories 7 and 8 and the one sanctioned platform divergence.
3. `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md` — spec goal,
   budget, dependency, and non-goal boundary.
4. `docs/prd-codex-gpt-5-6-agent-routing.md` — product acceptance criteria,
   interpreted through the roadmap's more specific three-control decision.
5. Current frozen G56R-003/CAR-003 contracts, content addresses, successor
   capability evidence, partition machinery, traces, and score-bundle logic.
6. `.specify/memory/constitution.md` and root `AGENTS.md` — repository runtime,
   testing, simplicity, naming, and generated-artifact rules.

Existing CAR-003/G56R-003 reconciliation remains in CAR-012/G56R-012. Do not
silently absorb it into this spec. If a new CAR-004 member is genuinely
unmirrorable, name it and raise the paired reconciliation disposition selected
in Design Concept Q13.

### Constitution Validation

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| I. Plugin Structure Compliance | Keep repository-only tests under `tests/speckit-pro/`; do not add install-facing plugin files | Changed-path review and Layer 1 |
| II. Cross-Platform Runtime & Script Safety | Python 3.11+ standard library; structured JSON; no active Bash or `jq` | Import/path review and Layer 4 |
| IV. Test Coverage Before Merge | Register every new unit path through `tests/speckit-pro/suite-manifest.json` and pass the Python-authoritative suite | Relevant unit files, then `python3 tests/speckit-pro/run-all.py` |
| VI. KISS, Simplicity & YAGNI | Add only the two contracts and minimum validation/replay/smoke machinery needed for the closed three-control surface | Plan review against Design Concept Non-goals |

**Constitution Check:** pending phase execution; no scaffold conflict found.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | G56R-004 |
| **Name** | Policy Controls and Adaptive Comparators |
| **Branch** | `g56r-004-policy-controls-adaptive-comparators` |
| **Dependencies** | G56R-003 complete/archived via PR #386; CAR-004 merged via PR #401; frozen CAR-003/G56R-003 bindings |
| **Enables** | G56R-005 directly; G56R-011 later consumes the comparison contract |
| **Priority** | P1 |

### Reviewability Budget and Split Decision

The setup `reviewability-gate` run against the series-wide technical roadmap
returned non-blocking `warn`: 395 estimated reviewable LOC, 2 production files,
15 total files, and 3 primary surfaces. Its only warning was the roadmap's
series-wide multi-surface aggregation.

The G56R-004 entry itself declares approximately 235 reviewable LOC, 3
production files, approximately 10 total files, one harness/adapter surface,
and one suggested slice. The Grill Me `estimate-spec-size` run used one user
story, three primary files/surfaces, and six requirement groups and returned:

```json
{"estimated_loc":235,"suggested_slices":1,"status":"ok"}
```

**Split decision:** keep one thin vertical slice. No O5 topology or split
exception is warranted. The plan-phase authoritative reviewable-LOC check may
still require re-slicing if the concrete file plan expands.

### Success Criteria Summary

- [ ] Exactly three Codex controls — `unpinned`, `adaptive`, and
  `justified_high_effort` — are defined, exact-treatment validated,
  content-addressed, and frozen; automatically spawned child work is accounted
  as a modifier, not a fourth control.
- [ ] New Codex-local contracts mirror every CAR-004 `mirror_required` record
  shape, required member, enum, numeric, decision semantic, and enforcement
  guard while using Codex-owned identifiers.
- [ ] Frozen G56R-003/CAR-003 bindings resolve by stable ID and committed-bytes
  digest, and zero frozen contract members are edited.
- [ ] Bidirectional completeness rejects missing, invented, drifted, or
  digest-mismatched members; the only platform divergence is the published
  third-control value.
- [ ] Adaptive signals and route order derive from frozen G56R-003 evidence;
  every signal resolves exactly once and no control selects an unqualified
  route.
- [ ] Dominance uses the mirrored gate-first Pareto rule, eight direction-aware
  dimensions, confidence method, 10% relative margins, and exact no-verdict
  behavior.
- [ ] The G56R-011 integrated-confirmation partition is content-addressed and
  mechanically protected from replay and smoke consumption.
- [ ] Deterministic replay covers all three controls, and one bounded non-scored
  ChatGPT-sign-in smoke per control can demonstrate exact treatment without
  committing raw captures or consuming qualification evidence.
- [ ] The verdict-to-claim-class mapping is total and machine-readable, while
  G56R-004 reaches no final static-core dominance verdict.

---

## Phase 1: Specify

**When to run:** Start of the feature. Define WHAT and WHY; do not prematurely
freeze implementation details that Plan must derive from current evidence.
Output: `specs/g56r-004-policy-controls-adaptive-comparators/spec.md`.

### Specify Prompt

```text
/speckit-specify

## Feature: G56R-004 Policy Controls and Adaptive Comparators

### Problem Statement

G56R-011 will eventually compare the final static Codex routing core against
policy-level alternatives. Those controls, their exact-treatment requirements,
their resource/quality floors, their statistical decision rule, and the release
messaging consequence must be frozen before outcome-bearing comparison begins.
G56R-004 creates that predeclared contract. It mirrors CAR-004's complete
cross-platform semantics against the frozen G56R-003/CAR-003 evaluation surface
without reopening those contracts and without deciding which policy wins.

### Users and Consumers

- G56R-011: applies the frozen comparison rule to the final assembled core.
- G56R-005 and G56R-006: inherit bounded control and route-eligibility semantics.
- Evaluation maintainers: replay and smoke the controls with exact treatment.
- Release reviewers: consume the machine-readable verdict-to-claim-class map.
- Cross-platform maintainers: verify the CAR-004/G56R-004 mirror and its one
  sanctioned platform-value divergence.

### User Story

As the Codex routing evaluation program, freeze three exact-treatment policy
controls and one adaptive comparison contract before final routing outcomes
exist, so later dominance and release-language decisions are predeclared,
reproducible, content-addressed, and aligned with CAR-003/CAR-004.

### Required Design Decisions

1. Alignment authority: CAR-004 twin handoff first, applied against current
   frozen G56R-003/CAR-003 bindings. Existing CAR-012/G56R-012 reconciliation is
   explicitly out of scope.
2. Closed control set: unpinned, adaptive, justified-high-effort. The sole
   sanctioned platform divergence is the third enum value; every record shape,
   member, numeric, semantic, and guard remains mirror-identical.
3. Contract form: new additive Codex-local schemas with Codex IDs. Bind frozen
   evaluation artifacts by stable ID and digest; edit none of them.
4. Completeness: derive and compare the mirror surface in both directions;
   missing, extra, drifted, or digest-mismatched members fail closed.
5. Adaptive behavior: route ladder derives from ordered admitted G56R-003
   tuples. Signals are the frozen terminal state, failure plane/code, retry, and
   budget fields. Preserve CAR-004's totality, precedence, consistency, streak,
   no-wrap, and non-scorable reroute semantics.
6. Unpinned identity: bind the frozen parent model, effort, client, and
   environment. A different parent context is a different content-addressed
   control version.
7. Justified-high-effort: bind one already-qualified high-effort route plus an
   explicit eligibility predicate and rationale. Include all spawned child work
   in the governed aggregate.
8. Dominance: mirror the gate-first order, eight dimensions, directions,
   confidence method, 10% relative margins, multiplicity position, zero-
   denominator behavior, and no-verdict outcomes exactly.
9. Partition: reserve G56R-011 integrated confirmation as a content-addressed
   registry entry; any replay or smoke row consuming a reserved objective fails.
10. Validation: deterministic replay plus one bounded, non-scored smoke per
    control on ChatGPT sign-in; raw captures remain off-repo. Bounds mirror
    CAR-004: <=5 non-reserved objectives, 1 repetition, 1,000,000 raw tokens,
    30 minutes, and the handoff's component/cache ceilings.
11. Messaging: machine-readable total verdict-to-claim-class mapping. A
    materially dominated static policy may still ship for declared operational
    simplicity but loses efficient, optimal, and best-measured claims.
12. Reconciliation: never weaken an unmirrorable member. Name it and raise a
    paired roadmap reconciliation entry.

### Constraints

- Python 3.11+ standard library only; no active Bash, jq, or package runtime.
- Repository-only evaluation surface; no plugin payload, installer, manifest,
  production scheduler, or shipped-default change.
- Durable filenames; no new script or test filename coupled to G56R-004.
- No new telemetry fields. Preserve null versus zero and every frozen unit.
- No outcome-bearing control campaigns and no final dominance conclusion.
- Live smoke execution requires explicit operator authorization and cannot run
  in default CI.

### Out of Scope

- Frozen G56R-003/CAR-003 edits or existing G56R-012 reconciliation work.
- A fourth control or a full topology-changing Codex control arm.
- Dynamic discovery of unqualified routes.
- Production adaptive routing, fallback resolution, installer behavior, or
  final release integration.
- API-key-required smoke paths, committed raw model/prompt captures, or scored
  mini-campaigns.

### Source References

- docs/ai/specs/.process/G56R-004-design-concept.md
- docs/ai/specs/.process/CAR-004-twin-handoff.md
- docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md
- docs/prd-codex-gpt-5-6-agent-routing.md
- current G56R-003/CAR-003 frozen contracts and evidence
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | |
| User Stories | |
| Acceptance Criteria | |

### Files Generated

- [ ] `specs/g56r-004-policy-controls-adaptive-comparators/spec.md`

### Required Traceability Markers

| Marker | Purpose |
|--------|---------|
| `[US1]` | The single end-to-end policy-control capability |
| `[FR-xxx]` | Contract, behavior, evidence, and failure requirements |
| `[NEEDS CLARIFICATION]` | Only unresolved items that Clarify must answer |
| `[Gap]` | Missing requirement coverage discovered later |

---

## Phase 2: Clarify

**When to run:** After Specify. Use a maximum of five targeted questions per
session. Resolve concrete ambiguity; do not reopen decisions already accepted
in the design concept.

### Clarify Prompts

#### Session 1: Codex identifiers and high-effort route binding

```text
/speckit-clarify Focus on the exact Codex-owned identifiers and frozen route
bindings. Select one already-qualified high-effort tuple from current G56R-003
successor-capability evidence; record its stable ID, digest, eligibility
predicate, and rationale. Verify the adaptive ladder contains only ordered,
admitted tuples and specify the failure when no eligible tuple exists. Do not
copy Claude route literals or discover a route after the control is frozen.
```

#### Session 2: Twin completeness and reconciliation boundary

```text
/speckit-clarify Focus on CAR-004 twin-handoff completeness. Enumerate how
categories 1-6 are derived from Codex artifacts in both directions; bind each
category-7 decision semantic and category-8 guard to executable Codex behavior;
prove the third control value is the only sanctioned divergence; and identify
any concrete mirror-required member that needs the Q13 reconciliation path.
Keep pre-existing CAR-003/G56R-003 issues in G56R-012.
```

#### Session 3: Smoke execution and evidence disposition

```text
/speckit-clarify Focus on the three local non-scored smokes: the observable
that proves unpinned inheritance, adaptive dispatch-time escalation, and
justified-high-effort eligibility/child aggregation; exact ChatGPT-sign-in
preconditions; component and cache ceilings from the handoff; refusal records;
off-repo raw-capture retention; and how the PR reports success criteria when an
operator does not authorize or complete a smoke.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | IDs and route binding | | |
| 2 | Twin completeness | | |
| 3 | Smoke evidence | | |

---

## Phase 3: Plan

**When to run:** After G2. Output the implementation blueprint under
`specs/g56r-004-policy-controls-adaptive-comparators/`.

### Plan Prompt

```text
/speckit-plan

## Tech Stack and Existing Surfaces

- Python 3.11+ standard library only.
- JSON Schema conventions matching
  tests/speckit-pro/layer6-efficiency/contracts-codex-specification/.
- Frozen G56R-003 logic and evidence under
  tests/speckit-pro/layer6-efficiency/ and docs/ai/research/.
- CAR-004 mirror input at docs/ai/specs/.process/CAR-004-twin-handoff.md.
- Repository suite ownership from tests/speckit-pro/suite-manifest.json.

## Required Architecture

1. Add standalone Codex policy-control-registry and control-comparison schemas
   under contracts-codex-specification/ using Codex $ids. Preserve the complete
   CAR-004 shape and semantics except the published control-kind enum value.
2. Add deterministic Codex control fixtures under a distinct durable directory
   such as fixtures-codex-controls/. Keep raw live results git-ignored.
3. Add the smallest Codex-local validator/comparison modules needed, following
   existing `lib/codex_*.py` patterns. Reuse only genuinely platform-neutral
   helpers; never import Claude identifiers as Codex authority and do not create
   speculative shared abstractions.
4. Bind frozen G56R-003/CAR-003 artifacts by stable ID and committed-bytes
   digest. Zero modifications are permitted under the frozen contract set.
5. Implement bidirectional twin completeness. Categories 1-6 are derived, not
   narrated. Categories 7-8 need executable checks tying each authored semantic
   and guard to behavior so the handoff cannot go stale silently.
6. Preserve exact adaptive semantics: total response maps, precedence,
   plane/code and terminal/code consistency, ordered no-wrap route sequence,
   three-clean-pass de-escalation, bound scope/breach results, platform-reroute
   non-scorability, and parent-plus-children aggregation.
7. Preserve exact comparison semantics: eligibility floors before verdict,
   eight direction-aware dimensions, 10% relative margin map, confidence and
   multiplicity contract, zero-denominator result, total verdict-to-claim-class
   mapping, and no weights.
8. Register G56R-011's reserved integrated-confirmation partition through the
   frozen partition machinery and add one entry-point guard rejecting any
   replay or smoke consumption.
9. Add a local smoke planner/sealer only if needed for the three selected
   observables. It must enforce ChatGPT sign-in, all handoff bounds, non-scored
   labeling, reserved-partition exclusion, governed evidence output, and
   off-repo raw retention. Live execution remains operator-only.

## Reviewability and File Plan

- Begin from the one-slice, 235-LOC roadmap budget.
- Declare every new/modified production and test path before implementation.
- Run the plan-phase reviewable-LOC estimator. If concrete reviewable LOC grows
  beyond one reviewable slice, re-slice vertically by capability rather than
  hiding growth in fixtures or generated artifacts.
- Keep script and test filenames durable and behavior-named, never G56R-004-
  named.

## Design Authority

Quote the selected answers from
docs/ai/specs/.process/G56R-004-design-concept.md for any architecture choice.
If spec.md or this plan conflicts with the design concept, surface the conflict
instead of silently preferring a downstream artifact.
```

### Required Plan Artifacts

| Artifact | Status | Purpose |
|----------|--------|---------|
| `plan.md` | ⏳ | Architecture, file plan, reviewability evidence |
| `research.md` | ⏳ | Route-binding and reuse decisions |
| `data-model.md` | ⏳ | Registry, control, comparison, partition, and smoke evidence entities |
| `contracts/` | ⏳ | Human-readable contract/API notes where useful |
| `quickstart.md` | ⏳ | Deterministic replay and operator smoke runbook |

---

## Phase 4: Domain Checklists

**When to run:** After Plan. These check requirement quality, not
implementation correctness. Run sequentially and remediate every `[Gap]` before
G4.

### 1. Data Integrity

```text
/speckit-checklist data-integrity

Focus on G56R-004 requirements:
- Every hash-relevant member and preimage rule is complete and unambiguous.
- Frozen G56R-003/CAR-003 ID/digest bindings fail on changed bytes.
- Twin categories 1-6 compare in both directions; missing and invented members
  both fail.
- The sole sanctioned divergence is closed to the control-kind enum value.
- Pay special attention to: no requirement permits editing a frozen contract to
  restore agreement.
```

### 2. Error Handling

```text
/speckit-checklist error-handling

Focus on G56R-004 requirements:
- Every adaptive signal resolves once under the frozen precedence order.
- Route ceilings/floors do not wrap; retry, cancellation, and bound breaches
  have exact terminal state and failure code outcomes.
- Platform reroutes remain non-scorable and never consume escalation allowance.
- Missing routes, unknown enum members, digest drift, and reserved-objective
  consumption all fail closed.
- Pay special attention to: the interaction of non-scorable rows with clean-pass
  streak accounting.
```

### 3. LLM Integration

```text
/speckit-checklist llm-integration

Focus on G56R-004 requirements:
- Exact treatment for unpinned inheritance, adaptive dispatch-time escalation,
  and the qualified high-effort route is observable in produced evidence.
- Automatically spawned child work is included in tokens, duration, retries,
  compaction, acceptance, and terminal-state aggregation.
- ChatGPT sign-in is the supported smoke path; no API key is required or
  silently substituted.
- Raw model/prompt captures remain off-repository and non-scored smoke evidence
  cannot support qualification claims.
- Pay special attention to: evidence must be read back from execution, never
  inferred from the dispatch request.
```

### 4. Performance

```text
/speckit-checklist performance

Focus on G56R-004 requirements:
- All mirrored smoke ceilings declare units, scope, and breach disposition.
- The 1,000,000 raw-token identity and input/cached/output components are
  arithmetically consistent.
- Cache read/write quantities use their distinct ceilings and unobserved values
  are not coerced to zero.
- The 30-minute limit is elapsed wall clock over the parent-plus-children unit,
  while child dispatches do not consume extra objective attempts.
- Pay special attention to: pairwise cache isolation across all three controls.
```

### Checklist Results

| Checklist | Items | Gaps | Resolution |
|-----------|-------|------|------------|
| data-integrity | | | |
| error-handling | | | |
| llm-integration | | | |
| performance | | | |
| **Total** | | | |

---

## Phase 5: Tasks

**When to run:** After all checklist gaps are resolved. Output:
`specs/g56r-004-policy-controls-adaptive-comparators/tasks.md`.

### Tasks Prompt

```text
/speckit-tasks

Generate one dependency-ordered vertical slice with strict TDD pairs. Every
task must reference spec.md, plan.md, and
docs/ai/specs/.process/G56R-004-design-concept.md.

## Required Task Order

1. Baseline and contract freeze
   - Record green relevant suite baselines before edits.
   - RED tests for additive schemas, Codex IDs, frozen bindings, closed control
     set, and the sole sanctioned divergence.
   - GREEN policy-control-registry and comparison contracts.
2. Policy behavior and replay
   - RED/GREEN unpinned parent-context identity.
   - RED/GREEN adaptive total maps, precedence, route order, clean-pass streak,
     bounds, reroute disposition, and no-unqualified-route rule.
   - RED/GREEN justified-high-effort eligibility and child-work aggregation.
3. Comparison, partition, and parity
   - RED/GREEN eligibility floors, direction-aware material dominance,
     confidence/margins, and total claim mapping.
   - RED/GREEN reserved G56R-011 partition registration and non-consumption.
   - RED/GREEN bidirectional twin completeness, including executable category
     7/8 checks and negative controls for missing, extra, drifted, and second-
     divergence cases.
4. Integration and operator evidence
   - Deterministic replay coverage for all three controls.
   - Smoke plan/seal validation and a plain-language runbook, without executing
     live work unless the operator explicitly authorizes it.
   - Final relevant layers, full suite, docs reference regeneration when
     required, diff review, and success-criteria evidence table.

## Constraints

- Keep one vertical slice unless the plan-phase authoritative estimate proves it
  cannot remain reviewable.
- Do not create a task that edits frozen G56R-003/CAR-003 contracts.
- Do not create a task for existing G56R-012 reconciliation debt.
- Do not generate outcome-bearing scored evidence or a final dominance verdict.
- Mark live smoke execution as operator-only and keep affected success criteria
  honestly open when it is not run.
- Use durable filenames and register new tests through suite-manifest.json.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | |
| RED→GREEN pairs | |
| Parallel-safe tasks | |
| User stories covered | |

---

## Atomicity Route

After G5, run the read-only classifier and record its exact result here:

```text
runner helper atomicity-route specs/g56r-004-policy-controls-adaptive-comparators
```

| Field | Value |
|-------|-------|
| Route | |
| Releasable | |
| Signals | |
| Warnings | |

Do not infer the route from the scaffold's one-slice estimate; the classifier
uses the concrete tasks and plan.

---

## Phase 6: Analyze

**When to run:** Always after Tasks and before implementation.

### Analyze Prompt

```text
/speckit-analyze

Perform a cross-artifact consistency analysis across spec.md, plan.md,
tasks.md, and docs/ai/specs/.process/G56R-004-design-concept.md.

Focus on:
1. Alignment authority: CAR-004 twin handoff plus frozen G56R-003/CAR-003
   bindings; no existing G56R-012 debt pulled into scope.
2. Control set: exactly unpinned, adaptive, justified-high-effort; child work
   is a modifier; no fourth arm.
3. Mirror completeness: shapes, required sets, enums, numerics, categories 7/8,
   and guards are covered; the one sanctioned divergence is explicit.
4. Statistical consistency: gate-first order, directions, 10% margins,
   confidence/multiplicity, zero denominator, and no-verdict behavior agree in
   every artifact.
5. Evidence boundary: replay plus bounded non-scored smokes, ChatGPT sign-in,
   off-repo raw captures, reserved partition untouched, and no final verdict.
6. Constitution and file paths: Python stdlib, durable names, suite ownership,
   generated docs accounted for, no frozen-contract edits.
7. Task coverage: every FR and success criterion has an ordered task and proof;
   operator-only smokes are not falsely marked automated.

Treat drift from the Design Concept Goals, Non-goals, or selected answers as a
blocking issue unless a dated, human-approved revision records the change.
```

### Analyze Results

| ID | Severity | Finding | Resolution |
|----|----------|---------|------------|
| | | | |

**G6 requirement:** zero CRITICAL/HIGH findings.

---

## Phase 7: Implement

**When to run:** After G6 passes.

### Implement Prompt

```text
/speckit-implement

## TDD Cycle

For every behavior task:
1. RED — write the smallest failing test or negative-control fixture.
2. GREEN — implement the minimum behavior that satisfies the frozen contract.
3. REFACTOR — simplify without changing content addresses or evidence meaning.
4. VERIFY — run the narrow test, then the declared broader gate.

## Pre-Implementation Setup

1. Verify branch `g56r-004-policy-controls-adaptive-comparators` and a clean
   worktree.
2. Read docs/ai/specs/.process/G56R-004-design-concept.md and the CAR-004 twin
   handoff before starting the first task.
3. Run `python3 tests/speckit-pro/run-all.py --layer 1` and
   `python3 tests/speckit-pro/run-all.py --layer 4` as the documented direct
   repository baseline; stop on unexplained red state.
4. If a docs reference command becomes required, obtain operator approval and
   run `pnpm --dir docs-site install --frozen-lockfile` once first.

## Implementation Rules

- Use existing G56R-003/CAR-003 artifacts read-only. A diff under the frozen
  contract set is a scope violation, not a convenient compatibility fix.
- Derive closed enums and bindings from committed authority wherever the
  handoff says derived; do not maintain parallel literals that can drift.
- Preserve structured JSON, deterministic UTF-8 serialization, explicit
  return-code handling, and platform-safe paths.
- Read treatment observables back from produced execution evidence. Dispatch
  configuration alone is not proof.
- Live smokes are local, non-scored, operator-authorized work. Do not send
  repository context off-box without explicit approval and do not fabricate
  evidence when a smoke is skipped.
- Consult the design Q&A for the reason behind every boundary, especially the
  third-control divergence, fail-closed parity, and G56R-012 exclusion.

## Verification

- Smallest affected unit file while iterating.
- Layer 1 and Layer 4 after contract/runner/test registration changes.
- Full `python3 tests/speckit-pro/run-all.py` before PR.
- Docs reference generation/checking required by root AGENTS.md for tracked
  test-tree `.md`, `.py`, or `.sh` changes.
- Final `git diff --check`, changed-file review, and zero unexpected files.
```

### Implementation Progress

| Group | Tasks | Completed | Evidence |
|-------|-------|-----------|----------|
| Contract freeze | | | |
| Policy behavior and replay | | | |
| Comparison, partition, parity | | | |
| Integration and operator evidence | | | |

---

## Post-Implementation Checklist

- [ ] All tasks complete or operator-only gaps explicitly identified
- [ ] Full repository suite passes with exact counts recorded
- [ ] New tests are declared in `tests/speckit-pro/suite-manifest.json`
- [ ] Required docs reference generation/check passes
- [ ] Zero frozen G56R-003/CAR-003 contract modifications
- [ ] CAR-004 twin completeness passes in both directions
- [ ] Exactly one sanctioned platform divergence remains
- [ ] Reserved G56R-011 partition is mechanically untouched
- [ ] No raw live model/prompt captures committed
- [ ] Unrun live smokes and affected success criteria are named honestly
- [ ] PR title passes the live release-readiness gate format
- [ ] PR created, reviewed, and merged through normal branch protection

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
tests/speckit-pro/
├── layer6-efficiency/
│   ├── contracts-codex-specification/  # frozen G56R-003 + additive G56R-004 schemas
│   ├── fixtures-codex/                 # existing G56R fixtures, read-only unless planned
│   ├── fixtures-codex-controls/        # proposed deterministic control fixtures
│   ├── lib/                            # existing codex_*.py helpers + minimal control modules
│   └── results-codex/                  # git-ignored per-run results
├── unit/                               # durable-named contract/behavior/parity tests
└── suite-manifest.json                 # authoritative test ownership
docs/ai/specs/.process/
├── CAR-004-twin-handoff.md             # complete cross-platform input
├── G56R-004-design-concept.md          # human-validated scoping authority
└── G56R-004-workflow.md                # this execution guide
specs/g56r-004-policy-controls-adaptive-comparators/
├── SPEC-MOC.md                         # navigation/version marker
├── spec.md
├── plan.md
├── tasks.md
└── .process/                           # later UAT/process exhaust
```

---

Populated from the shared SpecKit workflow template, G56R-004 roadmap entry,
CAR-004 twin handoff, frozen G56R-003/CAR-003 evidence boundary, constitution,
and the 2026-07-28 Grill Me interview.
