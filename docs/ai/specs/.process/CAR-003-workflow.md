# SpecKit Workflow: CAR-003 — Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

**Template Version**: 1.0.0
**Created**: 2026-07-24
**Purpose**: Executable workflow for CAR-003. Copy-paste the prompts below into your AI coding agent, or run `/speckit-pro:speckit-autopilot` against this file.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/CAR-003-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. The
Specify and Clarify Prompts below were populated from that interview,
so the design concept doc is the source of truth for any decision
captured during scoping.

> **Note:** Grill Me is human-in-the-loop only. It is **not** part of
> the autopilot loop. Once the workflow file is populated and autopilot
> begins, clarifications happen via `/speckit-clarify` and the
> consensus protocol — never via grill-me.

### Decisions carried from the interview

| Q | Branch | Decision |
|---|--------|----------|
| Q1 | Candidate admission | Successor capability snapshot + versioned refresh triggers; close CAP-Q6 alias-re-pointing detection |
| Q2 | Environment contract | Dated amendment to AC-2.19: subscription auth is the supported scored path, API-key optional |
| Q3 | Capability coverage | Probe the full ordered effort set `low` through `max` per role-eligible model |
| Q4 | Source ownership | Canonical materializer ships in `speckit_pro_runner`; Layer 6 keeps a thin adapter |
| Q5 | Shared infrastructure | Edit the shared dual-platform smoke runner in place; coordinate the merge with G56R-003 |
| Q6 | Evidence schema | New trace records under the frozen CAR-002 contract + a separate versioned score bundle |
| Q7 | Scoring authority | Deterministic hard gates + frozen blinded semantic rubric |
| Q8 | Adjudication | Two candidate-blind ballots, third adjudicator on disagreement, all ballots retained |
| Q9 | Selection rule | Content-address one dated price-sheet revision at lock time and freeze it |
| Q10 | CI boundary | Explicit local budgeted campaigns; CI runs deterministic replay only, zero live calls |
| Q11 | Stage ownership | CAR-003 implements the stages; CAR-007 through CAR-010 run outcome-bearing campaigns |
| Q12 | Pilot validity | Calibration-only partition; records explicitly ineligible for qualification |
| Q13 | Analysis plan | Freeze margins, sample sizes, power, multiplicity, attrition after calibration |
| Q14 | Reviewability | Three ordered slices; WP-A stays intact as slice 1 |

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
| I. Plugin Structure Compliance | The materializer lands in `speckit_pro_runner` as a shipped module (Q4); the generated-artifact contract is accounted for before the work is called done | Review plugin manifests and payload hashes; plugin-shaped run with `speckit-pro/` alone |
| II. Cross-Platform Runtime & Script Safety | Python 3.11+ standard-library importable modules; no new Bash or `jq`; live campaigns are operator-only, never CI (Q10) | `python3 tests/speckit-pro/run-all.py` is deterministic with zero live calls |
| IV. Test Coverage Before Merge | Deterministic unit tests cover the successor-snapshot schema, materializer equivalence, score-bundle contract, scorer contracts, adjudication, and statistical decisions; suite green | `python3 tests/speckit-pro/run-all.py` |
| V. Conventional Commits | Scoped commits, e.g. `feat(car-003): ...` / `test(speckit-pro): ...` / `chore(car-003): ...` | `git log` review |
| VI. KISS, Simplicity & YAGNI | One materializer implementation, not two (Q4); only the record fields the ACs require; no speculative schema surface | Review against design concept Q4, Q6, Q9 |

**Constitution Check:** ⏳ (mark before proceeding to G1)

### Scaffold Preflight

