# PRD: Claude Code Agent Model Routing and Graceful Fallback

**Status**: Active - CAR-001 through CAR-005 complete/archived; current-source
roster rebaseline complete; CAR-006 ready
**Source**: Maintainer request plus current official Anthropic documentation
retrieved 2026-08-30 under the evidence-authority contract below
**Created**: 2026-07-12
**Last updated**: 2026-08-30
**Target window**: Next SpecKit Pro minor release after the evaluation and
route-policy specifications in this roadmap are implemented
**Parity note**: This PRD now targets 14 required shipped Claude agents plus
the optional helper. Shared roles mirror the companion Codex routing PRD;
Claude-only secure feedback-sweep roles are an explicit platform-specific
exception. The frozen CAR-003 v1 11+helper corpus remains historical evidence;
the current-source successor roster is recorded in
[`claude-subagent-runtime-rebaseline.md`](ai/research/claude-subagent-runtime-rebaseline.md).

---

## Evidence Authority

- The shared
  [agent-routing parity contract](ai/specs/agent-routing-parity-contract.md)
  governs structure, evidence classes, source records, historical integrity,
  and fail-closed behavior for CAR and G56R.
- Official Anthropic documentation under `code.claude.com/docs/**` and
  `platform.claude.com/docs/**` is the sole authority for Claude Code and
  Claude platform facts, including model IDs and positioning, supported
  configuration fields, effort controls, telemetry fields, lifecycle, and
  client-surface behavior.
- Repository files, generated payloads, installed caches, and Codex agent
  definitions are project inputs used to inventory the current implementation
  and define SpecKit Pro role contracts. They cannot establish an Anthropic
  model, capability, configuration field, telemetry field, or native behavior.
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
- The official-source ledger is versioned and revalidated before each CAR
  scaffold that consumes it and again before release. A changed, conflicting,
  inaccessible, or withdrawn source invalidates bound candidates and claims.

---

## 1. Problem

> Which evidence-backed preferred model and reasoning-effort route, with which
> ordered qualified fallbacks, should SpecKit Pro ship for each named Claude
> Code agent so that the agent remains usable when its preferred route is
> unavailable without silently changing its role, tools, safety boundary, or
> output contract?

SpecKit Pro currently defines 14 required Claude Code agents: three
quality-critical executors, three structured-work roles, four read-only
reasoning roles, two orchestration-support roles, and two broker-confined
untrusted-feedback roles. Every shipped agent has explicit model, effort, and
turn limits. This plan therefore targets a 15-role Claude catalog: the 14
required shipped agents plus optional `autopilot-fast-helper`.

The existing definitions pin one floating model alias each, but they do not
express an evidence-backed ordered fallback policy, and no committed Claude
benchmark evidence supports any pin: the Layer 6 results directory is
git-ignored, only two role fixtures exist, and the model catalog has shifted
under the pins (Fable 5, Opus 4.8, Sonnet 5, Haiku 4.5) without any probe. A
model can be absent from an account, an effort can be unsupported, or an alias
can re-point across model releases - today nothing detects, reports, or safely
falls back from any of those changes.

Current Anthropic documentation establishes these platform facts:

- Each subagent Markdown file describes one named agent and may set one
  `model` (alias, full model ID, or `inherit`; omitted values inherit) and one
  `effort` (`low` through `max`; omitted values inherit the session; `high` is
  the documented default posture).
- Subagent model resolution follows a documented precedence: the
  `CLAUDE_CODE_SUBAGENT_MODEL` environment variable, then a per-invocation
  model parameter, then frontmatter, then the session model. Plugin-loaded
  agents ignore `hooks`, `mcpServers`, and `permissionMode` frontmatter.
- Non-interactive runs (`claude -p --output-format json`) document usage and a
  per-model `modelUsage` breakdown keyed by full model ID, including billed
  cache-write and cache-read token categories, and transcripts record a
  per-message model. No surface returns an authoritative effective reasoning
  effort.
- No documented command lists the account's available model catalog; the API
  models endpoint requires API-key authentication. Availability is otherwise
  provable only by a bounded exact invocation probe.
- Fast mode is an Opus-only, usage-credit-billed research preview and changes
  output-speed economics.
- Model aliases float across model releases: an alias can re-point to a newer
  model without any plugin action.
- Skills and plugin instructions can direct named subagent delegation; bundled
  agents dispatch as `speckit-pro:<name>`.

The following are proposed SpecKit Pro policies, not claims about native
Claude Code behavior:

- one preferred route and an ordered list of independently qualified fallback
  routes for each named agent;
- capability probing and bounded exact invocation probes;
- one canonical materializer and frontmatter drift gate shared by evaluation
  and the shipped payload;
- session preflight that resolves the complete matrix and reports every
  resolution;
- strict validation and disclosure for the global subagent-model override; and
- route-resolution, exact-treatment, and release identities.

A route is more than a model name. It includes an explicit model and explicit
reasoning effort plus the instruction hash, required model and modality
capabilities, tool and skill contract, mutation contract, supported client
range, and qualification evidence. A fallback may change only the approved
model/effort route for the same named agent. It cannot substitute a different
named agent, a generic agent, or a weaker safety or tool contract.

No complete public benchmark compares every supported Claude model and effort
on SpecKit Pro's 15 target roles. Model branding, generation, or placement in
product guidance therefore does not prove a route. The PRD uses controlled
evaluation to qualify preferred and fallback routes, then resolves dispatch
against a versioned capability snapshot from the user's working Claude Code
environment.

The evaluation boundary is the accepted end-to-end workflow, not an isolated
agent response. It includes parent and child work, retries, validation,
repairs, compaction, cancellations, and abandoned branches. Long-horizon work
is a powered comparative stratum in the release decision and also has separate
recovery canaries. Resource evidence remains environment-independent: raw
token vectors (input, cache writes by TTL class, cache reads, output),
duration, retries, compaction, and accepted-workflow rate.

## 2. Goals, Product Contract, and Non-goals

### 2.1 Goals

- Give every required named agent one evidence-backed preferred route and zero
  or more ordered, independently qualified fallback routes.
- Give the optional helper a preferred route, qualified helper fallbacks, and a
  validated no-helper path.
- Maintain parity for shared Claude/Codex roles while recording explicit
  platform-specific exceptions; this plan covers all 14 shipped Claude roles
  plus the optional `autopilot-fast-helper`.
- Preserve role-specific correctness, grounding, safety, mutation, output,
  tool, and orchestration contracts across every route.
- Select preferred routes quality and reliability first, then use one
  predeclared environment-independent resource/latency rule among passing
  candidates.
- Ship explicit model and reasoning-effort values in every shipped agent
  policy; never rely on an unmeasured inherited default. Shipped frontmatter
  carries floating aliases for consumer resilience while the route-policy
  manifest and capability snapshots pin the exact model IDs each alias
  resolved to during qualification.
- Resolve the complete required-agent matrix during session preflight, and
  report the preferred route, effective route, fallback index, and resolution
  reason for every named agent without ever mutating shipped agent files.
- Keep the global subagent-model override honest: the preflight validates the
  override tuple against qualified routes and loudly reports a non-qualified
  route; release claims exclude overridden environments.
