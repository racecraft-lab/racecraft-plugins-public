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
| Implement | `$speckit-implement` | In Progress | T016-T025 completed at the clean US2 checkpoint; T026-T030 synthetic replay is in progress |
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
  manifest adds one data file while the current implementation uses 13
  production modules.
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
| 2 - Treatment contracts | Review pending | 10 | 57/57 focused tests, standalone validation, privacy, docs-reference, and 2821/2821 full-suite checks pass after the latest two exact-head findings were remediated; exact-head re-audit pending |
| 3 - Synthetic replay | In Progress | 0 | T026-T030 exist on the next marker branch; restack and exact-head review follow US2 approval |
| Polish and validation | Pending | 0 | Not started |

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
- Implementation checkpoint: `2b7096dacdaa7a6af62b3c12b36e83cf4515213e`

### Treatment Checkpoint Evidence

- Implementation baseline: `bbffc774c815594edc64cf412a2b5f91127ef213`
- Successor candidate freeze: `sha256:087cd717bd4daf9e41f064b86e70335e011c2ba33c5a7b4d3d95a2962f22629c`
- Superseded candidate freeze: `sha256:403051de7d5e0a0a358cd372533ef93da2a25609e8d01ab73cb529e820aaaf03`
- Telemetry profile: `sha256:9be2156764d858a2358a778414e4f978325e69686f11359ad1a7b168463a8979`
- Treatment contract: `sha256:8c2f9e182d4a97f0934f7f79ab260a09777cfde362f7e8d3bf9a7884101a5199`
- Treatment evidence set: `sha256:e9c1b23f4b09b594f17d23f7632cab25eb1f73f8b63c1e91da0544507c73ce1f`
- Superseded marker checkpoint: `ce64616342ab977fc5bbaa675b8b9ca7ed192108`
- Reviewability: aggregate size-only `block` at 4,809 source / 4,386
  nonblank, non-comment lines across 13 production modules. The stable
  capability facade and 11 focused internal modules total 2,901 / 2,628 with
  a 395-line maximum; capability code no longer uses a `no_safe_boundary`
  exception. `treatment_trace_schema.py` remains 1,885 / 1,737 under its
  treatment-only typed exception, with only T026-T030 replay growth reserved.
