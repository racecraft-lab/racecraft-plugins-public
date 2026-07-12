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

> "Which evidence-backed static installation defaults should SpecKit Pro use
> so the component-wise assembled nine-agent core improves canonical resource
> use over the immutable production core in one predeclared canonical
> environment, clears every frozen plan-row qualification and non-inferiority
> gate—including the powered long-horizon and required plan-native allowance
> gates—and is not materially dominated by the named controls?"

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
SpecKit Pro consumers in scope authenticate Codex through supported ChatGPT
subscription and managed-workspace categories that provide ChatGPT-
authenticated Codex Local and satisfy the frozen treatment contract, not
through an API key. OpenAI documents those as different accounting modes:
ChatGPT sign-in uses subscription access and plan credits/limits, while API-key
sign-in is usage-based at standard API rates. The objective therefore cannot be
API dollars per isolated agent call.

OpenAI currently lists Codex for ChatGPT Free, Go, Plus, Pro, Business, Edu,
and Enterprise, while its current Codex rate card also names Health, Gov, and
ChatGPT for Teachers. Healthcare, Regulated, Clinicians, Gov, and FedRAMP
environments require explicit classification because their authentication,
surface, admin, tool, and compliance contracts can differ even when an
accounting schedule is shared. This PRD therefore freezes a finite
`plan_support_manifest` and named-category resolution table before screening
instead of allowing the release domain to expand whenever OpenAI adds or
changes a category. An unresolved category may inform exploratory research but
cannot prove support for a named manifest row.

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
default as a proven assignment. It defines evidence-first component
qualification followed by one integrated release decision and ships only role
assignments that clear the consumer-focused gates.

## 2. Goals & Non-goals

### 2.1 Goals

- Give every installed SpecKit Pro Codex agent an explicit, role-appropriate,
  immutable installable policy selected by measured evidence.
- Preserve consumer-visible correctness, grounding, output contracts,
  reliability, and completion time while reducing canonical resource units per
  assigned objective under a fixed terminal policy and acceptance gate.
- Make long-horizon efficiency a comparative release stratum with pre-treatment
  membership and independent quality/resource gates, not an operability-only
  canary claim.
- Select one portability-first universal core from the model/capability
  intersection of a finite, versioned support manifest, while reporting the
  per-plan opportunity cost against the best measured component-wise assembled
  plan-specific challenger.
- Block material plan-native allowance regressions wherever the same
  authoritative measure is attributable to both arms; otherwise publish an
  explicit canonical-resource-only claim boundary for that row.
- Make controlled model-effort pair, prompt/context, and speed decisions
  reproducible through exact treatment delivery, versioned fixtures, documented
  component-qualification rules, and one integrated release-decision rule.
