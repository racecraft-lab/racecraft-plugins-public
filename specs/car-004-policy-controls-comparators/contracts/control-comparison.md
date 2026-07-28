# Contract: `control-comparison.schema.json`

**Path**: `tests/speckit-pro/layer6-efficiency/contracts-claude/control-comparison.schema.json`

**`$id`**: `https://racecraft.dev/schemas/car-004/control-comparison.schema.json`

**`$schema`**: `https://json-schema.org/draft/2020-12/schema`

**Consumers**: CAR-011 (applies the rules and produces the verdict), release
reviewers (read the messaging map to validate wording), G56R-004 (mirrors the
members).

This document owns the CAR-011-facing rules. CAR-004 produces no verdict; it
freezes how one will be produced. Field-level rules and their requirement mapping
are in [../data-model.md](../data-model.md).

## Shape

```text
{
  "$schema", "$id", "title", "description",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version", "comparison_id", "comparison_digest", "status",
    "frozen_at", "eligibility_floors", "dominance_rule", "confidence_method",
    "multiplicity_position", "reserved_partition_binding", "messaging_map",
    "car_003_bindings"
  ],
  "properties": { ... },
  "$defs": {
    "digest", "binding", "eligibilityFloors", "dominanceRule",
    "marginMapEntry", "confidenceMethod", "multiplicityPosition",
    "messagingMapEntry", "dimensionProjection"
  }
}
```

## The decision procedure this document freezes

Three stages in a fixed order. The order is part of the contract, not a
convention, and `dominance_rule.evaluation_order` states it literally.

```text
1. eligibility_floors      -> not cleared        => no verdict, whatever the numbers say
2. pareto (8 dimensions)   -> comparator wins    => not_dominant
                           -> tie / mixed        => inconclusive
                           -> candidate wins     => continue
3. materiality_margin      -> >= 1 eligible component clears its lower bound => dominant
                           -> none clears                                    => not_dominant
                           -> all margin_not_computable                      => not_dominant
```

The margin never replaces the Pareto rule; it is a second-stage materiality
filter reached only on candidate dominance. [FR-020, FR-021a]

## Invariants a conforming instance must satisfy

| # | Invariant | Requirement |
|---|---|---|
| C1 | `comparison_digest` recomputes to the recorded value | FR-002, SC-012 |
| C2 | Every `$ref` resolves under this document's own `#/$defs/` | FR-004, SC-017 |
| C3 | `required_gates` is set-equal to the frozen seven-member `deterministic_gates.gate` enum | FR-019 |
| C4 | `dimensions` is set-equal to the frozen eight-member `pareto_policy.dimensions` | FR-020 |
| C5 | `weights_prohibited` is `true`; no weighted scalar ranking appears anywhere | FR-020 |
| C6 | `margin_map` is total over all eight dimensions — four margin-eligible at 0.10, four no-worse-only with a recorded reason | FR-021, SC-016 |
| C7 | `dimension_projection` declares the single frozen rename `duration_ms` to `duration`; an unprojected vector raises rather than comparing | FR-021e |
| C8 | `margin_denominator` is the comparator's value; a zero comparator value yields `margin_not_computable`, never an infinite or 100% improvement | FR-021c, SC-016 |
| C9 | Exactly one confidence method and exactly one multiplicity position are declared | FR-023, SC-017 |
| C10 | `secondary_control_arm_family` is declared here, disjoint from the frozen analysis plan's three families rather than added to them | FR-005, FR-023, SC-017 |
| C11 | `messaging_map` is total and single-valued over `dominant \| not_dominant \| inconclusive` | FR-024, SC-008 |
| C12 | The `dominant` entry restricts wording to measured improvement over the previous static baseline and forbids `efficient`, `optimal`, and `best_measured` | FR-024 |
| C13 | `reserved_partition_binding` names the CAR-011 reserved entry by `{id, digest}` | FR-025 |

## What this document deliberately does not do

- **It concludes nothing about dominance.** No CAR-004 artifact states or implies
  which side wins. [spec Out of Scope]
- **It imposes no messaging restriction outside `dominant`.** A mixed, tied,
  inconclusive, or incomplete comparison restricts nothing. [FR-022]
- **It introduces no weighted composite**, and no ranking that could be read as
  one. Acceptance participates only through the no-worse half, so a control that
  is cheaper because it gave up can never read as materially dominant. [FR-020,
  FR-021b]
- **It does not read the FR-016a severity rank.** Terminal state is categorical
  and unordered here; the severity order is aggregation-only. Both halves are
  separate decision-semantics entries in the twin-handoff record so a mirroring
  implementation cannot collapse them. [FR-021b, FR-016a]
