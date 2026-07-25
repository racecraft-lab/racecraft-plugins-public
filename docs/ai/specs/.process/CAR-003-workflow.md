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
| Q9 | Selection rule | **Superseded by the parity decision below** — raw-vector Pareto dominance, not a price-weighted scalar |
| Q10 | CI boundary | Explicit local budgeted campaigns; CI runs deterministic replay only, zero live calls |
| Q11 | Stage ownership | CAR-003 implements the stages; CAR-007 through CAR-010 run outcome-bearing campaigns |
| Q12 | Pilot validity | Calibration-only partition; records explicitly ineligible for qualification |
| Q13 | Analysis plan | Freeze margins, sample sizes, power, multiplicity, attrition after calibration |
| Q14 | Reviewability | Three ordered slices; WP-A stays intact as slice 1 |

### Parity alignment with G56R-003

CAR-003 and G56R-003 must be **logically the same**, diverging only where a
platform genuinely documents a different surface. G56R-003 is further along
(through Plan, with committed contract schemas), so its `spec.md` is the
reference shape. The following were aligned to it after the interview:

| Aligned item | G56R reference |
|---|---|
| Four user stories: successor freeze, exact treatment, corpus scoring, analysis plan | US1–US4 |
| Four Clarify sessions, including a dedicated materialization/delivery/trace-join session | Clarifications S1–S4 |
| Checklist domains: data-integrity, error-handling, llm-integration, performance | committed `checklists/` |
| Explicit score-eligibility predicate gating every scored outcome | FR-030 |
| Separate closed failure taxonomies per plane, incl. unclassifiable attrition | FR-029, FR-034 |
| Byte-identical / content-hash materialization proof, not parsed or semantic equivalence | FR-006, FR-008 |
| Deny-by-default sanitization allowlist that fails closed and blocks publication | FR-027, FR-036 |
| Non-executable role contracts retained but never run until a route is admitted | FR-011, FR-012 |
| Selection rule: absolute floors → paired non-inferiority → raw-vector Pareto dominance, no forced weighted ranking | FR-018, FR-019 |

**Known platform-surface differences (values, not logic):** the raw token vector
categories differ (CAR carries cache-write by TTL class and cache-read; Codex
carries cached-input tokens), and CAR carries the AC-2.19 auth amendment because
only the Claude PRD constrains the scored-run auth environment. Both sides record
the auth mode of every run and produce no plan-based claim.

**Selection rule — RESOLVED 2026-07-24 in favour of Pareto.** CAR-003 adopts
raw-vector **Pareto dominance**, matching G56R-003 FR-018/FR-019. Absolute
quality and reliability floors run first, then task-paired cluster-adjusted
non-inferiority, then Pareto comparison over the complete raw vector. A failed
gate, tie, mixed dominance, incomplete evidence, or statistical uncertainty is
inconclusive and yields no qualification; **no weighted ranking is forced**.
Published price data may be cited as diagnostic context only, never as a
selection coefficient.

This required amending two Claude-side documents, both carried on this branch:

| Document | Change |
|---|---|
| `docs/prd-claude-agent-routing.md` AC-2.5 | Price-weighted scalar → Pareto rule, with a dated inline amendment note preserving the superseded wording and its rationale |
| `docs/ai/specs/claude-agent-routing-technical-roadmap.md` qualification rule | Same substitution, cross-referencing PRD AC-2.5 |

The raw-vector reporting obligation is unchanged; only the rule that ranks
passing candidates changed. Design concept Q9 is superseded and annotated as
such — the Q&A log records what was asked and answered at scoping time and is
not rewritten.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | G1 PASS — 43 FR, 4 US, SC-001…019, 0 markers; Pareto + auth amendment verified |
| Clarify | `/speckit-clarify` | 🔄 In Progress | 4 sessions, resolution after each |
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

