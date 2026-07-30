# Phase 1 Data Model: CAR-005 Model Availability, Fallback, and Recovery Simulation

**Date**: 2026-07-29 | **Spec**: `specs/car-005-availability-fallback-recovery/spec.md`

Field-level design for the three JSON Schema documents, the scenario corpus
envelope, and the simulator's public surface. Every shape here lands **complete in
slice 1**; slice 2 adds no field and edits no schema (FR-033b).

The three schema documents are the implementation deliverables. This file is the
design that produces them — it is deliberately **not** a second copy of their
bytes, because a transcribed contract is the drift hazard this whole feature is
built to avoid (spec FR-017a; research D1).

---

## Document map

| Document | `$id` | Validates |
| --- | --- | --- |
| `route-policy.schema.json` | `https://racecraft.dev/schemas/car-005/route-policy.schema.json` | each corpus case's `policy` |
| `environment-snapshot-projection.schema.json` | `https://racecraft.dev/schemas/car-005/environment-snapshot-projection.schema.json` | each corpus case's `snapshot` |
| `route-resolution-report.schema.json` | `https://racecraft.dev/schemas/car-005/route-resolution-report.schema.json` | each case's `expected_report` and every simulator output |

All three declare `$schema` draft 2020-12, `additionalProperties: false` at every
object, and `schema_version: {"const": "1.0.0"}`. No `$ref` leaves its own
`#/$defs/` (FR-016). No fourth shared-definitions document exists; helpers are
re-declared locally, which is what all eleven existing documents do (research D5).

---

## 1. Route policy

Root, all required: `schema_version`, `agent`, `preferred_route`,
`fallback_routes`, `budgets`.

### `$defs/agentIdentity`

| Field | Type | Notes |
| --- | --- | --- |
| `name` | string, `minLength: 1` | synthetic; never one of the twelve shipped agents (FR-018, SC-006) |
| `role_class` | inline enum | `required_executor`, `bounded_analyst`, `optional_helper` — the three classes the spec's assumptions fix |

### `$defs/route`

| Field | Required | Type | Purpose |
| --- | --- | --- | --- |
| `route_id` | yes | string, `minLength: 1` | attempt-order identity; how a `fallback_loop` revisit is recognised |
| `alias` | yes | string, `minLength: 1` | the pinned alias (FR-003) |
| `resolved_model` | **no** | string, `minLength: 1` | the pinned qualified resolved model ID |
| `effort` | **no** | inline enum `low`/`medium`/`high`/`xhigh`/`max` | the frozen Claude ladder (research D11) |
| `qualified` | yes | boolean | fixture-declared qualification, per the spec's assumption |
| `adjacent_to` | no | string | a sibling `route_id`; encodes the FR-021 adjacency relation |
| `substituted_agent` | no | object `{name, class}`, `class` inline enum `named`/`generic` | present only when the route dispatches a different agent (FR-022) |

**`resolved_model` and `effort` are deliberately optional.** FR-023 requires a
corpus case whose route omits an explicit model or effort so the value *would* be
materialized by inheritance, and requires the simulator to reject it with
`silent_inherit_materialization`. If the schema required both fields, that fixture
would fail **validation** instead of producing a **diagnostic**, and FR-023 asks
for a diagnostic. This is the deliberate inverse of FR-027, which does want a
validation failure. The two requirements pull opposite ways on purpose, and the
schema honours each where it is asked:

- omitted model/effort → admitted by schema, rejected by the simulator;
- out-of-range budget → rejected by schema, never reaches the simulator.

### `fallback_routes`

Array of `$defs/route`, ordered, `minItems: 0`.

**`uniqueItems` MUST NOT be set.** FR-020 requires a case whose fallback chain
revisits an already-attempted route. `uniqueItems: true` would make that fixture
unrepresentable, converting a required diagnostic into a validation error — the
same trap as the omitted-model case above. `minItems: 0` is likewise required:
the spec's edge cases include an empty fallback list whose preferred rejection
leads directly to `no_safe_route`.

### `$defs/declaredBudgets`

