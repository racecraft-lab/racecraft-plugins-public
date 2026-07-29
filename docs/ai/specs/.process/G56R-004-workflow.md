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
| Specify | `/speckit-specify` | ✅ Complete | 1 P1 story, 42 FRs, 18 scenarios, 19 success criteria; G1 passed with 0 markers |
| Clarify | `/speckit-clarify` | ✅ Complete | Three sessions; 14 questions; G2 passed with 0 markers; smoke consensus accepted with cache/auth precision |
| Plan | `/speckit-plan` | ✅ Complete | Seven artifacts; 12 declared implementation paths; estimator passed; G3 passed |
| Checklist | `/speckit-checklist` | ✅ Complete | 121 items; 13 gaps remediated to zero; G4 passed |
| Tasks | `/speckit-tasks` | ✅ Complete | 38 tasks; 15 RED→GREEN pairs; full 42-FR/19-SC coverage; G5 passed |
| Analyze | `/speckit-analyze` | ✅ Complete | One MEDIUM and one implementation-discovered HIGH dependency finding remediated; final findings zero; G6 passed |
| Confidence Gate | G6.5 | ✅ Complete | Advisory gate passed: composite 0.98 ≥ threshold 0.90; proceed |
| Implement | `/speckit-implement` | 🔄 In Progress | TDD implementation; do not run live smokes without operator authorization |
| Post | Post-Implementation | 🔄 In Progress | Verification and code review complete; reviewability, PR, remediation, and retrospective remain |

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
| G6.5 | Before Implement | Latest confidence emit evaluated in advisory mode at threshold 0.90 |
| G7 | After each implementation group | Relevant tests pass and evidence is recorded |

---

## Prerequisites

### Worktree and Branch

- Worktree root: the current checkout returned by
  `git rev-parse --show-toplevel`; it MUST be the registered worktree for the
  branch below and contain this workflow file.
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

### Archive Sweep

- Status: eligible prior candidate found; no mutation performed.
- Current target excluded:
  `specs/g56r-004-policy-controls-adaptive-comparators`.
- Prior candidate: `specs/car-004-policy-controls-comparators`; live PR #401
  is merged at `8b224ce8`, and archival is already isolated in open PR #402.
- Cleanup mode: report-only. This feature worktree is not an integration
  branch, no `--apply-cleanup` authorization was supplied, and
  `safeToApplyCleanup=false`.
- Execution path: archive extension command contract with Codex-native
  worktree binding.

### Runtime and Capability Context

- Installed runner: Python 3.11 direct module invocation; prerequisite helper
  returned `all_pass=true`.
- Branch authority: `git branch --show-current` returned
  `g56r-004-policy-controls-adaptive-comparators`. The read-only prerequisite
  helper returned an empty branch field for this linked worktree, so Git is
  the recorded branch authority.
- Confidence gate mode: `advisory`.
- Settings: `consensus-mode=moderate`, `gate-failure=stop`,
  `auto-commit=per-phase`.
- Installed Codex agents: dry-run comparison returned `mutation_status=no_op`
  for all ten required agent files using the `gpt-5.5` templates.
- Preset: `speckit-pro-reviewability` v1.0.0. It requires an explicit
  reviewability budget, declared file operations, PR review packet evidence,
  dependency-ordered tasks, and TDD-first test tasks.
- Project commands: root `AGENTS.md` overrides generic stack detection with
  Layer 1 (`python3 tests/speckit-pro/run-all.py --layer 1`), Layer 4
  (`python3 tests/speckit-pro/run-all.py --layer 4`), and full-suite
  (`python3 tests/speckit-pro/run-all.py`) verification.
- Capability path: repository/spec context uses local file and Git evidence;
  live PR provenance uses GitHub CLI. Confidence is high because both are
  direct sources. No external library documentation is required by this spec.

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
| I. Plugin Structure Compliance | Keep repository-only tests under `tests/speckit-pro/`; do not add install-facing plugin files | ✅ Layer 1 baseline `1428/1428` |
| II. Cross-Platform Runtime & Script Safety | Python 3.11+ standard library; structured JSON; no active Bash or `jq` | ✅ Layer 4 baseline `3334/3334` |
| III. Semantic Versioning | Do not edit plugin versions for repository-only evaluation work | ✅ No manifest/version path in scope |
| IV. Test Coverage Before Merge | Register every new unit path through `tests/speckit-pro/suite-manifest.json` and pass the Python-authoritative suite | ✅ Baseline recorded; full suite required after implementation |
| V. Conventional Commits | Use repository-valid scoped commits and PR title | ✅ Per-phase commit policy recorded |
| VI. KISS, Simplicity & YAGNI | Add only the two contracts and minimum validation/replay/smoke machinery needed for the closed three-control surface | ✅ Design Concept non-goals bound; re-check in Plan and Implement |

