# Codex ChatGPT Subscription Agent Routing Optimization Roadmap

**Select component-wise evidence-backed static defaults across a finite ChatGPT
support manifest, assemble one nine-agent core that improves over production in
one locked canonical environment, require non-regression in every other support
row, and gate Spark separately as an optional helper.**

This document defines the SPEC catalog for Codex ChatGPT subscription routing.
Each SPEC maps to an explicit acceptance-criteria subset in the source PRD and
is prepared for `$speckit-scaffold-spec G56R-NNN`.

**Source PRD:** [../../prd-codex-chatgpt-agent-routing.md](../../prd-codex-chatgpt-agent-routing.md)
**Roadmap MOC:** [codex-chatgpt-agent-routing-roadmap-MOC.md](codex-chatgpt-agent-routing-roadmap-MOC.md)
**Spec ID prefix:** `G56R-###`
**Proposed branch:** `codex/chatgpt-agent-routing`
**Status:** Draft; dependency graph approved 2026-07-09

**Legacy identifier note:** `G56R` is retained as a stable historical SPEC
prefix; it does not constrain the eligible model catalog or subscription plan.

---

## Roadmap Overview

The effort is decomposed into **11 specifications** across **8 dependency
tiers**.

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | G56R-001 | Authoritative research baseline and candidate matrix | Sequential spike |
| 2 | G56R-002 | Authentication, native telemetry, treatment proof, and replayable trace schema | Sequential foundation |
| 3 | G56R-003 | Corpus runner, acceptance scoring, and deterministic statistics | Sequential foundation |
| 4 | G56R-004 | Static/unpinned/adaptive policy comparison | Sequential foundation |
| 5 | G56R-005 | Harness budgets and boundary simulation | Sequential foundation |
| 6 | G56R-006 | Subscription-aware installer defaults and explicit global override | Sequential; implements the deferred Python helper |
| 7 | G56R-007, G56R-008, G56R-009, G56R-010 | Route four disjoint agent cohorts | Parallel after G56R-006; serialize shared regeneration |
| 8 | G56R-011 | Rebuild payload, reconcile shared assertions, run installed UAT, and prove release readiness | Sequential integration |

**Execution order:** G56R-001 -> G56R-002 -> G56R-003 -> G56R-004 ->
G56R-005 -> G56R-006 -> G56R-007 + G56R-008 + G56R-009 + G56R-010 ->
G56R-011

**Implementation boundary:** This sequence has no external prerequisite, but its
internal dependencies still apply: only G56R-001 is immediately scaffoldable.
G56R-006 later implements and activates the currently deferred Python
`install-codex-agents` helper; it must not reintroduce a deleted Bash helper.

### Research-backed starting hypotheses

This table records starting hypotheses, not a complete candidate shortlist or
pre-approved routing table. G56R-001 must capability-probe the catalog union
across every frozen support-manifest row and tested client, then derive the
universally deliverable intersection. G56R-003 screens every role-eligible entry
after G56R-002 establishes trustworthy telemetry; evidence controls qualification.

| Agent | Current source baseline | Starting hypothesis | Initial effort comparison | Required catalog challengers |
|---|---|---|---|---|
| `phase-executor` | GPT-5.5 / xhigh | Sol | progressive descent | Every eligible catalog model, including baseline and GPT-5.4 |
| `implement-executor` | GPT-5.5 / xhigh | Sol | progressive descent | Every eligible catalog model, including baseline and GPT-5.4 |
| `analyze-executor` | GPT-5.5 / xhigh | Sol | progressive descent; max only after measured failure | Every eligible catalog model, including baseline and GPT-5.4 |
| `checklist-executor` | GPT-5.5 / xhigh | Terra | progressive descent | Full eligible catalog; GPT-5.4 Mini required when exposed |
| `uat-runbook-author` | GPT-5.5 / xhigh | Terra | progressive descent | Full eligible catalog; GPT-5.4 Mini required when exposed |
| `clarify-executor` | GPT-5.5 / xhigh | Terra | progressive descent | Every eligible catalog model |
| `domain-researcher` | GPT-5.5 / xhigh | Terra | progressive descent | Every eligible catalog model |
| `codebase-analyst` | GPT-5.5 / low | Terra | progressive descent | Full eligible catalog, including lighter bounded-work models |
| `spec-context-analyst` | GPT-5.5 / low | Terra | progressive descent | Full eligible catalog, including lighter bounded-work models |
| `autopilot-fast-helper` | GPT-5.3 Codex Spark / effort omitted | Optional Spark on supported Pro rows | separate endpoint only | Validate no-helper behavior everywhere else |

### Qualification and integrated release-decision rule

- Deterministic role contract, grounding/evidence, and safety checks are hard
  gates.
- A candidate must have zero critical contract, safety, grounding, or mutation
  failures, clear absolute floors for every semantic-quality dimension, and
  clear a confidence-bound non-inferiority margin against baseline.
- The predeclared primary endpoint is task-level paired mean canonical resource
  units per assigned objective through acceptance or the fixed terminal stop,
  versus the immutable production policy in the locked canonical row and the
  frozen assigned comparator in every other row. Candidate-caused failures
  remain in the endpoint and acceptance gate.
- Accepted-workflow rate must be non-inferior; p95 canonical use/duration, late
  failure, retries, and steering are mandatory guardrails, never alternative
  post-hoc release endpoints.
