# PRD: Codex Agent Model Routing and Graceful Fallback

**Status**: Active - not yet implemented
**Source**: Maintainer request plus current official OpenAI documentation,
revalidated under the evidence-authority contract below
**Created**: 2026-07-09
**Last updated**: 2026-07-16
**Target window**: Next SpecKit Pro minor release after the evaluation and
installer specifications in this roadmap are implemented
**Legacy identifier note**: The stable `G56R` SPEC prefix originated when this
work was scoped to GPT-5.6. It remains for traceability, but the candidate
catalog includes any supported Codex model that satisfies an agent's contract.
**Parity note**: This PRD is the Codex half of the shared twelve-agent catalog.
The Claude half is defined by the companion Claude routing PRD; the two
documents mirror each other and diverge only for platform-specific
implementation requirements.

---

## Evidence Authority

- The shared
  [agent-routing parity contract](ai/specs/agent-routing-parity-contract.md)
  governs structure, evidence classes, source records, historical integrity,
  and fail-closed behavior for CAR and G56R.
- Official OpenAI documentation under `learn.chatgpt.com/docs/**`,
  `developers.openai.com/codex/**`, `developers.openai.com/api/docs/**`, and
  `platform.openai.com/docs/**` is the sole authority for Codex and OpenAI
  platform facts, including model IDs and positioning, supported configuration
  fields, reasoning controls, telemetry fields, lifecycle, and client-surface
  behavior.
- Repository files, generated payloads, installed caches, and Claude agent
  definitions are project inputs used to inventory the current implementation
  and define SpecKit Pro role contracts. They cannot establish an OpenAI model,
  capability, configuration field, telemetry field, or native behavior.
- Responses from documented runtime methods and bounded invocation probes may
  verify environment availability or exact treatment for an already
  documented candidate. They cannot add a candidate or broaden a platform
  claim.
- Controlled SpecKit Pro evaluations may qualify and rank document-eligible
  routes against project role contracts. Those results are product
  qualification evidence, not authority for platform behavior.
- If official documentation does not establish a required platform fact, the
  fact is `undocumented` and the dependent claim or route fails closed. Support
  articles, marketing pages, news posts, repository inference, runtime success,
  and neighboring-model analogy cannot promote it to a platform fact.
- The official-source ledger is versioned and revalidated before each G56R
  scaffold that consumes it and again before release. A changed, conflicting,
  inaccessible, or withdrawn source invalidates bound candidates and claims.

---

## 1. Problem

> Which evidence-backed preferred model and reasoning-effort route, with which
> ordered qualified fallbacks, should SpecKit Pro install for each named Codex
> agent so that the agent remains usable when its preferred route is unavailable
> without silently changing its role, tools, safety boundary, or output
> contract?

SpecKit Pro currently defines ten named Codex custom agents: nine required core
agents and the optional `autopilot-fast-helper`. The Claude plugin also defines
two orchestration-support agents with no Codex counterpart:
`consensus-synthesizer` and `gate-validator`. Cross-platform agent parity is a
governing principle: both platforms define the same named agents under each
platform's official configuration surface and diverge only for
platform-specific implementation requirements. This plan therefore targets a
twelve-agent Codex catalog: eleven required core agents (the nine current core
roles plus the two net-new parity additions) and the optional helper. The
existing definitions pin one model or
inherit one configuration, but they do not express an evidence-backed ordered
fallback policy. A model may also be absent, an effort may be unsupported, or
the exact configured treatment may fail even when a catalog entry exists.
Without a project-owned resolver, installation can either fail late or silently
produce a different runtime than the one evaluated.

Current official OpenAI documentation establishes these platform facts:

- The [Codex models documentation](https://developers.openai.com/codex/models)
  publishes model IDs, surface availability, and general model/effort guidance.
- Each custom-agent file describes one named agent and may set `model` and
  `model_reasoning_effort`; documented optional values inherit from the parent
  when omitted.
- The [Codex app-server documentation](https://learn.chatgpt.com/docs/app-server)
  defines `model/list`, `modelProvider/capabilities/read`, token-usage updates,
  and `model/rerouted` events for that surface.
- Applicable project or skill instructions can request named subagent
  delegation.
- The [non-interactive-mode documentation](https://learn.chatgpt.com/docs/non-interactive-mode)
  defines JSONL lifecycle, item, and error events for `codex exec --json`; it
  does not document universal effective-model, effective-effort, or token-usage
  fields.

The following are proposed SpecKit Pro policies, not claims about native Codex
fallback behavior:

- one preferred route and an ordered list of independently qualified fallback
  routes for each named agent;
- documented capability discovery and bounded availability probes;
- one canonical resolver and materializer shared by evaluation and install;
- complete-matrix atomic installation with previous-install preservation;
- strict explicit override behavior; and
- route-resolution, exact-treatment, and release identities.

A route is more than a model name. It includes an explicit model and explicit
reasoning effort plus the instruction hash, required model and modality
capabilities, tool/skill/MCP contract, sandbox and mutation contract, supported
client range, and qualification evidence. A fallback may change only the
approved model/effort route for the same named agent. It cannot substitute a
different named agent, a generic agent, or a weaker safety/tool contract.

The official source set does not publish a complete benchmark for SpecKit Pro's
twelve roles. Model branding, generation, or placement in product guidance
therefore does not qualify a route. The PRD admits candidates only from official
documentation, uses controlled evaluation to qualify preferred and fallback
routes, then resolves installation against a versioned capability snapshot from
the user's working Codex environment.

The evaluation boundary is the accepted end-to-end workflow, not an isolated
agent response. It includes parent and child work, retries, validation, repairs,
compaction, cancellations, and abandoned branches. Long-horizon work is a
powered comparative stratum in the release decision and also has separate
recovery canaries. Resource evidence remains environment-independent: raw token
vectors, duration, retries, compaction, and accepted-workflow rate.

## 2. Goals, Product Contract, and Non-goals

### 2.1 Goals

- Give every required named agent one evidence-backed preferred route and zero
  or more ordered, independently qualified fallback routes.
- Give the optional helper a preferred route, qualified helper fallbacks, and a
  validated no-helper path.
- Maintain the same named agents on both the Codex and Claude platforms,
  following each platform's official documentation and diverging only for
  platform-specific implementation requirements; this plan delivers the Codex
  half of the shared twelve-agent catalog.
- Preserve role-specific correctness, grounding, safety, mutation, output,
  tool, and orchestration contracts across every route.
- Select preferred routes quality and reliability first, then use one
  predeclared environment-independent resource/latency rule among passing
  candidates.
- Materialize explicit model and reasoning-effort values; never rely on an
  unmeasured inherited default in installed destination policies.
- Resolve the complete required-agent matrix before one atomic write, and
  preserve the previous known-good installation when any required agent has no
  safe compatible route.
- Report the preferred route, effective route, fallback index, and resolution
  reason for every installed named agent.
- Keep the explicit global model override strict: an unavailable or
  incompatible requested override fails atomically rather than silently falling
  back.
- Use the same materializer and exact-treatment predicate in evaluation and
  installation.
- Include bounded prompt and context tuning when it targets measured overhead,
  while retaining an unchanged-prompt attribution stage.
- Compare the selected static policy with frozen unpinned and adaptive controls
  before describing the static result as efficient.
- Make installed Codex skills explicitly spawn the required custom agents by
  name and prove that their returned work affects a downstream decision,
  artifact, or validation result.
- Rebuild and reconcile payloads, active guidance, installed-cache evidence,
  fallback UAT, and rollback evidence before release.

### 2.2 Non-goals (out of scope)

- Detecting or classifying commercial subscription plans, entitlements,
  workspaces, billing, credits, allowances, quotas, rate limits, or account
  upgrades. None of those may determine route selection, fallback order,
  installation, evaluation, UAT, or release eligibility.
- Changing Claude agent models, Claude commands, or Claude marketplace
  behavior.
- Claiming that ordered model fallback is a native custom-agent TOML feature.
  SpecKit Pro owns the ordered route policy, resolver, and materializer.
- Adopting GPT-5.6 Pro mode, persisted reasoning, Programmatic Tool Calling,
  explicit prompt caching, or the Responses API multi-agent beta.
- Unbounded or aesthetic prompt rewriting. Prompt changes must target measured
  instruction, handoff, tool-schema, duplicated-context, or compaction overhead
  and be tested against an unchanged-prompt control.
- Offering quality/balanced/economy profiles or arbitrary per-agent user
  overrides in v1. The existing one-model compatibility override remains the
  KISS escape hatch and is strict.
- Searching the complete eleven-agent combination space or claiming global
  assembled-policy optimality. Version 1 performs component-wise route and
  prompt selection, then confirms the assembled preferred core.
- Automatically selecting an unqualified adjacent model, changing a named
  agent, or weakening its prompt, sandbox, tools, skills, MCP, mutation, or
  output contract during fallback.
- Building production checkpoint/resume or external-limit-aware scheduling. Evaluation
  budgets and failure simulations do not create a new workflow scheduler.
- Rewriting historical model references or archived evidence solely to make
  repository-wide searches uniform.

### 2.3 Route and Identity Lifecycle

One route is the following complete, qualified tuple:

```text
route = explicit model
      + explicit model_reasoning_effort
      + instruction/prompt hash
      + required model and modality capabilities
      + required tool/skill/MCP contract
      + sandbox/mutation contract
      + supported client range
      + qualification evidence
```

The identity lifecycle is intentionally staged so early experiments do not
depend on final aggregates that do not yet exist.

| Identity | Created by | Required contents |
|---|---|---|
| `agent_contract_id` | G56R-001 | Named role plus safety, grounding, mutation, tool, and output contract |
| `official_source_ledger_id` | G56R-001 | Source family, retrieval method, requested/canonical official URLs, retrieval dates, supported surfaces, exact documented facts, undocumented gaps, and source invalidation rules |
| `effort_surface_record_id` | G56R-001 | Source-scoped effort/default evidence for model guidance, custom-agent TOML, config TOML, app-server catalog, and API guidance surfaces |
| `candidate_route_id` | G56R-001/G56R-002 | G56R-001 source-bound model candidate or G56R-002 executable model/effort tuple, effort-surface record binding, official-source-ledger binding, contract and instruction hashes, required capabilities, rationale, and invalidation rules |
| `telemetry_profile_id` | G56R-002 | Pinned client/surface and telemetry fields classified as `stable_native`, `experimental_native`, `derived_from_controlled_configuration`, `conditional`, `unavailable`, `not_applicable`, or `undocumented` |
| `runtime_capability_snapshot_id` | G56R-002 or installer preflight | Client/surface, available models, efforts and capabilities, timestamp, retrieval/probe method, and raw environment observation; never candidate authority |
| `experiment_policy_id` | G56R-003 | Corpus and partitions, scorer, analysis plan, budgets, terminal policy, and treatment controls |
| `execution_trace_id` | G56R-003 | Assigned route, effective-route evidence, task outcome, resource evidence, retries, terminal state, and treatment integrity |
| `agent_route_policy_id` | G56R-007 through G56R-010 | Named agent, preferred route, ordered fallbacks, hard contract, evidence, client bounds, and invalidation rules |
| `route_resolution_id` | G56R-002 schema; G56R-003/G56R-006 records | Preferred and effective routes, fallback index and reason, attempted routes, capability snapshot, and timestamp |
| `resolved_agent_policy_id` | G56R-006 schema/fixtures; G56R-011 final records | Exact materialized destination content and selected effective route for one named agent |
| `core_routing_policy_id` | G56R-011 | Ordered mapping of the eleven required named agents to final route policies |
| `optional_helper_policy_id` | G56R-011 | Helper preferred route, qualified fallbacks, no-helper contract, and integration reference |
| `resolved_installation_id` | G56R-011 | Ordered mapping of installed agents to resolved policies and resolution evidence |
| `release_policy_id` | G56R-011 | Final core, helper state, resolver/installer version, evidence lock, UAT, invalidation rules, and bounded claims |

`core_routing_policy_id`, `optional_helper_policy_id`, and `release_policy_id`
are attached to evidence only after G56R-007 through G56R-010 finish route
selection and G56R-011 composes the aggregates.

## 3. Acceptance Criteria

### 3.1 Research Baseline and Candidate Routes *(-> G56R-001)*

- **AC-1.1**: A dated research record inventories all twelve named target agents
  (the ten current Codex agents plus the parity additions
  `consensus-synthesizer` and `gate-validator` derived from the Claude plugin)
  and every active source, installer, skill, validation, evaluation,
  generated-payload, and installed-cache surface that encodes or consumes their
  route policy. The inventory is labeled `project_input` and cannot establish
  OpenAI platform facts or candidate eligibility.
- **AC-1.2 - Official-source ledger**: The record cites only current official
  OpenAI documentation for every shared research-matrix family: model IDs and
  lifecycle, custom-agent fields, reasoning controls, skills and instructions,
  tools and MCP, sandboxing, hooks, discovery, noninteractive output,
  telemetry, authentication, availability, pricing, cost, and analytics. Every
  platform claim records its source-ledger ID, canonical URL, retrieval
  timestamp, supported surface, exact fact, bounded extract and hash, claim
  binding, gap, and invalidation trigger. Conflicting or absent claims are
  blocked or marked `undocumented`.
- **AC-1.3**: Every agent has an immutable production route (recorded as absent
  for the two parity additions), a role-specific contract, candidate routes
  admitted only by the official-source ledger, prompt/context candidates when
  justified, and a fixture backlog. G56R-001 records model/effort tuples as
  non-executable until documented model support, surface-specific effort
  support, environment availability, and exact treatment are verified. Runtime
  discovery and probes may narrow availability but cannot introduce a model or
  effort outside the official ledger. Before G56R-003 freezes the executable
  set, G56R-002 may add a role/model binding only for a model already present
  in the G56R-001 ledger and only with role-contract rationale or explicit
  exclusion evidence. It cannot introduce a model ID outside that ledger.
  A model, effort, or role/model binding is excluded only for recorded
  incompatibility, contract failure, or predeclared dominance evidence.
- **AC-1.4**: Platform facts, reasonable inferences, proposed SpecKit Pro
  policies, project inputs, runtime observations, qualification evidence, and
  undocumented facts are visibly separated under the shared five-class
  contract. Only official documentation may support a platform fact. No
  head-to-head benchmark or native fallback feature is claimed where none is
  documented.
- **AC-1.5 — Research completion without a dependency cycle**: The time-boxed
  research spike ends with an official-source ledger, provisional
  candidate-route manifest,
  role-contract catalog, fixture backlog, telemetry requirements, unresolved
  capability questions, and a go/no-go handoff to G56R-002. It does not depend
  on G56R-002 results, change installed defaults, or claim that a candidate is
  executable before capability preflight.
- **AC-1.6 — Candidate route and fallback manifest**: Before scored screening,
  G56R-001 publishes a Schema `2.0.0` `agent_route_candidate_manifest`
  covering all twelve named agents under the same top-level and record-level
  contract as CAR-001. It records the immutable comparator, source ledger,
  effort surfaces, project inputs, role contracts, source-bound candidates,
  fixtures, telemetry, capability questions, traceability, decisions,
  historical fact dispositions, and invalidation rules. Platform differences
  remain values, explicit statuses, nulls, or empty arrays rather than
  platform-only schema fields. Every candidate binds source-ledger and effort-
  surface records and remains non-executable pending capability verification
  and qualification. The two parity additions retain role contracts derived
  from Claude definitions and record no current Codex production route.
  G56R-002 later binds the manifest to a versioned runtime capability snapshot,
  expands listed source-bound candidates and any newly justified ledger-bound
  role/model bindings into supported model/effort tuples,
  and freezes the executable candidate set before G56R-003 scores outcomes.
- **AC-1.7 — Current harness baseline**: The research record labels historical
  prompt-emulation results as `non_release_evidence` until G56R-003 replays them
  through the shared materializer with exact treatment and the required skills,
  MCP servers, tool schema, sandbox, parent configuration, and telemetry proof.

### 3.2 Route Evaluation and Qualification *(-> G56R-002 through G56R-004)*

- **AC-2.1 — Controlled model-effort pair selection**: Stage A1 screens each
  eligible model at its documented default ordinary effort after exact
  treatment is proven. Stage A2 holds the model and all non-effort variables
  fixed, ascends when necessary to find a pass, then descends through every
  supported lower ordinary effort and retests the failing boundary. Stage A3
  compares frozen passing model-effort pairs with every non-candidate variable
  frozen. Stage B admits only A3-shortlisted pairs and evaluates predeclared
  prompt-by-pair interactions. Stage C freezes the complete cohort policy and
  evaluates it once on its disjoint cohort-lock partition. Stage A selects
  model-effort pairs; it does not claim independent model and effort effects.
- **AC-2.2 — Capability discovery and controlled environment**: The harness
  binds every run to a pinned Codex client/surface, candidate route, controlled
  repository/task environment, and versioned
  `runtime_capability_snapshot_id`. The snapshot records discovered model IDs,
  supported reasoning efforts, relevant model/provider capabilities, client
  version, retrieval/probe method, timestamp, and raw evidence. When
  authoritative model discovery is unavailable, the harness may use a
  predeclared exact-invocation availability probe only to test installation-time availability
  of a candidate already admitted by the official-source ledger. A probe cannot
  establish model support, effort support, candidate eligibility, or any other
  platform claim; unresolved availability blocks that route's scored run.
- **AC-2.3 — Route-resolution and execution trace**: Every assigned objective
  binds `candidate_route_id`, `agent_contract_id`,
  `runtime_capability_snapshot_id`, `route_resolution_id`,
  `experiment_policy_id`, and `execution_trace_id`. The trace records requested
  and effective model/effort when the telemetry profile supports those claims,
  fallback index and reason, service-reroute events, instruction hash, effective
  sandbox and approvals, loaded skills/MCP/tools, parent-child graph, token
  categories when exposed, wall time, retries, compaction, validation,
  cancellation, terminal state, and outcome. Nulls are preserved. Final
  core/helper/release aggregate IDs are attached only after those aggregates
  exist. A service reroute is always recorded separately from SpecKit Pro route
  resolution and never reported as plugin fallback. Any service reroute makes
  the run non-scorable as qualification evidence for the requested route.
- **AC-2.4 — Telemetry capability profile**: G56R-002 publishes a versioned
  telemetry capability profile for the pinned client and surface. Qualification
  classifies each desired field as `stable_native`, `experimental_native`,
  `derived_from_controlled_configuration`, `conditional`, `unavailable`,
  `not_applicable`, or `undocumented`. A native class requires the
  official-source ledger to document that field for the pinned surface.
  Controlled configuration may prove requested assignment but cannot prove an
  undocumented returned or effective value. Qualification
  requires complete evidence only for fields classified as mandatory by that
  profile: successful treatment assignment, effective route or an approved
  proof of configured route with no unapproved reroute, task outcome, duration,
  and raw token fields needed by the declared endpoint. Conditional or
  unavailable fields remain null and cannot support claims that require them.
  Telemetry failure classification, bounded complete-pair reruns, attrition
  reporting, and no arm-only discretionary reruns are predeclared.
- **AC-2.5 — Environment-independent resource evidence**: The primary resource
  evidence is the complete objective-level raw token vector, request/turn count,
  wall time, retries, compaction, and failed or abandoned work through the
  terminal policy. The selection rule uses one predeclared
  environment-independent score or Pareto rule across passing candidates.
- **AC-2.6 — Per-agent attribution**: Paired per-agent experiments freeze the
  parent route, every non-candidate agent route, all prompts other than the
  allowed Stage B candidate prompt, tools, skills, MCP, sandbox, repository
  snapshot, context/compaction policy, retry/escalation policy, validation, and
  acceptance checker. Unpinned and adaptive runs are policy-level controls and
  are not evidence attributable to one agent.
- **AC-2.7 — Objective-level estimand**: For each randomized objective `i`,
  `R_i` is all attributable resource consumption from assignment until
  acceptance or the predeclared terminal stop, and `A_i` is one only when the
  objective is accepted. Candidate-caused failures, timeouts, cancellations,
  budget exhaustion, and abandoned branches remain in `R_i` with `A_i = 0`.
  Independently proven transient harness failure is classified before outcome
  inspection and may receive only the bounded full-pair rerun defined in the
  analysis plan.
- **AC-2.8 — Statistical unit and workload population**: The primary unit is a
  unique workflow objective; repeats are clustered within objective and paired
  inference occurs at the task level. Before screening, a versioned workload
  manifest freezes pre-treatment stratum definitions, target weights, unknown
  handling, minimum unique tasks, and cache-state isolation. Strata and weights
  cannot be selected from candidate outcomes.
- **AC-2.9 — Long-horizon comparative evidence**: The workload manifest defines
  long-horizon membership from task and protocol characteristics before either
  arm runs, never from realized duration, turns, tokens, retries, or
  compactions. Integrated confirmation contains a powered long-horizon stratum
  that independently clears accepted-workflow, semantic-quality, raw-resource,
  p95-resource, p95-duration, late-failure, retry, and compaction guardrails. A
  long-horizon efficiency claim additionally requires its predeclared
  superiority endpoint; recovery canaries cannot substitute for this evidence.
- **AC-2.10 — Prompt interaction stage**: Model/effort attribution uses the
  unchanged baseline prompt. Only Stage A-shortlisted pairs enter prompt/context
  interaction evaluation, where only the candidate agent's bounded prompt may
  vary. After one final instruction hash is selected, every preferred and
  fallback route is requalified under that same instruction hash. The selected
  model, effort, prompt, and fallback order are then frozen as one route policy
  for cohort lock and integrated confirmation.
- **AC-2.11 — Search and campaign bounds**: For every model, capability probing
  produces an ordered supported-effort set. The predeclared rule starts at the
  documented default, ascends to the first stable pass when necessary, then
  descends and boundary-retests to find the lowest stable ordinary effort.
  Ultra or any mode that changes orchestration topology is a policy-level
  control, not an ordinary per-agent effort. Campaign raw-token use, wall time,
  candidate count, futility rules, racing method, and confirmation-entry cap are
  frozen before outcome-bearing runs.
- **AC-2.12 — Evidence partitions and multiplicity**: Screening, selection,
  cohort lock, and integrated release confirmation use disjoint objective sets.
  The final confirmation set is used exactly once after candidates, prompts,
  margins, endpoints, guardrails, stopping rules, and multiplicity strategy are
  locked. Changing any locked decision invalidates affected evidence.
- **AC-2.13 — Immutable production comparator**: Before screening, the immutable
  production comparator is pinned by repository revision, plugin version,
  per-agent route/configuration IDs, client version, tool/configuration contract,
  corpus snapshot, prompt hashes, and analysis plan. Candidate routes compare
  with the corresponding production role route; integrated release compares the
  final assembled preferred core with the immutable production core. A parity
  addition with no production role route qualifies against its absolute
  contract, quality, and reliability floors; the workflow-level integrated
  comparison still pairs the assembled eleven-agent core against the immutable
  production core on the same objectives. The
  immutable production comparator remains the sole release baseline.
- **AC-2.14 — Missing telemetry and attrition**: Every attempt records missing
  fields, cause classification, evidence, rerun eligibility/count, and final
  disposition. Only independently proven transient harness failures can receive
  a capped full-pair rerun under the original assignment. Candidate-inherent,
  environment-inherent, recurrent, unknown, or arm-differential telemetry loss
  fails qualification or blocks the affected claim. No primary conclusion may
  use an unexplained complete-case subset.
- **AC-2.15 — Guardrail registry**: Before outcome-bearing evaluation, every
  mandatory safety, quality, grounding, mutation, accepted-workflow, p95
  resource/duration, late-failure, retry, steering, and compaction guardrail has
  a definition, unit, denominator, comparator, margin, confidence method,
  missing-data rule, multiplicity position, and minimum unique-task count.
  Human steering is prohibited or follows one frozen scripted intervention
  policy.
- **AC-2.16 — Analysis plan and decision rule**: A versioned analysis plan
  predeclares the primary endpoint, practical margin, one-sided confidence rule,
  alpha/multiplicity strategy, target power, variance and clustering assumptions,
  sample sizes, racing adjustment, attrition thresholds, terminal policy, and
  `inconclusive => no qualification`. Numeric thresholds live in this plan or a
  content-addressed registry, not in post-hoc review judgment.
- **AC-2.17 — Policy controls and dominance**: G56R-004 defines and freezes the
  unpinned, adaptive, and topology-changing controls, their execution contracts,
  parameters, eligibility floors, dominance metrics, margins, multiplicity, and
  untouched comparison partition. G56R-011 later compares the final frozen core
  with those controls. A control materially dominates only when it passes every
  mandatory contract, safety, quality, reliability, and availability gate and
  clears the predeclared resource/duration dominance rule.
- **AC-2.18 — Optional helper availability contract**:
  `autopilot-fast-helper` is optional and excluded from the required-core
  primary statistic. G56R-010 selects a preferred helper route, zero or more
  independently qualified helper fallback routes, and a validated no-helper
  path. Installation resolves the first available qualified helper route; when
  none is available, the helper is not installed and autopilot continues
  through the no-helper contract.
- **AC-2.19 — Exact treatment and fallback resolution**: Every scored run
  executes an installed custom-agent configuration or a configuration produced
  by the same canonical materializer used by the installer. Equivalence
  requires byte-identical serialization of plugin-owned fields and equality of
  the predeclared route, instructions, sandbox/mutation class, skills, MCP
  servers, tool schema, relevant parent configuration, client version, and
  controlled runtime overrides. Preferred-route unavailability invokes the
  resolver before assignment. A scored run begins only after one approved route
  is resolved and exact treatment is proven. Runtime UAT may continue after a
  service reroute only when the event identifies a route already qualified for
  the same named agent; the event and resulting route remain service behavior,
  never resolver success. An unapproved or unidentifiable reroute is a hard
  treatment failure. `codex exec --json` lifecycle output is not treated as
  universal proof of effective model or effort when the pinned telemetry
  profile does not expose those fields.
- **AC-2.20 — Blinded fixture and scorer governance**: Before evaluation, each
  fixture and scorer has a versioned contract, independent validity review, and
  frozen acceptance behavior. Low or surprising output is adjudicated blind to
  candidate identity as exactly one of candidate quality failure, treatment-
  delivery failure, invalid fixture, invalid scorer, or infrastructure failure;
  no score threshold predetermines the cause. Changing a fixture or scorer
  increments its version and invalidates every affected candidate result.
  Neither may change after its selection or confirmation partition locks.
  Historical results produced without exact-treatment proof remain
  non-release evidence.
- **AC-2.21 — Preferred and fallback route qualification**: For each required
  agent, the preferred route is the highest-ranked route that clears all hard
  contract, absolute quality/reliability, and production non-inferiority gates
  under the predeclared environment-independent selection rule. An ordered
  fallback route is eligible only when it clears the same hard contract and the
  declared fallback quality/reliability floor. The final
  `agent_route_policy_id` records the preferred route, ordered eligible
  fallbacks, evidence IDs, and invalidation triggers. G56R-011 confirms the
  assembled preferred core and separately verifies resolver behavior for
  preferred unavailable, effort unsupported, treatment-probe failure, service
  reroute, no safe route, and optional-helper absent scenarios.

### 3.3 Capability-aware Installer and Strict Override *(-> G56R-006)*

- **AC-3.1**: The installer consumes final per-agent route policies and a
  runtime capability snapshot, resolves one effective route for every required
  named agent, and creates content-addressed `route_resolution_id` and
  `resolved_agent_policy_id` evidence for framework fixtures. After every route
  policy is locked, G56R-011 creates the final `resolved_agent_policy_id`
  records and composes `resolved_installation_id`.
- **AC-3.2**: Default installation automatically selects the first compatible
  route in each agent's ordered policy and reports every fallback. It never
  changes the named agent, prompt, sandbox, tools, skills, MCP, output contract,
  or mutation boundary as part of model fallback.
- **AC-3.3**: The installer resolves the complete matrix before writing. If
  every required agent has a safe route, it commits atomically. If any required
  agent has no safe route, it preserves the previous known-good installation
  and reports the unresolved agent, attempted routes, rejection reasons, and
  remediation. An optional helper with no safe route is omitted and uses the
  validated no-helper path without failing the core install.
- **AC-3.4**: Bundled source policies are never mutated. Destination copies
  contain explicit effective model and effort; omitted inherited defaults do
  not satisfy the contract. The plugin-managed destination set contains
  exactly the eleven core agent files plus the helper only when resolved;
  unrelated user files are preserved and excluded from that count. Reinstall
  without a helper removes a stale plugin-managed helper atomically.
- **AC-3.5**: The explicit global model override remains strict, validates every
  resulting named-agent route and effort before mutation, and aborts atomically
  when unavailable or incompatible. It does not use the default fallback chain
  or silently coerce effort.
- **AC-3.6**: Install output reports preferred and effective routes, fallback
  indices and reasons, capability snapshot, attempted/rejected routes, copied
  files, optional-helper state, previous-install disposition, verification
  result, and restart requirement.

### 3.4 Quality-critical Executor Routing *(-> G56R-007)*

- **AC-4.1**: `phase-executor`, `implement-executor`, and `analyze-executor`
  screen every eligible model/effort route from the frozen candidate manifest;
  named models are hypotheses, not predetermined winners.
- **AC-4.2**: Each agent's preferred route and every committed fallback clear
  the role qualification rules on planning, TDD implementation, and
  analysis/remediation fixtures before the cohort lock.
- **AC-4.3**: Sandbox, TDD, grounding, artifact, validation, and remediation
  contracts remain hard invariants across route, prompt/context, and fallback
  evaluation.
- **AC-4.4**: Each role follows the staged pair, prompt-interaction, and cohort-
  lock design. Only G56R-011 supplies integrated release confirmation.
- **AC-4.5**: Each final `agent_route_policy_id` records the preferred route,
  ordered fallbacks, evidence, supported client bounds, invalidation triggers,
  install proof, and rollback evidence.

### 3.5 Structured-work Agent Routing *(-> G56R-008)*

- **AC-5.1**: `checklist-executor` and `uat-runbook-author` screen every eligible
  route, including bounded-work candidates when their tool and output contracts
  pass.
- **AC-5.2**: Checklist remediation remains complete at every severity; UAT
  runbooks remain executable, plain-English, non-circular, and traceable to
  acceptance criteria.
- **AC-5.3**: Preferred and fallback routes preserve each role's workspace-write
  boundary and fail-open/fail-closed behavior and clear component qualification
  plus the disjoint cohort lock.
- **AC-5.4**: Each final `agent_route_policy_id` contains the complete route
  order, contract, evidence, client bounds, invalidation rules, install proof,
  and rollback evidence.

### 3.6 Read-only Reasoning and Orchestration-support Agent Routing *(-> G56R-009)*

- **AC-6.1**: `clarify-executor`, `domain-researcher`, `codebase-analyst`,
  `spec-context-analyst`, `consensus-synthesizer`, and `gate-validator` screen
  every eligible route; lighter routes remain only when their grounding,
  citation, and output contracts pass.
- **AC-6.2**: Each model follows the ordered effort search and boundary-retest
  contract; selection cannot stop after testing only one lower effort.
- **AC-6.3**: Every route remains grounded in its assigned evidence domain,
  preserves citations or file locators, and performs no writes.
- **AC-6.4**: One model is not forced across all six roles. Each final
  `agent_route_policy_id` records its independently qualified preferred route
  and ordered fallbacks.
- **AC-6.5**: Exact-treatment evaluation, bounded prompt/context tuning, cohort
  lock, install proof, and rollback evidence follow the shared contract; release
  proof remains G56R-011.
- **AC-6.6**: The two parity additions are authored as named Codex custom agents
  per current official custom-agent documentation before route qualification,
  with role contracts mirroring the Claude definitions (three-analyst consensus
  synthesis with confidence assessment; structured gate-validation evidence).
  Any platform-specific divergence from the Claude contract is recorded
  explicitly.

### 3.7 Optional Latency-first Helper Routing *(-> G56R-010)*

- **AC-7.1**: `autopilot-fast-helper` remains optional. It receives one
  preferred route, zero or more qualified fallback routes, and a validated
  no-helper path. Candidate eligibility comes from the official-source ledger;
  current availability is established separately through documented runtime
  discovery or a bounded availability probe.
- **AC-7.2**: Every helper route remains read-only and advisory, bounded to
  compression, triage, and query drafting, and never performs SpecKit reasoning
  or mutation.
- **AC-7.3**: The helper scorecard measures functionality, latency, raw resource
  evidence, spawn reliability, and resolver behavior. An omitted effort cannot
  select an unmeasured inherited default.
- **AC-7.4**: Autopilot continues correctly when no helper route resolves, the
  helper is not installed, is not invoked, or fails to spawn. The no-helper path
  is a release requirement.
- **AC-7.5**: The helper's `agent_route_policy_id` binds the preferred route,
  ordered fallbacks, qualification evidence, invalidation triggers, and
  rollback proof. G56R-011 combines it with the no-helper contract and
  installation state to create `optional_helper_policy_id`.

### 3.8 Payload, Installed UAT, and Release Proof *(-> G56R-011)*

- **AC-8.1**: The Codex payload is rebuilt from source. All twelve source and
  payload agent definitions, manifests/checksums, eleven required destination
  policies, optional installed helper, final identities, and active guidance
  reconcile without hand-editing generated artifacts.
- **AC-8.2**: Active Codex guidance explains preferred routes, qualified
  fallback, strict override, resolver reporting, restart, optional-helper/no-
  helper behavior, and bounded evidence claims without rewriting history.
- **AC-8.3**: Focused structural, installer, replay, payload, installed-cache,
  active-path, and UAT gates pass on the final implementation. Every surface
  agrees on the identity it owns and distinguishes requested configuration,
  route resolution, environment evidence, and runtime observation.
- **AC-8.4 — Installed fallback UAT**: Installed UAT uses actual skill entry
  points and covers the preferred path for every routed cohort; at least one
  deterministic preferred-unavailable fallback per route-policy class;
  unsupported-effort resolution; treatment-probe failure; approved and
  unapproved service-reroute handling; no-safe-route preservation of the
  previous installation; optional-helper resolved and no-helper behavior;
  strict override failure; and rollback. UAT records the named agent,
  `route_resolution_id`, effective model/effort when proven, exact-treatment
  evidence, returned result hash, and downstream consuming step.
- **AC-8.5**: Release messaging states only the routes, fallback behavior,
  quality/reliability evidence, resource evidence, and supported client bounds
  that were proven. It includes rollback through the previous known-good
  installation or a previous plugin release.
- **AC-8.6**: The release packet lists `core_routing_policy_id`,
  `optional_helper_policy_id`, `resolved_installation_id`, `release_policy_id`,
  `official_source_ledger_id`, every `agent_route_policy_id`, rejected
  candidates, capability and telemetry profiles, analysis-plan lock,
  qualification and control results, UAT, remaining gaps, and review order.
- **AC-8.7**: Release evidence pins minimum/tested Codex versions, candidate
  manifest, official-source ledger, runtime capability snapshot, telemetry
  profile, prompts, tool and context contracts, materializer/resolver versions,
  analysis plan, workload manifest, route policies, and release policy. Changes
  trigger the predeclared scope of source review, requalification, fallback
  revalidation, or integrated confirmation.
- **AC-8.8**: Deterministic documentation checks validate relative links,
  current versus proposed paths, the twelve-agent count, PRD-to-roadmap ownership,
  acyclic dependencies, candidate-versus-final identity lifecycle, exact-
  treatment wording, fallback ownership, strict override, atomic no-write,
  helper/no-helper behavior, and skill-to-agent coverage. They reject retired
  non-capability routing requirements and unsupported claims that native
  custom-agent TOML provides ordered fallback.
- **AC-8.9 — Integrated release gate**: After G56R-007 through G56R-010 lock
  their policies, G56R-011 composes one `core_routing_policy_id` from the
  eleven required preferred routes and evaluates it exactly once against the
  immutable production core on the untouched integrated confirmation corpus. The core
  must pass every contract, safety, quality, reliability, accepted-workflow,
  predeclared environment-independent resource-superiority, long-horizon, and
  simultaneous guardrail gate. Frozen controls run as predeclared secondary
  arms on untouched data and gate the bounded efficiency wording without
  changing the primary comparator. Failure reopens route, prompt, or
  orchestration selection and requires new versioned confirmation evidence.
  Passing proves bounded improvement over production, not global assembled-
  policy optimality.
- **AC-8.10 — Capability support claim**: Support means the eleven required named
  agents resolve from qualified route policies, install atomically, deliver
  exact treatment in the tested Codex client/surface, and preserve the previous
  installation when resolution fails. The claim is limited to the tested
  technical capability contract and does not promise uninterrupted completion
  under an external usage limit.
- **AC-8.11 — Optional-helper release gate**: G56R-010 and G56R-011 separately
  prove the helper's preferred route, qualified fallbacks, spawn reliability,
  latency/resource evidence, and no-helper behavior. Helper results do not enter
  the required-core primary statistic unless a later analysis plan explicitly
  defines a comparable integrated policy.
- **AC-8.12 — Long-workflow recovery canaries**: A pre-treatment portfolio
  contains at least the minimum unique-task count from the analysis plan. Each
  task declares at least four phases and its scripted multi-agent, interruption,
  validation-repair, compaction-stress, cancellation, or resume event before
  treatment. Across the portfolio, at least one task exercises each named event
  class. Active model time, tool wait, and human wait are separated. These
  canaries validate operability and recovery only and never substitute for
  AC-2.9 comparative long-horizon evidence.
- **AC-8.13 — Skill-to-agent and model-fallback proof**: Before release,
  G56R-011 publishes a versioned `skill_agent_usage_manifest` covering every
  active Codex skill entry point and all twelve source agents. Each mapping records
  skill ID and instruction hash, exact installed agent name, trigger/phase,
  `required`, `conditional`, `prohibited`, or `not_applicable` state, spawn
  condition, result-consumption contract, and allowed model-route fallback.
  Every applicable skill explicitly directs Codex to spawn the named installed
  custom agent. Across the manifest, every required core agent has at least one
  production skill path; the helper remains conditional.

  Representative UAT invokes the actual installed skills, not a direct harness
  call. Across those workflows, every one of the eleven core agents is observed at
  least once under a predeclared trigger. Each trace binds `skill_id` and skill
  hash to the named-agent spawn, `route_resolution_id`, effective model/effort
  when proven, exact-treatment evidence, returned result hash, and downstream
  decision, artifact, or validation step that consumed the result. Fallback
  changes only the approved model/effort route within that same named agent.
  Missing a required spawn, leaving returned work unused, substituting a
  different named or generic agent, or injecting the agent directly from the
  harness fails release proof. The separate helper campaign proves the same
  chain when a helper route resolves and proves the no-helper path otherwise.
  No single workflow must spawn all twelve agents.

### 3.9 Budgets, Controls, Fallback, and Recovery *(-> G56R-004, G56R-005, G56R-011)*

- **AC-9.1**: The harness declares maximum campaign and per-objective resource
  use/time, retries, subagent threads/depth, context growth, probe attempts, and
  redundant work. These are evaluation controls, not production scheduler
  features.
- **AC-9.2**: Adaptive controls define observable escalation signals, qualified
  escalation/de-escalation routes, retry and cancellation bounds, and evidence
  requirements. They cannot choose a model or effort outside the frozen
  candidate set.
- **AC-9.3**: G56R-005 simulates preferred model absent, effort unsupported,
  model hidden, discovery unavailable, exact-invocation availability-probe
  success/failure,
  treatment-probe failure, approved/unapproved service reroute, no safe required
  route, helper unavailable, atomic no-write, previous-install preservation,
  strict override failure, rollback, and retry exhaustion.
- **AC-9.4**: G56R-004 freezes the dominance contract, and G56R-011 applies it
  to the final assembled core. If an eligible frozen control materially
  dominates, static defaults may still ship for declared operational simplicity,
  but release language cannot call them efficient, optimal, or best measured.
- **AC-9.5 — Fallback and recovery semantics**: The resolver deterministically
  evaluates the preferred route then each ordered fallback. Eligibility
  requires admission by the official-source ledger, discovered runtime
  availability or a successful bounded availability probe, a documented and
  runtime-supported effort, complete hard-contract qualification, and
  successful exact-treatment materialization. Preferred-model absence,
  effort-unsupported, discovery-unavailable, treatment-probe-failed, and other
  outcomes have stable reason codes. The resolver records every attempted
  route, limits retries, prevents fallback loops, and never accepts an
  unqualified route. If a required agent has no safe route, installation makes
  no partial write, preserves the previous known-good installation, and emits
  actionable recovery. If no helper route resolves, it uses the validated no-
  helper path. It never changes unrelated Codex configuration.

## 4. Migration Path (one phase per SPEC)

- **Phase 1 (G56R-001) - Candidate and role-contract research**: Establish
  official platform facts, twelve-agent role contracts, provisional candidate
  routes, fallback requirements, and fixture/telemetry needs without waiting on
  G56R-002 or changing defaults.
- **Phase 2 (G56R-002 through G56R-005) - Evaluation foundation**: Freeze
  capability discovery, telemetry profile, exact treatment, shared materializer,
  runner, fixtures, statistical analysis, controls, budgets, and fallback/
  recovery simulation.
- **Phase 3 (G56R-006) - Resolver and installer framework**: Implement the
  capability-aware resolver, canonical materializer, atomic installer, strict
  override, and fixture route policies. Do not create final route aggregates.
- **Phase 4 (G56R-007 through G56R-010) - Agent route policies**: Select
  preferred and ordered fallback routes for the three required-agent cohorts
  and optional helper after the shared framework is stable.
- **Phase 5 (G56R-011) - Final composition and release proof**: Create final
  core/helper/release identities, rebuild payloads, reconcile installed
  evidence, run skill-driven UAT and fallback proof, compare frozen controls,
  and publish only proven claims.

## 5. Constraints

- Codex-only scope: Codex agent definitions and skills, the active Python
  runner/install path, Codex payloads, and directly related tests/evals/docs.
- Cross-platform parity: the named-agent catalog remains identical across the
  Codex and Claude plugins; catalog changes land on both platforms or record an
  explicit platform-specific exception. The Claude half of the shared
  twelve-agent catalog is owned by the companion Claude routing PRD.
- G56R-006 implements the currently deferred Python Codex-agent installer; no
  deleted Bash helper may be restored or described as active.
- Python 3.11+ standard library remains the installed runtime substrate; this
  PRD adds no runtime dependency.
- A documented custom-agent file can set one model and one reasoning effort;
  ordered fallback remains SpecKit Pro policy outside the native agent schema.
- Source agent definitions and final route-policy manifests are plugin-owned
  implementation sources of truth, not Codex platform evidence. Official
  OpenAI documentation remains the sole platform authority; capability
  snapshots and execution traces prove only the environment and observed
  runtime.
- Destination agent policies always materialize explicit model and effort.
- A model and effort must first be admitted by the official-source ledger, then
  be discovered or pass the pinned availability probe and exact-treatment
  contract before becoming a preferred or fallback route.
- No silent model fallback, generic-agent substitution, partial required-agent
  install, or unreported change to sandbox/mutation/tool boundaries is allowed.
- Live AI evaluation remains developer-local, controlled, and budgeted;
  deterministic replay and structural checks remain the default CI path.
- Release-please owns version changes; implementation does not manually bump
  plugin versions.
- Every implementation slice follows repository reviewability limits and runs
  only the relevant Python-authoritative validation.

## 6. Open Questions

- **OQ-1 (G56R-001/G56R-002):** Which current model IDs and efforts are exposed
  by each supported Codex client/surface? Recommendation: admit source-bound
  model candidates and effort-surface concepts only from official
  documentation, then use documented discovery to expand those model candidates
  into supported executable model/effort tuples and narrow runtime availability.
  A bounded invocation probe may verify availability only when discovery is
  unavailable.
- **OQ-2 (G56R-002):** Which app-server model and provider capability fields are
  stable enough for installer preflight? Recommendation: version the raw
  capability snapshot and classify each field through the telemetry profile.
- **OQ-3 (G56R-002):** Which surface supplies authoritative effective-model and
  effective-effort evidence for every run? Recommendation: require an official
  field-level citation for each claim and preserve nulls otherwise. Do not infer
  returned effort or treat `codex exec --json` lifecycle output as proof of a
  field it does not document.
- **OQ-4 (G56R-002/G56R-003):** How reliably does the tested surface expose
  the documented app-server `model/rerouted` event? Recommendation: bind the
  claim to the officially documented app-server surface and pinned client,
  classify missing observations as unknown rather than proof that no reroute
  occurred, and apply AC-2.3 and AC-2.19.
- **OQ-5 (G56R-007 through G56R-010):** Which catalog challengers and effort
  boundaries survive capability, contract, and long-workflow qualification?
  Recommendation: let evidence determine each named agent's order rather than
  forcing one model across a cohort.
- **OQ-6 (G56R-006):** Which Codex integration point gives the installer the
  required model/capability snapshot? Recommendation: use the documented
  discovery surface when available. A bounded probe may check availability of
  an officially documented candidate but cannot supply missing platform facts;
  unresolved capability produces no write.
- **OQ-7 (G56R-010):** Does the current helper candidate expose a stable,
  comparable resource measure and exact effort configuration? Recommendation:
  qualify only what the telemetry profile proves and preserve the no-helper path
  for every unresolved case.
- **OQ-8 (G56R-001/G56R-009):** Which Codex custom-agent capabilities are
  required to express the Claude orchestration-support contracts (consensus
  synthesis and gate validation)? Recommendation: derive the role contracts
  from the Claude agent definitions, author per current official custom-agent
  documentation, and record any platform-specific divergence explicitly.

## 7. SPEC Catalog Crosswalk

| Feature (§3) | Acceptance Criteria | SPEC | Depends on | Priority |
|---|---|---|---|---|
| Candidate Route Baseline and Role Contracts | AC-1.* | G56R-001 | - | P1 |
| Capability Discovery and Telemetry Profile | AC-2.2 through AC-2.5 | G56R-002 | G56R-001 | P1 |
| Evaluation Runner, Fixtures, Scoring, and Statistical Analysis | AC-2.1, AC-2.6 through AC-2.16, AC-2.20 | G56R-003 | G56R-002 | P1 |
| Exact Treatment and Service-reroute Handling | AC-2.19 | G56R-002, G56R-003, G56R-006, G56R-011 | G56R-001 | P1 |
| Preferred and Fallback Route Qualification | AC-2.21 | G56R-003, G56R-007 through G56R-011 | G56R-002 | P1 |
| Policy Controls and Adaptive Comparators | AC-2.17, AC-9.2, AC-9.4 | G56R-004, G56R-011 | G56R-003 | P1 |
| Model Availability, Fallback, and Recovery Simulation | AC-9.1, AC-9.3 | G56R-005 | G56R-004 | P1 |
| Production Fallback and Recovery Semantics | AC-9.5 | G56R-005, G56R-006, G56R-011 | G56R-004 | P1 |
| Capability-aware Resolver, Materializer, Installer, and Strict Override | AC-3.* | G56R-006, G56R-011 | G56R-005 | P1 |
| Quality-critical Executor Routing | AC-4.* | G56R-007, G56R-011 | G56R-006 | P1 |
| Structured-work Agent Routing | AC-5.* | G56R-008, G56R-011 | G56R-006 | P1 |
| Read-only Reasoning and Orchestration-support Agent Routing | AC-6.* | G56R-009, G56R-011 | G56R-006 | P1 |
| Optional Helper Routing and No-helper Path | AC-2.18, AC-7.* | G56R-006, G56R-010, G56R-011 | G56R-005 | P1 |
| Payload, Installed Skill UAT, Fallback Proof, and Release Integration | AC-8.* | G56R-011 | G56R-007 through G56R-010 | P1 |

## 8. Success Criteria

1. All acceptance criteria map once through the acyclic G56R-001 through
   G56R-011 catalog; G56R-001 does not wait on G56R-002, G56R-006 creates only
   framework/fixture policies, and G56R-011 creates final aggregates.
2. Every one of the eleven required named agents has one qualified preferred
   route and zero or more ordered qualified fallbacks. Every fallback preserves
   the same agent contract and changes only explicit model/effort route fields.
3. The optional helper has one qualified preferred route when available,
   approved helper fallbacks when supported, and a validated no-helper path.
4. The resolver considers only candidates admitted by the official-source
   ledger, uses a versioned capability snapshot, materializes explicit model and
   effort values, reports every fallback, bounds availability probes/retries,
   and distinguishes service rerouting from plugin fallback.
5. A complete required-agent matrix resolves before one atomic install. Any
   unresolved required agent causes no partial write and preserves the previous
   known-good installation; strict override failure has the same atomicity.
6. The assembled preferred core passes integrated contract, quality,
   reliability, environment-independent resource-superiority, simultaneous
   guardrail, and powered long-horizon gates against the immutable production
   core. Release wording obeys the frozen control-dominance result and does not
   claim global optimality.
7. Installed skill-driven UAT collectively proves named-agent spawn, resolved
   route, exact treatment, returned result, and downstream consumption for every
   required agent, plus the optional helper and no-helper paths. Direct harness
   injection, generic substitution, or unused results do not satisfy release.
8. Source, generated payload, installer output, installed cache, active
   guidance, replay evidence, UAT, rollback, and final identities agree.
   Platform claims require current official OpenAI documentation;
   qualification claims require the pinned client/surface and evaluation
   evidence.

## 9. References

- **Technical roadmap:** [codex-gpt-5-6-agent-routing-technical-roadmap.md](ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md)
- **Roadmap MOC:** [codex-gpt-5-6-agent-routing-roadmap-MOC.md](ai/specs/codex-gpt-5-6-agent-routing-roadmap-MOC.md)
- **Shared parity contract:** [agent-routing-parity-contract.md](ai/specs/agent-routing-parity-contract.md)
- **Shared manifest schema:** [agent-route-candidate-manifest.schema.json](ai/research/agent-route-candidate-manifest.schema.json)
- **Constitution:** [Racecraft Plugins Public Constitution](../.specify/memory/constitution.md)
- **Project standards:** [AGENTS.md](../AGENTS.md) and [CLAUDE.md](../CLAUDE.md)
- **Official documentation discovery:** [Codex manual](https://developers.openai.com/codex/codex-manual.md)
- **Codex custom agents and subagents:** [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- **Codex model discovery, provider capabilities, token usage, and conditional reroute events:** [App server](https://learn.chatgpt.com/docs/app-server)
- **Codex model and reasoning guidance:** [Models](https://learn.chatgpt.com/docs/models)
- **Codex configuration fields and inheritance:** [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
- **Codex non-interactive JSONL lifecycle, item, and error events:** [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
- **Current model-selection and prompting guidance:** [Latest model](https://developers.openai.com/api/docs/guides/latest-model)
- **Cross-platform parity source (Claude agent definitions):**
  `speckit-pro/agents/consensus-synthesizer.md` and
  `speckit-pro/agents/gate-validator.md`