**Constitution Check:** ✅ Verified for Phase 0. The initial Layer 4 attempt
exposed one scaffold-local privacy leak: this workflow committed an absolute
home path. Replacing it with a portable Git worktree identity restored the
focused privacy scan (`10/10`) and Layer 4 (`3334/3334`) without changing
feature scope.

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
| Functional Requirements | 42 |
| User Stories | 1 |
| Acceptance Criteria | 18 scenarios |
| Success Criteria | 19 |
| G1 | Passed — `spec.md` exists with 0 clarification markers |

### Files Generated

- [x] `specs/g56r-004-policy-controls-adaptive-comparators/spec.md`

Phase 1 deliberately leaves three evidence questions to the required Clarify
sessions without inserting vague markers: the exact Codex-owned IDs and
qualified high-effort route, any concrete unrepresentable CAR-004 member, and
the operator-authorized live-smoke disposition.

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
| 1 | IDs and route binding | 4 | Fixed the five Codex-owned IDs and schema namespace; bound the qualified `g56r-003-route-phase-executor` `gpt-5.5`/`xhigh` tuple to its successor-freeze and route digests; made adaptive ladder membership/order hash-relevant and fail-closed; prohibited fallback, discovery, or comparative claims for an ineligible high-effort control. Consensus skipped because the executor reported zero unresolved items. |
| 2 | Twin completeness | 5 | Categories 1–6 are derived from Codex artifacts and diffed bidirectionally; all 19 category-7 semantics and both category-8 guards require executable checks; the only divergence is `justified_high_effort` replacing `orchestration_changing`; zero concrete reconciliation candidates were identified, with Q13 retained as the fail-closed path. |
| 3 | Smoke evidence | 5 | Fixed the three produced-evidence observables; required the Codex-owned observed ChatGPT subscription auth value with retained refusal records; preserved all mirrored component/cache/time/attempt ceilings over the parent-plus-children unit; kept raw captures off-repository; and required the PR to report unauthorized, refused, or incomplete live smokes honestly rather than claim success. Consensus accepted all four routed security/evidence answers, clarifying that missing cache quantities are `unobserved` while missing/shared isolation roots invalidate the smoke. |

**G2 Result:** ✅ Passed. The authoritative gate reported
`0 [NEEDS CLARIFICATION] markers`; the all-marker check also reported zero
clarifications, gaps, and severity findings.

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
| `plan.md` | ✅ | Architecture, file plan, reviewability evidence |
| `research.md` | ✅ | Route-binding and reuse decisions |
| `data-model.md` | ✅ | Registry, control, comparison, partition, and smoke evidence entities |
| `contracts/` | ✅ | Human-readable contract/API notes |
| `quickstart.md` | ✅ | Deterministic replay and operator smoke runbook |

### Plan Results

- G3: ✅ `plan.md exists with 0 unresolved markers`.
- Constitution: PASS before and after design; no complexity exception.
- Reviewability: estimator `status=pass`, `projected=0`, 9 new paths, 3
  modified paths, 12 total entries. It counts repository-only test-tree files
  outside its production-LOC total; the logical implementation remains three
  focused Python helpers in one vertical slice.
- File-plan correction: the existing three Layer 4 owners are already present
  in `suite-manifest.json`, so no manifest edit is planned.