- Freeze a finite support manifest. Keep native credits, legacy messages,
  included-limit utilization, purchased credits, resets, and throughput
  plan-stratified; never pool incompatible regimes.
- Use A1 capability/treatment screening, A2 within-model effort search, A3
  frozen pair comparison, Stage B prompt interaction, and Stage C cohort locks
  across disjoint component-selection partitions. Reserve a separate untouched
  integrated release-confirmation corpus for G56R-011.
- Run integrated confirmation as one multi-stratum campaign over the same locked
  objectives: the canonical row owns production superiority, every other
  mandatory row or proven equivalence class owns assigned-comparator non-
  inferiority, and incompatible native accounting is never pooled. This proves
  component-wise assembly improvement and support, not global optimization over
  alternative complete nine-agent policies.
- Treat unique objectives as the experimental units, cluster repeats within
  task, freeze stratum weights, and isolate cache crossover.
- Require installed or semantically equivalent custom-agent treatment before
  scoring; bare prompt emulation cannot support release.
- Start ordinary effort search at the documented default, ascend to a stable
  pass when needed, then descend and retest the boundary. Freeze Standard speed.
  Evaluate orchestration-changing Ultra only at policy level.
- Benchmark static pins against unpinned Codex selection and an explicit
  adaptive escalation policy.
- Evidence wins: no generation, tier, preview, or current default is forced into
  a role when it fails.

## Reviewability Contract

Every implementation spec must fit the repository's human review budget. Warn
above approximately 400 reviewable production LOC, 6 production files, or 15
total files; block-sized work must split unless an existing typed exception
legitimately applies. Generated payloads, tests, and documentation still count
toward reviewer load even where they do not count as production LOC.

**Estimator advisory:** The Python-authoritative `estimate-spec-size` operation
was rerun on 2026-07-11. Each implementation SPEC used one user story, its
declared total-file estimate, its current Scope-bullet count as functional
requirements, and `new_vs_modify=modify`; G56R-001 used the spike flag. The
per-SPEC budgets below record those outputs. G56R-003 returned `warn` at 500 LOC
and two suggested slices, so its scaffold must preserve the declared runner/
treatment versus fixture/scorer/corpus split. Every scaffold reruns the
estimator if scope changes.

## Dependency Graph

```text
G56R-001 Research Baseline and Candidate Matrix
    |
    v
G56R-002 Authentication, Telemetry, Treatment, and Trace Schema
    |
    v
G56R-003 Corpus Runner, Scoring, and Statistics
    |
    v
G56R-004 Policy Comparison
    |
    v
G56R-005 Harness Budgets and Boundary Simulation
    |
    v
G56R-006 Subscription-aware Installer Defaults and Explicit Override
    |
    +--> G56R-007 Quality-critical Executor Routing --------+
    +--> G56R-008 Structured-work Agent Routing ------------+
    +--> G56R-009 Read-only Reasoning Agent Routing --------+
    +--> G56R-010 Latency-first Helper Routing -------------+
                                                              |
                                                              v
                              G56R-011 Payload, Documentation, UAT, and Release Proof
```

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|---|---|---|---|---|
| G56R-001 | Research Baseline and Candidate Matrix | Pending | - | Ready to scaffold |
| G56R-002 | Authentication, Telemetry, Treatment, and Trace Schema | Pending | - | Blocked by G56R-001 |
| G56R-003 | Corpus Runner, Acceptance Scoring, and Statistics | Pending | - | Blocked by G56R-002 |
| G56R-004 | Static/Unpinned/Adaptive Policy Comparison | Pending | - | Blocked by G56R-003 |
| G56R-005 | Harness Budgets and Boundary Simulation | Pending | - | Blocked by G56R-004 |
| G56R-006 | Subscription-aware Installer Defaults and Explicit Override | Pending | - | Blocked by G56R-005 |
| G56R-007 | Quality-critical Executor Routing | Pending | - | Blocked by G56R-006 |
| G56R-008 | Structured-work Agent Routing | Pending | - | Blocked by G56R-006 |
| G56R-009 | Read-only Reasoning Agent Routing | Pending | - | Blocked by G56R-006 |
| G56R-010 | Latency-first Helper Routing | Pending | - | Blocked by G56R-006 |
| G56R-011 | Payload, Documentation, UAT, and Release Proof | Pending | - | Blocked by G56R-007 through G56R-010 |

**Status legend:** Pending | Ready | In Progress | In Review | Complete | Blocked

---

## Specification Sections

### G56R-001: Research Baseline and Candidate Matrix

**Priority:** P1 | **Depends On:** None | **Enables:** G56R-002

**Goal:** Produce the dated, cited decision input that defines what must be
measured before any installed default changes.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 0 (spike) | Suggested slices: 1 | Status: ok |
Production files: 0 |
Total files: approximately 3 |
Budget result: research spike; time-boxed, LOC sizing not applicable

**Scope:**

- Inventory the ten `speckit-pro/codex-agents/*.toml` files plus active Codex
  install, autopilot, structural validation, Layer 6, payload, installed-cache,
  and user-documentation policy surfaces.
- Record current model/effort, role boundary, output contract, mutation class,
  expected tool use, and representative task for each agent.
