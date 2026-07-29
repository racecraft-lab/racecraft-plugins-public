# Contract: validator module API

The two new modules under `tests/speckit-pro/layer6-efficiency/lib/` are the
programmatic interface the unit tests, the smoke script, and any later CAR spec
import. Every entrypoint is **fail-closed**: it raises on the first violation and
never returns a partial verdict, matching the `validate_manifest` idiom the
CAR-001 and CAR-003 modules already use.

Naming follows the `claude_*.py` convention. Neither module makes a live model
call; both are repository-only harness code on the Python 3.11+ standard library.

---

## `claude_policy_controls.py`

Owns the shared fail-closed schema engine plus every registry and control rule.
The engine lives here rather than in a module of its own because it has exactly
two in-tree callers, which is the same reason `claude_successor_freeze.py` owns
`canonical_json` and `record_digest` for the whole program.

```python
class ControlContractError(AssertionError): ...

# --- shared schema engine (imported by claude_control_comparison) ---
def load_contract(path: Path) -> dict[str, Any]: ...
def validate_instance(instance: Any, schema: dict, *, path: str = "") -> Any: ...

# --- registry and identity ---
def load_registry(path: Path = FROZEN_REGISTRY_PATH) -> dict[str, Any]: ...
def validate_registry(registry: Mapping[str, Any]) -> Mapping[str, Any]: ...
def control_digest(control: Mapping[str, Any]) -> str: ...
def assert_closed_at_three(registry: Mapping[str, Any]) -> None: ...
def verify_car_003_bindings(document: Mapping[str, Any]) -> None: ...

# --- adaptive control ---
def validate_escalation_ladder(control, freeze) -> None: ...
def validate_signal_maps(control) -> None: ...
def resolve_response(control, row) -> str: ...        # escalate | hold | non_scorable
def next_route(control, current_route_id) -> str | None: ...
def previous_route(control, current_route_id) -> str | None: ...
def advance_clean_streak(control, state, objective) -> dict[str, Any]: ...
def evaluate_bounds(control, objective) -> dict[str, Any]: ...

# --- orchestration-changing control ---
def unit_members(rows, control) -> list[Mapping[str, Any]]: ...
def aggregate_objective(parent, children, control) -> dict[str, Any]: ...
def worst_terminal_state(states, severity_order) -> str: ...
def aggregate_raw_tokens_and_cache(members, control) -> dict[str, Any]: ...

# --- evidence and partitions ---
def assert_reserved_partition_untouched(rows, reserved_entry) -> None: ...
def validate_smoke_record(record, registry) -> Mapping[str, Any]: ...
def evaluate_demonstration(record, registry) -> dict[str, Any]: ...
def evaluate_cache_isolation(series) -> dict[str, Any]: ...
def replay(fixture_path: Path) -> list[dict[str, Any]]: ...
```

**Behavioral contract:**

