# Phase 1 Data Model: CAR-004 Policy Controls and Adaptive Comparators

Entities, their fields, hash-relevance, validation rules, and the requirement each
rule serves. Two new contract documents own everything below; the frozen CAR-003
members they reference are marked read-only and are never redeclared as schema.

Conventions used in every table:

- **Hash?** — whether the field is inside the owning record's content address
  (FR-002). `n/a` marks a field that is itself the address.
- Digest fields all use the frozen pattern `^sha256:[0-9a-f]{64}$`.
- Binding fields all use the local `#/$defs/binding` shape, `{id, digest}` with
  `additionalProperties: false`, restated per document (research D2).

---

## Document 1 — `policy-control-registry.schema.json`

`$id`: `https://racecraft.dev/schemas/car-004/policy-control-registry.schema.json`

Top-level object, `additionalProperties: false`.

| Field | Type | Hash? | Rule | Requirement |
|---|---|---|---|---|
| `schema_version` | `const "1.0.0"` | yes | — | FR-004 |
| `registry_id` | string, minLength 1 | yes | — | FR-004 |
| `registry_digest` | digest | n/a | recomputed and compared on load | FR-002, SC-012 |
| `status` | `const "frozen"` | yes | follows the analysis-plan precedent | FR-004 |
| `frozen_at` | date-time, `Z`-suffixed UTC | yes | follows the `frozen_at` precedent | FR-002, SC-012 |
| `controls` | array, exactly 3 items | yes | closed at three; a fourth entry is refused | FR-001, SC-001 |
| `smoke_bounds` | object | yes (registry-level only) | hash-relevant to the registry, **not** to any control identity | FR-030 |
| `car_003_bindings` | array of bindings | yes | every CAR-003 contract this document references | FR-004 |

### 1.1 Control (common shape, three instances)

Every control carries this envelope. `control_kind` selects which of the three
specialization objects is required.

| Field | Type | Hash? | Rule | Requirement |
|---|---|---|---|---|
| `control_id` | string, minLength 1 | yes | unique within the registry | FR-002 |
| `control_kind` | enum `unpinned \| adaptive \| orchestration_changing` | yes | closed at three, one instance each | FR-001 |
| `control_digest` | digest | n/a | `record_digest(control, digest_field="control_digest")` | FR-002, SC-002 |
| `frozen_at` | date-time UTC | yes | — | FR-002, SC-012 |
| `execution_contract` | object | yes | dispatch parameters, observed signals, bounds, required evidence rows | FR-003 |
| `evidence_requirements` | array of strings, minItems 1 | yes | the row kinds a valid run must produce | FR-003 |
| `attribution_level` | `const "policy"` | yes | never attributed to a single agent's route | FR-018 |

`execution_contract` sub-object:

| Field | Type | Hash? | Rule | Requirement |
|---|---|---|---|---|
| `dispatch_parameters` | object | yes | what the control sets at dispatch time | FR-003 |
| `observed_signals` | array of strings, minItems 1 | yes | every member must resolve to a frozen CAR-003 trace or score-bundle member | FR-008, FR-009 |
| `retry_bounds` | object `{max_retries, per_objective}` | yes | replay-provable | FR-014 |
| `cancellation_bounds` | object `{max_duration_ms, on_breach}` | yes | replay-provable | FR-014 |

### 1.2 Unpinned control specialization

| Field | Type | Hash? | Rule | Requirement |
|---|---|---|---|---|
| `pinned_parent_binding` | binding | yes | the environment contract's already-pinned parent session | FR-006 |
| `pinned_parent_model` | string, minLength 1 | yes | mirrors the pin; not re-derived | FR-006 |
| `pinned_parent_effort` | enum from the frozen effort ladder | yes | `low \| medium \| high \| xhigh \| max` | FR-006 |
| `arm_count` | `const 1` | yes | exactly one arm; no matrix | FR-007 |
| `model_resolution` | `const "inherit"` | yes | agents omit the model or set it to inherit | FR-006 |

