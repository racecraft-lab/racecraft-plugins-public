# Data Model: Capability-aware Codex Agent Installation

## Route Policy Manifest

**Purpose**: Explicit trusted input that activates route-aware mode.

**Fields**:

- `schema_version`: manifest schema version, exactly `1.0.0` for this slice.
- `manifest_id`: SHA-256 identity recomputed from the canonical manifest document with only `manifest_id` omitted.
- `provenance_id`: identity for the trusted policy provenance record.
- `source_roster`: strict canonical 13-record source inventory containing each filename and original-byte digest plus its recomputed roster identity.
- `required_agent_policies`: exactly 12 records keyed by canonical required agent name.
- `optional_helper`: object containing the `autopilot-fast-helper` policy fields, or an explicit no-helper policy state.
- `bounded_probes`: manifest-admitted probe definitions keyed by candidate/probe ID.

**Validation rules**:

- Manifest must come from a trusted non-symlink regular-file path inside the current repository boundary, not inline JSON.
- Manifest schema must be closed: unknown top-level fields fail validation.
- Source roster records must be in ascending filename order and match the current strict 13 bundled TOML files by name and original-byte digest; the roster identity is recomputed from the canonical records.
- Required roster must contain exactly `analyze-executor`, `artifact-author`, `checklist-executor`, `clarify-executor`, `codebase-analyst`, `domain-researcher`, `implement-executor`, `phase-executor`, `spec-context-analyst`, `sweep-analyst`, `sweep-classifier`, and `uat-runbook-author`.
- Optional helper state must mention only `autopilot-fast-helper`.
- Every route candidate and bounded probe used by resolution must be manifest-admitted.

## Agent Route Policy

**Purpose**: Per-agent route contract supplied by the manifest.

**Fields**:

- `policy_id`: stable policy identity.
- `agent_name`: required agent or optional helper name.
- `preferred_route`: explicit model and effort tuple plus required capabilities.
- `fallback_routes`: ordered explicit model and effort tuples plus required capabilities.
- `non_route_contract_digest`: digest of instructions, tools, skills, MCP bindings, sandbox, mutation policy, and output contract expected to remain invariant.
- `no_helper`: optional-helper-only record proving validated no-helper continuation.

**Validation rules**:

- Model and effort are required. They are never inferred from bundled TOML defaults, parent config, or adjacent routes.
- Fallback order is honored only in normal mode.
- Required-agent strict override replaces the route list with exactly one override-derived tuple preserving agent effort and non-route contract.

## Runtime Capability Snapshot

**Purpose**: One fresh batch observation used by all route decisions.

**Fields**:

- `snapshot_id`: identity for this invocation's observation.
- `observed_at`: deterministic timestamp or fixture identity in tests.
- `adapter_id`: runner-owned observation adapter identity.
- `models`: model availability and supported effort/capability facts.
- `child_probe_results`: bounded probe outcomes keyed by probe ID.

**Validation rules**:

- Exactly one snapshot is captured per route-aware invocation.
- Every required-agent and helper decision cites the same `snapshot_id`.
- Probe results are child evidence of the snapshot and cannot widen the manifest-admitted candidate set.

## Route Resolution Record

**Purpose**: Per-agent decision trail.

**Fields**:

- `agent_name`
- `route_resolution_id`
- `policy_id`
- `snapshot_id`
- `attempted_routes`
- `rejection_reasons`
- `selected_route`
- `terminal_outcome`

**Validation rules**:

- Required agents appear in stable canonical roster order.
- Normal mode attempts preferred route then ordered fallbacks.
- Strict override attempts exactly one override-derived tuple per required agent.
- A required miss still leaves complete records for all 12 required agents.

## Resolved Agent Policy Record

**Purpose**: Identity for exact destination content selected after route resolution.

**Fields**:

- `resolved_agent_policy_id`
- `agent_name`
- `selected_route`
- `materialization_id`
- `materialization_proof`
- `destination_digest`
- `non_route_contract_digest`

**Validation rules**:

- Exists only for successfully resolved agents.
- Binds one selected route to one materialization proof.
- Cannot claim route qualification beyond manifest-admitted compatibility.

## Materialization Proof

**Purpose**: Byte-level proof that destination TOML was rendered from source TOML without non-route drift.

**Fields**:

- `materialization_id`
- `source_path`
- `source_bytes_digest`
- `destination_bytes_digest`
- `selected_model`
- `selected_model_reasoning_effort`
- `non_route_fields_unchanged`
- `materializer_binding`

**Validation rules**:

- Source bytes are the original bundled TOML bytes.
- Destination bytes render only the selected explicit model and effort route.
- Non-route fields must match exactly after structured TOML parsing.

## Optional Helper Decision

**Purpose**: Batch-level decision for `autopilot-fast-helper`.

**Fields**:

- `decision_id`
- `helper_name`
- `outcome`: `installed`, `omitted`, `removed`, `preserved`, or `unresolved`
- `policy_id`
- `route_resolution_id`
- `resolved_agent_policy_id`
- `materialization_id`
- `materialization_proof`
- `snapshot_id`
- `attempted_routes`
- `rejection_reasons`
- `terminal_outcome`
- `selected_route`
- `no_helper_validation`
- `managed_ownership_proof`
- `manual_remediation`

**Validation rules**:

- Helper absence does not fail the required roster when no-helper continuation validates.
- Existing helper removal requires trusted provenance or exact known rendered-byte digest match.
- Same filename, syntactic TOML validity, parsed equivalence, or normalized content never prove ownership.

## Recovery Record

**Purpose**: Mutation and rollback evidence.

**Fields**:

- `pre_state_id`
- `final_state_id`
- `planned_writes`
- `planned_removals`
- `staged_actions`
- `applied_actions`
- `rolled_back_actions`
- `cleanup_actions`
- `cleanup_errors`
- `failed_actions`
- `rollback_outcome`
- `writes_state`
- `restart_required`
- `manual_remediation`
- `terminal_outcome`

**Validation rules**:

- Pre-state bytes and file modes are captured for every planned write or managed removal.
- Pre-mutation required-route failures have zero planned/applied writes and removals.
- Successful no-op or successful rollback reports `writes_state=false` and `restart_required=false`.
- Any unrestored mutation reports changed or uncertain state, restart required, and bounded remediation.

## Routing Evidence

**Purpose**: Closed top-level route-aware response object.

**Fields**:

- `schema_version`
- `mode`
- `manifest`
- `runtime_capability_snapshot`
- `required_agents`
- `optional_helper_decision`
- `strict_override`
- `recovery_or_mutation`

**Validation rules**:

- Present only in route-aware mode.
- Static mode omits `routing` and preserves existing mechanical `mutation`, `verification`, `agent_files`, `model`, `source`, `destination`, `writes_state`, and `restart_required` fields.
- Low-level mutation records remain mechanical and do not own policy evidence.
- Each installed required-agent or helper record embeds its materialization proof so the response itself can substantiate the destination-byte claim without a separate report file.

## State Transitions

```text
static_request_without_manifest
  -> load_strict_13_source_inventory
  -> static_render_13_files
  -> dry_run_or_apply_existing_copy_verify
  -> static_response_without_routing

route_aware_request_with_manifest
  -> validate_manifest_and_source_roster
  -> capture_one_snapshot
  -> resolve_all_required_agents
  -> decide_optional_helper
  -> materialize_all_selected_destination_bytes
  -> verify_complete_plan_before_mutation
  -> no_required_miss ? plan_or_apply_batch : zero_write_failure
  -> rollback_on_apply_failure
  -> route_aware_response_with_routing
```
