# Phase 1 Data Model: Atomicity-test router (PRSG-007)

The classifier has no persistent storage (read-only, FR-011). The "data model" is the
single JSON object it emits — a STABLE CONTRACT consumed by PRSG-008 — plus the conceptual
change-class mapping the detectors apply. The machine-readable schema lives in
`contracts/routing-decision.schema.json`.

---

## Entity 1 — Routing decision (the emitted JSON object)

### Success object (FR-011a)

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `route` | string | yes | Exactly one of the five-value enum (below). |
| `releasable` | boolean | yes | `false` only for destructive-migration or concurrency classes (FR-008); else `true` (FR-009). Route-INDEPENDENT. |
| `signals` | string[] | yes (may be empty) | Decisive detector findings, from the controlled vocabulary (Entity 2). |
| `hints` | string[] | yes (may be empty) | Advisory-probe output from the three shallow probes (flag-system, release-cadence, consumer-locality). MUST NOT contain any `signals[]` token (FR-010/FR-011b). |
| `warnings` | string[] | yes (may be empty) | Canonical CI-green sentences only (Entity 3). |

### Error object (FR-011a, FR-012)

| Key | Type | Description |
|-----|------|-------------|
| `error` | string | Human-readable usage/unreadable-input message. Emitted with exit 2. NO `route` key is present on the error path. |

### `route` enum (FR-001) — five values

| Value | When | MVP-emittable? |
|-------|------|----------------|
| `split-PR` | Proven additive multi-seam change (multiple independent additive capabilities), no hard-atomic signature. | yes |
| `one-navigable-PR` | Default / abstain route: uncertain splittability, OR modify-heavy non-hard-atomic change. | yes |
| `single-atomic-PR` | Any hard-atomic signature detected (overrides split). | yes |
| `out-of-scope` | `tasks.md` missing or empty (short-circuits before any detector). | yes |
| `branch-by-abstraction` | RESERVED. Trigger (in-place modify, all consumers in-tree) needs a decisive consumer-locality probe kept advisory-only here. | **NO — never emitted in the MVP** (FR-001, SC-008; owned by PRSG-010 US3). |

---

## Entity 2 — `signals[]` controlled vocabulary (FR-011b)

The decisive tokens. PRSG-008 and the Layer-4 fixtures treat this as a closed contract.

### Hard-atomic tokens (FR-007) — each routes to `single-atomic-PR`

| Token | Class | Read from |
|-------|-------|-----------|
| `hard-atomic:exported-symbol-rename` | rename of an exported/public symbol | `tasks.md` + `plan.md` (keyword, FR-007a) |
| `hard-atomic:global-version-pin` | global version/dependency/runtime bump or pin | `tasks.md` + `plan.md` (keyword, FR-007a) |
| `hard-atomic:destructive-migration` | destructive/irreversible schema migration | all three artifacts (path + SQL verb) |
| `hard-atomic:mutual-exclusion-primitive` | auth / payment / mutual-exclusion / locking / leader-election (ONE coarse class) | `tasks.md` + `plan.md` (keyword, FR-007a) |
| `hard-atomic:out-of-tree-contract-break` | breaking change to a versioned/out-of-tree contract (`/api/vN`, public/MCP/webhook) | all three artifacts (path + keyword) |

### Releasability tokens (FR-008) — set `releasable: false` + append a warning

| Token | Class | Warning appended |
|-------|-------|------------------|
| `releasability:destructive-migration` | destructive migration | the destructive-migration CI-green sentence (Entity 3) |
| `releasability:concurrency` | concurrency-sensitive change | the concurrency CI-green sentence (Entity 3) |

### US1 routing reads (FR-011b) — two tokens, namespace `change-shape:`

The additive-vs-modify reading (FR-005) is the US1 routing signal. Both tokens are recorded
in `signals[]` as decisive findings (distinct from the three advisory probes, which go to
`hints[]` only).

| Token | Class | When emitted |
|-------|-------|--------------|
| `change-shape:additive-multi-seam` | proven additive multi-seam change | route → `split-PR` |
| `change-shape:modify-heavy` | modify-heavy non-hard-atomic change | route → `one-navigable-PR` |

Abstain (uncertain / no decisive signal) emits NO `change-shape:` token — `signals[]` is
empty and the route is `one-navigable-PR` (FR-006). The `change-shape:` namespace does not
collide with the reserved `hard-atomic:` / `releasability:` namespaces above.