All three required, integers, each carrying **both** bounds so FR-027's maxima are
co-located with the field's `type` (the directory's universal habit):

| Field | Bounds |
| --- | --- |
| `max_probe_attempts` | `minimum: 1`, `maximum: 8` |
| `max_retries` | `minimum: 0`, `maximum: 8` |
| `max_fan_out` | `minimum: 1`, `maximum: 8` |

A declared `1` satisfies FR-028's budget-of-one exhaustion case. Slice 2's
negative fixture declares `9` and must fail validation rather than be clamped.

The spec records the honest caveat, repeated here: bounding a `max_*` field from
**above** with `maximum` has no exact precedent in this directory — the existing
budget precedent bounds such fields from below, because there the field's value
*is* the ceiling. The keyword choice is this feature's own; only its placement
follows convention.

---

## 2. Environment snapshot projection

Root, all required: `schema_version`, `available_models`, `alias_bindings`,
`supported_efforts`, `probe_availability`, `exact_invocation_probe`,
`platform_route_changes`.

Purpose-built from the five facts resolution consumes. It does **not** reuse the
CAR-002 runtime-capability capture-record shape (FR-002), which carries capture
provenance, digests, and retention metadata resolution never reads.

| Field | Shape | Consumed by |
| --- | --- | --- |
| `available_models` | array of model-ID strings, `uniqueItems: true` | FR-006 `model_absent` |
| `alias_bindings` | object, alias → resolved model ID | FR-006 `alias_unresolved` (key absent) and `alias_repointed` (key present, different value) |
| `supported_efforts` | object, model ID → array of ladder efforts | FR-007 `effort_unsupported` |
| `probe_availability` | object, model ID → boolean | FR-008 `capability_probe_unavailable` |
| `exact_invocation_probe` | object, model ID → inline enum `success`/`failure`/`absent` | FR-009 `treatment_probe_failed`, FR-011 clean success |
| `platform_route_changes` | array of `{alias, resolved_model}` pinned tuples | FR-006 `platform_route_changed` |

**Resolved ambiguity — keying.** Acceptance scenarios 4 and 5 speak of probe state
"for a candidate route", while FR-002 enumerates probe availability and
exact-invocation outcomes among *per-model* facts. FR-002 is the authority on the
projection's shape, so both maps are keyed by **model ID**, and the scenario prose
reads as "for that route's model". Keying by `route_id` would also make the
snapshot depend on policy identifiers, coupling two documents that FR-015 keeps
independent within a case.

`probe_availability` uses an explicit `false` rather than an absent key wherever a
probe is unavailable, because FR-008 forbids treating probe absence as probe
success and an absent key is exactly the ambiguity that invites it.

Object maps are safe for determinism: `canonical_json` sorts keys (research D1),
so no dict-insertion order reaches the serialized bytes.

---

## 3. Route resolution report

**One shape, discriminated by `outcome`** (FR-013a). Not a root `oneOf` — the
FR-024 override path emits a `no_safe_route` report that still carries
`effective_dispatch_tuple`, so the two outcomes do not partition the field space
(research D3).

### Root fields

Required in **both** outcomes: `schema_version`, `agent`, `outcome`,
`attempted_routes`, `diagnostics`, `budgets`, `release_claim_eligible`,
`optional_helper`.

| Field | Type | Notes |
| --- | --- | --- |
| `outcome` | inline enum `resolved`/`no_safe_route` | the discriminator |
| `attempted_routes` | array of `$defs/attemptedRoute`, `minItems: 1` | array order **is** attempt order (FR-004); no redundant index field |
| `diagnostics` | array, no `minItems` | may be empty — FR-011's clean success emits none |
| `budgets` | `$defs/reportedBudgets` | declared caps plus actual counts (FR-026) |
| `release_claim_eligible` | boolean | `false` under an unqualified override (FR-024) |
| `optional_helper` | `$defs/optionalHelper` | structured, never a diagnostic (FR-025) |
| `effective_dispatch_tuple` | `$defs/dispatchTuple` | conditional (below) |
| `unresolved_agent` | string, `minLength: 1` | conditional (below) |
| `override` | `$defs/override` | optional; present only when the environment carries one |