- Use the same materializer and exact-treatment predicate in evaluation and in
  the shipped-payload drift gate.
- Include bounded prompt and context tuning when it targets measured overhead,
  while retaining an unchanged-prompt attribution stage.
- Compare the selected static policy with frozen unpinned and adaptive
  controls before describing the static result as efficient.
- Make installed Claude skills explicitly spawn the required agents by name
  (`speckit-pro:<name>`) and prove that their returned work affects a
  downstream decision, artifact, or validation result.
- Rebuild and reconcile the Claude payload, active guidance, installed-cache
  evidence, fallback UAT, and rollback evidence before release.

### 2.2 Non-goals (out of scope)

- Detecting or classifying commercial subscription plans, entitlements,
  workspaces, billing, credits, allowances, quotas, or rate limits. None of
  those may determine route selection, fallback order, evaluation, UAT, or
  release eligibility. Statusline rate-limit data and usage displays remain
  diagnostic environment evidence only.
- Changing Codex agent definitions, Codex skills, or Codex marketplace
  behavior. Shared-role parity remains companion work; Claude-only sweep roles
  do not expand this PRD into Codex changes.
- Claiming that ordered model fallback, strict override enforcement, or
  availability preflight is a native subagent-frontmatter feature. SpecKit Pro
  owns the ordered route policy, preflight resolver, and materializer.
- Adopting fast mode, orchestration-changing execution modes, or Agent SDK
  features beyond the pinned harness usage. **Fast mode is never enabled by
  SpecKit Pro, on any surface, under any qualification outcome.** It is
  Opus-only and usage-credit-billed, so enabling it on an operator's behalf
  spends their credits for a speed characteristic they did not ask for. It is
  used only when the operator turns it on themselves. The converse also binds:
  no SpecKit Pro surface may turn fast mode *off* on an operator who has
  enabled it. The plugin neither grants nor revokes this setting — it observes
  the state and, for a scored run, refuses rather than mutates. No result from
  CAR-004's policy-control evaluation or CAR-011's comparison may be read as
  authority to adopt it: a control that measures well is still not adopted.
- Unbounded or aesthetic prompt rewriting. Prompt changes must target measured
  instruction, handoff, tool-schema, duplicated-context, cache-write, or
  compaction overhead and be tested against an unchanged-prompt control.
- Offering quality/balanced/economy profiles or arbitrary per-agent user
  overrides in v1. The documented global subagent-model override remains the
  compatibility escape hatch and is validated, not silently accepted.
- Searching the complete fourteen-agent combination space or claiming global
  assembled-policy optimality. Version 1 performs component-wise route and
  prompt selection, then confirms the assembled preferred core.
- Automatically selecting an unqualified adjacent model, changing a named
  agent, or weakening its prompt, tools, skills, mutation, or output contract
  during fallback.
- Building production checkpoint/resume or external-limit-aware scheduling.
  Evaluation budgets and failure simulations do not create a new workflow
  scheduler.
- Rewriting historical model references or archived evidence solely to make
  repository-wide searches uniform.

### 2.3 Route and Identity Lifecycle

One route is the following complete, qualified tuple:

```text
route = explicit model (shipped alias + qualified resolved model ID)
      + explicit effort
      + instruction/prompt hash
      + required model and modality capabilities
      + required tool/skill contract
      + mutation contract (disallowedTools, tools omission, maxTurns)
      + supported client range
      + qualification evidence
```

The identity lifecycle is intentionally staged so early experiments do not
depend on final aggregates that do not yet exist.

| Identity | Created by | Required contents |
|---|---|---|
| `agent_contract_id` | CAR-001 | Named role plus safety, grounding, mutation, tool, and output contract |
| `candidate_route_id` | CAR-001/CAR-002 | Candidate model/effort tuple, contract and instruction hashes, required capabilities, rationale, and invalidation rules |
| `telemetry_profile_id` | CAR-002 | Pinned client and mandatory, conditional, derived, and unavailable telemetry fields |
| `runtime_capability_snapshot_id` | CAR-002 or session preflight | Client version, probed model IDs, alias-to-ID bindings, supported efforts, retrieval/probe method, timestamp, and raw evidence |
| `experiment_policy_id` | CAR-003 | Corpus and partitions, scorer, analysis plan, budgets, terminal policy, and treatment controls |
| `execution_trace_id` | CAR-003 | Assigned route, effective-route evidence, task outcome, raw resource evidence, retries, terminal state, and treatment integrity |
| `agent_route_policy_id` | CAR-007 through CAR-010 | Named agent, preferred route, ordered fallbacks, hard contract, evidence, client bounds, and invalidation rules |
| `route_resolution_id` | CAR-002 schema; CAR-003/CAR-006 records | Preferred and effective routes, fallback index and reason, attempted routes, capability snapshot, and timestamp |
| `resolved_agent_policy_id` | CAR-006 schema/fixtures; CAR-011 final records | Exact shipped frontmatter-plus-body content hash and selected effective route for one named agent |
| `core_routing_policy_id` | CAR-011 | Ordered mapping of the fourteen required named agents to final route policies |
| `optional_helper_policy_id` | CAR-011 | Helper preferred route, qualified fallbacks, no-helper contract, and integration reference |
| `resolved_installation_id` | CAR-011 | dist/claude payload tree hash plus installed-cache proof binding shipped agents to resolved policies |
| `release_policy_id` | CAR-011 | Final core, helper state, preflight/materializer version, evidence lock, UAT, invalidation rules, and bounded claims |

`core_routing_policy_id`, `optional_helper_policy_id`, and `release_policy_id`
are attached to evidence only after CAR-007 through CAR-010 finish route
selection and CAR-011 composes the aggregates. Because Claude plugin agents
auto-load from the shipped payload, the shipped file is the materialized
policy: source and destination collapse, installation atomicity is plugin
release atomicity, and the previous known-good installation is the previous
plugin release.

## 3. Acceptance Criteria

### 3.1 Candidate Route Baseline and Role Contracts *(-> CAR-001)*

AC-1.1 through AC-1.7 describe the immutable CAR-001/CAR-003 v1 evidence set.
They are historical requirements, not the current source count.

- **AC-1.1**: A dated research record inventories all twelve named target
  agents (the eleven current Claude agents plus the net-new
  `autopilot-fast-helper` whose contract derives from the Codex helper under
  the parity principle) and every active source, skill, validation,
  evaluation, generated-payload, and installed-cache surface that encodes or
  consumes their route policy. The inventory is labeled `project_input` and
  cannot establish Anthropic platform facts or candidate eligibility.
- **AC-1.2 - Official-source ledger**: The record cites only current official
  Anthropic documentation for every shared research-matrix family: model IDs,
  aliases and lifecycle, subagent and plugin fields, effort controls, skills,
  tools, permissions, hooks, noninteractive output, telemetry, authentication,
  availability, fast mode, pricing, cost, and analytics. Every platform claim
  records its source-ledger ID, canonical URL, retrieval timestamp, supported
  surface, exact fact, bounded extract and hash, claim binding, gap, and
  invalidation trigger. Conflicting or absent claims are blocked or marked
  `undocumented`.
