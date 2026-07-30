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

All three declare `$schema` draft 2020-12 and `schema_version: {"const": "1.0.0"}`.
No `$ref` leaves its own `#/$defs/` (FR-016). No fourth shared-definitions document
exists; helpers are re-declared locally, which is what all eleven existing documents
do (research D5).

### Object closure rule — three classes, not one blanket setting

Closure is `additionalProperties: false` for **record** objects only. Stating it as a
blanket rule for *every* object would be wrong in two places, and wrong in opposite
directions, so the rule is written out per class:

| Class | Setting | Members |
| --- | --- | --- |
| **Record** — a fixed, known field set | `additionalProperties: false` | every root; every `$defs` in §1 and §3 (`agentIdentity`, `route`, `declaredBudgets`, `attemptedRoute`, both diagnostic `$defs`, `remediation`, `dispatchTuple`, `reportedBudgets`, `optionalHelper`, `override`); each corpus case's validated members |
| **Open-keyed map** — keys are data, not schema | `additionalProperties: <value schema>` plus `propertyNames` | the four §2 snapshot maps |
| **Deliberately open** | `additionalProperties: true` | `details` only (§3) |

`false` on an open-keyed map would reject **every** entry, because each data key is by
definition an additional property — the snapshot schema would be unsatisfiable for any
non-empty snapshot. The map form is the directory's established shape, not an
exception invented here: `score-bundle.schema.json` `$defs/ballot/properties/`
`criterion_scores` is an open-keyed map declared with `additionalProperties: <schema>`,
and `propertyNames` already constrains map keys in three of the eleven documents.

`details` is the single deliberate `true`, justified in §3. Recording it in this table
is what keeps it distinguishable from an oversight — an unclosed nested object is
otherwise indistinguishable from a forgotten one, which is precisely where drift
enters.

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

**Map closure.** Four of these fields are open-keyed maps whose keys are aliases or
model IDs — data, not schema — so they take the map form from the closure table above,
never `additionalProperties: false`:

| Map | `propertyNames` | `additionalProperties` (the value schema) |
| --- | --- | --- |
| `alias_bindings` | `{"type": "string", "minLength": 1}` | `{"type": "string", "minLength": 1}` |
| `supported_efforts` | `{"type": "string", "minLength": 1}` | `{"type": "array", "items": {<ladder enum>}, "uniqueItems": true}` |
| `probe_availability` | `{"type": "string", "minLength": 1}` | `{"type": "boolean"}` |
| `exact_invocation_probe` | `{"type": "string", "minLength": 1}` | `{"enum": ["success", "failure", "absent"]}` |

Keys are constrained by `propertyNames` rather than left unconstrained, so an empty-string
alias or model ID is rejected at validation instead of becoming a silently unmatchable
map entry. The key sets cannot be closed to an `enum` — the aliases and model IDs are
per-case synthetic values, and a cross-document constraint tying snapshot keys to
policy values is not expressible here (the same limit FR-006 records for
`alias_unresolved`).

`platform_route_changes` is an **array** of two-field records, not a map, so it is
closed with `additionalProperties: false` per record and carries
`uniqueItems: true` — a tuple listed twice would carry no additional meaning, and the
engine implements `uniqueItems` (research D2).

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
| `attempted_routes` | array of `$defs/attemptedRoute`, `minItems: 0` | array order **is** attempt order (FR-004); no redundant index field. Empty **iff** the pre-walk pass rejected the policy (FR-019c) |
| `diagnostics` | array, no `minItems` | may be empty — FR-011's clean success emits none. Order is the three-stage sequence in FR-012b |
| `budgets` | `$defs/reportedBudgets` | declared caps plus actual counts (FR-026), counted per the units in FR-026a |
| `release_claim_eligible` | boolean | `true` only as a residual — `false` under an override, under `no_safe_route`, or with any policy-violation diagnostic present (FR-024a) |
| `optional_helper` | `$defs/optionalHelper` | structured, never a diagnostic (FR-025); valued per FR-025a in all three helper states |
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
`oneOf` could not express. Note what branch 3 does **not** do: it does not make the
report `resolved`. `outcome` follows the qualified walk and an override never promotes
it (FR-024a), which is why branches 2 and 3 are independent rather than exclusive.

**The empty-attempt case validates.** With `minItems: 0` on `attempted_routes`, a
pre-walk structural rejection (FR-019c) produces `outcome: no_safe_route` plus
`unresolved_agent`, satisfying branch 2, with an empty attempt array, all three actual
budget counters at `0`, and `release_claim_eligible: false`. It is an ordinary valid
instance of this one shape, not a fourth branch. The `minItems: 1` this document
previously carried would have made that report invalid — the array's bound and the
pre-pass ordering contradicted each other, and the biconditional in FR-019c is what
replaces the guarantee the bound was providing.

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
| `severity` | yes | inline enum `info`/`warning`/`error`; the value is a **function of `code`** — see the table below (FR-012c) |
| `source` | yes | `{"const": "route-fallback-simulator"}` — one literal per producing module, mirroring `envelope.py:55` (FR-012c) |
| `remediation` | yes | `$ref: "#/$defs/remediation"` |
| `details` | **no** | object; required conditionally — for all four route-scoped resolution codes (FR-012, FR-029a) |

