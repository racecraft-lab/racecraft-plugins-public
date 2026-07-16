# SpecKit Workflow: G56R-001 - Candidate Route Baseline and Role Contracts

**Template Version**: 1.0.0
**Created**: 2026-07-15
**Purpose**: Prepare the official-documentation candidate-route and twelve-agent role-contract baseline required by G56R-002 without changing installed behavior.

---

## 2026-07-16 Evidence-Parity Amendment

The completed v0.1 workflow below remains historical execution evidence. The
approved CAR/G56R parity plan adds a post-completion evidence package:

- canonical human report:
  `docs/ai/research/codex-agent-route-candidates.md`
- schema-v2 planning manifest:
  `docs/ai/research/codex-agent-route-candidate-manifest.json`
- shared contract: `docs/ai/specs/agent-routing-parity-contract.md`
- shared schema:
  `docs/ai/research/agent-route-candidate-manifest.schema.json`

This amendment supersedes only the original report-only packaging decision.
It introduces no runtime manifest, route policy, installer input, generated
payload, cache change, or version change. Foundation PR #362 and G56R-001 PR
#360 are merged; G56R-002 is ready for capability discovery and telemetry
profiling under the preserved no-qualification boundary.

---

## How to Use This Workflow

Run this workflow from the dedicated G56R-001 worktree:

```text
$speckit-autopilot docs/ai/specs/.process/G56R-001-workflow.md
```

This file is fully populated for G56R-001. Do not replace it with the generic
workflow template, and do not run it from the parent `main` checkout.

---

## Design Concept

The setup Grill Me record is:

```text
docs/ai/specs/.process/G56R-001-design-concept.md
```

Re-read it before each phase. Its accepted decisions are:

- Revalidate official OpenAI sources when G56R-001 executes, then freeze the
  dated evidence snapshot for this spec.
- Treat the five roadmap model IDs as a seed, not a closed list; add, retain,
  or remove candidates only when current official documentation supports it.
- Publish one canonical report at
  `docs/ai/research/codex-agent-route-candidates.md` and one schema-v2 planning
  manifest at
  `docs/ai/research/codex-agent-route-candidate-manifest.json`.
- Require complete claim-to-source and role-contract traceability before the
  G56R-002 handoff; unsupported platform facts fail closed as `undocumented`.
- Define executable fixture specifications without creating or running live
  fixture payloads.
- Run the full operational checklist set: `llm-integration`,
  `data-integrity`, `error-handling`, `security`, `observability`, and
  `reliability`. The reliability checklist carries the resilience review for
  this documentation-only spike.

Grill Me is human-in-the-loop only. Once autopilot starts, clarification uses
`$speckit-clarify` and the consensus protocol, never grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|---|---|---|---|
| Specify | `$speckit-specify` | Complete | Created spec and requirements checklist; G1 passed |
| Clarify | `$speckit-clarify` | Complete | Resolved execution-time source, parity-role, fixture, and handoff ambiguities; G2 passed |
| Plan | `$speckit-plan` | Complete | Generated plan, research, data model, report contract, quickstart, and G3 pass evidence |
| Checklist | `$speckit-checklist` | Complete | All six selected domains passed after seed-list drift was resolved |
| Tasks | `$speckit-tasks` | Complete | Generated 38 source-first documentation tasks; G5 passed |
| Analyze | `$speckit-analyze` | Complete | Resolved seed-list drift and passed G6 |
| Confidence Gate | G6.5 | Complete | Advisory no-data result recorded because Phase 6 ran locally without synthesizer confidence emit |
| Implement | `$speckit-implement` | Complete | Authored and validated the canonical research report; G7 passed |
| Post | Post-Implementation | Complete | RepoPrompt review loop is clean; PR #360 merged with all review threads resolved and CI green |
| Evidence Parity Amendment | Post-completion amendment | Complete | Foundation PR #362 and G56R-001 PR #360 merged; shared parity package is current on `main` |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|---|---|---|
| G1 | After Specify | AC-1.1 through AC-1.7 are testable; authority classes and no-runtime boundary are explicit; no unresolved scope markers remain |
| G2 | After Clarify | Candidate admission, unsupported facts, parity-role divergence, source invalidation, and G56R-002 handoff rules are unambiguous |
| G3 | After Plan | One-report architecture, stable IDs, source snapshot, twelve-role inventory, fixture backlog, and deterministic checks are fully planned |
| G4 | After Checklist | All true gaps from the six selected checklist domains are remediated or explicitly rejected as out of scope |
| G5 | After Tasks | Every task maps to AC-1.*, uses official evidence or labeled project input, and creates no runtime behavior |
| G6 | After Analyze | No critical or high authority, traceability, count, dependency-cycle, or scope-leakage finding remains |
| G6.5 | Before Implement | Advisory confidence gate records the current evidence posture or no-data outcome without weakening G7 |
| G7 | After Implement | Canonical report, strict go/no-go result, source links, count checks, diff hygiene, and repository validation pass |

---

## Prerequisites

### Worktree and Branch

- Worktree: `.worktrees/g56r-001-candidate-route-baseline`
- Branch: `g56r-001-candidate-route-baseline`
- Feature directory: `specs/g56r-001-candidate-route-baseline`
- Contract marker: `specs/g56r-001-candidate-route-baseline/SPEC-MOC.md`
- Design concept: `docs/ai/specs/.process/G56R-001-design-concept.md`
- Workflow: `docs/ai/specs/.process/G56R-001-workflow.md`

