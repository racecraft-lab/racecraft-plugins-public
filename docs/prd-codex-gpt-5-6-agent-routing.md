# PRD: Codex ChatGPT Pro Agent Routing Optimization

**Status**: Active - not yet implemented
**Source**: Maintainer request plus official OpenAI documentation, `$research`,
and `$tavily-research` passes completed 2026-07-09
**Created**: 2026-07-09
**Last updated**: 2026-07-11
**Target window**: Next SpecKit Pro minor release after the active XPLAT-009
installer/runtime surface is stable

---

## 1. Problem

> "Which efficient static installation defaults should SpecKit Pro use for
> each Codex agent so ChatGPT Pro consumers complete accepted end-to-end
> workflows with the lowest measured allowance consumption that preserves
> quality, reliability, and completion time?"

SpecKit Pro currently defines ten Codex custom agents. Nine source TOMLs pin
`gpt-5.5`; the latency-first helper pins `gpt-5.3-codex-spark`. Effort is mostly
`xhigh`, with two read-only analysts at `low` and the Spark helper omitting an
effort field. The installer and structural tests also encode a mostly uniform
model policy. That policy cannot optimize across the full model catalog
available to ChatGPT Pro, and the current Layer 6 Codex harness
sweeps effort while holding the TOML model constant.

OpenAI positions `gpt-5.6-sol` for quality-critical work, `gpt-5.6-terra` as
the everyday balance, and `gpt-5.6-luna` for lighter or high-volume work.
SpecKit Pro consumers in scope authenticate Codex through a ChatGPT Pro
subscription, not an API key. OpenAI documents those as different accounting
modes: ChatGPT sign-in uses subscription access and plan credits/limits, while
API-key sign-in is usage-based at standard API rates. The production objective
therefore cannot be API dollars per isolated agent call.

This PRD targets both declared Pro tiers (`5x` and `20x`) but requires every
benchmark and release claim to name exactly one tier. Local messages share a
five-hour allowance window with other covered activity and may also face weekly
limits. Model choice, context, reasoning, tools, retrieval, and caching all
affect consumption. The benchmark must therefore account from the initial user
objective through the final accepted artifact, including parent and child
agents, retries, validation, compaction, escalation, repair, steering, and
abandoned work. The current published Pro rate-limit table also includes
GPT-5.5, GPT-5.4, and GPT-5.4 Mini, while Pro separately exposes
GPT-5.3-Codex-Spark as a research preview. The evaluated catalog must be
discovered from the declared Pro account and current Codex client at benchmark
time rather than frozen to the models named in this document.

The requested research passes did not find a complete public benchmark that
compares the full Pro-available Codex catalog on SpecKit Pro's ten roles.
Therefore this PRD does not treat a generation, marketing tier, or current
default as a proven assignment. It defines an evidence-first promotion process
and ships only role assignments that clear a consumer-focused quality floor.

## 2. Goals & Non-goals

### 2.1 Goals

- Give every installed SpecKit Pro Codex agent an explicit, role-appropriate
  model and reasoning-effort default selected by measured evidence.
- Preserve consumer-visible correctness, grounding, output contracts,
  reliability, and completion time while minimizing observed or estimated Pro
  allowance consumption per accepted end-to-end workflow.
- Evaluate every model exposed to the declared ChatGPT Pro tier and tested
  Codex client, including current GPT-5.6, GPT-5.5, GPT-5.4, GPT-5.4 Mini, and
  separately accounted preview models; do not force any generation or tier
  into production when it fails the promotion bar.
- Make the model x effort decision reproducible through role fixtures,
  versioned results, and a documented promotion rule.
- Keep installation predictable: role-pinned defaults, one explicit global
  compatibility override, no silent downgrade, and complete verification of
  all ten installed agents.
- Rebuild and verify the Codex payload, active guidance, and installed-cache
  evidence before release.
- Compare static role pins with an unpinned Codex-selected control and an
  explicit adaptive-policy control before claiming a static route is efficient.
- Jointly evaluate routing and bounded prompt/context variants because model,
  effort, instructions, handoffs, and tool context can interact. Preserve the
  current prompt as a control rather than deferring prompt tuning until after a
  route is selected.