`remediation` is a field of each diagnostic entry and **never** a top-level report
field — hoisting it would create the second dialect FR-012 forbids.

**`$defs/resolutionDiagnostic`** — `properties/code/enum` holds exactly the five
codes the Claude roadmap pins at
`docs/ai/specs/claude-agent-routing-technical-roadmap.md:527-529`:
`preferred_model_unavailable`, `effort_unsupported`,
`capability_probe_unavailable`, `treatment_probe_failed`, `no_safe_route`.

This pointer — `$defs/resolutionDiagnostic/properties/code/enum` — is FR-017a's
live read target. Nothing else may restate these five members anywhere.

**Four** `allOf` branches inside this `$defs` make `details` required, one per
route-scoped resolution code: `preferred_model_unavailable` (FR-006),
`effort_unsupported` (FR-007), `capability_probe_unavailable` (FR-008), and
`treatment_probe_failed` (FR-009). Each branch requires **both** `details` and
`route_id` within it, since FR-029a's join key living in an optional object — or in a
required object as an optional member — is not a key a consumer can rely on. The first
two branches additionally require the payload members their own requirements name.
`$defs/policyViolationDiagnostic` carries **four more** branches of the same shape, so
the eight route-scoped codes are covered symmetrically; see below.

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
| `route_id` | string | **every** route-scoped diagnostic — all four resolution codes and the four policy-authoring violations (FR-029a); the join key to `attempted_routes` |
| `exhausted_budget` | array, `items` an inline 3-member enum (`probe_attempts`, `retries`, `fan_out`), `minItems: 1`, `uniqueItems: true`, enum declaration order | the terminal `no_safe_route` diagnostic only; lists every class whose actual count equals its declared cap (FR-026a) |

The four sub-reasons are total over the projection and the simulator evaluates them in
the FR-006 order — `alias_unresolved`, `alias_repointed`, `model_absent`,
`platform_route_changed` — so exactly one applies and replay stays byte-identical.

**Two orders, orthogonal, both structural.** The sub-reason order above is
*intra-diagnostic*: it picks the single `sub_reason` a `preferred_model_unavailable`
entry carries. FR-012b adds an *inter-diagnostic* order: a route failing several
independent checks emits one diagnostic per failed check, sequenced by the FR-005
declaration order, and the whole `diagnostics` array runs pre-walk violations, then
per-route entries in attempt order, then `unqualified_override`, then exactly one
terminal `no_safe_route` last. Neither order supplies the other, and treating the
sub-reason staging as covering diagnostic sequencing is exactly how the inter-code order
stayed unpinned while appearing to be settled. Both are staged call graphs, not comments.

Their exclusivity is **not uniform**, which is why the order is structural rather than
decorative (FR-006). The first three partition the state of `alias_bindings` against
`available_models` and cannot co-occur. `platform_route_changed` reads the separate
`platform_route_changes` array, so it *can* co-occur with any of the first three and is
disjoint only because it is evaluated last. Concretely, for the
`platform-route-changed` case to pin the sub-reason its name promises, its snapshot must
bind the alias exactly as the route pins it and list the pinned model in
`available_models`; otherwise an earlier predicate matches first and the case's pinned
report is wrong. The staged private helpers make this order a call-graph property, so a
future edit cannot reorder it by moving a line.

**`$defs/policyViolationDiagnostic`** — identical envelope; its
`properties/code/enum` holds exactly `fallback_loop`,
`unqualified_adjacent_model`, `generic_agent_substitution`,
`silent_inherit_materialization`, `unqualified_override`.

It carries **four** `allOf` branches of its own, mirroring the resolution `$defs`
exactly: `fallback_loop`, `unqualified_adjacent_model`, `generic_agent_substitution`,
and `silent_inherit_materialization` each require `details` and `route_id` within it
(FR-012, FR-029a). Without them, four of the eight codes FR-029a names could validly omit
`details` and so omit the route key — the join would hold for resolution rejections and
silently fail for policy-authoring ones, which is the half-covered state a reviewer would
be least likely to notice. `unqualified_override` takes **no** branch, and that is the
deliberate exception: it is an environment condition scoped to no route (FR-019c), so it
has no `route_id` to carry. Eight branches across the two `$defs`, one per route-scoped
code, with exactly one member of either enum exempt.

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