The branch must track `origin/g56r-001-candidate-route-baseline`. Preset
resolution must use `.specify/presets/speckit-pro-reviewability/` unless a
deliberate higher-priority repository override is documented.

### Grounded Source Truth

- Technical roadmap:
  `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`
- Roadmap MOC:
  `docs/ai/specs/codex-gpt-5-6-agent-routing-roadmap-MOC.md`
- Product requirement: `docs/prd-codex-gpt-5-6-agent-routing.md`, especially
  Evidence Authority and AC-1.1 through AC-1.7.
- Project constitution: `.specify/memory/constitution.md`
- Project agent contract: `AGENTS.md`
- Current Codex role sources: `speckit-pro/codex-agents/*.toml`
- Claude parity-role project inputs:
  `speckit-pro/agents/consensus-synthesizer.md` and
  `speckit-pro/agents/gate-validator.md`
- Current fixture-gap project inputs:
  `tests/speckit-pro/layer6-efficiency/`
- Official OpenAI source families listed in the roadmap References section:
  Codex models, subagents, app server, configuration reference,
  non-interactive mode, and current prompting guidance.

At execution time, retrieve current official pages directly and record their
URLs and retrieval date. Repository links and remembered facts are not a
substitute. No blog, social, issue, forum, third-party benchmark, changelog
inference, neighboring-model analogy, or local probe may establish a platform
fact or admit a candidate.

### Phase 0 Preflight Results

| Check | Result | Evidence |
|---|---|---|
| Main synchronization | Pass | `main` was checked and `git pull --ff-only` returned `Already up to date.` on 2026-07-15 |
| Remote | Pass | Detected `origin` at `https://github.com/racecraft-lab/racecraft-plugins-public.git` |
| Worktree and branch | Pass | Registered dedicated worktree on `g56r-001-candidate-route-baseline` |
| Codex agent install | Pass | Python-authoritative `install-codex-agents` dry run reported all ten bundled agent TOMLs current and `mutation_status=no_op` |
| SpecKit CLI | Pass | Python 3.11.0 and `specify 0.12.12.dev0` are available |
| Repository bootstrap | Not required | `AGENTS.md` and `CLAUDE.md` document no worktree bootstrap, package install, build, or index command; none was run |
| Reviewability setup gate | Warn/pass | `status=warn`, `pass=true`, 395 reviewable LOC, 2 production files, 15 total files, 3 primary surfaces; warning only for surface count and no blockers |
| Grill Me | Complete | Six picker questions reached a natural stop; decisions are recorded in the design concept |
| Size estimator | Pass | Research-spike input returned `estimated_loc=0`, `suggested_slices=1`, `status=ok` |
| Preset resolution | Pass | Spec, plan, and tasks templates resolve to `speckit-pro-reviewability v1.0.0` |
| Legacy relocation | Not applicable | No `.specify/feature.json` and no prior G56R-001 feature artifacts were found |

The setup reviewability warning is advisory. G56R-001 remains one research
slice because its implementation output is one canonical documentation
artifact and no production code.

### Constitution Validation

| Principle | G56R-001 Requirement | Verification |
|---|---|---|
| Plugin Structure Compliance | Treat plugin, agent, payload, cache, and fixture files as read-only project inputs; add only planning and research documentation | Diff scope review plus Layer 1 validation |
| Cross-Platform Runtime and Script Safety | Add no active script, runtime dependency, Bash, `jq`, package install, or platform-specific implementation | Diff scope review and Layer 4 active-path guards if required by changed-file selection |
| Semantic Versioning | Do not edit plugin or marketplace versions | Diff review |
| Test Coverage Before Merge | Validate links, structure, counts, placeholders, spec MOC, and the deterministic repository suite | Focused structural checks, Layer 1, then `python3 tests/speckit-pro/run-all.py` |
| Conventional Commits | Use repository-approved conventional commit subjects | Git history and PR-title review |
| KISS, Simplicity, YAGNI | Keep one canonical human report plus one shared-schema planning manifest; add no runtime manifest or speculative abstraction | Plan complexity review, G6 analysis, and parity amendment validation |

---

## Specification Context

### Basic Information

| Field | Value |
|---|---|
| **Spec ID** | G56R-001 |
| **Name** | Candidate Route Baseline and Role Contracts |
| **Branch** | `g56r-001-candidate-route-baseline` |
| **Feature directory** | `specs/g56r-001-candidate-route-baseline` |
| **Dependencies** | None |
| **Enables** | G56R-002 Capability Discovery, Telemetry Profile, and Exact Treatment |
| **Priority** | P1 |
| **Implementation output** | `docs/ai/research/codex-agent-route-candidates.md` |
| **Slice decision** | One time-boxed research spike; LOC sizing is not applicable |

### Evidence Authority Contract

| Class | Permitted use | Prohibited use |
|---|---|---|
| `official_documentation` | Establish model IDs, positioning, documented efforts, configuration fields, discovery and telemetry schemas, reroute behavior, and client-surface behavior | Claim facts not stated by the cited official page |
| `project_input` | Define current implementation inventory, immutable production routes, role contracts, fixture gaps, and parity requirements | Establish any Codex platform fact or candidate eligibility |
| `runtime_verification` | In G56R-002, narrow availability or prove exact treatment for a document-eligible candidate | Create a candidate or broaden a platform claim |
| `qualification_evidence` | In later specs, rank document-eligible routes against project contracts | Redefine platform behavior or repair missing official support |
| `undocumented` | Record a gap, open question, invalidation, or no-go reason | Support a candidate, effort, field, capability, or native-behavior claim |

### Twelve-Agent Catalog

