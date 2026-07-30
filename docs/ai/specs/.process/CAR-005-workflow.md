# SpecKit Workflow: CAR-005 — Model Availability, Fallback, and Recovery Simulation

**Template Version**: 1.0.0
**Created**: 2026-07-29
**Purpose**: Executable workflow for CAR-005. Phase prompts below are populated
from the technical roadmap scope and the grill-me design concept; the autopilot
consumes them phase by phase.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/CAR-005-design-concept.md
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
| IV. Test Coverage Before Merge | Every new schema, simulator path, and fixture case covered by the repository suite | `python3 tests/speckit-pro/run-all.py --layer 1` while iterating; full suite per `tests/speckit-pro/suite-manifest.json` before PR |
| VI. KISS, Simplicity & YAGNI | Simulator proves only the mandated scenario semantics; no speculative resolver features beyond the roadmap scope | Code review against the design concept's Non-goals |

**Constitution Check:** ✅ (verified at scaffold — the spec surface is repository-only validation; no plugin runtime, payload, or shipped-default change)

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | CAR-005 |
| **Name** | Model Availability, Fallback, and Recovery Simulation |
| **Branch** | `car-005-availability-fallback-recovery` |
| **Dependencies** | CAR-004 (merged, PR #401) — frozen control registry, comparison rule, fixtures, validators |
| **Enables** | CAR-006 (route-policy manifest, materializer, preflight) — it re-proves its framework against this spec's fixture policies |
| **Priority** | P1 |

### Success Criteria Summary

From the technical roadmap scope and the design concept:

- [ ] An executable reference simulator (`lib/claude_route_fallback.py`, test-tree only) resolves fixture route policies against synthetic environment snapshots and emits resolution reports (Q1)
- [ ] The scenario corpus covers every mandated family: preferred model absent (including a `fable`-unavailable case), effort unsupported, probe unavailable, exact-invocation probe success and failure, alias re-pointing, platform route change, unqualified `CLAUDE_CODE_SUBAGENT_MODEL` override, helper-unavailable, no-safe-route, and retry exhaustion
- [ ] Two closed enums: the five roadmap-pinned resolution codes verbatim, plus the policy-violation enum (`fallback_loop`, `unqualified_adjacent_model`, `generic_agent_substitution`, `silent_inherit_materialization`, `unqualified_override`); a structural parity test asserts the resolution enum exactly matches the five codes both roadmaps pin (Q2, Q3)
- [ ] Rejection and remediation entries mirror the installed runner diagnostics envelope — `{code, message, severity, source, details, remediation: {summary, actions[]}}` (Q4)
- [ ] Alias re-pointing / platform route change code as `preferred_model_unavailable` with a machine-readable sub-reason in `details` (Q11)
- [ ] The override scenario reports the override as the effective dispatch tuple with a loud `unqualified_override` diagnostic, claims-exclusion marking, and the qualified would-have-been resolution (Q12)
- [ ] No-safe-route is report-only: unresolved agent, attempted routes, rejection reasons, and remediation (including previous-plugin-release rollback guidance) — never a mutation of shipped agent files
- [ ] Helper-unavailable: the helper is simply not consulted; the validated no-helper path continues without failing required-agent resolution
- [ ] Probe/retry/fan-out bounds are fixture-declared budget fields with schema maxima; exhaustion proven with minimal budgets; reports record actual attempt counts (Q7)
- [ ] Deterministic replay proven by pinned expected reports: run-twice byte-identity AND byte-identity to the pinned report under canonical JSON serialization (Q8)
- [ ] Delivered as 2 vertical slices in a gh-stack stacked-PR chain (Q10 + user directive)

### Reviewability Budget (setup gate, 2026-07-29)

Recorded from the authoritative `reviewability-gate` setup run against the
CAR-005 roadmap section: **pass** — reviewable LOC 257, production files 0,
total files 10, primary surface `harness/fixtures` (1). Estimator
(`estimate-spec-size`, roadmap signal convention): 770 LOC, 2 slices, status
**warn** — the estimator and the authored budget disagree; the operator chose
the estimator-recommended **split into 2 vertical slices** (Q10): slice 1 =
resolution-failure semantics (five reason codes, snapshot projection, replay
pinning); slice 2 = structural rejections, override/helper paths, retry
exhaustion. Delivery directive: with more than one PR, the slice PRs are
managed as a **gh-stack stacked-PR chain** (slice 2 stacks on slice 1).

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/car-005-availability-fallback-recovery/spec.md`

### Specify Prompt

```text
/speckit-specify

## Feature: CAR-005 Model Availability, Fallback, and Recovery Simulation

### Problem Statement

CAR-006 will implement the real route-policy manifest, materializer, and
session preflight. If its recovery semantics are designed while the framework
is being built, failure behavior becomes whatever the implementation happens
to do. CAR-005 proves bounded resolution and recovery semantics synthetically
first: an executable reference simulator plus a deterministic fixture corpus
that pins, byte-for-byte, how resolution must behave when a preferred model is
absent, an effort is unsupported, a probe is unavailable or fails, an alias
re-points, the platform changes a route, an environment carries an unqualified
override, the optional helper is unavailable, or no safe route exists. CAR-006
then re-proves its production resolver against this same corpus — the fixtures
land already tested, and the framework inherits its failure semantics instead
of inventing them.

### Users

- CAR-006 (primary consumer): re-proves the route-policy framework against the
  fixture policies, adopts the resolution-report contract, reason-code enums,
  snapshot projection, and declared-budget fields.
- CAR-007 through CAR-010: inherit the proven rejection semantics (no fallback
  loops, no unqualified adjacent models, no generic-agent substitution, no
  silent inherit) for cohort qualification.
- G56R-005 (Codex twin, not yet scaffolded): mirrors the structural template —
  schemas, enums, corpus organization — set by this first-mover spec.
- Operators: read the no-safe-route report's remediation (including
  previous-plugin-release rollback guidance) when a real preflight later
  reports an unresolvable agent.