- Freeze the same finite manifest domain as AC-1.6. `mandatory_plan_keys` =
  [`free`, `go`, `plus`, `pro_5x`, `pro_20x`, `business_standard`,
  `business_grandfathered_codex_seat`, `enterprise_flexible`,
  `enterprise_included_seat`, `enterprise_legacy_message`, `edu_flexible`,
  `edu_included_seat`, `healthcare_managed`,
  `regulated_workspace_managed`, `gov_managed`, `teachers_managed`,
  `clinicians_managed`]. `named_category_keys` =
  [`chatgpt_for_healthcare`, `enterprise_regulated_workspace`, `chatgpt_gov`,
  `chatgpt_fedramp`, `chatgpt_for_teachers`, `chatgpt_for_clinicians`].
  `named_category_row_mappings` =
  [`chatgpt_for_healthcare -> healthcare_managed`,
  `enterprise_regulated_workspace -> regulated_workspace_managed`,
  `chatgpt_gov -> gov_managed`, `chatgpt_for_teachers -> teachers_managed`,
  `chatgpt_for_clinicians -> clinicians_managed`]. Record `chatgpt_fedramp` as a
  named exclusion because the current
  supported Codex setup is API-key-only. Treat rate-card inclusion as accounting
  evidence, never as treatment-delivery equivalence. Record a versioned
  `accounting_regime_id`, accounting
  components, and rate revisions rather than collapsing included usage, optional
  credits, grandfathered seats, and legacy messages. Freeze workspace/surface,
  permissions, required/optional
  capabilities, exclusions, support state, equivalence evidence/UAT owner, and
  the versioned allowance-boundary contract, including auto-top-up/overage
  state, for every row before screening. Every row also freezes
  `target_population_weight`, `baseline_policy_id`, `baseline_support_state`,
  `baseline_exact_treatment_evidence_hashes`, `baseline_comparator_type`,
  `row_reference_policy_id` or null, and `comparator_claim_boundary`. Before
  screening, select exactly one canonical row using the greatest frozen target-
  population weight with lexical `plan_key` tie-breaking, then bind
  `canonical_row_key`, `canonical_subscription_environment_id`,
  `canonical_selection_rationale`, `canonical_selection_rule_version`,
  `canonical_baseline_deliverable`, `canonical_candidate_set_hash`, and
  `canonical_lock_timestamp`. Prove production and candidate delivery there and
  invalidate downstream evidence if that lock changes.
- Create a primary-source fact table from current Codex plan/model availability,
  live client catalog/capability probes, model pages, pricing/limits, migration,
  prompt guidance, and Codex subagent pages.
- Reconcile research conflicts explicitly. Current canonical model pages take
  precedence over secondary claims about context size, availability, or effort
  support.
- Deliver the narrow candidate matrix, role-quality contracts, fixture backlog,
  three-current/seven-missing fixture inventory, availability probes, current
  harness limitations, and go/no-go handoffs to G56R-002 and G56R-003.
- INVEST/vertical-slice rationale: this spike independently reduces the one
  uncertainty that blocks safe model routing and is bounded by a research
  output rather than implementation layers.

**Out of Scope:**

- Agent TOML, installer, prompt, payload, or default changes.
- Live corpus execution or sweeps; G56R-003 owns them after G56R-002 supplies
  trustworthy telemetry and treatment-proof schemas.

**Key Files:**

- `docs/ai/research/` - dated subscription model-catalog research and matrix
- `speckit-pro/codex-agents/*.toml` - read-only inventory source
- `tests/speckit-pro/layer6-efficiency/` - fixture-gap inventory source

---

### G56R-002: Authentication, Telemetry, Treatment, and Trace Schema

**Priority:** P1 | **Depends On:** G56R-001 | **Enables:** G56R-003

**Goal:** Produce privacy-safe native telemetry, identity, and exact-treatment
proof schemas before live experiments depend on derived resource measures.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 265 | Suggested slices: 1 | Status: ok |
Production files: approximately 3 | Total files: approximately 10 |
Budget result: re-estimate at scaffold; synthetic traces precede live use

**Scope:**

- Fail closed when ChatGPT authentication or a frozen support-manifest row
  cannot be proven for qualification or release evidence. Preserve unresolved accounts for exploratory
  evidence only.
- Define trace fields and canonical serialization for `support_manifest_id`,
  `installable_agent_policy_id`, `subscription_environment_id`, and
  `execution_trace_id`, plus `universal_core_policy_id`,
  `optional_helper_policy_id`, and `release_policy_id`; G56R-001 and G56R-006
  own the manifest and policy identities that populate those fields.
- Serialize named-category resolution, the exactly-one canonical-row lock, and
  each row's production/reference comparator identity, delivery evidence, and
  claim boundary. G56R-001 owns the frozen values; G56R-003 owns live
  enforcement and population.
- Define raw parent/child trace events, requested/returned model/effort, speed,
  tokens/context/tools/compaction/retry/validation/abandonment, null behavior,
  and synthetic replay fixtures.
- Define the replay and exact-treatment proof schema for installed or
  semantically equivalent custom-agent configuration, including sandbox,
  approvals, skills, MCP startup, actual tool schema, parent overrides, context
  policy, and client. Synthetically validate success, null, and misdelivery
  records; G56R-003 owns live gate execution.
- Require 100% returned-model, speed, token, rate, and parent attribution for
  every billable invocation used by the primary endpoint; preserve nulls but
  never use a partial total for qualification or release. Separate benchmark judge cost.
- Keep the canonical token-vector score, plan-native token credits, legacy
  message observations, every included-limit bucket, and purchased-credit
  balances separate. Record limit ID, window, reset, utilization, and crossing.
- Use opaque aliases or keyed HMACs; enforce authorized datasets, ephemeral
  worktrees, candidate isolation, retention, secrets scanning, and public/
  private content/path redaction.

