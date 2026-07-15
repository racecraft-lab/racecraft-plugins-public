# Data Model: G56R-001 Candidate Route Baseline

This model defines planning-time record shapes for the canonical Markdown
report. It is not a runtime schema and does not create a generated manifest.

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
- `direct_url`
- `retrieval_date`
- `page_or_surface`
- `documented_facts`
- `supported_surfaces`
- `documented_models`
- `documented_efforts`
- `documented_defaults`
- `conflicts_or_gaps`
- `claim_bindings`
- `invalidation_triggers`

Validation rules:

- IDs are unique.
- Every platform claim binds at least one ledger record.
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

## CandidateRouteRecord

Fields:

- `candidate_route_id`
- `agent_contract_id`
- `official_source_ledger_ids`
- `model`
- `model_reasoning_effort`
- `effort_surface_records`
- `role_contract_binding`
- `required_capabilities`
- `unsupported_facts`
- `candidate_status`
- `lifecycle_state`
- `shutdown_date`
- `replacement_model`
- `capability_questions`
- `invalidation_rules`

Validation rules:

- Every admitted route binds one role contract and official source support.
- Unsupported, deprecated, withdrawn, or undocumented facts block admission.
- No record claims availability, executability, qualification, preference,
  efficiency, fallback behavior, or exact treatment.
- Candidate status is one of `admitted_for_discovery`,
  `rejected_undocumented`, `rejected_deprecated_or_withdrawn`,
  `blocked_pending_capability`, or `project_input_only`.

## EffortSurfaceRecord

Fields:

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