### User Stories

Two stories, one per accepted vertical slice (Q10):

- [US1] Resolution-failure semantics: as the routing program, prove that route
  resolution against a synthetic environment snapshot walks preferred route
  then ordered fallbacks, emits the five pinned reason codes with
  machine-readable sub-reasons, and replays byte-identically against pinned
  expected reports.
- [US2] Structural rejection and recovery semantics: as the routing program,
  prove that structurally defective policies (loops, unqualified adjacent
  models, generic-agent substitution, silent inherit) are rejected with their
  own closed violation codes, that unqualified overrides and
  helper-unavailable environments behave as contracted, and that declared
  probe/retry/fan-out budgets exhaust deterministically with report-only
  no-safe-route output.

### Design decisions to encode (from the design concept Q&A log)

- The thing-under-test is an executable reference simulator in
  tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py — a pure
  function over (policy fixture, synthetic snapshot, overrides, declared
  budgets) returning a resolution report; the fixtures are the durable
  contract CAR-006 re-proves against (Q1).
- Two closed enums: the roadmap's five resolution codes verbatim
  (preferred_model_unavailable, effort_unsupported,
  capability_probe_unavailable, treatment_probe_failed, no_safe_route) plus a
  CAR-005-owned policy-violation enum (fallback_loop,
  unqualified_adjacent_model, generic_agent_substitution,
  silent_inherit_materialization, unqualified_override) (Q2, Q12).
- Schemas land platform-scoped in
  tests/speckit-pro/layer6-efficiency/contracts-claude/; nothing is added to
  the shared byte-identical contracts/ directory; a structural parity test
  asserts the resolution enum matches the five codes both roadmaps pin (Q3).
