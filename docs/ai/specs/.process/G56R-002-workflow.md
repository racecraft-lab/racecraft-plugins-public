# SpecKit Workflow: G56R-002 — Capability Discovery, Telemetry Profile, and Exact-Treatment Contract

**Template Version**: 1.0.0
**Created**: 2026-07-16
**Purpose**: Freeze the source-bound executable Codex candidate set and its trustworthy treatment/trace contract before G56R-003 performs outcome-bearing evaluation.

---

## How to Use This Workflow

Start a Codex task rooted at the dedicated worktree, then run:

```text
$speckit-autopilot docs/ai/specs/.process/G56R-002-workflow.md
```

This workflow is fully populated for G56R-002. Do not run it from the parent
`main` checkout and do not replace it with the generic workflow template.

---

## Design Concept

The required setup interview is recorded at:

```text
docs/ai/specs/.process/G56R-002-design-concept.md
```

Its accepted decisions are binding inputs to every phase:

- Verify a pinned-build surface matrix across app-server, CLI, and interactive
  picker evidence.
- Record hidden model evidence but exclude hidden tuples unless the official
  source ledger independently admits them.
- Apply claim-scoped invalidation to any current `OPENAI-DOC-*` record proven
  changed; historical `OSL-*` rows are not the consuming ledger.
- If documented discovery is unavailable, permit one non-scored,
  timeout-bounded canary per source-admitted tuple and retain only redacted
  evidence.
- Require observed effective treatment or an approved configured-route proof
  plus reroute monitoring; requested configuration alone is insufficient.
- Preserve missing treatment or reroute evidence as `unknown` and exclude only
  the affected tuple.
- Commit deterministic sanitized fixtures, schemas, and hashes; keep raw live
  responses out of Git.
- Separate Codex capability collection from vendor-neutral treatment/trace
  schemas with the smallest practical orchestration entry point.
- Keep one guarded slice with three ordered increments. Surface disagreement
  excludes only the affected tuple.

Grill Me is human-in-the-loop only. Once autopilot begins, clarifications use
`$speckit-clarify` and the consensus protocol, never Grill Me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|---|---|---|---|
| Specify | `$speckit-specify` | Complete | Defined source, surface, snapshot, and treatment requirements; G1 passed |
| Clarify | `$speckit-clarify` | Complete | Resolved field-level and bounded-probe details; G2 passed |
| Plan | `$speckit-plan` | Complete | Designed one guarded three-increment slice; G3 and reviewability passed |
| Checklist | `$speckit-checklist` | Complete | Four risk-focused domains passed consensus; G4 passed |
| Tasks | `$speckit-tasks` | Complete | 39 TDD-first tasks; G5 passed |
| Analyze | `$speckit-analyze` | Complete | Nine findings remediated; G6 passed |
| Confidence Gate | G6.5 | Complete | Advisory score 0.99 passed the 0.90 threshold |
| Implement | `$speckit-implement` | In Progress | T001-T039 are implemented; the restacked US3 implementation/evidence head returned `NO FINDINGS`, with final metadata-head review pending |
| Post | Post-Implementation | Pending | Complete verification, reviewability, PR, remediation, and retrospective work |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|---|---|---|
| G1 | After Specify | AC-2.2 through AC-2.5 and the G56R-002 share of AC-2.19 are testable; no unresolved requirement markers remain |
| G2 | After Clarify | Surface joining, telemetry classification, canary bounds, null semantics, and evidence retention are unambiguous |
| G3 | After Plan | Architecture, schema ownership, reviewability, source invalidation, and one-slice ordering are approved |
| G4 | After Checklist | All true gaps from the four selected domains are remediated or explicitly rejected as out of scope |
| G5 | After Tasks | Every requirement maps to an ordered, independently verifiable task and no qualification or installer work leaks in |
| G6 | After Analyze | No critical or high inconsistency, authority violation, treatment-proof gap, or reviewability blocker remains |
| G6.5 | Before Implement | Record and evaluate pre-implementation confidence; advisory mode may continue after bounded remediation |
| G7 | After Each Implementation Increment | Focused tests, synthetic replay, diff hygiene, and the applicable repository gates pass |

---

## Prerequisites

### Worktree and Branch

- Worktree: `.worktrees/g56r-002-capability-discovery-telemetry`
- Branch: `g56r-002-capability-discovery-telemetry`
- Feature directory: `specs/g56r-002-capability-discovery-telemetry`
- Contract marker: `specs/g56r-002-capability-discovery-telemetry/SPEC-MOC.md`
- Design concept: `docs/ai/specs/.process/G56R-002-design-concept.md`
- Workflow: `docs/ai/specs/.process/G56R-002-workflow.md`

The branch must track `origin/g56r-002-capability-discovery-telemetry` before
autopilot begins. Spec, plan, and task templates must continue resolving to the
`speckit-pro-reviewability v1.0.0` preset unless a deliberate repository
override is documented.

### Grounded Source Truth

- Technical roadmap:
  `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`
- Product requirement: `docs/prd-codex-gpt-5-6-agent-routing.md`, especially
  AC-2.2 through AC-2.5, AC-2.19, and OQ-1 through OQ-4.
- Design decisions:
  `docs/ai/specs/.process/G56R-002-design-concept.md`.
- G56R-001 canonical report:
  `docs/ai/research/codex-agent-route-candidates.md`.
- G56R-001 planning manifest:
  `docs/ai/research/codex-agent-route-candidate-manifest.json`.
  Its 22 `OPENAI-DOC-*` rows are the current v3 consumption ledger; the
  report's `OSL-*` rows remain historical evidence only.
- Shared parity contract:
  `docs/ai/specs/agent-routing-parity-contract.md`.
- Shared schema:
  `docs/ai/research/agent-route-candidate-manifest.schema.json`.
- Project constitution: `.specify/memory/constitution.md`.
- Project agent contract: `AGENTS.md`.
- Current official app-server model discovery:
  <https://learn.chatgpt.com/docs/app-server#list-models-modellist>.
- Current official app-server turn and reroute events:
  <https://learn.chatgpt.com/docs/app-server#turn-events>.
- Direct GPT-5.6 prompting guide:
  <https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6.md>.
  It may establish API-surface prompt-treatment facts only; it cannot establish
  Codex custom-agent fields, availability, defaults, telemetry, or exact
  treatment.
- Current official MCP page included in execution-time source revalidation:
  <https://learn.chatgpt.com/docs/extend/mcp>.

Capability path: current Codex app-server contract -> Context7
`/websites/developers_openai_codex` plus official OpenAI documentation -> local
roadmap, PRD, and G56R-001 handoff. Confidence is high for documented
app-server fields and conditional reroute events. Any CLI or picker field
without direct documentation remains runtime evidence only.

### Phase 0 Preflight Results

| Check | Result | Evidence |
|---|---|---|
| Main synchronization | Pass | Worktree was created from current `origin/main` at `b57d21a8` on 2026-07-16 |
| Remote | Pass | Detected `origin` at `https://github.com/racecraft-lab/racecraft-plugins-public.git` |
| Worktree and branch | Pass | Dedicated worktree registered on `g56r-002-capability-discovery-telemetry` |
| Codex agent install | Pass | Python-authoritative dry run found all ten bundled Codex agent TOMLs current with `mutation_status=no_op` |
| SpecKit CLI | Pass | `specify 0.12.12.dev0` is available |
| Repository bootstrap | Not required | `AGENTS.md` and `CLAUDE.md` document no bootstrap, package-install, build, or index command; none was run |
| Reviewability setup gate | Warn/pass | Roadmap gate returned pass with an advisory three-primary-surface warning and no blocker |
| Spec size estimator | Pass | Three stories, ten files, and eight requirements returned 297 estimated reviewable LOC, one suggested slice, and `status=ok` |
| Split decision | Accepted | Keep one guarded slice with three ordered increments and re-run the gate during planning |
| Grill Me | Complete | Ten picker questions reached a natural stop; all decisions are in the Design Concept |
| Preset resolution | Pass | Spec, plan, and tasks templates resolve to `speckit-pro-reviewability v1.0.0` |
| Legacy relocation | Not applicable | No `.specify/feature.json` or legacy G56R-002 artifacts require relocation |
| Official-source refresh | Partial / pending phase work | Scaffold verified current app-server fields and spot-checked source families; all 22 current `OPENAI-DOC-*` records still require execution-time revalidation before candidate freeze |

