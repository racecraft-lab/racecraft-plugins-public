# PRD: Codex ChatGPT Subscription Agent Routing Optimization

**Status**: Active - not yet implemented
**Source**: Maintainer request plus official OpenAI documentation, `$research`,
and `$tavily-research` passes completed 2026-07-09 and revalidated 2026-07-11
**Created**: 2026-07-09
**Last updated**: 2026-07-11
**Target window**: Next SpecKit Pro minor release after the active XPLAT-009
installer/runtime surface is stable
**Legacy identifier note**: The stable `G56R` SPEC prefix originated when this
work was scoped to GPT-5.6. It is retained for traceability only and no longer
limits the model catalog or ChatGPT subscription plans in scope.

---

## 1. Problem

> "Which efficient static installation defaults should SpecKit Pro use for
> each Codex agent so ChatGPT subscription consumers complete accepted
> end-to-end workflows with the lowest measured allowance consumption that
> preserves quality, reliability, and completion time?"

SpecKit Pro currently defines ten Codex custom agents. Nine source TOMLs pin
`gpt-5.5`; the latency-first helper pins `gpt-5.3-codex-spark`. Effort is mostly
`xhigh`, with two read-only analysts at `low` and the Spark helper omitting an
effort field. The installer and structural tests also encode a mostly uniform
model policy. That policy cannot optimize across the full model catalog
available to each supported ChatGPT subscription, and the current Layer 6
Codex harness sweeps effort while holding the TOML model constant.

OpenAI positions `gpt-5.6-sol` for quality-critical work, `gpt-5.6-terra` as
the everyday balance, and `gpt-5.6-luna` for lighter or high-volume work.
SpecKit Pro consumers in scope authenticate Codex through any supported ChatGPT
subscription plan, not an API key. OpenAI documents those as different
accounting modes: ChatGPT sign-in uses subscription access and plan credits/
limits, while API-key sign-in is usage-based at standard API rates. The objective
therefore cannot be API dollars per isolated agent call.

This PRD supports any ChatGPT-authenticated subscription plan exposed by the
tested Codex client. Plan and subtier evidence is recorded when authoritative,
but missing or unresolved plan detail does not block tier-neutral token/credit
analysis. It blocks only plan-specific allowance, throughput, reset, or
availability claims. Local messages may share allowance windows with other
covered activity and may face additional limits. Model choice, context,
reasoning, tools, retrieval, and caching all affect consumption. The benchmark
therefore accounts from the initial objective through the terminal outcome,
including parent/child agents, retries, validation, compaction, escalation,
repair, steering, and abandoned work. The current published rate-limit table
includes GPT-5.5, GPT-5.4, and GPT-5.4 Mini, while Pro separately exposes
GPT-5.3-Codex-Spark as a research preview. The evaluated catalog must be
discovered from the authenticated account and current Codex client at benchmark
time rather than frozen to the models named in this document.

The requested research passes did not find a complete public benchmark that
compares the full subscription-available Codex catalog on SpecKit Pro's ten
roles. Therefore this PRD does not treat a generation, marketing tier, or current
default as a proven assignment. It defines an evidence-first promotion process
and ships only role assignments that clear a consumer-focused quality floor.

## 2. Goals & Non-goals

### 2.1 Goals

- Give every installed SpecKit Pro Codex agent an explicit, role-appropriate,
  immutable policy identity selected by measured evidence.
- Preserve consumer-visible correctness, grounding, output contracts,
  reliability, and completion time while minimizing token-derived credits per
  assigned objective under a fixed terminal policy and acceptance gate.
- Evaluate every model exposed to the declared ChatGPT subscription and tested
  Codex client, including current GPT-5.6, GPT-5.5, GPT-5.4, GPT-5.4 Mini, and
  separately accounted preview models; do not force any generation or tier
  into production when it fails the promotion bar.