**Constitution Check:** ✅ PASS — baseline recorded 2026-07-24 before Phase 1.
`python3 tests/speckit-pro/run-all.py` → **3251/3251 passed** (L1 1428, L4 1637,
L5 186; toolchain preflight ok, gate not counted), exit 0, zero failures. This is
the green starting point; any later suite failure is attributable to CAR-003
changes.

### Autopilot Pre-flight Evidence (Step -1 / Step 0)

| Item | Result |
|------|--------|
| `check-prerequisites` | `all_pass: true` with the workflow file supplied. `is_worktree: true`; `branch: ""` and `on_feature_branch: false` are the known non-numeric-branch limitation, not a failure |
| Branch handling | `.specify/feature.json` created → `{"feature_directory":"specs/car-003-evaluation-runner-scoring"}`. Gitignored (`.gitignore:11`), so it never reaches the diff. Matches the committed G56R-003 precedent. Branch NOT renamed and the numeric regex NOT faked |
| `before_specify` hook | Mandatory `git.feature` hook neutralized for dispatch — already on the feature branch; creating a second one would be wrong |
| `detect-commands` | stack `unknown`; BUILD/TYPECHECK/LINT do not exist. UNIT_TEST = FULL_VERIFY = `python3 tests/speckit-pro/run-all.py` |
| `detect-presets` | `speckit-pro-reviewability` v1.0.0; spec/plan/tasks templates resolve as top layer; 18 hook events |
| `resolve-confidence-mode` | `advisory` → `CONFIDENCE_GATE_MODE=advisory` for G6.5 |
| `PROJECT_IMPLEMENTATION_AGENT` | fallback `speckit-pro:phase-executor` (the two project agents are auditors, not implementers) |
| `AGENT_TEAMS_AVAILABLE` | `false` — no `TeamCreate` surface. Parallel runs use batched background subagents in one message |
| Archive Sweep | Ran discovery-only, current target excluded. **0 candidates, 0 mutations.** `origin/main:specs` holds only `.gitkeep`; all prior specs already archived with provenance (`f07bcb0f`, `f93bef1a`). No cleanup applied — it would have broken the three-slice reviewability budget |
| Shared-runner merge risk | Branch is level with `origin/main` (0 behind). **Neither `main` nor `g56r-003-evaluation-runner-scoring` has yet modified `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py`** (still 495 lines). G56R-003 is only through Checklist, so the conflict is latent — CAR-003 can land its demotion edit first. Re-check before slice 1 |
| Orchestrator effort | Run executed at `xhigh` (ultracode), below the skill's mandated `max`. Operator reaffirmed after the gate was raised; recorded as a deliberate deviation |

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

Mirrors the G56R-003 SC set one-for-one so both platforms are measured the same way.

