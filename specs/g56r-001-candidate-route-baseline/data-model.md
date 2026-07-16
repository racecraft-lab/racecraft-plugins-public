# Data Model: G56R-001 Candidate Route Baseline

This model defines planning-time record shapes for the canonical Markdown
report and its schema-v2 planning companion. The shared JSON Schema validates
the evidence package; neither the schema nor manifest is runtime configuration,
a generated payload, or an installer input.

## Machine Companion

- Manifest: `docs/ai/research/codex-agent-route-candidate-manifest.json`
- Schema: `docs/ai/research/agent-route-candidate-manifest.schema.json`
- Contract: `docs/ai/specs/agent-routing-parity-contract.md`
- Current platform: `codex`
- Current schema version: `2.0.0`

The manifest maps these record shapes into the same top-level and record-level
structure used by CAR-001. Platform differences are values and explicit
statuses, not schema differences.

## Authority Classes

| Class | Meaning |
|---|---|
| `official_documentation` | Current official OpenAI documentation that can establish platform facts. |
| `project_input` | Repository files, payloads, caches, fixtures, roadmaps, PRD text, or Claude definitions used only to describe project state or role intent. |
| `runtime_verification_needed` | A fact that must be discovered by G56R-002 before use. |
| `qualification_needed` | A candidate behavior that must be evaluated by G56R-003 or later. |
| `undocumented` | A missing, conflicting, withdrawn, or unsupported platform fact that cannot admit a candidate. |

## OfficialSourceLedgerRecord

Fields:

- `official_source_ledger_id`
- `source_family`
- `retrieval_method`
- `requested_url`
- `canonical_url`
- `direct_url`
- `retrieval_date`
- `retrieval_timestamp_utc`
- `http_status`
- `response_body_bytes`
- `response_body_sha256`
- `page_or_surface`
- `page_or_section_title`
- `access_status`
- `conflict_status`
- `documented_facts`
- `supported_surfaces`
- `documented_models`
- `documented_efforts`
- `documented_defaults`
- `conflicts_or_gaps`
- `source_fact_extracts`
- `source_fact_extract_sha256`
- `source_fact_extract_normalization`
- `claim_bindings`
- `invalidation_triggers`

Validation rules:

- IDs are unique.
- Every platform claim binds at least one ledger record.
- Every source fact used for candidate admission has a bounded normalized
  official-documentation extract and SHA-256 hash.
- Repository files cannot populate platform facts.
- Changed, redirected, inaccessible, withdrawn, or conflicting source material
  is recorded as an invalidation trigger.

## AgentContractRecord

Fields:

- `agent_contract_id`
- `role`
- `source_file`
- `source_class`
- `client_surface`
- `production_route_status`
- `declared_toml_model`
- `declared_toml_model_reasoning_effort`
- `declared_toml_sandbox_mode`
- `declared_toml_mutation_intent`
- `instruction_sha256`
- `full_file_sha256`
- `hash_source`
- `instruction_hash_extraction_rule`
- `instruction_hash_encoding`
- `hash_validation_status`
- `role_boundary`
- `safety_contract`
- `grounding_contract`
- `mutation_contract`
- `tool_contract`
- `skill_contract`
- `mcp_contract`
- `source_config_bindings`
- `output_contract`
- `representative_future_task`
- `effective_runtime_permissions`
- `effective_parent_overrides`
- `effective_sandbox_and_approval_policy`
- `exact_treatment_boundary`
- `platform_divergence`

Validation rules:

- Exactly twelve records exist.
- Ten records have `production_route_status=active_codex_toml`.
- Two records have `production_route_status=parity_only_absent`.
- Effective runtime fields are `runtime_verification_needed` in G56R-001.
- Claude parity-role metadata is always `project_input`.
- Instruction and full-file hashes are recomputed for all twelve records with
  documented extraction and encoding rules, and every record has
  `hash_validation_status=pass`.

## ProjectInputRecord

Fields:

- `project_input_id`
- `path_or_surface`
- `source_class`
- `use`
- `candidate_authority`

Validation rules:

- Every active route-policy project, skill, runner, payload, cache, fixture, or
  parity source surface included in AC-1.1 has one stable record.
- `candidate_authority` is always false in G56R-001.
- Project input records can define project state but cannot establish platform
  facts.

## CandidateRouteRecord

Fields:

- `candidate_route_id`
- `agent_contract_id`
- `role_instruction_sha256`
- `official_source_ledger_ids`
- `model`
- `model_reasoning_effort`
- `effort_surface_records`
- `effort_surface_record_ids`
- `role_contract_binding`
- `required_capabilities`
- `unsupported_facts`
- `candidate_status`
- `candidate_rationale`
- `source_fact_id`
- `source_fact_locator`
- `short_excerpt_anchor`
- `source_fact_extract`
- `source_fact_extract_sha256`
- `source_fact_extract_normalization`
- `required_qualification_artifacts`
- `lifecycle_state`
- `shutdown_date`
- `replacement_model`
- `capability_questions`
- `invalidation_rules`

Validation rules:

- Every source-bound candidate record binds one role contract and official
  source support.
- Every source-bound candidate record records the `instruction_sha256` of its bound role
  contract so instruction changes trigger rediscovery.
- Every source-bound candidate record binds a source fact with a bounded
  normalized official-documentation extract and extract hash.
- Every source-bound candidate record binds required qualification artifacts:
  role-specific fixture backlog ID, `runtime_capability_snapshot_id`,
  `telemetry_profile_id`, `route_resolution_id`, `execution_trace_id`, and
  `experiment_policy_id` with scorer contract.
- Unsupported, deprecated, withdrawn, or undocumented facts block admission.
- No record claims availability, executability, qualification, preference,
  efficiency, fallback behavior, or exact treatment.
- Candidate status is one of `admitted_for_discovery`,
  `rejected_undocumented`, `rejected_undocumented_lifecycle_detail`,
  `rejected_undocumented_for_current_codex_route`,
  `rejected_deprecated_or_withdrawn`, or `blocked_pending_capability`.
- Source-bound and admitted records have a rationale that binds an exact source fact to a
  role-contract need and names remaining incompatibilities or gaps.
- G56R-002 may add a role/model binding only for a model already present in the
  G56R-001 official-source ledger, and only when the binding records
  role-contract rationale or explicit exclusion evidence before G56R-003 freezes
  the executable candidate set.

## EffortSurfaceRecord

Fields:

- `effort_surface_record_id`
- `surface`
- `source_ledger_id`
- `setting_or_field`
- `documented_values`
- `documented_default`
- `default_scope`
- `runtime_supported_effort_required`
- `claim_status`

Validation rules:

- Effort and default claims are scoped to the documented surface.
- Documented values and defaults are either exact source-scoped values or an
  explicit undocumented/runtime-only classification.
- Absence on one surface cannot be filled from another surface unless the
  official source explicitly links them.

## FixtureBacklogRecord

Fields:

- `fixture_backlog_id`
- `agent_contract_id`
- `role`
- `current_status`
- `current_source_path`
- `non_release_evidence`
- `executable_specification`
- `representative_input`
- `telemetry_requirements`
- `success_oracle`
- `blocking_dependency`
- `owner_spec`
- `priority`
- `invalidation_triggers`
- `no_payload_created_in_g56r_001`

Validation rules:

- Exactly twelve records exist.
- Exactly three records are current Codex prompt-emulation fixtures.
- Exactly nine records are missing executable fixtures.
- Prompt-emulation records are `non_release_evidence=true`.
- No fixture payload is created or executed in G56R-001.

## TraceabilityRecord

Fields:

- `traceability_id`
- `claim`
- `claim_location`
- `authority_class`
- `source_binding`
- `dependent_records`
- `verification_status`
- `invalidation_trigger`

Validation rules:

- Every platform claim maps to `official_documentation` or `undocumented`.
- Every repository-derived claim maps to `project_input`.
- Every deferred runtime claim maps to `runtime_verification_needed`.
- Every deferred scoring or ranking claim maps to `qualification_needed`.

## GoNoGoDecision

Fields:

- `decision_id`
- `decision_area`
- `decision`
- `required_evidence`
- `evidence_status`
- `blocked_downstream_work`
- `handoff_owner`

Validation rules:

- G56R-002 capability discovery is `GO` only if source, contract, candidate,
  fixture, telemetry, capability-question, and invalidation records are
  complete.
- Route qualification, installation, resolver behavior, and fallback policy are
  `NO-GO` in G56R-001.

## Relationships

- `CandidateRouteRecord.agent_contract_id` references
  `AgentContractRecord.agent_contract_id`.
- `CandidateRouteRecord.official_source_ledger_ids` references
  `OfficialSourceLedgerRecord.official_source_ledger_id`.
- `EffortSurfaceRecord.source_ledger_id` references
  `OfficialSourceLedgerRecord.official_source_ledger_id`.
- `FixtureBacklogRecord.agent_contract_id` references
  `AgentContractRecord.agent_contract_id`.
- `TraceabilityRecord.source_binding` references the authoritative source for
  each claim.
- `GoNoGoDecision.required_evidence` references completed source, contract,
  candidate, fixture, telemetry, and traceability records.