- Review: PENDING after direct canonical validation of the actual
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
  errors. The prior exact-head RepoPrompt review returned `NO FINDINGS`
  (`windows-telemetry-review-D88461`). A later current-head re-audit
  (`untitled-chat-869257`) reported two P1 findings: stale retention-order prose
  and an unjustified capability `no_safe_boundary` claim. This remediation
  corrects the deletion-intent/completion sequence and safely splits capability
  trust and failure responsibilities behind the stable facade. A follow-up
  exact-head audit
  (`review-us2-remediation-1AE3C9`) reported three further findings: a durability
  probe could bypass restoration, wildcard exports leaked internal trust
  primitives, and the checkpoint was labeled complete while review remained
  open. The remediation restored raw bytes when the completion probe was
  untrusted, constrained the facade to its exact supported API, and marked US2
  review-pending for the
  next audit.
  The exact-head re-audit returned `NO FINDINGS`
  (`audit-us2-remediation-F4E33F`).
  A later exact-range re-audit (`review-exact-treatments-9ED44E`) found three
  remaining boundaries: a post-unlink hard-link race could remove the canonical
  raw-evidence path, treatment publication did not cryptographically bind its
  retained observation, route-proof, and source evidence, and a non-initial
  treatment freeze could not provide predecessor lineage authority. Remediation
  at `cc04e5460bbc2050c803875a5193f525a47f381c` restores verified canonical
  bytes while preserving a fail-closed deletion intent, validates exact trusted
  evidence bytes for every treatment owner, and accepts explicitly bound
  predecessor authority. Focused 53/53, docs-reference, standalone treatment,
  privacy 10/10, and full 2821/2821 gates pass; exact-head re-audit is pending.
  The next exact-head re-audit (`review-us2-remediation-5AD0BD`) found two P1
  gaps and one stale P2 claim: the successor identity did not retain the exact
  treatment evidence-set digest, the public freeze validator exposed a lineage
  bypass, and checkpoint evidence still named a 363-line capability maximum.
  Remediation at `6afcf8c9e4a5a482be03bb300d4d39e2f5d499f8` binds the exact owner-to-content
  digest set into every treatment-aware freeze and candidate ID, moves
  payload-only recursive validation behind a private helper, and synchronizes
  the measured 373-line maximum. Exact-head re-audit remains pending.
  The next exact-head review (`re-review-pr-367-747B1B`) found two P1 gaps and
  one stale P2 claim: a durable deletion intent could not resume a provably
  pre-unlink cleanup, arbitrary treatment evidence mappings were read more than
  once, and `plan.md` retained old implementation measurements. Remediation at
  `ed1e442cc2507c72ef46702a36dee79bdee08135` binds the intent to the private
  target identity and safely resumes only that exact file, snapshots treatment
  evidence once before validation and hashing, and synchronizes plan, tasks,
  checkpoint, and reviewability measurements. Focused 53/53, standalone
  treatment, docs-reference, and full 2821/2821 gates pass; exact-head re-audit
  remains pending.
  The next exact-head review (`pr-367-rereview-B3E562`) found one P1 and one P2:
  an unlink error before removal rewrote the intent-bound inode and blocked a
  later retry, while public append-only publication did not directory-fsync
  temporary-name removal. Remediation at
  `92ccbbaefd290a64fd70f2a28487b67cd5ff9d29` preserves and validates the
  existing inode when unlink has not occurred, restores bytes only after the
  entry is absent, and synchronizes the public temporary-link removal. Focused
  53/53, standalone treatment, docs-reference, and full 2821/2821 gates pass;
  exact-head re-audit remains pending.
  The next exact-head review (`pr-367-rereview-5B3AA1`) found one remaining P1:
  verified bytes restored after completion-record persistence failed received a
  new inode that no durable intent authorized, permanently blocking supported
  cleanup. Remediation at `c76e3fd6654e9a57a417a35aed829437954e53b4`
  appends an immutable recovery-intent successor only after post-unlink proof,
  binds the predecessor, exact replacement identity, and restoration proof,
  rejects missing, forked, disconnected, or cyclic chains, and resumes from the
  unique terminal intent. Hard-link races and unverified mutations remain
  fail-closed. Focused 53/53, standalone treatment, docs-reference, and full
  2821/2821 gates pass; exact-head re-audit remains pending.
  The next exact-head review (`pr-367-rereview-6DC2A3`) found one P1 crash
  window and one stale P2 narrative: restored bytes became durable before their
  recovery successor, and capability evidence still called treatment pending.
  Remediation at `a47b00e2257c165236a9f8796d93ca32c0362bf0` journals a
  post-unlink v3 stage before any replacement, binds restored bytes in v4, and
  lets cleanup finalize both missing-stage and restored-stage interruptions.
  The research evidence now names the current treatment-bound successor and
  v2/v3/v4 deletion-recovery behavior. Focused 53/53, standalone treatment, and
  docs-reference and full 2821/2821 gates pass; exact-head re-audit remains
  pending.
  The exact-head review (`pr-367-rereview-A6C704`) then found one P0 and one P1:
  terminal v3 could record deletion while a restoration temporary or external
  hard link still retained governed bytes, and the US2 checkpoint contradicted
  its pending independent review. Remediation at
  `c3052ff151563d9b146de347b392e79f688cd3eb` removes post-proof restoration,
  journals v3 immediately after the durable unlink, retries only completion
  publication while the canonical target remains absent, and keeps US2
  review-pending. Focused 53/53, standalone treatment, docs-reference, and full
  2821/2821 gates pass; exact-head re-audit remains pending.
  The exact-head review (`pr-367-re-review-40F2F7`) then found one P1 and one P2:
  failure before v3 publication left v2 with a missing canonical target and no
  supported retry, while `tasks.md` retained stale reviewability measurements.
  Remediation at `ce64616342ab977fc5bbaa675b8b9ca7ed192108` durably renames
  the v2-bound inode into deterministic quarantine, binds that name and identity
  in v3 before unlink, resumes from either pre- or post-persistence v3 failure,
  and synchronizes the task measurements. Focused 53/53, standalone treatment,
  docs-reference, and full 2821/2821 gates pass; exact-head re-audit remains
  pending.
  The next exact-head review (`pr-367-rereview-112186`) found two P1 gaps: a
  resumed quarantine could publish v3 without first directory-syncing and
  revalidating the rename, and both authorized `proven` disposition paths were
  unreachable. Remediation at `e041319053e1a650d92953869a9ecec5c15f8879`
  synchronizes and revalidates every quarantine retry before v3, makes complete
  observed reroute capture authoritative for configured proof, and accepts an
  observed supported route bound to canonical non-null model/effort as effective
  evidence without claiming undocumented effort telemetry. Focused 54/54,
  standalone treatment, docs-reference, and full 2821/2821 gates pass;
  exact-head re-audit remains pending.
  The next exact-head review (`review-treatment-contrac-F02243`) found one P0
  and one P1: a v3 retry could falsely certify deletion after an interrupted
  unlink while an external hard link retained the evidence, and the resulting
  completion record backdated `deleted_at` to the original attempt. Remediation
  at `aef759559688ecf53ef74de0fbbfd000b1de6871` now resumes v3 only while the
  exact bound quarantine exists, treats a missing quarantine without durable
  completion proof as indeterminate, and records the actual successful retry
  time. Focused 54/54, standalone treatment, docs-reference, and full 2821/2821
  gates pass; exact-head re-audit remains pending.
  The next exact-head review (`review-retention-remedia-D1A187`) found one P0
  and one P1: a `proven` trace could target a tuple the authoritative prior
  freeze marked excluded, and successor publication could predate its route or
  observation evidence. Remediation at
  `7ddf5763681f9862c642664dcac8146cab51e4d9` now requires every published
  `proven` trace to map to an included, source-admitted,
  availability-supported, surface-agreed prior tuple and orders publication at
  or after every bound route resolution and non-null observation capture.
  Focused 54/54, standalone treatment, docs-reference, and full 2821/2821 gates
  pass; exact-head re-audit remains pending.
  The next exact-head review (`capability-remediation-r-9F1346`) found one P0
  and two P1 gaps: retained unknown-observation and canary bytes were not
  semantically revalidated before receipt, public append-only publication was
  pathname-based, and private record loads could mix directory snapshots.
  Remediation at `9d9ceea3b7aa1abd641afb46660d1deb838fa25c`
  now semantically validates all retained evidence before registration,
  descriptor-binds and re-reads exact public output bytes before receipt, and
  loads every private record set through one unchanged identity-bound directory
  snapshot. Focused 55/55, standalone treatment, docs-reference, and full
  2821/2821 gates pass; exact-head re-audit remains pending.
  The next exact-head review (`pr-367-review-6D565E`) found two P1 gaps: an
  existing matching hard-linked publication output could bypass the single-link
  receipt invariant, and deeply nested capability JSON could escape the
  fail-closed validation contract without explicit depth and node limits.
  Remediation at `2d1ea3ec1932421740c655d92239a45e81f0a2e7`
  requires every recovered publication output to be single-link before receipt
  and bounds all capability JSON to 64 nesting levels and 100,000 total nodes
  while normalizing parser recursion to `ValueError`. Focused 55/55, standalone
  treatment, docs-reference, and full 2821/2821 gates pass; exact-head re-audit
  remains pending.
  The next exact-head review (`pr-367-review-D20B53`) found one P0 and two P1
  gaps: an older governing receipt could hide a newer bounded pending claim,
  durable append-only linking could strand an unrecoverable temporary after a
  crash, and exported source-capture materialization parsed before checking its
  byte bound. Remediation at
  `22aad882c836cf9d2d8a86bde34df154d5caede2` computes the latest deadline
  across governing and individually capped pending claims, descriptor-recovers
  only the exact single temporary/target inode pair, and enforces bytes-like
  32-MiB source-capture input before parsing or hashing. Focused 56/56,
  standalone treatment, docs-reference, and full 2821/2821 gates pass;
  exact-head re-audit remains pending.
  The exact-head review (`review-pr-367-C52F62`) then found one P1 and one P2:
  a crash before final-name linking could strand a single-link temporary and
  wedge the evidence root, while concurrent identical source-capture writers
  could propagate `FileExistsError`. Remediation at
  `3c439b154669175226ec2ffed3f26731dcae373f` gives every reserved temporary an
  advisory lock, removes abandoned pre-link files only after lock and
  descriptor-relative identity proof, applies the same protocol to public
  append-only directories, and accepts only a verified content-addressed winner.
  Focused 57/57, standalone treatment, privacy 10/10, docs-reference, and full
  2821/2821 checks pass; the exact-head re-audit remains pending.
