# PRD: Codex ChatGPT Subscription Agent Routing Optimization

**Status**: Active - not yet implemented
**Source**: Maintainer request plus official OpenAI documentation, `$research`,
and `$tavily-research` passes completed 2026-07-09 and revalidated 2026-07-11
**Created**: 2026-07-09
**Last updated**: 2026-07-11
**Target window**: Next SpecKit Pro minor release after the evaluation and
installer specifications in this roadmap are implemented
**Legacy identifier note**: The stable `G56R` SPEC prefix originated when this
work was scoped to GPT-5.6. It is retained for traceability only and no longer
limits the model catalog or ChatGPT subscription plans in scope.

---

## 1. Problem

> "Which efficient static installation defaults should SpecKit Pro use for
> each Codex agent so ChatGPT subscription consumers complete accepted
> end-to-end workflows with the lowest canonical resource consumption that
> preserves quality, reliability, and completion time?"

SpecKit Pro currently defines ten Codex custom agents. Nine source TOMLs pin
`gpt-5.5`; the latency-first helper pins `gpt-5.3-codex-spark`. Effort is mostly
`xhigh`, with two read-only analysts at `low` and the Spark helper omitting an
effort field. The current Python Layer 6 runner is not a production-routing
harness: it extracts only `developer_instructions`, prepends them to one of
three existing fixtures, invokes bare `codex exec`, and optionally overrides
reasoning effort. It does not explicitly load the TOML model, sandbox, skills,
MCP servers, tool schema, parent overrides, or a controlled Codex profile.

OpenAI positions `gpt-5.6-sol` for quality-critical work, `gpt-5.6-terra` as
the everyday balance, and `gpt-5.6-luna` for lighter or high-volume work.
SpecKit Pro consumers in scope authenticate Codex through any supported ChatGPT
subscription plan, not an API key. OpenAI documents those as different
accounting modes: ChatGPT sign-in uses subscription access and plan credits/
limits, while API-key sign-in is usage-based at standard API rates. The objective
therefore cannot be API dollars per isolated agent call.

OpenAI currently lists Codex for ChatGPT Free, Go, Plus, Pro, Business, Edu,
and Enterprise. Availability, limits, workspace permissions, plugin policy,
tools, and accounting can still differ by plan, workspace, role, surface, and
rate-card regime. This PRD therefore freezes a finite
`plan_support_manifest` before screening instead of allowing the release domain
to expand whenever OpenAI adds or changes a plan. An unresolved plan may inform
exploratory research but cannot prove support for a named manifest row.

The primary cross-plan resource measure is a versioned canonical normalization
of the raw input, cached-input, and output token vector. Observed included-limit
utilization, purchased-credit consumption, reset behavior, throughput, and
legacy Enterprise per-message accounting remain plan-stratified and are never
pooled. Model choice, context, reasoning, tools, retrieval, and caching all
affect consumption. The benchmark therefore accounts from the initial objective
through the terminal outcome, including parent/child agents, retries,
validation, compaction, escalation, repair, steering, and abandoned work.

The universal release unit is a nine-agent core that must be deliverable on
every frozen support-manifest row. Spark remains an optional Pro-only helper
with a separate, demand-sensitive limit and separate release evidence. The
plugin may still ship ten TOML files, but installation inventory is not proof
that the same ten-agent runtime policy is universally executable.

The requested research passes did not find a complete public benchmark that
compares the full subscription-available Codex catalog on SpecKit Pro's ten
roles. Therefore this PRD does not treat a generation, marketing tier, or current
default as a proven assignment. It defines an evidence-first promotion process
and ships only role assignments that clear a consumer-focused quality floor.

## 2. Goals & Non-goals

### 2.1 Goals

- Give every installed SpecKit Pro Codex agent an explicit, role-appropriate,
  immutable installable policy selected by measured evidence.
- Preserve consumer-visible correctness, grounding, output contracts,
  reliability, and completion time while minimizing canonical resource units
  per assigned objective under a fixed terminal policy and acceptance gate.
- Select one portability-first universal core from the model/capability
  intersection of a finite, versioned support manifest, while reporting the
  per-plan opportunity cost against the best measured plan-specific route.
- Make controlled model-effort pair, prompt/context, and speed decisions
  reproducible through exact treatment delivery, versioned fixtures, and a
  documented promotion rule.
- Keep installation predictable: role-pinned defaults, one explicit global
  compatibility override, no silent downgrade, and complete verification of
  all ten installed agents.
- Rebuild and verify the Codex payload, active guidance, and installed-cache
  evidence before release.
- Compare static role pins with an unpinned Codex-selected control and an
  explicit adaptive-policy control before claiming a static route is efficient.
- Evaluate model-effort pairs and bounded prompt/context variants in explicit
  stages because model, effort, instructions, handoffs, and tool context can
  interact. Do not claim independent model or effort effects without a
  separately predeclared factorial experiment.

### 2.2 Non-goals (out of scope)

- Changing Claude agent models, Claude commands, or Claude marketplace
  behavior.
- Adopting GPT-5.6 Pro mode, persisted reasoning, Programmatic Tool Calling,
  explicit prompt caching, or the Responses API multi-agent beta.
- Unbounded or aesthetic rewriting of every agent prompt. Prompt tuning is in
  scope when a variant targets measured instruction, handoff, tool-schema,
  duplicated-context, or compaction overhead and is evaluated alongside route
  candidates in Stage B against an unchanged-prompt control.
- Offering quality/balanced/economy install profiles or per-agent overrides in
  v1. The existing one-model compatibility override remains the KISS escape
  hatch.
- Automatically absorbing a new plan, entitlement, workspace category, or
  surface into the release domain without revising the support manifest and
  rerunning the affected confirmation evidence.
- Replacing historical model references, archived evidence, or old eval
  baselines solely to make repository-wide search results uniform.
- Claiming the universal core is individually optimal for every plan. Version 1
  optimizes portability across the frozen release domain; plan-specific
  profiles remain a later product decision.