**Out of Scope:**

- Corpus execution, statistical qualification, policy comparison, budgets, and
  route selection.

**Key Files:**

- [proposed] `tests/speckit-pro/layer6-efficiency/lib/subscription_telemetry.py` - native account, plan, rate, and token adapter
- [proposed] `tests/speckit-pro/layer6-efficiency/lib/treatment_trace_schema.py` - identity and exact-treatment trace schema
- [proposed] `tests/speckit-pro/unit/test_efficiency_codex_telemetry.py` - synthetic replay and null/completeness contracts

---

### G56R-003: Corpus Runner, Acceptance Scoring, and Statistics

**Priority:** P1 | **Depends On:** G56R-002 | **Enables:** G56R-004

**Goal:** Execute exact custom-agent treatments and make component selection and
cohort locking deterministic without consuming final release-confirmation data.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 500 | Suggested slices: 2 | Status: warn |
Production files: approximately 4 | Total files: more than 20 expected |
Budget result: mandatory scaffold-time split between runner/treatment,
fixture/scorer governance, and seven-role corpus expansion

**Scope:**

- Add disjoint screening, selection, per-cohort lock, and integrated release-
  confirmation corpora. G56R-003 owns only the first three; it reserves the last
  untouched for G56R-011. Apply randomized paired order, cache isolation,
  unique-task sample sizing, blinded scoring, audits, inter-rater agreement, and
  multiplicity gatekeeping.
- Execute the installed custom-agent TOML or a generated semantically equivalent
  profile. Classify every pre-score failure as candidate incompatibility or
  independent harness misdelivery, populate the AC-2.16 live replay artifact,
  and permit only successfully assigned treatments to reach quality scoring.
- For per-agent pair selection freeze parent and non-candidate routes, prompts,
  tools/MCP/skills, repository snapshot, validator, truncation, context/
  compaction, retries, escalation, and acceptance checker.
- Implement `R_i` canonical units through acceptance/terminal stop and `A_i`
  acceptance per assigned objective after successful assignment. Candidate
  incompatibility is a hard row-qualification failure; rerun only preclassified
  independent harness/infrastructure misdelivery. Use task-level paired
  inference and frozen weights.
- Implement the one-sided bound, accepted-workflow non-inferiority, and a fully
  specified simultaneous guardrail registry. Cohort locks apply component gates;
  G56R-011 alone executes the final below-`-delta` release decision.
- Implement A1 default-effort treatment screening, A2 within-model effort
  boundaries, A3 frozen pair comparison, Stage B prompt interactions, and Stage
  C cohort lock. A1/A2 use screening, A3 and Stage B use selection, and each
  Stage C consumes only its preassigned cohort-lock partition. Keep the baseline
  prompt frozen throughout A1/A2/A3. Do not claim independent model or effort
  effects, and do not consume integrated release-confirmation data.
- Version/hash fixtures and scorers; use blinded five-class adjudication and
  invalidate all affected results after a change. Label legacy results
  non-release evidence.
- Apply the cross-plan decision rule: enforce the pre-outcome canonical-row
  lock, production superiority only there, assigned-comparator non-inferiority
  on every other manifest row, no pooled native accounting, and per-row
  opportunity-cost reporting. Freeze each row's candidate set, environment,
  production delivery state, comparator identity/claim boundary, and one
  selected challenger before integrated release confirmation. If production is
  not deliverable outside the canonical row, use only the predeclared content-
  addressed row reference; if neither comparator is deliverable, the row blocks
  release. A canonical-row or comparator change invalidates affected evidence;
  use the primary task-level estimator and confidence method for the descriptive
  universal-versus-row-specific contrast. Plan-only models never enter the
  universal candidate set.
- Pin the immutable canonical production policy, every non-canonical assigned
  comparator, and the total campaign budget, racing method, futility/dominance
  thresholds, and maximum cohort-lock and release candidates.

**Out of Scope:** unpinned/adaptive policy comparison, runtime budgets, and
installation defaults.

**Key Files:**

- `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py` - current Python runner to replace or extend
- `tests/speckit-pro/layer6-efficiency/lib/quality-scorer.py` - current lexical smoke scorer to layer beneath semantic gates
- `tests/speckit-pro/layer6-efficiency/fixtures-codex/` - three current fixture directories and seven-role backlog
- `tests/speckit-pro/unit/test-efficiency-codex-runner.py` - current runner contract coverage
- `tests/speckit-pro/unit/test-efficiency-runner-portability.py` - current Python portability coverage

---

### G56R-004: Static, Unpinned, and Adaptive Policy Comparison

**Priority:** P1 | **Depends On:** G56R-003 | **Enables:** G56R-005

**Goal:** Compare complete routing policies without misattributing policy-level
effects to one agent.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 235 | Suggested slices: 1 | Status: ok |
Production files: approximately 3 | Total files: approximately 10 |
Budget result: bounded to policy orchestration and replay fixtures

**Scope:**

- Compare static pins, unpinned Codex selection, adaptive routes, and Ultra on
  the same policy-level scorecard; Ultra includes all spawned child work.
- Log routing decisions and escalation/de-escalation signals. Keep these results
  policy-level; never use them as causal evidence for one agent route.
- Apply the static dominance consequence: if a control materially dominates but
  is not shipped, messaging may claim improvement only over the old static
  baseline, not best measured efficiency.

---

