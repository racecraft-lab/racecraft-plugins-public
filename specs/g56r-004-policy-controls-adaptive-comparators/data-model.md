# Data Model: G56R-004 Policy Controls and Adaptive Comparators

## PolicyControlRegistry

**Purpose**: Content-addressed Codex document that freezes the closed control
set, shared smoke bounds, frozen G56R-003/CAR-003 bindings, and registry digest.

**Fields**: `schema_version`, `registry_id`, `status`, `frozen_at`,
`car_003_bindings`, `controls`, `smoke_bounds`, `registry_digest`.

**Validation rules**:
- `registry_id` is `g56r-004-policy-control-registry`.
- Exactly three `controls` exist.
- `control_kind` values are unique and exactly `unpinned`, `adaptive`, and
  `justified_high_effort`.
- Content address is SHA-256 over canonical JSON with the digest member removed,
  sorted keys, minimal separators, UTF-8, no NaN, and declared array order
  preserved.
- Any fourth control, duplicate kind, missing digest, changed `frozen_at`, or
  frozen-binding mismatch fails closed.

## PolicyControl

**Purpose**: Common envelope for one Codex policy-level alternative.

**Fields**: `control_id`, `control_kind`, `control_digest`, `frozen_at`,
`attribution_level`, `execution_contract`, `evidence_requirements`, plus one
type-specific payload.

**Relationships**: Belongs to one `PolicyControlRegistry`; may produce replay
fixtures and one operator-authorized smoke record.

**Validation rules**:
- `attribution_level` is `policy`.
- Child work is represented inside evidence aggregation, never as a fourth
  policy arm.
- Type-specific payload must match `control_kind`.

## UnpinnedControl

**Purpose**: Single inherited-parent treatment arm.

**Fields**: `arm_count`, `model_resolution`, `pinned_parent_binding`,
`pinned_parent_model`, `pinned_parent_effort`, `authentication_mode`,
`environment_boundary`, `required_absent_overrides`.

**Validation rules**:
- `arm_count` is `1`.
- `model_resolution` is `inherit`.
- Exact treatment is demonstrated only from produced evidence: served model and
  effort equal the pinned parent and local model, effort, provider,
  service-tier, and API-key overrides are observed absent.
- A changed parent context creates a new content address.

## AdaptiveControl

**Purpose**: Frozen ladder and response rule over admitted G56R-003 routes.

**Fields**: `candidate_freeze_id`, `freeze_digest`, `escalation_ladder`,
`escalation_ladder_rationales`, `signal_precedence`,
`failure_code_response`, `failure_plane_response`,
`retry_count_response`, `budget_triggers`, `terminal_state_response`,
`max_escalations_per_objective`, `clean_pass_definition`,
`clean_pass_accounting`, `de_escalation_clean_pass_threshold`,
`de_escalation_timing`.

**State transitions**:
- `hold`: retain current ladder position.
- `escalate`: move to the next higher declared ladder entry, at most once per
  objective; ceiling records no step.
- `non_scorable`: consume no escalation allowance, change no ladder position,
  and neither advance nor reset the clean-pass streak.
- `de_escalate`: between objectives only after exactly three consecutive clean
  passes; floor records no step.

**Validation rules**:
- Ladder entries are ordered, hash-relevant, unique admitted
  `candidate_route_id` values from the bound successor freeze.
- Within one model, effort order follows `low -> medium -> high -> xhigh ->
  max`; cross-model steps carry non-empty rationale.
- Signal precedence is `failure_code`, `failure_plane`, `retry_count`,
  `budget_threshold`, `terminal_state`.
- Response maps are total and single-valued over `escalate`, `hold`, and
  `non_scorable`.
- `service_reroute` makes the whole parent-plus-children unit non-scorable.

## JustifiedHighEffortControl

**Purpose**: Single already-qualified high-effort treatment with executable
eligibility.

**Fields**: `route_id`, `model`, `effort`, `successor_freeze_id`,
`successor_freeze_digest`, `route_evidence_digest`, `eligibility_predicate`,
`eligibility_rationale`, `aggregation_rule`, `raw_token_aggregation`,
`cache_aggregation`, `terminal_state_severity`,
`acceptance_floor_on_non_completed`.

**Validation rules**:
- Route binding is `g56r-003-route-phase-executor`, model `gpt-5.5`, effort
  `xhigh`.
- Successor freeze is
  `sha256:734672cea5a83e5b8f296ee604f7cb8d93e0a5296a3f864b873fe78bfe518f1e`.
- Route evidence digest is
  `sha256:f01ff64ca3d17b40db8ca802dd6501e62d91c4c161d01a94879c156f90eb09e4`.
- False, missing, or unreproducible eligibility produces no dominance verdict
  and no comparative claim.
- Automatically spawned child work is included in parent-plus-children
  aggregation.

## FrozenBinding

**Purpose**: Stable ID plus committed-bytes digest for frozen G56R-003/CAR-003
authority.