- [ ] **SC-001** 100% of CAR-002 artifact paths and IDs remain unchanged after CAR-003 artifacts are generated
- [ ] **SC-002** The successor freeze contains at least one admitted tuple, and every admitted tuple carries both official-source and pinned-runtime support evidence
- [ ] **SC-003** 100% of excluded candidate tuples include a machine-checkable exclusion reason from the closed taxonomy
- [ ] **SC-004** 100% of accepted score bundles reference a pre-score immutable treatment record with content-hash-identical materialization or installed-policy proof, configured-route proof, complete mandatory observations, authoritative route-change monitoring, `treatment_disposition=proven`, and no disqualifying re-point or treatment failure
- [ ] **SC-005** The fixture corpus contains exactly twelve valid role contracts: the eleven required core roles plus `autopilot-fast-helper`, reported separately from required-core statistics
- [ ] **SC-006** 100% of semantic score outcomes include two distinct independently executed candidate-blind ballots bound to one frozen rubric, and 100% of decision-affecting disagreements include a frozen third adjudicator record
- [ ] **SC-007** 100% of decision bundles apply semantic and reliability floors before paired cluster-adjusted non-inferiority, and non-inferiority before the resource comparison
- [ ] **SC-008** 100% of inconclusive or incomplete evidence paths produce no qualification
- [ ] **SC-009** 100% of candidate-caused failures, timeouts, cancellations, budget exhaustion events, and abandoned work are included in the estimand with acceptance zero
- [ ] **SC-010** 100% of approved transient harness reruns are complete-pair reruns under a documented cap, with zero one-arm reruns or complete-case substitutions
- [ ] **SC-011** Deterministic replay reconstructs the same terminal decisions from frozen experiment, score, analysis, and decision bundles on a clean checkout
- [ ] **SC-012** The numeric analysis plan is frozen before any CAR-007 through CAR-010 outcome-bearing cohort evidence is observed
- [ ] **SC-013** The planning reviewability gate records three ordered review slices and maps each slice to requirements, files, and verification evidence
- [ ] **SC-014** Every shipped runner source change has synchronized generated payloads, hashes, and installed-cache proofs before the phase is complete
- [ ] **SC-015** 100% of committed capability snapshots and replay fixtures pass deny-by-default sensitive-field inspection and contain only allowlisted sanitized boundary evidence
- [ ] **SC-016** 100% of empty, malformed, stale, untrusted, unsanitized, identity-mismatched, or digest-mismatched successor collections block authoritative freeze publication
- [ ] **SC-017** *(CAR-specific)* CAP-Q6 is closed: alias re-pointing is detected from observed-versus-resolved model ID, recorded as platform behavior, and never reported as SpecKit Pro fallback
- [ ] **SC-018** *(CAR-specific)* The full ordered effort set `low` through `max` is probed per role-eligible model, including `high` as the documented search origin
- [ ] **SC-019** Full default suite green with zero live calls; payload boundary clean

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/car-003-evaluation-runner-scoring/spec.md`

### Specify Prompt

```text
/speckit-specify Build the reusable, qualification-capable evaluation platform for Claude Code agent route selection: a successor runtime capability freeze, a canonical shipped materializer with proven content-hash exact-treatment equivalence, a governed twelve-role corpus with blinded scoring, a frozen experiment policy whose selection rule is raw-vector Pareto dominance after absolute floors and paired non-inferiority, and a calibration-only live pilot — without emitting any final route policy.
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

Use exactly these four, mirroring G56R-003's US1 through US4 so the two
platforms decompose identically. They map onto the three review slices as
US1+US2 → slice 1 (roadmap Work Package A, kept intact), US3 → slice 2,
US4 → slice 3.

[US1] Publish successor capability freeze (P1) — collect the pinned-runtime
catalog, canonicalize ordinary effort values through an explicit evidence-backed
map, admit only tuples present in both the official-source candidate ledger and
the pinned runtime, probe the full ordered effort set `low` through `max`
including `high` as the documented search origin, close CAP-Q6 with an
alias-re-pointing detection rule, and define versioned refresh triggers. Publish
additively; never mutate or reuse archived CAR-002 evidence. An empty, malformed,
stale, untrusted, unsanitized, or digest-mismatched collection records diagnostic
evidence and blocks authoritative publication.

[US2] Prove exact treatment before scoring (P1) — one shipped materializer in
`speckit_pro_runner` owning the exact rendered destination bytes and
instruction/configuration digests; real installed-plugin `speckit-pro:<name>`
dispatch proven from the transcript; cache isolation between arms; an explicit
score-eligibility predicate that admits an outcome only on `treatment_disposition
=proven` with content-hash-identical materialization or installed-policy proof,
configured-route proof, complete mandatory telemetry-profile observations, and
complete route-change monitoring. Every assigned attempt emits an immutable trace
regardless of score eligibility; platform-re-pointed attempts stay immutable but
non-scorable for the requested route, and different-agent, ambiguous, unapproved,
or unidentifiable delivery is a hard treatment failure that never scores the
observed destination.

