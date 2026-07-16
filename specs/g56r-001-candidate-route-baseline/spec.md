# Feature Specification: G56R-001 Candidate Route Baseline

**Feature Branch**: `g56r-001-candidate-route-baseline`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "Create the G56R-001 specification for a documentation-only research spike that prepares the candidate model/effort route baseline and role-contract matrix for G56R-002."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Freeze Official Evidence (Priority: P1)

As the G56R program owner, I need a dated official-source ledger so every platform, model, effort, subagent, MCP, app, configuration, non-interactive, and prompting claim is traceable to current OpenAI documentation before G56R-002 uses it.

**Why this priority**: Candidate admission is unsafe unless platform claims fail closed when current official documentation does not support them.

**Independent Test**: Review `docs/ai/research/codex-agent-route-candidates.md` and confirm every platform claim has an `official_source_ledger_id`, source family, retrieval method, requested URL, canonical URL, retrieval date, durable retrieval evidence, page or section locator, short excerpt anchor, bounded source-fact extract, extract hash, invalidation trigger, and claim binding.

**Acceptance Scenarios**:

1. **Given** a model, effort, custom-agent, MCP, app, telemetry, non-interactive, or prompting claim, **When** the report presents it as a platform fact, **Then** it cites an official OpenAI source record retrieved on 2026-07-16 with durable retrieval evidence, source locator, bounded source-fact extract, and extract hash.
2. **Given** a roadmap seed model lacks current official Codex route support, **When** the report evaluates it, **Then** the model is marked `undocumented`, rejected, or blocked and cannot appear as an executable route.

---

### User Story 2 - Define Twelve Role Contracts (Priority: P1)

As the G56R-002 implementer, I need one role contract record for each target role so later capability discovery and fixture work preserve role intent, mutation boundaries, grounding, tool needs, output shape, client surface, and representative tasks.

**Why this priority**: Route fallback can only change model and effort; the role contract is the invariant that prevents silent substitution.

**Independent Test**: Count exactly twelve `agent_contract_id` records: ten active Codex TOML source records and two Claude parity-only comparison records.

**Acceptance Scenarios**:

1. **Given** the current `speckit-pro/codex-agents/*.toml` inventory contains ten files, **When** the report records the active Codex catalog, **Then** all ten appear with source file, current route input, mutation expectation, grounding requirement, tool/skill/MCP need, output contract, client surface, and future task.
2. **Given** `consensus-synthesizer` and `gate-validator` currently exist only in Claude definitions, **When** the report includes them, **Then** they are labeled `project_input` comparison records and not active Codex agents.

---

### User Story 3 - Publish Provisional Candidate Routes (Priority: P2)

As a route evaluator, I need provisional candidate records that bind documented model options, effort-surface evidence, and role requirements without claiming availability, executability, preference, efficiency, qualification, or fallback behavior.

**Why this priority**: G56R-002 needs a bounded model-candidate set and exact effort questions, but executable model/effort tuples, qualification, and availability belong to later phases.

**Independent Test**: For each role contract, inspect its candidate records and verify every source-bound model record cites an official source, blocks executable model/effort tuples until capability discovery, marks unsupported facts explicitly, and selects no preferred or fallback order.

**Acceptance Scenarios**:

1. **Given** a candidate route record, **When** it names a model or effort, **Then** it binds to the official-source ledger and states required runtime capability checks before use.
2. **Given** a route depends on current availability or exact treatment, **When** the report describes it, **Then** that dependency is listed as a G56R-002 capability question rather than a completed fact.

---

### User Story 4 - Hand Off Fixture and Telemetry Gaps (Priority: P2)

As the G56R-002/G56R-003 owner, I need an exact fixture and telemetry backlog so executable automation can replace prompt-emulation evidence without creating or running fixture payloads in G56R-001.

**Why this priority**: Historical prompt-emulation results are non-release evidence and cannot qualify candidates.

**Independent Test**: Confirm the backlog contains exactly three current prompt-emulation fixtures and nine missing executable role fixtures, each with executable specification, telemetry need, success oracle, blocking dependency, and priority.

**Acceptance Scenarios**:

1. **Given** the current `tests/speckit-pro/layer6-efficiency/fixtures-codex/` tree, **When** the report inventories fixture status, **Then** only `codebase-analyst`, `domain-researcher`, and `spec-context-analyst` are marked current prompt-emulation fixtures.
2. **Given** any other target role, **When** the report records fixture status, **Then** it is marked missing executable fixture with the exact automation specification needed for future G56R work.

### Edge Cases