- **AC-1.3**: Every agent has an immutable production route (recorded as
  absent for the net-new helper), a role-specific contract, candidate
  routes admitted only by the official-source ledger, prompt/context candidates
  when justified, and a fixture backlog. CAR-001 records model/effort tuples as
  non-executable until the documented alias, model-specific effort support,
  environment availability, and exact treatment are verified. Runtime probes
  may narrow availability but cannot introduce a model or effort outside the
  official ledger. A route is excluded only for recorded incompatibility,
  contract failure, or predeclared dominance evidence.
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
  capability questions, and a go/no-go handoff to CAR-002. It does not depend
  on CAR-002 results, change shipped defaults, or claim that a candidate is
  executable before capability probing.
- **AC-1.6 — Candidate route and fallback manifest**: Before scored screening,
  CAR-001 publishes a Schema `2.0.0` `agent_route_candidate_manifest` covering
  all twelve named agents under the same top-level and record-level contract as
  G56R-001. It records the immutable comparator, source ledger, effort
  surfaces, project inputs, role contracts, source-bound candidates, fixtures,
  telemetry, capability questions, traceability, decisions, historical fact
  dispositions, and invalidation rules. Platform differences remain values,
  explicit statuses, nulls, or empty arrays rather than platform-only schema
  fields. CAR-002 later binds the manifest to a versioned runtime capability
  snapshot and freezes the executable candidate set before CAR-003 scores
  outcomes.
- **AC-1.7 — Current harness baseline**: The research record labels the
  current Layer 6 Claude path - a frontmatter-stripped agent body piped to
  `claude -p --model` - as bare prompt emulation and labels all historical
  results `non_release_evidence` until CAR-003 replays them through the shared
  materializer with exact treatment and the required tool surface, mutation
  contract, dispatch context, and telemetry proof.
- **AC-1.8 — Current-source successor roster**: Before CAR-006, publish a
  separately versioned roster that binds all 14 shipped agent source digests,
  cohorts, trust boundaries, and memory scopes plus the optional helper. It
  references the historical corpus by ID/digest without changing it. Add
  `artifact-author` to structured work and put `sweep-classifier` and
  `sweep-analyst` in a broker-only untrusted-feedback cohort.

### 3.2 Route Evaluation and Qualification *(-> CAR-002 through CAR-004)*

- **AC-2.1 — Controlled model-effort pair selection**: Stage A1 screens each
  eligible model at its documented default ordinary effort (`high`) after
  exact treatment is proven. Stage A2 holds the model and all non-effort
  variables fixed, ascends when necessary to find a pass, then descends
  through every supported lower ordinary effort and retests the failing
  boundary to select the lowest stable ordinary effort. Stage A3 compares
  frozen passing model-effort pairs with every non-candidate variable frozen.
  Stage B admits only A3-shortlisted pairs and evaluates predeclared
  prompt-by-pair interactions. Stage C freezes the complete cohort policy and
  evaluates it once on its disjoint cohort-lock partition. Stage A selects
  model-effort pairs; it does not claim independent model and effort effects.
  The current uniform `effort: max` pins are the comparator, not the search
  origin.
- **AC-2.2 — Capability probing and controlled environment**: The harness
  binds every run to a pinned Claude Code client version range, candidate
  route, controlled repository/task environment, and versioned
  `runtime_capability_snapshot_id`. The snapshot records probed model IDs,
  alias-to-ID bindings, supported efforts, client version, retrieval/probe
  method (bounded exact invocation probe, or the API models endpoint under
  API-key authentication), timestamp, and raw evidence. Unresolved
  availability blocks that route's scored run.
- **AC-2.3 — Route-resolution and execution trace**: Every assigned objective
  binds `candidate_route_id`, `agent_contract_id`,
  `runtime_capability_snapshot_id`, `route_resolution_id`,
  `experiment_policy_id`, and `execution_trace_id`. The trace records
  requested and effective model when the telemetry profile supports those
  claims, configured effort, fallback index and reason, platform-initiated
  route-change events, instruction hash, effective tool surface and mutation
  contract, parent-child graph, raw token categories including cache writes by
  TTL class and cache reads, wall time, retries, compaction, validation,
  cancellation, terminal state, and outcome. Nulls are preserved. Final
  core/helper/release aggregate IDs are attached only after those aggregates
  exist. A platform-initiated route change - an observed model ID that differs
  from the resolved qualified ID, including alias re-pointing - is always
  recorded separately from SpecKit Pro route resolution and never reported as
  plugin fallback. Any platform-initiated route change makes the run
  non-scorable as qualification evidence for the requested route.
- **AC-2.4 — Telemetry capability profile**: CAR-002 publishes a versioned
  telemetry capability profile for the pinned client. Qualification requires
  complete evidence only for fields classified as mandatory by that profile:
  successful treatment assignment, effective model or an approved proof of
  configured route with no unapproved route change, task outcome, duration,
  and the raw token fields needed by the declared endpoint. Effective
  reasoning effort is never returned by the platform and is classified as
  derived from controlled configuration; it cannot support claims that require
  a returned value. Conditional or unavailable fields remain null. Telemetry
  failure classification, bounded complete-pair reruns, attrition reporting,
  and no arm-only discretionary reruns are predeclared.
- **AC-2.5 — Environment-independent resource evidence**: The primary resource
  evidence is the complete objective-level raw token vector - input,
  cache-write by TTL class, cache-read, and output tokens - plus request/turn
  count, wall time, retries, compaction, and failed or abandoned work through
  the terminal policy. The selection rule among passing candidates is one
  predeclared environment-independent Pareto rule over that complete raw
  vector, applied only after absolute quality and reliability floors and
  task-paired cluster-adjusted non-inferiority have passed. A failed gate, a
  tie, mixed dominance, incomplete evidence, or statistical uncertainty is
  inconclusive and yields no qualification; no weighted ranking may be forced.
  The complete raw vector is always reported. Published price data may be cited
  as diagnostic context only, never as a selection coefficient and never as
  plan accounting.
  **Amendment 2026-07-24 (CAR-003):** this criterion previously mandated one
  predeclared weighted scalar whose per-category coefficients were pinned from
  a dated revision of the published Anthropic API price sheet, content-addressed
  at lock time and labeled diagnostic-derived. It is amended to the Pareto rule
  above to hold logical parity with the Codex routing program, whose PRD permits
  "one predeclared environment-independent score or Pareto rule" and whose
  G56R-003 specification selected Pareto dominance and forbids a forced weighted
  ranking. The raw-vector reporting obligation is unchanged; only the rule that
  ranks passing candidates changed.
- **AC-2.6 — Per-agent attribution**: Paired per-agent experiments freeze the
  parent session model and effort, every non-candidate agent route, all
  prompts other than the allowed Stage B candidate prompt, tools, skills,
  mutation contracts, repository snapshot, context/compaction policy,
  retry/escalation policy, validation, and acceptance checker. Unpinned and
  adaptive runs are policy-level controls and are not evidence attributable to
  one agent.
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
  handling, minimum unique tasks, and cache-state isolation between arms -
  cache isolation matters doubly here because cache writes are billed token
  events. Strata and weights cannot be selected from candidate outcomes.
