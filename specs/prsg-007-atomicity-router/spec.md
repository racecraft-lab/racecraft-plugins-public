# Feature Specification: Atomicity-test router (read-only classifier) (PRSG-007)

**Feature Branch**: `prsg-007-atomicity-router`

**Created**: 2026-06-08

**Status**: Draft

**Input**: User description: "Atomicity-test router (read-only classifier) — PRSG-007. The brain that decides whether a change can be split SAFELY. Ship as a read-only classifier: given a feature's tasks.md/plan.md/spec.md, emit a routing decision. It changes nothing and blocks nothing — it only classifies and records."

## User Scenarios & Testing *(mandatory)*

<!--
  Phase 4 of PR-Size Governance is the split-PR engine. Before any PR emission is wired
  (PRSG-008 layer-planner, PRSG-009 multi-PR emission), this spec ships the "brain" that
  decides whether a change can be split safely. It is the read-only first half of the
  engine: a classifier that emits a routing decision and records nothing itself.
-->

### User Story 1 - Atomicity classifier emits a route (Priority: P1)

The speckit-autopilot workflow, after finishing the Tasks phase (gate G5), needs to know
whether the feature it just planned can be split into multiple small PRs safely, or
whether it must stay a single PR. It runs the read-only classifier against the feature's
`tasks.md`, `plan.md`, and `spec.md`. The classifier inspects the change's *structural
shape* and emits exactly one routing decision, choosing from a fixed set of routes:
`split-PR`, `one-navigable-PR`, `branch-by-abstraction`, `single-atomic-PR`, or
`out-of-scope`. Splittability is judged by **structural seams** — multiple independent
additive capabilities or surfaces that could each ship on their own — **not** by lines of
code. The decision is emitted as a single machine-readable result so the autopilot can
record it for the downstream layer-planner (PRSG-008) and emission (PRSG-009) specs to
read.

**Why this priority**: This classifier is the brain that makes split-PR a *safe* default.
No PR-splitting can happen safely without it: the layer-planner and emission specs that
follow have nothing to act on until a route exists. Shipping it first, as a pure
classifier that records the route but changes nothing, de-risks the whole Phase 4 engine —
the routing logic can be exercised and trusted before any irreversible PR emission is
wired. This story alone delivers value: a trustworthy route recorded in the workflow file.

**Independent Test**: Run the classifier against a fixture feature directory whose
`tasks.md` describes multiple independent additive capabilities, and confirm it emits a
single result naming a route from the fixed set (e.g. `split-PR`); run it against a
fixture with a single indivisible additive capability and confirm it emits a
single-PR-style route. The result is observable directly from the classifier's output
without any other component.

**Acceptance Scenarios**:

1. **Given** a feature directory whose `tasks.md` shows multiple independent additive
   capabilities (distinct structural seams), **When** the classifier runs, **Then** it
   emits exactly one result naming the `split-PR` route.
2. **Given** a feature directory whose change is a single indivisible additive capability,
   **When** the classifier runs, **Then** it emits a single-PR-style route
   (`one-navigable-PR` or `single-atomic-PR`) and never `split-PR`.
3. **Given** a feature whose `tasks.md`/`plan.md` indicate the change modifies existing
   behavior (signals such as `UPDATE`, `DELETE`, `DROP`, `CHECK`) rather than purely
   adding (signals such as `CREATE TABLE` or nullable column additions), **When** the
   classifier applies its detection order, **Then** the additive-vs-modify reading
   influences the route, and a purely additive multi-seam change is preferred for
   splitting over a modify-heavy one.
4. **Given** a feature where the classifier cannot confidently determine splittability
   (ambiguous or insufficient signal), **When** it finishes, **Then** it abstains to the
   default route `one-navigable-PR` and never auto-selects `split-PR` on uncertainty.
5. **Given** any successful classification, **When** the classifier finishes, **Then** it
   emits exactly one machine-readable result and writes no files of its own.

---

### User Story 2 - Hard-atomic override and releasability warning (Priority: P1)