- Official OpenAI documentation changes, redirects, withdraws a model, changes source wording, or changes a supported effort after this snapshot.
- Official API docs mention a model that Codex model guidance deprecates or does not position for current Codex routes.
- Repository files mention a model, effort, fallback, MCP, app, telemetry, or route field that official documentation does not establish.
- A Claude parity role has no active Codex TOML source file.
- A current prompt-emulation fixture exists but lacks exact-treatment, MCP/tool, sandbox, parent configuration, or effective-route proof.
- Service reroute or token telemetry fields are absent from the pinned G56R-002 client or absent from current official app-server documentation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The implementation artifact MUST be `docs/ai/research/codex-agent-route-candidates.md`.
- **FR-002**: The implementation artifact MUST be documentation-only and MUST NOT change runtime behavior, agent TOMLs, installers, payloads, cache proofs, generated payloads, versions, or live model evaluation state.
- **FR-003**: The artifact MUST include an official-source ledger with source family, retrieval method, requested URLs, canonical URLs, retrieval date, durable retrieval evidence, page or section locators, short excerpt anchors, bounded source-fact extracts, extract hashes, invalidation triggers, and claim bindings for every platform fact.
- **FR-004**: The artifact MUST treat official OpenAI documentation as the only authority for platform and model facts.
- **FR-005**: The artifact MUST label repository files, active route-policy skill/runner surfaces, payloads, caches, fixtures, and Claude role definitions as `project_input` only.
- **FR-006**: The artifact MUST mark unsupported platform facts as `undocumented` and reject or block any candidate depending on those facts.
- **FR-007**: The artifact MUST record exactly twelve target role contract records: ten active Codex TOML source records and two Claude parity-only comparison records.
- **FR-008**: Each role contract record MUST include source file, production route or absence, declared model/effort/sandbox fields, instruction and full-file hashes, instruction hash extraction rule, hash encoding rule, validation result, role boundary, safety and mutation expectations, grounding requirements, separate tool/skill/MCP contracts, source config bindings, output contract, client surface, representative future task, and effective-runtime fields marked for later verification.
- **FR-009**: Claude parity-only roles `consensus-synthesizer` and `gate-validator` MUST be comparison records only and MUST NOT be described as active Codex agents.
- **FR-010**: The artifact MUST evaluate the current roadmap seed models `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`, `gpt-5.5`, and `gpt-5.3-codex-spark` only against current official OpenAI documentation; historical seed inputs may be recorded only as rejected, blocked, or undocumented exclusions.
- **FR-011**: The artifact MUST record provisional candidate records with `candidate_route_id`, `agent_contract_id`, source bindings, source fact extract hash, effort-surface records, role instruction hash, candidate rationale, required capabilities, unsupported facts, lifecycle gap fields, blocked model/effort tuple status when required, and invalidation rules.
- **FR-012**: No candidate record MUST claim availability, executability, qualification, preference, efficiency, fallback behavior, or exact treatment before G56R-002/G56R-003 evidence exists.
- **FR-013**: The artifact MUST record the fixture baseline as exactly three current prompt-emulation fixtures and nine missing executable role fixtures.
- **FR-014**: Every fixture backlog record MUST include fixture ID, current status, executable specification, representative input, telemetry need, success oracle, blocking dependency, owner spec, priority, and invalidation triggers.
- **FR-015**: Historical prompt-emulation evidence MUST be labeled `non_release_evidence`.
- **FR-016**: The G56R-002 handoff MUST include capability questions, telemetry contract needs including terminal state and missing-field classification, candidate and fixture invalidation rules, fixture backlog, and a go/no-go matrix.
- **FR-017**: The final report traceability section MUST map every claim to `official_documentation`, `project_input`, `runtime_verification_needed`, `qualification_needed`, or `undocumented`.
- **FR-018**: The report MUST end with a strict decision that is `GO` only for G56R-002 capability discovery and telemetry profiling when evidence completeness is satisfied, and `NO-GO` for route qualification or installation.

### Required Acceptance Criteria

- **AC-1.1**: Official-source ledger with source family, retrieval method, requested URLs, canonical URLs, retrieval date, durable retrieval evidence, page or section locators, short excerpt anchors, bounded source-fact extracts, extract hashes, invalidation triggers, and claim bindings.
- **AC-1.2**: Exactly twelve role contract records with source file, production route or absence, declared model/effort/sandbox fields, instruction and full-file hashes, instruction hash extraction rule, hash encoding rule, validation result, role boundary, safety and mutation expectations, grounding requirements, separate tool/skill/MCP contracts, source config bindings, output contract, client surface, representative future task, and effective-runtime fields marked for later verification.
- **AC-1.3**: Provisional candidate records bind official-source IDs, exact source facts, source fact extract hashes, effort-surface records, role instruction hash, candidate rationale, and role contract requirements; they explicitly mark unsupported facts and block executable model/effort tuple admission until the required effort is proven.
- **AC-1.4**: Fixture backlog contains exactly three current and nine missing records with fixture ID, current status, executable specification, representative input, telemetry need, success oracle, blocking dependency, owner spec, priority, and invalidation triggers.
- **AC-1.5**: No candidate claims availability, executability, qualification, preference, efficiency, or fallback behavior without official documentation and later phase evidence.
- **AC-1.6**: G56R-002 handoff includes capability questions, telemetry contract, invalidation rules, fixture backlog, and go/no-go matrix.
- **AC-1.7**: Final report traceability maps every claim to official documentation, project input, runtime verification needed, qualification needed, or undocumented status.

