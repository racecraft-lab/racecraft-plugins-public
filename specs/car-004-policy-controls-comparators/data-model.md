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
| `retry_bounds` | object `{max_retries, counted_over, on_breach}` | yes | replay-provable | FR-014, FR-014a |
| `cancellation_bounds` | object `{max_duration_ms, counted_over, on_breach}` | yes | replay-provable | FR-014, FR-014a |

Both bound objects carry the same two FR-014a members beside their ceiling, and
both are hash-relevant:

| Member | Value | Requirement |
|---|---|---|
| `counted_over` | `per_objective` on the unpinned and adaptive controls — spanning every attempt and every route the policy occupies inside that objective, so an escalation resets neither counter; `per_unit` on the orchestration-changing control, matching the FR-016 additive aggregation so a run cannot stay inside its bounds by distributing retries or elapsed time across children | FR-014a.1, FR-014a.2 |
| `retry_bounds.on_breach` | `{terminal_state: "failed", failure_code: "candidate_failed"}` — exhausting retries means at least one attempt failed, the one outcome the bound CAR-003 execution trace can evidence; `abandoned` stays reserved for work given up with no recorded failure and `budget_exhausted` is not representable on that trace | FR-014a.3 |
| `cancellation_bounds.on_breach` | `{terminal_state: "cancelled", failure_code: "candidate_cancelled"}` — the breach action is a cancellation the harness itself performs, which is what the frozen trace's completed-cancellation evidence records; `timed_out` stays reserved for a platform-side timeout the harness did not request, and is not representable on that trace either | FR-014a.3 |

Each `on_breach` pairing is the frozen candidate-plane pairing, not a chosen one:
the candidate plane admits one code per terminal state, and a candidate-plane row
whose terminal state and failure code disagree is refused. Committed replay
fixtures exercise **both** breach paths, not only the respected path, and both
breach states are non-`completed`, so the same fixtures prove the FR-016a fold by
severity and the FR-016b floor to acceptance 0. [FR-014a.4, SC-023]

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
| `signal_precedence` | `const ["failure_code", "failure_plane", "retry_count", "budget_threshold", "terminal_state"]` | yes | ordered array over the **closed source set**, which must cover every source FR-008 admits; the first source whose value is not the frozen `none` sentinel decides. Terminal state is ranked **last** and is always valued, so every row resolves — which is also why it cannot sit ahead of the retry-count and budget-threshold sources, whose mapped responses and ranks would otherwise be unreachable, the outcome FR-010b exists to forbid. A source FR-008 admits but this array omits fails the well-formedness check closed | FR-010b |
| `retry_count_response` | `{threshold, direction, response}` | yes | the mapped response and rank for the retry-count source named in `signal_precedence` | FR-008, FR-010b |
| `budget_triggers` | ordered array of `{member, direction, threshold, response}` | yes | `member` drawn from the frozen budget field names; the mapped response applies once the declared direction and threshold are met, which is what gives the budget-threshold source a response and a rank | FR-008, FR-010b |
| `clean_pass_definition` | object | yes | `completed` + `none` + zero retries + no declared budget **trigger** met (the trigger, not a breach) | FR-012, FR-012a.1 |
| `clean_pass_accounting` | object | yes | the five FR-012a rules: an escalating objective is never clean; a `non_scorable` objective neither advances nor resets and the streak resumes across it, taking precedence over the reset-on-non-clean rule; the streak resets whenever de-escalation is evaluated whether or not a step occurs; a de-escalation due at the first ladder entry records no step and no wrap-around | FR-012a |

**Policy response enum**: closed at `escalate \| hold \| non_scorable`.

**Map-consistency rules** (revalidated on every load under FR-010a, fail-closed):

1. **Plane agrees with code** — the frozen contract derives a row's failure plane
   from its failure code, so the plane map must assign each plane the same
   response the code map assigns to every code on that plane. Codes on one plane
   that disagree fail closed. Without this the plane map is unreachable under any
   code-first precedence, because a `none` code always carries a `none` plane.
   [FR-010c.1]
