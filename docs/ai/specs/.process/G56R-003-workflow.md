# SpecKit Workflow: G56R-003 - Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

**Template Version**: 1.0.0
**Created**: 2026-07-24
**Purpose**: Build and validate the exact-treatment Codex qualification
platform, including an authoritative successor capability freeze, without
emitting final per-agent route policies or consuming outcome-bearing cohort
evidence.

---

## How to Use This Workflow

Start a new Codex task rooted at the dedicated worktree, then run:

```text
$speckit-autopilot docs/ai/specs/.process/G56R-003-workflow.md
```

This workflow is fully populated for G56R-003. Do not run it from the parent
`main` checkout. Do not start outcome-bearing cohort campaigns or final route
policy work in this spec.

---

## Design Concept

The required Grill Me interview is recorded at:

```text
docs/ai/specs/.process/G56R-003-design-concept.md
```

Its accepted decisions are binding inputs to every phase:

- Preserve the archived G56R-002 zero-eligible freeze and add an authoritative,
  non-empty successor freeze from the pinned live Codex catalog.
- Keep the existing bare `codex exec` benchmark as non-release smoke evidence;
  add a separately named exact-treatment qualification runner.
- Store scores and decisions in versioned G56R-003 bundles keyed to new
  immutable G56R-003 `execution_trace_id` records that conform to the G56R-002
  trace contract.
- Use deterministic hard gates followed by two independent candidate-blind
  semantic ballots and a third blinded adjudicator on disagreement.
- Put the single canonical Python materializer in the shipped
  `speckit_pro_runner` package for direct G56R-006 reuse.
- Govern one twelve-role corpus—eleven required core role contracts plus
  `autopilot-fast-helper`—execute only admitted routes, and analyze the helper
  separately from required-core primary statistics.
- Require quality and reliability floors plus paired non-inferiority before a
  Pareto comparison of the raw resource vector. Ties remain inconclusive.
- Run live campaigns only through explicit budgeted developer commands. CI
  verifies deterministic replay and contracts.
- Permit only capped complete-pair reruns for independently preclassified
  transient harness failures.
- Let G56R-007 through G56R-010 own final outcome-bearing per-agent campaigns
  and route policies.
- Refresh immutable capability snapshots only on declared client, account,
  catalog, or source-ledger invalidation triggers.
- Deliver three ordered review slices.
- Use a disposable calibration-only pilot, then freeze one versioned analysis
  plan before any cohort outcome is observed.

Grill Me is human-in-the-loop only. Once autopilot begins, clarifications use
`$speckit-clarify` and the consensus protocol, never Grill Me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|---|---|---|---|
| Specify | `$speckit-specify` | Complete | 26 testable requirements, 4 user stories, 14 success criteria; G1 passed with zero clarification markers |
| Clarify | `$speckit-clarify` | Complete | Four sessions resolved authority, treatment, scoring, partition, statistical, and evidence contracts; G2 passed with zero markers |
| Plan | `$speckit-plan` | Complete | Three ordered slices, six contract families, explicit ownership and generated boundaries; G3 passed |
| Checklist | `$speckit-checklist` | Complete | All 141 checks pass; 6 gaps across Error Handling and Performance were remediated; G4 passed |
| Tasks | `$speckit-tasks` | Complete | Repaired to 25 self-contained TDD tasks, 3 conflict-safe fixture groups, all 38 requirements mapped; G5 rerun passed |
| Analyze | `$speckit-analyze` | Complete | Task-contract rerun passed with zero findings; G6 rerun passed |
| Confidence Gate | G6.5 | Complete | Task-repair rerun passed at 0.99 against the 0.90 advisory threshold |
| Implement | `$speckit-implement` | Complete | All 25 tasks complete; Slice 3 G7 passed with 25/25 tasks and zero markers |
| Post | Post-Implementation | In Progress | PR #386 is open; three late GitHub Code Quality findings are being remediated against the current head |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|---|---|---|
| G1 | After Specify | Requirements are testable; no unresolved markers; final cohort qualification is explicitly out of scope |
| G2 | After Clarify | Snapshot authority, treatment proof, score bundles, adjudication, partitioning, and null behavior are unambiguous |
| G3 | After Plan | Three slices are reviewable, source/generated boundaries are explicit, and G56R-006 reuse is proven by design |
| G4 | After Checklist | Every true gap is remediated or explicitly recorded as out of scope |
| G5 | After Tasks | Every requirement maps to ordered TDD tasks and each slice has independent verification |
| G6 | After Analyze | No critical or high inconsistency, evidence leak, authority drift, or roadmap-boundary conflict remains |
| G6.5 | Before Implement | Record and evaluate pre-implementation confidence in the preflight-resolved advisory mode |
| G7 | After Each Implementation Slice | Focused tests, replay, diff hygiene, reviewability, and applicable generated-artifact checks pass |

---

## Prerequisites

### Worktree and Branch

- Worktree: `.worktrees/g56r-003-evaluation-runner-scoring`
- Branch: `g56r-003-evaluation-runner-scoring`
- Feature directory: `specs/g56r-003-evaluation-runner-scoring`
- Contract marker:
  `specs/g56r-003-evaluation-runner-scoring/SPEC-MOC.md`
- Design concept:
  `docs/ai/specs/.process/G56R-003-design-concept.md`
- Workflow: `docs/ai/specs/.process/G56R-003-workflow.md`
- Technical roadmap:
  `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`

The branch must track `origin/g56r-003-evaluation-runner-scoring` before
autopilot begins. Spec, plan, and task templates must continue resolving to
the `speckit-pro-reviewability v1.0.0` preset unless a deliberate
repository-specific override is documented.

### Grounded Source Truth

- Product requirement: `docs/prd-codex-gpt-5-6-agent-routing.md`, specifically
  AC-2.1, AC-2.6 through AC-2.16, AC-2.20, and G56R-003's shared contributions
  to AC-2.19 and AC-2.21. Consume AC-2.2 through AC-2.5 as upstream G56R-002
  contracts; AC-2.17 and AC-2.18 belong to G56R-004 and G56R-010.
- Technical roadmap:
  `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`, especially
  the G56R-003 and G56R-007 through G56R-010 sections.
- Design decisions:
  `docs/ai/specs/.process/G56R-003-design-concept.md`.
- G56R-001 candidate report:
  `docs/ai/research/codex-agent-route-candidates.md`.
- G56R-001 candidate manifest:
  `docs/ai/research/codex-agent-route-candidate-manifest.json`.
- G56R-002 canonical capability evidence:
  `docs/ai/research/codex-g56r-002-capability-evidence.md`.
- G56R-002 executable freeze:
  `docs/ai/research/codex-g56r-002-executable-candidate-freeze.json`.
- Shared parity contract:
  `docs/ai/specs/agent-routing-parity-contract.md`.
- Treatment schema:
  `tests/speckit-pro/layer6-efficiency/contracts/treatment-record.schema.json`.
- Treatment model and replay helpers:
  `tests/speckit-pro/layer6-efficiency/lib/treatment_trace_model.py` and
  `tests/speckit-pro/layer6-efficiency/lib/treatment_trace_bundle.py`.
- Legacy smoke runner:
  `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py`.
- Legacy lexical smoke scorer:
  `tests/speckit-pro/layer6-efficiency/lib/quality-scorer.py`.
- Project constitution: `.specify/memory/constitution.md`.
- Project agent contract: `AGENTS.md`.
- Release workflow:
  `docs-site/src/content/docs/contribute-and-release.md`.
- Current official Codex model and developer-command documentation:
  <https://learn.chatgpt.com/docs/models> and
  <https://learn.chatgpt.com/docs/developer-commands?surface=cli#cli-codex-debug-models>.

Runtime collection may establish facts only for the pinned account and client.
It cannot turn an undocumented or source-unbound model into a universal
platform claim.

### Phase 0 Preflight Results