- Keep installation predictable: role-pinned defaults, one explicit global
  compatibility override, no silent downgrade, exactly nine installed core
  agents, and a conditional tenth helper only where its invocation contract is
  proven.
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
- Searching the complete nine-agent combination space or claiming that the
  assembled core is the globally lowest-resource passing policy. Version 1
  performs component-wise pair, prompt, and cohort selection, then confirms one
  assembled core against its frozen comparators.
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
  `edu_included_seat`, `healthcare_managed`,
  `regulated_workspace_managed`, `gov_managed`, `teachers_managed`,
  `clinicians_managed`]. These rows distinguish included usage, optional
  individual or workspace credits, grandfathered usage-based seats, legacy
  message accounting, and managed-workspace treatment differences instead of
  assigning one scalar regime to a named plan.
  `named_category_keys` = [`chatgpt_for_healthcare`,
  `enterprise_regulated_workspace`, `chatgpt_gov`, `chatgpt_fedramp`,
  `chatgpt_for_teachers`, `chatgpt_for_clinicians`].
  `named_category_row_mappings` =
  [`chatgpt_for_healthcare -> healthcare_managed`,
  `enterprise_regulated_workspace -> regulated_workspace_managed`,
  `chatgpt_gov -> gov_managed`, `chatgpt_for_teachers -> teachers_managed`,
  `chatgpt_for_clinicians -> clinicians_managed`]. Each remains a distinct
  treatment row until full
  authentication, client/surface, model catalog, plugin, permission, tool, and
  boundary equivalence is proven. Rate-card inclusion is accounting evidence,
  not treatment-delivery evidence. `chatgpt_fedramp` is a named exclusion from
  this ChatGPT-authenticated release domain because current official guidance
  supports Codex there only through a pinned API-key CLI configuration, not
  ChatGPT sign-in.
  Every row records `support_manifest_id`, `manifest_version`, `effective_as_of`,
  `plan_key`, `supported_plan_type`, `supported_subtier`, `workspace_type`,
  `authentication_mode`, `codex_client_range`, `codex_surface`,
  `accounting_regime_id`, `accounting_components`, `rate_card_revisions`,
  `plan_native_guardrail_state`, `plan_native_guardrail_id`,
  `plan_native_guardrail_claim_boundary`,
  `required_capabilities`,
  `workspace_role_admin_prerequisites`, `optional_capabilities`,
  `known_exclusions`, `equivalence_class_id` or null,
  `equivalence_evidence_hashes`, `uat_owner`, `support_state`,
  `target_population_weight`, the shared `target_population_snapshot_id`,
  `baseline_policy_id`, `baseline_support_state`,
  `baseline_exact_treatment_evidence_hashes`, `baseline_comparator_type`,
  `row_reference_policy_id` or null, `row_reference_selection_rule_id`,
  `eligible_reference_policy_set`, `required_quality_and_contract_floors`,
  `relationship_to_production_policy`, `compatibility_projection_rules`,
  `selection_metric`, `selection_precedence`, `tie_break_rule`,
  `selection_evidence_hash`, `reference_qualification_evidence_id`,
  `comparator_claim_boundary`,
  `evidence_timestamp`, and `evidence_hashes`. Each named-category resolution
  records `named_plan_or_workspace`, `manifest_row`, `equivalence_class_id` or
  null, `authentication_supported`, `codex_surface`, `workspace_tool_deltas`,
  `support_claim`, and `evidence_hashes`. Each row also freezes a versioned
  `boundary_contract` containing the one-window completion expectation,
  limit-near threshold, active-turn and new-phase/child-start policy,
  limit-exhausted behavior, auto-top-up/overage state, durable artifacts,
  resume-or-rerun contract, recovery instructions, and graceful-termination
  criteria. `support_state` is
  exactly `supported`, `conditional`, `unverified`, or `unsupported`;
  `baseline_support_state` is exactly `deliverable`, `not_deliverable`, or
  `unverified`. Every
  mandatory row remains visible and must be `supported` for universal release;
  any other state blocks that claim. Additional plan or managed-workspace
  categories require a manifest revision and affected confirmation rerun.
  At manifest level, exactly one `target_population_snapshot` object records
  `target_population_snapshot_id`, `snapshot_source`,
  `query_or_derivation_version`, `measurement_start`, `measurement_end`,
  `population_definition`, `inclusion_and_exclusion_rules`,
  `unknown_plan_handling`, `coverage_numerator`, `coverage_denominator`,
  `minimum_coverage_threshold`, `weight_normalization_rule`,
  `fallback_canonical_row_rule`, `assignment_count_by_plan`,
  `terminal_state_by_extraction_cutoff`, `right_censored_count`,
  `active_count`, `missing_terminal_event_count`, `allowance_blocked_count`,
  `unknown_plan_count`, `extraction_cutoff`, `extraction_lag`, and
  `snapshot_hash`.
  The manifest records exactly one canonical row through `canonical_row_key`,
  `canonical_subscription_environment_id`, `canonical_selection_rationale`,
  `canonical_selection_rule_version`, `canonical_baseline_deliverable`,
  `canonical_candidate_set_hash`, and `canonical_lock_timestamp`. Before
  screening or outcome observation, it selects the exact-treatment-deliverable
  row with the greatest frozen `target_population_weight`; ties resolve by
  lexical `plan_key`. The weight source is a locked assignment cohort of all
  non-test, ChatGPT-authenticated SpecKit Pro objectives assigned to the
  immutable production core where `measurement_start <= assigned_at <
  measurement_end`; the window is the trailing 90 complete UTC days immediately
  before snapshot lock. Benchmark, canary, synthetic, and developer-test
  assignments are excluded. Every eligible assignment remains in
  `coverage_denominator` whether it succeeds, fails, times out, is abandoned,
  remains active or right-censored, is allowance-blocked, or lacks a recorded
  terminal event. An objective assigned outside the window is excluded even if
  it terminates inside it. Terminal status is reporting-only and never controls
  cohort membership or plan weights. `assignment_count_by_plan` supplies
  resolved-row weights; `coverage_numerator` counts assignments whose manifest
  row is authoritatively resolved at assignment. Unknown plans remain in the
  denominator and `unknown_plan_count`, receive no imputed weight, and are
  excluded from normalization. At the frozen extraction cutoff the artifact
  reports terminal, right-censored, active, missing-terminal, and allowance-
  blocked counts plus `extraction_cutoff` and `extraction_lag`, where
  `extraction_lag = extraction_cutoff - measurement_end`.
  The snapshot is representative only when `coverage_numerator /
  coverage_denominator >= 0.95`; resolved-row counts are normalized to sum to
  one. Exactly one predeclared `fallback_canonical_row_rule` applies when an
  authorized representative source is unavailable, the denominator is zero, or
  coverage is below 0.95: use `plus`; estimated weights and alternate fallbacks
  are prohibited. The fallback is valid only when the immutable production
  baseline and every frozen universal candidate pass exact-treatment preflight
  there; otherwise the campaign is blocked. Changing the snapshot, source,
  derivation, assignment-cohort definition, extraction cutoff, measurement
  window, population definition, coverage or normalization rule, fallback, or
  resulting canonical row invalidates selection, cohort locks, and integrated
  confirmation. Observed benchmark outcomes never choose the canonical row.
- **AC-1.7 — Current harness baseline**: The research record states that the
  current Python Layer 6 runner uses prompt emulation, ambient Codex
  configuration, four hard-coded effort values, and only three current role
  fixtures. Historical results are labeled `non_release_evidence` until replayed by
  G56R-003 with exact treatment delivery and frozen environment evidence.

### 3.2 Model-Effort Benchmark and Qualification Harness *(-> G56R-002 through G56R-004)*

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
  not qualify a named release row, enter cross-plan qualification or the
  integrated release decision, or support an
  availability, allowance, throughput, reset, or completion claim.
