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

# --- adaptive control ---
def validate_escalation_ladder(control, freeze) -> None: ...
def validate_signal_maps(control) -> None: ...
def resolve_response(control, row) -> str: ...        # escalate | hold | non_scorable
def next_route(control, current_route_id) -> str | None: ...
def previous_route(control, current_route_id) -> str | None: ...

# --- orchestration-changing control ---
def aggregate_objective(parent, children, control) -> dict[str, Any]: ...
def worst_terminal_state(states, severity_order) -> str: ...

# --- evidence and partitions ---
def assert_reserved_partition_untouched(rows, reserved_entry) -> None: ...
def validate_smoke_record(record, registry) -> Mapping[str, Any]: ...
def replay(fixture_path: Path) -> list[dict[str, Any]]: ...
```

**Behavioral contract:**

| Function | Raises when | Requirement |
|---|---|---|
| `validate_instance` | any `$ref` resolves outside the document's own `#/$defs/`; any required key missing; any unexpected key under `additionalProperties: false`; any `const`, `enum`, `pattern`, `minLength`, `minItems`, or `format: date-time` violation | FR-004, SC-017 |
| `assert_closed_at_three` | the registry carries other than three controls, or two share a `control_kind` | FR-001, SC-001 |
| `validate_registry` | any recorded digest does not recompute; `frozen_at` is not a `Z`-suffixed UTC instant; the raw-token identity does not sum to 1,000,000 | FR-002, FR-030, SC-012, SC-017 |
| `validate_escalation_ladder` | more than one freeze bound; an entry outside `admitted_tuples`; a duplicate; an omission; a within-model pair contradicting the frozen effort ladder; a cross-model step with no rationale | FR-011a, SC-014 |
| `validate_signal_maps` | any of the three maps is not set-equal to its frozen enum; any signal resolves to more than one response; `signal_precedence` is not the frozen array | FR-010, SC-003 |
| `next_route` | never raises; returns `None` at the ceiling so the caller records no escalation and refuses wrap-around | FR-011b, FR-013 |
| `aggregate_objective` | `aggregation_rule` omits a dimension; `terminal_state_severity` is not set-equal to the frozen enum; an aggregate acceptance is non-zero while the aggregate terminal state is not `completed` | FR-016, FR-016a, FR-016b, SC-015 |
| `assert_reserved_partition_untouched` | any row — replay **or** smoke — references a reserved objective id | FR-026, SC-007 |
| `validate_smoke_record` | `authentication_mode` is not `subscription`; `scored` is not `false`; any consumed budget member exceeds its frozen bound; the record names the reserved partition | FR-027, FR-030, SC-009, SC-010 |
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
| `claim_class` | total over the three verdicts; returns the permitted class and the forbidden classes | FR-024, SC-008 |

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
  running anything.
- `--seal` validates a produced record through
  `claude_policy_controls.validate_smoke_record` and writes it under the
  git-ignored `results/` directory.
- The script refuses to seal a record whose `authentication_mode` is `api_key`,
  whose `scored` is not `false`, or whose consumed budget exceeds any frozen
  bound. [FR-030, FR-033]