| Check | Result | Evidence |
|---|---|---|
| Main synchronization | Pass | Worktree created from refreshed `origin/main` at `6c1ced03` |
| Remote | Pass | Detected `origin` |
| Worktree and branch | Pass | Dedicated worktree registered on `g56r-003-evaluation-runner-scoring` |
| Codex agent install | Pass | Dry run found all ten bundled TOMLs current, including `uat-runbook-author.toml`, with `mutation_status=no_op` |
| SpecKit CLI | Pass | `specify 0.12.12.dev0` is available |
| Repository bootstrap | Not required | No bootstrap, dependency-install, build, or index command is documented; none was run |
| Reviewability setup gate | Warn/pass | No blocker; roadmap requires a split because the projected surface exceeds one review unit |
| Live catalog check | Pass | Pinned Codex CLI 0.145.0 reported seven visible models with explicit supported efforts |
| Dependency integrity | Repaired by design | G56R-002 remains immutable; G56R-003 owns an additive successor snapshot and collector |
| Grill Me | Complete | Fifteen picker decisions reached a natural stop |
| Size estimator | Warn | Four capabilities, 21 files, and 12 requirement groups returned 1120 estimated LOC and 3 suggested slices |
| Split decision | Accepted | One spec, three ordered review slices |
| Preset resolution | Pass | Spec, plan, and tasks templates resolve to `speckit-pro-reviewability v1.0.0` |
| Legacy relocation | Not applicable | G56R namespaces are suppressed by the static Tier-2 relocation rule |
| After-Specify Doctor | Warn | Templates, Python runner, constitution, and feature spec passed; `.specify/init-options.json` names Claude while `.claude/commands/` is absent in this Codex worktree |

The size estimate is advisory and likely overstates fixture-heavy work. The
plan-phase reviewability gate is authoritative. Planning must preserve the
three accepted slices unless a smaller independently reviewable decomposition
is proven.

### Constitution Validation

| Principle | G56R-003 Requirement | Verification |
|---|---|---|
| Plugin Structure Compliance | Put the shared materializer in the shipped runner; keep evaluation adapters and fixtures under Layer 6 | Planned-file review and changed-file manifest |
| Cross-Platform Runtime and Script Safety | Use Python 3.11+ standard library; add no active Bash, `jq`, or shell-language dependency | Focused tests and active-path structural checks |
| Test Coverage Before Merge | Use TDD, deterministic replay, adversarial fixtures, focused tests, then the full suite | Recorded red-green evidence and final test commands |
| Conventional Commits | Use lowercase conventional scopes and validate the final PR title | Git history and release-readiness gate |
| KISS, Simplicity, YAGNI | Reuse G56R-002 contracts, add one score-bundle family, one materializer, and thin adapters | Plan complexity review and Analyze |
| Generated Artifact Integrity | Refresh runner trust metadata, payloads, and proof fixtures after shipped runner changes | `refresh-release-artifacts.py` and final `--check` |

**Constitution Check:** Verified after Specify; G1 artifacts preserve the
declared plugin, runtime, TDD, commit, simplicity, and generated-artifact
boundaries. Recheck at G3.

---

## Specification Context

### Basic Information

| Field | Value |
|---|---|
| **Spec ID** | G56R-003 |
| **Name** | Evaluation Runner, Fixtures, Scoring, and Statistical Analysis |
| **Branch** | `g56r-003-evaluation-runner-scoring` |
| **Dependencies** | G56R-002 plus G56R-001 source-ledger inputs |
| **Enables** | G56R-004 directly; qualification infrastructure for G56R-007 through G56R-010 |
| **Priority** | P1 |
| **Roadmap budget** | 500 reviewable LOC; approximately 4 production files; more than 20 total files; mandatory two-package minimum |
| **Scaffold estimate** | 1120 advisory LOC; 3 accepted review slices |
| **Roadmap tools** | No explicit tool count or tool-name list recorded |

### Source and Evidence Boundaries

| Evidence | Permitted use | Prohibited use |
|---|---|---|
| Current official documentation | Establish documented catalog and command contracts | Claim availability for another account or later runtime |
| Pinned live Codex catalog | Admit source-bound tuples for this environment and snapshot | Add models absent from the official-source candidate ledger |
| G56R-002 trace contract and archived records | Define the immutable treatment shape and preserve historical evidence | Supply new G56R-003 run instances or carry acceptance scores |
| New G56R-003 execution trace | Prove exact delivery and preserve execution resource/lifecycle evidence under the G56R-002 contract | Rewrite an archived G56R-002 artifact |
| G56R-003 score bundle | Record hard-gate results, blinded ballots, statistics, and decisions | Rewrite the referenced G56R-003 execution trace |
| Calibration-only pilot | Estimate feasibility, variance, and scorer operation | Support route qualification or consume governed outcome partitions |
| Deterministic replay | Validate contracts, failure classes, scoring, and statistical decisions in CI | Substitute for outcome-bearing live evidence |

### Success Criteria Summary

- [ ] An authoritative collector records client, account context, retrieval
  method, raw-evidence digest, model visibility, default effort, supported
  efforts, source-ledger binding, timestamp, and invalidation triggers.
- [ ] The initial successor freeze is immutable, non-empty, and contains only
  the intersection of source-admitted candidates and pinned-runtime-supported
  tuples. Ultra and topology-changing modes are classified as policy controls.
- [ ] The shipped canonical materializer produces byte-identical plugin-owned
  agent fields for evaluation and later G56R-006 installation use.
- [ ] The canonical runner proves named-agent delivery, explicit route,
  instruction hash, sandbox, permissions, skills, tools, MCP startup/schema,
  parent controls, client, context, and treatment outcome before scoring.
- [ ] Every assigned attempt emits a new immutable G56R-003
  `execution_trace_id` conforming to the G56R-002 trace contract; service
  reroute and treatment failure remain non-scorable for the requested route.
- [ ] A versioned experiment/score/decision bundle validates joins, hard-gate
  outcomes, blinded ballots, adjudication, analysis, and invalidation without
  changing the treatment record.
- [ ] One governed twelve-role fixture corpus exists: eleven required core
  roles plus `autopilot-fast-helper`, with disjoint calibration, screening,
  selection, cohort-lock, and integrated-confirmation partitions. G56R-003
  consumes calibration only.
- [ ] Deterministic hard gates execute before two independent candidate-blind
  semantic ballots; disagreement invokes one frozen third adjudicator.
- [ ] The current lexical scorer and bare runner remain explicitly
  `non_release_evidence`.
- [ ] The frozen decision rule applies absolute quality/reliability floors and
  paired non-inferiority before Pareto comparison. No dominance means
  inconclusive and no qualification.
- [ ] Candidate-caused failures remain outcomes. Only a preclassified
  independent transient harness failure permits a capped full-pair rerun.
- [ ] Live runs require explicit opt-in, frozen budgets, a pinned environment,
  and operator-only raw evidence retention. Default CI executes replay only.
- [ ] Calibration produces no qualification claim. Numeric margins, sample
  sizes, power, multiplicity, racing, attrition, and terminal rules freeze
  afterward and before any G56R-007 through G56R-010 outcome.
- [ ] Final per-agent route policies, resolver/installer behavior, aggregate
  identities, and integrated confirmation remain out of scope.

---

## Phase 1: Specify

**When to run:** At the start of G56R-003. Define what the qualification
platform must prove and what evidence it may consume. Output:
`specs/g56r-003-evaluation-runner-scoring/spec.md`.

### Specify Prompt

