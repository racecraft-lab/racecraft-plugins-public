# Tasks: CAR-004 Policy Controls and Adaptive Comparators

**Input**: Design documents from `specs/car-004-policy-controls-comparators/`

**Prerequisites**: [plan.md](./plan.md) (required), [spec.md](./spec.md) (required for user stories),
[research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: TDD-first is explicitly requested by the workflow's Tasks Prompt and by
spec.md's Independent Test. Every implementation task below is immediately preceded by
the test task that must fail first.

**Reviewability**: The plan declares 15 file operations, 0 production files, and one
primary surface (`harness/fixtures`) — at the 15-file warn threshold, below every block
threshold. T004 re-verifies that reading before implementation begins. Task generation
added no file beyond the plan's declared set, so the ratified no-split decision stands.

**Organization**: One user story (US1, P1) — a single vertical slice. Phase 3 is
subdivided into lettered groups that follow the mandated dependency chain:
**contracts → validators → fixtures → guard test → smoke harness → twin-handoff doc**.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel — the task touches files no concurrently-available task
  touches. Within a RED→GREEN pair the order is always strict.
- **[Story]**: `[US1]`. Setup, Foundational, and Polish tasks carry no story label.
- Every task states its exact target path.

## Path Conventions

Repository-only validation assets. No `src/`, no application code, nothing under
`speckit-pro/`.

- Contract schemas: `tests/speckit-pro/layer6-efficiency/contracts-claude/`
- Validators: `tests/speckit-pro/layer6-efficiency/lib/` (`claude_*.py` convention)
- Fixtures: `tests/speckit-pro/layer6-efficiency/fixtures-controls/`
- Unit tests: `tests/speckit-pro/unit/` — **durable filenames, never containing the
  spec ID**. This is machine-enforced: `tests/speckit-pro/unit/test-unit-layout.py`
  derives repository spec families from `.process/` declarations and fails any tracked
  authored filename carrying one.
- Twin-handoff record: `docs/ai/specs/.process/` — **not** the test tree.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a known-green starting point and the one new directory.

- [X] T001 Record the green baseline before any edit: run `python3 tests/speckit-pro/run-all.py --layer 1` and `python3 tests/speckit-pro/run-all.py --layer 4` from the worktree root and confirm both pass. A red baseline is an environment problem, not a CAR-004 finding (quickstart.md §1).
- [X] T002 [P] Create the new fixture directory `tests/speckit-pro/layer6-efficiency/fixtures-controls/`. Git tracks it once the first fixture lands in T039; do not add a placeholder file.
- [X] T003 [P] Verify `tests/speckit-pro/layer6-efficiency/.gitignore` already excludes `results/*` wholesale with a single named allow-rule for the CAR-003 consolidated baseline, confirming CAR-004 needs no `.gitignore` edit because it commits no smoke output. [FR-033]

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Wire the three durable-named unit modules into Layer 4 so that every later
RED failure is observable through the suite runner rather than only in an ad-hoc run.

**CRITICAL**: No Phase 3 work begins until this phase is complete.

- [X] T004 Re-verify the reviewability budget against the planned task and file scope — 15 declared file operations, 0 production files, 1 primary surface (`harness/fixtures`) — and record the unchanged no-split decision in `specs/car-004-policy-controls-comparators/plan.md` under "Budget position and split decision".
- [X] T005 Create importable `unittest` skeletons at `tests/speckit-pro/unit/test-policy-control-contracts.py`, `tests/speckit-pro/unit/test-control-comparison-dominance.py`, and `tests/speckit-pro/unit/test-twin-handoff-completeness.py`. Each resolves `tests/speckit-pro/layer6-efficiency/lib/` on `sys.path` following the existing unit-test precedent, uses behavior-named test methods, and imports nothing beyond the Python 3.11+ standard library.
- [X] T006 Append three `{path, label, baseline: null}` entries to the existing Layer 4 `scripts` array in `tests/speckit-pro/suite-manifest.json` — the layer already declares `dispatch: python-module` at layer level, and script entries carry only those three keys — then confirm `python3 tests/speckit-pro/run-all.py --layer 4` picks them up and stays green.

**Checkpoint**: Layers 1 and 4 green with three registered, empty modules. Every RED task
below is now a suite-visible failure.

---

## Phase 3: User Story 1 - Freeze the policy comparators before the static core exists (Priority: P1) 🎯 MVP

**Goal**: Freeze the three AC-2.17 controls, the comparison rule, the reserved CAR-011
partition, and the messaging consequence as content-addressed, replay-validated,
additive-only contracts — so the CAR-011 comparison is predeclared and tamper-evident.
CAR-004 concludes nothing about dominance.

**Independent Test**: Run the repository suite against the delivered contracts and
fixtures — the control set is closed at three, every control replays deterministically,
the reserved-partition guard fails on a seeded violation and passes on the delivered
evidence, and every dominance verdict state resolves to exactly one permitted claim
class. Then execute the three bounded live smokes once, by hand, on the supported
subscription authentication path. No other CAR spec needs to land first and nothing
shipped to users changes.

---

### Group A — Contract schemas and content addressing *(chain step 1: contracts)*

- [X] T007 [US1] RED — add failing registry document-shape assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: the document loads as JSON, declares its `$id`, `schema_version` const and `status: "frozen"`, sets `additionalProperties: false` on every object, resolves no `$ref` outside its own `#/$defs/`, constrains `controls` to exactly three items, and declares `smoke_bounds` and `car_003_bindings`. [FR-004, SC-017]
- [X] T008 [US1] GREEN — author `tests/speckit-pro/layer6-efficiency/contracts-claude/policy-control-registry.schema.json` per data-model.md §1: the registry envelope, the common control shape with `execution_contract` and `attribution_level`, the three specialization objects (unpinned, adaptive, orchestration-changing), `smoke_bounds`, and `car_003_bindings` as local `#/$defs/binding` `{id, digest}` pairs. [FR-001, FR-003, FR-004, FR-017, FR-018, FR-030]
- [X] T009 [P] [US1] RED — add failing comparison document-shape assertions to `tests/speckit-pro/unit/test-control-comparison-dominance.py`: `$id`, `schema_version`, `status: "frozen"`, `additionalProperties: false`, no `$ref` outside `#/$defs/`, and the declared `eligibility_floors`, `dominance_rule`, `confidence_method`, `multiplicity_position`, `reserved_partition_binding`, `messaging_map`, and `car_003_bindings` blocks. [FR-004, SC-017]
- [X] T010 [P] [US1] GREEN — author `tests/speckit-pro/layer6-efficiency/contracts-claude/control-comparison.schema.json` per data-model.md §2, including the `secondary_control_arm_family` declared beside and disjoint from the frozen analysis plan's three families rather than added to them. [FR-019–FR-025, FR-030a]

---

### Group B — Shared engine, identity, and additive-only enforcement *(chain step 2: validators)*

Every RED task in Groups B and C builds its subject from an **in-test synthetic
instance**, so the tests are independent of the committed fixtures that land in Group E.
Group E then adds committed-instance conformance (T045).

- [X] T011 [US1] RED — add failing fail-closed schema-engine assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: `validate_instance` raises on a `$ref` resolving outside the document's own `#/$defs/`, a missing `required` key, an unexpected key under `additionalProperties: false`, and any `const`, `enum`, `pattern`, `minLength`, `minItems`, or `format: date-time` violation. [FR-004, SC-017]
- [X] T012 [US1] GREEN — implement `ControlContractError`, `load_contract`, and `validate_instance` in `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`, driven from the schema document itself as `lib/claude_trace_schema.py` already does. Python 3.11+ standard library only; no third-party `jsonschema`. [FR-004, research D1]
- [X] T013 [US1] RED — add failing identity and closure assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: every recorded address recomputes under the single frozen preimage rule (`record_digest` over canonical JSON with only the record's own digest member removed); `frozen_at` is a `Z`-suffixed UTC instant and is inside the preimage, so a timestamp-only change moves the address; the registry document and each control carry their own address; the raw-token identity `max_input_tokens + max_cached_input_tokens + max_output_tokens == raw_token_ceiling` holds against the declared member and is refused if it admits `max_cache_read_tokens` or a cache-write class; a seeded fourth control and a duplicate `control_kind` are each refused. [FR-001, FR-002, FR-002a, FR-002b, FR-002c, FR-030a, SC-001, SC-002, SC-012, SC-017]
- [X] T014 [US1] GREEN — implement `control_digest`, `load_registry`, `validate_registry`, and `assert_closed_at_three` in `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`, importing `canonical_json` and `record_digest` read-only from `lib/claude_successor_freeze.py` so one preimage rule governs the whole program. [FR-001, FR-002a, FR-030a, research D3]
- [X] T015 [US1] RED — add failing CAR-003 binding assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: every recorded `{id, digest}` binding recomputes the SHA-256 of the bound document's committed bytes, and a seeded byte change to any bound CAR-003 document fails the check closed rather than passing unnoticed. [FR-005a, SC-018]
- [X] T016 [US1] GREEN — implement the `car_003_bindings` verifier in `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`, keeping the file-bytes digest distinct from the FR-002a record preimage. Bindings are data-level `{id, digest}` pairs, never `$ref`. [FR-004, FR-005, FR-005a, research D2]

---

### Group C — Per-control rules *(chain step 2 continued: validators)*

- [X] T017 [US1] RED — add failing unpinned-control assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: `arm_count` is exactly 1, `model_resolution` is `inherit`, the control binds the already-pinned parent model and effort from the document FR-006 identifies — the Claude-side `environment_contract` object of the frozen experiment-assignment contract, never the shared runtime environment-contract document — and a different pin yields a different `control_digest` rather than a second concurrent arm. [FR-006, FR-007]
- [X] T018 [US1] GREEN — implement the unpinned specialization rules in `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`. [FR-006, FR-007]
- [X] T019 [US1] RED — add failing adaptive signal-map assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: the terminal-state, failure-plane, and failure-code maps are set-equal to the enums read live from `contracts-claude/score-bundle.schema.json`; the mapping is total and single-valued; `signal_precedence` is an ordered array over the closed source set covering every source FR-008 admits including the retry-count and budget-threshold entries, with the always-valued terminal state ranked last so neither trailing source is unreachable, and a seeded array that ranks terminal state ahead of either is refused; the plane map agrees with the code map under the frozen plane derivation and the terminal-state map agrees with it under the frozen candidate-plane pairing; and a seeded membership change on a frozen enum fails closed. [FR-008, FR-009, FR-010, FR-010a, FR-010b, FR-010c, SC-003, SC-021, SC-022]
- [X] T020 [US1] GREEN — implement `validate_signal_maps` and `resolve_response` in `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`, importing the frozen plane derivation read-only from `lib/claude_score_bundle.py` (`FAILURE_PLANE_BY_CODE` / `failure_plane_for`) and deriving the candidate-plane pairing live from the frozen `failure_code` enum in `contracts-claude/score-bundle.schema.json` as `candidate_<state>`, failing closed on a derived code the enum does not carry. That module publishes no terminal-state-keyed map, and none may be added to it. Neither derivation is transcribed. `signal_precedence` is the five-member array of data-model.md §1.3 with terminal state ranked last. Policy responses stay closed at `escalate | hold | non_scorable`. [FR-010a–c, data-model.md §1.3, research D5]
- [X] T021 [US1] RED — add failing `escalation_ladder` assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: exactly one successor-capability freeze is bound by `candidate_freeze_id` and `freeze_digest`; the ladder carries every admitted tuple exactly once; a seeded duplicate, a seeded omission, a within-model position contradicting the frozen closed effort ladder, and a cross-model step with no recorded rationale are each refused; and reordering the ladder yields a new adaptive-control address rather than an in-place edit. [FR-011, FR-011a, FR-011b, SC-014]
- [X] T022 [US1] GREEN — implement `validate_escalation_ladder`, `next_route`, and `previous_route` in `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`. Rank is array position only; `next_route` returns `None` at the ceiling and `previous_route` returns `None` at the floor so wrap-around is refused at both ends. [FR-011, FR-011a, FR-011b, FR-013, research D6]
- [X] T023 [US1] RED — add failing clean-pass streak assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: a clean pass requires `completed`, failure code `none`, zero retries, and no declared budget trigger met; an objective in which the policy escalated never counts; a `non_scorable` objective neither advances nor resets the streak and the streak resumes across it; the streak resets whenever de-escalation is evaluated at a boundary whether or not a step occurs; and a de-escalation due at the first ladder entry records no step and no wrap-around. [FR-012, FR-012a, SC-024]
- [X] T024 [US1] GREEN — implement the clean-pass streak accounting in `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`, with the exclusion of non-scorable objectives taking precedence over the reset-on-non-clean rule. [FR-012, FR-012a]
- [X] T025 [US1] RED — add failing bound-scope and reroute assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: retry and cancellation bounds are counted per objective across every attempt and route, unit-scoped for the orchestration-changing control, and an escalation resets neither counter; a cancellation-bound breach records `cancelled` with `candidate_cancelled` and a retry-bound breach records `failed` with `candidate_failed`; and a `service_reroute` row resolves `non_scorable`, spends no escalation allowance, leaves the ladder position untouched, and makes a whole orchestration unit non-scorable. [FR-014, FR-014a, FR-015, FR-015a, SC-023]
- [X] T026 [US1] GREEN — implement bound evaluation and the frozen `service_reroute` classification in `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`, importing `service_reroute` and its frozen non-scorable disposition reason read-only from `lib/claude_score_bundle.py` rather than coining a signal. [FR-014a, FR-015a]
- [X] T027 [US1] RED — add failing aggregate-fold assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: the additive dimensions sum across the parent and every unit member including children that failed, timed out, or were cancelled; a zero-child run folds to the parent's own values and is valid; aggregate terminal state is the worst-wins fold over a `terminal_state_severity` array validated set-equal (not order-equal) to the frozen enum; acceptance is the parent objective's oracle result, floored to 0 whenever the aggregate state is not `completed`, and null only when the oracle did not run; and no committed fixture row carries a null aggregate acceptance. [FR-016, FR-016a, FR-016b, FR-016c, FR-029, SC-006, SC-015]
- [X] T028 [US1] GREEN — implement `aggregate_objective` and `worst_terminal_state` in `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`, with the `aggregation_rule` required total over all eight Pareto dimensions. [FR-016, FR-016a–c, research D7]
- [X] T029 [US1] RED — add failing unit-membership and topology assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: the unit is the parent node plus the transitive closure of the authored spawn link each non-parent row records, so a nested grandchild is inside it for both the additive sum and the fan-out ceiling; a member recording no terminal state and a member carrying no authored spawn link are each refused rather than folded over; the unit boundary must agree with the frozen `parent_child_graph` wherever a member's evidence binds one, failing closed on disagreement; fan-out is a declared ceiling so a zero-child run conforms while an over-fan-out run is refused; and evidence is attributed at policy level only. [FR-016d, FR-017, FR-017a, FR-018, SC-025]
- [X] T030 [US1] GREEN — implement unit membership and topology conformance in `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`, reading `parent_child_graph` from the shared treatment-record contract and never from the CAR-002 Claude trace contract. [FR-016d, FR-017a, FR-018]
- [X] T031 [US1] RED — add failing raw-token and cache-aggregation assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: all four frozen raw-token members (`input_tokens`, `output_tokens`, `cached_input_tokens`, `reasoning_output_tokens`) sum across the unit; `reasoning_output_tokens` sums but never enters the dominance comparison; cache write sums per frozen TTL class (`ephemeral_5m`, `ephemeral_1h`) under `max_cache_write_tokens_by_ttl_class` and cache read sums under `max_cache_read_tokens`, each keyed identically to the ceiling that bounds it; neither cache quantity becomes a Pareto dimension, enters the raw-token identity, or is constrained against `max_input_tokens`; the `raw_token_ceiling` is read against the three bounded raw-token members alone, `reasoning_output_tokens` being summed and reported under no ceiling; and a member with no cache diagnostic makes that bound unobserved rather than passed or zero. [FR-016e, SC-028]
- [X] T032 [US1] GREEN — implement raw-token and cache-diagnostic aggregation in `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`. [FR-016e]

---

### Group D — Comparison contract validator *(chain step 2 continued: validators)*

This whole group is a lane that runs concurrently with Group C: it touches only
`tests/speckit-pro/unit/test-control-comparison-dominance.py` and
`tests/speckit-pro/layer6-efficiency/lib/claude_control_comparison.py` — files no Group C
task touches. The concurrency is between the two *lanes*, so no task here carries `[P]`:
its siblings share these two files, and within Group D the RED→GREEN order is strict.

- [X] T033 [US1] RED — add failing projection and eligibility assertions to `tests/speckit-pro/unit/test-control-comparison-dominance.py`: `project_resource_vector` renames `duration_ms` to `duration` and raises on any key outside the eight frozen dimensions; `required_gates` is set-equal to the frozen `deterministic_gates.gate` enum; a control that has not cleared every mandatory contract, safety, quality, reliability, and availability gate yields `no_verdict` whatever its resource numbers; and that no-verdict outcome maps inside the eligibility block to `no_comparative_claim` with no messaging restriction, without adding a fourth verdict enum member or a fourth messaging-map row. [FR-019, FR-021e, FR-024a, SC-019]
- [X] T034 [US1] GREEN — implement `ControlComparisonError`, `load_comparison`, `validate_comparison`, `project_resource_vector`, and `check_eligibility_floors` in `tests/speckit-pro/layer6-efficiency/lib/claude_control_comparison.py`, importing the shared schema engine from `claude_policy_controls.py` rather than duplicating it. [FR-019, FR-021e, FR-024a]
- [X] T035 [US1] RED — add failing dominance assertions to `tests/speckit-pro/unit/test-control-comparison-dominance.py`: the three stages run in the frozen order (floors, Pareto, materiality) and the margin test never replaces the Pareto rule; the `margin_map` is total over all eight dimensions with exactly four margin-eligible at 0.10 and four no-worse-only carrying reasons; acceptance is higher-is-better and can only defeat dominance; terminal state is categorical so any difference is inconclusive and the FR-016a severity rank is not read here; the denominator is the comparator's value and a zero comparator records `margin_not_computable` rather than an infinite or 100% improvement; a margin clears only when the one-sided lower confidence bound reaches 0.10, with the replay point estimate standing in on a single synthetic row; and mixed, tied, incomplete, or uncertain comparisons yield `inconclusive`. [FR-020, FR-021, FR-021a–e, FR-022, FR-023, SC-016]
- [X] T036 [US1] GREEN — implement `pareto_verdict`, `materiality_filter`, and `compare` in `tests/speckit-pro/layer6-efficiency/lib/claude_control_comparison.py`. `compare` returns `{verdict, per_component, stage_reached}` with `verdict` closed at `dominant | not_dominant | inconclusive`; no weighted scalar ranking is imported or accepted. [FR-020, FR-021a–e, FR-022, research D8, D9]
- [X] T037 [US1] RED — add failing messaging-map assertions to `tests/speckit-pro/unit/test-control-comparison-dominance.py`: the map is total and single-valued over the three verdict states; `dominant` restricts wording to measured improvement over the previous static baseline, forbids the `efficient`, `optimal`, and `best_measured` classes, and records that the restriction reaches wording alone so the static defaults may still ship for declared operational simplicity; `not_dominant` and `inconclusive` impose no messaging restriction and carry an empty forbidden-class set rather than the `dominant` entry's; and the claim-class lookup is total over every reachable outcome including the eligibility-floor no-verdict outcome while the verdict enum still carries exactly three members. [FR-022, FR-024, FR-024a, SC-008, SC-019]
- [X] T038 [US1] GREEN — implement `claim_class` in `tests/speckit-pro/layer6-efficiency/lib/claude_control_comparison.py`. [FR-024, FR-024a, research D10]

---

### Group E — Frozen instances and replay fixtures *(chain step 3: fixtures)*

- [X] T039 [US1] Author the frozen registry instance `tests/speckit-pro/layer6-efficiency/fixtures-controls/policy-control-registry.json` per data-model.md §1, every required top-level member included — `car_003_bindings` among them: all three controls with their execution contracts, the adaptive `escalation_ladder` with rationales and `de_escalation_clean_pass_threshold: 3`, the orchestration topology descriptor and `terminal_state_severity`, `smoke_bounds` at their frozen values from spec.md Assumptions (`max_attempts: 5`, `max_candidates: 1`, `max_confirmation_entries: 0`, `max_duration_seconds: 1800`, `max_input_tokens: 800000`, `max_cached_input_tokens: 150000`, `max_output_tokens: 50000`, `raw_token_ceiling: 1000000`, `max_cache_read_tokens: 1200000`, `max_cache_write_tokens_by_ttl_class: {ephemeral_5m: 160000, ephemeral_1h: 40000}`), every numeric carrying its unit and comparison direction, and the recorded `registry_digest`, `control_digest`, and `frozen_at` values. That `smoke_bounds` list is the closed bound set: `authentication_mode` and `scored` are **not** `smoke_bounds` members — both belong to a produced smoke record, and a `const "subscription"` bound would restate operator intent and make a refused `api_key` record unrepresentable. Choose no numeric — every value is frozen in the spec. [FR-002, FR-030, FR-030a, FR-030c]
- [X] T040 [P] [US1] Author `tests/speckit-pro/layer6-efficiency/fixtures-controls/partition-registry-entries.json` — the reserved CAR-011 entry (`integrated_confirmation`, qualification-eligible) and the CAR-004 smoke entry (`calibration`, never qualification-eligible), both produced by the frozen `build_partition_registry_entry` and registered through `register_partitions` in `lib/claude_experiment_policy.py`, both recording `owning_spec: "CAR-004"`. No new schema and no new partition type is coined. [FR-025, FR-025a, FR-025b, FR-025d, research D4]
- [X] T041 [US1] Author the frozen comparison instance `tests/speckit-pro/layer6-efficiency/fixtures-controls/control-comparison.json` per data-model.md §2, every required top-level member included — `eligibility_floors`, `dominance_rule` with its margin map, `messaging_map`, and `car_003_bindings` alongside the three named below — and whose `reserved_partition_binding` pins the T040 reserved entry's `partition_id` together with its membership digest — the digest over the deduplicated, lexicographically sorted objective identifiers — and whose `confidence_method` and `multiplicity_position` carry alpha 0.05, confidence level 0.95, `cluster_robust_sandwich_variance_by_role`, and `holm_bonferroni_within_the_secondary_control_arm_family`. [FR-023, FR-025c]
- [X] T042 [P] [US1] Author `tests/speckit-pro/layer6-efficiency/fixtures-controls/control-replay.json` — the nine deterministic cases in data-model.md §4, of which cases 7 and 8 are the two FR-014a bound-breach paths and case 9 is a streak that survives and completes across an excluded non-scorable objective; those three are required by requirement, not by preference. Every value is literal: no run-time timestamps, no randomness, no absolute paths, no session identifiers. The multi-child orchestration case is required. [FR-012a, FR-014a, FR-028, FR-029, SC-006, SC-015]
- [X] T043 [US1] RED — add failing replay assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: `replay()` digested over two runs yields the same value; every fixture row carries `scored: false`; zero rows are outcome-bearing; and no row references a selection, confirmation, or reserved-partition objective. [FR-027, FR-028, SC-005, SC-010]
- [X] T044 [US1] GREEN — implement `replay()` in `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`, returning a deterministic list that validates each row through the schema engine. [FR-028]
- [X] T045 [US1] Add committed-instance conformance assertions — `load_registry()` validates `fixtures-controls/policy-control-registry.json` in `tests/speckit-pro/unit/test-policy-control-contracts.py`, and `load_comparison()` validates `fixtures-controls/control-comparison.json` in `tests/speckit-pro/unit/test-control-comparison-dominance.py` — with every recorded digest recomputed and matched against the committed bytes. [SC-012, SC-017]

---

### Group F — Reserved-partition guard *(chain step 4: guard test)*

- [X] T046 [US1] RED — add failing partition-guard assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: `assert_reserved_partition_untouched` fails on a seeded replay row and on a seeded smoke row referencing a reserved objective and passes on the delivered evidence set; `register_partitions` fails closed on a seeded duplicate partition identifier and on a seeded shared objective; the frozen builder refuses `calibration` paired with `qualification_eligible: true`; and both entries record `owning_spec: "CAR-004"`. [FR-025a–d, FR-026, SC-007, SC-020]
- [X] T047 [US1] GREEN — implement `assert_reserved_partition_untouched` in `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`, covering replay rows and smoke rows through one entry point. [FR-026]

---

### Group G — Bounded smoke harness *(chain step 5: smoke harness)*

- [X] T048 [US1] RED — add failing smoke-record assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: `validate_smoke_record` refuses a record whose observed `authentication_mode` is `api_key` while still recording the observed value alongside the refusal so a refused run stays distinguishable from one that never ran; refuses `scored` other than `false`; refuses any reserved-partition reference; refuses a consumed budget exceeding any frozen bound; reads all four bounds over the parent-plus-children unit; reads the 30-minute cap as elapsed wall clock rather than the additive `duration_ms`; and counts no child dispatch as an objective attempt. The mode is read from the Claude-side frozen member enumerated `subscription | api_key`, never the shared member enumerated `chatgpt_subscription | api_key`. [FR-027, FR-030, FR-030b, FR-030c, SC-009, SC-029, SC-030]
- [X] T049 [US1] GREEN — implement `validate_smoke_record` in `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`. [FR-030, FR-030b, FR-030c]
- [X] T050 [US1] RED — add failing demonstration and cache-isolation assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: every observable is read back from run evidence and never from the dispatch request; the adaptive smoke shows served `model`, `effort`, and `candidate_route_id` moving from ladder index i to i + 1; the unpinned smoke shows a served model and effort equal to the pinned parent session's; the orchestration smoke shows at least two non-parent unit members with a parent wall time strictly below their summed wall times, with a null wall time anywhere recording the demonstration as not made rather than as passed; every smoke records the frozen `claude_code_subagent_model_unset` observation and an adaptive or unpinned smoke that cannot record it true is not reported as demonstrating its behavior; an unevidenced demonstration is recorded as not demonstrated and never relabeled; and all three unordered arm pairs record `observed_disjoint` with both root digests present and no root recorded as a filesystem path, while a seeded `observed_shared` carries the frozen `infrastructure_failure` code and a seeded `unobserved` carries the frozen `required_evidence_missing` code, each invalidating the affected smoke. [FR-031, FR-031a, FR-032, FR-032a, SC-026, SC-027, SC-031]
- [X] T051 [US1] GREEN — implement demonstration-state and cache-isolation evaluation in `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`, reading `observed_cache_isolation` and its closed status set live from the frozen cache diagnostic rather than restating them. [FR-031a, FR-032a, research D11]
- [X] T052 [US1] RED — add failing smoke-driver assertions to `tests/speckit-pro/unit/test-policy-control-contracts.py`: `--plan` derives its objective list from the registered CAR-004 smoke partition and refuses to emit any objective the frozen consumption path does not admit, so a reserved objective never reaches an operator; `--seal` refuses any record `validate_smoke_record` refuses; and accepted records are written under the git-ignored `results/` directory. [FR-026a, FR-033, SC-007]
- [X] T053 [US1] GREEN — author `tests/speckit-pro/layer6-efficiency/run-control-smoke.py` following the `run-calibration-pilot.py` precedent: operator-only, live, therefore deliberately **not** registered in `tests/speckit-pro/suite-manifest.json`, with its deterministic logic covered from `test-policy-control-contracts.py`. Accepts `--control <unpinned|adaptive|orchestration-changing>` with `--plan` or `--seal <record>`. [FR-026a, FR-030–FR-033]

---

### Group H — Twin-handoff record *(chain step 6: twin-handoff doc)*

This whole group is a lane that runs concurrently with Groups F and G: it touches only
`tests/speckit-pro/unit/test-twin-handoff-completeness.py` and
`docs/ai/specs/.process/CAR-004-twin-handoff.md` — files no Group F or G task touches.
The concurrency is between the lanes, so no task here carries `[P]`: its siblings share
these two files, and within Group H the order is strict. Group H
depends on Groups A–E only, since categories 1–6 derive from the committed contract
documents and registry entries and need neither the guard test nor the smoke harness.

- [X] T054 [US1] RED — add failing completeness assertions to `tests/speckit-pro/unit/test-twin-handoff-completeness.py`: categories 1 through 6 re-derive from the committed contract documents and registry entries and diff to zero differences in **both** directions — a delivered member absent from the record and a recorded member absent from the artifacts each fail; every entry carries exactly one mirror obligation drawn from `mirror_required | sanctioned_divergence | car_owned` and an entry with none or more than one is rejected, all three obligations being publishable since none of them is a reconciliation candidate; the sanctioned-divergence set is closed at exactly one entry and a second divergence, or one classified against a contract document, declared member, frozen numeric, or decision-semantics entry, fails; and the reconciliation candidate list is explicitly stated empty. [FR-034, FR-034a, FR-035, FR-035a, FR-036a, SC-011]
- [X] T055 [US1] Implement the category 1–6 re-derivation and the both-directions diff inside `tests/speckit-pro/unit/test-twin-handoff-completeness.py` — durable filename, Python 3.11+ standard library only, no new Bash or `jq` dependency. [FR-034a, research D12]
- [X] T056 [US1] Author `docs/ai/specs/.process/CAR-004-twin-handoff.md` categories 1 through 6 — contract documents by `$id`, `schema_version`, and committed-bytes SHA-256; declared members by JSON Pointer with their `required` subsets; closed enumerations with every member; stable identifiers; bindings into frozen CAR-003 contracts; and frozen numerics with unit and comparison direction — until T054 and T055 pass. [FR-034, SC-011]
- [X] T057 [US1] Author the remainder of `docs/ai/specs/.process/CAR-004-twin-handoff.md`: category 7 decision semantics (row-resolution precedence, the two map-consistency rules, the ordered route sequence, clean-pass streak accounting, bound scope and breach outcomes, the reroute observable, unit membership and its agreement with the frozen parent-child graph, the aggregation rules including the reasoning member and both cache quantities with the unobserved-not-zero disposition, smoke-bound scope and the elapsed wall-clock reading, the read-back rule and three exact-treatment observables, the constraining authentication-mode reading, the pairwise cache-isolation observable, the eligibility floors, the materiality margin test, and the verdict-to-claim-class mapping), category 8 enforcement guards, the single sanctioned-divergence entry reachable without opening either roadmap, the explicitly empty reconciliation candidate list, the publication date, and the reference by which the G56R-004 owner was notified. The record is not a hash-relevant input to any content address. [FR-034, FR-035, FR-036, FR-036a, FR-037, FR-037a, SC-013]

**Checkpoint**: User Story 1 is complete and independently testable. `--layer 1` and
`--layer 4` are green, and the three bounded live smokes remain the only manual step.

---

## Phase 4: Polish & Cross-Cutting Concerns

- [X] T058 Run the full gate `python3 tests/speckit-pro/run-all.py` from the worktree root and confirm every layer passes.
- [X] T059 Regenerate the docs reference: `pnpm --dir docs-site install` once per worktree, then `pnpm --dir docs-site reference:generate`, and commit `docs-site/src/content/docs/reference/tests.md`. New `.py` files under `tests/speckit-pro/` stale it and CI's validate-docs job runs `reference:check` against it. Requires Node 22.12 or newer.
- [ ] T060 [P] Verify additive-only discipline and untracked smoke output from the change set alone: `git diff --name-status origin/main...HEAD -- tests/speckit-pro/layer6-efficiency/contracts-claude/` shows exactly two `A` lines and zero `M` lines, the same command against `tests/speckit-pro/layer6-efficiency/lib/` shows two `A` and zero `M`, and `git status --porcelain tests/speckit-pro/layer6-efficiency/results/` prints nothing. [FR-005, FR-033, SC-004]
- [ ] T061 Walk `specs/car-004-policy-controls-comparators/quickstart.md` sections 1 through 4 end to end and confirm every expected outcome in the section 3 table.
- [ ] T062 Execute the three bounded live smokes per `specs/car-004-policy-controls-comparators/quickstart.md` §5 — developer-local, never CI, in sequence, each under its own ephemeral cache root, on the supported subscription authentication path with no API key. Then confirm every row of the §5 post-run verification table from the three sealed records rather than from memory: the four bounds over the unit, each named observable read back from run evidence, the frozen no-subagent-override observation on all three, the observed `subscription` mode, and `observed_disjoint` on all three unordered arm pairs. Commit nothing from `tests/speckit-pro/layer6-efficiency/results/`. [FR-030, FR-030b, FR-030c, FR-031, FR-031a, FR-032, FR-032a, FR-033, SC-009, SC-026, SC-027, SC-029, SC-030, SC-031]
- [ ] T063 Generate the PR review packet into the untracked `specs/car-004-policy-controls-comparators/.process/pr-packets/` directory, following the packet layout the other CAR specs use, from the "PR review packet source" table in `specs/car-004-policy-controls-comparators/plan.md` — review order, scope budget, traceability, verification evidence, known gaps, and the no-flag rollback note — and validate the exact final PR title against the repository release-readiness gate (`<type>(<lowercase-scope>): <plain English description>`).
- [ ] T064 [P] Re-run the authoritative reviewability gate in diff mode (`runner helper reviewability-gate`) against the actual change set, confirm the primary surface is still `harness/fixtures` with zero production files, and record the result in `specs/car-004-policy-controls-comparators/plan.md` under "Reviewability Budget".

---

## Out-of-Scope Boundary (bounded generation)

Task generation was bounded by spec.md's Out of Scope section and the design concept's
Non-goals. **Zero generated tasks cross the boundary.** Each item below was checked and
produced no task:

| Boundary | Why no task exists |
|---|---|
| Concluding dominance | T033–T038 build and validate the comparison *rule*. No task computes or records a CAR-004 verdict about which side wins. |
| Any production adaptive-routing or orchestration feature | Nothing under `speckit-pro/` is touched. Every deliverable is an evaluation fixture, validator, or record under `tests/speckit-pro/` and `docs/ai/specs/.process/`. |
| Edits to frozen CAR-003 schemas | T016 verifies bindings by recomputing committed-bytes digests; T060 proves zero `M` lines under `contracts-claude/`. Frozen modules are imported read-only in T014, T020, T026, T040, and T051. |
| New telemetry fields | T019 binds every adaptive signal to an already-published frozen member; T026 uses the frozen `service_reroute` code; T050 uses the frozen `observed_cache_isolation` object and `claude_code_subagent_model_unset` observation. |
| An unpinned-control matrix over multiple parent sessions | T017/T018 freeze `arm_count: 1`; a different pin is a new control version, not a second arm. |
| Scored smoke rows and scored mini-campaigns | T043 and T048 assert `scored: false` and zero outcome-bearing rows; T040 registers the smoke partition as `calibration` with `qualification_eligible: false`, which the frozen builder refuses to invert. |

**Authentication note**: T048, T050, and T062 follow the design concept's `## Revisions`
correction of 2026-07-27 — the smoke runs on the **subscription** path and must never
require an API key, per PRD `AC-2.19` as amended 2026-07-26. The technical roadmap is
known stale on this point (lines 159-160, 359-360, 1110) and was deliberately not
followed.

---

## Declared File Operation Coverage

Every one of the plan's fifteen declared file operations has at least one covering task.

| # | Declared file operation | Covering tasks |
|---|---|---|
| 1 | NEW `tests/speckit-pro/layer6-efficiency/contracts-claude/policy-control-registry.schema.json` | T008 |
| 2 | NEW `tests/speckit-pro/layer6-efficiency/contracts-claude/control-comparison.schema.json` | T010 |
| 3 | NEW `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py` | T012, T014, T016, T018, T020, T022, T024, T026, T028, T030, T032, T044, T047, T049, T051 |
| 4 | NEW `tests/speckit-pro/layer6-efficiency/lib/claude_control_comparison.py` | T034, T036, T038 |
| 5 | NEW `tests/speckit-pro/layer6-efficiency/fixtures-controls/policy-control-registry.json` | T039 |
| 6 | NEW `tests/speckit-pro/layer6-efficiency/fixtures-controls/control-comparison.json` | T041 |
| 7 | NEW `tests/speckit-pro/layer6-efficiency/fixtures-controls/partition-registry-entries.json` | T040 |
| 8 | NEW `tests/speckit-pro/layer6-efficiency/fixtures-controls/control-replay.json` | T042 |
| 9 | NEW `tests/speckit-pro/layer6-efficiency/run-control-smoke.py` | T053 |
| 10 | NEW `tests/speckit-pro/unit/test-policy-control-contracts.py` | T005, T007, T011, T013, T015, T017, T019, T021, T023, T025, T027, T029, T031, T043, T045, T046, T048, T050, T052 |
| 11 | NEW `tests/speckit-pro/unit/test-control-comparison-dominance.py` | T005, T009, T033, T035, T037, T045 |
| 12 | NEW `tests/speckit-pro/unit/test-twin-handoff-completeness.py` | T005, T054, T055 |
| 13 | MODIFIED `tests/speckit-pro/suite-manifest.json` | T006 |
| 14 | NEW `docs/ai/specs/.process/CAR-004-twin-handoff.md` | T056, T057 |
| 15 | MODIFIED `docs-site/src/content/docs/reference/tests.md` | T059 |

Supporting directory: `tests/speckit-pro/layer6-efficiency/fixtures-controls/` (T002).
No task creates a file outside this table. T004 and T064 edit this feature's own
`specs/car-004-policy-controls-comparators/plan.md`, and T063 writes its packet under the
untracked `specs/car-004-policy-controls-comparators/.process/pr-packets/`; in-feature
spec artifacts and `.process/` output sit outside the declared change-set budget by
convention, which is why neither appears above.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup. **Blocks all of Phase 3** — the manifest
  registration is what makes each RED failure suite-visible.
- **User Story 1 (Phase 3)**: depends on Foundational.
- **Polish (Phase 4)**: depends on Phase 3 completing.

### Group Chain (mandated dependency order)

```text
A. contracts (T007–T010)
      ↓
B. validators — engine, identity, additive-only (T011–T016)
      ↓
C. validators — per-control rules (T017–T032)   ║   D. validators — comparison (T033–T038)
      ↓                                          ║              ↓
      └──────────────── E. fixtures (T039–T045) ─┘
                              ↓
      ┌───────────────────────┴───────────────────────┐
      ↓                                               ↓
F. guard test (T046–T047)                   H. twin-handoff doc (T054–T057)
      ↓
G. smoke harness (T048–T053)
```

Groups C and D are file-disjoint lanes and run concurrently. Group H is file-disjoint from
F and G and branches off E rather than off F: it depends on A–E because categories 1–6
derive from the committed contract documents and registry entries, and on nothing later.

### Within Each Group

- Every RED task must be written and **observed failing** before its GREEN task.
- Contracts before validators; validators before fixtures; fixtures before the guard test;
  the guard test before the smoke harness. Group G depends on A–F; Group H depends on A–E
  alone, and the two run concurrently with each other — the group chain diagram above is
  authoritative on that pair, and neither one precedes the other.
- Tasks touching the same file are strictly sequential, so `[P]` is never applied to a
  task whose file another concurrently-available task touches. Lane-level concurrency —
  Group C against D, Group H against F and G — is carried by the group chain diagram and
  the group headers instead of by the marker.

### Parallel Opportunities

- **8 tasks are marked `[P]`**: T002, T003, T009, T010, T040, T042, T060, T064. Every one
  of them targets a file no other concurrently-available task targets, which is the whole
  meaning of the marker; lane-level concurrency is not expressed with it.
- The two contract schemas (T008, T010) and their document-shape tests (T007, T009) sit in
  two disjoint files each.
- After T040, the comparison instance (T041) and the replay fixture (T042) are disjoint.
- `tests/speckit-pro/unit/test-policy-control-contracts.py` and
  `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py` are the two
  highest-traffic files. **No task touching either is ever marked `[P]`.**

---

## Parallel Example: Groups C and D

```bash
# Two file-disjoint lanes, concurrent:
Lane 1 (Group C): "RED adaptive signal maps in tests/speckit-pro/unit/test-policy-control-contracts.py"
Lane 2 (Group D): "RED projection and eligibility in tests/speckit-pro/unit/test-control-comparison-dominance.py"

# Two disjoint contract documents, concurrent:
Task T008: "Author tests/speckit-pro/layer6-efficiency/contracts-claude/policy-control-registry.schema.json"
Task T010: "Author tests/speckit-pro/layer6-efficiency/contracts-claude/control-comparison.schema.json"
```

---

## Implementation Strategy

### MVP scope

User Story 1 **is** the MVP and the whole feature. The plan's ratified split decision is
no split: the three controls, the comparison rule, the reserved partition, and the
twin-handoff record are one freeze. Shipping half would publish a comparator set CAR-011
could not apply and would leave the un-frozen half authorable after the static core's
results are visible — the exact failure this feature exists to prevent.

### Sequence

1. Phase 1 Setup → green baseline recorded.
2. Phase 2 Foundational → three modules registered, RED failures now suite-visible.
3. Phase 3 Groups A → B → (C ∥ D) → E → (F → G) ∥ H.
4. **STOP and VALIDATE**: `python3 tests/speckit-pro/run-all.py` green; quickstart §1–4 clean.
5. Phase 4 Polish, ending with the three developer-local live smokes and the PR packet.

---

## Notes

- `[P]` = different files, no incomplete dependencies. Where a whole group is
  file-disjoint from another and the two lanes run concurrently, the group header and the
  chain diagram say so; the marker is never used for that.
- Verify every RED task actually fails before writing its GREEN counterpart. A RED task
  that passes on first run means the assertion is not testing what it claims.
- Commit after each RED→GREEN pair or logical group.
- Frozen enums, derivations, and constants are read **live** from their committed sources
  and never transcribed into Python — that is what makes FR-010a fail closed on an
  upstream membership change instead of absorbing it.
- Every value inside a hash-relevant object is frozen in spec.md. Implementation chooses
  no numeric.
- Unit test filenames must never contain the spec ID. `tests/speckit-pro/unit/test-unit-layout.py`
  enforces this mechanically against spec families derived from `.process/` declarations.
- The twin-handoff record belongs in `docs/ai/specs/.process/`, never in the test tree.
- Do not expand this task list past the reviewability budget. If new work appears, split
  the spec rather than adding implementation tasks.
