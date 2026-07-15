# Contract: Codex Agent Route Candidates Report

This is a planning-only Markdown contract for
`docs/ai/research/codex-agent-route-candidates.md`. It is not a runtime schema,
generated manifest, fixture payload, or installer input.

## Artifact

| Field | Value |
|---|---|
| Path | `docs/ai/research/codex-agent-route-candidates.md` |
| Authority | Official OpenAI documentation for platform facts; repository files as `project_input` only |
| Runtime effect | None |
| Payload effect | None |
| Version effect | None |

## Required Sections

The report must contain these reviewable sections:

1. Scope, non-goals, authority classes, and snapshot metadata.
2. Official-source ledger with source IDs, direct URLs, retrieval date, source
   family, documented facts, supported surfaces, claim bindings, and
   invalidation triggers.
3. Project-input surface inventory for route policy, agent sources, parity
   role files, fixtures, payload/cache references, and generated artifacts.
4. Twelve role contract records.
5. Provisional candidate route manifest and candidate route records.
6. Fixture backlog with three current prompt-emulation records and nine missing
   executable-fixture records.
7. Telemetry requirements and G56R-002 capability questions.
8. Traceability matrix.
9. Completeness matrix, go/no-go decision, downstream no-go decisions, and
   invalidation rules.

## Record Count Contract

| Record | Required Count |
|---|---:|
| `OfficialSourceLedgerRecord` | 9 |
| `AgentContractRecord` | 12 |
| `FixtureBacklogRecord` | 12 |
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

## Candidate Contract

Every candidate route record must include:

- `candidate_route_id`
- `agent_contract_id`
- `official_source_ledger_ids`
- explicit model and effort tuple or a blocked status explaining why no tuple
  is admitted
- role-contract binding
- required runtime capabilities
- unsupported facts
- candidate status
- lifecycle state when documented
- G56R-002 capability questions
- invalidation rules

No candidate route record may claim availability, executability,
qualification, preference, efficiency, fallback order, or exact treatment.

## Role Contract

Every role contract record must include:

- source file and source class
- production route status or recorded absence
- declared TOML model, effort, sandbox, and mutation fields when applicable
- instruction and full-file hashes when a source file exists
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
- exact counts match this contract
- every platform claim binds official documentation
- every unsupported route is rejected or blocked
- every deferred runtime claim is handed off to G56R-002
- route qualification, installation, resolver behavior, and fallback policy are
  explicitly `NO-GO` for G56R-001
- changed-file scope confirms no runtime, installer, payload, cache, fixture
  payload, generated artifact, or version change
