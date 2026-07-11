# Codex ChatGPT Pro Agent Routing Optimization Roadmap

**Select efficient static installation defaults across the full model catalog
available to ChatGPT Pro that minimize
Pro allowance consumption per accepted end-to-end workflow while preserving
role quality, reliability, and completion time.**

This document defines the SPEC catalog for Codex ChatGPT Pro agent routing.
Each SPEC maps to an explicit acceptance-criteria subset in the source PRD and
is prepared for `$speckit-scaffold-spec G56R-NNN`.

**Source PRD:** [../../prd-codex-gpt-5-6-agent-routing.md](../../prd-codex-gpt-5-6-agent-routing.md)
**Roadmap MOC:** [codex-gpt-5-6-agent-routing-roadmap-MOC.md](codex-gpt-5-6-agent-routing-roadmap-MOC.md)
**Spec ID prefix:** `G56R-###`
**Proposed branch:** `codex/gpt-5-6-agent-routing`
**Status:** Draft; dependency graph approved 2026-07-09

---

## Roadmap Overview

The effort is decomposed into **11 specifications** across **8 dependency
tiers**.

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | G56R-001 | Authoritative research baseline and candidate matrix | Sequential spike |
| 2 | G56R-002 | Authentication, native telemetry, and replayable trace schema | Sequential foundation |
| 3 | G56R-003 | Corpus runner, acceptance scoring, and deterministic statistics | Sequential foundation |
| 4 | G56R-004 | Static/unpinned/adaptive policy comparison | Sequential foundation |
| 5 | G56R-005 | Budgets, reset boundaries, checkpoint, and resume | Sequential foundation |
| 6 | G56R-006 | Tier-aware installer defaults and explicit global override | Sequential; requires stable post-XPLAT-009 runtime |
| 7 | G56R-007, G56R-008, G56R-009, G56R-010 | Route four disjoint agent cohorts | Parallel after G56R-006; serialize shared regeneration |
| 8 | G56R-011 | Rebuild payload, reconcile shared assertions, run installed UAT, and prove release readiness | Sequential integration |

**Execution order:** G56R-001 -> G56R-002 -> G56R-003 -> G56R-004 ->
G56R-005 -> G56R-006 -> G56R-007 + G56R-008 + G56R-009 + G56R-010 ->
G56R-011

**External prerequisite:** G56R-001 through G56R-005 may start immediately.
G56R-006 must scaffold against the authoritative installer/runtime that exists
after XPLAT-009 stabilizes; it must not reintroduce a deleted Bash helper.

### Research-backed starting hypotheses

This table records starting hypotheses, not a complete candidate shortlist or
pre-approved routing table. G56R-001 must capability-probe the entire model
catalog exposed to the declared Pro tier and tested client. G56R-003 screens
every role-eligible entry after G56R-002 establishes trustworthy telemetry;
evidence controls promotion.

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
| `autopilot-fast-helper` | GPT-5.3 Codex Spark / effort omitted | Luna | progressive descent | Full eligible catalog; Spark reported separately |

### Promotion rule

- Deterministic role contract, grounding/evidence, and safety checks are hard
  gates.
- A candidate must have zero critical contract, safety, grounding, or mutation
  failures, clear absolute floors for every semantic-quality dimension, and
  clear a confidence-bound non-inferiority margin against baseline.
- The predeclared primary endpoint is paired mean total token-derived credits-
  to-acceptance versus the current production routing policy, including all
  failed, cancelled, retried, repaired, compacted, and abandoned work. Promote
  only when the upper one-sided 95% confidence bound for the paired difference
  is below the predeclared `-delta` practical-improvement margin.
- Accepted-workflow rate must be non-inferior; p95 credits/duration, late
  failure, retries, and steering are mandatory guardrails, never alternative
  post-hoc promotion endpoints.
- Record rate-limit utilization delta and successful accepted workflows per
  five-hour window as direct Pro-plan outcomes. Keep API-dollar normalization
  as a separately labeled diagnostic only.