- Make the model x effort x prompt x speed decision reproducible through role
  fixtures, versioned results, and a documented promotion rule.
- Keep installation predictable: role-pinned defaults, one explicit global
  compatibility override, no silent downgrade, and complete verification of
  all ten installed agents.
- Rebuild and verify the Codex payload, active guidance, and installed-cache
  evidence before release.
- Compare static role pins with an unpinned Codex-selected control and an
  explicit adaptive-policy control before claiming a static route is efficient.
- Evaluate routing and bounded prompt/context variants in explicit stages
  because model, effort, instructions, handoffs, and tool context can interact.
  Preserve the current prompt for causal model/effort attribution before prompt
  interaction and locked joint confirmation.

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
- Claiming universal model availability across accounts, operating systems,
  or Codex surfaces.
- Replacing historical model references, archived evidence, or old eval
  baselines solely to make repository-wide search results uniform.
- Claiming global optimization across unavailable, undocumented, or future
  models. Version 1 selects efficient static defaults across the full catalog
  actually exposed to the authenticated subscription and tested client;
  runtime-adaptive optimization still requires separate evidence.
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
  every model exposed to the authenticated subscription/client, supported
  effort values, a role-eligibility rationale, and a role-specific quality
  contract. The
  initial shortlist includes every eligible model; exclusion requires recorded
  incompatibility, contract failure, or predeclared dominance evidence.
- **AC-1.4**: Facts, inferences, and unverified assumptions are visibly
  separated, and no public head-to-head benchmark is claimed where none was
  located.
- **AC-1.5**: The time-boxed spike ends with a go/no-go decision and fixture
  requirements for G56R-002; it does not change installed defaults.

### 3.2 Model-Effort Benchmark and Promotion Harness *(-> G56R-002 through G56R-004)*

- **AC-2.1 — Three-stage experiment**: Stage A varies only the candidate
  agent's model or ordinary reasoning effort with its baseline prompt while
  freezing the parent, other agents, all prompts, tools/MCP/skills, repository,
  validator, truncation, context/compaction, retry, escalation, and speed.
  Stage B admits only Stage-A-shortlisted model/effort pairs and varies only the
  candidate prompt/context policy, explicitly estimating prompt-by-model
  interactions. Stage C freezes the selected model + effort + prompt + speed
  policy and evaluates it once on the locked confirmation corpus. Unpinned,
  adaptive, and Ultra comparisons are policy-level controls, never per-agent
  causal evidence.
- **AC-2.2 — Authentication and plan scope**: The harness fails closed only
  when it cannot verify ChatGPT subscription authentication. Any supported
  ChatGPT subscription plan may participate. Plan/subtier evidence is recorded
  from an authoritative field or archived entitlement record when available
  and is never inferred from capacity. Unresolved plan detail permits tier-
  neutral token/credit analysis but blocks plan-specific availability,
  allowance-window, throughput, reset, or completion-before-limit claims.
- **AC-2.3 — Complete trace**: Every assigned objective emits a parent-child
  trace through acceptance or the terminal stopping condition, including
  requested/returned model, ordinary effort, speed, input/cached-input/output
  tokens, credit-rate revision, parent attribution, context/tool volume,
  compaction, retries, repair, validation, steering, cancellation, abandonment,
  and outcome. Raw nulls are preserved and never invented.
- **AC-2.4 — Primary-endpoint completeness**: A paired objective is eligible
  for promotion analysis only when 100% of attributable model activity has
  returned-model identity, speed, input/cached-input/output token counts,
  applicable credit-rate revision, and parent-child attribution. Any missing
  required field invalidates and reruns the pair or marks it non-comparable; a
  partial total can never support promotion. Production validation belongs in
  the workflow total; benchmark-only judge/scorer consumption is reported
  separately.