- Consensus: skipped because the Plan executor reported zero unresolved items.

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
| data-integrity | 31 | 0 | Complete; zero gaps, consensus skipped |
| error-handling | 35 | 3 → 0 | Complete; clarified unknown values, floor reset/no-step, and budget-trigger vs breach semantics; consensus skipped |
| llm-integration | 27 | 4 → 0 | Complete; clarified dispatch read-back, all-control child aggregation, raw-output storage, and non-qualification smoke evidence; consensus skipped |
| performance | 28 | 6 → 0 | Complete; clarified breach disposition, raw-token arithmetic, cache ownership, elapsed wall clock, attempt accounting, and all three isolation pairs; consensus skipped |
| **Total** | 121 | 13 → 0 | G4 passed with zero `[Gap]` markers |

**G4 Result:** ✅ Passed. All four checklist domains completed sequentially,
all 13 discovered requirement gaps were remediated, and the authoritative
marker check reported zero remaining gaps.

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
| Total Tasks | 38 |
| RED→GREEN pairs | 15 |
| Parallel-safe tasks | 3 |
| User stories covered | 1 of 1 |
| FR coverage | 42 of 42 |
| Success-criteria coverage | 19 of 19 |

**G5 Result:** ✅ Passed. The authoritative gate found 38 tasks and zero
markers. All tasks cite `spec.md`, `plan.md`, and the selected decisions in
`docs/ai/specs/.process/G56R-004-design-concept.md`.

**Task-mode reviewability:** deferred. The installed `reviewability-gate`
runner helper supports setup mode only, so no unsupported tasks-mode invocation
was made. The concrete plan estimator remains `pass`, and the atomicity router
below independently confirms a releasable single-PR route.

---

## Atomicity Route

After G5, run the read-only classifier and record its exact result here:

```text
runner helper atomicity-route specs/g56r-004-policy-controls-adaptive-comparators
```

| Field | Value |
|-------|-------|
| Route | `one-navigable-PR` |
| Releasable | `true` |
| Signals | `change-shape:modify-heavy` |
| Warnings | none |

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
| A-001 | MEDIUM | `quickstart.md` named docs reference generation but omitted the required reference check command. | Added `pnpm --dir docs-site reference:check`; final semantic and marker findings are zero. |
| A-002 | HIGH | Implementation exposed that T006 required comparison-owned null evidence before the T021 comparison fixture and partition-owned evidence before T025. | Dependency-ordered mirror proof by artifact availability: registry T006-T007, comparison T020-T021, partition T024-T025, and final composed bidirectional proof T032-T033. FR-006/FR-007 remain unchanged and final findings return to zero. |

**Coverage verification:** 42 of 42 functional requirements and 19 of 19
success criteria have task coverage.

**Analyze consensus:** CLEAN PASS. The independent confidence synthesizer
confirmed the quickstart remediation, artifact and gate alignment, frozen
CAR-003/CAR-004 decision coverage, and zero unresolved consensus defects.
Operator-only smoke status and FR-041 remain explicit conditional
implementation gates rather than analysis defects.

```text
📊 Confidence: 0.98
Task understanding: 0.99
Approach clarity: 0.98
Requirements alignment: 0.99
Risk assessment: 0.96
Completeness: 0.99
Unresolved/error status: None.
```

**Post-remediation consensus:** CLEAN PASS. The dependency-ordered registry,
comparison, partition, and final-composition tasks preserve FR-006, FR-007, and
SC-004 without claiming unavailable evidence.

```text
📊 Confidence: 0.98
Task understanding: 0.99
Approach clarity: 0.99
Requirements alignment: 0.99
Risk assessment: 0.96
Completeness: 0.97
Unresolved/error status: None.
```

**G6 Result:** ✅ Passed. Final consistency findings contain zero CRITICAL or
HIGH items, and the authoritative marker count is zero.

---

## Phase 6.5: Confidence Gate

**When to run:** After Analyze and its mandatory consensus item, before any
implementation task. Use the `advisory` mode resolved during Phase 0 and the
latest workflow confidence emit.