**State rule.** A different pinned parent produces a different `control_digest`
and therefore a new control version. It is never applied as an in-place edit.
[FR-007, spec edge case "Parent session re-pinned"]

### 1.3 Adaptive control specialization

| Field | Type | Hash? | Rule | Requirement |
|---|---|---|---|---|
| `candidate_freeze_id` | digest | yes | exactly one successor-capability freeze is bound | FR-011a.1 |
| `freeze_digest` | digest | yes | paired with the id above | FR-011a.1 |
| `escalation_ladder` | array of `candidate_route_id` strings, minItems 1, uniqueItems | yes, **in declared order** | permutation of the bound freeze's `admitted_tuples` | FR-011, FR-011a, FR-011b |
| `escalation_ladder_rationales` | array of `{from_route, to_route, rationale}` | yes | one entry per cross-model step, `rationale` non-empty | FR-011a.4 |
| `max_escalations_per_objective` | `const 1` | yes | one step up, next-higher only | FR-011 |
| `de_escalation_clean_pass_threshold` | `const 3` | yes | N = 3; lives here, not in the comparison contract | FR-012 |
| `de_escalation_timing` | `const "between_objectives"` | yes | never mid-objective | FR-012 |
| `terminal_state_response` | object, 6 entries | yes | total over the frozen terminal-state enum | FR-010 |
| `failure_plane_response` | object, 12 entries | yes | total over the frozen failure-plane enum | FR-010 |
| `failure_code_response` | object, 36 entries | yes | total over the frozen failure-code enum | FR-010, FR-015 |
| `signal_precedence` | `const ["failure_code", "failure_plane", "terminal_state"]` | yes | first non-`none` source decides | FR-010 |
| `budget_triggers` | array of `{member, direction, threshold}` | yes | `member` drawn from the frozen budget field names | FR-008 |
| `clean_pass_definition` | object | yes | `completed` + `none` + zero retries + no budget trigger | FR-012 |

**Policy response enum**: closed at `escalate \| hold \| non_scorable`.

**Ladder validation rules** (all fail-closed, all in
`claude_policy_controls.py`):

1. Binding and membership — every ladder entry resolves to an admitted tuple of
   the single bound freeze. [FR-011a.1]
2. Totality — the ladder is a permutation of the admitted set: no duplicate, no
   omission. Exclusion happens at the freeze through `excluded_tuples`, never by
   omission from the ladder. [FR-011a.2, FR-013]
3. Within-model order — entries sharing a `model` must be ordered consistently
   with the frozen effort ladder read from the freeze schema. [FR-011a.3]
4. Cross-model order — every step whose `model` differs from its predecessor's
   must carry a non-empty rationale. [FR-011a.4]

**State transitions** (the adaptive policy's only state is `current_index` into
the ladder plus `clean_streak`):

| From | Signal | To | Rule |
|---|---|---|---|
| `current_index = i`, escalation unspent | response `escalate`, `i + 1` exists | `current_index = i + 1`, escalation spent for this objective | FR-011 |
| `current_index = i`, escalation spent | response `escalate` | unchanged; objective terminates under retry/cancellation bounds | FR-011, FR-014 |
| `current_index = last` | response `escalate` | unchanged; no escalation recorded; no wrap-around | FR-011b, FR-013 |
| any | response `non_scorable` | unchanged; row marked non-scorable; not counted as escalation | FR-015 |
| objective boundary, `clean_streak = 3`, `i > 0` | — | `current_index = i - 1`, `clean_streak = 0` | FR-012 |
| objective boundary, non-clean objective | — | `clean_streak = 0` | FR-012 |
| mid-objective | any | de-escalation never evaluated | FR-012 |

### 1.4 Orchestration-changing control specialization