### NOT in `signals[]`

The three advisory probes — flag-system, release-cadence, consumer-locality — emit ONLY
into `hints[]` (FR-010/FR-011b) and MUST NEVER appear in `signals[]`. Each hint carries a
TODO referencing its full-depth home (the deep implementation is deferred).

---

## Entity 3 — Canonical `warnings[]` sentences (FR-008) — exactly two, fixed strings

| Class | Fixed warning string |
|-------|----------------------|
| destructive-migration | `destructive migration: a passing CI run does not prove this change is releasable (CI-green ≠ releasable)` |
| concurrency | `concurrency-sensitive change: a passing CI run does not prove this change is releasable (CI-green ≠ releasable)` |

These are the ONLY strings allowed in `warnings[]`. `warnings[]` carries no detector tokens
and no advisory-probe output.

---

## Entity 4 — Change class (conceptual mapping, NOT an emitted field)

The category a change falls into as read from its artifacts. It is NOT a separate JSON
field (spec Out of Scope) — it is recoverable from `route` + `signals` (FR-011a).

| Change class | → route | → releasable | Decisive signal(s) |
|--------------|---------|--------------|--------------------|
| additive multi-seam | `split-PR` | true | `change-shape:additive-multi-seam` |
| single additive seam | `one-navigable-PR` or `single-atomic-PR` | true (unless also releasability-risk) | (single-seam read) |
| modify-heavy (non-hard-atomic) | `one-navigable-PR` | true | `change-shape:modify-heavy` (NEVER `branch-by-abstraction`) |
| hard-atomic: rename | `single-atomic-PR` | true | `hard-atomic:exported-symbol-rename` |
| hard-atomic: version pin | `single-atomic-PR` | true | `hard-atomic:global-version-pin` |
| hard-atomic: destructive migration | `single-atomic-PR` | **false** | `hard-atomic:destructive-migration` + `releasability:destructive-migration` |
| hard-atomic: mutual-exclusion/auth/payment | `single-atomic-PR` | true | `hard-atomic:mutual-exclusion-primitive` |
| hard-atomic: out-of-tree contract break | `single-atomic-PR` | true | `hard-atomic:out-of-tree-contract-break` |
| concurrency-sensitive | (route per other detectors) | **false** | `releasability:concurrency` |
| out-of-scope (empty/missing tasks.md) | `out-of-scope` | true | (none — short-circuit) |

Note the orthogonality (FR-008): releasability is independent of route — a destructive
migration is `single-atomic-PR` AND `releasable: false`.

---

## Entity 5 — Atomicity Route record (written by the SKILL, not the script)

The `## Atomicity Route` section the speckit-autopilot SKILL writes into the workflow file
from the emitted decision, after the Tasks phase / gate G5 (FR-013). It surfaces `route`,
`releasable`, `signals`, and `warnings`. The `workflow-template.md` gains this section as a
placeholder (Q11). The route is recorded ONLY in the workflow file — NOT in `SPEC-MOC.md`
(spec Assumptions). This record is the artifact PRSG-008 / PRSG-009 read downstream.

---

## Validation rules summary (from requirements)

- Exactly one `route` per successful run, from the five-value enum (SC-001).
- `route == split-PR` ⇒ proven additive multi-seam, no hard-atomic signature (FR-003); `signals[]` contains `change-shape:additive-multi-seam` (FR-011b).
- modify-heavy + non-hard-atomic ⇒ `signals[]` contains `change-shape:modify-heavy`, `route == one-navigable-PR`; abstain (no decisive signal) emits no `change-shape:*` token (FR-006).
- Any hard-atomic signature ⇒ `route == single-atomic-PR`, overriding split (FR-007, SC-003).
- `releasable == false` ⇔ destructive-migration or concurrency class, with the matching
  canonical warning present (FR-008, SC-004); otherwise `releasable == true`, `warnings == []`
  (FR-009).
- Uncertain splittability ⇒ `route == one-navigable-PR`, never `split-PR` (FR-006, SC-005).
- MVP NEVER emits `branch-by-abstraction` (FR-001, SC-008).
- Empty/missing `tasks.md` ⇒ `route == out-of-scope`, decided before any detector (FR-003).
- `signals[]` ∩ `hints[]` == ∅; `hints[]` holds only the three advisory probes (FR-010/FR-011b).
- Error path ⇒ `{"error":...}`, exit 2, no `route` key (FR-011a, FR-012).
