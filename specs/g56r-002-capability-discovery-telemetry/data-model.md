# Data Model: G56R-002 Capability and Exact-Treatment Contracts

## Conventions

- IDs are non-empty stable strings and are immutable once published.
- Timestamps are UTC RFC 3339 strings.
- Digests are lowercase `sha256:<64 hex characters>` values over canonical
  UTF-8 JSON unless a field states that it hashes external bytes.
- Canonical JSON uses sorted keys, compact separators, UTF-8, and one terminal
  newline only when the stored artifact contract requires it.
- A typed `value` is distinct from `observation_state`. The string `unknown` is
  never substituted for a missing value.
- Every record carries `schema_version`; successor records reference the prior
  immutable ID instead of editing it.

## Relationship Map

| Record | Required parents | Required children or consumers |
|---|---|---|
| `OfficialSourceRefresh` | G56R-001 current `OPENAI-DOC-*` record | `ExecutableCandidateTuple`, `CandidateFreeze` |
| `ClientIdentity` | Pinned client/package bytes | `SurfaceObservation`, `TelemetryProfileEntry`, `TreatmentTrace` |
| `SurfaceMatrix` | One `ClientIdentity`, three surface observations | `RuntimeCapabilitySnapshot`, `Disagreement`, `CandidateFreeze` |
| `RuntimeCapabilitySnapshot` | Matrix and raw-evidence digest/reference | `ExecutableCandidateTuple`, `RouteResolution`, objective join |
| `CandidateFreeze` | Current-ledger digest, matrix digest, all tuple decisions | G56R-003 handoff |
| `TelemetryProfile` | Client identity and surface-keyed field entries | `ConfiguredRouteProof`, `TreatmentTrace` |
| `RouteResolution` | Candidate route and capability snapshot | `TreatmentTrace`, objective join |
| `TreatmentTrace` | Six-ID objective join and telemetry profile | Synthetic replay and G56R-003 handoff |

## Source and Surface Records

### `OfficialSourceRefresh`

| Field | Type | Rule |
|---|---|---|
| `official_source_ledger_id` | string | One of exactly 22 current `OPENAI-DOC-*` records; never `OSL-*` |
| `requested_url` / `canonical_url` | string | Canonical URL must remain in the approved OpenAI domain allowlist |
| `retrieved_at` | timestamp | Required per refresh |
| `body_digest` | digest or null | Null only when retrieval did not yield a body |
| `status` | enum | `confirmed_current`, `changed`, `redirected`, `inaccessible`, `withdrawn`, or `conflicting` |
| `documented_facts` | array | Bounded field-level claims supported by the refreshed source |
| `claim_bindings` | array | Current claim/route IDs affected by this record |
| `invalidated_claim_ids` | array | Subset of bindings invalidated by this outcome |
| `prior_record_digest` | digest | Binds the G56R-001 input without rewriting it |

Invariant: an adverse refresh invalidates only bound current claims/routes.
Historical `OSL-*` evidence is never copied into this record as current.

### `ClientIdentity`

| Field | Type | Rule |
|---|---|---|
| `client_identity_id` | digest | Digest of the canonical identity payload |
| `reported_version` | string | Required exact client version |
| `build_identifier_kind` | enum | `vendor_build_id`, `executable_sha256`, or `package_sha256` |
| `build_identifier` | string | Immutable build ID or digest |
| `distribution` | string | Recorded provenance, not a platform claim |

All surface observations in one matrix must reference the same ID.

### `SurfaceObservation`

| Field | Type | Rule |
|---|---|---|
| `surface_observation_id` | string | Stable within the matrix |
| `client_identity_id` | digest | Must match the matrix |
| `surface` | enum | `app_server`, `cli`, or `interactive_picker` |
| `collection_method_id` | string | Versioned predeclared method |
| `method_inputs_digest` | digest | Fixed inputs/configuration |
| `started_at` / `completed_at` | timestamp | Ordered collection window |
| `completeness_state` | enum | `complete`, `partial`, `unavailable`, or `unknown` |
| `visibility_policy` | object or null | Required for picker completeness/hidden omission claims |
| `entries` | array | Raw label, machine ID when exposed, efforts, capabilities, hidden state, and typed fields |
| `raw_evidence_digest` | digest | Digest of the raw capture bytes |
| `raw_evidence_ref` | string | Content-addressed external reference outside Git |
| `sanitized_evidence_digest` | digest or null | Present when a fixture is committed |

App-server observations record initialization, `model/list(includeHidden:
true)`, and provider-capability method outcomes separately. CLI/picker partial or
irreproducible collection is unknown; missing values are not inferred.