- **AC-2.9 — Long-horizon comparative evidence**: The workload manifest
  defines long-horizon membership from task and protocol characteristics
  before either arm runs, never from realized duration, turns, tokens,
  retries, or compactions. Integrated confirmation contains a powered
  long-horizon stratum that independently clears accepted-workflow,
  semantic-quality, raw-resource, p95-resource, p95-duration, late-failure,
  retry, and compaction guardrails. A long-horizon efficiency claim
  additionally requires its predeclared superiority endpoint; recovery
  canaries cannot substitute for this evidence.
- **AC-2.10 — Prompt interaction stage**: Model/effort attribution uses the
  unchanged baseline prompt. Only Stage A-shortlisted pairs enter
  prompt/context interaction evaluation, where only the candidate agent's
  bounded prompt may vary. After one final instruction hash is selected, every
  preferred and fallback route is requalified under that same instruction
  hash. The selected model, effort, prompt, and fallback order are then frozen
  as one route policy for cohort lock and integrated confirmation.
- **AC-2.11 — Search and campaign bounds**: For every model, capability
  probing produces an ordered supported-effort set from `low` through `max`.
  The predeclared rule starts at the documented default, ascends to the first
  stable pass when necessary, then descends and boundary-retests to find the
  lowest stable ordinary effort. Fast mode or any mode that changes
  orchestration topology is a policy-level control, not an ordinary per-agent
  effort. Campaign raw-token use, wall time, candidate count, futility rules,
  racing method, and confirmation-entry cap are frozen before outcome-bearing
  runs.
- **AC-2.12 — Evidence partitions and multiplicity**: Screening, selection,
  cohort lock, and integrated release confirmation use disjoint objective
  sets. The final confirmation set is used exactly once after candidates,
  prompts, margins, endpoints, guardrails, stopping rules, and multiplicity
  strategy are locked. Changing any locked decision invalidates affected
  evidence.
- **AC-2.13 — Immutable production comparator**: Before screening, the
  immutable CAR-003 v1 production comparator is pinned by repository revision,
  plugin version, its eleven frontmatter route tuples with their resolved
  model IDs, each agent's instruction hash and mutation contract, client
  version, corpus snapshot, and analysis plan. Candidate routes compare with
  the corresponding production role route; integrated release compares the
  final assembled preferred core with the immutable production core. The
  net-new helper has no production route and qualifies against its absolute
  contract, quality, and reliability floors outside the required-core primary
  statistic. The immutable production comparator remains the sole release
  baseline. The current-source v2 successor separately binds all 14 shipped
  source policies; newly added roles use their bound shipped policy as the
  comparator when their cohort is evaluated, without rewriting v1 evidence.
- **AC-2.14 — Missing telemetry and attrition**: Every attempt records missing
  fields, cause classification, evidence, rerun eligibility/count, and final
  disposition. Only independently proven transient harness failures can
  receive a capped full-pair rerun under the original assignment.
  Candidate-inherent, environment-inherent, recurrent, unknown, or
  arm-differential telemetry loss fails qualification or blocks the affected
  claim. No primary conclusion may use an unexplained complete-case subset.
- **AC-2.15 — Guardrail registry**: Before outcome-bearing evaluation, every
  mandatory safety, quality, grounding, mutation, accepted-workflow, p95
  resource/duration, late-failure, retry, steering, and compaction guardrail
  has a definition, unit, denominator, comparator, margin, confidence method,
  missing-data rule, multiplicity position, and minimum unique-task count.
  Human steering is prohibited or follows one frozen scripted intervention
  policy.
- **AC-2.16 — Analysis plan and decision rule**: A versioned analysis plan
  predeclares the primary endpoint, practical margin, one-sided confidence
  rule, alpha/multiplicity strategy, target power, variance and clustering
  assumptions, sample sizes, racing adjustment, attrition thresholds, terminal
  policy, and `inconclusive => no qualification`. Numeric thresholds live in
  this plan or a content-addressed registry, not in post-hoc review judgment.
- **AC-2.17 — Policy controls and dominance**: CAR-004 defines and freezes
  three controls - unpinned (agents with `model` omitted or `inherit`, riding
  the session model), adaptive (a frozen escalation/de-escalation policy over
  qualified routes exercised through the documented dispatch-time model
  parameter), and orchestration-changing (a parallel multi-agent execution
  mode) - with their execution contracts, parameters, eligibility floors,
  dominance metrics, margins, multiplicity, and untouched comparison
  partition. CAR-011 later compares the final frozen core with those controls.
  A control materially dominates only when it passes every mandatory contract,
  safety, quality, reliability, and availability gate and clears the
  predeclared resource/duration dominance rule.
- **AC-2.18 — Optional helper availability contract**:
  `autopilot-fast-helper` is optional and excluded from the required-core
  primary statistic. CAR-010 selects a preferred helper route, zero or more
  independently qualified helper fallback routes, and a validated no-helper
  path. Because Claude plugin agents ship unconditionally, the helper's
  optional status is an invocation contract, not an installation state:
  autopilot consults it only when the preflight resolves a qualified helper
  route, and continues through the no-helper contract otherwise. Helper
  availability is established through capability evidence, never through a
  product label or plan assumption.
- **AC-2.19 — Exact treatment and fallback resolution**: Every scored run
  executes the installed plugin agent through real dispatch
  (`speckit-pro:<name>`), or a configuration produced by the same canonical
  materializer that gates the shipped payload, proven semantically equivalent.
  Equivalence requires equality of the predeclared route, instructions,
  mutation contract, tool surface, skill availability, relevant parent-session
  configuration, client version, and controlled runtime overrides. The
  environment contract freezes fast mode off, a pinned client version range, a
  pinned parent-session model and effort, and proof that
  `CLAUDE_CODE_SUBAGENT_MODEL` is unset; scored campaigns run under
  subscription authentication, no supported path requires API-key
  authentication, and the authentication mode of every run is recorded in the
  environment snapshot without producing any plan-based claim.
  **Amendment 2026-07-26 (CAR-003):** this criterion previously required scored
  campaigns to run under a dedicated API-key-authenticated environment with at
  least one installed-UAT smoke row under subscription authentication. That
  inverted the product's actual delivery model: SpecKit Pro ships to operators
  running Claude Code under a subscription, so evidence gathered only under an
  authentication mode most operators never use would not describe the routes
  they actually get. Requiring an API key on the scored path would also make
  qualification depend on a credential the product does not require. It is
  amended to make subscription the supported scored path and to forbid any
  supported path requiring API-key authentication. CAR-003 FR-042 implements
  this and additionally makes the recorded mode *constraining* — the observed
  mode is compared against the mode pinned in the run's FR-051 environment
  contract and a divergence blocks scoring, so the field is not merely
  observable. The recording-without-plan-claims obligation is unchanged; only
  which mode the scored path uses changed. Note the knock-on already relied
  upon elsewhere: FR-004 refuses to let the models catalog endpoint *admit* a
  tuple precisely because that endpoint yields evidence only under API-key
  authentication, which this amendment forbids requiring.
  Preferred-route unavailability invokes the resolver
  before assignment. A scored run begins only after one approved route is
  resolved and exact treatment is proven. Runtime UAT may continue after a
  platform-initiated route change only when the observed model is itself a
  qualified route for the same named agent; the event remains platform
  behavior, never resolver success. An unapproved or unidentifiable route
  change is a hard treatment failure. Bare prompt emulation - the current
  Layer 6 Claude path - is smoke-only degradation evidence and cannot support
  release.