### 2.2 Non-goals (out of scope)

- Changing Claude agent models, Claude commands, or Claude marketplace
  behavior.
- Adopting GPT-5.6 Pro mode, persisted reasoning, Programmatic Tool Calling,
  explicit prompt caching, or the Responses API multi-agent beta.
- Unbounded or aesthetic rewriting of every agent prompt. Prompt tuning is in
  scope when a variant targets measured instruction, handoff, tool-schema,
  duplicated-context, or compaction overhead and is evaluated alongside route
  candidates against an unchanged-prompt control.
- Offering quality/balanced/economy install profiles or per-agent overrides in
  v1. The existing one-model compatibility override remains the KISS escape
  hatch.
- Claiming universal model availability across accounts, operating systems,
  or Codex surfaces.
- Replacing historical model references, archived evidence, or old eval
  baselines solely to make repository-wide search results uniform.
- Claiming global optimization across unavailable, undocumented, or future
  models. Version 1 selects efficient static defaults across the full catalog
  actually exposed to the declared Pro tier and tested client; runtime-adaptive
  optimization still requires separate evidence.
- Treating GPT-5.6 Pro mode as the same concept as the consumer's ChatGPT Pro
  subscription. The former remains out of scope; the latter defines the
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
  every model exposed to the declared Pro tier/client, supported effort values,
  a role-eligibility rationale, and a role-specific quality contract. The
  initial shortlist includes every eligible model; exclusion requires recorded
  incompatibility, contract failure, or predeclared dominance evidence.
- **AC-1.4**: Facts, inferences, and unverified assumptions are visibly
  separated, and no public head-to-head benchmark is claimed where none was
  located.
- **AC-1.5**: The time-boxed spike ends with a go/no-go decision and fixture
  requirements for G56R-002; it does not change installed defaults.

### 3.2 Model-Effort Benchmark and Promotion Harness *(-> G56R-002 through G56R-004)*

- **AC-2.1**: The Codex efficiency harness can run an explicit
  `model x model_reasoning_effort x agent` configuration instead of holding the
  TOML model constant. It evaluates static pins, an unpinned Codex-selected
  control, and an explicit adaptive-policy control on end-to-end workflows.
  Static per-agent attribution and policy-level comparison are distinct modes:
  unpinned/adaptive results may compare whole policies but may not be attributed
  to one agent.
- **AC-2.2**: The harness fails closed unless native account evidence reports
  ChatGPT authentication and `planType == "pro"`. Pro 5x/20x is recorded only
  from authoritative machine-readable entitlement data or archived account
  entitlement evidence with source, timestamp, and hash. It is never inferred
  from observed capacity. Tier-specific conclusions fail closed when that
  evidence is unavailable; tier-neutral token/credit analysis may continue only
  with `pro_tier = unresolved`. Runs also record an opaque run-local account
  alias, Codex version/configuration, speed mode, workload snapshot, cache state,
  and before/after quota windows under dedicated or no-concurrent usage.
- **AC-2.3**: Every run emits a parent-child workflow trace from initial
  objective to final acceptance: workflow/turn/thread/agent identifiers,
  requested and returned model/effort, raw native token fields, start/end
  context, tool-result volume when measurable, compactions, spawn count/depth,
  retries/escalations, validation, steering, checkpoints, abandonment, and
  final acceptance. Missing native fields remain null and are never invented.
- **AC-2.4**: Telemetry separates three non-interchangeable measures:
  `token_derived_credits`, included-limit utilization for every applicable
  `rate_limit_id` (before/after used percent, window duration, reset time), and
  purchased-credit balance consumption (before/after when exposed). It records
  `crossed_reset_boundary`; reset-crossing runs are excluded from within-window
  throughput inference but retained in total credits-to-acceptance. Derived p50,
  p95, duration, cache, retry/rework, compaction, and subagent fields remain
  labeled/versioned. API dollars are diagnostic only and never share a generic
  `cost` field with these measures.