**Fields**: `id`, `digest`, `binding_role`, `source_family`.

**Validation rules**:
- Digest is recomputed from committed bytes.
- Any mismatch fails closed.
- No validator repairs drift by editing the frozen source.

## ControlComparisonContract

**Purpose**: Codex-local document freezing eligibility, dominance, materiality,
confidence, multiplicity, reserved partition binding, and claim mapping.

**Fields**: `schema_version`, `comparison_id`, `status`, `frozen_at`,
`car_003_bindings`, `eligibility_floors`, `dominance_rule`,
`confidence_method`, `multiplicity_position`, `reserved_partition_binding`,
`messaging_map`, `comparison_digest`.

**Validation rules**:
- `comparison_id` is `g56r-004-control-comparison`.
- Eligibility floors run before Pareto or materiality logic.
- No price coefficient, weight, scalar score, or forced rank is allowed.
- The verdict-to-claim-class mapping is total over `dominant`,
  `not_dominant`, `inconclusive`, and the floor-unmet no-verdict outcome.

## DimensionRule

**Purpose**: One direction-aware comparison dimension.

**Fields**: `dimension`, `source_member`, `unit`, `direction`, `class`,
`relative_margin`, `reason`.

**Validation rules**:
- Exactly eight dimensions exist: `input_tokens`, `cached_input_tokens`,
  `output_tokens`, `duration`, `retries`, `compactions`, `acceptance`,
  `terminal_state`.
- `input_tokens`, `cached_input_tokens`, `output_tokens`, and `duration` are
  lower-is-better and margin-eligible at 10%.
- `retries`, `compactions`, and `acceptance` are no-worse-only.
- `terminal_state` is categorical equal-only and no-worse-only.
- Zero comparator denominator returns `margin_not_computable`.

## ReservedComparisonPartition

**Purpose**: Content-addressed reservation of G56R-011 integrated confirmation
objectives plus separate G56R-004 non-qualification smoke partition.

**Fields**: `partition_id`, `objective_ids`, `objective_set_digest`,
`partition_type`, `qualification_eligible`, `owner`, `frozen_at`.

**Validation rules**:
- G56R-004 evidence consumes zero G56R-011 integrated-confirmation objectives.
- Replay admission, smoke planning, and smoke sealing refuse any row referencing
  a reserved objective.
- G56R-004 smoke objectives are non-reserved and non-scored.

## ReplayFixture

**Purpose**: Deterministic non-live evidence for exact-treatment, aggregation,
guard, and comparison behavior.

**Fields**: `fixture_id`, `control_id`, `case_kind`, `input_record`,
`expected_result`, `expected_digest`, `scoring_status`.

**Validation rules**:
- Replaying the same fixture twice emits byte-identical governed results.
- Positive and seeded-negative cases cover all three controls.
- No fixture creates outcome-bearing scored evidence.

## SmokePlan

**Purpose**: Operator-facing plan for one bounded non-scored ChatGPT sign-in
smoke.

**Fields**: `control_id`, `authentication_mode`, `objective_attempt_limit`,
`repetition_limit`, `confirmation_entry_limit`, `elapsed_seconds_limit`,
`raw_token_ceiling`, `component_token_ceilings`, `cache_ceilings`,
`reserved_objective_check`, `raw_capture_retention`.

**Validation rules**:
- `authentication_mode` must be observed as `chatgpt_subscription`.
- An observed `api_key`, missing auth observation, or ambiguous auth mode seals a
  refused record and does not count as success.
- Cache isolation must be `observed_disjoint` with root digests for all three
  unordered control pairs.

## SmokeRecord

**Purpose**: Governed sealed result for an authorized smoke attempt.

**Fields**: `control_id`, `status`, `refusal_reasons`, `observed_authentication`,
`produced_evidence_digest`, `exact_treatment_observables`, `bounds_result`,
`cache_isolation_result`, `raw_capture_digest`, `raw_capture_location_status`.

**State transitions**:
- `planned` -> `sealed_non_scored` when authorized, bounded, and governed.
- `planned` -> `refused` on API-key auth, missing auth, ambiguous auth, reserved
  objective, bound breach, cache-isolation failure, or missing produced
  evidence.
- `planned` -> `unrun` when operator authorization is absent.

## TwinCompletenessRecord

**Purpose**: Machine-checkable comparison between the CAR-004 handoff and
Codex-local mirror artifacts.

**Fields**: `category`, `member_id`, `contract_id`, `hash_relevant`,
`requirement`, `rationale`, `mirror_obligation`, and category-specific detail.

**Validation rules**:
- Categories 1-6 are re-derived from committed Codex schemas, frozen instances,
  and partition registry entries.
- Categories 7-8 are tied to executable checks.
- Missing, extra, invented, mismatched, duplicated, digest-drifted, and
  obligation-mismatched entries fail closed.
- Exactly one sanctioned divergence exists: category-3 `control_kind`.
