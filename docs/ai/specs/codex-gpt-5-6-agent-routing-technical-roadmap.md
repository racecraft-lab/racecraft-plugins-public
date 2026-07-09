# Codex GPT-5.6 Agent Routing Implementation Roadmap

**Route SpecKit Pro's Codex agents to the lowest-cost GPT-5.6 model and
reasoning effort that preserves their role-specific quality contract.**

This document defines the SPEC catalog for Codex GPT-5.6 agent routing. Each
SPEC maps 1:1 to a Feature / Acceptance-Criteria group in the source PRD
(`AC-N.*`) and is prepared for `$speckit-scaffold-spec G56R-NNN`.

**Source PRD:** [../../prd-codex-gpt-5-6-agent-routing.md](../../prd-codex-gpt-5-6-agent-routing.md)
**Roadmap MOC:** [codex-gpt-5-6-agent-routing-roadmap-MOC.md](codex-gpt-5-6-agent-routing-roadmap-MOC.md)
**Spec ID prefix:** `G56R-###`
**Proposed branch:** `codex/gpt-5-6-agent-routing`
**Status:** Draft; dependency graph approved 2026-07-09

---

## Roadmap Overview

The effort is decomposed into **8 specifications** across **5 dependency
tiers**.

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | G56R-001 | Authoritative research baseline and candidate matrix | Sequential spike |
| 2 | G56R-002 | Model x effort benchmark, cost accounting, and promotion contract | Sequential foundation |
| 3 | G56R-003 | Tier-aware installer defaults and explicit global override | Sequential; requires stable post-XPLAT-009 runtime |
| 4 | G56R-004, G56R-005, G56R-006, G56R-007 | Route four disjoint agent cohorts | Parallel after G56R-003; serialize shared regeneration |
| 5 | G56R-008 | Rebuild payload, reconcile shared assertions, run installed UAT, and prove release readiness | Sequential integration |

**Execution order:** G56R-001 -> G56R-002 -> G56R-003 ->
G56R-004 + G56R-005 + G56R-006 + G56R-007 -> G56R-008

**External prerequisite:** G56R-001 and G56R-002 may start immediately.
G56R-003 must scaffold against the authoritative installer/runtime that exists
after XPLAT-009 stabilizes; it must not reintroduce a deleted Bash helper.

### Research-backed starting matrix

This is a **candidate shortlist**, not a pre-approved final routing table.
G56R-002 evidence controls promotion.

| Agent | Current source baseline | Primary GPT-5.6 candidate | Initial effort comparison | Adjacent challenger |
|---|---|---|---|---|
| `phase-executor` | GPT-5.5 / xhigh | Sol | xhigh vs high | Terra |
| `implement-executor` | GPT-5.5 / xhigh | Sol | xhigh vs high | Terra |
| `analyze-executor` | GPT-5.5 / xhigh | Sol | xhigh vs high; max only after a measured failure | Terra |
| `checklist-executor` | GPT-5.5 / xhigh | Terra | xhigh vs high | Sol; Luna only if contract-safe |
| `uat-runbook-author` | GPT-5.5 / xhigh | Terra | xhigh vs high | Sol; Luna only if contract-safe |
| `clarify-executor` | GPT-5.5 / xhigh | Terra | xhigh vs high | Sol |
| `domain-researcher` | GPT-5.5 / xhigh | Terra | xhigh vs high | Sol |
| `codebase-analyst` | GPT-5.5 / low | Terra | low vs next supported lower effort | Luna for bounded scans |
| `spec-context-analyst` | GPT-5.5 / low | Terra | low vs next supported lower effort | Luna for bounded scans |
| `autopilot-fast-helper` | GPT-5.3 Codex Spark / effort omitted | Luna | low vs none when supported | Terra; retain current behavior if no 5.6 route passes |

### Promotion rule

- Deterministic role contract, grounding/evidence, and safety checks are hard
  gates.
- A candidate must have zero critical regressions and at least 95% of the
  current role-quality baseline.
- Among passing candidates, choose the lowest normalized cost per successful
  run; use latency as the tie-breaker.
- Start at the current effort and one level lower. Test `max` only for an
  unresolved quality-first failure.
- Run three live repeats per shortlisted configuration and expand only close or
  unstable comparisons.
- Evidence wins: Sol, Terra, or Luna is not forced into a role when it fails.

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
G56R-002 Model-Effort Benchmark and Promotion Harness
    |
    v
G56R-003 Tier-aware Installer Defaults and Explicit Override
    |
    +--> G56R-004 Quality-critical Executor Routing --------+
    +--> G56R-005 Structured-work Agent Routing ------------+
    +--> G56R-006 Read-only Reasoning Agent Routing --------+
    +--> G56R-007 Latency-first Helper Routing -------------+
                                                              |
                                                              v
                              G56R-008 Payload, Documentation, UAT, and Release Proof