- **AC-2.5**: Deterministic contract, grounding/evidence, safety, and mutation
  boundaries are hard gates with zero critical failures. Each semantic-quality
  dimension has an absolute floor and a predeclared non-inferiority margin;
  confidence or bootstrap bounds must clear that margin. Blinded scoring adds
  random human audits, disputed-case review, and inter-rater agreement.
- **AC-2.6**: Evaluation uses paired candidates on identical clean repository
  snapshots, randomized run order, controlled warm/cold cache states, and a
  held-out corpus stratified by repository/task size, ambiguity, language,
  tool topology, compaction crossing, single/multi-agent work, interruption,
  resume, and recoverable/unrecoverable failure. Pilot repeats may start at
  three, but final sample sizes follow a predeclared confidence rule. For
  per-agent attribution, the parent route, every non-candidate agent route,
  prompts, tools/MCP/skills, repository snapshot, validation/acceptance policy,
  tool-result truncation, context/compaction controls, retries, and escalation
  policy are frozen; only that agent's model or effort varies.
- **AC-2.7**: The predeclared primary endpoint is paired mean total
  `token_derived_credits_to_acceptance` relative to the current production
  routing policy. It charges all parent/child work, retries, failed attempts,
  cancellations, abandoned branches, validation, repair, and compaction from
  objective start through acceptance; unsuccessful workflows retain their full
  consumption and receive the predeclared failure handling rule rather than
  disappearing from the denominator. Promote only when the upper one-sided 95%
  confidence bound for the paired mean difference is below `-delta`, where
  `delta` is a predeclared minimum practically meaningful improvement. Accepted-
  workflow rate must clear its non-inferiority gate; p95 credit consumption,
  p95 duration, late failure, retries, and steering are mandatory guardrails.
  Included-limit utilization and workflows per five-hour window are secondary
  user-facing outcomes, not alternative promotion endpoints.
- **AC-2.8**: Effort tuning uses progressive descent through every supported
  lower effort while gates pass. After the first failing level is retested with
  the predeclared boundary-validation sample rule, promotion selects the lowest
  stable passing level. `max` is tested only for unresolved quality-first
  failure. Capability probes, rather than assumed effort mappings, control the
  tested matrix.
- **AC-2.9**: A versioned, replayable artifact preserves raw telemetry,
  formulas, source-field definitions (including whether reasoning is included
  in output tokens), null behavior, rate-card revision, full traces, candidates,
  failures, selected/rejected policies, and promotion rationale.
  Public artifacts use an opaque random benchmark-account alias or keyed HMAC
  with a private rotating key; they redact email, raw account/workspace IDs,
  quota/purchased-credit balances, and identifying private repository paths.
- **AC-2.10**: The candidate matrix includes a prompt/context dimension. For
  each role it compares the unchanged prompt with bounded variants that reduce
  duplicated instructions, oversized handoffs, repeated repository context,
  unnecessary tool schemas/output, or post-compaction rereading. The harness
  records prompt/configuration hashes, instruction and handoff tokens, stable-
  prefix size, tool-context volume, and prompt-by-model interaction effects.
  Promotion selects the passing route + effort + prompt policy as a unit; a
  prompt variant is never generalized to other models or roles without data.

### 3.3 Tier-aware Installer Defaults and Explicit Override *(-> G56R-006)*

- **AC-3.1**: A default install preserves each bundled agent TOML's validated
  role-specific model and effort instead of rewriting every non-helper agent to
  one default model.
- **AC-3.2**: The existing single global model override remains available as an
  explicit compatibility action and deliberately replaces all routed agent
  models only when the consumer requests it.
- **AC-3.3**: The installer never silently downgrades. Unsupported or
  unavailable requested models produce a clear, actionable report without a
  partial install or mutation of the bundled source templates.
- **AC-3.4**: Source and destination inventory agree on all ten agent TOMLs,
  including `uat-runbook-author.toml`; unrelated user agents are preserved.
- **AC-3.5**: Install output reports the effective model/effort matrix, the
  destination, override state, copied files, verification result, and restart
  requirement.
- **AC-3.6**: Implementation uses the post-XPLAT-009 Python runner/install path
  and does not restore a deleted active Bash helper.