- **AC-2.5 — Distinct accounting measures**: Artifacts separately report token-
  derived credits, every included-limit bucket's before/after utilization, and
  purchased-credit balance consumption. They record rate-limit ID, duration,
  reset time, and reset crossing. Reset-crossing runs remain in objective credit
  totals but not ordinary within-window throughput estimates. API dollars are a
  diagnostic only and never share a generic `cost` field.
- **AC-2.6 — Data partitions and multiplicity**: The campaign uses disjoint
  screening, selection, and locked confirmation corpora. Screening performs
  capability/contract elimination; selection ranks a frozen shortlist; final
  promotion uses the confirmation corpus exactly once under a predeclared
  hierarchical gatekeeping or family-wise error strategy. Changing a candidate,
  prompt, endpoint, margin, guardrail, weighting, or stopping rule after
  confirmation starts invalidates the confirmation run.
- **AC-2.7 — Estimand**: For randomized objective `i`, `C_i` is all attributable
  token-derived credits from objective start until acceptance or the fixed
  terminal stopping condition, and `A_i` is 1 only on acceptance. Candidate-
  caused failure, budget exhaustion, timeout, cancellation, and abandonment
  remain in `C_i` and `A_i`. Preclassified harness/infrastructure failures that
  prevent treatment delivery are excluded and rerun. The primary endpoint is
  paired mean `C_i` per assigned objective versus the immutable production
  baseline; accepted-workflow rate is a separate quality gate.
- **AC-2.8 — Promotion statistic**: Promotion requires the upper one-sided 95%
  confidence bound for the task-level paired mean `C_i` difference to be below
  predeclared `-delta`. The confirmation result—not screening or selection—owns
  this decision. Critical safety/grounding/contract/mutation gates and accepted-
  workflow non-inferiority must pass first.
- **AC-2.9 — Statistical unit and weighting**: A unique workflow objective is
  the experimental unit; repeats are clustered within objective and inference
  is paired at task level using a predeclared task-cluster bootstrap or
  hierarchical model. Sample sizes count unique tasks. Production-justified
  stratum weights are frozen before evaluation; equal-weight sensitivity is
  secondary. Cache crossover isolates arms so one cannot warm another's local
  or provider cache.
- **AC-2.10 — Guardrail registry**: Before candidate evaluation, every p95-
  credit, p95-duration, late-failure, retry, steering, and incomplete-workflow
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
- **AC-2.12 — Speed control**: V1 freezes Standard speed for every attribution,
  confirmation, installation, and release claim. Any future speed optimization
  must treat speed as an explicit policy dimension and promote model + effort +
  prompt + speed together with the correct multiplier.
- **AC-2.13 — Immutable baseline**: Before screening, the production comparator
  is pinned by repository commit, plugin version, ten complete agent policy IDs,
  Codex version, returned models, Standard speed, rate-card revision, tool
  configuration, and corpus snapshot. A production change creates a versioned
  new baseline and requires confirmation to be rebased and rerun.
- **AC-2.14 — Campaign budget**: The campaign fixes maximum total credits,
  wall-clock time, candidates reaching confirmation, capability/contract
  screening, and futility/dominance elimination thresholds before results are
  observed. A fixed racing/successive-halving method may be used; thresholds
  cannot change after viewing outcomes.
- **AC-2.15 — Evidence governance**: Evaluation uses licensed, synthetic,
  public, or explicitly authorized repositories in ephemeral clean worktrees,
  with no production credentials. Candidate context is isolated. Raw private
  traces have defined retention; public/private artifacts are separated and
  secrets/content/path redaction runs before publication. Account identity uses
  an opaque alias or keyed HMAC.
- **AC-2.16 — Replay artifact**: The versioned artifact preserves raw telemetry,
  formulas, nulls, rates, corpus partition, task/stratum IDs, weights, campaign
  decisions, policy hashes, guardrail registry, confirmation lock, failures,
  and selected/rejected routes.