- Progressively descend through supported efforts while gates pass, then
  retest the lowest passing boundary. Test `max` only for an unresolved
  quality-first failure.
- Use paired runs on identical snapshots, randomized order, controlled cache
  states, a stratified and held-out workflow corpus, and a predeclared
  confidence rule. Three repeats are a pilot floor, not the final design.
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

**Estimator advisory:** The required `estimate-spec-size` runner operation was
not registered in the installed/source 2.18.0 runner during authoring. Per the
authoring protocol, projected LOC is marked unavailable rather than guessed.
Every G56R scaffold must rerun the estimator and split on a SPIDR seam if the
operation returns a warning.

## Dependency Graph

```text
G56R-001 Research Baseline and Candidate Matrix
    |
    v
G56R-002 Authentication, Telemetry, and Trace Schema
    |
    v
G56R-003 Corpus Runner, Scoring, and Statistics
    |
    v
G56R-004 Policy Comparison
    |
    v
G56R-005 Budgets, Reset Boundaries, Checkpoint, and Resume
    |
    v
G56R-006 Tier-aware Installer Defaults and Explicit Override
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
| G56R-002 | Authentication, Telemetry, and Trace Schema | Pending | - | Blocked by G56R-001 |
| G56R-003 | Corpus Runner, Acceptance Scoring, and Statistics | Pending | - | Blocked by G56R-002 |
| G56R-004 | Static/Unpinned/Adaptive Policy Comparison | Pending | - | Blocked by G56R-003 |
| G56R-005 | Budgets, Reset Boundaries, Checkpoint, and Resume | Pending | - | Blocked by G56R-004 |
| G56R-006 | Tier-aware Installer Defaults and Explicit Override | Pending | - | Blocked by G56R-005 and stable XPLAT-009 runtime |
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
Projected reviewable LOC: unavailable (estimator operation absent) |
Production files: 0 |
Total files: approximately 3 |
Budget result: research spike; time-boxed, LOC sizing not applicable

**Scope:**

- Inventory the ten `speckit-pro/codex-agents/*.toml` files plus active Codex
  install, autopilot, structural validation, Layer 6, payload, installed-cache,
  and user-documentation policy surfaces.
- Record current model/effort, role boundary, output contract, mutation class,
  expected tool use, and representative task for each agent.
- Create a primary-source fact table from current Codex plan/model availability,
  live client catalog/capability probes, model pages, pricing/limits, migration,
  prompt guidance, and Codex subagent pages.
- Reconcile research conflicts explicitly. Current canonical model pages take
  precedence over secondary claims about context size, availability, or effort
  support.
- Deliver the narrow candidate matrix, role-quality contracts, fixture backlog,
  availability probes, and a go/no-go handoff to G56R-002.
- INVEST/vertical-slice rationale: this spike independently reduces the one
  uncertainty that blocks safe model routing and is bounded by a research
  output rather than implementation layers.

**Out of Scope:**

- Agent TOML, installer, prompt, payload, or default changes.
- Live exhaustive sweeps; G56R-002 owns executable evaluation.

**Key Files:**

- `docs/ai/research/` - dated Pro model-catalog research and candidate matrix
- `speckit-pro/codex-agents/*.toml` - read-only inventory source
- `tests/speckit-pro/layer6-efficiency/` - fixture-gap inventory source

---

### G56R-002: Authentication, Telemetry, and Trace Schema

**Priority:** P1 | **Depends On:** G56R-001 | **Enables:** G56R-003

**Goal:** Produce privacy-safe, replayable native evidence before live
experiments or routing decisions depend on derived allowance measures.

**Reviewability Budget:** Primary surface: harness/adapter |
Production files: approximately 3 | Total files: approximately 10 |
Budget result: re-estimate at scaffold; synthetic traces precede live use

**Scope:**

- Fail closed on non-ChatGPT or non-Pro auth. Record Pro 5x/20x only from an
  authoritative entitlement field or archived entitlement evidence with source,
  timestamp, and hash; never infer it from capacity. Allow explicitly tier-
  unresolved, tier-neutral analysis while blocking tier-specific conclusions.
- Define raw parent/child trace events, requested/returned model and effort,
  tokens/context/tools/compaction/retry/validation/abandonment, null behavior,
  version/configuration hashes, and synthetic replay fixtures.
- Keep token-derived credits, every included-limit bucket, and purchased-credit
  balances separate. Record limit ID, window duration, reset time, before/after
  utilization, and reset crossing.
- Use opaque aliases or keyed HMACs; redact emails, IDs, balances, and private
  paths from public evidence.

**Out of Scope:** corpus execution, statistical promotion, policy comparison,
budgets, and route selection.

---

### G56R-003: Corpus Runner, Acceptance Scoring, and Statistics

**Priority:** P1 | **Depends On:** G56R-002 | **Enables:** G56R-004

**Goal:** Make the quality and efficiency decision deterministic on a paired,
stratified, held-out corpus.

**Reviewability Budget:** Primary surface: harness/adapter |
Production files: approximately 4 | Total files: approximately 15 |
Budget result: split corpus fixtures from statistics if the estimator warns

**Scope:**

- Add ten role contracts, stratified/held-out workflows, randomized paired run
  order, controlled cache states, confidence-driven sample sizes, blinded
  scoring, random audits, and inter-rater agreement.
- For per-agent attribution freeze parent and non-candidate routes, prompts,
  tools/MCP/skills, repository snapshot, validator, truncation, context/
  compaction, retries, escalation, and acceptance checker.
- Implement paired mean token-derived credits-to-acceptance versus current
  production as the sole primary efficiency endpoint. Charge failures,
  cancellations, retries, repairs, compaction, and abandonment; require the
  upper one-sided 95% confidence bound below predeclared `-delta`.
- Enforce accepted-workflow non-inferiority and p95 credits/duration, late-
  failure, retry, and steering guardrails. Report included-limit and purchased-
  credit measures separately as secondary outcomes.
- Progressively descend every supported effort and retest the first failing
  boundary; select the lowest stable passing effort.

**Out of Scope:** unpinned/adaptive policy attribution, runtime budgets, and
installation defaults.

---

### G56R-004: Static, Unpinned, and Adaptive Policy Comparison

**Priority:** P1 | **Depends On:** G56R-003 | **Enables:** G56R-005

**Goal:** Compare complete routing policies without misattributing policy-level
effects to one agent.

**Reviewability Budget:** Primary surface: harness/adapter |
Production files: approximately 3 | Total files: approximately 10 |
Budget result: bounded to policy orchestration and replay fixtures

**Scope:**

- Compare static pins, unpinned Codex selection, and explicit adaptive routes on
  the same end-to-end corpus and deterministic promotion scorecard.
- Log routing decisions and escalation/de-escalation signals. Keep these results
  policy-level; never use them as causal evidence for one agent route.
- Jointly test bounded prompt/context variants with route and effort while
  preserving unchanged-prompt controls and configuration hashes.

---

### G56R-005: Budgets, Reset Boundaries, Checkpoint, and Resume

**Priority:** P1 | **Depends On:** G56R-004 | **Enables:** G56R-006

**Goal:** Prove allowance-aware behavior at phase budgets and quota boundaries.

**Reviewability Budget:** Primary surface: scheduler/runtime |
Production files: approximately 3 | Total files: approximately 10 |
Budget result: synthetic boundary fixtures before live quota experiments

**Scope:**

- Enforce phase-credit, retry, subagent, context-growth, cancellation, and
  escalation/de-escalation budgets.
- Define limit-near/exhausted checkpoint, pause, reset-boundary resume, continue,
  and cancel behavior with durable objectives and acceptance state.
- Mark reset-crossing runs and exclude them from ordinary within-window
  throughput inference while retaining all credits-to-acceptance.

---

### G56R-006: Tier-aware Installer Defaults and Explicit Override

**Priority:** P1 | **Depends On:** G56R-005 and stable post-XPLAT-009 runtime |
**Enables:** G56R-007 through G56R-010

**Goal:** Install role-pinned defaults predictably while preserving one explicit
global compatibility override and complete ten-agent verification.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: unavailable (estimator operation absent) |
Production files: approximately 4 |
Total files: approximately 10 |
Budget result: re-estimate at scaffold; within one installer-policy slice by construction

**Scope:**

- Ground on the authoritative Python mutation/install registry after XPLAT-009;
  remove assumptions about the deleted shell installer from active guidance and
  tests without changing historical evidence.
- Change default installation from a uniform model rewrite to verified copying
  of each source TOML's explicit model and effort.
- Retain a single deliberate global override that changes destination copies,
  never bundled source, and report when it collapses the role matrix.
- Validate model/effort syntax and inventory before mutation; reject incomplete
  source sets and prevent partial installation or silent fallback.
- Reconcile the active install skill's expected set with all ten source agents,
  including `uat-runbook-author.toml`, preserve unrelated user agents, verify
  destination content, and require restart.
- INVEST/vertical-slice rationale: a consumer can install any later cohort's
  role-pinned TOMLs end-to-end without another installer redesign.

**Out of Scope:**

- Per-tier or per-agent overrides and install profiles.
- Network entitlement discovery that Codex does not expose reliably.
- Claude installation behavior.

**Key Files:**

- `speckit-pro/codex-skills/install/SKILL.md` - active install contract
- `speckit-pro/speckit_pro_runner/helpers/` - post-XPLAT-009 authoritative install/mutation implementation
- `speckit-pro/codex-agents/*.toml` - source inventory
- `tests/speckit-pro/layer4-scripts/` - active installer/mutation contract coverage after XPLAT-009

---

### G56R-007: Quality-critical Executor Routing

**Priority:** P1 | **Depends On:** G56R-006 | **Enables:** G56R-011

**Goal:** Route phase, implementation, and analyze/remediation work to the
lowest-allowance passing static configuration, starting with Sol.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: unavailable (estimator operation absent) |
Production files: 0 |
Total files: approximately 10 |
Budget result: re-estimate at scaffold; three disjoint TOMLs plus role evidence

**Scope:**

- Start with Sol/Terra hypotheses, then screen every eligible model exposed by
  the declared Pro tier/client for `phase-executor`, `implement-executor`, and
  `analyze-executor`, including GPT-5.5 baseline and GPT-5.4; progressively
  descend effort and test `max` only for a measured unresolved failure.
- Score real Specify/Plan/Tasks, strict TDD implementation, and full Analyze
  remediation contracts, not generic coding prompts.
- Pin each winning model and effort independently in its TOML; update only
  cohort-specific descriptions, tests, and guidance required for truthfulness.
- Evaluate the unchanged prompt and targeted prompt/context variants alongside
  model and effort candidates; promote only a jointly passing combination.
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

**Goal:** Route checklist remediation and UAT runbook authoring to the
lowest-allowance passing static configuration, starting with Terra.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: unavailable (estimator operation absent) |
Production files: 0 |
Total files: approximately 8 |
Budget result: re-estimate at scaffold; two role TOMLs plus evidence

**Scope:**

- Start with Terra, then screen the full eligible Pro catalog for
  `checklist-executor` and `uat-runbook-author`; GPT-5.4 Mini is
  required when exposed. Progressively descend supported effort for
  every candidate.
- Require complete all-severity checklist remediation and executable,
  non-circular, acceptance-criteria-linked UAT runbooks.
- Pin independent winners while preserving workspace-write, error, and fail-open
  boundaries.
- Include unchanged-prompt controls and targeted prompt/context variants in the
  paired model/effort matrix, then prove install, override, and rollback for the
  selected combination.
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
context analysis independently across the full eligible Pro catalog while
preserving evidence boundaries.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: unavailable (estimator operation absent) |
Production files: 0 |
Total files: approximately 12 |
Budget result: re-estimate at scaffold; four TOMLs plus bounded role fixtures

**Scope:**

- Start with Terra, then screen every eligible model exposed by the declared Pro
  tier/client for all four roles; retain lighter models for bounded scans only
  when they preserve the contract.
- Progressively descend every candidate's supported effort levels. Never rely
  on an omitted or model-specific default effort.
- Hard-gate read-only behavior, source-domain separation, citations/file
  locators, abstention, and structured return formats.
- Pin the lowest-allowance passing static route + effort + prompt combination
  per agent, not one forced cohort policy, and prove install/override/rollback.
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

**Goal:** Select the best bounded-helper route from the full eligible Pro
catalog while preserving its advisory contract and graceful unavailability.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: unavailable (estimator operation absent) |
Production files: 0 |
Total files: approximately 6 |
Budget result: re-estimate at scaffold; single-agent vertical slice

**Scope:**

- Screen Luna, GPT-5.4 Mini, GPT-5.4, Terra, current Spark behavior, and every
  other eligible exposed model on compression, triage, and query drafting;
  report Spark separately until its preview quota is comparable.
- Hard-gate read-only/advisory scope, concise return format, and prohibition on
  SDD reasoning or mutation.
- Explicitly set the winning effort so omission cannot inherit an unmeasured
  model default.
- Preserve autopilot's correct continuation when the optional helper cannot
  spawn; do not force any named model when it fails the shared promotion rule.
- Evaluate unchanged and bounded prompt/context variants jointly with the route
  and effort candidates, then prove install, override, and rollback behavior.
- INVEST/vertical-slice rationale: one optional leaf helper can be evaluated,
  shipped, or rejected without changing any core executor.

**Out of Scope:**

- General SDD reasoning and all other agent routes.

**Key Files:**

- `speckit-pro/codex-agents/autopilot-fast-helper.toml`
- `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` - only directly tied helper guidance
- `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex/autopilot-fast-helper/`

---

### G56R-011: Payload, Documentation, UAT, and Release Proof

**Priority:** P1 | **Depends On:** G56R-007, G56R-008, G56R-009, G56R-010 |
**Enables:** Release

**Goal:** Publish one internally consistent Codex payload whose ten-agent matrix
is proven in source, generated artifacts, install verification, controlled
ChatGPT Pro canaries, and live UAT.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: unavailable (estimator operation absent) |
Production files: approximately 2 |
Total files: approximately 15 |
Budget result: re-estimate at scaffold; split release evidence from source fixes if warned

**Scope:**

- Rebuild `dist/codex` through the Python-authoritative payload builder and
  regenerate integrity metadata; never hand-edit generated agent files.
- Reconcile shared structural/tool-scoping/install assertions with the final ten
  independent model/effort choices and delete active uniform-policy claims.
- Update active Codex install/autopilot/public docs with the evidence-backed
  matrix, global override, restart, entitlement, progressive-claim, and rollback
  boundaries while preserving historical records.
- Run deterministic source, payload, installed-cache, default-suite,
  active-path, benchmark replay, and install verification gates.
- On an isolated ChatGPT Pro 5x or 20x account, complete one installed workflow
  per cohort as a smoke gate, then run multiple held-out long workflows with
  the full workflow trace and allowance scorecard.
- Pin minimum/tested Codex versions, capability probes, tier, configuration,
  and rate-card revision. Define rebenchmark triggers for model, client,
  prompt, rate-card, entitlement, or policy changes and production drift alerts
  for accepted-workflow rate, p95 allowance/duration, escalation, and late
  failure.
- Produce a public-readable PR packet with selected and rejected candidates,
  known gaps, review order, rollback, and release evidence.
- INVEST/vertical-slice rationale: this final integration slice turns four
  independently proven cohorts into one consumer-installable release without
  reopening their routing decisions.

**Out of Scope:**

- Universal OS/account availability claims and unrelated XPLAT cleanup.
- Manual version bumps; release-please owns promotion.

**Key Files:**

- `scripts/build-plugin-payloads.py`
- `speckit-pro/speckit_pro_runner/gates/payloads.py`
- `dist/codex/speckit-pro/` - generated output only
- `speckit-pro/codex-skills/install/SKILL.md`
- `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`
- `docs-site/src/content/docs/install/codex.md`
- `tests/speckit-pro/layer1-structural/validate-codex-agents.sh`
- `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh`
- `docs/ai/specs/.process/` - release and live-UAT evidence

---

## Environment & Deployment Context

### Existing Infrastructure (No Changes Needed)

| Resource | Detail |
|---|---|
| Codex agent source | Ten TOML files under `speckit-pro/codex-agents/` |
| Installed destination | `~/.codex/agents/` or explicit compatible destination |
| Evaluation | Layer 6 Codex runner, three existing role fixtures, quality scorer, replay result |
| Payload build | Python 3.11+ `scripts/build-plugin-payloads.py` and runner payload gate |
| Release | release-please plus deterministic source/payload/install/release gates |

### Changes Required

| Change | Where | Detail |
|---|---|---|
| Research record | `docs/ai/research/` | Dated official facts, conflicts, candidate matrix, role contracts |
| Model x effort/policy evaluation | Layer 6 active Codex harness | Pro-auth fail-close, workflow trace, allowance scorecard, stratified/held-out corpus, all ten role contracts |
| Installer policy | Post-XPLAT-009 Python install/mutation surface | Preserve role pins; one explicit global override; ten-agent verification |
| Agent routes | `speckit-pro/codex-agents/*.toml` | Independent evidence-backed model/effort pins |
| Generated payload | `dist/codex/` | Rebuild from source and refresh integrity evidence |
| Consumer guidance | Codex install/autopilot/docs surfaces | Matrix, fallback, restart, availability, rollback |

### Local Development Setup

| Requirement | How |
|---|---|
| Python | Python 3.11+ standard library runner already required by SpecKit Pro |
| Codex | Current client with custom-agent TOML support and access to shortlisted models |
| Live eval budget | Explicit developer-local budget; never required by default CI |
| Official accounting | Snapshot Codex plan/credit/limit documentation; API pricing is diagnostic only |

## References

- **Source PRD:** [../../prd-codex-gpt-5-6-agent-routing.md](../../prd-codex-gpt-5-6-agent-routing.md)
- **Roadmap MOC:** [codex-gpt-5-6-agent-routing-roadmap-MOC.md](codex-gpt-5-6-agent-routing-roadmap-MOC.md)
- **Constitution:** [../../../.specify/memory/constitution.md](../../../.specify/memory/constitution.md)
- **Project standards:** [../../../AGENTS.md](../../../AGENTS.md) and [../../../CLAUDE.md](../../../CLAUDE.md)
- **OpenAI latest model:** [Using GPT-5.6](https://developers.openai.com/api/docs/guides/latest-model)
- **OpenAI migration guide:** [Upgrading to GPT-5.6 Sol](https://developers.openai.com/api/docs/guides/upgrading-to-gpt-5p6-sol)
- **Codex model routing:** [Choosing models and reasoning](https://developers.openai.com/codex/concepts/subagents#choosing-models-and-reasoning)
- **Model details:** [Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol), [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra), [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
- **Codex authentication:** [ChatGPT subscription access versus API-key usage](https://learn.chatgpt.com/docs/auth)
- **Codex plans, credits, and limits:** [Codex pricing](https://learn.chatgpt.com/docs/pricing)
- **Codex telemetry capability surface:** [App server](https://learn.chatgpt.com/docs/app-server)
- **Speed modes and Spark:** [Codex speed](https://learn.chatgpt.com/docs/agent-configuration/speed)
- **Long-workflow controls:** [Long-running work](https://learn.chatgpt.com/docs/long-running-work)
- **API-price diagnostic only:** [OpenAI API pricing](https://developers.openai.com/api/docs/pricing)
- **Prompt guidance:** [GPT-5.6 prompting best practices](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices)
