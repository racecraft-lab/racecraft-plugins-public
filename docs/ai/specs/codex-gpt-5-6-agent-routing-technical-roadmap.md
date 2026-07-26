# Codex Agent Model Routing and Graceful Fallback Implementation Roadmap

**Select one preferred model/effort route and ordered qualified fallbacks from
an official-documentation candidate catalog for each named Codex agent, narrow
that catalog with documented runtime discovery, and install the complete matrix
atomically without changing any agent's safety, tool, or mutation contract.**

This document defines the SPEC catalog for capability-based Codex agent routing.
Each SPEC maps to an explicit acceptance-criteria subset in the source PRD and
is prepared for `$speckit-scaffold-spec G56R-NNN`.

**Source PRD:** [../../prd-codex-gpt-5-6-agent-routing.md](../../prd-codex-gpt-5-6-agent-routing.md)
**Roadmap MOC:** [codex-gpt-5-6-agent-routing-roadmap-MOC.md](codex-gpt-5-6-agent-routing-roadmap-MOC.md)
**Shared parity contract:** [agent-routing-parity-contract.md](agent-routing-parity-contract.md)
**Shared manifest schema:** [../research/agent-route-candidate-manifest.schema.json](../research/agent-route-candidate-manifest.schema.json)
**Spec ID prefix:** `G56R-###`
**Proposed branch:** `codex/agent-routing-fallback`
**Status:** Active; G56R-001 is complete and archived after PR #360 merged on
the shared official-source evidence foundation from PR #362;
[G56R-002](.process/G56R-002-workflow.md) is complete and archived after
PRs #366-#368; G56R-003 is ready

**Legacy identifier note:** `G56R` and the existing filenames are retained for
traceability. They do not limit the candidate catalog to GPT-5.6.

---

## Roadmap Overview

The effort is decomposed into **11 specifications** across **8 dependency
tiers**.

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | G56R-001 | Candidate route baseline and role contracts | Sequential spike |
| 2 | G56R-002 | Capability discovery, telemetry profile, and exact treatment | Sequential foundation |
| 3 | G56R-003 | Evaluation runner, fixtures, scoring, and statistics | Sequential foundation; two required work packages |
| 4 | G56R-004 | Policy controls and adaptive comparators | Sequential foundation |
| 5 | G56R-005 | Availability, fallback, and recovery simulation | Sequential foundation |
| 6 | G56R-006 | Resolver, materializer, atomic installer, and strict override | Sequential framework slice |
| 7 | G56R-007, G56R-008, G56R-009, G56R-010 | Qualify four disjoint agent cohorts | Parallel after G56R-006; serialize shared regeneration |
| 8 | G56R-011 | Compose final identities, rebuild payload, run installed UAT, and prove release readiness | Sequential integration |
| 9 | G56R-012 | Reconcile the mirrored evaluation contracts with CAR-003 | Joint change; must land on both platforms together |

**Execution order:** G56R-001 -> G56R-002 -> G56R-003 -> G56R-004 ->
G56R-005 -> G56R-006 -> G56R-007 + G56R-008 + G56R-009 + G56R-010 ->
G56R-011

**Implementation boundary:** This sequence has no external prerequisite, but its
internal dependencies still apply: the shared official-source evidence
foundation merged via PR #362, G56R-001 merged via PR #360, and G56R-002
completed through PRs #366-#368 under the preserved no-qualification boundary.
G56R-003 is ready to consume the canonical capability freeze, treatment
contracts, replay fixtures, and evidence report.
A route-agnostic Python `install-codex-agents` helper is active for safe static
agent refreshes. G56R-006 later extends that baseline with capability-aware
resolution, materialization, and atomic policy installation; it must not
reintroduce a deleted Bash helper. Any legacy static model rewrite behavior is
project-input compatibility only: it does not qualify model routes or runtime
capabilities, and G56R-006 replaces it with strict route-aware resolution.

### Evidence authority

G56R evidence must satisfy the shared parity contract and manifest schema.
Platform capability claims may cite only canonical OpenAI documentation under
`learn.chatgpt.com/docs/**`, `developers.openai.com/codex/**`,
`developers.openai.com/api/docs/**`, or `platform.openai.com/docs/**`.
Repository state, pinned runtime captures, and governed evaluations remain
authoritative for production qualification, but cannot establish undocumented
platform behavior. The schema-v2 G56R-001 handoff is the active baseline for
downstream specifications.

### Official candidate seed

G56R-001 starts from the current official Codex model guidance retrieved
2026-07-15. This table is a source ledger, not a pre-approved route table and not
an agent-to-model assignment. G56R-001 maps documented model candidates to
project role contracts and records executable tuple status as blocked when the
surface-supported effort set must be discovered. G56R-002 may expand listed
source-bound model records, or newly recorded role/model bindings for models
already present in this official-source ledger, into supported model/effort
tuples and narrow that set by runtime availability before the G56R-003 freeze.

| Official model ID | Documented positioning | Candidate use |
|---|---|---|
| `gpt-5.6-sol` | Complex, open-ended, high-value work needing analysis, judgment, or polish | Candidate for roles whose project contract matches that documented workload |
| `gpt-5.6-terra` | Everyday work requiring strong reasoning and tool use | Candidate for roles whose project contract matches that documented workload |
| `gpt-5.6-luna` | Clear, specific, repeatable, or high-volume work | Candidate for roles whose project contract matches that documented workload |
| `gpt-5.5` | Previous-generation model for complex coding, computer use, knowledge work, and research | Immutable comparator where project inventory records it; candidate only while officially documented |
| `gpt-5.3-codex-spark` | Text-only, low-latency research preview | Optional-helper candidate only when runtime availability, text-only suitability, and role contract are satisfied |

For every admitted model, effort search begins at the documented default and
uses only effort values documented for the pinned surface and returned by the
documented discovery schema. No route is preferred before qualification.

### Route, evidence, and identity contract

A route is a complete qualified tuple, not a model name:

```text
route = model
      + explicit model_reasoning_effort
      + instruction_hash
      + required model and modality capabilities
      + tool, skill, and MCP contract
      + sandbox and mutation contract
      + supported client range
      + qualification evidence
```