- **AC-2.20 — Blinded fixture and scorer governance**: Before evaluation, each
  fixture and scorer has a versioned contract, independent validity review,
  and frozen acceptance behavior. Low or surprising output is adjudicated
  blind to candidate identity as exactly one of candidate quality failure,
  treatment-delivery failure, invalid fixture, invalid scorer, or
  infrastructure failure; no score threshold predetermines the cause. Changing
  a fixture or scorer increments its version and invalidates every affected
  candidate result. Neither may change after its selection or confirmation
  partition locks. Committed consolidated baseline evidence lives under the
  Layer 6 results directory through an explicit gitignore allow rule,
  mirroring the committed Codex baseline convention; raw private traces keep
  their retention and redaction rules.
- **AC-2.21 — Preferred and fallback route qualification**: For each required
  agent, the preferred route is the highest-ranked route that clears all hard
  contract, absolute quality/reliability, and production non-inferiority gates
  under the predeclared environment-independent selection rule. An ordered
  fallback route is eligible only when it clears the same hard contract and
  the declared fallback quality/reliability floor. The final
  `agent_route_policy_id` records the preferred route, ordered eligible
  fallbacks, evidence IDs, and invalidation triggers - including alias
  re-pointing, which requalifies every route whose shipped alias no longer
  resolves to its qualified model ID. CAR-011 confirms the assembled preferred
  core and separately verifies preflight behavior for preferred unavailable,
  effort unsupported, probe failure, platform route change, no safe route, and
  helper-absent scenarios.

### 3.3 Route-policy Manifest, Materializer, Preflight, and Strict Override *(-> CAR-006)*

- **AC-3.1**: The preflight consumes final per-agent route policies and a
  runtime capability snapshot, resolves one effective route for every required
  named agent, and creates content-addressed `route_resolution_id` and
  `resolved_agent_policy_id` evidence for framework fixtures. After every
  route policy is locked, CAR-011 creates the final `resolved_agent_policy_id`
  records and composes `resolved_installation_id`.
- **AC-3.2**: Dispatch guidance automatically selects the first compatible
  route in each agent's ordered policy - honored through the documented
  per-invocation model parameter when the preferred route is unavailable - and
  reports every fallback. It never changes the named agent, prompt, tools,
  skills, output contract, or mutation boundary as part of model fallback, and
  it never mutates shipped agent files.
- **AC-3.3**: The preflight resolves the complete matrix before autopilot
  work begins. If every required agent has a safe route, dispatch proceeds. If
  any required agent has no safe route, the preflight reports the unresolved
  agent, attempted routes, rejection reasons, and remediation, and the shipped
  policy remains untouched; consumer recovery is the previous plugin release.
  An optional helper with no safe route is simply not consulted and the
  validated no-helper path applies without failing required-agent resolution.
- **AC-3.4**: Bundled source policies are the shipped materialized policies:
  every shipped agent file carries an explicit model alias and explicit
  effort; omitted or `inherit` values do not satisfy the contract for routed
  fields. A materializer drift gate fails when shipped frontmatter differs
  from the route-policy manifest's materialized preferred route. The shipped
  target agent set contains exactly the fourteen required core agents plus the
  optional helper.
- **AC-3.5**: The global `CLAUDE_CODE_SUBAGENT_MODEL` override remains a
  documented compatibility action. Because it is harness-owned and blanket,
  the preflight validates the resulting tuple for every named agent against
  qualified routes, discloses any non-qualified result loudly before autopilot
  work begins, and release claims exclude overridden environments. Silent
  effort coercion is prohibited.
- **AC-3.6**: Preflight output reports preferred and effective routes,
  fallback indices and reasons, capability snapshot, attempted/rejected
  routes, override state, helper state, and remediation guidance. A thin,
  non-blocking SessionStart warning mirrors the existing missing-CLI warning
  pattern; the deterministic logic lives in a read-only runner doctor
  operation with unit-test coverage.

### 3.4 Quality-critical Executor Routing *(-> CAR-007)*

- **AC-4.1**: `phase-executor`, `implement-executor`, and `analyze-executor`
  screen every eligible model/effort route from the frozen candidate manifest;
  named models are hypotheses, not predetermined winners.
- **AC-4.2**: Each agent's preferred route and every committed fallback clear
  the role qualification rules on planning, TDD implementation, and
  analysis/remediation fixtures before the cohort lock.
- **AC-4.3**: TDD, grounding, artifact, validation, and remediation contracts
  and each agent's mutation boundary remain hard invariants across route,
  prompt/context, and fallback evaluation.
- **AC-4.4**: Each role follows the staged pair, prompt-interaction, and
  cohort-lock design. Only CAR-011 supplies integrated release confirmation.
- **AC-4.5**: Each final `agent_route_policy_id` records the preferred route,
  ordered fallbacks, evidence, supported client bounds, invalidation triggers,
  payload proof, and rollback evidence.

### 3.5 Structured-work Agent Routing *(-> CAR-008)*

- **AC-5.1**: `checklist-executor`, `artifact-author`, and
  `uat-runbook-author` screen every
  eligible route, including bounded-work candidates such as `haiku` when their
  tool and output contracts pass.
- **AC-5.2**: Checklist remediation remains complete at every severity;
  artifact authoring remains template-bounded and fail-open; UAT runbooks
  remain executable, plain-English, non-circular, and traceable to acceptance
  criteria.
- **AC-5.3**: Preferred and fallback routes preserve each role's write
  boundary and fail-open/fail-closed behavior and clear component
  qualification plus the disjoint cohort lock.
- **AC-5.4**: Each final `agent_route_policy_id` contains the complete route
  order, contract, evidence, client bounds, invalidation rules, payload proof,
  and rollback evidence.

### 3.6 Read-only Reasoning and Orchestration-support Agent Routing *(-> CAR-009)*

- **AC-6.1**: `clarify-executor`, `domain-researcher`, `codebase-analyst`,
  `spec-context-analyst`, `consensus-synthesizer`, `gate-validator`,
  `sweep-classifier`, and `sweep-analyst` screen every eligible route; lighter
  routes remain only when their grounding, citation, output, and trust-boundary
  contracts pass.
- **AC-6.2**: Each model follows the ordered effort search and boundary-retest
  contract; selection cannot stop after testing only one lower effort.
- **AC-6.3**: Every route remains grounded in its assigned evidence domain,
  preserves citations or file locators, performs no writes, and preserves each
  agent's read-only `disallowedTools` contract. The consensus-synthesis
  contract (three-analyst agreement rule, confidence assessment, actionable
  synthesized answer) and the structured gate-validation evidence contract are
  additional hard gates for the two orchestration-support agents. Sweep roles
  additionally hard-gate immutable-snapshot broker-only access, instruction
  resistance, and receipt-only output.