| Cohort | Named agents | Required treatment in G56R-001 |
|---|---|---|
| Current Codex sources | `analyze-executor`, `autopilot-fast-helper`, `checklist-executor`, `clarify-executor`, `codebase-analyst`, `domain-researcher`, `implement-executor`, `phase-executor`, `spec-context-analyst`, `uat-runbook-author` | Inventory source, immutable route or inherited state, instructions, role boundary, contracts, expected capabilities, and representative tasks |
| Claude-derived parity additions | `consensus-synthesizer`, `gate-validator` | Derive role contracts as `project_input`, record current Codex production route as absent, and document any official-surface divergence |

### Official Candidate Seed

The execution-time review starts from these roadmap IDs but does not presume
that they remain eligible or complete:

- `gpt-5.6-sol`
- `gpt-5.6-terra`
- `gpt-5.6-luna`
- `gpt-5.5`
- `gpt-5.3-codex-spark`

Every retained or added candidate must have direct execution-snapshot official
support, a role-contract rationale, and either an explicit model/effort tuple
or blocked model/effort tuple status pending G56R-002 capability discovery. Every
withdrawn, conflicting, or unsupported seed entry must be removed from the
candidate set or marked `undocumented`; local availability cannot restore it.

### Success Criteria Summary

- [ ] AC-1.1: One dated record inventories all twelve named agents and every active project surface that encodes or consumes their route policy, all labeled `project_input`.
- [ ] AC-1.2: The official-source ledger records source family, retrieval method, requested/canonical official URLs, retrieval dates, durable retrieval evidence, page or section locators, short excerpt anchors, bounded source-fact extracts, extract hashes, supported surfaces, documented facts, conflicts, and `undocumented` gaps.
- [ ] AC-1.3: Every agent has an immutable production route or recorded absence, a role contract, source-bound candidate records with blocked executable tuple status, and a fixture backlog.
- [ ] AC-1.4: Platform facts, project inputs, proposed policy, runtime observations, qualification evidence, inferences, and assumptions are visibly separated.
- [ ] AC-1.5: The spike independently produces the source ledger, role catalog, candidate manifest, fixture backlog, telemetry requirements, capability questions, and go/no-go handoff without depending on G56R-002.
- [ ] AC-1.6: A versioned `agent_route_candidate_manifest` covers all twelve agents and binds every provisional route to `official_source_ledger_id` and `agent_contract_id` without claiming executability or preference.
- [ ] AC-1.7: Historical prompt-emulation results are labeled `non_release_evidence` until later exact-treatment replay.
- [ ] The fixture inventory identifies exactly three current and nine missing role fixtures, each with an executable specification but no new live payload.
- [ ] G56R-002 receives a strict go only when all source, contract, manifest, fixture, telemetry, and capability-question completeness checks pass.

---

## Phase 1: Specify

**When to run:** At the start of G56R-001. Define what the research handoff
must prove and the authority boundary it must preserve. Output:
`specs/g56r-001-candidate-route-baseline/spec.md`.

### Specify Prompt

```text
$speckit-specify

## Feature: Candidate Route Baseline and Role Contracts

### Problem Statement
G56R-002 cannot safely discover runtime availability or exact treatment until
the project has a current official-documentation source ledger, a complete
twelve-agent role-contract catalog, and a provisional candidate-route manifest.
Current repository configuration and historical evaluations describe project
state but cannot establish Codex platform facts or admit model/effort routes.

### Users
- SpecKit Pro maintainers who need a reviewable, official-only basis for model
  route research.
- G56R-002 implementers who need bounded candidate, telemetry, and capability
  questions without a dependency cycle.
- Release reviewers who need every platform claim and provisional candidate to
  be traceable to a dated official source.

### User Stories
1. As an evidence steward, I can freeze an execution-time ledger of current
   official OpenAI facts and see every conflict, withdrawal, and undocumented
   gap without third-party inference.
2. As a routing maintainer, I can review all twelve named role contracts and
   provisional model/effort candidates while preserving each role's safety,
   grounding, mutation, tool, skill, MCP, and output boundaries.
3. As an evaluation designer, I receive executable fixture specifications,
   telemetry requirements, capability questions, and a strict go/no-go handoff
   without G56R-001 running probes, qualification, or fallback ordering.

### Constraints
- Current official OpenAI documentation is the sole authority for platform
  facts and candidate admission.
- Revalidate sources at execution, record retrieval dates, and freeze the
  resulting ledger for G56R-001.
- Treat the roadmap's five IDs as a seed and refresh them only from current
  official documentation filtered through role contracts.
- Label repository, payload, cache, fixture, and Claude-definition evidence as
  `project_input`.
- Mark absent or conflicting official support `undocumented` and fail closed.
- Cover all twelve named agents in one canonical report and its schema-v2
  planning companion with stable ledger, contract, candidate, and fixture
  identifiers.
- Define three current and nine missing fixtures as executable specifications;
  do not create or run live fixture payloads.
- Require `llm-integration`, `data-integrity`, `error-handling`, `security`,
  `observability`, and `reliability` requirement-quality checklists.

### Out of Scope
- Agent TOML, installer, prompt, skill, payload, cache, default, resolver, or
  version changes.
- Runtime capability probes, model execution, corpus execution, scoring,
  qualification, preference, fallback ordering, or release claims.
- Third-party research, benchmark results, remembered platform facts, and
  inference from changelogs, adjacent models, or successful local behavior.
- A machine-readable runtime manifest separate from the canonical report.
```

### Specify Results