[US3] Score governed twelve-role corpus (P2) — eleven required core roles plus
`autopilot-fast-helper` analyzed separately from required-core primary
statistics. Run only roles with admitted executable routes; retain contracts for
roles without a shipped agent definition and never run them until a route is
admitted. Each versioned fixture binds role/source digest, objective, evidence
partition, permitted tools and mutation contract, expected artifacts, acceptance
oracle, fixture digest, and independent validity review. Deterministic hard gates
run before semantic evaluation and fail closed on missing gate evidence; semantic
scoring requires two distinct candidate-blind scorer identities on one frozen
rubric plus a frozen third adjudicator for every decision-affecting disagreement.

[US4] Freeze calibration analysis plan (P3) — registry-bound `partition_id` with
closed partition types (`calibration`, `screening`, `selection`, `cohort_lock`,
`integrated_confirmation`); calibration is always `qualification_eligible=false`
and cross-partition reuse fails closed. Each pair immutably binds its comparison
set, routes, role, fixture, task, hashes, capability freeze, route resolution,
experiment policy, and analysis plan before execution; later refreshes create
additive invalidations and never rebind. One versioned plan freezes margins,
sample sizes, power, alpha, multiplicity, racing and futility rules, attrition
caps, campaign budgets, and terminal rules after the calibration-only pilot and
before any CAR-007 through CAR-010 outcome is observed.

### Closed taxonomies (required)

Keep these failure planes in **separate closed taxonomies**; a failure in one
plane must never be recorded as a failure in another:

- **Capability exclusion** — why a candidate tuple was not admitted to the freeze
- **Snapshot / publication authority** — why an authoritative freeze could not be published
- **Treatment and scoring** — score disposition, failure plane, failure code, and
  invalidation reason. The failure-code taxonomy must distinguish at minimum:
  treatment misdelivery, platform route change, missing mandatory telemetry,
  invalid or stale fixture, invalid or stale scorer, missing or non-blind ballot,
  unresolved adjudication disagreement, invalid or stale adjudicator, candidate
  terminal outcome, infrastructure failure, evidence-boundary violation,
  partition violation, schema violation, and **unclassifiable attrition**

Unknown or unclassifiable attrition is never treated as candidate-caused,
transient, or complete-case evidence — it is an evidence-boundary failure that
blocks completeness and returns inconclusive unless resolved before terminal
analysis.

### Constraints

- Python 3.11+ standard library only; no new Bash or `jq` dependency
- The canonical materializer ships in `speckit_pro_runner`; Layer 6 keeps only a
  thin adapter, and there is exactly one materializer implementation. It owns the
  exact rendered destination bytes and the instruction/configuration digests
  consumed by both Layer 6 evidence and CAR-006 resolver behavior — no
  parsed-only or divergent evaluation materializer
- Equivalence is proven by **content-hash identity** over the shipped
  frontmatter-plus-body, matching the roadmap's own definition of
  `resolved_agent_policy_id` as an "exact shipped frontmatter-plus-body content
  hash." Parsed-field equivalence or source-template equality does not prove
  installed-policy equivalence
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
- Committed evidence is a **deny-by-default allowlist that fails closed**. Git may
  contain only sanitized client identity, opaque account or environment boundary
  IDs, collection metadata, digests and content-addressed references, tuple
  decisions, invalidation criteria, schemas, manifests, deterministic fixtures,
  opaque scorer identities, rubric/scorer/adjudicator digests, anonymized ballots,
  score bundles, and evidence references. Raw captures, prompts, responses,
  transcripts, account identifiers, authentication material, credentials,
  headers, cookies, private hostnames, absolute paths, repository remotes, and
  plan or billing identifiers stay operator-only. Any non-allowlisted field
  **blocks publication** rather than being silently stripped
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

Completed 2026-07-24. **G1: PASS** (`validate-gate` → `pass: true`, `markers: 0`,
"spec.md exists with 0 markers").

| Metric | Value |
|--------|-------|
| Functional Requirements | 43 (FR-001 … FR-043) |
| User Stories | 4 — US1 P1 successor freeze, US2 P1 exact treatment, US3 P2 corpus scoring, US4 P3 analysis plan |
| Acceptance Criteria | SC-001 … SC-019 carried from the Success Criteria Summary |
| `[NEEDS CLARIFICATION]` markers | 0 |