- **AC-2.17 — Static-control consequence**: A static policy may be called
  efficient only if it passes against production and is not materially dominated
  by a tested unpinned or adaptive control on quality, reliability, credits, and
  duration. If a non-shipped control dominates, v1 may still ship static for
  declared operational simplicity, but messaging is limited to improvement over
  the previous static baseline and cannot claim best measured efficiency.
- **AC-2.18 — Spark**: Spark remains the unchanged helper route while its
  separate demand-sensitive limit lacks a common attributable credit measure.
  Non-Spark helper results are exploratory and cannot displace Spark under the
  shared endpoint. Any integrated workflow containing Spark is excluded from a
  complete shared-credit claim or reported under a separately predeclared
  helper endpoint; Spark consumption is never silently omitted.

### 3.3 Subscription-aware Installer Defaults and Explicit Override *(-> G56R-006)*

- **AC-3.1**: A default install preserves each validated immutable agent policy,
  not only its model and effort. `agent_policy_id` covers requested/resolved
  model, ordinary effort, Standard speed, prompt and instruction/skill hashes,
  tool/MCP schema hash, context/truncation/compaction hash, retry/escalation
  hash, and tested Codex version.
- **AC-3.2**: The global model override remains an explicit compatibility
  action. Before any mutation, the installer validates all ten resulting model
  x effort x speed combinations. If any retained effort is incompatible, the
  entire override fails unless the user also supplies a validated effort policy;
  silent effort coercion is prohibited.
- **AC-3.3**: The installer distinguishes known unsupported from local catalog
  evidence (atomic abort), known unavailable from authoritative entitlement
  evidence (atomic abort), and availability unresolved when no authoritative
  preflight exists. Unresolved availability is disclosed before mutation and
  requires explicit acknowledgement plus post-install verification. There is
  no silent downgrade or partial install.
- **AC-3.4**: Source and destination inventory agree on all ten agent TOMLs,
  including `uat-runbook-author.toml`; unrelated user agents are preserved.
- **AC-3.5**: Install output reports the complete effective policy matrix,
  destination, plan-evidence state, override state, copied files, post-install
  returned-model verification, result, and restart requirement.
- **AC-3.6**: Implementation uses the post-XPLAT-009 Python runner/install path
  and does not restore a deleted active Bash helper.

### 3.4 Quality-critical Executor Routing *(-> G56R-007)*

- **AC-4.1**: `phase-executor`, `implement-executor`, and `analyze-executor`
  start with Sol and Terra hypotheses but screen every eligible model available
  to the authenticated subscription, including the GPT-5.5 baseline and GPT-5.4
  family, through the AC-2.11 effort search.
- **AC-4.2**: Each committed complete agent policy clears the G56R-003 promotion
  rule on role-specific planning, TDD implementation, and analyze/remediation
  fixtures.
- **AC-4.3**: Agent sandbox, TDD, grounding, artifact, and remediation contracts
  remain hard invariants across Stage A attribution, Stage B prompt interaction,
  and Stage C locked confirmation.
- **AC-4.4**: Each role follows AC-2.1 exactly: unchanged-prompt model/effort
  attribution first, shortlisted prompt interactions second, then one frozen
  joint policy confirmation.
- **AC-4.5**: Cohort-specific source, install, validation, and rollback evidence
  makes the route independently reviewable.

### 3.5 Structured-work Agent Routing *(-> G56R-008)*

- **AC-5.1**: `checklist-executor` and `uat-runbook-author`
  start with Terra as a hypothesis but screen every eligible model available to
  the authenticated subscription, including GPT-5.4 Mini for bounded structured
  work, through the AC-2.11 effort search.
- **AC-5.2**: Checklist remediation remains complete at every severity and UAT
  runbooks remain executable, plain-English, non-circular, and traceable to
  acceptance criteria.
- **AC-5.3**: The selected routes clear the shared promotion rule and preserve
  workspace-write boundaries and fail-open/fail-closed behavior specific to
  each role.