| Item | Result |
|------|--------|
| Claude agent package | 11/11 bundled agents present, including `uat-runbook-author.md` |
| SpecKit CLI | `specify 0.12.12.dev0` |
| Reviewability setup gate | `status: warn`, `pass: true`, 0 blockers; 1 warning (primary surfaces 5 exceeds warn threshold 1) |
| Size estimator | Roadmap signals → `502 LOC / 2 slices / warn`; post-interview signals → `675 LOC / 2 slices / warn`. Binding constraint is the gate's 25-total-file block, not LOC — see Q14 |
| Branch context | `car-003-evaluation-runner-scoring`, IS_WORKTREE=true. Non-numeric branch pattern → autopilot must create `.specify/feature.json` (gitignored) pointing at `specs/car-003-evaluation-runner-scoring` and use the skip-branch-creation prefix for Specify dispatch |
| PROJECT_COMMANDS | Stack `unknown`, all N/A — constitution commands govern: UNIT_TEST / FULL_VERIFY = `python3 tests/speckit-pro/run-all.py` (Layers 1/4/5); no BUILD / TYPECHECK / LINT surface |
| PRESET_CONVENTIONS | `speckit-pro-reviewability` v1.0.0 — spec/plan/tasks templates resolve as top layer |
| Bootstrap | None documented in `AGENTS.md`; nothing installed |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | CAR-003 |
| **Name** | Evaluation Runner, Fixtures, Scoring, and Statistical Analysis |
| **Branch** | `car-003-evaluation-runner-scoring` |
| **Dependencies** | CAR-002 (complete / archived, PR #369) |
| **Enables** | CAR-004; the qualification platform for CAR-007 through CAR-010 |
| **Priority** | P1 |

### Success Criteria Summary

- [ ] An immutable successor capability snapshot exists, captured under the recorded auth mode, covering the full ordered effort set `low` through `max` per role-eligible model
- [ ] CAP-Q6 is closed: the alias-re-pointing detection rule distinguishes platform-initiated route change from SpecKit Pro fallback, and never reports the former as the latter
- [ ] Versioned refresh triggers are defined and invalidate affected evidence on client change, catalog change, alias re-point, or source-ledger change
- [ ] A canonical materializer in `speckit_pro_runner` parses `agents/*.md` into a policy structure and renders evaluation configurations proven semantically equivalent to real `speckit-pro:<name>` dispatch
- [ ] Real installed-plugin dispatch is proven from the transcript, with the per-model usage breakdown establishing the effective model
- [ ] Treatment misdelivery is classified separately from candidate quality, and any platform-initiated route change marks the run non-scorable
- [ ] The legacy prompt-emulation path is labeled smoke-only; historical results carry `non_release_evidence`
- [ ] A governed twelve-role corpus exists under `fixtures/<agent>/`, with versioned fixture and scorer contracts
- [ ] `results/consolidated-*.json` commits through an explicit gitignore allow rule while per-run outputs stay ignored
- [ ] Blind adjudication resolves low or surprising output into exactly one of the five AC-2.20 causes, with no score threshold predetermining the cause
- [ ] `experiment_policy_id` is frozen with disjoint screening / selection / cohort-lock / confirmation partitions and `inconclusive => no qualification`
- [ ] The immutable production comparator is bound: repository revision, plugin version, eleven current frontmatter tuples with dated-ID resolution from the snapshot, instruction hashes, mutation contracts, client version, corpus snapshot
- [ ] The selection scalar's coefficients are content-addressed from one dated price-sheet revision, labeled diagnostic-derived, with the complete raw token vector always reported alongside
- [ ] A calibration-only live pilot proves the platform end-to-end, and every pilot record states it is ineligible for qualification
- [ ] Campaign budgets are frozen before any outcome-bearing run: maximum raw-token use, wall time, candidate count, futility rules, racing method, confirmation-entry cap
- [ ] Full default suite green with zero live calls; payload boundary clean

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/car-003-evaluation-runner-scoring/spec.md`

### Specify Prompt

```text
/speckit-specify Build the reusable, qualification-capable evaluation platform for Claude Code agent route selection: a successor runtime capability freeze, a canonical shipped materializer with proven exact-treatment equivalence, a governed twelve-role corpus with blinded scoring, a frozen experiment policy with a price-weighted selection scalar, and a calibration-only live pilot — without emitting any final route policy.
```

#### Detailed Prompt (for complex specs)

```text
/speckit-specify

## Feature: CAR-003 Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

### Problem Statement

CAR-002 established what the Claude runtime can do and how a run proves it was
delivered as configured. Nothing yet decides whether one route is better than
another. The current Layer 6 path emulates agents with bare prompts and scores
them by lexical heading and word overlap — AC-2.19 explicitly classifies that as
smoke-only degradation evidence that cannot support release. CAR-003 builds the
platform that turns capability evidence into qualification evidence, so the four
cohort specs (CAR-007 through CAR-010) can run per-agent campaigns against one
governed corpus, one frozen analysis plan, and one canonical treatment path.

Two facts make the dependency non-trivial. First, the archived snapshot
(`CAR-002-RCS-2026-07-17-V3`) binds `opus` to `claude-opus-4-8` as of
2026-07-17, and the model catalog has moved since — so a successor freeze is
required before any qualification-capable execution, and CAP-Q6 alias
re-pointing, left open by CAR-002, has to be closed. Second, that snapshot
probed only `max` and `low`, so `high` — the AC-2.1 documented-default search
origin — was never observed at all.

### Users

- Maintainers running per-agent qualification campaigns in CAR-007 through CAR-010
- Reviewers auditing whether a route decision is replayable and evidence-backed
- The CAR-006 frontmatter drift gate and session preflight, which consume the
  same canonical materializer this spec ships

### User Stories

Derive the user stories from the two roadmap work packages, preserving both, and
from the three-slice division recorded in design concept Q14:

[US1] Treatment and capability — successor capability freeze with the full
ordered effort ladder, alias-re-pointing detection and refresh triggers, the
canonical materializer in `speckit_pro_runner`, real installed-plugin dispatch
with transcript-proven spawn, cache isolation between arms, misdelivery
classification, and new execution-trace records under the frozen CAR-002
contract. This is roadmap Work Package A, kept intact.

[US2] Corpus and blinded scoring — the governed twelve-role corpus, versioned
fixture and scorer contracts, deterministic hard gates, the frozen semantic
rubric under two candidate-blind ballots plus a disagreement adjudicator, the
five-cause adjudication taxonomy, and the gitignore allow rule for consolidated
baselines.

[US3] Experiment policy and statistics — the frozen `experiment_policy_id` with
disjoint partitions, the immutable production comparator, the content-addressed
price-weighted selection scalar, stage implementations for A1, A2, A3, B and C,
campaign budgets, replayable task-level paired inference, and the
calibration-only live pilot.

### Constraints

- Python 3.11+ standard library only; no new Bash or `jq` dependency
- The canonical materializer ships in `speckit_pro_runner`; Layer 6 keeps only a
  thin adapter, and there is exactly one materializer implementation
- The CAR-002 capability snapshot, telemetry profile, and trace contract schema
  are immutable — emit new records under them, never edit them
- Scores live in a separate versioned bundle referencing trace records by ID;
  the frozen `exactTreatmentReplay.outcome` shape is not extended
- Subscription authentication is the supported scored path; API-key
  authentication is optional and must never be required. Record the auth mode of
  every run and produce no plan-based claim. This is a dated amendment to
  AC-2.19 and must be recorded as such
- Live campaigns are operator-only and explicitly budgeted; the default suite
  runs deterministic replay with zero live calls
- Raw captures inherit CAR-002's sanitization contract — no raw model, CLI,
  prompt, or response bytes are committed
- Fast mode and any orchestration-topology-changing mode are policy-level
  controls owned by CAR-004, never ordinary per-agent efforts
- The shared dual-platform smoke runner is also touched by the in-flight
  G56R-003 branch; treat merge coordination as an explicit deliverable and
  resolve overlap by merge rather than rebase

### Out of Scope

- Final preferred and fallback route policies, shipped defaults, aggregate
  release identities, resolver or preflight behavior, and release confirmation
- Running outcome-bearing per-agent A1/A2/A3, Stage B or Stage C campaigns —
  CAR-003 implements the stages; the cohort specs execute them
- Consuming screening, selection, cohort-lock, or untouched
  integrated-confirmation objectives during the CAR-003 pilot
- Treating the lexical scorer as qualification evidence, or deleting the legacy
  smoke runner
- Requiring an API key for any supported path
- Policy controls and adaptive comparators (CAR-004) and availability or
  fallback simulation (CAR-005)
```

### Specify Results

<!-- Fill in after running the command -->

| Metric | Value |
|--------|-------|
| Functional Requirements | |
| User Stories | |
| Acceptance Criteria | |

### Files Generated

- [ ] `specs/car-003-evaluation-runner-scoring/spec.md`

### SpecKit Traceability Markers

Use these markers in spec.md for traceability through later phases:

| Marker | Purpose | Example |
|--------|---------|---------|
| `[US1]`, `[US2]` | User story reference | `[US1] Successor capability freeze` |
| `[FR-001]` | Functional requirement | `[FR-001] Alias re-pointing marks the run non-scorable` |
| `[NEEDS CLARIFICATION]` | Flag for Clarify phase | `Adjudicator identities [NEEDS CLARIFICATION]` |
| `[P]` | Parallel-safe task | `[P] Can run alongside other tasks` |
| `[Gap]` | Missing coverage | `[Gap] No task covers attrition thresholds` |

---

## Phase 2: Clarify (Optional but Recommended)

**When to run:** When spec has areas that could be interpreted multiple ways. 10-20 minutes here saves hours of rework later.

**Best Practice:** Maximum 5 targeted questions per Clarify session.

The design concept's Open Questions are the seed for these sessions — everything
else was settled during the interview and should not be re-litigated.

### Clarify Prompts

#### Session 1: Capability freeze and invalidation

```text
/speckit-clarify Focus on the successor capability freeze: what exactly constitutes an alias re-pointing event versus a SpecKit Pro fallback; which observable fields the detection rule reads; what the four refresh triggers (client change, catalog change, alias re-point, source-ledger change) invalidate and what survives; how an unresolved availability blocks a route's scored run; and how the recorded auth mode interacts with the AC-2.19 amendment.
```

#### Session 2: Scoring contracts and adjudication

```text
/speckit-clarify Focus on scoring: the boundary between deterministic hard gates and the semantic rubric; how a fixture or scorer version bump invalidates affected candidate results; what evidence the two blinded ballots and the disagreement adjudicator retain for replay; how blinding is enforced so the adjudicator cannot infer candidate identity; and how the five AC-2.20 causes are assigned without any score threshold predetermining the cause.
```

#### Session 3: Partitions, comparator, and budgets

```text
/speckit-clarify Focus on experiment policy: how the screening, selection, cohort-lock and confirmation partitions stay provably disjoint; what makes a calibration-only record permanently ineligible for qualification; exactly which fields pin the immutable production comparator; how the price-sheet revision is content-addressed and what happens when list prices change mid-series; and which campaign budget fields must be frozen before the first outcome-bearing run.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Capability freeze and invalidation | | |
| 2 | Scoring contracts and adjudication | | |
| 3 | Partitions, comparator, and budgets | | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/car-003-evaluation-runner-scoring/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack

- Language: Python 3.11+, standard library only (constitution principle II)
- Shipped plugin module: `speckit_pro_runner` — hosts the canonical materializer
- Harness: `tests/speckit-pro/layer6-efficiency/` — thin adapters, fixtures, contracts
- Existing CAR-002 libraries to consume, not modify:
  `lib/claude_capabilities.py`, `lib/claude_trace_schema.py`
- Testing: `python3 tests/speckit-pro/run-all.py` (Layers 1/4/5), deterministic, zero live calls
- No Bash, no `jq`, no external evaluation framework, no second materializer

## Constraints

- The materializer is one implementation in `speckit_pro_runner`, consumed by a
  thin Layer 6 adapter now and reused directly by the CAR-006 drift gate and
  session preflight later. Do not implement it under `tests/` and relocate later
  — that would run the artifact and hash regeneration ritual twice
- Placing production code in the shipped payload means the roadmap's recorded
  `Production files: 0` reviewability budget no longer holds. Re-run the
  reviewability gate against the real plan and record the new figure
- CAR-002's schema and evidence are immutable. New execution-trace records
  conform to the existing `exactTreatmentReplay` contract unchanged; the score
  bundle is a separate versioned artifact referencing them by ID
- Subscription auth is the supported scored path. Record the AC-2.19 amendment
  explicitly, with a date, so Analyze does not read it as spec-versus-PRD drift
- Cache state is isolated between arms; billed cache writes make crossover
  directly distortive
- The shared 495-line dual-platform smoke runner is edited in place. Sync from
  `main` before implementing and coordinate with `g56r-003-evaluation-runner-scoring`

## Architecture Notes

- Successor capability freeze: a collector plus one immutable snapshot record,
  probing the full ordered effort set `low` through `max` per role-eligible
  model, with four versioned refresh triggers. `high` is the AC-2.1 search
  origin and was never probed by CAR-002 — it must be covered
- Alias re-pointing detection compares the observed model ID against the
  resolved qualified ID; a mismatch is always recorded as platform behavior,
  never as SpecKit Pro fallback, and makes the run non-scorable for the
  requested route
- Exact treatment: real installed-plugin `claude -p` sessions spawning
  `speckit-pro:<name>`, proven from the transcript using the Layer 7
  transcript-parsing approach, with the per-model usage breakdown establishing
  the effective model. The canonical materializer rendering must be proven
  semantically equivalent to that dispatch
- Score bundle: versioned experiment, score, and decision records keyed by
  `execution_trace_id`
- Selection: deterministic hard gates, then quality and reliability floors and
  paired non-inferiority, then one predeclared price-weighted scalar over the
  raw token vector (input, cache-write by TTL class, cache-read, output) with
  coefficients content-addressed from one dated published price-sheet revision
  and labeled diagnostic-derived. The complete raw vector is always reported
- Slicing: three ordered slices per design concept Q14 — WP-A intact; corpus and
  blinded scoring; experiment policy, statistics and the calibration pilot
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Technical context, execution flow |
| `research.md` | ⏳ | Decision rationales |
| `data-model.md` | ⏳ | Entities and types |
| `contracts/` | ⏳ | Schemas for successor freeze, score bundle, experiment policy, scorer contracts |
| `quickstart.md` | ⏳ | Operator runbook for a budgeted local campaign |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates both spec AND plan together. Run multiple times for different domains.

**Best Practice:** Don't guess which domains to check. Analyze the spec first, then generate enriched prompts with spec-specific focus areas.

### Step 1: Analyze Spec for Recommended Domains

Signals present in this spec: JSON schemas and immutable evidence records
(**data-integrity**); real model dispatch, alias resolution, effort levels, token
accounting (**llm-integration**); statistical partitions, margins, multiplicity,
attrition (**research-rigor**). Error handling appears throughout as misdelivery
classification, rerun policy, and attrition, and is folded into the
data-integrity and research-rigor focus areas rather than run separately.

**Recommended domains: data-integrity, llm-integration, research-rigor.**

### Step 2: Run Enriched Checklist Prompts

#### 1. data-integrity Checklist

<!-- Why this domain: the spec adds several versioned schemas alongside frozen CAR-002 contracts, and its central risk is evidence that is mutated, duplicated, or silently invalidated. -->

```text
/speckit-checklist data-integrity

Focus on CAR-003 requirements:
- The CAR-002 capability snapshot, telemetry profile, and trace contract stay byte-immutable; new records conform to the existing contract rather than extending it
- The score bundle references trace records by ID with no duplicated source of truth for the same run
- Fixture and scorer version bumps invalidate exactly the affected candidate results, no more and no fewer
- The four refresh triggers invalidate the right scope of evidence, and an unresolved availability blocks that route's scored run
- The gitignore allow rule commits consolidated baselines while per-run outputs stay ignored
- Raw captures inherit CAR-002's sanitization contract; no raw model, CLI, prompt, or response bytes are committed
- Pay special attention to: whether any code path can write to, reinterpret, or shadow archived CAR-002 evidence
```

#### 2. llm-integration Checklist

<!-- Why this domain: exact treatment is WP-A's central claim, and the alias re-pointing gap CAR-002 left open is precisely an integration-boundary failure mode. -->

```text
/speckit-checklist llm-integration

Focus on CAR-003 requirements:
- Real installed-plugin dispatch spawns `speckit-pro:<name>` and the spawn is proven from the transcript, not assumed
- The per-model usage breakdown establishes the effective model, and the effective route is recorded rather than inferred from configuration
- Alias re-pointing is detected by comparing observed against resolved model ID, recorded as platform behavior, and never reported as plugin fallback
- The full ordered effort set `low` through `max` is probed per role-eligible model, including `high` as the documented search origin
- The environment contract freezes fast mode off, a pinned client range, a pinned parent-session model and effort, and proves `CLAUDE_CODE_SUBAGENT_MODEL` is unset
- The auth mode of every run is recorded, subscription auth is sufficient, and no path requires an API key
- Cache state is isolated between arms so one arm cannot warm another's cache
- Pay special attention to: whether the materializer rendering and real dispatch are proven equivalent, or merely asserted to be
```

#### 3. research-rigor Checklist

<!-- Why this domain: the statistical claims are what make a route qualification defensible, and most of the ways this spec can be wrong are silent. -->

```text
/speckit-checklist research-rigor

Focus on CAR-003 requirements:
- Screening, selection, cohort-lock and confirmation partitions are provably disjoint, and the confirmation set is consumed exactly once
- Calibration-only records are permanently ineligible for qualification and cannot leak into any outcome-bearing claim
- The analysis plan predeclares primary endpoint, practical margin, one-sided confidence rule, alpha and multiplicity, target power, clustering assumptions, sample sizes, racing adjustment, attrition thresholds, terminal policy, and `inconclusive => no qualification`
- Blind adjudication assigns exactly one of the five AC-2.20 causes with no score threshold predetermining the cause
- Only independently preclassified transient harness failure receives a capped complete-pair rerun; candidate-caused failures remain outcomes in the estimand
- The immutable production comparator is fully pinned, and the price-sheet revision is content-addressed at lock time
- Pay special attention to: any numeric threshold that could be set or changed after outcomes are observed
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| data-integrity | | | |
| llm-integration | | | |
| research-rigor | | | |
| **Total** | | | |

### Addressing Gaps

When checklist identifies `[Gap]` items:

1. Review the gap — is it a genuine missing requirement?
2. Update `spec.md` or `plan.md` to address it
3. Re-run the checklist to verify coverage
4. If the gap is intentionally out of scope, document why

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/car-003-evaluation-runner-scoring/tasks.md`

### Tasks Prompt

```text
/speckit-tasks

## Task Structure

- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: capability and treatment → corpus and scoring → policy and statistics
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story, not by technical layer

## Implementation Phases

Mirror the three ordered slices from design concept Q14. Do not reorder them —
slice 1 is roadmap Work Package A and the roadmap requires it stay intact.

1. Slice 1 / US1 — successor capability freeze and collector, refresh triggers,
   alias-re-pointing detection, canonical materializer in `speckit_pro_runner`,
   Layer 6 adapter, real-dispatch exact-treatment runner, cache isolation,
   misdelivery classification, execution-trace records, smoke-runner demotion
2. Slice 2 / US2 — twelve-role corpus, versioned fixture and scorer contracts,
   deterministic hard gates, blinded semantic rubric, two-ballot adjudication
   plus disagreement adjudicator, gitignore allow rule for consolidated baselines
3. Slice 3 / US3 — frozen `experiment_policy_id`, disjoint partitions, immutable
   production comparator, content-addressed price-weighted scalar, stage
   implementations for A1/A2/A3/B/C, campaign budgets, replayable statistics,
   calibration-only pilot, frozen analysis plan

## Constraints

- The canonical materializer is implemented once, under `speckit_pro_runner`
- Tests live under `tests/speckit-pro/`; fixtures under
  `tests/speckit-pro/layer6-efficiency/fixtures/<agent>/`
- No task may modify archived CAR-002 evidence or its schema
- The shared dual-platform smoke runner edit is one task, sequenced early, with
  an explicit note to sync `main` and coordinate with G56R-003
- Live-campaign tasks are operator-only and must not run in the default suite
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
**placeholder** until then — leave the cells blank during scoping.

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | | `true`, or `false` for a destructive-migration or concurrency-sensitive change. |
| **Signals** | | The decisive detector findings behind the route and releasability reading. |
| **Warnings** | | Any release-safety warning attached to the change. |

To produce the decision, run the classifier against the feature directory:

```text
runner helper atomicity-route specs/car-003-evaluation-runner-scoring
```

> **Scoping note:** design concept Q14 records a three-slice division driven by
> the reviewability gate's 25-total-file block threshold. If the classifier
> returns a route that contradicts that division, surface the conflict rather
> than silently overriding either — the roadmap independently requires Work
> Package A stay intact.

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```text
/speckit-analyze

Focus on:
1. Constitution alignment — Python 3.11+ stdlib only, no new Bash or jq, one materializer implementation, deterministic suite with zero live calls
2. Coverage gaps — every FR and user story has tasks; all three slices are represented
3. Consistency between task file paths and actual project structure, especially the split between `speckit_pro_runner` and `tests/speckit-pro/layer6-efficiency/`
4. Drift against `docs/ai/specs/.process/CAR-003-design-concept.md` — the design concept is the source of truth for every scoping decision. If a downstream artifact contradicts it, the downstream artifact is wrong unless there is an explicit revision note
5. Known roadmap supersessions that must NOT be reported as defects: the CAR-003 Key Files entry placing the materializer under `tests/` is superseded by design concept Q4, and the recorded `Production files: 0` reviewability budget no longer holds as a result
6. The AC-2.19 amendment recorded in design concept Q2 — subscription auth as the supported scored path is a deliberate, dated amendment, not spec-versus-PRD drift
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

1. Sync from `main` before starting slice 1 — the shared dual-platform smoke
   runner is also being edited on `g56r-003-evaluation-runner-scoring`
2. Verify the full suite passes before making changes:
   `python3 tests/speckit-pro/run-all.py`
3. Confirm you are on `car-003-evaluation-runner-scoring`, not `main`

### Implementation Notes

- Consult `docs/ai/specs/.process/CAR-003-design-concept.md` for the reasoning
  behind each decision; it informs test specifications and edge-case handling
- Any decision captured in the design concept but absent from tasks.md is a gap
  to surface before coding, not to silently drop
- The canonical materializer is shipped plugin source. Account for the generated
  artifact contract — payload, hashes, installed-cache proofs — before calling
  the work done, and verify with a plugin-shaped run using `speckit-pro/` alone
- Live probing and live campaigns are operator-only. Never add a live call to
  the default suite
- Sanitize every committed capture: home paths and session identifiers
  normalized, per CAR-002's sanitization contract
- Commit with conventional-commit scopes, e.g. `feat(car-003): ...`,
  `test(speckit-pro): ...`
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Slice 1 — capability and treatment | | | Roadmap Work Package A, kept intact |
| Slice 2 — corpus and blinded scoring | | | |
| Slice 3 — policy, statistics, pilot | | | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in tasks.md
- [ ] Tests pass: `python3 tests/speckit-pro/run-all.py` (Layers 1/4/5), zero live calls
- [ ] Generated artifact contract accounted for — payload, hashes, installed-cache proofs
- [ ] Plugin-shaped run verified with `speckit-pro/` alone
- [ ] Privacy scan clean — no absolute home paths, no raw session identifiers
- [ ] Reviewability gate re-run and the new production-file count recorded
- [ ] Merge coordination with `g56r-003-evaluation-runner-scoring` resolved
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

```text
speckit-pro/
├── speckit_pro_runner/          # Shipped plugin runner — canonical materializer lands here
│   ├── helpers/
│   └── gates/
├── agents/                      # The twelve named agent definitions
└── skills/

tests/speckit-pro/
├── layer6-efficiency/
│   ├── run-efficiency-benchmarks.py   # Shared dual-platform smoke runner (also edited by G56R-003)
│   ├── lib/                           # CAR-002 libraries + Layer 6 adapters
│   ├── contracts/
│   ├── fixtures/                      # Claude role corpus — two dirs today, twelve required
│   └── results/                       # Ignored except the consolidated-baseline allow rule
└── unit/

docs/ai/
├── research/                    # Canonical snapshots, telemetry profile, trace schema
└── specs/
    ├── claude-agent-routing-technical-roadmap.md
    └── .process/                # Workflow and design-concept exhaust

specs/car-003-evaluation-runner-scoring/   # Review-visible contract artifacts
└── SPEC-MOC.md
```

---

Template based on SpecKit best practices. Populated from the CAR-003 Grill Me interview on 2026-07-24.