### `SurfaceMatrix`

| Field | Type | Rule |
|---|---|---|
| `surface_matrix_id` | digest | Content digest of the aggregate |
| `schema_version` | string | Required and supported |
| `client_identity_id` | digest | Shared by all observations |
| `surface_observation_ids` | object | Exactly one key per required surface |
| `normalization_map_id` | digest | Versioned one-to-one mappings only |
| `normalized_tuples` | array | Canonical model/effort keys plus per-surface evidence |
| `disagreements` | array | Lossless conflict records |
| `aggregate_integrity_digest` | digest | Covers all referenced observation and mapping digests |
| `validity` | enum | `valid` or `invalid` |
| `invalidity_reasons` | array | Closed aggregate-level reasons |

Aggregate invalidity is limited to missing/unsupported matrix version,
unprovable shared client identity, failed aggregate hash, or ambiguous/duplicate
normalization keys that prevent tuple attribution. Other gaps are tuple-local.

### `Disagreement`

Required fields: canonical tuple key (or null when key attribution failed), all
surface raw values and evidence references, proposed normalized key,
`disagreement_class`, and tuple disposition. It never contains a winning value.

## Capability and Freeze Records

### `RuntimeCapabilitySnapshot`

| Field | Type | Rule |
|---|---|---|
| `runtime_capability_snapshot_id` | digest | Stable content-addressed ID |
| `surface_matrix_id` | digest | Required parent |
| `client_identity_id` | digest | Must match matrix |
| `controlled_repository_snapshot` | string | Exact repository revision/tree binding |
| `task_fixture_or_objective_id` | string | Controlled input identity |
| `models` / `efforts` / `capabilities` | arrays | Surface-keyed observations, never candidate authority |
| `collection_window` | object | Start/end timestamps |
| `raw_evidence_digest` / `raw_evidence_ref` | digest/string | External raw capture binding |
| `source_refresh_set_digest` | digest | Binds all 22 current refresh outcomes |
| `supersedes_snapshot_id` | string or null | Append-only successor chain |

### `CanaryResult`

| Field | Type | Rule |
|---|---|---|
| `canary_key` | tuple | Snapshot ID, canonical model ID, canonical effort |
| `attempt_index` | integer | Must be exactly `1` |
| `timeout_seconds` | integer | Must equal `30` |
| `combined_output_cap_bytes` | integer | Must equal `65536` |
| `exit_code` | integer or null | Raw process result |
| `sentinel_observed` | boolean | True only for the predeclared bounded response |
| `terminal_class` | enum | `success`, `timeout`, `output_cap_exceeded`, `launch_error`, `transport_error`, `authentication_error`, `rate_limited`, `malformed_response`, `explicit_rejection`, `service_reroute`, or `ambiguous_error` |
| `availability_disposition` | enum | `available_for_pinned_environment` only for success; otherwise `unknown` |
| `evidence_digest` | digest | Redacted evidence binding |

There is no retry flag. A transient exception creates a successor snapshot and
a new key. Canary results never establish support, effort support, eligibility,
quality, preference, or qualification.

### `ExecutableCandidateTuple`

Required fields: `candidate_route_id`, `agent_contract_id`, canonical named
agent/model/effort, official-source and effort-surface bindings, instruction and
contract hashes, `runtime_capability_snapshot_id`, per-surface evidence,
availability disposition, source-admission decision, hidden state,
normalization/disagreement reference, exact-treatment readiness, and one
`included` or tuple-local `excluded` decision with reasons.

Inclusion requires current source admission, supported effort authority,
supported pinned-environment availability, required-surface agreement under the
hidden visibility rule, and no invalidated bound claim. Runtime discovery may
only narrow this set.

### `CandidateFreeze`

| Field | Type | Rule |
|---|---|---|
| `candidate_freeze_id` | digest | Hash of all identity inputs and tuple decisions |
| `schema_version` | string | Required |
| `client_identity_id` | digest | Required |
| `current_ledger_digest` | digest | All 22 refresh outcomes |
| `surface_matrix_digest` | digest | Required |
| `tuple_decision_digest` | digest | Complete ordered included/excluded set |
| `runtime_capability_snapshot_id` | digest | Required |
| `telemetry_profile_id` | digest | Required before G56R-003 handoff |
| `included_candidate_route_ids` | array | May be empty; never inferred |
| `excluded_candidates` | array | Every considered tuple and explicit reasons |
| `published_at` | timestamp | Required |
| `supersedes_candidate_freeze_id` | string or null | Successor only; prior freeze is immutable |