**Parity verification against G56R-003 (orchestrator-verified, not self-reported):**

| Item | Result |
|------|--------|
| Selection rule | ✅ FR-018 floors → task-paired cluster-adjusted non-inferiority → raw-vector Pareto dominance. FR-019 "MUST return no qualification for a failed gate, tie, mixed dominance, incomplete evidence, or statistical uncertainty and MUST NOT force a weighted ranking." Price data diagnostic-only, never a selection coefficient or scalar weight |
| Decision-bundle shape | ✅ "carries no per-category weights, price coefficients, or scalar score field" — mirrors G56R `analysis-decision.schema.json` rather than inventing a Claude-only schema |
| Auth amendment | ✅ FR-042 — subscription auth is the supported scored path; API-key auth MUST NOT be required on any supported path; auth mode recorded per run; no plan/billing claim; explicitly flagged as a dated AC-2.19 amendment so Analyze does not read it as drift |
| Score-eligibility predicate | ✅ FR-030 |
| Closed taxonomies | ✅ FR-029 tuple exclusions; publication authority recorded separately; treatment/telemetry/fixture/scorer/adjudication in their own bundles |
| Deny-by-default allowlist | ✅ FR-027 / FR-028, fail-closed publication |
| Three ordered slices, WP-A intact | ✅ FR-025 |
| FR count | 43 vs G56R's 38 — the delta is CAR-specific surface (SC-017 CAP-Q6 closure, SC-018 full effort ladder, FR-042 auth amendment), not divergent logic |

**Privacy scan:** clean — no `/Users` or `/home` absolute paths, no session UUIDs,
no unresolved `{{TOKEN}}` placeholders.

⚠️ **Carry into Plan:** the spec's projected **total files is 18–26**. The upper
bound touches the reviewability gate's 25-total-file block threshold. The
three-slice split already absorbs this, but the Plan phase must re-derive the
real figure rather than trusting the range.

### Files Generated

- [x] `specs/car-003-evaluation-runner-scoring/spec.md` (43 FRs, 4 US, SC-001…SC-019)
- [x] `specs/car-003-evaluation-runner-scoring/checklists/requirements.md` — standard `/speckit-specify` spec-quality artifact (G56R-003 carries the same file); not a Phase 4 domain checklist

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

Four sessions, matching G56R-003's four Clarify sessions one-for-one.

#### Session 1: Successor freeze and invalidation

```text
/speckit-clarify Focus on the successor capability freeze: which runtime surface is the sole authority for freeze admission and which observations are diagnostic-only; how source-admitted ordinary effort values are canonicalized through an evidence-backed map before intersection with the pinned runtime; what exactly constitutes an alias re-pointing event versus a SpecKit Pro fallback and which observable fields the detection rule reads; what each of the four refresh triggers invalidates and what survives; what an empty or invalid intersection publishes; and the closed taxonomy separating tuple-local capability exclusions from snapshot-publication authority failures.
```

#### Session 2: Materialization, delivery, and trace joins

```text
/speckit-clarify Focus on treatment: the exact score-eligibility predicate that admits an outcome; what content-hash-identical materialization proves that parsed-field equivalence does not; which mandatory telemetry-profile observations must be present and where explicit nulls remain permitted; how platform route change (immutable but non-scorable) is distinguished from different-agent, ambiguous, unapproved, or unidentifiable delivery (hard treatment failure); and how score and decision bundles reference immutable trace IDs and digests without embedding or mutating traces.
```

#### Session 3: Corpus and blinded scoring

```text
/speckit-clarify Focus on the corpus and scorers: which of the twelve roles are currently executable versus contract-only, and how a contract-only role is retained without being run; what each versioned fixture must bind before any candidate scores against it; the boundary between deterministic hard gates and the semantic rubric; what the two blinded ballots and the disagreement adjudicator retain for replay and how blinding is enforced; how fixture, scorer, rubric, or adjudicator version changes invalidate affected bundles additively; and the closed score disposition, failure-plane, failure-code, and invalidation-reason fields including unclassifiable attrition.
```

