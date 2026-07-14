# Contract: Agent Route Candidate Manifest v1

## Purpose

This is the review-visible contract for
`docs/ai/research/codex-agent-route-candidate-manifest.json`. It defines a
research handoff, not an executable route configuration, installer input,
qualification result, or fallback policy.

## Envelope

The root JSON object requires:

| Field | Contract |
|---|---|
| `manifest_type` | Literal `agent_route_candidate_manifest` |
| `manifest_version` | Integer `1` |
| `research_date` | ISO date `YYYY-MM-DD` |
| `agents` | Exactly twelve self-contained agent records |
| `handoff` | One reproducible `go` or `no_go` decision |

The manifest is UTF-8 without BOM. Root-level normalized contract, route,
candidate, or evidence lookup tables are prohibited.

## Exact agent set and route states

The `agents` array contains each name exactly once:

```text
analyze-executor
autopilot-fast-helper
checklist-executor
clarify-executor
codebase-analyst
consensus-synthesizer
domain-researcher
gate-validator
implement-executor
phase-executor
spec-context-analyst
uat-runbook-author
```

Exactly ten `production_route.status` values are `present`. Only
`consensus-synthesizer` and `gate-validator` are `absent`; their route bindings
are null and their cited `absence_reason` is non-empty.

## Agent record

Each record requires:

```text
agent_name
agent_contract
production_route
candidates
source_observations
surface_records
fixture_contract
telemetry_requirements
classified_unknowns
provenance
invalidation_triggers
```

`agent_contract` requires IDs and hashes plus every semantic field:

```text
agent_contract_id
instruction_hash
contract_hash
role_boundary
authorization_boundaries
safety_requirements
grounding_requirements
mutation_policy
tool_requirements
skill_requirements
mcp_requirements
sandbox_expectations
output_contract
supported_client_assumptions
representative_tasks
```

`production_route` requires:

```text
status
candidate_route_id
model_id
reasoning_effort
instruction_hash
contract_hash
absence_reason
provenance
invalidation_triggers
```

Every candidate requires:

```text
candidate_route_id
agent_contract_id
model_id
reasoning_effort
treatment
instruction_hash
contract_hash
project_eligibility
installation_availability
capability_requirements
rationale
known_incompatibilities
qualification_requirements
provenance
invalidation_triggers
```

Capability requirements independently cover model, modalities, effort, custom
agents, tools, skills, MCP, sandbox, mutation, and clients. Rationale contains
classification, summary, and evidence IDs. Each incompatibility contains the
affected contract field, description, evidence IDs, and eligibility effect.
Use an explicit empty list when no incompatibility exists. Qualification is
`unqualified` or `not_applicable_excluded` and names required capability
checks, fixture, artifacts, telemetry, and owner.

`installation_availability.status` is always `unresolved_g56r_002`. It never
changes `project_eligibility`.

## Identity and hashing

- Contract ID: `agent-contract/<agent-name>/v<N>`
- Candidate ID:
  `candidate-route/<agent-name>/<model-slug>/<effort-slug>/<treatment-slug>/v<N>`
- Hash: lowercase `sha256:<64-hex>`

IDs do not encode rank and are not reused after canonical content or the bound
route tuple changes. `treatment-slug` is `unchanged` or an evidence-justified
variant.

Normalize strings to Unicode NFC and CRLF/CR to LF, preserve all other
whitespace, and encode UTF-8 without BOM. `instruction_hash` covers the complete
decoded instruction body only. `contract_hash` covers `agent_name` and the
twelve semantic fields using recursively normalized strings and Python JSON
serialization with `ensure_ascii=False`, sorted keys, compact separators, and
`allow_nan=False`.

## Evidence and surfaces

Every agent records independent `tracked_source`, `cached_source`, and
`installed_state` observations. Common retained values are limited to evidence
class, agent name, relevant model/effort, instruction/contract hashes,
observation date, surface, and known version. Tracked source adds a
repository-relative path, revision, and evidence role. Cache/installed records
use logical locators only.

Absolute/home paths, usernames, hostnames, credentials, secrets, and unrelated
configuration are prohibited.

Platform provenance uses only official OpenAI sources and requires URL, exact
locator, retrieval date, surface, feature, documented scope (`not_stated` when
omitted), applicability, conflict status, and invalidation triggers. Project
provenance requires repository-relative path, revision, and evidence role.

Surface values are `cli`, `desktop_app`, `app_server`, and `non_interactive`.
Records are independent; silence is `undocumented`, and `not_applicable`
requires explicit official evidence.

## Candidate and policy bounds

- Include every evidence-supported eligible project candidate, including the
  immutable production baseline.
- Exclusion requires cited incompatibility, hard-contract failure, or
  applicable predeclared dominance evidence.
- Local unavailability is not an exclusion.
- A treatment variant requires a bounded evidence-backed hypothesis and a
  matching unchanged control.
- Candidates never claim executable, qualified, preferred, or ordered fallback
status.
- Lexical ID ordering is presentation only.

## Fixture contract

Each agent requires fixture status, nullable repository-relative path,
representative task, input type, expected behavior, expected output shape, and
hard-contract assertions. Exactly `codebase-analyst`, `domain-researcher`, and
`spec-context-analyst` are current; the other nine are missing. Historical
prompt-emulation evidence is `non_release_evidence`.

## Unknowns and handoff

Every unknown records class, question, impact, owner spec, required follow-up,
and status. G56R-002 owns executable capability/availability; G56R-003 owns
fixture execution, replay, scoring, qualification, and route ordering. An
unclassified unknown is invalid.

`handoff` requires `decision`, `started_at`, `stopped_at`,
`completed_artifacts`, `completion_checks`, and `unmet_conditions`. `go`
requires every check to pass, an empty unmet list, no blocking conflict, and no
unclassified unknown.

For `no_go`, every unmet condition requires:

```text
gate_id
requirement_refs
condition
available_evidence_ids
impact
owner_spec
required_follow_up
```

The workday stop time is terminal. `no_go` does not authorize extended work,
reduced deliverables, probing, scoring, mutation, or defect repair.

## Checker contract

`specs/g56r-001-candidate-route-baseline/check-artifacts.py` is a fixed-path,
offline, read-only Python 3.11+ check. It fails on an invalid envelope/version,
wrong 12/10/2 inventory, missing/duplicate IDs, invalid or non-repeatable
hashes, incomplete fields/evidence/surfaces/fixtures/unknowns, sanitization
violations, eligibility/availability conflation, unsupported qualification or
ordering claims, Markdown/JSON disagreement, or an unreproducible handoff.

It performs no network access, runtime probing, scoring, qualification,
mutation, or generic schema service.