| Field | Value |
|-------|-------|
| Mode | Advisory |
| Threshold | 0.90 |
| Status | ✅ Passed — composite 0.98; recommended action `proceed` |
| Bounded remediation | Not required |

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
| Baseline and guardrails | T001-T003 | 3 of 3 | Owner baselines 545/545, 135/135, and 26/26; exact 12-path boundary confirmed; live smoke remains operator-only and unrun |
| Contract freeze | T004-T007 | 4 of 4 | Registry RED 545/547 → GREEN 549/549; registry-mirror RED 26/29 → GREEN 32/32; A-002 dependency ordering remediated and revalidated |
| Policy behavior and replay | T008-T015 | 8 of 8 | Unpinned RED 549/553 → GREEN 561/561; ladder RED 561/565 → GREEN 566/566; signal RED 610/616 → GREEN 615/615; movement RED 615/622 → GREEN 622/622; replay 18/18 |
| High effort and aggregation | T016-T019 | 4 of 4 | High-effort RED 622/626 → GREEN 629/629; aggregation RED 629/633 → GREEN 638/638; deterministic aggregation replay fixture verified; twin owner 32/32 |
| Comparison and claims | T020-T023 | 4 of 4 | Comparison RED 135/147 → GREEN 159/159; claim-policy RED 159/167 → GREEN 170/170; final owners policy 638/638, comparison 170/170, twin 32/32 |
| Partition, replay, and parity | T024-T027 | 4 of 4 | Partition RED 638/645 → GREEN 650/650; deterministic replay RED 650/654 → GREEN 657/657; final owners policy 657/657, comparison 170/170, twin 32/32 |
| Smoke and capture boundary | T028-T031 | 4 of 4 | Smoke plan/seal RED 657/674 → GREEN 681/681; raw-capture exclusion RED 681/689 → GREEN 689/689; live smoke remains operator-only and unrun |
| Twin reconciliation | T032-T033 | 2 of 2 | Final composition RED 32/36 → GREEN 41/41 across registry, comparison, and partition groups; zero drift buckets, zero unrepresentable members, zero frozen-contract edits |
| Verification and review evidence | T034-T038 | 5 of 5 | PR traceability packet complete; narrow owners pass 689/689, 170/170, and 41/41; docs reference generation/check passes; default suite passes 5142/5142; privacy 10/10; scope/frozen-artifact audit and diff check pass; live smoke remains operator-only and unrun |

---

## Post