2. **Candidate terminal state agrees with code** — the frozen contract pairs each
   non-`completed` terminal state with exactly one candidate-plane failure code,
   so the terminal-state map must assign each such state the same response the
   code map assigns to its paired code. [FR-010c.2]

Neither derivation is transcribed. The plane derivation is imported read-only
from `lib/claude_score_bundle.py`, which publishes it as `FAILURE_PLANE_BY_CODE`
and `failure_plane_for`. That module publishes no terminal-state-keyed map, so
the candidate-plane pairing is derived live from the frozen `failure_code` enum in
`contracts-claude/score-bundle.schema.json` instead: each non-`completed` member
of the frozen terminal-state enum pairs with the `candidate_<state>` member of
the code enum, and a derived code absent from that enum fails the check closed.
The pairing is therefore read from the same committed bytes the contract
publishes, and no map is added to a frozen module to make it importable. A
disagreement is repaired by re-freezing the control as a new
version under FR-002, never by editing a map in place and never by editing the
frozen CAR-003 derivation or pairing.

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
| any | response `non_scorable` | unchanged; row marked non-scorable; not counted as escalation; escalation allowance unspent; ladder position untouched | FR-015, FR-015a |
| objective boundary, `clean_streak = 3`, `i > 0` | — | `current_index = i - 1`, `clean_streak = 0` | FR-012 |
| objective boundary, `clean_streak = 3`, `i = 0` | — | no step and **no wrap-around** to the final entry; `clean_streak = 0` still | FR-012a.5 |
| objective boundary, clean objective, `clean_streak < 3` | — | `clean_streak + 1` | FR-012, FR-012a.1 |
| objective boundary, objective in which the policy escalated | — | `clean_streak = 0`; an escalating objective never counts toward the streak | FR-012a.2 |
| objective boundary, non-scorable objective | — | `clean_streak` **unchanged** — neither advanced nor reset; the streak resumes across it | FR-012a.3 |
| objective boundary, any other non-clean objective | — | `clean_streak = 0` | FR-012, FR-012a |
| mid-objective | any | de-escalation never evaluated | FR-012 |

Row order is precedence: the non-scorable exclusion outranks the
reset-on-non-clean rule, so a non-scorable objective is neither a clean pass nor
a streak-breaking one. [FR-012a.3]

### 1.4 Orchestration-changing control specialization

| Field | Type | Hash? | Rule | Requirement |
|---|---|---|---|---|
| `topology_descriptor` | object, exactly three members `{topology_id, fan_out, child_shape}` | yes | inside the content address; restated in full so "altering any hash-relevant field" is decidable over an enumerated member set | FR-017, FR-017a |
| `topology_digest` | digest | yes | over the descriptor | FR-017 |
| `aggregation_rule` | object, 8 entries | yes | one entry per Pareto dimension, none omitted | FR-016 |
| `raw_token_aggregation` | object, 4 entries | yes | the frozen four-member raw token vector, all `sum`; deliberately not the eight-dimension Pareto vector | FR-016e.1 |
| `cache_aggregation` | object | yes | cache write summed per frozen TTL class and cache read summed, keyed identically to the ceilings that bound them | FR-016e.3 |
| `unrecorded_quantity_disposition` | `const "unobserved"` | yes | a unit member with no cache diagnostic makes that aggregate not computable, so the bound it feeds is recorded unobserved — never passed, never zero | FR-016e.5 |
| `terminal_state_severity` | array, exactly 6 members, ordered | yes | `completed, failed, timed_out, cancelled, budget_exhausted, abandoned`; validated **set-equal** to the frozen terminal-state enum | FR-016a |
| `acceptance_rule` | `const "parent_objective_oracle"` | yes | never summed, averaged, minimized, or maximized | FR-016b |
| `acceptance_floor_on_non_completed` | `const 0` | yes | matches the frozen candidate-failure acceptance constant | FR-016b |

`fan_out` is a declared **ceiling** on automatically spawned children, never an
exact count: a run spawning fewer children — zero included — still conforms and
yields a valid row, while a run spawning more does not conform and is refused
rather than aggregated. [FR-017a]