| Field | Type | Hash? | Rule | Requirement |
|---|---|---|---|---|
| `topology_descriptor` | object `{topology_id, fan_out, child_shape}` | yes | inside the content address | FR-017 |
| `topology_digest` | digest | yes | over the descriptor | FR-017 |
| `aggregation_rule` | object, 8 entries | yes | one entry per Pareto dimension, none omitted | FR-016 |
| `terminal_state_severity` | array, exactly 6 members, ordered | yes | `completed, failed, timed_out, cancelled, budget_exhausted, abandoned`; validated **set-equal** to the frozen terminal-state enum | FR-016a |
| `acceptance_rule` | `const "parent_objective_oracle"` | yes | never summed, averaged, minimized, or maximized | FR-016b |
| `acceptance_floor_on_non_completed` | `const 0` | yes | matches the frozen candidate-failure acceptance constant | FR-016b |

`aggregation_rule` entries:

| Dimension | Rule value | Requirement |
|---|---|---|
| `input_tokens` | `sum` | FR-016 |
| `cached_input_tokens` | `sum` | FR-016 |
| `output_tokens` | `sum` | FR-016 |
| `duration_ms` | `sum` | FR-016 |
| `retries` | `sum` | FR-016 |
| `compactions` | `sum` | FR-016 |
| `terminal_state` | `worst_wins_by_severity` | FR-016a |
| `acceptance` | `parent_objective_oracle` | FR-016b |

**Aggregation invariants** enforced by the validator:

- Every automatically spawned child contributes to the six additive dimensions,
  including children that failed, timed out, or were cancelled. [FR-016]
- A zero-child run folds to the parent's own values and is a valid row, not an
  error. [FR-016 edge case]
- The aggregate terminal state is `completed` only when the parent and every
  child are `completed`. [FR-016a]
- Acceptance is 0 whenever the aggregate terminal state is not `completed`.
  [FR-016b]
- Acceptance is `null` only when the oracle did not run at all; every committed
  replay fixture row carries a non-null aggregate acceptance. [FR-016c, SC-015]

### 1.5 `smoke_bounds`

Registry-level, shared by all three controls, hash-relevant to the registry
document only.

| Field | Value | In the raw-token identity? | Requirement |
|---|---|---|---|
| `max_attempts` | 5 | — | FR-030 |
| `max_candidates` | 1 | — | FR-030 |
| `max_confirmation_entries` | 0 | — | FR-027, FR-030 |
| `max_duration_seconds` | 1800 | — | FR-030 |
| `max_input_tokens` | 800000 | yes | FR-030 |
| `max_cache_read_tokens` | 150000 | yes | FR-030 |
| `max_output_tokens` | 50000 | yes | FR-030 |
| `max_cache_write_tokens_by_ttl_class` | `{ephemeral_5m, ephemeral_1h}` | no — diagnostic only | FR-030 |
| `authentication_mode` | `const "subscription"` | — | FR-030 |
| `scored` | `const false` | — | FR-027, FR-030 |

**Machine-checked identity**: `max_input_tokens + max_cache_read_tokens +
max_output_tokens == 1000000`. [SC-017]

Every numeric in this object carries its unit and comparison direction, following
the frozen guardrail-method precedent, so twin-handoff category 6 is derived from
the committed bytes rather than transcribed. [FR-034.6]

---

## Document 2 — `control-comparison.schema.json`

`$id`: `https://racecraft.dev/schemas/car-004/control-comparison.schema.json`

Top-level object, `additionalProperties: false`.

| Field | Type | Hash? | Rule | Requirement |
|---|---|---|---|---|
| `schema_version` | `const "1.0.0"` | yes | — | FR-004 |
| `comparison_id` | string, minLength 1 | yes | — | FR-004 |
| `comparison_digest` | digest | n/a | recomputed on load | FR-002, SC-012 |
| `status` | `const "frozen"` | yes | — | FR-004 |
| `frozen_at` | date-time UTC | yes | — | FR-002, SC-012 |
| `eligibility_floors` | object | yes | — | FR-019 |
| `dominance_rule` | object | yes | — | FR-020, FR-021 |
| `confidence_method` | object | yes | — | FR-021d, FR-023 |
| `multiplicity_position` | object | yes | — | FR-023 |
| `reserved_partition_binding` | binding | yes | the CAR-011 reserved entry | FR-025 |
| `messaging_map` | object, 3 entries | yes | total over the verdict enum | FR-024 |
| `car_003_bindings` | array of bindings | yes | — | FR-004 |