- Treating GPT-5.6 Pro mode as the same concept as a consumer's ChatGPT
  subscription plan. The former remains out of scope; the latter defines the
  required authentication and accounting environment.

## 3. Acceptance Criteria

### 3.1 Research Baseline and Candidate Matrix *(-> G56R-001)*

- **AC-1.1**: A dated research record inventories all ten Codex agents and every
  active source, installer, skill, validation, eval, generated-payload, and
  installed-cache surface that encodes their model or effort policy.
- **AC-1.2**: The record cites current official OpenAI pages for model IDs,
  positioning, pricing, context/tool support, Codex custom-agent fields, and
  reasoning-effort guidance; conflicting secondary claims are rejected or
  labeled unresolved.
- **AC-1.3**: Every agent has a current baseline, capability-probed entries for
  every model exposed on each support-manifest row and tested client, supported
  effort values, a role-eligibility rationale, and a role-specific quality
  contract. The initial shortlist includes every eligible model; exclusion
  requires recorded incompatibility, contract failure, or predeclared dominance
  evidence.
- **AC-1.4**: Facts, inferences, and unverified assumptions are visibly
  separated, and no public head-to-head benchmark is claimed where none was
  located.
- **AC-1.5**: The time-boxed spike ends with a go/no-go decision and fixture
  requirements for G56R-003 after G56R-002 establishes trustworthy telemetry;
  it does not change installed defaults.
- **AC-1.6 — Frozen support manifest**: Before screening, G56R-001 publishes a
  versioned `plan_support_manifest`. `mandatory_plan_keys` = [`free`, `go`,
  `plus`, `pro_5x`, `pro_20x`, `business_standard`,
  `business_grandfathered_codex_seat`, `enterprise_flexible`,
  `enterprise_included_seat`, `enterprise_legacy_message`, `edu_flexible`,
  `edu_included_seat`]. These rows distinguish included usage, optional
  individual or workspace credits, grandfathered usage-based seats, and legacy
  message accounting instead of assigning one scalar regime to a named plan.
  Each row records `support_manifest_id`, `manifest_version`, `effective_as_of`,
  `plan_key`, `supported_plan_type`, `supported_subtier`, `workspace_type`,
  `authentication_mode`, `codex_client_range`, `codex_surface`,
  `accounting_regime_id`, `accounting_components`, `rate_card_revisions`,
  `required_capabilities`,
  `workspace_role_admin_prerequisites`, `optional_capabilities`,
  `known_exclusions`, `equivalence_class_id` or null,
  `equivalence_evidence_hashes`, `uat_owner`, `support_state`,
  `evidence_timestamp`, and `evidence_hashes`. Each row also freezes a versioned
  `boundary_contract` containing the one-window completion expectation,
  limit-near threshold, active-turn and new-phase/child-start policy,
  limit-exhausted behavior, auto-top-up/overage state, durable artifacts,
  resume-or-rerun contract, recovery instructions, and graceful-termination
  criteria. `support_state` is
  exactly `supported`, `conditional`, `unverified`, or `unsupported`. Every
  mandatory row remains visible and must be `supported` for universal release;
  any other state blocks that claim. Additional plan or managed-workspace
  categories require a manifest revision and affected confirmation rerun.
- **AC-1.7 — Current harness baseline**: The research record states that the
  current Python Layer 6 runner uses prompt emulation, ambient Codex
  configuration, four hard-coded effort values, and only three current role
  fixtures. Historical results are labeled `non_promotional` until replayed by
  G56R-003 with exact treatment delivery and frozen environment evidence.

### 3.2 Model-Effort Benchmark and Promotion Harness *(-> G56R-002 through G56R-004)*

- **AC-2.1 — Controlled model-effort pair selection**: Stage A has three
  predeclared steps. A1 screens each eligible model at its documented default
  ordinary effort and proceeds to scoring only after AC-2.19 proves treatment
  delivery. A2 holds the model and all non-effort variables fixed, ascends until
  a stable pass exists when necessary, then descends through every supported
  lower ordinary effort and retests the failing boundary. A3 compares the
  frozen passing model-effort pairs with every non-candidate variable frozen.
  Stage B admits only A3-shortlisted pairs and estimates predeclared
  prompt-by-pair interactions. Stage C freezes each complete cohort policy and
  evaluates it once on that cohort's disjoint lock partition; this is component
  selection, not release proof. Stage A selects pairs; it does not independently
  attribute model or effort effects. A1 and A2 use only the screening corpus;
  A3 and Stage B use selection. The candidate agent retains its unchanged
  baseline prompt throughout A1, A2, and A3. Stage B varies only the shortlisted
  candidate agent's prompt. Stage C uses only its preassigned cohort-lock
  partition. AC-8.9 alone uses the untouched integrated release-confirmation
  corpus.
- **AC-2.2 — Authentication and release domain**: The harness fails closed when
  it cannot verify ChatGPT authentication and bind the run to one frozen
  support-manifest row. Plan/subtier evidence comes from an authoritative field
  or archived entitlement record and is never inferred from capacity. An
  unresolved plan may contribute to exploratory plan-neutral research but may
  not qualify a named release row, enter cross-plan promotion, or support an
  availability, allowance, throughput, reset, or completion claim.
- **AC-2.3 — Complete trace**: Every assigned objective binds
  `support_manifest_id`, `installable_agent_policy_id`,
  `subscription_environment_id`, `execution_trace_id`,
  `universal_core_policy_id`, `optional_helper_policy_id`, and
  `release_policy_id`, then emits a parent-child trace through acceptance or the
  terminal stop. The trace records
  requested/returned model and effort, speed, input/cached-input/output tokens,
  rate revision, parent attribution, effective context/tools, compaction,
  retries, repair, validation, steering, cancellation, abandonment, and outcome.
  Raw nulls are preserved and never invented.
