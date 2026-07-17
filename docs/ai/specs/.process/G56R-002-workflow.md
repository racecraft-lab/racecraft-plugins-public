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
| Plan | `$speckit-plan` | In Progress | Design one guarded three-increment slice |
| Checklist | `$speckit-checklist` | Pending | Run four risk-focused domains |
| Tasks | `$speckit-tasks` | Pending | Generate TDD-first, vertically ordered tasks |
| Analyze | `$speckit-analyze` | Pending | Prove cross-artifact consistency and scope containment |
| Confidence Gate | G6.5 | Pending | Evaluate the Analyze confidence emit in advisory mode |
| Implement | `$speckit-implement` | Pending | Implement only after G6 passes |
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

**Constitution Check:** Verified at G1; the plan must record a pass before G3.

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
| `plan.md` | Pending | Must include re-estimation and one-slice decision |
| `research.md` | Pending | Must bind every native field to current official evidence |
| `data-model.md` | Pending | Must preserve null, unknown, mismatch, and exclusion states |
| `contracts/` | Pending | No runtime qualification or installer schema |
| `quickstart.md` | Pending | Must avoid raw live evidence in Git |

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
| LLM integration | Pending | Pending | Pending autopilot |
| Data integrity | Pending | Pending | Pending autopilot |
| Error handling | Pending | Pending | Pending autopilot |
| Observability | Pending | Pending | Pending autopilot |

Every accepted gap must update `spec.md` or `plan.md`, then the affected
checklist must be rerun before G4 passes.

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
| Total Tasks | Pending autopilot |
| Phases | Three implementation increments plus setup and polish |
| Parallel Opportunities | Pending dependency analysis |
| User Stories Covered | US1, US2, and US3 required |

---

## Atomicity Route

After G5, autopilot must run the read-only atomicity classifier against
`specs/g56r-002-capability-discovery-telemetry` and record its decision here.
The classifier records structure only; it does not create PRs or split branches.

| Field | Value | Meaning |
|---|---|---|
| Route | Pending G5 classifier | Expected to remain one navigable or atomic PR unless planned seams prove otherwise |
| Releasable | Pending G5 classifier | No assumption before classifier output |
| Signals | Pending G5 classifier | Record decisive structural findings |
| Warnings | Pending G5 classifier | Record every release-safety warning |

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
   approximately three production files, ten total files, and one guarded slice.
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
| Pending | Pending | Autopilot has not run analysis | Resolve before G6 |

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
| Status | Pending Analyze confidence emit |
| Bounded remediation | Up to three focused iterations on the lowest-scoring criterion |

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
| 1 - Capability freeze | Pending | 0 | Not started |
| 2 - Treatment contracts | Pending | 0 | Not started |
| 3 - Synthetic replay | Pending | 0 | Not started |
| Polish and validation | Pending | 0 | Not started |

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