| Metric | Value |
|---|---|
| Functional Requirements | 18 |
| User Stories | 4 |
| Acceptance Criteria | AC-1.1 through AC-1.7 plus fixture and handoff completeness |
| G1 Gate | Pass - `spec.md` exists with 0 markers |

### Files Generated

- [x] `specs/g56r-001-candidate-route-baseline/spec.md`
- [x] `specs/g56r-001-candidate-route-baseline/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** After Specify. Do not reopen Grill Me decisions. Resolve only
execution-time evidence and contract details that remain ambiguous.

### Clarify Prompts

#### Session 1: Source Ledger and Candidate Admission

```text
$speckit-clarify Focus on the execution-time official-source ledger: exact source freshness metadata, supported-surface recording, conflict and withdrawal handling, documented effort/default treatment, candidate seed additions/removals, and fail-closed `undocumented` outcomes. Do not use repository state or runtime probes as platform authority.
```

#### Session 2: Role Contracts and Parity Additions

```text
$speckit-clarify Focus on the twelve `agent_contract_id` records: immutable production route or absence, instruction hash, role boundary, safety, grounding, mutation, tool, skill, MCP, output, client assumptions, representative tasks, and explicit platform divergence for `consensus-synthesizer` and `gate-validator`.
```

#### Session 3: Fixture and G56R-002 Handoff

```text
$speckit-clarify Focus on executable fixture specifications, the exact three-current/nine-missing inventory, telemetry requirements, capability questions, candidate invalidation triggers, and strict go/no-go criteria for G56R-002. Keep live payloads, probes, qualification, and fallback ordering out of scope.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---|---|---|---|
| 1 | Source ledger and candidate admission | 4 | Added required ledger metadata, deprecated/withdrawn seed status, per-surface effort/default treatment, and non-authoritative candidate snapshot wording |
| 2 | Role contracts and parity additions | 5 | Added route/absence, declared TOML, hash, boundary, separate tool/skill/MCP, parity-divergence, and effective-runtime verification fields |
| 3 | Fixture and G56R-002 handoff | 4 | Clarified Claude prompt-emulation fixture status, fixture record shape, telemetry requirements, invalidation triggers, and strict G56R-002 go/no-go criteria; run locally because agent thread cap blocked new executor spawn |

---

### Consensus Resolution Log

| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |
|---|---|---|---|---|---|---|
| 1 | Clarify | Deprecated or withdrawn seed status | [domain] | 1 | high-confidence | Added `rejected_deprecated_or_withdrawn` and lifecycle fields; kept unpublished exact slugs as `rejected_undocumented` | domain-researcher |
| 2 | Clarify | Per-surface effort/default treatment | [domain] | 1 | high-confidence | Added `effort_surface_records` and required source-specific effort/default evidence | domain-researcher |
| 3 | Clarify | Declared TOML vs effective runtime permissions | [security, domain, spec] | 1 | high-confidence | Added declared-source fields plus `runtime_verification_needed` effective permission fields; thread cap blocked extra analyst spawns, so parent verified official docs and project context directly | codebase-analyst + parent verification |

---

## Phase 3: Plan

**When to run:** After the specification is finalized. Generate a documentation
execution blueprint. Output: `specs/g56r-001-candidate-route-baseline/plan.md`.

### Plan Prompt

```text
$speckit-plan

## Technical Context
- Implementation surface: Markdown research and SpecKit planning artifacts only.
- Platform authority: current official OpenAI documentation retrieved at
  execution and frozen as a dated ledger.
- Project inputs: current Codex TOMLs, Claude parity-role definitions, skills,
  installers, generated payloads, installed-cache evidence, fixture inventory,
  and historical evaluation records, all read-only and labeled `project_input`.
- Validation: structured document checks, exact count and traceability review,
  relative-link validation, Layer 1, and the Python-authoritative deterministic
  repository suite.
- Runtime dependencies: none; use existing repository tooling only.

## Constraints
- Produce one canonical report at
  `docs/ai/research/codex-agent-route-candidates.md` and one schema-v2 planning
  manifest at
  `docs/ai/research/codex-agent-route-candidate-manifest.json`.
- Record `official_source_ledger_id`, twelve `agent_contract_id` records, a
  versioned `agent_route_candidate_manifest`, and provisional
  `candidate_route_id` records.
- Every platform claim and retained candidate must bind a direct official URL,
  retrieval date, supported surface, and documented fact from the frozen
  execution snapshot.
- Every unsupported or conflicting fact remains `undocumented` and cannot
  support a route.
- Candidate records must distinguish documentation eligibility from runtime
  availability and must not claim executability, qualification, preference, or
  fallback order.
- Fixture records define stable IDs, representative inputs, expected signals,
  ownership, and later acceptance checks without creating payload files.
- Add no script, platform-specific or runtime schema, runtime JSON, agent
  definition, test fixture, generated payload, installation change, or version
  change. The shared planning schema and its evidence manifest are allowed.

## Report Architecture
1. Scope, evidence classes, snapshot metadata, and bounded claims.
2. Versioned official-source ledger and source invalidation rules.
3. Active project-input route-policy surface inventory.
4. Twelve-agent role-contract catalog and instruction hashes.
5. Versioned provisional candidate-route manifest with source bindings.
6. Three-current/nine-missing executable fixture-specification backlog.
7. Telemetry requirements and unresolved capability questions for G56R-002.
8. Strict completeness matrix, go/no-go decision, and invalidation triggers.

## Architecture Notes
- Keep IDs deterministic and cross-reference them rather than duplicating
  free-form claims.
- Preserve historical prompt-emulation evidence only as
  `non_release_evidence`.
- Treat the parity-role Claude files as contract inputs, never Codex platform
  proof.
- Record the setup reviewability result as warn/pass and preserve one research
  slice unless planning discovers a genuine blocking scope increase.
- Follow the decisions in
  `docs/ai/specs/.process/G56R-001-design-concept.md`.
```