Some changes must never be split, no matter how many seams they appear to have, because
splitting them would break the tree at an intermediate commit or expose an unsafe partial
state. The classifier therefore applies a **hard-atomic override**: if it detects a
hard-atomic signature — an exported-symbol rename, a global version pin, a destructive
migration, a mutual-exclusion / auth / payment primitive, or an out-of-tree contract
break — it routes the change to `single-atomic-PR` regardless of any seams it found.
Separately, the classifier flags **releasability** risk: for change classes where
continuous-integration success does not prove the change is safe to release — destructive
migrations and concurrency-sensitive changes — it marks the result as not releasable and
attaches a warning that "CI-green ≠ releasable" for that class, so the autopilot and a
human reviewer are alerted before the change is treated as shippable.

**Why this priority**: Without the hard-atomic override, the classifier could recommend
splitting a change that is irreducible, and the downstream engine would produce a broken
intermediate state. Without the releasability warning, a destructive or concurrency change
could pass every automated gate and still be unsafe to ship. Both behaviors are essential
safety properties of the "safe by default" split engine, so both share P1 with the core
classifier.

**Independent Test**: Run the classifier against a fixture containing a hard-atomic
signature (e.g. an exported-symbol rename described in `tasks.md`/`plan.md`) and confirm
the emitted route is `single-atomic-PR` even though the fixture has multiple apparent
seams; run it against a destructive-migration fixture and confirm the result is marked not
releasable and carries the CI-green warning.

**Acceptance Scenarios**:

1. **Given** a feature whose signals include a hard-atomic signature (exported-symbol
   rename, global version pin, destructive migration, mutual-exclusion/auth/payment
   primitive, or out-of-tree contract break), **When** the classifier runs, **Then** the
   emitted route is `single-atomic-PR`, overriding any split-PR signal from detected seams.
2. **Given** a feature whose change is a destructive migration, **When** the classifier
   runs, **Then** the result is marked not releasable and includes a warning that a
   passing CI run does not prove the change is releasable.
3. **Given** a feature whose change has a concurrency signature, **When** the classifier
   runs, **Then** the result is marked not releasable and includes the same CI-green
   warning.
4. **Given** a feature with no hard-atomic signature and no releasability risk, **When**
   the classifier runs, **Then** the result is marked releasable and carries no
   CI-green warning.

---

### Edge Cases

- **Unreadable or missing input**: The classifier reports a usage/input error (non-success
  exit status, never a block) only for genuine read failures: (a) the feature directory is
  absent or unreadable, or (b) a *present* input file (`tasks.md`, `plan.md`, or `spec.md`)
  cannot be read. A **missing or empty `tasks.md` is NOT an error** — it short-circuits to
  the `out-of-scope` route with a success exit (see "Conflicting signals / precedence" below
  and FR-003), because absence of tasks means there is nothing in scope to classify, not that
  the input could not be read. A merely-*absent* (not unreadable) `plan.md` or `spec.md` is
  likewise tolerated: the detector that would read it degrades gracefully (it contributes no
  signal), so absence of an optional artifact never errors or blocks. Only a file that is
  present-but-unreadable is a read failure.
- **No discernible signal at all**: When none of the detectors find a decisive signal, the
  classifier abstains to the default route `one-navigable-PR` — it never auto-splits and
  never blocks.
- **Conflicting signals / precedence**: Precedence is total and ordered: (1) input shape — a
  missing/empty `tasks.md` yields `out-of-scope` before anything else; then, among changes
  that have a `tasks.md`, (2) a hard-atomic signature wins and yields `single-atomic-PR`,
  overriding any split-PR signal; then (3) a proven additive multi-seam change yields
  `split-PR`; otherwise (4) the change abstains to `one-navigable-PR`.
- **Change is entirely outside the governed scope**: When the change does not fit any
  splittable or atomic category the router governs, it emits the `out-of-scope` route so
  the autopilot can fall back to its default single-PR behavior.
- **Contextual probe signal present but shallow**: When a flag-system, release-cadence, or
  consumer-locality signal is detected, it is surfaced only as an advisory hint and does
  not, on its own, force a split — the three fully-implemented detectors decide the route.
- **Advisory probe cannot run / errors internally**: An advisory probe that cannot run or
  fails internally degrades silently — it emits no hint and MUST NOT produce a failure, a
  non-success exit, or a block. An empty `hints[]` is a normal successful outcome; advisory
  probes can never change the success/error outcome (only the three decisive detectors and
  the input-shape check can), so no input can cause the classifier to block (FR-010, FR-012).

## Requirements *(mandatory)*

### Functional Requirements

#### Core classifier (fully implemented)