`child_shape` sub-members, both hash-relevant:

| Member | Value | Requirement |
|---|---|---|
| `dispatch_mechanism` | the mechanism under which **every** unit member is dispatched through the CAR-004 harness. A topology admitting a member that could spawn a further node outside that harness is not freezable under CAR-004, because its membership would not be decidable from the record. This is also what makes the FR-031 smoke feasible on the subscription path by construction | FR-016d.1 |
| `wall_time_window` | `const "full_elapsed_including_child_wait"` — every unit member's recorded wall time is its full elapsed window, dispatch to completion. The frozen trace declares `wall_time_ms` as a bare nullable integer with no such semantics, and the FR-031a.5 parallel inequality is only sound on this reading; a topology whose parent wall time excludes child wait is not freezable under CAR-004 | FR-031a.5 |

`raw_token_aggregation` entries:

| Member | Rule | Bounded by | Note | Requirement |
|---|---|---|---|---|
| `input_tokens` | `sum` | `max_input_tokens` | also a Pareto dimension | FR-016e.1 |
| `output_tokens` | `sum` | `max_output_tokens` | also a Pareto dimension | FR-016e.1 |
| `cached_input_tokens` | `sum` | `max_cached_input_tokens` | also a Pareto dimension | FR-016e.1 |
| `reasoning_output_tokens` | `sum` | — no ceiling | **not** a Pareto dimension: the unit carries the sum and that sum must not enter the dominance comparison, which would add a ninth dimension to a frozen eight-dimension policy. It also carries no sub-budget and admits a null value, so it is summed and reported but is not an input to the `raw_token_ceiling` check | FR-016e.2, FR-030b.2 |

The three bounded members are exactly the summands of the §1.5 raw-token
identity, so the quantity the 1,000,000 ceiling is read against and the quantity
the identity decomposes are the same sum. [FR-030a, FR-030b.2, SC-028]

`cache_aggregation` entries — diagnostic-only, and aggregating them promotes
nothing: neither becomes a Pareto dimension, neither enters the FR-030a
raw-token identity, and neither is constrained against `max_input_tokens`.
[FR-016e.4]

| Member | Rule | Bounded by | Requirement |
|---|---|---|---|
| `cache_write_tokens_by_ttl_class` | `sum` per class over the frozen closed key space `ephemeral_5m`, `ephemeral_1h` | `max_cache_write_tokens_by_ttl_class`, keyed over the same closed class space | FR-016e.3 |
| `cache_read_tokens` | `sum` | `max_cache_read_tokens` | FR-016e.3 |

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

**Unit membership** — the unit is the parent objective's node together with the
transitive closure of the spawning identifier every non-parent row records,
authored at dispatch rather than read back. Nested descendants are inside the
unit for both the additive sum and the fan-out ceiling, so a topology cannot shed
cost by nesting a child one level deeper. Wherever a unit member's evidence binds
a frozen execution trace carrying the shared treatment-record contract's
`parent_child_graph`, the CAR-004 boundary must agree with it and a disagreement
fails the row closed rather than letting either source win; the obligation is
conditional on the binding existing. That graph belongs to the shared
treatment-record contract, never to the CAR-002 Claude trace contract, which
publishes only a nullable parent-session configuration string. [FR-016d.1]

**Aggregation invariants** enforced by the validator:

- Every automatically spawned child contributes to the six additive Pareto
  dimensions and to the four raw-token members, including children that failed,
  timed out, or were cancelled. [FR-016, FR-016e.1]
- A zero-child run folds to the parent's own values and is a valid row, not an
  error. [FR-016 edge case]
- The aggregate terminal state is `completed` only when the parent and every
  child are `completed`. [FR-016a]
- Acceptance is 0 whenever the aggregate terminal state is not `completed`.
  [FR-016b]