- Every rejection/remediation entry mirrors the installed runner diagnostics
  envelope: {code, message, severity, source, details,
  remediation: {summary, actions[]}} (Q4).
- Fixture policies name a small synthetic cast by role class
  (fixture-required-executor, fixture-bounded-analyst,
  fixture-optional-helper); never the twelve real shipped agent names (Q5).
- The simulator input is a minimal purpose-built snapshot projection:
  available model IDs, alias-to-resolved bindings, per-model supported
  efforts, probe availability, exact-invocation probe outcomes — not the full
  CAR-002 capture-record shape; defining this projection IS the CAR-006
  preflight input contract (Q6).
- Probe/retry/fan-out bounds are fixture-declared budget fields with
  schema-enforced maxima; the simulator treats them as hard caps and reports
  actual attempt counts (Q7).
- Deterministic replay: each corpus case pins its full expected resolution
  report; tests assert run-twice byte-identity and byte-identity to the
  pinned report under canonical JSON serialization; no wall-clock or
  randomness inputs (Q8).
- One self-contained scenario corpus,
  fixtures-fallback/fallback-scenario-corpus.json, where each case bundles
  {policy, synthetic snapshot, overrides, declared budgets, expected report}
  (Q9).
- Alias re-pointing and platform route change map to
  preferred_model_unavailable with a machine-readable sub-reason
  (alias_repointed | platform_route_changed | model_absent) in the envelope's
  details object; the five-code enum is not extended (Q11).
- The unqualified CLAUDE_CODE_SUBAGENT_MODEL scenario simulates documented
  runtime behavior honestly: the override wins as the effective dispatch
  tuple, the report emits a loud unqualified_override diagnostic, marks the
  environment excluded from release claims, and still records the qualified
  would-have-been resolution (Q12).
- No-safe-route is report-only (unresolved agent, attempted routes, rejection
  reasons, remediation including previous-plugin-release rollback); shipped
  agent files are never mutated. Helper-unavailable means the helper is not
  consulted and the validated no-helper path continues without failing
  required-agent resolution (roadmap scope).
- Delivery: 2 vertical slices as a gh-stack stacked-PR chain — slice 2 stacks
  on slice 1 (Q10 + recorded user directive).

### Constraints

- Python 3.11+ standard library only; repository-only surface (no plugin
  runtime, payload, or shipped-default change; 0 production files).
- Deterministic everything: canonical JSON serialization, no timestamps, no
  randomness in simulator output.
- Durable file names (never coupled to the spec ID) for scripts and tests.
- Additive only: no edit to any frozen CAR-002/003/004 schema or fixture; no
  member added to the shared byte-identical contracts/ directory.

### Out of Scope

- The real resolver, manifest schema, materializer, preflight doctor
  operation, and SessionStart warning (CAR-006).
- Real route qualification and final preferred/fallback selection
  (CAR-007 through CAR-010).
- Live UAT, live probing, or any live dispatch; production checkpoint/resume
  scheduling.
- Real shipped agent names in fixtures; reuse of the full CAR-002
  runtime-capability-snapshot shape as simulator input.
- Any Codex-side change (G56R-005 mirrors later; parity promotion to shared
  contracts/ is a deliberate future joint change).
