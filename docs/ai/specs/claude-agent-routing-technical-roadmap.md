# Claude Code Agent Model Routing and Graceful Fallback Implementation Roadmap

**Select one evidence-backed preferred model/effort route and ordered qualified
fallbacks for each named Claude Code agent, resolve the first compatible route
from probed runtime capabilities at session preflight, and ship the complete
matrix in one consistent payload without changing any agent's safety, tool, or
mutation contract.**

This document defines the SPEC catalog for capability-based Claude Code agent
routing. Each SPEC maps to an explicit acceptance-criteria subset in the source
PRD and is prepared for `$speckit-scaffold-spec CAR-NNN`.

**Source PRD:** [../../prd-claude-agent-routing.md](../../prd-claude-agent-routing.md)
**Roadmap MOC:** [claude-agent-routing-roadmap-MOC.md](claude-agent-routing-roadmap-MOC.md)
**Shared parity contract:** [agent-routing-parity-contract.md](agent-routing-parity-contract.md)
**Shared manifest schema:** [../research/agent-route-candidate-manifest.schema.json](../research/agent-route-candidate-manifest.schema.json)
**Spec ID prefix:** `CAR-###`
**Proposed branch:** `claude/agent-routing-fallback`
**Status:** Draft; dependency graph approved 2026-07-12; CAR-001 evidence
parity amendment in review; CAR-002 blocked until that amendment merges

