# Phase 1 Data Model: CAR-002 Capability Probing, Telemetry Profile, and Exact-Treatment Contract

Four record contracts published as one JSON Schema (draft 2020-12) file with a `$def`
per record type, plus shared primitive `$defs`. `$def` **names** are camelCase; instance
**fields** are snake_case (CAR-001 convention). Every record carries `schema_version`
const `"1.0.0"`. `additionalProperties: false` throughout. The schema draft is in
[contracts/claude-trace-contract.schema.json](./contracts/claude-trace-contract.schema.json);
the shipped file is `docs/ai/research/claude-trace-contract.schema.json`.

Cross-reference IDs are strings reused **verbatim** from the CAR-001 manifest / this
snapshot — never duplicated data that can drift (constitution VI; Architecture Notes).

---

## Shared primitive `$defs`

| `$def` | Shape | Notes |
|--------|-------|-------|
| `sha256` | `string`, `^[0-9a-f]{64}$` | Reused from CAR-001. |
| `nullableString` | `["string","null"]` | Reused from CAR-001. Nulls preserved, never dropped (FR-020). |
| `rawEvidence` | object (below) | CAR-002-specific; distinct from CAR-001 `boundedExtract`. |

**`rawEvidence`** (FR-012/FR-013; Key Entities "Raw probe evidence"):

| Field | Type | Required | Rule |
|-------|------|----------|------|
| `raw_output` | string | yes | The **full** `--output-format json` stdout, sanitized to `<home>`, committed verbatim as a string (not a parsed object). |
| `raw_output_sha256` | `sha256` | yes | SHA-256 over the exact sanitized UTF-8 bytes of `raw_output` (reproducible from committed bytes). |
| `sanitization` | const `"home_paths_normalized_utf8"` | yes | Marks the applied sanitization convention. |

---

## Identity conventions and cross-references

| ID | Form | Owner | Rule |
|----|------|-------|------|
| `runtime_capability_snapshot_id` | `CAR-002-RCS-<YYYY-MM-DD>-V<n>` | this snapshot | Re-probe bumps `V<n>`; git history preserves priors (FR-011). |
| `telemetry_profile_id` | `CAR-002-TP-<YYYY-MM-DD>-V<n>` | telemetry profile | Client version is a recorded field, not part of the ID (FR-018). |
| `tuple_id` | `<model>__<effort>` (lowercase, `__`) | derived | Pure function of manifest `model_selector`/`effort_selector`; null effort → `none` (research R1). Never persisted as a per-route map (FR-004/SC-005). |
| `route_resolution_id` | non-empty unique string | consumers (CAR-003+) | Pattern only; recommended `candidate_route_id`+`snapshot_id`+timestamp/uuid; fixtures use deterministic literals e.g. `CAR-002-RR-FIXTURE-001`. |
| `candidate_route_id` | `CAR-001-CR-<NN>-<NN>` | CAR-001 manifest | Reused verbatim. |
| `agent_contract_id` | `car.<name>.v1` | CAR-001 manifest | Reused verbatim. |
| `execution_trace_id` | non-empty unique string | consumers (optional) | Optional downstream-minted replay identity (AC-2.3). |

The 6 tuple IDs (verified against the committed manifest): `opus__max`, `sonnet__max`,
`fable__max`, `haiku__max`, `haiku__low`, `sonnet__low`.

---

## Record 1 — `runtimeCapabilitySnapshot` (WP1, US1)

The single committed JSON artifact answering CAP-Q1..CAP-Q6. Shipped at
`docs/ai/research/claude-runtime-capability-snapshot.json`.

**Top-level fields**

| Field | Type | Required | Rule / FR |
|-------|------|----------|-----------|
| `schema_version` | const `"1.0.0"` | yes | FR-015. |
| `runtime_capability_snapshot_id` | string | yes | `CAR-002-RCS-<YYYY-MM-DD>-V<n>` (FR-011). |
| `captured_at_utc` | string, date-time | yes | Probe-run timestamp. |
| `pinned_client_version` | string | yes | The one pinned `claude` CLI version this snapshot scopes (Assumptions "Pinned client"). |
| `authentication_mode` | enum `["api_key","subscription"]` | yes | Derived from documented signals (FR-014, research R7). |
| `canary` | object `{ text, canary_sha256 }` | yes | One identical canary across all probes; hash over exact bytes (FR-005, research R8). |
| `tuple_evidence` | array of `tupleEvidence` (below) | yes | One shared evidence set per unique (model, effort) tuple (FR-003/FR-004). |
| `alias_bindings` | array of `aliasBinding` (below) | yes | alias→dated-ID for opus/sonnet/haiku/fable (CAP-Q1, FR-006). |
| `unavailable_observations` | array of `unavailableObservation` (below) | yes | Per-surface unavailable-model results (CAP-Q5, FR-009/FR-010). |
| `models_endpoint_evidence` | `modelsEndpointEvidence` or null | yes (nullable) | API-key-mode corroborating catalog, else a recorded gap (FR-014). |
| `capability_answers` | array of `capabilityAnswer` (below) | yes | CAP-Q1..Q6 answered or explicitly open (FR-007). |
| `open_gaps` | array of `openGap` (below) | yes | Explicit open/gap entries (FR-007/FR-027); empty array allowed. |