- **AC-2.3 — Complete trace**: Every assigned objective binds
  `support_manifest_id`, `installable_agent_policy_id`,
  `subscription_environment_id`, `execution_trace_id`,
  `universal_core_policy_id`, `optional_helper_policy_id`, the bound row's
  `helper_installation_state_id`, `workload_population_manifest_id`,
  `workload_stratum_id`, `canonical_rate_schedule_id`, and `release_policy_id`,
  then emits a parent-child trace through acceptance or the
  terminal stop. The trace records
  requested/returned model and effort, speed, input/cached-input/output tokens,
  rate revision, parent attribution, effective context/tools, compaction,
  retries, repair, validation, steering, cancellation, abandonment, and outcome.
  Raw nulls are preserved and never invented.
- **AC-2.4 — Primary-endpoint completeness**: A paired objective is eligible
  for qualification or release-decision analysis only when 100% of attributable
  model activity has returned-model identity, speed, input/cached-input/output
  token counts, canonical-rate revision, and parent-child attribution. A plan-
  native rate or quota field is additionally required for any guardrail or claim
  that uses it; a partial total can never support the release decision. Every
  telemetry failure emits `telemetry_failure_id`, `objective_id`, `arm`,
  `candidate_policy_id`, `manifest_row`, `workload_stratum_id`, `failure_stage`,
  `missing_fields`, `classification`, `classification_evidence`,
  `rerun_eligible`, `rerun_count`, and `final_disposition`. Classification uses
  a frozen automated rule or blinded AC-2.20 pre-outcome adjudication before
  quality or resource outcomes are inspected.
  `independent_transient_harness_failure` may receive at most one complete-pair
  rerun under the original assignment and cache condition; both arms and every
  attempt remain in the attrition artifact.
  `candidate_or_environment_inherent_telemetry_failure` cannot be rerun into
  eligibility and fails the candidate or row's telemetry qualification.
  `unknown_or_unproven_cause` receives no discretionary rerun and blocks the
  affected comparison and release claim. Arm-only reruns and primary conclusions
  from unexplained complete-case subsets are prohibited. Before screening, the
  attrition registry freezes the maximum transient-failure rate, maximum
  absolute arm-difference threshold, confidence method, and minimum unique-task
  count. Evidence reports attrition by arm, returned model, plan row, workload
  stratum, and cause; exceeding either threshold blocks qualification. Production
  validation belongs in the workflow total; benchmark-only judge/scorer
  consumption is reported separately.
- **AC-2.5 — Distinct accounting measures**: The primary plan-neutral resource
  measure applies one content-addressed schedule locked before screening. The
  `canonical_rate_schedule` artifact contains `canonical_rate_schedule_id`,
  `schema_version`, `authoritative_source_class`, `source_revision`,
  `effective_as_of`, `unit_name`, `returned_model_alias_map`,
  `model_rate_table`, `input_coefficient`, `cached_input_coefficient`,
  `output_coefficient`, `reasoning_token_inclusion_rule`,
  `standard_speed_multiplier`, `formula`, `numeric_precision`, `rounding_rule`,
  `unknown_model_behavior`, `schedule_hash`, and `lock_timestamp`.
  `authoritative_source_class = official_chatgpt_codex_token_rate_card`; each
  model-rate row copies the authoritative credits per million input, cached-
  input, and output tokens as exact decimal strings. At Standard speed the
  multiplier is exactly 1, and the explicit calculation is:

  `R_i = sum_j((input_tokens_j * input_coefficient(returned_model_j)) +
  (cached_input_tokens_j * cached_input_coefficient(returned_model_j)) +
  (output_tokens_j * output_coefficient(returned_model_j))) / 1_000_000`.

  Calculation uses decimal arithmetic without intermediate rounding and applies
  the one frozen final precision and rounding rule only after objective-level
  aggregation. Native `output_tokens` is charged exactly once; any separately
  exposed reasoning count is diagnostic and is never added. If the pinned
  client schema cannot prove that relationship, the invocation fails AC-2.4
  completeness. Every returned model or alias resolves to exactly one rate-table
  row. Proven capability or alias incompatibility is a non-rerunnable
  `candidate_or_environment_inherent_telemetry_failure`; genuinely unresolved
  alias or rate provenance is a non-rerunnable `unknown_or_unproven_cause`.
  Neither class may use a generic fallback rate. Any formula,
  coefficient, alias, reasoning rule, precision, rounding, source revision, or
  schedule change invalidates affected screening, selection, cohort-lock, and
  confirmation evidence.

  Artifacts separately report the canonical score, plan-native token-derived
  credits when authoritative, every included-limit bucket's utilization,
  purchased-credit consumption, and any legacy per-message observation. Plan-
  native measures are never pooled across incompatible `accounting_regime_id` or
  rate-card revisions; equivalence classes cannot cross either boundary without
  a predeclared conversion excluded from the primary statistic. Reset-crossing
  runs remain in canonical objective totals but not ordinary within-window
  throughput estimates. API pricing remains a separately labeled diagnostic and
  never supplies canonical coefficients.