Any source, build, evidence, normalization, telemetry, or disposition change
must produce a successor ID.

## Telemetry and Treatment Records

### `ObservationValue`

| Field | Type | Rule |
|---|---|---|
| `field_path` | string | Closed inventory path |
| `observation_state` | enum | `observed_value`, `explicit_null`, `missing`, `unavailable`, `not_applicable`, or `undocumented` |
| `value` | typed value or null | Non-null only for `observed_value` unless the documented field itself returns null, which uses `explicit_null` |
| `evidence_ref` | string or null | Required when evidence exists |
| `captured_at` | timestamp or null | Required for an observation |

No state may be coerced to zero, false, a configured value, or the string
`unknown`. Unknown is a resulting knowledge/treatment disposition.

### `TelemetryProfileEntry`

Key: `(client_identity_id, surface, field_path)`.

Required fields: classification (`stable_native`, `experimental_native`,
`derived_from_controlled_configuration`, `conditional`, `unavailable`,
`not_applicable`, or `undocumented`), official source ID or null, documented
predicate, completeness rule, permitted claims, prohibited claims, and
observation-state rules. An omitted key is `undocumented`; classifications do
not inherit across surfaces.

### `ConfiguredRouteProof`

Required fields: proof ID/digest, telemetry-profile approval entry, named agent,
explicit model and effort, candidate route and agent-contract IDs, instruction
and materialized-configuration hashes, client identity, controlled overrides,
launch ID, consumption evidence, and complete-reroute-monitoring binding. It
proves requested/assigned intent only.

### `ObjectiveBinding`

Every assigned objective requires all six non-null IDs:

1. `candidate_route_id`
2. `agent_contract_id`
3. `runtime_capability_snapshot_id`
4. `route_resolution_id`
5. `experiment_policy_id`
6. `execution_trace_id`

Later aggregate IDs remain explicit null until their owning specs create them.

### `RouteResolution`

Required fields: `route_resolution_id`, preferred route, ordered attempted
routes, resolver-selected assigned route, supported effective route or typed
unknown, fallback index/reason, capability snapshot, and timestamp. Resolver
fallback occurs before assignment. G56R-002 validates the record shape but does
not define fallback ordering or resolver policy.

### `ServiceRerouteEvent`

Required documented fields: `threadId`, `turnId`, `fromModel`, `toModel`, and
`reason`, plus pinned surface and event evidence. It joins to a trace by
`(surface, threadId, turnId)`. It proves no effort or named-agent identity and
never overwrites resolver fields. Ambiguous/conflicting joins hard-fail.

### `TreatmentTrace`

The trace contains:

- objective six-ID binding;
- named agent, assigned/requested route, supported effective evidence, and
  separate service-reroute events;
- instruction/configuration hashes, sandbox, approvals, mutation class,
  expected/loaded skills, MCP, and tools;
- parent configuration, pinned client, controlled overrides, delivery canary,
  context, and parent-child graph;
- complete raw token vector when exposed, request/turn count, wall time,
  retries, compaction, validation, cancellation, failed/abandoned work,
  terminal state, outcome, and acceptance;
- one `ObservationValue` per closed telemetry-profile field;
- `treatment_disposition`: `proven`, `unknown`, `non_scorable_rerouted`, or
  `hard_fail` with reasons.

Rules:

- Exact treatment is proven only by supported observed effective treatment or
  approved configured-route proof plus complete reroute monitoring.
- Every service reroute makes the requested route non-scorable.
- Runtime UAT may continue only for an identifiable, prequalified destination
  for the same named agent. Unapproved, unknown, unidentifiable, different-agent,
  or ambiguous reroutes hard-fail.
- Missing evidence is unknown and excludes only the affected tuple/run.

## Fixture Provenance and Replay

Each committed fixture records `schema_version`, `sanitizer_version`,
`raw_evidence_digest`, `fixture_digest`, and expected disposition. Sanitization
removes credentials, headers, cookies, prompt/user content, account IDs,
hostnames, absolute paths, and repository remotes, replacing necessary joins
with deterministic fixture-local pseudonyms.

Replay acceptance requires:

1. verify each fixture digest before parsing;
2. reject undeclared fields and any raw-store or network dependency;
3. cover success, explicit null, unavailable, misdelivery, approved reroute,
   unapproved/unidentifiable reroute, discovery unavailable, and surface
   disagreement;
4. run the complete set twice; and
5. require byte-identical normalized outputs, dispositions, and digests.

Any mismatch fails acceptance. Replay never turns canary evidence into support,
eligibility, scoring, or qualification.