The setup warning is advisory. Planning must re-estimate the extracted
G56R-002 change, preserve the 265-LOC roadmap target where practical, and stop
for decomposition if a binding threshold is crossed.

### Constitution Validation

| Principle | G56R-002 Requirement | Verification |
|---|---|---|
| Plugin Structure Compliance | Keep implementation in the existing layer6 efficiency harness and repository-owned tests; do not mutate agent or installer surfaces | Planned-file review and changed-file validation |
| Cross-Platform Runtime and Script Safety | Use Python 3.11+ standard library; add no active Bash, `jq`, platform shell dependency, or unbounded subprocess behavior | Code review plus active-path checks selected by the suite |
| Test Coverage Before Merge | Develop against sanitized deterministic fixtures, then run focused tests, Layer 1, and the full deterministic suite | Recorded command results and G7 evidence |
| Conventional Commits | Use repository-valid lowercase conventional commit scopes and validate the final PR title before readiness | Git history and release-readiness gate |
| KISS, Simplicity, YAGNI | Use a Codex adapter, neutral schemas, and only the smallest orchestration seam; no cross-vendor framework | Plan complexity review and G6 analysis |

**Constitution Check:** Passed at G1 and re-checked after planning before G3.

---

## Specification Context

### Basic Information

| Field | Value |
|---|---|
| **Spec ID** | G56R-002 |
| **Name** | Capability Discovery, Telemetry Profile, and Exact-Treatment Contract |
| **Branch** | `g56r-002-capability-discovery-telemetry` |
| **Dependencies** | G56R-001 and the shared official-source evidence foundation |
| **Enables** | G56R-003 Evaluation Runner, Fixtures, Scoring, and Statistical Analysis |
| **Priority** | P1 |
| **Roadmap target** | 265 reviewable LOC, approximately 3 production files, approximately 10 total files |
| **Scaffold estimate** | 297 reviewable LOC, one guarded slice |

### Evidence and Surface Contract

| Evidence | Permitted use | Prohibited use |
|---|---|---|
| Current official documentation | Establish documented schemas, fields, surfaces, and platform facts | Support a claim absent from the cited field-level source |
| G56R-001 source ledger | Admit source-bound model candidates and effort-surface concepts | Prove runtime availability or exact treatment |
| App-server discovery | Verify pinned-environment model, effort, and provider capability availability under the documented schema | Admit undocumented candidates or create new platform facts |
| CLI and picker observations | Cross-check the pinned client experience and detect surface mismatches | Override an official source or broaden eligibility |
| One-canary fallback | Establish pinned-environment availability when documented discovery is unavailable | Establish model support, effort support, eligibility, quality, or preference |
| Configured-route proof | Prove requested assignment only when the telemetry profile explicitly approves it and reroute monitoring is present | Prove an undocumented effective model or effort |

Surface disagreement, hidden status without independent admission, missing
treatment proof, and missing reroute evidence each produce a tuple-local
exclusion with explicit evidence. They do not become global snapshot failure
unless the snapshot itself is malformed, unversioned, or unbound to the pinned
client.

### Success Criteria Summary

- [ ] AC-2.2: A versioned surface-matrix aggregate composes surface-keyed
  `runtime_capability_snapshot_id` observations for the pinned Codex build;
  app-server, CLI, and picker fields are not collapsed before Clarify freezes
  the join key. Each environment-scoped record binds its surface, discovered
  models, supported efforts, relevant capabilities, method, timestamp, and the
  raw discovery response or an explicit content-addressed raw-evidence
  reference retained outside Git. Committed fixtures remain sanitized and
  hash-bound, and runtime observation never becomes platform authority.
- [ ] AC-2.3: Every assigned objective/run binds its pinned client/surface,
  candidate route, controlled repository snapshot and task/fixture identity,
  `candidate_route_id`, `agent_contract_id`,
  `runtime_capability_snapshot_id`, `route_resolution_id`,
  `experiment_policy_id`, and `execution_trace_id`.
- [ ] Each `route_resolution_id` records preferred and effective route,
  attempted routes, fallback index and reason, capability snapshot, and
  timestamp while keeping service reroute distinct from resolver selection.
- [ ] Exact-treatment traces record the named agent, explicit model and effort,
  assigned and requested route, supported effective-route evidence, instruction
  hash, sandbox/approvals/mutation class, expected and loaded skills/MCP/tools,
  parent configuration, pinned client, controlled overrides, delivery canary,
  treatment failures, context, parent-child graph, validation, cancellation,
  outcome/acceptance, terminal state, and explicit null behavior.
- [ ] AC-2.4: Surface-keyed `telemetry_profile_id` records within the matrix
  classify every desired field
  as `stable_native`, `experimental_native`,
  `derived_from_controlled_configuration`, `conditional`, `unavailable`,
  `not_applicable`, or `undocumented`, with its source, completeness rule, and
  permitted claims. Returned effort, effective model, speed, token categories,
  and parent attribution are never fabricated.
- [ ] AC-2.5 boundary: The schema carries the complete objective-level raw token
  vector, request/turn count, wall time, retries, compaction, and failed or
  abandoned work through terminal policy without selecting a score,
  comparator, or qualification rule in G56R-002.
- [ ] AC-2.19 share: Exact treatment requires profiled proof, service reroute is
  distinct from resolver fallback, and every service-rerouted run is
  non-scorable as the requested route. Runtime UAT may continue only when the
  destination is already prequalified for the same named agent; otherwise
  treatment fails. Unapproved, unidentifiable, or unknown reroutes hard-fail.
- [ ] G56R-001 source-bound candidates, plus any newly recorded
  official-ledger-bound role/model binding for a model already in the canonical
  candidate set, expand only into surface-supported executable model/effort
  tuples and freeze before G56R-003. Runtime discovery never adds a model.
- [ ] Synthetic replay covers success, null, unavailable field, misdelivery,
  an approved same-agent prequalified-destination reroute with requested-route
  non-scorability, an unapproved or unidentifiable hard-fail reroute, surface
  disagreement, and unavailable discovery records.
- [ ] Raw live responses remain outside Git; committed fixtures are sanitized,
  deterministic, and hash-bound.

---

## Phase 1: Specify

**When to run:** At the start of G56R-002. Define what the executable candidate
freeze and treatment evidence must prove, not how later candidates score.
Output: `specs/g56r-002-capability-discovery-telemetry/spec.md`.

### Specify Prompt