### Official-Source Ledger Seed

The implementation artifact must refresh these sources during its own authoring pass and must not rely on this spec as the evidence source.

Each refreshed ledger record MUST include `source_url_requested`, canonical or
redirected URL, `retrieved_at_utc`, retrieval method, source family,
page/section title, supported surface, documented fact, bounded source-fact
extract, extract hash, claim binding, conflict status, access status, and
invalidation trigger.

| ID | Direct URL | Retrieved | Source family | Claim bindings | Invalidation triggers |
|---|---|---:|---|---|---|
| `OSL-001` | `https://developers.openai.com/codex/models` | 2026-07-16 | Codex models | Current Codex model recommendations, model IDs, deprecated Codex models, Codex CLI model flag examples, reasoning effort guidance | Model list changes, deprecation wording changes, support surfaces change, new recommended model appears |
| `OSL-002` | `https://developers.openai.com/codex/agent-configuration/subagents` | 2026-07-16 | Codex subagents/custom agents | Custom agent TOML optional fields for `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, `skills.config`, and parent inheritance for those omitted fields | Custom agent schema changes, spawn semantics change, inheritance wording changes, effort values change |
| `OSL-003` | `https://learn.chatgpt.com/docs/config-file/config-reference` | 2026-07-16 | Codex configuration | `model_reasoning_effort` and managed model defaults | Config key names/values change, managed defaults change, MCP config behavior changes |
| `OSL-004` | `https://learn.chatgpt.com/docs/app-server` | 2026-07-16 | Codex app server | `model/list`, `modelProvider/capabilities/read`, `supportedReasoningEfforts`, `defaultReasoningEffort`, `inputModalities`, app listing, command/MCP methods, and token/account usage fields where documented | JSON-RPC method schema changes, telemetry fields change, reroute event appears or changes, experimental method status changes |
| `OSL-005` | `https://learn.chatgpt.com/docs/non-interactive-mode` | 2026-07-16 | Codex non-interactive | `codex exec`, JSON lifecycle/item/error events, and output schema | JSONL event types change, auth guidance changes, sandbox behavior changes |
| `OSL-006` | `https://developers.openai.com/codex/extend/mcp` | 2026-07-16 | Codex MCP | Codex MCP CLI commands, stdio/HTTP setup, and plugin-bundled MCP server support | MCP transport, auth, plugin MCP, or shared-config behavior changes |
| `OSL-007` | `https://developers.openai.com/apps-sdk/mcp-apps-in-chatgpt` | 2026-07-16 | ChatGPT Apps SDK | MCP app iframe bridge and tool-call boundary in ChatGPT | Apps SDK or hosted MCP compatibility changes |
| `OSL-008` | `https://developers.openai.com/api/docs/guides/latest-model` | 2026-07-16 | API model guidance and prompting | GPT-5.6 API model family, `gpt-5.6` alias, reasoning effort values, pro mode, prompting/migration guidance | Model family guidance changes, effort values change, prompting guidance changes |
| `OSL-009` | `https://developers.openai.com/api/docs/deprecations` | 2026-07-16 | API model lifecycle | Deprecated, retiring, shut down, removed, or replacement model lifecycle facts for exact seed slugs | Deprecation wording changes, shutdown date changes, substitute model changes, seed slug disappears |

### Roadmap Seed Candidate Admission

The current roadmap seed models are not automatically admitted. Current official Codex documentation is decisive.

| Seed model | G56R-001 status | Required report treatment |
|---|---|---|
| `gpt-5.6-sol` | `execution_snapshot_review_required` | Evaluate against refreshed official source records and admit only as a provisional discovery candidate when role contract and source bindings support it. |
| `gpt-5.6-terra` | `execution_snapshot_review_required` | Evaluate against refreshed official source records and admit only as a provisional discovery candidate when role contract and source bindings support it. |
| `gpt-5.6-luna` | `execution_snapshot_review_required` | Evaluate against refreshed official source records and admit only as a provisional discovery candidate when role contract and source bindings support it. |
| `gpt-5.5` | `execution_snapshot_review_required` | Treat as an immutable comparator where project inventory records it and retain as a candidate only while current official documentation supports it. |
| `gpt-5.3-codex-spark` | `execution_snapshot_review_required` | Treat as an optional-helper candidate only when current official documentation and the role contract support it; account/surface availability remains G56R-002 runtime verification. |

### Historical And Legacy Seed Exclusions

These entries came from earlier roadmap drafts, adjacent naming patterns, or
legacy project-input fallback guidance. They are not the current roadmap seed
set and cannot be admitted unless current official documentation independently
supports them.