```text
$speckit-specify

## Feature: Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

### Problem Statement
G56R-002 froze a structurally valid but empty executable candidate set because
its pinned collection surfaces did not establish canonical efforts. The current
pinned Codex 0.145.0 catalog now exposes seven visible models and explicit
supported efforts through the documented local catalog inspection path.
G56R-003 must preserve the archived zero set, create an additive authoritative
successor freeze, and build the exact-treatment runner, governed corpus,
blinded scorer, and statistical decision platform that later cohort specs can
use without consuming final integrated-confirmation data.

The existing Layer 6 benchmark prompt-emulates TOML instructions through bare
`codex exec` and scores heading/word overlap. It is useful smoke evidence but
cannot prove named-agent delivery, tools, MCP, parent controls, treatment,
semantic quality, or route qualification.

### Users
- Routing maintainers who need a trustworthy, reproducible qualification
  platform and current source-bound executable tuple freeze.
- Cohort-spec authors in G56R-007 through G56R-010 who need stable corpus,
  scorer, materializer, trace, and analysis contracts.
- Reviewers who need immutable treatment evidence, blinded scoring provenance,
  deterministic replay, and fail-closed statistical decisions.
- Release maintainers who need one shipped materializer and synchronized
  runner trust metadata rather than divergent evaluation/install code.

### User Stories
1. As a capability steward, I can collect the pinned Codex catalog and publish
   a versioned non-empty successor freeze containing only source-admitted,
   runtime-supported model/effort tuples.
2. As an evaluation author, I can materialize and run the actual named-agent
   policy, prove exact treatment, and emit immutable replayable traces before
   any outcome is scored.
3. As a scorer, I can evaluate one governed twelve-role corpus—eleven required
   core roles plus `autopilot-fast-helper`—through deterministic hard gates and
   blinded semantic ballots, with explicit fixture, scorer, treatment,
   candidate, and infrastructure failure classes.
4. As an experiment owner, I can run a calibration-only pilot, freeze the
   analysis plan, and replay paired decision behavior without creating final
   route policies or consuming cohort evidence.

### Constraints
- Preserve G56R-002 artifacts and IDs as immutable historical evidence. Add a
  new versioned capability snapshot/freeze; do not overwrite the zero set.
- Use the pinned runtime's documented catalog inspection contract and record
  client version, account/environment boundary, collection method, raw digest,
  visible models, defaults, supported efforts, timestamps, and invalidation.
- Admit only the intersection of the current official-source candidate ledger
  and pinned-runtime-supported tuples. Runtime discovery cannot add a model.
- Treat Ultra or any topology-changing mode as a G56R-004 policy-level control,
  not an ordinary per-agent effort.
- Implement one Python 3.11 standard-library materializer in
  `speckit-pro/speckit_pro_runner/`; Layer 6 and G56R-006 must consume the same
  implementation.
- Keep `run-efficiency-benchmarks.py` and `quality-scorer.py` as explicitly
  non-release smoke surfaces. Do not delete them or promote their historical
  results.
- Execute installed custom-agent policy or byte-identical canonical
  materialization. Prove named agent, requested route, instruction hash,
  sandbox, permissions, skills, tools, MCP startup/schema, parent controls,
  client, context, and all mandatory G56R-002 treatment fields before scoring.
- Create new immutable G56R-003 `execution_trace_id` records under the
  G56R-002 trace contract. Add versioned experiment/score/decision bundles
  rather than mutating archived treatment evidence or new traces.
- Govern one twelve-role fixture corpus: eleven required core roles plus
  `autopilot-fast-helper`. Create contracts for roles that do not yet have
  executable Codex TOMLs, but run only admitted executable routes. Analyze the
  helper separately from the required core.
- Keep calibration, screening, selection, cohort-lock, and untouched
  integrated-confirmation objectives disjoint. G56R-003 consumes only
  disposable calibration objectives.
- Run deterministic hard gates before semantic evaluation. Require two
  independent candidate-blind rubric ballots, a frozen third adjudicator on
  disagreement, and complete ballot provenance.
- Apply absolute semantic/reliability floors and task-paired non-inferiority
  before Pareto comparison of raw input, cached-input, output tokens, duration,
  retries, compactions, acceptance, and terminal state.
- Preserve `inconclusive => no qualification`; do not force a weighted ranking.
- Keep candidate-caused failures, timeouts, cancellations, budget exhaustion,
  and abandoned work in the estimand with acceptance zero.
- Permit only capped complete-pair reruns for independently preclassified
  transient harness failures. Never rerun one arm alone.
- Make live campaigns explicit, local, pinned, and budgeted. CI runs only
  deterministic replay and contract/statistical tests.
- Use calibration and historical non-release evidence to freeze the numeric
  analysis plan before G56R-007 through G56R-010 observe outcomes.
- Implement as three ordered review slices and rerun the authoritative
  reviewability gate during planning.
- Refresh generated runner metadata, payloads, and proof fixtures whenever
  shipped runner source changes.

### Out of Scope
- Final preferred/fallback route policies or outcome-bearing G56R-007 through
  G56R-010 cohort campaigns.
- G56R-004 adaptive/unpinned controls, G56R-005 availability simulations,
  G56R-006 resolver/installer behavior, and G56R-011 integrated confirmation.
- Installed defaults, aggregate identities, final release claims, or consuming
  the untouched integrated-confirmation partition.
- Raw live captures in Git, live model campaigns in default CI, independent
  arm retries, post-hoc thresholds, and inferred platform facts.
- A second materializer, cross-vendor framework, external evaluation SaaS,
  active Bash, `jq`, or new third-party Python dependencies.
```

### Specify Results

| Metric | Result |
|---|---|
| Functional requirements | 26 uniquely identified, testable requirements |
| User stories | 4 independently testable capability stories with 14 acceptance scenarios |
| Acceptance criteria | 14 measurable success criteria preserve the required PRD ownership and upstream/downstream boundaries |
| Unresolved markers | 0; G1 passed |

### Files Generated

- [x] `specs/g56r-003-evaluation-runner-scoring/spec.md`
- [x] `specs/g56r-003-evaluation-runner-scoring/checklists/requirements.md`

### Traceability Markers

Use `[US1]` through `[US4]` and `[FR-NNN]` consistently. No
`[NEEDS CLARIFICATION]` marker may remain when G1 passes. Every later task must
reference its story and requirement IDs.

---

## Phase 2: Clarify

**When to run:** After Specify. Do not reopen accepted Grill Me decisions.
Resolve only implementation-independent requirements still needed for a
testable specification. Use at most five questions per session.

### Clarify Prompts

#### Session 1: Successor Freeze and Invalidation

```text
$speckit-clarify Focus on the additive successor capability snapshot and executable freeze: exact catalog collection method, pinned client and account/environment identity, source-ledger intersection, visible/hidden handling, ordinary effort versus topology-changing control, raw-evidence digest, non-empty requirement, immutable publication, trigger-based refresh, and tuple-local exclusion. Preserve the archived G56R-002 zero set.
```

#### Session 2: Materialization, Delivery, and Trace Joins

```text
$speckit-clarify Focus on byte-identical materialization, installed-policy equivalence, named-agent delivery proof, requested/effective route evidence, skills/tools/MCP/parent/context fields, service reroute, misdelivery, mandatory telemetry, null behavior, creation of new G56R-003 `execution_trace_id` records under the immutable G56R-002 trace contract, and the exact join from those traces to additive G56R-003 experiment/score/decision bundles.
```

#### Session 3: Corpus and Blinded Scoring

```text
$speckit-clarify Focus on the twelve-role corpus of eleven required core roles plus `autopilot-fast-helper`, currently non-executable roles, helper separation from required-core primary statistics, fixture validity review, deterministic hard gates, rubric schema, two independent candidate-blind ballots, third-adjudicator disagreement handling, scorer identities and calibration, failure taxonomy, score invalidation, and committed-versus-private evidence.
```

#### Session 4: Partitions, Statistics, and Campaign Controls

```text
$speckit-clarify Focus on disjoint calibration/screening/selection/cohort-lock/integrated-confirmation partitions, calibration-only non-qualification labels, immutable comparator bindings, quality-first non-inferiority plus Pareto selection, task-level pairing and clustering, budget and terminal rules, capped full-pair reruns, attrition, live-local versus replay-CI behavior, and the freeze point for margins, sample sizes, power, multiplicity, racing, and `inconclusive => no qualification`.
```