### Conditional requiredness

Three `allOf` branches, each in the directory's verified `if`/`then` +
`not: {required: [...]}` idiom (research D3):

1. `outcome == "resolved"` → require `effective_dispatch_tuple`, **forbid**
   `unresolved_agent`.
2. `outcome == "no_safe_route"` → require `unresolved_agent`.
3. `override` present → require `effective_dispatch_tuple`.

Branch 3 is what makes the override path expressible: combined with branch 2 it
yields a `no_safe_route` report carrying both `unresolved_agent` and
`effective_dispatch_tuple`, which is precisely the field combination a root
`oneOf` could not express.

### `$defs/attemptedRoute`

`route_id` (required), `alias` (required), `resolved_model` (optional), `effort`
(optional), `disposition` (required, inline enum `selected`/`rejected`).

Model and effort stay optional here for the same reason as in the policy: an
inherit-materialization route must be recordable as attempted.

### The two diagnostic `$defs` (FR-016a)

`diagnostics.items` is
`{"oneOf": [{"$ref": "#/$defs/resolutionDiagnostic"}, {"$ref": "#/$defs/policyViolationDiagnostic"}]}`.

Both share the runner envelope verified at `envelope.py:43-66` (research D7):

| Field | Required | Notes |
| --- | --- | --- |
| `code` | yes | the inline closed enum — differs per `$defs` |
| `message` | yes | string, `minLength: 1`, `maxLength: 240` (the runner truncates at 240) |
| `severity` | yes | inline enum `info`/`warning`/`error` |
| `source` | yes | string, `minLength: 1` |
| `remediation` | yes | `$ref: "#/$defs/remediation"` |
| `details` | **no** | object; required conditionally |

`remediation` is a field of each diagnostic entry and **never** a top-level report
field — hoisting it would create the second dialect FR-012 forbids.

**`$defs/resolutionDiagnostic`** — `properties/code/enum` holds exactly the five
codes the Claude roadmap pins at
`docs/ai/specs/claude-agent-routing-technical-roadmap.md:527-529`:
`preferred_model_unavailable`, `effort_unsupported`,
`capability_probe_unavailable`, `treatment_probe_failed`, `no_safe_route`.

This pointer — `$defs/resolutionDiagnostic/properties/code/enum` — is FR-017a's
live read target. Nothing else may restate these five members anywhere.

Two `allOf` branches make `details` required for `preferred_model_unavailable`
(FR-006) and `effort_unsupported` (FR-007).

`details` is an **open** object (`additionalProperties: true`) with named
properties pinned, mirroring the runner's `dict[str, Any]`. Openness is load
bearing, not laziness: slice 2 must add no schema field (FR-033b), so
`details` must already admit every payload slice 2 emits. The named properties
and their inline enums are declared in slice 1:

| `details` property | Shape | Carried by |
| --- | --- | --- |
| `sub_reason` | inline 4-member enum: `alias_unresolved`, `alias_repointed`, `model_absent`, `platform_route_changed` | `preferred_model_unavailable` (FR-006) |
| `alias` | string | all four sub-reasons |
| `pinned_resolved_model` | string | `alias_repointed`, `model_absent`, `platform_route_changed` |
| `observed_resolved_model` | string | `alias_repointed`, `platform_route_changed` |
| `declared_effort` | ladder enum | `effort_unsupported` (FR-007) |
| `supported_efforts` | array of ladder efforts | `effort_unsupported` (FR-007) |
| `route_id` | string | probe diagnostics |

The four sub-reasons are mutually exclusive and total over the projection, and the
simulator evaluates them in the FR-006 order — `alias_unresolved`,
`alias_repointed`, `model_absent`, `platform_route_changed` — so exactly one
applies and replay stays byte-identical.

**`$defs/policyViolationDiagnostic`** — identical envelope; its
`properties/code/enum` holds exactly `fallback_loop`,
`unqualified_adjacent_model`, `generic_agent_substitution`,
`silent_inherit_materialization`, `unqualified_override`.

