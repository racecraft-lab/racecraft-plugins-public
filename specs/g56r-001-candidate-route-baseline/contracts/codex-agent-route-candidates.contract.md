# Contract: Codex Agent Route Candidates Report

This contract governs the canonical human report and its sole schema-v2
planning-manifest companion. Neither artifact is runtime configuration, a
generated payload, a fixture payload, or an installer input.

## Artifact

| Field | Value |
|---|---|
| Path | `docs/ai/research/codex-agent-route-candidates.md` |
| Machine companion | `docs/ai/research/codex-agent-route-candidate-manifest.json` |
| Shared schema | `docs/ai/research/agent-route-candidate-manifest.schema.json` (`2.0.0`) |
| Shared parity contract | `docs/ai/specs/agent-routing-parity-contract.md` |
| Authority | Official OpenAI documentation for platform facts; repository files as `project_input` only |
| Runtime effect | None |
| Payload effect | None |
| Version effect | None |

## Required Sections

The report must contain these reviewable sections:

1. Scope, non-goals, authority classes, and snapshot metadata.
2. Official-source ledger with source IDs, source family, retrieval method,
   requested URLs, canonical URLs, UTC retrieval timestamp, durable retrieval
   evidence such as HTTP status/body hash, page or section title, short excerpt
   anchors, bounded source-fact extracts, extract hashes, access/conflict status,
   documented facts, supported surfaces, claim bindings, and invalidation
   triggers.
3. Project-input surface inventory for route policy, agent sources, parity
   role files, fixtures, payload/cache references, and generated artifacts.
4. Twelve role contract records.
5. Provisional candidate route manifest, candidate route records, explicit
   candidate rationales, effort-surface records, and lifecycle gap fields.
6. Fixture backlog with three current prompt-emulation records and nine missing
   executable-fixture records.
7. Telemetry requirements and G56R-002 capability questions.
8. Traceability matrix with stable `traceability_id` records.
9. Completeness matrix, go/no-go decision with stable `decision_id` records,
   downstream no-go decisions, and invalidation rules.

## Record Count Contract

The table below preserves the completed v0.1 human-report count contract. The
active schema-v2 manifest count contract is: 21 official sources, 5 effort
surfaces, 17 project inputs, 12 agent contracts, 23 candidate routes, 12
fixtures, 24 traceability records, and 5 decisions.

| Record | Required Count |
|---|---:|
| `OfficialSourceLedgerRecord` | 9 |
| Source fact binding rows | 25 |
| Source fact extract evidence rows | 25 |
| `EffortSurfaceRecord` | 5 |
| `ProjectInputRecord` | 16 |
| `AgentContractRecord` | 12 |
| `CandidateRouteRecord` | 23 |
| `FixtureBacklogRecord` | 12 |
| `TraceabilityRecord` | 24 |
| `GoNoGoDecision` | 4 |
| Current Codex prompt-emulation fixtures | 3 |
| Missing executable fixtures | 9 |
| Unsupported admitted seed candidates | 0 |

## Authority Contract

- Every platform fact must cite at least one `official_source_ledger_id`.
- Every project-derived fact must be labeled `project_input`.
- Every runtime-only fact must be labeled `runtime_verification_needed`.
- Every qualification, preference, efficiency, or fallback claim must be
  labeled `qualification_needed` or excluded.
- Every unsupported, conflicting, withdrawn, or absent platform fact must be
  labeled `undocumented` or rejected.

## Machine Companion Contract

- The manifest validates against schema `2.0.0` with `platform=codex` and
  `spec_id=G56R-001`.
- It uses only shared schema fields and the five shared evidence classes.
- All 25 legacy source-fact IDs have explicit dispositions; none is silently
  deleted or renumbered.
- The 21 current source records use only allowlisted official OpenAI domains.
- All source, role, candidate, fixture, traceability, and decision references
  resolve within the manifest.
- No candidate is executable or preferred; later capability and qualification
  evidence remains required.

## Candidate Contract

Every candidate route record must include:

- `candidate_route_id`
- `agent_contract_id`
- `official_source_ledger_ids`
- explicit model and effort tuple or a blocked status explaining why no tuple
  is admitted
- explicit effort-surface record bindings
- explicit `effort_surface_record_ids`
- explicit role instruction hash from the bound role contract record
- candidate rationale binding an exact source fact, bounded source extract, and
  extract hash to a role-contract need
- required qualification artifacts, including the role-specific fixture backlog
  ID, `runtime_capability_snapshot_id`, `telemetry_profile_id`,
  `route_resolution_id`, `execution_trace_id`, and `experiment_policy_id` with
  scorer contract
- remaining incompatibilities or gaps
- role-contract binding
- required runtime capabilities
- unsupported facts
- candidate status
- lifecycle state when documented
- shutdown date and replacement model when documented, otherwise an explicit
  not-recorded value
- G56R-002 capability questions
- invalidation rules

No candidate route record may claim availability, executability,
qualification, preference, efficiency, fallback order, or exact treatment.

The report must hand off that G56R-002 may add a role/model binding only for a
model already present in the G56R-001 official-source ledger, and only when the
binding records role-contract rationale or explicit exclusion evidence before
G56R-003 freezes the executable candidate set.

## Role Contract

Every role contract record must include:

- source file and source class
- production route status or recorded absence
- declared TOML model, effort, sandbox, and mutation fields when applicable
- instruction and full-file hashes when a source file exists
- instruction hash extraction rule, hash encoding rule, and complete validation
  result for all twelve role source records
- role boundary
- safety contract
- grounding contract
- mutation contract
- separate tool, skill, and MCP contracts
- source configuration bindings
- output contract
- client surface
- representative future task
- effective runtime fields set to `runtime_verification_needed`

## Fixture Contract

Every fixture backlog record must include:

- stable fixture backlog ID
- linked role contract ID
- current status
- current source path when present
- non-release evidence label
- executable specification
- representative input
- telemetry requirements
- success oracle
- blocking dependency
- owner spec
- priority
- invalidation triggers
- `no_payload_created_in_g56r_001=true`

## Completion Contract

The report is complete only when:

- all required sections exist
- stable traceability and go/no-go decision IDs are present
- exact counts match this contract
- every platform claim binds official documentation with source family,
  retrieval method, durable retrieval evidence, bounded source-fact extracts,
  and extract hashes
- every active route-policy project-input surface is inventoried as
  non-authoritative project input
- every unsupported route is rejected or blocked
- every deferred runtime claim is handed off to G56R-002
- route qualification, installation, resolver behavior, and fallback policy are
  explicitly `NO-GO` for G56R-001
- changed-file scope confirms no runtime, installer, payload, cache, fixture
  payload, generated artifact, or version change
- the schema-v2 companion passes shared schema, source-domain, cross-reference,
  historical-disposition, and cross-platform structural-parity validation
