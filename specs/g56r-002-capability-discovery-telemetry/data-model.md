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

## Owning-ID Uniqueness

Every owning collection rejects duplicate identity keys even when the duplicate
objects differ: source-refresh ledger ID; surface-observation ID and
`(client_identity_id, surface)` key; tuple-decision candidate-route/model/effort
key; telemetry `(client_identity_id, surface, field_path)` key;
route-resolution ID; controlled-environment binding ID; reroute event ID;
execution-trace ID; and fixture path in the digest manifest. Repeated foreign
key references to one valid owner remain allowed. A collision fails before any
join or disposition is evaluated.

## Source and Surface Records

### `OfficialSourceRefresh`

| Field | Type | Rule |
|---|---|---|
| `official_source_ledger_id` | string | One of exactly 22 current `OPENAI-DOC-*` records; never `OSL-*` |
| `requested_url` / `canonical_url` | string | Canonical URL must remain in the approved OpenAI domain allowlist |
| `retrieved_at` | timestamp | Required per refresh |
| `body_digest` | digest or null | Null only when retrieval did not yield a body |
| `status` | enum | `confirmed_current`, `changed`, `redirected`, `inaccessible`, `withdrawn`, or `conflicting` |
| `bounded_extracts` | array | Exact visible-text extracts with SHA-256 and normalization contract |
| `retrieval_evidence_digest` | digest | Binds canonical URL, retrieval time, body digest, and bounded extracts |
| `documented_facts` | array | Bounded field-level claims supported by the refreshed source |
| `claim_bindings` | array | Current claim/route IDs affected by this record |
| `invalidated_claim_ids` | array | Subset of bindings invalidated by this outcome |
| `prior_record_digest` | digest | Binds the G56R-001 input without rewriting it |

Invariant: an adverse refresh invalidates only bound current claims/routes.
Historical `OSL-*` evidence is never copied into this record as current. The
private normalized refresh additionally retains `retrieved_body_b64` so the
adapter can recheck the body and visible-text extracts. The published
`OfficialSourceRefresh` strips that field.

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
| `surface_observation_id` | digest | Content identity of the closed observation payload |
| `client_identity_id` | digest | Must match the matrix |
| `repository_binding` | object | Closed revision/tree object, tree digest, and `git-object://` evidence binding derived from the active checkout |
| `work_item` | object | Typed `task`, `fixture`, or `objective` ID supplied at collection |
| `surface` | enum | `app_server`, `cli`, or `interactive_picker` |
| `collection_method_id` | enum | Closed registry: `fixture-enumeration-v1` or `unknown-observation-v1` in this slice |
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
Neither registered method can authorize inclusion: fixture enumeration is
synthetic and unknown observation is non-authoritative. The live collection
allowlist is empty in this slice. A live unknown observation's
`raw://sha256:<digest>` reference maps to `<raw_evidence_root>/<digest>.json`;
the collector writes that sanitized attempt record with mode `0600` and
verifies the exact stored bytes before publishing the observation.

### `SurfaceMatrix`

| Field | Type | Rule |
|---|---|---|
| `surface_matrix_id` | digest | Content digest of the aggregate |
| `schema_version` | string | Required and supported |
| `client_identity_id` | digest | Shared by all observations |
| `repository_binding_id` | digest | Shared by all three observation repository bindings |
| `work_item` | object | Shared typed work-item binding |
| `observations` | array | Exactly one observation for each required surface in canonical surface order |
| `normalization_map` | object | Pinned-build aliases backed by an exact raw-label/machine-ID entry on the named authority surface |
| `normalization_map_id` | digest | Content digest of the one-to-one alias map |
| `disagreements` | array | Lossless conflict records |
| `aggregate_integrity_digest` | digest | Covers all canonical observation objects and the normalization-map ID |
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
| `controlled_repository_snapshot` | object | Exact repository-binding ID, revision, tree object/digest, and content-addressed evidence reference derived from the observations |
| `work_item` | object | Exact shared typed work-item binding derived from the observations |
| `models` / `efforts` / `capabilities` | arrays | Surface-keyed observations, never candidate authority |
| `collection_window` | object | Start/end timestamps |
| `raw_evidence_digest` / `raw_evidence_ref` | digest/string | External raw capture binding |
| `source_refresh_set_digest` | digest | Binds all 22 current refresh outcomes |
| `supersedes_snapshot_id` | string or null | Append-only successor chain |

