# Claude Code Agent Model Routing and Graceful Fallback Implementation Roadmap

**Select one evidence-backed preferred model/effort route and ordered qualified
fallbacks for each named Claude Code agent, resolve the first compatible route
from probed runtime capabilities at session preflight, and ship the complete
matrix in one consistent payload without changing any agent's safety, tool, or
mutation contract.**

This document defines the SPEC catalog for capability-based Claude Code agent
routing. Each SPEC maps to an explicit acceptance-criteria subset in the source
PRD and is prepared for `$speckit-scaffold-spec CAR-NNN`.

**Source PRD:** [../../prd-claude-agent-routing.md](../../prd-claude-agent-routing.md)
**Roadmap MOC:** [claude-agent-routing-roadmap-MOC.md](claude-agent-routing-roadmap-MOC.md)
**Shared parity contract:** [agent-routing-parity-contract.md](agent-routing-parity-contract.md)
**Shared manifest schema:** [../research/agent-route-candidate-manifest.schema.json](../research/agent-route-candidate-manifest.schema.json)
**Spec ID prefix:** `CAR-###`
**Proposed branch:** `claude/agent-routing-fallback`
**Status:** Active; dependency graph approved 2026-07-12; CAR-001 is complete
and archived after PRs #350 and #362; CAR-002 is complete and archived after
PR #369; CAR-003 is complete and archived after PR #385; CAR-004 is complete
and archived after PR #401; CAR-005 is complete and archived after the stacked
PRs #411 and #412; CAR-006 is ready