### Clarify Results

| Session | Focus Area | Outcome |
|---|---|---|
| 1 | Successor freeze | Complete: refreshed `codex debug models` authority, sanitized evidence allowlist, source/runtime effort normalization, non-empty publication rule, and separate tuple/snapshot/treatment failure planes |
| 2 | Treatment and joins | Complete: byte-owned materialization, strict requested-route score predicate, explicit null/missing behavior, reroute/misdelivery disposition, and additive trace-to-bundle joins |
| 3 | Corpus and scoring | Complete: explicit 9+2 core role inventory plus helper, fixture validity contract, closed failure/invalidation planes, two blinded ballots, frozen adjudicator, and sanitized scorer evidence |
| 4 | Statistics and campaigns | Complete: closed partitions, immutable pair bindings, floors→paired NI→Pareto sequence, assigned-attempt estimand, capped complete-pair reruns, and post-calibration/pre-cohort analysis-plan freeze |

**G2 Gate:** Pass only when zero unresolved requirement markers remain.

### Consensus Resolution Log

| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |
|---|---|---|---|---|---|---|---|
| 1 | Clarify | Runtime catalog authority | [codebase, domain] | 1 | both-agree | Refreshed `codex debug models` is runtime authority; other surfaces are diagnostic only | codebase-analyst, domain-researcher |
| 2 | Clarify | Commit-safe account and auth boundary | [security] | 1 | 3/3 | Applied deny-by-default sanitized allowlist under the already accepted operator-only raw-evidence decision | codebase-analyst, spec-context-analyst, domain-researcher |
| 3 | Clarify | Effort vocabulary normalization | [spec, domain] | 1 | both-agree | Normalize only evidence-backed ordinary tokens before source/runtime intersection; exclude topology controls | spec-context-analyst, domain-researcher |
| 4 | Clarify | Tuple exclusion taxonomy | [codebase, spec] | 1→2 | escape-hatch, 2/3 | Kept capability tuple reasons closed and separate from snapshot authority and treatment/scoring failure planes | codebase-analyst, spec-context-analyst, domain-researcher |
| 5 | Clarify | Requested-route score eligibility | [codebase, spec] | 1 | both-agree | Require byte-identical/configured-route proof, complete mandatory observations and reroute monitoring, proven disposition, and no disqualifying delivery failure | codebase-analyst, spec-context-analyst |
| 6 | Clarify | Commit-safe scorer evidence | [security] | 1 (reused) | 3/3 prior consensus | Reused Session 1's deny-by-default sanitized allowlist for scorer artifacts; raw/private evidence stays operator-only | codebase-analyst, spec-context-analyst, domain-researcher |

### Analyze Consensus

The Analyze executor reported zero findings across all twelve required checks,
so the mandatory consensus row completed without analyst escalation.

📊 Confidence: 0.99

- Task understanding: 0.98
- Approach clarity: 0.98
- Requirements alignment: 1.00
- Risk assessment: 1.00
- Completeness: 1.00

#### Analyze Consensus Rerun After Task-Executor Contract Repair

The rerun verified 25 self-contained executor tasks, complete FR coverage, safe
fixture parallelism, and all prior Analyze checks with zero findings.

📊 Confidence: 0.99

- Task understanding: 0.98
- Approach clarity: 0.98
- Requirements alignment: 1.00
- Risk assessment: 1.00
- Completeness: 1.00

---

## Phase 3: Plan

**When to run:** After the specification is finalized. Generate the technical
blueprint and re-run reviewability before implementation. Output:
`specs/g56r-003-evaluation-runner-scoring/plan.md`.

### Plan Prompt

```text
$speckit-plan

## Technical Context
- Runtime: Python 3.11+ standard library.
- Shipped source: `speckit-pro/speckit_pro_runner/` owns the single canonical
  materializer consumed by evaluation and later G56R-006 installation.
- Evaluation source: `tests/speckit-pro/layer6-efficiency/` owns thin runner
  adapters, corpus manifests, scorer/statistical contracts, and replay tools.
- Existing treatment truth: G56R-002 treatment schema, model, bundles, and
  synthetic replay fixtures remain immutable and are reused.
- Existing smoke boundary: `run-efficiency-benchmarks.py`,
  `fixtures-codex/`, and `quality-scorer.py` remain non-release evidence.
- Candidate truth: G56R-001 source ledger intersected with an additive,
  pinned-runtime successor capability freeze.
- Generated-artifact contract: shipped runner changes require
  `scripts/refresh-release-artifacts.py`, runner trust metadata, payloads,
  installed-cache proofs, and final drift verification.
- Tests: deterministic replay in CI; explicit budgeted local command for the
  calibration-only live pilot.

## Accepted Architecture Decisions
- "Add successor freeze": preserve G56R-002 history and create a versioned,
  non-empty pinned-runtime successor.
- "Add canonical runner": preserve smoke evidence and add a separate
  exact-treatment runner.
- "Add score bundle": reference new immutable G56R-003 execution traces
  conforming to the G56R-002 contract rather than changing archived evidence.
- "Shipped runner module": one production materializer, no relocation or copy
  in G56R-006.
- "Twelve contracts": govern eleven required core roles plus the optional
  helper and execute only admitted routes; helper evidence is separate from
  required-core primary statistics.
- "Hybrid blinded scoring" plus "Two blinded ballots": deterministic gates
  precede semantic ballots and frozen disagreement resolution.
- "Quality-first Pareto": non-inferiority before raw-vector dominance, with
  explicit inconclusive outcomes.
- "Explicit local campaigns" and "Capped paired rerun": replay in CI, live
  opt-in, and no discretionary arm-only retry.
- "Cohort specs own them": G56R-007 through G56R-010 own final
  outcome-bearing campaigns and route policies.
- "Versioned refresh on triggers": immutable snapshots refresh only on
  declared invalidation.
- "Calibration-only partition": G56R-003 pilot results never qualify routes.
- "Freeze after calibration": publish the analysis plan before cohort outcomes.
- "Three ordered slices": keep one spec but emit three reviewable PR slices.

## Ordered Review Slices
1. Capability, materialization, and trace:
   - Authoritative catalog collector and additive successor freeze.
   - Shipped canonical materializer plus thin exact-treatment runner adapter.
   - New G56R-003 traces under the G56R-002 contract, treatment proof, and
     deterministic delivery replay.
2. Corpus and blinded scoring:
   - Eleven required core role contracts plus the optional-helper contract and
     disjoint partition manifests.
   - Deterministic hard gates, rubric/ballot schemas, two-ballot adjudication,
     score bundles, failure taxonomy, and scorer invalidation replay.
3. Experiment policy, statistics, and calibration:
   - Immutable comparator and analysis-plan schemas.
   - Paired task-level inference, quality-first Pareto decision, budgets,
     attrition, full-pair reruns, and inconclusive handling.
   - Explicit calibration-only live command, report, and post-calibration
     analysis-plan freeze.

## Required Ownership and Data-Flow Proof
- Show the materializer import path used by both Layer 6 and planned G56R-006.
- Show the immutable foreign-key-style joins from source ledger to successor
  snapshot to route assignment to new G56R-003 execution trace under the
  G56R-002 contract to G56R-003 score bundle and decision.
- Show every raw-byte boundary, digest, redaction rule, operator-only
  retention path, and committed deterministic fixture.
- Show how fixture/scorer/rubric/adjudicator changes increment versions and
  invalidate affected results.
- Show how each evidence partition remains disjoint and why the pilot cannot
  leak into later inference.
- Show source-authored versus generated release artifacts and the regeneration
  owner for every shipped runner change.

## Constraints
- Prefer existing G56R-002 schema, trace, replay, and content-addressed
  retention helpers. Add the smallest new contracts required for scoring and
  analysis.
- Do not hand-edit generated payloads, installed-cache proofs, runner hashes,
  or release evidence. Use the canonical refresh script.
- Do not create `run_codex_role_eval.py` merely because the roadmap names it.
  Bind planning to the live smoke runner and choose a durable capability-based
  name for the canonical qualification entry point.
- Keep the optional helper outside required-core primary statistics.
- Keep Ultra and topology-changing behavior outside ordinary per-agent effort
  search.
- Do not emit final route policies, resolver behavior, installer defaults,
  aggregate IDs, or integrated confirmation.
- Preserve the accepted three-slice boundary unless the authoritative
  reviewability gate proves a smaller safe decomposition.
- Follow `docs/ai/specs/.process/G56R-003-design-concept.md` as the source of
  truth for accepted scoping decisions.

## Required Plan Artifacts
- `plan.md` with constitution, ownership, generated-artifact, and reviewability
  decisions.
- `research.md` for current official catalog contracts, G56R-002 reuse, scorer
  calibration, statistical methods, and source-versus-runtime authority.
- `data-model.md` for capability snapshots, route assignments, immutable trace
  joins, fixtures, ballots, scores, policies, campaigns, partitions, and
  decisions.
- `contracts/` for successor snapshot/freeze, experiment policy, corpus,
  score/adjudication bundle, and analysis output schemas.
- `quickstart.md` for deterministic replay, explicit local calibration, raw
  evidence retention, and release-artifact regeneration.
```