- Acceptance is `null` only when the oracle did not run at all; every committed
  replay fixture row carries a non-null aggregate acceptance. The FR-016b floor
  **outranks** this allowance wherever they meet: a unit that failed and
  therefore never reached its oracle records 0, not null, so null is reachable
  only on a `completed` unit whose oracle did not run. [FR-016c, SC-015]
- A unit member recording **no terminal state** makes the row non-conforming and
  is refused rather than folded over the remaining members — deliberately the
  opposite disposition to a null acceptance, because a missing severity leaves
  the unit malformed rather than merely incomplete. [FR-016d.3]
- A row that is neither the parent's own nor carries an authored spawning
  identifier is likewise refused rather than aggregated. [FR-016d.4]
- A `service_reroute` on the parent or on any unit member makes the **whole
  unit** non-scorable; `terminal_state_severity` carries no non-scorable member,
  so a rerouted member cannot be folded away. [FR-015a.3]

### 1.5 `smoke_bounds`

Registry-level, shared by all three controls, hash-relevant to the registry
document only.

| Field | Value | In the raw-token identity? | Requirement |
|---|---|---|---|
| `max_attempts` | 5 | — | FR-030 |
| `max_candidates` | 1 | — | FR-030 |
| `max_confirmation_entries` | 0 | — | FR-027, FR-030 |
| `max_duration_seconds` | 1800 | — | FR-030 |
| `max_input_tokens` | 800000 | yes — bounds `input_tokens` | FR-030 |
| `max_cached_input_tokens` | 150000 | yes — bounds `cached_input_tokens`; coined by CAR-004 because the frozen budget carries no ceiling for that raw-token member | FR-030, FR-030a |
| `max_output_tokens` | 50000 | yes — bounds `output_tokens` | FR-030 |
| `raw_token_ceiling` | 1000000 | n/a — it is the identity's right-hand side | FR-030a |
| `max_cache_read_tokens` | 1200000 | no — bounds the `cache_read_tokens` diagnostic, which FR-016e.4 keeps out of the identity; just under 2x the frozen CAR-003 campaign budget's per-attempt allowance over five attempts (6,000,000 / 48 attempts = 125,000; x5 = 625,000) | FR-030, FR-030a |
| `max_cache_write_tokens_by_ttl_class` | `{ephemeral_5m: 160000, ephemeral_1h: 40000}` | no — diagnostic only; just under 2x the frozen CAR-003 campaign budget's per-attempt allowance over five attempts, keeping that budget's 4:1 ratio between the classes | FR-030, FR-030a |

This is the closed member set spec.md Assumptions freezes, and `smoke_bounds` is
hash-relevant to the registry, so nothing may be added to it. In particular
**`authentication_mode` and `scored` are not members of `smoke_bounds`**. Both
are properties of a produced smoke record (Entity 5), not declared bounds:
FR-030c.2 requires the recorded mode be an observation of the run that happened
and never a restatement of operator intent or a configuration setting, and a
`const "subscription"` bound would be exactly that — it would also make
FR-030c.3's refused record, which must still carry its observed `api_key` value,
unrepresentable.

**Scope**: every bound in this object is counted over the parent-plus-children
unit, `max_duration_seconds` as elapsed wall clock over the unit rather than as
the additive `duration_ms` the Pareto rule sums, and a child dispatch consumes
no attempt against `max_attempts`. Each token ceiling is read against the §1.4
aggregate of the quantity it names, and against no other. [FR-030b]

**Machine-checked identity**: `max_input_tokens + max_cached_input_tokens +
max_output_tokens == raw_token_ceiling`, with `raw_token_ceiling` frozen at
1,000,000 so FR-034 category 6 derives the ceiling from committed bytes rather
than transcribing it. The three summands are the ceilings on the three bounded
members of the frozen raw token vector; the validator refuses an identity that
admits `max_cache_read_tokens` or a cache-write class, since both bound the
cache diagnostics FR-016e.4 keeps out of it. `max_cache_read_tokens` and each
cache-write TTL class are separately checked to be present at their frozen values
and to stay outside the identity. None of the three is checked
against `max_input_tokens`: neither cache quantity is bounded by input, as the frozen
calibration-pilot envelope shows by declaring cache-write and cache-read ceilings
well above its own input ceiling. [SC-017, SC-028, FR-030a]

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
| `claim_class_when_floor_unmet` | `const "no_comparative_claim"` | FR-024a |
| `messaging_restriction_when_floor_unmet` | `const false` | FR-024a |

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

