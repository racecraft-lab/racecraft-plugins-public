# Data Model: Candidate Route Baseline and Role Contracts

## Model boundaries

The published JSON is an agent-centric projection of the cited Markdown
narrative. It is not an executable router, installation manifest, qualification
result, or final fallback policy. Every route and candidate remains bound to one
named agent's semantic contract.

The root envelope contains:

- `manifest_type`: literal `agent_route_candidate_manifest`
- `manifest_version`: integer `1`
- `research_date`: ISO date `YYYY-MM-DD`
- `agents`: exactly twelve self-contained `AgentRecord` objects
- `handoff`: one `HandoffDecision`

No normalized top-level contract, route, candidate, or evidence table is
allowed. Presentation order is lexical by stable ID only and never means
preference or fallback rank.

## Entity relationships

```text
Manifest
├── AgentRecord (exactly 12)
│   ├── AgentContract (exactly 1)
│   ├── ProductionRoute (exactly 1; present or absent)
│   ├── CandidateRoute (1..n unless evidence proves none)
│   │   ├── CapabilityRequirements
│   │   ├── Rationale
│   │   ├── Incompatibility (0..n)
│   │   ├── QualificationRequirements
│   │   └── ProvenanceRecord (1..n)
│   ├── SourceObservation (exactly one per required evidence class)
│   ├── SurfaceRecord (independent records as applicable)
│   ├── FixtureContract (exactly 1)
│   ├── TelemetryRequirement (1..n)
│   └── ClassifiedUnknown (0..n)
└── HandoffDecision
    ├── CompletionCheck (one per objective gate)
    └── UnmetCondition (0..n; required for no_go)
```

## `AgentRecord`

Required fields:

- `agent_name`: one exact name from the FR-002 set
- `agent_contract`: `AgentContract`
- `production_route`: `ProductionRoute`
- `candidates`: explicit array of `CandidateRoute`
- `source_observations`: tracked, cache, and installed observations kept
  independent
- `surface_records`: explicit applicability records using the four allowed
  surface values
- `fixture_contract`: `FixtureContract`
- `telemetry_requirements`: non-empty array
- `classified_unknowns`: explicit array, empty when none
- `provenance`: non-empty array of `ProvenanceRecord`
- `invalidation_triggers`: non-empty array of concrete triggers

Validation rules:

- Agent names are unique and equal exactly the twelve-name required set.
- All embedded contract, route, candidate, fixture, and evidence records refer
  to the enclosing `agent_name`.
- The normalized Markdown projection contains the same record.

## `AgentContract`

Required identity fields:

- `agent_contract_id`: `agent-contract/<agent-name>/v<N>`
- `instruction_hash`: lowercase `sha256:<64-hex>`
- `contract_hash`: lowercase `sha256:<64-hex>`

Required FR-006 semantic fields:

- `role_boundary`
- `authorization_boundaries`
- `safety_requirements`
- `grounding_requirements`
- `mutation_policy`
- `tool_requirements`
- `skill_requirements`
- `mcp_requirements`
- `sandbox_expectations`
- `output_contract`
- `supported_client_assumptions`
- `representative_tasks`

All semantic fields are non-empty strings or explicit non-empty arrays as
defined by the contract. The two parity-role contracts derive these semantics
from the cited Claude instruction bodies, while excluding Claude frontmatter,
tool-list syntax, transport, and routing mechanics.

### Canonical identity rules

Before either hash:

1. Normalize every string to Unicode NFC.
2. Normalize CRLF and CR line endings to LF.
3. Preserve every other whitespace character.
4. Encode UTF-8 without a BOM.

`instruction_hash` covers the complete decoded instruction body only. For the
two parity roles, it covers the cited Claude body as semantic source without
implying a Codex production route.

`contract_hash` covers a mapping containing `agent_name` and exactly the twelve
semantic fields above after recursive string normalization. Serialize with:

```python
json.dumps(
    payload,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
)
```