```text
$speckit-specify

## Feature: Capability Discovery, Telemetry Profile, and Exact-Treatment Contract

### Problem Statement
G56R-003 cannot run outcome-bearing evaluation until G56R-001's source-bound
candidate catalog is narrowed to executable model/effort tuples for a pinned
Codex build and every run has a trustworthy, null-preserving treatment/trace
contract. App-server, CLI, and interactive picker evidence can differ; runtime
observations cannot create undocumented platform facts, and requested
configuration alone cannot prove effective treatment.

### Users
- Routing maintainers who must freeze a source-bound executable candidate set.
- Evaluation authors who need exact-treatment and telemetry schemas before
  creating scored traces.
- Release reviewers who need claim-scoped source invalidation, sanitized
  replay evidence, and explicit unknown outcomes.

### User Stories
1. As a capability steward, I can pin a Codex build, collect app-server, CLI,
   and picker evidence, and freeze only source-admitted model/effort tuples
   whose surfaces agree and whose availability is supported.
2. As an evaluation designer, I can classify every desired telemetry field and
   prove requested or effective treatment without inferring missing values or
   confusing service reroutes with plugin fallback.
3. As a test author, I can replay sanitized deterministic success, null,
   unavailable, misdelivery, and reroute records before any live corpus run.

### Constraints
- Revalidate the G56R-001 official-source ledger before candidate freeze.
- Revalidate all 22 current `OPENAI-DOC-*` manifest records before candidate
  freeze. Apply invalidation only to the current claims proven changed; do not
  consume or rewrite historical `OSL-*` rows as the active ledger.
- Revalidate the direct GPT-5.6 prompting guide and bind it only to API-surface
  prompt treatment. Do not use it for Codex custom-agent fields, availability,
  defaults, telemetry, or exact-treatment claims.
- Use the documented app-server `model/list` and
  `modelProvider/capabilities/read` contracts, then cross-check CLI and picker
  observations for the same pinned build.
- Preserve app-server, CLI, and picker observations as surface-keyed snapshot
  and telemetry-profile records under one versioned matrix aggregate until
  Clarify freezes the normalization and join key; never collapse contradictory
  fields. Bind every run to the pinned client/surface, candidate route,
  controlled repository snapshot, and task/fixture identity without defining
  G56R-003's corpus.
- Preserve hidden entries as evidence but exclude them absent independent
  official-ledger admission.
- Permit a new role/model binding only when the model already exists in the
  canonical official-ledger candidate set and the new binding records its
  source and agent-contract rationale. Runtime discovery cannot add a model.
- When documented discovery is unavailable, permit at most one non-scored,
  timeout-bounded canary per source-admitted tuple; retain only redacted
  evidence and make no platform-support claim from it.
- Require observed effective treatment or an approved configured-route proof
  plus reroute monitoring. Missing evidence is `unknown`, not success.
- For every telemetry field, record its classification, source, completeness
  rule, and permitted claims. Never fabricate returned effort, effective model,
  speed, token categories, or parent attribution.
- Require every assigned objective to bind `candidate_route_id`,
  `agent_contract_id`, `runtime_capability_snapshot_id`,
  `route_resolution_id`, `experiment_policy_id`, and `execution_trace_id`.
- Define route-resolution records with preferred/effective route, attempted
  routes, fallback index/reason, snapshot, and timestamp. Define treatment
  traces with named agent, explicit model/effort, instruction hash,
  assigned/requested/effective route evidence, sandbox/approvals/mutation class,
  expected and loaded skills/MCP/tools, parent configuration, pinned client,
  controlled overrides, delivery canary, treatment failures, context,
  parent-child graph, complete raw token vector, request/turn count, wall time,
  retries, compaction, validation, cancellation, failed/abandoned work,
  terminal state, outcome/acceptance, and explicit null behavior.
- Surface mismatch or unknown treatment excludes only the affected tuple.
- Mark every service-rerouted run non-scorable as the requested route. Define
  runtime-UAT continuation only for a destination already prequalified for the
  same named agent; otherwise fail treatment. An unapproved, unidentifiable, or
  unknown reroute is a hard treatment failure.
- Capture raw capability evidence, or a content-addressed reference to it, in
  the runtime snapshot under the Clarify/Plan retention contract outside Git.
  Commit only sanitized deterministic fixtures and hashes.
- Separate Codex collection from vendor-neutral treatment/trace schemas and use
  the smallest practical orchestration seam.
- Keep one guarded slice with three ordered increments and re-run the
  reviewability gate before implementation.
- Use Python 3.11+ standard library and existing repository tooling only.

### Out of Scope
- Corpus execution, scores, statistical qualification, ranking, preference,
  fallback ordering, resolver policy, installation, defaults, agent TOML,
  payload regeneration, or release claims.
- Raw live responses in Git, broad or repeated availability campaigns, and
  cross-vendor probing abstractions.
- Treating CLI lifecycle JSON, picker visibility, successful invocation, or
  configured intent as universal proof of effective model or effort.
```

### Specify Results

| Metric | Value |
|---|---|
| Functional Requirements | 8 |
| User Stories | 3 |
| Acceptance Criteria | AC-2.2 through AC-2.5 plus the G56R-002 portion of AC-2.19 |
| G1 Gate | Passed — `spec.md` exists with 0 unresolved markers |

### Files Generated

- [x] `specs/g56r-002-capability-discovery-telemetry/spec.md`
- [x] `specs/g56r-002-capability-discovery-telemetry/checklists/requirements.md`

**Documentation refresh:** Context7 transport was unavailable during Specify;
the phase used the official OpenAI documentation MCP as the authoritative
fallback and bounded undocumented runtime shapes to discovery evidence.

### Traceability Markers

Use `[US1]`, `[US2]`, `[US3]`, and `[FR-NNN]` consistently. No
`[NEEDS CLARIFICATION]` marker may remain when G1 passes. Later tasks must carry
the relevant user-story and requirement IDs.

---

## Phase 2: Clarify

**When to run:** After Specify. Do not reopen accepted Grill Me decisions.
Resolve only the implementation-independent evidence rules still required for
a testable specification.

### Clarify Prompts

#### Session 1: Surface Matrix and Candidate Freeze

```text
$speckit-clarify Focus on the pinned app-server, CLI, and interactive-picker surface matrix: exact client-version identity, deterministic observation methods, normalization keys, hidden-status handling, disagreement records, tuple-local exclusion, snapshot-wide invalidity, and candidate-freeze immutability. Preserve official documentation as the only platform authority.
```

#### Session 2: Telemetry and Exact Treatment

```text
$speckit-clarify Focus on each field's telemetry classification, official source, completeness rule, and permitted claims; approved configured-route proof; effective-route evidence; documented `model/rerouted` events; missing observations as unknown; null preservation; and the boundary between service reroute and resolver-selected fallback. Never fabricate returned effort, effective model, speed, token categories, or parent attribution.
```

#### Session 3: Probe Bounds and Evidence Retention

```text
$speckit-clarify Focus on the one-canary fallback contract: timeout, output cap, retry prohibition or independently proven transient exception, error taxonomy, redaction, local raw-evidence retention, deterministic fixture derivation, hashes, and synthetic replay acceptance. The probe remains non-scored and cannot establish support or eligibility.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---|---|---|---|
| 1 | Surface matrix and candidate freeze | 6 | Frozen client identity, deterministic collection, normalization, hidden-state, aggregate-invalidity, and immutable-freeze rules |
| 2 | Telemetry and exact treatment | 6 | Frozen profile keys/classes, configured-route proof, effective evidence, reroute separation, and typed null states |
| 3 | Probe bounds and evidence retention | 6 | Frozen canary envelope, error taxonomy, redaction, retention, fixture hashing, and replay acceptance |

**G2 Gate:** Passed — 0 `[NEEDS CLARIFICATION]` markers remain.

---

## Phase 3: Plan

**When to run:** After the specification is finalized. Generate the technical
blueprint and re-run reviewability before any implementation task begins.
Output: `specs/g56r-002-capability-discovery-telemetry/plan.md`.

### Plan Prompt

```text
$speckit-plan

## Technical Context
- Runtime: Python 3.11+ standard library in the existing
  `tests/speckit-pro/layer6-efficiency/` harness.
- Protocol input: documented Codex app-server initialization,
  `model/list`, `modelProvider/capabilities/read`, and conditional
  `model/rerouted` events for a pinned client build.
- Cross-surface evidence: bounded CLI and interactive-picker observations from
  the same pinned build, normalized without promoting runtime evidence to
  official platform authority.
- Controlled environment: every run binds the pinned client/surface, candidate
  route, repository snapshot, and task/fixture or objective identity. G56R-002
  defines these identity fields but does not design the G56R-003 corpus.
- Raw-evidence boundary: the runtime snapshot retains the raw response or an
  explicit content-addressed external reference; repository fixtures are
  sanitized and hash-bound. Clarify and Planning must freeze the local
  retention path, lifetime, access boundary, and sanitization procedure.
- Data contracts: shared G56R/CAR evidence taxonomy and manifest schema,
  extended through runtime capability snapshot, telemetry profile,
  route-resolution, and exact-treatment trace records. Every assigned
  objective must join `candidate_route_id`, `agent_contract_id`,
  `runtime_capability_snapshot_id`, `route_resolution_id`,
  `experiment_policy_id`, and `execution_trace_id`.
- Tests: deterministic sanitized fixtures and existing Python-authoritative
  repository validation.

## Accepted Architecture Decisions
- "Surface Matrix": compare app-server, CLI, and interactive picker; a mismatch
  excludes only the affected tuple.
- "Record, Exclude": retain hidden entries but require independent
  source-ledger admission before eligibility.
- "Profiled Proof": require observed effective treatment or approved
  configured-route proof plus reroute monitoring.
- "Redacted Fixtures": commit sanitized deterministic fixtures, schemas, and
  hashes; keep raw live responses out of Git.
- "Adapter Plus Schema": isolate Codex collection from vendor-neutral
  treatment/trace schemas and add only the smallest orchestration seam.
- "One Guarded Slice": plan three ordered increments and rerun reviewability
  before code.