| Item | Status | Notes |
|------|--------|-------|
| Post: Doctor Extension Check | Completed | Passed with 5/5 templates, agent config, Python runner, constitution, and 2/2 feature checks; two non-blocking warnings: legacy Claude command files absent and extensions.yml omits the registry-enabled speckit-utils entry |
| Post: Verify Implementation | Completed | Verify extension passed with zero findings after resolving the dedicated feature directory explicitly |
| Post: Verify Tasks Phantom Check | Completed | 38/38 tasks verified, zero flagged, zero missing task-referenced paths; report at `specs/g56r-004-policy-controls-adaptive-comparators/verify-tasks-report.md` |
| Post: Code Review | Completed | Fourteen completed independent passes found and remediated 24 Important correctness/privacy gaps with strict RED→GREEN coverage; the final pass returned `NO FINDINGS` |
| Post: Integration Suite | Completed | 5194/5194 passed: Layer 1 1428/1428, Layer 4 3580/3580, Layer 5 186/186; privacy 10/10 |
| Post: Reviewability Diff Gate | Completed | Current committed plan evidence passes with 12 declared implementation operations, zero production-runtime paths, one vertical slice, and no marker plan; installed helper supports setup mode only |
| Post: Self-Review | Completed | Four-question audit recorded below with current test, edge-case, FR/task, and tidiness evidence; zero orphan findings |
| Post: UAT Runbook Generation | Skipped | `generate-uat-skeleton` is deferred and no committed feature-local UAT runbook exists; UAT validation is unavailable |
| Post: Final Reviewability Backstop | Completed | Proceed on current committed pass evidence at `8fc3bc74`; single-PR route remains authoritative and no PR marker plan exists |
| Post: PR Packet/Body Generation | Completed | `pr-packet-output` dry-run/apply emitted the current feature-local packet/body; refined packet passed read-only validation (`pr_blocked=false`, outer `writes_state=false`), clean-worktree validation was persisted, and the PR workflow contract passed |
| Post: PR Body Generation | Completed | Refined only the three packet-sanctioned editable prose regions for public readability; protected sections remained unchanged and fresh validation passed |
| Post: PR Creation | Completed | Pushed packet-owned head and created draft PR [#403](https://github.com/racecraft-lab/racecraft-plugins-public/pull/403) against `main` with the validated packet-owned title/body |
| Post: Review Remediation | Completed | Initial PR audit found zero reviews, comments, or review threads; no actionable remediation was required; CI was queued on the newly created draft |
| Post: Retrospective | In Progress | Run `$speckit-retrospective-analyze` as the final canonical Post item |

---

### Self-Review — 2026-07-29T12:12:01Z

1. **Tests executed?** `BUILD`, `TYPECHECK`, and `INTEGRATION_TEST` are `N/A`
   in `PROJECT_COMMANDS`. `LINT` and `UNIT_TEST` both ran through
   `python3 -u tests/speckit-pro/run-all.py` immediately before this evidence
   was recorded and passed 5194/5194 (L1 1428/1428, L4 3580/3580, L5
   186/186). Focused owners also passed 730/730, 172/172, and 50/50; privacy
   passed 10/10 and docs references are current.
2. **Edge cases?** All 18 acceptance scenarios have non-happy-path evidence.
   Scenarios 1-4 are covered by closure, authority, digest, timestamp, and
   bidirectional drift controls (`test-policy-control-contracts.py:791`,
   `test-policy-control-contracts.py:852`,
   `test-twin-handoff-completeness.py:789`,
   `test-twin-handoff-completeness.py:914`). Scenarios 5-10 are covered by
   parent identity, ladder boundary, non-scorable, ineligible route, and
   parent-plus-children controls (`test-policy-control-contracts.py:1035`,
   `test-policy-control-contracts.py:1369`,
   `test-policy-control-contracts.py:1399`,
   `test-policy-control-contracts.py:1566`,
   `test-policy-control-contracts.py:1676`). Scenarios 11-13 are covered by
   ineligible, mixed/null, zero-denominator, and forbidden-claim controls
   (`test-control-comparison-dominance.py:770`,
   `test-control-comparison-dominance.py:684`,
   `test-control-comparison-dominance.py:733`,
   `test-control-comparison-dominance.py:878`). Scenarios 14-16 are covered by
   reserved-partition, outcome-bearing replay, authorization-withheld, cache,
   and raw-capture controls (`test-policy-control-contracts.py:1825`,
   `test-policy-control-contracts.py:1924`,
   `test-policy-control-contracts.py:2182`,
   `test-policy-control-contracts.py:2298`,
   `test-policy-control-contracts.py:2635`). Scenarios 17-18 are covered by
   declined-member, exact artifact derivation, and the completed PR traceability
   packet (`test-twin-handoff-completeness.py:812`,
   `test-twin-handoff-completeness.py:864`,
   `specs/g56r-004-policy-controls-adaptive-comparators/.process/pr-review-traceability.md`).
   No `[edge-case-gap]` remains.
3. **Requirements matched?** The `tasks.md` coverage matrix maps FR-001 through
   FR-042 and SC-001 through SC-019 to completed tasks. Verify-Tasks reports
   38/38 verified with zero missing paths. Task-group evidence is committed in
   `8bb3684f` through `5f9b835a`; Post review regressions and their passing
   controls are committed in `8fc3bc74`. There are zero orphan FRs, tasks, or
   implementation paths.
4. **Follow-up and tidiness?** Scans of `spec.md`, `plan.md`, `tasks.md`, commit
   messages, and changed Python/tests found no `[TODO]`, `[DEFERRED]`,
   `[OUT-OF-SCOPE]`, debug prints, breakpoints, or temporary scaffolding. The
   operator-only live smoke remains an explicit Known Gap in the review packet,
   not a silent deferral; no live or off-box execution is claimed.

---

## Post-Implementation Checklist

- [x] All tasks complete or operator-only gaps explicitly identified
- [x] Full repository suite passes with exact counts recorded
- [x] Existing test owners remain declared in `tests/speckit-pro/suite-manifest.json`; no manifest edit was required
- [x] Required docs reference generation/check passes
- [x] Zero frozen G56R-003/CAR-003 contract modifications
- [x] CAR-004 twin completeness passes in both directions
- [x] Exactly one sanctioned platform divergence remains
- [x] Reserved G56R-011 partition is mechanically untouched
- [x] No raw live model/prompt captures committed
- [x] Unrun live smokes and affected success criteria are named honestly
- [x] PR title passes the live release-readiness gate format
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