- **AC-2.6 — Data partitions and multiplicity**: The campaign uses disjoint
  reference-qualification, screening, selection, cohort-lock, and integrated
  release-confirmation corpora. Reference qualification runs before candidate
  screening only when comparable frozen evidence is unavailable and cannot be
  reused by a candidate. Screening performs capability/contract elimination;
  selection ranks a frozen shortlist; each Stage C cohort consumes only its
  preassigned lock partition once. Cohort locks remain inside the predeclared component-selection
  multiplicity family and cannot support the release claim. The final release decision uses
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
  A successfully assigned arm that attempts to resolve, spawn, or invoke the
  optional helper during universal-core evaluation is a candidate-caused core-
  policy contract failure: `A_i = 0`, all measurable universal-core `R_i`
  through the terminal stop is retained, and the arm cannot be rerun into
  eligibility. Any separately metered helper activity is reported outside
  `R_i`. Only independently proven harness contamination may invalidate and
  rerun that arm.
  Independent harness or infrastructure misdelivery invalidates the arm and is
  rerun under the predeclared rule; recurrence blocks the harness. Post-
  assignment telemetry completeness failures follow AC-2.4, and this treatment-
  delivery rule never authorizes an arm-only telemetry rerun. The primary
  endpoint in the canonical row is paired mean `R_i` per assigned objective
  versus the immutable production baseline. Every other row pairs against its
  AC-2.13 assigned comparator; accepted-workflow rate is a separate quality
  gate.
- **AC-2.8 — Integrated release-decision statistic**: The AC-8.9 decision
  requires the upper one-sided 95% confidence bound for the canonical-row
  task-level paired mean `R_i` difference to be below predeclared `-delta`.
  Every non-canonical row applies its predeclared non-inferiority bound against
  its AC-2.13 assigned comparator. The AC-8.9 integrated release-confirmation
  result—not screening, selection, or a Stage C cohort lock—owns this decision.
  Critical safety/grounding/contract/mutation gates and accepted-workflow non-
  inferiority must pass first. The integrated multiplicity family includes the
  powered `long_horizon_stratum_id`. Regardless of the weighted aggregate, that
  stratum independently passes accepted-workflow rate, semantic-quality floors,
  paired mean canonical-resource non-inferiority, p95 canonical resource, p95
  duration, late-failure, retry, and compaction-overhead gates against each row's
  assigned comparator. Failure cannot be offset by another workload stratum.
  Release wording may claim improved long-horizon efficiency only when the
  canonical-row long-horizon paired mean additionally clears a predeclared
  superiority margin `-delta_long_horizon` under its frozen one-sided confidence
  rule.
- **AC-2.9 — Statistical unit and weighting**: A unique workflow objective is
  the experimental unit; repeats are clustered within objective and inference
  is paired at task level using a predeclared task-cluster bootstrap or
  hierarchical model. Sample sizes count unique tasks. Workload-stratum weights
  are frozen before evaluation; plan rows are qualification strata, not pooled
  repeated observations. Before screening, G56R-003 publishes and locks one
  versioned `workload_population_manifest` containing
  `workload_population_manifest_id`, `snapshot_source`,
  `target_workload_definition`, `stratum_definitions`,
  `pre_treatment_assignment_rule`, `assignment_count_by_stratum`,
  `stratum_weights`,
  `unknown_stratum_handling`, `minimum_unique_tasks_per_stratum`,
  `long_horizon_stratum_id`, `manifest_hash`, and `lock_timestamp`. Weights sum
  to one and derive from the declared target workload, never candidate outcomes.
  For v1, `snapshot_source` links the AC-1.6
  `target_population_snapshot_id` and reuses its frozen underlying assignment
  cohort and `query_or_derivation_version`; `assignment_count_by_stratum`
  records authoritative classifications for that same cohort, and
  `stratum_weights` normalize those counts over known strata. Unknown
  assignments stay in the coverage denominator, and classification coverage
  below 0.95 blocks the campaign rather than permitting imputation or alternate
  weights.
  Every objective is assigned exactly one stratum from immutable task or
  protocol metadata before either arm runs. Realized tokens, duration, model
  turns, compactions, retries, or outcomes cannot define or change membership.
  At minimum, the long-horizon definition requires four mandatory acceptance-
  linked phases and two separately scored validation checkpoints declared in the
  task protocol before treatment; it may add other immutable task properties.
  Unknowns follow the frozen handling rule and cannot be silently discarded.
  Integrated confirmation gives the required long-horizon stratum a confidence-
  powered minimum unique-task count in every required plan row or equivalence
  class. Changing the source, definitions, assignment rule, weights, minimums,
  or long-horizon identity invalidates affected selection, cohort-lock, and
  integrated-confirmation evidence. Cache crossover isolates arms so one cannot
  warm another's local or provider cache.
- **AC-2.10 — Guardrail registry**: Before candidate evaluation, every p95-
  canonical-resource, p95-duration, late-failure, retry, steering, and
  compaction-overhead, incomplete-workflow, and required plan-native allowance
  guardrail declares its definition, unit/denominator, frozen assigned comparator,
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
  optimization must treat model + effort + prompt + speed as one explicit
  policy tuple with the correct multiplier.