- **AC-2.4 — Primary-endpoint completeness**: A paired objective is eligible
  for promotion analysis only when 100% of attributable model activity has
  returned-model identity, speed, input/cached-input/output token counts,
  canonical-rate revision, and parent-child attribution. A plan-native rate or
  quota field is additionally required only for a claim that uses it. Any
  missing required field invalidates and reruns the pair or marks it non-
  comparable; a partial total can never support promotion. Production
  validation belongs in the workflow total; benchmark-only judge/scorer
  consumption is reported separately.
- **AC-2.5 — Distinct accounting measures**: The primary plan-neutral resource
  measure applies one frozen canonical token-rate schedule to the raw input,
  cached-input, and output token vector. Artifacts separately report that
  canonical score, plan-native token-derived credits when authoritative, every
  included-limit bucket's utilization, purchased-credit consumption, and any
  legacy per-message observation. Plan-native measures are never pooled across
  incompatible `accounting_regime_id` or rate-card revisions; equivalence classes
  cannot cross either boundary without a predeclared conversion that is excluded
  from the primary statistic. Reset-crossing runs remain in canonical
  objective totals but not ordinary within-window throughput estimates. API
  dollars remain a separately labeled diagnostic.
- **AC-2.6 — Data partitions and multiplicity**: The campaign uses disjoint
  screening, selection, cohort-lock, and integrated release-confirmation
  corpora. Screening performs capability/contract elimination; selection ranks
  a frozen shortlist; each Stage C cohort consumes only its preassigned lock
  partition once. Cohort locks remain inside the predeclared component-selection
  multiplicity family and cannot support the release claim. Final promotion uses
  the untouched integrated release-confirmation corpus exactly once under the
  predeclared hierarchical gatekeeping or family-wise error strategy. Changing
  a candidate, prompt, endpoint, margin, guardrail, weighting, or stopping rule
  after the integrated lock starts invalidates that confirmation run.
- **AC-2.7 — Estimand**: For randomized objective `i`, `R_i` is all attributable
  canonical resource units from objective start until acceptance or the fixed
  terminal stop, and `A_i` is 1 only on acceptance. Only objectives with
  successful treatment assignment enter the primary estimand. Candidate-caused
  quality or behavior failure after successful assignment, budget exhaustion,
  timeout, cancellation, and abandonment remain in `R_i` and `A_i`. A candidate-
  specific model, effort, entitlement, or capability incompatibility discovered
  at any treatment-delivery stage is a hard support-row qualification failure
  under AC-2.21; it is not an `R_i` observation and cannot be rerun into
  eligibility. Any pre-score consumption is reported separately.
  Independent harness or infrastructure misdelivery invalidates the arm and is
  rerun under the predeclared rule; recurrence blocks the harness. The primary
  endpoint is paired mean `R_i` per assigned objective versus the immutable
  production baseline; accepted-workflow rate is a separate quality gate.
- **AC-2.8 — Promotion statistic**: Promotion requires the upper one-sided 95%
  confidence bound for the task-level paired mean `R_i` difference to be below
  predeclared `-delta`. The AC-8.9 integrated release-confirmation result—not
  screening, selection, or a Stage C cohort lock—owns this decision. Critical
  safety/grounding/contract/mutation gates and accepted-workflow non-inferiority
  must pass first.
- **AC-2.9 — Statistical unit and weighting**: A unique workflow objective is
  the experimental unit; repeats are clustered within objective and inference
  is paired at task level using a predeclared task-cluster bootstrap or
  hierarchical model. Sample sizes count unique tasks. Workload-stratum weights
  are frozen before evaluation; plan rows are qualification strata, not pooled
  repeated observations. Cache crossover isolates arms so one cannot warm
  another's local or provider cache.
- **AC-2.10 — Guardrail registry**: Before candidate evaluation, every p95-
  canonical-resource, p95-duration, late-failure, retry, steering, and
  incomplete-workflow
  guardrail declares its definition, unit/denominator, immutable baseline,
  direction, margin, confidence/interval method, missing-data treatment,
  gatekeeping position, and minimum unique-task count. All guardrails pass
  simultaneously. Late failure means failure after a predeclared budget share
  or named validation phase. Controlled runs prohibit human steering or use one
  scripted intervention policy applied identically to both arms.
- **AC-2.11 — Effort search**: Capability probing produces each model's ordered
  ordinary effort set. Search starts at the documented default, ascends until
  the first stable pass when necessary, then descends and retests the first
  failing boundary to select the lowest stable pass. `max` is an ordinary
  single-agent high-effort candidate when supported. Ultra is excluded from
  per-agent descent because it changes orchestration topology; it is evaluated
  only as a policy-level control unless a separate subagent experiment is
  predeclared.
- **AC-2.12 — Speed control**: V1 freezes Standard speed for every pair selection,
  cohort lock, integrated confirmation, and release claim. It is an explicit
  environment prerequisite recorded by the installer and proven by treatment
  traces, not a field the current TOMLs or installer mutate. Any future speed
  optimization must treat speed as an explicit policy dimension and promote
  model + effort + prompt + speed together with the correct multiplier.
- **AC-2.13 — Immutable baseline**: Before screening, the production comparator
  is pinned by repository commit, plugin version, the nine-agent core policy,
  each installable policy ID, support manifest, canonical rate schedule,
  canonical subscription environment, Codex version, tool configuration, and
  corpus snapshot. Runtime observations belong to execution traces, not the
  installed baseline identity. A production or manifest change creates a
  versioned new baseline and requires affected confirmation to be rerun.
- **AC-2.14 — Campaign budget**: The campaign fixes maximum canonical resource
  use, plan-native usage where applicable, wall-clock time, candidates reaching
  cohort lock or release confirmation, capability/contract screening, and
  futility/dominance
  elimination thresholds before results are observed. A fixed racing/
  successive-halving method may be used; thresholds cannot change after viewing
  outcomes.
- **AC-2.15 — Evidence governance**: Evaluation uses licensed, synthetic,
  public, or explicitly authorized repositories in ephemeral clean worktrees,
  with no production credentials. Candidate context is isolated. Raw private
  traces have defined retention; public/private artifacts are separated and
  secrets/content/path redaction runs before publication. Account identity uses
  an opaque alias or keyed HMAC.