### Plan Results

| Artifact | Required Content |
|---|---|
| `plan.md` | Complete — three slices, shipped materializer ownership, constitution, generated artifacts, and reviewability |
| `research.md` | Complete — twelve decisions covering authority, reuse, calibration, inference, and CI/live boundaries |
| `data-model.md` | Complete — append-only ID graph, state transitions, joins, invalidation, and evidence allowlist |
| `contracts/` | Complete — successor freeze, experiment policy, corpus, score/adjudication, analysis-plan, and analysis/decision schemas |
| `quickstart.md` | Complete — replay, explicit calibration, retention, analysis freeze, regeneration, and verification |

### Planning Reviewability Inputs

Record explicit post-plan values so the reviewability parser does not infer
them from prose:

- Reviewable LOC: 760 for the largest individual slice
- Production Files: 5 for the largest individual slice
- Total Files: 16 for the largest individual slice
- Primary Surface: harness/adapter
- Accepted decomposition: three ordered review slices

The authoritative `estimate-reviewable-loc` helper returned `pass` with 24
declared file operations. Its current production-file taxonomy reported zero
because these Python sources live below repository-specific nested roots, so
the explicit per-slice estimates above remain the conservative planning
boundary.

**G3 Gate:** Passed — zero unresolved plan markers. No slice exceeds the
explicit 800-LOC block boundary, generated release artifacts are excluded from
authored design counts, and G56R-006 reuses
`speckit_pro_runner.agent_materialization.materialize_agent_policy`.

---

## Phase 4: Domain Checklists

**When to run:** After `$speckit-plan`. Run these four domains because the
highest risks are model-route authority, immutable evidence joins, fail-closed
failure behavior, and statistically valid resource comparisons.

### Checklist Prompts

#### 1. LLM Integration Checklist

```text
$speckit-checklist llm-integration

Focus on G56R-003 requirements:
- Source-ledger intersection with the pinned live catalog and non-empty
  successor freeze.
- Documented default effort, supported ordinary efforts, and exclusion of
  Ultra/topology-changing modes from per-agent effort search.
- Exact named-agent materialization, route delivery, skills, tools, MCP,
  parent controls, and service-reroute handling.
- A twelve-role corpus of eleven required core roles plus the optional helper,
  semantic rubric calibration, and helper separation from required-core
  primary statistics.
- Pay special attention to any runtime observation promoted into a universal
  platform claim or any score produced before exact treatment passes.
```

#### 2. Data Integrity Checklist

```text
$speckit-checklist data-integrity

Focus on G56R-003 requirements:
- Immutable joins across source ledger, successor snapshot/freeze, candidate
  route, assignment, new G56R-003 execution trace under the G56R-002 contract,
  G56R-003 score bundle, analysis plan, and decision.
- Stable IDs, schema versions, hashes, timestamps, nulls, provenance, and
  invalidation triggers.
- Disjoint calibration, screening, selection, cohort-lock, and integrated-
  confirmation partitions.
- Operator-only raw evidence versus committed deterministic fixtures.
- Pay special attention to orphan records, in-place mutation, lossy joins,
  cross-partition reuse, and stale scorer or fixture versions.
```

#### 3. Error Handling Checklist

```text
$speckit-checklist error-handling

Focus on G56R-003 requirements:
- Empty or malformed catalog, unsupported effort, hidden tuple, stale snapshot,
  treatment misdelivery, service reroute, missing mandatory telemetry, invalid
  fixture, invalid scorer, infrastructure failure, and adjudicator disagreement.
- Candidate-caused failure retention and independently preclassified transient
  harness failures.
- Capped complete-pair reruns, no arm-only retries, unknown attrition, budget
  exhaustion, cancellation, and terminal policy.
- `inconclusive => no qualification` at every decision boundary.
- Pay special attention to paths that silently score a failed treatment,
  discard a failed attempt, or force a route ordering.
```

#### 4. Performance Checklist

```text
$speckit-checklist performance

Focus on G56R-003 requirements:
- Raw input, cached-input, and output tokens; duration; retries; compactions;
  acceptance; terminal state; and all attributable failed/abandoned work.
- Task-level pairing and clustering, workload strata, sample-size assumptions,
  p95 guardrails, power, alpha, multiplicity, racing, futility, and attrition.
- Calibration-only estimation followed by a frozen pre-outcome analysis plan.
- Explicit campaign token, time, candidate, and confirmation-entry budgets.
- Pay special attention to post-hoc thresholds, unpaired comparisons,
  complete-case bias, cache leakage, and hidden weighted scores.
```

### Checklist Results

| Checklist | Status | Required Verdict |
|---|---|---|
| LLM integration | Complete — 34/34 pass, zero gaps; consensus skipped because no unresolved item was reported | No unsupported platform claim or treatment/scoring ambiguity |
| Data integrity | Complete — 38/38 pass, zero gaps; consensus skipped because no unresolved item was reported | Complete immutable joins, partitions, versions, and retention rules |
| Error handling | Complete — 35/35 pass after closing 2 gaps; consensus skipped because no unresolved item remained | Every failure class and rerun path is explicit and fail-closed |
| Performance | Complete — 34/34 pass after closing 4 gaps; consensus skipped because no unresolved item remained | Estimand, budgets, inference, and decision rules are measurable |

**G4 Gate:** Passed — 0 `[Gap]` markers remain after one remediation loop for
Error Handling and one for Performance. Every checklist executor reported zero
unresolved consensus items.

---

## Phase 5: Tasks

**When to run:** After all checklist gaps are resolved. Output:
`specs/g56r-003-evaluation-runner-scoring/tasks.md`.

### Tasks Prompt