IDs, hashes, production routes, candidates, provenance, invalidation triggers,
and presentation fields are excluded from the contract-hash payload. An ID is
never reused after the canonical content or bound route tuple changes.

## `ProductionRoute`

Required fields:

- `status`: `present` or `absent`
- `candidate_route_id`
- `model_id`
- `reasoning_effort`
- `instruction_hash`
- `contract_hash`
- `absence_reason`
- `provenance`
- `invalidation_triggers`

State rules:

- Exactly ten agents use `present` with non-null route bindings and null
  `absence_reason`.
- Only `consensus-synthesizer` and `gate-validator` use `absent`, null route
  bindings, and a non-empty cited absence reason.
- A tracked source establishes the project production route. Cache or installed
  observations can report mismatch but cannot change this state.

## `CandidateRoute`

Required fields:

- `candidate_route_id`
- `agent_contract_id`
- `model_id`
- `reasoning_effort`
- `treatment`
- `instruction_hash`
- `contract_hash`
- `project_eligibility`
- `installation_availability`
- `capability_requirements`
- `rationale`
- `known_incompatibilities`
- `qualification_requirements`
- `provenance`
- `invalidation_triggers`

Identity form:

`candidate-route/<agent-name>/<model-slug>/<effort-slug>/<treatment-slug>/v<N>`

`treatment-slug` is `unchanged` or an evidence-justified variant. Exact model,
effort, and treatment values remain separate fields. The ID contains no rank.

Validation rules:

- `project_eligibility` is one of `eligible` or `excluded` and includes its
  evidence-backed basis.
- `installation_availability.status` is always `unresolved_g56r_002` in this
  feature; sanitized observations cannot change eligibility.
- A variant requires a bounded overhead hypothesis and a corresponding
  unchanged candidate control.
- An exclusion requires a cited incompatibility, hard-contract failure, or
  applicable predeclared dominance record. Local unavailability is invalid.
- Candidates remain `unqualified` or `not_applicable_excluded`; no field may
  claim executability, qualification, preference, or fallback rank.

## `CapabilityRequirements`

Required independent fields:

- `model`
- `modalities`
- `reasoning_effort`
- `custom_agents`
- `tools`
- `skills`
- `mcp`
- `sandbox`
- `mutation`
- `clients`

Each field records a concrete requirement or an explicit unresolved value with
evidence/owner. Capability availability is not tested in G56R-001.

## `Rationale`

Required fields:

- `classification`: fact, inference, proposed policy, assumption, or hypothesis
- `summary`: non-empty and non-ranking explanation
- `evidence_ids`: non-empty when the rationale asserts an evidence-backed fact

## `Incompatibility`

Required fields:

- `contract_field`
- `description`
- `evidence_ids`
- `eligibility_effect`: `none` or `exclude`

Use an explicit empty `known_incompatibilities` array when none exist. A hard
authorization, safety, grounding, mutation, tool, sandbox, or output-contract
failure requires `exclude`.

## `QualificationRequirements`

Required fields:

- `status`: `unqualified` or `not_applicable_excluded`
- `capability_checks`
- `fixture`
- `required_artifacts`
- `telemetry`
- `owner_spec`: normally `G56R-002` or `G56R-003`

These are handoff requirements, not evidence that qualification occurred.

## Evidence entities

### `ProvenanceRecord`

Common required fields:

- `evidence_id`
- `evidence_class`
- `classification`
- `exact_locator`
- `observed_or_retrieved_on`
- `surface`
- `feature`
- `documented_scope`
- `applicability`
- `conflict_status`
- `invalidation_triggers`

Official platform provenance additionally requires `source_url` and uses only
an official OpenAI URL. Missing source scope is the literal `not_stated`.

Tracked project provenance additionally requires `repository_path`,
`repository_revision`, and `evidence_role`. Paths are repository-relative.

Cache and installed records use logical locators only. They never contain a
home/absolute path, username, hostname, credential, secret, or unrelated
configuration field.