| Function | Raises when | Requirement |
|---|---|---|
| `validate_instance` | any `$ref` resolves outside the document's own `#/$defs/`; any required key missing; any unexpected key under `additionalProperties: false`; any `const`, `enum`, `pattern`, `minLength`, `minItems`, or `format: date-time` violation | FR-004, SC-017 |
| `assert_closed_at_three` | the registry carries other than three controls, or two share a `control_kind` | FR-001, SC-001 |
| `validate_registry` | any recorded digest does not recompute; `frozen_at` is not a `Z`-suffixed UTC instant; the three raw-token sub-budgets (`max_input_tokens`, `max_cached_input_tokens`, `max_output_tokens`) do not sum to the declared `raw_token_ceiling` member, or the identity admits `max_cache_read_tokens` or a cache-write class; any smoke-bound member is missing a frozen value, a unit, or a direction | FR-002, FR-030, FR-030a, SC-012, SC-017 |
| `verify_car_003_bindings` | any recorded `{id, digest}` binding's digest does not match the SHA-256 of the bound document's committed bytes — the file-bytes digest, kept distinct from the FR-002a record preimage — so a seeded byte change to a frozen CAR-003 document fails closed | FR-005, FR-005a, SC-018 |
| `validate_escalation_ladder` | more than one freeze bound; an entry outside `admitted_tuples`; a duplicate; an omission; a within-model pair contradicting the frozen effort ladder; a cross-model step with no rationale | FR-011a, SC-014 |
| `validate_signal_maps` | any of the three maps is not set-equal to its frozen enum; any signal resolves to more than one response; `signal_precedence` omits a source FR-008 admits, is not the frozen ordered array over the closed five-member source set, or does not rank the always-valued terminal state last; the plane map disagrees with the code map under the plane derivation imported from `claude_score_bundle.py`; the terminal-state map disagrees with it under the candidate-plane pairing derived live from the frozen `failure_code` enum as `candidate_<state>`, or a derived code is absent from that enum | FR-010, FR-010a, FR-010b, FR-010c, SC-003, SC-021, SC-022 |
| `next_route` | never raises; returns `None` at the ceiling so the caller records no escalation and refuses wrap-around | FR-011b, FR-013 |
| `previous_route` | never raises; returns `None` at the floor, so a de-escalation due at the first entry records no step and no wrap-around while the streak still resets | FR-011b, FR-012a.5 |
| `advance_clean_streak` | never raises; an escalating objective never counts; a `non_scorable` objective leaves the streak unchanged and the streak resumes across it; reaching three resets the counter at that boundary whether or not a step occurs | FR-012, FR-012a, SC-024 |
| `evaluate_bounds` | a bound is counted over a scope other than the declared `counted_over`; an escalation reset either counter; a breach records anything but the declared `on_breach` terminal state and its frozen candidate-plane failure code | FR-014, FR-014a, SC-023 |
| `unit_members` | a unit member records no terminal state; a row is neither the parent's own nor carries an authored spawning identifier; the induced membership disagrees with a bound frozen `parent_child_graph`; the unit exceeds the declared fan-out ceiling | FR-016d, FR-017a, SC-025 |
| `aggregate_objective` | `aggregation_rule` omits a dimension; `terminal_state_severity` is not set-equal to the frozen enum; an aggregate acceptance is non-zero while the aggregate terminal state is not `completed`; a `service_reroute` anywhere in the unit is folded away rather than making the whole unit non-scorable | FR-015a.3, FR-016, FR-016a, FR-016b, FR-016c, SC-015 |
| `aggregate_raw_tokens_and_cache` | a raw-token member is omitted from the four-member sum; `reasoning_output_tokens` enters the dominance comparison, the raw-token identity, or the quantity the `raw_token_ceiling` is read against — that quantity being the three bounded members alone; a cache quantity is keyed differently from the ceiling that bounds it (`max_cache_read_tokens` for cache read, the same closed TTL class space for cache write), is constrained against `max_input_tokens`, or is read as zero when a unit member recorded no diagnostic instead of reporting the bound unobserved | FR-016e, FR-030b, SC-028 |
| `assert_reserved_partition_untouched` | any row — replay **or** smoke — references a reserved objective id | FR-026, SC-007 |
| `validate_smoke_record` | `scored` is not `false`; any consumed budget member exceeds its frozen bound when read over the parent-plus-children unit; the wall clock is read as the additive `duration_ms` rather than as elapsed; a child dispatch is counted as an objective attempt; the record names the reserved partition. An observed `authentication_mode` of `api_key` is **not** a schema violation: the record is marked inadmissible as FR-031 evidence with the observed value retained and a refusal reason recorded, so a refused run stays distinguishable from one that never ran | FR-027, FR-030, FR-030b, FR-030c, SC-009, SC-010, SC-029, SC-030 |
| `evaluate_demonstration` | never raises; returns the demonstration state read back from run evidence rather than from the dispatch request. A missing observable, a null wall time anywhere in the compared set, or a smoke that cannot record `claude_code_subagent_model_unset` true yields *not demonstrated*, counted toward neither FR-031 nor SC-009 and never relabeled | FR-031, FR-031a, SC-026, SC-027 |
| `evaluate_cache_isolation` | fewer than all three unordered arm pairs recorded; a pair missing either root digest; a root recorded as a filesystem path; the `per_arm_ephemeral_root` precommitment offered as the observation. `observed_shared` and `unobserved` invalidate the affected smoke under their frozen codes and planes rather than warning | FR-032, FR-032a, SC-031 |
| `replay` | any fixture row fails schema validation or references a reserved objective | FR-026, FR-028 |