### G56R-005: Harness Budgets and Boundary Simulation

**Priority:** P1 | **Depends On:** G56R-004 | **Enables:** G56R-006

**Goal:** Prove evaluation accounting at campaign, workflow, and quota
boundaries without adding production scheduler scope.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 242 | Suggested slices: 1 | Status: ok |
Production files: approximately 3 | Total files: approximately 10 |
Budget result: synthetic boundary fixtures before live quota experiments

**Scope:**

- Enforce campaign and objective canonical-use/time, plan-native usage where
  applicable, retry, subagent, context-growth, cancellation, and escalation/
  de-escalation budgets in the harness.
- Simulate limit-near/exhausted, reset crossing, timeout, continue, and cancel
  terminal outcomes. Production checkpoint/resume is a separate follow-up.
- Mark reset-crossing runs and exclude them from ordinary within-window
  throughput inference while retaining canonical use through the terminal stop.
- Validate the boundary contracts frozen by G56R-001 for every manifest row:
  observable active-turn and new-work platform behavior, durable artifacts,
  graceful termination, supported resume/rerun path, user-visible recovery, and
  the prohibition on plugin-initiated purchase, auto top-up, overage, or route
  change. Freeze and record any pre-existing account-level automation; do not
  introduce or claim a production scheduler gate.

---

### G56R-006: Subscription-aware Installer Defaults and Explicit Override

**Priority:** P1 | **Depends On:** G56R-005 |
**Enables:** G56R-007 through G56R-010

**Goal:** Implement the deferred Python agent installer, install role-pinned
defaults predictably, and preserve one model-only compatibility override.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 265 | Suggested slices: 1 | Status: ok |
Production files: approximately 4 |
Total files: approximately 10 |
Budget result: re-estimate at scaffold; within one installer-policy slice by construction

**Scope:**

- Implement and activate the currently deferred `install-codex-agents` registry
  operation in the Python install helper; do not restore the deleted shell
  installer.
- Define `universal_core_policy_id` as the versioned ordered mapping from nine
  core roles to plugin-owned `installable_agent_policy_id` values plus the
  plugin-owned orchestration/retry hash. Define `optional_helper_policy_id` from
  the helper policy, allowed rows, `installed_enabled` or `not_installed` state,
  invocation rule, and no-helper contract; bind both into `release_policy_id` with the required
  environment-contract hash.
- Install and verify each plugin-owned `installable_agent_policy_id` plus the
  three aggregate IDs. Standard speed remains an environment-contract
  prerequisite verified by treatment traces; the installer neither claims nor
  mutates an unsupported per-agent speed field.
- Retain one model-only override for the nine required core agents. Change
  destination copies, never bundled source; retain each installed effort,
  prompt, and sandbox; leave Spark unchanged and preserve the Standard-speed
  environment requirement. Abort before any write if the tested client/catalog
  cannot prove compatibility for every resulting model-effort tuple under that
  requirement. Arbitrary effort mappings are out of scope.
- Distinguish known unsupported, known unavailable, and unresolved availability.
  Abort atomically for the first two; disclose unresolved preflight, require
  acknowledgement, and require a post-install treatment-delivery canary only
  when tuple compatibility is proven but authoritative entitlement preflight is
  unavailable. Apply hard availability aborts to required agents and an
  explicitly installed helper only. Known or unresolved Spark availability on
  a non-Spark row leaves the optional TOML out of the discoverable destination
  and requires the no-helper path instead.
- Reconcile the active install skill's expected set with all ten source agents,
  including `uat-runbook-author.toml`, preserve unrelated user agents, install
  exactly nine required destination TOMLs, install the conditional tenth only
  on proven Spark rows, verify destination content, and require restart.
- INVEST/vertical-slice rationale: a consumer can install any later cohort's
  role-pinned TOMLs end-to-end without another installer redesign.

**Out of Scope:**

- Per-plan or per-agent overrides, install profiles, and user-supplied effort
  mappings.
- Inventing entitlement results when authoritative discovery is unavailable.
- Claude installation behavior.

**Key Files:**

- `speckit-pro/codex-skills/install/SKILL.md` - active install contract
- `speckit-pro/speckit_pro_runner/helpers/install.py` - current install/doctor module and proposed agent-copy owner
- `speckit-pro/speckit_pro_runner/helpers/registry.py` - current deferred operation and proposed activation point
- `speckit-pro/codex-agents/*.toml` - source inventory
- `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` - current mutation/install contract tests to extend with fake-home cases

---

### G56R-007: Quality-critical Executor Routing

**Priority:** P1 | **Depends On:** G56R-006 | **Enables:** G56R-011

**Goal:** Qualify evidence-backed component policies for phase,
implementation, and analyze/remediation work, starting with Sol, without
claiming complete-core optimality.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 257 | Suggested slices: 1 | Status: ok |
Production files: 0 |
Total files: approximately 10 |
Budget result: re-estimate at scaffold; three disjoint TOMLs plus role evidence

**Scope:**

- Start with Sol/Terra hypotheses, then screen every model in the universal
  support-manifest intersection for `phase-executor`, `implement-executor`, and
  `analyze-executor`, including GPT-5.5 baseline and GPT-5.4. Follow A1/A2/A3
  pair selection, Stage B prompt interaction, one Stage C cohort lock, and exact
  treatment under the Standard-speed environment contract.
- Score real Specify/Plan/Tasks, strict TDD implementation, and full Analyze
  remediation contracts, not generic coding prompts.