- Implementation checkpoint: `3c439b154669175226ec2ffed3f26731dcae373f`

## PR Marker Plan Evidence

- Schema version: `pr-marker-plan.v1`
- Authoritative state: top-level `pr_marker_plan` in
  `docs/ai/specs/.process/autopilot-state.json`
- Fingerprint status: Current
- Plan status: `checkpointing`

| Fingerprint input | SHA-256 |
|---|---|
| Feature spec | `sha256:0bbd979954897e669c6579d31cfc80995100e7b037c58f8f9f844a84e381892c` |
| Plan-declared scope | `sha256:60a1b0f2cea34de0fbb176ca5d3e775730839082967a7b4f1d0fa5d03c37623f` |
| Tasks | `sha256:d2d55fc31f3a8b560cd51c54d4e4cbd59d2984afc47b71e3b1fc21686ac2b4ac` |
| Reviewability evidence | `sha256:082e1f4ec9aad898ccafeb68ce86b40eaf3549c72cf4d1c45fa17123f91dc534` |
| Hazard route | `sha256:ed87694636ff706326d71ee50c6f3635045445b70129bf4e1120e54dc42a42c2` |

| Review order | Marker | Tasks | Reviewability | Checkpoint | Warning |
|---|---|---|---|---|---|
| 1 | `us1` | T001-T015 | Size-only `block`; honored typed `no_safe_boundary` exception | Complete at `2b7096dacdaa7a6af62b3c12b36e83cf4515213e` | No feature growth after checkpoint |
| 2 | `us2` | T016-T025 | Aggregate size-only `block`; capability safely subdivided, treatment-only typed exception retained | Review pending at `3c439b154669175226ec2ffed3f26731dcae373f` | Exact-head re-audit required before restack |
| 3 | `us3` | T026-T030; T031-T039 folded | Not estimated | Pending | Replay and polish remain ordered after treatment |

- Warnings: `CAPABILITY_SIZE_BLOCK`, `TREATMENT_SIZE_BLOCK`, and marker-level
  size warnings. The historical US1 checkpoint is 1,844 / 1,645 source/nonblank
  lines under its historical typed exception; the current US2 marker is 5,224 /
  4,772 across 14 modules against the aggregate 400-LOC boundary. Capability
  modules are safely split with a 388-line maximum; only the treatment module
  retains a typed size-only exception.
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