| Verdict | `permitted_claim_class` | `forbidden_claim_classes` | `messaging_restriction` | Requirement |
|---|---|---|---|---|
| `dominant` | `measured_improvement_over_previous_static_baseline` | `efficient`, `optimal`, `best_measured` | `true` | FR-024 |
| `not_dominant` | `no_comparative_claim` | *(empty)* | `false` | FR-022, FR-024 |
| `inconclusive` | `no_comparative_claim` | *(empty)* | `false` | FR-022, FR-024 |

Total and single-valued over the closed verdict enum `dominant \| not_dominant \|
inconclusive`. A mixed, tied, inconclusive, or incomplete comparison imposes no
messaging restriction, so neither non-dominant entry carries a forbidden set:
carrying one would *be* the restriction FR-022 refuses to impose. Only the
`dominant` entry restricts. [FR-022, SC-008]

The `dominant` entry additionally carries
`restriction_scope: "release_wording_only"` with
`static_defaults_may_still_ship: true` — the second half of the acceptance
criterion this map freezes, which permits shipping the static defaults for
declared operational simplicity in the same sentence that removes the
"efficient", "optimal", and "best measured" wording. Without it a mechanical
consumer cannot tell a wording restriction from a shipping one. [FR-024]

---

## Entity 3 — Partition Registry Entries (frozen CAR-003 record kind)

Produced by `build_partition_registry_entry()` in `claude_experiment_policy.py`.
No new schema is authored; the record kind already exists.

| Entry | `partition_type` | `qualification_eligible` | `owning_spec` | Purpose |
|---|---|---|---|---|
| Reserved CAR-011 comparison partition | `integrated_confirmation` | `true` | `CAR-004` | held untouched for CAR-011; never referenced by any CAR-004 row |
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
- `owning_spec` is `CAR-004` on both entries — the spec that freezes them, as in
  the four reserved entries `run-calibration-pilot.py` registers under
  `owning_spec: "CAR-003"` and never consumes. No frozen admission rule reads the
  field; the reservation's beneficiary is carried by the partition id and the
  comparison contract's binding. [FR-025d, FR-025c]
- The guard fails if any replay row or smoke row references a member of the
  reserved objective set, and passes on the delivered evidence set. The smoke half
  runs at two points: the plan refuses to emit a reserved objective, and the seal
  refuses a record that references one. [FR-026, FR-026a, SC-007]

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
| 7 | adaptive | retry-bound breach: the objective exhausts its retry bound and records `failed` with `candidate_failed`, the escalation earlier in the objective having reset neither counter; the aggregate folds non-`completed` with acceptance 0 | FR-014a.3, FR-014a.4, FR-016a, FR-016b, SC-023 |
| 8 | adaptive | cancellation-bound breach: the objective breaches its cancellation bound and records `cancelled` with `candidate_cancelled`, folding the same way | FR-014a.3, FR-014a.4, SC-023 |
| 9 | adaptive | a clean-pass streak that **survives and completes across** an excluded non-scorable objective — the streak neither advances nor resets on it and reaches three afterwards, proving the accounting rather than asserting it | FR-012a.3, SC-024 |