| Historical or legacy input | G56R-001 status | Required report treatment |
|---|---|---|
| `gpt-5.1` | `undocumented_for_current_codex_route` | Do not admit unless an official current Codex source supports it for the pinned surface. |
| `gpt-5.1-codex-max` | `rejected_undocumented_lifecycle_detail` | Reject unless current official lifecycle docs publish exact text for the slug; record lifecycle state, surface, shutdown date, replacement model, and source binding only when captured. |
| `gpt-5.2` | `rejected_undocumented_for_current_codex_route` | Do not admit for new Codex sign-in route policy; API-key availability, if any, is a separate G56R-002 capability question and not route authority. |
| `gpt-5.2-codex` | `rejected_undocumented_lifecycle_detail` | Reject unless current official lifecycle docs publish exact text for the slug; record lifecycle state, surface, shutdown date, replacement model, and source binding only when captured. |
| `gpt-5.2-codex-pro` | `rejected_undocumented` | Reject unless an official current OpenAI source publishes this exact model or pro-route construct; do not infer it from GPT-5.6 pro mode or adjacent model names. |
| `gpt-5.4` | `rejected_undocumented_for_current_codex_route` | Treat legacy UAT TOML and installer rewrite fallback guidance as project input only; do not admit unless official current Codex documentation supports this exact slug for the pinned surface. |

### Refreshed Provisional Candidate Pool

This table is a non-authoritative execution snapshot, not a fixed route set.
The implementation artifact must refresh it from current official
documentation, may add or remove candidates only with direct official evidence,
and may admit entries only as provisional route candidates with official-source
bindings. Runtime availability, exact treatment, quality, and fallback order
remain unresolved.