#### Session 4: Partitions, statistics, and campaign controls

```text
/speckit-clarify Focus on experiment policy: how the closed partition types stay provably disjoint and how cross-partition reuse fails closed; exactly which fields each comparison pair immutably binds before execution and why refreshes must be additive rather than rebinding; the decision sequence from absolute floors through task-paired cluster-adjusted non-inferiority to the resource comparison, and what makes a result inconclusive; the assigned-attempt estimand and the capped complete-pair rerun rule; and which campaign budget and terminal-policy fields freeze after calibration and before any cohort outcome.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Successor freeze and invalidation | 5 asked, 3 applied directly, 2 to consensus | FR-003 effort map bounded to the closed ladder; FR-041 invalidates/survives mapping stated; **FR-044 new** (empty intersection publishes nothing and never promotes archived CAR-002 tuples); FR-002/FR-004 sole-admitting-authority; **FR-045, FR-046 new** (bounded attribution in an additive record; detector validated by synthetic replay) |

### Consensus Resolution Log

| Session | Item | Tags | Round | Analysts | Agreement | Resolution |
|---------|------|------|-------|----------|-----------|------------|
| 1 | Q1 — sole admitting runtime surface | `[codebase, domain]` | 1 | codebase-analyst, domain-researcher | **N=2, both agree** — no Round 2 | Print-mode canary probe is the sole admitting authority; all other surfaces diagnostic-only. Decisive evidence: the CAR-002 capability library already encodes the catalog endpoint as "corroborating (never alias-establishing)" and returns evidence only under `api_key` mode — so admitting on it would make freeze admission depend on an auth mode FR-042 forbids requiring. Domain research added the binding refinement that probe-vs-diagnostic disagreement must trigger investigate-or-exclude, else the design collapses into mono-operation bias. Applied to FR-002 / FR-004 |
| 1 | Q2 — alias re-point vs resolver fallback | `[domain, ambiguous]` | 1 (full fan-out; `[ambiguous]` never single-routes) | codebase-analyst, spec-context-analyst, domain-researcher | **N=3, converged** on "classification already settled, detection mechanics incomplete" | spec-context (high): the roadmap already fixes the category boundary; only mechanics were open; parity with G56R-003 holds and the `alias_repoint_unresolved` vs `hidden_state_disagreement` difference is a pre-decided value divergence. codebase (low, but concrete): no ordered-fallback resolver exists in shipped source (deferred to CAR-006); frozen `record_class` is closed so attribution needs an additive record; `resolved_dated_model_id` is ambiguous across freeze-time and run-time records; `client_version` is a missing fifth observable. domain (high): the four-observable elimination argument is not closed-world safe — documented serving-infrastructure change alters behavior without changing model identity — and the catch-22 resolves via synthetic replay below the live trigger. Applied to FR-039 / FR-045 / FR-046 |

| 2 | Q1 — does `scorable` bind the predicate; what is `treatment_disposition` | `[spec, codebase]` | 1 | codebase-analyst, spec-context-analyst | **N=2, both agree, both high** | Both **rejected the executor's proposed enum**. `treatment_disposition` already ships closed as `proven`/`unknown`/`non_scorable_rerouted`/`hard_fail` in the shared treatment-record contract, and that file is **byte-identical across both worktrees** (`diff` empty). Adopting the executor's four invented names would have created a third unbridged vocabulary and manufactured divergence. `scorable` is keyed purely off record class via a fixed pairing table, so it cannot certify materialization or route proof — necessary, never sufficient. Applied to FR-030 |
| 2 | Q4 — ordering of co-occurring disqualifiers | `[spec]` | **1 → 2** (Round 1 returned low confidence) | R1 spec-context; R2 codebase-analyst, domain-researcher | **N=3, converged; executor's proposal rejected on both counts** | R1 (low on order, high on recording): reject "record first match, discard rest" — the project pattern is a scalar terminal cause plus complete provenance. R2 codebase (**high, dispositive**): shipped shared code has **no condition-level precedence at all** — conditions are derived independently and merged by set union into a real `disposition_reasons` array; the only ordering is a disposition-*bucket* chain `hard_fail` > `non_scorable_rerouted` > `unknown` > `proven`. All three lib files plus the schema are byte-identical across both worktrees, so documenting this creates **zero** divergence. R2 domain (low-med): the correct genre is a specified, evidence-preserving precedence, and cross-implementation determinism requires the order be fixed in-spec rather than left to each implementation; one terminal cause plus retained contributing causes matches established incident-classification practice. Applied to FR-031 + a new Edge Case |

**Why Round 2 fired on Session 2 Q4:** `[spec]` routes to a single analyst, and
that analyst returned `confidence: low` on the core question, which the
single-analyst rule escalates. Escalating was correct — Round 1 had read only
specs and the PRD, and the shipped code turned out to contradict the proposed
answer. Had we shipped Round 1's recommendation, the spec would have mandated a
condition-level ordering that does not exist in the code both platforms already
share.

**Why no Round 2 on Session 1 Q2 despite a low-confidence analyst:** `[ambiguous]` routes to
all three in Round 1, so the item already had full fan-out. The codebase
analyst's low confidence was scoped to *completeness of the observable set* —
precisely the point the domain researcher independently confirmed was
incomplete. The three answers are complementary rather than contradictory, and
all three findings were folded into the resolution instead of being averaged
away.
| 2 | Materialization, delivery, and trace joins | 5 asked, 3 applied directly, 2 to consensus (1 escalated to Round 2) | FR-008 digest preimage pinned to on-disk bytes; **FR-009 mandatory-observation manifest** (the inherited profile never enumerated them, leaving the requirement undecidable); FR-032 trace-digest verification; FR-030 binds the **already-shipped** disposition enum instead of inventing one; FR-031 co-occurrence precedence + union recording |
| 3 | Corpus and blinded scoring | | |
| 4 | Partitions, statistics, and campaign controls | | |

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
- Exact treatment: prove equivalence by content-hash identity over the shipped
  frontmatter-plus-body, not parsed-field comparison. The materializer owns the
  rendered bytes and the instruction/configuration digests
- Selection: deterministic hard gates, then absolute quality and reliability
  floors, then task-paired cluster-adjusted non-inferiority, then **Pareto
  dominance** over the raw token vector (input, cache-write by TTL class,
  cache-read, output) plus duration, retries, and compaction. A failed gate,
  tie, mixed dominance, incomplete evidence, or statistical uncertainty returns
  no qualification, and no weighted ranking is forced. The complete raw vector,
  duration, retries, and compaction are always reported. Published price data is
  diagnostic context only, never a selection coefficient
- The decision-bundle contract must express Pareto dominance and an explicit
  inconclusive terminal state. It must **not** carry per-category weights, price
  coefficients, or a scalar score field — mirror G56R-003's
  `contracts/analysis-decision.schema.json` shape rather than inventing a
  Claude-only decision schema
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
(**data-integrity**); closed failure taxonomies, misdelivery classification,
rerun policy, attrition, and fail-closed publication (**error-handling**); real
model dispatch, alias resolution, effort levels, and token accounting
(**llm-integration**).

Plus p95 resource and duration guardrails, campaign budgets, wall-time and
raw-token caps, racing and futility rules, the powered long-horizon stratum, and
cache isolation between arms (**performance**).

**Domains: data-integrity, error-handling, llm-integration, performance** — the
same four G56R-003 ran in its completed Checklist phase, so both platforms are
validated against identical lenses. Statistical-rigor concerns are carried inside
the error-handling and data-integrity focus areas rather than run as a separate
domain, matching G56R.

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

#### 3. error-handling Checklist

<!-- Why this domain: this spec's correctness lives in its failure paths — closed taxonomies, fail-closed publication, attrition, and the rules that decide when to return no qualification rather than a number. -->

```text
/speckit-checklist error-handling