- **AC-2.13 — Immutable baseline and row comparators**: Before screening, the
  canonical-row production comparator is pinned by repository commit, plugin
  version, the nine-agent core policy, each installable policy ID, support
  manifest, canonical rate schedule ID/hash, workload-population manifest,
  canonical subscription environment, Codex version, tool configuration, and
  corpus snapshot. The canonical row
  must set `baseline_support_state = deliverable`,
  `baseline_comparator_type = production_baseline`, and
  `comparator_claim_boundary = production_superiority`. Every non-canonical row
  freezes one exact-treatment-deliverable comparator before screening. It uses
  the immutable production baseline when deliverable; otherwise it uses a
  content-addressed `row_reference_policy_id` selected before candidate
  screening under its frozen `row_reference_selection_rule_id`. The
  rule serializes `eligible_reference_policy_set`,
  `required_quality_and_contract_floors`,
  `relationship_to_production_policy`, `compatibility_projection_rules`,
  `selection_metric`, `selection_precedence`, `tie_break_rule`, and
  `selection_evidence_hash`. The `reference_qualification_evidence_id`
  content-addresses either previously frozen evidence produced under the same
  task, validator, environment, and acceptance contracts or a dedicated pre-
  screen reference-qualification corpus disjoint from every candidate and
  confirmation partition. G56R-003 executes that corpus before candidate
  screening when prior comparable evidence is unavailable. Any evidence or
  corpus change invalidates the reference and final support-manifest lock. The
  `eligible_reference_policy_set` contains only
  exact-treatment-deliverable
  compatibility projections of the immutable production core. Each projection
  preserves every production-policy field not independently proven
  incompatible, may change only fields independently proven incompatible, and
  clears the frozen `required_quality_and_contract_floors`, including every
  absolute safety, quality, grounding, contract, mutation, and reliability
  floor. The frozen `selection_metric` and `compatibility_projection_rules` rank projections first by
  ascending changed-agent count, then ascending changed-field count, then by
  `selection_precedence`; `tie_break_rule` resolves any remainder by lexical
  content-addressed policy ID. Candidate outcomes, resource measurements, and
  shortlist membership cannot affect reference generation or selection. If no
  eligible projection passes exact treatment and the absolute floors, the row
  is not `supported` and blocks universal release. Changing the eligible set,
  projection rules, floor registry, precedence, tie-break, evidence hash, or
  selected reference invalidates affected evidence. Its claim boundary is
  respectively
  `production_noninferiority` or `row_reference_noninferiority`. A row-reference
  result establishes support and non-regression only and cannot claim
  improvement over production. If neither comparator is deliverable, the row
  is not `supported` and blocks universal release. Runtime observations belong
  to execution traces, not installed comparator identities. Any comparator,
  production policy, or manifest change creates a versioned new baseline and
  invalidates affected selection, cohort-lock, and confirmation evidence.
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
  telemetry, the complete telemetry-attrition artifact and attempt history,
  canonical-rate schedule/formula/alias resolution, plan-native formulas, nulls,
  rates, corpus partition, workload-population manifest and preassigned stratum
  IDs, named-category resolution, plan-population snapshot and fallback,
  canonical-row lock, per-row comparator selection rule/qualification evidence/
  identity/delivery/claim boundary, weights, campaign decisions, guardrail
  registry, confirmation lock, failures, and selected/rejected routes.
  G56R-003 populates
  live artifacts only after exact treatment enforcement under AC-2.19.
- **AC-2.17 — Frozen policy controls and dominance rule**: Before cohort
  selection, G56R-004 defines, exact-treatment validates, and content-addresses
  the unpinned, adaptive, and Ultra control policies. It freezes every adaptive
  signal, threshold, escalation/de-escalation path, and Ultra topology, plus
  control-eligibility gates, dominance metrics and margins, confidence method,
  multiplicity position, and integrated-confirmation arm assignment. G56R-004
  does not assess whether the future release policy is dominated. A control
  materially dominates only when it clears every mandatory safety, quality,
  reliability, availability, and support-row gate; meets the frozen quality,
  reliability, guardrail, and duration non-inferiority margins; and clears the
  predeclared canonical-resource superiority margin. G56R-011 compares the
  final frozen `universal_core_policy_id` with these controls under AC-8.9.
  Changing any control content hash, adaptive parameter, dominance margin,
  confidence method, multiplicity assignment, or arm assignment invalidates the
  affected control comparison and bounded efficiency claim.
- **AC-2.18 — Universal core and optional Spark helper**: The universal primary
  endpoint covers exactly nine required agents. During every qualification or
  cohort lock for the nine-agent core and in every primary and secondary arm of
  integrated confirmation, Spark is
  `not_installed` and absent from the agent registry and effective tool surface
  on every row, including Pro rows. An attempted resolution, spawn,
  or invocation after successful assignment follows AC-2.7 and hard-fails the
  universal-core contract. Independently proven harness contamination that
  makes Spark available may invalidate and rerun the arm; candidate-caused
  behavior may not. The separate optional-helper campaign may install Spark on
  supported Pro rows and never contributes to the universal canonical-resource
  claim. Every support row must pass the no-helper product path unless a
  portable fallback is separately selected and validated.
- **AC-2.19 — Exact treatment delivery**: Every scored run executes
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
  emulation is smoke-only degradation evidence and cannot support release. G56R-003
  classifies every pre-score delivery failure as candidate-attributable
  incompatibility or independent harness misdelivery and writes that
  classification to the AC-2.16 replay artifact. Candidate incompatibility at
  any treatment-delivery stage is a hard support-row qualification failure and
  cannot be rerun into eligibility; its pre-score consumption is reported as
  separate treatment-delivery resource use, outside `R_i`. Only independent
  misdelivery is rerun. Successfully delivered treatments alone reach quality
  scoring, and later failures follow AC-2.7. After assignment, AC-2.18's
  optional-helper attempt rule overrides generic unexpected-resolution
  classification.
- **AC-2.20 — Blinded fixture and scorer governance**: Every fixture and scorer
  has an immutable version and content hash before screening. Disputed results
  are adjudicated blind to candidate identity into exactly one of: candidate-
  quality failure, treatment-delivery failure, invalid fixture, invalid scorer,
  or infrastructure failure. A fixture or scorer change increments its version
  and invalidates every affected candidate result; a post-lock change invalidates
  the affected confirmation decision. A low score never presumes which class
  applies. Telemetry-completeness disputes use AC-2.4's three-class taxonomy
  under the same blinded and versioned governance; they do not create another
  telemetry class.