- **AC-2.16 — Replay schema**: G56R-002 defines and synthetically validates the
  versioned replay schema. It preserves the four evidence identities, three
  policy aggregates, raw
  telemetry, canonical and native formulas, nulls, rates, corpus partition,
  task/stratum IDs, weights, campaign decisions, guardrail registry,
  confirmation lock, failures, and selected/rejected routes. G56R-003 populates
  live artifacts only after exact treatment enforcement under AC-2.19.
- **AC-2.17 — Static-control consequence**: A static policy may be called
  efficient only if it passes against production and is not materially dominated
  by a tested unpinned or adaptive control on quality, reliability, canonical
  resource use, and duration. If a non-shipped control dominates, v1 may still
  ship static for declared operational simplicity, but messaging is limited to
  improvement over the previous static baseline and cannot claim best measured
  efficiency.
- **AC-2.18 — Universal core and optional Spark helper**: The universal primary
  endpoint covers exactly nine required agents with Spark disabled or provably
  not invoked in both arms. Spark is an optional Pro-row capability with a
  separate scorecard and never contributes to the universal canonical-resource
  claim. A Spark invocation invalidates a universal-core run. Every non-Spark
  support row must pass the no-helper product path unless a portable fallback is
  separately selected and validated.
- **AC-2.19 — Exact treatment delivery**: Every promotion-scored run executes
  the installed custom-agent TOML or a generated configuration proven
  semantically equivalent to the complete candidate policy. Before scoring, the
  harness verifies the support manifest, installable policy, subscription
  environment, and custom-agent identity, then initializes the execution trace.
  It records requested and returned model/effort, Standard speed,
  instruction hash, effective sandbox/approval behavior, expected and loaded
  skills, expected MCP servers and startup results, expected and actual tool
  schema, parent overrides, context/truncation/compaction, retry/escalation, and
  Codex client/surface. Any unexpected resolution, missing tool, failed server,
  unavailable skill, or permission/configuration mismatch is treatment
  misdelivery—not candidate quality—and invalidates the arm. Bare prompt
  emulation is non-promotional smoke or degradation evidence only. G56R-003
  classifies every pre-score delivery failure as candidate-attributable
  incompatibility or independent harness misdelivery and writes that
  classification to the AC-2.16 replay artifact. Candidate incompatibility at
  any treatment-delivery stage is a hard support-row qualification failure and
  cannot be rerun into eligibility; its pre-score consumption is reported as
  separate treatment-delivery resource use, outside `R_i`. Only independent
  misdelivery is rerun. Successfully delivered treatments alone reach quality
  scoring, and later failures follow AC-2.7.
- **AC-2.20 — Blinded fixture and scorer governance**: Every fixture and scorer
  has an immutable version and content hash before screening. Disputed results
  are adjudicated blind to candidate identity into exactly one of: candidate-
  quality failure, treatment-delivery failure, invalid fixture, invalid scorer,
  or infrastructure failure. A fixture or scorer change increments its version
  and invalidates every affected candidate result; a post-lock change invalidates
  the affected confirmation decision. A low score never presumes which class
  applies.
- **AC-2.21 — Cross-plan decision rule**: A universal candidate must deliver its
  complete treatment and clear safety, quality, availability, and reliability
  gates on every support-manifest row. Controlled selection uses the canonical
  environment and canonical resource score. Integrated release confirmation
  executes the same locked objective set in the canonical row and in every other
  mandatory row or predeclared equivalence class under one multiplicity family.
  The canonical row owns the primary superiority endpoint; every other stratum
  owns predeclared safety, quality, reliability, and canonical-resource non-
  inferiority gates. The winner is the lowest canonical-consumption candidate
  satisfying every stratum, not a pooled cross-plan mean. Evidence reports each
  row's opportunity cost against its best measured plan-specific candidate.
  Legacy-rate observations, included-limit utilization, purchased credits, reset
  behavior, and throughput remain separate plan-stratified outcomes. Before
  screening, each support row
  freezes its eligible plan-specific candidate set and
  `subscription_environment_id`; plan-only models may enter that row-specific
  set but never the universal set. The selection and cohort-lock partitions
  identify one best row-specific challenger and freeze it before integrated
  confirmation. Opportunity cost on the integrated release-confirmation corpus
  is paired mean `R_i(universal) - R_i(row-specific challenger)`,
  reported with the primary analysis's task clustering, weights, confidence
  method, and multiplicity strategy. This contrast is plan-stratified and
  descriptive; it cannot change the universal winner after confirmation lock.

### 3.3 Subscription-aware Installer Defaults and Explicit Override *(-> G56R-006)*

- **AC-3.1 — Identity separation**: Release evidence uses four canonical,
  content-addressed evidence identities plus three policy aggregates.
  `support_manifest_id` identifies the frozen release domain.
  `installable_agent_policy_id` contains only fields actually encoded and
  installed by the plugin: requested model/effort, developer instructions,
  sandbox defaults, plugin-owned skills and MCP declarations, and any plugin-
  owned retry/escalation policy that is concretely represented in instructions
  or configuration.
  `subscription_environment_id` contains the manifest row, plan/workspace/role,
  authentication, client/surface, rate regime, effective speed/service tier,
  inherited parent configuration, effective permissions, enabled skills/MCP/
  apps/tools, context policy, repository/project-instruction hashes, account
  isolation, and cache state.
  `execution_trace_id` contains returned model/effort, effective runtime
  overrides, MCP startup, actual tools/calls, parent-child graph, telemetry,
  retries, validation, termination, and outcome. `universal_core_policy_id`
  hashes a versioned plugin-owned core-policy manifest containing its schema
  version, the ordered nine role-to-`installable_agent_policy_id` mapping, and
  the plugin-owned parent orchestration/retry-policy hash.
  `optional_helper_policy_id` hashes the helper's installable policy, allowed
  manifest rows, installed-enabled/installed-disabled state, invocation rule,
  and no-helper/fallback contract. `release_policy_id` binds the core and helper
  aggregates plus the required environment-contract hash. Standard speed is an
  environment prerequisite, not an agent-TOML or installer-owned setting; the
  environment contract requires it and AC-2.19 verifies its effective value.
  G56R-006 creates, atomically installs, and verifies the plugin-owned aggregates;
  G56R-011 reconciles them across source, payload, installation, benchmark,
  canary, rollback, and PR evidence. The installer verifies only identities it
  owns; confirmation binds them to the observed environment and execution.