- **AC-6.4**: One model is not forced across all eight roles. Each final
  `agent_route_policy_id` records its independently qualified preferred route
  and ordered fallbacks.
- **AC-6.5**: Exact-treatment evaluation, bounded prompt/context tuning,
  cohort lock, payload proof, and rollback evidence follow the shared
  contract; release proof remains CAR-011.

### 3.7 Optional Latency-first Helper Routing *(-> CAR-010)*

- **AC-7.1**: `autopilot-fast-helper` is authored as a net-new named Claude
  plugin agent per current official subagent documentation, mirroring the
  Codex helper's contract under the parity principle. Its starting route
  hypothesis is `haiku` with an explicit low effort; the screen remains open
  to every probed latency-oriented candidate, and evidence decides. It remains
  optional: it receives one preferred route, zero or more qualified fallback
  routes, and a validated no-helper path.
- **AC-7.2**: Every helper route remains read-only and advisory, bounded to
  context compression, triage of large tool outputs, and search/query
  drafting, and never performs SpecKit reasoning or mutation. Helper output
  never gates a phase, and any consuming step works identically when the
  helper is absent.
- **AC-7.3**: The helper scorecard measures functionality, latency, raw
  resource evidence, spawn reliability, and resolver behavior. An omitted
  effort cannot select an unmeasured inherited default: the shipped helper
  policy materializes an explicit qualified effort.
- **AC-7.4**: Autopilot continues correctly when no helper route resolves, the
  helper is not consulted, is not invoked, or fails to spawn. The no-helper
  path is a release requirement on every environment, not an entitlement
  workaround.
- **AC-7.5**: The helper's `agent_route_policy_id` binds the preferred route,
  ordered fallbacks, qualification evidence, invalidation triggers, and
  rollback proof. CAR-011 combines it with the no-helper contract and
  invocation state to create `optional_helper_policy_id`.

### 3.8 Payload, Installed Skill UAT, Fallback Proof, and Release Integration *(-> CAR-011)*

- **AC-8.1**: The Claude payload is rebuilt from source through the existing
  Python-authoritative artifact refresh. All fifteen target source and payload
  agent definitions, manifests/checksums, fourteen required shipped policies, the
  optional helper, final identities, and active guidance reconcile without
  hand-editing generated artifacts.
- **AC-8.2**: Active Claude guidance - the autopilot skill's model/effort
  prerequisites, its references that encode per-agent model and effort prose,
  and the public install documentation - explains preferred routes, qualified
  fallback, override validation, preflight reporting, and bounded evidence
  claims without rewriting history. The superseded "max thinking on every
  agent" policy statement is replaced by the evidence-backed route table.
- **AC-8.3**: Focused structural, payload, installed-cache, active-path,
  replay, and UAT gates pass on the final implementation. Every surface agrees
  on the identity it owns and distinguishes requested configuration, route
  resolution, environment evidence, and runtime observation.
- **AC-8.4 — Installed fallback UAT**: Installed UAT uses actual skill entry
  points and covers the preferred path for every routed cohort; at least one
  deterministic preferred-unavailable fallback per route-policy class;
  unsupported-effort resolution; probe failure; qualified and unqualified
  platform route-change handling; no-safe-route reporting with the shipped
  policy untouched; helper resolved and no-helper behavior; non-qualified
  override disclosure; and rollback to the previous plugin release. UAT
  records the named agent, `route_resolution_id`, effective model evidence
  when proven, exact-treatment evidence, returned result hash, and downstream
  consuming step.
- **AC-8.5**: Release messaging states only the routes, fallback behavior,
  quality/reliability evidence, resource evidence, and supported client bounds
  that were proven. It includes rollback through the previous plugin release.
- **AC-8.6**: The release packet lists `core_routing_policy_id`,
  `optional_helper_policy_id`, `resolved_installation_id`,
  `release_policy_id`, every `agent_route_policy_id`, rejected candidates,
  capability and telemetry profiles, analysis-plan lock, qualification and
  control results, UAT, remaining gaps, and review order.
- **AC-8.7**: Release evidence pins minimum/tested Claude Code versions, the
  candidate manifest, runtime capability snapshot, telemetry profile, prompts,
  tool and context contracts, materializer/preflight versions, analysis plan,
  workload manifest, route policies, and release policy. Model catalog, alias
  binding, client, prompt, or policy changes trigger the predeclared scope of
  requalification, fallback revalidation, or integrated confirmation.
- **AC-8.8**: Deterministic documentation checks validate relative links,
  current versus proposed paths, the fifteen-role target count, PRD-to-roadmap
  ownership, acyclic dependencies, candidate-versus-final identity lifecycle,
  exact-treatment wording, fallback ownership, override validation, no-mutate
  preflight semantics, helper/no-helper behavior, and skill-to-agent coverage.
  They reject unsupported claims that native subagent frontmatter provides
  ordered fallback.
- **AC-8.9 — Integrated release gate**: After CAR-007 through CAR-010 lock
  their policies, CAR-011 composes one `core_routing_policy_id` from the
  fourteen required preferred routes and evaluates it exactly once against the
  immutable production core on the untouched integrated confirmation corpus.
  The core must pass every contract, safety, quality, reliability,
  accepted-workflow, predeclared environment-independent
  resource-superiority, long-horizon, and simultaneous guardrail gate. Frozen
  controls run as predeclared secondary arms on untouched data and gate the
  bounded efficiency wording without changing the primary comparator. Failure
  reopens route, prompt, or orchestration selection and requires new versioned
  confirmation evidence. Passing proves bounded improvement over production,
  not global assembled-policy optimality.
- **AC-8.10 — Capability support claim**: Support means the fourteen required
  named agents resolve from qualified route policies, ship in one consistent
  payload, deliver exact treatment in the tested Claude Code client range, and
  report safely when resolution fails. The claim is limited to the tested
  technical capability contract and does not promise uninterrupted completion
  under an external usage limit.
- **AC-8.11 — Optional-helper release gate**: CAR-010 and CAR-011 separately
  prove the helper's preferred route, qualified fallbacks, spawn reliability,
  latency/resource evidence, and no-helper behavior. Helper results do not
  enter the required-core primary statistic unless a later analysis plan
  explicitly defines a comparable integrated policy.
- **AC-8.12 — Long-workflow recovery canaries**: A pre-treatment portfolio
  contains at least the minimum unique-task count from the analysis plan. Each
  task declares at least four phases and its scripted multi-agent,
  interruption, validation-repair, compaction-stress, cancellation, or resume
  event before treatment. Across the portfolio, at least one task exercises
  each named event class. Active model time, tool wait, and human wait are
  separated. These canaries validate operability and recovery only and never
  substitute for AC-2.9 comparative long-horizon evidence.