### Plan Results

| Artifact | Status | Notes |
|---|---|---|
| `plan.md` | Complete | Original one-report execution flow; the dated parity amendment adds one governed planning manifest |
| `research.md` | Complete | Source, classification, ID, candidate-admission, fixture, and validation decisions |
| `data-model.md` | Complete | Ledger, role, candidate, effort-surface, fixture, traceability, and handoff record fields |
| `contracts/` | Complete | Planning-only Markdown report contract; no runtime schema |
| `quickstart.md` | Complete | Revalidation and deterministic verification steps |
| G3 Gate | Pass | `plan.md` exists with 0 unresolved markers; reviewability estimate projected 0 production LOC |

---

## Phase 4: Domain Checklists

**When to run:** After `$speckit-plan`. The user explicitly selected the full
operational set. Run all six enriched checklists even though the general
guidance normally recommends two to four.

### Checklist Prompts

#### 1. LLM Integration Checklist

```text
$speckit-checklist llm-integration

Focus on G56R-001 requirements:
- Official-only model IDs, positioning, documented defaults, effort values,
  supported surfaces, and custom-agent fields.
- Role-fit hypotheses versus later capability and qualification evidence.
- Candidate tuple completeness and source-ledger bindings.
- Clear prohibition on executable, preferred, optimal, or native-fallback claims.
- Pay special attention to model/effort facts that are absent, conflicting, or
  documented for a different client surface.
```

#### 2. Data Integrity Checklist

```text
$speckit-checklist data-integrity

Focus on G56R-001 requirements:
- Stable and unique `official_source_ledger_id`, `agent_contract_id`,
  `candidate_route_id`, fixture IDs, and manifest version.
- Exact twelve-agent, three-current, and nine-missing counts.
- Complete foreign-key-style bindings from candidates to sources and contracts.
- Retrieval dates, evidence classes, instruction hashes, invalidation triggers,
  and completeness matrices.
- Pay special attention to orphan claims, duplicate IDs, stale links, and mixed
  authority classes.
```

#### 3. Error Handling Checklist

```text
$speckit-checklist error-handling

Focus on G56R-001 requirements:
- Missing, withdrawn, conflicting, inaccessible, or surface-mismatched official
  documentation.
- `undocumented` classification and dependent candidate rejection.
- Missing immutable routes, parity-role divergence, incomplete fixture specs,
  and unresolved telemetry questions.
- Source invalidation and strict G56R-002 no-go behavior.
- Pay special attention to any path that silently substitutes inference,
  runtime availability, or project input for official authority.
```

#### 4. Security Checklist

```text
$speckit-checklist security

Focus on G56R-001 requirements:
- Per-role safety, grounding, sandbox, approvals, mutation, tool, skill, MCP,
  and output contracts.
- Candidate and fallback requirements that may never weaken a named role's hard
  contract.
- Clear separation of read-only research from installer, config, payload, and
  user-local mutation.
- Source trust boundaries and prohibition on third-party platform claims.
- Pay special attention to the two parity roles and any undocumented Codex
  field needed to preserve their safety contracts.
```

#### 5. Observability Checklist

```text
$speckit-checklist observability

Focus on G56R-001 requirements:
- Source-audit metadata: source family, retrieval method, requested URL,
  canonical URL, retrieval timestamp, and invalidation triggers.
- Telemetry field coverage, terminal-state evidence, and missing-field
  classification for G56R-002.
- Traceability from platform claims to official source IDs and from project
  inputs to route-policy surfaces.
- Reviewability and changed-file evidence that proves no runtime route policy
  changed.
- Pay special attention to lifecycle gaps, not-recorded fields, and
  observability evidence that is deferred rather than silently assumed.
```

#### 6. Reliability Checklist

```text
$speckit-checklist reliability

Focus on G56R-001 requirements:
- Observable source freshness, retrieval dates, invalidation triggers, and
  reproducible ledger review.
- Telemetry requirements and null/unknown handling for fields G56R-002 must
  verify.
- Capability-question completeness, no-go recovery guidance, and handoff
  ownership.
- Fallback-candidate requirements without premature ordering or availability
  claims.
- Pay special attention to changed official documentation, no eligible route,
  and incomplete evidence conditions.
```

### Checklist Results

| Checklist | Items | Gaps | Resolution |
|---|---|---|---|
| LLM integration | 15 | 1 | `spec.md` and workflow official candidate seed lists aligned with the current roadmap seed set; checklist now passes |
| Data integrity | 15 | 0 | No unresolved data-integrity requirement defects |
| Error handling | 15 | 0 | No unresolved error-handling requirement defects |
| Security | 15 | 0 | No unresolved security requirement defects |
| Observability | 15 | 0 | No unresolved observability requirement defects |
| Reliability | 15 | 0 | No unresolved reliability requirement defects |

All true gaps must update `spec.md` or `plan.md`, then the affected checklist
must be rerun before G4 passes.

G4 passed with zero checklist gap markers.

Chronology note: Phase 4 originally completed on `2026-07-15T23:29:14Z`.
`observability.md` was added during later review remediation on 2026-07-16 to
complete the six-domain operational checklist taxonomy, then revalidated with
the structural checks, Layer 1, and full suite.

---

## Phase 5: Tasks