### 2.1 `eligibility_floors`

| Field | Value | Requirement |
|---|---|---|
| `required_gates` | array of 7, set-equal to the frozen `deterministic_gates.gate` enum — `role, safety, grounding, mutation, tool, output, acceptance` | FR-019 |
| `all_gates_must_pass` | `const true` | FR-019 |
| `quality_floors_binding` | binding to the frozen analysis plan | FR-019 |
| `reliability_guardrail_breach_result` | `const "no_qualification"` | FR-019 |
| `availability_gate_required` | `const true` | FR-019 |
| `verdict_when_floor_unmet` | `const "no_verdict"` | FR-019 |

A control that has not cleared every floor yields no verdict whatever its
resource numbers say. [FR-019]

### 2.2 `dominance_rule`

| Field | Value | Requirement |
|---|---|---|
| `rule` | `const "environment_independent_pareto"` | FR-020 |
| `weights_prohibited` | `const true` | FR-020 |
| `dimensions` | array of 8, set-equal to the frozen `pareto_policy.dimensions` | FR-020 |
| `dimension_projection` | object, one frozen rename: `duration_ms` to `duration` | FR-021e |
| `evaluation_order` | `const ["eligibility_floors", "pareto", "materiality_margin"]` | FR-021a |
| `margin_denominator` | `const "comparator_value"` | FR-021c |
| `zero_denominator_result` | `const "margin_not_computable"` | FR-021c |
| `margin_map` | object, exactly 8 entries | FR-021, SC-016 |

`margin_map` entries — total over all eight dimensions, none omitted:

| Dimension | Class | Relative margin | Unit | Direction | Requirement |
|---|---|---|---|---|---|
| `input_tokens` | margin_eligible | 0.10 | tokens | lower_is_better | FR-021 |
| `cached_input_tokens` | margin_eligible | 0.10 | tokens | lower_is_better | FR-021 |
| `output_tokens` | margin_eligible | 0.10 | tokens | lower_is_better | FR-021 |
| `duration` | margin_eligible | 0.10 | milliseconds | lower_is_better | FR-021 |
| `retries` | no_worse_only | — | count | lower_is_better | FR-021 |
| `compactions` | no_worse_only | — | count | lower_is_better | FR-021 |
| `acceptance` | no_worse_only | — | ratio | higher_is_better | FR-021b |
| `terminal_state` | no_worse_only | — | categorical | equal_only | FR-021b |

Each `no_worse_only` entry carries a `reason` string. None of the four can ever
supply material dominance; any of them being worse defeats it. A null or absent
`acceptance` or `terminal_state` makes that dimension uncertain and the whole
comparison inconclusive. [FR-021b]

### 2.3 `confidence_method` and `multiplicity_position`

| Field | Value | Requirement |
|---|---|---|
| `method` | `const "one_sided_lower_confidence_bound"` | FR-021d, FR-023 |
| `confidence_level` | `const 0.95` | FR-023 |
| `alpha` | `const 0.05` | FR-023 |
| `cluster_unit` | `const "role"` | FR-023 |
| `cluster_adjustment` | `const "cluster_robust_sandwich_variance_by_role"` | FR-023 |
| `replay_point_estimate_stand_in` | `const true` | FR-021d |
| `family` | `const "secondary_control_arm_family"` | FR-023 |
| `adjustment` | `const "holm_bonferroni_within_the_secondary_control_arm_family"` | FR-023 |
| `family_wise_alpha` | `const 0.05` | FR-023 |
| `draws_alpha_from_primary` | `const false` | FR-023 |
| `disjoint_from_frozen_families` | `const true` | FR-023, SC-017 |
| `rationale` | string, minLength 1 | FR-023 |