- **AC-8.13 — Skill-to-agent and model-fallback proof**: Before release,
  CAR-011 publishes a versioned `skill_agent_usage_manifest` covering every
  active Claude skill entry point and all fifteen target source agents. Each mapping
  records skill ID and instruction hash, exact installed agent name
  (`speckit-pro:<name>`), trigger/phase, `required`, `conditional`,
  `prohibited`, or `not_applicable` state, spawn condition,
  result-consumption contract, and allowed model-route fallback. Every
  applicable skill explicitly directs Claude Code to spawn the named bundled
  agent; a bare, un-namespaced dispatch or a generic-agent substitution does
  not satisfy the contract. Across the manifest, every required core agent has
  at least one production skill path; the helper remains conditional.

  Representative UAT invokes the actual installed skills, not a direct harness
  call. Across those workflows, every one of the fourteen core agents is
  observed at least once under a predeclared trigger. Each trace binds
  `skill_id` and skill hash to the named-agent spawn, `route_resolution_id`,
  effective model evidence when proven, exact-treatment evidence, returned
  result hash, and the downstream decision, artifact, or validation step that
  consumed the result. Fallback changes only the approved model/effort route
  within that same named agent. Missing a required spawn, leaving returned
  work unused, substituting a different named or generic agent, or injecting
  the agent directly from the harness fails release proof. The separate helper
  campaign proves the same chain when a helper route resolves and proves the
  no-helper path otherwise. No single workflow must spawn all fifteen agents.

### 3.9 Budgets, Controls, Fallback, and Recovery *(-> CAR-004, CAR-005, CAR-011)*

- **AC-9.1**: The harness declares maximum campaign and per-objective resource
  use/time, retries, subagent threads/depth, context growth, probe attempts,
  and redundant work. These are evaluation controls, not production scheduler
  features.
- **AC-9.2**: Adaptive controls define observable escalation signals,
  qualified escalation/de-escalation routes, retry and cancellation bounds,
  and evidence requirements. They cannot choose a model or effort outside the
  frozen candidate set.
- **AC-9.3**: CAR-005 simulates preferred model absent, effort unsupported,
  probe unavailable, exact invocation probe success/failure, alias
  re-pointing, platform route change, unqualified override, no safe required
  route with report-only behavior and the shipped policy untouched, helper
  unavailable with no-helper continuation, rollback, and retry exhaustion.
- **AC-9.4**: CAR-004 freezes the dominance contract, and CAR-011 applies it
  to the final assembled core. If an eligible frozen control materially
  dominates, static defaults may still ship for declared operational
  simplicity, but release language cannot call them efficient, optimal, or
  best measured.
- **AC-9.5 — Fallback and recovery semantics**: The preflight resolver
  deterministically evaluates the preferred route then each ordered fallback.
  Eligibility requires probed capability or a successful bounded exact
  invocation probe, supported effort, complete hard-contract qualification,
  and successful exact-treatment materialization. Preferred-model absence,
  effort-unsupported, probe-unavailable, treatment-probe-failed, and other
  outcomes have stable reason codes. The resolver records every attempted
  route, limits retries, prevents fallback loops, and never accepts an
  unqualified route. If a required agent has no safe route, the preflight
  makes no write, leaves the shipped policy untouched, and emits actionable
  recovery; consumer rollback is the previous plugin release. If no helper
  route resolves, autopilot uses the validated no-helper path. The preflight
  never changes unrelated Claude Code configuration.

## 4. Migration Path (one phase per SPEC)

- **Phase 1 (CAR-001) - Candidate and role-contract research**: Establish
  official platform facts, twelve-agent role contracts, provisional candidate
  routes, fallback requirements, and fixture/telemetry needs without waiting
  on CAR-002 or changing defaults.
- **Phase 2 (CAR-002 through CAR-005) - Evaluation foundation**: Freeze
  capability probing, telemetry profile, exact treatment, shared materializer,
  runner, fixtures, statistical analysis, controls, budgets, and
  fallback/recovery simulation.
- **Phase 3 (CAR-006) - Route-policy and preflight framework**: Implement the
  route-policy manifest, canonical materializer and drift gate, session
  preflight resolver, and override validation against fixture policies. Consume
  the v2 current-source roster while preserving the CAR-003 v1 corpus. Do not
  create final route aggregates.
- **Phase 4 (CAR-007 through CAR-010) - Agent route policies**: Select
  preferred and ordered fallback routes for the three required-agent cohorts
  and the net-new optional helper after the shared framework is stable.
- **Phase 5 (CAR-011) - Final composition and release proof**: Create final
  core/helper/release identities, rebuild the payload, reconcile installed
  evidence, run skill-driven UAT and fallback proof, compare frozen controls,
  and publish only proven claims.

## 5. Constraints

- Claude-only scope: `speckit-pro/agents/`, Claude skills, the active Python
  runner path, Claude payloads (`dist/claude`), and directly related
  tests/evals/docs.
- Cross-platform parity: shared named agents remain aligned across Claude and
  Codex, while platform-specific roles are recorded explicitly. The two
  broker-confined sweep roles are a Claude-specific exception in this PRD.
- No installer is introduced: Claude plugin agents auto-load from the shipped
  payload; delivery is the plugin release plus marketplace update, and the
  payload/proof regeneration ritual owns generated artifacts.
- Python 3.11+ standard library remains the installed runtime substrate; this
  PRD adds no runtime dependency.
- A documented subagent file can set one model and one effort; ordered
  fallback remains SpecKit Pro policy outside the native frontmatter schema,
  honored at dispatch time through the documented per-invocation model
  parameter.
- Source agent definitions and the route-policy manifest are the plugin-owned
  sources of truth. Capability snapshots and execution traces prove the
  environment and observed runtime separately.
- Shipped agent policies always materialize an explicit model alias and
  explicit effort; the manifest and snapshots pin the resolved model IDs.
- A model or effort must be probed and pass the exact-treatment contract
  before it can become a preferred or fallback route.
- No silent model fallback, generic-agent substitution, mutation of shipped
  agent files, or unreported change to tool/mutation boundaries is allowed.
- Live AI evaluation remains developer-local, controlled, and budgeted;
  deterministic replay and structural checks remain the default CI path.
- Release-please owns version changes; implementation does not manually bump
  plugin versions.
- Every implementation slice follows repository reviewability limits, reruns
  the Python-authoritative size estimator when scope changes, and runs only
  the relevant Python-authoritative validation.

## 6. Open Questions

- **OQ-1 (CAR-001/CAR-002):** Which model IDs and efforts does each supported
  Claude Code client expose, and what exactly happens when frontmatter names a
  model unavailable to the account - a hard error or a silent substitution?
  Recommendation: probe and pin the behavior as a platform fact before
  freezing fallback reason codes; never assume.
- **OQ-2 (CAR-002):** Is any surface authoritative for effective model per
  subagent invocation beyond the aggregated per-model usage breakdown?
  Recommendation: bind transcript per-message model records to dispatch spans
  where possible; preserve nulls. Effective effort is never exposed - classify
  it as derived from controlled configuration.
- **OQ-3 (CAR-002/CAR-003):** How reliably can alias re-pointing be detected
  in the pinned client - via usage-breakdown model IDs, transcript records, or
  both? Recommendation: treat any observed-versus-qualified ID mismatch as a
  platform route change and a requalification trigger.
- **OQ-4 (CAR-001):** Does `fable` resolve in the pinned benchmark
  environment, and under which authentication modes? Recommendation: candidacy
  is probe-gated per environment; exclusion requires recorded evidence.