- **FR-001**: The classifier MUST accept a feature's `tasks.md`, `plan.md`, and `spec.md`
  as inputs and emit exactly one routing decision drawn from the fixed set: `split-PR`,
  `one-navigable-PR`, `branch-by-abstraction`, `single-atomic-PR`, `out-of-scope`.
  The `branch-by-abstraction` value is **RESERVED** in this contract enum: the MVP's
  fully-implemented detectors MUST NEVER emit it. Its trigger — in-place modification with
  ALL consumers in the tree — depends on a *decisive* consumer-locality determination, which
  FR-010 deliberately keeps advisory-only; so a modify-heavy, non-hard-atomic change abstains
  to `one-navigable-PR` (FR-006) instead. The value is reserved (not dropped) to keep the
  JSON enum a stable contract for PRSG-008; promoting the consumer-locality probe to decisive
  (and thus making `branch-by-abstraction` emittable) is owned by PRSG-010 US3.
- **FR-002**: The classifier MUST decide splittability by **structural seams** (multiple
  independent additive capabilities or surfaces), NOT by lines of code; it MUST NOT compute
  or rely on any LOC/sizing metric.
- **FR-003**: The classifier MUST first short-circuit on input shape: if `tasks.md` is
  missing or empty, it MUST emit `out-of-scope` and stop BEFORE any detector (including the
  hard-atomic override) runs. Otherwise it MUST apply detectors in this order: (1) `tasks.md`
  shape, (2) additive-vs-modify, (3) flag-system probe, (4) release cadence, (5) consumer
  locality.
- **FR-004**: The classifier MUST fully implement the `tasks.md`-shape detector — reading
  the structure of `tasks.md` to identify whether the work comprises multiple independent
  additive capabilities (seams) or a single indivisible one.
- **FR-005**: The classifier MUST fully implement the additive-vs-modify detector —
  distinguishing modify signals (e.g. `UPDATE`, `DELETE`, `DROP`, `CHECK`) from additive
  signals (e.g. `CREATE TABLE`, nullable column additions) — and use that reading when
  choosing the route.
- **FR-006**: When the classifier cannot confidently determine splittability, it MUST
  abstain to the default route `one-navigable-PR` and MUST NOT auto-select `split-PR` on
  uncertainty.

#### Hard-atomic override and releasability (fully implemented)

- **FR-007**: The classifier MUST fully implement a hard-atomic override: on detecting any
  hard-atomic signature it MUST route the change to `single-atomic-PR`, overriding any
  split-PR signal. Each class is detected by a case-insensitive intent-grep over the planning
  prose (`tasks.md` + `plan.md` + `spec.md`) and, on a hit, emits one namespaced `signals[]`
  token (the stable vocabulary for PRSG-008 and the L4 fixtures):
  - `hard-atomic:exported-symbol-rename` — a described rename of an exported/public symbol.
  - `hard-atomic:global-version-pin` — a global version/dependency/runtime bump or pin.
  - `hard-atomic:destructive-migration` — a destructive/irreversible schema migration.
  - `hard-atomic:mutual-exclusion-primitive` — an auth / payment / mutual-exclusion /
    locking / leader-election primitive (ONE coarse, over-inclusive class; not sub-divided).
  - `hard-atomic:out-of-tree-contract-break` — a breaking change to a versioned/out-of-tree
    contract (e.g. `/api/vN`, a public / MCP / webhook surface).
  Detection is tuned OVER-INCLUSIVE on purpose: a false positive only refuses a split
  (→ `single-atomic-PR`), the safe direction; a false negative is the dangerous one.
- **FR-007a**: Keyword-based detection of the conceptual classes that have no path signal
  (exported-symbol rename, global version pin, auth/payment/mutual-exclusion primitive, AND
  the concurrency releasability class) MUST avoid false positives from a feature's own
  definitional vocabulary: (a) it MUST match on word boundaries or a structural
  task-/story-line shape AND a described ACTION/INTENT — e.g. "introduce a mutex", "add a lock
  around", "fix a data race", "rename … to …" — NOT a bare class noun / topic mention (e.g.
  `lock` MUST NOT fire on "block", and the word "concurrency" appearing as a topic MUST NOT
  fire the concurrency probe); and (b) it MUST read these keyword classes from `tasks.md` +
  `plan.md` (the work description), NOT from `spec.md` (which may merely enumerate the class
  names as vocabulary). This is what makes the mandated dogfood self-check hold: running the
  classifier on PRSG-007's own feature dir — whose artifacts enumerate
  auth/payment/lock/mutex/concurrency as vocabulary but perform none of those actions — MUST
  NOT yield a spurious `single-atomic-PR` NOR a spurious `releasable: false` +
  `releasability:concurrency`. (The path-signalled classes — destructive-migration,
  additive-vs-modify — continue to read all three artifacts, because their signal is a file
  path / SQL verb, not a definitional keyword.)