- Pin each winning installable policy independently; update only
  cohort-specific descriptions, tests, and guidance required for truthfulness.
- Keep prompts frozen in A1/A2/A3; vary candidate prompt/context only for the A3
  shortlist in Stage B; freeze the joint policy in its Stage C cohort lock
  without consuming integrated release-confirmation data.
- Prove default install, explicit override, unavailable-helper behavior, and
  rollback for this cohort without touching the other cohorts.
- INVEST/vertical-slice rationale: the three highest-risk mutating roles share
  one quality-first evaluation seam and become installable with complete
  cohort-specific evidence.

**Out of Scope:**

- Structured checklist/UAT, read-only analyst, and fast-helper routes.
- Pro mode or API/runtime feature adoption.

**Key Files:**

- `speckit-pro/codex-agents/phase-executor.toml`
- `speckit-pro/codex-agents/implement-executor.toml`
- `speckit-pro/codex-agents/analyze-executor.toml`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex/` - cohort fixtures/results
- Cohort-specific structural/install assertions selected by G56R-006

---

### G56R-008: Structured-work Agent Routing

**Priority:** P1 | **Depends On:** G56R-006 | **Enables:** G56R-011

**Goal:** Qualify evidence-backed component policies for checklist remediation
and UAT runbook authoring, starting with Terra, without claiming complete-core
optimality.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 210 | Suggested slices: 1 | Status: ok |
Production files: 0 |
Total files: approximately 8 |
Budget result: re-estimate at scaffold; two role TOMLs plus evidence

**Scope:**

- Start with Terra, then screen the universal support-manifest intersection for
  `checklist-executor` and `uat-runbook-author`; GPT-5.4 Mini is
  required when exposed. Follow A1/A2/A3, Stage B, one Stage C cohort lock, and
  exact treatment for every candidate before integration.
- Require complete all-severity checklist remediation and executable,
  non-circular, acceptance-criteria-linked UAT runbooks.
- Pin independent winners while preserving workspace-write, error, and fail-open
  boundaries.
- Keep prompts frozen for A1/A2/A3, evaluate shortlisted prompt interactions in
  Stage B, consume only the cohort's Stage C lock partition, then prove install/
  override/rollback for the complete policy and tested environment.
- INVEST/vertical-slice rationale: two structured-output mutators share a
  measurable contract and ship independently of deep executors and analysts.

**Out of Scope:**

- Quality-critical executors, read-only analysts, and latency helper.

**Key Files:**

- `speckit-pro/codex-agents/checklist-executor.toml`
- `speckit-pro/codex-agents/uat-runbook-author.toml`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex/` - cohort fixtures/results
- Cohort-specific structural/install assertions selected by G56R-006

---

### G56R-009: Read-only Reasoning Agent Routing

**Priority:** P1 | **Depends On:** G56R-006 | **Enables:** G56R-011

**Goal:** Route clarification, external research, codebase analysis, and project
context analysis independently across the full eligible subscription catalog while
preserving evidence boundaries.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 290 | Suggested slices: 1 | Status: ok |
Production files: 0 |
Total files: approximately 12 |
Budget result: re-estimate at scaffold; four TOMLs plus bounded role fixtures

**Scope:**

- Start with Terra, then screen every universal-intersection candidate for all
  four roles; retain lighter models for bounded scans only when they preserve
  the contract.
- Start each candidate at its documented default, ascend to a stable pass when
  needed, then descend and retest the boundary. Exclude Ultra from this
  per-agent search and freeze Standard speed.
- Hard-gate read-only behavior, source-domain separation, citations/file
  locators, abstention, and structured return formats.
- Apply A1/A2/A3, Stage B, one Stage C cohort lock, and exact treatment. Pin the
  lowest-canonical-use qualified component policy per agent, not one forced
  cohort policy; prove install/override/rollback without consuming release-
  confirmation data or claiming complete-core optimality.
- INVEST/vertical-slice rationale: one read-only evidence seam enables parallel
  evaluation without mutation conflicts while preserving four distinct
  perspective contracts.

**Out of Scope:**

- Mutating executors, UAT authoring, and latency helper.

**Key Files:**