```

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|---|---|---|---|---|
| G56R-001 | Research Baseline and Candidate Matrix | Pending | - | Ready to scaffold |
| G56R-002 | Model-Effort Benchmark and Promotion Harness | Pending | - | Blocked by G56R-001 |
| G56R-003 | Tier-aware Installer Defaults and Explicit Override | Pending | - | Blocked by G56R-002 and stable XPLAT-009 runtime |
| G56R-004 | Quality-critical Executor Routing | Pending | - | Blocked by G56R-003 |
| G56R-005 | Structured-work Agent Routing | Pending | - | Blocked by G56R-003 |
| G56R-006 | Read-only Reasoning Agent Routing | Pending | - | Blocked by G56R-003 |
| G56R-007 | Latency-first Helper Routing | Pending | - | Blocked by G56R-003 |
| G56R-008 | Payload, Documentation, UAT, and Release Proof | Pending | - | Blocked by G56R-004 through G56R-007 |

**Status legend:** Pending | Ready | In Progress | In Review | Complete |
Blocked

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
- Create a primary-source fact table from current OpenAI latest-model, Sol,
  Terra, Luna, pricing, migration, prompt-guidance, and Codex subagent pages.
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

- `docs/ai/research/` - dated GPT-5.6 research and candidate matrix
- `speckit-pro/codex-agents/*.toml` - read-only inventory source
- `tests/speckit-pro/layer6-efficiency/` - fixture-gap inventory source

---

### G56R-002: Model-Effort Benchmark and Promotion Harness

**Priority:** P1 | **Depends On:** G56R-001 | **Enables:** G56R-003 through G56R-007

**Goal:** Make role routing a replayable model x effort decision based on
quality, evidence, latency, tokens, credits, and normalized cost per success.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: unavailable (estimator operation absent) |
Production files: approximately 4 |
Total files: approximately 15 |
Budget result: re-estimate at scaffold; split fixture expansion from runner work if warned

**Scope:**

- Extend the Codex Layer 6 runner so callers can override both `model` and
  `model_reasoning_effort` without mutating agent TOMLs.
- Store requested/returned model, effort, environment, native token categories,
  credits when exposed, wall time, exit/completion state, and dated pricing
  inputs; calculate normalized cost per successful run without collapsing
  cached input and output into one misleading total.
- Add one role-specific fixture contract for each of the ten agents, with
  deterministic output/grounding/safety gates and a blinded semantic rubric.
- Add staged-run controls: three repeats per shortlist, bounded expansion for
  instability, live-mode budget, and a replayable consolidated result schema.
- Implement the approved non-inferiority promotion report and keep live calls
  outside default CI.
- INVEST/vertical-slice rationale: one executable benchmark path produces a
  complete promotion decision for any single agent before any route changes.

**Out of Scope:**

- Selecting or changing agent defaults.
- A general-purpose model benchmark unrelated to SpecKit Pro contracts.
- A mandatory LLM judge for deterministic facts.

**Key Files:**

- `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.sh` - current Codex benchmark entrypoint; use the active post-XPLAT-009 equivalent if migrated
- `tests/speckit-pro/layer6-efficiency/fixtures-codex/` - ten role fixtures
- `tests/speckit-pro/layer6-efficiency/lib/quality-scorer.sh` - layered scoring surface or active replacement
- `tests/speckit-pro/layer4-scripts/test-l6-codex-runner.sh` - deterministic runner contract coverage or active replacement

---

### G56R-003: Tier-aware Installer Defaults and Explicit Override

**Priority:** P1 | **Depends On:** G56R-002 and stable post-XPLAT-009 runtime |
**Enables:** G56R-004 through G56R-007

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

### G56R-004: Quality-critical Executor Routing

**Priority:** P1 | **Depends On:** G56R-003 | **Enables:** G56R-008

**Goal:** Route phase, implementation, and analyze/remediation work to the
lowest-cost passing configuration, starting with Sol.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: unavailable (estimator operation absent) |
Production files: 0 |
Total files: approximately 10 |
Budget result: re-estimate at scaffold; three disjoint TOMLs plus role evidence

**Scope:**

- Run the approved Sol xhigh/high baseline and Terra challenger matrix for
  `phase-executor`, `implement-executor`, and `analyze-executor`; test `max` only
  for a measured unresolved failure and only when supported.
- Score real Specify/Plan/Tasks, strict TDD implementation, and full Analyze
  remediation contracts, not generic coding prompts.
- Pin each winning model and effort independently in its TOML; update only
  cohort-specific descriptions, tests, and guidance required for truthfulness.
- Establish unchanged-prompt results first. Apply a minimal prompt cleanup only
  when its separate before/after record clears the same promotion bar.
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
- Cohort-specific structural/install assertions selected by G56R-003

---

### G56R-005: Structured-work Agent Routing

**Priority:** P1 | **Depends On:** G56R-003 | **Enables:** G56R-008

**Goal:** Route checklist remediation and UAT runbook authoring to the
lowest-cost passing configuration, starting with Terra.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: unavailable (estimator operation absent) |
Production files: 0 |
Total files: approximately 8 |
Budget result: re-estimate at scaffold; two role TOMLs plus evidence

**Scope:**

- Evaluate `checklist-executor` and `uat-runbook-author` on Terra at the current
  effort and one level lower; add Sol or Luna only when the role fixture makes
  the adjacent comparison credible.
- Require complete all-severity checklist remediation and executable,
  non-circular, acceptance-criteria-linked UAT runbooks.
- Pin independent winners while preserving workspace-write, error, and fail-open
  boundaries.
- Use unchanged-prompt baselines before any measured prompt cleanup and prove
  install, override, and rollback behavior for the cohort.
- INVEST/vertical-slice rationale: two structured-output mutators share a
  measurable contract and ship independently of deep executors and analysts.

**Out of Scope:**

- Quality-critical executors, read-only analysts, and latency helper.

**Key Files:**

- `speckit-pro/codex-agents/checklist-executor.toml`
- `speckit-pro/codex-agents/uat-runbook-author.toml`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex/` - cohort fixtures/results
- Cohort-specific structural/install assertions selected by G56R-003

---

### G56R-006: Read-only Reasoning Agent Routing

**Priority:** P1 | **Depends On:** G56R-003 | **Enables:** G56R-008

**Goal:** Route clarification, external research, codebase analysis, and project
context analysis independently, starting with Terra and preserving evidence
boundaries.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: unavailable (estimator operation absent) |
Production files: 0 |
Total files: approximately 12 |
Budget result: re-estimate at scaffold; four TOMLs plus bounded role fixtures

**Scope:**

- Evaluate Terra for `clarify-executor`, `domain-researcher`,
  `codebase-analyst`, and `spec-context-analyst`; use Sol for harder synthesis
  and Luna only for bounded scans that preserve the contract.
- Compare xhigh/high for current xhigh roles and low/the next supported lower
  effort for current low roles. Never rely on GPT-5.6's omitted medium default.
- Hard-gate read-only behavior, source-domain separation, citations/file
  locators, abstention, and structured return formats.
- Pin the lowest-cost winner per agent, not one forced cohort model; baseline
  before prompt cleanup and prove cohort install/override/rollback behavior.
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

### G56R-007: Latency-first Helper Routing

**Priority:** P1 | **Depends On:** G56R-003 | **Enables:** G56R-008

**Goal:** Decide whether Luna can replace the Spark helper while preserving its
bounded advisory contract and graceful unavailability behavior.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: unavailable (estimator operation absent) |
Production files: 0 |
Total files: approximately 6 |
Budget result: re-estimate at scaffold; single-agent vertical slice

**Scope:**

- Benchmark Luna low/none when supported against current Spark behavior and a
  Terra challenger on compression, triage, and query-drafting fixtures.
- Hard-gate read-only/advisory scope, concise return format, and prohibition on
  SDD reasoning or mutation.
- Explicitly set the winning effort so omission cannot inherit GPT-5.6 medium.
- Preserve autopilot's correct continuation when the optional helper cannot
  spawn; retain a non-Luna route when Luna fails the shared promotion rule.
- Establish an unchanged-prompt baseline before measured cleanup and prove
  install, override, and rollback behavior.
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

### G56R-008: Payload, Documentation, UAT, and Release Proof

**Priority:** P1 | **Depends On:** G56R-004, G56R-005, G56R-006, G56R-007 |
**Enables:** Release

**Goal:** Publish one internally consistent Codex payload whose ten-agent matrix
is proven in source, generated artifacts, install verification, and live UAT.

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
- On an entitled account, install the generated payload and complete at least
  one live representative workflow per cohort, recording returned model,
  effort, quality, wall time, token/credit cost, and safeguards.
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
| Model x effort evaluation | Layer 6 active Codex harness | Explicit model override, token categories, cost per success, all ten fixtures |
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
| Official pricing | Snapshot and date the current OpenAI pricing page for normalized comparisons |

## References

- **Source PRD:** [../../prd-codex-gpt-5-6-agent-routing.md](../../prd-codex-gpt-5-6-agent-routing.md)
- **Roadmap MOC:** [codex-gpt-5-6-agent-routing-roadmap-MOC.md](codex-gpt-5-6-agent-routing-roadmap-MOC.md)
- **Constitution:** [../../../.specify/memory/constitution.md](../../../.specify/memory/constitution.md)
- **Project standards:** [../../../AGENTS.md](../../../AGENTS.md) and [../../../CLAUDE.md](../../../CLAUDE.md)
- **OpenAI latest model:** [Using GPT-5.6](https://developers.openai.com/api/docs/guides/latest-model)
- **OpenAI migration guide:** [Upgrading to GPT-5.6 Sol](https://developers.openai.com/api/docs/guides/upgrading-to-gpt-5p6-sol)
- **Codex model routing:** [Choosing models and reasoning](https://developers.openai.com/codex/concepts/subagents#choosing-models-and-reasoning)
- **Model details:** [Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol), [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra), [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
- **Pricing:** [OpenAI API pricing](https://developers.openai.com/api/docs/pricing)
- **Prompt guidance:** [GPT-5.6 prompting best practices](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices)