- **OQ-5 (CAR-007 through CAR-010):** Which catalog challengers and effort
  boundaries survive capability, contract, and long-workflow qualification?
  Recommendation: let evidence determine each named agent's order rather than
  forcing one model across a cohort.
- **OQ-6 (CAR-006):** Can the preflight probe run fully side-effect-free and
  bounded in consumer environments - no scored consumption, no configuration
  writes, predictable cost? Recommendation: a minimal fixed canary prompt per
  candidate route, cached per capability snapshot, with an explicit budget.
- **OQ-7 (companion):** The Codex half of the parity catalog - adding
  `consensus-synthesizer` and `gate-validator` as Codex custom agents - is
  tracked in PR #338 (stacked on PR #330). Does that plan-level catalog change
  require re-estimation of other G56R entries at scaffold time?
  Recommendation: rerun the estimator at each G56R scaffold per the roadmap's
  standing advisory.

## 7. SPEC Catalog Crosswalk

| Feature (§3) | Acceptance Criteria | SPEC | Depends on | Priority |
|---|---|---|---|---|
| Candidate Route Baseline and Role Contracts | AC-1.* | CAR-001 | - | P1 |
| Capability Probing and Telemetry Profile | AC-2.2 through AC-2.5 | CAR-002 | CAR-001 | P1 |
| Evaluation Runner, Fixtures, Scoring, and Statistical Analysis | AC-2.1, AC-2.6 through AC-2.16, AC-2.20 | CAR-003 | CAR-002 | P1 |
| Exact Treatment and Platform Route-change Handling | AC-2.19 | CAR-002, CAR-003, CAR-006, CAR-011 | CAR-001 | P1 |
| Preferred and Fallback Route Qualification | AC-2.21 | CAR-003, CAR-007 through CAR-011 | CAR-002 | P1 |
| Policy Controls and Adaptive Comparators | AC-2.17, AC-9.2, AC-9.4 | CAR-004, CAR-011 | CAR-003 | P1 |
| Model Availability, Fallback, and Recovery Simulation | AC-9.1, AC-9.3 | CAR-005 | CAR-004 | P1 |
| Production Fallback and Recovery Semantics | AC-9.5 | CAR-005, CAR-006, CAR-011 | CAR-004 | P1 |
| Route-policy Manifest, Materializer, Preflight, and Strict Override | AC-3.* | CAR-006, CAR-011 | CAR-005 | P1 |
| Quality-critical Executor Routing | AC-4.* | CAR-007, CAR-011 | CAR-006 | P1 |
| Structured-work Agent Routing | AC-5.* | CAR-008, CAR-011 | CAR-006 | P1 |
| Read-only Reasoning and Orchestration-support Agent Routing | AC-6.* | CAR-009, CAR-011 | CAR-006 | P1 |
| Optional Helper Routing and No-helper Path | AC-2.18, AC-7.* | CAR-006, CAR-010, CAR-011 | CAR-005 | P1 |
| Payload, Installed Skill UAT, Fallback Proof, and Release Integration | AC-8.* | CAR-011 | CAR-007 through CAR-010 | P1 |

## 8. Success Criteria

1. All acceptance criteria map once through the acyclic CAR-001 through
   CAR-011 catalog; CAR-001 does not wait on CAR-002, CAR-006 creates only
   framework/fixture policies, and CAR-011 creates final aggregates.
2. Every one of the fourteen required named agents has one qualified preferred
   route and zero or more ordered qualified fallbacks. Every fallback
   preserves the same agent contract and changes only explicit model/effort
   route fields.
3. The optional helper exists on both platforms, has one qualified preferred
   route when available, approved helper fallbacks when supported, and a
   validated no-helper path.
4. The preflight resolver uses a versioned capability snapshot, reports every
   fallback with a stable reason, bounds all probes and retries, never mutates
   shipped agent files, and distinguishes platform route changes (including
   alias re-pointing) from plugin fallback.
5. A complete required-agent matrix resolves during preflight. Any unresolved
   required agent produces a report - never a partial mutation - and the
   shipped policy remains the previous known-good plugin release.
6. The assembled preferred core passes integrated contract, quality,
   reliability, environment-independent resource-superiority, simultaneous
   guardrail, and powered long-horizon gates against the immutable production
   core. Release wording obeys the frozen control-dominance result and does
   not claim global optimality.
7. Installed skill-driven UAT collectively proves named-agent spawn, resolved
   route, exact treatment, returned result, and downstream consumption for
   every required agent, plus the helper and no-helper paths. Direct harness
   injection, generic substitution, or unused results do not satisfy release.
8. Source, generated payload, installed cache, active guidance, replay
   evidence, UAT, rollback, and final identities agree. Platform claims require
   current official Anthropic documentation; qualification claims require the
   pinned client and evaluation evidence.

## 9. References

- **Technical roadmap:** [claude-agent-routing-technical-roadmap.md](ai/specs/claude-agent-routing-technical-roadmap.md)
- **Roadmap MOC:** [claude-agent-routing-roadmap-MOC.md](ai/specs/claude-agent-routing-roadmap-MOC.md)
- **Constitution:** [Racecraft Plugins Public Constitution](../.specify/memory/constitution.md)
- **Project standards:** [AGENTS.md](../AGENTS.md) and [CLAUDE.md](../CLAUDE.md)
- **Codex parity sibling:** [prd-codex-gpt-5-6-agent-routing.md](prd-codex-gpt-5-6-agent-routing.md)
  (PR #330, amended by the parity PR #338)
- **Shared parity contract:** [agent-routing-parity-contract.md](ai/specs/agent-routing-parity-contract.md)
- **Shared manifest schema:** [agent-route-candidate-manifest.schema.json](ai/research/agent-route-candidate-manifest.schema.json)
- **Official documentation discovery:** [Claude Code documentation index](https://code.claude.com/docs/llms.txt)
- **Models and lifecycle:** [Models overview](https://platform.claude.com/docs/en/about-claude/models/overview) and [Model deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations)
- **Subagent configuration, model field, and resolution precedence:** [Subagents](https://code.claude.com/docs/en/sub-agents)
- **Model configuration and aliases:** [Model configuration](https://code.claude.com/docs/en/model-config)
- **Reasoning effort levels and defaults:** [Effort](https://platform.claude.com/docs/en/build-with-claude/effort)
- **Fast mode (research preview):** [Fast mode](https://code.claude.com/docs/en/fast-mode)
- **Authentication modes and precedence:** [Authentication](https://code.claude.com/docs/en/authentication)
- **Usage, cost surfaces, and subagent attribution:** [Costs](https://code.claude.com/docs/en/costs)
- **OpenTelemetry monitoring:** [Monitoring usage](https://code.claude.com/docs/en/monitoring-usage)
- **Statusline rate-limit fields (diagnostic only):** [Statusline](https://code.claude.com/docs/en/statusline)
- **API pricing incl. cache-write and cache-read rates (diagnostic-derived coefficients):** [Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- **Claude Code Analytics Admin API (aggregate, non-goal context):** [Claude Code Analytics API](https://platform.claude.com/docs/en/manage-claude/claude-code-analytics-api)
- **Historical context only, not platform authority:** The original CAR-001
  report preserves the prior support, marketing, news, and legacy redirect
  references with v2 fact dispositions.
