# Contract: `policy-control-registry.schema.json`

**Path**: `tests/speckit-pro/layer6-efficiency/contracts-claude/policy-control-registry.schema.json`

**`$id`**: `https://racecraft.dev/schemas/car-004/policy-control-registry.schema.json`

**`$schema`**: `https://json-schema.org/draft/2020-12/schema`

**Consumers**: CAR-011 (applies the frozen controls), CAR-005 through CAR-010
(inherit the frozen candidate-set boundary), G56R-004 (mirrors the members), the
repository suite.

This document owns the closed-at-three control set and everything hash-relevant
to a control's identity. Field-level rules and their requirement mapping are in
[../data-model.md](../data-model.md); this file fixes the document's shape and the
invariants a conforming instance must satisfy.

## Shape

```text
{
  "$schema", "$id", "title", "description",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version", "registry_id", "registry_digest", "status",
    "frozen_at", "controls", "smoke_bounds", "car_003_bindings"
  ],
  "properties": {
    "schema_version": { "const": "1.0.0" },
    "registry_id":    { "type": "string", "minLength": 1 },
    "registry_digest":{ "$ref": "#/$defs/digest" },
    "status":         { "const": "frozen" },
    "frozen_at":      { "type": "string", "format": "date-time" },
    "controls": {
      "type": "array", "minItems": 3, "maxItems": 3, "uniqueItems": true,
      "items": { "$ref": "#/$defs/control" }
    },
    "smoke_bounds":     { "$ref": "#/$defs/smokeBounds" },
    "car_003_bindings": { "type": "array", "minItems": 1,
                          "items": { "$ref": "#/$defs/binding" } }
  },
  "$defs": {
    "digest", "binding", "control",
    "unpinnedControl", "adaptiveControl", "orchestrationChangingControl",
    "executionContract", "ladderRationale", "budgetTrigger",
    "aggregationRule", "smokeBounds", "unitAndDirection"
  }
}
```

`$defs/control` carries the common envelope and selects one specialization with
an `allOf` / `if` / `then` keyed on `control_kind`, following the `if`/`then`
precedent already used in the frozen `experiment-policy.schema.json`.

## Invariants a conforming instance must satisfy

| # | Invariant | Enforced by | Requirement |
|---|---|---|---|
| R1 | Exactly three controls, one per `control_kind`; a fourth entry is refused, including a justified-high-effort arm | `maxItems: 3` plus a uniqueness check on `control_kind` in the validator | FR-001, SC-001 |
| R2 | `registry_digest` recomputes to the recorded value | validator, using the frozen `record_digest` preimage rule | FR-002, SC-012 |
| R3 | Each `control_digest` recomputes to its recorded value, and altering any hash-relevant field changes it | validator | FR-002, SC-002 |
| R4 | Every `$ref` resolves under this document's own `#/$defs/` | validator, fail-closed | FR-004, SC-017 |
| R5 | Every CAR-003 reference is a `{id, digest}` binding, never a `$ref` | schema shape | FR-004 |
| R6 | `escalation_ladder` is a permutation of the bound freeze's `admitted_tuples` | validator ladder rules 1 and 2 | FR-011a, SC-014 |
| R7 | Within-model ladder order agrees with the frozen effort ladder | validator ladder rule 3 | FR-011a.3, SC-014 |
| R8 | Every cross-model ladder step carries a non-empty rationale | validator ladder rule 4 | FR-011a.4, SC-014 |
| R9 | The three response maps are total over their frozen enums and single-valued | validator, set-equality against `score-bundle.schema.json` | FR-010, SC-003 |
| R10 | `terminal_state_severity` is set-equal — not order-equal — to the frozen terminal-state enum | validator | FR-016a |
| R11 | `aggregation_rule` is total over all eight Pareto dimensions | validator | FR-016 |
| R12 | `max_input_tokens + max_cache_read_tokens + max_output_tokens == 1000000` | validator, machine-checked identity | FR-030, SC-017 |
| R13 | `smoke_bounds.authentication_mode == "subscription"` | schema `const` | FR-030 |
| R14 | Every numeric in `smoke_bounds` carries its unit and comparison direction | schema shape (`$defs/unitAndDirection`) | FR-034.6 |

## Compatibility rules

- **Additive only.** This document is new. It edits, re-versions, and removes
  nothing in the frozen CAR-003 set, including every member already listed for
  CAR-012 reconciliation. [FR-005, SC-004]
- **No new telemetry.** Every `observed_signals` member resolves to a member the
  frozen CAR-003 execution-trace or score-bundle contract already publishes as
  stable. [FR-008, FR-009]
- **Identity, not mutation.** Any hash-relevant change produces a new control or
  registry version. There is no in-place edit path. [FR-002, FR-007]