## Ordered Increments
1. Capability freeze: claim-scoped source refresh, pinned surface matrix,
   surface-keyed capability snapshots and telemetry profiles under a versioned
   aggregate, controlled repository/task identity, expansion of existing
   source-bound candidates and
   bounded new role/model bindings for already-canonical models, and
   tuple-local exclusions. Discovery cannot broaden the model catalog.
2. Treatment contracts: telemetry profile, route-resolution schema,
   exact-treatment trace schema, six-ID objective bindings, preferred/effective
   and attempted route fields, assigned/requested route fields, exact
   agent/configuration/tooling fields, context and parent-child graph,
   resource/lifecycle/validation/cancellation/outcome fields, null rules, and
   reroute semantics.
3. Synthetic replay: sanitized fixtures for success, null, unavailable,
   misdelivery, approved/unapproved reroute, discovery loss, and surface
   disagreement.

## Constraints
- Prefer the roadmap-proposed
  `tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py` and
  `tests/speckit-pro/layer6-efficiency/lib/treatment_trace_schema.py` surfaces.
  Put orchestration in an existing harness seam when possible; create a third
  production file only when planning proves it is simpler and within budget.
- Target 265 reviewable LOC and approximately ten total files. Record the
  scaffold estimate of 297 LOC and stop for decomposition if the setup or plan
  gate blocks, if the slice exceeds 400 estimated LOC, or if the three
  increments cannot remain independently testable.
- Reuse schema/evidence concepts from CAR only; do not port Claude-specific
  probing mechanics or create a shared vendor framework.
- Bound subprocesses, inputs, outputs, timeouts, and errors deterministically.
- Add no Bash, `jq`, third-party package, agent definition, installer, payload,
  default, score, comparator, qualification rule, or fallback order.
- Follow `docs/ai/specs/.process/G56R-002-design-concept.md` and preserve every
  chosen answer exactly.

## Required Plan Artifacts
- `plan.md` with constitution and reviewability decisions.
- `research.md` for field-level source bindings and surface-method decisions.
- `data-model.md` for snapshot, profile, candidate tuple, six-ID objective join,
  preferred/effective/attempted route resolution, exact agent treatment,
  raw discovery evidence or external reference, raw resource/lifecycle
  evidence, mismatch, and invalidation records.
- `contracts/` for deterministic schemas or contract examples when needed.
- `quickstart.md` for safe pinned-build collection and synthetic validation.
```

### Plan Results

| Artifact | Status | Notes |
|---|---|---|
| `plan.md` | Complete | 297-LOC binding estimate; one guarded slice retained |
| `research.md` | Complete | Native claims bound to current official evidence; CLI/picker remain runtime-only |
| `data-model.md` | Complete | Preserves null, unknown, mismatch, exclusion, reroute, and successor states |
| `contracts/` | Complete | Two deterministic planning schemas; no qualification or installer schema |
| `quickstart.md` | Complete | Safe operator collection and offline replay; raw live evidence stays outside Git |

### Planning Reviewability Inputs

- Reviewable LOC: 297
- Production Files: 2
- Total Files: 10
- Primary Surface: harness/adapter

These explicit post-plan values supersede the scaffold's prose estimate for
gate parsing. `schema/data contract` remains a secondary review surface.

**Plan review:** Independent conformance review passed. **G3 Gate:** Passed —
`plan.md` exists with 0 unresolved markers. The reviewability gate passed with
no warnings or blockers.

---

## Phase 4: Domain Checklists

**When to run:** After `$speckit-plan`. Run these four domains because the
highest risks are model-surface claims, evidence integrity, fail-closed
behavior, and telemetry observability.

### Checklist Prompts

#### 1. LLM Integration Checklist

```text
$speckit-checklist llm-integration

Focus on G56R-002 requirements:
- Source-admitted model/effort tuples and documented app-server fields.
- Pinned-build app-server, CLI, and picker normalization without authority drift.
- Hidden candidates, configured-route proof, effective treatment, and unknowns.
- Service reroute versus resolver fallback and non-scorable treatment failures.
- Pay special attention to any inferred model, effort, capability, or native field.
```

#### 2. Data Integrity Checklist

```text
$speckit-checklist data-integrity

Focus on G56R-002 requirements:
- Stable snapshot, profile, candidate, contract, resolution, and trace IDs.
- Foreign-key-style bindings to G56R-001 source, effort, and agent records.
- Null preservation, tuple-local exclusion, immutable freeze, timestamps, and hashes.
- Sanitized fixture provenance without committed raw live responses.
- Pay special attention to orphan tuples, duplicate IDs, stale current-ledger bindings, historical `OSL-*` leakage, and lossy normalization.
```

#### 3. Error Handling Checklist

```text
$speckit-checklist error-handling

Focus on G56R-002 requirements:
- Discovery unavailable, malformed response, timeout, output cap, and probe failure.
- Hidden model, unsupported effort, surface mismatch, unknown treatment, and misdelivery.
- Approved, unapproved, unidentifiable, and missing service-reroute evidence.
- Claim-scoped source invalidation and deterministic recovery guidance.
- Pay special attention to paths that silently assume success or retry outcome-bearing work.
```

#### 4. Observability Checklist

```text
$speckit-checklist observability

Focus on G56R-002 requirements:
- Field-level telemetry source, classification, completeness, and supported claim.
- Requested versus effective route, reroute events, raw token vectors, duration,
  lifecycle, parent-child graph, retries, compaction, and terminal state.
- Missing observation as unknown rather than negative proof.
- Snapshot timestamp, pinned client/surface identity, evidence method, and invalidation.
- Pay special attention to any field classified native without an official citation.
```

### Checklist Results

| Checklist | Items | Gaps | Resolution |
|---|---|---|---|
| LLM integration | 28 | 0 | Independent consensus PASS; no inferred platform fact or treatment gap |
| Data integrity | 30 | 0 | Independent consensus PASS; identity, FK, null, hash, retention, and provenance contracts complete |
| Error handling | 33 | 0 | Independent consensus PASS; every recovery is fail-closed and bounded |
| Observability | 32 | 0 | Independent consensus PASS; every field has source, completeness, claim, and null semantics |

Every accepted gap must update `spec.md` or `plan.md`, then the affected
checklist must be rerun before G4 passes.

**G4 Gate:** Passed — all 123 domain items passed consensus and 0 `[Gap]`
markers remain in `spec.md` or `plan.md`.

---

## Phase 5: Tasks

**When to run:** After all four checklists pass. Output:
`specs/g56r-002-capability-discovery-telemetry/tasks.md`.

### Tasks Prompt

```text
$speckit-tasks

## Required Inputs
- `specs/g56r-002-capability-discovery-telemetry/spec.md`
- `specs/g56r-002-capability-discovery-telemetry/plan.md`
- `docs/ai/specs/.process/G56R-002-design-concept.md`
- All completed G56R-002 domain checklists

## Task Structure
- Order tasks by the three accepted vertical increments: capability freeze,
  treatment contracts, then synthetic replay.
- Use TDD: write the failing sanitized fixture or contract test before the
  smallest implementation change.
- Give every task an exact file path, acceptance check, `[USn]` marker, and
  `[FR-NNN]` references.
- Mark `[P]` only when tasks do not edit the same adapter, schema, fixture, or
  generated index surface.
- Require complete execution-time revalidation of the 22-row current v3 ledger
  before a task consumes its claims; keep historical `OSL-*` rows out of the
  active evidence path.
- Require snapshot and tuple-freeze tests before treatment schema work, and
  schema/null tests before replay integration.
- Require explicit task coverage for all six objective bindings; every
  route-resolution field; every named-agent/configuration/tooling treatment
  field; and AC-2.5 request/turn, failed/abandoned-work, and terminal-policy
  evidence.

## Reviewability Constraints
- Preserve one guarded slice and the three-file production budget unless the
  plan gate explicitly requires decomposition.
- Keep committed evidence sanitized and deterministic; raw live responses are
  never task outputs.
- Do not add corpus runs, scorers, statistical analysis, preferred routes,
  fallback ordering, installer changes, agent TOML changes, generated payloads,
  version changes, or a cross-vendor probing framework.
- Include focused tests, spec-MOC/index checks, Layer 1, full deterministic
  suite, diff review, and final PR-title validation tasks.