### `CanaryResult`

| Field | Type | Rule |
|---|---|---|
| `snapshot_id` | digest | Runtime snapshot parent |
| `canonical_model_id` / `canonical_effort` | strings | Together with snapshot ID, the one-attempt canary key |
| `attempt_index` | integer | Must be exactly `1` |
| `timeout_seconds` | integer | Must equal `30` |
| `combined_output_cap_bytes` | integer | Must equal `65536` |
| `executor_contract_id` | digest | Approved platform executor contract that enforced output and process-tree bounds |
| `implementation_digest` | digest | Must equal the matching approval record's implementation digest |
| `executor_result_digest` | digest | Exact closed external result-envelope binding, excluding only this digest and the derived availability disposition |
| `contract_version` | string | Must equal `1.0.0` |
| `timeout_enforced` / `output_cap_enforced` | booleans | Both must be true |
| `process_tree_termination_state` | enum | `not_needed`, `completed`, or `failed`; failed remains unknown |
| `retry_count` | integer | Must equal `0` |
| `exit_code` | integer or null | Raw process result |
| `sentinel_observed` | boolean | True only for the predeclared bounded response |
| `terminal_class` | enum | `success`, `timeout`, `output_cap_exceeded`, `launch_error`, `transport_error`, `authentication_error`, `rate_limited`, `malformed_response`, `explicit_rejection`, `service_reroute`, or `ambiguous_error` |
| `availability_disposition` | enum | `available_for_pinned_environment` only for success; otherwise `unknown` |
| `evidence_digest` | digest | Redacted evidence binding |

The module owns a versioned, default-empty allowlist of approved executor
contract IDs. An executor becomes trusted only through a separately reviewed
repository change that binds its implementation and approval-evidence digests;
an executor result cannot self-approve. The repository adapter consumes the
closed result envelope and fails closed as `unknown` when the ID is absent from
the allowlist, any enforcement acknowledgement is missing, or process-tree
termination failed. Its default path never launches a process. A transient
exception creates a successor snapshot and a new key. Canary results never
establish support, effort support, eligibility, quality, preference, or
qualification.

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
| `candidate_freeze_id` | digest | Hash of the complete published payload except this field |
| `schema_version` | string | Required |
| `source_manifest_binding` | object | Canonical G56R-001 manifest schema, snapshot ID, and whole-manifest digest |
| `client_identity` | object | Embedded closed pinned-build identity |
| `client_identity_id` | digest | Required |
| `official_source_refreshes` | array | All 22 sanitized, body-free published refresh outcomes |
| `source_refresh_set_digest` / `current_ledger_digest` | digests | Equal digest over all 22 refresh outcomes |
| `surface_matrix` | object | Embedded validated matrix |
| `surface_matrix_id` / `surface_matrix_digest` | digests | Both equal the embedded matrix ID |
| `tuple_decision_digest` | digest | Complete ordered included/excluded set |
| `tuple_decisions` | array | Complete manifest-backed decision records with runtime snapshot binding |
| `runtime_capability_snapshot` | object | Embedded rebuilt runtime snapshot |
| `runtime_capability_snapshot_id` | digest | Required |
| `telemetry_profile_id` | digest | Required before G56R-003 handoff |
| `included_candidate_route_ids` | array | May be empty; never inferred |
| `excluded_candidates` | array | Every excluded tuple and its explicit reasons |
| `approved_canary_executors` / `canary_results` | arrays | Closed approval and replay-safe result records; both empty in the first freeze |
| `published_at` | timestamp | Required |
| `supersedes_candidate_freeze_id` | string or null | Successor only; prior freeze is immutable |

`candidate_freeze_id` hashes the complete published object except that ID
itself. Validation rebuilds the manifest binding, source refresh, matrix,
runtime snapshot, tuple decisions, derived candidate lists, canary state, and
whole-freeze identity. Any source, build, evidence, normalization, telemetry,
or disposition change must produce a successor ID.

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