- **AC-5.4**: The cohort follows Stage A frozen-prompt attribution, Stage B
  shortlisted prompt interaction, and Stage C locked confirmation; install and
  rollback evidence records the complete selected policy identity.

### 3.6 Read-only Reasoning Agent Routing *(-> G56R-009)*

- **AC-6.1**: `clarify-executor`, `domain-researcher`, `codebase-analyst`, and
  `spec-context-analyst` start with Terra as a hypothesis but screen every
  eligible subscription-available model; lighter models are retained for
  bounded scans only when their grounding and output contracts pass.
- **AC-6.2**: Each role applies AC-2.11 to every candidate model: start at the
  documented default, ascend when needed to find a stable pass, then descend
  and retest the failing boundary to select the lowest stable ordinary effort.
- **AC-6.3**: All outputs remain grounded in their assigned evidence domain,
  preserve citations/file locators, and perform no writes.
- **AC-6.4**: The complete static agent policy that passes the shared staged
  promotion rule is committed per role; one cohort model is not forced across
  all four roles.
- **AC-6.5**: Joint prompt/context tuning, install proof, and rollback evidence
  obey the same cohort contract as G56R-007.

### 3.7 Latency-first Helper Routing *(-> G56R-010)*

- **AC-7.1**: `autopilot-fast-helper` retains its current Spark policy while a
  common attributable measure is unavailable. Luna, GPT-5.4 Mini, GPT-5.4,
  Terra, and other eligible subscription models remain exploratory challengers.
- **AC-7.2**: The helper remains read-only, advisory, bounded to compression,
  triage, and query drafting, and never performs SpecKit reasoning or mutation.
- **AC-7.3**: Spark cannot be replaced under the shared credit endpoint until
  its consumption is comparable. A separately predeclared helper endpoint may
  justify a future change but must not claim shared-allowance superiority;
  omitted effort never selects an unmeasured default.
- **AC-7.4**: Autopilot continues correctly when the helper is unavailable, and
  evidence wins over a requirement to use Luna.
- **AC-7.5**: Source, install, validation, complete policy identity, and rollback
  evidence is independently reviewable.

### 3.8 Payload, Documentation, UAT, and Release Proof *(-> G56R-011)*

- **AC-8.1**: The Codex payload is rebuilt from source; source TOMLs, generated
  payloads, manifests/checksums, install inventory, and complete expected policy
  matrix agree without hand-editing generated artifacts.
- **AC-8.2**: Active Codex install/autopilot guidance explains the selected
  routes, promotion evidence, explicit global override, restart requirement,
  and non-universal availability boundary without rewriting historical records.
- **AC-8.3**: Structural, installer, benchmark-replay, payload, installed-cache,
  default-suite, and active-path gates pass on the final source tree and verify
  complete policy IDs across source, trace, payload, install, and canary.
- **AC-8.4**: A live ChatGPT subscription account completes at least one installed
  representative workflow per routed cohort as an installation smoke gate.
  Separately, the controlled canary portfolio contains at least the minimum
  unique-task count from the risk/sample rule. Every long-workflow canary has at
  least four named phases and twelve model turns and meets a predeclared minimum
  active-agent duration or credit budget. Across the portfolio, at least one
  task includes each of: a multi-agent graph, compaction crossing, interruption/
  resume, validation failure/repair, and controlled approach to a predeclared
  allowance-boundary threshold. Active runtime, quota wait, tool wait, and human
  wait are recorded separately.
- **AC-8.5**: Release messaging makes only progressively proven claims and
  includes rollback through an explicit global override or previous plugin
  release.
- **AC-8.6**: The PR packet lists the final ten-agent policy matrix, rejected
  candidates, verification evidence, known availability gaps, and review order.