### 3.4 Quality-critical Executor Routing *(-> G56R-007)*

- **AC-4.1**: `phase-executor`, `implement-executor`, and `analyze-executor`
  start with Sol and Terra hypotheses but screen every eligible Pro-available
  model, including the GPT-5.5 baseline and GPT-5.4 family, through progressive
  effort descent. `max` is considered only after a measured quality failure.
- **AC-4.2**: Each committed model/effort clears the G56R-003 promotion rule on
  role-specific planning, TDD implementation, and analyze/remediation fixtures.
- **AC-4.3**: Agent sandbox, TDD, grounding, artifact, and remediation contracts
  remain hard invariants while route + effort + bounded prompt variants are
  evaluated jointly.
- **AC-4.4**: Each role includes the unchanged prompt as a control and tests
  targeted prompt/context variants in the same paired matrix. The committed
  combination must clear the shared end-to-end promotion rule.
- **AC-4.5**: Cohort-specific source, install, validation, and rollback evidence
  makes the route independently reviewable.

### 3.5 Structured-work Agent Routing *(-> G56R-008)*

- **AC-5.1**: `checklist-executor` and `uat-runbook-author`
  start with Terra as a hypothesis but screen every eligible Pro-available
  model, including GPT-5.4 Mini for bounded structured work, through
  progressively lower efforts.
- **AC-5.2**: Checklist remediation remains complete at every severity and UAT
  runbooks remain executable, plain-English, non-circular, and traceable to
  acceptance criteria.
- **AC-5.3**: The selected routes clear the shared promotion rule and preserve
  workspace-write boundaries and fail-open/fail-closed behavior specific to
  each role.
- **AC-5.4**: Prompt/context variants are evaluated jointly with model and
  effort under the same control and promotion contract as G56R-007; cohort-
  specific install and rollback evidence records the selected combination.

### 3.6 Read-only Reasoning Agent Routing *(-> G56R-009)*

- **AC-6.1**: `clarify-executor`, `domain-researcher`, `codebase-analyst`, and
  `spec-context-analyst` start with Terra as a hypothesis but screen every
  eligible Pro-available model; lighter models are retained for bounded scans
  only when their grounding and output contracts pass.
- **AC-6.2**: Each role progressively descends from its current effort through
  supported lower efforts until a quality boundary is found, without relying
  on any model's omitted/default effort.
- **AC-6.3**: All outputs remain grounded in their assigned evidence domain,
  preserve citations/file locators, and perform no writes.
- **AC-6.4**: The lowest-allowance passing static route is committed per agent;
  one cohort model is not forced across all four roles.
- **AC-6.5**: Joint prompt/context tuning, install proof, and rollback evidence
  obey the same cohort contract as G56R-007.

### 3.7 Latency-first Helper Routing *(-> G56R-010)*

- **AC-7.1**: `autopilot-fast-helper` screens every eligible Pro-available
  model, explicitly including Luna, GPT-5.4 Mini, GPT-5.4, Terra, its current
  Spark behavior, and any newly exposed bounded-work model. Spark remains on a
  separate quota scorecard until a common attributable measure exists.
- **AC-7.2**: The helper remains read-only, advisory, bounded to compression,
  triage, and query drafting, and never performs SpecKit reasoning or mutation.
- **AC-7.3**: The committed route clears the shared end-to-end promotion rule
  and improves or preserves latency and allowance consumption without causing
  downstream rework; omitted effort must not accidentally select an unmeasured
  model default.
- **AC-7.4**: Autopilot continues correctly when the helper is unavailable, and
  evidence wins over a requirement to use Luna.
- **AC-7.5**: Source, install, validation, prompt-cleanup, and rollback evidence
  is independently reviewable.

### 3.8 Payload, Documentation, UAT, and Release Proof *(-> G56R-011)*

- **AC-8.1**: The Codex payload is rebuilt from source; source TOMLs, generated
  payloads, manifests/checksums, install inventory, and expected model/effort
  matrix agree without hand-editing generated artifacts.