**Adequacy of the vocabulary against the bounds.** `minItems: 1` obliges every
diagnostic to carry an action and `maxItems: 3` caps it, so the eleven members are only
sufficient if every code has at least one apt action and no code needs a fourth. Both
hold, and the mapping is recorded here rather than left to the implementer, so a
reviewer can check sufficiency without re-deriving it:

The same table fixes each code's `severity`, which FR-012c makes a function of `code`
rather than of the occurrence. A single test asserts both columns over every emitted
diagnostic.

| Code | `severity` | Action members | Count |
| --- | --- | --- | --- |
| `preferred_model_unavailable` | `warning` | Re-probe the environment and confirm the pinned alias and resolved model. | 1 |
| `effort_unsupported` | `warning` | Declare an effort the model's probed capability set supports. | 1 |
| `capability_probe_unavailable` | `warning` | Re-run capability probing before trusting this route. | 1 |
| `treatment_probe_failed` | `warning` | Inspect the exact-invocation probe evidence for this route. | 1 |
| `no_safe_route` | `error` | Widen the declared fallback list with qualified routes. **+** Roll back to the previous plugin release. | 2 |
| `fallback_loop` | `error` | Remove the repeated route from the fallback chain. | 1 |
| `unqualified_adjacent_model` | `error` | Replace the adjacent model with a qualified route. | 1 |
| `generic_agent_substitution` | `error` | Restore the named agent in the fallback route. | 1 |
| `silent_inherit_materialization` | `error` | Declare the model and effort explicitly on the route. | 1 |
| `unqualified_override` | `warning` | Unset the unqualified subagent-model override before making release claims. | 1 |

All ten codes across both closed enums are covered; the maximum is 2, against a cap of
3, so no code is near the truncation boundary and none would be silently shortened by
the real runner. The mapping is one-to-one except for `no_safe_route`, which is the
only code carrying both a forward remedy and the mandated rollback — and FR-029a makes
that allocation binding, so the rollback action never repeats on a per-route entry.

The severity split is what makes `error` a usable threshold. A route rejection is a
`warning` because the walk may still resolve on a later fallback, so a report carrying
only warnings resolved *despite* them; `error` marks a policy that is unusable as
written, or a walk that ended with no route. `unqualified_override` is a `warning`
because dispatch proceeds under it — its consequence is carried by
`release_claim_eligible: false`, not by the severity. `info` is declared by the closed
vocabulary and emitted by no code, which is the same declared-but-unexercised position
FR-019 takes for the policy-violation members slice 1 cannot emit.

Each corpus case pins its diagnostic's `actions` array explicitly, so this mapping
constrains *authoring* rather than adding a runtime rule — but leaving it unrecorded
would let a case pair, say, `fallback_loop` with the rollback action and still satisfy
every schema keyword.

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
| `reportedBudgets` | `declared` (`max_probe_attempts`, `max_retries`, `max_fan_out`) and `actual` (`probe_attempts`, `retries`, `fan_out`), all required integers (FR-026); each actual counter's unit is defined in FR-026a |
| `optionalHelper` | `consulted` (boolean), `no_helper_path_validated` (boolean), and `probe_attempts` (integer, `minimum: 0`) — all three required (FR-025, FR-025a) |
| `override` | `source`, `tuple` (`$ref: #/$defs/dispatchTuple`), `would_have_been` (`outcome` required, `effective_dispatch_tuple` optional) — all required (FR-024) |

**What each actual counter counts** (FR-026a), stated here because a counter without a
unit cannot be checked against its cap: `probe_attempts` increments once per attempted
route whose snapshot probe state is consulted; `retries` once per re-consultation of a
route whose exact-invocation outcome is `failure`, which is what makes retry exhaustion
reachable against a static snapshot; `fan_out` once per candidate route entered, so it
equals `len(attempted_routes)` whenever the walk runs. Hence
`probe_attempts <= fan_out` always, and the two are not redundant — a route rejected
before probing is reached raises `fan_out` without raising `probe_attempts`. Declaring
the unit follows this directory's own habit of pairing every cap with a required `unit`
(`policy-control-registry.schema.json:670-676`).

`optional_helper.probe_attempts` is **disjoint** from `budgets.actual.probe_attempts`:
the former counts probes spent on the helper's routes, the latter the reported agent's
own walk. The helper counter exists so that "not consulted" is a measurable zero rather
than a self-asserted boolean (FR-025a) — an implementation could otherwise probe every
helper route and still write `consulted: false` without changing a pinned byte.

`override.would_have_been.outcome` carries its own `resolved`/`no_safe_route`
value so the spec's edge case is expressible: an unqualified override present
*and* no qualified route resolving still records the override as effective, still
sets `release_claim_eligible: false`, and still reports the would-have-been
outcome as `no_safe_route`. In that case `would_have_been.effective_dispatch_tuple` is
**omitted**, never present as `null` (FR-024a) — canonical serialization renders both
forms deterministically, so the choice is a schema decision that has to be stated, and
omission is what the rest of this report already does for conditional members.

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