- **AC-2.21 — Cross-plan decision rule**: A universal candidate must deliver its
  complete treatment and clear safety, quality, availability, and reliability
  gates on every support-manifest row. Controlled component selection uses the
  canonical environment and canonical resource score. The resulting component-
  wise assembled `universal_core_policy_id` proceeds to AC-8.9 only when it
  satisfies every row's treatment, safety, quality, reliability, and assigned-
  comparator gates. Integrated release confirmation executes the same locked
  objective set in the canonical row and every other mandatory row or
  predeclared equivalence class under one multiplicity family. The canonical
  row owns the production-superiority endpoint; every other stratum compares
  the candidate with its AC-2.13 assigned comparator under predeclared safety,
  quality, reliability, and canonical-resource non-inferiority gates. Before
  screening, every support row freezes `plan_native_guardrail_state = required |
  unavailable`. It is `required` whenever authoritative telemetry exposes the
  same attributable native measure for both arms, and its
  `plan_native_guardrail_claim_boundary = native_allowance_noninferiority`.
  The content-addressed
  `plan_native_guardrail_id` then freezes `native_metric`, `rate_limit_id`,
  `accounting_regime_id`, `rate_card_revision`, `comparator`, `unit`,
  `denominator`, `direction`, `noninferiority_margin`, `confidence_method`,
  `reset_crossing_treatment`, `missing_data_rule`, `multiplicity_position`,
  `minimum_unique_task_count`, and `account_isolation_proof`. A required guardrail
  uses identical bucket/window semantics and controlled account isolation,
  passes simultaneously in integrated confirmation, and is never pooled across
  rows or regimes; a material regression blocks that row and universal release.
  An `unavailable` state must be established from authoritative capability
  evidence before screening; missing telemetry observed during evaluation
  follows AC-2.4 and cannot downgrade a `required` row. When comparable
  authoritative telemetry is unavailable, the row's
  `plan_native_guardrail_claim_boundary = canonical_resource_only`; release
  evidence states that native allowance, purchased-credit, reset, and throughput
  regression were not ruled out. A native-allowance efficiency claim requires a
  required-and-passing native guardrail for every row covered by that claim.
  Passing establishes canonical-row improvement over production and non-regression
  within every other row's declared claim boundary. It does not establish the
  lowest-resource complete nine-agent policy among alternative assemblies or a
  pooled cross-plan mean. Evidence reports each row's opportunity cost against
  its best measured component-wise assembled plan-specific challenger.
  Legacy-rate observations, included-limit utilization, purchased credits, reset
  behavior, and throughput remain separate plan-stratified outcomes. Before
  screening, each support row
  freezes its eligible plan-specific candidate set and
  `subscription_environment_id`; plan-only models may enter that row-specific
  set but never the universal set. The selection and cohort-lock partitions
  identify one component-wise assembled row-specific challenger under the
  frozen rule and freeze it before integrated confirmation. Opportunity cost on
  the integrated release-confirmation corpus
  is paired mean `R_i(universal) - R_i(row-specific challenger)`,
  reported with the primary analysis's task clustering, weights, confidence
  method, and multiplicity strategy. This contrast is plan-stratified and
  descriptive; it cannot change the frozen assembled release candidate after
  confirmation lock.

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
  `optional_helper_policy_id` hashes the helper definition plus the complete,
  ordered `plan_key -> helper_installation_state_id` mapping. Each row-specific
  `helper_installation_state_id` hashes `installed_enabled` or `not_installed`,
  the resolved helper policy or null, invocation rule, no-helper/fallback
  contract, and supporting capability evidence. `release_policy_id` binds the core and helper
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
  bound manifest row. Known or unresolved Spark availability on a non-Spark row
  produces `not_installed` plus the validated no-helper path, not core-install
  failure.
- **AC-3.4**: Source and generated payload inventory contain all ten agent TOMLs,
  including `uat-runbook-author.toml`. The plugin-managed destination set
  contains exactly nine required core TOMLs plus the helper only when its row-
  specific state is `installed_enabled`. Unrelated user-owned files are excluded
  from this count and preserved byte-for-byte. Any reinstall whose bound
  `helper_installation_state_id` is `not_installed` atomically removes any stale
  plugin-managed Spark TOML and registry entry, then proves helper resolution
  and spawning fail closed to the no-helper path.
  A future disabled-in-place state requires an official documented agent-disable
  mechanism, a capability probe, and a pinned minimum client version.
- **AC-3.5**: Install output reports the nine installed core
  `installable_agent_policy_id` values, `universal_core_policy_id`,
  `optional_helper_policy_id`, the bound row's `helper_installation_state_id`,
  `release_policy_id`, helper state, the optional
  tenth helper identity only when installed, destination, support-manifest
  compatibility evidence, override state, copied files, result, and restart
  requirement. Returned-model and effective-speed proof are runtime/canary
  evidence, not installer-owned claims.
- **AC-3.6**: The current Python `install-codex-agents` registry entry is
  deferred and has no active destination-copy implementation. G56R-006
  implements and activates the helper through `helpers/install.py` and
  `helpers/registry.py`, with fake-home proof, without restoring a Bash helper.

### 3.4 Quality-critical Executor Routing *(-> G56R-007)*