**When to run:** After all six checklist domains are complete and true gaps
are resolved. Output: `specs/g56r-001-candidate-route-baseline/tasks.md`.

### Tasks Prompt

```text
$speckit-tasks

## Task Structure
- Organize tasks by independently reviewable research outcome, not by tool.
- Give every task an exact output path, source class, acceptance check, and
  AC-1.* reference.
- Mark [P] only for independent read-only inventory work that cannot create
  conflicting report edits.
- Require source-ledger completion before candidate admission tasks.
- Require role-contract completion before final candidate and fixture handoff.
- Keep report integration and strict go/no-go review sequential.

## Documentation Phases
1. Foundation: freeze official-source snapshot metadata and report skeleton.
2. US1 Evidence: complete official ledger and project-input surface inventory.
3. US2 Contracts: complete twelve role contracts and instruction hashes.
4. US3 Candidates: complete provisional document-eligible candidate routes.
5. US4 Handoff: complete executable fixture specifications, telemetry
   requirements, capability questions, invalidation rules, and go/no-go result.
6. Polish: run traceability, count, link, scope, diff, and repository checks.

## Constraints
- Create no runtime code, helper, runtime JSON manifest, platform-specific or
  runtime schema, agent TOML, fixture payload, generated payload, cache proof,
  install output, or version change. The shared planning manifest/schema pair
  is the sole packaging amendment.
- Use only the frozen official ledger for platform facts and candidate
  admission; label every repository-derived fact `project_input`.
- Preserve exactly twelve agent contracts and exactly three-current/nine-missing
  fixture records.
- A no-go result is valid output when strict completeness cannot be proven; do
  not weaken the gate to force progression.
- Keep one research slice, consistent with the estimator result of zero LOC and
  one suggested slice.
```

### Tasks Results

| Metric | Value |
|---|---|
| Total Tasks | 38 |
| Phases | 7 generated: setup, foundational, US1, US2, US3, US4, polish |
| Parallel Opportunities | 0 marked `[P]` because the implementation output is one shared report |
| User Stories Covered | US1, US2, US3, and US4 |
| G5 Gate | Pass - 38 tasks found |

---

## Atomicity Route

Autopilot populates this section after G5 by running the read-only classifier
against `specs/g56r-001-candidate-route-baseline`. The classifier records a
decision only; it does not create PRs or split branches.

| Field | Value | Meaning |
|---|---|---|
| Route | `one-navigable-PR` | Keep as one documentation PR |
| Releasable | `true` | Classifier found no release-safety warning |
| Signals | `change-shape:modify-heavy` | Structural finding behind the route |
| Warnings | none | No release-safety warnings |

---

## Phase 6: Analyze

**When to run:** Always run after tasks and atomicity classification.

### Analyze Prompt

```text
$speckit-analyze

Focus on:
1. Drift among the PRD AC-1.*, technical roadmap, design concept, spec, plan,
   checklists, and tasks.
2. Any platform claim or candidate supported by project input, runtime
   observation, third-party material, memory, inference, or an uncited source.
3. Missing or duplicate ledger, contract, candidate, fixture, or handoff IDs and
   broken cross-record bindings.
4. Exact coverage of twelve named agents and the three-current/nine-missing
   fixture inventory.
5. Scope leakage into TOML, installers, prompts, skills, payloads, runtime JSON,
   probes, live evaluation, qualification, preference, fallback ordering, or
   release claims.
6. Dependency-cycle risk: G56R-001 must end without requiring G56R-002 evidence.
7. Reviewability: one canonical report, one governed planning manifest, no
   speculative supporting artifacts, and no unplanned production surface.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|---|---|---|---|
| A1 | HIGH | Current roadmap seed models drifted from `spec.md` FR-010 and the workflow seed list | Resolved by aligning `spec.md` and workflow to the current roadmap seed set and preserving older model names only as historical exclusions |

G6 passes only when no `CRITICAL` or `HIGH` finding remains and every accepted
lower-severity finding has a recorded disposition.

## Phase 6.5: Confidence Gate

**When to run:** After G6 passes and before implementation begins. This gate is
advisory for G56R-001 and records whether current planning evidence is
sufficient to proceed into report authoring.

| Gate | Status | Evidence | Disposition |
|---|---|---|---|
| G6.5 | Advisory no-data | `confidence-gate` returned `NO_DATA` with `recommended_action=soft_skip` because no synthesizer confidence emit was present in the workflow | Proceed to implementation; G7 remains the binding verification gate |

The confidence gate cannot admit undocumented platform claims, relax the
official-documentation authority rule, or replace G7 verification.

---

## Phase 7: Implement

**When to run:** After tasks and analysis pass. In this research spike,
implementation means authoring and validating the canonical report, not
changing runtime behavior.

### Implement Prompt

```text
$speckit-implement

## Approach: Evidence First
1. SNAPSHOT: Revalidate current official OpenAI documentation, record URLs,
   page/surface identity, retrieval date, and invalidation metadata, then freeze
   `official_source_ledger_id` for this spec.
2. INVENTORY: Read repository, payload, cache, fixture, and Claude parity files
   only as `project_input`; record current surfaces and immutable routes.
3. CONTRACT: Complete all twelve `agent_contract_id` records, including safety,
   grounding, mutation, tool, skill, MCP, output, client, and representative-task
   requirements.
4. ADMIT: Create provisional candidate tuples only where the frozen official
   ledger and role contract both support admission; preserve every unsupported
   fact as `undocumented` and reject the dependent route.