- **FR-008**: The classifier MUST detect destructive-migration and concurrency signatures
  and, for those classes, mark the result not releasable (`releasable: false`) AND append one
  canonical `warnings[]` sentence. Each releasability class emits a namespaced `signals[]`
  token and its fixed warning string (stable contract):
  - `releasability:destructive-migration` → warning: "destructive migration: a passing CI
    run does not prove this change is releasable (CI-green ≠ releasable)".
  - `releasability:concurrency` → warning: "concurrency-sensitive change: a passing CI run
    does not prove this change is releasable (CI-green ≠ releasable)".
  Releasability is INDEPENDENT of the route: a change MAY be `single-atomic-PR` AND not
  releasable (a destructive migration is both). A false negative here is the dangerous
  direction, so these probes are tuned over-inclusive. Over-inclusion applies to genuine
  change-intent signals (a real lock introduction, a data-race fix, an actual destructive
  migration) — it does NOT license firing on topic-mention vocabulary: a spec/task that
  enumerates concurrency keywords while *implementing a concurrency detector* contains no
  concurrency-sensitive change. The concurrency probe is therefore governed by the
  action-intent discipline of FR-007a(a), for the same reason the hard-atomic keyword classes
  are.
- **FR-009**: For changes with no releasability-risk signature, the classifier MUST mark
  the result releasable and attach no CI-green warning.

#### Contextual probes (advisory hints only)

- **FR-010**: The classifier MUST emit the flag-system probe, release-cadence, and
  consumer-locality detectors as **advisory hints only** — surfaced in the result but not
  deeply implemented, and not, on their own, sufficient to force a split. Each advisory probe
  MUST degrade gracefully: a probe that cannot run or fails internally emits no hint and MUST
  NOT cause a failure, a non-success exit, or a block — an empty `hints[]` is a normal
  successful outcome (reinforcing FR-012's never-block guarantee). (Deep implementation of
  these three probes is out of scope for this spec — see Out of Scope.)

#### Output, advisory contract, and recording

- **FR-011**: The classifier MUST be read-only: it MUST emit exactly one machine-readable
  result to standard output and MUST write no files of its own.
- **FR-011a**: The single JSON object MUST contain top-level keys `route` (string, one of
  the five enum values), `releasable` (boolean), `signals` (array of strings, from the
  fully-implemented detectors), `hints` (array of strings, from the three advisory probes),
  and `warnings` (array of strings). The `signals` array carries decisive detector findings;
  the `hints` array carries advisory-probe output (FR-010), kept distinct from `signals`.
  Field names and the route enum are a STABLE CONTRACT consumed by PRSG-008; the error path
  emits a top-level `{"error": <string>}` with no `route`. Naming follows the existing
  `reviewability-gate.sh` conventions (flat top-level keys, string arrays).
- **FR-011b**: The `signals[]` vocabulary is a controlled, stable contract for PRSG-008 and
  the L4 fixtures. Decisive tokens: `hard-atomic:exported-symbol-rename`,
  `hard-atomic:global-version-pin`, `hard-atomic:destructive-migration`,
  `hard-atomic:mutual-exclusion-primitive`, `hard-atomic:out-of-tree-contract-break`,
  `releasability:destructive-migration`, `releasability:concurrency`,
  `change-shape:additive-multi-seam` (→ `split-PR`), and `change-shape:modify-heavy`
  (→ `one-navigable-PR`). Abstain (no decisive signal) emits NO `change-shape:` token —
  `signals[]` is empty and the route is `one-navigable-PR` (FR-006). The three advisory probes
  (flag-system, release-cadence, consumer-locality) emit ONLY into `hints[]` and MUST NOT
  appear in `signals[]` (FR-010); `warnings[]` carries only the human CI-green sentences.
- **FR-012**: The classifier MUST be advisory-only and MUST NOT act as a gate: it MUST
  report success without blocking the workflow, and MUST signal only a usage/unreadable-input
  error condition as a non-success outcome (it MUST NOT emit a "blocked"/threshold-exceeded
  outcome).