```

### Specify Results

<!-- Fill in after running the command -->

| Metric | Value |
|--------|-------|
| Functional Requirements | |
| User Stories | |
| Acceptance Criteria | |

### Files Generated

- [ ] `specs/car-005-availability-fallback-recovery/spec.md`

### SpecKit Traceability Markers

Use these markers in spec.md for traceability through later phases:

| Marker | Purpose | Example |
|--------|---------|---------|
| `[US1]`, `[US2]` | User story reference | `[US1] Resolution walks preferred then ordered fallbacks` |
| `[FR-001]` | Functional requirement | `[FR-001] Resolution enum carries exactly the five pinned codes` |
| `[NEEDS CLARIFICATION]` | Flag for Clarify phase | `Sub-reason enum membership [NEEDS CLARIFICATION]` |
| `[P]` | Parallel-safe task | `[P] Can run alongside other tasks` |
| `[Gap]` | Missing coverage | `[Gap] No case covers fan-out exhaustion` |

---

## Phase 2: Clarify (Optional but Recommended)

**When to run:** When spec has areas that could be interpreted multiple ways. 10-20 minutes here saves hours of rework later.

**Best Practice:** Maximum 5 targeted questions per Clarify session.

### Clarify Prompts

#### Session 1: Slice seam and stacked delivery

Seeded from design-concept Open Questions 1 and 2.

```text
/speckit-clarify Focus on the two-slice seam: exactly which schemas, corpus
cases, simulator functions, and tests land in slice 1 (resolution-failure
semantics) versus slice 2 (structural rejections, override/helper paths,
exhaustion); how slice 2 stacks on slice 1's schemas in the gh-stack chain so
slice 1 is independently landable and releasable; and whether the plan-phase
LOC re-estimate still supports two slices or the operator should be asked to
ratify a single-slice fallback (the setup estimator said warn/770/2 while the
authored roadmap budget said ok/257/1).
```

#### Session 2: Enum closure and report field totality

Seeded from design-concept Open Question 4 and the report contract.

```text
/speckit-clarify Focus on closed-set membership: the exact details sub-reason
enum for preferred_model_unavailable (alias_repointed |
platform_route_changed | model_absent — is the set exhaustive for the
mandated scenarios?); whether the policy-violation enum needs any member
beyond the five decided at scoping; the closed set of remediation action
strings (including the previous-plugin-release rollback wording) so pinned
reports stay byte-stable; and which report fields are required versus
optional for a successful resolution versus a no-safe-route outcome.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Slice seam / stacked delivery | | |
| 2 | Enum closure / report totality | | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/car-005-availability-fallback-recovery/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack

- Language: Python 3.11+ standard library only (constitution principle II)
- Surface: repository-only validation under
  tests/speckit-pro/layer6-efficiency/ and tests/speckit-pro/unit/
- Contracts: JSON Schema documents in
  tests/speckit-pro/layer6-efficiency/contracts-claude/ (draft 2020-12 and
  $id convention matching the CAR-003/004 schemas they sit beside)
- Simulator: tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py
  following the claude_*.py naming convention
- Fixtures: tests/speckit-pro/layer6-efficiency/fixtures-fallback/ (new
  directory, named per the existing fixtures-<topic> pattern)
- Testing: unit tests in tests/speckit-pro/unit/ registered through
  tests/speckit-pro/suite-manifest.json; layer runner
  python3 tests/speckit-pro/run-all.py

## Constraints

- 0 production files: nothing under speckit-pro/ changes; the simulator is an
  executable specification living in the test tree (design concept Q1).
- Additive only: no edit to frozen CAR-002/003/004 schemas or fixtures; no
  member added to the shared byte-identical contracts/ directory (Q3; the
  joint-change rule from the CAR-012 record).
- Durable names: no script or test filename coupled to the CAR-005 spec ID.
- Deterministic: canonical JSON serialization for reports; no timestamps,
  randomness, or environment-dependent output anywhere in the simulator.
- Two-slice delivery: the plan's file operations must partition cleanly along
  the Q10 seam so slice 1 lands independently and slice 2 stacks on it
  (gh-stack chain per the recorded user directive).

## Architecture Notes

- Follow the established schema + lib + fixture + unit-test pattern: a
  route-policy fixture schema, a snapshot-projection schema, and a
  resolution-report schema in contracts-claude/; the simulator in lib/; the
  self-contained scenario corpus in fixtures-fallback/; coverage in unit/.
- The resolution report's rejection entries reuse the installed runner
  diagnostics envelope shape ({code, message, severity, source, details,
  remediation: {summary, actions[]}}) so CAR-006's doctor operation emits it
  natively (Q4).