- **AC-4.1**: `phase-executor`, `implement-executor`, and `analyze-executor`
  start with Sol and Terra hypotheses but screen every model in the universal
  candidate intersection, including the GPT-5.5 baseline and GPT-5.4 family,
  through AC-2.1 and AC-2.11.
- **AC-4.2**: Each committed installable policy clears the G56R-003 role-
  qualification rule under its frozen subscription environment on role-specific planning,
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
- **AC-5.3**: The selected routes clear the component-qualification and cohort-
  lock rules and preserve workspace-write boundaries and fail-open/fail-closed
  behavior specific to each role.
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
- **AC-6.4**: The installable static policy that passes the staged component-
  qualification and cohort-lock rules is committed per role; one cohort model
  is not forced across all four roles.
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
- **AC-7.4**: Autopilot continues correctly when the helper is not installed,
  unavailable, quota-limited, not invoked, or fails to spawn. That no-helper
  path is part of universal product acceptance, not merely a fallback note.
- **AC-7.5**: Source, install, supported-row validation, no-helper validation,
  `optional_helper_policy_id`, each `helper_installation_state_id`, installable/
  environment/trace identities, and rollback evidence are independently
  reviewable.

### 3.8 Payload, Documentation, UAT, and Release Proof *(-> G56R-011)*

- **AC-8.1**: The Codex payload is rebuilt from source; all ten source and payload
  TOMLs, manifests/checksums, the exactly nine-agent required plugin-managed
  destination inventory, any conditionally installed tenth helper, the universal
  core, optional-helper policy, and release policy agree without hand-editing
  generated artifacts.
- **AC-8.2**: Active Codex install/autopilot guidance explains the selected
  routes, component-qualification and integrated release-decision evidence,
  explicit global override, restart requirement,
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
  `optional_helper_policy_id`, every row's `helper_installation_state_id`,
  `release_policy_id`, `workload_population_manifest_id`,
  `canonical_rate_schedule_id`, telemetry attrition, per-row native-guardrail
  state, qualification and opportunity-cost results, rejected candidates,
  verification evidence, gaps, and review order.
- **AC-8.7**: Release evidence pins the support manifest, canonical rate
  schedule ID/hash, workload-population manifest ID/hash, telemetry-attrition
  registry, minimum/tested Codex versions, per-row capability probes,
  environment IDs, rate regimes, native-guardrail states, and tested model
  availability. Model, client, prompt, rate-card, canonical formula/alias/
  coefficient/rounding rule, workload manifest, attrition rule, entitlement,
  support manifest, installable-policy, helper-policy, helper-installation-state,
  or release-policy changes trigger the predeclared scope of requalification or
  rebenchmarking.
- **AC-8.8**: Before merge and release, deterministic documentation checks
  validate relative links, repository-local paths labeled current, fixture and
  agent counts, PRD-to-roadmap acceptance-criteria ownership, SPEC dependencies,
  current-versus-proposed path labels, named-category resolutions, canonical-row
  invariants and assignment-cohort provenance, deterministic per-row comparator
  selection, workload-stratum and long-horizon gates, telemetry-attrition rules,
  canonical-rate calculation, plan-native claim boundaries, source-versus-
  destination agent inventory, row-aware helper identity and absence semantics,
  final-static-versus-control ownership, component terminology, and the bounded
  assembled-policy claim. They reject
  absent paths described as current,
  obsolete Layer 6 shell paths, contradictory G56R-002/G56R-003 ownership,
  collapsed canonical/native/legacy accounting terms, or any undocumented
  discoverable-but-non-invocable helper state.
- **AC-8.9 — Integrated policy promotion gate**: Before release, the frozen
  component-wise assembled nine-agent `universal_core_policy_id` is evaluated
  exactly once on the untouched integrated release-confirmation corpus as one
  multi-stratum campaign after every cohort lock. In the canonical row it is
  paired with the immutable production core and must pass the superiority
  endpoint. In every other mandatory row or proven equivalence class it is
  paired with the AC-2.13 assigned comparator and must pass that row's non-
  inferiority, quality/safety, simultaneous guardrail, and qualification gates.
  The campaign uses the locked `workload_population_manifest_id`; every objective
  keeps its pre-treatment `workload_stratum_id`. In every required plan row or
  equivalence class, the confidence-powered `long_horizon_stratum_id`
  independently passes acceptance, semantic quality, paired mean and p95
  canonical resource, p95 duration, late-failure, retry, and compaction-overhead
  gates. Another stratum cannot offset failure. Long-horizon efficiency wording
  additionally requires the canonical-row `-delta_long_horizon` superiority
  result. Every row with `plan_native_guardrail_state = required` also passes its
  frozen plan-native non-inferiority gate under the explicit
  `native_allowance_noninferiority` claim boundary; an `unavailable` row receives
  only the explicit `canonical_resource_only` claim boundary.
  Spark is `not_installed` in every primary and secondary arm. An attempted
  helper resolution, spawn, or invocation is a candidate-caused hard contract
  failure under AC-2.7 with
  `A_i = 0` and retained measurable universal-core `R_i`, not a rerunnable
  invalid observation. Only independently proven harness contamination permits
  invalidation and rerun. The AC-2.17 frozen controls run as predeclared
  secondary arms on the same untouched locked objectives in the canonical row
  and every mandatory row or proven equivalence class under the frozen
  multiplicity strategy. G56R-011 compares those controls with the final frozen
  `universal_core_policy_id`, not an earlier static prototype. Control parameters
  cannot change after G56R-004; the secondary arms do not select or modify the
  frozen core or replace the primary comparison. They determine whether release
  may carry the bounded efficiency claim under AC-9.4. The candidate-versus-
  assigned-comparator primary family remains the sole promotion decision; the
  secondary control arms gate only the bounded efficiency wording under AC-9.4.
  Passing proves
  improvement over production only in the canonical row and support/non-
  regression within every other row's declared claim boundary; it does not
  prove global assembled-policy optimality. Failure reopens route, prompt,
  environment, comparator, or orchestration selection and requires a new
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
  Evidence binds `optional_helper_policy_id`, the row-specific
  `helper_installation_state_id`, and its `installed_enabled` or `not_installed`
  state. Spark results never enter the universal-core primary
  statistic.