**`tupleEvidence`** (the deduplicated probe unit; FR-003/FR-004; Key Entities "(model, effort) tuple")

| Field | Type | Required | Rule |
|-------|------|----------|------|
| `tuple_id` | string | yes | `<model>__<effort>` (research R1). |
| `model_requested` | string | yes | Alias, e.g. `opus`. |
| `effort_requested` | `nullableString` | yes | e.g. `max`; `null` → `tuple_id` segment `none`. |
| `resolved_dated_model_id` | `nullableString` | yes | From the canary `modelUsage` (CAP-Q1..Q4). |
| `effort_acceptance` | enum `["accepted","clamped","rejected","observation_only"]` | yes | Labeled observation, never certification (FR-027, research R6). |
| `effort_probe_output_mode` | enum `["plain_text_print","json_no_org_cap_assumed"]` | yes | Plain-text `--print` avoids silent JSON clamp (research R6). |
| `raw_evidence` | `rawEvidence` | yes | Full sanitized payload + hash (FR-012/FR-013). |

**`aliasBinding`** (CAP-Q1, FR-006): `{ alias: enum[opus,sonnet,haiku,fable], resolved_dated_model_id: nullableString, tuple_id: string, raw_evidence: rawEvidence }`.

**`unavailableObservation`** (CAP-Q5, FR-009/FR-010; two surfaces recorded separately)

| Field | Type | Required | Rule |
|-------|------|----------|------|
| `surface` | enum `["print_model","subagent_frontmatter"]` | yes | `claude -p --model <id>` vs file-agent `@mention` (research R12). |
| `requested_unavailable_model_id` | string | yes | The unavailable ID dispatched. |
| `observed_outcome` | enum `["soft_remap","hard_rejection","silent_fallback","undetermined"]` | yes | Labeled inference; the probe's observation to capture (Assumptions CAP-Q5). |
| `observed_model_id` | `nullableString` | yes | From result `modelUsage`; drives the requested-vs-observed cross-check (research R4). |
| `unset_proof` | `unsetProof` (below) | yes | FR-010 proof from the actual operator environment. |
| `remap_flagged` | boolean | yes | True when `observed_model_id` ≠ requested (interfering-configuration edge case, research R4). |
| `dispatch_equivalence_caveat` | string | yes | States the file-agent-vs-production-Agent-tool inference (Assumptions CAP-Q5). |
| `raw_evidence` | `rawEvidence` | yes | FR-012/FR-013. |

**`unsetProof`** (FR-010, research R13): `{ fallback_model_unset: bool, fallbackModel_unset: bool, claude_code_subagent_model_unset: bool, available_models_absent: bool, enforce_available_models_observed: nullableString, config_dir_isolation: enum["none","partial_defense_in_depth"], inherit_equivalent_to_unset: nullableBool-as-nullableString, org_restriction_gap: nullableString }`. `available_models_absent` means the key is absent, not an empty list; `enforce_available_models_observed` and `org_restriction_gap` are audit/gap records, not gates.

**`capabilityAnswer`** (FR-007): `{ capability_question_id: enum[CAP-Q1..CAP-Q6], status: enum["answered","open"], answer: nullableString, evidence_refs: [tuple_id|surface|...], label: enum["fact","observation","labeled_inference"] }`. CAP-Q6 is `open` with a route-change detection-rule note (research R11).

**`openGap`** (FR-007/FR-027): `{ subject: string, reason: string, disposition: enum["open","unavailable","gap"] }`.

**Snapshot-write dispositions (FR-023; edge case "Partial probe matrix")** — a state rule, not a field:
1. Any observation failing schema validation, or an unparseable `--output-format json`
   payload → **abort the whole snapshot write** (fail-closed; nothing committed).
2. An infrastructure/transport failure with no interpretable platform signal (non-zero exit
   with no parseable error body, timeout, network failure) → **abort the run**, commit
   nothing, and do **not** record "unavailable" (recording transport failure as unavailable
   would falsely narrow platform availability, FR-026).