`replay()` returns a deterministic list; digesting its output twice yields the
same value, which is how SC-005's byte-identical claim is tested rather than
asserted.

---

## `claude_control_comparison.py`

```python
class ControlComparisonError(AssertionError): ...

def load_comparison(path: Path = FROZEN_COMPARISON_PATH) -> dict[str, Any]: ...
def validate_comparison(contract: Mapping[str, Any]) -> Mapping[str, Any]: ...

def project_resource_vector(resource_vector: Mapping[str, Any]) -> dict[str, Any]: ...
def check_eligibility_floors(arm, contract) -> bool: ...
def pareto_verdict(candidate, comparator, contract) -> str: ...
def materiality_filter(candidate, comparator, contract) -> dict[str, Any]: ...
def compare(candidate, comparator, contract) -> dict[str, Any]: ...
def claim_class(verdict: str, contract) -> dict[str, Any]: ...
```

**Behavioral contract:**

| Function | Behavior | Requirement |
|---|---|---|
| `project_resource_vector` | renames `duration_ms` to `duration`; raises on any key outside the eight frozen dimensions | FR-021e |
| `check_eligibility_floors` | returns `False` unless every mandatory contract, safety, quality, reliability, and availability gate passed; `compare` then returns no verdict | FR-019 |
| `pareto_verdict` | returns `candidate_dominant`, `comparator_dominant`, `tied`, or `mixed`; imports no weights and accepts none | FR-020 |
| `materiality_filter` | reached only on `candidate_dominant`; per component returns `cleared`, `not_cleared`, or `margin_not_computable`; the denominator is the comparator's value; a clear requires the one-sided lower bound to reach 0.10 | FR-021, FR-021c, FR-021d |
| `compare` | runs the three stages in the frozen order and returns `{verdict, per_component, stage_reached}` with `verdict` in `dominant \| not_dominant \| inconclusive` | FR-021a, FR-022 |
| `claim_class` | total over the three verdicts **and** over the eligibility-floor no-verdict outcome; returns the permitted class plus a `messaging_restriction` flag. Only `dominant` carries a forbidden set and a `true` flag, and its entry also records that the restriction reaches release wording alone — the static defaults may still ship for declared operational simplicity. `not_dominant`, `inconclusive`, and the no-verdict outcome return `no_comparative_claim` with an empty forbidden set and a `false` flag | FR-022, FR-024, FR-024a, SC-008, SC-019 |

`compare` returns `inconclusive` — never a partial or directional dominance —
whenever the comparison is mixed, tied, incomplete, or statistically uncertain,
and `claim_class("inconclusive")` imposes no messaging restriction. [FR-022]

---

## `run-control-smoke.py` (operator entry point, not suite-registered)

Follows the `run-calibration-pilot.py` precedent: live and operator-only,
therefore absent from `suite-manifest.json`, with its deterministic logic covered
from `test-policy-control-contracts.py`.

```text
python3 tests/speckit-pro/layer6-efficiency/run-control-smoke.py \
    --control <unpinned|adaptive|orchestration-changing> [--plan | --seal <record>]
```

- `--plan` prints the bounded command set for one control and exits without
  running anything. Its objective list is derived from the registered CAR-004
  smoke partition, and it refuses to emit any objective the frozen consumption
  path does not admit, so a reserved objective never reaches an operator.
  [FR-026a]
- `--seal` validates a produced record through
  `claude_policy_controls.validate_smoke_record` and writes it under the
  git-ignored `results/` directory.
- The script refuses to seal a record as FR-031 evidence when its observed
  `authentication_mode` is `api_key`, when `scored` is not `false`, when its rows
  reference a reserved objective, or when its consumed budget exceeds any frozen
  bound. [FR-026a, FR-030, FR-033]
- A refusal is **not** a discard. The refused record is still written under
  `results/` carrying its observed values — the observed `api_key` included — and
  its refusal reason, so a refused run stays distinguishable from one that never
  ran, and the remedy is a re-run rather than a relabel. Nothing under `results/`
  is committed either way. [FR-030c.3, FR-033]