- `speckit-pro/codex-agents/clarify-executor.toml`
- `speckit-pro/codex-agents/domain-researcher.toml`
- `speckit-pro/codex-agents/codebase-analyst.toml`
- `speckit-pro/codex-agents/spec-context-analyst.toml`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex/` - cohort fixtures/results

---

### G56R-010: Latency-first Helper Routing

**Priority:** P1 | **Depends On:** G56R-006 | **Enables:** G56R-011

**Goal:** Gate Spark as an optional Pro-row capability and prove the universal
no-helper path without overstating shared efficiency.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 177 | Suggested slices: 1 | Status: ok |
Production files: 0 |
Total files: approximately 6 |
Budget result: re-estimate at scaffold; single-agent vertical slice

**Scope:**

- Retain Spark only on support-manifest rows where availability is proven.
  Explore Luna, GPT-5.4 Mini, GPT-5.4, Terra, and other candidates on a separate
  helper scorecard until Spark has a comparable resource measure.
- Create and reconcile `optional_helper_policy_id`, including allowed rows,
  `installed_enabled` or `not_installed` state, invocation rule, and no-helper
  contract. On a non-Spark row, retain the helper in source and payload but do
  not copy it into the discoverable destination or installed registry; Spark
  unavailability is not a core-install failure.
- Hard-gate read-only/advisory scope, concise return format, and prohibition on
  SDD reasoning or mutation.
- Explicitly set the winning effort so omission cannot inherit an unmeasured
  model default.
- Measure functionality, latency, spawn reliability, fallback, and observed
  Spark quota separately. Preserve autopilot continuation when the helper is
  not installed, unavailable, quota-limited, not invoked, or cannot spawn.
- Prove the no-helper path on every non-Spark support row. Spark is not installed
  or not invoked for universal-core confirmation and never enters its primary
  statistic.
- INVEST/vertical-slice rationale: one optional leaf helper can be evaluated,
  shipped, or rejected without changing any core executor.

**Out of Scope:**

- General SDD reasoning and all other agent routes.

**Key Files:**

- `speckit-pro/codex-agents/autopilot-fast-helper.toml`
- `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` - only directly tied helper guidance
- `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json`
- [proposed] `tests/speckit-pro/layer6-efficiency/fixtures-codex/autopilot-fast-helper/`

---

### G56R-011: Payload, Documentation, UAT, and Release Proof

**Priority:** P1 | **Depends On:** G56R-007, G56R-008, G56R-009, G56R-010 |
**Enables:** Release

**Goal:** Publish one internally consistent Codex payload whose nine-agent
universal core and optional helper are proven through separate release gates.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 395 | Suggested slices: 1 | Status: ok |
Production files: approximately 2 |
Total files: approximately 15 |
Budget result: re-estimate at scaffold; split release evidence from source fixes if warned

**Scope:**

- Rebuild `dist/codex` through the Python-authoritative payload builder and
  regenerate integrity metadata; never hand-edit generated agent files.
- Reconcile source, payload, install, benchmark, canary, rollback, and PR packet
  using `support_manifest_id`, `universal_core_policy_id`,
  `optional_helper_policy_id`, `release_policy_id`, each
  `installable_agent_policy_id`, each tested `subscription_environment_id`, and
  linked `execution_trace_id` values. Source and payload retain ten definitions;
  every destination has exactly nine core agents and only a proven Spark row has
  the conditional tenth.
- Update active Codex install/autopilot/public docs with the evidence-backed
  universal-core/optional-helper policy, global override, restart, entitlement,
  progressive-claim, and rollback boundaries while preserving historical
  records.
- Run deterministic source, payload, installed-cache, default-suite,
  active-path, benchmark replay, and install verification gates.
- Run cohort locks and one integrated multi-stratum release-confirmation
  campaign. Use the same locked objectives in the canonical row and every other
  mandatory row or predeclared equivalence class. The exactly one pre-outcome
  canonical row owns production superiority; every other stratum uses its AC-
  2.13 assigned comparator and owns non-inferiority under the same multiplicity
  family. For every support-manifest row and named-category resolution, prove
  authentication, entitlement, model/effort catalog, installation, effective
  tools, exact treatment, comparator delivery, and no-helper behavior. Run at
  least one live smoke per predeclared plan-equivalence class. An inaccessible
  mandatory row remains `unverified` and blocks universal release; another
  class cannot cover it without the equivalence proof frozen before screening.
- Execute the predeclared long-workflow portfolio with per-row or equivalence-
  class results, including multi-agent work, compaction, interruption/resume,
  validation repair, and an allowance-boundary approach with wait categories
  separated. Validate the frozen boundary contract, platform stop behavior,
  user-visible recovery, and no plugin-initiated purchase or route change for
  each represented row; do not claim a v1 production scheduler gate.
- Evaluate the component-wise assembled installed nine-agent core exactly once
  on the untouched integrated release-confirmation corpus after cohort locks.
  Pair it with the immutable production core in the canonical row and each
  non-canonical row's frozen assigned comparator elsewhere, with Spark not
  installed or not invoked in both arms. This is the sole promotion decision.
  It must pass canonical production superiority plus every other stratum's
  assigned-comparator non-inferiority, acceptance, safety/quality, guardrail,
  and manifest-row qualification without pooling regimes. Passing does not
  establish global optimality among alternative complete assemblies. Failure
  reopens selection and requires a new versioned release-confirmation corpus.
- Separately gate Spark on supported Pro rows and the no-helper path everywhere
  else. A Spark invocation invalidates a universal-core run.
- Pin the support manifest, named-category resolutions, canonical schedule,
  canonical row/environment/rationale/candidate hash/lock timestamp, per-row
  comparator identities and claim boundaries, minimum/tested Codex versions,
  capability probes, environments, and rate regimes. Define affected-evidence
  rerun triggers and production drift alerts.
- Produce a public-readable PR packet with selected and rejected candidates,
  known gaps, review order, rollback, and release evidence.
- INVEST/vertical-slice rationale: this final integration slice tests whether
  four independently selected cohorts form a passing consumer-installable
  system and reopens selection if they do not.

**Out of Scope:**

- Plans or environments absent from the frozen support manifest and unrelated
  XPLAT cleanup.
- Manual version bumps; release-please owns release versioning.

**Key Files:**

- `scripts/build-plugin-payloads.py`
- `speckit-pro/speckit_pro_runner/gates/payloads.py`
- `dist/codex/speckit-pro/` - generated output only
- `speckit-pro/codex-skills/install/SKILL.md`
- `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`
- `docs-site/src/content/docs/install/codex.md`
- `tests/speckit-pro/layer1-structural/validate-codex-agents.py`
- `tests/speckit-pro/layer1-structural/validate-codex-routing-docs.py`
- `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py`
- `docs/ai/specs/.process/` - release and live-UAT evidence

---

## Environment & Deployment Context

### Existing Infrastructure (No Changes Needed)

| Resource | Detail |
|---|---|
| Codex agent source | Ten TOML files under `speckit-pro/codex-agents/` |
| Installed destination | `~/.codex/agents/` or explicit compatible destination |
| Evaluation | Python Layer 6 prompt-emulation runner, three existing role fixtures, lexical smoke scorer; current results cannot support release |
| Payload build | Python 3.11+ `scripts/build-plugin-payloads.py` and runner payload gate |
| Release | release-please plus deterministic source/payload/install/release gates |

### Changes Required

| Change | Where | Detail |
|---|---|---|
| Research record | `docs/ai/research/` | Dated official facts, conflicts, candidate matrix, role contracts |
| Support manifest | `docs/ai/research/` | Finite plan/accounting variants, named-category resolutions, one canonical row, per-row comparators, boundary contracts, evidence hashes, support states, and equivalence classes |
| Model-effort pair evaluation | Layer 6 Python Codex harness | Exact treatment, canonical score, per-plan qualification, disjoint corpora, task-level statistics, ten role contracts |
| Installer policy | Python install helper and registry | Activate deferred copy helper; core/helper/release IDs; nine required destination agents plus conditional tenth helper; model-only atomic override |
| Agent routes | `speckit-pro/codex-agents/*.toml` | Nine-agent universal core plus separately gated optional helper |
| Generated payload | `dist/codex/` | Rebuild from source and refresh integrity evidence |
| Consumer guidance | Codex install/autopilot/docs surfaces | Core/helper policy, fallback, restart, availability, rollback |

### Local Development Setup

| Requirement | How |
|---|---|
| Python | Python 3.11+ standard library runner already required by SpecKit Pro |
| Codex | Current client with custom-agent TOML support and access to shortlisted models |
| Live eval budget | Explicit developer-local budget; never required by default CI |
| Official accounting | Freeze canonical token schedule and plan-native/legacy regimes; API pricing is diagnostic only |

## References

- **Source PRD:** [../../prd-codex-chatgpt-agent-routing.md](../../prd-codex-chatgpt-agent-routing.md)
- **Roadmap MOC:** [codex-chatgpt-agent-routing-roadmap-MOC.md](codex-chatgpt-agent-routing-roadmap-MOC.md)
- **Constitution:** [../../../.specify/memory/constitution.md](../../../.specify/memory/constitution.md)
- **Project standards:** [../../../AGENTS.md](../../../AGENTS.md) and [../../../CLAUDE.md](../../../CLAUDE.md)
- **OpenAI latest model:** [Using GPT-5.6](https://developers.openai.com/api/docs/guides/latest-model)
- **OpenAI migration guide:** [Upgrading to GPT-5.6 Sol](https://developers.openai.com/api/docs/guides/upgrading-to-gpt-5p6-sol)
- **Codex models, Max, and Ultra:** [Codex models](https://learn.chatgpt.com/docs/models)
- **Codex model routing:** [Choosing models and reasoning](https://learn.chatgpt.com/docs/agent-configuration/subagents#choosing-models-and-reasoning)
- **Codex custom-agent configuration:** [Custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents)
- **Model details:** [Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol), [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra), [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
- **Codex authentication:** [ChatGPT subscription access versus API-key usage](https://learn.chatgpt.com/docs/auth)
- **Codex plans, credits, and limits:** [Codex pricing](https://learn.chatgpt.com/docs/pricing)
- **ChatGPT plan access:** [Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)
- **Native and legacy accounting:** [Codex rate card](https://help.openai.com/en/articles/20001106-codex-rate-card)
- **Healthcare, Regulated, Clinicians, and Codex Local:** [HIPAA-eligible products and functionality](https://help.openai.com/en/articles/20001069-chatgpt-healthcare-and-regulated-workspace-functionality)
- **FedRAMP Codex authentication boundary:** [ChatGPT Enterprise and API Platform for FedRAMP](https://help.openai.com/en/articles/20001070-chatgpt-enterprise-and-api-platform-for-fedramp)
- **ChatGPT Gov environment:** [Introducing ChatGPT Gov](https://openai.com/global-affairs/introducing-chatgpt-gov/)
- **Individual-plan credits:** [Using credits for flexible usage](https://help.openai.com/en/articles/12642688-using-credits-for-flexible-usage-in-chatgpt-freegopluspro)
- **Managed-plan accounting variants:** [Flexible managed-plan pricing](https://help.openai.com/en/articles/11487671-flexible-pricing-for-chatgpt-enterprise-plans)
- **Codex telemetry capability surface:** [App server](https://learn.chatgpt.com/docs/app-server)
- **Speed modes and Spark:** [Codex speed](https://learn.chatgpt.com/docs/agent-configuration/speed)
- **ChatGPT plugins and permissions:** [Plugins](https://learn.chatgpt.com/docs/plugins)
- **Managed workspace controls:** [ChatGPT Work Admin FAQ](https://learn.chatgpt.com/docs/enterprise/work-admin-faq)
- **Long-workflow controls:** [Long-running work](https://learn.chatgpt.com/docs/long-running-work)
- **API-price diagnostic only:** [OpenAI API pricing](https://developers.openai.com/api/docs/pricing)
- **Prompt guidance:** [GPT-5.6 prompting best practices](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices)