- **AC-3.2**: The global model override remains an explicit compatibility
  action for the nine required core agents. It retains each installed effort,
  prompt, sandbox, and other policy fields while leaving the optional Spark
  helper unchanged and preserving the Standard-speed environment requirement.
  Before mutation, every resulting model-effort tuple must have frozen
  compatibility evidence under that environment contract. Any
  incompatibility or unresolved tuple aborts atomically. Arbitrary user-supplied
  effort mappings are out of scope and never count as validated; silent effort
  coercion is prohibited. An unresolved tuple means the tested client/catalog
  cannot prove compatibility for the requested model-effort combination under
  Standard speed; it always aborts before mutation.
- **AC-3.3**: The installer distinguishes known unsupported from local catalog
  evidence (atomic abort), known unavailable from authoritative entitlement
  evidence (atomic abort), and availability unresolved when no authoritative
  preflight exists. Unresolved availability is disclosed before mutation and
  requires explicit acknowledgement plus a post-install canary that proves
  treatment delivery. This case applies only after tuple compatibility is proven
  but authoritative account-entitlement preflight remains unavailable. There is
  no silent downgrade or partial install. Hard abort applies to all nine required
  agents and to the optional helper only when that helper is enabled for the
  bound manifest row; known Spark unavailability on a non-Pro row produces the
  installed-disabled helper state and validated no-helper path, not install
  failure.
- **AC-3.4**: Source and destination inventory agree on all ten agent TOMLs,
  including `uat-runbook-author.toml`; unrelated user agents are preserved. The
  Spark TOML may be copied as installed-disabled on a non-Spark row, but it is
  never treated as a required or invocable capability there.
- **AC-3.5**: Install output reports all ten installed
  `installable_agent_policy_id` values, `universal_core_policy_id`,
  `optional_helper_policy_id`, `release_policy_id`, helper state, destination,
  support-manifest compatibility evidence, override state, copied files, result,
  and restart requirement. Returned-model and effective-speed proof are runtime/
  canary evidence, not installer-owned claims.
- **AC-3.6**: The current Python `install-codex-agents` registry entry is
  deferred and has no active destination-copy implementation. G56R-006
  implements and activates the helper through `helpers/install.py` and
  `helpers/registry.py`, with fake-home proof, without restoring a Bash helper.

### 3.4 Quality-critical Executor Routing *(-> G56R-007)*

- **AC-4.1**: `phase-executor`, `implement-executor`, and `analyze-executor`
  start with Sol and Terra hypotheses but screen every model in the universal
  candidate intersection, including the GPT-5.5 baseline and GPT-5.4 family,
  through AC-2.1 and AC-2.11.
- **AC-4.2**: Each committed installable policy clears the G56R-003 promotion
  rule under its frozen subscription environment on role-specific planning,
  TDD implementation, and analyze/remediation fixtures.
- **AC-4.3**: Agent sandbox, TDD, grounding, artifact, and remediation contracts
  remain hard invariants across A1/A2/A3 pair selection, Stage B prompt interaction,
  and the Stage C cohort lock.
- **AC-4.4**: Each role follows AC-2.1 and AC-2.19 exactly: controlled pair
  selection first, shortlisted prompt interactions second, then one exact-
  treatment cohort lock. Only AC-8.9 supplies release confirmation.
- **AC-4.5**: Cohort-specific source, install, validation, and rollback evidence
  makes the route independently reviewable.

### 3.5 Structured-work Agent Routing *(-> G56R-008)*

- **AC-5.1**: `checklist-executor` and `uat-runbook-author`
  start with Terra as a hypothesis but screen every universal-intersection
  candidate, including GPT-5.4 Mini for bounded structured work, through AC-2.1
  and AC-2.11.
- **AC-5.2**: Checklist remediation remains complete at every severity and UAT
  runbooks remain executable, plain-English, non-circular, and traceable to
  acceptance criteria.
- **AC-5.3**: The selected routes clear the universal-core promotion rule and
  preserve workspace-write boundaries and fail-open/fail-closed behavior
  specific to each role.
- **AC-5.4**: The cohort follows A1/A2/A3 frozen-prompt pair selection, Stage B
  shortlisted prompt interaction, and one Stage C cohort lock; install and
  rollback evidence records the installable policy and tested environments.

### 3.6 Read-only Reasoning Agent Routing *(-> G56R-009)*

- **AC-6.1**: `clarify-executor`, `domain-researcher`, `codebase-analyst`, and
  `spec-context-analyst` start with Terra as a hypothesis but screen every
  universal-intersection candidate; lighter models are retained for bounded
  scans only when their grounding and output contracts pass.
- **AC-6.2**: Each role applies AC-2.11 to every candidate model: start at the
  documented default, ascend when needed to find a stable pass, then descend
  and retest the failing boundary to select the lowest stable ordinary effort.
- **AC-6.3**: All outputs remain grounded in their assigned evidence domain,
  preserve citations/file locators, and perform no writes.
- **AC-6.4**: The installable static policy that passes the universal staged
  promotion rule is committed per role; one cohort model is not forced across
  all four roles.
- **AC-6.5**: Exact-treatment pair selection, joint prompt/context tuning,
  one Stage C cohort lock, install proof, and rollback evidence obey the same
  cohort contract as G56R-007; release proof remains AC-8.9.

### 3.7 Latency-first Helper Routing *(-> G56R-010)*