3. An interpretable platform observation (unavailable-model result, models endpoint
   unreachable in subscription mode, a question unanswerable within the bounded matrix) →
   record as an explicit unavailable/gap/open observation and **write** the snapshot.

---

## Record 2 — `telemetryProfile` (WP2, US2)

Versioned, per-client field classification. Shipped at
`docs/ai/research/claude-telemetry-capability-profile.json`. Validated against this `$def`
(FR-024; SC-006).

| Field | Type | Required | Rule / FR |
|-------|------|----------|-----------|
| `schema_version` | const `"1.0.0"` | yes | FR-015. |
| `telemetry_profile_id` | string | yes | `CAR-002-TP-<YYYY-MM-DD>-V<n>` (Key Entities). |
| `pinned_client_version` | string | yes | The client version the profile describes (FR-018). |
| `runtime_capability_snapshot_id` | string | yes | Cross-ref to the snapshot that grounds observed values. |
| `field_classifications` | array of `fieldClassification` | yes | One entry per telemetry field; SC-006 exactly-one-label. |

**`fieldClassification`** (FR-019/FR-020)

| Field | Type | Required | Rule |
|-------|------|----------|------|
| `field` | string | yes | Dotted telemetry field path, e.g. `usage.input_tokens`, `modelUsage.<model>.costUSD`. |
| `classification` | enum `["stable_native","derived","derived_from_controlled_configuration","unavailable"]` | yes | Exactly one label (SC-006). |
| `observed_value` | `nullableString` | yes | Null preserved when unobserved — distinguishes "unavailable" from "absent" (FR-020). |
| `label` | enum `["fact","observation","labeled_inference"]` | yes | Unconfirmed key spellings labeled `observation` until R3 confirmation runs. |
| `source_ref` | `nullableString` | yes | Canonical doc URL when `fact` (FR-026). |

**Mandated classifications (FR-019)** — at minimum: `stable_native` for
`usage.input_tokens`, `usage.output_tokens`, `usage.cache_read_input_tokens`, the per-TTL
pair `usage.cache_creation.ephemeral_5m_input_tokens` / `ephemeral_1h_input_tokens`, the
flat aggregate `usage.cache_creation_input_tokens` (documented sum of the per-TTL pair —
optional cross-check, not a substitute), `num_turns`, `duration_ms`, and the `modelUsage`
per-model key set with `inputTokens`/`outputTokens`/`cacheReadInputTokens`/
`cacheCreationInputTokens`/`contextWindow`; `derived` for `total_cost_usd`, the
`modelUsage.<model>.costUSD` sub-field, and the effective model (extracted from the
`modelUsage` key set — `SDKResultMessage` has no scalar `model` field);
`derived_from_controlled_configuration` for effective reasoning effort (no documented field
returns it). Any field whose result-message key or availability the canonical docs do not
establish is `unavailable`, labeled `observation` (FR-027). Label crosswalk from CAR-001
`source_class` (Key Entities "Telemetry capability profile").

---

## Record 3 — `routeResolution` (WP2, US3)

The binding needed to resolve one requested route to concrete execution identity. Exercised
in isolation by the WP2 `route-resolution.json` fixture (US3 acceptance scenario 1). Consumers (CAR-003+) mint
these per invocation; CAR-002 fixes the contract.

| Field | Type | Required | Rule / FR |
|-------|------|----------|-----------|
| `schema_version` | const `"1.0.0"` | yes | FR-015. |
| `route_resolution_id` | string | yes | Non-empty unique string (pattern only, Key Entities). |
| `agent_contract_id` | string | yes | Reused verbatim from CAR-001 (FR-021). |
| `candidate_route_id` | string | yes | Reused verbatim from CAR-001 (FR-021). |
| `runtime_capability_snapshot_id` | string | yes | Joins to the committed snapshot (FR-021). |
| `requested_model_alias` | string | yes | e.g. `opus` (FR-021). |
| `resolved_dated_model_id` | string | yes | e.g. `claude-opus-4-8` (FR-021). |
| `effort_level` | `nullableString` | yes | Requested effort (FR-021). |
| `instruction_sha256` | `sha256` | yes | System-prompt/instruction hash (FR-021). |
| `mutation_contract` | string | yes | The route's mutation boundary (FR-021). |
| `client_version` | string | yes | Pinned client version (FR-021). |
| `fast_mode_state` | enum `["on","off","unknown"]` | yes | Fast-mode state (FR-021). |
| `env_override_proof` | `unsetProof` | yes | Env-override proof, reusing the snapshot `unsetProof` shape (FR-021). |
| `fallback_index` | nullable integer | yes | AC-2.3; consumer-populated only when a documented fallback chain fires; always null under CAR-002's unset-proof probes (FR-021, nulls preserved). |
| `fallback_reason` | `nullableString` | yes | AC-2.3; same population rule as `fallback_index` (FR-021). |
| `tuple_id` | string | yes | Derived join key to the snapshot's `tuple_evidence` (FR-004). |