5. HAND OFF: Complete the three-current/nine-missing executable fixture backlog,
   telemetry requirements, capability questions, invalidation rules, and strict
   G56R-002 go/no-go matrix.
6. VERIFY: Check sources, IDs, cross-references, exact counts, links, scope,
   changed files, Layer 1, and the deterministic repository suite.

## Pre-Implementation Setup
- Confirm `git rev-parse --abbrev-ref HEAD` returns
  `g56r-001-candidate-route-baseline`.
- Confirm the worktree has no unrelated changes with `git status --short`.
- Re-read the Evidence Authority sections in the PRD and roadmap and the six
  accepted Grill Me decisions.
- Do not install packages, run a build/index bootstrap, modify user-local
  configuration, or run live model probes; no such bootstrap is documented or
  required for this spec.
- Use current official OpenAI documentation only for platform research and cite
  direct official URLs in the canonical report.

## Implementation Notes
- Keep the canonical report self-contained and navigable with stable table IDs.
- Clearly label `official_documentation`, `project_input`, `undocumented`,
  proposed policy, deferred runtime verification, qualification evidence, and
  `non_release_evidence`.
- A successful local configuration or runtime response cannot repair absent
  official support.
- Do not state that a candidate is available, executable, qualified, preferred,
  efficient, optimal, or a fallback.
- Do not alter source agent definitions or derive final route policies.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|---|---|---|---|
| Foundation and official evidence | Complete | Complete | Execution-time source snapshot and report skeleton completed |
| Role contracts and candidates | Complete | Complete | Twelve contracts and provisional source-bound/blocked model candidates completed |
| Fixture and G56R-002 handoff | Complete | Complete | Exact fixture inventory, telemetry/capability backlog, and strict decision completed |
| Verification | Complete | Complete | G7 passed; `git diff --check`, Layer 1, and full suite passed |

---

## Post

| Item | Status | Notes |
|---|---|---|
| Post: Doctor Extension Check | Complete | Parent fallback health check passed |
| Post: Verify Implementation | Complete | G7 passed with all 38 tasks complete |
| Post: Verify Tasks Phantom Check | Complete | `verify-tasks-report.md` found no phantom completions |
| Post: Code Review | Complete | RepoPrompt reviews through `review-g56r-baseline-B40534` returned actionable findings; clean rerun `review-g56r-baseline-EE3373` returned no findings |
| Post: Integration Suite | Complete | Final full suite passed 2768/2768 |
| Post: Reviewability Diff Gate | Complete | Setup-mode runner gate passed; actual branch-diff backstop is 25 docs/process/test-guard files, warning-only above the 15-file warning threshold, and not above the 25-file block threshold |
| Post: Self-Review | Complete | Four-question self-review recorded below |
| Post: UAT Runbook Generation | Skipped | No committed runbook exists; `generate-uat-skeleton` is deferred |
| Post: Final Reviewability Backstop | Complete | Deferred helper boundary honored; current diff evidence is warning-only; PR side effect completed afterward by explicit user instruction |
| Post: PR Packet/Body Generation | Skipped | No current feature-local PR packet exists; `pr-packet-output` remains deferred |
| Post: PR Body Generation | Complete | Manual PR body was prepared from completed workflow evidence for draft PR #360 by explicit user instruction |
| Post: PR Creation | Complete | Draft PR #360 opened against `main`: https://github.com/racecraft-lab/racecraft-plugins-public/pull/360 |
| Post: Review Remediation | Complete | All RepoPrompt findings remediated; clean rerun `review-g56r-baseline-EE3373` returned no findings |
| Post: Retrospective | Complete | `retrospective.md` saved with no proposed spec changes |

---

## Post Results

### Extension And Review Results

| Item | Result |
|---|---|
| Doctor Extension Check | Pass: templates 5/5, agent directory present, 29 local skills, runner manifest valid, constitution present, feature artifacts complete |
| Verify Implementation | Pass: G7, marker search, exact counts, scope review, `git diff --check`, Layer 1, and full suite passed |
| Verify Tasks Phantom Check | Pass: 38/38 verified in `specs/g56r-001-candidate-route-baseline/verify-tasks-report.md` |
| Code Review | Pass: RepoPrompt reviews through `review-g56r-baseline-B40534` returned findings and were remediated; clean rerun `review-g56r-baseline-EE3373` returned no findings against the branch diff |
| Integration Suite | Pass: `python3 tests/speckit-pro/run-all.py` reported 2768/2768 |
| Reviewability Diff Gate | Warn/pass: installed `reviewability-gate` runner supports setup mode only and passed against `specs/g56r-001-candidate-route-baseline/plan.md`; actual branch-diff backstop records 25 docs/process/test-guard files, zero runtime production files, and a warning for total changed files over the 15-file warning threshold but not over the 25-file block threshold |
| Final Reviewability Backstop | Proceeded for validation; PR side effect completed afterward by explicit user instruction |
| PR Packet/Body Generation | Skipped because no `specs/g56r-001-candidate-route-baseline/.process/pr-packets/` packet exists and packet output remains deferred |
| PR Body Generation | Pass: manual PR body prepared from completed workflow evidence for draft PR #360 |
| PR Creation | Pass: draft PR #360 opened against `main` |

### Self-Review

**Tests executed?** No project build, typecheck, or lint command is documented
for this worktree. The relevant gates were run directly: G7 passed,
`git diff --check` passed, Layer 1 passed 1428/1428, the focused
`test-speckit-pro-runner.py` guard passed 11/11 after remediation, and the
final full suite passed 2768/2768 after review remediation.