- **AC-8.12 — Long-workflow boundary/recovery canaries**: Membership is selected
  before execution from the frozen long-horizon task/protocol definition, never
  from realized tokens, duration, turns, compactions, retries, or outcomes. The
  controlled portfolio contains at least the minimum unique-task count from the
  risk/sample rule. Each canary declares at least four required phases and its
  scripted orchestration, interruption, validation-repair, compaction-stress, or
  allowance-boundary events before treatment. Across the portfolio, at least one
  task includes a multi-agent graph, compaction crossing, interruption/resume,
  validation failure/repair, and controlled approach to a plan-specific
  allowance boundary. Active runtime, quota wait, tool wait, and human wait are
  reported separately; results are stratified by manifest row or proven
  equivalence class. This portfolio validates operability, recovery, and
  boundary behavior only; it is additional evidence and never substitutes for
  AC-2.9/AC-8.9 comparative long-horizon results.

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
- **AC-9.4**: Before cohort selection, G56R-004 freezes this consequence: if
  G56R-011 later finds under AC-8.9 that an eligible control materially dominates
  the final `universal_core_policy_id`, version 1 may still ship static defaults
  for declared operational simplicity, but release language is limited to
  measured improvement over the previous static baseline and cannot claim
  efficient, optimal, or best measured routing.
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
  implement telemetry/traces, corpus/statistics, frozen policy-control
  definitions, and allowance-boundary budgets.
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
| Policy Control Definition and Dominance Contract | AC-2.17, AC-9.2, AC-9.4 | G56R-004 | G56R-003 | P1 |
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
2. The component-wise assembled nine-agent universal core improves over the
   immutable production core in the canonical environment and clears every
   other row's assigned-comparator, treatment, safety, quality, reliability,
   and non-regression gate without pooling incompatible accounting or claiming
   complete-policy global optimality. The bounded efficiency claim additionally
   requires that no eligible frozen control materially dominate the final core
   under AC-2.17 and AC-8.9; otherwise only AC-9.4's restricted release claim is
   permitted. The powered long-horizon stratum independently clears its gates;
   long-horizon improvement wording additionally requires its own canonical-row
   superiority result.
3. A clean install verifies exactly nine plugin-managed core installable
   identities plus the core, row-aware optional-helper, helper-installation-
   state, and release-policy IDs; it verifies a conditional tenth helper identity
   only on supported rows. Environment and execution evidence separately prove
   effective speed, tools, permissions, and model resolution.
4. Source, generated payload, installed cache, guidance, tests, and UAT agree on
   the universal core and optional-helper split, workload manifest, canonical
   rate schedule, and telemetry-attrition evidence. Every mandatory manifest row
   is `supported`; any additional row has an explicit non-claiming state. A
   plan-native allowance claim is made only for rows whose required native
   guardrail passes.
5. Consumers retain a documented global compatibility override and a previous
   release rollback path.

## 9. References

- **Technical roadmap:** [codex-gpt-5-6-agent-routing-technical-roadmap.md](ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md)
- **Roadmap MOC:** [codex-gpt-5-6-agent-routing-roadmap-MOC.md](ai/specs/codex-gpt-5-6-agent-routing-roadmap-MOC.md)
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
- **Healthcare, Regulated, Clinicians, and Codex Local:** [HIPAA-eligible products and functionality](https://help.openai.com/en/articles/20001069-chatgpt-healthcare-and-regulated-workspace-functionality)
- **FedRAMP Codex authentication boundary:** [ChatGPT Enterprise and API Platform for FedRAMP](https://help.openai.com/en/articles/20001070-chatgpt-enterprise-and-api-platform-for-fedramp)
- **ChatGPT Gov environment:** [Introducing ChatGPT Gov](https://openai.com/global-affairs/introducing-chatgpt-gov/)
- **Individual-plan credits:** [Using credits for flexible usage](https://help.openai.com/en/articles/12642688-using-credits-for-flexible-usage-in-chatgpt-freegopluspro)
- **Managed-plan accounting variants:** [Flexible managed-plan pricing](https://help.openai.com/en/articles/11487671-flexible-pricing-for-chatgpt-enterprise-plans)
- **Codex native protocol/telemetry capability surface:** [App server](https://learn.chatgpt.com/docs/app-server)
- **Speed modes and Spark limits:** [Codex speed](https://learn.chatgpt.com/docs/agent-configuration/speed)
- **Long-workflow controls:** [Long-running work](https://learn.chatgpt.com/docs/long-running-work)
- **API-price diagnostic only:** [OpenAI API pricing](https://developers.openai.com/api/docs/pricing)
- **Prompt guidance:** [GPT-5.6 prompting best practices](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices)