```text
$speckit-tasks

Read:
- `specs/g56r-003-evaluation-runner-scoring/spec.md`
- `specs/g56r-003-evaluation-runner-scoring/plan.md`
- `docs/ai/specs/.process/G56R-003-design-concept.md`

## Task Structure
- Follow strict red-green-refactor TDD for every behavior.
- Keep tasks small, observable, and linked to `[USn]` and `[FR-NNN]`.
- Organize tasks by the three accepted end-to-end review slices, not by a
  generic foundation layer.
- Mark parallel-safe fixture authoring only when it cannot conflict with shared
  manifests, schemas, generated artifacts, or suite registration.
- Include explicit failing-test evidence, minimum implementation, refactor,
  focused verification, reviewability, and slice-closeout tasks.

## Slice 1: Capability, Materialization, and Trace
- Test and implement the authoritative catalog collector and additive successor
  freeze, including non-empty and invalidation behavior.
- Test and implement the shipped canonical materializer and thin Layer 6
  exact-treatment runner.
- Reuse the G56R-002 trace contract, create new G56R-003 traces, and add
  delivery/treatment replay without changing archived records.
- Refresh generated release artifacts after shipped runner changes and verify
  the slice diff is clean.

## Slice 2: Corpus and Blinded Scoring
- Author and independently validate eleven required core role fixture
  contracts plus the `autopilot-fast-helper` contract.
- Freeze partition and workload metadata without consuming governed outcome
  objectives.
- Test deterministic hard gates, rubric/ballot contracts, two independent
  ballots, third-adjudicator resolution, failure taxonomy, score bundles, and
  invalidation.
- Keep optional-helper contracts and statistics separate.

## Slice 3: Experiment Policy, Statistics, and Calibration
- Test immutable comparator, analysis-plan, campaign, and decision contracts.
- Test task-level paired inference, clustering, non-inferiority, Pareto
  dominance, ties, missing data, attrition, budgets, terminal policy, and
  capped complete-pair reruns.
- Implement explicit calibration-only local execution and deterministic replay.
- Run calibration only after its safety gates pass, freeze the versioned
  analysis plan, and prove no calibration result can qualify a route.

## Non-goal Enforcement
- Add negative tests that reject final route policy IDs, integrated-
  confirmation consumption, live-default CI behavior, raw evidence in Git,
  arm-only retries, post-hoc thresholds, trace mutation, and duplicate
  materializers.
- Ensure the absent roadmap path `run_codex_role_eval.py` is not recreated by
  accident.

## Verification Tasks
- Run focused new unit tests during each red-green cycle.
- Run `python3 -u tests/speckit-pro/run-all.py` before final readiness.
- Run `PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py`
  after shipped source changes and commit the generated outputs.
- Run
  `PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py --check`
  after all source and generated outputs are final.
- Validate the exact final PR title with the repository release-readiness gate.
```

### Tasks Results

| Metric | Required Record |
|---|---|
| Total tasks | 25 self-contained implement-executor tasks |
| Review slices | 3 ordered implementation/review slices |
| Parallel opportunities | 3 disjoint role-fixture groups (T008–T010); shared manifests, schemas, helpers, and generated artifacts stay serial |
| Requirements covered | FR-001 through FR-038, with an explicit traceability matrix |
| Non-goal tests | T024 rejects final policies, integrated confirmation, live-default CI, raw evidence, arm-only retry, post-hoc thresholds, trace mutation, duplicate materializers, cache leakage, unknown attrition, unrestricted codes, and missing budgets |

**Tasks-phase reviewability evidence**:

- `reviewability-gate` requested mode: tasks
- Helper diagnostic: installed runner supports setup mode only; tasks mode is
  deferred and was not invoked as an active helper.
- Fallback evidence: scaffold/setup reviewability was non-blocking;
  plan-phase `estimate-reviewable-loc` returned `pass`; the workflow-ratified
  decomposition remains three ordered slices.
- Correctness result: no malformed or stale marker state, failed verification,
  unsafe output, or non-size safety finding was observed.

**G5 Gate:** Passed after executor-contract repair — 25 unchecked,
self-contained RED→GREEN→REFACTOR tasks found; every FR-001 through FR-038 is
mapped; the Phase 7 rows name the three concrete task groups; and no executor
must cross a task boundary to complete its mandatory TDD cycle.

---

## Atomicity Route

After Tasks/G5, run the read-only atomicity classifier:

```text
runner helper atomicity-route specs/g56r-003-evaluation-runner-scoring
```

Record the emitted route, releasability, decisive signals, and warnings in this
section. The accepted Grill Me decomposition is three ordered review slices;
the classifier may refine PR mechanics but must not silently collapse the
reviewability decision.

| Field | Value |
|---|---|
| **Route** | `one-navigable-PR` |
| **Releasable** | `true` |
| **Signals** | `change-shape:modify-heavy` |
| **Warnings** | None |

The classifier chose one navigable PR because the shared manifest, schemas,
runner entry point, and generated artifacts make the task graph modify-heavy.
The PR still preserves the three ordered review slices and their independent
G7 evidence.

---

## Layer Plan

| Field | Value |
|---|---|
| **Status** | `skipped` |
| **Reason** | Atomicity route is `one-navigable-PR`, not `split-PR` |
| **Planner invocation** | Not required |
| **PR mechanics** | One PR with three ordered review slices |

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks.

### Analyze Prompt

```text
$speckit-analyze

Cross-check:
- `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`
- `docs/prd-codex-gpt-5-6-agent-routing.md`
- `docs/ai/specs/.process/G56R-003-design-concept.md`
- `specs/g56r-003-evaluation-runner-scoring/spec.md`
- `specs/g56r-003-evaluation-runner-scoring/plan.md`
- `specs/g56r-003-evaluation-runner-scoring/tasks.md`

Focus on:
1. Preserve every accepted Grill Me decision and flag downstream drift.
2. Reconcile the roadmap's stale `run_codex_role_eval.py` path with the live
   smoke runner without inventing compatibility work.
3. Reconcile G56R-003's broad "qualify candidates" goal with the accepted
   boundary that G56R-007 through G56R-010 own final outcome-bearing campaigns
   and route policies.
4. Verify the successor freeze is additive, source-bound, pinned, non-empty,
   immutable, and refreshable only through declared invalidation.
5. Verify treatment records remain immutable and score/decision evidence uses
   validated foreign-key-style joins.
6. Verify exact treatment gates precede scoring in every path.
7. Verify all eleven required core roles and the optional helper are governed,
   only admitted routes execute, and the helper stays outside required-core
   statistics.
8. Verify calibration cannot enter screening, selection, cohort-lock, or
   integrated-confirmation inference.
9. Verify two-ballot blinding, third-adjudicator resolution, versioning, and
   failure classification are complete.
10. Verify paired inference, quality-first Pareto rules, budgets, reruns,
    attrition, and inconclusive handling are predeclared and testable.
11. Verify the three slices are vertical, independently reviewable, and within
    the authoritative plan budget.
12. Verify shipped source and generated release artifacts have one explicit
    owner and regeneration path.

Remediate all critical and high findings before G6. Do not implement code in
Analyze.
```

### Analyze Severity Levels

| Severity | Meaning | Required Action |
|---|---|---|
| `CRITICAL` | Evidence invalidity, constitution violation, or scope ownership conflict | Must fix before G6 |
| `HIGH` | Significant requirement, data, statistical, or reviewability gap | Must fix or obtain explicit disposition |
| `MEDIUM` | Important clarity or maintainability improvement | Review and record |
| `LOW` | Minor inconsistency | Record for later |

### Analyze Results

| Field | Result |
|---|---|
| Findings | Rerun: 0 CRITICAL, 0 HIGH, 0 MEDIUM, 0 LOW |
| Remediation | Tasks repaired to match the single-task implement-executor contract |
| Consensus | Rerun completed by zero-unresolved-item rule |
| Mechanical checks | 25 self-contained TDD tasks, all 38 FRs mapped, 6 schemas valid, stale runner path absent |
| G6 | Passed after task repair — 0 CRITICAL/HIGH findings |

---

## Phase 6.5: Confidence Gate

**When to run:** After Analyze and its mandatory consensus item, before any
implementation task. Resolve the mode once during preflight and use the latest
workflow confidence emit.

| Field | Value |
|---|---|
| Mode | Advisory |
| Threshold | 0.90 |
| Status | Passed after task repair — 0.99 ≥ 0.90 |
| Bounded remediation | Not required |

---

## Phase 7: Implement

**When to run:** After tasks and Analyze pass.

### Implement Prompt