### `ControlledEnvironmentBinding`

Required fields: content-addressed binding ID, pinned client identity and
surface, runtime-capability snapshot ID, repository revision and tree digest,
candidate route ID, work-item kind (`task`, `fixture`, or `objective`), and
work-item ID. Every treatment bundle carries a unique
`controlled_environments` owner registry, and each trace references one owner
by ID. The client, snapshot, and candidate route MUST equal the corresponding
treatment and objective fields. A missing owner, duplicate owner, mismatch, or
orphan hard-fails validation; no environment value is inferred from another
record.

### `RouteResolution`

Required fields: `route_resolution_id`, preferred route, ordered attempted
routes, resolver-selected assigned route, supported effective route or typed
unknown, fallback index/reason, capability snapshot, and timestamp. Resolver
fallback occurs before assignment. G56R-002 validates the record shape but does
not define fallback ordering or resolver policy.

### `ServiceRerouteEvent`

Required documented fields: `threadId`, `turnId`, `fromModel`, `toModel`, and
`reason`, plus event ID, pinned surface, and event evidence. It joins to a trace
by `(surface, threadId, turnId)`. It proves no effort or named-agent identity
and never overwrites resolver fields. Ambiguous/conflicting joins hard-fail.

### `RerouteDestinationAssessment`

Required fields: source event ID, destination candidate-route ID, destination
agent-contract ID, destination named agent, assessment, and nullable
prequalification-evidence ID. The raw service event remains unchanged. The
treatment bundle includes a read-only `qualification_evidence_registry` whose
owners bind evidence ID, authority kind, owning spec, destination route,
agent-contract, named agent, status, and digest. Synthetic fixture authority
exercises replay only and can never authorize live continuation. Runtime UAT is
allowed only for a matching `owned_external` record created by its owning later
spec. G56R-002 validates and consumes the slot but never creates or asserts real
qualification evidence. Missing, mismatched, unknown, ambiguous, or
different-agent assessments hard-fail treatment.

### `TreatmentFailure`

Required fields: closed failure code, affected contract field, expected and
observed evidence references (nullable when unavailable), and resulting
treatment disposition. The collection is required even when empty. Free-form
disposition reasons may add context but never replace structured failures.

### `TreatmentTrace`

The trace contains:

- objective six-ID binding;
- controlled-environment binding and equality with the objective/snapshot;
- named agent, assigned/requested route, supported effective evidence, and
  separate raw service-reroute events and destination assessments;
- instruction/configuration hashes, sandbox, approvals, mutation class,
  expected/loaded skills, MCP, and tools;
- parent configuration, pinned client, controlled overrides, delivery canary,
  context, and parent-child graph;
- complete raw token vector when exposed, request/turn count, wall time,
  retries, compaction, validation, cancellation, failed/abandoned work,
  terminal state, outcome, and acceptance;
- one `ObservationValue` per closed telemetry-profile field;
- structured treatment failures for every expected-versus-observed mismatch;
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
`raw_evidence_digest`, and expected disposition. The adjacent behavior-named
`fixture-digests.json` maps each repo-relative fixture path to its SHA-256 over
the exact raw bytes. Keeping that digest out of the hashed file avoids a
self-referential value and lets replay verify bytes before parsing.
Sanitization removes credentials, headers, cookies, prompt/user content,
account IDs, hostnames, absolute paths, and repository remotes, replacing
necessary joins with deterministic fixture-local pseudonyms.

Replay acceptance requires:

1. load the out-of-band digest entry, verify raw fixture bytes, and only then
   parse the fixture;
2. reject undeclared fields and any raw-store or network dependency;
3. cover success, explicit null, unavailable, misdelivery, approved reroute,
   unapproved/unidentifiable reroute, discovery unavailable, and surface
   disagreement;
4. run the complete set twice; and
5. require byte-identical normalized outputs, dispositions, and digests.

Any mismatch fails acceptance. Replay never turns canary evidence into support,
eligibility, scoring, or qualification.
