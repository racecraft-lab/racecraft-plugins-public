# Contract: `install-codex-agents` Route-aware Request and Response

This contract extends the existing `install-codex-agents` mutation helper without changing static no-manifest compatibility.

## Request

Base runner envelope remains unchanged:

```json
{
  "schema_version": "1.0",
  "helper_id": "install-codex-agents",
  "operation": "install-codex-agents",
  "mode": "dry_run",
  "inputs": {}
}
```

Route-aware inputs:

- `destination`: optional. Existing accepted values remain unchanged.
- `route_policy_manifest`: explicit path to a trusted manifest. Presence activates route-aware mode; the implementation resolves it through the runner's safe path boundary before reading.
- `strict_model_override`: optional string model override for the entire required roster.

Static inputs:

- `destination`: optional.
- `model`: optional static model value currently supported by the installer.

Static requests must not include `routing` in the response and must not perform route discovery or strict override validation.

## Route-aware Success Response

The response keeps the existing helper envelope and mechanical fields. It adds `data.routing` only in route-aware mode.

Required `data.routing` fields:

- `schema_version`
- `mode`: `route_aware`
- `manifest`
- `runtime_capability_snapshot`
- `required_agents`
- `optional_helper_decision`
- `strict_override`
- `recovery_or_mutation`

`manifest` fields:

- `path`
- `manifest_id`
- `schema_version`
- `source_roster_id`
- `provenance_id`

`runtime_capability_snapshot` fields:

- `snapshot_id`
- `adapter_id`
- `observation_evidence`
- `child_probe_results`

Each `required_agents` record fields:

- `agent_name`
- `route_resolution_id`
- `policy_id`
- `resolved_agent_policy_id`
- `materialization_id`
- `materialization_proof`
- `snapshot_id`
- `attempted_routes`
- `rejection_reasons`
- `selected_route`
- `terminal_outcome`

`optional_helper_decision` fields:

- `helper_name`
- `outcome`
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

`strict_override` fields:

- `requested`
- `status`: `absent`, `compatible`, or `incompatible`
- `model`
- `evaluated_tuples`
- `required_agents_evaluated`
- `helper_evaluated`
- `fallback_suppressed`

`recovery_or_mutation` fields:

- `planned_writes`
- `planned_removals`
- `applied_writes`
- `applied_removals`
- `recovery_record`
- `writes_state`
- `restart_required`

## Static Compatibility Response

When no `route_policy_manifest` input is supplied:

- `data.routing` is absent.
- Current static 13-file destination copy/verify behavior is preserved.
- Existing fields remain: `agent_files`, selected static `model`, `source`, `destination`, `writes_state`, `mutation`, `verification`, and `restart_required`.
- No capability snapshot, route policy evaluation, optional-helper omission, or strict override validation runs.

## Failure Outcomes

Required-agent miss:

- Complete read-only diagnostics for all 12 required agents.
- Zero planned writes.
- Zero planned removals.
- Zero applied writes.
- Zero applied removals.
- `writes_state=false`.
- `restart_required=false`.
- No preferred/fallback route after a strict override miss.

Helper unavailable:

- If required roster resolves and no-helper continuation validates, install proceeds without helper.
- If an existing helper is plugin-managed, managed removal can be planned/applied.
- If an existing helper lacks ownership proof, it is preserved with manual remediation.
- If no-helper continuation does not validate, the batch fails before mutation.

Apply failure after mutation begins:

- Capture prior bytes and file modes before each planned write or managed removal.
- Attempt rollback for every applied action.
- Successful rollback reports `rollback_outcome=restored`, `writes_state=false`, and `restart_required=false`.
- Failed or uncertain rollback reports every unrestored action, sets `writes_state` true or uncertain, sets `restart_required=true`, and includes manual remediation.

Fake-home acceptance uses a temporary HOME/USERPROFILE or a temporary repository's existing `.codex/agents` destination boundary. It does not add a test-only `fake_home` input to `install-codex-agents` and never writes the operator's real home.