- Resolution algorithm under test: walk preferred route then ordered
  fallbacks; each candidate checks model availability, alias binding
  stability, effort support, and probe outcomes against the synthetic
  snapshot; fallback changes only model and effort for the same named agent;
  structural validation (loop/adjacent/substitution/inherit) rejects the
  policy before any route walk (Q2).
- Budgets (probe attempts, retries, fan-out) are fixture-declared fields with
  schema maxima; the simulator enforces them as hard caps and reports actual
  counts; exhaustion cases use minimal budgets (Q7).
- Replay: each corpus case pins its expected report; the test asserts
  run-twice byte-identity and pinned-report byte-identity (Q8).
- The structural parity test reads the resolution enum from the committed
  schema and asserts exact equality with the five codes pinned in BOTH
  docs/ai/specs/claude-agent-routing-technical-roadmap.md and the Codex
  roadmap (Q3).
- Re-read docs/ai/specs/.process/CAR-005-design-concept.md for the rationale
  behind any decision the prompts compress.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Technical context, execution flow |
| `research.md` | ⏳ | Decision rationales (if needed) |
| `data-model.md` | ⏳ | Entities and types |
| `contracts/` | ⏳ | Fixture/snapshot/report contract specifications |
| `quickstart.md` | ⏳ | Developer onboarding |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates both spec AND plan together. Run multiple times for different domains.

**Best Practice:** Don't guess which domains to check. Analyze the spec first, then generate enriched prompts with spec-specific focus areas.

### Step 1: Analyze Spec for Recommended Domains

Domain signals for this spec: JSON contract schemas, closed enums, and
byte-pinned golden reports (**data-integrity**); the entire subject matter is
failure paths, bounded retries, exhaustion, and recovery guidance
(**error-handling**); and the semantics simulated are model routing facts —
alias re-pointing, effort support, override env vars, probe outcomes
(**llm-integration**). UI, API-endpoint, streaming, and security domains do
not apply to a repository-only simulation surface with no live dispatch.

### Step 2: Run Enriched Checklist Prompts

#### 1. data-integrity Checklist

Why this domain: the spec's core outputs are closed enums, schema contracts,
and byte-pinned expected reports whose integrity CAR-006 depends on.

```text
/speckit-checklist data-integrity

Focus on CAR-005 Model Availability, Fallback, and Recovery Simulation requirements:
- Closed-enum discipline: both enums schema-closed (additionalProperties /
  enum constraints), the resolution enum exactly the five pinned codes, and
  the parity test failing on any drift in either direction.
- Corpus self-containment: every case carries policy, snapshot, overrides,
  budgets, and expected report with no cross-case references; case IDs unique
  and stable.
- Canonical serialization: the byte-identity rule is well-defined (key order,
  whitespace, unicode) and identical between the simulator and the pinning
  test.
- Pay special attention to: schema maxima on declared budgets — an
  out-of-range budget must fail schema validation, not silently clamp.
```

#### 2. error-handling Checklist

Why this domain: the spec exists to pin failure semantics — every scenario is
an error path with a contracted outcome.

```text
/speckit-checklist error-handling

Focus on CAR-005 Model Availability, Fallback, and Recovery Simulation requirements:
- Scenario totality: every mandated family (preferred absent incl.
  fable-unavailable, effort unsupported, probe unavailable, exact-invocation
  success AND failure, alias re-pointing, platform route change, unqualified
  override, helper-unavailable, no-safe-route, retry exhaustion) has at least
  one corpus case with a pinned report.
- Structural rejections fire before route walking; each maps to exactly one
  policy-violation code; no defect maps to prose only.
- Exhaustion semantics: which resolution code fires when each budget class
  (probe attempts, retries, fan-out) exhausts, and attempt counts in the
  report equal the declared budget.
- No-safe-route report completeness: unresolved agent, every attempted route
  with its rejection diagnostic, and remediation including the
  previous-plugin-release rollback action.
- Pay special attention to: helper-unavailable — the optional helper is not
  consulted (zero probe attempts recorded for it) and required-agent
  resolution still succeeds.
```