The family is declared here and MUST NOT be added to the frozen analysis plan's
multiplicity declaration, which is closed at three families. [FR-005, FR-023]

### 2.4 `messaging_map`

| Verdict | `permitted_claim_class` | `forbidden_claim_classes` | Requirement |
|---|---|---|---|
| `dominant` | `measured_improvement_over_previous_static_baseline` | `efficient`, `optimal`, `best_measured` | FR-024 |
| `not_dominant` | `no_comparative_claim` | `efficient`, `optimal`, `best_measured` | FR-024 |
| `inconclusive` | `no_comparative_claim` | `efficient`, `optimal`, `best_measured` | FR-022, FR-024 |

Total and single-valued over the closed verdict enum `dominant \| not_dominant \|
inconclusive`. A mixed, tied, inconclusive, or incomplete comparison imposes no
messaging restriction. [FR-022, SC-008]

---

## Entity 3 — Partition Registry Entries (frozen CAR-003 record kind)

Produced by `build_partition_registry_entry()` in `claude_experiment_policy.py`.
No new schema is authored; the record kind already exists.

| Entry | `partition_type` | `qualification_eligible` | `owning_spec` | Purpose |
|---|---|---|---|---|
| Reserved CAR-011 comparison partition | `integrated_confirmation` | `true` | `CAR-011` | held untouched; never referenced by any CAR-004 row |
| CAR-004 smoke partition | `calibration` | `false` | `CAR-004` | the at most five non-reserved objectives the smokes use |

Fields on each entry (all set by the frozen builder): `schema_version`,
`record_kind`, `partition_id`, `partition_type`, `qualification_eligible`,
`objective_set_digest`, `objective_ids` (deduplicated and sorted), `frozen_at`,
`owning_spec`.

**Validation rules:**

- The frozen builder raises when `calibration` is paired with
  `qualification_eligible: true`, so the CAR-004 smoke partition is structurally
  incapable of carrying qualification-bearing evidence. [FR-027]
- `register_partitions([reserved, smoke])` fails closed on a duplicate partition
  id or any shared objective, proving disjointness with the same machinery
  CAR-003 uses. [FR-025]
- The guard fails if any replay row or smoke row references a member of the
  reserved objective set, and passes on the delivered evidence set. [FR-026,
  SC-007]

---

## Entity 4 — Replay case (`control-replay.json`)

Fixture envelope follows the CAR-003 precedent: `{schema_version, fixture_kind,
description, cases: [...]}` with `fixture_kind: "policy_control_replay"`.

| Case | Control | Proves | Requirement |
|---|---|---|---|
| 1 | unpinned | inherit resolution rides the pinned parent; a different pin is a different digest | FR-006, FR-007 |
| 2 | adaptive | one escalation per objective; a second signal does not escalate again | FR-011, FR-014 |
| 3 | adaptive | ceiling reached — no route outside the frozen candidate set; no wrap-around | FR-011b, FR-013 |
| 4 | adaptive | three consecutive clean passes de-escalate at the boundary; an interrupted streak does not | FR-012 |
| 5 | adaptive | a platform-initiated reroute is non-scorable and is not counted as escalation | FR-015 |
| 6 | orchestration_changing | multi-child aggregate: additive dimensions equal the parent-plus-children sum; one failed child makes the terminal state non-`completed` and floors acceptance to 0 | FR-016, FR-016a, FR-016b, FR-029, SC-006, SC-015 |

**Determinism rules** (FR-028, SC-005): no timestamps generated at run time, no
randomness, no absolute paths, no session identifiers. Every value is literal in
the fixture. Replaying twice produces byte-identical results, asserted by
digesting the replay output on two runs.

**Evidence rules** (FR-027, FR-030, SC-010): every case row carries `scored:
false`, references only CAR-004 smoke-partition or synthetic objective ids, and
references no member of the reserved partition. Zero rows are outcome-bearing.

---

## Entity 5 — Bounded smoke record