---

## Record 4 — `exactTreatmentReplay` (WP2 contract; WP3 four-class fixtures)

The reproducible-treatment contract CAR-003..CAR-011 consume without re-probing (FR-022).
Carries a complete `routeResolution` binding plus the observed record class and outcome.

| Field | Type | Required | Rule / FR |
|-------|------|----------|-----------|
| `schema_version` | const `"1.0.0"` | yes | FR-015. |
| `route_resolution` | `routeResolution` | yes | Full binding embedded (FR-022/FR-025). |
| `execution_trace_id` | `nullableString` | yes | Optional downstream-minted replay identity (AC-2.3). |
| `record_class` | enum `["success","null","unavailable","misdelivery"]` | yes | The observed record class (research R2). |
| `observed_model_id` | `nullableString` | yes | Delivered model; drives the misdelivery rule. |
| `outcome` | `outcome` object (below) | yes | Observed telemetry/outcome sufficient to replay (FR-022). |
| `scorable` | boolean | yes | False for `unavailable` and `misdelivery`. |

**`outcome`**: `{ status: enum["completed","unavailable","error"], telemetry_ref: nullableString, notes: nullableString }`. Telemetry references the telemetry-profile field set rather than duplicating values. Resolution rule (FR-022): a non-null `telemetry_ref` MUST resolve against the telemetry-profile field set during deterministic validation; a dangling reference fails validation. Class→status mapping (FR-025): `success`/`null`/`misdelivery` ⇒ `completed` (misdelivery is a completed-but-misrouted treatment, non-scorable); `unavailable` ⇒ `unavailable`; `error` is reserved for consumer-recorded execution errors outside the four synthetic classes.

### Record-class rules (FR-025; the four synthetic fixtures, WP3)

| Class | Rule | Cross-ref |
|-------|------|-----------|
| `success` | Fully-populated, scorable record; every binding field present and non-null. | `scorable: true`. |
| `null` | Every **nullable** field present but `null` (not dropped) — proves "unavailable" ≠ "absent" (FR-020). Required non-nullable fields still present. | `scorable: true`. |
| `unavailable` | The record class is unavailable; cross-references the corresponding unavailable observation in the committed snapshot via `runtime_capability_snapshot_id` (FR-021/FR-025). | `scorable: false`. |
| `misdelivery` | `observed_model_id` ≠ `route_resolution.resolved_dated_model_id` → non-scorable for the requested route (mirrors AC-2.3; route-change detection rule, R11). | `scorable: false`. |

---

## Relationships and derived join (SC-005)

```text
CAR-001 manifest (candidate_routes[37])
   │  group by (model_selector.requested_value, effort_selector.requested_value)
   ▼
tuple_id (6)  ──────────────►  runtimeCapabilitySnapshot.tuple_evidence[6]
   ▲                                   │ runtime_capability_snapshot_id
   │ candidate_route_id                ▼
routeResolution ──────────────►  exactTreatmentReplay (embeds routeResolution)
   │ agent_contract_id                 │
   ▼                                   ▼
CAR-001 agent_contracts          telemetryProfile.runtime_capability_snapshot_id
```

The deterministic test (FR-024/SC-005) recomputes the 37-route→tuple join from the committed
CAR-001 manifest against `tuple_evidence`, failing closed if any route resolves to **zero**
or to **more than one** tuple. The join is derived every run — never stored as a
`candidate_route_id`→`tuple_id` map (FR-004/SC-005; constitution VI).

## Validation enforcement (FR-023/FR-024)

- **Write-time (WP1, `claude_capabilities.py`)**: the fail-closed writer validates every
  observation against the schema (via `claude_trace_schema.py`) **before** writing; any
  invalid observation aborts the write (SC-004). Defense-in-depth with the continuous test.
- **Continuous (WP1→WP3, `test-efficiency-claude-telemetry.py`)**: on every CI run validate
  the four record-class fixtures + the standalone route_resolution fixture + the committed
  snapshot + the committed telemetry profile, and compute the 37-route join — all offline,
  zero live model calls (SC-002/SC-003/SC-005/SC-006).