- **AC-8.7**: Release evidence pins minimum/tested Codex versions, capability
  probes, plan evidence state, client configuration, rate-card revision, and
  tested model availability. Model, client, prompt, rate-card, entitlement, or
  agent-policy
  changes trigger rebenchmarking; production canaries watch accepted-workflow
  rate, p95 allowance use/duration, escalation, and late failure.
- **AC-8.8**: Before merge and release, deterministic documentation checks
  validate relative links, PRD-to-roadmap acceptance-criteria coverage, SPEC
  dependencies/anchors, and terminology separation for token-derived credits,
  included-limit utilization, purchased-credit consumption, and API-dollar
  diagnostics.
- **AC-8.9 — Integrated policy gate**: Before release, the assembled installed
  ten-agent policy is compared with the immutable production policy on a fresh
  locked confirmation corpus. It independently passes all safety/quality gates,
  accepted-workflow non-inferiority, the primary credit endpoint, and every
  guardrail. Failure reopens route, prompt, speed, or orchestration selection;
  cohort success is necessary but insufficient.
- **AC-8.10 — Plan-domain claims**: The default policy uses the model/capability
  intersection available to all ChatGPT subscription plans supported by the
  tested Codex release for required agents. The optional Spark helper may remain
  plan-specific only because autopilot has a verified no-helper path and reports
  unavailability explicitly. Tier-neutral credit promotion may use any
  authenticated plan. Plan-specific availability and operational claims require
  validation on each named plan; unresolved plan evidence cannot support them.

### 3.9 Workflow Budget and Adaptive-policy Contract *(-> G56R-004, G56R-005, G56R-011)*

- **AC-9.1**: The evaluation harness declares maximum campaign and per-objective
  credits/time, retries, subagent threads/depth, context growth, and redundant
  work. These are harness controls, not new production scheduler behavior.
- **AC-9.2**: Adaptive-policy fixtures define observable escalation signals
  (for example repeated validation failure, high ambiguity, or cross-cutting
  dependency impact), catalog-derived escalation/de-escalation paths based on
  measured quality and allowance use, and cancellation of redundant child work.
- **AC-9.3**: Harness simulations classify limit-near/exhausted, reset crossing,
  timeout, continue, and cancel outcomes under a fixed terminal policy. Product
  checkpoint/resume features are a separate follow-up and do not block static
  installer work.
- **AC-9.4**: Version 1 may ship static defaults for operational simplicity only
  under AC-2.17. If a control dominates, release language is limited to measured
  improvement over the previous static baseline and cannot claim optimal or
  best measured efficiency.

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
- G56R-006 and later implementation must ground on the post-XPLAT-009 active
  installer/runtime surface; no deleted Bash helper may be restored.
- Python 3.11+ standard library remains the installed runtime substrate; this
  PRD adds no runtime dependency.
- Agent TOMLs remain the role-policy source of truth. Generated payloads are
  rebuilt from source, never edited directly.
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
  contract and reruns the forward size estimator when it becomes available.

## 6. Open Questions

- **OQ-1 (G56R-001):** Which models and efforts does each supported ChatGPT
  subscription plan expose through the installed Codex client?
  Recommendation: snapshot the live catalog, probe every entry, and abstain
  from unverified routes.
- **OQ-1A (G56R-001/G56R-002):** Which Codex/account interface authoritatively
  exposes plan and subtier? Recommendation: record it when available; otherwise
  continue tier-neutral evaluation and block only plan-specific claims.
- **OQ-2 (G56R-002):** Which native app-server/client fields expose observed
  credits, token activity, account type/plan, and rate-limit buckets in the
  tested Codex version? Recommendation: capability-probe every field, preserve
  nulls, and derive estimates only with labeled/versioned formulas. Do not add a
  consumer-facing cache-write category unless native subscription telemetry
  exposes it.
- **OQ-3 (G56R-006):** Which Python helper owns agent installation after
  XPLAT-009 merges? Recommendation: bind to the live authoritative registry at
  scaffold time instead of naming a removed compatibility script.