- **AC-7.1**: `autopilot-fast-helper` is an optional capability, not a universal
  core agent. It may retain Spark only on support-manifest rows with verified
  Spark availability; every other row uses the validated no-helper path unless
  a portable fallback is separately selected.
- **AC-7.2**: The helper remains read-only, advisory, bounded to compression,
  triage, and query drafting, and never performs SpecKit reasoning or mutation.
- **AC-7.3**: The helper scorecard separately measures functionality, latency,
  spawn reliability, fallback behavior, and observed Spark quota. It does not
  claim shared or canonical-resource superiority while Spark lacks a comparable
  measure; omitted effort never selects an unmeasured default.
- **AC-7.4**: Autopilot continues correctly when the helper is absent, disabled,
  unavailable, quota-limited, or fails to spawn. That no-helper path is part of
  universal product acceptance, not merely a fallback note.
- **AC-7.5**: Source, install, supported-row validation, no-helper validation,
  `optional_helper_policy_id`, installable/environment/trace identities, and
  rollback evidence are independently reviewable.

### 3.8 Payload, Documentation, UAT, and Release Proof *(-> G56R-011)*

- **AC-8.1**: The Codex payload is rebuilt from source; all ten source TOMLs,
  generated payloads, manifests/checksums, install inventory, the nine-agent
  universal core, optional-helper policy, and release policy agree without hand-
  editing generated artifacts.
- **AC-8.2**: Active Codex install/autopilot guidance explains the selected
  routes, promotion evidence, explicit global override, restart requirement,
  support-manifest boundary, and optional capabilities without rewriting
  historical records.
- **AC-8.3**: Structural, installer, benchmark-replay, payload, installed-cache,
  default-suite, and active-path gates pass on the final source tree. Source,
  payload, install evidence, subscription environments, and canaries agree on
  the identities each surface actually owns.
- **AC-8.4 — Multi-plan UAT**: Selection, cohort locks, and integrated release
  confirmation run in the versioned environments assigned to each stage. Every support-
  manifest row separately proves
  authentication, entitlement, model/effort catalog, plugin installation,
  required skills/MCP/tools, effective policy delivery, and the supported
  no-helper behavior. At least one live installed smoke workflow runs per
  predeclared plan-equivalence class. Plans may share a class only when rate-card
  regime, catalog, limit semantics, surface/tool contract, workspace controls,
  and boundary behavior are proven equivalent. The integrated confirmation
  campaign also runs its identical locked objective set in every mandatory row
  or proven equivalence class; smoke evidence cannot replace the AC-2.21
  statistical gates. Plan-specific allowance,
  throughput, reset, or completion claims require separate operational evidence
  for every named plan. An unresolved or inaccessible row is `unverified`, not
  supported.
- **AC-8.5**: Release messaging makes only progressively proven claims and
  includes rollback through an explicit global override or previous plugin
  release.
- **AC-8.6**: The PR packet lists `universal_core_policy_id`,
  `optional_helper_policy_id`, `release_policy_id`, per-row qualification and opportunity-cost results,
  rejected candidates, verification evidence, gaps, and review order.
- **AC-8.7**: Release evidence pins the support manifest, canonical rate
  schedule, minimum/tested Codex versions, per-row capability probes,
  environment IDs, rate regimes, and tested model availability. Model, client,
  prompt, rate-card, entitlement, manifest, installable-policy, helper-policy, or
  release-policy changes trigger the predeclared scope of requalification or
  rebenchmarking.
- **AC-8.8**: Before merge and release, deterministic documentation checks
  validate relative links, repository-local paths labeled current, fixture and
  agent counts, PRD-to-roadmap acceptance-criteria ownership, SPEC dependencies,
  and current-versus-proposed path labels. They reject absent paths described as
  current, obsolete Layer 6 shell paths, contradictory G56R-002/G56R-003
  ownership, and collapsed canonical/native/legacy accounting terms.
- **AC-8.9 — Integrated policy gate**: Before release, the assembled installed
  nine-agent `universal_core_policy_id` is compared with the immutable nine-agent
  production core on the untouched integrated release-confirmation corpus,
  consumed as one multi-stratum campaign after every cohort lock. Both arms use
  the same locked objectives in the canonical row and each mandatory row or
  proven equivalence class, with the helper disabled. The canonical stratum
  passes the primary endpoint; every other stratum passes the AC-2.21 non-
  inferiority gates, and all strata pass safety/quality/acceptance and guardrail
  gates simultaneously. A helper invocation invalidates the run. Failure reopens
  route, prompt, environment, or orchestration selection and requires a new
  versioned release-confirmation corpus.
- **AC-8.10 — Support claims**: Universal core support means the nine required
  agents install and deliver their tested treatment on every frozen manifest
  row. It does not mean every workflow completes within one allowance window or
  that the universal route is individually optimal for each plan. Operational
  claims remain plan-specific, and optional capabilities never become universal
  requirements. Release is blocked until every mandatory row from AC-1.6 is
  `supported`; a `conditional`, `unverified`, or `unsupported` row cannot be
  silently removed from the frozen-manifest universal claim.
- **AC-8.11 — Optional-helper release gate**: G56R-010 and G56R-011 separately
  prove Spark functionality, latency, spawn reliability, observed quota, and
  fallback on supported Pro rows, plus the no-helper path on all other rows.
  Evidence binds `optional_helper_policy_id` and the installed-enabled or
  installed-disabled state. Spark results never enter the universal-core primary
  statistic.
- **AC-8.12 — Long-workflow canaries**: The controlled canary portfolio contains
  at least the minimum unique-task count from the risk/sample rule. Each long
  workflow has at least four named phases and twelve model turns plus a
  predeclared duration or canonical-resource minimum. Across the portfolio, at
  least one task includes a multi-agent graph, compaction crossing,
  interruption/resume, validation failure/repair, and controlled approach to a
  plan-specific allowance boundary. Active runtime, quota wait, tool wait, and
  human wait are reported separately; results are stratified by manifest row or
  proven equivalence class.

### 3.9 Workflow Budget and Adaptive-policy Contract *(-> G56R-004, G56R-005, G56R-011)*