Nine cases in all. Cases 7 through 9 are required by requirement, not by
preference: FR-014a.4 obliges the fixtures to exercise both breach paths and not
only the respected path, and FR-012a.3 obliges a committed streak fixture that
both survives an excluded objective and completes across it.

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
| `authentication_mode` | the **observed** mode, over the Claude-side frozen enum `subscription \| api_key` — the member the experiment-assignment and successor-capability-freeze contracts carry, never the shared runtime environment contract's `chatgpt_subscription \| api_key`. Never a `const`: an observed `api_key` is recorded, and the record is refused **as evidence** rather than discarded | FR-030, FR-030c |
| `evidence_admissibility` | `admitted` or `refused` with a refusal reason, so a refused run stays distinguishable from one that never ran; a refused record counts toward neither FR-031 nor SC-009, and the remedy is a re-run, never a relabel | FR-030c.3 |
| `scored` | `const false` | FR-027, FR-030 |
| `objective_ids` | subset of the CAR-004 smoke partition; at most 5; a child dispatch consumes no attempt | FR-030, FR-030b.4 |
| `partition_id` | the CAR-004 smoke partition; never the reserved one | FR-026, FR-027 |
| consumed budget members | each at or below the frozen `smoke_bounds` value, read over the parent-plus-children unit; token and cache ceilings against the FR-016e unit aggregate | FR-030, FR-030b, SC-009 |
| `elapsed_wall_clock_seconds` | elapsed over the unit from the parent's dispatch to the last member's completion; deliberately not the additive `duration_ms` | FR-030b.3 |
| `observed_cache_isolation` | one frozen record per **unordered arm pair** — all three across the series — each carrying `status`, this arm's cache-root digest, the paired arm's cache-root digest, and the disjointness flag. Roots are digests, never filesystem paths. `observed_disjoint` is the only status under which the smoke stands as FR-031 evidence; `observed_shared` carries `infrastructure_failure` at `failure_plane=infrastructure` and `unobserved` carries `required_evidence_missing` at `failure_plane=evidence_boundary`, both invalidating the affected smoke. The `per_arm_ephemeral_root` precommitment alone is not the observation | FR-032, FR-032a |
| `claude_code_subagent_model_unset` | the already-frozen observation, recorded on all three smokes; an adaptive or unpinned smoke that cannot record it true is not reported as demonstrating its behavior | FR-031a.6 |
| `demonstration_state` | a CAR-004-owned closed member — demonstrated or not demonstrated — never a score-plane failure code, since a non-scored row produces no score bundle | FR-031a.7 |
| demonstrated observable | read back from the evidence the run produced, never from the dispatch request: adaptive — served `model`, `effort`, and `candidate_route_id` moving from ladder index i to i + 1; unpinned — served `model` and `effort` equal to the pinned parent session's; orchestration-changing — at least two non-parent unit members with a parent wall time strictly below their summed wall times, a null anywhere in that set recording the demonstration as not made | FR-031, FR-031a.1–5 |

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
entry carries one of `mirror_required`, `car_owned`, or the single sanctioned
divergence — the three FR-034 obligations, none of which is a reconciliation
candidate. [FR-036a]

**The record is not hash-relevant** to any control's or the comparison contract's
content address. [FR-037a]

---

## Requirement coverage index

| Artifact | Requirements it carries |
|---|---|
| `policy-control-registry.schema.json` + its frozen instance | FR-001, FR-002, FR-003, FR-004, FR-006 – FR-018, FR-030 |
| `control-comparison.schema.json` + its frozen instance | FR-002, FR-004, FR-019 – FR-025 |
| `claude_policy_controls.py` | FR-001, FR-002, FR-005, FR-005a, FR-008 – FR-018, FR-026, FR-028, FR-030 – FR-032a |
| `claude_control_comparison.py` | FR-019 – FR-024a |
| `partition-registry-entries.json` | FR-025, FR-027 |
| `control-replay.json` | FR-012a, FR-014a, FR-028, FR-029, FR-027 |
| `run-control-smoke.py` | FR-026a, FR-030 – FR-033 |
| `test-policy-control-contracts.py` | FR-001 – FR-018, FR-026 – FR-032a |
| `test-control-comparison-dominance.py` | FR-019 – FR-024a |
| `test-twin-handoff-completeness.py` | FR-034, FR-034a, FR-035, FR-035a, FR-036, FR-036a, FR-037a |
| `CAR-004-twin-handoff.md` | FR-034 – FR-037a |
| Additive-only discipline, verifiable from the diff alone | FR-004, FR-005, SC-004 |