Allowed claim classifications are `platform_fact`, `project_fact`,
`reasonable_inference`, `proposed_policy`, `unverified_assumption`,
`environment_observation`, and `conflict`.

Allowed conflict states are `none`, `resolved_by_authority`,
`blocking_no_go`, and `nonblocking_deferred`. A deferred conflict also records
owner, impact, and required follow-up and supports no G56R-001 conclusion.

### `SourceObservation`

Each agent records independent `tracked_source`, `cached_source`, and
`installed_state` observations. Retained common fields are limited to:

- evidence class
- agent name
- relevant model ID and effort, when present
- instruction and contract hashes
- observation date
- surface
- version, when known

Tracked source adds repository-relative path, revision, and evidence role.
Cache/installed observations add only a logical locator. A mismatch records a
finding and owner but does not mutate the source or production record.

### `SurfaceRecord`

Required fields:

- `surface`: one of `cli`, `desktop_app`, `app_server`, `non_interactive`
- `feature`
- `applicability`: `documented`, `undocumented`, or `not_applicable`
- `evidence_ids`
- `documented_scope`
- `conflict_status`

Each record is independent. `not_applicable` requires explicit official
evidence; missing evidence becomes `undocumented`.

## `FixtureContract`

Required fields:

- `status`: `current` or `missing`
- `fixture_path`: repository-relative string for current fixtures, otherwise
  null
- `representative_task`
- `input_type`
- `expected_behavior`
- `expected_output_shape`
- `hard_contract_assertions`: covers the applicable FR-006 fields
- `evidence_class`: historical prompt-emulation is always
  `non_release_evidence`

Exactly the following three are current: `codebase-analyst`,
`domain-researcher`, `spec-context-analyst`. The other nine required agents are
missing.

## `TelemetryRequirement`

Required fields:

- `field_or_proof`
- `purpose`
- `required_for`: capability preflight or scored qualification
- `owner_spec`
- `current_status`: `deferred`

The record must not claim unavailable effective-route, reroute, token,
parentage, or treatment telemetry.

## `ClassifiedUnknown`

Required fields:

- `unknown_id`
- `class`: `documentation`, `inventory`, `executable_capability`, or
  `scored_qualification`
- `question`
- `impact`
- `owner_spec`
- `required_follow_up`
- `status`

G56R-001 must close documentation and inventory unknowns needed for its own
completion. `executable_capability` belongs to G56R-002;
`scored_qualification` belongs to G56R-003. An unclassified unknown is invalid
and forces no-go.

## `HandoffDecision`

Required fields:

- `decision`: `go` or `no_go`
- `started_at`
- `stopped_at`
- `completed_artifacts`
- `completion_checks`
- `unmet_conditions`

`CompletionCheck` contains `gate_id`, requirement references, objective
condition, status, and evidence IDs. The checks cover artifact presence,
12/10/2 coverage, contracts, candidates, provenance, Markdown/JSON agreement,
fixtures, telemetry requirements, classified unknowns, sanitization, and
conflict disposition.

For `go`, every check passes, `unmet_conditions` is empty, and no blocking
conflict or unclassified unknown exists.

For `no_go`, every `UnmetCondition` contains:

- `gate_id`
- `requirement_refs`
- `condition`
- `available_evidence_ids`
- `impact`
- `owner_spec`
- `required_follow_up`

The recorded stop time is terminal; no-go does not authorize more time, smaller
deliverables, probing, scoring, mutation, or defect repair.

## Cross-artifact agreement projection

The checker compares normalized Markdown and JSON values for:

- all twelve agent names;
- contract IDs and both hashes;
- production route or explicit absence;
- model/effort/treatment tuples and candidate IDs;
- project eligibility and unresolved installed availability;
- capability requirements, rationale, incompatibilities, and qualification;
- provenance, surface applicability, and invalidation triggers;
- fixture status/contracts, telemetry requirements, and classified unknowns;
- completion checks and terminal handoff state.

Missing values fail. Empty arrays and permitted nulls are explicit values, not
omissions.