Fallback may change only the approved model and effort for the same named agent.
It preserves instructions, output contract, sandbox, mutation boundary, tools,
skills, and MCP configuration. Ordered fallback is SpecKit Pro policy; it is not
represented as a native custom-agent TOML fallback field.

| Identity | Created by | Required contents |
|---|---|---|
| `agent_contract_id` | G56R-001 | Named role plus safety, grounding, mutation, tool, and output contracts |
| `official_source_ledger_id` | G56R-001 | Source family, retrieval method, requested/canonical official URLs, retrieval dates, supported surfaces, exact documented facts, undocumented gaps, and source invalidation rules |
| `effort_surface_record_id` | G56R-001 | Source-scoped effort/default evidence for Codex model guidance, custom-agent TOML, config TOML, app-server catalog, and API guidance surfaces |
| `candidate_route_id` | G56R-001/G56R-002 | G56R-001 source-bound model candidate or G56R-002 executable model/effort tuple, effort-surface record binding, official-source-ledger binding, contract and instruction hashes, required capabilities, and rationale |
| `telemetry_profile_id` | G56R-002 | Pinned client/surface and fields classified as `stable_native`, `experimental_native`, `derived_from_controlled_configuration`, `conditional`, `unavailable`, `not_applicable`, or `undocumented` |
| `runtime_capability_snapshot_id` | G56R-002 or installer preflight | Client/surface, available model IDs, efforts, relevant capabilities, method, timestamp, and raw environment observation; never candidate authority |
| `experiment_policy_id` | G56R-003 | Corpora, partitions, scorers, analysis plan, budgets, terminal policy, and treatment controls |
| `execution_trace_id` | G56R-003 | Assigned route, effective-route evidence, result, raw resource observations, retries, terminal state, and treatment integrity |
| `route_resolution_id` | G56R-002 schema; G56R-003/G56R-006 records | Preferred and effective route, fallback index, reason, snapshot, attempted routes, and timestamp |
| `resolved_agent_policy_id` | G56R-006 schema/fixtures; G56R-011 final records | Exact destination custom-agent content and selected effective route |
| `agent_route_policy_id` | G56R-007 through G56R-010 | Named agent, preferred route, ordered qualified fallbacks, hard contract, evidence, client bounds, and invalidation rules |
| `core_routing_policy_id` | G56R-011 | Ordered mapping of the eleven required named agents to final route-policy IDs |
| `optional_helper_policy_id` | G56R-011 | Final helper route policy, approved fallbacks, and no-helper contract |
| `resolved_installation_id` | G56R-011 | Ordered mapping of installed agents to resolved policies and route resolutions |
| `release_policy_id` | G56R-011 | Final core/helper identities, resolver version, evidence lock, UAT, invalidation rules, and bounded claims |

Early traces must not require the final aggregate identities before G56R-011
creates them.

### Qualification and release-decision rule

- Deterministic role, safety, grounding, mutation, tool, and output-contract
  checks are hard gates.
- A candidate must clear absolute semantic-quality and reliability floors and a
  predeclared confidence-bound non-inferiority margin against the immutable
  production route.
- Among passing candidates, choose the preferred route under one predeclared,
  environment-independent resource/latency score or Pareto rule. Raw input,
  cached-input, and output tokens; duration; retries; compactions; terminal
  state; and accepted-workflow rate are the evidence.
- Every fallback independently passes the same hard role contract and the
  declared fallback quality/reliability floor. Fallback order is frozen before
  installed UAT.
- Use disjoint screening, selection, cohort-lock, and integrated-confirmation
  partitions; paired task-level inference; frozen workload strata; a powered
  long-horizon stratum; cache isolation; bounded attrition rules; and
  `inconclusive => no qualification`.
- Benchmark the installed custom-agent treatment or the exact canonical
  materialization later used by the installer. Bare prompt emulation remains a
  smoke/degradation test and cannot support route qualification.
- Begin each model at its documented default effort, ascend to the first stable
  pass when necessary, then descend and retest the boundary. Treat any
  orchestration-changing high-effort mode as a policy-level control, not a
  normal per-agent effort step.
- A `model/rerouted` service event is distinct from plugin fallback. A rerouted
  run cannot score the requested route. Runtime UAT may continue only when the
  destination is a qualified route for the same named agent; report it as a
  service reroute. An unapproved destination is a hard treatment failure.
- `codex exec --json` lifecycle and token events do not, by themselves,
  constitute an authoritative effective-model field. The telemetry profile must
  classify each claimed field by its actual source and preserve unavailable
  values as null.
- Evidence wins: no model family, effort, preview, or current default is forced
  into a role when it fails.

## Reviewability Contract

Every implementation spec must fit the repository's human review budget. Warn
above approximately 400 reviewable production LOC, 6 production files, or 15
total files; block-sized work must split unless an existing typed exception
legitimately applies. Generated payloads, tests, and documentation still count
toward reviewer load even where they do not count as production LOC.

**Estimator advisory:** The Python-authoritative `estimate-spec-size` operation
was last recorded on 2026-07-11 and rerun for G56R-009 on 2026-07-12 after the
two parity agents joined that cohort (392 LOC, ok). Each scaffold must rerun it
when scope or file counts change. G56R-003 remains a warning-sized SPEC and must
preserve its two declared work packages.

## Dependency Graph

