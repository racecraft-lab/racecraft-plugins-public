# Contract: Route Policy Manifest

Route-aware `install-codex-agents` requests activate only when `inputs.route_policy_manifest` points to a trusted manifest document matching this contract. Inline policy objects and inferred bundled defaults do not activate route-aware mode.

## Top-level Object

Required keys:

- `schema_version`: must be `1.0.0`; every other value fails closed.
- `manifest_id`: `sha256:<64 lowercase hex>` identity recomputed from the canonical UTF-8 JSON document with only `manifest_id` omitted.
- `provenance_id`: non-empty identity for the trusted policy provenance represented by the manifest path; it is evidence, not a substitute for path and content validation.
- `source_roster`: object.
- `required_agent_policies`: object with exactly 12 keys.
- `optional_helper`: object.
- `bounded_probes`: object.

Unknown top-level keys are invalid.

## `source_roster`

Required keys:

- `schema_version`: must be `1.0.0`.
- `source_roster_id`: `sha256:<64 lowercase hex>` recomputed from the canonical `files` array.
- `files`: array in ascending filename order containing exactly 13 closed records with `name` and `sha256` fields; each `sha256` is the digest of that original bundled TOML's bytes.

Canonical JSON uses UTF-8, sorted object keys, compact separators, no ASCII escaping, and no NaN values, matching the runner's existing canonical-byte contract.

`files` must contain exactly the 13 bundled source TOML names:

- `analyze-executor.toml`
- `artifact-author.toml`
- `autopilot-fast-helper.toml`
- `checklist-executor.toml`
- `clarify-executor.toml`
- `codebase-analyst.toml`
- `domain-researcher.toml`
- `implement-executor.toml`
- `phase-executor.toml`
- `spec-context-analyst.toml`
- `sweep-analyst.toml`
- `sweep-classifier.toml`
- `uat-runbook-author.toml`

## `required_agent_policies`

The object must contain exactly these keys:

- `analyze-executor`
- `artifact-author`
- `checklist-executor`
- `clarify-executor`
- `codebase-analyst`
- `domain-researcher`
- `implement-executor`
- `phase-executor`
- `spec-context-analyst`
- `sweep-analyst`
- `sweep-classifier`
- `uat-runbook-author`

Each policy requires:

- `policy_id`
- `agent_name`
- `preferred_route`
- `fallback_routes`
- `required_capabilities`
- `non_route_contract_digest`

Each route requires:

- `route_id`
- `model`
- `model_reasoning_effort`
- `capabilities`
- `probe_id` or `probe_id: null`

Routes must be explicit. Missing model or effort is invalid.

## `optional_helper`

Required keys:

- `helper_name`: must be `autopilot-fast-helper`.
- `policy_id`: string or null when explicit no-helper-only state is used.
- `preferred_route`: route object or null.
- `fallback_routes`: array.
- `no_helper`: object proving whether no-helper continuation is valid.

The helper is optional only in destination planning. The source TOML remains mandatory in `source_roster`.

## `bounded_probes`

Each probe record requires:

- `probe_id`
- `candidate_route_id`
- `purpose`
- `bounds`
- `expected_result_shape`

Only probes listed here can run when native discovery is unavailable. Probe results are child evidence of the one runtime capability snapshot; they never add candidates.

## Invalid Manifest Outcomes

A manifest is invalid when it is missing, unreadable, malformed, unsupported, has unknown top-level fields, fails source-roster digest binding, omits or adds required-agent policies, omits explicit helper/no-helper state, or references unadmitted candidates or probes.

Invalid manifests fail route-aware activation before mutation and before capability discovery. Static compatibility is available only when no route-policy manifest input is supplied, not when a supplied manifest is invalid.

The manifest reader must use the existing runner trusted-file boundary: the resolved path must remain inside the current repository root and open as a non-symlink regular file. A path outside that boundary is invalid even when its JSON content is otherwise valid.