```text
$speckit-implement

Read `tasks.md`, `plan.md`, and
`docs/ai/specs/.process/G56R-003-design-concept.md` before each slice. The
Design Concept records why each boundary exists.

## TDD Cycle
For every task:
1. RED: Add the smallest failing unit or replay test for the requirement.
2. VERIFY RED: Run the focused test and record the expected failure.
3. GREEN: Implement only enough Python 3.11 standard-library behavior to pass.
4. VERIFY GREEN: Run the focused test and adjacent G56R-002 regression tests.
5. REFACTOR: Remove duplication and keep one materializer/contract authority.
6. VERIFY: Re-run the focused and slice-level tests.

## Slice Discipline
- Finish Slice 1 verification and generated-artifact refresh before Slice 2.
- Finish Slice 2 fixture/scorer validity and replay before Slice 3.
- Run only the calibration partition in Slice 3. Stop if any command would
  consume screening, selection, cohort-lock, or integrated-confirmation data.
- Do not emit final per-agent route policies.

## Evidence Discipline
- Keep raw live captures in the inherited operator-only content-addressed
  store. Commit only schemas, digests, sanitized fixtures, deterministic
  replay, and bounded reports.
- Preserve candidate-caused failures and every assigned attempt.
- Never score before exact treatment passes.
- Never adjust thresholds after cohort outcomes.

## Verification
- Run focused new tests during every TDD cycle.
- Run the existing G56R-002 capability/treatment contract and replay tests
  after shared-schema or trace-adjacent changes.
- Run `python3 -u tests/speckit-pro/run-all.py` before final readiness.
- After any shipped runner change, run
  `PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py`.
- When source and generated outputs are final, run
  `PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py --check`.
- Review the final diff for raw evidence, secrets, personal paths, stale
  generated artifacts, scope leakage, and reviewability.
```

### Implementation Progress

| Slice | Goal | Status |
|---|---|---|
| 1 | Capability, materialization, and trace | Complete |
| 2 | Corpus and blinded scoring | Complete |
| 3 | Experiment policy, statistics, and calibration | Complete |

### Task Evidence

| Task | Status | RED | GREEN / Regression |
|---|---|---|---|
| T001 | Complete | Initial missing module, then corrective catalog-contract run: 5 tests with 18 failures and 3 errors | Successor 5/5; unchanged G56R-002 capability contract 99/99; predecessor freeze has no diff |
| T002 | Complete | 7 tests failed because the shipped canonical module was missing | Materialization 7/7; pure exact-byte contract and shared shipped import verified |
| T003 | Complete | Initial 9 failures; corrective materialization/public-API RED also confirmed | Qualification 9/9; unchanged G56R-002 capability contract 99/99 |
| T004 | Complete | 5 CLI tests failed because the entry point was missing | Combined qualification/CLI 14/14; stale roadmap runner absent |
| T005 | Complete | Trust assertion failed because the materializer was absent from runner metadata | Trust 8/8; generator-only refresh committed at `a9bdfe0e`; final generated drift check passed |
| T006 | Complete | End-to-end replay failed because qualification did not accept successor authority | Focused 5/5 + 8/8 + 15/15; Layer 4 1637/1637; docs reference current; G7 passed |
| T007 | Complete | 8 corpus-contract tests failed before the validator/schema existed | Corpus 8/8; exact 12/11/9/2/1 role boundary and admitted-route scheduling verified |
| T008-T010 | Complete | Disjoint fixture groups failed on 4, 5, and 3 missing role fixtures | Fixture groups A/B/C independently pass 3/3, 1/1, and 1/1 |
| T011 | Complete | Shared-manifest RED failed before the manifest and non-executable skip reasons existed | Corpus 10/10; fixture groups A/B/C 3/3, 1/1, and 1/1; manifest digest frozen |
| T012 | Complete | 8 focused tests produced 14 missing-implementation assertion failures | Hard-gate scoring 8/8; closed seven-gate order, fail-closed evidence, and score-before-gates prohibition verified |
| T013 | Complete | Ballot/adjudication additions produced 1 failure and 15 missing-API errors | Scoring 12/12; distinct blind ballots, frozen rubric, current calibration, and non-reused third adjudicator verified |
| T014 | Complete | Score-bundle additions produced 2 failures and 50 missing schema/API errors | Scoring 20/20; immutable ID/digest joins, closed taxonomy, terminal estimand records, and additive invalidation verified |
| T015 | Complete | Evidence safety/replay additions produced 5 failures against the prior 19-test baseline | Scoring 24/24; deny-by-default sanitizer, opaque bindings, stale-version invalidation, deterministic replay, and zero sensitive scan matches verified |
| T016 | Complete | End-to-end regression produced 1 failure and 1 missing summary API error | Scoring 25/25; corpus 10/10 + 3/3 + 1/1 + 1/1; privacy 10/10; Layer 4 1637/1637; docs reference current; G7 passed |
| T017 | Complete | Four contract tests produced 6 assertions for missing repository schemas | Qualification contracts 19/19; closed experiment, analysis-plan, and ordered decision schemas verified |
| T018 | Complete | Five comparison tests produced 21 missing-API errors and 1 export failure | Qualification contracts 24/24; complete pre-execution joins, calibration isolation, additive invalidation, and rebinding refusal verified |
| T019 | Complete | Six statistics tests produced 12 missing-behavior assertion failures | Statistics 6/6; floors → paired cluster-adjusted NI → raw Pareto order, uncertainty, ties, mixed outcomes, and no hidden weights verified |
| T020 | Complete | Four workload/cache tests produced 10 failures and 1 missing-API error | Statistics 10/10; closed strata, p95 tail guardrails, minimum tasks, unknown-stratum handling, cache isolation, and order-leak rejection verified |
| T021 | Complete | Four terminal/rerun tests produced 4 failures and 5 missing-behavior errors | Statistics 14/14; acceptance-zero terminals, evidence-boundary attrition, capped complete-pair reruns, and one-arm/complete-case refusal verified |
| T022 | Complete | Three budget/partition tests produced 17 failures and 10 errors | Statistics 17/17; all seven budget ceilings, calibration-only partitions/decisions, no final policy/default/aggregate/release, and one no-qualification path verified |
| T023 | Complete | Replay/CLI additions produced contract 1 failure + 4 errors and statistics 2 failures + 1 error | Qualification contracts 27/27; statistics/replay 20/20; deterministic offline decision identity, explicit local calibration, frozen analysis-plan output, complete bindings, and no-network/no-live-write boundaries verified |
| T024 | Complete | Six new methods and one expanded test produced 11 failures and 1 error | Statistics/replay 26/26; qualification contracts 27/27; closed freeze metadata/numeric validation and all prohibited route, evidence, retry, mutation, cache, attrition, code, and budget boundaries verified; stale runner absent |
| T025 | Complete | Full source-lineage replay failed once on the missing closed-shape join | Focused G56R-003 107/107; G56R-002 99/99; full suite 3251/3251; exact suite registration, docs reference/validation, release-title validation, diff check, and post-checkpoint release-artifact check passed |

---

## Post-Implementation Checklist