Focus on CAR-003 requirements:
- Capability exclusion, snapshot-publication authority, and treatment/scoring failures use separate closed taxonomies, and a failure in one plane is never recorded in another
- The score failure-code taxonomy distinguishes treatment misdelivery, platform route change, missing mandatory telemetry, invalid or stale fixture, invalid or stale scorer, missing or non-blind ballot, unresolved adjudication disagreement, invalid or stale adjudicator, candidate terminal outcome, infrastructure failure, evidence-boundary violation, partition violation, schema violation, and unclassifiable attrition
- Unknown or unclassifiable attrition is an evidence-boundary failure that returns inconclusive, never candidate-caused, transient, or complete-case evidence
- Only independently preclassified transient harness failure receives a capped complete-pair rerun; one-arm reruns are impossible by construction
- A failed gate, tie, incomplete evidence, or statistical uncertainty returns no qualification rather than a forced ranking
- Publication fails closed on empty, malformed, stale, untrusted, unsanitized, identity-mismatched, or digest-mismatched collections, and on any non-allowlisted committed field
- Pay special attention to: any path where a failure could be silently absorbed, reclassified into a different plane, or scored against the observed rather than the requested route
```

#### 4. performance Checklist

<!-- Why this domain: campaign budgets, p95 guardrails, and cache isolation are the constraints that keep a long-running evaluation both affordable and statistically valid; G56R-003 ran this domain in its completed Checklist phase. -->

```text
/speckit-checklist performance