**Parity note:** This roadmap is the Claude half of the shared twelve-agent
catalog. The Codex half lives in the companion Codex routing roadmap (PR #330
as amended by the parity PR #338); the two catalogs mirror each other and
diverge only for platform-specific implementation requirements.

---

## Roadmap Overview

The effort is decomposed into **11 specifications** across **8 dependency
tiers**.

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | CAR-001 | Candidate route baseline and role contracts | Sequential spike |
| 2 | CAR-002 | Capability probing, telemetry profile, and exact treatment | Sequential foundation |
| 3 | CAR-003 | Evaluation runner, fixtures, scoring, and statistics | Sequential foundation; two required work packages |
| 4 | CAR-004 | Policy controls and adaptive comparators | Sequential foundation |
| 5 | CAR-005 | Availability, fallback, and recovery simulation | Sequential foundation |
| 6 | CAR-006 | Route-policy manifest, materializer, session preflight, and override validation | Sequential framework slice |
| 7 | CAR-007, CAR-008, CAR-009, CAR-010 | Qualify four disjoint agent cohorts | Parallel after CAR-006; serialize shared regeneration |
| 8 | CAR-011 | Compose final identities, rebuild payload, run installed UAT, and prove release readiness | Sequential integration |

**Execution order:** CAR-001 -> CAR-002 -> CAR-003 -> CAR-004 ->
CAR-005 -> CAR-006 -> CAR-007 + CAR-008 + CAR-009 + CAR-010 ->
CAR-011

**Implementation boundary:** This sequence has no external prerequisite, but
its internal dependencies still apply: CAR-001 implementation is complete and
archived, while its official-source evidence parity amendment must merge before
CAR-002 can be scaffolded. No installer exists or is introduced on the Claude
side - agents
auto-load from the shipped payload - so CAR-006 builds the route-policy
manifest, materializer drift gate, and read-only session-preflight resolver
instead of a copy step.

### Evidence authority

CAR evidence must satisfy the shared parity contract and manifest schema.
Platform capability claims may cite only canonical Anthropic documentation
under `code.claude.com/docs/**` or `platform.claude.com/docs/**`. Repository
state, pinned runtime captures, and governed evaluations remain authoritative
for production qualification, but cannot establish undocumented platform
behavior. The historical CAR-001 report remains available for provenance; its
v2 amendment is the active handoff for downstream specifications.

### Candidate-route starting hypotheses

This table records hypotheses, not a pre-approved route table. CAR-001 derives
the candidate set from official model guidance and probed capability evidence.
CAR-002 freezes the executable subset before CAR-003 scores outcomes. Current
baselines are the shipped frontmatter pins (all at `effort: max`); the effort
search itself starts at the documented default per AC-2.1.

| Agent | Current source baseline | Starting hypothesis | Effort search | Required challengers |
|---|---|---|---|---|
| `phase-executor` | opus / max | opus | default, ascend if needed, then descend | Every role-eligible probed model, including fable when probed available |
| `implement-executor` | opus / max | opus | default, ascend if needed, then descend | Every role-eligible probed model, including fable when probed available |
| `analyze-executor` | opus / max | opus | default, ascend if needed, then descend | Every role-eligible probed model, including fable when probed available |
| `checklist-executor` | opus / max | opus | default, ascend if needed, then descend | Every role-eligible probed model, including bounded-work haiku |
| `uat-runbook-author` | sonnet / max | sonnet | default, ascend if needed, then descend | Every role-eligible probed model, including bounded-work haiku |
| `clarify-executor` | opus / max | opus | default, ascend if needed, then descend | Every role-eligible probed model |
| `domain-researcher` | sonnet / max | sonnet | default, ascend if needed, then descend | Every role-eligible probed model |
| `codebase-analyst` | sonnet / max | sonnet | default, ascend if needed, then descend | Every role-eligible probed model, including bounded-work haiku |
| `spec-context-analyst` | sonnet / max | sonnet | default, ascend if needed, then descend | Every role-eligible probed model, including bounded-work haiku |
| `consensus-synthesizer` | sonnet / max | sonnet | default, ascend if needed, then descend | Every role-eligible probed model, including bounded-work haiku |
| `gate-validator` | sonnet / max | sonnet | default, ascend if needed, then descend | Every role-eligible probed model, including bounded-work haiku |
| `autopilot-fast-helper` | None - net-new parity addition (Codex baseline: Spark helper) | haiku with explicit low effort | explicit effort search | Every probed latency-oriented candidate plus a validated no-helper path |

### Route, evidence, and identity contract

A route is a complete qualified tuple, not a model name:

```text
route = explicit model (shipped alias + qualified resolved model ID)
      + explicit effort
      + instruction_hash
      + required model and modality capabilities
      + tool and skill contract
      + mutation contract (disallowedTools, tools omission, maxTurns)
      + supported client range
      + qualification evidence
```

Fallback may change only the approved model and effort for the same named
agent. It preserves instructions, output contract, mutation boundary, tools,
and skills. Ordered fallback is SpecKit Pro policy honored at dispatch time
through the documented per-invocation model parameter; it is not represented
as a native subagent-frontmatter fallback field, and shipped agent files are
never mutated at runtime.

| Identity | Created by | Required contents |
|---|---|---|
| `agent_contract_id` | CAR-001 | Named role plus safety, grounding, mutation, tool, and output contracts |
| `candidate_route_id` | CAR-001/CAR-002 | Candidate model/effort, contract and instruction hashes, required capabilities, and rationale |
| `telemetry_profile_id` | CAR-002 | Pinned client and mandatory, conditional, derived, and unavailable fields |
| `runtime_capability_snapshot_id` | CAR-002 or session preflight | Client version, probed model IDs, alias-to-ID bindings, supported efforts, probe method, timestamp, and raw evidence |
| `experiment_policy_id` | CAR-003 | Corpora, partitions, scorers, analysis plan, budgets, terminal policy, and treatment controls |
| `execution_trace_id` | CAR-003 | Assigned route, effective-route evidence, result, raw resource observations, retries, terminal state, and treatment integrity |
| `route_resolution_id` | CAR-002 schema; CAR-003/CAR-006 records | Preferred and effective route, fallback index, reason, snapshot, attempted routes, and timestamp |
| `resolved_agent_policy_id` | CAR-006 schema/fixtures; CAR-011 final records | Exact shipped frontmatter-plus-body content hash and selected effective route |
| `agent_route_policy_id` | CAR-007 through CAR-010 | Named agent, preferred route, ordered qualified fallbacks, hard contract, evidence, client bounds, and invalidation rules |
| `core_routing_policy_id` | CAR-011 | Ordered mapping of the eleven required named agents to final route-policy IDs |
| `optional_helper_policy_id` | CAR-011 | Final helper route policy, approved fallbacks, and no-helper contract |
| `resolved_installation_id` | CAR-011 | dist/claude payload tree hash plus installed-cache proof binding shipped agents to resolved policies |
| `release_policy_id` | CAR-011 | Final core/helper identities, preflight/materializer version, evidence lock, UAT, invalidation rules, and bounded claims |

Early traces must not require the final aggregate identities before CAR-011
creates them.

### Qualification and release-decision rule

- Deterministic role contract, grounding/evidence, and safety checks are hard
  gates; quality and reliability floors plus production non-inferiority pass
  before any resource ranking.
- The selection rule among passing candidates is one predeclared
  environment-independent weighted scalar over the raw token vector (input,
  cache-write by TTL class, cache-read, output) with coefficients pinned from
  a dated published API price-sheet revision, labeled diagnostic-derived; the
  complete raw vector, duration, retries, and compaction are always reported.
- Effort search starts at the documented default (`high`), ascends to the
  first stable pass when necessary, then descends and boundary-retests to the
  lowest stable ordinary effort. The current uniform `max` pins are the
  immutable comparator, not the search origin.
- Exact treatment means real `speckit-pro:<name>` dispatch or a canonical
  materializer rendering proven equivalent; bare prompt emulation is
  smoke-only. The environment contract freezes fast mode off, a pinned client
  range, a pinned parent-session model and effort, and an unset
  `CLAUDE_CODE_SUBAGENT_MODEL`; scored campaigns run API-key-authenticated
  with at least one subscription-authenticated installed smoke row, and no
  run produces a plan-based claim.
- Screening, selection, cohort lock, and integrated confirmation use disjoint
  partitions; the untouched confirmation corpus is used exactly once.
- A platform-initiated route change - any observed model ID differing from the
  resolved qualified ID, including alias re-pointing - makes a run non-scorable
  for the requested route and is never reported as plugin fallback.
- Unpinned, adaptive, and orchestration-changing controls are frozen before
  cohort selection and compared with the final static core during integrated
  confirmation; a dominant control restricts efficiency wording.
- Evidence wins: no model generation, alias, or product tier is forced into a
  role when it fails.

## Reviewability Contract

Every implementation spec must fit the repository's human review budget. Warn
above approximately 400 reviewable production LOC, 6 production files, or 15
total files; block-sized work must split unless an existing typed exception
legitimately applies. Generated payloads, tests, and documentation still count
toward reviewer load even where they do not count as production LOC.

**Estimator advisory:** The Python-authoritative `estimate-spec-size`
operation was run on 2026-07-12 with the documented convention: one user
story, the declared total-file estimate, the Scope-bullet count excluding the
INVEST line as functional requirements, and `new_vs_modify=modify`; CAR-001
uses the spike flag and CAR-010 uses `new` because its helper agent is
net-new. CAR-003 (502 LOC, warn) must preserve its two declared work packages,
and CAR-010 (450 LOC, warn) must preserve its declared helper-definition
versus qualification-evidence split. Every scaffold reruns the estimator when
scope or file counts change.

## Dependency Graph

```text
CAR-001 Candidate Route Baseline and Role Contracts
    |
    v
CAR-002 Capability Probing, Telemetry Profile, and Exact Treatment
    |
    v
CAR-003 Evaluation Runner, Fixtures, Scoring, and Statistics
    |
    v
CAR-004 Policy Controls and Adaptive Comparators
    |
    v
CAR-005 Model Availability, Fallback, and Recovery Simulation
    |
    v
CAR-006 Route-policy Manifest, Materializer, Preflight, and Override
    |
    +--> CAR-007 Quality-critical Executor Routing ---------+
    +--> CAR-008 Structured-work Agent Routing -------------+
    +--> CAR-009 Read-only and Orchestration Routing -------+
    +--> CAR-010 Optional Helper and No-helper Path --------+
                                                            |
                                                            v
                 CAR-011 Final Composition, Installed UAT, and Release Proof
```

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|---|---|---|---|---|
| CAR-001 | Candidate Route Baseline and Role Contracts | Evidence Amendment In Review | [.process/CAR-001-workflow.md](.process/CAR-001-workflow.md) | Merge official-source v2 amendment |
| CAR-002 | Capability Probing, Telemetry Profile, and Exact-Treatment Contract | Blocked | - | Revalidate the merged v2 source ledger |
| CAR-003 | Evaluation Runner, Fixtures, Scoring, and Statistical Analysis | Pending | - | Blocked by CAR-002 |
| CAR-004 | Policy Controls and Adaptive Comparators | Pending | - | Blocked by CAR-003 |
| CAR-005 | Model Availability, Fallback, and Recovery Simulation | Pending | - | Blocked by CAR-004 |
| CAR-006 | Route-policy Manifest, Materializer, Preflight, and Strict Override | Pending | - | Blocked by CAR-005 |
| CAR-007 | Quality-critical Executor Routing | Pending | - | Blocked by CAR-006 |
| CAR-008 | Structured-work Agent Routing | Pending | - | Blocked by CAR-006 |
| CAR-009 | Read-only Reasoning and Orchestration-support Agent Routing | Pending | - | Blocked by CAR-006 |
| CAR-010 | Optional Latency-first Helper Routing and No-helper Path | Pending | - | Blocked by CAR-006 |
| CAR-011 | Payload, Installed Skill UAT, Fallback Proof, and Release Integration | Pending | - | Blocked by CAR-007 through CAR-010 |

**Status legend:** Pending | Ready | In Progress | In Review | Complete | Blocked

---

## Specification Sections

### CAR-001: Candidate Route Baseline and Role Contracts

**Priority:** P1 | **Depends On:** None | **Enables:** CAR-002

**Implementation Status:** Runtime-neutral research spike complete / archived;
official-source evidence parity amendment in review. PR #350 merged on
2026-07-15 at
`725be949b856724a073622900bd168d29b2f4603`; the active spec folder was removed
in `.specify/memory/archive-reports/2026-07-15-car-001-post-merge-hygiene.md`.
Canonical artifacts now live at `docs/ai/research/claude-agent-route-candidates.md`
and `docs/ai/research/claude-agent-route-candidate-manifest.json`. CAR-002 must
consume the schema-v2 amendment and pass its source-ledger gate before it can
begin capability probing.

**Goal:** Produce the dated, cited candidate-route and role-contract handoff
needed for capability probing without changing shipped defaults.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 0 (spike) | Suggested slices: 1 | Status: ok |
Production files: 0 | Total files: approximately 3 |
Budget result: research spike; time-boxed, LOC sizing not applicable

**Scope:**

- Inventory the eleven current `speckit-pro/agents/*.md` definitions plus the
  net-new `autopilot-fast-helper` contract derived from the Codex helper under
  the parity principle, recording each agent's immutable production route or
  its recorded absence, instructions, role boundary, safety/grounding/mutation
  contract (`disallowedTools`, `tools` omission, `maxTurns`), output contract,
  expected tool/skill use, and representative tasks.
- Publish a versioned `agent_route_candidate_manifest` covering all twelve
  named agents. Create `agent_contract_id` and provisional
  `candidate_route_id` records for every agent. Each candidate records the
  shipped alias plus expected resolved model ID, an explicit effort,
  instruction hash, required capabilities, mutation contract, rationale, known
  incompatibilities, evidence requirements, and invalidation triggers
  including alias re-pointing.
- Distinguish project-level candidate eligibility from environment-time
  availability. Record preferred-route hypotheses and fallback-candidate
  requirements without claiming that any candidate is executable; `fable`
  enters executor-class candidate sets and is excluded only by recorded probe
  or contract evidence.
- Record the immutable production-route inputs (the eleven current frontmatter
  alias/effort tuples and content hashes at the pinned plugin version; each
  alias→dated-ID resolution is deferred to CAR-002 probing, not recorded as
  settled) that CAR-003 will bind into the sole candidate and integrated
  comparator before screening.
- Build a primary-source fact table from official Anthropic subagent,
  model-configuration, effort, fast-mode, authentication, cost/monitoring, and
  pricing documentation. Label every undocumented behavior - including what
  happens when frontmatter names an unavailable model, and how alias
  re-pointing manifests - as an inference, open question, or proposed SpecKit
  Pro policy.
- Deliver the role contracts, provisional candidate manifest, fixture backlog,
  two-current/ten-missing fixture inventory, telemetry requirements,
  capability questions, and independent go/no-go handoff to CAR-002.
- INVEST rationale: the spike closes the research uncertainty that blocks safe
  capability probing and ends without depending on later telemetry results.

**Out of Scope:**

- Agent frontmatter, prompt, payload, or default changes.
- Live corpus execution, qualification, or fallback ordering.

**Key Files:**

- [proposed] `docs/ai/research/claude-agent-route-candidates.md`
- `speckit-pro/agents/*.md` - read-only inventory source
- `speckit-pro/codex-agents/autopilot-fast-helper.toml` - parity contract source
- `tests/speckit-pro/layer6-efficiency/` - current fixture-gap inventory source

---

### CAR-002: Capability Probing, Telemetry Profile, and Exact-Treatment Contract

**Priority:** P1 | **Depends On:** CAR-001 | **Enables:** CAR-003

**Goal:** Freeze the executable candidate set and a trustworthy trace contract
for the pinned Claude Code client before outcome-bearing evaluation.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 265 | Suggested slices: 1 | Status: ok |
Production files: 0 | Total files: approximately 10 |
Budget result: re-estimate at scaffold; probe, profile, and schema libraries

**Scope:**

- Implement `runtime_capability_snapshot` capture: a bounded exact invocation
  probe per candidate route (`claude -p --model <alias-or-id>` on a minimal
  fixed canary), plus the API models endpoint when the environment is
  API-key-authenticated. Record probed model IDs, alias-to-ID bindings,
  supported efforts by configuration acceptance, client version, probe
  method, timestamp, and raw evidence.
- Probe and record the undocumented unavailable-model behavior (hard error
  versus silent substitution) as a pinned platform fact; its result shapes the
  CAR-005 reason codes.
- Publish `telemetry_profile_id` for the pinned client: effective model from
  the per-model usage breakdown and transcript per-message records is
  `stable_native`; the raw token vector including cache-write TTL classes and
  cache-read is `stable_native`; client-side cost estimates are `derived`;
  effective reasoning effort is `derived_from_controlled_configuration` and
  never a returned value; nulls are preserved.
- Define `route_resolution_id` and exact-treatment replay schemas binding the
  named agent, explicit model and effort, instruction hash, mutation contract,
  dispatch namespace, parent-session configuration, client version, fast-mode
  state, and env-override proof (`CLAUDE_CODE_SUBAGENT_MODEL` unset).
- Define platform route-change detection: any observed model ID differing from
  the resolved qualified ID, including alias re-pointing, is recorded
  separately from resolver fallback and marks the run non-scorable for the
  requested route.
- Record the authentication mode of every run (API-key for scored campaigns,
  subscription for installed smoke) in the environment snapshot without
  producing plan-based claims.
- Validate success, null, unavailable, and misdelivery records with synthetic
  replay before any live scoring.
- INVEST rationale: one probing/telemetry seam gives every later cohort the
  same trustworthy treatment evidence without touching agent policies.

**Out of Scope:**

- Corpus execution, scoring, statistics, and fallback ordering.
- Payload or guidance changes.

**Key Files:**

- [proposed] `tests/speckit-pro/layer6-efficiency/lib/claude_capabilities.py`
- [proposed] `tests/speckit-pro/layer6-efficiency/lib/claude_trace_schema.py`
- [proposed] `tests/speckit-pro/unit/test-efficiency-claude-telemetry.py`
- `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py` - current runner (read-only reference)

---

### CAR-003: Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

**Priority:** P1 | **Depends On:** CAR-002 | **Enables:** CAR-004

**Goal:** Qualify preferred and fallback candidates reproducibly on governed
fixtures without consuming integrated-confirmation data.

**Reviewability Budget:** Primary surface: harness/fixtures |
Projected reviewable LOC: 502 | Suggested slices: 2 | Status: warn |
Production files: 0 | Total files: approximately 20 |
Budget result: warning-sized; must preserve the two declared work packages
below when scaffolded

**Required Work Package A - Treatment runner and materializer:**

- Replace prompt emulation for qualification with real dispatch: installed-
  plugin `claude -p` sessions that spawn `speckit-pro:<name>` and prove the
  spawn from the transcript (reusing the Layer 7 transcript-parsing approach),
  with the per-model usage breakdown proving the effective model.
- Implement the canonical Python materializer that parses `agents/*.md` into a
  canonical policy structure, renders equivalent evaluation configurations,
  and later backs the CAR-006 frontmatter drift gate.
- Classify treatment misdelivery separately from candidate quality; emit
  replayable `execution_trace_id` records carrying the raw token vector
  (input, cache-write by TTL class, cache-read, output), duration, retries,
  and terminal state.
- Demote the current prompt-emulation path to explicitly labeled smoke
  evidence; historical results remain `non_release_evidence`.
- Isolate cache state between arms so one arm cannot warm another's cache;
  billed cache writes make crossover directly distortive.

**Required Work Package B - Fixtures, scoring, and statistics:**

- Expand from two current role fixtures to a governed twelve-role corpus under
  `fixtures/<agent>/`. Use blinded adjudication for candidate quality failure,
  treatment-delivery failure, invalid fixture, invalid scorer, and
  infrastructure failure. A fixture/scorer change versions it and invalidates
  affected results.
- Add a gitignore allow rule so consolidated baselines
  (`results/consolidated-*.json`) commit while per-run outputs stay ignored,
  mirroring the committed Codex baseline convention.
- Freeze `experiment_policy_id`: disjoint screening/selection/cohort-lock/
  confirmation partitions, workload strata and weights from pre-treatment
  properties, the powered long-horizon stratum, acceptance checker, margins,
  alpha/power/multiplicity, task-level clustering, attrition thresholds, and
  `inconclusive => no qualification`.
- Bind the immutable production comparator: repository revision, plugin
  version, the eleven current frontmatter alias/effort tuples (dated-ID
  resolution supplied by the CAR-002 runtime capability snapshot, not the
  frontmatter), instruction hashes, mutation contracts, client version, and
  corpus snapshot.
- Implement A1 (documented-default effort screening), A2 (within-model effort
  boundary search), A3 (frozen pair comparison), Stage B (bounded prompt
  interaction), and Stage C (cohort locks) with the predeclared price-weighted
  scalar plus complete raw-vector reporting.
- Enforce campaign budgets: maximum raw-token use, wall time, candidate count,
  futility rules, racing method, and confirmation-entry cap frozen before
  outcome-bearing runs.
- Publish replayable statistics with task-level paired inference and the
  frozen analysis plan; no post-hoc threshold changes.
- INVEST rationale: the runner/materializer seam and the fixture/statistics
  seam are separable, independently testable, and jointly sufficient for every
  cohort spec.

**Out of Scope:**

- Final route policies, shipped defaults, and release confirmation.
- Production preflight and guidance changes.

**Key Files:**

- `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py` - current runner to demote to smoke
- [proposed] `tests/speckit-pro/layer6-efficiency/lib/agent_materializer.py`
- [proposed] `tests/speckit-pro/layer6-efficiency/lib/statistical_analysis.py`
- `tests/speckit-pro/layer6-efficiency/fixtures/` - two current dirs; ten proposed
- `tests/speckit-pro/layer6-efficiency/.gitignore` - allow rule for consolidated baselines
- [proposed] `tests/speckit-pro/unit/test-efficiency-claude-runner.py`

---

### CAR-004: Policy Controls and Adaptive Comparators

**Priority:** P1 | **Depends On:** CAR-003 | **Enables:** CAR-005

**Goal:** Define, exact-treatment validate, and freeze the policy-level
controls that bound the final static-policy efficiency claim.

**Reviewability Budget:** Primary surface: harness/fixtures |
Projected reviewable LOC: 250 | Suggested slices: 1 | Status: ok |
Production files: 0 | Total files: approximately 10 |
Budget result: re-estimate at scaffold; control fixtures plus registry entries

**Scope:**

- Define and content-address three frozen controls: unpinned (agents with
  `model` omitted or `inherit`, riding the session model), adaptive (a frozen
  escalation/de-escalation policy over qualified routes exercised through the
  documented dispatch-time model parameter), and orchestration-changing (a
  parallel multi-agent execution mode evaluated at policy level only).
- Freeze each control's execution contract, parameters, observable escalation
  signals, retry and cancellation bounds, and evidence requirements; adaptive
  controls cannot choose a model or effort outside the frozen candidate set.
- Freeze control-eligibility floors, dominance metrics and margins, confidence
  method, multiplicity position, and the untouched comparison partition
  CAR-011 will use.
- Freeze the messaging consequence: a materially dominant qualified control
  restricts release wording to measured improvement over the previous static
  baseline, never "efficient", "optimal", or "best measured".
- Validate control execution and telemetry through synthetic replay and smoke
  runs without consuming selection or confirmation partitions.
- INVEST rationale: controls are pure evaluation fixtures - freezing them
  early prevents post-hoc comparator construction without touching any
  shipped policy.

**Out of Scope:**

- Concluding dominance (CAR-011 owns the comparison).
- Any production adaptive routing feature.

**Key Files:**

- [proposed] `tests/speckit-pro/layer6-efficiency/fixtures-controls/`
- [proposed] analysis-plan registry entries under `tests/speckit-pro/layer6-efficiency/`
- [proposed] `tests/speckit-pro/unit/test-efficiency-claude-controls.py`

---

### CAR-005: Model Availability, Fallback, and Recovery Simulation

**Priority:** P1 | **Depends On:** CAR-004 | **Enables:** CAR-006

**Goal:** Prove bounded resolution and recovery semantics synthetically before
real route policies exist.

**Reviewability Budget:** Primary surface: harness/fixtures |
Projected reviewable LOC: 257 | Suggested slices: 1 | Status: ok |
Production files: 0 | Total files: approximately 10 |
Budget result: re-estimate at scaffold; replay fixtures plus reason-code tests

**Scope:**

- Build fixture route policies that simulate: preferred model absent from the
  probed environment (including a `fable`-unavailable case), effort
  unsupported for a model, probe unavailable, exact invocation probe success
  and failure, alias re-pointing, platform route change, and an unqualified
  `CLAUDE_CODE_SUBAGENT_MODEL` override.
- Define stable reason codes (`preferred_model_unavailable`,
  `effort_unsupported`, `capability_probe_unavailable`,
  `treatment_probe_failed`, `no_safe_route`) aligned with the CAR-002 probed
  unavailable-model behavior.
- Reject fallback loops, unqualified adjacent models, generic-agent
  substitution, and silent `inherit` materialization; bound probe attempts,
  retries, and fan-out.
- Simulate no-safe-route behavior as report-only: the preflight emits the
  unresolved agent, attempted routes, rejection reasons, and remediation, and
  never mutates shipped agent files; consumer recovery is the previous plugin
  release.
- Simulate helper-unavailable behavior: the helper is simply not consulted and
  the validated no-helper path continues without failing required-agent
  resolution.
- Prove retry exhaustion, rollback guidance, and deterministic replay of every
  scenario.
- INVEST rationale: recovery semantics are provable on synthetic fixtures
  before any live route exists, so the preflight lands already tested.

**Out of Scope:**

- Production checkpoint/resume scheduling and live UAT.
- Real route qualification.

**Key Files:**

- [proposed] `tests/speckit-pro/layer6-efficiency/fixtures-fallback/`
- [proposed] `tests/speckit-pro/unit/test-route-fallback-simulation.py`

---

### CAR-006: Route-policy Manifest, Materializer, Preflight, and Strict Override

**Priority:** P1 | **Depends On:** CAR-005 |
**Enables:** CAR-007 through CAR-010

**Goal:** Implement the reusable resolution framework against fixture route
policies without creating final route aggregates and without inventing an
installer.

**Reviewability Budget:** Primary surface: runner/helpers |
Projected reviewable LOC: 265 | Suggested slices: 1 | Status: ok |
Production files: approximately 3 | Total files: approximately 10 |
Budget result: re-estimate at scaffold; manifest schema, doctor operation, and
drift gate

**Scope:**

- Define the plugin-owned, versioned, content-addressed `agent-route-policy`
  manifest schema: per named agent, the preferred route (shipped alias plus
  qualified resolved model ID and explicit effort), ordered qualified
  fallbacks, hard contract reference, and invalidation triggers including
  alias re-pointing.
- Wire the CAR-003 canonical materializer as a frontmatter drift gate: shipped
  `agents/*.md` frontmatter must equal the manifest's materialized preferred
  route; `inherit` or omitted values fail the gate for routed fields.
- Implement a read-only runner doctor/preflight operation that captures a
  bounded capability snapshot, resolves each agent's first compatible route
  (preferred, then ordered fallbacks), and emits a `route_resolution_id`
  report with stable reason codes; it performs no writes and never mutates
  shipped files.
- Document the dispatch-time fallback contract for autopilot: when the
  preflight reports a fallback, dispatch passes the resolved model through the
  documented per-invocation model parameter; the named agent and its contract
  never change.
- Implement override validation: read `CLAUDE_CODE_SUBAGENT_MODEL` and
  settings-level overrides, validate the resulting tuple for every named agent
  against qualified routes, and report non-qualified overrides loudly;
  release claims exclude overridden environments.
- Add a thin, non-blocking SessionStart warning that surfaces unresolved
  routes or non-qualified overrides, mirroring the existing missing-CLI
  warning pattern.
- Prove the framework against CAR-005 fixture policies with fake-home unit
  tests and suite-manifest membership; Python 3.11+ standard library only.
- INVEST rationale: one framework slice gives all four cohort specs the same
  resolution, drift-gate, and reporting surface while shipping no route
  decision itself.

**Out of Scope:**

- Final preferred/fallback selection (CAR-007 through CAR-010).
- Any installer, destination copy step, or Codex-side change.
- Per-agent user override features.

**Key Files:**

- [proposed] `speckit-pro/speckit_pro_runner/helpers/route_policy.py`
- `speckit-pro/speckit_pro_runner/helpers/registry.py` - register the doctor operation
- `speckit-pro/hooks/hooks.json` - SessionStart warning wiring
- [proposed] `tests/speckit-pro/unit/test-route-policy-preflight.py`

---

### CAR-007: Quality-critical Executor Routing

**Priority:** P1 | **Depends On:** CAR-006 | **Enables:** CAR-011

**Goal:** Produce final preferred and ordered fallback route policies for
phase execution, TDD implementation, and analysis/remediation.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 257 | Suggested slices: 1 | Status: ok |
Production files: approximately 3 | Total files: approximately 10 |
Budget result: re-estimate at scaffold; three agent policies plus role evidence

**Scope:**

- Screen every executable, role-eligible candidate for `phase-executor`,
  `implement-executor`, and `analyze-executor` from the frozen manifest,
  including `fable` when probed available; named models are hypotheses, not
  predetermined winners.
- Score real Specify/Plan/Tasks, strict TDD implementation, and full Analyze
  remediation fixtures, not generic coding prompts.
- Apply A1/A2/A3, Stage B, Stage C, exact treatment, and the shared
  statistical plan without consuming integrated-confirmation data.
- Emit one final `agent_route_policy_id` per named agent with preferred route,
  ordered independently qualified fallbacks, hard contract, evidence, client
  bounds, and invalidation triggers.
- Prove all policies against CAR-006 preflight and drift-gate fixtures, then
  update only cohort-specific frontmatter and the directly tied guidance prose
  for truthfulness.
- Keep TDD, grounding, artifact, validation, and mutation contracts hard
  across route, prompt, and fallback evaluation.
- INVEST rationale: the three highest-risk mutating roles share one
  quality-first evaluation seam and ship with complete cohort-specific
  evidence.

**Out of Scope:**

- Structured-work, read-only, orchestration-support, and helper routes.

**Key Files:**

- `speckit-pro/agents/phase-executor.md`
- `speckit-pro/agents/implement-executor.md`
- `speckit-pro/agents/analyze-executor.md`
- `tests/speckit-pro/layer6-efficiency/fixtures/` - cohort fixtures/results

---

### CAR-008: Structured-work Agent Routing

**Priority:** P1 | **Depends On:** CAR-006 | **Enables:** CAR-011

**Goal:** Produce final preferred and ordered fallback route policies for
checklist remediation and UAT runbook authoring.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 210 | Suggested slices: 1 | Status: ok |
Production files: approximately 2 | Total files: approximately 8 |
Budget result: re-estimate at scaffold; two agent policies plus role evidence

**Scope:**

- Screen every executable, role-eligible candidate for `checklist-executor`
  and `uat-runbook-author`, including bounded-work `haiku` when its tool and
  output contracts pass.
- Require complete all-severity checklist remediation and executable,
  plain-English, non-circular, acceptance-criteria-traceable UAT runbooks as
  hard gates.
- Preserve each role's write boundary and fail-open/fail-closed behavior
  across every route and fallback.
- Apply the staged pair, prompt-interaction, and cohort-lock design with exact
  treatment for every candidate before integration.
- Emit final `agent_route_policy_id` records with complete route order,
  contract, evidence, client bounds, and invalidation rules.
- INVEST rationale: two structured-output mutators share a measurable contract
  and ship independently of deep executors and analysts.

**Out of Scope:**

- Quality-critical executors, read-only/orchestration analysts, and the
  helper.

**Key Files:**

- `speckit-pro/agents/checklist-executor.md`
- `speckit-pro/agents/uat-runbook-author.md`
- `tests/speckit-pro/layer6-efficiency/fixtures/` - cohort fixtures/results

---

### CAR-009: Read-only Reasoning and Orchestration-support Agent Routing

**Priority:** P1 | **Depends On:** CAR-006 | **Enables:** CAR-011

**Goal:** Produce final preferred and ordered fallback route policies for
clarification, research, codebase analysis, project-context analysis,
consensus synthesis, and gate validation.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 392 | Suggested slices: 1 | Status: ok |
Production files: approximately 6 | Total files: approximately 16 |
Budget result: re-estimate at scaffold; six agent policies plus bounded role
fixtures; declare an analysts-versus-orchestration-support work-package split
if a scaffold re-estimate warns

**Scope:**

- Screen every executable, role-eligible candidate for `clarify-executor`,
  `domain-researcher`, `codebase-analyst`, `spec-context-analyst`,
  `consensus-synthesizer`, and `gate-validator`; retain lighter models only
  when they preserve the complete role contract.
- Hard-gate read-only behavior (the shared `disallowedTools` denylist),
  source-domain separation, citations or file locators, abstention, and
  structured return formats.
- Hard-gate the three-analyst consensus-synthesis contract (agreement rule,
  confidence assessment, actionable synthesized answer) and the structured
  gate-validation evidence contract for the two orchestration-support agents,
  reusing and extending their two existing fixtures.
- Apply A1/A2/A3, Stage B, Stage C, exact treatment, progressive effort
  search, and the shared statistical plan without consuming
  integrated-confirmation data.
- Emit one final `agent_route_policy_id` per named agent with preferred route,
  ordered independently qualified fallbacks, hard contract, evidence, client
  bounds, and invalidation triggers; one model is never forced across all six
  roles.
- Prove all policies against CAR-006 preflight and drift-gate fixtures.
- Keep this cohort layout mirrored with the Codex catalog, where the same two
  orchestration-support agents join the read-only cohort as parity additions.
- Update only cohort-specific frontmatter and directly tied guidance prose.
- INVEST rationale: one read-only evidence seam preserves six distinct
  perspective and orchestration-support contracts without mutation conflicts.

**Out of Scope:**

- Mutating executors, UAT authoring, and helper routing.

**Key Files:**

- `speckit-pro/agents/clarify-executor.md`
- `speckit-pro/agents/domain-researcher.md`
- `speckit-pro/agents/codebase-analyst.md`
- `speckit-pro/agents/spec-context-analyst.md`
- `speckit-pro/agents/consensus-synthesizer.md`
- `speckit-pro/agents/gate-validator.md`
- `tests/speckit-pro/layer6-efficiency/fixtures/consensus-synthesizer/` - existing fixture
- `tests/speckit-pro/layer6-efficiency/fixtures/gate-validator/` - existing fixture

---

### CAR-010: Optional Latency-first Helper Routing and No-helper Path

**Priority:** P1 | **Depends On:** CAR-006 | **Enables:** CAR-011

**Goal:** Introduce the net-new `autopilot-fast-helper` under the parity
principle, select its qualified routes, and prove that autopilot remains valid
when no helper route is available.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 450 | Suggested slices: 2 | Status: warn |
Production files: approximately 3 | Total files: approximately 8 |
Budget result: warning-sized because the helper is net-new (`new_vs_modify` =
new); preserve the declared helper-definition versus qualification-evidence
split when scaffolded

**Scope:**

- Author `speckit-pro/agents/autopilot-fast-helper.md` as a net-new named
  plugin agent per current official subagent documentation, mirroring the
  Codex helper's contract: read-only, advisory, bounded to context
  compression, triage of large tool outputs, and search/query drafting, with a
  comprehensive no-tool `disallowedTools` denylist (prompt-context-only — denies
  reads/web too, stricter than the analysts' read-only denylist; the exact list
  finalized here) and a small `maxTurns`.
- Materialize an explicit starting route hypothesis of `haiku` with explicit
  low effort; never ship an omitted or inherited value for routed fields.
- Screen every probed latency-oriented candidate under the same route and
  exact-treatment rules as required agents; evidence decides the final route.
- Wire conditional helper dispatch into the autopilot skill and its
  references - compression, triage, and query-drafting touchpoints only -
  including the no-helper contract prose, mirroring how the Codex skills
  reference their helper.
- Measure functionality, latency, spawn reliability, raw resource evidence,
  resolution reasons, and result use on a helper scorecard; keep helper
  qualification separate from the required eleven-agent core statistic.
- Prove autopilot continuation when the helper is omitted, unavailable, not
  consulted, not invoked, or cannot spawn; helper absence is never a
  required-core resolution failure.
- Emit the helper's final `agent_route_policy_id` with preferred route,
  ordered qualified fallbacks, and the frozen no-helper contract; CAR-011
  creates the aggregate `optional_helper_policy_id` after integration.
- INVEST rationale: the optional leaf can be selected, omitted, or rejected
  without changing any required agent, and its skill wiring is separable from
  its qualification evidence.

**Out of Scope:**

- General SDD reasoning and all other agent routes.
- Any entitlement- or plan-conditional behavior.

**Key Files:**

- [proposed] `speckit-pro/agents/autopilot-fast-helper.md` - net-new parity addition
- `speckit-pro/skills/speckit-autopilot/SKILL.md` - conditional helper dispatch and no-helper contract
- `speckit-pro/codex-agents/autopilot-fast-helper.toml` - parity contract source (read-only)
- [proposed] `tests/speckit-pro/layer6-efficiency/fixtures/autopilot-fast-helper/`

---

### CAR-011: Payload, Installed Skill UAT, Fallback Proof, and Release Integration

**Priority:** P1 | **Depends On:** CAR-007, CAR-008, CAR-009, CAR-010 |
**Enables:** Release

**Goal:** Compose, ship, and prove one internally consistent twelve-agent
routing policy whose skills use the named agents and whose preflight behaves
safely when a preferred route is unavailable.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 395 | Suggested slices: 1 | Status: ok |
Production files: approximately 2 | Total files: approximately 15 |
Budget result: re-estimate at scaffold; split release evidence from source
fixes if warned

**Scope:**

- After all cohort locks, create final `resolved_agent_policy_id` records and
  `core_routing_policy_id` from the eleven required `agent_route_policy_id`
  values; create `optional_helper_policy_id` from the helper route policy and
  no-helper contract; bind the dist/claude payload tree hash and
  installed-cache proof into `resolved_installation_id`; then bind the
  evidence, preflight/materializer version, UAT, invalidation rules, and
  bounded claims into `release_policy_id`.
- Rebuild `dist/claude` through the Python-authoritative payload builder and
  the artifact refresh ritual; never hand-edit generated agent files.
- Reconcile source, payload, installed-cache, benchmark, rollback, and release
  packet identities. Source and payload retain twelve definitions - eleven
  required agents plus the helper - and the materializer drift gate passes on
  the final tree.
- Update active guidance with route resolution, fallback, override validation,
  preflight reporting, and rollback: the autopilot skill's model/effort
  prerequisites, its references that encode per-agent model and effort prose,
  and the public install documentation; the superseded "max thinking on every
  agent" statement is replaced by the evidence-backed route table.
- Run final integrated confirmation of the assembled preferred eleven-agent
  core against the immutable production core on untouched data. Require all
  safety, quality, reliability, accepted-workflow, raw-resource, duration,
  retry, compaction, attrition, and powered long-horizon gates, including the
  predeclared environment-independent resource-superiority endpoint. Passing
  proves bounded component-wise improvement, not global optimality.
- Compare the final static core with the frozen CAR-004 controls on
  predeclared secondary arms. A materially dominant qualified control
  restricts efficiency wording under the frozen messaging rule.
- Publish `skill_agent_usage_manifest` for every active Claude skill entry
  point and all twelve source agents. Update each applicable skill to name the
  installed agent (`speckit-pro:<name>`), triggering condition, allowed route
  resolution, and result-consumption contract; classify other mappings as
  conditional, prohibited, or not applicable.
- Run representative workflows through actual installed Claude skills. Across
  the set, prove every one of the eleven required core agents was spawned by
  its namespaced name and that its returned result affected a decision,
  artifact, or validation. Direct harness injection, generic-agent
  substitution, missing required spawn, or unconsumed result fails release
  proof. Test the helper in a separate workflow and prove the no-helper path;
  no single workflow must spawn all twelve agents.
- Bind every installed UAT trace as:

  ```text
  skill_id
    -> skill_instruction_hash
    -> named_agent (speckit-pro namespace)
    -> route_resolution_id
    -> effective_model_evidence_or_null
    -> effort_configuration_evidence
    -> exact_treatment_evidence
    -> returned_result_hash
    -> consuming_decision_or_artifact
  ```

- Prove installed preferred selection and the bounded failure scenarios:
  preferred model absent, effort unsupported, probe unavailable with the
  allowed exact probe, treatment-probe failure, qualified and unqualified
  platform route-change handling, no safe required route with report-only
  behavior and the shipped policy untouched, helper unavailable with
  no-helper continuation, non-qualified override disclosure, and rollback to
  the previous plugin release.
- Run deterministic source, payload, installed-cache, default-suite,
  active-path, benchmark replay, and skill-driven integration gates
  appropriate to the implementation changes. Produce a public-readable
  evidence packet with selected/rejected routes, fallback order, controls,
  long-horizon results, known gaps, review order, rollback, and rerun
  triggers.
- INVEST rationale: the integration slice proves independently selected route
  policies form a safe consumer-installable system and reopens selection when
  they do not.

**Out of Scope:**

- Global optimality across every complete twelve-agent assembly.
- Manual version bumps; release-please owns release versioning.

**Key Files:**

- `scripts/build-plugin-payloads.py`
- `scripts/refresh-release-artifacts.py`
- `speckit-pro/speckit_pro_runner/gates/payloads.py`
- `dist/claude/speckit-pro/` - generated output only
- `speckit-pro/skills/speckit-autopilot/SKILL.md`
- `speckit-pro/skills/speckit-autopilot/references/` - model/effort prose surfaces
- `docs-site/src/content/docs/install/claude-code.md`
- `tests/speckit-pro/layer1-structural/validate-agents.py`
- `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py`
- `tests/speckit-pro/layer7-integration/` - skill-driven spawn and result-use proof
- `docs/ai/specs/.process/` - release and live-UAT evidence

---

## Environment & Deployment Context

### Existing Infrastructure (No Changes Needed)

| Resource | Detail |
|---|---|
| Claude agent source | Eleven Markdown files under `speckit-pro/agents/`; the twelfth (helper) arrives via CAR-010 |
| Delivery | Plugin agents auto-load from the shipped payload; no installer, no destination copy, no restart step |
| Evaluation | Python Layer 6 prompt-emulation runner, two existing role fixtures, git-ignored results; current results cannot qualify production routes |
| Payload build | Python 3.11+ `scripts/build-plugin-payloads.py` and runner payload gate |
| Release | release-please plus deterministic source/payload/install/release gates |

### Changes Required

| Change | Where | Detail |
|---|---|---|
| Candidate route record | [proposed] `docs/ai/research/` | Dated official facts, role contracts, candidate routes, capability questions, and fixture backlog |
| Capability and telemetry adapter | [proposed] Layer 6 Python libraries | Runtime capability snapshot, exact invocation probe, telemetry profile, treatment and route-change trace schemas |
| Route evaluation | Layer 6 Python harness | Canonical materializer, twelve-role fixtures, disjoint corpora, scoring, statistics, raw resource evidence, and long-horizon stratum |
| Fallback simulation | [proposed] Layer 6 replay fixtures | Availability, effort, probe, alias re-pointing, override, no-safe-route, helper, and retry cases |
| Route-policy framework | Runner helpers, registry, and hooks | Route-policy manifest, frontmatter drift gate, read-only doctor/preflight, override validation, SessionStart warning |
| Agent route policies | `speckit-pro/agents/*.md` | Preferred/fallback order remains project-owned; shipped frontmatter materializes one explicit route per agent |
| Skill-to-agent orchestration | `speckit-pro/skills/` and Layer 7 | Namespaced named-agent dispatch plus installed spawn and result-consumption proof for all required agents and the conditional helper |
| Generated payload | `dist/claude/` | Rebuild from source and refresh integrity evidence |
| Consumer guidance | Autopilot skill, references, and docs surfaces | Route resolution, fallback, override validation, effective route, rollback, and no-helper behavior |

### Local Development Setup

| Requirement | How |
|---|---|
| Python | Python 3.11+ standard-library runner already required by SpecKit Pro |
| Claude Code | Pinned client range with plugin-agent support and probed candidate routes |
| Live evaluation | Explicit developer-local campaign and workflow budgets in a dedicated API-key-authenticated environment, plus one subscription-authenticated installed smoke row; never required by default CI |
| Evidence | Versioned capability snapshot, telemetry profile, exact-treatment trace, immutable production comparator, and raw resource observations |

## References

- **Source PRD:** [../../prd-claude-agent-routing.md](../../prd-claude-agent-routing.md)
- **Roadmap MOC:** [claude-agent-routing-roadmap-MOC.md](claude-agent-routing-roadmap-MOC.md)
- **Constitution:** [../../../.specify/memory/constitution.md](../../../.specify/memory/constitution.md)
- **Project standards:** [../../../AGENTS.md](../../../AGENTS.md) and [../../../CLAUDE.md](../../../CLAUDE.md)
- **Codex parity sibling roadmap:** [codex-gpt-5-6-agent-routing-technical-roadmap.md](codex-gpt-5-6-agent-routing-technical-roadmap.md)
  (PR #330, amended by the parity PR #338)
- **Subagent configuration and model resolution:** [Subagents](https://code.claude.com/docs/en/sub-agents)
- **Model configuration and aliases:** [Model configuration](https://code.claude.com/docs/en/model-config)
- **Reasoning effort levels:** [Effort](https://platform.claude.com/docs/en/build-with-claude/effort)
- **Fast mode (frozen off in the environment contract):** [Fast mode](https://code.claude.com/docs/en/fast-mode)
- **Authentication modes:** [Authentication](https://code.claude.com/docs/en/authentication)
- **Usage and cost surfaces:** [Costs](https://code.claude.com/docs/en/costs)
- **OpenTelemetry monitoring:** [Monitoring usage](https://code.claude.com/docs/en/monitoring-usage)
- **API pricing (diagnostic-derived coefficients):** [Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