Produced by `run-control-smoke.py`, written under the git-ignored
`tests/speckit-pro/layer6-efficiency/results/`, never committed. [FR-033]

| Field | Rule | Requirement |
|---|---|---|
| `control_id` | one of the three frozen controls | FR-030 |
| `control_digest` | must match the frozen registry | FR-002 |
| `authentication_mode` | must be `subscription`; the script refuses `api_key` | FR-030 |
| `scored` | `const false` | FR-027, FR-030 |
| `objective_ids` | subset of the CAR-004 smoke partition; at most 5 | FR-030 |
| `partition_id` | the CAR-004 smoke partition; never the reserved one | FR-026, FR-027 |
| consumed budget members | each at or below the frozen `smoke_bounds` value | FR-030, SC-009 |
| `cache_root` | per-arm ephemeral root, distinct per control | FR-032 |
| demonstrated behavior | escalation / inherit resolution / parallel child aggregation | FR-031 |

A run that reaches a bound stops at the bound and remains valid non-scored
evidence; it must not silently exceed the declared budget. [FR-030 edge case]

---

## Entity 6 — Twin-handoff record

`docs/ai/specs/.process/CAR-004-twin-handoff.md`. Two fenced JSON blocks plus
prose.

**Mirror-membership entry fields** (block 1):

| Field | Rule | Requirement |
|---|---|---|
| `category` | integer 1–8 | FR-034 |
| `member_id` | JSON Pointer, `$id`, enum member, or identifier | FR-034 |
| `contract_id` | the owning contract `$id` | FR-034 |
| `hash_relevant` | boolean, matching FR-002 | FR-034 |
| `requirement` | the CAR-004 requirement it implements | FR-034 |
| `rationale` | one line | FR-034 |
| `mirror_obligation` | exactly one of `mirror_required`, `sanctioned_divergence`, `car_owned` | FR-034 |

**Categories 1–6 are derived** from the committed schema documents and frozen
instances and diffed both directions by the automated check. **Categories 7–8 are
authored** — decision semantics that add no schema member, and required guard
behaviors. [FR-034a, SC-011]

**Sanctioned divergence** (block 2): closed at exactly one entry, the
three-control composition, stating the authority on each side, why the difference
is a platform value rather than a logic divergence, the expected twin action
(none), and the resulting status (closed, nothing owed). Must be reachable
without opening either roadmap. A second divergence, or one classified against a
contract document, declared member, frozen numeric, or decision-semantics entry,
fails the check. [FR-035, FR-035a, SC-011]

**At publication** the reconciliation candidate list is explicitly empty and every
entry is `mirror_required` or the single sanctioned divergence. [FR-036a]

**The record is not hash-relevant** to any control's or the comparison contract's
content address. [FR-037a]

---

## Requirement coverage index

| Artifact | Requirements it carries |
|---|---|
| `policy-control-registry.schema.json` + its frozen instance | FR-001, FR-002, FR-003, FR-004, FR-006 – FR-018, FR-030 |
| `control-comparison.schema.json` + its frozen instance | FR-002, FR-004, FR-019 – FR-025 |
| `claude_policy_controls.py` | FR-001, FR-002, FR-005, FR-008 – FR-018, FR-026, FR-028, FR-030 |
| `claude_control_comparison.py` | FR-019 – FR-024 |
| `partition-registry-entries.json` | FR-025, FR-027 |
| `control-replay.json` | FR-028, FR-029, FR-027 |
| `run-control-smoke.py` | FR-030, FR-031, FR-032, FR-033 |
| `test-policy-control-contracts.py` | FR-001 – FR-018, FR-026 – FR-030 |
| `test-control-comparison-dominance.py` | FR-019 – FR-024 |
| `test-twin-handoff-completeness.py` | FR-034, FR-034a, FR-035, FR-035a, FR-036, FR-036a, FR-037a |
| `CAR-004-twin-handoff.md` | FR-034 – FR-037a |
| Additive-only discipline, verifiable from the diff alone | FR-004, FR-005, SC-004 |