Because no schema governs the envelope, the properties FR-033b and SC-007 lean on are
asserted in the test instead of being assumed (FR-015a): `case_id` values are unique,
non-empty strings; every case carries `policy`, `snapshot`, `overrides` (explicitly
`null` when none) and `expected_report`; and no case's payload names another case's
`case_id`. `uniqueItems` could have expressed the first of these if the corpus were
schema-validated, but it is not, and adding a fourth document to gain one keyword is
what FR-016 forbids.

**Cross-slice stability is review-borne, not asserted.** Uniqueness and
self-containment are properties of one committed state and are checkable; "slice 2 did
not alter a slice-1 case" spans two states. The replay test cannot detect it, because a
case whose inputs *and* pinned report both moved still replays consistently. FR-033b
plus the stacked-diff review is the enforcement, and saying so keeps the guarantee from
being over-read.

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
fixture is **not** a corpus case — it must fail schema validation, and every corpus
case must validate — so it is constructed inline in the **slice-1** test, the same
technique FR-019a uses, travelling with the `maximum` keyword it proves (FR-027).

Two case-authoring obligations that the field design alone does not convey:

- **`budget-exhaustion-of-one` binds the `retries` class.** It declares all three budgets
  at `1` — valid against §1's bounds, since `max_retries` allows `0` upward and the other
  two allow `1` upward — pins all three actual counts, and pins
  `details.exhausted_budget: ["probe_attempts", "retries", "fan_out"]` on its terminal
  diagnostic (FR-028, FR-026a). Its preferred route's exact-invocation outcome is
  `failure`, the one permitted retry re-consults it and returns the same `failure`, and no
  further retry may be taken. Retries are named explicitly because the roadmap states
  retry exhaustion as its own obligation while FR-028's parent sentence and User Story 2's
  scenario 7 both allow "a probe or retry budget", which a probe-only case would satisfy
  while leaving retries unproven. No case makes probe-attempt or fan-out exhaustion the
  sole at-cap class.
- **The three pre-walk violation cases record an empty `attempted_routes`.**
  `unqualified-adjacent-model`, `generic-agent-substitution`, and
  `silent-inherit-materialization` are rejected before the walk starts, so their pinned
  reports carry `attempted_routes: []`, all three actual counters at `0`, and
  `release_claim_eligible: false` (FR-019c). `fallback-loop` is the exception in that
  group: it is detected during the walk, so its report carries the routes attempted
  before the revisit and does **not** repeat the revisited route.

---

## 5. Simulator public surface

`tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py` — one module
across both slices (FR-033d). Pure function of its arguments: no filesystem,
network, wall-clock, or randomness input (FR-001).

Imported read-only rather than restated (research D1): `validate_instance`,
`load_contract`, `CONTRACT_ROOT`, `ControlContractError` from
`claude_policy_controls`; `canonical_json` from `claude_successor_freeze`.

**The unit test imports the same `canonical_json`, and re-declares nothing** (FR-014a).
This is a deliberate break with local habit: all six existing `canonical_json`
occurrences under `unit/` define their own copy, and two of those six append a trailing
newline while the library function does not. A local copy here would be a second
serializer, and because the pinning comparison passes the pinned report through the same
local copy, a discrepancy against the simulator's real output would cancel rather than
fail. The test therefore asserts over the string `serialize_report` itself returns.
Serialized reports carry **no trailing newline** and **no floating-point value** — the
only numeric fields are the integer budget caps and counts — so neither dimension is
left to a serializer default.

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

**The pre-pass covers three codes, not four** (FR-019c). `unqualified_adjacent_model`,
`generic_agent_substitution`, and `silent_inherit_materialization` are decidable from
the declared policy alone, so they run to completion before the first route is
attempted and suppress the walk entirely. `fallback_loop` is detected *inside* the walk,
on reaching a route already attempted — which is what FR-001 means by needing walk state
and what FR-020 means by "already-attempted". `unqualified_override` is neither: it is an
environment condition read from the overrides input and never suppresses the walk.

**Diagnostic ordering is a second staged call graph** (FR-012b), separate from the
sub-reason staging. Per attempted route, one private helper per rejection family is
called in the FR-005 declaration order and each appends its own diagnostic if its
predicate holds — the accumulate-all shape
`claude_policy_controls.py:2282-2298` already uses for budget breaches, rather than the
alphabetical `sorted(set(reasons))` at `claude_policy_controls.py:2524`, which would
scramble a meaningful precedence and could not be made structural. The array is then
assembled in the three stages FR-012b fixes, with exactly one terminal `no_safe_route`
entry last.

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