Declared in **slice 1** even though no slice-1 corpus case can emit one (FR-019).
That is house style here — `score-bundle.schema.json:88-89` declares a 12-member
and a 36-member enum of which at most four members are ever exercised (research
D6) — and FR-019a's inline negative test proves the closure of both enums inside
slice 1's own diff.

### `$defs/remediation`

`summary` (required, string `minLength: 1`) and `actions` (required, array,
`minItems: 1`, `maxItems: 3`). Both bounds mirror the runner: `envelope.py:37`
truncates with `actions[:3]`, and `envelope.py:60` substitutes a default so the
list is never empty. A fourth action would be silently discarded by the real
runner.

`actions.items` is a **closed inline enum of literal strings** — no structured
objects, no substitution slots. Case-specific values live in `details`, never
interpolated into an action string, so a consumer acts on set membership without
parsing prose (FR-012a, SC-010). Eleven members, one per diagnostic code plus the
rollback action:

```text
Roll back to the previous plugin release.
Widen the declared fallback list with qualified routes.
Re-probe the environment and confirm the pinned alias and resolved model.
Declare an effort the model's probed capability set supports.
Re-run capability probing before trusting this route.
Inspect the exact-invocation probe evidence for this route.
Remove the repeated route from the fallback chain.
Replace the adjacent model with a qualified route.
Restore the named agent in the fallback route.
Declare the model and effort explicitly on the route.
Unset the unqualified subagent-model override before making release claims.
```

`Roll back to the previous plugin release.` is verbatim per FR-012a/FR-029 and is
the imperative rendering of the roadmap's own guidance at
`claude-agent-routing-technical-roadmap.md:536-537` and `:902-903` (research D10).
The `no_safe_route` diagnostic's `actions` must include it.

> **Documented deviation.** FR-012a names this vocabulary
> `$defs.remediationAction`. It is instead declared inline at
> `$defs/remediation/properties/actions/items/enum`, because FR-016a prohibits
> bare-enum `$defs` members and the directory has **zero** of them across all
> eleven documents (research D4) — a `$defs.remediationAction` holding a
> top-level `enum` would be the first. Inlining preserves everything FR-012a
> asks for in substance: one closed set, literal strings, a single declaration
> site in the resolution-report schema, and a stable JSON pointer for a
> set-equality test. Only the `$defs` *name* is lost. `/items/enum` under a
> `$defs` object is itself an existing shape here (four occurrences). See
> plan.md "Complexity Tracking".

### Remaining `$defs`

| `$defs` | Fields |
| --- | --- |
| `dispatchTuple` | `agent`, `alias`, `resolved_model`, `effort` — all required (FR-013) |
| `reportedBudgets` | `declared` (`max_probe_attempts`, `max_retries`, `max_fan_out`) and `actual` (`probe_attempts`, `retries`, `fan_out`), all required (FR-026) |
| `optionalHelper` | `consulted` (boolean) and `no_helper_path_validated` (boolean), both required (FR-025) |
| `override` | `source`, `tuple` (`$ref: #/$defs/dispatchTuple`), `would_have_been` (`outcome` plus optional `effective_dispatch_tuple`) — all required (FR-024) |

`override.would_have_been.outcome` carries its own `resolved`/`no_safe_route`
value so the spec's edge case is expressible: an unqualified override present
*and* no qualified route resolving still records the override as effective, still
sets `release_claim_eligible: false`, and still reports the would-have-been
outcome as `no_safe_route`.

`optional_helper` is a structured field, never a diagnostic, and neither closed
enum gains a member for helper unavailability (FR-025).

---

## 4. Scenario corpus envelope

One file, `fixtures-fallback/fallback-scenario-corpus.json`, across both slices
(FR-015, FR-033c). Shape follows the verified precedent
`fixtures-controls/control-replay.json` (research D8).

Top level: `schema_version`, `fixture_kind` (`route_fallback_replay`),
`description`, `cases`.

Each entry of `cases`:

| Field | Purpose |
| --- | --- |
| `case_id` | stable identity; slice-1 values never change (FR-033b) |
| `purpose` | plain-English statement of what environment the case simulates |
| `proves` | the behaviour the case pins |
| `requirements` | array of FR identifiers, for traceability |
| `policy` | validates against `route-policy.schema.json`; declared budgets live here per FR-003 |
| `snapshot` | validates against `environment-snapshot-projection.schema.json` |
| `overrides` | the environment overrides, `null` when none |
| `expected_report` | the fully pinned report; validates against `route-resolution-report.schema.json` |

`purpose` and `proves` are what satisfy SC-007 — a reader opens one case and
learns what it simulates and what it expects without opening another file.

**Order is declaration order, never sorted.** Verified as the existing precedent
(research D8). Slice 2 appends its cases at the tail of `cases[]`, so no existing
case moves and no pinned byte is perturbed.

The corpus has no schema of its own — FR-016 permits exactly three documents, and
a fourth would have to be `$ref`-ed across files, which the engine refuses. Its
envelope is asserted structurally by the unit test; its three payload members are
validated against the three committed schemas.

### Case allocation

Slice 1 (User Story 1) — nine cases covering FR-004 through FR-011 and the four
sub-reasons:

`preferred-absent-fallback-selected`, `fable-alias-model-absent`,
`alias-unresolved`, `alias-repointed`, `platform-route-changed`,
`effort-unsupported`, `capability-probe-unavailable`, `treatment-probe-failed`,
`preferred-probe-success-clean`.

Slice 2 (User Story 2) — eight cases appended at the tail:

`fallback-loop`, `unqualified-adjacent-model`, `generic-agent-substitution`,
`silent-inherit-materialization`, `unqualified-override`,
`helper-unavailable-continues`, `budget-exhaustion-of-one`,
`no-safe-route-report-only`.

Seventeen cases cover every scenario SC-001 enumerates. The out-of-range budget
fixture is **not** a corpus case — it must fail schema validation, so it is
constructed inline in the slice-2 test, the same technique FR-019a uses.

---

## 5. Simulator public surface

`tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py` — one module
across both slices (FR-033d). Pure function of its arguments: no filesystem,
network, wall-clock, or randomness input (FR-001).

Imported read-only rather than restated (research D1): `validate_instance`,
`load_contract`, `CONTRACT_ROOT`, `ControlContractError` from
`claude_policy_controls`; `canonical_json` from `claude_successor_freeze`.

**Slice 1** — module constants for both closed vocabularies and the sub-reason
order; `RouteFallbackError(AssertionError)`; a `_require(condition, message)`
fail-closed helper; and:

| Entry point | Role |
| --- | --- |
| `load_corpus(path=...)` | read and structurally check the corpus envelope |
| `resolve(policy, snapshot, overrides, budgets)` | the walk; returns a report dict |
| `serialize_report(report)` | `canonical_json` over the report |

Private staged helpers, one per rule, so the FR-006 evaluation order is a
call-graph property rather than a comment. This mirrors CAR-004's stated rationale
for the same technique — "implemented as three functions so the order is a
call-graph property rather than a convention"
(`claude_control_comparison.py` module docstring).

**Slice 2** — additive only: new module constants, new private helpers, and new
public entry points. **No slice-1 signature changes** (FR-001, FR-033b). Adds the
structural-validation pre-pass, budget cap enforcement with attempt counting,
override handling, the helper-unavailable path, and no-safe-route remediation.

Because structural validation is a pre-pass of the same resolution walk — and
because `fallback_loop` detection needs the walk state this module already owns —
it is not a second module (FR-033d).

---

## Entity coverage

All seven Key Entities from the spec are modelled:

| Spec entity | Where |
| --- | --- |
| Route policy fixture | §1 |
| Environment snapshot projection | §2 |
| Environment overrides | §3 `$defs/override`, §4 case `overrides` |
| Declared budgets | §1 `$defs/declaredBudgets`, §3 `$defs/reportedBudgets` |
| Resolution report | §3 |
| Diagnostic entry | §3, both `$defs` |
| Scenario corpus case | §4 |