- **AC-8.2**: Active Codex install/autopilot guidance explains the selected
  routes, promotion evidence, explicit global override, restart requirement,
  and non-universal availability boundary without rewriting historical records.
- **AC-8.3**: Structural, installer, benchmark-replay, payload, installed-cache,
  default-suite, and active-path gates pass on the final source tree.
- **AC-8.4**: A live entitled Codex account completes at least one installed
  representative workflow per routed cohort as an installation smoke gate.
  Separately, a controlled canary suite completes multiple held-out,
  end-to-end long workflows on the declared ChatGPT Pro tier and records the
  full AC-2 trace and scorecard.
- **AC-8.5**: Release messaging makes only progressively proven claims and
  includes rollback through an explicit global override or previous plugin
  release.
- **AC-8.6**: The PR packet lists the final ten-agent matrix, rejected
  candidates, verification evidence, known availability gaps, and review order.
- **AC-8.7**: Release evidence pins minimum/tested Codex versions, capability
  probes, Pro tier, client configuration, rate-card revision, and tested model
  availability. Model, client, prompt, rate-card, entitlement, or agent-policy
  changes trigger rebenchmarking; production canaries watch accepted-workflow
  rate, p95 allowance use/duration, escalation, and late failure.
- **AC-8.8**: Before merge and release, deterministic documentation checks
  validate relative links, PRD-to-roadmap acceptance-criteria coverage, SPEC
  dependencies/anchors, and terminology separation for token-derived credits,
  included-limit utilization, purchased-credit consumption, and API-dollar
  diagnostics.

### 3.9 Workflow Budget and Adaptive-policy Contract *(-> G56R-004, G56R-005, G56R-011)*

- **AC-9.1**: The evaluation contract declares maximum estimated credits per
  phase, retries, subagent threads/depth, context growth, and redundant work.
- **AC-9.2**: Adaptive-policy fixtures define observable escalation signals
  (for example repeated validation failure, high ambiguity, or cross-cutting
  dependency impact), catalog-derived escalation/de-escalation paths based on
  measured quality and allowance use, and cancellation of redundant child work.
- **AC-9.3**: Limit-near and limit-exhausted behavior is explicit: checkpoint,
  pause/resume across reset, continue, or cancel decisions preserve a durable
  objective, verifiable stopping condition, validation loop, and progress log.
- **AC-9.4**: Version 1 may still ship static defaults, but its release claim is
  limited to efficient static defaults across the capability-probed
  Pro-available catalog unless the adaptive policy independently clears all
  promotion gates.

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
- Benchmark accounts must be ChatGPT-authenticated Pro accounts. API-key runs
  are rejected as non-comparable production evidence.
- Shared-account activity invalidates allowance-delta attribution unless the
  run is isolated and the before/after quota state is captured.
- Release-please owns version changes; implementation does not manually bump
  plugin versions.
- Every implementation slice stays within the repository reviewability
  contract and reruns the forward size estimator when it becomes available.

## 6. Open Questions

- **OQ-1 (G56R-001):** Which models and efforts does the declared
  Pro 5x or Pro 20x release-test account expose through the installed Codex
  client?
  Recommendation: snapshot the live catalog, probe every entry, and abstain
  from unverified routes.
- **OQ-1A (G56R-001/G56R-002):** Which supported Codex or account interface
  authoritatively exposes Pro 5x versus Pro 20x? Recommendation: require a
  machine-readable entitlement field or archived account entitlement evidence;
  leave the tier unresolved and block tier-specific claims until available.
- **OQ-2 (G56R-002):** Which native app-server/client fields expose observed
  credits, token activity, account type/plan, and rate-limit buckets in the
  tested Codex version? Recommendation: capability-probe every field, preserve
  nulls, and derive estimates only with labeled/versioned formulas. Do not add a
  consumer-facing cache-write category unless native Pro telemetry exposes it.
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
  preview limit be compared with shared Pro allowance? Recommendation: report
  Spark on a separate scorecard until an attributable common measure exists.

## 7. SPEC Catalog Crosswalk