```

### Tasks Results

| Metric | Value |
|---|---|
| Total Tasks | 39 |
| Phases | Three implementation increments plus integration and polish |
| Parallel Opportunities | 2 (generated test reference and SPEC-MOC only) |
| User Stories Covered | US1, US2, and US3 |

**G5 Gate:** Passed — all 39 tasks have exact paths, acceptance checks,
user-story markers, and functional-requirement traceability.

---

## Atomicity Route

After G5, autopilot must run the read-only atomicity classifier against
`specs/g56r-002-capability-discovery-telemetry` and record its decision here.
The classifier records structure only; it does not create PRs or split branches.

| Field | Value | Meaning |
|---|---|---|
| Route | `one-navigable-PR` | Modify-heavy guarded slice remains easiest to review as one PR |
| Releasable | `true` | No destructive-migration or concurrency-sensitive signal |
| Signals | `change-shape:modify-heavy` | Classifier found no proven additive multi-seam split |
| Warnings | None | Classifier returned no release-safety warnings |

## Layer Plan

| Field | Value |
|---|---|
| Status | Skipped |
| Reason | Atomicity route is `one-navigable-PR`; layer planning is required only for `split-PR` |
| Implementation increments | Capability freeze (T001-T015), exact-treatment contracts (T016-T025), synthetic replay (T026-T030), integration and polish (T031-T039) |

---

## Phase 6: Analyze

**When to run:** Always run after tasks and atomicity classification.

### Analyze Prompt

```text
$speckit-analyze

Focus on:
1. Drift among the PRD AC-2.2 through AC-2.5 and AC-2.19, technical roadmap,
   G56R-001 handoff, Design Concept, spec, plan, checklists, and tasks.
2. Any platform claim supported only by runtime discovery, CLI/picker state,
   successful invocation, repository state, memory, inference, historical
   `OSL-*` evidence, or a current `OPENAI-DOC-*` record not revalidated for this run.
3. Any use of the direct GPT-5.6 prompting guide outside API-surface prompt
   treatment, especially for Codex custom-agent fields, availability, defaults,
   telemetry, or exact treatment.
4. Missing or duplicate `candidate_route_id`, `agent_contract_id`,
   `runtime_capability_snapshot_id`, `route_resolution_id`,
   `experiment_policy_id`, or `execution_trace_id`; broken source/effort/agent
   bindings; and incomplete preferred/effective/attempted route records.
5. Any path that treats configured intent as effective treatment, missing
   reroute evidence as proof of no reroute, service reroute as plugin fallback,
   or a rerouted run as scorable for its requested route.
6. Tuple-local exclusion coverage for hidden, mismatched, unknown,
   unavailable, misdelivered, and unapproved-reroute cases.
7. Scope leakage into corpus execution, scoring, statistics, qualification,
   ranking, fallback order, installation, agent configuration, payloads, or versioning.
8. Reviewability against the 265-LOC target, 297-LOC scaffold estimate,
   approximately three production files, ten implementation files, and one guarded slice.
9. Verification coverage for sanitized fixtures, raw-evidence exclusion,
   Python 3.11 standard-library constraints, and the selected repository gates.
10. Exact-treatment coverage for named agent, model/effort, instruction hash,
   assigned/requested/effective route evidence, sandbox/approvals/mutation
   class, expected and loaded skills/MCP/tools, parent configuration,
   client/overrides, delivery canary, treatment failures, context,
   parent-child graph, request/turn count, validation, cancellation, outcome,
   acceptance, explicit null behavior, and failed or abandoned work through
   terminal policy.
11. Telemetry-profile coverage for every field's source, completeness rule,
   permitted claims, and explicit prohibition on fabricating returned effort,
   effective model, speed, token categories, or parent attribution.
12. Service-reroute continuation only when the destination is already
   prequalified for the same named agent, with treatment failure for every
   unapproved, unidentifiable, unknown, or otherwise ineligible destination.
13. Controlled-environment binding for pinned client/surface, candidate route,
   repository snapshot, and task/fixture identity, without leaking G56R-003
   corpus design into this spec.
14. Surface-keyed snapshot/profile records remain distinct inside the matrix
   until the clarified join key reconciles them; contradictory fields are never
   collapsed or silently overwritten.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|---|---|---|---|
| A-001 | HIGH (resolved) | Treatment contract omitted controlled repository/task binding | Added an environment owner registry, trace references, equality invariants, and T018/T021 missing-owner/mismatch coverage |
| A-002 | HIGH (resolved) | Raw service-reroute event could not prove a same-agent prequalified destination | Kept the raw event immutable and added destination assessment plus a read-only qualification owner registry; synthetic evidence cannot authorize live continuation |
| A-003 | HIGH (resolved) | Closed trace schema omitted structured treatment failures | Added the required closed failure collection and T016/T019/T021 coverage |
| A-004 | MEDIUM (resolved) | Telemetry entries omitted observation-state rules required by the data model | Added required state/value/evidence rules and T016/T017/T020 validation |
| A-005 | MEDIUM (resolved) | Owning-ID collision checks were incomplete | Enumerated owner uniqueness, preserved repeated foreign keys, and added T018/T021 collision coverage |
| A-006 | MEDIUM (resolved) | Spec-ID fixture directory violated the behavior-named fixture contract | Renamed the namespace to `capability-treatment-replay` everywhere |
| A-007 | HIGH (resolved) | In-band `fixture_digest` made exact-byte hash-before-parse self-referential | Added an out-of-band digest manifest and manifest-first replay contract |
| A-008 | HIGH (resolved) | Portable stdlib code could not unconditionally promise live process-tree control | Added a closed executor-result envelope, default-empty repository approval allowlist, and fail-closed missing/unapproved executor behavior |
| A-009 | MEDIUM (resolved) | Inherited `G56R-001-ESR-003` punctuation-only effort values could be misread as authority | T001/T007 now reject malformed or undocumented effort values without rewriting G56R-001 evidence |

### Consensus Resolution Log

- Primary Analyze executor: 3 HIGH and 2 MEDIUM contract findings confirmed.
- Independent contract consensus: PASS on A-001 through A-005, with no
  G56R-003 qualification leakage after the destination-assessment boundary.
- Independent repository consensus: PASS on A-006 through A-008; the digest
  manifest adds one data file while retaining two production modules.
- Independent source-manifest audit: 22 current source records, 0 active
  historical `OSL-*` rows, and malformed effort tokens explicitly quarantined.
- Final remediation review: PASS after environment/qualification owner
  registries and executor approval-to-implementation equality were added.

📊 Confidence: 0.99

- Task understanding: 0.98
- Approach clarity: 0.98
- Requirements alignment: 0.99
- Risk assessment: 1.00
- Completeness: 0.98

G6 passes only when no `CRITICAL` or `HIGH` finding remains and every accepted
lower-severity finding has a recorded disposition.

---

## Phase 6.5: Confidence Gate

**When to run:** After Analyze and its mandatory consensus item, before any
implementation task. Resolve mode once during preflight and use the latest
workflow confidence emit.

| Field | Value |
|---|---|
| Mode | Advisory |
| Threshold | 0.90 |
| Status | Passed at 0.99; proceed |
| Bounded remediation | Not required |

---

## Phase 7: Implement

**When to run:** Only after G6 passes.

### Implement Prompt

```text
$speckit-implement

## Approach: TDD-First, Three Ordered Increments

For every task:
1. RED: add the smallest sanitized deterministic fixture or contract test that
   proves the relevant source, surface, null, mismatch, or reroute rule.
2. GREEN: implement the minimum Python 3.11 standard-library behavior needed
   to pass without adding qualification or installer behavior.
3. REFACTOR: preserve the accepted Codex-adapter versus neutral-schema boundary
   and remove only duplication introduced by this slice.
4. VERIFY: run the focused test, inspect the exact diff, and record the bound
   source/requirement evidence before continuing.

## Increment Order
1. Capability freeze and tuple-local exclusion.
2. Telemetry, route-resolution, and exact-treatment contracts.
3. Sanitized synthetic replay and full validation.

## Required Decisions
- Compare the pinned app-server, CLI, and picker surfaces; do not silently pick
  a winner when they disagree.
- Record hidden entries but exclude them absent official-ledger admission.
- Use at most one bounded non-scored canary per admitted tuple only when
  documented discovery is unavailable.
- Require profiled treatment proof plus reroute monitoring; preserve unknowns.
- Mark every rerouted run non-scorable as the requested route. Permit later
  runtime-UAT continuation only for an already prequalified destination for the
  same named agent; hard-fail every other or unidentifiable reroute.
- Keep raw live responses out of Git and commit only sanitized fixtures,
  schemas, and hashes.
- Re-read `docs/ai/specs/.process/G56R-002-design-concept.md` for the reason
  behind each rule before changing an edge-case expectation.

## Pre-Implementation Checks
- Confirm the branch and worktree root match this workflow.
- Confirm the G56R-001 evidence manifest and shared schema are current.
- Confirm the plan reviewability gate passes and the accepted slice decision is recorded.
- Confirm focused baseline tests pass before editing implementation files.
```