- **AC-9.1**: The evaluation harness declares maximum campaign and per-objective
  canonical resource use/time, retries, subagent threads/depth, context growth,
  and redundant work. These are harness controls, not new production scheduler
  behavior.
- **AC-9.2**: Adaptive-policy fixtures define observable escalation signals
  (for example repeated validation failure, high ambiguity, or cross-cutting
  dependency impact), catalog-derived escalation/de-escalation paths based on
  measured quality, canonical use, and plan-native boundary signals, plus
  cancellation of redundant child work.
- **AC-9.3**: Harness simulations classify limit-near/exhausted, reset crossing,
  timeout, continue, and cancel outcomes under a fixed terminal policy. Product
  checkpoint/resume features are a separate follow-up and do not block static
  installer work.
- **AC-9.4**: Version 1 may ship static defaults for operational simplicity only
  under AC-2.17. If a control dominates, release language is limited to measured
  improvement over the previous static baseline and cannot claim optimal or
  best measured efficiency.
- **AC-9.5 — Allowance-boundary support semantics**: Every support-manifest row
  declares whether one-window long-horizon completion is expected or unproven,
  observable limit-near/exhausted signals, the platform's active-turn and new-
  work behavior, durable artifacts, supported resume or rerun path, user-visible
  error and recovery instructions, and graceful-termination versus failure
  criteria. No plugin-initiated credit purchase or model/effort switch is
  automatic.
  G56R-001 freezes these values in each row before screening, G56R-005 validates
  them through simulation, and G56R-011 supplies live release proof. Included-
  only consumer rows document wait/reset or voluntary-upgrade recovery; credit-
  enabled consumer rows document wait/reset or explicit user-authorized credit/
  upgrade recovery; managed rows document the authoritative administrator,
  workspace-owner, overage, or account-team path when supported by evidence. An
  active turn may finish only when the platform permits it. V1 relies on the
  platform's stop behavior and documented recovery; it does not claim a plugin
  scheduler gate where no authoritative quota signal exists. The plugin never
  initiates or enables a purchase, auto top-up, overage, or route change.
  Controlled boundary runs freeze and record any pre-existing account-level
  auto-top-up or overage setting. A future plugin-managed checkpoint, no-new-
  child, or cross-reset resume policy requires a separate production-runtime
  specification.
  Unless production checkpoint/resume is separately implemented and validated,
  support means portable installation, exact treatment delivery, safe
  termination, and documented recovery—not uninterrupted completion across a
  quota reset.

## 4. Migration Path (phased - one phase per SPEC)

- **Phase 1 (G56R-001) - Research baseline**: establish authoritative facts,
  current surfaces, candidate routes, and role contracts without changing
  defaults.
- **Phase 2 (G56R-002 through G56R-005) - Evaluation foundation**: separately
  implement telemetry/traces, corpus/statistics, policy comparison, and
  allowance-boundary budgets.
- **Phase 3 (G56R-006) - Installer policy**: preserve role-pinned defaults and
  keep one explicit global compatibility override on the Python runtime path.
- **Phase 4 (G56R-007 through G56R-010) - Role cohorts**: evaluate and migrate
  four independently reviewable cohorts in parallel after the shared contract
  is stable.
- **Phase 5 (G56R-011) - Release proof**: regenerate payloads, reconcile shared
  assertions, run installed UAT, and publish only proven claims.

## 5. Constraints

- Codex-only scope: `speckit-pro/codex-agents/`, Codex skills, the active Python
  runner/install path, Codex payloads, and directly related tests/evals/docs.
- G56R-006 implements the currently deferred Python Codex-agent install helper;
  no deleted Bash helper may be restored or described as active.
- Python 3.11+ standard library remains the installed runtime substrate; this
  PRD adds no runtime dependency.
- Agent TOMLs remain the per-agent installable-policy source of truth; the
  versioned core, optional-helper, and release-policy manifests are the source of
  truth for plugin-owned composition and enablement. Effective speed, workspace
  permissions, inherited configuration, MCP startup, returned model, and runtime
  telemetry remain environment or trace evidence, never TOML claims.
- `model_reasoning_effort` values must be accepted by the installed Codex
  version and selected model before they become defaults.
- No silent model fallback, partial install, or unreported change to an agent's
  sandbox/mutation boundary.
- Live AI evals remain developer-local and budgeted; deterministic and replay
  checks remain the default CI path.
- Benchmark accounts must use ChatGPT subscription authentication. API-key runs
  are rejected as non-comparable production evidence.
- Shared-account activity invalidates allowance-delta attribution unless the
  run is isolated and the before/after quota state is captured.
- Release-please owns version changes; implementation does not manually bump
  plugin versions.
- Every implementation slice stays within the repository reviewability
  contract and reruns the Python-authoritative size estimator when scope changes.

## 6. Open Questions

- **OQ-1 (G56R-001):** Which manifest rows can be proven with controlled
  accounts and which must remain `unverified`? Recommendation: snapshot the
  finite domain, probe every row, and abstain from unsupported release claims.
- **OQ-1A (G56R-001/G56R-002):** Which Codex/account interface authoritatively
  exposes plan and subtier? Recommendation: record authoritative evidence when
  available. Otherwise retain the run as exploratory only; the mandatory row
  remains `unverified` and blocks universal release. Never infer plan or subtier
  from observed limits.
- **OQ-2 (G56R-002):** Which native app-server/client fields expose observed
  credits, token activity, account type/plan, and rate-limit buckets in the
  tested Codex version? Recommendation: capability-probe every field, preserve
  nulls, and derive estimates only with labeled/versioned formulas. Do not add a
  consumer-facing cache-write category unless native subscription telemetry
  exposes it.
- **OQ-3 (resolved for G56R-006):** The registry entry exists but is deferred;
  no active Python helper currently copies agents to the destination. G56R-006
  owns implementation in `helpers/install.py`, activation in
  `helpers/registry.py`, and fake-home contract tests.