- **FR-013**: The speckit-autopilot workflow (the SKILL, not the classifier script) MUST be
  the component that records the emitted route into the workflow file's "## Atomicity Route"
  section, after the Tasks phase / gate G5.
- **FR-014**: The classifier MUST be generic across technology stacks — its detection MUST
  rely on a stack-agnostic surface taxonomy (in the spirit of the existing reviewability
  surface taxonomy) rather than assuming a specific language, framework, or build system.
  Two mechanisms keep it stack-agnostic: (1) surface-by-path detection that DUPLICATES the
  small `surface_for_path` / `is_excluded_generated` matchers from `reviewability-gate.sh`
  (per the no-shared-lib constraint, FR-015) for the migration/API surfaces; and (2)
  over-inclusive natural-language intent-greps for the conceptual classes (rename, version
  pin, auth/payment, concurrency) that have no path signal. Maintainers MUST NOT "tighten"
  the hard-atomic / releasability probes into false negatives. The duplicated matcher MUST
  carry a `KEEP IN SYNC with reviewability-gate.sh` comment marker (the repo's established
  anti-drift convention for mandated duplication).
- **FR-015**: The classifier MUST operate independently of the existing reviewability gate:
  it MUST NOT call that gate internally and MUST NOT edit it. (Combining this route with
  reviewability sizing to decide whether to *actually* split is the autopilot's job, not
  the classifier's.)

### Reviewability Budget *(mandatory)*

- **Primary surface**: scheduler/runtime (a new classifier script invoked by the autopilot
  workflow after the Tasks phase).
- **Secondary surfaces, if any**: harness/adapter (Layer 4 fixtures and unit tests);
  docs/process (a minimal `speckit-autopilot` SKILL edit to invoke the classifier and
  record the route).
- **Projected reviewable LOC**: ~400 (one `scripts/atomicity-route.sh`, plain `bash` + `jq`).
- **Projected production files**: 1 (`scripts/atomicity-route.sh`); plus a small,
  bounded edit to the `speckit-autopilot` SKILL.
- **Projected total files**: ~6 (the script, its Layer 4 test with one fixture per change
  class, and the SKILL edit).
- **Budget result**: within budget.
- **Split decision**: This remains one spec. It ships a single read-only classifier with no
  PR-emission machinery; the LOC budget (~400) sits at the per-spec warning line, and the
  change has one structural seam (classify-and-emit). PR emission, the layer-planner, and
  multi-PR rewrite are separate downstream specs (PRSG-008, PRSG-009).

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget,
  traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and
  verification evidence (Layer 4 fixtures per change class; Layer 1 structural validation).
- Deferred work MUST name the follow-up spec or issue (PRSG-008 layer-planner, PRSG-009
  multi-PR emission, and the deep implementation of the three contextual probes).

### Key Entities *(include if feature involves data)*

- **Routing decision**: The single JSON result the classifier emits. Top-level keys
  (FR-011a): `route` (one of `split-PR`, `one-navigable-PR`, `branch-by-abstraction`,
  `single-atomic-PR`, `out-of-scope`); `releasable` (boolean); `signals` (decisive detector
  findings); `hints` (advisory-probe output from the three shallow probes); and `warnings`
  (e.g. the CI-green-≠-releasable message). The error path emits a top-level
  `{"error": <string>}` instead.
- **Change class**: The category a change falls into as read from its artifacts — e.g.
  additive multi-seam, modify-heavy, hard-atomic (rename / version pin / destructive
  migration / mutual-exclusion-auth-payment primitive / out-of-tree contract break), or
  concurrency-sensitive. Each class maps to a route and a releasability reading. Change class
  is the conceptual mapping the detectors apply; it is NOT a separate emitted JSON field — it
  is recoverable from `route` + `signals` (FR-011a).
- **Atomicity Route record**: The "## Atomicity Route" section the autopilot SKILL writes
  into the workflow file from the emitted decision, for downstream specs to read. (Written
  by the SKILL, not by the classifier.)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every governed change class, the classifier emits exactly one route from
  the fixed set of five, in a single machine-readable result — a JSON object with the
  contract keys `route`, `releasable`, `signals`, `hints`, `warnings` (FR-011a).
- **SC-002**: A change with multiple independent additive capabilities is routed to
  `split-PR`, and an equivalent change measured only by size (large LOC, single seam) is
  NOT routed to `split-PR` — demonstrating the decision is seam-driven, not size-driven.
- **SC-003**: Every hard-atomic signature (exported-symbol rename, global version pin,
  destructive migration, mutual-exclusion/auth/payment primitive, out-of-tree contract
  break) routes to `single-atomic-PR`, even when seams are present.
- **SC-004**: Every destructive-migration and every concurrency change is marked not
  releasable and carries the CI-green warning; every change with no releasability risk is
  marked releasable with no warning.
- **SC-005**: When splittability is uncertain, the classifier abstains to
  `one-navigable-PR` 100% of the time and never auto-selects `split-PR`.
- **SC-006**: The classifier never blocks the workflow and never writes a file: a
  successful run reports success and produces only its single emitted result; an
  unreadable/missing input is reported as a usage/input error, not a block.
- **SC-007**: One Layer 4 fixture exists per change class and confirms the expected route
  and releasability reading; Layer 1 structural validation passes for the new script and
  any edited skill files.
- **SC-008**: The MVP classifier NEVER emits `branch-by-abstraction`. A modify-heavy,
  non-hard-atomic change (modify signals present, no hard-atomic signature, no proven
  additive seams) routes to `one-navigable-PR` 100% of the time. One Layer 4 fixture for
  this change class MUST exist and assert the emitted route is `one-navigable-PR` (never
  `branch-by-abstraction`), releasable, with no CI-green warning.

## Assumptions

- **Read-only, single result to stdout**: The classifier writes nothing; it emits exactly
  one machine-readable result (a single JSON object) to standard output. Recording is the
  autopilot SKILL's responsibility (FR-013).
- **Exit-status contract**: Following the existing reviewability-gate convention but without
  its blocking outcome, the classifier uses a success status on a completed classification
  and a usage/unreadable-input status otherwise; it never uses a "blocked"/threshold-exceeded
  status, because it is advisory-only (FR-012).
- **Default / abstain route**: The default route when signal is insufficient is
  `one-navigable-PR`; uncertainty never produces `split-PR` (FR-006).
- **Invocation point**: The classifier runs after the Tasks phase / gate G5 in the
  autopilot workflow (FR-013).
- **Independence from sizing**: This classifier decides *splittability by seams*; the
  autopilot separately combines this route with reviewability sizing to decide whether to
  actually split. The classifier makes no internal call to, and no edit of, the existing
  reviewability gate (FR-015).
- **MVP probe depth**: The hard-atomic overrides, the `tasks.md`-shape detector, and the
  additive-vs-modify detector are implemented fully; the flag-system, release-cadence, and
  consumer-locality probes are emitted as advisory hints only (FR-010).
- **Tooling**: Implementation is plain `bash` + `jq` per the project constitution (Script
  Safety, KISS, YAGNI) within a ~400 reviewable-LOC budget.
- **Route storage**: The route is recorded only in the workflow file's "## Atomicity Route"
  section; it is NOT stored in `SPEC-MOC.md`.

## Out of Scope

- **No PR emission, branch creation, or multi-PR rewrite** — those belong to PRSG-008
  (layer-planner) and PRSG-009 (multi-PR emission).
- **No blocking or gating behavior** — the classifier is advisory-only and never stops the
  workflow.
- **No LOC / sizing computation** — that is the existing reviewability gate's job, not this
  classifier's.
- **No deep implementation of the three contextual probes** — flag-system, release-cadence,
  and consumer-locality are emitted as advisory hints only in this spec; their deep
  implementation is deferred.
- **No `branch-by-abstraction` emission in the MVP** — the route is a reserved enum value;
  its trigger requires a decisive consumer-locality probe this spec keeps advisory-only.
  PRSG-010 US3 owns deepening that probe (and thus making the route emittable). Until then a
  modify-heavy non-hard-atomic change abstains to `one-navigable-PR` (FR-001, FR-006).
- **No internal call to, and no edit of, the existing reviewability gate; no shared-library
  extraction** in this spec.
- **No separate `change_class` JSON field** — the emitted contract is `route` + `releasable`
  + `signals` + `hints` + `warnings` (FR-011a); the change class is recoverable from `route`
  and `signals`.
- **The route is NOT stored in `SPEC-MOC.md`** — only in the workflow file's "## Atomicity
  Route" section.