```text
G56R-001 Candidate Route Baseline and Role Contracts
    |
    v
G56R-002 Capability Discovery, Telemetry Profile, and Exact Treatment
    |
    v
G56R-003 Evaluation Runner, Fixtures, Scoring, and Statistics
    |
    v
G56R-004 Policy Controls and Adaptive Comparators
    |
    v
G56R-005 Model Availability, Fallback, and Recovery Simulation
    |
    v
G56R-006 Resolver, Materializer, Installer, and Strict Override
    |
    +--> G56R-007 Quality-critical Executor Routing --------+
    +--> G56R-008 Structured-work Agent Routing ------------+
    +--> G56R-009 Read-only Reasoning and Orchestration-support Agent Routing --+
    +--> G56R-010 Optional Helper and No-helper Path --------+
                                                              |
                                                              v
                   G56R-011 Final Composition, Installed UAT, and Release Proof
```

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|---|---|---|---|---|
| G56R-001 | Candidate Route Baseline and Role Contracts | Complete / Archived | [.process/G56R-001-workflow.md](.process/G56R-001-workflow.md) | PR #360 merged; canonical evidence lives under `docs/ai/research/` |
| G56R-002 | Capability Discovery, Telemetry Profile, and Exact Treatment | Complete / Archived | [.process/G56R-002-workflow.md](.process/G56R-002-workflow.md) | PRs #366-#368 merged; canonical evidence, contracts, replay fixtures, and validators live outside `specs/**` |
| G56R-003 | Evaluation Runner, Fixtures, Scoring, and Statistical Analysis | Ready | - | G56R-002 dependency satisfied by PRs #366-#368 |
| G56R-004 | Policy Controls and Adaptive Comparators | Pending | - | Blocked by G56R-003 |
| G56R-005 | Model Availability, Fallback, and Recovery Simulation | Pending | - | Blocked by G56R-004 |
| G56R-006 | Capability-aware Resolver, Materializer, Installer, and Strict Override | Pending | - | Blocked by G56R-005 |
| G56R-007 | Quality-critical Executor Routing | Pending | - | Blocked by G56R-006 |
| G56R-008 | Structured-work Agent Routing | Pending | - | Blocked by G56R-006 |
| G56R-009 | Read-only Reasoning and Orchestration-support Agent Routing | Pending | - | Blocked by G56R-006 |
| G56R-010 | Optional Helper Routing and No-helper Path | Pending | - | Blocked by G56R-006 |
| G56R-011 | Payload, Installed Skill UAT, Fallback Proof, and Release Integration | Pending | - | Blocked by G56R-007 through G56R-010 |
| G56R-012 | Mirrored Evaluation-Contract Reconciliation with CAR-003 | Pending | - | Raised 2026-07-26; the Codex half of a joint change, scoped in CAR-012 |

**Status legend:** Pending | Ready | In Progress | In Review | Complete | Complete / Archived | Blocked

---

## Specification Sections

### G56R-001: Candidate Route Baseline and Role Contracts

**Priority:** P1 | **Depends On:** None | **Enables:** G56R-002

**Goal:** Produce the dated, cited candidate-route and role-contract handoff
needed for capability discovery without changing installed defaults.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 0 (spike) | Suggested slices: 1 | Status: ok |
Production files: 0 | Total files: approximately 3 |
Budget result: research spike; time-boxed, LOC sizing not applicable

**Scope:**

- Inventory the ten current custom-agent source definitions plus the two
  parity additions derived from the Claude plugin (`consensus-synthesizer`,
  `gate-validator`) and record each agent's immutable production route or its
  recorded absence, instructions, role boundary, safety/grounding/
  mutation contract, output contract, expected tool/skill/MCP use, supported
  client assumptions, and representative tasks.
- Label every repository, route-policy skill/runner surface, payload, cache,
  fixture, and Claude-definition fact as `project_input`; none may establish a
  Codex model, effort, field, capability, or native behavior.
- Publish a versioned `agent_route_candidate_manifest` covering all twelve
  named agents. Create `official_source_ledger_id`,
  `effort_surface_record_id`, `agent_contract_id`, and provisional
  `candidate_route_id` records. Each candidate binds the ledger and
  source-scoped effort records, and records either an officially proven
  model/effort tuple or blocked executable-tuple status pending G56R-002
  capability discovery, plus instruction hash, required model and modality
  capabilities, tool/skill/MCP contract, sandbox/mutation contract, rationale,
  known incompatibilities, evidence requirements, and invalidation triggers.
- Admit project-level candidates only from the official-source ledger and bind
  every candidate to source family, retrieval method, requested/canonical
  official URLs, retrieval dates, documented positioning, supported surfaces,
  source-scoped effort/default records, and documented constraints. Distinguish
  that eligibility from
  installation-time availability. Record role-fit hypotheses and fallback-
  candidate requirements without claiming that any candidate is executable or
  preferred.
- Record the immutable production-route inputs that G56R-003 will bind into the
  sole candidate and integrated comparator before screening. This research
  output does not depend on G56R-002 or G56R-003 completion evidence.
- Build the sole platform-fact table from official Codex model, custom-agent,
  configuration, app-server, and non-interactive documentation. Record source
  family, retrieval method, requested/canonical URL, retrieval date, surface,
  exact documented fact, and affected roadmap claim. Label every unsupported
  behavior `undocumented`; it may remain an open question or proposed SpecKit
  Pro policy but cannot support a candidate or platform claim.
- Deliver the role contracts, effort-surface records, provisional candidate
  manifest, fixture backlog, three-current/nine-missing fixture inventory,
  telemetry requirements, capability questions, and independent go/no-go
  handoff to G56R-002.
- INVEST rationale: the spike closes the research uncertainty that blocks safe
  capability probing and ends without depending on later telemetry results.

**Out of Scope:**

- Agent TOML, installer, prompt, payload, or default changes.
- Live corpus execution, qualification, or fallback ordering.

**Key Files:**

- [proposed] `docs/ai/research/codex-agent-route-candidates.md`
- `speckit-pro/codex-agents/*.toml` - read-only inventory source
- `tests/speckit-pro/layer6-efficiency/` - current fixture-gap inventory source

---

### G56R-002: Capability Discovery, Telemetry Profile, and Exact-Treatment Contract

**Priority:** P1 | **Depends On:** G56R-001 | **Enables:** G56R-003

**Goal:** Freeze the executable candidate set and trustworthy trace contract
before outcome-bearing evaluation begins.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 265 | Suggested slices: 1 | Status: ok |
Production files: approximately 3 | Total files: approximately 10 |
Budget result: re-estimate at scaffold; synthetic traces precede live use

**Scope:**

- Revalidate the official-source ledger before freezing candidates, including
  the direct GPT-5.6 prompting guide as API-surface authority for prompt
  treatment only. It cannot establish Codex custom-agent fields, availability,
  defaults, telemetry, or exact treatment; a changed or inaccessible source
  invalidates only the claims bound to it.