### Implementation Progress

| Increment | Tasks | Completed | Notes |
|---|---|---|---|
| 1 - Capability freeze | Complete | 15 | 11/11 focused tests, published validator, schema validation, deterministic replay, full suite pass, and clean independent core/process reviews |
| 2 - Treatment contracts | Complete | 10 | 51/51 focused tests, 2821/2821 full suite, Windows-safe offline replay, and exact-head independent review returned `NO FINDINGS` |
| 3 - Synthetic replay | Complete | 5 | Finding-driven remediation passes 95/95 capability tests, 39/39 validator tests, 77/77 reviewability-contract tests, and the 2864/2864 full suite; the review chain through `untitled-chat-3C1A9A` reports no P0/P1 findings |
| Polish and validation | Complete | 9 | T031-T039 remain implemented; reference and generated artifacts are current; the 124/124 manifest and live release-title gates pass |

### Capability Checkpoint Evidence

- Clean collection baseline: `ab272f05937bd08a50e40710b3f1ad3b0dc8452b`
- Candidate freeze: `sha256:403051de7d5e0a0a358cd372533ef93da2a25609e8d01ab73cb529e820aaaf03`
- Runtime snapshot: `sha256:450a655fabafb765b19bfc9ff3cbefe4b075d6c40fdbc5fd9dbc8ce8c4cfc3fe`
- Surface matrix: `sha256:99739c0895250de0eb0cf1a0215fd2e5168213081d41f6b2f828c274528c32b2`
- Included routes: 0; excluded routes: 23
- Review: PASS after route-to-claim, retention lifecycle,
  publication-transaction, permission-boundary, schema-parity, concurrency,
  destructive-clock, and hard-link durability remediation. Exact-head
  RepoPrompt reviews returned `NO FINDINGS` for the core
  (`untitled-chat-337E74`) and process state (`untitled-chat-55E370`).
- Implementation checkpoint [us1]: `5624ecd7a68aa09ee8434bca595f10fb276d3c21`

### Treatment Checkpoint Evidence

- Implementation baseline: `bbffc774c815594edc64cf412a2b5f91127ef213`
- Current published successor candidate freeze: `sha256:d4764d2e67218e21ca0920d33a90c472b26d311dd3cc25cfdd582db41ff72578`
- Superseded candidate freeze: `sha256:403051de7d5e0a0a358cd372533ef93da2a25609e8d01ab73cb529e820aaaf03`
- Telemetry profile: `sha256:acb87238dea1f7a4f56c1ab4d6ddf0f2c5407b74d1aa8f9198cafddf4da6bdb6`
- Treatment contract: `sha256:ed88fb1d5310385ba8bcaaa0badbb2bbba8819b5fb01775ebdb6f63bbeedf981`
- Treatment evidence: `sha256:2c81b6665c892b4b91ca5c2578c73c70f6fb06e74aa1ff46d6b7652248959f45`
- Superseded marker checkpoint [us2]: `8a179bdbb6aef08849bbfc4ed07c547c26f8194a`
- Reviewability: size-only `block` at 4,214 source / 3,843 nonblank,
  non-comment lines across the current two production modules
  (`codex_capabilities.py`: 2,470 / 2,243; `treatment_trace_schema.py`:
  1,744 / 1,600); typed `no_safe_boundary` exception honored for the
  checkpoint with only T026-T030 replay growth reserved.
- Review: PASS after direct canonical validation of the actual
  successor, external treatment-binding and predecessor-lineage authority,
  bounded non-extending recovery of pending retention records, crash-released
  advisory locking with unconditional failure-path release, durable post-unlink
  completion proof without contradictory byte restoration, executable
  schema/runtime parity, descriptor-relative private inputs, Windows
  handle-bound offline replay, post-unlink hard-link and digest proof, blocking
  hard-link race preservation, exact declared
  treatment-result validation, single-snapshot schema, canonical manifest authority,
  manifest-bound preferred, attempted, assigned, and supported effective routes,
  same-agent route ownership, resolver-supported effective-route semantics,
  descriptor-relative private writes and deletion recovery,
  discovery-to-treatment reconciliation, bounded private dictionary keys,
  field-specific identifier and hostname/IP privacy, parent configuration owner joins,
  sanitized CLI handling, and US2-only CLI documentation,
  single-client profile authority, content-addressed six-ID ownership,
  reciprocal acyclic trace-graph validation, externally trusted successor
  reroutes, detailed reroute reasons, and normalized malformed-predecessor
  errors. The exact-head RepoPrompt review returned `NO FINDINGS`
  (`windows-telemetry-review-D88461`).
- Implementation checkpoint [us2]: `5624ecd7a68aa09ee8434bca595f10fb276d3c21`

### Synthetic Replay Checkpoint Evidence

> The evidence below records the historical pre-restack checkpoint. The current
> US3 implementation/evidence head passed the exact live-head independent-review
> gate. Final metadata synchronization remains review-pending. The refreshed
> full-suite, manifest, and release-readiness gates pass.

- Historical reviewed remediation source head: `096605e6a4987c0f580c525bc377a68c438a9a22`
- Historical exact reviewed PR head: `3d7bd9eff79a1889830c74b6bcd22ae8945098c0`
- Prior reviewed findings head: `cbce9e631d2ae3db0c0e104cbfb356d53de1587e`
- Prior remediation source head: `688b3054d2734b4825361b3c18977ed1e3ada4da`
- Current exact-range findings head: `ff0c4d57f630dcc4058e1d4180ef24aaabae277c`
- Prior remediation source head: `3608f0dbeaca34be5585375f87e7f3ebc5feba6b`
- Current verification-authority findings head: `61014105efd7c99e04e6a40008c85e9d718a4db7`
- Initial whole-range findings head: `41643ee0b93eab88758c655bdbcb23cd05fe6473`
- Latest exact-head findings head: `a0e4e62c6a173a4d51dc6fb070d16d95aa443c9c`
- Current remediation source head [us3]: `5624ecd7a68aa09ee8434bca595f10fb276d3c21`
- Latest clean exact reviewed head: `4842c33172bef31634180c7e9585e412f0786059`
- Capability fixture: `sha256:4c4b2bc56d6ad3251beaab64126ece7012502b0230ce7c474a8cb231d7166b1a`.
- Treatment fixture: `sha256:935c2b104cb1036ef5befb8a36c2fd47c71845b4b5a7d901c26827ca9a2b3788`.
- Replay output: `sha256:c8a69de446be0ba98ec876ee37c715b008e21c97dcebc067866405a9d92d5eb4` with byte-identical two-pass verification.
- Cases: eight exact success, null, unavailable, misdelivery, approved reroute,
  unapproved reroute, discovery-loss, and surface-disagreement classes.
- Verification: 95/95 focused tests, 39/39 validator tests, 77/77 contract tests, and the 2864/2864
  full suite pass. Generated references and byte-identical replay remain current.
- Reviewability: aggregate size-only `block` at 7,052 source / 6,439 nonblank,
  non-comment lines across 29 safely subdivided modules; the largest module is
  398 lines and the two public entry points retain their APIs.
- Review: `untitled-chat-B2AE31` confirmed the first remediation but reported
  seven deeper gaps: non-monotonic partial emission, generic marker ownership
  uniqueness, mutable completed evidence, stale exact-head metadata, v1
  compatibility, unsafe path/timestamp inputs, and incomplete module
  documentation. Re-review `untitled-chat-3AC330` confirmed those seven fixes
  and reported one remaining v1 compatibility gap: top-level timestamps still
  inherited v2-only strict UTC validation. The current remediation moves that
  strictness into the v2 conditional. Exact-head re-review
  `untitled-chat-A24ABC` returned `NO FINDINGS`.