| Feature (§3) | Acceptance Criteria | SPEC | Depends on | Priority |
|---|---|---|---|---|
| Research Baseline and Candidate Matrix | AC-1.* | G56R-001 | - | P1 |
| Authentication, Telemetry, and Trace Schema | AC-2.2 through AC-2.4, AC-2.9 | G56R-002 | G56R-001 | P1 |
| Corpus Runner, Acceptance Scoring, and Statistics | AC-2.5 through AC-2.8 | G56R-003 | G56R-002 | P1 |
| Static/Unpinned/Adaptive Policy Comparison | AC-2.1, AC-2.10, AC-9.2, AC-9.4 | G56R-004 | G56R-003 | P1 |
| Budgets, Reset Boundaries, Checkpoint, and Resume | AC-9.1, AC-9.3 | G56R-005 | G56R-004 | P1 |
| Tier-aware Installer Defaults and Explicit Override | AC-3.* | G56R-006 | G56R-005; XPLAT-009 runtime stable | P1 |
| Quality-critical Executor Routing | AC-4.* | G56R-007 | G56R-006 | P1 |
| Structured-work Agent Routing | AC-5.* | G56R-008 | G56R-006 | P1 |
| Read-only Reasoning Agent Routing | AC-6.* | G56R-009 | G56R-006 | P1 |
| Latency-first Helper Routing | AC-7.* | G56R-010 | G56R-006 | P1 |
| Payload, Documentation, UAT, and Release Proof | AC-8.* | G56R-011 | G56R-007 through G56R-010 | P1 |

## 8. Success Criteria

1. All acceptance criteria are traceable through G56R-001 through G56R-011;
   the cross-cutting workflow-budget contract is implemented in the shared
   harness and release-proof specs.
2. Every shipped agent route has zero critical failures, clears per-dimension
   quality and accepted-workflow non-inferiority, and has an upper one-sided 95%
   confidence bound for paired mean token-derived credits-to-acceptance versus
   the current production policy below the predeclared `-delta`; mandatory p95
   credit/duration, late-failure, retry, and steering guardrails also pass.
3. A clean install verifies all ten agents and reports the exact effective
   model/effort matrix with no silent fallback.
4. Source, generated Codex payload, installed cache, guidance, tests, and UAT
   evidence agree on the final matrix.
5. Consumers retain a documented global compatibility override and a previous
   release rollback path.

## 9. References

- **Technical roadmap:** [codex-gpt-5-6-agent-routing-technical-roadmap.md](ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md)
- **Roadmap MOC:** [codex-gpt-5-6-agent-routing-roadmap-MOC.md](ai/specs/codex-gpt-5-6-agent-routing-roadmap-MOC.md)
- **Constitution:** [Racecraft Plugins Public Constitution](../.specify/memory/constitution.md)
- **Project standards:** [AGENTS.md](../AGENTS.md) and [CLAUDE.md](../CLAUDE.md)
- **Latest-model guidance:** [Using GPT-5.6](https://developers.openai.com/api/docs/guides/latest-model)
- **Migration guidance:** [Upgrading to GPT-5.6 Sol](https://developers.openai.com/api/docs/guides/upgrading-to-gpt-5p6-sol)
- **Codex subagents:** [Choosing models and reasoning](https://developers.openai.com/codex/concepts/subagents#choosing-models-and-reasoning)
- **Model pages:** [Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol), [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra), [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
- **Codex authentication:** [ChatGPT subscription access versus API-key usage](https://learn.chatgpt.com/docs/auth)
- **Codex plans, credits, and limits:** [Codex pricing](https://learn.chatgpt.com/docs/pricing)
- **Codex native protocol/telemetry capability surface:** [App server](https://learn.chatgpt.com/docs/app-server)
- **Speed modes and Spark limits:** [Codex speed](https://learn.chatgpt.com/docs/agent-configuration/speed)
- **Long-workflow controls:** [Long-running work](https://learn.chatgpt.com/docs/long-running-work)
- **API-price diagnostic only:** [OpenAI API pricing](https://developers.openai.com/api/docs/pricing)
- **Prompt guidance:** [GPT-5.6 prompting best practices](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices)