- **OQ-4 (G56R-007 through G56R-010):** Which catalog challengers survive
  the research spike's availability and contract screen? Recommendation: keep
  the approved shortlist narrow and expand only unstable comparisons.
- **OQ-5 (G56R-001/G56R-002):** Which catalog entries are ineligible for a role
  because of missing custom-agent/tool/effort support? Recommendation: exclude
  only after a recorded capability or contract failure; GPT-5.4 Mini is a
  required bounded-work candidate when exposed.
- **OQ-6 (resolved for G56R-010):** Spark's separate, demand-sensitive preview
  limit has no common primary measure. Keep it out of universal confirmation,
  retain it only on proven Pro rows, and validate the no-helper path elsewhere.

## 7. SPEC Catalog Crosswalk

| Feature (§3) | Acceptance Criteria | SPEC | Depends on | Priority |
|---|---|---|---|---|
| Research Baseline and Candidate Matrix | AC-1.* | G56R-001 | - | P1 |
| Authentication, Telemetry, Treatment, and Trace Schema | AC-2.2 through AC-2.5, AC-2.15, AC-2.16 | G56R-002 | G56R-001 | P1 |
| Corpus Runner, Acceptance Scoring, and Statistics | AC-2.1, AC-2.6 through AC-2.14, AC-2.19 through AC-2.21 | G56R-003 | G56R-002 | P1 |
| Static/Unpinned/Adaptive Policy Comparison | AC-2.17, AC-9.2, AC-9.4 | G56R-004 | G56R-003 | P1 |
| Harness Budgets and Boundary Simulation | AC-9.1, AC-9.3, AC-9.5 | G56R-005 | G56R-004 | P1 |
| Subscription-aware Installer Defaults and Explicit Override | AC-3.* | G56R-006 | G56R-005 | P1 |
| Quality-critical Executor Routing | AC-4.* | G56R-007 | G56R-006 | P1 |
| Structured-work Agent Routing | AC-5.* | G56R-008 | G56R-006 | P1 |
| Read-only Reasoning Agent Routing | AC-6.* | G56R-009 | G56R-006 | P1 |
| Latency-first Helper Routing | AC-2.18, AC-7.* | G56R-010 | G56R-006 | P1 |
| Payload, Documentation, UAT, and Release Proof | AC-8.* | G56R-011 | G56R-007 through G56R-010 | P1 |

## 8. Success Criteria

1. All acceptance criteria are traceable through G56R-001 through G56R-011;
   the cross-cutting workflow-budget contract is implemented in the shared
   harness and release-proof specs.
2. The nine-agent universal core clears the untouched integrated release-
   confirmation corpus in the canonical environment and every per-row treatment,
   safety, quality, reliability, and non-regression qualification gate without
   pooling incompatible accounting.
3. A clean install verifies all ten installable identities plus the core,
   optional-helper, and release-policy IDs; environment and execution evidence
   separately prove effective speed, tools, permissions, and model resolution.
4. Source, generated payload, installed cache, guidance, tests, and UAT agree on
   the universal core and optional-helper split. Every mandatory manifest row
   is `supported`; any additional row has an explicit non-claiming state.
5. Consumers retain a documented global compatibility override and a previous
   release rollback path.

## 9. References

- **Technical roadmap:** [codex-chatgpt-agent-routing-technical-roadmap.md](ai/specs/codex-chatgpt-agent-routing-technical-roadmap.md)
- **Roadmap MOC:** [codex-chatgpt-agent-routing-roadmap-MOC.md](ai/specs/codex-chatgpt-agent-routing-roadmap-MOC.md)
- **Constitution:** [Racecraft Plugins Public Constitution](../.specify/memory/constitution.md)
- **Project standards:** [AGENTS.md](../AGENTS.md) and [CLAUDE.md](../CLAUDE.md)
- **Latest-model guidance:** [Using GPT-5.6](https://developers.openai.com/api/docs/guides/latest-model)
- **Migration guidance:** [Upgrading to GPT-5.6 Sol](https://developers.openai.com/api/docs/guides/upgrading-to-gpt-5p6-sol)
- **Codex models, Max, and Ultra:** [Codex models](https://learn.chatgpt.com/docs/models)
- **Codex subagents:** [Choosing models and reasoning](https://learn.chatgpt.com/docs/agent-configuration/subagents#choosing-models-and-reasoning)
- **Codex custom-agent configuration:** [Custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents)
- **ChatGPT plugins and effective permissions:** [Plugins](https://learn.chatgpt.com/docs/plugins)
- **Managed workspace controls:** [ChatGPT Work Admin FAQ](https://learn.chatgpt.com/docs/enterprise/work-admin-faq)
- **Model pages:** [Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol), [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra), [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
- **Codex authentication:** [ChatGPT subscription access versus API-key usage](https://learn.chatgpt.com/docs/auth)
- **Codex plans, credits, and limits:** [Codex pricing](https://learn.chatgpt.com/docs/pricing)
- **ChatGPT plan access:** [Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)
- **Native and legacy accounting:** [Codex rate card](https://help.openai.com/en/articles/20001106-codex-rate-card)
- **Individual-plan credits:** [Using credits for flexible usage](https://help.openai.com/en/articles/12642688-using-credits-for-flexible-usage-in-chatgpt-freegopluspro)
- **Managed-plan accounting variants:** [Flexible managed-plan pricing](https://help.openai.com/en/articles/11487671-flexible-pricing-for-chatgpt-enterprise-plans)
- **Codex native protocol/telemetry capability surface:** [App server](https://learn.chatgpt.com/docs/app-server)
- **Speed modes and Spark limits:** [Codex speed](https://learn.chatgpt.com/docs/agent-configuration/speed)
- **Long-workflow controls:** [Long-running work](https://learn.chatgpt.com/docs/long-running-work)
- **API-price diagnostic only:** [OpenAI API pricing](https://developers.openai.com/api/docs/pricing)
- **Prompt guidance:** [GPT-5.6 prompting best practices](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices)