| Post Item | Status | Findings | Action Needed |
|---|---|---|---|
| Post: Doctor Extension Check | Complete | 0 failures; known warning that Claude integration has no `.claude/commands/` in this Codex worktree | None |
| Post: Verify Implementation | Complete | 25/25 tasks, 38/38 requirements, 0 findings | None |
| Post: Verify Tasks Phantom Check | Complete | 25 VERIFIED; 0 partial, weak, not found, or skipped | None |
| Post: Code Review | Complete | Multiple authority and replay joins were remediated; final independent review found 0 findings | None |
| Post: Integration Suite | Complete | 3251/3251 passed; G56R-002 regression 99/99 passed | None |
| Post: Reviewability Diff Gate | Complete | Current committed estimator passed with 24 declared entries; the three ordered slices and one-navigable-PR route remain ratified | None |
| Post: Self-Review | Complete | No edge-case gaps, requirement orphans, silent deferrals, or tidiness findings | None |
| Post: UAT Runbook Generation | Skipped | `skipped: generate-uat-skeleton deferred`; no committed source-derived runbook exists | None; deferred output is fail-open |
| Post: Final Reviewability Backstop | Complete | Deferred-helper rule satisfied by estimator pass at `3981dfe0`, three G7 slice records, and the ratified one-navigable-PR route | None |
| Post: PR Packet/Body Generation | Complete | Packet and packet-owned body emitted by `pr-packet-output` in dry-run and apply modes | None |
| Post: PR Body Generation | Complete | Read-only packet validation passed with `pr_blocked=false`; the required consumer-facing release-note block is present | None |
| Post: PR Creation | Complete | PR [#386](https://github.com/racecraft-lab/racecraft-plugins-public/pull/386) created from the validated packet at pushed head `9fcff1d2` | None |
| Post: Review Remediation | In Progress | GitHub Code Quality reported one imprecise assertion, one unused import, and one unused assignment after the earlier green review audit | Apply the three surgical fixes, rerun focused and full gates, and verify the next pushed head |
| Post: Retrospective | Complete | Reproducibility, failed authority assumptions, reusable boundaries, and later-cohort invalidation rules recorded; roadmap marks G56R-003 complete in PR #386 | None |

- [x] All tasks are complete and trace to requirements.
- [x] Every slice has red-green-refactor evidence.
- [x] Focused capability, treatment, materializer, corpus, scorer, and
  statistical tests pass.
- [x] `python3 -u tests/speckit-pro/run-all.py` passes.
- [x] Release artifacts were refreshed after shipped runner changes.
- [x] `refresh-release-artifacts.py --check` reports no drift.
- [x] The calibration-only pilot is explicitly non-qualification evidence.
- [x] No screening, selection, cohort-lock, or integrated-confirmation
  objective was consumed.
- [x] No final per-agent route policy or installed default was created.
- [x] No raw live capture, secret, credential, or personal path is committed.
- [x] Actual reviewability evidence passes for the three ratified slices.
- [x] The exact PR title passes release readiness.
- [ ] Review findings are remediated against the final pushed head.
- [x] Roadmap and workflow status accurately reflect the final state.

---

### Self-Review (auto-generated)

**Tests executed:** `BUILD`, `TYPECHECK`, and `LINT` are not defined for this
repository scope. The applicable unit and integration commands ran in this
session at 2026-07-25T17:34:50Z and exited zero: focused G56R-003 suites,
G56R-002 regression 99/99, and the full repository suite 3251/3251. Release
artifact and generated-reference drift checks also passed.

**Edge cases:** All 14 acceptance scenarios have non-happy-path coverage:

- US1.1 additive history and authority failures:
  `test-codex-successor-capability.py:390,453`.
- US1.2 runtime-only tuple exclusion and diagnostic non-authority:
  `test-codex-successor-capability.py:330`.
- US1.3 topology controls excluded from ordinary effort:
  `test-codex-successor-capability.py:330`.
- US2.1 missing mandatory treatment evidence:
  `test-codex-qualification-contracts.py:1498,1565`.
- US2.2 materialization mismatch and score refusal:
  `test-agent-materialization.py:166` and
  `test-codex-qualification-contracts.py:1836,1870`.
- US2.3 immutable one-to-one trace and score joins:
  `test-codex-qualification-contracts.py:1696,1885` and
  `test-codex-qualification-scoring.py:1060`.
- US3.1 governed membership and admitted-route authority:
  `test-codex-qualification-corpus.py:445,570,616`.
- US3.2 gate failure, absence, and ordering:
  `test-codex-qualification-scoring.py:1316,1323,1332,1342`.
- US3.3 disagreement and adjudicator validity:
  `test-codex-qualification-scoring.py:1483,1531`.
- US3.4 closed failure classification and attrition:
  `test-codex-qualification-scoring.py:946,1009`.
- US4.1 pre-cohort numeric plan freeze:
  `test-codex-qualification-statistics.py:707,1628,1666`.
- US4.2 floors, complete pairs, and uncertainty:
  `test-codex-qualification-statistics.py:1295,1334,1393`.
- US4.3 later-partition and prohibited-output refusal:
  `test-codex-qualification-statistics.py:865,885,1588`.
- US4.4 implicit-live and incomplete-budget refusal:
  `test-codex-qualification-contracts.py:1979,2050`.

No `[edge-case-gap]` markers were found.

**Requirements matched:** FR-001→T001/T006/T025; FR-002→T001;
FR-003→T001; FR-004→T001; FR-005→T001; FR-006→T002/T006; FR-007→T004;
FR-008→T002/T004; FR-009→T003/T004; FR-010→T003/T004/T006/T023/T025;
FR-011→T007–T011/T016; FR-012→T007/T010/T011; FR-013→T011/T017/T018/T022/T024;
FR-014→T012/T016; FR-015→T013/T016; FR-016→T014–T016/T025;
FR-017→T017/T019; FR-018→T017/T019/T020; FR-019→T017/T019/T022/T024;
FR-020→T021/T024; FR-021→T017/T021/T024; FR-022→T017/T022/T023;
FR-023→T017/T023/T024; FR-024→T017/T022/T024; FR-025→T006/T016/T025;
FR-026→T005/T006/T025; FR-027→T001/T015/T024; FR-028→T001;
FR-029→T001; FR-030→T003; FR-031→T003; FR-032→T014/T017/T023;
FR-033→T007–T011; FR-034→T014/T015/T021/T024; FR-035→T013;
FR-036→T015; FR-037→T017/T018; FR-038→T017/T020/T022/T024.
All 25 tasks are complete with commit and passing-test evidence; no orphans exist
in either direction.

**Follow-up & tidiness:** No `[TODO]`, `[DEFERRED]`, or `[OUT-OF-SCOPE]`
markers appear in the spec, plan, tasks, or branch commit messages. The final
diff contains no added TODO/FIXME, debugger, `console.log`, or ad hoc `print`
scaffolding. No `[tidiness]` findings remain.

---

## Lessons Learned

- Exact-treatment delivery became reproducible only after score authorization
  replayed the original qualification evidence and joined both the immutable
  execution-trace ID and its source digest. The shipped canonical materializer
  prevents treatment construction from drifting across callers.
- Trace IDs, role names, and caller-resealed digests were not sufficient
  authority by themselves. Corpus membership must join the canonical fixture
  manifest and admitted-route evidence, while ballots, adjudication, rubric
  bindings, and analysis decisions must be recomputed rather than trusted from
  caller summaries.
- G56R-004 through G56R-010 should reuse the governed corpus, qualification
  schemas, replayable score bundles, create-only freeze outputs, and
  calibration-only boundary. The materializer remains shipped runner source;
  fixtures, scorers, and statistical evidence remain repository test assets,
  with release payloads and reference pages refreshed only from their authored
  sources.
- Later cohorts must refresh capability authority after client, account,
  catalog, or official-source-ledger invalidation. Fixture, scorer, rubric, or
  partition version changes invalidate affected scores and decisions. Each
  cohort must freeze its numeric plan before outcomes, preserve disjoint
  partitions, and use multi-cluster evidence for cluster-aware inference.

---

## Project Structure Reference

```text
speckit-pro/
  speckit_pro_runner/                   # shipped canonical materializer
tests/speckit-pro/
  layer6-efficiency/
    contracts/                          # treatment and G56R-003 evidence contracts
    fixtures-codex/                     # governed role fixtures
    lib/                                # thin runner/scorer/statistics adapters
    run-efficiency-benchmarks.py        # retained smoke-only runner
  unit/                                 # deterministic unit and replay tests
docs/ai/
  research/                             # source ledger, freezes, evidence reports
  specs/
    .process/                           # design concept and workflow exhaust
specs/
  g56r-003-evaluation-runner-scoring/   # review-visible SpecKit contracts
```

Capability path: official Codex model/developer-command documentation -> pinned
Codex CLI 0.145.0 live catalog -> G56R-001 source ledger -> immutable G56R-002
capability/treatment evidence -> G56R-003 additive snapshot, runner, scorer,
and analysis contracts. Confidence is high for the pinned runtime and local
repository contracts; later accounts, clients, and catalog revisions require a
new versioned snapshot.