| Candidate model | Source binding | Provisional role fit | Unsupported or unresolved facts |
|---|---|---|---|
| `gpt-5.6-sol` / alias `gpt-5.6` | `OSL-001`, `OSL-002`, `OSL-008` | Quality-first executor, research, planning, and high-value reasoning roles | Runtime availability, exact effort support, effective route telemetry, qualification |
| `gpt-5.6-terra` | `OSL-001`, `OSL-002`, `OSL-008` | Balanced executor, analyst, and parallel-worker roles | Runtime availability, exact effort support, effective route telemetry, qualification |
| `gpt-5.6-luna` | `OSL-001`, `OSL-002`, `OSL-008` | Clear, repeatable, high-volume, or structured summary roles | Runtime availability, exact effort support, qualification for nontrivial roles |
| `gpt-5.5` | `OSL-001`, `OSL-002` | Immutable comparator where current TOML project input uses it | Future availability, whether to retain as candidate after discovery |
| `gpt-5.3-codex-spark` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004` | Optional latency-first helper and near-instant text-only cases | Account/surface availability runtime verification, text-only suitability, role qualification |

### Candidate Route Record Shape

Every candidate route record in the implementation artifact MUST use this minimum shape:

- `candidate_route_id`: stable identifier, e.g. `G56R-001-CR-<agent>-<model>` before G56R-002 effort discovery and `G56R-001-CR-<agent>-<model>-<effort>` after executable tuple admission.
- `agent_contract_id`: one of the twelve role contracts below.
- `official_source_ledger_ids`: at least one model source and one custom-agent/configuration source.
- `source_fact_extract_sha256`: hash of the bounded official-documentation extract supporting the candidate rationale.
- `model` and `model_reasoning_effort`: explicit tuple only when admitted; blocked model candidates use `blocked_pending_model_list_effort` until G56R-002 proves supported efforts for the pinned client.
- `effort_surface_records`: per-surface evidence entries for `codex_model_guidance`, `custom_agent_toml`, `config_toml`, `app_server_catalog`, or `responses_api`, with source ledger ID, setting or field name, documented values or an explicit undocumented classification, documented default or `not_documented_for_surface`, default scope, runtime-support requirement, and claim status.
- `role_instruction_sha256`: exact instruction hash from the bound `AgentContractRecord`.
- `candidate_rationale`: exact source fact plus role-contract need that source-binds the provisional model candidate for discovery.
- `required_qualification_artifacts`: role-specific fixture backlog ID plus the
  required G56R-002/G56R-003 artifact identities: `runtime_capability_snapshot_id`,
  `telemetry_profile_id`, `route_resolution_id`, `execution_trace_id`, and
  `experiment_policy_id` with scorer contract.
- `role_contract_binding`: required reasoning depth, role boundary, safety boundary, mutation boundary, grounding, tool contract, skill contract, MCP contract, output contract, source config bindings, and client surface.
- `unsupported_facts`: list every missing fact as `undocumented`, `runtime_verification_needed`, or `qualification_needed`.
- `candidate_status`: `admitted_for_discovery`, `rejected_undocumented`, `rejected_undocumented_lifecycle_detail`, `rejected_undocumented_for_current_codex_route`, `rejected_deprecated_or_withdrawn`, or `blocked_pending_capability`.
- `lifecycle_state`: `current`, `deprecated`, `retiring`, `shut_down`, `removed`, `undocumented`, `undocumented_in_current_snapshot`, or `not_applicable`, with explicit `shutdown_date` and `replacement_model` values when official lifecycle docs provide them or explicit not-recorded/not-applicable values otherwise.
- `invalidation_rules`: documentation changes, model deprecation, source withdrawal, capability snapshot mismatch, telemetry-profile mismatch, instruction hash change, or fixture/scorer change.

### Role Contract Record Shape

Every `agent_contract_id` record in the implementation artifact MUST include
these normalized fields:

- `role`, `source_file`, `source_class`, and `client_surface`.
- `production_route_status`: `active_codex_toml` or `parity_only_absent`.
- `declared_toml_model`, `declared_toml_model_reasoning_effort`,
  `declared_toml_sandbox_mode`, and `declared_toml_mutation_intent` for active
  Codex TOML roles; parity-only roles use `absent`.
- `instruction_sha256`, `full_file_sha256`, `hash_source`,
  `instruction_hash_extraction_rule`, `instruction_hash_encoding`, and
  `hash_validation_status`.
- `role_boundary`: in-scope actions, out-of-scope actions, and representative
  future task.
- `safety_contract`, `grounding_contract`, `mutation_contract`,
  `tool_contract`, `skill_contract`, `mcp_contract`, `source_config_bindings`,
  and `output_contract`.
- `effective_runtime_permissions`, `effective_parent_overrides`, and
  `effective_sandbox_and_approval_policy`, all set to
  `runtime_verification_needed` in G56R-001.
- `exact_treatment_boundary`: G56R-001 records declared source fields only;
  G56R-002/G56R-003 must prove effective sandbox, approvals, model/effort,
  parent configuration, loaded tools/skills/MCP, and telemetry before any route
  can be qualified.
- `platform_divergence` for `consensus-synthesizer` and `gate-validator`,
  recording `active_codex_route_status=absent` and treating Claude model,
  effort, and disallowed-tool metadata as `project_input` only.

### Role Contract Matrix

| `agent_contract_id` | Role | Source file | Role intent | Mutation expectation | Grounding requirement | Tools/skills/MCP needs | Output contract | Client surface | Representative future task |
|---|---|---|---|---|---|---|---|---|---|
| `G56R-001-AC-ANALYZE-EXECUTOR` | `analyze-executor` | `speckit-pro/codex-agents/analyze-executor.toml` | Run `$speckit-analyze`, research every finding, apply fixes, and summarize remediation | `workspace-write`; edits spec, plan, tasks, or code as required by findings | Capability-first research plus local artifacts and citations | Analyze command, marker counter, codebase/domain/spec sources | `## Analyze Result` with finding remediation, files, verification, unresolved items | Active Codex custom agent | Remediate all Analyze findings for a routed G56R spec. |
| `G56R-001-AC-AUTOPILOT-FAST-HELPER` | `autopilot-fast-helper` | `speckit-pro/codex-agents/autopilot-fast-helper.toml` | Compress, triage, draft queries, or normalize prompt context quickly | `read-only`; no commands, edits, decisions, or spawned agents | Uses only prompt context | No tool, skill, MCP, filesystem, or web dependency | Fast brief, triage, query drafts, or compact context | Active optional Codex custom agent | Summarize an executor result for the parent orchestrator. |
| `G56R-001-AC-CHECKLIST-EXECUTOR` | `checklist-executor` | `speckit-pro/codex-agents/checklist-executor.toml` | Run one `$speckit-checklist` domain and remediate all gap markers | `workspace-write`; edits spec, plan, checklist artifacts | Capability-first research plus constitution/prior specs | Checklist command, marker counter, codebase/domain/spec sources | `## Checklist Domain Result` with gaps, fixes, verification | Active Codex custom agent | Close evidence-integrity gaps in the G56R-001 artifacts. |
| `G56R-001-AC-CLARIFY-EXECUTOR` | `clarify-executor` | `speckit-pro/codex-agents/clarify-executor.toml` | Prepare clarify questions and recommendations without acting as user | `read-only`; no artifact edits or interactive skills | Research-based recommendations from workflow/spec/project sources | Read-only discovery, codebase, docs, project context | `## Clarify Question Set` with questions, evidence, markers | Active Codex custom agent | Prepare `$speckit-clarify` questions after Specify markers. |
| `G56R-001-AC-CODEBASE-ANALYST` | `codebase-analyst` | `speckit-pro/codex-agents/codebase-analyst.toml` | Answer consensus questions from existing code patterns only | `read-only` | File references and code patterns | Codebase search, structure, targeted reads | `## Answer`, `## Evidence`, `## Confidence` | Active Codex custom agent | Resolve a gap by citing existing repository behavior. |
| `G56R-001-AC-DOMAIN-RESEARCHER` | `domain-researcher` | `speckit-pro/codex-agents/domain-researcher.toml` | Answer consensus questions from official docs, standards, and best practices | `read-only` | URL or library citations for every claim | Web/domain research, extraction, library docs | `## Answer`, `## Citations`, `## Confidence` | Active Codex custom agent | Verify current OpenAI model or config documentation. |
| `G56R-001-AC-IMPLEMENT-EXECUTOR` | `implement-executor` | `speckit-pro/codex-agents/implement-executor.toml` | Execute one implementation task with strict red-green-refactor TDD | `workspace-write`; scoped task edits only | Spec, plan, task, TDD protocol, project commands, focused external research only when required | Project commands, tests, edits, optional docs/codebase capability | `## Task Result` with TDD evidence, commands, files, errors | Active Codex custom agent | Implement one future G56R-006 resolver task. |
| `G56R-001-AC-PHASE-EXECUTOR` | `phase-executor` | `speckit-pro/codex-agents/phase-executor.toml` | Run one Specify, Plan, or Tasks phase exactly as prompted | `workspace-write` for phase artifacts only | Loaded command instructions only | Provided `$speckit-*` skill sigil and command-owned scripts/templates | `## Phase Result` summary with files, metrics, markers, errors | Active Codex custom agent | Run `$speckit-plan` for G56R-002. |
| `G56R-001-AC-SPEC-CONTEXT-ANALYST` | `spec-context-analyst` | `speckit-pro/codex-agents/spec-context-analyst.toml` | Answer consensus questions from constitution, roadmaps, specs, and decision records | `read-only` | Project artifact references by section | Constitution, roadmap, design concept, prior specs, local docs | `## Answer`, `## References`, `## Confidence` | Active Codex custom agent | Resolve a cross-spec consistency question for G56R. |
| `G56R-001-AC-UAT-RUNBOOK-AUTHOR` | `uat-runbook-author` | `speckit-pro/codex-agents/uat-runbook-author.toml` | Rewrite UAT skeleton into executable plain-English acceptance runbook | `workspace-write`; edits skeleton in place and fails open | Spec, plan, quickstart, diff, project commands | Skeleton generation output, file reads, direct edit only | Short summary of rewrites, count, removed sections | Active Codex custom agent | Produce UAT runbook for a final G56R PR. |
| `G56R-001-AC-CONSENSUS-SYNTHESIZER` | `consensus-synthesizer` | `speckit-pro/agents/consensus-synthesizer.md` | Synthesize one to three analyst outputs, apply agreement rules, produce exact edit instructions | `project_input` parity-only; Claude read-only/disallowed write tools | Analyst evidence only; no new research | Consumes codebase/spec/domain analyst responses | `## Consensus Result` with agreement, answer, edit, flags | Claude comparison only; not active Codex TOML | Define future Codex parity contract for consensus synthesis. |
| `G56R-001-AC-GATE-VALIDATOR` | `gate-validator` | `speckit-pro/agents/gate-validator.md` | Run a supplied validation command and return JSON evidence without remediation | `project_input` parity-only; mechanical command execution, no edits | Verbatim command JSON output | Gate validation command only | `## Gate Result` with status and verbatim JSON | Claude comparison only; not active Codex TOML | Define future Codex parity contract for G0-G7 validation. |