- Implement or bind the pinned client integration to app-server `model/list`
  and `modelProvider/capabilities/read`. Capture model IDs, supported efforts, relevant
  capabilities, client/surface, evidence method, raw response, and timestamp in
  `runtime_capability_snapshot_id`. Treat the response as runtime availability
  verification under the officially documented schema, not as authority for a
  new platform fact.
- Where authoritative discovery is unavailable, allow only the predeclared
  bounded exact-invocation availability probe for a candidate already admitted by the
  official-source ledger. A probe may establish availability for the pinned
  environment only; it cannot establish platform support, effort support, or
  candidate eligibility. An unresolved model or effort is unavailable for
  qualification.
- Bind provisional candidates to the capability snapshot, expand G56R-001
  source-bound model candidates and any newly recorded official-ledger-bound
  role/model bindings into supported executable model/effort tuples, complete
  their `candidate_route_id` records, and freeze the executable set before
  G56R-003 scores outcomes.
- Publish `telemetry_profile_id` for the pinned client and surface. Classify each
  desired field as `stable_native`, `experimental_native`,
  `derived_from_controlled_configuration`, `conditional`, `unavailable`,
  `not_applicable`, or `undocumented`; state the source, completeness rule, and
  claims each class may support. Never fabricate returned effort, effective
  model, speed, token categories, or parent attribution. A native classification
  requires an official field-level citation for the pinned surface; controlled
  configuration proves requested assignment only.
- Define `route_resolution_id` and exact-treatment replay schemas for candidate route, named
  agent, explicit model and effort, instruction hash, sandbox and mutation
  class, expected skills/MCP/tools, parent configuration, client, controlled
  runtime overrides, delivery canary, and treatment failures.
- Require every assigned objective to bind `candidate_route_id`,
  `agent_contract_id`, `runtime_capability_snapshot_id`, `route_resolution_id`,
  `experiment_policy_id`, and `execution_trace_id`. Define raw trace fields for assigned route, requested route,
  effective-route evidence, service reroute events, raw token vector, duration,
  context/tools/compaction/retries/validation, parent-child graph, terminal
  state, acceptance, and null behavior.
- A service-rerouted run is not scored as the requested route. Permit continued
  runtime UAT only when the destination is a prequalified route for the same
  named agent; otherwise fail treatment. Keep service rerouting distinct from a
  resolver-selected fallback.
- Validate success, null, unavailable-field, misdelivery, and approved/
  unapproved service-reroute records with synthetic replay.

**Out of Scope:**

- Corpus execution, scoring, statistical qualification, fallback ordering, or
  installation.

**Key Files:**

- [proposed] `tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py`
- [proposed] `tests/speckit-pro/layer6-efficiency/lib/treatment_trace_schema.py`
- [proposed] `tests/speckit-pro/unit/test-codex-capability-contract.py`

---

### G56R-003: Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

**Priority:** P1 | **Depends On:** G56R-002 | **Enables:** G56R-004

**Goal:** Qualify preferred and fallback candidates reproducibly without
consuming final integrated-confirmation data.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 500 | Suggested slices: 2 | Status: warn |
Production files: approximately 4 | Total files: more than 20 expected |
Budget result: mandatory scaffold-time split between treatment runner and
fixture/scorer/statistical work

**Required Work Package A - Treatment runner and trace:**

- Replace bare prompt emulation for qualification with execution of the actual
  custom-agent policy or byte-identical canonical materialization. Implement the
  canonical materializer as a shared Python component consumed later by
  G56R-006.
- Before scoring, prove the expected named agent, explicit model/effort,
  instruction hash, sandbox, tools, skills, MCP startup/schema, parent controls,
  client, and context configuration. Treatment misdelivery does not become a
  candidate-quality observation.
- Emit replayable `execution_trace_id` records under the G56R-002 schema.
  Preserve every assigned attempt, failed/abandoned branch, retry, repair,
  validation, compaction, child, terminal result, and raw resource observation.

**Required Work Package B - Fixtures, scoring, and statistics:**

- Expand from three current role fixtures to a governed twelve-role corpus. Use
  blinded adjudication for candidate quality failure, treatment-delivery
  failure, invalid fixture, invalid scorer, and infrastructure failure. A
  fixture/scorer change versions it and invalidates affected results.
- Create disjoint screening, selection, cohort-lock, and untouched integrated-
  confirmation partitions. G56R-003 reserves but never consumes the final
  partition.
- Freeze `experiment_policy_id` before outcome-bearing evaluation. It defines
  corpus versions, workload strata, long-horizon assignment from pretreatment
  task properties, acceptance checker, semantic floors, safety gates,
  superiority/non-inferiority margins, alpha, power, multiplicity, task-level
  clustering, repeat rules, racing, attrition, campaign/workflow budgets,
  terminal policy, and `inconclusive => no qualification`.
- Before screening, bind the immutable production comparator to repository
  revision, plugin version, per-agent route/configuration IDs, client version,
  tool/configuration contract, corpus snapshot, instruction hashes, and the
  frozen analysis plan. It remains the sole baseline for candidate and final
  integrated comparisons.
- Compare route resource behavior using raw input/cached-input/output tokens,
  duration, retries, compactions, acceptance, and terminal state.
- Use A1 capability/treatment screening at each model's documented default, A2
  within-model effort boundary search, A3 frozen passing-pair comparison, Stage
  B prompt interaction, and Stage C cohort locks. Prompts stay frozen through
  A1/A2/A3; only shortlisted pairs enter Stage B. After selecting the final
  instruction hash, requalify every committed preferred and fallback route
  under that same hash before Stage C.
- In Stage B, start every ablation from the unchanged baseline, vary one
  predeclared instruction/example/tool-description/context group at a time, and
  rerun the same representative evaluations. Record baseline and candidate
  instruction hashes, changed group IDs, normalized instruction bytes,
  available token estimate, and contradiction-review result. Permit removal of
  repeated or behavior-neutral process scaffolding only when the variant keeps
  the complete role contract: outcome, success and stop conditions, safety,
  business, grounding, permissions, mutation, contextual tool routing, output
  shape, and validation. Outcome-first wording may replace discretionary
  narration but not required SDD phases, dependency rules, approvals, or
  verification.
- Freeze all non-candidate parent routes, agent routes, prompts, tools, context,
  repository snapshot, validators, retries, and acceptance behavior for per-
  agent attribution. Unpinned/adaptive experiments are policy-level controls.