#### 3. llm-integration Checklist

Why this domain: the simulated facts are model routing semantics — aliases,
efforts, probes, and the subagent-model override — that must match documented
platform behavior.

```text
/speckit-checklist llm-integration

Focus on CAR-005 Model Availability, Fallback, and Recovery Simulation requirements:
- Route-tuple fidelity: a route is alias + qualified resolved model ID +
  explicit effort; an alias re-point invalidates the tuple
  (preferred_model_unavailable + alias_repointed sub-reason), never a silent
  re-qualification.
- Snapshot projection sufficiency: the minimal projection carries everything
  resolution consumes (model IDs, alias bindings, per-model efforts, probe
  availability, exact-invocation outcomes) and nothing it doesn't — this is
  CAR-006's preflight input contract.
- Override honesty: the simulated CLAUDE_CODE_SUBAGENT_MODEL behavior matches
  the documented runtime (override wins at dispatch); the report flags it
  loudly and excludes the environment from release claims while still
  recording the qualified would-have-been route.
- Pay special attention to: alignment with CAR-002's probed
  unavailable-model observation — an unavailable model is a preflight
  detection from the snapshot, never a simulated dispatch attempt.
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

**When to run:** After checklists complete (all gaps resolved). Output: `specs/car-005-availability-fallback-recovery/tasks.md`

### Tasks Prompt

```text
/speckit-tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: schemas -> simulator core -> corpus cases -> replay
  pinning -> structural-rejection and override/helper paths -> exhaustion ->
  parity test -> suite-manifest registration
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story: US1 (slice 1, resolution-failure semantics) before
  US2 (slice 2, structural rejections + override/helper + exhaustion); TDD
  RED->GREEN pairs throughout

## Implementation Phases
1. Slice 1 foundation: route-policy, snapshot-projection, and
   resolution-report schemas + canonical-serialization helper
2. Slice 1 proof: simulator resolution walk, five-code semantics, sub-reason
   details, corpus cases for the resolution-failure families, pinned replay
   test
3. Slice 2 rejections: structural validation (loop, adjacent, substitution,
   inherit) + override and helper-unavailable cases with pinned reports
4. Slice 2 recovery: declared-budget exhaustion cases, no-safe-route report
   with rollback remediation, structural parity test, suite-manifest
   registration

## Constraints
- The slice seam is load-bearing: no US2 task may edit a US1 artifact in a
  way that would force slice-1 PR churn; slice 2 stacks on slice 1
  (gh-stack chain per the recorded user directive).
- Unit tests live in tests/speckit-pro/unit/ with durable (non-spec-ID)
  filenames; register in tests/speckit-pro/suite-manifest.json.
- Fixtures live under tests/speckit-pro/layer6-efficiency/fixtures-fallback/.
- Bound task generation by the design concept's Non-goals: no production
  resolver tasks, no real-agent-name fixtures, no shared contracts/ members,
  no live dispatch, no CAR-002/003/004 schema edits. Flag any task that would
  cross these boundaries.
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

Scoping note: the operator has already ratified a 2-slice split (Q10) with
gh-stack stacked delivery. If the classifier route disagrees with `split-PR`,
surface the conflict to the operator instead of silently following either.

To produce the decision, run the classifier against the feature directory:

```text
runner helper atomicity-route specs/car-005-availability-fallback-recovery
```

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```text
/speckit-analyze

Focus on:
1. Constitution alignment — Python 3.11+ stdlib only, deterministic I/O,
   durable filenames, 0 production files
2. Coverage gaps — every FR, every mandated scenario family, and both user
   stories have tasks; every corpus case has a pinned expected report
3. Consistency between task file paths and the layer6 harness structure
   (contracts-claude/, lib/, fixtures-fallback/, unit/)
4. Design-concept drift — docs/ai/specs/.process/CAR-005-design-concept.md is
   the source of truth for scoping decisions; if spec.md, plan.md, or
   tasks.md contradicts it (two-enum taxonomy, five codes verbatim,
   diagnostics-envelope report shape, synthetic fixture-* names, minimal
   snapshot projection, fixture-declared budgets, byte-identical pinning,
   2-slice split with gh-stack delivery) the downstream artifact is wrong
   unless a dated revision note says otherwise
5. Verify no task adds a shared contracts/ member, edits a frozen
   CAR-002/003/004 schema, names a real shipped agent in fixtures, or
   introduces live dispatch
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
2. Verify you are on `car-005-availability-fallback-recovery` (never main)
3. Re-read docs/ai/specs/.process/CAR-005-design-concept.md — decisions
   captured there but missing from tasks.md are gaps to surface before
   coding, not silently drop

### Implementation Notes
- Match the CAR-003/004 conventions in contracts-claude/ and lib/claude_*.py —
  schema style ($schema draft 2020-12, racecraft.dev $id), validator
  structure, error taxonomy discipline.
- Determinism is absolute: canonical JSON serialization everywhere a report
  is produced or compared; no timestamps, randomness, dict-order dependence,
  or environment-dependent output.
- Respect the slice seam while committing: slice-1 artifacts (schemas,
  simulator resolution walk, resolution-failure corpus + replay test) must
  not depend on slice-2 artifacts; the PR-emission step delivers two stacked
  PRs via gh-stack (slice 2 on slice 1).
- The smallest useful check while iterating is the affected unit test file;
  run the broader suite (per suite-manifest.json) before the PR.
- After any tracked .py change under tests/speckit-pro/, the generated docs
  reference is stale: run pnpm --dir docs-site reference:generate (deps
  already installed in this worktree) before calling the work done.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Slice 1: schemas + serialization | | | |
| 2 - Slice 1: simulator + corpus + replay | | | |
| 3 - Slice 2: rejections + override/helper | | | |
| 4 - Slice 2: exhaustion + parity + registration | | | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in tasks.md
- [ ] Full repository suite passes per `tests/speckit-pro/suite-manifest.json`
- [ ] New unit tests registered in the suite manifest
- [ ] Docs reference regenerated (`pnpm --dir docs-site reference:generate`; deps installed at scaffold) — new `.py` files under `tests/speckit-pro/` stale the generated `reference/tests.md`, and CI's validate-docs job runs `reference:check` against it
- [ ] No shared `contracts/` member added; no frozen CAR-002/003/004 schema modified (additive-only verified in the diff)
- [ ] Structural parity test proves the resolution enum matches both roadmaps' five pinned codes
- [ ] Two stacked slice PRs created via gh-stack (slice 2 stacks on slice 1); each PR title passes the release-readiness gate (`<type>(<lowercase-scope>): <plain English description>`) and each feat/fix PR body carries exactly one non-empty release-note fence
- [ ] PRs reviewed
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
│   ├── contracts-claude/       # + route-policy / snapshot-projection / resolution-report schemas
│   ├── fixtures-fallback/      # + fallback-scenario-corpus.json (new directory)
│   └── lib/                    # + claude_route_fallback.py (reference simulator)
├── unit/                       # + test-route-fallback-simulation.py (durable name)
└── suite-manifest.json         # register new unit tests
specs/car-005-availability-fallback-recovery/   # spec.md, plan.md, tasks.md, SPEC-MOC.md
docs/ai/specs/.process/                          # this workflow + design concept
```

---

Template based on SpecKit best practices. Prompts above are populated from the CAR-005 roadmap scope and the 2026-07-29 grill-me design concept.