### Fixture Backlog

| Role | Current status | Executable specification | Telemetry need | Success oracle | Blocking dependency | Priority |
|---|---|---|---|---|---|---|
| `codebase-analyst` | Current prompt-emulation fixture in `fixtures-codex/codebase-analyst/` | Re-execute as materialized custom agent with read-only sandbox and codebase evidence fixtures | Assigned route, effective route or null, file-read/search item events, tokens, duration | Cites 1-5 file evidence items and stays in codebase lane | G56R-002 telemetry profile, G56R-003 materializer | P1 |
| `domain-researcher` | Current prompt-emulation fixture in `fixtures-codex/domain-researcher/` | Re-execute with official-doc source access and citation capture | Assigned/effective route, web/doc/MCP item events, token vector, duration | Provides official citations and confidence without codebase claims | G56R-002 MCP/tool telemetry classification | P1 |
| `spec-context-analyst` | Current prompt-emulation fixture in `fixtures-codex/spec-context-analyst/` | Re-execute with project docs and no writes | Assigned/effective route, file reads, token vector, duration | Cites constitution/roadmap/spec sections and proposes exact spec text when applicable | G56R-003 exact treatment | P1 |
| `analyze-executor` | Missing executable fixture | Run synthetic Analyze findings through command, remediation loop, and marker recount in a disposable feature fixture | Command execution, file changes, marker counts, retries, duration, tokens | All findings remediated or tagged for consensus after bounded loops | G56R-003 runner and safe fixture repo | P1 |
| `autopilot-fast-helper` | Missing executable fixture | Invoke one compression, one triage, one query draft, and one context normalization prompt as separate helper cases | Spawn reliability, route, latency, output tokens | Compact advisory output, no decisions, no tools, no mutation | G56R-010 helper campaign and no-helper contract | P2 |
| `checklist-executor` | Missing executable fixture | Run one checklist domain with seeded gap markers and verify remediation loop | Checklist output, marker counts, file changes, tokens, duration | All gaps closed or tagged after bounded loops | G56R-003 exact treatment plus checklist fixture | P1 |
| `clarify-executor` | Missing executable fixture | Provide spec/workflow ambiguity and require bounded question set without edits | File reads, route, markers count, tokens, duration | Up to five questions with evidence and no interactive skill invocation | G56R-002 telemetry and safe spec fixture | P1 |
| `implement-executor` | Missing executable fixture | Assign one small TDD task with known failing then passing test in fixture repo | Test commands, RED/GREEN evidence, file changes, route, tokens, duration | Tests fail for real reason, then pass, scoped edits only | G56R-003 executable harness | P1 |
| `phase-executor` | Missing executable fixture | Run a fake Specify/Plan/Tasks command fixture with command-owned template and no extra context | Created files, markers, phase metrics, route, tokens, duration | Only command instructions followed; concise phase result returned | Command fixture scaffolding in G56R-003 | P1 |
| `uat-runbook-author` | Missing executable fixture | Rewrite generated UAT skeleton with known placeholders into plain-English runbook | File change evidence, route, tokens, duration | Env setup, story steps, and FR matrix rewritten; fail-open preserved | G56R-003 skeleton fixture | P2 |
| `consensus-synthesizer` | Missing executable fixture | Replay 1-, 2-, and 3-analyst consensus cases, including security override and all-disagree | Route, input analyst hashes, output hash, tokens, duration | Correct agreement, flags, and exact edit behavior | Future Codex parity TOML in G56R-009 | P1 |
| `gate-validator` | Missing executable fixture | Execute supplied gate command returning JSON and verify verbatim pass/fail summary | Command execution, exit code, JSON output, route, duration | Verbatim JSON preserved; no remediation or artifact reads | Future Codex parity TOML in G56R-009 | P1 |