- **OQ-4 (G56R-007 through G56R-010):** Which catalog challengers survive
  the research spike's availability and contract screen? Recommendation: keep
  the approved shortlist narrow and expand only unstable comparisons.
- **OQ-5 (G56R-001/G56R-002):** Which catalog entries are ineligible for a role
  because of missing custom-agent/tool/effort support? Recommendation: exclude
  only after a recorded capability or contract failure; GPT-5.4 Mini is a
  required bounded-work candidate when exposed.
- **OQ-6 (G56R-002):** How can Spark's separate, demand-sensitive research
  preview limit be compared with shared allowance? Recommendation: retain Spark
  unchanged and report Spark on a separate scorecard until an attributable
  common measure exists.

## 7. SPEC Catalog Crosswalk

| Feature (§3) | Acceptance Criteria | SPEC | Depends on | Priority |
|---|---|---|---|---|
| Research Baseline and Candidate Matrix | AC-1.* | G56R-001 | - | P1 |
| Authentication, Telemetry, and Trace Schema | AC-2.2 through AC-2.5, AC-2.15, AC-2.16 | G56R-002 | G56R-001 | P1 |
| Corpus Runner, Acceptance Scoring, and Statistics | AC-2.1, AC-2.6 through AC-2.14 | G56R-003 | G56R-002 | P1 |
| Static/Unpinned/Adaptive Policy Comparison | AC-2.17, AC-2.18, AC-9.2, AC-9.4 | G56R-004 | G56R-003 | P1 |
| Harness Budgets and Boundary Simulation | AC-9.1, AC-9.3 | G56R-005 | G56R-004 | P1 |
| Subscription-aware Installer Defaults and Explicit Override | AC-3.* | G56R-006 | G56R-005; XPLAT-009 runtime stable | P1 |
| Quality-critical Executor Routing | AC-4.* | G56R-007 | G56R-006 | P1 |
| Structured-work Agent Routing | AC-5.* | G56R-008 | G56R-006 | P1 |
| Read-only Reasoning Agent Routing | AC-6.* | G56R-009 | G56R-006 | P1 |
| Latency-first Helper Routing | AC-7.* | G56R-010 | G56R-006 | P1 |
| Payload, Documentation, UAT, and Release Proof | AC-8.* | G56R-011 | G56R-007 through G56R-010 | P1 |

## 8. Success Criteria

1. All acceptance criteria are traceable through G56R-001 through G56R-011;
   the cross-cutting workflow-budget contract is implemented in the shared
   harness and release-proof specs.
2. Every shipped agent policy clears the locked-confirmation primary endpoint,
   multiplicity strategy, quality/safety gates, accepted-workflow non-
   inferiority, and all predeclared guardrails at task-level inference.
3. A clean install verifies all ten complete policy identities with no silent
   model, effort, prompt, speed, tool, context, or retry-policy fallback.
4. Source, generated Codex payload, installed cache, guidance, tests, and UAT
   evidence agree on the final policy matrix, and the assembled ten-agent
   policy independently passes its joint confirmation gate.
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
- **Model pages:** [Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol), [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra), [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
- **Codex authentication:** [ChatGPT subscription access versus API-key usage](https://learn.chatgpt.com/docs/auth)
- **Codex plans, credits, and limits:** [Codex pricing](https://learn.chatgpt.com/docs/pricing)
- **Codex native protocol/telemetry capability surface:** [App server](https://learn.chatgpt.com/docs/app-server)
- **Speed modes and Spark limits:** [Codex speed](https://learn.chatgpt.com/docs/agent-configuration/speed)
- **Long-workflow controls:** [Long-running work](https://learn.chatgpt.com/docs/long-running-work)
- **API-price diagnostic only:** [OpenAI API pricing](https://developers.openai.com/api/docs/pricing)
- **Prompt guidance:** [GPT-5.6 prompting best practices](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices)