**Edge cases?** G56R-001 is documentation-only. The report covers source
redirect/invalidation, unsupported and historical seed exclusion, parity-role
absence, prompt-emulation non-release status, telemetry gaps, and strict
G56R-002 no-go conditions. No runtime edge-case tests are applicable.

**Requirements matched?** FR-001 through FR-018 and SC-001 through SC-006 map
to the report traceability and completeness sections. All 38 tasks are checked
complete and verified in `verify-tasks-report.md`.

**Follow-up and tidiness?** Marker search found no live deferred-work,
placeholder, clarification, or critical markers. PR packet output remains
deferred because no feature-local packet exists; draft PR #360 was opened by
explicit user instruction using a manual body from the completed workflow
evidence.

## Post-Implementation Checklist

- [x] All tasks are complete in `tasks.md`.
- [x] `docs/ai/research/codex-agent-route-candidates.md` remains the canonical human report; the parity amendment adds only `docs/ai/research/codex-agent-route-candidate-manifest.json` as its governed planning companion.
- [x] The official-source ledger is dated, versioned, revalidated at execution, and contains source family, retrieval method, requested URLs, canonical official URLs, durable retrieval evidence, page or section locators, short excerpt anchors, bounded source-fact extracts, extract hashes, documented facts, and invalidation triggers for every platform claim.
- [x] Every repository, route-policy skill/runner surface, payload, cache, fixture, and Claude-definition fact is labeled `project_input`.
- [x] Exactly twelve unique `agent_contract_id` records exist and cover the named catalog.
- [x] Every provisional `candidate_route_id` binds official source IDs, one `agent_contract_id`, explicit effort-surface records, blocked model/effort tuple status where G56R-002 must discover supported efforts, and complete contract requirements.
- [x] No candidate relies on an `undocumented` fact or claims availability, executability, qualification, preference, or fallback order.
- [x] The fixture backlog contains exactly three current and nine missing records with executable specifications and no new payloads.
- [x] Telemetry requirements, terminal-state fields, missing-field classification, capability questions, invalidation triggers, and the strict G56R-002 go/no-go result are complete.
- [x] Historical prompt-emulation evidence is labeled `non_release_evidence`.
- [x] All six user-selected requirement-quality checklists have zero unresolved true gaps.
- [x] Relative links, stable IDs, counts, and source bindings pass focused validation.
- [x] `git diff --check` passes and changed-file review confirms no runtime, agent, installer, payload, cache, fixture payload, generated artifact, platform-specific or runtime schema, helper script, or version change.
- [x] `python3 tests/speckit-pro/run-all.py --layer 1` passes.
- [x] `python3 tests/speckit-pro/run-all.py` passes with zero failures.

---

## Project Structure Reference

```text
docs/ai/research/
  codex-agent-route-candidates.md          # G56R-001 canonical implementation output
  codex-agent-route-candidate-manifest.json # Schema-v2 planning evidence companion
docs/ai/specs/.process/
  G56R-001-design-concept.md               # Setup interview record
  G56R-001-workflow.md                     # Durable workflow state
specs/g56r-001-candidate-route-baseline/
  SPEC-MOC.md                              # Parent-roadmap join marker
  spec.md                                  # Requirements generated by Specify
  plan.md                                  # Documentation execution blueprint
  research.md                              # Planning decisions
  data-model.md                            # Record definitions when emitted by preset
  contracts/                               # Planning-only contracts when required
  checklists/                              # Requirements plus six domain audits
  tasks.md                                 # Ordered documentation tasks
speckit-pro/codex-agents/                  # Read-only current Codex role inputs
speckit-pro/agents/                        # Read-only Claude parity-role inputs
tests/speckit-pro/layer6-efficiency/       # Read-only fixture-gap inputs
```

---

## Completion Record

Populate this section only after G7:

- Initial canonical report commit: `b776814a`
- Final verified report content SHA-256: `272a495da0adf429acbaa6bfb759ec03a0afa7f73eaf49ee76270b3fbba83602`
- Frozen `official_source_ledger_id`: `OSL-001` through `OSL-009`
- Frozen `effort_surface_record_id`: `G56R-001-ESR-001` through `G56R-001-ESR-005`
- Historical report-embedded `agent_route_candidate_manifest` version: `agent_route_candidate_manifest.v0.1`
- Current planning manifest schema version: `2.0.0`
- Current official-source ledger: `OPENAI-DOC-001` through `OPENAI-DOC-021`
- Shared evidence foundation: PR #362, merged as `f2e664d5afbb9525f6486506425dc47c2f8bed12`
- Current report SHA-256: `b429a568ebc780bf638e6891eff6532deefae97c3ed4e5ef86cc7eced1436289`
- Current planning manifest SHA-256: `71d2ee129d5ca0fd407382ac5102566efe4c0321541514ee0eece38b29d6117d`
- Evidence-parity verification: validator 8/8, Layer 1 1428/1428,
  full suite 2811/2811, and docs reference check passed
- Publication: PR #360 merged into `main` as
  `191642962e55df21000a5303f36e9010a14898d2` after foundation PR #362; all
  checks passed and all three review threads were resolved
- G56R-002 handoff decision: `GO` for capability discovery and telemetry profiling only; `NO-GO` for executable candidate set, route qualification, installer behavior, resolver behavior, preferred routes, and fallback policy
- Verification summary: G7 passed with all 38 tasks complete; `git diff --check`, Layer 1, and full suite passed
- Remaining invalidation or follow-up items: Refresh official documentation before G56R-002 if source content, model lifecycle, app-server capability schema, telemetry schema, role source hashes, or fixture inputs change