Existing Claude prompt-emulation fixtures under
`tests/speckit-pro/layer6-efficiency/fixtures/` are `project_input` and
`non_release_evidence`. They do not count as current Codex executable fixtures
and cannot qualify a route.

### Fixture Backlog Record Shape

Every fixture backlog record in the implementation artifact MUST include:

- `fixture_backlog_id`: stable identifier, e.g.
  `G56R-001-FB-<role>`.
- `agent_contract_id` and role name.
- `current_status`: `current_prompt_emulation_codex`,
  `existing_claude_prompt_emulation_project_input`, or
  `missing_executable_fixture`.
- `current_source_path` when a prompt-emulation fixture exists.
- `non_release_evidence`: true for all current prompt-emulation records.
- `executable_specification`: future harness setup, materialized role,
  representative input, expected tool/skill/MCP/sandbox needs, and allowed
  mutation boundary.
- `telemetry_requirements`: assigned route, effective route or null, model,
  effort, parent-child attribution, loaded tools/skills/MCP, sandbox and
  approval evidence, token vector, duration, retries, route-match status,
  terminal state, terminal reason, and missing-field classification.
- `success_oracle`: observable pass criteria independent of model preference.
- `blocking_dependency`: required future G56R spec, runner, materializer,
  telemetry profile, or fixture harness.
- `owner_spec`, `priority`, `invalidation_triggers`, and
  `no_payload_created_in_g56r_001=true`.

### G56R-002 Handoff Contract

The final report MUST hand off these questions and constraints:

- Which source-bound blocked candidates appear in `model/list` for the pinned client with `includeHidden` policy declared?
- Which model entries expose `supportedReasoningEfforts`, `defaultReasoningEffort`, and `inputModalities`?
- Which provider capabilities are returned by `modelProvider/capabilities/read` for each source-bound blocked candidate?
- Which surface can prove requested model, requested effort, effective model, effective effort, service reroute if documented, route-match status, token usage, duration, retry count, terminal state, terminal reason, and parent/child attribution?
- Which telemetry fields are `stable_native`, `experimental_native`,
  `derived_from_controlled_configuration`, `conditional`, `unavailable`,
  `not_applicable`, or `undocumented`?
- Which evidence separates declared TOML model/effort/sandbox/mutation fields from effective runtime sandbox, approval policy, parent overrides, and loaded tool/skill/MCP state?
- Which exact-treatment evidence proves a materialized custom-agent route matched its intended model, effort, instructions, sandbox, skills, MCP, tools, and parent configuration?
- Which role-specific fixture backlog ID, runtime capability snapshot,
  telemetry profile, route-resolution evidence, execution trace, experiment
  policy, and scorer contract bind each candidate before qualification?
- Which documented MCP/app/tool surfaces are available to each role under the pinned client?
- Which `undocumented` or deprecated seed candidates remain rejected before capability probing?
- G56R-002 may add a role/model binding only for a model already present in the
  G56R-001 official-source ledger, and only when it records role-contract
  rationale or explicit exclusion evidence before G56R-003 freezes the executable
  candidate set.
- Which candidate or fixture invalidation trigger requires source refresh,
  capability rediscovery, telemetry-profile revision, fixture/scorer revision,
  or no-go escalation before G56R-002 proceeds?

### G56R-002 Go/No-Go Matrix