- The current restacked review `review-us3-replay-20A28F` reported four P1
  boundary gaps: private treatment API leakage, cross-checkout dependency
  reuse, an optional v2 changed-file manifest, and checkpoint commits not
  bound to immutable evidence. All four are remediated at
  `688b3054d2734b4825361b3c18977ed1e3ada4da`; exact-head re-review is pending.
- Re-review `exact-range-review-905F43` reported four further P1 boundaries:
  same-path stale or shadowed capability imports, unsupported marker-plan
  versions, an unbound manifest base, and folded tasks omitted from checkpoint
  freshness. All four are remediated at
  `3608f0dbeaca34be5585375f87e7f3ebc5feba6b`; exact-head re-review is pending.
- The next review turn in `exact-range-review-905F43` confirmed those four fixes
  and reported three lifecycle gaps: incomplete v2 marker shapes, complete plans
  accepting pending checkpoint evidence, and unverified evidence-commit history.
  All three are remediated at `1430eb0f6414064900044cd153b8adfb7ba5917c`.
  The next exact live-range review through `61014105efd7c99e04e6a40008c85e9d718a4db7`
  reported four remaining gaps: incomplete nested v2 schema enforcement, mutable
  verification reports, failed verification values qualifying as complete, and
  transient canonical module exposure during private capability loading. All four
  are remediated in source.
- Focused follow-up reviews for the schema (`untitled-chat-A46475`), authority
  and model binding (`untitled-chat-B6D973`), bundle and successor validation
  (`untitled-chat-1632BA`), and replay/I/O boundaries
  (`untitled-chat-73BE33`) each returned `NO FINDINGS` through
  `bb665837ba72851402ed10f2af21808554585983`. Those focused reviews remain
  clean; whole-range review continued below.
- The first exact live-range review `live-range-review-9FBA02` at
  `41643ee0b93eab88758c655bdbcb23cd05fe6473` reported three P1 gaps: duplicate
  JSON keys could downgrade strict marker-plan authority, capability file-to-FIFO
  swaps could block before descriptor validation, and nested Phase 7 evidence
  retained stale replay provenance. All three are remediated at
  `4c938205ccf396e0a6c99c9dc830f64e2764fd50`. The next exact-head turn at
  `3e4b13b7437d6774deeb3ef180b5196eae523b01` confirmed those fixes and reported
  three further P1 boundaries: package-mode imports could reuse same-path stale
  dependencies, deletion or completion-record FIFO swaps could block cleanup,
  and a private retention-record directory could be swapped to an external
  symlink. All three are remediated at
  `fb038346894260d1b3ceeaa6cd1966e4435bdb5a`. The next exact-head review at
  `91a66e043ddc1d21d9d2ffbb1b77bbf223e677c1` reported two P1 gaps and one P2:
  pending checkpoint evidence still trusted mutable worktree bytes, folded
  integration and polish claims escaped marker checkpoint cross-validation,
  and non-finite JSON constants could crash the validator. All three are
  remediated at `043f2d2e2dae5612ba162dffa6876c7b35a95888`; exact live-head
  re-review at `c28b2c69a30c1bdc14cfdf36bfd46a504f98b5b5` found one further P1:
  the phase-facing `independent_review` claim did not bind to checkpoint gate
  `independent_critical_high_review`. The explicit compatibility alias and a
  completed-phase fabricated-pass regression are remediated at
  `ed31f222ed47650075732b81c7d6075a59351bba`; exact live-head re-review is
  pending. The next exact-head review at
  `ab879cd4658a4aebc09fd55428da1b94b2e97180` reported one further P1: raw
  captures created before publication were not registered for cleanup and
  could be rematerialized after unlink. Shared-lock pending registration,
  descriptor-bound orphan inventory, deletion-state rejection, and abandoned
  and post-unlink race regressions are remediated at
  `0810750235ffc934dde411ee2a7a5470943e2461`. Exact live-head re-review at
  `60054601dc7364aae5dfb29299b5c4f15e45653a` found one further P1: the legacy
  private materializer aliases remained reachable and bypassed retention
  enforcement. Both aliases now delegate to the retention authority, with
  post-deletion source and unknown-capture regressions, at
  `06c94413387849b9373cb0223889f698ca6c7f65`. Exact live-head re-review at
  `4a5491cf64ea7e77cc39ea5a3b6c1b29a3e11597` found one further P1: the
  workflow claimed a superseded US2 checkpoint and the validator did not
  compare workflow checkpoint claims with authoritative marker state. The
  workflow is synchronized to `42cdf743346c880c1b7e8cb172e842a82ab6f343`,
  and semantic claim/table validation with a drift regression is implemented at
  `cd4b8d48bf4494d5906c5c9dc7796ee2c19516f6`. Exact live-head re-review at
  `a7cbcb6081b12129c617995b8fe585550de547ec` found two further P1 boundaries:
  the workflow retained a conflicting US2 superseded checkpoint, and same-user
  lock-file replacement could create two retention critical sections. The
  superseded claim now binds `8a179bdbb6aef08849bbfc4ed07c547c26f8194a`,
  the validator cross-checks superseded claims, and retention uses a directory
  descriptor lock plus lock-path identity checks with a concurrent cleanup and
  materialization regression at
  `7f846a02254c6337eb207fee7dba6a06cd485a00`. Exact live-head re-review at
  `9ddc51c820d8f1e4763f3c6adad1751ca9f500dc` found two further P1 boundaries:
  workflow checkpoint claims were only globally, not marker-specifically,
  matched, and replacing the raw-root pathname could let a replacement root
  acquire a different directory lock. Claims now name and bind their exact
  marker, unscoped claims fail, and a focused retention-lock module serializes
  on the stable parent inode before the raw root with a concurrent raw-root
  replacement regression at
  `a324f4e95bfddb7b37e4612879d5b57c9d2af412`; exact live-head re-review is
  pending.
- Exact live-head re-review at
  `8c84eb4222863b0d399cdf4ea0cadcf865e1076e` found three further P1 boundaries:
  exact-head validation trusted mutable workflow bytes, pending phase evidence
  failed open when direct or verification authority keys were absent, and public
  capability outputs followed symlinks. Workflow and checkpoint schemas now load
  from the authorized head and require byte-equal worktree copies, every projected
  phase claim requires a matching checkpoint evidence owner, and public outputs use
  descriptor-relative no-follow temporary creation with parent identity checks and
  atomic replacement. Dirty-workflow, missing-authority, pre-existing-symlink,
  file-to-symlink, and parent-replacement regressions pass at
  `19b748ae3f108d68a05ceb282968c76b4debe340`; exact live-head re-review is pending.
- Exact live-head re-review at
  `eeebd7380b798bb8b6ea1dd4ba20ce284155a9d7` found two further P1 boundaries:
  the supplied workflow was not bound to `state.workflow_file`, and v2 workflows
  could omit the marker-evidence section and current checkpoint claims. Exact-head
  validation now requires the normalized state path to equal the supplied
  repository-relative workflow, and v2 projection requires one marker-evidence
  section, one current checkpoint claim, and one row per marker. Alternate-workflow,
  missing-section, and missing-claim regressions pass at
  `6d546a5013cee11cca936c491e82de85e4eb8ead`; exact live-head re-review is pending.
- Exact live-head re-review at
  `2b4063417808b2b98ef94309d1ab41629d71bfaf` found three further P1 boundaries:
  pending markers could omit evidence and commit authority, exact-head validation
  trusted mutable copies of three canonical schemas, and workflow claims inside
  comments or fenced code could satisfy mandatory projection. Pending checkpoint
  authority is now required, all canonical schemas load from and byte-match the
  authorized head, and only visible Markdown supplies workflow evidence. Missing-
  authority, dirty-schema, fenced-section, and commented-claim regressions pass at
  `17fe36df500b31552a7dcfe62da6285684839886`; exact live-head re-review is pending.
