# Data Model: Gate Repair

## GateVerdict

| Field | Type | Notes |
| --- | --- | --- |
| gate | string | G1 to G7 |
| pass | boolean | The authoritative result |
| open_findings | integer | Required findings still unresolved |

Each of the 19 increments reuses this entity unchanged.