| Decision area | Required evidence | G56R-001 expected result |
|---|---|---|
| Proceed to G56R-002 capability discovery | Complete official-source ledger with retrieval evidence, source-fact extract hashes, effort-surface records, twelve role contracts, role instruction hashes with all-role validation evidence, blocked/source-bound candidate table, fixture backlog, telemetry questions, and invalidation rules | `GO` if all required records exist, no unsupported route is admitted, current fixtures are labeled non-release, every candidate has a capability question, documented or undocumented effort values/defaults are explicit, and any uncaptured lifecycle field remains explicit rather than inferred |
| Proceed to executable candidate set | Runtime capability snapshot and telemetry profile | `NO-GO` in G56R-001; owned by G56R-002 |
| Proceed to route qualification | Exact treatment, fixtures, scorer, analysis plan, executable corpus | `NO-GO` in G56R-001; owned by G56R-003+ |
| Proceed to installer or fallback policy | Qualified preferred/fallback routes and resolver behavior | `NO-GO` in G56R-001; owned by G56R-006+ |

### Reviewability Notes *(if applicable)*

- This phase is documentation-only and creates no runtime route policy.
- Generated payloads, installed-cache proofs, release notes, and version updates are out of scope.
- Typed reviewability exceptions are not needed because the implementation surface is docs/process; one repository test guard allowlist may change only to admit the new Codex research report path. If post-review remediation expands process files, record the actual diff warning and keep runtime production files at zero.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: repository test guard allowlist for the new research report path
- **Projected reviewable LOC**: 0 production LOC; documentation-only research artifact
- **Projected production files**: 0
- **Projected total files**: 2 for Specify artifacts; later implementation target is one research report
- **Budget result**: within budget for planned implementation; post-review actual diff may warn on total file count but must stay below the block threshold and preserve zero runtime production files
- **Split decision**: Remains one spec because G56R-001 is a bounded research spike with no runtime behavior.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **OfficialSourceLedgerRecord**: Source family, retrieval method, requested URL, canonical official OpenAI source URL, retrieval date, durable retrieval evidence, page or section locators, short excerpt anchors, bounded source-fact extracts, extract hashes, documented facts, claim bindings, and invalidation triggers.
- **AgentContractRecord**: One target role's source file, production route or absence, declared TOML fields, instruction/full-file hashes, instruction hash extraction and encoding rules, hash validation result, role boundary, safety/mutation boundary, grounding, separate tool/skill/MCP contracts, output contract, client surface, effective-runtime verification fields, and representative future task.
- **CandidateRouteRecord**: Provisional model candidate or explicit model/effort tuple bound to an agent contract, role instruction hash, exact source fact, source fact extract hash, effort-surface records, and official-source records, with blocked tuple status when applicable, candidate rationale, unsupported facts, lifecycle gap fields, capability questions, and invalidation rules.
- **EffortSurfaceRecord**: Source-scoped effort/default record that prevents one surface's default or values from being treated as global authority.
- **FixtureBacklogRecord**: Current or missing fixture entry with stable ID, source path, non-release evidence label, executable specification, representative input, telemetry need, success oracle, blocking dependency, owner spec, priority, and invalidation triggers.
- **TraceabilityRecord**: Mapping from each claim to official documentation, project input, runtime verification needed, qualification needed, or undocumented status.
- **GoNoGoDecision**: Strict G56R-002 handoff status and blocked downstream decisions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Reviewer can count exactly 9 official-source ledger records, 25 source fact binding rows, 25 source fact extract rows, 5 effort-surface records, 12 role contract records, 12 fixture backlog records, and 0 unsupported admitted seed candidates in the research artifact.
- **SC-002**: 100% of platform facts in the report map to an `official_source_ledger_id`; unsupported or deprecated/withdrawn facts are explicitly labeled and cannot support a candidate.
- **SC-003**: 100% of role contract records include source file, production route or absence, declared TOML fields, instruction/full-file hashes, instruction hash extraction and encoding rules, hash validation result, role boundary, safety and mutation expectations, grounding requirements, separate tool/skill/MCP contracts, output contract, client surface, effective-runtime verification fields, and representative future task.
- **SC-004**: Fixture backlog contains exactly 3 current Codex prompt-emulation records and exactly 9 missing executable-fixture records; any Claude prompt-emulation records are labeled `project_input` and `non_release_evidence` outside the current-Codex count.
- **SC-005**: Report ends with an explicit `GO` or `NO-GO` for G56R-002 capability discovery and explicit `NO-GO` for route qualification and installation; `GO` requires complete source, contract, candidate, fixture, telemetry, capability-question, and invalidation records.
- **SC-006**: Search for unresolved clarification, gap, and critical marker tokens in `spec.md` returns zero matches.

## Assumptions

- The current execution snapshot is 2026-07-16 and must be refreshed inside the implementation artifact before G56R-002 consumes it.
- The active worktree already exists on branch `g56r-001-candidate-route-baseline`; no new branch is created by this phase.
- `speckit-pro/codex-agents/*.toml` currently contains ten active Codex agent files; the two additional roles are parity-only project inputs from Claude agent definitions.
- The three current prompt-emulation Codex fixtures are `codebase-analyst`, `domain-researcher`, and `spec-context-analyst`.
- A model candidate can be source-bound for discovery without being available, executable, qualified, preferred, efficient, or usable as fallback.
- The Specify phase does not create `docs/ai/research/codex-agent-route-candidates.md`; it specifies the artifact to be produced by the implementation phase.