**Parity note:** This roadmap now targets 14 required shipped Claude agents
plus the optional helper. Shared roles mirror the companion Codex routing
roadmap (PR #330 as amended by parity PR #338); Claude-only secure
feedback-sweep roles are an explicit platform-specific exception. The frozen
CAR-003 v1 11+helper corpus remains historical evidence, while the
[current-source successor roster](../research/claude-subagent-runtime-rebaseline.md)
binds the live 14-agent source tree for CAR-006 onward.

---

## Roadmap Overview

The effort is decomposed into **12 specifications** across **9 dependency
tiers**.

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | CAR-001 | Candidate route baseline and role contracts | Sequential spike |
| 2 | CAR-002 | Capability probing, telemetry profile, and exact treatment | Sequential foundation |
| 3 | CAR-003 | Evaluation runner, fixtures, scoring, and statistics | Sequential foundation; two required work packages |
| 4 | CAR-004 | Policy controls and adaptive comparators | Sequential foundation |
| 5 | CAR-005 | Availability, fallback, and recovery simulation | Sequential foundation |
| 6 | CAR-006 | Route-policy manifest, materializer, session preflight, and override validation | Sequential framework slice |
| 7 | CAR-007, CAR-008, CAR-009, CAR-010 | Qualify four disjoint agent cohorts | Parallel after CAR-006; serialize shared regeneration |
| 8 | CAR-011 | Compose final identities, rebuild payload, run installed UAT, and prove release readiness | Sequential integration |
| 9 | CAR-012 | Reconcile the mirrored evaluation contracts with G56R-003 | Joint change; must land on both platforms together |

**Execution order:** CAR-001 -> CAR-002 -> CAR-003 -> CAR-004 ->
CAR-005 -> CAR-006 -> CAR-007 + CAR-008 + CAR-009 + CAR-010 ->
CAR-011

**Implementation boundary:** This sequence has no external prerequisite, but
its internal dependencies still apply: CAR-001 through CAR-005 and their
official-source evidence amendments are complete and archived. CAR-006 must
revalidate the source ledger and consume the current-source v2 roster before
route-policy work begins. No installer exists or is introduced on the Claude
side - agents
auto-load from the shipped payload - so CAR-006 builds the route-policy
manifest, materializer drift gate, and read-only session-preflight resolver
instead of a copy step.

### Evidence authority

CAR evidence must satisfy the shared parity contract and manifest schema.
Platform capability claims may cite only canonical Anthropic documentation
under `code.claude.com/docs/**` or `platform.claude.com/docs/**`. Repository
state, pinned runtime captures, and governed evaluations remain authoritative
for production qualification, but cannot establish undocumented platform
behavior. The historical CAR-001 report remains available for provenance; its
v2 amendment is the active handoff for downstream specifications.

### Candidate-route starting hypotheses

This table records hypotheses, not a pre-approved route table. CAR-001 derives
the candidate set from official model guidance and probed capability evidence.
CAR-002 freezes the executable subset before CAR-003 scores outcomes. Current
baselines are the shipped frontmatter pins (all at `effort: max`); the effort
search itself starts at the documented default per AC-2.1.

| Agent | Current source baseline | Starting hypothesis | Effort search | Required challengers |
|---|---|---|---|---|
| `phase-executor` | opus / max | opus | default, ascend if needed, then descend | Every role-eligible probed model, including fable when probed available |
| `implement-executor` | opus / max | opus | default, ascend if needed, then descend | Every role-eligible probed model, including fable when probed available |
| `analyze-executor` | opus / max | opus | default, ascend if needed, then descend | Every role-eligible probed model, including fable when probed available |
| `checklist-executor` | opus / max | opus | default, ascend if needed, then descend | Every role-eligible probed model, including bounded-work haiku |
| `artifact-author` | opus / max | opus | default, ascend if needed, then descend | Every role-eligible probed model, including bounded-work haiku |
| `uat-runbook-author` | sonnet / max | sonnet | default, ascend if needed, then descend | Every role-eligible probed model, including bounded-work haiku |
| `clarify-executor` | opus / max | opus | default, ascend if needed, then descend | Every role-eligible probed model |
| `domain-researcher` | sonnet / max | sonnet | default, ascend if needed, then descend | Every role-eligible probed model |
| `codebase-analyst` | sonnet / max | sonnet | default, ascend if needed, then descend | Every role-eligible probed model, including bounded-work haiku |
| `spec-context-analyst` | sonnet / max | sonnet | default, ascend if needed, then descend | Every role-eligible probed model, including bounded-work haiku |
| `consensus-synthesizer` | sonnet / max | sonnet | default, ascend if needed, then descend | Every role-eligible probed model, including bounded-work haiku |
| `gate-validator` | sonnet / max | sonnet | default, ascend if needed, then descend | Every role-eligible probed model, including bounded-work haiku |
| `sweep-classifier` | opus / max | opus | default, ascend if needed, then descend | Every role-eligible probed model that preserves the broker-only trust boundary |
| `sweep-analyst` | opus / max | opus | default, ascend if needed, then descend | Every role-eligible probed model that preserves the broker-only trust boundary |
| `autopilot-fast-helper` | None - net-new parity addition (Codex baseline: Spark helper) | haiku with explicit low effort | explicit effort search | Every probed latency-oriented candidate plus a validated no-helper path |

### Route, evidence, and identity contract

A route is a complete qualified tuple, not a model name:

```text
route = explicit model (shipped alias + qualified resolved model ID)
      + explicit effort
      + instruction_hash
      + required model and modality capabilities
      + tool and skill contract
      + mutation contract (disallowedTools, tools omission, maxTurns)
      + supported client range
      + qualification evidence
```

Fallback may change only the approved model and effort for the same named
agent. It preserves instructions, output contract, mutation boundary, tools,
and skills. Ordered fallback is SpecKit Pro policy honored at dispatch time
through the documented per-invocation model parameter; it is not represented
as a native subagent-frontmatter fallback field, and shipped agent files are
never mutated at runtime.

| Identity | Created by | Required contents |
|---|---|---|
| `agent_contract_id` | CAR-001 | Named role plus safety, grounding, mutation, tool, and output contracts |
| `candidate_route_id` | CAR-001/CAR-002 | Candidate model/effort, contract and instruction hashes, required capabilities, and rationale |
| `telemetry_profile_id` | CAR-002 | Pinned client and mandatory, conditional, derived, and unavailable fields |
| `runtime_capability_snapshot_id` | CAR-002 or session preflight | Client version, probed model IDs, alias-to-ID bindings, supported efforts, probe method, timestamp, and raw evidence |
| `experiment_policy_id` | CAR-003 | Corpora, partitions, scorers, analysis plan, budgets, terminal policy, and treatment controls |
| `execution_trace_id` | CAR-003 | Assigned route, effective-route evidence, result, raw resource observations, retries, terminal state, and treatment integrity |
| `route_resolution_id` | CAR-002 schema; CAR-003/CAR-006 records | Preferred and effective route, fallback index, reason, snapshot, attempted routes, and timestamp |
| `resolved_agent_policy_id` | CAR-006 schema/fixtures; CAR-011 final records | Exact shipped frontmatter-plus-body content hash and selected effective route |
| `agent_route_policy_id` | CAR-007 through CAR-010 | Named agent, preferred route, ordered qualified fallbacks, hard contract, evidence, client bounds, and invalidation rules |
| `core_routing_policy_id` | CAR-011 | Ordered mapping of the fourteen required named agents to final route-policy IDs |
| `optional_helper_policy_id` | CAR-011 | Final helper route policy, approved fallbacks, and no-helper contract |
| `resolved_installation_id` | CAR-011 | dist/claude payload tree hash plus installed-cache proof binding shipped agents to resolved policies |
| `release_policy_id` | CAR-011 | Final core/helper identities, preflight/materializer version, evidence lock, UAT, invalidation rules, and bounded claims |

Early traces must not require the final aggregate identities before CAR-011
creates them.

### Qualification and release-decision rule

- Deterministic role contract, grounding/evidence, and safety checks are hard
  gates; quality and reliability floors plus production non-inferiority pass
  before any resource ranking.
- The selection rule among passing candidates is one predeclared
  environment-independent Pareto rule over the raw token vector (input,
  cache-write by TTL class, cache-read, output) plus duration, retries, and
  compaction, applied only after absolute quality and reliability floors and
  task-paired cluster-adjusted non-inferiority pass. A tie, mixed dominance,
  incomplete evidence, or statistical uncertainty is inconclusive and yields no
  qualification; no weighted ranking is forced. The complete raw vector,
  duration, retries, and compaction are always reported. Amended 2026-07-24
  under CAR-003 from the previous price-weighted scalar, for logical parity with
  G56R-003; see PRD AC-2.5.
- Effort search starts at the documented default (`high`), ascends to the
  first stable pass when necessary, then descends and boundary-retests to the
  lowest stable ordinary effort. The current uniform `max` pins are the
  immutable comparator, not the search origin.
- Amended 2026-09-02: the shipped pins are no longer uniform `max`.
  `consensus-synthesizer` ships at `high` under the role-contract admission
  path, because its body forbids its own analysis and evidence search and its
  output is program-parsed. The comparator is unchanged: the immutable
  `car-003-role-corpus.json` source digests and the uniform-max configuration
  recorded at git 45147ad15. See
  `docs/ai/research/prompt-audit-roster-decision.md`.
- Exact treatment means real `speckit-pro:<name>` dispatch or a canonical
  materializer rendering proven equivalent; bare prompt emulation is
  smoke-only. The environment contract freezes fast mode off, a pinned client
  range, a pinned parent-session model and effort, and an unset
  `CLAUDE_CODE_SUBAGENT_MODEL`; scored campaigns run API-key-authenticated
  with at least one subscription-authenticated installed smoke row, and no
  run produces a plan-based claim.
- Screening, selection, cohort lock, and integrated confirmation use disjoint
  partitions; the untouched confirmation corpus is used exactly once.
- A platform-initiated route change - any observed model ID differing from the
  resolved qualified ID, including alias re-pointing - makes a run non-scorable
  for the requested route and is never reported as plugin fallback.
- Unpinned, adaptive, and orchestration-changing controls are frozen before
  cohort selection and compared with the final static core during integrated
  confirmation; a dominant control restricts efficiency wording.
- Evidence wins: no model generation, alias, or product tier is forced into a
  role when it fails.

## Grounded Platform Facts

Verified against the live Claude Code documentation on 2026-07-30 (CLI 2.1.220)
during the CAR-005 autopilot run. **Every spec from CAR-006 onward inherits these;
read this section before writing a requirement about model, effort, or override
behaviour.** Three of the four facts below contradicted a requirement that had
already been written and reviewed, so treat platform behaviour as something to
verify rather than assume.

**PF-1 — the `CLAUDE_CODE_SUBAGENT_MODEL` override is NOT unconditional.** It is
first in the resolution order (env var → per-invocation `model` parameter →
subagent frontmatter `model` → main conversation model), and its scope is "all
subagents, agent teams, and agents in a workflow". But Claude Code checks it, the
per-invocation parameter, and frontmatter against the organization
`availableModels` allowlist and **skips a value resolving to an excluded model,
running the subagent on the *inherited* model instead**. Two consequences for any
override-validation requirement: an override can fail to take effect, so "the
override wins" is false as an unconditional claim; and the documented fallback
target is the *inherited* model — the docs do **not** say resolution resumes at
the per-invocation parameter, so reading it that way is inference. Also note the
variable sets a **model only**: it cannot supply an `effort`, so a dispatch tuple
under an override is part-override, part-retained.

**PF-2 — an unsupported effort DEGRADES silently; it is not rejected.** "If you
set a level the active model does not support, Claude Code falls back to the
highest supported level at or below the one you set." Organization effort caps
clamp the same way, and the warning is **suppressed** under `--output-format json`
or `stream-json` and in background agents. Supported sets: `low|medium|high|xhigh|max`
on Fable 5, Opus 5, Sonnet 5, Opus 4.8 and Opus 4.7; only `low|medium|high|max`
on Opus 4.6 and Sonnet 4.6 (**no `xhigh`**); and models outside that table support
**no effort at all**, including Haiku 4.5, Claude 3, Sonnet 4.0/4.5 and Opus
4.0/4.1. The effort scale is also calibrated per model, so the same level name
does not denote the same underlying value across models. **Implication for
qualification (CAR-007 through CAR-010): a route whose effort silently degrades is
not a qualified route**, because the tuple that ran is not the tuple the policy
pinned and no result field records the difference. CAR-005 therefore rejects such a
route at preflight as a deliberate policy divergence from runtime behaviour — a
divergence, not a mirror, and future specs must keep it labelled that way.
`ultracode` is **not** a model effort level (it sends `xhigh` plus workflow
orchestration) and must not appear in an effort enum.

**PF-3 — aliases re-point, by three distinct mechanisms.** "Aliases point to the
recommended version for your provider and update over time. To pin to a specific
version, use the full model name." The documented mechanisms are provider/version
drift (the docs record `opus` moving at v2.1.219 and v2.1.207), per-family env
redefinition via `ANTHROPIC_DEFAULT_OPUS_MODEL` and siblings, which redefines the
alias process-wide *underneath* the whole resolution order, and **allowlist
substitution** — on the Anthropic API and Claude Platform on AWS a family alias
"resolves to the newest version of its family that the allowlist permits" and
announces both requested and substituted models, while Bedrock, Google Cloud and
Foundry reject or replace instead. So substitution behaviour is
**provider-dependent**. This is why a route tuple must pin a qualified resolved
model ID and not merely an alias. `modelUsage` in the result message is the
authoritative post-hoc record of what an alias actually resolved to; the stderr
remap warning is suppressed under `json`/`stream-json`.

**PF-4 — CAR-002 did not pin the unavailable-model platform fact.** The CAR-005
scope line below says its reason codes are "aligned with the CAR-002 probed
unavailable-model behavior". CAR-002 in fact produced a **three**-member
vocabulary — `hard_rejection`, `soft_remap`, `undetermined` — recorded as
`labeled_inference` rather than `observation`; CAP-Q5 is `answered` only when some
surface returns a non-`undetermined` outcome; CAP-Q6 (route-change detection) is
hardcoded `status: "open"`; and **no live capture is committed to the tree**. Any
spec claiming alignment with a determinate CAR-002 observation is claiming more
than exists. CAR-005 pins its semantics *ahead of* the platform fact, which is
coherent for a synthetic simulation but must be stated rather than glossed. Note
also that `undetermined` must map to probe-unavailable, never to probe-success —
the fail-open direction was a live defect caught in CAR-005.

**Parity:** PF-1 through PF-4 are platform facts, not Claude-specific design, so
they apply equally to the Codex half of this catalog. They are recorded here only,
because a Codex-side edit is a deliberate joint two-platform landing under the
shared parity contract. **G56R-005 onward should carry the same section**; raise it
as a joint change rather than copying unilaterally.

---

## Reviewability Contract

Every implementation spec must fit the repository's human review budget. Warn
above approximately 400 reviewable production LOC, 6 production files, or 15
total files; block-sized work must split unless an existing typed exception
legitimately applies. Generated payloads, tests, and documentation still count
toward reviewer load even where they do not count as production LOC.

**Estimator advisory:** The Python-authoritative `estimate-spec-size`
operation was run on 2026-07-12 with the documented convention: one user
story, the declared total-file estimate, the Scope-bullet count excluding the
INVEST line as functional requirements, and `new_vs_modify=modify`; CAR-001
uses the spike flag and CAR-010 uses `new` because its helper agent is
net-new. CAR-003 (502 LOC, warn) must preserve its two declared work packages,
and CAR-010 (450 LOC, warn) must preserve its declared helper-definition
versus qualification-evidence split. Every scaffold reruns the estimator when
scope or file counts change.

## Dependency Graph

```text
CAR-001 Candidate Route Baseline and Role Contracts
    |
    v
CAR-002 Capability Probing, Telemetry Profile, and Exact Treatment
    |
    v
CAR-003 Evaluation Runner, Fixtures, Scoring, and Statistics
    |
    v
CAR-004 Policy Controls and Adaptive Comparators
    |
    v
CAR-005 Model Availability, Fallback, and Recovery Simulation
    |
    v
CAR-006 Route-policy Manifest, Materializer, Preflight, and Override
    |
    +--> CAR-007 Quality-critical Executor Routing ---------+
    +--> CAR-008 Structured-work Agent Routing -------------+
    +--> CAR-009 Read-only and Orchestration Routing -------+
    +--> CAR-010 Optional Helper and No-helper Path --------+
                                                            |
                                                            v
                 CAR-011 Final Composition, Installed UAT, and Release Proof

CAR-003 --+
          +--> CAR-012 Mirrored Evaluation-Contract Reconciliation
G56R-003 -+     (joint change; lands with G56R-012 on both platforms)
                Not on the CAR-004..CAR-011 critical path. Required before any
                analysis pools outcomes across the two platforms.
```

## Progress Tracking

### Current-source roster rebaseline (2026-08-30)

The CAR-003 v1 qualification corpus is immutable historical evidence for the
11 required agents plus optional helper that existed when it was captured. It
is not silently expanded or rehashed. The separately versioned
`claude-agent-roster-rebaseline-v2.json` binds the exact 14 shipped source
digests, cohorts, trust boundaries, and memory scopes plus the still-optional
helper. CAR-006 must consume this v2 roster and retain the v1 corpus reference
and digest for provenance. `artifact-author` joins structured work;
`sweep-classifier` and `sweep-analyst` form a broker-only,
untrusted-feedback cohort. Native runtime fallback remains an explicit
operator-controlled recovery option, never a plugin-owned qualification
substitute, and an unqualified delivered model is release-ineligible.

| Spec | Name | Status | Workflow File | Next Phase |
|---|---|---|---|---|
| CAR-001 | Candidate Route Baseline and Role Contracts | Complete / Archived | [.process/CAR-001-workflow.md](.process/CAR-001-workflow.md) | PR #350 and evidence-parity amendment PR #362 merged; canonical evidence lives under `docs/ai/research/` |
| CAR-002 | Capability Probing, Telemetry Profile, and Exact-Treatment Contract | Complete / Archived | [.process/CAR-002-workflow.md](.process/CAR-002-workflow.md) | PR #369 merged; canonical snapshot, telemetry profile, trace schema, and validators live outside `specs/**` |
| CAR-003 | Evaluation Runner, Fixtures, Scoring, and Statistical Analysis | Complete / Archived | [.process/CAR-003-workflow.md](.process/CAR-003-workflow.md) | PR #385 merged; canonical materializer, evaluation evidence, qualification modules, and validators live outside `specs/**` |
| CAR-004 | Policy Controls and Adaptive Comparators | Complete / Archived | [.process/CAR-004-workflow.md](.process/CAR-004-workflow.md) | PR #401 merged; frozen control registry, comparison rule, fixtures, and validators live outside `specs/**`. T062's three live smokes were never run, so SC-009, SC-026, SC-027, SC-029, SC-030, and SC-031 stay unevidenced; the operator runbook is [.process/CAR-004-live-smoke-runbook.md](.process/CAR-004-live-smoke-runbook.md) |
| CAR-005 | Model Availability, Fallback, and Recovery Simulation | Complete / Archived | [.process/CAR-005-workflow.md](.process/CAR-005-workflow.md) | Stacked PRs #411 and #412 merged; the reference simulator, three closed contracts, the eighteen-case corpus, and the Layer 4 owner live outside `specs/**`. The simulator declares `POLICY_SCHEMA_PATH` and `SNAPSHOT_SCHEMA_PATH` but reads neither, so it validates the report it emits and not the policy or snapshot it accepts; CAR-006 inherits that gap |
| CAR-006 | Route-policy Manifest, Materializer, Preflight, and Strict Override | Ready | - | CAR-005 dependency satisfied by PRs #411 and #412; current-source v2 roster prerequisite satisfied 2026-08-30 |
| CAR-007 | Quality-critical Executor Routing | Pending | - | Blocked by CAR-006 |
| CAR-008 | Structured-work Agent Routing | Pending | - | Blocked by CAR-006 |
| CAR-009 | Read-only Reasoning and Orchestration-support Agent Routing | Pending | - | Blocked by CAR-006 |
| CAR-010 | Optional Latency-first Helper Routing and No-helper Path | Pending | - | Blocked by CAR-006 |
| CAR-011 | Payload, Installed Skill UAT, Fallback Proof, and Release Integration | Pending | - | Blocked by CAR-007 through CAR-010 |
| CAR-012 | Mirrored Evaluation-Contract Reconciliation with G56R-003 | Pending | - | Raised 2026-07-26 from CAR-003 open coordination items; joint change with G56R-012 |

**Status legend:** Pending | Ready | In Progress | In Review | Complete | Blocked

---

## Specification Sections

### CAR-001: Candidate Route Baseline and Role Contracts

**Priority:** P1 | **Depends On:** None | **Enables:** CAR-002

**Implementation Status:** Complete / Archived. The runtime-neutral research
spike merged in PR #350 on 2026-07-15 at
`725be949b856724a073622900bd168d29b2f4603`; the active spec folder was removed
in `.specify/memory/archive-reports/2026-07-15-car-001-post-merge-hygiene.md`.
Canonical artifacts now live at `docs/ai/research/claude-agent-route-candidates.md`
and `docs/ai/research/claude-agent-route-candidate-manifest.json`. The
official-source evidence parity amendment merged in PR #362 on 2026-07-16.
CAR-002 must consume that schema-v2 amendment and pass its source-ledger gate
before it begins capability probing.

**Goal:** Produce the dated, cited candidate-route and role-contract handoff
needed for capability probing without changing shipped defaults.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 0 (spike) | Suggested slices: 1 | Status: ok |
Production files: 0 | Total files: approximately 3 |
Budget result: research spike; time-boxed, LOC sizing not applicable

**Scope:**

- Inventory the eleven current `speckit-pro/agents/*.md` definitions plus the
  net-new `autopilot-fast-helper` contract derived from the Codex helper under
  the parity principle, recording each agent's immutable production route or
  its recorded absence, instructions, role boundary, safety/grounding/mutation
  contract (`disallowedTools`, `tools` omission, `maxTurns`), output contract,
  expected tool/skill use, and representative tasks.
- Publish a versioned `agent_route_candidate_manifest` covering all twelve
  named agents. Create `agent_contract_id` and provisional
  `candidate_route_id` records for every agent. Each candidate records the
  shipped alias plus expected resolved model ID, an explicit effort,
  instruction hash, required capabilities, mutation contract, rationale, known
  incompatibilities, evidence requirements, and invalidation triggers
  including alias re-pointing.
- Distinguish project-level candidate eligibility from environment-time
  availability. Record preferred-route hypotheses and fallback-candidate
  requirements without claiming that any candidate is executable; `fable`
  enters executor-class candidate sets and is excluded only by recorded probe
  or contract evidence.
- Record the immutable production-route inputs (the eleven current frontmatter
  alias/effort tuples and content hashes at the pinned plugin version; each
  alias→dated-ID resolution is deferred to CAR-002 probing, not recorded as
  settled) that CAR-003 will bind into the sole candidate and integrated
  comparator before screening.
- Build a primary-source fact table from official Anthropic subagent,
  model-configuration, effort, fast-mode, authentication, cost/monitoring, and
  pricing documentation. Label every undocumented behavior - including what
  happens when frontmatter names an unavailable model, and how alias
  re-pointing manifests - as an inference, open question, or proposed SpecKit
  Pro policy.
- Deliver the role contracts, provisional candidate manifest, fixture backlog,
  two-current/ten-missing fixture inventory, telemetry requirements,
  capability questions, and independent go/no-go handoff to CAR-002.
- INVEST rationale: the spike closes the research uncertainty that blocks safe
  capability probing and ends without depending on later telemetry results.

**Out of Scope:**

- Agent frontmatter, prompt, payload, or default changes.
- Live corpus execution, qualification, or fallback ordering.

**Key Files:**

- [proposed] `docs/ai/research/claude-agent-route-candidates.md`
- `speckit-pro/agents/*.md` - read-only inventory source
- `speckit-pro/codex-agents/autopilot-fast-helper.toml` - parity contract source
- `tests/speckit-pro/layer6-efficiency/` - current fixture-gap inventory source

---

### CAR-002: Capability Probing, Telemetry Profile, and Exact-Treatment Contract

**Priority:** P1 | **Depends On:** CAR-001 | **Enables:** CAR-003

**Goal:** Freeze the executable candidate set and a trustworthy trace contract
for the pinned Claude Code client before outcome-bearing evaluation.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 265 | Suggested slices: 1 | Status: ok |
Production files: 0 | Total files: approximately 10 |
Budget result: re-estimate at scaffold; probe, profile, and schema libraries

**Scope:**

- Implement `runtime_capability_snapshot` capture: a bounded exact invocation
  probe per candidate route (`claude -p --model <alias-or-id>` on a minimal
  fixed canary), plus the API models endpoint when the environment is
  API-key-authenticated. Record probed model IDs, alias-to-ID bindings,
  supported efforts by configuration acceptance, client version, probe
  method, timestamp, and raw evidence.
- Probe and record the undocumented unavailable-model behavior (hard error
  versus silent substitution) as a pinned platform fact; its result shapes the
  CAR-005 reason codes.
- Publish `telemetry_profile_id` for the pinned client: effective model from
  the per-model usage breakdown and transcript per-message records is
  `stable_native`; the raw token vector including cache-write TTL classes and
  cache-read is `stable_native`; client-side cost estimates are `derived`;
  effective reasoning effort is `derived_from_controlled_configuration` and
  never a returned value; nulls are preserved.
- Define `route_resolution_id` and exact-treatment replay schemas binding the
  named agent, explicit model and effort, instruction hash, mutation contract,
  dispatch namespace, parent-session configuration, client version, fast-mode
  state, and env-override proof (`CLAUDE_CODE_SUBAGENT_MODEL` unset).
- Define platform route-change detection: any observed model ID differing from
  the resolved qualified ID, including alias re-pointing, is recorded
  separately from resolver fallback and marks the run non-scorable for the
  requested route.
- Record the authentication mode of every run (API-key for scored campaigns,
  subscription for installed smoke) in the environment snapshot without
  producing plan-based claims.
- Validate success, null, unavailable, and misdelivery records with synthetic
  replay before any live scoring.
- INVEST rationale: one probing/telemetry seam gives every later cohort the
  same trustworthy treatment evidence without touching agent policies.

**Out of Scope:**

- Corpus execution, scoring, statistics, and fallback ordering.
- Payload or guidance changes.

**Key Files:**

- [proposed] `tests/speckit-pro/layer6-efficiency/lib/claude_capabilities.py`
- [proposed] `tests/speckit-pro/layer6-efficiency/lib/claude_trace_schema.py`
- [proposed] `tests/speckit-pro/unit/test-efficiency-claude-telemetry.py`
- `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py` - current runner (read-only reference)

---

### CAR-003: Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

**Priority:** P1 | **Depends On:** CAR-002 | **Enables:** CAR-004

**Goal:** Qualify preferred and fallback candidates reproducibly on governed
fixtures without consuming integrated-confirmation data.

**Reviewability Budget:** Primary surface: harness/fixtures |
Projected reviewable LOC: 502 | Suggested slices: 2 | Status: warn |
Production files: 0 | Total files: approximately 20 |
Budget result: warning-sized; must preserve the two declared work packages
below when scaffolded

**Required Work Package A - Treatment runner and materializer:**

- Replace prompt emulation for qualification with real dispatch: installed-
  plugin `claude -p` sessions that spawn `speckit-pro:<name>` and prove the
  spawn from the transcript (reusing the Layer 7 transcript-parsing approach),
  with the per-model usage breakdown proving the effective model.
- Implement the canonical Python materializer that parses `agents/*.md` into a
  canonical policy structure, renders equivalent evaluation configurations,
  and later backs the CAR-006 frontmatter drift gate.
- Classify treatment misdelivery separately from candidate quality; emit
  replayable `execution_trace_id` records carrying the raw token vector
  (input, cache-write by TTL class, cache-read, output), duration, retries,
  and terminal state.
- Demote the current prompt-emulation path to explicitly labeled smoke
  evidence; historical results remain `non_release_evidence`.
- Isolate cache state between arms so one arm cannot warm another's cache;
  billed cache writes make crossover directly distortive.

**Required Work Package B - Fixtures, scoring, and statistics:**

- Expand from two current role fixtures to a governed twelve-role corpus under
  `fixtures/<agent>/`. Use blinded adjudication for candidate quality failure,
  treatment-delivery failure, invalid fixture, invalid scorer, and
  infrastructure failure. A fixture/scorer change versions it and invalidates
  affected results.
- Add a gitignore allow rule so consolidated baselines
  (`results/consolidated-*.json`) commit while per-run outputs stay ignored,
  mirroring the committed Codex baseline convention.
- Freeze `experiment_policy_id`: disjoint screening/selection/cohort-lock/
  confirmation partitions, workload strata and weights from pre-treatment
  properties, the powered long-horizon stratum, acceptance checker, margins,
  alpha/power/multiplicity, task-level clustering, attrition thresholds, and
  `inconclusive => no qualification`.
- Bind the immutable production comparator: repository revision, plugin
  version, the eleven current frontmatter alias/effort tuples (dated-ID
  resolution supplied by the CAR-002 runtime capability snapshot, not the
  frontmatter), instruction hashes, mutation contracts, client version, and
  corpus snapshot.
- Implement A1 (documented-default effort screening), A2 (within-model effort
  boundary search), A3 (frozen pair comparison), Stage B (bounded prompt
  interaction), and Stage C (cohort locks) with the predeclared price-weighted
  scalar plus complete raw-vector reporting.
- Enforce campaign budgets: maximum raw-token use, wall time, candidate count,
  futility rules, racing method, and confirmation-entry cap frozen before
  outcome-bearing runs.
- Publish replayable statistics with task-level paired inference and the
  frozen analysis plan; no post-hoc threshold changes.
- INVEST rationale: the runner/materializer seam and the fixture/statistics
  seam are separable, independently testable, and jointly sufficient for every
  cohort spec.

**Out of Scope:**

- Final route policies, shipped defaults, and release confirmation.
- Production preflight and guidance changes.

**Key Files:**

- `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py` - current runner to demote to smoke
- [proposed] `tests/speckit-pro/layer6-efficiency/lib/agent_materializer.py`
- [proposed] `tests/speckit-pro/layer6-efficiency/lib/statistical_analysis.py`
- `tests/speckit-pro/layer6-efficiency/fixtures/` - two current dirs; ten proposed
- `tests/speckit-pro/layer6-efficiency/.gitignore` - allow rule for consolidated baselines
- [proposed] `tests/speckit-pro/unit/test-efficiency-claude-runner.py`

---

### CAR-004: Policy Controls and Adaptive Comparators

**Priority:** P1 | **Depends On:** CAR-003 | **Enables:** CAR-005

**Goal:** Define, exact-treatment validate, and freeze the policy-level
controls that bound the final static-policy efficiency claim.

**Reviewability Budget:** Primary surface: harness/fixtures |
Projected reviewable LOC: 250 | Suggested slices: 1 | Status: ok |
Production files: 0 | Total files: approximately 10 |
Budget result: re-estimate at scaffold; control fixtures plus registry entries

**Scope:**

- Define and content-address three frozen controls: unpinned (agents with
  `model` omitted or `inherit`, riding the session model), adaptive (a frozen
  escalation/de-escalation policy over qualified routes exercised through the
  documented dispatch-time model parameter), and orchestration-changing (a
  parallel multi-agent execution mode evaluated at policy level only).
- Freeze each control's execution contract, parameters, observable escalation
  signals, retry and cancellation bounds, and evidence requirements; adaptive
  controls cannot choose a model or effort outside the frozen candidate set.
- Freeze control-eligibility floors, dominance metrics and margins, confidence
  method, multiplicity position, and the untouched comparison partition
  CAR-011 will use.
- Freeze the messaging consequence: a materially dominant qualified control
  restricts release wording to measured improvement over the previous static
  baseline, never "efficient", "optimal", or "best measured".
- Validate control execution and telemetry through synthetic replay and smoke
  runs without consuming selection or confirmation partitions.
- INVEST rationale: controls are pure evaluation fixtures - freezing them
  early prevents post-hoc comparator construction without touching any
  shipped policy.

**Out of Scope:**

- Concluding dominance (CAR-011 owns the comparison).
- Any production adaptive routing feature.

**Key Files:**

- [proposed] `tests/speckit-pro/layer6-efficiency/fixtures-controls/`
- [proposed] analysis-plan registry entries under `tests/speckit-pro/layer6-efficiency/`
- [proposed] `tests/speckit-pro/unit/test-efficiency-claude-controls.py`

---

### CAR-005: Model Availability, Fallback, and Recovery Simulation

**Priority:** P1 | **Depends On:** CAR-004 | **Enables:** CAR-006

**Goal:** Prove bounded resolution and recovery semantics synthetically before
real route policies exist.

**Reviewability Budget:** Primary surface: harness/fixtures |
Projected reviewable LOC: 257 | Suggested slices: 1 | Status: ok |
Production files: 0 | Total files: approximately 10 |
Budget result: re-estimate at scaffold; replay fixtures plus reason-code tests

**Scope:**

- Build fixture route policies that simulate: preferred model absent from the
  probed environment (including a `fable`-unavailable case), effort
  unsupported for a model, probe unavailable, exact invocation probe success
  and failure, alias re-pointing, platform route change, and an unqualified
  `CLAUDE_CODE_SUBAGENT_MODEL` override.
- Define stable reason codes (`preferred_model_unavailable`,
  `effort_unsupported`, `capability_probe_unavailable`,
  `treatment_probe_failed`, `no_safe_route`) aligned with the CAR-002 probed
  unavailable-model behavior. **Amended 2026-07-30 (see PF-4):** CAR-002 recorded
  that behaviour as *labeled inference* over a three-member vocabulary with no
  committed live capture, so this alignment is with CAR-002's **vocabulary and
  detection rule**, not with a pinned platform observation. CAR-005 pins its
  semantics ahead of the platform fact. `effort_unsupported` is likewise a
  deliberate **preflight qualification** decision, not a mirror of runtime
  behaviour, because the runtime silently degrades an unsupported effort (PF-2).
- Reject fallback loops, unqualified adjacent models, generic-agent
  substitution, and silent `inherit` materialization; bound probe attempts,
  retries, and fan-out.
- Simulate no-safe-route behavior as report-only: the preflight emits the
  unresolved agent, attempted routes, rejection reasons, and remediation, and
  never mutates shipped agent files; consumer recovery is the previous plugin
  release.
- Simulate helper-unavailable behavior: the helper is simply not consulted and
  the validated no-helper path continues without failing required-agent
  resolution.
- Prove retry exhaustion, rollback guidance, and deterministic replay of every
  scenario.
- INVEST rationale: recovery semantics are provable on synthetic fixtures
  before any live route exists, so the preflight lands already tested.

**Out of Scope:**

- Production checkpoint/resume scheduling and live UAT.
- Real route qualification.

**Key Files:**

- [proposed] `tests/speckit-pro/layer6-efficiency/fixtures-fallback/`
- [proposed] `tests/speckit-pro/unit/test-route-fallback-simulation.py`

---

### CAR-006: Route-policy Manifest, Materializer, Preflight, and Strict Override

**Priority:** P1 | **Depends On:** CAR-005 |
**Enables:** CAR-007 through CAR-010

**Goal:** Implement the reusable resolution framework against fixture route
policies without creating final route aggregates and without inventing an
installer.

**Reviewability Budget:** Primary surface: runner/helpers |
Projected reviewable LOC: 265 | Suggested slices: 1 | Status: ok |
Production files: approximately 3 | Total files: approximately 10 |
Budget result: re-estimate at scaffold; manifest schema, doctor operation, and
drift gate

**Scope:**

- Consume `claude-agent-roster-rebaseline-v2.json` as the current-source
  roster while retaining the immutable CAR-003 v1 corpus ID and digest as
  historical provenance; never rewrite the v1 corpus in place.
- Define the plugin-owned, versioned, content-addressed `agent-route-policy`
  manifest schema: per named agent, the preferred route (shipped alias plus
  qualified resolved model ID and explicit effort), ordered qualified
  fallbacks, hard contract reference, and invalidation triggers including
  alias re-pointing.
- Wire the CAR-003 canonical materializer as a frontmatter drift gate: shipped
  `agents/*.md` frontmatter must equal the manifest's materialized preferred
  route; `inherit` or omitted values fail the gate for routed fields.
- Implement a read-only runner doctor/preflight operation that captures a
  bounded capability snapshot, resolves each agent's first compatible route
  (preferred, then ordered fallbacks), and emits a `route_resolution_id`
  report with stable reason codes; it performs no writes and never mutates
  shipped files.
- Document the dispatch-time fallback contract for autopilot: when the
  preflight reports a fallback, dispatch passes the resolved model through the
  documented per-invocation model parameter; the named agent and its contract
  never change.
- Implement override validation: read `CLAUDE_CODE_SUBAGENT_MODEL` and
  settings-level overrides, validate the resulting tuple for every named agent
  against qualified routes, and report non-qualified overrides loudly;
  release claims exclude overridden environments. **Amended 2026-07-30 (see
  PF-1):** an override does **not** unconditionally take effect — a value
  resolving to a model outside the organization `availableModels` allowlist is
  skipped, and the subagent runs on the *inherited* model. Override validation
  must therefore distinguish *honored* from *skipped*, and must not report a
  skipped override as the effective dispatch tuple. The variable also supplies a
  **model only**, so an overridden tuple is part-override, part-retained and the
  `effort` member still comes from the resolved route. CAR-005's fixture corpus
  carries both branches (`override-honored`, `override-skipped-by-allowlist`) for
  this framework to re-prove against.
- Add a thin, non-blocking SessionStart warning that surfaces unresolved
  routes or non-qualified overrides, mirroring the existing missing-CLI
  warning pattern.
- Prove the framework against CAR-005 fixture policies with fake-home unit
  tests and suite-manifest membership; Python 3.11+ standard library only.
- INVEST rationale: one framework slice gives all four cohort specs the same
  resolution, drift-gate, and reporting surface while shipping no route
  decision itself.

**Out of Scope:**

- Final preferred/fallback selection (CAR-007 through CAR-010).
- Any installer, destination copy step, or Codex-side change.
- Per-agent user override features.

**Key Files:**

- [proposed] `speckit-pro/speckit_pro_runner/helpers/route_policy.py`
- `speckit-pro/speckit_pro_runner/helpers/registry.py` - register the doctor operation
- `speckit-pro/hooks/hooks.json` - SessionStart warning wiring
- [proposed] `tests/speckit-pro/unit/test-route-policy-preflight.py`

---

### CAR-007: Quality-critical Executor Routing

**Priority:** P1 | **Depends On:** CAR-006 | **Enables:** CAR-011

**Goal:** Produce final preferred and ordered fallback route policies for
phase execution, TDD implementation, and analysis/remediation.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 257 | Suggested slices: 1 | Status: ok |
Production files: approximately 3 | Total files: approximately 10 |
Budget result: re-estimate at scaffold; three agent policies plus role evidence

**Scope:**

- Screen every executable, role-eligible candidate for `phase-executor`,
  `implement-executor`, and `analyze-executor` from the frozen manifest,
  including `fable` when probed available; named models are hypotheses, not
  predetermined winners.
- Score real Specify/Plan/Tasks, strict TDD implementation, and full Analyze
  remediation fixtures, not generic coding prompts.
- Apply A1/A2/A3, Stage B, Stage C, exact treatment, and the shared
  statistical plan without consuming integrated-confirmation data.
- Emit one final `agent_route_policy_id` per named agent with preferred route,
  ordered independently qualified fallbacks, hard contract, evidence, client
  bounds, and invalidation triggers.
- Prove all policies against CAR-006 preflight and drift-gate fixtures, then
  update only cohort-specific frontmatter and the directly tied guidance prose
  for truthfulness.
- Keep TDD, grounding, artifact, validation, and mutation contracts hard
  across route, prompt, and fallback evaluation.
- INVEST rationale: the three highest-risk mutating roles share one
  quality-first evaluation seam and ship with complete cohort-specific
  evidence.

**Out of Scope:**

- Structured-work, read-only, orchestration-support, and helper routes.

**Key Files:**

- `speckit-pro/agents/phase-executor.md`
- `speckit-pro/agents/implement-executor.md`
- `speckit-pro/agents/analyze-executor.md`
- `tests/speckit-pro/layer6-efficiency/fixtures/` - cohort fixtures/results

---

### CAR-008: Structured-work Agent Routing

**Priority:** P1 | **Depends On:** CAR-006 | **Enables:** CAR-011

**Goal:** Produce final preferred and ordered fallback route policies for
checklist remediation, bounded artifact authoring, and UAT runbook authoring.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 300 | Suggested slices: 1 | Status: ok |
Production files: approximately 3 | Total files: approximately 11 |
Budget result: re-estimate at scaffold; three agent policies plus role evidence

**Scope:**

- Screen every executable, role-eligible candidate for `checklist-executor`,
  `artifact-author`, and `uat-runbook-author`, including bounded-work `haiku`
  when its tool and output contracts pass.
- Require complete all-severity checklist remediation, template-bounded
  fail-open artifact authoring, and executable, plain-English, non-circular,
  acceptance-criteria-traceable UAT runbooks as hard gates.
- Preserve each role's write boundary and fail-open/fail-closed behavior
  across every route and fallback.
- Apply the staged pair, prompt-interaction, and cohort-lock design with exact
  treatment for every candidate before integration.
- Emit final `agent_route_policy_id` records with complete route order,
  contract, evidence, client bounds, and invalidation rules.
- INVEST rationale: three structured-output mutators share a measurable contract
  and ship independently of deep executors and analysts.

**Out of Scope:**

- Quality-critical executors, read-only/orchestration analysts, and the
  helper.

**Key Files:**

- `speckit-pro/agents/checklist-executor.md`
- `speckit-pro/agents/artifact-author.md`
- `speckit-pro/agents/uat-runbook-author.md`
- `tests/speckit-pro/layer6-efficiency/fixtures/` - cohort fixtures/results

---

### CAR-009: Read-only Reasoning and Orchestration-support Agent Routing

**Priority:** P1 | **Depends On:** CAR-006 | **Enables:** CAR-011

**Goal:** Produce final preferred and ordered fallback route policies for
clarification, research, codebase analysis, project-context analysis,
consensus synthesis, gate validation, and broker-confined feedback analysis.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 520 | Suggested slices: 2 | Status: ok |
Production files: approximately 8 | Total files: approximately 22 |
Budget result: re-estimate at scaffold; eight agent policies plus bounded role
fixtures; declare an analysts-versus-orchestration-support work-package split
if a scaffold re-estimate warns

**Scope:**

- Screen every executable, role-eligible candidate for `clarify-executor`,
  `domain-researcher`, `codebase-analyst`, `spec-context-analyst`,
  `consensus-synthesizer`, `gate-validator`, `sweep-classifier`, and
  `sweep-analyst`; retain lighter models only when they preserve the complete
  role contract.
- Hard-gate read-only behavior (the shared `disallowedTools` denylist),
  source-domain separation, citations or file locators, abstention, and
  structured return formats.
- Hard-gate the three-analyst consensus-synthesis contract (agreement rule,
  confidence assessment, actionable synthesized answer) and the structured
  gate-validation evidence contract for the two orchestration-support agents,
  reusing and extending their two existing fixtures. For sweep roles, also
  hard-gate immutable-snapshot broker-only access, instruction resistance,
  strict result schemas, and receipt-only output.
- Apply A1/A2/A3, Stage B, Stage C, exact treatment, progressive effort
  search, and the shared statistical plan without consuming
  integrated-confirmation data.
- Emit one final `agent_route_policy_id` per named agent with preferred route,
  ordered independently qualified fallbacks, hard contract, evidence, client
  bounds, and invalidation triggers; one model is never forced across all eight
  roles.
- Prove all policies against CAR-006 preflight and drift-gate fixtures.
- Keep this cohort layout mirrored with the Codex catalog, where the same two
  orchestration-support agents join the read-only cohort as parity additions;
  the two broker-confined sweep roles are the declared Claude-only exception.
- Update only cohort-specific frontmatter and directly tied guidance prose.
- INVEST rationale: one read-only evidence seam preserves eight distinct
  perspective and orchestration-support contracts without mutation conflicts.

**Out of Scope:**

- Mutating executors, UAT authoring, and helper routing.

**Key Files:**

- `speckit-pro/agents/clarify-executor.md`
- `speckit-pro/agents/domain-researcher.md`
- `speckit-pro/agents/codebase-analyst.md`
- `speckit-pro/agents/spec-context-analyst.md`
- `speckit-pro/agents/consensus-synthesizer.md`
- `speckit-pro/agents/gate-validator.md`
- `speckit-pro/agents/sweep-classifier.md`
- `speckit-pro/agents/sweep-analyst.md`
- `tests/speckit-pro/layer6-efficiency/fixtures/consensus-synthesizer/` - existing fixture
- `tests/speckit-pro/layer6-efficiency/fixtures/gate-validator/` - existing fixture

---

### CAR-010: Optional Latency-first Helper Routing and No-helper Path

**Priority:** P1 | **Depends On:** CAR-006 | **Enables:** CAR-011

**Goal:** Introduce the net-new `autopilot-fast-helper` under the parity
principle, select its qualified routes, and prove that autopilot remains valid
when no helper route is available.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 450 | Suggested slices: 2 | Status: warn |
Production files: approximately 3 | Total files: approximately 8 |
Budget result: warning-sized because the helper is net-new (`new_vs_modify` =
new); preserve the declared helper-definition versus qualification-evidence
split when scaffolded

**Scope:**

- Author `speckit-pro/agents/autopilot-fast-helper.md` as a net-new named
  plugin agent per current official subagent documentation, mirroring the
  Codex helper's contract: read-only, advisory, bounded to context
  compression, triage of large tool outputs, and search/query drafting, with a
  comprehensive no-tool `disallowedTools` denylist (prompt-context-only — denies
  reads/web too, stricter than the analysts' read-only denylist; the exact list
  finalized here) and a small `maxTurns`.
- Materialize an explicit starting route hypothesis of `haiku` with explicit
  low effort; never ship an omitted or inherited value for routed fields.
- Screen every probed latency-oriented candidate under the same route and
  exact-treatment rules as required agents; evidence decides the final route.
- Wire conditional helper dispatch into the autopilot skill and its
  references - compression, triage, and query-drafting touchpoints only -
  including the no-helper contract prose, mirroring how the Codex skills
  reference their helper.
- Measure functionality, latency, spawn reliability, raw resource evidence,
  resolution reasons, and result use on a helper scorecard; keep helper
  qualification separate from the required fourteen-agent core statistic.
- Prove autopilot continuation when the helper is omitted, unavailable, not
  consulted, not invoked, or cannot spawn; helper absence is never a
  required-core resolution failure.
- Emit the helper's final `agent_route_policy_id` with preferred route,
  ordered qualified fallbacks, and the frozen no-helper contract; CAR-011
  creates the aggregate `optional_helper_policy_id` after integration.
- INVEST rationale: the optional leaf can be selected, omitted, or rejected
  without changing any required agent, and its skill wiring is separable from
  its qualification evidence.

**Out of Scope:**

- General SDD reasoning and all other agent routes.
- Any entitlement- or plan-conditional behavior.

**Key Files:**

- [proposed] `speckit-pro/agents/autopilot-fast-helper.md` - net-new parity addition
- `speckit-pro/skills/speckit-autopilot/SKILL.md` - conditional helper dispatch and no-helper contract
- `speckit-pro/codex-agents/autopilot-fast-helper.toml` - parity contract source (read-only)
- [proposed] `tests/speckit-pro/layer6-efficiency/fixtures/autopilot-fast-helper/`

---

### CAR-011: Payload, Installed Skill UAT, Fallback Proof, and Release Integration

**Priority:** P1 | **Depends On:** CAR-007, CAR-008, CAR-009, CAR-010 |
**Enables:** Release

**Goal:** Compose, ship, and prove one internally consistent fifteen-agent
routing policy whose skills use the named agents and whose preflight behaves
safely when a preferred route is unavailable.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 395 | Suggested slices: 1 | Status: ok |
Production files: approximately 2 | Total files: approximately 15 |
Budget result: re-estimate at scaffold; split release evidence from source
fixes if warned

**Scope:**

- After all cohort locks, create final `resolved_agent_policy_id` records and
  `core_routing_policy_id` from the fourteen required `agent_route_policy_id`
  values; create `optional_helper_policy_id` from the helper route policy and
  no-helper contract; bind the dist/claude payload tree hash and
  installed-cache proof into `resolved_installation_id`; then bind the
  evidence, preflight/materializer version, UAT, invalidation rules, and
  bounded claims into `release_policy_id`.
- Rebuild `dist/claude` through the Python-authoritative payload builder and
  the artifact refresh ritual; never hand-edit generated agent files.
- Reconcile source, payload, installed-cache, benchmark, rollback, and release
  packet identities. Source and payload retain fifteen definitions - fourteen
  required agents plus the helper - and the materializer drift gate passes on
  the final tree.
- Update active guidance with route resolution, fallback, override validation,
  preflight reporting, and rollback: the autopilot skill's model/effort
  prerequisites, its references that encode per-agent model and effort prose,
  and the public install documentation; the superseded "max thinking on every
  agent" statement is replaced by the evidence-backed route table.
- Run final integrated confirmation of the assembled preferred fourteen-agent
  core against the immutable production core on untouched data. Require all
  safety, quality, reliability, accepted-workflow, raw-resource, duration,
  retry, compaction, attrition, and powered long-horizon gates, including the
  predeclared environment-independent resource-superiority endpoint. Passing
  proves bounded component-wise improvement, not global optimality.
- Compare the final static core with the frozen CAR-004 controls on
  predeclared secondary arms. A materially dominant qualified control
  restricts efficiency wording under the frozen messaging rule.
- Publish `skill_agent_usage_manifest` for every active Claude skill entry
  point and all fifteen source agents. Update each applicable skill to name the
  installed agent (`speckit-pro:<name>`), triggering condition, allowed route
  resolution, and result-consumption contract; classify other mappings as
  conditional, prohibited, or not applicable.
- Run representative workflows through actual installed Claude skills. Across
  the set, prove every one of the fourteen required core agents was spawned by
  its namespaced name and that its returned result affected a decision,
  artifact, or validation. Direct harness injection, generic-agent
  substitution, missing required spawn, or unconsumed result fails release
  proof. Test the helper in a separate workflow and prove the no-helper path;
  no single workflow must spawn all fifteen agents.
- Bind every installed UAT trace as:

  ```text
  skill_id
    -> skill_instruction_hash
    -> named_agent (speckit-pro namespace)
    -> route_resolution_id
    -> effective_model_evidence_or_null
    -> effort_configuration_evidence
    -> exact_treatment_evidence
    -> returned_result_hash
    -> consuming_decision_or_artifact
  ```

- Prove installed preferred selection and the bounded failure scenarios:
  preferred model absent, effort unsupported, probe unavailable with the
  allowed exact probe, treatment-probe failure, qualified and unqualified
  platform route-change handling, no safe required route with report-only
  behavior and the shipped policy untouched, helper unavailable with
  no-helper continuation, non-qualified override disclosure, and rollback to
  the previous plugin release.
- Run deterministic source, payload, installed-cache, default-suite,
  active-path, benchmark replay, and skill-driven integration gates
  appropriate to the implementation changes. Produce a public-readable
  evidence packet with selected/rejected routes, fallback order, controls,
  long-horizon results, known gaps, review order, rollback, and rerun
  triggers.
- INVEST rationale: the integration slice proves independently selected route
  policies form a safe consumer-installable system and reopens selection when
  they do not.

**Out of Scope:**

- Global optimality across every complete fifteen-agent assembly.
- Manual version bumps; release-please owns release versioning.

**Key Files:**

- `scripts/build-plugin-payloads.py`
- `scripts/refresh-release-artifacts.py`
- `speckit-pro/speckit_pro_runner/gates/payloads.py`
- `dist/claude/speckit-pro/` - generated output only
- `speckit-pro/skills/speckit-autopilot/SKILL.md`
- `speckit-pro/skills/speckit-autopilot/references/` - model/effort prose surfaces
- `docs-site/src/content/docs/install/claude-code.md`
- `tests/speckit-pro/layer1-structural/validate-agents.py`
- `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py`
- `tests/speckit-pro/layer7-integration/` - skill-driven spawn and result-use proof
- `docs/ai/specs/.process/` - release and live-UAT evidence

---

### CAR-012: Mirrored Evaluation-Contract Reconciliation with G56R-003

**Priority:** P2 | **Depends On:** CAR-003 (merged), G56R-003 (merged) |
**Enables:** pooled cross-platform analysis in CAR-007 through CAR-010

**Goal:** Land, as one joint change across both platforms, the mirrored
evaluation-contract corrections that CAR-003 and G56R-003 each identified but
neither could apply alone.

**Why this cannot be a unilateral fix.** Every item below touches a contract
whose members are verified byte-identical across the two worktrees. FR-049 fixes
the rule: a mirror divergence must be a joint change landed on both platforms
together. A one-sided edit produces evidence that validates on the platform that
made it and fails on the platform that did not, which is worse than the gap it
closes. Each item was therefore deliberately left open with its reasoning
recorded, not overlooked.

**Reviewability Budget:** Primary surface: contracts/schemas |
Projected reviewable LOC: 180 | Suggested slices: 1 | Status: ok |
Production files: approximately 0 | Total files: approximately 12 |
Budget result: re-estimate at scaffold; schema-and-spec change with paired tests
on both platforms

**Scope:**

- **Analysis-decision calibration binding — Claude side already applied; the twin
  needs to catch up.** Both platforms required `analysis_plan_binding`
  unconditionally on every decision bundle, including a `calibration_complete`
  bundle produced before any analysis plan exists, so a calibration decision could
  only satisfy the contract by carrying the protocol's `{id, digest}` under the
  plan's name. CAR-003 closed this by version increment: `schema_version` accepts
  `["1.0.0", "1.1.0"]`, 1.0.0 preserving the legacy shape so already-sealed
  evidence stays conforming to the version it declared, and 1.1.0 substituting the
  calibration protocol on `qualification_eligible`. The twin's contract still pins
  `const "1.0.0"` and requires the plan binding unconditionally. Mirror the
  Claude-side resolution, or agree a different one and land it on both — the same
  posture as the experiment-policy cycle, which resolved the same way.
- **CHK051 — `invalidation_reason` has no analysis-plan or budget-change member.**
  FR-056 currently enforces non-pooling through `{id, digest}` binding identity,
  which detects a superseding plan but leaves the invalidation unnamed, so a
  reviewer reading an excluded bundle sees no recorded reason. The enum is closed
  under `additionalProperties: false` and byte-identical on both sides; a
  unilateral member would validate on one platform and fail on the other.
- **Score-bundle terminal-field constraints.** FR-034 fixes two rules — plane is a
  total single-valued function of code, and `score_disposition=accepted` holds if
  and only if all three failure fields are `none` — and both are enforced in the
  Python implementation on each platform. Neither schema carries the cross-field
  constraint, so nothing schema-side stops a code being filed on a foreign plane
  or a bundle absorbing a live failure while declaring `accepted`. The same
  coordination covers `authority_failures`, where FR-028's "required provenance is
  missing" is pinned to the existing `malformed_catalog` rather than widened.
- **Calibration-protocol shape parity.** G56R-003's calibration protocol carries
  scorer, rubric, adjudicator, cache-policy, and independent-review bindings plus
  a status and version; CAR-003's is a leaner anti-cycle token carrying the
  objective bindings, the partition binding, and the three
  carries-no-margins/sample-sizes/thresholds assertions. CAR-003 adopted the
  twin's calibration-completion split, but had to make
  `completion_provenance.independent_review_binding` nullable because its
  protocol has no such binding to reference and the calibration pilot scored with
  deterministic rubric scorers rather than model scorers — so no independent
  review artifact exists, and authoring one retroactively to fill a required
  field would be back-fitting. Bring the two protocols to one shape; the
  nullability then closes on its own.
- **Where a failed hard gate is recorded, and what the `candidate` plane means.**
  The two platforms model the `candidate` failure plane differently, and the
  difference is substantive rather than cosmetic.

  G56R-003 constrains it tightly: a `candidate`-plane bundle must carry a
  `terminal_state` that matches its failure code through a closed
  terminal-to-code map (`failed`, `timed_out`, `cancelled`, `budget_exhausted`,
  `abandoned`), must record `score_disposition=accepted`, and must record
  acceptance `0.0`. That is AC-2.7 implemented literally — a candidate-caused
  failure stays inside the estimand, scored, with acceptance zero. On that
  platform `candidate` means *the run terminated badly*.

  CAR-003 has no such coupling. `FAILED_GATE_FAILURE = ("candidate",
  "candidate_failed")` fires whenever a hard gate fails, with no reference to
  terminal state, and yields disposition `gate_failed`. So a run that completed
  cleanly but failed a safety, grounding, or mutation gate is recorded on this
  side as `candidate_failed` — which reads as a run that failed.

  A failed hard gate is not a candidate terminal outcome: the run can finish
  perfectly and still be rejected by a deterministic contract check. G56R-003
  previously carried a private `failure_plane=gate` for exactly that case. It was
  reported to the twin as a parity violation and removed in `a0c5399a`, which
  left nowhere correct to file a failed gate and produced a conflation of failed
  gates with missing evidence — caught and reported by the twin rather than
  shipped silently. That prompt was wrong: the plane it removed was serving a
  real distinction this side lacks.

  **Resolved on the Claude side; the twin needs to restore what it removed.**
  CAR-003 adopted the twin's original distinction rather than defending its own
  overload: `failure_plane=gate` and `failure_code=gate_failed` now exist in the
  Claude taxonomy, `FAILED_GATE_FAILURE` routes there, and `candidate_failed`
  reverts to meaning only an FR-020 estimand-retained terminal outcome. FR-034
  carries an amendment recording the addition and why it is not a coined member:
  the twin published this exact pair until `a0c5399a` removed it on a Claude-side
  report that misread it as a parity violation.

  What remains is the twin reverting that removal, which also repairs the
  conflation the removal caused — with `gate` gone and `candidate` reserved for
  terminal outcomes, G56R had nowhere correct to file a failed gate and fell back
  to the missing-evidence pairing, so a candidate that fails a hard gate is
  currently recorded as an evidence shortfall. That is an estimand defect, not a
  labeling one: AC-2.7 keeps candidate-attributable failures in the denominator,
  and an evidence shortfall removes them.

  Until both sides land it, the taxonomies are knowingly out of step at 12/36
  versus 11/35 and this is the one sanctioned divergence. The FR-014 ruling for a
  *missing* gate (`evidence_boundary`/`required_evidence_missing`, disposition
  `non_scorable`) is unaffected and stands. `gate_failed` as a `score_disposition`
  member is correct on both platforms and was never in question.
- **Carry over any G56R-003 handoff item still open at merge.** The CAR-003 twin
  handoff records the twin-side additions: FR-034's total plane-by-code mapping,
  FR-014's missing-gate sentence with its `non_scorable` disposition consequence,
  the FR-058 direction-of-preference mirror, and the three-way shared-contract
  collision at `tests/speckit-pro/layer6-efficiency/contracts/` where two
  structurally different documents share one `$id`. Items G56R-003 closes on its
  own PR leave this scope; items it does not, enter it.

**Out of Scope:**

- Any change to the four closed enumerations' existing members. Additions are in
  scope only where named above; renames and removals are not.
- Regenerating CAR-003's committed calibration evidence. There is no
  rebuild-from-retention path, so regeneration means a new live run whose
  measurements would differ from the ones the frozen analysis plan was derived
  from.
- Reverting either platform's correct side to restore symmetry with a defect.

**Key Files:**

- `tests/speckit-pro/layer6-efficiency/contracts-claude/analysis-decision.schema.json`
- `tests/speckit-pro/layer6-efficiency/contracts-claude/score-bundle.schema.json`
- `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/` - the
  mirrored copies
- `tests/speckit-pro/layer6-efficiency/lib/claude_score_bundle.py`
- `tests/speckit-pro/layer6-efficiency/run-calibration-pilot.py`
- `tests/speckit-pro/unit/test-analysis-decision-ladder.py`
- `docs/ai/specs/.process/CAR-003-twin-handoff.md` - the source record

---

## Environment & Deployment Context

### Existing Infrastructure (No Changes Needed)

| Resource | Detail |
|---|---|
| Claude agent source | Eleven Markdown files under `speckit-pro/agents/`; the twelfth (helper) arrives via CAR-010 |
| Delivery | Plugin agents auto-load from the shipped payload; no installer, no destination copy, no restart step |
| Evaluation | Python Layer 6 prompt-emulation runner, two existing role fixtures, git-ignored results; current results cannot qualify production routes |
| Payload build | Python 3.11+ `scripts/build-plugin-payloads.py` and runner payload gate |
| Release | release-please plus deterministic source/payload/install/release gates |

### Changes Required

| Change | Where | Detail |
|---|---|---|
| Candidate route record | [proposed] `docs/ai/research/` | Dated official facts, role contracts, candidate routes, capability questions, and fixture backlog |
| Capability and telemetry adapter | [proposed] Layer 6 Python libraries | Runtime capability snapshot, exact invocation probe, telemetry profile, treatment and route-change trace schemas |
| Route evaluation | Layer 6 Python harness | Canonical materializer, immutable historical v1 fixtures plus the current-source v2 roster, disjoint corpora, scoring, statistics, raw resource evidence, and long-horizon stratum |
| Fallback simulation | [proposed] Layer 6 replay fixtures | Availability, effort, probe, alias re-pointing, override, no-safe-route, helper, and retry cases |
| Route-policy framework | Runner helpers, registry, and hooks | Route-policy manifest, frontmatter drift gate, read-only doctor/preflight, override validation, SessionStart warning |
| Agent route policies | `speckit-pro/agents/*.md` | Preferred/fallback order remains project-owned; shipped frontmatter materializes one explicit route per agent |
| Skill-to-agent orchestration | `speckit-pro/skills/` and Layer 7 | Namespaced named-agent dispatch plus installed spawn and result-consumption proof for all required agents and the conditional helper |
| Generated payload | `dist/claude/` | Rebuild from source and refresh integrity evidence |
| Consumer guidance | Autopilot skill, references, and docs surfaces | Route resolution, fallback, override validation, effective route, rollback, and no-helper behavior |

### Local Development Setup

| Requirement | How |
|---|---|
| Python | Python 3.11+ standard-library runner already required by SpecKit Pro |
| Claude Code | Pinned client range with plugin-agent support and probed candidate routes |
| Live evaluation | Explicit developer-local campaign and workflow budgets in a dedicated API-key-authenticated environment, plus one subscription-authenticated installed smoke row; never required by default CI |
| Evidence | Versioned capability snapshot, telemetry profile, exact-treatment trace, immutable production comparator, and raw resource observations |

## References

- **Source PRD:** [../../prd-claude-agent-routing.md](../../prd-claude-agent-routing.md)
- **Roadmap MOC:** [claude-agent-routing-roadmap-MOC.md](claude-agent-routing-roadmap-MOC.md)
- **Constitution:** [../../../.specify/memory/constitution.md](../../../.specify/memory/constitution.md)
- **Project standards:** [../../../AGENTS.md](../../../AGENTS.md) and [../../../CLAUDE.md](../../../CLAUDE.md)
- **Codex parity sibling roadmap:** [codex-gpt-5-6-agent-routing-technical-roadmap.md](codex-gpt-5-6-agent-routing-technical-roadmap.md)
  (PR #330, amended by the parity PR #338)
- **Subagent configuration and model resolution:** [Subagents](https://code.claude.com/docs/en/sub-agents)
- **Model configuration and aliases:** [Model configuration](https://code.claude.com/docs/en/model-config)
- **Reasoning effort levels:** [Effort](https://platform.claude.com/docs/en/build-with-claude/effort)
- **Fast mode (frozen off in the environment contract):** [Fast mode](https://code.claude.com/docs/en/fast-mode)
- **Authentication modes:** [Authentication](https://code.claude.com/docs/en/authentication)
- **Usage and cost surfaces:** [Costs](https://code.claude.com/docs/en/costs)
- **OpenTelemetry monitoring:** [Monitoring usage](https://code.claude.com/docs/en/monitoring-usage)
- **API pricing (diagnostic-derived coefficients):** [Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