- Exact live-head re-review at
  `2496446d8ba53f7edd9399db2c221acb84fa0768` found two further P1 boundaries:
  general workflow requirements still trusted raw Markdown, including unclosed
  comments, and the shared checkpoint definition made v2 pending authority fields
  mandatory for v1 schema consumers. Every workflow requirement now uses one
  visible-Markdown projection that treats unclosed comments as hidden through EOF,
  while pending evidence and commit fields live only in the v2 conditional. Full-
  workflow fence/comment and every-mirror legacy-v1 regressions pass at
  `22507c2667d7698fd65e1ce74dff8e97317a42eb`; exact live-head re-review is pending.
- Exact live-head re-review at
  `a0e4e62c6a173a4d51dc6fb070d16d95aa443c9c` found three further P1 boundaries:
  indented code could satisfy workflow requirements, pending checkpoint commits
  were not bound to evidence and authorized-head ancestry, and evidence owners
  could shadow one another across top-level and verification containers. The
  visible projection now excludes four-space and tab-indented code, every v2
  checkpoint commit must match its evidence and exist in the authorized history,
  and phase claims require one unique owner across all permitted locations.
  Indented-workflow, mismatched/nonexistent/unrelated-commit, top-level-shadow,
  and cross-container duplicate-owner regressions pass at
  `a048c80875465eafd9187b848f4b3b3139cf326b`; exact live-head re-review is pending.
- Exact live-head re-review at
  `723e488225453937b8a8d72185af9f53c9774ba8` found four further evidence
  boundaries: pending evidence commits and digests were unauthenticated,
  completed evidence could be rewritten and rebound, raw HTML blocks could hide
  workflow authority, and Python primitive equality accepted booleans as
  integers. Pending authority now binds both evidence files to an existing
  authorized commit and exact digests; completed US1/US2 records are restored to
  their `a6284ae644634fde09a5109827068cf8de2d8b15` bytes and use discoverable,
  append-only correction records; all CommonMark raw-HTML block forms are hidden
  from workflow checks; and phase projection uses JSON-type-preserving equality.
  Authority, correction-chain, raw-HTML, and boolean-versus-integer regressions
  pass at `b43333f0268c442696f8bd48ce4f8f225da56a6a`; exact live-head re-review is
  pending.
- Exact live-head re-review `untitled-chat-9B00BE` at
  `cf962cc5480c6e84a10c1889bc34cfc475dc1128` found one further P1 boundary:
  the visible workflow claimed Current fingerprints while retaining stale
  reviewability-evidence and changed-file-manifest digests. The workflow now
  mirrors all six authoritative marker-plan fingerprints, and the strict
  validator rejects any Current claim whose visible rows do not exactly match
  `pr_marker_plan.source_fingerprint`. The digest-drift regression and the full
  2857/2857 suite pass at
  `aea7282a9b3c64c2d04928104e13b35defeaa0f3`. Exact live-head re-review at
  `4842c33172bef31634180c7e9585e412f0786059` returned `NO FINDINGS`; the final
  metadata-only binding head remains to be reviewed.
- Evidence finalization after the source head is metadata-only; it does not
  change implementation or verification inputs.
- Folded polish: T031-T039 are complete. The current reviewability and title
  gates pass. Historical 78-file base-to-head manifest gates passed before
  restack; the current 107/107 manifest passes exact current-head validation.

## PR Marker Plan Evidence

- Schema version: `pr-marker-plan.v2` for strict evidence; legacy
  `pr-marker-plan.v1` remains readable without the new v2-only fields.
- Authoritative state: top-level `pr_marker_plan` in
  `docs/ai/specs/.process/autopilot-state.json`
- Fingerprint status: Current
- Plan status: `emission_ready`

| Fingerprint input | SHA-256 |
|---|---|
| Feature spec | `sha256:ee5e6e7efafecd1064407398806558991c09f5e9bea58a1ac6ab60342bd82046` |
| Plan-declared scope | `sha256:892c9c8c87f21233cd06323a2303913e698aad9ac8546014a11462fa8e34756f` |
| Tasks | `sha256:7bd80934ed9521709209774e0233bdf492b9a233fb6bd19d890511c9155245d8` |
| Reviewability evidence | `sha256:743d43d98417239daabfed3048d6c978600833e4b03ca2639d6826a44dbc9ee4` |
| Hazard route | `sha256:ed87694636ff706326d71ee50c6f3635045445b70129bf4e1120e54dc42a42c2` |
| Changed-file manifest | `sha256:9e4c7ce14d10e05acca4a40460cd5724d60e5bd7e53f5f4ea37e94c8775e2eed` |

| Review order | Marker | Tasks | Reviewability | Checkpoint | Warning |
|---|---|---|---|---|---|
| 1 | `us1` | T001-T015 | Size-only `block`; honored typed `no_safe_boundary` exception | Complete at `5624ecd7a68aa09ee8434bca595f10fb276d3c21` | Historical checkpoint evidence remains append-only |
| 2 | `us2` | T016-T025 | Size-only `block`; honored typed `no_safe_boundary` exception | Complete at `5624ecd7a68aa09ee8434bca595f10fb276d3c21` | Historical checkpoint evidence remains append-only |
| 3 | `us3` | T026-T030; T031-T039 folded | Aggregate size-only `block`; current safe subdivision keeps every module below 400 lines | Complete at `5624ecd7a68aa09ee8434bca595f10fb276d3c21`; source review chain through `untitled-chat-3C1A9A` reports no P0/P1 findings; final metadata-head review pending | No correctness or safety exception remains |

- Warnings: `CAPABILITY_SIZE_BLOCK`, `TREATMENT_SIZE_BLOCK`, and marker-level
  size warnings. The historical US1 checkpoint is 1,844 / 1,645 source/nonblank
  lines; the current US2 marker is 4,214 / 3,843 across its two modules against
  the 400-LOC boundary at its immutable checkpoint. The current US3 remediation
  is 7,052 / 6,439 across 29 focused modules with a 398-line maximum.
- Final `marker_split`: Pending.
- Packet validation: Pending.
- PR mappings: Pending.

---

## Post-Implementation Checklist

| Post Item | Status |
|---|---|
| Post: Doctor Extension Check | Pending |
| Post: Verify Implementation | Pending |
| Post: Verify Tasks Phantom Check | Pending |
| Post: Code Review | Pending |
| Post: Integration Suite | Pending |
| Post: Reviewability Diff Gate | Pending |
| Post: Self-Review | Pending |
| Post: UAT Runbook Generation | Pending |
| Post: Final Reviewability Backstop | Pending |
| Post: PR Packet/Body Generation | Pending |
| Post: PR Body Generation | Pending |
| Post: PR Creation | Pending |
| Post: Review Remediation | Pending |
| Post: Retrospective | Pending |

- [ ] All tasks and user-story acceptance checks are complete.
- [ ] Focused capability, telemetry, treatment, and replay tests pass.
- [ ] Sanitized fixture hashes are deterministic and no raw live response is tracked.
- [ ] `git diff --check` passes.
- [ ] Spec MOC and generated-index contracts pass.
- [ ] `python3 -u tests/speckit-pro/run-all.py --layer 1` passes.
- [ ] `python3 -u tests/speckit-pro/run-all.py` passes.
- [ ] Changed-file review proves no corpus, scorer, qualification, installer,
      agent, payload, default, version, or cross-vendor framework change leaked in.
- [ ] The final PR title passes the live release-readiness gate and follows
      `<type>(<lowercase-scope>): <plain English description>`.
- [ ] Manual review confirms tuple-local exclusions, source authority, treatment
      proof, reroute semantics, and null behavior match the Design Concept.

---

## Lessons Learned

### What Worked Well

- Pending implementation retrospective.

### Challenges Encountered

- Pending implementation retrospective.

### Patterns to Reuse

- Pending implementation retrospective.

---

## Project Structure Reference

```text
docs/ai/research/                                 # G56R-001 evidence baseline
docs/ai/specs/.process/                           # Design Concept and workflow exhaust
specs/g56r-002-capability-discovery-telemetry/   # G56R-002 contract artifacts
tests/speckit-pro/layer6-efficiency/lib/          # Capability and treatment contract code
tests/speckit-pro/layer6-efficiency/              # Synthetic fixtures and integration tests
tests/speckit-pro/unit/                           # Focused deterministic unit coverage
```

---

Instantiated from the shared SpecKit workflow template and populated from the
G56R-002 roadmap entry, project constitution, current official documentation,
and the 2026-07-16 Grill Me Design Concept.