- Retain candidate-caused failures in resource and acceptance outcomes. Permit a
  complete-pair rerun only for a preclassified independent transient harness
  failure under the capped attrition rule; unexplained or differential loss
  blocks the affected conclusion.

**Out of Scope:**

- Final route-policy creation, installed defaults, final aggregate identities,
  or release confirmation.

**Key Files:**

- `tests/speckit-pro/layer6-efficiency/run_codex_role_eval.py` - current runner to replace for qualification
- [proposed] `tests/speckit-pro/layer6-efficiency/lib/agent_materializer.py`
- [proposed] `tests/speckit-pro/layer6-efficiency/lib/statistical_analysis.py`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex/` - current fixtures and proposed expansion
- [proposed] `tests/speckit-pro/unit/test_efficiency_codex_runner.py`

---

### G56R-004: Policy Controls and Adaptive Comparators

**Priority:** P1 | **Depends On:** G56R-003 | **Enables:** G56R-005

**Goal:** Define, exact-treatment validate, and freeze policy-level controls
before the final static routing policy exists.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 235 | Suggested slices: 1 | Status: ok |
Production files: approximately 3 | Total files: approximately 10 |
Budget result: bounded to policy orchestration and replay fixtures

**Scope:**

- Define, exact-treatment validate, content-address, and freeze unpinned,
  adaptive, and justified high-effort controls. Include automatically spawned
  child work in any orchestration-changing control.
- Freeze adaptive signals, thresholds, escalation/de-escalation paths, budgets,
  quality eligibility, dominance metrics and margins, confidence method,
  multiplicity position, and integrated-confirmation arm assignment.
- Define material dominance to require every mandatory safety, role, quality,
  reliability, and availability gate plus the predeclared resource/duration
  margins. Validate control execution and telemetry with replay and smoke data.
- Keep results policy-level. G56R-004 cannot conclude whether the future static
  `core_routing_policy_id` is dominated; G56R-011 performs that comparison.
- Freeze the messaging rule: a materially dominated static release may ship for
  declared operational simplicity but cannot claim efficient, optimal, or best
  measured routing.

---

### G56R-005: Model Availability, Fallback, and Recovery Simulation

**Priority:** P1 | **Depends On:** G56R-004 | **Enables:** G56R-006

**Goal:** Prove bounded resolver and recovery semantics before the installer
uses real route policies.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 242 | Suggested slices: 1 | Status: ok |
Production files: approximately 3 | Total files: approximately 10 |
Budget result: synthetic availability and recovery fixtures before live UAT

**Scope:**

- Define fixture route policies and simulate preferred model absent, effort
  unsupported, discovery unavailable, exact-invocation availability-probe
  success/failure,
  treatment-probe failure, approved/unapproved service reroute, and no safe
  required route.
- Simulate optional-helper unavailable, validated no-helper continuation,
  strict override incompatibility, bounded retry, fallback-list exhaustion,
  rollback, atomic no-write, and previous-known-good installation preservation.
- Require deterministic resolution reasons:
  `preferred_model_unavailable`, `effort_unsupported`,
  `capability_discovery_unavailable`, `treatment_probe_failed`, and
  `no_safe_route`; distinguish every service reroute from these plugin reasons.
- Reject loops, unqualified adjacent models, generic-agent substitution,
  omitted model/effort inheritance, partial required-agent installation, or
  fallback changes to instructions, tools, skills, MCP, sandbox, mutation, or
  output contracts.
- Enforce bounded campaign/workflow time, retries, subagent fan-out, context
  growth, cancellation, and escalation/de-escalation in the harness. Production
  checkpoint/resume scheduling remains separate follow-up work.

---

### G56R-006: Capability-aware Resolver, Materializer, Installer, and Strict Override

**Priority:** P1 | **Depends On:** G56R-005 |
**Enables:** G56R-007 through G56R-010

**Goal:** Implement the reusable installation framework and prove it against
fixture route policies without creating final route aggregates.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 265 | Suggested slices: 1 | Status: ok |
Production files: approximately 4 | Total files: approximately 10 |
Budget result: re-estimate at scaffold; one resolver/installer policy slice

**Scope:**

- Extend the active route-agnostic Python `install-codex-agents` operation with
  capability-aware resolution and atomic policy installation; do not restore
  the deleted shell installer.
- Consume the G56R-003 canonical materializer. The resolver evaluates the
  preferred route, then each ordered fallback, using a fresh
  `runtime_capability_snapshot_id`; when discovery is unavailable, use only the
  predeclared bounded availability-probe path for an official-ledger candidate.
- A route is compatible only when its model, effort, and required capabilities
  are documented for the pinned surface, runtime availability is verified, and
  the exact materialized treatment passes. Materialize explicit model and
  effort values; never inherit an unmeasured parent default.
- Emit `route_resolution_id` and `resolved_agent_policy_id` for each fixture
  agent, including attempted routes and rejection reasons. G56R-006 owns the
  production resolver implementation and framework fixtures, not the
  G56R-002 trace schema or final `core_routing_policy_id`,
  `optional_helper_policy_id`, `resolved_installation_id`, or
  `release_policy_id` values.
- Resolve every required agent before any write. If one has no safe route,
  preserve the previous known-good installation and report every attempt.
  Materialize destination copies only; never mutate bundled source policies or
  unrelated user-owned files.
- Install the optional helper only when at least one qualified helper route
  resolves. Otherwise omit or remove the stale plugin-managed helper and prove
  the no-helper contract without failing the required-agent installation.
- Retain one explicit global model override for required agents. The override is
  strict: preserve each effort and contract, validate every resulting tuple,
  fail atomically when any tuple is incompatible or unresolved, and never fall
  back silently. Arbitrary user effort mappings remain out of scope.
- Verify destination content, required-agent count, conditional helper state,
  resolution report, restart guidance, rollback, and previous-install
  preservation using fixture policies and fake-home tests.
- INVEST rationale: later cohorts can supply final route policies without
  redesigning installation.

**Out of Scope:**

- Final preferred/fallback selection or final aggregate identities.
- Per-agent overrides, user-supplied effort maps, or Claude installation.

**Key Files:**

- `speckit-pro/codex-skills/install/SKILL.md` - current install contract
- `speckit-pro/speckit_pro_runner/helpers/install.py` - current install/doctor module and proposed agent-copy owner
- `speckit-pro/speckit_pro_runner/helpers/registry.py` - active static baseline and capability-aware extension point
- `speckit-pro/codex-agents/*.toml` - source inventory
- `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` - current tests to extend with fake-home cases

---

### G56R-007: Quality-critical Executor Routing

**Priority:** P1 | **Depends On:** G56R-006 | **Enables:** G56R-011

**Goal:** Produce final preferred and ordered fallback route policies for phase,
implementation, and analyze/remediation agents.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 257 | Suggested slices: 1 | Status: ok |
Production files: 0 | Total files: approximately 10 |
Budget result: re-estimate at scaffold; three disjoint TOMLs plus role evidence

**Scope:**

- Screen every executable, role-eligible candidate from the frozen manifest for
  `phase-executor`, `implement-executor`, and `analyze-executor`; retain the
  immutable production route as comparator.
- Score real Specify/Plan/Tasks, strict TDD implementation, and full Analyze
  remediation contracts rather than generic coding prompts.
- Apply A1/A2/A3, Stage B prompt interaction, Stage C cohort lock, exact
  treatment, task-level inference, and progressive effort search without
  consuming integrated-confirmation data.
- Emit one final `agent_route_policy_id` per named agent containing its preferred
  route, ordered independently qualified fallbacks, hard contract, evidence,
  supported client bounds, and invalidation triggers.
- Prove each route policy against the G56R-006 resolver/installer fixtures while
  leaving non-cohort policies frozen.
- INVEST rationale: the three highest-risk mutating roles share a quality-first
  evidence seam but retain independent route policies.

**Out of Scope:**

- Structured checklist/UAT, read-only analyst, and helper routes.

**Key Files:**

- `speckit-pro/codex-agents/phase-executor.toml`
- `speckit-pro/codex-agents/implement-executor.toml`
- `speckit-pro/codex-agents/analyze-executor.toml`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex/` - cohort fixtures/results

---

### G56R-008: Structured-work Agent Routing

**Priority:** P1 | **Depends On:** G56R-006 | **Enables:** G56R-011

**Goal:** Produce final preferred and ordered fallback route policies for
checklist remediation and UAT runbook authoring.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 210 | Suggested slices: 1 | Status: ok |
Production files: 0 | Total files: approximately 8 |
Budget result: re-estimate at scaffold; two role TOMLs plus evidence

**Scope:**

- Screen every executable, role-eligible candidate for `checklist-executor` and
  `uat-runbook-author`; require complete all-severity checklist remediation and
  executable, non-circular, acceptance-criteria-linked UAT runbooks.
- Preserve workspace-write, error, and fail-open boundaries while applying the
  same A1/A2/A3, Stage B, Stage C, exact-treatment, effort-search, and evidence
  rules as G56R-007.
- Emit one final `agent_route_policy_id` per named agent with preferred route,
  ordered independently qualified fallbacks, hard contract, evidence, client
  bounds, and invalidation triggers.
- Prove both policies against the G56R-006 resolver/installer fixtures without
  consuming integrated-confirmation data.
- INVEST rationale: two structured-output mutators share a measurable contract
  and remain independent of deep executors and analysts.

**Out of Scope:**

- Quality-critical executors, read-only analysts, and helper routes.

**Key Files:**

- `speckit-pro/codex-agents/checklist-executor.toml`
- `speckit-pro/codex-agents/uat-runbook-author.toml`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex/` - cohort fixtures/results

---

### G56R-009: Read-only Reasoning and Orchestration-support Agent Routing

**Priority:** P1 | **Depends On:** G56R-006 | **Enables:** G56R-011

**Goal:** Produce final preferred and ordered fallback route policies for
clarification, research, codebase analysis, project-context analysis, consensus
synthesis, and gate validation.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 392 | Suggested slices: 1 | Status: ok |
Production files: 0 | Total files: approximately 16 |
Budget result: re-estimate at scaffold; six TOMLs plus bounded role fixtures

**Scope:**

- Screen every executable, role-eligible candidate for `clarify-executor`,
  `domain-researcher`, `codebase-analyst`, `spec-context-analyst`,
  `consensus-synthesizer`, and `gate-validator`; retain lighter models only
  when they preserve the complete role contract.
- Author the two parity additions as named Codex custom agents per current
  official custom-agent documentation before route qualification, with role
  contracts mirroring the Claude definitions, and record any platform-specific
  divergence explicitly.
- Hard-gate read-only behavior, source-domain separation, citations or file
  locators, abstention, and structured return formats; additionally hard-gate
  the three-analyst consensus-synthesis contract (agreement rule, confidence
  assessment, actionable synthesized answer) and the structured gate-validation
  evidence contract.
- Apply A1/A2/A3, Stage B, Stage C, exact treatment, progressive effort search,
  and the shared statistical plan without consuming integrated-confirmation
  data.
- Emit one final `agent_route_policy_id` per named agent with preferred route,
  ordered independently qualified fallbacks, hard contract, evidence, client
  bounds, and invalidation triggers.
- Prove all policies against G56R-006 resolver/installer fixtures.
- INVEST rationale: one read-only evidence seam preserves six distinct
  perspective and orchestration-support contracts without mutation conflicts.

**Out of Scope:**

- Mutating executors, UAT authoring, and helper routing.

**Key Files:**

- `speckit-pro/codex-agents/clarify-executor.toml`
- `speckit-pro/codex-agents/domain-researcher.toml`
- `speckit-pro/codex-agents/codebase-analyst.toml`
- `speckit-pro/codex-agents/spec-context-analyst.toml`
- [proposed] `speckit-pro/codex-agents/consensus-synthesizer.toml` - net-new parity addition
- [proposed] `speckit-pro/codex-agents/gate-validator.toml` - net-new parity addition
- `tests/speckit-pro/layer6-efficiency/fixtures-codex/` - cohort fixtures/results

---

### G56R-010: Optional Helper Routing and No-helper Path

**Priority:** P1 | **Depends On:** G56R-006 | **Enables:** G56R-011

**Goal:** Select qualified helper routes and prove that autopilot remains valid
when no helper route is available.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 177 | Suggested slices: 1 | Status: ok |
Production files: 0 | Total files: approximately 6 |
Budget result: re-estimate at scaffold; single-agent vertical slice

**Scope:**

- Screen runtime-available latency-oriented candidates from the frozen
  official-source manifest, including the production helper route when it is
  document-eligible and executable, under the same explicit route and exact-
  treatment rules as required agents.
- Hard-gate read-only/advisory scope, concise return format, low-latency
  behavior, and prohibition on SDD reasoning or mutation. Explicitly materialize
  the qualified effort rather than inheriting a parent default.
- Emit the helper's final `agent_route_policy_id` with preferred route and
  ordered independently qualified fallbacks. Also freeze the no-helper contract
  used when none resolves. G56R-011 creates the aggregate
  `optional_helper_policy_id` after integration.
- Measure functionality, latency, spawn reliability, resolution reasons, and
  result use. Prove autopilot continuation when the helper is omitted,
  unavailable, not invoked, or cannot spawn.
- Keep helper qualification separate from the required eleven-agent core
  statistic; helper absence is not a required-core installation failure.
- INVEST rationale: the optional leaf can be selected, omitted, or rejected
  without changing any required agent.

**Out of Scope:**

- General SDD reasoning and all other agent routes.

**Key Files:**

- `speckit-pro/codex-agents/autopilot-fast-helper.toml`
- `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` - directly tied helper guidance
- `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json`
- [proposed] `tests/speckit-pro/layer6-efficiency/fixtures-codex/autopilot-fast-helper/`

---

### G56R-011: Payload, Installed Skill UAT, Fallback Proof, and Release Integration

**Priority:** P1 | **Depends On:** G56R-007, G56R-008, G56R-009, G56R-010 |
**Enables:** Release

**Goal:** Compose, install, and prove one internally consistent routing policy
whose skills use the named agents and whose resolver behaves safely when a
preferred route is unavailable.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 395 | Suggested slices: 1 | Status: ok |
Production files: approximately 2 | Total files: approximately 15 |
Budget result: re-estimate at scaffold; split release evidence from source fixes if warned

**Scope:**

- After all cohort locks, create final `resolved_agent_policy_id` records and
  `core_routing_policy_id` from the eleven required `agent_route_policy_id`
  values; create `optional_helper_policy_id` from the helper route policy and
  no-helper contract; resolve them into `resolved_installation_id`; then bind
  `official_source_ledger_id`, the evidence, resolver version, UAT, invalidation
  rules, and bounded claims into `release_policy_id`.
- Rebuild `dist/codex` through the Python-authoritative payload builder and
  regenerate integrity metadata; never hand-edit generated agent files.
- Reconcile source, payload, installation, benchmark, rollback, and release
  packet identities. Source and payload retain twelve definitions; the plugin-
  managed destination contains eleven required agents plus the helper only when a
  qualified route resolves. Preserve unrelated user-owned files byte-for-byte
  and remove a stale plugin-managed helper when the no-helper state applies.
- Update active install/autopilot/public guidance with preferred/fallback route
  resolution, strict override, effective-route reporting, restart, rollback,
  service-reroute distinction, and the no-helper path.
- Run final integrated confirmation of the assembled preferred eleven-agent core
  against the immutable production core on untouched data. Require all safety,
  quality, reliability, accepted-workflow, raw-resource, duration, retry,
  compaction, attrition, and powered long-horizon gates, including the
  predeclared environment-independent resource-superiority endpoint. Passing
  proves bounded component-wise improvement, not global optimality among every
  possible assembled policy.
- Compare the final static core with the frozen G56R-004 controls on predeclared
  secondary arms. A materially dominant qualified control restricts efficiency
  wording under the frozen messaging rule.
- Publish `skill_agent_usage_manifest` for every active Codex skill entry point
  and all twelve source agents. Update each applicable skill to name the installed
  agent, triggering condition, allowed route resolution, and result-consumption
  contract; classify other mappings as conditional, prohibited, or not
  applicable.
- Run representative workflows through actual installed Codex skills. Across
  the set, prove every required core agent was spawned by its name and that its
  returned result affected a decision, artifact, or validation. Direct harness
  injection, generic-agent substitution, missing required spawn, or unconsumed
  result fails release proof. Test the helper in a separate workflow and prove
  the no-helper path; no single workflow must spawn all twelve agents.
- Bind every installed UAT trace as:

  ```text
  skill_id
    -> skill_instruction_hash
    -> named_agent
    -> route_resolution_id
    -> effective_model_evidence_or_null
    -> effective_effort_evidence_or_null
    -> exact_treatment_evidence
    -> returned_result_hash
    -> consuming_decision_or_artifact
  ```

- Prove installed preferred selection and these bounded failure scenarios:
  preferred model absent, effort unsupported, discovery unavailable with
  allowed exact probe, treatment-probe failure, no safe required route with
  atomic no-write and previous-install preservation, helper unavailable and
  no-helper continuation, strict override failure, and rollback.
- For service rerouting, prove a rerouted run never scores the requested route;
  an approved destination may continue only as separately labeled runtime UAT,
  while an unapproved destination fails treatment.
- Run deterministic source, payload, installed-cache, default-suite,
  active-path, benchmark replay, install, rollback, and skill-driven integration
  gates appropriate to the implementation changes. Produce a public-readable
  evidence packet with selected/rejected routes, fallback order, controls,
  long-horizon results, known gaps, review order, rollback, and rerun triggers.
- INVEST rationale: the integration slice proves independently selected route
  policies form a safe consumer-installable system and reopens selection when
  they do not.

**Out of Scope:**

- Global optimality across every complete twelve-agent assembly.
- Manual version bumps; release-please owns release versioning.

**Key Files:**

- `scripts/build-plugin-payloads.py`
- `speckit-pro/speckit_pro_runner/gates/payloads.py`
- `dist/codex/speckit-pro/` - generated output only
- `speckit-pro/codex-skills/install/SKILL.md`
- `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`
- `speckit-pro/codex-skills/*/SKILL.md` - active skill-to-agent contracts
- `docs-site/src/content/docs/install/codex.md`
- `tests/speckit-pro/layer1-structural/validate-codex-agents.py`
- `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py`
- `tests/speckit-pro/layer7-integration/` - skill-driven spawn and result-use proof
- `docs/ai/specs/.process/` - release and live-UAT evidence

---

### G56R-012: Mirrored Evaluation-Contract Reconciliation with CAR-003

**Priority:** P2 | **Depends On:** G56R-003 (merged), CAR-003 (merged) |
**Enables:** pooled cross-platform analysis in G56R-007 through G56R-010

**Goal:** Land the Codex half of one joint change across both platforms. The
scope, rationale, and per-item reasoning are authored once in
[CAR-012](claude-agent-routing-technical-roadmap.md#car-012-mirrored-evaluation-contract-reconciliation-with-g56r-003)
and are not restated here — duplicating them is how two platforms drift while
both believe they agree.

**Why a separate spec ID for one change.** The work is a single joint change, but
each platform carries its own roadmap, progress table, and reviewability budget.
This entry exists so the Codex roadmap does not silently omit work its contracts
require. Scaffold whichever ID leads; the other closes when the joint change
lands on both.

**Scope:** as CAR-012, applied to
`specs/g56r-003-evaluation-runner-scoring/contracts/` and the Codex
qualification harness. Two items are Codex-side additions the CAR-003 twin
handoff already specifies in full: FR-034's total plane-by-code mapping, and
FR-014's missing-gate sentence together with its `non_scorable` disposition
consequence, which must be verified explicitly rather than assumed to follow from
the plane change.

**Out of Scope:** as CAR-012.

**Key Files:**

- `specs/g56r-003-evaluation-runner-scoring/contracts/analysis-decision.schema.json`
- `specs/g56r-003-evaluation-runner-scoring/contracts/score-bundle.schema.json`
- `specs/g56r-003-evaluation-runner-scoring/spec.md` - FR-014, FR-034, FR-058
- `tests/speckit-pro/layer6-efficiency/lib/qualification_contracts.py`
- `tests/speckit-pro/layer6-efficiency/contracts/` - the shared-path collision

---

## Environment & Deployment Context

### Existing Infrastructure (No Changes Needed)

| Resource | Detail |
|---|---|
| Codex agent source | Ten current TOML files under `speckit-pro/codex-agents/`; two parity additions arrive via G56R-009 |
| Installed destination | `~/.codex/agents/` or explicit compatible destination |
| Evaluation | Python Layer 6 prompt-emulation runner, three existing role fixtures, and lexical smoke scorer; current results cannot qualify production routes |
| Payload build | Python 3.11+ `scripts/build-plugin-payloads.py` and runner payload gate |
| Release | release-please plus deterministic source/payload/install/release gates |

### Changes Required

| Change | Where | Detail |
|---|---|---|
| Candidate route record | [proposed] `docs/ai/research/` | Dated official-source ledger, project-input role contracts, document-eligible candidate routes, capability questions, and fixture backlog |
| Capability and telemetry adapter | [proposed] Layer 6 Python libraries | Runtime capability snapshot, exact-invocation availability probe, telemetry profile, treatment and reroute trace schemas |
| Route evaluation | Layer 6 Python harness | Canonical materializer, twelve-role fixtures, disjoint corpora, scoring, statistics, raw resource evidence, and long-horizon stratum |
| Fallback simulation | [proposed] Layer 6 replay fixtures | Availability, effort, probe, service-reroute, no-safe-route, helper, atomicity, rollback, and retry cases |
| Installer policy | Python install helper and registry | Capability-aware resolver, explicit materialization, strict override, atomic complete-matrix write, reporting, and preservation |
| Agent route policies | Route-policy evidence plus `speckit-pro/codex-agents/*.toml` | Preferred/fallback order remains project-owned; destination TOMLs materialize one explicit route |
| Skill-to-agent orchestration | `speckit-pro/codex-skills/` and Layer 7 | Named-agent dispatch plus installed spawn and result-consumption proof for all required agents and the optional helper |
| Generated payload | `dist/codex/` | Rebuild from source and refresh integrity evidence |
| Consumer guidance | Codex install/autopilot/docs surfaces | Route resolution, fallback, strict override, effective route, restart, rollback, and no-helper behavior |

### Local Development Setup

| Requirement | How |
|---|---|
| Python | Python 3.11+ standard-library runner already required by SpecKit Pro |
| Codex | Pinned client with documented custom-agent support and runtime availability for official-ledger candidates through documented discovery or a bounded availability probe |
| Live evaluation | Explicit developer-local campaign and workflow budgets; never required by default CI |
| Evidence | Versioned capability snapshot, telemetry profile, exact-treatment trace, immutable production comparator, and raw resource observations |

## References

- **Source PRD:** [../../prd-codex-gpt-5-6-agent-routing.md](../../prd-codex-gpt-5-6-agent-routing.md)
- **Roadmap MOC:** [codex-gpt-5-6-agent-routing-roadmap-MOC.md](codex-gpt-5-6-agent-routing-roadmap-MOC.md)
- **Constitution:** [../../../.specify/memory/constitution.md](../../../.specify/memory/constitution.md)
- **Project standards:** [../../../AGENTS.md](../../../AGENTS.md) and [../../../CLAUDE.md](../../../CLAUDE.md)
- **Official-source policy:** Only the OpenAI documentation links below may
  establish Codex platform facts; retrieved 2026-07-15.
- **Codex models and reasoning controls:** [Codex models](https://developers.openai.com/codex/models)
- **Codex custom-agent behavior:** [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- **Codex model discovery, capabilities, token use, and reroute events:** [Codex app server](https://learn.chatgpt.com/docs/app-server)
- **Codex configuration:** [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
- **Codex non-interactive JSON events:** [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
- **Prompt guidance:** [GPT-5.6 prompting best practices](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices)
- **Prompt migration and ablation guidance:** [Prompting guidance for GPT-5.6 Sol](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6.md)
- **Cross-platform parity source (Claude agent definitions):**
  `speckit-pro/agents/consensus-synthesizer.md` and
  `speckit-pro/agents/gate-validator.md`