Focus on CAR-003 requirements:
- Campaign budgets freeze maximum raw-token use, wall time, candidate count, futility rules, racing method, and confirmation-entry cap before any outcome-bearing run
- The guardrail registry defines p95 resource and p95 duration guardrails with unit, denominator, comparator, margin, confidence method, missing-data rule, multiplicity position, and minimum unique-task count
- Cache state is isolated between arms so one arm cannot warm another's cache; billed cache writes make crossover directly distortive
- The powered long-horizon stratum derives membership from task and protocol characteristics before either arm runs, never from realized duration, turns, tokens, retries, or compactions
- Late-failure, retry, and compaction guardrails are defined alongside the resource and duration ones
- The deterministic replay suite stays fast enough to run in default CI with zero live calls
- Pay special attention to: any budget or guardrail threshold that could be set or relaxed after outcomes are observed
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| data-integrity | | | |
| error-handling | | | |
| llm-integration | | | |
| performance | | | |
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

1. Slice 1 / US1 + US2 — successor capability freeze and collector, effort
   normalization map, alias-re-pointing detection and refresh triggers,
   fail-closed publication gate, canonical materializer in `speckit_pro_runner`
   with content-hash equality proof, Layer 6 adapter, real-dispatch
   exact-treatment runner, cache isolation, score-eligibility predicate,
   route-change versus misdelivery classification, immutable execution-trace
   records, smoke-runner demotion. This is roadmap Work Package A, kept intact
2. Slice 2 / US3 — twelve-role corpus with contract-only roles retained but not
   run, versioned fixture and scorer contracts, deterministic hard gates,
   blinded semantic rubric, two-ballot adjudication plus disagreement
   adjudicator, closed score disposition and failure-code taxonomy, gitignore
   allow rule for consolidated baselines
3. Slice 3 / US4 — frozen `experiment_policy_id`, registry-bound closed
   partitions, immutable pair binding, immutable production comparator, the
   Pareto selection rule with an explicit inconclusive terminal state, stage
   implementations for A1/A2/A3/B/C, campaign budgets, replayable statistics,
   calibration-only pilot, frozen analysis plan, generated-artifact refresh

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
| Slice 1 — US1 + US2 capability freeze and materialized treatment trace | | | Roadmap Work Package A, kept intact |
| Slice 2 — US3 governed corpus, hard gates, blinded scoring | | | |
| Slice 3 — US4 calibration analysis plan and replayable decision bundles | | | |

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
